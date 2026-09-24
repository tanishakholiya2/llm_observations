from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://observability:observability@localhost:5432/llm_observatory"
    llm_api_url: str | None = None
    llm_api_key: str | None = None
    llm_default_model: str = "local-observer"
    frontend_origin: str = "http://localhost:5173"
    app_env: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
