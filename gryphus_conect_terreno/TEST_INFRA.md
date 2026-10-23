# E2E Test Infrastructure for Trackeo Avances

This document describes the design, setup, and methodology of the E2E test suite for the `app_trackeo_avances` React Native (Expo) mobile application.

## 1. Testing Methodology: Headless/Simulated E2E

Testing React Native applications often requires heavy simulators, emulators, or real devices (e.g., using Detox or Appium). While visual testing on real devices is valuable, it introduces execution delays, configuration overhead, and flakiness in automated environments.

To achieve rapid, high-fidelity, and CPU-only E2E validation, this project implements a **Headless/Simulated E2E Testing Strategy**:
- **Execution Environment**: Node.js (command line / CI/CD) using the **Jest** runner with the **`jest-expo`** preset.
- **Component Rendering**: React Native Testing Library (RNTL) via `@testing-library/react-native` is used to mount the entire React component hierarchy (`App.js`), simulate user events (clicks, input typing), and query the render tree.
- **Hardware/Platform Mocks**: Core hardware APIs that do not run in Node (such as SQLite, Camera, Image Compression, and NetInfo) are mocked with **fully stateful implementations** that execute real logic:
  - **SQLite**: Simulated via an in-memory SQL database (using Node's `sqlite3` or `better-sqlite3`), running the actual database schema scripts, storing rows, and validating synchronization fields.
  - **NetInfo**: A mock connection listener that allows tests to toggle `isConnected` status dynamically during runtime.
  - **Camera & Compression**: Pre-programmed mocks that return simulated paths and trigger compression scaling utilities.
  - **Supabase**: Intercepted/mocked client API that captures database payloads and authentication requests to verify data synchronization matches the PRD.

This approach tests the **entire application loop** (Login ➔ Selection ➔ Capture ➔ Database Insert ➔ Network Synchronization) without a browser or emulator.

---

## 2. Dependencies and Setup

### Required Packages (devDependencies)
To execute the tests, the following packages are configured:
- `jest` and `jest-expo`: The testing engine and Expo preset configurations.
- `react-test-renderer`: React Native renderer hook.
- `@testing-library/react-native` and `@testing-library/jest-native`: RNTL assertions and queries.
- `sqlite3` or `better-sqlite3`: Backing database engine for local SQLite simulation under Node.
- `babel-jest` and `@babel/core`: Javascript transpilations.

### Setup Instructions
1. Navigate to the project folder:
   ```bash
   cd C:/Users/fcola/Desktop/APPACCURATEK/app_trackeo_avances/
   ```
2. Install the devDependencies:
   ```bash
   npm install --save-dev jest jest-expo react-test-renderer @testing-library/react-native @testing-library/jest-native sqlite3
   ```
3. Run the E2E test suite:
   ```bash
   npm run test:e2e
   ```

---

## 3. Test Tiers Structure

The test cases are divided into four tiers corresponding to different functional depths:

### Tier 1: Feature Coverage (Happy Path)
- **Login Flow**: Input email/password, hit Login, assert authentication succeeds, and the screen navigates to Home.
- **Selection Flow**: Select Project (Obra), select Phase/Plan, and select work Item from cascading pickers.
- **Camera/Photo**: Trigger photo capture, show image preview.
- **Local DB**: Store the progress record locally in SQLite with `synced = 0`.
- **Supabase Sync**: Verify immediate upload of the photo and the database row to Supabase, updating the local record to `synced = 1`.

### Tier 2: Boundary & Corner Cases
- **Offline Mode**: Toggle NetInfo connection to offline, register progress, verify it stays in SQLite queue with `synced = 0`, and the network layer is not called.
- **Empty States**: Verify the UI displays helpful guidelines when no projects are returned from the database.
- **Input Boundaries**: Attempt to submit progress reports with values out of bounds (negative progress, or exceeding item total quantities) and confirm validation warning banners.
- **Image Compression**: Verify that raw images are compressed before saving, reducing memory print.

### Tier 3: Cross-Feature Combinations (Resilience)
- **Offline to Online Transition**: Record multiple progress entries while offline, toggle connection online, run the sync worker, and verify sequential upload and status updates in SQLite.
- **State Recovery / Crash Test**: Record local progress, simulate an application crash (unmount component tree), restart the app (remount), and verify that unsynced items are successfully read and synchronized.
- **Network Interruptions**: Simulate a network failure in the middle of a sync batch. Check that successfully sent items are marked `synced`, while failed ones stay in the queue, without crashing the app.

### Tier 4: Real-World Workload Scenario
- **High-Volume Workday**: Simulate a manager's day:
  1. Boot app online, download catalog metadata.
  2. Transition offline and record multiple progress logs with photos.
  3. Reconnect to the network.
  4. Record more online advances.
  5. Run bulk synchronization.
  6. Confirm all records are successfully uploaded to the cloud database and synced columns in the SQLite file are updated with valid timestamps.
- **Double Click Prevention**: Rapidly hit the submit button to ensure debouncing works and only one entry is written.
