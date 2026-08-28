# Schema & Test Suite Quality Review Report — Milestone 1 (Attendance Control R1)

**Review Date**: 2026-07-29
**Reviewer**: Reviewer 1 (reviewer, critic)
**Verdict**: **REQUEST_CHANGES** (VETO)

---

## 1. Review Summary

The DDL defined in `C:\Users\fcola\Desktop\APPACCURATEK\.agents\worker_m1_1\schema_r1.sql` accurately implements the 5 core attendance control tables, data types, constraints, FK cascade/restrict rules, indexes, and RLS policies required by `SCOPE.md`.

However, the verification script `verify_r1_schema.py` and the E2E test harness `tests/e2e/test_supabase_attendance_schema.py` contain **CRITICAL flaws** and an **INTEGRITY VIOLATION**:

1. **Integrity Violation**: `test_07_rls_security_policy_rules_verification` in `tests/e2e/test_supabase_attendance_schema.py` implements a dummy facade class (`RLSPolicyEvaluator`) with hardcoded return statements (`if role in ['authenticated', 'jefe_obra', 'admin']: return True`). It tests its own python code instead of verifying actual PostgreSQL RLS policies or database engine behavior.
2. **Verification Failure**: `verify_r1_schema.py` fails with exit code 1 on repeat runs because it commits test data with fixed RUTs (`12.345.678-K`) without teardown/cleanup logic or dynamic test keys.
3. **Specification Mismatches**: SQLite simulator in `test_supabase_attendance_schema.py` defines `ON DELETE CASCADE` for `asistencia_diaria_detalle.maestro_id` (line 104) and `ON DELETE SET NULL` for `asistencia_diaria.registrado_por` (line 90), which directly contradict `SCOPE.md` (`ON DELETE RESTRICT` and NO ACTION/default respectively).

---

## 2. Findings & Classification

### [Critical / INTEGRITY VIOLATION] Finding 1: Facade Implementation in RLS Test Verification
- **What**: `test_07_rls_security_policy_rules_verification` in `tests/e2e/test_supabase_attendance_schema.py` uses a local dummy class `RLSPolicyEvaluator` with hardcoded return logic (`if role in ['authenticated', 'jefe_obra', 'admin']: return True`).
- **Where**: `tests/e2e/test_supabase_attendance_schema.py:265-285`
- **Why**: The test claims to verify RLS policy security rules, but only calls hardcoded Python logic. It performs zero checks against PostgreSQL `pg_policies`, SQLite constraints, or actual Supabase RLS mechanics. This is a self-certifying facade.
- **Suggestion**: Remove the dummy class. In PostgreSQL verification (`verify_r1_schema.py`), query `pg_policies` and test actual queries under different database roles. In SQLite unit tests, test table access or mock standard permission rules appropriately without fake self-certifying helpers.

### [Critical] Finding 2: Programmatic Verification Script Fails Non-Idempotent Run
- **What**: Executing `.\.venv\Scripts\python.exe C:\Users\fcola\Desktop\APPACCURATEK\.agents\worker_m1_1\verify_r1_schema.py` fails with `exit code 1` on subsequent runs.
- **Where**: `C:\Users\fcola\Desktop\APPACCURATEK\.agents\worker_m1_1\verify_r1_schema.py:233-245`
- **Error Output**:
  ```text
  [FAIL] [FAIL] Error during behavioral enforcement tests: llave duplicada viola restricción de unicidad «maestros_rut_key»
  DETAIL: Ya existe la llave (rut)=(12.345.678-K).
  ```
- **Why**: The script inserts static test RUT `12.345.678-K` and commits transactions without deleting test records in a `finally` block or using dynamic test keys. Additionally, line 233 places the initial seed insert outside a `try...except` block, causing unhandled transaction crashes.
- **Suggestion**: Wrap behavioral tests in transactional rollback (`conn.rollback()`), clean up seeded test rows in a `finally` block, or generate random unique test RUTs per execution.

