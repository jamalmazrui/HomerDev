"""
summarizeLogs.py -- one report from a folder (or zip) of Homer logs.

Usage:
    python summarizeLogs.py <folder-or-zip> [--all]

Reads every <App>-<task>-yyyyMMdd-HHmmss.log (an upload may add numeric
suffixes, which are ignored) and prints, per app, the newest run of each task:
the build result and version, the check counts and failures, the release
outcome with its version and whether GitHub confirmed it as latest, tidy's
changes, push's outcome, and the first ERROR lines of anything else. Files
that are not Homer logs are counted and skipped. --all reports every run,
not only the newest of each task.

Exit code 0 when nothing failed, 1 when a run failed, 2 when the input could
not be read.
"""

import io, os, re, sys, tempfile, zipfile

c_iMaxErrors = 3  # enough to show where a failure began without flooding
c_reName = re.compile(r"^(?P<app>[A-Za-z0-9]+)-(?:(?P<task>[a-z][a-z-]*?)-)?(?P<stamp>\d{8}-\d{6})(?:-\d+)*\.(?:log|md)$")


def readText(sPath):
    """A log's text, whatever its encoding."""
    binData = open(sPath, "rb").read()
    for sEncoding in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            return binData.decode(sEncoding)
        except UnicodeDecodeError:
            continue
    return binData.decode("utf-8", "replace")


def firstMatch(sText, sPattern):
    oMatch = re.search(sPattern, sText, re.M)
    return oMatch.group(1).strip() if oMatch else ""


def errorLines(sText):
    lsErrors = [s.strip() for s in sText.splitlines()
                if re.search(r"\bERROR\b|\bFAILED\b|Traceback", s)]
    return lsErrors[:c_iMaxErrors]


def summarizeBuild(sText):
    sResult = firstMatch(sText, r"build end result=(\w+)")
    # The kit's own build (buildHomerDev) ends with its audit's verdict.
    if not sResult and re.search(r"\b0 problems found", sText): sResult = "succeeded"
    elif not sResult and re.search(r"\b[1-9]\d* problems? found", sText): sResult = "failed"
    if not sResult:
        if re.search(r"Build succeeded", sText): sResult = "succeeded"
        elif re.search(r"Build FAILED|BUILD FAILED", sText): sResult = "failed"
        else: sResult = "unfinished"
    sVersion = (firstMatch(sText, r"Homer Development Kit ([\d.]+)") or
                firstMatch(sText, r"Built \S+ version ([\d.]+)") or
                firstMatch(sText, r"version\.txt is now ([\d.]+)"))
    lsOut = ["result=" + sResult]
    if sVersion: lsOut.append("version=" + sVersion)
    # A warning is worth seeing even in a build that succeeded: the kit's
    # build names the apps whose build script is stale this way.
    lsWarn = [re.sub(r"^\S+ WARN\s+", "", s.strip()) for s in sText.splitlines()
              if re.match(r"^\S+ WARN ", s) and "CONSOLE:" not in s]
    lsOut += ["WARN " + s[:120] for s in lsWarn[:c_iMaxErrors]]
    return lsOut, sResult != "succeeded"


def summarizeCheck(sText):
    sCounts = firstMatch(sText, r"(\d+ checks? passed, \d+ checks? failed[^\r\n]*)")
    lsFailed = re.findall(r"^\S+ \S+\s+(\w+)\s+FAIL\s+(.*)$", sText, re.M)
    lsOut = [sCounts or "no totals"]
    lsOut += ["FAIL %s: %s" % (sName, sWhy.strip()[:120]) for sName, sWhy in lsFailed]
    return lsOut, bool(lsFailed) or not sCounts


def summarizeRelease(sText):
    sPublished = firstMatch(sText, r"=== (.+?) published")
    sLatest = firstMatch(sText, r"GitHub's latest release: (v\S+)")
    lsOut = []
    if sPublished: lsOut.append("published " + sPublished)
    if sLatest: lsOut.append("latest=" + sLatest)
    if re.search(r"ALREADY RELEASED", sText): lsOut.append("already released")
    sCounts = firstMatch(sText, r"(\d+ checks? passed, \d+ checks? failed[^\r\n]*)")
    if sCounts: lsOut.append("check: " + sCounts)
    lsOut += ["failed: " + s.strip()[:120] for s in re.findall(r"failed: (.*)", sText)]
    bFailed = not sPublished or "=== FAILED" in sText
    if bFailed and not re.findall(r"failed: ", sText): lsOut += errorLines(sText)
    return lsOut or ["no outcome"], bFailed


