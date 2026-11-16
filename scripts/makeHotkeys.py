r"""makeHotkeys: write an app's help\Hotkeys.md from its key file (HomerDev 1.241.0, 15 November 2026).

    python makeHotkeys.py <project folder>        the app is the folder's name

WHY. The keyboard audit Claude and ChatGPT agreed on (A1) asks for one command record, with every surface generated
from it, so a page can never say what the program does not do. FileDir's Hotkeys.md has long been generated from
configs\Hotkeys.inix by its own makeKeyMap.py, and DbDo's from its menus. EdSharp's said it was generated but was
written by hand, and it drifted: it still listed Control+PageDown for sections and an old Set on Favorite List on
Control+L after both had changed. This writes the page from the key file -- configs\<App>.inix's [Hotkeys], else
configs\Hotkeys.inix -- in FileDir's three orderings: by command name, by key, and by first modifier. Lists, not
tables, since a list reads better aloud.

A detailed log goes to the project's logs\<App>-hotkeys-<time>.log: the command line, the key file, every entry read
and every line skipped, and the file written."""

import datetime, os, platform, re, sys, traceback

lModifierGroups = ["Alt+Shift", "Alt+Control", "Control+Shift", "Alt", "Control", "Shift", "Function keys", "Other keys"]


def logLine(sLog, sText):
    with open(sLog, "a", encoding="utf-8") as oFile: oFile.write(datetime.datetime.now().isoformat(timespec="milliseconds") + "  " + sText + "\n")
    return True


def keyFileOf(sRoot, sApp):
    """configs\\<App>.inix when it has a [Hotkeys] section, else configs\\Hotkeys.inix."""
    sPath = os.path.join(sRoot, "configs", sApp + ".inix")
    if os.path.isfile(sPath) and re.search(r"(?mi)^\[hotkeys\]", open(sPath, encoding="utf-8-sig", errors="replace").read()):
        return sPath
    return os.path.join(sRoot, "configs", "Hotkeys.inix")


def readEntries(sPath, sLog):
    """[(command, key, description)] from the [Hotkeys] lines: Command=Key, Description, split on the first comma,
    as the apps themselves read it. A key of None is no key."""
    lEntries, sSection = [], ""
    for iLine, sLine in enumerate(open(sPath, encoding="utf-8-sig", errors="replace"), 1):
        sTrim = sLine.strip()
        if not sTrim or sTrim.startswith(";"): continue
        if sTrim.startswith("["):
            sSection = sTrim.lower()
            continue
        if sSection and sSection != "[hotkeys]": continue
        if "=" not in sTrim:
            logLine(sLog, "line %d skipped, no '=': %s" % (iLine, sTrim))
            continue
        sCommand, sValue = sTrim.split("=", 1)
        iComma = sValue.find(",")
        sKey = sValue[:iComma].strip() if iComma >= 0 else ""
        sDescription = sValue[iComma + 1:].strip() if iComma >= 0 else sValue.strip()
        if sKey.lower() == "none": sKey = ""
        lEntries.append((sCommand.strip(), sKey, sDescription.rstrip(".")))
    return lEntries


def inGroup(sGroup, sKey):
    if sGroup == "Alt+Shift": return sKey.startswith("Alt+Shift")
    if sGroup == "Alt+Control": return sKey.startswith("Alt+Control") or sKey.startswith("Control+Alt")
    if sGroup == "Control+Shift": return sKey.startswith("Control+Shift")
    if sGroup == "Alt": return sKey.startswith("Alt+") and not sKey.startswith("Alt+Shift") and not sKey.startswith("Alt+Control")
    if sGroup == "Control": return sKey.startswith("Control+") and not sKey.startswith("Control+Shift") and not sKey.startswith("Control+Alt")
    if sGroup == "Shift": return sKey.startswith("Shift+")
    if sGroup == "Function keys": return re.match(r"^F\d", sKey) is not None
    return re.match(r"^(Alt|Control|Shift|F\d)", sKey) is None


