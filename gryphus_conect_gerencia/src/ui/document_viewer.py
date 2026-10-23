import os
import tempfile
import urllib.request
import shutil

try:
    import fitz # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False
    fitz = None

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QWidget, QMessageBox, QFileDialog, QFrame, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QPixmap, QImage


import requests

class FetchDocumentWorker(QThread):
    finished = pyqtSignal(str, bytes) # temp_path, file_bytes
    error = pyqtSignal(str)

    def __init__(self, url_or_path: str):
        super().__init__()
        self.url_or_path = url_or_path

    def run(self):
        try:
            temp_dir = tempfile.gettempdir()
            
            if self.url_or_path.startswith("http://") or self.url_or_path.startswith("https://"):
                resp = requests.get(
                    self.url_or_path,
                    headers={'User-Agent': 'Mozilla/5.0'},
                    timeout=15
                )
                resp.raise_for_status()
                file_bytes = resp.content
                
                # Intentar determinar la extensión
                ext = ".pdf"
                if ".png" in self.url_or_path.lower(): ext = ".png"
                elif ".jpg" in self.url_or_path.lower() or ".jpeg" in self.url_or_path.lower(): ext = ".jpg"

                temp_path = os.path.join(temp_dir, f"view_doc_{os.urandom(4).hex()}{ext}")
                with open(temp_path, "wb") as f:
                    f.write(file_bytes)
            else:
                if not os.path.exists(self.url_or_path):
                    self.error.emit("El archivo local no fue encontrado.")
                    return
                temp_path = self.url_or_path
                with open(self.url_or_path, "rb") as f:
                    file_bytes = f.read()

            self.finished.emit(temp_path, file_bytes)
        except Exception as e:
            self.error.emit(f"Error al descargar/leer documento: {str(e)}")


