"""Pydantic V2 Schemas für Request/Response."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class KatalogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    hersteller: str
    katalog_nr: str
    typ: str
    serie: str | None = None
    min_euro: float | None = None
    max_euro: float | None = None
    quelle: str | None = None


class KonvolutOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    quelle: str | None = None
    gesamtpreis: float | None = None
    datum: str | None = None


class KonvolutCreate(BaseModel):
    quelle: str | None = None
    gesamtpreis: float | None = None
    datum: str | None = None


class KonvolutMitKindern(KonvolutOut):
    kinder: list["ModellOut"] = []
    anzahl_kinder: int = 0


class FotoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    modell_id: int | None = None
    konvolut_id: int | None = None
    pfad: str
    quelle: str


class ModellOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    katalog_id: int
    farbe: str | None = None
    zustand: str | None = None
    bemerkung: str | None = None
    bezahlt: float | None = None
    schaetzwert: float | None = None
    kaufdatum: str | None = None
    anzahl: int
    konvolut_id: int | None = None
    katalog: KatalogOut | None = None
    foto_url: str | None = None  # erstes Foto (Galerie-Thumbnail), z.B. "/media/modell_1_ab12cd34.jpg"


class ModellCreate(BaseModel):
    katalog_id: int
    farbe: str | None = None
    zustand: str | None = None
    bemerkung: str | None = None
    bezahlt: float | None = None
    schaetzwert: float | None = None
    kaufdatum: str | None = None
    anzahl: int = 1
    konvolut_id: int | None = None


class ModellCreateVoll(BaseModel):
    """Modell manuell anlegen (z.B. eBay copy-paste) — Katalog inline.

    Legt bei Bedarf einen neuen Katalog-Eintrag an (neuer Hersteller / neue Nr.).
    Felder entsprechen 1:1 der Sammler-Excel.
    """
    # Katalog-Teil (Identität + Werte)
    hersteller: str
    katalog_nr: str | None = None
    typ: str
    serie: str | None = None
    min_euro: float | None = None
    max_euro: float | None = None
    quelle: str | None = None
    # Modell-Teil (das konkrete Exemplar)
    farbe: str | None = None
    zustand: str | None = None
    bemerkung: str | None = None
    bezahlt: float | None = None          # Einkaufspreis
    schaetzwert: float | None = None
    kaufdatum: str | None = None
    anzahl: int = 1
    konvolut_id: int | None = None


class ModellUpdate(BaseModel):
    farbe: str | None = None
    zustand: str | None = None
    bemerkung: str | None = None
    bezahlt: float | None = None
    schaetzwert: float | None = None
    kaufdatum: str | None = None
    anzahl: int | None = None
    konvolut_id: int | None = None


class ModellListe(BaseModel):
    total: int
    items: list[ModellOut]


class StatistikOut(BaseModel):
    anzahl_modelle: int
    anzahl_katalog: int
    summe_bezahlt: float
    summe_schaetzwert: float
    summe_min: float
    summe_max: float
    hersteller: dict[str, int]


# Forward-Ref in KonvolutMitKindern.kinder auflösen (ModellOut ist jetzt bekannt)
KonvolutMitKindern.model_rebuild()
