@echo off
rem installPython.cmd -- install or update Python, which runs the kit's scripts.
rem
rem KIT COPY (HomerDev 1.69.1), one machine-wide component of the shared pattern. The kit's scripts -- build, tidy, check, buildBooks, fetchStations -- are Python; HomerDev recommends it.
rem It goes where its own installer puts it, never under a program's tree, so an upgrade of a program cannot take
rem it away. WHETHER IT IS INSTALLED IS ASKED OF WINGET, BY EACH PACKAGE ID IT IS KNOWN BY (Python.Python.3.14, Python.Python.3.13), not by a program
rem on the PATH, which an older, unrelated copy can answer for; checking one id alone would install a second copy
rem beside one registered under another. Installed: winget upgrade of the id found, which installs only something
rem newer. Missing, or reinstall: winget install of the first id. Every command and exit code is in the log.
setlocal enabledelayedexpansion
set "sScript=%~n0"
if not exist "%~dp0installCommon.cmd" (
  echo(
  echo installCommon.cmd is missing from %~dp0
  echo That file is part of this program. Reinstall, or copy it from the
  echo program's zip into this folder, and run this again.
  echo(
  if not defined noPause pause
  exit /b 1
)
call "%~dp0installCommon.cmd" setup "%~f0" %*

set "bReinstall="
for %%A in (%*) do if /i "%%A"=="reinstall" set "bReinstall=1"
set "sWhat=Python"
set "sFound="
for %%I in (Python.Python.3.14 Python.Python.3.13) do if not defined sFound (
  call "%~dp0installCommon.cmd" wingetHas %%I
  if not errorlevel 1 set "sFound=%%I"
)
call "%~dp0installCommon.cmd" log "installed under: !sFound!"
if defined sFound if not defined bReinstall goto :update
rem A REINSTALL REINSTALLS WHAT IS THERE: the id it is registered under, forced, never a second copy beside it.
set "sInstallId=Python.Python.3.14"
set "sForce="
if defined sFound set "sInstallId=!sFound!"
if defined bReinstall set "sForce=--force"

echo Installing Python. Nothing is asked of you while it runs.
winget install --id !sInstallId! !sForce! --exact --silent --accept-source-agreements --accept-package-agreements --disable-interactivity >> "%log%" 2>&1
set "iCode=!ERRORLEVEL!"
call "%~dp0installCommon.cmd" log "winget install !sInstallId! !sForce! exit code !iCode!"
if not "!iCode!"=="0" goto :failed
echo Python is installed.
goto :done

:update
call "%~dp0installCommon.cmd" wingetUpgrade !sFound! "Python"
if errorlevel 1 goto :failed
goto :done

:failed
echo(
echo %sWhat% could not be installed automatically. The log says why:
echo   %log%
echo(
if not defined noPause pause
endlocal
exit /b 1

:done
echo(
if not defined noPause pause
endlocal
exit /b 0
