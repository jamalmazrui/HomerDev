"""axeWindow: scan one window for accessibility, with Axe.Windows, saying how it goes (5 November 2026).

    axeWindow                      the app whose folder this is run from: the window it has in front -- a dialog when one
                                   is open -- or, when it is not running, its main window, opened and closed again
    axeWindow DbDo                 the same, for the app named
    axeWindow --pid 1234 --hwnd 0x1A2B   one window of a process by its handle

Every push's check runs it too, on the app's main window, so it is seldom needed by hand.

WHY ONE WINDOW. AxeWindowsCLI scans a whole program, and a window holding a long list -- DbDo's record list of 49,186
rows -- took it minutes and then failed. The Axe.Windows library can scan one window's subtree by its handle:
ScanOptions(scanId, scanRootWindowHandle), added in Axe.Windows 2.4.1 (docs\\AutomationReference.md in
microsoft/axe-windows). So a dialog is scanned without the record list behind it.

WHERE THE LIBRARY COMES FROM. AxeWindowsCLI, which the kit already fetches (axeScan --fetch), ships the library and
everything it needs in its own folder. pythonnet loads it from there into .NET, using the CLI's own runtime
configuration, so nothing else is downloaded but pythonnet itself (pip, installed when missing).

SPEECH WHILE IT WORKS. A scan can take a while, and silence sounds like a hang. JAWS is told directly, through its COM
interface, when the scan starts, every 10 seconds while it runs, and when it ends; with JAWS not running, a Windows
voice says the same. A walk scans between its recordings, so this speech never lands in a recording.

A finding is a question, not an order: see axeScan.py and the homer-gui-test skill. Never add an accessible name where
a label before the control, its own caption, or the window's title already names it.

The console says little; logs\\<App>-axeWindow-<time>.log holds every step."""

import argparse, ctypes, datetime, glob, json, os, platform, subprocess, sys, threading, time, traceback

iProgressSeconds = 10
iScanLimit = 600

sLog = ""


def logLine(sText):
    if not sLog: return
    with open(sLog, "a", encoding="utf-8") as fOut: fOut.write(datetime.datetime.now().isoformat(timespec="milliseconds") + "  " + sText + "\n")


def useLog(fLog):
    global logLine
    logLine = fLog


# ---- speech ------------------------------------------------------------------------------------------------------
oJaws, oVoice = None, None


def speak(sText):
    """Through JAWS when it is running, else a Windows voice; never fails the caller."""
    global oJaws, oVoice
    logLine("SAY: " + sText)
    try:
        import win32com.client
        if oJaws is None:
            try: oJaws = win32com.client.Dispatch("FreedomSci.JawsApi")
            except Exception: oJaws = False
        if oJaws:
            try:
                if oJaws.SayString(sText, False): return
            except Exception: pass
        if oVoice is None: oVoice = win32com.client.Dispatch("SAPI.SpVoice")
        oVoice.Speak(sText, 1)   # 1: asynchronous, so the scan is not held up
    except Exception as oError:
        logLine("speech failed: " + str(oError))


# ---- the library -------------------------------------------------------------------------------------------------
oAxe = None


def cliFolder():
    lFound = glob.glob(os.path.join(os.environ.get("LOCALAPPDATA", ""), "HomerDev", "tools", "AxeWindowsCLI", "**", "Axe.Windows.Automation.dll"), recursive=True)
    return os.path.dirname(lFound[0]) if lFound else ""


