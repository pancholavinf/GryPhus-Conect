from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, QPushButton, QLabel, QLineEdit,
    QMessageBox, QFormLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QComboBox, QDoubleSpinBox, QTextEdit, QFileDialog,
    QScrollArea, QSplitter, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QThread
from PyQt6.QtGui import QPixmap, QDesktopServices
import urllib.request
import webbrowser
import json
import uuid
import os
import datetime


from src.core.workers import (
    FetchMaterialesWorker, SaveMaterialWorker, UploadMaterialFileWorker, DeleteMaterialWorker
)
from src.ui.document_viewer import DocumentViewerDialog



import requests

class LoadImageWorker(QThread):
    loaded = pyqtSignal(bytes, str) # image_bytes, url
    error = pyqtSignal(str)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def run(self):
        try:
            resp = requests.get(
                self.url,
                headers={'User-Agent': 'Mozilla/5.0'},
                timeout=5
            )
            resp.raise_for_status()
            self.loaded.emit(resp.content, self.url)
        except Exception as e:
            self.error.emit(str(e))


class MaterialesContent(QWidget):
    def __init__(self, supabase_client=None):
        super().__init__()
        self.supabase_client = supabase_client
        self.materiales_data = []
        self.current_material = None
        self.current_foto_url = ""
        self.current_ficha_url = ""
        self.current_estudios = [] # list of dicts: [{"id":..., "nombre":..., "url":..., "fecha":...}]
        self.is_editing = False

        self.setup_ui()
        if self.supabase_client:
            self.cargar_materiales()

    def setup_ui(self):
        # Estilos globales para la vista
        self.setStyleSheet("""
            QWidget {
                background-color: #FAF8F5;
                color: #1F2421;
                font-size: 13px;
            }
            QLabel {
                color: #1F2421;
                font-weight: 500;
            }
            QLineEdit, QComboBox, QDoubleSpinBox, QTextEdit {
                background-color: #FFFFFF;
                color: #1F2421;
                border: 1px solid #D8D5CD;
                border-radius: 6px;
                padding: 6px 10px;
                selection-background-color: #3D523C;
            }
            QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {
                border: 2px solid #3D523C;
            }
            QLineEdit:disabled, QComboBox:disabled, QDoubleSpinBox:disabled, QTextEdit:disabled {
                background-color: #F2EFE9;
                color: #334155;
                border: 1px solid #D8D5CD;
            }
            QGroupBox {
                background-color: #FFFFFF;
                font-weight: bold;
                font-size: 14px;
                color: #1F2421;
                border: 1px solid #D8D5CD;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                background-color: #FFFFFF;
                color: #262B29;
            }
            
            
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(15)

        # Header Superior
        header_layout = QHBoxLayout()
        header_title = QLabel("Gestión de Materiales")
        header_title.setStyleSheet("font-size: 24px; font-weight: 800; color: #1F2421;")
        header_layout.addWidget(header_title)
        header_layout.addStretch()

        self.btn_nuevo = QPushButton("+ Nuevo Material")
        self.btn_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nuevo.setStyleSheet("""
            QPushButton {
                background-color: #3D523C; color: white; border-radius: 6px;
                padding: 8px 18px; font-weight: 700; font-size: 13px; border: none;
            }
            QPushButton:hover { background-color: #2F402E; }
        """)
        self.btn_nuevo.clicked.connect(self.preparar_nuevo_material)
        header_layout.addWidget(self.btn_nuevo)

        main_layout.addLayout(header_layout)

        # Splitter principal: Izquierda (Tabla y Filtros) / Derecha (Detalle / Edición)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # --- PANEL IZQUIERDO: Tabla y Búsqueda ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 10, 0)
        left_layout.setSpacing(10)

        # Filtros
        filter_layout = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Buscar material por nombre o descripción...")
        self.txt_search.setClearButtonEnabled(True)
        self.txt_search.textChanged.connect(self.filtrar_tabla)

        self.combo_filter_unidad = QComboBox()
        self.combo_filter_unidad.addItem("Todas las Unidades", "")
        self.combo_filter_unidad.addItems(["m2", "m3", "kg", "tineta", "saco", "litro", "unidad"])
        self.combo_filter_unidad.currentIndexChanged.connect(self.filtrar_tabla)

        filter_layout.addWidget(self.txt_search, stretch=3)
        filter_layout.addWidget(self.combo_filter_unidad, stretch=1)
        left_layout.addLayout(filter_layout)

        # Tabla
        self.table = QTableWidget()
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setMinimumSectionSize(110)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Nombre", "Unidad", "Rend. Ref.", "Foto", "Estudios"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_tabla_selection_changed)

        left_layout.addWidget(self.table)
        splitter.addWidget(left_widget)

        # --- PANEL DERECHO: Detalle y Edición (FONDO BLANCO PURO) ---
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setStyleSheet("QScrollArea { background-color: #FFFFFF; border: 1px solid #D8D5CD; border-radius: 8px; }")

        right_container = QWidget()
        right_container.setStyleSheet("background-color: #FFFFFF;")
        self.right_layout = QVBoxLayout(right_container)
        self.right_layout.setContentsMargins(20, 20, 20, 20)
        self.right_layout.setSpacing(15)

        # Header del Detalle + Botón Editar
        detail_header_layout = QHBoxLayout()
        self.lbl_detail_title = QLabel("Detalle del Material")
        self.lbl_detail_title.setStyleSheet("font-size: 19px; font-weight: 800; color: #1F2421; background: transparent;")
        
        self.btn_edit = QPushButton("Editar Material")
        self.btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_edit.setStyleSheet("""
            QPushButton {
                background-color: #B85A3A; color: white; border-radius: 6px;
                padding: 7px 14px; font-weight: 700; font-size: 13px; border: none;
            }
            QPushButton:hover { background-color: #9A482D; }
        """)
        self.btn_edit.clicked.connect(self.activar_edicion)
        self.btn_edit.setVisible(False)

        detail_header_layout.addWidget(self.lbl_detail_title, stretch=1)
        detail_header_layout.addWidget(self.btn_edit)
        self.right_layout.addLayout(detail_header_layout)

        # Formulario de datos básicos
        form_group = QGroupBox("Información Básica")
        form_layout = QFormLayout(form_group)
        form_layout.setVerticalSpacing(10)

        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: Pintura Intumescente R60")

        self.combo_unidad = QComboBox()
        self.combo_unidad.setEditable(True)
        self.combo_unidad.addItems(["m2", "m3", "kg", "tineta", "saco", "litro", "unidad"])

        self.spin_rendimiento = QDoubleSpinBox()
        self.spin_rendimiento.setRange(0.0, 99999.0)
        self.spin_rendimiento.setDecimals(2)
        self.spin_rendimiento.setSuffix(" m²/unidad")
        self.spin_rendimiento.setToolTip("El rendimiento real se calcula dinámicamente en los reportes diarios según el avance (m²) y espesor del ítem.")

        self.txt_descripcion = QTextEdit()
        self.txt_descripcion.setMaximumHeight(75)
        self.txt_descripcion.setPlaceholderText("Descripción técnica general...")

        form_layout.addRow("Nombre:", self.txt_nombre)
        form_layout.addRow("Unidad de Medida:", self.combo_unidad)
        form_layout.addRow("Rend. Referencial (opcional):", self.spin_rendimiento)
        form_layout.addRow("Descripción:", self.txt_descripcion)
        self.right_layout.addWidget(form_group)

        # Sección Foto
        photo_group = QGroupBox("Fotografía del Material")
        photo_layout = QHBoxLayout(photo_group)

        self.lbl_photo_preview = QLabel("Sin Imagen")
        self.lbl_photo_preview.setFixedSize(130, 110)
        self.lbl_photo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_photo_preview.setStyleSheet("border: 1px dashed #94A3B8; border-radius: 6px; background: #FAF8F5; color: #262B29; font-weight: bold;")

        photo_btns_layout = QVBoxLayout()
        self.btn_upload_photo = QPushButton("Subir / Cambiar Foto")
        self.btn_upload_photo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_upload_photo.setStyleSheet("QPushButton { background-color: #262B29; color: white; font-weight: 600; padding: 6px 12px; border-radius: 4px; } QPushButton:disabled { background-color: #D8D5CD; color: #94A3B8; }")
        self.btn_upload_photo.clicked.connect(self.seleccionar_foto)

        self.btn_remove_photo = QPushButton("Quitar Foto")
        self.btn_remove_photo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_remove_photo.setStyleSheet("QPushButton { color: #DC2626; background: transparent; border: 1px solid #DC2626; font-weight: 500; border-radius: 4px; padding: 4px 8px; } QPushButton:disabled { border-color: #D8D5CD; color: #D8D5CD; }")
        self.btn_remove_photo.clicked.connect(self.quitar_foto)

        photo_btns_layout.addWidget(self.btn_upload_photo)
        photo_btns_layout.addWidget(self.btn_remove_photo)
        photo_btns_layout.addStretch()

        photo_layout.addWidget(self.lbl_photo_preview)
        photo_layout.addLayout(photo_btns_layout)
        self.right_layout.addWidget(photo_group)

        # Sección Ficha Técnica (PDF)
        ficha_group = QGroupBox("Especificaciones Técnicas (Ficha PDF)")
        ficha_layout = QVBoxLayout(ficha_group)

        self.lbl_ficha_status = QLabel("No hay ficha técnica cargada.")
        self.lbl_ficha_status.setStyleSheet("color: #262B29; font-style: italic; font-weight: 500;")

        ficha_btns_layout = QHBoxLayout()
        self.btn_open_ficha = QPushButton("Abrir Ficha Técnica")
        self.btn_open_ficha.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_ficha.setStyleSheet("QPushButton { background-color: #3D523C; color: white; font-weight: 600; padding: 6px 12px; border-radius: 4px; } QPushButton:disabled { background-color: #D8D5CD; color: #94A3B8; }")
        self.btn_open_ficha.setEnabled(False)
        self.btn_open_ficha.clicked.connect(self.abrir_ficha_tecnica)

        self.btn_upload_ficha = QPushButton("⬆️ Subir / Cambiar Ficha PDF")
        self.btn_upload_ficha.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_upload_ficha.setStyleSheet("QPushButton { background-color: #262B29; color: white; font-weight: 600; padding: 6px 12px; border-radius: 4px; } QPushButton:disabled { background-color: #D8D5CD; color: #94A3B8; }")
        self.btn_upload_ficha.clicked.connect(self.seleccionar_ficha_pdf)

        ficha_btns_layout.addWidget(self.btn_open_ficha)
        ficha_btns_layout.addWidget(self.btn_upload_ficha)

        ficha_layout.addWidget(self.lbl_ficha_status)
        ficha_layout.addLayout(ficha_btns_layout)
        self.right_layout.addWidget(ficha_group)

        # Sección Estudios de Laboratorio
        estudios_group = QGroupBox("Estudios y Ensayos de Laboratorio")
        estudios_main_layout = QVBoxLayout(estudios_group)

        self.estudios_container = QWidget()
        self.estudios_container.setStyleSheet("background: transparent;")
        self.estudios_list_layout = QVBoxLayout(self.estudios_container)
        self.estudios_list_layout.setContentsMargins(0, 0, 0, 0)
        self.estudios_list_layout.setSpacing(6)

        self.btn_upload_estudio = QPushButton("+ Subir Estudio de Laboratorio")
        self.btn_upload_estudio.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_upload_estudio.setStyleSheet("QPushButton { background-color: #3D523C; color: white; border-radius: 4px; padding: 6px 12px; font-weight: 600; } QPushButton:disabled { background-color: #D8D5CD; color: #94A3B8; }")
        self.btn_upload_estudio.clicked.connect(self.seleccionar_estudio_pdf)

        estudios_main_layout.addWidget(self.estudios_container)
        estudios_main_layout.addWidget(self.btn_upload_estudio, alignment=Qt.AlignmentFlag.AlignLeft)
        self.right_layout.addWidget(estudios_group)

        # Botones de Acción al pie del detalle
        actions_layout = QHBoxLayout()
        self.btn_save = QPushButton("Guardar Cambios")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setStyleSheet("background-color: #3D523C; color: white; border-radius: 6px; padding: 9px 18px; font-weight: 700;")
        self.btn_save.clicked.connect(self.guardar_material)

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setStyleSheet("background-color: #262B29; color: white; border-radius: 6px; padding: 9px 16px; font-weight: 600;")
        self.btn_cancel.clicked.connect(self.cancelar_edicion)

        self.btn_delete = QPushButton("Eliminar Material")
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete.setStyleSheet("QPushButton { color: #DC2626; border: 1px solid #DC2626; border-radius: 6px; padding: 8px 14px; background: transparent; font-weight: 600; } QPushButton:hover { background: #FEF2F2; }")
        self.btn_delete.clicked.connect(self.eliminar_material)

        actions_layout.addWidget(self.btn_save)
        actions_layout.addWidget(self.btn_cancel)
        actions_layout.addStretch()
        actions_layout.addWidget(self.btn_delete)

        self.right_layout.addLayout(actions_layout)

        right_scroll.setWidget(right_container)
        splitter.addWidget(right_scroll)

        # Dimensiones iniciales del splitter (58% / 42%)
        splitter.setSizes([580, 420])
        main_layout.addWidget(splitter)

        # Estado inicial del detalle (Modo Lectura / Formulario Limpio)
        self.limpiar_formulario()
        self.set_editing_mode(False)

    # --- CONTROL DE MODO LECTURA / EDICIÓN ---

    def set_editing_mode(self, enabled: bool):
        self.is_editing = enabled

        # Inputs del formulario
        self.txt_nombre.setEnabled(enabled)
        self.combo_unidad.setEnabled(enabled)
        self.spin_rendimiento.setEnabled(enabled)
        self.txt_descripcion.setEnabled(enabled)

        # Botones de subida
        self.btn_upload_photo.setEnabled(enabled)
        self.btn_remove_photo.setEnabled(enabled)
        self.btn_upload_ficha.setEnabled(enabled)
        self.btn_upload_estudio.setEnabled(enabled)

        # Re-renderizar estudios para mostrar/ocultar botones de eliminar
        self.renderizar_lista_estudios()

        # Visibilidad de botones principales
        if self.current_material and not enabled:
            # Seleccionado y en Modo Lectura
            self.btn_edit.setVisible(True)
            self.btn_save.setVisible(False)
            self.btn_cancel.setVisible(False)
            self.btn_delete.setVisible(True)
        elif enabled:
            # En Modo Edición (Creando o Modificando)
            self.btn_edit.setVisible(False)
            self.btn_save.setVisible(True)
            self.btn_cancel.setVisible(True)
            self.btn_delete.setVisible(not (self.current_material is None))
        else:
            # Sin material seleccionado
            self.btn_edit.setVisible(False)
            self.btn_save.setVisible(False)
            self.btn_cancel.setVisible(False)
            self.btn_delete.setVisible(False)

    def activar_edicion(self):
        if self.current_material:
            self.set_editing_mode(True)

    # --- LÓGICA DE CARGA Y FILTRADO ---

    def cargar_materiales(self, force_refresh: bool = False):
        if not self.supabase_client: return
        self.fetch_worker = FetchMaterialesWorker(self.supabase_client, force_refresh=force_refresh)
        self.fetch_worker.success.connect(self.on_cargar_materiales_success)
        self.fetch_worker.error.connect(lambda e: QMessageBox.warning(self, "Error", e))
        self.fetch_worker.start()

    def on_cargar_materiales_success(self, data):
        self.materiales_data = data
        self.filtrar_tabla()

    @staticmethod
    def _normalize_unidad(u: str) -> str:
        u = (u or "").strip().lower()
        mapping = {
            "tinetas": "tineta",
            "sacos": "saco",
            "litros": "litro",
            "unidades": "unidad",
            "un": "unidad",
            "m²": "m2",
            "m³": "m3",
            "kilos": "kg",
        }
        return mapping.get(u, u)

    def filtrar_tabla(self):
        query = self.txt_search.text().strip().lower()
        unidad_filtro = self.combo_filter_unidad.currentData() or self.combo_filter_unidad.currentText()
        if unidad_filtro == "Todas las Unidades": unidad_filtro = ""
        norm_filtro = self._normalize_unidad(unidad_filtro)

        filtered = []
        for mat in self.materiales_data:
            nombre = str(mat.get("nombre", "")).lower()
            desc = str(mat.get("descripcion", "")).lower()
            unidad = str(mat.get("unidad_medida", ""))

            match_text = (not query) or (query in nombre) or (query in desc)
            match_unidad = (not norm_filtro) or (self._normalize_unidad(unidad) == norm_filtro)

            if match_text and match_unidad:
                filtered.append(mat)

        self.popular_tabla(filtered)

    def popular_tabla(self, items):
        self.table.blockSignals(True)
        self.table.setRowCount(len(items))
        for i, mat in enumerate(items):
            nombre = str(mat.get("nombre", ""))
            unidad = str(mat.get("unidad_medida", ""))
            rend = str(mat.get("rendimiento_teorico_m2", 0))
            tiene_foto = "Sí" if mat.get("foto_url") else "No"

            estudios = mat.get("estudios_laboratorio") or []
            cnt_estudios = f"{len(estudios)}" if estudios else "0"

            item_nombre = QTableWidgetItem(nombre)
            item_nombre.setData(Qt.ItemDataRole.UserRole, mat)

            self.table.setItem(i, 0, item_nombre)
            self.table.setItem(i, 1, QTableWidgetItem(unidad))
            self.table.setItem(i, 2, QTableWidgetItem(rend))
            self.table.setItem(i, 3, QTableWidgetItem(tiene_foto))
            self.table.setItem(i, 4, QTableWidgetItem(cnt_estudios))

        self.table.blockSignals(False)

    def on_tabla_selection_changed(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return
        row = self.table.currentRow()
        item_nombre = self.table.item(row, 0)
        if item_nombre:
            mat_data = item_nombre.data(Qt.ItemDataRole.UserRole)
            self.cargar_detalle_material(mat_data)

    def cargar_detalle_material(self, mat):
        self.current_material = mat
        self.lbl_detail_title.setText(f"{mat.get('nombre', '')}")
        self.txt_nombre.setText(mat.get("nombre", ""))

        unidad = mat.get("unidad_medida", "")
        idx = self.combo_unidad.findText(unidad)
        if idx >= 0:
            self.combo_unidad.setCurrentIndex(idx)
        else:
            self.combo_unidad.setEditText(unidad)

        self.spin_rendimiento.setValue(float(mat.get("rendimiento_teorico_m2") or 0.0))
        self.txt_descripcion.setPlainText(mat.get("descripcion", "") or "")

        # Foto
        self.current_foto_url = mat.get("foto_url") or ""
        self.mostrar_foto_preview(self.current_foto_url)

        # Ficha PDF
        self.current_ficha_url = mat.get("ficha_tecnica_url") or ""
        if self.current_ficha_url:
            self.lbl_ficha_status.setText(f"Ficha cargada: {os.path.basename(self.current_ficha_url)}")
            self.btn_open_ficha.setEnabled(True)
        else:
            self.lbl_ficha_status.setText("No hay ficha técnica cargada.")
            self.btn_open_ficha.setEnabled(False)

        # Estudios de laboratorio
        self.current_estudios = mat.get("estudios_laboratorio") or []
        if isinstance(self.current_estudios, str):
            try: self.current_estudios = json.loads(self.current_estudios)
            except: self.current_estudios = []

        # Carga por defecto en MODO LECTURA
        self.set_editing_mode(False)

    def preparar_nuevo_material(self):
        self.table.clearSelection()
        self.limpiar_formulario()
        self.lbl_detail_title.setText("Crear Nuevo Material")
        self.set_editing_mode(True)
        self.txt_nombre.setFocus()

    def limpiar_formulario(self):
        self.current_material = None
        self.current_foto_url = ""
        self.current_ficha_url = ""
        self.current_estudios = []

        self.lbl_detail_title.setText("Seleccione o cree un Material")
        self.txt_nombre.clear()
        self.combo_unidad.setCurrentIndex(0)
        self.spin_rendimiento.setValue(0.0)
        self.txt_descripcion.clear()

        self.lbl_photo_preview.setText("Sin Imagen")
        self.lbl_photo_preview.setPixmap(QPixmap())

        self.lbl_ficha_status.setText("No hay ficha técnica cargada.")
        self.btn_open_ficha.setEnabled(False)

        self.set_editing_mode(False)

    # --- MANEJO DE ARCHIVOS Y FOTOS ---

    def mostrar_foto_preview(self, url):
        if not url:
            self.lbl_photo_preview.setText("Sin Imagen")
            self.lbl_photo_preview.setPixmap(QPixmap())
            return

        self.lbl_photo_preview.setText("Cargando...")
        self.img_worker = LoadImageWorker(url)
        self.img_worker.loaded.connect(self.on_foto_loaded)
        self.img_worker.error.connect(lambda e: self.lbl_photo_preview.setText("Error Imagen"))
        self.img_worker.start()

    def on_foto_loaded(self, data, url):
        pixmap = QPixmap()
        if pixmap.loadFromData(data):
            scaled = pixmap.scaled(self.lbl_photo_preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.lbl_photo_preview.setPixmap(scaled)
        else:
            self.lbl_photo_preview.setText("Formato Inválido")

    def seleccionar_foto(self):
        if not self.is_editing: return
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Foto del Material", "", "Imágenes (*.png *.jpg *.jpeg *.webp)")
        if not path: return
        self.upload_file(path, "foto")

    def quitar_foto(self):
        if not self.is_editing: return
        self.current_foto_url = ""
        self.lbl_photo_preview.setText("Sin Imagen")
        self.lbl_photo_preview.setPixmap(QPixmap())

    def seleccionar_ficha_pdf(self):
        if not self.is_editing: return
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Ficha Técnica (PDF)", "", "Documentos PDF (*.pdf)")
        if not path: return
        self.upload_file(path, "ficha")

    def abrir_documento(self, url_or_path: str, title: str = "Documento"):
        if not url_or_path:
            QMessageBox.warning(self, "Documento no disponible", "No hay ningún archivo o enlace disponible para abrir.")
            return
        dialog = DocumentViewerDialog(self, url_or_path, title)
        dialog.exec()


    def abrir_ficha_tecnica(self):
        if self.current_ficha_url:
            nombre_mat = self.current_material.get("nombre", "Material") if self.current_material else "Material"
            self.abrir_documento(self.current_ficha_url, f"Ficha Técnica - {nombre_mat}")

    def seleccionar_estudio_pdf(self):
        if not self.is_editing: return
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Estudio de Laboratorio (PDF)", "", "Documentos PDF (*.pdf)")
        if not path: return
        self.upload_file(path, "estudio")

    def upload_file(self, local_path, file_type):
        if not self.supabase_client:
            QMessageBox.warning(self, "Error", "Cliente de Supabase no disponible.")
            return

        filename = os.path.basename(local_path)
        self.up_worker = UploadMaterialFileWorker(self.supabase_client, local_path, file_type)
        self.up_worker.success.connect(lambda url, ftype, fn=filename: self.on_upload_success(url, ftype, fn))
        self.up_worker.error.connect(lambda err: QMessageBox.critical(self, "Error de Subida", err))
        self.up_worker.start()

    def on_upload_success(self, public_url, file_type, original_filename):
        if file_type == "foto":
            self.current_foto_url = public_url
            self.mostrar_foto_preview(public_url)
            QMessageBox.information(self, "Éxito", "Fotografía subida correctamente.")
        elif file_type == "ficha":
            self.current_ficha_url = public_url
            self.lbl_ficha_status.setText(f"Ficha cargada: {original_filename}")
            self.btn_open_ficha.setEnabled(True)
            QMessageBox.information(self, "Éxito", "Ficha técnica subida correctamente.")
        elif file_type == "estudio":
            nuevo_estudio = {
                "id": str(uuid.uuid4()),
                "nombre": original_filename,
                "url": public_url,
                "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            self.current_estudios.append(nuevo_estudio)
            self.renderizar_lista_estudios()
            QMessageBox.information(self, "Éxito", "Estudio de laboratorio subido correctamente.")

    def renderizar_lista_estudios(self):
        # Limpiar layout
        while self.estudios_list_layout.count():
            child = self.estudios_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self.current_estudios:
            lbl_empty = QLabel("No hay estudios de laboratorio adjuntos.")
            lbl_empty.setStyleSheet("color: #262B29; font-style: italic; padding: 4px 0;")
            self.estudios_list_layout.addWidget(lbl_empty)
            return

        for idx, est in enumerate(self.current_estudios):
            row_widget = QFrame()
            row_widget.setStyleSheet("QFrame { background: #F2EFE9; border-radius: 4px; padding: 4px 8px; border: 1px solid #D8D5CD; }")
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(6, 4, 6, 4)

            lbl_name = QLabel(f"{est.get('nombre', 'Estudio PDF')}")
            lbl_name.setStyleSheet("font-weight: 600; color: #1F2421;")

            btn_open = QPushButton("Abrir")
            btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_open.setStyleSheet("background: #3D523C; color: white; border-radius: 3px; padding: 3px 10px; font-weight: 600;")
            url_est = est.get("url", "")
            nombre_est = est.get("nombre", "Estudio de Laboratorio")
            btn_open.clicked.connect(lambda _, u=url_est, n=nombre_est: self.abrir_documento(u, n))

            row_layout.addWidget(lbl_name, stretch=1)
            row_layout.addWidget(btn_open)

            if self.is_editing:
                btn_del = QPushButton("✕")
                btn_del.setToolTip("Eliminar estudio")
                btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_del.setStyleSheet("background: transparent; color: #EF4444; border: none; font-weight: bold; padding: 2px 6px;")
                btn_del.clicked.connect(lambda _, i=idx: self.eliminar_estudio_item(i))
                row_layout.addWidget(btn_del)

            self.estudios_list_layout.addWidget(row_widget)

    def eliminar_estudio_item(self, index):

        if not self.is_editing: return
        if 0 <= index < len(self.current_estudios):
            del self.current_estudios[index]
            self.renderizar_lista_estudios()

    # --- GUARDAR Y ELIMINAR ---

    def guardar_material(self):
        if not self.is_editing: return

        nombre = self.txt_nombre.text().strip()
        unidad = self.combo_unidad.currentText().strip()
        rendimiento = self.spin_rendimiento.value()
        descripcion = self.txt_descripcion.toPlainText().strip()

        if not nombre or not unidad:
            QMessageBox.warning(self, "Datos Incompletos", "El nombre y la unidad de medida son obligatorios.")
            return

        is_new = self.current_material is None
        mat_id = self.current_material.get("id") if not is_new else str(uuid.uuid4())

        payload = {
            "id": mat_id,
            "nombre": nombre,
            "unidad_medida": unidad,
            "rendimiento_teorico_m2": rendimiento,
            "descripcion": descripcion,
            "foto_url": self.current_foto_url,
            "ficha_tecnica_url": self.current_ficha_url,
            "estudios_laboratorio": self.current_estudios
        }

        self.btn_save.setEnabled(False)
        self.btn_save.setText("Guardando...")
        self.save_worker = SaveMaterialWorker(self.supabase_client, payload, is_new=is_new)
        self.save_worker.success.connect(self.on_guardar_success)
        self.save_worker.error.connect(self.on_guardar_error)
        self.save_worker.start()

    def on_guardar_success(self, saved_mat, msg):
        self.btn_save.setEnabled(True)
        self.btn_save.setText("Guardar Cambios")
        QMessageBox.information(self, "Éxito", msg)
        self.cargar_materiales()
        self.cargar_detalle_material(saved_mat)

    def on_guardar_error(self, msg):
        self.btn_save.setEnabled(True)
        self.btn_save.setText("Guardar Cambios")
        QMessageBox.critical(self, "Error", msg)

    def cancelar_edicion(self):
        if self.current_material:
            self.cargar_detalle_material(self.current_material)
        else:
            self.limpiar_formulario()

    def eliminar_material(self):
        if not self.current_material: return

        nombre = self.current_material.get("nombre", "")
        confirm = QMessageBox.question(
            self, "Confirmar Eliminación",
            f"¿Estás seguro de que deseas eliminar el material '{nombre}'?\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            mat_id = self.current_material.get("id")
            self.del_worker = DeleteMaterialWorker(self.supabase_client, mat_id)
            self.del_worker.success.connect(self.on_eliminar_success)
            self.del_worker.error.connect(lambda e: QMessageBox.critical(self, "Error", e))
            self.del_worker.start()

    def on_eliminar_success(self, msg):
        QMessageBox.information(self, "Eliminado", msg)
        self.limpiar_formulario()
        self.cargar_materiales()
