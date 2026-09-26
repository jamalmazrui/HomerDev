@echo off
setlocal EnableExtensions
rem create_APP_Repo.cmd -- thin wrapper that runs the PowerShell worker and
rem captures everything to create_APP_Repo.log. PowerShell does the git and gh
rem work, because invoking gh from a batch file falls into a batch trap when gh
rem is installed as a .cmd shim: without "call", control transfers to the shim
rem and never returns, ending the script silently.
rem
rem ONE-TIME bootstrap: turns this folder into a git repository, creates
rem https://github.com/JamalMazrui/_APP_, and pushes the first commit. After
rem this, publishing a release is tagRelease's job.
rem
rem This is a MAINTAINER script. Name it in .gitignore so it stays out of the
rem distribution, the same treatment as tagRelease.
rem
rem Usage:
rem   create_APP_Repo.cmd            create the repo and push
rem   create_APP_Repo.cmd -DryRun    report what would happen, changing
rem                                  nothing. Worth running first.
rem
rem Requirements: git and gh on the PATH, gh authenticated (gh auth login),
rem PowerShell 5.1 or later.

if not defined sLogging (
    set "sLogging=1"
    cmd /d /c ""%~f0"" %* > "%~dp0create_APP_Repo.log" 2>&1
    type "%~dp0create_APP_Repo.log"
    exit /b
)

cd /d "%~dp0"
if not exist "%~dp0create_APP_Repo.ps1" (
    echo ERROR: create_APP_Repo.ps1 was not found next to this script.
    exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0create_APP_Repo.ps1" %*
exit /b %errorlevel%
