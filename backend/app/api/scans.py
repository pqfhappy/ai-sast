from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.project import ScanTask, ScanStatus, Vulnerability, VulnerabilitySeverity
from app.services.database import async_session
from app.core.scanner.orchestrator import ScanOrchestrator

router = APIRouter(prefix="/api/scans", tags=["scans"])
orchestrator = ScanOrchestrator()

async def get_db():
    async with async_session() as session:
        yield session

class ScanRunRequest(BaseModel):
    code: str
    language: str = "python"
    file_path: str = ""

@router.get("")
async def list_scans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScanTask).order_by(ScanTask.created_at.desc()))
    return result.scalars().all()

@router.post("")
async def create_scan(project_id: int, branch: str = "master", db: AsyncSession = Depends(get_db)):
    scan = ScanTask(project_id=project_id, branch=branch)
    db.add(scan)
    await db.commit()
    await db.refresh(scan)
    return scan

@router.get("/{scan_id}")
async def get_scan(scan_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScanTask).where(ScanTask.id == scan_id))
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(404, "Scan not found")
    return scan

@router.post("/{scan_id}/run")
async def run_scan(scan_id: int, req: ScanRunRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScanTask).where(ScanTask.id == scan_id))
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(404, "Scan not found")

    scan.status = ScanStatus.RUNNING
    await db.commit()

    try:
        scan_result = await orchestrator.scan_code(req.code, req.language, req.file_path)
        for finding in scan_result["findings"]:
            vuln = Vulnerability(
                scan_id=scan_id,
                file_path=finding.get("path", "inline"),
                line_start=finding.get("start_line"),
                line_end=finding.get("end_line"),
                vulnerability_type=finding.get("check_id", "unknown"),
                severity=_parse_severity(finding.get("severity", "MEDIUM")),
                description=finding.get("message", ""),
                remediation=finding.get("remediation", ""),
                confidence=finding.get("confidence", 50),
                code_snippet=req.code,
            )
            db.add(vuln)

        scan.status = ScanStatus.COMPLETED
        scan.total_vulnerabilities = scan_result["total"]
        await db.commit()
    except Exception as e:
        scan.status = ScanStatus.FAILED
        await db.commit()
        raise HTTPException(500, str(e))

    return scan_result

def _parse_severity(sev: str) -> VulnerabilitySeverity:
    mapping = {
        "CRITICAL": VulnerabilitySeverity.CRITICAL,
        "HIGH": VulnerabilitySeverity.HIGH,
        "MEDIUM": VulnerabilitySeverity.MEDIUM,
        "LOW": VulnerabilitySeverity.LOW,
        "WARNING": VulnerabilitySeverity.MEDIUM,
        "ERROR": VulnerabilitySeverity.HIGH,
    }
    return mapping.get(sev.upper(), VulnerabilitySeverity.MEDIUM)
