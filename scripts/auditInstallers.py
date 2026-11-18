r"""auditInstallers: audits the components a Homer setup program offers (HomerDev 1.232.0, 15 November 2026).

    auditInstallers                     audit the scripts; exit 0 when every component can be installed and updated
    auditInstallers --setup             also read the newest Setup log in %LOCALAPPDATA%\HomerDev\logs
    auditInstallers --setup PATH        the same, for the Setup log named
    auditInstallers --iss FILE.iss      audit another app's setup script instead of HomerDev_setup.iss

WHY. Setup offered "Update Pandoc 3.13 to 3.14" on 12 and 15 November 2026 and ran scripts\installPandoc each time.
The script stopped at once, because an old C:\bin\pandoc.exe answered on the PATH, and exited 0, so Setup counted it a
success and nothing in its log said otherwise. An Update that cannot update is a fact about the script, so it is
checked on every build; whether an update happened is a fact about a run, so --setup reads Setup's log.

THE SCRIPT AUDIT. Every component Setup adds (homerAdd) is matched with the script its Install, Update and Reinstall
boxes run, and that script is read for:
  1. present        the script is in scripts\.
  2. update path    it can update an installed copy: winget upgrade (installCommon's wingetUpgrade), pip --upgrade,
                    npm's @latest against the installed version, or the newest release on GitHub against a recorded
                    version.
  3. no early out   it does not end with success merely because the program answers on the PATH or sits in its
                    folder, before any update is tried. That was Pandoc's fault, and Tesseract's.
  4. one copy       a component known by several winget ids is looked for under each, so a copy registered under one
                    is updated rather than joined by a second.
  5. reinstall      it honours the reinstall argument, and Setup's Reinstall box passes it. Until 1.232.0 HomerDev's
                    Reinstall boxes passed only noPause, so a winget component's Reinstall was an update that found
                    nothing newer and did nothing.

THE SETUP AUDIT reads the Component lines Setup writes when it checks each component (what was found, what is newest,
what is offered), the Run entries for the scripts it ran, and the Outcome lines Setup writes afterwards (1.232.0 on):
wanted, before, after. An Update whose Outcome is a MISMATCH fails. A Setup older than 1.232.0 writes no Outcome
lines, so for each Update the script's own log from that run is read instead, and a script that said "already
installed" or "Already on the path" is reported as having done nothing.

Every finding goes to logs\HomerDev-auditInstallers-<time>.log beside this script's folder."""

import datetime, glob, os, platform, re, sys

