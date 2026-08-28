# Technical Analysis & Architecture Plan: Desktop App (`app_local`) Control de Personal Workers

**Module**: `app_local/src/workers/personal_workers.py`  
**Milestone**: Milestone 2 — Control de Personal (Desktop App)  
**Author**: Explorer 2 (`teamwork_preview_explorer_m2_2`)  
**Date**: 2026-07-29  

---

## 1. Executive Summary

This report establishes the complete architectural design and technical specification for `app_local/src/workers/personal_workers.py`. The module provides asynchronous background worker threads using PyQt6's `QThread` to execute all Supabase database operations related to **Control de Personal** (`tipos_maestro`, `maestros`, `obras_maestros`, `obras`).

By delegating network requests and database queries to specialized background threads, the application guarantees 60 FPS UI responsiveness, preventing UI freezing, lockups, or "Not Responding" OS warnings during network latency spikes.

---

## 2. Supabase Integration Analysis in `app_local`

### 2.1 Database Client Initialization
- **Location**: `app_local/main.py`
- **Pattern**: Singleton client instance created via `supabase.create_client(SUPABASE_URL, SUPABASE_KEY)`.
- **Environment**: Reads `SUPABASE_URL` and `SUPABASE_KEY` from local `.env`.
- **Client Passing**: The main window (`MainAppWindow`) passes the `supabase: Client` instance down to views (`LoginScreen`, `MainView`) and controller/worker objects.

### 2.2 Authentication Context & Security
- **Auth Session**: Handled via `supabase.auth` (`sign_in_with_password`, `get_session`, `sign_out`).
- **RLS Policies**: All five attendance tables (`tipos_maestro`, `maestros`, `obras_maestros`, `asistencia_diaria`, `asistencia_diaria_detalle`) enforce Row Level Security (`ENABLE ROW LEVEL SECURITY`) targeting the `authenticated` role.
- **Role Validation**: Desktop app validates user profile role in `perfiles_usuario`. Users with role `Jefe_Obra` are denied access to the desktop client and redirected to mobile/web views.

### 2.3 Existing Worker Pattern Analysis (`src/core/workers.py`)
Examination of existing workers (e.g., `FetchDashboardDataWorker`, `FetchMaterialesWorker`, `SaveMaterialWorker`) reveals a standardized QThread pattern:
1. Inherits from `PyQt6.QtCore.QThread`.
2. Defines custom PySide/PyQt signals:
   - Data payload signals (e.g., `success = pyqtSignal(list)`, `success = pyqtSignal(dict, str)`).
   - Error signal (`error = pyqtSignal(str)`).
3. Accepts `supabase: Client` and operation parameters in `__init__`.
4. Overrides `run()` method, wrapping Supabase RPC/REST calls inside `try...except Exception as e`.
5. Emits data payload signals on success, or `error.emit(str(e))` on failure.
6. Primary key generation using `uuid.uuid4()` for new records before calling Supabase `.insert()`.

### 2.4 Database Table Schema & Relational Integrity (`schema_r1.sql`)
1. **`public.tipos_maestro`** (Cargos / Trade Types):
   - `id`: `uuid` (PK)
   - `nombre`: `text NOT NULL`
   - `sueldo_diario`: `numeric NOT NULL`
   - `created_at`: `timestamptz DEFAULT now()`
2. **`public.maestros`** (Workers / Personnel):
   - `id`: `uuid` (PK)
   - `rut`: `text UNIQUE NOT NULL`
   - `nombre_completo`: `text NOT NULL`
   - `tipo_maestro_id`: `uuid REFERENCES public.tipos_maestro(id) ON DELETE RESTRICT`
   - `telefono`: `text`
   - `activo`: `boolean NOT NULL DEFAULT true`
   - `created_at`: `timestamptz DEFAULT now()`
   - *Indexes*: `idx_maestros_tipo_maestro_id`, `idx_maestros_rut`, `idx_maestros_activo`
