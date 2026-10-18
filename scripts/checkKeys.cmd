@echo off
rem checkKeys.cmd -- check the Homer Suite commands and keys. Arguments are
rem passed on: export files written with /exportkeys, and --gate.
setlocal
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found on the PATH. Install it with: winget install Python.Python.3.12
    endlocal
    exit /b 1
)
python "%~dp0checkKeys.py" %*
set "iExit=%errorlevel%"
endlocal & exit /b %iExit%
