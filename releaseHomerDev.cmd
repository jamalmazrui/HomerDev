@echo off
rem releaseHomerDev.cmd -- the whole release, as one command.
rem
rem     releaseHomerDev "What changed."
rem     releaseHomerDev                    uses a default commit message
rem
rem It runs, in order, and stops at the first failure:
rem
rem   1. checkHomerDev         the environment, a clean build of all the
rem                            samples, the dependency rule and the tools on
rem                            your PATH (checkHomerDev --ui also drives them)
rem   2. scripts\push         stage what the whitelist allows, commit, push
rem   3. scripts\release      tag and publish
rem
rem -SKIPCHECK ONLY WHEN RELEASE TAKES IT (1.65.27). release.ps1 belongs to your separate release-script project and is
rem not in git. Kit 1.38.0 gave it -SkipCheck, but the copy in scripts can be one without it, and on 11 October
rem PowerShell refused the unknown parameter, so kit 1.65.26 was pushed and never tagged. release.ps1 is now asked
rem first: -SkipCheck is passed when it declares the parameter; otherwise release runs without it, which costs at
rem most a second run of the check. The log says which.
rem
rem Nothing here is a test you have to remember. If it finishes, the evidence
rem report in logs says what was verified, what was not checked, and what remains
rem uncertain. Read the third list before announcing.
rem
rem Writes logs\HomerDev-releaseHomerDev-<stamp>.log; each step writes its own too.
setlocal
if not exist "%~dp0logs" mkdir "%~dp0logs"
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "sStamp=%%i"
set "log=%~dp0logs\HomerDev-releaseHomerDev-%sStamp%.log"
set "message=%~1"
if "%message%"=="" set "message=Release."

> "%log%" echo releaseHomerDev started %date% %time%
>> "%log%" echo Folder: %CD%
>> "%log%" echo Message: %message%

echo Step 1 of 3: building everything from clean and checking it.
call "%~dp0checkHomerDev.cmd"
if errorlevel 1 (
    echo Something failed the check, so nothing was released.
    echo Read the newest evidence report in logs, fix it, and run this again.
    echo CHECK FAILED>> "%log%"
    endlocal
    exit /b 1
)

echo Step 2 of 3: committing and pushing.
call "%~dp0scripts\push.cmd" "%message%"
if errorlevel 1 (
    echo The push failed, so nothing was tagged.
    echo PUSH FAILED>> "%log%"
    endlocal
    exit /b 1
)

echo Step 3 of 3: tagging and publishing.
set "sSkip="
findstr /i /c:"$SkipCheck" "%~dp0scripts\release.ps1" >nul 2>&1 && set "sSkip=-SkipCheck"
if defined sSkip (>> "%log%" echo release.ps1 declares -SkipCheck, so it is passed) else (>> "%log%" echo release.ps1 has no -SkipCheck, so release runs without it)
call "%~dp0scripts\release.cmd" %sSkip%
set "exitCode=%errorlevel%"
>> "%log%" echo release exit code %exitCode%
>> "%log%" echo releaseHomerDev finished %date% %time%
if "%exitCode%"=="0" (
    echo Released. The evidence report in logs says what was checked.
) else (
    echo release failed. The log has why: %log%
)
endlocal & exit /b %exitCode%
