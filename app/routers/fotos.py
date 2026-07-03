"""Router: Foto-Upload pro Modell (später vom Sammler genutzt)."""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.models import Foto, Modell
from app.schemas import FotoOut

router = APIRouter(prefix="/api", tags=["fotos"])

ERLAUBT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


@router.post("/modelle/{modell_id}/foto", response_model=FotoOut, status_code=201)
async def upload_foto(
    modell_id: int,
    datei: UploadFile,
    session: AsyncSession = Depends(get_session),
) -> FotoOut:
    modell = await session.get(Modell, modell_id)
    if modell is None:
        raise HTTPException(404, "Modell nicht gefunden")

    ext = Path(datei.filename or "").suffix.lower()
    if ext not in ERLAUBT:
        raise HTTPException(400, f"Dateityp {ext} nicht erlaubt")

    settings.media_dir.mkdir(parents=True, exist_ok=True)
    dateiname = f"modell_{modell_id}_{uuid.uuid4().hex[:8]}{ext}"
    ziel = settings.media_dir / dateiname
    inhalt = await datei.read()
    ziel.write_bytes(inhalt)

    foto = Foto(modell_id=modell_id, pfad=f"media/{dateiname}", quelle="manuell")
    session.add(foto)
    await session.commit()
    await session.refresh(foto)
    return FotoOut.model_validate(foto)


@router.get("/modelle/{modell_id}/fotos", response_model=list[FotoOut])
async def liste_fotos(
    modell_id: int, session: AsyncSession = Depends(get_session)
) -> list[FotoOut]:
    rows = (await session.execute(
        select(Foto).where(Foto.modell_id == modell_id)
    )).scalars().all()
    return [FotoOut.model_validate(f) for f in rows]


@router.delete("/fotos/{foto_id}", status_code=204)
async def loesche_foto(
    foto_id: int, session: AsyncSession = Depends(get_session)
) -> None:
    foto = await session.get(Foto, foto_id)
    if foto is None:
        raise HTTPException(404, "Foto nicht gefunden")
    # Datei mitlöschen (best effort)
    pfad = settings.media_dir.parent / foto.pfad
    if pfad.exists():
        pfad.unlink()
    await session.delete(foto)
    await session.commit()
