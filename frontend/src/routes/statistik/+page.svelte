<script>
  import { onMount } from 'svelte';
  import { getDashboard, euro } from '$lib/api.js';

  let d = $state(null);
  let laedt = $state(true);
  let fehler = $state(null);

  onMount(async () => {
    try {
      d = await getDashboard();
    } catch (e) {
      fehler = e.message || 'Auswertung konnte nicht geladen werden.';
    } finally {
      laedt = false;
    }
  });

  // ---- SVG-Helfer ----
  const W = 640, H = 260, PAD = 40;

  function linienPfad(punkte, maxY) {
    if (!punkte.length) return '';
    const n = punkte.length;
    return punkte.map((p, i) => {
      const x = PAD + (i / Math.max(1, n - 1)) * (W - 2 * PAD);
      const y = H - PAD - (p / maxY) * (H - 2 * PAD);
      return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(' ');
  }

  // Donut-Segmente
  function donut(items) {
    const total = items.reduce((s, i) => s + i.anzahl, 0) || 1;
    let winkel = -90;
    const farben = ['#8a6d3b','#4a7c59','#a35a45','#6b7d8a','#b8925a','#7a5c8a','#c0a068','#5a8a7c','#a0785a','#8a8a6b','#d0c0a0'];
    return items.map((it, idx) => {
      const anteil = it.anzahl / total;
      const start = winkel;
      const end = winkel + anteil * 360;
      winkel = end;
      const r = 90, ri = 54, cx = 130, cy = 130;
      const a0 = (start * Math.PI) / 180, a1 = (end * Math.PI) / 180;
      const large = anteil > 0.5 ? 1 : 0;
      const x0 = cx + r * Math.cos(a0), y0 = cy + r * Math.sin(a0);
      const x1 = cx + r * Math.cos(a1), y1 = cy + r * Math.sin(a1);
      const xi0 = cx + ri * Math.cos(a1), yi0 = cy + ri * Math.sin(a1);
      const xi1 = cx + ri * Math.cos(a0), yi1 = cy + ri * Math.sin(a0);
      const path = `M${x0},${y0} A${r},${r} 0 ${large} 1 ${x1},${y1} L${xi0},${yi0} A${ri},${ri} 0 ${large} 0 ${xi1},${yi1} Z`;
      return { path, farbe: farben[idx % farben.length], name: it.name, anzahl: it.anzahl, prozent: (anteil*100).toFixed(1) };
    });
  }

  const zFarbe = { z0: '#4a7c59', z1: '#8a6d3b', z2: '#a35a45', unbekannt: '#c9c2b6' };
</script>

<svelte:head><title>Statistik — ModellGarage</title></svelte:head>

<div class="container">
  <div style="padding-top:28px"><a href="/" class="back-link">← Zurück zur Galerie</a></div>
  <h1 style="font-size:2.6rem; margin:18px 0 30px">Sammlung in Zahlen</h1>

  {#if laedt}
    <div class="loading">Lade Auswertung …</div>
  {:else if fehler}
    <div class="loading">⚠ {fehler}</div>
  {:else if d}
    <!-- Wertentwicklung (kumuliert) -->
    <section class="chart-card">
      <h2>Wertentwicklung <small>investierte Summe, kumuliert über die Jahre</small></h2>
      {#if d.wertentwicklung.length}
        {@const maxW = Math.max(...d.wertentwicklung.map(p => p.wert))}
        <svg viewBox="0 0 {W} {H}" class="chart">
          <!-- Fläche -->
          <path d="{linienPfad(d.wertentwicklung.map(p=>p.wert), maxW)} L{W-PAD},{H-PAD} L{PAD},{H-PAD} Z"
                fill="rgba(138,109,59,.10)" />
          <path d={linienPfad(d.wertentwicklung.map(p=>p.wert), maxW)}
                fill="none" stroke="var(--accent)" stroke-width="2.5" />
          {#each d.wertentwicklung as p, i}
            {@const x = PAD + (i/Math.max(1,d.wertentwicklung.length-1))*(W-2*PAD)}
            {@const y = H-PAD - (p.wert/maxW)*(H-2*PAD)}
            <circle cx={x} cy={y} r="3" fill="var(--accent)" />
            <text x={x} y={H-PAD+16} font-size="10" text-anchor="middle" fill="var(--ink-soft)">{p.jahr}</text>
          {/each}
          <text x={PAD} y="20" font-size="12" fill="var(--ink-soft)">{euro(maxW)}</text>
        </svg>
      {/if}
    </section>

    <div class="chart-grid">
      <!-- Zukäufe pro Jahr (Balken) -->
      <section class="chart-card">
        <h2>Zukäufe pro Jahr <small>Anzahl neuer Modelle</small></h2>
        {#if d.zukaeufe_pro_jahr.length}
          {@const maxA = Math.max(...d.zukaeufe_pro_jahr.map(e => e.anzahl))}
          <svg viewBox="0 0 {W} {H}" class="chart">
            {#each d.zukaeufe_pro_jahr as e, i}
              {@const bw = (W-2*PAD)/d.zukaeufe_pro_jahr.length * 0.7}
              {@const x = PAD + (i+0.15)*(W-2*PAD)/d.zukaeufe_pro_jahr.length}
              {@const bh = (e.anzahl/maxA)*(H-2*PAD)}
              <rect x={x} y={H-PAD-bh} width={bw} height={bh} rx="3" fill="var(--accent)" opacity="0.85" />
              <text x={x+bw/2} y={H-PAD+16} font-size="9" text-anchor="middle" fill="var(--ink-soft)">{e.jahr.slice(2)}</text>
              <text x={x+bw/2} y={H-PAD-bh-5} font-size="9" text-anchor="middle" fill="var(--ink)">{e.anzahl}</text>
            {/each}
          </svg>
        {/if}
      </section>

      <!-- Zustand-Split (horizontale Balken) -->
      <section class="chart-card">
        <h2>Zustand <small>Verteilung der Erhaltung</small></h2>
        {#if d.zustand_verteilung.length}
          {@const totZ = d.zustand_verteilung.reduce((s,z)=>s+z.anzahl,0)}
          <div class="hbars">
            {#each [...d.zustand_verteilung].sort((a,b)=>b.anzahl-a.anzahl) as z}
              <div class="hbar-row">
                <span class="hbar-lbl">{z.zustand}</span>
                <div class="hbar-track">
                  <div class="hbar-fill" style="width:{(z.anzahl/totZ*100).toFixed(1)}%; background:{zFarbe[z.zustand]||'#c9c2b6'}"></div>
                </div>
                <span class="hbar-val">{z.anzahl}</span>
              </div>
            {/each}
          </div>
        {/if}
      </section>
    </div>

    <div class="chart-grid">
      <!-- Hersteller-Donut -->
      <section class="chart-card">
        <h2>Hersteller <small>Top 10 nach Anzahl</small></h2>
        <div style="display:flex; gap:20px; align-items:center; flex-wrap:wrap">
          <svg viewBox="0 0 260 260" style="width:200px; height:200px; flex-shrink:0">
            {#each donut(d.hersteller_verteilung) as seg}
              <path d={seg.path} fill={seg.farbe} />
            {/each}
          </svg>
          <div class="legend">
            {#each donut(d.hersteller_verteilung) as seg}
              <div class="leg-row">
                <span class="leg-dot" style="background:{seg.farbe}"></span>
                <span class="leg-name">{seg.name}</span>
                <span class="leg-val">{seg.anzahl} · {seg.prozent}%</span>
              </div>
            {/each}
          </div>
        </div>
      </section>

      <!-- Preis-Histogramm -->
      <section class="chart-card">
        <h2>Preisklassen <small>gezahlte Preise in €</small></h2>
        {#if d.preis_histogramm.length}
          {@const maxH = Math.max(...d.preis_histogramm.map(h=>h.anzahl))}
          <svg viewBox="0 0 {W} {H}" class="chart">
            {#each d.preis_histogramm as h, i}
              {@const bw = (W-2*PAD)/d.preis_histogramm.length * 0.72}
              {@const x = PAD + (i+0.14)*(W-2*PAD)/d.preis_histogramm.length}
              {@const bh = (h.anzahl/maxH)*(H-2*PAD)}
              <rect x={x} y={H-PAD-bh} width={bw} height={bh} rx="3" fill="var(--accent-dark)" opacity="0.8" />
              <text x={x+bw/2} y={H-PAD+16} font-size="10" text-anchor="middle" fill="var(--ink-soft)">{h.klasse}</text>
              <text x={x+bw/2} y={H-PAD-bh-5} font-size="9" text-anchor="middle" fill="var(--ink)">{h.anzahl}</text>
            {/each}
          </svg>
        {/if}
      </section>
    </div>

    <!-- Top 10 teuerste -->
    <section class="chart-card">
      <h2>Wertvollste Modelle <small>höchster Kaufpreis</small></h2>
      <div class="top-list">
        {#each d.top_teuerste as t, i}
          <a href="/modell/{t.id}" class="top-row">
            <span class="top-rang">{i+1}</span>
            <span class="top-h">{t.hersteller}</span>
            <span class="top-typ">{t.typ}</span>
            <span class="top-preis">{euro(t.bezahlt)}</span>
          </a>
        {/each}
      </div>
    </section>
  {/if}
</div>

<style>
  .chart-card {
    background: var(--bg-card); border: 1px solid var(--line);
    border-radius: var(--radius); padding: 24px 26px; margin-bottom: 26px;
    box-shadow: var(--shadow);
  }
  .chart-card h2 {
    font-size: 1.4rem; margin-bottom: 18px; display: flex; align-items: baseline; gap: 12px;
  }
  .chart-card h2 small { font-family: var(--sans); font-size: .78rem; color: var(--ink-soft); font-weight: 400; letter-spacing: .02em; }
  .chart { width: 100%; height: auto; }
  .chart-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 26px; }
  .hbars { display: flex; flex-direction: column; gap: 12px; padding: 8px 0; }
  .hbar-row { display: grid; grid-template-columns: 70px 1fr 50px; align-items: center; gap: 12px; }
  .hbar-lbl { font-size: .85rem; color: var(--ink-soft); text-transform: uppercase; letter-spacing: .05em; }
  .hbar-track { background: var(--bg); border-radius: 6px; height: 22px; overflow: hidden; }
  .hbar-fill { height: 100%; border-radius: 6px; transition: width .4s; }
  .hbar-val { text-align: right; font-variant-numeric: tabular-nums; }
  .legend { display: flex; flex-direction: column; gap: 7px; font-size: .85rem; flex: 1; min-width: 180px; }
  .leg-row { display: grid; grid-template-columns: 14px 1fr auto; align-items: center; gap: 9px; }
  .leg-dot { width: 12px; height: 12px; border-radius: 3px; }
  .leg-name { color: var(--ink); }
  .leg-val { color: var(--ink-soft); font-variant-numeric: tabular-nums; }
  .top-list { display: flex; flex-direction: column; }
  .top-row {
    display: grid; grid-template-columns: 36px 110px 1fr auto; align-items: center; gap: 14px;
    padding: 12px 8px; border-bottom: 1px solid var(--line); transition: background .12s;
  }
  .top-row:hover { background: var(--bg); }
  .top-row:last-child { border-bottom: none; }
  .top-rang { font-family: var(--serif); font-size: 1.3rem; color: var(--accent); text-align: center; }
  .top-h { font-size: .72rem; letter-spacing: .12em; text-transform: uppercase; color: var(--accent); }
  .top-typ { color: var(--ink); }
  .top-preis { font-family: var(--serif); font-size: 1.1rem; font-weight: 600; }
  @media (max-width: 720px) {
    .chart-grid { grid-template-columns: 1fr; }
    .top-row { grid-template-columns: 28px 1fr auto; }
    .top-h { display: none; }
  }
</style>
