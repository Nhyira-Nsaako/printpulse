import logging
from typing import Optional
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models import User, FaultEvent, FaultClass

logger = logging.getLogger(__name__)

# Severity labels used in alert messages
SEVERITY = {
    FaultClass.NOZZLE_CLOG: "Medium",
    FaultClass.MOTOR_FAULT: "High",
    FaultClass.THERMAL_RUNAWAY: "CRITICAL",
}


def _build_email_body(event: FaultEvent) -> str:
    severity = SEVERITY.get(event.fault_class, "Unknown")
    return f"""
PrintPulse Fault Alert
======================
Fault Class : {event.fault_class.value}
Severity    : {severity}
Confidence  : {event.confidence * 100:.1f}%
Detected At : {event.received_at.strftime('%Y-%m-%d %H:%M:%S UTC')}

Sensor Readings
---------------
Vibration RMS (Z) : {event.accel_rms_z:.4f} g  (if available)
Current RMS       : {event.current_rms:.3f} A   (if available)
Temperature       : {event.temperature:.1f} °C  (if available)

Please inspect your printer immediately.

— PrintPulse Monitoring System
"""


async def send_email_alert(to_email: str, event: FaultEvent) -> bool:
    """Send a fault alert email via SMTP."""
    if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured — skipping email alert.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[PrintPulse] {event.fault_class.value} Detected ({event.confidence*100:.0f}% confidence)"
    msg["From"] = settings.ALERT_FROM_EMAIL
    msg["To"] = to_email
    msg.attach(MIMEText(_build_email_body(event), "plain"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        logger.info(f"Email alert sent to {to_email} for {event.fault_class.value}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email alert: {e}")
        return False


async def send_sms_alert(to_phone: str, event: FaultEvent) -> bool:
    """Send a fault alert SMS via Twilio REST API."""
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        logger.warning("Twilio credentials not configured — skipping SMS alert.")
        return False

    import httpx
    severity = SEVERITY.get(event.fault_class, "")
    body = (
        f"[PrintPulse] {severity} ALERT: {event.fault_class.value} "
        f"({event.confidence*100:.0f}% conf) at "
        f"{event.received_at.strftime('%H:%M UTC')}. "
        f"Inspect your printer immediately."
    )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json",
                data={"From": settings.TWILIO_FROM_NUMBER, "To": to_phone, "Body": body},
                auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
            )
            response.raise_for_status()
        logger.info(f"SMS alert sent to {to_phone} for {event.fault_class.value}")
        return True
    except Exception as e:
        logger.error(f"Failed to send SMS alert: {e}")
        return False


async def dispatch_alerts(event: FaultEvent, db: AsyncSession) -> None:
    """
    Check whether this event should trigger alerts, then send to all
    users who have alerts enabled.
    """
    # Only alert on configured fault classes above the confidence threshold
    if event.fault_class.value not in settings.alert_fault_classes_list:
        return
    if event.confidence < settings.ALERT_CONFIDENCE_THRESHOLD:
        return

    result = await db.execute(
        select(User).where(User.is_active == True, User.alerts_enabled == True)
    )
    users = result.scalars().all()

    for user in users:
        if user.alert_email:
            await send_email_alert(user.alert_email, event)
        if user.alert_phone:
            await send_sms_alert(user.alert_phone, event)
