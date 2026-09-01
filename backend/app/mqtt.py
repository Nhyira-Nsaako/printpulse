import json
import logging
import ssl
import asyncio
from datetime import datetime, timezone

import aiomqtt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal
from app.models import FaultEvent
from app.schemas import MQTTPayload
from app.websocket import manager
from app.alerts import dispatch_alerts

logger = logging.getLogger(__name__)


async def _handle_message(payload: dict, db: AsyncSession) -> FaultEvent:
    """Parse the MQTT payload, persist to DB, broadcast to WebSocket clients."""

    data = MQTTPayload(**payload)

    event = FaultEvent(
        fault_class=data.fault_class,
        confidence=data.confidence,
        accel_rms_z=data.accel_rms_z,
        current_rms=data.current_rms,
        temperature=data.temperature,
        esp32_timestamp=data.timestamp,
        received_at=datetime.now(timezone.utc),
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    await manager.broadcast({
        "type": "live_reading",
        "fault_class": event.fault_class.value,
        "confidence": event.confidence,
        "accel_rms_z": event.accel_rms_z,
        "current_rms": event.current_rms,
        "temperature": event.temperature,
        "received_at": event.received_at.isoformat(),
        "event_id": event.id,
    })

    await dispatch_alerts(event, db)
    return event


async def mqtt_listener():
    """
    Long-running background task that subscribes to the ESP32 MQTT topic
    and processes every incoming message.
    Reconnects automatically on connection loss.
    """
    logger.info(
        f"MQTT listener starting — "
        f"broker={settings.MQTT_BROKER}:{settings.MQTT_PORT} "
        f"topic={settings.MQTT_TOPIC}"
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
                await client.subscribe(settings.MQTT_TOPIC)
                logger.info(f"Subscribed to {settings.MQTT_TOPIC}")

                async for message in client.messages:
                    try:
                        raw = json.loads(message.payload.decode())
                        async with AsyncSessionLocal() as db:
                            event = await _handle_message(raw, db)
                            logger.debug(
                                f"Event #{event.id}: {event.fault_class.value} "
                                f"({event.confidence*100:.1f}%)"
                            )
                    except json.JSONDecodeError:
                        logger.warning(
                            f"Non-JSON MQTT payload: {message.payload}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Error handling MQTT message: {e}",
                            exc_info=True
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
