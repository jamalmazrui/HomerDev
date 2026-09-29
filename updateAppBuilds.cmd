@echo off
rem updateAppBuilds.cmd -- bring app build scripts up to the kit's current layout.
rem   updateAppBuilds              every app beside the kit that needs it
rem   updateAppBuilds Jobrise      only the apps named
rem The work is in updateAppBuilds.py; its log is in logs.
setlocal
where python >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python was not found on the PATH.
  endlocal
  exit /b 1
)
python "%~dp0updateAppBuilds.py" %*
set "iCode=%errorlevel%"
endlocal & exit /b %iCode%
