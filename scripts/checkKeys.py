r"""checkKeys.py -- check the Homer Suite's commands and keys against the suite contract.

Usage (through checkKeys.cmd):

    checkKeys                      check the kit's manifest and ownership data
    checkKeys DbDo-keys.inix ...   also check files an app wrote with /exportkeys
    checkKeys --gate               exit 1 when a problem is found (for a build)
    checkKeys --app DbDo           check one app's manifest entries and exports
    checkKeys --app DbDo --source C:\DbDo
                                   also check that the app's source calls the
                                   shared code its manifest entries name

What it reads, all in the kit:
    data\SuiteCommands.inix    every command of the four apps, with its keys
    data\KeyOwnership.inix     keys owned by Windows, screen readers and browsers
    exec\CSharp\KeyMap.cs      its short reserved-key table, compared with the above

What it reports: duplicate identifiers; a key bound twice in one app; a key a
system or a screen reader takes everywhere; keys to test in their real control
(laptop-layout and table keys, input-method keys); hotkey letters that are not
the first letter of a word; for each export, every difference between
what the program declared and what the manifest says; and ONE NAME, ONE PIECE
OF CODE (kit 1.74.0): a manifest command with a shared= line names a method of
SuiteCommands in exec\CSharp\Mdi.cs, which must exist, and which the app's own
.cs files must call when --source gives the app's folder.

The kit's build runs it on every build, with the export of the MDI sample, so
nobody needs to run it by hand. Report-only unless --gate is given: stage 2 of
the suite plan turns the gate on.
The console says briefly what was found; the log in the kit's logs folder,
HomerDev-checkKeys-<stamp>.log, holds every finding and the environment.
Camel Type throughout.
"""

import datetime
import os
import platform
import re
import sys
import traceback

