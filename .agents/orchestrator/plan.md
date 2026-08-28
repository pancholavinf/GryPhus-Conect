# Plan: Sistema de Control de Asistencia Diario, Maestros y Tarifas Diarias

## Phase 1: Initial Codebase Exploration & Setup
1. Spawn an Explorer subagent to inspect the existing Supabase migrations, database connection setup, Desktop PyQt6 codebase (`app_local`), and Mobile React Native codebase (`app_trackeo_avances`).
2. Identify existing database tables, models, components, screens, database scripts, and sync logic.

## Phase 2: Parallel Dual-Track Execution
- **Track A: E2E Testing Track**
  - Spawn E2E Testing Orchestrator.
  - Define E2E test infra and test cases covering database schemas, RLS, mobile offline attendance & sync, desktop personal control UI, daily rate CRUD, KPI dashboards, and Excel/PDF reports.
  - Publish `TEST_READY.md`.

- **Track B: Implementation Track**
  - **Milestone 1: Database & Supabase Schema**
    - Create tables: `tipos_maestro`, `maestros`, `obras_maestros`, `asistencia_diaria`, `asistencia_diaria_detalle`.
    - Set up foreign keys, indexes, and RLS policies.
  - **Milestone 2: Desktop App - Control de Personal**
    - Refactor tab layout to "Control de Personal" with 3 sub-tabs: Jefes de Obra, Maestros (with on-the-fly cargo creation), Cargos y Tarifas Diarias (CRUD for cargos and `sueldo_diario`).
  - **Milestone 3: Desktop App - Dashboard & Attendance Reports**
    - Attendance KPI metrics per obra on Dashboard.
    - Attendance reports tab with date range filter, half day / full day summaries, total salary calculation, Excel and PDF export.
  - **Milestone 4: Mobile App - Offline Attendance & Sync**
    - SQLite schema update, "Asistencia de Personal" screen in work menu, 1.0/0.5/0.0 evaluation selection, photo evidence requirement, `sync.js` sync, and Corrective Attendance Report handling.
  - **Milestone 5: E2E Integration, Adversarial Hardening & Forensic Audit**
    - Execute Tier 1-4 E2E tests, Tier 5 Adversarial Coverage Hardening, and Forensic Integrity Audit.

## Phase 3: Verification & Sentinel Reporting
- Verify all acceptance criteria are met with passing test suite and CLEAN forensic audit verdict.
- Report completion to Sentinel.
