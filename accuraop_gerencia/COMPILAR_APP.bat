@echo off
title Compilando Trabs Gerencia (.EXE)
echo ====================================================
echo   Compilando Trabs Gerencia con PyInstaller...
echo ====================================================
cd /d "%~dp0"
call ..\.venv\Scripts\activate.bat
python build_exe.py
echo.
echo ====================================================
echo   Proceso finalizado. Presiona una tecla para salir.
echo ====================================================
pause
