/**
 * In-memory cache for catalog and pending transaction data.
 * Crucial for web mode where SQLite native module is stubbed out.
 */

const cache = {
  obras: [],
  items: [],
  materiales: [],
  maestros: [],
  jefeId: null,
  pendingAvances: [],
  pendingAsistencias: [],
  pendingReportes: [],
};

// ── Setters ──────────────────────────────────────────────────────

export function cacheObras(obras) {
  cache.obras = obras || [];
}

export function cacheItems(items) {
  cache.items = items || [];
}

export function cacheMateriales(materiales) {
  cache.materiales = materiales || [];
}

export function cacheMaestros(maestros) {
  cache.maestros = maestros || [];
}

export function cacheJefeId(id) {
  cache.jefeId = id;
}

// ── Getters ──────────────────────────────────────────────────────

export function getCachedObras() {
  return cache.obras;
}

export function getCachedItemsForObra(obraId) {
  if (!obraId) return cache.items;
  return cache.items.filter((i) => i.obra_id === obraId);
}

export function getCachedMaterialesForObra(obraId) {
  return cache.materiales;
}

export function getCachedMaestrosForObra(obraId) {
  return cache.maestros;
}

export function getCachedJefeId() {
  return cache.jefeId;
}

// ── Pending Transactions (Web Fallback) ──────────────────────────

export function addPendingAvance(avance) {
  cache.pendingAvances.push({ ...avance, synced: 0 });
}

export function getPendingAvancesFromCache() {
  return cache.pendingAvances.filter((a) => a.synced === 0);
}

export function markPendingAvanceSyncedInCache(id) {
  const item = cache.pendingAvances.find((a) => a.id === id);
  if (item) item.synced = 1;
}

export function addPendingAsistencia(asistencia) {
  cache.pendingAsistencias.push({ ...asistencia, synced: 0 });
}

export function getPendingAsistenciasFromCache() {
  return cache.pendingAsistencias.filter((a) => a.synced === 0);
}

export function markPendingAsistenciaSyncedInCache(id) {
  const item = cache.pendingAsistencias.find((a) => a.id === id);
  if (item) item.synced = 1;
}

export function addPendingReporte(reporte) {
  cache.pendingReportes.push({ ...reporte, synced: 0 });
}

export function getPendingReportesFromCache() {
  return cache.pendingReportes.filter((r) => r.synced === 0);
}

export function markPendingReporteSyncedInCache(id) {
  const item = cache.pendingReportes.find((r) => r.id === id);
  if (item) item.synced = 1;
}

export function clearCache() {
  cache.obras = [];
  cache.items = [];
  cache.materiales = [];
  cache.maestros = [];
  cache.jefeId = null;
  cache.pendingAvances = [];
  cache.pendingAsistencias = [];
  cache.pendingReportes = [];
}
