"""实验专区需求测试用例 — 自动化验证脚本.

来源：docs/experiment_test_cases.md（用户诉求，禁止随代码漂移）。
验证实验专区是否满足用户的 3 条诉求。全 PASS 退出码 0，有 FAIL 退出码 1。

数据契约：实验数据应由后端 /api/experiment/summary 提供（数据驱动，非前端硬编码）。
"""
import os
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    import requests
except ImportError:
    sys.exit("ERROR: pip install requests")

env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

BASE = os.environ.get("SAST_BASE_URL", "http://localhost").rstrip("/")

# 伪造项目黑名单（setup_demo.py 用内联代码造的，禁止出现在实验区）
FABRICATED = {
    "OWASP WebGoat (Java)", "DVWA (PHP)", "NodeGoat (Node.js)",
    "Rust Security Examples", "Go Vulnerability Examples", "C Buffer Overflow Examples",
}
GITHUB_RE = re.compile(r"^https?://github\.com/[^/]+/[^/]+")

_results = []


def check(tc_id, name, ok, detail=""):
    _results.append((tc_id, name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {tc_id} {name}" + (f"  -- {detail}" if detail else ""))
    return ok


def get(path):
    try:
        return requests.get(BASE + path, timeout=20)
    except Exception as e:
        return e


def main():
    print(f"实验专区需求测试 @ {BASE}\n")

    # ---- 取实验数据源 ----
    r = get("/api/experiment/summary")
    has_endpoint = not isinstance(r, Exception) and r.status_code == 200
    data = r.json() if has_endpoint else {}
    projects = data.get("projects", []) if isinstance(data, dict) else []

    check("EXP-0", "实验数据源 /api/experiment/summary 存在", has_endpoint,
          "" if has_endpoint else f"endpoint missing/err: {str(r)[:80]}")

    if not projects:
        check("EXP-0.1", "实验数据源含项目", False, "no projects in experiment data")

    # ================= 诉求 1：资源描述 =================
    print("\n--- 诉求1: 资源描述 ---")
    for p in projects:
        nm = p.get("project_name", "?")
        check("EXP-1.1", f"[{nm}] 有项目名", bool(nm and nm != "?"))
        url = p.get("repo_url", "")
        check("EXP-1.2", f"[{nm}] URL 真实有效", bool(GITHUB_RE.match(url or "")), url or "empty")
        check("EXP-1.3", f"[{nm}] 有预期漏洞数 expected_count",
              isinstance(p.get("expected_count"), int), f"got {p.get('expected_count')!r}")
        check("EXP-1.4", f"[{nm}] 有实际检出数 actual_count",
              isinstance(p.get("actual_count"), int), f"got {p.get('actual_count')!r}")
        metrics = p.get("metrics", {})
        check("EXP-1.5", f"[{nm}] 有>=2项额外指标",
              isinstance(metrics, dict) and len(metrics) >= 2, f"metrics keys={list(metrics.keys())}")

    # ================= 诉求 2：Agent 博弈效果 =================
    print("\n--- 诉求2: Agent 博弈真实效果 ---")
    for p in projects:
        nm = p.get("project_name", "?")
        cmp = p.get("agent_comparison", {})
        for mode in ("baseline", "single_agent", "debate"):
            tc = {"baseline": "EXP-2.1", "single_agent": "EXP-2.2", "debate": "EXP-2.3"}[mode]
            check(tc, f"[{nm}] 有 {mode} 真实数据",
                  isinstance(cmp.get(mode), dict) and len(cmp.get(mode, {})) > 0,
                  "" if cmp.get(mode) else "missing")
        # EXP-2.4 可对比量化指标
        modes = [cmp.get(m) for m in ("baseline", "single_agent", "debate") if isinstance(cmp.get(m), dict)]
        if modes:
            common_keys = set.intersection(*[set(m.keys()) for m in modes]) if modes else set()
            check("EXP-2.4", f"[{nm}] 三模式有共同可对比指标",
                  len(common_keys) >= 1, f"common={sorted(common_keys)}")
        else:
            check("EXP-2.4", f"[{nm}] 三模式有共同可对比指标", False, "no mode data")

    # EXP-2.5 总体聚合
    overall = data.get("overall", {}) if isinstance(data, dict) else {}
    check("EXP-2.5", "有总体(overall)聚合效果",
          isinstance(overall, dict) and all(m in overall for m in ("baseline", "single_agent", "debate")),
          f"overall keys={list(overall.keys()) if isinstance(overall, dict) else 'N/A'}")

    # EXP-2.6 数据可追溯到 scan_id（非硬编码）
    traceable = all(isinstance(p.get("scan_id"), int) for p in projects) if projects else False
    check("EXP-2.6", "效果数据可追溯到 scan_id", traceable,
          "" if traceable else "some project missing scan_id")

    # ================= 诉求 3：真实开源项目 =================
    print("\n--- 诉求3: 真实开源项目（底线） ---")
    for p in projects:
        nm = p.get("project_name", "?")
        url = p.get("repo_url", "")
        check("EXP-3.1", f"[{nm}] 是真实 GitHub 项目", bool(GITHUB_RE.match(url or "")), url or "empty")
        check("EXP-3.2", f"[{nm}] URL 非占位符",
              bool(url) and url not in ("#", "") and "example.com" not in url, url or "empty")
        check("EXP-3.3", f"[{nm}] 有 repo_url（真实clone）", bool(url), "repo_url empty=可能内联伪造")
        check("EXP-3.4", f"[{nm}] 非伪造样本", nm not in FABRICATED,
              "" if nm not in FABRICATED else "在伪造黑名单中!")

    # EXP-3.4 额外：独立核对 DB 中是否还有伪造项目被当作实验数据
    pr = get("/api/projects")
    if not isinstance(pr, Exception) and pr.status_code == 200:
        db_names = {p.get("name") for p in pr.json()}
        leaked = FABRICATED & db_names
        # 仅提示：伪造项目可能仍存在于 DB（实验区不应使用它们）
        check("EXP-3.4b", "DB 中伪造项目未被实验区使用",
              not (leaked and any(p.get("project_name") in leaked for p in projects)),
              f"DB仍含伪造项目: {sorted(leaked)}（实验区勿用）" if leaked else "DB无伪造项目")

    # ---- 汇总 ----
    passed = sum(1 for _, _, ok, _ in _results if ok)
    total = len(_results)
    failed = total - passed
    print(f"\n{'='*56}")
    print(f"RESULT: {passed}/{total} passed, {failed} failed")
    print("=" * 56)
    if failed:
        print("\nFAILED:")
        for tc, name, ok, detail in _results:
            if not ok:
                print(f"  - {tc} {name}: {detail}")
        sys.exit(1)
    print("\nALL EXPERIMENT REQUIREMENTS SATISFIED")
    sys.exit(0)


if __name__ == "__main__":
    main()