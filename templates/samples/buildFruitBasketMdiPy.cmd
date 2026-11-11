@echo off
rem ===================================================================
rem buildFruitBasketMdiPyPy.cmd -- build FruitBasketMdiPy.exe from FruitBasketMdiPy.py and the Homer
rem Python package.
rem
rem This is the HomerDev TEMPLATE for a PYTHON app. newHomerApp.cmd
rem writes a copy of it with FruitBasketMdiPy replaced by a real app name when it
rem is asked for a Python app.
rem
rem WHAT IT PRODUCES: one file, FruitBasketMdiPy.exe, with Python, the Homer
rem package and every dependency inside it. Somebody who installs the
rem program needs no Python of their own. That is what makes a Python
rem program shippable on the same terms as a C# one, and it is how
rem urlCheck and helpFido are built.
rem
rem KIT: the Homer Python package is NOT copied into the app folder. It
rem is taken from the kit, which is looked for in this order, first hit
rem wins:
rem   1. %HomerDev%        the environment variable, when it is set
rem   2. the current folder and every folder above it, each either the kit
rem      or holding a folder named HomerDev
rem   3. this script's folder and every folder above it, the same way
rem   4. a folder named HomerDev at the top of any drive
rem Only Windows and the folder name are assumed (1.46.0), never a drive.
rem
rem VERSION: version.txt is the single source of truth, exactly as in
rem the C# build. This script increments it on every build, stepping
rem over any number already released, which it learns from the
rem repository's own tags, and writes version.py from it so the running
rem program reports the same number. FruitBasketMdiPy_setup.iss reads version.txt
rem directly.
rem
rem   buildFruitBasketMdiPyPy.cmd          increments the version, then builds
rem   buildFruitBasketMdiPyPy.cmd nobump   keeps the current number
rem
rem PYTHON: a virtual environment beside this script, so the machine's
rem own Python is left alone and two Homer apps cannot disagree about a
rem package version. It is created on the first build and reused after.
rem
rem Output in this folder: FruitBasketMdiPy.exe, and the installer if Inno Setup is
rem present. Everything is logged to buildFruitBasketMdiPyPy.log in logs\ beside this script, one file per run.
rem ===================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

set "app=FruitBasketMdiPy"
rem THE KIT'S logs FOLDER (1.65.31): a sample in the kit logs where every kit script does, two folders up; a copy of
rem a sample anywhere else logs in a logs folder beside itself.
set "sLogs=%CD%\logs"
if exist "%~dp0..\..\version.txt" if exist "%~dp0..\..\Templates" for %%K in ("%~dp0..\..") do set "sLogs=%%~fK\logs"
if not exist "!sLogs!" mkdir "!sLogs!"
for /f %%T in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "sNow=%%T"
set "log=!sLogs!\%app%-build-%sNow%.log"
echo %app% build started %DATE% %TIME%> "%log%"
echo Script: %~f0>> "%log%"
echo Folder: %CD%>> "%log%"
echo Command line: %0 %*>> "%log%"
echo Build log: %log%

