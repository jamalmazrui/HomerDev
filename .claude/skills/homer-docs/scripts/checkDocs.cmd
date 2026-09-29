@echo off
rem checkDocs.cmd -- runs checkDocs.py, passing its arguments on.
python "%~dp0checkDocs.py" %*
exit /b %errorlevel%
