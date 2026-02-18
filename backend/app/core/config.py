from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "Deciduum"
    database_url: str = "sqlite+aiosqlite:///./deciduum.db"
    deciduum_api_key: Optional[str] = None

    class Config:
        env_file = ".env"
        extra = "ignore"  # Allow extra fields in .env


@lru_cache
def get_settings() -> Settings:
    return Settings()
