# Handoff Report: E2E Headless Testing Strategy for React Native (Expo)

## Executive Summary
This report presents a headless end-to-end (E2E) testing strategy for the upcoming React Native (Expo) mobile application, `app_trackeo_avances`. Since React Native native modules (SQLite, Camera, Supabase client network layer) cannot run out-of-the-box in a standard Node.js/Jest environment, we propose a simulated rendering and stateful mocking architecture using React Native Testing Library (RNTL) and a real in-memory SQLite database in Node (`better-sqlite3`). This enables rapid, CPU-only execution of full user workflows, verification of offline-first queuing, and network synchronization logic, without the complexity and instability of real simulators/emulators in CI/CD environments.

---

## 1. Observation
1. **Workspace Examination**:
   - The directory `C:\Users\fcola\Desktop\APPACCURATEK\app_trackeo_avances` does not exist on disk yet. Listing it yields `Encountered error in step execution: directory C:\Users\fcola\Desktop\APPACCURATEK\app_trackeo_avances does not exist`.
   - The existing directories in the workspace are:
     - `app_mobile/`: A Python mobile app built with Kivy (`app_mobile/main.py` utilizes `kivymd.app` and `kivy.uix.screenmanager`).
     - `app_local/`: A Python desktop app built with PyQt6 (`app_local/main.py` utilizes `PyQt6.QtWidgets`).
     - `.agents/`: Contains plans and state trackers for different milestones.
2. **Project Planning**:
   - According to `.agents/orchestrator/PROJECT.md` line 15:
     > `Milestone 1 | Milestone 1: App Setup & Styling | Initialize Expo app in app_trackeo_avances, install packages, implement Auth/Login screen... | None | IN_PROGRESS`
   - According to `.agents/milestone_1_orchestrator/SCOPE.md` line 20:
     > `1.1 | Initialize App & Dependencies | Create expo app, configure package.json with react-navigation, @supabase/supabase-js, expo-sqlite, expo-image-manipulator, etc. | None | PLANNED`
3. **Dependencies Status**:
   - No node dependencies have been installed yet because the `app_trackeo_avances` folder is not yet initialized.

---

## 2. Logic Chain
1. **State of the Workspace**: Since the React Native Expo app is currently in the setup/planning phase (Milestone 1, step 1.1) and the folder `app_trackeo_avances` has not been generated, there are no packages installed.
2. **Headless E2E Selection**: Testing an offline-first Expo application with complex hardware/network interactions (Camera, SQLite, Supabase) typically requires either:
   - *Full-device E2E* (e.g. Detox/Appium): Heavy, slow, requires compilation of binary builds, difficult to manage in standard Docker containers or headless servers.
   - *Simulated/Headless E2E* (Jest + `@testing-library/react-native`): Runs in pure Node.js, uses `react-test-renderer` to mount components, fires events like text typing and buttons clicks, and simulates the network and hardware layers.
3. **Mocks as the Core Pillar**: To run headless tests that verify SQLite queries, compression, and network synchronization:
   - **SQLite**: A mock of `expo-sqlite` that maps SQLite API calls to an in-memory SQL database (`better-sqlite3`) allows tests to run real SQL statements, verifying tables, inserts, selects, and synchronization states.
   - **Supabase**: Intercepting and mocking calls to `@supabase/supabase-js` permits testing authentication transitions, remote DB inserts, and storage uploads.
   - **NetInfo**: Mocking `@react-native-community/netinfo` allows testing connection flapping, triggering offline vs. online states dynamically.
   - **Camera / Image Manipulator**: Mocking these enables the flow to ingest mock photos, resizing/compressing them, and verifying file URLs stored in SQLite.

---

## 3. Caveats
- **Mock Fidelity**: Headless tests run in Node.js rather than a real Android/iOS runtime. Discrepancies between the behavior of the mocked APIs (e.g., `better-sqlite3` vs. real device `expo-sqlite`) could mask native bugs.
- **No True Layout/UI Testing**: Element positions, CSS rendering errors, font loading issues, or touch event blocking (e.g. a view covering a button) cannot be detected via React Native Testing Library.
- **Operating System Platform Differences**: Behavior specific to iOS/Android platform-specific packages is ignored under Jest.

