import asyncio
import json
import logging
import ssl
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from app.config import settings
from app.database import AsyncSessionLocal
from app.models import FaultEvent, FaultClass
from app.websocket import manager


logger = logging.getLogger(__name__)


# =============================================================================
# LATEST SENSOR / MODEL DATA
# =============================================================================

latest_vibration = {
    "vibe_x": None,
    "vibe_y": None,
    "vibe_z": None,
    "vibe_mag": None,
    "accel_rms_z": None,
}

latest_printer = {
    "nozzle_temp": None,
    "bed_temp": None,
}

latest_status = {
    "fault_class": None,
    "confidence": None,
}


# =============================================================================
# BUILD LIVE DASHBOARD MESSAGE
# =============================================================================

def build_live_reading(event_id=None, received_at=None):
    """
    Build the message expected by the React dashboard.

    The WebSocket expects:

        {
            "type": "live_reading",
            "fault_class": "...",
            "confidence": ...,
            "accel_rms_z": ...,
            "nozzle_temp": ...,
            "bed_temp": ...,
            "received_at": "...",
            "event_id": ...
        }
    """

    fault_class = latest_status.get("fault_class")
    confidence = latest_status.get("confidence")

    # We cannot produce a complete LiveReading until we have
    # a classification result.
    if fault_class is None or confidence is None:
        return None

    return {
        "type": "live_reading",

        "fault_class": (
            fault_class.value
            if isinstance(fault_class, FaultClass)
            else fault_class
        ),

        "confidence": confidence,

        "accel_rms_z": latest_vibration.get("accel_rms_z"),

        "nozzle_temp": latest_printer.get("nozzle_temp"),

        "bed_temp": latest_printer.get("bed_temp"),

        "received_at": (
            received_at
            if received_at is not None
            else datetime.now(timezone.utc).isoformat()
        ),

        "event_id": event_id,
    }


# =============================================================================
# BROADCAST TO DASHBOARD
# =============================================================================

async def broadcast_live_reading(
    event_id=None,
    received_at=None,
):
    """
    Send the latest combined reading to all connected dashboard clients.
    """

    reading = build_live_reading(
        event_id=event_id,
        received_at=received_at,
    )

    if reading is None:
        logger.debug(
            "No complete classification available yet; "
            "not broadcasting live reading."
        )
        return

    if manager.client_count == 0:
        logger.debug(
            "No WebSocket clients connected."
        )
        return

    logger.info(
        "Broadcasting live reading to %s dashboard client(s): %s",
        manager.client_count,
        reading,
    )

    await manager.broadcast(reading)


# =============================================================================
# MQTT CONNECT
# =============================================================================

def on_connect(
    client,
    userdata,
    flags,
    reason_code,
    properties=None,
):
    """
    Called when the backend successfully connects to HiveMQ.
    """

    if reason_code != 0:
        logger.error(
            "MQTT connection failed. Reason code: %s",
            reason_code,
        )
        return

    logger.info("Connected to MQTT broker.")

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
                "Failed to subscribe to MQTT topic: %s (code=%s)",
                topic,
                result,
            )


# =============================================================================
# MQTT DISCONNECT
# =============================================================================

def on_disconnect(
    client,
    userdata,
    flags,
    reason_code,
    properties=None,
):
    logger.warning(
        "Disconnected from MQTT broker. Reason code: %s",
        reason_code,
    )


# =============================================================================
# MQTT MESSAGE RECEIVED
# =============================================================================

def on_message(client, userdata, msg):
    """
    Called whenever an MQTT message is received.
    """

    try:
        payload = json.loads(
            msg.payload.decode("utf-8")
        )

    except (json.JSONDecodeError, UnicodeDecodeError) as exc:

        logger.warning(
            "Invalid JSON received on topic %s: %s",
            msg.topic,
            exc,
        )

        return

    logger.info(
        "MQTT message received | topic=%s | payload=%s",
        msg.topic,
        payload,
    )

    # -------------------------------------------------------------------------
    # VIBRATION
    # -------------------------------------------------------------------------

    if msg.topic == settings.MQTT_TOPIC_VIBRATION:

        handle_vibration(payload)

        # Broadcast the updated sensor data if we already have
        # a classification result.
        asyncio.create_task(
            broadcast_live_reading()
        )

    # -------------------------------------------------------------------------
    # PRINTER
    # -------------------------------------------------------------------------

    elif msg.topic == settings.MQTT_TOPIC_TEMPERATURE:

        handle_printer(payload)

        # Broadcast the updated temperature if we already have
        # a classification result.
        asyncio.create_task(
            broadcast_live_reading()
        )

    # -------------------------------------------------------------------------
    # ML STATUS
    # -------------------------------------------------------------------------

    elif msg.topic == settings.MQTT_TOPIC_STATUS:

        asyncio.create_task(
            handle_status(payload)
        )

    # -------------------------------------------------------------------------
    # UNKNOWN TOPIC
    # -------------------------------------------------------------------------

    else:

        logger.warning(
            "Received message on unknown MQTT topic: %s",
            msg.topic,
        )


