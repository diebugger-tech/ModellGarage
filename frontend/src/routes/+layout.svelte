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
    <nav style="display:flex; gap:22px; font-size:.82rem; letter-spacing:.14em; text-transform:uppercase; color:var(--ink-soft)">
      <a href="/">Galerie</a>
      <a href="/neu">+ Anlegen</a>
      <a href="/import">Import</a>
      <a href="/api/export/excel">Export</a>
    </nav>
  </div>
</header>

<main>
  {@render children()}
</main>
