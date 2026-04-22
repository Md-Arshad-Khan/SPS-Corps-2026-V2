"""
agents.py  –  V2
Three agents with V2 capabilities:
  • Planner   – classifies query type, identifies companies/years/metrics
  • Executor  – retrieves per-(company, year) context, builds metric table
  • Critic    – scores + generates investment signals (buy/hold/sell)
"""
import json
from llm_client import call_ollama, extract_text
from state import AgentState
from retriever import retrieve, retrieve_multi
from metrics import SUPPORTED_METRICS, metric_prompt_block, format_metric_table

PLANNER_MODEL  = "phi4-mini"
EXECUTOR_MODEL = "qwen2.5-coder:3b"
CRITIC_MODEL   = "gemma2:2b"


# ─────────────────────────────────────────────────────────────────────────────
# PLANNER
# ─────────────────────────────────────────────────────────────────────────────

def planner_node(state: AgentState) -> AgentState:
    """
    V2 Planner:
    1. Classifies the query type: single | comparison | investment_signal | trend
    2. Extracts company names, fiscal years, and relevant metrics
    3. Produces a subtask plan
    """
    prompt = f"""You are a financial analysis planner for a multi-company RAG system.

{metric_prompt_block()}

QUERY TYPES:
  - "single"            → one company, one year, general question
  - "comparison"        → two or more companies and/or metrics side-by-side
  - "investment_signal" → asks if a company is a good investment / buy / hold / sell
  - "trend"             → one company across multiple years

Your task:
1. Classify the query type.
2. Extract company names (normalise: "AAPL" → "Apple", "MSFT" → "Microsoft").
3. Extract fiscal years mentioned (default to ["2024"] if none specified).
4. Identify which of the 6 supported metrics are relevant (use the key names).
5. Break the question into 2-4 ordered subtasks.

Question: {state['user_input']}

Respond ONLY in valid JSON (no markdown, no extra text):
{{
  "query_type": "comparison",
  "companies": ["Apple", "Microsoft"],
  "years": ["2022", "2023", "2024"],
  "metrics": ["gross_margin", "net_profit_margin"],
  "subtasks": [
    "Retrieve Apple gross margin for 2022–2024",
    "Retrieve Microsoft gross margin for 2022–2024",
    "Compare and highlight year-over-year trend"
  ]
}}"""

    result = call_ollama(PLANNER_MODEL, prompt)

    # ── Defensive extraction ──────────────────────────────────────────────
    query_type = result.get("query_type", "single")
    companies  = result.get("companies", [])
    years      = result.get("years", ["2024"])
    metrics    = [m for m in result.get("metrics", []) if m in SUPPORTED_METRICS]
    subtasks   = result.get("subtasks", [])

    # Fallback: if planner missed companies, try to infer from text
    if not companies:
        lowered = state["user_input"].lower()
        if "apple" in lowered:   companies.append("Apple")
        if "microsoft" in lowered: companies.append("Microsoft")
    if not companies:
        companies = ["Apple"]

    # Fallback: if no metrics detected, default to the core four
    if not metrics:
        metrics = ["gross_margin", "net_profit_margin", "operating_margin", "revenue_growth_yoy"]

    return {
        **state,
        "query_type": query_type,
        "companies": companies,
        "years": years,
        "metrics": metrics,
        "plan": subtasks,
    }


# ─────────────────────────────────────────────────────────────────────────────
# EXECUTOR
# ─────────────────────────────────────────────────────────────────────────────

