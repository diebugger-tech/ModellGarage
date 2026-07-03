# ModellGarage

> **Inventar- & Bewertungs-App für Modellauto-Sammlungen.**
> Aus einer statischen Sammler-Excel wird eine leichtgewichtige, schöne App —
> mit Konvolut-Handling, Katalog-Abgleich und optionaler eBay-Anbindung.

---

## Idee

Ein leidenschaftlicher Sammler dokumentiert seine Modellautos (Wiking, Siku,
Majorette) bisher in Excel. ModellGarage überführt diese Daten in eine echte
App: durchsuchbar, mobil bedienbar, mit Fotos und automatischer Wertermittlung.

**Kernnutzen:**
- Doppelkäufe vermeiden (Sammlung durchsuchbar)
- Gesamtwert im Blick (Katalog-Schätzwerte)
- **Konvolute** (Auktions-Pakete) sauber aufschlüsseln
- Zustand & Fotos je Modell dokumentieren

---

## Was die App besonders macht

### 1. Katalog-basierte Identität
Jedes Modell hat eine herstellereigene Katalognummer (Wiking `30/6K.`,
Siku `1050`, …). Diese steht **nicht am Modell**, sondern kommt aus dem
jeweiligen Sammlerkatalog (Grüner Katalog / Rawe / Siku-Katalog).
→ Kataloge werden einmalig als Seed importiert; Werte (Min/Max) leben dort,
nicht am Einzelmodell (keine 6-fache Pflege identischer Werte).

### 2. Konvolut-Handling (Kernfeature)
Kauf mehrerer Autos in einer Auktion, ohne Einzelangaben:
1. Konvolut als **Eltern-Datensatz** anlegen (Quelle, Gesamtpreis, Datum, Gesamtfoto)
2. Beim Auspacken jedes Auto als **Kind-Datensatz** verknüpfen
3. Einzelpreis **nach Katalog-Schätzwert gewichtet** berechnen
   (nicht stumpf Gesamtpreis ÷ Anzahl — ein 5€- und ein 80€-Auto
   bekommen faire Anteile)

### 3. Zustand bleibt Handarbeit
Zustand (z0/z1/z2) entscheidet der Sammler per Sichtung — die App bietet
nur ein schnelles Dropdown. Optionale Foto-KI schlägt später höchstens vor.

### 4. eBay-Anbindung (optional, Endstufe)
Beim Import eines Kaufs werden **Auktionsfoto + Preis** übernommen.
Bilder werden **lokal gespeichert** (eBay-URLs sterben nach Auktionsende).

---

## Tech-Stack

| Schicht    | Wahl                    | Warum                                              |
|------------|-------------------------|----------------------------------------------------|
| Backend    | **FastAPI** (async)     | Schnell, auto-Swagger, Pydantic V2                 |
| DB         | **SQLite** (aiosqlite)  | Leichteste DB — eine Datei, kein Server, relational|
| ORM        | SQLAlchemy 2.x + Alembic| Wie KAiTix; Migrationen versioniert                |
| Frontend   | **SvelteKit** (Svelte 5)| Schön, schnell, PWA-fähig (mobil)                  |
| Fotos      | Lokaler `media/`-Ordner | eBay-Bilder herunterladen statt verlinken          |

**Design-Prinzip:** leichtgewichtig. Serverlose DB, dünnes Backend,
schönes Frontend. Kein MongoDB/Postgres, kein Kubernetes.

---

## Projektstruktur (geplant)

```
modellgarage/
├── app/
│   ├── core/            config.py, database.py (async SQLite)
│   ├── domains/
│   │   ├── modelle/     CRUD, Suche, Filter
│   │   ├── katalog/     Siku / Majorette / Wiking Kataloge
│   │   ├── konvolut/    Eltern/Kind + gewichteter Einzelpreis
│   │   └── ebay/        Import: Foto + Preis lokal ziehen
│   └── services/
│       └── excel_import.py   Erst-Migration Excel → SQLite
├── frontend/            SvelteKit (Svelte 5)
├── alembic/             Migrationen (immutable)
├── media/              eBay-/Modell-Fotos (lokal, gitignored)
└── data/               SQLite-DB + Katalog-Seeds (gitignored)
```

---

## Datenmodell (Kurzfassung)

```
katalog    (hersteller, katalog_nr, typ, min_euro, max_euro, serie, quelle)
modell     (katalog_id→, farbe, zustand z0/z1/z2, bemerkung,
            bezahlt, schätzwert, kaufdatum, anzahl, konvolut_id→, fotos[])
konvolut   (quelle, gesamtpreis, datum, gesamtfoto)
```

---

## Roadmap (MVP-first)

1. **Excel → SQLite Import** + Tabellen-UI → ersetzt sofort die Excel
2. **Konvolut-Handling** (Eltern/Kind, gewichteter Preis)
3. **eBay-Import** (Foto + Preis lokal ziehen)
4. **Foto-KI** (optional) — Maske ist vorbereitet, KI füllt später vor

---

## Status

🌱 **Konzeptphase / Initialisierung.** Noch kein Anwendungscode.

---

## Lizenz

Privates Hobbyprojekt.
