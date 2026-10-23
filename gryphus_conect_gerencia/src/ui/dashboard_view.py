from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QFrame, QHBoxLayout, 
    QMessageBox, QGraphicsDropShadowEffect, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor
from src.core.workers import FetchDashboardDataWorker, FetchDashboardAsistenciaWorker

class ClickableObraCard(QFrame):
    clicked = pyqtSignal(dict)

    def __init__(self, obra, nombres_jefes=None, parent=None):
        super().__init__(parent)
        self.obra = obra
        self.nombres_jefes = nombres_jefes or []
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.init_ui()

    def init_ui(self):
        # Base Card Container Styling (Pure White with shadow and rounded corners)
        self.setStyleSheet("""
            ClickableObraCard {
                background-color: #FFFFFF;
                border: 1px solid #4A524E;
                border-radius: 12px;
            }
            ClickableObraCard:hover {
                border: 2px solid #3D523C;
                background-color: #FFFFFF;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setColor(QColor(69, 107, 109, 30))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        color_obra = self.obra.get("color") or "#3D523C"
        nombre_obra = self.obra.get("nombre", "Sin Nombre")
        estado_obra = self.obra.get("estado", "Activa")

        # 1. Top Banner Accent Bar (Elegante cabecera superior sin franjas extrañas)
        top_bar = QFrame()
        top_bar.setFixedHeight(8)
        top_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {color_obra};
                border-top-left-radius: 11px;
                border-top-right-radius: 11px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }}
        """)
        layout.addWidget(top_bar)

        # 2. Card Content Layout
        body = QWidget()
        body.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        body.setStyleSheet("background-color: #FFFFFF; border-bottom-left-radius: 11px; border-bottom-right-radius: 11px;")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(20, 16, 20, 16)
        body_layout.setSpacing(12)

        # Header Row: Title + Status Pill Badge
        head_row = QHBoxLayout()
        head_row.setSpacing(10)

        title = QLabel(nombre_obra)
        title.setWordWrap(True)
        title.setStyleSheet("""
            font-size: 16px; 
            font-weight: 800; 
            color: #1F2421; 
            font-family: 'Space Grotesk', 'Work Sans', sans-serif;
            background: transparent;
        """)

        is_activa = estado_obra.lower() == "activa"
        badge_bg = "#F2EFE9" if is_activa else "#FEE2E2"
        badge_fg = "#262B29" if is_activa else "#DC2626"

        status_badge = QLabel(estado_obra.upper())
        status_badge.setStyleSheet(f"""
            background-color: {badge_bg};
            color: {badge_fg};
            font-size: 10px;
            font-weight: 800;
            padding: 4px 10px;
            border-radius: 10px;
            font-family: 'Inter', sans-serif;
        """)
        status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

        head_row.addWidget(title, stretch=1)
        head_row.addWidget(status_badge, alignment=Qt.AlignmentFlag.AlignTop)
        body_layout.addLayout(head_row)

        # Supervisor Row
        texto_jefe = "Supervisor: No asignado"
        if self.nombres_jefes:
            texto_jefe = f"Supervisor: {self.nombres_jefes[0]}"
            if len(self.nombres_jefes) > 1:
                texto_jefe += f" (+{len(self.nombres_jefes)-1})"

        lbl_jefe = QLabel(texto_jefe)
        lbl_jefe.setStyleSheet("""
            color: #262B29;
            font-size: 12px;
            font-weight: 600;
            background: transparent;
        """)
        body_layout.addWidget(lbl_jefe)

        # Separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Plain)
        sep.setStyleSheet("color: #F2EFE9; background-color: #F2EFE9; height: 1px; border: none;")
        body_layout.addWidget(sep)

        # Footer Action Link
        footer_row = QHBoxLayout()
        action_lbl = QLabel("Ingresar a Detalle de Obra ->")
        action_lbl.setStyleSheet("""
            color: #3D523C;
            font-size: 12px;
            font-weight: 700;
            background: transparent;
        """)
        footer_row.addWidget(action_lbl)
        footer_row.addStretch()

        body_layout.addLayout(footer_row)
        layout.addWidget(body)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.pos()):
            QTimer.singleShot(0, lambda: self.clicked.emit(self.obra))
        super().mouseReleaseEvent(event)


