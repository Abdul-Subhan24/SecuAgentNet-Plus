# src/agents/detection_agent_llm.py
"""
LLM-backed Detection Agent.
It calls the llm_client with a structured prompt and expects JSON in return.
Fallbacks to rule-based heuristics if LLM response is missing.
"""

from typing import Dict, Any
from src.llm.llm_client import call_llm
from src.agents.detection_agent import compute_phishing_score, extract_urls_from_text, normalize_domain, safe_str


PROMPT_TEMPLATE = PROMPT_TEMPLATE = PROMPT_B = """
You are a security analysis assistant. You MUST output exactly one JSON object and nothing else.

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
\"\"\"{content}\"\"\"
"""



def parse_llm_output(resp):
    if not resp:
        return None
    return resp.get("json")

def detection_agent_llm_run(row: Dict[str, Any],
                            provider: str = "openai",
                            model: str = None,
                            mock: bool = False) -> Dict[str, Any]:
    """
    Calls LLM and returns the same A2A structured message format as detection_agent_run.
    If LLM returns no JSON, falls back to compute_phishing_score heuristics.
    """
    incident_id = safe_str(row.get("incident_id") or "<unknown>")
    metadata = {
        "kind": safe_str(row.get("kind")),
        "sender": safe_str(row.get("sender")),
        "attachment_type": safe_str(row.get("attachment_type")),
        "has_link": bool(row.get("has_link"))
    }
    content = safe_str(row.get("content"))

    # prompt = PROMPT_TEMPLATE.format(metadata=json_safe(metadata), content=content)
    # safer substitution that avoids interpreting other braces in the prompt
    prompt = PROMPT_TEMPLATE.replace("{metadata}", json_safe(metadata)).replace("{content}", content)


    # call LLM
    try:
        resp = call_llm(prompt, provider=provider, model=model, mock=mock, temperature=0.0)
        parsed = parse_llm_output(resp)
    except Exception as e:
        parsed = None

    # If parsed JSON exists and is valid, use it
    if parsed and isinstance(parsed, dict):
        urls = parsed.get("iocs", {}).get("urls", []) or []
        domains = parsed.get("iocs", {}).get("domains", []) or []
        # ensure lists
        if not isinstance(urls, list):
            urls = [urls]
        if not isinstance(domains, list):
            domains = [domains]
        score = float(parsed.get("confidence") or 0.0)
        threat = parsed.get("threat_type") or ("phishing" if score >= 0.6 else "suspicious" if score >= 0.35 else "benign")
        evidence = [parsed.get("explanation")] if parsed.get("explanation") else []
        message = {
            "message_id": f"detection-llm-{incident_id}",
            "from_agent": "detection_agent_llm",
            "incident_id": incident_id,
            "iocs": {"urls": urls, "domains": domains},
            "score": round(score, 2),
            "tags": [threat],
            "evidence_chain": evidence,
            "metadata": metadata,
            "raw_llm": resp.get("raw_text")
        }
        return message

    # Fallback: use existing heuristic compute_phishing_score
    fallback_score = compute_phishing_score(row)
    urls = []
    if safe_str(row.get("link")):
        urls.append(safe_str(row.get("link")))
    text_urls = extract_urls_from_text(content)
    for u in text_urls:
        if u not in urls:
            urls.append(u)
    domains = [normalize_domain(u) for u in urls if normalize_domain(u)]
    tags = ["phishing"] if fallback_score >= 0.6 else ["suspicious"] if fallback_score >= 0.35 else ["benign"]
    message = {
        "message_id": f"detection-heuristic-{incident_id}",
        "from_agent": "detection_agent_heuristic_fallback",
        "incident_id": incident_id,
        "iocs": {"urls": urls, "domains": domains},
        "score": fallback_score,
        "tags": tags,
        "evidence_chain": ["fallback_heuristic"],
        "metadata": metadata
    }
    return message

# small helper to safely stringify metadata as JSON inside prompt
import json
def json_safe(obj):
    try:
        return json.dumps(obj, ensure_ascii=False)
    except Exception:
        return str(obj)
