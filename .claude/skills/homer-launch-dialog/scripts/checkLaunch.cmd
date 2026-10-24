@echo off
rem checkLaunch.cmd -- runs checkLaunch.py with every argument passed on.
python "%~dp0checkLaunch.py" %*
exit /b %errorlevel%
