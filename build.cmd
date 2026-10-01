@echo off
rem build.cmd -- build the Homer Development Kit.
rem
rem The kit has no executable, so building it means converting every .md to a
rem matching .htm with pandoc (fetching pandoc with winget if it is missing),
rem then checking the kit over: every component present, every text file in the
rem Homer encoding, every template still carrying its _APP_ token, and no
rem zero-byte file anywhere.
rem
rem   build          convert the documents and check the kit
rem   build check    check only, convert nothing
rem
rem The work is in build.py beside this script, which writes a detailed
rem build.log there. This wrapper exists so nobody has to type the
rem Python invocation, in the same way a .ps1 always ships with a .cmd.
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
python "build.py" %*
set exitCode=%errorlevel%
popd
endlocal & exit /b %exitCode%
