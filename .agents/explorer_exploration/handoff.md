# Handoff Report: Attendance Control Codebase Exploration

**Date:** 2026-07-29  
**Agent:** Teamwork Explorer (`explorer_exploration`)  
**Target Project:** Accuratek Ecosystem (`C:\Users\fcola\Desktop\APPACCURATEK`)  
**Status:** Investigation Complete (Read-Only)  

---

## 1. Observation

Direct observations from codebase inspection across `app_local`, `app_trackeo_avances`, and `INFO PROYECTO`:

1. **Desktop App Navigation Structure:**
   - In `app_local/src/ui/main_view.py` (lines 48–101), four main buttons exist in `Sidebar`: `btn_dashboard` (index 0), `btn_ingesta` (index 1), `btn_jefes` (index 2), and `btn_materiales` (index 3).
   - In `app_local/src/ui/main_view.py` (lines 110–136), clicking an Obra card in the Dashboard dynamically instantiates `AvancesContent` (`avances_window.py`) as an embedded sub-view.
   - `AvancesContent` contains sub-tabs for Statistics (Matplotlib), Advance Audit Grid, `EDPTab` (`edp_tab.py`), and `ReportesContent` (`reportes_view.py`).

2. **Desktop App Supabase Client Initialization:**
   - In `app_local/main.py` (lines 15–27), environment variables `SUPABASE_URL` and `SUPABASE_KEY` are read from `.env` via `dotenv` and `create_client` is initialized.
   - In `app_local/src/core/workers.py` (lines 40–43 & 80–84), worker threads enforce role checks: users with role `jefe_obra` are rejected with `"Acceso denegado: Los Jefes de Obra no pueden acceder a la aplicación de escritorio."`

3. **Desktop App Report Generation:**
   - `generate_pdf_report.py` (root directory, lines 13–73): Implements `NumberedCanvas` inheriting from `reportlab.pdfgen.canvas.Canvas` for dynamic two-pass page numbering (`"Página X de Y"`).
   - `app_local/src/utils/pdf_edp_generator.py` (lines 1–250): Uses ReportLab `SimpleDocTemplate` to compile institutional Estados de Pago (EDP).
   - `app_local/src/core/edp_controller.py` (lines 128–236): Calculates financial totals (Subtotal, 5% Retention default, Advance discount, 19% IVA), writes to `estados_pago` table in Supabase, freezes advances (`estado_pago_id`), uploads PDF to Storage bucket `estados_pago`, and returns public URL.

4. **Mobile App Architecture & Offline SQLite:**
   - In `app_trackeo_avances/App.js` (lines 223–277), `@react-navigation/native-stack` handles navigation across `Login`, `Home`, `ObraMenu`, `SelectionFlow`, and `ReporteDiarioFlow`.
   - In `app_trackeo_avances/src/database/db.js` (lines 28–116), `initDatabase()` creates local SQLite tables: `perfiles_usuario`, `obras`, `obras_jefes_obra`, `items_obra`, `avances`, `materiales`, `reporte_obra`, `reporte_obra_consumos`, `sync_meta`.
   - In `app_trackeo_avances/src/database/sync.js` (lines 183–329), `syncAdvances()` reads unsynced advances (`synced = 0`), converts local photo URIs to Base64/ArrayBuffer (`blobToBase64` $\rightarrow$ `base64ToArrayBuffer`), uploads to bucket `accuratek-data`, inserts record into Supabase `avances`, and marks local `synced = 1`.

5. **Mobile App Work Menu & Selection Hierarchy:**
   - `app_trackeo_avances/src/screens/ObraMenuScreen.js` (lines 283–494): Contains a primary action button "Registrar Avance" and a complete "Reporte Diario de Terreno" form with report types (`actualizacion`, `incidente`, `accidente`, `otro`), text notes, gallery/camera photo attachments, material counters (`+`/`-`), and an emergency custom material reporter (`REP_OTRO_MAT_LOGO`).
   - `app_trackeo_avances/src/screens/SelectionFlowScreen.js`: Implements step-by-step selection for physical progress ($m^2$) with **Auto-Skip logic** (`[Estructura] ➔ [Dimensión] ➔ [Ubicación] ➔ [Largo] ➔ [Cantidad] ➔ [Foto] ➔ [Comentario]`).

