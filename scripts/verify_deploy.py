"""AI-SAST post-deployment self-verification script (the "test agent's" hands & eyes).

Runs a suite of checks against the deployed instance. Every check prints PASS/FAIL.
Exits non-zero if ANY check fails, so it can gate the "done" report.

Three tiers:
  - smoke (default): all READ-ONLY checks (free, catch regressions). Always safe to run full.
  - tagged subset:   --only api|frontend|quality|ssh  (run just what your change touched)
  - active (opt-in): --with-scan  (triggers a REAL scan, costs Qwen tokens — use sparingly)

Tags:
  api      = health / projects / scans / report connectivity
  frontend = frontend serves 200
  quality  = data-quality regressions (confidence int, code_snippet, severity enum)
  ssh      = service active / no import errors / samples archived (needs credentials)
  scan     = active scan trigger (opt-in, costs tokens)

Usage:
    python scripts/verify_deploy.py                      # full smoke (read-only)
    python scripts/verify_deploy.py --only quality       # just data-quality checks
    python scripts/verify_deploy.py --only api,frontend  # multiple tags
    python scripts/verify_deploy.py --with-scan          # smoke + trigger a real scan
    SAST_HOST=... SAST_PASSWORD=... python scripts/verify_deploy.py   # include SSH checks
"""
import os
import sys
import json
import argparse
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    import requests
except ImportError:
    sys.exit("ERROR: 'requests' not installed. pip install requests")

# Load .env if present (same convention as deploy.py)
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

BASE = os.environ.get("SAST_BASE_URL", "http://localhost").rstrip("/")
HOST = os.environ.get("SAST_HOST", "")
USER = os.environ.get("SAST_USER", "deployer")
PASSWORD = os.environ.get("SAST_PASSWORD", "")

# ---- CLI / tag filtering ----
parser = argparse.ArgumentParser(description="AI-SAST self-verification")
parser.add_argument("--only", default="", help="comma-separated tags to run (api,frontend,quality,ssh,scan)")
parser.add_argument("--with-scan", action="store_true", help="also run active scan check (costs tokens)")
parser.add_argument("--scan-repo", default="https://github.com/we45/Vulnerable-Flask-App.git",
                    help="repo url for active scan check")
parser.add_argument("--scan-lang", default="python", help="language for active scan check")
ARGS = parser.parse_args()

# Active tag filter: empty set = run all read-only tags (smoke). 'scan' only if --with-scan.
_ONLY = {t.strip() for t in ARGS.only.split(",") if t.strip()}
READONLY_TAGS = {"api", "frontend", "quality", "ssh"}


def _should_run(tags):
    """Decide if a check (with given tags) should run under current filter."""
    if "scan" in tags and not ARGS.with_scan:
        return False
    if not _ONLY:
        # default smoke: run everything except opt-in 'scan'
        return not ("scan" in tags and not ARGS.with_scan)
    return bool(tags & _ONLY)


# ---- result tracking ----
_results = []


def check(name, ok, detail="", tags=None):
    tags = tags or set()
    if not _should_run(tags):
        return None  # skipped
    _results.append((name, ok, detail))
    mark = "[PASS]" if ok else "[FAIL]"
    line = f"{mark} {name}"
    if detail:
        line += f"  -- {detail}"
    print(line)
    return ok


def http_get(path, **kw):
    try:
        r = requests.get(BASE + path, timeout=20, **kw)
        return r
    except Exception as e:
        return e


# ============================================================
# HTTP CHECKS (no credentials needed)
# ============================================================
def run_http_checks():
    print(f"\n=== HTTP checks against {BASE} ===")

    # 1. health
    r = http_get("/api/health")
    ok = not isinstance(r, Exception) and r.status_code == 200 and r.json().get("status") == "ok"
    check("backend health", ok, "" if ok else str(r)[:120], tags={"api"})

    # 2. frontend serves
    r = http_get("/")
    ok = not isinstance(r, Exception) and r.status_code == 200 and "<html" in r.text.lower()
    check("frontend serves 200", ok, "" if ok else str(r)[:120], tags={"frontend"})

    # 3. projects list non-empty
    r = http_get("/api/projects")
    projects = []
    if not isinstance(r, Exception) and r.status_code == 200:
        projects = r.json()
    check("projects API returns data", isinstance(projects, list) and len(projects) > 0,
          f"{len(projects) if isinstance(projects, list) else 'ERR'} projects", tags={"api"})

    # 4. scans list non-empty
    r = http_get("/api/scans")
    scans = []
    if not isinstance(r, Exception) and r.status_code == 200:
        scans = r.json()
    check("scans API returns data", isinstance(scans, list) and len(scans) > 0,
          f"{len(scans) if isinstance(scans, list) else 'ERR'} scans", tags={"api"})

    # 5. find a completed scan with vulnerabilities for deep checks
    completed = [s for s in scans if isinstance(s, dict) and s.get("status") == "completed"
                 and (s.get("total_vulnerabilities") or 0) > 0]
    if not completed:
        check("have a completed scan with vulns", False, "no completed scan with vulns found", tags={"quality"})
        return

    scan = completed[0]
    sid = scan["id"]
    r = http_get(f"/api/reports/scan/{sid}")
    vulns = r.json() if not isinstance(r, Exception) and r.status_code == 200 else []
    check(f"report for scan #{sid} returns vulns", len(vulns) > 0, f"{len(vulns)} vulns", tags={"api", "quality"})
    if not vulns:
        return

    # 6. confidence must be integer 0-100 (regression: was 'MEDIUM%')
    bad_conf = []
    for v in vulns:
        c = v.get("confidence")
        if not isinstance(c, int) or c < 0 or c > 100:
            bad_conf.append(f"{v.get('vulnerability_type')}={c!r}")
    check("confidence is integer 0-100", len(bad_conf) == 0,
          "" if not bad_conf else "bad: " + ", ".join(bad_conf[:5]), tags={"quality"})

    # 7. at least some project-scan vulns have code_snippet (regression: was empty)
    with_snippet = [v for v in vulns if (v.get("code_snippet") or "").strip()]
    has_snippet = len(with_snippet) > 0
    check("vulnerabilities have code_snippet", has_snippet,
          f"{len(with_snippet)}/{len(vulns)} with snippet", tags={"quality"})

    # 8. severity values are valid enums
    valid_sev = {"critical", "high", "medium", "low", "info"}
    bad_sev = [v.get("severity") for v in vulns if v.get("severity") not in valid_sev]
    check("severity values valid", len(bad_sev) == 0,
          "" if not bad_sev else "bad: " + ", ".join(map(str, bad_sev[:5])), tags={"quality"})


