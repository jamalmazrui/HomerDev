@echo off
rem installModels.cmd -- fetch or update local AI models through Ollama.
rem
rem KIT COPY (HomerDev 1.69.1). HomerDev_setup.iss's model entry named this script from 1.66.0 on, but it was never in
rem the kit, so that entry did nothing, unnoticed where the model was already there. One copy now, for every app.
rem
rem     installModels noPause                 the chat's model, qwen2.5:7b
rem     installModels noPause llama3.2 ...    the models named
rem
rem COMPARED, NOT RE-FETCHED: ollama pull checks each layer of a model against the registry and downloads only what
rem changed, so a current model costs a moment. Ollama is found on the PATH or in its own install folder, which the
rem PATH may not show yet when Ollama was installed a moment ago. Every pull and exit code is in the log.
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

set "sModels="
for %%A in (%*) do if /i not "%%A"=="noPause" if /i not "%%A"=="reinstall" set "sModels=!sModels! %%A"
if not defined sModels set "sModels= qwen2.5:7b"
set "sOllama="
for /f "delims=" %%O in ('where ollama 2^>nul') do if not defined sOllama set "sOllama=%%O"
if not defined sOllama if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" set "sOllama=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
call "%~dp0installCommon.cmd" log "Ollama: !sOllama!; models wanted:!sModels!"
if not defined sOllama (
  echo Ollama is not installed, so no model can be fetched. Tick Ollama on the finish page, or run installOllama.
  goto :failed
)
set "iFailed=0"
for %%M in (!sModels!) do (
  echo Fetching or updating %%M. A new model is several gigabytes; an up-to-date one takes a moment.
  "!sOllama!" pull %%M >> "%log%" 2>&1
  set "iCode=!ERRORLEVEL!"
  call "%~dp0installCommon.cmd" log "ollama pull %%M exit code !iCode!"
  if not "!iCode!"=="0" set "iFailed=1"
)
if "!iFailed!"=="1" goto :failed
echo The models are ready.
goto :done

:failed
echo(
echo Not every model could be fetched. The log says why:
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
