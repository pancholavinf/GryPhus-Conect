from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QMessageBox, QFormLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QComboBox, QSplitter, QGroupBox, QScrollArea, QFrame,
    QFileDialog, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath
from src.core.workers import (
    FetchJefesWorker, FetchObrasWorker, CreateJefeWorker, AssignJefeWorker,
    UpdateJefeWorker, DeleteJefeWorker, UploadFotoPerfilWorker
)
import requests


class JefesContent(QWidget):
    def __init__(self, supabase_client=None):
        super().__init__()
        self.supabase_client = supabase_client
        self.jefes_data = []
        self.current_jefe = None
        self.current_foto_url = ""
        self.is_editing = False

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(15)

        # Encabezado Principal + Botón Nuevo Supervisor
        header_layout = QHBoxLayout()
        title = QLabel("Gestión de Supervisores")
        title.setObjectName("TitleLabel")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1F2421;")

        self.btn_nuevo = QPushButton("+ Nuevo Supervisor")
        self.btn_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nuevo.setStyleSheet("""
            QPushButton {
                background-color: #3D523C; color: white; border-radius: 6px;
                padding: 9px 18px; font-weight: 700; font-size: 13px; border: none;
            }
            QPushButton:hover { background-color: #2F402E; }
        """)
        self.btn_nuevo.clicked.connect(self.preparar_nuevo_jefe)

        header_layout.addWidget(title, stretch=1)
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

        # Búsqueda
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Buscar por nombre, teléfono o rol...")
        self.txt_search.setClearButtonEnabled(True)
        self.txt_search.textChanged.connect(self.filtrar_tabla)
        left_layout.addWidget(self.txt_search)

        # Tabla
        self.table = QTableWidget()
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setMinimumSectionSize(110)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Nombre", "Rol", "Teléfono", "Foto Perfil"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
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

        # ── 1. Tarjeta Superior de Perfil Ultra Compacta (Foto 48x48 + Datos clave + Botón Editar) ──
        header_card = QFrame()
        header_card.setObjectName("ProfileHeaderCard")
        header_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        header_card.setStyleSheet("""
            QFrame#ProfileHeaderCard {
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

        # Info resumida del Supervisor
        info_layout = QVBoxLayout()
        info_layout.setSpacing(1)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.lbl_detail_title = QLabel("Seleccione o cree un Supervisor")
        self.lbl_detail_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #1F2421; background: transparent; font-family: 'Space Grotesk', 'Work Sans', sans-serif;")
        self.lbl_detail_title.setWordWrap(True)

        self.lbl_detail_sub = QLabel("Supervisor de Faena")
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

        # ── 2. Formulario de Datos Básicos (con títulos claros y espaciados) ──
        form_group = QGroupBox("Información del Supervisor")
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
        self.txt_nombre.setPlaceholderText("Ej: Juan Pérez")

        self.txt_rut = QLineEdit()
        self.txt_rut.setPlaceholderText("Ej: 12.345.678-9")

        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("correo@empresa.cl")

        self.lbl_pwd_tag = QLabel("Contraseña:")
        self.txt_password = QLineEdit()
        self.txt_password.setPlaceholderText("Contraseña para inicio de sesión")
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)

        self.txt_telefono = QLineEdit()
        self.txt_telefono.setPlaceholderText("+56 9 1234 5678")

        self.lbl_rol_val = QLabel("Supervisor")
        self.lbl_rol_val.setStyleSheet("font-weight: bold; color: #262B29;")

        form_layout.addRow("Nombre Completo:", self.txt_nombre)
        form_layout.addRow("RUT / DNI:", self.txt_rut)
        form_layout.addRow("Correo Electrónico:", self.txt_email)
        form_layout.addRow(self.lbl_pwd_tag, self.txt_password)
        form_layout.addRow("Teléfono:", self.txt_telefono)
        form_layout.addRow("Rol en Sistema:", self.lbl_rol_val)
        self.right_layout.addWidget(form_group)

        # ── 3. Sección Asignación de Obra ──
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

        self.combo_obras = QComboBox()
        self.btn_asignar = QPushButton("Asignar a Obra")
        self.btn_asignar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_asignar.setStyleSheet("QPushButton { background-color: #3D523C; color: white; font-weight: 600; padding: 7px 14px; border-radius: 4px; } QPushButton:hover { background-color: #B85A3A; }")
        self.btn_asignar.clicked.connect(self.asignar_jefe_obra)

        asign_layout.addRow("Obra Destino:", self.combo_obras)
        asign_layout.addRow("", self.btn_asignar)
        self.right_layout.addWidget(asign_group)

        # ── 4. Botones de Acción ──
        actions_layout = QHBoxLayout()
        self.btn_save = QPushButton("Guardar Cambios")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setStyleSheet("background-color: #3D523C; color: white; border-radius: 6px; padding: 9px 18px; font-weight: 700;")
        self.btn_save.clicked.connect(self.guardar_jefe)

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setStyleSheet("background-color: #262B29; color: white; border-radius: 6px; padding: 9px 16px; font-weight: 600;")
        self.btn_cancel.clicked.connect(self.cancelar_edicion)

        self.btn_delete = QPushButton("🗑️ Eliminar Supervisor")
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete.setStyleSheet("QPushButton { color: #DC2626; border: 1px solid #DC2626; border-radius: 6px; padding: 8px 14px; background: transparent; font-weight: 600; } QPushButton:hover { background: #FEF2F2; }")
        self.btn_delete.clicked.connect(self.eliminar_jefe)

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
            self.cargar_tabla()
            self.cargar_combos()

    # --- MODO LECTURA / EDICIÓN ---

    def set_editing_mode(self, enabled: bool):
        self.is_editing = enabled

        self.txt_nombre.setEnabled(enabled)
        self.txt_rut.setEnabled(enabled)
        # Si es un jefe existente, el email se deshabilita en edición para evitar inconsistencias de Auth
        self.txt_email.setEnabled(enabled and self.current_jefe is None)
        self.txt_password.setEnabled(enabled and self.current_jefe is None)
        self.lbl_pwd_tag.setVisible(self.current_jefe is None)
        self.txt_password.setVisible(self.current_jefe is None)
        self.txt_telefono.setEnabled(enabled)
        
        self.btn_upload_foto.setVisible(enabled)
        self.btn_remove_foto.setVisible(enabled and bool(self.current_foto_url))

        self.btn_save.setVisible(enabled)
        self.btn_cancel.setVisible(enabled)

        if enabled:
            self.btn_edit.setVisible(False)
            self.btn_delete.setVisible(False)
        else:
            self.btn_edit.setVisible(self.current_jefe is not None)
            self.btn_delete.setVisible(self.current_jefe is not None)

    def preparar_nuevo_jefe(self):
        self.table.clearSelection()
        self.limpiar_formulario()
        self.lbl_detail_title.setText("Crear Nuevo Supervisor")
        self.lbl_detail_sub.setText("Completar datos de acceso y perfil")
        self.set_editing_mode(True)
        self.txt_nombre.setFocus()

    def limpiar_formulario(self):
        self.current_jefe = None
        self.current_foto_url = ""
        self.lbl_detail_title.setText("Seleccione o cree un Supervisor")
        self.lbl_detail_sub.setText("Supervisor de Faena")

        self.txt_nombre.clear()
        self.txt_rut.clear()
        self.txt_email.clear()
        self.txt_password.clear()
        self.txt_telefono.clear()
        self.actualizar_preview_foto("")

        self.set_editing_mode(False)

    def activar_edicion(self):
        if not self.current_jefe:
            return
        self.lbl_detail_title.setText(f"Editando: {self.current_jefe.get('nombre', '')}")
        self.set_editing_mode(True)

    def cancelar_edicion(self):
        if self.current_jefe:
            self.cargar_detalle_jefe(self.current_jefe)
        else:
            self.limpiar_formulario()

    def cargar_tabla(self):
        if not self.supabase_client:
            return
        self.fetch_worker = FetchJefesWorker(self.supabase_client)
        self.fetch_worker.success.connect(self.on_cargar_tabla_success)
        self.fetch_worker.error.connect(lambda e: QMessageBox.warning(self, "Error", e))
        self.fetch_worker.start()

    def on_cargar_tabla_success(self, data):
        self.jefes_data = data
        self.filtrar_tabla()

    def filtrar_tabla(self):
        search = self.txt_search.text().strip().lower()

        filtered = []
        for j in self.jefes_data:
            nombre = str(j.get("nombre", "")).lower()
            email = str(j.get("email", "")).lower()
            telef = str(j.get("telefono", "")).lower()
            rol = str(j.get("rol", "")).lower()

            match_search = not search or (search in nombre or search in email or search in telef or search in rol)
            if match_search:
                filtered.append(j)

        self.popular_tabla(filtered)

    def popular_tabla(self, items):
        self.table.blockSignals(True)
        self.table.setRowCount(len(items))
        for i, j in enumerate(items):
            nombre = str(j.get("nombre", ""))
            rol_raw = str(j.get("rol", ""))
            # Mapeo local: valores de BD → etiqueta visual
            rol = "Supervisor" if rol_raw.strip().lower() in ("jefe_obra", "jefe obra", "supervisor") else rol_raw
            telefono = str(j.get("telefono", ""))
            foto = "Sí" if j.get("foto_perfil_url") else "No"

            item_nombre = QTableWidgetItem(nombre)
            item_nombre.setData(Qt.ItemDataRole.UserRole, j)

            self.table.setItem(i, 0, item_nombre)
            self.table.setItem(i, 1, QTableWidgetItem(rol))
            self.table.setItem(i, 2, QTableWidgetItem(telefono))
            self.table.setItem(i, 3, QTableWidgetItem(foto))

        self.table.blockSignals(False)

    def on_tabla_selection_changed(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            return
        row = self.table.currentRow()
        item_nombre = self.table.item(row, 0)
        if item_nombre:
            jefe_data = item_nombre.data(Qt.ItemDataRole.UserRole)
            self.cargar_detalle_jefe(jefe_data)

    def cargar_detalle_jefe(self, jefe):
        self.current_jefe = jefe
        nombre = jefe.get('nombre', '') or "Sin Nombre"
        email = jefe.get('email', '') or ""
        self.lbl_detail_title.setText(nombre)
        self.lbl_detail_sub.setText(f"Supervisor • {email}" if email else "Supervisor de Faena")
        self.txt_nombre.setText(nombre)
        self.txt_rut.setText(jefe.get("rut_dni", "") or "")
        self.txt_email.setText(email)
        self.txt_telefono.setText(jefe.get("telefono", "") or "")
        self.current_foto_url = jefe.get("foto_perfil_url", "") or ""
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
        try:
            res = requests.get(url, timeout=3)
            if res.status_code == 200:
                pix = QPixmap()
                if pix.loadFromData(res.content):
                    scaled = pix.scaled(
                        self.lbl_photo_preview.size(),
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    # Recorte circular
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
                    return
        except Exception:
            pass
        self.lbl_photo_preview.setText("Foto")

    # --- FOTO DE PERFIL: subida y eliminación ---

    def _quitar_foto(self):
        self.current_foto_url = ""
        self.actualizar_preview_foto("")

    def _seleccionar_foto(self):
        """Abre diálogo para seleccionar imagen local y la sube al bucket 'accuratek-data' (carpeta personal/)."""
        if not self.supabase_client:
            QMessageBox.warning(self, "Error", "Sin conexión a Supabase.")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar foto de perfil",
            "",
            "Imágenes (*.jpg *.jpeg *.png *.webp)"
        )
        if not file_path:
            return  # usuario canceló

        self.btn_upload_foto.setEnabled(False)
        self.btn_upload_foto.setText("⏳ Subiendo...")

        self.upload_worker = UploadFotoPerfilWorker(self.supabase_client, file_path, subfolder="personal")
        self.upload_worker.success.connect(self._on_foto_subida)
        self.upload_worker.error.connect(self._on_foto_error)
        self.upload_worker.start()

    def _on_foto_subida(self, url: str):
        """Callback cuando la foto se sube correctamente."""
        self.btn_upload_foto.setEnabled(True)
        self.btn_upload_foto.setText("📷 Cambiar Foto")
        self.current_foto_url = url
        self.actualizar_preview_foto(url)

    def _on_foto_error(self, msg: str):
        self.btn_upload_foto.setEnabled(True)
        self.btn_upload_foto.setText("📷 Cambiar Foto")
        QMessageBox.critical(self, "Error al subir foto", msg)

    def cargar_combos(self):
        if not self.supabase_client:
            return
        self.combo_obras.clear()
        self.fetch_obras_worker = FetchObrasWorker(self.supabase_client)
        self.fetch_obras_worker.success.connect(self.on_cargar_obras_success)
        self.fetch_obras_worker.start()

    def on_cargar_obras_success(self, obras):
        self.combo_obras.clear()
        for o in obras:
            self.combo_obras.addItem(o["nombre"], o["id"])

    def guardar_jefe(self):
        nombre = self.txt_nombre.text().strip()
        rut = self.txt_rut.text().strip()
        email = self.txt_email.text().strip()
        password = self.txt_password.text().strip()
        telefono = self.txt_telefono.text().strip()
        foto_url = self.current_foto_url.strip()

        if not nombre:
            QMessageBox.warning(self, "Campos obligatorios", "Por favor ingrese el Nombre Completo.")
            return

        if not self.supabase_client:
            QMessageBox.warning(self, "Error", "Sin conexión a Supabase.")
            return

        self.btn_save.setEnabled(False)
        self.btn_save.setText("Guardando...")

        if self.current_jefe is None:
            # Crear nuevo Jefe
            if not email or not password:
                self.btn_save.setEnabled(True)
                self.btn_save.setText("Guardar Cambios")
                QMessageBox.warning(self, "Campos obligatorios", "Debe ingresar correo y contraseña para crear un usuario nuevo.")
                return

            self.create_w = CreateJefeWorker(self.supabase_client, nombre, email, password, rut, telefono, foto_url)
            self.create_w.success.connect(self.on_guardar_success)
            self.create_w.error.connect(self.on_guardar_error)
            self.create_w.start()
        else:
            # Actualizar existente
            jefe_id = self.current_jefe.get("id")
            self.update_w = UpdateJefeWorker(self.supabase_client, jefe_id, nombre, rut, telefono, foto_url)
            self.update_w.success.connect(self.on_guardar_success)
            self.update_w.error.connect(self.on_guardar_error)
            self.update_w.start()

    def on_guardar_success(self, msg):
        self.btn_save.setEnabled(True)
        self.btn_save.setText("Guardar Cambios")
        QMessageBox.information(self, "Éxito", msg)
        self.cargar_tabla()

    def on_guardar_error(self, err):
        self.btn_save.setEnabled(True)
        self.btn_save.setText("Guardar Cambios")
        QMessageBox.critical(self, "Error", err)

    def eliminar_jefe(self):
        if not self.current_jefe:
            return
        reply = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Está seguro de eliminar al Supervisor '{self.current_jefe.get('nombre')}'?\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            jefe_id = self.current_jefe.get("id")
            self.del_w = DeleteJefeWorker(self.supabase_client, jefe_id)
            self.del_w.success.connect(self.on_eliminar_success)
            self.del_w.error.connect(lambda e: QMessageBox.critical(self, "Error", e))
            self.del_w.start()

    def on_eliminar_success(self, msg):
        QMessageBox.information(self, "Éxito", msg)
        self.limpiar_formulario()
        self.cargar_tabla()

    def asignar_jefe_obra(self):
        if not self.current_jefe:
            QMessageBox.warning(self, "Seleccionar Supervisor", "Seleccione o guarde primero a un Supervisor.")
            return
        obra_id = self.combo_obras.currentData()
        jefe_id = self.current_jefe.get("id")

        if not obra_id or not jefe_id:
            QMessageBox.warning(self, "Error", "Debe seleccionar una obra de destino.")
            return

        self.btn_asignar.setEnabled(False)
        self.btn_asignar.setText("Asignando...")
        self.assign_w = AssignJefeWorker(self.supabase_client, obra_id, jefe_id)
        self.assign_w.success.connect(lambda msg: (
            self.btn_asignar.setEnabled(True),
            self.btn_asignar.setText("Asignar a Obra"),
            QMessageBox.information(self, "Éxito", msg)
        ))
        self.assign_w.error.connect(lambda e: (
            self.btn_asignar.setEnabled(True),
            self.btn_asignar.setText("Asignar a Obra"),
            QMessageBox.critical(self, "Error", e)
        ))
        self.assign_w.start()

    def _seleccionar_foto(self):
        """Abre el selector de archivos y sube la foto seleccionada al Storage."""
        if not self.supabase_client:
            QMessageBox.warning(self, "Error", "Sin conexión a Supabase.")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar foto de perfil",
            "",
            "Imágenes (*.jpg *.jpeg *.png *.webp)"
        )
        if not file_path:
            return

        self.btn_upload_foto.setEnabled(False)
        self.btn_upload_foto.setText("Subiendo foto...")

        self._w_upload = UploadFotoPerfilWorker(
            self.supabase_client, file_path, subfolder="supervisores"
        )
        self._w_upload.success.connect(self._on_foto_subida)
        self._w_upload.error.connect(self._on_foto_error)
        self._w_upload.start()

    def _on_foto_subida(self, url: str):
        self.btn_upload_foto.setEnabled(True)
        self.btn_upload_foto.setText("📁  Seleccionar foto desde dispositivo")
        self.txt_foto_url.setText(url)  # actualiza campo URL y dispara preview
        QMessageBox.information(self, "Foto subida", "Foto subida exitosamente.\nRecuerde guardar los cambios para vincularla al perfil.")

    def _on_foto_error(self, err: str):
        self.btn_upload_foto.setEnabled(True)
        self.btn_upload_foto.setText("📁  Seleccionar foto desde dispositivo")
        QMessageBox.critical(self, "Error al subir foto", err)
