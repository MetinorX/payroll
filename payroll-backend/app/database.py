from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

url = settings.database_url
if url.startswith("postgresql://") and "asyncpg" not in url and "psycopg" not in url:
    url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

connect_args = {}
if "supabase" in url:
    connect_args["ssl"] = "require"

engine = create_async_engine(
    url,
    echo=settings.debug,
    connect_args=connect_args if connect_args else {},
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
