import asyncio
import json
from typing import Optional


class SemgrepScanner:
    def __init__(self):
        self.rules_dir = "./knowledge/rules"

    async def scan(self, code: str, language: str = "python") -> list[dict]:
        try:
            proc = await asyncio.create_subprocess_exec(
                "semgrep", "--lang", language, "--json", "-",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate(code.encode())
            if proc.returncode != 0:
                return []
            results = json.loads(stdout)
            return self._parse_results(results)
        except FileNotFoundError:
            return [{"error": "semgrep not installed", "type": "system"}]

    async def scan_file(self, file_path: str, language: str = "python") -> list[dict]:
        try:
            proc = await asyncio.create_subprocess_exec(
                "semgrep", "--lang", language, "--json", file_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            results = json.loads(stdout)
            return self._parse_results(results)
        except Exception as e:
            return [{"error": str(e), "type": "system"}]

    def _parse_results(self, raw: dict) -> list[dict]:
        findings = []
        for result in raw.get("results", []):
            findings.append({
                "check_id": result.get("check_id", ""),
                "path": result.get("path", ""),
                "start_line": result.get("start", {}).get("line", 0),
                "end_line": result.get("end", {}).get("line", 0),
                "message": result.get("extra", {}).get("message", ""),
                "severity": result.get("extra", {}).get("severity", "WARNING"),
                "metadata": result.get("extra", {}).get("metadata", {}),
                "source": "semgrep",
            })
        return findings
