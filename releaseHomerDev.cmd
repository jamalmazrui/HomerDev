@echo off
rem releaseHomerDev.cmd -- the whole release, as one command.
rem
rem     releaseHomerDev "What changed."
rem     releaseHomerDev                    uses a default commit message
rem
rem It runs, in order, and stops at the first failure:
rem
rem   1. Tools\installTools    puts the kit's current tools on the PATH, so an
rem                            old tagRelease cannot refuse the release
rem   2. checkHomerDev         the environment, a clean build of all four
rem                            samples, the dependency rule, the tools on your
rem                            PATH, and every program driven through its keys
rem   3. Tools\gitPush         stage what the whitelist allows, commit, push
rem   4. Tools\gitRelease      tag and publish (the check has already run)
rem
rem Nothing here is a test you have to remember. If it finishes, the evidence
rem reports beside checkHomerDev and uiCheck say what was verified, what was not
rem checked, and what remains uncertain. Read the third list before announcing.
rem
rem Writes releaseHomerDev.log beside this script; each step writes its own too.
setlocal
set "log=%~dp0releaseHomerDev.log"
set "message=%~1"
if "%message%"=="" set "message=Release."

> "%log%" echo releaseHomerDev started %date% %time%
>> "%log%" echo Folder: %CD%
>> "%log%" echo Message: %message%

echo Step 1 of 4: putting the current tools on the PATH.
call "%~dp0Tools\installTools.cmd" >> "%log%" 2>&1
if errorlevel 1 (
    echo installTools failed. The log has why: %log%
    endlocal
    exit /b 1
)

echo Step 2 of 4: building everything from clean and driving the programs.
call "%~dp0checkHomerDev.cmd"
if errorlevel 1 (
    echo Something failed the check, so nothing was released.
    echo Read the newest evidence report in this folder, fix it, and run this again.
    echo CHECK FAILED>> "%log%"
    endlocal
    exit /b 1
)

echo Step 3 of 4: committing and pushing.
call "%~dp0Tools\gitPush.cmd" "%message%"
if errorlevel 1 (
    echo The push failed, so nothing was tagged.
    echo PUSH FAILED>> "%log%"
    endlocal
    exit /b 1
)

echo Step 4 of 4: tagging and publishing.
call "%~dp0Tools\gitRelease.cmd" --skip-check
set "exitCode=%errorlevel%"
>> "%log%" echo gitRelease exit code %exitCode%
>> "%log%" echo releaseHomerDev finished %date% %time%
if "%exitCode%"=="0" (
    echo Released. The evidence reports in this folder say what was checked.
) else (
    echo tagRelease failed. The log has why: %log%
)
endlocal & exit /b %exitCode%
