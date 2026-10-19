"""System Configuration Module.

Loads environment variables with fallback support for local embedded development.
"""
from typing import List, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # 1. 시스템 기본
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000"

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # 2. 데이터베이스 설정 (Postgres vs SQLite 폴백)
    DB_ENGINE: Literal["postgres", "sqlite"] = "postgres"
    DATABASE_URL: str = "postgresql+asyncpg://ontology_user:ontology_secure_pass@localhost:5432/ontology_wiki"
    SQLITE_DATABASE_URL: str = "sqlite+aiosqlite:///./data/ontology_wiki.db"

    @property
    def active_db_url(self) -> str:
        if self.DB_ENGINE == "sqlite":
            return self.SQLITE_DATABASE_URL
        return self.DATABASE_URL

    # 3. L2 캐시 및 동시성 락 (Redis vs 인메모리 폴백)
    USE_IN_MEMORY_REDIS: bool = False
    REDIS_URL: str = "redis://:ontology_redis_pass@localhost:6379/0"

    # 4. 온톨로지 거버넌스 및 판본
    ACTIVE_VERSION: str = "v1.2"
    LATEST_VERSION: str = "v1.3"
    GAP_THRESHOLD: float = 0.35
    CACHE_TTL_CONCEPT_SECONDS: int = 86400
    PRESENCE_LOCK_TTL_SECONDS: int = 30

    # 5. AI 인과 추론 엔진
    GEMINI_API_KEY: str = ""
    LLM_MODEL: str = "gemini-2.5-flash"
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 3
    CIRCUIT_BREAKER_RECOVERY_TIME_SECONDS: int = 30

    # 6. 3단계 상태 인디케이터
    # 🟢 healthy: 정상 가동
    # 🟡 degraded: 성능 저하 모드
    # ⚫ maintenance: 계획된 점검 및 안전 정지 (검은색)
    SYSTEM_STATUS: Literal["healthy", "degraded", "maintenance"] = "healthy"


settings = Settings()
