# Handoff Report: Test Infrastructure & Test Strategy for `app_local` Control de Personal

**Agent**: Explorer 3  
**Milestone**: Milestone 2 — Desktop App (`app_local`) Control de Personal  
**Working Directory**: `C:\Users\fcola\Desktop\APPACCURATEK\.agents\teamwork_preview_explorer_m2_3`  
**Date**: 2026-07-29  

---

## 1. Observation

- **Existing Test Suite**:
  - `tests/e2e/test_desktop_control_personal.py` (435 lines) uses standard Python `unittest.TestCase` and tests an in-memory mock controller (`MockControlPersonalController`) for Jefes, Cargos, Maestros, daily rates calculation (`1.0`, `0.5`, `0.0`), KPIs, date range reports, Excel (`pandas`/`openpyxl`), and PDF (`reportlab`) exports. All 8 tests currently pass.
  - `app_local/test_controller.py` contains a 16-line ad-hoc test script for Excel ingesta.
- **Environment & Dependencies**:
  - Executing `.venv\Scripts\python.exe -m pytest --version` returns exit code 1 (`No module named pytest`).
  - Executing `.venv\Scripts\python.exe -m pip list` shows `PyQt6` (v6.11.0), `pandas` (v3.0.3), `openpyxl` (v3.1.5), `reportlab` (v5.0.0), `supabase` (v2.31.0), and `httpx` (v0.28.1) installed in `.venv`, but `pytest`, `pytest-qt`, and `pytest-mock` are missing.
- **UI & Navigation Components**:
  - `app_local/src/ui/main_view.py` (lines 60-64) defines `btn_jefes = QPushButton("Jefes de Obra")` at index 2 of `content_stack` (`JefesContent`).
  - Milestone 2 requires renaming `btn_jefes` to `"Control de Personal"` and replacing `JefesContent` with `PersonalContent(QWidget)` containing a 3-tab `QTabWidget` (Sub-tab 1: Jefes de Obra, Sub-tab 2: Maestros, Sub-tab 3: Cargos y Tarifas).
- **Directory Layout**:
  - Currently, `app_local/tests/` does not exist.

---

## 2. Logic Chain

1. **Observation**: Executing `.venv\Scripts\python.exe -m pytest` fails because `pytest` is not installed in `.venv`.  
   **Deduction**: The test runner environment must be prepared by running `.venv\Scripts\python.exe -m pip install pytest pytest-qt pytest-mock`.
2. **Observation**: `app_local` has no `app_local/tests/` folder or `pytest.ini` configuration.  
   **Deduction**: To establish co-located, clean unit and UI testing, `app_local/tests/` must be created alongside `app_local/pytest.ini` configured with `qt_api = pyqt6` and `testpaths = app_local/tests tests/e2e`.
3. **Observation**: `personal_workers.py` will use asynchronous `QThread` workers for Supabase API calls.  
   **Deduction**: Standard unit test assertions will fail or race if run synchronously. `pytest-qt`'s `qtbot.waitSignal(worker.finished, timeout=1000)` fixture must be used to asynchronously wait for `finished` or `error` signals without blocking the Qt event loop.
4. **Observation**: Running PyQt GUI tests in headless automated environments or Windows terminals can cause focus stealing or window creation errors.  
   **Deduction**: Running pytest with `$env:QT_QPA_PLATFORM="offscreen"` forces Qt to render offscreen, guaranteeing deterministic background execution.

---

## 3. Caveats

- **Read-Only Scope**: This report is produced during a read-only investigation phase. No production code in `app_local/src/` or new test code in `app_local/tests/` was modified or created outside `.agents/teamwork_preview_explorer_m2_3/`.
- **Dependency Prerequisites**: The recommended pytest commands assume `.venv\Scripts\python.exe -m pip install pytest pytest-qt pytest-mock` has been executed by the implementer.
- **Supabase Mocking**: All unit and UI tests for `personal_workers.py` and `personal_view.py` rely on the `mock_supabase` fixture to avoid requiring an live internet connection or live database instance during test runs.

---

## 4. Conclusion

We have fully analyzed the test infrastructure, identified the environment requirements, and formulated a complete test execution and implementation plan for Milestone 2.

### 4.1 Required Test Commands

