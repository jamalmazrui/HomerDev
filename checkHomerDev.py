#!/usr/bin/env python3
r"""checkHomerDev.py -- prove the kit still builds, by building with it.

WHY THIS EXISTS, IN THREE FAILURES
==================================

Three releases in a row shipped a fault that no check in the kit could see,
because every check read files and none of them compiled anything:

    1.5.0   Homer.Keys collided with System.Windows.Forms.Keys, so Lbc.cs
            could not override ProcessCmdKey. Nine compiler errors.
    1.6.0   The samples' version.txt had been removed on purpose, and the build
            script still treated a missing one as fatal. Both samples stopped.
    1.8.0   Mdi.cs needs KeyMap.cs, and the build script had KeyMap commented
            out. Nine more compiler errors.

Each was found by the user running a build, which is the wrong person and the
wrong time. A compiler is the only instrument that answers "does this still
work", so this script runs one, three times, from a clean start.

WHAT IT DOES

    0. the environment      what pandoc, python and the compiler actually are
    1. the kit audit        every component present, every file encoded right
    2. clean                remove what previous builds wrote, so nothing passes
                            on a stale executable
    3. build each sample    C#, MDI and Python, with their own scripts
    4. dependencies         every module's REQUIRES line against every build
                            script that includes it
    5. shared tools         whether the copy on the PATH matches the kit's
    6. the programs         uiCheck starts each one and presses the keys
    7. the report           what was verified, what was not, what is uncertain

WHAT IT DOES NOT DO. It does not hear. uiCheck drives each program through UI
Automation -- starting it, sending keys, reading back the same tree a screen
reader reads -- so "somebody has to open it and press the keys" is no longer the
answer. What is still not automated is SPEECH: UI Automation reports that a
control exists and what it is called, not what JAWS said. Every report says so,
and capturing NVDA's speech log is the next step rather than a finished one.

    checkHomerDev             audit, clean, build all three, report
    checkHomerDev --deep      also delete the Python virtual environment, so the
                              next build proves it can build that too (slow)
    checkHomerDev --no-clean  build over whatever is there (fast, weaker)

Writes evidence-kit-<yyyymmdd-hhmmss>.md and checkHomerDev.log beside this
script. Exit code 0 when nothing failed, 1 when something did.
"""

import argparse
import datetime
import glob
import os
import platform
import re
import shutil
import subprocess
import sys
import traceback

# The three samples, and the script that builds each. Lowercase alphabetical by
# sample name, as every list in Homer code is.
c_lSamples = [
    ("FruitBasketCs", "buildFruitBasketCs.cmd", "FruitBasketCs.exe"),
    ("FruitBasketMdiCs", "buildFruitBasketMdiCs.cmd", "FruitBasketMdiCs.exe"),
    ("FruitBasketMdiPy", "buildFruitBasketMdiPy.cmd", "FruitBasketMdiPy.exe"),
    ("FruitBasketPy", "buildFruitBasketPy.cmd", "FruitBasketPy.exe"),
]

# What a build writes and this script removes before building again. The virtual
# environment is not here: rebuilding it costs minutes, so it goes only with
# --deep.
c_lsBuildProducts = ["Version.cs", "build", "dist", "version.py"]

c_sKit = os.path.dirname(os.path.abspath(__file__))
c_sSamples = os.path.join(c_sKit, "Samples")
sLogPath = os.path.join(c_sKit, "checkHomerDev.log")
oLog = None
lsFindings = []          # (sName, sVerdict, sEvidence)


# --- saying things ----------------------------------------------------------

def logLine(sText):
    if oLog is None: return True
    oLog.write(sText + "\n")
    oLog.flush()
    return True


def sayLine(sText=""):
    print(sText)
    logLine("CONSOLE: " + sText)
    return True


def countNoun(iCount, sSingular, sPlural=None):
    if sPlural is None: sPlural = sSingular + "s"
    return "%d %s" % (iCount, sSingular if iCount == 1 else sPlural)


def finding(sName, sVerdict, sEvidence):
    """One check, its verdict, and what the verdict rests on.

    Three verdicts: pass, fail, skip. A skip is never counted as a pass, and its
    evidence says why it could not run.
    """
    lsFindings.append((sName, sVerdict, sEvidence))
    logLine("%-14s %-5s %s" % (sName, sVerdict.upper(), sEvidence))
    return True


