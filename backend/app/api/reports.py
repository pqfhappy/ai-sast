from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.project import Vulnerability
from app.services.database import async_session

router = APIRouter(prefix="/api/reports", tags=["reports"])

async def get_db():
    async with async_session() as session:
        yield session

@router.get("/scan/{scan_id}")
async def get_scan_vulnerabilities(scan_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Vulnerability).where(Vulnerability.scan_id == scan_id).order_by(Vulnerability.severity)
    )
    return result.scalars().all()
