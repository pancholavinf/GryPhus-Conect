# Analysis: Test Infrastructure & PyQt Test Strategy for `app_local` Control de Personal

**Agent**: Explorer 3  
**Milestone**: Milestone 2 — Desktop App (`app_local`) Control de Personal  
**Date**: 2026-07-29  

---

## 1. Executive Summary & Scope Overview

This report presents a comprehensive analysis of the testing environment, existing test suites, test infrastructure gaps, and proposed PyQt test architecture for the `app_local` Control de Personal module in Milestone 2.

### Primary Objectives:
1. **Infrastructure Audit**: Inspect existing tests in `tests/e2e/`, evaluate current `.venv` dependencies, and identify missing testing configuration.
2. **Execution Strategy**: Define standard commands for running unit, UI, and integration tests for `app_local` under headless Qt configurations (`QT_QPA_PLATFORM=offscreen`).
3. **Test Architecture**: Design pytest configuration (`pytest.ini`), shared fixtures (`conftest.py`), and test suite layout (`app_local/tests/`).
4. **PyQt Unit & UI Test Design**: Formulate specific, actionable test cases for `personal_workers.py` (QThread backend workers), `personal_view.py` (QTabWidget container view), and `main_view.py` (sidebar navigation integration) using `pytest-qt` and Qt mocks.

---

## 2. Current Project Test Infrastructure Analysis

### 2.1 Existing Test Suite Inventory
An audit of the repository revealed the following existing test assets:

| File Location | Test Framework / Runner | Scope & Responsibilities |
| :--- | :--- | :--- |
| `tests/e2e/test_desktop_control_personal.py` | Python `unittest` | In-memory controller unit/E2E test suite validating business logic (Jefes, Cargos, Maestros, daily rates calculation, KPIs, date range reports, Excel/PDF export). Contains 8 tests, 100% passing. |
| `tests/e2e/test_supabase_attendance_schema.py` | Python `unittest` | Supabase PostgreSQL DDL and RLS schema verification. |
| `app_local/test_controller.py` | Ad-hoc script | Direct test script invoking `IngestaController.procesar_ingesta`. |

### 2.2 Critical Infrastructure Gaps Identified
1. **Missing `app_local/tests/` Directory**: No co-located test folder exists inside `app_local/`.
2. **Missing `pytest` and `pytest-qt` in `.venv`**:
   - Running `.venv\Scripts\python.exe -m pytest` fails with `No module named pytest`.
   - `.venv` contains `PyQt6` (v6.11.0), `pandas`, `openpyxl`, `reportlab`, `supabase`, `httpx`, but lacks test automation packages (`pytest`, `pytest-qt`, `pytest-mock`).
3. **No Qt Headless Environment Configuration**: GUI testing with PyQt requires `pytest-qt`'s `qtbot` fixture and headless Qt platform configuration (`QT_QPA_PLATFORM=offscreen`) to run smoothly in automated runner environments without spawning visible desktop windows or stealing OS focus.
4. **Lack of `pytest.ini` and `conftest.py`**: No root or module-level pytest configuration defining test discovery paths, Qt API selection (`qt_api = pyqt6`), or mock fixtures.

---

## 3. Proposed `app_local` Test Suite Layout & Configuration

To achieve modular, maintainable, and high-coverage testing for Milestone 2, we propose creating a structured test directory at `app_local/tests/`.

### 3.1 Target Directory Structure
```text
app_local/
├── pytest.ini
├── src/
│   ├── core/
│   │   ├── personal_workers.py       # Async QThread workers (Supabase operations)
│   │   └── ...
│   └── ui/
│       ├── main_view.py              # Main sidebar window
│       ├── personal_view.py            # Main container with QTabWidget (Jefes, Maestros, Cargos)
│       └── ...
└── tests/
    ├── __init__.py
    ├── conftest.py                   # Shared pytest fixtures (mock Supabase client, QApplication, sample data)
    ├── test_personal_workers.py      # Unit tests for asynchronous QThread backend workers
    ├── test_personal_view.py         # PyQt UI tests for personal_view.py (QTabWidget, forms, tables)
    └── test_main_view_integration.py # UI integration tests for sidebar switching to Control de Personal
```

### 3.2 `pytest.ini` Configuration File
Create `app_local/pytest.ini` (or root `pytest.ini`) with the following settings:

```ini
[pytest]
testpaths = app_local/tests tests/e2e
python_files = test_*.py
python_classes = Test*
python_functions = test_*
qt_api = pyqt6
addopts = -v --tb=short
markers =
    unit: Fast isolated unit tests for workers and logic
    ui: PyQt UI widget tests using pytest-qt (qtbot)
    integration: Cross-component integration tests
```

