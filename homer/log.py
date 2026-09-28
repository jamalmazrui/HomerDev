"""log.py -- part of the shared Homer toolkit.

ONE SESSION, ONE LOG FILE, IN ONE PLACE EVERY HOMER PROGRAM AGREES ON.

    %LOCALAPPDATA%\\<App>\\logs\\<App>-<yyyyMMdd-HHmmss>.log

THIS MODULE AND CSharp\\Log.cs ARE THE SAME CLASS IN TWO LANGUAGES. Same file
name, same folder, same header block, same method names: start, close, line,
info, warn, error, section, keyValue, command, exception, prune, show. A program
in either language leaves a log another person can read without being told which
language wrote it.

The shape was taken from the two implementations that already worked:
HomerScribe's session log in C#, which names a file for the moment the run
began, and HomerView's Python logger, which keeps the last thirty and deletes
the rest. Both had grown the same answer separately, which is the usual sign
that the answer belongs in the kit rather than in an app.

WHY A FILE PER SESSION rather than one file appended to forever. A user who
reports something an hour later still has the log from when it happened, and the
log being read is never the log being written.

WHY %LOCALAPPDATA% rather than beside the program. A program installed under
Program Files cannot write beside its own .exe. The log has to live somewhere
the user owns, and the same folder holds the settings.

WHY SO MUCH DETAIL. Writing a line costs microseconds; not having the line costs
an evening. The log records the environment, every effective setting, every
external command with its exit code, and every error with its full traceback --
and a failure never produces a console message with nothing in the log.

WHAT GOES WHERE. The console gets short, plain sentences for a person. The log
gets everything else. A log line is never spoken.

Usage, which is three calls in the ordinary case:

    from homer import log
    log.start("FruitBasketPy")              # once, at startup
    log.info("Basket loaded, 4 fruits")     # whenever something happens
    log.close()                             # once, on the way out

and, where it helps:

    log.section("Building the dialog")
    log.keyValue("Sort order", sSort)
    log.command("pandoc ReadMe.md", iExitCode)
    log.exception(oError)                   # message and traceback
    log.warn("Pandoc was not found, so no HTML was written")

Nothing here raises. A program whose logging fails should still run, so every
function swallows its own errors and sets log.bWorking to False.
"""

import datetime
import os
import platform
import re
import subprocess
import sys
import traceback

from . import paths

# How many session logs to keep. Thirty reaches back through a few weeks.
c_iKeepLogs = 30

bWorking = False
dtStarted = datetime.datetime.now()
sAppName = ""
sFolder = ""
sPath = ""
fileLog = None


# --- starting and stopping --------------------------------------------------

def start(sAppNameGiven):
    """Open this session's log and write the header block.

    sAppNameGiven decides the folder, so pass the same name the installer uses.
    Call it once, as early as possible: a failure before the log opens is the
    one failure that cannot be explained afterwards.
    """
    global bWorking, dtStarted, fileLog, sAppName, sFolder, sPath
    try:
        sAppName = (sAppNameGiven or "").strip() or "Homer"
        dtStarted = datetime.datetime.now()
        # paths owns the layout, so the log lands where the convention says and
        # nothing here has to know the folder names.
        paths.start(sAppName)
        sFolder = paths.logs()
        sPath = os.path.join(sFolder, "%s-%s.log" % (sAppName, dtStarted.strftime("%Y%m%d-%H%M%S")))
        fileLog = open(sPath, "w", encoding="utf-8-sig")
        bWorking = True
        _writeHeader()
        prune()
        return True
    except Exception:
        bWorking = False
        return False


def close():
    """The last line, with how long the session ran. Safe to call twice."""
    global fileLog
    try:
        if fileLog is None: return False
        _level("INFO", "session end seconds=%.3f" % (datetime.datetime.now() - dtStarted).total_seconds())
        fileLog.close()
        fileLog = None
        return True
    except Exception:
        return False


# --- writing ----------------------------------------------------------------
#
# THE LINE FORMAT (1.43.21), the same as Log.cs writes, one event per line and
# every line stamped:
#
#     2026-09-27T16:30:06.412-07:00 INFO  session start app=urlCheck version=1.12.6 pid=9120
#     2026-09-27T16:30:06.413-07:00 INFO  env python=3.13.15
#     2026-09-27T16:30:07.020-07:00 ERROR run exit=1 ms=607 cmd="npx axe ..."
#     2026-09-27T16:30:07.021-07:00 ERROR | File "urlCheck.py", line 88, in main
#
# ISO 8601 to the millisecond with the UTC offset; the level in five
# characters; the message. Facts are key=value, keys in lower camel case,
# values quoted when they hold a space, a quote or an equals sign (an inner
# quote as \", a final backslash doubled). A line continuing the one above
# starts "| ". No blank lines, no unstamped lines.

def stamp():
    """The time as every Homer log writes it."""
    return datetime.datetime.now().astimezone().isoformat(timespec="milliseconds")


def key(sLabel):
    """Lower camel case from any label: "Log file" -> logFile."""
    lsWords = re.findall(r"[A-Za-z0-9]+", sLabel or "")
    if not lsWords: return "value"
    return lsWords[0][:1].lower() + lsWords[0][1:] + "".join(s[:1].upper() + s[1:] for s in lsWords[1:])


def value(sValue):
    """Bare when it can be, quoted when it must be."""
    s = "" if sValue is None else str(sValue)
    if s and not re.search(r'[\s"=]', s): return s
    s = s.replace('"', '\\"')
    if s.endswith("\\"): s += "\\"
    return '"' + s + '"'


