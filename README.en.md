# ModellGarage

[🇩🇪 Deutsch](README.md) · 🇬🇧 **English**

> **Inventory & valuation app for model-car collections.**
> Turns a static collector's Excel sheet into a lightweight, polished app —
> with catalog matching, "lot" handling and optional eBay capture.

## Screenshots

| Gallery | Statistics |
|:---:|:---:|
| [![Gallery – the collection at a glance](docs/screenshots/landingpage.png)](docs/screenshots/landingpage.png) | [![Statistics – the collection in numbers](docs/screenshots/statistik.png)](docs/screenshots/statistik.png) |
| Search, filter and sort the collection | Value over time, purchases per year, condition split |

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

1. **Install Podman** — via the **official, signed** installer:
   - **Windows:** Podman Desktop via winget in an **Administrator PowerShell**:
     ```powershell
     winget install -e --id RedHat.Podman-Desktop
     ```
     …or download the signed `.exe` from https://podman-desktop.io/ and run it.
     Podman Desktop also sets up **WSL2** (the Linux subsystem Podman needs) —
     this needs **admin rights once**, and Windows usually requires **a reboot**
     for the first WSL2 setup.
   - **macOS/Linux:** Podman or Podman Desktop from https://podman.io/ (or your
     package manager).

   On first launch of Podman Desktop, confirm "Initialize / Start" for the Podman
   machine once.
2. **Get the project:** on GitHub click the green **"Code"** button → **"Download
   ZIP"**, then unzip — or `git clone`.

> **A note on admin rights:** admin is only needed **once**, to install Podman
> Desktop / WSL2 (official, signed installer). **Running** ModellGarage afterwards
> needs **no admin and no terminal**: just double-click `start-podman.bat` to start
> and `stop-podman.bat` to stop — or do everything from the Podman Desktop UI.

### Windows — start the app

Podman Desktop installed and running (see "First, on every system" above)? Then
you need **no admin and no terminal** anymore:

1. Go into the unzipped project folder — the one that contains `start-podman.bat`
   (usually called `ModellGarage-main`, possibly nested twice).
2. **Double-click `start-podman.bat`.** The first run builds the container (a few
   minutes), then the browser opens at http://localhost:8003.
3. **Stop:** double-click **`stop-podman.bat`**.

This is what it looks like when everything is up — the `modellgarage` container
shows **RUNNING** on port **8003** in Podman Desktop:

[![Podman Desktop – modellgarage container running on port 8003](docs/screenshots/podman.png)](docs/screenshots/podman.png)

> **Why the container route?** ModellGarage runs **isolated** in a Podman
> container (rootless, inside a WSL2 VM), separated from your Windows system. Your
> collection data stays local, and you install Podman Desktop via the **official,
> signed** installer — no self-made remote script.

> **What does `start-podman.bat` do?** The batch file only launches the
> **bundled, readable** `start-podman.ps1` from the same folder — it fetches
> **nothing from the internet** and needs **no admin**. The `-ExecutionPolicy
> Bypass` in it applies only to that single call of the local script (needed
> because Windows otherwise blocks files from a downloaded ZIP) — your machine's
> execution policy stays unchanged. You can open `start-podman.ps1` and check it
> first: it just builds the image from the local `Containerfile`, creates the
> volumes and starts the container on port 8003.

> Note: the `make …` commands below are for development on **Linux/macOS** only.
> On Windows always use the `*-podman.bat` scripts.

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

### Then (all systems): load data

The app is running — now bring data in. There are three ways:

#### 1. Try it first (recommended)

Without your own data, import the bundled test data: click **"Import"** at the
top and upload **`examples/testdaten.xlsx`** (14 fictional models across Wiking,
Siku, Majorette, Playmobil — including duplicates and gaps). You instantly see
the gallery, statistics, gaps and wishlist in action. (Alternatively the smaller
`examples/beispiel-sammlung.xlsx`.) All values are made up.

**Lots (Konvolute) and the wishlist** are **not** created by the Excel import. To
test those too, run the seed script once after importing (creates two example
lots with weighted price distribution plus wishlist entries):

```bash
python scripts/seed_testdaten.py        # app must be running (http://localhost:8003)
```

#### 2. Import your own collection

The import expects a **specific column schema** (German headers). An arbitrary
spreadsheet with different columns will **not** import meaningfully — the expected
columns are:

| Hersteller | Nr. | Min. | Max. | Typ | Farbe | Zustand | Bemerkung | bezahlt | Schätzwert | Anzahl | Kaufdatum |

The easiest way to get a matching template is **Export**:

1. Click **"Export"** in the app → you get an `.xlsx` with exactly the right
   columns (empty if there's no data yet).
2. Fill in your collection — one row per model. `Zustand` is `z0`/`z1`/`z2`,
   `Kaufdatum` e.g. `15.11.2020` or `2020-11-15`.
3. Upload the file again via **"Import"**.

Export and import match: an exported spreadsheet re-imports unchanged, without
losing values or manufacturer. Alternatively use `examples/testdaten.xlsx` as a
template and replace the rows.

#### 3. No Excel — capture directly in the app

You don't need a spreadsheet: click **"+ Anlegen"** to add models one by one
(with catalog matching and a condition dropdown). For eBay purchases there's the
quick-capture at `/neu` — paste title/description and the app suggests
manufacturer, number, color, price and condition.

> Your data (database + photos) lives in the Podman volumes and is automatically
> back on the next start.

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

## Volumes & data safety

The app runs as a **single Podman container**, but your data deliberately lives **outside** it in two named volumes. They survive every restart and rebuild — the start scripts rebuild the container each time (`podman rm -f` / `compose up --build`), while the volumes stay in place:

| Volume | Contents | Path in container |
|--------|----------|-------------------|
| `modellgarage-media` | uploaded **photos** | `/app/media` |
| `modellgarage-data`  | the **database** | `/app/data/modellgarage.db` |

> ⚠️ **Never delete these volumes — otherwise all photos and the entire collection are lost for good.**

Dangerous commands that destroy the data:

```bash
podman volume rm modellgarage-media   # deletes all photos
podman volume rm modellgarage-data    # deletes the database
podman machine reset                  # deletes ALL volumes on the machine
podman system prune --volumes         # deletes unused volumes
```

By contrast, `stop-podman.*` and `podman compose down` (without `-v`) are **safe** — they only stop the container and keep the volumes.

**Backup** goes through the **in-app export** (Excel), *not* through Git: the volumes (`media/`, `data/`) are intentionally excluded from the repo via `.gitignore`. Export regularly and keep the file outside the container.

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
