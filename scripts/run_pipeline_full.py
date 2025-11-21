# scripts/run_pipeline_full.py
"""
Full orchestrator with hybrid detection (rule-based -> optional LLM re-check).

Usage examples (from project root, venv active):

# hybrid mode, mock LLM (safe, default)
python -m scripts.run_pipeline_full --mode hybrid

# hybrid mode, real LLM provider (use small sample only until you check costs)
python -m scripts.run_pipeline_full --mode hybrid --real --provider openai --model gpt-4o-mini

# force rule-only
python -m scripts.run_pipeline_full --mode rule

# force llm-only (use with caution)
python -m scripts.run_pipeline_full --mode llm --real --provider openai --model gpt-4o-mini

Notes:
- In hybrid mode: rule-based detection runs first. If rule_score >= llm_trigger_threshold,
  the LLM detection will be called. Final detection is chosen using confidence heuristics.
- Audit logs (one JSON per incident) are written to logs/.
"""

import argparse
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import math

# Agents (both rule-based and LLM)
from src.agents.detection_agent import detection_agent_run as detection_agent_rule_run
from src.agents.detection_agent_llm import detection_agent_llm_run as detection_agent_llm_run
from src.agents.misuse_agent import misuse_agent_run
from src.agents.deepfake_agent import deepfake_agent_run
from src.agents.crosscheck_agent import crosscheck_agent_run
from src.agents.governance_agent import governance_agent_run

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_ROOT / "data" / "synthetic_incidents_professional.csv"
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Configuration defaults
DEFAULT_MODE = "hybrid"  # "rule", "llm", "hybrid"
# If rule score >= this threshold, call LLM to re-check (hybrid mode)
LLM_TRIGGER_THRESHOLD = 0.45
# If LLM returns, compare scores with this margin; if LLM higher by margin -> pick LLM
LLM_PREFERENCE_MARGIN = 0.02
# Max incidents to run (None == all). Useful for testing
DEFAULT_SAMPLE_SIZE = None  # set to e.g., 20 for small runs

def choose_final_detection(rule_msg, llm_msg):
    """
    Decide final detection message given rule_msg and llm_msg (llm_msg may be None).
    Strategy:
      - If llm_msg is None: return rule_msg
      - If both present: compare numeric scores (0-1). Prefer the one with higher score,
        unless scores equal (then prefer LLM for richer evidence).
      - Keep both messages in audit under 'detection.rule' and 'detection.llm'.
    Returns: final_msg, metadata dict with 'chosen_by' and both messages included.
    """
    meta = {"chosen_by": "rule_only", "rule_msg": rule_msg, "llm_msg": llm_msg}
    if llm_msg is None:
        meta["chosen_by"] = "rule_only"
        return rule_msg, meta

    # numeric scores safe extraction
    try:
        r_score = float(rule_msg.get("score", 0) or 0)
    except Exception:
        r_score = 0.0
    try:
        l_score = float(llm_msg.get("score", 0) or 0)
    except Exception:
        l_score = 0.0

    # preference logic
    if math.isclose(l_score, r_score, rel_tol=LLM_PREFERENCE_MARGIN):
        chosen = llm_msg  # prefer LLM when scores are very close (richer evidence)
        meta["chosen_by"] = "llm_tie_preference"
    elif l_score > r_score + LLM_PREFERENCE_MARGIN:
        chosen = llm_msg
        meta["chosen_by"] = "llm_higher_confidence"
    else:
        chosen = rule_msg
        meta["chosen_by"] = "rule_higher_confidence"

    return chosen, meta

