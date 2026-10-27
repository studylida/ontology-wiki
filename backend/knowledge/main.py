from contextlib import asynccontextmanager
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from .core.config import get_settings
from .core.errors import install_error_handlers
from .identity.service import IdentityService
from .conversations.service import ConversationService
from .rag.service import RetrievalService
from .answers.service import AnswerService
from .integrations.providers import get_embedding_client, get_generation_client


def create_app(settings=None, session_factory=None, embedding_client=None, generation_client=None):
    settings = settings or get_settings()
    engine = None
    if session_factory is None:
        engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        session_factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    embedding_client = embedding_client or get_embedding_client(settings)
    generation_client = generation_client or get_generation_client(settings)
    identity = IdentityService(session_factory, settings)
    conversations = ConversationService(session_factory, settings)
    retrieval = RetrievalService(session_factory, embedding_client, settings)
    answers = AnswerService(session_factory, identity, conversations, retrieval, generation_client, settings)

    @asynccontextmanager
    async def lifespan(app):
        # Schema creation/migration and account provisioning are explicit CLI tasks.
        # Starting the API cannot mutate a legacy schema or seed default credentials.
        from .registry import load_entities
        load_entities()
        await answers.recover()
        try:
            yield
        finally:
            await answers.shutdown()
            await retrieval.aclose()
            if engine:
                await engine.dispose()

    app = FastAPI(title="Semiconductor Knowledge Service", version="1.0.0", lifespan=lifespan)
    app.state.settings, app.state.session_factory = settings, session_factory
    app.state.embedding_client, app.state.generation_client = embedding_client, generation_client
    app.state.services = SimpleNamespace(identity=identity, conversations=conversations, rag=retrieval, answers=answers)
    app.add_middleware(CORSMiddleware, allow_origins=[item.strip() for item in settings.cors_origins.split(",") if item.strip()],
                       allow_credentials=False, allow_methods=["GET", "POST", "PATCH", "DELETE"],
                       allow_headers=["Authorization", "Content-Type", "Last-Event-ID"])
    install_error_handlers(app)

    from .identity.router import router as identity_router
    from .conversations.router import router as conversation_router
    from .rag.router import router as retrieval_router
    from .answers.router import router as answer_router
    from .documents.router import router as document_router
    from .ontology.router import router as ontology_router
    from .personal_wiki.router import router as wiki_router
    from .research.router import router as research_router
    from .jobs.router import router as jobs_router
    for router in (identity_router, conversation_router, retrieval_router, answer_router,
                   document_router, ontology_router, wiki_router, research_router, jobs_router):
        app.include_router(router, prefix="/api/v1")

    @app.get("/api/v1/health", tags=["health"])
    async def health():
        database_ok = False
        try:
            async with session_factory() as session:
                database_ok = (await session.scalar(text("SELECT 1"))) == 1
        except Exception:
            pass
        mode, model = settings.provider_mode, getattr(generation_client, "model", None)
        status = "fixture" if mode == "fixture" else "configuration_incomplete" if mode == "disabled" or model in (None, "unconfigured") else "configured_not_verified"
        return JSONResponse({"status": "ok" if database_ok else "degraded", "database": "connected" if database_ok else "unavailable",
            "providerMode": mode, "generationModel": model, "generationStatus": status,
            "embeddingProfile": embedding_client.profile_id, "autoWikiDefaultIsAssumption": True}, status_code=200 if database_ok else 503)

    return app


app = create_app()
