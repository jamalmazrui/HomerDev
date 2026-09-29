@echo off
setlocal
where py >nul 2>&1 && ( py -3 "%~dp0buildDirectory.py" %* ) || ( python "%~dp0buildDirectory.py" %* )
endlocal
