# E2E Test Suite Plan

## Architecture & Design Goals
- Target directory: `C:/Users/fcola/Desktop/APPACCURATEK/app_trackeo_avances/`
- Test runner: Jest (with ts-jest or babel-jest) or a Node-based simulated testing framework.
- Methodology: Opaque-box testing simulating the React Native environment, including SQLite (simulated via an in-memory/mocked driver if needed or using sqlite3) and Supabase connectivity.
- Coverage tiers:
  - Tier 1: Feature coverage
  - Tier 2: Boundary/Corner cases
  - Tier 3: Cross-feature combinations
  - Tier 4: Real-world workload scenario

## Milestones
1. **Milestone 1: Exploration & Setup**
   - Check if `app_trackeo_avances` is created. If not, wait/create the skeleton.
   - Design the `TEST_INFRA.md` document outlining test runners, mock strategy, and test files.
   - Output: `TEST_INFRA.md` created.
2. **Milestone 2: Implementation of E2E Tests (Tiers 1-4)**
   - Implement the opaque-box simulated tests under `app_trackeo_avances/tests/`.
   - Output: Test files for Tiers 1-4.
3. **Milestone 3: Package Integration & Run**
   - Add `"test:e2e"` script in `app_trackeo_avances/package.json`.
   - Install test dependencies (Jest, sqlite3/mock, etc.).
   - Execute the test suite and verify passing results.
   - Output: Updated `package.json`, passing test output.
4. **Milestone 4: Completion & Verification**
   - Write `TEST_READY.md`.
   - Run Forensic Auditor to verify.
   - Output: `TEST_READY.md` created, audit clean.
