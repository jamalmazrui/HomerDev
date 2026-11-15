@echo off
rem installExifTool.cmd -- install or update ExifTool, which reads what a recording or photo knows about itself and
rem writes descriptions into photographs.
rem
rem WHY IT CHANGED. This script ran "winget install OliverBetz.ExifTool" whatever was there. Setup knows ExifTool by
rem two ids, OliverBetz.ExifTool and PhilHarvey.ExifTool, so a copy registered under the second would have been joined
rem by a second copy rather than updated, and Reinstall was not honored (15 November 2026, the installer audit).
rem
rem THE SHARED PATTERN (HomerDev 1.232.0, 15 November 2026), as installGitHubCli and the rest have had since 1.69.1.
rem WHETHER IT IS INSTALLED IS ASKED OF WINGET, by each package id it is known by, never of the PATH, which an older,
rem unrelated copy can answer for. Installed: winget upgrade of the id found, which installs only something newer.
rem Missing, or reinstall: winget install of the id found, else the first. Before and after, every copy on the PATH or
rem in its own folder is logged with its version, and an older copy that comes first on the PATH is named.
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
set "sWhat=ExifTool"
where winget >nul 2>&1
if errorlevel 1 (
  call "%~dp0installCommon.cmd" say "winget was not found, so ExifTool cannot be installed or updated automatically."
  goto :failed
)
call "%~dp0installCommon.cmd" copies exiftool.exe "%ProgramFiles%\ExifTool\exiftool.exe" "%LOCALAPPDATA%\Programs\ExifTool\exiftool.exe"
call "%~dp0installCommon.cmd" log "before: !sHomerCopies!"
set "sFound="
for %%I in (OliverBetz.ExifTool PhilHarvey.ExifTool) do if not defined sFound (
  call "%~dp0installCommon.cmd" wingetHas %%I
  if not errorlevel 1 set "sFound=%%I"
)
call "%~dp0installCommon.cmd" log "installed under: !sFound!"
if defined sFound if not defined bReinstall goto :update
rem A REINSTALL REINSTALLS ExifTool IS THERE: the id it is registered under, forced, never a second copy beside it.
set "sInstallId=OliverBetz.ExifTool"
set "sForce="
if defined sFound set "sInstallId=!sFound!"
if defined bReinstall set "sForce=--force"
echo Installing ExifTool. About 10 MB, and nothing is asked of you while it runs.
set "sHomerRunLong=winget install --id !sInstallId! !sForce! --exact --silent --accept-source-agreements --accept-package-agreements --disable-interactivity"
call "%~dp0installCommon.cmd" runLong "ExifTool"
set "iCode=!ERRORLEVEL!"
call "%~dp0installCommon.cmd" log "winget install !sInstallId! !sForce! exit code !iCode!"
if not "!iCode!"=="0" goto :failed
echo ExifTool is installed.
goto :after

:update
call "%~dp0installCommon.cmd" wingetUpgrade !sFound! "ExifTool"
if errorlevel 1 goto :failed

:after
call "%~dp0installCommon.cmd" copies exiftool.exe "%ProgramFiles%\ExifTool\exiftool.exe" "%LOCALAPPDATA%\Programs\ExifTool\exiftool.exe"
call "%~dp0installCommon.cmd" log "after: !sHomerCopies!"
if defined sHomerShadow call "%~dp0installCommon.cmd" say "!sHomerShadow!"
goto :done

:failed
echo(
echo %sWhat% could not be installed or updated automatically. The log says why:
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
