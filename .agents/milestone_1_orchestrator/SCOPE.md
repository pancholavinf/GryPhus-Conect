# Scope: Milestone 1 - Database & Supabase Schema (Attendance Control R1)

## Architecture & Requirements
Implement and verify Supabase PostgreSQL schema, foreign keys, performance indexes, RLS policies, and programmatic verification scripts for attendance control.

### Required Tables & Specifications:
1. `tipos_maestro`
   - `id` uuid PRIMARY KEY DEFAULT gen_random_uuid()
   - `nombre` text NOT NULL
   - `sueldo_diario` numeric NOT NULL
   - `created_at` timestamptz DEFAULT now()

2. `maestros`
   - `id` uuid PRIMARY KEY DEFAULT gen_random_uuid()
   - `rut` text UNIQUE NOT NULL
   - `nombre_completo` text NOT NULL
   - `tipo_maestro_id` uuid REFERENCES tipos_maestro(id) ON DELETE RESTRICT
   - `telefono` text
   - `activo` bool DEFAULT true NOT NULL
   - `created_at` timestamptz DEFAULT now()

3. `obras_maestros`
   - `id` uuid PRIMARY KEY DEFAULT gen_random_uuid()
   - `obra_id` uuid REFERENCES obras(id) ON DELETE CASCADE
   - `maestro_id` uuid REFERENCES maestros(id) ON DELETE CASCADE
   - `created_at` timestamptz DEFAULT now()
   - UNIQUE(obra_id, maestro_id)

4. `asistencia_diaria`
   - `id` uuid PRIMARY KEY DEFAULT gen_random_uuid()
   - `obra_id` uuid REFERENCES obras(id) ON DELETE CASCADE
   - `fecha` date NOT NULL
   - `foto_evidencia_url` text
   - `es_correctivo` bool DEFAULT false NOT NULL
   - `registrado_por` uuid REFERENCES perfiles_usuario(id)
   - `created_at` timestamptz DEFAULT now()

5. `asistencia_diaria_detalle`
   - `id` uuid PRIMARY KEY DEFAULT gen_random_uuid()
   - `asistencia_diaria_id` uuid REFERENCES asistencia_diaria(id) ON DELETE CASCADE
   - `maestro_id` uuid REFERENCES maestros(id) ON DELETE RESTRICT
   - `estado_asistencia` numeric(3,1) CHECK (estado_asistencia IN (1.0, 0.5, 0.0)) NOT NULL
   - `observaciones` text
   - `created_at` timestamptz DEFAULT now()
   - UNIQUE(asistencia_diaria_id, maestro_id)

### Security & Performance
- RLS enabled on all 5 tables
- Policies allowing read and write for authenticated users / active profiles
- Indexes on FK columns, dates, unique keys, search fields

## Work Items & Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Exploration | Analyze codebase, existing migrations, DB setup | none | IN_PROGRESS |
| 2 | Implementation | SQL Migration scripts & programmatic verification script | Step 1 | PLANNED |
| 3 | Review | Code review & schema validation | Step 2 | PLANNED |
| 4 | Challenge | Stress test & policy validation script execution | Step 3 | PLANNED |
| 5 | Forensic Audit | Integrity verification of implementation & tests | Step 4 | PLANNED |
