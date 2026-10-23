from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QComboBox, QSplitter, QFrame, QScrollArea, QSizePolicy, QDialog
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QColor
from src.core.workers import FetchReportesWorker, RespondReporteWorker

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

class GraficosRendimientoDialog(QDialog):
    def __init__(self, obra_id, obra_nombre, consumos, materiales, items, avances, parent=None):
        super().__init__(parent)
        self.obra_id = obra_id
        self.obra_nombre = obra_nombre
        self.consumos = consumos
        # Filtrar materiales globales asociados a los items de la obra actual
        obra_mat_ids = {i.get("material_id") for i in items if i.get("obra_id") == self.obra_id and i.get("material_id")}
        self.materiales = [m for m in materiales if m.get("id") in obra_mat_ids] if obra_mat_ids else materiales
        self.items = items
        self.avances = avances
        
        self.setWindowTitle(f"Rendimiento de Materiales - {self.obra_nombre}")
        self.setMinimumSize(850, 700)
        self.setStyleSheet("QDialog { background-color: #FFFFFF; color: #1F2421; }")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # Header
        title = QLabel(f"Análisis de Desviaciones de Material: {self.obra_nombre}")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1F2421; font-family: 'Space Grotesk', 'Work Sans';")
        layout.addWidget(title)
        
        # Selector de material
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Seleccionar Material de la Obra:"))
        self.combo_material = QComboBox()
        for m in self.materiales:
            self.combo_material.addItem(f"{m.get('nombre')} ({m.get('unidad_medida')})", m.get("id"))
        
        self.combo_material.currentIndexChanged.connect(self.actualizar_graficos)
        selector_layout.addWidget(self.combo_material, 1)
        selector_layout.addStretch()
        layout.addLayout(selector_layout)
        
        # Matplotlib Figure Canvas
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setParent(self)
        layout.addWidget(self.canvas, 1)
        
        # Botón Cerrar
        btn_close = QPushButton("Cerrar")
        btn_close.setStyleSheet("QPushButton { background-color: #262B29; color: white; font-weight: bold; border-radius: 6px; padding: 10px 20px; } QPushButton:hover { background-color: #262B29; }")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.actualizar_graficos()
        
    def actualizar_graficos(self):
        self.figure.clear()
        
        mat_id = self.combo_material.currentData()
        if not mat_id:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, "No hay materiales registrados para esta obra.", 
                    horizontalalignment='center', verticalalignment='center', fontsize=12, color='gray')
            self.canvas.draw()
            return
            
        mat_info = next((m for m in self.materiales if m.get("id") == mat_id), None)
        if not mat_info:
            return
            
        # 1. Filtrar consumos exclusivamente de la obra seleccionada
        mat_consumos = [
            c for c in self.consumos
            if c.get("material_id") == mat_id and (not c.get("obra_id") or c.get("obra_id") == self.obra_id)
        ]
        
        # 2. Filtrar items asociados al material
        items_ids = {i.get("id") for i in self.items if i.get("material_id") == mat_id and i.get("obra_id") == self.obra_id}
        
        # 3. Filtrar avances de esos items (excluyendo avances rechazados)
        avances_mat = [
            av for av in self.avances
            if av.get("item_obra_id") in items_ids and str(av.get("estado_revision") or "").lower() != "rechazado"
        ]
        
        # 4. Agrupar consumos reales por fecha
        consumos_por_dia = {}
        for c in mat_consumos:
            f_val = c.get("fecha") or ""
            if len(f_val) >= 10:
                f_str = f_val[:10]
                consumos_por_dia[f_str] = consumos_por_dia.get(f_str, 0.0) + float(c.get("cantidad") or 0.0)
                
        # 5. Agrupar avances m2 por fecha
        avances_por_dia = {}
        for av in avances_mat:
            f_val = av.get("fecha_captura_local") or ""
            if len(f_val) >= 10:
                f_str = f_val[:10]
                avances_por_dia[f_str] = avances_por_dia.get(f_str, 0.0) + float(av.get("cantidad") or 0.0)
                
        # Fechas ordenadas
        fechas = sorted(list(set(list(consumos_por_dia.keys()) + list(avances_por_dia.keys()))))
        
        if not fechas:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, "Sin registros de consumo ni avances para este material hoy.", 
                    horizontalalignment='center', verticalalignment='center', fontsize=12, color='gray')
            self.canvas.draw()
            return
            
        cant_reales = []
        avances_reales_m2 = []
        rendimientos_diarios = []
        
        total_consumo = sum(consumos_por_dia.values())
        total_avance_m2 = sum(avances_por_dia.values())
        rend_promedio_global = (total_avance_m2 / total_consumo) if total_consumo > 0 else 0.0
        consumo_unitario_prom = (total_consumo / total_avance_m2) if total_avance_m2 > 0 else 0.0
        
        for f in fechas:
            c_val = consumos_por_dia.get(f, 0.0)
            a_val = avances_por_dia.get(f, 0.0)
            cant_reales.append(c_val)
            avances_reales_m2.append(a_val)
            
            rend_dia = (a_val / c_val) if c_val > 0 else 0.0
            rendimientos_diarios.append(rend_dia)
            
        unidad_medida = mat_info.get('unidad_medida', 'unidades')
        
        # Graficar
        # Grafico 1: Consumo Real vs Avance Físico por Día
        ax1 = self.figure.add_subplot(2, 1, 1)
        x = np.arange(len(fechas))
        width = 0.35
        
        rects1 = ax1.bar(x - width/2, cant_reales, width, label=f'Consumo Real ({unidad_medida})', color='#3D523C')
        ax1.set_ylabel(f"Consumo ({unidad_medida})", color='#2F402E')
        ax1.set_xticks(x)
        ax1.set_xticklabels(fechas)
        ax1.grid(True, linestyle=':', alpha=0.6)
        
        # Eje secundario para m2 avanzadas
        ax1_twin = ax1.twinx()
        line1 = ax1_twin.plot(x, avances_reales_m2, color='#2E6F40', marker='o', linewidth=2.5, label='Avance Físico (m²)')
        ax1_twin.set_ylabel("Avance Executado (m²)", color='#2F402E')
        
        # Leyenda combinada
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax1_twin.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
        ax1.set_title(f"Consumo Real ({unidad_medida}) vs. Avance Físico (m²) - {mat_info.get('nombre')}", fontsize=11, fontweight='bold', pad=10)
        
        # Grafico 2: Rendimiento Real Calculado (m² / unidad)
        ax2 = self.figure.add_subplot(2, 1, 2)
        ax2.bar(x, rendimientos_diarios, width=0.4, label='Rendimiento Real Diario (m²/unidad)', color='#4A524E')
        if rend_promedio_global > 0:
            ax2.axhline(rend_promedio_global, color='#EF4444', linestyle='--', linewidth=2, 
                        label=f'Promedio Real Obra ({rend_promedio_global:.2f} m²/{unidad_medida})')
        
        ax2.set_title(f"Rendimiento Real Calculado por Terreno ({rend_promedio_global:.2f} m²/{unidad_medida} acum. | {consumo_unitario_prom:.3f} {unidad_medida}/m²)", fontsize=11, fontweight='bold', pad=10)
        ax2.set_xticks(x)
        ax2.set_xticklabels(fechas)
        ax2.set_ylabel(f"Rendimiento (m²/{unidad_medida})")
        ax2.grid(True, linestyle=':', alpha=0.6)
        ax2.legend(loc='upper right')
        
        self.figure.autofmt_xdate()
        self.figure.tight_layout()
        self.canvas.draw()


