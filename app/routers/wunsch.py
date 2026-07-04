"""Router: manuelle Wunschliste (Merkliste gesuchter Nummern).

Unabhängig vom Lücken-Finder in ``extras.py`` — hier trägt der Sammler selbst
ein, was er noch sucht, und markiert es später als 'gekauft'.
"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models import Wunsch

router = APIRouter(prefix="/api/wunsch", tags=["wunsch"])

STATUS = ("gesucht", "gekauft")


class WunschIn(BaseModel):
    hersteller: str
    katalog_nr: str | None = None
    typ: str | None = None
    notiz: str | None = None
    max_euro: float | None = None


class WunschPatch(BaseModel):
    status: str | None = None
    notiz: str | None = None
    typ: str | None = None
    max_euro: float | None = None


def _out(w: Wunsch) -> dict:
    return {
        "id": w.id,
        "hersteller": w.hersteller,
        "katalog_nr": w.katalog_nr,
        "typ": w.typ,
        "notiz": w.notiz,
        "max_euro": float(w.max_euro) if w.max_euro is not None else None,
        "status": w.status,
        "erstellt_am": w.erstellt_am,
    }


@router.get("")
async def liste(
    status: str | None = None, session: AsyncSession = Depends(get_session)
) -> list[dict]:
    """Alle Wünsche, optional nach Status gefiltert. 'gesucht' zuerst, neueste oben."""
    stmt = select(Wunsch).order_by(Wunsch.status, Wunsch.id.desc())
    if status:
        stmt = stmt.where(Wunsch.status == status)
    rows = (await session.execute(stmt)).scalars().all()
    return [_out(w) for w in rows]


@router.post("", status_code=201)
async def anlegen(
    data: WunschIn, session: AsyncSession = Depends(get_session)
) -> dict:
    if not data.hersteller.strip():
        raise HTTPException(400, "Hersteller ist Pflicht")
    w = Wunsch(
        hersteller=data.hersteller.strip(),
        katalog_nr=(data.katalog_nr or "").strip() or None,
        typ=(data.typ or "").strip() or None,
        notiz=(data.notiz or "").strip() or None,
        max_euro=data.max_euro,
        status="gesucht",
        erstellt_am=date.today().isoformat(),
    )
    session.add(w)
    await session.commit()
    await session.refresh(w)
    return _out(w)


@router.patch("/{wid}")
async def aktualisieren(
    wid: int, data: WunschPatch, session: AsyncSession = Depends(get_session)
) -> dict:
    w = await session.get(Wunsch, wid)
    if not w:
        raise HTTPException(404, "Wunsch nicht gefunden")
    if data.status is not None:
        if data.status not in STATUS:
            raise HTTPException(400, f"status muss {STATUS} sein")
        w.status = data.status
    if data.notiz is not None:
        w.notiz = data.notiz.strip() or None
    if data.typ is not None:
        w.typ = data.typ.strip() or None
    if data.max_euro is not None:
        w.max_euro = data.max_euro
    await session.commit()
    await session.refresh(w)
    return _out(w)


@router.delete("/{wid}", status_code=204)
async def loeschen(wid: int, session: AsyncSession = Depends(get_session)) -> None:
    w = await session.get(Wunsch, wid)
    if not w:
        raise HTTPException(404, "Wunsch nicht gefunden")
    await session.delete(w)
    await session.commit()
