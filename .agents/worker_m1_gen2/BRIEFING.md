# BRIEFING — 2026-07-14T13:50:00Z

## Mission
Refactor the React Native Expo application, updating theme colors/fonts, migrating SQLite schema safely, implementing auth loading check and synchronization race-condition locking, adding cascading location/plan selectors with Jest compatibility, integrating the real expo-camera, fixing Android custom font layout/fontWeight styling, and verifying all changes pass E2E tests.

## 🔒 My Identity
- Archetype: worker
- Roles: implementer, qa, specialist
- Working directory: C:/Users/fcola/Desktop/APPACCURATEK/.agents/worker_m1_gen2/
- Original parent: dbc475a3-aaff-4e8d-b269-f62fda890938
- Milestone: Milestone 1 (Generation 2, Iteration 2)

## 🔒 Key Constraints
- Network: CODE_ONLY (no external websites/services, no curl/wget/lynx targeting external URLs, can use code search/local commands).
- Minimal changes principle: modify only what is necessary, no unrelated refactoring.
- Do not cheat: no hardcoded test results, expected outputs, or dummy/facade implementations.
- Write only to our own folder C:/Users/fcola/Desktop/APPACCURATEK/.agents/worker_m1_gen2/.

## Current Parent
- Conversation ID: dbc475a3-aaff-4e8d-b269-f62fda890938
- Updated: 2026-07-14T13:50:00Z

## Task Summary
- **What to build**: React Native Expo app updates for DB schema (adding columns `ubicacion` and `plano`), cascading select UI in `SelectionFlowScreen.js`, actual expo-camera implementation (no camera facade), App.js loader/sync locks/error screens, theme/fonts definitions, custom font iOS/Android fontWeight compatibility, and Supabase client uploads.
- **Success criteria**: All E2E tests pass via `npm run test:e2e` run within `app_trackeo_avances/`.
- **Interface contracts**: See user instructions and project files.
- **Code layout**: React Native App using Expo, SQLite database module (`src/database/db.js`), constants (`src/constants/theme.js`), screens (`src/screens/SelectionFlowScreen.js`, `src/screens/LoginScreen.js`, `src/screens/HomeScreen.js`), synchronizer (`src/database/sync.js`), and main entry point (`App.js`).

## Key Decisions Made
- Dumped and referenced loaded skills locally in agent workspace.
- Will verify existing files and run tests before implementing.

## Artifact Index
- C:/Users/fcola/Desktop/APPACCURATEK/.agents/worker_m1_gen2/ORIGINAL_REQUEST.md — Initial parent request content
- C:/Users/fcola/Desktop/APPACCURATEK/.agents/worker_m1_gen2/progress.md — Liveness progress heartbeat tracker
- C:/Users/fcola/Desktop/APPACCURATEK/.agents/worker_m1_gen2/handoff.md — Final handoff report (TBD)

## Change Tracker
- **Files modified**: None yet
- **Build status**: Untested
- **Pending issues**: None

## Quality Status
- **Build/test result**: Untested
- **Lint status**: Untested
- **Tests added/modified**: None yet

## Loaded Skills
- **Source**: C:\Users\fcola\Desktop\APPACCURATEK\.agents\skills\frontend-ui-engineering_skill\SKILL.md
  - **Local copy**: C:\Users\fcola\Desktop\APPACCURATEK\.agents\worker_m1_gen2\skills\frontend-ui-engineering_skill\SKILL.md
  - **Core methodology**: Building production-quality, accessible React Native/React frontends matching design system constraints.
- **Source**: C:\Users\fcola\Desktop\APPACCURATEK\.agents\skills\python-desing-patterns_skill\SKILL.md
  - **Local copy**: C:\Users\fcola\Desktop\APPACCURATEK\.agents\worker_m1_gen2\skills\python-design-patterns_skill\SKILL.md
  - **Core methodology**: Following patterns like KISS, single responsibility, and composition over inheritance.
