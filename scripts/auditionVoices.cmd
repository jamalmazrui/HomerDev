@echo off
rem auditionVoices.cmd -- hear candidate screen reader voices for the tutorials, side by side (HomerDev 1.237.0).
rem
rem   auditionVoices          every candidate, one mp3 each and all of them joined, in results\voiceAudition
rem
rem An occasional script, not part of the build: it fetches Kokoro v1.0 and Phonon's ptts once, into the voices
rem folder buildTutorials uses, and renders the same short exchange with each reader. The log is
rem logs\HomerDev-auditionVoices-yyyyMMdd-HHmmss.log. auditionVoices.ps1 says why and how.
setlocal
set "sHere=%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%sHere%auditionVoices.ps1" %*
set iResult=%ERRORLEVEL%
endlocal & exit /b %iResult%
