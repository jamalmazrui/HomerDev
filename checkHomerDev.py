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
    6. the programs         with --ui only: uiCheck starts each one and presses
                            the keys
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
    checkHomerDev --ui        also start each sample and press its keys

UICHECK RUNS ONLY WHEN ASKED (1.65.26). It opens every sample's window, which
takes the screen reader's focus in the middle of a build, and build_release runs
this check unattended. So the programs check is reported as not checked unless
--ui is given.

Writes logs\HomerDev-evidence-<yyyymmdd-hhmmss>.md and
logs\HomerDev-checkHomerDev-<stamp>.log. Exit code 0 when nothing failed, 1 when something did.
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
lAllSamples = [
    ("FruitBasketCs", "buildFruitBasketCs.cmd", "FruitBasketCs.exe"),
    ("FruitBasketMdiCs", "buildFruitBasketMdiCs.cmd", "FruitBasketMdiCs.exe"),
    ("FruitBasketMdiPy", "buildFruitBasketMdiPy.cmd", "FruitBasketMdiPy.exe"),
    ("FruitBasketPy", "buildFruitBasketPy.cmd", "FruitBasketPy.exe"),
]

# What a build writes and this script removes before building again. The virtual
# environment is not here: rebuilding it costs minutes, so it goes only with
# --deep.
lsBuildProducts = ["Version.cs", "build", "dist", "version.py"]

