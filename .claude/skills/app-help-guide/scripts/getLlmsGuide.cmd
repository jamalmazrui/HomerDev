@echo off
rem getLlmsGuide.cmd -- runs getLlmsGuide.py, passing its arguments on.
rem   getLlmsGuide                 gathers and builds Expo, Hermes Agent and Kiro
rem   getLlmsGuide kiro /build     rebuilds one guide from what was gathered before
python "%~dp0getLlmsGuide.py" %*
exit /b %errorlevel%
