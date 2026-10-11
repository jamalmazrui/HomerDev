@echo off
rem installMpv.cmd -- install or update mpv, which Homer programs use to play audio and video in the Player.
rem
rem Run from the installer's final page, or on its own at any time. The
rem common half -- the log under %LOCALAPPDATA%\<App>\logs, the quiet
rem flag when the installer is driving -- is the kit's installCommon.cmd, so a
rem fix there reaches every install script in every Homer app.
rem
rem MACHINE WIDE, to its own default folder, never under a program's own tree: an
rem upgrade of a program replaces that tree and would take the tool with it.
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

where mpv >nul 2>&1
if not errorlevel 1 if not defined bReinstall goto :update

echo Installing mpv. Nothing is asked of you while it runs.
winget install --id shinchiro.mpv --exact --silent --accept-source-agreements --accept-package-agreements --disable-interactivity >> "%log%" 2>&1
set "iCode=%ERRORLEVEL%"
call "%~dp0installCommon.cmd" log "winget install shinchiro.mpv exit code %iCode%"
if not "%iCode%"=="0" goto :failed
echo mpv is installed.
goto :done

:update
echo mpv is installed. Checking for a newer version.
winget upgrade --id shinchiro.mpv --exact --silent --accept-source-agreements --accept-package-agreements --disable-interactivity >> "%log%" 2>&1
set "iCode=%ERRORLEVEL%"
call "%~dp0installCommon.cmd" log "winget upgrade shinchiro.mpv exit code %iCode%"
if "%iCode%"=="0" echo mpv was updated.
if not "%iCode%"=="0" echo mpv is already the newest winget offers.
goto :done

:failed
echo(
echo mpv could not be installed automatically. The log says why:
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