def runHere(sCommand, sFolder):
    """Run a command in a folder; log it with its exit code."""
    logLine("RUN (%s): %s" % (sFolder, sCommand))
    try:
        oResult = subprocess.run(sCommand, shell=True, cwd=sFolder,
                                 capture_output=True, text=True, timeout=1800)
    except Exception as oError:
        logLine("RUN FAILED: %s" % oError)
        return (1, str(oError))
    logLine("EXIT: %d" % oResult.returncode)
    sOut = (oResult.stdout or "") + (oResult.stderr or "")
    if sOut: logLine("OUTPUT:\n" + sOut[-4000:])
    return (oResult.returncode, sOut)


# --- 1. the kit audit -------------------------------------------------------

def checkKit():
    """buildHomerDev's own audit: every component present and encoded right."""
    iCode, sOut = runHere("python buildHomerDev.py check", c_sKit)
    if iCode == 0 and "0 problems" in sOut:
        return finding("kit audit", "pass", "buildHomerDev check found 0 problems")
    sFirst = ""
    for sLine in sOut.splitlines():
        if sLine.strip().startswith(("missing:", "empty:")) or "problem" in sLine:
            sFirst = sLine.strip()
            break
    return finding("kit audit", "fail", "buildHomerDev check reported: " + (sFirst or "see the log"))


# --- 2. clean ---------------------------------------------------------------

def cleanSamples(bDeep):
    """Remove what previous builds wrote, so nothing passes on a stale file.

    This is the part that makes the answer mean something. A build that is not
    run still leaves yesterday's executable in the folder, and an existence
    check would call that a pass.
    """
    iRemoved = 0
    lsGone = list(c_lsBuildProducts) + [sExe for sName, sScript, sExe in c_lSamples]
    if bDeep: lsGone.append(".venv")
    for sName in lsGone:
        sPath = os.path.join(c_sSamples, sName)
        try:
            if os.path.isdir(sPath):
                shutil.rmtree(sPath)
                iRemoved += 1
                logLine("REMOVED FOLDER: " + sPath)
            elif os.path.isfile(sPath):
                os.remove(sPath)
                iRemoved += 1
                logLine("REMOVED: " + sPath)
        except Exception as oError:
            logLine("COULD NOT REMOVE %s: %s" % (sPath, oError))
    return finding("clean", "pass", "%s removed before building%s" %
                   (countNoun(iRemoved, "build product"),
                    ", virtual environment included" if bDeep else ""))


# --- 3. build each sample ---------------------------------------------------

def compilerErrors(sName):
    """The error lines from a sample's own build log, which is where they are."""
    sLog = os.path.join(c_sSamples, "build" + sName + ".log")
    lsErrors = []
    try:
        for sLine in open(sLog, "rb").read().decode("utf-8-sig", "replace").splitlines():
            if re.search(r"\berror\b", sLine, re.I): lsErrors.append(sLine.strip())
    except Exception:
        pass
    return lsErrors


def buildSample(sName, sScript, sExe):
    sExePath = os.path.join(c_sSamples, sExe)
    iCode, sOut = runHere('"%s" nobump' % sScript, c_sSamples)
    lsErrors = compilerErrors(sName)
    for sError in lsErrors: logLine("ERROR LINE: " + sError)

    if iCode != 0:
        sWhy = lsErrors[0] if lsErrors else "exit code %d; build%s.log has the detail" % (iCode, sName)
        return finding("build " + sName, "fail", sWhy)
    if not os.path.isfile(sExePath):
        return finding("build " + sName, "fail",
                       "%s returned 0 but produced no %s" % (sScript, sExe))
    iBytes = os.path.getsize(sExePath)
    return finding("build " + sName, "pass",
                   "%s returned 0 and wrote %s (%d bytes)" % (sScript, sExe, iBytes))


# --- 4b. the environment and the shared tools -------------------------------

