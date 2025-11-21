# scripts/run_detection_test.py
"""
Load the professional CSV and run detection_agent on a small set of diverse incidents.
Prints structured agent messages for inspection.
"""

import pandas as pd
from pathlib import Path
from src.agents.detection_agent import detection_agent_run

DATA_FILE = Path("data/synthetic_incidents_professional.csv")

def main():
    if not DATA_FILE.exists():
        print("ERROR: data/synthetic_incidents_professional.csv not found.")
        print("Run: python scripts/generate_synthetic_data.py")
        return

    df = pd.read_csv(DATA_FILE)
    n = len(df)
    print(f"Loaded {n} incidents from {DATA_FILE}")

    # pick indices to test coverage: one email, one sms, one document, one social, one upload
    sample = []
    kinds = ["email", "sms", "document", "social", "upload"]
    for k in kinds:
        subset = df[df["kind"] == k]
        if not subset.empty:
            sample.append(subset.sample(1).iloc[0].to_dict())

    # fallback if some kinds missing
    if not sample:
        sample = [df.iloc[i].to_dict() for i in range(min(5, len(df)))]

    for idx, row in enumerate(sample):
        print("\n" + "="*60)
        print(f"TEST INCIDENT #{idx+1} (kind={row.get('kind')}, id={row.get('incident_id')})")
        out = detection_agent_run(row)
        import json
        print(json.dumps(out, indent=2))
        print("="*60 + "\n")

if __name__ == "__main__":
    main()
