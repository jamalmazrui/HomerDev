r"""recordWalk.py -- drive a Homer app through a walk, record what the screen reader says, and compare.

WHY THIS EXISTS (3 November 2026)

uiCheck drives a program through Windows UI Automation and checks what appears, and says plainly that it
does not hear speech. The tutorials' Hear lines are what a screen reader should say, written by hand and
marked "confirm with a live run". This script is that live run: it presses each step's keys in the real
program while JAWS (or NVDA) runs as usual, records the computer's own sound, writes it down with a local
speech recognizer, and sets beside it, step by step, what the walk expected, what UI Automation says has
focus, and what the app itself said in its speech log.

WHAT IT NEEDS. Python 3 and the internet the first time, to install pywinauto, comtypes, soundcard, numpy
and faster-whisper with pip, for this user only, and to download the speech model (about 500 MB for small.en,
once). No administrator rights. The app must be running, or installed where Windows can start it.

WHILE IT RUNS, keep your hands off the keyboard: it presses keys in the app. To stop it, switch to any
other window -- before every step it checks that the app is still in front, and stops if not.

THE WALK. The same format as a tutorial walk: [step] sections with Key=, Hear= and Say= lines, plus two of
its own, both optional:

    Type=seahawks       text typed before the Key, letter by letter
    Wait=6              seconds to listen after the key, instead of the default
    Press=2             the key pressed twice in quick succession, a double press

recordWalk menus walks every menu item and the Alternate Menu without a walk file; --menus and --items set how far.

USAGE

    recordWalk                          WITH NO ARGUMENTS, THE SENSIBLE WHOLE: the pilot walk, each window scanned once with
                                        Axe.Windows, and then Tutorial 1 performed live -- the menus through the real screen
                                        reader -- when its recording is missing or older than the tutorial or the program
    recordWalk --walk C:\path\walk.inix another walk
    recordWalk --steps 3                only the first three steps
    recordWalk --wait 5                 listen five seconds after each key (default 4)
    recordWalk --model base.en          a smaller, faster, less accurate recognizer (default small.en)
    recordWalk --no-transcribe          record and report, and write nothing down
    recordWalk --no-axe                 leave out the scans
    recordWalk 1                        the same as recordWalk --tutorial --walk 1: Tutorial 1 performed live
    recordWalk --tutorial --walk 1       (or the tutorial's path; a number finds help\Tutorial_1_*.inix)
                                        perform a tutorial live: the host's lines in one Windows voice, the real screen
                                        reader recorded at each key, joined into one recording, <walk>-live.wav and .mp3
    recordWalk --keep                   leave the app open at the end; by default it is closed, so its closing says the run is over
    recordWalk --speaker Headphones     record the sound output whose name holds Headphones (the log names them all)
    recordWalk --app DbDo               the app, when the folder does not say

Writes logs\<App>-recordWalk-<stamp>.log, logs\<App>-recordWalk-<stamp>.md (the report), and one .wav per
step under results\recordWalk-<stamp>. Exit code 0 when every step was heard as expected, 1 otherwise.
"""

import argparse, ctypes, datetime, difflib, glob, json, os, platform, re, shutil, subprocess, sys, time, traceback, urllib.request, wave, zipfile

iDefaultWait, iSampleRate, nMatchNeeded = 4, 16000, 0.6
# Listening (3 November 2026): chunks of a quarter second; speech is a chunk louder than 0.01 (JAWS peaked 0.13 to 0.22);
# half a second of quiet before a key, 0.8 after speech ends, at most ten seconds to settle and fifteen to listen.
nChunkSeconds, nMaxListen, nMaxSettle, nQuietAfter, nQuietBefore, nSpeechLevel = 0.25, 15, 10, 0.8, 0.5, 0.01
sDefaultModel = "small.en"

sStamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
sScriptDir = os.path.dirname(os.path.abspath(__file__))
# THE APP'S FOLDER (5 November 2026): recordWalk lives in the kit's scripts, and is run from the app's folder; that
# folder, when it has a scripts folder of its own, is the app's. Run from the app's own scripts, the folder above it.
sProject = os.getcwd() if (os.path.isdir(os.path.join(os.getcwd(), "scripts"))
                           and os.path.normcase(os.path.abspath(os.getcwd())) != os.path.normcase(os.path.dirname(sScriptDir))) \
    else os.path.dirname(sScriptDir)

sLogPath = ""
lsReport = []


def logLine(sText):
    """Writes one line to the detailed log."""
    if not sLogPath: return False
    with open(sLogPath, "a", encoding="utf-8") as fLog:
        fLog.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + "  " + sText + "\n")
    return True


def sayLine(sText=""):
    """Writes a line to the console, which JAWS reads, and to the log."""
    print(sText, flush=True)
    logLine("CONSOLE: " + sText)
    return True


def ensurePackages():
    """Installs, for this user only, the packages the run needs, when they are missing. Returns True when all import."""
    # SOUNDCARD FIRST (3 November 2026). pywinauto starts COM in multithreaded mode as it loads; soundcard then
    # starts COM itself, is told "already started" (S_FALSE, 1) and treats that success as an error -- "Error
    # 0x100000001" on all three of the first runs. Loaded first, soundcard starts COM, and pywinauto and comtypes
    # accept the apartment they find.
    dNeeded = {"soundcard": "soundcard", "numpy": "numpy", "pywinauto": "pywinauto", "comtypes": "comtypes"}
    lMissing = []
    for sModule, sPackage in dNeeded.items():
        try:
            __import__(sModule)
        except ImportError:
            lMissing.append(sPackage)
    if lMissing:
        sayLine("Installing " + ", ".join(lMissing) + " for this user. This happens once.")
        iCode = subprocess.call([sys.executable, "-m", "pip", "install", "--user", "--quiet"] + lMissing)
        logLine("pip install " + " ".join(lMissing) + " exit " + str(iCode))
    try:
        import soundcard, numpy, pywinauto, comtypes
        return True
    except ImportError as exceptionError:
        sayLine("A package could not be installed: " + str(exceptionError) + ". The log has pip's answer.")
        return False


def ensureWhisper():
    """faster-whisper, installed when missing; None when it cannot be."""
    try:
        from faster_whisper import WhisperModel
        return WhisperModel
    except ImportError:
        pass
    sayLine("Installing faster-whisper, the local speech recognizer. This happens once.")
    iCode = subprocess.call([sys.executable, "-m", "pip", "install", "--user", "--quiet", "faster-whisper"])
    logLine("pip install faster-whisper exit " + str(iCode))
    try:
        from faster_whisper import WhisperModel
        return WhisperModel
    except ImportError as exceptionError:
        logLine("faster-whisper still does not import: " + str(exceptionError))
        return None


