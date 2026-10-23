import os
import sys
import datetime
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
    Custom canvas that performs two-pass rendering to dynamically display the 
    total page count in the footer, and suppresses headers/footers on the cover page.
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
        # Page 1 is the cover page — suppress headers and footers
        if self._pageNumber == 1:
            self.saveState()
            # Top primary color bar
            self.setFillColor(colors.HexColor("#3D523C"))
            self.rect(0, 772, 612, 20, stroke=0, fill=1)
            # Bottom primary color bar
            self.setFillColor(colors.HexColor("#262B29"))
            self.rect(0, 0, 612, 30, stroke=0, fill=1)
            self.restoreState()
            return

        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#262B29"))
        
        # Header
        self.drawString(54, 752, "GRYPHUS CONECT")
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#4A5156"))
        self.drawRightString(558, 752, "Reporte de Arquitectura y Estado Actual")
        
        # Header line
        self.setStrokeColor(colors.HexColor("#808A92"))
        self.setLineWidth(0.5)
        self.line(54, 745, 558, 745)
        
        # Footer line
        self.line(54, 52, 558, 52)
        
        # Footer text
        self.setFont("Helvetica", 8)
        self.drawString(54, 40, "Confidencial - Propiedad de GryPhus Conect")
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(558, 40, page_text)
        
        self.restoreState()

