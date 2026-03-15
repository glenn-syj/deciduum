"""Input validation utilities."""

from typing import Any

import typer


# ============================================================================
# Input Validation
# ============================================================================


def validate_safe_input(value: str, field_name: str = "input") -> None:
    """Validate input string for safety.

    Checks for:
    - Path traversal sequences (../)
    - Control characters (below ASCII 0x20)
    - URL-encoded path traversal (%2e%2e, etc.)

    Raises typer.Exit on failure.
    """
    if not value:
        return

    # Check for path traversal
    if "../" in value or "..\\" in value:
        typer.echo(
            f"Invalid {field_name}: path traversal not allowed ('..').",
            err=True,
        )
        raise typer.Exit(1)

    # Check for control characters (below ASCII 0x20, except tab, newline, carriage return)
    # Allow: tab (0x09), newline (0x0a), carriage return (0x0d)
    for char in value:
        if ord(char) < 0x09 or (0x0B <= ord(char) < 0x20):
            typer.echo(
                f"Invalid {field_name}: control characters not allowed.",
                err=True,
            )
            raise typer.Exit(1)

    # Check for URL-encoded path traversal
    # Common encodings: %2e%2e (../), %2e%2e%2f (../), %252e%252e (double-encoded)
    lower_value = value.lower()

    # Single-encoded: %2e%2e or %2e%2f
    if "%2e%2e" in lower_value or "%2e%2f" in lower_value or "%2e%5c" in lower_value:
        typer.echo(
            f"Invalid {field_name}: URL-encoded path traversal not allowed.",
            err=True,
        )
        raise typer.Exit(1)

    # Double-encoded: %252e%252e
    if "%252e%252e" in lower_value or "%252e%252f" in lower_value:
        typer.echo(
            f"Invalid {field_name}: double-encoded path traversal not allowed.",
            err=True,
        )
        raise typer.Exit(1)


def validate_resource_id(resource_id: str) -> None:
    """Validate resource ID doesn't contain query params or fragments.

    Checks for:
    - Query string separator (?)
    - Fragment separator (#)

    These could indicate an attempt to embed additional resource references.

    Raises typer.Exit on failure.
    """
    if not resource_id:
        return

    if "?" in resource_id:
        typer.echo(
            "Invalid resource ID: query parameters not allowed ('?').",
            err=True,
        )
        raise typer.Exit(1)

    if "#" in resource_id:
        typer.echo(
            "Invalid resource ID: fragment identifiers not allowed ('#').",
            err=True,
        )
        raise typer.Exit(1)
