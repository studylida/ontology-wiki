from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OW_", extra="ignore")

    database_url: str = Field("postgresql+asyncpg://localhost/ontology_wiki_dev", repr=False)
    auth_secret: str = Field("", repr=False)
    token_ttl_seconds: int = Field(86400, ge=60, le=604800)
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    storage_path: str = "./var/raw"
    provider_mode: Literal["live", "fixture", "disabled"] = "disabled"
    generation_model: str | None = "gpt-6-luna"
    generation_effort: str | None = "medium"
    embedding_model: str = "text-embedding-3-large"
    embedding_dimensions: int = Field(1536, ge=1)
    embedding_api_dimensions: int = Field(1536, ge=1)
    embedding_transform: Literal["native", "prefix_l2"] = "native"
    index_hour_local: int = Field(3, ge=0, le=23)
    index_timezone: str = "Asia/Seoul"
    worker_poll_seconds: float = Field(2.0, ge=0.05)
    research_api_url: str = "https://api.crossref.org/works"
    research_timeout_seconds: float = Field(15.0, gt=0)
    research_network_mode: Literal["system", "google_doh_egress"] = "system"
    auto_wiki_default: bool = True
    retrieval_limit: int = Field(8, ge=1, le=40)
    retrieval_candidate_limit: int = Field(60, ge=8, le=200)
    reranker_mode: Literal["disabled", "cross_encoder"] = "disabled"
    reranker_python_path: str = ""
    reranker_model_path: str = ""
    reranker_model_revision: str = ""
    reranker_timeout_seconds: float = Field(120.0, gt=0, le=600)
    reranker_device: Literal["cpu", "cuda"] = "cpu"
    reranker_max_length: int = Field(1024, ge=128, le=8192)
    reranker_batch_size: int = Field(4, ge=1, le=64)
    retrieval_graph_mode: Literal["disabled", "lightrag"] = "disabled"
    lightrag_python_path: str = ""
    lightrag_index_path: str = ""
    lightrag_timeout_seconds: float = Field(90.0, gt=0, le=600)
    pdf_parser: Literal["legacy", "docling"] = "legacy"
    docling_python_path: str = ""
    docling_artifacts_path: str = "./var/docling-artifacts"
    docling_ocr: bool = False
    docling_max_pages: int = Field(100, ge=1, le=500)
    docling_max_characters: int = Field(300000, ge=1000, le=2000000)
    docling_timeout_seconds: float = Field(480.0, gt=0, le=900)
    extended_max_queries: int = Field(3, ge=0, le=12)
    extended_seconds: float = Field(15.0, gt=0)
    context_max_characters: int = Field(24000, ge=1000)
    prompt_max_characters: int = Field(64000, ge=35000)
    stream_flush_characters: int = Field(512, ge=32)
    stream_flush_seconds: float = Field(0.4, ge=0.05)

    @field_validator("database_url")
    @classmethod
    def postgres_only(cls, value: str) -> str:
        if not value.startswith("postgresql+asyncpg://"):
            raise ValueError("OW_DATABASE_URL must use postgresql+asyncpg; no silent database fallback")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
