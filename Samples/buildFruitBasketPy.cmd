@echo off
rem ===================================================================
rem buildFruitBasketPyPy.cmd -- build FruitBasketPy.exe from FruitBasketPy.py and the Homer
rem Python package.
rem
rem This is the HomerDev TEMPLATE for a PYTHON app. newHomerApp.cmd
rem writes a copy of it with FruitBasketPy replaced by a real app name when it
rem is asked for a Python app.
rem
rem WHAT IT PRODUCES: one file, FruitBasketPy.exe, with Python, the Homer
rem package and every dependency inside it. Somebody who installs the
rem program needs no Python of their own. That is what makes a Python
rem program shippable on the same terms as a C# one, and it is how
rem urlCheck and helpFido are built.
rem
rem KIT: the Homer Python package is NOT copied into the app folder. It
rem is taken from the kit, which is looked for in this order, first hit
rem wins:
rem   1. %HomerDev%        the environment variable, when it is set
rem   2. C:\HomerDev        the usual place
rem   3. the current directory, for a folder that carries its own copy
rem
rem VERSION: version.txt is the single source of truth, exactly as in
rem the C# build. This script increments it on every build, stepping
rem over any number already released, which it learns from the
rem repository's own tags, and writes version.py from it so the running
rem program reports the same number. FruitBasketPy_setup.iss reads version.txt
rem directly.
rem
rem   buildFruitBasketPyPy.cmd          increments the version, then builds
rem   buildFruitBasketPyPy.cmd nobump   keeps the current number
rem
rem PYTHON: a virtual environment beside this script, so the machine's
rem own Python is left alone and two Homer apps cannot disagree about a
rem package version. It is created on the first build and reused after.
rem
rem Output in this folder: FruitBasketPy.exe, and the installer if Inno Setup is
rem present. Everything is logged to buildFruitBasketPyPy.log beside this script.
rem ===================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

set "app=FruitBasketPy"
set "log=%CD%\build%app%.log"
echo %app% build started %DATE% %TIME%> "%log%"
echo Script: %~f0>> "%log%"
echo Folder: %CD%>> "%log%"
echo Command line: %0 %*>> "%log%"
echo Build log: %log%

rem ---- the Homer Development Kit -------------------------------------
set "homerDev="
if defined HomerDev if exist "%HomerDev%\homer\lbc.py" set "homerDev=%HomerDev%"
if not defined homerDev if exist "C:\HomerDev\homer\lbc.py" set "homerDev=C:\HomerDev"
if not defined homerDev if exist "%CD%\homer\lbc.py" set "homerDev=%CD%"
if not defined homerDev (
  echo ERROR: the Homer Development Kit was not found.
  echo         Looked in %%HomerDev%%, C:\HomerDev, and this folder.
  echo ERROR: no kit found.>> "%log%"
  goto :failed
)
set "homerVer=unknown"
if exist "!homerDev!\version.txt" set /p homerVer=<"!homerDev!\version.txt"
echo Kit: !homerDev! version !homerVer!
echo Kit: !homerDev! version !homerVer!>> "%log%"

rem ---- component options ----------------------------------------------
rem EVERY PYTHON COMPONENT ANY HOMER APP HAS NEEDED IS LISTED HERE. The ones
rem used by MORE THAN ONE app are switched on, because that is the evidence
rem that the next app will want them too; the ones used by a single app are
rem left commented with the app named, so turning one on is one character.
rem Alphabetical, as every list in Homer code is.
rem
rem AI NOTE: to add a package, uncomment its line, or add a new one in the same
rem shape. pipPackages is what the virtual environment installs; nothing else
rem needs changing.
rem
rem On in the template, because more than one app uses each:
set "useDocs=1"
rem set "useInstaller=1"   rem the sample ships as source, not as an installed program
rem set "useScreenReaderScripts=1"   rem the sample has no scripts of its own
rem set "useVersionSteps=1"   rem a sample is not released, so its number never moves
set "pipPackages=pyinstaller wxpython"
rem
rem Off in the template, each used by one app so far.
rem set "pipPackages=!pipPackages! beautifulsoup4"   rem helpFido: reading a help page
rem set "pipPackages=!pipPackages! pillow"           rem urlCheck: images
rem set "pipPackages=!pipPackages! playwright"       rem helpFido: driving a browser
rem set "pipPackages=!pipPackages! pythonnet"        rem helpFido: WinForms from Python
rem set "pipPackages=!pipPackages! requests"         rem urlCheck: fetching a page

