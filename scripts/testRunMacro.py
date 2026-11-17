r"""testRunMacro.py -- the kit's proof that a macro script means what it says, without pressing a key.

WHY (17 November 2026). runMacro turns plain lines -- "Say Filter and Order", "Say Line", "Expect speech filter" --
into the keys recordWalk presses. A wrong key there presses the wrong command in a real app, with nobody watching,
so the translation is proved on every kit build where it changed: an app command by its key, one with no key by the
Alternate Menu, FileDir's character key names, a reader command by its JAWS key, "twice", Wait, Expect, and the
lines it must refuse. Then recordWalk's keysFor is proved on Homer's own key names, which it once typed as text.

Writes logs\HomerDev-testRunMacro-<stamp>.log. Exit code 0 when every check passed, 1 otherwise.
"""

import datetime, importlib.util, os, sys, tempfile, traceback

sScriptDir = os.path.dirname(os.path.abspath(__file__))
sProject = os.path.dirname(sScriptDir)
sStamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
sLogPath = os.path.join(sProject, "logs", "HomerDev-testRunMacro-" + sStamp + ".log")
lsResults = []


def logLine(sText):
    os.makedirs(os.path.dirname(sLogPath), exist_ok=True)
    with open(sLogPath, "a", encoding="utf-8-sig") as fLog:
        fLog.write(datetime.datetime.now().strftime("%H:%M:%S") + "  " + sText + "\n")
    return True


def check(sWhat, vActual, vWanted):
    bPass = vActual == vWanted
    lsResults.append(bPass)
    logLine("%s %s: wanted %r, got %r" % ("PASS" if bPass else "FAIL", sWhat, vWanted, vActual))
    if not bPass: print("FAIL " + sWhat)
    return bPass


def loadModule(sName):
    oSpec = importlib.util.spec_from_file_location(sName, os.path.join(sScriptDir, sName + ".py"))
    oModule = importlib.util.module_from_spec(oSpec)
    oSpec.loader.exec_module(oModule)
    return oModule


def main():
    logLine("testRunMacro: Python %s; %s" % (sys.version.split()[0], sys.platform))
    oRunMacro = loadModule("runMacro")
    sFolder = tempfile.mkdtemp(prefix="HomerRunMacro-")
    os.makedirs(os.path.join(sFolder, "configs"))
    sKeyFile = os.path.join(sFolder, "configs", "Hotkeys.inix")
    with open(sKeyFile, "w", encoding="utf-8-sig") as fOut:
        fOut.write("[Hotkeys]\nSay Filter and Order=Shift+8, Say the filter and the order in force\n"
                   "Say What Content=Question, Say the current file's text\n"
                   "Say Selected=JAWS+Shift+DownArrow or Shift+Space, Say the selected items\n"
                   "Show in FileDir=None, Open this page's folder in FileDir\n"
                   "Say Line=Alt+Shift+L, An app command named like a reader command\n")
    dCommands = oRunMacro.appCommands(sKeyFile)
    check("command count", len(dCommands), 5)
    check("character key", dCommands["say what content"][1], "Shift+Slash")
    check("first key without a reader key", dCommands["say selected"][1], "Shift+Space")
    dReader = dict(oRunMacro.dJawsFallback)
    lSteps = [(1, "Say Filter and Order twice"), (2, "Expect speech filter"), (3, "Wait 2"), (4, "Say What Content"),
              (5, "Show in FileDir"), (6, "Say Window Title"), (7, "JAWS Say Line"), (8, "Say Line"),
              (9, 'Type "a=b"'), (10, "Press Control+Shift+F"), (11, "Expect window Filter"), (12, "Say Title")]
    lWalk, lsProblems = oRunMacro.translate(lSteps, dCommands, dReader, "FileDir")
    check("no problems", lsProblems, [])
    check("twice", (lWalk[0]["sKey"], lWalk[0]["iPress"]), ("Shift+8", 2))
    check("expect speech", lWalk[0]["lHear"], ["filter"])
    check("wait becomes a pause", lWalk[1]["nPause"], 2.0)
    check("the character key", lWalk[1]["sKey"], "Shift+Slash")
    check("keyless command, in order", [d["sKey"] for d in lWalk[2:6]], ["Alt+F10", "Control+F", "Enter", "Enter"])
    check("keyless command, the Alternate Menu expected", lWalk[2]["lWindow"], ["Alternate Menu"])
    check("keyless command, the name typed", lWalk[4]["sType"], "Show in FileDir,")
    check("reader command", lWalk[6]["sKey"], "Insert+T")
    check("JAWS forces the reader", lWalk[7]["sKey"], "Insert+UpArrow")
    check("the app's command wins", lWalk[8]["sKey"], "Alt+Shift+L")
    check("type keeps an equals sign", lWalk[9]["sType"], "a=b")
    check("expect window", lWalk[10]["lWindow"], ["Filter"])
    check("reader alias", lWalk[11]["sKey"], "Insert+T")
    lBad, lsBad = oRunMacro.translate([(1, "Expect speech hello"), (2, "Frobnicate the widget"), (3, "Run Nothing Here"),
                                       (4, "Start DbDo"), (5, "Wait soon")], dCommands, dReader, "FileDir")
    check("refusals", len(lsBad), 5)
    # A whole file, through readMacro and play --check.
    sMacro = os.path.join(sFolder, "sample.inix")
    with open(sMacro, "w", encoding="utf-8-sig") as fOut:
        fOut.write("FileTask = macroScript\nApp = FileDir\n\n[steps]\n; a note\nSay Filter and Order\nExpect speech filter\n")
    dHeader, lsLines = oRunMacro.readMacro(sMacro)
    check("header", dHeader.get("filetask"), "macroScript")
    check("steps read, notes left out", [s for i, s in lsLines], ["Say Filter and Order", "Expect speech filter"])
    oRunMacro.sLogPath = os.path.join(sFolder, "runMacro.log")
    check("play --check", oRunMacro.play(sMacro, bCheck=True, sProject=sFolder), 0)
    # recordWalk's keys, by Homer's names.
    sys.argv = [sys.argv[0]]
    oRecordWalk = loadModule("recordWalk")
    for sKey, sWanted in [("Shift+Slash", "+/"), ("Control+Shift+Backslash", "^+\\"), ("Alt+UpArrow", "%{UP}"),
                          ("Shift+LeftBracket", "+{[}"), ("NumPadStar", "{VK_MULTIPLY}"), ("Control+PageDown", "^{PGDN}"),
                          ("Alt+Semicolon", "%;"), ("Shift+8", "+8")]:
        check("keysFor " + sKey, oRecordWalk.keysFor(sKey), sWanted)
    iPassed = sum(1 for b in lsResults if b)
    sSummary = "testRunMacro: %d passed, %d failed" % (iPassed, len(lsResults) - iPassed)
    logLine(sSummary)
    print(sSummary + ("." if iPassed == len(lsResults) else "; the log names each: " + sLogPath))
    return 0 if iPassed == len(lsResults) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        logLine("ERROR " + traceback.format_exc())
        print("testRunMacro stopped on an error; the log says why: " + sLogPath)
        sys.exit(1)
