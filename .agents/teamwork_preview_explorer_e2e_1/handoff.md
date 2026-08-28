# Handoff Report: Headless E2E Testing Strategy for React Native (Expo)

## 1. Observation

- **Directory Existence**: Checked `C:/Users/fcola/Desktop/APPACCURATEK/app_trackeo_avances/` using workspace directory listings and explicit folder checks. It **does not exist** at this path, nor are there any background tasks running to create it.
- **Current Workspace State**:
  - `app_mobile/`: A KivyMD (Python) app with a simulated `api_service.py` (Kivy UI for login and home screen).
  - `app_local/`: A PyQt/PySide (Python) desktop app.
  - `INFO PROYECTO/`: Contains `PRD y Design System - Track Obra.pdf` which outlines the requirements for a multiplatform ecosystem: a mobile app (Offline-First, SQLite, Supabase sync, camera compression) and a desktop app.
  - No existing React Native / Expo environment, `package.json`, or node_modules are located at the root or within subfolders.

---

## 2. Logic Chain

1. **Objective**: Define a simulated, headless E2E testing strategy using Node.js and Jest for a future React Native (Expo) mobile app (`app_trackeo_avances`).
2. **Reasoning**:
   - Because native mobile environments require emulator/simulator overhead, running unit-like UI integration tests in Jest using **React Native Testing Library (RNTL)** allows for fast, headless, and cost-effective simulated E2E testing on developer machines and in CI/CD pipelines.
   - For simulated E2E to be meaningful, it must execute the **entire application loop** (from rendering the Root component down to database operations and mock network requests) rather than testing isolated components.
   - Native modules (like SQLite, Camera, File System, NetInfo) do not run in Node.js. Therefore, we must implement custom Jest mocks or use lightweight Javascript-equivalent engines (like in-memory sqlite bindings for SQLite, or Mock Service Worker for Supabase) to simulate the device/network environment.

---

## 3. Caveats

- **No Visual/Layout Verification**: Headless E2E testing using Jest/RNTL renders components into a virtual DOM-like hierarchy. It will not detect visual glitches, overlapping layout elements, or CSS/styling differences between iOS and Android.
- **Mock Accuracy**: The tests depend heavily on the accuracy of the mocks (e.g. SQLite query simulation, NetInfo listeners). If the real native implementation of `expo-sqlite` behaves differently under specific conditions than the mock, tests may pass but fail in production.
- **No Native Crash Tracking**: Headless Jest cannot capture true memory leaks or hard native crashes (out-of-memory due to large images) that occur on actual OS platforms.

---

## 4. Conclusion & Strategy Proposal

We propose the following headless E2E testing architecture for the React Native/Expo app when `app_trackeo_avances` is created.

### 4.1 Required Packages

Install these devDependencies in the Expo app's `package.json`:
```json
{
  "devDependencies": {
    "jest": "^29.2.1",
    "jest-expo": "~51.0.0",
    "@testing-library/react-native": "^12.5.0",
    "@testing-library/jest-native": "^5.4.3",
    "msw": "^2.0.0",
    "better-sqlite3": "^9.0.0"
  }
}
```

### 4.2 Test folder structure

```
app_trackeo_avances/
├── __tests__/
│   ├── e2e/
│   │   ├── mocks/
│   │   │   ├── sqlite.mock.js
│   │   │   ├── camera.mock.js
│   │   │   ├── netinfo.mock.js
│   │   │   └── supabase.mock.js
│   │   ├── setup.js
│   │   ├── tier1_happy_path.test.js
│   │   ├── tier2_edge_cases.test.js
│   │   ├── tier3_resilience.test.js
│   │   └── tier4_workload.test.js
```

### 4.3 Key Mocks implementation

#### NetInfo Connection Controller
Allows dynamically toggling the internet state to test Offline-First workflows:
```javascript
// __tests__/e2e/mocks/netinfo.mock.js
let connectionState = { isConnected: true, isInternetReachable: true };
let listeners = [];

export const NetInfoMock = {
  addEventListener: (listener) => {
    listeners.push(listener);
    listener(connectionState);
    return () => {
      listeners = listeners.filter(l => l !== listener);
    };
  },
  fetch: () => Promise.resolve(connectionState),
  // Helper for test runner to change state:
  setConnected: (state) => {
    connectionState = { isConnected: state, isInternetReachable: state };
    listeners.forEach(l => l(connectionState));
  }
};
jest.mock('@react-native-community/netinfo', () => NetInfoMock);
```