---

## 4. Conclusion & Proposed Strategy

### A. Packages to Install
When `app_trackeo_avances` is initialized, the following development dependencies must be installed to support the headless testing suite:

```bash
# In app_trackeo_avances/ directory
npm install --save-dev jest jest-expo @testing-library/react-native @testing-library/jest-native react-test-renderer better-sqlite3
```

- **`jest` & `jest-expo`**: The testing framework and the official Expo Jest preset that sets up required Babel transforms for React Native/Expo code.
- **`react-test-renderer`**: Required for mounting the React tree in Jest.
- **`@testing-library/react-native`**: React Native Testing Library (RNTL) for queries and simulated user actions (e.g., `fireEvent.changeText`, `fireEvent.press`).
- **`@testing-library/jest-native`**: Extends Jest matchers with assertions like `.toBeVisible()`, `.toHaveTextContent()`.
- **`better-sqlite3`**: Pure Node.js in-memory database to back the simulated `expo-sqlite` library.

### B. Suggested Test Structure
We propose separating tests into files matching the requested Tiers:

```
app_trackeo_avances/
├── __tests__/
│   ├── setup.js                      # Core mocks (SQLite, Supabase, Camera, NetInfo)
│   ├── tier1_functional.test.js      # Login, Selection Flow, Camera, SQLite insert, Sync (Happy Path)
│   ├── tier2_edgecases.test.js       # Offline queueing, Empty states, Max limits, Image compression
│   ├── tier3_resiliency.test.js      # Offline to Online transition, Partial sync failures, App crash recovery
│   └── tier4_workload.test.js        # High volume data stress, debounce/double-click prevention, thread safety
├── jest.config.js                    # Jest configurations targeting setup.js and Babel transforms
└── package.json
```

### C. Jest Configuration & Mocks Boilerplate

#### `jest.config.js`
```javascript
module.exports = {
  preset: 'jest-expo',
  setupFilesAfterEnv: ['<rootDir>/__tests__/setup.js'],
  transformIgnorePatterns: [
    'node_modules/(?!((jest-)?react-native|@react-native(-community)?)|expo(nent)?|@expo(nent)?/.*|@expo-google-fonts/.*|react-navigation|@react-navigation/.*|@unimodules/.*|unimodules|sentry-expo|native-base|react-native-svg)',
  ],
  testPathIgnorePatterns: ['/node_modules/', '/android/', '/ios/'],
};
```

