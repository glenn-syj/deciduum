"""Deciduum CLI configuration module."""

import json
import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


# Config file path
CONFIG_FILE = Path.home() / ".deciduum" / "config.json"


class ServerConfig(BaseSettings):
    """Server configuration for remote API access."""

    server_url: Optional[str] = Field(
        default=None,
        description="URL of the FastAPI server",
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authentication",
    )

    class Config:
        env_prefix = "DECIDUUM_"
        extra = "ignore"


class Settings(BaseSettings):
    """Application settings for the Deciduum CLI."""

    session_id: str = Field(
        default="default",
        description="Session ID for multi-database support",
    )

    sessions_dir: Path = Field(
        default=Path.home() / ".deciduum" / "sessions",
        description="Directory to store session databases",
    )

    class Config:
        env_prefix = "DECIDUUM_"
        env_file = ".env"
        extra = "ignore"


def load_config() -> dict:
    """Load configuration from config file."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_config(config: dict) -> None:
    """Save configuration to config file."""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_server_config() -> ServerConfig:
    """Get server configuration from config file."""
    config = load_config()
    return ServerConfig(
        server_url=config.get("server_url"),
        api_key=config.get("api_key"),
    )


def get_config_value(key: str) -> Optional[str]:
    """Get a configuration value by key."""
    config = load_config()
    return config.get(key)


def set_config_value(key: str, value: str) -> None:
    """Set a configuration value."""
    config = load_config()
    config[key] = value
    save_config(config)


def unset_config_value(key: str) -> None:
    """Remove a configuration value."""
    config = load_config()
    if key in config:
        del config[key]
        save_config(config)


def get_session_id() -> str:
    """Get the session ID from environment variable or default."""
    return os.environ.get("DECIDUUM_SESSION", "default")


def get_sessions_dir() -> Path:
    """Get the sessions directory path, creating it if necessary."""
    sessions_dir = Path.home() / ".deciduum" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    return sessions_dir


def get_session_db_path(session_id: str) -> Path:
    """Get the database path for a specific session."""
    sessions_dir = get_sessions_dir()
    return sessions_dir / f"{session_id}.db"


# Global settings instance
settings = Settings(
    session_id=get_session_id(),
    sessions_dir=get_sessions_dir(),
)
