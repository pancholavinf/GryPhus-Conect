# Comprehensive Exploration Report: Attendance Control & Accuratek Ecosystem Architecture

**Date:** July 29, 2026  
**Investigator:** Teamwork Explorer Agent  
**Workspace:** `C:\Users\fcola\Desktop\APPACCURATEK`  
**Working Directory:** `C:\Users\fcola\Desktop\APPACCURATEK\.agents\explorer_exploration`  

---

## Executive Summary

An exhaustive investigation of the **Accuratek (Track Obra)** codebase was conducted to evaluate the desktop application (`app_local`), mobile application (`app_trackeo_avances`), Supabase database schemas, and report generation systems. 

The system currently handles **physical progress tracking ($m^2$)**, **material consumption deviations**, **daily field logs**, and **payment state generation (EDP)**. However, **Attendance Control (Control de Asistencia)**, **Worker Masters (Maestro de Trabajadores/Operarios)**, and **Daily Labor Rates (Tarifas Diarias / Jornales)** are **not yet implemented** in the database schema or UI layers.

This report provides the full architectural map of existing modules and detailed integration points required to implement the Attendance Control feature cleanly into the ecosystem.

---

## 1. Desktop Application (`app_local`) Analysis

### 1.1 Directory Structure & Key Files
- **Root Entry Point:** `app_local/main.py` — Application lifecycle, Supabase authentication check, window setup, and stylesheet loader (`src/ui/style.qss`).
- **Core Business Logic (`app_local/src/core/`):**
  - `controller.py`: Ingestion controller for Excel parsing (`openpyxl`, `pandas`), mapping items to `items_obra` and handling material price validation.
  - `edp_controller.py`: Controller for Payment State (EDP) compilation, sequence number assignment, subtotal/tax/retention calculations, freezing approved advances (`estado_pago_id`), and PDF generation/upload.
  - `jefes_controller.py`: CRUD operations for Jefe de Obra user profiles (`perfiles_usuario`) and project assignment (`obras_jefes_obra`).
  - `workers.py`: Asynchronous execution threads (`QThread`) preventing UI freezing during network operations: `LoginWorker`, `SessionCheckWorker`, `FetchDashboardDataWorker`, `FetchJefesWorker`, `ProcessIngestaWorker`, `FetchEDPHistorialWorker`, `EmitEDPWorker`, `FetchReportesWorker`, `RespondReporteWorker`, `FetchMaterialesWorker`, `SaveMaterialWorker`, `DeleteMaterialWorker`.
- **User Interface Layer (`app_local/src/ui/`):**
  - `main_view.py`: Outer shell featuring a 250px left navigation sidebar and a `QStackedWidget` containing primary views.
  - `dashboard_view.py`: Main executive dashboard rendering color-coded project cards (`ClickableObraCard`) and key performance indicators.
  - `ingesta_view.py`: UI for uploading Excel cubications, mapping work items, setting contract unit prices, and saving backups to Supabase Storage (`archivos_obras`).
  - `jefes_view.py`: Admin interface to create Jefe de Obra accounts and assign them to specific projects (`obras_jefes_obra`).
  - `materiales_view.py`: Global material catalog manager (units, theoretical yield $m^2$, technical sheets, studies, images).
  - `avances_window.py` / `AvancesContent`: Obra detail analytics embedded view with Matplotlib charts (cumulative progress, horizontal bars by status/category, donut chart, financial bar chart) and an interactive auditing grid with photo downloader (`ImageDownloader`).
  - `edp_tab.py` / `EDPTab`: Tab for creating and reviewing Estados de Pago (EDPs), retention/advance discounts modal (`EmisionEDPDialog`), and historical PDF viewer.
  - `reportes_view.py` / `ReportesContent`: Daily field log dashboard, material consumption auditor, manager response form, and Matplotlib deviation graph (`GraficosRendimientoDialog`).
- **Utilities (`app_local/src/utils/`):**
  - `pdf_edp_generator.py`: ReportLab PDF generator compiling formal institutional EDP documents with accurate sub-tables and page numbering.

