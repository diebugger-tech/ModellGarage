"""Regressionstest: die private Sammler-Excel muss immer importierbar bleiben.

Wird übersprungen, wenn die Datei fehlt (sie ist gitignored und nicht auf
GitHub) — so bleibt CI ohne die private Datei grün, aber lokal / auf Andreas'
Rechner schlägt der Test an, sobald ein Feature den Import bricht.
"""
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models import Katalog, Modell

EXCEL = Path(__file__).resolve().parents[1] / "2026-06-05 Modelle.xlsx"

pytestmark = pytest.mark.skipif(
    not EXCEL.exists(), reason="private Sammler-Excel nicht vorhanden"
)


@pytest.mark.asyncio
async def test_excel_import_kennzahlen(tmp_path):
    from app.services.excel_import import importiere_excel

    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'import.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as session:
        stats = await importiere_excel(session, EXCEL)

    # Import-Statistik (großzügige Untergrenzen, damit kleine Datenpflege okay ist)
    assert stats["modelle"] > 6000
    assert stats["katalog_neu"] > 3000
    assert stats["blaetter"] >= 15

    async with Session() as session:
        n_modelle = (await session.execute(select(func.count(Modell.id)))).scalar_one()
        hersteller = set(
            (await session.execute(select(Katalog.hersteller).distinct())).scalars().all()
        )

    assert n_modelle > 6000
    # Kern-Hersteller müssen erkannt worden sein
    assert {"Wiking", "Siku", "Majorette"} <= hersteller
    await engine.dispose()
