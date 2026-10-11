@echo off
setlocal EnableDelayedExpansion
rem build_release -- the Homer development cycle for the project in the current folder: build, tidy, push
rem and release, in that order, stopping at the first step that fails, so nothing broken is pushed or released.
rem
rem THE KIT'S ONE COPY (1.65.25). Each project had its own build_release.bat, written by hand, and copies drift as
rem the installers did. The kit's build now writes this file as build_release.bat at the top of every project beside
rem the kit, and of the kit itself; it acts on the current folder, so the same file serves them all.
rem
rem FOUR SCRIPTS, GATES INSIDE (1.65.30). The cycle is build, tidy, push and release, and nothing else; every audit gate
rem runs inside one of them. push runs the project's check before it stages anything, so a failing check is never
rem pushed, and release runs it again before it tags. 1.65.25 to 1.65.29 ran the check as a fifth step here.
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

rem The project's own steps: its build.cmd, and the kit's tidy, push and release in its scripts folder.
rem ONE CHECK, ONE PUSH (1.65.28). For the kit, release was releaseHomerDev, which runs checkHomerDev and push again
rem after this cycle had just run both: on 11 October each ran twice. The cycle now calls release directly, as it does
rem for every project; releaseHomerDev stays the one command for releasing the kit by hand.
set "sRelease=scripts\release.cmd"
>> "%sLog%" echo Settings: release=!sRelease!
set "sSummary="

call :step build "build.cmd" || goto :stopped
call :step tidy "scripts\tidy.cmd" || goto :stopped
call :step push "scripts\push.cmd" || goto :stopped
call :step release "!sRelease!" || goto :stopped

echo(
set "sSummary=!sSummary:~0,-1!"
echo Built, tidied, pushed and released:!sSummary!.
>> "%sLog%" echo Finished %date% %time%: every step passed:!sSummary!
rem The kit's own copy is replaced here, on the same line as the exit: Windows reads the whole line before running
rem it, so nothing of the old file is read after the copy (1.65.26). A project's copy is written by the kit's build.
if exist "releaseHomerDev.cmd" if exist "scripts\build_release.cmd" copy /y "scripts\build_release.cmd" "build_release.bat" >nul & exit /b 0
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
