"""Smoke-Test der API-Endpoints."""
import json
import urllib.request

BASE = "http://127.0.0.1:8137"


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=10) as r:
        return r.status, json.loads(r.read())


print("=== /api/health ===")
print(get("/api/health"))

print("=== /api/statistik ===")
s, data = get("/api/statistik")
print("status", s)
print("  Modelle:", data["anzahl_modelle"], "| Katalog:", data["anzahl_katalog"])
print("  Summe bezahlt:", round(data["summe_bezahlt"], 2))
print("  Summe min/max:", round(data["summe_min"], 2), "/", round(data["summe_max"], 2))
print("  Top-Hersteller:", list(data["hersteller"].items())[:5])

print("=== /api/modelle?q=Käfer&limit=3 ===")
s, data = get("/api/modelle?q=K%C3%A4fer&limit=3")
print("status", s, "| total:", data["total"])
for m in data["items"]:
    k = m["katalog"]
    print(f"  #{m['id']} {k['katalog_nr']} {k['typ'][:30]} | {m['zustand']} | {m['bezahlt']}€ | min/max {k['min_euro']}/{k['max_euro']}")

print("=== /api/modelle?hersteller=Siku&limit=2 ===")
s, data = get("/api/modelle?hersteller=Siku&limit=2")
print("status", s, "| total:", data["total"])
for m in data["items"]:
    print(f"  #{m['id']} {m['katalog']['typ'][:30]} | farbe={m['farbe']}")

print("=== /api/statistik/hersteller (Anzahl) ===")
s, data = get("/api/statistik/hersteller")
print("status", s, "| Hersteller-Anzahl:", len(data))
