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
    """Write the footer and let the file go. Safe to call twice."""
    global fileLog
    try:
        if fileLog is None: return False
        line("")
        iSeconds = int((datetime.datetime.now() - dtStarted).total_seconds())
        line("Session ended %s after %d seconds"
             % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), iSeconds))
        fileLog.close()
        fileLog = None
        return True
    except Exception:
        return False


# --- writing ----------------------------------------------------------------

def line(sText=""):
    """One line, exactly as given, with no timestamp and no level."""
    global bWorking
    try:
        if fileLog is None: return False
        fileLog.write((sText or "") + "\n")
        fileLog.flush()
        return True
    except Exception:
        bWorking = False
        return False


def info(sText):
    return _level("INFO", sText)


def warn(sText):
    return _level("WARN", sText)


def error(sText):
    return _level("ERROR", sText)


def _level(sLevel, sText):
    """Stamp the time and the level, so a log can be scanned for ERROR."""
    return line("%s  %-5s  %s" % (datetime.datetime.now().strftime("%H:%M:%S"),
                                  sLevel, sText or ""))


def section(sTitle):
    """A heading, so a long log can be read by its parts."""
    line("")
    line("---- %s ----" % (sTitle or ""))
    return True


def keyValue(sKey, sValue):
    """A setting and its value, which is what answers "what was it set to"."""
    return line("    %-24s = %s" % (sKey or "", sValue or ""))


def command(sCommand, iExitCode):
    """An external program that was run, and what it answered."""
    return _level("INFO" if iExitCode == 0 else "ERROR",
                  "Ran: %s   exit code %d" % (sCommand, iExitCode))


def exception(oError=None):
    """The message AND the traceback, which is the part that saves the evening."""
    try:
        if oError is not None:
            _level("ERROR", "%s: %s" % (type(oError).__name__, oError))
        line(traceback.format_exc().rstrip())
        return True
    except Exception:
        return False


# --- the header block -------------------------------------------------------

def _writeHeader():
    """Everything wanted later that cannot be worked out afterwards."""
    line("%s session log" % sAppName)
    line("Started %s" % dtStarted.strftime("%Y-%m-%d %H:%M:%S"))
    section("Environment")
    keyValue("Version", _appVersion())
    keyValue("Log file", sPath)
    try:
        keyValue("Program", os.path.abspath(sys.argv[0]))
        keyValue("Frozen", str(getattr(sys, "frozen", False)))
        keyValue("Python", sys.version.replace("\n", " "))
        keyValue("Platform", platform.platform())
        keyValue("Working directory", os.getcwd())
        keyValue("Command line", " ".join(sys.argv))
        keyValue("User", os.environ.get("USERNAME", ""))
        keyValue("Machine", platform.node())
    except Exception:
        pass
    return True


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
            info("Removed %d old session log%s, keeping the most recent %d"
                 % (iRemoved, "" if iRemoved == 1 else "s", iKeep))
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
