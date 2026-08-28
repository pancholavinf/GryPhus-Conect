## 2026-07-29T23:39:28Z
You are Explorer 2 for Milestone 4 (R2: Mobile App Offline Attendance & Sync).
Your working directory is C:\Users\fcola\Desktop\APPACCURATEK\.agents\teamwork_preview_explorer_m4_ui_photo_2.
Your task:
1. Create your working directory and briefing/progress files.
2. Read project code files (especially `src/screens/ObraMenuScreen.js`, `src/screens/AsistenciaScreen.js`, `package.json`, and navigation configuration in the mobile app).
3. Analyze existing screen navigation and UI design patterns.
4. Formulate exact UI and screen logic for:
   - Adding 'Asistencia de Personal' operational button in `ObraMenuScreen.js` navigating to `AsistenciaScreen.js`.
   - `AsistenciaScreen.js`:
     - Querying assigned maestros for the current obra (`obras_maestros` joined with `maestros` and `tipos_maestro`).
     - Selecting evaluation status for each maestro: 1.0 (Día Completo), 0.5 (Medio Día), 0.0 (Ausente).
     - Mandatory photo evidence capture using `expo-camera` or `expo-image-picker` before submission.
     - Checking existing attendance for current date in local DB: if present, display 'Reporte Correctivo de Asistencia' notice and set `es_correctivo = true`.
     - Saving attendance records locally to SQLite (`asistencia_diaria` and `asistencia_diaria_detalle`) with `synced = 0`.
5. Document your complete findings and implementation strategy in `analysis.md` and deliver `handoff.md` in your working directory. Send a message to parent when complete with the path to your handoff.
