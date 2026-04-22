"""
ingestor.py  –  V2
Ingests one PDF at a time and tags each chunk with:
  - company  (e.g. "Apple")
  - year     (e.g. "2024")
  - source   (filename)

Usage:
    python ingestor.py <path_to_pdf> --company Apple --year 2024

The collection name is always "financial_docs_v2" so V2 and V1 stay separate.
"""
import argparse
import sys
import uuid
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader

COLLECTION_NAME = "financial_docs_v2"
CHUNK_SIZE = 800        # characters per chunk
CHUNK_OVERLAP = 150     # character overlap between chunks


# ── Chunking ──────────────────────────────────────────────────────────────────

def extract_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap
    return chunks


# ── ChromaDB ──────────────────────────────────────────────────────────────────

def get_collection():
    client = chromadb.PersistentClient(path="./chroma_db")
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
    )


def ingest(pdf_path: str, company: str, year: str):
    path = Path(pdf_path)
    if not path.exists():
        print(f"❌  File not found: {pdf_path}")
        sys.exit(1)

    print(f"📄  Reading {path.name} …")
    text = extract_text(pdf_path)
    chunks = chunk_text(text)
    print(f"   → {len(chunks)} chunks extracted")

    collection = get_collection()

    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [
        {"company": company.strip(), "year": year.strip(), "source": path.name}
        for _ in chunks
    ]

    collection.add(documents=chunks, ids=ids, metadatas=metadatas)
    print(f"✅  Ingested {len(chunks)} chunks  →  company={company}, year={year}")
    print(f"   Collection now has {collection.count()} total documents.")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest a financial PDF into ChromaDB (V2)")
    parser.add_argument("pdf", help="Path to the PDF file")
    parser.add_argument("--company", required=True, help='Company name, e.g. "Apple"')
    parser.add_argument("--year", required=True, help='Fiscal year, e.g. "2024"')
    args = parser.parse_args()

    ingest(args.pdf, args.company, args.year)
