"""End-to-End: Backend serviert Frontend + API."""
import json
import urllib.request

BASE = "http://127.0.0.1:8137"


def fetch(path):
    with urllib.request.urlopen(BASE + path, timeout=10) as r:
        return r.status, r.read(), r.headers.get("content-type", "")


# Frontend-Root
s, body, ct = fetch("/")
print(f"GET /            → {s} | {ct} | {len(body)} bytes")
print(f"  enthält 'ModellGarage': {b'ModellGarage' in body or b'sveltekit' in body.lower()}")

# API weiterhin erreichbar
s, body, ct = fetch("/api/health")
print(f"GET /api/health  → {s} | {json.loads(body)}")

s, body, ct = fetch("/api/modelle?limit=1")
d = json.loads(body)
print(f"GET /api/modelle → {s} | total={d['total']}")

# Detail eines echten Modells
mid = d["items"][0]["id"]
s, body, ct = fetch(f"/api/modelle/{mid}")
print(f"GET /api/modelle/{mid} → {s} | {json.loads(body)['katalog']['typ'][:30]}")

print("\n=== E2E OK: ein Prozess serviert Frontend + API ===")
