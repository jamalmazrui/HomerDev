@echo off
rem ===================================================================
rem build.cmd -- build _APP_.exe from _APP_.cs and the Homer C#
rem classes in the HomerDev folder, wherever it is.
rem
rem This is the HomerDev TEMPLATE for a C# app. newHomerApp.cmd writes a
rem copy of it with _APP_ replaced by the app's name. If you are reading
rem the copy, the name is in place and the SETTINGS block below is the part
rem to edit. urlFido's buildUrlFido.cmd is the worked example.
rem
rem IT KEEPS THE SAME CONTRACT AS THE PYTHON BUILD, build_APP_Py.cmd,
rem clause for clause (kit 1.43.3):
rem   - finds the kit, and stops with a plain message when the kit is older
rem     than kitNeeded, telling a parse failure from an old kit;
rem   - version.txt is the single source of truth: stepped on every build
rem     (nobump keeps it), seeded when missing from the app's own number or
rem     one past its newest release tag, never from 1.0.0 over a released
rem     app, and written into Version.cs as BuildVersion.Version;
rem   - the program goes to exec\, as in the installed tree;
rem   - the kit's classes are NOT copied: each module named in homerModules
rem     is compiled straight from the kit's exec\CSharp, and a stale copy of a
rem     kit class at the top of the project is deleted once the kit's is here;
rem   - the compiler is Roslyn, found with vswhere or installed with winget
rem     as the free Build Tools. The Framework's own csc stops at C# 5 and
rem     cannot compile the kit, so it is never used;
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
rem   build               steps the version, then builds
rem   build nobump        keeps the current number
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
set "progFiles86=%ProgramFiles(x86)%"
set "progFiles=%ProgramFiles%"

rem ---- SETTINGS: the part an app edits -------------------------------
rem The oldest kit with everything this build uses.
set "kitNeeded=1.43.31"
rem The number to start from when version.txt is missing. A newer release
rem tag, if the repository has one, wins. It is also a floor: a version.txt
rem holding less is raised to it.
set "seedVersion=1.0.0"
rem winexe for a program with only windows; exe for one that writes to the
rem console, even if it also opens a dialog.
set "cscTarget=winexe"
rem The kit classes the program uses, alphabetical. Lbc needs Elevate (its
rem Help box offers the update), Log, Paths, Say and Util; Log needs Paths and
rem Say; Mdi needs KeyMap. Each is compiled from the kit's exec\CSharp.
set "homerModules=Elevate Inix KeyName Lbc Log Paths Say Util Web"
rem The app's own sources beside _APP_.cs, if any, space separated.
set "appSources="
rem Files embedded in the program as resources, space separated: a sound, a
rem native DLL the program extracts itself.
set "csResources="
rem NVDA's controller client, the DLL Say.cs speaks to NVDA through.
rem   exec   fetched and put beside the program in exec (the usual choice;
rem          the installer ships exec\*.dll)
rem   embed  fetched and embedded as a resource, for a program that extracts
rem          and loads it itself (urlFido)
rem   (empty) not used
set "nvdaClient=exec"
rem NuGet packages the program references, as id:assembly pairs, such as
rem Markdig:Markdig.dll. Each is fetched into exec and referenced there.
set "nugetPackages="
rem The kit tools this app uses, refreshed into scripts\ on every build.
rem Name each; add one the day it is used (installCommon.cmd for install
rem scripts written in cmd, buildTutorials and its fellows once a walk exists,
rem post.cmd and post.ps1 once the app publishes a page).
set "kitTools=check.cmd check.py fixEncoding.cmd fixEncoding.py kind.cmd kind.py push.cmd release.cmd release.ps1 tidy.cmd tidy.py unpushed.cmd unpushed.py"
set "useDocs=1"
set "useInstaller=1"
set "useVersionSteps=1"
rem ---- end of SETTINGS -------------------------------------------------

rem Retired and renamed kit scripts an app may still carry: deleted.
set "retiredTools=checkHomerApp.cmd checkHomerApp.py cleanDir.cmd cleanDir.py gitPush.cmd gitRelease.cmd gitUnpushed.cmd gitUnpushed.py homerFinish.cmd homerInstall.cmd homerPolicy.py homerTidy.cmd homerTidy.py installTools.cmd sayTutorial.cmd sayTutorial.py tagRelease.cmd tagRelease.ps1 tidyRepo.cmd tidyRepo.py"
rem Kit classes an app used to carry its own copy of. Once the kit's is here,
rem a copy at the top of the project is deleted: copies drift, and every one
rem found so far had.
set "kitClasses=Elevate.cs Inix.cs inixVert.cs KeyMap.cs KeyName.cs Lbc.cs Log.cs Mdi.cs Ollama.cs Paths.cs PdfRead.cs Say.cs Util.cs Web.cs"

