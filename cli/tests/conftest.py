"""Shared pytest fixtures for Deciduum CLI tests."""

import os
import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from deciduum.database import reset_db_manager


def reset_all_state(
    config_module,
    db_module,
    main_module,
    original_config_get_sessions_dir,
    original_config_get_session_db_path,
    original_config_get_session_id,
    original_config_get_server_config,
    original_config_config_file,
    original_db_get_sessions_dir,
    original_db_get_session_db_path,
    original_db_get_server_config,
    original_main_get_active_session,
):
    """Reset all test state by restoring original functions and clearing global state."""
    # Restore config module
    config_module.get_sessions_dir = original_config_get_sessions_dir
    config_module.get_session_db_path = original_config_get_session_db_path
    config_module.get_session_id = original_config_get_session_id
    config_module.get_server_config = original_config_get_server_config
    config_module.CONFIG_FILE = original_config_config_file

    # Restore database module
    db_module.get_sessions_dir = original_db_get_sessions_dir
    db_module.get_session_db_path = original_db_get_session_db_path
    db_module.get_server_config = original_db_get_server_config

    # Restore main module
    main_module.get_active_session = original_main_get_active_session

    # Reset global database manager
    reset_db_manager()


@pytest.fixture
def runner():
    """Provide a CliRunner instance for testing."""
    return CliRunner()


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch, tmp_path):
    """Create an isolated environment with temp directories.

    This fixture:
    - Creates a temporary directory structure for the test
    - Patches config module to use temp directories
    - Patches get_active_session to not auto-initialize the database
    - Ensures tests don't touch the real ~/.deciduum directory
    - Uses unique session ID based on tmp_path for parallel test support

    This is an autouse fixture so it runs for every test.
    """
    # Generate a unique session ID from tmp_path for parallel test support
    unique_session_id = f"test-{tmp_path.name}-{uuid.uuid4().hex[:8]}"

    # Create a temporary directory structure
    temp_dir = tmp_path / "deciduum_test"
    temp_dir.mkdir()
    temp_sessions = temp_dir / "sessions"
    temp_sessions.mkdir(parents=True)
    temp_config = temp_dir / "config.json"
    temp_config.touch()

    # Set environment variables for isolated test environment
    monkeypatch.setenv("DECIDUUM_SESSION", unique_session_id)
    monkeypatch.setenv("DECIDUUM_SESSIONS_DIR", str(temp_sessions))

    # Import the config module and store original functions for cleanup
    import deciduum.config as config_module

    # Store original functions for cleanup
    original_config_get_sessions_dir = config_module.get_sessions_dir
    original_config_get_session_db_path = config_module.get_session_db_path
    original_config_get_session_id = config_module.get_session_id
    original_config_get_server_config = config_module.get_server_config
    original_config_config_file = config_module.CONFIG_FILE

    # Import the database module and store original functions for cleanup
    import deciduum.database as db_module

    original_db_get_sessions_dir = db_module.get_sessions_dir
    original_db_get_session_db_path = db_module.get_session_db_path
    original_db_get_server_config = db_module.get_server_config

    # Import the main module and store original functions for cleanup
    import deciduum.__main__ as main_module

    original_main_get_active_session = main_module.get_active_session

    # Create mock functions
    def mock_get_sessions_dir():
        temp_sessions.mkdir(parents=True, exist_ok=True)
        return temp_sessions

    def mock_get_session_db_path(session_id):
        sessions_dir = mock_get_sessions_dir()
        return sessions_dir / f"{session_id}.db"

    def mock_get_session_id():
        return unique_session_id

    # Patch the functions using setattr on the module
    config_module.get_sessions_dir = mock_get_sessions_dir
    config_module.get_session_db_path = mock_get_session_db_path
    config_module.get_session_id = mock_get_session_id
    config_module.CONFIG_FILE = temp_config

    # Patch get_server_config to return no server (local mode)
    def mock_get_server_config():
        return MagicMock(server_url=None)

    config_module.get_server_config = mock_get_server_config

    # Clear settings.sessions_dir to force get_sessions_dir() to use get_data_dir()
    # which checks the DECIDUUM_SESSIONS_DIR environment variable
    config_module.settings.sessions_dir = None

    # Also need to patch the database module's reference to config functions
    import deciduum.database as db_module

    db_module.get_sessions_dir = mock_get_sessions_dir
    db_module.get_session_db_path = mock_get_session_db_path
    db_module.get_server_config = mock_get_server_config

    # Patch get_active_session in __main__ to properly initialize the database
    # in the temp directory instead of the real directory
    import deciduum.__main__ as main_module
    import deciduum.database as db_module

    def mock_get_active_session():
        """Mock that initializes the database in the temp directory."""
        session_id = config_module.get_session_id()
        db_path = config_module.get_session_db_path(session_id)

        # Ensure sessions directory exists
        config_module.get_sessions_dir()

        # Initialize database if it doesn't exist
        if not db_path.exists():
            # Use typer.echo to print the message (like the real function)
            import typer

            typer.echo(f"Initializing new session: {session_id}")

        db_manager = db_module.get_db_manager(session_id)
        db_manager.init_database()

        # Set environment variable for child processes
        os.environ["DECIDUUM_SESSION"] = session_id

        return session_id

    main_module.get_active_session = mock_get_active_session

    yield {
        "temp_dir": temp_dir,
        "temp_sessions": temp_sessions,
        "temp_config": temp_config,
    }

    # Cleanup: restore original functions and reset state
    reset_all_state(
        config_module,
        db_module,
        main_module,
        original_config_get_sessions_dir,
        original_config_get_session_db_path,
        original_config_get_session_id,
        original_config_get_server_config,
        original_config_config_file,
        original_db_get_sessions_dir,
        original_db_get_session_db_path,
        original_db_get_server_config,
        original_main_get_active_session,
    )


@pytest.fixture
def cli_with_data(runner, isolated_env):
    """Provide a CLI runner with pre-populated test data.

    Creates:
    - A direction: "Test Direction"
    - A decision: "Test Decision" linked to the direction
    - Returns a dict with the created IDs
    """
    from deciduum.__main__ import app

    # Get the unique session ID from the environment (set by isolated_env)
    session_id = os.environ.get("DECIDUUM_SESSION")

    # Create a direction
    result = runner.invoke(
        app,
        [
            "directions",
            "add",
            "--title",
            "Test Direction",
        ],
        env={"DECIDUUM_SESSION": session_id},
    )

    # Extract direction ID from output
    direction_id = None
    if "Created direction:" in result.stdout:
        for line in result.stdout.split("\n"):
            if "Created direction:" in line:
                direction_id = line.split("Created direction:")[1].strip()
                break

    # Create a decision with direction
    result = runner.invoke(
        app,
        [
            "decisions",
            "add",
            "--title",
            "Test Decision",
            "--direction",
            direction_id,
        ],
        env={"DECIDUUM_SESSION": session_id},
    )

    # Extract decision ID from output
    decision_id = None
    if "Created decision:" in result.stdout:
        for line in result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

    return {
        "direction_id": direction_id,
        "decision_id": decision_id,
    }
