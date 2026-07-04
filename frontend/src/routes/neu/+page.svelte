<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { getHersteller, erstelleModellVoll, ebayParseText, checkDublette, getKatalogKandidaten } from '$lib/api.js';

  let hersteller = $state([]);
  let laeuft = $state(false);
  let fehler = $state(null);
  let dublettenWarnung = $state(null);
  let dubTimer;
  let katalogKandidaten = $state([]);
  let katTimer;

  // eBay-Schnellerfassung
  let ebayTitel = $state('');
  let ebayExtra = $state('');
  let ebayBeschreibung = $state('');
  let ebayLaeuft = $state(false);
  let ebayHinweis = $state(null);
  let ebayInfo = $state(false);

  // Felder = 1:1 die Excel-Spalten
  let f = $state({
    hersteller: '', katalog_nr: '', typ: '', serie: '',
    min_euro: '', max_euro: '', quelle: '',
    farbe: '', zustand: '', bemerkung: '',
    bezahlt: '', schaetzwert: '', kaufdatum: '', anzahl: 1
  });

  onMount(async () => { hersteller = await getHersteller(); });

  async function ebayUebernehmen() {
    if (!ebayTitel.trim()) return;
    ebayLaeuft = true; ebayHinweis = null;
    try {
      const v = await ebayParseText(ebayTitel, ebayExtra, ebayBeschreibung);
      if (v.hersteller) f.hersteller = v.hersteller;
      if (v.typ) f.typ = v.typ;
      if (v.katalog_nr) f.katalog_nr = v.katalog_nr;
      if (v.farbe) f.farbe = v.farbe;
      if (v.bezahlt != null) f.bezahlt = v.bezahlt;
      if (v.zustand) f.zustand = v.zustand;
      if (v.bemerkung) f.bemerkung = v.bemerkung;
      if (v.katalog_nr) pruefeDublette();
      ebayHinweis = 'Übernommen — bitte prüfen und ggf. korrigieren. '
        + (v.hersteller ? '' : 'Hersteller nicht erkannt. ')
        + (v.katalog_nr
            ? 'Katalog-Nr. „' + v.katalog_nr + '" aus der Beschreibung übernommen — bitte gegen den Katalog prüfen.'
            : 'Katalog-Nr. nicht gefunden — Artikelbeschreibung mit einfügen hilft.');
    } catch (e) {
      ebayHinweis = '⚠ ' + e.message;
    } finally {
      ebayLaeuft = false;
    }
  }

  function num(v) { return v === '' || v == null ? null : Number(v); }

  // Textarea wächst automatisch mit dem Inhalt (kein Maus-Ziehen nötig).
  function autoGrow(e) {
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 600) + 'px';
  }

  // Live-Dublettencheck bei Hersteller + Katalog-Nr.
  function pruefeDublette() {
    clearTimeout(dubTimer);
    dublettenWarnung = null;
    const h = f.hersteller.trim(), nr = f.katalog_nr.trim();
    sucheKatalog();
    if (!h || !nr) return;
    dubTimer = setTimeout(async () => {
      try {
        const r = await checkDublette(h, nr);
        if (r.vorhanden > 0) {
          dublettenWarnung = `Achtung: „${h} ${nr}" hast du bereits ${r.vorhanden}× in der Sammlung.`;
        }
      } catch { /* ignore */ }
    }, 350);
  }

  // Katalog-Abgleich: Top-3-Kandidaten zur Nr./zum Typ vorschlagen.
  function sucheKatalog() {
    clearTimeout(katTimer);
    const h = f.hersteller.trim(), nr = f.katalog_nr.trim(), typ = f.typ.trim();
    if (!nr && !typ) { katalogKandidaten = []; return; }
    katTimer = setTimeout(async () => {
      try {
        katalogKandidaten = await getKatalogKandidaten({ hersteller: h, katalog_nr: nr, typ });
      } catch { katalogKandidaten = []; }
    }, 350);
  }

  function uebernehmeKandidat(k) {
    f.hersteller = k.hersteller;
    f.katalog_nr = k.katalog_nr;
    f.typ = k.typ;
    if (k.serie) f.serie = k.serie;
    if (k.min_euro != null) f.min_euro = k.min_euro;
    if (k.max_euro != null) f.max_euro = k.max_euro;
    if (k.quelle) f.quelle = k.quelle;
    katalogKandidaten = [];
    pruefeDublette();
  }

  async function speichern() {
    if (!f.hersteller.trim() || !f.typ.trim()) {
      fehler = 'Hersteller und Typ sind Pflicht.';
      return;
    }
    laeuft = true; fehler = null;
    try {
      const neu = await erstelleModellVoll({
        hersteller: f.hersteller.trim(),
        katalog_nr: f.katalog_nr.trim() || null,
        typ: f.typ.trim(),
        serie: f.serie.trim() || null,
        min_euro: num(f.min_euro),
        max_euro: num(f.max_euro),
        quelle: f.quelle.trim() || null,
        farbe: f.farbe.trim() || null,
        zustand: f.zustand || null,
        bemerkung: f.bemerkung.trim() || null,
        bezahlt: num(f.bezahlt),
        schaetzwert: num(f.schaetzwert),
        kaufdatum: f.kaufdatum.trim() || null,
        anzahl: Number(f.anzahl) || 1
      });
      goto('/modell/' + neu.id);
    } catch (e) {
      fehler = e.message;
    } finally {
      laeuft = false;
    }
  }
