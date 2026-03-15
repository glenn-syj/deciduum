"""Schema introspection commands."""

import inspect
import json
from typing import Any, Dict, List, Optional, get_type_hints, get_origin, get_args

import typer

# Import schema classes for JSON payload extraction
from deciduum.schemas import *  # noqa: F401, F403

# Note: We import subapps directly to avoid circular imports

# Map of (app_name, command_name) -> (create_model_name, module_name)
# This maps CLI commands to their Pydantic payload schemas
PAYLOAD_MODELS = {
    ("decisions", "add"): ("DecisionCreate", "decision.py"),
    ("decisions", "update"): ("DecisionUpdate", "decision.py"),
    ("tasks", "add"): ("TaskCreate", "task.py"),
    ("tasks", "update"): ("TaskUpdate", "task.py"),
    ("memos", "add"): ("MemoCreate", "memo.py"),
    ("memos", "update"): ("MemoUpdate", "memo.py"),
    ("directions", "add"): ("DirectionCreate", "direction.py"),
    ("directions", "update"): ("DirectionUpdate", "direction.py"),
    ("logs", "add"): ("LogCreate", "log.py"),
    ("session", "create"): ("SessionCreate", "session.py"),
}


def _get_model_from_schema(model_name: str) -> Optional[type]:
    """Get a Pydantic model class by name from the schemas module."""
    import deciduum.schemas as schemas_module

    return getattr(schemas_module, model_name, None)


def _extract_json_fields(model_class: type) -> Dict[str, Any]:
    """Extract JSON field definitions from a Pydantic model."""
    if model_class is None:
        return {}

    try:
        json_schema = model_class.model_json_schema()
    except Exception:
        return {}

    json_fields = {}
    properties = json_schema.get("properties", {})
    required_fields = json_schema.get("required", [])

    for field_name, field_schema in properties.items():
        # Determine if required
        is_required = field_name in required_fields

        # Extract type
        field_type = field_schema.get("type", "string")

        # Handle Pydantic's "anyOf" for optional fields with defaults
        if "anyOf" in field_schema:
            # Get the first non-null type
            for type_info in field_schema["anyOf"]:
                if type_info.get("type") != "null":
                    field_type = type_info.get("type", "string")
                    break

        # Extract description
        description = field_schema.get("description", "")

        # Extract default value
        default = field_schema.get("default")

        field_info = {
            "type": field_type,
            "required": is_required,
        }

        if description:
            field_info["description"] = description

        if default is not None:
            field_info["default"] = default

        json_fields[field_name] = field_info

    return json_fields


schema_app = typer.Typer(help="Schema introspection commands.")


def _python_type_to_json_type(py_type: Any) -> str:
    """Convert Python type to JSON-serializable type name."""
    # Handle Optional types (Union with None)
    origin = get_origin(py_type)
    if origin is not None:
        # Handle Optional[X] which is Union[X, None]
        args = get_args(py_type)
        if type(None) in args:
            # It's Optional[X], get the non-None type
            non_none_types = [a for a in args if a is not type(None)]
            if non_none_types:
                py_type = non_none_types[0]

    # Handle typing.List, typing.Optional, etc.
    origin = get_origin(py_type)
    if origin is list:
        return "array"
    if origin is dict:
        return "object"

    # Handle regular types
    type_name = str(py_type).lower()

    if "int" in type_name and "string" not in type_name:
        return "integer"
    elif "float" in type_name:
        return "number"
    elif "bool" in type_name:
        return "boolean"
    elif "str" in type_name or "string" in type_name:
        return "string"
    elif "path" in type_name:
        return "string"  # Path is serialized as string
    else:
        return "string"  # Default to string


def _get_param_schema(param_name: str, param: inspect.Parameter) -> Dict[str, Any]:
    """Extract schema from a single parameter.

    - Detect if required: param.default is ... (Ellipsis)
    - Extract type from param.annotation
    - Extract help from param.default.help if available
    - Extract choices/enum from param.default.choices if available
    - Convert to JSON-serializable type names (string, int, bool)
    """
    # Determine if required (default is Ellipsis)
    # For Typer Option/Argument objects, check param.default.default
    # For regular parameters, check param.default directly
    is_required = False
    if hasattr(param.default, "default"):
        # It's a Typer Option/Argument - check inner default
        is_required = param.default.default is ...
    else:
        # Regular parameter or bare Ellipsis
        is_required = param.default is ...

    # Extract type
    param_type = "string"  # Default
    if param.annotation is not inspect.Parameter.empty:
        param_type = _python_type_to_json_type(param.annotation)

    # Extract help text and choices from default (if it's a Typer Option)
    description = ""
    choices = None

    # Try to get the long option name from Typer's param_decls
    flag_name = param.name.replace("_", "-")

    if param.default is not inspect.Parameter.empty and param.default is not None:
        # Check if it's a Typer Option/Argument object
        default_val = param.default
        if hasattr(default_val, "help") and default_val.help:
            description = default_val.help
        if hasattr(default_val, "choices") and default_val.choices:
            choices = list(default_val.choices)
        # Also check for enum attribute
        if hasattr(default_val, "enum") and default_val.enum:
            choices = list(default_val.enum)

        # Try to extract the long option name from param_decls
        if hasattr(default_val, "param_decls") and default_val.param_decls:
            param_decls = default_val.param_decls
            # Find the long option (starts with --)
            for decl in param_decls:
                if decl.startswith("--"):
                    # Remove leading dashes
                    flag_name = decl[2:]
                    break
                elif decl.startswith("-"):
                    # It's a short option, skip
                    continue

    # Handle case where it's an Argument vs Option
    # Arguments don't have the -- prefix in help, but we still want the name
    result = {
        "name": flag_name,
        "type": param_type,
        "required": is_required,
    }

    if description:
        result["description"] = description
    if choices:
        result["enum"] = choices

    return result


