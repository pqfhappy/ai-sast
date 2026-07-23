from fastapi import APIRouter, HTTPException

from app.core.experiment.service import build_experiment_data, load_experiment_data

router = APIRouter(prefix="/api/experiment", tags=["experiment"])


@router.get("/summary")
async def experiment_summary():
    data = load_experiment_data()
    if data is None:
        raise HTTPException(404, "Experiment data not generated yet. POST /api/experiment/run first.")
    return data


@router.post("/run")
async def experiment_run():
    """Run the 3-mode comparison on all registry projects (REAL scans, costs tokens).

    Synchronous and may take a few minutes. Writes data/experiment.json.
    """
    try:
        data = await build_experiment_data()
        return data
    except Exception as e:
        raise HTTPException(500, f"Experiment run failed: {e}")
