<script>
  import '$lib/styles.css';
  let { children } = $props();
</script>

<header class="site-header">
  <div class="inner">
    <a href="/" class="brand">
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
