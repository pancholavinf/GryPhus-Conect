## 2026-07-29T23:39:28Z
You are Explorer 3 for Milestone 4 (R2: Mobile App Offline Attendance & Sync).
Your working directory is C:\Users\fcola\Desktop\APPACCURATEK\.agents\teamwork_preview_explorer_m4_tests_hermes_3.
Your task:
1. Create your working directory and briefing/progress files.
2. Search and inspect the mobile app repository (`app_trackeo_avances` or root), package.json, test scripts, Jest configurations, and existing test suites.
3. Investigate Hermes JavaScript engine constraints regarding binary photo upload (`ArrayBuffer`, base64, `FormData` vs `Blob`) for Supabase Storage uploads in Expo / React Native.
4. Define comprehensive test specifications and test cases for:
   - Local SQLite table creation and CRUD operations for attendance tables.
   - `ObraMenuScreen` navigation and button rendering.
   - `AsistenciaScreen` rendering, maestro evaluation selection (1.0, 0.5, 0.0), photo requirement validation, and corrective attendance flag logic.
   - `syncCatalog()` and `syncAsistencia()` execution (with mock Supabase client and SQLite DB).
5. Document your complete findings, Hermes compatibility analysis, and test plan in `analysis.md` and deliver `handoff.md` in your working directory. Send a message to parent when complete with the path to your handoff.
