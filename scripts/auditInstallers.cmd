@echo off
rem auditInstallers.cmd: runs auditInstallers.py with the arguments given; see that script.
python "%~dp0auditInstallers.py" %*
exit /b %errorlevel%
