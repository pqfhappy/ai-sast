from app.core.scanner.semgrep import SemgrepScanner
from app.core.scanner.bandit import BanditScanner
from app.core.scanner.ai_scanner import AIScanner


class ScanOrchestrator:
    def __init__(self):
        self.semgrep = SemgrepScanner()
        self.bandit = BanditScanner()
        self.ai = AIScanner()

    async def scan_code(self, code: str, language: str = "python") -> dict:
        findings = []

        semgrep_results = await self.semgrep.scan(code, language)
        findings.extend(semgrep_results)

        ai_result = await self.ai.analyze_code(code)
        for v in ai_result.get("vulnerabilities", []):
            findings.append({
                "check_id": v.get("type", ""),
                "start_line": v.get("line", 0),
                "end_line": v.get("line", 0),
                "message": v.get("description", ""),
                "severity": v.get("severity", "medium").upper(),
                "remediation": v.get("remediation", ""),
                "confidence": v.get("confidence", 0),
                "source": "ai",
            })

        return {"findings": findings, "total": len(findings)}
