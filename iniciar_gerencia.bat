@echo off
title GryPhus Conect Gerencia - Control de Obras
echo ====================================================
echo   Iniciando GryPhus Conect Gerencia (gryphus_conect_gerencia)...
echo ====================================================
cd /d "%~dp0"
call .venv\Scripts\activate.bat
cd gryphus_conect_gerencia
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Ocurrio un error al ejecutar la aplicacion.
    pause
)
