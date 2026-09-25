@echo off
rem tidyRepo.cmd
rem
rem Surveys the whole repository -- what is tracked that should not be, what is
rem large in the history, what is on disk that belongs nowhere -- and then fixes
rem it in one pass. What belongs is decided by homerPolicy.py, which reads this
rem project's own <App>_setup.iss and RepoFiles.txt, so there is no list in here
rem to maintain and nothing is hardcoded to one program.
rem
rem Running it does nothing: it prints the whole plan and stops. Run it again
rem with --do-it to carry that plan out.
rem
rem     tidyRepo
rem     tidyRepo --do-it
rem     tidyRepo --do-it --no-push
rem
rem Writes tidyRepo.log beside this script.
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
python "tidyRepo.py" %*
set exitCode=%errorlevel%
popd
endlocal & exit /b %exitCode%
