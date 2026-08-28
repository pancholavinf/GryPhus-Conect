-- =============================================================================
-- MIGRACIÓN 003: Habilitar Permisos RLS para Bucket 'accuratek-data' en Storage
-- Aplicar en: Supabase SQL Editor
-- Fecha: 2026-07-30
-- =============================================================================

-- 1. Crear el bucket 'accuratek-data' si no existe y asegurar que sea público
INSERT INTO storage.buckets (id, name, public)
VALUES ('accuratek-data', 'accuratek-data', true)
ON CONFLICT (id) DO UPDATE SET public = true;

-- 2. Habilitar RLS en la tabla storage.objects
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- 3. Limpiar políticas anteriores sobre accuratek-data para evitar conflictos
DROP POLICY IF EXISTS "accuratek_data_public_select" ON storage.objects;
DROP POLICY IF EXISTS "accuratek_data_authenticated_insert" ON storage.objects;
DROP POLICY IF EXISTS "accuratek_data_authenticated_update" ON storage.objects;
DROP POLICY IF EXISTS "accuratek_data_authenticated_delete" ON storage.objects;
DROP POLICY IF EXISTS "Allow public read access accuratek-data" ON storage.objects;
DROP POLICY IF EXISTS "Allow authenticated insert accuratek-data" ON storage.objects;
DROP POLICY IF EXISTS "Allow all for accuratek-data" ON storage.objects;

-- 4. Crear política universal para el bucket 'accuratek-data' (lectura, subida, edición y borrado)
CREATE POLICY "Allow all for accuratek-data"
ON storage.objects FOR ALL
TO public
USING (bucket_id = 'accuratek-data')
WITH CHECK (bucket_id = 'accuratek-data');

-- =============================================================================
-- FIN DE MIGRACIÓN 003
-- =============================================================================
