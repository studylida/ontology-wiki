"""PostgreSQL integration fixtures; every test owns a disposable schema.

No production database or live model API is used. A missing dev database fails
the integration test rather than silently substituting SQLite or memory storage.
"""
import os
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from knowledge.core.config import Settings
from knowledge.core.database import Base
from knowledge.core.ids import new_id
from knowledge.identity.entities import User
from knowledge.identity.security import create_token, hash_password
from knowledge.identity.service import principal_from_user
from knowledge.integrations.providers import FixtureEmbeddingClient, FixtureGenerationClient
from knowledge.registry import load_entities


TEST_PASSWORD = "test-only-password"
TEST_HASH = hash_password(TEST_PASSWORD)


@pytest.fixture
def settings(tmp_path):
    url = os.environ.get("OW_TEST_DATABASE_URL", os.environ.get("OW_DATABASE_URL",
        "postgresql+asyncpg://ontology:ontology@127.0.0.1:55432/ontology_wiki_dev"))
    database = make_url(url).database or ""
    if not (database.endswith("_dev") or "test" in database):
        raise RuntimeError("Tests require an explicitly isolated development/test database")
    return Settings(database_url=url, auth_secret="test-only-secret-which-is-at-least-thirty-two-characters",
                    storage_path=str(tmp_path / "raw"), provider_mode="fixture",
                    generation_model="fixture-generation", auto_wiki_default=True)


@pytest_asyncio.fixture
async def pg_engine(settings):
    load_entities()
    schema = "ow_test_" + uuid4().hex
    control = create_async_engine(settings.database_url)
    async with control.begin() as connection:
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_async_engine(settings.database_url,
        connect_args={"server_settings": {"search_path": f"{schema},public"}},
        execution_options={"schema_translate_map": {None: schema}})
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
            count = await connection.scalar(text("SELECT count(*) FROM information_schema.tables WHERE table_schema=:schema"), {"schema": schema})
            assert count == len(Base.metadata.tables), "All fixture tables must exist in the isolated schema"
        yield engine
    finally:
        await engine.dispose()
        async with control.begin() as connection:
            await connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        await control.dispose()


@pytest.fixture
def sessions(pg_engine):
    return async_sessionmaker(pg_engine, expire_on_commit=False, autoflush=False)


@pytest.fixture
def seed_user(sessions):
    async def create(username="test-user", *, role="user", kind="user", permissions=None, auto_wiki=False):
        async with sessions() as session, session.begin():
            user = User(id=new_id("usr"), username=username, password_hash=TEST_HASH, role=role, kind=kind,
                        permissions=permissions or [], auto_wiki=auto_wiki)
            session.add(user)
            await session.flush()
            return principal_from_user(user)
    return create


@pytest_asyncio.fixture
async def principal(seed_user):
    return await seed_user()


@pytest_asyncio.fixture
async def other_principal(seed_user):
    return await seed_user("other-user")


@pytest_asyncio.fixture
async def reviewer(seed_user):
    return await seed_user("test-reviewer", role="reviewer")


@pytest_asyncio.fixture
async def service_principal(seed_user):
    return await seed_user("test-service", kind="service", permissions=["ontology:read", "rag:retrieve"])


@pytest.fixture
def embedding_client():
    return FixtureEmbeddingClient()


@pytest.fixture
def generation_client():
    return FixtureGenerationClient()


@pytest_asyncio.fixture
async def app(settings, sessions, embedding_client, generation_client):
    from knowledge.main import create_app
    application = create_app(settings, sessions, embedding_client, generation_client)
    async with application.router.lifespan_context(application):
        yield application


@pytest_asyncio.fixture
async def client(app):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
                                base_url="http://testserver") as client:
        yield client


@pytest_asyncio.fixture
async def auth_headers(principal, sessions, settings):
    async with sessions() as session:
        user = await session.get(User, principal.id)
    return {"Authorization": "Bearer " + create_token(user, settings)}
