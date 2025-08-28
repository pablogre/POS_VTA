@echo off
start "Flask Server" /min python app.py
timeout /t 2 >nul
start http://127.0.0.1:5080
echo Flask iniciado - ventana minimizada en la barra de tareas
timeout /t 1 >nul
exit