import unittest
import os
import sys
import tempfile
import json
from unittest.mock import patch, MagicMock

# Añadir ruta del módulo accuraop_gerencia
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "accuraop_gerencia")))

from src.version import __version__, APP_NAME, UPDATE_MANIFEST_URL
from src.core.updater import CheckUpdateWorker, DownloadUpdateWorker, install_update_and_restart
from publish_release import update_version_py, update_iss_script

class TestUpdaterModule(unittest.TestCase):
    
    def test_01_version_constants(self):
        """Valida que las constantes de versión existan y tengan el formato correcto."""
        self.assertTrue(bool(__version__))
        self.assertRegex(__version__, r'^\d+\.\d+\.\d+$')
        self.assertEqual(APP_NAME, "Trabs Gerencia")
        self.assertTrue(UPDATE_MANIFEST_URL.startswith("https://"))

    @patch("requests.get")
    def test_02_check_update_available(self, mock_get):
        """Valida que CheckUpdateWorker detecte correctamente cuando existe una versión superior."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "version": "1.0.1",
            "release_notes": "Mejoras en EDP y reportes",
            "download_url": "https://example.com/setup.exe"
        }
        mock_get.return_value = mock_response

        worker = CheckUpdateWorker(current_ver="1.0.0")
        available_data = []
        worker.update_available.connect(lambda d: available_data.append(d))
        worker.run()

        self.assertEqual(len(available_data), 1)
        self.assertEqual(available_data[0]["remote_version"], "1.0.1")
        self.assertEqual(available_data[0]["local_version"], "1.0.0")

    @patch("requests.get")
    def test_03_check_up_to_date(self, mock_get):
        """Valida que CheckUpdateWorker emita up_to_date cuando la versión remota es igual o menor."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "version": "1.0.0",
            "release_notes": "Versión actual",
            "download_url": "https://example.com/setup.exe"
        }
        mock_get.return_value = mock_response

        worker = CheckUpdateWorker(current_ver="1.0.0")
        uptodate_data = []
        worker.up_to_date.connect(lambda d: uptodate_data.append(d))
        worker.run()

        self.assertEqual(len(uptodate_data), 1)
        self.assertEqual(uptodate_data[0]["remote_version"], "1.0.0")

    @patch("requests.get")
    def test_04_check_failed_network_error(self, mock_get):
        """Valida que CheckUpdateWorker capture errores de red y emita check_failed."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        worker = CheckUpdateWorker()
        errors = []
        worker.check_failed.connect(lambda e: errors.append(e))
        worker.run()

        self.assertEqual(len(errors), 1)
        self.assertIn("HTTP 500", errors[0])

    @patch("requests.get")
    def test_05_download_update_worker_stream(self, mock_get):
        """Valida que DownloadUpdateWorker descargue el archivo por bloques emitiendo progreso."""
        fake_content = [b"chunk1_" * 1024, b"chunk2_" * 1024, b"chunk3_" * 1024]
        total_len = sum(len(c) for c in fake_content)
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-length": str(total_len)}
        mock_response.iter_content.return_value = fake_content
        mock_get.return_value = mock_response

        worker = DownloadUpdateWorker(download_url="https://example.com/setup.exe", target_version="1.0.1")
        progress_events = []
        finished_events = []
        
        worker.progress.connect(lambda d, t, p, s: progress_events.append((d, t, p)))
        worker.finished.connect(lambda p: finished_events.append(p))
        worker.run()

        self.assertTrue(len(progress_events) > 0)
        self.assertEqual(len(finished_events), 1)
        self.assertTrue(os.path.exists(finished_events[0]))
        
        # Limpieza de archivo temporal
        try:
            os.remove(finished_events[0])
        except Exception:
            pass

    def test_06_update_scripts_helpers(self):
        """Valida que update_version_py y update_iss_script reemplacen adecuadamente las versiones."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_ver_py = os.path.join(tmp_dir, "version.py")
            with open(temp_ver_py, "w", encoding="utf-8") as f:
                f.write('__version__ = "1.0.0"\nAPP_NAME = "Test"')
            
            update_version_py(temp_ver_py, "1.0.5")
            with open(temp_ver_py, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn('__version__ = "1.0.5"', content)

            temp_iss = os.path.join(tmp_dir, "test.iss")
            with open(temp_iss, "w", encoding="utf-8") as f:
                f.write('#define MyAppVersion "1.0.0"\n#define MyAppName "Test"')
            
            update_iss_script(temp_iss, "1.0.5")
            with open(temp_iss, "r", encoding="utf-8") as f:
                iss_content = f.read()
            self.assertIn('#define MyAppVersion "1.0.5"', iss_content)

if __name__ == "__main__":
    unittest.main()
