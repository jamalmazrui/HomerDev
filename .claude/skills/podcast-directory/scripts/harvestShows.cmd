@echo off
setlocal
where py >nul 2>&1 && ( py -3 "%~dp0harvestShows.py" %* ) || ( python "%~dp0harvestShows.py" %* )
endlocal
