"""axeScan: accessibility scans for every Homer app, with Microsoft's Axe.Windows (5 November 2026).

    axeScan --fetch                      get AxeWindowsCLI once, into %LOCALAPPDATA%\\HomerDev\\tools\\AxeWindowsCLI
    axeScan --fetch --fresh              get the newest again, replacing what is there (the installer's Reinstall)
    axeScan --exe C:\\DbDo\\exec\\DbDo.exe  start the program, scan its window, close it, write a report
    axeScan --pid 1234                   scan a program that is already running

Axe.Windows is the rule engine of Accessibility Insights for Windows: missing names, wrong roles, controls the
keyboard cannot reach. recordWalk (with --axe) scans after each step; the shared check scans an app's main window
at every push. Both use the functions here, so the rules and the advice are one.

WHAT A FINDING ASKS OF US. A finding is a question, not an order. The report says, rule by rule, what a screen
reader user would meet and what to check before changing anything. Above all: a control with no accessible name is
often named already -- by the label just before it in the focus order, by its own caption (a check box, a button),
or by the window's title -- and JAWS and NVDA say that name. Setting AccessibleName to the same words makes the
reader say them twice. So no name is added where the reader already has one; a fix is made only where a user would
truly meet nothing, or where the finding is plainly a bug.

Every finding the person has reviewed and accepted goes in the app's a11yAccepted.txt, one per line, as the report
prints it; accepted findings are counted, but no longer reported as new.

The console says little; the log, logs\\<App>-axeScan-<time>.log, holds every command, exit code and output."""

import argparse, ctypes, datetime, glob, json, os, platform, re, shutil, subprocess, sys, time, traceback, urllib.request, zipfile

sAxeReleases = "https://api.github.com/repos/microsoft/axe-windows/releases/latest"
iWaitForWindow = 30
iWaitToClose = 10
# A SCAN HAS A LIMIT (5 November 2026). Axe.Windows walks every element of a window. DbDo's record list held 49,186
# rows of RadioTrail; the scan ran 2 minutes 44 seconds, then failed inside Axe.Windows itself (a null reference in
# AddLogicalSizePseudoProperty), and push and recordWalk seemed to hang. A scan not done in this many seconds is
# stopped and reported as unfinished, never waited on.
iScanLimit = 60
sAccepted = "a11yAccepted.txt"

sLog = ""
sLastOutput = ""   # the full output of the last scan, for findingsFrom


def logLine(sText):
    """Into the log, when one is open; the caller's own log takes over when this module is imported."""
    if not sLog: return
    with open(sLog, "a", encoding="utf-8") as fOut: fOut.write(datetime.datetime.now().isoformat(timespec="milliseconds") + "  " + sText + "\n")


def sayLine(sText):
    print(sText)
    logLine("CONSOLE: " + sText)


def useLog(fLog):
    """Send this module's log lines to a caller's logger (recordWalk's, check.py's)."""
    global logLine
    logLine = fLog


def toolHome():
    return os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "HomerDev", "tools", "AxeWindowsCLI")


