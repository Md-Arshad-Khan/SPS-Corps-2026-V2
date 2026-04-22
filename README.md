# Financial Report Q&A Assistant — V2
### Multi-Company · Multi-Year · Investment Signals
> **5 Companies:** Apple · Microsoft · Amazon · Google (Alphabet) · Huawei  
> **3 Years:** 2022 · 2023 · 2024  
> **6 Metrics:** Gross Margin · Net Profit Margin · Operating Margin · EPS · ROE · Revenue Growth (YoY)

---

## Quick Start (3 commands)

```bash
# 1. Install dependencies
pip install langgraph langchain-ollama pydantic fastapi uvicorn \
            chromadb pypdf sentence-transformers requests

# 2. Download ALL 15 reports + auto-ingest into ChromaDB
python downloader.py

# 3. Run the assistant
python main.py
```

---

## The 5 Companies

| Company | Ticker | Regulator | Currency | Fiscal Year Ends |
|---|---|---|---|---|
| Apple | AAPL | SEC (US) | USD | September |
| Microsoft | MSFT | SEC (US) | USD | June |
| Amazon | AMZN | SEC (US) | USD | December |
| Google (Alphabet) | GOOGL | SEC (US) | USD | December |
| Huawei | Private | None (Chinese private co.) | CNY | December |

> **Huawei Note:** Huawei is a private Chinese company and does NOT file with the SEC.
> Its annual reports are published in English on huawei.com and independently audited by KPMG.
> All Huawei figures are in **CNY (Chinese Yuan)**. 2024 rate: 1 USD = 7.2957 CNY.

---

## PDF Sources (All Verified — April 2026)

### Apple — SEC via Q4 CDN (s2.q4cdn.com)
| Year | URL |
|---|---|
| 2024 | https://s2.q4cdn.com/470004039/files/doc_earnings/2024/q4/filing/10-Q4-2024-As-Filed.pdf |
| 2023 | https://s2.q4cdn.com/470004039/files/doc_earnings/2023/q4/filing/_10-K-Q4-2023-As-Filed.pdf |
| 2022 | https://s2.q4cdn.com/470004039/files/doc_earnings/2022/q4/_10-K-Q4-2022-As-Filed.pdf |

### Microsoft — Official Microsoft CDN (cdn-dynmedia-1.microsoft.com)
| Year | URL |
|---|---|
| 2024 | https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/MSFT_FY24Q4_10K |
| 2023 | https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/msft-10k-20230630 |
| 2022 | https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/msft-10k-20220630 |

### Amazon — SEC EDGAR CloudFront (d18rn0p25nwr6d.cloudfront.net)
| Year | URL |
|---|---|
| 2024 | https://d18rn0p25nwr6d.cloudfront.net/CIK-0001018724/c7c14359-36fa-40c3-b3ca-5bf7f3fa0b96.pdf |
| 2023 | https://d18rn0p25nwr6d.cloudfront.net/CIK-0001018724/44bf47a5-aa4d-4fc5-b5a6-eea66c9dba3a.pdf |
| 2022 | https://d18rn0p25nwr6d.cloudfront.net/CIK-0001018724/d2a623b0-3f3f-4f31-b074-b5e5b1d3d01b.pdf |

### Google/Alphabet — abc.xyz (Official Alphabet Investor Site)
| Year | URL |
|---|---|
| 2024 | https://abc.xyz/assets/77/51/9841ad5c4fbe85b4440c47a4df8d/goog-10-k-2024.pdf |
| 2023 | https://abc.xyz/assets/9e/91/a0dad80d4f20a0a55d49ad8a96bb/20240123-alphabet-10k.pdf |
| 2022 | https://abc.xyz/assets/be/f4/4fe61e784dc296018bdc38977e84/20230203-alphabet-10-k.pdf |

### Huawei — www-file.huawei.com (Official Huawei File Server, KPMG-Audited)
| Year | URL |
|---|---|
| 2024 | https://www-file.huawei.com/admin/asset/v1/pro/view/4326dcd4a11e48e5a03491d3b13ed7c6.pdf |
| 2023 | https://www-file.huawei.com/minisite/media/annual_report/annual_report_2023_en.pdf |
| 2022 | https://www-file.huawei.com/minisite/media/annual_report/annual_report_2022_en.pdf |

