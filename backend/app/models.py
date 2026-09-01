from datetime import datetime, timezone
from sqlalchemy import (
    String, Float, DateTime, Boolean, Integer,
    ForeignKey, Enum as SAEnum, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.database import Base


class FaultClass(str, enum.Enum):
    NORMAL = "NORMAL"
    NOZZLE_CLOG = "NOZZLE_CLOG"
    MOTOR_FAULT = "MOTOR_FAULT"
    THERMAL_RUNAWAY = "THERMAL_RUNAWAY"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Alert preferences
    alert_email: Mapped[str] = mapped_column(String(255), nullable=True)
    alert_phone: Mapped[str] = mapped_column(String(30), nullable=True)
    alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    fault_events = relationship("FaultEvent", back_populates="acknowledged_by_user")


class FaultEvent(Base):
    """
    One row per classification cycle received from the ESP32 via MQTT.
    Non-NORMAL events are also stored; NORMAL readings are stored too
    for trend charting but can be filtered in queries.
    """
    __tablename__ = "fault_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Classification result
    fault_class: Mapped[FaultClass] = mapped_column(
        SAEnum(FaultClass, name="fault_class_enum"), nullable=False, index=True
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # Raw sensor readings at time of classification
    accel_rms_z: Mapped[float] = mapped_column(Float, nullable=True)
    current_rms: Mapped[float] = mapped_column(Float, nullable=True)
    temperature: Mapped[float] = mapped_column(Float, nullable=True)

    # Timestamps
   esp32_timestamp: Mapped[int] = mapped_column(BigInteger, nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    # Alert tracking
    alert_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    acknowledged_by_user = relationship("User", back_populates="fault_events")
