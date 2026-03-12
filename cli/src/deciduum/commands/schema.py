"""Schema introspection commands."""

import json
import typer
from typing import Optional, List, Dict, Any

schema_app = typer.Typer(help="Schema introspection commands.")


# Schema definitions for each command group
# Format: command group -> subcommand -> {description, flags}
SCHEMA_DEFINITIONS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "decisions": {
        "list": {
            "description": "List all decisions",
            "flags": [
                {
                    "name": "json-output",
                    "type": "boolean",
                    "required": False,
                    "description": "Output as JSON",
                },
                {
                    "name": "quiet",
                    "type": "boolean",
                    "required": False,
                    "description": "Output IDs only, one per line",
                },
                {
                    "name": "status",
                    "type": "string",
                    "required": False,
                    "description": "Filter by status",
                },
                {
                    "name": "limit",
                    "type": "integer",
                    "required": False,
                    "description": "Number of decisions to show",
                },
                {
                    "name": "one-line",
                    "type": "boolean",
                    "required": False,
                    "description": "Show in one-line format",
                },
            ],
        },
        "add": {
            "description": "Add a new decision",
            "flags": [
                {
                    "name": "json-input",
                    "type": "string",
                    "required": False,
                    "description": "JSON payload",
                },
                {
                    "name": "title",
                    "type": "string",
                    "required": False,
                    "description": "Decision title",
                },
                {
                    "name": "date",
                    "type": "string",
                    "required": False,
                    "description": "Date (YYYY-MM-DD)",
                },
                {
                    "name": "status",
                    "type": "string",
                    "required": False,
                    "enum": ["ongoing", "completed", "archived"],
                    "description": "Decision status",
                },
                {
                    "name": "direction",
                    "type": "string",
                    "required": False,
                    "description": "Direction ID",
                },
            ],
        },
        "show": {
            "description": "Show a decision's details",
            "flags": [
                {
                    "name": "json-output",
                    "type": "boolean",
                    "required": False,
                    "description": "Output as JSON",
                },
                {
                    "name": "quiet",
                    "type": "boolean",
                    "required": False,
                    "description": "Output ID only",
                },
                {
                    "name": "with",
                    "type": "string",
                    "required": False,
                    "enum": ["memos", "tasks", "logs", "all"],
                    "description": "Show related items",
                },
            ],
        },
        "delete": {
            "description": "Soft delete a decision",
            "flags": [
                {
                    "name": "force",
                    "type": "boolean",
                    "required": False,
                    "description": "Skip confirmation",
                },
            ],
        },
        "next": {
            "description": "Show the next decision that needs review based on review_at date",
            "flags": [
                {
                    "name": "json-output",
                    "type": "boolean",
                    "required": False,
                    "description": "Output as JSON",
                },
                {
                    "name": "quiet",
                    "type": "boolean",
                    "required": False,
                    "description": "Output ID only",
                },
            ],
        },
        "pending": {
            "description": "List all pending decisions (ongoing status) that need attention",
            "flags": [
                {
                    "name": "json-output",
                    "type": "boolean",
                    "required": False,
                    "description": "Output as JSON",
                },
                {
                    "name": "quiet",
                    "type": "boolean",
                    "required": False,
                    "description": "Output IDs only, one per line",
                },
                {
                    "name": "overdue",
                    "type": "boolean",
                    "required": False,
                    "description": "Only show overdue decisions",
                },
                {
                    "name": "due-soon",
                    "type": "boolean",
                    "required": False,
                    "description": "Show decisions due within 7 days",
                },
            ],
        },
        "update": {
            "description": "Update a decision",
            "flags": [
                {
                    "name": "title",
                    "type": "string",
                    "required": False,
                    "description": "Decision title",
                },
                {
                    "name": "status",
                    "type": "string",
                    "required": False,
                    "enum": ["ongoing", "completed", "archived"],
                    "description": "Status",
                },
                {
                    "name": "direction",
                    "type": "string",
                    "required": False,
                    "description": "Direction ID",
                },
                {
                    "name": "review-at",
                    "type": "string",
                    "required": False,
                    "description": "Review date (YYYY-MM-DD)",
                },
            ],
        },
    },
    "tasks": {
        "list": {
            "description": "List all tasks",
            "flags": [
                {
                    "name": "json-output",
                    "type": "boolean",
                    "required": False,
                    "description": "Output as JSON",
                },
                {
                    "name": "quiet",
                    "type": "boolean",
                    "required": False,
                    "description": "Output IDs only, one per line",
                },
                {
                    "name": "status",
                    "type": "string",
                    "required": False,
                    "description": "Filter by status",
                },
                {
                    "name": "decision",
                    "type": "string",
                    "required": False,
                    "description": "Filter by decision ID",
                },
                {
                    "name": "limit",
                    "type": "integer",
                    "required": False,
                    "description": "Number of tasks to show",
                },
                {
                    "name": "one-line",
                    "type": "boolean",
                    "required": False,
                    "description": "Show compact one-line output",
                },
            ],
        },
        "add": {
            "description": "Add a new task",
            "flags": [
                {
                    "name": "json-input",
                    "type": "string",
                    "required": False,
                    "description": "JSON payload",
                },
                {
                    "name": "title",
                    "type": "string",
                    "required": False,
                    "description": "Task title",
                },
                {
                    "name": "decision",
                    "type": "string",
                    "required": False,
                    "description": "Decision ID to link to",
                },
                {
                    "name": "due-date",
                    "type": "string",
                    "required": False,
                    "description": "Due date (YYYY-MM-DD)",
                },
                {
                    "name": "notes",
                    "type": "string",
                    "required": False,
                    "description": "Task notes",
                },
                {
                    "name": "status",
                    "type": "string",
                    "required": False,
                    "enum": ["pending", "in_progress", "completed"],
                    "description": "Status",
                },
            ],
        },
        "show": {
            "description": "Show a task's details",
            "flags": [
                {
                    "name": "json-output",
                    "type": "boolean",
                    "required": False,
                    "description": "Output as JSON",
                },
                {
                    "name": "quiet",
                    "type": "boolean",
                    "required": False,
                    "description": "Output ID only",
                },
            ],
        },
        "complete": {
            "description": "Mark a task as completed",
            "flags": [],
        },
        "delete": {
            "description": "Soft delete a task",
            "flags": [
                {
                    "name": "force",
                    "type": "boolean",
                    "required": False,
                    "description": "Skip confirmation",
                },
            ],
        },
        "update": {
            "description": "Update a task",
            "flags": [
                {
                    "name": "title",
                    "type": "string",
                    "required": False,
                    "description": "Task title",
                },
                {
                    "name": "status",
                    "type": "string",
                    "required": False,
                    "enum": ["pending", "in_progress", "completed"],
                    "description": "Status",
                },
                {
                    "name": "due-date",
                    "type": "string",
                    "required": False,
                    "description": "Due date (YYYY-MM-DD)",
                },
                {
                    "name": "notes",
                    "type": "string",
                    "required": False,
                    "description": "Task notes",
                },
            ],
        },
    },
    "memos": {
        "list": {
            "description": "List all memos",
            "flags": [
                {
                    "name": "json-output",
                    "type": "boolean",
                    "required": False,
                    "description": "Output as JSON",
                },
                {
                    "name": "quiet",
                    "type": "boolean",
                    "required": False,
                    "description": "Output IDs only, one per line",
                },
                {
                    "name": "date",
                    "type": "string",
                    "required": False,
                    "description": "Filter by date",
                },
                {
                    "name": "limit",
                    "type": "integer",
                    "required": False,
                    "description": "Number of memos to show",
                },
                {
                    "name": "one-line",
                    "type": "boolean",
                    "required": False,
                    "description": "Show compact one-line format",
                },
            ],
        },
        "add": {
            "description": "Add a new memo",
            "flags": [
                {
                    "name": "json-input",
                    "type": "string",
                    "required": False,
                    "description": "JSON payload",
                },
                {
                    "name": "content",
                    "type": "string",
                    "required": False,
                    "description": "Memo content",
                },
                {
                    "name": "date",
                    "type": "string",
                    "required": False,
                    "description": "Date (YYYY-MM-DD)",
                },
                {
                    "name": "decision",
                    "type": "string",
                    "required": False,
                    "description": "Linked decision ID",
                },
                {
                    "name": "direction",
                    "type": "string",
                    "required": False,
                    "description": "Linked direction ID",
                },
            ],
        },
        "show": {
            "description": "Show a memo's details",
            "flags": [
                {
                    "name": "json-output",
                    "type": "boolean",
                    "required": False,
                    "description": "Output as JSON",
                },
                {
                    "name": "quiet",
                    "type": "boolean",
                    "required": False,
                    "description": "Output ID only",
                },
            ],
        },
        "delete": {
            "description": "Soft delete a memo",
            "flags": [
                {
                    "name": "force",
                    "type": "boolean",
                    "required": False,
                    "description": "Skip confirmation",
                },
            ],
        },
        "update": {
            "description": "Update a memo",
            "flags": [
                {
                    "name": "content",
                    "type": "string",
                    "required": False,
                    "description": "Memo content",
                },
                {
                    "name": "decision",
                    "type": "string",
                    "required": False,
                    "description": "Linked decision ID",
                },
                {
                    "name": "direction",
                    "type": "string",
                    "required": False,
                    "description": "Linked direction ID",
                },
            ],
        },
    },
    "directions": {
        "list": {
            "description": "List all directions",
            "flags": [
                {
                    "name": "json-output",
                    "type": "boolean",
                    "required": False,
                    "description": "Output as JSON",
                },
                {
                    "name": "quiet",
                    "type": "boolean",
                    "required": False,
                    "description": "Output IDs only, one per line",
                },
                {
                    "name": "limit",
                    "type": "integer",
                    "required": False,
                    "description": "Number of directions to show",
                },
                {
                    "name": "one-line",
                    "type": "boolean",
                    "required": False,
                    "description": "Show compact one-line format",
                },
            ],
        },
        "add": {
            "description": "Add a new direction",
            "flags": [
                {
                    "name": "json-input",
                    "type": "string",
                    "required": False,
                    "description": "JSON payload",
                },
                {
                    "name": "title",
                    "type": "string",
                    "required": False,
                    "description": "Direction title",
                },
            ],
        },
        "show": {
            "description": "Show a direction's details",
            "flags": [
                {
                    "name": "json-output",
                    "type": "boolean",
                    "required": False,
                    "description": "Output as JSON",
                },
                {
                    "name": "quiet",
                    "type": "boolean",
                    "required": False,
                    "description": "Output ID only",
                },
            ],
        },
        "delete": {
            "description": "Soft delete a direction",
            "flags": [
                {
                    "name": "force",
                    "type": "boolean",
                    "required": False,
                    "description": "Skip confirmation",
                },
            ],
        },
        "update": {
            "description": "Update a direction",
            "flags": [
                {
                    "name": "title",
                    "type": "string",
                    "required": False,
                    "description": "Direction title",
                },
            ],
        },
    },
    "logs": {
        "add": {
            "description": "Add a log entry to a decision",
            "flags": [
                {
                    "name": "type",
                    "type": "string",
                    "required": False,
                    "enum": ["note", "reflection", "state_change"],
                    "description": "Log type",
                },
                {
                    "name": "content",
                    "type": "string",
                    "required": True,
                    "description": "Log content",
                },
                {
                    "name": "source",
                    "type": "string",
                    "required": False,
                    "description": "Source (human/system)",
                },
            ],
        },
        "list": {
            "description": "List all logs for a decision",
            "flags": [
                {
                    "name": "json-output",
                    "type": "boolean",
                    "required": False,
                    "description": "Output as JSON",
                },
                {
                    "name": "quiet",
                    "type": "boolean",
                    "required": False,
                    "description": "Output IDs only, one per line",
                },
                {
                    "name": "limit",
                    "type": "integer",
                    "required": False,
                    "description": "Number of logs to show",
                },
            ],
        },
        "delete": {
            "description": "Delete a log entry",
            "flags": [
                {
                    "name": "force",
                    "type": "boolean",
                    "required": False,
                    "description": "Skip confirmation",
                },
            ],
        },
    },
    "journey": {
        "show": {
            "description": "Show full decision journey timeline",
            "flags": [
                {
                    "name": "json-output",
                    "type": "boolean",
                    "required": False,
                    "description": "Output as JSON",
                },
                {
                    "name": "quiet",
                    "type": "boolean",
                    "required": False,
                    "description": "Output ID only",
                },
            ],
        },
    },
    "session": {
        "list": {
            "description": "List all existing sessions",
            "flags": [],
        },
        "info": {
            "description": "Show information about a session",
            "flags": [],
        },
        "create": {
            "description": "Create a new session",
            "flags": [
                {
                    "name": "name",
                    "type": "string",
                    "required": False,
                    "description": "Session display name",
                },
            ],
        },
        "delete": {
            "description": "Delete a session and its database",
            "flags": [
                {
                    "name": "force",
                    "type": "boolean",
                    "required": False,
                    "description": "Skip confirmation",
                },
            ],
        },
        "path": {
            "description": "Show the database path for a session",
            "flags": [],
        },
    },
    "config": {
        "set": {
            "description": "Set a configuration value",
            "flags": [],
        },
        "unset": {
            "description": "Remove a configuration value",
            "flags": [],
        },
        "show": {
            "description": "Show all configuration values",
            "flags": [],
        },
        "get": {
            "description": "Get a specific configuration value",
            "flags": [],
        },
    },
    "today": {
        "": {
            "description": "Show today's summary",
            "flags": [],
        },
    },
}


