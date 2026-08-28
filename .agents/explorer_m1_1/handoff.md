# Handoff Report: Database & Supabase Schema Investigation (Milestone 1)

## 1. Observation

Direct observations recorded during investigation:

- **Environment Config**:
  - File `C:\Users\fcola\Desktop\APPACCURATEK\.env` contains:
    ```
    SUPABASE_URL=https://xkifhzhqgroemzudzxrf.supabase.co
    SUPABASE_KEY=sb_publishable_Lbkl0KuLm8h2ZaPQAUM7VQ_PVTjSw7W
    ```

- **Migrations / SQL Files**:
  - File search across `C:\Users\fcola\Desktop\APPACCURATEK` for `*.sql` files returned **0 results**. No migration folder exists in codebase.

- **Live Supabase Table Verification (API Query)**:
  - Command: `.\.venv\Scripts\python.exe .agents\explorer_m1_1\inspect_db.py`
  - Output excerpt:
    ```json
    {
      "obras": { "exists": true },
      "perfiles_usuario": { "exists": true },
      "obras_jefes_obra": { "exists": true },
      "items_obra": { "exists": true },
      "avances": { "exists": true },
      "reporte_obra": { "exists": true },
      "reporte_obra_consumos": { "exists": true },
      "materiales": { "exists": true },
      "tipos_maestro": { "exists": false, "error": "{'message': \"Could not find the table 'public.tipos_maestro' in the schema cache\", 'code': 'PGRST205'}" },
      "maestros": { "exists": false, "error": "{'message': \"Could not find the table 'public.maestros' in the schema cache\", 'code': 'PGRST205'}" },
      "obras_maestros": { "exists": false, "error": "{'message': \"Could not find the table 'public.obras_maestros' in the schema cache\", 'code': 'PGRST205'}" },
      "asistencia_diaria": { "exists": false, "error": "{'message': \"Could not find the table 'public.asistencia_diaria' in the schema cache\", 'code': 'PGRST205'}" },
      "asistencia_diaria_detalle": { "exists": false, "error": "{'message': \"Could not find the table 'public.asistencia_diaria_detalle' in the schema cache\", 'code': 'PGRST205'}" }
    }
    ```

- **Codebase Table Usage & Schema Definitions**:
  - `obras`:
    - Defined in `INFO PROYECTO\contexto_bd.md:47-54` and `INFO PROYECTO\HANDOFF.md:132-138`.
    - Columns: `id` (uuid PRIMARY KEY), `nombre` (text), `estado` (text DEFAULT 'Activa'), `color` (text DEFAULT '#1A529B'), `fecha_creacion` (timestamptz DEFAULT now()).
    - FK targets: `obras_jefes_obra.obra_id`, `items_obra.obra_id`, `reporte_obra.obra_id`, `estados_pago.obra_id`.
  - `perfiles_usuario`:
    - Defined in `INFO PROYECTO\contexto_bd.md:31-37` and `INFO PROYECTO\HANDOFF.md:124-129`.
    - Columns: `id` (uuid PRIMARY KEY REFERENCES auth.users), `nombre` (text), `email` (text), `rol` (text CHECK rol IN ('Administrador', 'Jefe_Obra')), `telefono` (text), `foto_perfil_url` (text).
    - FK targets: `obras_jefes_obra.jefe_obra_id`, `avances.jefe_obra_id`, `reporte_obra.jefe_obra_id`.

---

## 2. Logic Chain

1. **Observation**: Querying the live Supabase API for `obras` and `perfiles_usuario` returned `exists: true`, while querying `tipos_maestro`, `maestros`, `obras_maestros`, `asistencia_diaria`, and `asistencia_diaria_detalle` returned PostgREST code `PGRST205` ("Could not find the table in the schema cache").
   **Inference**: The core application tables (`obras`, `perfiles_usuario`, `items_obra`, `avances`, etc.) are already deployed and active on Supabase. The 5 attendance control tables specified in `SCOPE.md` have NOT been created yet.

2. **Observation**: `find_by_name` returned zero `*.sql` files in the repository.
   **Inference**: The existing schema was created directly on Supabase without committed repository migration scripts. Implementer needs to create a new, self-contained SQL migration script for the 5 attendance tables.

3. **Observation**: `SCOPE.md` specifies foreign keys:
   - `obras_maestros.obra_id` REFERENCES `obras(id)` ON DELETE CASCADE
   - `asistencia_diaria.obra_id` REFERENCES `obras(id)` ON DELETE CASCADE
   - `asistencia_diaria.registrado_por` REFERENCES `perfiles_usuario(id)`
   **Inference**: The attendance tables strictly depend on the existing `obras(id)` and `perfiles_usuario(id)` primary keys. Creating these FK constraints in the migration will enforce relational integrity across the ecosystem.

---

## 3. Caveats

- RLS policies on Supabase currently enforce row access based on authenticated user session token (`auth.uid()`). Public select queries with `SUPABASE_KEY` (anon key) return 0 rows when unauthenticated, though table metadata/existence is confirmed via schema cache.
- The SQLite local database schema in React Native (`app_trackeo_avances/src/database/db.js`) will need a corresponding local SQLite table creation for offline attendance capture in future mobile milestones.

---

## 4. Conclusion

- The live Supabase database environment is accessible and configured via `C:\Users\fcola\Desktop\APPACCURATEK\.env`.
- Tables `obras` and `perfiles_usuario` exist in live Supabase and are actively used across `app_local` and `app_trackeo_avances`.
- All 5 Attendance Control tables (`tipos_maestro`, `maestros`, `obras_maestros`, `asistencia_diaria`, `asistencia_diaria_detalle`) do **not** exist in Supabase and must be created by the Implementer during Step 2 of Milestone 1.

---

## 5. Verification Method

To independently verify these findings:

1. Execute the verification python script:
   ```powershell
   .\.venv\Scripts\python.exe .agents\explorer_m1_1\inspect_db.py
   ```
2. Verify that `obras` and `perfiles_usuario` report `exists: true`.
3. Verify that `tipos_maestro`, `maestros`, `obras_maestros`, `asistencia_diaria`, and `asistencia_diaria_detalle` report `exists: false` with error `PGRST205`.
4. Inspect `INFO PROYECTO\contexto_bd.md` lines 31-54 for documented definitions of `perfiles_usuario` and `obras`.
