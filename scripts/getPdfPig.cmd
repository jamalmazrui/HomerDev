@echo off
rem getPdfPig.cmd -- runs getPdfPig.ps1 beside it, passing every argument on.
rem     getPdfPig -App <ProgramName>
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0getPdfPig.ps1" %*
exit /b %errorlevel%
