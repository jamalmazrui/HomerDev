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
rem UNLOCK DOES NOT CLEAR A CYCLE THAT IS RUNNING (kit 1.88.5). On 22 October a FileDir cycle speaking its tutorials
rem for over an hour looked stuck, a second cycle started beside it, and when the second ended it replaced
rem build_release.bat under the first, which then ran its steps again from the middle of the new file. So unlock
rem now clears only a lock whose holder is gone; for a holder that is alive and older than the lock it says so, and
rem names what that cycle is doing. "build_release unlock force" clears it all the same.
if /i "%~1"=="unlock" (
  set "sUnlockAlive=no"
  set "iUnlockHolder="
  if exist "!sLock!\pid.txt" set /p iUnlockHolder=<"!sLock!\pid.txt"
  if defined iUnlockHolder for /f %%a in ('powershell -NoProfile -Command "$p = Get-Process -Id !iUnlockHolder! -ErrorAction SilentlyContinue; if ($p -and $p.StartTime -le (Get-Item -LiteralPath '!sLock!').CreationTime) { 'yes' } else { 'no' }"') do set "sUnlockAlive=%%a"
  if /i "!sUnlockAlive!"=="yes" if /i not "%~2"=="force" (
    set "sUnlockLog="
    if exist "!sLock!\holder.txt" for /f "usebackq tokens=3*" %%a in ("!sLock!\holder.txt") do set "sUnlockLog=%%b"
    echo A %sName% cycle is still running ^(process !iUnlockHolder!^), so the lock stays.
    if defined sUnlockLog for /f "usebackq delims=" %%l in (`powershell -NoProfile -Command "Get-Content -LiteralPath '!sUnlockLog!' -Tail 1 -ErrorAction SilentlyContinue"`) do echo Its latest line: %%l
    echo A long step, such as speaking tutorials, can run an hour. To clear it regardless: build_release unlock force
    >> "%sLog%" echo Unlock refused: the holder ^(process !iUnlockHolder!^) is still running
    exit /b 1
  )
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
    if defined sHolderLog for /f "tokens=3*" %%a in ("!sHolderLog!") do for /f "usebackq delims=" %%l in (`powershell -NoProfile -Command "Get-Content -LiteralPath '%%b' -Tail 1 -ErrorAction SilentlyContinue"`) do echo Its latest line: %%l
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
rem THE KIT'S RELEASE SKIPS A SECOND CHECK (12 October 2026), as releaseHomerDev does: push's gate has just run
rem checkHomerDev, and release.ps1's own check is the app check, not the kit's. Passed only when release.ps1 declares
rem -SkipCheck; a copy without it runs as it is.
set "sReleaseArgs="
if exist "releaseHomerDev.cmd" findstr /i /c:"$SkipCheck" "scripts\release.ps1" >nul 2>&1 && set "sReleaseArgs=-SkipCheck"
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
>> "%sLog%" echo Settings: release=!sRelease! !sReleaseArgs! runner=!sRunner!
set "sSummary="

call :step build "build.cmd" || goto :stopped
call :step tidy "scripts\tidy.cmd" || goto :stopped
rem PUSH AND RELEASE VERIFY (14 October 2026, from an audit by another AI). Build and tidy may trust a file's
rem remembered hash while its size and time are unchanged, which keeps them quick; the checks before anything goes
rem public read every file again, so a file changed without changing its size or time cannot pass on its old hash.
set "HomerVerify=1"
>> "%sLog%" echo Settings: HomerVerify=1 for push and release, so their checks read every file again
call :step push "scripts\push.cmd" || goto :stopped
call :step release "!sRelease!" !sReleaseArgs! || goto :stopped

echo(
set "sSummary=!sSummary:~0,-1!"
echo Built, tidied, pushed and released:!sSummary!.
>> "%sLog%" echo Finished %date% %time%: every step passed:!sSummary!
rem THE RUNNER IS REPLACED ONLY BY THE CYCLE THAT HOLDS THE LOCK (kit 1.88.5): replacing it under another cycle of
rem this project makes that cycle read the new file from the middle.
set "bOwnLock="
if exist "!sLock!\pid.txt" (set /p iOwner=<"!sLock!\pid.txt") else (set "iOwner=")
if "!iOwner!"=="!iMine!" set "bOwnLock=1"
if not exist "!sLock!" set "bOwnLock="
rmdir /s /q "!sLock!" 2>nul
rem The kit's own copy is replaced here, on the same line as the exit: Windows reads the whole line before running
rem it, so nothing of the old file is read after the copy (1.65.26). A project's copy is written by the kit's build.
if defined sRunner if defined bOwnLock copy /y "!sRunner!" "build_release.bat" >nul & exit /b 0
exit /b 0

:step
rem %1 the step's name, %2 the script it runs, %3 an argument for it (the kit's release: -SkipCheck).
set "sStep=%~1"
if not exist "%~2" (
  echo %~1: %~2 is not in this project, so the cycle stops here.
  >> "%sLog%" echo %~1: %~2 not found
  exit /b 1
)
rem THE STEP'S TIME, MEASURED BY POWERSHELL ITSELF (kit 1.88.2). The epoch seconds this took,
rem subtracted in cmd, came out -33s and then -36s for steps of fifty and eighty minutes, the same
rem for every step of a cycle, so the values were plainly not being renewed -- and nothing showed
rem why. Now the start is a full timestamp, PowerShell computes the seconds since it, and both go
rem in this log, so a wrong time can be traced.
set "sCycleStepStart="
for /f "delims=" %%t in ('powershell -NoProfile -Command "(Get-Date).ToString('o')"') do set "sCycleStepStart=%%t"
>> "%sLog%" echo %~1: start stamp [!sCycleStepStart!]
>> "%sLog%" echo %~1: started %time%, running %~2
echo %~1 ...
call "%~2" %~3
set "iCode=!errorlevel!"
set "iSeconds="
if defined sCycleStepStart for /f %%t in ('powershell -NoProfile -Command "[int]((Get-Date) - [DateTime]::Parse('!sCycleStepStart!')).TotalSeconds"') do set "iSeconds=%%t"
>> "%sLog%" echo %~1: seconds measured [!iSeconds!]
if defined iSeconds (
  set /a "iMin=iSeconds/60, iSec=iSeconds %% 60"
  if !iMin! gtr 0 (set "sTook=!iMin!m !iSec!s") else (set "sTook=!iSec!s")
) else (
  set "sTook=an unmeasured time"
)
>> "%sLog%" echo %~1: exit code !iCode!, !sTook!
if not "!iCode!"=="0" exit /b !iCode!
set "sSummary=!sSummary! %~1 !sTook!;"
exit /b 0

:stopped
echo(
echo Stopped: %sStep% failed, so the steps after it did not run. Its own log is in logs, and this cycle's is
echo logs\%sName%-build_release-%sStamp%.log.
>> "%sLog%" echo Stopped %date% %time%: %sStep% failed; steps passed before it:!sSummary!
rem THE RUNNER IS REPLACED ONLY BY THE CYCLE THAT HOLDS THE LOCK (kit 1.88.5): replacing it under another cycle of
rem this project makes that cycle read the new file from the middle.
set "bOwnLock="
if exist "!sLock!\pid.txt" (set /p iOwner=<"!sLock!\pid.txt") else (set "iOwner=")
if "!iOwner!"=="!iMine!" set "bOwnLock=1"
if not exist "!sLock!" set "bOwnLock="
if defined bOwnLock rmdir /s /q "!sLock!" 2>nul
if defined sRunner if defined bOwnLock copy /y "!sRunner!" "build_release.bat" >nul & exit /b 1
exit /b 1
