#!/usr/bin/env python3
"""
Project Test Harness
Drop this file into the project root and run: python project_test_harness.py

It will:
- Inspect repo structure
- Check .env (without printing values)
- Compile all .py files (syntax check)
- Try safe imports of top-level modules
- Check packages from requirements.txt are installed (using pip show)
- Check CSV files exist in data/
- List scripts and optionally run those that do not require an API key
- Produce a summary report
"""

import os
import sys
import subprocess
import traceback
import compileall
from pathlib import Path
import csv

# --- Configuration: change if your project root is different ---
PROJECT_ROOT = Path(__file__).resolve().parent
# If your extracted folder has a subfolder like "SecuAgentNet-Plus-main", point to it:
# PROJECT_ROOT = Path("/mnt/data/SecuAgentNet-Plus-main")
# --- End configuration ---

expected_dirs = [
    "src",
    "src/agents",
    "src/llm",
    "scripts",
    "data",
    "docs",
]
expected_files = [
    "README.md",
    "requirements.txt",
    ".env.example",
    "notebook.ipynb",
    "convert_notebook.py",
]

report = {
    "found_dirs": [],
    "missing_dirs": [],
    "found_files": [],
    "missing_files": [],
    "env": {},
    "compiled": {"ok": 0, "failed": 0, "errors": []},
    "imports": {"ok": [], "failed": []},
    "requirements": {"checked": [], "missing": []},
    "data_files": [],
    "scripts": {"listed": [], "runcount": 0, "ran": [], "skipped": []},
}

def check_paths():
    for d in expected_dirs:
        p = PROJECT_ROOT / d
        if p.exists() and p.is_dir():
            report["found_dirs"].append(d)
        else:
            report["missing_dirs"].append(d)
    for f in expected_files:
        p = PROJECT_ROOT / f
        if p.exists():
            report["found_files"].append(f)
        else:
            report["missing_files"].append(f)

def read_env():
    env_path = PROJECT_ROOT / ".env"
    example_path = PROJECT_ROOT / ".env.example"
    if env_path.exists():
        # read but don't print values
        with env_path.open() as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k = line.split("=",1)[0].strip()
                    report["env"][k] = "present"
    elif example_path.exists():
        with example_path.open() as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k = line.split("=",1)[0].strip()
                    report["env"][k] = "example"
    else:
        report["env"][".env"] = "missing"

def compile_python_files():
    # compile all .py files under PROJECT_ROOT/src, scripts, and root
    paths = [PROJECT_ROOT / "src", PROJECT_ROOT / "scripts", PROJECT_ROOT]
    for base in paths:
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            try:
                ok = compileall.compile_file(str(p), doraise=True, quiet=1)
                report["compiled"]["ok"] += 1
            except Exception as e:
                report["compiled"]["failed"] += 1
                report["compiled"]["errors"].append({
                    "file": str(p.relative_to(PROJECT_ROOT)),
                    "error": repr(e)
                })

def try_safe_imports():
    # build a small list of top-level packages to try import
    candidates = set()
    # derive from requirements.txt if present
    req = PROJECT_ROOT / "requirements.txt"
    if req.exists():
        for line in req.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-e"):
                continue
            # take package name before version specifiers
            pkg = line.split("==")[0].split(">=")[0].split("<=")[0].strip()
            # map some known keys to import names (heuristic)
            if pkg.lower().startswith("openai"):
                candidates.add("openai")
            elif pkg.lower().startswith("fastapi"):
                candidates.add("fastapi")
            elif pkg.lower().startswith("uvicorn"):
                candidates.add("uvicorn")
            elif pkg.lower().startswith("pandas"):
                candidates.add("pandas")
            else:
                # try raw pkg name
                candidates.add(pkg.split()[0])
    # always try internal modules by adding project src to sys.path
    src_path = PROJECT_ROOT / "src"
    if src_path.exists():
        sys.path.insert(0, str(src_path))
        # attempt to import common project modules
        candidates.update(["llm.llm_client", "agents.detection_agent", "agents.detection_agent_llm"])
    # try imports
    for name in sorted(candidates):
        if not name:
            continue
        try:
            __import__(name)
            report["imports"]["ok"].append(name)
        except Exception as e:
            report["imports"]["failed"].append({"module": name, "error": repr(e)})

def check_requirements_installed():
    req = PROJECT_ROOT / "requirements.txt"
    if not req.exists():
        return
    for line in req.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-e"):
            continue
        pkg = line.split("==")[0].split(">=")[0].split("<=")[0].strip()
        report["requirements"]["checked"].append(pkg)
        try:
            # use pip show
            res = subprocess.run([sys.executable, "-m", "pip", "show", pkg],
                                 capture_output=True, text=True)
            if res.returncode != 0 or not res.stdout:
                report["requirements"]["missing"].append(pkg)
        except Exception:
            report["requirements"]["missing"].append(pkg)

def check_data_files():
    data_dir = PROJECT_ROOT / "data"
    if not data_dir.exists():
        return
    for p in sorted(data_dir.glob("*")):
        if p.is_file():
            info = {"file": str(p.relative_to(PROJECT_ROOT))}
            if p.suffix.lower() == ".csv":
                try:
                    with p.open(newline="", encoding="utf-8") as fh:
                        reader = csv.reader(fh)
                        row_count = sum(1 for _ in reader)
                    info["rows"] = row_count
                except Exception as e:
                    info["error"] = repr(e)
            report["data_files"].append(info)

