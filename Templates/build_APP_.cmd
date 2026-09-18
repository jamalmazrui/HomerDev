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
rem are compiled straight out of %homerDev%\CSharp, so there is one copy
rem of Lbc.cs on the machine and every app gets a fix the moment the kit
rem gets it. Set the HOMERDEV environment variable to override the path.
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
rem present. Everything is logged to build_APP_.log beside this script.
rem ===================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

set "app=_APP_"
set "log=%CD%\build%app%.log"
echo %app% build started %DATE% %TIME%> "%log%"
echo Script: %~f0>> "%log%"
echo Folder: %CD%>> "%log%"
echo Command line: %0 %*>> "%log%"
echo Build log: %log%

rem ---- the Homer Development Kit ------------------------------------
if defined HOMERDEV (set "homerDev=%HOMERDEV%") else (set "homerDev=C:\HomerDev")
if not exist "!homerDev!\CSharp\Lbc.cs" (
  echo ERROR: the Homer Development Kit was not found at !homerDev!.
  echo         Unpack HomerDev.zip into C:\HomerDev, or set HOMERDEV to where it is.
  echo ERROR: no kit at !homerDev!>> "%log%"
  goto :failed
)
set "homerVer=unknown"
if exist "!homerDev!\version.txt" set /p homerVer=<"!homerDev!\version.txt"
echo Kit: !homerDev! version !homerVer!
echo Kit: !homerDev! version !homerVer!>> "%log%"

rem The Homer modules this app compiles in. Drop any it does not use;
rem every one of them is optional except the ones your code references.
set "homerSources="
set "homerSources=!homerSources! "!homerDev!\CSharp\Lbc.cs""
set "homerSources=!homerSources! "!homerDev!\CSharp\Say.cs""
set "homerSources=!homerSources! "!homerDev!\CSharp\Inix.cs""
set "homerSources=!homerSources! "!homerDev!\CSharp\Util.cs""
set "homerSources=!homerSources! "!homerDev!\CSharp\Web.cs""
set "homerSources=!homerSources! "!homerDev!\CSharp\Keys.cs""
rem set "homerSources=!homerSources! "!homerDev!\CSharp\KeyMap.cs""
echo Homer modules: !homerSources!>> "%log%"

rem ---- version: version.txt is the single source of truth -----------
if not exist "version.txt" (
  echo ERROR: version.txt not found. It must hold the current version, e.g. 1.0.0
  echo ERROR: version.txt not found.>> "%log%"
  goto :failed
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
if exist "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\Roslyn\csc.exe" set "csc=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\Roslyn\csc.exe"
if not defined csc if exist "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\Roslyn\csc.exe" set "csc=C:\Program Files\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\Roslyn\csc.exe"
if not defined csc if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\Roslyn\csc.exe" set "csc=C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\Roslyn\csc.exe"
if not defined csc if exist "C:\Program Files (x86)\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\Roslyn\csc.exe" set "csc=C:\Program Files (x86)\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\Roslyn\csc.exe"
if not defined csc if exist "C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\Roslyn\csc.exe" set "csc=C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\Roslyn\csc.exe"
if not defined csc if exist "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\Roslyn\csc.exe" set "csc=C:\Program Files\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\Roslyn\csc.exe"
if not defined csc if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\MSBuild\Current\Bin\Roslyn\csc.exe" set "csc=C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\MSBuild\Current\Bin\Roslyn\csc.exe"
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

rem ---- optional icon ------------------------------------------------
set "icon="
if exist "%app%.ico" set "icon=/win32icon:%app%.ico"

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
  !icon! ^
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

rem ---- documentation -------------------------------------------------
rem Every .md ships with a matching .htm. Pandoc writes them when it is
rem on the PATH; without it the .md files travel alone and the installer
rem lines that name .htm are skipped.
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

rem ---- installer, if Inno Setup is present --------------------------
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
