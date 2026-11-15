@echo off
rem harvestQueue.cmd -- runs harvestQueue.py, which gathers the help guides named in a collection's data\addGuides.inix.
rem Passes its arguments on: the collection's folder, or none for the current folder.
python "%~dp0harvestQueue.py" %*
exit /b %errorlevel%
