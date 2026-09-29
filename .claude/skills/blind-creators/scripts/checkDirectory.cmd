@echo off
setlocal
where py >nul 2>&1 && ( py -3 "%~dp0checkDirectory.py" %* ) || ( python "%~dp0checkDirectory.py" %* )
endlocal
