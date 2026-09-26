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

A detailed log is written to logs\\HomerDev-build-yyyyMMdd-HHmmss.log,
one file per run, so the log of a run that went wrong is never overwritten
by the run that followed it.
"""

import datetime
import os
import platform
import subprocess
import sys
import traceback

c_lsExpected = [
    "CSharp/Elevate.cs", "CSharp/Inix.cs", "CSharp/KeyName.cs", "CSharp/KeyMap.cs", "CSharp/Lbc.cs",
    "CSharp/Log.cs", "CSharp/Mdi.cs", "CSharp/Paths.cs",
    "CSharp/PdfRead.cs", "CSharp/Say.cs", "CSharp/Util.cs", "CSharp/Web.cs",
    "CSharp/inixVert.cs",
    "homer/__init__.py", "homer/inix.py", "homer/lbc.py", "homer/log.py",
    "homer/mdi.py", "homer/paths.py", "homer/say.py", "homer/util.py", "homer/version.py", "homer/web.py",
    "Templates/build_APP_.cmd", "Templates/build_APP_Py.cmd",
    "Templates/_APP__setup.iss", "Templates/_APP_.cs",
    "Templates/installModels.cmd",
    "scripts/installOllama.cmd", "scripts/installScreenReaderSupport.cmd", "scripts/homerFinish.cmd",
    "Templates/HomerComponents.iss", "scripts/homerInstall.cmd",
    "Templates/create_APP_Repo.cmd", "Templates/create_APP_Repo.ps1",
    "Templates/accept.inix", "Templates/gitignore.txt", "Templates/self.md", "Templates/version.txt",
    "scripts/tagRelease.cmd", "scripts/tagRelease.ps1", "RepoFiles.txt", "LocalFiles.txt",
    "Templates/samples/FruitBasketCs.cs", "Templates/samples/FruitBasketMdiCs.cs",
    "Templates/samples/FruitBasketMdiPy.py", "Templates/samples/FruitBasketPy.py",
    "Templates/samples/accept.inix", "Templates/samples/uiTest.inix",
    "Templates/samples/buildFruitBasketCs.cmd", "Templates/samples/buildFruitBasketMdiCs.cmd",
    "Templates/samples/buildFruitBasketMdiPy.cmd", "Templates/samples/buildFruitBasketPy.cmd", "Templates/samples/version.txt",
    "checkHomerDev.cmd", "checkHomerDev.py", "releaseHomerDev.cmd",
    "scripts/gitPush.cmd", "scripts/gitUnpushed.cmd", "scripts/gitUnpushed.py",
    "scripts/checkHomerApp.cmd", "scripts/checkHomerApp.py", "scripts/uiCheck.cmd", "scripts/uiCheck.py",
    "scripts/homerTidy.cmd", "scripts/homerTidy.py",
    "scripts/buildTutorials.cmd", "scripts/buildTutorials.ps1", "scripts/checkTutorial.cmd", "scripts/checkTutorial.py",
    "scripts/fixEncoding.cmd", "scripts/fixEncoding.py",
    "scripts/makeTutorials.cmd", "scripts/makeTutorials.py",
    "Templates/Tutorial_00_Overview.inix", "Templates/skills/homer-tutorial/SKILL.md",
    "Templates/makeHotkeys.py",
    "Templates/LocalFiles.txt",
    "Templates/_APP_.cmd",
    "help/CamelType_CSharp.md", "help/CamelType_CSharp_Reference.md",
    "help/CamelType_JAWSScript.md",
    "ReadMe.md", "License.md",
    "help/Announce.md", "help/Developer.md", "help/History.md", "help/HomerDev.md",
    "help/FAQ.md", "help/FinishPage.md", "help/Hotkeys.md", "help/Logging.md", "help/Tutorials.md",
    "help/Tutorial_HomerDev.inix",
    "License.md", "version.txt",
]

c_sLogName = "HomerDev-build-%s.log" % datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

# Folders a build makes, which are none of the kit's business. Walking into one
# means auditing thousands of somebody else's files: a virtual environment alone
# holds the whole of PyInstaller. Lowercase alphabetical, as every list in Homer
# code is.
c_lsSkipFolders = [".git", ".venv", "__pycache__", "build", "dist", "exec", "notes", "venv"]

# How many problems to print before saying how many more there are. The log
# always holds every one of them.
c_iShowProblems = 20

# Files a build writes. They are generated on every build, they are in the
# never-pushed list, and auditing their encoding says nothing about the kit.
c_lsGeneratedFiles = ["version.py", "version.cs"]

# Reports a check writes; they are dated, disposable and not part of the kit.
c_sEvidencePrefix = "evidence-"

# The standard document set. ReadMe and License sit at the top of the project;
# every other document lives in help, which is where the Homer layout puts them.
c_lsDocumentsTop = ["License", "ReadMe"]

# The samples, and the script that builds each. One command builds everything,
# so a problem anywhere is found by running one thing rather than four.
c_lsSampleScripts = [
    "buildFruitBasketCs.cmd",
    "buildFruitBasketMdiCs.cmd",
    "buildFruitBasketMdiPy.cmd",
    "buildFruitBasketPy.cmd",
]

# WHERE FILES USED TO BE, AND WHERE THEY ARE NOW.
#
# A zip unarchived over an existing folder adds and replaces; it never deletes.
# So when the kit moves a file, the old copy stays on every machine that had the
# earlier version, and the result is two HomerDev.md files with different
# contents -- which is worse than either.
#
# Telling somebody to delete the old ones by hand is not an answer. A script
# that makes the change is, and this is it: for each pair below, when BOTH the
# old and the new file exist, the old one is removed. Both must exist, so
# nothing is ever deleted without its replacement already in place.
#
# Add a pair here whenever a file moves. Old entries can be dropped once nobody
# could still be carrying that version.
c_lMoved = [
    ("Announce.md", "help/Announce.md"),
    ("Announce.htm", "help/Announce.htm"),
    ("Developer.md", "help/Developer.md"),
    ("Developer.htm", "help/Developer.htm"),
    ("History.md", "help/History.md"),
    ("History.htm", "help/History.htm"),
    ("HomerDev.md", "help/HomerDev.md"),
    ("HomerDev.htm", "help/HomerDev.htm"),
    ("Hotkeys.md", "help/Hotkeys.md"),
    ("Hotkeys.htm", "help/Hotkeys.htm"),
    ("Style/CamelType_CSharp.md", "help/CamelType_CSharp.md"),
    ("Style/CamelType_CSharp.htm", "help/CamelType_CSharp.htm"),
    ("Style/CamelType_CSharp_Reference.md", "help/CamelType_CSharp_Reference.md"),
    ("Style/CamelType_CSharp_Reference.htm", "help/CamelType_CSharp_Reference.htm"),
    ("Style/CamelType_JAWSScript.md", "help/CamelType_JAWSScript.md"),
    ("Style/CamelType_JAWSScript.htm", "help/CamelType_JAWSScript.htm"),
    ("Tutorial_HomerDev.inix", "help/Tutorial_HomerDev.inix"),
    ("Samples/FruitBasketMdi.cs", "Templates/samples/FruitBasketMdiCs.cs"),
    ("Samples/FruitBasketMdi.exe", "Templates/samples/FruitBasketMdiCs.exe"),
    ("Samples/buildFruitBasketMdi.log", "Templates/samples/buildFruitBasketMdiCs.log"),
    ("Samples/buildFruitBasketMdi.cmd", "Samples/buildFruitBasketMdiCs.cmd"),
    ("Tutorials.md", "help/Tutorials.md"),
    ("Tutorials.htm", "help/Tutorials.htm"),
    ("self.md", "help/self.md"),
    ("self.htm", "help/self.htm"),
    ("Samples/FruitBasketCs/FruitBasketCs.cs", "Templates/samples/FruitBasketCs.cs"),
    ("Samples/FruitBasketMdi/FruitBasketMdi.cs", "Templates/samples/FruitBasketMdi.cs"),
    ("Samples/FruitBasketPy/FruitBasketPy.py", "Templates/samples/FruitBasketPy.py"),
    ("Python/homer/inix.py", "homer/inix.py"),
    ("Python/homer/lbc.py", "homer/lbc.py"),
    ("Python/homer/say.py", "homer/say.py"),
    ("Python/homer/util.py", "homer/util.py"),
    ("Python/homer/web.py", "homer/web.py"),
    ("CSharp/Keys.cs", "CSharp/KeyName.cs"),
    # 1.29.0: four files delivered on 24 Sep 2026 under folders the kit never
    # had (Docs, Inno, Scripts) now sit where RepoFiles.txt says kit files go.
    ("Docs/FinishPage.md", "help/FinishPage.md"),
    ("Docs/FinishPage.htm", "help/FinishPage.htm"),
    ("Docs/Logging.md", "help/Logging.md"),
    ("Docs/Logging.htm", "help/Logging.htm"),
    ("Inno/HomerComponents.iss", "Templates/HomerComponents.iss"),
    ("buildHomerDev.log", "buildHomerDev.py"),
    ("Samples/buildFruitBasketCs.log", "Templates/samples/buildFruitBasketCs.cmd"),
    ("Samples/buildFruitBasketMdiCs.log", "Templates/samples/buildFruitBasketMdiCs.cmd"),
    ("Samples/buildFruitBasketMdiPy.log", "Templates/samples/buildFruitBasketMdiPy.cmd"),
    ("Samples/buildFruitBasketPy.log", "Templates/samples/buildFruitBasketPy.cmd"),
    # 1.37.0: Samples shared its first letter with scripts, so the sample programs
    # live under Templates, the folder for what an app starts from.
    ("Samples/FruitBasketCs.cs", "Templates/samples/FruitBasketCs.cs"),
    ("Samples/FruitBasketMdiCs.cs", "Templates/samples/FruitBasketMdiCs.cs"),
    ("Samples/FruitBasketMdiPy.py", "Templates/samples/FruitBasketMdiPy.py"),
    ("Samples/FruitBasketMdiPy.spec", "Templates/samples/FruitBasketMdiPy.spec"),
    ("Samples/FruitBasketPy.py", "Templates/samples/FruitBasketPy.py"),
    ("Samples/FruitBasketPy.spec", "Templates/samples/FruitBasketPy.spec"),
    ("Samples/accept.inix", "Templates/samples/accept.inix"),
    ("Samples/buildFruitBasketCs.cmd", "Templates/samples/buildFruitBasketCs.cmd"),
    ("Samples/buildFruitBasketMdiCs.cmd", "Templates/samples/buildFruitBasketMdiCs.cmd"),
    ("Samples/buildFruitBasketMdiPy.cmd", "Templates/samples/buildFruitBasketMdiPy.cmd"),
    ("Samples/buildFruitBasketPy.cmd", "Templates/samples/buildFruitBasketPy.cmd"),
    ("Samples/uiTest.inix", "Templates/samples/uiTest.inix"),
    ("Samples/version.txt", "Templates/samples/version.txt"),
    # 1.37.0: the shared install scripts are scripts, refreshed into every app,
    # not starters; only installModels.cmd stays a template, naming an app's models.
    ("Templates/installOllama.cmd", "scripts/installOllama.cmd"),
    ("Templates/homerInstall.cmd", "scripts/homerInstall.cmd"),
    ("Templates/installScreenReaderSupport.cmd", "scripts/installScreenReaderSupport.cmd"),
    ("Templates/homerFinish.cmd", "scripts/homerFinish.cmd"),
    # 1.34.0: the kit follows the layout it asks of every app. Tools is scripts.
    ("Tools/buildTutorials.cmd", "scripts/buildTutorials.cmd"),
    ("Tools/buildTutorials.ps1", "scripts/buildTutorials.ps1"),
    ("Tools/checkHomerApp.cmd", "scripts/checkHomerApp.cmd"),
    ("Tools/checkHomerApp.py", "scripts/checkHomerApp.py"),
    ("Tools/gitPush.cmd", "scripts/gitPush.cmd"),
    ("Tools/homerTidy.cmd", "scripts/homerTidy.cmd"),
    ("Tools/homerTidy.py", "scripts/homerTidy.py"),
    ("Tools/makeTutorials.cmd", "scripts/makeTutorials.cmd"),
    ("Tools/makeTutorials.py", "scripts/makeTutorials.py"),
    ("Tools/tagRelease.cmd", "scripts/tagRelease.cmd"),
    ("Tools/tagRelease.ps1", "scripts/tagRelease.ps1"),
    ("Tools/uiCheck.cmd", "scripts/uiCheck.cmd"),
    ("Tools/uiCheck.py", "scripts/uiCheck.py"),
]

# SCRIPTS RETIRED (25 Sep 2026) because their names sounded like another's and
# the other does the job: cleanDir and tidyRepo (with homerPolicy, which only
# tidyRepo read) are homerTidy; gitRelease is tagRelease, which runs the
# checks itself; sayTutorial is buildTutorials; installTools copied tools into
# C:\bin, where they went stale, and every app refreshes its scripts from the
# kit on each build instead. A retired file is deleted when the build finds
# it, and the log says so. One tool per job.
c_lsRetired = [
    "scripts/cleanDir.cmd", "scripts/cleanDir.py", "scripts/gitRelease.cmd", "scripts/homerPolicy.py",
    "scripts/installTools.cmd", "scripts/sayTutorial.cmd", "scripts/sayTutorial.py",
    "scripts/tidyRepo.cmd", "scripts/tidyRepo.py",
    "Tools/cleanDir.cmd", "Tools/cleanDir.py", "Tools/gitRelease.cmd", "Tools/homerPolicy.py",
    "Tools/installTools.cmd", "Tools/sayTutorial.cmd", "Tools/sayTutorial.py",
    "Tools/tidyRepo.cmd", "Tools/tidyRepo.py",
]

# Folders that existed in an earlier layout and hold nothing the kit wants now.
# Removed only when empty, which they are once the pairs above have been applied.
c_lsOldFolders = ["Docs", "Inno", "Python/homer", "Python", "Templates/samples/FruitBasketCs",
                  "Templates/samples/FruitBasketMdi", "Templates/samples/FruitBasketPy", "Samples", "Style", "Tools"]
sScriptDir = os.path.dirname(os.path.abspath(__file__))
sLogPath = os.path.join(sScriptDir, "logs", c_sLogName)
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


def buildSamples():
    """Build every sample, and report each one.

    buildHomerDev is the single command. Somebody who changes a shared class
    should not have to remember four build scripts and the order to run them in,
    and a problem in any of them should surface from the one thing they already
    run. Each script writes its own log beside itself; the failures are named
    here and the detail is there.
    """
    sSamples = os.path.join(sScriptDir, "Templates", "samples")
    if not os.path.isdir(sSamples): return 0
    iFailed = 0
    for sScript in c_lsSampleScripts:
        if not os.path.isfile(os.path.join(sSamples, sScript)): continue
        sName = sScript[5:-4] if sScript.lower().startswith("build") else sScript
        logLine("RUN: %s in %s" % (sScript, sSamples))
        try:
            oResult = subprocess.run('"%s" nobump' % sScript, shell=True, cwd=sSamples,
                                     capture_output=True, text=True, timeout=1800)
            iCode = oResult.returncode
            if oResult.stdout: logLine("STDOUT:\n" + oResult.stdout[-3000:])
            if oResult.stderr: logLine("STDERR:\n" + oResult.stderr[-3000:])
        except Exception as oError:
            logLine("RUN FAILED: %s" % oError)
            iCode = 1
        logLine("EXIT: %d" % iCode)
        if iCode == 0:
            sayLine("Built %s." % sName)
        else:
            iFailed += 1
            sayLine("%s FAILED. Its own log, build%s.log, has the compiler output."
                    % (sName, sName))
    return iFailed


def removeStaleBinCopies():
    """Kit tools once copied into C:\\bin go stale there and run in place of an
    app's own; on 25 Sep 2026 a push and a release ran from such copies. Only
    files bearing a kit tool's name are touched, and each removal is logged."""
    sBin = "C:\\bin"
    if not os.path.isdir(sBin): return True
    lsNames = ["checkHomerApp.cmd", "checkHomerApp.py", "cleanDir.cmd", "cleanDir.py", "gitPush.cmd",
               "gitRelease.cmd", "gitUnpushed.cmd", "gitUnpushed.py", "homerPolicy.py", "homerTidy.cmd",
               "homerTidy.py", "installTools.cmd", "sayTutorial.cmd", "sayTutorial.py", "tagRelease.cmd",
               "tagRelease.ps1", "tidyRepo.cmd", "tidyRepo.py"]
    lsGone = []
    for sName in lsNames:
        sPath = os.path.join(sBin, sName)
        if not os.path.isfile(sPath): continue
        try:
            os.remove(sPath)
            lsGone.append(sName)
            logLine("REMOVED FROM C:\\bin: %s (every app carries its own copy in scripts)" % sName)
        except Exception as oError:
            logLine("COULD NOT REMOVE %s: %s" % (sPath, oError))
            sayLine("C:\\bin\\%s could not be removed: %s" % (sName, oError))
    if lsGone:
        sayLine("Removed from C:\\bin: " + ", ".join(lsGone) + ". Every app carries its own copy in scripts.")
    return True


