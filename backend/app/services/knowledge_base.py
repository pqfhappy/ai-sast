try:
    import pysqlite3
    import sys
    sys.modules["sqlite3"] = pysqlite3
except ImportError:
    pass

import chromadb
from chromadb.config import Settings
from app.config import settings


class KnowledgeBase:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
        self._init_collections()

    def _init_collections(self):
        try:
            self.vuln_collection = self.client.get_collection("vulnerabilities")
        except ValueError:
            self.vuln_collection = self.client.create_collection("vulnerabilities")

    def add_vulnerability(self, vuln_id: str, vuln_type: str, description: str, code: str, fix: str, metadata: dict = None):
        text = f"Type: {vuln_type}\nDescription: {description}\nCode: {code}\nFix: {fix}"
        self.vuln_collection.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[vuln_id],
        )

    def search_similar(self, query: str, n_results: int = 5) -> list[dict]:
        results = self.vuln_collection.query(
            query_texts=[query],
            n_results=n_results,
        )
        items = []
        for i in range(len(results["ids"][0])):
            items.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results.get("distances") else 0,
            })
        return items


knowledge_base = KnowledgeBase()
