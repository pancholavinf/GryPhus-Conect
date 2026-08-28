-- =============================================================================
-- MIGRACIÓN 006: Unificación Total de Almacenamiento en Bucket 'accuratek-data'
-- Aplicar en: Supabase SQL Editor
-- Fecha: Agosto 2026
-- =============================================================================

-- 1. Asegurar que el bucket 'accuratek-data' exista y sea público
INSERT INTO storage.buckets (id, name, public)
VALUES ('accuratek-data', 'accuratek-data', true)
ON CONFLICT (id) DO UPDATE SET public = true;

-- 2. Habilitar RLS en storage.objects
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- 3. Limpiar políticas previas redundantes sobre accuratek-data
DROP POLICY IF EXISTS "accuratek_data_select" ON storage.objects;
DROP POLICY IF EXISTS "accuratek_data_insert" ON storage.objects;
DROP POLICY IF EXISTS "accuratek_data_update" ON storage.objects;
DROP POLICY IF EXISTS "accuratek_data_delete" ON storage.objects;
DROP POLICY IF EXISTS "Allow all for accuratek-data" ON storage.objects;

-- 4. Crear política universal para lectura, inserción, actualización y borrado en 'accuratek-data'
CREATE POLICY "accuratek_data_select"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'accuratek-data');

CREATE POLICY "accuratek_data_insert"
ON storage.objects FOR INSERT
TO public
WITH CHECK (bucket_id = 'accuratek-data');

CREATE POLICY "accuratek_data_update"
ON storage.objects FOR UPDATE
TO public
USING (bucket_id = 'accuratek-data')
WITH CHECK (bucket_id = 'accuratek-data');

CREATE POLICY "accuratek_data_delete"
ON storage.objects FOR DELETE
TO public
USING (bucket_id = 'accuratek-data');

-- =============================================================================
-- FIN DE MIGRACIÓN 006
-- =============================================================================
