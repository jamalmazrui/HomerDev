@echo off
rem installNode.cmd -- install or update Node.js, which runs Ace by DAISY and other JavaScript tools.
rem
rem KIT COPY (HomerDev 1.69.1), one machine-wide component of the shared pattern. The long-term-support release; npm comes with it, which installs Ace. HomerDev recommends it.
rem It goes where its own installer puts it, never under a program's tree, so an upgrade of a program cannot take
rem it away. WHETHER IT IS INSTALLED IS ASKED OF WINGET, BY EACH PACKAGE ID IT IS KNOWN BY (OpenJS.NodeJS.LTS, OpenJS.NodeJS), not by a program
rem on the PATH, which an older, unrelated copy can answer for; checking one id alone would install a second copy
rem beside one registered under another. Installed: winget upgrade of the id found, which installs only something
rem newer. Missing, or reinstall: winget install of the first id. Installed outside winget: the long-term-support
rem package over it. Every command, exit code and the version before and after are in the log.
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
set "sWhat=Node.js"
rem WHICH PACKAGE OWNS NODE.JS IS READ FROM WINGET'S ANSWER, NOT ITS EXIT CODE (13 October 2026). winget list exits 0
rem on some machines while printing "No installed package found", so the first id was taken as installed, winget
rem upgrade then found nothing, and the update never happened: setup offered Update again on every install, since the
rem installed 25.9.0 stayed older than the 26.8.1 it had found. A package is installed only when its id is in the list.
set "sFound="
for %%I in (OpenJS.NodeJS.LTS OpenJS.NodeJS) do if not defined sFound (
  call "%~dp0installCommon.cmd" wingetHas %%I
  if not errorlevel 1 set "sFound=%%I"
)
set "sBefore="
for /f "delims=" %%V in ('node --version 2^>nul') do set "sBefore=%%V"
call "%~dp0installCommon.cmd" log "winget package: !sFound!; node.exe on the PATH reports: !sBefore!"
if defined bReinstall goto :install
if defined sFound goto :update
if defined sBefore (
  rem Installed, but not through winget -- the nodejs.org installer, most often. Node's installers upgrade an existing
  rem installation in place, so the long-term-support package is installed over it.
  call "%~dp0installCommon.cmd" log "Node.js !sBefore! is installed outside winget; installing OpenJS.NodeJS.LTS over it"
  echo Updating Node.js to the newest long-term-support release. Nothing is asked of you while it runs.
  set "sInstallId=OpenJS.NodeJS.LTS"
  set "sForce="
  goto :installRun
)

:install
set "sInstallId=OpenJS.NodeJS.LTS"
set "sForce="
if defined sFound set "sInstallId=!sFound!"
if defined bReinstall set "sForce=--force"
echo Installing Node.js. Nothing is asked of you while it runs.

:installRun
set "sHomerRunLong=winget install --id !sInstallId! !sForce! --exact --silent --accept-source-agreements --accept-package-agreements --disable-interactivity"
call "%~dp0installCommon.cmd" runLong "Node.js"
set "iCode=!ERRORLEVEL!"
call "%~dp0installCommon.cmd" log "winget install !sInstallId! !sForce! exit code !iCode!"
if not "!iCode!"=="0" goto :failed
goto :report

:update
rem SETUP HAS ALREADY DECIDED (13 October 2026): it compared the installed version with the newest and ticked Update only
rem when a newer one exists, so this updates rather than checking again.
call "%~dp0installCommon.cmd" wingetUpgrade !sFound! "Node.js"
if errorlevel 1 goto :failed

:report
set "sAfter="
for /f "delims=" %%V in ('node --version 2^>nul') do set "sAfter=%%V"
call "%~dp0installCommon.cmd" log "node.exe now reports: !sAfter! (was: !sBefore!)"
if defined sAfter (echo Node.js !sAfter! is installed.) else (echo Node.js is installed.)
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
