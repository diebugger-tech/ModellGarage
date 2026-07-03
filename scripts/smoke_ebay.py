"""Testet den eBay-Text-Parser mit echten eBay-Titeln."""
import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8003"

# Echte Titel aus eBay-Suchergebnissen
FAELLE = [
    ('Wiking VW T2 Bus "Siebensitzer" Sondermodell IG T2 - 4145 - 1:87', "EUR 39,00"),
    ("VW Käfer 1303 IAA 2007, VW Käfer 1303 und VW Cabriolet 1302 WIKING 1:87 OVP", "EUR 27,00 Gebraucht"),
    ("Wiking 1:87 99861 - Werbemodelle 1985 Set PKW & LKW", "EUR 17,90 Neu"),
    ("Siku 1050 VW Golf rot 1:55 bespielt", "EUR 8,50"),
    ("Majorette Porsche 911 blau OVP neuwertig 1:64", "5,00 EUR"),
    ("Herpa MAN Sattelzug Spedition 1:87 neuwertig", "EUR 24,90"),
]


def post(payload):
    req = urllib.request.Request(
        BASE + "/api/ebay/parse-text", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


for titel, extra in FAELLE:
    s, d = post({"titel": titel, "extra": extra})
    print(f"\nTitel: {titel[:55]}")
    if s == 200:
        print(f"  → Hersteller: {d['hersteller']:<12} Typ: {d['typ']}")
        print(f"    Preis: {d['bezahlt']}  Zustand: {d['zustand']}  Maßstab: {d['massstab']}")
    else:
        print(f"  ✗ {s}: {d.get('detail')}")
