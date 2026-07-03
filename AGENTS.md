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
            bezahlt, schätzwert, kaufdatum, anzahl, konvolut_id→null)
konvolut   (id, quelle, gesamtpreis, datum)
foto       (id, modell_id→null, konvolut_id→null, pfad, quelle[ebay/manuell])
```

- **`foto` ist eine eigene Tabelle** (1:n): Ein Modell kann mehrere Fotos haben,
  ein Konvolut sein Gesamtfoto. Genau eines von `modell_id`/`konvolut_id` ist
  gesetzt. Kein Foto-Array am Modell (relational nicht möglich).
- **`katalog_nr` kann sich über mehrere `modell`-Zeilen wiederholen** (Dubletten
  / "doppelt" in der Excel) — viele `modell` → ein `katalog`. Das ist gewollt.

## Domänen-Glossar (echte Codes aus der Sammler-Excel)

Diese Kürzel stehen in der Freitext-Spalte `Bemerkung` der Quell-Excel und
müssen beim Import erkannt / geparst werden. Sie sind die Fachsprache des
Sammlers — die App muss sie verstehen, nicht wegwerfen.

| Code | Bedeutung | Behandlung im Import |
|------|-----------|----------------------|
| `z0` / `z1` / `z2` | Zustand (z0 = neuwertig/OVP … z2 = bespielt) | → Feld `zustand` |
| `z1-z2`, `z1-(z2)` | Zwischenstufe; Klammer = Tendenz zur schlechteren | → schlechtere Stufe (`z1`), Original in `bemerkung` |
| `doppelt` | Dublette (Sammler hat das Modell mehrfach) | eigene `modell`-Zeile, nicht mergen |
| `ovp` | Originalverpackung vorhanden | in `bemerkung` behalten (später Flag denkbar) |
| `e.P.` | Einzel-/Festpreis (min = max, fester Wert) | `min_euro` = `max_euro` |
| `IE` | Inneneinrichtung (Farbvariante des Interieurs) | in `bemerkung` |
| `SW` | Scheibenwischer (Ausstattungsdetail) | in `bemerkung` |
| `Ladegut` | Beiladungs-/Ladungs-Modell (kein Fahrzeug) | Typ so übernehmen |
| `aus Konvolut` | stammt aus einem Sammelkauf | Kandidat für `konvolut`-Verknüpfung |
| `nicht in GK` / `nicht in Rawe` | Farbvariante nicht im Katalog (GK = Grüner Katalog, Rawe = Rawe-Katalog) | in `bemerkung`; ggf. `quelle` markieren |

**Wert-Regel:** Pro Zeile ist meist entweder `bezahlt` **oder** `Schätzwert`
gefüllt, selten beides. `bezahlt` = real gezahlt, `Schätzwert` = geschätzt wenn
kein Kaufpreis bekannt. Beim Import beide Felder getrennt übernehmen.

## Echte Datengröße (verifiziert am Import)

Die Quell-Excel ist **größer als anfangs geschätzt** — nicht ~537, sondern:
- **~20 Blätter**, u.a. Wiking-Segmente (UV500, UVRest, W100–W1000, "Wik ab 1001"),
  **Siku** (574 Katalog-Einträge!), **Majorette**, **Matchbox**, "Sonstige Modelle"
- **~8100 Modell-Zeilen**, ~1750 eindeutige Katalog-Einträge
- Also bereits **multi-Hersteller** in der einen Datei (nicht nur Wiking)
- Summe bezahlt ~31.900 €

Import-Erkenntnisse (Stand `app/services/excel_import.py`):
- Zustand wird nur bei ~440 Zeilen erkannt (der Rest hat kein z0/z1/z2 im Freitext
  → `zustand=NULL`, korrekt: nicht raten).
- **Datum-Parsing hat noch Fehltreffer**: In manchen Blättern rutschen Werte wie
  `99.74` oder `bezahlt` in die Datumsspalte → die Spaltenreihenfolge ist NICHT
  in allen 20 Blättern identisch. TODO: pro Blatt Header-Zeile lesen und Spalten
  dynamisch zuordnen statt fixe Indizes (COL_DAT etc.).

## Bilder: NICHT in der Excel (verifiziert)

Geprüft mit `scripts/check_images.py`:
- **Keine eingebetteten Bilder** (`xl/media/` leer, keine drawings)
- **Keine Bildpfade/URLs** als Text in den Zellen

→ **Ein-Klick-Bildimport aus der Excel ist unmöglich** — es gibt keine Verknüpfung.
Fotos müssen anders in die App: (a) manueller Upload pro Modell, (b) eBay-Import
(Phase 3), (c) später Bulk-Zuordnung aus einem Foto-Ordner, WENN die Dateinamen
die Katalog-Nr. enthalten (z.B. `30-6K.jpg`). Quelle/Ort seiner Fotos ist offen.

**Entscheidung des Sammlers:** Fotos werden **später von ihm selbst** in die App
hochgeladen (manueller Upload pro Modell). Kein Excel-/Bulk-Import nötig. Der
Foto-Upload-Endpoint (`POST /api/modelle/{id}/foto`) speichert nach `media/` und
legt einen `foto`-Datensatz an — steht bereit, wenn er soweit ist.

## Import / Export (Anforderung des Sammlers)

- **Excel-Import**: `app/services/excel_import.py` — Erst-Migration + laufend
  (neue Zeilen nachladen). Muss die 20-Blätter-Struktur robust verarbeiten.
- **Excel-Export**: Gegenrichtung — die DB zurück nach xlsx (openpyxl), damit der
  Sammler seine gewohnte Excel-Sicht behält und Backups außerhalb der App hat.
  Format: ein Blatt pro Serie/Hersteller, gleiche Spalten wie das Original.

## Design-Sprache (verbindlich)

**Vorbild: classicdriver.com/de — übertragen auf Modellautos.**
Edel, ruhig, "Apple-nah". Konkret:
- **Viel Weißraum**, großzügige Ränder, ruhiges Grid.
- **Große, hochwertige Fotos** als Held jedes Modells (Karten mit Bild oben).
- **Serifen-Akzente für Überschriften** (Editorial-Look wie Classic Driver),
  serifenlose, gut lesbare Fließschrift (System-/SF-nahe Stack).
- **Zurückhaltende Farbpalette**: Off-White/Anthrazit, ein einziger dezenter
  Akzent. Keine grellen Buttons, keine "Tool"-Optik.
- **Sanfte Übergänge**, dezente Schatten, abgerundete Ecken (Apple-Anmutung).
- **Mobil-first / responsiv** (PWA) — auf dem Handy durchblättern wie ein Magazin.
- Kein Dashboard-Look, keine Tabellen-Wüste als Startseite: die Sammlung wird
  **kuratiert präsentiert** (Galerie), Tabellen-/Filteransicht ist zusätzlich.

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

## Umgebung (Host: Ubuntu + Nix Home-Manager Hybrid)

**Wichtig für alle Agenten** — der Host läuft **Ubuntu mit Nix Home-Manager**
(Hybrid, nicht reines NixOS). Das kombiniert bewusst zwei Welten:
- **Ubuntu/apt** für System-Basis
- **Nix Home-Manager** für deklarative User-Tools (reproduzierbar)

Konsequenzen fürs Entwickeln:
- **Kein globales `pip install`** — System-Python ist extern verwaltet (PEP 668).
  Immer projektlokales venv.
- **`uv` ist der Standard-Weg** für Python-Deps: `uv venv .venv` +
  `uv pip install ...` (installiert isoliert ins `.venv`, fasst System-Python
  nicht an). Bevorzugt gegenüber `pip`.
- **venv liegt projektlokal** (`.venv/`), gitignored.
- Vor `uv`-Installs die Umgebung prüfen; bei blockierten Kommandos den Nutzer
  fragen statt blind zu wiederholen.

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

## ADR — Ein Prozess: FastAPI liefert das Frontend aus

- **Entscheidung:** Das gebaute SvelteKit (`adapter-static`, `npm run build` →
  `frontend/build/`) wird von FastAPI als statische Dateien ausgeliefert
  (`StaticFiles`). API unter `/api/*`, Frontend unter `/`.
- **Begründung:** Leichtgewichtig + Single-User. Ein `uvicorn`-Start, ein Port,
  kein separater Node-Server im Betrieb. In der Entwicklung dürfen Vite-Dev-Server
  (Frontend) und uvicorn (Backend) getrennt laufen (Proxy auf `/api`).
- **Konsequenz:** Kein CORS-Setup nötig im Betrieb (gleiche Origin). Media unter
  `/media/*` ebenfalls von FastAPI serviert.

## Deployment-Ziel: Windows + Podman (Container)

**Produktiv läuft ModellGarage als Container unter Podman auf Windows.**
- **Ein Container, ein Prozess, ein Port** — genau der `start-prod`-Weg
  (FastAPI serviert gebautes SvelteKit + `/media` + `/api`).
- **Multi-Stage-Build** (`Containerfile`): Stage 1 Node baut das Frontend,
  Stage 2 Python (slim) läuft schlank ohne Node/npm.
- **Podman-kompatibel** — `compose.yml` läuft mit `podman compose` /
  `podman-compose`. Keine Docker-spezifischen Features (kein BuildKit-Syntax,
  kein `docker compose`-Only).
- **Persistenz über Volumes**: `data/` (SQLite-DB) und `media/` (Fotos) werden
  als Named Volumes gemountet, damit sie Container-Rebuilds überleben.
- **Windows-Fallstricke**: LF-Zeilenenden erzwingen (`.gitattributes`), keine
  absoluten Linux-Pfade hart kodieren, Port-Mapping explizit (`8003:8003`).
- Excel-Import läuft einmalig im Container (`podman exec ... make import`) oder
  über ein gemountetes `data/`-Volume mit vorbefüllter DB.

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

🚀 **MVP lauffähig.** Phase 1 komplett:
- Excel-Import (header-getrieben, 18 Blätter, ~6300 Modelle, ~3250 Katalog-Einträge)
- FastAPI-Backend: CRUD, Suche, Filter, Statistik, Excel-Export, Foto-Upload
- SvelteKit-Frontend (Classic-Driver-Design): Galerie + Detail, Suche/Filter, Statistik-Band
- Ein Prozess serviert Frontend + API + /media (SPA-Fallback für Deep-Links)
- 4 pytest grün, E2E verifiziert

**Start:** `make install && make import && make build && make dev` → http://127.0.0.1:8137

Offene TODOs (Phase 2+):
- Konvolut-Handling (Eltern/Kind, gewichteter Einzelpreis) — Tabelle steht, UI/Logik fehlt
- Hersteller-Normalisierung (Matchbox-Serien wie "Superfast"/"Lesney" als Serie statt Hersteller)
- eBay-Import (Phase 3, braucht Developer-Keys)

Erledigt (Phase 1b — CRUD + Upload-UI):
- ✅ Excel-Import-UI (`/import`, Drag&Drop-Upload → `POST /api/import/excel`)
- ✅ Foto-Upload-UI (Detailseite, `POST /api/modelle/{id}/foto`)
- ✅ Modell manuell anlegen (`/neu`, eBay copy-paste) — `POST /api/modelle/voll`
  legt bei Bedarf neuen Hersteller/Katalog-Eintrag an (get-or-create)
- ✅ Bearbeiten + Löschen auf der Detailseite (PATCH/DELETE)
- Manuell angelegte Modelle nutzen dieselben Tabellen/Felder wie importierte —
  kein Bruch zwischen Excel-Daten und Handeingabe
