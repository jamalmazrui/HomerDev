@echo off
rem evalSkills.cmd -- measure whether the Homer skills make an AI write a better
rem program: the same task given to Claude Code without and with the skills,
rem each result built and scored with check and uiCheck. evalSkills.py says how.
rem
rem     evalSkills                 3 runs of each
rem     evalSkills --runs 5        5 of each
rem     evalSkills --model sonnet  the model Claude Code should use
rem     evalSkills --dry-run       prepare the folders, ask no AI
rem
rem The report and the log go to logs in the kit.
setlocal
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found on the PATH. Install it with: winget install Python.Python.3.12
    endlocal
    exit /b 1
)
python "%~dp0evalSkills.py" %*
set exitCode=%errorlevel%
endlocal & exit /b %exitCode%
