r"""suiteCatalog: compares an app's key file with the Homer Suite's catalog (HomerDev 1.235.0, 15 November 2026).

The kit's data\SuiteCatalog.inix holds every command the suite shares: its name, its suite key and one sentence,
word for word the same in every app but for the app's own words. check.py's suite commands check calls suiteBreaks
here for the app being checked, and scripts\testSuiteGate.py proves, on every kit build, that it fails what it must.

WHAT IT FINDS, in the words of the audit both Claude and ChatGPT agreed on 15 November (A2):
  - a shared command whose key file lacks the suite's key, among its primary key and its aliases;
  - a shared command whose sentence differs from the suite's;
  - a shared command the catalog says this app has (apps=) that the key file leaves out; before 1.235.0 a key file that
    left a command out was never asked about it;
  - a key file that names no shared command at all, which used to pass as "0 shared commands".

It is a module of functions, not a script: check.py and testSuiteGate.py import it from the kit's scripts folder."""

import re


def readCatalog(sText):
    """(commands, words, key exceptions) from the catalog's text: {name: {field: value}} for each."""
    dCommands, dWords, dKeyExceptions, sSection = {}, {}, {}, ""
    for sLine in sText.splitlines():
        sTrim = sLine.strip().lstrip("﻿")
        if not sTrim or sTrim.startswith(";"): continue
        if sTrim.startswith("["):
            sSection = sTrim[1:-1]
            continue
        if "=" not in sTrim: continue
        sKey, sValue = sTrim.split("=", 1)
        if sSection.startswith("command "): dCommands.setdefault(sSection[8:], {})[sKey.strip()] = sValue.strip()
        elif sSection.startswith("words "): dWords.setdefault(sSection[6:], {})[sKey.strip()] = sValue.strip()
        elif sSection.startswith("keys "): dKeyExceptions.setdefault(sSection[5:], {})[sKey.strip()] = sValue.strip()
    return dCommands, dWords, dKeyExceptions


def normKey(sKey):
    """One spelling for a key: modifiers in the order Control, Alt, Shift, and symbol names as their characters."""
    dRep = {"Ctrl": "Control", "Apostrophe": "'", "OemQuotes": "'", "Semicolon": ";", "Semi-colon": ";", "Backslash": "\\",
            "Slash": "/", "Grave": "`", "Equals": "=", "Return": "Enter", "Comma": ",", "Period": ".", "SemiColon": ";"}
    # MORE SPELLINGS OF ONE KEY (1.239.0): the first /exportkeys runs of EdSharp and FileDir wrote the kit's KeyName
    # spellings -- GraveAccent, RightBracket, Backspace -- where the key files say Accent, ], BackSpace, and the key files
    # name some shifted characters by themselves -- Tilde, Question, LeftParen -- where a program binds Shift with the
    # unshifted key. Both now come to one spelling, so only a real difference is reported.
    dRep.update({"BackSpace": "Backspace", "Back": "Backspace", "RightBracket": "]", "LeftBracket": "[", "OemCloseBrackets": "]",
                 "OemOpenBrackets": "[", "GraveAccent": "`", "Accent": "`", "Oemtilde": "`", "Oemplus": "="})
    dShifted = {"Tilde": "`", "Question": "/", "Exclamation": "1", "At": "2", "RightParen": "0", "LeftParen": "9",
                "RightBrace": "]", "LeftBrace": "[", "Colon": ";", "Less": ",", "Greater": ".", "Underscore": "-"}
    lParts = []
    for sPart in [s for s in sKey.strip().split("+") if s]:
        if sPart in dShifted: lParts += ["Shift", dShifted[sPart]]
        else: lParts.append(dRep.get(sPart, sPart))
    lMods = [s for s in ("Control", "Alt", "Shift") if s in lParts]
    lRest = [re.sub(r"^D(\d)$", r"\1", s) for s in lParts if s not in ("Control", "Alt", "Shift")]
    return "+".join(lMods + lRest)


def readKeyFile(sText, sApp):
    """{canonical name: (name as written, [keys], sentence)} for the key file's [Hotkeys] lines. A key file may name
    the app in a command ("Exit DbDo"); the catalog writes {app} there."""
    dEntries, sSection = {}, ""
    for sLine in sText.splitlines():
        sTrim = sLine.strip().lstrip("﻿")
        if sTrim.startswith("["):
            sSection = sTrim.lower()
            continue
        if "=" not in sTrim or sTrim.startswith(";"): continue
        if sSection and sSection != "[hotkeys]": continue
        sName, sRest = sTrim.split("=", 1)
        lParts = sRest.split(",")
        iAt = 1
        while iAt < len(lParts) and re.match(r"^\s*(or|through)\b", lParts[iAt]): iAt += 1
        lKeys = [normKey(s) for sPart in lParts[:iAt] for s in re.split(r"\s+or\s+|^\s*or\s+|^\s*through\s+", sPart.strip())
                 if s.strip() and s.strip().lower() != "none"]
        dEntries[sName.strip().replace(sApp, "{app}")] = (sName.strip(), lKeys, ",".join(lParts[iAt:]).strip())
    return dEntries


def render(dCommands, dWords, sName, sApp):
    """The suite's sentence for a command, in this app's words."""
    sText = dCommands[sName].get("description", "")
    dAll = dict(dWords.get(sApp, {}))
    dAll["app"] = sApp
    dAll.update(dWords.get(sName + "|" + sApp, {}))
    for sKey, sValue in dAll.items(): sText = sText.replace("{" + sKey + "}", sValue)
    return sText


def appsOf(dCommand):
    """The apps the catalog says have this command (apps=), lowercased; empty when it does not say."""
    return [s.strip().lower() for s in dCommand.get("apps", "").split(",") if s.strip()]


