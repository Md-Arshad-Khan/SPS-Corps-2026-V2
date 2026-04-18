"""
state.py  –  V2 AgentState
Adds: companies, years, metrics, query_type, investment_signals
"""
from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict):
    # ── Input ──────────────────────────────────────────────────────────────
    user_input: str

    # ── Query classification (set by Planner) ──────────────────────────────
    query_type: str          # "single" | "comparison" | "investment_signal" | "trend"
    companies: List[str]     # e.g. ["Apple", "Microsoft"]
    years: List[str]         # e.g. ["2022", "2023", "2024"]
    metrics: List[str]       # e.g. ["gross_margin", "net_profit_margin"]

    # ── Pipeline stages ────────────────────────────────────────────────────
    plan: List[str]
    retrieved_contexts: Dict[str, str]   # key: "Company_Year", value: raw text
    execution_result: str
    critique: Dict[str, Any]
    retry_count: int
    final_output: str

    # ── V2 additions ───────────────────────────────────────────────────────
    metric_table: Dict[str, Any]         # structured metric results for comparison
    investment_signals: Dict[str, Any]   # per-company buy/hold/sell signals
