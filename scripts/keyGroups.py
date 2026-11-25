r"""keyGroups.py -- count the Homer Suite's keys by pattern group (HomerDev 1.269.0, 21 November 2026).

Usage (through keyGroups.cmd, with no arguments):

    keyGroups

It reads the key files of DbDo, EdSharp, FileDir and HomerView from the folders beside the kit (C:\DbDo and so on,
on any drive), sorts every key binding into the pattern groups named below, and writes the counts and the members of
each group into help\KeyGroups.md, between its two marker lines. The audit of each group, above the markers, is
written by hand; the numbers below them are written by this script, so they never drift from the key files.

A binding may belong to several groups: Copy Log is in the clipboard group and in the F12 group. A binding in no
group is listed at the end, so a new command shows up until a group claims it.

The console says briefly what was done; the log in the kit's logs folder, HomerDev-keyGroups-<stamp>.log, holds the
environment, every file read and every count. Camel Type throughout.
"""

import datetime
import os
import platform
import re
import sys
import traceback

lApps = ["DbDo", "EdSharp", "FileDir", "HomerView"]
sEnd = "<!-- key groups end -->"
sStart = "<!-- key groups start -->"

sKitDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sLogDir = os.path.join(sKitDir, "logs")
sLogPath = os.path.join(sLogDir, "HomerDev-keyGroups-%s.log" % datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))


def logLine(sText):
    os.makedirs(sLogDir, exist_ok=True)
    with open(sLogPath, "a", encoding="utf-8") as fLog:
        fLog.write(datetime.datetime.now().isoformat(timespec="milliseconds") + " " + sText + "\n")
    return True


def lastKey(sKey):
    return sKey.split("+")[-1]


def modifiers(sKey):
    return "+".join(sKey.split("+")[:-1])


def nameHas(sPattern):
    return lambda d, sKey: re.search(sPattern, d["name"]) is not None


def functionKey(iNumber):
    return lambda d, sKey: lastKey(sKey) == "F%d" % iNumber


