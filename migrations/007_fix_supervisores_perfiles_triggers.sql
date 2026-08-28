-- Migration 007: Normalización de roles, saneamiento de perfiles y trigger automático para auth.users
-- Fecha: 2026-08-28
-- Autor: Accuratek

-- 1. Limpiar caracteres especiales (\r, \n, espacios) y normalizar campos en perfiles_usuario
UPDATE public.perfiles_usuario 
SET 
  rol = TRIM(REPLACE(REPLACE(rol, E'\r', ''), E'\n', '')),
  nombre = TRIM(REPLACE(REPLACE(nombre, E'\r', ''), E'\n', '')),
  telefono = NULLIF(TRIM(REPLACE(REPLACE(COALESCE(telefono, ''), E'\r', ''), E'\n', '')), ''),
  rut_dni = NULLIF(TRIM(REPLACE(REPLACE(COALESCE(rut_dni, ''), E'\r', ''), E'\n', '')), '');

-- 2. Normalizar nombres de roles a minúsculas estándar ('jefe_obra', 'administrador')
UPDATE public.perfiles_usuario
SET rol = CASE 
  WHEN LOWER(rol) IN ('administrador', 'admin', 'gerente') THEN 'administrador'
  ELSE 'jefe_obra'
END;

-- 3. Sincronizar emails faltantes desde auth.users
UPDATE public.perfiles_usuario p
SET email = u.email
FROM auth.users u
WHERE p.id = u.id AND (p.email IS NULL OR p.email = '');

-- 4. Eliminar perfiles sin cuenta de autenticación correspondiente
DELETE FROM public.perfiles_usuario
WHERE id NOT IN (SELECT id FROM auth.users);

-- 5. Crear función y trigger automático para nuevos usuarios en auth.users
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.perfiles_usuario (id, email, nombre, rol, telefono, foto_perfil_url, rut_dni)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'nombre', NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1)),
    CASE 
      WHEN LOWER(COALESCE(NEW.raw_user_meta_data->>'rol', '')) IN ('administrador', 'admin', 'gerente') THEN 'administrador'
      ELSE 'jefe_obra'
    END,
    COALESCE(NEW.raw_user_meta_data->>'telefono', ''),
    COALESCE(NEW.raw_user_meta_data->>'foto_perfil_url', ''),
    COALESCE(NEW.raw_user_meta_data->>'rut_dni', NULL)
  )
  ON CONFLICT (id) DO UPDATE SET
    email = EXCLUDED.email,
    nombre = COALESCE(NULLIF(EXCLUDED.nombre, ''), perfiles_usuario.nombre),
    rol = COALESCE(NULLIF(EXCLUDED.rol, ''), perfiles_usuario.rol),
    telefono = COALESCE(NULLIF(EXCLUDED.telefono, ''), perfiles_usuario.telefono),
    foto_perfil_url = COALESCE(NULLIF(EXCLUDED.foto_perfil_url, ''), perfiles_usuario.foto_perfil_url),
    rut_dni = COALESCE(NULLIF(EXCLUDED.rut_dni, ''), perfiles_usuario.rut_dni);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 6. Robustecer función es_administrador()
CREATE OR REPLACE FUNCTION public.es_administrador()
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM public.perfiles_usuario
    WHERE id = auth.uid() AND TRIM(LOWER(rol)) IN ('administrador', 'admin')
  );
END;
$$;
