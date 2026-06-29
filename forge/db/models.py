"""SQLAlchemy ORM models for forge-agent.

Defines all core entities: projects, agents, sessions, messages,
events, tasks, schedules, and audit logs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from forge.db.base import Base

# A small helper for UTC timestamps
_utc_now = lambda: datetime.now(timezone.utc)


# ── Project ──────────────────────────────────────────────────────

class ProjectModel(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    root_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    allowed_paths: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    default_agent_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    default_runner: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    env_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    security_policy_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(
        String(32), default=lambda: _utc_now().isoformat()
    )
    updated_at: Mapped[str] = mapped_column(
        String(32), default=lambda: _utc_now().isoformat()
    )

    # Relationships
    sessions = relationship("SessionModel", back_populates="project", cascade="all, delete-orphan")


# ── Agent ────────────────────────────────────────────────────────

class AgentModel(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    runner: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    temperature: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tool_policy_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(
        String(32), default=lambda: _utc_now().isoformat()
    )
    updated_at: Mapped[str] = mapped_column(
        String(32), default=lambda: _utc_now().isoformat()
    )

    # Relationships
    sessions = relationship("SessionModel", back_populates="agent")


# ── Session ──────────────────────────────────────────────────────

class SessionModel(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("projects.id"), nullable=False, index=True
    )
    agent_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("agents.id"), nullable=False
    )
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="idle")
    runner: Mapped[str] = mapped_column(String(64), nullable=False, default="codex")
    external_session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cwd: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(
        String(32), default=lambda: _utc_now().isoformat()
    )
    updated_at: Mapped[str] = mapped_column(
        String(32), default=lambda: _utc_now().isoformat()
    )

    # Relationships
    project = relationship("ProjectModel", back_populates="sessions")
    agent = relationship("AgentModel", back_populates="sessions")
    messages = relationship(
        "MessageModel", back_populates="session",
        cascade="all, delete-orphan",
        order_by="MessageModel.seq",
    )
    events = relationship(
        "EventModel", back_populates="session",
        cascade="all, delete-orphan",
    )


# ── Message ──────────────────────────────────────────────────────

class MessageModel(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("sessions.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    seq: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(
        String(32), default=lambda: _utc_now().isoformat()
    )

    # Relationships
    session = relationship("SessionModel", back_populates="messages")


# ── Event ────────────────────────────────────────────────────────

class EventModel(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    session_id: Mapped[Optional[str]] = mapped_column(
        String(32), ForeignKey("sessions.id"), nullable=True, index=True
    )
    task_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[str] = mapped_column(
        String(32), default=lambda: _utc_now().isoformat()
    )

    # Relationships
    session = relationship("SessionModel", back_populates="events")


# ── Task ─────────────────────────────────────────────────────────

class TaskModel(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    session_id: Mapped[Optional[str]] = mapped_column(
        String(32), ForeignKey("sessions.id"), nullable=True, index=True
    )
    project_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    command: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    pid: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    exit_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    started_at: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    finished_at: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    created_at: Mapped[str] = mapped_column(
        String(32), default=lambda: _utc_now().isoformat()
    )
    updated_at: Mapped[str] = mapped_column(
        String(32), default=lambda: _utc_now().isoformat()
    )


# ── Schedule ─────────────────────────────────────────────────────

class ScheduleModel(Base):
    __tablename__ = "schedules"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(String(32), nullable=False)
    agent_id: Mapped[str] = mapped_column(String(32), nullable=False)
    cron: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[str] = mapped_column(
        String(32), default=lambda: _utc_now().isoformat()
    )
    updated_at: Mapped[str] = mapped_column(
        String(32), default=lambda: _utc_now().isoformat()
    )


# ── Audit Log ────────────────────────────────────────────────────

class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    actor: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    target_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    target_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    payload_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(
        String(32), default=lambda: _utc_now().isoformat()
    )
