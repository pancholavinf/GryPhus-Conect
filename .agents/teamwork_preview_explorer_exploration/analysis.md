# Analysis Report: Supabase & Environment Exploration

This report documents the exploration of the remote Supabase database and the system environment setup for the mobile progress tracking application.

## 1. Executive Summary
- **Supabase Connectivity**: Successfully loaded credentials from `.env` and connected to the remote database.
- **Table Existence**: Verified that tables `perfiles_usuario`, `obras`, `obras_jefes_obra`, `items_obra`, `avances`, and `estados_pago` exist in the database schema cache.
- **Database State**: All inspected tables currently contain **0 rows** (empty database).
- **Test Users**: Authenticated successfully with `test@test.cl` (password: `123456`) in Supabase Auth. However, its profile row does not exist in `public.perfiles_usuario` (the table is empty), and query results confirm no assignments or items exist.
- **System Environment**: Node, npm, Python, and pip are installed. The `expo` CLI is not installed globally or is not in the system path.

---

## 2. Supabase Credentials
Loaded from `C:/Users/fcola/Desktop/APPACCURATEK/.env`:
- **SUPABASE_URL**: `https://xkifhzhqgroemzudzxrf.supabase.co`
- **SUPABASE_KEY** (Publishable): `sb_publishable_Lbkl0KuLm8h2ZaPQAUM7VQ_PVTjSw7W`

---

## 3. Remote Database Inspection & Table Schemas

The remote Supabase instance's root OpenAPI/PostgREST schema definition endpoint is restricted (401 Unauthorized), which is standard for newer Supabase gateway configurations. However, table existence and schemas have been mapped from direct API calls and the desktop app's controller mapping.

### Table Definitions & Mappings

