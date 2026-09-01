import { Platform } from 'react-native';
import * as SQLite from 'expo-sqlite';
import {
  getCachedObras,
  getCachedItemsForObra,
  getCachedMaterialesForObra,
  getCachedMaestrosForObra,
  addPendingAvance,
  getPendingAvancesFromCache,
  markPendingAvanceSyncedInCache,
  addPendingAsistencia,
  getPendingAsistenciasFromCache,
  markPendingAsistenciaSyncedInCache,
  addPendingReporte,
  getPendingReportesFromCache,
  markPendingReporteSyncedInCache,
} from '../services/memoryCache';

let db;

export function getDatabase() {
  if (!db) {
    if (Platform.OS === 'web') {
      // Mock db object on web
      db = {
        execSync: () => {},
        runSync: () => ({ insertId: Date.now(), rowsAffected: 1 }),
        getAllSync: () => [],
        getFirstSync: () => null,
      };
    } else {
      db = SQLite.openDatabaseSync('accuraop.db');
    }
  }
  return db;
}

/**
 * Initialize all tables in local SQLite using exact same column names
 * as remote Supabase PostgreSQL schema.
 */
export function initDatabase() {
  if (Platform.OS === 'web') return;

  const database = getDatabase();
  database.execSync(`
    CREATE TABLE IF NOT EXISTS perfiles_usuario (
      id TEXT PRIMARY KEY,
      nombre TEXT,
      email TEXT,
      rol TEXT,
      foto_perfil_url TEXT,
      telefono TEXT
    );

    CREATE TABLE IF NOT EXISTS obras (
      id TEXT PRIMARY KEY,
      nombre TEXT,
      estado TEXT DEFAULT 'Activa',
      color TEXT,
      fecha_creacion TEXT
    );

    CREATE TABLE IF NOT EXISTS obras_jefes_obra (
      id TEXT PRIMARY KEY,
      obra_id TEXT NOT NULL,
      jefe_obra_id TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS items_obra (
      id TEXT PRIMARY KEY,
      obra_id TEXT NOT NULL,
      ubicacion TEXT,
      plano TEXT,
      descripcion_plano TEXT,
      estructura TEXT,
      dimension TEXT,
      perfil TEXT,
      cantidad REAL,
      cantidad_estructuras REAL,
      largo_mm REAL,
      caras_expuestas INTEGER,
      perimetro_expuesto_mm REAL,
      resist_fuego TEXT,
      masividad_m1 REAL,
      area_expuesta_m2 REAL,
      material TEXT,
      certificacion TEXT,
      micras REAL,
      formula TEXT,
      tinetas REAL,
      sacos REAL,
      precio_unitario_contrato REAL,
      material_id TEXT,
      anotaciones TEXT
    );

    CREATE TABLE IF NOT EXISTS avances (
      id TEXT PRIMARY KEY,
      item_obra_id TEXT NOT NULL,
      jefe_obra_id TEXT NOT NULL,
      estado_pago_id TEXT,
      foto_url TEXT,
      comentario TEXT,
      cantidad REAL,
      fecha_captura_local TEXT,
      fecha_subida_servidor TEXT,
      estado_revision TEXT DEFAULT 'pendiente',
      synced INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS tipos_maestro (
      id TEXT PRIMARY KEY,
      nombre TEXT NOT NULL,
      sueldo_diario REAL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS maestros (
      id TEXT PRIMARY KEY,
      nombre TEXT NOT NULL,
      rut_dni TEXT,
      tipo_maestro_id TEXT,
      telefono TEXT,
      foto_perfil_url TEXT,
      estado TEXT DEFAULT 'Activo'
    );

    CREATE TABLE IF NOT EXISTS obras_maestros (
      obra_id TEXT NOT NULL,
      maestro_id TEXT NOT NULL,
      PRIMARY KEY (obra_id, maestro_id)
    );

    CREATE TABLE IF NOT EXISTS materiales (
      id TEXT PRIMARY KEY,
      nombre TEXT NOT NULL,
      unidad_medida TEXT,
      rendimiento_teorico_m2 REAL,
      descripcion TEXT
    );

    CREATE TABLE IF NOT EXISTS reporte_obra (
      id TEXT PRIMARY KEY,
      obra_id TEXT NOT NULL,
      jefe_obra_id TEXT NOT NULL,
      tipo_reporte TEXT DEFAULT 'actualizacion',
      mensaje TEXT,
      archivos_adjuntos TEXT,
      fecha_publicacion TEXT,
      estado_reb TEXT DEFAULT 'pendiente',
      synced INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS reporte_obra_consumos (
      id TEXT PRIMARY KEY,
      reporte_obra_id TEXT NOT NULL,
      material_id TEXT,
      material TEXT,
      cantidad REAL,
      unidad TEXT,
      fecha TEXT
    );

    CREATE TABLE IF NOT EXISTS asistencia_diaria (
      id TEXT PRIMARY KEY,
      obra_id TEXT NOT NULL,
      jefe_obra_id TEXT NOT NULL,
      fecha TEXT NOT NULL,
      foto_url TEXT,
      es_correctivo INTEGER DEFAULT 0,
      observaciones TEXT,
      fecha_registro TEXT,
      synced INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS asistencia_diaria_detalle (
      id TEXT PRIMARY KEY,
      asistencia_id TEXT NOT NULL,
      maestro_id TEXT NOT NULL,
      estado TEXT DEFAULT 'presente',
      valor_jornada REAL DEFAULT 1.0,
      observacion TEXT
    );
  `);
}

