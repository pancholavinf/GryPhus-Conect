import os
import sys
import subprocess
import shutil

def run_build():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    spec_path = os.path.join(base_dir, "gerencia.spec")
    
    print("====================================================")
    print("  Iniciando Compilación de Trabs Gerencia (.EXE)")
    print("====================================================")
    print(f"Directorio base: {base_dir}")
    print(f"Archivo Spec:    {spec_path}")
    
    # Limpiar compilaciones anteriores si existen
    build_dir = os.path.join(base_dir, "build")
    dist_dir = os.path.join(base_dir, "dist")
    
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        f"--workpath={build_dir}",
        f"--distpath={dist_dir}",
        spec_path
    ]
    
    print("\nEjecutando PyInstaller...")
    res = subprocess.run(cmd, cwd=base_dir)
    
    if res.returncode == 0:
        exe_path = os.path.join(dist_dir, "TrabsGerencia", "TrabsGerencia.exe")
        print("\n====================================================")
        print("  ¡COMPILACIÓN EXITOSA!")
        print("====================================================")
        print(f"Ejecutable generado en:\n{exe_path}")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"Tamaño del archivo principal: {size_mb:.2f} MB")
    else:
        print("\n====================================================")
        print("  ERROR EN LA COMPILACIÓN")
        print("====================================================")
        sys.exit(res.returncode)

if __name__ == "__main__":
    run_build()
