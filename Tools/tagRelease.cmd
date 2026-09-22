@echo off
rem ============================================================
rem  tagRelease.cmd  -  launcher for tagRelease.ps1.
rem
rem  Generic. It acts on the CURRENT DIRECTORY, never on its own
rem  location, so one copy in a tools folder on the PATH serves
rem  every project:
rem
rem      C:\bin\tagRelease.cmd
rem      C:\bin\tagRelease.ps1
rem
rem      cd C:\EdSharp
rem      tagRelease
rem
rem  or, without changing directory:
rem
rem      tagRelease -Path C:\EdSharp
rem
rem  A copy beside the project works the same way.
rem
rem  Invokes PowerShell with execution policy bypass for this single
rem  invocation only (it does not change the system policy), and
rem  forwards every argument. Each run writes its own log in the
rem  project's logs folder, logs\<App>-release-<date>-<time>.log --
rem  with the project rather than with the script, because the log is
rem  about that release.
rem
rem  Usage:
rem    tagRelease                      the normal command; no flags needed
rem    tagRelease -Path C:\EdSharp     act on another folder
rem    tagRelease -Version 5.1         set an explicit version
rem                                    (source-only projects; an app with an
rem                                    installer takes its version from the
rem                                    installer itself)
rem    tagRelease -NoCommit            do not commit anything
rem    tagRelease -SkipStaleCheck      publish even if the version looks released
rem ============================================================

setlocal

set "sScriptDir=%~dp0"
set "sPsScript=%sScriptDir%tagRelease.ps1"

if not exist "%sPsScript%" (
    echo ERROR: Cannot find tagRelease.ps1 next to tagRelease.cmd
    echo Expected at: %sPsScript%
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%sPsScript%" %*
exit /b %ERRORLEVEL%
