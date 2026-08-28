# Database Schema Analysis & Specifications: Attendance Control (Milestone 1)

## Executive Summary
This analysis details the PostgreSQL schema specifications for the **Attendance Control (Control de Asistencia)** module on Supabase. It covers 5 core tables:
1. `tipos_maestro` (Master Worker Roles / Trade Categories & Daily Wages)
2. `maestros` (Worker Profiles)
3. `obras_maestros` (Site-Worker Junction Table)
4. `asistencia_diaria` (Daily Attendance Header & Photo Proof)
5. `asistencia_diaria_detalle` (Daily Worker Attendance Ratings & Status)

All tables use standard PostgreSQL primitives compatible with Supabase (`uuid`, `gen_random_uuid()`, `timestamptz`, `now()`, `numeric`, `date`, `boolean`, `text`), strict foreign key relationships, `ON DELETE` integrity rules, explicit domain constraints, and optimized B-tree indexes for foreign keys, date-range filtering, and RUT lookups.

---

## 1. Detailed Table Specifications & Constraint Verification

### 1.1 `tipos_maestro`
Catalogue of trade categories (e.g., "Maestro Mayor", "Jornal", "Carpintero") and their standard daily wage rate.

- **Columns**:
  - `id`: `uuid PRIMARY KEY DEFAULT gen_random_uuid()` — Unique identifier generated server-side.
  - `nombre`: `text NOT NULL` — Display name of the trade. Recommended: `UNIQUE (nombre)` to avoid duplicate entries.
  - `sueldo_diario`: `numeric NOT NULL` — Standard daily wage amount in CLP. Constraint: `CHECK (sueldo_diario >= 0)`.
  - `created_at`: `timestamptz DEFAULT now() NOT NULL` — Record creation timestamp.

- **FK Integrity & Deletion Rules**:
  - Referenced by `maestros(tipo_maestro_id)`. Deletion of a `tipos_maestro` record is **RESTRICTED** if assigned to any worker.

---

### 1.2 `maestros`
Registry of individual workers employed across sites.

- **Columns**:
  - `id`: `uuid PRIMARY KEY DEFAULT gen_random_uuid()` — Primary Key.
  - `rut`: `text UNIQUE NOT NULL` — Chilean National Identity Number (RUT/RUN), formatted as `XX.XXX.XXX-X`. Unique across the system.
  - `nombre_completo`: `text NOT NULL` — Worker full name.
  - `tipo_maestro_id`: `uuid NOT NULL REFERENCES tipos_maestro(id) ON DELETE RESTRICT` — Primary trade/role assigned.
  - `telefono`: `text` — Optional contact phone number.
  - `activo`: `boolean DEFAULT true NOT NULL` — Flag indicating active employment status.
  - `created_at`: `timestamptz DEFAULT now() NOT NULL` — Ingestion timestamp.

- **FK Integrity & Deletion Rules**:
  - `tipo_maestro_id` -> `tipos_maestro(id)`: **ON DELETE RESTRICT**. Deleting a trade type will throw a foreign key violation error if referenced by workers.
  - Referenced by `obras_maestros(maestro_id)` (CASCADE) and `asistencia_diaria_detalle(maestro_id)` (RESTRICT).

---

### 1.3 `obras_maestros`
Junction table assigning workers (`maestros`) to specific active construction projects (`obras`).

- **Columns**:
  - `id`: `uuid PRIMARY KEY DEFAULT gen_random_uuid()` — Primary Key.
  - `obra_id`: `uuid NOT NULL REFERENCES obras(id) ON DELETE CASCADE` — Target site ID.
  - `maestro_id`: `uuid NOT NULL REFERENCES maestros(id) ON DELETE CASCADE` — Assigned worker ID.
  - `created_at`: `timestamptz DEFAULT now() NOT NULL` — Assignment timestamp.

- **Constraints**:
  - `UNIQUE (obra_id, maestro_id)` — Prevents duplicate active assignments of a single worker to the same project.

