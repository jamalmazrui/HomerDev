@echo off
rem newHomerApp.cmd -- start a new Homer Tools app from the kit templates.
rem
rem   newHomerApp                  ask for the name, write into C:\<App>
rem   newHomerApp JobDo            write C:\JobDo
rem   newHomerApp JobDo D:\Work    write somewhere else
rem
rem It writes a complete starting project -- source, build, installer, lists,
rem acceptance checks and document starters -- with the app name filled in and
rem in the Homer encoding. Nothing already in the folder is overwritten.
rem
rem The work is in newHomerApp.py beside this script; its log is in logs.
setlocal
pushd "%~dp0"
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found on the PATH. Install it from python.org
    echo        or with: winget install Python.Python.3.12
    popd
    endlocal
    exit /b 1
)
python "newHomerApp.py" %*
set exitCode=%errorlevel%
popd
endlocal & exit /b %exitCode%
