@echo off
rem skillsPage.cmd -- the kit's skills as one web page, Homer Skills, with each skill's zip, the
rem Agent Skills discovery index and llms.txt beside it. skillsPage.py says how.
rem
rem     skillsPage              write it in MyPages\pages\HomerSkills, or the kit's work folder
rem     skillsPage <folder>     write it in that folder
setlocal
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found on the PATH. Install it with: winget install Python.Python.3.12
    endlocal
    exit /b 1
)
python "%~dp0skillsPage.py" %*
set exitCode=%errorlevel%
endlocal & exit /b %exitCode%
