# Großer Prompt — nächster ModellGarage-Lauf

> **Wichtig vorab:** Im Working Tree (`develop`) liegen bereits **uncommittete**
> Änderungen aus einer parallelen Session (eBay-Beschreibung + Statistik-Fix +
> Doku). Nicht verwerfen — erst reviewen & committen, dann die neuen Features.
> Nur **eine** Claude-Code-Session gleichzeitig auf diesem Tree laufen lassen.

---

## Bereits im Working Tree (uncommitted) — zuerst reviewen & committen

1. **eBay-Schnellerfassung liest jetzt die Artikelbeschreibung** → zieht
   Katalog-/Wiking-Nr. und Farbe (die im Titel fehlen).
   - `app/services/ebay_parse.py`: `parse_text(titel, extra, beschreibung)`,
     neue Extraktoren `_katalog_nr`, `_katalog_nr_bare`, `_farbe`; explizites
     `z0/z1/z2` hat Vorrang.
   - `app/routers/ebay.py`: `EbayTextIn.beschreibung`.
   - `frontend/src/lib/api.js`, `frontend/src/routes/neu/+page.svelte`:
     Beschreibungs-Textarea (rows 6, resize), Mapping `katalog_nr`+`farbe`.
   - `tests/test_ebay_parse.py`: 7 neue Unit-Tests.
   - `app/routers/konvolut.py`: ungenutzter Import `func` entfernt (ruff).
2. **Statistik-Seite hängt nicht mehr bei „Lade Auswertung …"**
   (`frontend/src/routes/statistik/+page.svelte`):
   - `onMount` mit try/catch + Fehleranzeige (vorher schluckte ein Fehler das
     Laden → ewiger Spinner).
   - **Root-Cause-Fix:** `d.zustand_verteilung.sort(...)` mutierte `$state`
     während des Renderns → in Svelte 5 verboten (`state_unsafe_mutation`).
     Jetzt `[...d.zustand_verteilung].sort(...)` auf einer Kopie.
3. Doku aktualisiert: `AGENTS.md`, `README.md`, `docs/HANDOFF_ebay-beschreibung.md`.

Sandbox-Checks waren grün: `pytest` 11 passed, `ruff check app/ tests/` sauber,
`npm run build` grün.

**→ Bitte: `git diff` mit mir durchgehen, dann committen:**
`feat(ebay): Artikelbeschreibung parsen (Nr.+Farbe) + fix(statistik): Ladehänger`
(oder zwei getrennte Commits: `feat(ebay)…` und `fix(statistik)…`).

---

## Neu zu bauen

### 1. Manuelle Wunschliste (fehlt komplett)
Aktuell ist „Fehlende Nummern" nur eine read-only Lücken-Analyse
(`GET /api/extras/wunschliste`). Es fehlt eine **echte Merkliste**:

- **DB:** neue Tabelle `wunsch` (SQLite, via `create_all` im MVP — kein Alembic
  nötig für eine neue Tabelle): `id, hersteller, katalog_nr (nullable),
  typ (nullable), notiz (nullable), status ['gesucht'|'gekauft'], erstellt_am`.
- **Backend** (`app/routers/extras.py` oder neuer `wunsch.py`):
  - `POST /api/wunsch` (anlegen), `GET /api/wunsch` (Liste),
    `PATCH /api/wunsch/{id}` (Status `gesucht`↔`gekauft`),
    `DELETE /api/wunsch/{id}`.
- **Frontend** (`/wunschliste`): **neben** dem Lücken-Finder ein Eingabeformular
  (Hersteller, Nr., Notiz) + Liste der Wünsche mit „gekauft"-Toggle und Löschen.
- **Verknüpfung Lücken → Wunschliste:** an jeder gefundenen Lücken-Nummer ein
  Button „+ merken", der sie direkt als Wunsch anlegt (Hersteller + Basis-Nr.).
  Genau der Workflow: aus den Lücken die interessanten Nummern übernehmen.
- Constraints (AGENTS.md): SQLite only, kein Auth, Werte nicht am Modell
  duplizieren. Wunsch ist unabhängig von `modell`/`katalog`.