- **FK Integrity & Deletion Rules**:
  - `obra_id` -> `obras(id)`: **ON DELETE CASCADE**. If a site is removed, site assignments are deleted automatically.
  - `maestro_id` -> `maestros(id)`: **ON DELETE CASCADE**. If a worker profile is deleted, active site assignments are deleted automatically.

---

### 1.4 `asistencia_diaria`
Daily attendance header record created per site per day. Stores evidence photo, submission date, recorder profile, and corrective flag.

- **Columns**:
  - `id`: `uuid PRIMARY KEY DEFAULT gen_random_uuid()` — Primary Key.
  - `obra_id`: `uuid NOT NULL REFERENCES obras(id) ON DELETE CASCADE` — Site for which attendance is recorded.
  - `fecha`: `date NOT NULL` — Date of attendance (`YYYY-MM-DD`).
  - `foto_evidencia_url`: `text` — URL of evidence photo stored in Supabase Storage.
  - `es_correctivo`: `boolean DEFAULT false NOT NULL` — `false` for standard daily attendance; `true` for corrective entries.
  - `registrado_por`: `uuid REFERENCES perfiles_usuario(id) ON DELETE SET NULL` — User profile ID of the recorder (Jefe de Obra).
  - `created_at`: `timestamptz DEFAULT now() NOT NULL` — Creation timestamp.

- **FK Integrity & Deletion Rules**:
  - `obra_id` -> `obras(id)`: **ON DELETE CASCADE**. If an obra is removed, historical attendance headers for that obra are deleted.
  - `registrado_por` -> `perfiles_usuario(id)`: **ON DELETE SET NULL**. Preserves attendance history even if a user account is removed.

---

### 1.5 `asistencia_diaria_detalle`
Line item records per worker contained within a daily attendance header.

- **Columns**:
  - `id`: `uuid PRIMARY KEY DEFAULT gen_random_uuid()` — Primary Key.
  - `asistencia_diaria_id`: `uuid NOT NULL REFERENCES asistencia_diaria(id) ON DELETE CASCADE` — Parent header record.
  - `maestro_id`: `uuid NOT NULL REFERENCES maestros(id) ON DELETE RESTRICT` — Worker evaluated.
  - `estado_asistencia`: `numeric(3,1) NOT NULL` — Attendance rating value. Must satisfy `CHECK (estado_asistencia IN (1.0, 0.5, 0.0))`.
    - `1.0`: Full Day (Día Completo)
    - `0.5`: Half Day (Medio Día)
    - `0.0`: Absent (Ausente)
  - `observaciones`: `text` — Optional notes (e.g. medical excuse, delay reason).
  - `created_at`: `timestamptz DEFAULT now() NOT NULL` — Creation timestamp.

- **Constraints**:
  - `CHECK (estado_asistencia IN (1.0, 0.5, 0.0))` — Strict enforcement of allowed numeric values.
  - `UNIQUE (asistencia_diaria_id, maestro_id)` — Prevents duplicate detail entries for the same worker under a single attendance header.

- **FK Integrity & Deletion Rules**:
  - `asistencia_diaria_id` -> `asistencia_diaria(id)`: **ON DELETE CASCADE**. Deleting an attendance header automatically removes all detail lines.
  - `maestro_id` -> `maestros(id)`: **ON DELETE RESTRICT**. **Critical Audit Safety Rule**: Prevents deletion of any worker record that has historical attendance data.

---

## 2. Performance Indexing Strategy

To support fast queries in the mobile app, local SQLite sync, and desktop analytics reports, the following indexes must be created:

