# scripts/evaluate.py
"""
Evaluation driver adapted to use hybrid detection (rule -> optional LLM check).

Usage examples (project root, venv active):

# Safe mock hybrid (default)
python -m scripts.evaluate --mode hybrid

# Real LLM hybrid on small sample (costly — use --sample to limit)
python -m scripts.evaluate --mode hybrid --real --provider openai --model gpt-4o-mini --sample 50

# Rule-only evaluation
python -m scripts.evaluate --mode rule

# LLM-only evaluation (calls LLM for all incidents)
python -m scripts.evaluate --mode llm --real --provider openai --model gpt-4o-mini --sample 50
"""

from pathlib import Path
import json
import argparse
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, classification_report

# agent imports (rule + llm)
from src.agents.detection_agent import detection_agent_run as detection_agent_rule_run
from src.agents.detection_agent_llm import detection_agent_llm_run as detection_agent_llm_run
from src.agents.misuse_agent import misuse_agent_run
from src.agents.deepfake_agent import deepfake_agent_run
from src.agents.governance_agent import governance_agent_run

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_ROOT / "data" / "synthetic_incidents_professional.csv"
REPORT_DIR = PROJECT_ROOT / "reports"
REPORT_DIR.mkdir(exist_ok=True)

# Hybrid config (mirror of run_pipeline_full.py)
LLM_TRIGGER_THRESHOLD = 0.45
LLM_PREFERENCE_MARGIN = 0.02

# Helper: safe str for NaN/None
def safe_str(x):
    try:
        if x is None:
            return ""
        s = str(x)
        if s.lower() in ("nan", "nat"):
            return ""
        return s
    except Exception:
        return ""

def choose_final_detection(rule_msg, llm_msg):
    """Same decision rules used in pipeline."""
    meta = {"chosen_by": "rule_only", "rule_msg": rule_msg, "llm_msg": llm_msg}
    if llm_msg is None:
        meta["chosen_by"] = "rule_only"
        return rule_msg, meta
    try:
        r_score = float(rule_msg.get("score", 0) or 0)
    except Exception:
        r_score = 0.0
    try:
        l_score = float(llm_msg.get("score", 0) or 0)
    except Exception:
        l_score = 0.0

    if math.isclose(l_score, r_score, rel_tol=LLM_PREFERENCE_MARGIN):
        chosen = llm_msg
        meta["chosen_by"] = "llm_tie_preference"
    elif l_score > r_score + LLM_PREFERENCE_MARGIN:
        chosen = llm_msg
        meta["chosen_by"] = "llm_higher_confidence"
    else:
        chosen = rule_msg
        meta["chosen_by"] = "rule_higher_confidence"
    return chosen, meta

