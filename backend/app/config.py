from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "GanttMind API"
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://gantt_mind:gantt_mind@localhost:5432/gantt_mind"
    max_excel_upload_bytes: int = 5 * 1024 * 1024

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
