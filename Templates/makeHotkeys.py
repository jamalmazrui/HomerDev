#!/usr/bin/env python3
r"""makeHotkeys.py -- write Hotkeys.md from the menus in DbDo.cs.

WHY GENERATED. Every key lives in one addItem call. A hand-kept list drifts the
first time a key changes, and this project has changed several in a week. So the
document is built from the source, and buildDbDo builds it each time.

THE FORMAT. One list item per key, and inside it one fact per line, the lines
joined with a backslash hard break -- which CommonMark, GitHub and pandoc all
honour. Three forms were considered:

  - pandoc line blocks ("| " at the start of each line) keep lines exactly, but
    GitHub does not support them and shows the bars, and the repository is where
    most people will read this file;
  - blank-line paragraphs work everywhere, but three paragraphs per key read as
    three unrelated things;
  - a list item per key keeps the three lines together as one thing, lets a
    screen reader move key by key, and renders the same everywhere.

So, lists. Every entry is: the thing the section is sorted on, then what it does,
then the other half of the pair.

THE ASSOCIATIONS. Each key's memory association is written once, in the "By
menu" section, beside its description. The rules behind them are written once at
the top.

Writes help\\Hotkeys.md and makeHotkeys.log beside this script.
"""

import datetime
import os
import re
import sys

sScriptDir = os.path.dirname(os.path.abspath(__file__))
sRoot = os.path.dirname(sScriptDir)
# logs\ at the top of the project, one file per run, named as the program names
# its own logs, so an alphabetical sort is a chronological one.
import datetime as _dt
sLogDir = os.path.join(os.path.dirname(sScriptDir), "logs")
os.makedirs(sLogDir, exist_ok=True)
sLogPath = os.path.join(sLogDir, os.path.basename(os.path.dirname(sScriptDir)) + "-hotkeys-%s.log" % _dt.datetime.now().strftime("%Y%m%d-%H%M%S"))

# Keys whose association comes from Windows, the suite, or long convention,
# rather than from a letter. Said plainly, without apology.
c_dNamed = {
    # Each function key is a family, from Windows and Office habits, extended.
    "F1": "F1 is help: this guide.",
    "Shift+F1": "F1 is help; Shift+F1 is the history of changes.",
    "Alt+F1": "F1 is help; Alt+F1 is About.",
    "Control+F1": "F1 is help; Control+F1 describes whatever key you press next.",
    "Alt+Shift+F1": "F1 is help; Alt+Shift+F1 is the ReadMe, the short start.",
    "Control+Shift+F1": "F1 is help; Control+F1 describes one key, and adding Shift describes them all.",
    "F2": "F2 is editing, as it renames a file in Windows.",
    "Control+F2": "F2 is editing; Control+F2 edits by picking a value.",
    "F3": "F3 is searching and searching again.",
    "Shift+F3": "F3 searches; Shift reverses the direction.",
    "Control+F3": "F3 searches; Control makes the search a pattern.",
    "Control+Shift+F3": "F3 searches; Control makes it a pattern and Shift reverses it.",
    "F4": "F4 picks, says or closes open windows: F4 picks one.",
    "Shift+F4": "F4 is open windows; Shift+F4 says which are open.",
    "Control+F4": "F4 is open windows; Control+F4 closes this one, as in Windows.",
    "Control+Shift+F4": "F4 is open windows; Control+Shift+F4 closes all but this one.",
    "Alt+F4": "Alt+F4 closes the program, as in every Windows program.",
    "F5": "F5 is refreshing.",
    "Control+F6": "F6 moves among parts of the window; Control+F6 moves to the next table.",
    "Control+Shift+F6": "F6 moves among parts; Shift reverses Control+F6.",
    "Alt+F6": "F6 moves among parts; Alt+F6 returns to tables you have visited.",
    "Alt+Shift+F6": "F6 moves among parts; Shift reverses Alt+F6.",
    "F8": "F8 is selection: F8 starts a run of marks.",
    "Shift+F8": "F8 is selection; Shift completes the run F8 started.",
    "Alt+F8": "F8 is selection; Alt turns the run into an unmark.",
    "Alt+Shift+F8": "F8 is selection; Shift completes the run Alt+F8 started.",
    "Alt+F10": "F10 is menus: F10 the menu bar, Shift+F10 the context menu, Alt+F10 the alternate menu.",
    "F11": "F11 is the version: elevate sounds like eleven.",
    "F12": "F12 is files and AI: F12 talks to the model on this computer.",
    "Shift+F12": "F12 is AI; Shift sends the table along with the question.",
    "Control+Tab": "Control+Tab moves among DbDo windows.",
    "Control+Shift+Tab": "Shift reverses Control+Tab.",
    "Control+Space": "Control+Space toggles a selection in any Windows list.",
    "Alt+RightArrow": "Alt+Right Arrow goes forward, and deeper, as in a browser.",
    "Alt+LeftArrow": "Alt+Left Arrow goes back, as in a browser.",
    "Control+Enter": "Control+Enter acts from anywhere in a Homer dialog; here it opens the cell's value.",
    "Delete": "Delete deletes, as everywhere.",
    "Shift+8": "Shift+8 is the asterisk, the SQL sign for everything: sort and filter together.",
    "Alt+Apostrophe": "The apostrophe is a quotation mark, and the clipboard is what you last quoted.",
    "Control+Grave": "Control+Grave opens a console, as it opens the terminal in Visual Studio Code.",
    "Alt+Home": "Home goes to the top; Alt+Home goes to the top table.",
    "Control+G": "G for Go, as Control+G goes to a line in Windows editors.",
    "Shift+Space": "Space marks in a list; Shift and Space asks how many are marked.",
    "Alt+Delete": "Delete echoes JAWS, where Insert+Delete says where the cursor is.",
}

