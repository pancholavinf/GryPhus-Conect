# Scope: Milestone 4 - Mobile App Offline Attendance & Sync (R2)

## Architecture & Requirements
This milestone delivers offline attendance tracking and sync capabilities for `app_trackeo_avances`.

### Key Components to Update / Create:
1. **SQLite Database Schema (`src/database/db.js`)**:
   - Create local SQLite tables if not existing:
     - `tipos_maestro`
     - `maestros`
     - `obras_maestros`
     - `asistencia_diaria`
     - `asistencia_diaria_detalle`
2. **Navigation / UI (`src/screens/ObraMenuScreen.js`)**:
   - Add 'Asistencia de Personal' operational button leading to `AsistenciaScreen.js`.
3. **Attendance Screen (`src/screens/AsistenciaScreen.js`)**:
   - Display list of assigned maestros for the selected obra (queried from `obras_maestros` joined with `maestros`).
   - Allow selecting attendance evaluation status per maestro:
     - `1.0` (Día Completo)
     - `0.5` (Medio Día)
     - `0.0` (Ausente)
   - Require mandatory photo evidence capture before submission using `expo-camera` or `expo-image-picker`.
   - Support 'Reporte Correctivo de Asistencia' if attendance for the current date was already registered (`es_correctivo = true`).
   - Save attendance records locally to SQLite (`asistencia_diaria`, `asistencia_diaria_detalle`) with sync status `pending`.
4. **Sync Mechanism (`src/database/sync.js`)**:
   - `syncCatalog()`: pulls catalog tables (`tipos_maestro`, `maestros`, `obras_maestros`) from Supabase and upserts/replaces into local SQLite tables.
   - `syncAsistencia()`: pushes unsynced local attendance records (`asistencia_diaria`, `asistencia_diaria_detalle`) and photo evidence to Supabase.
   - Photo upload pipeline must use Hermes-compatible ArrayBuffer upload for Supabase Storage.

## Sub-Milestone Execution Matrix
| # | Work Item | Status | Key Targets |
|---|-----------|--------|-------------|
| R2-1 | SQLite Schema Update | PLANNED | `src/database/db.js` |
| R2-2 | ObraMenu Navigation | PLANNED | `src/screens/ObraMenuScreen.js` |
| R2-3 | AsistenciaScreen UI & Logic | PLANNED | `src/screens/AsistenciaScreen.js` |
| R2-4 | Sync Catalog & Attendance | PLANNED | `src/database/sync.js` |
| R2-5 | Verification & Testing | PLANNED | Unit & Integration tests |

## Verification Criteria
- Local SQLite tables correctly created with appropriate schemas.
- Navigation button opens `AsistenciaScreen.js`.
- Assigned maestros listed with evaluation state controls (1.0, 0.5, 0.0).
- Photo capture required before saving.
- Corrective attendance flag (`es_correctivo = true`) handled when re-submitting for today.
- `syncCatalog()` successfully populates local SQLite from Supabase.
- `syncAsistencia()` pushes records and photo ArrayBuffers to Supabase Storage and database.
- Unit and integration tests pass without regression.
- Forensic Integrity Audit passes with CLEAN verdict.
