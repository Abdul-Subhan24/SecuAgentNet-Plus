# src/llm/llm_client.py
"""
LLM client wrapper supporting:
 - OpenAI (via openai Python package)
 - Ollama (local HTTP API)
 - MOCK mode (for offline testing)

Usage:
  from src.llm.llm_client import call_llm
  resp = call_llm(prompt, provider="openai", model="gpt-4o-mini")
"""

import os
import time
import json
import re
import requests

# Try to import OpenAI SDK if present
try:
    import openai
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

# Environment config
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")  # must be set for OpenAI usage
DEFAULT_OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")  # override if desired

# Simple retry wrapper
def _retry(func, retries=2, backoff=0.5):
    for attempt in range(retries):
        try:
            return func()
        except Exception as e:
            last_exc = e
            time.sleep(backoff * (1 + attempt))
    raise last_exc

# Safe JSON extractor: finds first {...} block and parses it
def extract_json_from_text(text):
    if not isinstance(text, str):
        return None
    # find the first JSON object in text
    match = re.search(r"\{(?:[^{}]|(?R))*\}", text, re.DOTALL)
    if not match:
        # fallback: try to locate a substring starting with '{' and ending with '}'
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end+1])
            except Exception:
                return None
        return None
    try:
        return json.loads(match.group())
    except Exception:
        # as a last resort, try to fix common single quotes -> double
        s = match.group().replace("'", '"')
        try:
            return json.loads(s)
        except Exception:
            return None

# MAIN function that other code will call
def call_llm(prompt: str,
             provider: str = "openai",
             model: str = None,
             max_tokens: int = 512,
             temperature: float = 0.0,
             mock: bool = False,
             timeout: int = 30):
    """
    Call an LLM and return a dict: {"raw_text": str, "json": Dict or None}
    provider: "openai" | "ollama"
    mock: if True, returns a canned response (useful for offline testing)
    """
    if mock:
        # return a conservative canned response to let pipeline run locally
        canned = {
            "raw_text": '{"threat_type": "phishing", "confidence": 0.78, "iocs": {"urls":["https://example.com"], "domains":["example.com"]}, "explanation":"Contains urgent+link"}',
            "json": {"threat_type": "phishing", "confidence": 0.78, "iocs": {"urls":["https://example.com"], "domains":["example.com"]}, "explanation":"Mock response"}
        }
        return canned

    if provider == "openai":
        if not OPENAI_AVAILABLE:
            raise RuntimeError("OpenAI SDK not installed. pip install openai")
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY environment variable not set.")
        model = model or DEFAULT_OPENAI_MODEL
        def _call():
            openai.api_key = OPENAI_API_KEY
            # use Chat Completions (compat)
            resp = openai.ChatCompletion.create(
                model=model,
                messages=[{"role":"system","content":"You are a concise, structured JSON generator for threat detection."},
                          {"role":"user","content":prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return resp.choices[0].message["content"]
        raw = _retry(_call, retries=2)
        parsed = extract_json_from_text(raw)
        return {"raw_text": raw, "json": parsed}

    elif provider == "ollama":
        model = model or "llama2"  # change if you have a specific model
        url = f"{OLLAMA_HOST}/api/generate"
        payload = {"model": model, "prompt": prompt, "max_tokens": max_tokens, "temperature": temperature}
        def _call():
            r = requests.post(url, json=payload, timeout=timeout)
            r.raise_for_status()
            data = r.json()
            # Ollama returns text in different shapes depending on versions
            # Try to find text
            txt = data.get("text") or (data.get("results")[0].get("content") if data.get("results") else None) or json.dumps(data)
            return txt
        raw = _retry(_call, retries=2)
        parsed = extract_json_from_text(raw)
        return {"raw_text": raw, "json": parsed}

    else:
        raise ValueError(f"Unknown provider: {provider}")
