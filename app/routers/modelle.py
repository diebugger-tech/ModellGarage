"""Router: Modelle — Liste, Suche, Filter, Detail, CRUD."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.models import Katalog, Modell
from app.schemas import (
    ModellCreate,
    ModellCreateVoll,
    ModellListe,
    ModellOut,
    ModellUpdate,
)

router = APIRouter(prefix="/api/modelle", tags=["modelle"])


@router.get("", response_model=ModellListe)
async def liste_modelle(
    session: AsyncSession = Depends(get_session),
    q: str | None = Query(None, description="Freitextsuche (Typ, Nr., Farbe, Bemerkung, Kaufjahr)"),
    hersteller: str | None = None,
    zustand: str | None = None,
    jahr: str | None = Query(None, description="Kaufjahr-Filter, z.B. '2015'"),
    limit: int = Query(50, le=200),
    offset: int = 0,
    sort: str = Query("id", pattern="^(id|bezahlt|schaetzwert|kaufdatum)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
) -> ModellListe:
    stmt = select(Modell).join(Katalog).options(selectinload(Modell.katalog))
    count_stmt = select(func.count(Modell.id)).join(Katalog)

    filters = []
    if q:
        like = f"%{q}%"
        filters.append(
            or_(
                Katalog.typ.ilike(like),
                Katalog.katalog_nr.ilike(like),
                Modell.farbe.ilike(like),
                Modell.bemerkung.ilike(like),
                Modell.kaufdatum.ilike(like),  # z.B. "2015" trifft das Kaufjahr
            )
        )
    if hersteller:
        filters.append(Katalog.hersteller == hersteller)
    if zustand:
        filters.append(Modell.zustand == zustand)
    if jahr:
        filters.append(func.substr(Modell.kaufdatum, 1, 4) == jahr)

    for f in filters:
        stmt = stmt.where(f)
        count_stmt = count_stmt.where(f)

    sort_col = {
        "id": Modell.id,
        "bezahlt": Modell.bezahlt,
        "schaetzwert": Modell.schaetzwert,
        "kaufdatum": Modell.kaufdatum,
    }[sort]
    stmt = stmt.order_by(sort_col.desc() if order == "desc" else sort_col.asc())
    stmt = stmt.limit(limit).offset(offset)

    total = (await session.execute(count_stmt)).scalar_one()
    items = (await session.execute(stmt)).scalars().all()
    return ModellListe(total=total, items=[ModellOut.model_validate(m) for m in items])


@router.get("/{modell_id}", response_model=ModellOut)
async def hole_modell(
    modell_id: int, session: AsyncSession = Depends(get_session)
) -> ModellOut:
    stmt = (
        select(Modell)
        .where(Modell.id == modell_id)
        .options(selectinload(Modell.katalog))
    )
    modell = (await session.execute(stmt)).scalar_one_or_none()
    if modell is None:
        raise HTTPException(404, "Modell nicht gefunden")
    return ModellOut.model_validate(modell)


@router.post("", response_model=ModellOut, status_code=201)
async def erstelle_modell(
    data: ModellCreate, session: AsyncSession = Depends(get_session)
) -> ModellOut:
    kat = await session.get(Katalog, data.katalog_id)
    if kat is None:
        raise HTTPException(400, "katalog_id existiert nicht")
    modell = Modell(**data.model_dump())
    session.add(modell)
    await session.commit()
    await session.refresh(modell, ["katalog"])
    return ModellOut.model_validate(modell)


@router.post("/voll", response_model=ModellOut, status_code=201)
async def erstelle_modell_voll(
    data: ModellCreateVoll, session: AsyncSession = Depends(get_session)
) -> ModellOut:
    """Manuell anlegen (eBay copy-paste). Katalog-Eintrag wird bei Bedarf erzeugt.

    get-or-create über (hersteller, katalog_nr): existiert die Kombination schon,
    wird angehängt (Dublette gewollt); sonst neuer Katalog-Eintrag (neuer
    Hersteller / neue Nummer). Werte (min/max) landen im Katalog.
    """
    nr = (data.katalog_nr or "").strip() or f"?/{data.hersteller}/{data.typ[:24]}"

    kat: Katalog | None = None
    stmt = select(Katalog).where(
        Katalog.hersteller == data.hersteller, Katalog.katalog_nr == nr
    )
    kat = (await session.execute(stmt)).scalar_one_or_none()

    if kat is None:
        kat = Katalog(
            hersteller=data.hersteller,
            katalog_nr=nr,
            typ=data.typ,
            serie=data.serie,
            min_euro=data.min_euro,
            max_euro=data.max_euro,
            quelle=data.quelle,
        )
        session.add(kat)
        await session.flush()
    else:
        # Werte im Katalog ergänzen, falls dort noch leer und hier angegeben
        if kat.min_euro is None and data.min_euro is not None:
            kat.min_euro = data.min_euro
        if kat.max_euro is None and data.max_euro is not None:
            kat.max_euro = data.max_euro

    modell = Modell(
        katalog_id=kat.id,
        farbe=data.farbe,
        zustand=data.zustand,
        bemerkung=data.bemerkung,
        bezahlt=data.bezahlt,
        schaetzwert=data.schaetzwert,
        kaufdatum=data.kaufdatum,
        anzahl=data.anzahl,
        konvolut_id=data.konvolut_id,
    )
    session.add(modell)
    await session.commit()
    await session.refresh(modell, ["katalog"])
    return ModellOut.model_validate(modell)


@router.patch("/{modell_id}", response_model=ModellOut)
async def aktualisiere_modell(
    modell_id: int, data: ModellUpdate, session: AsyncSession = Depends(get_session)
) -> ModellOut:
    stmt = (
        select(Modell)
        .where(Modell.id == modell_id)
        .options(selectinload(Modell.katalog))
    )
    modell = (await session.execute(stmt)).scalar_one_or_none()
    if modell is None:
        raise HTTPException(404, "Modell nicht gefunden")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(modell, k, v)
    await session.commit()
    await session.refresh(modell, ["katalog"])
    return ModellOut.model_validate(modell)


@router.delete("/{modell_id}", status_code=204)
async def loesche_modell(
    modell_id: int, session: AsyncSession = Depends(get_session)
) -> None:
    modell = await session.get(Modell, modell_id)
    if modell is None:
        raise HTTPException(404, "Modell nicht gefunden")
    await session.delete(modell)
    await session.commit()
