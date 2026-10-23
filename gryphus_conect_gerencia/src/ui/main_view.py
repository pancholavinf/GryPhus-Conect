from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFrame, QPushButton, QStackedWidget, QLabel, QGraphicsDropShadowEffect, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QColor
import os
from pathlib import Path
from src.ui.dashboard_view import DashboardContent
from src.ui.ingesta_view import IngestaContent
from src.ui.control_personal_view import ControlPersonalContent
from src.ui.materiales_view import MaterialesContent
from src.ui.avances_window import AvancesContent
from src.ui.reportes_asistencia_view import ReportesAsistenciaContent

from src.core.data_manager import DataManager
from src.version import __version__
from src.core.updater import CheckUpdateWorker
from src.ui.update_dialog import UpdateDialog

class MainView(QWidget):
    logout_requested = pyqtSignal()

    def __init__(self, supabase_client=None):
        super().__init__()
        self.setAutoFillBackground(True)
        self.supabase_client = supabase_client
        if self.supabase_client:
            DataManager(self.supabase_client)
        self.obra_content = None  # widget de detalle de obra embebido
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Barra lateral
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(250)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(2, 0)
        self.sidebar.setGraphicsEffect(shadow)
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        sidebar_layout.setContentsMargins(10, 30, 10, 20)
        sidebar_layout.setSpacing(10)
        
        brand = QLabel()
        local_assets = Path(__file__).resolve().parents[2] / "assets"
        info_logos = Path(__file__).resolve().parents[3] / "INFO PROYECTO" / "LOGOS"
        logo_path = None
        for d in [local_assets, info_logos]:
            for fname in ["logo_gryphus_sidebar_blanco.png", "logo_gryphus_nombre_cf.png", "logo_gryphus_nombre_sf.png"]:
                p = d / fname
                if p.exists():
                    logo_path = str(p)
                    break
            if logo_path:
                break
            
        if logo_path:
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaledToWidth(210, Qt.TransformationMode.SmoothTransformation)
            brand.setPixmap(scaled_pixmap)
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand.setStyleSheet("padding-bottom: 30px;")
        sidebar_layout.addWidget(brand)
        
        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_dashboard.setProperty("class", "SidebarButton")
        self.btn_dashboard.setCheckable(True)
        self.btn_dashboard.setChecked(True)
        self.btn_dashboard.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_dashboard.clicked.connect(lambda: self.switch_view(0))
        
        self.btn_ingesta = QPushButton("Ingesta de Obras")
        self.btn_ingesta.setProperty("class", "SidebarButton")
        self.btn_ingesta.setCheckable(True)
        self.btn_ingesta.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ingesta.clicked.connect(lambda: self.switch_view(1))
        
        self.btn_control_personal = QPushButton("Control de Personal")
        self.btn_control_personal.setProperty("class", "SidebarButton")
        self.btn_control_personal.setCheckable(True)
        self.btn_control_personal.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_control_personal.clicked.connect(lambda: self.switch_view(2))

        self.btn_materiales = QPushButton("Materiales")
        self.btn_materiales.setProperty("class", "SidebarButton")
        self.btn_materiales.setCheckable(True)
        self.btn_materiales.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_materiales.clicked.connect(lambda: self.switch_view(3))

        self.btn_asistencia = QPushButton("Asistencia")
        self.btn_asistencia.setProperty("class", "SidebarButton")
        self.btn_asistencia.setCheckable(True)
        self.btn_asistencia.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_asistencia.clicked.connect(lambda: self.switch_view(4))
        
        self.btn_dashboard.setToolTip("Panel principal de control y avance de obras")
        self.btn_ingesta.setToolTip("Ingesta y procesamiento de reportes diarios de terreno")
        self.btn_control_personal.setToolTip("Control de personal, dotación y subcontratistas")
        self.btn_materiales.setToolTip("Gestión de stock, inventario y solicitudes de materiales")
        self.btn_asistencia.setToolTip("Auditoría y reportes detallados de asistencia")
        
        sidebar_layout.addWidget(self.btn_dashboard)
        sidebar_layout.addWidget(self.btn_ingesta)
        sidebar_layout.addWidget(self.btn_control_personal)
        sidebar_layout.addWidget(self.btn_materiales)
        sidebar_layout.addWidget(self.btn_asistencia)
        
        # Espaciador para empujar botones hacia abajo
        sidebar_layout.addStretch()
        
        self.btn_resync = QPushButton("⚡ Resincronizar Datos")
        self.btn_resync.setProperty("class", "SidebarButtonSync")
        self.btn_resync.setToolTip("Forzar actualización de todos los datos desde Supabase")
        self.btn_resync.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_resync.clicked.connect(self.resincronizar_todo)
        sidebar_layout.addWidget(self.btn_resync)

        self.btn_updates = QPushButton("🔄 Buscar Actualizaciones")
        self.btn_updates.setProperty("class", "SidebarButtonUpdate")
        self.btn_updates.setToolTip("Comprobar si existe una nueva versión disponible en GitHub")
        self.btn_updates.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_updates.clicked.connect(self.buscar_actualizaciones_manual)
        sidebar_layout.addWidget(self.btn_updates)

        self.btn_logout = QPushButton("Cerrar Sesión")
        self.btn_logout.setProperty("class", "SidebarButtonLogout")
        self.btn_logout.setToolTip("Cerrar sesión activa y salir de la cuenta")
        self.btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_logout.clicked.connect(self.logout_requested.emit)
        sidebar_layout.addWidget(self.btn_logout)

        version_lbl = QLabel(f"GryPhus Conect Gerencia v{__version__}  🟢\nGryphus Systems")
        version_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_lbl.setStyleSheet("font-size: 11px; color: #D8D5CD; font-weight: 600; padding-top: 6px;")
        sidebar_layout.addWidget(version_lbl)
        
        # Área de contenido
        self.content_stack = QStackedWidget()
        self.content_stack.setAutoFillBackground(True)
        
        self.dashboard_content = DashboardContent(self.supabase_client)
        self.ingesta_content = IngestaContent(self.supabase_client)
        self.control_personal_content = ControlPersonalContent(self.supabase_client)
        self.materiales_content = MaterialesContent(self.supabase_client)
        self.reportes_asistencia_content = ReportesAsistenciaContent(self.supabase_client)
        
        self.content_stack.addWidget(self.dashboard_content)             # index 0
        self.content_stack.addWidget(self.ingesta_content)               # index 1
        self.content_stack.addWidget(self.control_personal_content)     # index 2
        self.content_stack.addWidget(self.materiales_content)            # index 3
        self.content_stack.addWidget(self.reportes_asistencia_content)  # index 4
        
        # Conectar señal de obra seleccionada desde el dashboard
        self.dashboard_content.obra_selected.connect(self.navegar_a_obra)
        
        layout.addWidget(self.sidebar)
        layout.addWidget(self.content_stack)
        
        # Seleccionar la pestaña por defecto y cargar datos iniciales
        self.switch_view(0)

    def navegar_a_obra(self, obra):
        """Navega al detalle de la obra dentro del mismo stack, sin abrir ventana nueva."""
        self.content_stack.setUpdatesEnabled(False)
        try:
            # Eliminar el widget de detalle anterior si existe
            if self.obra_content is not None:
                self.content_stack.removeWidget(self.obra_content)
                self.obra_content.deleteLater()
                self.obra_content = None

            # Obtener el ID del usuario autenticado para pasarlo al EDP
            current_user_id = None
            if self.supabase_client:
                try:
                    session = self.supabase_client.auth.get_session()
                    if session and session.user:
                        current_user_id = session.user.id
                except Exception:
                    pass

            # Crear el nuevo widget de detalle embebido
            self.obra_content = AvancesContent(obra, self.supabase_client, user_id=current_user_id)
            self.obra_content.volver_dashboard.connect(lambda: self.switch_view(0))
            self.content_stack.addWidget(self.obra_content)

            # Navegar al índice del detalle
            obra_index = self.content_stack.indexOf(self.obra_content)
            self.content_stack.setCurrentIndex(obra_index)

            # Deseleccionar todos los botones del sidebar (estamos en sub-vista)
            self.btn_dashboard.setChecked(False)
            self.btn_ingesta.setChecked(False)
            self.btn_control_personal.setChecked(False)
            self.btn_materiales.setChecked(False)
            self.btn_asistencia.setChecked(False)
        finally:
            self.content_stack.setUpdatesEnabled(True)

        top_window = self.window()
        if top_window is not None:
            top_window.activateWindow()

    def switch_view(self, index):
        # Limpiar el detalle de obra si existe al navegar a otra sección
        if self.obra_content is not None:
            self.content_stack.removeWidget(self.obra_content)
            self.obra_content.deleteLater()
            self.obra_content = None

        self.content_stack.setCurrentIndex(index)
        self.btn_dashboard.setChecked(index == 0)
        self.btn_ingesta.setChecked(index == 1)
        self.btn_control_personal.setChecked(index == 2)
        self.btn_materiales.setChecked(index == 3)
        self.btn_asistencia.setChecked(index == 4)
        
        # Recargar los datos dinámicamente al entrar a cada vista
        if index == 0:  # Dashboard
            self.dashboard_content.cargar_obras()
        elif index == 1:  # Ingesta
            self.ingesta_content.cargar_jefes()
        elif index == 2:  # Control de Personal
            self.control_personal_content.cargar_datos()
        elif index == 3:  # Materiales
            self.materiales_content.cargar_materiales()
        elif index == 4:  # Asistencia
            self.reportes_asistencia_content._cargar_obras()

    def resincronizar_todo(self):
        """Resincroniza todos los datos recargándolos directamente desde Supabase a través del batch inicial."""
        try:
            self.btn_resync.setEnabled(False)
            self.btn_resync.setText("Sincronizando...")

            from src.core.workers import FetchInitialBatchWorker
            self.resync_worker = FetchInitialBatchWorker(self.supabase_client, force_refresh=True)
            self.resync_worker.success.connect(self.on_resync_success)
            self.resync_worker.error.connect(self.on_resync_error)
            self.resync_worker.start()
        except Exception as e:
            self.btn_resync.setEnabled(True)
            self.btn_resync.setText("Resincronizar Datos")
            QMessageBox.warning(
                self,
                "Error de Resincronización",
                f"Ocurrió un error al intentar resincronizar los datos: {str(e)}"
            )

    def on_resync_success(self, data=None):
        self.btn_resync.setEnabled(True)
        self.btn_resync.setText("Resincronizar Datos")
        self.dashboard_content.cargar_obras(force_refresh=False)
        self.ingesta_content.cargar_jefes()
        self.control_personal_content.cargar_datos()
        self.materiales_content.cargar_materiales(force_refresh=False)
        self.reportes_asistencia_content._cargar_obras()

        if self.obra_content is not None and hasattr(self.obra_content, 'cargar_datos'):
            self.obra_content.cargar_datos(force_refresh=True)

        QMessageBox.information(
            self,
            "Resincronización Completada",
            "Todos los datos de la aplicación se han actualizado exitosamente desde Supabase."
        )

    def on_resync_error(self, err_msg: str):
        self.btn_resync.setEnabled(True)
        self.btn_resync.setText("Resincronizar Datos")
        QMessageBox.warning(
            self,
            "Error de Resincronización",
            f"Ocurrió un error al intentar resincronizar los datos: {err_msg}"
        )

    def buscar_actualizaciones_manual(self):
        self.btn_updates.setEnabled(False)
        self.btn_updates.setText("Buscando...")
        self.manual_update_checker = CheckUpdateWorker(parent=self)
        self.manual_update_checker.update_available.connect(self._on_manual_update_available)
        self.manual_update_checker.up_to_date.connect(self._on_manual_up_to_date)
        self.manual_update_checker.check_failed.connect(self._on_manual_update_failed)
        self.manual_update_checker.start()

    def _on_manual_update_available(self, data: dict):
        self.btn_updates.setEnabled(True)
        self.btn_updates.setText("Buscar Actualizaciones")
        dlg = UpdateDialog(data, parent=self)
        dlg.exec()

    def _on_manual_up_to_date(self, data: dict):
        self.btn_updates.setEnabled(True)
        self.btn_updates.setText("Buscar Actualizaciones")
        QMessageBox.information(
            self,
            "Aplicación al Día",
            f"Tienes instalada la versión más reciente de GryPhus Conect Gerencia (v{__version__})."
        )

    def _on_manual_update_failed(self, err_msg: str):
        self.btn_updates.setEnabled(True)
        self.btn_updates.setText("Buscar Actualizaciones")
        QMessageBox.warning(
            self,
            "Actualizaciones",
            f"No se pudo comprobar si hay actualizaciones:\n{err_msg}"
        )


