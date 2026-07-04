<script>
  import { onMount } from 'svelte';
  import {
    getWunschliste, getHersteller,
    getWunsch, createWunsch, updateWunsch, deleteWunsch, euro
  } from '$lib/api.js';

  let hersteller = $state([]);
  let auswahl = $state('Wiking');
  let daten = $state(null);
  let laedt = $state(false);
  let fehler = $state(null);

  // Manuelle Wunschliste
  let wuensche = $state([]);
  let wLaedt = $state(false);
  let wFehler = $state(null);
  let hinweis = $state(null);
  let form = $state({ hersteller: 'Wiking', katalog_nr: '', typ: '', notiz: '', max_euro: '' });

  onMount(async () => {
    hersteller = await getHersteller();
    await Promise.all([lade(), ladeWuensche()]);
  });

  async function lade() {
    laedt = true; fehler = null;
    try {
      daten = await getWunschliste(auswahl);
    } catch (e) {
      fehler = e.message;
    } finally {
      laedt = false;
    }
  }

  async function ladeWuensche() {
    wLaedt = true; wFehler = null;
    try {
      wuensche = await getWunsch();
    } catch (e) {
      wFehler = e.message;
    } finally {
      wLaedt = false;
    }
  }

  function schonGemerkt(h, nr) {
    return wuensche.some(w => w.status === 'gesucht' && w.hersteller === h && w.katalog_nr === String(nr));
  }

  async function merken(h, nr) {
    hinweis = null;
    if (schonGemerkt(h, nr)) { hinweis = `${h} ${nr} steht schon auf der Wunschliste.`; return; }
    try {
      await createWunsch({ hersteller: h, katalog_nr: String(nr) });
      await ladeWuensche();
      hinweis = `${h} ${nr} zur Wunschliste hinzugefügt.`;
    } catch (e) {
      hinweis = '⚠ ' + e.message;
    }
  }

  async function anlegen() {
    if (!form.hersteller.trim()) { wFehler = 'Hersteller ist Pflicht.'; return; }
    wFehler = null;
    try {
      await createWunsch({
        hersteller: form.hersteller.trim(),
        katalog_nr: form.katalog_nr.trim() || null,
        typ: form.typ.trim() || null,
        notiz: form.notiz.trim() || null,
        max_euro: form.max_euro === '' ? null : Number(form.max_euro)
      });
      form.katalog_nr = ''; form.typ = ''; form.notiz = ''; form.max_euro = '';
      await ladeWuensche();
      hinweis = 'Wunsch hinzugefügt.';
    } catch (e) {
      wFehler = e.message;
    }
  }

  async function toggle(w) {
    const neu = w.status === 'gesucht' ? 'gekauft' : 'gesucht';
    try { await updateWunsch(w.id, { status: neu }); await ladeWuensche(); }
    catch (e) { wFehler = e.message; }
  }

  async function entfernen(w) {
    try { await deleteWunsch(w.id); await ladeWuensche(); }
    catch (e) { wFehler = e.message; }
  }
</script>

<svelte:head><title>Lücken & Wunschliste — ModellGarage</title></svelte:head>

