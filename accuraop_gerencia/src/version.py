"""
Módulo de versión centralizado para Trabs Gerencia.
Define la versión actual de la aplicación y el endpoint del manifiesto de actualizaciones.
"""

__version__ = "1.0.1"
APP_NAME = "Trabs Gerencia"
APP_ORGANIZATION = "Accuratek"
APP_USER_MODEL_ID = f"Accuratek.TrabsGerencia.{__version__}"

# Endpoint público en Supabase Storage para el manifiesto de versiones
UPDATE_MANIFEST_URL = "https://xkifhzhqgroemzudzxrf.supabase.co/storage/v1/object/public/app-updates/version.json"
