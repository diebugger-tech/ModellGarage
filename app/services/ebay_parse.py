"""eBay-Angebot → Modell-Felder vorausfüllen.

WICHTIG: eBay blockt Server-seitige HTTP-Abfragen zuverlässig mit 403
(Bot-Erkennung auf Datacenter-IPs). Verifiziert 2026-07: direkter Fetch,
.com/.de, und Reader-Proxy (r.jina.ai) alle 403.

→ Deshalb der robuste Weg: Der Nutzer kopiert **Titel (+ optional Preis)** aus
seinem eigenen Browser und fügt sie ein. Dieses Modul parst nur Text — kein
Netzwerk, keine Blockade. Der Nutzer prüft/korrigiert die Vorschläge immer selbst.

Optional (`versuche_fetch`) gibt es noch einen URL-Fetch-Versuch für den Fall,
dass die App lokal mit Wohn-IP läuft — schlägt bei Datacenter-IP aber fehl.
"""
from __future__ import annotations

import re
from html import unescape
from typing import Any

# Bekannte Modellauto-Hersteller (für Titel-Heuristik). Längere/spezifischere
# Namen zuerst, damit "Matchbox Superfast" nicht nur "Matchbox" trifft.
HERSTELLER = [
    "Wiking", "Siku", "Majorette", "Matchbox", "Herpa", "Schuco", "Brekina",
    "Rietze", "Busch", "Märklin", "Marklin", "Norev", "Corgi", "Dinky",
    "Lesney", "Playmobil", "Bburago", "Minichamps", "Kibri", "Faller",
    "Roco", "Vollmer", "Preiser", "Gama", "Tekno", "Lion Car",
]

ZUSTAND_KEYS = {
    "z0": ["neuwertig", "unbespielt", "ungeöffnet", "mint", "fabrikneu"],
    "z2": ["bespielt", "gebraucht", "defekt", "beschädigt", "kratzer",
           "played", "used", "stark"],
    # 'neu'/'ovp' allein → oft z0/z1, wird als z1 belassen (Default None)
}

_MASSSTAB_RE = re.compile(r'\b1[:/](\d{2,3})\b')
_PREIS_RE = re.compile(r'(?:EUR|€)\s*([0-9]+(?:[.,][0-9]{1,2})?)', re.IGNORECASE)

# Katalog-Nr. mit Kontextwort ("Wiking-Nr. 30/6K.", "Kat.-Nr: 1050", "Art.Nr 8/1")
_NR_KONTEXT_RE = re.compile(
    r'(?:wiking|kat(?:alog)?|art(?:ikel)?)?[.\-\s]*nr\.?\s*:?\s*'
    r'([0-9]{1,4}(?:[/\-][0-9]{1,3})?\s?[A-Za-z]?\.?)',
    re.IGNORECASE,
)
# Wiking-typische Nummer ohne Kontext: "30/6K.", "30/6", "8/1" — aber KEIN Maßstab (1/87)
_NR_SLASH_RE = re.compile(r'(?<![0-9:/])([0-9]{1,3}/[0-9]{1,3}\s?[A-Za-z]?\.?)')
# Bloße Nummer (Siku/Majorette-Stil) — nur als Fallback auf dem kurzen Titel
_NR_BARE_RE = re.compile(r'\b(\d{3,5}[A-Za-z]?)\b')
# Explizite Zustandsangabe der Sammler-Skala: "Z1", "z 2", "Z0"
_ZUSTAND_RE = re.compile(r'\bz\s?([012])\b', re.IGNORECASE)

# Bekannte Lackfarben (inkl. typischer Wiking-Kompositfarben). Präfixe hell/dunkel
# werden separat erlaubt. Längere/spezifischere zuerst.
_FARBE_BASIS = [
    "blaugrau", "graugrün", "graugruen", "silbergrau", "rotbraun", "gelbgrün",
    "gelbgruen", "olivgrün", "olivgruen", "elfenbein", "anthrazit", "bordeaux",
    "türkis", "tuerkis", "violett", "petrol", "creme", "crème", "beige",
    "silber", "gold", "schwarz", "weiß", "weiss", "grau", "braun", "blau",
    "grün", "gruen", "gelb", "rot", "orange", "oliv", "ocker", "lila",
    "rosa", "pink",
]
_FARBE_RE = re.compile(
    r'\b((?:hell|dunkel|blass|licht)?[\s-]?(?:' + "|".join(_FARBE_BASIS) + r'))\b',
    re.IGNORECASE,
)


def _preis(text: str) -> float | None:
    m = _PREIS_RE.search(text)
    if not m:
        # auch nackte Zahl mit Dezimalstellen
        m2 = re.search(r'\b([0-9]{1,4}[.,][0-9]{2})\b', text)
        if not m2:
            return None
        val = m2.group(1)
    else:
        val = m.group(1)
    try:
        return round(float(val.replace(",", ".")), 2)
    except ValueError:
        return None


