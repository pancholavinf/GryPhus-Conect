# Informe Maestro de Diseño UI/UX: Ecosistema GryPhus Conect (2026)
**Documento Técnico Oficial de Componentes, Vistas, Efectos Visuales y Elementos en Pantalla**  
*Plataforma Gryphus Systems • GryPhus Conect Gerencia (Escritorio PyQt6) & GryPhus Conect Terreno (Móvil React Native / Expo)*

---

## 1. Fundamentos del Sistema de Diseño (Design Tokens)

El ecosistema Trabs está construido bajo una identidad industrial moderna, combinando alta visibilidad operativa en terreno con legibilidad ejecutiva para escritorio.

### 1.1 Paleta Cromática Global (Tokens Hexadecimales)

| Token | Nombre Semántico | Hexadecimal | Aplicación Visual Primaria |
|---|---|---|---|
| `primary` / `cta` / `accent` | **Verde Musgo (Slate Forest)** | `#3D523C` | Acciones principales (CTA), badges destacados, focus de inputs, barras de carga activas |
| `secondary` / `darkSurface` | **Basalto Oscuro (Dark Basalt)** | `#262B29` | Sidebar de escritorio, cabeceras de tablas, títulos oscuros, tarjetas contrastadas |
| `surfaceDarkSecondary` | **Carbón Pizarra** | `#414445` | Separadores oscuros, hover activo de sidebar |
| `support` / `textLight` | **Piedra Media (Medium Slate)** | `#4A524E` | Subtítulos, bordes neutros, placeholders, estados desactivados |
| `borderLight` | **Gris Slate** | `#CBD5E1` / `#E2E8F0` | Líneas divisorias en tarjetas, bordes de inputs de formularios |
| `background` | **Tiza / Papel Kraft (Chalk White)** | `#F2EFE9` | Lienzo de fondo de ventanas y pantallas completas |
| `surface` | **Blanco Puro** | `#FFFFFF` | Contenedores modales, cards elevadas, celdas de datos |
| `text` | **Grafito Intenso** | `#1F2421` | Tipografía principal, títulos con alto ratio de contraste (>10:1) |
| `synced` / `approved` / `success` | **Verde Esmeralda** | `#10B981` | Estados sincronizados, avances aprobados, badges de éxito |
| `pending` / `warning` | **Ámbar Precaución** | `#F59E0B` / `#D97706` | Elementos pendientes de revisión, estados correctivos, botones de edición |
| `error` / `offline` / `danger` | **Rojo Alerta** | `#DC2626` / `#EF4444` | Borrado, desconexión, errores de validación, incidentes graves |
| `accentLight` | **Ámbar Suave** | `#FFF3D6` / `#FEF3C7` | Fondos de banners de aviso, selecciones de lote |

### 1.2 Sistema Tipográfico

- **Títulos y Encabezados Ejecutivos (`Heading`):** Familia tipográfica `Montserrat` (`Montserrat-Bold` 700/800, `Montserrat-SemiBold` 600).
- **Lectura, Tablas y Campos (`Body`):** Familia tipográfica `Inter` (`Inter-Regular` 400, `Inter-Medium` 500, `Inter-Bold` 700).

---

## 2. GryPhus Conect Gerencia — Aplicación de Escritorio (PyQt6)

La aplicación de escritorio cuenta con una arquitectura de ventana principal (`QMainWindow`, resolución base 1200×800 px) gestionada por un `QStackedWidget` central y un `QFrame#Sidebar` fijo de navegación lateral de 250 px de ancho.

```
MainAppWindow (1200x800)
├── [0] Splash Screen Inicial (Animación GIF + Línea Negra 3px)
├── [1] Data Pull Screen (Sincronización inicial post-auth)
├── [2] LoginScreen (Card centrada 400px con sombra)
└── [3] MainView (Layout Horizontal)
    ├── QFrame#Sidebar (250px fijo, Fondo #262B29)
    └── QStackedWidget (Área de Contenido)
        ├── [0] DashboardContent (Mis Obras + Asistencia Hoy)
        ├── [1] IngestaContent (Presupuestos Excel + Catálogos)
        ├── [2] ControlPersonalContent (Gestión Maestros y Supervisores)
        ├── [3] MaterialesContent (Fichas técnicas y rendimiento)
        ├── [4] ReportesAsistenciaContent (Auditoría de jornales y pagos)
        └── [*] AvancesContent (Detalle de Obra embebido: Gráficos, Ítems, Bitácora, EDP)
```

---

### 2.1 Pantallas de Inicio y Acceso

#### A. Splash Screen Inicial (`main.py`)
- **Propósito:** Presentación de marca durante el arranque del ejecutable y validación de sesión en segundo plano.
- **Fondo:** `#FFFFFF`.
- **Estructura y Spacing:** `QVBoxLayout` centrado, espaciado de 16 px.
- **Elementos Visuales:**
  - **Animación de Identidad:** `QLabel` que ejecuta un `QMovie` cargando `assets/animacion_gryphus.gif` a resolución escalada de 480×339 px.
  - **Línea de Progreso Sutil:** `QProgressBar` horizontal (ancho fijo 280 px, alto 3 px), sin texto visible (`textVisible=False`), fondo de pista `#E2E8F0`, barra activa (`chunk`) `#1A1D20` con radio de 1 px.
  - **Efecto de Transición:** Temporizador `QTimer` a 20 FPS (50 ms por ciclo) completando 5800 ms de animación suave antes de conmutar de vista.

