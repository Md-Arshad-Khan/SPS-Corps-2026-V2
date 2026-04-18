"""
main.py  –  V2
Interactive CLI for the Financial Report Q&A Assistant.

Usage:
    python main.py                      # interactive prompt
    python main.py --api                # start FastAPI server on :8000
    python main.py --demo               # run the V2 professor example query

Example queries to try:
    "Compare Apple and Microsoft gross margins from 2022 to 2024."
    "Based on its financials, is Apple a good investment?"
    "Which company has stronger profitability — Apple or Microsoft?"
    "Has Microsoft's gross margin improved or declined over 3 years?"
"""
import argparse
import json
from orchestrator import build_graph
from metrics import format_metric_table
from state import AgentState

DEMO_QUESTION = "Compare Apple and Microsoft gross margins from 2022 to 2024."

# ANSI colours
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"
RED    = "\033[91m"


def banner():
    print(f"""
{BOLD}{CYAN}╔══════════════════════════════════════════════════════╗
║   Financial Report Q&A Assistant  –  V2              ║
║   Multi-Company · Multi-Year · Investment Signals     ║
╚══════════════════════════════════════════════════════╝{RESET}
""")


def run_query(question: str, graph=None):
    if graph is None:
        graph = build_graph()

    initial_state: AgentState = {
        "user_input":          question,
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

    print(f"\n{BOLD}🔍 Question:{RESET} {question}\n")
    result = graph.invoke(initial_state)

    # ── Query classification ──────────────────────────────────────────────
    print(f"{CYAN}{'─'*54}{RESET}")
    print(f"{BOLD}📌 Query Type:{RESET}  {result.get('query_type', 'N/A')}")
    print(f"{BOLD}🏢 Companies:{RESET}   {', '.join(result.get('companies', []))}")
    print(f"{BOLD}📅 Years:{RESET}       {', '.join(result.get('years', []))}")
    print(f"{BOLD}📐 Metrics:{RESET}     {', '.join(result.get('metrics', []))}")

    # ── Plan ─────────────────────────────────────────────────────────────
    print(f"\n{CYAN}{'─'*54}{RESET}")
    print(f"{BOLD}📋 Plan:{RESET}")
    for i, step in enumerate(result.get("plan", []), 1):
        print(f"   {i}. {step}")

    # ── Metric table ─────────────────────────────────────────────────────
    metric_table = result.get("metric_table", {})
    if metric_table:
        print(f"\n{CYAN}{'─'*54}{RESET}")
        print(f"{BOLD}📊 Metric Table:{RESET}")
        print(format_metric_table(metric_table))

    # ── Investment signals ────────────────────────────────────────────────
    signals = result.get("investment_signals", {})
    if signals:
        print(f"\n{CYAN}{'─'*54}{RESET}")
        print(f"{BOLD}💡 Investment Signals:{RESET}")
        for company, info in signals.items():
            signal = info.get("signal", "N/A")
            colour = GREEN if signal == "BUY" else (YELLOW if signal == "HOLD" else RED)
            rationale = info.get("rationale", "")
            print(f"   {company:15s} → {colour}{BOLD}{signal}{RESET}  |  {rationale}")

    # ── Final answer ──────────────────────────────────────────────────────
    answer = result.get("final_output") or result.get("execution_result") or "No answer generated."
    print(f"\n{CYAN}{'─'*54}{RESET}")
    print(f"{BOLD}✅ Final Answer:{RESET}")
    print(answer)

    # ── Critic metadata ───────────────────────────────────────────────────
    critique = result.get("critique", {})
    score    = critique.get("score", "N/A")
    retries  = result.get("retry_count", 0)
    print(f"\n{CYAN}{'─'*54}{RESET}")
    print(f"{BOLD}🔁 Retries:{RESET} {retries}   {BOLD}📈 Critic Score:{RESET} {score}/10")
    if critique.get("feedback"):
        print(f"{BOLD}💬 Critic Feedback:{RESET} {critique['feedback']}")
    print(f"{CYAN}{'─'*54}{RESET}\n")

    return result


def start_api():
    import uvicorn
    print(f"{GREEN}Starting FastAPI server on http://localhost:8000 …{RESET}")
    print(f"  POST http://localhost:8000/query")
    print(f"  GET  http://localhost:8000/metrics")
    print(f"  GET  http://localhost:8000/health\n")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Financial Q&A Assistant V2")
    parser.add_argument("--api",  action="store_true", help="Start FastAPI server")
    parser.add_argument("--demo", action="store_true", help="Run professor demo query")
    args = parser.parse_args()

    banner()

    if args.api:
        start_api()
    elif args.demo:
        graph = build_graph()
        run_query(DEMO_QUESTION, graph)
    else:
        graph = build_graph()
        print("Type your financial question below (or 'exit' to quit).\n")
        print(f"{YELLOW}Example queries:{RESET}")
        print("  • Compare Apple and Microsoft gross margins from 2022 to 2024.")
        print("  • Based on its financials, is Apple a good investment?")
        print("  • Which company has stronger profitability — Apple or Microsoft?")
        print("  • Has Microsoft's gross margin improved or declined over 3 years?\n")

        while True:
            try:
                question = input(f"{BOLD}❓ Enter question:{RESET} ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye!")
                break
            if not question:
                continue
            if question.lower() in ("exit", "quit", "q"):
                print("Goodbye!")
                break
            run_query(question, graph)