### 1.2 Existing Navigation & Tabs Structure (`main_view.py`)
Navigation is managed via `QStackedWidget` in `main_view.py`:
1. **Index 0:** `DashboardContent` (`dashboard_view.py`)
2. **Index 1:** `IngestaContent` (`ingesta_view.py`)
3. **Index 2:** `JefesContent` (`jefes_view.py`)
4. **Index 3:** `MaterialesContent` (`materiales_view.py`)
5. **Sub-view (Index 4 dynamic):** `AvancesContent` (`avances_window.py`) — Opened when clicking an Obra card in the Dashboard. Contains sub-tabs:
   - Tab 1: Statistics & Matplotlib Charts
   - Tab 2: Detailed Progress Grid & Photo Auditor
   - Tab 3: `EDPTab` (Estados de Pago)
   - Tab 4: `ReportesContent` (Daily Field Logs & Consumptions)

### 1.3 Supabase Database Connection Configuration
- **Initialization:** In `app_local/main.py` (lines 15–27), environment variables are loaded using `python-dotenv`:
  ```python
  SUPABASE_URL = os.getenv("SUPABASE_URL")
  SUPABASE_KEY = os.getenv("SUPABASE_KEY")
  supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
  ```
- **Authentication Handling:** Uses `supabase.auth.sign_in_with_password` and `get_session()` inside `QThread` workers. Ensures desktop access is restricted strictly to users with role `Administrador` (denying `jefe_obra` role access).

### 1.4 Dashboard Widgets (`dashboard_view.py`)
- **`ClickableObraCard`:** Inherits from `QFrame` with drop shadow (`QGraphicsDropShadowEffect`). Styled with a 8px left border colored dynamically according to `obra.color` (hex string from database).
- **Layout Grid:** 3-column `QGridLayout` displaying active projects dynamically loaded via `FetchDashboardDataWorker`. Shows assigned supervisor names (`obras_jefes_obra` join).

### 1.5 Existing Report Generation Scripts
1. **`generate_pdf_report.py` (Root directory):** 60 KB standalone ReportLab script using `NumberedCanvas` (two-pass page count, corporate styling, header/footer suppression on cover).
2. **`app_local/src/utils/pdf_edp_generator.py`:** Generates institutional PDF Estados de Pago (EDP) containing:
   - Header with Accuratek logo & mandatory project data.
   - Itemized financial table: Contract Quantity vs Previous Quantity vs Present Quantity vs Unit Price vs Present Subtotal.
   - Financial totals: Subtotal, Retention %, Advance Discount, Net Subtotal, 19% IVA, and Total Amount.
   - Manager and Supervisor signature lines.
3. **`app_local/src/ui/reportes_view.py` (`GraficosRendimientoDialog`):** Interactive Matplotlib performance dialog comparing:
   - Daily Real Consumption line chart.
   - Real Consumption vs Theoretical Consumption ($Avance(m^2) \times Rendimiento$) bar chart.

---

## 2. Mobile Application (`app_trackeo_avances`) Analysis

### 2.1 Directory Structure & Stack
- **Framework:** React Native with **Expo SDK 54**.
- **Root Entry Point:** `app_trackeo_avances/App.js` — Database initialization, font loading (`Montserrat`, `Inter`), Supabase session restoration, background sync management, navigation stack configuration, and custom Toast notification config.
- **Directory Breakdown (`app_trackeo_avances/src/`):**
  - `components/`: Custom UI elements like `Toast.js`.
  - `constants/`: Theme styling (`theme.js` — corporate colors `#1A529B`, `#4BA2E3`, `#0F172A`).
  - `database/`: Local SQLite engine (`db.js`) and bidirectional sync engine (`sync.js`).
  - `screens/`: `HomeScreen.js`, `LoginScreen.js`, `ObraMenuScreen.js`, `ReporteDiarioScreen.js`, `SelectionFlowScreen.js`.
  - `services/`: `supabase.js` client client, `imageCompressor.js`, `memoryCache.js` (web fallback).

