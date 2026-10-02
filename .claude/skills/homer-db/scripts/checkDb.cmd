@echo off
rem checkDb.cmd -- check a SQLite database against the Homer database
rem conventions DbDo follows. Reads only. checkDb.py says what each check means.
rem
rem     checkDb BookTrail.db     one database
rem     checkDb templates        every .db under a folder
setlocal
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found on the PATH. Install it with: winget install Python.Python.3.12
    endlocal
    exit /b 1
)
python "%~dp0checkDb.py" %*
set exitCode=%errorlevel%
endlocal & exit /b %exitCode%
