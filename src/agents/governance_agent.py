# src/agents/governance_agent.py
"""
AURA-style Governance & Risk Scoring Agent.
Inputs: detection_msg, misuse_msg, deepfake_msg, original row
Outputs: governance decision with autonomy risk score (0-100),
         recommended automation allowance, policy_constraints, justification
"""

from typing import Dict, Any

def aura_score(sensitivity: float, impact: float, confidence: float) -> float:
    """
    Simple weighted AURA score (0-100).
    sensitivity, impact, confidence are 0.0-1.0
    Higher score = higher risk (more human oversight needed)
    """
    # weights can be tuned; demonstrated values
    score = 100.0 * (0.5 * sensitivity + 0.35 * impact + 0.15 * (1 - confidence))
    return round(max(0.0, min(score, 100.0)), 2)


def governance_agent_run(row: Dict[str, Any],
                         detection_msg: Dict[str, Any],
                         misuse_msg: Dict[str, Any],
                         deepfake_msg: Dict[str, Any]) -> Dict[str, Any]:
    # compute sensitivity: PII presence, medical, government doc increase sensitivity
    sensitivity = 0.0
    kind = (row.get("kind") or "").lower()
    if int(row.get("pii_present") or 0):
        sensitivity = max(sensitivity, 0.8)
    if kind in ("document",):
        sensitivity = max(sensitivity, 0.7)
    if misuse_msg.get("misuse_label") in ("invoice_fraud", "loan_scam", "phishing"):
        sensitivity = max(sensitivity, 0.6)
    if misuse_msg.get("misuse_label") in ("harassment",):
        # harassment has privacy & safety implications
        sensitivity = max(sensitivity, 0.9)

    # compute impact: financial/hospital/identity -> high
    impact = 0.0
    if misuse_msg.get("misuse_label") in ("invoice_fraud", "loan_scam"):
        impact = max(impact, 0.8)
    if misuse_msg.get("misuse_label") == "phishing":
        impact = max(impact, 0.6)
    if deepfake_msg.get("tag") == "deepfake":
        impact = max(impact, 0.7)
    # detection confidence reduces uncertainty
    detection_conf = float(detection_msg.get("score", 0) or 0)

    # compute AURA score
    autonomy_risk = aura_score(sensitivity, impact, detection_conf)

    # governance rules & constraints
    policy_constraints = []
    allow_automation = False
    justification = []

    # if autonomy risk is high => disallow automation, require HITL
    if autonomy_risk >= 70:
        allow_automation = False
        policy_constraints.append("HITL_required")
        justification.append("High autonomy risk; manual review required")
    elif autonomy_risk >= 40:
        allow_automation = False
        policy_constraints.append("Limited_automation")
        justification.append("Moderate autonomy risk; escalate to analyst")
    else:
        allow_automation = True
        policy_constraints.append("Automation_allowed_under_monitoring")
        justification.append("Low autonomy risk; automation permitted")

    # Additional constraints for deepfake / harassment
    if deepfake_msg.get("tag") == "deepfake":
        policy_constraints.append("Preserve_evidence; No_publication_without_HITL")
        justification.append("Deepfake detected; preserve evidence and escalate")
    if misuse_msg.get("misuse_label") == "harassment":
        policy_constraints.append("Immediate_support_and_privacy_measures")
        justification.append("Harassment detected; privacy & support required")

    out = {
        "message_id": f"governance-{row.get('incident_id')}",
        "from_agent": "governance_agent",
        "incident_id": row.get("incident_id"),
        "autonomy_risk_score": autonomy_risk,
        "allow_automation": allow_automation,
        "policy_constraints": policy_constraints,
        "justification": " ; ".join(justification),
        "metadata": {
            "sensitivity": sensitivity,
            "impact": impact,
            "detection_confidence": detection_conf
        }
    }
    return out