# THE GROUPS (21 November 2026). Each is a phrase, a kind -- key shape (the keys themselves make the pattern) or topic
# (what the commands are about) -- and a rule over a command and one of its keys.
lGroups = [
    ("again", "key shape", nameHas(r" Again$")),
    ("ai and online help", "topic", nameHas(r"^Chat |Copilot|Instruct Page|Query Web|Lookup Term|Translate|Thesaurus")),
    ("apostrophe, clipboard text", "key shape", lambda d, sKey: lastKey(sKey) == "'" and "Clipboard" in d["name"]),
    ("archives", "topic", nameHas(r"Zip|Unarchive")),
    ("back, forward and levels", "topic", nameHas(r"Child Table|Root Table|Go Back|Go Forward|Parent Folder|Come up Level")),
    ("backslash, open elsewhere", "key shape", lambda d, sKey: lastKey(sKey) == "\\"),
    ("bookmarks and favorites", "topic", nameHas(r"Bookmark|Favorite")),
    ("case, lines and text shape", "topic", lambda d, sKey: re.search(r"Case$|[Qq]uote|Join Lines|Hard Line|[Ww]rap|Trim Blanks|Format Code|PyDent|PyBrace|Justify|Baseline|Selection Font|^Align|Indent|Outdent|New Line|Insert Time|Calculate Date|Section Break|Repeat Line|Replace Tokens|Transform Files|Brace|Tag$", d["name"]) is not None or (d["name"] == "Evaluate Expression" and d["app"] == "EdSharp")),
    ("clipboard", "topic", lambda d, sKey: re.search(r"Clipboard|^Copy|^Cut|^Paste|Append File Contents|^Merge File$", d["name"]) is not None or (d["name"] in ("Extract with Regex", "Evaluate Expression", "Convert Units") and d["app"] in ("DbDo", "FileDir"))),
    ("conversion and export", "topic", nameHas(r"Export|Import|Convert|Text Co|HTML|Markdown to|to Markdown|to Plain|Open Other Format|Open Document|Save Page|Translate|Encoding")),
    ("data records and fields", "topic", lambda d, sKey: d["app"] == "DbDo" and re.search(r"Record|Notes|Tags|Edit url|Null Value|Pick Value|Edit Cell|Merge Data|Show Columns|Design Database|Table Summary|Table Properties|Generate|Query|Inspect", d["name"]) is not None and d["name"] != "Record Playback"),
    ("delete", "topic", nameHas(r"^Delete")),
    ("editing basics", "topic", lambda d, sKey: d["name"] in ("Complete Selection", "Enter New Line", "Go to Start of Selection", "Redo", "Replace", "Reselect", "Select All", "Select Chunk", "Special Character", "Start Selection", "Undo", "Unselect All")),
    ("f1 help", "key shape", lambda d, sKey: lastKey(sKey) == "F1" or d["name"] in ("Alternate Menu", "Hotkey Summary", "Where Am I")),
    ("f2 edit and rename", "key shape", functionKey(2)),
    ("f3 search again", "key shape", functionKey(3)),
    ("f4 windows", "key shape", functionKey(4)),
    ("f5 refresh and run", "key shape", functionKey(5)),
    ("f6 panes, sections and views", "key shape", functionKey(6)),
    ("f7 review and language", "key shape", functionKey(7)),
    ("f8 selection, marking and reading all", "key shape", functionKey(8)),
    ("f9 readable view", "key shape", functionKey(9)),
    ("f10 menus", "key shape", functionKey(10)),
    ("f11 version and window layout", "key shape", functionKey(11)),
    ("f12 ai, logs, media and macros", "key shape", functionKey(12)),
    ("filter and order", "topic", lambda d, sKey: re.search(r"Filter|Order", d["name"]) is not None and d["name"] != "Order Items"),
    ("folders and windows tools", "topic", lambda d, sKey: (d["app"] == "FileDir" and re.search(r"Environment Variables|Recycle Bin|Restart Windows|Control Panel|Volume Format|Network Connections|Context Menu|SendTo Menu|ReadOnly|ReadWrite|Folder$|Shortcut|Quick url", d["name"]) is not None) or d["name"] in ("Context Menu", "Environment Variables", "SendTo Menu")),
    ("go to and open", "topic", lambda d, sKey: re.search(r"^(Go to|Open|Choose|Recent|List Favorites|Drive Letter|Path List$|Insert All Users Path|Insert Script Path)", d["name"]) is not None and "Again" not in d["name"]),
    # CELL VALUE DOWN AND UP (24 November 2026): Alt+DownArrow and Alt+UpArrow, the short forms that say the cell alone.
    ("grid table keys", "key shape", lambda d, sKey: d["app"] == "DbDo" and ((sKey.startswith("Control+Alt+") and lastKey(sKey) in ("DownArrow", "End", "Home", "LeftArrow", "NumPad5", "PageDown", "PageUp", "RightArrow", "UpArrow")) or d["name"].startswith("Cell Value "))),
    ("home and end", "key shape", lambda d, sKey: (lastKey(sKey) in ("End", "Home") and re.search(r"Mark|Root", d["name"]) is None) or d["name"] == "Beginning File"),
    ("item lists in text", "topic", nameHas(r" Items$")),
    ("launch from the desktop", "key shape", nameHas(r"^Launch ")),
    ("local ai", "topic", nameHas(r"^Chat ")),
    ("mail, send and web", "topic", nameHas(r"Mail|SendTo|Send to|Burn|Web Download|Web Client|FTP")),
    ("marking", "topic", lambda d, sKey: re.search(r"\bMark\b|\bMarks\b|\bUnmark\b|Marked|^Toggle Mark", d["name"]) is not None and not d["name"].startswith(("Read ", "Say "))),
    ("media and play", "topic", nameHas(r"^Play|Homer Player|Record Playback")),
    ("new and save", "topic", nameHas(r"^New|^Save( As| Copy|$)|Save Marks|Restore Marks")),
    ("properties and details", "topic", nameHas(r"Properties|Type Extended|Inspect Record|Table Summary|Iterate Processes|Inquire Differences")),
    ("reading aloud", "topic", nameHas(r"^Read (Wide|Lean|All|Headed)|Toggle Reading|^Say Selected")),
    ("regex", "topic", nameHas(r"Regex")),
    ("rename", "topic", nameHas(r"Rename|Reorder Names")),
    ("repeat and next or previous", "topic", nameHas(r"^(Next|Previous) ")),
    ("say, on alt", "key shape", lambda d, sKey: (d["name"].startswith("Say ") or d["name"] == "Topic") and modifiers(sKey) in ("Alt", "Alt+Shift")),
    ("say, on shift", "key shape", lambda d, sKey: (d["name"].startswith("Say ") or d["name"] == "Show Type Extended") and (modifiers(sKey) == "Shift" or d["name"] == "Say Item Name")),
    ("scripts and macros", "topic", nameHas(r"Script|Macro|Dot Prompt|Sqlean|Command Prompt|Environment$|Compile|Run|Prompt Command")),
    ("search", "topic", lambda d, sKey: re.search(r"^(Reverse )?(Jump|Keywords|Find|Forward Find)|File Find|Find Duplicates|Search |Jump to (Line|Main|Probable)|Find Contacts", d["name"]) is not None and "Again" not in d["name"]),
    ("settings and toggles", "topic", lambda d, sKey: re.search(r"Settings|Toggle|Configuration|Guard|Mode|Default Font|Append from Clipboard", d["name"]) is not None and d["name"] != "Toggle Reading"),
    ("space bar", "key shape", lambda d, sKey: lastKey(sKey) == "Space"),
    ("web pages", "topic", lambda d, sKey: d["app"] == "HomerView" and re.search(r"Page|Accessibility|Dialog|Contacts|Link|Elements|Names|Form|Main|Kind|Browser|Address|Metadata|Session Log|Structure", d["name"]) is not None),
    ("windows", "topic", nameHas(r"Window|Arrange Icons|Cascade|^Tile|^Tab ")),
    ("yield (counting)", "topic", nameHas(r"Yield")),
    ("z keys", "key shape", lambda d, sKey: lastKey(sKey) == "Z"),
]


