from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import settings

DATABASE_URL = settings.DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
engine = create_async_engine(DATABASE_URL, echo=settings.DEBUG)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def init_db():
    from app.models.project import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
