"""Database session management for Deciduum CLI."""

from pathlib import Path
from typing import List, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from deciduum.config import (
    get_session_db_path,
    get_sessions_dir,
    get_server_config,
    get_registry_db_path,
    get_registry_data_dir,
)
from deciduum.models import (
    Base,
    RegistrySession,
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


def reset_registry_manager() -> None:
    """Reset the global registry manager to None.

    This function is primarily used in tests to ensure clean state
    between test cases by closing any existing engine connections
    and resetting the global _registry_manager variable.
    """
    global _registry_manager
    if _registry_manager is not None:
        _registry_manager.close()
    _registry_manager = None


class RegistryManager:
    """Manages the registry database for session tracking."""

    def __init__(self):
        self.db_path = get_registry_db_path()
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

    def init_database(self) -> None:
        """Initialize the registry database with all tables."""
        # Ensure the registry directory exists
        get_registry_data_dir().mkdir(parents=True, exist_ok=True)

        # Create all tables
        Base.metadata.create_all(self.engine)

    def list_sessions(self) -> List[RegistrySession]:
        """List all registered sessions.

        Returns:
            List of all RegistrySession objects.
        """
        session = self.create_session()
        try:
            return session.query(RegistrySession).all()
        finally:
            session.close()

    def get_session(self, session_id: str) -> Optional[RegistrySession]:
        """Get a session by session_id.

        Args:
            session_id: The session ID to look up.

        Returns:
            RegistrySession if found, None otherwise.
        """
        session = self.create_session()
        try:
            return (
                session.query(RegistrySession)
                .filter(RegistrySession.session_id == session_id)
                .first()
            )
        finally:
            session.close()

    def add_session(self, session_id: str) -> RegistrySession:
        """Add a new session to the registry.

        Args:
            session_id: The session ID to add.

        Returns:
            The newly created RegistrySession.
        """
        session = self.create_session()
        try:
            existing = (
                session.query(RegistrySession)
                .filter(RegistrySession.session_id == session_id)
                .first()
            )

            if existing:
                return existing

            registry_session = RegistrySession(session_id=session_id)
            session.add(registry_session)
            session.commit()
            session.refresh(registry_session)
            return registry_session
        finally:
            session.close()

    def remove_session(self, session_id: str) -> bool:
        """Remove a session from the registry.

        Args:
            session_id: The session ID to remove.

        Returns:
            True if session was removed, False if not found.
        """
        session = self.create_session()
        try:
            registry_session = (
                session.query(RegistrySession)
                .filter(RegistrySession.session_id == session_id)
                .first()
            )

            if registry_session:
                session.delete(registry_session)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def close(self) -> None:
        """Close the database engine."""
        if self._engine:
            self._engine.dispose()
            self._engine = None
        self._session_factory = None


def needs_migration() -> bool:
    """Check if the registry needs migration.

    Returns:
        True if migration is needed (registry doesn't exist or is empty),
        False otherwise.
    """
    registry_db_path = get_registry_db_path()

    # Registry doesn't exist at all
    if not registry_db_path.exists():
        return True

    # Registry exists but might be empty - check if there are any sessions
    try:
        manager = RegistryManager()
        sessions = manager.list_sessions()
        return len(sessions) == 0
    except Exception:
        # If we can't read the registry, assume migration is needed
        return True


def migrate_sessions() -> int:
    """Migrate existing session databases to the master registry.

    Scans the filesystem for session databases in the sessions directory
    and adds any missing sessions to the master registry.

    Returns:
        Number of sessions migrated (added to registry).
    """
    sessions_dir = get_sessions_dir()

    # Ensure registry is initialized
    registry_manager = get_registry_manager()
    registry_manager.init_database()

    # Get existing sessions in registry
    existing_sessions = registry_manager.list_sessions()
    existing_ids = {s.session_id for s in existing_sessions}

    if not sessions_dir.exists():
        return 0

    db_files = list(sessions_dir.glob("*.db"))

    migrated_count = 0

    for db_file in db_files:
        session_id = db_file.stem

        # Skip if already in registry (idempotent)
        if session_id in existing_ids:
            continue

        # Try to add to registry - add_session is already idempotent
        try:
            registry_manager.add_session(session_id)
            migrated_count += 1
            existing_ids.add(session_id)  # Track to avoid duplicates in same run
        except Exception:
            # Skip duplicates or errors gracefully
            pass

    return migrated_count


# Global registry manager instance
_registry_manager: Optional[RegistryManager] = None


def get_registry_manager() -> RegistryManager:
    """Get or create the registry manager."""
    global _registry_manager
    if _registry_manager is None:
        _registry_manager = RegistryManager()
    return _registry_manager
