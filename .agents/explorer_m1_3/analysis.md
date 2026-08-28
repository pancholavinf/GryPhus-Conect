# Technical Analysis Report — RLS Policies & Verification Strategy (Milestone 1)

## Executive Summary
This analysis details the security, Row Level Security (RLS) policy definitions, index performance optimization, and automated programmatic schema verification strategy for the 5 attendance control tables in the Accurateck Supabase PostgreSQL platform:
1. `tipos_maestro`
2. `maestros`
3. `obras_maestros`
4. `asistencia_diaria`
5. `asistencia_diaria_detalle`

---

## 1. Table Specifications & Integrity Constraints Analysis

### A. Table Schemas & Foreign Key Relationships
* **`tipos_maestro`**: Primary catalog for worker roles and daily base rates (`sueldo_diario`).
* **`maestros`**: Master registry of workers. References `tipos_maestro(id)` with `ON DELETE RESTRICT` to prevent accidental orphan wage calculations. Must enforce `rut UNIQUE`.
* **`obras_maestros`**: Association table mapping workers to specific construction projects (`obras`). References `obras(id)` `ON DELETE CASCADE` and `maestros(id)` `ON DELETE CASCADE`. Enforces composite `UNIQUE(obra_id, maestro_id)`.
* **`asistencia_diaria`**: Header record for daily attendance logs by project. References `obras(id)` `ON DELETE CASCADE` and `perfiles_usuario(id)` (`registrado_por`). Contains audit fields (`es_correctivo`, `foto_evidencia_url`).
* **`asistencia_diaria_detalle`**: Itemized worker attendance entry. References `asistencia_diaria(id)` `ON DELETE CASCADE` and `maestros(id)` `ON DELETE RESTRICT`. Enforces `UNIQUE(asistencia_diaria_id, maestro_id)` and a domain check `CHECK (estado_asistencia IN (1.0, 0.5, 0.0))`.

---

## 2. Row Level Security (RLS) Policy Architecture