def findWhisperCpp():
    """HomerScribe's whisper.cpp, when it is installed: (program, model) or ("", ""). The fallback when
    faster-whisper cannot be installed, which happens on a Python too new for its engine."""
    lRoots = [os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "HomerScribe"),
              os.path.join(os.environ.get("LOCALAPPDATA", ""), "HomerScribe")]
    sExe, sModel = "", ""
    for sRoot in lRoots:
        for sDir, _lDirs, lFiles in os.walk(sRoot):
            for sFile in lFiles:
                sLower = sFile.lower()
                if not sExe and sLower in ("whisper-cli.exe", "main.exe", "whisper.exe"): sExe = os.path.join(sDir, sFile)
                if sLower.startswith("ggml-") and sLower.endswith(".bin"):
                    if not sModel or ".en" in sLower: sModel = os.path.join(sDir, sFile)
    logLine("whisper.cpp: program " + (sExe or "not found") + ", model " + (sModel or "not found"))
    return (sExe, sModel) if sExe and sModel else ("", "")


def transcribeCpp(sExe, sModel, sWave):
    """Writes a recording down with whisper.cpp."""
    sOut = os.path.splitext(sWave)[0]
    lCommand = [sExe, "-m", sModel, "-f", sWave, "-l", "en", "-nt", "-otxt", "-of", sOut]
    oRun = subprocess.run(lCommand, capture_output=True, text=True, timeout=300)
    logLine("whisper.cpp exit " + str(oRun.returncode) + " for " + os.path.basename(sWave))
    if os.path.isfile(sOut + ".txt"):
        with open(sOut + ".txt", "r", encoding="utf-8", errors="replace") as fIn: return " ".join(fIn.read().split())
    return ""


# ---- the walk ----

def readWalk(sPath, bAll=False):
    """The walk's steps: a list of dictionaries with sKey, sType, iWait, sSay and lHear. A walk keeps only the steps
    that press or type something; a tutorial (bAll) keeps its narration too."""
    lSteps, dStep = [], None
    with open(sPath, "r", encoding="utf-8-sig") as fWalk:
        for sRaw in fWalk:
            sLine = sRaw.strip()
            if sLine.startswith(";") or not sLine: continue
            if sLine.lower() == "[step]":
                dStep = {"sKey": "", "sType": "", "iWait": 0, "iPress": 1, "sSay": "", "lHear": []}
                lSteps.append(dStep)
                continue
            if sLine.startswith("["):
                dStep = None
                continue
            if dStep is None or "=" not in sLine: continue
            sName, sValue = [s.strip() for s in sLine.split("=", 1)]
            sName = sName.lower()
            if sName == "key": dStep["sKey"] = sValue
            elif sName == "type": dStep["sType"] = sValue
            elif sName == "say": dStep["sSay"] = sValue
            elif sName == "hear" and sValue: dStep["lHear"].append(sValue)
            elif sName == "press":
                # PRESS=2 (9 November 2026): the key pressed twice in quick succession, as a person double-presses a
                # Homer key to have its second meaning -- spell a value, or show a summary in a window.
                try: dStep["iPress"] = max(1, min(2, int(sValue)))
                except ValueError: logLine("Press is not 1 or 2: " + sValue)
            elif sName == "wait":
                try: dStep["iWait"] = int(sValue)
                except ValueError: logLine("Wait is not a whole number: " + sValue)
    return lSteps if bAll else [d for d in lSteps if d["sKey"] or d["sType"]]


# ---- A TUTORIAL PERFORMED LIVE (5 November 2026) ----------------------------------------------------------------------
# --tutorial reads a tutorial's [step] sections, narration and all. Before each key, the host's Say line is spoken by a
# Windows voice into a file -- never aloud, so it cannot spill into the recording of the screen reader -- then the key
# is pressed and the real reader recorded, as in any walk. A step with no key but a Hear line, where the tutorial has a
# second voice play the screen reader reading, gets a second Windows voice. Every piece is 16 kHz, 16-bit mono, the
# recording's own format, so they join end to end: <walk>-live.wav, and an .mp3 beside it when ffmpeg can be found.
def speechFrames(sText, iVoice):
    """sText spoken by the iVoice'th enabled Windows voice (the first when there are fewer), as 16-bit samples."""
    import numpy, tempfile
    sPath = os.path.join(tempfile.gettempdir(), "recordWalk-say.wav")
    sScript = ("Add-Type -AssemblyName System.Speech; $o = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
               "$l = @($o.GetInstalledVoices() | Where-Object { $_.Enabled }); if ($l.Count -gt %d) { $o.SelectVoice($l[%d].VoiceInfo.Name) }; "
               "$f = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(%d, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, "
               "[System.Speech.AudioFormat.AudioChannel]::Mono); $o.SetOutputToWaveFile($env:RW_WAV, $f); $o.Speak($env:RW_TEXT); $o.Dispose()") % (iVoice, iVoice, iSampleRate)
    oRun = subprocess.run(["powershell", "-NoProfile", "-Command", sScript], env=dict(os.environ, RW_WAV=sPath, RW_TEXT=sText),
                          capture_output=True, text=True, timeout=120)
    if oRun.returncode != 0: logLine("voice exit " + str(oRun.returncode) + ": " + (oRun.stderr or "").strip()[:500])
    with wave.open(sPath, "rb") as oWave:
        return numpy.frombuffer(oWave.readframes(oWave.getnframes()), dtype=numpy.int16)


def launchKey(sProject, sApp):
    """The app's own launch hotkey, from #define HotKey in its installer script, as a set of lower-case key names."""
    sIss = os.path.join(sProject, sApp + "_setup.iss")
    try:
        with open(sIss, encoding="utf-8-sig", errors="replace") as fIn:
            oMatch = re.search(r'^#define\s+HotKey\s+"([^"]+)"', fIn.read(), re.M)
        return keySet(oMatch.group(1)) if oMatch else set()
    except Exception:
        return set()


def keySet(sKey):
    dSame = {"ctrl": "control", "ctl": "control"}
    return set(dSame.get(s.strip().lower(), s.strip().lower()) for s in (sKey or "").split("+") if s.strip())


def framesToInt16(aFrames):
    import numpy
    aMono = aFrames.mean(axis=1) if aFrames.ndim > 1 else aFrames
    return (numpy.clip(aMono, -1.0, 1.0) * 32767).astype(numpy.int16)


