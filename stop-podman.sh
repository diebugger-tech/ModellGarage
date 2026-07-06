#!/usr/bin/env bash
# ModellGarage — Stoppen (Linux / macOS)
cd "$(dirname "$0")"
echo "Stoppe ModellGarage ..."
# 'podman compose down' (ohne -v) stoppt nur den Container und LAESST die
# benannten Volumes stehen -> Fotos und DB bleiben erhalten.
podman compose down || true
echo "Gestoppt. Daten (DB + Fotos) bleiben in den Podman-Volumes erhalten."
echo ""
echo "WICHTIG - diese Volumes NIEMALS loeschen, sonst sind Fotos UND DB weg:"
echo "  modellgarage-media  (Fotos)      modellgarage-data  (Datenbank)"
echo "  Gefaehrlich:  podman volume rm modellgarage-media"
echo "                podman volume rm modellgarage-data"
echo "                podman machine reset"
echo "                podman system prune --volumes"
echo "Backup laeuft ueber den App-Export (Excel), NICHT ueber Git."
