@echo off
rem ===================================================================
rem build_APP_.cmd -- build _APP_.exe from _APP_.cs and the Homer
rem Development Kit modules in C:\HomerDev.
rem
rem This is the HomerDev TEMPLATE. newHomerApp.cmd writes a copy of it
rem with _APP_ replaced by a real app name. If you are reading the copy,
rem the app name is already in place and you can edit freely.
rem
rem KIT: the shared C# modules are NOT copied into the app folder. They
rem are compiled straight out of the kit, so there is one copy of Lbc.cs
rem on the machine and every app gets a fix the moment the kit gets it.
rem
rem WHERE THE KIT IS LOOKED FOR, in order, first hit wins:
rem   1. %HomerDev%        the environment variable, when it is set
rem   2. C:\HomerDev        the usual place
rem   3. the current directory, for a folder that carries its own copy
rem
rem The third is what lets a sample, a demonstration, or a machine with no
rem kit installed still build: drop the CSharp folder beside the source.
rem
rem VERSION: version.txt is the SINGLE source of truth. It holds one
rem line, nothing else. This script increments it on every build --
rem stepping over any number already released, which it learns from the
rem repository's own tags -- then generates Version.cs from it, so the
rem running program reports the same number. _APP__setup.iss reads
rem version.txt directly, so the installer reports it too, and
rem tagRelease reads it back out of the built setup's version resource
rem to form the tag. No version literal appears anywhere else, so a
rem stale file cannot rewind it.
rem
rem   build_APP_.cmd          increments the version, then builds
rem   build_APP_.cmd nobump   keeps the current number
rem
rem COMPILER: Roslyn is preferred, from Visual Studio or the free Build
rem Tools. The pre-Roslyn csc.exe under Microsoft.NET\Framework64 is
rem accepted as a fallback, but the Homer modules use language features
rem beyond C# 5, so if that fallback is taken and Lbc.cs or Inix.cs
rem fails to compile, install Build Tools:
rem https://visualstudio.microsoft.com/downloads/
rem
rem REFERENCES: three assemblies are NOT on the compiler's default
rem reference path and must be given by full path, or the build fails
rem with CS0006:
rem   System.Speech.dll        -- the Windows voices
rem   UIAutomationProvider.dll -- Say.cs, Narrator notification events
rem   UIAutomationTypes.dll    -- Say.cs
rem Inix.cs additionally needs System.IO.Compression and System.Xml,
rem which are part of the Framework and are referenced below.
rem
rem PARSE-TIME PITFALL: the variable NAME ProgramFiles(x86) contains
rem parentheses, and cmd.exe scans a parenthesised block for its closing
rem paren BEFORE expanding variables. Every search below is therefore a
rem single-line "if not defined X if exist ... set" chain, never a block.
rem
rem Output in this folder: _APP_.exe, and the installer if Inno Setup is
rem present. Everything is logged to logs\_APP_-build-<date>-<time>.log.
rem ===================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

set "app=_APP_"
rem EVERY SESSION ITS OWN LOG, IN logs\, named as the program names its own:
rem <App>-build-yyyyMMdd-HHmmss.log. An alphabetical sort is then a
rem chronological one, and zipping logs\ gathers everything.
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "sStamp=%%i"
if not exist "%~dp0logs" mkdir "%~dp0logs"
set "log=%~dp0logs\%app%-build-%sStamp%.log"
echo %app% build started %DATE% %TIME%> "%log%"
echo Script: %~f0>> "%log%"
echo Folder: %CD%>> "%log%"
echo Command line: %0 %*>> "%log%"
echo Build log: %log%

