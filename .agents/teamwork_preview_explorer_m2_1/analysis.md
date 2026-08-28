# Comprehensive Architectural Analysis: Milestone 2 - Control de Personal (`app_local`)

## 1. Executive Summary & Scope

Milestone 2 aims to evolve the desktop management application (`app_local`) from a isolated "Jefes de Obra" view into a unified **"Control de Personal"** module. This module brings together three key administrative sub-domains:

1. **Jefes de Obra**: Site managers who use the mobile application to capture progress reports.
2. **Maestros (Workers)**: Master workers and specialized tradesmen assigned to active job sites (*obras*), including complete RUT validation, status toggling (active/inactive), job site assignment, and on-the-fly cargo creation.
3. **Cargos y Tarifas Diarias**: Trade position definitions (*tipos_maestro*) and their associated daily pay rates (*sueldo_diario*).

This document details the code analysis of existing views (`main_view.py`, `jefes_view.py`, `workers.py`, `jefes_controller.py`), the refactoring strategy for `main_view.py`, and the complete UI/component design for `personal_view.py`.

---

## 2. Examination of Existing Codebase

### 2.1 `app_local/src/ui/main_view.py` Analysis
- **Navigation Architecture**: `MainView` inherits from `QWidget` and hosts a fixed-width (250px) `QFrame` sidebar on the left and a `QStackedWidget` (`self.content_stack`) on the right.
- **Sidebar Buttons**: Sidebar contains vertical layout with brand logo, stacked buttons, stretch space, and a logout button.
  - Button 0: `btn_dashboard` -> index 0 (`DashboardContent`)
  - Button 1: `btn_ingesta` -> index 1 (`IngestaContent`)
  - Button 2: `btn_jefes` -> index 2 (`JefesContent`)
  - Button 3: `btn_materiales` -> index 3 (`MaterialesContent`)
- **View Switching Logic (`switch_view(index)`)**:
  - Destroys dynamic sub-views (e.g. `obra_content` for detailed progress tracking).
  - Sets `content_stack` index.
  - Updates checkable button highlights (`setChecked(True/False)`).
  - Triggers tab-specific data load methods (`cargar_obras()`, `cargar_jefes()`, `cargar_tabla()`, `cargar_materiales()`).

### 2.2 `app_local/src/ui/jefes_view.py` Analysis
- `JefesContent` inherits from `QWidget` and contains:
  - Form layout for site manager creation (Nombre, Correo, Contraseña, Teléfono, Foto Perfil).
  - `QTableWidget` (5 columns) listing registered site managers.
  - Assignment section with `QComboBox` for Jefe and Obra.
- Uses asynchronous workers from `src.core.workers`:
  - `FetchJefesWorker`
  - `FetchObrasWorker`
  - `CreateJefeWorker`
  - `AssignJefeWorker`

### 2.3 `app_local/src/core/workers.py` Analysis
- Asynchronous tasks in PyQt6 inherit from `QThread`.
- Communication with UI threads occurs strictly via `pyqtSignal`:
  - `success = pyqtSignal(...)`
  - `error = pyqtSignal(str)`
- Supabase client operations are performed in `run()` to avoid freezing the Qt main GUI loop.

---

## 3. Sidebar Reorganization Plan (`main_view.py`)

### 3.1 Sidebar Button Refactoring
- **Button Rename**: Change `self.btn_jefes = QPushButton("Jefes de Obra")` to `self.btn_personal = QPushButton("Control de Personal")`.
- **Property & Styling**: Keep `setProperty("class", "SidebarButton")` and checkable state.
- **Signal Connection**: `self.btn_personal.clicked.connect(lambda: self.switch_view(2))`.

### 3.2 Content Stack Replacement
- **Import Update**: Replace `from src.ui.jefes_view import JefesContent` with `from src.ui.personal_view import PersonalContent`.
- **Widget Stack**:
  ```python
  self.personal_content = PersonalContent(self.supabase_client)
  self.content_stack.addWidget(self.personal_content) # Index 2
  ```
- **Switch View Logic Update**:
  ```python
  def switch_view(self, index):
      # ... cleanup obra_content ...
      self.content_stack.setCurrentIndex(index)
      self.btn_dashboard.setChecked(index == 0)
      self.btn_ingesta.setChecked(index == 1)
      self.btn_personal.setChecked(index == 2)
      self.btn_materiales.setChecked(index == 3)
      
      if index == 0:
          self.dashboard_content.cargar_obras()
      elif index == 1:
          self.ingesta_content.cargar_jefes()
      elif index == 2:
          self.personal_content.cargar_datos() # Triggers data refresh across sub-tabs
      elif index == 3:
          self.materiales_content.cargar_materiales()
  ```

