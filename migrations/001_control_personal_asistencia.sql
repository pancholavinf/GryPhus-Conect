-- =============================================================================
-- MIGRACIÓN 001: Control de Personal y Asistencia Diaria — Accurateck
-- Aplicar en: Supabase SQL Editor
-- Fecha: 2026-07-29
-- =============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. TABLA MAESTRA DE TIPOS/CARGOS DE MAESTRO
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.tipos_maestro (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre          VARCHAR(100) NOT NULL UNIQUE,
    sueldo_diario   NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    fecha_creacion  TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE  public.tipos_maestro                IS 'Catálogo de cargos/posiciones de maestros y sus tarifas diarias';
COMMENT ON COLUMN public.tipos_maestro.nombre         IS 'Nombre único del cargo (ej: Aplicador, Pintor, Ayudante, Mallero)';
COMMENT ON COLUMN public.tipos_maestro.sueldo_diario  IS 'Tarifa de pago por jornada completa (1.0)';

-- Datos iniciales del catálogo de cargos
INSERT INTO public.tipos_maestro (nombre, sueldo_diario) VALUES
    ('Aplicador', 0.00),
    ('Pintor',    0.00),
    ('Ayudante',  0.00),
    ('Mallero',   0.00)
ON CONFLICT (nombre) DO NOTHING;


-- ─────────────────────────────────────────────────────────────────────────────
-- 2. TABLA DE PERFILES DE MAESTROS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.maestros (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre            VARCHAR(200) NOT NULL,
    rut_dni           VARCHAR(50),
    tipo_maestro_id   UUID NOT NULL REFERENCES public.tipos_maestro(id) ON DELETE RESTRICT,
    telefono          VARCHAR(30),
    foto_perfil_url   TEXT,
    estado            VARCHAR(20) NOT NULL DEFAULT 'Activo' CHECK (estado IN ('Activo', 'Inactivo')),
    fecha_creacion    TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE  public.maestros                 IS 'Perfiles únicos de maestros/trabajadores de la empresa';
COMMENT ON COLUMN public.maestros.tipo_maestro_id IS 'FK al cargo asignado al maestro (define su sueldo diario)';
COMMENT ON COLUMN public.maestros.estado          IS 'Estado laboral activo/inactivo del maestro';

CREATE INDEX IF NOT EXISTS idx_maestros_tipo_maestro_id ON public.maestros(tipo_maestro_id);
CREATE INDEX IF NOT EXISTS idx_maestros_estado           ON public.maestros(estado);


-- ─────────────────────────────────────────────────────────────────────────────
-- 3. TABLA DE ASIGNACIÓN DE MAESTROS A OBRAS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.obras_maestros (
    obra_id           UUID NOT NULL REFERENCES public.obras(id) ON DELETE CASCADE,
    maestro_id        UUID NOT NULL REFERENCES public.maestros(id) ON DELETE CASCADE,
    fecha_asignacion  TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (obra_id, maestro_id)
);

COMMENT ON TABLE public.obras_maestros IS 'Asignación de maestros a obras. Un maestro puede estar en múltiples obras.';

CREATE INDEX IF NOT EXISTS idx_obras_maestros_obra_id    ON public.obras_maestros(obra_id);
CREATE INDEX IF NOT EXISTS idx_obras_maestros_maestro_id ON public.obras_maestros(maestro_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- 4. TABLA DE CABECERA DE ASISTENCIA DIARIA
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.asistencia_diaria (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    obra_id          UUID NOT NULL REFERENCES public.obras(id) ON DELETE CASCADE,
    jefe_obra_id     UUID NOT NULL REFERENCES public.perfiles_usuario(id),
    fecha            DATE NOT NULL,
    foto_url         TEXT,
    es_correctivo    BOOLEAN NOT NULL DEFAULT FALSE,
    observaciones    TEXT,
    fecha_registro   TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE  public.asistencia_diaria                IS 'Cabecera de la toma de asistencia diaria de una obra';
COMMENT ON COLUMN public.asistencia_diaria.fecha          IS 'Fecha de la jornada laboral (no la fecha de captura)';
COMMENT ON COLUMN public.asistencia_diaria.foto_url       IS 'Evidencia fotográfica de la asistencia en terreno';
COMMENT ON COLUMN public.asistencia_diaria.es_correctivo  IS 'TRUE si es un reporte correctivo enviado después del normal del día';
COMMENT ON COLUMN public.asistencia_diaria.fecha_registro IS 'Momento exacto de captura/sincronización desde el dispositivo';

CREATE INDEX IF NOT EXISTS idx_asistencia_diaria_obra_id      ON public.asistencia_diaria(obra_id);
CREATE INDEX IF NOT EXISTS idx_asistencia_diaria_fecha        ON public.asistencia_diaria(fecha);
CREATE INDEX IF NOT EXISTS idx_asistencia_diaria_jefe_obra_id ON public.asistencia_diaria(jefe_obra_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- 5. TABLA DE DETALLE INDIVIDUAL DE ASISTENCIA POR MAESTRO
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.asistencia_diaria_detalle (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asistencia_id  UUID NOT NULL REFERENCES public.asistencia_diaria(id) ON DELETE CASCADE,
    maestro_id     UUID NOT NULL REFERENCES public.maestros(id) ON DELETE CASCADE,
    estado         VARCHAR(20) NOT NULL CHECK (estado IN ('presente', 'medio_dia', 'ausente')),
    valor_jornada  NUMERIC(3, 1) NOT NULL CHECK (valor_jornada IN (1.0, 0.5, 0.0)),
    observacion    TEXT,
    UNIQUE (asistencia_id, maestro_id)
);

COMMENT ON TABLE  public.asistencia_diaria_detalle               IS 'Detalle de asistencia individual por maestro';
COMMENT ON COLUMN public.asistencia_diaria_detalle.estado        IS 'presente=Día completo, medio_dia=Media jornada, ausente=No asistió';
COMMENT ON COLUMN public.asistencia_diaria_detalle.valor_jornada IS '1.0=Día completo, 0.5=Medio día, 0.0=Ausente';

CREATE INDEX IF NOT EXISTS idx_asist_detalle_asistencia_id ON public.asistencia_diaria_detalle(asistencia_id);
CREATE INDEX IF NOT EXISTS idx_asist_detalle_maestro_id    ON public.asistencia_diaria_detalle(maestro_id);


-- =============================================================================
-- POLÍTICAS DE SEGURIDAD A NIVEL DE FILA (RLS)
-- =============================================================================

-- Habilitar RLS en todas las tablas nuevas
ALTER TABLE public.tipos_maestro           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.maestros                ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.obras_maestros          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.asistencia_diaria       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.asistencia_diaria_detalle ENABLE ROW LEVEL SECURITY;

-- ──────────────────────────────────────
-- Políticas: tipos_maestro
-- ──────────────────────────────────────
-- Administrador: acceso total
CREATE POLICY "tipos_maestro_admin_all"
    ON public.tipos_maestro FOR ALL
    TO authenticated
    USING (es_administrador())
    WITH CHECK (es_administrador());

-- Jefe de Obra: solo lectura (necesita ver cargos para reportar asistencia)
CREATE POLICY "tipos_maestro_jefe_select"
    ON public.tipos_maestro FOR SELECT
    TO authenticated
    USING (auth.uid() IS NOT NULL);

-- ──────────────────────────────────────
-- Políticas: maestros
-- ──────────────────────────────────────
CREATE POLICY "maestros_admin_all"
    ON public.maestros FOR ALL
    TO authenticated
    USING (es_administrador())
    WITH CHECK (es_administrador());

-- Jefe de Obra: solo puede ver maestros asignados a sus obras
CREATE POLICY "maestros_jefe_select"
    ON public.maestros FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.obras_maestros om
            JOIN public.obras_jefes_obra ojo ON ojo.obra_id = om.obra_id
            WHERE om.maestro_id = maestros.id
              AND ojo.jefe_obra_id = auth.uid()
        )
    );

-- ──────────────────────────────────────
-- Políticas: obras_maestros
-- ──────────────────────────────────────
CREATE POLICY "obras_maestros_admin_all"
    ON public.obras_maestros FOR ALL
    TO authenticated
    USING (es_administrador())
    WITH CHECK (es_administrador());

CREATE POLICY "obras_maestros_jefe_select"
    ON public.obras_maestros FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.obras_jefes_obra
            WHERE obra_id = obras_maestros.obra_id
              AND jefe_obra_id = auth.uid()
        )
    );

-- ──────────────────────────────────────
-- Políticas: asistencia_diaria
-- ──────────────────────────────────────
CREATE POLICY "asistencia_diaria_admin_all"
    ON public.asistencia_diaria FOR ALL
    TO authenticated
    USING (es_administrador())
    WITH CHECK (es_administrador());

-- Jefe de Obra: puede leer y crear asistencia de sus obras
CREATE POLICY "asistencia_diaria_jefe_select"
    ON public.asistencia_diaria FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.obras_jefes_obra
            WHERE obra_id = asistencia_diaria.obra_id
              AND jefe_obra_id = auth.uid()
        )
    );

