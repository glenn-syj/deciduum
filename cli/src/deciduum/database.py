"""Database session management for Deciduum CLI."""

from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from deciduum.config import get_session_db_path, get_sessions_dir, get_server_config
from deciduum.models import (
    Base,
    SessionInfo,
    Direction,
    Decision,
    DecisionLog,
    Memo,
    Task,
)


def is_server_mode() -> bool:
    """Check if CLI should use server mode.

    Returns:
        True if server_url is configured, False otherwise.
    """
    server_config = get_server_config()
    return server_config.server_url is not None and server_config.server_url != ""


def get_backend_url() -> Optional[str]:
    """Get configured server URL or None.

    Returns:
        The server URL if configured, None otherwise.
    """
    server_config = get_server_config()
    return server_config.server_url


class DatabaseManager:
    """Manages database connections for session-based SQLite databases."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.db_path = get_session_db_path(session_id)
        self._engine = None
        self._session_factory = None

    @property
    def engine(self):
        """Lazy-load the database engine."""
        if self._engine is None:
            db_url = f"sqlite:///{self.db_path}"
            self._engine = create_engine(db_url, echo=False)
        return self._engine

    @property
    def session_factory(self):
        """Lazy-load the session factory."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(bind=self.engine)
        return self._session_factory

    def create_session(self) -> Session:
        """Create a new database session."""
        return self.session_factory()

    def init_database(self, name: Optional[str] = None) -> None:
        """Initialize the database with all tables."""
        # Ensure the sessions directory exists
        get_sessions_dir()

        # Create all tables
        Base.metadata.create_all(self.engine)

        # Create session info if not exists
        session = self.create_session()
        try:
            existing = (
                session.query(SessionInfo)
                .filter(SessionInfo.session_id == self.session_id)
                .first()
            )

            if not existing:
                session_info = SessionInfo(
                    session_id=self.session_id,
                    name=name or self.session_id,
                )
                session.add(session_info)
                session.commit()
        finally:
            session.close()

    def get_session_info(self) -> Optional[SessionInfo]:
        """Get session metadata."""
        session = self.create_session()
        try:
            return (
                session.query(SessionInfo)
                .filter(SessionInfo.session_id == self.session_id)
                .first()
            )
        finally:
            session.close()

    def close(self) -> None:
        """Close the database engine."""
        if self._engine:
            self._engine.dispose()
            self._engine = None
        self._session_factory = None


# Global database manager instance (will be set per CLI invocation)
_db_manager: Optional[DatabaseManager] = None


def get_db_manager(session_id: str) -> DatabaseManager:
    """Get or create the database manager for a session."""
    global _db_manager
    # Reuse existing instance if same session_id
    if _db_manager is not None and _db_manager.session_id == session_id:
        return _db_manager
    # Close previous instance if different session_id to prevent connection leaks
    if _db_manager is not None:
        _db_manager.close()
    _db_manager = DatabaseManager(session_id)
    return _db_manager


def get_db() -> Session:
    """Get a database session for the current manager."""
    if _db_manager is None:
        raise RuntimeError(
            "Database manager not initialized. Call get_db_manager() first."
        )
    return _db_manager.create_session()


def reset_db_manager() -> None:
    """Reset the global database manager to None.

    This function is primarily used in tests to ensure clean state
    between test cases by closing any existing engine connections
    and resetting the global _db_manager variable.
    """
    global _db_manager
    if _db_manager is not None:
        _db_manager.close()
    _db_manager = None
