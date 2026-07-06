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


@pytest.mark.asyncio
async def test_liste_liefert_foto_url_wie_detail():
    """Regression: Galerie-Liste muss das erste Foto mitliefern (foto_url),
    identisch zu dem, was die Detailseite über /fotos anzeigt."""
    from io import BytesIO

    from PIL import Image

    buf = BytesIO()
    Image.new("RGB", (8, 8), (200, 40, 40)).save(buf, format="PNG")
    png = buf.getvalue()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # frisches Modell (bekommt höchste id)
        r = await ac.post("/api/modelle/voll", json={"hersteller": "TestFoto", "typ": "Foto-Testwagen"})
        assert r.status_code == 201
        mid = r.json()["id"]
        foto_id = None
        try:
            up = await ac.post(
                f"/api/modelle/{mid}/foto",
                files={"datei": ("t.png", png, "image/png")},
            )
            assert up.status_code == 201, up.text
            foto_id = up.json()["id"]

            # Detail-Route (Quelle der Wahrheit für die Detailseite)
            fotos = (await ac.get(f"/api/modelle/{mid}/fotos")).json()
            assert fotos, "Detail-Route liefert das Foto nicht"
            detail_url = "/" + fotos[0]["pfad"]

            # Listen-Route: unser Modell ist das neueste
            liste = (await ac.get("/api/modelle?sort=id&order=desc&limit=1")).json()
            item = liste["items"][0]
            assert item["id"] == mid
            assert item["foto_url"] == detail_url
        finally:
            if foto_id is not None:
                await ac.delete(f"/api/fotos/{foto_id}")
            await ac.delete(f"/api/modelle/{mid}")


@pytest.mark.asyncio
async def test_liste_faellt_auf_konvolut_foto_zurueck():
    """Ein Konvolut-Kind ohne eigenes Foto zeigt in der Galerie das
    Konvolut-Gesamtfoto; ein eigenes Modell-Foto hat Vorrang."""
    from io import BytesIO

    from PIL import Image

    def png(farbe):
        buf = BytesIO()
        Image.new("RGB", (8, 8), farbe).save(buf, format="PNG")
        return buf.getvalue()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        kid = (await ac.post("/api/konvolut", json={"quelle": "TestPaket"})).json()["id"]
        kon_foto = mod_foto = mid = None
        try:
            # Kind im Konvolut anlegen (bekommt höchste id)
            kres = await ac.post(
                f"/api/konvolut/{kid}/modell-voll",
                json={"hersteller": "TestKonv", "typ": "Konvolut-Testwagen"},
            )
            assert kres.status_code == 200, kres.text
            mid = kres.json()["kinder"][-1]["id"]

            # Foto NUR am Konvolut
            kf = await ac.post(
                f"/api/konvolut/{kid}/foto", files={"datei": ("k.png", png((10, 10, 200)), "image/png")}
            )
            assert kf.status_code == 201, kf.text
            kon_foto = kf.json()
            kon_url = "/" + kon_foto["pfad"]

            # Galerie: Kind ohne Eigenfoto -> Fallback auf Konvolut-Foto
            item = (await ac.get("/api/modelle?sort=id&order=desc&limit=1")).json()["items"][0]
            assert item["id"] == mid
            assert item["foto_url"] == kon_url

            # Eigenes Modell-Foto hat Vorrang
            mf = await ac.post(
                f"/api/modelle/{mid}/foto", files={"datei": ("m.png", png((200, 10, 10)), "image/png")}
            )
            assert mf.status_code == 201, mf.text
            mod_foto = mf.json()
            item2 = (await ac.get("/api/modelle?sort=id&order=desc&limit=1")).json()["items"][0]
            assert item2["foto_url"] == "/" + mod_foto["pfad"]
        finally:
            if mod_foto:
                await ac.delete(f"/api/fotos/{mod_foto['id']}")
            if kon_foto:
                await ac.delete(f"/api/fotos/{kon_foto['id']}")
            if mid is not None:
                await ac.delete(f"/api/modelle/{mid}")
            await ac.delete(f"/api/konvolut/{kid}")
