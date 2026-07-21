"""Agent analysis API with persistent task support."""
import asyncio
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.agents.orchestrator import AgentOrchestrator

router = APIRouter(prefix="/api/agents", tags=["agents"])
orchestrator = AgentOrchestrator()

class AnalyzeRequest(BaseModel):
    code: str
    language: str = "python"

# In-memory task store: {task_id: {"status": "pending|running|completed|failed", "result": dict, "error": str}}
_analysis_tasks = {}

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

@router.post("/analyze/async")
async def analyze_code_async(req: AnalyzeRequest):
    task_id = str(uuid.uuid4())
    _analysis_tasks[task_id] = {"status": "pending", "result": None, "error": None}

    async def _run():
        _analysis_tasks[task_id]["status"] = "running"
        try:
            result = await orchestrator.analyze(req.code, req.language)
            _analysis_tasks[task_id]["status"] = "completed"
            _analysis_tasks[task_id]["result"] = result
        except Exception as e:
            _analysis_tasks[task_id]["status"] = "failed"
            _analysis_tasks[task_id]["error"] = str(e)

    asyncio.create_task(_run())
    return {"task_id": task_id, "status": "pending"}

@router.get("/analyze/{task_id}")
async def get_analysis_result(task_id: str):
    task = _analysis_tasks.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    resp = {"task_id": task_id, "status": task["status"]}
    if task["status"] == "completed":
        resp["result"] = task["result"]
    elif task["status"] == "failed":
        resp["error"] = task["error"]
    return resp
