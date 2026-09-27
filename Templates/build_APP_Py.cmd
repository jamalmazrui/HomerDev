@echo off
rem ===================================================================
rem build_APP_Py.cmd -- build _APP_.exe from _APP_.py and the Homer
rem Python package in C:\HomerDev.
rem
rem This is the HomerDev TEMPLATE for a PYTHON app. newHomerApp.cmd
rem writes a copy of it, named build_APP_.cmd, with _APP_ replaced by the
rem app's name. If you are reading the copy, the name is in place and the
rem SETTINGS block below is the part to edit. urlCheck's buildUrlCheck.cmd
rem is the worked example.
rem
rem IT KEEPS THE SAME CONTRACT AS THE C# BUILD, build_APP_.cmd (kit 1.43.2), so a Python
rem app is a Homer app on the same terms:
rem   - finds the kit, and stops with a plain message when the kit is older
rem     than kitNeeded, telling a parse failure from an old kit;
rem   - version.txt is the single source of truth: stepped on every build
rem     (nobump keeps it), seeded when missing from the app's own number or
rem     its newest release tag, never from 1.0.0 over a released app, and
rem     written into version.py so the running program reports it;
rem   - the program goes to exec\, as in the installed tree; PyInstaller's
rem     scratch goes to work\, never beside the source;
rem   - the kit's Python package is NOT copied: PyInstaller is pointed at
rem     the kit with --paths and each module is named with --hidden-import,
rem     so the .exe carries the kit's current code;
rem   - the kit tools this app uses are refreshed into scripts\ and retired
rem     ones deleted, saying so when the kit lacks one;
rem   - documents: every .md at the top and in help\ gets its .htm when the
rem     .htm is missing or older; then fixEncoding puts every file the
rem     project names into the Homer encoding;
rem   - every file in help\ and every scripts\install*.cmd must be named by
rem     a Source: line of _APP__setup.iss, or the build stops;
rem   - the installer is compiled with /DHomerDev=<kit>;
rem   - one log per run: logs\_APP_-build-yyyyMMdd-HHmmss.log. The console
rem     says briefly what is happening; the log holds every command and
rem     its exit code.
rem
rem   build_APP_          steps the version, then builds
rem   build_APP_ nobump   keeps the current number
rem
rem A running copy of the program is never closed. The build says so and
rem stops only when the copy running is exec\_APP_.exe from THIS project,
rem which cannot be replaced while it runs; an installed copy under Program
rem Files is no concern of the build's.
rem
rem PARSE-TIME PITFALL: the variable NAME ProgramFiles(x86) contains
rem parentheses, and cmd.exe scans a parenthesised block for its closing
rem paren BEFORE expanding variables. The name is copied into progFiles86
rem outside any block, and only !progFiles86! is used inside one.
rem ===================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

set "app=_APP_"

rem ---- SETTINGS: the part an app edits -------------------------------
rem The oldest kit with everything this build uses.
set "kitNeeded=1.43.20"
rem The number to start from when version.txt is missing. A newer release
rem tag, if the repository has one, wins. It is also a floor: a version.txt
rem holding less is raised to it.
set "seedVersion=1.0.0"
rem The Python this app is built with. pythonnet, for WinForms from Python,
rem supports up to 3.13 at the time of writing.
set "pyVersion=3.13"
rem --windowed for a program with only windows; --console for one that
rem writes to the console, even if it also opens a dialog.
set "pyiMode=--windowed"
rem The kit modules the program imports, alphabetical. Each becomes a
rem --hidden-import, so PyInstaller bundles it from the kit.
set "homerModules=elevate inix lbc log paths say util web"
rem 1 when the program builds WinForms dialogs with the kit's C# LbcDialog
rem through homer.lbcnet: C:\HomerDev\exec\Homer.dll, which buildHomerDev
rem compiles, is bundled into the program. Empty for a console or wx program.
set "homerDll="
rem Anything else PyInstaller needs, such as --collect-all pythonnet.
set "pyiExtra="
rem pip packages beyond requirements.txt, which is installed when present.
set "pipPackages=pyinstaller"
rem The kit tools this app uses, refreshed into scripts\ on every build.
rem Name each; add one the day it is used (installCommon.cmd for install
rem scripts written in cmd, buildTutorials and its fellows once a walk exists).
set "kitTools=check.cmd check.py fixEncoding.cmd fixEncoding.py push.cmd release.cmd release.ps1 tidy.cmd tidy.py unpushed.cmd unpushed.py"
set "useDocs=1"
set "useInstaller=1"
set "useVersionSteps=1"
rem ---- end of SETTINGS -------------------------------------------------