#### SQLite Mock with Real SQL execution (In-Memory)
Avoid plain dummy mocks; use `better-sqlite3` to run real queries inside Jest:
```javascript
// __tests__/e2e/mocks/sqlite.mock.js
import Database from 'better-sqlite3';

const inMemoryDb = new Database(':memory:');

jest.mock('expo-sqlite', () => ({
  openDatabaseAsync: async () => ({
    execAsync: async (queries) => {
      inMemoryDb.exec(queries);
    },
    runAsync: async (query, params = []) => {
      const stmt = inMemoryDb.prepare(query);
      const info = stmt.run(...params);
      return { changes: info.changes, lastInsertRowId: info.lastInsertRowId };
    },
    getFirstAsync: async (query, params = []) => {
      const stmt = inMemoryDb.prepare(query);
      return stmt.get(...params);
    },
    getAllAsync: async (query, params = []) => {
      const stmt = inMemoryDb.prepare(query);
      return stmt.all(...params);
    }
  })
}));
```

#### Supabase Network Mocks using MSW
Intercept network requests to verify request payloads:
```javascript
// __tests__/e2e/mocks/supabase.mock.js
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

export const server = setupServer(
  // Auth login interceptor
  http.post('https://*.supabase.co/auth/v1/token', () => {
    return HttpResponse.json({
      access_token: 'mocked_token',
      user: { id: 'jefe-123', email: 'test@test.cl' }
    });
  }),
  // Storage upload interceptor
  http.post('https://*.supabase.co/storage/v1/object/fotos/*', () => {
    return HttpResponse.json({ Key: 'fotos/compressed_image.jpg' }, { status: 200 });
  }),
  // Insert progress log interceptor
  http.post('https://*.supabase.co/rest/v1/avances', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({ id: 'uuid-123', ...body }, { status: 201 });
  })
);
```

---

### 4.4 Test Tiers Structure

#### Tier 1: Happy Path (Login, Selection, Camera, SQLite, Supabase)
- **Objective**: Verify standard operational flow under nominal online conditions.
- **Workflow**:
  1. Render `<App />` via RNTL.
  2. Input user `test@test.cl` and `123456` on Login Screen -> Tap Submit.
  3. Verify redirection to Home -> Show active project select (loaded from mock SQLite or mock Supabase).
  4. Select Project "Edificio Central" -> Select Item "Item 101 (F-60 Metálico)".
  5. Tap "Capture Photo" -> Mock Camera resolves photo path.
  6. Fill in "Advance" (e.g. 50% / 15m²) -> Tap "Send".
  7. Verify:
     - SQLite stores the row with status `pending`.
     - Sync worker gets triggered -> Uploads file & uploads row to Supabase mock.
     - SQLite updates local status to `synced`.
     - UI displays synced status banner/toast.

#### Tier 2: Edge Cases (Offline, Empty, Max, Compression)
- **Objective**: Ensure the system handles resource limitations and offline restrictions correctly.
- **Scenarios**:
  - **Offline operation**: Trigger `NetInfoMock.setConnected(false)`. Record progress. Verify SQLite database holds the record as `pending` and Supabase is not invoked.
  - **Empty states**: Ensure that when SQLite holds 0 projects, the UI displays clear instruction messages ("No assigned projects. Contact administration").
  - **Camera Compression**: Mock camera returning a 5MB raw image. Verify that the compression service reduces image quality/size before saving to local cache.
  - **Boundary/Max Capacity**: Write 500 fake records to mock SQLite to verify pagination/scrolling limits and local DB threshold notifications.

#### Tier 3: Resilience (Offline Sync, Crash Recovery)
- **Objective**: Verify background recovery routines and synchronization queues.
- **Scenarios**:
  - **Reconnection queue sync**:
    1. Set app offline (`NetInfoMock.setConnected(false)`).
    2. Log 3 advances (stores in SQLite as `pending`).
    3. Toggle online (`NetInfoMock.setConnected(true)`).
    4. Verify that background sync reads SQLite, posts requests to MSW (verifying sequential execution), and updates SQLite status to `synced`.
  - **Crash Recovery**:
    1. Render navigation screen, insert draft state in AsyncStorage (simulating mid-entry draft).
    2. Unmount the React tree (simulate crash).
    3. Re-render `<App />`.
    4. Assert that the draft state is read and the screen populates the previously entered details automatically.

#### Tier 4: Load & Stress (Workload, UI Congestion)
- **Objective**: Identify database locks and race conditions.
- **Scenarios**:
  - **Concurrent Queue Sync**: Simulate 50 pending records in local database. Switch online and verify that bulk operations are batched or throttled to avoid memory spikes and Supabase rate limiting.
  - **Debouncing Inputs**: Rapidly press "Submit" 5 times in less than 1 second. Verify that only a single SQLite record is written and only one network payload is fired.

---

## 5. Verification Method

To verify the proposed strategy once `app_trackeo_avances` is set up:
1. Create the `package.json` with devDependencies listed in Section 4.1.
2. Initialize Jest config `jest.config.js` pointing to the setup file `__tests__/e2e/setup.js`.
3. Put the mock files under `__tests__/e2e/mocks/`.
4. Run the test command:
   ```bash
   npm test
   ```
5. Assert that the runner logs suite completions without errors and correctly resolves simulated asynchronous storage / network events.
