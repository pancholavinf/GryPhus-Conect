# Original User Request

## 2026-07-29T23:12:37Z

<USER_REQUEST>
Sistema de Control de Asistencia Diario, Maestros y Tarifas Diarias en la plataforma Accurateck (Supabase, App Móvil React Native Expo app_trackeo_avances, App de Escritorio PyQt6 app_local).

Working directory: C:\Users\fcola\Desktop\APPACCURATEK
Integrity mode: development

## Requirements

### R1. Base de Datos en Supabase (PostgreSQL & RLS)
Crear e integrar las tablas `tipos_maestro` (cargos y `sueldo_diario`), `maestros` (perfil de trabajador), `obras_maestros` (asignación a obras), `asistencia_diaria` (cabecera con foto, fecha y flag `es_correctivo`) y `asistencia_diaria_detalle` (evaluación con 1.0 Día Completo, 0.5 Medio Día, 0.0 Ausente). Configurar políticas RLS para lectura y escritura seguras.

### R2. App Móvil (`app_trackeo_avances`)
Implementar la toma de asistencia diaria offline en SQLite con sincronización bidireccional en Supabase. Agregar botón "Asistencia de Personal" en el menú de obras, permitir seleccionar la asistencia de cada maestro asignado (1.0, 0.5, 0.0), requerir foto de evidencia y permitir el envío de un "Reporte Correctivo de Asistencia" si la asistencia del día ya fue enviada previamente.

### R3. App de Escritorio (`app_local`)
Renombrar/reorganizar la pestaña a "Control de Personal" dividida en 3 pestañas: Jefes de Obra, Maestros (con opción de crear nuevo tipo/cargo sobre la marcha) y Cargos y Tarifas Diarias (CRUD de cargos y `sueldo_diario`). Actualizar el Dashboard con resumen KPI de asistencia y crear la pestaña/módulo de Reportes de Asistencia por Obra con filtro de rango de fechas, resumen de medios días/días enteros, cálculo de sueldos totales y exportación a Excel/PDF.

## Acceptance Criteria

### Verificación de Base de Datos
- [ ] Tablas `tipos_maestro`, `maestros`, `obras_maestros`, `asistencia_diaria` y `asistencia_diaria_detalle` creadas con relaciones FK e índices requeridos.

### Verificación App Móvil
- [ ] El menú de la obra muestra la opción de Asistencia de Personal.
- [ ] Permite marcar Día Completo (1.0), Medio Día (0.5) y Ausente (0.0), requiriendo foto de evidencia.
- [ ] La asistencia se guarda localmente en SQLite y se sincroniza con Supabase mediante `sync.js`.
- [ ] Si ya se envió asistencia en el día, permite registrar un Reporte Correctivo.

### Verificación App Escritorio
- [ ] La barra lateral incluye la pestaña "Control de Personal" con las 3 sub-pestañas operativas.
- [ ] Se pueden crear/editar cargos con su `sueldo_diario` y asignar maestros a obras.
- [ ] El Dashboard muestra las métricas de asistencia del día por obra.
- [ ] Se pueden generar reportes de asistencia por obra filtrando por fechas, mostrando totales de jornales/pagos y exportando a Excel/PDF.
</USER_REQUEST>
