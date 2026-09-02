import os
import sys
import json
import re
import datetime
import argparse
import subprocess
import requests
from dotenv import load_dotenv

GITHUB_OWNER = "pancholavinf"
GITHUB_REPO = "trabs-gerencia"

def update_version_py(version_file: str, new_version: str):
    """Actualiza la constante __version__ en src/version.py"""
    with open(version_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    updated_content = re.sub(
        r'__version__\s*=\s*["\'][^"\']+["\']',
        f'__version__ = "{new_version}"',
        content
    )
    with open(version_file, "w", encoding="utf-8") as f:
        f.write(updated_content)
    print(f"[OK] src/version.py actualizado con versión {new_version}")

def update_iss_script(iss_file: str, new_version: str):
    """Actualiza #define MyAppVersion en TrabsGerencia_Setup.iss"""
    if not os.path.exists(iss_file):
        return
    with open(iss_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    updated_content = re.sub(
        r'#define\s+MyAppVersion\s+["\'][^"\']+["\']',
        f'#define MyAppVersion "{new_version}"',
        content
    )
    with open(iss_file, "w", encoding="utf-8") as f:
        f.write(updated_content)
    print(f"[OK] TrabsGerencia_Setup.iss actualizado con versión {new_version}")

def compile_inno_setup(iss_file: str) -> bool:
    """Compila el instalador con Inno Setup"""
    possible_iscc = [
        "iscc",
        r"C:\Program Files (x86)\Inno Setup 6\iscc.exe",
        r"C:\Program Files\Inno Setup 6\iscc.exe",
    ]
    iscc_bin = None
    for p in possible_iscc:
        try:
            res = subprocess.run([p, "/?"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if res.returncode in (0, 1):
                iscc_bin = p
                break
        except Exception:
            continue

    if iscc_bin:
        print(f"Compilando instalador Inno Setup...")
        res = subprocess.run([iscc_bin, iss_file], cwd=os.path.dirname(iss_file))
        return res.returncode == 0
    else:
        print("Aviso: ISCC.exe no detectado en PATH.")
        return False

def upload_release_to_github(tag: str, release_title: str, release_notes: str, installer_path: str, token: str) -> bool:
    """Crea un Release en GitHub y sube el archivo instalador .exe usando la API REST"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "TrabsGerencia-Publisher/1.0"
    }

    # 1. Crear el Release en GitHub
    release_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases"
    payload = {
        "tag_name": tag,
        "name": release_title,
        "body": release_notes,
        "draft": False,
        "prerelease": False
    }
    
    print(f"Creando Release {tag} en GitHub ({GITHUB_OWNER}/{GITHUB_REPO})...")
    resp = requests.post(release_url, headers=headers, json=payload)
    
    if resp.status_code == 422 and "already_exists" in resp.text:
        print(f"Aviso: El release/tag {tag} ya existía. Obteniendo información...")
        get_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/tags/{tag}"
        resp = requests.get(get_url, headers=headers)

    if resp.status_code not in (200, 201):
        print(f"Error al crear Release en GitHub HTTP {resp.status_code}: {resp.text}")
        return False

    release_data = resp.json()
    upload_url_template = release_data.get("upload_url", "")
    if not upload_url_template:
        print("Error: No se obtuvo URL de subida de assets desde GitHub.")
        return False

    # 2. Subir el archivo instalador .exe (eliminando el anterior si ya existía en este release)
    filename = os.path.basename(installer_path)
    for existing_asset in release_data.get("assets", []):
        if existing_asset.get("name") == filename:
            asset_id = existing_asset.get("id")
            del_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/assets/{asset_id}"
            print(f"Reemplazando archivo anterior {filename} (ID: {asset_id})...")
            requests.delete(del_url, headers=headers)
            break

    clean_upload_url = upload_url_template.split("{")[0]
    upload_url = f"{clean_upload_url}?name={filename}"

    file_size = os.path.getsize(installer_path)
    print(f"Subiendo {filename} ({file_size/(1024*1024):.1f} MB) a GitHub Releases...")
    
    upload_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/octet-stream",
        "Content-Length": str(file_size),
        "User-Agent": "TrabsGerencia-Publisher/1.0"
    }

    with open(installer_path, "rb") as f:
        up_resp = requests.post(upload_url, headers=upload_headers, data=f)

    if up_resp.status_code in (200, 201):
        asset_info = up_resp.json()
        download_url = asset_info.get("browser_download_url", "")
        print(f"[OK] ¡Instalador subido exitosamente a GitHub Releases!")
        print(f"URL de descarga pública: {download_url}")
        return True
    else:
        print(f"Error al subir asset a GitHub HTTP {up_resp.status_code}: {up_resp.text}")
        return False

def get_local_desktop_version(version_py_path: str) -> str:
    """Obtiene la versión actual desde version.py"""
    if os.path.exists(version_py_path):
        try:
            with open(version_py_path, "r", encoding="utf-8") as f:
                content = f.read()
                m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
                if m:
                    return m.group(1)
        except Exception:
            pass
    return "1.0.6"

def get_latest_github_desktop_version(token: str = None) -> str:
    """Consulta la última versión de escritorio en GitHub Releases"""
    try:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "TrabsGerencia-Publisher/1.0"
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases"
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            releases = resp.json()
            if isinstance(releases, list):
                for r in releases:
                    tag = (r.get("tag_name") or "").lower()
                    if not tag.startswith("mobile-"):
                        ver = re.sub(r'^[^\d]*', '', tag).strip()
                        if ver:
                            return ver
    except Exception:
        pass
    return None

def bump_patch_version(ver_str: str) -> str:
    """Incrementa el patch de una versión semántica X.Y.Z -> X.Y.(Z+1)"""
    clean_ver = re.sub(r'^[^\d]*', '', ver_str).strip()
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)$', clean_ver)
    if match:
        major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
        return f"{major}.{minor}.{patch + 1}"
    return "1.0.7"

def semver_max(v1: str, v2: str) -> str:
    """Retorna la versión semántica mayor entre dos cadenas"""
    if not v1: return v2
    if not v2: return v1
    try:
        p1 = [int(x) for x in re.sub(r'^[^\d]*', '', v1).split('.')]
        p2 = [int(x) for x in re.sub(r'^[^\d]*', '', v2).split('.')]
        return v1 if p1 >= p2 else v2
    except Exception:
        return v1 or v2

def main():
    parser = argparse.ArgumentParser(description="Automatiza la publicación completa de una nueva versión en GitHub Releases.")
    parser.add_argument("--version", "-v", type=str, help="Nuevo número de versión (ej: 1.0.3)")
    parser.add_argument("--notes", "-n", type=str, help="Notas de la versión o changelog")
    parser.add_argument("--skip-build", action="store_true", help="Omitir recompilación de PyInstaller")
    parser.add_argument("--token", "-t", type=str, help="GitHub Personal Access Token")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(base_dir)

    # Cargar .env
    for p in [os.path.join(base_dir, ".env"), os.path.join(root_dir, ".env")]:
        if os.path.exists(p):
            load_dotenv(p)
            break

    gh_token = args.token or os.getenv("GITHUB_TOKEN")

    version_py = os.path.join(base_dir, "src", "version.py")
    local_ver = get_local_desktop_version(version_py)
    remote_ver = get_latest_github_desktop_version(gh_token)

    current_highest = semver_max(local_ver, remote_ver)
    suggested_ver = bump_patch_version(current_highest)

    new_ver = args.version
    if not new_ver:
        print("====================================================")
        print("  Detección Automática de Versión de Escritorio")
        print("====================================================")
        print(f"  • Versión actual local:       {local_ver}")
        if remote_ver:
            print(f"  • Última versión en GitHub:   {remote_ver}")
        print(f"  👉 Siguiente versión sugerida: {suggested_ver}")
        print("----------------------------------------------------")
        
        user_input = input(f"Presiona [Enter] para usar '{suggested_ver}' o escribe una versión personalizada: ").strip()
        new_ver = user_input if user_input else suggested_ver
    
    if not re.match(r'^\d+\.\d+\.\d+$', new_ver):
        print(f"Error: La versión '{new_ver}' no cumple con el formato semántico X.Y.Z")
        sys.exit(1)

    release_notes = args.notes
    if not release_notes:
        print("\nIngresa las notas de la versión (deja una línea en blanco para terminar):")
        lines = []
        while True:
            try:
                line = input()
                if not line and lines:
                    break
                if line:
                    lines.append(line)
            except EOFError:
                break
        release_notes = "\n".join(lines) if lines else "Mejoras de rendimiento y corrección de errores."

    print("\n====================================================")
    print(f"  Publicando Automáticamente Trabs Gerencia v{new_ver}")
    print("====================================================")

    # 1. Actualizar archivos de versión
    version_py = os.path.join(base_dir, "src", "version.py")
    iss_file = os.path.join(base_dir, "TrabsGerencia_Setup.iss")
    update_version_py(version_py, new_ver)
    update_iss_script(iss_file, new_ver)

    # 2. Recompilar PyInstaller
    if not args.skip_build:
        print("\n--- 1/4. Ejecutando compilación con PyInstaller ---")
        build_script = os.path.join(base_dir, "build_exe.py")
        res = subprocess.run([sys.executable, build_script], cwd=base_dir)
        if res.returncode != 0:
            print("Error en la compilación de PyInstaller. Cancelando publicación.")
            sys.exit(res.returncode)

    # 3. Compilar instalador Inno Setup
    print("\n--- 2/4. Generando instalador con Inno Setup ---")
    compile_inno_setup(iss_file)

    installer_filename = f"TrabsGerencia_Setup_v{new_ver}.exe"
    installer_path = os.path.join(base_dir, "dist_installer", installer_filename)

    # 4. Commit y Push en Git
    print("\n--- 3/4. Sincronizando código con Git ---")
    try:
        subprocess.run(["git", "add", "."], cwd=root_dir)
        subprocess.run(["git", "commit", "-m", f"release: versión v{new_ver}"], cwd=root_dir)
        subprocess.run(["git", "push", "origin", "main"], cwd=root_dir)
        print("[OK] Cambios subidos a la rama principal en GitHub.")
    except Exception as e_git:
        print(f"Aviso en Git: {e_git}")

    # 5. Publicar en GitHub Releases
    print("\n--- 4/4. Publicando Release en GitHub ---")
    gh_token = args.token or os.getenv("GITHUB_TOKEN")

    if not gh_token:
        print("\nPara publicar automáticamente el instalador en GitHub sin abrir el navegador:")
        print("1. Crea un Token en: https://github.com/settings/tokens (Permiso: repo)")
        print("2. Agrega en tu archivo .env la línea: GITHUB_TOKEN=ghp_tu_token_aqui")
        gh_token = input("\nIngresa tu GitHub Personal Access Token (o presiona Enter para omitir): ").strip()

    if gh_token and os.path.exists(installer_path):
        tag_name = f"v{new_ver}"
        release_title = f"Trabs Gerencia v{new_ver}"
        upload_release_to_github(tag_name, release_title, release_notes, installer_path, gh_token)
    else:
        print(f"\nPuedes subir manualmente el archivo generado a GitHub Releases:")
        print(f"👉 {installer_path}")
        print(f"Enlace: https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/new")

    print("\n====================================================")
    print(f"  ¡PROCESO DE VERSIÓN v{new_ver} COMPLETADO!")
    print("====================================================")

if __name__ == "__main__":
    main()
