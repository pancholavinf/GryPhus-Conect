import os
import urllib.request
import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QSplitter, QTextEdit, QFrame, QGraphicsDropShadowEffect,
    QScrollArea, QMessageBox, QPushButton, QProgressBar, QFormLayout, QGroupBox
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
        self.filtered_items = []
        self.current_selected_item = None
        self.downloader = None
        self.item_adv_downloader = None
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
            "QPushButton { background: transparent; color: #262B29; border: none; "
            "font-size: 13px; font-weight: 600; padding: 4px 0px; } "
            "QPushButton:hover { color: #3D523C; }"
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
        self.title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #1F2421;")

        self.subtitle_label = QLabel("Visualización de estadísticas generales de progreso y bitácora detallada de avances.")
        self.subtitle_label.setStyleSheet("color: #262B29; font-size: 13px;")

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
        color_badge = "#2E6F40" if estado.lower() == "activa" else "#EF4444"
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
                border: 1px solid #D8D5CD;
                background-color: #FFFFFF;
                border-radius: 8px;
                padding: 10px;
            }
            QTabBar::tab {
                background-color: #F2EFE9;
                color: #262B29;
                border: 1px solid #D8D5CD;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
                margin-right: 4px;
            }
            QTabBar::tab:hover {
                background-color: #D8D5CD;
                color: #1F2421;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                color: #3D523C;
                border: 1px solid #D8D5CD;
                border-bottom: 2px solid #FFFFFF;
            }
        """)

        self.tab_stats = QWidget()
        self.tab_items = QWidget()
        self.tab_table = QWidget()
        self.tab_reportes = None
        self.tab_edp = None

        self.tab_reportes_dummy = QWidget()
        self.tab_edp_dummy = QWidget()

        self.setup_tab_stats()
        self.setup_tab_items()
        self.setup_tab_table()

        self.tabs.addTab(self.tab_stats, "Gráficos y Estadísticas")
        self.tabs.addTab(self.tab_items, "Ítems de Obra")
        self.tabs.addTab(self.tab_table, "Detalle de Avances")
        self.tabs.addTab(self.tab_reportes_dummy, "Reportes y Consumo")
        self.tabs.addTab(self.tab_edp_dummy, "Estados de Pago")

        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.main_layout.addWidget(self.tabs)

    def _on_tab_changed(self, index):
        if index == 3 and self.tab_reportes is None:
            self.tab_reportes = ReportesContent(supabase_client=self.supabase, fixed_obra_id=self.obra_data.get('id'))
            self.tabs.removeTab(3)
            self.tabs.insertTab(3, self.tab_reportes, "Reportes y Consumo")
            self.tabs.setCurrentIndex(3)
        elif index == 4 and self.tab_edp is None:
            self.tab_edp = EDPTab(
                supabase_client=self.supabase,
                obra_id=self.obra_data.get('id'),
                user_id=self.user_id
            )
            self.tabs.removeTab(4)
            self.tabs.insertTab(4, self.tab_edp, "Estados de Pago")
            self.tabs.setCurrentIndex(4)

    def setup_tab_items(self):
        tab_layout = QVBoxLayout(self.tab_items)
        tab_layout.setContentsMargins(10, 10, 10, 10)
        tab_layout.setSpacing(8)

        # ── Splitter Horizontal: Tabla con Filtros (Izquierda) / Detalle y Avances (Derecha) ──
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #D8D5CD; width: 2px; }")

        # 1. Panel Izquierdo: Barra de Filtros + Tabla de Ítems
        table_container = QWidget()
        table_vbox = QVBoxLayout(table_container)
        table_vbox.setContentsMargins(0, 0, 8, 0)
        table_vbox.setSpacing(8)

        # Barra de Filtros compacta encima de la tabla
        filters_widget = QWidget()
        filters_layout = QHBoxLayout(filters_widget)
        filters_layout.setContentsMargins(0, 0, 0, 0)
        filters_layout.setSpacing(8)

        self.items_search_input = QLineEdit()
        self.items_search_input.setPlaceholderText("🔍 Buscar por ubicación, plano, estructura, material, perfil...")
        self.items_search_input.textChanged.connect(self.aplicar_filtros_items)
        self.items_search_input.setStyleSheet("padding: 6px 10px; font-size: 12px; height: 30px;")
        filters_layout.addWidget(self.items_search_input, stretch=3)

        self.combo_filter_items_ubicacion = QComboBox()
        self.combo_filter_items_ubicacion.addItem("Todas las Ubicaciones")
        self.combo_filter_items_ubicacion.currentIndexChanged.connect(self.aplicar_filtros_items)
        self.combo_filter_items_ubicacion.setStyleSheet("padding: 4px 8px; font-size: 12px; height: 30px;")
        filters_layout.addWidget(self.combo_filter_items_ubicacion, stretch=2)

        self.combo_filter_items_status = QComboBox()
        self.combo_filter_items_status.addItems([
            "Todos los Estados",
            "Completados (100%)",
            "En Progreso (1-99%)",
            "Sin Iniciar (0%)",
            "Excedidos (>100%)"
        ])
        self.combo_filter_items_status.currentIndexChanged.connect(self.aplicar_filtros_items)
        self.combo_filter_items_status.setStyleSheet("padding: 4px 8px; font-size: 12px; height: 30px;")
        filters_layout.addWidget(self.combo_filter_items_status, stretch=2)

        self.lbl_items_counter = QLabel("0 ítems")
        self.lbl_items_counter.setStyleSheet("font-size: 12px; font-weight: bold; color: #4A524E; padding-left: 4px;")
        filters_layout.addWidget(self.lbl_items_counter)

        table_vbox.addWidget(filters_widget)

        # Tabla de Ítems
        self.table_items = QTableWidget()
        self.table_items.verticalHeader().setDefaultSectionSize(38)
        self.table_items.verticalHeader().setVisible(False)
        self.table_items.horizontalHeader().setMinimumSectionSize(80)
        self.table_items.setColumnCount(10)
        self.table_items.setHorizontalHeaderLabels([
            "#", "Ubicación", "Plano", "Estructura", "Material",
            "Contrato (m²)", "Aprobado (m²)", "Pendiente (m²)", "Progreso", "Estado"
        ])
        self.table_items.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_items.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # #
        self.table_items.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)      # Ubicacion
        self.table_items.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Plano
        self.table_items.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)      # Estructura
        self.table_items.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)          # Material
        self.table_items.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents) # Contrato
        self.table_items.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents) # Aprobado
        self.table_items.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents) # Pendiente
        self.table_items.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents) # Progreso
        self.table_items.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents) # Estado
        self.table_items.setAlternatingRowColors(True)
        self.table_items.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_items.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_items.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_items.itemSelectionChanged.connect(self.on_item_row_selected)

        table_vbox.addWidget(self.table_items)
        splitter.addWidget(table_container)

        # 2. Panel Lateral Derecho: Detalle del Ítem y Lista de Avances
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setMinimumWidth(340)
        right_scroll.setMaximumWidth(460)
        right_scroll.setStyleSheet("QScrollArea { background-color: #FAF8F5; color: #1F2421; border: 1px solid #D8D5CD; border-radius: 8px; }")

        right_container = QWidget()
        right_container.setStyleSheet("background-color: #FAF8F5;")
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(10)

        # Encabezado del Ítem
        item_header_frame = QFrame()
        item_header_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #D8D5CD; border-radius: 8px;")
        item_header_layout = QVBoxLayout(item_header_frame)
        item_header_layout.setContentsMargins(10, 8, 10, 8)
        item_header_layout.setSpacing(3)

        self.lbl_item_detail_title = QLabel("Seleccione un Ítem")
        self.lbl_item_detail_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #1F2421; font-family: 'Space Grotesk', 'Work Sans', sans-serif;")
        self.lbl_item_detail_title.setWordWrap(True)

        self.lbl_item_detail_sub = QLabel("Haga clic en una fila para ver sus cubicaciones y avances")
        self.lbl_item_detail_sub.setStyleSheet("font-size: 11px; color: #64748B; font-weight: 500;")
        self.lbl_item_detail_sub.setWordWrap(True)

        item_header_layout.addWidget(self.lbl_item_detail_title)
        item_header_layout.addWidget(self.lbl_item_detail_sub)
        right_layout.addWidget(item_header_frame)

        # Caja de Ficha Técnica del Ítem
        self.item_tech_box = QFrame()
        self.item_tech_box.setStyleSheet("background-color: #FFFFFF; border: 1px solid #D8D5CD; border-radius: 8px;")
        tech_layout = QFormLayout(self.item_tech_box)
        tech_layout.setContentsMargins(10, 8, 10, 8)
        tech_layout.setVerticalSpacing(5)
        tech_layout.setHorizontalSpacing(10)

        self.lbl_item_tech_perfil = QLabel("-")
        self.lbl_item_tech_dim = QLabel("-")
        self.lbl_item_tech_fuego = QLabel("-")
        self.lbl_item_tech_micras = QLabel("-")
        self.lbl_item_tech_precio = QLabel("-")
        self.lbl_item_tech_total_val = QLabel("-")

        for lbl in [self.lbl_item_tech_perfil, self.lbl_item_tech_dim, self.lbl_item_tech_fuego, self.lbl_item_tech_micras, self.lbl_item_tech_precio, self.lbl_item_tech_total_val]:
            lbl.setStyleSheet("font-size: 11px; color: #1F2421; font-weight: 600;")

        tech_layout.addRow("Perfil / Tipo:", self.lbl_item_tech_perfil)
        tech_layout.addRow("Dimensión:", self.lbl_item_tech_dim)
        tech_layout.addRow("Resistencia Fuego:", self.lbl_item_tech_fuego)
        tech_layout.addRow("Espesor Teórico:", self.lbl_item_tech_micras)
        tech_layout.addRow("Precio Contrato ($/m²):", self.lbl_item_tech_precio)
        tech_layout.addRow("Monto Total Contrato:", self.lbl_item_tech_total_val)
        right_layout.addWidget(self.item_tech_box)

        # Barra de Progreso del Ítem
        progress_card = QFrame()
        progress_card.setStyleSheet("background-color: #FFFFFF; border: 1px solid #D8D5CD; border-radius: 8px;")
        progress_card_layout = QVBoxLayout(progress_card)
        progress_card_layout.setContentsMargins(10, 8, 10, 8)
        progress_card_layout.setSpacing(5)

        prog_head = QHBoxLayout()
        prog_title = QLabel("Progreso de Ejecución")
        prog_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #262B29;")
        self.lbl_item_kpi_pct = QLabel("0.0%")
        self.lbl_item_kpi_pct.setStyleSheet("font-size: 14px; font-weight: 800; color: #3D523C; font-family: 'Space Grotesk', 'Work Sans';")
        prog_head.addWidget(prog_title)
        prog_head.addStretch()
        prog_head.addWidget(self.lbl_item_kpi_pct)
        progress_card_layout.addLayout(prog_head)

        self.item_progress_bar = QProgressBar()
        self.item_progress_bar.setRange(0, 100)
        self.item_progress_bar.setValue(0)
        self.item_progress_bar.setFixedHeight(6)
        self.item_progress_bar.setTextVisible(False)
        self.item_progress_bar.setStyleSheet("""
            QProgressBar { border: none; background-color: #D8D5CD; border-radius: 3px; }
            QProgressBar::chunk { background-color: #2E6F40; border-radius: 3px; }
        """)
        progress_card_layout.addWidget(self.item_progress_bar)

        kpis_row = QHBoxLayout()
        self.lbl_item_kpi_contratado = QLabel("Contrato: 0 m²")
        self.lbl_item_kpi_aprobado = QLabel("Aprobado: 0 m²")
        self.lbl_item_kpi_pendiente = QLabel("Pendiente: 0 m²")
        for k_lbl, col in [(self.lbl_item_kpi_contratado, "#262B29"), (self.lbl_item_kpi_aprobado, "#2E6F40"), (self.lbl_item_kpi_pendiente, "#B85A3A")]:
            k_lbl.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {col};")
            kpis_row.addWidget(k_lbl)
        kpis_row.addStretch()
        progress_card_layout.addLayout(kpis_row)

        right_layout.addWidget(progress_card)

        # Sección de Avances del Ítem
        adv_group = QGroupBox("Avances Registrados de este Ítem")
        adv_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold; font-size: 12px; color: #1F2421;
                border: 1px solid #D8D5CD; border-radius: 8px;
                margin-top: 8px; padding-top: 14px; padding-bottom: 6px;
                background-color: #FFFFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin; subcontrol-position: top left;
                padding: 0 8px; left: 10px; color: #262B29;
            }
        """)
        adv_layout = QVBoxLayout(adv_group)
        adv_layout.setContentsMargins(6, 6, 6, 6)
        adv_layout.setSpacing(6)

        self.table_item_advances = QTableWidget()
        self.table_item_advances.verticalHeader().setDefaultSectionSize(30)
        self.table_item_advances.verticalHeader().setVisible(False)
        self.table_item_advances.setColumnCount(5)
        self.table_item_advances.setHorizontalHeaderLabels(["Fecha", "Supervisor", "m²", "Estado", "Evidencia"])
        self.table_item_advances.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_item_advances.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_item_advances.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_item_advances.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_item_advances.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table_item_advances.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table_item_advances.setAlternatingRowColors(True)
        self.table_item_advances.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_item_advances.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_item_advances.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_item_advances.setMinimumHeight(130)
        self.table_item_advances.itemSelectionChanged.connect(self.on_item_advance_selected)
        adv_layout.addWidget(self.table_item_advances)

        self.lbl_no_item_advances = QLabel("No hay avances registrados para este ítem.")
        self.lbl_no_item_advances.setStyleSheet("color: #64748B; font-size: 11px; padding: 8px; font-style: italic;")
        self.lbl_no_item_advances.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_no_item_advances.setVisible(False)
        adv_layout.addWidget(self.lbl_no_item_advances)

        # Caja de Vista Previa de Evidencia de Avance
        self.item_adv_preview_box = QFrame()
        self.item_adv_preview_box.setStyleSheet("background-color: #FAF8F5; border: 1px solid #D8D5CD; border-radius: 6px;")
        prev_layout = QVBoxLayout(self.item_adv_preview_box)
        prev_layout.setContentsMargins(6, 6, 6, 6)
        prev_layout.setSpacing(4)

        self.lbl_item_adv_comment = QLabel("Comentario: -")
        self.lbl_item_adv_comment.setStyleSheet("font-size: 11px; color: #334155;")
        self.lbl_item_adv_comment.setWordWrap(True)
        prev_layout.addWidget(self.lbl_item_adv_comment)

        self.lbl_item_adv_image = QLabel("Seleccione un avance arriba para ver la foto")
        self.lbl_item_adv_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_item_adv_image.setFixedHeight(140)
        self.lbl_item_adv_image.setStyleSheet("background-color: #D8D5CD; border-radius: 4px; color: #64748B; font-size: 10px;")
        prev_layout.addWidget(self.lbl_item_adv_image)

        adv_layout.addWidget(self.item_adv_preview_box)
        right_layout.addWidget(adv_group)

        right_layout.addStretch()

        right_scroll.setWidget(right_container)
        splitter.addWidget(right_scroll)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([780, 360])
        tab_layout.addWidget(splitter)

    # ── MÉTODOS DE LA PESTAÑA ÍTEMS DE OBRA ──

    def aplicar_filtros_items(self):
        search = self.items_search_input.text().strip().lower()
        ubicacion_filtro = self.combo_filter_items_ubicacion.currentText()
        status_filtro = self.combo_filter_items_status.currentText()

        self.filtered_items = []
        for item in self.items:
            ubicacion = str(item.get("ubicacion") or "").lower()
            plano = str(item.get("plano") or "").lower()
            estructura = str(item.get("estructura") or "").lower()
            material = str(item.get("material") or "").lower()
            perfil = str(item.get("perfil") or "").lower()
            desc_plano = str(item.get("descripcion_plano") or "").lower()

            # Texto libre
            match_search = (
                not search
                or (search in ubicacion)
                or (search in plano)
                or (search in estructura)
                or (search in material)
                or (search in perfil)
                or (search in desc_plano)
            )
            if not match_search:
                continue

            # Filtro Ubicación
            if ubicacion_filtro != "Todas las Ubicaciones" and item.get("ubicacion") != ubicacion_filtro:
                continue

            # Cálculo de avance del ítem
            item_id = item.get("id")
            cant_contratada = float(item.get("area_expuesta_m2") or item.get("cantidad") or 0.0)
            item_avances = [av for av in self.avances if av.get("item_obra_id") == item_id]
            cant_aprobada = sum(float(av.get("cantidad") or 0.0) for av in item_avances if str(av.get("estado_revision") or "").lower() == "aprobado")
            cant_pendiente = sum(float(av.get("cantidad") or 0.0) for av in item_avances if str(av.get("estado_revision") or "").lower() == "pendiente")
            pct = (cant_aprobada / cant_contratada * 100.0) if cant_contratada > 0 else 0.0

            # Filtro Estado
            if status_filtro == "Completados (100%)" and (pct < 100.0 or pct > 100.05):
                continue
            elif status_filtro == "En Progreso (1-99%)" and (pct <= 0.0 or pct >= 100.0):
                continue
            elif status_filtro == "Sin Iniciar (0%)" and (pct > 0.0 or cant_pendiente > 0):
                continue
            elif status_filtro == "Excedidos (>100%)" and pct <= 100.05:
                continue

            self.filtered_items.append((item, cant_contratada, cant_aprobada, cant_pendiente, pct))

        self.poblar_tabla_items()

    def poblar_tabla_items(self):
        self.table_items.blockSignals(True)
        self.table_items.setRowCount(len(self.filtered_items))
        self.lbl_items_counter.setText(f"{len(self.filtered_items)} de {len(self.items)} ítems")

        for idx, (item, cant_contratada, cant_aprobada, cant_pendiente, pct) in enumerate(self.filtered_items):
            # 0: #
            it_num = QTableWidgetItem(str(idx + 1))
            it_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_num.setData(Qt.ItemDataRole.UserRole, item)
            self.table_items.setItem(idx, 0, it_num)

            # 1: Ubicación
            self.table_items.setItem(idx, 1, QTableWidgetItem(str(item.get("ubicacion") or "-")))
            # 2: Plano
            self.table_items.setItem(idx, 2, QTableWidgetItem(str(item.get("plano") or "-")))
            # 3: Estructura
            self.table_items.setItem(idx, 3, QTableWidgetItem(str(item.get("estructura") or "-")))
            # 4: Material
            self.table_items.setItem(idx, 4, QTableWidgetItem(str(item.get("material") or "-")))

            # 5: Contrato m2
            it_cont = QTableWidgetItem(f"{cant_contratada:,.2f}")
            it_cont.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_items.setItem(idx, 5, it_cont)

            # 6: Aprobado m2
            it_apr = QTableWidgetItem(f"{cant_aprobada:,.2f}")
            it_apr.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if cant_aprobada > 0:
                it_apr.setForeground(QColor("#2E6F40"))
            self.table_items.setItem(idx, 6, it_apr)

            # 7: Pendiente m2
            it_pend = QTableWidgetItem(f"{cant_pendiente:,.2f}")
            it_pend.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if cant_pendiente > 0:
                it_pend.setForeground(QColor("#B85A3A"))
            self.table_items.setItem(idx, 7, it_pend)

            # 8: Progreso %
            it_prog = QTableWidgetItem(f"{pct:.1f}%")
            it_prog.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_items.setItem(idx, 8, it_prog)

            # 9: Estado Badge
            status_lbl = QLabel()
            status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if pct >= 100.0 and pct <= 100.05:
                status_lbl.setText("Completado")
                status_lbl.setStyleSheet("color: #2F402E; font-weight: bold; background-color: #D1FAE5; border-radius: 4px; font-size: 11px; padding: 2px;")
            elif pct > 100.05:
                status_lbl.setText("Excedido")
                status_lbl.setStyleSheet("color: #2F402E; font-weight: bold; background-color: #DBEAFE; border-radius: 4px; font-size: 11px; padding: 2px;")
            elif pct > 0:
                status_lbl.setText("En Progreso")
                status_lbl.setStyleSheet("color: #B85A3A; font-weight: bold; background-color: #FEF3C7; border-radius: 4px; font-size: 11px; padding: 2px;")
            elif cant_pendiente > 0:
                status_lbl.setText("En Revisión")
                status_lbl.setStyleSheet("color: #9333EA; font-weight: bold; background-color: #F3E8FF; border-radius: 4px; font-size: 11px; padding: 2px;")
            else:
                status_lbl.setText("Sin Iniciar")
                status_lbl.setStyleSheet("color: #64748B; font-weight: bold; background-color: #F1F5F9; border-radius: 4px; font-size: 11px; padding: 2px;")

            self.table_items.setCellWidget(idx, 9, status_lbl)

        self.table_items.blockSignals(False)

        # Si hay filas, seleccionar la primera por defecto
        if self.filtered_items:
            self.table_items.selectRow(0)
        else:
            self.limpiar_detalle_item()

    def on_item_row_selected(self):
        ranges = self.table_items.selectedRanges()
        if not ranges:
            return
        row = ranges[0].topRow()
        if row < 0 or row >= len(self.filtered_items):
            return

        item_tuple = self.filtered_items[row]
        item, cant_contratada, cant_aprobada, cant_pendiente, pct = item_tuple
        self.mostrar_detalle_item(item, cant_contratada, cant_aprobada, cant_pendiente, pct)

    def mostrar_detalle_item(self, item, cant_contratada, cant_aprobada, cant_pendiente, pct):
        self.current_selected_item = item

        est = item.get("estructura") or "Elemento"
        ubic = item.get("ubicacion") or "Sin Ubicación"
        plano = item.get("plano") or "-"
        mat = item.get("material") or "-"

        self.lbl_item_detail_title.setText(f"{est} • {ubic}")
        self.lbl_item_detail_sub.setText(f"Plano: {plano} | Recubrimiento: {mat}")

        self.lbl_item_tech_perfil.setText(str(item.get("perfil") or "-"))
        self.lbl_item_tech_dim.setText(str(item.get("dimension") or "-"))
        self.lbl_item_tech_fuego.setText(str(item.get("resist_fuego") or "-"))
        self.lbl_item_tech_micras.setText(f"{item.get('micras')} µm" if item.get("micras") else "-")

        pu = float(item.get("precio_unitario_contrato") or 0.0)
        self.lbl_item_tech_precio.setText(f"$ {pu:,.0f}".replace(",", "."))
        self.lbl_item_tech_total_val.setText(f"$ {pu * cant_contratada:,.0f}".replace(",", "."))

        # KPIs y Barra de Progreso
        self.lbl_item_kpi_pct.setText(f"{pct:.1f}%")
        self.item_progress_bar.setValue(min(100, int(pct)))
        if pct >= 100:
            self.item_progress_bar.setStyleSheet("""
                QProgressBar { border: none; background-color: #D8D5CD; border-radius: 4px; }
                QProgressBar::chunk { background-color: #2E6F40; border-radius: 4px; }
            """)
        elif pct > 0:
            self.item_progress_bar.setStyleSheet("""
                QProgressBar { border: none; background-color: #D8D5CD; border-radius: 4px; }
                QProgressBar::chunk { background-color: #3D523C; border-radius: 4px; }
            """)
        else:
            self.item_progress_bar.setStyleSheet("""
                QProgressBar { border: none; background-color: #D8D5CD; border-radius: 4px; }
                QProgressBar::chunk { background-color: #94A3B8; border-radius: 4px; }
            """)

        self.lbl_item_kpi_contratado.setText(f"Contrato: {cant_contratada:,.2f} m²")
        self.lbl_item_kpi_aprobado.setText(f"Aprobado: {cant_aprobada:,.2f} m²")
        self.lbl_item_kpi_pendiente.setText(f"Pendiente: {cant_pendiente:,.2f} m²")

        # Cargar avances del ítem
        item_id = item.get("id")
        item_avances = [av for av in self.avances if av.get("item_obra_id") == item_id]
        item_avances = sorted(item_avances, key=lambda x: x.get("fecha_captura_local") or "", reverse=True)
        self.current_item_avances = item_avances

        self.table_item_advances.blockSignals(True)
        self.table_item_advances.setRowCount(len(item_avances))

        if not item_avances:
            self.table_item_advances.setVisible(False)
            self.lbl_no_item_advances.setVisible(True)
            self.item_adv_preview_box.setVisible(False)
        else:
            self.table_item_advances.setVisible(True)
            self.lbl_no_item_advances.setVisible(False)
            self.item_adv_preview_box.setVisible(True)

            for a_idx, av in enumerate(item_avances):
                # Fecha
                f_raw = (av.get("fecha_captura_local") or "").replace("T", " ")[:16]
                it_f = QTableWidgetItem(f_raw)
                it_f.setData(Qt.ItemDataRole.UserRole, av)
                self.table_item_advances.setItem(a_idx, 0, it_f)

                # Supervisor
                self.table_item_advances.setItem(a_idx, 1, QTableWidgetItem(str(av.get("jefe_nombre") or "Desconocido")))

                # Cantidad m2
                q_av = float(av.get("cantidad") or 0.0)
                it_q = QTableWidgetItem(f"{q_av:,.2f}")
                it_q.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table_item_advances.setItem(a_idx, 2, it_q)

                # Estado Badge
                st_av = str(av.get("estado_revision") or "pendiente").capitalize()
                st_lbl = QLabel(st_av)
                st_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                if st_av.lower() == "aprobado":
                    st_lbl.setStyleSheet("color: #2F402E; font-weight: bold; background-color: #D1FAE5; border-radius: 3px; font-size: 10px; padding: 1px;")
                elif st_av.lower() == "pendiente":
                    st_lbl.setStyleSheet("color: #B85A3A; font-weight: bold; background-color: #FEF3C7; border-radius: 3px; font-size: 10px; padding: 1px;")
                else:
                    st_lbl.setStyleSheet("color: #DC2626; font-weight: bold; background-color: #FEE2E2; border-radius: 3px; font-size: 10px; padding: 1px;")
                self.table_item_advances.setCellWidget(a_idx, 3, st_lbl)

                # Evidencia / Foto
                has_foto = bool(av.get("foto_url"))
                btn_foto = QPushButton("📷 Foto" if has_foto else "Sin foto")
                btn_foto.setEnabled(has_foto)
                btn_foto.setStyleSheet("""
                    QPushButton { background-color: #FFFFFF; color: #0369A1; border: 1px solid #BAE6FD; border-radius: 3px; font-size: 11px; padding: 2px 6px; }
                    QPushButton:hover { background-color: #E0F2FE; }
                    QPushButton:disabled { color: #94A3B8; border-color: #D8D5CD; background: #FAF8F5; }
                """)
                if has_foto:
                    btn_foto.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn_foto.clicked.connect(lambda ch, a=av: self.on_item_advance_foto_clicked(a))
                self.table_item_advances.setCellWidget(a_idx, 4, btn_foto)

            self.table_item_advances.selectRow(0)

        self.table_item_advances.blockSignals(False)

    def on_item_advance_selected(self):
        ranges = self.table_item_advances.selectedRanges()
        if not ranges or not hasattr(self, 'current_item_avances'):
            return
        row = ranges[0].topRow()
        if row < 0 or row >= len(self.current_item_avances):
            return

        av = self.current_item_avances[row]
        com = av.get("comentario") or "Sin comentario registrado."
        self.lbl_item_adv_comment.setText(f"<b>Comentario:</b> {com}")

        foto_url = av.get("foto_url")
        if foto_url:
            self.lbl_item_adv_image.setText("Cargando evidencia...")
            self.item_adv_downloader = ImageDownloader(foto_url)
            self.item_adv_downloader.finished.connect(self._on_item_adv_image_loaded)
            self.item_adv_downloader.error.connect(lambda e: self.lbl_item_adv_image.setText("No se pudo cargar la imagen"))
            self.item_adv_downloader.start()
        else:
            self.lbl_item_adv_image.setPixmap(QPixmap())
            self.lbl_item_adv_image.setText("Sin foto adjunta")

    def _on_item_adv_image_loaded(self, data):
        try:
            image = QImage()
            if image.loadFromData(data):
                pix = QPixmap.fromImage(image)
                scaled = pix.scaled(
                    self.lbl_item_adv_image.width(),
                    self.lbl_item_adv_image.height(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.lbl_item_adv_image.setPixmap(scaled)
            else:
                self.lbl_item_adv_image.setText("Error al procesar foto")
        except Exception:
            self.lbl_item_adv_image.setText("Error al renderizar foto")

    def on_item_advance_foto_clicked(self, avance):
        foto_url = avance.get("foto_url")
        if not foto_url:
            return
        from src.ui.document_viewer import DocumentViewerDialog
        dlg = DocumentViewerDialog(self, url_or_path=foto_url, title="Evidencia Fotográfica de Avance")
        dlg.exec()

    def limpiar_detalle_item(self):
        self.lbl_item_detail_title.setText("Seleccione un Ítem")
        self.lbl_item_detail_sub.setText("Haga clic en una fila para ver sus cubicaciones y avances")
        self.lbl_item_tech_perfil.setText("-")
        self.lbl_item_tech_dim.setText("-")
        self.lbl_item_tech_fuego.setText("-")
        self.lbl_item_tech_micras.setText("-")
        self.lbl_item_tech_precio.setText("-")
        self.lbl_item_tech_total_val.setText("-")
        self.item_progress_bar.setValue(0)
        self.lbl_item_kpi_pct.setText("0.0%")
        self.lbl_item_kpi_contratado.setText("Contrato: 0 m²")
        self.lbl_item_kpi_aprobado.setText("Aprobado: 0 m²")
        self.lbl_item_kpi_pendiente.setText("Pendiente: 0 m²")
        self.table_item_advances.setRowCount(0)
        self.table_item_advances.setVisible(False)
        self.lbl_no_item_advances.setVisible(True)
        self.item_adv_preview_box.setVisible(False)

    def setup_tab_stats(self):
        stats_layout = QVBoxLayout(self.tab_stats)
        stats_layout.setContentsMargins(10, 10, 10, 10)
        stats_layout.setSpacing(15)

        # KPI Summary Row
        kpi_widget = QWidget()
        kpi_layout = QHBoxLayout(kpi_widget)
        kpi_layout.setContentsMargins(0, 0, 0, 0)
        kpi_layout.setSpacing(15)

        self.kpi_contratado = self.create_kpi_card("Presupuesto Contratado", "$0", "#262B29")
        self.kpi_ejecutado = self.create_kpi_card("Ejecutado (Aprobado)", "$0", "#2E6F40")
        self.kpi_pendiente = self.create_kpi_card("Pendiente de Aprobación", "$0", "#B85A3A")
        self.kpi_progreso = self.create_kpi_card("Progreso General", "0.0%", "#3D523C")

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
        c1_card.setStyleSheet("background-color: #FFFFFF; color: #1F2421; border: 1px solid #D8D5CD; border-radius: 8px;")
        c1_layout = QVBoxLayout(c1_card)
        c1_layout.addWidget(QLabel("<b>Progreso Temporal Acumulado</b>", styleSheet="font-size: 14px; color: #262B29;"))
        self.canvas_time = MplCanvas(parent=c1_card, width=5, height=3)
        c1_layout.addWidget(self.canvas_time)
        row1_layout.addWidget(c1_card, stretch=1)

        # Chart 2 Container Card (with Switcher for Location / Structure + Chart Style Toggle)
        c2_card = QFrame()
        c2_card.setStyleSheet("background-color: #FFFFFF; color: #1F2421; border: 1px solid #D8D5CD; border-radius: 8px;")
        c2_layout = QVBoxLayout(c2_card)
        c2_header = QWidget()
        c2_header_layout = QHBoxLayout(c2_header)
        c2_header_layout.setContentsMargins(0, 0, 0, 0)
        c2_header_layout.addWidget(QLabel("<b>Avance por Categoría</b>", styleSheet="font-size: 14px; color: #262B29;"))
        c2_header_layout.addStretch()

        self.btn_toggle_style = QPushButton("Vista: Agrupado")
        self.btn_toggle_style.setFixedHeight(26)
        self.btn_toggle_style.setStyleSheet(
            "QPushButton { padding: 2px 10px; font-size: 11px; background-color: #F2EFE9; "
            "color: #3D523C; border: 1px solid #A5B4FC; border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background-color: #C7D2FE; color: #3D523C; }"
        )
        self.btn_toggle_style.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_style.clicked.connect(self.toggle_chart_style)
        c2_header_layout.addWidget(self.btn_toggle_style)

        c2_header_layout.addSpacing(6)

        self.combo_group_by = QComboBox()
        self.combo_group_by.addItems(["Ubicación", "Estructura", "Material"])
        self.combo_group_by.currentIndexChanged.connect(self.actualizar_grafico_avance_categoria)
        self.combo_group_by.setStyleSheet("padding: 4px 8px; font-size: 12px; height: 26px; color: #1F2421; background-color: #FFFFFF;")
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
        c3_card.setStyleSheet("background-color: #FFFFFF; color: #1F2421; border: 1px solid #D8D5CD; border-radius: 8px;")
        c3_layout = QVBoxLayout(c3_card)
        c3_layout.addWidget(QLabel("<b>Distribución de Avances por Estado</b>", styleSheet="font-size: 14px; color: #262B29;"))
        self.canvas_status = MplCanvas(parent=c3_card, width=5, height=3)
        c3_layout.addWidget(self.canvas_status)
        row2_layout.addWidget(c3_card, stretch=1)

        # Chart 4 Container Card
        c4_card = QFrame()
        c4_card.setStyleSheet("background-color: #FFFFFF; color: #1F2421; border: 1px solid #D8D5CD; border-radius: 8px;")
        c4_layout = QVBoxLayout(c4_card)
        c4_layout.addWidget(QLabel("<b>Comparación Económica Presupuestaria</b>", styleSheet="font-size: 14px; color: #262B29;"))
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
                color: #1F2421;
                border: 1px solid #D8D5CD;
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
        t_lbl.setStyleSheet("color: #262B29; font-size: 11px; font-weight: bold; text-transform: uppercase;")
        
        v_lbl = QLabel(val)
        v_lbl.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold; font-family: 'Space Grotesk', 'Work Sans';")
        
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
            "QPushButton { background-color: #2E6F40; color: #FFFFFF; font-weight: bold; border: none; border-radius: 6px; padding: 6px 14px; font-size: 13px; height: 32px; } "
            "QPushButton:hover { background-color: #3D523C; } "
            "QPushButton:disabled { background-color: #D8D5CD; color: #262B29; }"
        )
        self.btn_aprobar_todos.clicked.connect(self.aprobar_todos_avances)
        filters_layout.addWidget(self.btn_aprobar_todos)

        tab_layout.addWidget(filters_widget)

        # Splitter for Table and Details Sidebar
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #D8D5CD; width: 2px; }")

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
        self.sidebar_detail.setStyleSheet("QFrame { background-color: #FAF8F5; color: #1F2421; border: 1px solid #D8D5CD; border-radius: 8px; }")

        sidebar_layout = QVBoxLayout(self.sidebar_detail)
        sidebar_layout.setContentsMargins(16, 16, 16, 16)
        sidebar_layout.setSpacing(12)

        sidebar_title = QLabel("Detalle del Avance")
        sidebar_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #262B29;")
        sidebar_layout.addWidget(sidebar_title)

        # Image Display Box
        self.image_container = QFrame()
        self.image_container.setFixedHeight(220)
        self.image_container.setStyleSheet("background-color: #D8D5CD; color: #1F2421; border-radius: 6px; border: 1px solid #D8D5CD;")
        
        img_container_layout = QVBoxLayout(self.image_container)
        img_container_layout.setContentsMargins(5, 5, 5, 5)
        
        self.image_label = QLabel("Seleccione un avance\npara ver la foto")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("color: #262B29; font-size: 13px; font-weight: 500;")
        img_container_layout.addWidget(self.image_label)
        
        sidebar_layout.addWidget(self.image_container)

        # Comment Text Area
        sidebar_layout.addWidget(QLabel("<b>Comentario del Supervisor:</b>", styleSheet="font-size: 12px; color: #262B29;"))
        self.comment_display = QTextEdit()
        self.comment_display.setReadOnly(True)
        self.comment_display.setPlaceholderText("Sin comentarios disponibles.")
        self.comment_display.setStyleSheet("background-color: #FFFFFF; color: #1F2421; border: 1px solid #D8D5CD; border-radius: 6px; padding: 8px;")
        self.comment_display.setFixedHeight(90)
        sidebar_layout.addWidget(self.comment_display)

        # Metadata Details Box
        self.meta_box = QFrame()
        self.meta_box.setStyleSheet("background-color: #FFFFFF; color: #1F2421; border: 1px solid #D8D5CD; border-radius: 6px;")
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
        self.action_box.setStyleSheet("background-color: #FFFFFF; color: #1F2421; border: 1px solid #D8D5CD; border-radius: 6px;")
        action_layout = QVBoxLayout(self.action_box)
        action_layout.setContentsMargins(10, 10, 10, 10)

        self.btn_aprobar_avance = QPushButton("Aprobar Avance")
        self.btn_aprobar_avance.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_aprobar_avance.setEnabled(False)
        self.btn_aprobar_avance.setStyleSheet(
            "QPushButton { background-color: #3D523C; color: #FFFFFF; font-weight: bold; border: none; border-radius: 6px; padding: 10px 14px; font-size: 13px; } "
            "QPushButton:hover { background-color: #476386; } "
            "QPushButton:disabled { background-color: #D8D5CD; color: #262B29; }"
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

            # Populate location filter combo in items tab
            locations = sorted(list(set(str(it.get("ubicacion") or "").strip() for it in self.items if it.get("ubicacion"))))
            self.combo_filter_items_ubicacion.blockSignals(True)
            self.combo_filter_items_ubicacion.clear()
            self.combo_filter_items_ubicacion.addItem("Todas las Ubicaciones")
            self.combo_filter_items_ubicacion.addItems(locations)
            self.combo_filter_items_ubicacion.blockSignals(False)

            # Apply initial filtering
            self.aplicar_filtros()
            self.aplicar_filtros_items()

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
            self.canvas_time.axes.plot(dates_app, pcts_app, marker='o', color='#3D523C', linewidth=2,
                                       label="Avance Aprobado")
            self.canvas_time.axes.fill_between(dates_app, pcts_app, color='#3D523C', alpha=0.15)

        if dates_all or dates_app:
            self.canvas_time.axes.set_ylabel("% del Presupuesto", fontsize=10)
            self.canvas_time.axes.grid(True, linestyle='--', alpha=0.4)
            self.canvas_time.axes.set_ylim(-5, 105)
            self.canvas_time.axes.legend(fontsize=8, loc='upper left')
            self.canvas_time.fig.autofmt_xdate()
        else:
            self.canvas_time.axes.text(0.5, 0.5, "No hay avances registrados\npara graficar el progreso temporal",
                                       ha='center', va='center', color='#262B29')
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
            "Aprobado": "#2E6F40",
            "Pendiente": "#B85A3A",
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
                                        ha='center', va='center', color='#262B29')
            self.canvas_status.axes.set_axis_off()

        self.canvas_status.draw()

        # 4. Financial Budget Chart (Bar)
        self.canvas_financial.axes.clear()
        categories = ["Contratado", "Aprobado", "Pendiente"]
        values = [total_budget, executed_approved, executed_pending]
        colors = ["#262B29", "#3D523C", "#B85A3A"]

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
            "aprobado":  "#2E6F40",
            "pendiente": "#B85A3A",
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
                ha='center', va='center', color='#262B29'
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
                status_widget.setStyleSheet("color: #2F402E; font-weight: bold; background-color: #D1FAE5; border: 1px solid #2E6F40; border-radius: 4px; padding: 2px;")
            else:
                status_widget = QLabel(status)
                status_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
                if status.lower() == "aprobado":
                    status_widget.setStyleSheet("color: #2E6F40; font-weight: bold; background-color: #D1FAE5; border-radius: 4px; padding: 2px;")
                elif status.lower() == "pendiente":
                    status_widget.setStyleSheet("color: #B85A3A; font-weight: bold; background-color: #FEF3C7; border-radius: 4px; padding: 2px;")
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
                "QPushButton { background-color: #3D523C; color: #FFFFFF; font-weight: bold; border: none; border-radius: 6px; padding: 10px 14px; font-size: 13px; } "
                "QPushButton:disabled { background-color: #D8D5CD; color: #262B29; }"
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
                self.lbl_meta_edp.setText(f"<b>Estado de Pago:</b> <font color='#2F402E'><b>EDP N° {edp_num}</b></font> ({f_edp})")
            else:
                self.lbl_meta_edp.setText("<b>Estado de Pago:</b> <font color='#262B29'>Pendiente de cobro (Sin asignar)</font>")
            
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
                    "QPushButton { background-color: #D1FAE5; color: #2F402E; font-weight: bold; border: 1px solid #2E6F40; border-radius: 6px; padding: 10px 14px; font-size: 13px; }"
                )
            else:
                self.btn_aprobar_avance.setText("Aprobar Avance")
                self.btn_aprobar_avance.setEnabled(True)
                self.btn_aprobar_avance.setStyleSheet(
                    "QPushButton { background-color: #3D523C; color: #FFFFFF; font-weight: bold; border: none; border-radius: 6px; padding: 10px 14px; font-size: 13px; } "
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
        self.aplicar_filtros_items()
        self.btn_aprobar_avance.setText("Avance Aprobado")
        self.btn_aprobar_avance.setEnabled(False)
        self.btn_aprobar_avance.setStyleSheet(
            "QPushButton { background-color: #D1FAE5; color: #2F402E; font-weight: bold; border: 1px solid #2E6F40; border-radius: 6px; padding: 10px 14px; font-size: 13px; }"
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
        self.aplicar_filtros_items()

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
