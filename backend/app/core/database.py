"""Async engine + session factory with RLS tenant-context helpers.

Row-level security is enforced by PostgreSQL policies that compare
``tenant_id`` to the transaction-local GUC ``app.current_tenant_id``.
Platform-level requests instead set ``app.platform_ctx = 'platform'`` which
the policies treat as a bypass. Both are applied via ``SET LOCAL`` inside the
same checked-out connection, so pool checkout order is safe.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, pool_size=10, max_overflow=20, pool_pre_ping=True)
SessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    """Plain session — only for platform-context endpoints and migrations."""

    async with SessionFactory() as session:
        yield session


@asynccontextmanager
async def tenant_session(tenant_id: str) -> AsyncIterator[AsyncSession]:
    """Session bound to a single tenant via ``SET LOCAL app.current_tenant_id``.

    Every statement inside runs in one transaction on one connection, so RLS
    policies see the tenant context. Must not outlive the request.
    """

    async with SessionFactory() as session:
        async with session.begin():
            await session.execute(
                text("SELECT set_config('app.current_tenant_id', :tid, true)"),
                {"tid": tenant_id},
            )
            yield session


@asynccontextmanager
async def platform_session() -> AsyncIterator[AsyncSession]:
    """Session flagged as platform context — RLS policies bypass tenant filter."""

    async with SessionFactory() as session:
        async with session.begin():
            await session.execute(text("SELECT set_config('app.platform_ctx', 'platform', true)"))
            yield session
