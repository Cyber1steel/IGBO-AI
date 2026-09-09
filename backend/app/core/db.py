from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import get_settings

# This wires up the connection so Phase 3 can start defining models and a
# migration pipeline without redoing infrastructure. No tables/ORM models
# are defined yet — deliberately out of scope for Phase 2.

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)

async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session():
    async with async_session() as session:
        yield session
