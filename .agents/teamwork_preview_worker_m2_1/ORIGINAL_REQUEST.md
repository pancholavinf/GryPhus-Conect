## 2026-07-29T23:41:20Z

You are Worker 1 for Milestone 2: Desktop App (`app_local`) Control de Personal.
Your working directory is `C:\Users\fcola\Desktop\APPACCURATEK\.agents\teamwork_preview_worker_m2_1`.
Create your working directory metadata files if needed, read the Explorer analysis reports in `.agents/teamwork_preview_explorer_m2_1/handoff.md`, `.agents/teamwork_preview_explorer_m2_2/handoff.md`, and `.agents/teamwork_preview_explorer_m2_3/handoff.md`.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your scope of work:
1. Ensure required test packages (`pytest`, `pytest-qt`, `pytest-mock`) are installed in `.venv` if not already present.
2. Implement asynchronous `QThread` workers in `app_local/src/workers/personal_workers.py` for Supabase operations on `tipos_maestro`, `maestros`, `obras_maestros`, and `obras`.
   - Provide worker classes for fetching, saving, updating, toggling active status, obra assignments, and inline cargo creation.
   - Signal error handling for unique RUT constraint (`23505`) and delete restriction (`23503`).
3. Implement `app_local/src/ui/personal_view.py`:
   - Create `PersonalContent(QWidget)` with a `QTabWidget` containing 3 sub-tabs:
     - Sub-tab 1: Jefes de Obra (embedding existing `JefesContent` from `app_local/src/ui/jefes_view.py`).
     - Sub-tab 2: Maestros (CRUD for maestros with search line edit, RUT formatting & Modulo 11 validation, active toggle, assignment to obras via `obras_maestros`, and inline dialog `DialogNuevoCargo` to create `tipo_maestro` on-the-fly).
     - Sub-tab 3: Cargos y Tarifas Diarias (CRUD for `tipos_maestro` table: `nombre` and `sueldo_diario`).
4. Update `app_local/src/ui/main_view.py`:
   - Rename sidebar button to "Control de Personal".
   - Replace stack widget index 2 with `PersonalContent`.
   - Connect sidebar navigation logic cleanly.
5. Create comprehensive unit and UI tests in `app_local/tests/`:
   - `app_local/tests/test_personal_workers.py`
   - `app_local/tests/test_personal_view.py`
   - `app_local/tests/test_main_view_integration.py`
6. Run builds and tests via terminal commands (e.g. `$env:QT_QPA_PLATFORM="offscreen"; .venv\Scripts\python.exe -m pytest app_local/tests/ -v` and legacy E2E suite `python -m unittest discover -s tests/e2e -p "test_*.py"`).
7. Record all executed commands, test outputs, modified files, and verification results in `C:\Users\fcola\Desktop\APPACCURATEK\.agents\teamwork_preview_worker_m2_1\handoff.md` and message your completion.

Relevant domain skills available for reference:
- Frontend UI Engineering: `C:\Users\fcola\Desktop\APPACCURATEK\.agents\skills\frontend-ui-engineering_skill\SKILL.md`
- Supabase: `C:\Users\fcola\Desktop\APPACCURATEK\.agents\skills\supabase\SKILL.md`
- Python Design Patterns: `C:\Users\fcola\Desktop\APPACCURATEK\.agents\skills\python-desing-patterns_skill\SKILL.md`
