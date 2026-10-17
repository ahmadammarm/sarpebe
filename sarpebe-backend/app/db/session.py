from contextvars import ContextVar
from contextlib import asynccontextmanager
from typing import AsyncIterator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
from sqlalchemy.pool import NullPool
from app.config import settings

engine = create_async_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=10,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Services that need an independent short-lived session (e.g. cost logging) resolve the
# factory through this variable so Celery tasks can substitute their loop-bound one.
_session_factory_var: ContextVar[async_sessionmaker[AsyncSession]] = ContextVar(
    "session_factory", default=AsyncSessionLocal
)


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return _session_factory_var.get()


@asynccontextmanager
async def task_session_scope() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """
    Provides a sessionmaker bound to the *current* event loop for a Celery task.

    Tasks call asyncio.run() per invocation, and pooled asyncpg connections from the
    module-level engine belong to a previous (closed) loop. This creates a NullPool engine
    inside the running loop, exposes it via get_session_factory(), and disposes it on exit.
    """
    task_engine: AsyncEngine = create_async_engine(settings.database_url, poolclass=NullPool, echo=False)
    factory = async_sessionmaker(
        bind=task_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    token = _session_factory_var.set(factory)
    try:
        yield factory
    finally:
        _session_factory_var.reset(token)
        await task_engine.dispose()