def writeLive(sWaves, sWalk, lPieces):
    """The pieces joined, with a short pause between, as <walk>-live.wav; an .mp3 beside it when ffmpeg is found."""
    import numpy
    aGap = numpy.zeros(int(iSampleRate * 0.4), dtype=numpy.int16)
    lJoined = []
    for aPiece in lPieces: lJoined += [aPiece, aGap]
    sBase = os.path.join(sWaves, os.path.splitext(os.path.basename(sWalk))[0] + "-live")
    with wave.open(sBase + ".wav", "wb") as oWave:
        oWave.setnchannels(1); oWave.setsampwidth(2); oWave.setframerate(iSampleRate)
        oWave.writeframes(numpy.concatenate(lJoined).tobytes() if lJoined else b"")
    sFfmpeg = shutil.which("ffmpeg") or ""
    for sKit in (os.environ.get("homerDev", ""), r"C:\HomerDev"):
        if not sFfmpeg and sKit and os.path.isfile(os.path.join(sKit, "exec", "ffmpeg.exe")): sFfmpeg = os.path.join(sKit, "exec", "ffmpeg.exe")
    if sFfmpeg:
        oRun = subprocess.run([sFfmpeg, "-y", "-loglevel", "error", "-i", sBase + ".wav", "-codec:a", "libmp3lame", "-q:a", "4", sBase + ".mp3"], capture_output=True, text=True, timeout=600)
        logLine("ffmpeg exit " + str(oRun.returncode) + " " + (oRun.stderr or "").strip()[:500])
        if oRun.returncode == 0: return sBase + ".mp3"
    return sBase + ".wav"


dNamedKeys = {"enter": "{ENTER}", "escape": "{ESC}", "esc": "{ESC}", "tab": "{TAB}", "space": "{SPACE}",
              "backspace": "{BACKSPACE}", "delete": "{DELETE}", "insert": "{INSERT}", "home": "{HOME}", "end": "{END}",
              "page up": "{PGUP}", "page down": "{PGDN}", "up arrow": "{UP}", "down arrow": "{DOWN}",
              "left arrow": "{LEFT}", "right arrow": "{RIGHT}", "up": "{UP}", "down": "{DOWN}", "left": "{LEFT}",
              "right": "{RIGHT}", "apps": "{APPS}", "applications": "{APPS}"}
dModifiers = {"control": "^", "ctrl": "^", "alt": "%", "shift": "+"}


def keysFor(sKey):
    """A walk's key name, such as Alt+Shift+F1 or Down Arrow, in pywinauto's send_keys syntax.
    Insert, the JAWS key, is held down around the rest, as JAWS needs it."""
    lParts = [s.strip() for s in sKey.split("+") if s.strip()]
    if not lParts: return ""
    sPrefix, bInsert = "", False
    for sPart in lParts[:-1]:
        sLower = sPart.lower()
        if sLower in dModifiers: sPrefix += dModifiers[sLower]
        elif sLower in ("insert", "jaws", "jawskey", "nvda"): bInsert = True
        else: logLine("unknown modifier in key " + repr(sKey) + ": " + sPart)
    sLast = lParts[-1]
    sLower = sLast.lower()
    if sLower in dNamedKeys: sMain = dNamedKeys[sLower]
    elif re.match(r"^f([1-9]|1[0-2])$", sLower): sMain = "{" + sLower.upper() + "}"
    elif len(sLast) == 1: sMain = escapeText(sLast.lower())
    else: sMain = escapeText(sLast)
    sKeys = sPrefix + sMain if len(sMain) == 1 or sMain.startswith("{") else sPrefix + "(" + sMain + ")"
    if bInsert: sKeys = "{INSERT down}" + sKeys + "{INSERT up}"
    return sKeys


def escapeText(sText):
    """Text typed letter by letter: send_keys' own characters wrapped in braces."""
    return "".join("{" + c + "}" if c in "+^%~(){}[]" else c for c in sText)


# ---- the app and its window ----

def exeNameOf(iPid):
    """The file name of the program a process runs, or "" when it cannot be read (from uiCheck)."""
    from ctypes import wintypes
    hProcess = ctypes.windll.kernel32.OpenProcess(0x1000, False, iPid)
    if not hProcess: return ""
    try:
        oBuffer = ctypes.create_unicode_buffer(1024)
        iSize = wintypes.DWORD(1024)
        if ctypes.windll.kernel32.QueryFullProcessImageNameW(hProcess, 0, oBuffer, ctypes.byref(iSize)):
            return os.path.basename(oBuffer.value)
        return ""
    finally:
        ctypes.windll.kernel32.CloseHandle(hProcess)


def exePathOf(iPid):
    """The full path of the program a process runs, or "" when it cannot be read."""
    from ctypes import wintypes
    hProcess = ctypes.windll.kernel32.OpenProcess(0x1000, False, iPid)
    if not hProcess: return ""
    try:
        oBuffer = ctypes.create_unicode_buffer(1024)
        iSize = wintypes.DWORD(1024)
        if ctypes.windll.kernel32.QueryFullProcessImageNameW(hProcess, 0, oBuffer, ctypes.byref(iSize)):
            return oBuffer.value
        return ""
    finally:
        ctypes.windll.kernel32.CloseHandle(hProcess)


def appIdentity(sExe):
    """WHICH BUILD WAS WALKED (5 November 2026): twice a walk's misses could only be explained by guessing that an older
    build had run, from the wording heard. The report now says, under its title, the program's path, its file version
    and when that file was built, so a run is matched to its build without guessing."""
    try:
        lWindows = windowsOf(sExe)
        if not lWindows: return "The app's program could not be identified: no window of " + sExe + " was found."
        sPath = exePathOf(lWindows[0][1])
        if not sPath: return "The app's program could not be identified: its path could not be read."
        sVersion = ""
        try:
            oRun = subprocess.run(["powershell", "-NoProfile", "-Command", "(Get-Item -LiteralPath '" + sPath.replace("'", "''") + "').VersionInfo.FileVersion"],
                                  capture_output=True, text=True, timeout=30)
            sVersion = (oRun.stdout or "").strip()
        except Exception: pass
        sBuilt = datetime.datetime.fromtimestamp(os.path.getmtime(sPath)).strftime("%d %B %Y at %H:%M")
        return "The app: " + sPath + (", version " + sVersion if sVersion else "") + ", built " + sBuilt + "."
    except Exception as oError:
        return "The app's program could not be identified: " + str(oError)


def foregroundExe():
    """The program whose window is in front, and that window's title."""
    from ctypes import wintypes
    hWnd = ctypes.windll.user32.GetForegroundWindow()
    iPid = wintypes.DWORD()
    ctypes.windll.user32.GetWindowThreadProcessId(hWnd, ctypes.byref(iPid))
    iLength = ctypes.windll.user32.GetWindowTextLengthW(hWnd)
    oTitle = ctypes.create_unicode_buffer(iLength + 1)
    ctypes.windll.user32.GetWindowTextW(hWnd, oTitle, iLength + 1)
    return exeNameOf(iPid.value), oTitle.value