### 3.3 `conftest.py` Fixture Architecture
`app_local/tests/conftest.py` will supply reusable mock objects and Qt initialization:

```python
import pytest
from unittest.mock import MagicMock
from PyQt6.QtWidgets import QApplication

@pytest.fixture(scope="session")
def qapp_args():
    """Configures QApplication arguments for headless testing."""
    return ["--platform", "offscreen"]

@pytest.fixture
def mock_supabase():
    """Provides a fully mocked Supabase client with chainable table/select/insert/update methods."""
    client = MagicMock()
    # Mock table query chain: supabase.table('name').select('*').execute()
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_execute = MagicMock()
    
    client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_table.insert.return_value = mock_select
    mock_table.update.return_value = mock_select
    mock_table.delete.return_value = mock_select
    mock_select.eq.return_value = mock_select
    mock_select.order.return_value = mock_select
    mock_select.ilike.return_value = mock_select
    mock_select.execute.return_value = mock_execute
    
    mock_execute.data = []
    return client

@pytest.fixture
def sample_cargos_data():
    return [
        {"id": "cargo-1", "nombre": "Maestro Mayor", "sueldo_diario": 50000.0},
        {"id": "cargo-2", "nombre": "Ayudante", "sueldo_diario": 30000.0}
    ]

@pytest.fixture
def sample_maestros_data():
    return [
        {
            "id": "m-1",
            "rut": "15.888.999-0",
            "nombre_completo": "Pedro Pascal",
            "tipo_maestro_id": "cargo-1",
            "telefono": "+56911112222",
            "activo": True,
            "tipos_maestro": {"nombre": "Maestro Mayor", "sueldo_diario": 50000.0}
        }
    ]
```

---

## 4. Test Execution Protocol & Terminal Commands

### 4.1 Environment Setup Commands
Before executing tests, install the test dependencies into the `.venv` environment:

```powershell
# Install required test runners in project virtualenv
.venv\Scripts\python.exe -m pip install pytest pytest-qt pytest-mock
```

### 4.2 Standard Test Execution Commands

#### 1. Run all tests in `app_local/tests/`:
```powershell
.venv\Scripts\python.exe -m pytest app_local/tests/ -v
```

#### 2. Run UI tests in headless mode (recommended for CI & automated scripts):
```powershell
$env:QT_QPA_PLATFORM="offscreen"; .venv\Scripts\python.exe -m pytest app_local/tests/ -v
```

#### 3. Run specific test files:
```powershell
# Worker unit tests
.venv\Scripts\python.exe -m pytest app_local/tests/test_personal_workers.py -v

# UI tab view tests
.venv\Scripts\python.exe -m pytest app_local/tests/test_personal_view.py -v

# Main view integration tests
.venv\Scripts\python.exe -m pytest app_local/tests/test_main_view_integration.py -v
```

#### 4. Run existing legacy E2E suite alongside new tests:
```powershell
.venv\Scripts\python.exe -m unittest discover -s tests/e2e -p "test_*.py" -v
```

---

## 5. Unit & UI Test Strategy for Milestone 2 Components

### 5.1 `personal_workers.py` Unit Test Architecture
`personal_workers.py` encapsulates asynchronous `QThread` workers performing Supabase RPC/REST operations. Because Qt workers run in background threads, testing requires `pytest-qt`'s `qtbot.waitSignal` to handle signal emission safely without deadlocks.

#### Key Worker Classes to Test:
1. `FetchCargosWorker(QThread)`: Emits `finished(list)` on success or `error(str)` on exception.
2. `SaveCargoWorker(QThread)`: Emits `finished(dict)` when inserting/updating `tipos_maestro`.
3. `FetchMaestrosWorker(QThread)`: Emits `finished(list)` with joined `tipos_maestro` data.
4. `SaveMaestroWorker(QThread)`: Emits `finished(dict)` when inserting/updating worker data.
5. `AssignObraMaestroWorker(QThread)`: Emits `finished(dict)` when writing to `obras_maestros`.