| Table | Index Name | Target Columns / Expression | Primary Query Target / Use Case |
|-------|------------|----------------------------|---------------------------------|
| `maestros` | `idx_maestros_rut` | `(rut)` (B-tree) | Fast RUT lookup during worker creation & SQLite sync |
| `maestros` | `idx_maestros_tipo_maestro_id` | `(tipo_maestro_id)` (B-tree) | FK Join performance when displaying worker trades |
| `maestros` | `idx_maestros_activo` | `(activo) WHERE activo = true` | Partial index for filtering active workers |
| `obras_maestros` | `idx_obras_maestros_obra_id` | `(obra_id)` (B-tree) | Mobile app fetching list of workers assigned to a specific obra |
| `obras_maestros` | `idx_obras_maestros_maestro_id` | `(maestro_id)` (B-tree) | Finding all obras assigned to a specific worker |
| `obras_maestros` | `idx_obras_maestros_unique` | `(obra_id, maestro_id)` | Automatic index created by UNIQUE constraint |
| `asistencia_diaria` | `idx_asistencia_diaria_obra_fecha` | `(obra_id, fecha DESC)` (B-tree) | Site daily logs, dashboard metrics, date range payroll reporting |
| `asistencia_diaria` | `idx_asistencia_diaria_registrado_por` | `(registrado_por)` (B-tree) | FK query for user logs & audit trail |
| `asistencia_diaria_detalle` | `idx_asistencia_diaria_detalle_header` | `(asistencia_diaria_id)` (B-tree) | Fetching all detail rows for an attendance header |
| `asistencia_diaria_detalle` | `idx_asistencia_diaria_detalle_maestro` | `(maestro_id)` (B-tree) | Worker attendance history & total worked days calculation |
| `asistencia_diaria_detalle` | `idx_asistencia_diaria_detalle_unique` | `(asistencia_diaria_id, maestro_id)` | Automatic index created by UNIQUE constraint |
| `asistencia_diaria_detalle` | `idx_asistencia_diaria_detalle_estado` | `(asistencia_diaria_id, estado_asistencia)` | Aggregating attendance rates (full vs half vs absent) |

---

## 3. Recommended Complete DDL Script

```sql
-- 1. tipos_maestro
CREATE TABLE IF NOT EXISTS tipos_maestro (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre text UNIQUE NOT NULL,
    sueldo_diario numeric(12,2) NOT NULL CHECK (sueldo_diario >= 0),
    created_at timestamptz DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tipos_maestro_nombre ON tipos_maestro(nombre);

-- 2. maestros
CREATE TABLE IF NOT EXISTS maestros (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    rut text UNIQUE NOT NULL,
    nombre_completo text NOT NULL,
    tipo_maestro_id uuid NOT NULL REFERENCES tipos_maestro(id) ON DELETE RESTRICT,
    telefono text,
    activo boolean DEFAULT true NOT NULL,
    created_at timestamptz DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_maestros_rut ON maestros(rut);
CREATE INDEX IF NOT EXISTS idx_maestros_tipo_maestro_id ON maestros(tipo_maestro_id);
CREATE INDEX IF NOT EXISTS idx_maestros_activo ON maestros(activo) WHERE activo = true;

-- 3. obras_maestros
CREATE TABLE IF NOT EXISTS obras_maestros (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    obra_id uuid NOT NULL REFERENCES obras(id) ON DELETE CASCADE,
    maestro_id uuid NOT NULL REFERENCES maestros(id) ON DELETE CASCADE,
    created_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT uq_obras_maestros UNIQUE (obra_id, maestro_id)
);

CREATE INDEX IF NOT EXISTS idx_obras_maestros_obra_id ON obras_maestros(obra_id);
CREATE INDEX IF NOT EXISTS idx_obras_maestros_maestro_id ON obras_maestros(maestro_id);

-- 4. asistencia_diaria
CREATE TABLE IF NOT EXISTS asistencia_diaria (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    obra_id uuid NOT NULL REFERENCES obras(id) ON DELETE CASCADE,
    fecha date NOT NULL,
    foto_evidencia_url text,
    es_correctivo boolean DEFAULT false NOT NULL,
    registrado_por uuid REFERENCES perfiles_usuario(id) ON DELETE SET NULL,
    created_at timestamptz DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_asistencia_diaria_obra_fecha ON asistencia_diaria(obra_id, fecha DESC);
CREATE INDEX IF NOT EXISTS idx_asistencia_diaria_registrado_por ON asistencia_diaria(registrado_por);

-- 5. asistencia_diaria_detalle
CREATE TABLE IF NOT EXISTS asistencia_diaria_detalle (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    asistencia_diaria_id uuid NOT NULL REFERENCES asistencia_diaria(id) ON DELETE CASCADE,
    maestro_id uuid NOT NULL REFERENCES maestros(id) ON DELETE RESTRICT,
    estado_asistencia numeric(3,1) NOT NULL CHECK (estado_asistencia IN (1.0, 0.5, 0.0)),
    observaciones text,
    created_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT uq_asistencia_diaria_detalle UNIQUE (asistencia_diaria_id, maestro_id)
);

CREATE INDEX IF NOT EXISTS idx_asistencia_diaria_detalle_header ON asistencia_diaria_detalle(asistencia_diaria_id);
CREATE INDEX IF NOT EXISTS idx_asistencia_diaria_detalle_maestro ON asistencia_diaria_detalle(maestro_id);
CREATE INDEX IF NOT EXISTS idx_asistencia_diaria_detalle_estado ON asistencia_diaria_detalle(asistencia_diaria_id, estado_asistencia);

-- Enable RLS on all 5 tables
ALTER TABLE tipos_maestro ENABLE ROW LEVEL SECURITY;
ALTER TABLE maestros ENABLE ROW LEVEL SECURITY;
ALTER TABLE obras_maestros ENABLE ROW LEVEL SECURITY;
ALTER TABLE asistencia_diaria ENABLE ROW LEVEL SECURITY;
ALTER TABLE asistencia_diaria_detalle ENABLE ROW LEVEL SECURITY;
```

