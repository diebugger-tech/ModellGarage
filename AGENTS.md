# AGENTS.md — ModellGarage

> Globaler Agent-Context für das gesamte Projekt.
> Canonical Source: Projekt-Root (`/AGENTS.md`)
> Gelesen von: Claude Code, Goose, opencode, pydantic-deep

## Grundprinzip

- **ModellGarage ist eine leichtgewichtige Inventar- & Bewertungs-App für
  Modellauto-Sammlungen** (Wiking, Siku, Majorette).
- **Produktziel**: Aus einer statischen Sammler-Excel wird eine schöne, mobil
  bedienbare App — durchsuchbar, mit Fotos, Konvolut-Handling und
  Wertermittlung über Sammlerkataloge.
- **Single-User** — ein Sammler, eine Instanz. Kein Multi-Tenant, kein Login.
- **Leichtgewichtig ist nicht verhandelbar** — serverlose DB (SQLite), dünnes
  Backend, schönes Frontend. Kein MongoDB, kein Postgres, kein Kubernetes.
- **Zustand ist Handarbeit** — die App schlägt höchstens vor, der Sammler
  entscheidet per Sichtung (z0/z1/z2).

## Kern-Domänenwissen

- **Katalognummer = Identität.** Jedes Modell hat eine herstellereigene Nummer
  (Wiking `30/6K.`, Siku `1050`). Sie steht **nicht am Modell**, sondern kommt
  aus dem Sammlerkatalog (Grüner Katalog / Rawe / Siku-Katalog).
- **Werte leben im Katalog, nicht am Modell.** Min/Max/Schätzwert sind
  Katalogwerte — identische Modelle teilen sie. Niemals pro Einzelmodell
  duplizieren.
- **Zustand (z0/z1/z2)** ist ein Enum, kein Freitext. Beim Excel-Import muss er
  aus der Freitext-Bemerkung extrahiert werden.
- **Konvolut** = Kauf mehrerer Autos in einer Auktion ohne Einzelangaben.
  Eltern-Datensatz (Gesamtpreis) + Kind-Datensätze (einzelne Autos). Einzelpreis
  wird **nach Katalog-Schätzwert gewichtet**, nicht stumpf geteilt.
- **Kaufdatum ist inkonsistent** in der Quell-Excel (mal Excel-Serial `45154`,
  mal Text `22.05.2020`) — beim Import normalisieren.
- **Summenzeilen** am Ende jedes Excel-Blatts (leere `Nr.`, Totals) beim Import
  herausfiltern — sonst entstehen Geister-Modelle.

## Kerndatenmodell

```
katalog    (id, hersteller, katalog_nr, typ, min_euro, max_euro, serie, quelle)
modell     (id, katalog_id→, farbe, zustand[z0/z1/z2], bemerkung,
            bezahlt, schätzwert, kaufdatum, anzahl, konvolut_id→null, fotos[])
konvolut   (id, quelle, gesamtpreis, datum, gesamtfoto)
```

## Design-Prinzipien (nicht verhandelbar)

- **Leichtgewichtig** — SQLite als einzige DB. Eine Datei, kein Server.
- **Single-User** — kein Auth, keine Sessions, keine Rollen. Ein Sammler im
  lokalen Netz oder auf dem eigenen Rechner.
- **Schönes Frontend** — SvelteKit, PWA-fähig, mobil bedienbar. Kein
  "Tool-Look" (kein reines Streamlit-Dashboard als Endprodukt).
- **MVP-first** — Excel-Import + Tabellen-UI zuerst, Foto-KI zuletzt.

**HARDREGEL FÜR AGENTEN:** Folgende Dinge sind **niemals** einzubauen:
- ❌ Multi-User / Auth / Login / Sessions / Rollen
- ❌ MongoDB, Postgres, MySQL oder andere Server-DBs (nur SQLite)
- ❌ Katalogwerte (Min/Max) am Einzelmodell duplizieren
- ❌ Zustand automatisch final setzen (immer nur Vorschlag, Mensch bestätigt)
- ❌ eBay-Bild-URLs verlinken statt lokal herunterladen (URLs sterben)
- ❌ Konvolut-Einzelpreis stumpf durch Anzahl teilen (immer gewichten)
- ❌ Secrets / eBay-Tokens in Commits

