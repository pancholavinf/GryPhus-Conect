import os
import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class EDPNumberedCanvas(canvas.Canvas):
    """
    Canvas personalizado de 2 pasadas para agregar encabezado, pie de página y numeración 'Página X de Y'.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        
        # Orientación horizontal (landscape letter: 792 x 612 pt)
        page_width, page_height = 792, 612
        margin = 36
        
        # Header Bar & Text
        self.setFont("Helvetica-Bold", 9)
        self.setFillColor(colors.HexColor("#262B29"))
        self.drawString(margin, page_height - 25, "GRYPHUS CONECT  |  DOCUMENTO OFICIAL DE ESTADO DE PAGO")
        
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#4A524E"))
        self.drawRightString(page_width - margin, page_height - 25, "Gryphus Systems")
        
        # Header line
        self.setStrokeColor(colors.HexColor("#4A524E"))
        self.setLineWidth(0.75)
        self.line(margin, page_height - 30, page_width - margin, page_height - 30)
        
        # Footer line
        self.line(margin, 35, page_width - margin, 35)
        
        # Footer Text
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#4A524E"))
        self.drawString(margin, 22, "Documento inalterable generado automáticamente por GryPhus Conect Gerencia")
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(page_width - margin, 22, page_text)
        
        self.restoreState()


def fmt_money(val):
    """Formatea valores numéricos como dinero chileno ($ X.XXX.XXX)"""
    try:
        val = float(val or 0)
        return f"${val:,.0f}".replace(",", ".")
    except Exception:
        return "$0"

def fmt_num(val, decimals=2):
    """Formatea valores de medición de cantidad"""
    try:
        val = float(val or 0)
        if val == int(val):
            return f"{int(val):,}".replace(",", ".")
        return f"{val:,.{decimals}f}".replace(",", ".").rstrip('0').rstrip('.')
    except Exception:
        return "0"

def generate_edp_pdf(output_path, edp_data, items_detail, logo_path=None):
    """
    Genera el archivo PDF oficial del Estado de Pago basado en la estructura de estado_pago_muestra.xlsx
    
    :param output_path: Ruta del archivo PDF a generar.
    :param edp_data: Diccionario con la información del EDP (obra_nombre, numero_estado_pago, fechas, montos, etc).
    :param items_detail: Lista de diccionarios con la matriz de cada partida.
    :param logo_path: Ruta opcional del logo institucional.
    """
    # Usar orientación Horizontal para dar cabida limpia a todas las columnas de contrato y avance
    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(letter), # 792 x 612 pt
        leftMargin=36,
        rightMargin=36,
        topMargin=45,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()
    
    # Colores corporativos Trabs
    c_primary = colors.HexColor("#262B29")
    c_accent = colors.HexColor("#3D523C")
    c_secondary = colors.HexColor("#3D523C")
    c_dark = colors.HexColor("#1F2421")
    c_slate = colors.HexColor("#4A524E")
    c_light_bg = colors.HexColor("#F2EFE9")
    c_border = colors.HexColor("#4A524E")

    # Estilos de texto
    style_title = ParagraphStyle(
        'EDPTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=c_primary
    )
    
    style_meta_label = ParagraphStyle(
        'EDPMetaLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=c_slate
    )
    
    style_meta_val = ParagraphStyle(
        'EDPMetaVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=c_dark
    )
    
    style_cell = ParagraphStyle(
        'EDPCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=9,
        textColor=c_dark
    )
    
    style_cell_center = ParagraphStyle(
        'EDPCellCenter',
        parent=style_cell,
        alignment=1 # Center
    )
    
    style_cell_right = ParagraphStyle(
        'EDPCellRight',
        parent=style_cell,
        alignment=2 # Right
    )
    
    style_th = ParagraphStyle(
        'EDPTH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        leading=9,
        textColor=colors.white,
        alignment=1 # Center
    )

    elements = []

    # 1. ENCABEZADO Y FICHA TÉCNICA
    edp_num = edp_data.get('numero_estado_pago', 1)
    fecha_emision = edp_data.get('fecha_emision', datetime.date.today().strftime("%d/%m/%Y"))
    periodo_desde = edp_data.get('periodo_desde', '')
    periodo_hasta = edp_data.get('periodo_hasta', '')
    
    title_text = f"ESTADO DE PAGO N° {edp_num}"
    
    # Preparar Logo
    img_element = None
    if logo_path and os.path.exists(logo_path):
        try:
            img_element = Image(logo_path, width=150, height=35)
            img_element.hAlign = 'LEFT'
        except Exception:
            img_element = Paragraph(f"<b>GRYPHUS CONECT</b>", style_title)
    else:
        img_element = Paragraph(f"<b>GRYPHUS CONECT</b>", style_title)

    meta_table_data = [
        [
            img_element,
            Paragraph(f"<font color='#262B29'><b>{title_text}</b></font><br/><font color='#4A524E' size=8>Fecha Emisión: {fecha_emision}</font>", style_title)
        ]
    ]
    meta_header_table = Table(meta_table_data, colWidths=[250, 470])
    meta_header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    elements.append(meta_header_table)
    elements.append(Spacer(1, 10))

    # Ficha de la Obra y Período
    info_box_data = [
        [
            Paragraph("OBRA:", style_meta_label),
            Paragraph(str(edp_data.get('obra_nombre', 'N/A')), style_meta_val),
            Paragraph("CONTRATO / OT #:", style_meta_label),
            Paragraph(str(edp_data.get('orden_trabajo_num', 'N/A')), style_meta_val),
        ],
        [
            Paragraph("MANDANTE / CLIENTE:", style_meta_label),
            Paragraph(str(edp_data.get('mandante', 'Gryphus Systems')), style_meta_val),
            Paragraph("PERÍODO COBRO:", style_meta_label),
            Paragraph(f"{periodo_desde} al {periodo_hasta}", style_meta_val),
        ],
        [
            Paragraph("UBICACIÓN:", style_meta_label),
            Paragraph(str(edp_data.get('ubicacion', 'Chile')), style_meta_val),
            Paragraph("MONEDA / UNIDAD:", style_meta_label),
            Paragraph("PESOS CHILENOS ($)", style_meta_val),
        ]
    ]
    info_table = Table(info_box_data, colWidths=[110, 250, 110, 250])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_light_bg),
        ('BOX', (0, 0), (-1, -1), 0.5, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 12))

    # 2. MATRIZ DE PARTIDAS Y AVANCE (Estructura de estado_pago_muestra.xlsx)
    # Encabezado Nivel 1 (Agrupadores)
    table_headers_row1 = [
        "Item",
        "Descripción",
        "Unidad",
        "Datos según Contrato / OC", "", "",
        "Avance Acumulado", "",
        "Avance E.P. Anterior", "",
        "Avance Presente E.P.", "", ""
    ]
    
    # Encabezado Nivel 2 (Subcolumnas)
    table_headers_row2 = [
        "", "", "",
        "Cantidad", "P. Unit ($)", "P. Total ($)",
        "Medición", "Avance %",
        "Medición", "Avance %",
        "Medición", "Avance %", "P. Total ($)"
    ]

    table_data = [
        [Paragraph(f"<b>{h}</b>", style_th) for h in table_headers_row1],
        [Paragraph(f"<b>{h}</b>", style_th) for h in table_headers_row2]
    ]

    # Filas de partidas
    for idx, item in enumerate(items_detail, start=1):
        q_contrato = float(item.get('cantidad_contrato', 0))
        pu = float(item.get('precio_unitario', 0))
        p_total_contrato = q_contrato * pu
        
        q_ant = float(item.get('cantidad_anterior', 0))
        pct_ant = (q_ant / q_contrato * 100.0) if q_contrato > 0 else 0.0
        
        q_pres = float(item.get('cantidad_presente', 0))
        pct_pres = (q_pres / q_contrato * 100.0) if q_contrato > 0 else 0.0
        p_total_pres = q_pres * pu
        
        q_acum = q_ant + q_pres
        pct_acum = (q_acum / q_contrato * 100.0) if q_contrato > 0 else 0.0
        
        desc = item.get('descripcion', 'Partida sin nombre')

        row_cells = [
            Paragraph(str(idx), style_cell_center),
            Paragraph(desc[:45], style_cell),
            Paragraph(str(item.get('unidad', 'm²')), style_cell_center),
            
            # Contrato
            Paragraph(fmt_num(q_contrato), style_cell_right),
            Paragraph(fmt_money(pu), style_cell_right),
            Paragraph(fmt_money(p_total_contrato), style_cell_right),
            
            # Acumulado
            Paragraph(fmt_num(q_acum), style_cell_right),
            Paragraph(f"{pct_acum:.1f}%", style_cell_right),
            
            # Anterior
            Paragraph(fmt_num(q_ant), style_cell_right),
            Paragraph(f"{pct_ant:.1f}%", style_cell_right),
            
            # Presente EDP
            Paragraph(fmt_num(q_pres), style_cell_right),
            Paragraph(f"{pct_pres:.1f}%", style_cell_right),
            Paragraph(fmt_money(p_total_pres), style_cell_right),
        ]
        table_data.append(row_cells)

    # Anchos de columna (Total: 720 pt)
    col_widths = [25, 160, 35, 45, 55, 65, 45, 45, 45, 45, 45, 45, 65]
    
    parts_table = Table(table_data, colWidths=col_widths, repeatRows=2)
    
    ts = [
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#3D523C")),
        ('SPAN', (0, 0), (0, 1)), # Item
        ('SPAN', (1, 0), (1, 1)), # Descripcion
        ('SPAN', (2, 0), (2, 1)), # Unidad
        ('SPAN', (3, 0), (5, 0)), # Datos contrato
        ('SPAN', (6, 0), (7, 0)), # Avance Acumulado
        ('SPAN', (8, 0), (9, 0)), # Avance Anterior
        ('SPAN', (10, 0), (12, 0)), # Avance Presente EDP
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 0.5, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('PADDING', (0, 0), (-1, -1), 2),
    ]
    
    # Alternar color de filas de partidas
    for r in range(2, len(table_data)):
        if r % 2 == 1:
            ts.append(('BACKGROUND', (0, r), (-1, r), c_light_bg))
            
    parts_table.setStyle(TableStyle(ts))
    elements.append(parts_table)
    elements.append(Spacer(1, 10))

    # 3. RESUMEN FINANCIERO Y RETENCIONES (CUADRO DERECHO DE TOTALES)
    subtotal_pesos = float(edp_data.get('subtotal_pesos', 0))
    monto_retencion = float(edp_data.get('monto_retencion', subtotal_pesos * 0.05))
    monto_anticipo = float(edp_data.get('monto_anticipo', 0))
    monto_neto = float(edp_data.get('monto_neto', subtotal_pesos - monto_retencion - monto_anticipo))
    monto_iva = float(edp_data.get('monto_iva', monto_neto * 0.19))
    monto_total = float(edp_data.get('monto_total', monto_neto + monto_iva))

    style_tot_lbl = ParagraphStyle('TotLbl', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=c_slate)
    style_tot_val = ParagraphStyle('TotVal', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, alignment=2, textColor=c_dark)
    style_tot_main_lbl = ParagraphStyle('TotMainLbl', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=c_primary)
    style_tot_main_val = ParagraphStyle('TotMainVal', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=12, alignment=2, textColor=c_primary)

    totals_box_data = [
        [Paragraph("SUBTOTAL PESOS (PRESENTE E.P.):", style_tot_lbl), Paragraph(fmt_money(subtotal_pesos), style_tot_val)],
        [Paragraph("(-) RETENCIÓN DE CONTRATO (5%):", style_tot_lbl), Paragraph(f"-{fmt_money(monto_retencion)}", style_tot_val)],
        [Paragraph("(-) DESCUENTO AMORTIZACIÓN ANTICIPO:", style_tot_lbl), Paragraph(f"-{fmt_money(monto_anticipo)}", style_tot_val)],
        [Paragraph("<b>SUB-TOTAL NETO:</b>", style_tot_lbl), Paragraph(f"<b>{fmt_money(monto_neto)}</b>", style_tot_val)],
        [Paragraph("<b>IVA (19%):</b>", style_tot_lbl), Paragraph(f"<b>{fmt_money(monto_iva)}</b>", style_tot_val)],
        [Paragraph(f"<b>TOTAL GENERAL E.P. N° {edp_num}:</b>", style_tot_main_lbl), Paragraph(f"<b>{fmt_money(monto_total)}</b>", style_tot_main_val)],
    ]
    
    totals_table = Table(totals_box_data, colWidths=[240, 110])
    totals_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -2), c_light_bg),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#EBE6DD")),
        ('BOX', (0, 0), (-1, -1), 1, c_primary),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))

    # Contenedor alineado a la derecha para Totales
    totals_wrapper = Table([[ "", totals_table ]], colWidths=[370, 350])
    totals_wrapper.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(KeepTogether([totals_wrapper, Spacer(1, 15)]))

    # 4. CUADRO CORPORATIVO DE FIRMAS Y APROBACIONES
    style_sig_title = ParagraphStyle('SigTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, alignment=1, textColor=c_slate)
    style_sig_sub = ParagraphStyle('SigSub', parent=styles['Normal'], fontName='Helvetica', fontSize=7, leading=9, alignment=1, textColor=c_slate)

    sig_data = [
        [
            Paragraph("<br/><br/>___________________________________<br/><b>RECEPCIÓN CLIENTE</b><br/>Fecha: ____ / ____ / ________", style_sig_title),
            Paragraph("<br/><br/>___________________________________<br/><b>APROBACIÓN CLIENTE</b><br/>Fecha: ____ / ____ / ________", style_sig_title),
            Paragraph("<br/><br/>___________________________________<br/><b>FRANCISCO DÍAZ P.</b><br/>GRYPHUS SYSTEMS<br/>Emitido el " + fecha_emision, style_sig_title),
        ]
    ]
    sig_table = Table(sig_data, colWidths=[230, 230, 240])
    sig_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('BACKGROUND', (0, 0), (-1, -1), c_light_bg),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(KeepTogether([sig_table]))

    # Renderizar PDF con EDPNumberedCanvas
    doc.build(elements, canvasmaker=EDPNumberedCanvas)
    return output_path
