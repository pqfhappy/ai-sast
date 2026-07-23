"""Test SAST pipeline via ECS API."""
import os
import requests
import json

BASE = os.environ.get("SAST_BASE_URL", "http://localhost").rstrip("/") + "/api"

def log(label, response):
    print(f"\n=== {label} ===")
    try:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
    except:
        print(response.text[:500])

# 1. Create project
resp = requests.post(f"{BASE}/projects", params={"name": "测试项目", "description": "漏洞样本测试", "language": "python"})
log("创建项目", resp)
project = resp.json()
project_id = project.get("id")

# 2. Create scan
resp = requests.post(f"{BASE}/scans", params={"project_id": project_id, "branch": "master"})
log("创建扫描任务", resp)
scan = resp.json()
scan_id = scan.get("id")

# 3. Run scan
vuln_code = open("tests/test_fixtures/vulnerable_sample.py", "r", encoding="utf-8").read()
resp = requests.post(f"{BASE}/scans/{scan_id}/run", json={"code": vuln_code, "language": "python"})
log("执行扫描", resp)

# 4. Get vulnerabilities
resp = requests.get(f"{BASE}/reports/scan/{scan_id}")
log("获取漏洞报告", resp)

# 5. List scans
resp = requests.get(f"{BASE}/scans")
log("扫描列表", resp)

# 6. List projects
resp = requests.get(f"{BASE}/projects")
log("项目列表", resp)
