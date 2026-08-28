# Scope: Milestone 2 — Desktop App (`app_local`) Control de Personal

## Overview
Implement R3 (Part 1) for `app_local`:
1. Rename/reorganize sidebar tab to 'Control de Personal' in `app_local/src/ui/main_view.py`.
2. Inside 'Control de Personal' (`personal_view.py`), build a main container view with 3 sub-tabs:
   - Sub-tab 1: Jefes de Obra (integration of existing `jefes_view.py`).
   - Sub-tab 2: Maestros (CRUD for workers/maestros: search filter, RUT format/validation, active toggle, assignment to obras via `obras_maestros`, inline creation of new `tipo_maestro`/cargo on-the-fly).
   - Sub-tab 3: Cargos y Tarifas Diarias (CRUD for `tipos_maestro` table: `nombre` and `sueldo_diario`).
3. Asynchronous `QThread` workers in `personal_workers.py` handling all Supabase calls for `tipos_maestro`, `maestros`, and `obras_maestros` without blocking the PyQt UI thread.

## Target Files
- `app_local/src/ui/main_view.py` (sidebar navigation update)
- `app_local/src/ui/personal_view.py` (new/updated view with QTabWidget containing 3 sub-tabs)
- `app_local/src/ui/jefes_view.py` (ensuring compatibility / integration)
- `app_local/src/workers/personal_workers.py` (QThread async workers for CRUD operations)
- Related tests in `app_local/tests/` (unit and UI testing)

## Status
| # | Requirement | Scope | Status |
|---|-------------|-------|--------|
| 1 | Main View Sidebar | Rename tab to 'Control de Personal' in `main_view.py` | PLANNED |
| 2 | Sub-tab 1: Jefes de Obra | Integrate `jefes_view.py` as sub-tab 1 inside `personal_view.py` | PLANNED |
| 3 | Sub-tab 2: Maestros | Worker CRUD, search, RUT, active toggle, obras assignment, inline cargo creation | PLANNED |
| 4 | Sub-tab 3: Cargos y Tarifas | `tipos_maestro` CRUD (`nombre`, `sueldo_diario`) | PLANNED |
| 5 | Async Workers | QThread workers in `personal_workers.py` for Supabase interaction | PLANNED |
| 6 | Unit/UI Testing | Full test coverage & verification | PLANNED |
