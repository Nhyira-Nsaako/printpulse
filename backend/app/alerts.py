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
    FaultClass.NORMAL: "Info",
    FaultClass.MECHANICAL_FAULT: "High",
    FaultClass.THERMAL_ANOMALY: "CRITICAL",
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
