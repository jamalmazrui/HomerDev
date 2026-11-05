@echo off
rem installAxeWindows.cmd -- install, update or reinstall Axe.Windows, which checks a window's accessibility, as Accessibility Insights for Windows does.
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
  echo Axe.Windows needs Python, which is not installed yet. Tick Python on this page, or run installPython, then this again.
  call "%~dp0installCommon.cmd" log "Python not found; Axe.Windows not installed"
  goto :failed
)
if defined bReinstall goto :fresh
if exist "%LOCALAPPDATA%\HomerDev\tools\AxeWindowsCLI\AxeWindowsCLI.exe" goto :fresh
echo Installing Axe.Windows. Nothing is asked of you while it runs.
set "sHomerRunLong=python "%~dp0axeScan.py" --fetch"
call "%~dp0installCommon.cmd" runLong "Axe.Windows"
set "iCode=%ERRORLEVEL%"
call "%~dp0installCommon.cmd" log "python '%~dp0axeScan.py' --fetch exit code %iCode%"
if not "%iCode%"=="0" goto :failed
echo Axe.Windows is installed.
goto :done

:fresh
rem Its newest version is on GitHub, not in winget, so a copy already here is replaced by the newest release.
echo Getting the newest Axe.Windows.
set "sHomerRunLong=python "%~dp0axeScan.py" --fetch --fresh"
call "%~dp0installCommon.cmd" runLong "Axe.Windows"
set "iCode=%ERRORLEVEL%"
call "%~dp0installCommon.cmd" log "python '%~dp0axeScan.py' --fetch --fresh exit code %iCode%"
if not "%iCode%"=="0" goto :failed
echo Axe.Windows is the newest release.
goto :done

:failed
echo(
echo Axe.Windows could not be installed automatically. The log says why:
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
