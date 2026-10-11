@echo off
rem connectAI.cmd -- tell the AI command-line tools on this computer where the Homer
rem Development Kit is, once: a pointer in each tool's personal instruction file, and
rem the kit's skills linked into its personal skills folder. connectAI.py says how.
rem
rem     connectAI              connect every AI tool found
rem     connectAI --check      say what is connected, and change nothing
rem     connectAI --remove     take back out everything connectAI put in
setlocal
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found on the PATH. Install it with: winget install Python.Python.3.12
    endlocal
    exit /b 1
)
python "%~dp0connectAI.py" %*
set exitCode=%errorlevel%
endlocal & exit /b %exitCode%