def loadAxe():
    """The Axe.Windows.Automation namespace, loaded from AxeWindowsCLI's folder; raises with the reason when it cannot."""
    global oAxe
    if oAxe is not None: return oAxe
    sFolder = cliFolder()
    if not sFolder:
        import axeScan
        axeScan.useLog(logLine)
        axeScan.getAxeCli()
        sFolder = cliFolder()
    if not sFolder: raise RuntimeError("Axe.Windows.Automation.dll is not in AxeWindowsCLI's folder")
    try:
        import pythonnet
    except ImportError:
        logLine("installing pythonnet")
        subprocess.call([sys.executable, "-m", "pip", "install", "--user", "--quiet", "pythonnet"])
        import pythonnet
    lConfigs = glob.glob(os.path.join(sFolder, "*.runtimeconfig.json"))
    if not lConfigs: raise RuntimeError("AxeWindowsCLI's folder has no runtimeconfig.json to start .NET with")
    with open(lConfigs[0], encoding="utf-8-sig") as fIn: dConfig = json.load(fIn)
    logLine("runtime config " + lConfigs[0] + ": " + json.dumps(dConfig.get("runtimeOptions", {}))[:400])
    # A FRAMEWORK-DEPENDENT CLI names a framework that is installed; a self-contained one carries the runtime in its folder.
    if "includedFrameworks" in dConfig.get("runtimeOptions", {}):
        pythonnet.load("coreclr", runtime_config=lConfigs[0], dotnet_root=sFolder)
    else:
        pythonnet.load("coreclr", runtime_config=lConfigs[0])
    import clr
    import System
    def resolve(oSender, oArgs):
        sPath = os.path.join(sFolder, oArgs.Name.split(",")[0] + ".dll")
        return System.Reflection.Assembly.LoadFrom(sPath) if os.path.isfile(sPath) else None
    System.AppDomain.CurrentDomain.AssemblyResolve += System.ResolveEventHandler(resolve)
    clr.AddReference(os.path.join(sFolder, "Axe.Windows.Automation.dll"))
    import Axe.Windows.Automation as oNamespace
    oAxe = oNamespace
    logLine("Axe.Windows.Automation loaded from " + sFolder)
    return oAxe


# ---- one window --------------------------------------------------------------------------------------------------
def windowTitle(hWnd):
    oBuffer = ctypes.create_unicode_buffer(512)
    ctypes.windll.user32.GetWindowTextW(hWnd, oBuffer, 512)
    return oBuffer.value


def scanWindow(iPid, hWnd, sFolder, sScanId, sSpoken="", iLimit=0):
    """Scan one window's subtree. Answers a dictionary: iErrors (or None), lFindings (rule -- element lines), sFile,
    sProblem. Speaks at the start, every iProgressSeconds while it runs, and at the end."""
    dResult = {"iErrors": None, "lFindings": [], "sFile": "", "sProblem": ""}
    sName = sSpoken or windowTitle(hWnd) or "the window"
    try:
        oNs = loadAxe()
    except Exception as oError:
        logLine("Axe.Windows library not loaded: " + traceback.format_exc())
        dResult["sProblem"] = "the Axe.Windows library could not be loaded: %s" % oError
        return dResult
    os.makedirs(sFolder, exist_ok=True)
    dShared = {}
    def work():
        try:
            import System
            oConfig = oNs.Config.Builder.ForProcessId(iPid).WithOutputFileFormat(oNs.OutputFileFormat.A11yTest).WithOutputDirectory(sFolder).Build()
            oScanner = oNs.ScannerFactory.CreateScanner(oConfig)
            dShared["oOutput"] = oScanner.Scan(oNs.ScanOptions(sScanId, System.IntPtr(int(hWnd))))
        except Exception:
            dShared["sError"] = traceback.format_exc()
    speak("Scanning " + sName + " for accessibility.")
    logLine("scan of %s: process %d, window 0x%X, into %s" % (sName, iPid, int(hWnd), sFolder))
    oThread = threading.Thread(target=work, daemon=True)
    oThread.start()
    nStart = time.time()
    while oThread.is_alive():
        oThread.join(iProgressSeconds)
        nGone = time.time() - nStart
        if oThread.is_alive():
            if nGone >= (iLimit or iScanLimit):
                dResult["sProblem"] = "the scan did not finish in %d seconds" % (iLimit or iScanLimit)
                speak("The scan of " + sName + " is taking too long; going on without it.")
                return dResult
            speak("Still scanning, %d seconds." % int(nGone))
    if "sError" in dShared:
        logLine("scan failed: " + dShared["sError"])
        dResult["sProblem"] = "the scan failed: " + dShared["sError"].strip().splitlines()[-1][:200]
        speak("The scan of " + sName + " could not finish.")
        return dResult
    oOutput = dShared.get("oOutput")
    iErrors, lFindings, sFile = 0, [], ""
    for oWindow in list(getattr(oOutput, "WindowScanOutputs", []) or []):
        iErrors += int(getattr(oWindow, "ErrorCount", 0) or 0)
        try: sFile = sFile or str(getattr(oWindow, "OutputFile", "") or "")
        except Exception: pass
        for oError in list(getattr(oWindow, "Errors", []) or []):
            lFindings.append(describe(oError))
    dResult.update({"iErrors": iErrors, "lFindings": lFindings, "sFile": sFile})
    logLine("scan of %s: %d error%s in %.1f s" % (sName, iErrors, "" if iErrors == 1 else "s", time.time() - nStart))
    speak("Scan done: %d error%s in %s." % (iErrors, "" if iErrors == 1 else "s", sName))
    return dResult


