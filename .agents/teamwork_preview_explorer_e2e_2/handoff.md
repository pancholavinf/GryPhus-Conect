# Handoff Report: React Native E2E Testing Strategy Proposal

This report proposes a Node.js/Jest-based simulated/headless E2E testing strategy for the upcoming React Native (Expo) application. It details the workspace status, required packages, and architectural test tiers (1 to 4).

---

## 1. Observation
1. **Directory Verification**:
   - Calling `list_dir` on `C:\Users\fcola\Desktop\APPACCURATEK\` returns the following subdirectories: `app_local`, `app_mobile`, `.agents`, `.idea`, `.venv`, `INFO PROYECTO`, `__pycache__`, and `venv`.
   - Calling `list_dir` on the target path `C:\Users\fcola\Desktop\APPACCURATEK\app_trackeo_avances` results in the error:
     ```
     Encountered error in step execution: directory C:\Users\fcola\Desktop\APPACCURATEK\app_trackeo_avances does not exist
     ```
2. **Planned Tasks**:
   - `C:\Users\fcola\Desktop\APPACCURATEK\.agents\milestone_1_orchestrator\progress.md` line 4 shows the pending task:
     ```markdown
     - [ ] Initialize React Native Expo app inside C:/Users/fcola/Desktop/APPACCURATEK/app_trackeo_avances
     ```
   - `C:\Users\fcola\Desktop\APPACCURATEK\.agents\e2e_testing_orchestrator\plan.md` lines 14-15:
     ```markdown
     14: 1. **Milestone 1: Exploration & Setup**
     15:    - Check if 'app_trackeo_avances' is created. If not, wait/create the skeleton.
     ```
3. **Environment Versions**:
   - Verification report `C:\Users\fcola\Desktop\APPACCURATEK\.agents\teamwork_preview_explorer_exploration\handoff.md` lines 22-24 confirms:
     ```markdown
     - Node: v24.15.0
     - npm: 11.12.1
     - Expo CLI: Not recognized
     ```
4. **App Tech Stack**:
   - Summarized in `C:\Users\fcola\Desktop\APPACCURATEK\.agents\orchestrator\PROJECT.md` lines 4-10:
     ```markdown
     - Local SQLite DB (using expo-sqlite) for offline-first data caching and queueing.
     - Supabase client (@supabase/supabase-js) for cloud synchronization when online.
     - Expo Image Manipulator for image compression.
     ```

---

## 2. Logic Chain
1. **Workspace State**: Since `C:\Users\fcola\Desktop\APPACCURATEK\app_trackeo_avances` is not in the directory listing and listing it throws an error, but the `milestone_1_orchestrator` has a pending task to initialize it, the folder **does not yet exist but is in queue for creation**.
2. **Current Packages**: Because the application directory has not been created, **no packages are currently installed** for the React Native application. The other directories contain Kivy/Python (`app_mobile`) and PyQt/Python (`app_local`) codebases.
3. **Testing Methodology**: Since a real device-based E2E test suite (e.g. Detox/Appium) introduces heavy setup times, binary compilation, and simulator dependencies, a **simulated/headless E2E testing strategy using Node.js & Jest** is the most robust and high-speed approach. It works by:
   - Rendering the React Native component hierarchy in a Node context using `@testing-library/react-native`.
   - Mocking the native modules (`expo-sqlite`, `expo-camera`, `expo-image-manipulator`, and `@react-native-community/netinfo`) with fully functional in-memory JS or SQLite equivalents.
   - Intercepting the network layer or mocking the `@supabase/supabase-js` client to test database synchronization and authentication states headlessly.

---

## 3. Caveats
- **Lack of Codebase Context**: Because the React Native application is not yet created, we cannot examine the actual component exports, file names, or SQLite setup code. The proposed setup and tests are designed to match the architectural layouts specified in `PROJECT.md` and `SCOPE.md`.
- **Simulation Limits**: Mocking hardware APIs (Camera, FileSystem, Network status) means that certain device-specific issues (e.g. storage file permission issues, slow SQL execution, UI font-rendering clipping) cannot be detected by this headless suite. Real-device spot checking is still recommended during final deployment.

---

## 4. Conclusion

### A. Package Setup Strategy
To support Node.js/Jest headless E2E testing, the following packages should be added to the devDependencies and dependencies in the future `app_trackeo_avances/package.json`:

```json
{
  "dependencies": {
    "expo-sqlite": "~14.0.0",
    "expo-camera": "~15.0.0",
    "expo-image-manipulator": "~12.0.0",
    "@react-native-community/netinfo": "7.1.0",
    "@supabase/supabase-js": "^2.39.0",
    "react-navigation": "^5.x"
  },
  "devDependencies": {
    "jest": "^29.2.1",
    "jest-expo": "~51.0.0",
    "babel-jest": "^29.2.1",
    "react-test-renderer": "18.2.0",
    "@testing-library/react-native": "^12.4.0",
    "@testing-library/jest-native": "^5.4.3",
    "sqlite3": "^5.1.7"
  }
}
```

*Note: `sqlite3` is added as a devDependency to power the in-memory SQLite mock wrapper, allowing tests to run real SQLite schema queries and check database state without device hardware.*

### B. Test Suite Structure & Jest Setup
The testing framework should be structured inside `app_trackeo_avances/tests/e2e/`:
- `setup.js`: Contains Mock implementations for Expo modules, Supabase, and NetInfo.
- `tier1_feature.test.js`: Feature-level happy path testing.
- `tier2_boundary.test.js`: Boundary values, error states, and offline queues.
- `tier3_integration.test.js`: Inter-feature flows (Reconnection, Sync, SQLite Crash Recovery).
- `tier4_workload.test.js`: End-to-end full workday flow simulation.

---

### C. Test Tiers Detail

#### Tier 1: Feature Coverage (Login, Selection, Camera, SQLite, Supabase)
- **Login Flow**:
  - Test UI interactions: user enters email/password.
  - Mock Supabase auth to succeed for credentials `test@test.cl` / `123456` and fail for invalid credentials.
  - Assert navigation changes from `LoginScreen` to `HomeScreen` or an alert Toast shown on fail.
- **Selection Workflow**:
  - Render `SelectionFlowScreen`. Simulate consecutive dropdown changes: Select Location -> Select Plan -> Select Item.
  - Verify that selecting a parent item updates the options lists for the child dropdowns in real time.
- **Camera Integration**:
  - Mock `expo-camera` or `expo-image-picker` to return a predefined mock path: `file://tmp/test_image.jpg` with a dummy file payload.
  - Verify that pressing "Capture" shows the image preview component and activates the save button.
