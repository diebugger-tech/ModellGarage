# ModellGarage — Entwickler-Komfort (Ubuntu + Nix Home-Manager)
.PHONY: help install import dev dev-frontend build test clean

VENV := .venv
PY := $(VENV)/bin/python
PORT := 8137

help:
	@echo "ModellGarage — verfügbare Targets:"
	@echo "  make install       venv + Python-Deps (uv) + npm install"
	@echo "  make import         Excel → SQLite importieren"
	@echo "  make dev            Backend (uvicorn) auf :$(PORT) — serviert gebautes Frontend"
	@echo "  make dev-frontend   Vite Dev-Server (Hot-Reload, Proxy → Backend)"
	@echo "  make build          Frontend bauen (frontend/build)"
	@echo "  make test           pytest"
	@echo "  make clean          DB + Build-Artefakte löschen"

install:
	uv venv $(VENV)
	VIRTUAL_ENV="$(PWD)/$(VENV)" uv pip install -r requirements.txt
	cd frontend && npm install

import:
	$(PY) scripts/import_excel.py "2026-06-05 Modelle.xlsx"

dev:
	$(PY) -m uvicorn app.main:app --host 127.0.0.1 --port $(PORT) --reload

dev-frontend:
	cd frontend && npm run dev

build:
	cd frontend && npm run build

test:
	$(PY) -m pytest -q

clean:
	rm -f data/modellgarage.db
	rm -rf frontend/build frontend/.svelte-kit