#### B. Pantalla de Descarga Inicial de Datos (`main.py`)
- **Propósito:** Informar la hidratación de caché y catálogos Supabase tras validar credenciales.
- **Fondo:** `#FFFFFF`.
- **Elementos:**
  - **Logo Estático:** `QLabel` con `logo_gryphus_nombre_sf.png` escalado a 240 px con suavizado bicúbico (`SmoothTransformation`).
  - **Barra de Progreso:** Idéntica a la del Splash (280×3 px, `#1A1D20`).
  - **Etiqueta de Estado:** `QLabel` en `Inter`, 11 px, color `#4A524E` ("Iniciando sincronización...").

#### C. Pantalla de Login (`login_screen.py`)
- **Propósito:** Autenticación de administradores y directivos.
- **Fondo General:** `#F2EFE9` (definido por regla global de hoja de estilos QSS).
- **Contenedor Tarjeta (`LoginContainer`):**
  - **Dimensiones:** Ancho fijo 400 px, centrado vertical y horizontalmente.
  - **Fondo y Bordes:** Fondo `#FFFFFF`, borde 1 px sólido `#4A524E`, esquinas redondeadas radio 12 px.
  - **Márgenes Internos:** Margen horizontal 30 px, vertical 40 px, espaciado entre campos 20 px.
  - **Efecto Gráfico:** `QGraphicsDropShadowEffect`, radio de desenfoque (`blurRadius`) 25 px, color `rgba(0, 0, 0, 0.08)` (alpha 20/255), desplazamiento vertical `offset(0, 8)`.
- **Elementos Internos:**
  - **Cabecera de Marca:** Logo Trabs escalado a 250 px (`logo_gryphus_nombre_sf.png`), centrado.
  - **Subtítulo:** `QLabel`, 14 px, `Inter`, color `#1F2421`.
  - **Campos de Entrada (`email_input`, `password_input`):** `QLineEdit` con fondo `#FFFFFF`, borde 1 px `#4A524E`, radio 6 px, relleno 10 px vertical y 12 px horizontal, tipografía 14 px. Al obtener foco: borde destacado de 2 px `#3D523C`.
  - **Etiqueta de Error (`ErrorLabel`):** Oculta por defecto, tipografía 13 px, color `#EF4444`.
  - **Botón Primario (`PrimaryButton`):** "Iniciar Sesión".
    - *Estado Normal:* Fondo `#3D523C`, texto `#1F2421`, peso 700 (`Inter`), relleno 10×20 px, radio 6 px. Cursor de mano (`PointingHandCursor`).
    - *Estado Hover:* Fondo `#D99300`.
    - *Estado Presionado:* Fondo `#BF8100`.
    - *Estado Desactivado:* Fondo `#4A524E`, texto `#E2E8F0`.
  - **Pie de Versión:** `QLabel`, 11 px, color `#94A3B8`, padding superior 10 px.

---

### 2.2 Shell Principal y Navegación (`main_view.py`)

#### Barra Lateral de Control (`QFrame#Sidebar`)
- **Dimensiones:** Ancho fijo de 250 px, se extiende al 100% de la altura de la ventana.
- **Fondo:** `#262B29` (Basalto Oscuro (Dark Basalt)) con borde derecho de 1 px `#414445`.
- **Efecto de Profundidad:** `QGraphicsDropShadowEffect`, radio de blur 15 px, color `rgba(0, 0, 0, 0.15)` (alpha 40/255), desplazamiento lateral `offset(2, 0)`.
- **Márgenes:** Margen superior 30 px, inferior 20 px, laterales 10 px, espaciado vertical 10 px.
- **Logotipo Superior:** Escala 180 px ancho con separación inferior de 30 px.
- **Botones de Sección (`QPushButton.SidebarButton`):**
  - Opciones: *Dashboard*, *Ingesta de Obras*, *Control de Personal*, *Materiales*, *Asistencia*.
  - *Estado Normal:* Fondo transparente, texto `#EAECEE`, alineación izquierda, relleno 12 px vertical y 16 px horizontal, radio 0 px, borde izquierdo transparente de 4 px, fuente 14 px SemiBold (`Inter`).
  - *Estado Hover:* Fondo `rgba(255, 255, 255, 0.12)`, texto blanco `#FFFFFF`.
  - *Estado Seleccionado (`:checked`):* Fondo `#414445`, texto `#FFFFFF` (peso 700), borde lateral izquierdo de 4 px sólido `#3D523C`.
