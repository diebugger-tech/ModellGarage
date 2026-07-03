<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { getHersteller, erstelleModellVoll } from '$lib/api.js';

  let hersteller = $state([]);
  let laeuft = $state(false);
  let fehler = $state(null);

  // Felder = 1:1 die Excel-Spalten
  let f = $state({
    hersteller: '', katalog_nr: '', typ: '', serie: '',
    min_euro: '', max_euro: '', quelle: '',
    farbe: '', zustand: '', bemerkung: '',
    bezahlt: '', schaetzwert: '', kaufdatum: '', anzahl: 1
  });

  onMount(async () => { hersteller = await getHersteller(); });

  function num(v) { return v === '' || v == null ? null : Number(v); }

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

  <datalist id="hersteller-liste">
    {#each hersteller as h}<option value={h}></option>{/each}
  </datalist>

  <div class="form">
    <div class="sec">Identität</div>
    <div class="row">
      <label>Hersteller *
        <input list="hersteller-liste" bind:value={f.hersteller} placeholder="Wiking, Siku, Majorette …" />
      </label>
      <label>Katalog-Nr.
        <input bind:value={f.katalog_nr} placeholder="z.B. 30/6K. oder 1050" />
      </label>
    </div>
    <div class="row">
      <label>Typ / Bezeichnung *
        <input bind:value={f.typ} placeholder="VW Käfer, ovale Heckscheibe" />
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
  .row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .row:has(label:nth-child(3)) { grid-template-columns: 1fr 1fr 1fr; }
  label { display: flex; flex-direction: column; gap: 6px; font-size: .82rem; color: var(--ink-soft); }
  input, select, textarea {
    border: 1px solid var(--line); background: var(--bg-card); padding: 10px 12px;
    border-radius: 9px; color: var(--ink); font-size: 1rem; outline: none;
  }
  input:focus, select:focus, textarea:focus { border-color: var(--accent); }
  .err { color: #a35a45; background: #f7ece9; border: 1px solid #e6c8c0; padding: 12px 16px; border-radius: 10px; }
  @media (max-width: 640px) { .row, .row:has(label:nth-child(3)) { grid-template-columns: 1fr; } }
</style>
