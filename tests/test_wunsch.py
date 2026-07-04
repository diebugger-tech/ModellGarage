"""API-Tests für die manuelle Wunschliste (CRUD + Status-Übergang)."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import init_db
from app.main import app


@pytest.mark.asyncio
async def test_wunsch_crud():
    # stellt sicher, dass die wunsch-Tabelle existiert (create_all, idempotent)
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # anlegen
        r = await ac.post("/api/wunsch", json={"hersteller": "Wiking", "katalog_nr": "99/9T."})
        assert r.status_code == 201
        w = r.json()
        wid = w["id"]
        assert w["status"] == "gesucht"
        assert w["katalog_nr"] == "99/9T."

        # in der Liste enthalten
        r = await ac.get("/api/wunsch")
        assert r.status_code == 200
        assert any(x["id"] == wid for x in r.json())

        # als gekauft markieren
        r = await ac.patch(f"/api/wunsch/{wid}", json={"status": "gekauft"})
        assert r.status_code == 200
        assert r.json()["status"] == "gekauft"

        # ungültiger Status → 400
        r = await ac.patch(f"/api/wunsch/{wid}", json={"status": "quatsch"})
        assert r.status_code == 400

        # löschen → 204
        r = await ac.delete(f"/api/wunsch/{wid}")
        assert r.status_code == 204

        # danach nicht mehr da → 404
        r = await ac.patch(f"/api/wunsch/{wid}", json={"status": "gesucht"})
        assert r.status_code == 404


@pytest.mark.asyncio
async def test_wunsch_hersteller_pflicht():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/api/wunsch", json={"hersteller": "  "})
        assert r.status_code == 400
