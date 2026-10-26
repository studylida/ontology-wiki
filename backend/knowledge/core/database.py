from functools import lru_cache

from fastapi import Request
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache
def get_engine():
    return create_async_engine(get_settings().database_url, pool_pre_ping=True)


@lru_cache
def get_session_factory():
    return async_sessionmaker(get_engine(), expire_on_commit=False, autoflush=False)


async def get_session(request: Request):
    async with request.app.state.session_factory() as session:
        try:
            yield session
        except BaseException:
            await session.rollback()
            raise
