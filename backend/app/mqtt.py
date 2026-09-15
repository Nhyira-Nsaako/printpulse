import asyncio
import json
import logging
import ssl
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from app.config import settings
from app.database import AsyncSessionLocal
from app.models import FaultEvent, FaultClass


logger = logging.getLogger(__name__)


# =============================================================================
# Latest MQTT readings
# =============================================================================
# These dictionaries hold the most recently received values from each topic.
#
# printpulse/live      -> vibration
# printpulse/printer   -> printer temperatures
# printpulse/status    -> ML classification result
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
# MQTT CONNECT
# =============================================================================

def on_connect(client, userdata, flags, reason_code, properties=None):
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
            logger.info("Subscribed to MQTT topic: %s", topic)
        else:
            logger.error(
                "Failed to subscribe to MQTT topic: %s (code=%s)",
                topic,
                result,
            )


# =============================================================================
# MQTT DISCONNECT
# =============================================================================

def on_disconnect(client, userdata, flags, reason_code, properties=None):
    """
    Called whenever the MQTT connection is lost.
    """

    logger.warning(
        "Disconnected from MQTT broker. Reason code: %s",
        reason_code,
    )


# =============================================================================
# MQTT MESSAGE RECEIVED
# =============================================================================

def on_message(client, userdata, msg):
    """
    Called whenever a message arrives on one of our subscribed topics.
    """

    try:
        payload = json.loads(msg.payload.decode("utf-8"))

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

    # -------------------------------------------------------------------------
    # PRINTER TEMPERATURE
    # -------------------------------------------------------------------------

    elif msg.topic == settings.MQTT_TOPIC_TEMPERATURE:
        handle_printer(payload)

    # -------------------------------------------------------------------------
    # ML STATUS / CLASSIFICATION
    # -------------------------------------------------------------------------

    elif msg.topic == settings.MQTT_TOPIC_STATUS:
        handle_status(payload)

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
    Handle messages from:

        printpulse/live

    Current ESP32 payload:

        {
            "vibe_x": ...,
            "vibe_y": ...,
            "vibe_z": ...,
            "vibe_mag": ...
        }
    """

    latest_vibration["vibe_x"] = payload.get("vibe_x")
    latest_vibration["vibe_y"] = payload.get("vibe_y")
    latest_vibration["vibe_z"] = payload.get("vibe_z")
    latest_vibration["vibe_mag"] = payload.get("vibe_mag")

    # If a future publisher provides accel_rms_z,
    # keep it available for FaultEvent creation.
    if payload.get("accel_rms_z") is not None:
        latest_vibration["accel_rms_z"] = payload.get("accel_rms_z")

    logger.debug(
        "Updated vibration data: %s",
        latest_vibration,
    )


# =============================================================================
# PRINTER HANDLER
# =============================================================================

def handle_printer(payload: dict):
    """
    Handle messages from:

        printpulse/printer

    Expected temperature information:

        {
            "nozzle_temp": ...,
            "bed_temp": ...
        }
    """

    if payload.get("nozzle_temp") is not None:
        latest_printer["nozzle_temp"] = payload.get("nozzle_temp")

    if payload.get("bed_temp") is not None:
        latest_printer["bed_temp"] = payload.get("bed_temp")

    logger.debug(
        "Updated printer data: %s",
        latest_printer,
    )


# =============================================================================
# STATUS / ML RESULT HANDLER
# =============================================================================

def handle_status(payload: dict):
    """
    Handle messages from:

        printpulse/status

    Expected ML result:

        {
            "fault_class": "NORMAL",
            "confidence": 0.97
        }

    The prediction is combined with the latest vibration and
    printer readings and stored as a FaultEvent.
    """

    fault_class_value = payload.get("fault_class")
    confidence_value = payload.get("confidence")

    if fault_class_value is None:
        logger.warning(
            "Status message missing 'fault_class': %s",
            payload,
        )
        return

    if confidence_value is None:
        logger.warning(
            "Status message missing 'confidence': %s",
            payload,
        )
        return

    # -------------------------------------------------------------------------
    # Convert fault class into the SQLAlchemy enum.
    # -------------------------------------------------------------------------

    try:
        fault_class = FaultClass(fault_class_value)

    except ValueError:
        logger.warning(
            "Unknown fault class received: %s",
            fault_class_value,
        )
        return

    # -------------------------------------------------------------------------
    # Convert confidence to float.
    # -------------------------------------------------------------------------

    try:
        confidence = float(confidence_value)

    except (TypeError, ValueError):
        logger.warning(
            "Invalid confidence value received: %s",
            confidence_value,
        )
        return

    latest_status["fault_class"] = fault_class
    latest_status["confidence"] = confidence

    logger.info(
        "ML RESULT | class=%s | confidence=%.3f",
        fault_class.value,
        confidence,
    )

    # Save the event asynchronously.
    asyncio.create_task(
        save_fault_event(
            fault_class=fault_class,
            confidence=confidence,
            status_payload=payload,
        )
    )


# =============================================================================
# DATABASE
# =============================================================================

async def save_fault_event(
    fault_class: FaultClass,
    confidence: float,
    status_payload: dict,
):
    """
    Create and save a FaultEvent using:

        - ML result from printpulse/status
        - latest vibration from printpulse/live
        - latest temperatures from printpulse/printer
    """

    try:
        async with AsyncSessionLocal() as db:

            # -------------------------------------------------------------
            # Vibration
            # -------------------------------------------------------------

            accel_rms_z = status_payload.get("accel_rms_z")

            if accel_rms_z is None:
                accel_rms_z = latest_vibration.get("accel_rms_z")

            # Your current ESP32 live payload does NOT send accel_rms_z.
            # FaultEvent requires this database field, so use 0.0 until
            # the actual value is provided by the status/model pipeline.
            if accel_rms_z is None:
                accel_rms_z = 0.0

            # -------------------------------------------------------------
            # Temperature
            # -------------------------------------------------------------

            nozzle_temp = status_payload.get("nozzle_temp")

            if nozzle_temp is None:
                nozzle_temp = latest_printer.get("nozzle_temp")

            if nozzle_temp is None:
                nozzle_temp = 0.0

            bed_temp = status_payload.get("bed_temp")

            if bed_temp is None:
                bed_temp = latest_printer.get("bed_temp")

            if bed_temp is None:
                bed_temp = 0.0

            # -------------------------------------------------------------
            # ESP32 timestamp
            # -------------------------------------------------------------

            esp32_timestamp = status_payload.get("timestamp")

            if esp32_timestamp is None:
                esp32_timestamp = status_payload.get("esp32_timestamp")

            # -------------------------------------------------------------
            # Create database event
            # -------------------------------------------------------------

            event = FaultEvent(
                fault_class=fault_class,
                confidence=confidence,

                accel_rms_z=float(accel_rms_z),

                nozzle_temp=float(nozzle_temp),
                bed_temp=float(bed_temp),

                esp32_timestamp=esp32_timestamp,

                received_at=datetime.now(timezone.utc),

                alert_sent=False,
                acknowledged=False,
            )

            db.add(event)

            await db.commit()
            await db.refresh(event)

            logger.info(
                "Fault event saved | id=%s | class=%s | confidence=%.3f",
                event.id,
                event.fault_class.value,
                event.confidence,
            )

    except Exception:
        logger.exception(
            "Failed to save MQTT fault event to PostgreSQL."
        )


# =============================================================================
# MQTT LISTENER
# =============================================================================

async def mqtt_listener():
    """
    Start the MQTT listener as a FastAPI background task.

    This function intentionally does NOT use loop_forever(), because
    loop_forever() would block the FastAPI application.

    Instead, Paho's loop() is called periodically while the asyncio
    event loop remains available to FastAPI.
    """

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2
    )

    # -------------------------------------------------------------------------
    # Authentication
    # -------------------------------------------------------------------------

    client.username_pw_set(
        settings.MQTT_USERNAME,
        settings.MQTT_PASSWORD,
    )

    # -------------------------------------------------------------------------
    # TLS for HiveMQ Cloud
    # -------------------------------------------------------------------------

    client.tls_set(
        cert_reqs=ssl.CERT_REQUIRED,
        tls_version=ssl.PROTOCOL_TLS,
    )

    # -------------------------------------------------------------------------
    # Callbacks
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
    # Connection / reconnect loop
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

            # Process MQTT network traffic.
            #
            # IMPORTANT:
            # Do NOT use client.loop_forever() here because it would
            # prevent FastAPI from continuing normally.
            client.loop(timeout=1.0)

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
