from fastapi import APIRouter

router = APIRouter(prefix="/api/agents", tags=["agents"])

@router.get("/status")
async def agent_status():
    return {
        "reviewer": "idle",
        "security": "idle",
        "fixer": "idle",
    }
