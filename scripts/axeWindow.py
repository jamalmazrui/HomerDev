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

WHERE THE LIBRARY COMES FROM (5 November 2026, night). The Axe.Windows package and every package it depends on are
fetched from NuGet once, into %LOCALAPPDATA%\\HomerDev\\tools\\AxeWindowsLib, following each package's own list of
dependencies, and loaded into 64-bit .NET Framework 4.8 with pythonnet. The first try borrowed AxeWindowsCLI's
runtime, which is 32-bit: its hostfxr.dll would not load into 64-bit Python (error 0xC1), and no scan ran.

SPEECH WHILE IT WORKS. A scan can take a while, and silence sounds like a hang. JAWS is told directly, through its COM
interface, when the scan starts, every 10 seconds while it runs, and when it ends; with JAWS not running, a Windows
voice says the same. A walk scans between its recordings, so this speech never lands in a recording.

A finding is a question, not an order: see axeScan.py and the homer-gui-test skill. Never add an accessible name where
a label before the control, its own caption, or the window's title already names it.

The console says little; logs\\<App>-axeWindow-<time>.log holds every step."""

import argparse, ctypes, datetime, glob, json, os, platform, subprocess, sys, threading, time, traceback

iProgressSeconds = 10
iScanLimit = 300   # five minutes at most, for any window (6 November 2026)

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
oAssembly = None


sNuget = "https://api.nuget.org/v3-flatcontainer/"
# The frameworks .NET Framework 4.8 can load, best first; ".NETFramework4.6.2" and "net462" name the same one.
# Written without dots, as shortFramework gives them: the Axe.Windows package's own folder is lib/netstandard20, an
# older spelling of netstandard2.0, and was missed while names kept their dots (5 November 2026, evening).
lsFrameworks = ["net48", "net472", "net471", "net47", "net462", "net461", "net46", "net452", "net451", "net45",
                  "netstandard20", "netstandard16", "netstandard13", "netstandard11", "netstandard10"]


def libFolder():
    return os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "HomerDev", "tools", "AxeWindowsLib")


def shortFramework(sName):
    """A framework's name without dots: ".NETFramework4.6.2" and "net462" as net462; ".NETStandard2.0",
    "netstandard2.0" and "netstandard20" as netstandard20."""
    s = (sName or "").strip().lower()
    if s.startswith(".netframework"): s = "net" + s[len(".netframework"):]
    elif s.startswith(".netstandard"): s = "netstandard" + s[len(".netstandard"):]
    return s.replace(".", "")


def urlGet(sUrl):
    import urllib.request
    oRequest = urllib.request.Request(sUrl, headers={"User-Agent": "HomerDev axeWindow"})
    with urllib.request.urlopen(oRequest, timeout=120) as oResponse: return oResponse.read()


def fetchLibrary(bFresh=False):
    """The Axe.Windows package and its dependencies, from NuGet, into libFolder(): each package's newest stable version
    for Axe.Windows itself, and the lowest version a dependency names, as NuGet chooses; from each, the lib folder of
    the best framework .NET Framework 4.8 can load. A package whose best folder holds only _._ is part of the framework
    and adds nothing. Answers the folder."""
    import io, re, shutil, zipfile
    sFolder = libFolder()
    if bFresh and os.path.isdir(sFolder): shutil.rmtree(sFolder, ignore_errors=True)
    if os.path.isfile(os.path.join(sFolder, "Axe.Windows.Automation.dll")): return sFolder
    os.makedirs(sFolder, exist_ok=True)
    dIndex = json.loads(urlGet(sNuget + "axe.windows/index.json").decode("utf-8"))
    sVersion = [v for v in dIndex["versions"] if "-" not in v][-1]
    lQueue, setDone = [("Axe.Windows", sVersion)], set()
    while lQueue:
        sId, sVer = lQueue.pop(0)
        if sId.lower() in setDone: continue
        setDone.add(sId.lower())
        sUrl = "%s%s/%s/%s.%s.nupkg" % (sNuget, sId.lower(), sVer.lower(), sId.lower(), sVer.lower())
        logLine("NuGet: " + sId + " " + sVer + " from " + sUrl)
        with zipfile.ZipFile(io.BytesIO(urlGet(sUrl))) as oZip:
            lNames = oZip.namelist()
            # EITHER SEPARATOR (5 November 2026, night): the Axe.Windows package itself was read as having no lib folder,
            # while its dependencies' were found; a package whose zip entries are written lib\\netstandard2.0\\... is
            # read the same as lib/netstandard2.0/... now.
            dByName = dict((n.replace("\\", "/"), n) for n in lNames)
            sSpec = next((n for n in lNames if n.lower().endswith(".nuspec")), "")
            sXml = oZip.read(sSpec).decode("utf-8-sig") if sSpec else ""
            # Its libraries, from the best framework folder it has.
            dLib = {}
            for n in dByName:
                m = re.match(r"^lib/([^/]+)/([^/]+)$", n, re.I)
                if m: dLib.setdefault(shortFramework(m.group(1)), []).append(dByName[n])
            sBest = next((f for f in lsFrameworks if f in dLib), "")
            if not sBest and sId.lower() == "axe.windows":
                logLine("  no lib folder found; the package holds: " + ", ".join(lNames[:80]))
            for n in dLib.get(sBest, []):
                if n.lower().endswith((".dll",)):
                    with open(os.path.join(sFolder, os.path.basename(n.replace("\\", "/"))), "wb") as fOut: fOut.write(oZip.read(n))
            logLine("  libraries from lib/" + (sBest or "(none)") + ": " + ", ".join(os.path.basename(n.replace("\\", "/")) for n in dLib.get(sBest, [])))
            # Its dependencies, from the group for the best framework it names.
            dGroups = {}
            for m in re.finditer(r"<group([^>]*)>(.*?)</group>", sXml, re.S):
                oTf = re.search(r'targetFramework="([^"]*)"', m.group(1))
                dGroups[shortFramework(oTf.group(1) if oTf else "")] = m.group(2)
            sGroup = next((f for f in lsFrameworks if f in dGroups), "")
            for m in re.finditer(r'<dependency\s+id="([^"]+)"\s+version="([^"]+)"', dGroups.get(sGroup, "")):
                sDepVer = re.sub(r"[\[\]\(\)\s]", "", m.group(2)).split(",")[0]
                lQueue.append((m.group(1), sDepVer))
    if not os.path.isfile(os.path.join(sFolder, "Axe.Windows.Automation.dll")):
        raise RuntimeError("the Axe.Windows package gave no Axe.Windows.Automation.dll; the log lists what it holds")
    with open(os.path.join(sFolder, "version.txt"), "w", encoding="utf-8") as fOut: fOut.write(sVersion + "\n")
    logLine("Axe.Windows " + sVersion + " and its dependencies are in " + sFolder)
    return sFolder


def loadAxe():
    """The Axe.Windows.Automation namespace, loaded into 64-bit .NET Framework; raises with the reason when it cannot."""
    global oAxe, oAssembly
    if oAxe is not None: return oAxe
    sFolder = fetchLibrary()
    try:
        import pythonnet
    except ImportError:
        logLine("installing pythonnet")
        subprocess.call([sys.executable, "-m", "pip", "install", "--user", "--quiet", "pythonnet"])
        import pythonnet
    try: pythonnet.load("netfx")
    except Exception as oError: logLine("pythonnet.load(netfx): " + str(oError))   # already loaded is fine
    import clr
    import System
    def resolve(oSender, oArgs):
        sPath = os.path.join(sFolder, oArgs.Name.split(",")[0] + ".dll")
        return System.Reflection.Assembly.LoadFrom(sPath) if os.path.isfile(sPath) else None
    System.AppDomain.CurrentDomain.AssemblyResolve += System.ResolveEventHandler(resolve)
    oAssembly = clr.AddReference(os.path.join(sFolder, "Axe.Windows.Automation.dll"))
    import Axe.Windows.Automation as oNamespace
    oAxe = oNamespace
    logLine("Axe.Windows.Automation loaded from " + sFolder + " into .NET Framework, " + ("64" if sys.maxsize > 2**32 else "32") + "-bit")
    return oAxe


def axeType(sName):
    """A type of the Axe.Windows.Automation library by its short name, whatever namespace holds it: the 20:01 walk found
    Config and ScannerFactory in Axe.Windows.Automation, but not ScanOptions, so the library is asked rather than guessed."""
    import importlib
    for oType in oAssembly.GetExportedTypes():
        if oType.Name == sName:
            logLine(sName + " is in " + str(oType.Namespace))
            return getattr(importlib.import_module(str(oType.Namespace)), sName)
    raise RuntimeError("the Axe.Windows library has no type named " + sName)


def scanOptions(sScanId, hWnd):
    """ScanOptions for one window: scanId and scanRootWindowHandle, positionally; if that constructor does not fit,
    by reflection with the same two values, so a signature change is answered rather than fatal."""
    import System
    oClass = axeType("ScanOptions")
    try:
        return oClass(sScanId, System.IntPtr(int(hWnd)))
    except Exception as oError:
        logLine("ScanOptions(scanId, handle) did not fit: " + str(oError) + "; its constructors: "
                + "; ".join(str(c) for c in oClass.__dict__.get("__overloads__", []) or []))
        oType = System.Type.GetType(oClass.__module__ + "." + "ScanOptions") or [t for t in oAssembly.GetExportedTypes() if t.Name == "ScanOptions"][0]
        aArgs = System.Array[System.Object]([sScanId, System.IntPtr(int(hWnd))])
        return System.Activator.CreateInstance(oType, aArgs)


# ---- a window's fingerprint: scan only what has changed (6 November 2026) ------------------------------------------
# A window whose controls are the same kinds, in the same order, with the same captions, is the same window to a scan;
# a list's rows or an edit box's text are its data, not its make-up, and are left out. The Axe.Windows version is part
# of the fingerprint, so a new rule set scans again. Windows Forms class names carry a per-build suffix
# (".app.0.141b42a_r6_ad1"), dropped so a rebuild alone is not a change. Kept in %LOCALAPPDATA%\\HomerDev\\axeScans.inix --
# a Homer file is .inix, not JSON (6 November 2026) -- one section a window, by program and window: a dialog by its title,
# the main window, whose title follows its folder or table, as "main"; each finding on its own numbered line.
lsDataClasses = ("edit", "richedit", "combobox", "listbox", "syslistview32", "systreeview32", "datagridview")


def scansFile():
    return os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "HomerDev", "axeScans.inix")


def exeNameOf(iPid):
    from ctypes import wintypes
    hProcess = ctypes.windll.kernel32.OpenProcess(0x1000, False, iPid)
    if not hProcess: return ""
    try:
        oBuffer = ctypes.create_unicode_buffer(1024); iSize = wintypes.DWORD(1024)
        if ctypes.windll.kernel32.QueryFullProcessImageNameW(hProcess, 0, oBuffer, ctypes.byref(iSize)): return os.path.basename(oBuffer.value)
        return ""
    finally:
        ctypes.windll.kernel32.CloseHandle(hProcess)


def windowFingerprint(hWnd):
    """A hash of the window's controls in order: kind, and the caption of each that is not a data control."""
    import hashlib, re as reLocal
    oUser = ctypes.windll.user32
    lParts = []
    fEnum = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def visit(hChild, lParam):
        oClass = ctypes.create_unicode_buffer(256); oUser.GetClassNameW(hChild, oClass, 256)
        sClass = reLocal.sub(r"\.app\..*$", "", oClass.value)
        sText = ""
        # ONLY BUTTONS AND LABELS SAY WHAT A WINDOW IS (9 November 2026). Every other control's text is its state: an
        # MDI child is titled with its folder or table, a status bar with what was last done. FileDir's main window
        # read as changed on every run, and was scanned every run, because its folder window's title was counted.
        sLower = sClass.lower()
        if ("button" in sLower or "static" in sLower) and not any(s in sLower for s in lsDataClasses):
            oText = ctypes.create_unicode_buffer(512); oUser.GetWindowTextW(hChild, oText, 512); sText = oText.value
        lParts.append("%s|%s|%d" % (sClass, sText, 1 if oUser.IsWindowVisible(hChild) else 0))
        return True
    oUser.EnumChildWindows(int(hWnd), fEnum(visit), 0)
    sVersion = ""
    try:
        with open(os.path.join(libFolder(), "version.txt"), encoding="utf-8") as fIn: sVersion = fIn.read().strip()
    except Exception: pass
    return hashlib.sha256(("axe " + sVersion + " fingerprint 2\n" + "\n".join(lParts)).encode("utf-8")).hexdigest(), len(lParts)


