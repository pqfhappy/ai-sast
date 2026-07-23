import json
import asyncio


class BanditScanner:
    async def scan_file(self, file_path: str) -> list[dict]:
        try:
            proc = await asyncio.create_subprocess_exec(
                "bandit", "-f", "json", "-r", file_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            results = json.loads(stdout)
            return self._parse_results(results)
        except Exception as e:
            return [{"error": str(e), "type": "system", "source": "bandit"}]

    def _parse_results(self, raw: dict) -> list[dict]:
        findings = []
        for result in raw.get("results", []):
            findings.append({
                "check_id": result.get("test_id", ""),
                "path": result.get("filename", ""),
                "start_line": result.get("line_number", 0),
                "end_line": result.get("line_number", 0),
                "message": result.get("issue_text", ""),
                "severity": result.get("issue_severity", "MEDIUM"),
                "confidence": result.get("issue_confidence", "MEDIUM"),
                "source": "bandit",
            })
        return findings
