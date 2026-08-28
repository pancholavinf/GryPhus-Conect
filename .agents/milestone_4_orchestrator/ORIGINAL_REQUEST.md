# Original User Request

## Initial Request — 2026-07-29T19:39:02-04:00

You are the Sub-Orchestrator for Milestone 4: Mobile App (`app_trackeo_avances`) Offline Attendance & Sync.
Your scope:
Implement R2:
1. Update SQLite setup in `src/database/db.js` to create local tables for `tipos_maestro`, `maestros`, `obras_maestros`, `asistencia_diaria`, `asistencia_diaria_detalle`.
2. Add 'Asistencia de Personal' operational button in `src/screens/ObraMenuScreen.js` leading to `AsistenciaScreen.js`.
3. In `AsistenciaScreen.js`:
   - List assigned maestros for the current obra (`obras_maestros`).
   - Select evaluation status for each maestro: 1.0 (Día Completo), 0.5 (Medio Día), 0.0 (Ausente).
   - Require photo evidence capture (`expo-camera` / `expo-image-picker`) before submission.
   - Support 'Reporte Correctivo de Asistencia' if attendance for the current date has already been registered (`es_correctivo = true`).
4. Update `src/database/sync.js`:
   - `syncCatalog()` pulls `tipos_maestro`, `maestros`, `obras_maestros` from Supabase down to local SQLite tables.
   - `syncAsistencia()` pushes local pending attendance records and evidence photos (Hermes-compatible photo pipeline ArrayBuffer upload) to Supabase `asistencia_diaria` and `asistencia_diaria_detalle`.

Your working directory is `C:\Users\fcola\Desktop\APPACCURATEK\.agents\milestone_4_orchestrator`.
Create your initialization metadata files (`SCOPE.md`, `plan.md`, `progress.md`, `BRIEFING.md`).
Follow the Explorer -> Worker -> Reviewer -> Challenger -> Auditor iteration loop.
Run build/test commands via workers and verify all mobile unit/integration tests pass.
Deliver `handoff.md` when complete and report back to parent (`1fe457b2-a09c-44c8-9bd4-7d097d8632fe` / orchestrator).