def windowKey(iPid, hWnd):
    bMain = not ctypes.windll.user32.GetWindow(int(hWnd), 4)   # GW_OWNER: an owned window is a dialog
    # A VERSION IN A TITLE IS NOT A NEW WINDOW (6 November 2026): HomerDev's main window has a hidden owner and is titled
    # "HomerDev 1.159.0", so each release would have keyed a new window and scanned it again; numbers like 1.159.0 are
    # left out of the key.
    import re as reLocal
    sTitle = reLocal.sub(r"\s*v?\d+(\.\d+)+", "", windowTitle(hWnd)).strip()
    return exeNameOf(iPid).lower() + " | " + ("main" if bMain else sTitle)


def loadScans():
    """axeScans.inix as {section: {key: value}}: [section] lines, then key = value lines."""
    dScans, sSection = {}, ""
    try:
        with open(scansFile(), encoding="utf-8-sig") as fIn:
            for sLine in fIn:
                sLine = sLine.strip()
                if not sLine or sLine.startswith(";"): continue
                if sLine.startswith("[") and sLine.endswith("]"):
                    sSection = sLine[1:-1]; dScans[sSection] = {}
                elif "=" in sLine and sSection:
                    sName, _, sValue = sLine.partition("=")
                    dScans[sSection][sName.strip()] = sValue.strip()
    except Exception: pass
    for d in dScans.values():
        d["lFindings"] = [d[k] for k in sorted((k for k in d if k.startswith("finding")), key=lambda k: int(k[7:] or 0))]
        try: d["iErrors"] = int(d.get("errors", ""))
        except ValueError: d["iErrors"] = None
    return dScans


