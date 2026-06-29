"""Session API routes — CRUD for sessions and messages, plus async AI run execution."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from forge.api.deps import get_db
from forge.api.schemas import (
    ErrorResponse,
    MessageCreate,
    MessageListResponse,
    MessageResponse,
    SessionCreate,
    SessionListResponse,
    SessionResponse,
)
from forge.core.errors import NotFoundError, ConflictError
from forge.services.session_manager import SessionManager
from forge.services.run_manager import RunManager, get_session_events

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    project_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List all sessions, optionally filtered by project."""
    mgr = SessionManager(db)
    items = await mgr.list_sessions(project_id=project_id)
    return SessionListResponse(
        sessions=[SessionResponse.model_validate(s) for s in items],
        total=len(items),
    )


@router.post(
    "",
    response_model=SessionResponse,
    status_code=201,
    responses={404: {"model": ErrorResponse}},
)
async def create_session(
    body: SessionCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new session."""
    mgr = SessionManager(db)
    try:
        session = await mgr.create_session(
            project_identifier=body.project,
            agent_identifier=body.agent,
            title=body.title,
            cwd=body.cwd,
        )
        return SessionResponse.model_validate(session)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": e.code, "message": e.message})


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get a session with its messages."""
    mgr = SessionManager(db)
    try:
        session = await mgr.get_session(session_id)
        return SessionResponse.model_validate(session)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": e.code, "message": e.message})


@router.get(
    "/{session_id}/messages",
    response_model=MessageListResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_messages(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get all messages for a session."""
    mgr = SessionManager(db)
    try:
        await mgr.get_session(session_id)
        messages = await mgr.get_messages(session_id)
        return MessageListResponse(
            messages=[MessageResponse.model_validate(m) for m in messages],
            total=len(messages),
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": e.code, "message": e.message})


@router.post(
    "/{session_id}/messages",
    response_model=MessageResponse,
    status_code=201,
    responses={404: {"model": ErrorResponse}},
)
async def add_message(
    session_id: str,
    body: MessageCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add a message to a session. Set run=true to trigger an async AI turn."""
    mgr = SessionManager(db)
    try:
        # Save user message first
        message = await mgr.add_message(
            session_id=session_id,
            role=body.role,
            content=body.content,
        )
        # If run=true, start async background turn (non-blocking)
        if body.run and body.role == "user":
            run_mgr = RunManager(db)
            try:
                await run_mgr.start_run(session_id, body.content)
            except ConflictError:
                pass  # Already running — message still saved
        return MessageResponse.model_validate(message)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": e.code, "message": e.message})
    except ConflictError as e:
        raise HTTPException(status_code=409, detail={"code": e.code, "message": e.message})
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"code": "VALIDATION", "message": str(e)})


class RunCreate(BaseModel):
    content: str = Field(..., description="User prompt")

class RunResponse(BaseModel):
    run_id: str
    session_id: str
    status: str

class EventItem(BaseModel):
    id: str; type: str; seq: int; session_id: str | None = None
    task_id: str | None = None; payload: dict = {}
    created_at: str = ""

class EventsResponse(BaseModel):
    events: list[EventItem]
    total: int


@router.post("/{session_id}/runs", response_model=RunResponse, status_code=202)
async def start_run(session_id: str, body: RunCreate, db: AsyncSession = Depends(get_db)):
    """Start an async AI run. Returns immediately, events stream via WebSocket."""
    mgr = RunManager(db)
    try:
        result = await mgr.start_run(session_id, body.content)
        return RunResponse(**result)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": e.code, "message": e.message})
    except ConflictError as e:
        raise HTTPException(status_code=409, detail={"code": e.code, "message": e.message})


@router.get("/{session_id}/events", response_model=EventsResponse)
async def get_events(session_id: str, after_seq: int = Query(0), db: AsyncSession = Depends(get_db)):
    """Get session events for timeline replay."""
    try:
        events = await get_session_events(db, session_id, after_seq)
        return EventsResponse(events=[EventItem(**e) for e in events], total=len(events))
    except Exception as e:
        raise HTTPException(status_code=500, detail={"code": "ERROR", "message": str(e)})


@router.post(
    "/{session_id}/interrupt",
    response_model=SessionResponse,
    responses={404: {"model": ErrorResponse}},
)
async def interrupt_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Interrupt a running session."""
    mgr = SessionManager(db)
    try:
        await mgr.interrupt_session(session_id)
        session = await mgr.get_session(session_id)
        return SessionResponse.model_validate(session)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": e.code, "message": e.message})


@router.delete(
    "/{session_id}",
    status_code=204,
    responses={404: {"model": ErrorResponse}},
)
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a session and all its messages/events."""
    mgr = SessionManager(db)
    try:
        await mgr.delete_session(session_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": e.code, "message": e.message})
