@echo off
rem axeScan.cmd: runs axeScan.py with the arguments given; see that script.
python "%~dp0axeScan.py" %*
exit /b %errorlevel%
