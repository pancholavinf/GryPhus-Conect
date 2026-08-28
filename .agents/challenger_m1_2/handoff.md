# Challenger Report — Milestone 1 Verification

This report details the empirical verification, stress testing, and adversarial review of the Expo mobile application `app_trackeo_avances`.

---

## 1. Observation

### E2E Test Suite Run
* **Command Executed**: `npm run test:e2e` in `C:/Users/fcola/Desktop/APPACCURATEK/app_trackeo_avances`
* **Result**: `Test Suites: 4 passed, 4 total; Tests: 8 passed, 8 total`
* **Log Snip**:
```
PASS tests/tier1_feature.test.js
PASS tests/tier2_boundary.test.js
PASS tests/tier3_integration.test.js
PASS tests/tier4_workload.test.js

Test Suites: 4 passed, 4 total
Tests:       8 passed, 8 total
Snapshots:   0 total
Time:        5.862 s, estimated 7 s
Ran all test suites.
```

### Code Base Discoveries

#### 1. Missing Theme Color parameters:
In `src/constants/theme.js` (lines 1-17), there is no `textLight` or `synced` property:
```javascript
export const COLORS = {
  background: '#FAFAFA',
  primary: '#1A529B', // Headers, branding
  secondary: '#EE741D', // CTA
  cta: '#EE741D',
  accent: '#4BA2E3',
  support: '#64748B', // Gris support
  border: '#F1F5F9', // slate-100 style
  white: '#FFFFFF',
  text: '#1F2937',

  // Statuses
  pending: '#F59E0B',
  approved: '#10B981',
  offline: '#EF4444',
  error: '#EF4444',
};
```
However, the components use:
* `HomeScreen.js` (lines 166, 177) and `SelectionFlowScreen.js` (line 231) use `COLORS.textLight`.
* `Toast.js` (line 8) uses `COLORS.synced`:
```javascript
const bgStyle = type === 'offline' ? COLORS.offline : (type === 'synced' ? COLORS.synced : COLORS.pending);
```

#### 2. Startup Database Initialization and Concurrent Syncing Race Conditions:
In `App.js` (lines 46-115), the `useEffect` on mount triggers database initialization and concurrent Supabase requests:
```javascript
  // Initialize DB and fetch session on mount
  useEffect(() => {
    try {
      initDatabase();
      setDbReady(true);
    } catch (error) {
      console.error('Failed to initialize database:', error);
      setDbReady(true); // <-- BUG: setDbReady(true) despite crash!
    }

    // Get initial Supabase auth session safely (mock-resilient)
    if (supabase.auth && typeof supabase.auth.getSession === 'function') {
      supabase.auth.getSession().then(async ({ data: { session: activeSession } }) => {
        if (activeSession) {
          ...
          try {
            await syncCatalog(profile.id);
          } catch (err) { ... }
          ...
        }
      });
    }

    // Listen for auth state changes safely
    let subscription = null;
    if (supabase.auth && typeof supabase.auth.onAuthStateChange === 'function') {
      const authListener = supabase.auth.onAuthStateChange(async (_event, activeSession) => {
        if (activeSession) {
          ...
          try {
            await syncCatalog(profile.id);
          } catch (err) { ... }
          ...
        }
      });
      ...
    }
```
* **Observation**: Both `getSession()` and `onAuthStateChange()` fire concurrently on app startup. Both attempt to execute `syncCatalog()` in parallel without locking.
* **Observation**: In the `initDatabase` try-catch block, if an exception is thrown during SQLite setup, it is caught, logged, but the state `setDbReady(true)` is still executed, which will trigger the layout to load screens that depend on SQLite.

#### 3. Font Family + Weight Combinations:
In `LoginScreen.js` (line 100) and `HomeScreen.js` (line 128), text elements apply custom font families with a manual font weight override:
```javascript
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.primary,
    fontFamily: 'Montserrat',
    ...
  }
```
* **Observation**: In React Native, custom fonts should be selected via their dedicated loaded families (e.g. `'Montserrat-Bold'`) without combining them with manual `fontWeight: 'bold'` settings, which causes styling warnings/issues on Android.

---

## 2. Logic Chain

