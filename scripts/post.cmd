@echo off
rem post.cmd -- publish the project's document as a GitHub Page that meets
rem WCAG 2.2 AA and the Homer conventions. Part of the HomerDev kit; an app
rem that uses it names "post.cmd post.ps1" in kitTools.
rem
rem     post                         publish the project's main document
rem     post -Source help\FAQ.md     publish that document instead
rem     post -DryRun                 stage everything and stop: nothing is pushed
rem
rem kind.py says what this folder is. An app, a collection or the kit publishes
rem to its gh-pages branch and never touches main or the releases: an app's or
rem the kit's guide, help\<App>.md, or a collection's ReadMe with its .htm
rem documents. A page is its repository: post creates it, publishes to main
rem and makes a release from the document's version. post.ps1 says why.
rem
rem The log is logs\<App>-post-yyyyMMdd-HHmmss.log in the project folder.
setlocal
set "sHere=%~dp0"
rem THE PROJECT IS THE FOLDER THIS IS RUN IN -- unless that folder is the
rem project's scripts or exec folder, in which case it is the parent.
set "sProject=%CD%"
for %%I in ("%CD%") do set "sLeaf=%%~nxI"
if /i "%sLeaf%"=="scripts" for %%I in ("%CD%\..") do set "sProject=%%~fI"
if /i "%sLeaf%"=="exec" for %%I in ("%CD%\..") do set "sProject=%%~fI"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%sHere%post.ps1" -Project "%sProject%" %*
set iResult=%ERRORLEVEL%
endlocal & exit /b %iResult%
