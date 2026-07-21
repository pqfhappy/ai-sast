from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.project import ScanTask, ScanStatus
from app.services.database import async_session

router = APIRouter(prefix="/api/scans", tags=["scans"])

async def get_db():
    async with async_session() as session:
        yield session

@router.get("")
async def list_scans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScanTask).order_by(ScanTask.created_at.desc()))
    return result.scalars().all()

@router.post("")
async def create_scan(project_id: int, branch: str = "main", db: AsyncSession = Depends(get_db)):
    scan = ScanTask(project_id=project_id, branch=branch)
    db.add(scan)
    await db.commit()
    await db.refresh(scan)
    return scan
