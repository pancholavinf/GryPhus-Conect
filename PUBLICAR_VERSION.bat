@echo off
title Publicador Automático de Trabs Gerencia
echo ====================================================
echo   Publicador de Nuevas Versiones a GitHub Releases
echo ====================================================
cd /d "%~dp0"
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)
cd accuraop_gerencia
python publish_release.py %*
echo.
pause
