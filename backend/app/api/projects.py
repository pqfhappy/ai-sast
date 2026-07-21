from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.project import Project, ProjectStatus
from app.services.database import async_session

router = APIRouter(prefix="/api/projects", tags=["projects"])

async def get_db():
    async with async_session() as session:
        yield session

@router.get("")
async def list_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    return result.scalars().all()

@router.post("")
async def create_project(name: str, description: str = "", language: str = "", db: AsyncSession = Depends(get_db)):
    project = Project(name=name, description=description, language=language)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project

@router.get("/{project_id}")
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")
    return project
