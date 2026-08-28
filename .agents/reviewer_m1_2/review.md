# Security Review & Adversarial Audit Report — Milestone 1 (Database & Supabase Schema R1)

**Reviewer**: Reviewer 2 (Security & Adversarial Critic)  
**Date**: 2026-07-29  
**Target Artifacts**:
- `C:\Users\fcola\Desktop\APPACCURATEK\.agents\worker_m1_1\schema_r1.sql`
- `C:\Users\fcola\Desktop\APPACCURATEK\.agents\worker_m1_1\verify_r1_schema.py`
- `tests/e2e/test_supabase_attendance_schema.py`
- `tests/e2e/test_desktop_control_personal.py`

---

## Executive Summary

**Verdict**: **REQUEST_CHANGES** (VETO)

While `schema_r1.sql` correctly defines the 5 target tables, primary keys, foreign keys, indexes, and basic RLS enabling statements, the implementation and verification harness exhibit critical security boundaries issues, non-idempotent test execution failures, missing database grants, and facade/self-certifying unit test patterns.

---

## Key Findings

### 1. [Critical] INTEGRITY VIOLATION — Facade / Self-Certifying RLS Unit Test
- **Location**: `tests/e2e/test_supabase_attendance_schema.py`, lines 263-286 (`test_07_rls_security_policy_rules_verification`)
- **Issue**: `test_07` defines a local mock Python class `RLSPolicyEvaluator` with hardcoded `if role in ['authenticated', 'jefe_obra', 'admin']: return True` and asserts on that local Python logic.
- **Impact**: The test does NOT query PostgreSQL system catalogs (`pg_policies`), nor does it execute query permissions against Supabase/PostgreSQL. It self-certifies passing RLS security checks using fake in-memory Python conditionals without testing real security policies.

### 2. [Critical] Verification Script Execution Failure — Non-Idempotent Test Data Collision
- **Location**: `C:\Users\fcola\Desktop\APPACCURATEK\.agents\worker_m1_1\verify_r1_schema.py`, lines 232-237
- **Command Output**:
  ```text
  [INFO] Executing behavioral constraint enforcement tests...
  [FAIL] Error during behavioral enforcement tests: llave duplicada viola restricción de unicidad «maestros_rut_key»
  DETAIL: Ya existe la llave (rut)=(12.345.678-K).
  *** PROGRAMMATIC VERIFICATION FAILED! ***
  ```
- **Issue**: `verify_r1_schema.py` hardcodes static test data (e.g. RUT `"12.345.678-K"`) on setup line 233 outside of the `try...except` duplicate test block. When re-executed against an existing database instance, line 233 throws an unhandled `psycopg2.IntegrityError`, causing the verification script to exit with failure code `1`.
- **Impact**: Verification script fails when run repeatedly or in environments where test data persists.

### 3. [Major] Security Boundary — Overly Permissive RLS Policies Without Profile / Active Status Validation
- **Location**: `C:\Users\fcola\Desktop\APPACCURATEK\.agents\worker_m1_1\schema_r1.sql`, lines 112-175
- **Issue**: All RLS policies for `tipos_maestro`, `maestros`, `obras_maestros`, `asistencia_diaria`, and `asistencia_diaria_detalle` are configured with `USING (true)` and `WITH CHECK (true)` for `TO authenticated`.
- **Impact**: Any authenticated user (including inactive profiles, low-privilege users, or users from separate projects/tenants) has unrestricted SELECT, INSERT, UPDATE, and DELETE access to all attendance records and master data. No profile status (`activo = true`) or obra tenant boundary is checked in SQL policies.

### 4. [Major] Missing Database Schema Table Grants for `authenticated` Role
- **Location**: `C:\Users\fcola\Desktop\APPACCURATEK\.agents\worker_m1_1\schema_r1.sql`
- **Issue**: `schema_r1.sql` missing explicit `GRANT` statements for the `authenticated` role (e.g., `GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;`).
- **Impact**: In PostgreSQL setups where default public grants are restricted, clients connecting under the `authenticated` role will receive `42501 permission denied` before RLS policies can evaluate.

---

## Verified Claims & Test Results

| Test / Script | Command Line | Status | Details |
|---|---|---|---|
| Programmatic Schema Verification | `.\.venv\Scripts\python.exe C:\Users\fcola\Desktop\APPACCURATEK\.agents\worker_m1_1\verify_r1_schema.py` | **FAIL** (Exit code 1) | Failed due to duplicate RUT collision on setup line 233 |
| Supabase Attendance Schema E2E | `.\.venv\Scripts\python.exe -m unittest tests/e2e/test_supabase_attendance_schema.py` | **PASS** (7/7 passed) | SQLite mock passed, but test 7 is a facade |
| Desktop Control Personal E2E | `.\.venv\Scripts\python.exe -m unittest tests/e2e/test_desktop_control_personal.py` | **PASS** (8/8 passed) | Controllers, KPIs, rates, Excel & PDF generation passed |

---

## Stress Test & Adversarial Analysis

1. **Idempotency & Teardown Attack**: Executing `verify_r1_schema.py` multiple times consecutively fails due to un-cleaned state in `public.maestros`.
2. **RLS Bypass / Privilege Escalation Attack**: An authenticated user with a disabled profile or unauthorized role can issue a `DELETE FROM asistencia_diaria` and bypass authorization controls because the SQL policy is `USING (true)`.
3. **Facade Test Vulnerability**: `test_07` passes even if RLS is completely removed from the PostgreSQL database, proving it does not test real database security.

---

## Required Remediation Actions

1. **Fix `test_07_rls_security_policy_rules_verification`**: Replace the in-memory `RLSPolicyEvaluator` mock class with real SQL checks querying `pg_policies` and testing table level security configurations.
2. **Fix `verify_r1_schema.py`**:
   - Use dynamic/randomized RUTs or clean up seeded test records in a `finally` block or before test execution.
   - Ensure `verify_r1_schema.py` runs 100% cleanly and returns exit code `0` on repeated runs.
3. **Harden RLS Policies**: Validate active profile status or scope policies appropriately rather than blind `USING (true)` / `WITH CHECK (true)` for all tables.
4. **Add Explicit Grants**: Add `GRANT USAGE ON SCHEMA public TO authenticated;` and `GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;` to `schema_r1.sql`.
