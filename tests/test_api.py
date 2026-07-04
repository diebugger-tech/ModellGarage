"""Backend-Tests: API-Endpoints gegen die importierte DB."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_statistik():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/api/statistik")
    assert r.status_code == 200
    data = r.json()
    assert data["anzahl_modelle"] > 0
    assert "hersteller" in data


@pytest.mark.asyncio
async def test_liste_und_suche():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/api/modelle?limit=5")
        assert r.status_code == 200
        assert len(r.json()["items"]) <= 5

        r2 = await ac.get("/api/modelle?q=Käfer")
        assert r2.status_code == 200
        assert r2.json()["total"] > 0


@pytest.mark.asyncio
async def test_detail_404():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/api/modelle/99999999")
    assert r.status_code == 404
