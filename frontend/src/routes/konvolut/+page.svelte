<script>
  import { onMount } from 'svelte';
  import { getKonvolute, erstelleKonvolut, konvolutKindHinzu, konvolutKindEntfernen,
           konvolutPreiseVerteilen, loescheKonvolut, getModelle, euro,
           konvolutKindAnlegen, uploadKonvolutFoto, getKonvolutFotos } from '$lib/api.js';

  let konvolute = $state([]);
  let laedt = $state(true);
  let konvolutFotos = $state({}); // { kid: [fotos] }

  // Neues Konvolut
  let neu = $state({ quelle: '', gesamtpreis: '', datum: '' });
  let anlegen = $state(false);

  // Modell-Suche zum Zuordnen
  let aktivKid = $state(null);
  let suche = $state('');
  let treffer = $state([]);
  let sucheTimer;

  // Modell direkt anlegen (Kind im Konvolut)
  let anlegenKind = $state(null); // kid
  const kindInit = { hersteller: 'Wiking', katalog_nr: '', typ: '', serie: '',
                     min_euro: '', max_euro: '', farbe: '', zustand: '', bemerkung: '', bezahlt: '' };
  let kindForm = $state({ ...kindInit });

  async function laden() {
    konvolute = await getKonvolute();
    for (const k of konvolute) {
      konvolutFotos[k.id] = await getKonvolutFotos(k.id);
    }
    laedt = false;
  }
  onMount(laden);

  async function konvolutAnlegen() {
    if (!neu.quelle.trim() && !neu.gesamtpreis) return;
    await erstelleKonvolut({
      quelle: neu.quelle.trim() || null,
      gesamtpreis: neu.gesamtpreis === '' ? null : Number(neu.gesamtpreis),
      datum: neu.datum.trim() || null
    });
    neu = { quelle: '', gesamtpreis: '', datum: '' };
    anlegen = false;
    await laden();
  }

  function onSuche() {
    clearTimeout(sucheTimer);
    sucheTimer = setTimeout(async () => {
      if (suche.trim().length < 2) { treffer = []; return; }
      const r = await getModelle({ q: suche, limit: 8 });
      treffer = r.items;
    }, 250);
  }

  async function zuordnen(kid, modellId) {
    await konvolutKindHinzu(kid, modellId);
    suche = ''; treffer = [];
    await laden();
  }
  async function entfernen(kid, modellId) {
    await konvolutKindEntfernen(kid, modellId);
    await laden();
  }
  async function verteilen(kid) {
    const r = await konvolutPreiseVerteilen(kid);
    alert(`Gesamtpreis ${euro(r.gesamtpreis)} gewichtet auf ${r.verteilt_auf} Modelle verteilt.`);
    await laden();
  }
  async function entfKonvolut(kid) {
    if (!confirm('Konvolut löschen? Die Modelle bleiben erhalten.')) return;
    await loescheKonvolut(kid);
    await laden();
  }

  async function kindSpeichern(kid) {
    const daten = {
      hersteller: kindForm.hersteller,
      katalog_nr: kindForm.katalog_nr || null,
      typ: kindForm.typ,
      serie: kindForm.serie || null,
      min_euro: kindForm.min_euro === '' ? null : Number(kindForm.min_euro),
      max_euro: kindForm.max_euro === '' ? null : Number(kindForm.max_euro),
      farbe: kindForm.farbe || null,
      zustand: kindForm.zustand || null,
      bemerkung: kindForm.bemerkung || null,
      bezahlt: kindForm.bezahlt === '' ? null : Number(kindForm.bezahlt),
    };
    await konvolutKindAnlegen(kid, daten);
    kindForm = { ...kindInit };
    anlegenKind = null;
    await laden();
  }

  async function fotoUpload(kid, e) {
    const file = e.target.files?.[0];
    if (!file) return;
    await uploadKonvolutFoto(kid, file);
    konvolutFotos[kid] = await getKonvolutFotos(kid);
  }
</script>

<svelte:head><title>Konvolute — ModellGarage</title></svelte:head>

