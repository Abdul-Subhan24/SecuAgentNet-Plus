# src/agents/deepfake_agent.py
"""
Deepfake & Media Integrity Agent (starter heuristics).
Input: original CSV row (dict) and optional detection_msg.
Output: structured message with:
 - deepfake_prob (0-1)
 - tag ('deepfake' / 'benign' / 'suspect_media')
 - explanation
"""

from typing import Dict, Any
from src.agents.detection_agent import safe_str

def deepfake_agent_run(row: Dict[str, Any], detection_msg: Dict[str, Any] = None) -> Dict[str, Any]:
    content = safe_str(row.get("content")).lower()
    attachment = safe_str(row.get("attachment_type")).lower()
    df_flag = int(row.get("deepfake_flag") or 0)

    score = 0.0
    reasons = []

    # start with dataset-provided flag (ground-truth-ish) as a prior
    if df_flag:
        score += 0.6
        reasons.append("dataset_deepfake_flag")

    # media attachments (mp4/jpg/png) increase chance
    if attachment in ("mp4", "jpg", "png"):
        score += 0.15
        reasons.append(f"attachment_type:{attachment}")

    # keyword cues
    if any(k in content for k in ("face swap", "deepfake", "voice clone", "audio clone", "fake video", "shocking reveal", "leaked")):
        score += 0.2
        reasons.append("deepfake keywords")

    # detection message influence (if detection says 'phishing' and media present, lower trust)
    if detection_msg and "phishing" in detection_msg.get("tags", []):
        score += 0.05
        reasons.append("detection_phishing_signal")

    score = min(score, 0.99)
    tag = "benign"
    if score >= 0.6:
        tag = "deepfake"
    elif score >= 0.35:
        tag = "suspect_media"

    explanation = "; ".join(reasons) if reasons else "no deepfake indicators"

    return {
        "message_id": f"deepfake-{safe_str(row.get('incident_id'))}",
        "from_agent": "deepfake_agent",
        "incident_id": safe_str(row.get("incident_id")),
        "deepfake_prob": round(score, 2),
        "tag": tag,
        "explanation": explanation,
        "metadata": {"attachment_type": attachment}
    }
