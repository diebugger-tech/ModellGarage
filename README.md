# ModellGarage

> **Inventar- & Bewertungs-App für Modellauto-Sammlungen.**
> Aus einer statischen Sammler-Excel wird eine leichtgewichtige, schöne App —
> mit Katalog-Abgleich, Konvolut-Handling und optionaler eBay-Anbindung.

---

## Idee

Ein leidenschaftlicher Sammler dokumentiert seine Modellautos (Wiking, Siku,
Majorette, Matchbox …) bisher in Excel. ModellGarage überführt diese Daten in
eine echte App: durchsuchbar, mobil bedienbar, mit Fotos und Wertermittlung.

**Kernnutzen:**
- Doppelkäufe vermeiden (Sammlung durchsuchbar)
- Gesamtwert im Blick (Katalog-Schätzwerte)
- **Konvolute** (Auktions-Pakete) sauber aufschlüsseln
- Zustand & Fotos je Modell dokumentieren

---

## Schnellstart

### Lokal (Entwicklung)

```bash
make setup     # venv + Python-Deps + npm ci
make import     # Excel → SQLite (einmalig)
make start      # Backend :8003 + Frontend :5173 (Hot-Reload)
make stop       # beides stoppen
make status     # laufende Prozesse zeigen
```

### Lokal (Produktion, ein Prozess)

```bash
make start-prod  # baut Frontend + FastAPI serviert alles auf :8003
```
→ http://127.0.0.1:8003

### Container (Podman — Linux/Mac mit `make`)

```bash
make podman-up      # Container bauen + starten (:8003)
make podman-import   # Excel im Container importieren
make podman-logs     # Logs folgen
make podman-down     # stoppen
```

### Windows (Podman, ohne `make`) — Schritt für Schritt

Für Windows gibt es Doppelklick-Skripte, kein `make` nötig.

1. **Podman Desktop installieren:** https://podman.io/getting-started/installation
   (beim ersten Start einmal „Initialize / Start" der Podman-Maschine bestätigen).
2. **Projekt holen:** dieses Repository als ZIP herunterladen (GitHub → grüner
   „Code"-Button → „Download ZIP") und entpacken — oder `git clone`.
3. **Starten:** im entpackten Ordner **`start-podman.bat`** doppelklicken.
   Der erste Start baut den Container (dauert ein paar Minuten) und öffnet dann
   automatisch den Browser auf http://localhost:8003.
4. **Eigene Excel importieren:** in der App oben auf **„Import"** klicken und die
   `.xlsx`-Sammlungsdatei hochladen. Fertig — die Sammlung erscheint in der Galerie.
5. **Stoppen:** **`stop-podman.bat`** doppelklicken. DB und Fotos bleiben in den
   Podman-Volumes erhalten und sind beim nächsten Start wieder da.

> Hinweis: Falls `podman compose` meldet, dass „compose" fehlt, in Podman Desktop
> unter *Settings → Extensions* „Compose" aktivieren (oder `podman-compose`
> nachinstallieren). Die Skripte selbst müssen dafür nicht geändert werden.

### Tests

```bash
make test        # pytest
```

`make help` zeigt alle Targets.

---

## Was die App besonders macht

### 1. Katalog-basierte Identität
Jedes Modell hat eine herstellereigene Katalognummer (Wiking `30/6K.`,
Siku `1050`, …). Diese steht **nicht am Modell**, sondern kommt aus dem
jeweiligen Sammlerkatalog. Werte (Min/Max) leben im Katalog, nicht am
Einzelmodell (keine mehrfache Pflege identischer Werte).

### 2. Konvolut-Handling (geplant, Phase 2)
Kauf mehrerer Autos in einer Auktion, ohne Einzelangaben: Konvolut als
Eltern-Datensatz, jedes Auto als Kind, Einzelpreis **nach Katalog-Schätzwert
gewichtet** (nicht stumpf Gesamtpreis ÷ Anzahl).

### 3. Zustand bleibt Handarbeit
Zustand (z0/z1/z2) entscheidet der Sammler per Sichtung — die App bietet nur
ein Dropdown. Optionale Foto-KI (später) schlägt höchstens vor.

### 4. eBay-Schnellerfassung (ohne API)
eBay blockt Server-Fetch (403). Der Sammler kopiert stattdessen **Titel**,
optional **Preis/Zustand** und optional die **Artikelbeschreibung** aus seinem
Browser in `/neu` — die App parst den Text lokal (kein Netzwerk) und füllt
Hersteller, Typ, **Katalog-/Wiking-Nr.**, **Farbe**, Preis, Zustand und Maßstab
als Vorschlag vor. Nr. und Farbe kommen dabei meist aus der Beschreibung —
genau die Felder, die im Titel fehlen. Alles bleibt Vorschlag, der Sammler
bestätigt.