rem Retired and renamed kit scripts an app may still carry: deleted.
set "retiredTools=checkHomerApp.cmd checkHomerApp.py cleanDir.cmd cleanDir.py gitPush.cmd gitRelease.cmd gitUnpushed.cmd gitUnpushed.py homerFinish.cmd homerInstall.cmd homerPolicy.py homerTidy.cmd homerTidy.py installTools.cmd sayTutorial.cmd sayTutorial.py tagRelease.cmd tagRelease.ps1 tidyRepo.cmd tidyRepo.py"

rem EVERY SESSION ITS OWN LOG, IN logs\: <App>-build-yyyyMMdd-HHmmss.log. An
rem alphabetical sort is then a chronological one. wmic is gone from Windows
rem 11, so the stamp comes from PowerShell.
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "sStamp=%%i"
if not exist "logs" mkdir "logs"
set "log=%CD%\logs\%app%-build-%sStamp%.log"
> "%log%" echo %app% build started %DATE% %TIME%
>> "%log%" echo Script: %~f0
>> "%log%" echo Folder: %CD%
>> "%log%" echo Command line: %0 %*
>> "%log%" echo User: %USERNAME% on %COMPUTERNAME%
for /f "delims=" %%v in ('ver') do >> "%log%" echo Windows: %%v
>> "%log%" echo Settings: kitNeeded=!kitNeeded! seedVersion=!seedVersion! pyVersion=!pyVersion! pyiMode=!pyiMode!
>> "%log%" echo Settings: homerModules=!homerModules!
>> "%log%" echo Settings: pyiExtra=!pyiExtra!
>> "%log%" echo Settings: pipPackages=!pipPackages!
>> "%log%" echo Settings: kitTools=!kitTools!
>> "%log%" echo Settings: useDocs=!useDocs! useInstaller=!useInstaller! useVersionSteps=!useVersionSteps!
echo Building %app%. The log is %log%

rem ---- the Homer Development Kit -------------------------------------
set "homerDev="
if defined HomerDev if exist "%HomerDev%\homer\log.py" set "homerDev=%HomerDev%"
if not defined homerDev if exist "C:\HomerDev\homer\log.py" set "homerDev=C:\HomerDev"
if not defined homerDev if exist "%CD%\homer\log.py" set "homerDev=%CD%"
if not defined homerDev (
  echo %app% needs the Homer Development Kit and cannot find it.
  echo Unzip HomerDev.zip into C:\HomerDev, or set the HomerDev environment variable.
  >> "%log%" echo ERROR: no kit found in %%HomerDev%%, C:\HomerDev or %CD%
  goto :failed
)
rem READ THE KIT'S VERSION WITHOUT ANYTHING INVISIBLE. A byte order mark or a
rem trailing space rides along with "set /p", and "kit 1.40.1 is older than
rem 1.40.1" followed on 25 September 2026. PowerShell reads and trims.
set "homerVer=0.0.0"
if exist "!homerDev!\version.txt" (
  for /f "usebackq delims=" %%v in (`powershell -NoProfile -Command "(Get-Content -Raw -LiteralPath '!homerDev!\version.txt').Trim([char]0xFEFF, ' ', [char]13, [char]10)"`) do set "homerVer=%%v"
)
>> "%log%" echo Kit: !homerDev! version !homerVer!, needed !kitNeeded!
powershell -NoProfile -Command "$h='!homerVer!'.Trim(); $n='!kitNeeded!'.Trim(); try { if ([version]$h -lt [version]$n) { exit 1 } else { exit 0 } } catch { exit 2 }"
if errorlevel 2 (
  echo The kit's version.txt at !homerDev! does not hold a version number.
  >> "%log%" echo ERROR: kit version "!homerVer!" does not parse
  goto :failed
)
if errorlevel 1 (
  echo %app% needs HomerDev !kitNeeded! or later, and the kit is !homerVer!.
  echo Unzip HomerDev.zip into C:\HomerDev, then build again.
  >> "%log%" echo ERROR: kit !homerVer! is older than !kitNeeded!
  goto :failed
)
echo Kit !homerVer! at !homerDev!

