"""
stress_test_attendance.py
Empirical Stress Test Harness & Boundary Verification for Attendance Control Tables.
Milestone 1: Database & Supabase Schema R1.

Target Tables:
1. tipos_maestro
2. maestros
3. obras_maestros
4. asistencia_diaria
5. asistencia_diaria_detalle

Tests:
1. Estado Asistencia Boundary Values (1.0, 0.5, 0.0 allowed; 0.8, -0.5, 2.0, 1.5 rejected).
2. RUT Unique Constraint & Boundary Handling (Duplicates, Case sensitivity 'K' vs 'k', Empty strings, NULLs).
3. FK Constraint Enforcement (RESTRICT on tipos_maestro and maestros; CASCADE on obras and asistencia_diaria header).
4. Composite Unique Constraints (obra_id + maestro_id, asistencia_diaria_id + maestro_id).
5. High-volume Batch Insertion Performance (100, 500, 1000, 5000 records performance metrics).
"""

import sys
import time
import uuid
import datetime
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "user": "postgres",
    "password": "1234",
    "dbname": "postgres"
}

class TestReporter:
    def __init__(self):
        self.results = []

    def add(self, suite, test_name, status, details, execution_time_ms=0.0):
        self.results.append({
            "suite": suite,
            "test_name": test_name,
            "status": status, # "PASS", "FAIL", "WARN"
            "details": details,
            "execution_time_ms": execution_time_ms
        })
        prefix = f"[{status}]"
        print(f"{prefix:<7} [{suite}] {test_name}: {details} ({execution_time_ms:.2f} ms)")

    def summary(self):
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        warned = sum(1 for r in self.results if r["status"] == "WARN")
        print("\n" + "="*80)
        print(f"STRESS TEST SUMMARY: Total={total} | PASSED={passed} | FAILED={failed} | WARNINGS={warned}")
        print("="*80)
        return passed, failed, warned


