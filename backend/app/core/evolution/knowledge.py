import json
from datetime import datetime


class KnowledgeGraph:
    def __init__(self):
        self.feedback_log: list[dict] = []

    def add_feedback(self, vulnerability_id: int, is_false_positive: bool, note: str = ""):
        self.feedback_log.append({
            "vulnerability_id": vulnerability_id,
            "is_false_positive": is_false_positive,
            "note": note,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def get_false_positive_rate(self) -> float:
        if not self.feedback_log:
            return 0.0
        fps = sum(1 for f in self.feedback_log if f["is_false_positive"])
        return fps / len(self.feedback_log)

    def get_common_false_positives(self, top_n: int = 5) -> list[dict]:
        from collections import Counter
        type_counter = Counter()
        for fb in self.feedback_log:
            if fb["is_false_positive"]:
                type_counter[fb.get("note", "unknown")] += 1
        return [{"type": t, "count": c} for t, c in type_counter.most_common(top_n)]

    def export_knowledge(self) -> dict:
        return {
            "feedback_count": len(self.feedback_log),
            "false_positive_rate": self.get_false_positive_rate(),
            "common_fps": self.get_common_false_positives(),
        }
