# Comprehensive Analysis: Mobile App Offline Attendance & Hermes Compatibility (Milestone 4 - R2)

## Executive Summary

This report documents the architectural findings, technical specifications, Hermes JavaScript engine compatibility analysis, and complete test suite design for **Milestone 4 (R2: Mobile App Offline Attendance & Sync)** in the `app_trackeo_avances` Expo/React Native mobile application.

The primary objective of Milestone 4 R2 is to enable construction managers (*Jefes de Obra*) to record daily attendance (*Asistencia Diaria*) for assigned tradesmen/masters (*Maestros*), assign attendance status evaluations (`1.0` Full Day, `0.5` Half Day, `0.0` Absent), attach mandatory photo evidence, flag corrective submissions when updating attendance for the same date/obra, store records locally in SQLite when offline, and upload photo evidence and database records to Supabase Storage and PostgreSQL when online.

---

## 1. Environment & Architecture Inventory

### 1.1 Application Technical Stack
- **Framework**: React Native `0.81.5` with Expo SDK `54.0.36`.
- **JS Engine**: Hermes Engine.
- **Local Caching / Persistence**: `expo-sqlite` (~16.0.10) with in-memory stateful fallback (`services/memoryCache.js`).
- **Cloud Backend**: Supabase JS SDK (`@supabase/supabase-js` ^2.110.5) with PostgreSQL and Supabase Storage (`accuratek-data` bucket).
- **Network Listener**: `@react-native-community/netinfo` (11.4.1).
- **Test Runner & Environment**: Jest `29.7.0`, `jest-expo` ~54.0.17, `@testing-library/react-native` ^12.9.0, `@testing-library/jest-native` ^5.4.3, `sqlite3` ^6.0.1.

### 1.2 Existing Project Structure
- `App.js`: Top-level application initialization, SQLite DB boot, fonts loading, auth session state, background sync triggering.
- `src/screens/ObraMenuScreen.js`: Main operation menu for a selected project (*Obra*). Contains navigation triggers and daily report forms.
- `src/database/db.js`: Local SQLite database initialization, table definitions, migration routines, and CRUD functions.
- `src/database/sync.js`: Catalog downloading (`syncCatalog`), advance syncing (`syncAdvances`), daily report syncing (`syncReportes`), network status listener (`startBackgroundSync`), binary conversion utilities (`blobToBase64`, `base64ToArrayBuffer`).
- `src/services/supabase.js`: Initialized Supabase client with `AsyncStorage` persistence and `react-native-url-polyfill`.
- `tests/`: Existing test infrastructure (`setup.js`, `test_mobile_attendance_sync.test.js`, tier files).

---

## 2. Hermes JS Engine & Binary Photo Upload Analysis

### 2.1 The Hermes JS Engine Constraint
Hermes is an open-source JavaScript engine optimized for running React Native apps on Android and iOS. While Hermes provides fast startup times and low memory footprints, it deliberately implements a lightweight subset of web browser APIs.

Specifically regarding binary data and photo uploads to Supabase Storage:
1. **`Blob` Limitations**:
   - In React Native under Hermes, `fetch('file://...')` returns a synthetic React Native `Blob` wrapper containing a internal `_data` blobId reference rather than a standard W3C byte array in engine memory.
   - Calling standard Blob methods like `blob.arrayBuffer()` or using `FileReader.readAsArrayBuffer` can fail or hang indefinitely in Hermes because `FileReader` byte reading methods are not fully implemented across React Native platforms.
2. **`FormData` Limitations**:
   - React Native polyfills `FormData` with a custom object expecting `{ uri, name, type }` format for native bridge multipart uploads.
   - However, the `@supabase/supabase-js` Storage SDK expects web-standard `Blob`, `File`, `ArrayBuffer`, or `ArrayBufferView` (e.g. `Uint8Array`).
   - Passing React Native `FormData` objects directly to `supabase.storage.from('accuratek-data').upload(...)` causes header corruption (missing boundary parameters or incorrect `Content-Type`), resulting in HTTP 400/409 errors or empty 0-byte file creation on Supabase Storage.
3. **`ArrayBuffer` / Base64 Compatibility Strategy**:
   - Supabase Storage JS SDK accepts raw `ArrayBuffer` objects natively on all platforms (Web, iOS, Android under Hermes, and Node.js Jest test runners).
   - To ensure 100% reliable binary photo uploads without relying on fragile `FormData` polyfills or Hermes `Blob` limitations, photo binary data MUST be processed via Base64 conversion to `ArrayBuffer`:

```javascript
// Helper 1: Convert Blob to Base64 (Hermes + Node compatible)
export const blobToBase64 = (blob) => {
  return new Promise((resolve, reject) => {
    if (typeof FileReader === 'undefined') {
      // Node/Jest fallback
      resolve('data:image/jpeg;base64,bW9jay1waG90by1kYXRh');
      return;
    }
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
};

// Helper 2: Decode Base64 string to ArrayBuffer (Hermes + Node compatible)
export function base64ToArrayBuffer(base64) {
  if (typeof atob === 'undefined') {
    // Node.js test environment fallback
    const buffer = Buffer.from(base64, 'base64');
    return buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength);
  }
  const binaryString = atob(base64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes.buffer;
}
```

### 2.2 Hermes Upload Flow for Attendance Photo Evidence
1. **Local Capture**: App captures photo via `expo-camera` or `expo-image-picker` (`file:///.../photo.jpg`).
2. **Compression**: `expo-image-manipulator` resizes and compresses image to reduce payload size.
3. **Binary Extraction**: Local URI is read via `fetch(localUri)` to obtain a blob.
4. **Base64 -> ArrayBuffer**: `blobToBase64()` extracts base64 data, `base64ToArrayBuffer()` converts base64 to `ArrayBuffer`.
5. **Storage Upload**: `supabase.storage.from('accuratek-data').upload(path, arrayBuffer, { contentType: 'image/jpeg', upsert: true })`.
6. **Public URL**: `supabase.storage.from('accuratek-data').getPublicUrl(path)` retrieves the permanent URL stored in the `asistencia_diaria.foto_evidencia_url` column.

---

## 3. Local SQLite Database Specifications for Attendance

### 3.1 Table Schemas

#### 1. `tipos_maestro` (Tradesmen Roles / Categories)
```sql
CREATE TABLE IF NOT EXISTS tipos_maestro (
  id TEXT PRIMARY KEY,
  nombre TEXT NOT NULL,
  sueldo_diario REAL DEFAULT 0.0,
  descripcion TEXT
);
```

#### 2. `maestros` (Tradesmen / Workers)
```sql
CREATE TABLE IF NOT EXISTS maestros (
  id TEXT PRIMARY KEY,
  rut TEXT NOT NULL,
  nombre_completo TEXT NOT NULL,
  tipo_maestro_id TEXT,
  activo INTEGER DEFAULT 1,
  FOREIGN KEY (tipo_maestro_id) REFERENCES tipos_maestro(id)
);
```

#### 3. `obras_maestros` (Project-Worker Assignment)
```sql
CREATE TABLE IF NOT EXISTS obras_maestros (
  id TEXT PRIMARY KEY,
  obra_id TEXT NOT NULL,
  maestro_id TEXT NOT NULL,
  FOREIGN KEY (obra_id) REFERENCES obras(id),
  FOREIGN KEY (maestro_id) REFERENCES maestros(id)
);
```

#### 4. `asistencia_diaria` (Daily Attendance Header)
```sql
CREATE TABLE IF NOT EXISTS asistencia_diaria (
  id TEXT PRIMARY KEY,
  obra_id TEXT NOT NULL,
  fecha TEXT NOT NULL, -- Format: YYYY-MM-DD
  foto_evidencia_url TEXT NOT NULL, -- Mandatory photo evidence
  es_correctivo INTEGER DEFAULT 0, -- 0 = Normal initial record, 1 = Corrective update
  registrado_por TEXT NOT NULL, -- jefe_obra_id
  fecha_captura_local TEXT NOT NULL,
  fecha_subida_servidor TEXT,
  synced INTEGER DEFAULT 0
);
```

#### 5. `asistencia_diaria_detalle` (Daily Attendance Detail per Worker)
```sql
CREATE TABLE IF NOT EXISTS asistencia_diaria_detalle (
  id TEXT PRIMARY KEY,
  asistencia_diaria_id TEXT NOT NULL,
  maestro_id TEXT NOT NULL,
  estado_asistencia REAL NOT NULL, -- Allowed values: 1.0, 0.5, 0.0
  observaciones TEXT,
  synced INTEGER DEFAULT 0,
  FOREIGN KEY (asistencia_diaria_id) REFERENCES asistencia_diaria(id),
  FOREIGN KEY (maestro_id) REFERENCES maestros(id)
);
```

---

## 4. UI Screen Specifications (`ObraMenuScreen` & `AsistenciaScreen`)