def windowsOf(sExe):
    """Visible top-level windows with a title, of any process running sExe: [(handle, pid, title)] (from uiCheck)."""
    from ctypes import wintypes
    lFound = []
    fnProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def onWindow(hWnd, lParam):
        if not ctypes.windll.user32.IsWindowVisible(hWnd): return True
        iLength = ctypes.windll.user32.GetWindowTextLengthW(hWnd)
        if iLength == 0: return True
        oTitle = ctypes.create_unicode_buffer(iLength + 1)
        ctypes.windll.user32.GetWindowTextW(hWnd, oTitle, iLength + 1)
        iPid = wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hWnd, ctypes.byref(iPid))
        if exeNameOf(iPid.value).lower() == sExe.lower(): lFound.append((hWnd, iPid.value, oTitle.value))
        return True
    ctypes.windll.user32.EnumWindows(fnProc(onWindow), 0)
    return lFound


def bringForward(sApp):
    """The app's main window in front: started first when it is not running. True when it is in front."""
    sExe = sApp + ".exe"
    if not windowsOf(sExe):
        lPlaces = [os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), sApp, "exec", sExe),
                   os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), sApp, sExe),
                   os.path.join(sProject, "exec", sExe)]
        sFound = next((s for s in lPlaces if os.path.isfile(s)), "")
        if not sFound:
            sayLine(sApp + " is not running, and " + sExe + " was not found to start it.")
            return False
        sayLine("Starting " + sApp + ".")
        logLine("starting " + sFound)
        subprocess.Popen([sFound], cwd=os.path.dirname(sFound))
        nUntil = time.time() + 30
        while not windowsOf(sExe) and time.time() < nUntil: time.sleep(0.5)
    lWindows = windowsOf(sExe)
    if not lWindows:
        sayLine(sApp + " has no window to bring forward.")
        return False
    hWnd = lWindows[0][0]
    from pywinauto.application import Application
    try:
        Application(backend="uia").connect(handle=hWnd).window(handle=hWnd).set_focus()
    except Exception as exceptionError:
        logLine("set_focus failed: " + str(exceptionError))
    time.sleep(1.0)
    sExeNow, sTitle = foregroundExe()
    logLine("in front: " + sExeNow + " " + repr(sTitle))
    return sExeNow.lower() == sExe.lower()


def closeApp(sApp):
    """Closes the app as Alt+F4 would, so its closing says the run is over (3 November 2026). Each window is asked
    to close; nothing is forced, and an app still open after ten seconds is left so and logged."""
    sExe = sApp + ".exe"
    for hWnd, iPid, sTitle in windowsOf(sExe):
        ctypes.windll.user32.PostMessageW(hWnd, 0x0010, 0, 0)  # WM_CLOSE
        logLine("asked to close: " + repr(sTitle))
    nUntil = time.time() + 10
    while windowsOf(sExe) and time.time() < nUntil: time.sleep(0.5)
    bClosed = not windowsOf(sExe)
    logLine(sApp + (" closed" if bClosed else " still open after ten seconds; left so"))
    return bClosed


# ---- AXE.WINDOWS, THE ENGINE OF ACCESSIBILITY INSIGHTS FOR WINDOWS ------------------------------------------------
# --axe scans the app after each step. Since 5 November 2026 the fetching and scanning live in the kit's axeScan.py,
# shared with the check every push runs, so the rules and the advice are one; it sits beside this script in the kit
# and in every app whose build copies the kit's scripts.
def getAxeCli():
    import axeScan
    axeScan.useLog(logLine)
    return axeScan.getAxeCli()


def axeScan(sCli, iPid, sFolder, sScanId):
    import axeScan as oAxe
    oAxe.useLog(logLine)
    return oAxe.axeScan(sCli, iPid, sFolder, sScanId)


def focusNow():
    """What UI Automation says has keyboard focus: name, kind, help text and automation id."""
    try:
        from pywinauto.uia_defines import IUIA
        oElement = IUIA().iuia.GetFocusedElement()
        lParts = []
        for sLabel, sProperty in (("name", "CurrentName"), ("kind", "CurrentLocalizedControlType"),
                                  ("help", "CurrentHelpText"), ("id", "CurrentAutomationId")):
            try:
                sValue = getattr(oElement, sProperty) or ""
            except Exception:
                sValue = ""
            if sValue: lParts.append(sLabel + ": " + str(sValue).strip())
        return "; ".join(lParts) or "(nothing has focus)"
    except Exception as exceptionError:
        return "(UI Automation did not answer: " + str(exceptionError) + ")"


# ---- the app's own speech ----

def speechLogFiles(sApp):
    """The app's speech log files, where Say writes what the app said, newest last.

    THE SESSION LOG TOO (9 November 2026). A Homer app writes what it says as "say:" lines in its session log,
    <App>-<date>-<time>.log, kept in %LOCALAPPDATA%\\<App>\\logs and in the project's own logs folder; only a file named
    for speech was looked for, so every step of DbDo's walks reported "nothing in its speech log" though DbDo had
    spoken. Session logs of the last two days are read now, for their say: lines only."""
    lFiles = []
    nRecent = time.time() - 2 * 86400
    for sFolder in (os.path.join(os.environ.get("LOCALAPPDATA", ""), sApp, "logs"), os.path.join(sProject, "logs")):
        lFiles += glob.glob(os.path.join(sFolder, "*peech*"))
        lFiles += [s for s in glob.glob(os.path.join(sFolder, sApp + "-2*.log"))
                   if re.match(re.escape(sApp) + r"-\d{8}-\d{6}\.log$", os.path.basename(s), re.I) and os.path.getmtime(s) >= nRecent]
    return sorted(set(lFiles), key=os.path.getmtime)


def speechSizes(sApp):
    return {s: os.path.getsize(s) for s in speechLogFiles(sApp)}


def speechSince(sApp, dBefore):
    """What the app's speech logs gained since dBefore."""
    lNew = []
    for sPath in speechLogFiles(sApp):
        iFrom = dBefore.get(sPath, 0)
        try:
            with open(sPath, "rb") as fIn:
                fIn.seek(iFrom)
                sText = fIn.read().decode("utf-8", "replace")
            if "peech" not in os.path.basename(sPath):
                # a session log: only what the app said, from its say: lines
                sText = " | ".join(oMatch.group(1).strip() for oMatch in re.finditer(r"\bsay: (.*)", sText, re.I))
            lNew.append(sText.strip())
        except OSError as exceptionError:
            logLine("speech log unreadable: " + sPath + ": " + str(exceptionError))
    return " | ".join(s for s in lNew if s)


# ---- sound ----

