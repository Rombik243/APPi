from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from contextlib import asynccontextmanager
from fastapi import FastAPI


DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(DATABASE_URL, echo=True)  # echo=True для логов SQL
async_session = async_sessionmaker(bind=engine, expire_on_commit=False)

Base = declarative_base(cls=AsyncAttrs)

async def get_db():
    async with async_session() as session:
        yield session

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код выполнения при старте
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Код выполнения при завершении (опционально)
    await engine.dispose()