3. **`public.obras_maestros`** (Obra Assignment Link):
   - `id`: `uuid` (PK)
   - `obra_id`: `uuid REFERENCES public.obras(id) ON DELETE CASCADE`
   - `maestro_id`: `uuid REFERENCES public.maestros(id) ON DELETE CASCADE`
   - `created_at`: `timestamptz DEFAULT now()`
   - *Constraint*: `CONSTRAINT uq_obras_maestros UNIQUE (obra_id, maestro_id)`
4. **`public.obras`** (Construction Projects):
   - `id`: `uuid` (PK)
   - `nombre`: `text NOT NULL`
   - `estado`: `text NOT NULL DEFAULT 'Activa'`
   - `color`: `text DEFAULT '#1A529B'`

---

## 3. Worker Architecture Plan for `personal_workers.py`

To fully support all requirements of Milestone 2 Control de Personal, `app_local/src/workers/personal_workers.py` will implement 9 dedicated `QThread` worker classes.

### 3.1 Class Breakdown & Specifications

#### 1. `FetchTiposMaestroWorker(QThread)`
- **Purpose**: Retrieves list of trade types (`tipos_maestro`) ordered by name.
- **Inputs**: `supabase: Client`
- **Signals**:
  - `success = pyqtSignal(list)` — Emits list of dictionary records.
  - `error = pyqtSignal(str)` — Emits human-readable error message.
- **Supabase Query**: `supabase.table("tipos_maestro").select("*").order("nombre").execute()`

#### 2. `SaveTipoMaestroWorker(QThread)`
- **Purpose**: Creates or updates a trade type (`tipos_maestro`).
- **Inputs**: `supabase: Client`, `data: dict`, `is_new: bool = False`
- **Signals**:
  - `success = pyqtSignal(dict, str)` — Emits saved dict and success message.
  - `error = pyqtSignal(str)` — Emits error message.
- **Logic**:
  - Validates `nombre` non-empty, `sueldo_diario >= 0`.
  - If `is_new`, sets `id = str(uuid.uuid4())` and calls `.insert(data)`.
  - If update, calls `.update(data).eq("id", data["id"])`.

#### 3. `FetchMaestrosWorker(QThread)`
- **Purpose**: Retrieves workers (`maestros`) with join on `tipos_maestro`. Supports text search, filtering by active status, and filtering by obra assignment.
- **Inputs**: `supabase: Client`, `search_query: str = ""`, `solo_activos: bool = False`, `obra_id_filter: str = ""`
- **Signals**:
  - `success = pyqtSignal(list)` — Emits enriched list of maestros containing embedded `tipos_maestro` data.
  - `error = pyqtSignal(str)`
- **Supabase Query**:
  - `supabase.table("maestros").select("*, tipos_maestro(id, nombre, sueldo_diario)").execute()`
  - If `obra_id_filter` is provided, fetches assigned `maestro_id` list from `obras_maestros` first, then applies `in_("id", maestro_ids)`.
  - Filters by `search_query` across `rut` or `nombre_completo`.

#### 4. `SaveMaestroWorker(QThread)`
- **Purpose**: Creates or updates a maestro record, supporting **on-the-fly inline cargo creation** if cargo does not exist.
- **Inputs**:
  - `supabase: Client`
  - `maestro_data: dict` (`rut`, `nombre_completo`, `tipo_maestro_id`, `telefono`, `activo`)
  - `inline_tipo_nombre: str = None` (optional string if user typed a new cargo name)
  - `inline_sueldo_diario: float = 0.0`
  - `is_new: bool = False`
- **Signals**:
  - `success = pyqtSignal(dict, str)`
  - `error = pyqtSignal(str)`
- **Logic**:
  1. If `inline_tipo_nombre` is provided:
     - Query `tipos_maestro` to check if `nombre` already exists (case-insensitive).
     - If exists, reuse existing `tipo_maestro.id`.
     - If not, create new `tipos_maestro` with `id = uuid4()`, `nombre = inline_tipo_nombre.strip()`, `sueldo_diario = inline_sueldo_diario`.
     - Assign `maestro_data["tipo_maestro_id"] = new_tipo_id`.
  2. Perform `rut` format cleaning/trimming.
  3. Insert (`.insert(maestro_data)`) or Update (`.update(maestro_data).eq("id", maestro_data["id"])`).

