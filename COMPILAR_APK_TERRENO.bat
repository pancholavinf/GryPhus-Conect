@echo off
title Compilador de GryPhus Conect Terreno (APK Android con EAS Build)
echo ====================================================
echo   Compilador de APK para Android - GryPhus Conect Terreno
echo   Servicio: Expo Application Services (EAS Build)
echo ====================================================
cd /d "%~dp0\gryphus_conect_terreno"
echo.
echo [1/2] Iniciando compilacion de APK en la nube (Perfil Preview)...
echo Nota: Si es tu primera vez, te solicitara iniciar sesion en tu cuenta de Expo (expo.dev).
echo.
call npx --yes eas-cli build -p android --profile preview
echo.
echo ====================================================
echo   Proceso finalizado. 
echo   Descarga el archivo .apk desde el enlace proporcionado por EAS.
echo ====================================================
pause
