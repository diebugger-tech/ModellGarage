<script>
  // Schriften lokal (self-hosted via @fontsource) — kein Google-CDN, kein
  // externer Request, kein IP-Abfluss (DSGVO). Gewichte wie zuvor: Cormorant
  // Garamond 400/500/600, Inter 300/400/500/600.
  import '@fontsource/cormorant-garamond/400.css';
  import '@fontsource/cormorant-garamond/500.css';
  import '@fontsource/cormorant-garamond/600.css';
  import '@fontsource/inter/300.css';
  import '@fontsource/inter/400.css';
  import '@fontsource/inter/500.css';
  import '@fontsource/inter/600.css';
  import '$lib/styles.css';
  import { onMount } from 'svelte';
  let { children } = $props();

  // Intro-Fahrt: einmal pro App-Start (Browser-Session) — und auf Klick aufs Logo.
  let zeigeIntro = $state(false);
  let introKey = $state(0);
  function spieleIntro() {
    zeigeIntro = true;
    introKey += 1; // Neu-Mount des Elements startet die CSS-Animation erneut
  }
  onMount(() => {
    try {
      if (!sessionStorage.getItem('mg_intro')) {
        spieleIntro();
        sessionStorage.setItem('mg_intro', '1');
      }
    } catch { /* sessionStorage nicht verfügbar → einfach nicht animieren */ }
  });
</script>

<header class="site-header" style="position:relative; overflow:hidden">
  {#if zeigeIntro}
    {#key introKey}
      <div class="szene" aria-hidden="true">
        <!-- Auto: fährt von rechts herein und verschwindet in der Garage (links) -->
        <svg class="auto" viewBox="0 0 96 34" width="40" height="15">
          <path d="M3,25 C4,17 11,15 17,15 L30,15 C35,8 44,7 52,9 C58,10.5 62,13 66,15 L80,16 C88,17 92,20 93,25
                   L86,25 a7,7 0 0 0 -14,0 L38,25 a7,7 0 0 0 -14,0 Z" fill="currentColor"/>
          <circle cx="31" cy="25" r="6" fill="currentColor"/>
          <circle cx="79" cy="25" r="6" fill="currentColor"/>
          <circle cx="31" cy="25" r="2.4" fill="var(--bg)"/>
          <circle cx="79" cy="25" r="2.4" fill="var(--bg)"/>
        </svg>
        <!-- Garage: Sturz + rechter Pfosten + Rolltor (rollt hoch/runter) -->
        <div class="sturz"></div>
        <div class="pfosten"></div>
        <div class="tor-rahmen"><div class="tor"></div></div>
      </div>
    {/key}
  {/if}
  <div class="inner">
    <a href="/" class="brand" onclick={spieleIntro} title="Animation abspielen">
      Modell<span>Garage</span>
      <small>Die Sammlung</small>
    </a>
    <nav style="display:flex; gap:18px; font-size:.78rem; letter-spacing:.12em; text-transform:uppercase; color:var(--ink-soft); flex-wrap:wrap; align-items:center">
      <a href="/">Galerie</a>
      <a href="/statistik">Statistik</a>
      <a href="/konvolut">Konvolute</a>
      <a href="/wunschliste">Lücken</a>
      <a href="/neu">+ Anlegen</a>
      <a href="/import">Import</a>
      <a href="/api/export/excel">Export</a>
      <a href="/api/extras/backup" title="Datenbank sichern">Backup</a>
    </nav>
  </div>
</header>

<main>
  {@render children()}
</main>

<style>
  /* Bühne über die volle Headerbreite: Auto fährt einmal quer durch, Garage links */
  .szene {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 3px;
    height: 30px;
    overflow: hidden;             /* Auto verschwindet am linken Rand = in der Garage */
    pointer-events: none;
    color: var(--accent);
    animation: szene-blende 6.5s linear 0.2s 1 both;
    will-change: opacity;
  }
  @keyframes szene-blende {
    0%, 90% { opacity: 0.4; }
    100%    { opacity: 0; }
  }

  /* Garage-Rahmen ganz links (Öffnung am linken Rand, Auto wird dort geclippt) */
  .sturz { position: absolute; left: 0; bottom: 27px; width: 42px; height: 3px; background: currentColor; }
  .pfosten { position: absolute; left: 39px; bottom: 0; width: 3px; height: 30px; background: currentColor; }
  .tor-rahmen { position: absolute; left: 0; bottom: 0; width: 39px; height: 27px; overflow: hidden; }
  .tor {
    width: 100%; height: 100%; background: currentColor; transform-origin: top;
    animation: tor 6.5s ease 0.2s 1 both;
  }
  @keyframes tor {
    0%   { transform: translateY(0); }        /* geschlossen */
    8%   { transform: translateY(-100%); }    /* rollt hoch (offen) */
    80%  { transform: translateY(-100%); }    /* bleibt offen, während Auto durchfährt */
    90%  { transform: translateY(0); }        /* rollt zu, Auto ist drin */
    100% { transform: translateY(0); }
  }

  /* Auto: startet ganz rechts, fährt einmal quer durch den Header in die Garage */
  .auto {
    position: absolute; bottom: 1px; left: 0; display: block;
    animation: auto-fahrt 6.5s cubic-bezier(0.45, 0, 0.35, 1) 0.2s 1 both;
    will-change: transform;
  }
  @keyframes auto-fahrt {
    0%, 6% { transform: translateX(calc(100vw + 20px)) scaleX(-1); } /* wartet rechts bis Tor offen */
    80%    { transform: translateX(-46px) scaleX(-1); }              /* quer durch, verschwindet links in der Garage */
    100%   { transform: translateX(-46px) scaleX(-1); }
  }

  @media (prefers-reduced-motion: reduce) {
    .szene { display: none; }
  }
</style>
