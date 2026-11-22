@echo off
rem installDataTools.cmd -- install or update the chart tools, which Homer programs use to draw charts of a table for
rem sighted readers: Python with pandas, matplotlib, seaborn and openpyxl (kit 1.269.0, 21 November 2026). Each is free
rem and under a license compatible with MIT. Without them DbDo's Generate Graphics falls back to Excel, when installed.
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

rem THREE PATHS, AS IN installPdfTools: no Python installs it, then the packages; Python present updates the packages;
rem reinstall puts them back in full.
where python >nul 2>&1
if errorlevel 1 goto :install
if defined bReinstall goto :reinstall
goto :update

:install
echo Installing the chart tools. Nothing is asked of you while it runs.
set "sHomerRunLong=winget install --id Python.Python.3.13 --exact --silent --accept-source-agreements --accept-package-agreements --disable-interactivity"
call "%~dp0installCommon.cmd" runLong "the chart tools"
set "iCode=%ERRORLEVEL%"
call "%~dp0installCommon.cmd" log "winget install Python.Python.3.13 exit code %iCode%"
if not "%iCode%"=="0" goto :failed
where python >nul 2>&1 || (echo Python is installed but not on this window's path yet; open a new window and run this again.& goto :done)
set "sHomerRunLong=python -m pip install --upgrade pandas matplotlib seaborn openpyxl"
call "%~dp0installCommon.cmd" runLong "the chart tools"
set "iCode=%ERRORLEVEL%"
call "%~dp0installCommon.cmd" log "pip install pandas matplotlib seaborn openpyxl exit code %iCode%"
if not "%iCode%"=="0" goto :failed
echo The chart tools are installed.
goto :done

:update
echo Python is installed. Making sure the chart packages are current.
set "sHomerRunLong=python -m pip install --upgrade pandas matplotlib seaborn openpyxl"
call "%~dp0installCommon.cmd" runLong "the chart tools"
set "iCode=%ERRORLEVEL%"
call "%~dp0installCommon.cmd" log "pip install pandas matplotlib seaborn openpyxl exit code %iCode%"
if "%iCode%"=="0" echo The chart packages are current.
if not "%iCode%"=="0" echo The chart packages could not be updated; the log says why.
rem Python has its own component, installPython; this updates the packages.
goto :done

:reinstall
echo Reinstalling the chart packages.
set "sHomerRunLong=python -m pip install --force-reinstall pandas matplotlib seaborn openpyxl"
call "%~dp0installCommon.cmd" runLong "the chart tools"
set "iCode=%ERRORLEVEL%"
call "%~dp0installCommon.cmd" log "pip install --force-reinstall pandas matplotlib seaborn openpyxl exit code %iCode%"
if not "%iCode%"=="0" goto :failed
echo The chart packages are reinstalled.
goto :done

:failed
echo(
echo The chart tools could not be installed automatically. The log says why:
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
