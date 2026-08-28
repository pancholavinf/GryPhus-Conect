# Supabase Skill Summary

Source: `C:\Users\fcola\Desktop\APPACCURATEK\.agents\skills\supabase\SKILL.md`

## Key Rules & Guidelines from Supabase Skill:
- Enable RLS on every table in exposed schemas (`public`).
- `auth.role()` is deprecated — use `TO authenticated` / `TO anon` clauses instead on RLS policies.
- RLS Policy standard pattern:
  - `to authenticated`
  - `using (...)`
  - For UPDATE: specify both `using (...)` and `with check (...)`.
- Exposing tables to Data API / Grants: `GRANT SELECT, INSERT, UPDATE, DELETE ON <table_name> TO authenticated;` (if needed for Data API exposure, plus enabling RLS).
- Use `execute_sql` or direct PostgreSQL connection / migrations to apply schema.
- Run advisors / verification checks.
