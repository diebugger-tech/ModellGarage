<script>
  import { onMount } from 'svelte';
  import { getWunschliste, getHersteller } from '$lib/api.js';

  let hersteller = $state([]);
  let auswahl = $state('Wiking');
  let daten = $state(null);
  let laedt = $state(false);
  let fehler = $state(null);

  onMount(async () => {
    hersteller = await getHersteller();
    await lade();
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
</script>

<svelte:head><title>Lücken — ModellGarage</title></svelte:head>

<div class="container" style="max-width:900px">
  <div style="padding-top:28px"><a href="/" class="back-link">← Zurück zur Galerie</a></div>
  <h1 style="font-size:2.6rem; margin:18px 0 8px">Fehlende Nummern</h1>
  <p style="color:var(--ink-soft); line-height:1.55; margin-bottom:26px">
    Grobe Orientierung, welche Basis-Nummern (vor dem „/“) in deiner Sammlung noch
    fehlen. Nicht jede Nummer existiert im Katalog — aber so siehst du Lücken auf
    einen Blick.
  </p>

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
                  <span class="luecke">{nr}</span>
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
    display: inline-flex; align-items: center; justify-content: center;
    min-width: 50px; padding: 7px 10px; border-radius: 8px;
    background: var(--bg); border: 1px solid var(--line);
    font-variant-numeric: tabular-nums; font-size: .9rem;
  }
  .empty-inner { color: var(--ink-soft); font-size: .9rem; }
  .err { color: #a35a45; background: #f7ece9; border: 1px solid #e6c8c0; padding: 12px 16px; border-radius: 10px; margin-bottom: 20px; }
  select { border: 1px solid var(--line); background: var(--bg-card); padding: 11px 15px; border-radius: 10px; color: var(--ink); outline: none; }
  select:focus { border-color: var(--accent); }
</style>
