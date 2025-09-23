@echo off
title Instalador MariaDB
echo ================================
echo INSTALADOR MARIADB PARA POS
echo ================================
echo.

REM Verificar si ya esta instalado
sc query MariaDB >nul 2>&1
if %errorlevel% equ 0 (
    echo MariaDB ya esta instalado
    echo.
    goto configurar_bd
)

echo Descargando MariaDB...
mkdir "%TEMP%\mariadb_install" 2>nul
powershell -Command "Invoke-WebRequest -Uri 'https://downloads.mariadb.org/rest-api/mariadb/11.1.2/mariadb-11.1.2-winx64.msi' -OutFile '%TEMP%\mariadb_install\mariadb.msi'"

if %errorlevel% neq 0 (
    echo Error descargando MariaDB
    echo Descarga manual desde: https://mariadb.org/download/
    pause
    exit /b 1
)

echo.
echo Instalando MariaDB...
echo IMPORTANTE: Usa password 'admin123' para root
echo.
pause

msiexec /i "%TEMP%\mariadb_install\mariadb.msi" /qb

echo.
echo Iniciando servicio MariaDB...
timeout /t 10
net start MariaDB

:configurar_bd
echo.
echo ================================
echo CONFIGURANDO BASE DE DATOS
echo ================================
echo.

REM Crear script de configuracion
echo CREATE DATABASE IF NOT EXISTS pos_argentina; > setup.sql
echo CREATE USER IF NOT EXISTS 'pos_user'@'localhost' IDENTIFIED BY 'pos_password'; >> setup.sql
echo GRANT ALL PRIVILEGES ON pos_argentina.* TO 'pos_user'@'localhost'; >> setup.sql
echo FLUSH PRIVILEGES; >> setup.sql

echo Configurando base de datos...
echo Ingresa la password de root (admin123):
"C:\Program Files\MariaDB 11.1\bin\mysql.exe" -u root -p < setup.sql

if %errorlevel% equ 0 (
    echo.
    echo Base de datos configurada correctamente
    echo Database: pos_argentina
    echo User: pos_user
    echo Password: pos_password
) else (
    echo.
    echo Error configurando base de datos
)

del setup.sql 2>nul
rmdir /s /q "%TEMP%\mariadb_install" 2>nul

echo.
echo Configuracion completada
pause