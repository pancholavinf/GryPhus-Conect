import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QProgressBar, QTextBrowser, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QColor, QFont
from src.core.updater import DownloadUpdateWorker, install_update_and_restart

class UpdateDialog(QDialog):
    """
    Diálogo modal moderno para notificar al usuario sobre una nueva versión,
    mostrar notas de la versión y gestionar la descarga/instalación interactiva.
    """
    def __init__(self, update_data: dict, parent=None):
        super().__init__(parent)
        self.update_data = update_data
        self.download_worker = None
        self.downloaded_installer_path = None
        
        self.local_version = update_data.get("local_version", "1.0.0")
        self.remote_version = update_data.get("remote_version", "1.0.1")
        self.release_notes = update_data.get("release_notes", "Mejoras de rendimiento y corrección de errores.")
        self.download_url = update_data.get("download_url", "")
        self.mandatory = update_data.get("mandatory", False)
        self.release_date = update_data.get("release_date", "")

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"Actualización Disponible — GryPhus Conect Gerencia v{self.remote_version}")
        self.setFixedSize(540, 520)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # ── 1. Cabecera con Logo y Versiones ────────────────────────────
        header_layout = QHBoxLayout()
        header_layout.setSpacing(14)

        logo_label = QLabel()
        local_assets = Path(__file__).resolve().parents[2] / "assets"
        icon_candidates = [
            local_assets / "logo_gryphus_circular_cf.png",
            local_assets / "logo_gryphus_circular_sf.png",
            local_assets / "logo_gryphus_solo_sf.png",
            local_assets / "logo_gryphus_circular_cf.png"
        ]
        logo_path = next((str(p) for p in icon_candidates if p.exists()), None)
        if logo_path:
            pix = QPixmap(logo_path).scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pix)
        header_layout.addWidget(logo_label)

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(4)
        
        title_label = QLabel("¡Nueva Versión Disponible!")
        title_label.setStyleSheet("font-family: 'Space Grotesk', 'Work Sans', sans-serif; font-size: 17px; font-weight: 800; color: #1F2421;")
        title_vbox.addWidget(title_label)

        version_badge = QLabel(f"Versión actual: <b>v{self.local_version}</b>  ➔  Nueva: <span style='color:#3D523C; font-weight:bold;'>v{self.remote_version}</span>")
        version_badge.setStyleSheet("font-family: 'Inter', sans-serif; font-size: 13px; color: #4A524E;")
        title_vbox.addWidget(version_badge)

        if self.release_date:
            date_lbl = QLabel(f"Fecha de lanzamiento: {self.release_date}")
            date_lbl.setStyleSheet("font-size: 11px; color: #4A524E;")
            title_vbox.addWidget(date_lbl)

        header_layout.addLayout(title_vbox)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Separador sutil
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #D8D5CD; max-height: 1px;")
        layout.addWidget(sep)

        # ── 2. Notas de la Versión (Release Notes) ──────────────────────
        notes_title = QLabel("Novedades y Mejoras:")
        notes_title.setStyleSheet("font-family: 'Space Grotesk', sans-serif; font-size: 13px; font-weight: 700; color: #262B29;")
        layout.addWidget(notes_title)

        self.notes_browser = QTextBrowser()
        self.notes_browser.setFixedHeight(150)
        self.notes_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #F2EFE9;
                border: 1px solid #D8D5CD;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                color: #1F2421;
                line-height: 1.4;
            }
        """)
        
        # Formatear el texto a HTML con viñetas limpias si viene como texto plano
        formatted_notes = self.release_notes.replace("\n", "<br>")
        self.notes_browser.setHtml(f"<div style='line-height: 1.4;'>{formatted_notes}</div>")
        layout.addWidget(self.notes_browser)

        # ── 3. Barra de Progreso y Estado de Descarga ────────────────────
        self.progress_container = QFrame()
        self.progress_container.setStyleSheet("background: transparent;")
        prog_vbox = QVBoxLayout(self.progress_container)
        prog_vbox.setContentsMargins(0, 0, 0, 0)
        prog_vbox.setSpacing(6)

        self.status_label = QLabel("Listo para actualizar a la última versión.")
        self.status_label.setStyleSheet("font-family: 'Inter', sans-serif; font-size: 12px; color: #4A524E;")
        prog_vbox.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #D8D5CD;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #3D523C;
                border-radius: 4px;
            }
        """)
        self.progress_bar.hide()
        prog_vbox.addWidget(self.progress_bar)

        self.speed_label = QLabel("")
        self.speed_label.setStyleSheet("font-family: 'Inter', sans-serif; font-size: 11px; color: #4A524E;")
        self.speed_label.hide()
        prog_vbox.addWidget(self.speed_label)

        layout.addWidget(self.progress_container)

        # ── 4. Botonera de Acción ───────────────────────────────────────
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        self.btn_later = QPushButton("Recordar más tarde")
        self.btn_later.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_later.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #4A524E;
                border-radius: 6px;
                padding: 10px 18px;
                font-family: 'Inter', sans-serif;
                font-size: 13px;
                font-weight: 600;
                color: #4A524E;
            }
            QPushButton:hover {
                background-color: #F2EFE9;
                color: #1F2421;
            }
        """)
        self.btn_later.clicked.connect(self.reject)
        
        if self.mandatory:
            self.btn_later.hide()

        button_layout.addWidget(self.btn_later)
        button_layout.addStretch()

        self.btn_update = QPushButton("🚀 Actualizar Ahora")
        self.btn_update.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_update.setStyleSheet("""
            QPushButton {
                background-color: #3D523C;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-family: 'Space Grotesk', 'Inter', sans-serif;
                font-size: 13px;
                font-weight: 700;
                color: #F2EFE9;
            }
            QPushButton:hover {
                background-color: #2F402E;
            }
            QPushButton:disabled {
                background-color: #D8D5CD;
                color: #4A524E;
            }
        """)
        self.btn_update.clicked.connect(self.start_download)
        button_layout.addWidget(self.btn_update)

        self.btn_cancel_download = QPushButton("Cancelar")
        self.btn_cancel_download.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel_download.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #EF4444;
                border-radius: 6px;
                padding: 10px 18px;
                font-family: 'Inter', sans-serif;
                font-size: 13px;
                font-weight: 600;
                color: #EF4444;
            }
            QPushButton:hover {
                background-color: #FEF2F2;
            }
        """)
        self.btn_cancel_download.hide()
        self.btn_cancel_download.clicked.connect(self.cancel_download)
        button_layout.addWidget(self.btn_cancel_download)

        layout.addLayout(button_layout)

    def start_download(self):
        if not self.download_url:
            self.status_label.setText("<span style='color:#EF4444;'>Error: No hay URL de descarga disponible.</span>")
            return

        self.btn_update.hide()
        self.btn_later.hide()
        self.btn_cancel_download.show()
        self.progress_bar.show()
        self.speed_label.show()
        self.progress_bar.setValue(0)
        self.status_label.setText("Iniciando descarga del instalador...")

        self.download_worker = DownloadUpdateWorker(self.download_url, self.remote_version, parent=self)
        self.download_worker.progress.connect(self.on_download_progress)
        self.download_worker.finished.connect(self.on_download_finished)
        self.download_worker.error.connect(self.on_download_error)
        self.download_worker.start()

    def on_download_progress(self, downloaded: int, total: int, percent: float, speed_mbps: float):
        self.progress_bar.setValue(int(percent))
        dl_mb = downloaded / (1024 * 1024)
        tot_mb = total / (1024 * 1024) if total > 0 else 0
        
        if total > 0:
            self.status_label.setText(f"Descargando actualización: <b>{dl_mb:.1f} MB</b> de <b>{tot_mb:.1f} MB</b> ({percent:.0f}%)")
        else:
            self.status_label.setText(f"Descargando actualización: <b>{dl_mb:.1f} MB</b>...")

        if speed_mbps > 0:
            self.speed_label.setText(f"Velocidad: {speed_mbps:.2f} MB/s")

    def on_download_finished(self, local_path: str):
        self.downloaded_installer_path = local_path
        self.progress_bar.setValue(100)
        self.status_label.setText("<span style='color:#10B981; font-weight:bold;'>✓ Descarga completada. Ejecutando instalador...</span>")
        self.speed_label.setText("La aplicación se cerrará para completar la actualización.")
        self.btn_cancel_download.hide()

        # Lanzar la instalación silenciosa e inmediata
        install_update_and_restart(local_path, silent=True)

    def on_download_error(self, err_msg: str):
        self.progress_bar.hide()
        self.speed_label.hide()
        self.status_label.setText(f"<span style='color:#EF4444; font-weight:600;'>Error: {err_msg}</span>")
        self.btn_cancel_download.hide()
        self.btn_update.setText("Reintentar Descarga")
        self.btn_update.show()
        if not self.mandatory:
            self.btn_later.show()

    def cancel_download(self):
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.cancel()
        self.on_download_error("Descarga cancelada.")