# =============================================================================
# VIBRATION HANDLER
# =============================================================================

def handle_vibration(payload: dict):
    """
    Handle:

        printpulse/live

    Current payload:

        {
            "vibe_x": -2.465,
            "vibe_y": -9.31,
            "vibe_z": -0.5,
            "vibe_mag": 9.644
        }
    """

    latest_vibration["vibe_x"] = payload.get("vibe_x")
    latest_vibration["vibe_y"] = payload.get("vibe_y")
    latest_vibration["vibe_z"] = payload.get("vibe_z")
    latest_vibration["vibe_mag"] = payload.get("vibe_mag")

    # If the publisher eventually provides accel_rms_z,
    # store it.
    if payload.get("accel_rms_z") is not None:

        latest_vibration["accel_rms_z"] = (
            payload.get("accel_rms_z")
        )

    logger.debug(
        "Updated vibration data: %s",
        latest_vibration,
    )


# =============================================================================
# PRINTER HANDLER
# =============================================================================

def handle_printer(payload: dict):
    """
    Handle:

        printpulse/printer

    ACTUAL payload received from your printer:

        {
            "timestamp": "2026-09-15 14:57:19",
            "nozzle_actual": 30.3,
            "nozzle_target": 0.0,
            "bed_actual": 30.5,
            "bed_target": 0.0
        }

    IMPORTANT:
    The publisher calls these fields nozzle_actual and bed_actual,
    so we map them to the names used by the backend.
    """

    latest_printer["nozzle_temp"] = payload.get(
        "nozzle_actual"
    )

    latest_printer["bed_temp"] = payload.get(
        "bed_actual"
    )

    logger.debug(
        "Updated printer data: %s",
        latest_printer,
    )


# =============================================================================
# STATUS / ML HANDLER
# =============================================================================

async def handle_status(payload: dict):
    """
    Handle:

        printpulse/status

    Expected payload:

        {
            "fault_class": "NORMAL",
            "confidence": 0.97
        }

    The status message triggers creation of a FaultEvent.
    """

    fault_class_value = payload.get(
        "fault_class"
    )

    confidence_value = payload.get(
        "confidence"
    )

    # -------------------------------------------------------------------------
    # Validate fault class
    # -------------------------------------------------------------------------

    if fault_class_value is None:

        logger.warning(
            "Status message missing 'fault_class': %s",
            payload,
        )

        return

    # -------------------------------------------------------------------------
    # Validate confidence
    # -------------------------------------------------------------------------

    if confidence_value is None:

        logger.warning(
            "Status message missing 'confidence': %s",
            payload,
        )

        return

    try:

        fault_class = FaultClass(
            fault_class_value
        )

    except ValueError:

        logger.warning(
            "Unknown fault class received: %s",
            fault_class_value,
        )

        return

    try:

        confidence = float(
            confidence_value
        )

    except (TypeError, ValueError):

        logger.warning(
            "Invalid confidence value received: %s",
            confidence_value,
        )

        return

    # -------------------------------------------------------------------------
    # Store latest ML result
    # -------------------------------------------------------------------------

    latest_status["fault_class"] = fault_class
    latest_status["confidence"] = confidence

    logger.info(
        "ML RESULT | class=%s | confidence=%.3f",
        fault_class.value,
        confidence,
    )

    # -------------------------------------------------------------------------
    # Save to PostgreSQL
    # -------------------------------------------------------------------------

    event = await save_fault_event(
        fault_class=fault_class,
        confidence=confidence,
        status_payload=payload,
    )

    # -------------------------------------------------------------------------
    # Broadcast to React dashboard
    # -------------------------------------------------------------------------

    if event is not None:

        await broadcast_live_reading(
            event_id=event.id,
            received_at=event.received_at.isoformat(),
        )


# =============================================================================
# SAVE FAULT EVENT
# =============================================================================