<div class="container" style="max-width:900px">
  <div style="padding-top:28px"><a href="/" class="back-link">← Zurück zur Galerie</a></div>
  <h1 style="font-size:2.6rem; margin:18px 0 8px">Fehlende Nummern</h1>
  <p style="color:var(--ink-soft); line-height:1.55; margin-bottom:26px">
    Grobe Orientierung, welche Basis-Nummern (vor dem „/“) in deiner Sammlung noch
    fehlen. Nicht jede Nummer existiert im Katalog — aber so siehst du Lücken auf
    einen Blick. Klick auf eine Nummer, um sie zur Wunschliste hinzuzufügen.
  </p>

  {#if hinweis}<div class="hint">{hinweis}</div>{/if}

  <div class="toolbar" style="margin-bottom:28px">
    <select bind:value={auswahl} onchange={lade}>
      {#each hersteller as h}
        <option value={h}>{h}</option>
      {/each}
    </select>
    <button class="btn" onclick={lade} disabled={laedt}>{laedt ? 'Lade …' : 'Aktualisieren'}</button>
  </div>

  {#if fehler}
    <div class="err">⚠ {fehler}</div>
  {/if}

  {#if daten}
    <div class="card">
      {#each Object.entries(daten.gesamt) as [herstellerName, hdaten]}
        {#if hdaten.vorhandene_basen > 0}
          <div class="marke">
            <div class="marke-head">
              <span class="marke-name">{herstellerName}</span>
              <span class="marke-meta">
                {hdaten.vorhandene_basen} Basen von {hdaten.bereich.von} bis {hdaten.bereich.bis}
              </span>
            </div>
            {#if hdaten.luecken.length}
              <div class="luecken">
                {#each hdaten.luecken as nr}
                  <button
                    class="luecke"
                    class:gemerkt={schonGemerkt(herstellerName, nr)}
                    title={schonGemerkt(herstellerName, nr) ? 'Bereits auf der Wunschliste' : 'Zur Wunschliste merken'}
                    onclick={() => merken(herstellerName, nr)}
                  >{nr}<span class="plus">+</span></button>
                {/each}
              </div>
            {:else}
              <div class="empty-inner">Keine Lücken gefunden — alle Basisnummern im Bereich vorhanden.</div>
            {/if}
          </div>
        {/if}
      {/each}
    </div>
  {/if}

  <!-- Manuelle Wunschliste -->
  <h2 class="section-title">Meine Wunschliste</h2>
  <p style="color:var(--ink-soft); line-height:1.55; margin-bottom:20px">
    Trag ein, was du noch suchst — später auf „gekauft“ setzen oder löschen.
  </p>

  <div class="card wunsch-form">
    <div class="w-row">
      <label>Hersteller *
        <input list="w-hersteller" bind:value={form.hersteller} placeholder="Wiking, Siku …" />
      </label>
      <label>Katalog-Nr.
        <input bind:value={form.katalog_nr} placeholder="z.B. 30/6K." />
      </label>
      <label>Max € (optional)
        <input type="number" step="0.01" bind:value={form.max_euro} placeholder="z.B. 40" />
      </label>
    </div>
    <div class="w-row">
      <label>Typ / Bezeichnung
        <input bind:value={form.typ} placeholder="VW Käfer …" />
      </label>
      <label>Notiz
        <input bind:value={form.notiz} placeholder="z.B. nur in blaugrau, Z1" />
      </label>
    </div>
    <datalist id="w-hersteller">{#each hersteller as h}<option value={h}></option>{/each}</datalist>
    <div>
      <button class="btn" onclick={anlegen}>Zur Wunschliste hinzufügen</button>
    </div>
    {#if wFehler}<div class="err" style="margin-top:12px">⚠ {wFehler}</div>{/if}
  </div>

  {#if wLaedt}
    <div class="empty-inner" style="margin-top:16px">Lade Wunschliste …</div>
  {:else if wuensche.length}
    <div class="card" style="margin-top:20px">
      {#each wuensche as w}
        <div class="wunsch-row" class:gekauft={w.status === 'gekauft'}>
          <span class="w-status">{w.status === 'gekauft' ? '✓' : '○'}</span>
          <div class="w-main">
            <span class="w-titel">
              <strong>{w.hersteller}</strong>{#if w.katalog_nr} · {w.katalog_nr}{/if}
              {#if w.typ} — {w.typ}{/if}
            </span>
            {#if w.notiz || w.max_euro != null}
              <span class="w-sub">
                {#if w.max_euro != null}max. {euro(w.max_euro)}{/if}{#if w.max_euro != null && w.notiz} · {/if}{#if w.notiz}{w.notiz}{/if}
              </span>
            {/if}
          </div>
          <button class="w-act" onclick={() => toggle(w)}>
            {w.status === 'gekauft' ? 'wieder suchen' : 'gekauft'}
          </button>
          <button class="w-act del" onclick={() => entfernen(w)} title="Löschen">✕</button>
        </div>
      {/each}
    </div>
  {:else if !wLaedt}
    <div class="empty-inner" style="margin-top:16px">Noch keine Wünsche — oben eintragen oder oben eine Lücke anklicken.</div>
  {/if}
</div>

<style>
  .card { background: var(--bg-card); border: 1px solid var(--line); border-radius: var(--radius); padding: 24px 28px; box-shadow: var(--shadow); }
  .marke { margin-bottom: 28px; }
  .marke:last-child { margin-bottom: 0; }
  .marke-head { display: flex; align-items: baseline; gap: 14px; margin-bottom: 14px; flex-wrap: wrap; }
  .marke-name { font-family: var(--serif); font-size: 1.5rem; color: var(--accent); }
  .marke-meta { color: var(--ink-soft); font-size: .85rem; }
  .luecken { display: flex; flex-wrap: wrap; gap: 8px; }
  .luecke {
    display: inline-flex; align-items: center; gap: 4px;
    min-width: 50px; padding: 7px 10px; border-radius: 8px;
    background: var(--bg); border: 1px solid var(--line); cursor: pointer;
    font-variant-numeric: tabular-nums; font-size: .9rem; color: var(--ink);
    transition: border-color .12s, background .12s;
  }
  .luecke:hover { border-color: var(--accent); background: var(--bg-card); }
  .luecke .plus { color: var(--accent); font-weight: 600; opacity: 0; transition: opacity .12s; }
  .luecke:hover .plus { opacity: 1; }
  .luecke.gemerkt { border-color: var(--accent); color: var(--accent); }
  .luecke.gemerkt .plus { opacity: 1; content: '✓'; }
  .empty-inner { color: var(--ink-soft); font-size: .9rem; }
  .err { color: #a35a45; background: #f7ece9; border: 1px solid #e6c8c0; padding: 12px 16px; border-radius: 10px; margin-bottom: 20px; }
  .hint { color: #4a7c59; background: #eef5ef; border: 1px solid #cfe3d4; padding: 11px 15px; border-radius: 10px; margin-bottom: 18px; font-size: .9rem; }
  select { border: 1px solid var(--line); background: var(--bg-card); padding: 11px 15px; border-radius: 10px; color: var(--ink); outline: none; }
  select:focus { border-color: var(--accent); }

  .section-title { font-family: var(--serif); font-size: 2rem; color: var(--accent); margin: 44px 0 6px; border-top: 1px solid var(--line); padding-top: 30px; }
  .wunsch-form { display: flex; flex-direction: column; gap: 16px; }
  .w-row { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
  .w-row:has(label:nth-child(2):last-child) { grid-template-columns: 1fr 1fr; }
  .wunsch-form label { display: flex; flex-direction: column; gap: 6px; font-size: .82rem; color: var(--ink-soft); }
  .wunsch-form input { border: 1px solid var(--line); background: var(--bg); padding: 10px 12px; border-radius: 9px; color: var(--ink); font-size: 1rem; outline: none; }
  .wunsch-form input:focus { border-color: var(--accent); }

  .wunsch-row { display: grid; grid-template-columns: 24px 1fr auto auto; align-items: center; gap: 12px; padding: 12px 6px; border-bottom: 1px solid var(--line); }
  .wunsch-row:last-child { border-bottom: none; }
  .wunsch-row.gekauft { opacity: .55; }
  .w-status { color: var(--accent); font-size: 1.1rem; text-align: center; }
  .w-main { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
  .w-titel { color: var(--ink); }
  .w-sub { color: var(--ink-soft); font-size: .82rem; }
  .w-act { border: 1px solid var(--line); background: var(--bg-card); color: var(--ink-soft); padding: 6px 12px; border-radius: 8px; cursor: pointer; font-size: .82rem; transition: border-color .12s, color .12s; }
  .w-act:hover { border-color: var(--accent); color: var(--accent); }
  .w-act.del { color: #a35a45; }
  @media (max-width: 640px) {
    .w-row, .w-row:has(label:nth-child(2):last-child) { grid-template-columns: 1fr; }
  }
</style>
