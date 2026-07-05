#!/usr/bin/env python3
"""Seed-Testdaten für Konvolut + Wunschliste.

Deckt ab, was der Excel-Import NICHT kann: Sammelkäufe (Konvolute) mit
gewichteter Preisverteilung und die manuelle Wunschliste.

Voraussetzung:
  1. Die App läuft (Standard: http://localhost:8003).
  2. Modelle sind bereits importiert — in der App auf "Import" gehen und
     examples/testdaten.xlsx hochladen. Danach dieses Skript ausführen.

Aufruf:
  python scripts/seed_testdaten.py                 # localhost:8003
  python scripts/seed_testdaten.py http://host:port

Nur Python-Standardbibliothek, keine Extra-Pakete nötig.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8003").rstrip("/")


def call(method: str, path: str, payload: dict | None = None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        BASE + path, data=data, method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read().decode()
            return json.loads(body) if body else None
    except urllib.error.URLError as e:
        print(f"FEHLER bei {method} {path}: {e}")
        sys.exit(1)


def main() -> None:
    # 0. App erreichbar?
    call("GET", "/api/health")

    # 1. Vorhandene Modelle holen (brauchen wir zum Zuordnen)
    liste = call("GET", "/api/modelle?limit=200")
    items = liste.get("items", []) if liste else []
    if len(items) < 6:
        print(f"Nur {len(items)} Modelle gefunden.")
        print("Bitte zuerst examples/testdaten.xlsx über den Import-Button hochladen,")
        print("dann dieses Skript erneut ausführen.")
        sys.exit(0)
    ids = [m["id"] for m in items]

    # 2. Konvolut A — gemischtes eBay-Paket. Teure + günstige Autos, damit die
    #    Gewichtung nach Katalog-Schätzwert sichtbar wird (nicht stumpf /Anzahl).
    kon = call("POST", "/api/konvolut", {
        "quelle": "eBay Sammelauktion 05.07.",
        "gesamtpreis": 120.0,
        "datum": "2024-07-05",
    })
    kid = kon["id"]
    for mid in ids[:4]:
        call("POST", f"/api/konvolut/{kid}/modell/{mid}")
    verteilt = call("POST", f"/api/konvolut/{kid}/preise-verteilen")
    print(f"Konvolut A (#{kid}): 4 Modelle, 120 EUR gewichtet verteilt:")
    for a in (verteilt or {}).get("anteile", []):
        print(f"   - {a.get('typ')}: {a.get('bezahlt')} EUR")

    # 3. Konvolut B — kleineres Flohmarkt-Paket
    kon2 = call("POST", "/api/konvolut", {
        "quelle": "Flohmarkt 20.06.",
        "gesamtpreis": 35.0,
        "datum": "2024-06-20",
    })
    kid2 = kon2["id"]
    for mid in ids[4:6]:
        call("POST", f"/api/konvolut/{kid2}/modell/{mid}")
    call("POST", f"/api/konvolut/{kid2}/preise-verteilen")
    print(f"Konvolut B (#{kid2}): 2 Modelle, 35 EUR verteilt.")

    # 4. Wunschliste — u. a. die Lücken 30 und 50 aus der Testdaten-Excel
    wuensche = [
        {"hersteller": "Wiking", "katalog_nr": "30/1",
         "typ": "VW Käfer Ovali", "notiz": "schließt Lücke 30", "max_euro": 20.0},
        {"hersteller": "Wiking", "katalog_nr": "50/2",
         "typ": "Borgward LKW", "notiz": "schließt Lücke 50", "max_euro": 35.0},
        {"hersteller": "Siku", "katalog_nr": "1042",
         "typ": "Feuerwehr Leiterwagen", "notiz": "noch gesucht", "max_euro": 15.0},
    ]
    for w in wuensche:
        call("POST", "/api/wunsch", w)
    print(f"Wunschliste: {len(wuensche)} Einträge angelegt.")

    print("\nFertig. In der App prüfen: Konvolute (gewichtete Preise),")
    print("Wunschliste, Statistik und Lücken.")


if __name__ == "__main__":
    main()
