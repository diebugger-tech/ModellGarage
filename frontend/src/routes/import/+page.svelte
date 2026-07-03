<script>
  import { importiereExcel } from '$lib/api.js';

  let datei = $state(null);
  let laeuft = $state(false);
  let ergebnis = $state(null);
  let fehler = $state(null);
  let dragover = $state(false);

  function waehle(e) {
    datei = e.target.files?.[0] ?? null;
    ergebnis = null; fehler = null;
  }

  function drop(e) {
    e.preventDefault();
    dragover = false;
    datei = e.dataTransfer.files?.[0] ?? null;
    ergebnis = null; fehler = null;
  }

  async function starten() {
    if (!datei) return;
    laeuft = true; fehler = null; ergebnis = null;
    try {
      ergebnis = await importiereExcel(datei);
    } catch (e) {
      fehler = e.message;
    } finally {
      laeuft = false;
    }
  }
</script>

<svelte:head><title>Excel importieren — ModellGarage</title></svelte:head>

<div class="container" style="max-width:760px">
  <div style="padding-top:28px"><a href="/" class="back-link">← Zurück zur Galerie</a></div>

  <h1 style="font-size:2.4rem; margin:20px 0 6px">Excel importieren</h1>
  <p style="color:var(--ink-soft); line-height:1.55; margin-bottom:30px">
    Lade die Sammlungs-Excel hoch. Alle Blätter werden erkannt (Wiking, Siku,
    Majorette, Matchbox …), Zustand und Kaufdatum automatisch geparst. Bereits
    vorhandene Katalog-Nummern werden nicht doppelt angelegt.
  </p>

  <div
    class="dropzone {dragover ? 'over' : ''}"
    ondragover={(e) => { e.preventDefault(); dragover = true; }}
    ondragleave={() => dragover = false}
    ondrop={drop}
    role="button" tabindex="0"
  >
    <input id="file" type="file" accept=".xlsx,.xlsm" onchange={waehle} style="display:none" />
    <label for="file" style="cursor:pointer; display:block">
      <div style="font-family:var(--serif); font-size:1.4rem; margin-bottom:8px">
        {datei ? datei.name : 'Datei hierher ziehen'}
      </div>
      <div style="color:var(--ink-soft); font-size:.9rem">
        {datei ? (datei.size/1024).toFixed(0) + ' KB — zum Ändern klicken' : 'oder klicken zum Auswählen (.xlsx)'}
      </div>
    </label>
  </div>

  <div style="margin-top:22px; display:flex; gap:12px; align-items:center">
    <button class="btn" onclick={starten} disabled={!datei || laeuft}>
      {laeuft ? 'Importiere …' : 'Import starten'}
    </button>
    {#if datei && !laeuft}
      <button class="btn ghost" onclick={() => { datei = null; ergebnis = null; fehler = null; }}>Zurücksetzen</button>
    {/if}
  </div>

  {#if fehler}
    <div class="box err">⚠ {fehler}</div>
  {/if}

  {#if ergebnis}
    <div class="box ok">
      <div style="font-family:var(--serif); font-size:1.3rem; margin-bottom:12px">Import erfolgreich</div>
      <dl class="rgrid">
        <dt>Datei</dt><dd>{ergebnis.datei}</dd>
        <dt>Blätter</dt><dd>{ergebnis.blaetter}</dd>
        <dt>Neue Katalog-Einträge</dt><dd>{ergebnis.katalog_neu}</dd>
        <dt>Importierte Modelle</dt><dd>{ergebnis.modelle}</dd>
        <dt>Übersprungen</dt><dd>{ergebnis.uebersprungen}</dd>
      </dl>
      <a href="/" class="btn" style="display:inline-block; margin-top:16px; text-decoration:none">Zur Galerie →</a>
    </div>
  {/if}
</div>

<style>
  .dropzone {
    border: 2px dashed var(--line);
    border-radius: var(--radius);
    background: var(--bg-card);
    padding: 54px 24px;
    text-align: center;
    transition: border-color .15s, background .15s;
  }
  .dropzone.over { border-color: var(--accent); background: rgba(138,109,59,.05); }
  .box { margin-top: 24px; padding: 22px 24px; border-radius: var(--radius); }
  .box.ok { background: #eef3ee; border: 1px solid #cfe0cf; }
  .box.err { background: #f7ece9; border: 1px solid #e6c8c0; color: #a35a45; }
  .rgrid { display: grid; grid-template-columns: 200px 1fr; gap: 8px 20px; margin: 0; }
  .rgrid dt { color: var(--ink-soft); }
  .rgrid dd { margin: 0; font-weight: 500; }
</style>
