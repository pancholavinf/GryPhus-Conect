"""
Módulo de versión centralizado para GryPhus Conect Gerencia.
Define la versión actual de la aplicación y el endpoint de GitHub Releases para actualizaciones.
"""

__version__ = "1.1.8"
APP_NAME = "GryPhus Conect Gerencia"
APP_ORGANIZATION = "Gryphus Systems"
APP_USER_MODEL_ID = f"GryphusSystems.GryPhusConectGerencia.{__version__}"

GITHUB_OWNER = "pancholavinf"
GITHUB_REPO = "GryPhus-Conect"

# Endpoint público de GitHub Releases API para comprobar las versiones disponibles
UPDATE_MANIFEST_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases"
