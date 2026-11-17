r"""jawsKeys.py -- the JAWS pass-through keys of a Homer app, kept by tidy.

Some keys a Homer app binds are taken by JAWS everywhere before the app sees
them. Where the suite has decided the app's command is the useful one -- Alt+
Delete, Say Position, instead of JAWS's pixel coordinates (Jamal's ruling of 18
October 2026) -- the app's own JAWS key map hands the key on with
TypeCurrentScriptKey. Which keys may be handed on is the REVIEWED ALLOWLIST in
the kit's data\KeyOwnership.inix (passThrough=yes), never every key JAWS owns:
a screen reader's commands are capabilities to keep, not obstacles.

ensure(sRoot, sApp, sKitDir) is called by the kit's tidy, which runs after every
build and before every push, so the key map is right without anybody editing it:

  * A key is handed on only when the app really binds it: its name appears in
    the app's own generated help\Hotkeys.md. A key the app does not yet bind
    keeps its JAWS meaning.
  * The lines live in a marked block in [Common Keys]; lines outside the block
    are the app's own and are left alone, and a key the app already maps to a
    script of its own is never overridden.
  * Bracket keys written as a bare "[" or "]" are renamed LeftBracket and
    RightBracket: a line beginning "[" is read by JAWS as a new section.
  * The file keeps its own encoding and line endings; it is written only when
    something changed.
  * THE SCRIPT THE KEY MAP NAMES MUST EXIST (17 November 2026). A .jkm line
    binds a key to a SCRIPT, and TypeCurrentScriptKey is a JAWS function, not a
    script. FileDir and EdSharp define a script of that name; DbDo did not, so
    JAWS answered Alt+Delete by spelling "unknown script TypeCurrentScriptKey"
    and DbDo never got the key -- found by DbDo's first live test. When the
    app's <App>.jss has no such script, a marked one that hands the key on
    quietly is added.

It also answers missing(sRoot, sApp, sKitDir) for the shared check. Camel Type.
"""

import os
import re

sBlockStart = "; Homer suite pass-through -- written by the kit's tidy from data\\KeyOwnership.inix; do not edit"
sBlockEnd = "; end of Homer suite pass-through"
sScriptStart = "; Homer suite pass-through script -- written by the kit's tidy, because the key map names it; do not edit"
sScriptEnd = "; end of Homer suite pass-through script"


def readInixSections(sPath):
    lsSections = []
    dNow = None
    for sLine in open(sPath, "rb").read().decode("utf-8-sig").splitlines():
        sTrim = sLine.strip()
        if not sTrim or sTrim.startswith(";"):
            continue
        if sTrim.startswith("[") and sTrim.endswith("]"):
            dNow = {"": sTrim[1:-1].strip()}
            lsSections.append(dNow)
        elif dNow is not None and "=" in sTrim:
            sKey, sValue = sTrim.split("=", 1)
            dNow[sKey.strip().lower()] = sValue.strip()
    return lsSections


def allowlist(sKitDir, sApp):
    """The keys the suite allows an app's JAWS key map to hand on."""
    sPath = os.path.join(sKitDir, "data", "KeyOwnership.inix")
    if not os.path.isfile(sPath):
        return []
    lsKeys = []
    for d in readInixSections(sPath):
        if not d[""].startswith("Key ") or d.get("passthrough", "").lower() != "yes":
            continue
        sExcept = d.get("passthroughexcept", "")
        if re.match(r"\s*%s\b" % re.escape(sApp), sExcept, re.I):
            continue
        lsKeys.append(d[""][4:].strip())
    return lsKeys


def keyMapPath(sRoot, sApp):
    sFolder = os.path.join(sRoot, "scripts", "jaws")
    if not os.path.isdir(sFolder):
        return ""
    for sName in os.listdir(sFolder):
        if sName.lower() == (sApp + ".jkm").lower():
            return os.path.join(sFolder, sName)
    return ""


