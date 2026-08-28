# Execution Plan: Milestone 2 — Control de Personal

## Objectives
1. Perform baseline exploration (3 Explorers) to inspect `app_local` layout, existing UI components, `jefes_view.py`, Supabase clients/schemas (`tipos_maestro`, `maestros`, `obras_maestros`), and existing tests/test runners.
2. Implement feature requirements using 1 Worker:
   - Create/update `app_local/src/workers/personal_workers.py` with QThread workers for non-blocking Supabase DB calls.
   - Update `app_local/src/ui/personal_view.py` with 3 sub-tabs (Jefes de Obra, Maestros, Cargos y Tarifas Diarias).
   - Update `app_local/src/ui/main_view.py` sidebar to reflect 'Control de Personal'.
   - Add/update unit and UI test coverage.
3. Review implementation with 2 Reviewers.
4. Stress test and challenge implementation with 2 Challengers.
5. Audit integrity with 1 Forensic Auditor (`teamwork_preview_auditor`).
6. Deliver final handoff and report to parent orchestrator.
