# ModellGarage — Makefile
# Ein-Kommando-Kriterium: `make start` bringt Backend + Frontend hoch.

PYTHON       := python3
BACKEND_PORT := 8003
FRONTEND_PORT:= 5173
APP          := app.main:app
PIDDIR       := .run

.PHONY: help setup install-backend install-frontend start start-prod build \
        test migrate migration stop status kill-backend kill-frontend clean import \
        podman-build podman-up podman-down podman-logs podman-import

help:  ## Zeigt diese Hilfe
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# --- Setup -----------------------------------------------------------------

setup: install-backend install-frontend  ## Alles installieren (Backend + Frontend)

install-backend:  ## Python-Deps + venv
	$(PYTHON) -m venv .venv
	.venv/bin/pip install -U pip
	.venv/bin/pip install -r requirements.txt

install-frontend:  ## Node-Deps (SvelteKit)
	cd frontend && npm ci

import:  ## Excel → SQLite importieren
	.venv/bin/python scripts/import_excel.py "2026-06-05 Modelle.xlsx"

# --- Entwicklung (ohne overmind — reines Shell mit PID-Datei) --------------

start:  ## Dev-Server starten (uvicorn :8003 + vite :5173, Hot-Reload)
	@mkdir -p $(PIDDIR)
	@echo "→ Backend  http://127.0.0.1:$(BACKEND_PORT)  (uvicorn --reload)"
	@.venv/bin/uvicorn $(APP) --reload --port $(BACKEND_PORT) \
	    > $(PIDDIR)/backend.log 2>&1 & echo $$! > $(PIDDIR)/backend.pid
	@echo "→ Frontend http://127.0.0.1:$(FRONTEND_PORT)  (vite dev, Proxy → Backend)"
	@cd frontend && npm run dev -- --port $(FRONTEND_PORT) \
	    > ../$(PIDDIR)/frontend.log 2>&1 & echo $$! > $(PIDDIR)/frontend.pid
	@sleep 1
	@echo "✓ gestartet. Logs: $(PIDDIR)/*.log  ·  Stoppen: make stop"

stop:  ## Alle Dev-Prozesse stoppen
	@-test -f $(PIDDIR)/backend.pid  && kill $$(cat $(PIDDIR)/backend.pid)  2>/dev/null && echo "✓ Backend gestoppt"  || true
	@-test -f $(PIDDIR)/frontend.pid && kill $$(cat $(PIDDIR)/frontend.pid) 2>/dev/null && echo "✓ Frontend gestoppt" || true
	@-pkill -f "uvicorn $(APP)" 2>/dev/null || true
	@-pkill -f "vite.*$(FRONTEND_PORT)" 2>/dev/null || true
	@rm -f $(PIDDIR)/*.pid
	@echo "✓ alle Dev-Prozesse beendet"

status:  ## Zeigt laufende Dev-Prozesse
	@echo "Backend  ($(BACKEND_PORT)):" ; ss -tlnp 2>/dev/null | grep :$(BACKEND_PORT)  || echo "  — nicht aktiv"
	@echo "Frontend ($(FRONTEND_PORT)):"; ss -tlnp 2>/dev/null | grep :$(FRONTEND_PORT) || echo "  — nicht aktiv"

# --- Produktion (ein Prozess, ein Port) ------------------------------------

build:  ## SvelteKit bauen (adapter-static)
	cd frontend && npm run build

start-prod: build  ## FastAPI serviert gebautes Frontend + /media (ein Prozess)
	.venv/bin/uvicorn $(APP) --host 0.0.0.0 --port $(BACKEND_PORT)

# --- Datenbank (Alembic) ---------------------------------------------------

migrate:  ## Migrationen auf head bringen
	ALEMBIC_SYNC_MODE=1 .venv/bin/python -m alembic upgrade head

migration:  ## Neue Migration erstellen (NAME= angeben)
	ALEMBIC_SYNC_MODE=1 .venv/bin/python -m alembic revision --autogenerate -m "$(NAME)"

# --- Container (Podman — Deployment-Ziel Windows) --------------------------

podman-build:  ## Container bauen (Multi-Stage)
	podman build -t modellgarage:latest -f Containerfile .

podman-up:  ## Container starten (compose, Port 8003)
	podman compose up -d --build

podman-down:  ## Container stoppen
	podman compose down

podman-logs:  ## Container-Logs folgen
	podman compose logs -f

podman-import:  ## Excel im laufenden Container importieren
	podman exec modellgarage python scripts/import_excel.py "2026-06-05 Modelle.xlsx"

# --- Qualität --------------------------------------------------------------

test:  ## Tests ausführen (Ein-Kommando-Kriterium!)
	.venv/bin/pytest -v

# --- Ports / Aufräumen -----------------------------------------------------

kill-backend:  ## Backend-Port freigeben
	-kill -9 $$(ss -tlnp | grep :$(BACKEND_PORT) | awk '{print $$NF}' | cut -d= -f2 | cut -d, -f1) 2>/dev/null || true

kill-frontend:  ## Frontend-Port freigeben
	-kill -9 $$(ss -tlnp | grep :$(FRONTEND_PORT) | awk '{print $$NF}' | cut -d= -f2 | cut -d, -f1) 2>/dev/null || true

clean:  ## Temp-Dateien löschen
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	rm -rf $(PIDDIR)
