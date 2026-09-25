@echo off
rem gitRelease.cmd -- check, then tag and publish a release of this project.
rem
rem     gitRelease          check, tag, publish
rem     gitRelease --skip-check   tag and publish without checking first
rem
rem THE CHECK COMES FIRST, and that is the only difference between this and
rem calling tagRelease by hand. A release is the one moment where a fault costs
rem somebody else time rather than you, so the evidence is gathered before the
rem tag rather than after it. checkHomerApp exits 1 when something failed, and
rem this stops there.
rem
rem tagRelease reads version.txt, tags the commit, and publishes the installer
rem as a release asset when the project has one. A source-only project releases
rem from version.txt with no asset.
rem
rem Writes gitRelease.log beside this script.
setlocal
set "log=%~dp0gitRelease.log"
> "%log%" echo gitRelease started %date% %time%
>> "%log%" echo Folder: %CD%

if /i "%~1"=="--skip-check" goto :tag

rem Releasing the kit itself? Its own check is the thorough one.
if exist "%CD%\checkHomerDev.cmd" (
    echo Checking before releasing...
    call "%CD%\checkHomerDev.cmd" >> "%log%" 2>&1
    if errorlevel 1 (
        echo Something failed the check, so nothing was released.
        echo CHECK FAILED>> "%log%"
        endlocal
        exit /b 1
    )
    echo The check passed.
    goto :tag
)

if exist "%~dp0checkHomerApp.cmd" (
    echo Checking before releasing...
    call "%~dp0checkHomerApp.cmd" --build >> "%log%" 2>&1
    if errorlevel 1 (
        echo Something failed the check, so nothing was released.
        echo Read the newest evidence report beside checkHomerApp, then fix and try again.
        echo CHECK FAILED>> "%log%"
        endlocal
        exit /b 1
    )
    echo The check passed.
)

:tag
if exist "%~dp0tagRelease.cmd" (
    call "%~dp0tagRelease.cmd" %*
) else (
    tagRelease %*
)
set "exitCode=%errorlevel%"
>> "%log%" echo tagRelease exit code %exitCode%
>> "%log%" echo gitRelease finished %date% %time%
endlocal & exit /b %exitCode%
