from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from app.models import FaultClass


# ── Auth ─────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime
    alert_email: Optional[str] = None
    alert_phone: Optional[str] = None
    alerts_enabled: bool

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    alert_email: Optional[EmailStr] = None
    alert_phone: Optional[str] = None
    alerts_enabled: Optional[bool] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


# ── MQTT payload (matches ESP32 JSON output) ──────────────────────────────────

class MQTTPayload(BaseModel):
    fault_class: FaultClass
    confidence: float = Field(ge=0.0, le=1.0)
    accel_rms_z: Optional[float] = None
    current_rms: Optional[float] = None
    temperature: Optional[float] = None
    timestamp: Optional[int] = None  # Unix ms from ESP32


# ── Fault Events ──────────────────────────────────────────────────────────────

class FaultEventOut(BaseModel):
    id: int
    fault_class: FaultClass
    confidence: float
    accel_rms_z: Optional[float]
    current_rms: Optional[float]
    temperature: Optional[float]
    esp32_timestamp: Optional[int]
    received_at: datetime
    alert_sent: bool
    acknowledged: bool
    acknowledged_at: Optional[datetime]
    notes: Optional[str]

    model_config = {"from_attributes": True}


class FaultEventAcknowledge(BaseModel):
    notes: Optional[str] = None


class FaultEventPage(BaseModel):
    items: List[FaultEventOut]
    total: int
    page: int
    page_size: int
    pages: int


# ── Dashboard / Stats ─────────────────────────────────────────────────────────

class LiveReading(BaseModel):
    """Latest single reading — sent over WebSocket and REST."""
    fault_class: FaultClass
    confidence: float
    accel_rms_z: Optional[float]
    current_rms: Optional[float]
    temperature: Optional[float]
    received_at: datetime


class FaultStats(BaseModel):
    """Aggregated counts for the dashboard stats panel."""
    total_events: int
    normal_count: int
    nozzle_clog_count: int
    motor_fault_count: int
    thermal_runaway_count: int
    unacknowledged_faults: int
    last_24h_faults: int


class TrendPoint(BaseModel):
    received_at: datetime
    fault_class: FaultClass
    confidence: float
    accel_rms_z: Optional[float]
    current_rms: Optional[float]
    temperature: Optional[float]


class TrendData(BaseModel):
    points: List[TrendPoint]
