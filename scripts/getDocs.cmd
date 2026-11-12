@echo off
rem getDocs.cmd -- fetches the documents in the kit's data\getDocs.inix into this folder's results\getDocs; passes its arguments on.
python "%~dp0getDocs.py" %*
exit /b %errorlevel%
