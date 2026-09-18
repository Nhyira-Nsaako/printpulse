# app/mqtt.py

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

import paho.mqtt.client as mqtt

from app.config import settings
from app.database import AsyncSessionLocal
from app.models import FaultEvent
from app.websocket import manager
from app.alerts import dispatch_alerts

logger = logging.getLogger(__name__)


# ============================================================
# LATEST SENSOR / ML DATA
# ============================================================

latest_vibration: dict[str, Any] = {}
latest_printer: dict[str, Any] = {}
latest_status: dict[str, Any] = {}


# ============================================================
# BUILD LIVE READING
# ============================================================

def build_live_reading() -> dict[str, Any]:
    """
    Combine the latest vibration, printer and ML data
    into the format expected by the frontend.
    """

    vibration = latest_vibration or {}
    printer = latest_printer or {}
    status = latest_status or {}

    # Always normalize the fault class to uppercase.
    fault_class = str(
        status.get("fault_class", "NORMAL")
    ).upper()

    return {
        "type": "live_reading",

        # ML classification
        "fault_class": fault_class,
        "confidence": status.get("confidence", 0.0),

        # Vibration
        "accel_rms_z": vibration.get("vibe_z"),
        "vibe_mag": vibration.get("vibe_mag"),

        # Printer temperatures
        "nozzle_temp": printer.get("nozzle_temp"),
        "bed_temp": printer.get("bed_temp"),

        # Server timestamp
        "received_at": datetime.now(
            timezone.utc
        ).isoformat(),

        # Database event ID
        "event_id": status.get("event_id"),
    }


# ============================================================
# BROADCAST TO DASHBOARD
# ============================================================

async def broadcast_live_reading() -> None:
    """
    Send the latest combined sensor/ML reading
    to every connected dashboard WebSocket.
    """

    if manager.client_count == 0:
        logger.debug(
            "No WebSocket clients connected. "
            "Live reading will not be broadcast."
        )
        return

    reading = build_live_reading()

    logger.info(
        "Broadcasting live reading to %s clients: %s",
        manager.client_count,
        reading,
    )

    await manager.broadcast(reading)


# ============================================================
# MQTT CONNECT
# ============================================================

def on_connect(
    client: mqtt.Client,
    userdata: Any,
    flags: dict,
    reason_code: Any,
    properties: Any = None,
) -> None:
    """
    Called when the MQTT client connects to HiveMQ.
    """

    logger.info(
        "Connected to MQTT broker | reason_code=%s",
        reason_code,
    )

    if reason_code != 0:
        logger.error(
            "MQTT connection failed | reason_code=%s",
            reason_code,
        )
        return

    topics = [
        settings.MQTT_TOPIC_VIBRATION,
        settings.MQTT_TOPIC_TEMPERATURE,
        settings.MQTT_TOPIC_STATUS,
    ]

    for topic in topics:
        result, _ = client.subscribe(topic)

        if result == mqtt.MQTT_ERR_SUCCESS:
            logger.info(
                "Subscribed to MQTT topic: %s",
                topic,
            )
        else:
            logger.error(
                "Failed to subscribe to MQTT topic: %s | result=%s",
                topic,
                result,
            )


# ============================================================
# MQTT DISCONNECT
# ============================================================

def on_disconnect(
    client: mqtt.Client,
    userdata: Any,
    disconnect_flags: Any,
    reason_code: Any,
    properties: Any = None,
) -> None:
    """
    Called when the MQTT client disconnects.
    """

    logger.warning(
        "Disconnected from MQTT broker | reason_code=%s",
        reason_code,
    )


# ============================================================
# MQTT MESSAGE RECEIVED
# ============================================================