// ── Perfiles de Usuario ────────────────────────────────────────────

export function getPerfilUsuario(id) {
  if (Platform.OS === 'web') return null;
  const database = getDatabase();
  try {
    const rows = database.getAllSync('SELECT * FROM perfiles_usuario WHERE id = ? LIMIT 1', [id]);
    return rows?.[0] || null;
  } catch {
    return null;
  }
}

export function savePerfilUsuario(payload) {
  const { id, email, nombre, rol, foto_perfil_url, telefono } = payload;
  if (Platform.OS === 'web') return;
  const database = getDatabase();
  return database.runSync(
    `INSERT OR REPLACE INTO perfiles_usuario (id, email, nombre, rol, foto_perfil_url, telefono)
     VALUES (?, ?, ?, ?, ?, ?)`,
    [id, email || null, nombre || null, rol || 'jefe_obra', foto_perfil_url || null, telefono || null]
  );
}

// ── Obras ──────────────────────────────────────────────────────────

export function getObrasForJefe(jefeId) {
  if (Platform.OS === 'web') {
    return getCachedObras();
  }
  const database = getDatabase();
  try {
    if (jefeId) {
      const obrasJefe = database.getAllSync(
        `SELECT DISTINCT o.* FROM obras o
         JOIN obras_jefes_obra ojo ON o.id = ojo.obra_id
         WHERE ojo.jefe_obra_id = ?`,
        [jefeId]
      );
      if (obrasJefe && obrasJefe.length > 0) return obrasJefe;
    }
    const allLocal = database.getAllSync('SELECT * FROM obras ORDER BY nombre');
    if (allLocal && allLocal.length > 0) return allLocal;
    return getCachedObras();
  } catch (err) {
    console.warn('getObrasForJefe error:', err);
    return getCachedObras();
  }
}

// ── Items de obra ──────────────────────────────────────────────────

export function getItemsForObra(obraId) {
  if (Platform.OS === 'web') {
    return getCachedItemsForObra(obraId);
  }
  const database = getDatabase();
  try {
    const items = database.getAllSync('SELECT * FROM items_obra WHERE obra_id = ?', [obraId]);
    if (items && items.length > 0) return items;
    return getCachedItemsForObra(obraId);
  } catch (err) {
    console.warn('getItemsForObra error:', err);
    return getCachedItemsForObra(obraId);
  }
}

// ── Avances ────────────────────────────────────────────────────────

export { saveAvance as saveAdvance };

export function saveAvance(payload) {
  const { id, item_obra_id, jefe_obra_id, cantidad, comentario, foto_url } = payload;
  if (Platform.OS === 'web') {
    addPendingAvance(payload);
    return;
  }
  const database = getDatabase();
  const fecha = new Date().toISOString();
  return database.runSync(
    `INSERT OR REPLACE INTO avances
      (id, item_obra_id, jefe_obra_id, cantidad, comentario, foto_url,
       fecha_captura_local, estado_revision, synced)
     VALUES (?, ?, ?, ?, ?, ?, ?, 'pendiente', 0)`,
    [id, item_obra_id, jefe_obra_id, cantidad, comentario, foto_url, fecha]
  );
}