---

## 4. Architectural Specification: `personal_view.py`

`PersonalContent` will serve as the master container widget in `app_local/src/ui/personal_view.py`.

```
PersonalContent (QWidget)
├── Title Label ("Control de Personal")
└── QTabWidget (self.tab_widget)
    ├── Tab 1: "Jefes de Obra" -> JefesContent (embedded from jefes_view.py)
    ├── Tab 2: "Maestros" -> MaestrosTabWidget (QWidget)
    └── Tab 3: "Cargos y Tarifas Diarias" -> CargosTabWidget (QWidget)
```

### 4.1 Sub-Tab 1: Jefes de Obra
- **Integration**: Direct reuse of `JefesContent(supabase_client)`.
- **Data Lifecycle**: Controlled via `personal_content.jefes_tab.cargar_tabla()` and `cargar_combos()` when Sub-tab 1 is selected.

### 4.2 Sub-Tab 2: Maestros (Worker Management)

#### UI Layout & Structure
1. **Top Toolbar Layout (`QHBoxLayout`)**:
   - `QLineEdit` (`self.search_input`): Search by worker name, RUT, or cargo title.
   - `QComboBox` (`self.status_filter`): Options: `["Todos", "Solo Activos", "Solo Inactivos"]`.
   - `QPushButton` (`self.btn_nuevo_maestro`): Opens/clears form for creating a new worker.
2. **Central Splitter Layout (`QSplitter` Horizontal)**:
   - **Left Widget (`QTableWidget`)**:
     - Columns: `["RUT", "Nombre", "Cargo / Tipo", "Sueldo Diario ($)", "Estado", "Obra Asignada", "Acciones"]`
     - Clickable rows populate the right-hand edit form.
     - Inline action buttons: Toggle status button (Activar/Desactivar).
   - **Right Widget (`QGroupBox("Detalle de Maestro")`)**:
     - Form fields (`QFormLayout`):
       - `self.rut_input` (`QLineEdit`): Performs automatic formatting on blur/input (`XX.XXX.XXX-K`) and Chilean Modulo 11 validation.
       - `self.rut_status_label` (`QLabel`): Displays validation message ("RUT Válido" in green or "RUT Inválido" in red).
       - `self.nombre_input` (`QLineEdit`): Full worker name.
       - Cargo Container (`QHBoxLayout`):
         - `self.combo_cargo` (`QComboBox`): List of available `tipos_maestro`.
         - `self.btn_inline_nuevo_cargo` (`QPushButton("+")`): Inline button to open `DialogNuevoCargo`.
       - `self.combo_obra` (`QComboBox`): List of active obras from database (including `"(Sin Asignación)"`).
       - `self.chk_activo` (`QCheckBox`): "Maestro Activo en Empresa".
     - Action Buttons (`QHBoxLayout`):
       - `self.btn_guardar_maestro` (`QPushButton`): Primary button ("Guardar Maestro").
       - `self.btn_cancelar_maestro` (`QPushButton`): Secondary button ("Cancelar / Limpiar").

#### Chilean RUT Validation & Formatting Algorithm
- **Formatting**:
  ```python
  def format_rut(raw_rut: str) -> str:
      clean = "".join(c for c in raw_rut if c.isalnum()).upper()
      if not clean: return ""
      if len(clean) == 1: return clean
      body, dv = clean[:-1], clean[-1]
      formatted_body = "{:,}".format(int(body)).replace(",", ".") if body.isdigit() else body
      return f"{formatted_body}-{dv}"
  ```
- **Modulo 11 Verification**:
  ```python
  def validate_rut(rut_str: str) -> bool:
      clean = "".join(c for c in rut_str if c.isalnum()).upper()
      if len(clean) < 8 or len(clean) > 9: return False
      body, dv = clean[:-1], clean[-1]
      if not body.isdigit(): return False
      
      factors = [2, 3, 4, 5, 6, 7]
      total = sum(int(digit) * factors[i % 6] for i, digit in enumerate(reversed(body)))
      remainder = total % 11
      expected_dv = 11 - remainder
      if expected_dv == 11: expected_dv = '0'
      elif expected_dv == 10: expected_dv = 'K'
      else: expected_dv = str(expected_dv)
      
      return dv == expected_dv
  ```