def loopbackMicrophone(sWanted):
    """A speaker as a recording source, so the recording is what the computer plays: the screen reader. The default
    speakers, or the first whose name holds sWanted (--speaker). Every output device is named in the log, since
    JAWS may speak through one that is not the default."""
    import soundcard
    lSpeakers = soundcard.all_speakers()
    oDefault = soundcard.default_speaker()
    for oOne in lSpeakers: logLine("sound output: " + oOne.name + (" (the default)" if oOne.name == oDefault.name else ""))
    oSpeaker = oDefault
    if sWanted:
        lMatch = [o for o in lSpeakers if sWanted.lower() in o.name.lower()]
        if lMatch: oSpeaker = lMatch[0]
        else: sayLine("No sound output's name holds " + sWanted + "; recording the default, " + oDefault.name + ".")
    sayLine("Recording what plays on " + oSpeaker.name + ".")
    return soundcard.get_microphone(id=str(oSpeaker.name), include_loopback=True)


def writeWave(sPath, aFrames):
    """Writes recorded frames as 16-bit mono at the recording rate."""
    import numpy
    aMono = aFrames.mean(axis=1) if aFrames.ndim > 1 else aFrames
    aInt = (numpy.clip(aMono, -1.0, 1.0) * 32767).astype(numpy.int16)
    with wave.open(sPath, "wb") as oWave:
        oWave.setnchannels(1); oWave.setsampwidth(2); oWave.setframerate(iSampleRate)
        oWave.writeframes(aInt.tobytes())
    return sPath


def wordsOf(sText):
    return re.findall(r"[a-z0-9]+", (sText or "").lower())


def hearMatch(sExpected, sHeard):
    """How much of an expected line was heard: the share of its words that were heard, each matched to a heard word
    spelled nearly alike. THE RECOGNIZER MISHEARS FAST SPEECH (3 November 2026): at Jamal's JAWS rate it wrote
    "show now" for "shown now", "looks" for "look's" and "rhymes" for "prime's", so exact, in-order matching scored
    3 and 4 lines of 10 on runs where JAWS said every line. A word now counts when a heard word is at least 75%
    alike, and order no longer matters within a step."""
    lWant, lGot = wordsOf(sExpected), wordsOf(sHeard)
    if not lWant: return 1.0
    iFound = 0
    for sWant in lWant:
        if sWant in lGot or any(difflib.SequenceMatcher(None, sWant, sGot).ratio() >= 0.75 for sGot in lGot): iFound += 1
    return iFound / float(len(lWant))


# ---- the run ----