export function getUnsyncedAvances() {
  if (Platform.OS === 'web') {
    return getPendingAvancesFromCache();
  }
  const database = getDatabase();
  try {
    return database.getAllSync('SELECT * FROM avances WHERE synced = 0');
  } catch {
    return getPendingAvancesFromCache();
  }
}

export function markAvanceSynced(id, serverTimestamp) {
  if (Platform.OS === 'web') {
    markPendingAvanceSyncedInCache(id);
    return;
  }
  const database = getDatabase();
  return database.runSync(
    'UPDATE avances SET synced = 1, fecha_subida_servidor = ? WHERE id = ?',
    [serverTimestamp, id]
  );
}

// ── Tipos Maestro ──────────────────────────────────────────────────

export function getTiposMaestro() {
  if (Platform.OS === 'web') return [];
  const database = getDatabase();
  try {
    return database.getAllSync('SELECT * FROM tipos_maestro ORDER BY nombre');
  } catch { return []; }
}

// ── Maestros ───────────────────────────────────────────────────────

export function getMaestrosForObra(obraId) {
  if (Platform.OS === 'web') {
    return getCachedMaestrosForObra(obraId);
  }
  const database = getDatabase();
  try {
    if (obraId) {
      const maestrosObra = database.getAllSync(
        `SELECT DISTINCT m.*, tm.nombre AS cargo_nombre, tm.sueldo_diario
         FROM maestros m
         JOIN obras_maestros om ON m.id = om.maestro_id
         LEFT JOIN tipos_maestro tm ON m.tipo_maestro_id = tm.id
         WHERE om.obra_id = ?
         ORDER BY m.nombre`,
        [obraId]
      );
      if (maestrosObra && maestrosObra.length > 0) return maestrosObra;
    }
    const allLocal = database.getAllSync(
      `SELECT m.*, tm.nombre AS cargo_nombre, tm.sueldo_diario
       FROM maestros m
       LEFT JOIN tipos_maestro tm ON m.tipo_maestro_id = tm.id
       ORDER BY m.nombre`
    );
    if (allLocal && allLocal.length > 0) return allLocal;
    return getCachedMaestrosForObra(obraId);
  } catch (err) {
    console.warn('getMaestrosForObra error:', err);
    return getCachedMaestrosForObra(obraId);
  }
}

// ── Materiales ─────────────────────────────────────────────────────

export function getMaterialesForObra(obraId) {
  if (Platform.OS === 'web') {
    return getCachedMaterialesForObra(obraId);
  }
  const database = getDatabase();
  try {
    const mats = database.getAllSync('SELECT * FROM materiales ORDER BY nombre');
    if (mats && mats.length > 0) return mats;
    return getCachedMaterialesForObra(obraId);
  } catch {
    return getCachedMaterialesForObra(obraId);
  }
}

// ── Asistencia diaria ──────────────────────────────────────────────

export function getAsistenciaByObraFecha(obraId, fecha) {
  if (Platform.OS === 'web') return null;
  const database = getDatabase();
  try {
    const rows = database.getAllSync(
      'SELECT * FROM asistencia_diaria WHERE obra_id = ? AND fecha = ? LIMIT 1',
      [obraId, fecha]
    );
    return rows?.[0] || null;
  } catch { return null; }
}

export function saveAsistenciaDiaria(payload) {
  const { id, obra_id, jefe_obra_id, fecha, foto_url, observaciones, es_correctivo } = payload;
  if (Platform.OS === 'web') {
    addPendingAsistencia(payload);
    return;
  }
  const database = getDatabase();
  const fecha_registro = new Date().toISOString();
  return database.runSync(
    `INSERT OR REPLACE INTO asistencia_diaria
      (id, obra_id, jefe_obra_id, fecha, foto_url, observaciones,
       es_correctivo, fecha_registro, synced)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)`,
    [
      id, obra_id, jefe_obra_id, fecha,
      foto_url || null,
      observaciones || '',
      es_correctivo ? 1 : 0,
      fecha_registro,
    ]
  );
}

