"""Tests for schema command."""

import json
import os

import pytest
from typer.testing import CliRunner

from deciduum.__main__ import app


runner = CliRunner()


def _parse_json_output(stdout: str) -> dict | list:
    """Parse JSON from stdout, handling initialization messages."""
    # Strip any initialization message that appears before JSON
    text = stdout.strip()
    # Find where JSON starts (after any initialization message)
    if text.startswith("Initializing"):
        # Find the first [ or { after the initialization message
        for i, char in enumerate(text):
            if char in "[{":
                text = text[i:]
                break
    return json.loads(text)


class TestSchemaCommands:
    """Tests for schema command introspection."""

    # Decisions tests
    def test_schema_decisions_list_all(self, runner, isolated_env):
        """Test schema decisions returns array of all subcommands."""
        result = runner.invoke(
            app,
            ["schema", "decisions"],
            env={"DECIDUUM_SESSION": os.environ.get("DECIDUUM_SESSION")},
        )
        assert result.exit_code == 0
        data = _parse_json_output(result.stdout)
        assert isinstance(data, list)
        # Should have multiple subcommands
        assert len(data) > 0
        # Each item should have expected keys
        for item in data:
            assert "command" in item
            assert "description" in item
            assert "flags" in item

    def test_schema_decisions_list_subcommand(self, runner, isolated_env):
        """Test schema decisions list returns JSON object with command details."""
        result = runner.invoke(
            app,
            ["schema", "decisions", "list"],
            env={"DECIDUUM_SESSION": os.environ.get("DECIDUUM_SESSION")},
        )
        assert result.exit_code == 0
        data = _parse_json_output(result.stdout)
        assert isinstance(data, dict)
        assert "command" in data
        assert data["command"] == "decisions list"
        assert "description" in data
        assert "flags" in data
        assert isinstance(data["flags"], list)

    def test_schema_decisions_add_flags(self, runner, isolated_env):
        """Test schema decisions add includes expected flags."""
        result = runner.invoke(
            app,
            ["schema", "decisions", "add"],
            env={"DECIDUUM_SESSION": os.environ.get("DECIDUUM_SESSION")},
        )
        assert result.exit_code == 0
        data = _parse_json_output(result.stdout)
        assert isinstance(data, dict)
        assert "flags" in data
        flag_names = [f["name"] for f in data["flags"]]
        # Only json is the actual flag - other fields are in the JSON payload
        assert "json" in flag_names
        # Verify json is required
        for flag in data["flags"]:
            if flag["name"] == "json":
                assert flag.get("required") is True

    def test_schema_decisions_show_flags(self, runner, isolated_env):
        """Test schema decisions show includes expected flags."""
        result = runner.invoke(
            app,
            ["schema", "decisions", "show"],
            env={"DECIDUUM_SESSION": os.environ.get("DECIDUUM_SESSION")},
        )
        assert result.exit_code == 0
        data = _parse_json_output(result.stdout)
        assert isinstance(data, dict)
        assert "flags" in data
        flag_names = [f["name"] for f in data["flags"]]
        assert "format" in flag_names
        assert "with" in flag_names

    def test_schema_decisions_invalid_subcommand(self, runner, isolated_env):
        """Test schema decisions with invalid subcommand returns error."""
        result = runner.invoke(
            app,
            ["schema", "decisions", "invalid"],
            env={"DECIDUUM_SESSION": os.environ.get("DECIDUUM_SESSION")},
        )
        assert result.exit_code == 1
        assert "Unknown subcommand" in result.stderr

    # Tasks tests
    def test_schema_tasks_list_all(self, runner, isolated_env):
        """Test schema tasks returns array of all subcommands."""
        result = runner.invoke(
            app,
            ["schema", "tasks"],
            env={"DECIDUUM_SESSION": os.environ.get("DECIDUUM_SESSION")},
        )
        assert result.exit_code == 0
        data = _parse_json_output(result.stdout)
        assert isinstance(data, list)
        assert len(data) > 0
        for item in data:
            assert "command" in item
            assert "description" in item
            assert "flags" in item

    def test_schema_tasks_add_flags(self, runner, isolated_env):
        """Test schema tasks add includes expected flags."""
        result = runner.invoke(
            app,
            ["schema", "tasks", "add"],
            env={"DECIDUUM_SESSION": os.environ.get("DECIDUUM_SESSION")},
        )
        assert result.exit_code == 0
        data = _parse_json_output(result.stdout)
        assert isinstance(data, dict)
        assert "flags" in data
        flag_names = [f["name"] for f in data["flags"]]
        # Only json is the actual flag - other fields are in the JSON payload
        assert "json" in flag_names

    # Memos tests
    def test_schema_memos_list_all(self, runner, isolated_env):
        """Test schema memos returns array of all subcommands."""
        result = runner.invoke(
            app,
            ["schema", "memos"],
            env={"DECIDUUM_SESSION": os.environ.get("DECIDUUM_SESSION")},
        )
        assert result.exit_code == 0
        data = _parse_json_output(result.stdout)
        assert isinstance(data, list)
        assert len(data) > 0
        for item in data:
            assert "command" in item
            assert "description" in item
            assert "flags" in item

    def test_schema_memos_add_flags(self, runner, isolated_env):
        """Test schema memos add includes expected flags."""
        result = runner.invoke(
            app,
            ["schema", "memos", "add"],
            env={"DECIDUUM_SESSION": os.environ.get("DECIDUUM_SESSION")},
        )
        assert result.exit_code == 0
        data = _parse_json_output(result.stdout)
        assert isinstance(data, dict)
        assert "flags" in data
        flag_names = [f["name"] for f in data["flags"]]
        # Only json is the actual flag - other fields are in the JSON payload
        assert "json" in flag_names

    # Directions tests
    def test_schema_directions_list_all(self, runner, isolated_env):
        """Test schema directions returns array of all subcommands."""
        result = runner.invoke(
            app,
            ["schema", "directions"],
            env={"DECIDUUM_SESSION": os.environ.get("DECIDUUM_SESSION")},
        )
        assert result.exit_code == 0
        data = _parse_json_output(result.stdout)
        assert isinstance(data, list)
        assert len(data) > 0
        for item in data:
            assert "command" in item
            assert "description" in item
            assert "flags" in item

    def test_schema_directions_add_flags(self, runner, isolated_env):
        """Test schema directions add includes expected flags."""
        result = runner.invoke(
            app,
            ["schema", "directions", "add"],
            env={"DECIDUUM_SESSION": os.environ.get("DECIDUUM_SESSION")},
        )
        assert result.exit_code == 0
        data = _parse_json_output(result.stdout)
        assert isinstance(data, dict)
        assert "flags" in data
        flag_names = [f["name"] for f in data["flags"]]
        # Only json is the actual flag - other fields are in the JSON payload
        assert "json" in flag_names

    # Logs tests
    def test_schema_logs_list_all(self, runner, isolated_env):
        """Test schema logs returns array of all subcommands."""
        result = runner.invoke(
            app,
            ["schema", "logs"],
            env={"DECIDUUM_SESSION": os.environ.get("DECIDUUM_SESSION")},
        )
        assert result.exit_code == 0
        data = _parse_json_output(result.stdout)
        assert isinstance(data, list)
        assert len(data) > 0
        for item in data:
            assert "command" in item
            assert "description" in item
            assert "flags" in item

    def test_schema_logs_add_flags(self, runner, isolated_env):
        """Test schema logs add includes expected flags with json input."""
        result = runner.invoke(
            app,
            ["schema", "logs", "add"],
            env={"DECIDUUM_SESSION": os.environ.get("DECIDUUM_SESSION")},
        )
        assert result.exit_code == 0
        data = _parse_json_output(result.stdout)
        assert isinstance(data, dict)
        assert "flags" in data
        flag_names = [f["name"] for f in data["flags"]]
        # Only json is the actual flag
        assert "json" in flag_names
        # Check for required json flag
        for flag in data["flags"]:
            if flag["name"] == "json":
                assert flag.get("required") is True

    # Journey tests
    def test_schema_journey_list_all(self, runner, isolated_env):
        """Test schema journey returns array of subcommands."""
        result = runner.invoke(
            app,
            ["schema", "journey"],
            env={"DECIDUUM_SESSION": os.environ.get("DECIDUUM_SESSION")},
        )
        assert result.exit_code == 0
        data = _parse_json_output(result.stdout)
        assert isinstance(data, list)
        assert len(data) > 0
        for item in data:
            assert "command" in item
            assert "description" in item
            assert "flags" in item

    def test_schema_journey_show_flags(self, runner, isolated_env):
        """Test schema journey show includes expected flags."""
        result = runner.invoke(
            app,
            ["schema", "journey", "show"],
            env={"DECIDUUM_SESSION": os.environ.get("DECIDUUM_SESSION")},
        )
        assert result.exit_code == 0
        data = _parse_json_output(result.stdout)
        assert isinstance(data, dict)
        assert "flags" in data
        flag_names = [f["name"] for f in data["flags"]]
        assert "format" in flag_names

    # Session tests
    def test_schema_session_list_all(self, runner, isolated_env):
        """Test schema session returns array of all subcommands."""
        result = runner.invoke(
            app,
            ["schema", "session"],
            env={"DECIDUUM_SESSION": os.environ.get("DECIDUUM_SESSION")},
        )
        assert result.exit_code == 0
        data = _parse_json_output(result.stdout)
        assert isinstance(data, list)
        assert len(data) > 0
        for item in data:
            assert "command" in item
            assert "description" in item
            assert "flags" in item

    def test_schema_session_create_flags(self, runner, isolated_env):
        """Test schema session create includes expected flags."""
        result = runner.invoke(
            app,
            ["schema", "session", "create"],
            env={"DECIDUUM_SESSION": os.environ.get("DECIDUUM_SESSION")},
        )
        assert result.exit_code == 0
        data = _parse_json_output(result.stdout)
        assert isinstance(data, dict)
        assert "flags" in data
        flag_names = [f["name"] for f in data["flags"]]
        assert "session-id" in flag_names
        assert "json" in flag_names

    # Config tests
    def test_schema_config_list_all(self, runner, isolated_env):
        """Test schema config returns array of all subcommands."""
        result = runner.invoke(
            app,
            ["schema", "config"],
            env={"DECIDUUM_SESSION": os.environ.get("DECIDUUM_SESSION")},
        )
        assert result.exit_code == 0
        data = _parse_json_output(result.stdout)
        assert isinstance(data, list)
        assert len(data) > 0
        for item in data:
            assert "command" in item
            assert "description" in item
            assert "flags" in item

    def test_schema_config_set_flags(self, runner, isolated_env):
        """Test schema config set returns expected flags."""
        result = runner.invoke(
            app,
            ["schema", "config", "set"],
            env={"DECIDUUM_SESSION": os.environ.get("DECIDUUM_SESSION")},
        )
        assert result.exit_code == 0
        data = _parse_json_output(result.stdout)
        assert isinstance(data, dict)
        assert "flags" in data
        # config set has key and value flags
        flag_names = [f["name"] for f in data["flags"]]
        assert "key" in flag_names
        assert "value" in flag_names

    # Today tests
    def test_schema_today(self, runner, isolated_env):
        """Test schema today returns command info."""
        result = runner.invoke(
            app,
            ["schema", "today"],
            env={"DECIDUUM_SESSION": os.environ.get("DECIDUUM_SESSION")},
        )
        assert result.exit_code == 0
        data = _parse_json_output(result.stdout)
        assert isinstance(data, dict)
        assert "command" in data
        assert data["command"] == "today"
        assert "description" in data

    # All tests
    def test_schema_all(self, runner, isolated_env):
        """Test schema all returns array of ALL commands."""
        result = runner.invoke(
            app,
            ["schema", "all"],
            env={"DECIDUUM_SESSION": os.environ.get("DECIDUUM_SESSION")},
        )
        assert result.exit_code == 0
        data = _parse_json_output(result.stdout)
        assert isinstance(data, list)
        # Should have many entries (all commands)
        assert len(data) > 10
        for item in data:
            assert "command" in item
            assert "description" in item
            assert "flags" in item

    # Invalid command tests
    def test_schema_invalid_command(self, runner, isolated_env):
        """Test schema with invalid command returns error."""
        result = runner.invoke(
            app,
            ["schema", "invalid"],
            env={"DECIDUUM_SESSION": os.environ.get("DECIDUUM_SESSION")},
        )
        assert result.exit_code != 0
        # Should have error message
        assert "No such command" in result.stderr or result.exit_code in (1, 2)
