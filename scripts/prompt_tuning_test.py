# scripts/prompt_tuning_test.py
"""
Prompt tuning harness: run detection_agent_llm_run over a small sample with different prompts.

Usage:
  python -m scripts.prompt_tuning_test    # runs mock mode (no API keys)
  python -m scripts.prompt_tuning_test --real --provider openai  # runs real LLM calls (set OPENAI_API_KEY)
"""

import argparse
from pathlib import Path
import json
import os
import statistics

# import the llm detection agent and override PROMPT_TEMPLATE at runtime
from src.agents import detection_agent_llm as dal
from src.agents.detection_agent_llm import detection_agent_llm_run
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT / "data" / "synthetic_incidents_professional.csv"
OUT_DIR = PROJECT / "reports" / "prompt_tuning"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Prompt variants (paste exactly same strings as provided)
PROMPTS = {
    "A": """You are a security analysis assistant that MUST return a single JSON object and nothing else.

Given the incident metadata and content, return a JSON object with exactly these keys:
- threat_type: one of ["phishing","benign","suspicious","malware","unknown"]
- confidence: float between 0.0 and 1.0 (two decimals)
- iocs: an object with keys "urls" (list) and "domains" (list)
- explanation: short human-readable explanation (1-2 sentences)

Return ONLY the JSON object, with no surrounding text.

Input metadata:
{metadata}

Content:
\"\"\"{content}\"\"\"""",
    "B": """You are a security analysis assistant. You MUST output exactly one JSON object and nothing else.

Return JSON matching this exact schema (do not add any fields):
{
  "threat_type": <string: one of ["phishing","benign","suspicious","malware","unknown"]>,
  "confidence": <number: 0.00 - 1.00 (two decimals)>,
  "iocs": {"urls": [<strings>], "domains": [<strings>]},
  "explanation": <string: 1-2 short sentences>
}

If you are uncertain, choose "suspicious" and give a conservative confidence (≤0.6). Do not output commentary or markdown — JSON only.

Metadata:
{metadata}

Content:
\"\"\"{content}\"\"\"""",
    "C": """You are a security analyst that must return a JSON object ONLY (no text). Use the schema shown and follow examples.

Schema:
{"threat_type":"phishing|benign|suspicious|malware|unknown","confidence":0.00,"iocs":{"urls":[],"domains":[]},"explanation":"..."}

Examples (DO NOT REPEAT these in output):
1) Input: "Urgent: verify account at https://bank.example/login"  
   -> {"threat_type":"phishing","confidence":0.88,"iocs":{"urls":["https://bank.example/login"],"domains":["bank.example"]},"explanation":"Contains urgent call-to-action plus a link to a banking domain."}

2) Input: "Happy birthday! Check this photo"  
   -> {"threat_type":"benign","confidence":0.10,"iocs":{"urls":[],"domains":[]},"explanation":"No suspicious cues or links."}

Now analyze this input and output a single JSON object following the schema exactly.

Metadata:
{metadata}

Content:
\"\"\"{content}\"\"\"""",
    "D": """You are a conservative security assistant. Return ONE JSON object (no extra text).

Rules:
- If you are not confident (>0.7) that content is malicious, prefer "suspicious" or "benign".
- If you find explicit links or threatening payment/invoice language, raise confidence.
- Always include any URLs/domains you observed in the "iocs" field.

Schema:
{"threat_type":"phishing|benign|suspicious|malware|unknown","confidence":0.00,"iocs":{"urls":[],"domains":[]},"explanation":"..."}

Metadata:
{metadata}

Content:
\"\"\"{content}\"\"\""""
}

def run_variant(variant, sample_rows, provider, model, mock):
    results = []
    # override the module-level prompt template used by detection_agent_llm
    dal.PROMPT_TEMPLATE = PROMPTS[variant]
    for row in sample_rows:
        msg = detection_agent_llm_run(row, provider=provider, model=model, mock=mock)
        results.append(msg)
    # write outputs
    var_dir = OUT_DIR / variant
    var_dir.mkdir(parents=True, exist_ok=True)
    for r in results:
        with open(var_dir / f"{r['incident_id']}.json", "w", encoding="utf8") as fh:
            json.dump(r, fh, indent=2)
    # summary
    counts = {}
    confidences = []
    for r in results:
        t = r.get("tags", ["unknown"])[0]
        counts[t] = counts.get(t, 0) + 1
        confidences.append(float(r.get("score", 0) or 0))
    avg_conf = statistics.mean(confidences) if confidences else 0.0
    return {"variant": variant, "counts": counts, "avg_confidence": round(avg_conf, 2)}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--real", action="store_true", help="Call real LLM provider (requires API key).")
    parser.add_argument("--provider", default="openai", choices=["openai","ollama"], help="LLM provider.")
    parser.add_argument("--model", default=None, help="Model name override.")
    args = parser.parse_args()

    if not DATA_FILE.exists():
        print("ERROR: data file missing.")
        return

    df = pd.read_csv(DATA_FILE)
    # sample 12 rows for quick testing (preserve variety)
    sample = df.sample(12, random_state=7).to_dict(orient="records")

    provider = args.provider
    model = args.model
    mock = not args.real

    print("Running prompt tuning with mock=" + str(mock))
    summaries = []
    for v in PROMPTS.keys():
        print("Running variant", v)
        summaries.append(run_variant(v, sample, provider, model, mock))

    # print compact table
    print("\nSummary table:")
    for s in summaries:
        print(s)

if __name__ == "__main__":
    main()