def summarizeTidy(sText):
    sChanges = firstMatch(sText, r"(\d+ changes? made)")
    iStrays = len(re.findall(r"TRACKED STRAY", sText))
    iMoved = len(re.findall(r"\bMOVED\b", sText))
    iDeleted = len(re.findall(r"DELETED EMPTY", sText))
    lsOut = [sChanges or "whitelist only"]
    if iStrays: lsOut.append("untracked=%d" % iStrays)
    if iMoved: lsOut.append("moved=%d" % iMoved)
    if iDeleted: lsOut.append("emptyDeleted=%d" % iDeleted)
    return lsOut, False


def summarizePush(sText):
    sSummary = firstMatch(sText, r"(\d+ files? changed[^\r\n]*)")
    if re.search(r"nothing to commit", sText): sSummary = sSummary or "nothing to commit"
    lsErrors = errorLines(sText)
    return [sSummary or "pushed"] + lsErrors, bool(lsErrors)


def summarizeSession(sText):
    sVersion = firstMatch(sText, r"session start app=\S+ version=(\S+)") or firstMatch(sText, r"Version\s*=\s*(\S+)")
    sExit = firstMatch(sText, r"[Ee]xit code (\-?\d+)")
    lsOut = []
    if sVersion: lsOut.append("version=" + sVersion)
    if sExit: lsOut.append("exit=" + sExit)
    lsErrors = errorLines(sText)
    return (lsOut or ["ran"]) + lsErrors, bool(lsErrors) or (sExit not in ("", "0"))


def summarizeOther(sText):
    lsErrors = errorLines(sText)
    return lsErrors or ["no errors"], bool(lsErrors)


c_dSummarizers = {"build": summarizeBuild, "check": summarizeCheck, "release": summarizeRelease,
                  "tidy": summarizeTidy, "push": summarizePush, "": summarizeSession}


def collect(sFolder):
    """(dRuns, iSkipped): dRuns maps (app, task) to [(stamp, path)] newest first."""
    dRuns = {}
    iSkipped = 0
    for sDir, lsDirs, lsFiles in os.walk(sFolder):
        for sName in lsFiles:
            oMatch = c_reName.match(sName)
            if not oMatch or not sName.endswith(".log"):
                iSkipped += 1
                continue
            sKey = (oMatch.group("app"), oMatch.group("task") or "")
            dRuns.setdefault(sKey, []).append((oMatch.group("stamp"), os.path.join(sDir, sName)))
    for lRuns in dRuns.values(): lRuns.sort(reverse=True)
    return dRuns, iSkipped


def main():
    lsArgs = [s for s in sys.argv[1:] if not s.startswith("--")]
    bAll = "--all" in sys.argv[1:]
    if not lsArgs:
        print(__doc__.strip())
        return 2
    sInput = lsArgs[0]
    if zipfile.is_zipfile(sInput):
        sFolder = tempfile.mkdtemp(prefix="homerLogs")
        with zipfile.ZipFile(sInput) as oZip: oZip.extractall(sFolder)
    elif os.path.isdir(sInput):
        sFolder = sInput
    else:
        print("Not a folder or zip: " + sInput)
        return 2

    dRuns, iSkipped = collect(sFolder)
    bAnyFailed = False
    for sApp in sorted(set(s[0] for s in dRuns), key=str.lower):
        print("== " + sApp)
        for sTask in sorted(set(s[1] for s in dRuns if s[0] == sApp)):
            lRuns = dRuns[(sApp, sTask)]
            for sStamp, sPath in (lRuns if bAll else lRuns[:1]):
                fnSummarize = c_dSummarizers.get(sTask, summarizeOther)
                try:
                    lsFacts, bFailed = fnSummarize(readText(sPath))
                except Exception as oError:
                    lsFacts, bFailed = ["could not read: %s" % oError], True
                bAnyFailed = bAnyFailed or bFailed
                sMark = "FAILED " if bFailed else ""
                print("  %s%s %s: %s" % (sMark, sTask or "session", sStamp, "; ".join(lsFacts)))
    print("%d file%s skipped: not a Homer log name." % (iSkipped, "" if iSkipped == 1 else "s"))
    return 1 if bAnyFailed else 0


if __name__ == "__main__":
    sys.exit(main())