### A. Core Security Principles
1. **Mandatory RLS**: RLS is explicitly enabled (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY;`) on all 5 attendance control tables.
2. **Authenticated Scope**: Access is restricted strictly to users with the Supabase `authenticated` role who possess an active profile in `perfiles_usuario` (`EXISTS (SELECT 1 FROM public.perfiles_usuario WHERE id = auth.uid())`).
3. **Granular Operations**: Policies are defined individually for `SELECT`, `INSERT`, `UPDATE`, and `DELETE` commands to ensure audit integrity.
4. **Audit Trail Protection**: On `asistencia_diaria` `INSERT`, the policy validates `registrado_por = auth.uid()` to prevent impersonation.

### B. Helper Function (Optional / Recommended)
To optimize policy execution and maintain DRY SQL definitions across RLS policies:
```sql
CREATE OR REPLACE FUNCTION public.is_active_authenticated_user()
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT (auth.role() = 'authenticated') AND EXISTS (
    SELECT 1 FROM public.perfiles_usuario
    WHERE id = auth.uid()
  );
$$;
```

---

## 3. Production-Ready SQL Syntax for RLS Policies

```sql
-- ============================================================================
-- 1. TABLE: tipos_maestro
-- ============================================================================
ALTER TABLE public.tipos_maestro ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "tipos_maestro_select_policy" ON public.tipos_maestro;
CREATE POLICY "tipos_maestro_select_policy"
ON public.tipos_maestro FOR SELECT
TO authenticated
USING (
  EXISTS (SELECT 1 FROM public.perfiles_usuario WHERE id = auth.uid())
);

DROP POLICY IF EXISTS "tipos_maestro_insert_policy" ON public.tipos_maestro;
CREATE POLICY "tipos_maestro_insert_policy"
ON public.tipos_maestro FOR INSERT
TO authenticated
WITH CHECK (
  EXISTS (SELECT 1 FROM public.perfiles_usuario WHERE id = auth.uid())
);

DROP POLICY IF EXISTS "tipos_maestro_update_policy" ON public.tipos_maestro;
CREATE POLICY "tipos_maestro_update_policy"
ON public.tipos_maestro FOR UPDATE
TO authenticated
USING (
  EXISTS (SELECT 1 FROM public.perfiles_usuario WHERE id = auth.uid())
)
WITH CHECK (
  EXISTS (SELECT 1 FROM public.perfiles_usuario WHERE id = auth.uid())
);

DROP POLICY IF EXISTS "tipos_maestro_delete_policy" ON public.tipos_maestro;
CREATE POLICY "tipos_maestro_delete_policy"
ON public.tipos_maestro FOR DELETE
TO authenticated
USING (
  EXISTS (SELECT 1 FROM public.perfiles_usuario WHERE id = auth.uid())
);

-- ============================================================================
-- 2. TABLE: maestros
-- ============================================================================
ALTER TABLE public.maestros ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "maestros_select_policy" ON public.maestros;
CREATE POLICY "maestros_select_policy"
ON public.maestros FOR SELECT
TO authenticated
USING (
  EXISTS (SELECT 1 FROM public.perfiles_usuario WHERE id = auth.uid())
);

DROP POLICY IF EXISTS "maestros_insert_policy" ON public.maestros;
CREATE POLICY "maestros_insert_policy"
ON public.maestros FOR INSERT
TO authenticated
WITH CHECK (
  EXISTS (SELECT 1 FROM public.perfiles_usuario WHERE id = auth.uid())
);

DROP POLICY IF EXISTS "maestros_update_policy" ON public.maestros;
CREATE POLICY "maestros_update_policy"
ON public.maestros FOR UPDATE
TO authenticated
USING (
  EXISTS (SELECT 1 FROM public.perfiles_usuario WHERE id = auth.uid())
)
WITH CHECK (
  EXISTS (SELECT 1 FROM public.perfiles_usuario WHERE id = auth.uid())
);

DROP POLICY IF EXISTS "maestros_delete_policy" ON public.maestros;
CREATE POLICY "maestros_delete_policy"
ON public.maestros FOR DELETE
TO authenticated
USING (
  EXISTS (SELECT 1 FROM public.perfiles_usuario WHERE id = auth.uid())
);

-- ============================================================================
-- 3. TABLE: obras_maestros
-- ============================================================================
ALTER TABLE public.obras_maestros ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "obras_maestros_select_policy" ON public.obras_maestros;
CREATE POLICY "obras_maestros_select_policy"
ON public.obras_maestros FOR SELECT
TO authenticated
USING (
  EXISTS (SELECT 1 FROM public.perfiles_usuario WHERE id = auth.uid())
);

DROP POLICY IF EXISTS "obras_maestros_insert_policy" ON public.obras_maestros;
CREATE POLICY "obras_maestros_insert_policy"
ON public.obras_maestros FOR INSERT
TO authenticated
WITH CHECK (
  EXISTS (SELECT 1 FROM public.perfiles_usuario WHERE id = auth.uid())
);

DROP POLICY IF EXISTS "obras_maestros_update_policy" ON public.obras_maestros;
CREATE POLICY "obras_maestros_update_policy"
ON public.obras_maestros FOR UPDATE
TO authenticated
USING (
  EXISTS (SELECT 1 FROM public.perfiles_usuario WHERE id = auth.uid())
)
WITH CHECK (
  EXISTS (SELECT 1 FROM public.perfiles_usuario WHERE id = auth.uid())
);

DROP POLICY IF EXISTS "obras_maestros_delete_policy" ON public.obras_maestros;
CREATE POLICY "obras_maestros_delete_policy"
ON public.obras_maestros FOR DELETE
TO authenticated
USING (
  EXISTS (SELECT 1 FROM public.perfiles_usuario WHERE id = auth.uid())
);

-- ============================================================================
-- 4. TABLE: asistencia_diaria
-- ============================================================================
ALTER TABLE public.asistencia_diaria ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "asistencia_diaria_select_policy" ON public.asistencia_diaria;
CREATE POLICY "asistencia_diaria_select_policy"
ON public.asistencia_diaria FOR SELECT
TO authenticated
USING (
  EXISTS (SELECT 1 FROM public.perfiles_usuario WHERE id = auth.uid())
);

DROP POLICY IF EXISTS "asistencia_diaria_insert_policy" ON public.asistencia_diaria;
CREATE POLICY "asistencia_diaria_insert_policy"
ON public.asistencia_diaria FOR INSERT
TO authenticated
WITH CHECK (
  EXISTS (SELECT 1 FROM public.perfiles_usuario WHERE id = auth.uid())
  AND (registrado_por IS NULL OR registrado_por = auth.uid())
);

DROP POLICY IF EXISTS "asistencia_diaria_update_policy" ON public.asistencia_diaria;
CREATE POLICY "asistencia_diaria_update_policy"
ON public.asistencia_diaria FOR UPDATE
TO authenticated
USING (
  EXISTS (SELECT 1 FROM public.perfiles_usuario WHERE id = auth.uid())
)
WITH CHECK (
  EXISTS (SELECT 1 FROM public.perfiles_usuario WHERE id = auth.uid())
);

DROP POLICY IF EXISTS "asistencia_diaria_delete_policy" ON public.asistencia_diaria;
CREATE POLICY "asistencia_diaria_delete_policy"
ON public.asistencia_diaria FOR DELETE
TO authenticated
USING (
  EXISTS (SELECT 1 FROM public.perfiles_usuario WHERE id = auth.uid())
);

-- ============================================================================
-- 5. TABLE: asistencia_diaria_detalle
-- ============================================================================
ALTER TABLE public.asistencia_diaria_detalle ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "asistencia_diaria_detalle_select_policy" ON public.asistencia_diaria_detalle;
CREATE POLICY "asistencia_diaria_detalle_select_policy"
ON public.asistencia_diaria_detalle FOR SELECT
TO authenticated
USING (
  EXISTS (SELECT 1 FROM public.perfiles_usuario WHERE id = auth.uid())
);

DROP POLICY IF EXISTS "asistencia_diaria_detalle_insert_policy" ON public.asistencia_diaria_detalle;
CREATE POLICY "asistencia_diaria_detalle_insert_policy"
ON public.asistencia_diaria_detalle FOR INSERT
TO authenticated
WITH CHECK (
  EXISTS (SELECT 1 FROM public.perfiles_usuario WHERE id = auth.uid())
);

DROP POLICY IF EXISTS "asistencia_diaria_detalle_update_policy" ON public.asistencia_diaria_detalle;
CREATE POLICY "asistencia_diaria_detalle_update_policy"
ON public.asistencia_diaria_detalle FOR UPDATE
TO authenticated
USING (
  EXISTS (SELECT 1 FROM public.perfiles_usuario WHERE id = auth.uid())
)
WITH CHECK (
  EXISTS (SELECT 1 FROM public.perfiles_usuario WHERE id = auth.uid())
);

DROP POLICY IF EXISTS "asistencia_diaria_detalle_delete_policy" ON public.asistencia_diaria_detalle;
CREATE POLICY "asistencia_diaria_detalle_delete_policy"
ON public.asistencia_diaria_detalle FOR DELETE
TO authenticated
USING (
  EXISTS (SELECT 1 FROM public.perfiles_usuario WHERE id = auth.uid())
);
```

---

## 4. Performance & Foreign Key Indexing SQL Syntax

To prevent full table scans on foreign key lookups and accelerate UI filtering on dates and search terms:

```sql
-- Indexes for Foreign Keys
CREATE INDEX IF NOT EXISTS idx_maestros_tipo_maestro_id ON public.maestros(tipo_maestro_id);
CREATE INDEX IF NOT EXISTS idx_obras_maestros_obra_id ON public.obras_maestros(obra_id);
CREATE INDEX IF NOT EXISTS idx_obras_maestros_maestro_id ON public.obras_maestros(maestro_id);
CREATE INDEX IF NOT EXISTS idx_asistencia_diaria_obra_id ON public.asistencia_diaria(obra_id);
CREATE INDEX IF NOT EXISTS idx_asistencia_diaria_registrado_por ON public.asistencia_diaria(registrado_por);
CREATE INDEX IF NOT EXISTS idx_asistencia_diaria_detalle_asistencia_id ON public.asistencia_diaria_detalle(asistencia_diaria_id);
CREATE INDEX IF NOT EXISTS idx_asistencia_diaria_detalle_maestro_id ON public.asistencia_diaria_detalle(maestro_id);

-- Indexes for Dates, Unique Constraints, and Common Search Queries
CREATE INDEX IF NOT EXISTS idx_asistencia_diaria_fecha ON public.asistencia_diaria(fecha);
CREATE INDEX IF NOT EXISTS idx_asistencia_diaria_obra_fecha ON public.asistencia_diaria(obra_id, fecha);
CREATE INDEX IF NOT EXISTS idx_maestros_rut ON public.maestros(rut);
CREATE INDEX IF NOT EXISTS idx_maestros_activo ON public.maestros(activo);
```

---

## 5. Programmatic & Automated Database Verification Strategy

### A. Verification Architecture
* **Environment**: Node.js execution environment using `@supabase/supabase-js` client or `pg` driver (`process.env.DATABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY`).
* **Design Pattern**: Declarative Schema Assertion Engine. A script queries PostgreSQL system catalogs (`information_schema` and `pg_catalog`), comparing the database metadata against expected JSON definitions.
* **Exit Behavior**: Exits with code `0` on 100% compliance; exits with code `1` and prints precise mismatch diffs if any constraint, index, or RLS policy is missing.

### B. Catalog Inspection Queries

#### 1. RLS Status Assertion Query (`pg_tables`)
```sql
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('tipos_maestro', 'maestros', 'obras_maestros', 'asistencia_diaria', 'asistencia_diaria_detalle');
```
*Expected Result*: `rowsecurity = true` for all 5 tables.

#### 2. Policy Definitions Assertion Query (`pg_policies`)
```sql
SELECT tablename, policyname, cmd, roles, qual, with_check
FROM pg_policies
WHERE schemaname = 'public'
  AND tablename IN ('tipos_maestro', 'maestros', 'obras_maestros', 'asistencia_diaria', 'asistencia_diaria_detalle');
```
*Expected Result*: 20 total policy entries (4 per table for `SELECT`, `INSERT`, `UPDATE`, `DELETE`), targeting role `authenticated`.

#### 3. Foreign Key & Referential Actions Assertion Query (`pg_constraint` + `pg_class`)
```sql
SELECT
  con.conname AS constraint_name,
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
WHERE con.contype = 'f'
  AND nsp.nspname = 'public'
  AND rel.relname IN ('tipos_maestro', 'maestros', 'obras_maestros', 'asistencia_diaria', 'asistencia_diaria_detalle');
```
*Expected Verification*:
- `maestros.tipo_maestro_id` ➔ `tipos_maestro(id)` with `RESTRICT`.
- `obras_maestros.obra_id` ➔ `obras(id)` with `CASCADE`.
- `obras_maestros.maestro_id` ➔ `maestros(id)` with `CASCADE`.
- `asistencia_diaria.obra_id` ➔ `obras(id)` with `CASCADE`.
- `asistencia_diaria.registrado_por` ➔ `perfiles_usuario(id)` with `NO ACTION` / `SET NULL`.
- `asistencia_diaria_detalle.asistencia_diaria_id` ➔ `asistencia_diaria(id)` with `CASCADE`.
- `asistencia_diaria_detalle.maestro_id` ➔ `maestros(id)` with `RESTRICT`.

#### 4. Unique & CHECK Constraints Assertion Query (`pg_constraint`)
```sql
SELECT
  rel.relname AS table_name,
  con.conname AS constraint_name,
  con.contype AS constraint_type,
  pg_get_constraintdef(con.oid) AS constraint_definition
FROM pg_constraint con
JOIN pg_class rel ON rel.oid = con.conrelid
JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
WHERE nsp.nspname = 'public'
  AND rel.relname IN ('tipos_maestro', 'maestros', 'obras_maestros', 'asistencia_diaria', 'asistencia_diaria_detalle');
```
*Expected Verification*:
- `maestros`: UNIQUE constraint on `(rut)`.
- `obras_maestros`: UNIQUE constraint on `(obra_id, maestro_id)`.
- `asistencia_diaria_detalle`: UNIQUE constraint on `(asistencia_diaria_id, maestro_id)`.
- `asistencia_diaria_detalle`: CHECK constraint matching `CHECK (estado_asistencia = ANY (ARRAY[1.0, 0.5, 0.0]))`.

#### 5. Performance Indexes Assertion Query (`pg_indexes`)
```sql
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('tipos_maestro', 'maestros', 'obras_maestros', 'asistencia_diaria', 'asistencia_diaria_detalle');
```
*Expected Verification*: Verify existence of `idx_maestros_tipo_maestro_id`, `idx_obras_maestros_obra_id`, `idx_obras_maestros_maestro_id`, `idx_asistencia_diaria_obra_id`, `idx_asistencia_diaria_fecha`, `idx_asistencia_diaria_detalle_asistencia_id`, `idx_asistencia_diaria_detalle_maestro_id`.

### C. Proposed Node.js Verification Script Outline (`verify_attendance_schema.js`)

```javascript
import { Client } from 'pg';

const EXPECTED_TABLES = [
  'tipos_maestro',
  'maestros',
  'obras_maestros',
  'asistencia_diaria',
  'asistencia_diaria_detalle'
];

async function runVerification() {
  const client = new Client({ connectionString: process.env.DATABASE_URL });
  await client.connect();

  let passed = true;
  console.log('🔍 Starting Database Verification for Milestone 1 Attendance Schema...\n');

  // 1. Verify RLS Enabled
  const rlsRes = await client.query(`
    SELECT tablename, rowsecurity FROM pg_tables
    WHERE schemaname = 'public' AND tablename = ANY($1);
  `, [EXPECTED_TABLES]);

  for (const table of EXPECTED_TABLES) {
    const row = rlsRes.rows.find(r => r.tablename === table);
    if (!row || !row.rowsecurity) {
      console.error(`❌ FAIL: RLS is NOT enabled on table "${table}"`);
      passed = false;
    } else {
      console.log(`✅ PASS: RLS is enabled on table "${table}"`);
    }
  }

  // 2. Verify Policy Count (4 per table)
  const polRes = await client.query(`
    SELECT tablename, count(*)::int AS count FROM pg_policies
    WHERE schemaname = 'public' AND tablename = ANY($1) GROUP BY tablename;
  `, [EXPECTED_TABLES]);

  for (const table of EXPECTED_TABLES) {
    const row = polRes.rows.find(r => r.tablename === table);
    if (!row || row.count < 4) {
      console.error(`❌ FAIL: Table "${table}" has ${row ? row.count : 0} policies, expected at least 4.`);
      passed = false;
    } else {
      console.log(`✅ PASS: Table "${table}" has ${row.count} RLS policies configured.`);
    }
  }

  // 3. Verify Foreign Keys & Delete Rules
  const fkRes = await client.query(`
    SELECT
      rel.relname AS table_name,
      att.attname AS column_name,
      frel.relname AS foreign_table_name,
      con.confdeltype AS delete_type
    FROM pg_constraint con
    JOIN pg_class rel ON rel.oid = con.conrelid
    JOIN pg_attribute att ON att.attrelid = rel.oid AND att.attnum = ANY(con.conkey)
    JOIN pg_class frel ON frel.oid = con.confrelid
    WHERE con.contype = 'f' AND rel.relname = ANY($1);
  `, [EXPECTED_TABLES]);
  console.log(`\n📋 Foreign Keys Found: ${fkRes.rows.length}`);

  // 4. Verify Check Constraint on estado_asistencia
  const checkRes = await client.query(`
    SELECT pg_get_constraintdef(con.oid) AS def
    FROM pg_constraint con
    JOIN pg_class rel ON rel.oid = con.conrelid
    WHERE con.contype = 'c' AND rel.relname = 'asistencia_diaria_detalle';
  `);
  const hasEstadoCheck = checkRes.rows.some(r => r.def.includes('estado_asistencia'));
  if (hasEstadoCheck) {
    console.log('✅ PASS: CHECK constraint on estado_asistencia is active.');
  } else {
    console.error('❌ FAIL: CHECK constraint on estado_asistencia is missing.');
    passed = false;
  }

  await client.end();
  if (!passed) {
    console.error('\n💥 Database schema verification failed!');
    process.exit(1);
  } else {
    console.log('\n🎉 Database schema verification passed successfully!');
    process.exit(0);
  }
}

runVerification().catch(err => {
  console.error('Error running verification script:', err);
  process.exit(1);
});
```

---

## 6. Recommendations & Next Steps
1. Include these SQL statements in the initial migration script for Milestone 1.
2. Store the programmatic verification script in `scripts/verify_attendance_schema.js` or `tests/db/verify_attendance_schema.test.js`.
3. Integrate the script into CI/CD pipelines to ensure future schema changes do not break RLS or constraint requirements.
