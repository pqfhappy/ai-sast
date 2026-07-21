import json
from app.core.agents.reviewer import ReviewAgent
from app.core.agents.security import SecurityAgent
from app.core.agents.fixer import FixAgent


class AgentOrchestrator:
    MAX_ROUNDS = 3
    CONVERGENCE_THRESHOLD = 0.8

    def __init__(self):
        self.reviewer = ReviewAgent()
        self.security = SecurityAgent()
        self.fixer = FixAgent()

    async def analyze(self, code: str, language: str = "python") -> dict:
        round_results = []

        reviewer_result = await self.reviewer.analyze(code, language)
        round_results.append({"round": 0, "agent": "reviewer", "result": reviewer_result})

        security_result = await self.security.analyze(code, reviewer_result, language)
        round_results.append({"round": 0, "agent": "security", "result": security_result})

        fix_result = await self.fixer.analyze(code, security_result, language)
        round_results.append({"round": 0, "agent": "fixer", "result": fix_result})

        for round_num in range(1, self.MAX_ROUNDS + 1):
            challenges = self._generate_challenges(
                reviewer_result, security_result, fix_result
            )

            if self._has_convergence(challenges):
                break

            reviewer_result = await self.reviewer.revise(reviewer_result, challenges)
            security_result = await self.security.revise(security_result, challenges)
            fix_result = await self.fixer.revise(fix_result, challenges)

            round_results.append({
                "round": round_num,
                "challenges": challenges,
                "reviewer": reviewer_result,
                "security": security_result,
                "fixer": fix_result,
            })

        final_report = self._arbitrate(reviewer_result, security_result, fix_result)
        final_report["rounds"] = round_results
        final_report["total_rounds"] = len(round_results) - 1
        return final_report

    def _generate_challenges(self, reviewer: dict, security: dict, fixer: dict) -> list:
        challenges = []
        security_disputed = security.get("disputed", [])
        for d in security_disputed:
            challenges.append({
                "from": "security_expert",
                "to": "reviewer",
                "issue": d.get("type", ""),
                "reason": d.get("reason", ""),
            })
        return challenges

    def _has_convergence(self, challenges: list) -> bool:
        return len(challenges) == 0

    def _arbitrate(self, reviewer: dict, security: dict, fixer: dict) -> dict:
        all_findings = []
        seen_types = set()

        for finding in security.get("confirmed_findings", []):
            key = finding.get("type", "") + str(finding.get("line", ""))
            if key not in seen_types:
                seen_types.add(key)
                all_findings.append({
                    "type": finding.get("type"),
                    "severity": finding.get("severity"),
                    "line": finding.get("line"),
                    "cvss_score": finding.get("cvss_score"),
                    "attack_vector": finding.get("attack_vector"),
                    "impact": finding.get("impact"),
                    "confidence": finding.get("confidence"),
                    "fix": None,
                    "status": "confirmed",
                })

        for finding in security.get("new_findings", []):
            key = finding.get("type", "") + str(finding.get("line", ""))
            if key not in seen_types:
                seen_types.add(key)
                all_findings.append({
                    "type": finding.get("type"),
                    "severity": finding.get("severity"),
                    "line": finding.get("line"),
                    "description": finding.get("description"),
                    "fix": None,
                    "status": "new",
                })

        fixes = fixer.get("fixes", [])
        fix_map = {f.get("type", ""): f.get("fix_code") for f in fixes}
        for finding in all_findings:
            finding["fix"] = fix_map.get(finding.get("type", ""))

        risk_scores = [
            s.get("confidence", 0)
            for s in security.get("confirmed_findings", [])
        ]
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0

        return {
            "vulnerabilities": all_findings,
            "total_vulnerabilities": len(all_findings),
            "risk_score": round(avg_risk, 1),
            "summary": security.get("summary", ""),
            "fix_summary": fixer.get("summary", ""),
            "review_summary": reviewer.get("summary", ""),
        }
