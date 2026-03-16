"""Scenario-based tests for Deciduum CLI commands."""

import json
import os
import re
from datetime import date, timedelta

import pytest
from typer.testing import CliRunner

from deciduum.__main__ import app


runner = CliRunner()


class TestSessionCommands:
    """Tests for session management commands."""

    def test_session_list_with_current_session(self, runner):
        """Test that session list shows the current (auto-created) session."""
        result = runner.invoke(
            app,
            ["session", "list"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        # CLI auto-creates a session on first run, so we should see it listed
        assert "test-session" in result.stdout

    def test_session_create(self, runner):
        """Test creating a new session."""
        result = runner.invoke(
            app,
            ["session", "create", "test-session", "--json", "{}"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Created session" in result.stdout
        assert "test-session" in result.stdout

    def test_session_create_duplicate(self, runner):
        """Test creating a duplicate session fails."""
        # First create
        runner.invoke(
            app,
            ["session", "create", "test-session", "--json", "{}"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        # Try to create again
        result = runner.invoke(
            app,
            ["session", "create", "test-session", "--json", "{}"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "already exists" in result.stderr

    def test_session_info(self, runner):
        """Test showing session info."""
        # First create a session
        runner.invoke(
            app,
            ["session", "create", "test-session", "--json", "{}"],
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

    def test_session_info_nonexistent(self, runner):
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

    def test_session_delete_confirmation_cancelled(self, runner):
        """Test deleting a session with cancelled confirmation."""
        # First create a session to delete (different from current)
        runner.invoke(
            app,
            ["session", "create", "delete-test", "--json", "{}"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        # Try to delete without --force (will trigger confirmation)
        result = runner.invoke(
            app,
            ["session", "delete", "delete-test"],
            input="n\n",
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Cancelled" in result.stdout

    def test_session_delete_with_force(self, runner):
        """Test deleting a session with --force flag."""
        # First create a session to delete (different from current)
        runner.invoke(
            app,
            ["session", "create", "delete-test", "--json", "{}"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        # Delete with --force
        result = runner.invoke(
            app,
            ["session", "delete", "delete-test", "--force"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Deleted session" in result.stdout

    def test_session_delete_current_session_fails(self, runner):
        """Test deleting the current session fails."""
        # The current session is set via env={"DECIDUUM_SESSION": "test-session"}
        result = runner.invoke(
            app,
            ["session", "delete", "test-session", "--force"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "Cannot delete the current session" in result.stderr

    def test_session_delete_nonexistent_fails(self, runner):
        """Test deleting a non-existent session fails."""
        result = runner.invoke(
            app,
            ["session", "delete", "nonexistent", "--force"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "does not exist" in result.stderr


class TestDirectionCommands:
    """Tests for direction management commands."""

    def test_directions_add(self, runner):
        """Test adding a new direction."""
        result = runner.invoke(
            app,
            ["directions", "add", "--json", '{"title": "Career Growth"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Created direction:" in result.stdout

    def test_directions_list_empty(self, runner):
        """Test listing directions when none exist."""
        result = runner.invoke(
            app,
            ["directions", "list"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        # In non-interactive mode (no TTY), output defaults to JSON which returns []
        # The output may include "Initializing new session" message from the test fixture
        assert result.stdout.strip().endswith("[]")

    def test_directions_list_with_data(self, runner):
        """Test listing directions with data."""
        # Add a direction first
        runner.invoke(
            app,
            ["directions", "add", "--json", '{"title": "Career Growth"}'],
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

    def test_directions_show(self, runner):
        """Test showing direction details."""
        # Add a direction first
        add_result = runner.invoke(
            app,
            ["directions", "add", "--json", '{"title": "Career Growth"}'],
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

    def test_directions_show_invalid_id(self, runner):
        """Test showing direction with invalid ID fails."""
        result = runner.invoke(
            app,
            ["directions", "show", "invalid-id"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr

    def test_directions_delete(self, runner):
        """Test soft deleting a direction."""
        # Add a direction first
        add_result = runner.invoke(
            app,
            ["directions", "add", "--json", '{"title": "To Delete"}'],
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

    def test_directions_delete_invalid_id(self, runner):
        """Test deleting direction with invalid ID fails."""
        result = runner.invoke(
            app,
            ["directions", "delete", "invalid-id", "--force"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr

    def test_directions_update_title(self, runner):
        """Test updating direction title."""
        # Add a direction first
        add_result = runner.invoke(
            app,
            ["directions", "add", "--json", '{"title": "Old Title"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        # Extract direction ID
        direction_id = None
        for line in add_result.stdout.split("\n"):
            if "Created direction:" in line:
                direction_id = line.split("Created direction:")[1].strip()
                break

        # Update title
        result = runner.invoke(
            app,
            ["directions", "update", direction_id, "--json", '{"title": "New Title"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Updated direction" in result.stdout

    def test_directions_update_with_json(self, runner):
        """Test updating direction with JSON payload."""
        # Add a direction first
        add_result = runner.invoke(
            app,
            ["directions", "add", "--json", '{"title": "Original Title"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        # Extract direction ID
        direction_id = None
        for line in add_result.stdout.split("\n"):
            if "Created direction:" in line:
                direction_id = line.split("Created direction:")[1].strip()
                break

        # Update with JSON payload
        result = runner.invoke(
            app,
            ["directions", "update", direction_id, "--json", '{"title": "JSON Title"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Updated direction" in result.stdout

    def test_directions_update_invalid_id(self, runner):
        """Test updating direction with invalid ID fails."""
        result = runner.invoke(
            app,
            ["directions", "update", "invalid-id", "--json", '{"title": "New Title"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr


class TestDecisionCommands:
    """Tests for decision management commands."""

    def test_decisions_add(self, runner):
        """Test adding a new decision without direction."""
        result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Learn Python"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Created decision:" in result.stdout

    def test_decisions_add_with_direction(self, runner):
        """Test adding a new decision with a direction."""
        # Add a direction first
        dir_result = runner.invoke(
            app,
            ["directions", "add", "--json", '{"title": "Career"}'],
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
                "--json",
                f'{{"title": "Learn Python", "direction_id": "{direction_id}"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Created decision:" in result.stdout

    def test_decisions_add_with_invalid_direction(self, runner):
        """Test adding decision with invalid direction fails."""
        result = runner.invoke(
            app,
            [
                "decisions",
                "add",
                "--json",
                '{"title": "Learn Python", "direction_id": "invalid-id"}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr

    def test_decisions_list_empty(self, runner):
        """Test listing decisions when none exist."""
        result = runner.invoke(
            app,
            ["decisions", "list"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        # In non-interactive mode (no TTY), output defaults to JSON which returns []
        # The output may include "Initializing new session" message from the test fixture
        assert result.stdout.strip().endswith("[]")

    def test_decisions_list_with_data(self, runner):
        """Test listing decisions with data."""
        # Add a decision
        runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Learn Python"}'],
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

    def test_decisions_list_with_status_filter(self, runner):
        """Test listing decisions with status filter."""
        # Add a completed decision
        runner.invoke(
            app,
            [
                "decisions",
                "add",
                "--json",
                '{"title": "Completed Decision", "status": "completed"}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        # Add an ongoing decision
        runner.invoke(
            app,
            [
                "decisions",
                "add",
                "--json",
                '{"title": "Ongoing Decision", "status": "ongoing"}',
            ],
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

    def test_decisions_show(self, runner):
        """Test showing decision details."""
        # Add a decision
        add_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Learn Python"}'],
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

    def test_decisions_show_invalid_id(self, runner):
        """Test showing decision with invalid ID fails."""
        result = runner.invoke(
            app,
            ["decisions", "show", "invalid-id"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr

    def test_decisions_update_title(self, runner):
        """Test updating decision title."""
        # Add a decision
        add_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Old Title"}'],
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
            ["decisions", "update", decision_id, "--json", '{"title": "New Title"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Updated decision" in result.stdout

    def test_decisions_update_status(self, runner):
        """Test updating decision status."""
        # Add a decision
        add_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "My Decision"}'],
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
            ["decisions", "update", decision_id, "--json", '{"status": "completed"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Updated decision" in result.stdout

    def test_decisions_update_invalid_id(self, runner):
        """Test updating decision with invalid ID fails."""
        result = runner.invoke(
            app,
            ["decisions", "update", "invalid-id", "--json", '{"title": "New Title"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr

    def test_decisions_delete(self, runner):
        """Test soft deleting a decision."""
        # Add a decision
        add_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "To Delete"}'],
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

    def test_decisions_delete_invalid_id(self, runner):
        """Test deleting decision with invalid ID fails."""
        result = runner.invoke(
            app,
            ["decisions", "delete", "invalid-id", "--force"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr

    def test_decisions_next_with_overdue(self, runner):
        """Test showing next decision when overdue exists."""
        # Add a decision
        add_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Overdue Decision"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        # Extract decision ID
        decision_id = None
        for line in add_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        # Update with past review date (overdue)
        past_date = (date.today() - timedelta(days=5)).strftime("%Y-%m-%d")
        runner.invoke(
            app,
            [
                "decisions",
                "update",
                decision_id,
                "--json",
                f'{{"review_at": "{past_date}"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )

        # Get next decision (default output is JSON in non-TTY test environment)
        result = runner.invoke(
            app,
            ["decisions", "next"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        # In non-TTY test environment, output defaults to JSON
        output_data = json.loads(result.stdout)
        assert output_data is not None
        assert output_data["title"] == "Overdue Decision"
        # The review_at date should be in the past (overdue)
        review_at = date.fromisoformat(output_data["review_at"])
        assert review_at < date.today()

    def test_decisions_next_none_pending(self, runner):
        """Test showing next decision when none pending."""
        # Get next decision with no decisions created
        # (default output is JSON in non-TTY test environment)
        result = runner.invoke(
            app,
            ["decisions", "next"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        # In non-TTY test environment, output defaults to JSON (null)
        # The output may contain "Initializing new session" message, so check for 'null' in output
        assert "null" in result.stdout

    def test_decisions_next_json_format(self, runner):
        """Test JSON output format for decisions next."""
        # Add a decision
        add_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "JSON Test Decision"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        # Extract decision ID
        decision_id = None
        for line in add_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        # Update with past review date (overdue)
        past_date = (date.today() - timedelta(days=3)).strftime("%Y-%m-%d")
        runner.invoke(
            app,
            [
                "decisions",
                "update",
                decision_id,
                "--json",
                f'{{"review_at": "{past_date}"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )

        # Get next decision with JSON format
        result = runner.invoke(
            app,
            ["decisions", "next", "--format", "json"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        # Verify valid JSON output
        output_data = json.loads(result.stdout)
        assert output_data is not None
        assert "id" in output_data
        assert output_data["title"] == "JSON Test Decision"

    def test_decisions_next_quiet_format(self, runner):
        """Test quiet output format for decisions next."""
        # Add a decision
        add_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Quiet Test Decision"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        # Extract decision ID
        decision_id = None
        for line in add_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        # Update with past review date (overdue)
        past_date = (date.today() - timedelta(days=2)).strftime("%Y-%m-%d")
        runner.invoke(
            app,
            [
                "decisions",
                "update",
                decision_id,
                "--json",
                f'{{"review_at": "{past_date}"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )

        # Get next decision with quiet format
        result = runner.invoke(
            app,
            ["decisions", "next", "--format", "quiet"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        # Verify just the ID is returned (no extra text)
        output = result.stdout.strip()
        # The output should be just the decision ID (a UUID-like string)
        assert len(output) > 0
        # Should not contain any of these phrases that appear in normal output
        assert "Next decision to review" not in output
        assert "Title:" not in output
        assert "ID:" not in output

    def test_decisions_pending_empty(self, runner):
        """Test listing pending decisions when none exist."""
        result = runner.invoke(
            app,
            ["decisions", "pending"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        # When no pending decisions, output is empty JSON array (after initialization message)
        assert result.stdout.strip().endswith("[]")

    def test_decisions_pending_list_all(self, runner):
        """Test listing all pending decisions with review dates."""
        from datetime import date, timedelta

        today = date.today()
        # Create decision first
        add_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Future Review Decision"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        # Extract decision ID
        decision_id = None
        for line in add_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        # Update with review date in the future
        future_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")
        runner.invoke(
            app,
            [
                "decisions",
                "update",
                decision_id,
                "--json",
                f'{{"review_at": "{future_date}"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )

        # List pending decisions
        result = runner.invoke(
            app,
            ["decisions", "pending"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Future Review Decision" in result.stdout

    def test_decisions_pending_overdue_only(self, runner):
        """Test filtering overdue decisions only."""
        from datetime import date, timedelta

        today = date.today()
        # Create overdue decision - first add, then update with past review date
        add_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Overdue Decision"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id_1 = None
        for line in add_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id_1 = line.split("Created decision:")[1].strip()
                break

        overdue_date = (today - timedelta(days=10)).strftime("%Y-%m-%d")
        runner.invoke(
            app,
            [
                "decisions",
                "update",
                decision_id_1,
                "--json",
                f'{{"review_at": "{overdue_date}"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )

        # Create future decision - first add, then update with future review date
        add_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Future Decision"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id_2 = None
        for line in add_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id_2 = line.split("Created decision:")[1].strip()
                break

        future_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")
        runner.invoke(
            app,
            [
                "decisions",
                "update",
                decision_id_2,
                "--json",
                f'{{"review_at": "{future_date}"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )

        # List only overdue
        result = runner.invoke(
            app,
            ["decisions", "pending", "--overdue"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Overdue Decision" in result.stdout
        assert "Future Decision" not in result.stdout

    def test_decisions_pending_due_soon_only(self, runner):
        """Test filtering decisions due within 7 days."""
        from datetime import date, timedelta

        today = date.today()
        # Create due soon decision - first add, then update with review date within 7 days
        add_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Due Soon Decision"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id_1 = None
        for line in add_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id_1 = line.split("Created decision:")[1].strip()
                break

        due_soon_date = (today + timedelta(days=5)).strftime("%Y-%m-%d")
        runner.invoke(
            app,
            [
                "decisions",
                "update",
                decision_id_1,
                "--json",
                f'{{"review_at": "{due_soon_date}"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )

        # Create far future decision - first add, then update with future review date
        add_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Future Decision"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id_2 = None
        for line in add_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id_2 = line.split("Created decision:")[1].strip()
                break

        future_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")
        runner.invoke(
            app,
            [
                "decisions",
                "update",
                decision_id_2,
                "--json",
                f'{{"review_at": "{future_date}"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )

        # List only due soon
        result = runner.invoke(
            app,
            ["decisions", "pending", "--due-soon"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Due Soon Decision" in result.stdout
        assert "Future Decision" not in result.stdout

    def test_decisions_pending_json_format(self, runner):
        """Test JSON output format for pending decisions."""
        from datetime import date, timedelta

        today = date.today()
        # Create decision first
        add_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "JSON Test Decision"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in add_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        # Update with review date
        future_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")
        runner.invoke(
            app,
            [
                "decisions",
                "update",
                decision_id,
                "--json",
                f'{{"review_at": "{future_date}"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )

        # List pending decisions in JSON format
        result = runner.invoke(
            app,
            ["decisions", "pending", "--format", "json"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        # Should be valid JSON
        import json

        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["title"] == "JSON Test Decision"
        assert "review_at" in data[0]

    def test_decisions_pending_no_overdue(self, runner):
        """Test empty result when no overdue decisions."""
        from datetime import date, timedelta

        today = date.today()
        # Create future decision (not overdue) - first add, then update
        add_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Future Decision"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in add_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        future_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")
        runner.invoke(
            app,
            [
                "decisions",
                "update",
                decision_id,
                "--json",
                f'{{"review_at": "{future_date}"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )

        # List overdue - should show empty JSON array
        result = runner.invoke(
            app,
            ["decisions", "pending", "--overdue"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert result.stdout.strip() == "[]"


class TestTaskCommands:
    """Tests for task management commands."""

    def test_tasks_add(self, runner):
        """Test adding a new task."""
        # Add a decision first
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Learn Python"}'],
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
            [
                "tasks",
                "add",
                "--json",
                f'{{"title": "Practice coding", "decision_id": "{decision_id}"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Created task:" in result.stdout

    def test_tasks_add_without_decision(self, runner):
        """Test adding task without decision fails."""
        result = runner.invoke(
            app,
            ["tasks", "add", "--json", '{"title": "Practice coding"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1  # Missing required decision_id

    def test_tasks_add_with_invalid_decision(self, runner):
        """Test adding task with invalid decision fails."""
        result = runner.invoke(
            app,
            [
                "tasks",
                "add",
                "--json",
                '{"title": "Practice coding", "decision_id": "invalid-id"}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr

    def test_tasks_list_empty(self, runner):
        """Test listing tasks when none exist."""
        result = runner.invoke(
            app,
            ["tasks", "list"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        # In non-interactive mode (no TTY), output defaults to JSON which returns []
        # The output may include "Initializing new session" message from the test fixture
        assert result.stdout.strip().endswith("[]")

    def test_tasks_list_with_data(self, runner):
        """Test listing tasks with data."""
        # Add a decision and task
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Learn Python"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        runner.invoke(
            app,
            [
                "tasks",
                "add",
                "--json",
                f'{{"title": "Practice coding", "decision_id": "{decision_id}"}}',
            ],
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

    def test_tasks_show(self, runner):
        """Test showing task details."""
        # Add a decision and task
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Learn Python"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        task_result = runner.invoke(
            app,
            [
                "tasks",
                "add",
                "--json",
                f'{{"title": "Practice coding", "decision_id": "{decision_id}"}}',
            ],
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

    def test_tasks_show_invalid_id(self, runner):
        """Test showing task with invalid ID fails."""
        result = runner.invoke(
            app,
            ["tasks", "show", "invalid-id"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr

    def test_tasks_complete(self, runner):
        """Test marking task as complete."""
        # Add a decision and task
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Learn Python"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        task_result = runner.invoke(
            app,
            [
                "tasks",
                "add",
                "--json",
                f'{{"title": "Practice coding", "decision_id": "{decision_id}"}}',
            ],
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

    def test_tasks_complete_invalid_id(self, runner):
        """Test completing task with invalid ID fails."""
        result = runner.invoke(
            app,
            ["tasks", "complete", "invalid-id"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr

    def test_tasks_delete(self, runner):
        """Test soft deleting a task."""
        # Add a decision and task
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Learn Python"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        task_result = runner.invoke(
            app,
            [
                "tasks",
                "add",
                "--json",
                f'{{"title": "To Delete", "decision_id": "{decision_id}"}}',
            ],
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

    def test_tasks_delete_invalid_id(self, runner):
        """Test deleting task with invalid ID fails."""
        result = runner.invoke(
            app,
            ["tasks", "delete", "invalid-id", "--force"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr

    def test_tasks_update_title(self, runner):
        """Test updating task title."""
        # Add a decision and task
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Learn Python"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        task_result = runner.invoke(
            app,
            [
                "tasks",
                "add",
                "--json",
                f'{{"title": "Old Title", "decision_id": "{decision_id}"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        task_id = None
        for line in task_result.stdout.split("\n"):
            if "Created task:" in line:
                task_id = line.split("Created task:")[1].strip()
                break

        # Update title
        result = runner.invoke(
            app,
            ["tasks", "update", task_id, "--json", '{"title": "New Title"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Updated task" in result.stdout

    def test_tasks_update_status(self, runner):
        """Test updating task status."""
        # Add a decision and task
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Learn Python"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        task_result = runner.invoke(
            app,
            [
                "tasks",
                "add",
                "--json",
                f'{{"title": "Practice coding", "decision_id": "{decision_id}"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        task_id = None
        for line in task_result.stdout.split("\n"):
            if "Created task:" in line:
                task_id = line.split("Created task:")[1].strip()
                break

        # Update status
        result = runner.invoke(
            app,
            ["tasks", "update", task_id, "--json", '{"status": "in_progress"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Updated task" in result.stdout

    def test_tasks_update_due_date(self, runner):
        """Test updating task due date."""
        # Add a decision and task
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Learn Python"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        task_result = runner.invoke(
            app,
            [
                "tasks",
                "add",
                "--json",
                f'{{"title": "Practice coding", "decision_id": "{decision_id}"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        task_id = None
        for line in task_result.stdout.split("\n"):
            if "Created task:" in line:
                task_id = line.split("Created task:")[1].strip()
                break

        # Update due date
        result = runner.invoke(
            app,
            ["tasks", "update", task_id, "--json", '{"due_date": "2025-12-31"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Updated task" in result.stdout

    def test_tasks_update_notes(self, runner):
        """Test updating task notes."""
        # Add a decision and task
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Learn Python"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        task_result = runner.invoke(
            app,
            [
                "tasks",
                "add",
                "--json",
                f'{{"title": "Practice coding", "decision_id": "{decision_id}"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        task_id = None
        for line in task_result.stdout.split("\n"):
            if "Created task:" in line:
                task_id = line.split("Created task:")[1].strip()
                break

        # Update notes
        result = runner.invoke(
            app,
            [
                "tasks",
                "update",
                task_id,
                "--json",
                '{"notes": "Updated notes for task"}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Updated task" in result.stdout

    def test_tasks_update_with_json(self, runner):
        """Test updating task with JSON payload."""
        # Add a decision and task
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Learn Python"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        task_result = runner.invoke(
            app,
            [
                "tasks",
                "add",
                "--json",
                f'{{"title": "Practice coding", "decision_id": "{decision_id}"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        task_id = None
        for line in task_result.stdout.split("\n"):
            if "Created task:" in line:
                task_id = line.split("Created task:")[1].strip()
                break

        # Update with JSON payload
        result = runner.invoke(
            app,
            [
                "tasks",
                "update",
                task_id,
                "--json",
                '{"title": "JSON Updated Title", "status": "completed"}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Updated task" in result.stdout

    def test_tasks_update_invalid_id(self, runner):
        """Test updating task with invalid ID fails."""
        result = runner.invoke(
            app,
            ["tasks", "update", "invalid-id", "--json", '{"title": "New Title"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr


class TestJourneyCommands:
    """Tests for journey commands."""

    def test_journey_show_with_logs(self, runner):
        """Test showing journey with logs - should show decision details and timeline."""
        # Add a decision
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Test Decision"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        # Add logs to the decision
        runner.invoke(
            app,
            [
                "logs",
                "add",
                "--json",
                f'{{"decision_id": "{decision_id}", "content": "First log entry", "type": "note"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        runner.invoke(
            app,
            [
                "logs",
                "add",
                "--json",
                f'{{"decision_id": "{decision_id}", "content": "Second log entry", "type": "reflection"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )

        # Show journey (defaults to JSON in non-TTY test environment)
        result = runner.invoke(
            app,
            ["journey", "show", decision_id],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        # Parse JSON output and verify contents
        data = json.loads(result.stdout)
        assert data["decision"]["title"] == "Test Decision"
        assert len(data["logs"]) == 2
        assert data["logs"][0]["content"] == "First log entry"
        assert data["logs"][1]["content"] == "Second log entry"

    def test_journey_show_no_logs(self, runner):
        """Test showing journey with no logs - should show decision but 'No journey logs yet'."""
        # Add a decision
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Decision Without Logs"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        # Show journey (no logs added) - defaults to JSON in non-TTY test environment
        result = runner.invoke(
            app,
            ["journey", "show", decision_id],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        # Parse JSON output and verify contents
        data = json.loads(result.stdout)
        assert data["decision"]["title"] == "Decision Without Logs"
        assert len(data["logs"]) == 0

    def test_journey_show_nonexistent(self, runner):
        """Test showing journey for non-existent decision - should fail with 'not found'."""
        result = runner.invoke(
            app,
            ["journey", "show", "nonexistent-id"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr

    def test_journey_show_json_format(self, runner):
        """Test JSON output format - should return valid JSON with decision and logs."""
        # Add a decision
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "JSON Test Decision"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        # Add a log
        runner.invoke(
            app,
            [
                "logs",
                "add",
                "--json",
                f'{{"decision_id": "{decision_id}", "content": "Test log content", "type": "note"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )

        # Show journey with JSON format
        result = runner.invoke(
            app,
            ["journey", "show", decision_id, "--format", "json"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0

        # Parse JSON output
        data = json.loads(result.stdout)
        assert "decision" in data
        assert "logs" in data
        assert data["decision"]["title"] == "JSON Test Decision"
        assert len(data["logs"]) == 1
        assert data["logs"][0]["content"] == "Test log content"

    def test_journey_show_quiet_format(self, runner):
        """Test quiet output format - should return just the decision ID."""
        # Add a decision
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Quiet Test Decision"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        # Add a log
        runner.invoke(
            app,
            ["logs", "add", decision_id, "--content", "Test log", "--type", "note"],
            env={"DECIDUUM_SESSION": "test-session"},
        )

        # Show journey with quiet format
        result = runner.invoke(
            app,
            ["journey", "show", decision_id, "--format", "quiet"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        # Should only contain the decision ID, nothing else
        assert result.stdout.strip() == decision_id


class TestLogCommands:
    """Tests for decision log commands."""

    def test_logs_add(self, runner):
        """Test adding a log entry to a decision."""
        # Add a decision first
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Learn Python"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        # Add log
        result = runner.invoke(
            app,
            [
                "logs",
                "add",
                "--json",
                f'{{"decision_id": "{decision_id}", "type": "note", "content": "Initial research complete"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Created log entry:" in result.stdout

    def test_logs_add_with_source(self, runner):
        """Test adding a log entry with custom source."""
        # Add a decision first
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Learn Python"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        # Add log with system source
        result = runner.invoke(
            app,
            [
                "logs",
                "add",
                "--json",
                f'{{"decision_id": "{decision_id}", "type": "note", "content": "System reminder", "source": "system"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Created log entry:" in result.stdout

    def test_logs_add_reflection_type(self, runner):
        """Test adding a log entry with reflection type."""
        # Add a decision first
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Learn Python"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        # Add reflection log
        result = runner.invoke(
            app,
            [
                "logs",
                "add",
                "--json",
                f'{{"decision_id": "{decision_id}", "type": "reflection", "content": "Better approach is to start with basics"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Created log entry:" in result.stdout

    def test_logs_add_state_change_type(self, runner):
        """Test adding a log entry with state_change type."""
        # Add a decision first
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Learn Python"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        # Add state_change log
        result = runner.invoke(
            app,
            [
                "logs",
                "add",
                "--json",
                f'{{"decision_id": "{decision_id}", "type": "state_change", "content": "Status changed to completed"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Created log entry:" in result.stdout

    def test_logs_add_invalid_decision(self, runner):
        """Test adding log to non-existent decision fails."""
        result = runner.invoke(
            app,
            [
                "logs",
                "add",
                "--json",
                '{"decision_id": "invalid-id", "type": "note", "content": "Test content"}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr

    def test_logs_add_invalid_type(self, runner):
        """Test adding log with invalid type fails."""
        # Add a decision first
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Learn Python"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        # Add log with invalid type
        result = runner.invoke(
            app,
            [
                "logs",
                "add",
                "--json",
                f'{{"decision_id": "{decision_id}", "type": "invalid_type", "content": "Test content"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "Invalid log type" in result.stderr

    def test_logs_list_empty(self, runner):
        """Test listing logs when none exist."""
        # Add a decision first
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Learn Python"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        # List logs (use --format json to get predictable output in test environment)
        result = runner.invoke(
            app,
            ["logs", "list", decision_id, "--format", "json"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        # In JSON format, empty logs returns []
        assert result.stdout.strip() == "[]"

    def test_logs_list_with_data(self, runner):
        """Test listing logs for a decision."""
        # Add a decision first
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Learn Python"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        # Add a log
        runner.invoke(
            app,
            [
                "logs",
                "add",
                "--json",
                f'{{"decision_id": "{decision_id}", "type": "note", "content": "Initial research"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )

        # List logs with JSON format for predictable output
        result = runner.invoke(
            app,
            ["logs", "list", decision_id, "--format", "json"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Initial research" in result.stdout

    def test_logs_list_json_format(self, runner):
        """Test listing logs with JSON format."""
        # Add a decision first
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Learn Python"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        # Add a log
        runner.invoke(
            app,
            [
                "logs",
                "add",
                "--json",
                f'{{"decision_id": "{decision_id}", "type": "note", "content": "Initial research"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )

        # List logs with JSON format
        result = runner.invoke(
            app,
            ["logs", "list", decision_id, "--format", "json"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "[" in result.stdout or "{" in result.stdout

    def test_logs_list_quiet_format(self, runner):
        """Test listing logs with quiet format."""
        # Add a decision first
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Learn Python"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        # Add a log
        runner.invoke(
            app,
            [
                "logs",
                "add",
                "--json",
                f'{{"decision_id": "{decision_id}", "type": "note", "content": "Initial research"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )

        # List logs with quiet format
        result = runner.invoke(
            app,
            ["logs", "list", decision_id, "--format", "quiet"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        # Should output just the log ID without extra formatting
        assert result.stdout.strip()

    def test_logs_list_limit(self, runner):
        """Test listing logs with limit parameter."""
        # Add a decision first
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Learn Python"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        # Add multiple logs
        for i in range(3):
            runner.invoke(
                app,
                [
                    "logs",
                    "add",
                    "--json",
                    f'{{"decision_id": "{decision_id}", "type": "note", "content": "Log entry {i}"}}',
                ],
                env={"DECIDUUM_SESSION": "test-session"},
            )

        # List logs with limit
        result = runner.invoke(
            app,
            ["logs", "list", decision_id, "--limit", "2"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0

    def test_logs_list_invalid_decision(self, runner):
        """Test listing logs for non-existent decision fails."""
        result = runner.invoke(
            app,
            ["logs", "list", "invalid-id"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr

    def test_logs_delete(self, runner):
        """Test deleting a log entry with --force."""
        # Add a decision first
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Learn Python"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        # Add a log
        log_result = runner.invoke(
            app,
            [
                "logs",
                "add",
                "--json",
                f'{{"decision_id": "{decision_id}", "type": "note", "content": "To be deleted"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        log_id = None
        for line in log_result.stdout.split("\n"):
            if "Created log entry:" in line:
                log_id = line.split("Created log entry:")[1].strip()
                break

        # Delete log with --force
        result = runner.invoke(
            app,
            ["logs", "delete", log_id, "--force"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Deleted log" in result.stdout

    def test_logs_delete_invalid_id(self, runner):
        """Test deleting log with invalid ID fails."""
        result = runner.invoke(
            app,
            ["logs", "delete", "invalid-id", "--force"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr

    def test_logs_delete_confirmation_cancelled(self, runner):
        """Test deleting log with cancelled confirmation."""
        # Add a decision first
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Learn Python"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        # Add a log
        log_result = runner.invoke(
            app,
            [
                "logs",
                "add",
                "--json",
                f'{{"decision_id": "{decision_id}", "type": "note", "content": "To cancel delete"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        log_id = None
        for line in log_result.stdout.split("\n"):
            if "Created log entry:" in line:
                log_id = line.split("Created log entry:")[1].strip()
                break

        # Try to delete without --force (will trigger confirmation)
        result = runner.invoke(
            app,
            ["logs", "delete", log_id],
            input="n\n",
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert "Cancelled" in result.stdout


class TestMemoCommands:
    """Tests for memo management commands."""

    def test_memos_add(self, runner):
        """Test adding a new memo with content."""
        result = runner.invoke(
            app,
            ["memos", "add", "--json", '{"content": "My first memo"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Created memo:" in result.stdout

    def test_memos_add_with_date(self, runner):
        """Test adding a memo with a specific date."""
        result = runner.invoke(
            app,
            [
                "memos",
                "add",
                "--json",
                '{"content": "Dated memo", "date": "2024-01-15"}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Created memo:" in result.stdout

    def test_memos_add_with_decision(self, runner):
        """Test adding a memo linked to a decision."""
        # First create a decision
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "Learn Python"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        # Add memo linked to decision
        result = runner.invoke(
            app,
            [
                "memos",
                "add",
                "--json",
                f'{{"content": "Decision memo", "decision_id": "{decision_id}"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Created memo:" in result.stdout

    def test_memos_add_with_direction(self, runner):
        """Test adding a memo linked to a direction."""
        # First create a direction
        dir_result = runner.invoke(
            app,
            ["directions", "add", "--json", '{"title": "Career Growth"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        direction_id = None
        for line in dir_result.stdout.split("\n"):
            if "Created direction:" in line:
                direction_id = line.split("Created direction:")[1].strip()
                break

        # Add memo linked to direction
        result = runner.invoke(
            app,
            [
                "memos",
                "add",
                "--json",
                f'{{"content": "Direction memo", "direction_id": "{direction_id}"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Created memo:" in result.stdout

    def test_memos_add_with_json(self, runner):
        """Test adding a memo with JSON payload."""
        result = runner.invoke(
            app,
            [
                "memos",
                "add",
                "--json",
                '{"content": "JSON memo", "date": "2024-01-20"}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Created memo:" in result.stdout

    def test_memos_list_empty(self, runner):
        """Test listing memos when none exist."""
        result = runner.invoke(
            app,
            ["memos", "list"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        # Should show empty list or "No memos found" message
        assert "No memos found" in result.stdout or "[]" in result.stdout

    def test_memos_list_with_data(self, runner):
        """Test listing memos with data."""
        # Add a memo first
        runner.invoke(
            app,
            ["memos", "add", "--json", '{"content": "Test memo"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )

        # List memos
        result = runner.invoke(
            app,
            ["memos", "list"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Test memo" in result.stdout

    def test_memos_list_with_date_filter(self, runner):
        """Test listing memos with date filter."""
        # Add a memo with specific date
        runner.invoke(
            app,
            [
                "memos",
                "add",
                "--json",
                '{"content": "Dated memo", "date": "2024-01-15"}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )

        # List with date filter
        result = runner.invoke(
            app,
            ["memos", "list", "--date", "2024-01-15"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Dated memo" in result.stdout

    def test_memos_list_json_format(self, runner):
        """Test listing memos with JSON format."""
        # Add a memo first
        runner.invoke(
            app,
            ["memos", "add", "--json", '{"content": "JSON test memo"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )

        # List with JSON format
        result = runner.invoke(
            app,
            ["memos", "list", "--format", "json"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert '"content"' in result.stdout or "[" in result.stdout

    def test_memos_list_quiet_format(self, runner):
        """Test listing memos with quiet format."""
        # Add a memo first
        runner.invoke(
            app,
            ["memos", "add", "--json", '{"content": "Quiet test memo"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )

        # List with quiet format
        result = runner.invoke(
            app,
            ["memos", "list", "--format", "quiet"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        # Should output just IDs without extra formatting
        assert result.stdout.strip()

    def test_memos_show(self, runner):
        """Test showing memo details."""
        # Add a memo first
        add_result = runner.invoke(
            app,
            ["memos", "add", "--json", '{"content": "Show test memo"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        # Extract memo ID
        memo_id = None
        for line in add_result.stdout.split("\n"):
            if "Created memo:" in line:
                memo_id = line.split("Created memo:")[1].strip()
                break

        # Show memo
        result = runner.invoke(
            app,
            ["memos", "show", memo_id],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Show test memo" in result.stdout

    def test_memos_show_invalid_id(self, runner):
        """Test showing memo with invalid ID fails."""
        result = runner.invoke(
            app,
            ["memos", "show", "invalid-id"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr

    def test_memos_update_content(self, runner):
        """Test updating memo content."""
        # Add a memo first
        add_result = runner.invoke(
            app,
            ["memos", "add", "--json", '{"content": "Original content"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        # Extract memo ID
        memo_id = None
        for line in add_result.stdout.split("\n"):
            if "Created memo:" in line:
                memo_id = line.split("Created memo:")[1].strip()
                break

        # Update content
        result = runner.invoke(
            app,
            ["memos", "update", memo_id, "--json", '{"content": "Updated content"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Updated memo" in result.stdout

    def test_memos_update_decision(self, runner):
        """Test updating memo decision link."""
        # Add a memo first
        add_result = runner.invoke(
            app,
            ["memos", "add", "--json", '{"content": "Decision link test"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        memo_id = None
        for line in add_result.stdout.split("\n"):
            if "Created memo:" in line:
                memo_id = line.split("Created memo:")[1].strip()
                break

        # Create a decision to link
        dec_result = runner.invoke(
            app,
            ["decisions", "add", "--json", '{"title": "New Decision"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        decision_id = None
        for line in dec_result.stdout.split("\n"):
            if "Created decision:" in line:
                decision_id = line.split("Created decision:")[1].strip()
                break

        # Update memo with decision
        result = runner.invoke(
            app,
            [
                "memos",
                "update",
                memo_id,
                "--json",
                f'{{"decision_id": "{decision_id}"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Updated memo" in result.stdout

    def test_memos_update_direction(self, runner):
        """Test updating memo direction link."""
        # Add a memo first
        add_result = runner.invoke(
            app,
            ["memos", "add", "--json", '{"content": "Direction link test"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        memo_id = None
        for line in add_result.stdout.split("\n"):
            if "Created memo:" in line:
                memo_id = line.split("Created memo:")[1].strip()
                break

        # Create a direction to link
        dir_result = runner.invoke(
            app,
            ["directions", "add", "--json", '{"title": "New Direction"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        direction_id = None
        for line in dir_result.stdout.split("\n"):
            if "Created direction:" in line:
                direction_id = line.split("Created direction:")[1].strip()
                break

        # Update memo with direction
        result = runner.invoke(
            app,
            [
                "memos",
                "update",
                memo_id,
                "--json",
                f'{{"direction_id": "{direction_id}"}}',
            ],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Updated memo" in result.stdout

    def test_memos_update_with_json(self, runner):
        """Test updating memo with JSON payload."""
        # Add a memo first
        add_result = runner.invoke(
            app,
            ["memos", "add", "--json", '{"content": "JSON update test"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        memo_id = None
        for line in add_result.stdout.split("\n"):
            if "Created memo:" in line:
                memo_id = line.split("Created memo:")[1].strip()
                break

        # Update with JSON
        result = runner.invoke(
            app,
            ["memos", "update", memo_id, "--json", '{"content": "Updated via JSON"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Updated memo" in result.stdout

    def test_memos_update_invalid_id(self, runner):
        """Test updating memo with invalid ID fails."""
        result = runner.invoke(
            app,
            ["memos", "update", "invalid-id", "--json", '{"content": "New content"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr

    def test_memos_delete_with_force(self, runner):
        """Test soft deleting a memo with --force flag."""
        # Add a memo first
        add_result = runner.invoke(
            app,
            ["memos", "add", "--json", '{"content": "To delete"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        # Extract memo ID
        memo_id = None
        for line in add_result.stdout.split("\n"):
            if "Created memo:" in line:
                memo_id = line.split("Created memo:")[1].strip()
                break

        # Delete memo with --force
        result = runner.invoke(
            app,
            ["memos", "delete", memo_id, "--force"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Deleted memo" in result.stdout

    def test_memos_delete_confirmation_cancelled(self, runner):
        """Test deleting memo with cancelled confirmation."""
        # Add a memo first
        add_result = runner.invoke(
            app,
            ["memos", "add", "--json", '{"content": "Cancel delete test"}'],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        # Extract memo ID
        memo_id = None
        for line in add_result.stdout.split("\n"):
            if "Created memo:" in line:
                memo_id = line.split("Created memo:")[1].strip()
                break

        # Try to delete without --force (will trigger confirmation)
        result = runner.invoke(
            app,
            ["memos", "delete", memo_id],
            input="n\n",
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 0
        assert "Cancelled" in result.stdout

    def test_memos_delete_invalid_id(self, runner):
        """Test deleting memo with invalid ID fails."""
        result = runner.invoke(
            app,
            ["memos", "delete", "invalid-id", "--force"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code == 1
        assert "not found" in result.stderr


class TestErrorCases:
    """Tests for error cases and edge conditions."""

    def test_missing_required_argument(self, runner):
        """Test missing required argument shows proper error."""
        # Try to add direction without title
        result = runner.invoke(
            app,
            ["directions", "add"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        # Should fail with usage error
        assert result.exit_code != 0

    def test_invalid_command(self, runner):
        """Test invalid command shows proper error."""
        result = runner.invoke(
            app,
            ["invalid", "command"],
            env={"DECIDUUM_SESSION": "test-session"},
        )
        assert result.exit_code != 0

    def test_delete_confirmation_cancelled(self, runner):
        """Test delete confirmation when cancelled."""
        # Add a direction
        add_result = runner.invoke(
            app,
            ["directions", "add", "--json", '{"title": "Test Direction"}'],
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