rem ---- version: version.txt is the single source of truth -----------
rem A MISSING version.txt IS MADE, NOT AN ERROR. Every build needs a number --
rem the program reports it, the installer carries it, the release tag is it --
rem so a folder without one gets 1.0.0 and carries on. Stopping here would
rem leave a manual step, which no Homer build does.
if not exist "version.txt" (
  > version.txt echo 1.0.0
  echo No version.txt here, so it was created holding 1.0.0.
  echo Created version.txt holding 1.0.0>> "%log%"
)
set "ver="
set /p ver=<version.txt
set "ver=!ver: =!"
if "!ver!"=="" (
  echo ERROR: version.txt is empty.
  echo ERROR: version.txt is empty.>> "%log%"
  goto :failed
)
if /i "%~1"=="nobump" goto :keepVersion
if not defined useVersionSteps goto :keepVersion
call :takeNextVersion
goto :haveVersion

:keepVersion
echo Version: !ver! ^(nobump: keeping the current number^)
echo Version: !ver! ^(nobump^)>> "%log%"

:haveVersion

rem ---- generate version.py from version.txt -------------------------
rem Generated output: do not edit it, and do not commit it.
> version.py echo # Generated by build%app%.cmd from version.txt.  Do not edit; do not commit.
>> version.py echo sVersion = "!ver!"

rem ---- Python --------------------------------------------------------
where python >nul 2>&1
if errorlevel 1 (
  echo Python was not found. Installing it.
  echo Python not on the PATH; installing with winget.>> "%log%"
  winget install --id Python.Python.3.12 --architecture x64 --scope machine ^
    --accept-source-agreements --accept-package-agreements --silent >> "%log%" 2>&1
  where python >nul 2>&1
  if errorlevel 1 (
    echo ERROR: Python is still not on the PATH. Sign out and back in, then run this again.
    echo ERROR: python not found after install.>> "%log%"
    goto :failed
  )
)
for /f "delims=" %%v in ('python --version 2^>^&1') do echo Python: %%v>> "%log%"

rem ---- the virtual environment ---------------------------------------
if exist ".venv\Scripts\python.exe" goto :haveVenv
echo Creating the build environment.
echo Creating .venv>> "%log%"
python -m venv .venv >> "%log%" 2>&1
if not exist ".venv\Scripts\python.exe" (
  echo ERROR: the virtual environment could not be created. See %log%.
  echo ERROR: venv creation failed.>> "%log%"
  goto :failed
)

:haveVenv
set "venvPy=%CD%\.venv\Scripts\python.exe"
echo Installing what the build needs.
"!venvPy!" -m pip install --upgrade pip >> "%log%" 2>&1
"!venvPy!" -m pip install --upgrade !pipPackages! >> "%log%" 2>&1
if errorlevel 1 (
  echo ERROR: the packages could not be installed. See %log%.
  echo ERROR: pip install failed.>> "%log%"
  goto :failed
)
"!venvPy!" -m pip list >> "%log%" 2>&1

rem ---- is the program still running? ---------------------------------
tasklist /fi "imagename eq %app%.exe" 2>nul | find /i "%app%.exe" >nul
if not errorlevel 1 (
  echo ERROR: %app%.exe is running. Close it and run this again.
  echo ERROR: %app%.exe is running.>> "%log%"
  goto :failed
)

rem ---- build one file -------------------------------------------------
rem --paths puts the kit's Python folder on the import path, so
rem "from homer import lbc" resolves to the kit rather than to a copy.
rem --windowed keeps a console from appearing behind the window; drop it
rem for a program that writes to the console.
set "icon="
if exist "%app%.ico" set "icon=--icon %app%.ico"
echo Building %app%.exe>> "%log%"
"!venvPy!" -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name %app% ^
  --paths "!homerDev!" ^
  --hidden-import homer ^
  --hidden-import homer.inix ^
  --hidden-import homer.lbc ^
  --hidden-import homer.log ^
  --hidden-import homer.paths ^
  --hidden-import homer.say ^
  --hidden-import homer.util ^
  --hidden-import homer.web ^
  !icon! ^
  %app%.py >> "%log%" 2>&1
