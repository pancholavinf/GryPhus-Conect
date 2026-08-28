@echo off
title Trabs Gerencia - Control de Obras
echo ====================================================
echo   Iniciando Trabs Gerencia (accuraop_gerencia)...
echo ====================================================
cd /d "%~dp0"
call .venv\Scripts\activate.bat
cd accuraop_gerencia
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Ocurrio un error al ejecutar la aplicacion.
    pause
)
