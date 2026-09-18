import logging

import aiosmtplib
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models import User, FaultEvent, FaultClass


logger = logging.getLogger(__name__)


SEVERITY = {
    FaultClass.NORMAL: "Info",
    FaultClass.MECHANICAL_FAULT: "High",
    FaultClass.THERMAL_ANOMALY: "CRITICAL",
}


def _build_email_body(event: FaultEvent) -> str:
    severity = SEVERITY.get(event.fault_class, "Unknown")

    return (
        "PrintPulse Fault Alert\n"
        "======================\n"
        f"Fault Class : {event.fault_class.value}\n"
        f"Severity    : {severity}\n"
        f"Confidence  : {event.confidence * 100:.1f}%\n"
        f"Detected At : {event.received_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        "Sensor Readings\n"
        "---------------\n"
        f"Vibration RMS (Z) : "
        f"{getattr(event, 'accel_rms_z', 0.0):.4f} g\n"
        f"Nozzle Temp       : "
        f"{getattr(event, 'nozzle_temp', 0.0):.1f} °C\n"
        f"Bed Temp          : "
        f"{getattr(event, 'bed_temp', 0.0):.1f} °C\n\n"
        "Please inspect your printer immediately.\n\n"
        "— PrintPulse Monitoring System"
    )


async def send_email_alert(to_email: str, event: FaultEvent) -> bool:
    """Send a fault alert email via SMTP."""

    if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        logger.warning(
            "SMTP credentials not configured — skipping email alert."
        )
        return False

    msg = MIMEMultipart("alternative")

    msg["Subject"] = (
        f"[PrintPulse] {event.fault_class.value} Detected "
        f"({event.confidence * 100:.0f}% confidence)"
    )

    msg["From"] = settings.ALERT_FROM_EMAIL
    msg["To"] = to_email

    msg.attach(
        MIMEText(
            _build_email_body(event),
            "plain",
        )
    )

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )

        logger.info(
            f"Email alert sent to {to_email} "
            f"for {event.fault_class.value}"
        )

        return True

    except Exception as e:
        logger.error(f"Failed to send email alert: {e}")
        return False


async def send_sms_alert(to_phone: str, event: FaultEvent) -> bool:
    """Send a fault alert SMS via the Arkesel REST API."""

    if not settings.ARKESEL_API_KEY:
        logger.warning(
            "Arkesel API key not configured — skipping SMS alert."
        )
        return False

    severity = SEVERITY.get(event.fault_class, "")

    body = (
        f"[PrintPulse] {severity} ALERT: "
        f"{event.fault_class.value} "
        f"({event.confidence * 100:.0f}% conf) at "
        f"{event.received_at.strftime('%H:%M UTC')}. "
        f"Inspect your printer immediately."
    )

    try:
        async with httpx.AsyncClient() as client:

            response = await client.post(
                "https://sms.arkesel.com/api/v2/sms/send",
                headers={
                    "api-key": settings.ARKESEL_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "sender": "PrintPulse",
                    "message": body,
                    "recipients": [to_phone],
                },
                timeout=30,
            )

        response.raise_for_status()

        data = response.json()

        if data.get("status") == "success":
            logger.info(
                f"SMS alert sent to {to_phone} "
                f"for {event.fault_class.value}"
            )
            return True

        logger.error(
            f"Arkesel SMS failed: {data}"
        )
        return False

    except Exception as e:
        logger.error(
            f"Failed to send Arkesel SMS: {e}"
        )
        return False


async def dispatch_alerts(
    event: FaultEvent,
    db: AsyncSession,
) -> bool:
    """
    Check whether this event should trigger alerts.

    Alerts are sent only when:
    - The fault class is included in ALERT_FAULT_CLASSES.
    - The confidence is at or above ALERT_CONFIDENCE_THRESHOLD.

    Each active user's email and SMS preferences are respected.

    Returns True if the event passes the alert gate and
    notification attempts are made.
    """

    # Check fault class
    if event.fault_class.value not in settings.alert_fault_classes_list:
        logger.info(
            f"Alert skipped: {event.fault_class.value} "
            f"not in ALERT_FAULT_CLASSES"
        )
        return False

    # Check confidence
    if event.confidence < settings.ALERT_CONFIDENCE_THRESHOLD:
        logger.info(
            f"Alert skipped: confidence "
            f"{event.confidence} below threshold "
            f"{settings.ALERT_CONFIDENCE_THRESHOLD}"
        )
        return False

    # Get all active users
    result = await db.execute(
        select(User).where(User.is_active == True)
    )

    users = result.scalars().all()

    # Send alerts according to each user's preferences
    for user in users:

        if user.email_alerts_enabled and user.alert_email:
            await send_email_alert(
                user.alert_email,
                event,
            )

        if user.sms_alerts_enabled and user.alert_phone:
            await send_sms_alert(
                user.alert_phone,
                event,
            )

    return True