#### `__tests__/setup.js`
```javascript
import '@testing-library/jest-native/extend-expect';

// 1. Mock expo-sqlite using better-sqlite3 for actual query execution
jest.mock('expo-sqlite', () => {
  const Database = require('better-sqlite3');
  const db = new Database(':memory:');
  
  return {
    openDatabaseSync: () => ({
      execSync: (sql) => {
        db.exec(sql);
      },
      runSync: (sql, params = []) => {
        const stmt = db.prepare(sql);
        const info = stmt.run(params);
        return { lastInsertRowId: info.lastInsertRowid, changes: info.changes };
      },
      getFirstSync: (sql, params = []) => {
        const stmt = db.prepare(sql);
        return stmt.get(params);
      },
      getAllSync: (sql, params = []) => {
        const stmt = db.prepare(sql);
        return stmt.all(params);
      }
    })
  };
});

// 2. Mock NetInfo for connection toggling
let isConnectedState = true;
jest.mock('@react-native-community/netinfo', () => ({
  fetch: jest.fn().mockImplementation(() => Promise.resolve({ isConnected: isConnectedState })),
  addEventListener: jest.fn((callback) => {
    // Notify immediate connection state
    callback({ isConnected: isConnectedState });
    return () => {};
  }),
  useNetInfo: () => ({ isConnected: isConnectedState })
}));

export const toggleNetwork = (state) => {
  isConnectedState = state;
};

// 3. Mock expo-camera
jest.mock('expo-camera', () => {
  const React = require('react');
  const { View, Text } = require('react-native');
  return {
    CameraView: ({ children }) => <View testID="camera-view"><Text>Camera Mock</Text>{children}</View>,
    useCameraPermissions: () => [{ granted: true }, () => Promise.resolve({ granted: true })]
  };
});

// 4. Mock expo-image-manipulator
jest.mock('expo-image-manipulator', () => ({
  manipulateAsync: jest.fn().mockResolvedValue({
    uri: 'file://mock-compressed-photo.jpg',
    width: 800,
    height: 600,
  })
}));

// 5. Mock Supabase JS Client API
export const mockSupabaseClient = {
  auth: {
    signInWithPassword: jest.fn().mockResolvedValue({ data: { session: { token: 'mock-token' } }, error: null }),
    signOut: jest.fn().mockResolvedValue({ error: null }),
    getSession: jest.fn().mockResolvedValue({ data: { session: null }, error: null }),
    onAuthStateChange: jest.fn(() => ({ data: { subscription: { unsubscribe: jest.fn() } } }))
  },
  from: jest.fn().mockReturnValue({
    select: jest.fn().mockReturnThis(),
    insert: jest.fn().mockReturnThis(),
    update: jest.fn().mockReturnThis(),
    eq: jest.fn().mockReturnThis(),
    then: jest.fn((resolve) => resolve({ data: [], error: null }))
  }),
  storage: {
    from: jest.fn().mockReturnValue({
      upload: jest.fn().mockResolvedValue({ data: { path: 'mock-supabase-path.jpg' }, error: null })
    })
  }
};

jest.mock('@supabase/supabase-js', () => ({
  createClient: () => mockSupabaseClient
}));

// 6. Mock React Native Async Storage
jest.mock('@react-native-async-storage/async-storage', () => 
  require('@react-native-async-storage/async-storage/jest/async-storage-mock')
);
```

---

### D. Detailed Tier-by-Tier Testing Structure

#### Tier 1: Functional Flow Integration (Happy Path)
- **Objective**: Verify a worker's complete journey from login to submitting an advance under ideal online conditions.
- **Execution Flow**:
  1. Render `App` container using `render(<App />)`.
  2. Locate input fields on `LoginScreen`, input email (`test@test.cl`) and password (`123456`). Press the Login button.
  3. Verify that `supabase.auth.signInWithPassword` was called with correct parameters.
  4. Mock the profile API returns `role: 'jefe_obra'`. Assert navigation shifts to the main `HomeScreen`.
  5. The sync manager should trigger an automatic fetch of works (`obras`, `items_obra`). Verify that SQLite helper runs `runSync()` to create local schema and insert the returned rows.
  6. On `SelectionFlowScreen`, simulate choosing an `Obra`, a plan, and an `ItemObra` via picker/button interactions.
  7. Navigate to the `CameraScreen`. Verify that clicking "Capture" triggers image manipulation compression.
  8. Enter `Progress (e.g. 50%)`, and click "Register".
  9. Assert that SQLite holds a row in `avances` with `synced = 0`.
  10. Assert that the sync engine triggers immediately, uploads the image file to Supabase storage, inserts the row in the remote table, and updates the local SQLite status to `synced = 1`.
  11. Check that a Success Toast component is rendered.

#### Tier 2: Edge Cases & Resource Constraints
- **Objective**: Verify application resilience during network dropouts, empty states, input limits, and compression constraints.
- **Execution Flow**:
  1. **Offline Queueing**:
     - Call `toggleNetwork(false)` in the test.
     - Complete selection flow, capture image mock, and click "Register".
     - Assert that the app did *not* invoke Supabase API calls.
     - Assert that SQLite has successfully stored the row in `avances` with `synced = 0`.
     - Verify that a warning Toast shows the offline status color `#EF4444` and states "Guardado localmente".
  2. **Empty States**:
     - Configure the SQLite mock to return empty arrays for works queries.
     - Render `HomeScreen`. Verify text "No tiene obras asignadas" is displayed.
     - Assert that the "Start Progress" button is disabled.
  3. **Input Range & Boundary Checks**:
     - User inputs `-10%` or `150%` progress. Assert input verification shows warnings and blocks form submission.
  4. **Image Compression Logic**:
     - Pass a heavy image mock representation. Check that the image compressor utility is invoked with quality reduction parameters and output file meets constraints.

