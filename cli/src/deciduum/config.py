"""Deciduum CLI configuration module."""

import json
import os
import platform
import shutil
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


# Legacy config paths for migration
LEGACY_CONFIG = Path.home() / ".deciduum" / "config.json"
LEGACY_SESSIONS = Path.home() / ".deciduum" / "sessions"


def get_config_dir() -> Path:
    """Get config directory following XDG spec."""
    # Check for environment variable override first
    if os.environ.get("DECIDUUM_CONFIG_DIR"):
        return Path(os.environ["DECIDUUM_CONFIG_DIR"])

    system = platform.system()

    if system == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / "deciduum"
    elif system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "deciduum"
    else:  # Linux/Unix
        xdg_config = os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
        return Path(xdg_config) / "deciduum"


def get_data_dir() -> Path:
    """Get data directory for sessions."""
    # Check for environment variable override first
    if os.environ.get("DECIDUUM_SESSIONS_DIR"):
        return Path(os.environ["DECIDUUM_SESSIONS_DIR"])

    system = platform.system()

    if system == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / "deciduum" / "sessions"
    elif system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "deciduum" / "sessions"
    else:
        xdg_data = os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")
        return Path(xdg_data) / "deciduum" / "sessions"


def get_registry_data_dir() -> Path:
    """Get registry data directory (parent of sessions directory)."""
    # Check for environment variable override first
    if os.environ.get("DECIDUUM_DATA_DIR"):
        return Path(os.environ["DECIDUUM_DATA_DIR"])

    system = platform.system()

    if system == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / "deciduum"
    elif system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "deciduum"
    else:
        xdg_data = os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")
        return Path(xdg_data) / "deciduum"


def get_registry_db_path() -> Path:
    """Get the registry database path."""
    registry_dir = get_registry_data_dir()
    return registry_dir / "sessions.db"


def get_config_file() -> Path:
    """Get the config file path."""
    return get_config_dir() / "config.json"


# Config file path - uses new location by default
CONFIG_FILE = get_config_file()


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

    config_dir: Optional[Path] = Field(
        default=None,
        description="Config directory (None means auto-detect)",
    )
    sessions_dir: Optional[Path] = Field(
        default=None,
        description="Sessions directory (None means auto-detect)",
    )
    server_url: Optional[str] = Field(
        default=None,
        description="URL of the FastAPI server",
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authentication",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )
    editor: Optional[str] = Field(
        default=None,
        description="Editor to use for editing",
    )

    class Config:
        env_prefix = "DECIDUUM_"
        env_file = ".env"
        extra = "ignore"


def migrate_if_needed() -> bool:
    """Migrate from legacy location if needed. Returns True if migration happened."""
    new_config = get_config_file()

    # Already migrated
    if new_config.exists():
        return False

    # Check for legacy config
    if not LEGACY_CONFIG.exists():
        return False

    # Migrate config
    new_config.parent.mkdir(parents=True, exist_ok=True)
    LEGACY_CONFIG.rename(new_config)

    # Migrate sessions if they exist
    if LEGACY_SESSIONS.exists():
        new_sessions = get_data_dir()
        new_sessions.parent.mkdir(parents=True, exist_ok=True)
        # Move each session file
        for db_file in LEGACY_SESSIONS.glob("*.db"):
            shutil.move(str(db_file), str(new_sessions / db_file.name))

    return True


def load_config() -> dict:
    """Load configuration from config file."""
    config_file = get_config_file()
    if config_file.exists():
        try:
            with open(config_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_config(config: dict) -> None:
    """Save configuration to config file."""
    config_file = get_config_file()
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, "w") as f:
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
    # Check settings first for override
    if settings.sessions_dir:
        sessions_dir = settings.sessions_dir
    else:
        sessions_dir = get_data_dir()

    sessions_dir.mkdir(parents=True, exist_ok=True)
    return sessions_dir


def get_session_db_path(session_id: str) -> Path:
    """Get the database path for a specific session."""
    sessions_dir = get_sessions_dir()
    return sessions_dir / f"{session_id}.db"


# Global settings instance
settings = Settings(
    config_dir=get_config_dir(),
    sessions_dir=get_data_dir(),
)
