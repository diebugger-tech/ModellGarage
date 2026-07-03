<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { getModell, euro, getFotos, uploadFoto, loescheFoto,
           aktualisiereModell, loescheModell } from '$lib/api.js';

  let modell = $state(null);
  let fehler = $state(false);
  let fotos = $state([]);
  let laedt = $state(false);
  let uploadFehler = $state(null);

  // Bearbeiten-Modus
  let editMode = $state(false);
  let e = $state({});
  let speichert = $state(false);
  let editFehler = $state(null);

  async function ladeFotos(id) { fotos = await getFotos(id); }

  onMount(async () => {
    try {
      modell = await getModell($page.params.id);
      await ladeFotos(modell.id);
    } catch {
      fehler = true;
    }
  });

  function startEdit() {
    e = {
      farbe: modell.farbe ?? '',
      zustand: modell.zustand ?? '',
      bezahlt: modell.bezahlt ?? '',
      schaetzwert: modell.schaetzwert ?? '',
      kaufdatum: modell.kaufdatum ?? '',
      anzahl: modell.anzahl ?? 1,
      bemerkung: modell.bemerkung ?? ''
    };
    editFehler = null;
    editMode = true;
  }

  function num(v) { return v === '' || v == null ? null : Number(v); }

  async function speichern() {
    speichert = true; editFehler = null;
    try {
      modell = await aktualisiereModell(modell.id, {
        farbe: e.farbe.trim() || null,
        zustand: e.zustand || null,
        bezahlt: num(e.bezahlt),
        schaetzwert: num(e.schaetzwert),
        kaufdatum: e.kaufdatum.trim() || null,
        anzahl: Number(e.anzahl) || 1,
        bemerkung: e.bemerkung.trim() || null
      });
      editMode = false;
    } catch (err) {
      editFehler = err.message;
    } finally {
      speichert = false;
    }
  }

  async function entferneModell() {
    if (!confirm('Dieses Modell wirklich löschen?')) return;
    await loescheModell(modell.id);
    goto('/');
  }

  async function fotoGewaehlt(ev) {
    const file = ev.target.files?.[0];
    if (!file) return;
    laedt = true; uploadFehler = null;
    try {
      await uploadFoto(modell.id, file);
      await ladeFotos(modell.id);
    } catch (err) {
      uploadFehler = err.message;
    } finally {
      laedt = false;
      ev.target.value = '';
    }
  }

  async function entferneFoto(fotoId) {
    if (!confirm('Foto wirklich löschen?')) return;
    await loescheFoto(fotoId);
    await ladeFotos(modell.id);
  }

  const initial = (typ) => (typ || '?').trim().charAt(0).toUpperCase();
  const zLabel = { z0: 'z0 — neuwertig', z1: 'z1 — sehr gut', z2: 'z2 — bespielt' };
</script>

<svelte:head><title>{modell?.katalog?.typ || 'Modell'} — ModellGarage</title></svelte:head>

<div class="container">
  <div style="padding-top:28px; display:flex; justify-content:space-between; align-items:center">
    <a href="/" class="back-link">← Zurück zur Galerie</a>
    {#if modell && !editMode}
      <div style="display:flex; gap:10px">
        <button class="btn ghost" onclick={startEdit}>Bearbeiten</button>
        <button class="btn ghost" style="color:#a35a45; border-color:#a35a45" onclick={entferneModell}>Löschen</button>
      </div>
    {/if}
  </div>

  {#if fehler}
    <div class="empty">Modell nicht gefunden.</div>
  {:else if !modell}
    <div class="loading">Lade …</div>
  {:else}
    <div class="detail-wrap detail">
      <div>
        <div class="detail-photo">
          {#if fotos.length > 0}
            <img src={'/' + fotos[0].pfad} alt={modell.katalog?.typ} />
          {:else}
            <span class="placeholder">{initial(modell.katalog?.typ)}</span>
          {/if}
        </div>
        <div class="fotos">
          {#each fotos as ft (ft.id)}
            <div class="foto-thumb">
              <img src={'/' + ft.pfad} alt="Foto" />
              <button class="del" onclick={() => entferneFoto(ft.id)} title="Löschen">×</button>
            </div>
          {/each}
          <label class="foto-add {laedt ? 'busy' : ''}">
            <input type="file" accept="image/*" onchange={fotoGewaehlt} style="display:none" disabled={laedt} />
            <span>{laedt ? '…' : '+ Foto'}</span>
          </label>
        </div>
        {#if uploadFehler}<div style="color:#a35a45; font-size:.85rem; margin-top:8px">⚠ {uploadFehler}</div>{/if}
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

        {#if editMode}
          <!-- Bearbeiten-Formular -->
          <div class="editform">
            <div class="erow">
              <label>Farbe<input bind:value={e.farbe} /></label>
              <label>Zustand
                <select bind:value={e.zustand}>
                  <option value="">—</option>
                  <option value="z0">z0 — neuwertig</option>
                  <option value="z1">z1 — sehr gut</option>
                  <option value="z2">z2 — bespielt</option>
                </select>
              </label>
            </div>
            <div class="erow">
              <label>Einkaufspreis €<input type="number" step="0.01" bind:value={e.bezahlt} /></label>
              <label>Schätzwert €<input type="number" step="0.01" bind:value={e.schaetzwert} /></label>
            </div>
            <div class="erow">
              <label>Kaufdatum<input type="date" bind:value={e.kaufdatum} /></label>
              <label>Anzahl<input type="number" min="1" bind:value={e.anzahl} /></label>
            </div>
            <label>Bemerkung<textarea rows="2" bind:value={e.bemerkung}></textarea></label>
            {#if editFehler}<div style="color:#a35a45; font-size:.85rem">⚠ {editFehler}</div>{/if}
            <div style="display:flex; gap:10px; margin-top:6px">
              <button class="btn" onclick={speichern} disabled={speichert}>{speichert ? 'Speichere …' : 'Speichern'}</button>
              <button class="btn ghost" onclick={() => editMode = false}>Abbrechen</button>
            </div>
          </div>
        {:else}
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
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .fotos { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 16px; }
  .foto-thumb { position: relative; width: 72px; height: 72px; border-radius: 8px; overflow: hidden; box-shadow: var(--shadow); }
  .foto-thumb img { width: 100%; height: 100%; object-fit: cover; }
  .foto-thumb .del {
    position: absolute; top: 2px; right: 2px; width: 20px; height: 20px;
    border: none; border-radius: 50%; background: rgba(26,26,26,.7); color: #fff;
    cursor: pointer; font-size: 14px; line-height: 1; display: flex; align-items: center; justify-content: center;
  }
  .foto-add {
    width: 72px; height: 72px; border: 2px dashed var(--line); border-radius: 8px;
    display: flex; align-items: center; justify-content: center; cursor: pointer;
    color: var(--ink-soft); font-size: .8rem; transition: border-color .15s;
  }
  .foto-add:hover { border-color: var(--accent); color: var(--accent); }
  .foto-add.busy { opacity: .5; }
  .editform { display: flex; flex-direction: column; gap: 14px; margin: 24px 0; }
  .erow { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
  .editform label { display: flex; flex-direction: column; gap: 5px; font-size: .78rem; color: var(--ink-soft); }
  .editform input, .editform select, .editform textarea {
    border: 1px solid var(--line); background: var(--bg-card); padding: 9px 12px;
    border-radius: 9px; color: var(--ink); font-size: 1rem; outline: none;
  }
  .editform input:focus, .editform select:focus, .editform textarea:focus { border-color: var(--accent); }
</style>
