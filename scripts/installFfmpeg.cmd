@echo off
rem installFfmpeg.cmd -- install or update ffmpeg, which Homer programs use to convert audio and video and measure their length.
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

where ffmpeg >nul 2>&1
if not errorlevel 1 if not defined bReinstall goto :update

echo Installing ffmpeg. Nothing is asked of you while it runs.
set "sHomerRunLong=winget install --id Gyan.FFmpeg --exact --silent --accept-source-agreements --accept-package-agreements --disable-interactivity"
call "%~dp0installCommon.cmd" runLong "FFmpeg"
set "iCode=%ERRORLEVEL%"
call "%~dp0installCommon.cmd" log "winget install Gyan.FFmpeg exit code %iCode%"
if not "%iCode%"=="0" goto :failed
echo ffmpeg is installed.
goto :done

:update
call "%~dp0installCommon.cmd" wingetUpgrade Gyan.FFmpeg "ffmpeg"
if errorlevel 1 goto :failed
goto :done

:failed
echo(
echo ffmpeg could not be installed automatically. The log says why:
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
