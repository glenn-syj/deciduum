"""CLI commands package."""

from deciduum.commands.session import session_app
from deciduum.commands.config import config_app
from deciduum.commands.decisions import decisions_app
from deciduum.commands.memos import memos_app
from deciduum.commands.directions import directions_app
from deciduum.commands.tasks import tasks_app
from deciduum.commands.schema import schema_app

__all__ = [
    "session_app",
    "config_app",
    "decisions_app",
    "memos_app",
    "directions_app",
    "tasks_app",
    "schema_app",
]
