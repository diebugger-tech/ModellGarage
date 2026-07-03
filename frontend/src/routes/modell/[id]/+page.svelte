<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { getModell, euro } from '$lib/api.js';

  let modell = $state(null);
  let fehler = $state(false);

  onMount(async () => {
    try {
      modell = await getModell($page.params.id);
    } catch {
      fehler = true;
    }
  });

  const initial = (typ) => (typ || '?').trim().charAt(0).toUpperCase();
  const zLabel = { z0: 'z0 — neuwertig', z1: 'z1 — sehr gut', z2: 'z2 — bespielt' };
</script>

<svelte:head><title>{modell?.katalog?.typ || 'Modell'} — ModellGarage</title></svelte:head>

<div class="container">
  <div style="padding-top:28px"><a href="/" class="back-link">← Zurück zur Galerie</a></div>

  {#if fehler}
    <div class="empty">Modell nicht gefunden.</div>
  {:else if !modell}
    <div class="loading">Lade …</div>
  {:else}
    <div class="detail-wrap detail">
      <div class="detail-photo">
        <span class="placeholder">{initial(modell.katalog?.typ)}</span>
      </div>
      <div>
        <div class="hersteller" style="color:var(--accent); letter-spacing:.2em; text-transform:uppercase; font-size:.7rem">
          {modell.katalog?.hersteller || '—'}
        </div>
        <h1 style="font-size:2.6rem; margin:8px 0 4px">{modell.katalog?.typ || 'Unbekannt'}</h1>
        {#if modell.katalog?.katalog_nr}
          <div style="color:var(--ink-soft); font-size:1rem">Katalog-Nr. {modell.katalog.katalog_nr}
            {#if modell.katalog.serie} · Serie {modell.katalog.serie}{/if}</div>
        {/if}

        <dl>
          {#if modell.farbe}<dt>Farbe</dt><dd>{modell.farbe}</dd>{/if}
          {#if modell.zustand}<dt>Zustand</dt><dd><span class="zustand {modell.zustand}">{zLabel[modell.zustand] || modell.zustand}</span></dd>{/if}
          <dt>Bezahlt</dt><dd>{euro(modell.bezahlt)}</dd>
          <dt>Schätzwert</dt><dd>{euro(modell.schaetzwert)}</dd>
          <dt>Katalogwert</dt><dd>{euro(modell.katalog?.min_euro)} – {euro(modell.katalog?.max_euro)}</dd>
          {#if modell.kaufdatum}<dt>Kaufdatum</dt><dd>{modell.kaufdatum}</dd>{/if}
          <dt>Anzahl</dt><dd>{modell.anzahl}×</dd>
        </dl>

        {#if modell.bemerkung}
          <div style="border-top:1px solid var(--line); padding-top:18px; margin-top:6px">
            <div style="color:var(--ink-soft); font-size:.72rem; letter-spacing:.14em; text-transform:uppercase; margin-bottom:8px">Bemerkung</div>
            <p style="line-height:1.55; margin:0">{modell.bemerkung}</p>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>
