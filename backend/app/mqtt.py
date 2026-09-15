# app/routers/dashboard.py

import logging

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models import FaultEvent, User
from app.schemas import LiveReading
from app.websocket import manager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


# ============================================================
# GET LATEST READING
# ============================================================

@router.get(
    "/live",
    response_model=LiveReading,
)
async def get_latest_reading(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):

    query = (
        select(FaultEvent)
        .order_by(
            FaultEvent.received_at.desc()
        )
        .limit(1)
    )

    event = (
        await db.execute(query)
    ).scalar_one_or_none()

    if not event:
        raise HTTPException(
            status_code=404,
            detail="No readings yet.",
        )

    return LiveReading(
        fault_class=event.fault_class,
        confidence=event.confidence,
        accel_rms_z=event.accel_rms_z,
        vibe_mag=None,
        nozzle_temp=event.nozzle_temp,
        bed_temp=event.bed_temp,
        received_at=event.received_at,
        event_id=event.id,
    )


# ============================================================
# LIVE WEBSOCKET
# ============================================================

@router.websocket(
    "/ws/live"
)
async def websocket_live(
    ws: WebSocket,
    token: str = Query(
        ...,
        description="JWT access token passed as query param",
    ),
    db: AsyncSession = Depends(get_db),
):

    from jose import JWTError, jwt
    from app.auth import get_user_by_username

    # --------------------------------------------------------
    # Authenticate JWT
    # --------------------------------------------------------

    try:

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        username = payload.get(
            "sub"
        )

        if not username:
            await ws.close(
                code=4001
            )
            return

        user = await get_user_by_username(
            db,
            username,
        )

        if not user or not user.is_active:
            await ws.close(
                code=4001
            )
            return

    except JWTError:

        logger.warning(
            "WebSocket authentication failed."
        )

        await ws.close(
            code=4001
        )

        return

    except Exception:

        logger.exception(
            "Unexpected WebSocket authentication error."
        )

        await ws.close(
            code=4001
        )

        return

    # --------------------------------------------------------
    # Connect WebSocket
    # --------------------------------------------------------

    await manager.connect(
        ws,
        user_id=user.id,
    )

    logger.info(
        "WebSocket connected for user %s",
        user.id,
    )

    # --------------------------------------------------------
    # Send latest DATABASE event when connecting
    #
    # This is only the historical/latest ML event.
    # Live MQTT readings will come through manager.broadcast().
    # --------------------------------------------------------

    try:

        query = (
            select(FaultEvent)
            .order_by(
                FaultEvent.received_at.desc()
            )
            .limit(1)
        )

        latest = (
            await db.execute(query)
        ).scalar_one_or_none()

        if latest:

            await manager.send_to(
                ws,
                {
                    "type": "live_reading",
                    "fault_class": latest.fault_class.value,
                    "confidence": latest.confidence,
                    "accel_rms_z": latest.accel_rms_z,
                    "vibe_mag": None,
                    "nozzle_temp": latest.nozzle_temp,
                    "bed_temp": latest.bed_temp,
                    "received_at": latest.received_at.isoformat(),
                    "event_id": latest.id,
                },
            )

    except Exception:

        logger.exception(
            "Failed to send latest reading to WebSocket."
        )

    # --------------------------------------------------------
    # Keep connection alive
    # --------------------------------------------------------

    try:

        while True:

            message = await ws.receive_text()

            logger.debug(
                "WS message from user %s: %s",
                user.id,
                message,
            )

    except WebSocketDisconnect:

        manager.disconnect(ws)

        logger.info(
            "WS disconnected for user %s",
            user.id,
        )

    except Exception:

        manager.disconnect(ws)

        logger.exception(
            "Unexpected WebSocket error for user %s",
            user.id,
        )
