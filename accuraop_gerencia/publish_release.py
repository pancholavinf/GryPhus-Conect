import os
import sys
import json
import re
import datetime
import argparse
import subprocess
from dotenv import load_dotenv
from supabase import create_client

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
    """Intenta compilar el instalador con Inno Setup si ISCC.exe está en PATH o rutas comunes"""
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
        print(f"Compilando instalador Inno Setup usando {iscc_bin}...")
        res = subprocess.run([iscc_bin, iss_file], cwd=os.path.dirname(iss_file))
        return res.returncode == 0
    else:
        print("Aviso: ISCC.exe (Inno Setup) no detectado en PATH. Puedes compilar manualmente haciendo clic derecho en TrabsGerencia_Setup.iss -> Compile.")
        return False

def main():
    parser = argparse.ArgumentParser(description="Automatiza la publicación y despliegue de una nueva versión de Trabs Gerencia.")
    parser.add_argument("--version", "-v", type=str, help="Nuevo número de versión (ej: 1.0.1)")
    parser.add_argument("--notes", "-n", type=str, help="Notas de la versión o changelog")
    parser.add_argument("--mandatory", action="store_true", help="Marcar actualización como obligatoria")
    parser.add_argument("--skip-build", action="store_true", help="Omitir recompilación de PyInstaller")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(base_dir)

    # Cargar .env
    for p in [os.path.join(base_dir, ".env"), os.path.join(root_dir, ".env")]:
        if os.path.exists(p):
            load_dotenv(p)
            break

    new_ver = args.version
    if not new_ver:
        new_ver = input("Ingresa el nuevo número de versión (ej: 1.0.1): ").strip()
    
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
    print(f"  Publicando Trabs Gerencia v{new_ver}")
    print("====================================================")

    # 1. Actualizar archivos de versión
    version_py = os.path.join(base_dir, "src", "version.py")
    iss_file = os.path.join(base_dir, "TrabsGerencia_Setup.iss")
    update_version_py(version_py, new_ver)
    update_iss_script(iss_file, new_ver)

    # 2. Recompilar PyInstaller
    if not args.skip_build:
        print("\n--- Ejecutando compilación con PyInstaller ---")
        build_script = os.path.join(base_dir, "build_exe.py")
        res = subprocess.run([sys.executable, build_script], cwd=base_dir)
        if res.returncode != 0:
            print("Error en la compilación de PyInstaller. Cancelando publicación.")
            sys.exit(res.returncode)

    # 3. Compilar instalador Inno Setup
    print("\n--- Generando instalador con Inno Setup ---")
    compile_inno_setup(iss_file)

    # 4. Generar version.json
    installer_filename = f"TrabsGerencia_Setup_v{new_ver}.exe"
    download_url = f"https://xkifhzhqgroemzudzxrf.supabase.co/storage/v1/object/public/app-updates/{installer_filename}"
    
    manifest = {
        "version": new_ver,
        "release_date": datetime.date.today().isoformat(),
        "mandatory": bool(args.mandatory),
        "min_supported_version": "1.0.0",
        "release_notes": release_notes,
        "download_url": download_url
    }

    manifest_path = os.path.join(base_dir, "version.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"[OK] Manifiesto generado en {manifest_path}")

    # 5. Subida a Supabase Storage
    supabase_url = os.getenv("SUPABASE_URL", "https://xkifhzhqgroemzudzxrf.supabase.co")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if supabase_url and supabase_key:
        try:
            print("\nConectando a Supabase para subir versión...")
            client = create_client(supabase_url, supabase_key)
            
            # Subir version.json
            with open(manifest_path, "rb") as mf:
                client.storage.from_("app-updates").upload(
                    "version.json",
                    mf.read(),
                    file_options={"upsert": "true", "content-type": "application/json"}
                )
            print("[OK] version.json subido exitosamente a Supabase Storage (bucket: app-updates)")

            # Subir instalador si existe localmente
            installer_path = os.path.join(base_dir, "dist_installer", installer_filename)
            if os.path.exists(installer_path):
                file_size_mb = os.path.getsize(installer_path) / (1024 * 1024)
                print(f"Subiendo {installer_filename} ({file_size_mb:.1f} MB)...")
                
                try:
                    # Intento directo estándar
                    with open(installer_path, "rb") as inst_file:
                        client.storage.from_("app-updates").upload(
                            installer_filename,
                            inst_file.read(),
                            file_options={"upsert": "true", "content-type": "application/octet-stream"}
                        )
                    print(f"[OK] {installer_filename} subido exitosamente a Supabase Storage.")
                except Exception as e_direct:
                    print(f"Subida directa requirió protocolo TUS resumible ({e_direct}). Iniciando subida por bloques...")
                    import base64
                    import requests
                    
                    file_size = os.path.getsize(installer_path)
                    b64_bucket = base64.b64encode(b"app-updates").decode()
                    b64_object = base64.b64encode(installer_filename.encode()).decode()
                    b64_type = base64.b64encode(b"application/octet-stream").decode()

                    headers = {
                        "apikey": supabase_key,
                        "Authorization": f"Bearer {supabase_key}",
                        "Upload-Length": str(file_size),
                        "Tus-Resumable": "1.0.0",
                        "Upload-Metadata": f"bucketName {b64_bucket},objectName {b64_object},contentType {b64_type}",
                        "x-upsert": "true"
                    }

                    tus_endpoint = f"{supabase_url}/storage/v1/upload/resumable"
                    resp = requests.post(tus_endpoint, headers=headers)
                    if resp.status_code not in (201, 200):
                        raise Exception(f"TUS Init falló HTTP {resp.status_code}: {resp.text}")

                    upload_url = resp.headers.get("Location")
                    if not upload_url:
                        raise Exception("TUS Init no retornó cabecera Location")

                    if upload_url.startswith("/"):
                        upload_url = f"{supabase_url}{upload_url}"

                    chunk_size = 5 * 1024 * 1024
                    offset = 0
                    with open(installer_path, "rb") as f_in:
                        while offset < file_size:
                            chunk = f_in.read(chunk_size)
                            patch_headers = {
                                "apikey": supabase_key,
                                "Authorization": f"Bearer {supabase_key}",
                                "Upload-Offset": str(offset),
                                "Content-Type": "application/offset+octet-stream",
                                "Tus-Resumable": "1.0.0"
                            }
                            patch_resp = requests.patch(upload_url, data=chunk, headers=patch_headers)
                            if patch_resp.status_code not in (204, 200):
                                raise Exception(f"TUS Patch falló en offset {offset} HTTP {patch_resp.status_code}: {patch_resp.text}")
                            offset += len(chunk)
                            print(f"Progreso subida: {offset/(1024*1024):.1f} / {file_size/(1024*1024):.1f} MB ({(offset/file_size)*100:.1f}%)")

                    print(f"[OK] {installer_filename} subido exitosamente vía protocolo TUS.")
            else:
                print(f"Nota: Si no se generó {installer_filename} automáticamente, compila TrabsGerencia_Setup.iss en Inno Setup y súbelo al bucket 'app-updates'.")

        except Exception as e_sup:
            print(f"Error al subir a Supabase: {e_sup}")
    else:
        print("Aviso: SUPABASE_KEY no encontrada en entorno para subida automática.")

    print("\n====================================================")
    print(f"  ¡PUBLICACIÓN DE VERSIÓN {new_ver} FINALIZADA!")
    print("====================================================")

if __name__ == "__main__":
    main()