def process_incident(row, mode="hybrid", provider="openai", model=None, mock=True):
    """
    Process a single incident row.
    mode: "rule", "llm", "hybrid"
    provider/model/mock: passthrough to LLM agent
    Returns audit dict.
    """
    incident_id = row.get("incident_id") or row.get("incidentId") or "<unknown>"

    # 1) Run rule-based detection (always run to keep audit)
    rule_msg = detection_agent_rule_run(row)

    # 2) Decide whether to call LLM (based on mode and thresholds)
    llm_msg = None
    if mode == "llm":
        # llm-only: call LLM directly
        llm_msg = detection_agent_llm_run(row, provider=provider, model=model, mock=mock)
    elif mode == "hybrid":
        # hybrid: call LLM only if rule score >= LLM_TRIGGER_THRESHOLD
        try:
            r_score = float(rule_msg.get("score", 0) or 0)
        except Exception:
            r_score = 0.0
        if r_score >= LLM_TRIGGER_THRESHOLD:
            llm_msg = detection_agent_llm_run(row, provider=provider, model=model, mock=mock)
        else:
            llm_msg = None
    else:
        llm_msg = None  # rule-only

    # 3) Choose final detection message
    final_det, det_meta = choose_final_detection(rule_msg, llm_msg)

    # 4) Continue with other agents using final_det
    misuse = misuse_agent_run(row, final_det)
    deepfake = deepfake_agent_run(row, final_det)
    cross = crosscheck_agent_run(row, final_det, misuse, deepfake)
    governance = governance_agent_run(row, final_det, misuse, deepfake)

    # 5) Triage (simple rules) using governance + detection signals
    def simple_triage(dec_msg, misuse_msg, deepfake_msg, gov_msg, row):
        det_score = dec_msg.get("score", 0)
        misuse_conf = misuse_msg.get("confidence", 0)
        deep_prob = deepfake_msg.get("deepfake_prob", 0) if isinstance(deepfake_msg.get("deepfake_prob", None), (int, float)) else (deepfake_msg.get("probability", 0) or 0)
        manual = row.get("manual_severity", "")

        if gov_msg.get("autonomy_risk_score", 0) >= 70:
            return {"recommended_severity": "high", "reason": "Governance: HITL_required"}
        if deepfake_msg.get("tag") == "deepfake" or misuse_msg.get("misuse_label") == "harassment":
            return {"recommended_severity": "high", "reason": "deepfake or harassment detected"}
        if det_score >= 0.7 or misuse_conf >= 0.75 or deep_prob >= 0.6:
            return {"recommended_severity": "high", "reason": "strong signals"}
        if det_score >= 0.45 or misuse_conf >= 0.45 or deep_prob >= 0.35:
            return {"recommended_severity": "medium", "reason": "moderate signals"}
        return {"recommended_severity": manual if manual else "low", "reason": "no strong automated signals"}

    triage = simple_triage(final_det, misuse, deepfake, governance, row)

    # 6) Build audit
    audit = {
        "run_ts": datetime.utcnow().isoformat() + "Z",
        "incident": {
            "incident_id": incident_id,
            "kind": row.get("kind"),
            "sender": row.get("sender"),
            "recipient": row.get("recipient"),
            "manual_severity": row.get("manual_severity")
        },
        "agents": {
            "detection": {
                "final": final_det,
                "rule": rule_msg,
                "llm": llm_msg,
                "selection_meta": det_meta
            },
            "misuse": misuse,
            "deepfake": deepfake,
            "crosscheck": cross,
            "governance": governance,
            "triage": triage
        }
    }

    out_path = LOG_DIR / f"audit_{incident_id}.json"
    with open(out_path, "w", encoding="utf8") as fh:
        json.dump(audit, fh, indent=2, ensure_ascii=False)

    # print compact line for CLI
    gov_score = governance.get("autonomy_risk_score") if governance else None
    print(f"{incident_id} | kind={row.get('kind')} | recommended={triage['recommended_severity']} | gov_score={gov_score}")

    return audit

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["rule", "llm", "hybrid"], default=DEFAULT_MODE, help="Detection mode")
    parser.add_argument("--real", action="store_true", help="Call real LLM provider (requires API key).")
    parser.add_argument("--provider", default="openai", choices=["openai", "ollama"], help="LLM provider")
    parser.add_argument("--model", default=None, help="LLM model name (provider-specific)")
    parser.add_argument("--sample", type=int, default=DEFAULT_SAMPLE_SIZE, help="Process first N incidents (for testing)")
    args = parser.parse_args()

    if not DATA_FILE.exists():
        print("ERROR: data file not found.")
        return

    df = pd.read_csv(DATA_FILE)
    print(f"Loaded {len(df)} incidents")

    # sample selection
    if args.sample:
        sample_rows = df.head(args.sample).to_dict(orient="records")
    else:
        sample_rows = df.to_dict(orient="records")

    provider = args.provider
    model = args.model
    mock = not args.real

    audits = []
    for row in sample_rows:
        audits.append(process_incident(row, mode=args.mode, provider=provider, model=model, mock=mock))

    # summary counts
    counts = {}
    for a in audits:
        r = a["agents"]["triage"]["recommended_severity"]
        counts[r] = counts.get(r, 0) + 1
    print("SUMMARY:", counts)
    print("Audit logs:", LOG_DIR.resolve())

if __name__ == "__main__":
    main()
