"""Smoke-Test der neuen Backend-Endpoints (Statistik, Konvolut, Extras)."""
import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8003"


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=15) as r:
        return r.status, json.loads(r.read())


def post(path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else b""
    req = urllib.request.Request(BASE + path, data=data,
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


print("=== Dashboard ===")
s, d = get("/api/statistik/dashboard")
print(f"  status {s}")
print(f"  Zukäufe/Jahr: {len(d['zukaeufe_pro_jahr'])} Jahre, z.B. {d['zukaeufe_pro_jahr'][:2]}")
print(f"  Wertentwicklung: {len(d['wertentwicklung'])} Punkte, Endwert {d['wertentwicklung'][-1] if d['wertentwicklung'] else '-'}")
print(f"  Hersteller-Verteilung: {[(h['name'], h['anzahl']) for h in d['hersteller_verteilung'][:3]]}")
print(f"  Zustand: {d['zustand_verteilung']}")
print(f"  Histogramm: {[(h['klasse'], h['anzahl']) for h in d['preis_histogramm']]}")
print(f"  Top teuerste #1: {d['top_teuerste'][0] if d['top_teuerste'] else '-'}")

print("\n=== Dubletten ===")
s, d = get("/api/extras/dubletten")
print(f"  status {s} | {d['anzahl']} Dubletten-Nummern, Top: {d['dubletten'][:2]}")

print("\n=== Dubletten-Check (30/6K. Wiking) ===")
s, d = get("/api/extras/dubletten-check?hersteller=Wiking&katalog_nr=30/6K.")
print(f"  status {s} | vorhanden: {d['vorhanden']}")

print("\n=== Wunschliste Wiking ===")
s, d = get("/api/extras/wunschliste?hersteller=Wiking")
print(f"  status {s} | Bereich {d.get('bereich')}, {len(d.get('luecken', []))} Lücken, z.B. {d.get('luecken', [])[:8]}")

print("\n=== Konvolut anlegen + Kinder + Preise verteilen ===")
s, kon = post("/api/konvolut", {"quelle": "Test-Auktion", "gesamtpreis": 100.0, "datum": "2024-01-01"})
print(f"  Konvolut angelegt: id={kon['id']}")
# Zwei Modelle zuordnen (id 4 = Käfer 50-75€, id 76 = billiges)
for mid in (4, 5):
    s, k = post(f"/api/konvolut/{kon['id']}/modell/{mid}")
print(f"  2 Kinder zugeordnet, anzahl_kinder={k['anzahl_kinder']}")
s, v = post(f"/api/konvolut/{kon['id']}/preise-verteilen")
print(f"  Preise verteilt (gewichtet): {[(a['modell_id'], a['bezahlt']) for a in v['anteile']]}")
# aufräumen
urllib.request.urlopen(urllib.request.Request(f"{BASE}/api/konvolut/{kon['id']}", method="DELETE"))
print("  Test-Konvolut gelöscht")
