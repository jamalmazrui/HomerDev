@echo off
rem kdpUpdate.cmd -- sends each book's audited EPUB and answers to its existing KDP title.
rem Part of the HomerDev kit's book tools; every argument goes to kdpUpdate.py. Run it from the project folder as
rem scripts\kdpUpdate, or from inside scripts.
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
set "sSetupLog=%sProject%\logs\kdpUpdate-setup.log"
echo %date% %time% kdpUpdate.cmd started with arguments: %* >> "%sSetupLog%"
set "sKit="
if defined HomerDev if exist "%HomerDev%\scripts\buildBooks.py" set "sKit=%HomerDev%"
if not defined sKit if exist "C:\HomerDev\scripts\buildBooks.py" set "sKit=C:\HomerDev"
for %%D in (D E F G H I J K L M N O P Q R S T U V W X Y Z) do if not defined sKit if exist "%%D:\HomerDev\scripts\buildBooks.py" set "sKit=%%D:\HomerDev"
if not defined sKit goto noKit
if /i "%sKit%\scripts\"=="%sHere%" goto noKit
for %%F in (buildBooks.py kdpBooks.py kdpSubmit.py kdpUpdate.py testKdpUpdate.py) do copy /y "%sKit%\scripts\%%F" "%sHere%%%F" >nul 2>&1 && echo %date% %time% copied %%F from %sKit%\scripts >> "%sSetupLog%"
goto haveTools
:noKit
echo %date% %time% the HomerDev kit was not found, or this is the kit; the book tools here run as they are >> "%sSetupLog%"
:haveTools
python --version >nul 2>&1
if errorlevel 1 goto installPython
goto havePython
:installPython
echo Python was not found. Installing Python 3.12 with winget; details go to logs\kdpUpdate-setup.log.
winget install --id Python.Python.3.12 --exact --silent --accept-package-agreements --accept-source-agreements >> "%sSetupLog%" 2>&1
set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts"
python --version >nul 2>&1
if errorlevel 1 goto noPython
:havePython
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set "sPython=%%v"
echo %date% %time% Python %sPython% >> "%sSetupLog%"
python -c "import playwright" >nul 2>&1
if not errorlevel 1 goto havePlaywright
echo Installing the Playwright package with pip; details go to logs\kdpUpdate-setup.log.
python -m pip install --quiet --upgrade "playwright>=1.47" >> "%sSetupLog%" 2>&1
python -c "import playwright" >nul 2>&1
if errorlevel 1 goto noPlaywright
:havePlaywright
rem ONE COMMAND (9 October 2026): the books that changed are built first -- buildBooks keeps every book whose sources,
rem data and templates are unchanged since its last build -- and kdpUpdate then opens on KDP only the books that changed
rem since their last submission. --no-build skips the build.
echo %* | find /i "--no-build" >nul
if not errorlevel 1 goto afterBuild
echo Building any book that changed since its last build.
python "%sHere%buildBooks.py"
set "iBuild=%errorlevel%"
echo %date% %time% buildBooks.py ended with exit code %iBuild% >> "%sSetupLog%"
:afterBuild
set "sErrors=%sProject%\logs\%sName%-kdpUpdate-errors.txt"
python "%sHere%kdpUpdate.py" %* 2> "%sErrors%"
rem The exit code is read with "if errorlevel N", from the highest down, in one statement: a variable named ERRORLEVEL
rem can hide the real code from %%ERRORLEVEL%%, and in a .cmd file a successful SET resets the error level to 0.
if errorlevel 6 (set "iCode=6") else if errorlevel 5 (set "iCode=5") else if errorlevel 4 (set "iCode=4") else if errorlevel 3 (set "iCode=3") else if errorlevel 2 (set "iCode=2") else if errorlevel 1 (set "iCode=1") else (set "iCode=0")
for %%F in ("%sErrors%") do if %%~zF equ 0 del "%sErrors%"
if exist "%sErrors%" echo Python reported an error before or outside the script's own log; it is saved in logs\%sName%-kdpUpdate-errors.txt.
echo %date% %time% kdpUpdate.py ended with exit code %iCode% >> "%sSetupLog%"
exit /b %iCode%
:noPython
echo Python is still not available. If Windows opened the Store, turn off the python App Execution Alias in Settings, then run this again.
exit /b 2
:noPlaywright
echo The Playwright package could not be installed. See logs\kdpUpdate-setup.log.
exit /b 2
