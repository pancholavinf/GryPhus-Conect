# Project: Accurateck Attendance & Master Rates System

## Architecture
Multi-platform system for Daily Attendance Control, Worker Masters, and Daily Rates:
- **Supabase PostgreSQL**: Tables `tipos_maestro`, `maestros`, `obras_maestros`, `asistencia_diaria`, `asistencia_diaria_detalle` with FKs, indexes, and RLS policies.
- **Mobile App (`app_trackeo_avances`)**: React Native (Expo) app with SQLite local caching and `sync.js` bidirectional synchronization with Supabase. Supports attendance registration, evidence photos, and corrective reports.
- **Desktop App (`app_local`)**: PyQt6 Python desktop app featuring "Control de Personal" (Jefes de Obra, Maestros, Cargos y Tarifas Diarias), Dashboard KPIs, and Attendance Reports by Obra (date filter, daily rates/salary calculation, Excel/PDF export).

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Database & Supabase Schema | Create `tipos_maestro`, `maestros`, `obras_maestros`, `asistencia_diaria`, `asistencia_diaria_detalle` with FKs, indexes, RLS policies | None | DONE |
| 2 | Desktop App Control de Personal | Refactor sidebar to "Control de Personal" with 3 sub-tabs (Jefes de Obra, Maestros with on-the-fly cargo creation, Cargos y Tarifas Diarias CRUD) | M1 | IN_PROGRESS |
| 3 | Desktop App Dashboard & Reports | Attendance KPI dashboard, Attendance Reports by Obra with date filtering, totals calculation, Excel & PDF export | M2 | PLANNED |
| 4 | Mobile App Attendance & Sync | SQLite schema updates, "Asistencia de Personal" screen, 1.0/0.5/0.0 evaluation, photo capture, `sync.js` sync, Corrective Report logic | M1 | IN_PROGRESS |
| 5 | E2E Integration & Verification | Pass 100% of E2E test suite (Tiers 1-4), Tier 5 Adversarial Coverage Hardening, Forensic Audit | M3, M4 | PLANNED |

## Interface Contracts
### Supabase PostgreSQL Tables & Columns
- `tipos_maestro`: `id` (uuid, default gen_random_uuid()), `nombre` (text, not null), `sueldo_diario` (numeric, not null default 0.0), `created_at` (timestamptz, default now()).
- `maestros`: `id` (uuid, default gen_random_uuid()), `rut` (text, unique, not null), `nombre_completo` (text, not null), `tipo_maestro_id` (uuid, fk tipos_maestro.id), `telefono` (text), `activo` (boolean, default true), `created_at` (timestamptz, default now()).
- `obras_maestros`: `id` (uuid, default gen_random_uuid()), `obra_id` (uuid, fk obras.id), `maestro_id` (uuid, fk maestros.id), `created_at` (timestamptz, default now()), UNIQUE(obra_id, maestro_id).
- `asistencia_diaria`: `id` (uuid, default gen_random_uuid()), `obra_id` (uuid, fk obras.id), `fecha` (date, not null), `foto_evidencia_url` (text, not null), `es_correctivo` (boolean, default false), `registrado_por` (uuid, fk perfiles_usuario.id), `created_at` (timestamptz, default now()).
- `asistencia_diaria_detalle`: `id` (uuid, default gen_random_uuid()), `asistencia_diaria_id` (uuid, fk asistencia_diaria.id), `maestro_id` (uuid, fk maestros.id), `estado_asistencia` (numeric(3,1), not null check (estado_asistencia in (1.0, 0.5, 0.0))), `observaciones` (text), `created_at` (timestamptz, default now()), UNIQUE(asistencia_diaria_id, maestro_id).

### Mobile SQLite ↔ Supabase Sync
- Sync pulls `tipos_maestro`, `maestros`, `obras_maestros` down to local SQLite tables.
- Sync pushes local `asistencia_diaria` and `asistencia_diaria_detalle` to Supabase.
- Handles `es_correctivo` flag when re-submitting attendance for a date that was already submitted.

## Code Layout
- `app_local/`: PyQt6 Desktop Application codebase
  - `src/ui/`: `main_view.py`, `personal_view.py`, `dashboard_view.py`, `reportes_asistencia_view.py`
  - `src/core/`: `personal_controller.py`, `personal_workers.py`, `reportes_asistencia_controller.py`
- `app_trackeo_avances/`: React Native Expo Mobile Application codebase
  - `src/screens/`: `ObraMenuScreen.js`, `AsistenciaScreen.js`
  - `src/database/`: `db.js`, `sync.js`
