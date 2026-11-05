@echo off
rem axeWindow.cmd: runs axeWindow.py with the arguments given; see that script.
python "%~dp0axeWindow.py" %*
exit /b %errorlevel%
