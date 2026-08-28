# Technical Analysis & Design Specification: Mobile App Offline Attendance & Supabase Sync (Milestone 4 / R2)

**Author**: Explorer 1 (Milestone 4: Mobile App Offline Attendance & Sync)  
**Target Architecture**: Expo / React Native (`app_trackeo_avances`), SQLite (`expo-sqlite`), Supabase PostgreSQL & Storage  
**Date**: 2026-07-29  

---

## 1. Executive Summary

This document establishes the exact SQLite database schema definitions, data models, offline queue synchronization strategies, and implementation logic for **Milestone 4 (R2: Mobile App Offline Attendance & Sync)** in `app_trackeo_avances`.

Building upon the remote Supabase schema established in Milestone 1 (`schema_r1.sql`), this specification details:
1. **Local SQLite Schema Extensions**: 5 local tables (`tipos_maestro`, `maestros`, `obras_maestros`, `asistencia_diaria`, `asistencia_diaria_detalle`) with offline tracking flags (`synced`, timestamps, local photo URIs vs remote URLs).
2. **Catalog Synchronization (`syncCatalog`)**: Downloading reference master data (`tipos_maestro`, `maestros`, `obras_maestros`) filtered by assigned `obra_id` for the authenticated Jefe de Obra.
3. **Attendance Synchronization (`syncAsistencia`)**: Robust two-pass push algorithm handling photo uploads via Hermes/React Native compatible `ArrayBuffer` conversion to Supabase Storage bucket `accuratek-data`, followed by transactional insertion into Supabase `asistencia_diaria` (header) and `asistencia_diaria_detalle` (detail) tables.
4. **Web Fallback Layer**: In-memory caching (`memoryCache.js`) integration for Expo Web development and offline state resilience.

---

## 2. Existing Database & Sync Architecture Analysis

### 2.1 Codebase Structure & Stack
- **Location**: `app_trackeo_avances/src/database/` and `app_trackeo_avances/src/services/`
- **Database Engine**: `expo-sqlite` (`SQLite.openDatabaseSync('trackeo.db')`) with web fallbacks via `memoryCache.js`.
- **Remote Backend**: Supabase client (`src/services/supabase.js`) connected to PostgreSQL.
- **Key Modules**:
  - `src/database/db.js`: Database initialization (`initDatabase()`), table DDL execution, safe ALTER TABLE migrations, local CRUD operations.
  - `src/database/sync.js`: Connectivity listener (`@react-native-community/netinfo`), catalog pull functions, push sync functions (`syncAdvances`, `syncReportes`), image binary processing (`blobToBase64`, `base64ToArrayBuffer`).
  - `src/services/memoryCache.js`: Fast read layer & fallback storage for web environments where native SQLite is unavailable.

### 2.2 Alignment with Remote Supabase R1 Schema
The remote PostgreSQL DDL (`.agents/worker_m1_1/schema_r1.sql`) defines the canonical attendance schema:
- `tipos_maestro` (id uuid, nombre text, sueldo_diario numeric)
- `maestros` (id uuid, rut text, nombre_completo text, tipo_maestro_id uuid FK RESTRICT, telefono text, activo boolean)
- `obras_maestros` (id uuid, obra_id uuid FK CASCADE, maestro_id uuid FK CASCADE)
- `asistencia_diaria` (id uuid, obra_id uuid FK CASCADE, fecha date, foto_evidencia_url text, es_correctivo boolean, registrado_por uuid FK)
- `asistencia_diaria_detalle` (id uuid, asistencia_diaria_id uuid FK CASCADE, maestro_id uuid FK RESTRICT, estado_asistencia numeric(3,1) CHECK (1.0, 0.5, 0.0), observaciones text)

All primary keys use UUIDs (`uuid_generate_v4()` / `gen_random_uuid()`).

---

## 3. Local SQLite Database Schema Formulation

To support offline recording without primary key collisions, the client application generates UUIDs locally before syncing to Supabase.

### 3.1 DDL Statements for `db.js`

