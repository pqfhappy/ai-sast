import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase
import enum


class Base(DeclarativeBase):
    pass


class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class VulnerabilitySeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    repo_url = Column(String(512), default="")
    language = Column(String(50), default="")
    status = Column(SAEnum(ProjectStatus), default=ProjectStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class ScanTask(Base):
    __tablename__ = "scan_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, nullable=False)
    status = Column(SAEnum(ScanStatus), default=ScanStatus.PENDING)
    branch = Column(String(255), default="main")
    total_vulnerabilities = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class Vulnerability(Base):
    __tablename__ = "vulnerabilities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(Integer, nullable=False)
    file_path = Column(String(512), nullable=False)
    line_start = Column(Integer, nullable=True)
    line_end = Column(Integer, nullable=True)
    vulnerability_type = Column(String(255), nullable=False)
    severity = Column(SAEnum(VulnerabilitySeverity), default=VulnerabilitySeverity.MEDIUM)
    description = Column(Text, default="")
    code_snippet = Column(Text, default="")
    remediation = Column(Text, default="")
    confidence = Column(Integer, default=0)
    cwe_id = Column(String(50), default="")
    agent_notes = Column(Text, default="")
    is_false_positive = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
