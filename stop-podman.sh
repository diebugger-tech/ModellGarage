#!/usr/bin/env bash
# ModellGarage — Stoppen (Linux / macOS)
cd "$(dirname "$0")"
echo "Stoppe ModellGarage ..."
podman compose down || true
echo "Gestoppt. Daten (DB + Fotos) bleiben in den Podman-Volumes erhalten."
