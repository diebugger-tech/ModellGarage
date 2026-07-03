"""Debug: was steht in den Nicht-ISO-Datumsfeldern?"""
import sqlite3
from pathlib import Path

db = sqlite3.connect(Path(__file__).resolve().parent.parent / "data" / "modellgarage.db")
c = db.cursor()

print("=== Nicht-ISO kaufdatum: Beispielwerte ===")
for r in c.execute("SELECT DISTINCT kaufdatum FROM modell WHERE kaufdatum IS NOT NULL AND kaufdatum NOT GLOB '____-__-__' LIMIT 15"):
    print(f"  [{r[0]}]")

print("=== Welche Serien/Hersteller haben Nicht-ISO-Datum? ===")
for r in c.execute("""SELECT k.hersteller, COUNT(*) FROM modell m JOIN katalog k ON m.katalog_id=k.id
                      WHERE m.kaufdatum IS NOT NULL AND m.kaufdatum NOT GLOB '____-__-__'
                      GROUP BY k.hersteller ORDER BY COUNT(*) DESC LIMIT 8"""):
    print(f"  {r[0]}: {r[1]}")
db.close()
