"""
Módulo de versión centralizado para Trabs Gerencia.
Define la versión actual de la aplicación y el endpoint de GitHub Releases para actualizaciones.
"""

__version__ = "1.0.6"
APP_NAME = "Trabs Gerencia"
APP_ORGANIZATION = "Accuratek"
APP_USER_MODEL_ID = f"Accuratek.TrabsGerencia.{__version__}"

GITHUB_OWNER = "pancholavinf"
GITHUB_REPO = "trabs-gerencia"

# Endpoint público de GitHub Releases API para comprobar las versiones disponibles
UPDATE_MANIFEST_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases"
