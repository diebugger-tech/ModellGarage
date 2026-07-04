"""Router: Katalog-Abgleich — Kandidaten zu einer Nummer/Typ vorschlagen.

Read-only auf der vorhandenen (aus der Excel importierten) katalog-Tabelle.
Kernnutzen: Beim Anlegen die erkannte Katalog-Nr. gegen den Katalog prüfen und
Typ + Min/Max-Wert vorschlagen — der Mensch bestätigt (AGENTS.md).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models import Katalog
from app.schemas import KatalogOut

router = APIRouter(prefix="/api/katalog", tags=["katalog"])


@router.get("/kandidaten", response_model=list[KatalogOut])
async def kandidaten(
    hersteller: str | None = None,
    katalog_nr: str | None = None,
    typ: str | None = None,
    limit: int = 3,
    session: AsyncSession = Depends(get_session),
) -> list[KatalogOut]:
    """Bis zu ``limit`` Katalog-Kandidaten in Prioritätsreihenfolge:

    1. exakte Nr. beim gleichen Hersteller
    2. Nr.-Präfix beim gleichen Hersteller
    3. exakte Nr. bei beliebigem Hersteller
    4. Typ-Ähnlichkeit beim gleichen Hersteller
    5. Typ-Ähnlichkeit bei beliebigem Hersteller
    """
    treffer: list[Katalog] = []
    gesehen: set[int] = set()

    async def add(stmt) -> None:
        if len(treffer) >= limit:
            return
        rows = (await session.execute(stmt.limit(limit * 2))).scalars().all()
        for k in rows:
            if k.id not in gesehen:
                gesehen.add(k.id)
                treffer.append(k)
                if len(treffer) >= limit:
                    break

    nr = (katalog_nr or "").strip()
    h = (hersteller or "").strip()
    t = (typ or "").strip()

    if nr:
        if h:
            await add(select(Katalog).where(Katalog.hersteller == h, Katalog.katalog_nr == nr))
            await add(select(Katalog).where(Katalog.hersteller == h, Katalog.katalog_nr.like(f"{nr}%")))
        await add(select(Katalog).where(Katalog.katalog_nr == nr))
    if t and len(treffer) < limit:
        like = f"%{t}%"
        if h:
            await add(select(Katalog).where(Katalog.hersteller == h, Katalog.typ.ilike(like)))
        await add(select(Katalog).where(Katalog.typ.ilike(like)))

    return [KatalogOut.model_validate(k) for k in treffer[:limit]]
