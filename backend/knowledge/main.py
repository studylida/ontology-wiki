"""Composition of private conversations and shared document intake."""
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


def create_app(settings=None, session_factory=None):
    settings = settings or get_settings()
    engine = None
    if session_factory is None:
        engine = create_async_engine(settings.database_url,pool_pre_ping=True)
        session_factory = async_sessionmaker(engine,expire_on_commit=False,autoflush=False)
    services = SimpleNamespace(identity=IdentityService(session_factory,settings),
        conversations=ConversationService(session_factory),documents=DocumentService(session_factory,settings))

    @asynccontextmanager
    async def lifespan(app):
        try:
            check_secret(settings)
            load_entities()
            async with session_factory() as session:
                await assert_current_schema(session)
            # No migration, account seeding, model call or worker on API startup.
            yield
        finally:
            if engine is not None:
                await engine.dispose()

    app = FastAPI(title='Company Knowledge Assistant',version='0.2.0',lifespan=lifespan)
    app.state.settings,app.state.session_factory,app.state.services = settings,session_factory,services
    app.add_middleware(CORSMiddleware,
        allow_origins=[origin.strip() for origin in settings.cors_origins.split(',') if origin.strip()],
        allow_credentials=False,allow_methods=['GET','POST','PATCH'],allow_headers=['Authorization','Content-Type'])
    install_error_handlers(app)

    @app.middleware('http')
    async def no_personal_response_cache(request,call_next):
        response = await call_next(request)
        if request.url.path.startswith('/api/v1/'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    app.include_router(identity_router,prefix='/api/v1')
    app.include_router(conversation_router,prefix='/api/v1')
    app.include_router(document_router,prefix='/api/v1')

    @app.get('/api/v1/health',tags=['health'])
    async def health():
        connected = False
        try:
            async with session_factory() as session:
                connected = await session.scalar(text('SELECT 1')) == 1
        except Exception:
            pass
        return JSONResponse({'status':'ok' if connected else 'degraded',
            'database':'connected' if connected else 'unavailable','stage':'documents',
            'capabilities':['authentication','private_conversations','message_storage','shared_document_upload','automatic_indexing']},
            status_code=200 if connected else 503)
    return app


app = create_app()
