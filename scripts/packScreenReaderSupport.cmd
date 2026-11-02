@echo off
rem packScreenReaderSupport.cmd -- forwards its arguments to packScreenReaderSupport.ps1 beside it.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0packScreenReaderSupport.ps1" %*
exit /b %ERRORLEVEL%
