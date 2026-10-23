@echo off
title Compilando GryPhus Conect Gerencia (.EXE)
echo ====================================================
echo   Compilando GryPhus Conect Gerencia con PyInstaller...
echo ====================================================
cd /d "%~dp0"
call .venv\Scripts\activate.bat
cd gryphus_conect_gerencia
python build_exe.py
echo.
echo ====================================================
echo   Proceso finalizado. Presiona una tecla para salir.
echo ====================================================
pause
