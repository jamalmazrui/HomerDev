@echo off
rem installJava.cmd -- install or update Java, which runs EPUBCheck.
rem
rem KIT COPY (HomerDev 1.69.0), one machine-wide component of the shared pattern. Microsoft's build of OpenJDK 21, which EPUBCheck needs (Java 11 or later).
rem It goes where its own installer puts it, never under a program's tree, so an upgrade of a program cannot take
rem it away. WHETHER IT IS INSTALLED IS ASKED OF WINGET BY PACKAGE ID, not by a program on the PATH, which an older,
rem unrelated copy can answer for. Installed: winget upgrade, which installs only something newer. Missing or
rem reinstall: winget install. Every command and exit code is in the log.
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
set "sWhat=Java"

winget list --id Microsoft.OpenJDK.21 --exact --accept-source-agreements >nul 2>&1
if not errorlevel 1 if not defined bReinstall goto :update

echo Installing Java. Nothing is asked of you while it runs.
winget install --id Microsoft.OpenJDK.21 --exact --silent --accept-source-agreements --accept-package-agreements --disable-interactivity >> "%log%" 2>&1
set "iCode=%ERRORLEVEL%"
call "%~dp0installCommon.cmd" log "winget install Microsoft.OpenJDK.21 exit code %iCode%"
if not "%iCode%"=="0" goto :failed
echo Java is installed.
goto :done

:update
echo Java is installed. Checking for a newer version.
winget upgrade --id Microsoft.OpenJDK.21 --exact --silent --accept-source-agreements --accept-package-agreements --disable-interactivity >> "%log%" 2>&1
set "iCode=%ERRORLEVEL%"
call "%~dp0installCommon.cmd" log "winget upgrade Microsoft.OpenJDK.21 exit code %iCode%"
if "%iCode%"=="0" echo Java was updated.
if not "%iCode%"=="0" echo Java is already the newest winget offers.
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
