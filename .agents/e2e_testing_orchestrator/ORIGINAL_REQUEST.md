# Original User Request

## 2026-07-29T19:19:21-04:00

<USER_REQUEST>
You are the E2E Testing Orchestrator for APPACCURATEK.
Your task is to build and manage the opaque-box E2E test suite for the Attendance Control System based on `C:\Users\fcola\Desktop\APPACCURATEK\.agents\orchestrator\PROJECT.md` and user requirements in `C:\Users\fcola\Desktop\APPACCURATEK\.agents\ORIGINAL_REQUEST.md`.
Your working directory is `C:\Users\fcola\Desktop\APPACCURATEK\.agents\e2e_testing_orchestrator`.
Follow the Project Dual Track E2E Testing methodology:
1. Create `TEST_INFRA.md` with test architecture, Category-Partition / BVA / Pairwise / Real-world workload test cases (Tiers 1-4).
2. Implement test scripts/harnesses in Python/JS to verify:
   - Supabase DB schema, FKs, indexes, RLS policies.
   - Desktop App Control de Personal UI CRUD, daily rates, dashboard KPIs, and Excel/PDF attendance reports.
   - Mobile App offline SQLite attendance, 1.0/0.5/0.0 marking, evidence photo requirement, sync.js sync, and Corrective Report handling.
3. When the test infrastructure and test cases are ready, publish `TEST_READY.md` at `C:\Users\fcola\Desktop\APPACCURATEK\TEST_READY.md`.
4. Report completion back to parent (`1fe457b2-a09c-44c8-9bd4-7d097d8632fe` / `c8acb89c-a6f4-4a26-8d24-dab6f3f57aa7` / orchestrator).
</USER_REQUEST>