def groupOrder(sName):
    # Lower-case alphabetical, but the function keys in number order, F1 to F12, which a listener expects.
    mFunction = re.match(r"^f(\d+) ", sName)
    return (sName.lower(), 0) if not mFunction else ("f%02d" % int(mFunction.group(1)), 0)


def keyFile(sAppDir, sApp):
    sOwn = os.path.join(sAppDir, "configs", sApp + ".inix")
    if os.path.isfile(sOwn) and re.search(r"(?mi)^\[hotkeys\]", open(sOwn, encoding="utf-8-sig").read()): return sOwn
    return os.path.join(sAppDir, "configs", "Hotkeys.inix")


def readBindings(sRoot):
    sys.path.insert(0, os.path.join(sKitDir, "scripts"))
    import suiteCatalog
    lBindings = []
    for sApp in lApps:
        sPath = keyFile(os.path.join(sRoot, sApp), sApp)
        if not os.path.isfile(sPath):
            logLine("missing key file: " + sPath)
            continue
        sText = open(sPath, encoding="utf-8-sig").read().replace("=no key,", "=,")
        dEntries = suiteCatalog.readKeyFile(sText, sApp)
        logLine("read %s: %d commands" % (sPath, len(dEntries)))
        for sCanon, (sName, lsKeys, sDescription) in dEntries.items():
            for sKey in lsKeys: lBindings.append({"app": sApp, "key": sKey, "name": sName})
    return lBindings