class ReportesContent(QWidget):
    def __init__(self, supabase_client=None, fixed_obra_id=None):
        super().__init__()
        self.supabase_client = supabase_client
        self.fixed_obra_id = fixed_obra_id
        self.reportes = []
        self.consumos = []
        self.materiales = []
        self.items = []
        self.avances = []
        self.reporte_seleccionado = None

        # Layout Principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Header
        header = QLabel("Panel de Reportes Diarios y Consumos")
        header.setObjectName("TitleLabel")
        main_layout.addWidget(header)
        main_layout.addSpacing(10)

        # Filtros
        filtros_frame = QFrame()
        filtros_frame.setStyleSheet("QFrame { background-color: #FAF8F5; color: #1F2421; border: 1px solid #D8D5CD; border-radius: 8px; }")
        filtros_layout = QHBoxLayout(filtros_frame)
        filtros_layout.setContentsMargins(15, 10, 15, 10)

        self.lbl_filtro_obra = QLabel("Filtrar por Obra:")
        filtros_layout.addWidget(self.lbl_filtro_obra)
        self.combo_obra = QComboBox()
        self.combo_obra.addItem("Todas las Obras", None)
        self.combo_obra.currentIndexChanged.connect(self.aplicar_filtros)
        filtros_layout.addWidget(self.combo_obra)
        filtros_layout.addSpacing(15)

        if self.fixed_obra_id:
            self.lbl_filtro_obra.hide()
            self.combo_obra.hide()

        filtros_layout.addWidget(QLabel("Tipo de Reporte:"))
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItem("Todos los tipos", None)
        self.combo_tipo.addItem("Diario (Actualización)", "actualizacion")
        self.combo_tipo.addItem("Incidente", "incidente")
        self.combo_tipo.addItem("Accidente", "accidente")
        self.combo_tipo.addItem("Otro", "otro")
        self.combo_tipo.currentIndexChanged.connect(self.aplicar_filtros)
        filtros_layout.addWidget(self.combo_tipo)
        filtros_layout.addSpacing(15)

        filtros_layout.addWidget(QLabel("Estado de Revisión:"))
        self.combo_estado = QComboBox()
        self.combo_estado.addItem("Todos", None)
        self.combo_estado.addItem("Pendiente", "pendiente")
        self.combo_estado.addItem("Leído", "leido")
        self.combo_estado.addItem("Respondido", "respondido")
        self.combo_estado.currentIndexChanged.connect(self.aplicar_filtros)
        filtros_layout.addWidget(self.combo_estado)
        filtros_layout.addStretch()

        self.btn_analizar = QPushButton("Ver Rendimientos")
        self.btn_analizar.setStyleSheet("QPushButton { background-color: #3D523C; color: white; font-weight: bold; border-radius: 6px; padding: 10px 16px; } QPushButton:hover { background-color: #3D523C; }")
        self.btn_analizar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_analizar.setEnabled(False)
        self.btn_analizar.clicked.connect(self.abrir_graficos)
        filtros_layout.addWidget(self.btn_analizar)
        filtros_layout.addSpacing(10)

        self.btn_refresh = QPushButton("Actualizar")
        self.btn_refresh.setObjectName("PrimaryButton")
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.clicked.connect(lambda: self.cargar_reportes(force_refresh=True))
        filtros_layout.addWidget(self.btn_refresh)

        main_layout.addWidget(filtros_frame)
        main_layout.addSpacing(15)

        # Splitter central
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter, 1)

        # Panel Izquierdo: Tabla de Reportes
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_title = QLabel("Reportes Recibidos")
        left_title.setStyleSheet("font-weight: bold; font-size: 16px; color: #1F2421;")
        left_layout.addWidget(left_title)

        self.table = QTableWidget()
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setMinimumSectionSize(110)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Fecha", "Obra", "Supervisor", "Tipo", "Estado"])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_reporte_seleccionado)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # Fecha
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)            # Obra
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Supervisor
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Tipo
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) # Estado
        self.table.horizontalHeader().setStretchLastSection(True)

        left_layout.addWidget(self.table)
        splitter.addWidget(left_widget)

        # Panel Derecho: Detalle del Reporte
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: 1px solid #D8D5CD; border-radius: 8px; background-color: #FFFFFF; color: #1F2421; }")

        right_widget = QWidget()
        right_widget.setStyleSheet("background-color: #FFFFFF; color: #1F2421;")
        self.right_layout = QVBoxLayout(right_widget)
        self.right_layout.setContentsMargins(20, 20, 20, 20)

        self.lbl_no_select = QLabel("Seleccione un reporte de la lista para ver sus detalles.")
        self.lbl_no_select.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_no_select.setStyleSheet("color: #94A3B8; font-size: 14px; font-style: italic; padding: 50px;")
        self.right_layout.addWidget(self.lbl_no_select)

        # Widget de detalles (oculto por defecto)
        self.detail_widget = QWidget()
        self.detail_layout = QVBoxLayout(self.detail_widget)
        self.detail_layout.setContentsMargins(0, 0, 0, 0)
        self.detail_layout.setSpacing(15)

        # Ficha de Info General
        self.info_card = QFrame()
        self.info_card.setStyleSheet("QFrame { background-color: #F2EFE9; border: 1px solid #BFDBFE; border-left: 6px solid #2F402E; border-radius: 8px; }")
        info_layout = QVBoxLayout(self.info_card)
        self.lbl_info_obra = QLabel()
        self.lbl_info_obra.setStyleSheet("font-weight: bold; font-size: 16px; color: #1E3A8A;")
        self.lbl_info_meta = QLabel()
        self.lbl_info_meta.setStyleSheet("font-size: 12px; color: #1E40AF;")
        info_layout.addWidget(self.lbl_info_obra)
        info_layout.addWidget(self.lbl_info_meta)
        self.detail_layout.addWidget(self.info_card)

        # Mensaje
        self.detail_layout.addWidget(QLabel("<b>Novedades y Mensaje Diario:</b>"))
        self.txt_mensaje = QTextEdit()
        self.txt_mensaje.setReadOnly(True)
        self.txt_mensaje.setMaximumHeight(120)
        self.txt_mensaje.setStyleSheet("QTextEdit { border: 1px solid #D8D5CD; border-radius: 6px; padding: 10px; background-color: #FAF8F5; color: #334155; }")
        self.detail_layout.addWidget(self.txt_mensaje)

        # Fotos / Adjuntos
        self.lbl_adjuntos_title = QLabel("<b>Archivos Adjuntos / Fotos:</b>")
        self.detail_layout.addWidget(self.lbl_adjuntos_title)
        self.adjuntos_container = QWidget()
        self.adjuntos_layout = QHBoxLayout(self.adjuntos_container)
        self.adjuntos_layout.setContentsMargins(0, 0, 0, 0)
        self.adjuntos_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.detail_layout.addWidget(self.adjuntos_container)

        # Consumo de Materiales
        self.lbl_consumo_title = QLabel("<b>Materiales Consumidos Reportados:</b>")
        self.detail_layout.addWidget(self.lbl_consumo_title)
        self.consumos_table = QTableWidget()
        self.consumos_table.verticalHeader().setDefaultSectionSize(44)
        self.consumos_table.verticalHeader().setVisible(False)
        self.consumos_table.horizontalHeader().setMinimumSectionSize(110)
        self.consumos_table.setColumnCount(3)
        self.consumos_table.setHorizontalHeaderLabels(["Material", "Cantidad", "Unidad"])
        self.consumos_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.consumos_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)            # Material
        self.consumos_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # Cantidad
        self.consumos_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Unidad
        self.consumos_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.consumos_table.setMaximumHeight(130)
        self.consumos_table.setAlternatingRowColors(True)
        self.detail_layout.addWidget(self.consumos_table)

        # Línea divisoria
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #D8D5CD;")
        self.detail_layout.addWidget(divider)

        # Panel de Respuesta
        self.detail_layout.addWidget(QLabel("<b>Respuesta del Gerente / Administrador:</b>"))
        self.txt_respuesta = QTextEdit()
        self.txt_respuesta.setPlaceholderText("Escriba aquí la respuesta, comentarios o instrucciones para el Supervisor...")
        self.txt_respuesta.setMaximumHeight(100)
        self.txt_respuesta.setStyleSheet("QTextEdit { border: 1px solid #D8D5CD; border-radius: 6px; padding: 10px; }")
        self.detail_layout.addWidget(self.txt_respuesta)

        # Fila de Acciones
        acciones_layout = QHBoxLayout()
        self.btn_leido = QPushButton("Marcar como Leído")
        self.btn_leido.setStyleSheet("QPushButton { background-color: #262B29; color: #FFFFFF; font-weight: bold; border-radius: 6px; padding: 8px 16px; } QPushButton:hover { background-color: #334155; }")
        self.btn_leido.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_leido.clicked.connect(self.marcar_leido)

        self.btn_responder = QPushButton("Enviar Respuesta")
        self.btn_responder.setStyleSheet("QPushButton { background-color: #2E6F40; color: #FFFFFF; font-weight: bold; border-radius: 6px; padding: 8px 20px; } QPushButton:hover { background-color: #3D523C; }")
        self.btn_responder.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_responder.clicked.connect(self.enviar_respuesta)

        acciones_layout.addWidget(self.btn_leido)
        acciones_layout.addWidget(self.btn_responder)
        acciones_layout.addStretch()
        self.detail_layout.addLayout(acciones_layout)

        # Estado de Respuesta Anterior (Solo lectura si ya fue respondido)
        self.lbl_respuesta_anterior = QLabel()
        self.lbl_respuesta_anterior.setWordWrap(True)
        self.lbl_respuesta_anterior.setStyleSheet("QLabel { background-color: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 6px; padding: 10px; color: #166534; font-size: 13px; }")
        self.detail_layout.addWidget(self.lbl_respuesta_anterior)

        self.right_layout.addWidget(self.detail_widget)
        self.detail_widget.hide()

        self.scroll_area.setWidget(right_widget)
        splitter.addWidget(self.scroll_area)

        # Ajustar proporciones de inicio en el Splitter (40% izquierda, 60% derecha)
        splitter.setSizes([450, 650])

    def cargar_reportes(self, force_refresh: bool = False):
        if not self.supabase_client:
            return
        
        self.btn_refresh.setEnabled(False)
        self.btn_refresh.setText("Cargando...")
        self.btn_analizar.setEnabled(False)
        self.detail_widget.hide()
        self.lbl_no_select.show()

        self.worker = FetchReportesWorker(self.supabase_client, force_refresh=bool(force_refresh))
        self.worker.success.connect(self.on_reportes_cargados)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_error(self, message):
        self.btn_refresh.setEnabled(True)
        self.btn_refresh.setText("Actualizar")
        self.btn_analizar.setEnabled(bool(self.fixed_obra_id or self.combo_obra.currentData()))
        QMessageBox.warning(self, "Error", message)

    def on_reportes_cargados(self, reportes, consumos, materiales, items, avances):
        self.btn_refresh.setEnabled(True)
        self.btn_refresh.setText("Actualizar")
        self.reportes = reportes
        self.consumos = consumos
        self.materiales = materiales
        self.items = items
        self.avances = avances

        # Cargar combo de obras
        obras_unicas = {}
        for r in reportes:
            obras_unicas[r.get("obra_id")] = r.get("obra_nombre")

        # Desconectar señal de forma temporal
        self.combo_obra.blockSignals(True)
        self.combo_obra.clear()
        self.combo_obra.addItem("Todas las Obras", None)
        for o_id, o_nombre in obras_unicas.items():
            self.combo_obra.addItem(o_nombre, o_id)
        self.combo_obra.blockSignals(False)

        self.aplicar_filtros()

    def aplicar_filtros(self):
        obra_id_filter = self.fixed_obra_id if self.fixed_obra_id else self.combo_obra.currentData()
        tipo_filter = self.combo_tipo.currentData()
        estado_filter = self.combo_estado.currentData()

        # Activar/Desactivar botón de análisis de gráficos
        self.btn_analizar.setEnabled(bool(obra_id_filter))

        # Filtrar
        filtered = self.reportes
        if obra_id_filter:
            filtered = [r for r in filtered if r.get("obra_id") == obra_id_filter]
        if tipo_filter:
            filtered = [r for r in filtered if r.get("tipo_reporte") == tipo_filter]
        if estado_filter:
            filtered = [r for r in filtered if r.get("estado_reb") == estado_filter]

        # Cargar Tabla
        self.table.setRowCount(0)
        for r in filtered:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)

            # Formatear fecha
            fecha_str = r.get("fecha_publicacion", "")
            if len(fecha_str) > 10:
                fecha_str = fecha_str[:16].replace("T", " ")

            tipo_val = r.get("tipo_reporte", "actualizacion")
            tipo_labels = {
                "actualizacion": "Diario",
                "incidente": "Incidente",
                "accidente": "Accidente",
                "otro": "Otro"
            }
            tipo_lbl = tipo_labels.get(tipo_val, tipo_val)

            estado_val = r.get("estado_reb", "pendiente")
            estado_labels = {
                "pendiente": "Pendiente",
                "leido": "Leído",
                "respondido": "Respondido"
            }
            estado_lbl = estado_labels.get(estado_val, estado_val)

            item_fecha = QTableWidgetItem(fecha_str)
            item_obra = QTableWidgetItem(r.get("obra_nombre", ""))
            item_jefe = QTableWidgetItem(r.get("jefe_nombre", ""))
            item_tipo = QTableWidgetItem(tipo_lbl)
            item_estado = QTableWidgetItem(estado_lbl)

            # Colorear incidentes/accidentes de forma sutil
            if tipo_val in ["incidente", "accidente"]:
                color = QColor(254, 242, 242) # Rojo claro
                item_tipo.setBackground(color)
                if tipo_val == "accidente":
                    item_tipo.setForeground(QColor(220, 38, 38))

            self.table.setItem(row_idx, 0, item_fecha)
            self.table.setItem(row_idx, 1, item_obra)
            self.table.setItem(row_idx, 2, item_jefe)
            self.table.setItem(row_idx, 3, item_tipo)
            self.table.setItem(row_idx, 4, item_estado)

            # Guardar el ID de reporte asociado a la fila
            item_fecha.setData(Qt.ItemDataRole.UserRole, r.get("id"))

    def on_reporte_seleccionado(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            self.reporte_seleccionado = None
            self.detail_widget.hide()
            self.lbl_no_select.show()
            return

        # El ID se guarda en la primera celda (Fecha) de la fila seleccionada
        row = selected_items[0].row()
        reporte_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        rep = next((r for r in self.reportes if r.get("id") == reporte_id), None)
        if not rep:
            return

        self.reporte_seleccionado = rep
        self.lbl_no_select.hide()
        self.detail_widget.show()

        # Rellenar Información
        self.lbl_info_obra.setText(rep.get("obra_nombre"))
        
        fecha_str = rep.get("fecha_publicacion", "")
        if len(fecha_str) > 10:
            fecha_str = fecha_str[:16].replace("T", " ")
        
        tipo_lbl = rep.get("tipo_reporte", "").upper()
        self.lbl_info_meta.setText(f"Enviado por: {rep.get('jefe_nombre')}   |   Fecha: {fecha_str}   |   Tipo: {tipo_lbl}")

        # Mensaje
        self.txt_mensaje.setText(rep.get("mensaje"))

        # Cargar Adjuntos/Fotos
        # Limpiar contenedor anterior de adjuntos
        for i in reversed(range(self.adjuntos_layout.count())):
            widget = self.adjuntos_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        adjuntos_links = rep.get("archivos_adjuntos", [])
        if adjuntos_links:
            self.lbl_adjuntos_title.show()
            self.adjuntos_container.show()
            for idx, link in enumerate(adjuntos_links):
                btn_link = QPushButton(f"Foto {idx+1}")
                btn_link.setStyleSheet("QPushButton { color: #2F402E; text-decoration: underline; background: transparent; border: none; font-size: 13px; font-weight: bold; } QPushButton:hover { color: #1E40AF; }")
                btn_link.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_link.clicked.connect(lambda checked, url=link: QDesktopServices.openUrl(QUrl(url)))
                self.adjuntos_layout.addWidget(btn_link)
        else:
            self.lbl_adjuntos_title.hide()
            self.adjuntos_container.hide()

        # Filtrar consumos asociados a este reporte
        rep_consumos = [c for c in self.consumos if c.get("reporte_obra_id") == rep.get("id")]
        self.consumos_table.setRowCount(0)
        if rep_consumos:
            self.lbl_consumo_title.show()
            self.consumos_table.show()
            for con in rep_consumos:
                row_con = self.consumos_table.rowCount()
                self.consumos_table.insertRow(row_con)
                # Cruzar para obtener el nombre del material desde materiales si mat_id está seteado, fallback a con.material
                mat_name = con.get("material") or "Desconocido"
                mat_id = con.get("material_id")
                if mat_id:
                    material_match = next((m for m in self.materiales if m.get("id") == mat_id), None)
                    if material_match:
                        mat_name = material_match.get("nombre")

                self.consumos_table.setItem(row_con, 0, QTableWidgetItem(mat_name))
                self.consumos_table.setItem(row_con, 1, QTableWidgetItem(str(con.get("cantidad", 0.0))))
                self.consumos_table.setItem(row_con, 2, QTableWidgetItem(con.get("unidad") or "un"))
        else:
            self.lbl_consumo_title.hide()
            self.consumos_table.hide()

        # Gestionar Sección de Respuesta
        estado_val = rep.get("estado_reb", "pendiente")
        if estado_val == "respondido":
            self.txt_respuesta.hide()
            self.btn_leido.hide()
            self.btn_responder.hide()
            
            resp_msg = rep.get("mensaje_respuesta") or "Sin mensaje de respuesta registrado."
            self.lbl_respuesta_anterior.setText(f"<b>Respuesta enviada anteriormente:</b><br/>{resp_msg}")
            self.lbl_respuesta_anterior.show()
        else:
            self.txt_respuesta.show()
            self.txt_respuesta.clear()
            self.btn_leido.show()
            self.btn_responder.show()
            self.lbl_respuesta_anterior.hide()

            # Habilitar o deshabilitar botón de marcar leido
            if estado_val == "leido":
                self.btn_leido.setEnabled(False)
                self.btn_leido.setText("Reporte ya Leído")
            else:
                self.btn_leido.setEnabled(True)
                self.btn_leido.setText("Marcar como Leído")

    def marcar_leido(self):
        if not self.reporte_seleccionado:
            return
        
        rep_id = self.reporte_seleccionado.get("id")
        self.setEnabled(False)

        self.resp_worker = RespondReporteWorker(self.supabase_client, rep_id, "", marcar_solo_leido=True)
        self.resp_worker.success.connect(self.on_respuesta_exitosa)
        self.resp_worker.error.connect(self.on_respuesta_error)
        self.resp_worker.start()

    def enviar_respuesta(self):
        if not self.reporte_seleccionado:
            return
        
        rep_id = self.reporte_seleccionado.get("id")
        msg = self.txt_respuesta.toPlainText().strip()
        
        if not msg:
            QMessageBox.warning(self, "Respuesta vacía", "Por favor escriba un mensaje de respuesta antes de enviar.")
            return

        self.setEnabled(False)

        self.resp_worker = RespondReporteWorker(self.supabase_client, rep_id, msg, marcar_solo_leido=False)
        self.resp_worker.success.connect(self.on_respuesta_exitosa)
        self.resp_worker.error.connect(self.on_respuesta_error)
        self.resp_worker.start()

    def on_respuesta_error(self, message):
        self.setEnabled(True)
        QMessageBox.warning(self, "Error", message)

    def on_respuesta_exitosa(self, message):
        self.setEnabled(True)
        QMessageBox.information(self, "Éxito", message)
        # Recargar datos forzando refresco de caché
        self.cargar_reportes(force_refresh=True)

    def abrir_graficos(self):
        obra_id = self.fixed_obra_id if self.fixed_obra_id else self.combo_obra.currentData()
        if not obra_id:
            return
            
        obra_nombre = self.combo_obra.currentText()
        if self.fixed_obra_id and self.reportes:
            match_rep = next((r for r in self.reportes if r.get("obra_id") == self.fixed_obra_id), None)
            if match_rep:
                obra_nombre = match_rep.get("obra_nombre", "Obra")

        obra_reporte_ids = {r.get("id") for r in self.reportes if r.get("obra_id") == obra_id}
        obra_consumos = [
            c for c in self.consumos
            if c.get("obra_id") == obra_id or c.get("reporte_obra_id") in obra_reporte_ids
        ]
            
        dialog = GraficosRendimientoDialog(
            obra_id, obra_nombre, obra_consumos, self.materiales, self.items, self.avances, self
        )
        dialog.exec()