- **Botonera Operativa Inferior:**
  - **Botón Forzar Sincronización (`SidebarButtonSync`):** Borde 1 px `#3D523C`, texto `#3D523C`, radio 6 px, padding 10×16 px. Al hover: fondo `rgba(243, 165, 0, 0.15)` y texto blanco.
  - **Botón Buscar Actualizaciones (`SidebarButtonUpdate`):** Borde 1 px `#65A30D`, texto `#BEF264`, fondo `rgba(85, 107, 47, 0.25)`, radio 6 px, padding 10×16 px. Al hover: fondo `#556B2F`, borde `#84CC16`, texto `#FFFFFF`.
  - **Botón Cerrar Sesión (`SidebarButtonLogout`):** Borde 1 px `#EF4444`, texto `#FCA5A5`, radio 6 px, padding 10×16 px. Al hover: fondo `rgba(239, 68, 68, 0.20)`, texto `#FFFFFF`.
  - **Insignia de Versión:** `QLabel` centrado en 11 px, `#94A3B8`, "GryPhus Conect Gerencia vX.X.X 🟢 • Gryphus Systems".

---

### 2.3 Dashboard Principal (`dashboard_view.py`)

- **Estructura:** Disposición vertical con márgenes de 30 px en todos los bordes, espaciado superior de 20 px.
- **Encabezado:** `TitleLabel` en `Montserrat` 22 px, peso 800, color `#262B29`.

#### Sección Superior: Asistencia del Día (Tarjetas KPI)
- **Título de Sección:** `QLabel` 16 px negrita, color `#262B29`.
- **Tarjetas KPI (`_create_asistencia_card`):**
  - Ancho fijo de 240 px, fondo `#FFFFFF`, borde 1 px `#4A524E`, radio 10 px.
  - Sombra: Blur 12 px, offset (0, 3), color `rgba(69, 107, 109, 0.10)`.
  - Padding interno: 14 px horizontal, 12 px vertical, separación 6 px.
  - Nombre de obra en `Montserrat` 13 px negrita `#262B29`.
  - Resumen operativo: Presentes / Medios / Ausentes y % de asistencia en 12 px `#1F2421`.
  - Costo de jornada laboral: `QLabel` en 12 px negrita, color destacado `#3D523C`.

#### Sección Inferior: Grilla de Tarjetas de Obras (`ClickableObraCard`)
- **Organización:** `QGridLayout` de 3 columnas dinámicas con espaciado entre tarjetas de 20 px.
- **Anatomía de la Tarjeta:**
  - **Efecto Elevado:** Sombra con desenfoque de 18 px, offset (0, 4), color `rgba(69, 107, 109, 0.12)`.
  - **Contenedor Base:** Fondo `#FFFFFF`, borde 1 px `#4A524E`, radio 12 px.
  - **Efecto Hover Interactivo:** Borde cambia a 2 px sólido `#3D523C`, cursor de mano.
  - **Franja Superior de Acento:** `QFrame` de 8 px de altura fija con el color distintivo de la obra (por defecto `#3D523C`), radio superior redondeado a 11 px y base recta (0 px).
  - **Cuerpo Interno:** Padding 20 px lateral y 16 px vertical, separación 12 px.
  - **Fila Superior:** Título de la obra en `Montserrat` 16 px (peso 800) y Badge de estado (píldora con padding 4×10 px, radio 10 px; si es "Activa": fondo `#F2EFE9` y texto `#262B29`; si no: fondo `#FEE2E2` y texto `#DC2626`).
  - **Fila Supervisor:** Texto 12 px en `#262B29` (peso 600).
  - **Línea Separadora:** 1 px de altura, color `#F2EFE9`.
  - **Enlace de Acción:** "Ingresar a Detalle de Obra ->", tipografía 12 px peso 700 en color `#3D523C`.

---

### 2.4 Ingesta de Obras y Presupuestos (`ingesta_view.py`)

- **Estructura:** Formulario superior `QFormLayout` con vista previa de tabla masiva.
- **Formulario de Parámetros:**
  - Input nombre de obra (`QLineEdit`).
  - Selector de supervisor (`QComboBox`).
  - Selector de color de obra (`QComboBox`) con iconos de muestra generados por software (cuadrículas de 16×16 px rellenas de cada color: Azul Track `#3D523C`, Slate Oscuro `#262B29`, Rojo `#EF4444`, Verde `#10B981`, etc.).
- **Botonera:**
  - `SecondaryButton` ("Seleccionar Excel"): Fondo blanco, borde 1 px `#4A524E`, hover `#F2EFE9`.
  - `PrimaryButton` ("Procesar y Crear Obra"): Fondo `#3D523C`, texto `#1F2421` 700.
- **Tabla de Previsualización (`QTableWidget`):**
  - Cabecera Antracita `#262B29`, texto blanco mayúsculas 12 px negrita, línea inferior ámbar 2 px `#3D523C`.
  - Altura de filas fijada en 44 px, padding de celda 12×14 px, filas alternadas con fondo `#F8FAFC`.

#### Modales de Asistente de Ingesta:
1. **`CrearMaterialesNuevosDialog` (Ancho mínimo 650 px):**
   - Modal para homologar insumos no registrados.
   - Tabla con filas de 44 px con combos incrustados (`tinetas`, `sacos`, `un`, `kg`, `litros`), `QDoubleSpinBox` de rendimiento y `QLineEdit` para notas descriptivas.
2. **`PreciosMaterialesDialog`:**
   - Lista dinámica de inputs monetarios con prefijo `$ ` para asignar costos unitarios al presupuesto.

---

### 2.5 Detalle de Obra y Avances Físicos (`avances_window.py`)

Es la pantalla más compleja y extensa del sistema de gestión (1752 líneas de código), embebida directamente en el stack para una experiencia fluida.