def buildTutorials():
    """Fetch the shared voices and speak the kit's own tutorials.

    THE KIT'S BUILD IS THE ONE THING THAT DOWNLOADS THE VOICES (25 Sep 2026).
    They live in exec, shared by every Homer app's build, so this is where
    they are fetched -- once -- with -fetch, which an app's build never passes.
    Then any kit tutorial without audio is spoken. The tool logs to
    logs\\HomerDev-tutorials-<stamp>.log; only the outcome is repeated here.
    """
    sTool = os.path.join(sScriptDir, "scripts", "buildTutorials.cmd")
    if not os.path.isfile(sTool):
        logLine("no scripts/buildTutorials.cmd; voices not fetched")
        return False
    # THE TOOL'S OWN LINES REACH THE SCREEN. It names each tutorial as it
    # starts and finishes, and the minutes between are speaking, not a
    # download; capturing them left seven silent minutes on 25 Sep 2026. It
    # keeps its own log in logs, so only the exit code is recorded here.
    sayLine("Fetching any voices not yet in exec, and speaking any tutorial without audio ...")
    logLine("RUN: %s -fetch -build (output on the console; its log is in logs)" % sTool)
    try:
        iCode = subprocess.call(["cmd.exe", "/c", sTool, "-fetch", "-build"])
    except Exception as oError:
        logLine("RUN FAILED: %s" % oError)
        iCode = 1
    logLine("EXIT: %d" % iCode)
    if iCode == 0:
        sayLine("Voices are in exec; tutorials are spoken.")
    else:
        sayLine("The voices or tutorials could not be completed; the tutorials log in logs says why.")
    return iCode == 0