rem EVERY SESSION ITS OWN LOG, IN logs\: <App>-build-yyyyMMdd-HHmmss.log. An
rem alphabetical sort is then a chronological one. wmic is gone from Windows
rem 11, so the stamp comes from PowerShell.
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "sStamp=%%i"
if not exist "logs" mkdir "logs"
set "log=%CD%\logs\%app%-build-%sStamp%.log"
rem THE START AND END LINES CARRY AN ISO 8601 TIME (1.43.21), with its UTC
rem offset, from PowerShell rather than %DATE% %TIME%, whose form depends on
rem the regional settings -- "Sun 09/27/2026 16:18:38.77" here -- and which no
rem program can read reliably. They name the event and its result as the other
rem Homer logs do: "build start app=2htm", "build end result=succeeded".
for /f "usebackq delims=" %%i in (`powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-ddTHH:mm:ss.fffzzz'"`) do set "sIso=%%i"
> "%log%" echo %sIso% INFO  build start app=%app%
>> "%log%" echo Script: %~f0
>> "%log%" echo Folder: %CD%
>> "%log%" echo Command line: %0 %*
>> "%log%" echo User: %USERNAME% on %COMPUTERNAME%
for /f "delims=" %%v in ('ver') do >> "%log%" echo Windows: %%v
>> "%log%" echo Settings: kitNeeded=!kitNeeded! seedVersion=!seedVersion! cscTarget=!cscTarget! nvdaClient=!nvdaClient!
>> "%log%" echo Settings: homerModules=!homerModules!
>> "%log%" echo Settings: appSources=!appSources! csResources=!csResources! nugetPackages=!nugetPackages!
>> "%log%" echo Settings: kitTools=!kitTools!
>> "%log%" echo Settings: useDocs=!useDocs! useInstaller=!useInstaller! useVersionSteps=!useVersionSteps!
echo Building %app%. The log is %log%