## eBay-Integration (bewusste Ausnahme)

Anders als KAiTix (Intranet-only) **darf** ModellGarage externe API-Calls machen
— aber nur die **eBay-API** und nur für: Kauf-Import (Foto + Preis + Titel).

- **Fotos herunterladen und lokal speichern** (`media/`), nie nur URL merken.
- **Marktwert = grobe Orientierung**, kein präziser Verkaufswert. Die Browse-API
  liefert nur aktive Angebote; "verkaufte Artikel" (Marketplace Insights API)
  ist zugangsbeschränkt.
- **eBay-Keys/Tokens** ausschließlich via `.env` / `ebay_token.json`
  (beide gitignored). Niemals committen.
- eBay ist **Phase 3+**, optional. MVP funktioniert komplett ohne eBay.

## Stack-spezifische Hinweise (Python / FastAPI)

- **Async überall**: FastAPI-Endpunkte und SQLAlchemy-Operationen `async`
  (`aiosqlite` als Treiber).
- **Typisierung**: 100 % Type Hints, Pydantic V2 für Request/Response.
- **SQLAlchemy 2.x**: neue `select()`-Syntax, kein Legacy-Query-Stil.
- **Dependency Injection**: FastAPI `Depends()` für DB-Sessions.
- **Fehlerbehandlung**: zentrale Exception Handler, keine Stacktraces an Client.
- **Alembic**: Migrationen versioniert und **immutable** (einmal generiert = nie
  ändern). Vor `apply` immer menschliches Review.
- **Excel-Import** (`app/services/excel_import.py`): openpyxl/pandas, Summenzeilen
  filtern, Kaufdatum normalisieren, Zustand aus Freitext extrahieren.
- **Tests**: `pytest` mit `asyncio_mode=auto`, `httpx.AsyncClient` für API-Tests.
- **Linting**: `ruff` (Format + Lint), `mypy` (Typprüfung).

## Frontend-Hinweise (SvelteKit)

- **Svelte 5**, Routes-Gruppen `src/routes/(app)/`.
- `npm run build` muss grün sein, bevor Frontend-Änderungen als fertig gelten.
- Mobil-first denken (PWA): Sammlung durchblättern, Zustand nachtragen am Handy.

## Commit-Konventionen

**Conventional Commits**:

| Typ        | Verwendung                          | Beispiel                                   |
|------------|-------------------------------------|--------------------------------------------|
| `feat`     | Neue Funktionalität                 | `feat(konvolut): add weighted price split` |
| `fix`      | Bugfix                              | `fix(import): skip summary rows`           |
| `chore`    | Wartung, Build, CI                  | `chore(deps): bump sqlalchemy`             |
| `refactor` | Restrukturierung ohne Verhalten     | `refactor(katalog): extract seed loader`   |
| `docs`     | Dokumentation                       | `docs(readme): add konvolut section`       |
| `test`     | Tests                               | `test(import): add date-normalize cases`   |
| `style`    | Formatierung                        | `style: ruff formatting`                   |

Regeln:
- Imperativ, Präsens ("add", nicht "added")
- Kurze Überschrift (<72 Zeichen)
- Body bei komplexen Änderungen erforderlich

## Verbotene Operationen (Hard Constraints)

```
❌ DB-Migrationen ohne menschliches Review anwenden
❌ Bestehende Migrations-Dateien ändern (Alembic: einmal generiert = immutable)
❌ Force-Push auf main
❌ Secrets / eBay-Tokens in Commits (.env, *.key, ebay_token.json)
❌ Server-DB einführen (MongoDB/Postgres/MySQL) — nur SQLite
❌ Auth/Login/Multi-User einbauen
❌ Große Binary-Dateien (>1MB) oder Fotos ins Repo committen (media/ ist gitignored)
❌ Excel-/CSV-Quelldateien committen (privat)
❌ git reset --hard ohne Backup
```

## Status

🌱 **Konzeptphase / Initialisierung.** Steuerdateien (README, .gitignore,
AGENTS.md) angelegt. Noch kein Anwendungscode. Nächster Schritt: SQLite-Schema
ausformulieren + Excel-Import-Prototyp.