def _build_command_schema(group: str, subcommand: str) -> Optional[Dict[str, Any]]:
    """Build schema for a specific command."""
    if group in SCHEMA_DEFINITIONS:
        if subcommand in SCHEMA_DEFINITIONS[group]:
            schema = SCHEMA_DEFINITIONS[group][subcommand]
            return {
                "command": f"{group} {subcommand}",
                "description": schema["description"],
                "flags": schema["flags"],
            }
    return None


def _list_all_schemas() -> List[Dict[str, Any]]:
    """List all available command schemas."""
    schemas = []
    for group, subcommands in SCHEMA_DEFINITIONS.items():
        for subcommand, schema in subcommands.items():
            cmd_name = f"{group} {subcommand}" if subcommand else group
            schemas.append(
                {
                    "command": cmd_name,
                    "description": schema["description"],
                    "flags": schema["flags"],
                }
            )
    return schemas


@schema_app.command("decisions")
def schema_decisions(
    subcommand: Optional[str] = typer.Argument(
        None, help="Subcommand (e.g., add, list)"
    ),
):
    """Show schema for decisions commands."""
    if subcommand:
        result = _build_command_schema("decisions", subcommand)
        if result:
            typer.echo(json.dumps(result, indent=2))
        else:
            typer.echo(f"Unknown subcommand: {subcommand}", err=True)
            raise typer.Exit(1)
    else:
        # List all decisions subcommands
        schemas = []
        for sub, schema in SCHEMA_DEFINITIONS.get("decisions", {}).items():
            schemas.append(
                {
                    "command": f"decisions {sub}",
                    "description": schema["description"],
                    "flags": schema["flags"],
                }
            )
        typer.echo(json.dumps(schemas, indent=2))


