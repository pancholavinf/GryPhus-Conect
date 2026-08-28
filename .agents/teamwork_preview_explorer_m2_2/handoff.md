# Handoff Report — Milestone 2: Desktop App (`app_local`) Control de Personal Workers Architecture

**Module**: `app_local/src/workers/personal_workers.py`  
**Explorer Agent**: Explorer 2 (`teamwork_preview_explorer_m2_2`)  
**Target Recipient**: Implementer Agent / Orchestrator  
**Status**: Completed (Read-Only Investigation & Architecture Plan)  

---

## 1. Observation

Direct observations from codebase inspection:

1. **Supabase Initialization & Environment Setup**:
   - File: `app_local/main.py`, lines 15-23:
     ```python
     SUPABASE_URL = os.getenv("SUPABASE_URL")
     SUPABASE_KEY = os.getenv("SUPABASE_KEY")
     supabase: Client | None = None
     if SUPABASE_URL and ...:
         supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
     ```
   - Client is initialized once at startup using `supabase-py` and injected into UI components.

2. **Existing PyQt Worker Pattern**:
   - File: `app_local/src/core/workers.py`, lines 1-7, 108-142:
     ```python
     from PyQt6.QtCore import QThread, pyqtSignal
     from supabase import Client

     class FetchDashboardDataWorker(QThread):
         success = pyqtSignal(list, dict)
         error = pyqtSignal(str)
         def __init__(self, supabase: Client):
             super().__init__()
             self.supabase = supabase
         def run(self):
             ...
     ```
   - Standard practice uses subclassed `QThread`, custom `pyqtSignal` definitions (`success`, `error`, `finished`), and `try...except` exception wrapping around synchronous Supabase table queries.

3. **Database Schema & Constraints**:
   - File: `.agents/worker_m1_1/schema_r1.sql`, lines 26-52:
     ```sql
     CREATE TABLE IF NOT EXISTS public.tipos_maestro (
         id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
         nombre text NOT NULL,
         sueldo_diario numeric NOT NULL,
         created_at timestamptz DEFAULT now()
     );

     CREATE TABLE IF NOT EXISTS public.maestros (
         id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
         rut text UNIQUE NOT NULL,
         nombre_completo text NOT NULL,
         tipo_maestro_id uuid REFERENCES public.tipos_maestro(id) ON DELETE RESTRICT,
         telefono text,
         activo boolean NOT NULL DEFAULT true,
         created_at timestamptz DEFAULT now()
     );

     CREATE TABLE IF NOT EXISTS public.obras_maestros (
         id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
         obra_id uuid REFERENCES public.obras(id) ON DELETE CASCADE,
         maestro_id uuid REFERENCES public.maestros(id) ON DELETE CASCADE,
         created_at timestamptz DEFAULT now(),
         CONSTRAINT uq_obras_maestros UNIQUE (obra_id, maestro_id)
     );
     ```
   - Core tables `tipos_maestro`, `maestros`, `obras_maestros`, and `obras` are present in PostgreSQL with constraints: `rut UNIQUE`, `ON DELETE RESTRICT` on `tipo_maestro_id`, and composite `UNIQUE(obra_id, maestro_id)` on `obras_maestros`.

4. **Business Logic Contracts**:
   - File: `tests/e2e/test_desktop_control_personal.py`, lines 73-101:
     - On-the-fly cargo creation occurs when registering a maestro with a non-existent `cargo_nombre`.
     - RUT uniqueness check prevents duplicate worker registration.
     - Daily rate sueldo_diario is linked via `tipo_maestro_id`.

---

## 2. Logic Chain

1. **Observation 1 & 2** establish that all database access in `app_local` must be non-blocking by encapsulating Supabase client calls inside PyQt6 `QThread` workers that communicate with UI components solely via `pyqtSignal`.
2. **Observation 3** shows that table operations require specific error handling for relational integrity constraints:
   - Attempting to insert a duplicate RUT in `maestros` throws a unique constraint error (`23505`), requiring `SaveMaestroWorker` to catch this exception and emit a user-friendly error message.
   - Attempting to delete a `maestro` referenced in attendance records violates `ON DELETE RESTRICT` (`23503`), requiring `DeleteMaestroWorker` to catch this and safely fall back to soft deletion (`activo = false`).
3. **Observation 4** indicates that inline creation of `tipos_maestro` must be handled seamlessly inside `SaveMaestroWorker` or via `CreateInlineTipoMaestroWorker` by first querying `tipos_maestro` by name, creating the cargo if missing, and then linking its `uuid` to `maestros.tipo_maestro_id`.
4. Therefore, designing 9 modular `QThread` workers in `app_local/src/workers/personal_workers.py` will satisfy all async requirements for Milestone 2 Control de Personal while maintaining full compatibility with the existing `app_local` codebase.

---

## 3. Caveats

- **Network Mode**: The investigation was conducted in CODE_ONLY mode without active network connection to live Supabase backend.
- **UI Integration**: UI views (`personal_view.py` or updated `main_view.py`) for Milestone 2 will be connected in subsequent implementation phases.

---

## 4. Conclusion

`app_local/src/workers/personal_workers.py` is fully designed and documented. The design consists of 9 asynchronous `QThread` background workers covering all Control de Personal database operations:
- `FetchTiposMaestroWorker`, `SaveTipoMaestroWorker`, `CreateInlineTipoMaestroWorker`
- `FetchMaestrosWorker`, `SaveMaestroWorker`, `DeleteMaestroWorker`
- `FetchObrasMaestrosWorker`, `AssignMaestrosToObraWorker`
- `FetchObrasListWorker`

Detailed code structure, input arguments, signal contracts, and error handling schemes are provided in `analysis.md` and section 4 of `analysis.md`.

---

## 5. Verification Method

To verify the implementation of `app_local/src/workers/personal_workers.py`:

1. **Code File Verification**:
   - Inspect `app_local/src/workers/personal_workers.py` and confirm all 9 `QThread` worker classes are present with `success` and `error` signals.

2. **Unit & Integration Testing**:
   - Execute test suite via command:
     ```powershell
     python -m unittest tests/e2e/test_desktop_control_personal.py
     ```
   - Create unit tests for `personal_workers.py` mocking or running Supabase queries to verify `success.emit(...)` and `error.emit(...)` payloads.

3. **Invalidation Conditions**:
   - Any synchronous call to `supabase.table()` executed on the main UI thread.
   - Unhandled exception causing UI thread freeze or app crash on duplicate RUT insert.