async def save_fault_event(
    fault_class: FaultClass,
    confidence: float,
    status_payload: dict,
):
    """
    Save the classification result + latest sensor readings
    into PostgreSQL.
    """

    try:

        async with AsyncSessionLocal() as db:

            # -----------------------------------------------------------------
            # ACCELERATION
            # -----------------------------------------------------------------

            accel_rms_z = status_payload.get(
                "accel_rms_z"
            )

            if accel_rms_z is None:

                accel_rms_z = latest_vibration.get(
                    "accel_rms_z"
                )

            # Your current live payload doesn't provide accel_rms_z.
            #
            # FaultEvent currently requires a non-null value, so this
            # remains a temporary fallback until the ML pipeline provides
            # the actual RMS value.
            if accel_rms_z is None:

                accel_rms_z = 0.0

            # -----------------------------------------------------------------
            # TEMPERATURE
            # -----------------------------------------------------------------

            nozzle_temp = status_payload.get(
                "nozzle_temp"
            )

            if nozzle_temp is None:

                nozzle_temp = latest_printer.get(
                    "nozzle_temp"
                )

            if nozzle_temp is None:

                nozzle_temp = 0.0

            bed_temp = status_payload.get(
                "bed_temp"
            )

            if bed_temp is None:

                bed_temp = latest_printer.get(
                    "bed_temp"
                )

            if bed_temp is None:

                bed_temp = 0.0

            # -----------------------------------------------------------------
            # TIMESTAMP
            # -----------------------------------------------------------------

            esp32_timestamp = status_payload.get(
                "timestamp"
            )

            if esp32_timestamp is None:

                esp32_timestamp = status_payload.get(
                    "esp32_timestamp"
                )

            # -----------------------------------------------------------------
            # CREATE EVENT
            # -----------------------------------------------------------------

            event = FaultEvent(

                fault_class=fault_class,

                confidence=confidence,

                accel_rms_z=float(
                    accel_rms_z
                ),

                nozzle_temp=float(
                    nozzle_temp
                ),

                bed_temp=float(
                    bed_temp
                ),

                esp32_timestamp=(
                    esp32_timestamp
                ),

                received_at=(
                    datetime.now(timezone.utc)
                ),

                alert_sent=False,

                acknowledged=False,
            )

            db.add(event)

            await db.commit()

            await db.refresh(event)

            logger.info(
                "Fault event saved | "
                "id=%s | class=%s | confidence=%.3f",
                event.id,
                event.fault_class.value,
                event.confidence,
            )

            return event

    except Exception:

        logger.exception(
            "Failed to save MQTT fault event to PostgreSQL."
        )

        return None


# =============================================================================
# MQTT LISTENER
# =============================================================================

async def mqtt_listener():
    """
    Run the MQTT listener alongside FastAPI.

    We intentionally do NOT use loop_forever(), because that would
    block FastAPI.

    Instead, Paho's loop() is called periodically.
    """

    client = mqtt.Client(
        callback_api_version=(
            mqtt.CallbackAPIVersion.VERSION2
        )
    )

    # -------------------------------------------------------------------------
    # MQTT AUTHENTICATION
    # -------------------------------------------------------------------------

    client.username_pw_set(
        settings.MQTT_USERNAME,
        settings.MQTT_PASSWORD,
    )

    # -------------------------------------------------------------------------
    # TLS
    # -------------------------------------------------------------------------

    client.tls_set(
        cert_reqs=ssl.CERT_REQUIRED,
        tls_version=ssl.PROTOCOL_TLS,
    )

    # -------------------------------------------------------------------------
    # CALLBACKS
    # -------------------------------------------------------------------------

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    logger.info(
        "Starting MQTT listener: %s:%s",
        settings.MQTT_BROKER,
        settings.MQTT_PORT,
    )

    # -------------------------------------------------------------------------
    # CONNECTION LOOP
    # -------------------------------------------------------------------------

    while True:

        try:

            if not client.is_connected():

                logger.info(
                    "Connecting to MQTT broker..."
                )

                client.connect(
                    settings.MQTT_BROKER,
                    settings.MQTT_PORT,
                    keepalive=60,
                )

            # Process MQTT traffic.
            client.loop(timeout=1.0)

            # Give control back to FastAPI / asyncio.
            await asyncio.sleep(0.1)

        except asyncio.CancelledError:

            logger.info(
                "MQTT listener shutting down..."
            )

            try:
                client.disconnect()
            except Exception:
                pass

            raise

        except Exception:

            logger.exception(
                "MQTT error. Retrying in 5 seconds..."
            )

            try:
                client.disconnect()
            except Exception:
                pass

            await asyncio.sleep(5)