@schema_app.command("tasks")
def schema_tasks(
    subcommand: Optional[str] = typer.Argument(
        None, help="Subcommand (e.g., add, list)"
    ),
):
    """Show schema for tasks commands."""
    if subcommand:
        result = _build_command_schema("tasks", subcommand)
        if result:
            typer.echo(json.dumps(result, indent=2))
        else:
            typer.echo(f"Unknown subcommand: {subcommand}", err=True)
            raise typer.Exit(1)
    else:
        schemas = []
        for sub, schema in SCHEMA_DEFINITIONS.get("tasks", {}).items():
            schemas.append(
                {
                    "command": f"tasks {sub}",
                    "description": schema["description"],
                    "flags": schema["flags"],
                }
            )
        typer.echo(json.dumps(schemas, indent=2))


@schema_app.command("memos")
def schema_memos(
    subcommand: Optional[str] = typer.Argument(
        None, help="Subcommand (e.g., add, list)"
    ),
):
    """Show schema for memos commands."""
    if subcommand:
        result = _build_command_schema("memos", subcommand)
        if result:
            typer.echo(json.dumps(result, indent=2))
        else:
            typer.echo(f"Unknown subcommand: {subcommand}", err=True)
            raise typer.Exit(1)
    else:
        schemas = []
        for sub, schema in SCHEMA_DEFINITIONS.get("memos", {}).items():
            schemas.append(
                {
                    "command": f"memos {sub}",
                    "description": schema["description"],
                    "flags": schema["flags"],
                }
            )
        typer.echo(json.dumps(schemas, indent=2))