- **Cabecera:** Botón de retorno "← Volver al Dashboard" (texto 13 px `#262B29`, hover `#3D523C`), título de obra en 22 px `#1F2421`, botón recargar datos y badge de estado con fondo translúcido (`#10B98115`) y borde verde.
- **Pestañas (`QTabWidget`):**
  - Pestañas inactivas: Fondo `#F2EFE9`, texto `#262B29`, borde `#E2E8F0`, radio superior 6 px, padding 10×20 px.
  - Pestaña activa: Fondo `#FFFFFF`, texto `#3D523C` negrita, borde inferior de 2 px blanco fundido con el panel.

#### Pestaña 1: Gráficos y Estadísticas Generales (`tab_stats`)
- **Integración Matplotlib (`MplCanvas`):** Fondo blanco `#FFFFFF`, renderizado nítido a 100 DPI.
- **Controles de Visualización:** Selectores agrupado vs apilado, filtros de agrupación temporal.
- **Indicadores Rápidos (KPIs):** Total presupuestado, total ejecutado, % de avance global con barras de progreso customizadas con chunk `#3D523C`.

#### Pestaña 2: Ítems de Obra (`tab_items`)
- **Estructura Splitter Horizontal:** Divisor central de 2 px `#E2E8F0`.
- **Panel Izquierdo:**
  - Barra de búsqueda de partidas (`QLineEdit` 30 px alto con icono de lupa).
  - Filtros en combo por ubicación, plano y estructura.
  - Tabla de cubicación con filas de 44 px y selección de fila completa.
- **Panel Derecho (Master-Detail):**
  - Tarjeta de detalle de partida seleccionada con desglose de dimensiones, largo de perfil (mm convertidos a metros), espesores y masividad.
  - Historial de capturas de terreno vinculadas exclusivamente a esa partida con miniaturas fotográficas y fechas de registro.

#### Pestaña 3: Detalle de Avances (`tab_table`)
- **Tabla Bitácora de Avances:**
  - Columnas: Fecha, Supervisor, Partida, Cantidad Registrada, Unidad, Evidencia, Estado, Acciones.
  - Badges de Estado: Aprobado (verde `#10B981`), Pendiente (ámbar `#3D523C`), Rechazado (rojo `#DC2626`).
  - Botones de Aprobación Inmediata: Botón verde `#10B981` ("Aprobar") y botón rojo `#EF4444` ("Rechazar") con hover diferenciado.
  - Galería Fotográfica: Vista previa de fotografía al seleccionar fila.

---

### 2.6 Control de Personal (`control_personal_view.py`) y Supervisores (`jefes_view.py`)

- **Estructura Master-Detail:** Splitter horizontal con panel izquierdo para la tabla y panel derecho para edición y ficha técnica.
- **Panel Izquierdo:** Tabla de personal con 6 columnas, búsqueda en tiempo real y selección sincronizada.
- **Panel Derecho (`QScrollArea` con fondo `#FFFFFF`):**
  - **Tarjeta de Perfil Superior (`#F8FAFC`):**
    - Contenedor con borde 1 px `#E2E8F0`, radio 8 px, padding 10×6 px.
    - **Foto de Perfil Circular (48×48 px):** `QLabel` con radio de borde de 24 px (`border-radius: 24px; border: 2px solid #CBD5E1;`). Si no hay foto, muestra iniciales en color `#64748B`.
    - Botones de acción rápida: `📷 Cambiar` (borde azul celeste `#BAE6FD`, texto `#0369A1`) y `✕ Quitar` (borde rosado `#FECACA`, texto `#DC2626`).
    - Botón de edición: `✏️ Editar` con fondo ámbar oscuro `#D97706`, texto blanco y radio de 5 px.
  - **Formularios de Datos Agrupados (`QGroupBox`):**
    - Fondo blanco, borde 1 px `#E2E8F0`, radio 8 px, título con padding lateral de 6 px.
    - Inputs con validadores numéricos y de RUT.

---

### 2.7 Materiales y Análisis de Desviaciones (`materiales_view.py` y `reportes_view.py`)

- **Gestión de Fichas Técnicas:**
  - Carga y previsualización de fotografías de materiales (130×110 px centradas).
  - Enlaces a Fichas de Seguridad (HDS) y Ensayos de Laboratorio con botones de acción.
- **Gráficos de Rendimiento Real (`GraficosRendimientoDialog`):**
  - Diálogo modal de 850×700 px con lienzo de gráficos Matplotlib (`FigureCanvasQTAgg`).
  - **Gráfico Superior (Doble Eje Y):**
    - Barras de Consumo Real en azul `#3B82F6` (eje izquierdo).
    - Curva de Avance Físico ejecutado en verde `#10B981` con marcadores circulares y línea de 2.5 px (eje derecho).
  - **Gráfico Inferior:**
    - Rendimiento Real Calculado en morado `#8B5CF6` comparado contra la línea punteada de promedio general en rojo `#EF4444`.

---

### 2.8 Estados de Pago EDP (`edp_tab.py` y `pdf_edp_generator.py`)

