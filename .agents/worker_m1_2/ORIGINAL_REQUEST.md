## 2026-07-29T23:28:45Z
<USER_REQUEST>
You are Worker 2 for Milestone 1: Database & Supabase Schema for APPACCURATEK.
Your working directory is `C:\Users\fcola\Desktop\APPACCURATEK\.agents\worker_m1_2`.
Create your `progress.md` and `BRIEFING.md` in your working directory.

Load and follow the Supabase skill instructions located at:
`C:\Users\fcola\Desktop\APPACCURATEK\.agents\skills\supabase\SKILL.md`

### Task Directives: Remediation of Reviewer 1 Findings

Reviewer 1 issued a VETO due to 3 critical issues in the implementation and test harness:

1. **FACADE IMPLEMENTATION IN RLS TEST (INTEGRITY VIOLATION)**:
   - In `tests/e2e/test_supabase_attendance_schema.py`, `test_07_rls_security_policy_rules_verification` defined a dummy local class `RLSPolicyEvaluator` with hardcoded return values (`if role in ['authenticated', 'jefe_obra', 'admin']: return True`).
   - **Fix**: Remove `RLSPolicyEvaluator` and hardcoded logic completely. Replace it with genuine programmatic introspection of `pg_policies` catalog or real database query evaluation against PostgreSQL/Supabase permissions.

2. **NON-IDEMPOTENT VERIFICATION SCRIPT**:
   - `verify_r1_schema.py` fails on repeat runs with `psycopg2.IntegrityError` because static test data (e.g. RUT `12.345.678-K`) is left committed in the database without cleanup/teardown.
   - **Fix**: Wrap DML test assertions in explicit transaction rollbacks or include robust `try...finally` teardown statements (cleaning up inserted test rows) so `verify_r1_schema.py` can be executed repeatedly with exit code 0 every time.

3. **FK SPECIFICATION MISMATCH IN UNIT TESTS**:
   - In `tests/e2e/test_supabase_attendance_schema.py` (line 104), `asistencia_diaria_detalle.maestro_id` was specified as `ON DELETE CASCADE` instead of `ON DELETE RESTRICT`.
   - **Fix**: Correct the unit test definition for `asistencia_diaria_detalle.maestro_id` FK to `ON DELETE RESTRICT`, matching `SCOPE.md` and `schema_r1.sql`.

### Verification Steps Required:
1. Run `verify_r1_schema.py` **at least twice sequentially** to verify clean idempotency:
   `.\.venv\Scripts\python.exe C:\Users\fcola\Desktop\APPACCURATEK\.agents\worker_m1_2\verify_r1_schema.py` (or updated script path)
2. Run unit tests:
   `.\.venv\Scripts\python.exe -m unittest tests/e2e/test_supabase_attendance_schema.py`
   `.\.venv\Scripts\python.exe -m unittest tests/e2e/test_desktop_control_personal.py`
3. Verify all tests pass with 100% genuine assertions (no facade classes or hardcoded boolean returns).

Document changes in `C:\Users\fcola\Desktop\APPACCURATEK\.agents\worker_m1_2\changes.md` and write handoff report in `C:\Users\fcola\Desktop\APPACCURATEK\.agents\worker_m1_2\handoff.md`.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Report back via send_message when completed.
</USER_REQUEST>
