import json
import logging
import ssl
import asyncio
from datetime import datetime, timezone
from typing import Optional

import aiomqtt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal
from app.models import FaultEvent
from app.schemas import MQTTPayload
from app.websocket import manager
from app.alerts import dispatch_alerts

logger = logging.getLogger(__name__)

# ── In-memory "latest known value" cache ──────────────────────────────────
# Vibration, temperature, and the prediction each arrive on their own topic
# instead of one combined payload, so we cache the most recent vibration/
# temperature values here and merge them in whenever a new prediction lands
# on the status topic. We also re-broadcast on every message (not just
# predictions) so the dashboard's live numbers update in real time.
_latest = {
    "fault_class": "NORMAL",
    "confidence": 0.0,
    "accel_rms_z": None,
    "nozzle_temp": None,
    "bed_temp": None,
}


def _first(payload: dict, *keys):
    """Return the first present, non-None value among the candidate keys."""
    for k in keys:
        if k in payload and payload[k] is not None:
            return payload[k]
    return None


async def _broadcast_live(event_id: Optional[int] = None):
    await manager.broadcast({
        "type": "live_reading",
        "fault_class": _latest["fault_class"],
        "confidence": _latest["confidence"],
        "accel_rms_z": _latest["accel_rms_z"],
        "nozzle_temp": _latest["nozzle_temp"],
        "bed_temp": _latest["bed_temp"],
        "received_at": datetime.now(timezone.utc).isoformat(),
        "event_id": event_id,
    })


async def _handle_vibration(payload: dict):
    """pulseprint/live — the ESP32 publishes two kinds of messages here:
    raw per-sample readings (vibe_x/vibe_y/vibe_z/vibe_mag, dominated by
    gravity ~9.8) and, once per completed 100-sample window, the windowed
    accel_rms_z feature (~0.03-0.1). We only care about the latter for the
    dashboard — it's the same feature the ML model consumes, and its scale
    is completely different from the raw magnitude, so mixing the two would
    make the displayed number meaningless."""
    value = _first(payload, "accel_rms_z", "head_rms")
    if value is None:
        return  # a raw vibe_x/y/z sample, not a windowed feature — ignore
    _latest["accel_rms_z"] = value
    await _broadcast_live()


async def _handle_temperature(payload: dict):
    """printpulse/printer — Marlin telemetry. Field names are
    nozzle_actual / bed_actual."""
    nozzle = _first(payload, "nozzle_actual", "nozzle_temp")
    bed = _first(payload, "bed_actual", "bed_temp")
    if nozzle is None and bed is None:
        return
    if nozzle is not None:
        _latest["nozzle_temp"] = nozzle
    if bed is not None:
        _latest["bed_temp"] = bed
    await _broadcast_live()


async def _handle_status(payload: dict, db: AsyncSession) -> FaultEvent:
    """printpulse/status — the model's fault prediction. This is the only
    topic that results in a persisted row, combined with whatever vibration/
    temperature values are currently cached."""

    if "predicted_label" in payload and "fault_class" not in payload:
        payload["fault_class"] = str(payload.pop("predicted_label")).upper()
    elif "fault_class" in payload and isinstance(payload["fault_class"], str):
        payload["fault_class"] = payload["fault_class"].upper()

    merged = {
        "fault_class": payload["fault_class"],
        "confidence": payload.get("confidence", 0.0),
        "accel_rms_z": _latest["accel_rms_z"],
        "nozzle_temp": _latest["nozzle_temp"],
        "bed_temp": _latest["bed_temp"],
        "timestamp": payload.get("timestamp"),
    }
    data = MQTTPayload(**merged)

    event = FaultEvent(
        fault_class=data.fault_class,
        confidence=data.confidence,
        accel_rms_z=data.accel_rms_z or 0.0,
        nozzle_temp=data.nozzle_temp or 0.0,
        bed_temp=data.bed_temp or 0.0,
        esp32_timestamp=data.timestamp,
        received_at=datetime.now(timezone.utc),
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    _latest["fault_class"] = event.fault_class.value
    _latest["confidence"] = event.confidence

    await _broadcast_live(event_id=event.id)
    await dispatch_alerts(event, db)
    return event


async def mqtt_listener():
    """
    Long-running background task that subscribes to all three PrintPulse
    MQTT topics (vibration, temperature, status) and processes every
    incoming message. Reconnects automatically on connection loss.
    """
    topics = [
        settings.MQTT_TOPIC_VIBRATION,
        settings.MQTT_TOPIC_TEMPERATURE,
        settings.MQTT_TOPIC_STATUS,
    ]
    logger.info(
        f"MQTT listener starting — "
        f"broker={settings.MQTT_BROKER}:{settings.MQTT_PORT} topics={topics}"
    )

    reconnect_interval = 5

    while True:
        try:
            # TLS context for HiveMQ cloud (port 8883)
            tls_context = ssl.create_default_context()

            async with aiomqtt.Client(
                hostname=settings.MQTT_BROKER,
                port=settings.MQTT_PORT,
                username=settings.MQTT_USERNAME if settings.MQTT_USERNAME else None,
                password=settings.MQTT_PASSWORD if settings.MQTT_PASSWORD else None,
                tls_context=tls_context,
            ) as client:
                logger.info("MQTT connected.")
                for t in topics:
                    await client.subscribe(t)
                    logger.info(f"Subscribed to {t}")

                async for message in client.messages:
                    topic = str(message.topic)

                    try:
                        raw = json.loads(message.payload.decode())
                    except json.JSONDecodeError:
                        logger.warning(f"Non-JSON MQTT payload on {topic}: {message.payload}")
                        continue

                    try:
                        if topic == settings.MQTT_TOPIC_VIBRATION:
                            await _handle_vibration(raw)
                        elif topic == settings.MQTT_TOPIC_TEMPERATURE:
                            await _handle_temperature(raw)
                        elif topic == settings.MQTT_TOPIC_STATUS:
                            async with AsyncSessionLocal() as db:
                                event = await _handle_status(raw, db)
                                logger.debug(
                                    f"Event #{event.id}: {event.fault_class.value} "
                                    f"({event.confidence*100:.1f}%)"
                                )
                        else:
                            logger.debug(f"Ignoring message on unrecognized topic {topic}")
                    except Exception as e:
                        logger.error(
                            f"Error handling MQTT message on {topic}: {e}",
                            exc_info=True,
                        )

        except aiomqtt.MqttError as e:
            logger.warning(
                f"MQTT connection lost ({e}). "
                f"Reconnecting in {reconnect_interval}s…"
            )
            await asyncio.sleep(reconnect_interval)

        except Exception as e:
            logger.error(f"Unexpected MQTT error: {e}", exc_info=True)
            await asyncio.sleep(reconnect_interval)