### 2.2 SQLite Setup (`src/database/db.js`)
Uses `expo-sqlite` (database `trackeo.db`) with fallback to `memoryCache.js` for web preview:
- **Local Tables Initialized in `initDatabase()`:**
  - `perfiles_usuario` (id, nombre, rol, email, clave)
  - `obras` (id, nombre, estado, fecha_creacion, color)
  - `obras_jefes_obra` (id, obra_id, jefe_obra_id)
  - `items_obra` (id, obra_id, ubicacion, plano, descripcion_plano, estructura, dimension, perfil, cantidad, unidad, descripcion, material_id)
  - `avances` (id, item_obra_id, jefe_obra_id, foto_url, comentario, fecha_captura_local, fecha_subida_servidor, estado_revision, cantidad, synced)
  - `materiales` (id, nombre, unidad_medida, rendimiento_teorico_m2, descripcion)
  - `reporte_obra` (id, obra_id, jefe_obra_id, tipo_reporte, mensaje, archivos_adjuntos, fecha_publicacion, estado_reb, respuesta, mensaje_respuesta, synced)
  - `reporte_obra_consumos` (id, reporte_obra_id, material_id, material, cantidad, unidad, fecha, synced)
  - `sync_meta` (key, value)

### 2.3 Sync Engine (`src/database/sync.js`)
- **Catalog Sync (`syncCatalog(jefeId)`):** Downloads assigned obras (`obras_jefes_obra`), associated `items_obra`, and linked `materiales` from Supabase to SQLite and memory cache.
- **Advances Sync (`syncAdvances(onProgress)`):**
  - Checks network connection using `@react-native-community/netinfo`.
  - Reads unsynced records (`synced = 0`).
  - **Hermes-Compatible Photo Pipeline:** Converts local photo URI to Blob $\rightarrow$ Base64 (`blobToBase64`) $\rightarrow$ `ArrayBuffer` (`base64ToArrayBuffer`). Uploads `ArrayBuffer` to Supabase Storage bucket `accuratek-data`.
  - Inserts `avances` row to Supabase with `fecha_captura_local` and `fecha_subida_servidor`.
  - Updates local SQLite `synced = 1`.
- **Daily Reports Sync (`syncReportes(onProgress)`):** Uploads pending `reporte_obra` logs, attachments, and material consumption entries (`reporte_obra_consumos`).
- **Background Listener (`startBackgroundSync`):** Subscribes to `NetInfo` state changes to automatically push pending local queues when internet is restored.

### 2.4 Mobile Navigation & Work Menu Screens (`src/screens/`)
- **Navigation Engine (`App.js`):** `createNativeStackNavigator` with screens:
  - `Login`: Supabase Auth login.
  - `Home`: Displays assigned obras cards with linear gradients (`expo-linear-gradient`), user profile tab, reload trigger.
  - `ObraMenu`: Core hub for the active project. Features:
    1. **"Registrar Avance" Button:** Launches physical progress workflow (`SelectionFlowScreen`).
    2. **Reporte Diario Form:** Type cards (`actualizacion`, `incidente`, `accidente`, `otro`), message input, camera/gallery attachment loader, guided material counters (`+` / `-`), and emergency unlisted material reporter (`REP_OTRO_MAT_LOGO`).
  - `SelectionFlow`: Hierarchical step-by-step selector for reporting physical progress ($m^2$). Implements **Auto-Skip logic** (if a step has only one available option, it auto-selects and skips to the next step):
    `[Estructura] ➔ [Dimensión] ➔ [Ubicación] ➔ [Largo] ➔ [Cantidad] ➔ [Foto] ➔ [Comentario] ➔ [Confirmar]`
  - `ReporteDiarioFlow`: Standalone daily report screen.

---

## 3. Supabase & Database Migrations Analysis

### 3.1 Migration Files Status
- **SQL Migration Directory:** Currently **no `.sql` files** or explicit migration tool configurations exist in the workspace repository.
- **Schema Management:** Database schemas have been applied directly to Supabase via Postgres DDL or web console and mirrored programmatically in `app_trackeo_avances/src/database/db.js`.

