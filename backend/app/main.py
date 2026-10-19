"""FastAPI Main Application Entry Point.

Semiconductor Causal Ontology Wiki Core Backend Service.
"""
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.core.cache import cache_manager
from backend.app.api.system import router as system_router
from backend.app.api.search import router as search_router
from backend.app.api.concepts import router as concepts_router
from backend.app.api.comparison import router as comparison_router
from backend.app.api.review_tickets import router as review_tickets_router

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ontology_wiki")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    logger.info("Initializing Ontology Wiki Core Services...")
    await cache_manager.init()
    yield
    logger.info("Shutting down Ontology Wiki Core Services...")
    await cache_manager.close()


app = FastAPI(
    title="반도체 공정·소자 인과 온톨로지 지식 위키 API",
    description="반도체 공정 인과 추론, 적응형 실무 사례, 2단계 비교 분석 및 거버넌스 REST API 서비스",
    version=settings.ACTIVE_VERSION,
    lifespan=lifespan
)

# CORS 미들웨어 등록
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API v1 라우터 등록
app.include_router(system_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(concepts_router, prefix="/api/v1")
app.include_router(comparison_router, prefix="/api/v1")
app.include_router(review_tickets_router, prefix="/api/v1")


@app.get("/healthz", tags=["System"])
async def root_health_check():
    """K8s / Container Root Liveness Probe."""
    return {"status": "ok", "version": settings.ACTIVE_VERSION}
