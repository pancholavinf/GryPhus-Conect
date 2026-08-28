# Detailed Database & Schema Investigation Report (Milestone 1)

## Executive Summary
This report provides a comprehensive analysis of the database architecture, environment configurations, existing database tables, and schema prerequisites for Milestone 1 (Attendance Control R1) in the **Accuratek** platform ecosystem.

---

## 1. Environment & Database Connection Details

- **Environment File**: `C:\Users\fcola\Desktop\APPACCURATEK\.env`
- **Supabase Project URL**: `https://xkifhzhqgroemzudzxrf.supabase.co`
- **Supabase Anon / Publishable Key**: `sb_publishable_Lbkl0KuLm8h2ZaPQAUM7VQ_PVTjSw7W`
- **Storage Buckets Utilized**:
  - `accuratek-data`: Public bucket hosting progress pictures (`avances/{jefe_obra_id}/{id}.jpg`), work reports, and original Excel cubication files (`obras/{obra_id}/{filename}.xlsx`).
  - `materiales`: Public bucket hosting material photos and technical datasheets.

---

## 2. Migration Files & SQL File Inspection

A full directory search of `C:\Users\fcola\Desktop\APPACCURATEK` revealed **0 SQL files** (`*.sql`) or versioned migration directories (`supabase/migrations/`).

- **Database State**: The existing database schema was created interactively or via Supabase dashboard / past ad-hoc execution and currently lives directly in the live Supabase PostgreSQL instance.
- **Client Schema Mirror**: `app_trackeo_avances/src/database/db.js` defines an embedded SQLite schema (`trackeo.db`) used for offline caching in the React Native mobile application.

---

## 3. Detailed Investigation of Existing Core Tables

### Table 1: `obras`
- **Status in Supabase**: **EXISTS**
- **Primary Key**: `id` (`uuid`, DEFAULT `gen_random_uuid()`)
- **Schema Definition**:
  | Column Name | Data Type | Nullable | Default | Description / Notes |
  |---|---|---|---|---|
  | `id` | `uuid` | NO | `gen_random_uuid()` | Primary Key |
  | `nombre` | `text` / `varchar` | NO | None | Name of the construction project |
  | `estado` | `text` / `varchar` | NO | `'Activa'` | Project state (`'Activa'`, `'Pausada'`, `'Finalizada'`) |
  | `color` | `text` | YES | `'#1A529B'` | Hex color code for UI branding |
  | `fecha_creacion` | `timestamptz` | YES | `now()` | Timestamp of creation |

- **Foreign Keys Referencing `obras` (Existing)**:
  - `obras_jefes_obra.obra_id` ➔ `obras(id)` ON DELETE CASCADE
  - `items_obra.obra_id` ➔ `obras(id)` ON DELETE CASCADE
  - `reporte_obra.obra_id` ➔ `obras(id)`
  - `estados_pago.obra_id` ➔ `obras(id)`

- **Incoming Foreign Keys Referencing `obras` for Attendance Control (Milestone 1)**:
  - `obras_maestros.obra_id` ➔ `obras(id)` ON DELETE CASCADE
  - `asistencia_diaria.obra_id` ➔ `obras(id)` ON DELETE CASCADE

---

### Table 2: `perfiles_usuario` (User Profiles / Auth Linkage)
- **Status in Supabase**: **EXISTS**
- **Primary Key**: `id` (`uuid`, REFERENCES `auth.users(id)`)
- **Schema Definition**:
  | Column Name | Data Type | Nullable | Default | Description / Notes |
  |---|---|---|---|---|
  | `id` | `uuid` | NO | None | FK referencing `auth.users.id` / `auth.uid()` |
  | `nombre` | `text` / `varchar` | NO | None | Full name of user |
  | `email` | `text` / `varchar` | NO | None | Email address |
  | `rol` | `text` / `varchar` | NO | None | Role: `'Administrador'` (or `'Gerente'`) or `'Jefe_Obra'` / `'Jefe de Obra'` |
  | `telefono` | `text` | YES | NULL | Chilean contact phone number (`+569XXXXXXXX`) |
  | `foto_perfil_url` | `text` | YES | NULL | Avatar photo URL in storage |

