"""
retriever.py  –  V2
Supports:
  - Plain retrieval (V1-style, no filters)
  - Filtered retrieval by company and/or year (new in V2)
  - Bulk retrieval for all (company, year) pairs in a query
"""
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Optional

COLLECTION_NAME = "financial_docs_v2"
DEFAULT_N = 5


def _get_collection():
    client = chromadb.PersistentClient(path="./chroma_db")
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
    )


def retrieve(
    query: str,
    company: Optional[str] = None,
    year: Optional[str] = None,
    n_results: int = DEFAULT_N,
) -> str:
    """
    Retrieve relevant passages.
    If company/year are provided, filter the ChromaDB collection accordingly.
    Returns a single string with passages separated by '---'.
    """
    collection = _get_collection()

    where: dict = {}
    if company and year:
        where = {"$and": [{"company": company}, {"year": year}]}
    elif company:
        where = {"company": company}
    elif year:
        where = {"year": year}

    kwargs = {
        "query_texts": [query],
        "n_results": min(n_results, collection.count() or 1),
    }
    if where:
        kwargs["where"] = where

    results = collection.query(**kwargs)
    passages = results["documents"][0] if results["documents"] else []
    return "\n\n---\n\n".join(passages) if passages else "[No relevant data found]"


def retrieve_multi(
    query: str,
    companies: List[str],
    years: List[str],
    n_results: int = DEFAULT_N,
) -> dict:
    """
    Retrieve context for every (company, year) combination.
    Returns a dict: {"Apple_2024": "<text>", "Microsoft_2024": "<text>", ...}
    """
    contexts: dict = {}
    for company in companies:
        for year in years:
            key = f"{company}_{year}"
            contexts[key] = retrieve(query, company=company, year=year, n_results=n_results)
    return contexts