def on_message(
    client: mqtt.Client,
    userdata: Any,
    msg: mqtt.MQTTMessage,
) -> None:
    """
    Called whenever a subscribed MQTT message arrives.
    """

    global latest_vibration
    global latest_printer
    global latest_status

    try:
        payload = json.loads(
            msg.payload.decode("utf-8")
        )

        logger.info(
            "MQTT message received | topic=%s | payload=%s",
            msg.topic,
            payload,
        )

    except json.JSONDecodeError:
        logger.exception(
            "Invalid JSON received from MQTT topic %s",
            msg.topic,
        )
        return

    except Exception:
        logger.exception(
            "Failed to decode MQTT message from topic %s",
            msg.topic,
        )
        return

    # --------------------------------------------------------
    # VIBRATION
    # --------------------------------------------------------

    if msg.topic == settings.MQTT_TOPIC_VIBRATION:

        latest_vibration = {
            "vibe_x": payload.get("vibe_x"),
            "vibe_y": payload.get("vibe_y"),
            "vibe_z": payload.get("vibe_z"),
            "vibe_mag": payload.get("vibe_mag"),
        }

        logger.info(
            "Updated vibration data: %s",
            latest_vibration,
        )

        # Broadcast immediately.
        asyncio.create_task(
            broadcast_live_reading()
        )

        return

    # --------------------------------------------------------
    # PRINTER TEMPERATURE
    # --------------------------------------------------------

    if msg.topic == settings.MQTT_TOPIC_TEMPERATURE:

        latest_printer = {
            "nozzle_temp": payload.get(
                "nozzle_actual"
            ),
            "nozzle_target": payload.get(
                "nozzle_target"
            ),
            "bed_temp": payload.get(
                "bed_actual"
            ),
            "bed_target": payload.get(
                "bed_target"
            ),
            "timestamp": payload.get(
                "timestamp"
            ),
        }

        logger.info(
            "Updated printer data: %s",
            latest_printer,
        )

        # Broadcast immediately.
        asyncio.create_task(
            broadcast_live_reading()
        )

        return

    # --------------------------------------------------------
    # ML STATUS
    # --------------------------------------------------------

    if msg.topic == settings.MQTT_TOPIC_STATUS:

        # Normalize fault class to uppercase.
        fault_class = str(
            payload.get(
                "fault_class",
                "NORMAL",
            )
        ).upper()

        latest_status = {
            "fault_class": fault_class,
            "confidence": payload.get(
                "confidence",
                0.0,
            ),
        }

        logger.info(
            "Updated ML status: %s",
            latest_status,
        )

        # Save the fault event first.
        #
        # The save function will update latest_status
        # with the generated database event ID.
        asyncio.create_task(
            save_and_broadcast_fault_event(
                payload
            )
        )

        return

    logger.warning(
        "Received message from unexpected topic: %s",
        msg.topic,
    )


# ============================================================
# SAVE FAULT EVENT AND BROADCAST
# ============================================================

async def save_and_broadcast_fault_event(
    payload: dict[str, Any],
) -> None:
    """
    Save an ML classification to PostgreSQL and then
    broadcast the updated live reading.

    The fault class is always normalized to uppercase.
    """

    await save_fault_event(payload)

    await broadcast_live_reading()


# ============================================================
# SAVE FAULT EVENT
# ============================================================

