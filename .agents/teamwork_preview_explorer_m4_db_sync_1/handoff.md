# Handoff Report: Milestone 4 (R2) Mobile App Offline Attendance & Sync Analysis

**Role**: Explorer 1 (Milestone 4: Mobile App Offline Attendance & Sync)  
**Target Path**: `C:\Users\fcola\Desktop\APPACCURATEK\.agents\teamwork_preview_explorer_m4_db_sync_1`  
**Handoff Type**: Hard (Task Complete)  
**Date**: 2026-07-29  

---

## 1. Observation

1. **Remote Supabase DDL Specification (`.agents/worker_m1_1/schema_r1.sql`)**:
   - `tipos_maestro`: `id uuid PRIMARY KEY`, `nombre text NOT NULL`, `sueldo_diario numeric NOT NULL`, `created_at timestamptz`.
   - `maestros`: `id uuid PRIMARY KEY`, `rut text UNIQUE NOT NULL`, `nombre_completo text NOT NULL`, `tipo_maestro_id uuid REFERENCES public.tipos_maestro(id) ON DELETE RESTRICT`, `telefono text`, `activo boolean NOT NULL DEFAULT true`, `created_at timestamptz`.
   - `obras_maestros`: `id uuid PRIMARY KEY`, `obra_id uuid REFERENCES public.obras(id) ON DELETE CASCADE`, `maestro_id uuid REFERENCES public.maestros(id) ON DELETE CASCADE`, `CONSTRAINT uq_obras_maestros UNIQUE (obra_id, maestro_id)`.
   - `asistencia_diaria`: `id uuid PRIMARY KEY`, `obra_id uuid REFERENCES public.obras(id) ON DELETE CASCADE`, `fecha date NOT NULL`, `foto_evidencia_url text`, `es_correctivo boolean NOT NULL DEFAULT false`, `registrado_por uuid REFERENCES public.perfiles_usuario(id)`.
   - `asistencia_diaria_detalle`: `id uuid PRIMARY KEY`, `asistencia_diaria_id uuid REFERENCES public.asistencia_diaria(id) ON DELETE CASCADE`, `maestro_id uuid REFERENCES public.maestros(id) ON DELETE RESTRICT`, `estado_asistencia numeric(3,1) NOT NULL CHECK (estado_asistencia IN (1.0, 0.5, 0.0))`, `observaciones text`, `CONSTRAINT uq_asistencia_diaria_detalle UNIQUE (asistencia_diaria_id, maestro_id)`.

2. **Existing Mobile Database Setup (`app_trackeo_avances/src/database/db.js`)**:
   - Uses `expo-sqlite` via `SQLite.openDatabaseSync('trackeo.db')`.
   - Contains DDL for `perfiles_usuario`, `obras`, `obras_jefes_obra`, `items_obra`, `avances`, `materiales`, `reporte_obra`, `reporte_obra_consumos`, `sync_meta`.
   - Uses safe ALTER TABLE migration array inside `initDatabase()` to preserve existing local databases.
   - Sync tracking relies on `synced INTEGER DEFAULT 0` column per transactional table.

3. **Existing Mobile Sync Logic (`app_trackeo_avances/src/database/sync.js`)**:
   - Uses `@react-native-community/netinfo` for connection detection.
   - Converts local blobs via `blobToBase64()` and `base64ToArrayBuffer()` to produce Hermes-engine compatible `ArrayBuffer` payloads for `supabase.storage.from('accuratek-data').upload()`.
   - `syncCatalog(jefeId)` queries assigned obras (`obras_jefes_obra`) and updates local SQLite and `memoryCache.js`.
   - Transaction push routines (`syncAdvances`, `syncReportes`) upload photo assets to Supabase Storage before executing Supabase table inserts and marking local records with `synced = 1` and server timestamps (`fecha_subida_servidor`).

---

## 2. Logic Chain

1. **Primary Key Alignment**: Since Supabase uses UUID primary keys, the mobile client app must generate UUIDs locally (using standard UUID generators like `crypto.randomUUID()`) when creating attendance headers and details offline. This eliminates ID collisions upon syncing.
2. **Schema Alignment**: SQLite schema for attendance tables (`tipos_maestro`, `maestros`, `obras_maestros`, `asistencia_diaria`, `asistencia_diaria_detalle`) must match remote column types while introducing `synced INTEGER DEFAULT 0` and timestamp tracking (`fecha_subida_servidor`) for offline queue management.
3. **Catalog Download Strategy (`syncCatalog`)**:
   - To keep local storage efficient and respect data boundaries, `syncCatalog()` must only pull `maestros` and `obras_maestros` relevant to the assigned obras of the logged-in Jefe de Obra (`obra_id IN (assigned_obras)`).
   - Global reference table `tipos_maestro` can be fetched in full.
4. **Attendance Push Strategy (`syncAsistencia`)**:
   - Attendance submission contains header (`asistencia_diaria`) with mandatory/optional photo evidence, and 1-to-N details (`asistencia_diaria_detalle`).
   - Photos must be processed via `blobToBase64()` and `base64ToArrayBuffer()` to ensure compatibility across Hermes/React Native platforms, stored in Supabase Storage bucket `accuratek-data` under path `asistencia/<jefe_id>/<asistencia_id>.jpg`.
   - Upon successful photo upload, header is inserted into `asistencia_diaria`, followed by batch detail insertion into `asistencia_diaria_detalle`.
   - Once confirmed by Supabase, local rows are updated to `synced = 1`.

---

## 3. Caveats

- **Network Instability Mid-Transaction**: If photo upload succeeds but DB insert fails due to network drop, retry logic must handle upserting/checking existing storage files to prevent redundant uploads.
- **Expo Web Platform**: In web preview/testing, native `expo-sqlite` falls back to `memoryCache.js`. Complete implementation must maintain dual persistence calls (`memoryCache` + `database.runSync`).

---

## 4. Conclusion

The SQLite database setup and Supabase sync architecture for Milestone 4 (R2) are fully formulated and documented in `analysis.md`. 
The design provides 100% alignment with Supabase R1 schema (`schema_r1.sql`), seamless Hermes `ArrayBuffer` photo upload integration, complete offline state tracking (`synced`, local vs remote URLs), and dual-layer persistence (SQLite + `memoryCache.js`).

---

## 5. Verification Method

1. **Schema & Code Inspection**:
   - Inspect `C:\Users\fcola\Desktop\APPACCURATEK\.agents\teamwork_preview_explorer_m4_db_sync_1\analysis.md` for complete DDL, `syncCatalog()`, `syncAsistencia()`, and helper function specifications.
2. **Existing Implementation Alignment Verification**:
   - Compare proposed functions against `app_trackeo_avances/src/database/db.js` and `app_trackeo_avances/src/database/sync.js`.
3. **Supabase Schema Consistency**:
   - Verify column names and constraints against `.agents/worker_m1_1/schema_r1.sql`.
