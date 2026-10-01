@echo off
rem renameBuild.cmd -- runs renameBuild.py with the arguments given.
python "%~dp0renameBuild.py" %*
exit /b %errorlevel%