def removeMoved():
    """Delete a file the kit has moved, once its replacement is in place.

    Unarchiving over an existing folder never deletes, so without this a machine
    that had an earlier kit keeps both copies of every document that moved. Two
    files with the same name and different contents is worse than either alone,
    and working out which is which is not the user's job.

    Both the old and the new file must exist before anything is removed, so a
    file is never deleted without its replacement already in place.
    """
    iRemoved = 0
    for sOld, sNew in c_lMoved:
        sOldPath = os.path.join(sScriptDir, sOld.replace("/", os.sep))
        sNewPath = os.path.join(sScriptDir, sNew.replace("/", os.sep))
        # NEVER WHEN BOTH SIDES ARE THE SAME FILE. Windows does not tell
        # "Scripts" from "scripts": on 25 Sep 2026 a pair that had once moved
        # Scripts/homerInstall.cmd to Templates saw the newly delivered
        # scripts/homerInstall.cmd as the old copy and deleted it.
        if os.path.normcase(os.path.abspath(sOldPath)) == os.path.normcase(os.path.abspath(sNewPath)): continue
        if not (os.path.isfile(sOldPath) and os.path.isfile(sNewPath)): continue
        try:
            os.remove(sOldPath)
            iRemoved += 1
            logLine("MOVED: %s is now %s; removed the old copy" % (sOld, sNew))
        except Exception as oError:
            logLine("COULD NOT REMOVE %s: %s" % (sOldPath, oError))

    for sRetired in c_lsRetired:
        sPath = os.path.join(sScriptDir, sRetired.replace("/", os.sep))
        if not os.path.isfile(sPath): continue
        try:
            os.remove(sPath)
            iRemoved += 1
            logLine("RETIRED: %s removed; its job belongs to another script now" % sRetired)
        except Exception as oError:
            logLine("COULD NOT REMOVE %s: %s" % (sPath, oError))

    for sFolder in c_lsOldFolders:
        sPath = os.path.join(sScriptDir, sFolder.replace("/", os.sep))
        try:
            if os.path.isdir(sPath) and not os.listdir(sPath):
                os.rmdir(sPath)
                iRemoved += 1
                logLine("REMOVED EMPTY FOLDER: %s" % sPath)
        except Exception as oError:
            logLine("COULD NOT REMOVE FOLDER %s: %s" % (sPath, oError))

    if iRemoved:
        sayLine("Removed %d file%s left by an earlier layout." %
                (iRemoved, "" if iRemoved == 1 else "s"))
    return iRemoved


