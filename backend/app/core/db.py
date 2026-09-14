from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

# Defense in depth against the class of bug where a stuck/slow query hangs a
# request (and, if it also holds a pooled connection, can make every
# subsequent request queue behind it): a shorter pool_timeout means "no free
# connection" fails fast with a clear error instead of queuing indefinitely,
# and asyncpg's command_timeout kills any single query that runs too long.
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_timeout=10,
    connect_args={"command_timeout": 10} if "asyncpg" in settings.database_url else {},
)

async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — one session per request, always closed after."""
    async with async_session() as session:
        yield session
