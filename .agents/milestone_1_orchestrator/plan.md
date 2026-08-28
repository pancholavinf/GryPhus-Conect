# Plan: Milestone 1 - Database & Supabase Schema Orchestration

## Iteration Loop Plan (Project Pattern)
1. **Phase 1: Exploration**
   - Spawn 3 Explorer agents (`teamwork_preview_explorer`) in parallel.
   - Task: Inspect codebase, existing Supabase setup, migrations, existing tables (`obras`, `perfiles_usuario`), environment files, and verification mechanisms.
   - Working directories: `.agents/explorer_m1_1`, `.agents/explorer_m1_2`, `.agents/explorer_m1_3`.

2. **Phase 2: Implementation**
   - Spawn 1 Worker agent (`teamwork_preview_worker`) armed with Supabase skill (`C:\Users\fcola\Desktop\APPACCURATEK\.agents\skills\supabase\SKILL.md`).
   - Task: Create SQL migration files, apply migrations/schema, write programmatic schema & RLS verification script, execute script, and capture outputs.
   - Working directory: `.agents/worker_m1_1`.

3. **Phase 3: Review**
   - Spawn 2 Reviewer agents (`teamwork_preview_reviewer`) independently.
   - Task: Inspect SQL quality, schema specs, FKs, indexes, RLS policies, verification script correctness.
   - Working directories: `.agents/reviewer_m1_1`, `.agents/reviewer_m1_2`.

4. **Phase 4: Challenge**
   - Spawn 2 Challenger agents (`teamwork_preview_challenger`).
   - Task: Run empirical tests, stress test schema, edge cases, check RLS enforcement.
   - Working directories: `.agents/challenger_m1_1`, `.agents/challenger_m1_2`.

5. **Phase 5: Forensic Audit**
   - Spawn 1 Forensic Auditor agent (`teamwork_preview_auditor`).
   - Task: Forensic audit for code/test integrity (zero tolerance for cheating/facades).
   - Working directory: `.agents/auditor_m1_1`.

6. **Phase 6: Synthesis & Handoff**
   - Synthesize results, document in `handoff.md`, notify parent.