def convertDocs(sPandoc):
    """Write a .htm beside every .md in the kit. Returns the number converted."""
    iDone = 0
    for sRoot, lsDirs, lsFiles in os.walk(sScriptDir):
        lsDirs[:] = [s for s in lsDirs if s.lower() not in c_lsSkipFolders]
        # Templates are not documents: Templates\self.md is a starter for a new
        # app, and converting it would leave a stray .htm in the kit.
        if os.path.basename(sRoot).lower() == "templates": continue
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
        lsDirs[:] = [s for s in lsDirs if s.lower() not in c_lsSkipFolders]
        for sName in sorted(lsFiles):
            if sName.lower() in c_lsGeneratedFiles: continue
            if sName.lower().startswith(c_sEvidencePrefix): continue
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
    for sName in ["build_APP_.cmd", "build_APP_Py.cmd", "_APP__setup.iss", "_APP_.cs",
                  "create_APP_Repo.cmd", "create_APP_Repo.ps1"]:
        sPath = os.path.join(sScriptDir, "Templates", sName)
        if not os.path.exists(sPath): continue
        if "_APP_" not in open(sPath, "rb").read().decode("utf-8-sig"):
            lsProblems.append("Templates/%s no longer carries the _APP_ token" % sName)

    return lsProblems


def main():
    global oLog
    if not os.path.isdir(os.path.dirname(sLogPath)): os.makedirs(os.path.dirname(sLogPath))
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

    iSamplesFailed = 0
    if not bCheckOnly:
        sPandoc = findPandoc()
        if sPandoc == "":
            sayLine("Pandoc is not available, so the .htm files were left as they are.")
        else:
            removeMoved()
            iDone = convertDocs(sPandoc)
            sayLine("%d document%s converted to HTML." % (iDone, "" if iDone == 1 else "s"))
        iSamplesFailed = buildSamples()
        buildTutorials()
        removeStaleBinCopies()

    lsProblems = checkKit()
    if len(lsProblems) == 0 and iSamplesFailed == 0:
        sayLine("0 problems found. The kit is complete.")
        logLine("Finished %s" % datetime.datetime.now().isoformat(" ", "seconds"))
        return 0
    if len(lsProblems) == 0:
        sayLine("The kit itself is complete, but %d sample build%s failed."
                % (iSamplesFailed, "" if iSamplesFailed == 1 else "s"))
        logLine("Finished %s" % datetime.datetime.now().isoformat(" ", "seconds"))
        return 1

    sayLine("%d problem%s found:" % (len(lsProblems), "" if len(lsProblems) == 1 else "s"))
    # The console gets the first few; the log gets all of them. A console that
    # scrolls for a minute tells a screen reader user nothing at all.
    for sProblem in lsProblems[:c_iShowProblems]:
        sayLine("  " + sProblem)
    for sProblem in lsProblems[c_iShowProblems:]:
        logLine("PROBLEM: " + sProblem)
    if len(lsProblems) > c_iShowProblems:
        sayLine("  and %d more, all of them in %s." %
                (len(lsProblems) - c_iShowProblems, c_sLogName))
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
