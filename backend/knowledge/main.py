"""Composition of private conversations, shared intake and evidence-based answers."""
from contextlib import asynccontextmanager
from types import SimpleNamespace
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from .core.config import get_settings
from .core.errors import install_error_handlers
from .conversations.router import router as conversation_router
from .conversations.service import ConversationService
from .documents.router import router as document_router
from .documents.service import DocumentService
from .identity.router import router as identity_router
from .identity.security import check_secret
from .identity.service import IdentityService
from .migration.schema import assert_current_schema
from .registry import load_entities
from .wiki.router import router as wiki_router
from .wiki.service import WikiService
from .wiki.search import WikiSearchService
from .wiki.search_router import router as wiki_search_router
from .answers.router import router as answer_router
from .answers.service import AnswerService
from .integrations.providers import get_embedding_client, get_generation_client
from .rag.service import RAGService


def create_app(settings=None, session_factory=None, *, embedding_client=None, generation_client=None, reranker=None):
    settings = settings or get_settings()
    engine = None
    if session_factory is None:
        engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        session_factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    if reranker is None and settings.reranker_mode == 'cross_encoder':
        from .integrations.rerank import LocalCrossEncoderReranker
        reranker = LocalCrossEncoderReranker(settings.reranker_python_path, settings.reranker_model_path,
            settings.reranker_model_revision, timeout_seconds=settings.reranker_timeout_seconds,
            device=settings.reranker_device, max_length=settings.reranker_max_length,
            batch_size=settings.reranker_batch_size)
    services = SimpleNamespace(identity=IdentityService(session_factory, settings),
        conversations=ConversationService(session_factory), documents=DocumentService(session_factory, settings))
    rag = RAGService(session_factory, settings, embedding_client or get_embedding_client(settings), reranker)
    services.wiki = WikiService(session_factory)
    services.wiki_search = WikiSearchService(session_factory, settings, rag.embedding_client, reranker)
    services.answers = AnswerService(session_factory, settings, services.identity, rag,
                                    generation_client or get_generation_client(settings))

    @asynccontextmanager
    async def lifespan(app):
        try:
            check_secret(settings)
            load_entities()
            async with session_factory() as session:
                await assert_current_schema(session)
            await services.answers.start()
            # Startup never migrates, seeds users, calls a model or starts document jobs.
            yield
        finally:
            await services.answers.close()
            if engine is not None:
                await engine.dispose()

    app = FastAPI(title='Company Knowledge Assistant', version='0.3.0', lifespan=lifespan)
    app.state.settings, app.state.session_factory, app.state.services = settings, session_factory, services
    app.add_middleware(CORSMiddleware,
        allow_origins=[o.strip() for o in settings.cors_origins.split(',') if o.strip()],
        allow_credentials=False, allow_methods=['GET', 'POST', 'PATCH'],
        allow_headers=['Authorization', 'Content-Type', 'Last-Event-ID'])
    install_error_handlers(app)

    @app.middleware('http')
    async def no_personal_response_cache(request, call_next):
        response = await call_next(request)
        if request.url.path.startswith('/api/v1/'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    for router in (identity_router, conversation_router, document_router, answer_router, wiki_router, wiki_search_router):
        app.include_router(router, prefix='/api/v1')

    @app.get('/api/v1/health', tags=['health'])
    async def health():
        connected = False
        try:
            async with session_factory() as session:
                connected = await session.scalar(text('SELECT 1')) == 1
        except Exception:
            pass
        return JSONResponse({'status': 'ok' if connected else 'degraded',
            'database': 'connected' if connected else 'unavailable', 'stage': 'answers', 'providerMode': settings.provider_mode,
            'capabilities': ['authentication', 'private_conversations', 'message_storage',
                'shared_document_upload', 'automatic_indexing', 'grounded_answers', 'durable_answer_events', 'shared_wiki']},
            status_code=200 if connected else 503)
    return app


app = create_app()
