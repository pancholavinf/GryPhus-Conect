# 🎨 Guía de Diseño UI/UX y Sistema de Interfaz: Ecosistema Trabs

**Organización**: Accuratek  
**Fecha de Actualización**: Agosto 2026  
**Ecosistema**: Trabs (Trabs Gerencia + Trabs Terreno)  
**Versión de Producción**: 1.0.5  
**Documento**: Design System Oficial Trabs 2026, Tokens de Diseño, Tipografía, Especificación de Componentes y Principios UX

---

## 🏛️ 1. Filosofía de Diseño y Principios UX

El ecosistema **Trabs** está diseñado para resolver la brecha entre el trabajo rudo e intensivo en el frente de faena y la toma de decisiones ejecutivas en la administración central. Se rige por 4 pilares esenciales:

1. **Estética Executive & Industrial Robust**: Combinación de alto contraste entre superficies oscuras en *Antracita Oscuro* (`#2D3033`), acentos dinámicos en *Ámbar Solar* (`#F3A500`), notas funcionales en *Verde Oliva Moderno* (`#65A30D` / `#BEF264`) y áreas de trabajo en *Gris Hielo Clean* (`#F4F6F8`), garantizando claridad bajo luz solar directa en terreno o pantallas de oficina.
2. **Zero-Freeze UX (Rendimiento Asíncrono Nativo)**: Ninguna llamada a Supabase PostgreSQL, subida de fotografías a Storage, consulta a GitHub Releases o renderizado de PDFs bloquea la interfaz de usuario. Todo proceso de entrada/salida corre en subprocesos `QThread` (escritorio) o tareas asíncronas optimizadas con ArrayBuffer (móvil).
3. **Diseño Offline-First Transparente**: La interfaz móvil responde de manera instantánea y optimista, almacenando los datos en SQLite local (`accuraop.db`) y mostrando indicadores visuales claros sobre el estado de sincronización.
4. **Prevención Activa de Errores Humanos**: Uso de asistentes guiados paso a paso (*wizards*) para la ingesta de presupuestos, toma de asistencia y emisión inmutable de Estados de Pago (EDP), requiriendo confirmaciones explícitas antes de acciones irreversibles.

---

## 🎨 2. Design Tokens y Paleta de Colores Curada (Trabs 2026)

