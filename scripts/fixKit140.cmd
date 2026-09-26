@echo off
rem fixKit140.cmd -- put back what kit 1.40.0 lost, so the shared classes compile.
rem Runs the Python beside it and passes every argument through.
python "%~dp0fixKit140.py" %*