#### Sample Worker Test Implementation Pattern:
```python
import pytest
from unittest.mock import MagicMock
from app_local.src.core.personal_workers import FetchCargosWorker, SaveCargoWorker

def test_fetch_cargos_worker_success(qtbot, mock_supabase, sample_cargos_data):
    # Setup mock response
    mock_supabase.table().select().order().execute.return_value.data = sample_cargos_data
    
    worker = FetchCargosWorker(mock_supabase)
    
    # Catch emitted signal with qtbot
    with qtbot.waitSignal(worker.finished, timeout=1000) as blocker:
        worker.start()
        
    cargos = blocker.args[0]
    assert len(cargos) == 2
    assert cargos[0]["nombre"] == "Maestro Mayor"
    assert cargos[0]["sueldo_diario"] == 50000.0

def test_fetch_cargos_worker_error(qtbot, mock_supabase):
    # Simulate network exception
    mock_supabase.table().select().order().execute.side_effect = Exception("Supabase connection timeout")
    
    worker = FetchCargosWorker(mock_supabase)
    
    with qtbot.waitSignal(worker.error, timeout=1000) as blocker:
        worker.start()
        
    error_msg = blocker.args[0]
    assert "Supabase connection timeout" in error_msg
```

---

### 5.2 `personal_view.py` PyQt UI Test Architecture
`personal_view.py` defines `PersonalContent(QWidget)`, which hosts a `QTabWidget` containing:
- **Sub-Tab 1**: `JefesView` (Jefes de Obra management).
- **Sub-Tab 2**: `MaestrosView` (Maestros CRUD, search filter, RUT validation, active status toggle, assignment to obras).
- **Sub-Tab 3**: `CargosView` (Cargos CRUD: name, daily rate `sueldo_diario`).

#### UI Testing Patterns with `pytest-qt`:
- Use `qtbot.addWidget(widget)` to manage memory and event loops.
- Use `qtbot.mouseClick(button, Qt.MouseButton.LeftButton)` to simulate button presses.
- Use `qtbot.keyClicks(line_edit, "text")` to simulate user typing.
- Verify table contents: `table.rowCount()`, `table.item(row, col).text()`.

#### Sample UI Test Implementation Pattern:
```python
import pytest
from PyQt6.QtCore import Qt
from app_local.src.ui.personal_view import PersonalContent

def test_personal_view_tab_switching(qtbot, mock_supabase):
    view = PersonalContent(mock_supabase)
    qtbot.addWidget(view)
    
    # Check default active tab (Sub-tab 1: Jefes de Obra)
    assert view.tab_widget.currentIndex() == 0
    
    # Switch to Sub-tab 2 (Maestros)
    view.tab_widget.setCurrentIndex(1)
    assert view.tab_widget.currentIndex() == 1
    assert view.tab_widget.tabText(1) == "Maestros"
    
    # Switch to Sub-tab 3 (Cargos y Tarifas)
    view.tab_widget.setCurrentIndex(2)
    assert view.tab_widget.currentIndex() == 2
    assert view.tab_widget.tabText(2) == "Cargos y Tarifas"

def test_cargos_negative_rate_validation(qtbot, mock_supabase):
    view = PersonalContent(mock_supabase)
    qtbot.addWidget(view)
    
    cargos_tab = view.cargos_view
    
    # Fill dialog inputs with negative salary
    cargos_tab.txt_nombre.setText("Jornal Test")
    cargos_tab.txt_sueldo.setText("-5000")
    
    # Click save
    qtbot.mouseClick(cargos_tab.btn_guardar, Qt.MouseButton.LeftButton)
    
    # Assert error label visible and worker not started
    assert cargos_tab.lbl_error.isVisible()
    assert "El sueldo diario no puede ser negativo" in cargos_tab.lbl_error.text()
```

---

### 5.3 `main_view.py` PyQt UI Integration Test Architecture
`main_view.py` handles the primary desktop navigation sidebar. Milestone 2 renames the "Jefes de Obra" navigation button to **"Control de Personal"** and routes index 2 of `QStackedWidget` to `PersonalContent`.

#### Integration Test Requirements:
1. Verify sidebar button label reads `"Control de Personal"`.
2. Verify clicking `"Control de Personal"` sets `content_stack.currentIndex()` to 2 and displays `PersonalContent`.
3. Verify entering `PersonalContent` triggers data reloading (`cargar_tabla()`, `cargar_cargos()`).

```python
def test_main_view_control_personal_navigation(qtbot, mock_supabase):
    from app_local.src.ui.main_view import MainView
    from app_local.src.ui.personal_view import PersonalContent
    
    main_view = MainView(mock_supabase)
    qtbot.addWidget(main_view)
    
    # Check button text
    assert main_view.btn_jefes.text() == "Control de Personal"
    
    # Click sidebar button
    qtbot.mouseClick(main_view.btn_jefes, Qt.MouseButton.LeftButton)
    
    # Verify current stacked widget index and type
    assert main_view.content_stack.currentIndex() == 2
    current_widget = main_view.content_stack.currentWidget()
    assert isinstance(current_widget, PersonalContent)
```

---