CREATE POLICY "asistencia_diaria_jefe_insert"
    ON public.asistencia_diaria FOR INSERT
    TO authenticated
    WITH CHECK (
        jefe_obra_id = auth.uid()
        AND EXISTS (
            SELECT 1 FROM public.obras_jefes_obra
            WHERE obra_id = asistencia_diaria.obra_id
              AND jefe_obra_id = auth.uid()
        )
    );

-- ──────────────────────────────────────
-- Políticas: asistencia_diaria_detalle
-- ──────────────────────────────────────
CREATE POLICY "asistencia_detalle_admin_all"
    ON public.asistencia_diaria_detalle FOR ALL
    TO authenticated
    USING (es_administrador())
    WITH CHECK (es_administrador());

CREATE POLICY "asistencia_detalle_jefe_select"
    ON public.asistencia_diaria_detalle FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.asistencia_diaria ad
            JOIN public.obras_jefes_obra ojo ON ojo.obra_id = ad.obra_id
            WHERE ad.id = asistencia_diaria_detalle.asistencia_id
              AND ojo.jefe_obra_id = auth.uid()
        )
    );

CREATE POLICY "asistencia_detalle_jefe_insert"
    ON public.asistencia_diaria_detalle FOR INSERT
    TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.asistencia_diaria ad
            WHERE ad.id = asistencia_diaria_detalle.asistencia_id
              AND ad.jefe_obra_id = auth.uid()
        )
    );