```powershell
# 1. Install test dependencies in .venv
.venv\Scripts\python.exe -m pip install pytest pytest-qt pytest-mock

# 2. Run all app_local unit and UI tests in headless offscreen mode
$env:QT_QPA_PLATFORM="offscreen"; .venv\Scripts\python.exe -m pytest app_local/tests/ -v

# 3. Run specific test modules
.venv\Scripts\python.exe -m pytest app_local/tests/test_personal_workers.py -v
.venv\Scripts\python.exe -m pytest app_local/tests/test_personal_view.py -v
.venv\Scripts\python.exe -m pytest app_local/tests/test_main_view_integration.py -v

# 4. Run legacy E2E suite
.venv\Scripts\python.exe -m unittest discover -s tests/e2e -p "test_*.py" -v
```

### 4.2 Test Case Summary Matrix

| Test Module | Test Case ID | Focus Area | Trigger / Inputs | Expected Outcome |
| :--- | :--- | :--- | :--- | :--- |
| `test_personal_workers.py` | **TC-WRK-01** | `FetchCargosWorker` | `worker.start()` | Emits `finished(list)` with cargo data. |
| `test_personal_workers.py` | **TC-WRK-02** | `SaveCargoWorker` | `SaveCargoWorker(name="Carpintero", rate=45000)` | Emits `finished(dict)` with new cargo UUID. |
| `test_personal_workers.py` | **TC-WRK-03** | `SaveCargoWorker` (Error) | DB duplicate exception | Emits `error(str)` with error message. |
| `test_personal_workers.py` | **TC-WRK-04** | `FetchMaestrosWorker` | Filter `search="Pedro", active=True` | Emits `finished(list)` with filtered maestros. |
| `test_personal_workers.py` | **TC-WRK-05** | `SaveMaestroWorker` | Maestro dict payload | Emits `finished(dict)` with maestro ID. |
| `test_personal_workers.py` | **TC-WRK-06** | `AssignObraMaestroWorker` | `obra_id`, `maestro_id` | Emits `finished(dict)` with assignment ID. |
| `test_personal_view.py` | **TC-UI-01** | `PersonalContent` Render | Instantiate widget | 3 sub-tabs present ("Jefes", "Maestros", "Cargos"). |
| `test_personal_view.py` | **TC-UI-02** | Tab Navigation | Click sub-tab 0, 1, 2 | `QTabWidget` index updates correctly. |
| `test_personal_view.py` | **TC-UI-03** | `MaestrosView` Validation | Click save with empty fields | Validation label displayed; no worker launched. |
| `test_personal_view.py` | **TC-UI-04** | `MaestrosView` Filter | Type in search line edit | Table widget filters matching rows. |
| `test_personal_view.py` | **TC-UI-05** | On-the-Fly Cargo Dialog | Select "Crear Nuevo Cargo..." | On-the-fly cargo creation modal opens. |
| `test_personal_view.py` | **TC-UI-06** | `CargosView` Negative Rate | Enter `sueldo_diario = -5000` | Error label displayed: negative rate rejected. |
| `test_personal_view.py` | **TC-UI-07** | `CargosView` Table Update | Edit sueldo cell | Table cell updates on worker `finished`. |
| `test_main_view_integration.py` | **TC-UI-08** | Navigation Renaming | Check `btn_jefes.text()` | Text is `"Control de Personal"`. |
| `test_main_view_integration.py` | **TC-UI-09** | Sidebar View Switch | Click `btn_jefes` button | `content_stack` displays `PersonalContent` (index 2). |

---

## 5. Verification Method

To independently verify the test infrastructure design and execution instructions:

1. **Verify Existing Tests**:
   Run `.venv\Scripts\python.exe -m unittest discover -s tests/e2e -p "test_*.py" -v` to confirm all 15 Python E2E tests pass.
2. **Verify Document Artifacts**:
   Inspect `.agents/teamwork_preview_explorer_m2_3/analysis.md` and `.agents/teamwork_preview_explorer_m2_3/handoff.md` for complete coverage of all 5 scope items.
3. **Verify Environment Requirements**:
   Confirm `.venv\Scripts\python.exe -m pip list` output against specified required test packages (`pytest`, `pytest-qt`, `pytest-mock`).