La paleta cromática está unificada en la hoja de estilos Qt [`accuraop_gerencia/src/ui/style.qss`](file:///C:/Users/fcola/Desktop/APPACCURATEK/accuraop_gerencia/src/ui/style.qss) y en las constantes móviles [`accuraop_terreno/src/constants/theme.js`](file:///C:/Users/fcola/Desktop/APPACCURATEK/accuraop_terreno/src/constants/theme.js).

| Rol en el Sistema | Nombre del Token | Código HEX | Uso en Escritorio (`PyQt6`) | Uso en Móvil (`React Native`) |
| :--- | :--- | :--- | :--- | :--- |
| **Primario / CTA / Acento** | Ámbar Solar | `#F3A500` | Botones de acción principales, bordes de foco, acento en pestañas activas y barra inferior de encabezados de tabla. | Botones de confirmación, selector de pasos activos y acentos de marca. |
| **Superficie Oscura / Header** | Antracita Oscuro | `#2D3033` | Fondo de la Barra Lateral fija (`#Sidebar`), encabezados de tablas (`QHeaderView`) y títulos destacados. | Encabezado superior (*Header*), barra de estado y tarjetas dark. |
| **Gris Neutro / Bordes** | Gris Acero | `#808A92` | Bordes de inputs, líneas de división de tablas, etiquetas de subtítulo y botones deshabilitados. | Bordes de contenedores, divisores y textos secundarios. |
| **Superficie Secundaria** | Carbón Pizarra | `#414445` | Separadores oscuros y botones activos del sidebar (`:checked`). | Fondos secundarios y divisores dark. |
| **Acento Neutro** | Pizarra Medio | `#4A5156` | Pestañas inactivas, iconografía de apoyo y textos complementarios. | Iconos secundarios y etiquetas descriptivas. |
| **Fondo Principal de Trabajo** | Gris Hielo Clean | `#F4F6F8` | Fondo de la ventana principal (`QMainWindow`), stack de vistas y áreas con scroll. | Fondo principal de todas las pantallas (`COLORS.background`). |
| **Superficie de Tarjetas** | Blanco Puro | `#FFFFFF` | Fondo de tarjetas KPI, diálogos modales (`QDialog`), filas de tabla e inputs. | Tarjetas de obra, modales y formularios. |
| **Texto Principal** | Oscuro Elegante | `#1F2115` | Títulos principales, cuerpo de tablas e inputs para máxima legibilidad. | Títulos de sección, nombres de faena y textos clave. |
| **Actualizaciones / Novedades** | Verde Oliva Tech | `#BEF264` (texto) / `#65A30D` (borde) / `#556B2F` (hover) | Botón de búsqueda de actualizaciones en el sidebar (`.SidebarButtonUpdate`). | N/A |
| **Estado Éxito / Sincronizado** | Verde Esmeralda | `#10B981` | Insignias de obras activas, avances aprobados, badges de estado `🟢 En línea` y KPIs. | Indicador de sincronización completada y presentismo (1.0). |
| **Estado Alerta / Peligro** | Rojo Alerta | `#EF4444` / `#DC2626` | Obras pausadas, avances rechazados, botón de cerrar sesión y errores de red. | Indicador sin conexión (*offline*), ausencias (0.0) y alertas. |
| **Estado Pendiente / Revisión**| Ámbar Solar | `#F3A500` | Avances en revisión, montos pendientes de cobro y registros por facturar. | Registros pendientes de sincronización y medio día (0.5). |

---

## 🔤 3. Tipografía y Jerarquía Visual

El sistema utiliza dos familias tipográficas de Google Fonts:

1. **Montserrat (Títulos, Headings y Valores KPI)**:
   * `Montserrat-Bold` (700/800) y `Montserrat-SemiBold` (600).
   * Utilizada en títulos principales (`#TitleLabel`, 22px-24px), encabezados modales y los valores numéricos destacados de las tarjetas KPI (26px-28px).
   * Otorga una presencia corporativa, ejecutiva y estructurada.
2. **Inter (Cuerpo de Texto, Tablas, Inputs, Tooltips y Metadatos)**:
   * `Inter-Regular` (400), `Inter-Medium` (500) e `Inter-Bold` (700).
   * Utilizada en formularios, celdas de tablas (13px-14px), subtítulos, tooltips flotantes (`QToolTip`), badges y descripciones técnicas.
   * Diseñada para legibilidad óptima en interfaces de alta densidad de datos.

---

## 🖥️ 4. Especificación de Componentes UI: Aplicación de Escritorio (`accuraop_gerencia`)

### 4.1 Barra Lateral de Navegación (`#Sidebar`)
* **Dimensiones y Elevación**: Ancho fijo de 250px con `QGraphicsDropShadowEffect` (blur: 15px, offset X: 2px, color: `rgba(0,0,0,40)`).
* **Identidad de Marca**: Logotipo oficial Trabs (`logo_trabs_nombre_sf.png`) centrado y escalado a 180px de ancho.
* **Tooltips en Botones**: Cada botón cuenta con un `setToolTip()` informativo que despliega un cuadro oscuro flotante (`QToolTip`) describiendo su funcionalidad:
  * *"Panel principal de control y avance de obras"*
  * *"Ingesta y procesamiento de reportes diarios de terreno"*
  * *"Control de personal, dotación y subcontratistas"*
  * *"Gestión de stock, inventario y solicitudes de materiales"*
  * *"Auditoría y reportes detallados de asistencia"*
  * *"Forzar actualización de todos los datos desde Supabase"*
  * *"Comprobar si existe una nueva versión disponible en GitHub"*
* **Botones Especiales**:
  * Botón `"⚡ Resincronizar Datos"` (`SidebarButtonSync`): Borde y texto en Ámbar Solar `#F3A500`.
  * Botón `"🔄 Buscar Actualizaciones"` (`SidebarButtonUpdate`): Borde y texto en Verde Oliva `#BEF264` / `#65A30D`.
  * Botón `"Cerrar Sesión"` (`SidebarButtonLogout`): Borde y texto en Rojo `#EF4444`.
* **Badge Institucional**: Pie inferior centrado: `Trabs Gerencia v1.0.5 🟢 • Accuratek` en color `#94A3B8` y peso 600.

### 4.2 Tarjetas de Perfil Ultra Compactas (`ProfileHeaderCard` / `MaestroHeaderCard`)
* **Dimensiones**: Altura visual contenida (~58-62 px), bordes redondeados `border-radius: 8px`, fondo `#F8FAFC` y borde `#E2E8F0`.
* **Avatar Circular**: 48×48 px con `QPainterPath` y `QPainter.RenderHint.Antialiasing`.
* **Políticas de Layout**: `QSizePolicy(Expanding, Fixed)` y espaciador `addStretch()` en el contenedor padre que impiden la expansión vertical indeseada.
* **Acciones Contextuales**: Botones micro `"📷 Cambiar"` y `"✕ Quitar"` para gestión directa con el bucket de Storage.

### 4.3 Diálogo de Actualizaciones (`UpdateDialog`)
* **Modal Flotante de 540x460px**: Fondo Blanco Puro con cabecera en Antracita Oscuro `#2D3033`.
* **Insignia de Versión**: Destaca la versión instalada vs. la versión nueva (`v1.0.4` ➔ `v1.0.5`).
* **Área de Notas de Lanzamiento**: Caja con scroll que renderiza en HTML enriquecido las novedades, correcciones y notas técnicas del Release en GitHub.
* **Barra de Progreso y Métricas de Descarga**: Barra de progreso animada en Verde Esmeralda `#10B981` con indicación en tiempo real de:
  * Porcentaje completado (`45%`).
  * Megabytes transferidos vs. total (`25.4 MB / 56.5 MB`).
  * Velocidad de descarga (`4.2 MB/s`).
* **Botones de Acción**:
  * `"🚀 Actualizar Ahora"` (Botón Primario `#F3A500`).
  * `"Recordármelo más tarde"` (Botón Secundario `#808A92`).

### 4.4 Pantalla de Login y Splash Screen
* **Splash Screen Animado**: Reproduce la animación institucional `animacion_trabs.gif` con temporizador de ~5.8s mientras comprueba en segundo plano el token de sesión (`SessionCheckWorker`).
* **Auto-Login Transparente**: Si la sesión es válida, salta la pantalla de login directamente al Dashboard.
* **Pantalla de Autenticación**:
  * Tarjeta centralizada con sombra suave.
  * Logotipo circular oficial con fondo blanco.
  * Precarga automática del último correo recordado.
  * Pie institucional: `Trabs Gerencia v1.0.5 • Accuratek`.

### 4.5 Tablas de Datos (`QTableWidget`)
* **Encabezados**: Fondo `#2D3033`, texto en `#FFFFFF`, fuente `Inter-SemiBold` (13px), altura fija de 36px y borde inferior sutil en `#F3A500`.
* **Filas y Celdas**: Altura de 34px, texto en `#1F2115`, líneas divisorias en `#E5E7EB` y efecto hover en gris claro `#F9FAFB`.
* **Selección**: Color de acento `#F3A500` al seleccionar filas.

### 4.6 Tooltips Modernos (`QToolTip`)
* **Estilizado en `style.qss`**:
  ```qss
  QToolTip {
      background-color: #1F2115;
      color: #FFFFFF;
      border: 1px solid #414445;
      border-radius: 6px;
      padding: 6px 10px;
      font-size: 12px;
      font-family: 'Inter', sans-serif;
  }
  ```

---

## 📱 5. Especificación de Componentes UI: Aplicación Móvil (`accuraop_terreno`)

### 5.1 Pantalla Principal y Selector de Obra (`HomeScreen.js`)
* Tarjetas de obra con sombras sutiles, código de faena, porcentaje de avance físico y barra de progreso.
* Indicador superior de estado de conectividad (*Online 🟢 / Offline 🔴*) y conteo de registros pendientes de sincronizar.

### 5.2 Menú de Obra (`ObraMenu.js`)
4 Vías de operación táctil diseñadas para uso en faena:
1. **Registrar Avance**: Asistente de selección (Piso ➔ Eje ➔ Partida ➔ Cantidad $m^2$ ➔ Captura de Foto Obligatoria).
2. **Tomar Asistencia**: Foto grupal obligatoria de la cuadrilla + lista de maestros con botones táctiles de tres estados: Presente (1.0), Medio Día (0.5) y Ausente (0.0).
3. **Bitácora y Consumos**: Formulario de incidentes/novedades con fotos adjuntas y registro de materiales consumidos.
4. **Control de Obra**: Consulta offline de la dotación asignada y avance consolidado.