rem ---- the Homer Development Kit -------------------------------------
set "homerDev="
if defined HomerDev if exist "%HomerDev%\CSharp\Lbc.cs" set "homerDev=%HomerDev%"
if not defined homerDev if exist "C:\HomerDev\CSharp\Lbc.cs" set "homerDev=C:\HomerDev"
if not defined homerDev if exist "%CD%\CSharp\Lbc.cs" set "homerDev=%CD%"
if not defined homerDev (
  echo ERROR: the Homer Development Kit was not found.
  echo         Looked in %%HomerDev%%, C:\HomerDev, and this folder.
  echo         Unpack HomerDev.zip into C:\HomerDev, or set HomerDev to where it is.
  echo ERROR: no kit found.>> "%log%"
  goto :failed
)
set "homerVer=unknown"
if exist "!homerDev!\version.txt" set /p homerVer=<"!homerDev!\version.txt"
echo Kit: !homerDev! version !homerVer!
echo Kit: !homerDev! version !homerVer!>> "%log%"

rem ---- the Homer modules this app compiles in -------------------------
rem Alphabetical, as every list in Homer code is unless another order is
rem clearly more logical. Comment out the ones this app does not use; an
rem unused module costs only build time, so when in doubt leave it in.
rem A MODULE MAY NEED ANOTHER MODULE, and only two do. Mdi.cs uses KeyMap to
rem register every command as it is added, so the two are switched on together:
rem turning on Mdi without KeyMap fails to compile with "The name 'KeyMap' does
rem not exist in the current context", which is exactly how this comment came to
rem be written. Nothing else in the kit has a dependency of its own.
set "homerSources="
rem Elevate.cs: Lbc's Help box checks the web for a newer release through it.
set "homerSources=!homerSources! "!homerDev!\CSharp\Elevate.cs""
set "homerSources=!homerSources! "!homerDev!\CSharp\Inix.cs""
set "homerSources=!homerSources! "!homerDev!\CSharp\KeyName.cs""
rem MDI ONLY (EdSharp, FileDir, DbDo): a multiple-document app needs both of
rem these, and needs them together. Uncomment the pair.
rem set "homerSources=!homerSources! "!homerDev!\CSharp\KeyMap.cs""
rem set "homerSources=!homerSources! "!homerDev!\CSharp\Mdi.cs""
set "homerSources=!homerSources! "!homerDev!\CSharp\Lbc.cs""
set "homerSources=!homerSources! "!homerDev!\CSharp\Log.cs""
set "homerSources=!homerSources! "!homerDev!\CSharp\Paths.cs""
rem set "homerSources=!homerSources! "!homerDev!\CSharp\PdfRead.cs""
set "homerSources=!homerSources! "!homerDev!\CSharp\Say.cs""
set "homerSources=!homerSources! "!homerDev!\CSharp\Util.cs""
set "homerSources=!homerSources! "!homerDev!\CSharp\Web.cs""
echo Homer modules: !homerSources!>> "%log%"

rem ---- component options ----------------------------------------------
rem EVERY COMPONENT ANY HOMER APP HAS EVER NEEDED IS LISTED HERE. The ones
rem used by MORE THAN ONE app are switched on, because that is the evidence
rem that the next app will want them too; the ones used by a single app are
rem left commented with the app named, so turning one on is one character.
rem
rem AI NOTE: to add a component to an app, uncomment its line here and, if it
rem needs fetching, the matching block further down. Do not invent a new
rem mechanism -- every block below follows the same shape: look for it, fetch
rem it when missing, log what happened, fail loudly if it cannot be had.
rem
rem On in the template, because more than one app uses each:
set "useConfigFile=1"
set "useDocs=1"
set "useIcon=1"
set "useInstaller=1"
set "useManifest=1"
set "useNuGet=1"
set "useScreenReaderScripts=1"
set "useVersionSteps=1"
rem
rem Off in the template, each used by one app so far. The app is named so you
rem know where to look for a working example.
rem set "useExifTool=1"        rem HomerScribe: writes descriptions into photographs
rem set "useFfmpeg=1"          rem HomerScribe: video and audio work, with yt-dlp
rem set "useMarkdig=1"         rem 2htm: Markdown to HTML, embedded as a resource
rem set "useNpoi=1"            rem DbDo: .xlsx without Excel
rem set "usePdfPig=1"          rem HomerScribe: reading a PDF with positions
rem set "useSqlite=1"          rem DbDo: System.Data.SQLite and the SQLean shell
rem set "useTesseract=1"       rem HomerScribe: reading scanned text quickly
rem set "useUde=1"             rem EdSharp: detecting a text file's encoding
rem set "useWhisper=1"         rem HomerScribe: transcribing speech

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