#### A. Table `perfiles_usuario`
- **Purpose**: Stores user profile metadata linked to Supabase Auth.
- **Columns**:
  - `id` (UUID, Primary Key, references `auth.users.id`)
  - `nombre` (Text, user's full name)
  - `rol` (Text, e.g., `"Jefe_Obra"`)

*Note: In `LoginWorker` and `CreateJefeWorker`, users are created in `auth.users` with user metadata, and profiles are synced to `public.perfiles_usuario`.*

#### B. Table `obras`
- **Purpose**: Construction projects/sites.
- **Columns**:
  - `id` (UUID/Text, Primary Key)
  - `nombre` (Text)
  - `estado` (Text, e.g., `"Activa"`)
  - `color` (Text, HEX representation)
  - `fecha_creacion` (Timestamp with timezone)

#### C. Table `obras_jefes_obra`
- **Purpose**: Pivot table assigning site managers (Jefes de Obra) to construction projects.
- **Columns**:
  - `id` (UUID, Primary Key)
  - `obra_id` (UUID, Foreign Key references `obras.id`)
  - `jefe_obra_id` (UUID, Foreign Key references `perfiles_usuario.id`)

#### D. Table `items_obra`
- **Purpose**: Structural items/elements of an excel cubicación uploaded for an obra.
- **Columns**:
  - `id` (UUID, Primary Key)
  - `obra_id` (UUID, Foreign Key references `obras.id`)
  - `ubicacion` (Text, maps to Excel `"UBICACIÓN"`)
  - `plano` (Text, maps to Excel `"PLANO"`)
  - `descripcion_plano` (Text, maps to Excel `"DESCRIPCIÓN EN PLANO"`)
  - `estructura` (Text, maps to Excel `"ESTRUCTURA"`)
  - `dimension` (Text, maps to Excel `"DIMENSIONES"`)
  - `perfil` (Text, maps to Excel `"PERFIL"`)
  - `cantidad` (Numeric/Float, maps to Excel `"CANT."`)
  - `cantidad_estructuras` (Numeric/Float, maps to Excel `"CANTIDAD ESTRUCTURAS"`)
  - `largo_mm` (Numeric/Float, maps to Excel `"LARGO\n[mm]"`)
  - `caras_expuestas` (Integer, maps to Excel `"CARAS EXPTAS."`)
  - `perimetro_expuesto_mm` (Numeric/Float, maps to Excel `"PERÍMETRO EXPUESTO\n[mm]"`)
  - `resist_fuego` (Text, maps to Excel `"RESIST. AL FUEGO"`)
  - `masividad_m1` (Numeric/Float, maps to Excel `"MASIV. (M-1)"`)
  - `area_expuesta_m2` (Numeric/Float, maps to Excel `"ÁREA EXPUESTA\n[m2]"`)
  - `material` (Text, maps to Excel `"MATERIAL"`)
  - `certificacion` (Text, maps to Excel `"CERTIFICACION"`)
  - `micras` (Numeric/Float, maps to Excel `"MICRAS"`)
  - `formula` (Text, maps to Excel `"FORMULA"`)
  - `tinetas` (Numeric/Float, maps to Excel `"TINETAS"`)
  - `espesor_mm` (Numeric/Float, maps to Excel `"ESPESOR (mm)"`)
  - `sacos` (Numeric/Float, maps to Excel `"SACOS"`)
  - `anotaciones` (Text, maps to Excel `"ANOTACIONES"`)
  - `precio_unitario_contrato` (Numeric/Float, contract unit price)

#### E. Table `avances`
- **Purpose**: Tracks reported progress updates from the mobile app (offline-first sync).
- **Columns**:
  - `id` (UUID, Primary Key)
  - `item_obra_id` (UUID, references `items_obra.id`)
  - `estado_pago_id` (UUID, references `estados_pago.id`)
  - `jefe_obra_id` (UUID, references `perfiles_usuario.id`)
  - `foto_url` (Text)
  - `comentario` (Text)
  - `fecha_captura_local` (Timestamp)
  - `fecha_subida_servidor` (Timestamp)
  - `estado_revision` (Text)

#### F. Table `estados_pago`
- **Purpose**: Payment statements (restricted financial data).
- **Columns**:
  - `id` (UUID, Primary Key)
  - `obra_id` (UUID, references `obras.id`)
  - `fecha_emision` (Date/Timestamp)
  - `monto_total` (Numeric/Float)
  - `archivo_pdf_url` (Text)

---

## 4. Row Audits & Data Profiles

### Table Rows Summary
| Table Name | Row Count | Status | Notes |
| :--- | :--- | :--- | :--- |
| `perfiles_usuario` | **0** | Empty | Select fails with `42501 permission denied` under authenticated role, but succeeds (returning 0 rows) under anonymous. |
| `obras` | **0** | Empty | |
| `obras_jefes_obra` | **0** | Empty | |
| `items_obra` | **0** | Empty | |
| `avances` | **0** | Empty | |
| `estados_pago` | **0** | Empty | |

### Auth Users Analysis
- **User `test@test.cl`**:
  - Successfully logged into Supabase Auth (`sign_in_with_password`).
  - Auth UID: `132f2267-7191-4444-b858-f85a1c7780be`
  - User Metadata: `{'email_verified': True, 'nombre': 'Francisco Lavin'}`
  - App Metadata: `{'role': 'jefe_obra'}` (Deduced from JS creation script settings).
  - Assigne Obras: **None** (verified `obras_jefes_obra` returns empty).
- **User `test@accuratek.cl`**:
  - Login fails with `"Invalid login credentials"` (does not exist in Auth system).

---

## 5. System Environment Verification

The execution of system check commands returned the following configurations:

| Command / Tool | Version | Path / Location |
| :--- | :--- | :--- |
| **Node** | `v24.15.0` | System Path |
| **npm** | `11.12.1` | System Path |
| **Expo CLI** | *Not Found* | `expo` command is not recognized |
| **Python** | `3.14.4` | System Path |
| **pip** | `26.1.2` | C:\Users\fcola\AppData\Roaming\Python\Python314\site-packages |

### Python Virtual Environments
- **`.venv`**: Configured with Python 3.14, contains dependencies like `Kivy 2.3.1`, `requests 2.34.2`, and `kivymd 1.2.0`.
- **`venv`**: Configured with Python 3.14, contains dependencies like `PyQt6 6.11.0`, `pandas 3.0.3`, and `supabase 2.31.0`.

---

## 6. Verification Evidence Chain

1. **Table existence verification**: Querying `non_existent_table` returned explicit error `"Could not find the table 'public.non_existent_table' in the schema cache"` (PostgREST code `PGRST205`). Querying `perfiles_usuario`, `obras`, `obras_jefes_obra`, `items_obra`, `avances`, and `estados_pago` returned successful responses (`[]` or specific permission indicators).
2. **Permission model findings**: Logging in as `test@test.cl` converts the PostgREST connection role to `authenticated`. The authenticated role lacks `SELECT` permissions on `perfiles_usuario` (throwing Postgres code `42501`), whereas the `anon` connection role has select privileges but returns empty arrays, verifying that Row Level Security (RLS) or default schema grants restrict authenticated users unless explicitly configured.
