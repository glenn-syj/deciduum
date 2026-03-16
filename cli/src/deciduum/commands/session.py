"""Session management commands."""

from pathlib import Path
from typing import Optional

import typer

from sqlalchemy import create_engine, text, inspect

from deciduum.config import (
    get_session_id,
    get_sessions_dir,
    get_session_db_path,
    get_registry_db_path,
)
from deciduum.database import (
    get_db_manager,
    get_registry_manager,
    needs_migration,
    migrate_sessions,
)
from deciduum.schemas import SessionCreate

session_app = typer.Typer(help="Session management commands.")


def resolve_session(session_id: Optional[str]) -> str:
    """Resolve session ID to a concrete value.

    Args:
        session_id: The session ID to resolve. If None or empty, defaults to
            the current session.

    Returns:
        The resolved session ID string.
    """
    return session_id if session_id else get_session_id()


REQUIRED_TABLES = [
    "session_info",
    "directions",
    "decisions",
    "decision_logs",
    "memos",
    "tasks",
]


def check_tables_exist(engine) -> bool:
    """Check if all required tables exist in the database.

    Args:
        engine: SQLAlchemy engine to inspect.

    Returns:
        True if all required tables exist, False otherwise.
    """
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    required = set(REQUIRED_TABLES)
    return required.issubset(existing_tables)


def validate_session_database(session_id: str) -> tuple[bool, str]:
    """Validate a session database.

    Performs comprehensive validation of the session database:
    1. File exists at expected path
    2. Can create database engine
    3. Can connect to database
    4. Database passes integrity check
    5. All required tables exist

    Args:
        session_id: The session ID to validate.

    Returns:
        Tuple of (is_valid, message) where is_valid indicates whether
        the session is valid and message provides details.
    """
    if not session_id or not isinstance(session_id, str):
        return False, "Invalid session ID: must be a non-empty string"

    try:
        db_path = get_session_db_path(session_id)
    except Exception as e:
        return False, f"Failed to resolve database path: {e}"

    # Check 1: Path is valid and file exists
    if db_path is None:
        return False, "Database path resolved to None"

    if not isinstance(db_path, Path):
        return False, f"Database path is not a Path object: {type(db_path)}"

    if not db_path.exists():
        return False, f"Database file does not exist at {db_path}"

    if not db_path.is_file():
        return False, f"Database path exists but is not a file: {db_path}"

    # Create engine and use single connection for all checks
    try:
        engine = create_engine(f"sqlite:///{db_path}")
    except Exception as e:
        return False, f"Cannot create database engine: {e}"

    # Use single connection for SQLite open check, integrity check, and table check
    try:
        with engine.connect() as conn:
            # Check 2: SQLite can be opened (connection works)
            # This is implicitly verified by the context manager succeeding

            # Check 3: PRAGMA integrity_check
            result = conn.execute(text("PRAGMA integrity_check"))
            integrity_result = result.fetchone()
            if integrity_result and integrity_result[0] != "ok":
                return False, f"Integrity check failed: {integrity_result[0]}"

    except Exception as e:
        return False, f"Cannot open database as SQLite: {e}"

    # Check 4: Required tables exist (can use engine without new connection)
    try:
        if not check_tables_exist(engine):
            inspector = inspect(engine)
            existing = set(inspector.get_table_names())
            missing = set(REQUIRED_TABLES) - existing
            return False, f"Missing required tables: {', '.join(sorted(missing))}"
    except Exception as e:
        return False, f"Failed to check tables: {e}"

    return True, "Validation successful"


