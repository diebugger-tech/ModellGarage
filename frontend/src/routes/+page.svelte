<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { getStatistik, getModelle, getHersteller, euro } from '$lib/api.js';

  let stats = $state(null);
  let hersteller = $state([]);
  let modelle = $state([]);
  let total = $state(0);
  let loading = $state(true);

  // Filter-State
  let q = $state('');
  let fHersteller = $state('');
  let fZustand = $state('');
  let sort = $state('id');
  let order = $state('asc');
  let offset = $state(0);
  const limit = 24;

  let suchTimer;

  async function ladeListe() {
    loading = true;
    const data = await getModelle({ q, hersteller: fHersteller, zustand: fZustand, limit, offset, sort, order });
    modelle = data.items;
    total = data.total;
    loading = false;
  }

  function onSuche() {
    clearTimeout(suchTimer);
    suchTimer = setTimeout(() => { offset = 0; ladeListe(); }, 250);
  }

  function filterAendern() { offset = 0; ladeListe(); }
  function seite(delta) { offset = Math.max(0, offset + delta * limit); ladeListe(); }

  onMount(async () => {
    [stats, hersteller] = await Promise.all([getStatistik(), getHersteller()]);
    await ladeListe();
  });

  const initial = (typ) => (typ || '?').trim().charAt(0).toUpperCase();
</script>

<svelte:head><title>ModellGarage — Die Sammlung</title></svelte:head>

<div class="container">
  {#if stats}
    <div class="stats-band">
      <div class="stat"><div class="num">{stats.anzahl_modelle.toLocaleString('de-DE')}</div><div class="lbl">Modelle</div></div>
      <div class="stat"><div class="num">{stats.anzahl_katalog.toLocaleString('de-DE')}</div><div class="lbl">Katalog-Einträge</div></div>
      <div class="stat"><div class="num">{euro(stats.summe_bezahlt)}</div><div class="lbl">Investiert</div></div>
      <div class="stat"><div class="num">{euro(stats.summe_min)}–{euro(stats.summe_max)}</div><div class="lbl">Katalogwert</div></div>
      <div class="stat"><div class="num">{Object.keys(stats.hersteller).length}</div><div class="lbl">Hersteller</div></div>
    </div>
  {/if}

  <div class="toolbar">
    <input type="search" placeholder="Suchen — Typ, Nummer, Farbe …" bind:value={q} oninput={onSuche} />
    <select bind:value={fHersteller} onchange={filterAendern}>
      <option value="">Alle Hersteller</option>
      {#each hersteller as h}<option value={h}>{h}</option>{/each}
    </select>
    <select bind:value={fZustand} onchange={filterAendern}>
      <option value="">Jeder Zustand</option>
      <option value="z0">z0 — neuwertig</option>
      <option value="z1">z1 — sehr gut</option>
      <option value="z2">z2 — bespielt</option>
    </select>
    <select bind:value={sort} onchange={filterAendern}>
      <option value="id">Sortierung: Standard</option>
      <option value="bezahlt">Preis</option>
      <option value="schaetzwert">Schätzwert</option>
      <option value="kaufdatum">Kaufdatum</option>
    </select>
    <button class="btn ghost" onclick={() => { order = order === 'asc' ? 'desc' : 'asc'; filterAendern(); }}>
      {order === 'asc' ? '↑' : '↓'}
    </button>
  </div>

  {#if loading}
    <div class="loading">Lade Sammlung …</div>
  {:else if modelle.length === 0}
    <div class="empty">Keine Modelle gefunden.</div>
  {:else}
    <div class="grid">
      {#each modelle as m (m.id)}
        <div class="card" onclick={() => goto('/modell/' + m.id)} role="button" tabindex="0"
             onkeydown={(e) => e.key === 'Enter' && goto('/modell/' + m.id)}>
          <div class="thumb">
            <span class="placeholder">{initial(m.katalog?.typ)}</span>
            {#if m.katalog?.katalog_nr}<span class="badge">{m.katalog.katalog_nr}</span>{/if}
          </div>
          <div class="body">
            <div class="hersteller">{m.katalog?.hersteller || '—'}</div>
            <div class="typ">{m.katalog?.typ || 'Unbekannt'}</div>
            {#if m.farbe}<div class="nr">{m.farbe}</div>{/if}
            <div class="foot">
              <span class="preis">{euro(m.bezahlt ?? m.schaetzwert)}</span>
              {#if m.zustand}<span class="zustand {m.zustand}">{m.zustand}</span>{/if}
            </div>
          </div>
        </div>
      {/each}
    </div>

    <div class="pager">
      <button onclick={() => seite(-1)} disabled={offset === 0}>← Zurück</button>
      <span>{offset + 1}–{Math.min(offset + limit, total)} von {total.toLocaleString('de-DE')}</span>
      <button onclick={() => seite(1)} disabled={offset + limit >= total}>Weiter →</button>
    </div>
  {/if}
</div>