def boundKeys(sRoot, lsKeys):
    """The allowlisted keys the app really binds, read from its own Hotkeys.md."""
    sDoc = os.path.join(sRoot, "help", "Hotkeys.md")
    if not os.path.isfile(sDoc):
        return []
    sText = open(sDoc, "rb").read().decode("utf-8-sig", "replace")
    return [k for k in lsKeys if re.search(r"(?<![\w+])%s(?![\w+])" % re.escape(k), sText, re.I)]


def wantedText(sText, lsKeys):
    """The key map with bracket keys named and the pass-through block in place."""
    sEol = "\r\n" if "\r\n" in sText else "\n"
    lsLines = sText.replace("\r\n", "\n").split("\n")
    # Bracket keys by name: "[=x" would start a section.
    dBrackets = {"[": "LeftBracket", "]": "RightBracket"}
    for i, sLine in enumerate(lsLines):
        oMatch = re.match(r"^((?:[A-Za-z]+\+)*)([\[\]])=(.*)$", sLine)
        if oMatch:
            lsLines[i] = oMatch.group(1) + dBrackets[oMatch.group(2)] + "=" + oMatch.group(3)
    # Take out an old block, then find [Common Keys].
    lsOut = []
    bInBlock = False
    for sLine in lsLines:
        if sLine.strip() == sBlockStart:
            bInBlock = True
            continue
        if bInBlock:
            if sLine.strip() == sBlockEnd:
                bInBlock = False
            continue
        lsOut.append(sLine)
    lsLines = lsOut
    iCommon = next((i for i, s in enumerate(lsLines) if s.strip().lower() == "[common keys]"), -1)
    if iCommon < 0:
        lsLines = ["[Common Keys]"] + lsLines
        iCommon = 0
    iEnd = next((i for i in range(iCommon + 1, len(lsLines)) if lsLines[i].strip().startswith("[")), len(lsLines))
    dMapped = {}
    for s in lsLines[iCommon + 1:iEnd]:
        if "=" in s and not s.strip().startswith(";"):
            sKey, sScript = s.split("=", 1)
            dMapped[sKey.strip().lower()] = sScript.strip()
    lsBlock = [k + "=TypeCurrentScriptKey" for k in lsKeys if k.lower() not in dMapped]
    if lsBlock:
        lsLines[iCommon + 1:iCommon + 1] = [sBlockStart] + lsBlock + [sBlockEnd]
    return sEol.join(lsLines)


def scriptPath(sRoot, sApp):
    """The app's own <App>.jss, found without regard to case, or ""."""
    sFolder = os.path.join(sRoot, "scripts", "jaws")
    if not os.path.isdir(sFolder):
        return ""
    for sName in os.listdir(sFolder):
        if sName.lower() == (sApp + ".jss").lower():
            return os.path.join(sFolder, sName)
    return ""


def ensureScript(sRoot, sApp):
    """Adds Script TypeCurrentScriptKey to the app's .jss when its key map names it and no .jss here defines it.
    Returns what was done, or ""."""
    sMap, sJss = keyMapPath(sRoot, sApp), scriptPath(sRoot, sApp)
    if not sMap or not sJss:
        return ""
    if not re.search(r"=\s*TypeCurrentScriptKey\s*$", open(sMap, "rb").read().decode("utf-8-sig", "replace"), re.M | re.I):
        return ""
    sFolder = os.path.dirname(sJss)
    for sName in os.listdir(sFolder):
        if sName.lower().endswith((".jss", ".jsh")):
            sText = open(os.path.join(sFolder, sName), "rb").read().decode("utf-8-sig", "replace")
            if re.search(r"^\s*Script\s+TypeCurrentScriptKey\s*\(", sText, re.M | re.I):
                return ""
    binData = open(sJss, "rb").read()
    bBom = binData.startswith(b"\xef\xbb\xbf")
    sText = binData.decode("utf-8-sig", "replace")
    sEol = "\r\n" if "\r\n" in sText else "\n"
    lsBlock = ["", sScriptStart, "; Way: pass quietly. Where: everywhere in " + sApp + ". A key the suite hands on reaches the app.",
               "Script TypeCurrentScriptKey ()", "TypeCurrentScriptKey ()", "EndScript", sScriptEnd, ""]
    sNew = sText.rstrip("\r\n") + sEol + sEol.join(lsBlock)
    open(sJss, "wb").write((b"\xef\xbb\xbf" if bBom else b"") + sNew.encode("utf-8"))
    return "defined the script TypeCurrentScriptKey in " + os.path.basename(sJss)


