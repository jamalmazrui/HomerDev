"""checkQuality -- the homer-quality skill's checker: the HomerDev kit's document checks on any file.

Usage: checkQuality <file or folder> ...

Every Word, Excel, PowerPoint, Markdown, web page, EPUB and PDF file named, or found in a folder named, is checked
through a copy, so no file is changed. Each finding is listed as one the kit would fix by itself when a Homer app makes
the file, or one that needs a person. Exit 0 when nothing needs a person, 1 when something does, 2 when it could not
run. The log, logs\\checkQuality-<time>.log under the folder it runs in, names the environment and every finding.
"""

import datetime
import os
import platform
import shutil
import sys
import tempfile

lsTypes = (".docx", ".epub", ".htm", ".html", ".md", ".pdf", ".pptx", ".xlsx")
lsLog = []


def log(sText):
    lsLog.append(datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + " " + sText)


def say(sText):
    print(sText)
    log("CONSOLE: " + sText)


def kitPython():
    """The kit's exec\\Python: four folders up from this script, in the kit itself."""
    sHere = os.path.dirname(os.path.abspath(__file__))
    sKit = os.path.abspath(os.path.join(sHere, "..", "..", "..", ".."))
    sPython = os.path.join(sKit, "exec", "Python")
    return sPython if os.path.isfile(os.path.join(sPython, "conversion.py")) else ""


def filesIn(lsArgs):
    lsFiles = []
    for sArg in lsArgs:
        if os.path.isdir(sArg):
            for sDir, lsSub, lsNames in os.walk(sArg):
                lsSub[:] = [s for s in lsSub if s.lower() not in ("logs", "notes", ".git")]
                lsFiles += [os.path.join(sDir, s) for s in sorted(lsNames) if s.lower().endswith(lsTypes)]
        elif os.path.isfile(sArg): lsFiles.append(sArg)
        else: say("Not found: " + sArg)
    return lsFiles


def main():
    log("checkQuality start; python %s on %s; cwd %s; command line %s" % (platform.python_version(), platform.platform(), os.getcwd(), " ".join(sys.argv)))
    if len(sys.argv) < 2:
        say(__doc__.strip().split("\n\n")[1])
        return 2
    sPython = kitPython()
    if not sPython:
        say("The HomerDev kit's exec\\Python was not found above this script, so nothing could be checked.")
        return 2
    sys.path.insert(0, sPython)
    import conversion
    lsFiles = filesIn(sys.argv[1:])
    if not lsFiles:
        say("No Word, Excel, PowerPoint, Markdown, web page, EPUB or PDF file was found.")
        return 2
    iPerson, iFiles = 0, 0
    sTemp = tempfile.mkdtemp(prefix="homerQuality-")
    try:
        for sFile in lsFiles:
            sCopy = os.path.join(sTemp, os.path.basename(sFile))
            shutil.copyfile(sFile, sCopy)
            try: lsFindings = conversion.finishOutput(sCopy)
            except Exception as oError:
                say("%s: could not be checked: %s" % (sFile, oError)); continue
            lsFix = [s for s in lsFindings if ": fixed" in s]
            lsHand = [s for s in lsFindings if ": fixed" not in s and not s.startswith("Header names")]
            iFiles += 1
            iPerson += len(lsHand)
            if not lsFix and not lsHand: say("%s: nothing to report." % sFile); continue
            say("%s:" % sFile)
            for s in lsFix: say("  Would fix: " + s.replace(": fixed,", ":"))
            for s in lsHand: say("  Needs a person: " + s)
    finally:
        shutil.rmtree(sTemp, ignore_errors=True)
    say("%d %s checked; %d %s that %s a person." % (iFiles, "file" if iFiles == 1 else "files", iPerson, "finding" if iPerson == 1 else "findings", "needs" if iPerson == 1 else "need"))
    return 1 if iPerson else 0


if __name__ == "__main__":
    try: iCode = main()
    except Exception as oError:
        import traceback
        log(traceback.format_exc()); say("checkQuality failed: %s" % oError); iCode = 2
    try:
        os.makedirs("logs", exist_ok=True)
        sLog = os.path.join("logs", "checkQuality-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".log")
        open(sLog, "w", encoding="utf-8-sig", newline="\r\n").write("\n".join(lsLog) + "\n")
    except OSError: pass
    sys.exit(iCode)