rem ---- generate Version.cs from version.txt -------------------------
rem Generated output: do not edit it, and do not commit it.
> Version.cs echo // Generated by build%app%.cmd from version.txt.  Do not edit; do not commit.
>> Version.cs echo public static class BuildVersion
>> Version.cs echo {
>> Version.cs echo     public const string Version = "!ver!";
>> Version.cs echo }

rem ---- locate the compiler ------------------------------------------
set "csc="
if exist "C:\Program Files (x86)\Microsoft Visual Studio\2022\Buildscripts\MSBuild\Current\Bin\Roslyn\csc.exe" set "csc=C:\Program Files (x86)\Microsoft Visual Studio\2022\Buildscripts\MSBuild\Current\Bin\Roslyn\csc.exe"
if not defined csc if exist "C:\Program Files\Microsoft Visual Studio\2022\Buildscripts\MSBuild\Current\Bin\Roslyn\csc.exe" set "csc=C:\Program Files\Microsoft Visual Studio\2022\Buildscripts\MSBuild\Current\Bin\Roslyn\csc.exe"
if not defined csc if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\Roslyn\csc.exe" set "csc=C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\Roslyn\csc.exe"
if not defined csc if exist "C:\Program Files (x86)\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\Roslyn\csc.exe" set "csc=C:\Program Files (x86)\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\Roslyn\csc.exe"
if not defined csc if exist "C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\Roslyn\csc.exe" set "csc=C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\Roslyn\csc.exe"
if not defined csc if exist "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\Roslyn\csc.exe" set "csc=C:\Program Files\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\Roslyn\csc.exe"
if not defined csc if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019\Buildscripts\MSBuild\Current\Bin\Roslyn\csc.exe" set "csc=C:\Program Files (x86)\Microsoft Visual Studio\2019\Buildscripts\MSBuild\Current\Bin\Roslyn\csc.exe"
if not defined csc if exist "%SystemRoot%\Microsoft.NET\Framework64\v4.0.30319\csc.exe" set "csc=%SystemRoot%\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
if not defined csc (
  echo ERROR: no C# compiler was found. Install the Visual Studio Build Tools:
  echo         https://visualstudio.microsoft.com/downloads/
  echo ERROR: no csc.exe found.>> "%log%"
  goto :failed
)
echo Compiler: !csc!
echo Compiler: !csc!>> "%log%"

rem ---- locate the reference assemblies given by full path -----------
rem Copy the paren-bearing root into a paren-free name before any block.
set "progFiles86=%ProgramFiles(x86)%"
set "progFiles=%ProgramFiles%"
set "refBase=Reference Assemblies\Microsoft\Framework\.NETFramework"

set "speech="
set "uiaProv="
set "uiaTypes="

for %%v in (v4.8 v4.7.2 v4.7.1 v4.7 v4.6.2 v4.6.1 v4.6 v4.5.2) do (
  if not defined speech if exist "!progFiles86!\!refBase!\%%v\System.Speech.dll" set "speech=!progFiles86!\!refBase!\%%v\System.Speech.dll"
  if not defined speech if exist "!progFiles!\!refBase!\%%v\System.Speech.dll" set "speech=!progFiles!\!refBase!\%%v\System.Speech.dll"
  if not defined uiaProv if exist "!progFiles86!\!refBase!\%%v\UIAutomationProvider.dll" set "uiaProv=!progFiles86!\!refBase!\%%v\UIAutomationProvider.dll"
  if not defined uiaProv if exist "!progFiles!\!refBase!\%%v\UIAutomationProvider.dll" set "uiaProv=!progFiles!\!refBase!\%%v\UIAutomationProvider.dll"
  if not defined uiaTypes if exist "!progFiles86!\!refBase!\%%v\UIAutomationTypes.dll" set "uiaTypes=!progFiles86!\!refBase!\%%v\UIAutomationTypes.dll"
  if not defined uiaTypes if exist "!progFiles!\!refBase!\%%v\UIAutomationTypes.dll" set "uiaTypes=!progFiles!\!refBase!\%%v\UIAutomationTypes.dll"
)