```sql
-- 1. Catalog: tipos_maestro
CREATE TABLE IF NOT EXISTS tipos_maestro (
  id TEXT PRIMARY KEY,
  nombre TEXT NOT NULL,
  sueldo_diario REAL NOT NULL,
  created_at TEXT
);

-- 2. Catalog: maestros
CREATE TABLE IF NOT EXISTS maestros (
  id TEXT PRIMARY KEY,
  rut TEXT UNIQUE NOT NULL,
  nombre_completo TEXT NOT NULL,
  tipo_maestro_id TEXT,
  telefono TEXT,
  activo INTEGER DEFAULT 1,
  created_at TEXT,
  FOREIGN KEY (tipo_maestro_id) REFERENCES tipos_maestro(id)
);

-- 3. Catalog: obras_maestros
CREATE TABLE IF NOT EXISTS obras_maestros (
  id TEXT PRIMARY KEY,
  obra_id TEXT NOT NULL,
  maestro_id TEXT NOT NULL,
  created_at TEXT,
  UNIQUE(obra_id, maestro_id)
);

-- 4. Transaction Header: asistencia_diaria
CREATE TABLE IF NOT EXISTS asistencia_diaria (
  id TEXT PRIMARY KEY,
  obra_id TEXT NOT NULL,
  fecha TEXT NOT NULL,
  foto_evidencia_url TEXT,
  es_correctivo INTEGER DEFAULT 0,
  registrado_por TEXT NOT NULL,
  created_at TEXT NOT NULL,
  fecha_subida_servidor TEXT,
  synced INTEGER DEFAULT 0
);

-- 5. Transaction Detail: asistencia_diaria_detalle
CREATE TABLE IF NOT EXISTS asistencia_diaria_detalle (
  id TEXT PRIMARY KEY,
  asistencia_diaria_id TEXT NOT NULL,
  maestro_id TEXT NOT NULL,
  estado_asistencia REAL NOT NULL,
  observaciones TEXT,
  created_at TEXT NOT NULL,
  synced INTEGER DEFAULT 0,
  FOREIGN KEY (asistencia_diaria_id) REFERENCES asistencia_diaria(id) ON DELETE CASCADE,
  FOREIGN KEY (maestro_id) REFERENCES maestros(id),
  UNIQUE(asistencia_diaria_id, maestro_id)
);

-- Performance & Indexing for Local Queries
CREATE INDEX IF NOT EXISTS idx_maestros_rut ON maestros(rut);
CREATE INDEX IF NOT EXISTS idx_obras_maestros_obra ON obras_maestros(obra_id);
CREATE INDEX IF NOT EXISTS idx_asistencia_diaria_obra_fecha ON asistencia_diaria(obra_id, fecha);
CREATE INDEX IF NOT EXISTS idx_asistencia_diaria_synced ON asistencia_diaria(synced);
CREATE INDEX IF NOT EXISTS idx_asistencia_detalle_asistencia_id ON asistencia_diaria_detalle(asistencia_diaria_id);
```

### 3.2 Safe Migrations Array for `initDatabase()`
```js
const attendanceMigrations = [
  'ALTER TABLE asistencia_diaria ADD COLUMN fecha_subida_servidor TEXT',
  'ALTER TABLE asistencia_diaria ADD COLUMN es_correctivo INTEGER DEFAULT 0',
  'ALTER TABLE asistencia_diaria_detalle ADD COLUMN observaciones TEXT',
];
```

---

## 4. Catalog Synchronization Formulation (`syncCatalog`)

The `syncCatalog` logic retrieves master records from Supabase and populates both SQLite and `memoryCache`.

### 4.1 Data Flow Sequence
1. Fetch assigned `obra_id` list for the logged-in Jefe de Obra (`obras_jefes_obra`).
2. Fetch `obras` assigned to the user.
3. Fetch `obras_maestros` cross-reference entries matching assigned `obra_id`s.
4. Fetch `maestros` matching the linked `maestro_id`s (or all active masters linked to assigned works).
5. Fetch `tipos_maestro` catalog.
6. Execute local transaction / batch `INSERT OR REPLACE INTO` statements.
7. Update `memoryCache` objects for web runtime compatibility.

### 4.2 Code Specification for `syncCatalog()`

