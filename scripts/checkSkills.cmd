@echo off
rem checkSkills.cmd -- check every Claude skill in a project against the rules a skill must meet to load and to be
rem chosen; checkSkills.py says which. Forwards every argument. Part of the HomerDev kit.
rem
rem     checkSkills                 the skills of the project this is run from
rem     checkSkills D:\Work\DbDo    another project's skills
setlocal
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found on the PATH. Install it with: winget install Python.Python.3.12
    endlocal
    exit /b 1
)
python "%~dp0checkSkills.py" %*
set exitCode=%errorlevel%
endlocal & exit /b %exitCode%
