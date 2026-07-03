"""Router: Statistik & Meta (Hersteller-Liste, Summen)."""
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

    # Summe Katalogwerte über die tatsächlich vorhandenen Modelle (via Join)
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