def writePage(sApp, sVersion, lEntries, sPath):
    sToday = datetime.datetime.now().strftime("%d %B %Y").lstrip("0")
    lOut = ["# %s Hotkeys" % sApp, ""]
    if sVersion: lOut += ["**Version %s**  " % sVersion, ""]
    lOut += ["Generated from the key file on %s. Do not edit this page; edit the key file in configs and build again." % sToday, "",
             "Every %s command, given three ways so you can find a command however you think of it. Press Control+F1 to turn on "
             "the Key Describer, which says a command's name, key and description instead of running it, and Alt+F10 for the "
             "Alternate Menu, which lists every command and finds one by a former name too." % sApp, "",
             "## Contents", "", "- [By Command Name](#by-command-name)", "- [By Key](#by-key)", "- [By First Modifier](#by-first-modifier)", "",
             "## By Command Name", "", "Commands in alphabetical order.", ""]
    for sCommand, sKey, sDescription in sorted(lEntries, key=lambda t: t[0].lower()):
        lOut.append("- **%s**, %s -- %s" % (sCommand, sKey or "no key", sDescription))
    lKeyed = [t for t in lEntries if t[1]]
    lOut += ["", "## By Key", "", "The same commands, in alphabetical order of the key that runs them.", ""]
    for sCommand, sKey, sDescription in sorted(lKeyed, key=lambda t: t[1].lower()):
        lOut.append("- **%s** -- %s: %s" % (sKey, sCommand, sDescription))
    lOut += ["", "## By First Modifier", "", "Grouped by the modifier key a command starts with.", ""]
    for sGroup in lModifierGroups:
        lIn = [t for t in sorted(lKeyed, key=lambda t: t[0].lower()) if inGroup(sGroup, t[1])]
        if not lIn: continue
        lOut += ["### " + sGroup, ""] + ["- **%s** -- %s" % (t[1], t[0]) for t in lIn] + [""]
    with open(sPath, "w", encoding="utf-8-sig", newline="\r\n") as oFile: oFile.write("\n".join(lOut).rstrip("\n") + "\n")
    return len(lEntries)


def main():
    sRoot = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.getcwd())
    sApp = os.path.basename(os.path.normpath(sRoot))
    sLogDir = os.path.join(sRoot, "logs")
    os.makedirs(sLogDir, exist_ok=True)
    sLog = os.path.join(sLogDir, "%s-hotkeys-%s.log" % (sApp, datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))
    try:
        logLine(sLog, "makeHotkeys %s, python %s, %s, cwd %s, args %s" % (sys.argv[0], sys.version.split()[0], platform.platform(), os.getcwd(), sys.argv[1:]))
        sKeyFile = keyFileOf(sRoot, sApp)
        if not os.path.isfile(sKeyFile):
            logLine(sLog, "no key file: " + sKeyFile)
            print("makeHotkeys: %s has no key file in configs. Log: %s" % (sApp, sLog))
            return 1
        lEntries = readEntries(sKeyFile, sLog)
        logLine(sLog, "key file %s: %d commands" % (sKeyFile, len(lEntries)))
        sVersion = ""
        sVersionFile = os.path.join(sRoot, "version.txt")
        if os.path.isfile(sVersionFile): sVersion = open(sVersionFile, encoding="utf-8-sig").read().strip().splitlines()[0].strip() if open(sVersionFile, encoding="utf-8-sig").read().strip() else ""
        sPage = os.path.join(sRoot, "help", "Hotkeys.md")
        iCount = writePage(sApp, sVersion, lEntries, sPage)
        logLine(sLog, "wrote %s, %d commands, version %s" % (sPage, iCount, sVersion or "unknown"))
        print("makeHotkeys: help\\Hotkeys.md written from %s, %d commands." % (os.path.basename(sKeyFile), iCount))
        return 0
    except Exception as oError:
        logLine(sLog, traceback.format_exc())
        print("makeHotkeys stopped: %s. Log: %s" % (oError, sLog))
        return 1


if __name__ == "__main__":
    sys.exit(main())