rem ---- version: version.txt is the single source of truth -----------
set "bSeeded="
if not exist "version.txt" call :seedVersion
if not exist "version.txt" goto :failed
set "ver="
for /f "usebackq delims=" %%v in (`powershell -NoProfile -Command "(Get-Content -Raw -LiteralPath 'version.txt').Trim([char]0xFEFF, ' ', [char]13, [char]10)"`) do set "ver=%%v"
if "!ver!"=="" (
  echo version.txt is empty.
  >> "%log%" echo ERROR: version.txt is empty
  goto :failed
)
rem SEEDVERSION IS A FLOOR, not only a starting point (kit 1.43.5). An app
rem moved to the kit may already have a version.txt below the number its move
rem was meant to start at -- 2htm had 1.18.4 and stepped to 1.18.5 while its
rem documents said 1.19.0. A version.txt below seedVersion is raised to it,
rem and that build takes the seed as it is, just as a newly made version.txt
rem would. A number that does not parse is left for the step below to report.
if not defined bSeeded (
  powershell -NoProfile -Command "try { if ([version]'!ver!' -lt [version]'!seedVersion!') { exit 1 } else { exit 0 } } catch { exit 0 }"
  if errorlevel 1 (
    > version.txt echo !seedVersion!
    echo Version !ver! is below this app's floor of !seedVersion!, so version.txt now holds !seedVersion!
    >> "%log%" echo Raised version.txt from !ver! to the seedVersion floor !seedVersion!
    set "ver=!seedVersion!"
    set "bSeeded=1"
  )
)
if defined bSeeded goto :keepVersion
if /i "%~1"=="nobump" goto :keepVersion
if not defined useVersionSteps goto :keepVersion
call :takeNextVersion
goto :haveVersion

:keepVersion
echo Version !ver!, kept
>> "%log%" echo Version: !ver! (kept: seeded this run, nobump, or no version steps)

:haveVersion
rem Generated output: do not edit it, and do not commit it.
> version.py echo # Generated by build%app%.cmd from version.txt.  Do not edit; do not commit.
>> version.py echo sVersion = "!ver!"
>> "%log%" echo Wrote version.py holding !ver!

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

rem ---- a copy running from this project's exec cannot be replaced ------
powershell -NoProfile -Command "$p = Get-Process -Name '%app%' -ErrorAction SilentlyContinue | Where-Object { $_.Path -and $_.Path -like '%CD%\exec\*' }; if ($p) { exit 1 } else { exit 0 }"
if errorlevel 1 (
  echo exec\%app%.exe from this project is running, so it cannot be replaced.
  echo Close it, then build again. An installed copy may stay open.
  >> "%log%" echo ERROR: exec\%app%.exe is running; the build does not close it
  goto :failed
)

rem ---- build one file into exec -----------------------------------------
if not exist "exec" mkdir "exec"
set "workDir=%CD%\work\pyinstaller"
set "icon="
if exist "%app%.ico" set "icon=--icon "%CD%\%app%.ico""
set "hidden=--hidden-import homer"
for %%M in (!homerModules!) do set "hidden=!hidden! --hidden-import homer.%%M"
set "homerDllArg="
if defined homerDll (
  if not exist "!homerDev!\exec\Homer.dll" (
    echo !homerDev!\exec\Homer.dll is missing. Run buildHomerDev, which compiles it, then build again.
    >> "%log%" echo ERROR: no !homerDev!\exec\Homer.dll
    goto :failed
  )
  set "homerDllArg=--add-binary "!homerDev!\exec\Homer.dll;.""
  >> "%log%" echo Bundling !homerDev!\exec\Homer.dll for homer.lbcnet
)
echo Building exec\%app%.exe, which takes a minute or two
>> "%log%" echo PyInstaller: !pyiMode! !hidden! !pyiExtra! !icon!
"!venvPy!" -m PyInstaller --noconfirm --clean --onefile !pyiMode! --name %app% --paths "!homerDev!" !hidden! !homerDllArg! !pyiExtra! !icon! --distpath "%CD%\exec" --workpath "!workDir!" --specpath "!workDir!" %app%.py >> "%log%" 2>&1
set "iCode=!errorlevel!"
>> "%log%" echo Ran: PyInstaller, exit code !iCode!
if not "!iCode!"=="0" (
  echo PyInstaller failed. The log has its output.
  goto :failed
)
if not exist "exec\%app%.exe" (
  echo PyInstaller returned 0 but wrote no exec\%app%.exe.
  >> "%log%" echo ERROR: no exec\%app%.exe
  goto :failed
)
echo Built exec\%app%.exe version !ver!
>> "%log%" echo Built exec\%app%.exe version !ver!
rem What the layout before exec left behind, removed now that the new one
rem exists: the program at the top, PyInstaller's build and dist folders and
rem its .spec. All are build output, never anything a person made.
if exist "%app%.exe" del /q "%app%.exe" && >> "%log%" echo Removed the old top-level %app%.exe
if exist "%app%.spec" del /q "%app%.spec" && >> "%log%" echo Removed the old %app%.spec
if exist "build\%app%\" rmdir /s /q "build\%app%" && >> "%log%" echo Removed the old build\%app% folder
if exist "build\" rmdir "build" 2>nul
if exist "dist\%app%.exe" del /q "dist\%app%.exe" && >> "%log%" echo Removed the old dist\%app%.exe
if exist "dist\" rmdir "dist" 2>nul