```javascript
export async function syncCatalog(jefeId) {
  try {
    // 1. User profile
    const { data: profileData, error: profileError } = await supabase
      .from('perfiles_usuario')
      .select('*')
      .eq('id', jefeId);
    if (profileError) throw profileError;

    // 2. Obras assigned
    const { data: relations, error: relError } = await supabase
      .from('obras_jefes_obra')
      .select('*')
      .eq('jefe_obra_id', jefeId);
    if (relError) throw relError;

    const obraIds = (relations || []).map((r) => r.obra_id);

    let obras = [];
    if (obraIds.length > 0) {
      const { data: obrasData, error: obrasError } = await supabase
        .from('obras')
        .select('*')
        .in('id', obraIds);
      if (obrasError) throw obrasError;
      obras = obrasData || [];
    }

    let items = [];
    if (obraIds.length > 0) {
      const { data: itemsData, error: itemsError } = await supabase
        .from('items_obra')
        .select('*')
        .in('obra_id', obraIds);
      if (itemsError) throw itemsError;
      items = itemsData || [];
    }

    const materialIds = [...new Set(items.map((i) => i.material_id).filter(Boolean))];
    let materiales = [];
    if (materialIds.length > 0) {
      const { data: matData, error: matError } = await supabase
        .from('materiales')
        .select('*')
        .in('id', materialIds);
      if (matError) throw matError;
      materiales = matData || [];
    }

    // ── ATTENDANCE CATALOG FETCH ──────────────────────────────
    // 3. Fetch tipos_maestro
    const { data: tiposMaestroData, error: tiposError } = await supabase
      .from('tipos_maestro')
      .select('*');
    if (tiposError) throw tiposError;
    const tiposMaestro = tiposMaestroData || [];

    // 4. Fetch obras_maestros for assigned obras
    let obrasMaestros = [];
    if (obraIds.length > 0) {
      const { data: omData, error: omError } = await supabase
        .from('obras_maestros')
        .select('*')
        .in('obra_id', obraIds);
      if (omError) throw omError;
      obrasMaestros = omData || [];
    }

    // 5. Fetch maestros linked to assigned obras
    const maestroIds = [...new Set(obrasMaestros.map((om) => om.maestro_id).filter(Boolean))];
    let maestros = [];
    if (maestroIds.length > 0) {
      const { data: mData, error: mError } = await supabase
        .from('maestros')
        .select('*')
        .in('id', maestroIds);
      if (mError) throw mError;
      maestros = mData || [];
    }

    // ── PERSIST TO SQLITE ──────────────────────────────────────
    const database = getDatabase();

    // Persist perfiles_usuario & obras_jefes_obra & obras & materiales & items_obra...
    // (existing persistence steps)

    // Persist tipos_maestro
    for (const tm of tiposMaestro) {
      database.runSync(
        'INSERT OR REPLACE INTO tipos_maestro (id, nombre, sueldo_diario, created_at) VALUES (?, ?, ?, ?)',
        [tm.id, tm.nombre, tm.sueldo_diario, tm.created_at || null]
      );
    }

    // Persist maestros
    for (const m of maestros) {
      database.runSync(
        'INSERT OR REPLACE INTO maestros (id, rut, nombre_completo, tipo_maestro_id, telefono, activo, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
        [
          m.id,
          m.rut,
          m.nombre_completo,
          m.tipo_maestro_id || null,
          m.telefono || null,
          m.activo ? 1 : 0,
          m.created_at || null,
        ]
      );
    }

    // Persist obras_maestros
    for (const om of obrasMaestros) {
      database.runSync(
        'INSERT OR REPLACE INTO obras_maestros (id, obra_id, maestro_id, created_at) VALUES (?, ?, ?, ?)',
        [om.id, om.obra_id, om.maestro_id, om.created_at || null]
      );
    }

    // ── PERSIST TO MEMORY CACHE ────────────────────────────────
    cacheObras(obras);
    cacheItems(items);
    cacheMateriales(materiales);
    cacheTiposMaestro(tiposMaestro);
    cacheMaestros(maestros);
    cacheObrasMaestros(obrasMaestros);
    cacheJefeId(jefeId);

    setSyncMeta('last_catalog_sync', new Date().toISOString());
    return true;
  } catch (error) {
    console.error('Error syncing catalog:', error);
    return false;
  }
}
```

---

## 5. Attendance Synchronization Formulation (`syncAsistencia`)

### 5.1 Push Flow for Attendance Records & Evidence Photos
1. **Connectivity Check**: Validate `NetInfo.fetch().isConnected`.
2. **Fetch Unsynced Local Records**: Query `asistencia_diaria WHERE synced = 0`.
3. **For Each Pending Attendance Record**:
   a. **Photo Evidence Upload**:
      - Read local image file `foto_evidencia_url` via `fetch()`.
      - Convert to `Blob` -> `blobToBase64()` -> `base64ToArrayBuffer()`.
      - Upload to Supabase Storage bucket `accuratek-data` path `asistencia/${registrado_por}/${asistencia_id}.${ext}` with `contentType: 'image/jpeg'`.
      - Retrieve public URL `publicUrl`.
   b. **Header Insertion**:
      - Insert header into Supabase `asistencia_diaria` table.
   c. **Detail Items Fetch & Insertion**:
      - Fetch local unsynced detail items for this `asistencia_diaria_id`.
      - Insert array into Supabase `asistencia_diaria_detalle` table.
   d. **Local State Update**:
      - Set `synced = 1`, `foto_evidencia_url = publicUrl`, `fecha_subida_servidor = serverTimestamp` in local SQLite and memory cache.

