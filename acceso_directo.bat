@echo off
title FactuFacil Launcher
color 0a
echo.
echo ====================================
echo     FACTUFACIL LAUNCHER
echo ====================================
echo.
echo 1. Abrir en navegador predeterminado
echo 2. Abrir en Chrome
echo 3. Abrir en Edge
echo 4. Abrir en Firefox
echo 5. Verificar estado del servicio
echo 6. Salir
echo.
set /p opcion="Seleccione una opcion (1-6): "

if "%opcion%"=="1" goto navegador_default
if "%opcion%"=="2" goto chrome
if "%opcion%"=="3" goto edge
if "%opcion%"=="4" goto firefox
if "%opcion%"=="5" goto verificar_servicio
if "%opcion%"=="6" goto salir
goto menu

:navegador_default
echo Abriendo en navegador predeterminado...
start http://127.0.0.1:5080
goto fin

:chrome
echo Abriendo en Google Chrome...
start chrome http://127.0.0.1:5080
goto fin

:edge
echo Abriendo en Microsoft Edge...
start msedge http://127.0.0.1:5080
goto fin

:firefox
echo Abriendo en Firefox...
start firefox http://127.0.0.1:5080
goto fin

:verificar_servicio
echo.
echo Verificando estado del servicio FactuFacil...
sc query factufacil
echo.
echo Verificando puerto 5080...
netstat -an | findstr 5080
echo.
pause
goto menu

:menu
cls
goto inicio

:fin
echo.
echo FactuFacil abierto exitosamente!
timeout /t 3 /nobreak >nul

:salir
exit