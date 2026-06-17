import os

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.models.enums import OrderFailureStep

MODE = os.getenv("MODE", "example")

ENV_FILES = {
    "example": ".env.example",
    "local": ".env.local",
    "dev": ".env.dev",
    "prod": ".env.prod",
}

ENV_FILE = ENV_FILES.get(MODE, ".env.example")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8")

    environment: str = "local"
    log_level: str = "INFO"
    queue_interval: int = 1

    max_processing_attempts: int = 3
    retry_base_delay_seconds: int = 1
    retry_backoff_multiplier: int = 2
    retryable_failure_steps: set[OrderFailureStep] = {
        OrderFailureStep.CAPTURE_PAYMENT,
        OrderFailureStep.SEND_NOTIFICATION,
    }


settings = Settings()
