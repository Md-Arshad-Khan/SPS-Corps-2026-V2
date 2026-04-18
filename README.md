# Financial Report Q&A Assistant — V2

> Multi-company · Multi-year · Investment Signals  
> Built on LangGraph + ChromaDB + Ollama

---

## What's New in V2

| Feature | V1 | V2 |
|---|---|---|
| Companies supported | Apple only | Any company (multi-company comparison) |
| Years supported | Single document | Multi-year (2022, 2023, 2024+) |
| Metrics | Ad-hoc | 6 structured metrics (see below) |
| Investment signals | ✗ | ✓ BUY / HOLD / SELL per company |
| ChromaDB tagging | No metadata | company + year metadata filters |
| API response | Raw text | Structured JSON with metric table |
| CLI output | Plain print | Rich colour terminal with metric table |

---

## The 6 Core Metrics

| Key | Label | Formula |
|---|---|---|
| `gross_margin` | Gross Margin | (Revenue − COGS) / Revenue × 100 |
| `net_profit_margin` | Net Profit Margin | Net Income / Revenue × 100 |
| `operating_margin` | Operating Margin | Operating Income / Revenue × 100 |
| `eps` | Earnings Per Share (EPS) | Net Income / Weighted Avg Shares |
| `return_on_equity` | Return on Equity (ROE) | Net Income / Shareholders' Equity × 100 |
| `revenue_growth_yoy` | Revenue Growth (YoY) | (Rev_current − Rev_prior) / Rev_prior × 100 |

---

## Setup

### 1 — Clone & enter the repo
```bash
git clone https://github.com/Md-Arshad-Khan/SPS-Corps-2026.git
cd SPS-Corps-2026
```

### 2 — Virtual environment
```bash
python3 -m venv agent_env
source agent_env/bin/activate
```

### 3 — Install dependencies
```bash
pip install langgraph langchain-ollama pydantic fastapi uvicorn \
            chromadb pypdf sentence-transformers requests
```

### 4 — Install Ollama and pull models
```bash
brew install ollama
brew services start ollama
ollama pull phi4-mini          # Planner
ollama pull qwen2.5-coder:3b   # Executor
ollama pull gemma2:2b          # Critic
```

---

## Ingesting Financial Documents (V2)

V2's ingestor tags every chunk with `company` and `year` metadata so the
retriever can filter precisely when comparing multiple companies.

```bash
# Apple FY2024 Q4
python ingestor.py FY24_Q4_Consolidated_Financial_Statements.pdf \
    --company Apple --year 2024

# Apple FY2023
python ingestor.py FY23_Q4_Consolidated_Financial_Statements.pdf \
    --company Apple --year 2023

# Apple FY2022
python ingestor.py FY22_Q4_Consolidated_Financial_Statements.pdf \
    --company Apple --year 2022

# Microsoft FY2024
python ingestor.py MSFT_FY24_Annual_Report.pdf \
    --company Microsoft --year 2024

# Microsoft FY2023
python ingestor.py MSFT_FY23_Annual_Report.pdf \
    --company Microsoft --year 2023

# Microsoft FY2022
python ingestor.py MSFT_FY22_Annual_Report.pdf \
    --company Microsoft --year 2022
```

**Where to download the PDFs:**
- Apple: https://investor.apple.com/sec-filings/annual-reports/
- Microsoft: https://www.microsoft.com/en-us/investor/reports/

---

## Running the App

### Interactive CLI (default)
```bash
python main.py
```

### Professor demo query
```bash
python main.py --demo
# Runs: "Compare Apple and Microsoft gross margins from 2022 to 2024."
```

### FastAPI server
```bash
python main.py --api
# Server: http://localhost:8000
# Docs:   http://localhost:8000/docs
```

---

## Example API Usage

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Compare Apple and Microsoft gross margins from 2022 to 2024."}'
```

**Response structure:**
```json
{
  "question": "...",
  "query_type": "comparison",
  "companies": ["Apple", "Microsoft"],
  "years": ["2022", "2023", "2024"],
  "metrics": ["gross_margin"],
  "plan": ["...", "..."],
  "answer": "Full analysis text...",
  "metric_table": {
    "Apple":     {"2022": {"gross_margin": "43.3%"}, "2023": {...}, "2024": {...}},
    "Microsoft": {"2022": {"gross_margin": "68.4%"}, "2023": {...}, "2024": {...}}
  },
  "investment_signals": {
    "Apple":     {"signal": "BUY",  "rationale": "Gross margin expanded 3pp over 3 years"},
    "Microsoft": {"signal": "HOLD", "rationale": "Margin stable; cloud growth moderating"}
  },
  "critic_score": 8,
  "retries": 0
}
```

---

## Example Queries to Try

```
Compare Apple and Microsoft gross margins from 2022 to 2024.
Based on its financials, is Apple a good investment?
Which company has stronger profitability — Apple or Microsoft?
Has Microsoft's gross margin improved or declined over 3 years?
What is Apple's EPS trend from 2022 to 2024?
Compare return on equity between Apple and Microsoft.
```

---

## Architecture (V2)

```
User Query
    │
    ▼
┌─────────┐    ┌──────────┐    ┌────────┐
│ Planner │───▶│ Executor │───▶│ Critic │──▶ ACCEPT → Final Output
│phi4-mini│    │qwen2.5-  │    │gemma2  │
│         │    │coder:3b  │    │:2b     │
└─────────┘    └──────────┘    └────────┘
    │               │               │
    │ classifies     │ retrieves      │ scores
    │ - query_type   │ per company    │ - accuracy
    │ - companies    │ + year from    │ - completeness
    │ - years        │ ChromaDB       │ + investment
    │ - metrics      │               │   signals
    └───────────────▼───────────────┘
                ChromaDB
         (tagged with company + year)
```

---

## File Overview

| File | Purpose |
|---|---|
| `state.py` | V2 AgentState (adds companies, years, metrics, investment_signals) |
| `llm_client.py` | Ollama wrapper with JSON extraction and retry |
| `ingestor.py` | PDF → ChromaDB with company/year metadata tags |
| `retriever.py` | Filtered + multi-company retrieval |
| `metrics.py` | 6-metric registry with formulas and descriptions |
| `agents.py` | Planner, Executor, Critic (all upgraded for V2) |
| `orchestrator.py` | LangGraph graph definition |
| `schemas.py` | Pydantic models for FastAPI |
| `api.py` | FastAPI server |
| `main.py` | CLI entry point |
