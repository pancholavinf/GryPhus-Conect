## 2026-07-29T23:40:46Z
You are the Implementation Worker for Milestone 4 (R2: Mobile App Offline Attendance & Sync).
Your working directory is C:\Users\fcola\Desktop\APPACCURATEK\.agents\teamwork_preview_worker_m4_impl_1.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your task:
1. Create your working directory and briefing/progress files.
2. Read the detailed specifications and strategy reports from the 3 Explorers:
   - `C:\Users\fcola\Desktop\APPACCURATEK\.agents\teamwork_preview_explorer_m4_db_sync_1\handoff.md` (and `analysis.md`)
   - `C:\Users\fcola\Desktop\APPACCURATEK\.agents\teamwork_preview_explorer_m4_ui_photo_2\handoff.md` (and `analysis.md`)
   - `C:\Users\fcola\Desktop\APPACCURATEK\.agents\teamwork_preview_explorer_m4_tests_hermes_3\handoff.md` (and `analysis.md`)

3. Implement R2 features in `app_trackeo_avances`:
   a. Update SQLite setup in `src/database/db.js`:
      - Add table DDLs in `initDatabase()` for `tipos_maestro`, `maestros`, `obras_maestros`, `asistencia_diaria`, `asistencia_diaria_detalle`.
      - Implement helper functions: `getMaestrosForObra`, `checkAttendanceExistsToday`, `saveLocalAttendance`, `getPendingAsistencias`, `markAsistenciaSynced`, and sync with `memoryCache.js`.
   b. Navigation and UI:
      - Register `AsistenciaFlow` screen in `App.js`.
      - Add 'Asistencia de Personal' operational button (`testID="btn-asistencia"`) in `src/screens/ObraMenuScreen.js` navigating to `AsistenciaScreen.js`.
   c. Create `src/screens/AsistenciaScreen.js`:
      - Display assigned maestros for selected obra.
      - Segmented controls for status evaluation: `1.0` (Día Completo), `0.5` (Medio Día), `0.0` (Ausente).
      - Mandatory photo evidence capture using `expo-camera` / `expo-image-picker` with compression. Validate photo presence before submission ("Foto de evidencia obligatoria").
      - Corrective attendance detection for existing date records: display warning banner "⚠️ REPORTE CORRECTIVO DE ASISTENCIA" and set `es_correctivo = true`.
      - Save header and details to local SQLite (`synced = 0`) and trigger background sync.
   d. Update `src/database/sync.js`:
      - `syncCatalog(jefeId)`: pull catalog tables from Supabase into SQLite and memoryCache.
      - `syncAsistencia()`: push unsynced attendance records and convert photos via `blobToBase64()` + `base64ToArrayBuffer()` ArrayBuffer pipeline for Supabase Storage uploads. Insert into Supabase `asistencia_diaria` and `asistencia_diaria_detalle`, then update local SQLite to `synced = 1`.

4. Run build and test commands (e.g. `npm test` or `npm run test:e2e` in `app_trackeo_avances`). Verify all tests pass and document full execution output.
5. Write `handoff.md` in your working directory and notify parent with the path to your handoff report and test results.
