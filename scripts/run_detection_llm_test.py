# scripts/run_detection_llm_test.py
"""
Test the LLM-backed detection agent on a few sample incidents.
Usage:
  python -m scripts.run_detection_llm_test
"""
from pathlib import Path
import pandas as pd
from src.agents.detection_agent_llm import detection_agent_llm_run

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_ROOT / "data" / "synthetic_incidents_professional.csv"

def main():
    if not DATA_FILE.exists():
        print("ERROR: data file not found. Run generator first.")
        return
    df = pd.read_csv(DATA_FILE)
    sample = df.sample(5, random_state=1).to_dict(orient="records")
    # Quick test: use mock=True to avoid API calls (set mock=False when you have keys)
    for row in sample:
        out = detection_agent_llm_run(row, provider="openai", model=None, mock=True)
        import json
        print(json.dumps(out, indent=2, ensure_ascii=False))
        print("-"*60)

if __name__ == "__main__":
    main()
