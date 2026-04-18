"""
api.py  –  V2
FastAPI server exposing:
  POST /query   → run the full Planner → Executor → Critic pipeline
  GET  /metrics → list the 6 supported financial metrics
  GET  /health  → liveness check
"""
from fastapi import FastAPI, HTTPException
from schemas import QueryRequest, QueryResponse
from orchestrator import build_graph
from metrics import SUPPORTED_METRICS
from state import AgentState

app = FastAPI(
    title="Financial Report Q&A Assistant – V2",
    description="Multi-company, multi-year financial analysis with investment signals.",
    version="2.0.0",
)

# Build graph once at startup
_graph = build_graph()


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/metrics")
def list_metrics():
    """Return the 6 supported financial metrics."""
    return {
        key: {
            "label":   m["label"],
            "formula": m["formula"],
            "unit":    m["unit"],
        }
        for key, m in SUPPORTED_METRICS.items()
    }


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    initial_state: AgentState = {
        "user_input":          request.question,
        "query_type":          "single",
        "companies":           [],
        "years":               [],
        "metrics":             [],
        "plan":                [],
        "retrieved_contexts":  {},
        "execution_result":    "",
        "critique":            {},
        "retry_count":         0,
        "final_output":        "",
        "metric_table":        {},
        "investment_signals":  {},
    }

    try:
        result = _graph.invoke(initial_state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    answer = result.get("final_output") or result.get("execution_result") or "No answer generated."

    return QueryResponse(
        question           = request.question,
        query_type         = result.get("query_type", "single"),
        companies          = result.get("companies", []),
        years              = result.get("years", []),
        metrics            = result.get("metrics", []),
        plan               = result.get("plan", []),
        answer             = answer,
        metric_table       = result.get("metric_table", {}),
        investment_signals = result.get("investment_signals", {}),
        critic_score       = result.get("critique", {}).get("score"),
        retries            = result.get("retry_count", 0),
    )
