# Original User Request

## Initial Request — 2026-07-29T19:19:21-04:00

You are the Sub-Orchestrator for Milestone 1: Database & Supabase Schema for APPACCURATEK.
Your task is to implement and verify R1 (Supabase PostgreSQL & RLS schema for attendance control):
Tables to create & configure:
- `tipos_maestro` (`id` uuid, `nombre` text, `sueldo_diario` numeric, `created_at` timestamptz)
- `maestros` (`id` uuid, `rut` text unique, `nombre_completo` text, `tipo_maestro_id` fk tipos_maestro, `telefono` text, `activo` bool, `created_at` timestamptz)
- `obras_maestros` (`id` uuid, `obra_id` fk obras, `maestro_id` fk maestros, `created_at` timestamptz, UNIQUE(obra_id, maestro_id))
- `asistencia_diaria` (`id` uuid, `obra_id` fk obras, `fecha` date, `foto_evidencia_url` text, `es_correctivo` bool, `registrado_por` fk perfiles_usuario, `created_at` timestamptz)
- `asistencia_diaria_detalle` (`id` uuid, `asistencia_diaria_id` fk asistencia_diaria, `maestro_id` fk maestros, `estado_asistencia` numeric(3,1) check in (1.0, 0.5, 0.0), `observaciones` text, `created_at` timestamptz, UNIQUE(asistencia_diaria_id, maestro_id))
Set up proper FK constraints, performance indexes, and RLS policies (allow reading and writing for authenticated users / active profiles).

Your working directory is `C:\Users\fcola\Desktop\APPACCURATEK\.agents\milestone_1_orchestrator`.
Create your `SCOPE.md`, `plan.md`, `progress.md`, and `BRIEFING.md`.
Follow the Explorer -> Worker -> Reviewer -> Challenger -> Auditor iteration loop.
Verify all database schemas, FKs, indexes, and RLS policies programmatically via a verification script.
Deliver `handoff.md` when complete and report back to parent.