def create_report(output_pdf_path, logo_path):
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,  # Leave room for header
        bottomMargin=72 # Leave room for footer
    )

    styles = getSampleStyleSheet()
    
    primary_color = colors.HexColor("#262B29")
    accent_color = colors.HexColor("#3D523C")
    secondary_color = colors.HexColor("#3D523C")
    dark_slate = colors.HexColor("#262B29")
    body_text_color = colors.HexColor("#1F2115")
    
    styles['Normal'].textColor = body_text_color
    styles['Normal'].fontSize = 10
    styles['Normal'].leading = 14
    styles['Normal'].fontName = 'Helvetica'
    
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=30,
        textColor=primary_color,
        alignment=1, # Center
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#475569"),
        alignment=1, # Center
        spaceAfter=25
    )
    
    meta_style = ParagraphStyle(
        'CoverMeta',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=14,
        textColor=dark_slate,
        alignment=1, # Center
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

    # ================= PAGE 1: COVER =================
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
        
    story.append(Paragraph("REPORTE DE ARQUITECTURA Y ESTADO ACTUAL", title_style))
    story.append(Paragraph("Sistema de Control de Obras y Registro de Avances en Terreno<br/><b>GRYPHUS CONECT</b>", subtitle_style))
    
    story.append(Spacer(1, 60))
    
    metadata_text = """
    <b>Organización:</b> GryPhus Conect<br/>
    <b>Fecha de Emisión:</b> Agosto 2026<br/>
    <b>Estado del Proyecto:</b> Operativo E2E / Ingesta, Control de Personal, Avances y EDPs Activos<br/>
    <b>Autor:</b> Antigravity Coding Assistant & GryPhus Conect Dev Team<br/>
    <b>Documento:</b> Arquitectura Técnica y Modelo de Base de Datos (Supabase/Postgres)
    """
    story.append(Paragraph(metadata_text, meta_style))
    story.append(PageBreak())

    # ================= PAGE 2: TABLE OF CONTENTS =================
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
        make_toc_row("1. Resumen Ejecutivo del Sistema", 3),
        make_toc_row("2. Conexión a la Base de Datos e Infraestructura", 3),
        make_toc_row("3. Arquitectura de la Aplicación de Escritorio (gryphus_conect_gerencia)", 4),
        make_toc_row("Componentes y Módulos Clave", 4, is_sub=True),
        make_toc_row("Mapeo e Ingesta de Datos desde Excel", 4, is_sub=True),
        make_toc_row("Columnas del Excel Mapeadas", 4, is_sub=True),
        make_toc_row("4. Arquitectura de la Aplicación Móvil (gryphus_conect_terreno)", 5),
        make_toc_row("Sincronización del Catálogo (Download)", 5, is_sub=True),
        make_toc_row("Mecánica de Registro y Caché (Offline Write)", 5, is_sub=True),
        make_toc_row("Pipeline de Sincronización en Segundo Plano (Upload)", 5, is_sub=True),
        make_toc_row("Estructura de la Base de Datos Local SQLite", 5, is_sub=True),
        make_toc_row("5. Estructura del Modelo de Datos (Base de Datos)", 6),
        make_toc_row("Tabla: perfiles_usuario", 6, is_sub=True),
        make_toc_row("Tabla: obras", 6, is_sub=True),
        make_toc_row("Tabla: obras_jefes_obra", 6, is_sub=True),
        make_toc_row("Tabla: items_obra (Cubicaciones y Presupuesto)", 7, is_sub=True),
        make_toc_row("Tabla: avances", 8, is_sub=True),
        make_toc_row("Tabla: estados_pago (EDP)", 8, is_sub=True),
        make_toc_row("Tabla: tipos_maestro y maestros (Control Personal)", 8, is_sub=True),
        make_toc_row("Tabla: asistencia_diaria y detalle", 8, is_sub=True),
        make_toc_row("6. Seguridad y Políticas de Acceso a Nivel de Fila (RLS)", 9),
        make_toc_row("Detalle de Comportamiento y Seguridad", 9, is_sub=True),
        make_toc_row("Prevención de Recursión Infinita", 9, is_sub=True),
        make_toc_row("7. Diagrama de Flujo de Datos Simplificado", 10),
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

    # ================= PAGE 3: EXECUTIVE SUMMARY & INFRASTRUCTURE =================
    story.append(Paragraph("1. Resumen Ejecutivo del Sistema", h1_style))
    story.append(Paragraph(
        "El sistema <b>GryPhus Conect</b> es una solución tecnológica integral multiplataforma diseñada "
        "para digitalizar y centralizar en tiempo real el control de avances físicos, presupuestos, control de personal "
        "y asistencia, bitácora diaria de faena y la emisión inmutable de Estados de Pago (EDP) en obras de construcción especializadas. "
        "La arquitectura del sistema está basada en un backend centralizado en <b>Supabase</b> (PostgreSQL, Auth y Storage) y dos aplicaciones "
        "principales con roles claramente delimitados:",
        body_style
    ))
    
    story.append(Paragraph(
        "• <b>Aplicación de Escritorio (GryPhus Conect Gerencia):</b> Desarrollada en Python utilizando <b>PyQt6</b>. "
        "Funciona como panel gerencial y de operaciones. Permite la ingesta inicial de presupuestos desde planillas Excel "
        "estructuradas, asignación de Jefes de Obra, administración de materiales y personal (maestros y cargos), monitoreo "
        "visual analítico enriquecido con gráficos de Matplotlib, auditoría de avances con fotografías y facturación/emisión de Estados de Pago (EDP) en PDF.",
        bullet_style
    ))
    
    story.append(Paragraph(
        "• <b>Aplicación Móvil (gryphus_conect_terreno):</b> Desarrollada en <b>React Native</b> con <b>Expo SDK 54</b>. "
        "Diseñada para los Jefes de Obra en terreno. Funciona bajo el paradigma <b>Offline-First</b> mediante una base de datos local "
        "<b>SQLite (trackeo.db)</b> y un pipeline de sincronización en segundo plano con Supabase. Permite el registro rápido de avances por m², "
        "captura obligatoria de fotos, bitácora diaria, consumo de insumos y control de asistencia diaria por maestro.",
        bullet_style
    ))
    
    story.append(Spacer(1, 10))
    story.append(Paragraph("2. Conexión a la Base de Datos e Infraestructura", h1_style))
    story.append(Paragraph(
        "Tanto la aplicación de escritorio como la móvil se conectan de manera directa y segura al backend de "
        "<b>Supabase</b> a través de sus respectivos SDKs oficiales (Python y JavaScript/TypeScript). "
        "La autenticación se realiza mediante Supabase Auth con JSON Web Tokens (JWT) que expiran periódicamente. "
        "Las variables de configuración se almacenan en archivos locales <code>.env</code>:",
        body_style
    ))

    env_table_data = [
        [Paragraph("<b>Variable de Entorno</b>", table_header_style), Paragraph("<b>Descripción / Rol en el Sistema</b>", table_header_style)],
        [Paragraph("<code>SUPABASE_URL</code>", table_cell_bold_style), Paragraph("Punto de enlace HTTP (Endpoint API) del proyecto de Supabase en la nube.", table_cell_style)],
        [Paragraph("<code>SUPABASE_KEY</code>", table_cell_bold_style), Paragraph("Clave pública anónima (anon key) utilizada para interactuar con la API del cliente respetando las políticas RLS.", table_cell_style)]
    ]
    t_env = Table(env_table_data, colWidths=[150, 354])
    t_env.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_env)
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "<b>Seguridad RLS (Row-Level Security):</b> El acceso a las tablas críticas está restringido a nivel de fila. "
        "Los Jefes de Obra autenticados solo pueden visualizar las obras que tienen asignadas y solo pueden reportar o ver "
        "avances asociados a su propio ID de usuario (<code>auth.uid()</code>). La función <code>public.es_administrador()</code> "
        "otorga a la administración acceso total sin generar bucles de recursión.",
        body_style
    ))

    story.append(PageBreak())

    # ================= PAGE 4: DESKTOP APP ARCHITECTURE =================
    story.append(Paragraph("3. Arquitectura de la Aplicación de Escritorio (gryphus_conect_gerencia)", h1_style))
    story.append(Paragraph(
        "La aplicación de escritorio actúa como el núcleo administrativo de la operación. Está estructurada bajo el "
        "patrón de diseño MVC (Modelo-Vista-Controlador) y desacopla la lógica de interfaz de las llamadas de red.",
        body_style
    ))
    
    story.append(Paragraph("Componentes y Módulos Clave:", h2_style))
    
    story.append(Paragraph(
        "• <b>Interfaz de Usuario Responsiva:</b> Desarrollada con <b>PyQt6</b>. Utiliza una hoja de estilos unificada "
        "(<code>style.qss</code>) para definir un diseño premium con bordes suaves, efectos de sombreado en tarjetas (QGraphicsDropShadowEffect) "
        "y colores dinámicos asociados a cada obra.",
        bullet_style
    ))
    
    story.append(Paragraph(
        "• <b>Modelo de Hilos de Trabajo (QThreads):</b> Para evitar congelamientos de la interfaz gráfica durante "
        "las llamadas a Supabase, se implementan workers personalizados (<code>workers.py</code>) que heredan de <code>QThread</code>: "
        "<code>FetchJefesWorker</code>, <code>ProcessIngestaWorker</code>, <code>FetchObraDetailsWorker</code>, <code>FetchMaestrosWorker</code>, "
        "<code>FetchEDPWorker</code> y <code>GenerateEDPWorker</code>.",
        bullet_style
    ))
    
    story.append(Paragraph(
        "• <b>Bitácora y Dashboard Analítico:</b> El módulo <code>avances_window.py</code> integra gráficos interactivos "
        "mediante <b>Matplotlib</b>. Muestra: 1) Progreso temporal acumulado (aprobados vs. total); 2) Avance porcentual por categoría (Ubicación, Estructura, Material); "
        "3) Gráfico de dona con la distribución de estados de revisión; y 4) Comparativa económica del presupuesto (Contratado vs Aprobado vs Pendiente).",
        bullet_style
    ))
    
    story.append(Paragraph(
        "• <b>Módulo de Control de Personal y Asistencia:</b> Vista <code>control_personal_view.py</code> para gestionar tipos de maestro, tarifas de sueldo diario, "
        "fichas de trabajadores y asignación a obras, con auditoría de asistencia diaria en <code>reportes_asistencia_view.py</code>.",
        bullet_style
    ))

    story.append(Paragraph(
        "• <b>Emisión de Estados de Pago (EDP):</b> Vista <code>edp_tab.py</code>, controlador <code>edp_controller.py</code> y generador PDF "
        "<code>pdf_edp_generator.py</code> para congelar avances aprobados, aplicar retenciones y anticipos, solicitar folios correlativos seguros "
        "con <code>get_next_edp_number</code> y maquetar el documento PDF oficial en Supabase Storage.",
        bullet_style
    ))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Mapeo e Ingesta de Datos desde Excel:", h2_style))
    story.append(Paragraph(
        "La ingesta de obras y cubicaciones se realiza a través de <code>ingesta_view.py</code> y es procesada por "
        "<code>IngestaController</code> en <code>controller.py</code>. El flujo de ingesta sigue estos pasos estrictos:",
        body_style
    ))
    
    steps_ingesta = [
        "1. El administrador ingresa el <b>Nombre</b>, selecciona un <b>Jefe de Obra</b> y le asigna un <b>Color</b> institucional.",
        "2. Se carga una planilla Excel y se procesa la hoja denominada <b>'CUBICACION'</b>.",
        "3. Se omiten las primeras 7 filas (<code>skiprows=7</code>) para saltar el encabezado comercial.",
        "4. Se limpia el dataset eliminando filas donde la columna <code>UBICACIÓN</code> sea nula.",
        "5. El sistema detecta los materiales únicos y abre un diálogo interactivo (<code>PreciosMaterialesDialog</code>) "
        "para definir el <b>Precio Unitario de Contrato</b> para cada material.",
        "6. Se genera un ID de Obra (UUID) y se inserta en <code>obras</code>, subiendo una copia de respaldo del Excel a <code>archivos_obras</code>.",
        "7. Se parsean las 22 columnas de interés mapeándolas a <code>items_obra</code> realizando un bulk insert a Supabase."
    ]
    for step in steps_ingesta:
        story.append(Paragraph(step, bullet_style))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Columnas del Excel Mapeadas:", h2_style))
    
    col_mapping_data = [
        [Paragraph("<b>Columna del Excel</b>", table_header_style), Paragraph("<b>Atributo en items_obra</b>", table_header_style), Paragraph("<b>Columna del Excel</b>", table_header_style), Paragraph("<b>Atributo en items_obra</b>", table_header_style)],
        [Paragraph("UBICACIÓN", table_cell_bold_style), Paragraph("ubicacion (varchar)", table_cell_style), Paragraph("PLANO", table_cell_bold_style), Paragraph("plano (varchar)", table_cell_style)],
        [Paragraph("DESCRIPCIÓN EN PLANO", table_cell_bold_style), Paragraph("descripcion_plano (text)", table_cell_style), Paragraph("ESTRUCTURA", table_cell_bold_style), Paragraph("estructura (varchar)", table_cell_style)],
        [Paragraph("DIMENSIONES", table_cell_bold_style), Paragraph("dimension (varchar)", table_cell_style), Paragraph("PERFIL", table_cell_bold_style), Paragraph("perfil (varchar)", table_cell_style)],
        [Paragraph("CANT.", table_cell_bold_style), Paragraph("cantidad (numeric)", table_cell_style), Paragraph("CANTIDAD ESTRUCTURAS", table_cell_bold_style), Paragraph("cantidad_estructuras (numeric)", table_cell_style)],
        [Paragraph("LARGO [mm]", table_cell_bold_style), Paragraph("largo_mm (numeric)", table_cell_style), Paragraph("CARAS EXPTAS.", table_cell_bold_style), Paragraph("caras_expuestas (int4)", table_cell_style)],
        [Paragraph("PERÍMETRO EXPUESTO [mm]", table_cell_bold_style), Paragraph("perimetro_expuesto_mm (numeric)", table_cell_style), Paragraph("RESIST. AL FUEGO", table_cell_bold_style), Paragraph("resist_fuego (varchar)", table_cell_style)],
        [Paragraph("MASIV. (M-1)", table_cell_bold_style), Paragraph("masividad_m1 (numeric)", table_cell_style), Paragraph("ÁREA EXPUESTA [m2]", table_cell_bold_style), Paragraph("area_expuesta_m2 (numeric)", table_cell_style)],
        [Paragraph("MATERIAL", table_cell_bold_style), Paragraph("material (varchar)", table_cell_style), Paragraph("CERTIFICACION", table_cell_bold_style), Paragraph("certificacion (varchar)", table_cell_style)],
        [Paragraph("MICRAS", table_cell_bold_style), Paragraph("micras (numeric)", table_cell_style), Paragraph("FORMULA", table_cell_bold_style), Paragraph("formula (text)", table_cell_style)],
        [Paragraph("TINETAS", table_cell_bold_style), Paragraph("tinetas (numeric)", table_cell_style), Paragraph("ESPESOR (mm)", table_cell_bold_style), Paragraph("espesor_mm (numeric)", table_cell_style)],
        [Paragraph("SACOS", table_cell_bold_style), Paragraph("sacos (numeric)", table_cell_style), Paragraph("ANOTACIONES", table_cell_bold_style), Paragraph("anotaciones (text)", table_cell_style)]
    ]
    t_mapping = Table(col_mapping_data, colWidths=[130, 122, 130, 122])
    t_mapping.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_mapping)

    story.append(PageBreak())

    # ================= PAGE 5: MOBILE APP ARCHITECTURE =================
    story.append(Paragraph("4. Arquitectura de la Aplicación Móvil (gryphus_conect_terreno)", h1_style))
    story.append(Paragraph(
        "La aplicación móvil está construida sobre <b>React Native</b> con el ecosistema <b>Expo SDK 54</b>. "
        "Su objetivo es la captura en terreno de avances, bitácoras, consumo de materiales y asistencia de maestros bajo el paradigma <b>Offline-First</b>.",
        body_style
    ))
    
    story.append(Paragraph("Sincronización del Catálogo (Download):", h2_style))
    story.append(Paragraph(
        "Al iniciar sesión, la función <code>syncCatalog(jefeId)</code> descarga el perfil del usuario, relaciones obra-jefe, "
        "obras asignadas, ítems de cubicación, catálogo de materiales y maestros asignados. "
        "Toda la información se guarda en la base de datos <b>SQLite</b> local del smartphone (<code>trackeo.db</code>).",
        body_style
    ))

    story.append(Paragraph("Mecánica de Registro y Caché (Offline Write):", h2_style))
    story.append(Paragraph(
        "Cuando el Jefe de Obra reporta un avance o asistencia, se realiza el siguiente flujo local:",
        body_style
    ))
    story.append(Paragraph("1. <b>Captura Obligatoria de Foto:</b> Evidencia fotográfica almacenada en el sistema de archivos local.", bullet_style))
    story.append(Paragraph("2. <b>Marcas Temporales Estrictas:</b> Se guardan <code>fecha_captura_local</code> (reloj local) y <code>fecha_subida_servidor</code> (completada al subir).", bullet_style))
    story.append(Paragraph("3. <b>Guardado en SQLite:</b> El registro se inserta con <code>synced = 0</code> para operar de forma inmutable sin internet.", bullet_style))

    story.append(Paragraph("Pipeline de Sincronización en Segundo Plano (Upload):", h2_style))
    story.append(Paragraph(
        "La sincronización hacia Supabase se gestiona mediante <code>sync.js</code>:",
        body_style
    ))
    story.append(Paragraph("• <b>Monitoreo con NetInfo:</b> Evalúa la conectividad con <code>@react-native-community/netinfo</code> e inicia la subida al detectar red.", bullet_style))
    story.append(Paragraph("• <b>Tratamiento de Fotos Hermes:</b> Convierte la foto local de Blob a Base64 y ArrayBuffer para subirse a Supabase Storage (<code>avance-fotos</code>, <code>bitacora-fotos</code>, <code>asistencia-fotos</code>).", bullet_style))
    story.append(Paragraph("• <b>Confirmación y Synced Flag:</b> Inserta los datos en Supabase y actualiza SQLite a <code>synced = 1</code>.", bullet_style))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Estructura de la Base de Datos Local SQLite (trackeo.db):", h2_style))
    
    sqlite_schema_desc = """-- Esquemática de trackeo.db
CREATE TABLE perfiles_usuario (id TEXT PRIMARY KEY, nombre TEXT, rol TEXT, email TEXT, clave TEXT);
CREATE TABLE obras (id TEXT PRIMARY KEY, nombre TEXT, estado TEXT, fecha_creacion TEXT, color TEXT);
CREATE TABLE obras_jefes_obra (id TEXT PRIMARY KEY, obra_id TEXT, jefe_obra_id TEXT);
CREATE TABLE items_obra (id TEXT PRIMARY KEY, obra_id TEXT, ubicacion TEXT, plano TEXT, descripcion_plano TEXT, estructura TEXT, dimension TEXT, perfil TEXT, cantidad REAL, unidad TEXT, descripcion TEXT, material_id TEXT);
CREATE TABLE materiales (id TEXT PRIMARY KEY, nombre TEXT, unidad_medida TEXT, rendimiento_teorico_m2 REAL DEFAULT 0.0, descripcion TEXT);
CREATE TABLE reporte_obra (id TEXT PRIMARY KEY, obra_id TEXT, jefe_obra_id TEXT, tipo_reporte TEXT, mensaje TEXT, archivos_adjuntos TEXT, fecha_publicacion TEXT, estado_reb TEXT DEFAULT 'pendiente', respuesta INTEGER DEFAULT 0, mensaje_respuesta TEXT, synced INTEGER DEFAULT 0);
CREATE TABLE reporte_obra_consumos (id TEXT PRIMARY KEY, reporte_obra_id TEXT, material_id TEXT, material TEXT, cantidad REAL, unidad TEXT, fecha TEXT, synced INTEGER DEFAULT 0);
CREATE TABLE avances (id TEXT PRIMARY KEY, item_obra_id TEXT, jefe_obra_id TEXT, foto_url TEXT, comentario TEXT, fecha_captura_local TEXT, fecha_subida_servidor TEXT, estado_revision TEXT DEFAULT 'pendiente', cantidad REAL, synced INTEGER DEFAULT 0);
CREATE TABLE tipos_maestro (id TEXT PRIMARY KEY, nombre TEXT, sueldo_diario REAL DEFAULT 0.0);
CREATE TABLE maestros (id TEXT PRIMARY KEY, nombre TEXT, rut_dni TEXT, tipo_maestro_id TEXT, telefono TEXT, foto_perfil_url TEXT, estado TEXT DEFAULT 'Activo');
CREATE TABLE obras_maestros (obra_id TEXT, maestro_id TEXT, PRIMARY KEY (obra_id, maestro_id));
CREATE TABLE asistencia_diaria (id TEXT PRIMARY KEY, obra_id TEXT, jefe_obra_id TEXT, fecha TEXT, foto_url TEXT, es_correctivo INTEGER DEFAULT 0, observaciones TEXT, fecha_registro TEXT, synced INTEGER DEFAULT 0);
CREATE TABLE asistencia_diaria_detalle (id TEXT PRIMARY KEY, asistencia_id TEXT, maestro_id TEXT, estado TEXT, valor_jornada REAL, observacion TEXT);"""
    
    story.append(Table(
        [[Paragraph(sqlite_schema_desc.replace("\n", "<br/>").replace(" ", "&nbsp;"), code_style)]],
        colWidths=[504],
        style=[
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ('PADDING', (0,0), (-1,-1), 6),
        ]
    ))

    story.append(PageBreak())

    # ================= PAGE 6 & 7: DATABASE SCHEMA TABLES =================
    story.append(Paragraph("5. Estructura del Modelo de Datos (Base de Datos)", h1_style))
    story.append(Paragraph(
        "El motor relacional opera sobre <b>PostgreSQL</b> en la nube de <b>Supabase</b>. A continuación se detallan las tablas del esquema:",
        body_style
    ))

    def make_table_doc(title, cols, widths=[130, 90, 284]):
        table_data = [[Paragraph("<b>Columna</b>", table_header_style), Paragraph("<b>Tipo</b>", table_header_style), Paragraph("<b>Restricciones / Descripción</b>", table_header_style)]]
        for col, dtype, desc in cols:
            table_data.append([
                Paragraph(f"<code>{col}</code>", table_cell_bold_style),
                Paragraph(dtype, table_cell_style),
                Paragraph(desc, table_cell_style)
            ])
        t = Table(table_data, colWidths=widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), primary_color),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        return t

    # Table perfiles_usuario
    story.append(Paragraph("Tabla: <code>perfiles_usuario</code>", h2_style))
    perfiles_cols = [
        ("id", "uuid", "Primary Key. Identificador de autenticación de Supabase (auth.users)."),
        ("nombre", "varchar", "Nombre completo del usuario."),
        ("rol", "varchar", "Rol asignado en el sistema ('administrador', 'jefe_obra')."),
        ("email", "text", "Unique. Correo electrónico institucional."),
        ("clave", "text", "Hash o string de contraseña."),
        ("foto_perfil_url", "text", "URL de la foto de perfil en el Storage.")
    ]
    story.append(make_table_doc("perfiles_usuario", perfiles_cols))
    story.append(Spacer(1, 8))

    # Table obras
    story.append(Paragraph("Tabla: <code>obras</code>", h2_style))
    obras_cols = [
        ("id", "uuid", "Primary Key. Identificador único de la obra física."),
        ("nombre", "varchar", "Nombre representativo del proyecto o faena."),
        ("estado", "varchar", "Estado operativo del proyecto ('Activa', 'Pausada', 'Finalizada')."),
        ("fecha_creacion", "timestamptz", "Fecha y hora de creación del proyecto."),
        ("color", "text", "Código de color HEX para visualización gráfica.")
    ]
    story.append(make_table_doc("obras", obras_cols))
    story.append(Spacer(1, 8))

    # Table obras_jefes_obra
    story.append(Paragraph("Tabla: <code>obras_jefes_obra</code>", h2_style))
    ojo_cols = [
        ("id", "uuid", "Primary Key. Relación de asignación única."),
        ("obra_id", "uuid", "Foreign Key -> obras.id. Referencia a la obra."),
        ("jefe_obra_id", "uuid", "Foreign Key -> perfiles_usuario.id. Referencia al Jefe de Obra asignado.")
    ]
    story.append(make_table_doc("obras_jefes_obra", ojo_cols))
    
    story.append(PageBreak())

    # Table items_obra
    story.append(Paragraph("Tabla: <code>items_obra</code> (Cubicaciones y Presupuesto)", h2_style))
    items_cols = [
        ("id", "uuid", "Primary Key. Identificador del ítem o elemento."),
        ("obra_id", "uuid", "Foreign Key -> obras.id. Obra a la que pertenece."),
        ("ubicacion", "varchar", "Ubicación o sectorización física en faena."),
        ("plano", "varchar", "Código o identificador del plano asociado."),
        ("descripcion_plano", "text", "Glosa descriptiva correspondiente al plano."),
        ("estructura", "varchar", "Elemento de soporte (Viga, Pilar, Diagonal)."),
        ("dimension", "varchar", "Especificaciones dimensionales."),
        ("perfil", "varchar", "Tipo de perfil metálico (H, IPE, Cajón)."),
        ("cantidad", "numeric", "Cantidad total presupuestada."),
        ("area_expuesta_m2", "numeric", "Área expuesta total en m² (métrica principal)."),
        ("precio_unitario_contrato", "numeric", "Valor unitario monetario pactado en el contrato."),
        ("material_id", "uuid", "Foreign Key -> materiales.id. Relación con el material global.")
    ]
    story.append(make_table_doc("items_obra", items_cols))
    story.append(Spacer(1, 8))

    # Table avances
    story.append(Paragraph("Tabla: <code>avances</code>", h2_style))
    avances_cols = [
        ("id", "uuid", "Primary Key. Identificador único de avance."),
        ("item_obra_id", "uuid", "Foreign Key -> items_obra.id. Ítem que registra el avance."),
        ("jefe_obra_id", "uuid", "Foreign Key -> perfiles_usuario.id. Jefe de obra que reporta."),
        ("estado_pago_id", "uuid", "Nullable. Foreign Key -> estados_pago.id. Vínculo al EDP inmutable."),
        ("foto_url", "text", "URL de la foto de evidencia cargada en el Storage."),
        ("cantidad", "numeric", "Cantidad física del avance ejecutado en m²."),
        ("fecha_captura_local", "timestamp", "Fecha y hora en que se registró físicamente en terreno."),
        ("fecha_subida_servidor", "timestamp", "Fecha y hora en que el registro fue insertado en Supabase."),
        ("estado_revision", "varchar", "Estado de aprobación: 'pendiente', 'aprobado', 'rechazado'.")
    ]
    story.append(make_table_doc("avances", avances_cols))
    story.append(Spacer(1, 8))

    # Table estados_pago
    story.append(Paragraph("Tabla: <code>estados_pago</code> (EDP)", h2_style))
    ep_cols = [
        ("id", "uuid", "Primary Key. Identificador del estado de pago."),
        ("obra_id", "uuid", "Foreign Key -> obras.id. Obra que factura."),
        ("numero_estado_pago", "int4", "Folio correlativo interno por obra (1, 2, 3...)."),
        ("fecha_emision", "timestamptz", "Fecha de emisión y consolidación del documento."),
        ("subtotal_pesos", "numeric", "Suma total bruta de los avances incluidos."),
        ("monto_neto", "numeric", "Subtotal menos retención de contrato y anticipo."),
        ("monto_total", "numeric", "Monto total a cobrar (Monto Neto + IVA 19%)."),
        ("archivo_pdf_url", "text", "Enlace al documento PDF generado en Supabase Storage.")
    ]
    story.append(make_table_doc("estados_pago", ep_cols))

    story.append(Spacer(1, 8))

    # Table tipos_maestro & maestros
    story.append(Paragraph("Tablas: <code>tipos_maestro</code> y <code>maestros</code> (Control de Personal)", h2_style))
    maestros_cols = [
        ("tipos_maestro.id", "uuid", "Primary Key. Identificador del cargo."),
        ("tipos_maestro.nombre", "varchar", "Nombre único del cargo (Aplicador, Pintor, Ayudante, Mallero)."),
        ("tipos_maestro.sueldo_diario", "numeric", "Tarifa de pago diaria por jornada completa (1.0)."),
        ("maestros.id", "uuid", "Primary Key. Perfil del trabajador."),
        ("maestros.rut_dni", "varchar", "RUT o DNI único del maestro."),
        ("maestros.tipo_maestro_id", "uuid", "Foreign Key -> tipos_maestro.id.")
    ]
    story.append(make_table_doc("maestros", maestros_cols))

    story.append(PageBreak())

    # ================= PAGE 8: SECURITY & RLS =================
    story.append(Paragraph("6. Seguridad y Políticas de Acceso a Nivel de Fila (RLS)", h1_style))
    story.append(Paragraph(
        "El backend de Supabase implementa políticas de <b>Row-Level Security (RLS)</b>. "
        "Estas directivas interceptan todas las consultas SQL entrantes para verificar los permisos de la sesión del usuario:",
        body_style
    ))
    
    rls_data = [
        [Paragraph("<b>Tabla</b>", table_header_style), Paragraph("<b>Nombre de la Política</b>", table_header_style), Paragraph("<b>Comando</b>", table_header_style), Paragraph("<b>Expresión de Validación (USING / WITH CHECK)</b>", table_header_style)],
        [Paragraph("<code>avances</code>", table_cell_bold_style), Paragraph("authenticated inserta sus avances", table_cell_style), Paragraph("INSERT", table_cell_style), Paragraph("WITH CHECK: <code>(jefe_obra_id = auth.uid())</code>", table_cell_style)],
        [Paragraph("<code>avances</code>", table_cell_bold_style), Paragraph("authenticated lee sus avances", table_cell_style), Paragraph("SELECT", table_cell_style), Paragraph("USING: <code>(jefe_obra_id = auth.uid())</code>", table_cell_style)],
        [Paragraph("<code>avances</code>", table_cell_bold_style), Paragraph("admin_all_avances", table_cell_style), Paragraph("ALL", table_cell_style), Paragraph("USING/CHECK: <code>public.es_administrador()</code>", table_cell_style)],
        [Paragraph("<code>items_obra</code>", table_cell_bold_style), Paragraph("authenticated lee items de sus obras", table_cell_style), Paragraph("SELECT", table_cell_style), Paragraph("USING: <code>(obra_id IN (SELECT obra_id FROM obras_jefes_obra WHERE jefe_obra_id = auth.uid()))</code>", table_cell_style)],
        [Paragraph("<code>items_obra</code>", table_cell_bold_style), Paragraph("admin_all_items", table_cell_style), Paragraph("ALL", table_cell_style), Paragraph("USING/CHECK: <code>public.es_administrador()</code>", table_cell_style)],
        [Paragraph("<code>obras</code>", table_cell_bold_style), Paragraph("authenticated lee obras asignadas", table_cell_style), Paragraph("SELECT", table_cell_style), Paragraph("USING: <code>(id IN (SELECT obra_id FROM obras_jefes_obra WHERE jefe_obra_id = auth.uid()))</code>", table_cell_style)],
        [Paragraph("<code>obras</code>", table_cell_bold_style), Paragraph("admin_all_obras", table_cell_style), Paragraph("ALL", table_cell_style), Paragraph("USING/CHECK: <code>public.es_administrador()</code>", table_cell_style)],
        [Paragraph("<code>estados_pago</code>", table_cell_bold_style), Paragraph("edp_admin_all", table_cell_style), Paragraph("ALL", table_cell_style), Paragraph("USING/CHECK: <code>public.es_administrador()</code>", table_cell_style)],
        [Paragraph("<code>asistencia_diaria</code>", table_cell_bold_style), Paragraph("asistencia_diaria_admin_all", table_cell_style), Paragraph("ALL", table_cell_style), Paragraph("USING/CHECK: <code>public.es_administrador()</code>", table_cell_style)]
    ]
    t_rls = Table(rls_data, colWidths=[80, 140, 64, 220])
    t_rls.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_rls)
    
    story.append(Spacer(1, 10))
    story.append(Paragraph("Detalle de Comportamiento y Seguridad:", h2_style))
    story.append(Paragraph("• <b>Inserción Restringida a Terreno:</b> Los Jefes de Obra solo pueden registrar e inspeccionar datos si su ID coincide con <code>auth.uid()</code>.", bullet_style))
    story.append(Paragraph("• <b>Control Total para Administradores:</b> Los usuarios con rol 'administrador' tienen acceso ilimitado a todas las tablas mediante la función <code>public.es_administrador()</code> con <code>SECURITY DEFINER</code>, evitando la recursión infinita.", bullet_style))

    story.append(PageBreak())

    # ================= PAGE 9: SIMPLIFIED DATA FLOW DIAGRAM =================
    story.append(Paragraph("7. Diagrama de Flujo de Datos Simplificado", h1_style))
    story.append(Paragraph(
        "Esquema estructurado del flujo de información entre el terreno (App Móvil), la administración (App Escritorio) y el backend en la nube (Supabase):",
        body_style
    ))
    
    flow_diagram_data = [
        [Paragraph("<b>PASO / ROL</b>", table_header_style), Paragraph("<b>ORIGEN (FRONTEND)</b>", table_header_style), Paragraph("<b>ACCION / OPERACION</b>", table_header_style), Paragraph("<b>DESTINO (BACKEND CLOUD)</b>", table_header_style)],
        [
            Paragraph("<b>1. Carga Inicial</b><br/>(Administrador)", table_cell_bold_style),
            Paragraph("App PyQt6 Escritorio<br/>(<code>ingesta_view.py</code>)", table_cell_style),
            Paragraph("<b>a)</b> Parsea Excel (Cubicaciones)<br/><b>b)</b> Pide precios por material<br/><b>c)</b> Carga masiva de la obra e ítems.", table_cell_style),
            Paragraph("<b>Supabase DB & Storage</b><br/>Tablas <code>obras</code>, <code>items_obra</code> y respaldo Excel.", table_cell_style)
        ],
        [
            Paragraph("<b>2. Asignación</b><br/>(Administrador)", table_cell_bold_style),
            Paragraph("App PyQt6 Escritorio<br/>(<code>jefes_view.py</code> / <code>control_personal_view.py</code>)", table_cell_style),
            Paragraph("Vincula la obra a Jefes de Obra (`obras_jefes_obra`) y asigna personal (`obras_maestros`).", table_cell_style),
            Paragraph("<b>Supabase DB</b><br/>Tablas <code>obras_jefes_obra</code> y <code>obras_maestros</code>", table_cell_style)
        ],
        [
            Paragraph("<b>3. Descarga</b><br/>(Jefe de Obra)", table_cell_bold_style),
            Paragraph("App Expo Móvil<br/>(<code>syncCatalog()</code>)", table_cell_style),
            Paragraph("Descarga las obras, ítems, materiales y personal asignados por RLS localmente.", table_cell_style),
            Paragraph("<b>Caché SQLite</b><br/>Base de datos local <code>trackeo.db</code> en el smartphone.", table_cell_style)
        ],
        [
            Paragraph("<b>4. Registro</b><br/>(Jefe de Obra)", table_cell_bold_style),
            Paragraph("App Expo Móvil<br/>(Avances, Bitácora, Asistencia)", table_cell_style),
            Paragraph("<b>a)</b> Captura foto obligatoria<br/><b>b)</b> Ingresa m² ejecutados o asistencia<br/><b>c)</b> Registra offline (<code>synced = 0</code>)", table_cell_style),
            Paragraph("<b>Caché SQLite</b> y almacenamiento de fotos local.", table_cell_style)
        ],
        [
            Paragraph("<b>5. Sincronización</b><br/>(Automático)", table_cell_bold_style),
            Paragraph("App Expo Móvil<br/>(<code>sync.js</code>)", table_cell_style),
            Paragraph("Al detectar conexión (NetInfo):<br/><b>a)</b> Sube fotos a Storage.<br/><b>b)</b> Inserta registros en Supabase.<br/><b>c)</b> Marca <code>synced = 1</code>", table_cell_style),
            Paragraph("<b>Supabase Storage & DB</b><br/>Buckets de fotos y tablas <code>avances</code>, <code>reporte_obra</code>, <code>asistencia_diaria</code>.", table_cell_style)
        ],
        [
            Paragraph("<b>6. Auditoría y EDP</b><br/>(Administrador)", table_cell_bold_style),
            Paragraph("App PyQt6 Escritorio<br/>(<code>avances_window.py</code> / <code>edp_tab.py</code>)", table_cell_style),
            Paragraph("<b>a)</b> Descarga avances y los aprueba/rechaza.<br/><b>b)</b> Genera EDP, calcula retenciones, obtiene folio secuencial y compila PDF.", table_cell_style),
            Paragraph("<b>Supabase DB & Storage</b><br/>Actualiza <code>estado_revision</code>, genera <code>estados_pago</code> y sube PDF.", table_cell_style)
        ]
    ]
    
    t_flow = Table(flow_diagram_data, colWidths=[104, 130, 140, 130])
    t_flow.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_flow)
    
    story.append(Spacer(1, 15))
    story.append(Paragraph("Flujo de Consolidación de Datos (Mermaid Text):", h2_style))
    
    flow_text = """[Administrador: Excel / Maestros] --> (Supabase DB: obras, items_obra, maestros)
                                     |
                                     V
[Jefe Obra: Expo App] <-- [Descarga Catálogo y Personal Vía RLS]
      |
      +---> (Registra avance, bitácora y asistencia offline en SQLite)
      |
      +---> [Detecta Red Online / NetInfo]
                 |
                 V
            [Sube Fotos a Supabase Storage Buckets]
                 |
                 V
            [Inserta Filas en Tablas Supabase DB]
                 |
                 V
            [Actualiza SQLite local -> synced = 1]
                                     |
                                     V
[Administrador: PyQt6 Dashboard] <-- [Audita Avance, Asistencia y Emite EDP PDF]"""

    story.append(Table(
        [[Paragraph(flow_text.replace("\n", "<br/>").replace(" ", "&nbsp;"), code_style)]],
        colWidths=[504],
        style=[
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ('PADDING', (0,0), (-1,-1), 8),
        ]
    ))

    # Build document without Section 8
    doc.build(story, canvasmaker=NumberedCanvas)
    print("Report PDF generated successfully.")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "INFO PROYECTO")
    os.makedirs(output_dir, exist_ok=True)
    
    output_pdf = os.path.join(output_dir, "Resumen_Arquitectura_y_Estado_Actual.pdf")
    logo = os.path.join(output_dir, "LOGOS", "logo_gryphus_nombre_sf.png")
    if not os.path.exists(logo):
        logo = os.path.join(output_dir, "LOGOS", "logo_gryphus_circular_sf.png")
    if not os.path.exists(logo):
        logo = os.path.join(output_dir, "LOGOS", "LOGO_CON_LETRAS.png")
        
    try:
        create_report(output_pdf, logo)
    except PermissionError:
        output_pdf_alt = os.path.join(output_dir, "Resumen_Arquitectura_y_Estado_Actual_Actualizado.pdf")
        print(f"Advertencia: El archivo PDF original estaba bloqueado por el visor de PDF de Windows. Guardando en: {output_pdf_alt}")
        create_report(output_pdf_alt, logo)
