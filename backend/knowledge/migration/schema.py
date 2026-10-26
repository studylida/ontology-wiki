from hashlib import sha256
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from knowledge.core.config import get_settings

MIGRATION_ROOT = Path(__file__).resolve().parents[2] / "migrations" / "v2"


async def migrate(expected_database: str):
    settings = get_settings()
    actual_database = make_url(settings.database_url).database
    if expected_database != actual_database:
        raise ValueError("Explicit --database-name must equal the configured target database")
    engine = create_async_engine(settings.database_url)
    applied = []
    async with engine.begin() as conn:
        await conn.execute(text("SELECT pg_advisory_xact_lock(820261026)"))
        await conn.execute(text("CREATE TABLE IF NOT EXISTS knowledge_schema_migrations (version text PRIMARY KEY, sha256 text NOT NULL, applied_at timestamptz NOT NULL DEFAULT now())"))
        for migration in sorted(MIGRATION_ROOT.glob("*.sql")):
            body = migration.read_text()
            fingerprint = sha256(body.encode()).hexdigest()
            previous = (await conn.execute(text("SELECT sha256 FROM knowledge_schema_migrations WHERE version=:v"), {"v": migration.name})).scalar_one_or_none()
            if previous:
                if previous != fingerprint:
                    raise RuntimeError(f"Applied migration changed: {migration.name}")
                continue
            # The initial migration is generated PostgreSQL DDL without function bodies.
            for statement in body.split(";"):
                if statement.strip():
                    await conn.execute(text(statement))
            await conn.execute(text("INSERT INTO knowledge_schema_migrations(version,sha256) VALUES (:v,:h)"), {"v": migration.name, "h": fingerprint})
            applied.append(migration.name)
    await engine.dispose()
    return {"database": actual_database, "applied": applied}
