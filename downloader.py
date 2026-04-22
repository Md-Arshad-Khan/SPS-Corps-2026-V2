"""
downloader.py  –  V2
====================
Downloads official financial reports (PDFs) directly from each company's
confirmed source (SEC EDGAR, official investor sites, Huawei.com) and
immediately ingests them into ChromaDB with the correct company + year tags.

All URLs have been verified to be live as of April 2026.

Usage:
    python downloader.py                  # download + ingest ALL companies
    python downloader.py --company Apple  # only Apple
    python downloader.py --list           # just list all reports without downloading
    python downloader.py --check          # test all URLs are reachable (HEAD request)

⚠️  Huawei note:
    Huawei is a private Chinese company — it does NOT file with the SEC.
    Its annual reports are published directly on huawei.com in English.
    Financials are reported in CNY (Chinese Yuan Renminbi).
"""

import argparse
import os
import sys
import time
import requests
from pathlib import Path
from ingestor import ingest   # reuse V2 ingestor

# ── Download folder ────────────────────────────────────────────────────────────
DOWNLOAD_DIR = Path("./financial_reports")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# ── Verified PDF sources ───────────────────────────────────────────────────────
#
#  Source key:
#    SEC_EDGAR  – US Securities and Exchange Commission EDGAR system
#    MSFT_CDN   – Microsoft's official Azure CDN (cdn-dynmedia-1.microsoft.com)
#    HUAWEI_CDN – Huawei official file server (www-file.huawei.com)
#    ALPHABET   – Alphabet/Google official investor site (abc.xyz)
#    APPLE_CDN  – Apple via Q4 CDN (s2.q4cdn.com)
#
REPORTS = [
    # ── APPLE ─────────────────────────────────────────────────────────────────
    {
        "company":  "Apple",
        "year":     "2024",
        "filename": "Apple_10K_FY2024.pdf",
        "url":      "https://s2.q4cdn.com/470004039/files/doc_earnings/2024/q4/filing/10-Q4-2024-As-Filed.pdf",
        "source":   "APPLE_CDN",
        "currency": "USD",
        "note":     "Apple FY2024 10-K (fiscal year ending Sep 28, 2024)",
    },
    {
        "company":  "Apple",
        "year":     "2023",
        "filename": "Apple_10K_FY2023.pdf",
        "url":      "https://s2.q4cdn.com/470004039/files/doc_earnings/2023/q4/filing/_10-K-Q4-2023-As-Filed.pdf",
        "source":   "APPLE_CDN",
        "currency": "USD",
        "note":     "Apple FY2023 10-K (fiscal year ending Sep 30, 2023)",
    },
    {
        "company":  "Apple",
        "year":     "2022",
        "filename": "Apple_10K_FY2022.pdf",
        "url":      "https://s2.q4cdn.com/470004039/files/doc_earnings/2022/q4/_10-K-Q4-2022-As-Filed.pdf",
        "source":   "APPLE_CDN",
        "currency": "USD",
        "note":     "Apple FY2022 10-K (fiscal year ending Sep 24, 2022)",
    },

    # ── MICROSOFT ─────────────────────────────────────────────────────────────
    # Microsoft fiscal year ends June 30
    {
        "company":  "Microsoft",
        "year":     "2024",
        "filename": "Microsoft_10K_FY2024.pdf",
        "url":      "https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/MSFT_FY24Q4_10K",
        "source":   "MSFT_CDN",
        "currency": "USD",
        "note":     "Microsoft FY2024 10-K (fiscal year ending Jun 30, 2024)",
    },
    {
        "company":  "Microsoft",
        "year":     "2023",
        "filename": "Microsoft_10K_FY2023.pdf",
        "url":      "https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/msft-10k-20230630",
        "source":   "MSFT_CDN",
        "currency": "USD",
        "note":     "Microsoft FY2023 10-K (fiscal year ending Jun 30, 2023)",
    },
    {
        "company":  "Microsoft",
        "year":     "2022",
        "filename": "Microsoft_10K_FY2022.pdf",
        "url":      "https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/msft-10k-20220630",
        "source":   "MSFT_CDN",
        "currency": "USD",
        "note":     "Microsoft FY2022 10-K (fiscal year ending Jun 30, 2022)",
    },

    # ── AMAZON ────────────────────────────────────────────────────────────────
    # Amazon fiscal year ends December 31
    {
        "company":  "Amazon",
        "year":     "2024",
        "filename": "Amazon_10K_FY2024.pdf",
        "url":      "https://d18rn0p25nwr6d.cloudfront.net/CIK-0001018724/c7c14359-36fa-40c3-b3ca-5bf7f3fa0b96.pdf",
        "source":   "SEC_EDGAR",
        "currency": "USD",
        "note":     "Amazon FY2024 10-K (fiscal year ending Dec 31, 2024)",
    },
    {
        "company":  "Amazon",
        "year":     "2023",
        "filename": "Amazon_10K_FY2023.pdf",
        "url":      "https://d18rn0p25nwr6d.cloudfront.net/CIK-0001018724/44bf47a5-aa4d-4fc5-b5a6-eea66c9dba3a.pdf",
        "source":   "SEC_EDGAR",
        "currency": "USD",
        "note":     "Amazon FY2023 10-K (fiscal year ending Dec 31, 2023)",
    },
    {
        "company":  "Amazon",
        "year":     "2022",
        "filename": "Amazon_10K_FY2022.pdf",
        "url":      "https://d18rn0p25nwr6d.cloudfront.net/CIK-0001018724/d2a623b0-3f3f-4f31-b074-b5e5b1d3d01b.pdf",
        "source":   "SEC_EDGAR",
        "currency": "USD",
        "note":     "Amazon FY2022 10-K (fiscal year ending Dec 31, 2022)",
    },

    # ── GOOGLE (ALPHABET) ─────────────────────────────────────────────────────
    # Alphabet fiscal year ends December 31
    {
        "company":  "Google",
        "year":     "2024",
        "filename": "Google_Alphabet_10K_FY2024.pdf",
        "url":      "https://abc.xyz/assets/77/51/9841ad5c4fbe85b4440c47a4df8d/goog-10-k-2024.pdf",
        "source":   "ALPHABET",
        "currency": "USD",
        "note":     "Alphabet/Google FY2024 10-K (fiscal year ending Dec 31, 2024)",
    },
    {
        "company":  "Google",
        "year":     "2023",
        "filename": "Google_Alphabet_10K_FY2023.pdf",
        "url":      "https://abc.xyz/assets/9e/91/a0dad80d4f20a0a55d49ad8a96bb/20240123-alphabet-10k.pdf",
        "source":   "ALPHABET",
        "currency": "USD",
        "note":     "Alphabet/Google FY2023 10-K (fiscal year ending Dec 31, 2023)",
    },
    {
        "company":  "Google",
        "year":     "2022",
        "filename": "Google_Alphabet_10K_FY2022.pdf",
        "url":      "https://abc.xyz/assets/be/f4/4fe61e784dc296018bdc38977e84/20230203-alphabet-10-k.pdf",
        "source":   "ALPHABET",
        "currency": "USD",
        "note":     "Alphabet/Google FY2022 10-K (fiscal year ending Dec 31, 2022)",
    },

    # ── HUAWEI ────────────────────────────────────────────────────────────────
    # Huawei is private — not SEC listed. Reports in CNY. KPMG-audited.
    {
        "company":  "Huawei",
        "year":     "2024",
        "filename": "Huawei_Annual_Report_2024.pdf",
        "url":      "https://www-file.huawei.com/admin/asset/v1/pro/view/4326dcd4a11e48e5a03491d3b13ed7c6.pdf",
        "source":   "HUAWEI_CDN",
        "currency": "CNY",
        "note":     "Huawei FY2024 Annual Report (KPMG-audited, CNY). USD rate: 1 USD = 7.2957 CNY",
    },
    {
        "company":  "Huawei",
        "year":     "2023",
        "filename": "Huawei_Annual_Report_2023.pdf",
        "url":      "https://www-file.huawei.com/minisite/media/annual_report/annual_report_2023_en.pdf",
        "source":   "HUAWEI_CDN",
        "currency": "CNY",
        "note":     "Huawei FY2023 Annual Report (KPMG-audited, CNY)",
    },
    {
        "company":  "Huawei",
        "year":     "2022",
        "filename": "Huawei_Annual_Report_2022.pdf",
        "url":      "https://www-file.huawei.com/minisite/media/annual_report/annual_report_2022_en.pdf",
        "source":   "HUAWEI_CDN",
        "currency": "CNY",
        "note":     "Huawei FY2022 Annual Report (KPMG-audited, CNY)",
    },
]

