import os
import subprocess
import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QDialog, QLineEdit, QFormLayout,
    QMessageBox, QDateEdit, QDoubleSpinBox, QSplitter, QAbstractItemView,
    QProgressBar
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont
from src.core.edp_controller import EDPController
from src.core.workers import FetchEDPHistorialWorker, EmitEDPWorker


def fmt_money(val):
    try:
        val = float(val or 0)
        return f"${val:,.0f}".replace(",", ".")
    except Exception:
        return "$0"


# =============================================================================
# DIALOG DE EMISIÓN OFICIAL DEL EDP
# =============================================================================

class EmisionEDPDialog(QDialog):
    def __init__(self, parent, edp_meta, items_detail, candidatos_ids,
                 controller, obra_id, user_id=None):
        super().__init__(parent)
        self.setWindowTitle(f"Emisión de Estado de Pago N° {edp_meta.get('numero_estado_pago', 1)}")
        self.resize(960, 640)
        self.edp_meta      = edp_meta
        self.items_detail  = items_detail
        self.candidatos_ids = candidatos_ids
        self.controller    = controller
        self.obra_id       = obra_id
        self.user_id       = user_id

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # ── Header ──────────────────────────────────────────────────────────
        lbl_title = QLabel(
            f"Resumen de Cobro: Estado de Pago N° {self.edp_meta.get('numero_estado_pago')}"
        )
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #3D523C;")
        layout.addWidget(lbl_title)

        cant_av = len(self.candidatos_ids)
        lbl_sub = QLabel(
            f"Obra: {self.edp_meta.get('obra_nombre')}  |  "
            f"Período: {self.edp_meta.get('periodo_desde')} → {self.edp_meta.get('periodo_hasta')}  |  "
            f"Avances aprobados incluidos: {cant_av}"
        )
        lbl_sub.setStyleSheet("font-size: 12px; color: #262B29;")
        layout.addWidget(lbl_sub)

        # ── Tabla de ítems (solo los que tienen cantidad presente > 0) ──────
        # Filtrar para no mostrar ítems vacíos
        items_con_monto = [it for it in self.items_detail if float(it.get('cantidad_presente', 0)) > 0]
        items_a_mostrar = items_con_monto if items_con_monto else self.items_detail

        self.table = QTableWidget()
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setMinimumSectionSize(110)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Item", "Descripción", "Unidad",
            "Cant. Contrato", "Cant. Anterior", "Cant. Presente", "Monto Presente ($)"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setRowCount(len(items_a_mostrar))

        for idx, item in enumerate(items_a_mostrar):
            self.table.setItem(idx, 0, QTableWidgetItem(str(idx + 1)))
            self.table.setItem(idx, 1, QTableWidgetItem(item['descripcion']))
            self.table.setItem(idx, 2, QTableWidgetItem(item.get('unidad', 'm²')))
            self.table.setItem(idx, 3, QTableWidgetItem(f"{float(item['cantidad_contrato']):.2f}"))
            self.table.setItem(idx, 4, QTableWidgetItem(f"{float(item['cantidad_anterior']):.2f}"))
            self.table.setItem(idx, 5, QTableWidgetItem(f"{float(item['cantidad_presente']):.2f}"))

            monto_item = QTableWidgetItem(fmt_money(item['monto_presente']))
            monto_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if float(item.get('monto_presente', 0)) > 0:
                monto_item.setForeground(QColor("#3D523C"))
            self.table.setItem(idx, 6, monto_item)

        layout.addWidget(self.table)

        # ── Formulario de retenciones y descuentos ───────────────────────────
        form_frame = QFrame()
        form_frame.setStyleSheet(
            "background-color: #FAF8F5; color: #1F2421; "
            "border: 1px solid #D8D5CD; border-radius: 6px; padding: 4px;"
        )
        form_layout = QHBoxLayout(form_frame)

        self.spin_retencion = QDoubleSpinBox()
        self.spin_retencion.setRange(0, 100)
        self.spin_retencion.setValue(5.0)
        self.spin_retencion.setSuffix(" %")
        self.spin_retencion.setDecimals(2)
        self.spin_retencion.valueChanged.connect(self.recalcular_totales)

        self.spin_anticipo = QDoubleSpinBox()
        self.spin_anticipo.setRange(0, 999_999_999)
        self.spin_anticipo.setPrefix("$ ")
        self.spin_anticipo.setValue(0.0)
        self.spin_anticipo.setDecimals(0)
        self.spin_anticipo.setSingleStep(1000)
        self.spin_anticipo.valueChanged.connect(self.recalcular_totales)

        form_layout.addWidget(QLabel("<b>% Retención Contrato:</b>"))
        form_layout.addWidget(self.spin_retencion)
        form_layout.addSpacing(20)
        form_layout.addWidget(QLabel("<b>$ Descuento Anticipo:</b>"))
        form_layout.addWidget(self.spin_anticipo)
        form_layout.addStretch()
        layout.addWidget(form_frame)

        # ── Caja de totales ──────────────────────────────────────────────────
        self.lbl_summary = QLabel()
        self.lbl_summary.setStyleSheet(
            "background: #F2EFE9; color: #1F2421; border: 1px solid #4A524E; "
            "border-radius: 6px; padding: 10px; font-size: 13px;"
        )
        self.lbl_summary.setWordWrap(True)
        layout.addWidget(self.lbl_summary)
        self.recalcular_totales()

        # ── Barra de progreso (oculta hasta emisión) ─────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # indeterminado
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(
            "QProgressBar { border:none; background:#D8D5CD; border-radius:4px; }"
            "QProgressBar::chunk { background:#3D523C; border-radius:4px; }"
        )
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # ── Botones de acción ────────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_cancel.setStyleSheet(
            "padding: 8px 16px; border: 1px solid #D8D5CD; "
            "border-radius: 4px; color: #1F2421;"
        )

        self.btn_confirm = QPushButton("Confirmar, Congelar y Emitir EDP")
        self.btn_confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirm.setStyleSheet(
            "padding: 8px 20px; background-color: #3D523C; color: white; "
            "font-weight: bold; border-radius: 4px;"
        )
        self.btn_confirm.clicked.connect(self.emitir_edp)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_confirm)
        layout.addLayout(btn_layout)

    def recalcular_totales(self):
        subtotal   = float(self.edp_meta.get('subtotal_pesos', 0))
        ret_pct    = self.spin_retencion.value() / 100.0
        monto_ret  = subtotal * ret_pct
        monto_ant  = self.spin_anticipo.value()

        neto   = max(0.0, subtotal - monto_ret - monto_ant)
        iva    = neto * 0.19
        total  = neto + iva

        self.lbl_summary.setText(
            f"<b>Subtotal Pesos:</b> {fmt_money(subtotal)} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Retención ({self.spin_retencion.value():.2f}%):</b> -{fmt_money(monto_ret)} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Descuento Anticipo:</b> -{fmt_money(monto_ant)} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Subtotal Neto:</b> {fmt_money(neto)} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>IVA (19%):</b> {fmt_money(iva)} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<font color='#3D523C' size=4><b>TOTAL GENERAL: {fmt_money(total)}</b></font>"
        )

    def emitir_edp(self):
        # Confirmación adicional antes de congelar avances
        reply = QMessageBox.question(
            self,
            "Confirmar Emisión",
            f"¿Confirma la emisión del Estado de Pago N° "
            f"{self.edp_meta.get('numero_estado_pago')}?\n\n"
            f"Esta acción congelará {len(self.candidatos_ids)} avances aprobados "
            f"y no podrá deshacerse fácilmente.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.btn_confirm.setEnabled(False)
        self.btn_confirm.setText("⏳ Emitiendo y generando PDF...")
        self.btn_cancel.setEnabled(False)
        self.progress_bar.show()

        periodo_desde = self.edp_meta.get('periodo_desde')
        periodo_hasta = self.edp_meta.get('periodo_hasta')
        ret_pct       = self.spin_retencion.value() / 100.0
        anticipo      = self.spin_anticipo.value()

        self.worker = EmitEDPWorker(
            self.controller,
            self.obra_id,
            periodo_desde,
            periodo_hasta,
            retencion_pct=ret_pct,
            anticipo_monto=anticipo,
            user_id=self.user_id
        )
        self.worker.finished.connect(self.on_emit_success)
        self.worker.error.connect(self.on_emit_error)
        self.worker.start()

    def on_emit_success(self, result_dict):
        self.progress_bar.hide()

        aviso_pdf = ""
        if not result_dict.get('pdf_generado', True):
            aviso_pdf = "\n\n️ El PDF no pudo generarse pero el EDP quedó registrado en la base de datos."

        QMessageBox.information(
            self,
            "Estado de Pago Emitido ",
            f"El Estado de Pago N° {result_dict.get('numero_estado_pago')} ha sido generado "
            f"y congelado exitosamente.\n\n"
            f"Avances incluidos: {result_dict.get('cant_avances', 0)}\n"
            f"Monto Total: {fmt_money(result_dict.get('monto_total'))}\n"
            f"PDF guardado en: {result_dict.get('pdf_path') or 'N/A'}"
            + aviso_pdf
        )
        self.accept()

    def on_emit_error(self, error_msg):
        self.progress_bar.hide()
        self.btn_confirm.setEnabled(True)
        self.btn_confirm.setText("Confirmar, Congelar y Emitir EDP")
        self.btn_cancel.setEnabled(True)
        QMessageBox.critical(
            self,
            "Error de Emisión",
            f"No se pudo emitir el Estado de Pago:\n\n{error_msg}"
        )


# =============================================================================
# PESTAÑA PRINCIPAL DE ESTADOS DE PAGO
# =============================================================================

class EDPTab(QWidget):
    def __init__(self, supabase_client=None, obra_id=None, user_id=None):
        super().__init__()
        self.supabase  = supabase_client
        self.obra_id   = obra_id
        self.user_id   = user_id  # ID del administrador autenticado
        self.controller = EDPController(self.supabase)

        self.historial          = []
        self.edp_meta_preview   = {}
        self.items_detail       = []
        self.candidatos_ids     = []

        self.setup_ui()
        if self.obra_id:
            self.cargar_datos()

    # ------------------------------------------------------------------
    # SETUP DE LA INTERFAZ
    # ------------------------------------------------------------------

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # ── KPI Header ──────────────────────────────────────────────────────
        kpi_frame = QFrame()
        kpi_frame.setStyleSheet(
            "background-color: #FAF8F5; color: #1F2421; "
            "border: 1px solid #D8D5CD; border-radius: 8px; padding: 8px;"
        )
        kpi_layout = QHBoxLayout(kpi_frame)

        self.card_total      = self._create_card("TOTAL FACTURADO (HISTÓRICO)", "$0", "#3D523C")
        self.card_cant       = self._create_card("ESTADOS DE PAGO EMITIDOS", "0", "#1F2421")
        self.card_pendientes = self._create_card("AVANCES POR COBRAR", "0", "#2E6F40")
        self.card_neto_pend  = self._create_card("MONTO PENDIENTE DE COBRO", "$0", "#B85A3A")

        kpi_layout.addWidget(self.card_total)
        kpi_layout.addWidget(self.card_cant)
        kpi_layout.addWidget(self.card_pendientes)
        kpi_layout.addWidget(self.card_neto_pend)
        layout.addWidget(kpi_frame)

        # ── Barra de filtros y acciones ──────────────────────────────────────
        actions_frame = QFrame()
        actions_layout = QHBoxLayout(actions_frame)
        actions_layout.setContentsMargins(0, 0, 0, 0)

        actions_layout.addWidget(QLabel("<b>Período Desde:</b>"))
        self.date_desde = QDateEdit()
        self.date_desde.setCalendarPopup(True)
        self.date_desde.setDate(QDate.currentDate().addDays(-30))
        actions_layout.addWidget(self.date_desde)

        actions_layout.addWidget(QLabel("<b>Hasta:</b>"))
        self.date_hasta = QDateEdit()
        self.date_hasta.setCalendarPopup(True)
        self.date_hasta.setDate(QDate.currentDate())
        actions_layout.addWidget(self.date_hasta)

        self.btn_filter = QPushButton("Filtrar")
        self.btn_filter.clicked.connect(self.cargar_datos)
        self.btn_filter.setStyleSheet(
            "padding: 6px 12px; background: #D8D5CD; color: #1F2421; "
            "border-radius: 4px; font-weight: bold;"
        )
        actions_layout.addWidget(self.btn_filter)
        actions_layout.addStretch()

        # Botón emitir nuevo EDP
        self.btn_emitir = QPushButton("Generar Nuevo Estado de Pago")
        self.btn_emitir.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_emitir.setStyleSheet(
            "padding: 8px 16px; background-color: #3D523C; color: white; "
            "font-weight: bold; border-radius: 6px;"
        )
        self.btn_emitir.clicked.connect(self.abrir_modal_emision)
        actions_layout.addWidget(self.btn_emitir)
        layout.addWidget(actions_frame)

        # ── Título de la tabla de historial ─────────────────────────────────
        lbl_hist_title = QLabel("Historial de Estados de Pago Emitidos")
        lbl_hist_title.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #1F2421; margin-top: 5px;"
        )
        layout.addWidget(lbl_hist_title)

        # ── Tabla de historial ───────────────────────────────────────────────
        self.table_historial = QTableWidget()
        self.table_historial.verticalHeader().setDefaultSectionSize(44)
        self.table_historial.verticalHeader().setVisible(False)
        self.table_historial.horizontalHeader().setMinimumSectionSize(110)
        self.table_historial.setColumnCount(9)
        self.table_historial.setHorizontalHeaderLabels([
            "Folio", "Fecha Emisión", "Período",
            "Subtotal", "Retención", "Neto", "IVA (19%)", "Total General ($)", "Acción"
        ])
        self.table_historial.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.table_historial.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch  # Columna Período se estira
        )
        self.table_historial.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_historial.setAlternatingRowColors(True)
        self.table_historial.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table_historial)

        # ── Barra de estado de carga ─────────────────────────────────────────
        self.status_bar = QLabel("")
        self.status_bar.setStyleSheet("color: #262B29; font-size: 11px; padding: 2px 0px;")
        layout.addWidget(self.status_bar)

    def _create_card(self, title, value, color_hex):
        frame = QFrame()
        frame.setStyleSheet(
            "background-color: #FFFFFF; border: 1px solid #D8D5CD; border-radius: 6px; padding: 10px;"
        )
        ly = QVBoxLayout(frame)
        ly.setContentsMargins(5, 5, 5, 5)

        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("font-size: 10px; font-weight: bold; color: #262B29;")

        lbl_v = QLabel(value)
        lbl_v.setObjectName("ValLabel")
        lbl_v.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color_hex};")

        ly.addWidget(lbl_t)
        ly.addWidget(lbl_v)
        return frame

    def _set_card_value(self, card_widget, text):
        val_label = card_widget.findChild(QLabel, "ValLabel")
        if val_label:
            val_label.setText(text)

    # ------------------------------------------------------------------
    # CARGA DE DATOS
    # ------------------------------------------------------------------

    def cargar_datos(self):
        if not self.obra_id:
            return

        self.btn_filter.setEnabled(False)
        self.btn_emitir.setEnabled(False)
        self.status_bar.setText("⏳ Cargando datos del EDP...")

        p_desde = self.date_desde.date().toString("yyyy-MM-dd")
        p_hasta = self.date_hasta.date().toString("yyyy-MM-dd")

        self.worker = FetchEDPHistorialWorker(
            self.controller, self.obra_id, p_desde, p_hasta
        )
        self.worker.finished.connect(self.on_datos_cargados)
        self.worker.error.connect(self.on_error_cargar)
        self.worker.start()

    def on_datos_cargados(self, historial, meta_preview, items_detail, candidato_ids):
        self.historial         = historial
        self.edp_meta_preview  = meta_preview
        self.items_detail      = items_detail
        self.candidatos_ids    = candidato_ids

        self.btn_filter.setEnabled(True)

        # ── Actualizar KPIs ──────────────────────────────────────────────────
        total_historico    = sum(float(e.get('monto_total', 0)) for e in historial)
        subtotal_pendiente = float(meta_preview.get('subtotal_pesos', 0))
        cant_pend          = len(candidato_ids)

        self._set_card_value(self.card_total,      fmt_money(total_historico))
        self._set_card_value(self.card_cant,        str(len(historial)))
        self._set_card_value(self.card_pendientes,  f"{cant_pend} avance(s)")
        self._set_card_value(self.card_neto_pend,   fmt_money(subtotal_pendiente))

        # ── Habilitar/deshabilitar botón de emisión ──────────────────────────
        if cant_pend > 0:
            self.btn_emitir.setEnabled(True)
            self.btn_emitir.setText(
                f"Generar EDP ({cant_pend} avances · {fmt_money(subtotal_pendiente)})"
            )
            self.btn_emitir.setStyleSheet(
                "padding: 8px 16px; background-color: #3D523C; color: white; "
                "font-weight: bold; border-radius: 6px;"
            )
        else:
            self.btn_emitir.setEnabled(False)
            self.btn_emitir.setText("Sin avances aprobados pendientes")
            self.btn_emitir.setStyleSheet(
                "padding: 8px 16px; background-color: #94A3B8; color: white; "
                "font-weight: bold; border-radius: 6px;"
            )

        # ── Poblar tabla de historial ────────────────────────────────────────
        self.table_historial.setRowCount(len(historial))
        for idx, edp in enumerate(historial):
            num        = edp.get('numero_estado_pago', 1)
            f_emision  = str(edp.get('fecha_emision', ''))[:10]
            per        = f"{edp.get('periodo_desde', '')} → {edp.get('periodo_hasta', '')}"
            subt       = fmt_money(edp.get('subtotal_pesos', 0))
            ret        = fmt_money(edp.get('monto_retencion', 0))
            neto       = fmt_money(edp.get('monto_neto', 0))
            iva        = fmt_money(edp.get('monto_iva', 0))
            tot        = fmt_money(edp.get('monto_total', 0))

            items_row = [
                QTableWidgetItem(f"EDP N° {num}"),
                QTableWidgetItem(f_emision),
                QTableWidgetItem(per),
                QTableWidgetItem(subt),
                QTableWidgetItem(ret),
                QTableWidgetItem(neto),
                QTableWidgetItem(iva),
                QTableWidgetItem(tot),
            ]
            # Alineación a la derecha para columnas de monto
            for col_idx, it in enumerate(items_row):
                if col_idx >= 3:
                    it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table_historial.setItem(idx, col_idx, it)

            # Dar formato al total con negrita y color
            tot_item = self.table_historial.item(idx, 7)
            if tot_item:
                tot_item.setFont(QFont("Helvetica", 9, QFont.Weight.Bold))
                tot_item.setForeground(QColor("#3D523C"))

            # Botón para abrir PDF
            pdf_url = edp.get('archivo_pdf_url')
            btn_pdf = QPushButton("Abrir PDF")
            btn_pdf.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_pdf.setStyleSheet(
                "padding: 4px 8px; font-size: 11px; background-color: #3D523C; "
                "color: white; border-radius: 4px;"
            )
            if not pdf_url:
                btn_pdf.setEnabled(False)
                btn_pdf.setText("Sin PDF")
                btn_pdf.setStyleSheet(
                    "padding: 4px 8px; font-size: 11px; background-color: #94A3B8; "
                    "color: white; border-radius: 4px;"
                )
            btn_pdf.clicked.connect(
                lambda _, url=pdf_url, n=num: self.abrir_pdf_edp(url, n)
            )
            self.table_historial.setCellWidget(idx, 8, btn_pdf)

        self.status_bar.setText(
            f"{len(historial)} EDP(s) emitido(s) | {cant_pend} avance(s) pendiente(s)"
        )

    def on_error_cargar(self, error_msg):
        self.btn_filter.setEnabled(True)
        self.status_bar.setText(f"Error al cargar: {error_msg}")
        print(f"Error al cargar historial EDP: {error_msg}")

    # ------------------------------------------------------------------
    # EMISIÓN DEL EDP
    # ------------------------------------------------------------------

    def abrir_modal_emision(self):
        if not self.candidatos_ids:
            QMessageBox.warning(
                self, "Sin Avances",
                "No hay avances aprobados pendientes de cobro para el período seleccionado."
            )
            return

        # Obtener user_id del controller si no está disponible en el tab
        uid = self.user_id
        if not uid and self.controller:
            uid = self.controller._get_current_user_id()

        dialog = EmisionEDPDialog(
            self,
            self.edp_meta_preview,
            self.items_detail,
            self.candidatos_ids,
            self.controller,
            self.obra_id,
            user_id=uid
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Recargar para actualizar historial y KPIs
            self.cargar_datos()

    # ------------------------------------------------------------------
    # ABRIR PDF
    # ------------------------------------------------------------------

    def abrir_pdf_edp(self, pdf_url, edp_num):
        if not pdf_url:
            QMessageBox.warning(
                self, "PDF no encontrado",
                f"No existe un archivo PDF registrado para el EDP N° {edp_num}."
            )
            return

        try:
            if os.path.exists(pdf_url):
                # Ruta local — abrir con el visor predeterminado del sistema
                os.startfile(pdf_url)
            else:
                # URL de Supabase Storage — abrir en el navegador
                import webbrowser
                webbrowser.open(pdf_url)
        except Exception as e:
            QMessageBox.critical(
                self, "Error al abrir PDF",
                f"No se pudo abrir el documento PDF:\n{str(e)}"
            )