sKit = os.path.dirname(os.path.abspath(__file__))
sSamples = os.path.join(sKit, "Templates", "samples")
# THE LOG AND REPORT GO IN logs (1.65.26), like every other script's: written at the top of the kit, a zip of the
# logs folder held nothing to say why the check had failed.
sLogs = os.path.join(sKit, "logs")
sLogPath = os.path.join(sLogs, "HomerDev-checkHomerDev-%s.log" % datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
oLog = None
lsFindings = []          # (sName, sVerdict, sEvidence)


# --- saying things ----------------------------------------------------------

def logLine(sText):
    """One event in the Homer log format (1.43.21), as log.py and Log.cs write:
    an ISO 8601 time with milliseconds and UTC offset, a five-character level,
    then the text; a line continuing the one above starts "| ", and no line is
    blank or unstamped. The level is ERROR or WARN when the text says so."""
    if oLog is None: return True
    import datetime as _datetime
    sText = (sText or "").replace("\r\n", "\n").rstrip("\n")
    if not sText.strip(): return True
    import re as _re
    sLevel = ("ERROR" if _re.search(r"\b(ERROR|FAIL|FAILED)\b", sText)
              else "WARN" if _re.search(r"\bWARN(ING)?\b", sText) else "INFO")
    # A LEADING LEVEL WORD IS THE LEVEL (1.43.33): "WARN: x" is written
    # "WARN  x", not "WARN  WARN: x".
    oLead = _re.match(r"(ERROR|WARN|WARNING)\b:?\s*", sText)
    if oLead: sText = sText[oLead.end():] or sText
    sPrefix = "%s %-5s " % (_datetime.datetime.now().astimezone().isoformat(timespec="milliseconds"), sLevel)
    lsOut = []
    for iAt, sOne in enumerate(sText.split("\n")):
        if iAt and not sOne.strip(): continue
        lsOut.append(sPrefix + ("| " if iAt else "") + sOne.rstrip())
    oLog.write("\n".join(lsOut) + "\n")
    oLog.flush()
    return True

def logValue(sValue):
    """A value as the Homer log format writes it: bare when it can be, quoted
    when it holds a space, a quote or an equals sign."""
    import re as _re
    s = "" if sValue is None else str(sValue)
    if s and not _re.search(r'[\s"=]', s): return s
    s = s.replace('"', '\\"')
    if s.endswith("\\"): s += "\\"
    return '"' + s + '"'


def logFact(sKey, sValue):
    """One environment fact: env key=value."""
    return logLine("env %s=%s" % (sKey, logValue(sValue)))

def logWindows():
    """The Windows actually running, worded as Log.cs and log.py word it:
    "Windows 11 25H2 (10.0.26200.9550)"."""
    try:
        import winreg as _winreg
        with _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as oKey:
            def read(sName):
                try: return str(_winreg.QueryValueEx(oKey, sName)[0])
                except OSError: return ""
            sBuild, sUbr, sDisplay = read("CurrentBuild"), read("UBR"), read("DisplayVersion")
        sName = "Windows 11" if sBuild.isdigit() and int(sBuild) >= 22000 else "Windows 10"
        return ("%s %s" % (sName, sDisplay)).strip() + " (10.0.%s%s)" % (sBuild, "." + sUbr if sUbr else "")
    except Exception:
        import platform as _platform
        return _platform.platform()




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
    """build's own audit: every component present and encoded right."""
    iCode, sOut = runHere("python build.py check", sKit)
    if iCode == 0 and "0 problems" in sOut:
        return finding("kit audit", "pass", "build check found 0 problems")
    sFirst = ""
    for sLine in sOut.splitlines():
        if sLine.strip().startswith(("missing:", "empty:")) or "problem" in sLine:
            sFirst = sLine.strip()
            break
    return finding("kit audit", "fail", "build check reported: " + (sFirst or "see the log"))


# --- 2. clean ---------------------------------------------------------------

def cleanSamples(bDeep, setBuilding=None):
    """Remove what previous builds wrote, so nothing passes on a stale file.

    This is the part that makes the answer mean something. A build that is not
    run still leaves yesterday's executable in the folder, and an existence
    check would call that a pass.
    """
    iRemoved = 0
    # Only what is about to be built (12 October 2026): a sample the cache calls current keeps its program, and the
    # shared build products go only when something will be built to make them again.
    lSamples = [t for t in lAllSamples if setBuilding is None or t[0] in setBuilding]
    lsGone = (list(lsBuildProducts) if lSamples else []) + [sExe for sName, sScript, sExe in lSamples]
    if bDeep: lsGone.append(".venv")
    for sName in lsGone:
        sPath = os.path.join(sSamples, sName)
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
    """The error lines from a sample's own build log, which is where they are: the newest <Name>-build-<stamp>.log in the
    kit's logs (1.65.31). This read Templates\\samples\\build<Name>.log, a name no build writes any more, so a sample
    that failed to compile never had its errors reported."""
    lsLogs = sorted(glob.glob(os.path.join(sKit, "logs", sName + "-build-*.log")))
    sLog = lsLogs[-1] if lsLogs else ""
    lsErrors = []
    try:
        for sLine in open(sLog, "rb").read().decode("utf-8-sig", "replace").splitlines():
            if re.search(r"\berror\b", sLine, re.I): lsErrors.append(sLine.strip())
    except Exception:
        pass
    return lsErrors


def buildSample(sName, sScript, sExe):
    sExePath = os.path.join(sSamples, sExe)
    iCode, sOut = runHere('"%s" nobump' % sScript, sSamples)
    lsErrors = compilerErrors(sName)
    for sError in lsErrors: logLine("ERROR LINE: " + sError)

    if iCode != 0:
        sWhy = lsErrors[0] if lsErrors else "exit code %d; %s-build-<stamp>.log in logs has the detail" % (iCode, sName)
        return finding("build " + sName, "fail", sWhy)
    if not os.path.isfile(sExePath):
        return finding("build " + sName, "fail",
                       "%s returned 0 but produced no %s" % (sScript, sExe))
    iBytes = os.path.getsize(sExePath)
    recordSample(sName, sScript, sExe)
    return finding("build " + sName, "pass",
                   "%s returned 0 and wrote %s (%d bytes)" % (sScript, sExe, iBytes))


def recordSample(sName, sScript, sExe):
    """THE CHECK'S BUILDS COUNT AS BUILDS (1.68.2). This check builds every sample from clean, and a compiler stamps
    each program with the time, so the program it leaves differs byte for byte from the one the build recorded. The
    build then saw "FruitBasketCs.exe changed since it was made" and rebuilt all four, every cycle, with nothing
    changed. A sample this check builds is now recorded in the same cache, with the build's own list of what a sample
    is made from, so the build and the check agree on what is current."""
    try:
        sys.path.insert(0, sKit)
        sys.path.insert(0, os.path.join(sKit, "scripts"))
        import build, fingerprint
        oCache = fingerprint.Cache(sKit, logLine)
        sPrint = oCache.fingerprint(build.sampleInputs(sName, sScript))
        oCache.record("sample " + sName, sPrint, ["Templates/samples/" + sExe])
        logLine("recorded sample %s as built, so the next build need not build it again" % sName)
    except Exception as oError:
        logLine("sample %s not recorded, so the next build builds it again: %s" % (sName, oError))
    return True


def currentSamples():
    """The samples the shared cache calls current: built from exactly these inputs, and their programs untouched since
    that build passed. Their names, and when each was built. (12 October 2026: this check rebuilt all four from clean
    every cycle -- the ordinary build bumps the kit's version, so the check's own pass never matched -- although the
    build had just confirmed each one.)"""
    dCurrent = {}
    try:
        sys.path.insert(0, sKit)
        sys.path.insert(0, os.path.join(sKit, "scripts"))
        import build, fingerprint
        oCache = fingerprint.Cache(sKit, logLine)
        for sName, sScript, sExe in lAllSamples:
            sPrint = oCache.fingerprint(build.sampleInputs(sName, sScript))
            if oCache.isCurrent("sample " + sName, sPrint, ["Templates/samples/" + sExe]):
                dCurrent[sName] = oCache.d["jobs"]["sample " + sName].get("when", "?")
    except Exception as oError:
        logLine("the sample cache could not be read, so every sample is built: %s" % oError)
    return dCurrent


# --- 4b. the environment and the shared tools -------------------------------

def checkEnvironment():
    """What the build actually ran with, recorded rather than assumed."""
    lsFound = []
    try:
        oResult = subprocess.run([sys.executable, "--version"], capture_output=True, text=True, timeout=60)
        sFirst = (oResult.stdout or oResult.stderr or "").splitlines()
        lsFound.append("python %s" % (sFirst[0].strip() if sFirst else "(no version)"))
    except Exception:
        lsFound.append("python not found")
    # PANDOC AS A BUILD WILL CHOOSE IT (1.56.0): the newest copy anywhere, from
    # exec\Python\media.py, not merely the first on the PATH. Every copy and its
    # version go to the log, and an older copy ahead of it on the PATH is named,
    # since other programs that run pandoc by name still get that one.
    try:
        sPython = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exec", "Python")
        if sPython not in sys.path: sys.path.insert(0, sPython)
        import media
        sPandoc = media.pandocProgram()
        for sLine in media.searchLog().splitlines(): logLine(sLine)
        lsFound.append("pandoc %s at %s" % (media.dLast.get("version", ""), sPandoc) if sPandoc else "pandoc not found")
        if media.shadowNote(): lsFound.append(media.shadowNote())
    except Exception as oError:
        lsFound.append("pandoc not checked: %s" % oError)
    logLine("ENVIRONMENT: " + "; ".join(lsFound))
    return finding("environment", "pass", "; ".join(lsFound))


def checkSharedTools():
    """Is an older copy of a kit tool sitting on the PATH?

    release, tidy, check and push act on the current
    directory, and every app carries its own copies in scripts, refreshed from
    the kit by its build. So a copy anywhere on the PATH -- C:\\bin was the
    place -- is one that will go stale and run instead of the app's own. A
    release once failed on exactly that. This reports every such copy; the
    fix is to delete it.
    """
    lsStale = []
    sScripts = os.path.join(sKit, "scripts")
    for sName in sorted(os.listdir(sScripts)):
        if not sName.lower().endswith((".cmd", ".ps1", ".py")): continue
        sMine = os.path.join(sScripts, sName)
        try:
            oWhere = subprocess.run(["where", sName], capture_output=True, text=True, timeout=30)
            lsPaths = [s.strip() for s in (oWhere.stdout or "").splitlines() if s.strip()]
        except Exception:
            lsPaths = []
        for sPath in lsPaths:
            if os.path.normcase(sPath) == os.path.normcase(sMine): continue
            if os.path.normcase(sPath).startswith(os.path.normcase(sKit)): continue
            lsStale.append("%s is on the PATH at %s" % (sName, sPath))
    for sLine in lsStale: logLine("COPY ON THE PATH: " + sLine)
    if lsStale:
        return finding("shared tools", "fail",
                       "%s on the PATH will go stale; delete: %s" %
                       (countNoun(len(lsStale), "copy", "copies"), "; ".join(lsStale)))
    return finding("shared tools", "pass", "no kit tool is on the PATH outside the kit")


def checkPrograms(bUi):
    """uiCheck: start each program, press the keys, read the tree back -- only when --ui asks for it."""
    if not bUi:
        return finding("programs", "skip",
                       "not run: uiCheck opens each sample's window, which takes the screen reader's focus; "
                       "run checkHomerDev --ui to drive them")
    # uiCheck moved to scripts with the rest of the kit's tools; looking in the retired Tools folder skipped this check
    # on every run (1.62.5, from an audit by another AI).
    sUi = os.path.join(sKit, "scripts", "uiCheck.py")
    if not os.path.isfile(sUi):
        return finding("programs", "fail", "uiCheck is not in scripts, so the sample programs were not driven")
    if not sys.platform.startswith("win"):
        return finding("programs", "skip",
                       "uiCheck drives Windows programs; this is %s" % sys.platform)
    iCode, sOut = runHere('"%s" "%s" --path "%s"' % (sys.executable, sUi, sSamples), sKit)
    sSummary = ""
    for sLine in sOut.splitlines():
        if "passed," in sLine: sSummary = sLine.strip()
    if iCode == 0:
        return finding("programs", "pass",
                       sSummary or "uiCheck ran every test and nothing failed")
    return finding("programs", "fail",
                   (sSummary or "uiCheck reported a failure") + "; see the uiCheck log and evidence-ui report in logs")


# --- 4. the dependency rule -------------------------------------------------

def moduleAssemblies():
    """Every module's ASSEMBLIES line, as a module to list of .dll names.

    A module can need an assembly reference as well as another module, and that
    failure is nastier: csc reports a missing TYPE, so the error points at the
    module rather than at the build script that under-referenced it. DbDo hit
    exactly that on its first build against the kit.
    """
    dNeeds = {}
    for sPath in sorted(glob.glob(os.path.join(sKit, "exec", "CSharp", "*.cs"))):
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
    for sPath in sorted(glob.glob(os.path.join(sKit, "exec", "CSharp", "*.cs"))):
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
    lsScripts = sorted(glob.glob(os.path.join(sSamples, "build*.cmd")) +
                       glob.glob(os.path.join(sKit, "Templates", "build*.cmd")))
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

# The samples this run did not build, with when their last build passed: the report says what happened, not what a
# fresh run would have done (13 October 2026, from an audit: it said "built from a clean start" about samples reused
# from the day before).
dReusedSamples = {}
sReusedRun = ""   # when the whole check was reused, the time of the pass it reuses


def samplesSentence(bDeep):
    # A REUSED CHECK BUILT NOTHING (13 October 2026): it leaves before the samples are looked at, so the list above was
    # empty and the sentence fell back to "built from a clean start" -- the very claim it was written to stop.
    if sReusedRun:
        return ("No sample was built in this run: the whole check was reused from its pass at %s, which recorded how its "
                "samples were built. checkHomerDev --fresh builds them all again." % sReusedRun)
    iAll, iReused = len(lAllSamples), len(dReusedSamples)
    sEarliest = min(dReusedSamples.values())[:10] if dReusedSamples else ""
    if iReused == 0:
        return ("The samples were built from a clean start%s, so nothing here passed on a file an earlier build had left behind."
                % (" including the Python virtual environment" if bDeep else ""))
    if iReused == iAll:
        return ("No sample was built in this run: each is unchanged since its last clean build passed, the earliest on %s. "
                "checkHomerDev --fresh builds them all again." % sEarliest)
    return ("%s built from a clean start in this run; %s not, being unchanged since %s last clean build passed, the earliest on %s."
            % (countNoun(iAll - iReused, "sample was", "samples were"), countNoun(iReused, "was", "were"), "its" if iReused == 1 else "their", sEarliest))


def writeReport(bDeep, bCleaned):
    sStamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    sPath = os.path.join(sLogs, "HomerDev-evidence-%s.md" % sStamp)
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
        "and the command and its exit code are in %s." % os.path.basename(sLogPath),
        "",
        samplesSentence(bDeep)
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
    oParser.add_argument("--ui", action="store_true",
                         help="also start each sample program and press its keys through UI Automation")
    oParser.add_argument("--fresh", action="store_true",
                         help="run every check even when a pass with exactly these inputs is on record")
    oParser.add_argument("--no-clean", action="store_true",
                         help="build over what is there instead of cleaning first")
    dArguments = oParser.parse_args()

    os.makedirs(sLogs, exist_ok=True)
    oLog = open(sLogPath, "w", encoding="utf-8")
    logLine("checkHomerDev start pid=%d" % os.getpid())
    logFact("script", os.path.abspath(__file__))
    logFact("python", platform.python_version())
    logFact("windows", logWindows())
    logLine("Kit: %s" % sKit)
    logLine("Samples: %s" % sSamples)
    logFact("arguments", " ".join(sys.argv[1:]))
    logLine("settings deep=%s no-clean=%s" % (dArguments.deep, dArguments.no_clean))

    # A PASS IS REUSED FOR THE SAME INPUTS (1.65.34). push and release both run this check, and each built all four
    # samples from clean -- a minute and more of the same work, twice a cycle, with nothing changed between. The kit's
    # inputs are fingerprinted (its templates, shared code, scripts, this checker and the version, build products
    # left out); a pass recorded with the same fingerprint is reused, and the report says so. --fresh, --ui, --deep
    # and --no-clean always run in full; a failure is never reused.
    sys.path.insert(0, os.path.join(sKit, "scripts"))
    import fingerprint
    oCache = fingerprint.Cache(sKit, logLine)
    lsInputs = ["Templates", "exec/CSharp", "exec/Python", "exec/conversions.inix", "scripts", "checkHomerDev.py", "build.py", "version.txt"]
    sPrint = oCache.fingerprint(lsInputs, [platform.python_version()], bSkipProducts=True)
    bReusable = not (dArguments.fresh or dArguments.ui or dArguments.deep or dArguments.no_clean)
    if bReusable and oCache.isCurrent("checkHomerDev pass", sPrint, []):
        sWhen = oCache.d["jobs"]["checkHomerDev pass"].get("when", "?")
        global sReusedRun
        sReusedRun = sWhen
        finding("reused", "pass", "the kit passed this check at %s with exactly these inputs (fingerprint %s); not run again. checkHomerDev --fresh runs it in full" % (sWhen, sPrint[:12]))
        # WHAT THE REUSED RUN DID NOT CHECK STILL WAS NOT CHECKED (13 October 2026, from an audit). Its skips are restored
        # with their reasons; a pass recorded before findings were kept says its coverage is unknown.
        lsKept = oCache.d["jobs"]["checkHomerDev pass"].get("findings")
        if lsKept is None: finding("original coverage", "skip", "this pass was recorded before findings were kept, so which checks it skipped is not known; checkHomerDev --fresh runs every check")
        else:
            for sKeptName, sKeptVerdict, sKeptEvidence in lsKept:
                if sKeptVerdict == "skip": finding(sKeptName, "skip", sKeptEvidence + " (in the run reused here)")
        sReport = writeReport(False, True)
        sayLine("The kit passed this check at %s, and nothing it checks has changed since; not run again." % sWhen)
        sayLine("checkHomerDev --fresh runs every check anyway. The report is %s." % os.path.basename(sReport))
        logLine("checkHomerDev end, reused")
        return 0

    sayLine("Checking the kit in %s" % sKit)
    # --fresh and --deep build every sample from clean; otherwise a sample the cache calls current is not built again.
    dCurrent = {} if (dArguments.fresh or dArguments.deep) else currentSamples()
    setBuilding = set(t[0] for t in lAllSamples) - set(dCurrent)
    if setBuilding: sayLine("This builds %s, which takes a few minutes." % countNoun(len(setBuilding), "sample"))
    else: sayLine("Every sample is unchanged since its last build passed; none is built again.")
    sayLine()

    checkEnvironment()
    checkKit()
    checkDependencies()
    checkSharedTools()
    if dArguments.no_clean:
        finding("clean", "skip", "asked not to; a stale file could make a build look like a pass")
    else:
        cleanSamples(dArguments.deep, setBuilding)
    for sName, sScript, sExe in lAllSamples:
        if sName in dCurrent:
            dReusedSamples[sName] = str(dCurrent[sName])
            finding("build " + sName, "pass", "unchanged since its build passed at %s: the same sources and kit code, and %s is the program that build made" % (dCurrent[sName], sExe))
            continue
        sayLine("Building %s..." % sName)
        buildSample(sName, sScript, sExe)

    checkPrograms(dArguments.ui)

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
    # Recorded for the files as this check left them: its builds rewrite version.py and Version.cs (12 October 2026).
    if not iFailed and bReusable: oCache.record("checkHomerDev pass", oCache.fingerprint(lsInputs, [platform.python_version()], bSkipProducts=True), [], lsFindings)
    if iFailed: oCache.forget("checkHomerDev pass")
    logLine("checkHomerDev end")
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
