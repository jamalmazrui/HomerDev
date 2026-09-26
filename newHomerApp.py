#!/usr/bin/env python3
"""newHomerApp.py -- start a new Homer Tools app from the HomerDev templates.

Usage (through the wrapper, which is how it is meant to be run):

    newHomerApp                     ask for the app name, write into C:\\<App>
    newHomerApp JobDo               write C:\\JobDo, a C# app
    newHomerApp JobDo --python      write C:\\JobDo, a Python app
    newHomerApp JobDo D:\\Work\\JobDo  write somewhere else

What it writes into the app folder, from Templates\\:

    build<App>.cmd          the build script, compiling from C:\\HomerDev
    help\self.md            the project's private notebook, never pushed
    help\                   where every document goes; ReadMe stays at the top
    <App>_setup.iss         the installer script
    create<App>Repo.cmd     the one-time GitHub bootstrap
    create<App>Repo.ps1
    version.txt             1.0.0
    .gitignore

Nothing already in the folder is overwritten. Every file is written in the
Homer encoding: UTF-8 with a BOM and CRLF line endings, except .cmd and .bat,
which take CRLF and no BOM.

A detailed log is written beside THIS SCRIPT as newHomerApp.log: the
environment, every effective setting, every file written or skipped, and any
traceback. Camel Type throughout.
"""

import datetime
import os
import platform
import sys
import traceback

c_sToken = "_APP_"
c_sLogName = "newHomerApp.log"

sScriptDir = os.path.dirname(os.path.abspath(__file__))
sLogPath = os.path.join(sScriptDir, c_sLogName)
oLog = None


def logLine(sText):
    """Write one line to the log and keep the file flushed."""
    if oLog is None: return True
    oLog.write(sText + "\n")
    oLog.flush()
    return True


def sayLine(sText):
    """Console messages stay short and human; detail belongs in the log."""
    print(sText)
    logLine("CONSOLE: " + sText)
    return True


def readTemplate(sPath):
    """Read a template file, discarding any BOM."""
    return open(sPath, "rb").read().decode("utf-8-sig")


def writeHomer(sPath, sText):
    """UTF-8 with a BOM and CRLF, except .cmd, .bat and version.txt.

    version.txt is read by "set /p" in a batch file and by Inno Setup's
    FileRead, and both would take a byte order mark as part of the number, so
    it goes out bare like a .cmd.
    """
    sBody = sText.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
    bBom = not sPath.lower().endswith((".cmd", ".bat", "version.txt"))
    binData = (("\ufeff" + sBody) if bBom else sBody).encode("utf-8")
    open(sPath, "wb").write(binData)
    logLine("WROTE: %s, %d bytes, bom=%s" % (sPath, len(binData), bBom))
    return True


def main():
    global oLog
    oLog = open(sLogPath, "w", encoding="utf-8")
    logLine("newHomerApp started %s" % datetime.datetime.now().isoformat(" ", "seconds"))
    logLine("Script: %s" % os.path.abspath(__file__))
    logLine("Python: %s" % sys.version.replace("\n", " "))
    logLine("Platform: %s" % platform.platform())
    logLine("Working directory: %s" % os.getcwd())
    logLine("Command line: %s" % " ".join(sys.argv))

    lsWords = [s for s in sys.argv[1:] if s.lower() not in ("--python", "-python", "python")]
    bPython = len(lsWords) < len(sys.argv) - 1
    logLine("Language: %s" % ("Python" if bPython else "C#"))

    sApp = lsWords[0] if len(lsWords) > 0 else ""
    if sApp == "":
        sApp = input("Name of the new app (for example JobDo): ").strip()
    if sApp == "":
        sayLine("No app name was given, so nothing was written.")
        return 1
    for sBad in " \t/\\:*?\"<>|":
        if sBad in sApp:
            sayLine("An app name cannot contain %r." % sBad)
            logLine("ERROR: bad character %r in app name %r" % (sBad, sApp))
            return 1

    sTarget = lsWords[1] if len(lsWords) > 1 else os.path.join("C:\\", sApp)
    if os.name != "nt" and len(lsWords) <= 1:
        sTarget = os.path.join(os.getcwd(), sApp)
    sTemplates = os.path.join(sScriptDir, "Templates")

    logLine("App: %s" % sApp)
    logLine("Target: %s" % sTarget)
    logLine("Templates: %s" % sTemplates)

    if not os.path.isdir(sTemplates):
        sayLine("The Templates folder is missing from the kit.")
        logLine("ERROR: no Templates folder at %s" % sTemplates)
        return 1

    lsScripts = [
        ("_APP_.cs",             sApp + ".cs"),
        ("build_APP_.cmd",       "build" + sApp + ".cmd"),
        ("_APP__setup.iss",      sApp + "_setup.iss"),
        ("create_APP_Repo.cmd",  "create" + sApp + "Repo.cmd"),
        ("create_APP_Repo.ps1",  "create" + sApp + "Repo.ps1"),
        ("version.txt",          "version.txt"),
        ("accept.inix",          "accept.inix"),
        ("gitignore.txt",        ".gitignore"),
        ("self.md",              "help/self.md"),
        ("installOllama.cmd",    "installOllama.cmd"),
        ("installModels.cmd",    "installModels.cmd"),
        ("installScreenReaderSupport.cmd", "installScreenReaderSupport.cmd"),
        ("homerFinish.cmd",      "homerFinish.cmd"),
    ]

    if bPython:
        #  A Python app takes the Python build script instead of the C# one and
        #  writes its source from the Python sample rather than the C# starter.
        lsScripts = [t for t in lsScripts if t[0] not in ("_APP_.cs", "build_APP_.cmd")]
        lsScripts.insert(0, ("build_APP_Py.cmd", "build" + sApp + ".cmd"))

    os.makedirs(sTarget, exist_ok=True)
    iWritten = 0
    iSkipped = 0
    for sFrom, sTo in lsScripts:
        sFromPath = os.path.join(sTemplates, sFrom)
        sToPath = os.path.join(sTarget, sTo)
        if not os.path.exists(sFromPath):
            sayLine("Template missing: %s" % sFrom)
            logLine("ERROR: template missing %s" % sFromPath)
            return 1
        if os.path.exists(sToPath):
            iSkipped += 1
            logLine("SKIPPED, already there: %s" % sToPath)
            continue
        writeHomer(sToPath, readTemplate(sFromPath).replace(c_sToken, sApp))
        iWritten += 1

    sayLine("%d file%s written in %s." % (iWritten, "" if iWritten == 1 else "s", sTarget))
    if iSkipped:
        sayLine("%d file%s left alone, already there." % (iSkipped, "" if iSkipped == 1 else "s"))
    if bPython:
        sayLine("Next: write %s.py -- Templates\\samples\\FruitBasketPy is the worked example --"
                % sApp)
        sayLine("set the AppId and hotkey in %s_setup.iss, then run build%s." % (sApp, sApp))
    else:
        sayLine("Next: fill in runScript() in %s.cs, set the AppId and hotkey in %s_setup.iss, then run build%s."
                % (sApp, sApp, sApp))
    logLine("Finished %s" % datetime.datetime.now().isoformat(" ", "seconds"))
    return 0


if __name__ == "__main__":
    iCode = 1
    try:
        iCode = main()
    except Exception:
        try:
            logLine("TRACEBACK:\n" + traceback.format_exc())
        except Exception:
            pass
        print("Something went wrong. The details are in %s." % sLogPath)
    finally:
        if oLog is not None: oLog.close()
    sys.exit(iCode)
