## 2026-07-29T23:20:12Z
You are Worker 1 for Milestone 1: Database & Supabase Schema for APPACCURATEK.
Your working directory is `C:\Users\fcola\Desktop\APPACCURATEK\.agents\worker_m1_1`.
Create your `progress.md` and `BRIEFING.md` in your working directory.

Load and follow the Supabase skill instructions located at:
`C:\Users\fcola\Desktop\APPACCURATEK\.agents\skills\supabase\SKILL.md`

### Task Specifications:
Implement and verify R1 (Supabase PostgreSQL & RLS schema for attendance control):

1. **Tables to Create & Configure**:
   - `tipos_maestro` (`id` uuid DEFAULT gen_random_uuid() PRIMARY KEY, `nombre` text NOT NULL, `sueldo_diario` numeric NOT NULL, `created_at` timestamptz DEFAULT now())
   - `maestros` (`id` uuid DEFAULT gen_random_uuid() PRIMARY KEY, `rut` text UNIQUE NOT NULL, `nombre_completo` text NOT NULL, `tipo_maestro_id` uuid REFERENCES tipos_maestro(id) ON DELETE RESTRICT, `telefono` text, `activo` bool DEFAULT true NOT NULL, `created_at` timestamptz DEFAULT now())
   - `obras_maestros` (`id` uuid DEFAULT gen_random_uuid() PRIMARY KEY, `obra_id` uuid REFERENCES obras(id) ON DELETE CASCADE, `maestro_id` uuid REFERENCES maestros(id) ON DELETE CASCADE, `created_at` timestamptz DEFAULT now(), UNIQUE(obra_id, maestro_id))
   - `asistencia_diaria` (`id` uuid DEFAULT gen_random_uuid() PRIMARY KEY, `obra_id` uuid REFERENCES obras(id) ON DELETE CASCADE, `fecha` date NOT NULL, `foto_evidencia_url` text, `es_correctivo` bool DEFAULT false NOT NULL, `registrado_por` uuid REFERENCES perfiles_usuario(id), `created_at` timestamptz DEFAULT now())
   - `asistencia_diaria_detalle` (`id` uuid DEFAULT gen_random_uuid() PRIMARY KEY, `asistencia_diaria_id` uuid REFERENCES asistencia_diaria(id) ON DELETE CASCADE, `maestro_id` uuid REFERENCES maestros(id) ON DELETE RESTRICT, `estado_asistencia` numeric(3,1) CHECK (estado_asistencia IN (1.0, 0.5, 0.0)) NOT NULL, `observaciones` text, `created_at` timestamptz DEFAULT now(), UNIQUE(asistencia_diaria_id, maestro_id))

   *(Note: Ensure referenced tables `obras` and `perfiles_usuario` exist or are created cleanly if not present so FKs resolve).*

2. **Foreign Key Constraints & Actions**:
   - Proper FK definitions and explicit ON DELETE actions (RESTRICT vs CASCADE as specified).

3. **Performance Indexes**:
   - Create indexes for FK columns, unique combinations, search fields (`rut`, `tipo_maestro_id`, `obra_id`, `maestro_id`, `fecha`, etc.).

4. **RLS Policies**:
   - Enable RLS on all 5 tables (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY;`).
   - Create RLS policies allowing SELECT, INSERT, UPDATE, DELETE for authenticated users (`auth.role() = 'authenticated'`) / active user profiles.

5. **Programmatic Verification Script**:
   - Create a script (e.g. Python using `psycopg2`/`sqlalchemy`/`supabase` or Node.js using `@supabase/supabase-js`/`pg`) that connects to PostgreSQL / Supabase or executes introspection queries against `information_schema` / `pg_policies` / `pg_indexes` / `pg_constraint`.
   - The script MUST programmatically assert and verify:
     1. Table existence and exact column types/defaults for all 5 tables.
     2. Existence and correct ON DELETE rules for all FK constraints.
     3. Existence of performance indexes.
     4. RLS enabled on all 5 tables.
     5. RLS policies allowing read/write for authenticated users.
     6. Enforcement of CHECK constraint (`estado_asistencia IN (1.0, 0.5, 0.0)`) and UNIQUE constraints.
   - Run the verification script and log complete execution output.

6. **Handoff**:
   - Document changes in `C:\Users\fcola\Desktop\APPACCURATEK\.agents\worker_m1_1\changes.md`.
   - Write handoff report in `C:\Users\fcola\Desktop\APPACCURATEK\.agents\worker_m1_1\handoff.md` including exact build/test/verification execution commands and passing output.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Report back via send_message when completed.