---

## 4. Security & Row-Level Security (RLS) Recommendations

- All 5 tables must have `ENABLE ROW LEVEL SECURITY;`.
- Access Policy Strategy:
  - **Authenticated Users (Jefe de Obra & Administrador)**:
    - `SELECT`: Allowed for all authenticated users (or scoped to assigned obras via `obras_jefes_obra` / `perfiles_usuario`).
    - `INSERT` / `UPDATE`: Allowed for authenticated users submitting attendance reports or managing master records.
  - Recommended policies can utilize helper functions like `es_administrador()` or check `auth.uid() IS NOT NULL` for development/production parity.

---

## 5. Summary Matrix of Requirements Verification

| Requirement | Requirement Detail | Verification Status | Implementation Rule |
|-------------|--------------------|---------------------|---------------------|
| Data Types | `uuid`, `text`, `numeric`, `date`, `boolean`, `timestamptz` | ✅ Verified | Matched exact domain requirements |
| Primary Keys | UUID default via `gen_random_uuid()` | ✅ Verified | Applied to all 5 tables |
| Timestamp Defaults | `created_at DEFAULT now()` | ✅ Verified | Applied to all 5 tables |
| CHECK Constraints | `estado_asistencia IN (1.0, 0.5, 0.0)` | ✅ Verified | Defined on `asistencia_diaria_detalle` |
| CHECK Constraints | `sueldo_diario >= 0` | ✅ Verified | Defined on `tipos_maestro` |
| UNIQUE Constraints | `rut` in `maestros`, `(obra_id, maestro_id)` in `obras_maestros`, `(asistencia_diaria_id, maestro_id)` in `asistencia_diaria_detalle` | ✅ Verified | Fully defined and indexed |
| ON DELETE RESTRICT | `tipos_maestro -> maestros` & `maestros -> asistencia_diaria_detalle` | ✅ Verified | Prevents deletion of referenced trades & workers with attendance history |
| ON DELETE CASCADE | Parent-child ownership (`obras -> obras_maestros`, `obras -> asistencia_diaria`, `asistencia_diaria -> asistencia_diaria_detalle`) | ✅ Verified | Ensures clean cascade deletion of site artifacts |