rem ---- the kit's tools this app uses, refreshed on every build ----------
if not exist "scripts" mkdir "scripts"
for %%F in (!kitTools!) do (
  if exist "!homerDev!\scripts\%%F" (
    copy /y "!homerDev!\scripts\%%F" "scripts\" >nul && >> "%log%" echo Refreshed scripts\%%F
  ) else (
    >> "%log%" echo NOT IN THE KIT: scripts\%%F
    echo The kit has no scripts\%%F. Update HomerDev to !kitNeeded! or later.
  )
)
for %%F in (!retiredTools!) do (
  if exist "scripts\%%F" del /q "scripts\%%F" && >> "%log%" echo Removed retired scripts\%%F
)

rem ---- documents ----------------------------------------------------------
if not defined useDocs goto :docsDone
set "pandoc="
for /f "delims=" %%p in ('where pandoc 2^>nul') do if not defined pandoc set "pandoc=%%p"
if not defined pandoc if exist "%ProgramFiles%\Pandoc\pandoc.exe" set "pandoc=%ProgramFiles%\Pandoc\pandoc.exe"
if not defined pandoc if exist "%LOCALAPPDATA%\Pandoc\pandoc.exe" set "pandoc=%LOCALAPPDATA%\Pandoc\pandoc.exe"
if not defined pandoc (
  echo Installing pandoc, which writes the .htm copy of each document
  winget install --id JohnMacFarlane.Pandoc --scope machine --silent --accept-source-agreements --accept-package-agreements >> "%log%" 2>&1
  >> "%log%" echo Ran: winget install JohnMacFarlane.Pandoc, exit code !errorlevel!
  if exist "%ProgramFiles%\Pandoc\pandoc.exe" set "pandoc=%ProgramFiles%\Pandoc\pandoc.exe"
)
if not defined pandoc (
  echo Pandoc could not be installed, so no .htm was rebuilt.
  >> "%log%" echo ERROR: no pandoc
  goto :failed
)
>> "%log%" echo Pandoc: !pandoc!
rem A .htm is written when it is missing or older than its .md, so a lost
rem .htm is a non-event and an unchanged document is left alone.
powershell -NoProfile -Command ^
  "$n = 0;" ^
  "$l = @(Get-ChildItem -LiteralPath '.' -Filter '*.md' -File) + @(Get-ChildItem -LiteralPath 'help' -Filter '*.md' -File -ErrorAction SilentlyContinue);" ^
  "foreach ($m in $l) {" ^
  "  $h = [IO.Path]::ChangeExtension($m.FullName, '.htm');" ^
  "  if ((Test-Path -LiteralPath $h) -and ((Get-Item -LiteralPath $h).LastWriteTime -ge $m.LastWriteTime)) { continue }" ^
  "  & '!pandoc!' -f markdown -t html5 --standalone --metadata ('title=' + $m.BaseName) -o $h $m.FullName;" ^
  "  'Ran: pandoc ' + $m.Name + ', exit code ' + $LASTEXITCODE;" ^
  "  if ($LASTEXITCODE -eq 0) { $n++ } else { $bad = 1 }" ^
  "}" ^
  "'Documents converted: ' + $n;" ^
  "if ($bad) { exit 1 } else { exit 0 }" >> "%log%" 2>&1
if errorlevel 1 (
  echo Pandoc could not convert every document. The log names each one.
  goto :failed
)
:docsDone

rem ---- the project's own files in the Homer encoding ---------------------
rem UTF-8 with a byte order mark and CRLF; .cmd and .bat CRLF without the
rem mark. Pandoc writes neither. -build is an argument of its own: a bare
rem call hands the tool THIS script's arguments through %%* (a cmd quirk).
if exist "scripts\fixEncoding.cmd" (
  call "scripts\fixEncoding.cmd" -build >> "%log%" 2>&1
  >> "%log%" echo Ran: scripts\fixEncoding -build, exit code !errorlevel!
)

