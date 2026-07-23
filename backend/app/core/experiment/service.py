"""Experiment service: assembles real experiment data.

Combines:
  - registry (real projects + ground-truth expected counts)
  - real production scan results from DB (actual_count, severity distribution)
  - 3-mode harness comparison (baseline / single_agent / debate)

Writes backend/data/experiment.json which the API serves.
"""
import os
import json
import glob
from datetime import datetime

from sqlalchemy import select
from app.services.database import async_session
from app.models.project import ScanTask, ScanStatus, Vulnerability
from app.core.experiment.registry import EXPERIMENT_PROJECTS
from app.core.experiment import harness

SAMPLES_DIR = "/data/ai-sast/samples"
DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "experiment.json")


def _find_sample_dir(repo_name: str):
    """Find the latest archived sample dir for a repo (scan{ID}_{name})."""
    pattern = os.path.join(SAMPLES_DIR, f"*_{repo_name}")
    matches = glob.glob(pattern)
    if not matches:
        return None, None
    # pick highest scan id
    best, best_id = None, -1
    for m in matches:
        base = os.path.basename(m)
        try:
            sid = int(base.split("_")[0].replace("scan", ""))
        except Exception:
            sid = -1
        if sid > best_id:
            best, best_id = m, sid
    return best, best_id


async def _scan_stats(scan_id: int):
    """Get actual_count + severity distribution from a real scan in DB."""
    async with async_session() as db:
        res = await db.execute(select(Vulnerability).where(Vulnerability.scan_id == scan_id))
        vulns = res.scalars().all()
    sev_dist = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for v in vulns:
        s = (v.severity.value if hasattr(v.severity, "value") else str(v.severity)).lower()
        if s in sev_dist:
            sev_dist[s] += 1
    return len(vulns), sev_dist


async def build_experiment_data() -> dict:
    projects_out = []
    overall = {"baseline": None, "single_agent": None, "debate": None}
    overall_acc = {m: {"findings_count": 0, "critical_high_count": 0, "ground_truth_hits": 0,
                       "ground_truth_total": 0} for m in overall}

    for proj in EXPERIMENT_PROJECTS:
        repo_name = proj["repo_url"].rstrip("/").split("/")[-1]
        sample_dir, scan_id = _find_sample_dir(repo_name)
        if not sample_dir:
            continue

        main_path = os.path.join(sample_dir, proj["main_file"])
        if not os.path.exists(main_path):
            continue
        with open(main_path, "r", encoding="utf-8", errors="replace") as f:
            code = f.read(20000)

        # real production scan stats
        actual_count, sev_dist = (0, {})
        if scan_id:
            actual_count, sev_dist = await _scan_stats(scan_id)

        # 3-mode comparison (REAL)
        cmp = await harness.run_comparison(sample_dir, code, proj["language"], proj["ground_truth"])

        expected = proj["expected_count"]
        metrics = {
            "detection_rate": cmp["debate"]["detection_rate"],  # best mode's ground-truth coverage
            "severity_distribution": sev_dist,
            "files_scanned": len(glob.glob(os.path.join(sample_dir, "**", "*.py"), recursive=True)),
            "scan_id": scan_id,
        }

        record = {
            "project_name": proj["project_name"],
            "repo_url": proj["repo_url"],
            "language": proj["language"],
            "description": proj["description"],
            "expected_count": expected,
            "actual_count": actual_count,
            "scan_id": scan_id,
            "metrics": metrics,
            "agent_comparison": cmp,
        }
        projects_out.append(record)

        for m in overall:
            for k in overall_acc[m]:
                overall_acc[m][k] += cmp[m][k]

    # finalize overall (detection rate)
    for m in overall:
        a = overall_acc[m]
        a["detection_rate"] = round(a["ground_truth_hits"] / a["ground_truth_total"], 3) if a["ground_truth_total"] else 0.0
        a["mode"] = m
        overall[m] = a

    result = {
        "generated_at": datetime.utcnow().isoformat(),
        "projects": projects_out,
        "overall": overall,
    }

    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result


def load_experiment_data():
    if not os.path.exists(DATA_FILE):
        return None
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
