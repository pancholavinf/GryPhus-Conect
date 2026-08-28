-- =============================================================================
-- MIGRACIÓN 002: Ajuste de Políticas RLS para Control de Personal y Asistencia
-- Aplicar en: Supabase SQL Editor
-- Fecha: 2026-07-30
-- =============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. HABILITAR ROW LEVEL SECURITY (RLS)
-- ─────────────────────────────────────────────────────────────────────────────
ALTER TABLE public.tipos_maestro ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.maestros ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.obras_maestros ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.asistencia_diaria ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.asistencia_diaria_detalle ENABLE ROW LEVEL SECURITY;

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. LIMPIAR POLÍTICAS ANTERIORES PARA EVITAR CONFLICTOS
-- ─────────────────────────────────────────────────────────────────────────────
DROP POLICY IF EXISTS "tipos_maestro_admin_all" ON public.tipos_maestro;
DROP POLICY IF EXISTS "tipos_maestro_jefe_select" ON public.tipos_maestro;
DROP POLICY IF EXISTS "tipos_maestro_select_policy" ON public.tipos_maestro;
DROP POLICY IF EXISTS "tipos_maestro_insert_policy" ON public.tipos_maestro;
DROP POLICY IF EXISTS "tipos_maestro_update_policy" ON public.tipos_maestro;
DROP POLICY IF EXISTS "tipos_maestro_delete_policy" ON public.tipos_maestro;
DROP POLICY IF EXISTS "tipos_maestro_authenticated_all" ON public.tipos_maestro;

DROP POLICY IF EXISTS "maestros_admin_all" ON public.maestros;
DROP POLICY IF EXISTS "maestros_jefe_select" ON public.maestros;
DROP POLICY IF EXISTS "maestros_select_policy" ON public.maestros;
DROP POLICY IF EXISTS "maestros_insert_policy" ON public.maestros;
DROP POLICY IF EXISTS "maestros_update_policy" ON public.maestros;
DROP POLICY IF EXISTS "maestros_delete_policy" ON public.maestros;
DROP POLICY IF EXISTS "maestros_authenticated_all" ON public.maestros;

DROP POLICY IF EXISTS "obras_maestros_admin_all" ON public.obras_maestros;
DROP POLICY IF EXISTS "obras_maestros_jefe_select" ON public.obras_maestros;
DROP POLICY IF EXISTS "obras_maestros_select_policy" ON public.obras_maestros;
DROP POLICY IF EXISTS "obras_maestros_insert_policy" ON public.obras_maestros;
DROP POLICY IF EXISTS "obras_maestros_update_policy" ON public.obras_maestros;
DROP POLICY IF EXISTS "obras_maestros_delete_policy" ON public.obras_maestros;
DROP POLICY IF EXISTS "obras_maestros_authenticated_all" ON public.obras_maestros;

DROP POLICY IF EXISTS "asistencia_diaria_admin_all" ON public.asistencia_diaria;
DROP POLICY IF EXISTS "asistencia_diaria_jefe_select" ON public.asistencia_diaria;
DROP POLICY IF EXISTS "asistencia_diaria_jefe_insert" ON public.asistencia_diaria;
DROP POLICY IF EXISTS "asistencia_diaria_select_policy" ON public.asistencia_diaria;
DROP POLICY IF EXISTS "asistencia_diaria_insert_policy" ON public.asistencia_diaria;
DROP POLICY IF EXISTS "asistencia_diaria_update_policy" ON public.asistencia_diaria;
DROP POLICY IF EXISTS "asistencia_diaria_delete_policy" ON public.asistencia_diaria;
DROP POLICY IF EXISTS "asistencia_diaria_authenticated_all" ON public.asistencia_diaria;

DROP POLICY IF EXISTS "asistencia_detalle_admin_all" ON public.asistencia_diaria_detalle;
DROP POLICY IF EXISTS "asistencia_detalle_jefe_select" ON public.asistencia_diaria_detalle;
DROP POLICY IF EXISTS "asistencia_detalle_jefe_insert" ON public.asistencia_diaria_detalle;
DROP POLICY IF EXISTS "asistencia_diaria_detalle_select_policy" ON public.asistencia_diaria_detalle;
DROP POLICY IF EXISTS "asistencia_diaria_detalle_insert_policy" ON public.asistencia_diaria_detalle;
DROP POLICY IF EXISTS "asistencia_diaria_detalle_update_policy" ON public.asistencia_diaria_detalle;
DROP POLICY IF EXISTS "asistencia_diaria_detalle_delete_policy" ON public.asistencia_diaria_detalle;
DROP POLICY IF EXISTS "asistencia_diaria_detalle_authenticated_all" ON public.asistencia_diaria_detalle;

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. CREAR POLÍTICAS UNIFICADAS PARA USUARIOS AUTENTICADOS (JEFES DE OBRA Y ADMINS)
-- Permite SELECT, INSERT, UPDATE, DELETE para operaciones directas y .upsert()
-- ─────────────────────────────────────────────────────────────────────────────

-- 3.1. tipos_maestro
CREATE POLICY "tipos_maestro_authenticated_all"
    ON public.tipos_maestro FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- 3.2. maestros
CREATE POLICY "maestros_authenticated_all"
    ON public.maestros FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- 3.3. obras_maestros
CREATE POLICY "obras_maestros_authenticated_all"
    ON public.obras_maestros FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- 3.4. asistencia_diaria
CREATE POLICY "asistencia_diaria_authenticated_all"
    ON public.asistencia_diaria FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- 3.5. asistencia_diaria_detalle
CREATE POLICY "asistencia_diaria_detalle_authenticated_all"
    ON public.asistencia_diaria_detalle FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- =============================================================================
-- FIN DE MIGRACIÓN 002
-- =============================================================================
