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
rem ONE CYCLE PER PROJECT AT A TIME (1.66.1, from an audit). Two cycles of the same project overlapped on
rem 11 October: an older cycle's release found an installer a newer, failed build had just written. Different projects
rem may still run side by side. The lock is a folder in %TEMP% named for the project, since making a folder succeeds
rem for only one process; a lock older than four hours is the trace of a window that was closed, and is cleared.
set "sLock=%TEMP%\Homer-%sName%-cycle.lock"
rem build_release unlock: YOU KNOW NOTHING IS RUNNING (12 October 2026). A lock the rules below cannot prove stale
rem refused every cycle until it was four hours old. Typed with unlock, the cycle clears it first and starts.
if /i "%~1"=="unlock" (
  if exist "!sLock!" rmdir /s /q "!sLock!" 2>nul
  >> "%sLog%" echo Unlock asked: !sLock! removed before the cycle
  echo The lock was cleared, as asked, and the cycle starts.
)
mkdir "!sLock!" 2>nul
rem A LOCK WHOSE CYCLE IS GONE IS CLEARED AT ONCE (12 October 2026). A cycle whose window was closed left its lock for
rem four hours, and every cycle of that project was refused meanwhile. The lock now records the process running the
rem cycle (pid.txt); when that process no longer exists, or the number now belongs to a process started after the lock
rem was made, the lock is stale whatever its age. A holder that is still alive proves nothing -- a cycle stopped with
rem Control+C leaves its Command Prompt running -- so it only keeps the refusal, which now names the holder's log, and
rem the four-hour rule still applies.
if errorlevel 1 (
  set "iAge=0"
  for /f %%a in ('powershell -NoProfile -Command "[int]((Get-Date)-(Get-Item -LiteralPath '!sLock!').CreationTime).TotalMinutes"') do set "iAge=%%a"
  set "sAlive=unknown"
  set "iHolder="
  if exist "!sLock!\pid.txt" set /p iHolder=<"!sLock!\pid.txt"
  if defined iHolder (
    for /f %%a in ('powershell -NoProfile -Command "$p = Get-Process -Id !iHolder! -ErrorAction SilentlyContinue; if ($p -and $p.StartTime -le (Get-Item -LiteralPath '!sLock!').CreationTime) { 'yes' } else { 'no' }"') do set "sAlive=%%a"
  )
  set "sHolderLog="
  if exist "!sLock!\holder.txt" set /p sHolderLog=<"!sLock!\holder.txt"
  set "bStale="
  if !iAge! geq 240 set "bStale=1"
  if "!sAlive!"=="no" set "bStale=1"
  rem A LOCK WITH NO HOLDER RECORD, 30 MINUTES OLD OR MORE, IS STALE (12 October 2026). The runner before 1.72.10
  rem recorded no process, and from 1.72.5 every one of its cycles ended in a syntax error at push, leaving its lock.
  rem No cycle that is still running takes that long, so such a lock no longer holds a project back for four hours.
  if not defined iHolder if !iAge! geq 30 set "bStale=1"
  if defined bStale (
    >> "%sLog%" echo Lock !sLock! was !iAge! minutes old, from a cycle no longer running ^(holder process !iHolder!, alive: !sAlive!^); cleared
    rmdir /s /q "!sLock!" 2>nul
    mkdir "!sLock!" 2>nul
  ) else (
    echo Another %sName% cycle started !iAge! minutes ago and is still running, so this one does not start.
    echo Its log: !sHolderLog!
    echo If that cycle's Command Prompt window is still open, look there: it may be waiting for
    echo you, for instance at a sign-in window. Closing that window ends the cycle, and the
    echo next build_release then starts at once. A lock older than four hours is cleared by itself.
    echo If you are sure no %sName% cycle is running, type: build_release unlock
    >> "%sLog%" echo Refused: another cycle holds !sLock!, made !iAge! minutes ago ^(holder process !iHolder!, alive: !sAlive!; !sHolderLog!^)
    exit /b 1
  )
)
> "!sLock!\holder.txt" echo %date% %time% %sLog%
rem The process running this cycle: the parent of the Command Prompt that for /f starts to run PowerShell.
set "iMine="
for /f %%p in ('powershell -NoProfile -Command "$c = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $PID); $b = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $c.ParentProcessId); $b.ParentProcessId"') do set "iMine=%%p"
if defined iMine > "!sLock!\pid.txt" echo !iMine!
>> "%sLog%" echo Lock: !sLock!, held by process !iMine!

set "sRelease=scripts\release.cmd"
rem EVERY RUNNER REPLACES ITSELF, AND ONLY AT ITS OWN END (1.65.32, from an audit). The kit's build overwrote every
rem sibling project's build_release.bat, including one running a cycle at that moment; Windows reads a running batch
rem file a piece at a time, so the running copy could execute garbage. Now the kit's build only creates a missing
rem runner, and each runner copies the kit's newest over itself on the line it exits by, which Windows reads whole
rem before running, so the bytes change only when no cycle is running them. The kit's own copy is its scripts copy.
set "sRunner="
if exist "releaseHomerDev.cmd" if exist "scripts\build_release.cmd" set "sRunner=%CD%\scripts\build_release.cmd"
rem THE DEVELOPMENT KIT FIRST (12 October 2026): the HomerDev variable points to the installed kit, which lags the kit
rem beside the projects until it is installed, so a fix to this runner reached no project until then.
if not defined sRunner if exist "..\HomerDev\scripts\build_release.cmd" for %%R in ("..\HomerDev\scripts\build_release.cmd") do set "sRunner=%%~fR"
if not defined sRunner if defined HomerDev if exist "%HomerDev%\scripts\build_release.cmd" set "sRunner=%HomerDev%\scripts\build_release.cmd"
>> "%sLog%" echo Settings: release=!sRelease! runner=!sRunner!
set "sSummary="

call :step build "build.cmd" || goto :stopped
call :step tidy "scripts\tidy.cmd" || goto :stopped
call :step push "scripts\push.cmd" || goto :stopped
call :step release "!sRelease!" || goto :stopped

echo(
set "sSummary=!sSummary:~0,-1!"
echo Built, tidied, pushed and released:!sSummary!.
>> "%sLog%" echo Finished %date% %time%: every step passed:!sSummary!
rmdir /s /q "!sLock!" 2>nul
rem The kit's own copy is replaced here, on the same line as the exit: Windows reads the whole line before running
rem it, so nothing of the old file is read after the copy (1.65.26). A project's copy is written by the kit's build.
if defined sRunner copy /y "!sRunner!" "build_release.bat" >nul & exit /b 0
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
rmdir /s /q "!sLock!" 2>nul
if defined sRunner copy /y "!sRunner!" "build_release.bat" >nul & exit /b 1
exit /b 1