def describe(oError):
    """One finding as a line: the rule's description and id, then the element's kind and name."""
    sRule, sElement = "", ""
    try:
        oRule = oError.Rule
        sRule = str(getattr(oRule, "Description", "") or "") + (" (" + str(getattr(oRule, "ID", "")) + ")" if getattr(oRule, "ID", None) is not None else "")
    except Exception: pass
    try:
        dProps = oError.Element.Properties
        sKind = str(dProps["LocalizedControlType"]) if dProps.ContainsKey("LocalizedControlType") else (str(dProps["ControlType"]) if dProps.ContainsKey("ControlType") else "")
        sName = str(dProps["Name"]) if dProps.ContainsKey("Name") else ""
        sElement = (sKind + " " + ("'" + sName + "'" if sName else "with no name")).strip()
    except Exception: pass
    return (sRule or "a rule") + (" -- on " + sElement if sElement else "")


def frontWindowOf(iPid):
    """The window of the process in front: the foreground window when it is the process's, else its first visible one."""
    oUser = ctypes.windll.user32
    hFront = oUser.GetForegroundWindow()
    iOwner = ctypes.c_ulong()
    oUser.GetWindowThreadProcessId(hFront, ctypes.byref(iOwner))
    if iOwner.value == iPid: return hFront
    import axeScan
    lWindows = axeScan.windowsOf(iPid)
    return lWindows[0][0] if lWindows else 0