def _level(sLevel, sText):
    """Each line of the text becomes its own stamped line; the ones after the
    first start "| ", so a reader knows they continue the event above."""
    global bWorking
    try:
        if fileLog is None: return False
        sPrefix = "%s %-5s " % (stamp(), sLevel)
        lsOut = []
        for iAt, sOne in enumerate((sText or "").replace("\r\n", "\n").split("\n")):
            if iAt and not sOne.strip(): continue
            lsOut.append(sPrefix + ("| " if iAt else "") + sOne.rstrip())
        fileLog.write("\n".join(lsOut) + "\n")
        fileLog.flush()
        return True
    except Exception:
        bWorking = False
        return False


def line(sText=""):
    """A line of plain text, stamped INFO. A blank line is not written."""
    if not sText: return True
    return _level("INFO", sText)


def info(sText):
    return _level("INFO", sText)


def warn(sText):
    return _level("WARN", sText)


def error(sText):
    return _level("ERROR", sText)


def section(sTitle):
    """A marker, so a long log can be read by its parts."""
    return _level("INFO", "---- %s ----" % (sTitle or ""))


_setFacts = set()


def keyValue(sKey, sValue):
    """A setting and its value as one fact, key=value, written once."""
    sFact = key(sKey) + "=" + value(sValue)
    if sFact in _setFacts: return True
    _setFacts.add(sFact)
    return _level("INFO", "env " + sFact)


def command(sCommand, iExitCode, iMilliseconds=None):
    """An external program that was run, what it answered, and how long it took."""
    sTime = "" if iMilliseconds is None else " ms=%d" % iMilliseconds
    return _level("INFO" if iExitCode == 0 else "ERROR",
                  "run exit=%d%s cmd=%s" % (iExitCode, sTime, value(sCommand)))


def exception(oError=None):
    """The type, the message AND the traceback, every frame on its own line."""
    try:
        sTrace = traceback.format_exc().rstrip()
        if oError is not None:
            return _level("ERROR", "exception type=%s message=%s\n%s"
                          % (type(oError).__name__, value(str(oError)), sTrace))
        return _level("ERROR", "exception\n" + sTrace)
    except Exception:
        return False


# --- the header -------------------------------------------------------------

def _writeHeader():
    """Everything wanted later that cannot be worked out afterwards."""
    _level("INFO", "session start app=%s version=%s pid=%d" % (value(sAppName), value(_appVersion()), os.getpid()))
    keyValue("Log file", sPath)
    try:
        keyValue("Program", os.path.abspath(sys.argv[0]))
        keyValue("Frozen", str(getattr(sys, "frozen", False)))
        keyValue("Python", platform.python_version())
        keyValue("Working directory", os.getcwd())
        keyValue("Arguments", " ".join(sys.argv[1:]))
        keyValue("Windows", windowsVersion())
        keyValue("Process 64-bit", str(sys.maxsize > 2 ** 32))
        keyValue("User", os.environ.get("USERNAME", ""))
        keyValue("Machine", os.environ.get("COMPUTERNAME", platform.node()))
        for sKey, sValue in speechFacts():
            keyValue(sKey, sValue)
    except Exception:
        pass
    return True


def windowsVersion():
    """The Windows actually running, from the registry, worded as Log.cs words it."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as oKey:
            def read(sName):
                try: return str(winreg.QueryValueEx(oKey, sName)[0])
                except OSError: return ""
            sBuild, sUbr, sDisplay = read("CurrentBuild"), read("UBR"), read("DisplayVersion")
        sName = "Windows 11" if sBuild.isdigit() and int(sBuild) >= 22000 else "Windows 10"
        return ("%s %s" % (sName, sDisplay)).strip() + " (10.0.%s%s)" % (sBuild, "." + sUbr if sUbr else "")
    except Exception:
        return platform.platform()


def speechFacts():
    """The screen reader facts Log.cs writes, from the same Windows calls."""
    lFacts = []
    try:
        import ctypes
        bJaws = bool(ctypes.windll.user32.FindWindowW("JFWUI2", None))
        lFacts.append(("jawsRunning", "yes" if bJaws else "no"))
        bFlag = ctypes.c_int(0)
        ctypes.windll.user32.SystemParametersInfoW(70, 0, ctypes.byref(bFlag), 0)
        lFacts.append(("screenReaderFlag", "yes" if bFlag.value else "no"))
    except Exception:
        pass
    return lFacts


def _appVersion():
    """The version the build wrote into version.py, when there is one."""
    try:
        import version
        return getattr(version, "sVersion", "unknown")
    except Exception:
        return "unknown"


# --- housekeeping -----------------------------------------------------------

def prune(iKeep=c_iKeepLogs):
    """Keep the most recent logs and remove the rest, silently."""
    iRemoved = 0
    try:
        lLogs = [os.path.join(sFolder, s) for s in os.listdir(sFolder)
                 if s.startswith(sAppName + "-") and s.lower().endswith(".log")]
        lLogs.sort(key=lambda s: os.path.getmtime(s), reverse=True)
        for sOld in lLogs[iKeep:]:
            try:
                os.remove(sOld)
                iRemoved += 1
            except OSError:
                pass
        if iRemoved:
            info("prune removed=%d kept=%d" % (iRemoved, iKeep))
    except Exception:
        pass
    return iRemoved


def show():
    """Open this session's log in whatever reads a text file."""
    try:
        if not sPath or not os.path.exists(sPath): return False
        os.startfile(sPath)
        return True
    except Exception:
        try:
            subprocess.Popen(["notepad.exe", sPath])
            return True
        except Exception:
            return False
