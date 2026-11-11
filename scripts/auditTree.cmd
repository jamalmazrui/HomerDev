@echo off
rem auditTree.cmd -- runs auditTree.py, which checks every Homer project against help\HomerTree.md and changes nothing.
python "%~dp0auditTree.py" %*
exit /b %errorlevel%