def _hersteller_und_typ(titel: str) -> tuple[str | None, str]:
    gefunden = None
    for h in HERSTELLER:
        if re.search(rf'\b{re.escape(h)}\b', titel, re.IGNORECASE):
            gefunden = h
            break
    typ = titel
    if gefunden:
        typ = re.sub(rf'\b{re.escape(gefunden)}\b', "", typ, flags=re.IGNORECASE)
    # eBay-Rauschen entfernen
    typ = re.sub(r'\b(H0|1[:/]\d{2,3}|OVP|NEU|TOP|SELTEN|RAR|KONVOLUT|RARITÄT|'
                 r'sammlung|modell(auto)?|spielzeug)\b', "", typ, flags=re.IGNORECASE)
    typ = _PREIS_RE.sub("", typ)
    typ = re.sub(r'[|–•]+', " ", typ)
    typ = re.sub(r'\s{2,}', " ", typ).strip(" ,-·\t")
    if gefunden and gefunden.lower() == "marklin":
        gefunden = "Märklin"
    return gefunden, typ or titel


def _zustand(text: str) -> str | None:
    # Explizite Sammler-Angabe ("Z1") hat Vorrang vor Stichwort-Heuristik.
    m = _ZUSTAND_RE.search(text)
    if m:
        return "z" + m.group(1)
    low = text.lower()
    for z, keys in ZUSTAND_KEYS.items():
        if any(k in low for k in keys):
            return z
    return None


def _massstab(text: str) -> str | None:
    m = _MASSSTAB_RE.search(text)
    return f"1:{m.group(1)}" if m else None


def _katalog_nr(text: str, massstab: str | None = None) -> str | None:
    """Katalog-/Wiking-Nr. aus Text ziehen. Kontextwort ("Nr.") bevorzugt,
    sonst Wiking-typische Schrägstrich-Nummer. Maßstab (1/87) wird ausgeschlossen."""
    massstab_slash = massstab.replace(":", "/") if massstab else None

    def _clean(raw: str) -> str:
        return re.sub(r'\s+', "", raw).strip()

    m = _NR_KONTEXT_RE.search(text)
    if m:
        cand = _clean(m.group(1))
        if cand and cand.lower() not in ("nr", ""):
            return cand
    for m in _NR_SLASH_RE.finditer(text):
        cand = _clean(m.group(1))
        # Maßstab wie "1/87" nicht als Katalog-Nr. missdeuten
        if massstab_slash and cand.rstrip(".").lower() == massstab_slash:
            continue
        if re.fullmatch(r'1/\d{2,3}', cand.rstrip(".")):
            continue
        return cand
    return None


def _katalog_nr_bare(titel: str, massstab: str | None = None) -> str | None:
    """Fallback: bloße Nummer (Siku/Majorette) — nur auf dem kurzen Titel, um
    Fehlgriffe in Fließtext zu vermeiden. Jahreszahlen/Maßstab ausgeschlossen."""
    mass_num = massstab.split(":")[1] if massstab else None
    for m in _NR_BARE_RE.finditer(titel):
        cand = m.group(1)
        digits = re.sub(r'\D', "", cand)
        if re.fullmatch(r'(?:19|20)\d{2}', digits):   # Jahreszahl
            continue
        if mass_num and digits == mass_num:
            continue
        return cand
    return None


def _farbe(text: str) -> str | None:
    m = _FARBE_RE.search(text)
    if not m:
        return None
    return re.sub(r'\s+', "", m.group(1)).lower()


def parse_text(titel: str, extra: str = "", beschreibung: str = "") -> dict[str, Any]:
    """Eingefügten eBay-Titel (+ optional Preiszeile + Artikelbeschreibung) → Felder.

    ``beschreibung`` ist die kopierte eBay-Artikelbeschreibung. Sie enthält oft
    die Katalog-/Wiking-Nr. und Farbe, die im Titel fehlen — genau die Felder,
    die aus einem Foto nicht ableitbar sind."""
    titel = unescape((titel or "").strip())
    extra = unescape((extra or "").strip())
    beschreibung = unescape((beschreibung or "").strip())
    if not titel:
        raise ValueError("Bitte den eBay-Titel einfügen")

    # Titel bleibt führend; Beschreibung reichert an (Nr., Farbe, Zustand).
    gesamt = "\n".join(p for p in (titel, extra, beschreibung) if p)
    # Nr./Farbe zuerst aus der Beschreibung (dort am zuverlässigsten), sonst Titel.
    nr_quelle = beschreibung or titel
    farb_quelle = "\n".join(p for p in (beschreibung, titel) if p)

    hersteller, typ = _hersteller_und_typ(titel)
    preis = _preis(extra) or _preis(beschreibung) or _preis(titel)
    zustand = _zustand(gesamt)
    massstab = _massstab(gesamt)
    katalog_nr = (_katalog_nr(nr_quelle, massstab)
                  or _katalog_nr(titel, massstab)
                  or _katalog_nr_bare(titel, massstab))
    farbe = _farbe(farb_quelle)

    bem_teile = []
    if massstab:
        bem_teile.append(f"Maßstab {massstab}")
    bem_teile.append("Quelle: eBay")
    bemerkung = "; ".join(bem_teile)

    return {
        "ok": True,
        "hersteller": hersteller,
        "typ": typ,
        "katalog_nr": katalog_nr,
        "farbe": farbe,
        "bezahlt": preis,          # Angebotspreis — Nutzer korrigiert auf Kaufpreis
        "zustand": zustand,
        "massstab": massstab,
        "bemerkung": bemerkung,
        "titel_roh": titel,
    }
