from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QMessageBox, QFormLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QComboBox, QTabWidget, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QFrame, QSizePolicy, QSplitter, QGroupBox, QScrollArea,
    QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QDoubleValidator, QPixmap, QPainter, QPainterPath
from src.core.workers import (
    FetchJefesWorker, FetchObrasWorker, CreateJefeWorker, AssignJefeWorker,
    FetchTiposMaestroWorker, CreateTipoMaestroWorker, UpdateTipoMaestroWorker,
    DeleteTipoMaestroWorker, FetchMaestrosWorker, CreateMaestroWorker,
    AssignMaestroObraWorker, UpdateMaestroWorker, DeleteMaestroWorker,
    UploadFotoPerfilWorker, DownloadImageWorker
)
from src.ui.jefes_view import JefesContent


# ─────────────────────────────────────────────────────────────────────────────
# Diálogo para crear un nuevo tipo de maestro sobre la marcha
# ─────────────────────────────────────────────────────────────────────────────
class NuevoCargoDlg(QDialog):
    def __init__(self, supabase_client, parent=None):
        super().__init__(parent)
        self.supabase_client = supabase_client
        self.setWindowTitle("Nuevo Cargo / Tipo de Maestro")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        form = QFormLayout()
        self.nombre_input = QLineEdit()
        self.nombre_input.setPlaceholderText("Ej: Soldador, Carpintero...")
        self.sueldo_input = QDoubleSpinBox()
        self.sueldo_input.setRange(0, 9_999_999)
        self.sueldo_input.setDecimals(2)
        self.sueldo_input.setPrefix("$ ")
        self.sueldo_input.setSingleStep(1000)
        form.addRow("Nombre del Cargo:", self.nombre_input)
        form.addRow("Sueldo Diario:", self.sueldo_input)
        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_data(self):
        return self.nombre_input.text().strip(), self.sueldo_input.value()


