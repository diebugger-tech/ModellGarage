# Handoff — eBay-Schnellerfassung liest Artikelbeschreibung

Stand: uncommitted auf Branch `develop`. Sandbox-Checks grün
(pytest 11 passed, `ruff check` sauber, `npm run build` grün).

## Geänderte Dateien
- `app/services/ebay_parse.py` — `parse_text(titel, extra, beschreibung)`;
  neue Extraktoren `_katalog_nr`, `_katalog_nr_bare`, `_farbe`; explizites
  `z0/z1/z2` hat jetzt Vorrang.
- `app/routers/ebay.py` — `EbayTextIn.beschreibung`.
- `app/routers/konvolut.py` — ungenutzten Import `func` entfernt (ruff F401).
- `frontend/src/lib/api.js` — `ebayParseText(titel, extra, beschreibung)`.
- `frontend/src/routes/neu/+page.svelte` — Beschreibungs-Textarea, Mapping auf
  `katalog_nr` + `farbe`, Auto-Dublettencheck, Info-Text.
- `tests/test_ebay_parse.py` — 7 neue Unit-Tests (NEU).
- `AGENTS.md`, `README.md`, `docs/HANDOFF_ebay-beschreibung.md` — Doku.

---

## Prompt für Claude Code (VSCodium-Terminal, im Projekt-Root)

> Kopiere alles zwischen den Linien in das Claude-Code-Terminal.

---
Wir haben in der eBay-Schnellerfassung die Artikelbeschreibung ergänzt
(Katalog-/Wiking-Nr. + Farbe). Die Änderungen sind uncommitted auf `develop`.
Bitte finalisiere sauber gemäß AGENTS.md:

1. Dev-Umgebung sicherstellen (Host = Ubuntu + Nix, **uv** statt pip):
   `uv pip install -r requirements.txt` ins projektlokale `.venv`.
2. Qualität durchlaufen lassen und Fehler zeigen (nicht blind fixen):
   - `.venv/bin/ruff check app/ tests/`
   - `.venv/bin/ruff format --check app/ tests/`  (nur anzeigen — NICHT
     projektweit formatieren, das wäre ein eigener `style:`-Commit)
   - `.venv/bin/mypy app/`
   - `.venv/bin/pytest -q`
   - `cd frontend && npm run build`
3. `git diff` zusammenfassen und mit mir kurz durchgehen (Code-Review).
4. Danach committen (Conventional Commit, kein Force-Push, keine Secrets):
   `feat(ebay): Katalog-Nr. und Farbe aus Artikelbeschreibung parsen`
   Body: Beschreibungsfeld in Schnellerfassung, neue Parser + Tests,
   Doku aktualisiert.

Falls `mypy` neue Typfehler in den geänderten Dateien zeigt, behebe nur die,
nicht das ganze Repo. Falls `uv`/Kommandos blockiert sind, frag mich, statt zu
wiederholen.
---

---

## Ideen & Verbesserungen (Backlog)

### eBay-Beschreibung / Erfassung
1. **Konvolut-Modus aus einer Beschreibung.** Eine Beschreibung listet oft
   mehrere Modelle mit mehreren Nummern. Ein Parser-Modus, der *alle* Nr.-Farbe-
   Paare findet und eine bestätigbare Liste (statt eines Formulars) liefert —
   passt genau zum bounded Konvolut-Workflow.
2. **Farbliste in Katalog/DB statt Hardcode.** Die Farb-Basisliste im Code
   pflegt sich schlecht. Kandidat: bekannte Farben pro Hersteller aus dem
   Katalog ziehen und damit matchen (robuster, weniger False-Negatives).
3. **Katalog-Abgleich statt reiner Text-Heuristik.** Sobald ein digitaler
   Wiking/Siku-Katalog vorliegt: erkannte Nr. gegen den Katalog validieren und
   Typ/Wert automatisch ziehen (der eigentliche Wertschöpfungsschritt laut
   AGENTS.md).
4. **Konfidenz anzeigen.** Pro vorgeschlagenem Feld ein „sicher/unsicher"-Flag
   (z.B. Nr. mit Kontextwort = sicher, bloße Titel-Nummer = unsicher), damit der
   Sammler weiß, was er besonders prüfen muss.

### Browser-Weg (optional, ohne Copy-Paste)
5. **Claude in Chrome / eigener eingeloggter Browser** liest die offene eBay-
   Seite aus (kein 403, weil echter Browser). Spart das manuelle Kopieren —
   sinnvoll erst, wenn die Text-Erfassung stabil ist.

### Qualität / Infra
6. **CI-Minimal** (GitHub Actions o.ä.): `ruff check`, `pytest`, `npm run build`
   bei jedem Push — sobald ein Remote existiert.
7. **`ruff format` projektweit** als einmaliger `style:`-Commit, danach im
   Pre-Commit-Hook erzwingen (aktuell wären 14 Dateien betroffen).
8. **mypy in der Pipeline** (steht in requirements, aber ungenutzt).

### Git / GitHub
9. **Kein Remote konfiguriert** — nichts ist auf GitHub. Falls
   `github.com/diebugger-tech/ModellGarage` das Ziel ist: Repo anlegen,
   `git remote add origin …`, `.gitignore` prüfen (media/, data/, .env,
   *.xlsx sind privat), dann `git push -u origin develop`.
