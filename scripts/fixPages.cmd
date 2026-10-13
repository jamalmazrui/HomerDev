@echo off
rem fixPages.cmd -- the kit's page finisher for a collection; arguments go to fixPages.py.
python "%~dp0fixPages.py" %*
exit /b %errorlevel%
