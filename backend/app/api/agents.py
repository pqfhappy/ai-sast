from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.agents.orchestrator import AgentOrchestrator

router = APIRouter(prefix="/api/agents", tags=["agents"])
orchestrator = AgentOrchestrator()


class AnalyzeRequest(BaseModel):
    code: str
    language: str = "python"


@router.get("/status")
async def agent_status():
    return {
        "reviewer": "ready",
        "security": "ready",
        "fixer": "ready",
        "orchestrator": "ready",
    }


@router.post("/analyze")
async def analyze_code(req: AnalyzeRequest):
    try:
        result = await orchestrator.analyze(req.code, req.language)
        return result
    except Exception as e:
        raise HTTPException(500, f"Agent analysis failed: {str(e)}")