- **Resumen Financiero:** Cálculo en vivo de retenciones de contrato (por defecto 5.00% con `QDoubleSpinBox`) y descuentos por anticipos con formateo monetario en pesos chilenos (`$X.XXX.XXX`).
- **Caja de Totales Resaltada:** Fondo azul claro `#EFF6FF`, borde 1 px `#93C5FD`, radio 6 px, padding 10 px con monto total en tipografía destacada `#3D523C`.
- **Botón de Emisión Oficial:** "Confirmar, Congelar y Emitir EDP" con fondo `#3D523C`, texto blanco negrita. Durante el proceso, se despliega una barra de progreso indeterminada de 8 px (`#3D523C`).
- **Documento PDF Generado:** Generación vectorizada con cabecera corporativa Trabs, franjas alternadas gris claro y firma digital de aprobación.

---

### 2.9 Visor de Documentos Integrado (`document_viewer.py`)

- **Tema de la Ventana:** Modo oscuro técnico (`QDialog` con fondo `#1F2421`, textos en `#F8FAFC`).
- **Barra de Herramientas:** Fondo `#262B29`, radio 8 px.
  - Botón "Descargar Copia": Azul `#2563EB` con hover `#1D4ED8`.
  - Botón "Abrir en Sistema": Verde `#059669` con hover `#047857`.
  - Botón "Cerrar": Carbón `#262B29`.
- **Renderizado PyMuPDF (140 DPI):** Cada página del PDF se convierte en imagen de alta definición montada en un `QLabel` con borde `#334155` y fondo blanco `#FFFFFF`, centrada en un área con scroll continuo.

---

### 2.10 Diálogo de Actualización de Software (`update_dialog.py`)

- **Modal:** Dimensiones fijas de 540×520 px, esquinas redondeadas de 12 px, fondo blanco.
- **Cabecera:** Logo Trabs circular de 56×56 px, título en `Montserrat` 17 px (peso 800) y comparativa de versiones: actual en gris oscuro y nueva en ámbar negrita `#3D523C`.
- **Visor de Notas de Versión (`QTextBrowser`):** Alto fijo de 150 px, fondo gris claro `#F8FAFC`, borde `#E2E8F0`, radio 8 px.
- **Barra de Progreso de Descarga:** Alto 8 px, fondo `#E2E8F0`, barra activa `#3D523C`, radio 4 px.
- **Botonera:** "Recordar más tarde" (borde `#CBD5E1`, texto `#475569`) y "🚀 Actualizar Ahora" (fondo `#3D523C`, texto blanco, hover `#D98E00`).

---

## 3. GryPhus Conect Terreno — Aplicación Móvil (React Native / Expo)

Diseñada para uso rudo en obra: componentes táctiles con área de contacto amplia (mínimo 48 px), alto contraste y soporte offline completo.

```
App Root (NavigationContainer)
├── LoginScreen (Acceso con validación y logo centrado)
├── HomeScreen (Selector de Obra, Avatar con cámara, Estado de Sincronización)
├── ObraMenuScreen (Menú de 4 operaciones de faena)
├── SelectionFlowScreen (Wizard de 8 pasos para captura de avance físico)
├── AsistenciaScreen (Pase de lista diario, foto obligatoria y modo correctivo)
├── ReporteDiarioScreen (Bitácora, fotos y contadores de materiales)
├── ControlObraScreen (Nómina de trabajadores asignados)
└── MandatoryUpdateModal (Modal bloqueante de Google Play Store)
```

---

### 3.1 Acceso y Autenticación Móvil (`LoginScreen.js`)

- **Contenedor Principal:** `KeyboardAvoidingView` con ajuste dinámico de teclado (`padding` en iOS, `height` en Android), fondo `#F2EFE9`.
- **Área de Marca:**
  - Imagen `logo_gryphus_nombre_sf.png` con tamaño 200×120 px, modo `contain`.
  - Subtítulo: "Control de obras en faena" en `Inter` 13 px, color `#4A524E`.
- **Tarjeta de Formulario (`formCard`):**
  - Fondo `#FFFFFF`, radio de curvatura de 16 px, padding de 24 px.
  - Sombra iOS: Color `#000`, offset `{width: 0, height: 4}`, opacidad `0.06`, radio `12`.
  - Sombra Android: Elevación de `3`.
- **Campos de Texto:**
  - Alto 48 px, borde 1 px `#CBD5E1`, radio 10 px, fondo `#FAFAFA`, padding horizontal 14 px.
  - Tipografía `Inter` 15 px, color `#1F2421`.
- **Botón de Ingreso (`button`):**
  - Alto 50 px, fondo `#3D523C`, radio 12 px, centrado vertical y horizontal.
  - Sombra ámbar: Color `#3D523C`, offset `{width: 0, height: 3}`, opacidad `0.25`, radio `6`, elevación `4`.
  - Texto: `Montserrat-Bold` 16 px, color `#FFFFFF`, espaciado entre letras `0.3 px`.
  - Estado cargando: Desactiva el botón (`opacity: 0.7`) y muestra `ActivityIndicator` blanco.

---

### 3.2 Menú Principal de Obras (`HomeScreen.js`)

