# fixKit140.py -- put back what kit 1.40.0 lost, so the shared classes compile.
#
# Two names went missing between HomerDev 1.39.1 and 1.40.0, and every app that
# compiles against the kit fails inside the kit's own files:
#
#   Lbc.cs(1167): 'handleListBoxCopyKeys' does not exist  -- the method that
#       answers Control+C and Alt+C in every Lbc list box was deleted; its
#       wiring survived. This script puts the method back, word for word from
#       1.39.1, if it is absent.
#   Util.cs(77): 'readSample' does not exist -- something calls a name that
#       was never defined. If a definition with the same shape exists under a
#       renamed name (readTemplate, say), the call is pointed at it; otherwise
#       the lines around the call are shown so the fix can be made by eye.
#
# Idempotent: run it twice and the second run changes nothing. Logs to
# C:\HomerDev\logs\HomerDev-fixkit-<stamp>.log.
import datetime, os, re, sys

sKit = os.environ.get("HomerDev", r"C:\HomerDev")
if not os.path.isfile(os.path.join(sKit, "CSharp", "Lbc.cs")):
    print("The kit was not found at " + sKit + ". Set HomerDev or unzip it into C:\\HomerDev.")
    sys.exit(1)
os.makedirs(os.path.join(sKit, "logs"), exist_ok=True)
sLog = os.path.join(sKit, "logs", "HomerDev-fixkit-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".log")
oLog = open(sLog, "w", encoding="utf-8")
def logLine(s):
    oLog.write(s + "\n"); oLog.flush()
def say(s):
    print(s); logLine("CONSOLE: " + s)
logLine("fixKit140 started " + datetime.datetime.now().isoformat())
logLine("Script: " + os.path.abspath(__file__))
logLine("Python: " + sys.version.replace("\n", " "))
logLine("Kit: " + sKit)

def readText(p): return open(p, "rb").read().decode("utf-8-sig").replace("\r\n", "\n")
def writeText(p, t): open(p, "wb").write(("\ufeff" + t).replace("\n", "\r\n").encode("utf-8"))

sMethod = '    // handleListBoxCopyKeys: Control+C copies the current list\n    // item\'s text to the clipboard; Alt+C appends it (clipboard,\n    // CRLF, item), mirroring the text-control family so every\n    // Lbc control answers the same chords.\n    private void handleListBoxCopyKeys(object sender, KeyEventArgs evArgs)\n    {\n        ListBox lb = sender as ListBox;\n        if (lb == null) return;\n        if (evArgs.KeyData != (Keys.Control | Keys.C)\n            && evArgs.KeyData != (Keys.Alt | Keys.C)) return;\n        string sItem = (lb.SelectedItem != null) ? lb.SelectedItem.ToString() : "";\n        if (sItem.Length == 0) { Say.say("No item"); }\n        else if (evArgs.KeyData == (Keys.Control | Keys.C))\n        { LbcTextBox.setClipboard(sItem); Say.say("Copied item"); }\n        else\n        { LbcTextBox.setClipboard(LbcTextBox.clipboardJoin(sItem)); Say.say("Appended to clipboard"); }\n        evArgs.Handled = true;\n        evArgs.SuppressKeyPress = true;\n    }\n\n'

# ---- Lbc.cs ----
pLbc = os.path.join(sKit, "CSharp", "Lbc.cs"); tLbc = readText(pLbc)
if "private void handleListBoxCopyKeys(" in tLbc:
    say("Lbc.cs already defines handleListBoxCopyKeys; nothing to do there.")
else:
    sAnchor = "    private void handleListBoxFindKeys"
    if sAnchor in tLbc:
        tLbc = tLbc.replace(sAnchor, sMethod + sAnchor, 1)
        writeText(pLbc, tLbc)
        say("Lbc.cs: put handleListBoxCopyKeys back, before handleListBoxFindKeys.")
    else:
        say("Lbc.cs: handleListBoxFindKeys is not there either, so the method was not inserted. The log shows the lines that mention it.")
        for iLine, sLine in enumerate(tLbc.split("\n"), 1):
            if "handleListBoxCopyKeys" in sLine: logLine("LINE %d: %s" % (iLine, sLine))

# ---- Util.cs ----
pUtil = os.path.join(sKit, "CSharp", "Util.cs"); tUtil = readText(pUtil)
if re.search(r"\b(static\s+)?[\w<>\[\]]+\s+readSample\s*\(", tUtil):
    say("Util.cs already defines readSample; nothing to do there.")
elif "readSample" not in tUtil:
    say("Util.cs does not mention readSample at all; nothing to do there.")
else:
    lsDefs = sorted(set(re.findall(r"\b(?:public|private|internal)\s+static\s+[\w<>\[\]]+\s+(read\w+)\s*\(", tUtil)))
    logLine("read* methods defined: " + ", ".join(lsDefs))
    sTarget = ""
    for sName in ("readTemplate", "readTemplateText", "readText", "readFile"):
        if sName in lsDefs: sTarget = sName; break
    if sTarget:
        tUtil = re.sub(r"\breadSample\b", sTarget, tUtil)
        writeText(pUtil, tUtil)
        say("Util.cs: readSample is not defined; the call now names " + sTarget + ", which is.")
    else:
        say("Util.cs calls readSample, and nothing by that name or a likely rename is defined. The log shows the lines around each call.")
        lsLines = tUtil.split("\n")
        for iLine, sLine in enumerate(lsLines, 1):
            if "readSample" in sLine:
                for k in range(max(0, iLine - 6), min(len(lsLines), iLine + 4)):
                    logLine("LINE %d: %s" % (k + 1, lsLines[k]))
say("The log is " + sLog)
logLine("finished " + datetime.datetime.now().isoformat())
