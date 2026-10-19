"""Unit Tests for System & Health Check Endpoints.

Verifies:
1. Root liveness probe (GET /healthz)
2. 3-tier status indicators (🟢 healthy / 🟡 degraded / ⚫ maintenance)
3. System version and standard policy metadata (GET /api/v1/system/version)
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch

from backend.app.main import app
from backend.app.core.config import settings


@pytest.mark.asyncio
async def test_root_healthz():
    """Verifies K8s / Container Root Liveness Probe."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == settings.ACTIVE_VERSION


@pytest.mark.asyncio
async def test_system_health_healthy():
    """Verifies 🟢 healthy status when all services and AI gateway are connected."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch("backend.app.api.system.check_db_connection", return_value=True), \
             patch("backend.app.api.system.cache_manager.check_health", return_value=True), \
             patch.object(settings, "GEMINI_API_KEY", "test_mock_api_key"), \
             patch.object(settings, "SYSTEM_STATUS", "healthy"):

            response = await client.get("/api/v1/system/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["services"]["database"] == "connected"
            assert data["services"]["redisCache"] == "connected"
            assert data["services"]["llmGateway"] == "ready"
            assert len(data["activeFallbacks"]) == 0


@pytest.mark.asyncio
async def test_system_health_degraded():
    """Verifies 🟡 degraded status (AI offline, static ontology fallback active)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch("backend.app.api.system.check_db_connection", return_value=True), \
             patch("backend.app.api.system.cache_manager.check_health", return_value=True), \
             patch.object(settings, "GEMINI_API_KEY", ""), \
             patch.object(settings, "SYSTEM_STATUS", "healthy"):

            response = await client.get("/api/v1/system/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert "circuit_open" in data["services"]["llmGateway"]
            assert "static_ontology_fallback" in data["activeFallbacks"]


@pytest.mark.asyncio
async def test_system_health_maintenance():
    """Verifies ⚫ maintenance status (DB disconnected, 503 Safe-Stop)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch("backend.app.api.system.check_db_connection", return_value=False):
            response = await client.get("/api/v1/system/health")
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "maintenance"
            assert data["services"]["database"] == "offline"
            assert "read_only_standby" in data["activeFallbacks"]


@pytest.mark.asyncio
async def test_system_version():
    """Verifies system version, metadata hash, and 0.35 gap threshold policy."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/system/version?clientVersion=v1.2")
        assert response.status_code == 200
        data = response.json()
        assert data["activeVersion"] == "v1.2"
        assert data["latestVersion"] == "v1.3"
        assert data["isUpdateAvailable"] is False
        assert data["systemConfig"]["gapThreshold"] == 0.35
        assert "sha256:" in data["schemaHash"]
