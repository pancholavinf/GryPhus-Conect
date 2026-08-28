-- ============================================================================
-- SQL MIGRATION / SCHEMA DEFINITION FOR R1 (ATTENDANCE CONTROL)
-- APPACCURATEK - Supabase PostgreSQL & RLS Schema
-- ============================================================================

-- Ensure referenced tables exist (if not already created)
CREATE TABLE IF NOT EXISTS public.perfiles_usuario (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre text NOT NULL,
    email text,
    clave text,
    rol text NOT NULL DEFAULT 'Jefe_Obra',
    foto_perfil_url text,
    telefono text,
    created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.obras (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre text NOT NULL,
    estado text NOT NULL DEFAULT 'Activa',
    color text DEFAULT '#1A529B',
    fecha_creacion timestamptz DEFAULT now()
);

-- 1. Table: tipos_maestro
CREATE TABLE IF NOT EXISTS public.tipos_maestro (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre text NOT NULL,
    sueldo_diario numeric NOT NULL,
    created_at timestamptz DEFAULT now()
);

-- 2. Table: maestros
CREATE TABLE IF NOT EXISTS public.maestros (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    rut text UNIQUE NOT NULL,
    nombre_completo text NOT NULL,
    tipo_maestro_id uuid REFERENCES public.tipos_maestro(id) ON DELETE RESTRICT,
    telefono text,
    activo boolean NOT NULL DEFAULT true,
    created_at timestamptz DEFAULT now()
);

-- 3. Table: obras_maestros
CREATE TABLE IF NOT EXISTS public.obras_maestros (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    obra_id uuid REFERENCES public.obras(id) ON DELETE CASCADE,
    maestro_id uuid REFERENCES public.maestros(id) ON DELETE CASCADE,
    created_at timestamptz DEFAULT now(),
    CONSTRAINT uq_obras_maestros UNIQUE (obra_id, maestro_id)
);

-- 4. Table: asistencia_diaria
CREATE TABLE IF NOT EXISTS public.asistencia_diaria (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    obra_id uuid REFERENCES public.obras(id) ON DELETE CASCADE,
    fecha date NOT NULL,
    foto_evidencia_url text,
    es_correctivo boolean NOT NULL DEFAULT false,
    registrado_por uuid REFERENCES public.perfiles_usuario(id),
    created_at timestamptz DEFAULT now()
);

-- 5. Table: asistencia_diaria_detalle
CREATE TABLE IF NOT EXISTS public.asistencia_diaria_detalle (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    asistencia_diaria_id uuid REFERENCES public.asistencia_diaria(id) ON DELETE CASCADE,
    maestro_id uuid REFERENCES public.maestros(id) ON DELETE RESTRICT,
    estado_asistencia numeric(3,1) NOT NULL CHECK (estado_asistencia IN (1.0, 0.5, 0.0)),
    observaciones text,
    created_at timestamptz DEFAULT now(),
    CONSTRAINT uq_asistencia_diaria_detalle UNIQUE (asistencia_diaria_id, maestro_id)
);

-- ============================================================================
-- PERFORMANCE & FOREIGN KEY INDEXES
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_maestros_tipo_maestro_id ON public.maestros(tipo_maestro_id);
CREATE INDEX IF NOT EXISTS idx_maestros_rut ON public.maestros(rut);
CREATE INDEX IF NOT EXISTS idx_maestros_activo ON public.maestros(activo);

CREATE INDEX IF NOT EXISTS idx_obras_maestros_obra_id ON public.obras_maestros(obra_id);
CREATE INDEX IF NOT EXISTS idx_obras_maestros_maestro_id ON public.obras_maestros(maestro_id);

CREATE INDEX IF NOT EXISTS idx_asistencia_diaria_obra_id ON public.asistencia_diaria(obra_id);
CREATE INDEX IF NOT EXISTS idx_asistencia_diaria_fecha ON public.asistencia_diaria(fecha);
CREATE INDEX IF NOT EXISTS idx_asistencia_diaria_obra_fecha ON public.asistencia_diaria(obra_id, fecha);
CREATE INDEX IF NOT EXISTS idx_asistencia_diaria_registrado_por ON public.asistencia_diaria(registrado_por);

CREATE INDEX IF NOT EXISTS idx_asistencia_diaria_detalle_asistencia_id ON public.asistencia_diaria_detalle(asistencia_diaria_id);
CREATE INDEX IF NOT EXISTS idx_asistencia_diaria_detalle_maestro_id ON public.asistencia_diaria_detalle(maestro_id);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

ALTER TABLE public.tipos_maestro ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.maestros ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.obras_maestros ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.asistencia_diaria ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.asistencia_diaria_detalle ENABLE ROW LEVEL SECURITY;

-- Ensure authenticated role exists (if on vanilla PostgreSQL)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        CREATE ROLE authenticated;
    END IF;
END $$;

-- 1. tipos_maestro RLS Policies
DROP POLICY IF EXISTS "tipos_maestro_select_policy" ON public.tipos_maestro;
CREATE POLICY "tipos_maestro_select_policy" ON public.tipos_maestro FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "tipos_maestro_insert_policy" ON public.tipos_maestro;
CREATE POLICY "tipos_maestro_insert_policy" ON public.tipos_maestro FOR INSERT TO authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "tipos_maestro_update_policy" ON public.tipos_maestro;
CREATE POLICY "tipos_maestro_update_policy" ON public.tipos_maestro FOR UPDATE TO authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "tipos_maestro_delete_policy" ON public.tipos_maestro;
CREATE POLICY "tipos_maestro_delete_policy" ON public.tipos_maestro FOR DELETE TO authenticated USING (true);

-- 2. maestros RLS Policies
DROP POLICY IF EXISTS "maestros_select_policy" ON public.maestros;
CREATE POLICY "maestros_select_policy" ON public.maestros FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "maestros_insert_policy" ON public.maestros;
CREATE POLICY "maestros_insert_policy" ON public.maestros FOR INSERT TO authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "maestros_update_policy" ON public.maestros;
CREATE POLICY "maestros_update_policy" ON public.maestros FOR UPDATE TO authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "maestros_delete_policy" ON public.maestros;
CREATE POLICY "maestros_delete_policy" ON public.maestros FOR DELETE TO authenticated USING (true);

-- 3. obras_maestros RLS Policies
DROP POLICY IF EXISTS "obras_maestros_select_policy" ON public.obras_maestros;
CREATE POLICY "obras_maestros_select_policy" ON public.obras_maestros FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "obras_maestros_insert_policy" ON public.obras_maestros;
CREATE POLICY "obras_maestros_insert_policy" ON public.obras_maestros FOR INSERT TO authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "obras_maestros_update_policy" ON public.obras_maestros;
CREATE POLICY "obras_maestros_update_policy" ON public.obras_maestros FOR UPDATE TO authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "obras_maestros_delete_policy" ON public.obras_maestros;
CREATE POLICY "obras_maestros_delete_policy" ON public.obras_maestros FOR DELETE TO authenticated USING (true);

-- 4. asistencia_diaria RLS Policies
DROP POLICY IF EXISTS "asistencia_diaria_select_policy" ON public.asistencia_diaria;
CREATE POLICY "asistencia_diaria_select_policy" ON public.asistencia_diaria FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "asistencia_diaria_insert_policy" ON public.asistencia_diaria;
CREATE POLICY "asistencia_diaria_insert_policy" ON public.asistencia_diaria FOR INSERT TO authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "asistencia_diaria_update_policy" ON public.asistencia_diaria;
CREATE POLICY "asistencia_diaria_update_policy" ON public.asistencia_diaria FOR UPDATE TO authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "asistencia_diaria_delete_policy" ON public.asistencia_diaria;
CREATE POLICY "asistencia_diaria_delete_policy" ON public.asistencia_diaria FOR DELETE TO authenticated USING (true);

-- 5. asistencia_diaria_detalle RLS Policies
DROP POLICY IF EXISTS "asistencia_diaria_detalle_select_policy" ON public.asistencia_diaria_detalle;
CREATE POLICY "asistencia_diaria_detalle_select_policy" ON public.asistencia_diaria_detalle FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "asistencia_diaria_detalle_insert_policy" ON public.asistencia_diaria_detalle;
CREATE POLICY "asistencia_diaria_detalle_insert_policy" ON public.asistencia_diaria_detalle FOR INSERT TO authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "asistencia_diaria_detalle_update_policy" ON public.asistencia_diaria_detalle;
CREATE POLICY "asistencia_diaria_detalle_update_policy" ON public.asistencia_diaria_detalle FOR UPDATE TO authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "asistencia_diaria_detalle_delete_policy" ON public.asistencia_diaria_detalle;
CREATE POLICY "asistencia_diaria_detalle_delete_policy" ON public.asistencia_diaria_detalle FOR DELETE TO authenticated USING (true);