- **Barra Superior / Header:**
  - Fondo `#262B29` (Basalto Oscuro (Dark Basalt)), padding vertical adaptativo.
  - **Fila de Perfil y Sincronización:**
    - Avatar circular de 44×44 px (radio 22 px) con foto del supervisor o iniciales en blanco sobre fondo `#3D523C`. Badge de cámara superpuesto en la esquina inferior derecha.
    - Nombre del supervisor en `Montserrat-Bold` 16 px blanco y rol formateado en 12 px `#4A524E`.
    - **Botón de Sincronización Manual:** Icono circular con contador flotante de registros pendientes offline (badge rojo `#DC2626` si hay datos por sincronizar, o verde `#10B981` si está al día).
- **Lista de Obras (`FlatList` con soporte `RefreshControl`):**
  - **Tarjeta de Obra:**
    - Fondo `#FFFFFF`, borde 1 px `#CBD5E1`, radio 14 px, padding 16 px, margen inferior 12 px.
    - Elevación Android 2, sombra iOS sutil (opacidad `0.04`).
    - Borde o barra lateral izquierda con el color propio de la obra.
    - Nombre de obra en `Montserrat-Bold` 16 px `#1F2421`.
    - Badge de estado: Píldora verde suave (`#D1FAE5`, texto `#065F46` en `Montserrat-SemiBold` 10 px).
    - Flecha indicadora de navegación: `›` en 22 px color `#4A524E`.
- **Modal de Perfil de Usuario (`modalCard`):**
  - Hoja emergente inferior (*Bottom Sheet*), fondo blanco, esquinas superiores redondeadas de 24 px, padding de 24 px, sobreimpreso en overlay `rgba(0, 0, 0, 0.50)`.
  - Avatar ampliado de 72×72 px con selector de cámara en vivo o galería de fotos.
  - Filas de información con fondo `#F2EFE9` (Correo, Rol, Teléfono).

---

### 3.3 Menú de Operaciones de Faena (`ObraMenuScreen.js`)

- **Cabecera:** Fondo `#3D523C`, padding superior de 50 px, padding inferior de 16 px.
  - Botón Volver: Cápsula translúcida `rgba(255, 255, 255, 0.15)` con radio 20 px, flecha `‹` y etiqueta "Menú Principal".
  - Título de la obra activa en `Montserrat-Bold` 17 px blanco.
- **Cuadrícula de Operaciones (Tarjetas de Módulos):**
  - Cada módulo es una tarjeta blanca `#FFFFFF`, radio 14 px, borde 1 px `#CBD5E1`, padding 18 px, sombra elevación 2.
  - Título en `Montserrat-Bold` 18 px `#3D523C`, descripción funcional en 13 px `#4A524E`.
  - Botón de acción (alto 50 px, radio 12 px, elevación 3):
    1. **Reporte de Avance:** Fondo dinámico según color de la obra (por defecto `#3D523C`).
    2. **Pasar Asistencia:** Fondo `#262B29` (Basalto Oscuro (Dark Basalt)).
    3. **Reporte Diario:** Fondo `#3D523C`.
    4. **Control de Obra:** Fondo `#262B29`.

---

### 3.4 Wizard de Captura de Avances (`SelectionFlowScreen.js`)

Flujo secuencial de 8 etapas diseñado para evitar errores de selección en terreno:

```
[1. Estructura] ➔ [2. Dimensión] ➔ [3. Ubicación] ➔ [4. Largo Perfil]
      ➔ [5. Cantidad] ➔ [6. Fotografía] ➔ [7. Comentario] ➔ [8. Confirmar]
```

- **Barra de Progreso Segmentada:** Altura de 4 px ubicada inmediatamente bajo el header; se compone de segmentos individuales por cada paso visto. Segmento inactivo en fondo `#CBD5E1`, segmento activo en `#3D523C`.
- **Banner de Lote Activo (Persistente si hay ítems acumulados):**
  - Fondo ámbar suave `#FEF3C7`, borde 1 px `#F59E0B`, radio 12 px, padding 10×14 px, elevación 2.
  - Icono `📦`, contador de ítems acumulados y botón directo "Ir a Foto ➔" (cápsula radio 20 px `#3D523C`).
- **Cards Selectoras de Partida (Pasos 1 al 4):**
  - Fondo `#FFFFFF`, radio 12 px, borde 1 px `#CBD5E1`, padding 16 px, margen inferior 10 px.
  - Iconos contextuales: `🏗️` (Estructura), `📐` (Dimensión), `📍` (Ubicación), `📏` (Largo).
  - Texto de partida en `Montserrat-SemiBold` 15 px `#1F2421`, flecha lateral `›`.
  - Migas de pan (*Breadcrumbs*): Enlace superior `‹ Volver a...` en 13 px `#3D523C` para retroceder en la jerarquía.
- **Paso 5: Ingreso de Cantidad Ejecutada:**
  - **Tarjeta Resumen de Ítem:** Fondo azul suave `#EFF6FF`, borde izquierdo destacado de 4 px `#3D523C`, radio 12 px, padding 14 px. Muestra badge de ID de partida y total presupuestado.
  - **Input Gigante de Unidades:** Altura fija de 72 px, borde 2 px `#3D523C`, radio 14 px, texto centrado a tamaño 36 px negrita en color `#3D523C` sobre fondo blanco.
  - **Botonera Doble:**
    - Botón Principal (Píldora radio 26 px, alto 52 px, `#3D523C`, sombra elevación 6): "Continuar → Foto".
    - Botón Secundario (Borde 2 px `#3D523C`, fondo blanco, texto ámbar, alto 50 px): "+ Agregar otro ítem al lote".