### 5. Fotos & eBay-API (später)
Fotos lädt der Sammler manuell pro Modell hoch (Upload-Endpoint steht). Ein
echter eBay-Import via Browse-API (Developer-Account + OAuth) ist Phase 3,
optional.

---

## Tech-Stack

| Schicht    | Wahl                     | Warum                                              |
|------------|--------------------------|----------------------------------------------------|
| Backend    | **FastAPI** (async)      | Schnell, auto-Swagger, Pydantic V2                 |
| DB         | **SQLite** (aiosqlite)   | Leichteste DB — eine Datei, kein Server, relational|
| ORM        | SQLAlchemy 2.x           | Wie KAiTix; `create_all` im MVP, Alembic vorbereitet|
| Frontend   | **SvelteKit** (Svelte 5) | Schön, schnell, PWA-fähig; `adapter-static`        |
| Deployment | **Podman** (Windows)     | Ein Container, ein Prozess, ein Port (8003)        |
| Fotos      | Lokaler `media/`-Ordner  | Bilder herunterladen/speichern statt verlinken     |

**Design-Prinzip:** leichtgewichtig. Serverlose DB, dünnes Backend, schönes
Frontend im Editorial-Stil (angelehnt an classicdriver.com). Kein MongoDB/
Postgres, kein Kubernetes.

---

## Projektstruktur (Ist-Stand)

```
ModellGarage/
├── app/
│   ├── core/            config.py, database.py (async SQLite, FK-Enforcement)
│   ├── routers/         modelle, statistik, export, fotos
│   ├── services/        excel_import.py (header-getrieben, 18 Blätter)
│   ├── models.py        SQLAlchemy: katalog/modell/konvolut/foto
│   ├── schemas.py       Pydantic V2
│   └── main.py          App + StaticFiles + SPA-Fallback
├── frontend/            SvelteKit 5 (Galerie + Detail)
│   └── src/routes/      +page.svelte (Galerie), modell/[id] (Detail)
├── scripts/             import_excel.py + Verifikations-Helfer
├── tests/               pytest (API)
├── docs/schema.sql      DDL-Referenz
├── Containerfile        Multi-Stage (Node build → Python runtime)
├── compose.yml          Podman/Docker Compose
├── Makefile             make start/stop/test/podman-*
├── data/                SQLite-DB (gitignored)
└── media/               Fotos (gitignored)
```

---

## Datenmodell

```
katalog    (hersteller, katalog_nr, typ, min_euro, max_euro, serie, quelle)
modell     (katalog_id→, farbe, zustand z0/z1/z2, bemerkung,
            bezahlt, schaetzwert, kaufdatum, anzahl, konvolut_id→)
konvolut   (quelle, gesamtpreis, datum)
foto       (modell_id→ | konvolut_id→, pfad, quelle)   # 1:n, eigene Tabelle
```

**Auslieferung:** FastAPI serviert das gebaute SvelteKit + `/media` als ein
einziger Prozess (ein Port, kein separater Node-Server im Betrieb).

---

## Status

🚀 **MVP lauffähig.**
- Excel-Import (header-getrieben, 18 Blätter, ~6.300 Modelle, ~3.250 Katalog-Einträge)
- Backend: CRUD, Suche, Filter, Sortierung, Statistik, Excel-Export, Foto-Upload
- Frontend: Galerie + Detail im Classic-Driver-Design, Suche/Filter/Statistik
- Ein Prozess serviert Frontend + API + `/media` (SPA-Fallback für Deep-Links)
- Podman-Deployment (Multi-Stage-Container) für Windows
- 4 pytest grün, E2E verifiziert

**Phase 2 erledigt:** Konvolut-UI (Eltern/Kind, gewichteter Preis, Fotos),
Wunschliste + Dubletten-Warnung, Statistik-Charts, Foto-Galerie mit Lightbox,
Hersteller-Normalisierung, eBay-Schnellerfassung inkl. Artikelbeschreibung
(Katalog-Nr. + Farbe).

**Phase 2b erledigt:** manuelle Wunschliste (Nummern merken, „gekauft"-Toggle,
aus Lücken übernehmen), Kaufjahr-Filter/-Suche/-Anzeige in der Galerie,
Katalog-Abgleich beim Anlegen (Top-3-Kandidaten), Datenqualitätsfilter
(ohne Foto/Zustand/Kaufdatum), rotierendes Auto-Backup, Import-Regressionstest.

**Offen (Phase 3):** eBay-Import via Browse-API (Developer-Account + OAuth),
Mehrfach-Erfassung aus einer Konvolut-Beschreibung, pflegbarer Katalog (GK/Rawe).

---

## Lizenz

MIT (siehe `LICENSE`).
