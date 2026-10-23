import os
import sys
import time
import tempfile
import subprocess
import requests
from packaging import version
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication
from src.version import __version__, UPDATE_MANIFEST_URL

class CheckUpdateWorker(QThread):
    """
    Hilo asíncrono para verificar si existe una nueva versión en Supabase Storage
    sin bloquear la interfaz de usuario.
    """
    update_available = pyqtSignal(dict)  # Emite datos de la nueva versión si remote > local
    up_to_date = pyqtSignal(dict)        # Emite datos cuando la versión actual es la más reciente
    check_failed = pyqtSignal(str)       # Emite mensaje de error en caso de fallo de red/JSON

    def __init__(self, manifest_url: str = UPDATE_MANIFEST_URL, current_ver: str = __version__, parent=None):
        super().__init__(parent)
        self.manifest_url = manifest_url
        self.current_ver = current_ver

    def run(self):
        try:
            headers = {
                "User-Agent": "GryPhusConectGerencia-App/1.0",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Accept": "application/vnd.github.v3+json"
            }
            response = requests.get(self.manifest_url, headers=headers, timeout=6)
            
            if response.status_code != 200:
                self.check_failed.emit(f"HTTP {response.status_code}: No se pudo obtener el manifiesto de versión.")
                return

            data = response.json()
            
            # Si el endpoint devuelve una lista de releases (recomendado)
            target_release = None
            if isinstance(data, list):
                for rel in data:
                    tag = rel.get("tag_name", "").lower()
                    # Ignorar releases móviles
                    if tag.startswith("mobile-"):
                        continue
                    # Verificar si contiene instalador .exe
                    for asset in rel.get("assets", []):
                        if asset.get("name", "").lower().endswith(".exe"):
                            target_release = rel
                            break
                    if target_release:
                        break
            elif isinstance(data, dict):
                # Si se consultó un release individual (ej: /releases/latest)
                tag = data.get("tag_name", "").lower()
                if not tag.startswith("mobile-"):
                    for asset in data.get("assets", []):
                        if asset.get("name", "").lower().endswith(".exe"):
                            target_release = data
                            break

            if not target_release:
                self.up_to_date.emit({
                    "version": self.current_ver,
                    "local_version": self.current_ver,
                    "remote_version": self.current_ver,
                    "download_url": "",
                    "release_notes": ""
                })
                return

            tag_raw = target_release.get("tag_name", "")
            # Limpiar prefijos como 'desktop-v', 'desktop-', 'v', etc.
            import re
            remote_ver_str = re.sub(r'^[^\d]*', '', tag_raw).strip()
            release_notes = target_release.get("body", "Novedades y mejoras en esta versión.")
            
            # Buscar el instalador .exe entre los assets del Release
            download_url = ""
            for asset in target_release.get("assets", []):
                if asset.get("name", "").lower().endswith(".exe"):
                    download_url = asset.get("browser_download_url", "")
                    break
            
            update_info = {
                "version": remote_ver_str,
                "release_notes": release_notes,
                "release_date": target_release.get("published_at", "")[:10],
                "download_url": download_url,
                "local_version": self.current_ver,
                "remote_version": remote_ver_str,
            }

            if not remote_ver_str or not download_url:
                self.up_to_date.emit(update_info)
                return

            local_v = version.parse(self.current_ver)
            remote_v = version.parse(remote_ver_str)

            if remote_v > local_v:
                self.update_available.emit(update_info)
            else:
                self.up_to_date.emit(update_info)

        except requests.exceptions.RequestException as e:
            self.check_failed.emit(f"Error de conexión al servidor de actualizaciones: {str(e)}")
        except Exception as e:
            self.check_failed.emit(f"Error inesperado al comprobar actualizaciones: {str(e)}")


class DownloadUpdateWorker(QThread):
    """
    Hilo asíncrono para descargar en streaming el instalador (.exe)
    con reporte en tiempo real de porcentaje, bytes y velocidad (MB/s).
    """
    progress = pyqtSignal(int, int, float, float)  # (downloaded_bytes, total_bytes, percent, speed_mbps)
    finished = pyqtSignal(str)                     # (local_installer_path)
    error = pyqtSignal(str)                        # (error_message)

    def __init__(self, download_url: str, target_version: str, parent=None):
        super().__init__(parent)
        self.download_url = download_url
        self.target_version = target_version
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            temp_dir = tempfile.gettempdir()
            clean_ver = self.target_version.replace(".", "_")
            local_filename = f"GryPhusConectGerencia_Setup_v{clean_ver}.exe"
            local_path = os.path.join(temp_dir, local_filename)

            response = requests.get(self.download_url, stream=True, timeout=15)
            if response.status_code != 200:
                self.error.emit(f"HTTP {response.status_code}: Error al descargar el instalador.")
                return

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            chunk_size = 64 * 1024  # 64 KB

            start_time = time.time()
            last_speed_time = start_time
            bytes_since_last = 0
            current_speed = 0.0

            with open(local_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if self._is_cancelled:
                        f.close()
                        if os.path.exists(local_path):
                            try:
                                os.remove(local_path)
                            except Exception:
                                pass
                        self.error.emit("Descarga cancelada por el usuario.")
                        return

                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        bytes_since_last += len(chunk)

                        now = time.time()
                        time_delta = now - last_speed_time
                        if time_delta >= 0.5:
                            current_speed = (bytes_since_last / (1024 * 1024)) / time_delta
                            last_speed_time = now
                            bytes_since_last = 0

                        percent = (downloaded / total_size * 100.0) if total_size > 0 else 0.0
                        self.progress.emit(downloaded, total_size, percent, current_speed)

            # Verificar que el archivo se haya escrito correctamente
            if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
                self.progress.emit(downloaded, total_size, 100.0, current_speed)
                self.finished.emit(local_path)
            else:
                self.error.emit("El archivo descargado está vacío o no se pudo guardar.")

        except requests.exceptions.RequestException as e:
            self.error.emit(f"Error de red durante la descarga: {str(e)}")
        except Exception as e:
            self.error.emit(f"Error inesperado al descargar el instalador: {str(e)}")


def install_update_and_restart(installer_path: str, silent: bool = True) -> bool:
    """
    Ejecuta el instalador Inno Setup en segundo plano y cierra la instancia actual de la app.
    
    :param installer_path: Ruta del instalador .exe descargado
    :param silent: Si es True, ejecuta con /SILENT y /CLOSEAPPLICATIONS
    :return: True si se lanzó el proceso correctamente
    """
    if not os.path.exists(installer_path):
        return False

    try:
        # Argumentos para Inno Setup:
        # /SILENT: Muestra la barra de progreso de instalación sin asistentes de confirmación
        # /CLOSEAPPLICATIONS: Cierra automáticamente las instancias de la app que usan los binarios
        # /RESTARTAPPLICATIONS=0: No forzar reinicio por el gestor de reinicios de Windows
        if silent:
            cmd = [installer_path, "/SILENT", "/TASKS=desktopicon", "/CLOSEAPPLICATIONS", "/RESTARTAPPLICATIONS=0"]
        else:
            cmd = [installer_path]

        subprocess.Popen(cmd, shell=False)
        
        # Cerrar limpiamente la aplicación PyQt6
        app = QApplication.instance()
        if app:
            app.quit()
        else:
            sys.exit(0)
        return True
    except Exception as e:
        print(f"Error al ejecutar el instalador de actualización: {e}", file=sys.stderr)
        return False
