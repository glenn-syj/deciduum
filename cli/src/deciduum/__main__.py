"""Deciduum CLI entry point."""

import os
from typing import Optional

import typer

from deciduum.config import get_session_id, get_sessions_dir, get_session_db_path
from deciduum.database import get_db_manager
from deciduum.commands.session import session_app
from deciduum.commands.config import config_app
from deciduum.commands.today import today_command
from deciduum.commands.decisions import decisions_app
from deciduum.commands.memos import memos_app
from deciduum.commands.directions import directions_app
from deciduum.commands.tasks import tasks_app
from deciduum.commands.logs import logs_app, journey_app
from deciduum.commands.schema import schema_app


app = typer.Typer(
    name="deciduum",
    help="Deciduum - Decision tracking CLI with session-based multi-database architecture.",
    add_completion=False,
)

# Register subcommands
app.add_typer(session_app, name="session")
app.add_typer(config_app, name="config")
app.add_typer(decisions_app, name="decisions")
app.add_typer(memos_app, name="memos")
app.add_typer(directions_app, name="directions")
app.add_typer(tasks_app, name="tasks")
app.add_typer(logs_app, name="logs")
app.add_typer(journey_app, name="journey")
app.add_typer(schema_app, name="schema")
app.command("today")(today_command)


def get_active_session() -> str:
    """Get the active session ID, initializing the database if needed."""
    session_id = get_session_id()
    db_path = get_session_db_path(session_id)

    # Ensure sessions directory exists
    get_sessions_dir()

    # Initialize database if it doesn't exist
    if not db_path.exists():
        typer.echo(f"Initializing new session: {session_id}")

    db_manager = get_db_manager(session_id)
    db_manager.init_database()

    # Set environment variable for child processes
    os.environ["DECIDUUM_SESSION"] = session_id

    return session_id


@app.callback()
def main(
    ctx: typer.Context,
    session: Optional[str] = typer.Option(
        None,
        "--session",
        "-s",
        help="Session ID (default: from $DECIDUUM_SESSION or 'default')",
    ),
):
    """Deciduum CLI - Decision tracking application."""
    # Handle session option
    if session:
        os.environ["DECIDUUM_SESSION"] = session

    # Get the command being invoked
    command_name = ctx.invoked_subcommand

    # Skip session initialization for session and config management commands
    # These commands handle their own session initialization
    if command_name not in ("session", "config"):
        get_active_session()


if __name__ == "__main__":
    app()