def ensure(sRoot, sApp, sKitDir):
    """Put the app's key map right. Returns a list of what was done, empty when nothing was needed."""
    sPath = keyMapPath(sRoot, sApp)
    if not sPath:
        return []
    lsKeys = boundKeys(sRoot, allowlist(sKitDir, sApp))
    sScriptDone = ensureScript(sRoot, sApp)
    binData = open(sPath, "rb").read()
    bBom = binData.startswith(b"\xef\xbb\xbf")
    sText = binData.decode("utf-8-sig", "replace")
    sWanted = wantedText(sText, lsKeys)
    if sWanted == sText:
        return [sScriptDone] if sScriptDone else []
    open(sPath, "wb").write((b"\xef\xbb\xbf" if bBom else b"") + sWanted.encode("utf-8"))
    lsDone = []
    if re.search(r"^(?:[A-Za-z]+\+)*[\[\]]=", sText, re.M):
        lsDone.append("named its bracket keys")
    if lsKeys:
        lsDone.append("passes " + ", ".join(lsKeys) + " to " + sApp)
    if sScriptDone: lsDone.append(sScriptDone)
    return lsDone or ["updated"]


def missing(sRoot, sApp, sKitDir):
    """The keys the app binds that its key map does not yet hand on, for the shared check."""
    sPath = keyMapPath(sRoot, sApp)
    if not sPath:
        return []
    lsKeys = boundKeys(sRoot, allowlist(sKitDir, sApp))
    sText = open(sPath, "rb").read().decode("utf-8-sig", "replace")
    return [k for k in lsKeys if not re.search(r"^%s=" % re.escape(k), sText, re.M | re.I)]


# ---- THE AUDIT (17 November 2026) ----
# JAWS answered two of DbDo's keys with errors in testSay: "unknown script call to TypeCurrentScriptKey" and "not in
# a table". Both are the kinds of mistake a JAWS scripter checks by hand: a key map line names a script, so that
# script must be defined -- spelled the same, in the app's own .jss or .jsh, or among JAWS's own scripts -- and a key
# the app binds must not be left to a JAWS script that works only somewhere else, such as a table cell command. The
# audit reads JAWS's own default.jkm on this computer, when there is one, to know JAWS's scripts and keys.

# JAWS's scripts that only work in a table, or that move the mouse: left to them, an app's key never reaches the app.
lsContextScripts = ["downcell", "movetobottomofcolumn", "movetoendofrow", "movetostartofrow", "movetotopofcolumn",
                    "nextcell", "priorcell", "saycell", "upcell", "leftmousebutton", "mousedown", "mouseleft",
                    "mouseright", "mouseup", "rightmousebutton"]


def jawsDefaultMap():
    """The newest JAWS default.jkm on this computer, the user's copy first, or ""."""
    import glob
    for sBase in (os.environ.get("APPDATA", ""), os.environ.get("ProgramData", "")):
        if not sBase:
            continue
        lsFound = glob.glob(os.path.join(sBase, "Freedom Scientific", "JAWS", "*", "Settings", "enu", "default.jkm"))
        if lsFound:
            return sorted(lsFound, key=lambda s: [int(x) if x.isdigit() else 0 for x in re.split(r"[.\\/]", s)])[-1]
    return ""


def canonicalKey(sKey):
    """A key in one spelling for comparing: modifiers sorted, JAWSKey and Insert as JAWS, lower case."""
    lsParts = [s.strip().lower() for s in re.split(r"\+(?!$)", sKey.strip()) if s.strip()]
    lsParts = ["jaws" if s in ("jawskey", "insert") else "control" if s == "ctrl" else s for s in lsParts]
    return "+".join(sorted(lsParts[:-1]) + lsParts[-1:])


