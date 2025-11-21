<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>SecuAgentNet+: AI Multi-Agent Platform — Md Abdul Subhan</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&family=Source+Serif+4:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
  <meta name="author" content="Md Abdul Subhan" />
  <style>
    :root{
      --bg:#0f1724; /* deep navy */
      --card:#0b1220;
      --muted:#9aa4b2;
      --accent:#6ee7b7;
      --accent-2:#7dd3fc;
      --glass: rgba(255,255,255,0.04);
      --radius:14px;
      --maxw:1100px;
      color-scheme: dark;
    }
    *{box-sizing:border-box}
    html,body{height:100%;margin:0;font-family:Inter,system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial; background:linear-gradient(180deg,#071021 0%,var(--bg) 60%); color:#e6eef6}
    .wrap{max-width:var(--maxw);margin:36px auto;padding:28px;border-radius:18px;background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));box-shadow:0 10px 40px rgba(2,6,23,0.6);backdrop-filter: blur(6px);}
    header{display:flex;gap:20px;align-items:center}
    .title{flex:1}
    h1{margin:0;font-weight:800;font-size:22px;letter-spacing:-0.2px}
    .subtitle{margin-top:6px;color:var(--muted);font-size:13px}
    .meta{display:flex;gap:12px;align-items:center}
    .chip{background:var(--glass);padding:8px 12px;border-radius:999px;font-size:13px;color:var(--muted)}
    .hero{display:flex;gap:20px;margin-top:20px}
    .left{flex:1}
    .card{background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));padding:18px;border-radius:12px;border:1px solid rgba(255,255,255,0.02);box-shadow:0 8px 30px rgba(2,6,23,0.4)}
    .kpi{display:flex;gap:14px;flex-wrap:wrap}
    .kpi .item{min-width:140px;padding:12px;background:linear-gradient(90deg, rgba(255,255,255,0.01), rgba(255,255,255,0.00));border-radius:10px}
    .section{margin-top:20px}
    h2{margin:0 0 10px 0;font-family: 'Source Serif 4', serif;font-weight:600}
    p.lead{color:var(--muted);margin:0 0 12px 0}
    .grid{display:grid;grid-template-columns:1fr 320px;gap:18px}
    .toc{font-size:14px;padding:12px;border-radius:10px;background:linear-gradient(180deg, rgba(13,20,30,0.4), rgba(7,12,18,0.2));}
    ul{margin:0 0 12px 18px}
    pre{background:#071022;padding:14px;border-radius:10px;overflow:auto;font-family:ui-monospace, SFMono-Regular, Menlo, Monaco, 'Roboto Mono', monospace}
    table{width:100%;border-collapse:collapse;margin-top:8px}
    th,td{padding:8px;border-bottom:1px dashed rgba(255,255,255,0.03);text-align:left}
    .badge{display:inline-block;padding:6px 10px;border-radius:999px;background:transparent;border:1px solid rgba(255,255,255,0.03);font-size:13px;color:var(--muted)}
    .diagram{font-family:ui-monospace,monospace;background:linear-gradient(180deg, rgba(255,255,255,0.01), rgba(255,255,255,0.00));padding:12px;border-radius:10px}
    footer{display:flex;justify-content:space-between;align-items:center;margin-top:22px;color:var(--muted);font-size:13px}
    a.btn{display:inline-block;padding:10px 14px;border-radius:10px;background:linear-gradient(90deg,var(--accent),var(--accent-2));color:#042029;font-weight:700;text-decoration:none}
    @media (max-width:880px){.grid{grid-template-columns:1fr}.hero{flex-direction:column}.wrap{margin:18px}}
  </style>
</head>
<body>
  <main class="wrap">
    <header>
      <div class="title">
        <h1>SecuAgentNet+: AI Multi‑Agent Platform for Threat Detection, Fraud Prevention &amp; Digital Safety</h1>
        <div class="subtitle">Author: <strong>Md Abdul Subhan</strong> — Kaggle Agents Intensive Capstone 2025 | Track: Freestyle (Enterprise + Safety Hybrid)</div>
      </div>
      <div class="meta">
        <div class="chip">Multi-Agent • Hybrid Detection • AURA Governance</div>
        <div class="chip">LLM + Rule Engine</div>
      </div>
    </header>

    <section class="hero">
      <div class="left">
        <div class="card">
          <h2>Abstract</h2>
          <p class="lead">SecuAgentNet+ is a hybrid AI-driven security and safety platform designed to detect phishing, fraud, AI‑generated misuse, and digital threats impacting individuals, students, families, healthcare workers, small businesses, and enterprises. It simulates an enterprise-grade incident pipeline while addressing real‑world harms such as job scams, deepfakes, fake documents, phishing, and fraud attempts.</p>

          <div class="section">
            <h2>Problem Statement</h2>
            <ul>
              <li>New AI-enabled attack vectors (phishing websites, smishing, deepfakes, fake credentials).</li>
              <li>Targeted scams (students, job seekers, healthcare records).</li>
              <li>Resource gap: non-enterprise users lack SOC tools; enterprises face alert overload.</li>
            </ul>
          </div>

          <div class="section">
            <h2>Solution Overview</h2>
            <p class="lead">A multi-agent security platform combining rule-based detection, LLM reasoning (OpenAI/Gemini/Ollama), and a hybrid engine that cross-verifies results to reduce false positives and provide SOC-like behavior.</p>
            <div class="kpi" style="margin-top:10px">
              <div class="item"><strong>Core</strong><div class="badge" style="margin-top:6px">Hybrid Detection Engine</div></div>
              <div class="item"><strong>Governance</strong><div class="badge" style="margin-top:6px">AURA-style HITL</div></div>
              <div class="item"><strong>Outputs</strong><div class="badge" style="margin-top:6px">JSON incidents &amp; Audit Logs</div></div>
            </div>
          </div>

          <div class="section">
            <h2>Multi-Agent Architecture</h2>
            <p class="lead">The platform contains dedicated agents for detection, governance, triage and reporting. Each agent is specialized and logs decisions for auditability.</p>
            <table>
              <thead><tr><th>Agent</th><th>Responsibility</th></tr></thead>
              <tbody>
                <tr><td>Rule-Based Detection Agent</td><td>Extract URLs, detect phishing indicators, heuristics scoring</td></tr>
                <tr><td>LLM Detection Agent</td><td>LLM classification → structured JSON</td></tr>
                <tr><td>Hybrid Detection Engine</td><td>Rule → LLM cross-check (threshold gating)</td></tr>
                <tr><td>Misuse &amp; Scam Analysis Agent</td><td>Fake offers, docs, fraud SMS, social engineering</td></tr>
                <tr><td>Deepfake Integrity Agent</td><td>Media manipulation screening (simulated)</td></tr>
                <tr><td>Safety &amp; Social Harm Agent</td><td>Harassment, blackmail, intimidation detection</td></tr>
                <tr><td>Triage Agent</td><td>Assign severity: Low / Medium / High / Critical</td></tr>
                <tr><td>Governance Agent (AURA)</td><td>Autonomy score, HITL rules, data sensitivity</td></tr>
                <tr><td>Anti-Hallucination Agent</td><td>Schema validation &amp; cross-checks</td></tr>
                <tr><td>Reporting Agent</td><td>Final incident report &amp; timeline</td></tr>
              </tbody>
            </table>
          </div>

          <div class="section">
            <h2>Hybrid Detection Engine (Core Innovation)</h2>
            <ol>
              <li><strong>Rule-Based Detection</strong>: URL extraction, risky keywords, attachment type, PII detection — compute rule_score (0–1).</li>
              <li><strong>Threshold Check</strong>: if rule_score ∈ [0.35, 0.95] → activate LLM Detection.</li>
              <li><strong>LLM Review</strong>: LLM returns JSON classification, IoCs, confidence, and reasoning.</li>
              <li><strong>Final Score</strong>: final_score = (rule_score * 0.4) + (llm_confidence * 0.6).</li>
            </ol>
            <p class="lead">This hybrid formula reduces false positives and creates more realistic SOC behavior.</p>
          </div>

          <div class="section">
            <h2>Governance (AURA-Style)</h2>
            <p class="lead">Autonomy Risk Score (0–100) computed from data sensitivity, threat impact, reversibility, confidence, presence of personal data, and LLM usage. HITL rules determine whether a human analyst must intervene.</p>
            <ul>
              <li>Score &gt; 60 — Human analyst required</li>
              <li>Score 40–60 — Allowed with warnings</li>
              <li>Score &lt; 40 — Auto-response (simulated)</li>
            </ul>
          </div>

          <div class="section">
            <h2>Evaluation Highlights</h2>
            <table>
              <tbody>
                <tr><td>Precision</td><td>0.4203</td></tr>
                <tr><td>Recall</td><td>0.7843</td></tr>
                <tr><td>F1</td><td>0.5473</td></tr>
                <tr><td>ROC AUC</td><td>0.7342</td></tr>
                <tr><td>Threshold</td><td>0.6</td></tr>
                <tr><td>High risk incidents</td><td>351</td></tr>
                <tr><td>Governance HITL compliance</td><td>1.0</td></tr>
              </tbody>
            </table>
          </div>

          <div class="section">
            <h2>Directory Structure (example)</h2>
            <pre>secuagentnet-plus/
├── data/
│   └── synthetic_incidents_professional.csv
├── logs/
│   └── audit_*.json
├── reports/
│   ├── metrics.json
│   ├── detection_roc.png
│   └── detection_score_distribution.png
├── scripts/
│   ├── run_detection_test.py
│   ├── run_detection_llm_test.py
│   ├── run_pipeline_full.py
│   ├── prompt_tuning_test.py
│   └── evaluate.py
└── src/
    ├── agents/
    │   ├── detection_agent.py
    │   ├── detection_agent_llm.py
    │   ├── governance_agent.py
    │   ├── misuse_agent.py
    │   ├── triage_agent.py
    │   └── …
    └── utils/</pre>
          </div>

          <div class="section">
            <h2>How to Run (developer notes)</h2>
            <ol>
              <li>Activate virtual environment — <code>.\venv\Scripts\Activate.ps1</code> (Windows) or <code>source venv/bin/activate</code> (Unix).</li>
              <li>Run hybrid pipeline — <code>python -m scripts.run_pipeline_full</code></li>
              <li>Run evaluation — <code>python -m scripts.evaluate</code></li>
              <li>Test LLM detection (mock) — <code>python -m scripts.run_detection_llm_test</code></li>
              <li>Prompt tuning tests — <code>python -m scripts.prompt_tuning_test</code></li>
            </ol>
          </div>

        </div>

        <div class="section card" style="margin-top:14px">
          <h2>Future Enhancements</h2>
          <ul>
            <li>Vision model for real deepfake detection</li>
            <li>Integrate Gemini Flash / Claude 3 Haiku for latency-sensitive LLMs</li>
            <li>Vector embedding memory for repeated fraud patterns</li>
            <li>FastAPI backend + Streamlit demo UI</li>
            <li>Production Dockerization &amp; SOC dashboard</li>
          </ul>
        </div>

        <div class="section card" style="margin-top:14px">
          <h2>Conclusion</h2>
          <p class="lead">SecuAgentNet+ demonstrates a functional multi-agent security pipeline that combines rule-based detection with LLM reasoning, includes governance and audit layers, and supports SOC-style triage and reporting. The project highlights capabilities in Data Science, Python, security automation, and AI governance.</p>
          <p style="margin-top:10px"><strong>Author:</strong> Md Abdul Subhan</p>
        </div>

      </div>

      <aside class="card" style="width:320px">
        <h2>Quick Contents</h2>
        <div class="toc">
          <strong>Contents</strong>
          <ul>
            <li>Abstract</li>
            <li>Problem Statement</li>
            <li>Solution Overview</li>
            <li>Multi-Agent Architecture</li>
            <li>Hybrid Engine</li>
            <li>Governance</li>
            <li>Evaluation</li>
            <li>How to Run</li>
          </ul>
        </div>

        <div style="margin-top:12px">
          <h3 style="margin:0 0 8px 0">System Diagram (text)</h3>
          <div class="diagram">
<pre>Input Incident
 (email, sms, doc, upload)
    ↓
Hybrid Detection
 (Rule Engine + LLM)
    ↓
Misuse &amp; Fraud Analysis
    ↓
Safety / Deepfake Agent
    ↓
Triage
    ↓
Governance (AURA)
    ↓
Reporting Agent</pre>
          </div>

          <div style="margin-top:12px">
            <a class="btn" href="#">Export HTML</a>
            <div style="margin-top:8px;color:var(--muted);font-size:13px">Tip: Copy the page source and save as <code>secuagentnet-plus.html</code>.</div>
          </div>
        </div>

      </aside>
    </section>

    <footer>
      <div>SecuAgentNet+ — AI Multi-Agent Platform • Author: Md Abdul Subhan</div>
      <div style="text-align:right">Prepared for Kaggle Agents Intensive Capstone 2025</div>
    </footer>
  </main>
</body>
</html>
