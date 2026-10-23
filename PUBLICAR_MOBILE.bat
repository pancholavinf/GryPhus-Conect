@echo off
title Publicador Automático de GryPhus Conect Terreno (Mobile APK)
echo ====================================================
echo   Publicador de Nuevas Versiones a GitHub Releases
echo   Modulo: GryPhus Conect Terreno (Mobile APK)
echo ====================================================
cd /d "%~dp0"
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)
cd gryphus_conect_terreno
python publish_mobile.py %*
echo.
pause
