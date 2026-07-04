"""Async SQLAlchemy Setup für SQLite (mit Foreign-Keys-Enforcement)."""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.database_url, echo=False, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


# SQLite erzwingt Foreign Keys nicht automatisch — pro Connection aktivieren.
@event.listens_for(engine.sync_engine, "connect")
def _fk_pragma(dbapi_conn, _record) -> None:  # noqa: ANN001
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA foreign_keys=ON")
    cur.close()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    """Tabellen anlegen (MVP: create_all statt Alembic, bis Schema stabil)."""
    settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    # Models importieren, damit sie in Base.metadata registriert sind
    from app import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
