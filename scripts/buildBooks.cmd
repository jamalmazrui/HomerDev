@echo off
rem buildBooks.cmd -- builds and audits an EPUB for every book in configs\books.inix, or those named.
rem Part of the HomerDev kit's book tools; every argument goes to buildBooks.py. Run it from the project folder as
rem scripts\buildBooks, or from inside scripts.
rem THE CODE COMES FROM THE KIT (8 October 2026): before running, the kit's current book tools are copied into this
rem project's scripts folder, as an app's build copies its kitTools, so a fix made once in the kit reaches every book
rem project. The kit is found as every kit script finds it: the HomerDev variable, then C:\HomerDev, then HomerDev at
rem the top of another drive. Without the kit, the copies already here run. Each copy is logged.
setlocal
set "sHere=%~dp0"
pushd "%sHere%.."
set "sProject=%CD%"
popd
for %%I in ("%sProject%") do set "sName=%%~nxI"
if not exist "%sProject%\logs" mkdir "%sProject%\logs"
set "sSetupLog=%sProject%\logs\buildBooks-setup.log"
echo %date% %time% buildBooks.cmd started with arguments: %* >> "%sSetupLog%"
set "sKit="
if defined HomerDev if exist "%HomerDev%\scripts\buildBooks.py" set "sKit=%HomerDev%"
if not defined sKit if exist "C:\HomerDev\scripts\buildBooks.py" set "sKit=C:\HomerDev"
for %%D in (D E F G H I J K L M N O P Q R S T U V W X Y Z) do if not defined sKit if exist "%%D:\HomerDev\scripts\buildBooks.py" set "sKit=%%D:\HomerDev"
if not defined sKit goto noKit
if /i "%sKit%\scripts\"=="%sHere%" goto noKit
for %%F in (buildBooks.py kdpBooks.py kdpSubmit.py kdpUpdate.py testKdpUpdate.py) do copy /y "%sKit%\scripts\%%F" "%sHere%%%F" >nul 2>&1 && echo %date% %time% copied %%F from %sKit%\scripts >> "%sSetupLog%"
rem THE WRAPPERS TOO, NEVER ITSELF (9 October 2026): only the .py files were refreshed, so a change to the kit's
rem kdpUpdate.cmd (building first) never reached the book project, and a book was refused as stale. Each wrapper
rem refreshes the others; a running batch file is never overwritten, since cmd reads it as it goes.
for %%F in (buildBooks.cmd kdpBooks.cmd kdpSubmit.cmd kdpUpdate.cmd) do if /i not "%%F"=="%~nx0" if exist "%sKit%\scripts\%%F" copy /y "%sKit%\scripts\%%F" "%sHere%%%F" >nul 2>&1 && echo %date% %time% copied %%F from %sKit%\scripts >> "%sSetupLog%"
goto haveTools
:noKit
echo %date% %time% the HomerDev kit was not found, or this is the kit; the book tools here run as they are >> "%sSetupLog%"
:haveTools
python --version >nul 2>&1
if errorlevel 1 goto installPython
goto havePython
:installPython
echo Python was not found. Installing Python 3.12 with winget; details go to logs\buildBooks-setup.log.
winget install --id Python.Python.3.12 --exact --silent --accept-package-agreements --accept-source-agreements >> "%sSetupLog%" 2>&1
set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts"
python --version >nul 2>&1
if errorlevel 1 goto noPython
:havePython
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set "sPython=%%v"
echo %date% %time% Python %sPython% >> "%sSetupLog%"
set "sErrors=%sProject%\logs\%sName%-buildBooks-errors.txt"
python "%sHere%buildBooks.py" %* 2> "%sErrors%"
rem The exit code is read with "if errorlevel N", from the highest down, in one statement: a variable named ERRORLEVEL
rem can hide the real code from %%ERRORLEVEL%%, and in a .cmd file a successful SET resets the error level to 0.
if errorlevel 6 (set "iCode=6") else if errorlevel 5 (set "iCode=5") else if errorlevel 4 (set "iCode=4") else if errorlevel 3 (set "iCode=3") else if errorlevel 2 (set "iCode=2") else if errorlevel 1 (set "iCode=1") else (set "iCode=0")
for %%F in ("%sErrors%") do if %%~zF equ 0 del "%sErrors%"
if exist "%sErrors%" echo Python reported an error before or outside the script's own log; it is saved in logs\%sName%-buildBooks-errors.txt.
echo %date% %time% buildBooks.py ended with exit code %iCode% >> "%sSetupLog%"
exit /b %iCode%
:noPython
echo Python is still not available. If Windows opened the Store, turn off the python App Execution Alias in Settings, then run this again.
exit /b 2