rem ---- spoken tutorials, when the app has any ---------------------------
if exist "help\Tutorial_*.inix" (
  set "tutorialsMissing="
  for %%F in (help\Tutorial_*.inix) do if not exist "help\tutorials\%%~nF.mp3" set "tutorialsMissing=1"
  if defined tutorialsMissing (
    if exist "scripts\buildTutorials.cmd" (
      echo Speaking the tutorials that have no audio yet
      call "scripts\buildTutorials.cmd" -build
      if errorlevel 1 echo Not every tutorial could be spoken. The tutorials log in logs\ says why.
    ) else (
      echo This app has walks but its kitTools do not name buildTutorials.
    )
  )
)

rem ---- installer ----------------------------------------------------------
if not defined useInstaller goto :done
rem EVERY FILE IN help\ AND EVERY scripts\install*.cmd MUST BE SHIPPED. The
rem Source: lines are read, {#Name} tokens resolved from #define lines, and
rem each file matched against them; recursesubdirs lets a line reach into
rem subfolders. HomerScribe once shipped without ten help files and the
rem shared half of its install scripts, and nothing said so. The PowerShell
rem holds no double quote of its own ([char]34 stands in): cmd would take
rem one as the end of the quoted chunk and eat the caret of [^...].
powershell -NoProfile -Command ^
  "$q = [char]34; $lIss = Get-Content -LiteralPath '%app%_setup.iss';" ^
  "$dDef = @{}; foreach ($s in $lIss) { if ($s -match ('^#define\s+(\w+)\s+' + $q + '([^' + $q + ']*)' + $q)) { $dDef[$matches[1]] = $matches[2] } };" ^
  "$lPat = @(); foreach ($s in $lIss) { if ($s -match ('^\s*Source:\s*' + $q + '([^' + $q + ']+)' + $q)) { $p = $matches[1]; foreach ($k in $dDef.Keys) { $p = $p.Replace('{#' + $k + '}', $dDef[$k]) };" ^
  "  $sAny = '[^\\]*'; if ($s -match 'recursesubdirs') { $sAny = '.*' };" ^
  "  $lPat += ('^' + [regex]::Escape($p).Replace('\*', $sAny).Replace('\?', '.') + '$') } };" ^
  "$iRoot = (Get-Location).Path.Length + 1;" ^
  "$lFiles = @(Get-ChildItem -LiteralPath 'help' -Recurse -File -ErrorAction SilentlyContinue) + @(Get-ChildItem -LiteralPath 'scripts' -Filter 'install*.cmd' -File -ErrorAction SilentlyContinue);" ^
  "$iMissing = 0; foreach ($f in $lFiles) { $r = $f.FullName.Substring($iRoot); $bHit = $false; foreach ($p in $lPat) { if ($r -match $p) { $bHit = $true; break } };" ^
  "  if (-not $bHit) { 'NOT IN THE INSTALLER: ' + $r; $iMissing++ } };" ^
  "'Files checked against the installer: ' + $lFiles.Count + ', missing: ' + $iMissing;" ^
  "exit $iMissing" >> "%log%" 2>&1
if errorlevel 1 (
  echo A file in help or an install script is not in %app%_setup.iss. The log names each one.
  goto :failed
)
set "progFiles86=%ProgramFiles(x86)%"
set "progFiles=%ProgramFiles%"
set "iscc="
if exist "!progFiles86!\Inno Setup 6\ISCC.exe" set "iscc=!progFiles86!\Inno Setup 6\ISCC.exe"
if not defined iscc if exist "!progFiles!\Inno Setup 6\ISCC.exe" set "iscc=!progFiles!\Inno Setup 6\ISCC.exe"
if not defined iscc (
  echo Installing Inno Setup, which builds %app%_setup.exe
  winget install --id JRSoftware.InnoSetup --silent --accept-source-agreements --accept-package-agreements >> "%log%" 2>&1
  >> "%log%" echo Ran: winget install JRSoftware.InnoSetup, exit code !errorlevel!
  if exist "!progFiles86!\Inno Setup 6\ISCC.exe" set "iscc=!progFiles86!\Inno Setup 6\ISCC.exe"
  if not defined iscc if exist "!progFiles!\Inno Setup 6\ISCC.exe" set "iscc=!progFiles!\Inno Setup 6\ISCC.exe"
)
if not defined iscc (
  echo Inno Setup could not be installed, so %app%_setup.exe was not built.
  >> "%log%" echo ERROR: no ISCC.exe
  goto :failed
)
>> "%log%" echo Inno Setup: !iscc!
echo Building %app%_setup.exe
"!iscc!" /DHomerDev="!homerDev!" "%app%_setup.iss" >> "%log%" 2>&1
set "iCode=!errorlevel!"
>> "%log%" echo Ran: ISCC %app%_setup.iss, exit code !iCode!
if not "!iCode!"=="0" (
  echo The installer build failed. The log has Inno Setup's output.
  goto :failed
)
if not exist "%app%_setup.exe" (
  echo Inno Setup returned 0 but wrote no %app%_setup.exe.
  >> "%log%" echo ERROR: no %app%_setup.exe
  goto :failed
)
echo Built %app%_setup.exe version !ver!
>> "%log%" echo Built %app%_setup.exe version !ver!

:done
>> "%log%" echo Build succeeded %DATE% %TIME%
echo Build succeeded. Next: exec\%app%.exe to try it, then scripts\push "message" and scripts\release.
endlocal
exit /b 0

:failed
>> "%log%" echo Build FAILED %DATE% %TIME%
echo Build failed. The log is %log%
endlocal
exit /b 1

:seedVersion
rem -------------------------------------------------------------------
rem A MISSING version.txt IS MADE, NOT AN ERROR -- and not from 1.0.0 over
rem an app that has released before, which would publish a release older
rem than every installed copy. The number is the higher of seedVersion and
rem one past the newest vN.N.N tag on origin. A number made here is new
rem already, so this build does not step it again.
rem -------------------------------------------------------------------
set "ver="
for /f "usebackq delims=" %%v in (`powershell -NoProfile -Command "$b = [version]'!seedVersion!'; try { foreach ($t in @(git ls-remote --tags origin 'v*' 2>$null)) { if ($t -match 'refs/tags/v(\d+)\.(\d+)\.?(\d*)') { $n = New-Object Version ([int]$matches[1]), ([int]$matches[2]), ([int]('0' + $matches[3]) + 1); if ($n -gt $b) { $b = $n } } } } catch { }; '{0}.{1}.{2}' -f $b.Major, $b.Minor, [Math]::Max($b.Build, 0)"`) do set "ver=%%v"
if "!ver!"=="" (
  echo version.txt is missing and no number could be made for it.
  >> "%log%" echo ERROR: could not seed version.txt from !seedVersion!
  goto :eof
)
> version.txt echo !ver!
set "bSeeded=1"
echo Made version.txt holding !ver!
>> "%log%" echo Made version.txt holding !ver! (seed !seedVersion!, or one past the newest release tag)
goto :eof

:takeNextVersion
rem -------------------------------------------------------------------
rem Take the next UNUSED version: the last dotted part of !ver! plus one,
rem stepping over any number that already carries a release tag on origin.
rem One "git ls-remote" is the only network call; if it fails the plain
rem increment is used and release remains the check it has always been.
rem -------------------------------------------------------------------
set "verOld=!ver!"
set "sTagFile=%TEMP%\%app%_tags.txt"
del "!sTagFile!" >nul 2>&1
git ls-remote --tags origin "v*" > "!sTagFile!" 2>> "%log%"
if errorlevel 1 >> "%log%" echo WARN: the released tags could not be read, so the next number is taken blindly.
if errorlevel 1 del "!sTagFile!" >nul 2>&1

:nextCandidate
call :incrementVersion
if not defined new goto :eof
if not exist "!sTagFile!" goto :haveNextVersion
findstr /e /c:"refs/tags/v!ver!" "!sTagFile!" >nul 2>&1
if errorlevel 1 goto :haveNextVersion
echo Version v!ver! is already released; stepping over it.
>> "%log%" echo Version v!ver! is already released; stepping over it.
goto :nextCandidate

:haveNextVersion
del "!sTagFile!" >nul 2>&1
> version.txt echo !ver!
echo Version !verOld! to !ver!
>> "%log%" echo Version: !verOld! to !ver!
goto :eof

:incrementVersion
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
  echo Could not work out the next version from "!ver!".
  >> "%log%" echo ERROR: could not work out the next version from "!ver!"
  goto :eof
)
set "ver=!new!"
goto :eof
