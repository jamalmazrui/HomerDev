@echo off
rem checkTypes.cmd: runs checkTypes.py with the arguments given; see that script.
python "%~dp0checkTypes.py" %*
exit /b %errorlevel%