def checkEnvironment():
    """What the build actually ran with, recorded rather than assumed."""
    lsFound = []
    for sName, lsArgs in [("python", [sys.executable, "--version"]),
                          ("pandoc", ["pandoc", "--version"])]:
        try:
            oResult = subprocess.run(lsArgs, capture_output=True, text=True, timeout=60)
            sFirst = (oResult.stdout or oResult.stderr or "").splitlines()
            lsFound.append("%s %s" % (sName, sFirst[0].strip() if sFirst else "(no version)"))
        except Exception:
            lsFound.append("%s not found" % sName)
    logLine("ENVIRONMENT: " + "; ".join(lsFound))
    return finding("environment", "pass", "; ".join(lsFound))


def checkSharedTools():
    """Is the copy of each tool on the PATH the same as the kit's?

    tagRelease, homerTidy, checkHomerApp, gitPush and gitRelease act on the
    current directory, so one copy on the PATH serves every project -- and an old
    copy on the PATH also serves every project. A release once failed on exactly
    that, with an error naming a file that was never meant to exist. Run
    scripts/installTools to fix what this reports.
    """
    lsStale = []
    iChecked = 0
    for sName in sorted(os.listdir(os.path.join(c_sKit, "Tools"))):
        if not sName.lower().endswith((".cmd", ".ps1", ".py")): continue
        sMine = os.path.join(c_sKit, "Tools", sName)
        try:
            oWhere = subprocess.run(["where", sName], capture_output=True, text=True, timeout=30)
            lsPaths = [s.strip() for s in (oWhere.stdout or "").splitlines() if s.strip()]
        except Exception:
            lsPaths = []
        lsPaths = [s for s in lsPaths if os.path.normcase(s) != os.path.normcase(sMine)]
        if not lsPaths: continue
        iChecked += 1
        try:
            binMine = open(sMine, "rb").read()
            binTheirs = open(lsPaths[0], "rb").read()
        except Exception:
            continue
        if binMine != binTheirs:
            lsStale.append("%s on the PATH (%s) differs from the kit's" % (sName, lsPaths[0]))
    for sLine in lsStale: logLine("STALE TOOL: " + sLine)
    if not iChecked:
        return finding("shared tools", "skip", "0 kit tools are on the PATH")
    if lsStale:
        return finding("shared tools", "fail",
                       "%s out of date; run scripts\\installTools" %
                       countNoun(len(lsStale), "tool"))
    return finding("shared tools", "pass",
                   "%s on the PATH match the kit's copies" % countNoun(iChecked, "tool"))


def checkPrograms():
    """uiCheck: start each program, press the keys, read the tree back."""
    sUi = os.path.join(c_sKit, "Tools", "uiCheck.py")
    if not os.path.isfile(sUi):
        return finding("programs", "skip", "uiCheck is not in Tools")
    if not sys.platform.startswith("win"):
        return finding("programs", "skip",
                       "uiCheck drives Windows programs; this is %s" % sys.platform)
    iCode, sOut = runHere('python "%s" --path "%s"' % (sUi, c_sSamples), c_sKit)
    sSummary = ""
    for sLine in sOut.splitlines():
        if "passed," in sLine: sSummary = sLine.strip()
    if iCode == 0:
        return finding("programs", "pass",
                       sSummary or "uiCheck ran every test and nothing failed")
    return finding("programs", "fail",
                   (sSummary or "uiCheck reported a failure") + "; see evidence-ui in Tools")


# --- 4. the dependency rule -------------------------------------------------

def moduleAssemblies():
    """Every module's ASSEMBLIES line, as a module to list of .dll names.

    A module can need an assembly reference as well as another module, and that
    failure is nastier: csc reports a missing TYPE, so the error points at the
    module rather than at the build script that under-referenced it. DbDo hit
    exactly that on its first build against the kit.
    """
    dNeeds = {}
    for sPath in sorted(glob.glob(os.path.join(c_sKit, "CSharp", "*.cs"))):
        sText = open(sPath, "rb").read().decode("utf-8-sig", "replace")
        oMatch = re.search(r"//\s*ASSEMBLIES:\s*([^\n\r]+)", sText)
        if not oMatch: continue
        lsNeeded = re.findall(r"[\w.]+\.dll", oMatch.group(1))
        if lsNeeded: dNeeds[os.path.basename(sPath)] = lsNeeded
    return dNeeds