rem ---- the Homer Development Kit -------------------------------------
set "homerDev="
if defined HomerDev if exist "%HomerDev%\exec\Python\lbc.py" set "homerDev=%HomerDev%"
rem FOUND WHEREVER IT IS (1.46.0): only Windows and the folder name HomerDev
rem are assumed, never a drive or a depth. After the HomerDev variable: the
rem current folder and every folder above it, then this script's folder and
rem every folder above that, each either the kit or holding a HomerDev
rem folder; then a HomerDev folder at the top of any drive.
if not defined homerDev (
  set "sUp=%CD%"
  call :findKitUp
)
if not defined homerDev (
  set "sUp=%~dp0."
  call :findKitUp
)
if not defined homerDev for %%L in (C D E F G H I J K L M N O P Q R S T U V W X Y Z) do if not defined homerDev if exist "%%L:\HomerDev\exec\Python\lbc.py" set "homerDev=%%L:\HomerDev"
if not defined homerDev (
  echo ERROR: the Homer Development Kit was not found.
  echo         Looked in %%HomerDev%%, this folder and every folder above it, and
  echo         a HomerDev folder at the top of each drive.
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
rem pythonnet, not wxPython (kit 1.73.6): the sample builds the C# Homer frame
rem from Python, so its menus, keys and commands are the C# sample's by
rem construction.
set "pipPackages=pyinstaller pythonnet"
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

rem ---- Python 3.13, for pythonnet (kit 1.73.6) ----------------------
rem THE SAMPLE RUNS THE C# HOMER FRAME FROM PYTHON, through pythonnet, which
rem supports Python up to 3.13 at the time of writing. The Python on the PATH
rem may be newer, so this block, the same as the build template's, finds 3.13
rem through the py launcher and installs it with winget when it is missing.
set "pyVersion=3.13"
rem ---- Python --------------------------------------------------------
set "sPy="
py -!pyVersion! --version >nul 2>&1
if not errorlevel 1 set "sPy=py -!pyVersion!"
if not defined sPy (
  echo Installing Python !pyVersion!, which the build needs.
  >> "%log%" echo Python !pyVersion! not found through py; installing with winget
  winget install --id Python.Python.!pyVersion! --architecture x64 --scope machine --silent --accept-source-agreements --accept-package-agreements >> "%log%" 2>&1
  >> "%log%" echo Ran: winget install Python.Python.!pyVersion!, exit code !errorlevel!
  py -!pyVersion! --version >nul 2>&1
  if not errorlevel 1 set "sPy=py -!pyVersion!"
)
if not defined sPy (
  echo Python !pyVersion! could not be found or installed. Sign out and back in, then build again.
  >> "%log%" echo ERROR: no Python !pyVersion!
  goto :failed
)
for /f "delims=" %%v in ('!sPy! --version 2^>^&1') do >> "%log%" echo Python: %%v through !sPy!
!sPy! -c "import struct,sys; sys.exit(0 if struct.calcsize('P') == 8 else 2)"
if errorlevel 1 (
  echo Python !pyVersion! here is 32-bit, and %app% must be 64-bit. Install the 64-bit Python.
  >> "%log%" echo ERROR: 32-bit Python
  goto :failed
)

rem ---- the virtual environment, rebuilt when its Python is not pyVersion
set "venvPy=%CD%\.venv\Scripts\python.exe"
if exist "!venvPy!" (
  "!venvPy!" -c "import sys; sys.exit(0 if '%%d.%%d' %% sys.version_info[:2] == '!pyVersion!' else 1)"
  if errorlevel 1 (
    >> "%log%" echo .venv holds another Python; removing it
    rmdir /s /q ".venv"
  )
)
if not exist "!venvPy!" (
  echo Creating the build environment, .venv
  !sPy! -m venv .venv >> "%log%" 2>&1
  >> "%log%" echo Ran: !sPy! -m venv .venv, exit code !errorlevel!
)
if not exist "!venvPy!" (
  echo The build environment could not be created. The log says why.
  goto :failed
)
echo Installing what the build needs
"!venvPy!" -m pip install --upgrade pip >> "%log%" 2>&1
>> "%log%" echo Ran: pip install --upgrade pip, exit code !errorlevel!
if exist "requirements.txt" (
  "!venvPy!" -m pip install --upgrade -r requirements.txt >> "%log%" 2>&1
  set "iCode=!errorlevel!"
  >> "%log%" echo Ran: pip install --upgrade -r requirements.txt, exit code !iCode!
  if not "!iCode!"=="0" (
    echo The packages in requirements.txt could not be installed. The log says why.
    goto :failed
  )
)
"!venvPy!" -m pip install --upgrade !pipPackages! >> "%log%" 2>&1
set "iCode=!errorlevel!"
>> "%log%" echo Ran: pip install --upgrade !pipPackages!, exit code !iCode!
if not "!iCode!"=="0" (
  echo !pipPackages! could not be installed. The log says why.
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
rem "import lbc" resolves to the kit rather than to a copy.
rem --windowed keeps a console from appearing behind the window; drop it
rem for a program that writes to the console.
set "icon="
if exist "%app%.ico" set "icon=--icon %app%.ico"
echo Building %app%.exe>> "%log%"
rem Homer.dll is the kit's C# frame, key router and dialogs, which the build
rem compiles before the samples; it is bundled beside the program, where
rem lbcnet finds it. pythonnet and clr_loader are collected whole, because
rem they load their own .NET pieces at run time.
if not exist "!homerDev!\exec\Homer.dll" (
  echo(
  echo ERROR: !homerDev!\exec\Homer.dll is missing. The kit's build compiles it first; run build again.
  echo ERROR: no !homerDev!\exec\Homer.dll>> "%log%"
  goto :failed
)
echo Bundling !homerDev!\exec\Homer.dll>> "%log%"
"!venvPy!" -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name %app% ^
  --paths "!homerDev!\exec\Python" ^
  --hidden-import lbcnet ^
  --hidden-import log ^
  --hidden-import mdi ^
  --hidden-import paths ^
  --add-binary "!homerDev!\exec\Homer.dll;." ^
  --collect-all pythonnet ^
  --collect-all clr_loader ^
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
rem The newest Pandoc on the machine, not merely the first on the PATH (kit 1.56.0).
set "pandoc="
for /f "usebackq delims=" %%p in (`powershell -NoProfile -ExecutionPolicy Bypass -File "!homerDev!\scripts\newest.ps1" pandoc -Log "%log%"`) do set "pandoc=%%p"
if not defined pandoc (
  echo Pandoc was not found, so the .htm files were not rebuilt.>> "%log%"
) else (
  for %%m in (*.md) do (
    "!pandoc!" -f markdown -t html5 --standalone --metadata title="%%~nm" -o "%%~nm.htm" "%%m" >> "%log%" 2>&1
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
echo To publish: commit, then run release. It reads the version from
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
rem fails, the plain increment is used and release remains the check it
rem has always been, so a machine with no network still builds.
rem -------------------------------------------------------------------
set "verOld=!ver!"
set "sTagFile=%TEMP%\%app%_tags.txt"
del "!sTagFile!" >nul 2>&1
git ls-remote --tags origin "v*" > "!sTagFile!" 2>> "%log%"
if errorlevel 1 echo WARN: the released tags could not be read, so the next number is taken blindly.>> "%log%"
if errorlevel 1 del "!sTagFile!" >nul 2>&1
rem THE TAG LIST WITH WINDOWS LINE ENDS (1 October 2026). git writes it with
rem LF alone, and findstr /e matches only before a CR LF, so no tag ever
rem matched and no spent number was stepped over: EdSharp's old releases
rem v5.0.32 to v5.0.36 were each chosen again, and each refused as already
rem released. find /v "" rewrites every line with CR LF.
if exist "!sTagFile!" type "!sTagFile!" | find /v "" > "!sTagFile!.crlf"
if exist "!sTagFile!.crlf" move /y "!sTagFile!.crlf" "!sTagFile!" >nul
if exist "!sTagFile!" for /f %%n in ('find /c "refs/tags/" ^< "!sTagFile!"') do echo Released tags on origin: %%n>> "%log%"

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

:findKitUp
rem Climbs from sUp to the top of its drive (1.46.0), looking for the kit
rem itself or for a folder named HomerDev that holds it.
if exist "!sUp!\exec\Python\lbc.py" (set "homerDev=!sUp!" & goto :eof)
if exist "!sUp!\HomerDev\exec\Python\lbc.py" (set "homerDev=!sUp!\HomerDev" & goto :eof)
for %%I in ("!sUp!\..") do set "sNext=%%~fI"
if /i "!sNext!"=="!sUp!" goto :eof
set "sUp=!sNext!"
goto :findKitUp
