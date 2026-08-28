# Original User Request

## 2026-07-29T19:39:02-04:00

You are the Sub-Orchestrator for Milestone 2: Desktop App (`app_local`) Control de Personal.
Your scope:
Implement R3 (Part 1):
1. Rename/reorganize the sidebar tab to 'Control de Personal' in `app_local/src/ui/main_view.py`.
2. Inside 'Control de Personal' (`personal_view.py`), create 3 sub-tabs:
   - Sub-tab 1: Jefes de Obra (integrated from `jefes_view.py`).
   - Sub-tab 2: Maestros (CRUD for workers/maestros with search, RUT, active toggle, assignment to obras via `obras_maestros`, and inline 'crear nuevo tipo/cargo sobre la marcha').
   - Sub-tab 3: Cargos y Tarifas Diarias (CRUD for `tipos_maestro` including `nombre` and `sueldo_diario`).
3. Connect all operations via asynchronous `QThread` workers (`personal_workers.py`) to Supabase tables (`tipos_maestro`, `maestros`, `obras_maestros`).

Your working directory is `C:\Users\fcola\Desktop\APPACCURATEK\.agents\milestone_2_orchestrator`.
Create your initialization metadata files (`SCOPE.md`, `plan.md`, `progress.md`, `BRIEFING.md`).
Follow the Explorer -> Worker -> Reviewer -> Challenger -> Auditor iteration loop.
Run build/test commands via workers and verify that all unit/UI tests pass.
Deliver `handoff.md` when complete and report back to parent (`1fe457b2-a09c-44c8-9bd4-7d097d8632fe` / orchestrator).