- **Paso 6: Evidencia Fotográfica:**
  - Tag obligatorio: Fondo rojo tenue `rgba(220, 38, 38, 0.09)`, texto `★ OBLIGATORIO PARA EL LOTE` en `Montserrat-Bold` 11 px `#DC2626`.
  - Botones de captura divididos: "Galería" y "Cámara" (tarjetas blancas de 14 px de radio, borde 2 px `#3D523C`, padding vertical 28 px con iconos de 36 px).
  - Previsualización de imagen: Ancho 100%, altura 220 px, esquinas redondeadas de 14 px con botón "↺ Cambiar foto".
- **Paso 7: Comentarios:**
  - Tag opcional grisáceo `rgba(128, 138, 146, 0.09)`.
  - Input multilínea: Altura mínima 110 px, borde 1.5 px `#CBD5E1`, radio 12 px, relleno 14 px.
- **Paso 8: Confirmación y Envío:**
  - Lista de ítems del lote con badges numerados circulares (24×24 px), desglose de medidas y botón de eliminación individual (`✕` en círculo rojo `#FEE2E2`).
  - Miniatura de la evidencia fotográfica (alto 160 px, radio 12 px).
  - Botón de envío final: "✓ Enviar Avance" con indicador de carga durante la sincronización.

---

### 3.5 Asistencia Diaria en Faena (`AsistenciaScreen.js`)

- **Cabecera:** Color de fondo adaptable a la obra activa o `#3D523C`, título "📋 Asistencia Diaria" o "📋 Reporte Correctivo".
- **Modo Reporte Correctivo (Si ya se registró la jornada):**
  - Banner de advertencia: Fondo amarillo `#FEF3C7`, borde 1 px `#F59E0B`, radio 10 px, texto `#92400E` ("⚠️ Ya se registró asistencia hoy. Este envío se procesará como Reporte Correctivo.").
  - Campo obligatorio de justificación con altura mínima de 80 px.
- **Badges de Resumen de Dotación:**
  - Presentes: Fondo `#D1FAE5`, texto `#065F46` ("✓ X").
  - Medios Días: Fondo `#FEF3C7`, texto `#92400E` ("½ X").
  - Ausentes: Fondo `#FEE2E2`, texto `#991B1B` ("✗ X").
- **Tarjeta de Trabajador (`maestroCard`):**
  - Fondo `#FAFAFA`, borde 1 px `#CBD5E1`, radio 10 px, padding 12 px.
  - Nombre en `Inter-Bold` 14 px, cargo en `Inter` 12 px `#4A524E`.
  - **Selector Segmentado de 3 Estados (Chips):**
    - *Inactivo:* Fondo blanco, borde 1.5 px `#CBD5E1`, texto `#1F2421`.
    - *Día Completo (Activo):* Fondo `#10B981`, borde `#10B981`, texto blanco.
    - *Medio Día (Activo):* Fondo `#F59E0B`, borde `#F59E0B`, texto blanco.
    - *Ausente (Activo):* Fondo `#EF4444`, borde `#EF4444`, texto blanco.
- **Evidencia Obligatoria de Asistencia:**
  - Botones de captura rápida (Cámara `#3D523C`, Galería `#475569`).
  - Preview de foto fija de 200×140 px con botón flotante superior de supresión `✕` (círculo 28×28 px en rojo `#EF4444`).
  - Placeholder con borde discontinuo (*dashed*) de 2 px `#CBD5E1` cuando no hay imagen cargada.

---

### 3.6 Reporte Diario y Consumo de Materiales (`ReporteDiarioScreen.js`)

- **1. Selector de Tipo de Novedad:**
  - Grilla de 2 columnas con tarjetas de radio 10 px.
  - Opciones: `📝 Diario` (actualización regular), `⚠️ Incidente` (retrasos), `🚨 Accidente` (seguridad), `⚙️ Otro`.
  - Estado inactivo: Fondo blanco, borde 1 px `#CBD5E1`.
  - Estado seleccionado: Borde 2 px `#3D523C`, fondo azul suave `#EFF6FF`.
- **2. Campo de Bitácora:** Input multilínea de 120 px de altura mínima.
- **3. Galería de Múltiples Fotos:** Carrusel horizontal de miniaturas (80×80 px, radio 8 px) con botón de borrado individual `✕` en rojo `#DC2626`.
- **4. Contadores de Consumo de Materiales (Steppers):**
  - Fila por material con nombre y unidad de medida.
  - **Control Stepper:** Contenedor con borde 1 px `#CBD5E1`, radio 8 px.
    - Botones táctiles `-` y `+`: 34×34 px, fondo blanco, texto en `Montserrat-Bold` 16 px `#3D523C`.
    - Input de cantidad: 50×34 px, texto centrado en `Inter-Medium` 13 px.
- **Materiales Adicionales No Listados:**
  - Formulario desplegable para registrar insumos extra con campos para nombre, cantidad y unidad.

---

### 3.7 Control y Nómina de Obra (`ControlObraScreen.js`)

