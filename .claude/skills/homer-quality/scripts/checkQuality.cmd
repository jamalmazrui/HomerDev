@echo off
rem checkQuality.cmd -- the homer-quality skill's checker; every argument goes to checkQuality.py.
setlocal
where python >nul 2>&1
if errorlevel 1 (
  echo Python was not found. Install it from python.org, or with winget install Python.Python.3.13, then run this again.
  exit /b 2
)
python "%~dp0checkQuality.py" %*
set exitCode=%errorlevel%
endlocal & exit /b %exitCode%