class DocumentViewerDialog(QDialog):
    def __init__(self, parent=None, url_or_path: str = "", title: str = "Visor de Documentos"):
        super().__init__(parent)
        self.url_or_path = url_or_path
        self.doc_title = title
        self.temp_filepath = None
        self.file_bytes = None

        self.setWindowTitle(f"Visor: {title}")
        self.resize(980, 750)
        self.setMinimumSize(700, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #1F2421;
                color: #FAF8F5;
            }
            QLabel {
                color: #FAF8F5;
            }
            QScrollArea {
                background-color: #262B29;
                border: 1px solid #334155;
                border-radius: 8px;
            }
        """)

        self.setup_ui()
        self.iniciar_descarga()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # Header Superior con título y botones de acción
        header_frame = QFrame()
        header_frame.setStyleSheet("QFrame { background-color: #262B29; border-radius: 8px; padding: 6px 12px; }")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 8, 10, 8)

        self.lbl_title = QLabel(self.doc_title)
        self.lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        header_layout.addWidget(self.lbl_title, stretch=1)

        self.btn_download = QPushButton("Descargar Copia")
        self.btn_download.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_download.setEnabled(False)
        self.btn_download.setStyleSheet("""
            QPushButton {
                background-color: #3D523C; color: white; border-radius: 6px;
                padding: 6px 14px; font-weight: bold; border: none;
            }
            QPushButton:hover { background-color: #2F402E; }
            QPushButton:disabled { background-color: #262B29; color: #94A3B8; }
        """)
        self.btn_download.clicked.connect(self.descargar_copia)
        header_layout.addWidget(self.btn_download)

        self.btn_open_external = QPushButton("Abrir en Sistema")
        self.btn_open_external.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_external.setEnabled(False)
        self.btn_open_external.setStyleSheet("""
            QPushButton {
                background-color: #3D523C; color: white; border-radius: 6px;
                padding: 6px 14px; font-weight: bold; border: none;
            }
            QPushButton:hover { background-color: #2F402E; }
            QPushButton:disabled { background-color: #262B29; color: #94A3B8; }
        """)
        self.btn_open_external.clicked.connect(self.abrir_en_sistema)
        header_layout.addWidget(self.btn_open_external)

        btn_close = QPushButton("Cerrar")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #262B29; color: white; border-radius: 6px;
                padding: 6px 12px; font-weight: bold; border: none;
            }
            QPushButton:hover { background-color: #262B29; }
        """)
        btn_close.clicked.connect(self.accept)
        header_layout.addWidget(btn_close)

        main_layout.addWidget(header_frame)

        # Barra de estado/carga
        self.lbl_status = QLabel("Cargando documento...")
        self.lbl_status.setStyleSheet("color: #38BDF8; font-weight: bold; font-size: 13px;")
        main_layout.addWidget(self.lbl_status)

        # Área de Scroll Principal
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background-color: #1F2421;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(20)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)

    def iniciar_descarga(self):
        if not self.url_or_path:
            self.lbl_status.setText("No se proporcionó enlace o ruta de archivo.")
            return

        self.fetch_worker = FetchDocumentWorker(self.url_or_path)
        self.fetch_worker.finished.connect(self.on_documento_cargado)
        self.fetch_worker.error.connect(self.on_error_carga)
        self.fetch_worker.start()

    def on_documento_cargado(self, temp_path, file_bytes):
        self.temp_filepath = temp_path
        self.file_bytes = file_bytes
        self.btn_download.setEnabled(True)
        self.btn_open_external.setEnabled(True)

        is_pdf = temp_path.lower().endswith(".pdf") or file_bytes.startswith(b"%PDF")
        if is_pdf:
            self.renderizar_pdf(temp_path)
        else:
            self.renderizar_imagen(file_bytes)

    def on_error_carga(self, err_msg):
        self.lbl_status.setText(f"{err_msg}")
        QMessageBox.critical(self, "Error al Cargar Documento", err_msg)

    def renderizar_pdf(self, pdf_path):
        if HAS_FITZ and fitz is not None:
            try:
                doc = fitz.open(pdf_path)
                total_pages = len(doc)
                self.lbl_status.setText(f"Documento PDF listo ({total_pages} página(s))")

                for page_num in range(total_pages):
                    page = doc.load_page(page_num)
                    # Renderizar a 140 DPI para excelente resolución visual
                    pix = page.get_pixmap(dpi=140)
                    img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
                    pixmap = QPixmap.fromImage(img)

                    lbl_page = QLabel()
                    lbl_page.setPixmap(pixmap)
                    lbl_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    lbl_page.setStyleSheet("border: 1px solid #334155; border-radius: 4px; background-color: #FFFFFF; color: #1F2421;")

                    # Etiqueta de número de página al pie
                    lbl_num = QLabel(f"Página {page_num + 1} de {total_pages}")
                    lbl_num.setStyleSheet("color: #94A3B8; font-size: 11px; margin-bottom: 10px;")
                    lbl_num.setAlignment(Qt.AlignmentFlag.AlignCenter)

                    self.content_layout.addWidget(lbl_page)
                    self.content_layout.addWidget(lbl_num)

                doc.close()
                return
            except Exception as e:
                print(f"Advertencia al renderizar con PyMuPDF: {e}")

        # Fallback elegante si PyMuPDF no está instalado o falló el renderizado
        self.lbl_status.setText("Documento PDF cargado y listo")
        
        info_frame = QFrame()
        info_frame.setStyleSheet("QFrame { background-color: #262B29; border: 1px solid #334155; border-radius: 8px; padding: 25px; }")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_icon = QLabel("")
        lbl_icon.setStyleSheet("font-size: 48px;")
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_msg = QLabel(f"Documento: {self.doc_title}\n\nPresiona 'Abrir en Sistema' o 'Descargar Copia' para visualizar.")
        lbl_msg.setStyleSheet("font-size: 14px; font-weight: bold; color: #FAF8F5; text-align: center;")
        lbl_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)

        info_layout.addWidget(lbl_icon)
        info_layout.addWidget(lbl_msg)
        self.content_layout.addWidget(info_frame)

    def renderizar_imagen(self, image_bytes):
        pixmap = QPixmap()
        if pixmap.loadFromData(image_bytes):
            self.lbl_status.setText("️ Imagen cargada exitosamente")
            lbl_img = QLabel()
            # Escalar si es gigante pero mantener alta definición
            if pixmap.width() > 900:
                scaled_pixmap = pixmap.scaledToWidth(900, Qt.TransformationMode.SmoothTransformation)
                lbl_img.setPixmap(scaled_pixmap)
            else:
                lbl_img.setPixmap(pixmap)

            lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_img.setStyleSheet("border: 1px solid #334155; border-radius: 6px; background-color: #FFFFFF; color: #1F2421;")
            self.content_layout.addWidget(lbl_img)
        else:
            self.lbl_status.setText("Formato de imagen no reconocido.")

    def descargar_copia(self):
        if not self.file_bytes or not self.temp_filepath: return
        ext = os.path.splitext(self.temp_filepath)[1] or ".pdf"
        default_name = f"{self.doc_title}{ext}".replace(" ", "_")

        save_path, _ = QFileDialog.getSaveFileName(self, "Guardar Copia de Documento", default_name, f"Archivos (*{ext})")
        if save_path:
            try:
                with open(save_path, "wb") as f:
                    f.write(self.file_bytes)
                QMessageBox.information(self, "Descarga Exitosa", f"Archivo guardado correctamente en:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error al Guardar", f"No se pudo guardar el archivo:\n{str(e)}")

    def abrir_en_sistema(self):
        if self.temp_filepath and os.path.exists(self.temp_filepath):
            try:
                os.startfile(self.temp_filepath)
            except Exception as e:
                QMessageBox.critical(self, "Error al Abrir en Sistema", f"No se pudo abrir el archivo:\n{str(e)}")
