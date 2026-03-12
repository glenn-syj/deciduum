"""Output mode utilities for AI-agent-friendly CLI output."""

import json
import sys
from enum import Enum
from typing import Any, Optional

# Exit code constants
EXIT_SUCCESS = 0
EXIT_GENERAL_ERROR = 1
EXIT_USAGE_ERROR = 2
EXIT_NOT_FOUND = 3
EXIT_PERMISSION_DENIED = 4
EXIT_CONFLICT = 5


class OutputMode(Enum):
    """Output mode for CLI commands."""

    PRETTY = "pretty"  # Human-friendly formatted output
    JSON = "json"  # Structured JSON output
    QUIET = "quiet"  # Bare values, one per line


def is_terminal() -> bool:
    """Check if stdout is connected to a terminal."""
    return sys.stdout.isatty()


def get_output_mode(
    json_flag: bool = False,
    quiet_flag: bool = False,
    tty_available: Optional[bool] = None,
) -> OutputMode:
    """
    Determine output format based on flags and terminal type.

    Priority:
    1. --json flag → JSON
    2. --quiet flag → QUIET
    3. not a TTY (piped) → JSON
    4. else → PRETTY

    Args:
        json_flag: Explicit JSON output requested
        quiet_flag: Explicit quiet mode requested
        tty_available: Override TTY detection (None = auto-detect)

    Returns:
        OutputMode enum value
    """
    # Priority 1: JSON flag
    if json_flag:
        return OutputMode.JSON

    # Priority 2: QUIET flag
    if quiet_flag:
        return OutputMode.QUIET

    # Priority 3: Not a TTY means piped output, use JSON
    if tty_available is None:
        tty_available = is_terminal()

    if not tty_available:
        return OutputMode.JSON

    # Priority 4: Default to PRETTY for interactive terminal
    return OutputMode.PRETTY


def echo_json(data: Any, pretty: bool = False) -> None:
    """Output data as JSON to stdout."""
    if pretty:
        json.dump(data, sys.stdout, indent=2, default=str)
    else:
        json.dump(data, sys.stdout, default=str)
    sys.stdout.write("\n")


def echo_error(
    message: str, json_flag: bool = False, error_code: str = "error"
) -> None:
    """Output error message to stderr, optionally as JSON."""
    if json_flag:
        json.dump({"error": error_code, "message": message}, sys.stderr, default=str)
        sys.stderr.write("\n")
    else:
        sys.stderr.write(message + "\n")