</script>

<svelte:head><title>Modell anlegen — ModellGarage</title></svelte:head>

<div class="container" style="max-width:820px">
  <div style="padding-top:28px"><a href="/" class="back-link">← Zurück zur Galerie</a></div>
  <h1 style="font-size:2.4rem; margin:20px 0 6px">Modell anlegen</h1>
  <p style="color:var(--ink-soft); line-height:1.55; margin-bottom:28px">
    Für Käufe, die nicht in der Excel stehen — z.B. per Copy-&-Paste aus eBay.
    Neuer Hersteller oder neue Katalog-Nummer werden automatisch angelegt und
    passen nahtlos zu den importierten Excel-Daten.
  </p>

  <!-- eBay-Schnellerfassung -->
  <div class="ebay-box">
    <div class="ebay-head">
      <span class="ebay-badge">eBay-Schnellerfassung</span>
      <span style="color:var(--ink-soft); font-size:.82rem">Titel aus dem eBay-Angebot kopieren & einfügen</span>
      <button class="info-btn" onclick={() => ebayInfo = !ebayInfo} title="Wie funktioniert das?" aria-label="Hilfe">i</button>
    </div>

    {#if ebayInfo}
      <div class="info-panel">
        <strong>So funktioniert die eBay-Schnellerfassung:</strong>
        <ol>
          <li>eBay-Angebot im Browser öffnen.</li>
          <li>Den <b>Titel</b> markieren und kopieren (Strg+C), oben einfügen.</li>
          <li>Optional: Preis & Zustand (z.B. „EUR 39,00 gebraucht") ins zweite Feld.</li>
          <li>Optional: die <b>Artikelbeschreibung</b> ins dritte Feld — daraus
              werden <b>Katalog-Nr.</b> und <b>Farbe</b> gezogen (stehen selten im Titel).</li>
          <li>„Werte übernehmen" klickt die Felder <b>Hersteller, Typ, Katalog-Nr.,
              Farbe, Preis, Zustand, Maßstab</b> automatisch voll.</li>
          <li>Prüfen, ggf. korrigieren — vor allem die <b>Katalog-Nr.</b>
              gegen den Katalog abgleichen.</li>
        </ol>
        <div class="info-warn">
          Warum kein Link? eBay blockt automatisches Laden von Angebots-Links
          (Bot-Schutz). Das Einfügen des Titels aus deinem Browser umgeht das
          zuverlässig — und funktioniert auch bei bereits beendeten Auktionen.
        </div>
      </div>
    {/if}
    <input
      bind:value={ebayTitel}
      placeholder='z.B. "Wiking VW T2 Bus Sondermodell 1:87 OVP"'
    />
    <input
      bind:value={ebayExtra}
      placeholder="optional: Preis / Zustand mitkopieren, z.B. EUR 39,00 gebraucht"
      style="margin-top:8px"
    />
    <textarea
      bind:value={ebayBeschreibung}
      rows="5"
      oninput={autoGrow}
      placeholder="optional: Artikelbeschreibung einfügen — hier stehen oft Katalog-Nr. (z.B. Wiking Nr. 30/6K.) und Farbe"
      style="margin-top:8px; resize:both; min-height:130px; max-width:100%; overflow:auto"
    ></textarea>
    <div style="display:flex; gap:10px; align-items:center; margin-top:10px">
      <button class="btn" onclick={ebayUebernehmen} disabled={ebayLaeuft || !ebayTitel.trim()}>
        {ebayLaeuft ? 'Werte aus …' : 'Werte übernehmen ↓'}
      </button>
      <span style="color:var(--ink-soft); font-size:.78rem">
        Hinweis: eBay blockt automatisches Laden per Link — daher Titel einfügen.
      </span>
    </div>
    {#if ebayHinweis}
      <div class="ebay-hint">{ebayHinweis}</div>
    {/if}
  </div>

  <datalist id="hersteller-liste">
    {#each hersteller as h}<option value={h}></option>{/each}
  </datalist>

  <div class="form">
    <div class="sec">Identität</div>
    <div class="row">
      <label>Hersteller *
        <input list="hersteller-liste" bind:value={f.hersteller} oninput={pruefeDublette} placeholder="Wiking, Siku, Majorette …" />
      </label>
      <label>Katalog-Nr.
        <input bind:value={f.katalog_nr} oninput={pruefeDublette} placeholder="z.B. 30/6K. oder 1050" />
      </label>
    </div>
    {#if dublettenWarnung}
      <div class="dub-warn">⚠ {dublettenWarnung} <span style="color:var(--ink-soft)">— Dublette ist erlaubt, nur zur Info.</span></div>
    {/if}
    {#if katalogKandidaten.length}
      <div class="kat-box">
        <div class="kat-head">Katalog-Kandidaten — anklicken übernimmt Typ, Serie und Werte:</div>
        {#each katalogKandidaten as k}
          <button type="button" class="kat-row" onclick={() => uebernehmeKandidat(k)}>
            <span class="kat-nr">{k.hersteller} {k.katalog_nr}</span>
            <span class="kat-typ">{k.typ}{#if k.serie} · {k.serie}{/if}</span>
            <span class="kat-wert">
              {#if k.min_euro != null || k.max_euro != null}{k.min_euro ?? '?'}–{k.max_euro ?? '?'} €{/if}
            </span>
          </button>
        {/each}
      </div>
    {/if}
    <div class="row">
      <label>Typ / Bezeichnung *
        <input bind:value={f.typ} oninput={sucheKatalog} placeholder="VW Käfer, ovale Heckscheibe" />
      </label>
      <label>Serie
        <input bind:value={f.serie} placeholder="z.B. UV500, W300" />
      </label>
    </div>

    <div class="sec">Werte (Katalog)</div>
    <div class="row">
      <label>Min € (Katalog)<input type="number" step="0.01" bind:value={f.min_euro} /></label>
      <label>Max € (Katalog)<input type="number" step="0.01" bind:value={f.max_euro} /></label>
      <label>Quelle<input bind:value={f.quelle} placeholder="GK / Rawe" /></label>
    </div>

    <div class="sec">Dieses Exemplar</div>
    <div class="row">
      <label>Farbe<input bind:value={f.farbe} placeholder="dunkelrot" /></label>
      <label>Zustand
        <select bind:value={f.zustand}>
          <option value="">—</option>
          <option value="z0">z0 — neuwertig</option>
          <option value="z1">z1 — sehr gut</option>
          <option value="z2">z2 — bespielt</option>
        </select>
      </label>
    </div>
    <div class="row">
      <label>Einkaufspreis € (bezahlt)<input type="number" step="0.01" bind:value={f.bezahlt} /></label>
      <label>Schätzwert €<input type="number" step="0.01" bind:value={f.schaetzwert} /></label>
    </div>
    <div class="row">
      <label>Kaufdatum<input type="date" bind:value={f.kaufdatum} /></label>
      <label>Anzahl<input type="number" min="1" bind:value={f.anzahl} /></label>
    </div>
    <label>Bemerkung
      <textarea rows="2" bind:value={f.bemerkung} placeholder="z1-z2, aus Konvolut, doppelt …"></textarea>
    </label>

    {#if fehler}<div class="err">⚠ {fehler}</div>{/if}

    <div style="display:flex; gap:12px; margin-top:8px">
      <button class="btn" onclick={speichern} disabled={laeuft}>{laeuft ? 'Speichere …' : 'Modell anlegen'}</button>
      <a href="/" class="btn ghost" style="text-decoration:none">Abbrechen</a>
    </div>
  </div>
</div>

<style>
  .form { display: flex; flex-direction: column; gap: 16px; }
  .sec { font-family: var(--serif); font-size: 1.15rem; color: var(--accent); margin-top: 10px; border-bottom: 1px solid var(--line); padding-bottom: 6px; }
  .kat-box { background: var(--bg); border: 1px solid var(--line); border-radius: 10px; padding: 12px 14px; display: flex; flex-direction: column; gap: 6px; }
  .kat-head { font-size: .8rem; color: var(--ink-soft); margin-bottom: 2px; }
  .kat-row { display: grid; grid-template-columns: minmax(90px,auto) 1fr auto; align-items: center; gap: 12px; text-align: left; background: var(--bg-card); border: 1px solid var(--line); border-radius: 8px; padding: 8px 12px; cursor: pointer; font-size: .9rem; color: var(--ink); transition: border-color .12s; }
  .kat-row:hover { border-color: var(--accent); }
  .kat-nr { font-variant-numeric: tabular-nums; color: var(--accent); }
  .kat-typ { color: var(--ink); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .kat-wert { color: var(--ink-soft); font-variant-numeric: tabular-nums; }
  .row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .row:has(label:nth-child(3)) { grid-template-columns: 1fr 1fr 1fr; }
  label { display: flex; flex-direction: column; gap: 6px; font-size: .82rem; color: var(--ink-soft); }
  input, select, textarea {
    border: 1px solid var(--line); background: var(--bg-card); padding: 10px 12px;
    border-radius: 9px; color: var(--ink); font-size: 1rem; outline: none;
  }
  input:focus, select:focus, textarea:focus { border-color: var(--accent); }
  .err { color: #a35a45; background: #f7ece9; border: 1px solid #e6c8c0; padding: 12px 16px; border-radius: 10px; }
  .dub-warn { background: #fdf6e3; border: 1px solid #e8d9a0; color: #8a6d1b; padding: 11px 15px; border-radius: 10px; font-size: .9rem; }
  .ebay-box {
    background: var(--bg-card); border: 1px solid var(--line);
    border-radius: var(--radius); padding: 20px 22px; margin-bottom: 30px;
    box-shadow: var(--shadow);
  }
  .ebay-head { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
  .info-btn {
    margin-left: auto; width: 24px; height: 24px; border-radius: 50%;
    border: 1px solid var(--accent); background: transparent; color: var(--accent);
    font-family: var(--serif); font-style: italic; font-size: .95rem; cursor: pointer;
    line-height: 1; display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; transition: background .15s;
  }
  .info-btn:hover { background: var(--accent); color: #fff; }
  .info-panel {
    background: var(--bg); border: 1px solid var(--line); border-radius: 10px;
    padding: 16px 18px; margin-bottom: 14px; font-size: .88rem; line-height: 1.55;
  }
  .info-panel ol { margin: 10px 0 0; padding-left: 20px; }
  .info-panel li { margin-bottom: 5px; }
  .info-warn {
    margin-top: 12px; padding: 10px 12px; background: rgba(138,109,59,.08);
    border-radius: 8px; color: var(--accent-dark); font-size: .84rem;
  }
  .ebay-badge {
    font-size: .66rem; letter-spacing: .12em; text-transform: uppercase;
    background: var(--accent); color: #fff; padding: 4px 10px; border-radius: 20px;
  }
  .ebay-box input {
    width: 100%; border: 1px solid var(--line); background: var(--bg);
    padding: 10px 12px; border-radius: 9px; color: var(--ink); font-size: 1rem; outline: none;
  }
  .ebay-box input:focus { border-color: var(--accent); }
  .ebay-hint {
    margin-top: 12px; font-size: .85rem; color: var(--accent-dark);
    background: rgba(138,109,59,.08); padding: 10px 14px; border-radius: 9px; line-height: 1.5;
  }
  @media (max-width: 640px) { .row, .row:has(label:nth-child(3)) { grid-template-columns: 1fr; } }
</style>
