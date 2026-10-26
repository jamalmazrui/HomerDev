@echo off
rem installAce.cmd -- install or update Ace by DAISY, the EPUB accessibility checker, which the book tools run.
rem
rem KIT COPY (HomerDev 1.69.0; Node.js from installNode.cmd since 1.69.1), one machine-wide component of the shared pattern. Ace is an npm package: it needs
rem Node.js, installed here with winget when npm is missing, and goes where npm's global install puts it. The
rem installed version (ace --version) is compared with the registry's (npm view, which downloads nothing), and npm
rem installs only a newer one, a missing one, or on reinstall -- npm reinstalling Ace and its own Chromium takes
rem minutes, so it is never done for nothing. Every step is in the log.
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
set "sWhat=Ace by DAISY"
set "sNpm="
for /f "delims=" %%N in ('where npm.cmd 2^>nul') do if not defined sNpm set "sNpm=%%N"
if not defined sNpm if exist "%ProgramFiles%\nodejs\npm.cmd" set "sNpm=%ProgramFiles%\nodejs\npm.cmd"
rem NODE.JS IS ITS OWN COMPONENT (HomerDev 1.69.1): installNode.cmd installs it, by every id it is known by, so this
rem script never keeps a second copy of that logic.
if not defined sNpm (
  echo Ace needs Node.js, so it is installed first.
  call "%~dp0installNode.cmd" noPause
  call "%~dp0installCommon.cmd" log "installNode.cmd exit code !ERRORLEVEL!"
  if exist "%ProgramFiles%\nodejs\npm.cmd" set "sNpm=%ProgramFiles%\nodejs\npm.cmd"
)
if not defined sNpm goto :failed
for %%D in ("!sNpm!") do set "PATH=%%~dpD;%APPDATA%\npm;!PATH!"
set "sHave="
for /f "delims=" %%V in ('ace --version 2^>nul') do set "sHave=%%V"
set "sLatest="
for /f "delims=" %%V in ('call "!sNpm!" view @daisy/ace version 2^>nul') do set "sLatest=%%V"
call "%~dp0installCommon.cmd" log "Ace installed !sHave!, latest on npm !sLatest!"
if defined sHave if not defined bReinstall if "!sHave!"=="!sLatest!" (echo Ace by DAISY !sHave! is the latest.& goto :done)
if defined sHave if not defined bReinstall if not defined sLatest (echo Ace by DAISY !sHave! is installed; npm could not be asked for a newer one.& goto :done)
echo Installing Ace by DAISY !sLatest! with npm. This fetches its own copy of Chromium and takes a few minutes.
set "sHomerRunLong=call "!sNpm!" install --global @daisy/ace@latest"
call "%~dp0installCommon.cmd" runLong "Ace by DAISY"
set "iCode=!ERRORLEVEL!"
call "%~dp0installCommon.cmd" log "npm install --global @daisy/ace exit code !iCode!"
if not "!iCode!"=="0" goto :failed
echo Ace by DAISY is installed.
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
