"""ModellGarage — FastAPI App.

Serviert im Betrieb das gebaute SvelteKit (frontend/build) + /media + /api.
Ein Prozess, ein Port (siehe AGENTS.md ADR).
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import init_db
from app.routers import ebay, export, fotos, modelle, statistik


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN201
    await init_db()
    settings.media_dir.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="ModellGarage", version="0.1.0", lifespan=lifespan)

app.include_router(modelle.router)
app.include_router(statistik.router)
app.include_router(export.router)
app.include_router(fotos.router)
app.include_router(ebay.router)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# Media (hochgeladene Fotos)
app.mount("/media", StaticFiles(directory=settings.media_dir, check_dir=False), name="media")

# Gebautes Frontend (falls vorhanden) — im Betrieb ein Prozess/ein Port.
# SPA-Fallback: unbekannte Nicht-API-Pfade liefern index.html (Client-Routing).
_frontend_build = Path(__file__).resolve().parent.parent / "frontend" / "build"
if _frontend_build.exists():
    app.mount(
        "/_app",
        StaticFiles(directory=_frontend_build / "_app", check_dir=False),
        name="assets",
    )

    _index = _frontend_build / "index.html"

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):  # noqa: ANN201
        if full_path.startswith("api/"):
            raise HTTPException(404, "Not found")
        # existierende statische Datei direkt ausliefern …
        kandidat = _frontend_build / full_path
        if full_path and kandidat.is_file():
            return FileResponse(kandidat)
        # … sonst index.html (SvelteKit übernimmt Client-seitig)
        return FileResponse(_index)
