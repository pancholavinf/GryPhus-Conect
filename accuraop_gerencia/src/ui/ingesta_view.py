from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHBoxLayout, QHeaderView, QLineEdit, QMessageBox, QFormLayout, QDialog,
    QDoubleSpinBox, QDialogButtonBox, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QColor, QPixmap
import pandas as pd
import uuid
from src.core.workers import FetchJefesWorker, ProcessIngestaWorker

class PreciosMaterialesDialog(QDialog):
    def __init__(self, materiales, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Precios de Materiales")
        self.layout = QVBoxLayout(self)
        
        self.inputs = {}
        form_layout = QFormLayout()
        
        for material in materiales:
            spin_box = QDoubleSpinBox()
            spin_box.setMaximum(1e9)
            spin_box.setPrefix("$ ")
            self.inputs[material] = spin_box
            form_layout.addRow(QLabel(str(material)), spin_box)
            
        self.layout.addLayout(form_layout)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)
        
    def get_precios(self):
        return {material: box.value() for material, box in self.inputs.items()}


class CrearMaterialesNuevosDialog(QDialog):
    def __init__(self, materiales_nuevos, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crear Materiales Nuevos en el Catálogo Global")
        self.setMinimumWidth(650)
        self.layout = QVBoxLayout(self)
        
        info = QLabel(
            "Se han detectado materiales en el archivo Excel que no existen en el catálogo global de la plataforma.\n"
            "Configure sus unidades de medida (el rendimiento real se calculará dinámicamente según reportes y avances por espesor):"
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #2D3033; font-weight: bold; margin-bottom: 10px;")
        self.layout.addWidget(info)
        
        # Tabla para editar datos de materiales
        self.table = QTableWidget()
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setMinimumSectionSize(110)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Material Nuevo", "Unidad de Medida", "Rend. Ref. (Opcional)", "Descripción"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setRowCount(len(materiales_nuevos))
        self.table.setMinimumHeight(200)
        
        self.widgets = {} # { nombre: (combo_unidad, spin_rendimiento, edit_desc) }
        
        for idx, mat in enumerate(materiales_nuevos):
            # Nombre (Solo lectura)
            item_nombre = QTableWidgetItem(mat)
            item_nombre.setFlags(item_nombre.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(idx, 0, item_nombre)
            
            # Unidad Combo
            combo = QComboBox()
            combo.addItems(["tinetas", "sacos", "un", "kg", "litros"])
            self.table.setCellWidget(idx, 1, combo)
            
            # Rendimiento Spin
            spin = QDoubleSpinBox()
            spin.setDecimals(3)
            spin.setSingleStep(0.01)
            spin.setMaximum(100.0)
            spin.setValue(0.0)
            spin.setToolTip("Opcional. El rendimiento real se determinará dinámicamente según avances y consumos reportados por espesor.")
            self.table.setCellWidget(idx, 2, spin)
            
            # Descripción
            desc = QLineEdit()
            desc.setPlaceholderText("Descripción breve (Opcional)")
            self.table.setCellWidget(idx, 3, desc)
            
            self.widgets[mat] = (combo, spin, desc)
            
        self.layout.addWidget(self.table)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)
        
    def get_materiales_data(self):
        data = {}
        for mat, (combo, spin, desc) in self.widgets.items():
            data[mat] = {
                "unidad": combo.currentText(),
                "rendimiento": spin.value(),
                "descripcion": desc.text().strip()
            }
        return data


class IngestaContent(QWidget):
    def __init__(self, supabase_client=None):
        super().__init__()
        self.supabase_client = supabase_client
        self.selected_file = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        header = QLabel("Ingesta de Obras (Presupuesto)")
        header.setObjectName("TitleLabel")
        layout.addWidget(header)
        
        # Formulario
        form_layout = QFormLayout()
        self.nombre_obra_input = QLineEdit()
        self.nombre_obra_input.setPlaceholderText("Nombre de la nueva obra")
        
        self.jefe_obra_input = QComboBox()
        self.cargar_jefes()
        
        self.color_obra_input = QComboBox()
        self.colores_obra = {
            "Azul Track": "#F3A500",
            "Azul Acero": "#F3A500",
            "Slate Oscuro": "#2D3033",
            "Gris Pizarra": "#2D3033",
            "Rojo Peligro": "#EF4444",
            "Verde Éxito": "#10B981",
            "Naranja Cálido": "#F59E0B",
            "Púrpura Profundo": "#6366F1"
        }
        for nombre, hex_color in self.colores_obra.items():
            pixmap = QPixmap(16, 16)
            pixmap.fill(QColor(hex_color))
            self.color_obra_input.addItem(QIcon(pixmap), nombre, hex_color)
        
        form_layout.addRow("Nombre de Obra:", self.nombre_obra_input)
        form_layout.addRow("Color de la Obra:", self.color_obra_input)
        form_layout.addRow("Supervisor:", self.jefe_obra_input)
        layout.addLayout(form_layout)

        # Botones
        btn_layout = QHBoxLayout()
        self.load_btn = QPushButton("Seleccionar Excel")
        self.load_btn.setObjectName("SecondaryButton")
        self.load_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.load_btn.clicked.connect(self.select_excel)
        
        self.process_btn = QPushButton("Procesar y Crear Obra")
        self.process_btn.setObjectName("PrimaryButton")
        self.process_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.process_btn.clicked.connect(self.process_obra)
        
        self.file_label = QLabel("Ningún archivo seleccionado")
        
        btn_layout.addWidget(self.load_btn)
        btn_layout.addWidget(self.file_label)
        btn_layout.addStretch()
        btn_layout.addWidget(self.process_btn)
        
        layout.addLayout(btn_layout)
        layout.addSpacing(20)
        
        self.table = QTableWidget()
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setMinimumSectionSize(110)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.table)

    def select_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Archivo Excel",
            "",
            "Excel Files (*.xlsx *.xls)"
        )
        
        if file_path:
            self.selected_file = file_path
            self.file_label.setText(file_path.split("/")[-1])
            try:
                columnas_interes = [
                    "UBICACIÓN", "PLANO", "DESCRIPCIÓN EN PLANO", "ESTRUCTURA", "DIMENSIONES",
                    "PERFIL", "CANT.", "CANTIDAD ESTRUCTURAS", "LARGO\n[mm]", "CARAS EXPTAS.",
                    "PERÍMETRO EXPUESTO\n[mm]", "RESIST. AL FUEGO", "MASIV. (M-1)", 
                    "ÁREA EXPUESTA\n[m2]", "MATERIAL", "CERTIFICACION", "MICRAS", 
                    "FORMULA", "TINETAS", "ESPESOR (mm)", "SACOS", "ANOTACIONES"
                ]
                df = pd.read_excel(file_path, sheet_name="CUBICACION", skiprows=7, usecols=columnas_interes)
                df.dropna(subset=['UBICACIÓN'], inplace=True)
                self.populate_table(df)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error previsualizando Excel: {e}")
                
    def populate_table(self, df):
        self.table.clear()
        preview_df = df.head(50)
        
        self.table.setColumnCount(len(preview_df.columns))
        self.table.setRowCount(len(preview_df.index))
        self.table.setHorizontalHeaderLabels([str(col) for col in preview_df.columns])
        
        for i, row in preview_df.iterrows():
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                self.table.setItem(i, j, item)
                
        # Auto-size columns to contents for a clean layout
        self.table.resizeColumnsToContents()

    def cargar_jefes(self):
        self.jefe_obra_input.clear()
        self.jefe_obra_input.addItem("-- Sin Supervisor --", None)
        if self.supabase_client:
            self.fetch_jefes_worker = FetchJefesWorker(self.supabase_client)
            self.fetch_jefes_worker.success.connect(self.on_cargar_jefes_success)
            self.fetch_jefes_worker.start()

    def on_cargar_jefes_success(self, data):
        for jefe in data:
            self.jefe_obra_input.addItem(jefe["nombre"], jefe["id"])

    def process_obra(self):
        if not self.selected_file:
            QMessageBox.warning(self, "Error", "Debe seleccionar un archivo Excel.")
            return
            
        nombre = self.nombre_obra_input.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Error", "Debe ingresar un nombre de obra.")
            return
            
        jefe_id = self.jefe_obra_input.currentData()
        
        if not self.supabase_client:
            QMessageBox.warning(self, "Error", "Cliente de Supabase no inicializado.")
            return

        color_seleccionado = self.color_obra_input.currentData()

        try:
            columnas_interes = [
                "UBICACIÓN", "PLANO", "DESCRIPCIÓN EN PLANO", "ESTRUCTURA", "DIMENSIONES",
                "PERFIL", "CANT.", "CANTIDAD ESTRUCTURAS", "LARGO\n[mm]", "CARAS EXPTAS.",
                "PERÍMETRO EXPUESTO\n[mm]", "RESIST. AL FUEGO", "MASIV. (M-1)", 
                "ÁREA EXPUESTA\n[m2]", "MATERIAL", "CERTIFICACION", "MICRAS", 
                "FORMULA", "TINETAS", "ESPESOR (mm)", "SACOS", "ANOTACIONES"
            ]
            df = pd.read_excel(self.selected_file, sheet_name="CUBICACION", skiprows=7, usecols=columnas_interes)
            df.dropna(subset=['UBICACIÓN'], inplace=True)
            
            materiales_unicos = [str(m).strip() for m in df['MATERIAL'].unique() if pd.notnull(m) and str(m).strip()]
            
            # 1. Consultar catálogo global en Supabase
            res_mats = self.supabase_client.table("materiales").select("id, nombre").execute()
            materiales_existentes = {str(m.get("nombre")).strip(): m.get("id") for m in res_mats.data or []}
            
            # 2. Identificar materiales faltantes
            materiales_nuevos = [m for m in materiales_unicos if m not in materiales_existentes]
            
            # 3. Registrar materiales nuevos interactivamente
            if materiales_nuevos:
                dialog_nuevos = CrearMaterialesNuevosDialog(materiales_nuevos, self)
                if dialog_nuevos.exec() == QDialog.DialogCode.Accepted:
                    nuevos_datos = dialog_nuevos.get_materiales_data()
                    for mat_nombre, data_cfg in nuevos_datos.items():
                        # Generar UUID local
                        new_id = str(uuid.uuid4())
                        record = {
                            "id": new_id,
                            "nombre": mat_nombre,
                            "unidad_medida": data_cfg["unidad"],
                            "rendimiento_teorico_m2": data_cfg["rendimiento"],
                            "descripcion": data_cfg["descripcion"]
                        }
                        res_ins = self.supabase_client.table("materiales").insert(record).execute()
                        if res_ins.data:
                            materiales_existentes[mat_nombre] = new_id
                        else:
                            # Fallback si por alguna razón falla el retorno
                            materiales_existentes[mat_nombre] = new_id
                else:
                    return # Cancelado por el usuario
            
            # 4. Diálogo de Precios
            precios_dict = {}
            if materiales_unicos:
                dialog_precios = PreciosMaterialesDialog(materiales_unicos, self)
                if dialog_precios.exec() == QDialog.DialogCode.Accepted:
                    precios_dict = dialog_precios.get_precios()
                else:
                    return
                    
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error procesando materiales de la obra: {e}")
            return
            
        self.process_btn.setEnabled(False)
        self.process_btn.setText("Procesando...")
        self.ingesta_worker = ProcessIngestaWorker(
            self.supabase_client, self.selected_file, nombre, jefe_id, precios_dict, color_seleccionado, materiales_existentes
        )
        self.ingesta_worker.success.connect(self.on_process_success)
        self.ingesta_worker.error.connect(self.on_process_error)
        self.ingesta_worker.start()

    def on_process_success(self, message):
        self.process_btn.setEnabled(True)
        self.process_btn.setText("Procesar y Crear Obra")
        QMessageBox.information(self, "Éxito", message)
        self.nombre_obra_input.clear()
        self.jefe_obra_input.setCurrentIndex(0)
        self.selected_file = None
        self.file_label.setText("Ningún archivo seleccionado")
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)

    def on_process_error(self, message):
        self.process_btn.setEnabled(True)
        self.process_btn.setText("Procesar y Crear Obra")
        QMessageBox.critical(self, "Error", message)
