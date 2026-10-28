"""Explicit fresh-schema installation. No legacy import or destructive reset."""
from hashlib import sha256
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from ..core.config import get_settings

MIGRATION_ROOT = Path(__file__).resolve().parents[2] / "migrations" / "v3"
MARKER = "knowledge_schema_migrations"


def migration_files():
    files = sorted(MIGRATION_ROOT.glob("*.sql"))
    if not files:
        raise RuntimeError("No foundation migrations found")
    return {path.name: (path.read_text(encoding="utf-8"), sha256(path.read_bytes()).hexdigest())
            for path in files}


async def installed_versions(connection):
    exists = await connection.scalar(text("SELECT to_regclass('public.knowledge_schema_migrations')"))
    if exists is None:
        return None
    return dict((await connection.execute(text(
        "SELECT version, sha256 FROM public.knowledge_schema_migrations ORDER BY version"
    ))).all())


def validate_versions(installed, files):
    for version, digest in installed.items():
        if version not in files or files[version][1] != digest:
            raise RuntimeError("Incompatible or modified migration. Use a fresh foundation database; no legacy upgrade is performed.")


async def assert_current_schema(connection):
    files = migration_files()
    installed = await installed_versions(connection)
    if installed is None:
        raise RuntimeError("Foundation schema missing. Run migrate --database-name for a fresh development database.")
    validate_versions(installed, files)
    if set(installed) != set(files):
        raise RuntimeError("Foundation migrations pending. Run the explicit migrate command before starting the server.")


async def migrate(expected_database: str):
    settings = get_settings()
    if make_url(settings.database_url).database != expected_database:
        raise ValueError("Explicit --database-name must equal the configured target database")
    engine = create_async_engine(settings.database_url)
    applied = []
    try:
        async with engine.begin() as connection:
            await connection.execute(text("SET LOCAL search_path TO public"))
            await connection.execute(text("SELECT pg_advisory_xact_lock(820261028)"))
            files = migration_files()
            installed = await installed_versions(connection)
            if installed is None:
                tables = (await connection.execute(text(
                    "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
                ))).scalars().all()
                if tables:
                    raise RuntimeError("Database is not empty. Create a fresh foundation database; existing tables are not modified.")
                await connection.execute(text(
                    "CREATE TABLE public.knowledge_schema_migrations (version text PRIMARY KEY, sha256 text NOT NULL, applied_at timestamptz NOT NULL DEFAULT now())"
                ))
                installed = {}
            validate_versions(installed, files)
            for version, (body, digest) in files.items():
                if version in installed:
                    continue
                # Foundation DDL contains no procedures or embedded semicolons.
                for statement in body.split(";"):
                    if statement.strip():
                        await connection.execute(text(statement))
                await connection.execute(text(
                    "INSERT INTO public.knowledge_schema_migrations(version, sha256) VALUES (:v, :h)"
                ), {"v": version, "h": digest})
                applied.append(version)
    finally:
        await engine.dispose()
    return {"database": expected_database, "applied": applied}
