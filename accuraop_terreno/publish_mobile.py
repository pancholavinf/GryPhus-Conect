import os
import sys
import json
import re
import argparse
import subprocess
import requests
from dotenv import load_dotenv

GITHUB_OWNER = "pancholavinf"
GITHUB_REPO = "trabs-gerencia"

def update_json_file(file_path: str, new_version: str, is_app_json: bool = False):
    """Actualiza la versión en app.json o package.json"""
    if not os.path.exists(file_path):
        return
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if is_app_json:
        if "expo" in data:
            data["expo"]["version"] = new_version
        else:
            data["version"] = new_version
    else:
        data["version"] = new_version

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"[OK] {os.path.basename(file_path)} actualizado a versión {new_version}")

def upload_release_to_github(tag: str, release_title: str, release_notes: str, apk_path: str, token: str) -> bool:
    """Crea un Release en GitHub con prefijo mobile- y sube el archivo .apk"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "TrabsTerreno-Publisher/1.0"
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

    # 2. Subir el archivo APK (eliminando el anterior si ya existía en este release)
    filename = os.path.basename(apk_path)
    for existing_asset in release_data.get("assets", []):
        if existing_asset.get("name") == filename:
            asset_id = existing_asset.get("id")
            del_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/assets/{asset_id}"
            print(f"Reemplazando archivo anterior {filename} (ID: {asset_id})...")
            requests.delete(del_url, headers=headers)
            break

    clean_upload_url = upload_url_template.split("{")[0]
    upload_url = f"{clean_upload_url}?name={filename}"

    file_size = os.path.getsize(apk_path)
    print(f"Subiendo {filename} ({file_size/(1024*1024):.1f} MB) a GitHub Releases...")
    
    upload_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/vnd.android.package-archive",
        "Content-Length": str(file_size),
        "User-Agent": "TrabsTerreno-Publisher/1.0"
    }

    with open(apk_path, "rb") as f:
        up_resp = requests.post(upload_url, headers=upload_headers, data=f)

    if up_resp.status_code in (200, 201):
        asset_info = up_resp.json()
        download_url = asset_info.get("browser_download_url", "")
        print(f"[OK] ¡APK subido exitosamente a GitHub Releases!")
        print(f"URL de descarga pública: {download_url}")
        return True
    else:
        print(f"Error al subir asset a GitHub HTTP {up_resp.status_code}: {up_resp.text}")
        return False

def get_local_version(app_json_path: str) -> str:
    """Obtiene la versión actual configurada en app.json"""
    if os.path.exists(app_json_path):
        try:
            with open(app_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("expo", {}).get("version") or data.get("version", "1.0.0")
        except Exception:
            pass
    return "1.0.0"

def get_latest_github_mobile_version(token: str = None) -> str:
    """Consulta la última versión móvil publicada en GitHub Releases"""
    try:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "TrabsTerreno-Publisher/1.0"
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
                    if tag.startswith("mobile-v") or tag.startswith("mobile-"):
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
    return "1.0.1"

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
    parser = argparse.ArgumentParser(description="Automatiza la publicación de una nueva versión de Trabs Terreno (APK) en GitHub Releases.")
    parser.add_argument("--version", "-v", type=str, help="Nuevo número de versión móvil (ej: 1.0.1)")
    parser.add_argument("--notes", "-n", type=str, help="Notas de la versión o changelog")
    parser.add_argument("--apk", "-a", type=str, help="Ruta al archivo .apk a subir")
    parser.add_argument("--skip-build", action="store_true", help="Omitir compilación con EAS")
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

    app_json_path = os.path.join(base_dir, "app.json")
    local_ver = get_local_version(app_json_path)
    remote_ver = get_latest_github_mobile_version(gh_token)

    current_highest = semver_max(local_ver, remote_ver)
    suggested_ver = bump_patch_version(current_highest)

    new_ver = args.version
    if not new_ver:
        print("====================================================")
        print("  Detección Automática de Versión Móvil")
        print("====================================================")
        print(f"  • Versión actual en app.json: {local_ver}")
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
                else:
                    break
            except EOFError:
                break
        release_notes = "\n".join(lines) if lines else "Mejoras operativas, corrección de errores y optimización."

    print("\n====================================================")
    print(f"  Publicando Trabs Terreno Móvil v{new_ver}")
    print("====================================================")

    # 1. Actualizar archivos de versión
    app_json_path = os.path.join(base_dir, "app.json")
    pkg_json_path = os.path.join(base_dir, "package.json")
    update_json_file(app_json_path, new_ver, is_app_json=True)
    update_json_file(pkg_json_path, new_ver, is_app_json=False)

    # 2. Localizar o compilar APK
    apk_path = args.apk
    if not apk_path:
        # Buscar APK existente en dist / build si skip-build
        possible_apks = [
            os.path.join(base_dir, f"TrabsTerreno_v{new_ver}.apk"),
            os.path.join(base_dir, "dist", f"TrabsTerreno_v{new_ver}.apk"),
            os.path.join(base_dir, "dist", "app-release.apk"),
            os.path.join(base_dir, "dist", "application.apk")
        ]
        for p in possible_apks:
            if os.path.exists(p):
                apk_path = p
                break

    if not apk_path and not args.skip_build:
        print("\n--- 1/3. Compilación de APK ---")
        print("Para generar el APK de producción/preview:")
        print("Opción A (Recomendada con EAS Cloud): eas build -p android --profile preview")
        print("Opción B (Local con Android Studio): npx expo run:android --variant release")
        input_apk = input("\nIngresa la ruta absoluta o relativa al archivo .apk generado (o presiona Enter para cancelar): ").strip()
        if input_apk and os.path.exists(input_apk):
            apk_path = input_apk

    # 3. Commit y Push en Git
    print("\n--- 2/3. Sincronizando código con Git ---")
    try:
        subprocess.run(["git", "add", "."], cwd=root_dir)
        subprocess.run(["git", "commit", "-m", f"release(mobile): versión v{new_ver}"], cwd=root_dir)
        subprocess.run(["git", "push", "origin", "main"], cwd=root_dir)
        print("[OK] Cambios subidos a la rama principal en GitHub.")
    except Exception as e_git:
        print(f"Aviso en Git: {e_git}")

    # 4. Publicar en GitHub Releases
    print("\n--- 3/3. Publicando Release en GitHub ---")
    gh_token = args.token or os.getenv("GITHUB_TOKEN")

    if not gh_token:
        print("Aviso: No se encontró GITHUB_TOKEN en .env")
        gh_token = input("Ingresa tu GitHub Personal Access Token: ").strip()

    tag_name = f"mobile-v{new_ver}"
    release_title = f"Trabs Terreno v{new_ver}"

    if gh_token and apk_path and os.path.exists(apk_path):
        upload_release_to_github(tag_name, release_title, release_notes, apk_path, gh_token)
    else:
        print(f"\nTag asignado para el Release: {tag_name}")
        print(f"Enlace para subir manualmente el APK si lo requieres: https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/new?tag={tag_name}")

    print("\n====================================================")
    print(f"  ¡PROCESO DE VERSIÓN MÓVIL v{new_ver} COMPLETADO!")
    print("====================================================")

if __name__ == "__main__":
    main()