def keyMapLines(sPath):
    """[(section, key, script, line number)] of a .jkm's key lines."""
    lsLines, sSection = [], ""
    for iLine, sRaw in enumerate(open(sPath, "rb").read().decode("utf-8-sig", "replace").splitlines(), 1):
        sLine = sRaw.strip()
        if sLine.startswith("["):
            sSection = sLine.lower()
            continue
        if not sLine or sLine.startswith(";") or "=" not in sLine or sSection == "[keyboard layouts]":
            continue
        sKey, sScript = [s.strip() for s in sLine.split("=", 1)]
        lsLines.append((sSection, sKey, sScript, iLine))
    return lsLines


def audit(sRoot, sApp, sDefaultMap=""):
    """Problems in the app's JAWS key maps, each a plain sentence; [] when there are none."""
    sFolder = os.path.join(sRoot, "scripts", "jaws")
    if not os.path.isdir(sFolder):
        return []
    sDefaultMap = sDefaultMap or jawsDefaultMap()
    dDefault, setDefaultScripts = {}, set()
    if sDefaultMap and os.path.isfile(sDefaultMap):
        for sSection, sKey, sScript, iLine in keyMapLines(sDefaultMap):
            setDefaultScripts.add(sScript.lower())
            if sSection in ("[common keys]", "[desktop keys]", "[laptop keys]") and "&" not in sKey:
                dDefault.setdefault(canonicalKey(sKey), sScript)
    dDefined = {}
    for sName in os.listdir(sFolder):
        if sName.lower().endswith((".jss", ".jsh")):
            sText = open(os.path.join(sFolder, sName), "rb").read().decode("utf-8-sig", "replace")
            for sScript in re.findall(r"^\s*Script\s+(\w+)", sText, re.M | re.I):
                dDefined[sScript.lower()] = sScript
    lsProblems = []
    dMapped = {}
    for sName in sorted(os.listdir(sFolder), key=str.lower):
        if not sName.lower().endswith(".jkm"):
            continue
        for sSection, sKey, sScript, iLine in keyMapLines(os.path.join(sFolder, sName)):
            if sName.lower() == (sApp + ".jkm").lower():
                dMapped[canonicalKey(sKey)] = sScript
            if not re.match(r"^\w+$", sScript):
                lsProblems.append("%s line %d: %s=%s names no script; a key map line is the key, then the script" % (sName, iLine, sKey, sScript))
            elif sScript.lower() in dDefined:
                if dDefined[sScript.lower()] != sScript:
                    lsProblems.append("%s line %d: %s is spelled %s where it is defined" % (sName, iLine, sScript, dDefined[sScript.lower()]))
            elif setDefaultScripts and sScript.lower() not in setDefaultScripts:
                lsProblems.append("%s line %d: %s=%s names a script defined neither in %s's scripts nor among JAWS's own" % (sName, iLine, sKey, sScript, sApp))
    # The app's keys that JAWS gives to a table or mouse script, and the app's key map does not hand on.
    sHotkeys = os.path.join(sRoot, "help", "Hotkeys.md")
    if dDefault and os.path.isfile(sHotkeys):
        sText = open(sHotkeys, "rb").read().decode("utf-8-sig", "replace")
        for sKey, sScript in sorted(dDefault.items()):
            if sScript.lower() not in lsContextScripts or sKey in dMapped:
                continue
            sShown = "+".join(s.capitalize() if len(s) > 1 else s.upper() for s in sKey.split("+"))
            if re.search(r"(?<![\w+])%s(?![\w+])" % re.escape(sShown), sText, re.I):
                lsProblems.append("%s binds %s, but JAWS gives it to %s, which works only in a table or moves the mouse; hand it on in %s.jkm" % (sApp, sShown, sScript, sApp))
    return lsProblems
