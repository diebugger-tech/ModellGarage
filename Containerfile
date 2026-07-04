# ModellGarage — Multi-Stage Container (Podman-kompatibel)
# Stage 1: Node baut das SvelteKit-Frontend
# Stage 2: schlankes Python-Image serviert Backend + gebautes Frontend
# Ein Prozess, ein Port (8003). Läuft unter Podman auf Windows.

# ---------------------------------------------------------------------------
# Stage 1 — Frontend-Build
# ---------------------------------------------------------------------------
FROM docker.io/library/node:22-slim AS frontend-build

WORKDIR /build/frontend

# Nur Manifeste zuerst → Layer-Cache für npm ci
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Restliche Frontend-Quellen + Build
COPY frontend/ ./
RUN npm run build
# Ergebnis: /build/frontend/build

# ---------------------------------------------------------------------------
# Stage 2 — Python-Runtime
# ---------------------------------------------------------------------------
FROM docker.io/library/python:3.11-slim AS runtime

# Kein .pyc, ungepufferte Logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production

WORKDIR /app

# Python-Deps zuerst (Layer-Cache)
COPY requirements.txt ./
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# Backend-Code
COPY app/ ./app/
COPY scripts/ ./scripts/

# Gebautes Frontend aus Stage 1 an den vom Backend erwarteten Ort
COPY --from=frontend-build /build/frontend/build ./frontend/build

# Laufzeit-Verzeichnisse (werden i.d.R. als Volume überschrieben)
RUN mkdir -p /app/data /app/media

EXPOSE 8003

# Ein Prozess: FastAPI serviert Frontend + /media + /api
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