@schema_app.command("directions")
def schema_directions(
    subcommand: Optional[str] = typer.Argument(
        None, help="Subcommand (e.g., add, list)"
    ),
):
    """Show schema for directions commands."""
    if subcommand:
        result = _build_command_schema("directions", subcommand)
        if result:
            typer.echo(json.dumps(result, indent=2))
        else:
            typer.echo(f"Unknown subcommand: {subcommand}", err=True)
            raise typer.Exit(1)
    else:
        schemas = []
        for sub, schema in SCHEMA_DEFINITIONS.get("directions", {}).items():
            schemas.append(
                {
                    "command": f"directions {sub}",
                    "description": schema["description"],
                    "flags": schema["flags"],
                }
            )
        typer.echo(json.dumps(schemas, indent=2))


@schema_app.command("logs")
def schema_logs(
    subcommand: Optional[str] = typer.Argument(
        None, help="Subcommand (e.g., add, list)"
    ),
):
    """Show schema for logs commands."""
    if subcommand:
        result = _build_command_schema("logs", subcommand)
        if result:
            typer.echo(json.dumps(result, indent=2))
        else:
            typer.echo(f"Unknown subcommand: {subcommand}", err=True)
            raise typer.Exit(1)
    else:
        schemas = []
        for sub, schema in SCHEMA_DEFINITIONS.get("logs", {}).items():
            schemas.append(
                {
                    "command": f"logs {sub}",
                    "description": schema["description"],
                    "flags": schema["flags"],
                }
            )
        typer.echo(json.dumps(schemas, indent=2))


