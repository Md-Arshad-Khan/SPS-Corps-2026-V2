"""
llm_client.py  –  V2
Thin wrapper around Ollama with JSON-mode extraction and retry logic.
"""
import json
import re
import time
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MAX_ATTEMPTS = 3


def call_ollama(model: str, prompt: str, timeout: int = 120) -> dict:
    """
    Call an Ollama model and return a parsed JSON dict.
    Falls back to {"raw": <text>} if the response is not valid JSON.
    """
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            resp = requests.post(
                OLLAMA_URL,
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=timeout,
            )
            resp.raise_for_status()
            raw_text = resp.json().get("response", "")

            # ── Try to extract JSON from the response ─────────────────────
            # 1. Look for a JSON code-block
            block = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.S)
            json_str = block.group(1) if block else raw_text

            # 2. Grab the outermost {...}
            brace_match = re.search(r"\{.*\}", json_str, re.S)
            if brace_match:
                return json.loads(brace_match.group())

            return {"raw": raw_text}

        except (requests.RequestException, json.JSONDecodeError) as exc:
            if attempt == MAX_ATTEMPTS:
                return {"error": str(exc), "raw": ""}
            time.sleep(1)

    return {"error": "max retries exceeded"}


def extract_text(result: dict) -> str:
    """Return the best string from a call_ollama result dict."""
    for key in ("answer", "analysis", "response", "raw"):
        if key in result and result[key]:
            return str(result[key])
    return " | ".join(f"{k}: {v}" for k, v in result.items() if v)