rem Fallbacks: the assembly cache and the runtime WPF folder.
if not defined speech if exist "%SystemRoot%\Microsoft.NET\assembly\GAC_MSIL\System.Speech\v4.0_4.0.0.0__31bf3856ad364e35\System.Speech.dll" set "speech=%SystemRoot%\Microsoft.NET\assembly\GAC_MSIL\System.Speech\v4.0_4.0.0.0__31bf3856ad364e35\System.Speech.dll"
if not defined uiaProv if exist "%SystemRoot%\Microsoft.NET\Framework64\v4.0.30319\WPF\UIAutomationProvider.dll" set "uiaProv=%SystemRoot%\Microsoft.NET\Framework64\v4.0.30319\WPF\UIAutomationProvider.dll"
if not defined uiaTypes if exist "%SystemRoot%\Microsoft.NET\Framework64\v4.0.30319\WPF\UIAutomationTypes.dll" set "uiaTypes=%SystemRoot%\Microsoft.NET\Framework64\v4.0.30319\WPF\UIAutomationTypes.dll"
if not defined uiaProv if exist "%SystemRoot%\Microsoft.NET\assembly\GAC_MSIL\UIAutomationProvider\v4.0_4.0.0.0__31bf3856ad364e35\UIAutomationProvider.dll" set "uiaProv=%SystemRoot%\Microsoft.NET\assembly\GAC_MSIL\UIAutomationProvider\v4.0_4.0.0.0__31bf3856ad364e35\UIAutomationProvider.dll"
if not defined uiaTypes if exist "%SystemRoot%\Microsoft.NET\assembly\GAC_MSIL\UIAutomationTypes\v4.0_4.0.0.0__31bf3856ad364e35\UIAutomationTypes.dll" set "uiaTypes=%SystemRoot%\Microsoft.NET\assembly\GAC_MSIL\UIAutomationTypes\v4.0_4.0.0.0__31bf3856ad364e35\UIAutomationTypes.dll"

if not defined speech (
  echo ERROR: System.Speech.dll was not found.
  echo         Install the .NET Framework 4.8 Developer Pack:
  echo         https://dotnet.microsoft.com/download/dotnet-framework/net48
  echo ERROR: System.Speech.dll was not found.>> "%log%"
  goto :failed
)
if not defined uiaProv (
  echo ERROR: UIAutomationProvider.dll was not found. Install the .NET Framework 4.8 Developer Pack.
  echo ERROR: UIAutomationProvider.dll was not found.>> "%log%"
  goto :failed
)
if not defined uiaTypes (
  echo ERROR: UIAutomationTypes.dll was not found. Install the .NET Framework 4.8 Developer Pack.
  echo ERROR: UIAutomationTypes.dll was not found.>> "%log%"
  goto :failed
)
echo Speech: !speech!>> "%log%"
echo UI Automation: !uiaProv!>> "%log%"

rem ---- components fetched from the web --------------------------------
rem Nothing here is committed to the repository: a build fetches what it needs,
rem so a fresh clone builds with nothing to install by hand. Every block is
rem idempotent -- a file already present is left alone.
set "extraRefs="

rem NuGet, the one mechanism all of these share. :getNuGet takes a package id
rem and an assembly name, and leaves the .dll in this folder.
rem   call :getNuGet Markdig Markdig.dll

if not defined useMarkdig goto :noMarkdig
call :getNuGet Markdig Markdig.dll
if not exist "Markdig.dll" goto :failed
rem Embedded rather than shipped beside the .exe, which is what keeps the
rem program one self-contained file; the app must resolve it in AssemblyResolve.
set "extraRefs=!extraRefs! /reference:Markdig.dll /resource:Markdig.dll,Markdig.dll"
:noMarkdig

if not defined useNpoi goto :noNpoi
call :getNuGet NPOI NPOI.dll
set "extraRefs=!extraRefs! /reference:NPOI.dll"
:noNpoi