def saveScan(sKey, sFingerprint, dResult):
    """This window's fingerprint and result into axeScans.inix, UTF-8 with a byte order mark and CRLF line endings, the
    other windows' sections kept. A JSON copy left by 1.155.0 is removed, so only the .inix remains."""
    dScans = loadScans()
    dScans[sKey.replace("[", "(").replace("]", ")")] = {"fingerprint": sFingerprint, "date": datetime.datetime.now().strftime("%d %B %Y"),
        "errors": "" if dResult["iErrors"] is None else str(dResult["iErrors"]), "file": dResult["sFile"] or "",
        "problem": dResult.get("sProblem", "") or "", "lFindings": dResult["lFindings"][:300]}
    lLines = ["; axeScans.inix -- the last Axe.Windows scan of each window, kept by axeWindow so an unchanged window is not scanned again", ""]
    for sSection in sorted(dScans, key=str.lower):
        d = dScans[sSection]
        lLines.append("[" + sSection + "]")
        for sName in ("fingerprint", "date", "errors", "file", "problem"):
            lLines.append(sName + " = " + str(d.get(sName, "")))
        for iAt, sFinding in enumerate(d.get("lFindings", []), 1):
            lLines.append("finding%d = %s" % (iAt, sFinding.replace("\r", " ").replace("\n", " ")))
        lLines.append("")
    try:
        os.makedirs(os.path.dirname(scansFile()), exist_ok=True)
        with open(scansFile(), "w", encoding="utf-8-sig", newline="\r\n") as fOut: fOut.write("\n".join(lLines))
        # SAID IN THE LOG (9 November 2026): a kept record was silent, so no one could tell from the logs that an
        # unchanged window would be skipped next time.
        logLine("scan record kept for %s in %s: fingerprint %s, %s" % (sKey, scansFile(), sFingerprint[:16],
            ("problem: " + dResult["sProblem"]) if dResult.get("sProblem") else ("%s error(s)" % dResult["iErrors"])))
        sOld = os.path.join(os.path.dirname(scansFile()), "axeScans.json")
        if os.path.isfile(sOld): os.remove(sOld); logLine("removed " + sOld + "; axeScans.inix replaces it")
    except Exception as oError: logLine("scan record not saved: " + str(oError))


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
    # UNCHANGED SINCE ITS LAST SCAN: the earlier result stands, and nothing is scanned.
    sKey, sFingerprint = "", ""
    try:
        sKey = windowKey(iPid, hWnd)
        sFingerprint, iControls = windowFingerprint(hWnd)
        dLast = loadScans().get(sKey.replace("[", "(").replace("]", ")"))
        logLine("fingerprint of %s: %s, %d controls; last %s" % (sKey, sFingerprint[:16], iControls, (dLast or {}).get("fingerprint", "none")[:16]))
        if dLast and dLast.get("fingerprint") == sFingerprint and dLast.get("iErrors") is not None:
            iLast = int(dLast["iErrors"])
            speak("%s is unchanged since its scan on %s: %d error%s then." % (sName, dLast.get("date", "an earlier day"), iLast, "" if iLast == 1 else "s"))
            dResult.update({"iErrors": iLast, "lFindings": list(dLast.get("lFindings", [])), "sFile": dLast.get("sFile", ""), "bUnchanged": True})
            return dResult
        # A SCAN THAT COULD NOT FINISH IS NOT TRIED AGAIN ON THE SAME WINDOW (9 November 2026). DbDo's main window has
        # never finished within the time allowed, so nothing was kept and every check scanned it for 5 minutes more.
        # Its outcome is kept now, like a finished scan's, and repeated while the window is unchanged; any change to
        # the window scans it again, and removing its section from %LOCALAPPDATA%\\HomerDev\\axeScans.inix forces one.
        if dLast and dLast.get("fingerprint") == sFingerprint and dLast.get("problem"):
            speak("%s is unchanged since %s, when its scan did not finish; not scanned again." % (sName, dLast.get("date", "an earlier day")))
            dResult.update({"sProblem": "unchanged since %s, when %s" % (dLast.get("date", "an earlier day"), dLast["problem"]), "bUnchanged": True})
            return dResult
    except Exception:
        logLine("fingerprint not taken: " + traceback.format_exc())
    # SPOKEN FIRST, EVEN BEFORE THE LIBRARY LOADS (5 November 2026, night): a first load fetches packages from NuGet,
    # and a failure there had been silent.
    speak("Scanning " + sName + " for accessibility.")
    try:
        oNs = loadAxe()
    except Exception as oError:
        logLine("Axe.Windows library not loaded: " + traceback.format_exc())
        dResult["sProblem"] = "the Axe.Windows library could not be loaded: %s" % oError
        speak("The accessibility scan could not start; the log says why.")
        return dResult
    os.makedirs(sFolder, exist_ok=True)
    dShared = {}
    def work():
        try:
            import System
            oConfig = oNs.Config.Builder.ForProcessId(iPid).WithOutputFileFormat(oNs.OutputFileFormat.A11yTest).WithOutputDirectory(sFolder).Build()
            oScanner = oNs.ScannerFactory.CreateScanner(oConfig)
            dShared["oOutput"] = oScanner.Scan(scanOptions(sScanId, hWnd))
        except Exception:
            dShared["sError"] = traceback.format_exc()
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
                if sKey and sFingerprint: saveScan(sKey, sFingerprint, dResult)
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
    if sKey and sFingerprint: saveScan(sKey, sFingerprint, dResult)
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


