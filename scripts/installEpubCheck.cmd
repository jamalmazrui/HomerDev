@echo off
rem installEpubCheck.cmd -- install or update EPUBCheck, the W3C's EPUB validator, which the book tools run.
rem
rem KIT COPY (HomerDev 1.69.0), one machine-wide component of the shared pattern. EPUBCheck has no installer: it is a
rem Java program in a zip on GitHub. It goes to %ProgramFiles%\EPUBCheck, shared by every project, never under a
rem program's tree; version.txt there names the release, and GitHub's latest is compared with it, so only something
rem newer is downloaded. Program Files needs administrator rights, which a Homer installer already has. Java comes
rem from installJava.cmd, its own component. Every step is in the log.
setlocal enabledelayedexpansion
set "sScript=%~n0"
if not exist "%~dp0installCommon.cmd" (
  echo(
  echo installCommon.cmd is missing from %~dp0
  echo That file is part of this program. Reinstall, or copy it from the
  echo program's zip into this folder, and run this again.
  echo(
  if not defined noPause pause
  exit /b 1
)
call "%~dp0installCommon.cmd" setup "%~f0" %*

set "bReinstall="
for %%A in (%*) do if /i "%%A"=="reinstall" set "bReinstall=1"
set "sWhat=EPUBCheck"
set "sHome=%ProgramFiles%\EPUBCheck"
set "sForce=0"
if defined bReinstall set "sForce=1"
echo Checking EPUBCheck against its latest release on GitHub.
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop'; $home2=$env:sHome; $force=($env:sForce -eq '1');" ^
  "$have=''; if (Test-Path (Join-Path $home2 'version.txt')) { $have=(Get-Content (Join-Path $home2 'version.txt') -Raw).Trim() };" ^
  "$rel=Invoke-RestMethod -Uri 'https://api.github.com/repos/w3c/epubcheck/releases/latest' -Headers @{ 'User-Agent'='HomerDev-installEpubCheck' } -UseBasicParsing;" ^
  "$want=($rel.tag_name -replace '^v',''); Write-Output ('installed ' + ($(if ($have) { $have } else { 'none' })) + ', latest ' + $want);" ^
  "if (-not $force -and $have -eq $want -and (Test-Path (Join-Path $home2 'epubcheck.jar'))) { Write-Output 'CURRENT'; exit 0 };" ^
  "$asset=$rel.assets | Where-Object { $_.name -like 'epubcheck-*.zip' } | Select-Object -First 1; if (-not $asset) { throw 'no epubcheck zip in the latest release' };" ^
  "$zip=Join-Path $env:TEMP $asset.name; Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zip -UseBasicParsing;" ^
  "$tmp=Join-Path $env:TEMP ('epubcheck-' + $want); if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }; Expand-Archive $zip $tmp;" ^
  "$jar=Get-ChildItem $tmp -Recurse -Filter epubcheck.jar | Select-Object -First 1; if (-not $jar) { throw 'epubcheck.jar was not in the zip' };" ^
  "New-Item -ItemType Directory -Force $home2 | Out-Null; Copy-Item (Join-Path $jar.DirectoryName '*') $home2 -Recurse -Force;" ^
  "Set-Content (Join-Path $home2 'version.txt') $want; Remove-Item $zip -Force; Remove-Item $tmp -Recurse -Force; Write-Output ('INSTALLED ' + $want)" > "%TEMP%\installEpubCheck.txt" 2>&1
set "iCode=%ERRORLEVEL%"
type "%TEMP%\installEpubCheck.txt" >> "%log%"
call "%~dp0installCommon.cmd" log "EPUBCheck check and install exit code %iCode%"
if not "%iCode%"=="0" goto :failed
findstr /b /c:"CURRENT" "%TEMP%\installEpubCheck.txt" >nul && (echo EPUBCheck is already the latest release.& goto :done)
echo EPUBCheck is installed in %sHome%.
goto :done

:failed
echo(
echo %sWhat% could not be installed automatically. The log says why:
echo   %log%
echo(
if not defined noPause pause
endlocal
exit /b 1

:done
echo(
if not defined noPause pause
endlocal
exit /b 0
