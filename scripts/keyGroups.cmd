@echo off
rem keyGroups.cmd -- count the Homer Suite's keys by pattern group into help\KeyGroups.md. No arguments are
rem needed: it reads the key files of DbDo, EdSharp, FileDir and HomerView from the folders beside the kit.
setlocal
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found on the PATH. Install it with: winget install Python.Python.3.12
    endlocal
    exit /b 1
)
python "%~dp0keyGroups.py" %*
set "iExit=%errorlevel%"
endlocal & exit /b %iExit%