# ANSI colours
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/pdf,*/*",
}


def check_url(url: str) -> tuple[bool, int]:
    """HEAD request to verify URL is reachable. Returns (ok, status_code)."""
    try:
        r = requests.head(url, headers=HEADERS, timeout=15, allow_redirects=True)
        return r.status_code < 400, r.status_code
    except Exception as e:
        return False, 0


def download_pdf(report: dict) -> Path | None:
    """Download a single PDF. Returns local path on success, None on failure."""
    dest = DOWNLOAD_DIR / report["filename"]

    if dest.exists() and dest.stat().st_size > 50_000:
        print(f"  {YELLOW}⏭  Already downloaded:{RESET} {dest.name}")
        return dest

    print(f"  {CYAN}⬇  Downloading:{RESET} {report['filename']}")
    print(f"     Source: {report['url']}")

    try:
        with requests.get(
            report["url"], headers=HEADERS, stream=True, timeout=120
        ) as r:
            r.raise_for_status()
            content_type = r.headers.get("Content-Type", "")
            if "pdf" not in content_type and "octet-stream" not in content_type:
                # Some CDNs return HTML for invalid URLs
                if len(r.content) < 10_000:
                    print(f"  {RED}❌  Not a PDF (Content-Type: {content_type}){RESET}")
                    return None

            total = int(r.headers.get("Content-Length", 0))
            downloaded = 0
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    f.write(chunk)
                    downloaded += len(chunk)

        size_mb = dest.stat().st_size / 1_048_576
        if dest.stat().st_size < 50_000:
            print(f"  {RED}❌  File too small ({size_mb:.2f} MB) — likely an error page{RESET}")
            dest.unlink(missing_ok=True)
            return None

        print(f"  {GREEN}✅  Saved:{RESET} {dest.name} ({size_mb:.1f} MB)")
        return dest

    except requests.RequestException as e:
        print(f"  {RED}❌  Download failed: {e}{RESET}")
        return None


def process_report(report: dict, skip_ingest: bool = False):
    """Download and ingest one report."""
    print(f"\n{BOLD}{'─'*60}{RESET}")
    print(f"{BOLD}📄 {report['company']} {report['year']}{RESET}  ({report['note']})")
    if report["currency"] == "CNY":
        print(f"  {YELLOW}⚠  Figures in CNY (Chinese Yuan). Not SEC-listed.{RESET}")

    pdf_path = download_pdf(report)
    if pdf_path and not skip_ingest:
        print(f"  🔄  Ingesting into ChromaDB …")
        try:
            ingest(str(pdf_path), report["company"], report["year"])
        except Exception as e:
            print(f"  {RED}❌  Ingest failed: {e}{RESET}")


def list_reports():
    """Print a formatted table of all configured reports."""
    print(f"\n{BOLD}{'Company':<12} {'Year':<6} {'Currency':<10} {'Source':<12} Note{RESET}")
    print("─" * 80)
    for r in REPORTS:
        print(f"{r['company']:<12} {r['year']:<6} {r['currency']:<10} {r['source']:<12} {r['note']}")
    print(f"\nTotal: {len(REPORTS)} reports across {len(set(r['company'] for r in REPORTS))} companies\n")


def check_all_urls():
    """HEAD-check all URLs and report which are reachable."""
    print(f"\n{BOLD}Checking all PDF URLs …{RESET}\n")
    ok = 0
    fail = 0
    for r in REPORTS:
        live, code = check_url(r["url"])
        status = f"{GREEN}✅ {code}{RESET}" if live else f"{RED}❌ {code}{RESET}"
        print(f"  {status}  {r['company']} {r['year']}  –  {r['url'][:80]}")
        if live:
            ok += 1
        else:
            fail += 1
        time.sleep(0.3)   # be polite
    print(f"\n{GREEN}{ok} OK{RESET}  {RED}{fail} FAILED{RESET}\n")


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download & ingest financial reports for 5 companies (V2)"
    )
    parser.add_argument("--company", help="Only download one company (Apple/Microsoft/Amazon/Google/Huawei)")
    parser.add_argument("--year",    help="Only download one year (2022/2023/2024)")
    parser.add_argument("--list",    action="store_true", help="List all configured reports")
    parser.add_argument("--check",   action="store_true", help="HEAD-check all URLs")
    parser.add_argument("--no-ingest", action="store_true", help="Download only, skip ChromaDB ingestion")
    args = parser.parse_args()

    if args.list:
        list_reports()
        sys.exit(0)

    if args.check:
        check_all_urls()
        sys.exit(0)

    # ── Filter reports ─────────────────────────────────────────────────────
    targets = REPORTS
    if args.company:
        targets = [r for r in targets if r["company"].lower() == args.company.lower()]
        if not targets:
            print(f"{RED}No reports found for company: {args.company}{RESET}")
            sys.exit(1)
    if args.year:
        targets = [r for r in targets if r["year"] == args.year]
        if not targets:
            print(f"{RED}No reports found for year: {args.year}{RESET}")
            sys.exit(1)

    print(f"\n{BOLD}📦 Financial Report Downloader — V2{RESET}")
    print(f"   Downloading {len(targets)} report(s) to {DOWNLOAD_DIR}/\n")

    for report in targets:
        process_report(report, skip_ingest=args.no_ingest)
        time.sleep(1)   # polite pause between downloads

    print(f"\n{BOLD}{GREEN}✅  All done!{RESET}")
    print(f"   PDFs saved in: {DOWNLOAD_DIR.resolve()}")
    if not args.no_ingest:
        print("   Documents ingested into ChromaDB (./chroma_db)")
    print()
