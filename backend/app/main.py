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
from backend.app.api.evidences import router as evidences_router
from backend.app.api.research import router as research_router
from backend.app.api.chatbot import router as chatbot_router

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

import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# CORS 미들웨어 등록
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list + ["null"],
    allow_origin_regex=r".*",
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
app.include_router(evidences_router, prefix="/api/v1")
app.include_router(research_router, prefix="/api/v1")
app.include_router(chatbot_router, prefix="/api/v1")


@app.get("/healthz", tags=["System"])
async def root_health_check():
    """K8s / Container Root Liveness Probe."""
    return {"status": "ok", "version": settings.ACTIVE_VERSION}


# 프론트엔드 정적 리소스 및 SPA 라우팅 서빙
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
css_dir = os.path.join(BASE_DIR, "css")
js_dir = os.path.join(BASE_DIR, "js")
index_html = os.path.join(BASE_DIR, "index.html")

if os.path.exists(css_dir):
    app.mount("/css", StaticFiles(directory=css_dir), name="css")
if os.path.exists(js_dir):
    app.mount("/js", StaticFiles(directory=js_dir), name="js")


@app.get("/", tags=["Frontend"])
async def serve_frontend_index():
    """웹 브라우저 접속 시 온톨로지 위키 SPA 화면을 직접 서빙합니다."""
    if os.path.exists(index_html):
        return FileResponse(index_html)
    return {"message": "Semiconductor Causal Ontology Wiki Core Service"}

