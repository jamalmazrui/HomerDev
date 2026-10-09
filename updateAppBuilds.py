r"""
updateAppBuilds.py -- bring app build scripts up to the kit's current layout.

Usage (through updateAppBuilds.cmd, from the kit's folder, wherever it is):

    updateAppBuilds                 every app beside the kit that needs it
    updateAppBuilds Jobrise urlFido only these

On 28 September 2026 the kit's libraries moved into exec\CSharp and
exec\Python, and the Python modules came out of the homer package. An app's
build script is its own copy, so until it is replaced it stops with "no kit
found". The newest <App>.zip carries the full current build script; this is
for an app without one, or one not unzipped. It changes only what the move
changed:

    \CSharp\...              -> \exec\CSharp\...
    \homer\log.py, lbc.py    -> \exec\Python\...
    --paths "!homerDev!"     -> --paths "!homerDev!\exec\Python"
    --hidden-import homer.X  -> --hidden-import X  (and the bare "homer" goes)

and in a Python app's own .py files at the top of its folder:

    from homer import a, b   -> import a, b
    homer.log                -> log

Each file changed is copied first into the app's notes folder, which git never
takes, as <file>.<stamp>.bak. Nothing else is touched. A detailed log goes to
<kit>\logs\HomerDev-updateAppBuilds-<stamp>.log. The apps are the folders
beside the kit, on its drive and at its depth (1.46.0).
"""

import datetime, os, re, shutil, sys

c_sStamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
sKit = os.path.dirname(os.path.abspath(__file__))
sLogPath = os.path.join(sKit, "logs", "HomerDev-updateAppBuilds-%s.log" % c_sStamp)
fileLog = None


def logLine(sLevel, sText):
    """One line in the Homer log format."""
    if fileLog is None: return True
    sTime = datetime.datetime.now().astimezone().isoformat(timespec="milliseconds")
    fileLog.write("%s %-5s %s\n" % (sTime, sLevel, sText))
    fileLog.flush()
    return True


def sayLine(sText):
    print(sText)
    logLine("INFO", "CONSOLE: " + sText)
    return True


def updateBuildText(sText):
    """The build script's text with the old kit paths replaced."""
    sText = re.sub(r"(?<!exec)\\CSharp\\", r"\\exec\\CSharp\\", sText)
    sText = re.sub(r'"CSharp\\', r'"exec\\CSharp\\', sText)
    sText = re.sub(r'(Join-Path \$\w+ )"CSharp"', r'\1"exec\\CSharp"', sText)
    sText = re.sub(r"\\homer\\(log|lbc)\.py", r"\\exec\\Python\\\1.py", sText)
    sText = sText.replace('--paths "!homerDev!" ', '--paths "!homerDev!\\exec\\Python" ')
    sText = sText.replace('--paths "!homerDev!\\exec" ', '--paths "!homerDev!\\exec\\Python" ')
    sText = sText.replace('set "hidden=--hidden-import homer"', 'set "hidden="')
    sText = re.sub(r"--hidden-import homer\.(%%\w|\w+)", r"--hidden-import \1", sText)
    sText = re.sub(r"(?m)^\s*--hidden-import homer \^\r?\n", "", sText)
    # kind.py joins the kit tools every app refreshes (1.45.0).
    sText = re.sub(r'(?m)^(set "kitTools=)(?![^"\n]*\bkind\.py\b)([^"\n]*)"', lambda m: m.group(1) + " ".join(sorted((m.group(2) + " kind.cmd kind.py").split(), key=str.lower)) + '"', sText)
    # A WRITTEN-OUT REFRESH LIST (9 October 2026): several apps refresh the kit's tools with "for %%F in (...)" naming
    # each file rather than a kitTools variable; one naming check.py must name kind.py too, since check.py imports it.
    sText = re.sub(r'(?m)^(\s*for %%F in \()((?=[^)\n]*\bcheck\.py\b)(?![^)\n]*\bkind\.py\b)[^)\n]*)(\))', lambda m: m.group(1) + " ".join(sorted((m.group(2) + " kind.cmd kind.py").split(), key=str.lower)) + m.group(3), sText)
    return sText


def updatePythonText(sText):
    """A Python app's source with the homer package taken out of its imports."""
    sText = re.sub(r"(?m)^([ \t]*)from homer import ([\w, ]+?)(\r?)$", r"\1import \2\3", sText)
    sText = re.sub(r"\bhomer\.(elevate|inix|lbc|lbcnet|log|mdi|paths|say|util|web)\b", r"\1", sText)
    return sText


def updateFile(sApp, sPath, fnUpdate):
    """Rewrite one file if it needs it. Returns True when it changed."""
    binData = open(sPath, "rb").read()
    bBom = binData.startswith(b"\xef\xbb\xbf")
    sText = binData[3 if bBom else 0:].decode("utf-8", "replace")
    sNew = fnUpdate(sText)
    if sNew == sText: return False
    sNotes = os.path.join(os.path.dirname(sPath), "notes")
    os.makedirs(sNotes, exist_ok=True)
    sBackup = os.path.join(sNotes, "%s.%s.bak" % (os.path.basename(sPath), c_sStamp))
    shutil.copyfile(sPath, sBackup)
    open(sPath, "wb").write((b"\xef\xbb\xbf" if bBom else b"") + sNew.encode("utf-8"))
    iLines = sum(1 for a, b in zip(sText.split("\n"), sNew.split("\n")) if a != b) + abs(sText.count("\n") - sNew.count("\n"))
    logLine("INFO", 'updated app=%s file="%s" lines=%d backup="%s"' % (sApp, sPath, iLines, sBackup))
    return True