#### Tier 3: Resiliency, Recovery, & Synchronization
- **Objective**: Verify reliable transitions from offline to online states and self-recovery during crashes or partial network errors.
- **Execution Flow**:
  1. **Offline-to-Online Sync (Network Flapping)**:
     - Keep network offline (`toggleNetwork(false)`). Record 3 advances in SQLite.
     - Turn connection back on (`toggleNetwork(true)`).
     - Run Jest timer functions (`jest.runOnlyPendingTimers()`) to trigger the sync scheduler.
     - Verify that the sync engine correctly reads all 3 pending advances from SQLite, performs sequential Supabase uploads (images followed by data rows), and writes `synced = 1` for all rows.
     - Verify that Toast notifications display sync updates.
  2. **Partial Sync Failures**:
     - Place 3 items in the offline queue.
     - Turn connection online. Program the Supabase client mock to throw an API timeout exception on the 2nd upload.
     - Run sync scheduler.
     - Assert that the 1st item updates to `synced = 1` (uploaded successfully).
     - Assert that the 2nd and 3rd items remain `synced = 0`.
     - Ensure the sync process terminates gracefully with a Toast warning without crashing the app.
  3. **Crash Recovery (State Persistence)**:
     - Simulate an application crash by unmounting the entire React components tree.
     - In the next test step, mount the application again.
     - Ensure that the SQLite DB still holds the queued data.
     - Turn the network online. Verify the background sync process automatically starts uploading the previously stored data.

#### Tier 4: Stress and Workload Simulation
- **Objective**: Avoid database bottlenecks, race conditions, memory leaks, and UI blockages during mass actions.
- **Execution Flow**:
  1. **Bulk Seeding**:
     - Seed the SQLite mock with 1,000 progress records.
     - Render history screens. Verify that pagination or virtualized list renders within acceptable limits and does not crash the Node runtime.
  2. **Race Conditions & Double Click Prevention**:
     - Mount the "Register" advance screen.
     - Trigger multiple rapid clicks on the submit button (`fireEvent.press` multiple times synchronously).
     - Assert that the SQLite insert utility is called exactly once.
     - Assert that Supabase client receives only one request.
  3. **Heavy Sync Pipeline Processing**:
     - Seed 100 unsynced records into SQLite, each with large image data mocks.
     - Trigger the sync engine. Check that execution occurs sequentially and does not block Jest's internal thread (by asserting that other parallel events can resolve concurrently).

---

## 5. Verification Method

### A. Independent Verification Instructions
To verify the implementation of this testing strategy once the app is initialized:
1. Navigate to the `app_trackeo_avances` directory.
2. Initialize Jest preset by creating `jest.config.js` and `__tests__/setup.js` as detailed in Section 4.
3. Run the tests via command line:
   ```bash
   npm run test
   # or
   npx jest
   ```
4. To test SQLite mock functionality specifically, inspect the `setup.js` console output or run a simple sandbox test:
   ```javascript
   import { openDatabaseSync } from 'expo-sqlite';
   test('SQLite Mock behaves like real SQLite', () => {
     const db = openDatabaseSync('test.db');
     db.execSync('CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, val TEXT)');
     db.runSync('INSERT INTO test (val) VALUES (?)', ['hello']);
     const row = db.getFirstSync('SELECT * FROM test');
     expect(row.val).toBe('hello');
   });
   ```

### B. Invalidation Conditions
The testing strategy will be invalidated if:
1. The app adopts an Expo version that deprecates `expo-sqlite` synchronous calls (`openDatabaseSync`, `runSync`, etc.) in favor of a completely different DB client structure that cannot be easily mocked with `better-sqlite3`'s interface.
2. Expo Router or React Navigation version updates introduce custom routing hooks that do not execute inside a Node.js simulated environment, requiring Detox/Appium for basic routing assertions.
