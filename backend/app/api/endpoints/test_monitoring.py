import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from app.main import app

@pytest.mark.asyncio
async def test_metrics_endpoint_requires_auth():
    """Test that metrics endpoint requires authentication"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/monitoring/metrics")
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_metrics_endpoint_with_auth():
    """Test metrics endpoint with valid API key"""
    with patch("app.api.dependencies.get_api_key", return_value="test-api-key"):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/monitoring/metrics",
                headers={"X-API-Key": "test-api-key"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "uptime_seconds" in data
            assert "total_requests" in data
            assert "system" in data

@pytest.mark.asyncio
async def test_health_metrics_endpoint():
    """Test health metrics endpoint (no auth required)"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/monitoring/metrics/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "checks" in data
        assert data["status"] in ["healthy", "unhealthy"]

@pytest.mark.asyncio
async def test_reset_metrics_endpoint():
    """Test reset metrics endpoint"""
    with patch("app.api.dependencies.get_api_key", return_value="test-api-key"):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/monitoring/metrics/reset",
                headers={"X-API-Key": "test-api-key"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "Metrics reset successfully"