def loadKind():
    """The kit's kind.py (1.45.0): beside this script, or in the kit's scripts
    folder wherever the kit is (1.46.0): the HomerDev variable, then a folder
    named HomerDev above or beside where this runs, at any depth, then one at
    the top of any fixed drive. Without it the project is taken to be an app,
    as every script assumed before there were four kinds."""
    lsDirs = [os.path.dirname(os.path.abspath(__file__)), os.path.join(os.environ.get("HomerDev", ""), "scripts")]
    for sStart in (os.getcwd(), os.path.dirname(os.path.abspath(__file__))):
        sDir = os.path.abspath(sStart)
        while True:
            lsDirs.append(os.path.join(sDir, "scripts"))
            lsDirs.append(os.path.join(sDir, "HomerDev", "scripts"))
            sUp = os.path.dirname(sDir)
            if sUp == sDir: break
            sDir = sUp
    if os.name == "nt":
        import ctypes
        lsDirs += [sLetter + ":\\HomerDev\\scripts" for sLetter in "CDEFGHIJKLMNOPQRSTUVWXYZ"
                   if ctypes.windll.kernel32.GetDriveTypeW(sLetter + ":\\") == 3]
    for sDir in lsDirs:
        if sDir and os.path.isfile(os.path.join(sDir, "kind.py")):
            if sDir not in sys.path: sys.path.insert(0, sDir)
            import kind
            return kind.projectKind
    return lambda sFolder: ("app", "kind.py was not found, so taken to be an app")

def main():
    global fileLog
    os.makedirs(os.path.dirname(sLogPath), exist_ok=True)
    fileLog = open(sLogPath, "w", encoding="utf-8-sig", newline="\r\n")
    logLine("INFO", "updateAppBuilds start pid=%d" % os.getpid())
    logLine("INFO", 'env script="%s" python=%s arguments="%s"' % (os.path.abspath(__file__), sys.version.split()[0], " ".join(sys.argv[1:])))
    sParent = os.path.dirname(sKit)
    lsWanted = [s.lower() for s in sys.argv[1:]]
    iApps = 0
    for sApp in sorted(os.listdir(sParent), key=str.lower):
        sFolder = os.path.join(sParent, sApp)
        if os.path.normcase(sFolder) == os.path.normcase(sKit) or not os.path.isdir(sFolder): continue
        if lsWanted and sApp.lower() not in lsWanted: continue
        # ONLY APPS (1.45.0): a page, a collection or a folder of another kind
        # beside the kit is never touched. Since 1.43.55 the build is build.cmd.
        sKind, sWhy = loadKind()(sFolder)
        if sKind != "app":
            logLine("INFO", 'skipped folder=%s kind=%s reason="%s"' % (sApp, sKind, sWhy))
            continue
        if not (os.path.isfile(os.path.join(sFolder, "build.cmd")) or os.path.isfile(os.path.join(sFolder, "build%s.cmd" % sApp))): continue
        # Only a project under git is an app, unless it is named: a folder left
        # from an idea (C:\\Jobrise, 28 September) is not changed unasked.
        if not lsWanted and not os.path.isdir(os.path.join(sFolder, ".git")):
            logLine("INFO", 'skipped app=%s reason="not a git repository; name it to update it anyway"' % sApp)
            sayLine("%s: skipped, not a git repository. Name it to update it anyway." % sApp)
            continue
        lsChanged = []
        for sName in ("build.cmd", "build.ps1", "build%s.cmd" % sApp, "build%s.ps1" % sApp):
            sPath = os.path.join(sFolder, sName)
            if os.path.isfile(sPath) and updateFile(sApp, sPath, updateBuildText): lsChanged.append(sName)
        for sName in sorted(os.listdir(sFolder)):
            if sName.lower().endswith(".py") and os.path.isfile(os.path.join(sFolder, sName)):
                if updateFile(sApp, os.path.join(sFolder, sName), updatePythonText): lsChanged.append(sName)
        if lsChanged:
            iApps += 1
            sayLine("%s: updated %s." % (sApp, ", ".join(lsChanged)))
    sayLine("%d app%s updated. The old copies are in each app's notes folder." % (iApps, "" if iApps == 1 else "s"))
    logLine("INFO", "updateAppBuilds end apps=%d" % iApps)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as oError:
        import traceback
        logLine("ERROR", "exception type=%s message=\"%s\"\n| %s" % (type(oError).__name__, oError, traceback.format_exc().replace("\n", "\n| ")))
        print("updateAppBuilds failed: %s. The log is %s" % (oError, sLogPath))
        sys.exit(1)
