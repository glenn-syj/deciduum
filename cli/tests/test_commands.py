"""Scenario-based tests for Deciduum CLI commands."""

import os
import re

import pytest
from typer.testing import CliRunner

from deciduum.__main__ import app


runner = CliRunner()


class TestSessionCommands:
    """Tests for session management commands."""

    def test_session_list_empty(self, runner, isolated_env):
        """Test listing sessions when none exist."""
        result = runner.invoke(
            app,
            ["session", "list"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "No sessions found" in result.stdout

    def test_session_create(self, runner, isolated_env):
        """Test creating a new session."""
        result = runner.invoke(
            app,
            ["session", "create", "test-session"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Created session" in result.stdout
        assert "test-session" in result.stdout

    def test_session_create_duplicate(self, runner, isolated_env):
        """Test creating a duplicate session fails."""
        # First create
        runner.invoke(
            app,
            ["session", "create", "test-session"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        # Try to create again
        result = runner.invoke(
            app,
            ["session", "create", "test-session"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "already exists" in result.stderr

    def test_session_info(self, runner, isolated_env):
        """Test showing session info."""
        # First create a session
        runner.invoke(
            app,
            ["session", "create", "test-session"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        # Show info
        result = runner.invoke(
            app,
            ["session", "info", "test-session"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Session ID:" in result.stdout
        assert "test-session" in result.stdout

    def test_session_info_nonexistent(self, runner, isolated_env):
        """Test showing info for non-existent session fails."""
        result = runner.invoke(
            app,
            ["session", "info", "nonexistent"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "does not exist" in result.stderr

    def test_session_path(self, runner, isolated_env):
        """Test showing database path."""
        result = runner.invoke(
            app,
            ["session", "path"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        # Extract the actual path from stdout and verify it
        path = result.stdout.strip()
        assert path.endswith(".db")
        assert str(isolated_env["temp_sessions"]) in path


class TestDirectionCommands:
    """Tests for direction management commands."""

    def test_directions_add(self, runner, isolated_env):
        """Test adding a new direction."""
        result = runner.invoke(
            app,
            ["directions", "add", "--title", "Career Growth"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Created direction:" in result.stdout

    def test_directions_list_empty(self, runner, isolated_env):
        """Test listing directions when none exist."""
        result = runner.invoke(
            app,
            ["directions", "list"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "No directions found" in result.stdout

    def test_directions_list_with_data(self, runner, isolated_env):
        """Test listing directions with data."""
        # Add a direction first
        runner.invoke(
            app,
            ["directions", "add", "--title", "Career Growth"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        # List directions
        result = runner.invoke(
            app,
            ["directions", "list"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Career Growth" in result.stdout

    def test_directions_show(self, runner, isolated_env):
        """Test showing direction details."""
        # Add a direction first
        add_result = runner.invoke(
            app,
            ["directions", "add", "--title", "Career Growth"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        # Extract direction ID
        direction_id = None
        for line in add_result.stdout.split("\n"):
            if "Created direction:" in line:
                direction_id = line.split("Created direction:")[1].strip()
                break

        # Show direction
        result = runner.invoke(
            app,
            ["directions", "show", direction_id],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Career Growth" in result.stdout

    def test_directions_show_invalid_id(self, runner, isolated_env):
        """Test showing direction with invalid ID fails."""
        result = runner.invoke(
            app,
            ["directions", "show", "invalid-id"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr

    def test_directions_delete(self, runner, isolated_env):
        """Test soft deleting a direction."""
        # Add a direction first
        add_result = runner.invoke(
            app,
            ["directions", "add", "--title", "To Delete"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        # Extract direction ID
        direction_id = None
        for line in add_result.stdout.split("\n"):
            if "Created direction:" in line:
                direction_id = line.split("Created direction:")[1].strip()
                break

        # Delete direction with --force
        result = runner.invoke(
            app,
            ["directions", "delete", direction_id, "--force"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Deleted direction" in result.stdout

    def test_directions_delete_invalid_id(self, runner, isolated_env):
        """Test deleting direction with invalid ID fails."""
        result = runner.invoke(
            app,
            ["directions", "delete", "invalid-id", "--force"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr


class TestDecisionCommands:
    """Tests for decision management commands."""

    def test_decisions_add(self, runner, isolated_env):
        """Test adding a new decision without direction."""
        result = runner.invoke(
            app,
            ["decisions", "add", "--title", "Learn Python"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Created decision:" in result.stdout

    def test_decisions_add_with_direction(self, runner, isolated_env):
        """Test adding a new decision with a direction."""
        # Add a direction first
        dir_result = runner.invoke(
            app,
            ["directions", "add", "--title", "Career"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        direction_id = None
        for line in dir_result.stdout.split("\n"):
            if "Created direction:" in line:
                direction_id = line.split("Created direction:")[1].strip()
                break

        # Add decision with direction
        result = runner.invoke(
            app,
            [
                "decisions",
                "add",
                "--title",
                "Learn Python",
                "--direction",
                direction_id,
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Created decision:" in result.stdout

    def test_decisions_add_with_invalid_direction(self, runner, isolated_env):
        """Test adding decision with invalid direction fails."""
        result = runner.invoke(
            app,
            [
                "decisions",
                "add",
                "--title",
                "Learn Python",
                "--direction",
                "invalid-id",
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr

    def test_decisions_list_empty(self, runner, isolated_env):
        """Test listing decisions when none exist."""
        result = runner.invoke(
            app,
            ["decisions", "list"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "No decisions found" in result.stdout

    def test_decisions_list_with_data(self, runner, isolated_env):
        """Test listing decisions with data."""
        # Add a decision
        runner.invoke(
            app,
            ["decisions", "add", "--title", "Learn Python"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        # List decisions
        result = runner.invoke(
            app,
            ["decisions", "list"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Learn Python" in result.stdout

    def test_decisions_list_with_status_filter(self, runner, isolated_env):
        """Test listing decisions with status filter."""
        # Add a completed decision
        runner.invoke(
            app,
            [
                "decisions",
                "add",
                "--title",
                "Completed Decision",
                "--status",
                "completed",
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        # Add an ongoing decision
        runner.invoke(
            app,
            ["decisions", "add", "--title", "Ongoing Decision", "--status", "ongoing"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        # Filter by completed
        result = runner.invoke(
            app,
            ["decisions", "list", "--status", "completed"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Completed Decision" in result.stdout
        assert "Ongoing Decision" not in result.stdout

    def test_decisions_show(self, runner, isolated_env):
        """Test showing decision details."""
        # Add a decision
        add_result = runner.invoke(
            app,
            ["decisions", "add", "--title", "Learn Python"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        # Extract decision ID
        decision_id = None
        for line in add_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        # Show decision
        result = runner.invoke(
            app,
            ["decisions", "show", decision_id],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Learn Python" in result.stdout

    def test_decisions_show_invalid_id(self, runner, isolated_env):
        """Test showing decision with invalid ID fails."""
        result = runner.invoke(
            app,
            ["decisions", "show", "invalid-id"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr

    def test_decisions_update_title(self, runner, isolated_env):
        """Test updating decision title."""
        # Add a decision
        add_result = runner.invoke(
            app,
            ["decisions", "add", "--title", "Old Title"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        # Extract decision ID
        decision_id = None
        for line in add_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        # Update title
        result = runner.invoke(
            app,
            ["decisions", "update", decision_id, "--title", "New Title"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Updated decision" in result.stdout

    def test_decisions_update_status(self, runner, isolated_env):
        """Test updating decision status."""
        # Add a decision
        add_result = runner.invoke(
            app,
            ["decisions", "add", "--title", "My Decision"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        # Extract decision ID
        decision_id = None
        for line in add_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        # Update status
        result = runner.invoke(
            app,
            ["decisions", "update", decision_id, "--status", "completed"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Updated decision" in result.stdout

    def test_decisions_update_invalid_id(self, runner, isolated_env):
        """Test updating decision with invalid ID fails."""
        result = runner.invoke(
            app,
            ["decisions", "update", "invalid-id", "--title", "New Title"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr

    def test_decisions_delete(self, runner, isolated_env):
        """Test soft deleting a decision."""
        # Add a decision
        add_result = runner.invoke(
            app,
            ["decisions", "add", "--title", "To Delete"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        # Extract decision ID
        decision_id = None
        for line in add_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        # Delete decision with --force
        result = runner.invoke(
            app,
            ["decisions", "delete", decision_id, "--force"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Deleted decision" in result.stdout

    def test_decisions_delete_invalid_id(self, runner, isolated_env):
        """Test deleting decision with invalid ID fails."""
        result = runner.invoke(
            app,
            ["decisions", "delete", "invalid-id", "--force"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr


class TestTaskCommands:
    """Tests for task management commands."""

    def test_tasks_add(self, runner, isolated_env):
        """Test adding a new task."""
        # Add a decision first
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--title", "Learn Python"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        # Add task
        result = runner.invoke(
            app,
            ["tasks", "add", "--title", "Practice coding", "--decision", decision_id],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Created task:" in result.stdout

    def test_tasks_add_without_decision(self, runner, isolated_env):
        """Test adding task without decision fails."""
        result = runner.invoke(
            app,
            ["tasks", "add", "--title", "Practice coding"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 2  # Typer error for missing required option

    def test_tasks_add_with_invalid_decision(self, runner, isolated_env):
        """Test adding task with invalid decision fails."""
        result = runner.invoke(
            app,
            ["tasks", "add", "--title", "Practice coding", "--decision", "invalid-id"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr

    def test_tasks_list_empty(self, runner, isolated_env):
        """Test listing tasks when none exist."""
        result = runner.invoke(
            app,
            ["tasks", "list"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "No tasks found" in result.stdout

    def test_tasks_list_with_data(self, runner, isolated_env):
        """Test listing tasks with data."""
        # Add a decision and task
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--title", "Learn Python"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        runner.invoke(
            app,
            ["tasks", "add", "--title", "Practice coding", "--decision", decision_id],
            env={"DECIDUUM_SESSION": "test-session"},
        )

        # List tasks
        result = runner.invoke(
            app,
            ["tasks", "list"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Practice coding" in result.stdout

    def test_tasks_show(self, runner, isolated_env):
        """Test showing task details."""
        # Add a decision and task
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--title", "Learn Python"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        task_result = runner.invoke(
            app,
            ["tasks", "add", "--title", "Practice coding", "--decision", decision_id],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        task_id = None
        for line in task_result.stdout.split("\n"):
            if "Created task:" in line:
                task_id = line.split("Created task:")[1].strip()
                break

        # Show task
        result = runner.invoke(
            app,
            ["tasks", "show", task_id],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Practice coding" in result.stdout

    def test_tasks_show_invalid_id(self, runner, isolated_env):
        """Test showing task with invalid ID fails."""
        result = runner.invoke(
            app,
            ["tasks", "show", "invalid-id"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr

    def test_tasks_complete(self, runner, isolated_env):
        """Test marking task as complete."""
        # Add a decision and task
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--title", "Learn Python"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        task_result = runner.invoke(
            app,
            ["tasks", "add", "--title", "Practice coding", "--decision", decision_id],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        task_id = None
        for line in task_result.stdout.split("\n"):
            if "Created task:" in line:
                task_id = line.split("Created task:")[1].strip()
                break

        # Complete task
        result = runner.invoke(
            app,
            ["tasks", "complete", task_id],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Completed task" in result.stdout

    def test_tasks_complete_invalid_id(self, runner, isolated_env):
        """Test completing task with invalid ID fails."""
        result = runner.invoke(
            app,
            ["tasks", "complete", "invalid-id"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr

    def test_tasks_delete(self, runner, isolated_env):
        """Test soft deleting a task."""
        # Add a decision and task
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--title", "Learn Python"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        task_result = runner.invoke(
            app,
            ["tasks", "add", "--title", "To Delete", "--decision", decision_id],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        task_id = None
        for line in task_result.stdout.split("\n"):
            if "Created task:" in line:
                task_id = line.split("Created task:")[1].strip()
                break

        # Delete task with --force
        result = runner.invoke(
            app,
            ["tasks", "delete", task_id, "--force"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Deleted task" in result.stdout

    def test_tasks_delete_invalid_id(self, runner, isolated_env):
        """Test deleting task with invalid ID fails."""
        result = runner.invoke(
            app,
            ["tasks", "delete", "invalid-id", "--force"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr


class TestErrorCases:
    """Tests for error cases and edge conditions."""

    def test_missing_required_argument(self, runner, isolated_env):
        """Test missing required argument shows proper error."""
        # Try to add direction without title
        result = runner.invoke(
            app,
            ["directions", "add"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        # Should fail with usage error
        assert result.exit_code != 0

    def test_invalid_command(self, runner, isolated_env):
        """Test invalid command shows proper error."""
        result = runner.invoke(
            app,
            ["invalid", "command"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code != 0

    def test_delete_confirmation_cancelled(self, runner, isolated_env):
        """Test delete confirmation when cancelled."""
        # Add a direction
        add_result = runner.invoke(
            app,
            ["directions", "add", "--title", "Test Direction"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        direction_id = None
        for line in add_result.stdout.split("\n"):
            if "Created direction:" in line:
                direction_id = line.split("Created direction:")[1].strip()
                break

        # Try to delete without --force (will trigger confirmation)
        # We need to pass 'n' to the confirmation prompt
        result = runner.invoke(
            app,
            ["directions", "delete", direction_id],
            input="n\n",
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert "Cancelled" in result.stdout
