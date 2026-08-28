## 2026-07-29T23:20:00Z
You are the E2E Test Suite Developer for APPACCURATEK's Attendance Control System.
Your working directory is `C:\Users\fcola\Desktop\APPACCURATEK\.agents\worker_e2e_testing`.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Scope & Tasks:
1. Create `C:\Users\fcola\Desktop\APPACCURATEK\TEST_INFRA.md` at project root containing complete specifications for Tiers 1-4 test cases (Category-Partition, Boundary Value Analysis, Pairwise, Real-world Workload) for the Attendance Control System based on `C:\Users\fcola\Desktop\APPACCURATEK\.agents\orchestrator\PROJECT.md` and `C:\Users\fcola\Desktop\APPACCURATEK\.agents\ORIGINAL_REQUEST.md`.
   - Feature coverage includes:
     - Supabase DB schema (`tipos_maestro`, `maestros`, `obras_maestros`, `asistencia_diaria`, `asistencia_diaria_detalle`), FKs, indexes, check constraints (`estado_asistencia in (1.0, 0.5, 0.0)`), unique constraints, RLS policies.
     - Desktop App (`app_local`) Control de Personal UI CRUD (Jefes de Obra, Maestros with on-the-fly cargo creation, Cargos y Tarifas Diarias), daily rates `sueldo_diario` calculation, Dashboard KPIs, and Attendance Reports by Obra with date filtering, totals (jornales, sueldos), and Excel/PDF export.
     - Mobile App (`app_trackeo_avances`) offline SQLite attendance marking (1.0, 0.5, 0.0), evidence photo requirement, `sync.js` bidirectional sync, and Corrective Report handling (`es_correctivo = true`).

2. Implement executable test scripts/harnesses in Python and JS under `C:\Users\fcola\Desktop\APPACCURATEK\tests\e2e\` (and/or inside `app_local/tests/` and `app_trackeo_avances/tests/`):
   - `tests/e2e/test_supabase_attendance_schema.py`: Pytest/unittest validating Supabase tables, FKs, indexes, check constraints (`estado_asistencia in (1.0, 0.5, 0.0)`), unique constraints, default values, and RLS policy rules.
   - `tests/e2e/test_desktop_control_personal.py`: Pytest/unittest validating Desktop App Control de Personal UI CRUD, Cargos and `sueldo_diario` updates, Maestros on-the-fly cargo creation, Dashboard KPIs calculation, Attendance Reports filtering by date range, daily rates calculation (0.5 * sueldo_diario, 1.0 * sueldo_diario), and Excel/PDF report generation.
   - `tests/e2e/test_mobile_attendance_sync.js` (or Jest/Node runner test in `app_trackeo_avances`): Node/Jest suite validating Mobile App SQLite attendance tables, 1.0/0.5/0.0 status selection, evidence photo validation (rejecting submission without photo), `sync.js` sync payload building and sync execution, and Corrective Report handling (`es_correctivo = true` when re-submitting attendance for an already submitted date).

3. Execute the test suite using pytest / python unittest and node/jest test runner. Verify that all tests execute and PASS 100%.

4. Publish `C:\Users\fcola\Desktop\APPACCURATEK\TEST_READY.md` at project root declaring readiness, including test execution timestamp, pass/fail metrics, execution commands, and tier coverage breakdown.

5. Report completion back to orchestrator with a detailed handoff report in `C:\Users\fcola\Desktop\APPACCURATEK\.agents\worker_e2e_testing\handoff.md`.
