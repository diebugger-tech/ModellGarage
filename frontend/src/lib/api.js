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
