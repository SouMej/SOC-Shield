"""
Alerts API Routes — CRUD, acknowledgment, and streaming for alerts.
"""
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from typing import Optional
from services.elasticsearch_service import es_service
from websocket.manager import ws_manager

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


@router.get("")
async def get_alerts(
    severity: str = Query(default=None),
    acknowledged: bool = Query(default=None),
    size: int = Query(default=50, le=200),
    time_from: str = Query(default="now-24h"),
):
    """Get alerts with optional filters."""
    return await es_service.get_alerts(
        severity=severity, acknowledged=acknowledged,
        size=size, time_from=time_from,
    )


@router.post("/{alert_index}/{alert_id}/acknowledge")
async def acknowledge_alert(alert_index: str, alert_id: str):
    """Acknowledge an alert."""
    success = await es_service.acknowledge_alert(
        index=alert_index, alert_id=alert_id, user="analyst"
    )
    return {"success": success}


@router.websocket("/stream")
async def alert_stream(websocket: WebSocket):
    """WebSocket endpoint for real-time alert streaming."""
    await ws_manager.connect(websocket)
    try:
        # Send recent alerts as initial snapshot
        recent = await es_service.get_alerts(size=30, time_from="now-1h")
        await ws_manager.send_personal(websocket, {
            "type": "snapshot",
            "data": recent,
        })
        # Keep connection alive and listen for client messages
        while True:
            data = await websocket.receive_text()
            # Client can send ping or filter requests
            if data == "ping":
                await ws_manager.send_personal(websocket, {"type": "pong"})
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