def scanProgramWindow(sExe, sRoot, sApp, sLogDir, iLimit=120):
    """Open the program, scan its main window, close it, and write the report -- for every push's check. Answers
    (verdict, evidence, report): "pass" with no errors, "warn" with errors to review, "skip" when no scan was made.
    It says aloud why the program opens, and how the scan goes, so nothing seems to hang."""
    import axeScan
    axeScan.useLog(logLine)
    sStamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    speak("Opening " + sApp + " to scan its window for accessibility. This takes up to %d minutes." % max(1, iLimit // 60))
    oProcess = subprocess.Popen([sExe], cwd=os.path.dirname(sExe))
    try:
        nEnd, lWindows = time.time() + 30, []
        while time.time() < nEnd:
            if oProcess.poll() is not None:
                speak(sApp + " is already open, so its window was not scanned.")
                return "skip", "%s ended at once: another copy may be running and took the start over; close it to scan" % os.path.basename(sExe), ""
            lWindows = [t for t in axeScan.windowsOf(oProcess.pid) if t[1].strip()]
            if lWindows: break
            time.sleep(0.5)
        if not lWindows: return "skip", "%s showed no window in 30 s" % os.path.basename(sExe), ""
        time.sleep(2)
        hWnd, sTitle = lWindows[0]
        dScan = scanWindow(oProcess.pid, hWnd, os.path.join(sLogDir, "axe-" + sStamp), "main", sApp + "'s main window", iLimit)
    finally:
        if oProcess.poll() is None: axeScan.closeProcess(oProcess)
    if dScan["sProblem"]:
        return "skip", "the window %s: %s" % (sTitle, dScan["sProblem"]), ""
    sReport = os.path.join(sLogDir, sApp + "-a11yScan-" + sStamp + ".md")
    iNew = axeScan.writeReport(sReport, sApp, "the window " + sTitle, dScan["iErrors"], "", dScan["lFindings"], axeScan.acceptedIn(sRoot), dScan["sFile"])
    if dScan["iErrors"] == 0: return "pass", "Axe.Windows found 0 errors in the window %s" % sTitle, sReport
    return "warn", ("Axe.Windows: %d error%s in the window %s, %d new; review %s before changing anything -- never a name the reader already has"
                    % (dScan["iErrors"], "" if dScan["iErrors"] == 1 else "s", sTitle, iNew, os.path.basename(sReport))), sReport


def pidOf(sApp):
    """The process id of a running program, by its name without .exe."""
    oRun = subprocess.run(["tasklist", "/fi", "imagename eq %s.exe" % sApp, "/fo", "csv", "/nh"], capture_output=True, text=True)
    for sLine in (oRun.stdout or "").splitlines():
        lParts = [s.strip('"') for s in sLine.split('","')]
        if len(lParts) > 1 and lParts[1].isdigit(): return int(lParts[1])
    return 0


def main():
    global sLog
    oParser = argparse.ArgumentParser(description="Scan one window for accessibility with Axe.Windows, saying how it goes.")
    oParser.add_argument("app", nargs="?", default="", help="a running program's name, such as DbDo")
    oParser.add_argument("--pid", type=int, default=0)
    oParser.add_argument("--hwnd", default="")
    oArgs = oParser.parse_args()
    sRoot = os.getcwd()
    if os.path.basename(sRoot).lower() == "scripts": sRoot = os.path.dirname(sRoot)
    sLogDir = os.path.join(sRoot, "logs"); os.makedirs(sLogDir, exist_ok=True)
    sApp = oArgs.app or os.path.basename(sRoot)
    sStamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    sLog = os.path.join(sLogDir, "%s-axeWindow-%s.log" % (sApp, sStamp))
    logLine("axeWindow %s; Python %s at %s; %s; working folder %s; arguments %s" % (os.path.abspath(__file__), platform.python_version(), sys.executable, platform.platform(), os.getcwd(), sys.argv[1:]))
    iPid = oArgs.pid or pidOf(sApp)
    if not iPid:
        # NOT RUNNING: OPEN IT, SCAN ITS MAIN WINDOW, CLOSE IT (5 November 2026): no argument to remember.
        sExe = os.path.join(sRoot, "exec", sApp + ".exe")
        if not os.path.isfile(sExe):
            print("%s is not running, and %s is not here to start." % (sApp, sExe)); return 1
        sVerdict, sEvidence, sReport = scanProgramWindow(sExe, sRoot, sApp, sLogDir)
        print(sEvidence); return 0 if sVerdict in ("pass", "warn") else 2
    hWnd = int(oArgs.hwnd, 0) if oArgs.hwnd else frontWindowOf(iPid)
    if not hWnd:
        print("%s has no window to scan." % sApp); return 1
    dResult = scanWindow(iPid, hWnd, os.path.join(sLogDir, "axe-" + sStamp), "window")
    import axeScan
    axeScan.useLog(logLine)
    sReport = os.path.join(sLogDir, "%s-a11yScan-%s.md" % (sApp, sStamp))
    if dResult["sProblem"]:
        print("No scan: " + dResult["sProblem"] + ". The log says why: " + os.path.basename(sLog)); return 2
    iNew = axeScan.writeReport(sReport, sApp, "the window " + (windowTitle(hWnd) or hex(hWnd)), dResult["iErrors"], "",
                               dResult["lFindings"], axeScan.acceptedIn(sRoot), dResult["sFile"])
    print("%d error%s, %d new; the report is %s." % (dResult["iErrors"], "" if dResult["iErrors"] == 1 else "s", iNew, os.path.basename(sReport)))
    return 0


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try: sys.exit(main())
    except Exception as oError:
        logLine(traceback.format_exc()); print("axeWindow stopped: %s" % oError); sys.exit(1)
