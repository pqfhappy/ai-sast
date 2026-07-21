from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.project import Vulnerability
from app.services.database import async_session
from app.core.evolution.learner import EvolutionLearner

router = APIRouter(prefix="/api/evolution", tags=["evolution"])
learner = EvolutionLearner()

async def get_db():
    async with async_session() as session:
        yield session

@router.post("/feedback")
async def submit_feedback(vulnerability_id: int, is_false_positive: bool, note: str = ""):
    learner.learn_from_feedback(vulnerability_id, is_false_positive, note)
    return {"status": "ok"}

@router.get("/stats")
async def evolution_stats():
    return learner.knowledge_graph.export_knowledge()

@router.get("/rule-suggestions")
async def rule_suggestions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Vulnerability).limit(50))
    vulns = result.scalars().all()
    suggestions = learner.suggest_new_rules([
        {"vulnerability_type": v.vulnerability_type, "code_snippet": v.code_snippet}
        for v in vulns
    ])
    return {"suggestions": suggestions}
