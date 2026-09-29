@echo off
setlocal
where py >nul 2>&1 && ( py -3 "%~dp0buildCreators.py" %* ) || ( python "%~dp0buildCreators.py" %* )
endlocal