#### 5. `DeleteMaestroWorker(QThread)`
- **Purpose**: Soft-deletes (`activo = false`) or hard-deletes a maestro record.
- **Inputs**: `supabase: Client`, `maestro_id: str`, `hard_delete: bool = False`
- **Signals**:
  - `success = pyqtSignal(str)`
  - `error = pyqtSignal(str)`
- **Logic & Error Handling**:
  - If `hard_delete` is requested, attempts `supabase.table("maestros").delete().eq("id", maestro_id)`.
  - Catches FK constraint violation (`23503` / RESTRICT from `asistencia_diaria_detalle`) and returns user-friendly guidance: *"No se puede eliminar el maestro debido a que posee asistencias registradas. Se ha desactivado el maestro en su lugar."*
  - Default soft delete performs `update({"activo": False}).eq("id", maestro_id)`.

#### 6. `FetchObrasMaestrosWorker(QThread)`
- **Purpose**: Retrieves assignment links between obras and maestros.
- **Inputs**: `supabase: Client`, `obra_id: str = None`, `maestro_id: str = None`
- **Signals**:
  - `success = pyqtSignal(list)`
  - `error = pyqtSignal(str)`
- **Supabase Query**: `supabase.table("obras_maestros").select("*, maestros(*, tipos_maestro(nombre, sueldo_diario)), obras(nombre)")`.

#### 7. `AssignMaestrosToObraWorker(QThread)`
- **Purpose**: Batch manages assignments for an obra (adds new links, removes obsolete links).
- **Inputs**: `supabase: Client`, `obra_id: str`, `target_maestro_ids: list[str]`
- **Signals**:
  - `success = pyqtSignal(str)`
  - `error = pyqtSignal(str)`
- **Logic**:
  - Queries existing `obras_maestros` for `obra_id`.
  - Determines diff: `to_add` vs `to_remove`.
  - Deletes removed links: `.delete().eq("obra_id", obra_id).in_("maestro_id", to_remove)`.
  - Inserts new links: `.insert([{"id": str(uuid.uuid4()), "obra_id": obra_id, "maestro_id": mid} for mid in to_add])`.

#### 8. `FetchObrasListWorker(QThread)`
- **Purpose**: Retrieves active construction projects (`obras`) for dropdown selection in worker assignment dialogs.
- **Inputs**: `supabase: Client`
- **Signals**:
  - `success = pyqtSignal(list)`
  - `error = pyqtSignal(str)`
- **Supabase Query**: `supabase.table("obras").select("id, nombre, estado, color").eq("estado", "Activa").order("nombre").execute()`

#### 9. `CreateInlineTipoMaestroWorker(QThread)`
- **Purpose**: Standalone worker dedicated to instant on-the-fly creation of cargo types from UI modal dialogs.
- **Inputs**: `supabase: Client`, `nombre: str`, `sueldo_diario: float = 0.0`
- **Signals**:
  - `success = pyqtSignal(dict, str)` — Emits `(tipo_maestro_dict, message)`
  - `error = pyqtSignal(str)`

---

## 4. Proposed Source Code Implementation

The following complete python code module is designed for `app_local/src/workers/personal_workers.py`:

