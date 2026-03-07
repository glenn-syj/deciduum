"""Configuration management commands."""

import os
import platform

import typer
from typing import Optional

from deciduum.config import (
    load_config,
    set_config_value,
    unset_config_value,
    get_config_value,
    get_config_file,
    get_config_dir,
    get_data_dir,
    LEGACY_CONFIG,
    migrate_if_needed,
)

config_app = typer.Typer(help="Manage Deciduum configuration.")

# Valid configuration keys
VALID_KEYS = ["server_url", "api_key", "sessions_dir", "log_level", "editor"]

# Valid log levels
VALID_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR"]


def _get_effective_config() -> dict:
    """Get effective configuration including environment variable overrides."""
    config = load_config()

    # Apply environment variable overrides
    if os.environ.get("DECIDUUM_SERVER_URL"):
        config["server_url"] = os.environ.get("DECIDUUM_SERVER_URL")
    if os.environ.get("DECIDUUM_API_KEY"):
        config["api_key"] = os.environ.get("DECIDUUM_API_KEY")
    if os.environ.get("DECIDUUM_SESSIONS_DIR"):
        config["sessions_dir"] = os.environ.get("DECIDUUM_SESSIONS_DIR")
    if os.environ.get("DECIDUUM_LOG_LEVEL"):
        config["log_level"] = os.environ.get("DECIDUUM_LOG_LEVEL")
    if os.environ.get("DECIDUUM_EDITOR"):
        config["editor"] = os.environ.get("DECIDUUM_EDITOR")

    return config


def _mask_value(key: str, value: str) -> str:
    """Mask sensitive values for display."""
    if key == "api_key" and value:
        return value[:4] + "*" * (len(value) - 4) if len(value) > 4 else "****"
    return value


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Config key"),
    value: str = typer.Argument(..., help="Config value"),
):
    """Set a configuration value."""
    if key not in VALID_KEYS:
        typer.echo(
            f"Invalid key '{key}'. Valid keys: {', '.join(VALID_KEYS)}", err=True
        )
        raise typer.Exit(1)

    # Validate log_level
    if key == "log_level" and value not in VALID_LOG_LEVELS:
        typer.echo(
            f"Invalid log level '{value}'. Valid levels: {', '.join(VALID_LOG_LEVELS)}",
            err=True,
        )
        raise typer.Exit(1)

    # Validate sessions_dir is a valid path
    if key == "sessions_dir":
        path = Path(value)
        if not path.is_absolute() and not path.expanduser().is_absolute():
            typer.echo(
                f"Invalid path '{value}'. Please provide an absolute path.",
                err=True,
            )
            raise typer.Exit(1)

    set_config_value(key, value)
    typer.echo(f"Set {key} = {value}")


@config_app.command("unset")
def config_unset(
    key: str = typer.Argument(..., help="Config key to remove"),
):
    """Remove a configuration value."""
    if key not in VALID_KEYS:
        typer.echo(
            f"Invalid key '{key}'. Valid keys: {', '.join(VALID_KEYS)}", err=True
        )
        raise typer.Exit(1)

    current = get_config_value(key)
    if current is None:
        typer.echo(f"Key '{key}' is not set.")
    else:
        unset_config_value(key)
        typer.echo(f"Unset {key} (was: {current})")


@config_app.command("show")
def config_show():
    """Show all configuration values."""
    # Check for migration
    migrated = migrate_if_needed()

    config_file = get_config_file()
    config = load_config()

    # Check for environment variable overrides
    env_overrides = {}
    if os.environ.get("DECIDUUM_SERVER_URL"):
        env_overrides["server_url"] = os.environ.get("DECIDUUM_SERVER_URL")
    if os.environ.get("DECIDUUM_API_KEY"):
        env_overrides["api_key"] = os.environ.get("DECIDUUM_API_KEY")
    if os.environ.get("DECIDUUM_SESSIONS_DIR"):
        env_overrides["sessions_dir"] = os.environ.get("DECIDUUM_SESSIONS_DIR")
    if os.environ.get("DECIDUUM_LOG_LEVEL"):
        env_overrides["log_level"] = os.environ.get("DECIDUUM_LOG_LEVEL")
    if os.environ.get("DECIDUUM_EDITOR"):
        env_overrides["editor"] = os.environ.get("DECIDUUM_EDITOR")

    # Show migration message if applicable
    if migrated:
        typer.echo("Migrated configuration from legacy location.")
        typer.echo()

    # Show config locations
    system = platform.system()
    typer.echo(f"Platform: {system}")
    typer.echo(f"Config directory: {get_config_dir()}")
    typer.echo(f"Data directory: {get_data_dir()}")
    typer.echo(f"Config file: {config_file}")
    typer.echo()

    if not config and not env_overrides:
        typer.echo("No configuration found.")
        typer.echo("\nTo configure:")
        typer.echo("  deciduum config set server_url <url>")
        typer.echo("  deciduum config set api_key <key>")
        typer.echo("  deciduum config set log_level <level>")
        typer.echo("  deciduum config set editor <editor>")
        return

    # Show file-based config
    typer.echo("Configuration from file:")
    if config:
        for key, value in config.items():
            masked = _mask_value(key, value)
            typer.echo(f"  {key}: {masked}")
    else:
        typer.echo("  (none)")

    # Show environment variable overrides
    if env_overrides:
        typer.echo("\nEnvironment variable overrides:")
        for key, value in env_overrides.items():
            masked = _mask_value(key, value)
            typer.echo(f"  {key}: {masked} (from DECIDUUM_{key.upper()})")

    # Show effective mode
    effective_server = env_overrides.get("server_url") or config.get("server_url")
    if effective_server:
        typer.echo(f"\nMode: SERVER (using {effective_server})")
    else:
        typer.echo("\nMode: LOCAL (using SQLite)")


@config_app.command("get")
def config_get(
    key: str = typer.Argument(..., help="Config key to retrieve"),
):
    """Get a specific configuration value."""
    if key not in VALID_KEYS:
        typer.echo(
            f"Invalid key '{key}'. Valid keys: {', '.join(VALID_KEYS)}", err=True
        )
        raise typer.Exit(1)

    # Check environment variable first
    env_key = f"DECIDUUM_{key.upper()}"
    if os.environ.get(env_key):
        value = os.environ.get(env_key)
        masked = _mask_value(key, value)
        typer.echo(f"{masked} (from environment)")
        return

    value = get_config_value(key)
    if value is None:
        typer.echo(f"Key '{key}' is not set.")
    else:
        masked = _mask_value(key, value)
        typer.echo(masked)


from pathlib import Path
