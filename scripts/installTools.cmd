@echo off
rem installTools.cmd -- put the Homer tools where every project can reach them.
rem
rem     installTools              copy to C:\bin
rem     installTools D:\utils     copy somewhere else
rem
rem WHY THIS EXISTS. tagRelease, homerTidy, checkHomerApp, gitPush and gitRelease
rem all act on the CURRENT DIRECTORY, so one copy on the PATH serves every
rem project. The catch is that an old copy on the PATH also serves every project:
rem a tagRelease from before source-only releases were supported will refuse to
rem release a project that has no installer script, and the error names a file
rem that was never supposed to exist.
rem
rem So this copies the kit's current tools over whatever is there. Run it after
rem updating the kit.
rem
rem It does NOT change your PATH. If the folder is not on it, add it once through
rem System Properties, Environment Variables.
rem
rem Writes installTools.log beside this script.
setlocal enabledelayedexpansion
set "log=%~dp0installTools.log"
set "target=%~1"
if "%target%"=="" set "target=C:\bin"

> "%log%" echo installTools started %date% %time%
>> "%log%" echo Source: %~dp0
>> "%log%" echo Target: %target%

if not exist "%target%" (
    mkdir "%target%" 2>nul
    if errorlevel 1 (
        echo Could not make %target%. Run this from an administrator prompt, or name another folder.
        echo COULD NOT CREATE TARGET>> "%log%"
        endlocal
        exit /b 1
    )
    echo Created %target%.
)

set "copied=0"
for %%f in (checkHomerApp.cmd checkHomerApp.py gitPush.cmd gitRelease.cmd homerTidy.cmd homerTidy.py sayTutorial.cmd sayTutorial.py tagRelease.cmd tagRelease.ps1) do (
    if exist "%~dp0%%f" (
        copy /y "%~dp0%%f" "%target%\%%f" >> "%log%" 2>&1
        if errorlevel 1 (
            echo %%f could not be copied. The log has why.
            echo COPY FAILED: %%f>> "%log%"
        ) else (
            set /a copied+=1
            echo COPIED: %%f>> "%log%"
        )
    )
)

echo Copied !copied! tools to %target%.
echo %PATH% | find /i "%target%" >nul
if errorlevel 1 (
    echo NOTE: %target% is not on your PATH, so the tools will only run from that folder.
    echo       Add it once through System Properties, Environment Variables.
    echo TARGET NOT ON PATH>> "%log%"
)
>> "%log%" echo installTools finished %date% %time%
endlocal & exit /b 0