<div class="container" style="max-width:960px">
  <div style="padding-top:28px; display:flex; justify-content:space-between; align-items:center">
    <a href="/" class="back-link">← Zurück zur Galerie</a>
    <button class="btn" onclick={() => anlegen = !anlegen}>+ Neues Konvolut</button>
  </div>
  <h1 style="font-size:2.6rem; margin:18px 0 8px">Konvolute</h1>
  <p style="color:var(--ink-soft); line-height:1.55; margin-bottom:26px">
    Sammelkäufe (Auktionspakete) mit mehreren Modellen. Ordne die einzelnen Autos
    zu und lass den Gesamtpreis <b>gewichtet nach Katalogwert</b> auf sie verteilen —
    ein teures Modell bekommt einen größeren Anteil als ein günstiges.
  </p>

  {#if anlegen}
    <div class="anlege-box">
      <div class="arow">
        <label>Quelle<input bind:value={neu.quelle} placeholder="z.B. eBay-Auktion 30.06." /></label>
        <label>Gesamtpreis €<input type="number" step="0.01" bind:value={neu.gesamtpreis} /></label>
        <label>Datum<input type="date" bind:value={neu.datum} /></label>
      </div>
      <div style="display:flex; gap:10px; margin-top:12px">
        <button class="btn" onclick={konvolutAnlegen}>Anlegen</button>
        <button class="btn ghost" onclick={() => anlegen = false}>Abbrechen</button>
      </div>
    </div>
  {/if}

  {#if laedt}
    <div class="loading">Lade …</div>
  {:else if konvolute.length === 0}
    <div class="empty">Noch keine Konvolute. Lege eins an, um Auktionspakete zu verwalten.</div>
  {:else}
    {#each konvolute as k (k.id)}
      <div class="konvolut-card">
        <div class="k-head">
          <div>
            <div class="k-quelle">{k.quelle || 'Konvolut #' + k.id}</div>
            <div class="k-meta">
              {#if k.gesamtpreis != null}Gesamtpreis {euro(k.gesamtpreis)} · {/if}
              {k.anzahl_kinder} Modell(e){#if k.datum} · {k.datum}{/if}
            </div>
          </div>
          <div style="display:flex; gap:8px">
            {#if k.gesamtpreis != null && k.anzahl_kinder > 0}
              <button class="btn" onclick={() => verteilen(k.id)}>Preise verteilen</button>
            {/if}
            <button class="btn ghost" style="color:#a35a45; border-color:#a35a45" onclick={() => entfKonvolut(k.id)}>×</button>
          </div>
        </div>

        <!-- Fotos -->
        {#if konvolutFotos[k.id]?.length}
          <div class="fotos">
            {#each konvolutFotos[k.id] as foto}
              <img src="/{foto.pfad}" alt="Konvolutfoto" />
            {/each}
          </div>
        {/if}
        <label class="foto-upload">
          <input type="file" accept="image/*" onchange={(e) => fotoUpload(k.id, e)} />
          + Foto
        </label>

        <!-- Kinder -->
        {#if k.kinder.length}
          <div class="kinder">
            {#each k.kinder as kind (kind.id)}
              <div class="kind-row">
                <a href="/modell/{kind.id}" class="kind-typ">{kind.katalog?.hersteller} — {kind.katalog?.typ}</a>
                <span class="kind-preis">{euro(kind.bezahlt)}</span>
                <button class="kind-del" onclick={() => entfernen(k.id, kind.id)} title="aus Konvolut entfernen">−</button>
              </div>
            {/each}
          </div>
        {/if}

        <!-- Kind anlegen -->
        {#if anlegenKind === k.id}
          <div class="kind-form">
            <div class="krow">
              <label>Hersteller
                <select bind:value={kindForm.hersteller}>
                  <option>Wiking</option>
                  <option>Siku</option>
                  <option>Majorette</option>
                  <option>Matchbox</option>
                  <option>Sonstige</option>
                </select>
              </label>
              <label>Katalog-Nr.<input bind:value={kindForm.katalog_nr} placeholder="30/6K." /></label>
              <label>Typ<input bind:value={kindForm.typ} placeholder="VW Käfer" /></label>
              <label>Serie<input bind:value={kindForm.serie} placeholder="Superfast" /></label>
            </div>
            <div class="krow">
              <label>Min €<input type="number" step="0.01" bind:value={kindForm.min_euro} /></label>
              <label>Max €<input type="number" step="0.01" bind:value={kindForm.max_euro} /></label>
              <label>Farbe<input bind:value={kindForm.farbe} /></label>
              <label>Zustand
                <select bind:value={kindForm.zustand}>
                  <option value="">–</option>
                  <option value="z0">z0 (neuwertig)</option>
                  <option value="z1">z1 (gut)</option>
                  <option value="z2">z2 (bespielt)</option>
                </select>
              </label>
              <label>Bezahlt €<input type="number" step="0.01" bind:value={kindForm.bezahlt} /></label>
            </div>
            <label style="margin-top:10px">Bemerkung<textarea bind:value={kindForm.bemerkung} rows="2"></textarea></label>
            <div style="display:flex; gap:10px; margin-top:12px">
              <button class="btn" onclick={() => kindSpeichern(k.id)}>Speichern</button>
              <button class="btn ghost" onclick={() => anlegenKind = null}>Abbrechen</button>
            </div>
          </div>
        {:else}
          <button class="btn ghost" style="margin-top:12px" onclick={() => anlegenKind = k.id}>+ Modell direkt anlegen</button>
        {/if}

        <!-- Bestehendes Modell zuordnen -->
        {#if aktivKid === k.id}
          <div class="zuordnen">
            <input placeholder="Modell suchen (Typ, Nr. …)" bind:value={suche} oninput={onSuche} />
            {#if treffer.length}
              <div class="treffer">
                {#each treffer as t}
                  <button class="treffer-row" onclick={() => zuordnen(k.id, t.id)}>
                    {t.katalog?.hersteller} — {t.katalog?.typ} <span style="color:var(--ink-soft)">{euro(t.bezahlt)}</span>
                  </button>
                {/each}
              </div>
            {/if}
            <button class="btn ghost" style="margin-top:8px" onclick={() => { aktivKid = null; suche=''; treffer=[]; }}>Fertig</button>
          </div>
        {:else}
          <button class="btn ghost" style="margin-top:12px" onclick={() => aktivKid = k.id}>+ Bestehendes Modell zuordnen</button>
        {/if}
      </div>
    {/each}
  {/if}
</div>

<style>
  .anlege-box, .konvolut-card {
    background: var(--bg-card); border: 1px solid var(--line);
    border-radius: var(--radius); padding: 22px 24px; margin-bottom: 20px;
    box-shadow: var(--shadow);
  }
  .arow { display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 14px; }
  .arow label, .zuordnen label, .kind-form label { display: flex; flex-direction: column; gap: 5px; font-size: .8rem; color: var(--ink-soft); }
  input, select, textarea {
    border: 1px solid var(--line); background: var(--bg); padding: 9px 12px;
    border-radius: 9px; color: var(--ink); font-size: 1rem; outline: none; width: 100%;
  }
  input:focus, select:focus, textarea:focus { border-color: var(--accent); }
  .k-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
  .k-quelle { font-family: var(--serif); font-size: 1.4rem; }
  .k-meta { color: var(--ink-soft); font-size: .88rem; margin-top: 4px; }
  .fotos { display: flex; gap: 10px; margin-top: 14px; overflow-x: auto; }
  .fotos img { height: 120px; border-radius: 10px; object-fit: cover; border: 1px solid var(--line); }
  .foto-upload { display: inline-block; margin-top: 10px; font-size: .82rem; color: var(--accent); cursor: pointer; }
  .foto-upload input { display: none; }
  .kinder { margin-top: 16px; border-top: 1px solid var(--line); padding-top: 12px; display: flex; flex-direction: column; gap: 6px; }
  .kind-row { display: grid; grid-template-columns: 1fr auto 28px; align-items: center; gap: 12px; padding: 4px 0; }
  .kind-typ { color: var(--ink); }
  .kind-typ:hover { color: var(--accent); }
  .kind-preis { font-variant-numeric: tabular-nums; color: var(--ink-soft); }
  .kind-del { border: 1px solid var(--line); background: transparent; border-radius: 6px; cursor: pointer; color: #a35a45; width: 26px; height: 26px; }
  .kind-form { margin-top: 14px; padding: 16px; background: var(--bg); border-radius: 12px; border: 1px solid var(--line); }
  .krow { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 4px; }
  .zuordnen { margin-top: 14px; }
  .treffer { margin-top: 8px; border: 1px solid var(--line); border-radius: 9px; overflow: hidden; }
  .treffer-row { display: block; width: 100%; text-align: left; padding: 10px 14px; border: none; background: var(--bg-card); cursor: pointer; border-bottom: 1px solid var(--line); }
  .treffer-row:hover { background: var(--bg); }
  .treffer-row:last-child { border-bottom: none; }
  @media (max-width: 760px) { .arow { grid-template-columns: 1fr; } .krow { grid-template-columns: 1fr 1fr; } }
  @media (max-width: 480px) { .krow { grid-template-columns: 1fr; } }
</style>
