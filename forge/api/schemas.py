"""Pydantic schemas for API request/response validation."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Health ───────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str


# ── Project ──────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    root_path: str = Field(..., description="Path to the project directory")
    name: Optional[str] = Field(None, description="Project name (defaults to directory name)")
    default_runner: Optional[str] = Field(None, description="Default runner type")
    allowed_paths: Optional[str] = Field(None, description="Allowed paths pattern")


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, description="New project name")
    default_runner: Optional[str] = Field(None)
    default_agent_id: Optional[str] = Field(None)
    allowed_paths: Optional[str] = Field(None)
    env_json: Optional[str] = Field(None)
    security_policy_json: Optional[str] = Field(None)


class ProjectResponse(BaseModel):
    id: str
    name: str
    root_path: str
    allowed_paths: Optional[str] = None
    default_agent_id: Optional[str] = None
    default_runner: Optional[str] = None
    env_json: Optional[str] = None
    security_policy_json: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]
    total: int


# ── Agent ────────────────────────────────────────────────────────

class AgentCreate(BaseModel):
    name: str = Field(..., description="Unique agent name")
    runner: str = Field(..., description="Runner type: claude, codex, openai-compatible, etc.")
    model: Optional[str] = Field(None, description="Model identifier")
    system_prompt: Optional[str] = Field(None, description="System prompt")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1)


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None)
    runner: Optional[str] = Field(None)
    model: Optional[str] = Field(None)
    system_prompt: Optional[str] = Field(None)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1)
    tool_policy_json: Optional[str] = Field(None)


class AgentResponse(BaseModel):
    id: str
    name: str
    runner: str
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    tool_policy_json: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class AgentListResponse(BaseModel):
    agents: list[AgentResponse]
    total: int


# ── Session ──────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    project: str = Field(..., description="Project ID or name")
    agent: str = Field(..., description="Agent ID or name")
    title: Optional[str] = Field(None, description="Session title")
    cwd: Optional[str] = Field(None, description="Working directory override")


class SessionResponse(BaseModel):
    id: str
    project_id: str
    agent_id: str
    title: Optional[str] = None
    status: str
    runner: str
    external_session_id: Optional[str] = None
    cwd: Optional[str] = None
    metadata_json: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
    total: int


# ── Message ──────────────────────────────────────────────────────

class MessageCreate(BaseModel):
    role: str = Field(..., description="Message role: user, assistant, system, tool")
    content: str = Field(..., description="Message content")
    run: bool = Field(False, description="If true, trigger an AI turn after adding the message")


class TurnResult(BaseModel):
    """Result of running an AI turn."""
    success: bool
    messages: list[dict] = []
    error: Optional[str] = None
    session_status: str = "idle"


class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: Optional[str] = None
    seq: int
    metadata_json: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}


class MessageListResponse(BaseModel):
    messages: list[MessageResponse]
    total: int


# ── Error ────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    code: str
    message: str
    detail: Optional[Any] = None