def main():
    global sLogPath
    oParser = argparse.ArgumentParser(description="Drive a Homer app through a walk and record what is said.")
    oParser.add_argument("which", nargs="?", default="", help="a tutorial's number, performed live, or a walk's path")
    oParser.add_argument("--walk", default=os.path.join(sProject, "scripts", "walks", "pilot.inix"))  # the app's own walks
    oParser.add_argument("--app", default=os.path.basename(sProject))
    oParser.add_argument("--steps", type=int, default=0)
    oParser.add_argument("--wait", type=int, default=iDefaultWait)
    oParser.add_argument("--model", default=sDefaultModel)
    oParser.add_argument("--no-transcribe", action="store_true")
    oParser.add_argument("--speaker", default="")
    oParser.add_argument("--keep", action="store_true")
    oParser.add_argument("--axe", action="store_true")      # kept for old command lines; scans are on by default
    oParser.add_argument("--no-axe", action="store_true")
    oParser.add_argument("--tutorial", action="store_true")
    oParser.add_argument("--menus", type=int, default=7)     # with "menus": how many top-level menus to walk
    oParser.add_argument("--items", type=int, default=25)    # with "menus": how many items to walk in each menu and the Alternate Menu
    oArgs = oParser.parse_args([s.lower() if s.startswith("--") else s for s in sys.argv[1:]])

    sLogs = os.path.join(sProject, "logs"); os.makedirs(sLogs, exist_ok=True)
    sLogPath = os.path.join(sLogs, oArgs.app + "-recordWalk-" + sStamp + ".log")
    sReportPath = os.path.join(sLogs, oArgs.app + "-recordWalk-" + sStamp + ".md")
    sWaves = os.path.join(sProject, "results", "recordWalk-" + sStamp); os.makedirs(sWaves, exist_ok=True)
    logLine("recordWalk started: " + os.path.abspath(__file__))
    logLine("Python " + sys.version.replace("\n", " ") + " at " + sys.executable + "; " + platform.platform())
    logLine("working folder " + os.getcwd() + "; command line " + " ".join(sys.argv))
    logLine("settings: app " + oArgs.app + ", walk " + oArgs.walk + ", steps " + str(oArgs.steps) + ", wait " + str(oArgs.wait)
            + ", model " + oArgs.model + ", transcribe " + str(not oArgs.no_transcribe))

    # recordWalk 1 PERFORMS TUTORIAL 1 LIVE (5 November 2026, evening): "recordWalk" alone walks the pilot, and the
    # menu tour needed --tutorial --walk 1, which no one remembers. A number given first is a tutorial, performed live.
    # recordWalk menus WALKS THE MENUS AND THE ALTERNATE MENU (9 November 2026). No walk is written by hand: one is made
    # here, in logs. F10 opens the menu bar and Down Arrow the first menu; Down Arrow then visits each item, and Right
    # Arrow the next menu, for --menus menus of --items items each (a menu shorter than that wraps round, which the
    # report shows as repeats). Escape twice leaves the menus. Alt+F10 opens the Alternate Menu, Down Arrow visits its
    # first --items commands, Home and End reach its ends, and Escape closes it. Each item is one step, heard and logged.
    if oArgs.which.strip().lower() == "menus":
        sMenuWalk = os.path.join(sLogs, oArgs.app + "-menus-" + sStamp + ".inix")
        lLines = ["; written by recordWalk menus, " + sStamp, ""]
        def menuStep(sKey, sSay, iWait=2):
            lLines.extend(["[step]", "Say=" + sSay, "Key=" + sKey, "Wait=" + str(iWait), ""])
        menuStep("F10", "F10, the menu bar.", 3)
        for iMenu in range(1, max(1, oArgs.menus) + 1):
            menuStep("Down", "Menu %d, opened." % iMenu, 3)
            for iItem in range(2, max(2, oArgs.items) + 1):
                menuStep("Down", "Menu %d, item %d." % (iMenu, iItem))
            if iMenu < oArgs.menus:
                menuStep("Escape", "Menu %d, closed." % iMenu)
                menuStep("Right", "The next menu's name.")
        menuStep("Escape", "Leaving the menu.")
        menuStep("Escape", "Leaving the menu bar.")
        menuStep("Alt+F10", "Alt+F10, the Alternate Menu.", 4)
        for iItem in range(2, max(2, oArgs.items) + 1):
            menuStep("Down", "Alternate Menu, command %d." % iItem)
        menuStep("End", "Alternate Menu, the last command.")
        menuStep("Home", "Alternate Menu, the first command.")
        menuStep("Escape", "The Alternate Menu closed.")
        with open(sMenuWalk, "w", encoding="utf-8-sig", newline="\r\n") as fWalk:
            fWalk.write("\n".join(lLines))
        logLine("menu walk written: %s, %d menus of %d items" % (sMenuWalk, oArgs.menus, oArgs.items))
        oArgs.which = sMenuWalk
    if oArgs.which:
        oArgs.walk = oArgs.which
        if oArgs.which.strip().isdigit(): oArgs.tutorial = True
    # A NUMBER NAMES A TUTORIAL, AND A RELATIVE PATH IS THE PROJECT'S (5 November 2026): recordWalk is usually
    # started from the scripts folder, so help\... and 1 are looked for from the project folder.
    if re.match(r"^\d+$", oArgs.walk.strip()):
        lFound = glob.glob(os.path.join(sProject, "help", "Tutorial_" + oArgs.walk.strip() + "_*.inix"))
        if lFound: oArgs.walk = lFound[0]
    if not os.path.isfile(oArgs.walk) and os.path.isfile(os.path.join(sProject, oArgs.walk)):
        oArgs.walk = os.path.join(sProject, oArgs.walk)
    if not os.path.isfile(oArgs.walk):
        sayLine("No walk at " + oArgs.walk + ".")
        return 1
    lSteps = readWalk(oArgs.walk, oArgs.tutorial)
    if oArgs.steps > 0: lSteps = lSteps[:oArgs.steps]
    sayLine("recordWalk: " + str(len(lSteps)) + (" step" if len(lSteps) == 1 else " steps") + " from " + os.path.basename(oArgs.walk) + ".")
    if not ensurePackages(): return 1
    WhisperModel = None if oArgs.no_transcribe else ensureWhisper()
    oModel = None
    if WhisperModel is not None:
        # SAID ONLY WHEN TRUE (6 November 2026): every run said the model is downloaded "the first time", though after
        # the first it loads from its cache in seconds -- and the faster-whisper component fetches it at install.
        sCache = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub", "models--Systran--faster-whisper-" + oArgs.model)
        if os.path.isdir(sCache): sayLine("Loading the recognizer, " + oArgs.model + ".")
        else: sayLine("Getting the recognizer, " + oArgs.model + ", once; this takes a few minutes, and later walks load it in seconds.")
        try:
            oModel = WhisperModel(oArgs.model, device="cpu", compute_type="int8")
        except Exception as exceptionError:
            sayLine("The recognizer did not load, so the steps are recorded but not written down. The log says why.")
            logLine("WhisperModel failed: " + traceback.format_exc())
    sCppExe, sCppModel = ("", "")
    if oModel is None and not oArgs.no_transcribe:
        sCppExe, sCppModel = findWhisperCpp()
        if sCppExe: sayLine("Using HomerScribe's whisper.cpp to write the speech down.")
        else: sayLine("No recognizer could be loaded, so the steps are recorded but not written down.")
    try:
        oMicrophone = loopbackMicrophone(oArgs.speaker)
    except Exception:
        sayLine("The computer's sound could not be recorded. The log says why.")
        logLine("loopback failed: " + traceback.format_exc())
        return 1

    sayLine("Starting in 5 seconds. Keep your hands off the keyboard. To stop, switch to another window.")
    time.sleep(5)
    if not bringForward(oArgs.app):
        sayLine(oArgs.app + " could not be brought to the front, so nothing was pressed.")
        return 1

    from pywinauto.keyboard import send_keys
    iMatched, iChecked = 0, 0
    lsReport.extend(["# recordWalk: " + oArgs.app + ", " + os.path.basename(oArgs.walk), "",
                     "Recorded " + datetime.datetime.now().strftime("%d %B %Y at %H:%M") + ". Each step: the key pressed, what the walk expected, "
                     "what was heard, what UI Automation says has focus, and what " + oArgs.app + " itself said.", ""])
    sIdentity = appIdentity(oArgs.app + ".exe")
    lsReport.extend([sIdentity, ""])
    logLine(sIdentity)
    sAxeCli, iAxeErrors = "", 0
    # EACH WINDOW SCANNED ONCE, BY DEFAULT, AND SAID (5 November 2026, night): the kit's axeWindow scans one window by
    # its handle and speaks every 10 seconds, so a scan never sounds like a hang; --no-axe leaves the scans out.
    if not oArgs.no_axe:
        try:
            sAxeCli = getAxeCli()
            sayLine("Each step is also scanned with Axe.Windows, the engine of Accessibility Insights.")
        except Exception:
            logLine("AxeWindowsCLI not available: " + traceback.format_exc())
            sayLine("AxeWindowsCLI could not be got, so no scans; the log says why.")
    lLive = []
    bAxeStopped = False
    setScanned, lAxeFindings = set(), []
    setLaunch = launchKey(sProject, oArgs.app)
    logLine("launch key: " + ("+".join(sorted(setLaunch)) if setLaunch else "none found"))
    for iIndex, dStep in enumerate(lSteps, 1):
        sExeNow, sTitleNow = foregroundExe()
        # ITS OWN CONSOLE IS NOT A REASON TO STOP (10 November 2026). testSay's run of 9 November stopped at step 97 of
        # 106 because the command prompt running testSay had come to the front. When the window in front is a console
        # -- the one running this walk -- the app is brought back once and the walk goes on; any other window stops it,
        # as before, so keys never go where they were not meant to.
        if sExeNow.lower() != (oArgs.app + ".exe").lower() and sExeNow.lower() in ("cmd.exe", "conhost.exe", "windowsterminal.exe", "openconsole.exe", "python.exe", "py.exe", "powershell.exe", "pwsh.exe"):
            logLine("before step %d the console %s %r was in front; bringing %s back" % (iIndex, sExeNow, sTitleNow, oArgs.app))
            if bringForward(oArgs.app):
                time.sleep(0.5)
                sExeNow, sTitleNow = foregroundExe()
        if sExeNow.lower() != (oArgs.app + ".exe").lower():
            sayLine("Stopped before step " + str(iIndex) + ": " + (sTitleNow or sExeNow or "another window") + " is in front.")
            logLine("stopped: foreground " + sExeNow + " " + repr(sTitleNow))
            break
        # THE APP'S OWN LAUNCH KEY IS NOT PRESSED (5 November 2026, night). Tutorial 1 opens DbDo with Alt+Control+D, its
        # desktop hotkey; recordWalk has already started DbDo, so the key went to Windows Explorer, which took the front,
        # and the walk stopped at step 3. The narration is kept; the key, already done, is not pressed.
        if oArgs.tutorial and dStep["sKey"] and setLaunch and keySet(dStep["sKey"]) == setLaunch:
            logLine("step " + str(iIndex) + ": " + dStep["sKey"] + " is " + oArgs.app + "'s launch key, and it is open already; not pressed")
            try:
                if dStep["sSay"]: lLive.append(speechFrames(dStep["sSay"], 0))
                if dStep["lHear"]: lLive.append(speechFrames(" ".join(dStep["lHear"]), 1))
            except Exception:
                logLine("tutorial voice failed at step " + str(iIndex) + ": " + traceback.format_exc())
            continue
        if oArgs.tutorial:
            try:
                if dStep["sSay"]: lLive.append(speechFrames(dStep["sSay"], 0))
                if not (dStep["sKey"] or dStep["sType"]):
                    if dStep["lHear"]: lLive.append(speechFrames(" ".join(dStep["lHear"]), 1))
                    logLine("step " + str(iIndex) + ": narration only")
                    continue
            except Exception:
                logLine("tutorial voice failed at step " + str(iIndex) + ": " + traceback.format_exc())
                if not (dStep["sKey"] or dStep["sType"]): continue
        iWait = dStep["iWait"] or oArgs.wait
        dBefore = speechSizes(oArgs.app)
        sKeys = keysFor(dStep["sKey"]) if dStep["sKey"] else ""
        logLine("step " + str(iIndex) + ": type " + repr(dStep["sType"]) + ", key " + repr(dStep["sKey"]) + " as " + repr(sKeys) + ", listen " + str(iWait) + " s")
        # LISTEN UNTIL JAWS STOPS, NOT FOR A FIXED TIME (3 November 2026). The recordings of nine walks showed JAWS
        # still speaking when the four-second window closed -- Filter Records, every Escape back to the grid, Order
        # Records -- and the rest spilling into the next step's recording, where it was taken for that step's words.
        # So: before the key, wait for half a second of quiet (up to ten seconds); after it, record until JAWS has been
        # quiet for 0.8 seconds, at most fifteen seconds, and stop at Wait= only if nothing was said at all.
        import numpy
        iChunk = int(iSampleRate * nChunkSeconds)
        def levelOf(aChunk):
            aOne = aChunk.mean(axis=1) if aChunk.ndim > 1 else aChunk
            return float(numpy.sqrt(numpy.mean(numpy.square(aOne)))) if aOne.size else 0.0
        with oMicrophone.recorder(samplerate=iSampleRate) as oRecorder:
            nQuiet, nWaited = 0.0, 0.0
            while nQuiet < nQuietBefore and nWaited < nMaxSettle:
                nLevel = levelOf(oRecorder.record(numframes=iChunk))
                nQuiet = nQuiet + nChunkSeconds if nLevel < nSpeechLevel else 0.0
                nWaited += nChunkSeconds
            if nWaited >= nMaxSettle: logLine("  still sound after %d s of waiting for quiet; pressed anyway" % nMaxSettle)
            if dStep["sType"]: send_keys(escapeText(dStep["sType"]), with_spaces=True, pause=0.05)
            if sKeys: send_keys(sKeys, pause=0.05)
            if sKeys and dStep.get("iPress", 1) >= 2:
                time.sleep(0.25)   # well inside the 1.2 seconds Homer counts as one double press
                send_keys(sKeys, pause=0.05)
            lChunks, nQuiet, nSpoken, nElapsed, bSpoke = [], 0.0, 0.0, 0.0, False
            while True:
                aChunk = oRecorder.record(numframes=iChunk)
                lChunks.append(aChunk)
                nElapsed += nChunkSeconds
                if levelOf(aChunk) >= nSpeechLevel: bSpoke, nQuiet, nSpoken = True, 0.0, nSpoken + nChunkSeconds
                else: nQuiet += nChunkSeconds
                if bSpoke and nQuiet >= nQuietAfter: break
                if not bSpoke and nElapsed >= iWait: break
                if nElapsed >= nMaxListen: break
            aFrames = numpy.concatenate(lChunks)
            bCutOff = bSpoke and nQuiet < nQuietAfter
        logLine("  listened %.2f s; speech %.2f s%s" % (nElapsed, nSpoken, "; STILL SPEAKING at the limit" if bCutOff else ""))
        sWave = writeWave(os.path.join(sWaves, "step%02d.wav" % iIndex), aFrames)
        if oArgs.tutorial: lLive.append(framesToInt16(aFrames))
        # HOW LOUD THE STEP WAS (3 November 2026): a recording of the wrong device is silence, which looks like
        # a reader that said nothing. The peak says which: below about 0.01 nothing was played there.
        aMono = (aFrames.mean(axis=1) if aFrames.ndim > 1 else aFrames).astype(numpy.float32)
        nPeak = float(numpy.abs(aMono).max()) if aMono.size else 0.0
        logLine("  loudness peak %.3f" % nPeak)
        sFocus = focusNow()
        sApp = speechSince(oArgs.app, dBefore)
        sAxe = ""
        # ONE WINDOW AT A TIME, EACH ONCE (5 November 2026, evening). The kit's axeWindow scans the window in front by its
        # handle, through the Axe.Windows library -- a dialog without the record list behind it -- and speaks as it
        # goes: at the start, every 10 seconds, and at the end, between this step's recording and the next. Each window
        # is scanned the first time it is in front; the main window, which may hold a long list, takes longest, and
        # says so. When the library cannot be loaded, the walk says so once and goes on unscanned.
        if sAxeCli and not bAxeStopped:
            try:
                lWindows = windowsOf(oArgs.app + ".exe")
                if lWindows:
                    import axeWindow
                    axeWindow.useLog(logLine)
                    iPid = lWindows[0][1]
                    hWnd = axeWindow.frontWindowOf(iPid)
                    sTitle = axeWindow.windowTitle(hWnd) if hWnd else ""
                    # DIALOGS ONLY (6 November 2026). The 8:56 walk spent seven minutes on DbDo's main window, record
                    # list and all; every push already scans an app's main window, so a walk scans the windows it
                    # opens -- the ones another window owns -- and passes the main window by.
                    if hWnd and not ctypes.windll.user32.GetWindow(hWnd, 4):
                        sAxe = (sTitle or "the main window") + ": the main window, scanned by every push, so not here"
                        hWnd = 0
                    if hWnd and sTitle in setScanned:
                        sAxe = sTitle + " was scanned at an earlier step"
                    elif hWnd:
                        setScanned.add(sTitle)
                        dScan = axeWindow.scanWindow(iPid, hWnd, os.path.join(sWaves, "axe"), "step%02d" % iIndex)
                        if dScan["sProblem"]:
                            sAxe = "no scan of " + (sTitle or "the window") + ": " + dScan["sProblem"]
                            if "could not be loaded" in dScan["sProblem"]:
                                bAxeStopped = True
                                sayLine("Axe.Windows could not be loaded, so the rest of the walk is not scanned; the log says why.")
                        else:
                            iAxeErrors += dScan["iErrors"]
                            lAxeFindings.extend(dScan["lFindings"])
                            sAxe = (str(dScan["iErrors"]) + (" error" if dScan["iErrors"] == 1 else " errors") + " in " + (sTitle or "the window")
                                    + (": " + "; ".join(dScan["lFindings"][:3]) + (" and more" if len(dScan["lFindings"]) > 3 else "") if dScan["lFindings"] else ""))
            except Exception:
                logLine("axe scan failed for step " + str(iIndex) + ": " + traceback.format_exc())
                sAxe = "the scan could not run; the log says why"
        sHeard = ""
        if oModel is not None:
            try:
                # THE SOUND ITSELF, NOT THE FILE (3 November 2026): given a file, faster-whisper opens it with PyAV,
                # and the PyAV pip installs is newer than it expects ("unexpected keyword argument
                # 'metadata_errors'"). Given the samples, 16 kHz mono floats, it needs no decoder at all.
                lSegments, _oInfo = oModel.transcribe(aMono, language="en", vad_filter=True)
                sHeard = " ".join(o.text.strip() for o in lSegments).strip()
            except Exception:
                logLine("transcription failed for step " + str(iIndex) + ": " + traceback.format_exc())
                sHeard = "(not written down: the recognizer failed; the log says why)"
        elif sCppExe:
            try:
                sHeard = transcribeCpp(sCppExe, sCppModel, sWave)
            except Exception:
                logLine("whisper.cpp failed for step " + str(iIndex) + ": " + traceback.format_exc())
        logLine("  heard: " + sHeard)
        logLine("  focus: " + sFocus)
        logLine("  app said: " + sApp)
        lsReport.append("## Step " + str(iIndex) + ": " + (("type " + dStep["sType"] + ", then ") if dStep["sType"] else "") + (dStep["sKey"] or ""))
        lsReport.append("")
        if dStep["sSay"]: lsReport.append("- **Walk says:** " + dStep["sSay"])
        for sWant in dStep["lHear"]:
            nShare = hearMatch(sWant, sHeard + " " + sApp)
            bHeard = nShare >= nMatchNeeded
            iChecked += 1; iMatched += 1 if bHeard else 0
            lsReport.append("- **Expected:** " + sWant + " -- " + ("heard" if bHeard else "NOT HEARD") + " (" + str(int(nShare * 100)) + "% of its words)")
        lsReport.append("- **Heard:** " + (sHeard or "(nothing written down)"))
        lsReport.append("- **Focus:** " + sFocus)
        lsReport.append("- **" + oArgs.app + " said:** " + (sApp or "(nothing in its speech log)"))
        if sAxeCli: lsReport.append("- **Axe.Windows:** " + (sAxe or "(no scan)"))
        lsReport.append("- **Recording:** " + os.path.relpath(sWave, sProject) + ", %.1f s of speech in %.1f s, loudness peak %.3f%s%s" % (nSpoken, nElapsed, nPeak,
                        " -- SILENT: nothing played on the recorded output; try --speaker" if nPeak < 0.01 else "",
                        " -- STILL SPEAKING at %d s, so the end is missing" % nMaxListen if bCutOff else ""))
        lsReport.append("")
        logLine("step " + str(iIndex) + " recorded")
    lsReport.insert(3, "**" + str(iMatched) + " of " + str(iChecked) + " expected lines heard.**")
    lsReport.insert(4, "")
    if sAxeCli: lsReport.insert(5, "**Axe.Windows: " + str(iAxeErrors) + (" error" if iAxeErrors == 1 else " errors") + " across the steps; each .a11ytest file opens in Accessibility Insights for Windows.**\n")
    with open(sReportPath, "w", encoding="utf-8") as fOut: fOut.write("\n".join(lsReport) + "\n")
    if sAxeCli: sayLine("Axe.Windows: " + str(iAxeErrors) + (" error" if iAxeErrors == 1 else " errors") + " across the steps; the report lists them by step.")
    if oArgs.tutorial and lLive:
        try:
            sLive = writeLive(sWaves, oArgs.walk, lLive)
            sayLine("The tutorial, performed live, is " + os.path.relpath(sLive, sProject) + ".")
        except Exception:
            logLine("live recording not written: " + traceback.format_exc())
            sayLine("The live recording could not be written; the log says why.")
    if not oArgs.keep:
        bClosed = closeApp(oArgs.app)
        if not bClosed: sayLine(oArgs.app + " did not close by itself, so it is still open.")
    sayLine("recordWalk is done. " + str(iMatched) + " of " + str(iChecked) + " expected lines heard. The report is " + sReportPath + ".")
    sayLine("Upload the report, the log and the results\\recordWalk-" + sStamp + " folder.")
    iCode = 0 if iMatched == iChecked else 1
    # TUTORIAL 1 LIVE WHEN IT IS DUE (5 November 2026, night): a plain recordWalk also performs Tutorial 1 -- the menus
    # through the real screen reader -- when its live recording is missing, or older than the tutorial or the program,
    # so no argument has to be remembered; it runs as a second pass, with the app started afresh.
    if not oArgs.which and not oArgs.tutorial and os.path.basename(oArgs.walk).lower() == "pilot.inix":
        lTutorial = glob.glob(os.path.join(sProject, "help", "Tutorial_1_*.inix"))
        if lTutorial:
            lLive = glob.glob(os.path.join(sProject, "results", "recordWalk-*", os.path.splitext(os.path.basename(lTutorial[0]))[0] + "-live.*"))
            nLive = max([os.path.getmtime(s) for s in lLive] or [0])
            sExe = os.path.join(sProject, "exec", oArgs.app + ".exe")
            nNewest = max(os.path.getmtime(lTutorial[0]), os.path.getmtime(sExe) if os.path.isfile(sExe) else 0)
            if nLive < nNewest:
                sayLine("Now Tutorial 1, performed live: the menus through the screen reader. Keep your hands off the keyboard.")
                lCommand = [sys.executable, os.path.abspath(__file__), "1"] + (["--no-axe"] if oArgs.no_axe else [])
                logLine("tutorial pass: " + " ".join(lCommand))
                iCode = max(iCode, subprocess.call(lCommand, cwd=os.getcwd()))
            else:
                logLine("Tutorial 1's live recording is current: " + max(lLive, key=os.path.getmtime))
    return iCode


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sayLine("Stopped.")
        sys.exit(1)
    except Exception:
        sayLine("recordWalk stopped on an error; the log has it.")
        logLine("ERROR: " + traceback.format_exc())
        sys.exit(1)
