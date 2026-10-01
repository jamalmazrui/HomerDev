"""renameBuild.py -- give a Homer app's build script its short name, build.cmd.

The folder already names the app, so build<App>.cmd (and build<App>.ps1, when
an app has one) said it twice. Since kit 1.43.55 the build script is build.cmd,
with build.ps1 beside it when the build has a PowerShell half, and the kit's
check fails an app whose script still carries the old name.

Usage:
  renameBuild                 the app in the current folder
  renameBuild C:\\EdSharp ...  the apps named
  renameBuild all             every app beside the kit (a folder with .git and
                              a build<Folder>.cmd)

For each app:
  1. build<App>.cmd and build<App>.ps1 become build.cmd and build.ps1, through
     git mv when the folder is a git repository, so history follows the file.
  2. Every reference to the old names in the app's own text files becomes the
     new one: the build scripts themselves (the .cmd calls the .ps1), the
     installer script, RepoFiles.txt and LocalFiles.txt, accept.inix,
     .gitattributes and .gitignore, and the help documents and their .htm
     pages -- except History.md and History.htm, which
     records what was true at the time.
  3. Each rename and each changed file, with how many references changed, goes
     to logs\\<App>-renameBuild-yyyyMMdd-HHmmss.log in that app's folder.

Nothing is deleted, and a file's encoding, byte order mark and line ends are
kept. Running it again on a renamed app changes nothing.

Exit codes: 0 done, 1 something could not be renamed (the log says what).
"""
import datetime, os, platform, re, subprocess, sys

c_lsTextExtensions = (".cmd", ".bat", ".ps1", ".py", ".iss", ".txt", ".inix", ".md", ".cs", ".js", ".json", ".yml", ".gitattributes", ".gitignore", ".htm")
c_lsSkipFolders = (".git", "exec", "logs", "configs", "data", "node_modules", "__pycache__", "templates")

oLog = None


def logLine(sText):
    sStamp = datetime.datetime.now().astimezone().isoformat(timespec="milliseconds")
    if oLog:
        oLog.write("%s INFO  %s\n" % (sStamp, sText))
        oLog.flush()


def sayLine(sText):
    print(sText)
    logLine(sText)


def startLog(sAppDir, sApp):
    global oLog
    if oLog: oLog.close()
    sLogDir = os.path.join(sAppDir, "logs")
    os.makedirs(sLogDir, exist_ok=True)
    sPath = os.path.join(sLogDir, "%s-renameBuild-%s.log" % (sApp, datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))
    oLog = open(sPath, "w", encoding="utf-8-sig", newline="\r\n")
    logLine("renameBuild start app=%s" % sApp)
    logLine("Script: %s" % os.path.abspath(__file__))
    logLine("Python: %s on %s" % (platform.python_version(), platform.platform()))
    logLine("Folder: %s" % sAppDir)
    logLine("Command line: %s" % " ".join(sys.argv))
    return sPath


def renameFile(sAppDir, sOld, sNew):
    """git mv when under git; a plain rename otherwise. Returns True when done."""
    sOldPath = os.path.join(sAppDir, sOld)
    sNewPath = os.path.join(sAppDir, sNew)
    if os.path.exists(sNewPath) and os.path.normcase(sOldPath) != os.path.normcase(sNewPath):
        sayLine("  %s and %s both exist; %s is left for you to compare." % (sOld, sNew, sOld))
        return False
    if os.path.isdir(os.path.join(sAppDir, ".git")):
        oResult = subprocess.run(["git", "mv", sOld, sNew], cwd=sAppDir, capture_output=True, text=True)
        logLine("RUN git mv %s %s exit=%d %s" % (sOld, sNew, oResult.returncode, (oResult.stdout + oResult.stderr).strip()))
        if oResult.returncode == 0:
            sayLine("  Renamed %s to %s (git mv)." % (sOld, sNew))
            return True
        # Not tracked: a plain rename does it.
    try:
        os.rename(sOldPath, sNewPath)
        sayLine("  Renamed %s to %s." % (sOld, sNew))
        return True
    except OSError as oError:
        sayLine("  Could not rename %s: %s" % (sOld, oError))
        return False