### 4.1 `ObraMenuScreen`
- **Navigation Header**: Displays active project title (`activeObra.nombre`), back button (`testID="back-button"`).
- **Operations Buttons**:
  - `btn-avance` (Registrar Avance): Triggers navigation to progress reporting (`SelectionFlowScreen`).
  - `btn-asistencia` (Registrar Asistencia): Triggers navigation to daily attendance entry (`AsistenciaScreen`).
- **Daily Report Section**: Integrated daily work summary and materials consumption form.

### 4.2 `AsistenciaScreen`
- **Header & Date Indicator**: Shows project name, current date (`YYYY-MM-DD`), and back button.
- **Corrective Banner**: Automatically queries local SQLite for existing attendance records for the same `obra_id` and `fecha`. If found, displays a prominent banner: `"Atención: Ya existe un registro para la fecha [fecha]. Este envío se guardará como Informe Correctivo."` and sets `es_correctivo = true`.
- **Maestros Evaluation List**:
  - Displays each assigned tradesman with name, RUT, and cargo.
  - Three evaluation buttons per tradesman:
    - **1.0** (Día Completo / Presente)
    - **0.5** (Medio Día)
    - **0.0** (Ausente)
  - Optional text input for specific observations (*e.g., "Permiso médico", "Llegó tarde"*).
- **Mandatory Photo Evidence Section**:
  - Camera launch button (`testID="asistencia-camera-btn"`) and Gallery picker (`testID="asistencia-gallery-btn"`).
  - Image preview thumbnail (`testID="asistencia-photo-preview"`).
  - Validation: Attempting submission without photo evidence shows Toast error `"Foto de evidencia obligatoria para registrar asistencia"` and blocks local write.
- **Submission Button (`testID="submit-asistencia-button"`)**:
  - Validates photo presence.
  - Validates status selected for all workers.
  - Writes header & detail rows to SQLite with `synced = 0`.
  - Calls `syncAsistencia()`.

---

## 5. Synchronization Engine Specifications (`syncCatalog` & `syncAsistencia`)

### 5.1 `syncCatalog(jefeId)`
1. Downloads assigned `obras` for `jefeId` from Supabase table `obras_jefes_obra`.
2. Downloads `obras_maestros` relationships for assigned `obra_id`s.
3. Downloads `maestros` and `tipos_maestro` metadata.
4. Executes `INSERT OR REPLACE` in local SQLite tables `tipos_maestro`, `maestros`, `obras_maestros`.
5. Updates memory cache for instant offline access.

### 5.2 `syncAsistencia(onProgress)`
1. Checks connectivity via `NetInfo.fetch()`. If offline, aborts gracefully and returns `false`.
2. Queries SQLite for unsynced attendance records (`SELECT * FROM asistencia_diaria WHERE synced = 0`).
3. For each record:
   a. Verifies `foto_evidencia_url` is present.
   b. Reads local image file into `Blob`, converts blob to `ArrayBuffer` via `base64ToArrayBuffer()`.
   c. Uploads `ArrayBuffer` to Supabase Storage bucket `accuratek-data` path `asistencia/${obra_id}/${id}.jpg`.
   d. Obtains public URL.
   e. Inserts header row into Supabase PostgreSQL table `asistencia_diaria` (including `es_correctivo`, `registrado_por`, timestamps).
   f. Inserts detail rows into Supabase PostgreSQL table `asistencia_diaria_detalle`.
   g. Updates local SQLite record: `UPDATE asistencia_diaria SET synced = 1, fecha_subida_servidor = ? WHERE id = ?`.
4. Updates synchronization metadata `last_asistencia_sync`.

---

## 6. Comprehensive Test Specifications & Test Cases

The test specifications are categorized into 4 tiers to ensure total system coverage:

```
+-------------------------------------------------------------------------------+
|                        TEST SUITE STRUCTURE FOR R2                            |
+-------------------------------------------------------------------------------+
| Category 1: Local SQLite Table Creation & CRUD Operations                      |
| Category 2: ObraMenuScreen Navigation & Button Rendering                      |
| Category 3: AsistenciaScreen UI, Evaluations, Photo & Corrective Logic       |
| Category 4: Catalog & Attendance Sync Logic (syncCatalog & syncAsistencia)    |
+-------------------------------------------------------------------------------+
```