def suiteBreaks(sCatalogText, sKeyFileText, sApp):
    """(breaks, shared count) for one app. Each break is one sentence naming the command and what differs."""
    dCommands, dWords, dKeyExceptions = readCatalog(sCatalogText)
    dEntries = readKeyFile(sKeyFileText, sApp)
    lBreaks, iShared = [], 0
    for sCanon, (sName, lKeys, sDescription) in dEntries.items():
        if sCanon not in dCommands: continue
        iShared += 1
        sSuiteKey = normKey(dCommands[sCanon].get("key", "").replace("{app}", sApp))
        sOwnKey = normKey(dKeyExceptions.get(sApp, {}).get(sCanon, ""))
        if sOwnKey: sSuiteKey = sOwnKey
        if sSuiteKey and sSuiteKey not in lKeys:
            lBreaks.append("%s: the suite's key is %s, but %s binds %s" % (sName, sSuiteKey, sApp, " or ".join(lKeys) or "none"))
        sWanted = render(dCommands, dWords, sCanon, sApp)
        if sDescription.rstrip(".") != sWanted.rstrip("."):   # a closing period is a matter of each app's style
            lBreaks.append("%s: says \"%s\", where the suite says \"%s\"" % (sName, sDescription, sWanted))
    # MEMBERSHIP (1.235.0): a command the catalog gives to this app must be in its key file.
    for sCanon, dCommand in sorted(dCommands.items()):
        if sApp.lower() in appsOf(dCommand) and sCanon not in dEntries:
            lBreaks.append("%s: the suite gives %s this command, but its key file leaves it out" % (sCanon.replace("{app}", sApp), sApp))
    if iShared == 0:
        lBreaks.append("%s's key file names no shared command at all, so nothing could be compared" % sApp)
    return lBreaks, iShared


def readExport(sText):
    """{canonical name: (name, [keys])} from a file a program wrote with /exportkeys (KeyMap.exportInix)."""
    dCommands, dCurrent = {}, None
    for sLine in sText.splitlines():
        sTrim = sLine.strip().lstrip("\ufeff")
        if sTrim.startswith("["):
            dCurrent = {} if sTrim.lower().startswith("[command ") else None
            if dCurrent is not None: dCommands[sTrim] = dCurrent
            continue
        if dCurrent is not None and "=" in sTrim and not sTrim.startswith(";"):
            sKey, sValue = sTrim.split("=", 1)
            dCurrent[sKey.strip()] = sValue.strip()
    dResult = {}
    for d in dCommands.values():
        sName = d.get("name", "")
        lKeys = [normKey(s) for s in re.split(r"\s*,\s*|\s+or\s+", d.get("keys", "")) if s.strip()]
        if sName: dResult[nameKey(sName)] = (sName, lKeys)
    return dResult


def nameKey(sName):
    """A command's name as both files can be matched on: no ampersand, no ellipsis, no case, letters and digits only."""
    return re.sub(r"[^a-z0-9]", "", sName.replace("&", "").lower())


def readHandled(sCatalogText, sApp):
    """{canonical name: reason} for the commands an app handles outside the kit's router, from the catalog's
    [handled <App>] section (1.239.0): keys whose meaning depends on the item under the cursor, a text box's own keys,
    or a screen reader script's. They are not in an /exportkeys file, and are not differences."""
    dHandled, bIn = {}, False
    for sLine in sCatalogText.splitlines():
        sTrim = sLine.strip().lstrip("\ufeff")
        if sTrim.startswith("["):
            bIn = sTrim[1:-1].strip().lower() == ("handled " + sApp).lower()
            continue
        if bIn and "=" in sTrim and not sTrim.startswith(";"):
            sName, sReason = sTrim.split("=", 1)
            dHandled[nameKey(sName)] = sReason.strip()
    return dHandled


def exportBreaks(sExportText, sKeyFileText, sApp, dHandled=None):
    """(differences, commands compared) between the keys a program declared (its /exportkeys file) and the keys its key
    file shows (HomerDev 1.238.0, the keyboard audit's Phase 1 and A2). A key shown but not declared is a false alias:
    the menu or the Key Describer names a key that does nothing. A key declared but not shown is hidden. A program that
    declares nothing is reported, since an empty export proves nothing."""
    dExport = readExport(sExportText)
    if not dExport: return ["%s exported no commands, so nothing could be compared" % sApp], 0
    lBreaks, iCompared = [], 0
    for sCanon, (sName, lShown, sSentence) in readKeyFile(sKeyFileText, sApp).items():
        sKey = nameKey(sName)
        if not lShown or sKey in (dHandled or {}):
            continue
        # A desktop shortcut is Windows' key, not the program's, and a key with the reader's own key in it belongs to
        # the screen reader's script; neither is declared by the program.
        if sName.startswith("Launch ") and all(("Alt" in s and "Control" in s) for s in lShown):
            continue
        lShown = [s for s in lShown if not re.search(r"JAWSKey|JAWS\+|NVDA|Insert\+", s)]
        if not lShown:
            continue
        if sKey not in dExport:
            lBreaks.append("%s: the key file shows %s, but %s declares no command of that name" % (sName, " or ".join(lShown), sApp))
            continue
        iCompared += 1
        lDeclared = dExport[sKey][1]
        lFalse = [s for s in lShown if s not in lDeclared]
        lHidden = [s for s in lDeclared if s not in lShown]
        if lFalse: lBreaks.append("%s: the key file shows %s, which %s does not bind" % (sName, " or ".join(lFalse), sApp))
        if lHidden: lBreaks.append("%s: %s binds %s, which the key file does not show" % (sName, sApp, " or ".join(lHidden)))
    return lBreaks, iCompared

