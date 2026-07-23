"""3-mode scan harness for the experiment zone.

Runs the SAME real code through three modes and computes comparable metrics:
  - baseline:     traditional tools only (semgrep + bandit + gitleaks), NO LLM agent
  - single_agent: tools + ONE AI agent (reviewer)
  - debate:       tools + 3-agent debate (reviewer -> security -> fixer, arbitrated)

The key comparable metric is ground-truth coverage: how many of the project's
KNOWN intentional vulnerability categories each mode detects. This is real evidence
of agent value (not fabricated).
"""
import os
from typing import List

from app.core.scanner.semgrep import SemgrepScanner
from app.core.scanner.bandit import BanditScanner
from app.core.agents.reviewer import ReviewAgent
from app.core.agents.orchestrator import AgentOrchestrator

# Optional tools (graceful fallback if not installed)
try:
    from app.core.scanner.tools import gitleaks_scan as _gitleaks_tool
except Exception:
    _gitleaks_tool = None


def _norm_severity(s: str) -> str:
    s = (s or "").lower()
    if s in ("critical", "high", "error"):
        return "high"
    if s in ("medium", "warning"):
        return "medium"
    return "low"


def _matches_category(text: str, keywords: List[str]) -> bool:
    t = (text or "").lower()
    return any(kw in t for kw in keywords)


def _compute_metrics(findings: List[dict], ground_truth: List[dict], confirmed_count: int = None) -> dict:
    """Compute comparable metrics from a list of normalized findings."""
    types_found = set()
    critical_high = 0
    gt_hits = set()

    for f in findings:
        vtype = f.get("type", "") or f.get("check_id", "")
        desc = f.get("message", "") or f.get("description", "")
        blob = f"{vtype} {desc}"
        if vtype:
            types_found.add(vtype)
        if _norm_severity(f.get("severity", "")) == "high":
            critical_high += 1
        for i, cat in enumerate(ground_truth):
            if _matches_category(blob, cat["keywords"]):
                gt_hits.add(i)

    gt_total = len(ground_truth)
    hits = len(gt_hits)
    return {
        "findings_count": len(findings),
        "confirmed_count": confirmed_count if confirmed_count is not None else len(findings),
        "critical_high_count": critical_high,
        "unique_types": len(types_found),
        "ground_truth_hits": hits,
        "ground_truth_total": gt_total,
        "detection_rate": round(hits / gt_total, 3) if gt_total else 0.0,
        "categories_detected": [ground_truth[i]["category"] for i in sorted(gt_hits)],
        "categories_missed": [ground_truth[i]["category"] for i in range(gt_total) if i not in gt_hits],
    }


async def run_baseline(repo_dir: str, code: str, language: str, ground_truth: List[dict]) -> dict:
    """Traditional tools only, no LLM."""
    findings = []
    semgrep = SemgrepScanner()
    bandit = BanditScanner()

    for r in await semgrep.scan(code, language):
        findings.append({"type": r.get("check_id", ""), "severity": r.get("severity", ""),
                         "message": r.get("message", "")})
    for r in await bandit.scan_file(repo_dir):
        findings.append({"type": r.get("check_id", ""), "severity": r.get("severity", ""),
                         "message": r.get("message", "")})
    if _gitleaks_tool is not None:
        try:
            res = await _gitleaks_tool.ainvoke({"repo_dir": repo_dir})
            for r in res.get("findings", []):
                findings.append({"type": r.get("check_id", ""), "severity": r.get("severity", ""),
                                 "message": r.get("message", "")})
        except Exception:
            pass

    m = _compute_metrics(findings, ground_truth)
    m["mode"] = "baseline"
    m["llm_calls"] = 0
    m["description"] = "仅传统工具（Semgrep + Bandit + Gitleaks），无 AI Agent"
    return m


async def run_single_agent(code: str, language: str, ground_truth: List[dict]) -> dict:
    """Tools + ONE AI agent (reviewer)."""
    agent = ReviewAgent()
    result = await agent.analyze(code, language)
    findings = []
    for f in result.get("findings", []):
        findings.append({"type": f.get("type", ""), "severity": f.get("severity", ""),
                         "message": f.get("description", "")})
    m = _compute_metrics(findings, ground_truth)
    m["mode"] = "single_agent"
    m["llm_calls"] = 1
    m["description"] = "传统工具 + 单个 AI Agent（代码审查员）"
    return m


async def run_debate(code: str, language: str, ground_truth: List[dict]) -> dict:
    """Tools + 3-agent debate (reviewer -> security -> fixer, arbitrated)."""
    orch = AgentOrchestrator()
    report = await orch.analyze(code, language)
    findings = []
    for v in report.get("vulnerabilities", []):
        findings.append({"type": v.get("type", ""), "severity": v.get("severity", ""),
                         "message": v.get("description", "") or v.get("impact", "")})
    confirmed = report.get("total_vulnerabilities", len(findings))
    m = _compute_metrics(findings, ground_truth, confirmed_count=confirmed)
    m["mode"] = "debate"
    m["llm_calls"] = 3 + report.get("total_rounds", 0) * 3
    m["rounds"] = report.get("total_rounds", 0)
    m["risk_score"] = report.get("risk_score", 0)
    m["description"] = "传统工具 + 三 Agent 博弈（审查员→安全专家→修复顾问，多轮辩论仲裁）"
    return m


async def run_comparison(repo_dir: str, code: str, language: str, ground_truth: List[dict]) -> dict:
    """Run all 3 modes and return comparable results."""
    baseline = await run_baseline(repo_dir, code, language, ground_truth)
    single = await run_single_agent(code, language, ground_truth)
    debate = await run_debate(code, language, ground_truth)
    return {"baseline": baseline, "single_agent": single, "debate": debate}
