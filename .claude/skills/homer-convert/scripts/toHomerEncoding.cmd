@echo off
rem toHomerEncoding.cmd -- runs toHomerEncoding.py, passing its arguments on.
python "%~dp0toHomerEncoding.py" %*
exit /b %errorlevel%