---

## Full Setup Guide

### 1 — Clone & enter
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
ollama pull phi4-mini          # Planner  (~2.5 GB)
ollama pull qwen2.5-coder:3b   # Executor (~2.0 GB)
ollama pull gemma2:2b          # Critic   (~1.5 GB)
```

### 5 — Download all 15 reports and ingest
```bash
# All 15 reports (5 companies x 3 years) — RECOMMENDED
python downloader.py

# Verify URLs before downloading
python downloader.py --check

# List all reports without downloading
python downloader.py --list

# Only one company
python downloader.py --company Apple
python downloader.py --company Amazon
python downloader.py --company Google
python downloader.py --company Microsoft
python downloader.py --company Huawei

# One company + one year
python downloader.py --company Huawei --year 2024

# Download only, skip ChromaDB (then ingest manually)
python downloader.py --no-ingest
python ingestor.py financial_reports/Apple_10K_FY2024.pdf --company Apple --year 2024
```

### 6 — Run the assistant
```bash
python main.py              # interactive CLI
python main.py --demo       # professor's demo query
python main.py --api        # FastAPI server on :8000
```

---

## Example Queries

```
Compare Apple and Microsoft gross margins from 2022 to 2024.
Based on its financials, is Amazon a good investment?
Which company has the highest net profit margin in 2024?
Compare Google and Microsoft revenue growth from 2022 to 2024.
Has Huawei's operating margin improved or declined over 3 years?
Rank all 5 companies by gross margin in 2024.
Compare Apple and Huawei EPS trends from 2022 to 2024.
Which company has the strongest return on equity?
Is Microsoft a better investment than Google based on 3-year financials?
```

---

## The 6 Core Metrics

| Key | Formula | Unit |
|---|---|---|
| `gross_margin` | (Revenue − COGS) / Revenue × 100 | % |
| `net_profit_margin` | Net Income / Revenue × 100 | % |
| `operating_margin` | Operating Income / Revenue × 100 | % |
| `eps` | Net Income / Weighted Avg Shares Outstanding | USD or CNY |
| `return_on_equity` | Net Income / Shareholders' Equity × 100 | % |
| `revenue_growth_yoy` | (Rev_curr − Rev_prior) / Rev_prior × 100 | % |

---

## Architecture

```
User Query
    │
    ▼
┌──────────────────────────────────────────┐
│ Planner (phi4-mini)                       │
│ - classifies: single/comparison/          │
│               investment_signal/trend     │
│ - extracts: companies, years, metrics    │
└──────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────┐
│ Executor (qwen2.5-coder:3b)              │
│ - retrieve_multi() per (company, year)  │
│ - calculates 6 metrics                  │
│ - returns answer + metric_table JSON    │
└──────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────┐
│ Critic (gemma2:2b)                       │
│ - scores 1-10 (accuracy/completeness)   │
│ - emits BUY/HOLD/SELL signals           │
│ - ACCEPT (≥7) or RETRY (up to 2x)      │
└──────────────────────────────────────────┘
    │
    ▼
 Final Output: answer + metric table + investment signals

ChromaDB collection: financial_docs_v2
  Each chunk: { company: "...", year: "...", source: "..." }
```

---

## File Reference

| File | Purpose |
|---|---|
| `downloader.py` | Auto-downloads all 15 PDFs with verified URLs and ingests them |
| `ingestor.py` | Ingest one PDF with company + year metadata tag |
| `retriever.py` | Filtered retrieval by company and/or year |
| `metrics.py` | 6-metric registry with formulas and descriptions |
| `agents.py` | Planner, Executor, Critic — all V2 |
| `orchestrator.py` | LangGraph graph with retry logic |
| `state.py` | V2 AgentState schema |
| `llm_client.py` | Ollama JSON wrapper with retry |
| `schemas.py` | FastAPI Pydantic models |
| `api.py` | FastAPI REST server |
| `main.py` | CLI entry point with rich output |
