@echo off
rem installPywinauto.cmd -- install, update or reinstall pywinauto, which drives an app by its keys and reads what has focus, with soundcard and numpy to record the screen reader, for recordWalk.
rem
rem Run from the installer's final page, or on its own at any time. The common half -- the log under
rem %LOCALAPPDATA%\<App>\logs, the quiet flag when the installer is driving -- is the kit's installCommon.cmd, so a
rem fix there reaches every install script in every Homer app. It follows installPdfTools.cmd: three paths,
rem each reached -- install when it is absent, update when it is there, reinstall when asked (5 November 2026).
rem Python is its own component, installPython, on the same page; this one does not install or update Python.
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

where python >nul 2>&1
if errorlevel 1 (
  echo pywinauto needs Python, which is not installed yet. Tick Python on this page, or run installPython, then this again.
  call "%~dp0installCommon.cmd" log "Python not found; pywinauto not installed"
  goto :failed
)
if defined bReinstall goto :reinstall
echo Installing or updating pywinauto, soundcard and numpy. Nothing is asked of you while it runs.
set "sHomerRunLong=python -m pip install --user --upgrade pywinauto soundcard numpy"
call "%~dp0installCommon.cmd" runLong "pywinauto"
set "iCode=%ERRORLEVEL%"
call "%~dp0installCommon.cmd" log "python -m pip install --user --upgrade pywinauto soundcard numpy exit code %iCode%"
if not "%iCode%"=="0" goto :failed
echo pywinauto, soundcard and numpy are ready.
goto :done

:reinstall
echo Reinstalling pywinauto, soundcard and numpy.
set "sHomerRunLong=python -m pip install --user --force-reinstall pywinauto soundcard numpy"
call "%~dp0installCommon.cmd" runLong "pywinauto"
set "iCode=%ERRORLEVEL%"
call "%~dp0installCommon.cmd" log "python -m pip install --user --force-reinstall pywinauto soundcard numpy exit code %iCode%"
if not "%iCode%"=="0" goto :failed
echo pywinauto, soundcard and numpy are reinstalled.
goto :done

:failed
echo(
echo pywinauto could not be installed automatically. The log says why:
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