- **Propósito:** Consulta rápida de la dotación autorizada en la faena.
- **Tarjetas de Trabajadores (`workerCard`):**
  - Fondo blanco `#FFFFFF`, radio 12 px, borde 1 px `#CBD5E1`, padding 16 px, elevación 2.
  - Nombre en `Montserrat-Bold` 16 px `#1F2421`.
  - Badge de cargo: Cápsula con fondo `#EFF6FF`, borde 1 px `#3D523C`, texto en `Montserrat-SemiBold` 11 px `#3D523C`.
  - Separador horizontal de 1 px `#CBD5E1`.
  - Cuadrícula de contacto: RUT/DNI y Teléfono con etiqueta en gris y valor en `Inter-Medium` 13 px.

---

### 3.8 Modal de Actualización Obligatoria (`MandatoryUpdateModal.js`)

- **Comportamiento:** Modal pantalla completa bloqueante (`transparent={false}`, `onRequestClose` anulado para impedir salida no autorizada).
- **Fondo:** Modo oscuro industrial `#1E2124`.
- **Identidad:** Logo circular Trabs de 80×80 px, título en `Montserrat-Bold` 22 px blanco y badge de versión remota en `#3D523C`.
- **Tarjeta de Novedades:** Fondo `#2B2F33`, borde 1 px `#3D4247`, radio 14 px con scroll interno de notas de versión.
- **Insignia Oficial:** Píldora verde translúcida `rgba(16, 185, 129, 0.15)` con borde `#10B981` y texto "DISPONIBLE EN GOOGLE PLAY".
- **Botón Primario:** "Actualizar en Google Play ➔" con fondo `#3D523C`, radio 12 px, relleno vertical 15 px, elevación 4.
- **Enlace de Contingencia:** "Abrir enlace en el navegador web" subrayado en gris claro `#718096`.
- **Pie de Seguridad:** Texto informativo con icono de candado garantizando la persistencia de datos locales durante la actualización.

---

## 4. Matriz Comparativa de Efectos Gráficos y Renderizado

| Tipo de Efecto | GryPhus Conect Gerencia (Escritorio PyQt6) | GryPhus Conect Terreno (Móvil React Native) |
|---|---|---|
| **Sombras en Tarjetas** | `QGraphicsDropShadowEffect`<br>• Blur: 12 px a 25 px<br>• Alpha: 0.08 a 0.15<br>• Offset: (0, 3) a (0, 8) | `StyleSheet` Shadow & Elevation<br>• iOS: shadowOpacity 0.04 - 0.30, radius 4 - 12<br>• Android: elevation 2 a 6 |
| **Bordes Redondeados** | • Botones / Inputs: 6 px a 8 px<br>• Tarjetas / Cards: 10 px a 12 px<br>• Avatares circulares: 24 px | • Botones / Inputs: 10 px a 14 px<br>• Tarjetas / Cards: 12 px a 16 px<br>• Botones píldora (CTA): 25 px a 26 px<br>• Modales Bottom Sheet: 24 px |
| **Animaciones & Transiciones** | • `QMovie` a 20 FPS para el Splash (GIF)<br>• `QTimer` para progreso continuo (5800 ms)<br>• Hover nativo de estilos Qt (QSS) | • `ActivityIndicator` nativo en CTA<br>• `activeOpacity` (0.7 a 0.85) en eventos de toque<br>• Modal fade & slide en pantallas emergentes |
| **Iconografía** | • Gráficos SVG y PNG (`assets/`)<br>• Muestras de color generadas por `QPixmap` en runtime | • Emojis Unicode estándar (`🏗️`, `📐`, `📍`, `📷`, `📋`)<br>• Sprites PNG dedicados (`carpeta_logo`, `camara_logo`) |
| **Gráficos Estadísticos** | `Matplotlib` embebido vía `FigureCanvasQTAgg`<br>• Barras dobles, curvas con marcadores, líneas de promedio | Indicadores de progreso segmentados en barra nativa de 4 px |

---

## 5. Recomendaciones de Consistencia Visual y Mejora Continua

1. **Unificación de Librería de Iconos Móvil:**  
   Actualmente, la app de terreno combina emojis de texto (`📷`, `✕`, `‹`, `➔`) con imágenes PNG estáticas. Se recomienda adoptar `@expo/vector-icons` (Ionicons / MaterialCommunityIcons) para asegurar un trazo idéntico en todos los fabricantes de Android e iOS.
2. **Homologación de Fondos Seleccionados:**  
   En `ReporteDiarioScreen.js` y `SelectionFlowScreen.js`, algunas tarjetas activas utilizan azul `#EFF6FF` heredado de librerías base. Es recomendable migrar estos estados a la paleta oficial ámbar suave (`#FFF3D6` / `COLORS.accentLight`) para respetar al 100% el Design System Trabs 2026.
3. **Contraste Tipográfico en Botones CTA:**  
   En la app de escritorio, los botones `#PrimaryButton` en fondo `#3D523C` llevan texto oscuro `#1F2421` (cumpliendo ratio de contraste WCAG AA > 7:1). En la app móvil, algunos botones ámbar utilizan texto blanco `#FFFFFF` (ratio ~2.2:1). Se sugiere unificar el color de texto en botones primarios a `#1F2421` para máxima visibilidad bajo la luz solar directa en obra.
