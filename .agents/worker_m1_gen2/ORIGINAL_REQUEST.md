## 2026-07-14T13:49:54Z

You are the Worker subagent for Milestone 1 (Generation 2, Iteration 2). Your working directory is C:/Users/fcola/Desktop/APPACCURATEK/.agents/worker_m1_gen2/.
Your mission is to implement the refactoring and fixes for the React Native Expo application inside `C:/Users/fcola/Desktop/APPACCURATEK/app_trackeo_avances/` based on the findings from the Forensic Auditor, Challengers, and Explorer 3 Gen 2.

## Detailed Refactoring Instructions:
1. **Theme Colors & Fonts (`src/constants/theme.js`)**:
   - Add `textLight: '#64748B'` and `synced: '#10B981'` to `COLORS`.
   - Update `FONTS` to map variants (e.g. `headingBold: 'Montserrat-Bold'`, `bodyBold: 'Inter-Bold'`).
2. **SQLite Database Update (`src/database/db.js`)**:
   - Add `ubicacion TEXT` and `plano TEXT` to the `items_obra` table schema definition.
   - Run safe `ALTER TABLE items_obra ADD COLUMN ubicacion TEXT;` and `ALTER TABLE items_obra ADD COLUMN plano TEXT;` at the end of database initialization to migrate existing databases.
   - Handle database initialization errors safely (log error and throw/propagate) instead of silently proceeding.
3. **App Loader & Sync Protection (`App.js`)**:
   - Prevent the login screen flash on startup by introducing a state `isAuthChecking` (initially `true`) which blocks navigator loading until the initial session check has resolved. Keep splash screen visible (`return null` in App rendering) until `fontsLoaded && dbReady && !isAuthChecking` is true.
   - Prevent concurrent race conditions when synchronizing the catalog by implementing a locking ref (`isSyncingRef.current`) inside `App.js` around the calls to `syncCatalog`.
   - Build a simple error fallback viewport if database initialization fails (`dbError` is set) rather than silently proceeding.
4. **Cascading Selectors & Camera Integration (`src/screens/SelectionFlowScreen.js`)**:
   - Implement cascading pickers for Location (`ubicacion`) and Plan (`plano`) before selecting the Item. Extract unique locations and plans dynamically from the loaded items list.
   - For backwards compatibility with Jest headless test mocks (which only have a single location/plan and expect direct selection), implement auto-selection: if only 1 location is available, auto-select it and show plans; if only 1 plan is available, auto-select it and show items.
   - Remove the camera facade. Integrate the actual `CameraView` component and camera permissions (`useCameraPermissions`) from `expo-camera`. Ask for permissions before showing camera.
   - Keep E2E test compatibility: if `process.env.NODE_ENV === 'test'`, bypass showing the real camera viewfinder and immediately run the mock compression to set `photoUri` to mock raw image file path. Otherwise, show the viewfinder overlay, capture using the camera ref's `takePictureAsync`, compress the photo, and update the UI.
5. **Supabase Synchronizer (`src/database/sync.js` & SQLite catalog inserts)**:
   - Insert `ubicacion` and `plano` columns during SQLite insert OR replace.
   - Generate `fecha_subida_servidor` timestamp on the client, insert it in the Supabase upload payload, and use that exact same timestamp to mark the SQLite sync record.
6. **Android Font Layout Styling**:
   - Inspect `src/screens/LoginScreen.js`, `src/screens/HomeScreen.js`, and `src/screens/SelectionFlowScreen.js`. Ensure that no custom fonts are combined with `fontWeight: 'bold'` or `fontWeight: '600'`. Instead, reference specific font variant families (like `'Montserrat-Bold'` or `'Inter-Bold'`) from `theme.js` directly.
7. **Verification**:
   - Run E2E test suite inside `app_trackeo_avances/` using `npm run test:e2e` and make sure all tests pass.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Please report your refactoring output in a handoff report at C:/Users/fcola/Desktop/APPACCURATEK/.agents/worker_m1_gen2/handoff.md and message me when complete.
