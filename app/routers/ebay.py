"""Router: eBay-Text parsen (Formular vorausfüllen). Kein Developer-Account.

eBay blockt Server-Fetch (403) → der Nutzer fügt Titel+Preis aus seinem Browser
ein, wir parsen nur Text. Nichts wird automatisch gespeichert (nur Vorschlag).
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.ebay_parse import parse_text

router = APIRouter(prefix="/api/ebay", tags=["ebay"])


class EbayTextIn(BaseModel):
    titel: str
    extra: str = ""          # optional: Preis-/Zustandszeile mitkopiert
    beschreibung: str = ""   # optional: eBay-Artikelbeschreibung (Nr., Farbe …)


@router.post("/parse-text")
async def ebay_parse_text(data: EbayTextIn) -> dict:
    """Eingefügten eBay-Titel (+ optional Preis + Beschreibung) → Feld-Vorschläge."""
    try:
        return parse_text(data.titel, data.extra, data.beschreibung)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
