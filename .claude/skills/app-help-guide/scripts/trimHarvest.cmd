@echo off
rem trimHarvest.cmd -- trims harvest archives for upload: the named harvests, or every harvest when none is named.
rem Run it in a guides collection (C:\AppHelpGuides). Passes its arguments on to harvestQueue.py --trim.
python "%~dp0harvestQueue.py" "%CD%" --trim %*
exit /b %errorlevel%
