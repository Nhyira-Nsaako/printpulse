import logging
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import FaultEvent, User
from app.schemas import LiveReading
from app.auth import get_current_user
from app.websocket import manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/live", response_model=LiveReading)
async def get_latest_reading(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    REST fallback: returns the most recent classification result.
    The dashboard calls this on page load before the WebSocket connects.
    """
    q = select(FaultEvent).order_by(FaultEvent.received_at.desc()).limit(1)
    event = (await db.execute(q)).scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="No readings yet.")
    return LiveReading(
        fault_class=event.fault_class,
        confidence=event.confidence,
        accel_rms_z=event.accel_rms_z,
        current_rms=event.current_rms,
        temperature=event.temperature,
        received_at=event.received_at,
    )


@router.websocket("/ws/live")
async def websocket_live(
    ws: WebSocket,
    token: str = Query(..., description="JWT access token passed as query param"),
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket endpoint.

    Connection URL:  ws://localhost:8000/dashboard/ws/live?token=<JWT>

    Messages sent by server:
      { "type": "live_reading", "fault_class": "...", "confidence": 0.97, ... }
      { "type": "ping" }

    Messages accepted from client:
      { "type": "pong" }   — keepalive
    """
    # Validate JWT before accepting
    from jose import JWTError, jwt
    from app.config import settings
    from app.auth import get_user_by_username

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        user = await get_user_by_username(db, username)
        if not user or not user.is_active:
            await ws.close(code=4001)
            return
    except JWTError:
        await ws.close(code=4001)
        return

    await manager.connect(ws, user_id=user.id)

    # Send the latest reading immediately on connect
    q = select(FaultEvent).order_by(FaultEvent.received_at.desc()).limit(1)
    latest = (await db.execute(q)).scalar_one_or_none()
    if latest:
        await manager.send_to(ws, {
            "type": "live_reading",
            "fault_class": latest.fault_class.value,
            "confidence": latest.confidence,
            "accel_rms_z": latest.accel_rms_z,
            "current_rms": latest.current_rms,
            "temperature": latest.temperature,
            "received_at": latest.received_at.isoformat(),
            "event_id": latest.id,
        })

    try:
        while True:
            # Keep connection alive; handle pong from client
            msg = await ws.receive_text()
            logger.debug(f"WS message from user {user.id}: {msg}")
    except WebSocketDisconnect:
        manager.disconnect(ws)
        logger.info(f"WS disconnected for user {user.id}")


# Fix missing import
from fastapi import HTTPException