### 2. Konvolut-Modus aus einer Beschreibung
Eine eBay-Beschreibung listet oft **mehrere** Modelle mit mehreren Nummern.
Der aktuelle Einzel-Parser nimmt nur die erste. Neu: ein Modus, der **alle**
Nr.-/Farbe-Paare findet und eine **bestätigbare Liste** liefert (jede Zeile
einzeln ins Konvolut übernehmbar). Passt zum bounded Konvolut-Workflow
(„Erfasse Konvolut X aus dieser Beschreibung", endliche Liste, kein eBay-Scan).

### 3. Backlog (nice-to-have, nur wenn Zeit)
- **Konfidenz-Flag** pro vorgeschlagenem Feld (Nr. mit Kontextwort = sicher,
  bloße Titel-Nummer = unsicher) — dem Sammler zeigen, was er prüfen muss.
- **Farbliste aus dem Katalog** statt Hardcode in `ebay_parse.py`.
- **Katalog-Abgleich:** erkannte Nr. gegen den Katalog validieren, Typ/Wert
  automatisch ziehen (der eigentliche Wertschöpfungsschritt laut AGENTS.md).

---

### 4. Excel-Import-Kompatibilität (nicht verhandelbar)
Die private Original-Sammler-Excel (`*.xlsx`, gitignored, **nicht** auf GitHub)
muss mit allen neuen Funktionen **unverändert importierbar** bleiben — der Kumpel
lädt die App und importiert seine eigene Datei.
- Ergänze `tests/test_excel_import.py`: importiert die echte Datei in eine
  temporäre DB, prüft Kennzahlen (~6310 Modelle, ~3253 Katalog-Einträge,
  Hersteller Wiking/Siku/Majorette vorhanden, keine Geister-Zeilen aus
  Summenzeilen). Via `@pytest.mark.skipif(Datei fehlt)` überspringen, damit
  CI/GitHub ohne die private Datei grün bleibt.
- Bei **jeder** Schema-Änderung (z. B. neue `wunsch`-Tabelle) sicherstellen, dass
  `make import` gegen die Original-Excel weiterhin fehlerfrei durchläuft.

---

## Ideen-Backlog (konsolidiert — für den großen Prompt auswählen)

★ = größter Hebel.

**Erfassung / eBay**
- ★ Katalog-Abgleich beim Anlegen: erkannte Nr. → Top-3-Katalog-Kandidaten,
  Typ + Min/Max automatisch ziehen (Mensch bestätigt nur). Der eigentliche
  Wertschöpfungsschritt.
- Foto direkt beim Anlegen hochladen (aktuell erst auf der Detailseite), inkl.
  Einfügen aus der Zwischenablage.
- Konfidenz-Flag pro Vorschlag (Nr. mit Kontextwort = sicher, bloße Titel-Nummer
  = unsicher).

**Katalog (fehlt als eigene Ebene)**
- ★ Digitaler Wiking/Siku-Katalog als pflegbare Tabelle (GK/Rawe importierbar).
  Voraussetzung für Matching, Wertermittlung und genauere Lücken.
- Wert-Historie: Katalogwerte mit Datum versionieren (Marktwert ändert sich).

**Sammlung / UX**
- Kombinierte Filter (Hersteller × Zustand × Serie × Preisrange) + gespeicherte
  Filter; Sortierung nach Wert/zuletzt hinzugefügt.
- Batch-Bearbeitung: mehrere Modelle markieren → Zustand/Serie/Konvolut setzen.
- Datenqualitäts-Listen: „ohne Foto", „ohne Zustand", „ohne Kaufdatum".

**Konvolut**
- Auto-Verteilung des Gesamtpreises auf die Kinder nach Katalog-Schätzwert
  (gewichtet), mit Anzeige „X € entfallen auf dieses Auto".
- Schnäppchen-Indikator: gezahlt vs. Summe der Katalogwerte pro Konvolut.

**Wert / Statistik**
- „Unrealisierter Zuwachs" = Katalogwert − bezahlt, pro Modell und gesamt.
- Dubletten als Verkaufskandidaten-Liste (oft „doppelt" in den Daten).

**Wunschliste (über Punkt 1 hinaus)**
- „gekauft" auf einem Wunsch → direkt vorausgefülltes Modell anlegen.
- Preis-Notiz „max. X €" pro Wunsch.

**Daten / Betrieb**
- ★ Auto-Backup täglich rotierend statt nur manuellem Knopf. **Vorbehalt:** läuft
  nur, wenn die App läuft → also beim App-Start + periodisch im Prozess, ODER als
  OS-Cron/Task dokumentieren (sonst kein Backup, wenn die App aus ist).
- Import-Dry-Run: vor Excel-Reimport zeigen, was neu/geändert wäre.
- Papierkorb/Undo für gelöschte Modelle.
- PDF-Katalog-Export (schöner Sammlungs-Ausdruck) neben xlsx.

**Qualität / Dev**
- CI (ruff/pytest/npm build) + pre-commit-Hook, sobald ein GitHub-Remote steht.
- Alembic wirklich nutzen, sobald das Schema wächst (wunsch, Katalog-Historie).
- E2E-Tests (Playwright) für die Kern-Flows.

---

## Abschluss jedes Laufs (Pflicht, gemäß AGENTS.md)
- Deps via **uv** ins `.venv`: `uv pip install -r requirements.txt`.
- `.venv/bin/ruff check app/ tests/` → sauber.
- `.venv/bin/mypy app/` → geänderte Dateien fehlerfrei.
- `.venv/bin/pytest -q` → grün (neue Wunsch-Endpoints mit einem Test abdecken).
- `cd frontend && npm run build` → grün.
- `ruff format` **nicht** projektweit anwenden (eigener `style:`-Commit später).
- Conventional Commits, kein Force-Push, keine Secrets (`.env`, `*.xlsx`,
  `media/`, `data/` bleiben ungetrackt).

## Noch offen / dein Input
- **GitHub:** aktuell kein Remote konfiguriert → nichts gepusht. Falls
  `github.com/diebugger-tech/ModellGarage` das Ziel ist: Repo anlegen,
  `git remote add origin …`, `.gitignore` prüfen, `git push -u origin develop`.
- **MCP:** „2 MCP servers need authentication" im Terminal → `/mcp`, falls die
  Server (z. B. Katalog-Abgleich) genutzt werden sollen.