def moduleRequirements():
    """Every C# module's REQUIRES line, as a module to list of modules.

    Mdi.cs is the only module with one today. The check exists because that was
    not true a release ago and may not be true a release from now: a module that
    needs another is invisible until a build script leaves one out.
    """
    dNeeds = {}
    for sPath in sorted(glob.glob(os.path.join(c_sKit, "CSharp", "*.cs"))):
        sText = open(sPath, "rb").read().decode("utf-8-sig", "replace")
        oMatch = re.search(r"//\s*REQUIRES:\s*([^\n\r]+)", sText)
        if not oMatch: continue
        lsNeeded = [s.strip().rstrip(".") for s in oMatch.group(1).split(",")]
        dNeeds[os.path.basename(sPath)] = [s for s in lsNeeded if s.lower().endswith(".cs")]
    return dNeeds


def checkDependencies():
    dNeeds = moduleRequirements()
    if not dNeeds:
        return finding("dependencies", "skip", "0 modules declare a REQUIRES line")

    lsBroken = []
    lsScripts = sorted(glob.glob(os.path.join(c_sSamples, "build*.cmd")) +
                       glob.glob(os.path.join(c_sKit, "Templates", "build*.cmd")))
    for sScript in lsScripts:
        sText = open(sScript, "rb").read().decode("utf-8-sig", "replace")
        # Only the lines that actually compile something: a commented line is a
        # module deliberately left out, not a module included.
        lsLive = [s for s in sText.splitlines()
                  if "homerSources=" in s and not s.strip().lower().startswith("rem ")]
        sLive = "\n".join(lsLive)
        for sModule, lsNeeded in sorted(dNeeds.items()):
            if sModule not in sLive: continue
            for sNeeded in lsNeeded:
                if sNeeded not in sLive:
                    lsBroken.append("%s includes %s without %s" %
                                    (os.path.basename(sScript), sModule, sNeeded))
    for sLine in lsBroken: logLine("DEPENDENCY: " + sLine)
    if lsBroken:
        return finding("dependencies", "fail", "%s; each is in the log" %
                       countNoun(len(lsBroken), "build script"))
    dAssemblies = moduleAssemblies()
    for sScript in lsScripts:
        sText = open(sScript, "rb").read().decode("utf-8-sig", "replace")
        lsLive = [s for s in sText.splitlines() if not s.strip().lower().startswith("rem ")]
        sLive = "\n".join(lsLive)
        for sModule, lsDlls in sorted(dAssemblies.items()):
            if sModule not in sLive: continue
            for sDll in lsDlls:
                if sDll not in sLive:
                    lsBroken.append("%s includes %s without referencing %s" %
                                    (os.path.basename(sScript), sModule, sDll))
    for sLine in lsBroken[len(lsBroken):]: pass
    if lsBroken:
        for sLine in lsBroken: logLine("DEPENDENCY: " + sLine)
        return finding("dependencies", "fail", "%s; each is in the log" %
                       countNoun(len(lsBroken), "problem"))
    return finding("dependencies", "pass",
                   "%s declare what they need, in modules and in assemblies, and every build script that includes them has it" %
                   countNoun(len(dNeeds) + len(dAssemblies), "declaration"))


# --- 5. the report ----------------------------------------------------------

