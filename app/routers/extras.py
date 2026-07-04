"""Router: Extras — Dubletten-Check, Wunschliste (fehlende Nummern), Backup.

Alles read-only-Analysen auf der vorhandenen Sammlung + DB-Backup-Download.
"""
from __future__ import annotations

import re

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.models import Katalog, Modell

router = APIRouter(prefix="/api/extras", tags=["extras"])


@router.get("/dubletten")
async def dubletten(
    hersteller: str | None = None, session: AsyncSession = Depends(get_session)
) -> dict:
    """Katalog-Nummern, die mehrfach in der Sammlung vorkommen (echte Dubletten)."""
    stmt = (
        select(
            Katalog.hersteller, Katalog.katalog_nr, Katalog.typ,
            func.count(Modell.id).label("anzahl"),
        )
        .select_from(Modell).join(Katalog)
        .group_by(Katalog.id)
        .having(func.count(Modell.id) > 1)
        .order_by(func.count(Modell.id).desc())
    )
    if hersteller:
        stmt = stmt.where(Katalog.hersteller == hersteller)
    rows = (await session.execute(stmt)).all()
    return {
        "anzahl": len(rows),
        "dubletten": [
            {"hersteller": h, "katalog_nr": nr, "typ": t, "vorhanden": n}
            for h, nr, t, n in rows
        ],
    }


@router.get("/dubletten-check")
async def dubletten_check(
    hersteller: str, katalog_nr: str, session: AsyncSession = Depends(get_session)
) -> dict:
    """Prüft beim Anlegen: besitzt der Sammler diese Nr. schon? (für Warnung)."""
    stmt = (
        select(func.count(Modell.id))
        .select_from(Modell).join(Katalog)
        .where(Katalog.hersteller == hersteller, Katalog.katalog_nr == katalog_nr)
    )
    n = (await session.execute(stmt)).scalar_one()
    return {"hersteller": hersteller, "katalog_nr": katalog_nr, "vorhanden": n}


def _nr_teile(nr: str) -> tuple[int, str] | None:
    """Zerlegt eine Wiking-Nr. wie '30/6K.' in (basis=30, rest='6K.')."""
    m = re.match(r"^(\d+)/(.+)$", nr.strip())
    if not m:
        return None
    return int(m.group(1)), m.group(2)


@router.get("/wunschliste")
async def wunschliste(
    hersteller: str = "Wiking", session: AsyncSession = Depends(get_session)
) -> dict:
    """Lücken in der Nummernfolge finden (was fehlt zwischen vorhandenen Nummern).

    Mehrere Hersteller können kommagetrennt übergeben werden.
    """
    hersteller_liste = [h.strip() for h in hersteller.split(",") if h.strip()]
    if not hersteller_liste:
        hersteller_liste = ["Wiking"]

    rows = (await session.execute(
        select(Katalog.hersteller, Katalog.katalog_nr).distinct()
        .select_from(Modell).join(Katalog)
        .where(Katalog.hersteller.in_(hersteller_liste))
    )).all()

    pro_hersteller: dict[str, set[int]] = {h: set() for h in hersteller_liste}
    for h, nr in rows:
        teile = _nr_teile(nr)
        if teile:
            pro_hersteller[h].add(teile[0])

    ergebnisse = {}
    for h, basen in pro_hersteller.items():
        if not basen:
            ergebnisse[h] = {"vorhandene_basen": 0, "bereich": None, "luecken": []}
            continue
        lo, hi = min(basen), max(basen)
        kandidaten = range(lo, hi + 1)
        luecken = [b for b in kandidaten if b not in basen and b % 10 == 0]
        ergebnisse[h] = {
            "vorhandene_basen": len(basen),
            "bereich": {"von": lo, "bis": hi},
            "luecken": luecken[:200],
        }

    return {
        "hersteller": hersteller_liste,
        "gesamt": ergebnisse,
        "hinweis": "Basis-Nummern (vor dem '/'), die in deiner Sammlung fehlen. "
                   "Grobe Orientierung — nicht jede Nummer existiert im Katalog.",
    }


@router.get("/backup")
async def backup() -> FileResponse:
    """Die SQLite-DB als Datei herunterladen (Backup-Knopf)."""
    from datetime import datetime

    db_path = settings.sqlite_path
    name = f"modellgarage_backup_{datetime.now():%Y-%m-%d}.db"
    return FileResponse(
        db_path, media_type="application/octet-stream", filename=name,
    )
