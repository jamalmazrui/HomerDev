@echo off
rem summarizeLogs.cmd -- runs summarizeLogs.py, passing its arguments on.
python "%~dp0summarizeLogs.py" %*
exit /b %errorlevel%
