-- =============================================================================
-- MIGRACIÓN 004: Tabla de Estados de Pago (EDP) — Accurateck
-- Aplicar en: Supabase SQL Editor
-- Fecha: 2026-08-03
-- Descripción:
--   1. Crear tabla estados_pago
--   2. Agregar columna estado_pago_id a avances (si no existe)
--   3. RLS Policies para estados_pago
--   4. Índices de performance
--   5. Vista v_edp_resumen para reportes
--   6. Función auxiliar para folio correlativo seguro (sin race conditions)
-- =============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. TABLA PRINCIPAL DE ESTADOS DE PAGO
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.estados_pago (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    obra_id              UUID NOT NULL REFERENCES public.obras(id) ON DELETE CASCADE,
    numero_estado_pago   INTEGER NOT NULL,
    fecha_emision        TIMESTAMPTZ NOT NULL DEFAULT now(),
    periodo_desde        DATE,
    periodo_hasta        DATE,

    -- Montos calculados al momento de emisión
    subtotal_pesos       NUMERIC(18, 2) NOT NULL DEFAULT 0,
    monto_retencion      NUMERIC(18, 2) NOT NULL DEFAULT 0,
    monto_anticipo       NUMERIC(18, 2) NOT NULL DEFAULT 0,
    monto_neto           NUMERIC(18, 2) NOT NULL DEFAULT 0,
    monto_iva            NUMERIC(18, 2) NOT NULL DEFAULT 0,
    monto_total          NUMERIC(18, 2) NOT NULL DEFAULT 0,

    -- Metadatos del documento
    orden_trabajo_num    VARCHAR(100),
    archivo_pdf_url      TEXT,
    creado_por           UUID REFERENCES public.perfiles_usuario(id) ON DELETE SET NULL,
    observaciones        TEXT,

    -- Restricción: folio único por obra
    CONSTRAINT uq_estados_pago_folio UNIQUE (obra_id, numero_estado_pago)
);

ALTER TABLE public.estados_pago ALTER COLUMN id SET DEFAULT gen_random_uuid();

COMMENT ON TABLE  public.estados_pago                     IS 'Tabla maestra de Estados de Pago emitidos por obra. Cada fila congela un período de cobro.';
COMMENT ON COLUMN public.estados_pago.numero_estado_pago  IS 'Folio correlativo dentro de la obra (1, 2, 3...). Único por obra.';
COMMENT ON COLUMN public.estados_pago.subtotal_pesos      IS 'Suma bruta de monto_presente de todos los avances incluidos.';
COMMENT ON COLUMN public.estados_pago.monto_retencion     IS 'Porcentaje de retención de contrato descontado del subtotal.';
COMMENT ON COLUMN public.estados_pago.monto_anticipo      IS 'Monto fijo descontado por amortización de anticipo.';
COMMENT ON COLUMN public.estados_pago.monto_neto          IS 'subtotal - retencion - anticipo.';
COMMENT ON COLUMN public.estados_pago.monto_iva           IS 'IVA (19%) sobre el monto_neto.';
COMMENT ON COLUMN public.estados_pago.monto_total         IS 'Monto total a cobrar (monto_neto + monto_iva).';
COMMENT ON COLUMN public.estados_pago.archivo_pdf_url     IS 'URL pública o ruta local del PDF institucional del EDP.';
COMMENT ON COLUMN public.estados_pago.creado_por          IS 'FK al administrador que emitió el EDP.';

-- Índices
CREATE INDEX IF NOT EXISTS idx_estados_pago_obra_id
    ON public.estados_pago(obra_id);

CREATE INDEX IF NOT EXISTS idx_estados_pago_fecha_emision
    ON public.estados_pago(fecha_emision DESC);

CREATE INDEX IF NOT EXISTS idx_estados_pago_numero
    ON public.estados_pago(obra_id, numero_estado_pago);


-- ─────────────────────────────────────────────────────────────────────────────
-- 2. AGREGAR COLUMNA estado_pago_id A TABLA avances
-- (Solo si no existe — idempotente)
-- ─────────────────────────────────────────────────────────────────────────────
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name   = 'avances'
          AND column_name  = 'estado_pago_id'
    ) THEN
        ALTER TABLE public.avances
            ADD COLUMN estado_pago_id UUID
                REFERENCES public.estados_pago(id)
                ON DELETE SET NULL;

        COMMENT ON COLUMN public.avances.estado_pago_id IS
            'Vincula este avance al Estado de Pago que lo cobró. NULL = pendiente de cobro.';
    END IF;
END
$$;

-- Índices para consultas rápidas del EDP Controller
CREATE INDEX IF NOT EXISTS idx_avances_estado_pago_id
    ON public.avances(estado_pago_id);

CREATE INDEX IF NOT EXISTS idx_avances_pendientes_cobro
    ON public.avances(estado_revision, estado_pago_id)
    WHERE estado_revision = 'aprobado' AND estado_pago_id IS NULL;