rem ---- the Homer Development Kit -------------------------------------
set "homerDev="
if defined HomerDev if exist "%HomerDev%\exec\CSharp\Lbc.cs" set "homerDev=%HomerDev%"
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
if not defined homerDev for %%L in (C D E F G H I J K L M N O P Q R S T U V W X Y Z) do if not defined homerDev if exist "%%L:\HomerDev\exec\CSharp\Lbc.cs" set "homerDev=%%L:\HomerDev"
if not defined homerDev (
  echo %app% needs the Homer Development Kit and cannot find it.
  echo Unzip HomerDev.zip into a folder named HomerDev beside your projects, on any drive,
  echo or set the HomerDev environment variable to where it is.
  >> "%log%" echo ERROR: no kit found from %%HomerDev%%, %CD% and the folders above it, this script's folder and those above it, or the top of any drive
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
  echo Unzip the newer HomerDev.zip into the HomerDev folder at !homerDev!, then build again.
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
rem THE VERSION MUST BE THIS APP'S. A kit unarchived into the app's folder put
rem the kit's version.txt in place of the app's (6 October 2026), and the next
rem build would have bumped the wrong series. The last published tag is the
rem app's own number: when version.txt's first two parts differ from the tag's,
rem the tag wins, and the log says so.
set "tagVer="
for /f "usebackq delims=" %%t in (`git describe --tags --abbrev^=0 2^>nul`) do set "tagVer=%%t"
set "tagVer=!tagVer:v=!"
if not "!tagVer!"=="" (
  for /f "tokens=1,2 delims=." %%a in ("!ver!") do set "verSeries=%%a.%%b"
  for /f "tokens=1,2 delims=." %%a in ("!tagVer!") do set "tagSeries=%%a.%%b"
  if not "!verSeries!"=="!tagSeries!" (
    echo version.txt held !ver!, not this app's series; the last published tag is !tagVer!, so that is the version now.
    >> "%log%" echo version.txt held !ver!, not this app's series; set to the last published tag !tagVer!
    > version.txt echo !tagVer!
    set "ver=!tagVer!"
  )
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
rem Generated output: do not edit it, and do not commit it. A const, so the
rem program may build other constants from it (a user agent, say).
> Version.cs echo // Generated by build.cmd from version.txt.  Do not edit; do not commit.
>> Version.cs echo public static class BuildVersion
>> Version.cs echo {
>> Version.cs echo     public const string Version = "!ver!";
>> Version.cs echo }
>> "%log%" echo Wrote Version.cs holding !ver!

rem ---- the Roslyn compiler ------------------------------------------------
rem vswhere knows every Visual Studio and Build Tools install, of any year and
rem edition, so no list of paths has to be kept current. The doubled quotes
rem are for cmd /c, which strips the outer pair of a command that starts
rem and ends with one.
set "csc="
set "vswhere=!progFiles86!\Microsoft Visual Studio\Installer\vswhere.exe"
if exist "!vswhere!" for /f "usebackq delims=" %%c in (`""!vswhere!" -latest -products * -find "MSBuild\**\Bin\Roslyn\csc.exe""`) do if not defined csc set "csc=%%c"
if not defined csc (
  echo Installing the Visual Studio Build Tools, which hold the C# compiler. This takes several minutes.
  >> "%log%" echo No Roslyn csc.exe; installing Microsoft.VisualStudio.2022.BuildTools with winget
  winget install --id Microsoft.VisualStudio.2022.BuildTools --silent --accept-source-agreements --accept-package-agreements --override "--quiet --wait --norestart --add Microsoft.VisualStudio.Workload.MSBuildTools --add Microsoft.Net.Component.4.8.TargetingPack" >> "%log%" 2>&1
  >> "%log%" echo Ran: winget install Microsoft.VisualStudio.2022.BuildTools, exit code !errorlevel!
  if exist "!vswhere!" for /f "usebackq delims=" %%c in (`""!vswhere!" -latest -products * -find "MSBuild\**\Bin\Roslyn\csc.exe""`) do if not defined csc set "csc=%%c"
)
if not defined csc (
  echo The C# compiler could not be found or installed. The log says why.
  >> "%log%" echo ERROR: no Roslyn csc.exe
  goto :failed
)
>> "%log%" echo Compiler: !csc!

rem ---- reference assemblies given by full path ---------------------------
rem Say.cs needs UIAutomationProvider.dll and UIAutomationTypes.dll for its
rem Narrator notifications, and System.Speech.dll for its SAPI backup. None is
rem on Roslyn's default reference path, so each is named by full path or the
rem compile fails with CS0006. The .NET Framework 4.8 targeting pack has them;
rem the runtime's WPF folder and the assembly cache are the fallbacks.
set "refBase=Reference Assemblies\Microsoft\Framework\.NETFramework"
set "speech="
set "uiaProv="
set "uiaTypes="
for %%v in (v4.8.1 v4.8 v4.7.2 v4.7.1 v4.7 v4.6.2) do (
  if not defined speech if exist "!progFiles86!\!refBase!\%%v\System.Speech.dll" set "speech=!progFiles86!\!refBase!\%%v\System.Speech.dll"
  if not defined uiaProv if exist "!progFiles86!\!refBase!\%%v\UIAutomationProvider.dll" set "uiaProv=!progFiles86!\!refBase!\%%v\UIAutomationProvider.dll"
  if not defined uiaTypes if exist "!progFiles86!\!refBase!\%%v\UIAutomationTypes.dll" set "uiaTypes=!progFiles86!\!refBase!\%%v\UIAutomationTypes.dll"
)
if not defined speech if exist "%SystemRoot%\Microsoft.NET\assembly\GAC_MSIL\System.Speech\v4.0_4.0.0.0__31bf3856ad364e35\System.Speech.dll" set "speech=%SystemRoot%\Microsoft.NET\assembly\GAC_MSIL\System.Speech\v4.0_4.0.0.0__31bf3856ad364e35\System.Speech.dll"
if not defined uiaProv if exist "%SystemRoot%\Microsoft.NET\Framework64\v4.0.30319\WPF\UIAutomationProvider.dll" set "uiaProv=%SystemRoot%\Microsoft.NET\Framework64\v4.0.30319\WPF\UIAutomationProvider.dll"
if not defined uiaTypes if exist "%SystemRoot%\Microsoft.NET\Framework64\v4.0.30319\WPF\UIAutomationTypes.dll" set "uiaTypes=%SystemRoot%\Microsoft.NET\Framework64\v4.0.30319\WPF\UIAutomationTypes.dll"
if not defined speech goto :noRefs
if not defined uiaProv goto :noRefs
if not defined uiaTypes goto :noRefs
>> "%log%" echo References: !speech! ; !uiaProv! ; !uiaTypes!
goto :haveRefs
:noRefs
echo A .NET Framework reference assembly is missing: System.Speech, UIAutomationProvider or UIAutomationTypes.
echo Install the .NET Framework 4.8 targeting pack with the Visual Studio Installer, then build again.
>> "%log%" echo ERROR: speech=!speech! uiaProv=!uiaProv! uiaTypes=!uiaTypes!
goto :failed
:haveRefs

rem ---- the kit's classes, and the stale copies they replace ---------------
set "homerSources="
for %%M in (!homerModules!) do (
  if exist "!homerDev!\exec\CSharp\%%M.cs" (
    set "homerSources=!homerSources! "!homerDev!\exec\CSharp\%%M.cs""
  ) else (
    echo The kit has no exec\CSharp\%%M.cs. Update HomerDev to !kitNeeded! or later.
    >> "%log%" echo ERROR: NOT IN THE KIT: exec\CSharp\%%M.cs
    goto :failed
  )
)
>> "%log%" echo Kit sources: !homerSources!
for %%F in (!kitClasses!) do (
  if exist "%%F" if exist "!homerDev!\exec\CSharp\%%F" (
    del /q "%%F" && >> "%log%" echo Removed the app's own copy of %%F; the kit's is compiled instead
  )
)

rem ---- fetched inputs: NuGet packages and the NVDA controller client -----
if not exist "exec" mkdir "exec"
if not exist "work" mkdir "work"
set "extraRefs="
for %%P in (!nugetPackages!) do (
  for /f "tokens=1,2 delims=:" %%a in ("%%P") do (
    call :getNuGet %%a %%b
    if not exist "exec\%%b" goto :failed
    set "extraRefs=!extraRefs! /reference:"exec\%%b""
  )
)
set "resourceArgs="
for %%R in (!csResources!) do (
  if exist "%%R" (
    set "resourceArgs=!resourceArgs! /resource:%%R,%%~nxR"
  ) else (
    echo The resource %%R named in csResources is missing.
    >> "%log%" echo ERROR: resource %%R missing
    goto :failed
  )
)
if defined nvdaClient (
  call :getNvdaClient
  if not exist "work\nvda\nvdaControllerClient.dll" goto :failed
  if /i "!nvdaClient!"=="embed" set "resourceArgs=!resourceArgs! /resource:work\nvda\nvdaControllerClient.dll,nvdaControllerClient.dll"
  if /i "!nvdaClient!"=="exec" copy /y "work\nvda\nvdaControllerClient.dll" "exec\" >nul
)

rem ---- a copy running from this project's exec cannot be replaced ------
powershell -NoProfile -Command "$p = Get-Process -Name '%app%' -ErrorAction SilentlyContinue | Where-Object { $_.Path -and $_.Path -like '%CD%\exec\*' }; if ($p) { exit 1 } else { exit 0 }"
if errorlevel 1 (
  echo exec\%app%.exe from this project is running, so it cannot be replaced.
  echo Close it, then build again. An installed copy may stay open.
  >> "%log%" echo ERROR: exec\%app%.exe is running; the build does not close it
  goto :failed
)

rem ---- the previous installer goes first (kit 1.64.7) -------------------------
rem A build that stopped before the installer step -- a compile error, say -- left
rem the last build's %app%_setup.exe in place, and installing it looked like
rem installing this build (DbDo, 9 October 2026). It is removed before anything
rem compiles, so a failed build leaves no installer rather than an old one.
if exist "%app%_setup.exe" (
  del /f /q "%app%_setup.exe"
  >> "%log%" echo Removed the previous %app%_setup.exe before compiling
)

rem ---- compile into exec -----------------------------------------------------
set "icon="
if exist "%app%.ico" set "icon=/win32icon:%app%.ico"
set "manifest="
if exist "%app%.manifest" set "manifest=/nowin32manifest /win32manifest:%app%.manifest"
echo Compiling exec\%app%.exe
"!csc!" /nologo /target:!cscTarget! /platform:x64 /optimize+ ^
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
  !extraRefs! !resourceArgs! !icon! !manifest! ^
  /out:"exec\%app%.exe" ^
  Version.cs %app%.cs !appSources! !homerSources! >> "%log%" 2>&1
set "iCode=!errorlevel!"
>> "%log%" echo Ran: csc, exit code !iCode!
if not "!iCode!"=="0" (
  echo The compile failed. The log has the compiler's messages.
  goto :failed
)
echo Built exec\%app%.exe version !ver!
>> "%log%" echo Built exec\%app%.exe version !ver!
rem The program at the top, from the layout before exec: removed now that the
rem new one exists. It is build output, never anything a person made.
if exist "%app%.exe" del /q "%app%.exe" && >> "%log%" echo Removed the old top-level %app%.exe

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
rem THE NEWEST PANDOC, NOT THE FIRST ON THE PATH (kit 1.56.0). An old copy early
rem on the PATH, such as C:\bin\pandoc.exe, used to hide a current one in
rem Program Files. The kit's newest.ps1 runs every copy it can find and prints
rem the newest; the search, every copy with its version, goes to this log.
set "pandoc="
for /f "usebackq delims=" %%p in (`powershell -NoProfile -ExecutionPolicy Bypass -File "!homerDev!\scripts\newest.ps1" pandoc -Log "%log%"`) do set "pandoc=%%p"
if not defined pandoc (
  echo Installing pandoc, which writes the .htm copy of each document
  winget install --id JohnMacFarlane.Pandoc --scope machine --silent --accept-source-agreements --accept-package-agreements >> "%log%" 2>&1
  >> "%log%" echo Ran: winget install JohnMacFarlane.Pandoc, exit code !errorlevel!
  for /f "usebackq delims=" %%p in (`powershell -NoProfile -ExecutionPolicy Bypass -File "!homerDev!\scripts\newest.ps1" pandoc -Log "%log%"`) do set "pandoc=%%p"
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
rem THE AUDIO SHIPS (kit 1.60.3): help\tutorials\*.mp3 goes into the installer
rem and the repository, made here before the installer is compiled, so no user
rem ever waits for it. Every build calls buildTutorials, which speaks only a
rem walk whose text changed since its audio was made, judged by the fingerprint
rem beside each mp3 rather than by dates, which a zip can shift by hours.
if exist "help\Tutorial_*.inix" (
  if exist "help\tutorials\Tutorial_*.mp3" del /q "help\tutorials\Tutorial_*.mp3"
  set "tutorialsWanted=1"
  rem AN ACCEPTANCE BUILD SPEAKS NOTHING (kit 1.54.2): check runs build.cmd
  rem nobump with HomerAcceptance set; speaking twelve walks there ran out its
  rem fifteen-minute clock. The ordinary build's audio is what ships.
  if defined HomerAcceptance (
    set "tutorialsWanted="
    >> "%log%" echo Tutorials: acceptance build, speaking left to the ordinary build
  )
  if defined tutorialsWanted (
    if exist "scripts\buildTutorials.cmd" (
      echo Making sure the spoken tutorials are current
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
for /f "usebackq delims=" %%i in (`powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-ddTHH:mm:ss.fffzzz'"`) do set "sIso=%%i"
>> "%log%" echo %sIso% INFO  build end result=succeeded
echo Build succeeded. Next: exec\%app%.exe to try it, then scripts\push "message" and scripts\release.
endlocal
exit /b 0

:failed
rem A FAILED BUILD TAKES NO NUMBER (HomerDev 1.43.29). version.txt is stepped
rem when a build begins; when it fails, the number goes back, so the next build
rem takes it again and the release never finds an installer one version behind
rem version.txt (HomerScribe, 28 September 2026: 1.0.260 stepped, the kit not
rem found, the release refused).
if defined verOld if not "!ver!"=="!verOld!" (
  > version.txt echo !verOld!
  >> "%log%" echo Version: restored to !verOld!; a failed build takes no number
)
for /f "usebackq delims=" %%i in (`powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-ddTHH:mm:ss.fffzzz'"`) do set "sIso=%%i"
>> "%log%" echo %sIso% ERROR build end result=failed
echo Build failed. The log is %log%
endlocal
exit /b 1


:getNuGet
rem -------------------------------------------------------------------
rem Fetch one assembly out of one NuGet package into exec.
rem   call :getNuGet <package id> <assembly file name>
rem Straight from nuget.org, the newest .NET Framework build preferred.
rem -------------------------------------------------------------------
if exist "exec\%~2" goto :eof
echo Fetching %~1 from NuGet
>> "%log%" echo Fetching %~1 from NuGet
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference = 'Stop';" ^
  "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12;" ^
  "$sTemp = Join-Path $env:TEMP ('nuget_' + [guid]::NewGuid().ToString('N'));" ^
  "New-Item -ItemType Directory -Path $sTemp -Force | Out-Null;" ^
  "$sPkg = Join-Path $sTemp 'package.zip';" ^
  "Invoke-WebRequest -Uri ('https://www.nuget.org/api/v2/package/%~1') -OutFile $sPkg -UseBasicParsing;" ^
  "Expand-Archive -LiteralPath $sPkg -DestinationPath $sTemp -Force;" ^
  "$o = Get-ChildItem -Path (Join-Path $sTemp 'lib') -Recurse -Filter '%~2' | Where-Object { $_.FullName -match 'net4' } | Sort-Object FullName -Descending | Select-Object -First 1;" ^
  "if (-not $o) { $o = Get-ChildItem -Path (Join-Path $sTemp 'lib') -Recurse -Filter '%~2' | Sort-Object FullName -Descending | Select-Object -First 1 };" ^
  "if (-not $o) { throw 'No %~2 in the %~1 package.' };" ^
  "Copy-Item -LiteralPath $o.FullName -Destination (Join-Path '%CD%\exec' '%~2') -Force;" ^
  "Remove-Item -LiteralPath $sTemp -Recurse -Force -ErrorAction SilentlyContinue;" ^
  "'%~2 taken from ' + $o.FullName" >> "%log%" 2>&1
>> "%log%" echo Ran: fetch %~1, exit code !errorlevel!
if not exist "exec\%~2" echo %~2 could not be fetched from NuGet. The log says why.
goto :eof

:getNvdaClient
rem -------------------------------------------------------------------
rem NVDA's controller client, 64-bit, into work\nvda. NV Access publishes it
rem beside each release as nvda_<version>_controllerClient.zip; since NVDA
rem 2024.1 the DLL carries no 32 or 64 in its name. The version below is a
rem known release (2025.3); the client's interface is stable across releases,
rem so a newer NVDA speaks through it as well. A copy the project already
rem has at its top, from the layout before, is taken instead of a download.
rem -------------------------------------------------------------------
if exist "work\nvda\nvdaControllerClient.dll" goto :eof
if not exist "work\nvda" mkdir "work\nvda"
if exist "nvdaControllerClient.dll" (
  move /y "nvdaControllerClient.dll" "work\nvda\" >nul
  >> "%log%" echo Moved the top-level nvdaControllerClient.dll into work\nvda
  goto :eof
)
echo Downloading NVDA's controller client, about 3 MB
>> "%log%" echo Fetching the NVDA controller client
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference = 'Stop';" ^
  "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12;" ^
  "$sVer = '2025.3';" ^
  "$sZip = Join-Path $env:TEMP ('nvdaClient_' + [guid]::NewGuid().ToString('N') + '.zip');" ^
  "$sDir = $sZip + '.d';" ^
  "Invoke-WebRequest -Uri ('https://download.nvaccess.org/releases/' + $sVer + '/nvda_' + $sVer + '_controllerClient.zip') -OutFile $sZip -UseBasicParsing;" ^
  "Expand-Archive -LiteralPath $sZip -DestinationPath $sDir -Force;" ^
  "$o = Get-ChildItem -Path $sDir -Recurse -Filter 'nvdaControllerClient*.dll' | Where-Object { $_.FullName -match '\\x64\\' } | Select-Object -First 1;" ^
  "if (-not $o) { throw 'No x64 nvdaControllerClient DLL in the controller client zip.' };" ^
  "Copy-Item -LiteralPath $o.FullName -Destination '%CD%\work\nvda\nvdaControllerClient.dll' -Force;" ^
  "Remove-Item -LiteralPath $sZip, $sDir -Recurse -Force -ErrorAction SilentlyContinue;" ^
  "'Taken from ' + $o.FullName" >> "%log%" 2>&1
>> "%log%" echo Ran: fetch the NVDA controller client, exit code !errorlevel!
if not exist "work\nvda\nvdaControllerClient.dll" echo NVDA's controller client could not be fetched. The log says why.
goto :eof

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

:findKitUp
rem Climbs from sUp to the top of its drive (1.46.0), looking for the kit
rem itself or for a folder named HomerDev that holds it.
if exist "!sUp!\exec\CSharp\Lbc.cs" (set "homerDev=!sUp!" & goto :eof)
if exist "!sUp!\HomerDev\exec\CSharp\Lbc.cs" (set "homerDev=!sUp!\HomerDev" & goto :eof)
for %%I in ("!sUp!\..") do set "sNext=%%~fI"
if /i "!sNext!"=="!sUp!" goto :eof
set "sUp=!sNext!"
goto :findKitUp