def executor_node(state: AgentState) -> AgentState:
    """
    V2 Executor:
    - Retrieves context per (company, year) from ChromaDB
    - Builds a structured metric table
    - Produces a comprehensive analysis covering all subtasks
    """
    companies  = state.get("companies", ["Apple"])
    years      = state.get("years", ["2024"])
    metrics    = state.get("metrics", [])
    query_type = state.get("query_type", "single")
    plan_text  = "\n".join(f"{i+1}. {t}" for i, t in enumerate(state.get("plan", [])))
    feedback   = state.get("critique", {}).get("feedback", "")
    feedback_text = f"\nPrevious critique to address:\n{feedback}" if feedback else ""

    # ── Multi-company, multi-year retrieval ───────────────────────────────
    contexts = retrieve_multi(state["user_input"], companies, years, n_results=5)

    # Format contexts for prompt
    context_block = ""
    for key, text in contexts.items():
        context_block += f"\n\n### Source: {key}\n{text}"

    # Metric descriptions for prompt
    metric_descriptions = "\n".join(
        f"  • {SUPPORTED_METRICS[m]['label']}: {SUPPORTED_METRICS[m]['formula']}"
        for m in metrics if m in SUPPORTED_METRICS
    )

    # ── Executor prompt ───────────────────────────────────────────────────
    prompt = f"""You are a senior financial analyst. Use ONLY the data below to answer.

FINANCIAL DATA (retrieved from SEC filings):
{context_block}

METRICS TO CALCULATE AND REPORT:
{metric_descriptions if metric_descriptions else "(Any relevant metrics)"}

ANALYSIS TASKS:
{plan_text}
{feedback_text}

QUERY TYPE: {query_type}
COMPANIES:  {", ".join(companies)}
YEARS:      {", ".join(years)}

Instructions:
- Show your formula and calculation for each metric.
- Reference actual numbers from the data (revenue, net income, COGS, etc.).
- For comparisons, produce a side-by-side table in text format.
- For investment_signal queries, flag key strengths and risks.
- If data is missing for a (company, year), note it explicitly.

You MUST respond in this exact JSON structure:
{{
  "answer": "<your full analysis here>",
  "metric_table": {{
    "Apple": {{
      "2024": {{"gross_margin": "X%", "net_profit_margin": "Y%"}}
    }},
    "Microsoft": {{
      "2024": {{"gross_margin": "A%", "net_profit_margin": "B%"}}
    }}
  }}
}}"""

    result = call_ollama(EXECUTOR_MODEL, prompt)

    answer = result.get("answer") or extract_text(result)
    metric_table = result.get("metric_table", {})

    return {
        **state,
        "retrieved_contexts": contexts,
        "execution_result": answer,
        "metric_table": metric_table,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CRITIC  (with investment signal logic)
# ─────────────────────────────────────────────────────────────────────────────

def critic_node(state: AgentState) -> AgentState:
    """
    V2 Critic:
    - Scores the answer (1-10) on accuracy, completeness, clarity
    - For investment_signal queries: emits per-company buy/hold/sell signals
    - Verdict: ACCEPT (score ≥ 7) or RETRY
    """
    query_type   = state.get("query_type", "single")
    metric_table = state.get("metric_table", {})
    mt_formatted = format_metric_table(metric_table)

    investment_instructions = ""
    if query_type == "investment_signal":
        investment_instructions = """
INVESTMENT SIGNAL TASK:
For each company, emit a signal based solely on the financial data in the answer:
  - "BUY"  → strong/improving profitability, solid margins, positive EPS trend
  - "HOLD" → mixed signals, moderate metrics, no clear directional trend
  - "SELL" → declining margins, negative EPS trend, deteriorating fundamentals
Provide a 1-2 sentence rationale grounded in the numbers.
"""

    prompt = f"""You are a senior financial analyst reviewing an AI-generated report.

Original question: {state['user_input']}

Metric table extracted:
{mt_formatted}

Full answer to review:
{state['execution_result']}
{investment_instructions}
Scoring rubric (1-10):
  • Accuracy          – Are numbers consistent with stated formulas?
  • Completeness      – Were all requested companies / years / metrics covered?
  • Clarity           – Is the comparison easy to follow?
  • Proper terminology – Does it use correct financial vocabulary?

ACCEPT if score >= 7, otherwise RETRY with specific feedback.

Respond ONLY in valid JSON (no markdown):
{{
  "score": 8,
  "feedback": "Missing net profit margin for Microsoft 2022. Add YoY trend commentary.",
  "verdict": "ACCEPT",
  "investment_signals": {{
    "Apple":     {{"signal": "BUY",  "rationale": "Gross margin expanded from 43% to 46%"}},
    "Microsoft": {{"signal": "HOLD", "rationale": "Revenue growth slowed; margins stable"}}
  }}
}}"""

    result = call_ollama(CRITIC_MODEL, prompt)

    score   = result.get("score", 0)
    verdict = "ACCEPT" if score >= 7 else "RETRY"
    # Override: respect model verdict if it says ACCEPT even with score edge cases
    if isinstance(result.get("verdict"), str) and result["verdict"].upper() == "ACCEPT":
        verdict = "ACCEPT"

    critique = {
        "score":    score,
        "feedback": result.get("feedback", ""),
        "verdict":  verdict,
    }

    investment_signals = result.get("investment_signals", {})
    final = state["execution_result"] if verdict == "ACCEPT" else ""

    return {
        **state,
        "critique":           critique,
        "investment_signals": investment_signals,
        "final_output":       final,
    }
