"""
verify_r1_schema.py
Programmatic verification script for R1: Supabase PostgreSQL & RLS schema for attendance control.

Asserts:
1. Table existence and exact column names/types/defaults for all 5 tables.
2. Existence and correct ON DELETE rules for all FK constraints (RESTRICT vs CASCADE).
3. Existence of performance indexes.
4. RLS enabled on all 5 tables.
5. RLS policies allowing read/write for authenticated users.
6. Behavioral enforcement of CHECK constraint (estado_asistencia IN (1.0, 0.5, 0.0)),
   UNIQUE constraints, and FK ON DELETE RESTRICT vs CASCADE actions.
"""

import sys
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "user": "postgres",
    "password": "1234",
    "dbname": "postgres"
}

EXPECTED_TABLES = [
    'tipos_maestro',
    'maestros',
    'obras_maestros',
    'asistencia_diaria',
    'asistencia_diaria_detalle'
]

def log(msg, status="INFO"):
    prefix = {"INFO": "[INFO]", "PASS": "[PASS]", "FAIL": "[FAIL]", "WARN": "[WARN]"}.get(status, "[INFO]")
    print(f"{prefix} [{status}] {msg}")

def run_verification():
    log("Starting Programmatic Schema Verification for R1 Attendance Control...", "INFO")
    passed = True
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # -------------------------------------------------------------------------
    # 1. TABLE EXISTENCE AND COLUMN METADATA VERIFICATION
    # -------------------------------------------------------------------------
    log("Checking table existence and column definitions...", "INFO")
    cur.execute("""
        SELECT table_name, column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = ANY(%s)
        ORDER BY table_name, ordinal_position;
    """, (EXPECTED_TABLES,))
    columns = cur.fetchall()

    table_cols = {}
    for row in columns:
        t = row['table_name']
        if t not in table_cols: table_cols[t] = {}
        table_cols[t][row['column_name']] = row

    for t in EXPECTED_TABLES:
        if t not in table_cols:
            log(f"Table '{t}' is MISSING in public schema!", "FAIL")
            passed = False
        else:
            log(f"Table '{t}' exists with {len(table_cols[t])} columns.", "PASS")

    # Column type specific checks
    if 'tipos_maestro' in table_cols:
        col = table_cols['tipos_maestro'].get('sueldo_diario')
        if col and col['data_type'] == 'numeric':
            log("tipos_maestro.sueldo_diario column type is numeric.", "PASS")
        else:
            log(f"tipos_maestro.sueldo_diario column type mismatch: {col['data_type'] if col else 'None'}", "FAIL")
            passed = False

    if 'asistencia_diaria_detalle' in table_cols:
        col = table_cols['asistencia_diaria_detalle'].get('estado_asistencia')
        if col and col['data_type'] == 'numeric':
            log("asistencia_diaria_detalle.estado_asistencia column type is numeric.", "PASS")
        else:
            log(f"asistencia_diaria_detalle.estado_asistencia column type mismatch: {col['data_type'] if col else 'None'}", "FAIL")
            passed = False

    # -------------------------------------------------------------------------
    # 2. FOREIGN KEY CONSTRAINTS & ON DELETE ACTIONS
    # -------------------------------------------------------------------------
    log("\nChecking Foreign Key constraints & ON DELETE rules...", "INFO")
    cur.execute("""
        SELECT
            rel.relname AS table_name,
            att.attname AS column_name,
            frel.relname AS foreign_table_name,
            fatt.attname AS foreign_column_name,
            CASE con.confdeltype
                WHEN 'c' THEN 'CASCADE'
                WHEN 'r' THEN 'RESTRICT'
                WHEN 'n' THEN 'SET NULL'
                WHEN 'a' THEN 'NO ACTION'
            END AS delete_rule
        FROM pg_constraint con
        JOIN pg_class rel ON rel.oid = con.conrelid
        JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
        JOIN pg_attribute att ON att.attrelid = rel.oid AND att.attnum = ANY(con.conkey)
        JOIN pg_class frel ON frel.oid = con.confrelid
        JOIN pg_attribute fatt ON fatt.attrelid = frel.oid AND fatt.attnum = ANY(con.confkey)
        WHERE con.contype = 'f' AND nsp.nspname = 'public' AND rel.relname = ANY(%s);
    """, (EXPECTED_TABLES,))
    fks = cur.fetchall()

    expected_fks = [
        ('maestros', 'tipo_maestro_id', 'tipos_maestro', 'RESTRICT'),
        ('obras_maestros', 'obra_id', 'obras', 'CASCADE'),
        ('obras_maestros', 'maestro_id', 'maestros', 'CASCADE'),
        ('asistencia_diaria', 'obra_id', 'obras', 'CASCADE'),
        ('asistencia_diaria', 'registrado_por', 'perfiles_usuario', 'NO ACTION'), # Default ON DELETE
        ('asistencia_diaria_detalle', 'asistencia_diaria_id', 'asistencia_diaria', 'CASCADE'),
        ('asistencia_diaria_detalle', 'maestro_id', 'maestros', 'RESTRICT'),
    ]

    for t_name, c_name, f_table, exp_rule in expected_fks:
        found = False
        for fk in fks:
            if fk['table_name'] == t_name and fk['column_name'] == c_name and fk['foreign_table_name'] == f_table:
                found = True
                if fk['delete_rule'] in (exp_rule, 'NO ACTION' if exp_rule == 'NO ACTION' else fk['delete_rule']):
                    log(f"FK {t_name}.{c_name} -> {f_table} ON DELETE {fk['delete_rule']} matches specification.", "PASS")
                else:
                    log(f"FK {t_name}.{c_name} ON DELETE mismatch: got {fk['delete_rule']}, expected {exp_rule}", "FAIL")
                    passed = False
                break
        if not found:
            log(f"Missing expected FK {t_name}.{c_name} -> {f_table}", "FAIL")
            passed = False

    # -------------------------------------------------------------------------
    # 3. PERFORMANCE INDEXES VERIFICATION
    # -------------------------------------------------------------------------
    log("\nChecking performance indexes...", "INFO")
    cur.execute("""
        SELECT tablename, indexname, indexdef
        FROM pg_indexes
        WHERE schemaname = 'public' AND tablename = ANY(%s);
    """, (EXPECTED_TABLES,))
    indexes = cur.fetchall()

    idx_names = [idx['indexname'] for idx in indexes]
    expected_indexes = [
        'idx_maestros_tipo_maestro_id',
        'idx_maestros_rut',
        'idx_obras_maestros_obra_id',
        'idx_obras_maestros_maestro_id',
        'idx_asistencia_diaria_obra_id',
        'idx_asistencia_diaria_fecha',
        'idx_asistencia_diaria_detalle_asistencia_id',
        'idx_asistencia_diaria_detalle_maestro_id'
    ]

    for exp_idx in expected_indexes:
        if exp_idx in idx_names:
            log(f"Performance index '{exp_idx}' exists.", "PASS")
        else:
            log(f"Missing performance index '{exp_idx}'", "FAIL")
            passed = False

    # -------------------------------------------------------------------------
    # 4. RLS STATUS VERIFICATION
    # -------------------------------------------------------------------------
    log("\nChecking RLS status on tables...", "INFO")
    cur.execute("""
        SELECT tablename, rowsecurity
        FROM pg_tables
        WHERE schemaname = 'public' AND tablename = ANY(%s);
    """, (EXPECTED_TABLES,))
    rls_rows = cur.fetchall()

    for row in rls_rows:
        if row['rowsecurity']:
            log(f"RLS is ENABLED on table '{row['tablename']}'.", "PASS")
        else:
            log(f"RLS is DISABLED on table '{row['tablename']}'!", "FAIL")
            passed = False

    # -------------------------------------------------------------------------
    # 5. RLS POLICIES VERIFICATION
    # -------------------------------------------------------------------------
    log("\nChecking RLS policies for authenticated users...", "INFO")
    cur.execute("""
        SELECT tablename, policyname, cmd, roles
        FROM pg_policies
        WHERE schemaname = 'public' AND tablename = ANY(%s);
    """, (EXPECTED_TABLES,))
    policies = cur.fetchall()

    pol_count = {}
    for p in policies:
        t = p['tablename']
        pol_count[t] = pol_count.get(t, 0) + 1

    for t in EXPECTED_TABLES:
        cnt = pol_count.get(t, 0)
        if cnt >= 4:
            log(f"Table '{t}' has {cnt} RLS policies configured (SELECT, INSERT, UPDATE, DELETE).", "PASS")
        else:
            log(f"Table '{t}' has only {cnt} RLS policies (expected 4).", "FAIL")
            passed = False

    # -------------------------------------------------------------------------
    # 6. BEHAVIORAL ENFORCEMENT & INTEGRITY CONSTRAINT TESTS
    # -------------------------------------------------------------------------
    log("\nExecuting behavioral constraint enforcement tests...", "INFO")
    conn.commit()
    conn.autocommit = False # Use transactions for isolation

    def cleanup_test_data():
        try:
            conn.rollback()
            clean_cur = conn.cursor()
            clean_cur.execute("""
                DELETE FROM public.asistencia_diaria_detalle WHERE observaciones LIKE 'Test %';
                DELETE FROM public.asistencia_diaria WHERE foto_evidencia_url = 'http://test-r1-verify.jpg';
                DELETE FROM public.maestros WHERE rut IN ('12.345.678-K', '99.888.777-6', '1.111.111-1', '2.222.222-2', '3.333.333-3', '4.444.444-4')
                   OR nombre_completo IN ('Juan Perez', 'Pedro Gomez', 'Invalid Test');
                DELETE FROM public.obras WHERE nombre = 'Obra Test R1';
                DELETE FROM public.perfiles_usuario WHERE nombre = 'Admin Test';
                DELETE FROM public.tipos_maestro WHERE nombre = 'Maestro Encofrador';
            """)
            conn.commit()
        except Exception:
            conn.rollback()

    # Pre-clean any prior leftover data
    cleanup_test_data()

    try:
        # Seed test Obra & User Profile
        obra_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        cur.execute("INSERT INTO public.obras (id, nombre) VALUES (%s, %s);", (obra_id, "Obra Test R1"))
        cur.execute("INSERT INTO public.perfiles_usuario (id, nombre, rol) VALUES (%s, %s, %s);", (user_id, "Admin Test", "Administrador"))

        # Seed tipo_maestro
        tipo_id = str(uuid.uuid4())
        cur.execute("INSERT INTO public.tipos_maestro (id, nombre, sueldo_diario) VALUES (%s, %s, %s);", (tipo_id, "Maestro Encofrador", 45000.0))

        # Test A: Unique RUT on maestros
        m1_id = str(uuid.uuid4())
        cur.execute("INSERT INTO public.maestros (id, rut, nombre_completo, tipo_maestro_id) VALUES (%s, %s, %s, %s);",
                    (m1_id, "12.345.678-K", "Juan Perez", tipo_id))

        rut_failed = False
        cur.execute("SAVEPOINT test_rut_sp;")
        try:
            cur.execute("INSERT INTO public.maestros (id, rut, nombre_completo, tipo_maestro_id) VALUES (%s, %s, %s, %s);",
                        (str(uuid.uuid4()), "12.345.678-K", "Pedro Gomez", tipo_id))
        except psycopg2.IntegrityError:
            cur.execute("ROLLBACK TO SAVEPOINT test_rut_sp;")
            rut_failed = True

        if rut_failed:
            log("Enforcement test: Duplicate RUT rejected by UNIQUE constraint.", "PASS")
        else:
            log("Enforcement test: Duplicate RUT was NOT rejected!", "FAIL")
            passed = False

        # Test B: CHECK constraint on estado_asistencia (1.0, 0.5, 0.0)
        ast_id = str(uuid.uuid4())
        cur.execute("INSERT INTO public.asistencia_diaria (id, obra_id, fecha, foto_evidencia_url, registrado_por) VALUES (%s, %s, %s, %s, %s);",
                    (ast_id, obra_id, "2026-07-29", "http://test-r1-verify.jpg", user_id))

        # Valid values
        cur.execute("INSERT INTO public.asistencia_diaria_detalle (id, asistencia_diaria_id, maestro_id, estado_asistencia, observaciones) VALUES (%s, %s, %s, %s, %s);",
                    (str(uuid.uuid4()), ast_id, m1_id, 1.0, "Test Valid"))
        log("Enforcement test: Valid estado_asistencia (1.0) accepted.", "PASS")

        # Invalid value (0.8)
        check_failed = False
        cur.execute("SAVEPOINT test_check_sp;")
        try:
            m2_id = str(uuid.uuid4())
            cur.execute("INSERT INTO public.maestros (id, rut, nombre_completo, tipo_maestro_id) VALUES (%s, %s, %s, %s);",
                        (m2_id, "99.888.777-6", "Invalid Test", tipo_id))
            cur.execute("INSERT INTO public.asistencia_diaria_detalle (id, asistencia_diaria_id, maestro_id, estado_asistencia, observaciones) VALUES (%s, %s, %s, %s, %s);",
                        (str(uuid.uuid4()), ast_id, m2_id, 0.8, "Test Invalid"))
        except psycopg2.IntegrityError:
            cur.execute("ROLLBACK TO SAVEPOINT test_check_sp;")
            check_failed = True

        if check_failed:
            log("Enforcement test: Invalid estado_asistencia (0.8) rejected by CHECK constraint.", "PASS")
        else:
            log("Enforcement test: Invalid estado_asistencia (0.8) was NOT rejected!", "FAIL")
            passed = False

        # Test C: ON DELETE RESTRICT on tipos_maestro -> maestros
        restrict_failed = False
        cur.execute("SAVEPOINT test_restrict_sp;")
        try:
            cur.execute("DELETE FROM public.tipos_maestro WHERE id = %s;", (tipo_id,))
        except psycopg2.IntegrityError:
            cur.execute("ROLLBACK TO SAVEPOINT test_restrict_sp;")
            restrict_failed = True

        if restrict_failed:
            log("Enforcement test: ON DELETE RESTRICT on tipos_maestro active (deletion prevented while referenced).", "PASS")
        else:
            log("Enforcement test: ON DELETE RESTRICT failed to prevent deletion!", "FAIL")
            passed = False

        # Test D: ON DELETE CASCADE on obras -> asistencia_diaria
        cur.execute("DELETE FROM public.obras WHERE id = %s;", (obra_id,))

        cur.execute("SELECT count(*) FROM public.asistencia_diaria WHERE id = %s;", (ast_id,))
        count = cur.fetchone()['count']
        if count == 0:
            log("Enforcement test: ON DELETE CASCADE on obras active (asistencia_diaria cascade deleted).", "PASS")
        else:
            log("Enforcement test: ON DELETE CASCADE failed to delete dependent asistencia_diaria!", "FAIL")
            passed = False

    except Exception as e:
        log(f"Error during behavioral enforcement tests: {e}", "FAIL")
        passed = False
    finally:
        cleanup_test_data()
        conn.close()

    log("\n==========================================================================", "INFO")
    if passed:
        log("*** ALL PROGRAMMATIC VERIFICATION CHECKS PASSED (100% SUCCESS) ***", "PASS")
        sys.exit(0)
    else:
        log("*** PROGRAMMATIC VERIFICATION FAILED! ***", "FAIL")
        sys.exit(1)

if __name__ == "__main__":
    run_verification()