def run_evaluation(mode="hybrid", provider="openai", model=None, real=False, sample=None):
    if not DATA_FILE.exists():
        print("ERROR: data file not found at", DATA_FILE)
        return

    df = pd.read_csv(DATA_FILE)
    n = len(df)
    print(f"Loaded {n} incidents for evaluation")

    if sample:
        df = df.head(sample)

    # containers for detection metrics
    detection_scores = []
    detection_labels = []

    # misuse predictions
    misuse_preds = []
    misuse_truth = []

    # governance
    governance_scores = []
    governance_allow = []

    # triage truth (if available)
    triage_truth = []

    PHISHING_LIKE = set([
        "phishing", "invoice_fraud", "scam_sms", "loan_scam",
        "job_scam", "scholarship_scam"
    ])

    # mapping for ground truth misuse labels (same as earlier implementation)
    GROUND_TO_MISUSE = {
        "phishing": "phishing",
        "invoice_fraud": "invoice_fraud",
        "scam_sms": "scam_sms",
        "loan_scam": "loan_scam",
        "job_scam": "job_scam",
        "scholarship_scam": "scholarship_scam",
        "fake_doc": "fake_doc",
        "deepfake_media": "deepfake",
        "harassment": "harassment",
        "benign": "benign",
        "social_engineering": "social_engineering",
        "legit_doc": "benign"
    }

    def safe_map_ground_to_misuse(label):
        return GROUND_TO_MISUSE.get(label, "other")

    mock = not real

    for _, row in df.iterrows():
        rowd = row.to_dict()

        # 1) run rule detection always for audit and hybrid decision
        rule_msg = detection_agent_rule_run(rowd)

        # 2) decide whether to call LLM depending on mode
        llm_msg = None
        if mode == "llm":
            llm_msg = detection_agent_llm_run(rowd, provider=provider, model=model, mock=mock)
        elif mode == "hybrid":
            try:
                r_score = float(rule_msg.get("score", 0) or 0)
            except Exception:
                r_score = 0.0
            if r_score >= LLM_TRIGGER_THRESHOLD:
                llm_msg = detection_agent_llm_run(rowd, provider=provider, model=model, mock=mock)
            else:
                llm_msg = None
        else:
            llm_msg = None

        # 3) choose final detection message
        final_det, det_meta = choose_final_detection(rule_msg, llm_msg)

        # 4) misuse, deepfake, governance (reuse same functions)
        misuse = misuse_agent_run(rowd, final_det)
        deepfake = deepfake_agent_run(rowd, final_det)
        governance = governance_agent_run(rowd, final_det, misuse, deepfake) if callable(governance_agent_run) else governance_agent_run(rowd, final_det, misuse, deepfake)

        # accumulate metrics for detection
        detection_scores.append(float(final_det.get("score", 0.0)))
        label_cat = safe_str(rowd.get("label_category"))
        detection_labels.append(1 if label_cat in PHISHING_LIKE else 0)

        # misuse
        misuse_preds.append(misuse.get("misuse_label"))
        misuse_truth.append(safe_map_ground_to_misuse(label_cat))

        # governance
        governance_scores.append(float(governance.get("autonomy_risk_score", 0.0)))
        governance_allow.append(bool(governance.get("allow_automation")))

        triage_truth.append(safe_str(rowd.get("ground_truth_severity", "")))

    # compute detection metrics
    y_true = np.array(detection_labels)
    y_scores = np.array(detection_scores)
    y_pred = (y_scores >= 0.6).astype(int)

    detection_precision = precision_score(y_true, y_pred, zero_division=0)
    detection_recall = recall_score(y_true, y_pred, zero_division=0)
    detection_f1 = f1_score(y_true, y_pred, zero_division=0)
    try:
        detection_auc = roc_auc_score(y_true, y_scores)
    except Exception:
        detection_auc = None

    misuse_report_str = classification_report(misuse_truth, misuse_preds, zero_division=0)

    gov_scores = np.array(governance_scores)
    gov_allow = np.array(governance_allow)
    high_risk_mask = gov_scores >= 70.0
    if high_risk_mask.sum() > 0:
        gov_compliance = float(((~gov_allow) & high_risk_mask).sum()) / float(high_risk_mask.sum())
    else:
        gov_compliance = None

    metrics = {
        "mode": mode,
        "n_incidents": int(len(df)),
        "detection": {
            "precision": float(detection_precision),
            "recall": float(detection_recall),
            "f1": float(detection_f1),
            "roc_auc": float(detection_auc) if detection_auc is not None else None,
            "threshold": 0.6
        },
        "governance": {
            "total_high_risk_cases": int(high_risk_mask.sum()),
            "governance_compliance_hitl": gov_compliance
        }
    }

    with open(REPORT_DIR / "metrics.json", "w", encoding="utf8") as fh:
        json.dump(metrics, fh, indent=2)
    print("Saved metrics ->", REPORT_DIR / "metrics.json")

    # plots
    plt.figure(figsize=(7,4))
    plt.hist(y_scores[y_true==0], bins=30, alpha=0.6, label="non-phishing")
    plt.hist(y_scores[y_true==1], bins=30, alpha=0.6, label="phishing-like")
    plt.legend()
    plt.title("Detection score distribution")
    plt.xlabel("detection score")
    plt.ylabel("count")
    plt.tight_layout()
    plt.savefig(REPORT_DIR / "detection_score_distribution.png")
    plt.close()
    print("Saved plot -> detection_score_distribution.png")

    if detection_auc is not None:
        from sklearn.metrics import roc_curve
        fpr, tpr, _ = roc_curve(y_true, y_scores)
        plt.figure(figsize=(6,6))
        plt.plot(fpr, tpr, label=f"AUC={detection_auc:.3f}")
        plt.plot([0,1],[0,1], linestyle="--", color="gray")
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.title("Detection ROC")
        plt.legend()
        plt.tight_layout()
        plt.savefig(REPORT_DIR / "detection_roc.png")
        plt.close()
        print("Saved plot -> detection_roc.png")

    with open(REPORT_DIR / "misuse_classification_report.txt", "w", encoding="utf8") as fh:
        fh.write(misuse_report_str)
    print("Saved misuse classification report -> misuse_classification_report.txt")

    print("Evaluation summary:")
    print(json.dumps(metrics, indent=2))
    print("Reports saved in", REPORT_DIR.resolve())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["rule","llm","hybrid"], default="hybrid")
    parser.add_argument("--real", action="store_true", help="Call real LLM provider (requires API key).")
    parser.add_argument("--provider", default="openai", choices=["openai","ollama"])
    parser.add_argument("--model", default=None)
    parser.add_argument("--sample", type=int, default=None, help="Limit number of incidents processed (useful for cost control)")
    args = parser.parse_args()

    run_evaluation(mode=args.mode, provider=args.provider, model=args.model, real=args.real, sample=args.sample)

if __name__ == "__main__":
    main()