if not defined usePdfPig goto :noPdfPig
call :getNuGet PdfPig UglyToad.PdfPig.dll
set "extraRefs=!extraRefs! /reference:UglyToad.PdfPig.dll"
:noPdfPig

if not defined useSqlite goto :noSqlite
call :getNuGet System.Data.SQLite.Core System.Data.SQLite.dll
set "extraRefs=!extraRefs! /reference:System.Data.SQLite.dll"
:noSqlite

if not defined useUde goto :noUde
call :getNuGet UDE.CSharp Ude.dll
set "extraRefs=!extraRefs! /reference:Ude.dll"
:noUde

rem The tools below are PROGRAMS rather than assemblies, so they are not
rem referenced by the compiler. They are fetched here only when the installer
rem packages them; an app that finds them on the PATH at run time needs none of
rem this. See buildHomerScribe.cmd for worked versions of all four.
rem   ffmpeg and yt-dlp  -- winget, or a direct download of the release zip
rem   exiftool           -- a single .exe from exiftool.org
rem   tesseract          -- winget: UB-Mannheim.TesseractOCR
rem   whisper            -- pip install, into the app's own virtual environment

rem ---- optional icon ------------------------------------------------
set "icon="
if defined useIcon if exist "%app%.ico" set "icon=/win32icon:%app%.ico"

rem ---- optional application manifest ---------------------------------
rem A manifest asks Windows for a privilege level and declares the Windows
rem versions the program understands. Compile with /nowin32manifest when one is
rem supplied, or the compiler embeds its own and the file is ignored.
set "manifest="
if defined useManifest if exist "%app%.manifest" set "manifest=/nowin32manifest /win32manifest:%app%.manifest"

rem ---- is the program still running? ---------------------------------
tasklist /fi "imagename eq %app%.exe" 2>nul | find /i "%app%.exe" >nul
if not errorlevel 1 (
  echo ERROR: %app%.exe is running. Close it and run this again.
  echo ERROR: %app%.exe is running.>> "%log%"
  goto :failed
)