def rewriteReferences(sAppDir, sApp):
    """Replace build<App> with build, as a whole word, in the app's text files."""
    oPattern = re.compile(r"(?<![A-Za-z_])([Bb])uild" + re.escape(sApp) + r"(?![A-Za-z0-9_])", re.IGNORECASE)
    iFiles = 0
    for sDir, lsDirs, lsNames in os.walk(sAppDir):
        lsDirs[:] = [s for s in lsDirs if s.lower() not in c_lsSkipFolders]
        for sName in lsNames:
            if sName.lower() in ("history.md", "history.htm"): continue
            if not sName.lower().endswith(c_lsTextExtensions) and sName.lower() not in (".gitattributes", ".gitignore"): continue
            sPath = os.path.join(sDir, sName)
            try:
                binData = open(sPath, "rb").read()
            except OSError:
                continue
            bBom = binData.startswith(b"\xef\xbb\xbf")
            try:
                sText = binData[3 if bBom else 0:].decode("utf-8")
            except UnicodeDecodeError:
                continue
            sNew, iCount = oPattern.subn(lambda m: m.group(1) + "uild", sText)
            if iCount:
                open(sPath, "wb").write((b"\xef\xbb\xbf" if bBom else b"") + sNew.encode("utf-8"))
                iFiles += 1
                logLine("Changed %s: %d reference(s)" % (os.path.relpath(sPath, sAppDir), iCount))
    return iFiles


def renameApp(sAppDir):
    sAppDir = os.path.abspath(sAppDir)
    sApp = os.path.basename(sAppDir.rstrip("\\/"))
    sLog = startLog(sAppDir, sApp)
    sayLine("%s:" % sApp)
    bOk = True
    bAny = False
    dNames = {s.lower(): s for s in os.listdir(sAppDir)}
    for sExt in (".cmd", ".ps1"):
        sOld = dNames.get(("build" + sApp + sExt).lower())
        if sOld:
            bAny = True
            bOk = renameFile(sAppDir, sOld, "build" + sExt) and bOk
    iFiles = rewriteReferences(sAppDir, sApp)
    if iFiles:
        sayLine("  References to build%s updated in %d file%s." % (sApp, iFiles, "" if iFiles == 1 else "s"))
        bAny = True
    if not bAny:
        sayLine("  Already build.cmd; nothing to change.")
    sayLine("  Log: %s" % sLog)
    logLine("renameBuild end ok=%s" % bOk)
    return bOk


def main():
    lsArgs = sys.argv[1:]
    sKit = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if lsArgs and lsArgs[0].lower() == "all":
        sParent = os.path.dirname(sKit)
        lsApps = []
        for sName in sorted(os.listdir(sParent), key=str.lower):
            sDir = os.path.join(sParent, sName)
            if os.path.normcase(sDir) == os.path.normcase(sKit): continue
            if not os.path.isdir(os.path.join(sDir, ".git")): continue
            lsFiles = [s.lower() for s in os.listdir(sDir)]
            if ("build" + sName + ".cmd").lower() in lsFiles or "build.cmd" in lsFiles:
                lsApps.append(sDir)
    elif lsArgs:
        lsApps = lsArgs
    else:
        lsApps = [os.getcwd()]
    if not lsApps:
        print("No Homer app found to rename.")
        return 0
    bAllOk = True
    for sApp in lsApps:
        if not os.path.isdir(sApp):
            print("%s is not a folder." % sApp)
            bAllOk = False
            continue
        bAllOk = renameApp(sApp) and bAllOk
    print("Done. Build, then push, so git records the rename." if bAllOk else "Done, with problems; the logs say what.")
    return 0 if bAllOk else 1


if __name__ == "__main__":
    sys.exit(main())