6. **Database Schemas & Attendance Gap:**
   - Database tables documented in `INFO PROYECTO/contexto_bd.md` (lines 30–105) and confirmed in `HANDOFF.md` (lines 122–177) are: `perfiles_usuario`, `obras`, `obras_jefes_obra`, `items_obra`, `avances`, `materiales`, `reporte_obra`, `reporte_obra_consumos`, `estados_pago`.
   - **Observation of Absent Feature:** No tables, models, SQLite DDLs, or UI components exist for `trabajadores` (workers/laborers), `asistencia_diaria` (attendance control), or `tarifas_diarias` (daily wages/jornales).

---

## 2. Logic Chain

1. **Premise:** The system currently provides robust physical progress tracking ($m^2$), material consumption deviation analysis, daily field logs, and EDP payment compilation.
2. **Finding 1 (Desktop):** The Desktop app (`app_local`) uses a modular QStackedWidget architecture with custom QThread workers for async I/O. Adding an Attendance Control and Worker Master module requires extending `main_view.py` with a new sidebar button and adding a `TrabajadoresContent` view.
3. **Finding 2 (Mobile):** The Mobile app (`app_trackeo_avances`) relies on a offline-first SQLite database (`db.js`) and module-locked sync pipeline (`sync.js`). Adding attendance roll-call requires adding `asistencia_diaria` to SQLite `initDatabase()`, adding an "Asistencia de Personal" button in `ObraMenuScreen.js`, and extending `sync.js` to push attendance logs to Supabase.
4. **Finding 3 (Database):** No `.sql` files exist in the codebase; schemas are maintained directly in Supabase Postgres and mirrored in `db.js`. Implementing Attendance Control will require creating new tables: `trabajadores`, `trabajadores_obras_tarifas`, and `asistencia_diaria`.

---

## 3. Caveats

- **Network Mode:** Investigation was conducted strictly in `CODE_ONLY` mode (no active network calls to remote Supabase instances).
- **Mobile Native Compilation:** Mobile app code was inspected directly; native build artifacts (`.apk` / `.ipa`) were not compiled during this read-only phase.
- **Unimplemented Feature:** Attendance Control is currently at 0% implementation in the existing repository. The design provided in `analysis.md` is the recommended integration blueprint.

---

## 4. Conclusion

The codebase is well-structured, clean, and highly modular. Integrating the **Attendance Control (Control de Asistencia)** feature requires three clear phases:
1. **Schema Layer:** Create `trabajadores`, `trabajadores_obras_tarifas`, and `asistencia_diaria` tables in Supabase Postgres and mirror them in SQLite `db.js`.
2. **Mobile App (`app_trackeo_avances`):** Add worker catalog pull in `syncCatalog()`, add an interactive attendance roll-call button/modal in `ObraMenuScreen.js`, and add `syncAsistencia()` to `sync.js`.
3. **Desktop App (`app_local`):** Add a "Trabajadores y Asistencia" tab in `main_view.py`, implement worker/rate management in `jefes_view.py` or a new `trabajadores_view.py`, and link attendance costs to the project analytics panel in `avances_window.py`.

---

## 5. Verification Method

To verify these findings independently:
1. **Inspect Desktop Tabs:** View `app_local/src/ui/main_view.py` lines 48–100 to verify existing sidebar buttons.
2. **Inspect Mobile SQLite DDL:** View `app_trackeo_avances/src/database/db.js` lines 28–116 to verify active local table definitions.
3. **Inspect Mobile Sync Engine:** View `app_trackeo_avances/src/database/sync.js` lines 183–329 to inspect the Hermes-compatible photo upload pipeline.
4. **Confirm SQL File Absence:** Run `Get-ChildItem -Recurse -Filter *.sql` in PowerShell inside `C:\Users\fcola\Desktop\APPACCURATEK` to confirm no `.sql` files exist.
