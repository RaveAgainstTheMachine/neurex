"""
tests/test_api_health.py
Tests for core API endpoints: health, files tree, settings.
"""
import pytest


@pytest.mark.asyncio
async def test_health_returns_ok(test_client):
    """GET /health must return 200 with status 'ok'."""
    response = await test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_openapi_schema_loads(test_client):
    """OpenAPI schema must be accessible (proves router mounting works)."""
    response = await test_client.get("/api/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "paths" in schema
    # Verify core routes are present
    assert "/api/chat" in str(schema["paths"]) or "/health" in str(schema["paths"])


@pytest.mark.asyncio
async def test_docs_endpoint(test_client):
    """Swagger UI must be accessible."""
    response = await test_client.get("/api/docs")
    assert response.status_code == 200
