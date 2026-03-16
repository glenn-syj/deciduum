"""Session management commands."""

import os
import shutil
from pathlib import Path

import typer

from deciduum.config import get_session_id, get_sessions_dir, get_session_db_path
from deciduum.database import get_db_manager, get_db
from deciduum.models import SessionInfo
from deciduum.schemas import SessionCreate

session_app = typer.Typer(help="Session management commands.")


@session_app.command("list")
def list_sessions():
    """List all existing sessions."""
    sessions_dir = get_sessions_dir()

    if not sessions_dir.exists():
        typer.echo("No sessions found.")
        return

    current_session = get_session_id()
    db_files = list(sessions_dir.glob("*.db"))

    if not db_files:
        typer.echo("No sessions found.")
        return

    typer.echo(f"Sessions directory: {sessions_dir}")
    typer.echo(f"Current session: {current_session}")
    typer.echo("\nAvailable sessions:")
    typer.echo("-" * 50)

    for db_file in sorted(db_files):
        session_id = db_file.stem
        marker = " (current)" if session_id == current_session else ""
        typer.echo(f"  {session_id}{marker}")


@session_app.command("info")
def session_info(
    session_id: str = typer.Argument(None, help="Session ID (defaults to current)"),
):
    """Show information about a session."""
    target_session = session_id or get_session_id()
    db_path = get_session_db_path(target_session)

    if not db_path.exists():
        typer.echo(f"Session '{target_session}' does not exist.", err=True)
        raise typer.Exit(1)

    db_manager = get_db_manager(target_session)
    db_manager.init_database()

    session_info_obj = db_manager.get_session_info()

    if session_info_obj is None:
        typer.echo("Session info not found.", err=True)
        raise typer.Exit(1)

    typer.echo(f"Session ID: {session_info_obj.session_id}")
    typer.echo(f"Name: {session_info_obj.name}")
    typer.echo(f"Created: {session_info_obj.created_at}")
    typer.echo(f"Database: {db_path}")


@session_app.command("create")
def create_session(
    session_id: str = typer.Argument(..., help="Session ID to create"),
    json_input: str = typer.Option(
        ..., "--json", "-j", help="JSON payload with session fields"
    ),
):
    """Create a new session."""
    db_path = get_session_db_path(session_id)

    if db_path.exists():
        typer.echo(f"Session '{session_id}' already exists.", err=True)
        raise typer.Exit(1)

    try:
        payload = SessionCreate.model_validate_json(json_input)
    except Exception as e:
        typer.echo(f"Invalid JSON: {e}", err=True)
        raise typer.Exit(1)

    # Access fields via payload.name
    # Use payload.name if provided, otherwise default to session_id argument
    name = payload.name if payload.name else session_id

    db_manager = get_db_manager(session_id)
    db_manager.init_database(name=name)

    typer.echo(f"Created session '{session_id}' at {db_path}")


@session_app.command("delete")
def delete_session(
    session_id: str = typer.Argument(..., help="Session ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a session and its database."""
    current_session = get_session_id()
    if session_id == current_session:
        typer.echo("Cannot delete the current session.", err=True)
        raise typer.Exit(1)

    db_path = get_session_db_path(session_id)

    if not db_path.exists():
        typer.echo(f"Session '{session_id}' does not exist.", err=True)
        raise typer.Exit(1)

    if not force:
        typer.echo(f"Warning: This will delete all data in session '{session_id}'.")
        confirm = typer.confirm("Are you sure?")
        if not confirm:
            typer.echo("Cancelled.")
            return

    db_path.unlink()
    typer.echo(f"Deleted session '{session_id}'.")


@session_app.command("path")
def session_path(
    session_id: str = typer.Argument(None, help="Session ID (defaults to current)"),
):
    """Show the database path for a session."""
    target_session = session_id or get_session_id()
    db_path = get_session_db_path(target_session)
    typer.echo(db_path)


@session_app.command("current")
def session_current():
    """Show the current session ID."""
    current = get_session_id()
    typer.echo(current)