def getAxeCli(bFresh=False):
    """AxeWindowsCLI.exe, fetched once from the newest release of microsoft/axe-windows: the release asset whose name
    holds "CLI" and ends .zip, rather than a guessed name. Raises when it cannot be had; the caller says so."""
    sHome = toolHome()
    lFound = glob.glob(os.path.join(sHome, "**", "AxeWindowsCLI.exe"), recursive=True)
    if lFound and not bFresh:
        logLine("AxeWindowsCLI: " + lFound[0])
        return lFound[0]
    if bFresh and os.path.isdir(sHome):
        shutil.rmtree(sHome, ignore_errors=True)
        logLine("removed " + sHome + " to fetch the newest again")
    sayLine("Getting AxeWindowsCLI, once; it is about the size of a small program.")
    oRequest = urllib.request.Request(sAxeReleases, headers={"User-Agent": "HomerDev axeScan", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(oRequest, timeout=60) as oResponse: dRelease = json.loads(oResponse.read().decode("utf-8"))
    lAssets = [d for d in dRelease.get("assets", []) if "cli" in d.get("name", "").lower() and d.get("name", "").lower().endswith(".zip")]
    logLine("axe-windows release " + str(dRelease.get("tag_name")) + "; assets " + ", ".join(d.get("name", "") for d in dRelease.get("assets", [])))
    if not lAssets: raise RuntimeError("the newest axe-windows release has no CLI zip among its assets")
    os.makedirs(sHome, exist_ok=True)
    sZip = os.path.join(sHome, lAssets[0]["name"])
    oRequest = urllib.request.Request(lAssets[0]["browser_download_url"], headers={"User-Agent": "HomerDev axeScan"})
    with urllib.request.urlopen(oRequest, timeout=300) as oResponse, open(sZip, "wb") as fOut: shutil.copyfileobj(oResponse, fOut)
    with zipfile.ZipFile(sZip) as oZip: oZip.extractall(sHome)
    logLine("AxeWindowsCLI fetched: " + lAssets[0]["name"] + " into " + sHome)
    lFound = glob.glob(os.path.join(sHome, "**", "AxeWindowsCLI.exe"), recursive=True)
    if not lFound: raise RuntimeError("the CLI zip held no AxeWindowsCLI.exe")
    # VERSION.TXT BESIDE THE PROGRAM (5 November 2026): the kit installer reads a version.txt beside a component's file
    # before asking it for --version, so the release's own tag, such as 2.4.2, is what its box shows.
    sVersion = re.sub(r"^[vV]", "", str(dRelease.get("tag_name") or "")).strip()
    if sVersion:
        with open(os.path.join(os.path.dirname(lFound[0]), "version.txt"), "w", encoding="utf-8") as fOut: fOut.write(sVersion + "\n")
    return lFound[0]


def axeScan(sCli, iPid, sFolder, sScanId):
    """One scan of a process; answers (error count or None, a one-line summary, the .a11ytest file or '').
    Its switches are from AxeWindowsCLI's own README: --processId, --outputDirectory, --scanId, --verbosity and
    --alwaysSaveTestFile, whose .a11ytest file opens in Accessibility Insights for Windows."""
    os.makedirs(sFolder, exist_ok=True)
    lCommand = [sCli, "--processId", str(iPid), "--outputDirectory", sFolder, "--scanId", sScanId, "--verbosity", "verbose", "--alwaysSaveTestFile"]
    logLine("axe: " + " ".join(lCommand))
    global sLastOutput
    try:
        oRun = subprocess.run(lCommand, capture_output=True, text=True, timeout=iScanLimit)
    except subprocess.TimeoutExpired as oTimeout:
        sLastOutput = ((oTimeout.stdout or b"").decode("utf-8", "replace") if isinstance(oTimeout.stdout, bytes) else (oTimeout.stdout or ""))
        logLine("axe did not finish in %d s and was stopped" % iScanLimit)
        return None, "Axe.Windows did not finish in %d seconds -- a window holding a very long list is beyond it" % iScanLimit, ""
    sOut = (oRun.stdout or "") + (oRun.stderr or "")
    sLastOutput = sOut
    logLine("axe exit code " + str(oRun.returncode) + "; output:\n" + sOut)
    if oRun.returncode == 2:
        oWhy = re.search(r"exception was caught: ([^\r\n]*)", sOut)
        return None, "Axe.Windows could not complete the scan" + (": " + oWhy.group(1)[:160] if oWhy else ""), ""
    oCount = re.search(r"(\d+)\s+errors?\b", sOut, re.I)
    lFiles = glob.glob(os.path.join(sFolder, "**", sScanId + "*.a11ytest"), recursive=True) or glob.glob(os.path.join(sFolder, "**", "*.a11ytest"), recursive=True)
    sFile = max(lFiles, key=os.path.getmtime) if lFiles else ""
    iErrors = int(oCount.group(1)) if oCount else None
    lLines = [s.strip() for s in sOut.splitlines() if s.strip()]
    lRules = [s for s in lLines if re.search(r"rule|error", s, re.I)][:6]
    return iErrors, ("; ".join(lRules) if lRules else (lLines[-1] if lLines else "no output")), sFile


def findingsFrom(sOut, sFile):
    """The findings as lines a person can read: from the CLI's verbose output, and from the JSON inside the .a11ytest
    file when its shape is recognized. The file's members are logged, so its shape can be learned from a real run."""
    lFindings = []
    for sLine in (sOut or "").splitlines():
        s = sLine.strip()
        if re.search(r"\b(rule|error)\b", s, re.I) and not re.match(r"^\d+\s+errors?\b", s, re.I) and len(s) > 12:
            lFindings.append(s)
    if sFile and zipfile.is_zipfile(sFile):
        try:
            with zipfile.ZipFile(sFile) as oZip:
                logLine("a11ytest members: " + ", ".join(oZip.namelist()))
                for sMember in oZip.namelist():
                    try: oData = json.loads(oZip.read(sMember).decode("utf-8-sig"))
                    except Exception: continue
                    walkJson(oData, lFindings)
        except Exception as oError:
            logLine("a11ytest not read: " + str(oError))
    lUnique = []
    for s in lFindings:
        if s not in lUnique: lUnique.append(s)
    return lUnique


def walkJson(oNode, lFindings, sElement=""):
    """A failed rule anywhere in the JSON: a dict whose status says it failed, with a rule's description or id."""
    if isinstance(oNode, dict):
        sName = str(oNode.get("Name") or oNode.get("name") or sElement or "")
        sStatus = str(oNode.get("Status") or oNode.get("status") or "")
        sRule = str(oNode.get("Description") or oNode.get("description") or oNode.get("RuleId") or oNode.get("Rule") or "")
        if sRule and re.search(r"fail|error", sStatus, re.I):
            lFindings.append(sRule + (" -- on " + sName if sName else ""))
        for oValue in oNode.values(): walkJson(oValue, lFindings, sName)
    elif isinstance(oNode, list):
        for oValue in oNode: walkJson(oValue, lFindings, sElement)


def adviceFor(sFinding):
    """Homer's guidance for a finding, by the kind of rule it names."""
    s = sFinding.lower()
    if "boundingrectangle" in s:
        return ("How a virtual list reports rows that are not on screen: Windows' own list control gives them no on-screen "
                "rectangle. DbDo's record list showed it 4,161 times. A screen reader reads the rows it is on; nothing to change.")
    if "scrollitem" in s:
        return ("How Windows Forms' standard list box reports its items: each lacks the ScrollItem pattern its scrolling list "
                "implies. Screen readers do not depend on it, and a user does not meet it; nothing to change in the app.")
    if "name" in s and re.search(r"null|empty|not null|missing|no name|whitespace", s):
        return ("Check first what already names it for the reader: the label just before it in the focus order, its own "
                "caption (a check box, a button), or the window's title. If any does, change nothing -- an accessible "
                "name with the same words would be said twice. Add a name only when nothing names it.")
    if "name" in s and re.search(r"control type|localized|informative|excludes|role", s):
        return ("The name repeats the kind of control, such as \"OK button\"; the reader says the kind itself, so the name "
                "should not. A plain bug to fix.")
    if re.search(r"keyboard|focusable|tab stop|focus", s):
        return "A control the keyboard may not reach: usually a real bug, worth fixing."
    if re.search(r"bounding|offscreen|off screen|clickable|rectangle", s):
        return ("Often how Windows Forms reports a hidden or zero-size control rather than a fault a user meets; check "
                "the control is really there before changing anything.")
    if re.search(r"structure|parent|child|sibling", s):
        return "How the window is put together; review whether a reader meets anything wrong before changing it."
    return "Review what a screen reader user would meet before changing anything."


def acceptedIn(sRoot):
    sPath = os.path.join(sRoot, sAccepted)
    if not os.path.isfile(sPath): return set()
    with open(sPath, encoding="utf-8-sig") as fIn:
        return set(s.strip() for s in fIn if s.strip() and not s.strip().startswith(("#", ";")))


def writeReport(sPath, sApp, sWhat, iErrors, sSummary, lFindings, setAccepted, sFile):
    lNew = [s for s in lFindings if s not in setAccepted]
    lLines = ["# Accessibility scan of " + sApp, "",
              "Scanned " + datetime.datetime.now().strftime("%d %B %Y at %H:%M") + ": " + sWhat + ", with Axe.Windows, the rule engine of Accessibility Insights for Windows.", "",
              "**" + (("%d error%s" % (iErrors, "" if iErrors == 1 else "s")) if iErrors is not None else "The error count could not be read") + "; "
              + "%d finding%s listed, %d new.**" % (len(lFindings), "" if len(lFindings) == 1 else "s", len(lNew)), "",
              "A finding is a question, not an order. Before changing anything, check what a screen reader user would meet; "
              "never add an accessible name where a label before the control, its own caption, or the window's title already "
              "names it, since the reader would then say it twice. A finding reviewed and accepted goes in " + sAccepted + ", one per line, as written here.", ""]
    if sFile: lLines += ["The full results, " + os.path.basename(sFile) + ", open in Accessibility Insights for Windows.", ""]
    # A REPEATING FINDING IS ONE ENTRY (6 November 2026). FileDir's list gave 60 of one rule, one per file, and 1,086
    # with a longer list: the same question each time. Findings are grouped by rule and kind of element, each group
    # with its count and up to three examples; a pattern seen once is read once.
    dGroups, lOrder = {}, []
    for sFinding in lFindings:
        sRule, _, sOn = sFinding.partition(" -- on ")
        sKind = re.sub(r"\s*'.*$", "", sOn).replace(" with no name", "").strip()
        sKey = sRule + " | " + sKind
        if sKey not in dGroups: dGroups[sKey] = []; lOrder.append(sKey)
        dGroups[sKey].append(sFinding)
    for sKey in sorted(lOrder, key=lambda k: -len(dGroups[k])):
        lSame = dGroups[sKey]
        sRule, _, sKind = sKey.partition(" | ")
        sNew = "" if all(s in setAccepted for s in lSame) else ""
        lLines += ["## " + sRule + (" -- on " + sKind if sKind else "") + " (%d time%s)" % (len(lSame), "" if len(lSame) == 1 else "s"), "",
                   adviceFor(lSame[0]), ""]
        for sOne in lSame[:3]: lLines.append("- " + ("Accepted: " if sOne in setAccepted else "") + sOne)
        if len(lSame) > 3: lLines.append("- and %d more like these" % (len(lSame) - 3))
        lLines.append("")
    if not lFindings: lLines += ["No finding could be listed. " + (sSummary or ""), ""]
    with open(sPath, "w", encoding="utf-8-sig", newline="\r\n") as fOut: fOut.write("\n".join(lLines))
    return len(lNew)


def windowsOf(iPid):
    """The visible top-level windows of a process, by Win32's EnumWindows: [(handle, title)]."""
    lFound = []
    if os.name != "nt": return lFound
    oUser = ctypes.windll.user32
    fEnum = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def visit(hWnd, lParam):
        iOwner = ctypes.c_ulong()
        oUser.GetWindowThreadProcessId(hWnd, ctypes.byref(iOwner))
        if iOwner.value == iPid and oUser.IsWindowVisible(hWnd):
            oBuffer = ctypes.create_unicode_buffer(512)
            oUser.GetWindowTextW(hWnd, oBuffer, 512)
            lFound.append((hWnd, oBuffer.value))
        return True
    oUser.EnumWindows(fEnum(visit), 0)
    return lFound


def closeProcess(oProcess):
    """Ask the program's windows to close, as Alt+F4 would, by WM_CLOSE; end it only if it will not. Nothing is
    clicked or pressed."""
    for hWnd, sTitle in windowsOf(oProcess.pid):
        ctypes.windll.user32.PostMessageW(hWnd, 0x0010, 0, 0)
    try:
        oProcess.wait(timeout=iWaitToClose)
        logLine("closed by WM_CLOSE, exit code " + str(oProcess.returncode))
    except subprocess.TimeoutExpired:
        oProcess.kill()
        logLine("did not close in %d s, so it was ended" % iWaitToClose)


def scanProgram(sExe, sRoot, sApp, sLogDir):
    """Start sExe, wait for its window, scan it, close it, and write the report. Answers (verdict, evidence, report):
    verdict "pass" with no errors, "warn" with errors to review, "skip" when no scan could be made."""
    if os.name != "nt": return "skip", "scans need Windows", ""
    try: sCli = getAxeCli()
    except Exception as oError:
        logLine("AxeWindowsCLI not available: " + traceback.format_exc())
        return "skip", "AxeWindowsCLI could not be had: %s" % oError, ""
    sStamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    sFolder = os.path.join(sLogDir, "axe-" + sStamp)
    logLine("starting " + sExe)
    oProcess = subprocess.Popen([sExe], cwd=os.path.dirname(sExe))
    try:
        nEnd = time.time() + iWaitForWindow
        lWindows = []
        while time.time() < nEnd:
            if oProcess.poll() is not None:
                return "skip", ("%s ended at once (exit code %s): another copy may be running and took the start over; "
                                "close it so the gate can scan a fresh one" % (os.path.basename(sExe), oProcess.returncode)), ""
            lWindows = [t for t in windowsOf(oProcess.pid) if t[1].strip()]
            if lWindows: break
            time.sleep(0.5)
        if not lWindows: return "skip", "%s showed no window in %d s" % (os.path.basename(sExe), iWaitForWindow), ""
        time.sleep(2)   # let the window finish filling before it is read
        sWhat = "the window " + lWindows[0][1]
        iErrors, sSummary, sFile = axeScan(sCli, oProcess.pid, sFolder, "main")
    finally:
        if oProcess.poll() is None: closeProcess(oProcess)
    if iErrors is None and not sFile:
        return "skip", "%s: %s" % (sWhat, sSummary), ""
    lFindings = findingsFrom(sLastOutput, sFile)
    sReport = os.path.join(sLogDir, sApp + "-a11yScan-" + sStamp + ".md")
    iNew = writeReport(sReport, sApp, sWhat, iErrors, sSummary, lFindings, acceptedIn(sRoot), sFile)
    if iErrors == 0: return "pass", "Axe.Windows found 0 errors in %s" % sWhat, sReport
    return "warn", ("Axe.Windows: %s in %s, %d new; review %s before changing anything -- never a name the reader already has"
                    % (("%d error%s" % (iErrors, "" if iErrors == 1 else "s")) if iErrors is not None else "an unread count of errors",
                       sWhat, iNew, os.path.basename(sReport))), sReport


def main():
    global sLog
    oParser = argparse.ArgumentParser(description="Accessibility scans with Axe.Windows, for Homer apps.")
    oParser.add_argument("--fetch", action="store_true", help="get AxeWindowsCLI once and stop")
    oParser.add_argument("--fresh", action="store_true", help="with --fetch, get the newest again")
    oParser.add_argument("--exe", default="", help="a program to start, scan and close")
    oParser.add_argument("--pid", type=int, default=0, help="a running program's process id, to scan")
    oArgs = oParser.parse_args()
    sRoot = os.getcwd()
    sLogDir = os.path.join(sRoot, "logs")
    os.makedirs(sLogDir, exist_ok=True)
    sApp = os.path.splitext(os.path.basename(oArgs.exe))[0] if oArgs.exe else os.path.basename(sRoot)
    sLog = os.path.join(sLogDir, "%s-axeScan-%s.log" % (sApp, datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))
    logLine("axeScan %s; Python %s at %s; %s; working folder %s; arguments %s" % (os.path.abspath(__file__), platform.python_version(), sys.executable, platform.platform(), sRoot, sys.argv[1:]))
    if oArgs.fetch:
        try: sayLine("AxeWindowsCLI is ready: " + getAxeCli(oArgs.fresh)); return 0
        except Exception as oError:
            logLine(traceback.format_exc()); sayLine("AxeWindowsCLI could not be had: %s; the log says why." % oError); return 1
    if oArgs.exe:
        sVerdict, sEvidence, sReport = scanProgram(os.path.abspath(oArgs.exe), sRoot, sApp, sLogDir)
        sayLine(sEvidence)
        return 0 if sVerdict in ("pass", "warn") else 2
    if oArgs.pid:
        sCli = getAxeCli()
        iErrors, sSummary, sFile = axeScan(sCli, oArgs.pid, os.path.join(sLogDir, "axe-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")), "pid%d" % oArgs.pid)
        sReport = os.path.join(sLogDir, sApp + "-a11yScan-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".md")
        writeReport(sReport, sApp, "process %d" % oArgs.pid, iErrors, sSummary, findingsFrom(sLastOutput, sFile), acceptedIn(sRoot), sFile)
        sayLine("Scanned; the report is " + os.path.basename(sReport))
        return 0
    oParser.print_help()
    return 1


if __name__ == "__main__":
    try: sys.exit(main())
    except Exception as oError:
        logLine(traceback.format_exc()); print("axeScan stopped: %s" % oError); sys.exit(1)
