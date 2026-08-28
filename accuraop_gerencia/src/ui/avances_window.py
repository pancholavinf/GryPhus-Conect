import os
import urllib.request
import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QSplitter, QTextEdit, QFrame, QGraphicsDropShadowEffect,
    QScrollArea, QMessageBox, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QColor, QPixmap, QImage, QIcon
from src.core.workers import FetchObraDetailsWorker, UpdateAvanceStatusWorker
from src.ui.reportes_view import ReportesContent
from src.ui.edp_tab import EDPTab

# Matplotlib integration
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import requests

class ImageDownloader(QThread):
    finished = pyqtSignal(bytes)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            resp = requests.get(
                self.url,
                headers={'User-Agent': 'Mozilla/5.0'},
                timeout=10
            )
            resp.raise_for_status()
            self.finished.emit(resp.content)
        except Exception as e:
            self.error.emit(str(e))


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='#FFFFFF')
        self.axes = self.fig.add_subplot(111)
        # Tight layout to avoid cropping labels
        self.fig.tight_layout()
        super().__init__(self.fig)
        if parent is not None:
            self.setParent(parent)


class AvancesContent(QWidget):
    volver_dashboard = pyqtSignal()

    def __init__(self, obra_data, supabase_client, user_id=None):
        super().__init__()
        self.obra_data = obra_data
        self.supabase = supabase_client
        self.user_id = user_id  # ID del administrador autenticado (para EDP)
        self.items = []
        self.avances = []
        self.filtered_avances = []
        self.downloader = None
        self.chart_style = "agrupado"  # 'agrupado' or 'apilado'

        self.setup_ui()
        self.cargar_datos()

    def setup_ui(self):
        self.setObjectName("MainCentralWidget")

        # Main Layout directly on self (widget, not QMainWindow)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # Header Title and Subtitle
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Back button
        self.btn_volver = QPushButton("← Volver al Dashboard")
        self.btn_volver.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_volver.setStyleSheet(
            "QPushButton { background: transparent; color: #2D3033; border: none; "
            "font-size: 13px; font-weight: 600; padding: 4px 0px; } "
            "QPushButton:hover { color: #F3A500; }"
        )
        self.btn_volver.clicked.connect(self.volver_dashboard.emit)
        header_layout.addWidget(self.btn_volver)

        header_layout.addSpacing(16)

        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        self.title_label = QLabel(f"Obra: {self.obra_data.get('nombre', 'Sin Nombre')}")
        self.title_label.setObjectName("TitleLabel")
        self.title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #1F2115;")

        self.subtitle_label = QLabel("Visualización de estadísticas generales de progreso y bitácora detallada de avances.")
        self.subtitle_label.setStyleSheet("color: #2D3033; font-size: 13px;")

        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.subtitle_label)
        header_layout.addWidget(title_container)

        header_layout.addStretch()

        # Reload Button
        self.btn_reload = QPushButton("Recargar Datos")
        self.btn_reload.setObjectName("SecondaryButton")
        self.btn_reload.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reload.clicked.connect(lambda: self.cargar_datos(force_refresh=True))
        self.btn_reload.setStyleSheet("padding: 6px 14px; font-size: 13px; height: 30px; margin-right: 8px;")
        header_layout.addWidget(self.btn_reload)

        # Status badge
        self.badge_frame = QFrame()
        self.badge_frame.setFrameShape(QFrame.Shape.StyledPanel)
        badge_layout = QHBoxLayout(self.badge_frame)
        badge_layout.setContentsMargins(12, 6, 12, 6)
        
        estado = self.obra_data.get('estado', 'Activa')
        self.badge_label = QLabel(estado.upper())
        color_badge = "#10B981" if estado.lower() == "activa" else "#EF4444"
        self.badge_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {color_badge}15;
                border: 1px solid {color_badge};
                border-radius: 6px;
            }}
            QLabel {{
                color: {color_badge};
                font-weight: bold;
                font-size: 12px;
            }}
        """)
        badge_layout.addWidget(self.badge_label)
        header_layout.addWidget(self.badge_frame)

        self.main_layout.addWidget(header_widget)

        # Tabs Container
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #E2E8F0;
                background-color: #FFFFFF;
                border-radius: 8px;
                padding: 10px;
            }
            QTabBar::tab {
                background-color: #F4F6F8;
                color: #2D3033;
                border: 1px solid #E2E8F0;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
                margin-right: 4px;
            }
            QTabBar::tab:hover {
                background-color: #E2E8F0;
                color: #1F2115;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                color: #F3A500;
                border: 1px solid #E2E8F0;
                border-bottom: 2px solid #FFFFFF;
            }
        """)

        self.tab_stats = QWidget()
        self.tab_table = QWidget()
        self.tab_reportes = None
        self.tab_edp = None

        self.tab_reportes_dummy = QWidget()
        self.tab_edp_dummy = QWidget()

        self.setup_tab_stats()
        self.setup_tab_table()

        self.tabs.addTab(self.tab_stats, "Gráficos y Estadísticas")
        self.tabs.addTab(self.tab_table, "Detalle de Avances")
        self.tabs.addTab(self.tab_reportes_dummy, "Reportes y Consumo")
        self.tabs.addTab(self.tab_edp_dummy, "Estados de Pago")

        self.tabs.currentChanged.connect(self._on_tab_changed)

        self.main_layout.addWidget(self.tabs)

    def _on_tab_changed(self, index):
        if index == 2 and self.tab_reportes is None:
            self.tab_reportes = ReportesContent(supabase_client=self.supabase, fixed_obra_id=self.obra_data.get('id'))
            self.tabs.removeTab(2)
            self.tabs.insertTab(2, self.tab_reportes, "Reportes y Consumo")
            self.tabs.setCurrentIndex(2)
        elif index == 3 and self.tab_edp is None:
            self.tab_edp = EDPTab(
                supabase_client=self.supabase,
                obra_id=self.obra_data.get('id'),
                user_id=self.user_id
            )
            self.tabs.removeTab(3)
            self.tabs.insertTab(3, self.tab_edp, "Estados de Pago")
            self.tabs.setCurrentIndex(3)

    def setup_tab_stats(self):
        stats_layout = QVBoxLayout(self.tab_stats)
        stats_layout.setContentsMargins(10, 10, 10, 10)
        stats_layout.setSpacing(15)

        # KPI Summary Row
        kpi_widget = QWidget()
        kpi_layout = QHBoxLayout(kpi_widget)
        kpi_layout.setContentsMargins(0, 0, 0, 0)
        kpi_layout.setSpacing(15)

        self.kpi_contratado = self.create_kpi_card("Presupuesto Contratado", "$0", "#2D3033")
        self.kpi_ejecutado = self.create_kpi_card("Ejecutado (Aprobado)", "$0", "#10B981")
        self.kpi_pendiente = self.create_kpi_card("Pendiente de Aprobación", "$0", "#F59E0B")
        self.kpi_progreso = self.create_kpi_card("Progreso General", "0.0%", "#F3A500")

        kpi_layout.addWidget(self.kpi_contratado)
        kpi_layout.addWidget(self.kpi_ejecutado)
        kpi_layout.addWidget(self.kpi_pendiente)
        kpi_layout.addWidget(self.kpi_progreso)

        stats_layout.addWidget(kpi_widget)

        # Scroll area for charts grid
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("background-color: transparent;")

        charts_container = QWidget()
        charts_container.setStyleSheet("background-color: transparent;")
        self.charts_grid = QVBoxLayout(charts_container)
        self.charts_grid.setContentsMargins(0, 0, 0, 0)
        self.charts_grid.setSpacing(20)

        # First row of charts: Progress over time & Location/Structure Progress
        row1_widget = QWidget()
        row1_layout = QHBoxLayout(row1_widget)
        row1_layout.setContentsMargins(0, 0, 0, 0)
        row1_layout.setSpacing(15)

        # Chart 1 Container Card
        c1_card = QFrame()
        c1_card.setStyleSheet("background-color: #FFFFFF; color: #1F2115; border: 1px solid #E2E8F0; border-radius: 8px;")
        c1_layout = QVBoxLayout(c1_card)
        c1_layout.addWidget(QLabel("<b>Progreso Temporal Acumulado</b>", styleSheet="font-size: 14px; color: #2D3033;"))
        self.canvas_time = MplCanvas(parent=c1_card, width=5, height=3)
        c1_layout.addWidget(self.canvas_time)
        row1_layout.addWidget(c1_card, stretch=1)

        # Chart 2 Container Card (with Switcher for Location / Structure + Chart Style Toggle)
        c2_card = QFrame()
        c2_card.setStyleSheet("background-color: #FFFFFF; color: #1F2115; border: 1px solid #E2E8F0; border-radius: 8px;")
        c2_layout = QVBoxLayout(c2_card)
        c2_header = QWidget()
        c2_header_layout = QHBoxLayout(c2_header)
        c2_header_layout.setContentsMargins(0, 0, 0, 0)
        c2_header_layout.addWidget(QLabel("<b>Avance por Categoría</b>", styleSheet="font-size: 14px; color: #2D3033;"))
        c2_header_layout.addStretch()

        self.btn_toggle_style = QPushButton("Vista: Agrupado")
        self.btn_toggle_style.setFixedHeight(26)
        self.btn_toggle_style.setStyleSheet(
            "QPushButton { padding: 2px 10px; font-size: 11px; background-color: #F4F6F8; "
            "color: #F3A500; border: 1px solid #A5B4FC; border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background-color: #C7D2FE; color: #F3A500; }"
        )
        self.btn_toggle_style.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_style.clicked.connect(self.toggle_chart_style)
        c2_header_layout.addWidget(self.btn_toggle_style)

        c2_header_layout.addSpacing(6)

        self.combo_group_by = QComboBox()
        self.combo_group_by.addItems(["Ubicación", "Estructura", "Material"])
        self.combo_group_by.currentIndexChanged.connect(self.actualizar_grafico_avance_categoria)
        self.combo_group_by.setStyleSheet("padding: 4px 8px; font-size: 12px; height: 26px; color: #1F2115; background-color: #FFFFFF;")
        c2_header_layout.addWidget(self.combo_group_by)
        c2_layout.addWidget(c2_header)

        self.canvas_category = MplCanvas(parent=c2_card, width=5, height=3)
        c2_layout.addWidget(self.canvas_category)
        row1_layout.addWidget(c2_card, stretch=1)

        self.charts_grid.addWidget(row1_widget)

        # Second row of charts: Pie Chart for Revision Status & Financial Progress
        row2_widget = QWidget()
        row2_layout = QHBoxLayout(row2_widget)
        row2_layout.setContentsMargins(0, 0, 0, 0)
        row2_layout.setSpacing(15)

        # Chart 3 Container Card
        c3_card = QFrame()
        c3_card.setStyleSheet("background-color: #FFFFFF; color: #1F2115; border: 1px solid #E2E8F0; border-radius: 8px;")
        c3_layout = QVBoxLayout(c3_card)
        c3_layout.addWidget(QLabel("<b>Distribución de Avances por Estado</b>", styleSheet="font-size: 14px; color: #2D3033;"))
        self.canvas_status = MplCanvas(parent=c3_card, width=5, height=3)
        c3_layout.addWidget(self.canvas_status)
        row2_layout.addWidget(c3_card, stretch=1)

        # Chart 4 Container Card
        c4_card = QFrame()
        c4_card.setStyleSheet("background-color: #FFFFFF; color: #1F2115; border: 1px solid #E2E8F0; border-radius: 8px;")
        c4_layout = QVBoxLayout(c4_card)
        c4_layout.addWidget(QLabel("<b>Comparación Económica Presupuestaria</b>", styleSheet="font-size: 14px; color: #2D3033;"))
        self.canvas_financial = MplCanvas(parent=c4_card, width=5, height=3)
        c4_layout.addWidget(self.canvas_financial)
        row2_layout.addWidget(c4_card, stretch=1)

        self.charts_grid.addWidget(row2_widget)

        scroll_area.setWidget(charts_container)
        stats_layout.addWidget(scroll_area)

    def create_kpi_card(self, title, val, color):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                color: #1F2115;
                border: 1px solid #E2E8F0;
                border-left: 5px solid {color};
                border-radius: 8px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 10))
        shadow.setOffset(0, 2)
        card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(4)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("color: #2D3033; font-size: 11px; font-weight: bold; text-transform: uppercase;")
        
        v_lbl = QLabel(val)
        v_lbl.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold; font-family: 'Montserrat';")
        
        layout.addWidget(t_lbl)
        layout.addWidget(v_lbl)
        
        # Store label ref to dynamically update later
        card.value_label = v_lbl
        return card

    def setup_tab_table(self):
        tab_layout = QVBoxLayout(self.tab_table)
        tab_layout.setContentsMargins(10, 10, 10, 10)
        tab_layout.setSpacing(12)

        # Filters Row
        filters_widget = QWidget()
        filters_layout = QHBoxLayout(filters_widget)
        filters_layout.setContentsMargins(0, 0, 0, 0)
        filters_layout.setSpacing(10)

        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por ubicación, plano, material, comentario...")
        self.search_input.textChanged.connect(self.aplicar_filtros)
        self.search_input.setStyleSheet("padding: 8px 12px; font-size: 13px; height: 32px;")
        filters_layout.addWidget(self.search_input, stretch=2)

        # Foreman filter
        self.combo_filter_jefe = QComboBox()
        self.combo_filter_jefe.addItem("Todos los Supervisores")
        self.combo_filter_jefe.currentIndexChanged.connect(self.aplicar_filtros)
        self.combo_filter_jefe.setStyleSheet("padding: 6px 12px; font-size: 13px; height: 32px;")
        filters_layout.addWidget(self.combo_filter_jefe, stretch=1)

        # Status filter
        self.combo_filter_status = QComboBox()
        self.combo_filter_status.addItems(["Todos los Estados", "Aprobados", "Pendientes", "Rechazados"])
        self.combo_filter_status.currentIndexChanged.connect(self.aplicar_filtros)
        self.combo_filter_status.setStyleSheet("padding: 6px 12px; font-size: 13px; height: 32px;")
        filters_layout.addWidget(self.combo_filter_status, stretch=1)

        # Botón Aprobar Todos los Avances
        self.btn_aprobar_todos = QPushButton("Aprobar Todos")
        self.btn_aprobar_todos.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_aprobar_todos.setToolTip("Aprobar la revisión de todos los avances mostrados")
        self.btn_aprobar_todos.setStyleSheet(
            "QPushButton { background-color: #10B981; color: #FFFFFF; font-weight: bold; border: none; border-radius: 6px; padding: 6px 14px; font-size: 13px; height: 32px; } "
            "QPushButton:hover { background-color: #059669; } "
            "QPushButton:disabled { background-color: #CBD5E1; color: #2D3033; }"
        )
        self.btn_aprobar_todos.clicked.connect(self.aprobar_todos_avances)
        filters_layout.addWidget(self.btn_aprobar_todos)

        tab_layout.addWidget(filters_widget)

        # Splitter for Table and Details Sidebar
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #E2E8F0; width: 2px; }")

        # Table Widget Container
        table_container = QWidget()
        table_vbox = QVBoxLayout(table_container)
        table_vbox.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setMinimumSectionSize(110)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Fecha", "Supervisor", "Ubicación", "Plano", 
            "Estructura", "Material", "Cantidad Rep.", "Estado"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # Fecha
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # Supervisor
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)      # Ubicación
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Plano
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)      # Estructura
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)          # Material (takes remaining space)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents) # Cantidad Rep.
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents) # Estado
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self.on_row_selected)
        
        table_vbox.addWidget(self.table)
        splitter.addWidget(table_container)

        # Right Pane: Avance Detail Inspection Sidebar
        self.sidebar_detail = QFrame()
        self.sidebar_detail.setMinimumWidth(320)
        self.sidebar_detail.setMaximumWidth(400)
        self.sidebar_detail.setStyleSheet("QFrame { background-color: #F8FAFC; color: #1F2115; border: 1px solid #E2E8F0; border-radius: 8px; }")

        sidebar_layout = QVBoxLayout(self.sidebar_detail)
        sidebar_layout.setContentsMargins(16, 16, 16, 16)
        sidebar_layout.setSpacing(12)

        sidebar_title = QLabel("Detalle del Avance")
        sidebar_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2D3033;")
        sidebar_layout.addWidget(sidebar_title)

        # Image Display Box
        self.image_container = QFrame()
        self.image_container.setFixedHeight(220)
        self.image_container.setStyleSheet("background-color: #E2E8F0; color: #1F2115; border-radius: 6px; border: 1px solid #CBD5E1;")
        
        img_container_layout = QVBoxLayout(self.image_container)
        img_container_layout.setContentsMargins(5, 5, 5, 5)
        
        self.image_label = QLabel("Seleccione un avance\npara ver la foto")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("color: #2D3033; font-size: 13px; font-weight: 500;")
        img_container_layout.addWidget(self.image_label)
        
        sidebar_layout.addWidget(self.image_container)

        # Comment Text Area
        sidebar_layout.addWidget(QLabel("<b>Comentario del Supervisor:</b>", styleSheet="font-size: 12px; color: #2D3033;"))
        self.comment_display = QTextEdit()
        self.comment_display.setReadOnly(True)
        self.comment_display.setPlaceholderText("Sin comentarios disponibles.")
        self.comment_display.setStyleSheet("background-color: #FFFFFF; color: #1F2115; border: 1px solid #E2E8F0; border-radius: 6px; padding: 8px;")
        self.comment_display.setFixedHeight(90)
        sidebar_layout.addWidget(self.comment_display)

        # Metadata Details Box
        self.meta_box = QFrame()
        self.meta_box.setStyleSheet("background-color: #FFFFFF; color: #1F2115; border: 1px solid #E2E8F0; border-radius: 6px;")
        meta_layout = QVBoxLayout(self.meta_box)
        meta_layout.setContentsMargins(12, 12, 12, 12)
        meta_layout.setSpacing(8)

        self.lbl_meta_jefe = QLabel("Supervisor: -")
        self.lbl_meta_fecha = QLabel("Fecha: -")
        self.lbl_meta_edp = QLabel("Estado de Pago: -")
        self.lbl_meta_item = QLabel("Detalle Ítem: -")
        self.lbl_meta_total_item = QLabel("Cantidad Contratada: -")
        self.lbl_meta_valor = QLabel("Valor Contrato: -")

        for lbl in [self.lbl_meta_jefe, self.lbl_meta_fecha, self.lbl_meta_edp, self.lbl_meta_item, self.lbl_meta_total_item, self.lbl_meta_valor]:
            lbl.setStyleSheet("font-size: 12px; color: #334155; font-family: 'Inter';")
            meta_layout.addWidget(lbl)

        sidebar_layout.addWidget(self.meta_box)

        # Botón de Acción: Aprobar Avance Seleccionado (debajo de los detalles)
        self.action_box = QFrame()
        self.action_box.setStyleSheet("background-color: #FFFFFF; color: #1F2115; border: 1px solid #E2E8F0; border-radius: 6px;")
        action_layout = QVBoxLayout(self.action_box)
        action_layout.setContentsMargins(10, 10, 10, 10)

        self.btn_aprobar_avance = QPushButton("Aprobar Avance")
        self.btn_aprobar_avance.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_aprobar_avance.setEnabled(False)
        self.btn_aprobar_avance.setStyleSheet(
            "QPushButton { background-color: #F3A500; color: #FFFFFF; font-weight: bold; border: none; border-radius: 6px; padding: 10px 14px; font-size: 13px; } "
            "QPushButton:hover { background-color: #476386; } "
            "QPushButton:disabled { background-color: #CBD5E1; color: #2D3033; }"
        )
        self.btn_aprobar_avance.clicked.connect(self.aprobar_avance_seleccionado)
        action_layout.addWidget(self.btn_aprobar_avance)

        sidebar_layout.addWidget(self.action_box)
        sidebar_layout.addStretch()

        splitter.addWidget(self.sidebar_detail)
        tab_layout.addWidget(splitter)

    def cargar_datos(self, force_refresh: bool = False):
        if not self.supabase:
            QMessageBox.warning(self, "Error", "Cliente Supabase no inicializado.")
            return

        self.status_dialog = QMessageBox(self)
        self.status_dialog.setWindowTitle("Cargando...")
        self.status_dialog.setText("Cargando avances y cubicaciones desde la nube. Por favor espere...")
        self.status_dialog.setStandardButtons(QMessageBox.StandardButton.NoButton)
        self.status_dialog.show()

        self.worker = FetchObraDetailsWorker(self.supabase, self.obra_data.get("id"), force_refresh=force_refresh)
        self.worker.success.connect(self.on_data_success)
        self.worker.error.connect(self.on_data_error)
        self.worker.start()

        if hasattr(self, 'tab_reportes') and self.tab_reportes:
            self.tab_reportes.cargar_reportes()

    def on_data_error(self, message):
        try:
            if hasattr(self, "status_dialog") and self.status_dialog:
                self.status_dialog.hide()
                self.status_dialog.deleteLater()
                self.status_dialog = None
        except Exception:
            pass
        QMessageBox.critical(self, "Error", f"Error al cargar los datos: {message}")

    def on_data_success(self, items, avances):
        try:
            if hasattr(self, "status_dialog") and self.status_dialog:
                self.status_dialog.hide()
                self.status_dialog.deleteLater()
                self.status_dialog = None
        except Exception:
            pass

        try:
            self.items = items
            self.avances = avances
            
            # Populate foreman filter combo
            jefes_names = sorted(list(set((av.get("jefe_nombre") or "Desconocido") for av in self.avances)))
            self.combo_filter_jefe.blockSignals(True)
            self.combo_filter_jefe.clear()
            self.combo_filter_jefe.addItem("Todos los Supervisores")
            self.combo_filter_jefe.addItems(jefes_names)
            self.combo_filter_jefe.blockSignals(False)

            # Apply initial filtering
            self.aplicar_filtros()

            # Update stats
            self.calcular_estadisticas()
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Error al procesar los datos de la obra: {str(e)}")


    def calcular_estadisticas(self):
        # Calculate budget and execution values
        total_budget = 0.0
        total_executed_approved = 0.0
        total_executed_pending = 0.0

        for item in self.items:
            qty = item.get("cantidad", 0.0) or 0.0
            price = item.get("precio_unitario_contrato", 0.0) or 0.0
            total_budget += qty * price

        for av in self.avances:
            qty_av = av.get("cantidad", 0.0) or 0.0
            price_item = av.get("item_precio_unitario", 0.0) or 0.0
            val_av = qty_av * price_item
            
            status = str(av.get("estado_revision", "pendiente")).lower()
            if status == "aprobado":
                total_executed_approved += val_av
            elif status == "pendiente":
                total_executed_pending += val_av

        # Update KPI text
        def fmt_currency(val):
            return f"$ {val:,.0f}"

        self.kpi_contratado.value_label.setText(fmt_currency(total_budget))
        self.kpi_ejecutado.value_label.setText(fmt_currency(total_executed_approved))
        self.kpi_pendiente.value_label.setText(fmt_currency(total_executed_pending))

        prog_pct = (total_executed_approved / total_budget * 100.0) if total_budget > 0 else 0.0
        self.kpi_progreso.value_label.setText(f"{prog_pct:.1f}%")

        # Draw graphs
        self.actualizar_graficos(total_budget, total_executed_approved, total_executed_pending)

    def toggle_chart_style(self):
        if self.chart_style == "agrupado":
            self.chart_style = "apilado"
            self.btn_toggle_style.setText("Vista: Apilado")
        else:
            self.chart_style = "agrupado"
            self.btn_toggle_style.setText("Vista: Agrupado")
        self.actualizar_grafico_avance_categoria()

    def actualizar_graficos(self, total_budget, executed_approved, executed_pending):
        # 1. Temporal Cumulative Progress Chart — 2 lines: Approved vs Total
        self.canvas_time.axes.clear()

        all_avances_sorted = sorted(self.avances, key=lambda x: x.get("fecha_captura_local") or "")

        def build_cumulative(avance_list):
            date_values = {}
            for av in avance_list:
                raw_date = av.get("fecha_captura_local") or ""
                if raw_date:
                    try:
                        dt = datetime.datetime.strptime(raw_date.split("T")[0], "%Y-%m-%d").date()
                        val = (av.get("cantidad") or 0.0) * (av.get("item_precio_unitario") or 0.0)
                        date_values[dt] = date_values.get(dt, 0.0) + val
                    except Exception:
                        pass
            sorted_dates = sorted(date_values.keys())
            dates = []
            pcts = []
            cum = 0.0
            if sorted_dates and total_budget > 0:
                dates.append(sorted_dates[0] - datetime.timedelta(days=1))
                pcts.append(0.0)
                for dt in sorted_dates:
                    cum += date_values[dt]
                    dates.append(dt)
                    pcts.append((cum / total_budget) * 100.0)
            return dates, pcts

        approved_list = [av for av in all_avances_sorted if str(av.get("estado_revision") or "").lower() == "aprobado"]
        dates_all, pcts_all = build_cumulative(all_avances_sorted)
        dates_app, pcts_app = build_cumulative(approved_list)

        if dates_all:
            self.canvas_time.axes.plot(dates_all, pcts_all, marker='', color='#94A3B8', linewidth=2,
                                       linestyle='--', label="Total Reportado")
            self.canvas_time.axes.fill_between(dates_all, pcts_all, color='#94A3B8', alpha=0.08)
        if dates_app:
            self.canvas_time.axes.plot(dates_app, pcts_app, marker='o', color='#F3A500', linewidth=2,
                                       label="Avance Aprobado")
            self.canvas_time.axes.fill_between(dates_app, pcts_app, color='#F3A500', alpha=0.15)

        if dates_all or dates_app:
            self.canvas_time.axes.set_ylabel("% del Presupuesto", fontsize=10)
            self.canvas_time.axes.grid(True, linestyle='--', alpha=0.4)
            self.canvas_time.axes.set_ylim(-5, 105)
            self.canvas_time.axes.legend(fontsize=8, loc='upper left')
            self.canvas_time.fig.autofmt_xdate()
        else:
            self.canvas_time.axes.text(0.5, 0.5, "No hay avances registrados\npara graficar el progreso temporal",
                                       ha='center', va='center', color='#2D3033')
            self.canvas_time.axes.set_axis_off()

        self.canvas_time.draw()

        # 2. Progress by Category (Location/Structure/Material)
        self.actualizar_grafico_avance_categoria()

        # 3. Revision Status Chart (Pie/Doughnut)
        self.canvas_status.axes.clear()
        status_counts = {"Aprobado": 0, "Pendiente": 0, "Rechazado": 0}
        for av in self.avances:
            st = str(av.get("estado_revision", "pendiente")).lower()
            if st == "aprobado":
                status_counts["Aprobado"] += 1
            elif st == "pendiente":
                status_counts["Pendiente"] += 1
            elif st == "rechazado":
                status_counts["Rechazado"] += 1

        labels = []
        sizes = []
        colors = []
        
        status_colors_map = {
            "Aprobado": "#10B981",
            "Pendiente": "#F59E0B",
            "Rechazado": "#EF4444"
        }

        for st, count in status_counts.items():
            if count > 0:
                labels.append(f"{st} ({count})")
                sizes.append(count)
                colors.append(status_colors_map[st])

        if sizes:
            self.canvas_status.axes.pie(
                sizes, labels=labels, colors=colors, autopct='%1.1f%%', 
                startangle=90, wedgeprops=dict(width=0.4, edgecolor='w')
            )
        else:
            self.canvas_status.axes.text(0.5, 0.5, "No hay avances registrados", 
                                        ha='center', va='center', color='#2D3033')
            self.canvas_status.axes.set_axis_off()

        self.canvas_status.draw()

        # 4. Financial Budget Chart (Bar)
        self.canvas_financial.axes.clear()
        categories = ["Contratado", "Aprobado", "Pendiente"]
        values = [total_budget, executed_approved, executed_pending]
        colors = ["#2D3033", "#F3A500", "#F59E0B"]

        bars = self.canvas_financial.axes.bar(categories, values, color=colors, width=0.5)
        self.canvas_financial.axes.grid(axis='y', linestyle='--', alpha=0.5)
        
        # Add labels on top of the bars
        for bar in bars:
            height = bar.get_height()
            self.canvas_financial.axes.annotate(
                f"${height:,.0f}" if height > 0 else "$0",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),  # 3 points vertical offset
                textcoords="offset points",
                ha='center', va='bottom', fontsize=8, fontweight='bold'
            )
        
        self.canvas_financial.axes.set_ylabel("Valor en Pesos ($)", fontsize=10)
        self.canvas_financial.draw()

    def actualizar_grafico_avance_categoria(self):
        self.canvas_category.axes.clear()
        
        group_field = self.combo_group_by.currentText().lower()
        db_field_map = {
            "ubicación": "ubicacion",
            "estructura": "estructura",
            "material": "material"
        }
        db_key = db_field_map.get(group_field, "ubicacion")

        # Gather all categories from cubicacion items
        all_cats = sorted(set((item.get(db_key) or "Sin Asignar") for item in self.items)) or ["Sin Asignar"]
        # Limit to top 10 most active categories
        all_cats = all_cats[:10]

        estado_colors = {
            "aprobado":  "#10B981",
            "pendiente": "#F59E0B",
            "rechazado": "#EF4444",
        }
        estados = ["aprobado", "pendiente", "rechazado"]

        # Build a dict: cat -> estado -> total_qty
        cat_estado_qty = {cat: {e: 0.0 for e in estados} for cat in all_cats}
        for av in self.avances:
            cat = av.get(f"item_{db_key}") or "Sin Asignar"
            if cat not in cat_estado_qty:
                continue
            estado = str(av.get("estado_revision") or "pendiente").lower()
            if estado not in estados:
                estado = "pendiente"
            qty = float(av.get("cantidad") or 0.0)
            cat_estado_qty[cat][estado] += qty

        # Only show categories that have at least one avance
        active_cats = [c for c in all_cats if sum(cat_estado_qty[c].values()) > 0]
        if not active_cats:
            self.canvas_category.axes.text(
                0.5, 0.5, "No hay avances registrados\npara las categorías de esta obra",
                ha='center', va='center', color='#2D3033'
            )
            self.canvas_category.axes.set_axis_off()
            self.canvas_category.draw()
            return

        import numpy as np
        y = np.arange(len(active_cats))
        n_estados = len(estados)

        if self.chart_style == "agrupado":
            bar_height = 0.22
            offsets = [-bar_height, 0, bar_height]
            for i, estado in enumerate(estados):
                vals = [cat_estado_qty[c][estado] for c in active_cats]
                self.canvas_category.axes.barh(
                    y + offsets[i], vals, height=bar_height,
                    color=estado_colors[estado], label=estado.capitalize(), alpha=0.9
                )
            self.canvas_category.axes.set_yticks(y)
            self.canvas_category.axes.set_yticklabels(active_cats, fontsize=8)
        else:  # apilado
            lefts = [0.0] * len(active_cats)
            for estado in estados:
                vals = [cat_estado_qty[c][estado] for c in active_cats]
                self.canvas_category.axes.barh(
                    y, vals, left=lefts, height=0.5,
                    color=estado_colors[estado], label=estado.capitalize(), alpha=0.9
                )
                lefts = [l + v for l, v in zip(lefts, vals)]
            self.canvas_category.axes.set_yticks(y)
            self.canvas_category.axes.set_yticklabels(active_cats, fontsize=8)

        self.canvas_category.axes.invert_yaxis()
        self.canvas_category.axes.set_xlabel("Cantidad Reportada", fontsize=10)
        self.canvas_category.axes.grid(axis='x', linestyle='--', alpha=0.4)
        self.canvas_category.axes.legend(fontsize=8, loc='lower right')

        self.canvas_category.draw()

    def aplicar_filtros(self):
        query = self.search_input.text().strip().lower()
        filter_jefe = self.combo_filter_jefe.currentText()
        filter_status = self.combo_filter_status.currentText()

        self.filtered_avances = []

        for av in self.avances:
            # 1. Supervisor filter
            if filter_jefe != "Todos los Supervisores" and av.get("jefe_nombre") != filter_jefe:
                continue

            # 2. Revision Status filter
            status = str(av.get("estado_revision", "pendiente")).lower()
            if filter_status == "Aprobados" and status != "aprobado":
                continue
            elif filter_status == "Pendientes" and status != "pendiente":
                continue
            elif filter_status == "Rechazados" and status != "rechazado":
                continue

            # 3. Search query query
            if query:
                loc = av.get("item_ubicacion", "").lower()
                plan = av.get("item_plano", "").lower()
                mat = av.get("item_material", "").lower()
                est = av.get("item_estructura", "").lower()
                com = av.get("comentario", "")
                com = com.lower() if com else ""
                jefe = av.get("jefe_nombre", "").lower()

                if not (query in loc or query in plan or query in mat or query in est or query in com or query in jefe):
                    continue

            self.filtered_avances.append(av)

        self.actualizar_tabla()

    def actualizar_tabla(self):
        self.table.blockSignals(True)
        self.table.setRowCount(0)

        for av in self.filtered_avances:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Date
            raw_date = av.get("fecha_captura_local", "")
            date_str = ""
            if raw_date:
                try:
                    # ISO Format: 2026-07-15T02:05:23-04:00
                    date_str = raw_date.split(".")[0].replace("T", " ")
                    if "-" in date_str and len(date_str) > 16:
                        # Strip timezone
                        date_str = date_str[:16]
                except:
                    date_str = raw_date

            # Status Badge widget
            is_cobrado = bool(av.get("estado_pago_id"))
            status = str(av.get("estado_revision", "pendiente")).capitalize()
            edp_num = av.get("numero_estado_pago")
            
            if is_cobrado:
                badge_txt = f"EDP N° {edp_num}" if edp_num else "Cobrado"
                status_widget = QLabel(badge_txt)
                status_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
                status_widget.setStyleSheet("color: #047857; font-weight: bold; background-color: #D1FAE5; border: 1px solid #10B981; border-radius: 4px; padding: 2px;")
            else:
                status_widget = QLabel(status)
                status_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
                if status.lower() == "aprobado":
                    status_widget.setStyleSheet("color: #10B981; font-weight: bold; background-color: #D1FAE5; border-radius: 4px; padding: 2px;")
                elif status.lower() == "pendiente":
                    status_widget.setStyleSheet("color: #D97706; font-weight: bold; background-color: #FEF3C7; border-radius: 4px; padding: 2px;")
                else:
                    status_widget.setStyleSheet("color: #DC2626; font-weight: bold; background-color: #FEE2E2; border-radius: 4px; padding: 2px;")

            qty = av.get("cantidad", 0.0) or 0.0
            
            # Populate cells
            self.table.setItem(row, 0, QTableWidgetItem(str(date_str or "")))
            self.table.setItem(row, 1, QTableWidgetItem(str(av.get("jefe_nombre") or "Desconocido")))
            self.table.setItem(row, 2, QTableWidgetItem(str(av.get("item_ubicacion") or "")))
            self.table.setItem(row, 3, QTableWidgetItem(str(av.get("item_plano") or "")))
            self.table.setItem(row, 4, QTableWidgetItem(str(av.get("item_estructura") or "")))
            self.table.setItem(row, 5, QTableWidgetItem(str(av.get("item_material") or "")))
            self.table.setItem(row, 6, QTableWidgetItem(f"{qty:g}"))
            
            # Place status badge
            self.table.setCellWidget(row, 7, status_widget)

        self.table.blockSignals(False)
        
        # Clear detail panel and reset action button
        self.image_label.setPixmap(QPixmap())
        self.image_label.setText("Seleccione un avance\npara ver la foto")
        self.comment_display.clear()
        self.lbl_meta_jefe.setText("Supervisor: -")
        self.lbl_meta_fecha.setText("Fecha: -")
        self.lbl_meta_edp.setText("Estado de Pago: -")
        self.lbl_meta_item.setText("Detalle Ítem: -")
        self.lbl_meta_total_item.setText("Cantidad Contratada: -")
        self.lbl_meta_valor.setText("Valor Contrato: -")

        if hasattr(self, 'btn_aprobar_avance'):
            self.btn_aprobar_avance.setText("Aprobar Avance")
            self.btn_aprobar_avance.setEnabled(False)
            self.btn_aprobar_avance.setStyleSheet(
                "QPushButton { background-color: #F3A500; color: #FFFFFF; font-weight: bold; border: none; border-radius: 6px; padding: 10px 14px; font-size: 13px; } "
                "QPushButton:disabled { background-color: #CBD5E1; color: #2D3033; }"
            )

    def on_row_selected(self):
        try:
            selected_ranges = self.table.selectedRanges()
            if not selected_ranges:
                if hasattr(self, 'btn_aprobar_avance'):
                    self.btn_aprobar_avance.setEnabled(False)
                    self.btn_aprobar_avance.setText("Aprobar Avance")
                return

            row = selected_ranges[0].topRow()
            if row < 0 or row >= len(self.filtered_avances):
                return

            avance = self.filtered_avances[row]

            # Disconnect previous downloader signals instead of calling unsafe terminate()
            if self.downloader:
                try:
                    self.downloader.finished.disconnect()
                    self.downloader.error.disconnect()
                except Exception:
                    pass

            # Update metadata info
            self.lbl_meta_jefe.setText(f"<b>Supervisor:</b> {avance.get('jefe_nombre') or 'Desconocido'}")
            
            raw_date = avance.get("fecha_captura_local") or ""
            self.lbl_meta_fecha.setText(f"<b>Fecha Captura:</b> {raw_date.replace('T', ' ')[:16]}")

            edp_num = avance.get("numero_estado_pago")
            raw_f_edp = avance.get("fecha_emision_edp") or ""
            f_edp = raw_f_edp[:10] if raw_f_edp else ""
            if edp_num:
                self.lbl_meta_edp.setText(f"<b>Estado de Pago:</b> <font color='#047857'><b>EDP N° {edp_num}</b></font> ({f_edp})")
            else:
                self.lbl_meta_edp.setText("<b>Estado de Pago:</b> <font color='#2D3033'>Pendiente de cobro (Sin asignar)</font>")
            
            est = avance.get('item_estructura') or ''
            mat = avance.get('item_material') or ''
            loc = avance.get('item_ubicacion') or ''
            detail_txt = f"{est} / {mat} ({loc})"
            self.lbl_meta_item.setText(f"<b>Cubicación:</b> {detail_txt}")
            
            try:
                qty_total = float(avance.get("item_cantidad_total") or 0.0)
            except (ValueError, TypeError):
                qty_total = 0.0
            self.lbl_meta_total_item.setText(f"<b>Cant. Contrato:</b> {qty_total:g}")
            
            try:
                price = float(avance.get("item_precio_unitario") or 0.0)
            except (ValueError, TypeError):
                price = 0.0
            self.lbl_meta_valor.setText(f"<b>Precio Unitario:</b> $ {price:,.0f}")

            # Update Comment
            self.comment_display.setText(avance.get("comentario") or "Sin comentario.")

            # Update Approval Button State
            estado_rev = str(avance.get("estado_revision", "pendiente")).lower()
            if estado_rev == "aprobado":
                self.btn_aprobar_avance.setText("Avance Aprobado")
                self.btn_aprobar_avance.setEnabled(False)
                self.btn_aprobar_avance.setStyleSheet(
                    "QPushButton { background-color: #D1FAE5; color: #047857; font-weight: bold; border: 1px solid #10B981; border-radius: 6px; padding: 10px 14px; font-size: 13px; }"
                )
            else:
                self.btn_aprobar_avance.setText("Aprobar Avance")
                self.btn_aprobar_avance.setEnabled(True)
                self.btn_aprobar_avance.setStyleSheet(
                    "QPushButton { background-color: #F3A500; color: #FFFFFF; font-weight: bold; border: none; border-radius: 6px; padding: 10px 14px; font-size: 13px; } "
                    "QPushButton:hover { background-color: #476386; }"
                )

            # Load image
            foto_url = avance.get("foto_url")
            if foto_url:
                self.image_label.setText("Cargando imagen...")
                self.downloader = ImageDownloader(foto_url)
                self.downloader.finished.connect(self.on_image_downloaded)
                self.downloader.error.connect(self.on_image_error)
                self.downloader.start()
            else:
                self.image_label.setPixmap(QPixmap())
                self.image_label.setText("Este avance no tiene foto asociada.")
        except Exception as e:
            import traceback
            traceback.print_exc()

    def aprobar_avance_seleccionado(self):
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            return
        row = selected_ranges[0].topRow()
        if row < 0 or row >= len(self.filtered_avances):
            return

        avance = self.filtered_avances[row]
        avance_id = avance.get("id")
        if not avance_id:
            return

        if not self.supabase:
            QMessageBox.warning(self, "Error", "Cliente Supabase no configurado.")
            return

        self.btn_aprobar_avance.setEnabled(False)
        self.btn_aprobar_avance.setText("Aprobando...")

        self.worker_update = UpdateAvanceStatusWorker(self.supabase, [avance_id], "aprobado")
        self.worker_update.success.connect(self.on_aprobar_avance_success)
        self.worker_update.error.connect(self.on_aprobar_error)
        self.worker_update.start()

    def on_aprobar_avance_success(self, avance_ids, nuevo_estado):
        set_ids = set(avance_ids)
        for av in self.avances:
            if av.get("id") in set_ids:
                av["estado_revision"] = nuevo_estado

        self.aplicar_filtros()
        self.btn_aprobar_avance.setText("Avance Aprobado")
        self.btn_aprobar_avance.setEnabled(False)
        self.btn_aprobar_avance.setStyleSheet(
            "QPushButton { background-color: #D1FAE5; color: #047857; font-weight: bold; border: 1px solid #10B981; border-radius: 6px; padding: 10px 14px; font-size: 13px; }"
        )
        # Refrescar el tab EDP para actualizar el contador de avances pendientes
        if hasattr(self, 'tab_edp') and self.tab_edp is not None:
            self.tab_edp.cargar_datos()

    def aprobar_todos_avances(self):
        if not self.filtered_avances:
            QMessageBox.information(self, "Sin Avances", "No hay avances para aprobar.")
            return

        pendientes = [av for av in self.filtered_avances if str(av.get("estado_revision")).lower() != "aprobado"]
        if not pendientes:
            QMessageBox.information(self, "Información", "Todos los avances mostrados ya se encuentran aprobados.")
            return

        reply = QMessageBox.question(
            self,
            "Aprobar Todos los Avances",
            f"¿Está seguro de que desea aprobar la revisión de los {len(pendientes)} avances pendientes?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        if not self.supabase:
            QMessageBox.warning(self, "Error", "Cliente Supabase no configurado.")
            return

        ids_to_approve = [av.get("id") for av in pendientes if av.get("id")]
        self.btn_aprobar_todos.setEnabled(False)
        self.btn_aprobar_todos.setText("Aprobando...")

        self.worker_update_all = UpdateAvanceStatusWorker(self.supabase, ids_to_approve, "aprobado")
        self.worker_update_all.success.connect(self.on_aprobar_todos_success)
        self.worker_update_all.error.connect(self.on_aprobar_error)
        self.worker_update_all.start()

    def on_aprobar_todos_success(self, avance_ids, nuevo_estado):
        set_ids = set(avance_ids)
        for av in self.avances:
            if av.get("id") in set_ids:
                av["estado_revision"] = nuevo_estado

        self.btn_aprobar_todos.setEnabled(True)
        self.btn_aprobar_todos.setText("Aprobar Todos")

        self.aplicar_filtros()

        # Refrescar el tab EDP para que los KPIs reflejen los nuevos avances aprobados
        if hasattr(self, 'tab_edp') and self.tab_edp is not None:
            self.tab_edp.cargar_datos()

        QMessageBox.information(self, "Éxito", f"Se han aprobado {len(avance_ids)} avances exitosamente.")

    def on_aprobar_error(self, message):
        self.btn_aprobar_todos.setEnabled(True)
        self.btn_aprobar_todos.setText("Aprobar Todos")
        if hasattr(self, 'btn_aprobar_avance'):
            self.btn_aprobar_avance.setEnabled(True)
            self.btn_aprobar_avance.setText("Aprobar Avance")
        QMessageBox.critical(self, "Error al Aprobar", message)

    def on_image_downloaded(self, data):
        try:
            image = QImage()
            if image.loadFromData(data):
                pixmap = QPixmap.fromImage(image)
                # Scale pixmap to fit the container maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    self.image_container.width(),
                    self.image_container.height(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
            else:
                self.image_label.setText("Error al procesar la imagen.")
        except Exception as e:
            print(f"Error displaying image: {e}")
            self.image_label.setText("No se pudo mostrar la imagen.")


    def on_image_error(self, err_msg):
        print(f"Error downloading image: {err_msg}")
        self.image_label.setText("No se pudo cargar la imagen.")


# Alias para compatibilidad retroactiva (ya no se usa como ventana separada)
AvancesWindow = AvancesContent