#### Inline Cargo Creation (`DialogNuevoCargo`)
- Implemented as a modal `QDialog`.
- Layout (`QFormLayout`):
  - `nombre_input` (`QLineEdit`): e.g., "Maestro Encofrador".
  - `sueldo_diario_input` (`QDoubleSpinBox`): Min 0, Max 10,000,000, SingleStep 1000.
- Buttons: "Guardar", "Cancelar".
- Upon creation:
  - Invokes `SaveTipoMaestroWorker`.
  - On success, reloads `combo_cargo` dropdown across UI and selects the newly created cargo automatically.

### 4.3 Sub-Tab 3: Cargos y Tarifas Diarias

#### UI Layout & Structure
- **Master-Detail Layout (`QHBoxLayout` with 2 main panels)**:
  - **Left Form Panel (`QGroupBox("Gestión de Cargos y Tarifas")`)**:
    - `self.cargo_nombre_input` (`QLineEdit`): Title of the position.
    - `self.cargo_sueldo_input` (`QDoubleSpinBox`): Daily rate in CLP.
    - `self.btn_guardar_cargo` (`QPushButton`): "Guardar Cargo".
    - `self.btn_limpiar_cargo` (`QPushButton`): "Limpiar".
    - `self.btn_eliminar_cargo` (`QPushButton`): "Eliminar Cargo" (enabled only when editing existing row).
  - **Right Table Panel (`QTableWidget`)**:
    - Columns: `["ID", "Nombre del Cargo", "Sueldo Diario ($ CLP)", "Trabajadores Asignados", "Acciones"]`
    - Custom currency cell renderer (formatting numbers as `$ 45.000`).

---

## 5. Database Data Models & Relationships

1. **`tipos_maestro`** (Cargo definitions):
   - `id`: UUID (Primary Key)
   - `nombre`: TEXT (e.g. "Maestro Pintor")
   - `sueldo_diario`: NUMERIC / DOUBLE PRECISION
   - `fecha_creacion`: TIMESTAMPTZ

2. **`maestros`** (Workers):
   - `id`: UUID (Primary Key)
   - `rut`: TEXT (Unique)
   - `nombre`: TEXT
   - `tipo_maestro_id`: UUID (FK -> `tipos_maestro.id`)
   - `activo`: BOOLEAN (Default `True`)
   - `fecha_creacion`: TIMESTAMPTZ

3. **`obras_maestros`** (Assignment of workers to job sites):
   - `id`: UUID (Primary Key)
   - `obra_id`: UUID (FK -> `obras.id`)
   - `maestro_id`: UUID (FK -> `maestros.id`)
   - `fecha_asignacion`: TIMESTAMPTZ

---

## 6. Asynchronous Worker Architecture (`src/core/workers.py`)

To ensure smooth performance and zero UI freezing:

1. **`FetchMaestrosWorker`**:
   - Executes select on `maestros` joining `tipos_maestro` and `obras_maestros(obras(id, nombre))`.
   - Signals: `success(list)`, `error(str)`.

2. **`SaveMaestroWorker`**:
   - Upserts `maestros` record.
   - Manages assignment record in `obras_maestros` (insert/update/delete assignment).
   - Signals: `success(dict, str)`, `error(str)`.

3. **`ToggleMaestroStatusWorker`**:
   - Updates `activo` flag in `maestros` table.
   - Signals: `success(str)`, `error(str)`.

4. **`FetchTiposMaestroWorker`**:
   - Queries all rows from `tipos_maestro` ordered by `nombre`.
   - Signals: `success(list)`, `error(str)`.

5. **`SaveTipoMaestroWorker`**:
   - Inserts or updates `tipos_maestro` table.
   - Signals: `success(dict, str)`, `error(str)`.

6. **`DeleteTipoMaestroWorker`**:
   - Deletes cargo record from `tipos_maestro`.
   - Checks FK constraints to prevent deletion if workers are assigned.
   - Signals: `success(str)`, `error(str)`.

---

## 7. Verification & Implementation Roadmap

1. **Verification Command**:
   - Launch Qt desktop application via Python test runner:
     `python app_local/main.py`
2. **Verification Criteria**:
   - Sidebar displays "Control de Personal".
   - Switching to "Control de Personal" shows `QTabWidget` with 3 sub-tabs.
   - Sub-tab 1 displays existing Jefes de Obra view seamlessly.
   - Sub-tab 2 permits searching, filtering, creating/editing maestros, valid/invalid RUT feedback, inline cargo creation, and site assignment.
   - Sub-tab 3 permits managing cargos and daily rates.
