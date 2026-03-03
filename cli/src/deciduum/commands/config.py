"""Configuration management commands."""

import typer
from typing import Optional

from deciduum.config import (
    load_config,
    set_config_value,
    unset_config_value,
    get_config_value,
    CONFIG_FILE,
)

config_app = typer.Typer(help="Manage Deciduum configuration.")


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Config key (server_url, api_key)"),
    value: str = typer.Argument(..., help="Config value"),
):
    """Set a configuration value."""
    valid_keys = ["server_url", "api_key"]

    if key not in valid_keys:
        typer.echo(
            f"Invalid key '{key}'. Valid keys: {', '.join(valid_keys)}", err=True
        )
        raise typer.Exit(1)

    set_config_value(key, value)
    typer.echo(f"Set {key} = {value}")


@config_app.command("unset")
def config_unset(
    key: str = typer.Argument(..., help="Config key to remove (server_url, api_key)"),
):
    """Remove a configuration value."""
    valid_keys = ["server_url", "api_key"]

    if key not in valid_keys:
        typer.echo(
            f"Invalid key '{key}'. Valid keys: {', '.join(valid_keys)}", err=True
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
    config = load_config()

    if not config:
        typer.echo("No configuration found.")
        typer.echo(f"Config file: {CONFIG_FILE}")
        typer.echo("\nTo configure server mode:")
        typer.echo("  deciduum config set server_url <url>")
        typer.echo("  deciduum config set api_key <key>")
        return

    typer.echo(f"Configuration file: {CONFIG_FILE}\n")

    for key, value in config.items():
        if key == "api_key" and value:
            # Mask API key for security
            masked = value[:4] + "*" * (len(value) - 4) if len(value) > 4 else "****"
            typer.echo(f"{key}: {masked}")
        else:
            typer.echo(f"{key}: {value}")

    # Show effective mode
    if config.get("server_url"):
        typer.echo(f"\nMode: SERVER (using {config['server_url']})")
    else:
        typer.echo("\nMode: LOCAL (using SQLite)")


@config_app.command("get")
def config_get(
    key: str = typer.Argument(..., help="Config key to retrieve"),
):
    """Get a specific configuration value."""
    valid_keys = ["server_url", "api_key"]

    if key not in valid_keys:
        typer.echo(
            f"Invalid key '{key}'. Valid keys: {', '.join(valid_keys)}", err=True
        )
        raise typer.Exit(1)

    value = get_config_value(key)
    if value is None:
        typer.echo(f"Key '{key}' is not set.")
    elif key == "api_key" and value:
        # Mask API key for security
        masked = value[:4] + "*" * (len(value) - 4) if len(value) > 4 else "****"
        typer.echo(masked)
    else:
        typer.echo(value)