def writeReport(bDeep, bCleaned):
    sStamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    sPath = os.path.join(c_sKit, "evidence-kit-%s.md" % sStamp)
    lsPassed = [t for t in lsFindings if t[1] == "pass"]
    lsFailed = [t for t in lsFindings if t[1] == "fail"]
    lsSkipped = [t for t in lsFindings if t[1] == "skip"]

    lsLines = [
        "---",
        'title: "Evidence report: the Homer Development Kit"',
        'date: "%s"' % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "---",
        "",
        "# Evidence report: the Homer Development Kit",
        "",
        "Written by checkHomerDev. Every line below rests on a command that ran,",
        "and the command and its exit code are in checkHomerDev.log.",
        "",
        ("The samples were built from a clean start%s, so nothing here passed on a "
         "file an earlier build had left behind."
         % (" including the Python virtual environment" if bDeep else ""))
        if bCleaned else
        ("The samples were NOT cleaned before building, because --no-clean was "
         "given. A build that did not run leaves its earlier program in place, "
         "so a pass here is weaker than a pass after a clean run."),
        "",
        "## What was verified",
        "",
    ]
    lsLines += ["- **%s** -- %s" % (s, e) for s, v, e in lsPassed] or ["- nothing"]
    lsLines += ["", "## What failed", ""]
    lsLines += ["- **%s** -- %s" % (s, e) for s, v, e in lsFailed] or ["- nothing"]
    lsLines += ["", "## What was not checked", ""]
    lsLines += ["- **%s** -- %s" % (s, e) for s, v, e in lsSkipped] or ["- nothing"]
    lsLines += [
        "",
        "## What remains uncertain",
        "",
        "A compiler answers whether the kit still builds. It answers nothing",
        "below, and a report that did not say so would be worse than none:",
        "",
        "- **What a screen reader says.** uiCheck reads the same tree a reader",
        "  reads, and proves a control is there and named. It does not hear.",
        "  Capturing NVDA's speech log is the next step and is not done.",
        "- **Whether anything untested works.** A program is only as checked as",
        "  its uiTest.inix says it is.",
        "- **Whether the keyboard order is right.** Add order is focus order by",
        "  construction; whether the resulting order is sensible is a judgement.",
        "- **Whether a kit change broke an app outside the kit.** EdSharp,",
        "  FileDir, DbDo and HomerScribe compile against these same modules and",
        "  are not built here. After changing a shared class, build them.",
        "- **Whether the installer works.** No sample has one; the apps do.",
        "",
        "## How to read this",
        "",
        "A check that passed is evidence. A check that was skipped is not a pass,",
        "and it is listed separately for that reason.",
        "",
    ]
    open(sPath, "wb").write(("\ufeff" + "\r\n".join(lsLines)).encode("utf-8"))
    return sPath


def main():
    global oLog
    oParser = argparse.ArgumentParser(description="Prove the kit still builds, by building with it.")
    oParser.add_argument("--deep", action="store_true",
                         help="also delete the Python virtual environment before building")
    oParser.add_argument("--no-clean", action="store_true",
                         help="build over what is there instead of cleaning first")
    dArguments = oParser.parse_args()

    oLog = open(sLogPath, "w", encoding="utf-8")
    logLine("checkHomerDev started %s" % datetime.datetime.now().isoformat(" ", "seconds"))
    logLine("Script: %s" % os.path.abspath(__file__))
    logLine("Python: %s" % sys.version.replace("\n", " "))
    logLine("Platform: %s" % platform.platform())
    logLine("Kit: %s" % c_sKit)
    logLine("Samples: %s" % c_sSamples)
    logLine("Command line: %s" % " ".join(sys.argv))
    logLine("Settings: deep=%s no-clean=%s" % (dArguments.deep, dArguments.no_clean))

    sayLine("Checking the kit in %s" % c_sKit)
    sayLine("This builds all %s, which takes a few minutes." % countNoun(len(c_lSamples), "sample"))
    sayLine()

    checkEnvironment()
    checkKit()
    checkDependencies()
    checkSharedTools()
    if dArguments.no_clean:
        finding("clean", "skip", "asked not to; a stale file could make a build look like a pass")
    else:
        cleanSamples(dArguments.deep)
    for sName, sScript, sExe in c_lSamples:
        sayLine("Building %s..." % sName)
        buildSample(sName, sScript, sExe)

    checkPrograms()

    sReport = writeReport(dArguments.deep, not dArguments.no_clean)
    iPassed = len([t for t in lsFindings if t[1] == "pass"])
    iFailed = len([t for t in lsFindings if t[1] == "fail"])
    iSkipped = len([t for t in lsFindings if t[1] == "skip"])
    sayLine()
    sayLine("%s passed, %s failed, %s not checked." %
            (countNoun(iPassed, "check"), countNoun(iFailed, "check"),
             countNoun(iSkipped, "check")))
    for sName, sVerdict, sEvidence in lsFindings:
        if sVerdict == "fail": sayLine("  failed: %s -- %s" % (sName, sEvidence))
    sayLine("The report is %s." % os.path.basename(sReport))
    logLine("Finished %s" % datetime.datetime.now().isoformat(" ", "seconds"))
    return 1 if iFailed else 0


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
