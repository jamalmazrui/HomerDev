@echo off
rem testMacro.cmd: runs testMacro.py with the arguments given; see that script.
python "%~dp0testMacro.py" %*
exit /b %errorlevel%
