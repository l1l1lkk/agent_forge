"""WebSocket API routes — real-time event streaming.

Full WebSocket event streaming will be implemented in Milestone 4.
This is a minimal placeholder.
"""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time event streaming.

    Placeholder: accepts connections and echoes back.
    Full implementation (subscribe, event streaming) in Milestone 4.
    """
    await websocket.accept()
    await websocket.send_json({"type": "connected", "message": "WebSocket endpoint ready"})

    try:
        while True:
            data = await websocket.receive_json()
            await websocket.send_json({
                "type": "echo",
                "received": data,
            })
    except WebSocketDisconnect:
        pass