@session_app.command("list")
def list_sessions():
    """List all existing sessions.

    Queries the master registry database for all sessions and displays
    them with their creation dates. The current session is marked with
    "(current)". If the master registry doesn't exist or is empty,
    automatically migrates existing session databases.
    """
    sessions_dir = get_sessions_dir()
    current_session = get_session_id()

    # Auto-migration: check if registry needs migration
    if needs_migration():
        migrated = migrate_sessions()
        if migrated > 0:
            typer.echo(f"Migrated {migrated} existing session(s) to registry.")

    # Get registry manager
    registry_manager = get_registry_manager()
    registry_db_path = get_registry_db_path()

    # Try to query master DB first
    if registry_db_path.exists():
        try:
            sessions = registry_manager.list_sessions()

            if sessions:
                typer.echo(f"Sessions directory: {sessions_dir}")
                typer.echo(f"Current session: {current_session}")
                typer.echo("\nAvailable sessions:")
                typer.echo("-" * 50)

                for reg_session in sorted(sessions, key=lambda s: s.session_id):
                    session_id = reg_session.session_id
                    created_at = reg_session.created_at
                    marker = " (current)" if session_id == current_session else ""
                    typer.echo(f"  {session_id} - {created_at}{marker}")
                return
        except Exception:
            # Fall through to filesystem fallback on any error
            pass

    # Fallback: filesystem scan if registry doesn't exist or failed
    if not sessions_dir.exists():
        typer.echo("No sessions found.")
        return

    # Ensure current session exists
    current_db_path = get_session_db_path(current_session)
    if not current_db_path.exists():
        db_manager = get_db_manager(current_session)
        db_manager.init_database()
        typer.echo(f"Initialized new session: {current_session}")

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
    """Show information about a session.

    Displays details about a session including its ID, name, creation
    date, and database file path.

    Args:
        session_id: Session ID to show info for. Defaults to current session.
    """
    target_session = resolve_session(session_id)
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
        None, "--json", "-j", help="JSON payload with session fields (optional)"
    ),
):
    """Create a new session.

    Creates a new session database with the specified session ID.
    The session name can be provided via JSON payload, otherwise
    defaults to the session ID.

    Args:
        session_id: Unique identifier for the new session.
        json_input: Optional JSON payload with session fields (e.g., {"name": "My Session"}).
    """
    # Step 1: Check if session_id exists in master DB
    registry_manager = get_registry_manager()
    existing_in_registry = registry_manager.get_session(session_id)
    if existing_in_registry:
        typer.echo(f"Session '{session_id}' already exists in registry.", err=True)
        raise typer.Exit(1)

    # Step 2: Check if session_id exists in filesystem
    db_path = get_session_db_path(session_id)
    if db_path.exists():
        typer.echo(f"Session '{session_id}' already exists in filesystem.", err=True)
        raise typer.Exit(1)

    # Step 3: Parse JSON payload if provided
    name = session_id
    if json_input:
        try:
            payload = SessionCreate.model_validate_json(json_input)
            if payload.name:
                name = payload.name
        except Exception as e:
            typer.echo(f"Invalid JSON: {e}", err=True)
            raise typer.Exit(1)

    # Step 4 & 5: Insert into master DB and create session DB file (atomic)
    try:
        # Insert into master DB first
        registry_manager.add_session(session_id)

        # Then create session DB file
        db_manager = get_db_manager(session_id)
        db_manager.init_database(name=name)

    except Exception as e:
        # If anything fails, we should ideally rollback
        # Since registry is already committed, we log the error
        typer.echo(f"Failed to create session: {e}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Created session '{session_id}' at {db_path}")


@session_app.command("delete")
def delete_session(
    session_id: str = typer.Argument(..., help="Session ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a session and its database.

    Permanently deletes a session and all its data. The current
    session cannot be deleted.

    Args:
        session_id: Session ID to delete.
        force: Skip confirmation prompt if True.
    """
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
    """Show the database path for a session.

    Prints the absolute path to the session's database file.

    Args:
        session_id: Session ID to show path for. Defaults to current session.
    """
    target_session = resolve_session(session_id)
    db_path = get_session_db_path(target_session)
    typer.echo(db_path)


@session_app.command("current")
def session_current():
    """Show the current session ID.

    Prints the ID of the currently active session.
    """
    current = get_session_id()
    typer.echo(current)


@session_app.command("validate")
def validate_session(
    session_id: str = typer.Argument(..., help="Session ID to validate"),
):
    """Validate a session database.

    Performs comprehensive validation of a session database to check
    for corruption or missing components. Validates file existence,
    database integrity, and required tables.

    Args:
        session_id: Session ID to validate.
    """
    is_valid, message = validate_session_database(session_id)

    if is_valid:
        typer.echo(f"Session '{session_id}' is valid.")
        raise typer.Exit(0)
    else:
        typer.echo(f"Error: Session '{session_id}' is corrupted or invalid.", err=True)
        typer.echo(f"Details: {message}", err=True)
        raise typer.Exit(1)


@session_app.command("migrate")
def migrate():
    """Migrate existing session databases to the master registry.

    Scans the filesystem for session databases in the sessions directory
    and adds any missing sessions to the master registry. This command
    is idempotent - running it multiple times is safe.

    Use this command to force a re-scan and sync of sessions from the
    filesystem to the registry database.
    """
    sessions_dir = get_sessions_dir()

    if not sessions_dir.exists():
        typer.echo("No sessions to migrate (sessions directory does not exist).")
        return

    # Ensure registry is initialized
    registry_manager = get_registry_manager()
    registry_manager.init_database()

    # Get count of sessions in registry before migration
    existing_sessions = registry_manager.list_sessions()
    existing_ids = {s.session_id for s in existing_sessions}

    # Scan filesystem for session databases
    db_files = list(sessions_dir.glob("*.db"))

    if not db_files:
        typer.echo("No sessions to migrate.")
        return

    migrated_count = 0

    for db_file in db_files:
        session_id = db_file.stem

        # Skip if already in registry (idempotent)
        if session_id in existing_ids:
            continue

        # Add to registry
        try:
            registry_manager.add_session(session_id)
            migrated_count += 1
            existing_ids.add(session_id)  # Track to avoid duplicates in same run
        except Exception as e:
            # Log but continue - migration should be resilient
            typer.echo(f"Warning: Failed to migrate session '{session_id}': {e}")

    if migrated_count > 0:
        typer.echo(f"Migrated {migrated_count} session(s).")
    else:
        typer.echo("No sessions to migrate.")