export function saveAsistenciaDetalle(payload) {
  const { id, asistencia_id, maestro_id, estado, valor_jornada, observacion } = payload;
  if (Platform.OS === 'web') return;
  const database = getDatabase();
  return database.runSync(
    `INSERT OR REPLACE INTO asistencia_diaria_detalle
      (id, asistencia_id, maestro_id, estado, valor_jornada, observacion)
     VALUES (?, ?, ?, ?, ?, ?)`,
    [id, asistencia_id, maestro_id, estado, valor_jornada, observacion || null]
  );
}

export function getUnsyncedAsistencias() {
  if (Platform.OS === 'web') return getPendingAsistenciasFromCache();
  const database = getDatabase();
  try {
    return database.getAllSync('SELECT * FROM asistencia_diaria WHERE synced = 0');
  } catch { return getPendingAsistenciasFromCache(); }
}

export function getAsistenciaDetalle(asistenciaId) {
  if (Platform.OS === 'web') return [];
  const database = getDatabase();
  try {
    return database.getAllSync(
      'SELECT * FROM asistencia_diaria_detalle WHERE asistencia_id = ?',
      [asistenciaId]
    );
  } catch { return []; }
}

export function markAsistenciaSynced(id) {
  if (Platform.OS === 'web') {
    markPendingAsistenciaSyncedInCache(id);
    return;
  }
  const database = getDatabase();
  return database.runSync(
    'UPDATE asistencia_diaria SET synced = 1 WHERE id = ?',
    [id]
  );
}

// ── Reporte Obra (Bitácora) ────────────────────────────────────────

export function saveReporteObra(payload) {
  const { id, obra_id, jefe_obra_id, tipo_reporte, mensaje, archivos_adjuntos } = payload;
  if (Platform.OS === 'web') {
    addPendingReporte(payload);
    return;
  }
  const database = getDatabase();
  const fecha_publicacion = new Date().toISOString();
  const adjuntosJson = JSON.stringify(archivos_adjuntos || []);
  return database.runSync(
    `INSERT OR REPLACE INTO reporte_obra
      (id, obra_id, jefe_obra_id, tipo_reporte, mensaje, archivos_adjuntos,
       fecha_publicacion, estado_reb, synced)
     VALUES (?, ?, ?, ?, ?, ?, ?, 'pendiente', 0)`,
    [id, obra_id, jefe_obra_id, tipo_reporte, mensaje, adjuntosJson, fecha_publicacion]
  );
}

export function saveReporteConsumo(payload) {
  const { id, reporte_obra_id, reporte_id, material_id, material_obra_id, material, cantidad, unidad, fecha } = payload;
  if (Platform.OS === 'web') return;
  const database = getDatabase();
  const fechaRecord = fecha || new Date().toISOString();
  const targetReporteId = reporte_obra_id || reporte_id;
  const targetMaterialId = material_id || material_obra_id || null;
  return database.runSync(
    `INSERT OR REPLACE INTO reporte_obra_consumos
      (id, reporte_obra_id, material_id, material, cantidad, unidad, fecha)
     VALUES (?, ?, ?, ?, ?, ?, ?)`,
    [id, targetReporteId, targetMaterialId, material, cantidad, unidad, fechaRecord]
  );
}

export function getUnsyncedReportes() {
  if (Platform.OS === 'web') return getPendingReportesFromCache();
  const database = getDatabase();
  try {
    return database.getAllSync('SELECT * FROM reporte_obra WHERE synced = 0');
  } catch { return getPendingReportesFromCache(); }
}

export function getReporteConsumos(reporteObraId) {
  if (Platform.OS === 'web') return [];
  const database = getDatabase();
  try {
    return database.getAllSync(
      'SELECT * FROM reporte_obra_consumos WHERE reporte_obra_id = ?',
      [reporteObraId]
    );
  } catch { return []; }
}

export function markReporteSynced(id) {
  if (Platform.OS === 'web') {
    markPendingReporteSyncedInCache(id);
    return;
  }
  const database = getDatabase();
  return database.runSync(
    'UPDATE reporte_obra SET synced = 1 WHERE id = ?',
    [id]
  );
}
