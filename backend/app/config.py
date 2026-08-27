from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://printpulse:password@localhost:5432/printpulse_db"

    @field_validator("DATABASE_URL")
    @classmethod
    def _use_asyncpg_driver(cls, v: str) -> str:
        # Managed Postgres providers (Railway, Render, Heroku, etc.) inject
        # DATABASE_URL as postgres:// or postgresql://, which is the psycopg2
        # scheme. SQLAlchemy's async engine needs the asyncpg driver spelled
        # out explicitly, so rewrite it rather than requiring a manually
        # edited env var on every deploy.
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # CORS — comma-separated list of allowed frontend origins. Defaults cover
    # local dev only; set this in production to your deployed frontend URL
    # (e.g. https://printpulse.vercel.app).
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # JWT
    SECRET_KEY: str = "change-this-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # MQTT
    MQTT_BROKER: str = "localhost"
    MQTT_PORT: int = 1883
    MQTT_TOPIC: str = "printpulse/status"
    MQTT_USERNAME: str = ""
    MQTT_PASSWORD: str = ""

    # Email (SMTP)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    ALERT_FROM_EMAIL: str = ""

    # SMS (Twilio)
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""

    # Alert config
    ALERT_CONFIDENCE_THRESHOLD: float = 0.85
    ALERT_FAULT_CLASSES: str = "NOZZLE_CLOG,MOTOR_FAULT,THERMAL_RUNAWAY"

    @property
    def alert_fault_classes_list(self) -> List[str]:
        return [c.strip() for c in self.ALERT_FAULT_CLASSES.split(",")]


settings = Settings()
