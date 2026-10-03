@echo off
rem relicense.cmd -- runs relicense.py with the arguments given.
python "%~dp0relicense.py" %*
exit /b %errorlevel%
