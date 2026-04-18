"""
schemas.py  –  V2
Pydantic models for the FastAPI layer.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str


class InvestmentSignal(BaseModel):
    signal:    str          # "BUY" | "HOLD" | "SELL"
    rationale: str


class QueryResponse(BaseModel):
    question:           str
    query_type:         str
    companies:          List[str]
    years:              List[str]
    metrics:            List[str]
    plan:               List[str]
    answer:             str
    metric_table:       Dict[str, Any]
    investment_signals: Dict[str, Any]
    critic_score:       Optional[int]
    retries:            int