```python
"""
app_local/src/workers/personal_workers.py
PyQt6 QThread asynchronous background workers for Control de Personal operations in Supabase.
"""

import uuid
from PyQt6.QtCore import QThread, pyqtSignal
from supabase import Client

# ============================================================================
# 1. TIPOS MAESTRO WORKERS (Cargos / Trade Types)
# ============================================================================

class FetchTiposMaestroWorker(QThread):
    """Retrieves all tipos_maestro ordered by name."""
    success = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client):
        super().__init__()
        self.supabase = supabase

    def run(self):
        try:
            res = self.supabase.table("tipos_maestro").select("*").order("nombre").execute()
            self.success.emit(res.data or [])
        except Exception as e:
            self.error.emit(f"Error al cargar cargos / tipos de maestro: {str(e)}")


class SaveTipoMaestroWorker(QThread):
    """Creates or updates a tipo_maestro record."""
    success = pyqtSignal(dict, str)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, data: dict, is_new: bool = False):
        super().__init__()
        self.supabase = supabase
        self.data = dict(data)
        self.is_new = is_new

    def run(self):
        try:
            nombre = str(self.data.get("nombre", "")).strip()
            if not nombre:
                self.error.emit("El nombre del cargo no puede estar vacío.")
                return

            sueldo_diario = float(self.data.get("sueldo_diario", 0.0))
            if sueldo_diario < 0:
                self.error.emit("El sueldo diario no puede ser negativo.")
                return

            self.data["nombre"] = nombre
            self.data["sueldo_diario"] = sueldo_diario

            if self.is_new:
                if "id" not in self.data or not self.data["id"]:
                    self.data["id"] = str(uuid.uuid4())
                res = self.supabase.table("tipos_maestro").insert(self.data).execute()
                msg = f"Cargo '{nombre}' creado exitosamente."
            else:
                tipo_id = self.data.get("id")
                if not tipo_id:
                    self.error.emit("ID de cargo no especificado para actualización.")
                    return
                res = self.supabase.table("tipos_maestro").update(self.data).eq("id", tipo_id).execute()
                msg = f"Cargo '{nombre}' actualizado exitosamente."

            saved_item = res.data[0] if res.data else self.data
            self.success.emit(saved_item, msg)
        except Exception as e:
            self.error.emit(f"Error al guardar el cargo: {str(e)}")


class CreateInlineTipoMaestroWorker(QThread):
    """Creates a new tipo_maestro on-the-fly during maestro creation/editing."""
    success = pyqtSignal(dict, str)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, nombre: str, sueldo_diario: float = 0.0):
        super().__init__()
        self.supabase = supabase
        self.nombre = str(nombre).strip()
        self.sueldo_diario = float(sueldo_diario)

    def run(self):
        if not self.nombre:
            self.error.emit("El nombre del cargo no puede estar vacío.")
            return

        try:
            # Check existing cargo by name
            res_check = self.supabase.table("tipos_maestro").select("*").ilike("nombre", self.nombre).execute()
            if res_check.data and len(res_check.data) > 0:
                existing = res_check.data[0]
                self.success.emit(existing, f"Cargo '{existing.get('nombre')}' existente seleccionado.")
                return

            new_id = str(uuid.uuid4())
            new_data = {
                "id": new_id,
                "nombre": self.nombre,
                "sueldo_diario": self.sueldo_diario
            }
            res_ins = self.supabase.table("tipos_maestro").insert(new_data).execute()
            saved = res_ins.data[0] if res_ins.data else new_data
            self.success.emit(saved, f"Cargo '{self.nombre}' creado al vuelo con éxito.")
        except Exception as e:
            self.error.emit(f"Error al crear cargo al vuelo: {str(e)}")


# ============================================================================
# 2. MAESTROS WORKERS (Personnel Management)
# ============================================================================

class FetchMaestrosWorker(QThread):
    """Fetches maestros with types, supporting text search and active status filter."""
    success = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, search_query: str = "", solo_activos: bool = False, obra_id_filter: str = ""):
        super().__init__()
        self.supabase = supabase
        self.search_query = search_query.strip().lower()
        self.solo_activos = solo_activos
        self.obra_id_filter = obra_id_filter.strip()

    def run(self):
        try:
            query = self.supabase.table("maestros").select("*, tipos_maestro(id, nombre, sueldo_diario)")

            if self.solo_activos:
                query = query.eq("activo", True)

            if self.obra_id_filter:
                res_om = self.supabase.table("obras_maestros").select("maestro_id").eq("obra_id", self.obra_id_filter).execute()
                maestro_ids = [r.get("maestro_id") for r in (res_om.data or []) if r.get("maestro_id")]
                if not maestro_ids:
                    self.success.emit([])
                    return
                query = query.in_("id", maestro_ids)

            res = query.order("nombre_completo").execute()
            data = res.data or []

            # Perform in-memory text filtering for search query if provided
            if self.search_query:
                filtered = []
                for m in data:
                    rut = (m.get("rut") or "").lower()
                    nombre = (m.get("nombre_completo") or "").lower()
                    cargo_nombre = (m.get("tipos_maestro", {}).get("nombre") or "").lower() if m.get("tipos_maestro") else ""
                    if self.search_query in rut or self.search_query in nombre or self.search_query in cargo_nombre:
                        filtered.append(m)
                data = filtered

            self.success.emit(data)
        except Exception as e:
            self.error.emit(f"Error al obtener lista de maestros: {str(e)}")


class SaveMaestroWorker(QThread):
    """Creates or updates a maestro, supporting inline cargo resolution."""
    success = pyqtSignal(dict, str)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, maestro_data: dict, inline_tipo_nombre: str = None, inline_sueldo_diario: float = 0.0, is_new: bool = False):
        super().__init__()
        self.supabase = supabase
        self.data = dict(maestro_data)
        self.inline_tipo_nombre = str(inline_tipo_nombre).strip() if inline_tipo_nombre else None
        self.inline_sueldo_diario = float(inline_sueldo_diario)
        self.is_new = is_new

    def run(self):
        try:
            rut = str(self.data.get("rut", "")).strip()
            nombre = str(self.data.get("nombre_completo", "")).strip()

            if not rut or not nombre:
                self.error.emit("El RUT y el Nombre Completo son datos obligatorios.")
                return

            # Handle inline tipo_maestro creation if specified
            if self.inline_tipo_nombre:
                res_cargo = self.supabase.table("tipos_maestro").select("id").ilike("nombre", self.inline_tipo_nombre).execute()
                if res_cargo.data and len(res_cargo.data) > 0:
                    self.data["tipo_maestro_id"] = res_cargo.data[0]["id"]
                else:
                    new_tipo_id = str(uuid.uuid4())
                    new_cargo = {
                        "id": new_tipo_id,
                        "nombre": self.inline_tipo_nombre,
                        "sueldo_diario": self.inline_sueldo_diario
                    }
                    self.supabase.table("tipos_maestro").insert(new_cargo).execute()
                    self.data["tipo_maestro_id"] = new_tipo_id

            if not self.data.get("tipo_maestro_id"):
                self.error.emit("Debe seleccionar o especificar un Cargo / Tipo de Maestro válido.")
                return

            self.data["rut"] = rut
            self.data["nombre_completo"] = nombre
            self.data["telefono"] = str(self.data.get("telefono", "")).strip()
            self.data["activo"] = bool(self.data.get("activo", True))

            if self.is_new:
                if "id" not in self.data or not self.data["id"]:
                    self.data["id"] = str(uuid.uuid4())
                res = self.supabase.table("maestros").insert(self.data).execute()
                msg = f"Maestro '{nombre}' registrado exitosamente."
            else:
                m_id = self.data.get("id")
                if not m_id:
                    self.error.emit("ID de maestro no especificado para actualización.")
                    return
                res = self.supabase.table("maestros").update(self.data).eq("id", m_id).execute()
                msg = f"Maestro '{nombre}' actualizado exitosamente."

            saved = res.data[0] if res.data else self.data
            self.success.emit(saved, msg)
        except Exception as e:
            err_str = str(e)
            if "23505" in err_str or "unique constraint" in err_str.lower() or "rut" in err_str.lower():
                self.error.emit(f"El RUT '{self.data.get('rut')}' ya se encuentra registrado en el sistema.")
            else:
                self.error.emit(f"Error al guardar maestro: {err_str}")


class DeleteMaestroWorker(QThread):
    """Soft-deletes (activo=false) or hard-deletes a maestro record."""
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, maestro_id: str, hard_delete: bool = False):
        super().__init__()
        self.supabase = supabase
        self.maestro_id = maestro_id
        self.hard_delete = hard_delete

    def run(self):
        try:
            if self.hard_delete:
                try:
                    self.supabase.table("maestros").delete().eq("id", self.maestro_id).execute()
                    self.success.emit("Maestro eliminado permanentemente de la base de datos.")
                except Exception as ex:
                    # Catch FK RESTRICT from asistencia_diaria_detalle
                    err_text = str(ex)
                    if "23503" in err_text or "foreign key constraint" in err_text.lower():
                        # Fallback to soft delete
                        self.supabase.table("maestros").update({"activo": False}).eq("id", self.maestro_id).execute()
                        self.success.emit("El maestro posee asistencias registradas y no puede ser eliminado. Ha sido desactivado automáticamente.")
                    else:
                        raise ex
            else:
                self.supabase.table("maestros").update({"activo": False}).eq("id", self.maestro_id).execute()
                self.success.emit("Maestro desactivado correctamente.")
        except Exception as e:
            self.error.emit(f"Error al eliminar / desactivar maestro: {str(e)}")


# ============================================================================
# 3. OBRAS MAESTROS ASSIGNMENT WORKERS
# ============================================================================

class FetchObrasMaestrosWorker(QThread):
    """Fetches assignments linking maestros to obras."""
    success = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, obra_id: str = None, maestro_id: str = None):
        super().__init__()
        self.supabase = supabase
        self.obra_id = obra_id
        self.maestro_id = maestro_id

    def run(self):
        try:
            query = self.supabase.table("obras_maestros").select("*, maestros(*, tipos_maestro(nombre, sueldo_diario)), obras(nombre)")

            if self.obra_id:
                query = query.eq("obra_id", self.obra_id)
            if self.maestro_id:
                query = query.eq("maestro_id", self.maestro_id)

            res = query.execute()
            self.success.emit(res.data or [])
        except Exception as e:
            self.error.emit(f"Error al consultar asignaciones de personal a obras: {str(e)}")


class AssignMaestrosToObraWorker(QThread):
    """Bulk manages maestro assignments for a given obra_id."""
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client, obra_id: str, target_maestro_ids: list[str]):
        super().__init__()
        self.supabase = supabase
        self.obra_id = obra_id
        self.target_maestro_ids = list(set(target_maestro_ids))

    def run(self):
        try:
            if not self.obra_id:
                self.error.emit("Debe especificar un ID de Obra válido.")
                return

            # Fetch existing assignments
            res_curr = self.supabase.table("obras_maestros").select("id, maestro_id").eq("obra_id", self.obra_id).execute()
            current_map = {r["maestro_id"]: r["id"] for r in (res_curr.data or []) if r.get("maestro_id")}

            current_set = set(current_map.keys())
            target_set = set(self.target_maestro_ids)

            to_add = target_set - current_set
            to_remove = current_set - target_set

            # Delete removed assignments
            if to_remove:
                self.supabase.table("obras_maestros").delete().eq("obra_id", self.obra_id).in_("maestro_id", list(to_remove)).execute()

            # Insert new assignments
            if to_add:
                new_records = [
                    {
                        "id": str(uuid.uuid4()),
                        "obra_id": self.obra_id,
                        "maestro_id": mid
                    }
                    for mid in to_add
                ]
                self.supabase.table("obras_maestros").insert(new_records).execute()

            self.success.emit("Asignaciones de personal actualizadas exitosamente.")
        except Exception as e:
            self.error.emit(f"Error al actualizar asignaciones de la obra: {str(e)}")


class FetchObrasListWorker(QThread):
    """Fetches list of active obras for dropdown selectors."""
    success = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, supabase: Client):
        super().__init__()
        self.supabase = supabase

    def run(self):
        try:
            res = self.supabase.table("obras").select("id, nombre, estado, color").eq("estado", "Activa").order("nombre").execute()
            self.success.emit(res.data or [])
        except Exception as e:
            self.error.emit(f"Error al cargar lista de obras: {str(e)}")
```

---

## 5. Summary of Verification Method

To verify `personal_workers.py` upon implementation:
1. Run `pytest` or `python -m unittest` unit test suites validating `QThread` signal emissions.
2. Confirm thread-safety by spawning workers from PyQt `QApplication` event loop and connecting `success` / `error` signals to UI slots.
3. Validate database constraints handling (duplicate RUT triggers `23505` error signal; foreign key restriction on deletion triggers soft-delete fallback).
