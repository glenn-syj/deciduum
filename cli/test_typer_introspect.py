#!/usr/bin/env python3
"""Explore Typer introspection API."""

import sys

sys.path.insert(0, "/home/glennsyj/deciduum/cli/src")

from deciduum.__main__ import app


def explore_typer_app():
    """Explore and print Typer app introspection data."""

    print("=" * 70)
    print("TYPER INTROSPECTION EXPLORATION")
    print("=" * 70)

    # Print app attributes
    print("\n--- APP ATTRIBUTES ---")
    print(f"app.type: {type(app)}")
    print(f"app.dir: {[a for a in dir(app) if not a.startswith('_')]}")

    # Check registered_subapps (Typer apps added via add_typer)
    print("\n--- REGISTERED SUBAPPS ---")
    if hasattr(app, "registered_subapps"):
        print(f"Type: {type(app.registered_subapps)}")
        print(f"Value: {app.registered_subapps}")

        for subapp in app.registered_subapps:
            print(f"\n  Subapp: {subapp}")
            print(f"    Type: {type(subapp)}")
            print(f"    Dir: {[a for a in dir(subapp) if not a.startswith('_')]}")
            if hasattr(subapp, "name"):
                print(f"    name: {subapp.name}")
            if hasattr(subapp, "info"):
                print(f"    info: {subapp.info}")
    else:
        print("No registered_subapps attribute")

    # Check registered_commands
    print("\n--- REGISTERED COMMANDS ---")
    if hasattr(app, "registered_commands"):
        print(f"Type: {type(app.registered_commands)}")

        for cmd in app.registered_commands:
            print(f"\n  Command: {cmd}")
            print(f"    Type: {type(cmd)}")
            print(f"    Dir: {[a for a in dir(cmd) if not a.startswith('_')]}")

            # Common attributes
            if hasattr(cmd, "name"):
                print(f"    name: {cmd.name}")
            if hasattr(cmd, "callback"):
                print(f"    callback: {cmd.callback}")
            if hasattr(cmd, "params"):
                print(f"    params: {cmd.params}")
            if hasattr(cmd, "rich_help_panel"):
                print(f"    rich_help_panel: {cmd.rich_help_panel}")
    else:
        print("No registered_commands attribute")

    # Try to get commands via typer CLI info
    print("\n--- APP COMMANDS (via app.commands) ---")
    if hasattr(app, "commands"):
        print(f"app.commands: {app.commands}")
        for name, cmd in app.commands.items():
            print(f"  {name}: {cmd}")
    else:
        print("No app.commands attribute")

    # Check all attrs starting with 'registered'
    print("\n--- ALL 'REGISTERED' ATTRS ---")
    registered_attrs = [a for a in dir(app) if "registered" in a.lower()]
    print(f"Attrs with 'registered': {registered_attrs}")

    for attr_name in registered_attrs:
        attr = getattr(app, attr_name, None)
        print(f"  {attr_name}: {attr}")
        if hasattr(attr, "__iter__") and not isinstance(attr, str):
            for item in attr:
                print(f"    - {item}")


def explore_subapp_details():
    """Explore subapp details more deeply using registered_groups."""

    print("\n" + "=" * 70)
    print("DETAILED SUBAPP EXPLORATION (via registered_groups)")
    print("=" * 70)

    if not hasattr(app, "registered_groups"):
        print("No registered_groups found")
        return

    print(f"Found {len(app.registered_groups)} registered groups\n")

    for idx, group in enumerate(app.registered_groups):
        print(f"--- Group {idx + 1}: {type(group)} ---")

        # Explore TyperInfo object attributes
        group_attrs = [a for a in dir(group) if not a.startswith("_")]
        print(f"Attributes: {group_attrs}")

        # Common attributes
        if hasattr(group, "name"):
            print(f"  name: {group.name}")

        # Try to get the actual subapp object - it's 'typer_instance'
        if hasattr(group, "typer_instance") and group.typer_instance:
            subapp = group.typer_instance
            print(f"\n  Subapp object: {type(subapp)}")
            print(f"  Subapp dir: {[a for a in dir(subapp) if not a.startswith('_')]}")

            # Check for commands in the subapp
            if hasattr(subapp, "registered_commands"):
                print(f"  Registered commands in subapp:")
                for cmd in subapp.registered_commands:
                    print(f"    - {cmd}")
                    if hasattr(cmd, "name"):
                        print(f"        name: {cmd.name}")
                    if hasattr(cmd, "callback") and cmd.callback:
                        print(f"        callback: {cmd.callback}")
                        params = get_cmd_params(cmd.callback)
                        for p in params:
                            print(f"        param: {p}")


