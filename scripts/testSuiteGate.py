r"""testSuiteGate: proves the suite commands gate fails what it must (HomerDev 1.235.0, 15 November 2026).

    testSuiteGate       run the checks; exit 0 when every one behaves as expected

The keyboard audit Claude and ChatGPT agreed on 15 November found that the gate passed a key file that left shared
commands out, and one that named none at all. scripts\suiteCatalog.py now catches both. This test feeds it small key
files made for the purpose, against a small catalog, and checks each verdict:
  1. a key file that matches passes;
  2. the suite's key given as a second key (an alias) passes;
  3. a wrong key fails;
  4. a different sentence fails;
  5. a command the catalog gives the app (apps=) but the key file leaves out fails;
  6. a key file naming no shared command fails;
  7. a key exception the catalog records ([keys <App>]) passes;
  8. the kit's own catalog parses, and every command in it has a key line and a sentence.
And for the exported keys check (1.238.0), suiteCatalog.exportBreaks against a small export:
  9. an export that binds what the key file shows passes;
 10. a key shown but not bound (a false alias) is found;
 11. a key bound but not shown is found;
 12. an empty export is found.
Every check goes to logs\HomerDev-testSuiteGate-<time>.log with what was expected and what happened. The kit's build
runs it."""

import datetime, os, platform, sys, traceback

sScriptDir = os.path.dirname(os.path.abspath(__file__))
sRoot = os.path.dirname(sScriptDir)
if sScriptDir not in sys.path: sys.path.insert(0, sScriptDir)
from kind import writableLogDir
sLogDir = writableLogDir(sRoot)   # the kit's logs, or %LOCALAPPDATA%\\HomerDev\\logs for a kit in Program Files (1.239.0)
sLog = os.path.join(sLogDir, "HomerDev-testSuiteGate-%s.log" % datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
if sScriptDir not in sys.path: sys.path.insert(0, sScriptDir)
import suiteCatalog

sCatalog = """[words Demo]
thing=record
[command Copy]
apps=Demo
key=Control+C
description=Copy the current {thing} to the clipboard
[command Say Status]
apps=Demo
key=Shift+Z
description=Say the status of {app}
[command Rename]
key=F2
description=Rename the current {thing}
[keys Demo]
Rename=Shift+F2
"""


def logLine(sText):
    with open(sLog, "a", encoding="utf-8") as oFile: oFile.write(datetime.datetime.now().isoformat(timespec="milliseconds") + "  " + sText + "\n")
    return True


def sayLine(sText):
    print(sText)
    logLine("CONSOLE: " + sText)
    return True


def keyFile(lsLines):
    return "[Hotkeys]\n" + "\n".join(lsLines) + "\n"


def main():
    logLine("testSuiteGate %s, python %s, %s, cwd %s" % (sys.argv[0], sys.version.split()[0], platform.platform(), os.getcwd()))
    sGood = "Copy=Control+C, Copy the current record to the clipboard"
    sStatus = "Say Status=Shift+Z, Say the status of Demo"
    lCases = [
        ("a matching key file passes", keyFile([sGood, sStatus]), 0, ""),
        ("the suite's key as an alias passes", keyFile([sGood, "Say Status=Alt+Z or Shift+Z, Say the status of Demo"]), 0, ""),
        ("a wrong key fails", keyFile(["Copy=Control+Insert, Copy the current record to the clipboard", sStatus]), 1, "suite's key"),
        ("a different sentence fails", keyFile(["Copy=Control+C, Copy the record", sStatus]), 1, "where the suite says"),
        ("a missing command fails", keyFile([sGood]), 1, "leaves it out"),
        ("a key file naming no shared command fails", keyFile(["Frobnicate=Alt+F, Do something else"]), 3, "names no shared command"),
        ("a recorded key exception passes", keyFile([sGood, sStatus, "Rename=Shift+F2, Rename the current record"]), 0, ""),
    ]
    iFailed = 0
    for sName, sText, iWanted, sWords in lCases:
        lBreaks, iShared = suiteCatalog.suiteBreaks(sCatalog, sText, "Demo")
        bPass = len(lBreaks) == iWanted and (not sWords or any(sWords in s for s in lBreaks))
        sayLine("%s %s: expected %d break%s%s; got %d%s" % ("PASS" if bPass else "FAIL", sName, iWanted, "" if iWanted == 1 else "s",
                " naming \"" + sWords + "\"" if sWords else "", len(lBreaks), (": " + " | ".join(lBreaks)) if lBreaks else ""))
        if not bPass: iFailed += 1
    # 8. the kit's own catalog
    sPath = os.path.join(sRoot, "data", "SuiteCatalog.inix")
    dCommands, dWords, dKeys = suiteCatalog.readCatalog(open(sPath, encoding="utf-8-sig").read())
    lsBad = [s for s, d in dCommands.items() if "key" not in d or not d.get("description")]
    bPass = len(dCommands) > 0 and not lsBad
    sayLine("%s the kit's catalog: %d commands%s" % ("PASS" if bPass else "FAIL", len(dCommands), (", without a key line or sentence: " + ", ".join(lsBad)) if lsBad else ", each with a key line and a sentence"))
    if not bPass: iFailed += 1
    # 9 to 12. the exported keys comparison
    sExport = "[Export]\napp=Demo\n[Command copy]\nname=&Copy\nkeys=Control+C\n[Command sayStatus]\nname=Say Status\nkeys=Shift+Z or Alt+Z\n"
    lExportCases = [
        ("an export that binds what is shown passes", sExport, keyFile(["Copy=Control+C, Copy", "Say Status=Shift+Z or Alt+Z, Say"]), 0, ""),
        ("a key shown but not bound is found", sExport, keyFile(["Copy=Control+C or Control+Insert, Copy", "Say Status=Shift+Z or Alt+Z, Say"]), 1, "does not bind"),
        ("a key bound but not shown is found", sExport, keyFile(["Copy=Control+C, Copy", "Say Status=Shift+Z, Say"]), 1, "does not show"),
        ("an empty export is found", "", keyFile(["Copy=Control+C, Copy"]), 1, "exported no commands"),
    ]
    for sName, sExportText, sText, iWanted, sWords in lExportCases:
        lBreaks, iCompared = suiteCatalog.exportBreaks(sExportText, sText, "Demo")
        bPass = len(lBreaks) == iWanted and (not sWords or any(sWords in s for s in lBreaks))
        sayLine("%s %s: expected %d difference%s; got %d%s" % ("PASS" if bPass else "FAIL", sName, iWanted, "" if iWanted == 1 else "s",
                len(lBreaks), (": " + " | ".join(lBreaks)) if lBreaks else ""))
        if not bPass: iFailed += 1
    sayLine("testSuiteGate: %d passed, %d failed. Log: %s" % (len(lCases) + 1 + len(lExportCases) - iFailed, iFailed, sLog))
    return 1 if iFailed else 0


if __name__ == "__main__":
    try: sys.exit(main())
    except Exception as oError:
        logLine(traceback.format_exc())
        sayLine("testSuiteGate stopped with: %s" % oError)
        sys.exit(1)
