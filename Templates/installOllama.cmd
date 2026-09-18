@echo off
rem installOllama.cmd -- install Ollama, the local AI engine, on this machine.
rem
rem SHIPPED WITH EVERY HOMER APP THAT CAN USE LOCAL AI, and offered as a
rem checkbox on the installer's final page. More than one Homer app now leans on
rem a local model, so the script is part of the kit rather than a one-off: an
rem app that never calls a model simply leaves the checkbox line out of its
rem .iss and does not ship this file.
rem
rem Local AI is the Homer default because the text it works on -- a job posting,
rem a medical letter, a draft nobody has read yet -- is the user's own and has no
rem business leaving the machine. Ollama runs the model on this computer, needs
rem no account, and costs nothing to run.
rem
rem AI NOTE FOR CUSTOMIZING THIS FILE: change only c_sModel and c_sModelSize
rem below. Everything else is app-independent and should stay as it is.
rem
rem NOTHING PAUSES. A console waiting for a keypress interrupts the
rem installation. The console says what is happening in a few plain words; every
rem detail goes to the log.
rem
rem LOG: %LOCALAPPDATA%\<App>\logs\<App>_setup.log, because an installed program
rem under Program Files cannot write beside its own .exe. The app name is taken
rem from the folder this script is installed into, so nothing is hardcoded.
setlocal EnableExtensions EnableDelayedExpansion

set "c_sModel=llama3.2"
set "c_sModelSize=about 2 GB"

for %%d in ("%~dp0.") do set "sApp=%%~nxd"
set "sLogDir=%LOCALAPPDATA%\%sApp%\logs"
set "sLog=%sLogDir%\%sApp%_setup.log"
if not exist "%sLogDir%" mkdir "%sLogDir%" >nul 2>&1

call :logLine "installOllama started %DATE% %TIME%"
call :logLine "Script: %~f0"
call :logLine "Folder: %~dp0"
call :logLine "App: %sApp%"
call :logLine "Command line: %0 %*"
call :logLine "Model wanted: %c_sModel% (%c_sModelSize%)"

echo Checking for Ollama.
where ollama >nul 2>&1
if not errorlevel 1 goto :haveOllama

call :logLine "Ollama not on the PATH; installing with winget."
where winget >nul 2>&1
if errorlevel 1 (
  echo Windows Package Manager is not available, so Ollama cannot be installed here.
  call :logLine "ERROR: winget not found."
  goto :done
)
echo Installing Ollama. This takes a few minutes.
winget install --id Ollama.Ollama --architecture x64 --accept-source-agreements --accept-package-agreements --silent >> "%sLog%" 2>&1
call :logLine "winget exit code: %ERRORLEVEL%"
where ollama >nul 2>&1
if errorlevel 1 (
  echo Ollama was installed but is not on the PATH yet. Sign out and back in, then run this again.
  call :logLine "ERROR: ollama still not on the PATH after install."
  goto :done
)

:haveOllama
echo Ollama is here.
call :logLine "Ollama found."
echo Fetching the %c_sModel% model (%c_sModelSize%). This takes a while.
ollama pull %c_sModel% >> "%sLog%" 2>&1
call :logLine "ollama pull exit code: %ERRORLEVEL%"
if errorlevel 1 (
  echo The model could not be fetched. The details are in the log.
  goto :done
)
echo The local AI is ready.
call :logLine "Model %c_sModel% is present."

:done
call :logLine "installOllama finished %DATE% %TIME%"
endlocal
exit /b 0

:logLine
echo %~1>> "%sLog%"
goto :eof