def explore_command_details():
    """Explore command details more deeply using registered_commands."""

    print("\n" + "=" * 70)
    print("DETAILED COMMAND EXPLORATION")
    print("=" * 70)

    import inspect

    # Get all commands from app
    all_commands = []

    # Main app commands from registered_commands
    if hasattr(app, "registered_commands"):
        for cmd_info in app.registered_commands:
            all_commands.append(("app", cmd_info))

    # Subapp commands from registered_groups
    if hasattr(app, "registered_groups"):
        for group in app.registered_groups:
            if hasattr(group, "typer_instance") and group.typer_instance:
                subapp = group.typer_instance
                if hasattr(subapp, "registered_commands"):
                    subapp_name = getattr(group, "name", "unknown")
                    for cmd_info in subapp.registered_commands:
                        all_commands.append((f"subapp:{subapp_name}", cmd_info))

    print(f"Found {len(all_commands)} total command sources\n")

    for source, cmd_info in all_commands:
        print(f"--- Command from {source} ---")
        print(f"    Type: {type(cmd_info)}")

        # Print all attributes of CommandInfo
        cmd_attrs = [a for a in dir(cmd_info) if not a.startswith("_")]
        print(f"    Attributes: {cmd_attrs}")

        # Common attributes
        if hasattr(cmd_info, "name"):
            print(f"    name: {cmd_info.name}")
        if hasattr(cmd_info, "callback"):
            print(f"    callback: {cmd_info.callback}")
        if hasattr(cmd_info, "help"):
            print(f"    help: {cmd_info.help}")
        if hasattr(cmd_info, "short_help"):
            print(f"    short_help: {cmd_info.short_help}")
        if hasattr(cmd_info, "hidden"):
            print(f"    hidden: {cmd_info.hidden}")
        if hasattr(cmd_info, "deprecated"):
            print(f"    deprecated: {cmd_info.deprecated}")

        # Get callback parameters
        if hasattr(cmd_info, "callback") and cmd_info.callback:
            params = get_cmd_params(cmd_info.callback)
            print(f"    Parameters:")
            for p in params:
                print(f"      - {p}")


def get_cmd_params(callback):
    """Get parameters from a callback function."""
    import inspect

    if not callback:
        return []

    params = []
    try:
        sig = inspect.signature(callback)
        for name, param in sig.parameters.items():
            param_info = {
                "name": name,
                "default": str(param.default)
                if param.default != inspect.Parameter.empty
                else "REQUIRED",
                "annotation": str(param.annotation)
                if param.annotation != inspect.Parameter.empty
                else "Any",
            }

            # Check for Typer-specific attributes
            if hasattr(param, "param_declared"):
                param_info["param_declared"] = param.param_declared

            params.append(param_info)
    except Exception as e:
        return [{"error": str(e)}]

    return params


def explore_typer_special_attrs():
    """Explore Typer-specific attributes."""

    print("\n" + "=" * 70)
    print("TYPER-SPECIFIC ATTRIBUTES")
    print("=" * 70)

    import typer

    # Check typer version
    print(f"\nTyper version: {typer.__version__}")

    # Check Typer class attributes
    print(f"\nTyper.Typer class attributes:")
    typer_attrs = [a for a in dir(typer.Typer) if not a.startswith("_")]
    print(f"  {typer_attrs}")

    # Check if there's an app attribute for subcommands
    print(f"\n--- App's _subcommands (private attr) ---")
    if hasattr(app, "_subcommands"):
        print(f"  _subcommands: {app._subcommands}")

    print(f"\n--- App's _commands (private attr) ---")
    if hasattr(app, "_commands"):
        print(f"  _commands: {app._commands}")


if __name__ == "__main__":
    explore_typer_app()
    explore_subapp_details()
    explore_command_details()
    explore_typer_special_attrs()
