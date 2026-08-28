import os
import sys
from PIL import Image as PILImage
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Custom canvas for two-pass rendering of header/footer and page numbers.
    Suppresses decorations on cover page (Page 1).
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
        if self._pageNumber == 1:
            self.saveState()
            # Top primary bar
            self.setFillColor(colors.HexColor("#F3A500"))
            self.rect(0, 772, 612, 20, stroke=0, fill=1)
            # Bottom bar
            self.setFillColor(colors.HexColor("#2D3033"))
            self.rect(0, 0, 612, 30, stroke=0, fill=1)
            self.restoreState()
            return

        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#2D3033"))
        
        # Header
        self.drawString(54, 752, "TRABS")
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#4A5156"))
        self.drawRightString(558, 752, "Documento Maestro: PRD y Sistema de Diseño")
        
        # Header line
        self.setStrokeColor(colors.HexColor("#808A92"))
        self.setLineWidth(0.5)
        self.line(54, 745, 558, 745)
        
        # Footer line
        self.line(54, 52, 558, 52)
        
        # Footer text
        self.setFont("Helvetica", 8)
        self.drawString(54, 40, "Confidencial - Propiedad de Trabs")
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(558, 40, page_text)
        
        self.restoreState()

def create_prd_report(output_pdf_path, logo_path):
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )

    styles = getSampleStyleSheet()
    
    primary_color = colors.HexColor("#2D3033")
    accent_color = colors.HexColor("#F3A500")
    secondary_color = colors.HexColor("#F3A500")
    neutral_color = colors.HexColor("#808A92")
    dark_slate = colors.HexColor("#2D3033")
    body_text_color = colors.HexColor("#1F2115")
    
    styles['Normal'].textColor = body_text_color
    styles['Normal'].fontSize = 10
    styles['Normal'].leading = 14
    styles['Normal'].fontName = 'Helvetica'
    
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=28,
        textColor=primary_color,
        alignment=1,
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#475569"),
        alignment=1,
        spaceAfter=25
    )
    
    meta_style = ParagraphStyle(
        'CoverMeta',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=14,
        textColor=dark_slate,
        alignment=1,
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=primary_color,
        spaceBefore=16,
        spaceAfter=10,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=dark_slate,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'MainBody',
        parent=styles['Normal'],
        spaceAfter=8
    )

    bullet_style = ParagraphStyle(
        'BulletText',
        parent=styles['Normal'],
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=8,
        leading=11,
        textColor=body_text_color
    )

    table_cell_bold_style = ParagraphStyle(
        'TableCellBold',
        parent=table_cell_style,
        fontName='Helvetica-Bold',
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7,
        leading=9.5,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=4
    )

    story = []

    # PAGE 1: COVER
    story.append(Spacer(1, 40))
    if os.path.exists(logo_path):
        try:
            pil_img = PILImage.open(logo_path)
            w, h = pil_img.size
            aspect = h / w
            pdf_w = 240
            pdf_h = 240 * aspect
            story.append(Image(logo_path, width=pdf_w, height=pdf_h))
            story.append(Spacer(1, 35))
        except Exception as e:
            print(f"Error loading logo: {e}")
            story.append(Spacer(1, 60))
    else:
        story.append(Spacer(1, 100))

    story.append(Paragraph("DOCUMENTO MAESTRO: PRD Y SISTEMA DE DISEÑO", title_style))
    story.append(Paragraph("Especificaciones del Producto, Casos de Uso y Sistema Visual (Design System)<br/><b>TRABS</b>", subtitle_style))
    
    story.append(Spacer(1, 60))
    
    metadata_text = """
    <b>Empresa:</b> Trabs<br/>
    <b>Fecha de Emisión:</b> Agosto 2026<br/>
    <b>Estado del Documento:</b> Especificación Oficial / Operativo E2E<br/>
    <b>Autor:</b> Antigravity Coding Assistant & Trabs Dev Team<br/>
    <b>Alcance:</b> Suite Gerencial PyQt6 (Desktop) y App Terreno React Native Expo (Mobile)
    """
    story.append(Paragraph(metadata_text, meta_style))
    story.append(PageBreak())

    # PAGE 2: TABLE OF CONTENTS
    toc_title_style = ParagraphStyle(
        'TOCTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=primary_color,
        spaceBefore=10,
        spaceAfter=20,
        keepWithNext=True
    )
    
    story.append(Paragraph("Índice de Contenido", toc_title_style))
    story.append(Spacer(1, 10))
    
    toc_item_style = ParagraphStyle(
        'TOCItem',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=dark_slate
    )
    
    toc_item_sub_style = ParagraphStyle(
        'TOCItemSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=body_text_color,
        leftIndent=15
    )
    
    toc_page_style = ParagraphStyle(
        'TOCPage',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=primary_color,
        alignment=2
    )
    
    def make_toc_row(title_text, page_num, is_sub=False):
        style = toc_item_sub_style if is_sub else toc_item_style
        return [
            Paragraph(title_text, style),
            Paragraph(f"Pág. {page_num}", toc_page_style)
        ]
    
    toc_data = [
        make_toc_row("PARTE 1: DOCUMENTO DE REQUISITOS DEL PRODUCTO (PRD)", 3),
        make_toc_row("1. Resumen Ejecutivo y Objetivos Core", 3, is_sub=True),
        make_toc_row("2. Matriz de Roles, Usuarios y Permisos", 3, is_sub=True),
        make_toc_row("3. Especificación de Herramientas del Ecosistema", 4, is_sub=True),
        make_toc_row("Herramienta 1: Ingesta de Presupuesto y Cubicaciones", 4, is_sub=True),
        make_toc_row("Herramienta 2: Trackeo de Avances y Asistencia Móvil", 4, is_sub=True),
        make_toc_row("Herramienta 3: Emisión de Estados de Pago (EDP)", 4, is_sub=True),
        make_toc_row("Herramienta 4: Panel de Estadísticas y Matplotlib", 5, is_sub=True),
        make_toc_row("4. Modelo de Datos y Reglas de Negocio", 5, is_sub=True),
        make_toc_row("PARTE 2: MANUAL DE ESTILOS Y SISTEMA DE DISEÑO (DESIGN SYSTEM)", 6),
        make_toc_row("1. Identidad de Marca y DNA Visual", 6, is_sub=True),
        make_toc_row("2. Paleta de Colores (Design Tokens)", 6, is_sub=True),
        make_toc_row("3. Tipografía y Jerarquía Visual", 6, is_sub=True),
        make_toc_row("4. Especificaciones UI/UX por Componente", 7, is_sub=True),
        make_toc_row("5. Patrones de Feedback, Prevención de Errores y Concurrencia", 8, is_sub=True)
    ]
    
    t_toc = Table(toc_data, colWidths=[420, 84])
    t_toc.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor("#F1F5F9")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_toc)
    story.append(PageBreak())

    # SECTION 1: PRD
    story.append(Paragraph("PARTE 1: DOCUMENTO DE REQUISITOS DEL PRODUCTO (PRD)", h1_style))
    story.append(Paragraph("1. Resumen Ejecutivo y Objetivos Core", h2_style))
    story.append(Paragraph(
        "<b>Trabs</b> es un ecosistema de software multiplataforma diseñado para centralizar y digitalizar el "
        "control de avances en proyectos de construcción especializadas (protección pasiva contra incendios, "
        "recubrimientos intumescentes, morteros ignífugos, aislación acústica y sellos de pasadas). "
        "El nombre 'Trabs' proviene del término en latín para 'viga', simbolizando solidez estructural y soporte técnico. "
        "El objetivo principal es resolver la fragmentación del registro de avances en terreno, eliminar la duplicación "
        "de digitación técnica y automatizar la facturación inmutable mediante Estados de Pago (EDP).",
        body_style
    ))
    
    story.append(Paragraph("2. Matriz de Roles, Usuarios y Permisos", h2_style))
    story.append(Paragraph(
        "El sistema soporta dos perfiles principales con privilegios estrictamente delimitados a nivel de backend (RLS en Supabase):",
        body_style
    ))
    
    roles_table_data = [
        [Paragraph("<b>Rol</b>", table_header_style), Paragraph("<b>Módulo Asignado</b>", table_header_style), Paragraph("<b>Funcionalidades Clave y Alcance</b>", table_header_style)],
        [
            Paragraph("Gerencia / Admin", table_cell_bold_style),
            Paragraph("Trabs Gerencia<br/>(Desktop PyQt6)", table_cell_style),
            Paragraph("• Ingesta inicial de partidas y cubicaciones desde Excel.<br/>• Asignación y gestión de Jefes de Obra.<br/>• Control de personal y asistencia.<br/>• Catálogo de materiales por obra.<br/>• Auditoría fotográfica y aprobación de avances.<br/>• Generación inmutable de Estados de Pago (EDP).", table_cell_style)
        ],
        [
            Paragraph("Jefe de Obra / Faena", table_cell_bold_style),
            Paragraph("Trabs Terreno<br/>(Mobile React Native)", table_cell_style),
            Paragraph("• Captura offline de avances por cuadrícula y partida.<br/>• Registro de asistencia de personal (presentes/ausentes).<br/>• Bitácora diaria y reporte de novedades/incidentes.<br/>• Solicitud y registro de consumo de materiales.<br/>• Sincronización automática al recuperar red.", table_cell_style)
        ]
    ]
    t_roles = Table(roles_table_data, colWidths=[100, 110, 294])
    t_roles.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#808A92")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_roles)
    story.append(Spacer(1, 15))

    story.append(Paragraph("3. Módulos y Flujo Operativo Funcional", h2_style))
    story.append(Paragraph("<b>Módulo 1: Ingesta de Presupuestos (Excel)</b>", bullet_style))
    story.append(Paragraph(
        "Permite cargar la estructura jerárquica de la obra (Ítem, Sub-ítem, Descripción, Unidad, Cantidad Contratada, "
        "Precio Unitario, Espesor/Micras) desde archivos <code>.xlsx</code> validados automáticamente. Asigna un color HEX "
        "único por obra para rápida diferenciación visual en tarjetas y reportes.",
        body_style
    ))
    
    story.append(Paragraph("<b>Módulo 2: Registro de Avances en Faena (Offline-First)</b>", bullet_style))
    story.append(Paragraph(
        "Los Jefes de Obra registran avances físicos especificando ubicación física, elemento estructural, cantidad o micras ejecutadas "
        "y captura obligatoria de fotografía como respaldo de auditoría técnica. Los datos se persisten localmente en SQLite "
        "y se sincronizan a Supabase Storage y Base de Datos cuando hay conectividad.",
        body_style
    ))

    story.append(Paragraph("<b>Módulo 3: Emisión Inmutable de Estados de Pago (EDP)</b>", bullet_style))
    story.append(Paragraph(
        "Generador de documentos oficiales en formato PDF apaisado. Realiza el cálculo automático de avances del período, "
        "acumulados anteriores, retenciones, amortización de anticipos y saldo neto por cobrar, congelando los registros "
        "asociados para impedir alteraciones retroactivas.",
        body_style
    ))

    story.append(Paragraph("<b>Módulo 4: Control de Asistencia, Personal y Materiales</b>", bullet_style))
    story.append(Paragraph(
        "Módulo gerencial y móvil para pase de lista diario por cuadrilla, seguimiento de dotación activa, cálculo de horas "
        "y control de inventario de materiales consumidos en faena por partida técnica.",
        body_style
    ))

    story.append(Paragraph("<b>Módulo 5: Panel de Estadísticas y Matplotlib</b>", bullet_style))
    story.append(Paragraph(
        "Incrustación de dashboards analíticos en PyQt6: curva S de avance acumulado, barras por categoría "
        "(Ubicación / Estructura / Material) con selector agrupado/apilado, dona de estados de revisión y "
        "comparativa de presupuesto contratado vs ejecutado vs pendiente.",
        body_style
    ))

    story.append(PageBreak())

    # SECTION 2: DESIGN SYSTEM
    story.append(Paragraph("PARTE 2: MANUAL DE ESTILOS Y SISTEMA DE DISEÑO (DESIGN SYSTEM)", h1_style))
    story.append(Paragraph("1. Identidad de Marca y DNA Visual", h2_style))
    story.append(Paragraph(
        "El sistema visual de <b>Trabs</b> combina robustez estructural industrial con claridad ejecutiva. "
        "Su estética se fundamenta en un contraste equilibrado entre el tono <b>Antracita Oscuro (#2D3033)</b>, "
        "el distintivo <b>Ámbar Dorado (#F3A500)</b> como acento de marca y CTA, y una escala de neutros técnicos "
        "<b>(#808A92, #414445, #4A5156)</b> sobre un fondo de alta legibilidad <b>(#F4F6F8)</b>.",
        body_style
    ))

    story.append(Paragraph("2. Paleta de Colores Curada Trabs (Design Tokens)", h2_style))
    
    color_tokens_data = [
        [Paragraph("<b>Rol / Token</b>", table_header_style), Paragraph("<b>Nombre del Color</b>", table_header_style), Paragraph("<b>Hex</b>", table_header_style), Paragraph("<b>Uso en Interfaz</b>", table_header_style)],
        [Paragraph("Primary / CTA", table_cell_bold_style), Paragraph("Ámbar Solar", table_cell_style), Paragraph("<code>#F3A500</code>", table_cell_style), Paragraph("Botones de acción principal, acento de marca, progreso y destacados.", table_cell_style)],
        [Paragraph("Dark Surface", table_cell_bold_style), Paragraph("Antracita Oscuro", table_cell_style), Paragraph("<code>#2D3033</code>", table_cell_style), Paragraph("Fondo de barra lateral (Sidebar), cabeceras de tablas y modales.", table_cell_style)],
        [Paragraph("Neutral / Border", table_cell_bold_style), Paragraph("Gris Acero", table_cell_style), Paragraph("<code>#808A92</code>", table_cell_style), Paragraph("Bordes de tarjetas, rejillas de tablas, subtítulos y textos secundarios.", table_cell_style)],
        [Paragraph("Secondary Dark", table_cell_bold_style), Paragraph("Carbón Pizarra", table_cell_style), Paragraph("<code>#414445</code>", table_cell_style), Paragraph("Fondos oscuros secundarios y separadores de sección.", table_cell_style)],
        [Paragraph("Slate Medium", table_cell_bold_style), Paragraph("Pizarra Medio", table_cell_style), Paragraph("<code>#4A5156</code>", table_cell_style), Paragraph("Iconografía secundaria, badges de estado y acentos de navegación.", table_cell_style)],
        [Paragraph("Light Clean", table_cell_bold_style), Paragraph("Gris Hielo", table_cell_style), Paragraph("<code>#F4F6F8</code>", table_cell_style), Paragraph("Fondo principal de la aplicación y áreas de trabajo centrales.", table_cell_style)],
        [Paragraph("Success", table_cell_bold_style), Paragraph("Verde Esmeralda", table_cell_style), Paragraph("<code>#10B981</code>", table_cell_style), Paragraph("Avances aprobados, obras activas e indicadores de sincronización.", table_cell_style)],
        [Paragraph("Danger", table_cell_bold_style), Paragraph("Rojo Alerta", table_cell_style), Paragraph("<code>#EF4444</code>", table_cell_style), Paragraph("Avances rechazados, obras pausadas y botón de cierre de sesión.", table_cell_style)]
    ]
    t_colors = Table(color_tokens_data, colWidths=[90, 84, 70, 260])
    t_colors.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#808A92")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_colors)
    story.append(Spacer(1, 10))

    story.append(Paragraph("3. Tipografía y Jerarquía Visual", h2_style))
    story.append(Paragraph(
        "Se utilizan dos tipografías complementarias de Google Fonts:<br/>"
        "• <b>Montserrat (Headings & Valores KPI):</b> Utilizada en títulos de sección (22px-24px, negrita) y métricas de tarjetas KPI (28px) para transmitir presencia gerencial y solidez.<br/>"
        "• <b>Inter (Cuerpo, Tablas y Formularios):</b> Optimizada para lectura digital densa en celdas de tabla (13px-14px), etiquetas de formulario e inputs.",
        body_style
    ))

    story.append(Spacer(1, 10))
    story.append(Paragraph("4. Especificaciones UI/UX por Componente", h2_style))
    story.append(Paragraph("<b>Barra Lateral (`#Sidebar`)</b>: Ancho estático 250px en Antracita Oscuro (`#2D3033`) con sombra proyectada. Logo institucional `logo_trabs_nombre_sf.png` y botones con hover interactivo y selección con acento ámbar (`#F3A500`).", bullet_style))
    story.append(Paragraph("<b>Tarjetas de Obra Clickeables (`ClickableObraCard`)</b>: Bordes redondeados (12px), franja de color lateral de 8px según la paleta de la obra, indicador pulsante de estado operativo y sombra flotante en hover.", bullet_style))
    story.append(Paragraph("<b>Visor de Evidencia de Fotografías</b>: Carga asíncrona de fotografías en panel lateral split (`ImageDownloader`), permitiendo auditar micras/m² ejecutados y aprobar/rechazar con 1 clic.", bullet_style))
    story.append(Paragraph("<b>Modales de Confirmación y Asistentes</b>: Asistentes por pasos para ingesta de Excel y emisión de EDP, deshabilitando botones y mostrando estado (`'Procesando...'`) para evitar doble clic accidental.", bullet_style))

    story.append(PageBreak())

    story.append(Paragraph("5. Patrones de Feedback, Prevención de Errores y Concurrencia", h1_style))
    story.append(Paragraph(
        "Para ofrecer una experiencia de usuario de nivel producción en ambas plataformas, se siguen cuatro principios rectores:",
        body_style
    ))
    
    principles = [
        "1. <b>Zero-Freeze UX (QThread / Async):</b> Ninguna llamada de red I/O a Supabase o Storage bloquea el hilo de la interfaz de usuario en PyQt6 o React Native.",
        "2. <b>Prevención Activa de Colisiones de Datos:</b> La emisión de Estados de Pago utiliza la función <code>get_next_edp_number</code> con bloqueo SQL <code>SHARE ROW EXCLUSIVE</code>, garantizando folios secuenciales libres de condiciones de carrera.",
        "3. <b>Inmutabilidad de Avances Facturados:</b> Al asociar un <code>estado_pago_id</code> a un avance, la base de datos y la UI congelan el registro impidiendo modificaciones o dobles cobros.",
        "4. <b>Resiliencia Offline-First:</b> La app móvil opera íntegramente sin conectividad apoyándose en SQLite, sincronizando de forma segura cuando el estado de la red cambia a online."
    ]
    for p in principles:
        story.append(Paragraph(p, bullet_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print("PRD PDF generated successfully.")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "INFO PROYECTO")
    os.makedirs(output_dir, exist_ok=True)
    
    output_pdf = os.path.join(output_dir, "PRD y Design System - Trabs.pdf")
    logo = os.path.join(output_dir, "LOGOS", "logo_trabs_nombre_sf.png")
    if not os.path.exists(logo):
        logo = os.path.join(output_dir, "LOGOS", "logo_trabs_circular_sf.png")
    if not os.path.exists(logo):
        logo = os.path.join(output_dir, "LOGOS", "LOGO_CON_LETRAS.png")
        
    try:
        create_prd_report(output_pdf, logo)
    except PermissionError:
        output_pdf_alt = os.path.join(output_dir, "PRD y Design System - Trabs_Actualizado.pdf")
        print(f"Advertencia: Guardando en alternativa: {output_pdf_alt}")
        create_prd_report(output_pdf_alt, logo)
