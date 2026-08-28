# Handoff Report: Explorer 1 (Milestone 2 - Control de Personal Desktop App)

## 1. Observation

Direct observations from examining the codebase:

1. **`app_local/src/ui/main_view.py`**:
   - Sidebar setup:
     - Lines 61-65:
       ```python
       self.btn_jefes = QPushButton("Jefes de Obra")
       self.btn_jefes.setProperty("class", "SidebarButton")
       self.btn_jefes.setCheckable(True)
       self.btn_jefes.setCursor(Qt.CursorShape.PointingHandCursor)
       self.btn_jefes.clicked.connect(lambda: self.switch_view(2))
       ```
     - Content stack initialization (lines 93, 98):
       ```python
       self.jefes_content = JefesContent(self.supabase_client)
       ...
       self.content_stack.addWidget(self.jefes_content)       # index 2
       ```
     - View switching logic (lines 148, 156-158):
       ```python
       self.btn_jefes.setChecked(index == 2)
       ...
       elif index == 2: # Pestaña de Jefes
           self.jefes_content.cargar_tabla()
           self.jefes_content.cargar_combos()
       ```
     - Sub-view navigation reset (line 130):
       ```python
       self.btn_jefes.setChecked(False)
       ```

2. **`app_local/src/ui/jefes_view.py`**:
   - Class definition: `class JefesContent(QWidget)` (line 5).
   - Worker imports (line 3): `from src.core.workers import FetchJefesWorker, FetchObrasWorker, CreateJefeWorker, AssignJefeWorker`.
   - Manages site managers via `perfiles_usuario` (role `Jefe_Obra`) and assigns them to `obras` via junction table `obras_jefes_obra`.

3. **`app_local/src/core/workers.py`**:
   - Contains all asynchronous `QThread` workers communicating with Supabase (`FetchDashboardDataWorker`, `FetchJefesWorker`, `FetchObrasWorker`, `CreateJefeWorker`, `AssignJefeWorker`, `FetchMaterialesWorker`, `SaveMaterialWorker`, etc.).
   - Standard pattern uses `pyqtSignal` for UI notifications (`success`, `error`, `finished`).

4. **Directory Structure & Layout**:
   - All desktop UI code is located under `app_local/src/ui/`.
   - Core background tasks and business logic reside under `app_local/src/core/`.
   - No `personal_view.py` exists currently in `app_local/src/ui/`.

---

## 2. Logic Chain

1. **Observation**: `main_view.py` currently binds index 2 of `self.content_stack` directly to `JefesContent` from `jefes_view.py` and names the sidebar button "Jefes de Obra".
2. **Logic Step 1**: To fulfill Milestone 2 ("Control de Personal"), the sidebar button must be renamed to "Control de Personal", and index 2 of `content_stack` must point to a new master container widget `PersonalContent` (in `app_local/src/ui/personal_view.py`).
3. **Logic Step 2**: To maintain backward compatibility and preserve existing functionality, `PersonalContent` must embed `JefesContent` as its first sub-tab inside a `QTabWidget`.
4. **Logic Step 3**: For Sub-tab 2 ("Maestros"), the view requires managing trade workers. This requires querying `maestros`, `tipos_maestro`, and `obras_maestros`. A split layout with search filtering, RUT formatting (`XX.XXX.XXX-K`), Chilean Modulo 11 validation, active status toggles, assignment dropdowns, and an inline dialog (`DialogNuevoCargo`) for on-the-fly cargo creation provides a smooth UX without forcing context switches.
5. **Logic Step 4**: For Sub-tab 3 ("Cargos y Tarifas Diarias"), managing trade categories (`tipos_maestro`) and their daily rates (`sueldo_diario`) via a master-detail form and table provides full CRUD capability over rates.
6. **Logic Step 5**: All Supabase database calls must be wrapped in `QThread` workers inside `src/core/workers.py` (`FetchMaestrosWorker`, `SaveMaestroWorker`, `ToggleMaestroStatusWorker`, `FetchTiposMaestroWorker`, `SaveTipoMaestroWorker`, `DeleteTipoMaestroWorker`) to prevent Qt main thread blocking.

---

## 3. Caveats

- **Supabase Table Migration**: The underlying database tables (`maestros`, `tipos_maestro`, `obras_maestros`) must exist in the Supabase PostgreSQL instance. If RLS (Row Level Security) policies are enabled on these tables, ensure service role or user permissions allow standard SELECT/INSERT/UPDATE operations for desktop admin users.
- **Offline / Network Errors**: Supabase operations inside worker threads rely on network availability. Network timeouts are caught in workers and emitted via `error = pyqtSignal(str)` to trigger `QMessageBox.critical` in the UI thread.

---

## 4. Conclusion

The architecture for Milestone 2 Desktop App (`app_local`) Control de Personal is fully specified and ready for implementation:
1. `main_view.py` will be updated to rename the sidebar button to "Control de Personal" and mount `PersonalContent` at stack index 2.
2. `personal_view.py` will be created with a container `QWidget` hosting a `QTabWidget` with 3 sub-tabs:
   - Sub-tab 1: Jefes de Obra (embedding `JefesContent`).
   - Sub-tab 2: Maestros (CRUD, RUT formatting & Modulo 11 validation, active toggle, obra assignment, inline cargo creation).
   - Sub-tab 3: Cargos y Tarifas Diarias (CRUD for `tipos_maestro` and `sueldo_diario`).
3. Six asynchronous `QThread` workers will be added to `src/core/workers.py` to handle all DB persistence.

---

## 5. Verification Method

To verify the investigation and future implementation:

1. **File Inspection**:
   - Inspect `C:\Users\fcola\Desktop\APPACCURATEK\.agents\teamwork_preview_explorer_m2_1\analysis.md` for complete UI layout specifications, signals/slots, worker signatures, and RUT validation logic.
   - Inspect `app_local/src/ui/main_view.py` lines 61-65 and 93-98 to verify button layout and stack indexing.

2. **Execution & UI Test**:
   - Launch application:
     `python main.py` (from `app_local` directory).
   - Log in as admin user.
   - Confirm sidebar displays "Control de Personal" button.
   - Click "Control de Personal" button: verify 3 sub-tabs ("Jefes de Obra", "Maestros", "Cargos y Tarifas Diarias").
   - Test Sub-tab 1: Verify existing site manager creation and obra assignment functionality works as expected.
   - Test Sub-tab 2: Enter RUT (e.g. `123456785` or `12345678-5`), verify Chilean Modulo 11 validation label, test inline cargo creation `[+]`, and assign worker to an obra.
   - Test Sub-tab 3: Create a new cargo ("Maestro Pintor", rate: 45000), verify table row insertion and currency formatting.
