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
_NR_RE = re.compile(r'\b(\d{3,6}[A-Za-z]?)\b')  # grobe Artikel-/Katalognummer


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
    low = text.lower()
    for z, keys in ZUSTAND_KEYS.items():
        if any(k in low for k in keys):
            return z
    return None


def _massstab(text: str) -> str | None:
    m = _MASSSTAB_RE.search(text)
    return f"1:{m.group(1)}" if m else None


def parse_text(titel: str, extra: str = "") -> dict[str, Any]:
    """Eingefügten eBay-Titel (+ optional Beschreibung/Preiszeile) → Felder."""
    titel = unescape((titel or "").strip())
    extra = unescape((extra or "").strip())
    if not titel:
        raise ValueError("Bitte den eBay-Titel einfügen")

    gesamt = f"{titel}\n{extra}"
    hersteller, typ = _hersteller_und_typ(titel)
    preis = _preis(extra) or _preis(titel)
    zustand = _zustand(gesamt)
    massstab = _massstab(gesamt)

    bem_teile = []
    if massstab:
        bem_teile.append(f"Maßstab {massstab}")
    bem_teile.append("Quelle: eBay")
    bemerkung = "; ".join(bem_teile)

    return {
        "ok": True,
        "hersteller": hersteller,
        "typ": typ,
        "bezahlt": preis,          # Angebotspreis — Nutzer korrigiert auf Kaufpreis
        "zustand": zustand,
        "massstab": massstab,
        "bemerkung": bemerkung,
        "titel_roh": titel,
    }
