import NetInfo from '@react-native-community/netinfo';
import { supabase } from '../services/supabase';
import {
  getDatabase,
  getUnsyncedAvances,
  markAvanceSynced,
  getUnsyncedAsistencias,
  getAsistenciaDetalle,
  markAsistenciaSynced,
  getUnsyncedReportes,
  getReporteConsumos,
  markReporteSynced,
} from './db';
import {
  cacheObras,
  cacheItems,
  cacheJefeId,
  cacheMateriales,
  cacheMaestros,
} from '../services/memoryCache';

// ─────────────────────────────────────────────────────────────────────────────
// syncCatalog — Download all data needed for offline operation.
// Supabase RLS automatically filters rows for the authenticated user session.
// ─────────────────────────────────────────────────────────────────────────────
export async function syncCatalog(jefeId) {
  try {
    const database = getDatabase();

    // 0. Fetch perfil_usuario
    let perfilUsuario = null;
    if (jefeId) {
      const { data: pData, error: pErr } = await supabase
        .from('perfiles_usuario')
        .select('*')
        .eq('id', jefeId);
      if (pErr) console.warn('[syncCatalog] perfiles_usuario fetch error:', pErr);
      perfilUsuario = pData?.[0] || null;
    }

    // 1. Fetch obras (Supabase RLS automatically filters obras visible to user/admin)
    const { data: obras, error: obrasErr } = await supabase
      .from('obras')
      .select('*');
    if (obrasErr) console.warn('[syncCatalog] obras fetch error:', obrasErr);

    const obraList = obras || [];
    const obraIds = obraList.map((o) => o.id);

    // 2. Fetch relaciones (obras_jefes_obra)
    const { data: relaciones, error: relErr } = await supabase
      .from('obras_jefes_obra')
      .select('*');
    if (relErr) console.warn('[syncCatalog] relaciones fetch error:', relErr);

    // 3. Fetch items_obra for all downloaded obras
    let items = [];
    if (obraIds.length > 0) {
      const { data: itemsData, error: itemsErr } = await supabase
        .from('items_obra')
        .select('*')
        .in('obra_id', obraIds);
      if (itemsErr) console.warn('[syncCatalog] items_obra fetch error:', itemsErr);
      items = itemsData || [];
    } else {
      const { data: allItems } = await supabase.from('items_obra').select('*');
      items = allItems || [];
    }

    // 4. Fetch tipos_maestro
    const { data: tiposMaestro } = await supabase
      .from('tipos_maestro')
      .select('id, nombre, sueldo_diario');

    // 5. Fetch maestros and assignment
    let maestros = [];
    let obrasMaestros = [];
    const { data: om } = await supabase.from('obras_maestros').select('*');
    obrasMaestros = om || [];

    const { data: m } = await supabase.from('maestros').select('*');
    maestros = m || [];

    // 6. Fetch materiales
    const { data: materiales } = await supabase.from('materiales').select('*');

    // ── Persist to SQLite ──────────────────────────────────────────────
    database.execSync('BEGIN TRANSACTION');
    try {
      // perfiles_usuario
      if (perfilUsuario) {
        database.runSync(
          `INSERT OR REPLACE INTO perfiles_usuario (id, email, nombre, rol, foto_perfil_url, telefono)
           VALUES (?, ?, ?, ?, ?, ?)`,
          [
            perfilUsuario.id,
            perfilUsuario.email || null,
            perfilUsuario.nombre || null,
            perfilUsuario.rol || 'jefe_obra',
            perfilUsuario.foto_perfil_url || null,
            perfilUsuario.telefono || null,
          ]
        );
      }

      // Obras
      for (const o of obraList) {
        database.runSync(
          `INSERT OR REPLACE INTO obras (id, nombre, estado, color, fecha_creacion)
           VALUES (?, ?, ?, ?, ?)`,
          [o.id, o.nombre, o.estado || 'Activa', o.color || null, o.fecha_creacion || null]
        );
      }

      // obras_jefes_obra
      for (const r of relaciones || []) {
        database.runSync(
          `INSERT OR REPLACE INTO obras_jefes_obra (id, obra_id, jefe_obra_id)
           VALUES (?, ?, ?)`,
          [r.id, r.obra_id, r.jefe_obra_id]
        );
      }

      // items_obra
      for (const i of items) {
        database.runSync(
          `INSERT OR REPLACE INTO items_obra (
             id, obra_id, ubicacion, plano, descripcion_plano, estructura, dimension,
             perfil, cantidad, cantidad_estructuras, largo_mm, caras_expuestas,
             perimetro_expuesto_mm, resist_fuego, masividad_m1, area_expuesta_m2,
             material, certificacion, micras, formula, tinetas, sacos,
             precio_unitario_contrato, material_id, anotaciones
           ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,
          [
            i.id, i.obra_id, i.ubicacion, i.plano, i.descripcion_plano,
            i.estructura, i.dimension, i.perfil, i.cantidad,
            i.cantidad_estructuras, i.largo_mm, i.caras_expuestas,
            i.perimetro_expuesto_mm, i.resist_fuego, i.masividad_m1,
            i.area_expuesta_m2, i.material, i.certificacion, i.micras,
            i.formula, i.tinetas, i.sacos, i.precio_unitario_contrato,
            i.material_id, i.anotaciones,
          ]
        );
      }

      // tipos_maestro
      for (const t of tiposMaestro || []) {
        database.runSync(
          `INSERT OR REPLACE INTO tipos_maestro (id, nombre, sueldo_diario) VALUES (?,?,?)`,
          [t.id, t.nombre, t.sueldo_diario || 0]
        );
      }

      // maestros
      for (const m of maestros) {
        database.runSync(
          `INSERT OR REPLACE INTO maestros
             (id, nombre, rut_dni, tipo_maestro_id, telefono, foto_perfil_url, estado)
           VALUES (?,?,?,?,?,?,?)`,
          [m.id, m.nombre, m.rut_dni, m.tipo_maestro_id, m.telefono, m.foto_perfil_url, m.estado || 'Activo']
        );
      }

      // obras_maestros
      for (const om of obrasMaestros) {
        database.runSync(
          `INSERT OR REPLACE INTO obras_maestros (obra_id, maestro_id) VALUES (?,?)`,
          [om.obra_id, om.maestro_id]
        );
      }

      // materiales
      for (const mat of materiales || []) {
        database.runSync(
          `INSERT OR REPLACE INTO materiales
             (id, nombre, unidad_medida, rendimiento_teorico_m2, descripcion)
           VALUES (?,?,?,?,?)`,
          [mat.id, mat.nombre, mat.unidad_medida, mat.rendimiento_teorico_m2, mat.descripcion]
        );
      }

      database.execSync('COMMIT');
    } catch (err) {
      database.execSync('ROLLBACK');
      throw err;
    }

    // Update in-memory cache
    cacheJefeId(jefeId);
    cacheObras(obraList);
    cacheItems(items);
    cacheMateriales(materiales || []);
    cacheMaestros(maestros);

    console.log(`[syncCatalog] Downloaded: ${obraList.length} obras, ${items.length} items, ${maestros.length} maestros`);
    return true;
  } catch (error) {
    console.error('[syncCatalog] Error:', error?.message || error);
    return false;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Photo upload helper
// ─────────────────────────────────────────────────────────────────────────────
async function uploadLocalPhoto(localUri, bucket, storagePath) {
  try {
    const response = await fetch(localUri);
    const blob = await response.blob();

    const arrayBuffer = await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsArrayBuffer(blob);
    });

    const { error: uploadError } = await supabase.storage
      .from(bucket)
      .upload(storagePath, arrayBuffer, {
        contentType: 'image/jpeg',
        upsert: true,
      });

    if (uploadError) throw new Error(uploadError.message);

    const { data: urlData } = supabase.storage.from(bucket).getPublicUrl(storagePath);
    return urlData.publicUrl;
  } catch (err) {
    console.warn('[sync] Photo upload failed:', err.message);
    return localUri;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// syncAvances
// ─────────────────────────────────────────────────────────────────────────────
export async function syncAvances(onProgress) {
  const state = await NetInfo.fetch();
  if (!state.isConnected) {
    if (onProgress) onProgress({ status: 'offline', message: 'Sin conexión a internet' });
    return { success: 0, failed: 0 };
  }

  const unsynced = getUnsyncedAvances();
  if (unsynced.length === 0) {
    if (onProgress) onProgress({ status: 'idle', message: 'Todo está sincronizado' });
    return { success: 0, failed: 0 };
  }

  let successCount = 0;
  let failCount = 0;
  const uploadedPhotoCache = new Map();

  for (const avance of unsynced) {
    try {
      let foto_url = avance.foto_url;

      if (foto_url && (foto_url.startsWith('file://') || foto_url.startsWith('content://'))) {
        if (uploadedPhotoCache.has(foto_url)) {
          foto_url = uploadedPhotoCache.get(foto_url);
        } else {
          const storagePath = `avances/${avance.jefe_obra_id}/${avance.id}.jpg`;
          const remoteUrl = await uploadLocalPhoto(foto_url, 'accuratek-data', storagePath);
          if (remoteUrl && remoteUrl !== foto_url) {
            uploadedPhotoCache.set(foto_url, remoteUrl);
            foto_url = remoteUrl;
          }
        }
      }

      const { error } = await supabase.from('avances').insert({
        id: avance.id,
        item_obra_id: avance.item_obra_id,
        jefe_obra_id: avance.jefe_obra_id,
        foto_url,
        comentario: avance.comentario,
        cantidad: avance.cantidad,
        fecha_captura_local: avance.fecha_captura_local,
        estado_revision: 'pendiente',
      });

      if (error) throw new Error(error.message);

      markAvanceSynced(avance.id, new Date().toISOString());
      successCount++;
      if (onProgress) onProgress({ status: 'item_synced', id: avance.id });
    } catch (err) {
      console.error(`[sync] avance ${avance.id} failed:`, err.message);
      failCount++;
    }
  }

  const result = {
    status: 'complete',
    success: successCount,
    failed: failCount,
    message: `Avances: ${successCount} sincronizados, ${failCount} fallidos`,
  };
  if (onProgress) onProgress(result);
  return result;
}

export { syncAvances as syncAdvances };

// ─────────────────────────────────────────────────────────────────────────────
// syncAsistencias
// ─────────────────────────────────────────────────────────────────────────────
export async function syncAsistencias(onProgress) {
  const state = await NetInfo.fetch();
  if (!state.isConnected) return { success: 0, failed: 0 };

  const unsynced = getUnsyncedAsistencias();
  if (unsynced.length === 0) return { success: 0, failed: 0 };

  let successCount = 0;
  let failCount = 0;

  for (const asistencia of unsynced) {
    try {
      let foto_url = asistencia.foto_url;

      if (foto_url && (foto_url.startsWith('file://') || foto_url.startsWith('content://'))) {
        const storagePath = `asistencia/${asistencia.jefe_obra_id}/${asistencia.id}.jpg`;
        foto_url = await uploadLocalPhoto(foto_url, 'accuratek-data', storagePath);
      }

      const { error } = await supabase.from('asistencia_diaria').insert({
        id: asistencia.id,
        obra_id: asistencia.obra_id,
        jefe_obra_id: asistencia.jefe_obra_id,
        fecha: asistencia.fecha,
        foto_url,
        es_correctivo: asistencia.es_correctivo === 1,
        observaciones: asistencia.observaciones,
        fecha_registro: asistencia.fecha_registro,
      });
      if (error) throw new Error(error.message);

      const detalles = getAsistenciaDetalle(asistencia.id);
      if (detalles.length > 0) {
        const { error: detErr } = await supabase
          .from('asistencia_diaria_detalle')
          .insert(
            detalles.map((d) => ({
              id: d.id,
              asistencia_id: d.asistencia_id,
              maestro_id: d.maestro_id,
              estado: d.estado,
              valor_jornada: d.valor_jornada,
              observacion: d.observacion,
            }))
          );
        if (detErr) console.warn('[sync] asistencia_detalle insert error:', detErr.message);
      }

      markAsistenciaSynced(asistencia.id);
      successCount++;
    } catch (err) {
      console.error(`[sync] asistencia ${asistencia.id} failed:`, err.message);
      failCount++;
    }
  }

  const result = {
    status: 'complete',
    success: successCount,
    failed: failCount,
    message: `Asistencias: ${successCount} ok, ${failCount} fallidos`,
  };
  if (onProgress) onProgress(result);
  return result;
}

// ─────────────────────────────────────────────────────────────────────────────
// syncReportes
// ─────────────────────────────────────────────────────────────────────────────
export async function syncReportes(onProgress) {
  const state = await NetInfo.fetch();
  if (!state.isConnected) return { success: 0, failed: 0 };

  const unsynced = getUnsyncedReportes();
  if (unsynced.length === 0) return { success: 0, failed: 0 };

  let successCount = 0;
  let failCount = 0;

  for (const reporte of unsynced) {
    try {
      let localUris = [];
      try { localUris = JSON.parse(reporte.archivos_adjuntos || '[]'); } catch { localUris = []; }

      const uploadedUrls = [];
      for (let i = 0; i < localUris.length; i++) {
        const uri = localUris[i];
        if (uri && (uri.startsWith('file://') || uri.startsWith('content://'))) {
          const storagePath = `bitacora/${reporte.jefe_obra_id}/${reporte.id}_${i}.jpg`;
          const url = await uploadLocalPhoto(uri, 'accuratek-data', storagePath);
          uploadedUrls.push(url);
        } else {
          uploadedUrls.push(uri);
        }
      }

      const { error } = await supabase.from('reporte_obra').insert({
        id: reporte.id,
        obra_id: reporte.obra_id,
        jefe_obra_id: reporte.jefe_obra_id,
        tipo_reporte: reporte.tipo_reporte,
        mensaje: reporte.mensaje,
        archivos_adjuntos: uploadedUrls,
        fecha_publicacion: reporte.fecha_publicacion,
        estado_reb: 'pendiente',
      });
      if (error) throw new Error(error.message);

      const consumos = getReporteConsumos(reporte.id);
      if (consumos.length > 0) {
        const { error: consErr } = await supabase
          .from('reporte_obra_consumos')
          .insert(
            consumos.map((c) => ({
              id: c.id,
              reporte_obra_id: c.reporte_obra_id,
              material_id: c.material_id,
              material: c.material,
              cantidad: c.cantidad,
              unidad: c.unidad,
              fecha: c.fecha,
            }))
          );
        if (consErr) console.warn('[sync] consumos insert error:', consErr.message);
      }

      markReporteSynced(reporte.id);
      successCount++;
    } catch (err) {
      console.error(`[sync] reporte ${reporte.id} failed:`, err.message);
      failCount++;
    }
  }

  const result = {
    status: 'complete',
    success: successCount,
    failed: failCount,
    message: `Reportes: ${successCount} ok, ${failCount} fallidos`,
  };
  if (onProgress) onProgress(result);
  return result;
}

// ─────────────────────────────────────────────────────────────────────────────
// startBackgroundSync
// ─────────────────────────────────────────────────────────────────────────────
export function startBackgroundSync(onResult) {
  const SYNC_INTERVAL_MS = 60_000;

  let cancelled = false;

  async function runSync() {
    if (cancelled) return;
    try {
      const state = await NetInfo.fetch();
      if (!state.isConnected) return;

      let totalSuccess = 0;
      let totalFailed = 0;

      const avRes = await syncAvances();
      totalSuccess += avRes.success;
      totalFailed += avRes.failed;

      const asRes = await syncAsistencias();
      totalSuccess += asRes.success;
      totalFailed += asRes.failed;

      const repRes = await syncReportes();
      totalSuccess += repRes.success;
      totalFailed += repRes.failed;

      if (onResult && totalSuccess + totalFailed > 0) {
        onResult({
          status: 'complete',
          success: totalSuccess,
          failed: totalFailed,
          message: `Auto-sync: ${totalSuccess} enviados, ${totalFailed} fallidos`,
        });
      }
    } catch (err) {
      console.warn('[bgSync] error:', err.message);
    }
  }

  const intervalId = setInterval(runSync, SYNC_INTERVAL_MS);

  return () => {
    cancelled = true;
    clearInterval(intervalId);
  };
}
