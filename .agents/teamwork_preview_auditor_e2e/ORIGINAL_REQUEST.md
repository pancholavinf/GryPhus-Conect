## 2026-07-14T13:37:58Z
Role: Forensic Auditor
Objective: Perform an integrity audit on the E2E test suite and application code located in C:/Users/fcola/Desktop/APPACCURATEK/app_trackeo_avances/.

Detailed Tasks:
1. Examine all files inside app_trackeo_avances/ including tests/, src/, package.json, and other configuration files.
2. Check for integrity violations or cheating:
   - Verify that tests do not use hardcoded test results, fake verification outputs, or mocked results that bypass actual code execution.
   - Verify that there are no dummy/facade implementations in the application code (e.g., methods returning mock responses instead of implementing actual logic).
   - Verify that all database and file operations in the application code and tests run authentic queries.
3. Check the code layout against C:/Users/fcola/Desktop/APPACCURATEK/.agents/orchestrator/PROJECT.md.
4. Document all findings and provide a clean or fail verdict in a report handoff.md in your working directory C:/Users/fcola/Desktop/APPACCURATEK/.agents/teamwork_preview_auditor_e2e/.
5. Notify the E2E Testing Orchestrator (parent) via send_message with your verdict and the path to your report.

MANDATORY WARNING: Do not skip any checks. If any violation is found, report it explicitly as INTEGRITY VIOLATION.
