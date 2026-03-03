from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from typing import AsyncGenerator
from fastapi import Header

# Session engines cache
_session_engines: dict[str, create_async_engine] = {}

# Session session makers cache
_session_makers: dict[str, async_sessionmaker[AsyncSession]] = {}

# Default session ID
DEFAULT_SESSION_ID = "default"


def get_sessions_dir() -> Path:
    """Get the sessions directory path, creating it if it doesn't exist."""
    home = Path.home()
    sessions_dir = home / ".deciduum" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    return sessions_dir


def get_session_db_path(session_id: str) -> Path:
    """Get database path for a session."""
    return get_sessions_dir() / f"{session_id}.db"


def get_session_engine(session_id: str) -> create_async_engine:
    """Get or create engine for session."""
    if session_id not in _session_engines:
        db_path = get_session_db_path(session_id)
        engine = create_async_engine(
            f"sqlite+aiosqlite:///{db_path}",
            echo=False,
            future=True,
        )
        _session_engines[session_id] = engine

        # Create tables for new session database
        from app.models.models import Base
        from sqlalchemy import text

        async def init_session_db():
            async with engine.begin() as conn:
                await conn.execute(text("PRAGMA foreign_keys = ON"))
                await conn.run_sync(Base.metadata.create_all)

        # Run initialization synchronously for new engines
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, schedule the initialization
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, init_session_db())
                    future.result()
            else:
                asyncio.run(init_session_db())
        except RuntimeError:
            asyncio.run(init_session_db())

    return _session_engines[session_id]


def get_session_maker(session_id: str) -> async_sessionmaker[AsyncSession]:
    """Get or create session maker for session."""
    if session_id not in _session_makers:
        engine = get_session_engine(session_id)
        _session_makers[session_id] = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_makers[session_id]


async def get_session_db(
    session_id: str = DEFAULT_SESSION_ID,
) -> AsyncGenerator[AsyncSession, None]:
    """Get database session for a specific session."""
    session_maker = get_session_maker(session_id)
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


# Keep backward compatibility - default database for migration/initial setup
from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Legacy get_db for backward compatibility - uses default database."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        # Enable foreign keys
        await conn.execute(text("PRAGMA foreign_keys = ON"))
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


# =============================================================================
# Session-based database dependency for routers
# =============================================================================


async def get_db_from_header(
    x_session_id: str = Header(default=DEFAULT_SESSION_ID),
) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that gets DB based on X-Session-ID header.

    If X-Session-ID header is missing, defaults to "default" session.
    Auto-creates the database if it doesn't exist.
    """
    session_id = x_session_id or DEFAULT_SESSION_ID
    session_maker = get_session_maker(session_id)
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