sScriptDir = os.path.dirname(os.path.abspath(__file__))
sRoot = os.path.dirname(sScriptDir)
if sScriptDir not in sys.path: sys.path.insert(0, sScriptDir)
from kind import writableLogDir
sLogDir = writableLogDir(sRoot)   # the kit's logs, or %LOCALAPPDATA%\\HomerDev\\logs for a kit in Program Files (1.239.0)
sLog = os.path.join(sLogDir, "HomerDev-auditInstallers-%s.log" % datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
lFindings = []


def logLine(sText):
    with open(sLog, "a", encoding="utf-8") as oFile: oFile.write(datetime.datetime.now().isoformat(timespec="milliseconds") + "  " + sText + "\n")
    return True


def sayLine(sText):
    print(sText)
    logLine("CONSOLE: " + sText)
    return True


def finding(sCheck, bPass, sEvidence):
    lFindings.append((sCheck, bPass, sEvidence))
    sayLine("%s %s: %s" % ("PASS" if bPass else "FAIL", sCheck, sEvidence))
    return bPass


def readText(sPath):
    with open(sPath, "rb") as oFile: return oFile.read().decode("utf-8-sig", errors="replace").replace("\r\n", "\n")


def countNoun(iCount, sNoun, sPlural=""):
    return "%d %s" % (iCount, sNoun if iCount == 1 else (sPlural or sNoun + "s"))


def components(sIss):
    """[(name, ids, script)] from a setup script: each homerAdd, and the script its Update box runs."""
    sText = readText(sIss)
    lResult = []
    lsBlocks = re.split(r"(?=FileName:)", sText)
    dScripts = {}
    for sBlock in lsBlocks:
        oName = re.match(r'FileName:\s*"\{app\}\\scripts\\(install\w+\.cmd)"', sBlock)
        if not oName: continue
        for sKind, sSuffix in re.findall(r"\bis(Install|Update|Reinstall)(\w+)\b", sBlock.split("\n\n")[0]):
            dScripts.setdefault((sKind, sSuffix.lower()), oName.group(1))
    for sVar, sName, sIds in re.findall(r"(i\w+)\s*:=\s*homerAdd\('([^']*)',\s*'([^']*)'", sText):
        sSuffix = sVar[1:].lower()
        sScript = dScripts.get(("Update", sSuffix)) or dScripts.get(("Install", sSuffix)) or dScripts.get(("Reinstall", sSuffix)) or ""
        lResult.append((sName, sIds, sScript))
    return lResult


def reinstallsWithoutWord(sIss):
    """The scripts whose Reinstall box in the setup script does not pass the word reinstall."""
    lsMissing = []
    for sBlock in re.split(r"(?=FileName:)", readText(sIss)):
        oName = re.match(r'FileName:\s*"\{app\}\\scripts\\(install\w+\.cmd)"', sBlock)
        sEntry = sBlock.split("\n\n")[0]
        # The screen reader boxes pass jaws or nvda: installScreenReaderSupport reinstalls whatever it is asked for.
        if oName and oName.group(1).lower() != "installscreenreadersupport.cmd" and re.search(r"\bisReinstall\w+", sEntry) and not re.search(r'Parameters:\s*"[^"]*\breinstall\b', sEntry, re.I):
            lsMissing.append(oName.group(1))
    return lsMissing


def updateWay(sCode):
    """How a script updates an installed copy, in words, or "" when it cannot."""
    if re.search(r"wingetUpgrade|winget upgrade", sCode): return "winget upgrade"
    if re.search(r"pip[^\n]*install[^\n]*--upgrade", sCode): return "pip --upgrade"
    if re.search(r"@latest", sCode) and re.search(r"view\s+@?\S+\s+version", sCode): return "npm @latest against the installed version"
    if re.search(r"releases/latest", sCode): return "the newest GitHub release against the installed one"
    if re.search(r"--fresh", sCode): return "a fresh fetch of the newest release"
    if re.search(r"ollama pull", sCode): return "ollama pull, which fetches only what changed"
    return ""


def earlyOut(sCode):
    """The first line that ends the script with success because a copy merely exists, before any update; else ""."""
    lsLines = [s for s in sCode.split("\n") if not s.strip().lower().startswith("rem")]
    for iAt, sLine in enumerate(lsLines):
        if re.search(r"wingetUpgrade|winget upgrade|--upgrade|@latest|releases/latest|--fresh|:update\b", sLine): return ""
        if re.search(r"^\s*(where \S+|if exist )", sLine, re.I):
            sNext = "\n".join(lsLines[iAt:iAt + 6])
            if re.search(r"exit /b 0", sNext) and re.search(r"already", sNext, re.I): return sLine.strip()
    return ""


def auditScripts(sIss):
    lComponents = components(sIss)
    if not lComponents: return finding("components", False, "no homerAdd components in " + sIss)
    sayLine("Components in %s: %d" % (os.path.basename(sIss), len(lComponents)))
    lsBad = []
    for sName, sIds, sScript in lComponents:
        sPath = os.path.join(sScriptDir, sScript) if sScript else ""
        if not sScript or not os.path.isfile(sPath):
            lsBad.append("%s: no install script%s" % (sName, " " + sScript if sScript else ""))
            sayLine("  %s (%s): no script" % (sName, sIds))
            continue
        sCode = readText(sPath)
        sWay = updateWay(sCode)
        sOut = earlyOut(sCode)
        lsIds = [s for s in sIds.split(";") if s and ":" not in s]
        bAllIds = len(lsIds) < 2 or all(s in sCode for s in lsIds)
        bReinstall = re.search(r'"reinstall"', sCode, re.I) is not None
        lsWrong = []
        if not sWay: lsWrong.append("no way to update an installed copy")
        if sOut: lsWrong.append("ends with success when a copy merely exists: " + sOut)
        if not bAllIds: lsWrong.append("looks under only some of its winget ids (" + ", ".join(lsIds) + ")")
        if not bReinstall: lsWrong.append("ignores Reinstall")
        sayLine("  %s (%s), %s: updates by %s%s" % (sName, sIds, sScript, sWay or "nothing", "; " + "; ".join(lsWrong) if lsWrong else "; sound"))
        if lsWrong: lsBad.append("%s (%s): %s" % (sName, sScript, "; ".join(lsWrong)))
    lsNoWord = reinstallsWithoutWord(sIss)
    finding("reinstall boxes", not lsNoWord, "every Reinstall box passes reinstall to its script" if not lsNoWord else "Reinstall passes no reinstall to " + ", ".join(lsNoWord))
    return finding("component scripts", not lsBad, "%s, each with an update path, no early success, every id and Reinstall" % countNoun(len(lComponents), "component") if not lsBad else "; ".join(lsBad))


def newestSetupLog():
    lsLogs = sorted(glob.glob(os.path.join(os.environ.get("LOCALAPPDATA", ""), "HomerDev", "logs", "HomerDev-setup-*.log")), key=os.path.getmtime)
    return lsLogs[-1] if lsLogs else ""


def scriptLogAfter(sFolder, sScript, sStamp):
    """The script's own log from the Setup run whose stamp (yyyyMMdd-HHmmss) is given: the first one at or after it."""
    lsLogs = sorted(glob.glob(os.path.join(sFolder, "*-" + sScript + "-*.log")))
    for sPath in lsLogs:
        oStamp = re.search(r"-(\d{8}-\d{6})\.log$", sPath)
        if oStamp and oStamp.group(1) >= sStamp: return sPath
    return ""


def auditSetupLog(sPath):
    if not sPath: sPath = newestSetupLog()
    if not sPath or not os.path.isfile(sPath): return finding("setup log", False, "no Setup log found" + (" at " + sPath if sPath else ""))
    sText = readText(sPath)
    logLine("setup log: " + sPath)
    oStamp = re.search(r"-(\d{8}-\d{6})\.log$", sPath)
    sStamp = oStamp.group(1) if oStamp else ""
    dOffered = dict((sName, (sWhat, sOffer)) for sName, sWhat, sOffer in re.findall(r"Component ([^:\n]+): ([^\n]*?); offered as (\w+)", sText))
    lsRan = re.findall(r"Filename: [^\n]*\\scripts\\(install\w+)\.cmd", sText)
    dOutcome = dict((sName, sRest) for sName, sRest in re.findall(r"Outcome ([^:\n]+): ([^\n]+)", sText))
    sayLine("Setup log %s: %s checked, %s run" % (os.path.basename(sPath), countNoun(len(dOffered), "component"), countNoun(len(lsRan), "script")))
    for sName in sorted(dOffered, key=str.lower): sayLine("  %s: %s; offered as %s" % (sName, dOffered[sName][0], dOffered[sName][1]))
    lsBad, lsGood, lsUnknown = [], [], []
    dScripts = dict((sName, sScript[:-4]) for sName, sIds, sScript in components(os.path.join(sRoot, "HomerDev_setup.iss"))) if os.path.isfile(os.path.join(sRoot, "HomerDev_setup.iss")) else {}
    for sName, sRest in sorted(dOutcome.items()):
        sayLine("  outcome %s: %s" % (sName, sRest))
        (lsBad if sRest.startswith("MISMATCH") else lsGood).append(sName)
    for sName, (sWhat, sOffer) in sorted(dOffered.items()):
        if sOffer != "Update" or sName in dOutcome: continue
        sScript = dScripts.get(sName, "")
        if sScript not in lsRan:
            lsUnknown.append("%s was offered as Update and not marked" % sName)
            continue
        sScriptLog = scriptLogAfter(os.path.dirname(sPath), sScript, sStamp)
        sSaid = readText(sScriptLog) if sScriptLog else ""
        if re.search(r"already installed|Already on the path|Already in Program Files", sSaid, re.I) and not re.search(r"winget upgrade", sSaid):
            lsBad.append(sName)
            sayLine("  %s: offered as Update (%s), and %s said it was already installed without updating anything: %s" % (sName, sWhat, sScript, os.path.basename(sScriptLog)))
        elif sScriptLog:
            lsUnknown.append("%s: this Setup logs no outcome; %s's log is %s" % (sName, sScript, os.path.basename(sScriptLog)))
        else: lsUnknown.append("%s: this Setup logs no outcome, and no log of %s was found" % (sName, sScript))
    for sLine in lsUnknown: sayLine("  unverified: " + sLine)
    return finding("setup log", not lsBad, "%s as expected%s" % (countNoun(len(lsGood), "component"), "" if not lsUnknown else ", " + countNoun(len(lsUnknown), "unverified update"))
                   if not lsBad else "not updated as offered: " + ", ".join(lsBad))


def main():
    lsArgs = sys.argv[1:]
    logLine("auditInstallers %s, python %s, %s, cwd %s, args %s" % (sys.argv[0], sys.version.split()[0], platform.platform(), os.getcwd(), lsArgs))
    if lsArgs and lsArgs[0] in ("-h", "--help", "/?"):
        print(__doc__)
        return 0
    sIss = os.path.join(sRoot, "HomerDev_setup.iss")
    if "--iss" in lsArgs: sIss = lsArgs[lsArgs.index("--iss") + 1]
    auditScripts(sIss)
    if "--setup" in lsArgs:
        iAt = lsArgs.index("--setup")
        auditSetupLog(lsArgs[iAt + 1] if iAt + 1 < len(lsArgs) and not lsArgs[iAt + 1].startswith("--") else "")
    iFailed = sum(1 for t in lFindings if not t[1])
    sayLine("auditInstallers: %d passed, %d failed. Log: %s" % (len(lFindings) - iFailed, iFailed, sLog))
    return 1 if iFailed else 0


if __name__ == "__main__":
    sys.exit(main())