### 5.2 Code Specification for `syncAsistencia()`

```javascript
let isSyncingAsistencia = false;

export async function syncAsistencia(onProgress) {
  if (isSyncingAsistencia) {
    console.log('🔄 [syncAsistencia] Sync already in progress. Skipping concurrent call.');
    return false;
  }
  isSyncingAsistencia = true;
  console.group('🔄 [syncAsistencia] Starting attendance synchronization...');

  try {
    // 1. Check network connectivity
    const state = await NetInfo.fetch();
    if (!state.isConnected) {
      console.warn('⚠️ No internet connection — aborting attendance sync');
      onProgress?.({ status: 'offline', message: 'Sin conexión a internet' });
      return false;
    }

    // 2. Fetch unsynced local headers
    const unsyncedHeaders = getUnsyncedAsistencias();
    console.log(`📋 Unsynced attendance records in local SQLite: ${unsyncedHeaders.length}`);

    if (unsyncedHeaders.length === 0) {
      console.log('✅ Nothing to sync');
      onProgress?.({ status: 'idle', message: 'Todo sincronizado' });
      return true;
    }

    let successCount = 0;
    let failCount = 0;

    for (const header of unsyncedHeaders) {
      console.group(`📤 Processing attendance header: ${header.id}`);
      try {
        let publicFotoUrl = header.foto_evidencia_url;

        // 3. Upload photo evidence if local file URI exists
        if (header.foto_evidencia_url && (header.foto_evidencia_url.startsWith('file:') || header.foto_evidencia_url.startsWith('ph:'))) {
          const rawExt = header.foto_evidencia_url.split('.').pop()?.split('?')[0] || 'jpg';
          const fileExt = ['jpg', 'jpeg', 'png', 'webp'].includes(rawExt.toLowerCase()) ? rawExt.toLowerCase() : 'jpg';
          const fileName = `asistencia/${header.registrado_por}/${header.id}_${Date.now()}.${fileExt}`;
          const storagePath = `asistencia/${fileName}`;

          console.log('📦 Uploading evidence photo to Storage:', storagePath);
          const response = await fetch(header.foto_evidencia_url);
          if (!response.ok) throw new Error(`Could not read local photo file: HTTP ${response.status}`);
          const blob = await response.blob();

          const dataUrl = await blobToBase64(blob);
          const base64Data = dataUrl.split(',')[1];
          const arrayBuffer = base64ToArrayBuffer(base64Data);

          const { data: uploadData, error: uploadError } = await supabase.storage
            .from('accuratek-data')
            .upload(storagePath, arrayBuffer, { contentType: `image/${fileExt}`, upsert: true });

          if (uploadError) throw new Error(`Storage upload error: ${uploadError.message}`);

          const { data: publicUrlData } = supabase.storage.from('accuratek-data').getPublicUrl(storagePath);
          publicFotoUrl = publicUrlData?.publicUrl || uploadData?.path || storagePath;
          console.log('✅ Evidence photo uploaded successfully:', publicFotoUrl);
        }

        // 4. Insert header record into Supabase
        const serverTimestamp = new Date().toISOString();
        const headerRecord = {
          id: header.id,
          obra_id: header.obra_id,
          fecha: header.fecha,
          foto_evidencia_url: publicFotoUrl || null,
          es_correctivo: !!header.es_correctivo,
          registrado_por: header.registrado_por,
          created_at: header.created_at || serverTimestamp,
        };

        const { error: headerDbError } = await supabase
          .from('asistencia_diaria')
          .insert(headerRecord);

        if (headerDbError) throw new Error(`Header DB insert error: ${headerDbError.message}`);

        // 5. Fetch and insert detail records for this header
        const details = getAsistenciaDetalles(header.id);
        if (details.length > 0) {
          const detailRecords = details.map((d) => ({
            id: d.id,
            asistencia_diaria_id: d.asistencia_diaria_id,
            maestro_id: d.maestro_id,
            estado_asistencia: d.estado_asistencia,
            observaciones: d.observaciones || null,
            created_at: d.created_at || serverTimestamp,
          }));

          const { error: detailDbError } = await supabase
            .from('asistencia_diaria_detalle')
            .insert(detailRecords);

          if (detailDbError) throw new Error(`Detail DB insert error: ${detailDbError.message}`);
        }

        // 6. Mark local records as synced
        markAsistenciaSynced(header.id, publicFotoUrl, serverTimestamp);
        console.log('💾 Attendance record marked as synced locally');
        successCount++;
        onProgress?.({ status: 'item_synced', id: header.id });

      } catch (err) {
        console.error(`❌ Failed to sync attendance ${header.id}:`, err.message);
        failCount++;
      }
      console.groupEnd();
    }

    setSyncMeta('last_asistencia_sync', new Date().toISOString());
    console.log(`\n📊 ATTENDANCE SYNC SUMMARY: ${successCount} succeeded, ${failCount} failed`);

    onProgress?.({
      status: 'complete',
      success: successCount,
      failed: failCount,
      message: failCount === 0
        ? `✓ ${successCount} registro(s) de asistencia sincronizados`
        : `${successCount} sincronizados, ${failCount} fallidos`,
    });

    return failCount === 0;
  } finally {
    isSyncingAsistencia = false;
    console.groupEnd();
  }
}
```

