@echo off
setlocal EnableDelayedExpansion
rem build_release -- the Homer development cycle for the project in the current folder: build, tidy, check, push
rem and release, in that order, stopping at the first step that fails, so nothing broken is pushed or released.
rem
rem THE KIT'S ONE COPY (1.65.25). Each project had its own build_release.bat, written by hand, and copies drift as
rem the installers did. The kit's build now writes this file as build_release.bat at the top of every project beside
rem the kit, and of the kit itself; it acts on the current folder, so the same file serves them all.
rem
rem CHECK BEFORE PUSH (1.65.25). The acceptance checks -- the installer pattern, the tutorials, the encoding -- ran
rem only inside release, after push had already sent the code to GitHub. They now run after tidy and before push, so
rem a failing check stops the cycle before anything leaves the computer. release still runs its own as the last gate.
rem
rem A LOG OF ITS OWN: logs\<Project>-build_release-<stamp>.log holds the environment, and each step's command, exit
rem code and time; each step also writes its own detailed log. The console says one line a step.

for %%I in ("%CD%") do set "sName=%%~nxI"
if not exist "build.cmd" (
  echo There is no build.cmd in %CD%, so this is not a Homer project folder. Change to the project's folder first.
  exit /b 1
)
if not exist "logs" mkdir "logs"
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "sStamp=%%i"
set "sLog=%CD%\logs\%sName%-build_release-%sStamp%.log"
for /f "tokens=*" %%v in ('ver') do set "sWindows=%%v"
> "%sLog%" echo build_release started %date% %time%
>> "%sLog%" echo Script: %~f0
>> "%sLog%" echo Project: %CD%
>> "%sLog%" echo User: %USERNAME% on %COMPUTERNAME%
>> "%sLog%" echo Windows: !sWindows!
>> "%sLog%" echo Arguments: %*

rem The project's own steps; the kit releases with releaseHomerDev, and checks with checkHomerDev.
set "sCheck="
if exist "scripts\check.cmd" set "sCheck=scripts\check.cmd"
if exist "checkHomerDev.cmd" set "sCheck=checkHomerDev.cmd"
set "sRelease=scripts\release.cmd"
if exist "releaseHomerDev.cmd" set "sRelease=releaseHomerDev.cmd"
>> "%sLog%" echo Settings: check=!sCheck! release=!sRelease!
set "sSummary="

call :step build "build.cmd" || goto :stopped
call :step tidy "scripts\tidy.cmd" || goto :stopped
if defined sCheck (
  call :step check "!sCheck!" || goto :stopped
) else (
  >> "%sLog%" echo check: no check script in this project; skipped
)
call :step push "scripts\push.cmd" || goto :stopped
call :step release "!sRelease!" || goto :stopped

echo(
set "sSummary=!sSummary:~0,-1!"
echo Built, tidied, checked, pushed and released:!sSummary!.
>> "%sLog%" echo Finished %date% %time%: every step passed:!sSummary!
exit /b 0

:step
rem %1 the step's name, %2 the script it runs.
set "sStep=%~1"
if not exist "%~2" (
  echo %~1: %~2 is not in this project, so the cycle stops here.
  >> "%sLog%" echo %~1: %~2 not found
  exit /b 1
)
for /f %%t in ('powershell -NoProfile -Command "[int][double]::Parse((Get-Date -UFormat %%s))"') do set "iStart=%%t"
>> "%sLog%" echo %~1: started %time%, running %~2
echo %~1 ...
call "%~2"
set "iCode=!errorlevel!"
for /f %%t in ('powershell -NoProfile -Command "[int][double]::Parse((Get-Date -UFormat %%s))"') do set "iEnd=%%t"
set /a "iSeconds=iEnd-iStart, iMin=iSeconds/60, iSec=iSeconds %% 60"
if !iMin! gtr 0 (set "sTook=!iMin!m !iSec!s") else (set "sTook=!iSec!s")
>> "%sLog%" echo %~1: exit code !iCode!, !sTook!
if not "!iCode!"=="0" exit /b !iCode!
set "sSummary=!sSummary! %~1 !sTook!;"
exit /b 0

:stopped
echo(
echo Stopped: %sStep% failed, so the steps after it did not run. Its own log is in logs, and this cycle's is
echo logs\%sName%-build_release-%sStamp%.log.
>> "%sLog%" echo Stopped %date% %time%: %sStep% failed; steps passed before it:!sSummary!
exit /b 1
