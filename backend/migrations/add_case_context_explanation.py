"""Explicit, idempotent migration; never imports application DB settings.

Run: python backend/migrations/add_case_context_explanation.py --database-url <URL>
"""
import argparse
import asyncio

from sqlalchemy import Column, JSON, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.schema import CreateColumn


def column_ddl(dialect) -> str:
    return str(CreateColumn(Column("context_explanation", JSON, nullable=True)).compile(dialect=dialect))


async def migrate(database_url: str) -> bool:
    url = make_url(database_url)
    backend = url.get_backend_name()
    if backend not in ("sqlite", "postgresql", "postgres"):
        raise ValueError("Only SQLite and PostgreSQL are supported")
    url = url.set(drivername="sqlite+aiosqlite" if backend == "sqlite" else "postgresql+asyncpg")
    engine = create_async_engine(url)
    try:
        async with engine.begin() as connection:
            columns = await connection.run_sync(lambda conn: inspect(conn).get_columns("perspective_cases"))
            if any(column["name"] == "context_explanation" for column in columns):
                return False
            await connection.execute(text("ALTER TABLE perspective_cases ADD COLUMN " + column_ddl(connection.dialect)))
            return True
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", required=True, help="Explicit target database URL; no configured default")
    args = parser.parse_args()
    changed = asyncio.run(migrate(args.database_url))
    print("context_explanation added" if changed else "context_explanation already exists")


if __name__ == "__main__":
    main()
