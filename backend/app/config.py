from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    DATABASE_URL: str = (
        "postgresql+asyncpg://printpulse:password@localhost:5432/printpulse_db"
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def _use_asyncpg_driver(cls, v: str) -> str:
        """
        Managed Postgres providers such as Render may provide DATABASE_URL
        using postgres:// or postgresql://.

        SQLAlchemy's async engine requires the asyncpg driver, so convert
        those URLs automatically.
        """
        if v.startswith("postgres://"):
            return v.replace(
                "postgres://",
                "postgresql+asyncpg://",
                1,
            )

        if v.startswith("postgresql://"):
            return v.replace(
                "postgresql://",
                "postgresql+asyncpg://",
                1,
            )

        return v

    # -------------------------------------------------------------------------
    # CORS
    # -------------------------------------------------------------------------
    # In Render, set this to your deployed frontend URL, for example:
    # https://printpulse-frontend.vercel.app
    CORS_ORIGINS: str = (
        "http://localhost:5173,http://localhost:3000"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]

    # -------------------------------------------------------------------------
    # JWT
    # -------------------------------------------------------------------------
    SECRET_KEY: str = "change-this-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # -------------------------------------------------------------------------
    # MQTT
    # -------------------------------------------------------------------------
    MQTT_BROKER: str = "localhost"
    MQTT_PORT: int = 1883
    MQTT_TOPIC_VIBRATION: str = "printpulse/live"
    MQTT_TOPIC_TEMPERATURE: str = "printpulse/printer"
    MQTT_TOPIC_STATUS: str = "printpulse/status"
    MQTT_USERNAME: str = "PrintPulse"
    MQTT_PASSWORD: str = "FinalYearProject@2026"

    # -------------------------------------------------------------------------
    # Email (SMTP)
    # -------------------------------------------------------------------------
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    ALERT_FROM_EMAIL: str = ""

    # -------------------------------------------------------------------------
    # SMS (Arkesel)
    # -------------------------------------------------------------------------
    # The actual API key should be stored in Render's Environment Variables.
    ARKESEL_API_KEY: str = ""

    # -------------------------------------------------------------------------
    # Alert configuration
    # -------------------------------------------------------------------------
    ALERT_CONFIDENCE_THRESHOLD: float = 0.85

    ALERT_FAULT_CLASSES: str = (
        "MECHANICAL_FAULT,THERMAL_ANOMALY"
    )

    @property
    def alert_fault_classes_list(self) -> List[str]:
        return [
            fault_class.strip()
            for fault_class in self.ALERT_FAULT_CLASSES.split(",")
            if fault_class.strip()
        ]


# -----------------------------------------------------------------------------
# Create the settings object.
# Other files import this as:
#
# from app.config import settings
# -----------------------------------------------------------------------------
settings = Settings()
