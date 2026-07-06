<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { getStatistik, getModelle, getHersteller, getJahre, euro } from '$lib/api.js';

  let stats = $state(null);
  let hersteller = $state([]);
  let jahre = $state([]);
  let modelle = $state([]);
  let total = $state(0);
  let loading = $state(true);

  // Filter-State
  let q = $state('');
  let fHersteller = $state('');
  let fZustand = $state('');
  let fJahr = $state('');
  let fQualitaet = $state('');
  let sort = $state('id');
  let order = $state('asc');
  let offset = $state(0);
  const limit = 24;

  let suchTimer;

  async function ladeListe() {
    loading = true;
    const data = await getModelle({ q, hersteller: fHersteller, zustand: fZustand, jahr: fJahr, qualitaet: fQualitaet, limit, offset, sort, order });
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

  let gesamtSeiten = $derived(Math.max(1, Math.ceil(total / limit)));
  let aktuelleSeite = $derived(Math.floor(offset / limit) + 1);
  let springZu = $state('');
  function geheZuSeite(n) {
    const p = Math.min(Math.max(1, Math.floor(n) || 1), gesamtSeiten);
    offset = (p - 1) * limit;
    springZu = '';
    ladeListe();
  }

  onMount(async () => {
    [stats, hersteller, jahre] = await Promise.all([getStatistik(), getHersteller(), getJahre()]);
    await ladeListe();
  });

  const initial = (typ) => (typ || '?').trim().charAt(0).toUpperCase();
  const kaufjahr = (m) => {
    const j = (m.kaufdatum || '').slice(0, 4);
    return /^\d{4}$/.test(j) ? j : '';
  };
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
    <select bind:value={fJahr} onchange={filterAendern}>
      <option value="">Alle Kaufjahre</option>
      {#each jahre as jahr}<option value={jahr}>{jahr}</option>{/each}
    </select>
    <select bind:value={fQualitaet} onchange={filterAendern}>
      <option value="">Datenqualität: alle</option>
      <option value="ohne_foto">ohne Foto</option>
      <option value="ohne_zustand">ohne Zustand</option>
      <option value="ohne_kaufdatum">ohne Kaufdatum</option>
    </select>
    <select bind:value={sort} onchange={filterAendern}>
      <option value="id">Sortierung: Standard</option>
      <option value="bezahlt">Preis</option>
      <option value="schaetzwert">Schätzwert</option>
      <option value="kaufdatum">Kaufjahr</option>
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
            {#if m.foto_url}
              <img src={m.foto_url} alt={m.katalog?.typ || 'Foto'} loading="lazy" />
            {:else}
              <span class="placeholder">{initial(m.katalog?.typ)}</span>
            {/if}
            {#if m.katalog?.katalog_nr}<span class="badge">{m.katalog.katalog_nr}</span>{/if}
          </div>
          <div class="body">
            <div class="hersteller">{m.katalog?.hersteller || '—'}</div>
            <div class="typ">{m.katalog?.typ || 'Unbekannt'}</div>
            {#if m.farbe}<div class="nr">{m.farbe}</div>{/if}
            <div class="foot">
              <span class="preis">{euro(m.bezahlt ?? m.schaetzwert)}</span>
              {#if kaufjahr(m)}<span class="jahr" style="color:var(--ink-soft); font-size:.8rem; font-variant-numeric:tabular-nums">{kaufjahr(m)}</span>{/if}
              {#if m.zustand}<span class="zustand {m.zustand}">{m.zustand}</span>{/if}
            </div>
          </div>
        </div>
      {/each}
    </div>

    <div class="pager">
      <button onclick={() => geheZuSeite(1)} disabled={aktuelleSeite === 1} title="Erste Seite">⏮</button>
      <button onclick={() => seite(-1)} disabled={offset === 0}>← Zurück</button>
      <span class="pager-info">
        {offset + 1}–{Math.min(offset + limit, total)} von {total.toLocaleString('de-DE')}
        <span class="pager-seite">
          · Seite
          <input
            type="number" min="1" max={gesamtSeiten}
            placeholder={aktuelleSeite}
            bind:value={springZu}
            onkeydown={(e) => e.key === 'Enter' && springZu && geheZuSeite(Number(springZu))}
            style="width:4.5em; padding:4px 8px; border:1px solid var(--line); border-radius:8px; background:var(--bg-card); color:var(--ink); text-align:center; font-variant-numeric:tabular-nums"
          />
          / {gesamtSeiten.toLocaleString('de-DE')}
        </span>
      </span>
      <button onclick={() => seite(1)} disabled={offset + limit >= total}>Weiter →</button>
      <button onclick={() => geheZuSeite(gesamtSeiten)} disabled={aktuelleSeite >= gesamtSeiten} title="Letzte Seite">⏭</button>
    </div>
  {/if}
</div>
