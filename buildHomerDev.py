#!/usr/bin/env python3
"""buildHomerDev.py -- the build step for the Homer Development Kit.

The kit has no executable of its own, so "building" it means two things:

  1. Convert every .md in the kit to a matching .htm with pandoc, because a
     Homer project ships both forms of every document. When pandoc is missing,
     this script fetches it with winget and tries again.
  2. Check the kit over: every component present, every text file in the Homer
     encoding, every template still carrying its _APP_ token, and no zero-byte
     file anywhere. Anything wrong is reported plainly and fails the build.

Usage (through buildHomerDev.cmd, which is how it is meant to be run):

    buildHomerDev              convert the documents and check the kit
    buildHomerDev check        check only, convert nothing

A detailed log is written beside this script as buildHomerDev.log.
"""

import datetime
import os
import platform
import subprocess
import sys
import traceback

c_lsExpected = [
    "CSharp/Inix.cs", "CSharp/Keys.cs", "CSharp/KeyMap.cs", "CSharp/Lbc.cs",
    "CSharp/PdfRead.cs", "CSharp/Say.cs", "CSharp/Util.cs", "CSharp/Web.cs",
    "CSharp/inixVert.cs",
    "Python/homer/__init__.py", "Python/homer/inix.py", "Python/homer/lbc.py",
    "Python/homer/say.py", "Python/homer/util.py", "Python/homer/version.py",
    "Python/homer/web.py",
    "Templates/build_APP_.cmd", "Templates/_APP__setup.iss", "Templates/_APP_.cs",
    "Templates/installOllama.cmd", "Templates/installModels.cmd",
    "Templates/create_APP_Repo.cmd", "Templates/create_APP_Repo.ps1",
    "Templates/gitignore.txt", "Templates/version.txt",
    "Tools/tagRelease.cmd", "Tools/tagRelease.ps1",
    "Tools/cleanDir.cmd", "Tools/cleanDir.py", "Tools/homerPolicy.py",
    "Tools/tidyRepo.cmd", "Tools/tidyRepo.py",
    "Style/CamelType_CSharp.md", "Style/CamelType_CSharp_Reference.md",
    "Style/CamelType_JAWSScript.md",
    "ReadMe.md", "HomerDev.md", "Developer.md", "Hotkeys.md", "History.md",
    "License.md", "version.txt",
]

c_sLogName = "buildHomerDev.log"
sScriptDir = os.path.dirname(os.path.abspath(__file__))
sLogPath = os.path.join(sScriptDir, c_sLogName)
oLog = None


def logLine(sText):
    if oLog is None: return True
    oLog.write(sText + "\n")
    oLog.flush()
    return True


def sayLine(sText):
    print(sText)
    logLine("CONSOLE: " + sText)
    return True


def runCommand(lsArgs):
    """Run a command, log its exit code and output, return (iCode, sOutput)."""
    logLine("RUN: %s" % " ".join(lsArgs))
    try:
        oResult = subprocess.run(lsArgs, capture_output=True, text=True)
    except Exception as oError:
        logLine("RUN FAILED: %s" % oError)
        return (1, str(oError))
    logLine("EXIT: %d" % oResult.returncode)
    if oResult.stdout: logLine("STDOUT:\n" + oResult.stdout.rstrip())
    if oResult.stderr: logLine("STDERR:\n" + oResult.stderr.rstrip())
    return (oResult.returncode, (oResult.stdout or "") + (oResult.stderr or ""))


def findPandoc():
    """The path to pandoc, fetching it with winget if it is not there yet."""
    iCode, sOut = runCommand(["pandoc", "--version"])
    if iCode == 0: return "pandoc"
    if os.name != "nt":
        logLine("No pandoc and no winget (not Windows), so no conversion.")
        return ""
    sayLine("Pandoc is not here yet. Fetching it.")
    runCommand(["winget", "install", "--id", "JohnMacFarlane.Pandoc",
                "--architecture", "x64", "--scope", "machine",
                "--accept-source-agreements", "--accept-package-agreements",
                "--silent"])
    iCode, sOut = runCommand(["pandoc", "--version"])
    if iCode == 0: return "pandoc"
    logLine("Pandoc is still not on the PATH after the install attempt.")
    return ""


def normalizeHomer(sPath):
    """Put a file into the Homer encoding: UTF-8 with a BOM and CRLF.

    Pandoc writes UTF-8 with no BOM and bare newlines, so its output is fixed
    here rather than left for the check to complain about.
    """
    try:
        sText = open(sPath, "rb").read().decode("utf-8-sig")
    except Exception as oError:
        logLine("NORMALIZE FAILED: %s: %s" % (sPath, oError))
        return False
    sText = sText.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
    bBom = not sPath.lower().endswith((".cmd", ".bat", "version.txt"))
    open(sPath, "wb").write((("\ufeff" + sText) if bBom else sText).encode("utf-8"))
    logLine("NORMALIZED: %s" % sPath)
    return True