- **Local SQLite Cache**:
  - In Jest `setup.js`, mock `expo-sqlite` by redirecting database transactions to an in-memory `sqlite3` database instance.
  - Assert that on successful login, the app triggers a catalog sync, creating tables (`perfiles_usuario`, `obras`, `obras_jefes_obra`, `items_obra`) and populating them with mock records. Verify by querying the in-memory database in-test.

#### Tier 2: Boundary/Corner Cases (Offline, Empty, Max, Compression)
- **Offline States**:
  - Set the `@react-native-community/netinfo` mock state to offline (`isConnected = false`).
  - Attempt to submit a progress report: assert that the app successfully falls back to offline mode, creates a record in the local SQLite table `avances` with `synced = false`, and displays a "Saved Offline" Toast notification.
- **Empty States**:
  - Mock the catalog payload to return `[]` (empty array of projects/items).
  - Verify that the selection screen displays helper text: "No construction projects assigned" and disables the next navigation steps.
- **Max / Limit Checks**:
  - Input a very long string (e.g. 5000+ characters) in the comments text area and verify that SQLite insert does not crash.
  - Input a progress quantity larger than the total quantity of the item. Verify validation rules prevent submission and trigger a Toast warning.
- **Image Compression**:
  - Mock `expo-image-manipulator`. Verify that when the camera returns a 10MB image, the manipulators compress it to a target path with specified arguments (e.g. `quality: 0.8`, format `JPEG`) and return a smaller virtual size.

#### Tier 3: Cross-Feature Combinations (Offline Sync, Crash Recovery)
- **Offline Sync (Reconnection)**:
  - Mock the network as offline. Queue 3 progress reports (each with photo metadata and SQLite inserts).
  - Toggle network mock to online.
  - Simulate triggering the synchronization function.
  - Assert that:
    1. Images are uploaded to Supabase Storage.
    2. Records are inserted into the remote database `public.avances` table.
    3. SQLite rows are updated locally to `synced = true` and `fecha_subida_servidor` is populated with the server timestamp.
- **Crash Recovery**:
  - Queue multiple advances while offline.
  - Simulate an app crash by resetting the React component tree and context state (re-instantiating the test renderer).
  - Assert that the local SQLite database still retains the un-synced advances.
  - Trigger the sync engine and confirm the recovered records are uploaded successfully.

#### Tier 4: Real-World Workload (Workday Simulation)
- **Workday Scenario Simulation**:
  - Execute a sequence of operations representing a manager's typical day:
    1. Start the app online and download project catalog (e.g., 50 items).
    2. Go offline. Record 5 advances (each containing an image and text).
    3. Reconnect to network.
    4. Record 2 online advances.
    5. Trigger background sync.
    6. Simulate app restart (crash/exit).
    7. Retrieve and assert database status.
  - Verify that:
    - All 7 advances have been stored locally.
    - All 7 advances are uploaded to the remote Supabase mock.
    - Local SQLite db database contains 7 records all marked `synced = true` with valid server timestamps.

---

## 5. Verification Method

To verify the test suite configuration and operation after the implementation team initializes the codebase:
1. **Dependencies Check**:
   Confirm that `app_trackeo_avances/package.json` contains:
   - `jest`, `jest-expo`
   - `@testing-library/react-native`
   - `sqlite3` (devDependency)
2. **Execute Command**:
   Run the following terminal command in the app directory:
   ```bash
   npm run test:e2e
   ```
3. **Inspect Output**:
   Check that 4 test files are executed corresponding to each tier and verify they complete with 0 failures:
   - `tests/e2e/tier1_feature.test.js`
   - `tests/e2e/tier2_boundary.test.js`
   - `tests/e2e/tier3_integration.test.js`
   - `tests/e2e/tier4_workload.test.js`
4. **Invalidation Conditions**:
   - The test runner passes but mocks do not execute queries against an actual SQL database (checking for false positives).
   - Sync tests complete without updating the mock SQLite sync columns (`synced = true`, `fecha_subida_servidor`).
