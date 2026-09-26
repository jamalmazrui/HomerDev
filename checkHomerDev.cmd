@echo off
rem checkHomerDev.cmd -- prove the kit still builds, by building with it.
rem
rem Three releases in a row shipped a fault no check could see, because every
rem check read files and none compiled anything: a class name that collided, a
rem missing version.txt, a module that needed another module. A compiler is the
rem only instrument that answers "does this still work", so this runs one, three
rem times, from a clean start.
rem
rem     checkHomerDev             audit, clean, build all three samples, report
rem     checkHomerDev --deep      also delete the Python virtual environment, so
rem                               the next build proves it can build that too
rem     checkHomerDev --no-clean  build over what is there (fast, weaker)
rem
rem Run it after changing anything in CSharp or homer, and before tagRelease.
rem
rem Writes evidence-kit-<yyyymmdd-hhmmss>.md and checkHomerDev.log beside this
rem script. Exit code 0 when nothing failed, 1 when something did.
setlocal
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found on the PATH. Install it from python.org
    echo        or with: winget install Python.Python.3.12
    endlocal
    exit /b 1
)
python "%~dp0checkHomerDev.py" %*
set exitCode=%errorlevel%
endlocal & exit /b %exitCode%
