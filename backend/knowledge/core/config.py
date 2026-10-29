from functools import lru_cache
from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='OW_', extra='ignore')
    database_url: str = Field(default='postgresql+asyncpg://localhost/ontology_wiki_dev', repr=False)
    auth_secret: str = Field(default='', repr=False)
    token_ttl_seconds: int = Field(default=86400, ge=60, le=604800)
    cors_origins: str = 'http://localhost:5173,http://127.0.0.1:5173'
    storage_path: str = './var/raw'
    provider_mode: Literal['live', 'fixture', 'disabled'] = 'disabled'
    generation_model: str | None = 'gpt-6-luna'
    generation_effort: str | None = 'medium'
    embedding_model: str = 'text-embedding-3-large'
    embedding_dimensions: int = 1536
    embedding_api_dimensions: int = 1536
    embedding_transform: str = 'native'
    wiki_proposal_timeout_seconds: float = Field(default=120, ge=5, le=300)
    worker_poll_seconds: float = Field(default=2, ge=.05)
    retrieval_limit: int = Field(default=8, ge=1, le=40)
    retrieval_candidate_limit: int = Field(default=60, ge=8, le=200)
    reranker_mode: Literal['disabled', 'cross_encoder'] = 'disabled'
    reranker_python_path: str = ''
    reranker_model_path: str = ''
    reranker_model_revision: str = ''
    reranker_timeout_seconds: float = Field(default=120, gt=0)
    reranker_device: Literal['cpu', 'cuda'] = 'cpu'
    reranker_max_length: int = Field(default=1024, ge=32)
    reranker_batch_size: int = Field(default=4, ge=1)
    pdf_parser: Literal['legacy', 'docling'] = 'legacy'
    docling_python_path: str = ''
    docling_artifacts_path: str = './var/docling-artifacts'
    docling_ocr: bool = False
    docling_max_pages: int = Field(default=100, ge=1, le=1000)
    docling_max_characters: int = Field(default=300000, ge=1000, le=2000000)
    docling_timeout_seconds: float = Field(default=480, gt=0)
    context_max_characters: int = Field(default=24000, ge=1000)
    prompt_max_characters: int = Field(default=64000, ge=35000)
    stream_flush_characters: int = Field(default=512, ge=32)
    stream_flush_seconds: float = Field(default=.4, ge=.05)

    @field_validator('database_url')
    @classmethod
    def postgres_only(cls, value):
        if not value.startswith('postgresql+asyncpg://'):
            raise ValueError('OW_DATABASE_URL must use postgresql+asyncpg')
        return value


@lru_cache
def get_settings():
    return Settings()
