// Dünne API-Anbindung ans FastAPI-Backend.
const BASE = '';

async function j(path) {
  const r = await fetch(BASE + path);
  if (!r.ok) throw new Error(`${r.status} ${path}`);
  return r.json();
}

export function getStatistik() {
  return j('/api/statistik');
}

export function getModelle({ q = '', hersteller = '', zustand = '', limit = 24, offset = 0, sort = 'id', order = 'asc' } = {}) {
  const p = new URLSearchParams();
  if (q) p.set('q', q);
  if (hersteller) p.set('hersteller', hersteller);
  if (zustand) p.set('zustand', zustand);
  p.set('limit', limit);
  p.set('offset', offset);
  p.set('sort', sort);
  p.set('order', order);
  return j('/api/modelle?' + p.toString());
}

export function getModell(id) {
  return j('/api/modelle/' + id);
}

export function getHersteller() {
  return j('/api/statistik/hersteller');
}

export function euro(v) {
  if (v == null) return '–';
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(v);
}

export async function importiereExcel(file) {
  const fd = new FormData();
  fd.append('datei', file);
  const r = await fetch('/api/import/excel', { method: 'POST', body: fd });
  const data = await r.json();
  if (!r.ok) throw new Error(data.detail || 'Import fehlgeschlagen');
  return data;
}

export async function uploadFoto(modellId, file) {
  const fd = new FormData();
  fd.append('datei', file);
  const r = await fetch('/api/modelle/' + modellId + '/foto', { method: 'POST', body: fd });
  const data = await r.json();
  if (!r.ok) throw new Error(data.detail || 'Upload fehlgeschlagen');
  return data;
}

export async function getFotos(modellId) {
  const r = await fetch('/api/modelle/' + modellId + '/fotos');
  if (!r.ok) return [];
  return r.json();
}

export async function loescheFoto(fotoId) {
  const r = await fetch('/api/fotos/' + fotoId, { method: 'DELETE' });
  return r.ok;
}

export async function erstelleModellVoll(daten) {
  const r = await fetch('/api/modelle/voll', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(daten)
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data.detail || 'Anlegen fehlgeschlagen');
  return data;
}

export async function aktualisiereModell(id, daten) {
  const r = await fetch('/api/modelle/' + id, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(daten)
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data.detail || 'Speichern fehlgeschlagen');
  return data;
}

export async function loescheModell(id) {
  const r = await fetch('/api/modelle/' + id, { method: 'DELETE' });
  return r.ok;
}
