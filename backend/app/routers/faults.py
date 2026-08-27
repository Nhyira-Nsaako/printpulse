from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.database import get_db
from app.models import FaultEvent, FaultClass, User
from app.schemas import (
    FaultEventOut, FaultEventPage, FaultEventAcknowledge,
    FaultStats, TrendData, TrendPoint,
)
from app.auth import get_current_user

router = APIRouter(prefix="/faults", tags=["Fault Events"])


@router.get("", response_model=FaultEventPage)
async def list_faults(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    fault_class: Optional[FaultClass] = None,
    acknowledged: Optional[bool] = None,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Paginated fault event history with optional filters."""
    filters = []
    if fault_class:
        filters.append(FaultEvent.fault_class == fault_class)
    if acknowledged is not None:
        filters.append(FaultEvent.acknowledged == acknowledged)
    if from_dt:
        filters.append(FaultEvent.received_at >= from_dt)
    if to_dt:
        filters.append(FaultEvent.received_at <= to_dt)

    count_q = select(func.count()).select_from(FaultEvent)
    if filters:
        count_q = count_q.where(and_(*filters))
    total = (await db.execute(count_q)).scalar()

    q = select(FaultEvent).order_by(FaultEvent.received_at.desc())
    if filters:
        q = q.where(and_(*filters))
    q = q.offset((page - 1) * page_size).limit(page_size)
    items = (await db.execute(q)).scalars().all()

    return FaultEventPage(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, -(-total // page_size)),  # ceiling division
    )


@router.get("/stats", response_model=FaultStats)
async def fault_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Aggregated counts for the dashboard stats panel."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    async def count(where=None):
        q = select(func.count()).select_from(FaultEvent)
        if where is not None:
            q = q.where(where)
        return (await db.execute(q)).scalar()

    return FaultStats(
        total_events=await count(),
        normal_count=await count(FaultEvent.fault_class == FaultClass.NORMAL),
        nozzle_clog_count=await count(FaultEvent.fault_class == FaultClass.NOZZLE_CLOG),
        motor_fault_count=await count(FaultEvent.fault_class == FaultClass.MOTOR_FAULT),
        thermal_runaway_count=await count(FaultEvent.fault_class == FaultClass.THERMAL_RUNAWAY),
        unacknowledged_faults=await count(
            and_(FaultEvent.fault_class != FaultClass.NORMAL, FaultEvent.acknowledged == False)
        ),
        last_24h_faults=await count(
            and_(FaultEvent.fault_class != FaultClass.NORMAL, FaultEvent.received_at >= cutoff)
        ),
    )


@router.get("/trend", response_model=TrendData)
async def fault_trend(
    minutes: int = Query(60, ge=5, le=1440, description="Lookback window in minutes"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Returns every reading in the last N minutes for trend chart rendering.
    The frontend draws time-series from this data.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    q = (
        select(FaultEvent)
        .where(FaultEvent.received_at >= cutoff)
        .order_by(FaultEvent.received_at.asc())
    )
    events = (await db.execute(q)).scalars().all()
    points = [
        TrendPoint(
            received_at=e.received_at,
            fault_class=e.fault_class,
            confidence=e.confidence,
            accel_rms_z=e.accel_rms_z,
            current_rms=e.current_rms,
            temperature=e.temperature,
        )
        for e in events
    ]
    return TrendData(points=points)


@router.get("/{event_id}", response_model=FaultEventOut)
async def get_fault(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    event = await db.get(FaultEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")
    return event


@router.post("/{event_id}/acknowledge", response_model=FaultEventOut)
async def acknowledge_fault(
    event_id: int,
    body: FaultEventAcknowledge,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a fault event as acknowledged by the current user."""
    event = await db.get(FaultEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")
    if event.acknowledged:
        raise HTTPException(status_code=400, detail="Event already acknowledged.")

    event.acknowledged = True
    event.acknowledged_at = datetime.now(timezone.utc)
    event.acknowledged_by = current_user.id
    if body.notes:
        event.notes = body.notes

    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event