class DashboardContent(QWidget):
    obra_selected = pyqtSignal(dict)  # Emite los datos de la obra seleccionada

    def __init__(self, supabase_client=None):
        super().__init__()
        self.supabase = supabase_client
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.scroll_content = QWidget()
        self.layout = QVBoxLayout(self.scroll_content)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.scroll_content)
        outer_layout.addWidget(self.scroll_area)
        
        header = QLabel("Dashboard Principal - Mis Obras")
        header.setObjectName("TitleLabel")
        self.layout.addWidget(header)
        self.layout.addSpacing(20)

        # ── Sección de Asistencia Hoy ──
        self.asistencia_title = QLabel("Asistencia Hoy")
        self.asistencia_title.setStyleSheet(
            "font-weight: bold; font-size: 16px; color: #262B29; padding-bottom: 4px;"
        )
        self.layout.addWidget(self.asistencia_title)

        self.asistencia_container = QHBoxLayout()
        self.asistencia_container.setContentsMargins(0, 0, 0, 4)
        self.asistencia_container.setSpacing(12)
        self.asistencia_widget = QWidget()
        self.asistencia_widget.setLayout(self.asistencia_container)

        self.asistencia_scroll = QScrollArea()
        self.asistencia_scroll.setWidgetResizable(True)
        self.asistencia_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.asistencia_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.asistencia_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.asistencia_scroll.setFixedHeight(135)
        self.asistencia_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.asistencia_scroll.setWidget(self.asistencia_widget)
        self.layout.addWidget(self.asistencia_scroll)

        self.lbl_sin_asistencia = QLabel("Sin asistencia registrada hoy.")
        self.lbl_sin_asistencia.setStyleSheet("color: #262B29; font-size: 13px; padding: 8px 0;")
        self.lbl_sin_asistencia.setVisible(False)
        self.layout.addWidget(self.lbl_sin_asistencia)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setStyleSheet("color: #4A524E; margin: 8px 0;")
        self.layout.addWidget(sep)
        self.layout.addSpacing(8)

        # ── Contenedor para el Grid de Obras ──
        self.grid_container = QWidget()
        self.grid = QGridLayout(self.grid_container)
        self.grid.setSpacing(20)
        self.layout.addWidget(self.grid_container)

    def cargar_obras(self, force_refresh: bool = False):
        # Limpiar grid anterior
        for i in reversed(range(self.grid.count())):
            widget = self.grid.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # Limpiar panel de asistencia
        for i in reversed(range(self.asistencia_container.count())):
            item = self.asistencia_container.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        if not self.supabase:
            return

        self.worker = FetchDashboardDataWorker(self.supabase, force_refresh=force_refresh)
        self.worker.success.connect(self.on_data_success)
        self.worker.error.connect(self.on_data_error)
        self.worker.start()

        self.worker_asist = FetchDashboardAsistenciaWorker(self.supabase, force_refresh=force_refresh)
        self.worker_asist.success.connect(self.on_asistencia_success)
        self.worker_asist.error.connect(lambda e: print(f"[Dashboard Asistencia] {e}"))
        self.worker_asist.start()

    def on_asistencia_success(self, asistencias):
        """Renderiza las tarjetas KPI de asistencia del día."""
        for i in reversed(range(self.asistencia_container.count())):
            item = self.asistencia_container.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        if not asistencias:
            self.asistencia_scroll.setVisible(False)
            self.lbl_sin_asistencia.setVisible(True)
            return

        self.asistencia_scroll.setVisible(True)
        self.lbl_sin_asistencia.setVisible(False)
        for data in asistencias:
            card = self._create_asistencia_card(data)
            self.asistencia_container.addWidget(card)
        self.asistencia_container.addStretch()

    def _create_asistencia_card(self, data):
        card = QFrame()
        card.setFixedWidth(240)
        card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #4A524E;
                border-radius: 10px;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(69, 107, 109, 25))
        shadow.setOffset(0, 3)
        card.setGraphicsEffect(shadow)

        cl = QVBoxLayout(card)
        cl.setContentsMargins(14, 12, 14, 12)
        cl.setSpacing(6)

        nombre = QLabel(data.get("obra_nombre", ""))
        nombre.setStyleSheet("font-weight: 800; font-size: 13px; color: #262B29; font-family: 'Space Grotesk', 'Work Sans', sans-serif;")
        nombre.setWordWrap(True)
        cl.addWidget(nombre)

        total = data.get("total", 0)
        presentes = data.get("presentes", 0)
        medios = data.get("medios", 0)
        ausentes = data.get("ausentes", 0)
        costo = data.get("costo_dia", 0.0)
        pct = int((presentes + medios * 0.5) / total * 100) if total else 0

        stats_text = (
            f"Presentes: {presentes}   Medios: {medios}   Ausentes: {ausentes}\n"
            f"Asistencia: {pct}%"
        )
        stats = QLabel(stats_text)
        stats.setStyleSheet("font-size: 12px; color: #1F2421; line-height: 1.4;")
        cl.addWidget(stats)

        costo_lbl = QLabel(f"Costo Hoy: ${costo:,.0f}")
        costo_lbl.setStyleSheet("font-weight: 800; font-size: 12px; color: #3D523C;")
        cl.addWidget(costo_lbl)

        return card

    def on_data_error(self, message):
        QMessageBox.warning(self, "Error", message)

    def on_data_success(self, obras, jefes_por_obra):
        for i in reversed(range(self.grid.count())):
            widget = self.grid.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        row, col = 0, 0
        for obra in obras:
            obra_id = obra.get("id")
            nombres_jefes = jefes_por_obra.get(obra_id, [])
            card = self.create_obra_card(obra, nombres_jefes)
            card.clicked.connect(self.on_card_clicked)
            self.grid.addWidget(card, row, col)
            col += 1
            if col > 2: # 3 columnas
                col = 0
                row += 1

    def on_card_clicked(self, obra):
        self.obra_selected.emit(obra)

    def create_obra_card(self, obra, nombres_jefes):
        card = ClickableObraCard(obra, nombres_jefes)
        return card
