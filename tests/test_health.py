import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_probe(async_client: AsyncClient):
    """Verifies the basic liveness probe works without the DB."""
    response = await async_client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_readiness_probe(async_client: AsyncClient):
    """
    Verifies the readiness probe works.
    This implicitly tests that testcontainers spun up PostGIS successfully,
    connected the ORM engine to it, and `SELECT 1` executed correctly!
    """
    response = await async_client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