- **Foreign Keys Referencing `perfiles_usuario` (Existing)**:
  - `obras_jefes_obra.jefe_obra_id` ➔ `perfiles_usuario(id)` ON DELETE CASCADE
  - `avances.jefe_obra_id` ➔ `perfiles_usuario(id)` ON DELETE CASCADE
  - `reporte_obra.jefe_obra_id` ➔ `perfiles_usuario(id)`

- **Incoming Foreign Keys Referencing `perfiles_usuario` for Attendance Control (Milestone 1)**:
  - `asistencia_diaria.registrado_por` ➔ `perfiles_usuario(id)`

---

## 4. Attendance Control Tables Verification (`SCOPE.md`)

A programmatic query against the live PostgREST API (`https://xkifhzhqgroemzudzxrf.supabase.co`) returned the following status for the 5 required attendance control tables:

| Table Name | Live Supabase Status | PostgREST Response Code | Error Details |
|---|---|---|---|
| `tipos_maestro` | **DOES NOT EXIST** | `PGRST205` | Could not find table `public.tipos_maestro` in schema cache |
| `maestros` | **DOES NOT EXIST** | `PGRST205` | Could not find table `public.maestros` in schema cache |
| `obras_maestros` | **DOES NOT EXIST** | `PGRST205` | Could not find table `public.obras_maestros` in schema cache |
| `asistencia_diaria` | **DOES NOT EXIST** | `PGRST205` | Could not find table `public.asistencia_diaria` in schema cache |
| `asistencia_diaria_detalle` | **DOES NOT EXIST** | `PGRST205` | Could not find table `public.asistencia_diaria_detalle` in schema cache |

---

## 5. Structural Requirements for Milestone 1 Migration

To support Attendance Control (Release R1), the following 5 tables must be created with explicit Foreign Key constraints, Indexes, and RLS Policies:

1. **`tipos_maestro`**
   - `id` uuid PRIMARY KEY DEFAULT gen_random_uuid()
   - `nombre` text NOT NULL
   - `sueldo_diario` numeric NOT NULL
   - `created_at` timestamptz DEFAULT now()

2. **`maestros`**
   - `id` uuid PRIMARY KEY DEFAULT gen_random_uuid()
   - `rut` text UNIQUE NOT NULL
   - `nombre_completo` text NOT NULL
   - `tipo_maestro_id` uuid REFERENCES `tipos_maestro(id)` ON DELETE RESTRICT
   - `telefono` text
   - `activo` boolean DEFAULT true NOT NULL
   - `created_at` timestamptz DEFAULT now()

3. **`obras_maestros`**
   - `id` uuid PRIMARY KEY DEFAULT gen_random_uuid()
   - `obra_id` uuid REFERENCES `obras(id)` ON DELETE CASCADE
   - `maestro_id` uuid REFERENCES `maestros(id)` ON DELETE CASCADE
   - `created_at` timestamptz DEFAULT now()
   - CONSTRAINT `unique_obra_maestro` UNIQUE(obra_id, maestro_id)

4. **`asistencia_diaria`**
   - `id` uuid PRIMARY KEY DEFAULT gen_random_uuid()
   - `obra_id` uuid REFERENCES `obras(id)` ON DELETE CASCADE
   - `fecha` date NOT NULL
   - `foto_evidencia_url` text
   - `es_correctivo` boolean DEFAULT false NOT NULL
   - `registrado_por` uuid REFERENCES `perfiles_usuario(id)`
   - `created_at` timestamptz DEFAULT now()

5. **`asistencia_diaria_detalle`**
   - `id` uuid PRIMARY KEY DEFAULT gen_random_uuid()
   - `asistencia_diaria_id` uuid REFERENCES `asistencia_diaria(id)` ON DELETE CASCADE
   - `maestro_id` uuid REFERENCES `maestros(id)` ON DELETE RESTRICT
   - `estado_asistencia` numeric(3,1) NOT NULL CHECK (estado_asistencia IN (1.0, 0.5, 0.0))
   - `observaciones` text
   - `created_at` timestamptz DEFAULT now()
   - CONSTRAINT `unique_asistencia_maestro` UNIQUE(asistencia_diaria_id, maestro_id)
