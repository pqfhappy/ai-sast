import json
from app.core.evolution.knowledge import KnowledgeGraph


class EvolutionLearner:
    def __init__(self):
        self.knowledge_graph = KnowledgeGraph()

    def learn_from_feedback(self, vulnerability_id: int, is_false_positive: bool, user_note: str = ""):
        self.knowledge_graph.add_feedback(vulnerability_id, is_false_positive, user_note)

    def optimize_prompt(self, agent_name: str, feedback_history: list) -> str:
        improvements = []
        for fb in feedback_history:
            if fb.get("is_false_positive"):
                improvements.append(f"之前对 {fb.get('vuln_type')} 的误报率较高，应更谨慎判断")

        if improvements:
            return "额外指导: " + "; ".join(improvements)
        return ""

    def suggest_new_rules(self, scan_results: list[dict]) -> list[dict]:
        new_rules = []
        grouped = {}
        for r in scan_results:
            vtype = r.get("vulnerability_type", "unknown")
            if vtype not in grouped:
                grouped[vtype] = {"count": 0, "examples": []}
            grouped[vtype]["count"] += 1
            grouped[vtype]["examples"].append(r.get("code_snippet", "")[:200])

        for vtype, data in grouped.items():
            if data["count"] >= 3:
                new_rules.append({
                    "type": vtype,
                    "frequency": data["count"],
                    "suggested_rule": f"检测 {vtype} 的Semgrep规则",
                    "example": data["examples"][0],
                })

        return new_rules
