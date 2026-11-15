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
    lParts = [dRep.get(s, s) for s in sKey.strip().split("+") if s]
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
