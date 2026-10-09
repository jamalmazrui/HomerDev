@echo off
rem testConversion.cmd -- runs testConversion.py, passing on its arguments.
python "%~dp0testConversion.py" %*
exit /b %errorlevel%
