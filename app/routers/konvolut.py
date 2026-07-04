"""Router: Konvolut-Handling — Sammelkäufe (Auktionspakete).

Kernfeature (siehe AGENTS.md): Ein Konvolut ist ein Kauf mehrerer Autos in einer
Auktion. Eltern-Datensatz (Gesamtpreis) + Kind-Modelle. Der rechnerische
Einzelpreis wird NACH KATALOG-SCHÄTZWERT GEWICHTET verteilt — nicht stumpf
Gesamtpreis / Anzahl. So bekommt ein 80€-Auto einen größeren Anteil als ein 5€-Auto.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.models import Katalog, Konvolut, Modell
from app.schemas import (
    KonvolutCreate,
    KonvolutMitKindern,
    KonvolutOut,
    ModellCreateVoll,
    ModellOut,
)

router = APIRouter(prefix="/api/konvolut", tags=["konvolut"])


def _gewichte_preise(gesamtpreis: float, kinder: list[Modell]) -> dict[int, float]:
    """Verteilt den Gesamtpreis gewichtet nach Katalog-Schätzwert auf die Kinder.

    Gewicht pro Kind = (min+max)/2 aus dem Katalog (Fallback: max, min, oder 1).
    Fehlen alle Katalogwerte, wird gleichmäßig verteilt.
    Rückgabe: {modell_id: anteiliger_preis}.
    """
    def gewicht(m: Modell) -> float:
        k = m.katalog
        if k is None:
            return 1.0
        werte = [v for v in (k.min_euro, k.max_euro) if v is not None]
        if len(werte) == 2:
            return (float(werte[0]) + float(werte[1])) / 2
        if werte:
            return float(werte[0])
        return 1.0

    gewichte = {m.id: gewicht(m) for m in kinder}
    summe = sum(gewichte.values())
    if summe <= 0:
        # gleichmäßig
        n = len(kinder) or 1
        return {m.id: round(gesamtpreis / n, 2) for m in kinder}
    return {mid: round(gesamtpreis * g / summe, 2) for mid, g in gewichte.items()}


async def _lade_konvolut(session: AsyncSession, kid: int) -> Konvolut:
    stmt = (
        select(Konvolut)
        .where(Konvolut.id == kid)
        .options(selectinload(Konvolut.modelle).selectinload(Modell.katalog))
    )
    kon = (await session.execute(stmt)).scalar_one_or_none()
    if kon is None:
        raise HTTPException(404, "Konvolut nicht gefunden")
    return kon


@router.get("", response_model=list[KonvolutMitKindern])
async def liste_konvolute(session: AsyncSession = Depends(get_session)) -> list[KonvolutMitKindern]:
    stmt = (
        select(Konvolut)
        .options(selectinload(Konvolut.modelle).selectinload(Modell.katalog))
        .order_by(Konvolut.id.desc())
    )
    konvolute = (await session.execute(stmt)).scalars().all()
    out = []
    for k in konvolute:
        out.append(KonvolutMitKindern(
            id=k.id, quelle=k.quelle, gesamtpreis=float(k.gesamtpreis) if k.gesamtpreis else None,
            datum=k.datum,
            kinder=[ModellOut.model_validate(m) for m in k.modelle],
            anzahl_kinder=len(k.modelle),
        ))
    return out


@router.get("/{kid}", response_model=KonvolutMitKindern)
async def hole_konvolut(kid: int, session: AsyncSession = Depends(get_session)) -> KonvolutMitKindern:
    k = await _lade_konvolut(session, kid)
    return KonvolutMitKindern(
        id=k.id, quelle=k.quelle, gesamtpreis=float(k.gesamtpreis) if k.gesamtpreis else None,
        datum=k.datum,
        kinder=[ModellOut.model_validate(m) for m in k.modelle],
        anzahl_kinder=len(k.modelle),
    )


@router.post("", response_model=KonvolutOut, status_code=201)
async def erstelle_konvolut(
    data: KonvolutCreate, session: AsyncSession = Depends(get_session)
) -> KonvolutOut:
    kon = Konvolut(quelle=data.quelle, gesamtpreis=data.gesamtpreis, datum=data.datum)
    session.add(kon)
    await session.commit()
    await session.refresh(kon)
    return KonvolutOut.model_validate(kon)


@router.post("/{kid}/modell/{modell_id}", response_model=KonvolutMitKindern)
async def kind_zuordnen(
    kid: int, modell_id: int, session: AsyncSession = Depends(get_session)
) -> KonvolutMitKindern:
    """Ein bestehendes Modell diesem Konvolut zuordnen (als Kind)."""
    kon = await session.get(Konvolut, kid)
    if kon is None:
        raise HTTPException(404, "Konvolut nicht gefunden")
    modell = await session.get(Modell, modell_id)
    if modell is None:
        raise HTTPException(404, "Modell nicht gefunden")
    modell.konvolut_id = kid
    await session.commit()
    return await hole_konvolut(kid, session)


@router.post("/{kid}/modell-voll", response_model=KonvolutMitKindern)
async def kind_anlegen_voll(
    kid: int,
    data: ModellCreateVoll,
    session: AsyncSession = Depends(get_session),
) -> KonvolutMitKindern:
    """Neues Modell + Katalog anlegen und direkt diesem Konvolut zuordnen.

    Praktisch für Konvolut-Erfassung: man tippt Hersteller/Katalog-Nr./Typ für
    jedes Auto aus dem Auktionspaket ein, ohne vorher in die Galerie zu springen.
    """
    kon = await session.get(Konvolut, kid)
    if kon is None:
        raise HTTPException(404, "Konvolut nicht gefunden")

    nr = (data.katalog_nr or "").strip()
    if not nr:
        nr = f"?/{data.hersteller}/{data.typ[:24]}"

    kat = (await session.execute(
        select(Katalog).where(
            Katalog.hersteller == data.hersteller,
            Katalog.katalog_nr == nr,
        )
    )).scalar_one_or_none()

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
        kaufdatum=data.kaufdatum or kon.datum,
        anzahl=data.anzahl,
        konvolut_id=kid,
    )
    session.add(modell)
    await session.commit()
    await session.refresh(modell, ["katalog"])
    return await hole_konvolut(kid, session)


@router.delete("/{kid}/modell/{modell_id}", response_model=KonvolutMitKindern)
async def kind_entfernen(
    kid: int, modell_id: int, session: AsyncSession = Depends(get_session)
) -> KonvolutMitKindern:
    modell = await session.get(Modell, modell_id)
    if modell is None or modell.konvolut_id != kid:
        raise HTTPException(404, "Modell nicht in diesem Konvolut")
    modell.konvolut_id = None
    await session.commit()
    return await hole_konvolut(kid, session)


@router.post("/{kid}/preise-verteilen")
async def preise_verteilen(kid: int, session: AsyncSession = Depends(get_session)) -> dict:
    """Gesamtpreis gewichtet nach Katalog-Schätzwert auf die Kinder verteilen.

    Schreibt den anteiligen Preis in `modell.bezahlt` jedes Kindes.
    """
    kon = await _lade_konvolut(session, kid)
    if not kon.modelle:
        raise HTTPException(400, "Konvolut hat keine zugeordneten Modelle")
    if not kon.gesamtpreis:
        raise HTTPException(400, "Konvolut hat keinen Gesamtpreis")

    anteile = _gewichte_preise(float(kon.gesamtpreis), list(kon.modelle))
    for m in kon.modelle:
        m.bezahlt = anteile.get(m.id, m.bezahlt)
    await session.commit()

    return {
        "ok": True,
        "gesamtpreis": float(kon.gesamtpreis),
        "verteilt_auf": len(kon.modelle),
        "anteile": [
            {"modell_id": m.id, "typ": m.katalog.typ if m.katalog else "?",
             "bezahlt": anteile.get(m.id)}
            for m in kon.modelle
        ],
    }


@router.delete("/{kid}", status_code=204)
async def loesche_konvolut(kid: int, session: AsyncSession = Depends(get_session)) -> None:
    """Konvolut löschen. Kinder bleiben erhalten (konvolut_id → NULL per FK)."""
    kon = await session.get(Konvolut, kid)
    if kon is None:
        raise HTTPException(404, "Konvolut nicht gefunden")
    await session.delete(kon)
    await session.commit()
