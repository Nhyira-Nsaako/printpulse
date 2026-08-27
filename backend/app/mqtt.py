import json
import logging
import ssl
import asyncio
from datetime import datetime, timezone

import aiomqtt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal
from app.models import FaultEvent, FaultClass
from app.schemas import MQTTPayload
from app.websocket import manager
from app.alerts import dispatch_alerts

logger = logging.getLogger(__name__)


async def _handle_message(payload: dict, db: AsyncSession) -> FaultEvent:
    """Parse the MQTT payload, persist to DB, broadcast to WebSocket clients."""

    # Validate with Pydantic
    data = MQTTPayload(**payload)

    # Persist to DB
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

    # Broadcast to all connected WebSocket clients
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

    # Dispatch email / SMS alerts if threshold exceeded
    await dispatch_alerts(event, db)

    return event


async def mqtt_listener():
    """
    Long-running background task that subscribes to the HiveMQ MQTT topic
    and processes every incoming message.
    Supports TLS encryption (port 8883) and auto-reconnects on connection loss.
    """
    logger.info(f"MQTT listener starting — broker={settings.MQTT_BROKER}:{settings.MQTT_PORT} topic={settings.MQTT_TOPIC}")

    reconnect_interval = 5  # seconds

    while True:
        try:
            connect_kwargs = {}
            if settings.MQTT_USERNAME:
                connect_kwargs["username"] = settings.MQTT_USERNAME
            if settings.MQTT_PASSWORD:
                connect_kwargs["password"] = settings.MQTT_PASSWORD

            # Configure SSL/TLS parameters required by HiveMQ Cloud (port 8883)
            if settings.MQTT_PORT == 8883:
                connect_kwargs["tls_params"] = aiomqtt.TLSParameters(
                    cert_reqs=ssl.CERT_REQUIRED,
                    tls_version=ssl.PROTOCOL_TLSv1_2,
                )

            async with aiomqtt.Client(
                hostname=settings.MQTT_BROKER,
                port=settings.MQTT_PORT,
                **connect_kwargs,
            ) as client:
                logger.info("MQTT connected successfully to HiveMQ.")
                await client.subscribe(settings.MQTT_TOPIC)
                logger.info(f"Subscribed to topic: {settings.MQTT_TOPIC}")

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
                        logger.warning(f"Non-JSON MQTT payload received: {message.payload}")
                    except Exception as e:
                        logger.error(f"Error handling MQTT message: {e}", exc_info=True)

        except aiomqtt.MqttError as e:
            logger.warning(f"MQTT connection lost ({e}). Reconnecting in {reconnect_interval}s…")
            await asyncio.sleep(reconnect_interval)
        except Exception as e:
            logger.error(f"Unexpected MQTT error: {e}", exc_info=True)
            await asyncio.sleep(reconnect_interval)