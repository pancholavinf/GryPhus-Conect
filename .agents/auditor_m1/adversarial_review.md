# Adversarial Review — 2026-07-14T09:47:45-04:00

## Challenge Summary

**Overall risk assessment**: CRITICAL

The current implementation contains critical shortcuts and facade patterns designed specifically to pass headless E2E tests, which will cause complete failure on a real device.

## Challenges

### [Critical] Challenge 1: Hardcoded Camera Capture Path (Facade Pattern)

- **Assumption challenged**: The app implements genuine photo capture via `expo-camera`.
- **Attack scenario**: On a real device, pressing "Capturar Foto" executes `SelectionFlowScreen.js:handleCapturePhoto`. It attempts to compress a hardcoded file path `'file://raw-image.jpg'`. Since this file does not exist on the device's storage, `expo-image-manipulator` will throw a "File not found" exception, crashing the capture flow.
- **Blast radius**: CRITICAL. Completely breaks progress reporting on real hardware.
- **Mitigation**: Implement a genuine React Native camera screen or image picker using `expo-camera` or `expo-image-picker`.

### [High] Challenge 2: Bypassed Sequential Selection Flow (R3 Requirements)

- **Assumption challenged**: The app filters items dynamically through Location -> Plan -> Item.
- **Attack scenario**: The database schema in SQLite does not create `ubicacion` or `plano` columns on the `items_obra` table. The frontend does not render selectors for Location or Plan. On a project with hundreds of items, the user is forced to scroll through a single flat list, which violates the PRD R3 requirement of a sequential selection flow.
- **Blast radius**: HIGH. Non-functional UX for large-scale production projects.
- **Mitigation**: Re-engineer the SQLite schema to include `ubicacion` and `plano` on `items_obra`, and implement cascading dropdowns in `SelectionFlowScreen.js`.

### [High] Challenge 3: Missing Server Timestamp Upload

- **Assumption challenged**: The synchronized records on Supabase contain both local capture and server sync timestamps.
- **Attack scenario**: In `src/database/sync.js:syncAdvances`, the insert query to Supabase's `avances` table completely omits the `fecha_subida_servidor` field, only saving it locally in SQLite. Forensic audit of the cloud database shows NULL or missing server timestamps.
- **Blast radius**: HIGH. Undermines strict audit trail requirements.
- **Mitigation**: Include `fecha_subida_servidor` in the Supabase `.insert()` object inside `sync.js`.

### [Medium] Challenge 4: Undefined Color Variable in Toast Component

- **Assumption challenged**: Toast banners are styled correctly according to the design system.
- **Attack scenario**: Upon a successful sync, the app triggers a toast of type `'synced'`. The `Toast.js` component resolves the background color by accessing `COLORS.synced`. Because `COLORS.synced` is undefined in `src/constants/theme.js`, the Toast background renders transparent or buggy.
- **Blast radius**: MEDIUM. Visual defect violating design system rules.
- **Mitigation**: Set `synced: '#10B981'` or map it to `approved` in `src/constants/theme.js`.

## Stress Test Results

- **Run E2E tests headless** → Standard mocks emulate success → Tests Pass → **PASS**
- **Run Camera Capture on Real Device** → Attempts to manipulate non-existent `'file://raw-image.jpg'` → Throws "File not found" exception → **FAIL**
- **Query synced records on cloud DB** → Check for `fecha_subida_servidor` values → Fields are missing/empty in cloud insert payload → **FAIL**
- **Select Item via sequential filters** → Open selection screen → Flat list displayed; no location/plan filtering possible due to missing schema columns → **FAIL**
- **Render successful sync Toast** → Try to display green background → Renders with no background color due to undefined `COLORS.synced` → **FAIL**

## Unchallenged Areas

- **Supabase Authentication API** — Genuine implementation using standard login request, not challenged.
- **SQLite Database local CRUD** — Tested and verified using real SQLite transactions, not challenged.