# ─────────────────────────────────────────────────────────────────────────────
# Pestaña 2: Gestión de Maestros (Master-Detail)
# ─────────────────────────────────────────────────────────────────────────────
class MaestrosTab(QWidget):
    def __init__(self, supabase_client=None):
        super().__init__()
        self.supabase_client = supabase_client
        self._tipos = []
        self.maestros_data = []
        self.current_maestro = None
        self.current_foto_url = ""
        self.is_editing = False

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        # Encabezado + Botón Nuevo Maestro
        header_layout = QHBoxLayout()
        title = QLabel("Gestión de Maestros")
        title.setObjectName("TitleLabel")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1F2421;")

        self.btn_nuevo = QPushButton("+ Nuevo Maestro")
        self.btn_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nuevo.setStyleSheet("""
            QPushButton {
                background-color: #3D523C; color: white; border-radius: 6px;
                padding: 9px 18px; font-weight: 700; font-size: 13px; border: none;
            }
            QPushButton:hover { background-color: #2F402E; }
        """)
        self.btn_nuevo.clicked.connect(self.preparar_nuevo_maestro)

        header_layout.addWidget(title, stretch=1)
        header_layout.addWidget(self.btn_nuevo)
        main_layout.addLayout(header_layout)

        # Splitter principal
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # --- PANEL IZQUIERDO: Tabla y Búsqueda ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 10, 0)
        left_layout.setSpacing(10)

        # Búsqueda
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Buscar por nombre, RUT, teléfono o cargo...")
        self.txt_search.setClearButtonEnabled(True)
        self.txt_search.textChanged.connect(self.filtrar_tabla)
        left_layout.addWidget(self.txt_search)

        # Tabla
        self.table = QTableWidget()
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setMinimumSectionSize(110)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Nombre", "RUT / DNI", "Cargo", "Sueldo Diario", "Teléfono", "Estado"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
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
        self.right_layout.setContentsMargins(14, 14, 14, 14)
        self.right_layout.setSpacing(10)

        # ── 1. Tarjeta Superior de Perfil del Maestro Ultra Compacta ──
        header_card = QFrame()
        header_card.setObjectName("MaestroHeaderCard")
        header_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        header_card.setStyleSheet("""
            QFrame#MaestroHeaderCard {
                background-color: #FAF8F5;
                border: 1px solid #D8D5CD;
                border-radius: 8px;
            }
        """)
        header_card_layout = QHBoxLayout(header_card)
        header_card_layout.setContentsMargins(10, 6, 10, 6)
        header_card_layout.setSpacing(10)

        # Foto de perfil superior compacta circular (48x48 px)
        self.lbl_photo_preview = QLabel()
        self.lbl_photo_preview.setFixedSize(48, 48)
        self.lbl_photo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_photo_preview.setStyleSheet("""
            QLabel {
                border: 2px solid #D8D5CD;
                border-radius: 24px;
                background-color: #FFFFFF;
                color: #64748B;
                font-weight: bold;
                font-size: 10px;
            }
        """)
        header_card_layout.addWidget(self.lbl_photo_preview)

        # Info del Maestro
        info_layout = QVBoxLayout()
        info_layout.setSpacing(1)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.lbl_detail_title = QLabel("Seleccione o cree un Maestro")
        self.lbl_detail_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #1F2421; background: transparent; font-family: 'Space Grotesk', 'Work Sans', sans-serif;")
        self.lbl_detail_title.setWordWrap(True)

        self.lbl_detail_sub = QLabel("Personal Técnico de Faena")
        self.lbl_detail_sub.setStyleSheet("font-size: 11px; color: #64748B; background: transparent; font-weight: 500;")

        # Botones para seleccionar / quitar foto
        photo_btn_row = QHBoxLayout()
        photo_btn_row.setSpacing(4)

        self.btn_upload_foto = QPushButton("📷 Cambiar")
        self.btn_upload_foto.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_upload_foto.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF; color: #0369A1;
                border: 1px solid #BAE6FD; border-radius: 4px;
                padding: 2px 8px; font-weight: 600; font-size: 10px;
            }
            QPushButton:hover { background-color: #E0F2FE; }
            QPushButton:disabled { color: #94A3B8; border-color: #D8D5CD; background: #FAF8F5; }
        """)
        self.btn_upload_foto.clicked.connect(self._seleccionar_foto)
        self.btn_upload_foto.setVisible(False)

        self.btn_remove_foto = QPushButton("✕ Quitar")
        self.btn_remove_foto.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_remove_foto.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF; color: #DC2626;
                border: 1px solid #FECACA; border-radius: 4px;
                padding: 2px 6px; font-weight: 600; font-size: 10px;
            }
            QPushButton:hover { background-color: #FEE2E2; }
        """)
        self.btn_remove_foto.clicked.connect(self._quitar_foto)
        self.btn_remove_foto.setVisible(False)

        photo_btn_row.addWidget(self.btn_upload_foto)
        photo_btn_row.addWidget(self.btn_remove_foto)
        photo_btn_row.addStretch()

        info_layout.addWidget(self.lbl_detail_title)
        info_layout.addWidget(self.lbl_detail_sub)
        info_layout.addLayout(photo_btn_row)

        header_card_layout.addLayout(info_layout, stretch=1)

        # Botón Editar
        self.btn_edit = QPushButton("✏️ Editar")
        self.btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_edit.setStyleSheet("""
            QPushButton {
                background-color: #B85A3A; color: white; border-radius: 5px;
                padding: 5px 12px; font-weight: 700; font-size: 12px; border: none;
            }
            QPushButton:hover { background-color: #9A482D; }
        """)
        self.btn_edit.clicked.connect(self.activar_edicion)
        self.btn_edit.setVisible(False)
        header_card_layout.addWidget(self.btn_edit, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.right_layout.addWidget(header_card)

        # ── 2. Formulario de Datos Personales ──
        form_group = QGroupBox("Información Personal del Maestro")
        form_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        form_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold; font-size: 12px; color: #1F2421;
                border: 1px solid #D8D5CD; border-radius: 8px;
                margin-top: 10px; padding-top: 14px; padding-bottom: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin; subcontrol-position: top left;
                padding: 0 8px; left: 10px; color: #262B29;
            }
        """)
        form_layout = QFormLayout(form_group)
        form_layout.setVerticalSpacing(8)
        form_layout.setHorizontalSpacing(12)

        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: Pedro Soto")

        self.txt_rut = QLineEdit()
        self.txt_rut.setPlaceholderText("12.345.678-9")

        # Cargo + botón rápido "+"
        cargo_row = QHBoxLayout()
        self.combo_tipo = QComboBox()
        self.combo_tipo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn_nuevo_cargo = QPushButton("+")
        btn_nuevo_cargo.setFixedWidth(36)
        btn_nuevo_cargo.setToolTip("Agregar nuevo cargo sobre la marcha")
        btn_nuevo_cargo.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_nuevo_cargo.clicked.connect(self._nuevo_cargo_rapido)
        cargo_row.addWidget(self.combo_tipo)
        cargo_row.addWidget(btn_nuevo_cargo)

        self.txt_telefono = QLineEdit()
        self.txt_telefono.setPlaceholderText("+56 9 8765 4321")

        self.combo_estado = QComboBox()
        self.combo_estado.addItem("Activo", "activo")
        self.combo_estado.addItem("Inactivo", "inactivo")

        form_layout.addRow("Nombre Completo:", self.txt_nombre)
        form_layout.addRow("RUT / DNI:", self.txt_rut)
        form_layout.addRow("Cargo / Especialidad:", cargo_row)
        form_layout.addRow("Teléfono:", self.txt_telefono)
        form_layout.addRow("Estado Laboral:", self.combo_estado)
        self.right_layout.addWidget(form_group)

        # ── 3. Asignación a Obra ──
        asign_group = QGroupBox("Asignación de Obra Destino")
        asign_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        asign_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold; font-size: 12px; color: #1F2421;
                border: 1px solid #D8D5CD; border-radius: 8px;
                margin-top: 10px; padding-top: 14px; padding-bottom: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin; subcontrol-position: top left;
                padding: 0 8px; left: 10px; color: #262B29;
            }
        """)
        asign_layout = QFormLayout(asign_group)
        asign_layout.setVerticalSpacing(8)
        asign_layout.setHorizontalSpacing(12)

        self.combo_obra_asign = QComboBox()
        self.btn_asignar = QPushButton("Asignar a Obra")
        self.btn_asignar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_asignar.setStyleSheet("QPushButton { background-color: #3D523C; color: white; font-weight: 600; padding: 7px 14px; border-radius: 4px; } QPushButton:hover { background-color: #B85A3A; }")
        self.btn_asignar.clicked.connect(self._asignar_maestro)

        asign_layout.addRow("Obra Destino:", self.combo_obra_asign)
        asign_layout.addRow("", self.btn_asignar)
        self.right_layout.addWidget(asign_group)

        # ── 4. Botones de Acción ──
        actions_layout = QHBoxLayout()
        self.btn_save = QPushButton("Guardar Cambios")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setStyleSheet("background-color: #3D523C; color: white; border-radius: 6px; padding: 9px 18px; font-weight: 700;")
        self.btn_save.clicked.connect(self.guardar_maestro)

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setStyleSheet("background-color: #262B29; color: white; border-radius: 6px; padding: 9px 16px; font-weight: 600;")
        self.btn_cancel.clicked.connect(self.cancelar_edicion)

        self.btn_delete = QPushButton("🗑️ Eliminar Maestro")
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete.setStyleSheet("QPushButton { color: #DC2626; border: 1px solid #DC2626; border-radius: 6px; padding: 8px 14px; background: transparent; font-weight: 600; } QPushButton:hover { background: #FEF2F2; }")
        self.btn_delete.clicked.connect(self.eliminar_maestro)

        actions_layout.addWidget(self.btn_save)
        actions_layout.addWidget(self.btn_cancel)
        actions_layout.addStretch()
        actions_layout.addWidget(self.btn_delete)

        self.right_layout.addLayout(actions_layout)
        self.right_layout.addStretch()

        right_scroll.setWidget(right_container)
        splitter.addWidget(right_scroll)

        splitter.setSizes([580, 420])
        main_layout.addWidget(splitter)

        self.limpiar_formulario()
        self.set_editing_mode(False)

        if self.supabase_client:
            self.cargar_tipos_maestro()
            self.cargar_maestros()
            self.cargar_obras_combo()

    # --- MODO LECTURA / EDICIÓN ---

    def set_editing_mode(self, enabled: bool):
        self.is_editing = enabled

        self.txt_nombre.setEnabled(enabled)
        self.txt_rut.setEnabled(enabled)
        self.combo_tipo.setEnabled(enabled)
        self.txt_telefono.setEnabled(enabled)
        self.combo_estado.setEnabled(enabled)
        
        self.btn_upload_foto.setVisible(enabled)
        self.btn_remove_foto.setVisible(enabled and bool(self.current_foto_url))

        self.btn_save.setVisible(enabled)
        self.btn_cancel.setVisible(enabled)

        if enabled:
            self.btn_edit.setVisible(False)
            self.btn_delete.setVisible(False)
        else:
            self.btn_edit.setVisible(self.current_maestro is not None)
            self.btn_delete.setVisible(self.current_maestro is not None)

    def preparar_nuevo_maestro(self):
        self.table.clearSelection()
        self.limpiar_formulario()
        self.lbl_detail_title.setText("Crear Nuevo Maestro")
        self.lbl_detail_sub.setText("Completar datos personales y cargo")
        self.set_editing_mode(True)
        self.txt_nombre.setFocus()

    def limpiar_formulario(self):
        self.current_maestro = None
        self.current_foto_url = ""
        self.lbl_detail_title.setText("Seleccione o cree un Maestro")
        self.lbl_detail_sub.setText("Personal Técnico de Faena")

        self.txt_nombre.clear()
        self.txt_rut.clear()
        self.txt_telefono.clear()
        self.actualizar_preview_foto("")

        self.set_editing_mode(False)

    def activar_edicion(self):
        if not self.current_maestro:
            return
        self.lbl_detail_title.setText(f"Editando: {self.current_maestro.get('nombre', '')}")
        self.set_editing_mode(True)

    def cancelar_edicion(self):
        if self.current_maestro:
            self.cargar_detalle_maestro(self.current_maestro)
        else:
            self.limpiar_formulario()

    def cargar_tipos_maestro(self):
        if not self.supabase_client:
            return
        self._w_tipos = FetchTiposMaestroWorker(self.supabase_client)
        self._w_tipos.success.connect(self._on_tipos_loaded)
        self._w_tipos.start()

    def _on_tipos_loaded(self, tipos):
        self._tipos = tipos
        self.combo_tipo.clear()
        for t in tipos:
            self.combo_tipo.addItem(t["nombre"], t["id"])

    def cargar_maestros(self):
        if not self.supabase_client:
            return
        self._w_maestros = FetchMaestrosWorker(self.supabase_client)
        self._w_maestros.success.connect(self._on_maestros_loaded)
        self._w_maestros.error.connect(lambda e: QMessageBox.warning(self, "Error", e))
        self._w_maestros.start()

    def _on_maestros_loaded(self, maestros):
        self.maestros_data = maestros
        self.filtrar_tabla()

    def filtrar_tabla(self):
        search = self.txt_search.text().strip().lower()

        filtered = []
        for m in self.maestros_data:
            nombre = str(m.get("nombre", "")).lower()
            rut = str(m.get("rut_dni", "")).lower()
            telef = str(m.get("telefono", "")).lower()
            cargo = ""
            if isinstance(m.get("tipos_maestro"), dict):
                cargo = str(m["tipos_maestro"].get("nombre", "")).lower()

            match_search = not search or (search in nombre or search in rut or search in telef or search in cargo)
            if match_search:
                filtered.append(m)

        self.popular_tabla(filtered)

    def popular_tabla(self, items):
        self.table.blockSignals(True)
        self.table.setRowCount(len(items))
        for i, m in enumerate(items):
            nombre = m.get("nombre", "")
            rut = m.get("rut_dni", "")
            telefono = m.get("telefono", "")
            estado = m.get("estado", "")

            tipo_nombre = ""
            sueldo = ""
            if isinstance(m.get("tipos_maestro"), dict):
                tipo_nombre = m["tipos_maestro"].get("nombre", "")
                sueldo = f"$ {m['tipos_maestro'].get('sueldo_diario', 0.0):,.0f}"

            item_nombre = QTableWidgetItem(nombre)
            item_nombre.setData(Qt.ItemDataRole.UserRole, m)

            self.table.setItem(i, 0, item_nombre)
            self.table.setItem(i, 1, QTableWidgetItem(rut))
            self.table.setItem(i, 2, QTableWidgetItem(tipo_nombre))
            self.table.setItem(i, 3, QTableWidgetItem(sueldo))
            self.table.setItem(i, 4, QTableWidgetItem(telefono))
            self.table.setItem(i, 5, QTableWidgetItem(estado))

        self.table.blockSignals(False)

    def on_tabla_selection_changed(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return
        row = self.table.currentRow()
        item_nombre = self.table.item(row, 0)
        if item_nombre:
            maestro_data = item_nombre.data(Qt.ItemDataRole.UserRole)
            self.cargar_detalle_maestro(maestro_data)

    def cargar_detalle_maestro(self, m):
        self.current_maestro = m
        nombre = m.get('nombre', '') or "Sin Nombre"
        cargo = ""
        if isinstance(m.get("tipos_maestro"), dict):
            cargo = m["tipos_maestro"].get("nombre", "")
        estado = (m.get("estado") or "activo").capitalize()

        self.lbl_detail_title.setText(nombre)
        self.lbl_detail_sub.setText(f"{cargo} • {estado}" if cargo else f"Personal • {estado}")
        self.txt_nombre.setText(nombre)
        self.txt_rut.setText(m.get("rut_dni", "") or "")
        self.txt_telefono.setText(m.get("telefono", "") or "")
        self.current_foto_url = m.get("foto_perfil_url") or m.get("foto_url") or ""

        # Seleccionar cargo en combo
        tipo_id = m.get("tipo_maestro_id")
        idx = self.combo_tipo.findData(tipo_id)
        if idx >= 0:
            self.combo_tipo.setCurrentIndex(idx)

        # Seleccionar estado en combo
        estado_val = (m.get("estado") or "activo").lower()
        idx_est = self.combo_estado.findData(estado_val)
        if idx_est >= 0:
            self.combo_estado.setCurrentIndex(idx_est)

        self.actualizar_preview_foto(self.current_foto_url)
        self.set_editing_mode(False)

    def actualizar_preview_foto(self, url):
        url = (url or "").strip()
        self.current_foto_url = url
        if not url:
            self.lbl_photo_preview.setText("Sin Foto")
            self.lbl_photo_preview.setPixmap(QPixmap())
            self.btn_remove_foto.setVisible(False)
            return

        self.btn_remove_foto.setVisible(self.is_editing)
        self.lbl_photo_preview.setText("Cargando...")
        self.lbl_photo_preview.setPixmap(QPixmap())
        self._w_img = DownloadImageWorker(url)
        self._w_img.success.connect(self._on_preview_downloaded)
        self._w_img.error.connect(lambda _: self.lbl_photo_preview.setText("Foto"))
        self._w_img.start()

    def _on_preview_downloaded(self, url: str, content: bytes):
        if url != self.current_foto_url:
            return
        pix = QPixmap()
        if pix.loadFromData(content):
            scaled = pix.scaled(
                self.lbl_photo_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            target = QPixmap(self.lbl_photo_preview.size())
            target.fill(Qt.GlobalColor.transparent)
            painter = QPainter(target)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            path = QPainterPath()
            path.addEllipse(0, 0, self.lbl_photo_preview.width(), self.lbl_photo_preview.height())
            painter.setClipPath(path)
            x = (self.lbl_photo_preview.width() - scaled.width()) // 2
            y = (self.lbl_photo_preview.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            painter.end()
            self.lbl_photo_preview.setText("")
            self.lbl_photo_preview.setPixmap(target)
        else:
            self.lbl_photo_preview.setText("Foto")

    # --- FOTO DEL MAESTRO: subida y eliminación ---

    def _quitar_foto(self):
        self.current_foto_url = ""
        self.actualizar_preview_foto("")

    def _seleccionar_foto(self):
        """Abre el selector de archivos y sube la foto seleccionada al Storage."""
        if not self.supabase_client:
            QMessageBox.warning(self, "Error", "Sin conexión a Supabase.")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar foto del maestro",
            "",
            "Imágenes (*.jpg *.jpeg *.png *.webp)"
        )
        if not file_path:
            return

        self.btn_upload_foto.setEnabled(False)
        self.btn_upload_foto.setText("⏳ Subiendo...")

        self._w_upload = UploadFotoPerfilWorker(
            self.supabase_client, file_path, subfolder="personal"
        )
        self._w_upload.success.connect(self._on_foto_subida)
        self._w_upload.error.connect(self._on_foto_error)
        self._w_upload.start()

    def _on_foto_subida(self, url: str):
        self.btn_upload_foto.setEnabled(True)
        self.btn_upload_foto.setText("📷 Cambiar Foto")
        self.current_foto_url = url
        self.actualizar_preview_foto(url)

    def _on_foto_error(self, err: str):
        self.btn_upload_foto.setEnabled(True)
        self.btn_upload_foto.setText("📷 Cambiar Foto")
        QMessageBox.critical(self, "Error al subir foto", err)

    def cargar_obras_combo(self):
        if not self.supabase_client:
            return
        self._w_obras = FetchObrasWorker(self.supabase_client)
        self._w_obras.success.connect(self._on_obras_loaded)
        self._w_obras.start()

    def _on_obras_loaded(self, obras):
        self.combo_obra_asign.clear()
        for o in obras:
            self.combo_obra_asign.addItem(o["nombre"], o["id"])

    def _nuevo_cargo_rapido(self):
        dlg = NuevoCargoDlg(self.supabase_client, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            nombre, sueldo = dlg.get_data()
            if not nombre:
                QMessageBox.warning(self, "Error", "El nombre del cargo no puede estar vacío.")
                return
            self._w_create_tipo = CreateTipoMaestroWorker(self.supabase_client, nombre, sueldo)
            self._w_create_tipo.success.connect(lambda msg: (
                QMessageBox.information(self, "Éxito", msg),
                self.cargar_tipos_maestro()
            ))
            self._w_create_tipo.error.connect(lambda e: QMessageBox.critical(self, "Error", e))
            self._w_create_tipo.start()

    def guardar_maestro(self):
        nombre = self.txt_nombre.text().strip()
        rut = self.txt_rut.text().strip()
        tipo_id = self.combo_tipo.currentData()
        telefono = self.txt_telefono.text().strip()
        estado = self.combo_estado.currentData()
        foto_url = self.current_foto_url.strip()

        if not nombre or not tipo_id:
            QMessageBox.warning(self, "Error", "Nombre y Cargo son obligatorios.")
            return

        if not self.supabase_client:
            QMessageBox.warning(self, "Error", "Sin conexión a Supabase.")
            return

        self.btn_save.setEnabled(False)
        self.btn_save.setText("Guardando...")

        if self.current_maestro is None:
            # Crear nuevo Maestro
            self._w_save = CreateMaestroWorker(
                self.supabase_client, nombre, rut, tipo_id, telefono, foto_url
            )
            self._w_save.success.connect(self._on_guardar_success)
            self._w_save.error.connect(self._on_guardar_error)
            self._w_save.start()
        else:
            # Actualizar existente
            maestro_id = self.current_maestro.get("id")
            self._w_save = UpdateMaestroWorker(
                self.supabase_client, maestro_id, nombre, rut, tipo_id, telefono, estado, foto_url
            )
            self._w_save.success.connect(self._on_guardar_success)
            self._w_save.error.connect(self._on_guardar_error)
            self._w_save.start()

    def _on_guardar_success(self, msg):
        self.btn_save.setEnabled(True)
        self.btn_save.setText("Guardar Cambios")
        QMessageBox.information(self, "Éxito", msg)
        self.cargar_maestros()

    def _on_guardar_error(self, err):
        self.btn_save.setEnabled(True)
        self.btn_save.setText("Guardar Cambios")
        QMessageBox.critical(self, "Error", err)

    def eliminar_maestro(self):
        if not self.current_maestro:
            return
        reply = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Está seguro de eliminar al Maestro '{self.current_maestro.get('nombre')}'?\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            maestro_id = self.current_maestro.get("id")
            self._w_del = DeleteMaestroWorker(self.supabase_client, maestro_id)
            self._w_del.success.connect(self._on_eliminar_success)
            self._w_del.error.connect(lambda e: QMessageBox.critical(self, "Error", e))
            self._w_del.start()

    def _on_eliminar_success(self, msg):
        QMessageBox.information(self, "Éxito", msg)
        self.limpiar_formulario()
        self.cargar_maestros()

    def _asignar_maestro(self):
        if not self.current_maestro:
            QMessageBox.warning(self, "Seleccionar Maestro", "Seleccione primero a un Maestro para asignarlo.")
            return
        maestro_id = self.current_maestro.get("id")
        obra_id = self.combo_obra_asign.currentData()

        if not maestro_id or not obra_id:
            QMessageBox.warning(self, "Error", "Seleccione un maestro y una obra.")
            return

        self.btn_asignar.setEnabled(False)
        self.btn_asignar.setText("Asignando...")
        self._w_asign = AssignMaestroObraWorker(self.supabase_client, obra_id, maestro_id)
        self._w_asign.success.connect(lambda msg: (
            self.btn_asignar.setEnabled(True),
            self.btn_asignar.setText("Asignar a Obra"),
            QMessageBox.information(self, "Éxito", msg)
        ))
        self._w_asign.error.connect(lambda e: (
            self.btn_asignar.setEnabled(True),
            self.btn_asignar.setText("Asignar a Obra"),
            QMessageBox.critical(self, "Error", e)
        ))
        self._w_asign.start()


# ─────────────────────────────────────────────────────────────────────────────
# Pestaña 3: Cargos y Tarifas Diarias
# ─────────────────────────────────────────────────────────────────────────────
class CargosTab(QWidget):
    def __init__(self, supabase_client=None):
        super().__init__()
        self.supabase_client = supabase_client
        self._selected_id = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Cargos y Tarifas Diarias")
        title.setObjectName("TitleLabel")
        layout.addWidget(title)

        # ── Formulario ──
        form = QFormLayout()
        form.setSpacing(10)
        self.nombre_input = QLineEdit()
        self.nombre_input.setPlaceholderText("Nombre del cargo (ej: Aplicador)")
        self.sueldo_input = QDoubleSpinBox()
        self.sueldo_input.setRange(0, 9_999_999)
        self.sueldo_input.setDecimals(2)
        self.sueldo_input.setPrefix("$ ")
        self.sueldo_input.setSingleStep(1000)
        form.addRow("Nombre del Cargo:", self.nombre_input)
        form.addRow("Sueldo Diario:", self.sueldo_input)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        self.btn_crear = QPushButton("Crear Cargo")
        self.btn_crear.setObjectName("PrimaryButton")
        self.btn_crear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_crear.clicked.connect(self._guardar)

        self.btn_nuevo = QPushButton("Nuevo")
        self.btn_nuevo.setObjectName("SecondaryButton")
        self.btn_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nuevo.clicked.connect(self._reset_form)

        self.btn_eliminar = QPushButton("Eliminar Cargo")
        self.btn_eliminar.setEnabled(False)
        self.btn_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_eliminar.setStyleSheet(
            "QPushButton { color: #DC2626; border: 1px solid #DC2626; border-radius: 6px; "
            "padding: 8px 16px; background: transparent; } "
            "QPushButton:hover { background: #FEF2F2; } "
            "QPushButton:disabled { color: #D8D5CD; border-color: #D8D5CD; }"
        )
        self.btn_eliminar.clicked.connect(self._eliminar)

        btn_row.addWidget(self.btn_crear)
        btn_row.addWidget(self.btn_nuevo)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_eliminar)
        layout.addLayout(btn_row)

        # ── Tabla ──
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        sub = QLabel("Cargos Registrados")
        sub.setStyleSheet("font-weight: bold; font-size: 16px; color: #1F2421;")
        layout.addWidget(sub)

        self.table = QTableWidget()
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setMinimumSectionSize(110)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Nombre del Cargo", "Sueldo Diario"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.table)

        if self.supabase_client:
            self.cargar_cargos()

    def cargar_cargos(self):
        if not self.supabase_client:
            return
        self._w = FetchTiposMaestroWorker(self.supabase_client)
        self._w.success.connect(self._on_loaded)
        self._w.error.connect(lambda e: QMessageBox.warning(self, "Error", e))
        self._w.start()

    def _on_loaded(self, tipos):
        self._tipos_data = tipos
        self.table.setRowCount(len(tipos))
        for i, t in enumerate(tipos):
            self.table.setItem(i, 0, QTableWidgetItem(t.get("nombre", "")))
            sueldo_item = QTableWidgetItem(f"$ {t.get('sueldo_diario', 0.0):,.2f}")
            sueldo_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 1, sueldo_item)

    def _on_selection_changed(self):
        rows = self.table.selectedItems()
        if rows:
            row = self.table.currentRow()
            if row >= 0 and hasattr(self, '_tipos_data') and row < len(self._tipos_data):
                t = self._tipos_data[row]
                self._selected_id = t.get("id")
                self.nombre_input.setText(t.get("nombre", ""))
                self.sueldo_input.setValue(float(t.get("sueldo_diario", 0)))
                self.btn_crear.setText("Actualizar Cargo")
                self.btn_eliminar.setEnabled(True)

    def _reset_form(self):
        self._selected_id = None
        self.nombre_input.clear()
        self.sueldo_input.setValue(0)
        self.btn_crear.setText("Crear Cargo")
        self.btn_eliminar.setEnabled(False)
        self.table.clearSelection()

    def _guardar(self):
        nombre = self.nombre_input.text().strip()
        sueldo = self.sueldo_input.value()
        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre del cargo es obligatorio.")
            return
        if sueldo < 0:
            QMessageBox.warning(self, "Error", "El sueldo diario no puede ser negativo.")
            return
        if not self.supabase_client:
            return

        self.btn_crear.setEnabled(False)
        if self._selected_id:
            self._w_save = UpdateTipoMaestroWorker(self.supabase_client, self._selected_id, nombre, sueldo)
        else:
            self._w_save = CreateTipoMaestroWorker(self.supabase_client, nombre, sueldo)

        self._w_save.success.connect(lambda msg: (
            self.btn_crear.setEnabled(True),
            QMessageBox.information(self, "Éxito", msg),
            self._reset_form(),
            self.cargar_cargos()
        ))
        self._w_save.error.connect(lambda e: (
            self.btn_crear.setEnabled(True),
            QMessageBox.critical(self, "Error", e)
        ))
        self._w_save.start()

    def _eliminar(self):
        if not self._selected_id:
            return
        reply = QMessageBox.question(
            self, "Confirmar",
            "¿Eliminar este cargo? Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._w_del = DeleteTipoMaestroWorker(self.supabase_client, self._selected_id)
        self._w_del.success.connect(lambda msg: (
            QMessageBox.information(self, "Éxito", msg),
            self._reset_form(),
            self.cargar_cargos()
        ))
        self._w_del.error.connect(lambda e: QMessageBox.critical(self, "Error", e))
        self._w_del.start()


# ─────────────────────────────────────────────────────────────────────────────
# Vista principal: Control de Personal (3 pestañas)
# ─────────────────────────────────────────────────────────────────────────────
class ControlPersonalContent(QWidget):
    def __init__(self, supabase_client=None):
        super().__init__()
        self.supabase_client = supabase_client

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # Pestaña 1: Supervisores (reutilizar vista existente)
        self.jefes_tab = JefesContent(supabase_client)
        self.tabs.addTab(self.jefes_tab, "Supervisores")

        # Pestaña 2: Maestros
        self.maestros_tab = MaestrosTab(supabase_client)
        self.tabs.addTab(self.maestros_tab, "Maestros")

        # Pestaña 3: Cargos y Tarifas
        self.cargos_tab = CargosTab(supabase_client)
        self.tabs.addTab(self.cargos_tab, "Cargos y Tarifas Diarias")

        layout.addWidget(self.tabs)

    def cargar_datos(self):
        """Recargar datos de todas las pestañas."""
        self.jefes_tab.cargar_tabla()
        self.jefes_tab.cargar_combos()
        self.maestros_tab.cargar_tipos_maestro()
        self.maestros_tab.cargar_maestros()
        self.maestros_tab.cargar_obras_combo()
        self.cargos_tab.cargar_cargos()