# One line for a group whose keys share their reason, written once above them
# instead of on every item.
c_dMenuNotes = {
    "Query, Say": "Shift and a letter asks. Nothing here changes anything; each answers a question about where you are, in one short line.",
    "Edit, Bulk Marking": "F8 starts a run and Shift completes it; Alt makes the run an unmark instead of a mark.",
}

# Where each menu is, as the menu bar says it. Submenus are named with their
# parent, since that is the path somebody walks to reach them.
c_dMenuNames = {
    "BulkMark": "Edit, Bulk Marking", "Edit": "Edit", "File": "File", "Help": "Help",
    "Misc": "Misc", "Navigate": "Navigate", "Query": "Query", "Say": "Query, Say",
    "Tools": "Misc, Tools", "Window": "Window",
}

def logLine(sText):
    with open(sLogPath, "a", encoding="utf-8") as oLog:
        oLog.write(sText + "\n")
    return True

def readText(sPath):
    return open(sPath, "rb").read().decode("utf-8-sig", errors="replace").replace("\r\n", "\n")

def keyName(sExpr):
    """Keys.Control | Keys.Shift | Keys.C -> Control+Shift+C, modifiers alphabetised."""
    lsParts = [s.strip().replace("Keys.", "") for s in sExpr.split("|")]
    dMap = {"Right": "RightArrow", "Left": "LeftArrow", "Up": "UpArrow", "Down": "DownArrow",
            "Next": "PageDown", "PageDown": "PageDown", "Prior": "PageUp", "Return": "Enter",
            "Back": "Backspace", "OemQuotes": "Apostrophe", "OemPeriod": "Period",
            "Oemcomma": "Comma", "OemMinus": "Dash", "Oemplus": "Equals",
            "OemQuestion": "Slash", "OemSemicolon": "Semicolon", "Oem1": "Semicolon",
            "OemOpenBrackets": "LeftBracket", "OemCloseBrackets": "RightBracket",
            "OemPipe": "Backslash", "OemBackslash": "Backslash", "Oemtilde": "Grave",
            "Multiply": "NumPadStar"}
    lsParts = [("D" + p[1:] if False else p) for p in lsParts]
    lsParts = [(p[1:] if re.match(r"^D\d$", p) else p) for p in lsParts]
    lsMods = sorted(p for p in lsParts if p in ("Alt", "Control", "Shift"))
    lsKeys = [dMap.get(p, p) for p in lsParts if p not in ("Alt", "Control", "Shift")]
    return "+".join(lsMods + lsKeys)

def association(sKey, sCaption, sCommand):
    """One sentence saying why this key, in the plainest terms available."""
    if sKey in c_dNamed:
        return c_dNamed[sKey]
    sLetter = sKey.split("+")[-1]
    if len(sLetter) != 1 or not sLetter.isalpha():
        return ""
    sWords = sCommand or sCaption
    if sLetter == "Z":
        return "Z is for sleep: it wakes this behavior or puts it to sleep."
    oWord = re.search(r"\b(" + sLetter + r"[A-Za-z']*)", sWords, re.I)
    sLead = ""
    if oWord:
        return sLead + "%s for %s." % (sLetter, oWord.group(1))
    if sLetter == "X" and re.search(r"ex", sWords, re.I):
        return sLead + "X for the sound of \"ex\"."
    if "Shift" in sKey and re.search(r"\bUn" + sLetter.lower(), sWords, re.I):
        sBase = re.search(r"\bUn(" + sLetter.lower() + r"[a-z]*)", sWords, re.I).group(1)
        return "Shift reverses %s: %s for %s." % (sBase.capitalize(), sLetter, sBase.capitalize())
    return sLead.strip()