def scanProgramWindow(sExe, sRoot, sApp, sLogDir, iLimit=300):
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
    return "warn", ("Axe.Windows: %d error%s in the window %s, " + str(axeScan.iToReview) + " to review, %d new; review %s before changing anything -- never a name the reader already has"
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
    oParser.add_argument("--fetch", action="store_true", help="get the Axe.Windows library once and stop (the build does this)")
    oParser.add_argument("--fresh", action="store_true", help="with --fetch, get the newest again")
    oArgs = oParser.parse_args()
    sRoot = os.getcwd()
    if os.path.basename(sRoot).lower() == "scripts": sRoot = os.path.dirname(sRoot)
    sLogDir = os.path.join(sRoot, "logs"); os.makedirs(sLogDir, exist_ok=True)
    sApp = oArgs.app or os.path.basename(sRoot)
    sStamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    sLog = os.path.join(sLogDir, "%s-axeWindow-%s.log" % (sApp, sStamp))
    logLine("axeWindow %s; Python %s at %s; %s; working folder %s; arguments %s" % (os.path.abspath(__file__), platform.python_version(), sys.executable, platform.platform(), os.getcwd(), sys.argv[1:]))
    if oArgs.fetch:
        try: print("The Axe.Windows library is ready: " + fetchLibrary(oArgs.fresh)); return 0
        except Exception as oError:
            logLine(traceback.format_exc()); print("The Axe.Windows library could not be had: %s; the log says why." % oError); return 1
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