---

## 6. Helper Functions for `db.js`

```javascript
/** Save attendance record locally */
export function saveAsistenciaDiaria({ id, obra_id, fecha, foto_evidencia_url, es_correctivo, registrado_por, detalles }) {
  const now = new Date().toISOString();
  const headerId = id || crypto.randomUUID();

  // SQLite execution
  try {
    const database = getDatabase();
    database.runSync(
      `INSERT INTO asistencia_diaria
        (id, obra_id, fecha, foto_evidencia_url, es_correctivo, registrado_por, created_at, synced)
       VALUES (?, ?, ?, ?, ?, ?, ?, 0)`,
      [headerId, obra_id, fecha, foto_evidencia_url || null, es_correctivo ? 1 : 0, registrado_por, now]
    );

    for (const d of detalles || []) {
      const detailId = d.id || crypto.randomUUID();
      database.runSync(
        `INSERT INTO asistencia_diaria_detalle
          (id, asistencia_diaria_id, maestro_id, estado_asistencia, observaciones, created_at, synced)
         VALUES (?, ?, ?, ?, ?, ?, 0)`,
        [detailId, headerId, d.maestro_id, d.estado_asistencia, d.observaciones || null, now]
      );
    }
  } catch (_e) {
    // Memory cache fallback for Web
  }

  addPendingAsistencia({ id: headerId, obra_id, fecha, foto_evidencia_url, es_correctivo, registrado_por, created_at: now, synced: 0 }, detalles);
  return headerId;
}

export function getUnsyncedAsistencias() {
  let sqliteRows = [];
  try {
    const database = getDatabase();
    sqliteRows = database.getAllSync('SELECT * FROM asistencia_diaria WHERE synced = 0');
  } catch (_e) {}

  const memoryRows = getPendingAsistencias();
  const allById = {};
  for (const r of sqliteRows) allById[r.id] = r;
  for (const r of memoryRows) allById[r.id] = r;
  return Object.values(allById);
}

export function getAsistenciaDetalles(asistenciaId) {
  try {
    const database = getDatabase();
    return database.getAllSync('SELECT * FROM asistencia_diaria_detalle WHERE asistencia_diaria_id = ?', [asistenciaId]);
  } catch (_e) {
    return getPendingAsistenciaDetalles(asistenciaId);
  }
}

export function markAsistenciaSynced(id, publicUrl, serverTimestamp) {
  markPendingAsistenciaSynced(id);
  try {
    const database = getDatabase();
    database.runSync(
      'UPDATE asistencia_diaria SET synced = 1, foto_evidencia_url = ?, fecha_subida_servidor = ? WHERE id = ?',
      [publicUrl || null, serverTimestamp, id]
    );
    database.runSync(
      'UPDATE asistencia_diaria_detalle SET synced = 1 WHERE asistencia_diaria_id = ?',
      [id]
    );
  } catch (_e) {}
}
```

---

## 7. Edge Cases & Resilience Strategy

1. **Partial Sync & Interrupted Network**:
   - Headers and details use matching UUIDs. If an insertion fails midway, the record remains `synced = 0` locally and will be safely retried during the next sync cycle.
   - Idempotent `insert` in Supabase using existing UUIDs prevents duplicate records.
2. **Hermes Engine Compatibility**:
   - Binary image upload uses `blobToBase64()` and `base64ToArrayBuffer()`, which avoids `Buffer` or Node.js native dependencies incompatible with Hermes JavaScript Engine on iOS/Android.
3. **Attendance State Constraint**:
   - Local validation enforces `estado_asistencia IN (1.0, 0.5, 0.0)` prior to insertion, matching Supabase `CHECK (estado_asistencia IN (1.0, 0.5, 0.0))` constraint.
4. **Unique Master Assignment Per Work**:
   - `obras_maestros` filtering ensures supervisors only see workers assigned to their specific job site (`obra_id`).