def main():
    logLine("makeHotkeys started %s" % datetime.datetime.now().isoformat(" ", "seconds"))
    logLine("Python: %s" % sys.version.replace("\n", " "))
    sSource = readText(os.path.join(sRoot, "DbDo.cs"))

    dSummary = dict(re.findall(r'^\s*add\("([^"]+)",\s*"([^"]*)"', sSource, re.M))
    lsItems = []
    for sMenu, sCaption, sCommand, sExpr in re.findall(
            r'addItem\(mi([A-Za-z]+),\s*"([^"]*)",\s*"([^"]*)",\s*([^,]+?),', sSource):
        if "Keys.None" in sExpr: continue
        sName = sCaption.replace("&", "").rstrip(".").strip()
        sKey = keyName(sExpr)
        sDesc = dSummary.get(sCommand, "").strip()
        if sDesc and not sDesc.endswith("."): sDesc += "."
        lsItems.append({"menu": c_dMenuNames.get(sMenu, sMenu), "name": sName, "key": sKey, "desc": sDesc,
                        "assoc": association(sKey, sCaption.replace("&", ""), sCommand)})
    # SHIFT REVERSES, said where it applies: a key whose unshifted twin is also
    # bound gets that pairing named, so the two are learned as one.
    dByKey = dict((i["key"], i) for i in lsItems)
    for i in lsItems:
        lsParts = i["key"].split("+")
        if "Shift" not in lsParts or len(lsParts) < 3: continue
        sBase = "+".join(p for p in lsParts if p != "Shift")
        # Only where the command really is the other one run backwards. Two Z
        # toggles on Alt+Z and Alt+Shift+Z are neighbours, not opposites.
        bOpposite = re.search(r"\b(Un\w+|Clear|Previous|Reverse|Back)\b", i["name"])
        if sBase in dByKey and bOpposite and "reverses" not in i["assoc"] and "completes" not in i["assoc"]:
            i["assoc"] = (i["assoc"] + " Shift reverses %s." % dByKey[sBase]["name"]).strip()
    logLine("keys found: %d" % len(lsItems))

    def entry(sFirst, sSecond, sThird):
        lsLines = [s for s in (sFirst, sSecond, sThird) if s]
        return "- " + "\\\n  ".join(lsLines)

    lsOut = ["# DbDo Hotkeys", "",
             "Every key DbDo binds, three ways: by menu, by key, and by command. The menu",
             "section says why each key is the one it is.", "",
             "## How the keys are chosen", "",
             "- **A letter is the first letter of a word in the command.** Shift+C is Say Cell; Alt+O is Order.",
             "- **Shift and a letter asks.** Every Say command is Shift and a letter, and none changes anything.",
             "- **Adding Shift reverses.** Control+M marks and Control+Shift+M unmarks; Control+W sets the Where filter and Control+Shift+W clears it.",
             "- **Z is for sleep.** Every Z key is a toggle: it wakes a behavior or puts it to sleep. Control+Z undoes in Windows, and restoring a behavior is the same idea.",
             "- **X is for the sound of \"ex\"**, as in Export.",
             "- **Alt takes the letter when Control already means something in Windows.** Control+O opens and Control+S saves everywhere, so Order is Alt+O and Select Columns is Alt+S.",
             "- **Each function key is a family,** from Windows and Office habits, extended: F1 help, F2 editing, F3 searching, F4 picking, saying or closing open windows, F5 refreshing, F6 moving among parts of the window, F7 review, F8 selection, F9 a more readable view, F10 menus, F11 the version (elevate sounds like eleven), F12 files and AI.",
             "- **Control+Tab moves among DbDo windows,** as it moves among tabs everywhere else.",
             "", "## By menu", ""]

    for sMenu in sorted(set(i["menu"] for i in lsItems), key=str.lower):
        lsOut += ["### " + sMenu, ""]
        if sMenu in c_dMenuNotes:
            lsOut += [c_dMenuNotes[sMenu], ""]
        for i in sorted((i for i in lsItems if i["menu"] == sMenu), key=lambda i: i["name"].lower()):
            sDesc = " ".join(s for s in (i["desc"], i["assoc"]) if s)
            lsOut.append(entry(i["name"], sDesc, i["key"]))
        lsOut.append("")

    lsOut += ["## By key", ""]
    def family(sKey):
        lsParts = sKey.split("+")
        sLast = lsParts[-1]
        if re.match(r"^F\d+$", sLast): return "Function keys"
        sMods = "+".join(lsParts[:-1])
        return sMods if sMods else "Other keys"
    for sFamily in sorted(set(family(i["key"]) for i in lsItems), key=str.lower):
        lsOut += ["### " + sFamily, ""]
        for i in sorted((i for i in lsItems if family(i["key"]) == sFamily), key=lambda i: i["key"].lower()):
            lsOut.append(entry(i["key"], i["desc"], i["name"]))
        lsOut.append("")

    lsOut += ["## By command", ""]
    for i in sorted(lsItems, key=lambda i: i["name"].lower()):
        lsOut.append(entry(i["name"], i["desc"], i["key"]))
    lsOut.append("")

    sOut = os.path.join(sRoot, "help", "Hotkeys.md")
    with open(sOut, "wb") as oFile:
        oFile.write(("\ufeff" + "\n".join(lsOut)).replace("\n", "\r\n").encode("utf-8"))
    print("Wrote Hotkeys.md: %d keys, by menu, by key and by command." % len(lsItems))
    logLine("wrote %s" % sOut)
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as oError:
        import traceback
        logLine(traceback.format_exc())
        print("Hotkeys.md could not be written. The log has why.")
        sys.exit(1)