def convertDocs(sPandoc):
    """Write a .htm beside every .md in the kit. Returns the number converted."""
    iDone = 0
    for sRoot, lsDirs, lsFiles in os.walk(sScriptDir):
        for sName in sorted(lsFiles):
            if not sName.lower().endswith(".md"): continue
            sMd = os.path.join(sRoot, sName)
            sHtm = os.path.join(sRoot, sName[:-3] + ".htm")
            iCode, sOut = runCommand([sPandoc, "-f", "markdown", "-t", "html5",
                                      "--standalone", "--metadata",
                                      "title=" + sName[:-3], "-o", sHtm, sMd])
            if iCode == 0:
                normalizeHomer(sHtm)
                iDone += 1
            else: sayLine("Pandoc could not convert %s." % sName)
    return iDone


def checkKit():
    """Report anything wrong with the kit. Returns a list of problems."""
    lsProblems = []

    for sRelative in c_lsExpected:
        sPath = os.path.join(sScriptDir, sRelative.replace("/", os.sep))
        if not os.path.exists(sPath):
            lsProblems.append("missing: " + sRelative)
            continue
        if os.path.getsize(sPath) == 0:
            lsProblems.append("empty: " + sRelative)

    # Encoding: every text file UTF-8 with a BOM and CRLF, except .cmd and .bat,
    # which take CRLF and no BOM.
    lsTextExt = (".cs", ".py", ".ps1", ".md", ".htm", ".inix", ".txt", ".iss", ".cmd")
    for sRoot, lsDirs, lsFiles in os.walk(sScriptDir):
        for sName in sorted(lsFiles):
            if not sName.lower().endswith(lsTextExt): continue
            sPath = os.path.join(sRoot, sName)
            sShown = os.path.relpath(sPath, sScriptDir).replace(os.sep, "/")
            if os.path.getsize(sPath) == 0:
                lsProblems.append("empty: " + sShown)
                continue
            binData = open(sPath, "rb").read()
            bBom = binData.startswith(b"\xef\xbb\xbf")
            bWantBom = not sName.lower().endswith((".cmd", ".bat", "version.txt"))
            if bBom != bWantBom:
                lsProblems.append("%s: %s a byte order mark" %
                                  (sShown, "should not have" if bBom else "needs"))
            iLf = binData.count(b"\n")
            iCrLf = binData.count(b"\r\n")
            if iLf != iCrLf:
                lsProblems.append("%s: %d of %d line endings are not CRLF" %
                                  (sShown, iLf - iCrLf, iLf))

    # A template that has lost its token would silently produce a broken app.
    for sName in ["build_APP_.cmd", "_APP__setup.iss", "_APP_.cs",
                  "create_APP_Repo.cmd", "create_APP_Repo.ps1"]:
        sPath = os.path.join(sScriptDir, "Templates", sName)
        if not os.path.exists(sPath): continue
        if "_APP_" not in open(sPath, "rb").read().decode("utf-8-sig"):
            lsProblems.append("Templates/%s no longer carries the _APP_ token" % sName)

    return lsProblems


def main():
    global oLog
    oLog = open(sLogPath, "w", encoding="utf-8")
    logLine("buildHomerDev started %s" % datetime.datetime.now().isoformat(" ", "seconds"))
    logLine("Script: %s" % os.path.abspath(__file__))
    logLine("Python: %s" % sys.version.replace("\n", " "))
    logLine("Platform: %s" % platform.platform())
    logLine("Working directory: %s" % os.getcwd())
    logLine("Command line: %s" % " ".join(sys.argv))

    bCheckOnly = len(sys.argv) > 1 and sys.argv[1].lower() == "check"
    logLine("Check only: %s" % bCheckOnly)

    sVersion = "unknown"
    sVersionPath = os.path.join(sScriptDir, "version.txt")
    if os.path.exists(sVersionPath):
        sVersion = open(sVersionPath, "rb").read().decode("utf-8-sig").strip()
    sayLine("Homer Development Kit %s in %s" % (sVersion, sScriptDir))

    if not bCheckOnly:
        sPandoc = findPandoc()
        if sPandoc == "":
            sayLine("Pandoc is not available, so the .htm files were left as they are.")
        else:
            iDone = convertDocs(sPandoc)
            sayLine("%d document%s converted to HTML." % (iDone, "" if iDone == 1 else "s"))

    lsProblems = checkKit()
    if len(lsProblems) == 0:
        sayLine("0 problems found. The kit is complete.")
        logLine("Finished %s" % datetime.datetime.now().isoformat(" ", "seconds"))
        return 0

    sayLine("%d problem%s found:" % (len(lsProblems), "" if len(lsProblems) == 1 else "s"))
    for sProblem in lsProblems:
        sayLine("  " + sProblem)
    logLine("Finished with problems %s" % datetime.datetime.now().isoformat(" ", "seconds"))
    return 1


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