-- Índice compuesto para filtrar avances por obra a través de item_obra_id
CREATE INDEX IF NOT EXISTS idx_avances_item_obra_id
    ON public.avances(item_obra_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- 3. FUNCIÓN AUXILIAR: Folio correlativo seguro con bloqueo de fila
-- Evita race conditions cuando dos admins emiten simultáneamente.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.get_next_edp_number(p_obra_id UUID)
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_next INTEGER;
BEGIN
    -- Bloqueo a nivel de tabla para serializar la asignación del folio
    LOCK TABLE public.estados_pago IN SHARE ROW EXCLUSIVE MODE;

    SELECT COALESCE(MAX(numero_estado_pago), 0) + 1
    INTO v_next
    FROM public.estados_pago
    WHERE obra_id = p_obra_id;

    RETURN v_next;
END;
$$;

COMMENT ON FUNCTION public.get_next_edp_number(UUID) IS
    'Retorna el siguiente folio correlativo de EDP para una obra. Usa bloqueo de tabla para evitar duplicados bajo concurrencia.';


-- ─────────────────────────────────────────────────────────────────────────────
-- 4. SEGURIDAD — RLS PARA estados_pago
-- ─────────────────────────────────────────────────────────────────────────────
ALTER TABLE public.estados_pago ENABLE ROW LEVEL SECURITY;

-- Administrador: acceso total (INSERT, SELECT, UPDATE, DELETE)
CREATE POLICY "edp_admin_all"
    ON public.estados_pago FOR ALL
    TO authenticated
    USING (es_administrador())
    WITH CHECK (es_administrador());

-- Jefe de Obra: solo puede leer EDPs de sus obras asignadas
CREATE POLICY "edp_jefe_select"
    ON public.estados_pago FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.obras_jefes_obra
            WHERE obra_id      = estados_pago.obra_id
              AND jefe_obra_id = auth.uid()
        )
    );


-- ─────────────────────────────────────────────────────────────────────────────
-- 5. VISTA AUXILIAR: Resumen de EDPs con datos de obra
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW public.v_edp_resumen AS
SELECT
    ep.id,
    ep.obra_id,
    o.nombre                             AS obra_nombre,
    ep.numero_estado_pago,
    ep.fecha_emision,
    ep.periodo_desde,
    ep.periodo_hasta,
    ep.subtotal_pesos,
    ep.monto_retencion,
    ep.monto_anticipo,
    ep.monto_neto,
    ep.monto_iva,
    ep.monto_total,
    ep.orden_trabajo_num,
    ep.archivo_pdf_url,
    ep.creado_por,
    p.nombre                             AS creado_por_nombre,
    COUNT(av.id)                         AS cant_avances_incluidos
FROM public.estados_pago ep
JOIN public.obras o
    ON o.id = ep.obra_id
LEFT JOIN public.perfiles_usuario p
    ON p.id = ep.creado_por
LEFT JOIN public.avances av
    ON av.estado_pago_id = ep.id
GROUP BY
    ep.id, ep.obra_id, o.nombre, ep.numero_estado_pago,
    ep.fecha_emision, ep.periodo_desde, ep.periodo_hasta,
    ep.subtotal_pesos, ep.monto_retencion, ep.monto_anticipo,
    ep.monto_neto, ep.monto_iva, ep.monto_total,
    ep.orden_trabajo_num, ep.archivo_pdf_url, ep.creado_por,
    p.nombre;

COMMENT ON VIEW public.v_edp_resumen IS
    'Vista desnormalizada para consultas del historial de EDPs con nombre de obra, emisor y cantidad de avances incluidos.';


-- ─────────────────────────────────────────────────────────────────────────────
-- 6. BUCKET DE STORAGE (Ejecutar en SQL Editor de Supabase)
-- ─────────────────────────────────────────────────────────────────────────────
-- Crear el bucket para PDFs de Estados de Pago:
INSERT INTO storage.buckets (id, name, public)
VALUES ('estados_pago', 'estados_pago', true)
ON CONFLICT (id) DO UPDATE SET public = true;

-- Policy de Storage para el administrador (subir/leer PDFs):
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'storage'
          AND tablename  = 'objects'
          AND policyname = 'admin_edp_storage_all'
    ) THEN
        EXECUTE $policy$
            CREATE POLICY "admin_edp_storage_all"
            ON storage.objects FOR ALL
            TO authenticated
            USING (
                bucket_id = 'estados_pago'
                AND (SELECT es_administrador())
            )
            WITH CHECK (
                bucket_id = 'estados_pago'
                AND (SELECT es_administrador())
            )
        $policy$;
    END IF;
END
$$;

-- Policy de Storage para lectura pública del bucket:
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'storage'
          AND tablename  = 'objects'
          AND policyname = 'edp_storage_public_select'
    ) THEN
        EXECUTE $policy$
            CREATE POLICY "edp_storage_public_select"
            ON storage.objects FOR SELECT
            TO public
            USING (bucket_id = 'estados_pago')
        $policy$;
    END IF;
END
$$;


-- =============================================================================
-- VERIFICACIÓN FINAL
-- =============================================================================
-- Ejecutar estos SELECTs para confirmar que todo se creó correctamente:
--
-- SELECT table_name FROM information_schema.tables
-- WHERE table_schema='public' AND table_name='estados_pago';
--
-- SELECT column_name FROM information_schema.columns
-- WHERE table_schema='public' AND table_name='avances'
-- AND column_name='estado_pago_id';
--
-- SELECT * FROM public.v_edp_resumen LIMIT 0;
-- SELECT public.get_next_edp_number('00000000-0000-0000-0000-000000000000'::uuid);
--
-- =============================================================================
-- FIN DE MIGRACIÓN 004
-- =============================================================================