1. **E2E Correctness**: The Headless E2E tests run on a Node/Jest-mocked SQLite, NetInfo, and Supabase client environment. All 8 tests passed successfully, confirming that the main application logic, synchronization cycles, offline queuing, image manipulations, and double-click debounces function correctly under standard scenarios.
2. **Missing Theme Parameters**: Since `COLORS.textLight` and `COLORS.synced` are absent in `theme.js`, any React Native stylesheet invoking them will receive `undefined`. On the Toast container, setting `backgroundColor: undefined` causes the background to render transparent or default gray/black, rendering the success toast unreadable and breaking the visual hierarchy.
3. **Database Setup Resiliency**: The database `catch` block blindly invokes `setDbReady(true)`. If the SQLite engine fails to run schema creations (e.g. due to permissions, file lock, corruption), the app proceeds to mount views that assume SQLite is ready. When these screens run queries (like fetching active Obras), they will immediately crash the JS thread or display blank states, failing silently without a user-facing error message.
4. **Startup Concurrency Race**: On cold starts with an active session, both the asynchronous `getSession().then(...)` promise and the `onAuthStateChange()` listener callback fire in the same tick. Both trigger `syncCatalog()` asynchronously. SQLite synchronous execution (`runSync`) could lock or crash if parallel writes occur concurrently. Redundant network calls are also made, fetching the catalog twice from Supabase, increasing startup time and data usage.
5. **Styling Inconsistencies**: Defining `fontFamily: 'Montserrat'` and `fontWeight: 'bold'` in stylesheets violates React Native's custom font recommendations. On Android, this combination ignores the custom font altogether and falls back to a system sans-serif bold font.

---

## 3. Caveats

* **No Real-Device / Emulator Testing**: The E2E tests are headless simulated using React Native Testing Library and Jest. True native-layer layout or hardware issues (such as physical camera permissions or background task execution policies on iOS/Android) were not evaluated under a real device environment.
* **Mocks Fidelity**: Mocks for `supabase`, `expo-sqlite`, `expo-image-manipulator`, and `NetInfo` are stateful and match anticipated behavior, but subtle differences in the actual native SDK API return values might exist.

---

## 4. Conclusion & Adversarial Challenge Report

### Overall Risk Assessment: MEDIUM

The core features are functional, well-structured, and pass simulated E2E testing. However, production readiness is hindered by critical styling omissions, race conditions, and silent failover handlers.

### Challenges

#### [High] Challenge 1: Redundant Concurrently Fired Catalog Synchronizations (Race Condition on Client Start)
* **Assumption challenged**: Session retrieval and auth state subscription fire sequentially.
* **Attack scenario**: On application cold boot, both `getSession().then(...)` and `onAuthStateChange()` execute concurrently. Both trigger `syncCatalog()` in parallel.
* **Blast Radius**: Double network requests to Supabase (fetching user profile, works, and work items twice). Redundant concurrent SQLite inserts. Potential database lock exceptions or write conflicts on slow devices.
* **Mitigation**: Introduce a state-lock or ref (`isSyncingCatalogRef.current`) to block redundant parallel calls to `syncCatalog`. Alternatively, let the initial `getSession` call be the sole initial sync runner, and ignore the initial firing of `onAuthStateChange` if the initial state is already loaded.

#### [Medium] Challenge 2: Missing Theme Constants (`COLORS.textLight` and `COLORS.synced`)
* **Assumption challenged**: All colors referenced in visual components exist in the configuration files.
* **Attack scenario**: Application triggers a success toast (`type = 'synced'`).
* **Blast Radius**: Toast component attempts to set `backgroundColor: COLORS.synced` (resolves to `undefined`). Toast displays with a transparent or broken background color, blocking user feedback. Text fields referencing `COLORS.textLight` revert to standard black.
* **Mitigation**: Add missing fields to `src/constants/theme.js`:
  ```javascript
  COLORS.textLight = '#64748B'; // slate-500
  COLORS.synced = '#10B981'; // green-500
  ```

#### [Medium] Challenge 3: SQLite Initialization Silent Failures
* **Assumption challenged**: Database schemas are successfully created on every device.
* **Attack scenario**: Disk is full or SQLite db file is locked/corrupt.
* **Blast Radius**: `initDatabase()` throws an error, which is caught. However, `setDbReady(true)` is called anyway, hiding the splash screen and loading the dashboard. Components crash on render when executing database SELECT operations.
* **Mitigation**: In the catch block of `App.js`, set an error state (`dbError`) and display a fallback screen telling the user the app cannot run due to a local database error. Do NOT set `dbReady(true)`.

#### [Low] Challenge 4: React Native font family style warnings on Android
* **Assumption challenged**: Standard custom font weight inheritance behaves correctly on Android.
* **Attack scenario**: Rendering typography with `fontFamily: 'Montserrat'` and `fontWeight: 'bold'`.
* **Blast Radius**: Platform warning output in logs and layout inconsistencies where Android falls back to system fonts because it cannot load the bold variant dynamically.
* **Mitigation**: Reference specific font families instead, e.g. use `fontFamily: 'Montserrat-Bold'` directly and remove `fontWeight: 'bold'`.

---

## 5. Verification Method

To verify the app correctness and test suite:
1. Run the headless E2E test command inside the app folder:
   ```bash
   npm run test:e2e
   ```
2. Verify all 8 tests pass successfully.
3. Check `src/constants/theme.js` to see the absence of `textLight` and `synced` parameters.
4. Verify references to `COLORS.textLight` in `HomeScreen.js` (lines 166, 177) and `SelectionFlowScreen.js` (line 231).
5. Verify reference to `COLORS.synced` in `Toast.js` (line 8).