# ============================================================
# SSH CHECKS (optional, need credentials)
# ============================================================
def run_ssh_checks():
    if not HOST or not PASSWORD:
        if _should_run({"ssh"}):
            print("\n=== SSH checks skipped (no SAST_HOST/SAST_PASSWORD) ===")
        return
    if not _should_run({"ssh"}):
        return
    print(f"\n=== SSH checks against {HOST} ===")
    try:
        import paramiko
    except ImportError:
        check("paramiko available", False, "pip install paramiko", tags={"ssh"})
        return

    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        c.connect(HOST, username=USER, password=PASSWORD, timeout=15)
    except Exception as e:
        check("SSH connect", False, str(e)[:120], tags={"ssh"})
        return

    def ssh(cmd):
        _, o, e = c.exec_command(cmd, timeout=30)
        return o.read().decode("utf-8", errors="replace").strip()

    # 9. backend service active
    out = ssh("systemctl is-active ai-sast.service")
    check("backend service active", out == "active", out, tags={"ssh"})

    # 10. no import/traceback errors in recent logs
    out = ssh("sudo journalctl -u ai-sast.service -n 40 --no-pager 2>&1 | grep -iE 'traceback|importerror|modulenotfound' | head -3")
    check("no import errors in logs", out == "", out[:200], tags={"ssh"})

    # 11. samples dir exists and has content
    out = ssh("ls /data/ai-sast/samples/ 2>/dev/null | head -5")
    check("samples dir has archived scans", out != "", out or "empty/missing", tags={"ssh"})

    c.close()


# ============================================================
# ACTIVE SCAN CHECK (opt-in via --with-scan, costs Qwen tokens)
# ============================================================
def run_active_scan_check():
    if not _should_run({"scan"}):
        return
    import time
    print(f"\n=== Active scan check (costs tokens) ===")
    print(f"Triggering real scan: {ARGS.scan_repo} ({ARGS.scan_lang})")

    # create project + scan
    try:
        rp = requests.post(BASE + "/api/projects", params={
            "name": "verify-auto", "description": "auto verification scan", "language": ARGS.scan_lang
        }, timeout=20).json()
        pid = rp.get("id")
        rs = requests.post(BASE + "/api/scans", params={"project_id": pid, "branch": "master"}, timeout=20).json()
        sid = rs.get("id")
        requests.post(BASE + f"/api/scans/{sid}/run-project",
                      json={"repo_url": ARGS.scan_repo, "language": ARGS.scan_lang}, timeout=20)
    except Exception as e:
        check("active scan: trigger", False, str(e)[:150], tags={"scan"})
        return

    # poll until complete (max 5 min)
    status = ""
    for _ in range(30):
        time.sleep(10)
        try:
            status = requests.get(BASE + f"/api/scans/{sid}", timeout=20).json().get("status", "")
        except Exception:
            pass
        if status in ("completed", "failed"):
            break

    check("active scan: completes", status == "completed", f"final status={status}", tags={"scan"})
    if status != "completed":
        return

    # verify it produced vulns with snippets
    try:
        vulns = requests.get(BASE + f"/api/reports/scan/{sid}", timeout=20).json()
    except Exception as e:
        check("active scan: report", False, str(e)[:150], tags={"scan"})
        return
    with_snip = sum(1 for v in vulns if (v.get("code_snippet") or "").strip())
    check("active scan: found vulns", len(vulns) > 0, f"{len(vulns)} vulns", tags={"scan"})
    check("active scan: vulns have snippets", with_snip > 0, f"{with_snip}/{len(vulns)}", tags={"scan"})


def main():
    print(f"AI-SAST self-verification @ {BASE}")
    if _ONLY:
        print(f"(filter: only tags {sorted(_ONLY)})")
    if ARGS.with_scan:
        print("(active scan check ENABLED — costs tokens)")

    run_http_checks()
    run_ssh_checks()
    run_active_scan_check()

    if not _results:
        print("\nNo checks ran (check your --only filter).")
        sys.exit(2)

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    failed = total - passed
    print(f"\n{'='*50}")
    print(f"RESULT: {passed}/{total} passed, {failed} failed")
    print("=" * 50)

    if failed:
        print("\nFAILED CHECKS:")
        for name, ok, detail in _results:
            if not ok:
                print(f"  - {name}: {detail}")
        sys.exit(1)
    print("\nALL CHECKS PASSED")
    sys.exit(0)


if __name__ == "__main__":
    main()