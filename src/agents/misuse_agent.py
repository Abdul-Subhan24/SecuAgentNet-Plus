# src/agents/misuse_agent.py
"""
Misuse & Scam Analysis Agent (rule-based starter).
Input: original CSV row (dict) and detection_message (output of detection_agent_run)
Output: structured message with:
 - misuse_label (one of scholarship/loan/invoice/job/harassment/social_engineering/benign)
 - confidence (0-1)
 - explanation
"""

from typing import Dict, Any
from src.agents.detection_agent import safe_str

def misuse_agent_run(row: Dict[str, Any], detection_msg: Dict[str, Any]) -> Dict[str, Any]:
    content = safe_str(row.get("content")).lower()
    kind = safe_str(row.get("kind")).lower()
    attachment = safe_str(row.get("attachment_type")).lower()

    # heuristics
    score = 0.0
    label = "benign"
    reasons = []

    # scholarship signals
    if any(w in content for w in ("scholarship", "apply here", "limited seats")):
        label = "scholarship_scam"
        score = max(score, 0.75)
        reasons.append("scholarship keywords")

    # loan signals
    if any(w in content for w in ("loan", "kYC", "loan approved", "interest")):
        label = "loan_scam" if score < 0.75 else label
        score = max(score, 0.7)
        reasons.append("loan keywords")

    # invoice / payment signals
    if any(w in content for w in ("invoice", "payment", "pay now", "payment method", "payroll")) or attachment in ("pdf","docx"):
        label = "invoice_fraud" if score < 0.7 else label
        score = max(score, 0.65)
        reasons.append("invoice/payment cues or attachment")

    # job scam
    if any(w in content for w in ("offer letter", "candidate", "job", "interview", "hire")):
        label = "job_scam" if score < 0.65 else label
        score = max(score, 0.6)
        reasons.append("job/offer wording")

    # harassment / social engineering
    if any(w in content for w in ("harass", "blackmail", "threat", "shocking reveal", "coerce")):
        # escalate harassment
        label = "harassment"
        score = max(score, 0.8)
        reasons.append("harassment keywords")

    # cross-check detection agent tag
    det_tags = detection_msg.get("tags", []) if detection_msg else []
    if "phishing" in det_tags and score < 0.6:
        # detection says phishing but we didn't find a specific misuse type
        label = "phishing"
        score = max(score, detection_msg.get("score", 0.5))

    # fallback small confidence if suspicious but not matched
    if label == "benign" and ("suspicious" in det_tags or detection_msg.get("score", 0) >= 0.35):
        label = "suspicious"
        score = max(score, detection_msg.get("score", 0.4))
        reasons.append("detection_agent_signals")

    # produce explanation text
    explanation = "; ".join(reasons) if reasons else "no strong misuse indicators; may be benign"

    out = {
        "message_id": f"misuse-{safe_str(row.get('incident_id'))}",
        "from_agent": "misuse_agent",
        "incident_id": safe_str(row.get("incident_id")),
        "misuse_label": label,
        "confidence": round(min(max(score, 0.0), 0.99), 2),
        "explanation": explanation,
        "metadata": {
            "kind": kind,
            "detection_tags": det_tags
        }
    }
    return out
