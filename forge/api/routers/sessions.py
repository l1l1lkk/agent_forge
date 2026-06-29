"""Session API routes — CRUD for sessions and messages, plus AI turn execution."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from forge.api.deps import get_db
from forge.api.schemas import (
    ErrorResponse,
    MessageCreate,
    MessageListResponse,
    MessageResponse,
    SessionCreate,
    SessionListResponse,
    SessionResponse,
    TurnResult,
)
from forge.core.errors import NotFoundError, ConflictError
from forge.services.session_manager import SessionManager

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
    """Add a message to a session. Set run=true to trigger an AI turn."""
    mgr = SessionManager(db)
    try:
        if body.run and body.role == "user":
            # Run a full AI turn — this adds the user message and runs the agent
            result = await mgr.run_turn(
                session_id=session_id,
                user_prompt=body.content,
            )
            # Return a placeholder message response with the user message
            messages = await mgr.get_messages(session_id)
            if messages:
                last_user = [m for m in messages if m.role == "user"][-1]
                return MessageResponse.model_validate(last_user)

        # Just add the message without running
        message = await mgr.add_message(
            session_id=session_id,
            role=body.role,
            content=body.content,
        )
        return MessageResponse.model_validate(message)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": e.code, "message": e.message})
    except ConflictError as e:
        raise HTTPException(status_code=409, detail={"code": e.code, "message": e.message})
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"code": "VALIDATION", "message": str(e)})


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
