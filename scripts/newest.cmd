@echo off
rem newest.cmd -- find every copy of a shared tool and print the newest one's
rem path, at or above a minimum version when one is given. Forwards every
rem argument to newest.ps1, which says how it searches. Part of the HomerDev kit.
rem
rem     newest pandoc                  the newest Pandoc, with the search shown
rem     newest pandoc -Minimum 3.1     the newest at 3.1 or later
rem     newest pandoc -Log build.log   the search appended to a log instead
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0newest.ps1" %*
set exitCode=%errorlevel%
endlocal & exit /b %exitCode%
