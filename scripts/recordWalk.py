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

USAGE

    recordWalk                          the walk scripts\walks\pilot.inix, for the app this folder belongs to
    recordWalk --walk C:\path\walk.inix another walk
    recordWalk --steps 3                only the first three steps
    recordWalk --wait 5                 listen five seconds after each key (default 4)
    recordWalk --model base.en          a smaller, faster, less accurate recognizer (default small.en)
    recordWalk --no-transcribe          record and report, and write nothing down
    recordWalk --keep                   leave the app open at the end; by default it is closed, so its closing says the run is over
    recordWalk --speaker Headphones     record the sound output whose name holds Headphones (the log names them all)
    recordWalk --app DbDo               the app, when the folder does not say

Writes logs\<App>-recordWalk-<stamp>.log, logs\<App>-recordWalk-<stamp>.md (the report), and one .wav per
step under results\recordWalk-<stamp>. Exit code 0 when every step was heard as expected, 1 otherwise.
"""

import argparse, ctypes, datetime, difflib, glob, os, platform, re, subprocess, sys, time, traceback, wave

iDefaultWait, iSampleRate, nMatchNeeded = 4, 16000, 0.6
sDefaultModel = "small.en"

sStamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
sScriptDir = os.path.dirname(os.path.abspath(__file__))
sProject = os.path.dirname(sScriptDir)
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

def readWalk(sPath):
    """The walk's steps: a list of dictionaries with sKey, sType, iWait, sSay and lHear."""
    lSteps, dStep = [], None
    with open(sPath, "r", encoding="utf-8-sig") as fWalk:
        for sRaw in fWalk:
            sLine = sRaw.strip()
            if sLine.startswith(";") or not sLine: continue
            if sLine.lower() == "[step]":
                dStep = {"sKey": "", "sType": "", "iWait": 0, "sSay": "", "lHear": []}
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
            elif sName == "wait":
                try: dStep["iWait"] = int(sValue)
                except ValueError: logLine("Wait is not a whole number: " + sValue)
    return [d for d in lSteps if d["sKey"] or d["sType"]]


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
    """The app's speech log files, where Say writes what the app said, newest last."""
    sFolder = os.path.join(os.environ.get("LOCALAPPDATA", ""), sApp, "logs")
    return sorted(glob.glob(os.path.join(sFolder, "*peech*")), key=os.path.getmtime)


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
                lNew.append(fIn.read().decode("utf-8", "replace").strip())
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
    oParser.add_argument("--walk", default=os.path.join(sScriptDir, "walks", "pilot.inix"))
    oParser.add_argument("--app", default=os.path.basename(sProject))
    oParser.add_argument("--steps", type=int, default=0)
    oParser.add_argument("--wait", type=int, default=iDefaultWait)
    oParser.add_argument("--model", default=sDefaultModel)
    oParser.add_argument("--no-transcribe", action="store_true")
    oParser.add_argument("--speaker", default="")
    oParser.add_argument("--keep", action="store_true")
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

    if not os.path.isfile(oArgs.walk):
        sayLine("No walk at " + oArgs.walk + ".")
        return 1
    lSteps = readWalk(oArgs.walk)
    if oArgs.steps > 0: lSteps = lSteps[:oArgs.steps]
    sayLine("recordWalk: " + str(len(lSteps)) + (" step" if len(lSteps) == 1 else " steps") + " from " + os.path.basename(oArgs.walk) + ".")
    if not ensurePackages(): return 1
    WhisperModel = None if oArgs.no_transcribe else ensureWhisper()
    oModel = None
    if WhisperModel is not None:
        sayLine("Loading the recognizer, " + oArgs.model + "; the first time it is downloaded, which takes a few minutes.")
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
    for iIndex, dStep in enumerate(lSteps, 1):
        sExeNow, sTitleNow = foregroundExe()
        if sExeNow.lower() != (oArgs.app + ".exe").lower():
            sayLine("Stopped before step " + str(iIndex) + ": " + (sTitleNow or sExeNow or "another window") + " is in front.")
            logLine("stopped: foreground " + sExeNow + " " + repr(sTitleNow))
            break
        iWait = dStep["iWait"] or oArgs.wait
        dBefore = speechSizes(oArgs.app)
        sKeys = keysFor(dStep["sKey"]) if dStep["sKey"] else ""
        logLine("step " + str(iIndex) + ": type " + repr(dStep["sType"]) + ", key " + repr(dStep["sKey"]) + " as " + repr(sKeys) + ", listen " + str(iWait) + " s")
        with oMicrophone.recorder(samplerate=iSampleRate) as oRecorder:
            if dStep["sType"]: send_keys(escapeText(dStep["sType"]), with_spaces=True, pause=0.05)
            if sKeys: send_keys(sKeys, pause=0.05)
            aFrames = oRecorder.record(numframes=iSampleRate * iWait)
        sWave = writeWave(os.path.join(sWaves, "step%02d.wav" % iIndex), aFrames)
        # HOW LOUD THE STEP WAS (3 November 2026): a recording of the wrong device is silence, which looks like
        # a reader that said nothing. The peak says which: below about 0.01 nothing was played there.
        import numpy
        aMono = (aFrames.mean(axis=1) if aFrames.ndim > 1 else aFrames).astype(numpy.float32)
        nPeak = float(numpy.abs(aMono).max()) if aMono.size else 0.0
        logLine("  loudness peak %.3f" % nPeak)
        sFocus = focusNow()
        sApp = speechSince(oArgs.app, dBefore)
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
        lsReport.append("- **Recording:** " + os.path.relpath(sWave, sProject) + ", loudness peak %.3f%s" % (nPeak, " -- SILENT: nothing played on the recorded output; try --speaker" if nPeak < 0.01 else ""))
        lsReport.append("")
        logLine("step " + str(iIndex) + " recorded")
    lsReport.insert(3, "**" + str(iMatched) + " of " + str(iChecked) + " expected lines heard.**")
    lsReport.insert(4, "")
    with open(sReportPath, "w", encoding="utf-8") as fOut: fOut.write("\n".join(lsReport) + "\n")
    if not oArgs.keep:
        bClosed = closeApp(oArgs.app)
        if not bClosed: sayLine(oArgs.app + " did not close by itself, so it is still open.")
    sayLine("recordWalk is done. " + str(iMatched) + " of " + str(iChecked) + " expected lines heard. The report is " + sReportPath + ".")
    sayLine("Upload the report, the log and the results\\recordWalk-" + sStamp + " folder.")
    return 0 if iMatched == iChecked else 1


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