### 3.2 Existing Database Tables Reference

| Table Name | Primary Key | Foreign Keys | Key Attributes | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `perfiles_usuario` | `id` (UUID) | `auth.users(id)` | `nombre`, `rol` ('Administrador'/'Jefe_Obra'), `email`, `telefono`, `foto_perfil_url` | User profile & RLS identity |
| `obras` | `id` (UUID) | None | `nombre`, `estado` ('Activa'/'Pausada'/'Finalizada'), `color`, `fecha_creacion` | Projects catalog |
| `obras_jefes_obra` | `id` (UUID) | `obra_id` $\rightarrow$ `obras`, `jefe_obra_id` $\rightarrow$ `perfiles_usuario` | - | Access control mapping (RLS filtering) |
| `items_obra` | `id` (UUID) | `obra_id` $\rightarrow$ `obras`, `material_id` $\rightarrow$ `materiales` | `ubicacion`, `estructura`, `dimension`, `perfil`, `cantidad` ($m^2$), `unidad`, `precio_unitario_contrato` | Cubication items loaded from Excel |
| `avances` | `id` (UUID) | `item_obra_id` $\rightarrow$ `items_obra`, `jefe_obra_id` $\rightarrow$ `perfiles_usuario`, `estado_pago_id` $\rightarrow$ `estados_pago` | `foto_url`, `comentario`, `cantidad`, `fecha_captura_local`, `fecha_subida_servidor`, `estado_revision` ('pendiente'/'aprobado'/'rechazado') | Physical progress reported in field |
| `materiales` | `id` (UUID) | None | `nombre`, `unidad_medida`, `rendimiento_teorico_m2`, `descripcion` | Global master catalog of materials |
| `reporte_obra` | `id` (UUID) | `obra_id` $\rightarrow$ `obras`, `jefe_obra_id` $\rightarrow$ `perfiles_usuario` | `tipo_reporte`, `mensaje`, `archivos_adjuntos` (text[]), `fecha_publicacion`, `estado_reb`, `respuesta`, `mensaje_respuesta` | Daily field log logbook |
| `reporte_obra_consumos` | `id` (UUID) | `reporte_obra_id` $\rightarrow$ `reporte_obra`, `material_id` $\rightarrow$ `materiales` | `material`, `cantidad`, `unidad`, `fecha` | Real material consumption per daily log |
| `estados_pago` | `id` (UUID) | `obra_id` $\rightarrow$ `obras`, `creado_por` $\rightarrow$ `perfiles_usuario` | `numero_estado_pago`, `fecha_emision`, `periodo_desde`, `periodo_hasta`, `subtotal_pesos`, `monto_retencion`, `monto_anticipo`, `monto_neto`, `monto_iva`, `monto_total`, `archivo_pdf_url` | Frozen financial billing statements |

---

## 4. Integration Analysis & Feature Mapping

To implement **Attendance Control (Control de Asistencia)**, **Worker Masters (Maestros)**, **Daily Rates (Jornales/Tarifas Diarias)**, and **Labor Reports**, the system requires targeted schema extensions and UI additions.

### 4.1 Master Catalog: Workers (`trabajadores` / `operarios`)
- **Current State:** Only supervisors (`perfiles_usuario`) exist. No table tracks field workers/laborers.
- **Proposed Table `trabajadores`:**
  ```sql
  CREATE TABLE trabajadores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rut TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    cargo TEXT NOT NULL, -- e.g. 'Pintor', 'Jornal', 'Capataz', 'Estructurero'
    telefono TEXT,
    estado TEXT DEFAULT 'Activo' CHECK (estado IN ('Activo', 'Inactivo')),
    fecha_ingreso DATE DEFAULT CURRENT_DATE
  );
  ```