if not exist "dist\%app%.exe" (
  echo(
  echo ERROR: the build failed. Details in %log%.
  echo ERROR: PyInstaller produced no exe.>> "%log%"
  goto :failed
)
copy /y "dist\%app%.exe" "%app%.exe" >nul
echo Built %app%.exe version !ver!>> "%log%"
echo(
echo Built %app%.exe version !ver!

rem ---- documentation ---------------------------------------------------
if not defined useDocs goto :docsDone
where pandoc >nul 2>&1
if errorlevel 1 (
  echo Pandoc was not found, so the .htm files were not rebuilt.>> "%log%"
) else (
  for %%m in (*.md) do (
    pandoc -f markdown -t html5 --standalone --metadata title="%%~nm" -o "%%~nm.htm" "%%m" >> "%log%" 2>&1
    if errorlevel 1 echo WARN: pandoc failed on %%m>> "%log%"
  )
  echo Documentation converted with pandoc.>> "%log%"
)
:docsDone

rem ---- screen reader scripts -----------------------------------------
if not defined useScreenReaderScripts goto :readersDone
if exist "jaws\*.js*" (
  powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Compress-Archive -Path 'jaws\*' -DestinationPath '%app%_JAWS.zip' -Force" >> "%log%" 2>&1
  echo Packed %app%_JAWS.zip>> "%log%"
)
if exist "addon\manifest.ini" (
  powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Compress-Archive -Path 'addon\*' -DestinationPath '%app%.nvda-addon' -Force" >> "%log%" 2>&1
  echo Packed %app%.nvda-addon>> "%log%"
)
:readersDone

rem ---- installer, if Inno Setup is present --------------------------
if not defined useInstaller goto :done
set "progFiles86=%ProgramFiles(x86)%"
set "progFiles=%ProgramFiles%"
set "iscc="
if exist "!progFiles86!\Inno Setup 6\ISCC.exe" set "iscc=!progFiles86!\Inno Setup 6\ISCC.exe"
if not defined iscc if exist "!progFiles!\Inno Setup 6\ISCC.exe" set "iscc=!progFiles!\Inno Setup 6\ISCC.exe"
if not defined iscc (
  echo Inno Setup was not found, so no installer was built.>> "%log%"
  echo(
  echo Inno Setup was not found. To produce %app%_setup.exe, open
  echo %app%_setup.iss in Inno Setup and click Compile.
  goto :done
)
echo Inno Setup: !iscc!>> "%log%"
"!iscc!" "%app%_setup.iss" >> "%log%" 2>&1
if errorlevel 1 (
  echo ERROR: the installer build failed. See %log%.
  echo ERROR: the installer build failed.>> "%log%"
  goto :failed
)
echo Built %app%_setup.exe version !ver!>> "%log%"
echo Built %app%_setup.exe version !ver!

:done
echo Build succeeded %DATE% %TIME%>> "%log%"
echo(
echo To publish: commit, then run tagRelease. It reads the version from
echo the version resource of %app%_setup.exe and tags v!ver!.
endlocal
exit /b 0

:failed
echo Build FAILED %DATE% %TIME%>> "%log%"
endlocal
exit /b 1

:takeNextVersion
rem -------------------------------------------------------------------
rem Take the next UNUSED version. The last dotted part of !ver! is
rem incremented, and any number that already carries a release tag on the
rem origin remote is stepped over, so a version.txt that has fallen behind
rem the repository cannot mint a number that is already spent.
rem
rem One "git ls-remote" is the only network call this step makes. If it
rem fails, the plain increment is used and tagRelease remains the check it
rem has always been, so a machine with no network still builds.
rem -------------------------------------------------------------------
set "verOld=!ver!"
set "sTagFile=%TEMP%\%app%_tags.txt"
del "!sTagFile!" >nul 2>&1
git ls-remote --tags origin "v*" > "!sTagFile!" 2>> "%log%"
if errorlevel 1 echo WARN: the released tags could not be read, so the next number is taken blindly.>> "%log%"
if errorlevel 1 del "!sTagFile!" >nul 2>&1

:nextCandidate
call :incrementVersion
if not defined new goto :eof
if not exist "!sTagFile!" goto :haveNextVersion
findstr /e /c:"refs/tags/v!ver!" "!sTagFile!" >nul 2>&1
if errorlevel 1 goto :haveNextVersion
echo Version v!ver! is already released; stepping over it.
echo Version v!ver! is already released; stepping over it.>> "%log%"
goto :nextCandidate

:haveNextVersion
del "!sTagFile!" >nul 2>&1
> version.txt echo !ver!
echo Version: !verOld! -^> !ver!
echo Version: !verOld! -^> !ver!>> "%log%"
goto :eof

:incrementVersion
rem -------------------------------------------------------------------
rem Increment the last dotted part of !ver!. Nothing is written here, so the
rem caller may call this repeatedly while stepping over spent numbers.
rem -------------------------------------------------------------------
set "p1=" & set "p2=" & set "p3=" & set "p4="
set "new="
for /f "tokens=1-4 delims=." %%a in ("!ver!") do (
  set "p1=%%a" & set "p2=%%b" & set "p3=%%c" & set "p4=%%d"
)
if defined p4 (
  set /a p4=p4+1
  set "new=!p1!.!p2!.!p3!.!p4!"
) else if defined p3 (
  set /a p3=p3+1
  set "new=!p1!.!p2!.!p3!"
) else if defined p2 (
  set "new=!p1!.!p2!.1"
) else (
  set "new=!p1!.0.1"
)
if not defined new (
  echo ERROR: could not work out the next version from "!ver!".
  echo ERROR: could not work out the next version from "!ver!".>> "%log%"
  goto :eof
)
set "ver=!new!"
goto :eof
