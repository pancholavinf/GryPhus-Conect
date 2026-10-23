@echo off
title Publicando GryPhus Conect Gerencia v1.0.5
echo ====================================================
echo   Publicando GryPhus Conect Gerencia Version 1.0.5
echo ====================================================
echo.
cd /d "%~dp0"
if exist "..\venv\Scripts\activate.bat" (
    call ..\venv\Scripts\activate.bat
) else if exist "..\.venv\Scripts\activate.bat" (
    call ..\.venv\Scripts\activate.bat
)

python publish_release.py --version 1.0.5 --notes "• Nueva pestaña 'Ítems de Obra' en el dashboard de cada faena con filtros avanzados en tiempo real, búsqueda y ficha técnica interactiva por partida.\n• Visualización de avances históricos y evidencias fotográficas vinculadas a cada ítem individual.\n• Rediseño ultra-compacto y optimizado del encabezado de perfil de supervisores y maestros técnicos.\n• Mejoras de espaciado y márgenes en formularios y títulos para evitar solapamientos.\n• Normalización y mapeo resiliente de roles de supervisores en la interfaz."

echo.
echo ====================================================
echo   Proceso de version v1.0.5 finalizado.
echo ====================================================
pause
