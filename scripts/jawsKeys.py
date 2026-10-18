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

It also answers missing(sRoot, sApp, sKitDir) for the shared check. Camel Type.
"""

import os
import re

sBlockStart = "; Homer suite pass-through -- written by the kit's tidy from data\\KeyOwnership.inix; do not edit"
sBlockEnd = "; end of Homer suite pass-through"


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


def ensure(sRoot, sApp, sKitDir):
    """Put the app's key map right. Returns a list of what was done, empty when nothing was needed."""
    sPath = keyMapPath(sRoot, sApp)
    if not sPath:
        return []
    lsKeys = boundKeys(sRoot, allowlist(sKitDir, sApp))
    binData = open(sPath, "rb").read()
    bBom = binData.startswith(b"\xef\xbb\xbf")
    sText = binData.decode("utf-8-sig", "replace")
    sWanted = wantedText(sText, lsKeys)
    if sWanted == sText:
        return []
    open(sPath, "wb").write((b"\xef\xbb\xbf" if bBom else b"") + sWanted.encode("utf-8"))
    lsDone = []
    if re.search(r"^(?:[A-Za-z]+\+)*[\[\]]=", sText, re.M):
        lsDone.append("named its bracket keys")
    if lsKeys:
        lsDone.append("passes " + ", ".join(lsKeys) + " to " + sApp)
    return lsDone or ["updated"]


def missing(sRoot, sApp, sKitDir):
    """The keys the app binds that its key map does not yet hand on, for the shared check."""
    sPath = keyMapPath(sRoot, sApp)
    if not sPath:
        return []
    lsKeys = boundKeys(sRoot, allowlist(sKitDir, sApp))
    sText = open(sPath, "rb").read().decode("utf-8-sig", "replace")
    return [k for k in lsKeys if not re.search(r"^%s=" % re.escape(k), sText, re.M | re.I)]
