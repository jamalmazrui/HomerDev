@echo off
rem whoOpens.cmd -- name the program behind the "Select an app to open this file" prompt; see whoOpens.ps1.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0whoOpens.ps1" %*
exit /b %errorlevel%
