@echo off
rem sayTutorial.cmd -- turn a Tutorial*.inix into an audio tutorial in two
rem voices: one for the narration, a different one for what the screen reader
rem answers.
rem
rem Copy this script and sayTutorial.py beside the tutorial, then:
rem
rem     sayTutorial                         every Tutorial*.inix here
rem     sayTutorial Tutorial_HomerDev.inix  one of them
rem     sayTutorial --list                  the voices this machine has
rem     sayTutorial --narrator "Microsoft David Desktop" --reader "Microsoft Zira Desktop"
rem     sayTutorial --rate 2                a little faster
rem
rem It writes one .wav per spoken line into a folder named for the tutorial, and
rem joins them into one .mp3 when ffmpeg is on the PATH. The parts are kept
rem either way, so one sentence can be re-recorded without redoing the whole
rem thing.
rem
rem Windows' own voices do the speaking, through System.Speech. Nothing is
rem installed and nothing is uploaded.
rem
rem Writes sayTutorial.log beside this script.
setlocal
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found on the PATH. Install it from python.org
    echo        or with: winget install Python.Python.3.12
    endlocal
    exit /b 1
)
python "%~dp0sayTutorial.py" %*
set exitCode=%errorlevel%
endlocal & exit /b %exitCode%
