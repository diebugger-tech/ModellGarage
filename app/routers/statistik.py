"""Router: Statistik & Meta — Kennzahlen, Zeitreihen, Verteilungen, Top-Listen."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models import Katalog, Modell
from app.schemas import StatistikOut

router = APIRouter(prefix="/api/statistik", tags=["statistik"])


@router.get("", response_model=StatistikOut)
async def statistik(session: AsyncSession = Depends(get_session)) -> StatistikOut:
    anzahl_modelle = (await session.execute(select(func.count(Modell.id)))).scalar_one()
    anzahl_katalog = (await session.execute(select(func.count(Katalog.id)))).scalar_one()
    summe_bezahlt = (await session.execute(select(func.coalesce(func.sum(Modell.bezahlt), 0)))).scalar_one()
    summe_schaetz = (await session.execute(select(func.coalesce(func.sum(Modell.schaetzwert), 0)))).scalar_one()

    smin = (await session.execute(
        select(func.coalesce(func.sum(Katalog.min_euro), 0)).select_from(Modell).join(Katalog)
    )).scalar_one()
    smax = (await session.execute(
        select(func.coalesce(func.sum(Katalog.max_euro), 0)).select_from(Modell).join(Katalog)
    )).scalar_one()

    hersteller_rows = (await session.execute(
        select(Katalog.hersteller, func.count(Modell.id))
        .select_from(Modell).join(Katalog)
        .group_by(Katalog.hersteller)
        .order_by(func.count(Modell.id).desc())
    )).all()

    return StatistikOut(
        anzahl_modelle=anzahl_modelle,
        anzahl_katalog=anzahl_katalog,
        summe_bezahlt=float(summe_bezahlt or 0),
        summe_schaetzwert=float(summe_schaetz or 0),
        summe_min=float(smin or 0),
        summe_max=float(smax or 0),
        hersteller={h: n for h, n in hersteller_rows},
    )


@router.get("/hersteller", response_model=list[str])
async def hersteller_liste(session: AsyncSession = Depends(get_session)) -> list[str]:
    rows = (await session.execute(
        select(Katalog.hersteller).distinct().order_by(Katalog.hersteller)
    )).scalars().all()
    return list(rows)


@router.get("/jahre", response_model=list[str])
async def jahre(session: AsyncSession = Depends(get_session)) -> list[str]:
    """Distinct Kaufjahre (für das Jahr-Dropdown), neueste zuerst."""
    jahr = func.substr(Modell.kaufdatum, 1, 4)
    rows = (await session.execute(
        select(jahr)
        .where(Modell.kaufdatum.isnot(None))
        .where(func.length(Modell.kaufdatum) >= 4)
        .distinct()
        .order_by(jahr.desc())
    )).scalars().all()
    return [j for j in rows if j and j.isdigit()]


@router.get("/dashboard")
async def dashboard(session: AsyncSession = Depends(get_session)) -> dict:
    """Aggregierte Daten für die Statistik-Grafiken (ein Call, viele Charts)."""
    # --- Zukäufe pro Jahr (Anzahl + Summe bezahlt) ---
    # kaufdatum ist ISO 'YYYY-MM-DD' → Jahr = substr(1,4)
    jahr = func.substr(Modell.kaufdatum, 1, 4)
    jahr_rows = (await session.execute(
        select(
            jahr.label("jahr"),
            func.count(Modell.id),
            func.coalesce(func.sum(Modell.bezahlt), 0),
        )
        .where(Modell.kaufdatum.isnot(None))
        .where(func.length(Modell.kaufdatum) >= 4)
        .group_by(jahr)
        .order_by(jahr)
    )).all()
    zukaeufe_pro_jahr = [
        {"jahr": j, "anzahl": n, "summe": float(s or 0)}
        for j, n, s in jahr_rows if j and j.isdigit()
    ]

    # --- Kumulierte Wertentwicklung (Summe bezahlt aufaddiert über Jahre) ---
    kumuliert = []
    laufend = 0.0
    for e in zukaeufe_pro_jahr:
        laufend += e["summe"]
        kumuliert.append({"jahr": e["jahr"], "wert": round(laufend, 2)})

    # --- Verteilung nach Hersteller (Top 10 + Rest) ---
    h_rows = (await session.execute(
        select(Katalog.hersteller, func.count(Modell.id))
        .select_from(Modell).join(Katalog)
        .group_by(Katalog.hersteller)
        .order_by(func.count(Modell.id).desc())
    )).all()
    top_h = [{"name": h, "anzahl": n} for h, n in h_rows[:10]]
    rest = sum(n for _, n in h_rows[10:])
    if rest:
        top_h.append({"name": "Sonstige", "anzahl": rest})

    # --- Zustand-Verteilung ---
    z_rows = (await session.execute(
        select(func.coalesce(Modell.zustand, "unbekannt"), func.count(Modell.id))
        .group_by(Modell.zustand)
    )).all()
    zustand = [{"zustand": z, "anzahl": n} for z, n in z_rows]

    # --- Preis-Histogramm (bezahlt, in Klassen) ---
    grenzen = [0, 5, 10, 20, 40, 75, 150, 10000]
    labels = ["<5", "5–10", "10–20", "20–40", "40–75", "75–150", "150+"]
    hist = [0] * (len(grenzen) - 1)
    preise = (await session.execute(
        select(Modell.bezahlt).where(Modell.bezahlt.isnot(None))
    )).scalars().all()
    for p in preise:
        if p is None:
            continue
        pv = float(p)
        for i in range(len(grenzen) - 1):
            if grenzen[i] <= pv < grenzen[i + 1]:
                hist[i] += 1
                break
    histogramm = [{"klasse": labels[i], "anzahl": hist[i]} for i in range(len(labels))]

    # --- Top 10 teuerste Modelle (nach bezahlt) ---
    top_rows = (await session.execute(
        select(Modell.id, Katalog.hersteller, Katalog.typ, Modell.bezahlt)
        .select_from(Modell).join(Katalog)
        .where(Modell.bezahlt.isnot(None))
        .order_by(Modell.bezahlt.desc())
        .limit(10)
    )).all()
    top_teuer = [
        {"id": i, "hersteller": h, "typ": t, "bezahlt": float(b or 0)}
        for i, h, t, b in top_rows
    ]

    return {
        "zukaeufe_pro_jahr": zukaeufe_pro_jahr,
        "wertentwicklung": kumuliert,
        "hersteller_verteilung": top_h,
        "zustand_verteilung": zustand,
        "preis_histogramm": histogramm,
        "top_teuerste": top_teuer,
    }
