# src/agents/detection_agent.py
"""
Detection Agent tailored for `synthetic_incidents_professional.csv`.

Responsibilities:
- Extract URLs/domains from 'link' and from free-text 'content'
- Compute a phishing/scam confidence score (0.0 - 1.0) using heuristics
- Flag PII presence and suspicious attachments
- Return a structured, agent-to-agent message (A2A style)
"""

import math
import re
from urllib.parse import urlparse
from typing import Dict, Any


# --------------------
# Safe helpers
# --------------------
def safe_str(x):
    """Return a safe string for possibly-NaN / None inputs."""
    try:
        if x is None:
            return ""
        s = str(x)
        if s.lower() in ("nan", "nat"):
            return ""
        return s
    except Exception:
        return ""


def extract_urls_from_text(text: str):
    text = safe_str(text)
    if not text:
        return []
    return re.findall(r"https?://[^\s)]+", text)


def normalize_domain(url: str):
    url = safe_str(url)
    if not url:
        return ""
    try:
        return urlparse(url).netloc
    except Exception:
        return ""


# --------------------
# Scoring & evidence
# --------------------
def compute_phishing_score(row: Dict[str, Any]) -> float:
    """
    Heuristic score composed from:
    - explicit link presence
    - suspicious keywords
    - attachment type (pdf/docx often used in invoice scams)
    - PII presence
    - kind (email > sms > document > social)
    Returns float between 0 and 1.
    """
    score = 0.0
    content = safe_str(row.get("content")).lower()
    kind = safe_str(row.get("kind")).lower()
    attachment = safe_str(row.get("attachment_type")).lower()
    # handle boolean-like or missing has_link
    has_link = bool(row.get("has_link")) and safe_str(row.get("link")) != ""
    link_text = safe_str(row.get("link")).strip()

    # base by kind
    if kind == "email":
        score += 0.25
    elif kind == "sms":
        score += 0.10
    elif kind == "document":
        score += 0.05

    # link presence
    if has_link or link_text:
        score += 0.30

    # suspicious keywords
    risky_words = [
        "verify", "suspend", "reset", "urgent", "account will be",
        "payment", "invoice", "confirm", "limited seats", "apply here",
        "loan approved", "redeem", "kyc", "ksy"  # typo catch
    ]
    matches = sum(1 for w in risky_words if w in content)
    score += min(0.4, 0.12 * matches)  # each match adds up to cap

    # suspicious attachment types
    if attachment in ("pdf", "docx"):
        score += 0.10

    # PII increases sensitivity: raise score slightly
    try:
        pii = int(row.get("pii_present") or 0)
    except Exception:
        pii = 0
    if pii:
        score += 0.05

    # clamp and return
    score = max(0.0, min(score, 0.99))
    return round(score, 2)


def build_evidence(row: Dict[str, Any], iocs: Dict[str, Any], score: float):
    evidence = []
    content_lower = safe_str(row.get("content")).lower()
    if iocs.get("urls"):
        evidence.append("contains_url")
    if any(k in content_lower for k in ("verify", "suspend", "reset", "urgent", "invoice", "payment")):
        evidence.append("suspicious_keywords")
    if safe_str(row.get("attachment_type")).lower() in ("pdf", "docx"):
        evidence.append("suspicious_attachment")
    try:
        if int(row.get("pii_present") or 0):
            evidence.append("pii_present")
    except Exception:
        pass
    if score >= 0.6:
        evidence.append("high_confidence_rule")
    elif score >= 0.35:
        evidence.append("medium_confidence_rule")
    return evidence


# --------------------
# Main agent interface
# --------------------
def detection_agent_run(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input: row dict from CSV (columns as keys)
    Output: A2A structured message:
      {
        "message_id": "...",
        "from_agent": "detection_agent",
        "incident_id": "...",
        "iocs": {...},
        "score": 0.72,
        "tags": [...],
        "evidence_chain": [...],
        "metadata": {...}
      }
    """
    incident_id = safe_str(row.get("incident_id") or row.get("incidentId") or "<unknown>")

    # extract urls from explicit link field and from text
    urls = []
    if safe_str(row.get("link")):
        urls.append(safe_str(row.get("link")))
    text_urls = extract_urls_from_text(row.get("content"))
    for u in text_urls:
        if u not in urls:
            urls.append(u)
    domains = [normalize_domain(u) for u in urls if normalize_domain(u)]

    iocs = {"urls": urls, "domains": domains}

    score = compute_phishing_score(row)

    tags = []
    if score >= 0.6:
        tags.append("phishing")
    elif score >= 0.35:
        tags.append("suspicious")
    else:
        tags.append("benign")

    evidence = build_evidence(row, iocs, score)

    message = {
        "message_id": f"detection-{incident_id}",
        "from_agent": "detection_agent",
        "incident_id": incident_id,
        "iocs": iocs,
        "score": score,
        "tags": tags,
        "evidence_chain": evidence,
        "metadata": {
            "kind": safe_str(row.get("kind")),
            "sender": safe_str(row.get("sender")),
            "recipient": safe_str(row.get("recipient")),
            "attachment_type": safe_str(row.get("attachment_type")),
            "pii_present": int(safe_str(row.get("pii_present") or 0) != "" and int(row.get("pii_present") or 0))
        }
    }
    return message


# quick local test when executed directly
if __name__ == "__main__":
    sample = {
        "incident_id": "test0001",
        "kind": "email",
        "content": "Urgent: Your account will be suspended. Click https://secure-bank.com/?id=abc123 to verify now. Invoice attached.",
        "attachment_type": "pdf",
        "has_link": True,
        "link": "https://secure-bank.com/?id=abc123",
        "pii_present": 1
    }
    import json
    print(json.dumps(detection_agent_run(sample), indent=2))