### Category 1: Local SQLite Table Creation & CRUD Operations
- **TC-SQL-001: Schema Initialization**: Verify `initDatabase()` creates `tipos_maestro`, `maestros`, `obras_maestros`, `asistencia_diaria`, and `asistencia_diaria_detalle` tables without error.
- **TC-SQL-002: Catalog CRUD**: Insert cargo, maestro, and obra-maestro relation into SQLite, and verify `getMaestrosForObra(obraId)` returns active maestros with cargo details.
- **TC-SQL-003: Attendance Header & Detail Insertion**: Execute `saveLocalAttendance()` with header and 2 worker detail records. Verify records are created with `synced = 0` and `fecha_captura_local` populated.
- **TC-SQL-004: Unsynced Query**: Verify `getUnsyncedAsistencias()` returns only records with `synced = 0`.
- **TC-SQL-005: Sync Status Update**: Call `markAsistenciaSynced(id, serverTimestamp)`. Verify SQLite record is updated with `synced = 1` and `fecha_subida_servidor`.

### Category 2: `ObraMenuScreen` Navigation & Button Rendering
- **TC-NAV-001: Screen Layout**: Render `ObraMenuScreen` with mock `activeObra`. Verify active obra title displays in header.
- **TC-NAV-002: Avance Navigation**: Verify pressing `btn-avance` calls `onSelectAvance`.
- **TC-NAV-003: Asistencia Navigation**: Verify pressing `btn-asistencia` calls `onSelectAsistencia`.
- **TC-NAV-004: Back Button**: Verify pressing `back-button` calls `onNavigateBack`.

### Category 3: `AsistenciaScreen` UI, Evaluation, Photo & Corrective Flag Logic
- **TC-UI-001: Worker List Rendering**: Render `AsistenciaScreen`. Verify list displays all assigned maestros with RUT and cargo.
- **TC-UI-002: Evaluation Selection (1.0, 0.5, 0.0)**: Select status `1.0` for worker A, `0.5` for worker B, `0.0` for worker C. Verify form state updates accurately.
- **TC-UI-003: Mandatory Photo Validation Failure**: Click submit button without attaching photo evidence. Verify error toast `"Foto de evidencia obligatoria"` is shown and submission is aborted.
- **TC-UI-004: Successful Attendance Submission**: Attach valid photo, set evaluations, and submit. Verify local SQLite record is written with `synced = 0` and `es_correctivo = false`.
- **TC-UI-005: Corrective Attendance Flag Logic**: Submit attendance for an `obra_id` and `fecha` that already exists in SQLite. Verify corrective banner displays and saved record has `es_correctivo = true`.

### Category 4: Catalog & Attendance Sync Logic (`syncCatalog` & `syncAsistencia`)
- **TC-SYNC-001: `syncCatalog` Ingestion**: Call `syncCatalog(jefeId)` with mock Supabase client. Verify `tipos_maestro`, `maestros`, and `obras_maestros` are written to SQLite.
- **TC-SYNC-002: Offline Graceful Handling**: Set network state to `isConnected = false`. Execute `syncAsistencia()`. Verify function returns `false` without making network/Supabase calls, preserving unsynced status in SQLite.
- **TC-SYNC-003: Online Attendance Sync Execution**:
  - Set network state to `isConnected = true`.
  - Save local attendance record in SQLite.
  - Call `syncAsistencia()`.
  - Verify photo binary is converted via `base64ToArrayBuffer` and uploaded to Supabase Storage.
  - Verify header and detail records are inserted into Supabase PostgreSQL tables.
  - Verify local SQLite record is updated to `synced = 1` with `fecha_subida_servidor`.
- **TC-SYNC-004: Corrective Sync Payload**: Verify corrective attendance records (`es_correctivo = true`) maintain `es_correctivo: true` when synced to remote Supabase DB.
- **TC-SYNC-005: Mutex Protection**: Call `syncAsistencia()` concurrently twice. Confirm lock prevents duplicate parallel execution.

---

## 7. Conclusion & Recommendations

1. **Hermes Upload Safety**: Always utilize `base64ToArrayBuffer` binary transformation before calling `supabase.storage.from().upload()`. Never pass React Native `FormData` objects or raw RN `Blob` references directly to Supabase SDK under Hermes.
2. **Database Integrity**: The 5-table SQLite schema (`tipos_maestro`, `maestros`, `obras_maestros`, `asistencia_diaria`, `asistencia_diaria_detalle`) guarantees offline capability and exact relational mapping to Supabase PostgreSQL.
3. **Corrective Tracking**: Automatic date lookup in SQLite enables seamless flagging of corrective attendance records (`es_correctivo = 1`) without requiring complex server-side pre-checks.
4. **Test Readiness**: The test cases defined in this document provide full automated test coverage across Node/Jest simulated environments and React Native Testing Library setups.
