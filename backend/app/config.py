from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://printpulse:password@localhost:5432/printpulse_db"

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
