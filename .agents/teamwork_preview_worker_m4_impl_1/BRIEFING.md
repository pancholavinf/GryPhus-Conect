# BRIEFING — 2026-07-29T19:41:00-04:00

## Mission
Implement Milestone 4 (R2: Mobile App Offline Attendance & Sync) in `app_trackeo_avances`.

## 🔒 My Identity
- Archetype: implementer, qa, specialist
- Roles: implementer, qa, specialist
- Working directory: C:\Users\fcola\Desktop\APPACCURATEK\.agents\teamwork_preview_worker_m4_impl_1
- Original parent: 92e9d86b-ed3f-43b1-b220-8ee6c7f7e73f
- Milestone: Milestone 4 (R2: Mobile App Offline Attendance & Sync)

## 🔒 Key Constraints
- DO NOT CHEAT. All implementations must be genuine.
- Minimal change principle.
- Write code only in `app_trackeo_avances`. Metadata only in agent directory.

## Current Parent
- Conversation ID: 92e9d86b-ed3f-43b1-b220-8ee6c7f7e73f
- Updated: 2026-07-29T19:41:00-04:00

## Task Summary
- **What to build**:
  1. SQLite schema update in `src/database/db.js` for catalog & attendance tables (`tipos_maestro`, `maestros`, `obras_maestros`, `asistencia_diaria`, `asistencia_diaria_detalle`).
  2. Implement SQLite helper functions: `getMaestrosForObra`, `checkAttendanceExistsToday`, `saveLocalAttendance`, `getPendingAsistencias`, `markAsistenciaSynced`, and integrate with `memoryCache.js`.
  3. Navigation & UI: Register `AsistenciaFlow` in `App.js`, add `btn-asistencia` in `ObraMenuScreen.js`, create `src/screens/AsistenciaScreen.js`.
  4. Mandatory photo evidence capture with compression, segmented control status evaluation (1.0, 0.5, 0.0), corrective attendance banner/flag.
  5. Sync updates in `src/database/sync.js`: `syncCatalog(jefeId)` and `syncAsistencia()`, photo arrayBuffer upload pipeline via `blobToBase64()` + `base64ToArrayBuffer()`.
  6. Execute tests (`npm test` / `npm run test:e2e`) in `app_trackeo_avances` and verify all tests pass.
- **Success criteria**: All tests pass natively, offline attendance state maintained properly, sync pushes to Supabase Storage & DB seamlessly.

## Key Decisions Made
- Follow exact detailed specs from Explorer 1, Explorer 2, Explorer 3.

## Change Tracker
- **Files modified**: None yet.
- **Build status**: Pending
- **Pending issues**: None

## Quality Status
- **Build/test result**: Pending
- **Lint status**: Pending
- **Tests added/modified**: Pending

## Loaded Skills
- None explicitly passed, but domain knowledge applied.

## Artifact Index
- `C:\Users\fcola\Desktop\APPACCURATEK\.agents\teamwork_preview_worker_m4_impl_1\ORIGINAL_REQUEST.md` — Original User Request
- `C:\Users\fcola\Desktop\APPACCURATEK\.agents\teamwork_preview_worker_m4_impl_1\BRIEFING.md` — Agent Briefing
- `C:\Users\fcola\Desktop\APPACCURATEK\.agents\teamwork_preview_worker_m4_impl_1\progress.md` — Progress tracker
