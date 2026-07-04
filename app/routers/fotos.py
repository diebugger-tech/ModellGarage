"""Router: Foto-Upload pro Modell — mit Sicherheits-Härtung.

Sicherheit (lokale App, kein Auth): Upload-Robustheit gegen kaputte/riesige/
gefährliche Dateien:
- Größenlimit (verhindert Speicher-/Platten-Erschöpfung)
- Endung UND echter Bild-Inhalt geprüft (Pillow verifiziert Magic-Bytes)
- Dateiname wird serverseitig generiert (uuid) — kein Nutzer-Pfad → kein
  Path-Traversal möglich
"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.models import Foto, Konvolut, Modell
from app.schemas import FotoOut

router = APIRouter(prefix="/api", tags=["fotos"])

ERLAUBT = {".jpg", ".jpeg", ".png", ".webp"}
MAX_BYTES = 10 * 1024 * 1024  # 10 MB pro Foto
MAX_MEGAPIXEL = 25  # Sanity-Grenze für Bildabmessungen
# Pillow-Format → kanonische Endung. GIF bewusst nicht erlaubt (Script-Einbettung möglich).
_PIL_EXT = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}
# HTTP-Content-Type-Whitelist; falsch deklarierte Dateien ablehnen
_ERLAUBTE_MIME = {"image/jpeg", "image/png", "image/webp"}


async def _validiere_bild(datei: UploadFile) -> tuple[bytes, str]:
    """Prüft MIME, Format, Größe und Abmessungen eines Uploads."""
    ext = Path(datei.filename or "").suffix.lower()
    if ext not in ERLAUBT:
        raise HTTPException(400, f"Dateityp {ext or '?'} nicht erlaubt")
    if datei.content_type and datei.content_type not in _ERLAUBTE_MIME:
        raise HTTPException(400, "Content-Type nicht erlaubt")

    inhalt = await datei.read()
    if not inhalt:
        raise HTTPException(400, "Leere Datei")
    if len(inhalt) > MAX_BYTES:
        raise HTTPException(413, f"Datei zu groß (max. {MAX_BYTES // 1024 // 1024} MB)")

    from io import BytesIO
    try:
        img = Image.open(BytesIO(inhalt))
        img.verify()
        fmt = img.format or ""
    except (UnidentifiedImageError, OSError) as e:
        raise HTTPException(400, "Datei ist kein gültiges Bild") from e

    sichere_ext = _PIL_EXT.get(fmt)
    if sichere_ext is None:
        raise HTTPException(400, f"Bildformat {fmt} nicht erlaubt")

    # Abmessungen sanity-check (verify() schließt das Bild, also neu öffnen)
    try:
        with Image.open(BytesIO(inhalt)) as img2:
            breite, hoehe = img2.size
            if breite * hoehe > MAX_MEGAPIXEL * 1_000_000:
                raise HTTPException(400, "Bildauflösung zu groß")
    except (UnidentifiedImageError, OSError) as e:
        raise HTTPException(400, "Bildabmessungen konnten nicht gelesen werden") from e

    return inhalt, sichere_ext


@router.post("/modelle/{modell_id}/foto", response_model=FotoOut, status_code=201)
async def upload_foto(
    modell_id: int,
    datei: UploadFile,
    session: AsyncSession = Depends(get_session),
) -> FotoOut:
    modell = await session.get(Modell, modell_id)
    if modell is None:
        raise HTTPException(404, "Modell nicht gefunden")

    inhalt, sichere_ext = await _validiere_bild(datei)

    settings.media_dir.mkdir(parents=True, exist_ok=True)
    dateiname = f"modell_{modell_id}_{uuid.uuid4().hex[:8]}{sichere_ext}"
    ziel = (settings.media_dir / dateiname).resolve()
    if not str(ziel).startswith(str(settings.media_dir.resolve())):
        raise HTTPException(400, "Ungültiger Zielpfad")
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


@router.post("/konvolut/{konvolut_id}/foto", response_model=FotoOut, status_code=201)
async def upload_konvolut_foto(
    konvolut_id: int,
    datei: UploadFile,
    session: AsyncSession = Depends(get_session),
) -> FotoOut:
    """Gesamtfoto eines Konvoluts (Auktionspaket, Sammelkauf)."""
    kon = await session.get(Konvolut, konvolut_id)
    if kon is None:
        raise HTTPException(404, "Konvolut nicht gefunden")

    ext = Path(datei.filename or "").suffix.lower()
    if ext not in ERLAUBT:
        raise HTTPException(400, f"Dateityp {ext or '?'} nicht erlaubt")

    inhalt, sichere_ext = await _validiere_bild(datei)
    settings.media_dir.mkdir(parents=True, exist_ok=True)
    dateiname = f"konvolut_{konvolut_id}_{uuid.uuid4().hex[:8]}{sichere_ext}"
    ziel = (settings.media_dir / dateiname).resolve()
    if not str(ziel).startswith(str(settings.media_dir.resolve())):
        raise HTTPException(400, "Ungültiger Zielpfad")
    ziel.write_bytes(inhalt)

    foto = Foto(konvolut_id=konvolut_id, pfad=f"media/{dateiname}", quelle="manuell")
    session.add(foto)
    await session.commit()
    await session.refresh(foto)
    return FotoOut.model_validate(foto)


@router.get("/konvolut/{konvolut_id}/fotos", response_model=list[FotoOut])
async def liste_konvolut_fotos(
    konvolut_id: int, session: AsyncSession = Depends(get_session)
) -> list[FotoOut]:
    rows = (await session.execute(
        select(Foto).where(Foto.konvolut_id == konvolut_id)
    )).scalars().all()
    return [FotoOut.model_validate(f) for f in rows]


@router.delete("/fotos/{foto_id}", status_code=204)
async def loesche_foto(
    foto_id: int, session: AsyncSession = Depends(get_session)
) -> None:
    foto = await session.get(Foto, foto_id)
    if foto is None:
        raise HTTPException(404, "Foto nicht gefunden")
    # Datei mitlöschen (best effort, nur innerhalb media/)
    ziel = (settings.media_dir.parent / foto.pfad).resolve()
    if str(ziel).startswith(str(settings.media_dir.resolve())) and ziel.exists():
        ziel.unlink()
    await session.delete(foto)
    await session.commit()
