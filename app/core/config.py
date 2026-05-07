import os

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = os.getenv("ENV_FILE", ".env.example")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8")

    environment: str = "local"
    log_level: str = "INFO"
    queue_interval: int = 1


settings = Settings()