class AttendanceStressTester:
    def __init__(self, use_postgres=True):
        self.use_postgres = use_postgres
        self.reporter = TestReporter()
        if self.use_postgres:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.conn.autocommit = False
            self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
            self.engine_name = "PostgreSQL"
        else:
            self.conn = sqlite3.connect(":memory:")
            self.conn.execute("PRAGMA foreign_keys = ON;")
            self.cur = self.conn.cursor()
            self._create_sqlite_schema()
            self.engine_name = "SQLite (In-Memory Simulator)"

    def _create_sqlite_schema(self):
        cur = self.conn.cursor()
        cur.execute("CREATE TABLE perfiles_usuario (id TEXT PRIMARY KEY, nombre TEXT NOT NULL, rol TEXT NOT NULL);")
        cur.execute("CREATE TABLE obras (id TEXT PRIMARY KEY, nombre TEXT NOT NULL, estado TEXT DEFAULT 'Activa');")
        cur.execute("CREATE TABLE tipos_maestro (id TEXT PRIMARY KEY, nombre TEXT NOT NULL, sueldo_diario REAL NOT NULL DEFAULT 0.0, created_at TEXT DEFAULT (datetime('now')));")
        cur.execute("""
            CREATE TABLE maestros (
                id TEXT PRIMARY KEY,
                rut TEXT NOT NULL UNIQUE,
                nombre_completo TEXT NOT NULL,
                tipo_maestro_id TEXT,
                telefono TEXT,
                activo INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (tipo_maestro_id) REFERENCES tipos_maestro(id) ON DELETE RESTRICT
            );
        """)
        cur.execute("""
            CREATE TABLE obras_maestros (
                id TEXT PRIMARY KEY,
                obra_id TEXT NOT NULL,
                maestro_id TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (obra_id) REFERENCES obras(id) ON DELETE CASCADE,
                FOREIGN KEY (maestro_id) REFERENCES maestros(id) ON DELETE CASCADE,
                UNIQUE (obra_id, maestro_id)
            );
        """)
        cur.execute("""
            CREATE TABLE asistencia_diaria (
                id TEXT PRIMARY KEY,
                obra_id TEXT NOT NULL,
                fecha TEXT NOT NULL,
                foto_evidencia_url TEXT NOT NULL,
                es_correctivo INTEGER DEFAULT 0,
                registrado_por TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (obra_id) REFERENCES obras(id) ON DELETE CASCADE,
                FOREIGN KEY (registrado_por) REFERENCES perfiles_usuario(id) ON DELETE SET NULL
            );
        """)
        cur.execute("""
            CREATE TABLE asistencia_diaria_detalle (
                id TEXT PRIMARY KEY,
                asistencia_diaria_id TEXT NOT NULL,
                maestro_id TEXT NOT NULL,
                estado_asistencia REAL NOT NULL CHECK (estado_asistencia IN (1.0, 0.5, 0.0)),
                observaciones TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (asistencia_diaria_id) REFERENCES asistencia_diaria(id) ON DELETE CASCADE,
                FOREIGN KEY (maestro_id) REFERENCES maestros(id) ON DELETE RESTRICT,
                UNIQUE (asistencia_diaria_id, maestro_id)
            );
        """)
        self.conn.commit()

    def cleanup(self):
        if self.use_postgres:
            try:
                self.conn.rollback()
                cur = self.conn.cursor()
                cur.execute("""
                    DELETE FROM public.asistencia_diaria_detalle WHERE observaciones LIKE 'StressTest%';
                    DELETE FROM public.asistencia_diaria WHERE foto_evidencia_url LIKE '%stresstest%';
                    DELETE FROM public.maestros WHERE rut LIKE 'STRESS%' OR nombre_completo LIKE 'Stress%';
                    DELETE FROM public.obras WHERE nombre LIKE 'Stress%';
                    DELETE FROM public.perfiles_usuario WHERE nombre LIKE 'Stress%';
                    DELETE FROM public.tipos_maestro WHERE nombre LIKE 'Stress%';
                """)
                self.conn.commit()
            except Exception as e:
                self.conn.rollback()

    def close(self):
        self.cleanup()
        self.conn.close()

    # -------------------------------------------------------------------------
    # SUITE 1: Estado Asistencia Boundaries & Check Constraints
    # -------------------------------------------------------------------------
    def run_suite_1_estado_asistencia(self):
        suite = f"Suite 1 ({self.engine_name})"
        print(f"\n--- Running {suite}: Estado Asistencia Check Constraints ---")

        # Setup base objects
        obra_id = str(uuid.uuid4())
        tipo_id = str(uuid.uuid4())
        maestro_id = str(uuid.uuid4())
        ast_id = str(uuid.uuid4())

        t0 = time.perf_counter()
        if self.use_postgres:
            self.cur.execute("INSERT INTO public.obras (id, nombre) VALUES (%s, %s);", (obra_id, "Stress Obra 1"))
            self.cur.execute("INSERT INTO public.tipos_maestro (id, nombre, sueldo_diario) VALUES (%s, %s, %s);", (tipo_id, "Stress Tipo 1", 35000))
            self.cur.execute("INSERT INTO public.maestros (id, rut, nombre_completo, tipo_maestro_id) VALUES (%s, %s, %s, %s);",
                             (maestro_id, "STRESS-RUT-1", "Stress Maestro 1", tipo_id))
            self.cur.execute("INSERT INTO public.asistencia_diaria (id, obra_id, fecha, foto_evidencia_url) VALUES (%s, %s, %s, %s);",
                             (ast_id, obra_id, "2026-07-29", "http://stresstest.jpg"))
        else:
            self.cur.execute("INSERT INTO obras (id, nombre) VALUES (?, ?);", (obra_id, "Stress Obra 1"))
            self.cur.execute("INSERT INTO tipos_maestro (id, nombre, sueldo_diario) VALUES (?, ?, ?);", (tipo_id, "Stress Tipo 1", 35000))
            self.cur.execute("INSERT INTO maestros (id, rut, nombre_completo, tipo_maestro_id) VALUES (?, ?, ?, ?);",
                             (maestro_id, "STRESS-RUT-1", "Stress Maestro 1", tipo_id))
            self.cur.execute("INSERT INTO asistencia_diaria (id, obra_id, fecha, foto_evidencia_url) VALUES (?, ?, ?, ?);",
                             (ast_id, obra_id, "2026-07-29", "http://stresstest.jpg"))
        self.conn.commit()

        # 1. Valid values (1.0, 0.5, 0.0)
        valid_values = [1.0, 0.5, 0.0]
        for val in valid_values:
            t_start = time.perf_counter()
            det_id = str(uuid.uuid4())
            # We need unique maestro_id per detail for the header, so seed extra maestros
            sub_m_id = str(uuid.uuid4())
            sub_rut = f"STRESS-VALID-{val}"
            try:
                if self.use_postgres:
                    self.cur.execute("INSERT INTO public.maestros (id, rut, nombre_completo, tipo_maestro_id) VALUES (%s, %s, %s, %s);",
                                     (sub_m_id, sub_rut, f"Maestro {val}", tipo_id))
                    self.cur.execute("INSERT INTO public.asistencia_diaria_detalle (id, asistencia_diaria_id, maestro_id, estado_asistencia, observaciones) VALUES (%s, %s, %s, %s, %s);",
                                     (det_id, ast_id, sub_m_id, val, "StressTest Valid"))
                else:
                    self.cur.execute("INSERT INTO maestros (id, rut, nombre_completo, tipo_maestro_id) VALUES (?, ?, ?, ?);",
                                     (sub_m_id, sub_rut, f"Maestro {val}", tipo_id))
                    self.cur.execute("INSERT INTO asistencia_diaria_detalle (id, asistencia_diaria_id, maestro_id, estado_asistencia, observaciones) VALUES (?, ?, ?, ?, ?);",
                                     (det_id, ast_id, sub_m_id, val, "StressTest Valid"))
                self.conn.commit()
                t_dur = (time.perf_counter() - t_start) * 1000
                self.reporter.add(suite, f"Valid Value {val}", "PASS", f"Accepted state {val}", t_dur)
            except Exception as e:
                self.conn.rollback()
                t_dur = (time.perf_counter() - t_start) * 1000
                self.reporter.add(suite, f"Valid Value {val}", "FAIL", f"Unexpected rejection: {e}", t_dur)

        # 2. Invalid boundary values (0.8, -0.5, 2.0, 1.5, 0.001)
        invalid_values = [0.8, -0.5, 2.0, 1.5, 0.001, -1.0, 99.0]
        for val in invalid_values:
            t_start = time.perf_counter()
            sub_m_id = str(uuid.uuid4())
            sub_rut = f"STRESS-INVALID-{val}"
            det_id = str(uuid.uuid4())

            if self.use_postgres:
                self.cur.execute("SAVEPOINT invalid_val_sp;")
            rejected = False
            err_msg = ""
            try:
                if self.use_postgres:
                    self.cur.execute("INSERT INTO public.maestros (id, rut, nombre_completo, tipo_maestro_id) VALUES (%s, %s, %s, %s);",
                                     (sub_m_id, sub_rut, f"Maestro Invalid {val}", tipo_id))
                    self.cur.execute("INSERT INTO public.asistencia_diaria_detalle (id, asistencia_diaria_id, maestro_id, estado_asistencia, observaciones) VALUES (%s, %s, %s, %s, %s);",
                                     (det_id, ast_id, sub_m_id, val, "StressTest Invalid"))
                else:
                    self.cur.execute("INSERT INTO maestros (id, rut, nombre_completo, tipo_maestro_id) VALUES (?, ?, ?, ?);",
                                     (sub_m_id, sub_rut, f"Maestro Invalid {val}", tipo_id))
                    self.cur.execute("INSERT INTO asistencia_diaria_detalle (id, asistencia_diaria_id, maestro_id, estado_asistencia, observaciones) VALUES (?, ?, ?, ?, ?);",
                                     (det_id, ast_id, sub_m_id, val, "StressTest Invalid"))
                self.conn.commit()
            except (psycopg2.IntegrityError, sqlite3.IntegrityError) as e:
                rejected = True
                err_msg = str(e).strip()
                if self.use_postgres:
                    self.cur.execute("ROLLBACK TO SAVEPOINT invalid_val_sp;")
                else:
                    self.conn.rollback()

            t_dur = (time.perf_counter() - t_start) * 1000
            if rejected:
                self.reporter.add(suite, f"Invalid Value {val}", "PASS", f"Rejected as expected by CHECK constraint", t_dur)
            else:
                self.reporter.add(suite, f"Invalid Value {val}", "FAIL", f"CRITICAL: Invalid value {val} WAS ACCEPTED by database!", t_dur)

    # -------------------------------------------------------------------------
    # SUITE 2: RUT Duplicate & Formatting Boundary Handling
    # -------------------------------------------------------------------------
    def run_suite_2_rut_boundaries(self):
        suite = f"Suite 2 ({self.engine_name})"
        print(f"\n--- Running {suite}: RUT Boundary & Unique Constraint Handling ---")

        tipo_id = str(uuid.uuid4())
        if self.use_postgres:
            self.cur.execute("INSERT INTO public.tipos_maestro (id, nombre, sueldo_diario) VALUES (%s, %s, %s);", (tipo_id, "Stress Tipo RUT", 40000))
        else:
            self.cur.execute("INSERT INTO tipos_maestro (id, nombre, sueldo_diario) VALUES (?, ?, ?);", (tipo_id, "Stress Tipo RUT", 40000))
        self.conn.commit()

        # 1. Exact Duplicate RUT
        base_rut = "12.345.678-K"
        m1_id = str(uuid.uuid4())
        t_start = time.perf_counter()
        if self.use_postgres:
            self.cur.execute("INSERT INTO public.maestros (id, rut, nombre_completo, tipo_maestro_id) VALUES (%s, %s, %s, %s);",
                             (m1_id, base_rut, "Stress Maestro Base RUT", tipo_id))
        else:
            self.cur.execute("INSERT INTO maestros (id, rut, nombre_completo, tipo_maestro_id) VALUES (?, ?, ?, ?);",
                             (m1_id, base_rut, "Stress Maestro Base RUT", tipo_id))
        self.conn.commit()

        m2_id = str(uuid.uuid4())
        if self.use_postgres:
            self.cur.execute("SAVEPOINT dup_rut_sp;")
        dup_rejected = False
        try:
            if self.use_postgres:
                self.cur.execute("INSERT INTO public.maestros (id, rut, nombre_completo, tipo_maestro_id) VALUES (%s, %s, %s, %s);",
                                 (m2_id, base_rut, "Stress Maestro Dup RUT", tipo_id))
            else:
                self.cur.execute("INSERT INTO maestros (id, rut, nombre_completo, tipo_maestro_id) VALUES (?, ?, ?, ?);",
                                 (m2_id, base_rut, "Stress Maestro Dup RUT", tipo_id))
            self.conn.commit()
        except (psycopg2.IntegrityError, sqlite3.IntegrityError):
            dup_rejected = True
            if self.use_postgres:
                self.cur.execute("ROLLBACK TO SAVEPOINT dup_rut_sp;")
            else:
                self.conn.rollback()

        t_dur = (time.perf_counter() - t_start) * 1000
        if dup_rejected:
            self.reporter.add(suite, "Duplicate Exact RUT", "PASS", f"Duplicate RUT '{base_rut}' rejected by UNIQUE constraint", t_dur)
        else:
            self.reporter.add(suite, "Duplicate Exact RUT", "FAIL", f"Duplicate RUT '{base_rut}' WAS ALLOWED!", t_dur)

        # 2. Case Sensitivity Test: Lowercase 'k' vs Uppercase 'K'
        lower_k_rut = "12.345.678-k"
        m3_id = str(uuid.uuid4())
        if self.use_postgres:
            self.cur.execute("SAVEPOINT case_rut_sp;")
        case_rejected = False
        try:
            if self.use_postgres:
                self.cur.execute("INSERT INTO public.maestros (id, rut, nombre_completo, tipo_maestro_id) VALUES (%s, %s, %s, %s);",
                                 (m3_id, lower_k_rut, "Stress Maestro Lowercase k", tipo_id))
            else:
                self.cur.execute("INSERT INTO maestros (id, rut, nombre_completo, tipo_maestro_id) VALUES (?, ?, ?, ?);",
                                 (m3_id, lower_k_rut, "Stress Maestro Lowercase k", tipo_id))
            self.conn.commit()
        except (psycopg2.IntegrityError, sqlite3.IntegrityError):
            case_rejected = True
            if self.use_postgres:
                self.cur.execute("ROLLBACK TO SAVEPOINT case_rut_sp;")
            else:
                self.conn.rollback()

        if case_rejected:
            self.reporter.add(suite, "RUT Case Insensitivity", "PASS", "DB rejected '12.345.678-k' as duplicate of '12.345.678-K'", 0.0)
        else:
            self.reporter.add(suite, "RUT Case Sensitivity Warning", "WARN", "FINDING: Standard UNIQUE index allows both '12.345.678-K' and '12.345.678-k' because standard text unique constraint is case-sensitive!", 0.0)

        # 3. Format Variation: Unformatted '12345678-K' vs Formatted '12.345.678-K'
        unformatted_rut = "12345678-K"
        m4_id = str(uuid.uuid4())
        if self.use_postgres:
            self.cur.execute("SAVEPOINT format_rut_sp;")
        fmt_rejected = False
        try:
            if self.use_postgres:
                self.cur.execute("INSERT INTO public.maestros (id, rut, nombre_completo, tipo_maestro_id) VALUES (%s, %s, %s, %s);",
                                 (m4_id, unformatted_rut, "Stress Maestro Unformatted", tipo_id))
            else:
                self.cur.execute("INSERT INTO maestros (id, rut, nombre_completo, tipo_maestro_id) VALUES (?, ?, ?, ?);",
                                 (m4_id, unformatted_rut, "Stress Maestro Unformatted", tipo_id))
            self.conn.commit()
        except (psycopg2.IntegrityError, sqlite3.IntegrityError):
            fmt_rejected = True
            if self.use_postgres:
                self.cur.execute("ROLLBACK TO SAVEPOINT format_rut_sp;")
            else:
                self.conn.rollback()

        if fmt_rejected:
            self.reporter.add(suite, "Unformatted RUT Rejection", "PASS", "Database rejected unformatted RUT", 0.0)
        else:
            self.reporter.add(suite, "Unformatted RUT Coexistence", "WARN", "FINDING: Database accepts unformatted RUT '12345678-K' alongside formatted '12.345.678-K' (RUT formatting must be enforced at application or domain layer)", 0.0)

        # 4. Empty String RUT ""
        empty_rut = ""
        m5_id = str(uuid.uuid4())
        if self.use_postgres:
            self.cur.execute("SAVEPOINT empty_rut_sp;")
        empty_rejected = False
        try:
            if self.use_postgres:
                self.cur.execute("INSERT INTO public.maestros (id, rut, nombre_completo, tipo_maestro_id) VALUES (%s, %s, %s, %s);",
                                 (m5_id, empty_rut, "Stress Maestro Empty RUT", tipo_id))
            else:
                self.cur.execute("INSERT INTO maestros (id, rut, nombre_completo, tipo_maestro_id) VALUES (?, ?, ?, ?);",
                                 (m5_id, empty_rut, "Stress Maestro Empty RUT", tipo_id))
            self.conn.commit()
        except (psycopg2.IntegrityError, sqlite3.IntegrityError):
            empty_rejected = True
            if self.use_postgres:
                self.cur.execute("ROLLBACK TO SAVEPOINT empty_rut_sp;")
            else:
                self.conn.rollback()

        if empty_rejected:
            self.reporter.add(suite, "Empty String RUT Rejection", "PASS", "Empty string RUT rejected", 0.0)
        else:
            self.reporter.add(suite, "Empty String RUT Acceptance", "WARN", "FINDING: Empty string '' is allowed by database on RUT column (requires CHECK (length(rut) >= 8) or app validation)", 0.0)

        # 5. NULL RUT Violation
        m6_id = str(uuid.uuid4())
        if self.use_postgres:
            self.cur.execute("SAVEPOINT null_rut_sp;")
        null_rejected = False
        try:
            if self.use_postgres:
                self.cur.execute("INSERT INTO public.maestros (id, rut, nombre_completo, tipo_maestro_id) VALUES (%s, %s, %s, %s);",
                                 (m6_id, None, "Stress Maestro NULL RUT", tipo_id))
            else:
                self.cur.execute("INSERT INTO maestros (id, rut, nombre_completo, tipo_maestro_id) VALUES (?, ?, ?, ?);",
                                 (m6_id, None, "Stress Maestro NULL RUT", tipo_id))
            self.conn.commit()
        except (psycopg2.IntegrityError, sqlite3.IntegrityError):
            null_rejected = True
            if self.use_postgres:
                self.cur.execute("ROLLBACK TO SAVEPOINT null_rut_sp;")
            else:
                self.conn.rollback()

        if null_rejected:
            self.reporter.add(suite, "NULL RUT Rejection", "PASS", "NULL RUT rejected by NOT NULL constraint", 0.0)
        else:
            self.reporter.add(suite, "NULL RUT Rejection", "FAIL", "CRITICAL: NULL RUT WAS ACCEPTED!", 0.0)

    # -------------------------------------------------------------------------
    # SUITE 3: Foreign Key Constraints & Cascade/Restrict Enforcement
    # -------------------------------------------------------------------------
    def run_suite_3_fk_enforcement(self):
        suite = f"Suite 3 ({self.engine_name})"
        print(f"\n--- Running {suite}: Foreign Key RESTRICT & CASCADE Enforcement ---")

        # Setup FK hierarchy: Obra -> AsistenciaDiaria -> AsistenciaDiariaDetalle
        #                     TipoMaestro -> Maestro -> (ObrasMaestros, AsistenciaDiariaDetalle)
        obra_id = str(uuid.uuid4())
        tipo_id = str(uuid.uuid4())
        maestro_id = str(uuid.uuid4())
        ast_id = str(uuid.uuid4())
        det_id = str(uuid.uuid4())
        om_id = str(uuid.uuid4())

        if self.use_postgres:
            self.cur.execute("INSERT INTO public.obras (id, nombre) VALUES (%s, %s);", (obra_id, "Stress Obra FK"))
            self.cur.execute("INSERT INTO public.tipos_maestro (id, nombre, sueldo_diario) VALUES (%s, %s, %s);", (tipo_id, "Stress Tipo FK", 50000))
            self.cur.execute("INSERT INTO public.maestros (id, rut, nombre_completo, tipo_maestro_id) VALUES (%s, %s, %s, %s);",
                             (maestro_id, "STRESS-FK-RUT", "Stress Maestro FK", tipo_id))
            self.cur.execute("INSERT INTO public.obras_maestros (id, obra_id, maestro_id) VALUES (%s, %s, %s);", (om_id, obra_id, maestro_id))
            self.cur.execute("INSERT INTO public.asistencia_diaria (id, obra_id, fecha, foto_evidencia_url) VALUES (%s, %s, %s, %s);",
                             (ast_id, obra_id, "2026-07-29", "http://stresstest_fk.jpg"))
            self.cur.execute("INSERT INTO public.asistencia_diaria_detalle (id, asistencia_diaria_id, maestro_id, estado_asistencia, observaciones) VALUES (%s, %s, %s, %s, %s);",
                             (det_id, ast_id, maestro_id, 1.0, "StressTest FK"))
        else:
            self.cur.execute("INSERT INTO obras (id, nombre) VALUES (?, ?);", (obra_id, "Stress Obra FK"))
            self.cur.execute("INSERT INTO tipos_maestro (id, nombre, sueldo_diario) VALUES (?, ?, ?);", (tipo_id, "Stress Tipo FK", 50000))
            self.cur.execute("INSERT INTO maestros (id, rut, nombre_completo, tipo_maestro_id) VALUES (?, ?, ?, ?);",
                             (maestro_id, "STRESS-FK-RUT", "Stress Maestro FK", tipo_id))
            self.cur.execute("INSERT INTO obras_maestros (id, obra_id, maestro_id) VALUES (?, ?, ?);", (om_id, obra_id, maestro_id))
            self.cur.execute("INSERT INTO asistencia_diaria (id, obra_id, fecha, foto_evidencia_url) VALUES (?, ?, ?, ?);",
                             (ast_id, obra_id, "2026-07-29", "http://stresstest_fk.jpg"))
            self.cur.execute("INSERT INTO asistencia_diaria_detalle (id, asistencia_diaria_id, maestro_id, estado_asistencia, observaciones) VALUES (?, ?, ?, ?, ?);",
                             (det_id, ast_id, maestro_id, 1.0, "StressTest FK"))
        self.conn.commit()

        # 3A: ON DELETE RESTRICT on tipos_maestro
        if self.use_postgres:
            self.cur.execute("SAVEPOINT del_tipo_sp;")
        del_tipo_blocked = False
        try:
            if self.use_postgres:
                self.cur.execute("DELETE FROM public.tipos_maestro WHERE id = %s;", (tipo_id,))
            else:
                self.cur.execute("DELETE FROM tipos_maestro WHERE id = ?;", (tipo_id,))
            self.conn.commit()
        except (psycopg2.IntegrityError, sqlite3.IntegrityError):
            del_tipo_blocked = True
            if self.use_postgres:
                self.cur.execute("ROLLBACK TO SAVEPOINT del_tipo_sp;")
            else:
                self.conn.rollback()

        if del_tipo_blocked:
            self.reporter.add(suite, "ON DELETE RESTRICT (tipos_maestro)", "PASS", "Deletion of referenced tipos_maestro prevented by RESTRICT rule", 0.0)
        else:
            self.reporter.add(suite, "ON DELETE RESTRICT (tipos_maestro)", "FAIL", "CRITICAL: Referenced tipos_maestro WAS DELETED!", 0.0)

        # 3B: ON DELETE RESTRICT on maestros (when referenced by asistencia_diaria_detalle)
        if self.use_postgres:
            self.cur.execute("SAVEPOINT del_maestro_sp;")
        del_maestro_blocked = False
        try:
            if self.use_postgres:
                self.cur.execute("DELETE FROM public.maestros WHERE id = %s;", (maestro_id,))
            else:
                self.cur.execute("DELETE FROM maestros WHERE id = ?;", (maestro_id,))
            self.conn.commit()
        except (psycopg2.IntegrityError, sqlite3.IntegrityError):
            del_maestro_blocked = True
            if self.use_postgres:
                self.cur.execute("ROLLBACK TO SAVEPOINT del_maestro_sp;")
            else:
                self.conn.rollback()

        if del_maestro_blocked:
            self.reporter.add(suite, "ON DELETE RESTRICT (maestros -> detalle)", "PASS", "Deletion of referenced maestro prevented by RESTRICT rule in asistencia_diaria_detalle", 0.0)
        else:
            self.reporter.add(suite, "ON DELETE RESTRICT (maestros -> detalle)", "FAIL", "CRITICAL: Referenced maestro WAS DELETED despite RESTRICT rule!", 0.0)

        # 3C: ON DELETE CASCADE on asistencia_diaria -> asistencia_diaria_detalle
        t_start = time.perf_counter()
        if self.use_postgres:
            self.cur.execute("DELETE FROM public.asistencia_diaria WHERE id = %s;", (ast_id,))
        else:
            self.cur.execute("DELETE FROM asistencia_diaria WHERE id = ?;", (ast_id,))
        self.conn.commit()

        # Verify detail row was cascade-deleted
        if self.use_postgres:
            self.cur.execute("SELECT count(*) AS cnt FROM public.asistencia_diaria_detalle WHERE id = %s;", (det_id,))
            cnt = self.cur.fetchone()['cnt']
        else:
            self.cur.execute("SELECT count(*) FROM asistencia_diaria_detalle WHERE id = ?;", (det_id,))
            cnt = self.cur.fetchone()[0]

        t_dur = (time.perf_counter() - t_start) * 1000
        if cnt == 0:
            self.reporter.add(suite, "ON DELETE CASCADE (asistencia_diaria -> detalle)", "PASS", "Header deletion automatically cascade deleted dependent detail row", t_dur)
        else:
            self.reporter.add(suite, "ON DELETE CASCADE (asistencia_diaria -> detalle)", "FAIL", "CRITICAL: Dependent detail row was NOT deleted!", t_dur)

        # 3D: Deleting maestro when ONLY referenced by obras_maestros (ON DELETE CASCADE)
        # Now that asistencia_diaria_detalle reference is removed (via 3C cascade delete above), deleting maestro should succeed and cascade-delete obras_maestros
        t_start = time.perf_counter()
        if self.use_postgres:
            self.cur.execute("DELETE FROM public.maestros WHERE id = %s;", (maestro_id,))
        else:
            self.cur.execute("DELETE FROM maestros WHERE id = ?;", (maestro_id,))
        self.conn.commit()

        if self.use_postgres:
            self.cur.execute("SELECT count(*) AS cnt FROM public.obras_maestros WHERE id = %s;", (om_id,))
            om_cnt = self.cur.fetchone()['cnt']
        else:
            self.cur.execute("SELECT count(*) FROM obras_maestros WHERE id = ?;", (om_id,))
            om_cnt = self.cur.fetchone()[0]

        t_dur = (time.perf_counter() - t_start) * 1000
        if om_cnt == 0:
            self.reporter.add(suite, "ON DELETE CASCADE (maestros -> obras_maestros)", "PASS", "Maestro deletion succeeded and cascade-deleted obras_maestros junction row", t_dur)
        else:
            self.reporter.add(suite, "ON DELETE CASCADE (maestros -> obras_maestros)", "FAIL", "CRITICAL: obras_maestros row was NOT deleted!", t_dur)

        # 3E: ON DELETE CASCADE on obras -> (asistencia_diaria, obras_maestros)
        # Create fresh header and junction row under obra_id, then delete obra_id
        m_temp = str(uuid.uuid4())
        ast_temp = str(uuid.uuid4())
        if self.use_postgres:
            self.cur.execute("INSERT INTO public.maestros (id, rut, nombre_completo, tipo_maestro_id) VALUES (%s, %s, %s, %s);",
                             (m_temp, "STRESS-TEMP-1", "Temp Maestro", tipo_id))
            self.cur.execute("INSERT INTO public.asistencia_diaria (id, obra_id, fecha, foto_evidencia_url) VALUES (%s, %s, %s, %s);",
                             (ast_temp, obra_id, "2026-07-29", "http://temp.jpg"))
            self.cur.execute("DELETE FROM public.obras WHERE id = %s;", (obra_id,))
            self.conn.commit()
            self.cur.execute("SELECT count(*) AS cnt FROM public.asistencia_diaria WHERE id = %s;", (ast_temp,))
            ast_cnt = self.cur.fetchone()['cnt']
        else:
            self.cur.execute("INSERT INTO maestros (id, rut, nombre_completo, tipo_maestro_id) VALUES (?, ?, ?, ?);",
                             (m_temp, "STRESS-TEMP-1", "Temp Maestro", tipo_id))
            self.cur.execute("INSERT INTO asistencia_diaria (id, obra_id, fecha, foto_evidencia_url) VALUES (?, ?, ?, ?);",
                             (ast_temp, obra_id, "2026-07-29", "http://temp.jpg"))
            self.cur.execute("DELETE FROM obras WHERE id = ?;", (obra_id,))
            self.conn.commit()
            self.cur.execute("SELECT count(*) FROM asistencia_diaria WHERE id = ?;", (ast_temp,))
            ast_cnt = self.cur.fetchone()[0]

        if ast_cnt == 0:
            self.reporter.add(suite, "ON DELETE CASCADE (obras -> asistencia_diaria)", "PASS", "Obra deletion cascade-deleted dependent asistencia_diaria headers", 0.0)
        else:
            self.reporter.add(suite, "ON DELETE CASCADE (obras -> asistencia_diaria)", "FAIL", "CRITICAL: Dependent asistencia_diaria was NOT deleted!", 0.0)

    # -------------------------------------------------------------------------
    # SUITE 4: Composite Unique Constraints
    # -------------------------------------------------------------------------
    def run_suite_4_composite_uniques(self):
        suite = f"Suite 4 ({self.engine_name})"
        print(f"\n--- Running {suite}: Composite Unique Constraints ---")

        obra_id = str(uuid.uuid4())
        tipo_id = str(uuid.uuid4())
        m_id = str(uuid.uuid4())
        ast_id = str(uuid.uuid4())

        if self.use_postgres:
            self.cur.execute("INSERT INTO public.obras (id, nombre) VALUES (%s, %s);", (obra_id, "Stress Obra Unique"))
            self.cur.execute("INSERT INTO public.tipos_maestro (id, nombre, sueldo_diario) VALUES (%s, %s, %s);", (tipo_id, "Stress Tipo Unique", 45000))
            self.cur.execute("INSERT INTO public.maestros (id, rut, nombre_completo, tipo_maestro_id) VALUES (%s, %s, %s, %s);",
                             (m_id, "STRESS-UQ-RUT", "Stress Maestro Unique", tipo_id))
            self.cur.execute("INSERT INTO public.asistencia_diaria (id, obra_id, fecha, foto_evidencia_url) VALUES (%s, %s, %s, %s);",
                             (ast_id, obra_id, "2026-07-29", "http://uq.jpg"))
            self.cur.execute("INSERT INTO public.obras_maestros (id, obra_id, maestro_id) VALUES (%s, %s, %s);",
                             (str(uuid.uuid4()), obra_id, m_id))
            self.conn.commit()
        else:
            self.cur.execute("INSERT INTO obras (id, nombre) VALUES (?, ?);", (obra_id, "Stress Obra Unique"))
            self.cur.execute("INSERT INTO tipos_maestro (id, nombre, sueldo_diario) VALUES (?, ?, ?);", (tipo_id, "Stress Tipo Unique", 45000))
            self.cur.execute("INSERT INTO maestros (id, rut, nombre_completo, tipo_maestro_id) VALUES (?, ?, ?, ?);",
                             (m_id, "STRESS-UQ-RUT", "Stress Maestro Unique", tipo_id))
            self.cur.execute("INSERT INTO asistencia_diaria (id, obra_id, fecha, foto_evidencia_url) VALUES (?, ?, ?, ?);",
                             (ast_id, obra_id, "2026-07-29", "http://uq.jpg"))
            self.cur.execute("INSERT INTO obras_maestros (id, obra_id, maestro_id) VALUES (?, ?, ?);",
                             (str(uuid.uuid4()), obra_id, m_id))
            self.conn.commit()

        # 4A: Unique (obra_id, maestro_id) in obras_maestros
        if self.use_postgres:
            self.cur.execute("SAVEPOINT uq_om_sp;")
        om_dup_rejected = False
        try:
            if self.use_postgres:
                self.cur.execute("INSERT INTO public.obras_maestros (id, obra_id, maestro_id) VALUES (%s, %s, %s);",
                                 (str(uuid.uuid4()), obra_id, m_id))
            else:
                self.cur.execute("INSERT INTO obras_maestros (id, obra_id, maestro_id) VALUES (?, ?, ?);",
                                 (str(uuid.uuid4()), obra_id, m_id))
            self.conn.commit()
        except (psycopg2.IntegrityError, sqlite3.IntegrityError):
            om_dup_rejected = True
            if self.use_postgres:
                self.cur.execute("ROLLBACK TO SAVEPOINT uq_om_sp;")
            else:
                self.conn.rollback()

        if om_dup_rejected:
            self.reporter.add(suite, "UNIQUE (obra_id, maestro_id)", "PASS", "Duplicate obra_maestro assignment rejected", 0.0)
        else:
            self.reporter.add(suite, "UNIQUE (obra_id, maestro_id)", "FAIL", "CRITICAL: Duplicate assignment WAS ALLOWED!", 0.0)

        # 4B: Unique (asistencia_diaria_id, maestro_id) in asistencia_diaria_detalle
        d1_id = str(uuid.uuid4())
        if self.use_postgres:
            self.cur.execute("INSERT INTO public.asistencia_diaria_detalle (id, asistencia_diaria_id, maestro_id, estado_asistencia, observaciones) VALUES (%s, %s, %s, %s, %s);",
                             (d1_id, ast_id, m_id, 1.0, "StressTest UQ 1"))
            self.conn.commit()
            self.cur.execute("SAVEPOINT uq_det_sp;")
        else:
            self.cur.execute("INSERT INTO asistencia_diaria_detalle (id, asistencia_diaria_id, maestro_id, estado_asistencia, observaciones) VALUES (?, ?, ?, ?, ?);",
                             (d1_id, ast_id, m_id, 1.0, "StressTest UQ 1"))
            self.conn.commit()

        det_dup_rejected = False
        try:
            if self.use_postgres:
                self.cur.execute("INSERT INTO public.asistencia_diaria_detalle (id, asistencia_diaria_id, maestro_id, estado_asistencia, observaciones) VALUES (%s, %s, %s, %s, %s);",
                                 (str(uuid.uuid4()), ast_id, m_id, 0.5, "StressTest UQ 2"))
            else:
                self.cur.execute("INSERT INTO asistencia_diaria_detalle (id, asistencia_diaria_id, maestro_id, estado_asistencia, observaciones) VALUES (?, ?, ?, ?, ?);",
                                 (str(uuid.uuid4()), ast_id, m_id, 0.5, "StressTest UQ 2"))
            self.conn.commit()
        except (psycopg2.IntegrityError, sqlite3.IntegrityError):
            det_dup_rejected = True
            if self.use_postgres:
                self.cur.execute("ROLLBACK TO SAVEPOINT uq_det_sp;")
            else:
                self.conn.rollback()

        if det_dup_rejected:
            self.reporter.add(suite, "UNIQUE (asistencia_diaria_id, maestro_id)", "PASS", "Duplicate detail row for same maestro in same attendance header rejected", 0.0)
        else:
            self.reporter.add(suite, "UNIQUE (asistencia_diaria_id, maestro_id)", "FAIL", "CRITICAL: Duplicate detail row WAS ALLOWED!", 0.0)

    # -------------------------------------------------------------------------
    # SUITE 5: Batch Record Insertion Performance Benchmark
    # -------------------------------------------------------------------------
    def run_suite_5_batch_performance(self):
        suite = f"Suite 5 ({self.engine_name})"
        print(f"\n--- Running {suite}: Batch Insertion Performance Benchmarks ---")

        # Setup Obra, TipoMaestro, and Attendance Header
        obra_id = str(uuid.uuid4())
        tipo_id = str(uuid.uuid4())
        ast_id = str(uuid.uuid4())

        if self.use_postgres:
            self.cur.execute("INSERT INTO public.obras (id, nombre) VALUES (%s, %s);", (obra_id, "Stress Obra Batch"))
            self.cur.execute("INSERT INTO public.tipos_maestro (id, nombre, sueldo_diario) VALUES (%s, %s, %s);", (tipo_id, "Stress Tipo Batch", 30000))
            self.cur.execute("INSERT INTO public.asistencia_diaria (id, obra_id, fecha, foto_evidencia_url) VALUES (%s, %s, %s, %s);",
                             (ast_id, obra_id, "2026-07-29", "http://batch.jpg"))
            self.conn.commit()
        else:
            self.cur.execute("INSERT INTO obras (id, nombre) VALUES (?, ?);", (obra_id, "Stress Obra Batch"))
            self.cur.execute("INSERT INTO tipos_maestro (id, nombre, sueldo_diario) VALUES (?, ?, ?);", (tipo_id, "Stress Tipo Batch", 30000))
            self.cur.execute("INSERT INTO asistencia_diaria (id, obra_id, fecha, foto_evidencia_url) VALUES (?, ?, ?, ?);",
                             (ast_id, obra_id, "2026-07-29", "http://batch.jpg"))
            self.conn.commit()

        batch_sizes = [100, 500, 1000, 5000]

        for size in batch_sizes:
            # 1. Seed `size` maestros first
            maestro_rows = []
            maestro_ids = []
            for i in range(size):
                m_id = str(uuid.uuid4())
                maestro_ids.append(m_id)
                rut = f"STRESS-B{size}-{i:05d}"
                name = f"Stress Worker B{size}-{i}"
                if self.use_postgres:
                    maestro_rows.append((m_id, rut, name, tipo_id))
                else:
                    maestro_rows.append((m_id, rut, name, tipo_id))

            # Batch insert maestros
            t_m_start = time.perf_counter()
            if self.use_postgres:
                execute_values(self.cur, """
                    INSERT INTO public.maestros (id, rut, nombre_completo, tipo_maestro_id)
                    VALUES %s;
                """, maestro_rows)
            else:
                self.cur.executemany("""
                    INSERT INTO maestros (id, rut, nombre_completo, tipo_maestro_id)
                    VALUES (?, ?, ?, ?);
                """, maestro_rows)
            self.conn.commit()
            t_m_dur = (time.perf_counter() - t_m_start) * 1000

            # 2. Build detail rows
            detail_rows = []
            states = [1.0, 0.5, 0.0]
            for i, m_id in enumerate(maestro_ids):
                det_id = str(uuid.uuid4())
                st = states[i % 3]
                obs = f"StressTest Batch {size} item {i}"
                detail_rows.append((det_id, ast_id, m_id, st, obs))

            # Benchmark batch insertion of detail rows
            t_det_start = time.perf_counter()
            if self.use_postgres:
                execute_values(self.cur, """
                    INSERT INTO public.asistencia_diaria_detalle (id, asistencia_diaria_id, maestro_id, estado_asistencia, observaciones)
                    VALUES %s;
                """, detail_rows)
            else:
                self.cur.executemany("""
                    INSERT INTO asistencia_diaria_detalle (id, asistencia_diaria_id, maestro_id, estado_asistencia, observaciones)
                    VALUES (?, ?, ?, ?, ?);
                """, detail_rows)
            self.conn.commit()
            t_det_dur = (time.perf_counter() - t_det_start) * 1000

            rec_per_sec = (size / t_det_dur) * 1000 if t_det_dur > 0 else 0
            details = f"Inserted {size} detail rows in {t_det_dur:.2f} ms ({rec_per_sec:.0f} rows/sec). Maestro seed: {t_m_dur:.2f} ms"
            self.reporter.add(suite, f"Batch Insert {size} Detail Rows", "PASS", details, t_det_dur)


