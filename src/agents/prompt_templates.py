# src/agents/prompt_templates.py
"""
Prompt templates and helpers for the LLM detection agent.

The LLM MUST return strict JSON. This file provides:
- DEFAULT_PROMPT: safe fallback used when no env var is provided
- PROMPT_VARIANTS: dict mapping 'A','B','C','D' -> template strings (for prompt tuning)
- get_prompt_from_variant(variant) helper
"""

import json
from textwrap import dedent

DEFAULT_PROMPT = dedent("""
You are a security analyst assistant. Given the incident content and metadata, return a single JSON object (no extra text)
that strictly follows this schema:

{
  "threat_type": "<one of: benign, phishing, job_scam, invoice_fraud, harassment, deepfake, fake_doc, scam_sms, suspicious>",
  "confidence": <float between 0.0 and 1.0>,
  "iocs": {
    "urls": [ "<url1>", "<url2>", ... ],
    "domains": [ "<domain1>", "<domain2>", ... ]
  },
  "explanation": "<one-sentence explanation for the classification>"
}

Important rules:
1) Output must be valid JSON and nothing else.
2) confidence must be a single float between 0 and 1 (e.g. 0.78).
3) If you find no URLs/domains, provide empty lists.
4) Keep explanation short (<= 30 words).

Input format (for your reference):
- metadata: JSON object with fields like sender, attachment_type, has_link
- content: the incident text or description

Return only the JSON object as specified above.
""").strip()

PROMPT_VARIANTS = {
    "A": DEFAULT_PROMPT,
    "B": dedent("""
        You are an expert SOC analyst. Provide a strict single-line JSON with fields:
        threat_type, confidence (0-1), iocs {urls, domains}, explanation (short).
        Use concise reasoning and prefer higher recall for suspicious cases.
    """).strip(),
    "C": dedent("""
        Use a conservative policy: prefer to label unknown-low-signal items as 'suspicious' not 'phishing'.
        Still return strict JSON as specified.
    """).strip(),
    "D": dedent("""
        Use brief output, but include more IoC extraction. Return JSON with fields exactly:
        threat_type, confidence, iocs, explanation.
    """).strip(),
}

def get_prompt_from_variant(variant: str) -> str:
    """Return the prompt string for a variant letter (A/B/C/D). Defaults to DEFAULT_PROMPT."""
    return PROMPT_VARIANTS.get(variant.upper(), DEFAULT_PROMPT)