sScriptDir = os.path.dirname(os.path.abspath(__file__))
sKitDir = os.path.dirname(sScriptDir)
sLogPath = os.path.join(sKitDir, "logs", "HomerDev-checkKeys-%s.log" % datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
oLog = None
lsModifierOrder = ["Alt", "Control", "Shift", "Windows"]


def logLine(sText):
    if oLog is not None:
        oLog.write(datetime.datetime.now().astimezone().isoformat(timespec="milliseconds") + " INFO  " + sText + "\n")


def sayLine(sText):
    print(sText)
    logLine(sText)


def plural(iCount, sNoun):
    if iCount == 1:
        return "1 " + sNoun
    return "%d %s" % (iCount, sNoun + ("es" if sNoun.endswith(("s", "sh", "ch", "x")) else "s"))


def readInix(sPath):
    """Sections in file order, each a dictionary; repeated section names are kept apart."""
    lsSections = []
    dNow = None
    sText = open(sPath, "rb").read().decode("utf-8-sig")
    for sLine in sText.splitlines():
        sTrim = sLine.strip()
        if sTrim == "" or sTrim.startswith(";") or sTrim.startswith("#"):
            continue
        if sTrim.startswith("[") and sTrim.endswith("]"):
            dNow = {"": sTrim[1:-1].strip()}
            lsSections.append(dNow)
            continue
        if dNow is not None and "=" in sTrim:
            sKey, sValue = sTrim.split("=", 1)
            dNow[sKey.strip().lower()] = sValue.strip()
    return lsSections


# THE READER IS FORGIVING, THE WRITER IS NOT (1.73.2): the manifest and the
# exports are written in KeyName.cs's spellings, taken from JAWS's own
# default.jkm (GraveAccent, Backslash, SemiColon), but a key typed another way
# still compares equal.
dKeyAliases = {"accent": "GraveAccent", "grave": "GraveAccent", "graveaccent": "GraveAccent",
               "backslash": "Backslash", "semicolon": "SemiColon", "ctrl": "Control",
               "minus": "Dash", "hyphen": "Dash", "back": "Backspace", "backspace": "Backspace"}


def normKey(sKey):
    lsParts = [dKeyAliases.get(s.strip().lower(), s.strip()) for s in sKey.split("+") if s.strip()]
    lsMods = sorted([s for s in lsParts if s in lsModifierOrder], key=lsModifierOrder.index)
    lsRest = [s for s in lsParts if s not in lsModifierOrder]
    return "+".join(lsMods + lsRest)


def splitKeys(sKeys):
    return [normKey(s) for s in re.split(r"\s+or\s+", sKeys or "") if s.strip()]


def firstLetterMiss(sName, sKey):
    """True when a letter key's letter starts no word of the command's name."""
    lsParts = sKey.split("+")
    sBase = lsParts[-1]
    if "NVDA" in lsParts or "JAWS" in lsParts:
        return False                       # a screen reader key, checked in its own key map
    if len(lsParts) < 2 or len(sBase) != 1 or not sBase.isalpha():
        return False
    if sBase in "XZ":
        return False                       # X for export or cut, Z for toggles and status
    if sBase in "CVY" and "Control" in lsParts and "Alt" not in lsParts:
        return False                       # Windows' copy, paste and redo conventions
    lsWords = re.findall(r"[A-Za-z]+", sName)
    if any(sWord[0].upper() == sBase for sWord in lsWords):
        return False
    if "Shift" in lsParts and re.match(r"(Un|Reverse|Previous|Clear|Restore|Lower)", sName):
        return False                       # Shift reverses its partner command
    return True


def main():
    global oLog
    lsArgs = sys.argv[1:]
    bGate = "--gate" in [s.lower() for s in lsArgs]
    sOnlyApp = ""
    sSource = ""
    for i, sArg in enumerate(lsArgs):
        if sArg.lower() == "--app" and i + 1 < len(lsArgs):
            sOnlyApp = lsArgs[i + 1]
        if sArg.lower() == "--source" and i + 1 < len(lsArgs):
            sSource = lsArgs[i + 1]
    lsExports = [s for i, s in enumerate(lsArgs) if not s.startswith("--") and not (i > 0 and lsArgs[i - 1].lower() in ("--app", "--source"))]
    os.makedirs(os.path.dirname(sLogPath), exist_ok=True)
    oLog = open(sLogPath, "w", encoding="utf-8-sig", newline="\r\n")
    logLine("checkKeys start")
    logLine("script: " + os.path.abspath(__file__))
    logLine("python: " + platform.python_version() + ", " + platform.platform())
    logLine("working directory: " + os.getcwd())
    logLine("command line: " + " ".join(sys.argv))
    logLine("kit: " + sKitDir + ", gate: " + str(bGate) + ", app: " + (sOnlyApp or "all") + ", source: " + (sSource or "none"))

    lsProblems = []
    lsExceptions = []
    lsToTest = []
    lsLetterMisses = []

    lsCommands = [d for d in readInix(os.path.join(sKitDir, "data", "SuiteCommands.inix")) if " " in d[""]]
    if sOnlyApp:
        lsCommands = [d for d in lsCommands if d[""].split(" ", 1)[0].lower() == sOnlyApp.lower()]
    lsOwnership = [d for d in readInix(os.path.join(sKitDir, "data", "KeyOwnership.inix")) if d[""].startswith("Key ")]
    dOwned = {}
    for d in lsOwnership:
        dOwned[normKey(d[""][4:])] = d
    logLine("manifest: %s; ownership: %s" % (plural(len(lsCommands), "command"), plural(len(dOwned), "key")))

    # Identifiers and keys, per app.
    dSeenIds = {}
    dAppKeys = {}
    dExceptions = {}
    for d in lsCommands:
        sApp, sId = d[""].split(" ", 1)
        if d.get("change", "").startswith("removed"):
            continue
        if (sApp, sId) in dSeenIds:
            lsProblems.append("%s: the identifier %s is used twice" % (sApp, sId))
        dSeenIds[(sApp, sId)] = d
        if d.get("exception"):
            dExceptions[(sApp, d.get("name", sId))] = d.get("exception")
        for sKey in splitKeys(d.get("keys", "")):
            dAppKeys.setdefault(sApp, {}).setdefault(sKey, []).append(d.get("name", sId))
            dOwner = dOwned.get(sKey)
            if dOwner is not None:
                sKind = dOwner.get("kind", "")
                sWhere = "%s %s (%s): %s %s, %s" % (sApp, d.get("name", sId), sKey, dOwner.get("owner"), sKind, dOwner.get("what"))
                if sKind in ("system", "reader global") and not dOwner.get("disposition", "").startswith("approved"):
                    if not (sApp == "HomerView" and sKind == "reader global"):
                        lsProblems.append(sWhere + " -- " + dOwner.get("disposition", ""))
                elif sKind in ("reader laptop", "reader tables", "conditional"):
                    lsToTest.append(sWhere + " -- " + dOwner.get("disposition", ""))
            if firstLetterMiss(d.get("name", ""), sKey):
                lsLetterMisses.append("%s %s: %s" % (sApp, d.get("name", sId), sKey))
    # A KEY SHARED ON PURPOSE IS AN EXCEPTION, NOT A PROBLEM (1.73.1): every
    # command but one sharing the key must carry an exception= line in the
    # manifest saying why, so the gate stops only on sharing nobody reviewed.
    for sApp, dKeys in sorted(dAppKeys.items()):
        for sKey, lsNames in sorted(dKeys.items()):
            if len(lsNames) > 1:
                lsUnexplained = [s for s in lsNames if (sApp, s) not in dExceptions]
                sLine = "%s: %s is bound to %s" % (sApp, sKey, ", ".join(lsNames))
                if len(lsUnexplained) <= 1:
                    lsExceptions.append(sLine + " -- reviewed: " + "; ".join(dExceptions[(sApp, s)] for s in lsNames if (sApp, s) in dExceptions))
                else:
                    lsProblems.append(sLine + " -- give all but one an exception= line, or a different key")

    # KeyMap.cs's own table must agree with KeyOwnership.inix.
    sKeyMap = open(os.path.join(sKitDir, "exec", "CSharp", "KeyMap.cs"), "rb").read().decode("utf-8-sig")
    oMatch = re.search(r"aReserved = new string\[\] \{(.*?)\};", sKeyMap, re.S)
    lsTable = re.findall(r'"([^"|]+)\|', oMatch.group(1)) if oMatch else []
    logLine("KeyMap.cs reserved table: %s" % plural(len(lsTable), "key"))
    for sKey in lsTable:
        dOwner = dOwned.get(normKey(sKey))
        if dOwner is None:
            lsProblems.append("KeyMap.cs reserves %s, which KeyOwnership.inix does not list" % sKey)
        elif dOwner.get("kind") not in ("system", "reader global", "conditional"):
            lsProblems.append("KeyMap.cs reserves %s, which KeyOwnership.inix calls %s" % (sKey, dOwner.get("kind")))

    # ONE NAME, ONE PIECE OF CODE (1.74.0). A shared= line names the
    # SuiteCommands method the command must run. The method must exist in the
    # kit, and, given the app's folder, the app's own C# must call it.
    sMdi = open(os.path.join(sKitDir, "exec", "CSharp", "Mdi.cs"), "rb").read().decode("utf-8-sig")
    oClass = re.search(r"public static class SuiteCommands \{(.*?)\n\}", sMdi, re.S)
    setMethods = set(re.findall(r"public static bool (\w+)\(", oClass.group(1))) if oClass else set()
    logLine("SuiteCommands methods: " + (", ".join(sorted(setMethods, key=str.lower)) or "none found"))
    sAppCode = ""
    if sSource and sOnlyApp:
        for sName in sorted(os.listdir(sSource)) if os.path.isdir(sSource) else []:
            if sName.lower().endswith(".cs"):
                sAppCode += open(os.path.join(sSource, sName), "rb").read().decode("utf-8-sig", "replace") + "\n"
        logLine("source: %s, %s of C#" % (sSource, plural(sAppCode.count("\n"), "line")))
    iShared = 0
    for (sApp, sId), d in sorted(dSeenIds.items()):
        sMethod = d.get("shared", "").strip()
        if not sMethod:
            continue
        iShared += 1
        if sMethod not in setMethods:
            lsProblems.append("%s %s: shared=%s, but SuiteCommands has no such method" % (sApp, d.get("name", sId), sMethod))
        elif sAppCode and not re.search(r"\bSuiteCommands\." + re.escape(sMethod) + r"\b", sAppCode):
            lsProblems.append("%s %s: its source does not call SuiteCommands.%s, the shared code its manifest entry names" % (sApp, d.get("name", sId), sMethod))
    logLine("shared commands checked: %d" % iShared)

    # Exports written by the programs themselves.
    for sExport in lsExports:
        lsSections = readInix(sExport)
        dHead = next((d for d in lsSections if d[""] == "Export"), {})
        sApp = dHead.get("app", os.path.basename(sExport))
        dDeclared = {d[""][8:]: d for d in lsSections if d[""].startswith("Command ")}
        dManifest = {k[1]: v for k, v in dSeenIds.items() if k[0].lower() == sApp.lower()}
        logLine("export %s: app %s, %s; manifest has %s" % (sExport, sApp, plural(len(dDeclared), "command"), plural(len(dManifest), "command")))
        if not dManifest:
            logLine("%s is not in the suite manifest (a sample or a new app), so its export is checked for problems only" % sApp)
        for sId, d in sorted(dDeclared.items()):
            if dManifest and sId not in dManifest:
                lsProblems.append("%s declares %s (%s), which the manifest does not list" % (sApp, sId, d.get("name")))
            elif dManifest and splitKeys(d.get("keys", "")) != splitKeys(dManifest[sId].get("keys", "")):
                lsProblems.append("%s %s: the program binds %s, the manifest says %s"
                                  % (sApp, sId, d.get("keys") or "no key", dManifest[sId].get("keys") or "no key"))
        for sId in sorted(dManifest):
            if dDeclared and sId not in dDeclared:
                lsProblems.append("%s: the manifest lists %s, which the program does not declare" % (sApp, sId))
        for d in lsSections:
            if d[""] == "Problems":
                for sKey, sValue in sorted(d.items()):
                    if sKey:
                        lsProblems.append("%s reported: %s" % (sApp, sValue))

    for sLine in lsProblems:
        logLine("PROBLEM: " + sLine)
    for sLine in lsExceptions:
        logLine("EXCEPTION: " + sLine)
    for sLine in lsToTest:
        logLine("TO TEST: " + sLine)
    for sLine in lsLetterMisses:
        logLine("LETTER: " + sLine)
    sayLine("checkKeys%s: %s, %s reviewed, %s to test in their real control, %s." % (
        (" " + sOnlyApp) if sOnlyApp else "", plural(len(lsProblems), "problem"), plural(len(lsExceptions), "shared key"),
        plural(len(lsToTest), "key"), plural(len(lsLetterMisses), "first-letter miss")))
    sayLine("Details: " + sLogPath)
    logLine("checkKeys end")
    return 1 if (bGate and lsProblems) else 0


if __name__ == "__main__":
    iCode = 1
    try:
        iCode = main()
    except Exception:
        if oLog is not None:
            logLine("TRACEBACK:\n" + traceback.format_exc())
        print("checkKeys could not finish. The details are in %s." % sLogPath)
    finally:
        if oLog is not None:
            oLog.close()
    sys.exit(iCode)