rem ---- compile ------------------------------------------------------
rem One assembly, so the result is a single self-contained executable:
rem   Version.cs   -- generated above from version.txt
rem   %app%.cs     -- the program
rem   and the Homer modules listed at the top, compiled from the kit.
echo Compiling>> "%log%"
echo(>> "%log%"
"!csc!" /nologo /target:winexe /platform:x64 /optimize+ ^
  /reference:System.dll ^
  /reference:System.Core.dll ^
  /reference:System.Data.dll ^
  /reference:System.Drawing.dll ^
  /reference:System.Windows.Forms.dll ^
  /reference:System.Web.dll ^
  /reference:System.Web.Extensions.dll ^
  /reference:System.Net.Http.dll ^
  /reference:System.Xml.dll ^
  /reference:System.IO.Compression.dll ^
  /reference:System.IO.Compression.FileSystem.dll ^
  /reference:Microsoft.VisualBasic.dll ^
  /reference:"!speech!" ^
  /reference:"!uiaProv!" ^
  /reference:"!uiaTypes!" ^
  !extraRefs! ^
  !icon! ^
  !manifest! ^
  /out:%app%.exe ^
  Version.cs %app%.cs !homerSources! >> "%log%" 2>&1

set iBuildResult=%ERRORLEVEL%
type "%log%"
if not "%iBuildResult%"=="0" (
  echo(
  echo ERROR: the build failed. Details above and in %log%.
  goto :failed
)
echo Built %app%.exe version !ver!>> "%log%"
echo(
echo Built %app%.exe version !ver!

rem A <App>.exe.config beside the program is left exactly as it is: it is
rem source, not output, and the installer ships it. It is where a runtime
rem version or an assembly binding redirect goes.
if defined useConfigFile if not exist "%app%.exe.config" echo NOTE: no %app%.exe.config here; the program will take the runtime defaults.>> "%log%"

rem ---- documentation -------------------------------------------------
rem Every .md ships with a matching .htm. Pandoc writes them when it is
rem on the PATH; without it the .md files travel alone and the installer
rem lines that name .htm are skipped.
if not defined useDocs goto :docsDone
where pandoc >nul 2>&1
if errorlevel 1 (
  rem FETCH IT RATHER THAN ASK FOR IT. "Install pandoc and run me again" is a
  rem manual step, and a Homer build script does not leave one.
  echo Installing pandoc, which writes the .htm copies of the documents...
  echo Pandoc not found; installing with winget>> "%log%"
  winget install --id JohnMacFarlane.Pandoc --silent --accept-source-agreements --accept-package-agreements >> "%log%" 2>&1
)
where pandoc >nul 2>&1
if errorlevel 1 (
  echo Pandoc could not be installed, so the .htm files were not rebuilt.>> "%log%"
  echo NOTE: pandoc could not be installed, so the .htm files were not rebuilt.
) else (
  for %%m in (*.md) do (
    pandoc -f markdown -t html5 --standalone --metadata title="%%~nm" -o "%%~nm.htm" "%%m" >> "%log%" 2>&1
    if errorlevel 1 echo WARN: pandoc failed on %%m>> "%log%"
  )
  echo Documentation converted with pandoc.>> "%log%"
)
:docsDone

rem ---- screen reader scripts -----------------------------------------
rem The JAWS scripts are shipped as <App>_JAWS.zip and the NVDA add-on as
rem <App>.nvda-addon; the installer offers both, checked by default. Packing
rem them here means the installer always carries the current ones.
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

rem ---- spoken tutorials, when the app has any ---------------------------
rem Scripts in help\Tutorial_NN_*.inix become Tutorials.md, TutorialFeed.xml,
rem and one .mp3 per walk in help\tutorials with Tutorials.m3u beside them.
rem The three tools that make them -- buildTutorials.cmd, buildTutorials.ps1,
rem makeTutorials.py -- are the kit's, refreshed into scripts\ on every build:
rem one source of truth, and the app still carries what it needs. (Calling
rem the kit's own copy in place does not work: it takes the project to be the
rem folder it sits in, which is the kit.) Speaking happens only when a walk has
rem no audio yet; delete an .mp3 to have it spoken again. The voices -- Kokoro
rem through sherpa-onnx, Apache 2.0, or piper's kristin and john, public
rem domain, when Kokoro cannot be fetched -- are fetched once by the tool.
rem Skipped silently when the app has no tutorial scripts, which most do not.
if exist "help\Tutorial_*.inix" (
  copy /y "%homerDev%\scripts\buildTutorials.cmd" scripts\ >nul
  copy /y "%homerDev%\scripts\buildTutorials.ps1" scripts\ >nul
  copy /y "%homerDev%\scripts\makeTutorials.py" scripts\ >nul
  set "tutorialsMissing="
  for %%F in (help\Tutorial_*.inix) do if not exist "help\tutorials\%%~nF.mp3" set "tutorialsMissing=1"
  if defined tutorialsMissing (
    echo Speaking the tutorials that have no audio yet. The first time fetches the voices.
    call "scripts\buildTutorials.cmd" >> "%log%" 2>&1
    if errorlevel 1 echo WARN: not every tutorial could be spoken. The tutorials log in logs\ says why.
  )
)

rem ---- installer, if Inno Setup is present --------------------------
if not defined useInstaller goto :done
set "iscc="
if exist "!progFiles86!\Inno Setup 6\ISCC.exe" set "iscc=!progFiles86!\Inno Setup 6\ISCC.exe"
if not defined iscc if exist "!progFiles!\Inno Setup 6\ISCC.exe" set "iscc=!progFiles!\Inno Setup 6\ISCC.exe"
if not defined iscc (
  rem FETCH IT RATHER THAN ASK FOR IT, as with pandoc above. The installer is
  rem part of a release, so building it is part of the build.
  echo Installing Inno Setup, which builds %app%_setup.exe...
  echo Inno Setup not found; installing with winget>> "%log%"
  winget install --id JRSoftware.InnoSetup --silent --accept-source-agreements --accept-package-agreements >> "%log%" 2>&1
  if exist "!progFiles86!\Inno Setup 6\ISCC.exe" set "iscc=!progFiles86!\Inno Setup 6\ISCC.exe"
  if not defined iscc if exist "!progFiles!\Inno Setup 6\ISCC.exe" set "iscc=!progFiles!\Inno Setup 6\ISCC.exe"
)
if not defined iscc (
  echo Inno Setup could not be installed, so no installer was built.>> "%log%"
  echo ERROR: Inno Setup could not be installed, so %app%_setup.exe was not built.
  goto :failed
)
echo Inno Setup: !iscc!>> "%log%"
"!iscc!" "%app%_setup.iss" >> "%log%" 2>&1
if errorlevel 1 (
  echo ERROR: the installer build failed. See %log%.
  echo ERROR: the installer build failed.>> "%log%"
  goto :failed
)
if not exist "%app%_setup.exe" (
  echo ERROR: Inno Setup returned 0 but wrote no %app%_setup.exe.>> "%log%"
  echo ERROR: Inno Setup returned 0 but wrote no %app%_setup.exe.
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

:getNuGet
rem -------------------------------------------------------------------
rem Fetch one assembly out of one NuGet package into this folder.
rem   call :getNuGet <package id> <assembly file name>
rem
rem Straight from nuget.org over https, unzipped in the temp folder, with the
rem newest .NET Framework build preferred and any build taken when there is no
rem net4 one. Nothing is installed on the machine and nothing is left behind.
rem -------------------------------------------------------------------
if exist "%~2" goto :eof
echo Fetching %~1 from NuGet.
echo Fetching %~1 from NuGet.>> "%log%"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;" ^
  "$sTemp=Join-Path $env:TEMP ('nuget_'+[guid]::NewGuid().ToString('N'));" ^
  "New-Item -ItemType Directory -Path $sTemp -Force | Out-Null;" ^
  "$sPkg=Join-Path $sTemp 'package.nupkg';" ^
  "Invoke-WebRequest -Uri ('https://www.nuget.org/api/v2/package/%~1') -OutFile $sPkg -UseBasicParsing;" ^
  "Expand-Archive -LiteralPath $sPkg -DestinationPath $sTemp -Force;" ^
  "$oDll = Get-ChildItem -Path (Join-Path $sTemp 'lib') -Recurse -Filter '%~2' |" ^
  "  Where-Object { $_.FullName -match 'net4' } | Sort-Object FullName -Descending | Select-Object -First 1;" ^
  "if (-not $oDll) { $oDll = Get-ChildItem -Path (Join-Path $sTemp 'lib') -Recurse -Filter '%~2' |" ^
  "  Sort-Object FullName -Descending | Select-Object -First 1 }" ^
  "if (-not $oDll) { throw 'No %~2 in the %~1 package.' }" ^
  "Copy-Item -LiteralPath $oDll.FullName -Destination (Join-Path '%CD%' '%~2') -Force;" ^
  "Remove-Item -LiteralPath $sTemp -Recurse -Force -ErrorAction SilentlyContinue;" ^
  "Write-Output ('%~2 taken from ' + $oDll.FullName)" >> "%log%" 2>&1
if not exist "%~2" (
  echo ERROR: %~2 could not be fetched from the %~1 package. See %log%.
  echo ERROR: %~2 could not be fetched.>> "%log%"
)
goto :eof

:takeNextVersion
rem -------------------------------------------------------------------
rem Take the next UNUSED version. The last dotted part of !ver! is
rem incremented, and any number that already carries a release tag on
rem the origin remote is stepped over, so a version.txt that has fallen
rem behind the repository cannot mint a number that is already spent.
rem
rem One "git ls-remote" is the only network call the build makes. If it
rem fails, the plain increment is used and tagRelease remains the check
rem it has always been, so a machine with no network still builds.
rem
rem These are subroutines rather than parenthesised blocks, so each line
rem is parsed on its own.
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
rem Increment the last dotted part of !ver!. Nothing is written here, so
rem the caller may call this repeatedly while stepping over numbers that
rem are already spent.
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
