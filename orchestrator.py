"""
orchestrator.py  –  V2
LangGraph pipeline:
  planner → executor → critic → (ACCEPT → END) | (RETRY → increment_retry → executor)
"""
from langgraph.graph import StateGraph, END
from state import AgentState
from agents import planner_node, executor_node, critic_node

MAX_RETRIES = 2


def should_retry(state: AgentState) -> str:
    verdict     = state.get("critique", {}).get("verdict", "RETRY")
    retry_count = state.get("retry_count", 0)
    if verdict == "ACCEPT":
        return "accept"
    if retry_count >= MAX_RETRIES:
        return "accept"   # give up gracefully; use best answer so far
    return "retry"


def increment_retry(state: AgentState) -> AgentState:
    # Preserve the last answer as fallback so we never return empty string
    fallback = state.get("execution_result", "")
    return {
        **state,
        "retry_count":  state.get("retry_count", 0) + 1,
        "final_output": fallback,   # keep last result as fallback
    }


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("planner",         planner_node)
    graph.add_node("executor",        executor_node)
    graph.add_node("critic",          critic_node)
    graph.add_node("increment_retry", increment_retry)

    graph.set_entry_point("planner")
    graph.add_edge("planner",  "executor")
    graph.add_edge("executor", "critic")

    graph.add_conditional_edges(
        "critic",
        should_retry,
        {"accept": END, "retry": "increment_retry"},
    )
    graph.add_edge("increment_retry", "executor")

    return graph.compile()
