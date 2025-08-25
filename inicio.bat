@echo off
cd /d %~dp0

echo ============================
echo Iniciando App Flask
echo ============================

REM Activar entorno virtual
REM call venv\Scripts\activate

REM Instalar dependencias por si falta algo
REM pip install -r requirements.txt

REM Iniciar el servidor en segundo plano
REM start "" python app.py

REM Ejecutar Flask en background sin ventana
start "" pythonw.exe app.py

REM Esperar 3 segundos para que arranque
timeout /t 3 >nul

REM Abrir navegador automáticamente
start http://127.0.0.1:5080
