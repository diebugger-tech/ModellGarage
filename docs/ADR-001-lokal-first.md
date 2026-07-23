# ADR-001: ModellGarage ist eine lokale Open-Source-Anwendung (Lokal First)

**Status:** beschlossen · 2026-07-23
**Kontext-Diskussion:** Web-App vs. lokale Anwendung, Monetarisierung, Datenschutz

---

## Entscheidung

ModellGarage ist und bleibt eine **lokale Anwendung** unter **MIT-Lizenz (Open
Source)**. Es gibt **kein Geschäftsmodell** — kein Abo, kein Hosting durch uns,
keine Nutzerkonten.

1. **Lokal First:** Alle Kernfunktionen (Katalog, Galerie, Statistik, Import/
   Export, Konvolute, Wunschliste) funktionieren vollständig **offline**. Die
   Daten (SQLite-DB + Fotos) bleiben ausschließlich beim Sammler.
2. **Auslieferung als Container (Podman, rootless):** bewusste Entscheidung für
   maximale Laufzeit-Isolation — die App läuft gekapselt (rootless, unter
   Windows zusätzlich in der WSL2-VM), getrennt vom Host-System. Der Preis
   (einmalige Podman/WSL2-Einrichtung mit Admin-Rechten) wird in Kauf genommen.
   Installation ausschließlich über **offizielle, signierte Installer** — kein
   selbst gehostetes Remote-Skript (`irm | iex` wurde entfernt).
3. **Externe Dienste nur als Opt-in (Phase 3+):** Geplante Netzfunktionen
   (eBay-Wertermittlung via Browse-API, evtl. Foto-Erkennung) sind **ab Werk
   deaktiviert**. Aktivierung nur ausdrücklich durch den Nutzer in den
   Einstellungen, mit Klartext-Hinweis, welche Daten an welchen Dienst gehen
   (z. B. „Fotos werden zur Erkennung an X gesendet"). Privacy by default.
4. **Keine Dritt-Requests im Frontend:** Schriften und Assets werden lokal
   ausgeliefert (self-hosted, @fontsource). Kein CDN, kein Analytics, kein
   Tracking. (Google-Fonts-Einbindung wurde entfernt — DSGVO.)

## Verworfene Alternativen

- **Gehostete Web-App mit Abo:** betriebswirtschaftlich denkbar, aber bewusst
  verworfen — sie macht aus dem Projekt einen *Betrieb* (Hosting, Accounts,
  Support, AVV/DSGVO-Verantwortlichkeit für fremde Sammlungsdaten und Fotos,
  laufende API-Kosten). Widerspricht dem Ziel: Hobby-Projekt, Daten beim
  Sammler.
- **Native Desktop-App (.exe / PyInstaller / Tauri, ggf. + OS-Sandbox):**
  einfachste Installation, aber schwächere bzw. keine Laufzeit-Isolation.
  Verworfen zugunsten der Container-Isolation. Kann als zusätzlicher
  Auslieferungsweg wieder geprüft werden, falls die Podman-Hürde sich als zu
  hoch für die Zielgruppe erweist.
- **KI-Automatik (Foto → Datensatz ohne Bestätigung):** verworfen. Es gilt
  weiterhin: *Die App schlägt vor, der Sammler entscheidet* (wie beim Zustand
  und der eBay-Schnellerfassung). Erkennung liefert höchstens Top-Kandidaten.

## Konsequenzen

- Architektur bleibt: FastAPI + SvelteKit + SQLite, ein Container, ein Port.
- `Containerfile`/`compose.yml` sind zugleich Dev-/CI-Umgebung und
  Auslieferung.
- Jede neue Funktion muss die Frage beantworten: **„Geht das offline?"** Wenn
  nein → Opt-in-Schalter, Default aus, Klartext-Hinweis.
- Beiträge (PRs/Issues) sind willkommen; Monetarisierungs-Features sind out of
  scope.
