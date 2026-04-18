"""
metrics.py  –  V2
Defines the 6 core financial metrics supported for cross-company comparison.
Also provides helper utilities used by the Executor agent to format metric tables.
"""
from typing import Dict

# ── Core metrics registry ─────────────────────────────────────────────────────

SUPPORTED_METRICS: Dict[str, dict] = {
    "gross_margin": {
        "label": "Gross Margin",
        "formula": "(Revenue - COGS) / Revenue × 100",
        "unit": "%",
        "description": "Measures the percentage of revenue retained after direct production costs.",
        "higher_is_better": True,
    },
    "net_profit_margin": {
        "label": "Net Profit Margin",
        "formula": "Net Income / Revenue × 100",
        "unit": "%",
        "description": "Shows how much of each dollar of revenue translates into profit after all expenses.",
        "higher_is_better": True,
    },
    "operating_margin": {
        "label": "Operating Margin",
        "formula": "Operating Income / Revenue × 100",
        "unit": "%",
        "description": "Reflects core business profitability before interest and taxes.",
        "higher_is_better": True,
    },
    "eps": {
        "label": "Earnings Per Share (EPS)",
        "formula": "Net Income / Weighted Average Shares Outstanding",
        "unit": "USD",
        "description": "Indicates profitability on a per-share basis; key for equity investors.",
        "higher_is_better": True,
    },
    "return_on_equity": {
        "label": "Return on Equity (ROE)",
        "formula": "Net Income / Shareholders' Equity × 100",
        "unit": "%",
        "description": "Measures how efficiently management generates profit from shareholders' equity.",
        "higher_is_better": True,
    },
    "revenue_growth_yoy": {
        "label": "Revenue Growth (YoY)",
        "formula": "(Revenue_current - Revenue_prior) / Revenue_prior × 100",
        "unit": "%",
        "description": "Year-over-year percentage change in total revenue; signals business momentum.",
        "higher_is_better": True,
    },
}


def metric_prompt_block() -> str:
    """Return a formatted string describing all 6 metrics for use in LLM prompts."""
    lines = ["SUPPORTED FINANCIAL METRICS (V2):"]
    for key, m in SUPPORTED_METRICS.items():
        lines.append(
            f"  • {m['label']} ({key})\n"
            f"    Formula: {m['formula']}\n"
            f"    Unit: {m['unit']}\n"
            f"    Note: {m['description']}"
        )
    return "\n".join(lines)


def format_metric_table(metric_table: dict) -> str:
    """
    Pretty-print a metric_table dict:
    {
        "Apple": {"2022": {"gross_margin": "43.3%", ...}, "2023": {...}},
        "Microsoft": {...}
    }
    """
    if not metric_table:
        return "(No metric table available)"

    lines = []
    for company, years in metric_table.items():
        lines.append(f"\n{'='*50}")
        lines.append(f"  {company}")
        lines.append(f"{'='*50}")
        for year, metrics in years.items():
            lines.append(f"  {year}:")
            for metric_key, value in metrics.items():
                label = SUPPORTED_METRICS.get(metric_key, {}).get("label", metric_key)
                lines.append(f"    {label:35s}: {value}")
    return "\n".join(lines)
