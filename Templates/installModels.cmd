@echo off
rem installModels.cmd -- fetch the local AI models this app uses, for a machine
rem that already has Ollama.
rem
rem The companion to installOllama.cmd, and the reason both exist: somebody who
rem already runs Ollama should not be made to reinstall it to get a model, and
rem somebody with neither should not have to run two things. The installer
rem offers Ollama-and-model as the checked box and this one unchecked beside it.
rem
rem AI NOTE FOR CUSTOMIZING THIS FILE: put every model this app needs on the
rem c_sModels line, separated by spaces, and say in c_sModelNote what they are
rem for. Nothing else here is app-specific.
rem
rem LOG: %LOCALAPPDATA%\<App>\logs\<App>_setup.log, with the app name taken from
rem the folder this script is installed into.
setlocal EnableExtensions EnableDelayedExpansion

set "c_sModels=llama3.2"
set "c_sModelNote=the model that reads and summarizes text"

rem The app name comes from the folder this script is installed into. That is
rem exec in an installed copy, so climb one level when it is.
for %%d in ("%~dp0.") do set "sApp=%%~nxd"
if /i "%sApp%"=="exec" for %%d in ("%~dp0..") do set "sApp=%%~nxd"
set "sLogDir=%LOCALAPPDATA%\%sApp%\logs"
set "sLog=%sLogDir%\%sApp%_setup.log"
if not exist "%sLogDir%" mkdir "%sLogDir%" >nul 2>&1

call :logLine "installModels started %DATE% %TIME%"
call :logLine "Script: %~f0"
call :logLine "App: %sApp%"
call :logLine "Models wanted: %c_sModels% (%c_sModelNote%)"

where ollama >nul 2>&1
if errorlevel 1 (
  echo Ollama is not installed. Tick the Ollama box instead, or run installOllama.
  call :logLine "ERROR: ollama not found."
  goto :done
)

for %%m in (%c_sModels%) do (
  echo Fetching %%m.
  call :logLine "Pulling %%m"
  ollama pull %%m >> "%sLog%" 2>&1
  call :logLine "ollama pull %%m exit code: !ERRORLEVEL!"
)
echo The models are ready.

:done
call :logLine "installModels finished %DATE% %TIME%"
endlocal
exit /b 0

:logLine
echo %~1>> "%sLog%"
goto :eof
