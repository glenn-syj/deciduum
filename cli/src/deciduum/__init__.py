"""Deciduum CLI - Decision tracking with session-based multi-database architecture."""

__version__ = "0.1.0"

# Exit code constants
from .output import (
    EXIT_SUCCESS,
    EXIT_GENERAL_ERROR,
    EXIT_USAGE_ERROR,
    EXIT_NOT_FOUND,
    EXIT_PERMISSION_DENIED,
    EXIT_CONFLICT,
)

# Output mode utilities
from .output import (
    OutputMode,
    get_output_mode,
    is_terminal,
    echo_json,
    echo_error,
)

__all__ = [
    # Version
    "__version__",
    # Exit codes
    "EXIT_SUCCESS",
    "EXIT_GENERAL_ERROR",
    "EXIT_USAGE_ERROR",
    "EXIT_NOT_FOUND",
    "EXIT_PERMISSION_DENIED",
    "EXIT_CONFLICT",
    # Output utilities
    "OutputMode",
    "get_output_mode",
    "is_terminal",
    "echo_json",
    "echo_error",
]