## 6. Comprehensive Test Case Matrix for Implementation Team

The following test case matrix specifies all unit and UI test scenarios required for Milestone 2:

| Test Case ID | Target File / Class | Test Type | Test Description | Input / Trigger | Expected Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-WRK-01** | `personal_workers.py` (`FetchCargosWorker`) | Unit | Fetch all `tipos_maestro` successfully | `worker.start()` with mock data | `finished` signal emitted with list of cargo dicts. |
| **TC-WRK-02** | `personal_workers.py` (`SaveCargoWorker`) | Unit | Create new cargo with `sueldo_diario` | `SaveCargoWorker(supabase, name="Carpintero", rate=45000)` | `finished` signal emitted with created cargo record. |
| **TC-WRK-03** | `personal_workers.py` (`SaveCargoWorker`) | Unit | Handle Supabase DB insert error | `SaveCargoWorker` with DB duplicate constraint error | `error` signal emitted with error message string. |
| **TC-WRK-04** | `personal_workers.py` (`FetchMaestrosWorker`) | Unit | Fetch maestros with search filter & active status | `FetchMaestrosWorker(supabase, search="Pedro", active_only=True)` | `finished` signal emitted with matching maestro list. |
| **TC-WRK-05** | `personal_workers.py` (`SaveMaestroWorker`) | Unit | Save maestro with RUT format & cargo link | `SaveMaestroWorker(supabase, maestro_dict)` | `finished` signal emitted with maestro UUID. |
| **TC-WRK-06** | `personal_workers.py` (`AssignObraMaestroWorker`) | Unit | Assign maestro to obra in `obras_maestros` | `AssignObraMaestroWorker(supabase, obra_id, maestro_id)` | `finished` signal emitted with assignment record. |
| **TC-UI-01** | `personal_view.py` (`PersonalContent`) | UI | Render container view with 3 sub-tabs | Instantiate `PersonalContent` | 3 sub-tabs present ("Jefes de Obra", "Maestros", "Cargos y Tarifas"). |
| **TC-UI-02** | `personal_view.py` (`PersonalContent`) | UI | Navigate between sub-tabs via click | Click tab bar index 0, 1, 2 | `QTabWidget` active index updates smoothly. |
| **TC-UI-03** | `personal_view.py` (`MaestrosView`) | UI | Validate empty RUT and name fields | Click "Guardar Maestro" with empty inputs | Validation error label shown; worker not launched. |
| **TC-UI-04** | `personal_view.py` (`MaestrosView`) | UI | Search filter updates table rows | Type search query into `txt_search` | Table filters visible rows matching search text. |
| **TC-UI-05** | `personal_view.py` (`MaestrosView`) | UI | On-the-fly cargo creation modal trigger | Select "Crear Nuevo Cargo..." in cargo combo | On-the-fly cargo modal dialog opens. |
| **TC-UI-06** | `personal_view.py` (`CargosView`) | UI | Validate negative `sueldo_diario` input | Enter `sueldo_diario = -5000` | Error label displayed: "El sueldo diario no puede ser negativo". |
| **TC-UI-07** | `personal_view.py` (`CargosView`) | UI | Display table of cargos and update rate | Double click cell or edit rate | Update worker invoked; table cell updates upon `finished`. |
| **TC-UI-08** | `main_view.py` (`MainView`) | Integration | Sidebar navigation button renamed | Inspect `btn_jefes.text()` | Button text is `"Control de Personal"`. |
| **TC-UI-09** | `main_view.py` (`MainView`) | Integration | Sidebar button opens `PersonalContent` | Click `btn_jefes` button | `content_stack` displays `PersonalContent` (index 2). |

---

## 7. Summary & Implementation Plan for Implementer

1. **Package Installation**: Run `.venv\Scripts\python.exe -m pip install pytest pytest-qt pytest-mock`.
2. **Directory Creation**: Create `app_local/tests/` and `app_local/pytest.ini`.
3. **Fixtures Creation**: Create `app_local/tests/conftest.py` containing `mock_supabase` and `qapp_args`.
4. **Worker Unit Tests**: Implement `app_local/tests/test_personal_workers.py` following TC-WRK-01 to TC-WRK-06.
5. **UI View Tests**: Implement `app_local/tests/test_personal_view.py` following TC-UI-01 to TC-UI-07.
6. **Main View Integration Tests**: Implement `app_local/tests/test_main_view_integration.py` following TC-UI-08 and TC-UI-09.
7. **Verification**: Run standard execution command `$env:QT_QPA_PLATFORM="offscreen"; .venv\Scripts\python.exe -m pytest app_local/tests/ -v`.
