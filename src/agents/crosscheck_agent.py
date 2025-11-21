# src/agents/crosscheck_agent.py
"""
Cross-Check & Anti-Hallucination Agent (starter).
Performs consistency checks among agent outputs and flags contradictions/hallucinations.
Inputs: detection_msg, misuse_msg, deepfake_msg, original row
Outputs: validation result with `ok: bool`, list of `issues`, and `corrective_suggestions`
"""

from typing import Dict, Any
from src.agents.detection_agent import safe_str

def crosscheck_agent_run(row: Dict[str, Any],
                         detection_msg: Dict[str, Any],
                         misuse_msg: Dict[str, Any],
                         deepfake_msg: Dict[str, Any]) -> Dict[str, Any]:
    issues = []
    suggestions = []

    # 1. If detection tags are 'benign' and misuse flags 'harassment' or 'phishing', warn
    if "benign" in detection_msg.get("tags", []) and misuse_msg.get("misuse_label") in ("phishing","harassment","invoice_fraud"):
        issues.append("Detection marked benign but misuse agent found high-risk label")
        suggestions.append("Re-check detection thresholds or escalate to HITL")

    # 2. If deepfake tag is 'deepfake' but no media attachment present -> suspicious
    attachment = safe_str(row.get("attachment_type"))
    if deepfake_msg.get("tag") == "deepfake" and attachment == "none":
        issues.append("Deepfake flagged but no media attachment present")
        suggestions.append("Verify dataset flag; check media file hashes")

    # 3. If multiple agents disagree strongly (e.g., detection score low, misuse_conf high) -> flag
    det_score = float(detection_msg.get("score", 0) or 0)
    misuse_conf = float(misuse_msg.get("confidence", 0) or 0)
    if det_score < 0.35 and misuse_conf >= 0.7:
        issues.append("High misuse confidence with low detection score")
        suggestions.append("Run additional enrichment (WHOIS, domain reputation) and retry")

    # 4. If fields are missing in messages -> warn
    if not detection_msg.get("iocs"):
        issues.append("No IOCs found by detection agent")
        suggestions.append("Add more heuristics or call LLM for extraction")

    ok = len(issues) == 0

    return {
        "message_id": f"crosscheck-{row.get('incident_id')}",
        "from_agent": "crosscheck_agent",
        "incident_id": row.get("incident_id"),
        "ok": ok,
        "issues": issues,
        "corrective_suggestions": suggestions
    }