### [Major] Finding 3: Foreign Key Constraint Rules Mismatch in Test Harness
- **What**: SQLite simulator schema in `test_supabase_attendance_schema.py` uses incorrect ON DELETE actions.
- **Where**: `tests/e2e/test_supabase_attendance_schema.py:90, 104`
- **Why**: Line 104 uses `FOREIGN KEY (maestro_id) REFERENCES maestros(id) ON DELETE CASCADE` for `asistencia_diaria_detalle`, whereas `SCOPE.md` line 41 specifies `ON DELETE RESTRICT`. Line 90 uses `ON DELETE SET NULL` for `registrado_por`, whereas `SCOPE.md` line 35 specifies default/NO ACTION.
- **Suggestion**: Update `test_supabase_attendance_schema.py` lines 90 and 104 to match `schema_r1.sql` and `SCOPE.md` (`ON DELETE RESTRICT` for `maestro_id` in `asistencia_diaria_detalle`).

---

## 3. Verified Claims Matrix

| Claim | Verification Method | Status | Notes |
|---|---|---|---|
| `schema_r1.sql` Table DDL & Columns | Inspected DDL vs `SCOPE.md` | **PASS** | 5 tables, correct types (`numeric`, `date`, `uuid`) |
| `schema_r1.sql` FK Constraints | Inspected DDL vs `SCOPE.md` | **PASS** | `RESTRICT` on `tipos_maestro` and `asistencia_diaria_detalle.maestro_id`, `CASCADE` on `obras` |
| `schema_r1.sql` CHECK & UNIQUE | Inspected DDL vs `SCOPE.md` | **PASS** | `estado_asistencia IN (1.0, 0.5, 0.0)`, UNIQUE `rut`, UNIQUE `(obra_id, maestro_id)`, UNIQUE `(asistencia_diaria_id, maestro_id)` |
| `schema_r1.sql` Performance Indexes | Inspected DDL | **PASS** | Indexes on all FKs, `fecha`, `(obra_id, fecha)` |
| `verify_r1_schema.py` Execution | Command execution via CLI | **FAIL** | Exit code 1 on repeat execution due to duplicate RUT collision |
| `test_supabase_attendance_schema.py` Execution | `unittest` CLI | **PASS** (with caveats) | 7 tests pass in 0.005s, but contains facade test & FK rule mismatch |
| `test_desktop_control_personal.py` Execution | `unittest` CLI | **PASS** | 8 tests pass in 0.043s (CRUD, rates, KPIs, date filtering, Excel/PDF exports) |

---

## 4. Adversarial Stress-Testing & Attack Surface

1. **Repeated Script Execution (Idempotency)**:
   - *Test*: Executed `verify_r1_schema.py` twice consecutively.
   - *Result*: **FAILED**. Dirty database state from run 1 caused run 2 to crash.
2. **Facade Detection in RLS Testing**:
   - *Test*: Analyzed implementation of `test_07_rls_security_policy_rules_verification`.
   - *Result*: **FAILED**. Self-certifying facade class bypassing DB security check.
3. **FK Cascade vs Restrict Inconsistencies**:
   - *Test*: Cross-referenced SQLite test simulator schema against Postgres SQL migration schema.
   - *Result*: **FAILED**. SQLite simulator allowed `CASCADE` delete on `maestros` -> `asistencia_diaria_detalle` instead of enforcing `RESTRICT`.

---

## 5. Required Action Items Before Re-Submission

1. **Fix `verify_r1_schema.py`**:
   - Add teardown / cleanup logic or wrap tests in explicit rollback transactions.
   - Use dynamic unique test data (e.g., UUID-based RUTs) so the script can run repeatedly cleanly without failing.
2. **Fix `test_supabase_attendance_schema.py`**:
   - Remove dummy `RLSPolicyEvaluator` facade class. Replace with genuine assertion logic or table inspection tests.
   - Fix foreign key `ON DELETE RESTRICT` constraint on `asistencia_diaria_detalle.maestro_id` (line 104).
3. **Re-run and verify zero failures across all commands**.