-- =============================================================================
-- VISTA AUXILIAR PARA REPORTES (opcional, facilita consultas del escritorio)
-- =============================================================================
CREATE OR REPLACE VIEW public.v_asistencia_resumen AS
SELECT
    add.asistencia_id,
    ad.obra_id,
    o.nombre                                   AS obra_nombre,
    ad.fecha,
    ad.es_correctivo,
    m.id                                       AS maestro_id,
    m.nombre                                   AS maestro_nombre,
    m.rut_dni,
    tm.nombre                                  AS tipo_nombre,
    tm.sueldo_diario,
    add.estado,
    add.valor_jornada,
    (add.valor_jornada * tm.sueldo_diario)     AS pago_jornada
FROM public.asistencia_diaria_detalle add
JOIN public.asistencia_diaria         ad  ON ad.id  = add.asistencia_id
JOIN public.obras                     o   ON o.id   = ad.obra_id
JOIN public.maestros                  m   ON m.id   = add.maestro_id
JOIN public.tipos_maestro             tm  ON tm.id  = m.tipo_maestro_id;

COMMENT ON VIEW public.v_asistencia_resumen IS 'Vista desnormalizada para facilitar reportes de asistencia por obra y fecha';

-- =============================================================================
-- FIN DE MIGRACIÓN
-- =============================================================================
