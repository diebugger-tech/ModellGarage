#!/usr/bin/env bash
# ModellGarage — Start unter Podman (Linux / macOS)
# Ausführen:  ./start-podman.sh   (ggf. vorher:  chmod +x start-podman.sh)
set -euo pipefail
cd "$(dirname "$0")"

echo "== ModellGarage - Podman-Start =="

if ! command -v podman >/dev/null 2>&1; then
  echo "Podman nicht gefunden. Installieren: https://podman.io/getting-started/installation"
  exit 1
fi

# macOS braucht eine Podman-Maschine (Linux startet Podman nativ)
if podman machine list --format '{{.Running}}' >/dev/null 2>&1; then
  if ! podman machine list --format '{{.Running}}' 2>/dev/null | grep -qi true; then
    echo "Starte die Podman-Maschine ..."
    podman machine start >/dev/null 2>&1 || true
  fi
fi

echo "Baue und starte den Container (erster Build dauert ein paar Minuten) ..."
podman compose up -d --build

url="http://localhost:8003"
echo "Warte, bis die App bereit ist ..."
for _ in $(seq 1 40); do
  if curl -sf "$url/api/health" >/dev/null 2>&1; then break; fi
  sleep 2
done

echo ""
echo "ModellGarage laeuft:  $url"
echo "Excel importieren:    im Browser auf 'Import' gehen und die .xlsx hochladen."
echo "Stoppen:              ./stop-podman.sh"

# Browser oeffnen (macOS: open, Linux: xdg-open)
{ command -v open >/dev/null 2>&1 && open "$url"; } \
  || { command -v xdg-open >/dev/null 2>&1 && xdg-open "$url"; } \
  || true