### 4.2 Daily Rates & Worker Assignment (`tarifas_diarias` / `obras_trabajadores`)
- **Current State:** Contract prices (`precio_unitario_contrato`) exist for physical cubication ($m^2$), but daily labor wage rates do not exist.
- **Proposed Table `trabajadores_obras_tarifas`:**
  ```sql
  CREATE TABLE trabajadores_obras_tarifas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    obra_id UUID REFERENCES obras(id) ON DELETE CASCADE,
    trabajador_id UUID REFERENCES trabajadores(id) ON DELETE CASCADE,
    tarifa_diaria NUMERIC NOT NULL DEFAULT 0.0, -- Wage rate per day ($/jornal)
    fecha_asignacion DATE DEFAULT CURRENT_DATE,
    UNIQUE(obra_id, trabajador_id)
  );
  ```

### 4.3 Attendance Control (`asistencia_diaria`)
- **Current State:** Absent in SQLite and Supabase.
- **Proposed Table `asistencia_diaria`:**
  ```sql
  CREATE TABLE asistencia_diaria (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    obra_id UUID REFERENCES obras(id) ON DELETE CASCADE,
    trabajador_id UUID REFERENCES trabajadores(id) ON DELETE CASCADE,
    jefe_obra_id UUID REFERENCES perfiles_usuario(id) ON DELETE SET NULL,
    fecha DATE NOT NULL DEFAULT CURRENT_DATE,
    estado_asistencia TEXT NOT NULL CHECK (estado_asistencia IN ('presente', 'ausente', 'medio_dia', 'licencia', 'vacaciones')),
    horas_extra NUMERIC DEFAULT 0.0,
    observacion TEXT,
    fecha_registro_local TIMESTAMPTZ NOT NULL,
    fecha_subida_servidor TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(obra_id, trabajador_id, fecha)
  );
  ```

### 4.4 Mobile App Integration Points (`app_trackeo_avances`)
1. **SQLite (`src/database/db.js`):** Add `trabajadores`, `trabajadores_obras_tarifas`, and `asistencia_diaria` tables to `initDatabase()` and write helper functions `saveAsistencia()`, `getUnsyncedAsistencias()`, `markAsistenciaSynced()`.
2. **Sync Engine (`src/database/sync.js`):** 
   - Extend `syncCatalog()` to pull `trabajadores` assigned to the user's obras.
   - Add `syncAsistencia()` pipeline to push local attendance records offline-first to Supabase.
3. **Screen Navigation (`ObraMenuScreen.js`):**
   - Add an **"Asistencia de Personal"** operational button alongside "Registrar Avance" and "Reporte Diario".
   - Implement an interactive attendance roll-call screen: list workers assigned to the project with toggles (`Presente`, `Ausente`, `Medio Día`), extra hours input, and single-tap submit.

### 4.5 Desktop App Integration Points (`app_local`)
1. **Sidebar Navigation (`main_view.py`):**
   - Add a new sidebar button `btn_trabajadores` / "Trabajadores y Asistencia" pointing to a new view `TrabajadoresContent`.
2. **Master UI (`trabajadores_view.py`):**
   - CRUD interface for worker records (RUT, Name, Position, Default Daily Rate).
   - Assignment modal to link workers to projects with specific daily wage rates (`tarifa_diaria`).
3. **Analytics & Reports (`avances_window.py` & `reportes_view.py`):**
   - Add Attendance sub-tab under project details: monthly attendance grid, absent count, total extra hours.
   - Labor Cost vs Production Ratio: Compare total daily labor cost ($\sum \text{Present Workers} \times \text{Daily Rate}$) against approved physical progress billing ($m^2 \times PU$).

---

## 5. Verification & Validation Protocol

To verify future implementations against this architecture:
1. **Database Schema Compliance:** Ensure foreign keys match `UUID` types and RLS policies allow `Administrador` full access while restricting `Jefe_Obra` to assigned projects (`obras_jefes_obra`).
2. **Mobile Offline Test:** Test attendance roll-call with device in Airplane mode. Verify SQLite insertion in `trackeo.db`, check `synced = 0`, toggle connectivity, and verify automatic background push via `NetInfo`.
3. **Desktop Financial Cross-Check:** Confirm that daily labor costs calculated from `asistencia_diaria` line up with project date ranges during EDP compilation in `EDPTab`.