def run_all_stress_tests():
    print("="*80)
    print("STARTING EMPIRICAL STRESS TEST SUITE FOR R1 ATTENDANCE CONTROL TABLES")
    print("="*80)

    # 1. Run against PostgreSQL
    pg_tester = None
    try:
        pg_tester = AttendanceStressTester(use_postgres=True)
        pg_tester.cleanup()
        pg_tester.run_suite_1_estado_asistencia()
        pg_tester.run_suite_2_rut_boundaries()
        pg_tester.run_suite_3_fk_enforcement()
        pg_tester.run_suite_4_composite_uniques()
        pg_tester.run_suite_5_batch_performance()
        pg_passed, pg_failed, pg_warn = pg_tester.reporter.summary()
    except Exception as e:
        print(f"\n[ERROR] PostgreSQL Stress Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        pg_passed, pg_failed, pg_warn = 0, 1, 0
    finally:
        if pg_tester:
            pg_tester.close()

    # 2. Run against SQLite Simulator
    print("\n" + "="*80)
    print("RUNNING IN-MEMORY SQLITE SIMULATOR STRESS SUITE")
    print("="*80)
    sq_tester = None
    try:
        sq_tester = AttendanceStressTester(use_postgres=False)
        sq_tester.run_suite_1_estado_asistencia()
        sq_tester.run_suite_2_rut_boundaries()
        sq_tester.run_suite_3_fk_enforcement()
        sq_tester.run_suite_4_composite_uniques()
        sq_tester.run_suite_5_batch_performance()
        sq_passed, sq_failed, sq_warn = sq_tester.reporter.summary()
    except Exception as e:
        print(f"\n[ERROR] SQLite Stress Test failed with exception: {e}")
        sq_passed, sq_failed, sq_warn = 0, 1, 0
    finally:
        if sq_tester:
            sq_tester.close()

    return (pg_passed, pg_failed, pg_warn), (sq_passed, sq_failed, sq_warn)

if __name__ == "__main__":
    run_all_stress_tests()