def _get_command_schema(cmd_name: str, cmd) -> Dict[str, Any]:
    """Extract schema for a single command using inspect.signature(cmd.callback)"""
    # Get the callback function (the actual command function)
    callback = cmd.callback

    if callback is None:
        return None

    # Get function signature
    try:
        sig = inspect.signature(callback)
    except (ValueError, TypeError):
        return None

    # Get description from docstring
    description = ""
    if callback.__doc__:
        # Take first line of docstring
        description = callback.__doc__.strip().split("\n")[0].strip()

    # Extract parameters (skip 'ctx' which is always first in Typer commands)
    flags = []
    for param_name, param in sig.parameters.items():
        # Skip 'ctx' parameter which is added by Typer
        if param_name == "ctx":
            continue

        flag_schema = _get_param_schema(param_name, param)
        flags.append(flag_schema)

    return {
        "command": cmd_name,
        "description": description,
        "flags": flags,
    }


def _get_subapp_schema(subapp, prefix: str = "") -> List[Dict[str, Any]]:
    """Extract schema for all commands in a subapp."""
    schemas = []

    # subapp.registered_groups contains the commands
    # Each group has registered_commands
    if hasattr(subapp, "registered_groups"):
        for group in subapp.registered_groups:
            # This group might have subcommands
            if hasattr(group, "registered_commands"):
                for cmd in group.registered_commands:
                    cmd_name = f"{prefix} {cmd.name}" if prefix else cmd.name
                    schema = _get_command_schema(cmd_name, cmd)
                    if schema:
                        schemas.append(schema)

    # Also check for direct commands on the app
    if hasattr(subapp, "registered_commands"):
        for cmd in subapp.registered_commands:
            cmd_name = f"{prefix} {cmd.name}" if prefix else cmd.name
            schema = _get_command_schema(cmd_name, cmd)
            if schema:
                schemas.append(schema)

    return schemas


def _get_today_schema() -> Dict[str, Any]:
    """Get schema for the today command (a plain function, not a typer app)."""
    from deciduum.commands.today import today_command

    try:
        sig = inspect.signature(today_command)
    except (ValueError, TypeError):
        return None

    description = ""
    if today_command.__doc__:
        description = today_command.__doc__.strip().split("\n")[0].strip()

    return {
        "command": "today",
        "description": description,
        "flags": [],
    }


def generate_full_schema() -> List[dict]:
    """Generate schema for all commands by walking app.registered_groups"""
    schemas = []

    # Import the subapps
    from deciduum.commands.session import session_app
    from deciduum.commands.config import config_app
    from deciduum.commands.decisions import decisions_app
    from deciduum.commands.memos import memos_app
    from deciduum.commands.directions import directions_app
    from deciduum.commands.tasks import tasks_app
    from deciduum.commands.logs import logs_app
    from deciduum.commands.logs import journey_app

    # Add each subapp's commands
    subapps = [
        ("decisions", decisions_app),
        ("tasks", tasks_app),
        ("memos", memos_app),
        ("directions", directions_app),
        ("logs", logs_app),
        ("journey", journey_app),
        ("session", session_app),
        ("config", config_app),
    ]

    for name, subapp in subapps:
        subapp_schemas = _get_subapp_schema(subapp, prefix=name)
        schemas.extend(subapp_schemas)

    # Add today command
    today_schema = _get_today_schema()
    if today_schema:
        schemas.append(today_schema)

    return schemas


def _build_command_schema(group: str, subcommand: str) -> Optional[Dict[str, Any]]:
    """Build schema for a specific command, including JSON payload schema if available."""
    schemas = generate_full_schema()

    # Find matching command
    target_cmd = f"{group} {subcommand}" if subcommand else group

    for schema in schemas:
        if schema["command"] == target_cmd:
            # Check if this command has a JSON payload model
            if subcommand and (group, subcommand) in PAYLOAD_MODELS:
                model_name, _ = PAYLOAD_MODELS[(group, subcommand)]
                model_class = _get_model_from_schema(model_name)
                if model_class:
                    json_fields = _extract_json_fields(model_class)
                    if json_fields:
                        schema["json_fields"] = json_fields
            return schema

    return None


def _list_all_schemas() -> List[Dict[str, Any]]:
    """List all available command schemas."""
    return generate_full_schema()


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
        for schema in generate_full_schema():
            if schema["command"].startswith("decisions "):
                schemas.append(schema)
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
        for schema in generate_full_schema():
            if schema["command"].startswith("tasks "):
                schemas.append(schema)
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
        for schema in generate_full_schema():
            if schema["command"].startswith("memos "):
                schemas.append(schema)
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
        for schema in generate_full_schema():
            if schema["command"].startswith("directions "):
                schemas.append(schema)
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
        for schema in generate_full_schema():
            if schema["command"].startswith("logs "):
                schemas.append(schema)
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
        for schema in generate_full_schema():
            if schema["command"].startswith("journey "):
                schemas.append(schema)
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
        for schema in generate_full_schema():
            if schema["command"].startswith("session "):
                schemas.append(schema)
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
        for schema in generate_full_schema():
            if schema["command"].startswith("config "):
                schemas.append(schema)
        typer.echo(json.dumps(schemas, indent=2))


@schema_app.command("today")
def schema_today():
    """Show schema for today command."""
    result = _build_command_schema("today", "")
    if result:
        typer.echo(json.dumps(result, indent=2))
    else:
        typer.echo("Could not generate schema for today command", err=True)
        raise typer.Exit(1)


@schema_app.command("all")
def schema_all():
    """Show schema for all commands."""
    schemas = _list_all_schemas()
    typer.echo(json.dumps(schemas, indent=2))