async def save_fault_event(
    payload: dict[str, Any],
) -> None:
    """
    Save an ML classification to PostgreSQL.

    This only runs when a message is received on
    printpulse/status.
    """

    global latest_status

    try:

        # ----------------------------------------------------
        # Fault classification
        # ----------------------------------------------------

        fault_class = str(
            payload.get(
                "fault_class",
                "NORMAL",
            )
        ).upper()

        # ----------------------------------------------------
        # Confidence
        # ----------------------------------------------------

        confidence = float(
            payload.get(
                "confidence",
                0.0,
            )
        )

        # ----------------------------------------------------
        # Vibration
        # ----------------------------------------------------

        accel_rms_z = latest_vibration.get(
            "vibe_z"
        )

        if accel_rms_z is None:
            accel_rms_z = 0.0

        accel_rms_z = float(
            accel_rms_z
        )

        # ----------------------------------------------------
        # Printer temperatures
        # ----------------------------------------------------

        nozzle_temp = latest_printer.get(
            "nozzle_temp"
        )

        bed_temp = latest_printer.get(
            "bed_temp"
        )

        if nozzle_temp is None:
            nozzle_temp = 0.0

        if bed_temp is None:
            bed_temp = 0.0

        nozzle_temp = float(
            nozzle_temp
        )

        bed_temp = float(
            bed_temp
        )

        # ----------------------------------------------------
        # ESP32 timestamp
        # ----------------------------------------------------

        esp32_timestamp = payload.get(
            "timestamp"
        )

        if not isinstance(
            esp32_timestamp,
            int,
        ):
            esp32_timestamp = None

        # ----------------------------------------------------
        # Create database event
        # ----------------------------------------------------

        async with AsyncSessionLocal() as db:

            event = FaultEvent(
                fault_class=fault_class,
                confidence=confidence,
                accel_rms_z=accel_rms_z,
                nozzle_temp=nozzle_temp,
                bed_temp=bed_temp,
                esp32_timestamp=esp32_timestamp,
                received_at=datetime.now(
                    timezone.utc
                ),
                alert_sent=False,
                acknowledged=False,
            )

            db.add(event)

            await db.commit()

            await db.refresh(event)

            # ------------------------------------------------
            # Dispatch alerts
            # ------------------------------------------------

            alert_triggered = await dispatch_alerts(
                event,
                db,
            )

            if alert_triggered:
                event.alert_sent = True
                await db.commit()

            logger.info(
                "Fault event saved | id=%s | class=%s | confidence=%.3f | alert=%s",
                event.id,
                fault_class,
                confidence,
                alert_triggered,
            )

            # ------------------------------------------------
            # Store database ID for WebSocket message
            # ------------------------------------------------

            latest_status = {
                "fault_class": fault_class,
                "confidence": confidence,
                "event_id": event.id,
            }

    except Exception:
        logger.exception(
            "Failed to save fault event"
        )



# ============================================================
# MQTT LISTENER
# ============================================================

async def mqtt_listener() -> None:
    """
    Start the MQTT client and keep it connected.

    This runs as a background asyncio task from FastAPI's
    lifespan.
    """

    logger.info(
        "Starting MQTT listener..."
    )

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="printpulse-backend",
    )

    # --------------------------------------------------------
    # Authentication
    # --------------------------------------------------------

    client.username_pw_set(
        settings.MQTT_USERNAME,
        settings.MQTT_PASSWORD,
    )

    # --------------------------------------------------------
    # HiveMQ Cloud uses TLS on port 8883
    # --------------------------------------------------------

    if settings.MQTT_PORT == 8883:
        client.tls_set()

    # --------------------------------------------------------
    # Callbacks
    # --------------------------------------------------------

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    # --------------------------------------------------------
    # Connect
    # --------------------------------------------------------

    try:

        logger.info(
            "Connecting to MQTT broker %s:%s...",
            settings.MQTT_BROKER,
            settings.MQTT_PORT,
        )

        client.connect(
            settings.MQTT_BROKER,
            settings.MQTT_PORT,
            keepalive=60,
        )

        logger.info(
            "MQTT client connected successfully."
        )

    except Exception:

        logger.exception(
            "Failed to connect to MQTT broker."
        )

        return

    # --------------------------------------------------------
    # Run MQTT network loop
    #
    # loop() is used instead of loop_forever() because
    # loop_forever() would block FastAPI's asyncio event loop.
    # --------------------------------------------------------

    try:

        while True:

            client.loop(
                timeout=1.0
            )

            await asyncio.sleep(0.01)

    except asyncio.CancelledError:

        logger.info(
            "MQTT listener cancelled."
        )

        try:

            client.disconnect()

        except Exception:

            logger.exception(
                "Error while disconnecting MQTT client."
            )

        raise

    except Exception:

        logger.exception(
            "MQTT listener stopped unexpectedly."
        )

        try:

            client.disconnect()

        except Exception:

            logger.exception(
                "Error while disconnecting MQTT client."
            )