def list_and_run_scripts():
    scripts_dir = PROJECT_ROOT / "scripts"
    if not scripts_dir.exists():
        return
    for p in sorted(scripts_dir.glob("*.py")):
        report["scripts"]["listed"].append(str(p.relative_to(PROJECT_ROOT)))
        # Decide whether it's safe to run:
        # If script contains "OPENAI" or "api_key" we skip execution unless env var present
        text = p.read_text(encoding="utf-8", errors="ignore").lower()
        if "openai" in text or "api_key" in text or "openai_api_key" in text or "anthropic" in text:
            # requires API key - skip unless env var set
            if os.environ.get("OPENAI_API_KEY") or os.environ.get("ANHOPIC_API_KEY"):
                # run it with current environment, but do not print full output to avoid leaking keys
                try:
                    res = subprocess.run([sys.executable, str(p)], capture_output=True, text=True, timeout=30)
                    report["scripts"]["ran"].append({
                        "script": str(p.relative_to(PROJECT_ROOT)),
                        "rc": res.returncode,
                        "stdout_head": (res.stdout or "")[:500],
                        "stderr_head": (res.stderr or "")[:500]
                    })
                    report["scripts"]["runcount"] += 1
                except Exception as e:
                    report["scripts"]["ran"].append({
                        "script": str(p.relative_to(PROJECT_ROOT)),
                        "error": repr(e)
                    })
            else:
                report["scripts"]["skipped"].append({
                    "script": str(p.relative_to(PROJECT_ROOT)),
                    "reason": "requires API key; set OPENAI_API_KEY in environment to run"
                })
        else:
            # safe to run
            try:
                res = subprocess.run([sys.executable, str(p)], capture_output=True, text=True, timeout=30)
                report["scripts"]["ran"].append({
                    "script": str(p.relative_to(PROJECT_ROOT)),
                    "rc": res.returncode,
                    "stdout_head": (res.stdout or "")[:500],
                    "stderr_head": (res.stderr or "")[:500]
                })
                report["scripts"]["runcount"] += 1
            except Exception as e:
                report["scripts"]["ran"].append({
                    "script": str(p.relative_to(PROJECT_ROOT)),
                    "error": repr(e)
                })

def notebook_check():
    nb = PROJECT_ROOT / "notebook.ipynb"
    if nb.exists():
        report["notebook"] = {"present": True, "size_bytes": nb.stat().st_size}
    else:
        report["notebook"] = {"present": False}

def print_report():
    print("\n==== PROJECT TEST HARNESS REPORT ====\n")
    print("Project root:", PROJECT_ROOT)
    print("\n-- Directories --")
    print(" Found:", report["found_dirs"])
    print(" Missing:", report["missing_dirs"])
    print("\n-- Files --")
    print(" Found:", report["found_files"])
    print(" Missing:", report["missing_files"])
    print("\n-- .env / .env.example keys (presence only) --")
    for k,v in report["env"].items():
        print(f"  {k}: {v}")
    print("\n-- Python compilation --")
    print("  OK files:", report["compiled"]["ok"])
    print("  Failed:", report["compiled"]["failed"])
    if report["compiled"]["errors"]:
        print("  Errors (first 5):")
        for e in report["compiled"]["errors"][:5]:
            print("   -", e["file"], e["error"])
    print("\n-- Safe imports --")
    print("  Import OK:", report["imports"]["ok"][:20])
    print("  Import failed (first 10):")
    for e in report["imports"]["failed"][:10]:
        print("   -", e["module"], e["error"])
    print("\n-- Requirements (checked) --")
    print("  Checked:", report["requirements"]["checked"][:40])
    print("  Missing:", report["requirements"]["missing"])
    print("\n-- Data files --")
    for d in report["data_files"]:
        print(" ", d)
    print("\n-- Scripts --")
    print("  Listed:", report["scripts"]["listed"])
    print("  Ran count:", report["scripts"]["runcount"])
    print("  Ran/Results (first 6):")
    for r in report["scripts"]["ran"][:6]:
        print("   -", r.get("script") or r.get("script"), " rc:", r.get("rc"), " err:", r.get("error", "") )
    print("  Skipped (first 6):")
    for s in report["scripts"]["skipped"][:6]:
        print("   -", s)
    print("\n-- Notebook --")
    print(" ", report.get("notebook"))
    print("\n==== END REPORT ====\n")

def main():
    print("Running project verification checks...")
    check_paths()
    read_env()
    compile_python_files()
    try_safe_imports()
    check_requirements_installed()
    check_data_files()
    list_and_run_scripts()
    notebook_check()
    print_report()
    # set nonzero exit code if critical checks failed
    failed = 0
    if report["missing_dirs"]:
        failed += len(report["missing_dirs"])
    if report["compiled"]["failed"] > 0:
        failed += report["compiled"]["failed"]
    if report["requirements"]["missing"]:
        failed += len(report["requirements"]["missing"])
    if failed:
        print("Some checks failed. Fix above issues and re-run the harness.")
        sys.exit(2)
    else:
        print("All basic checks passed. Project appears runnable (subject to valid API keys and environment).")
        sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("Unexpected error running harness:")
        traceback.print_exc()
        sys.exit(3)
