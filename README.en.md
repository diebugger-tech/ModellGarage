# ModellGarage

[🇩🇪 Deutsch](README.md) · 🇬🇧 **English**

> **Inventory & valuation app for model-car collections.**
> Turns a static collector's Excel sheet into a lightweight, polished app —
> with catalog matching, "lot" handling and optional eBay capture.

---

## Idea

A passionate collector used to track their model cars (Wiking, Siku, Majorette,
Matchbox …) in Excel. ModellGarage turns that data into a real app: searchable,
mobile-friendly, with photos and value estimates.

**Core benefits:**
- Avoid buying duplicates (searchable collection)
- Keep an eye on total value (catalog estimates)
- Break down **lots** (auction bundles) cleanly
- Document condition & photos per model

---

## Install (Windows · macOS · Linux)

On all three systems ModellGarage runs as a **container via Podman** — one
window, one port (`http://localhost:8003`). No Python/Node install required.

**First, on every system:**

1. **Install Podman Desktop:** https://podman.io/getting-started/installation
   (on first launch, confirm "Initialize / Start" for the Podman machine once).
2. **Get the project:** on GitHub click the green **"Code"** button → **"Download
   ZIP"**, then unzip — or `git clone`.

### Windows — fastest (one command)

Easiest path: **one** command installs Podman, fetches the project (no `git`,
via ZIP) and starts the app. Open **PowerShell as Administrator** (Start → type
"PowerShell" → right-click → *Run as administrator*) and paste:

```powershell
irm https://raw.githubusercontent.com/diebugger-tech/ModellGarage/main/install-windows.ps1 | iex
```

The installer tells you if a **reboot** is needed once (first-time WSL2 setup) —
just paste the same command again after rebooting. At the end the browser opens
at http://localhost:8003.

### Windows — manual (double-click)

3. In the unzipped folder, double-click **`start-podman.bat`**.
   The first start builds the container (a few minutes) and then opens the
   browser at http://localhost:8003.
4. Stop: double-click **`stop-podman.bat`**.

### macOS / Linux

3. In a terminal, `cd` into the folder and run:
   ```bash
   ./start-podman.sh
   ```
   (builds the container, waits, opens the browser at http://localhost:8003)
4. Stop:
   ```bash
   ./stop-podman.sh
   ```
   Or via `make`: `make podman-up` / `make podman-down` / `make podman-logs`.

### Then (all systems)

5. **Import your Excel:** in the app, click **"Import"** at the top and upload
   your `.xlsx` collection file. The collection then appears in the gallery.
   Database and photos persist in the Podman volumes — they're back on next start.

> **Just want to try it?** Without your own data you can import the bundled sample
> collection **`examples/beispiel-sammlung.xlsx`** (18 fictional models from
> Wiking, Siku, Majorette and others) — an instant look at the gallery,
> statistics, gaps and wishlist. The file contains made-up demo data only.

> Note: if `podman compose` reports that "compose" is missing, enable "Compose"
> in Podman Desktop under *Settings → Extensions* (or install `podman-compose`).
> The scripts themselves don't need changing.

### Development

```bash
make setup      # venv + Python deps + npm ci
make import     # Excel → SQLite (once)
make start      # backend :8003 + frontend :5173 (hot reload)
make start-prod # build frontend + FastAPI serves everything on :8003
make test       # pytest
make help       # all targets
```

---

## What makes the app special

1. **Catalog-based identity.** Every model has a manufacturer catalog number
   (Wiking `30/6K.`, Siku `1050`, …). It's **not on the model itself** but comes
   from the collector catalog. Values (min/max) live in the catalog, not on each
   individual model (no duplicate maintenance of identical values).
2. **Lot handling.** Buying several cars in one auction without per-item detail:
   the lot is a parent record, each car a child, the individual price is
   **weighted by catalog estimate** (not total ÷ count).
3. **Condition stays manual.** Condition (z0/z1/z2) is decided by the collector
   on inspection — the app only offers a dropdown.
4. **eBay quick-capture (no API).** eBay blocks server fetches (403). Instead the
   collector pastes the **title**, optional **price/condition** and optionally the
   **item description** into `/neu`; the app parses the text locally (no network)
   and pre-fills manufacturer, type, **catalog number**, **color**, price,
   condition and scale as suggestions — number and color usually come from the
   description. Everything stays a suggestion the collector confirms.
5. **Photos & eBay API (later).** Photos are uploaded manually per model. A real
   eBay import via the Browse API (developer account + OAuth) is Phase 3, optional.

---

## Tech stack

| Layer      | Choice                    | Why                                             |
|------------|---------------------------|-------------------------------------------------|
| Backend    | **FastAPI** (async)       | Fast, auto Swagger, Pydantic V2                 |
| DB         | **SQLite** (aiosqlite)    | Lightest DB — one file, no server, relational   |
| ORM        | SQLAlchemy 2.x            | `create_all` in MVP, Alembic prepared           |
| Frontend   | **SvelteKit** (Svelte 5)  | Fast, PWA-ready; `adapter-static`               |
| Deployment | **Podman** (Windows)      | One container, one process, one port (8003)     |
| Photos     | Local `media/` folder     | Download/store images instead of linking        |

**Design principle:** lightweight. Serverless DB, thin backend, an editorial-style
frontend (inspired by classicdriver.com). No MongoDB/Postgres, no Kubernetes.

---

## Status

🚀 **MVP running.** Excel import (~6,300 models, ~3,250 catalog entries), backend
(CRUD, search, filter, sort, statistics, Excel export, photo upload), gallery +
detail in a Classic-Driver style, single-process serving of frontend + API +
`/media`, Podman deployment for Windows.

**Done (Phase 2 / 2b):** lot UI (parent/child, weighted price, photos), manual
wishlist, duplicate warnings, statistics charts, photo lightbox, manufacturer
normalization, eBay quick-capture incl. item description (catalog number + color),
purchase-year filter/search/display, catalog matching when adding, data-quality
filters, rotating auto-backup, Excel-import regression test.

**Open (Phase 3):** eBay import via Browse API, multi-capture from a lot
description, editable catalog (GK/Rawe).

---

## Contributing

The app is entirely in German. An **in-app language switcher (DE/EN)** is
intentionally not included (the audience is German-speaking). If you'd like one,
feel free to open an **issue** or contribute a **pull request** — suggestions and
improvements are welcome.

---

## License

MIT (see `LICENSE`).