def writeSection(lBindings):
    lsOut = [sStart, "", "## The groups, counted", ""]
    lsOut.append("Written by scripts\\keyGroups from the four key files, %s. Each count is key bindings: a command with two keys counts twice, and a binding may be in more than one group." % datetime.date.today().strftime("%d %B %Y").lstrip("0"))
    lsOut.append("")
    setGrouped = set()
    dMembers = {}
    for sGroup, sKind, fRule in sorted(lGroups, key=lambda t: groupOrder(t[0])):
        lMembers = [d for d in lBindings if fRule(d, d["key"])]
        dMembers[sGroup] = (sKind, lMembers)
        for d in lMembers: setGrouped.add((d["app"], d["name"], d["key"]))
        lsCounts = ["%s %d" % (sApp, sum(1 for d in lMembers if d["app"] == sApp)) for sApp in lApps if any(d["app"] == sApp for d in lMembers)]
        lsOut.append("- **%s** (%s): %d -- %s" % (sGroup, sKind, len(lMembers), ", ".join(lsCounts)))
        logLine("group %s: %d" % (sGroup, len(lMembers)))
    lUngrouped = [d for d in lBindings if (d["app"], d["name"], d["key"]) not in setGrouped]
    lsOut += ["", "In all, %d key binding%s in %d group%s; %d in no group." % (len(lBindings), "" if len(lBindings) == 1 else "s", len(lGroups), "" if len(lGroups) == 1 else "s", len(lUngrouped)), ""]
    lsOut += ["## Appendix: the members of each group", ""]
    for sGroup, sKind, fRule in sorted(lGroups, key=lambda t: groupOrder(t[0])):
        lMembers = dMembers[sGroup][1]
        lsOut += ["### " + sGroup, ""]
        for sApp in lApps:
            lsApp = sorted(set("%s (%s)" % (d["name"], d["key"]) for d in lMembers if d["app"] == sApp), key=str.lower)
            if lsApp: lsOut.append("- **%s:** %s." % (sApp, "; ".join(lsApp)))
        lsOut.append("")
    if lUngrouped:
        lsOut += ["### in no group", ""]
        for d in sorted(lUngrouped, key=lambda d: (d["app"], d["name"].lower())): lsOut.append("- %s: %s (%s)" % (d["app"], d["name"], d["key"]))
        lsOut.append("")
    lsOut.append(sEnd)
    return "\n".join(lsOut), len(lUngrouped)


def main():
    logLine("keyGroups %s, python %s, %s, cwd %s, args %s" % (__file__, sys.version.split()[0], platform.platform(), os.getcwd(), sys.argv[1:]))
    sRoot = os.path.dirname(sKitDir)
    if len(sys.argv) > 1: sRoot = os.path.abspath(sys.argv[1])
    logLine("apps looked for in " + sRoot)
    lBindings = readBindings(sRoot)
    if not lBindings:
        print("keyGroups: no key files found beside the kit, in %s. Log: %s" % (sRoot, sLogPath))
        return 1
    sSection, iUngrouped = writeSection(lBindings)
    sPage = os.path.join(sKitDir, "help", "KeyGroups.md")
    sText = open(sPage, encoding="utf-8-sig").read().replace("\r\n", "\n") if os.path.isfile(sPage) else "# Homer Key Groups\n\n" + sStart + "\n" + sEnd + "\n"
    if sStart not in sText or sEnd not in sText: sText = sText.rstrip("\n") + "\n\n" + sStart + "\n" + sEnd + "\n"
    sText = sText[:sText.index(sStart)] + sSection + sText[sText.index(sEnd) + len(sEnd):]
    with open(sPage, "wb") as fPage: fPage.write(("\ufeff" + sText).replace("\n", "\r\n").encode("utf-8"))
    logLine("wrote %s: %d bindings, %d in no group" % (sPage, len(lBindings), iUngrouped))
    print("keyGroups: help\\KeyGroups.md counted %d key binding%s in %d groups; %d in no group." % (len(lBindings), "" if len(lBindings) == 1 else "s", len(lGroups), iUngrouped))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exceptionError:
        logLine(traceback.format_exc())
        print("keyGroups stopped: %s. Log: %s" % (exceptionError, sLogPath))
        sys.exit(1)
