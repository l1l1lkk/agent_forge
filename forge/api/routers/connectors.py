"""Connector API routes."""

from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter

router = APIRouter(prefix="/connectors", tags=["connectors"])


class ConnectorResponse(BaseModel):
    id: str
    type: str
    label: str
    account: str
    status: str


class ConnectorListResponse(BaseModel):
    connectors: list[ConnectorResponse]
    total: int


@router.get("", response_model=ConnectorListResponse)
async def list_connectors():
    """List configured connectors.

    Connector persistence is not implemented yet, so the real API returns an
    empty collection instead of letting the desktop UI display mock accounts.
    """
    return ConnectorListResponse(connectors=[], total=0)
