## 2026-07-29T23:39:28Z
You are Explorer 1 for Milestone 4 (R2: Mobile App Offline Attendance & Sync).
Your working directory is C:\Users\fcola\Desktop\APPACCURATEK\.agents\teamwork_preview_explorer_m4_db_sync_1.
Your task:
1. Create your working directory and briefing/progress files.
2. Read project code files (especially `src/database/db.js` and `src/database/sync.js` in `app_trackeo_avances` or wherever mobile app code is located).
3. Analyze the existing SQLite database setup and Supabase sync logic.
4. Formulate exact schema definitions for local SQLite tables: `tipos_maestro`, `maestros`, `obras_maestros`, `asistencia_diaria`, `asistencia_diaria_detalle`. Ensure columns align with Supabase tables and support offline sync state (e.g. `synced` / `pending` status, local IDs vs remote UUIDs/IDs, timestamps).
5. Formulate exact logic for `syncCatalog()` (pulling `tipos_maestro`, `maestros`, `obras_maestros` from Supabase into local SQLite) and `syncAsistencia()` (pushing pending local attendance records and photo evidence via Hermes-compatible ArrayBuffer upload to Supabase storage and tables).
6. Document your complete findings and implementation strategy in `analysis.md` and deliver `handoff.md` in your working directory. Send a message to parent when complete with the path to your handoff.
