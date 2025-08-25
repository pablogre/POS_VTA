Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c inicio.bat", 0, False
WshShell.Run "http://127.0.0.1:5080"
