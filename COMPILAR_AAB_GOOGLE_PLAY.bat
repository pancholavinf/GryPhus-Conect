@echo off
title Compilador de GryPhus Conect Terreno (AAB para Google Play Console)
echo ================================================================
echo   Compilador de Android App Bundle (.aab) - GryPhus Conect Terreno
echo   Destino: Google Play Console (Produccion / Pruebas Cerradas)
echo   Servicio: Expo Application Services (EAS Build)
echo ================================================================
cd /d "%~dp0\gryphus_conect_terreno"
echo.
echo [1/2] Verificando configuracion de produccion...
echo El paquete a compilar es: com.gryphus.conect.terreno en formato .aab
echo.
echo [2/2] Iniciando compilacion en la nube con EAS Build (Perfil Production)...
echo Nota: Si es tu primera vez, EAS te solicitara:
echo   - Iniciar sesion con tu cuenta de Expo (expo.dev).
echo   - Generar la clave de firma (Keystore) automaticamente (Presiona Y / Si).
echo.
call npx --yes eas-cli build -p android --profile production
echo.
echo ================================================================
echo   Compilacion finalizada exitosamente.
echo.
echo   PASOS SIGUIENTES PARA GOOGLE PLAY CONSOLE:
echo   1. Descarga el archivo .aab desde el enlace que te mostro EAS arriba.
echo   2. Ingresa a tu cuenta de Google Play Console (play.google.com/console).
echo   3. En tu aplicacion, ve a 'Produccion' o 'Pruebas Cerradas' (Testing).
echo   4. Crea un nuevo lanzamiento y sube el archivo .aab descargado.
echo ================================================================
pause