@schema_app.command("journey")
def schema_journey(
    subcommand: Optional[str] = typer.Argument(None, help="Subcommand (e.g., show)"),
):
    """Show schema for journey commands."""
    if subcommand:
        result = _build_command_schema("journey", subcommand)
        if result:
            typer.echo(json.dumps(result, indent=2))
        else:
            typer.echo(f"Unknown subcommand: {subcommand}", err=True)
            raise typer.Exit(1)
    else:
        schemas = []
        for sub, schema in SCHEMA_DEFINITIONS.get("journey", {}).items():
            schemas.append(
                {
                    "command": f"journey {sub}",
                    "description": schema["description"],
                    "flags": schema["flags"],
                }
            )
        typer.echo(json.dumps(schemas, indent=2))


@schema_app.command("session")
def schema_session(
    subcommand: Optional[str] = typer.Argument(
        None, help="Subcommand (e.g., list, info)"
    ),
):
    """Show schema for session commands."""
    if subcommand:
        result = _build_command_schema("session", subcommand)
        if result:
            typer.echo(json.dumps(result, indent=2))
        else:
            typer.echo(f"Unknown subcommand: {subcommand}", err=True)
            raise typer.Exit(1)
    else:
        schemas = []
        for sub, schema in SCHEMA_DEFINITIONS.get("session", {}).items():
            schemas.append(
                {
                    "command": f"session {sub}",
                    "description": schema["description"],
                    "flags": schema["flags"],
                }
            )
        typer.echo(json.dumps(schemas, indent=2))


@schema_app.command("config")
def schema_config(
    subcommand: Optional[str] = typer.Argument(
        None, help="Subcommand (e.g., set, get)"
    ),
):
    """Show schema for config commands."""
    if subcommand:
        result = _build_command_schema("config", subcommand)
        if result:
            typer.echo(json.dumps(result, indent=2))
        else:
            typer.echo(f"Unknown subcommand: {subcommand}", err=True)
            raise typer.Exit(1)
    else:
        schemas = []
        for sub, schema in SCHEMA_DEFINITIONS.get("config", {}).items():
            schemas.append(
                {
                    "command": f"config {sub}",
                    "description": schema["description"],
                    "flags": schema["flags"],
                }
            )
        typer.echo(json.dumps(schemas, indent=2))


@schema_app.command("today")
def schema_today():
    """Show schema for today command."""
    result = _build_command_schema("today", "")
    # Fix the command name to not have trailing space
    result["command"] = "today"
    typer.echo(json.dumps(result, indent=2))


@schema_app.command("all")
def schema_all():
    """Show schema for all commands."""
    schemas = _list_all_schemas()
    typer.echo(json.dumps(schemas, indent=2))
