# **SecuAgentNet+**
**AI Multi-Agent Platform for Threat Detection, Fraud Prevention & Digital Safety**

**Author:** Md Abdul Subhan  
**Track:** Kaggle Agents Intensive Capstone 2025 — Freestyle (Enterprise + Safety Hybrid)

---

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-proof%20of%20concept-green)](#)

## Table of Contents
1. [Project Overview](#project-overview)
2. [Problem Statement](#problem-statement)
3. [Solution Summary](#solution-summary)
4. [Multi-Agent Architecture](#multi-agent-architecture)
5. [Hybrid Detection Engine (Core Innovation)](#hybrid-detection-engine-core-innovation)
6. [Governance (AURA-Style)](#governance-aura-style)
7. [Evaluation Results](#evaluation-results)
8. [Directory Structure](#directory-structure)
9. [How to Run](#how-to-run)
10. [Prompt Tuning & LLMs](#prompt-tuning--llms)
11. [Future Enhancements](#future-enhancements)
12. [Contributing & License](#contributing--license)

---

## Project Overview
**SecuAgentNet+** is a hybrid AI-driven security & safety platform designed to detect phishing, fraud, AI-generated misuse (deepfakes, forged documents), and other digital threats affecting individuals and enterprises. Built as a Kaggle Capstone (Agents Intensive 2025), the project demonstrates a multi-agent pipeline combining rule engines, LLM reasoning and governance for auditable incident handling.

The project focuses on:
- Reducing false positives with a rule + LLM hybrid detection pipeline.
- Providing an AURA-style governance layer (autonomy scoring + HITL rules).
- Producing structured JSON incidents, audit logs and evaluation metrics suitable for SOC-like workflows.

---

## Problem Statement
Modern AI has enabled novel attack vectors that are difficult for traditional heuristics alone:
- Phishing websites, smishing and credential-harvesting campaigns
- Deepfake media and manipulated multimedia targeting vulnerable groups
- Fake hospital certificates, insurance claims, and admission documents
- Scholarship and job scams targeting students and job-seekers
- Ransom/blackmail messages and fraudulent parcel/OTP scams

Non-technical users lack enterprise SOC tooling while enterprises suffer alert overload and analyst fatigue. There is a need for a universal, AI-powered digital safety assistant that is auditable, explainable and governed.

---

## Solution Summary
SecuAgentNet+ implements a multi-agent system with the following capabilities:
- Rule-based prefiltering for fast, explainable signals.
- LLM-based review for nuanced classification and IoC extraction.
- Hybrid scoring formula that weights rule and LLM confidences.
- Governance agent to compute autonomy risk and enforce HITL rules.
- Audit logs and reporting agent to generate incident timelines and structured outputs.

**Design goals:** auditable decisions, human-in-the-loop where necessary, JSON structured outputs for downstream automation.

---

## Multi-Agent Architecture
**Agents & Responsibilities** (compact):

| # | Agent | Responsibility |
|---:|---|---|
| 1 | Rule-Based Detection Agent | Extract URLs, heuristics, PII detection, compute `rule_score` (0–1) |
| 2 | LLM Detection Agent | Structured JSON classification (phishing/benign/suspicious/malware), extract IoCs |
| 3 | Hybrid Detection Engine | Gate: rule → LLM when threshold crossed; compute `final_score` |
| 4 | Misuse & Scam Analysis Agent | Detect job scams, fake docs, fraud SMS, social engineering patterns |
| 5 | Deepfake Integrity Agent | Media manipulation screening (simulated in this project) |
| 6 | Safety & Social Harm Agent | Harassment, blackmail detection, content safety scoring |
| 7 | Triage Agent | Assign severity: Low / Medium / High / Critical |
| 8 | Governance Agent (AURA) | Autonomy score, HITL determination, data sensitivity assessment |
| 9 | Anti-Hallucination Agent | Validate LLM outputs against schemas, cross-checks with rules |
| 10 | Reporting Agent | Compile final incident report, timeline, recommendations |

Agents are modular, observable, and emit audit entries for every decision step.

---

## Hybrid Detection Engine (Core Innovation)
**Workflow**:
1. **Rule-Based Detection**  
   - Extract URLs, suspect keywords ("verify", "urgent", "payment"), attachment types, PII indicators.  
   - Compute `rule_score` in [0,1].

2. **Threshold Check**  
   - If `rule_score` ∈ [0.35, 0.95] → forward to LLM Detection Agent.

3. **LLM Review**  
   - LLM returns JSON: `{ classification, iocs, confidence, reasoning }`.

4. **Final Score**  
   - `final_score = (rule_score * 0.4) + (llm_confidence * 0.6)`  
   - Action determined by final_score + governance rules.

**Benefits:** reduces false positives, realistic SOC-like triage, retains explainability via rule features and LLM rationale.

---

## Governance (AURA-Style)
**Autonomy Risk Score (0–100)** computed from:
- Data sensitivity
- Threat impact
- Action reversibility
- Confidence quality
- Presence of personal data
- Whether an LLM was used

**HITL Rules:**
- Score > 60 → Human analyst required (HITL)
- 40 ≤ Score ≤ 60 → Allowed with warnings and additional logging
- Score < 40 → Auto-response allowed (simulation only in this repo)

All governance decisions are logged with timestamps and rationale for auditability.

---

## Evaluation Results
**Detection Metrics** (sample results from experiments):

- Precision: `0.4203`
- Recall: `0.7843`
- F1: `0.5473`
- ROC AUC: `0.7342`
- Threshold (decision): `0.6`

**Governance Metrics:**
- High risk incidents: `351`
- Governance HITL compliance: `1.0` (simulated enforcement metric)

> Note: Misuse classification initially uses rule-baseline only. Accuracy will improve when LLM logic is enabled in production.

---

## System Diagram (text)

             ┌────────────────────────────┐
             │       Input Incident        │
             │ (email, sms, doc, upload)   │
             └──────────────┬──────────────┘
                            │
                 ┌──────────▼──────────┐
                 │ Hybrid Detection     │
                 │ Rule Engine + LLM    │
                 └──────────┬──────────┘
                            │
             ┌──────────────▼──────────────┐
             │ Misuse & Fraud Analysis      │
             └──────────────┬──────────────┘
                            │
                  ┌─────────▼─────────┐
                  │ Safety / Deepfake │
                  │     Agent         │
                  └─────────┬─────────┘
                            │
                    ┌───────▼───────┐
                    │   Triage       │
                    └───────┬───────┘
                            │
               ┌────────────▼────────────┐
               │   Governance (AURA)      │
               └────────────┬────────────┘
                            │
                  ┌─────────▼──────────┐
                  │  Reporting Agent    │
                  └─────────────────────┘

---

## Directory Structure

secuagentnet-plus/
├── data/
│ └── synthetic_incidents_professional.csv
├── docs/
│ └── architecture.svg
├── scripts/
│ ├── run_pipeline_full.py
│ ├── evaluate.py
│ └── prompt_tuning_test.py
├── src/
│ ├── agents/
│ └── llm/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
└── notebook.ipynb


---

## How to Run
**Windows (PowerShell)**
```powershell
# create & activate venv (recommended Python 3.11.x)
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# run pipeline (mock mode if you don't want to call LLMs)
python -m scripts.prompt_tuning_test --mock
python -m scripts.run_pipeline_full   # or run individual scripts
python -m scripts.evaluate


**Unix / Mac**
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m scripts.run_pipeline_full


**Notes:**

1. For real LLM runs set your provider environment variables locally (do not commit .env with real keys).

2. Use --mock if you want to avoid external API calls during validation.

**Prompt Tuning & LLMs**

The repo ships with 4 prompt variants (A/B/C/D) used for automated prompt tuning experiments.

Structured output enforcement and schema validation are required to reduce hallucination.

For deployment, configure provider credentials and set model selection in src/agents/detection_agent_llm.py.

**Future Enhancements**

1. Add a vision model for real deepfake detection (beyond simulation).

2. Integrate Gemini Flash / Claude 3 Haiku for low-latency LLM responses.

3. Add vector embedding memory store for repeated fraud patterns and fast lookup.

4. Deploy FastAPI backend and a Streamlit demo front-end for interactive testing.

5. Production Dockerization and SOC dashboard for metrics/alerting.

**Contributing**

Contributions welcome — fork, branch, add tests, and open a PR. Run python -m pytest before submitting.

**License**

Released under the **MIT License**. See LICENSE.

**Author**: Md Abdul Subhan

Prepared for Kaggle Agents Intensive Capstone 2025 — SecuAgentNet+


---

