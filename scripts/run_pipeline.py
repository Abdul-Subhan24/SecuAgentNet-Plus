# scripts/run_pipeline.py
"""
Simple orchestrator that:
 - loads the professional CSV,
 - for a small sample of incidents runs: detection -> misuse -> deepfake -> simple triage
 - writes a JSON log per incident into logs/
 - prints a human-readable final report.

Run with:
    python -m scripts.run_pipeline
"""

import json
from pathlib import Path
from datetime import datetime
import pandas as pd

# agent imports
from src.agents.detection_agent import detection_agent_run
from src.agents.misuse_agent import misuse_agent_run
from src.agents.deepfake_agent import deepfake_agent_run

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_ROOT / "data" / "synthetic_incidents_professional.csv"
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

def simple_triage(dec_msg, misuse_msg, deepfake_msg, row):
    """
    Basic triage logic that returns recommended severity and action.
    - If deepfake tag is deepfake OR misuse is harassment -> escalate high
    - If detection score high or misuse confidence high -> medium/high
    - else follow manual severity or low
    """
    det_score = dec_msg.get("score", 0)
    misuse_conf = misuse_msg.get("confidence", 0)
    deep_prob = deepfake_msg.get("deepfake_prob", 0)
    manual = row.get("manual_severity", "")

    # baseline
    if deepfake_msg.get("tag") == "deepfake" or misuse_msg.get("misuse_label") == "harassment":
        rec = "high"
        reason = "deepfake or harassment detected"
    elif det_score >= 0.7 or misuse_conf >= 0.75 or deep_prob >= 0.6:
        rec = "high"
        reason = "strong signals from detection/misuse/deepfake"
    elif det_score >= 0.45 or misuse_conf >= 0.45 or deep_prob >= 0.35:
        rec = "medium"
        reason = "moderate signals"
    else:
        rec = manual if manual else "low"
        reason = "no strong automated signals; follow manual severity"

    return {"recommended_severity": rec, "reason": reason}

def process_incident(row):
    # run agents
    det = detection_agent_run(row)
    misuse = misuse_agent_run(row, det)
    deepfake = deepfake_agent_run(row, det)
    triage = simple_triage(det, misuse, deepfake, row)

    report = {
        "run_ts": datetime.utcnow().isoformat() + "Z",
        "incident": {
            "incident_id": row.get("incident_id"),
            "kind": row.get("kind"),
            "sender": row.get("sender"),
            "recipient": row.get("recipient"),
            "manual_severity": row.get("manual_severity")
        },
        "agents": {
            "detection": det,
            "misuse": misuse,
            "deepfake": deepfake,
            "triage": triage
        }
    }

    # write log
    out_path = LOG_DIR / f"{row.get('incident_id')}.json"
    with open(out_path, "w", encoding="utf8") as fh:
        json.dump(report, fh, indent=2)

    # print summary
    print("="*80)
    print(f"Incident {row.get('incident_id')} ({row.get('kind')}) => Recommended severity: {triage['recommended_severity']}")
    print(f"Reason: {triage['reason']}")
    print(f"Detection score: {det.get('score')} | Misuse: {misuse.get('misuse_label')} ({misuse.get('confidence')}) | Deepfake: {deepfake.get('tag')} ({deepfake.get('deepfake_prob')})")
    print(f"Log written: {out_path.resolve()}")
    print("="*80 + "\n")

    return report

def main():
    if not DATA_FILE.exists():
        print("ERROR: data file not found. Run generator first.")
        return

    df = pd.read_csv(DATA_FILE)
    print(f"Loaded {len(df)} incidents from {DATA_FILE}")

    # Process a short sample to test end-to-end (first 8 incidents)
    sample = df.sample(8, random_state=42).to_dict(orient="records")
    reports = []
    for row in sample:
        reports.append(process_incident(row))

    # summary metrics (simple)
    high = sum(1 for r in reports if r["agents"]["triage"]["recommended_severity"] == "high")
    medium = sum(1 for r in reports if r["agents"]["triage"]["recommended_severity"] == "medium")
    low = len(reports) - high - medium
    print("SUMMARY (sample):", {"high": high, "medium": medium, "low": low})
    print("Log files saved in:", LOG_DIR.resolve())

if __name__ == "__main__":
    main()
