# Orchestration Plan: Milestone 4

## Objective
Implement R2 Offline Attendance & Sync for `app_trackeo_avances`.

## Strategy & Topology
Pattern: Project (Sub-orchestrator) using Explorer -> Worker -> Reviewer -> Challenger -> Auditor iteration loop.

### Iteration 1 Topology:
1. **Exploration (3 Explorers in parallel)**:
   - `explorer_1`: Focus on SQLite schema (`src/database/db.js`) and sync functions (`src/database/sync.js`).
   - `explorer_2`: Focus on UI screens (`src/screens/ObraMenuScreen.js` and `src/screens/AsistenciaScreen.js`), photo capture integration.
   - `explorer_3`: Focus on test runner, existing test suites, mock setups, and Hermes compatibility requirements.
2. **Implementation (1 Worker)**:
   - Implement SQLite tables, navigation, AsistenciaScreen, photo pipeline, and Supabase sync logic. Run unit/integration tests.
3. **Review (2 Reviewers in parallel)**:
   - Independent verification of code quality, offline SQLite behavior, error handling, Hermes photo handling, and test passing.
4. **Adversarial Verification (2 Challengers in parallel)**:
   - Empirical test execution, edge case testing (e.g. offline/online transition, photo upload failures, corrective attendance flags, partial selections).
5. **Forensic Integrity Audit (1 Auditor)**:
   - Static analysis and integrity check (verify genuine logic, no hardcoded responses, clean audit verdict).

## Timeline / Milestone Gates
- [ ] Phase 1: Exploration complete & strategy compiled
- [ ] Phase 2: Worker implementation & unit/integration test run complete
- [ ] Phase 3: Reviewer verification complete
- [ ] Phase 4: Challenger verification complete
- [ ] Phase 5: Forensic Auditor CLEAN verdict
- [ ] Phase 6: Final handoff delivery to parent orchestrator
