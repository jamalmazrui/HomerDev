"""
summarizeLogs.py -- one report from a folder (or zip) of Homer logs.

Usage:
    python summarizeLogs.py <folder-or-zip> [--all] [--review]

Reads every <App>-<task>-yyyyMMdd-HHmmss.log (an upload may add numeric
suffixes, which are ignored) and prints, per app, the newest run of each task:
the build result and version, the check counts and failures, the release
outcome with its version and whether GitHub confirmed it as latest, tidy's
changes, push's outcome, and the first ERROR lines of anything else. Files
that are not Homer logs are counted and skipped. --all reports every run,
not only the newest of each task.

--review then reads EVERY text file, evidence reports and setup logs included, and lists what a quick reading
misses: every caution in any wording (skipped, unknown, possible, could not, flagged, partial, a rate limit, a
compiler warning, each distinct page message), every skipped check, and every claim another file contradicts -- a
report that says the samples were built clean beside a log that says they were reused, or a success stated in the
same log as a fact it could not confirm. Run it on logs someone sends before writing any conclusion about them.

Exit code 0 when nothing failed, 1 when a run failed, 2 when the input could
not be read.
"""

import io, os, re, sys, tempfile, zipfile

iMaxErrors = 3  # enough to show where a failure began without flooding
reName = re.compile(r"^(?P<app>[A-Za-z0-9]+)-(?:(?P<task>[a-z][A-Za-z-]*?)-)?(?P<stamp>\d{8}-\d{6})(?:-\d+)*\.(?:log|md)$")


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
    return lsErrors[:iMaxErrors]


def summarizeBuild(sText):
    sResult = firstMatch(sText, r"build end result=(\w+)")
    # The kit's own build (build) ends with its audit's verdict.
    if not sResult and re.search(r"\b0 problems found", sText): sResult = "succeeded"
    elif not sResult and re.search(r"\b[1-9]\d* problems? found", sText): sResult = "failed"
    if not sResult:
        if re.search(r"Build succeeded", sText): sResult = "succeeded"
        elif re.search(r"Build FAILED|BUILD FAILED", sText): sResult = "failed"
        else: sResult = "unfinished"
    sVersion = (firstMatch(sText, r"Homer Development Kit ([\d.]+)") or
                firstMatch(sText, r"Built \S+ version ([\d.]+)") or
                firstMatch(sText, r"Version:? [\d.]+ (?:->|to) ([\d.]+)") or
                firstMatch(sText, r"Version: ([\d.]+) \(from version\.txt") or
                firstMatch(sText, r"version\.txt is now ([\d.]+)"))
    lsOut = ["result=" + sResult]
    if sVersion: lsOut.append("version=" + sVersion)
    # A warning is worth seeing even in a build that succeeded: the kit's
    # build names the apps whose build script is stale this way.
    lsWarn = [re.sub(r"^\S+ WARN\s+", "", s.strip()) for s in sText.splitlines()
              if re.match(r"^\S+ WARN ", s) and "CONSOLE:" not in s]
    lsOut += ["WARN " + s[:120] for s in lsWarn[:iMaxErrors]]
    # UNFINISHED IS NOT FAILED (8 October 2026): a build still speaking its walks,
    # queued behind another project's, has written no end line yet; three such
    # builds were reported FAILED while they waited their turn.
    return lsOut, sResult == "failed"


def summarizeCheck(sText):
    sCounts = firstMatch(sText, r"(\d+ checks? passed, \d+ checks? failed[^\r\n]*)")
    lsFailed = re.findall(r"^\S+ \S+\s+(\w+)\s+FAIL\s+(.*)$", sText, re.M)
    # THE KIT'S OWN CHECK IS NOT A FAILURE (1.50.1). Run in C:\\HomerDev, check
    # recognizes the kit and points to checkHomerDev, with no totals; that was
    # reported as "FAILED: no totals". It is reported as what it is.
    if not sCounts and re.search(r"This is the kit, which checkHomerDev checks", sText):
        return ["the kit: check hands over to checkHomerDev"], False
    # READ AS WHAT THEY ARE (13 October 2026): a check that reused an earlier pass ends "check end, reused" with no
    # totals of its own, and the kit's check now says "This is the kit; running checkHomerDev" and reports its exit
    # code; both were listed as UNFINISHED on every release.
    if not sCounts and re.search(r"check end, reused", sText):
        return ["reused the pass at " + (firstMatch(sText, r"passed this check at (\S+)") or "an earlier run")], False
    oKit = re.search(r"checkHomerDev exit code (\d+)", sText)
    if not sCounts and oKit and re.search(r"This is the kit", sText):
        return ["the kit: checkHomerDev exit code " + oKit.group(1)], oKit.group(1) != "0"
    # UNFINISHED IS NOT FAILED (9 October 2026): the check started by a release is still running when the release
    # gathers the logs, so its own log has no totals yet; every project's release reported "FAILED check: no
    # totals". A check log with no totals, no failed finding and no traceback is unfinished. A crash keeps its
    # traceback and stays a failure, as HomerScribe's did that day.
    if not sCounts and not lsFailed and not re.search(r"Traceback|TRACEBACK", sText):
        return ["result=unfinished"], False
    # A check still running that has already failed a finding says so plainly; "no totals" read as if it had broken.
    lsOut = [sCounts or ("no totals" if re.search(r"Traceback|TRACEBACK", sText) else "still running")]
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
    # UNFINISHED IS NOT FAILED (9 October 2026): a release is still running while it gathers the logs, so its own
    # log has no outcome yet. Without a published line, a FAILED marker, a "failed:" line or a traceback, it is
    # unfinished rather than failed.
    if not sPublished and "=== FAILED" not in sText and not re.search(r"failed: |Traceback|TRACEBACK", sText):
        return ["result=unfinished"], False
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


def summarizeBuildBooks(sText):
    """BOOK TASKS ARE HOMER LOGS TOO (1.64.6): buildBooks and kdpUpdate, named in
    Camel Type, were skipped as not Homer log names. buildBooks ends by saying how
    many books are ready to submit."""
    oReady = re.search(r"(\d+) books? of (\d+) ready to submit", sText)
    if not oReady: return ["no ready count"] + errorLines(sText), True
    return [oReady.group(0)], oReady.group(1) != oReady.group(2)


def summarizeKdpUpdate(sText):
    """kdpUpdate ends with each book's outcome; the counts, and any book not
    submitted by name, are the summary."""
    lsOutcomes = re.findall(r"CONSOLE:   (.+?): ([^\r\n]*?)\r?$", sText, re.M)
    if not lsOutcomes: return ["no outcomes"] + errorLines(sText), True
    iSubmitted = sum(1 for sBook, sWhat in lsOutcomes if sWhat.startswith("submitted") and "locks" not in sWhat)
    lsOther = [sBook.strip() + " (" + sWhat.split(";")[0].strip() + ")" for sBook, sWhat in lsOutcomes
               if not (sWhat.startswith("submitted") and "locks" not in sWhat)]
    lsFacts = ["%d of %d submitted" % (iSubmitted, len(lsOutcomes))]
    if lsOther: lsFacts.append("not submitted: " + ", ".join(lsOther)[:200])
    # "no spelling errors" is good news, and a book KDP locks for review is waiting, not failing.
    bFailed = any(re.search(r"(?i)\bfailed\b|could not|not submitted|stopped", sWhat) for sBook, sWhat in lsOutcomes)
    return lsFacts, bFailed


dSummarizers = {"build": summarizeBuild, "buildBooks": summarizeBuildBooks, "kdpUpdate": summarizeKdpUpdate, "check": summarizeCheck, "release": summarizeRelease,
                  "tidy": summarizeTidy, "push": summarizePush, "": summarizeSession}


def collect(sFolder):
    """(dRuns, iSkipped): dRuns maps (app, task) to [(stamp, path)] newest first."""
    dRuns = {}
    iSkipped = 0
    for sDir, lsDirs, lsFiles in os.walk(sFolder):
        for sName in lsFiles:
            oMatch = reName.match(sName)
            if not oMatch or not sName.endswith(".log"):
                iSkipped += 1
                continue
            sKey = (oMatch.group("app"), oMatch.group("task") or "")
            dRuns.setdefault(sKey, []).append((oMatch.group("stamp"), os.path.join(sDir, sName)))
    for lRuns in dRuns.values(): lRuns.sort(reverse=True)
    return dRuns, iSkipped


# REVIEW: WHAT A KEYWORD SEARCH MISSES (13 October 2026). Reading a day of logs for "warn" and "error", Claude missed
# what another AI found in the same files: sixteen possible spelling errors KDP reported, two checks DbDo's audit
# skipped on every run, a report claiming a clean build of samples its own log said were reused, and a known warning
# set aside unexamined. Each was there, in words no chosen keyword matched. These lists are made mechanically, so
# that what is noticed does not depend on which words someone thought to search for.
reCaution = re.compile(r"\b(skip|skipped|not checked|not run|unknown|could not|cannot|can't|unable|possible|flagged|unverified|"
                       r"unconfirmed|incomplete|partial|refused|rejected|denied|429|408|timed out|timeout|deprecated|obsolete|"
                       r"not shown|not found|missing|retry|retrying|falling back|fallback|left in|doubt|loop|stale|mismatch)\b"
                       r"|warning [A-Z]{2,}\d+|KDP RECOMMENDS|KDP SPELLING|\bMESSAGE: ", re.I)
reNoise = re.compile(r"no errors|0 checks? failed|0 failures|^\s*(a|button|input|select|h5|span|div) \||not a Homer log|"
                     r"no-skip|--skip|Learn more|BROWSER (lifecycle|frame|document request|navigated|PAGE)", re.I)


def plainLine(sLine):
    """A line without its leading timestamp and level, for comparing one occurrence with another."""
    sLine = re.sub(r"^\ufeff?\S*\d{4}-\d\d-\d\d[T ]\S+\s+(?:(?:INFO|WARN|WARNING|ERROR|DEBUG|CMD)\s+)?", "", sLine.strip())
    return re.sub(r"^\w{3} \d\d/\d\d/\d{4} \S+\s+", "", sLine)


def review(sFolder):
    """Prints the cautions, skips and contradictions in every text file under sFolder. Returns the number of lines listed."""
    dTexts = {}
    for sDir, lsDirs, lsFiles in os.walk(sFolder):
        for sName in lsFiles:
            if os.path.splitext(sName)[1].lower() in (".log", ".md", ".txt"):
                try: dTexts[os.path.relpath(os.path.join(sDir, sName), sFolder)] = readText(os.path.join(sDir, sName))
                except Exception: pass
    iListed = 0
    print()
    print("== REVIEW: claims another line contradicts")
    lsChecks = [f for f in dTexts if "checkHomerDev-" in f and f.endswith(".log")]
    for sFile in sorted(f for f in dTexts if "evidence" in f):
        if "built from a clean start" in dTexts[sFile]:
            sStamp = re.search(r"(\d{8}-\d{6})", sFile).group(1) if re.search(r"(\d{8}-\d{6})", sFile) else ""
            lsBefore = sorted(f for f in lsChecks if re.search(r"(\d{8}-\d{6})", f) and re.search(r"(\d{8}-\d{6})", f).group(1) <= sStamp)
            if lsBefore and "skipped, unchanged since" in dTexts[lsBefore[-1]]:
                print("  %s says the samples were built from a clean start; %s says they were skipped, unchanged" % (sFile, lsBefore[-1]))
                iListed += 1
    for sFile in sorted(dTexts):
        sText = dTexts[sFile]
        oSuccess = re.search(r"(outcome[: ]+submitted|\bsubmitted\b.*exit code 0|One source done|every step passed)", sText, re.I)
        oDoubt = re.search(r"(status not shown|could not be read|outcome unknown|unconfirmed|PARTIAL|no words for)", sText, re.I)
        if oSuccess and oDoubt:
            print("  %s states \"%s\" and also \"%s\"" % (sFile, oSuccess.group(1), oDoubt.group(1)))
            iListed += 1
    # A VERSION CLAIM WITH NO VERSION, AND ONE APP'S VERSIONS DISAGREEING (13 October 2026, from an audit). Setup
    # logged mpv and Whisper "found, current" with no version read; a results file said DbDo 1.0.270 beside a setup log
    # of 1.0.272; a dialog's log began "version=0.0.0.0". Each was in the review's caution list, unanswered.
    for sFile in sorted(dTexts):
        for sLine in dTexts[sFile].splitlines():
            if re.search(r"Component [^:]+:\s{2,}found, current", sLine):
                print("  %s claims a component current with no version read: %s" % (sFile, plainLine(sLine)[:120])); iListed += 1
            if re.search(r"\bversion[= ]0\.0\.0\.0\b", sLine):
                print("  %s reports version 0.0.0.0, an unstamped build: %s" % (sFile, plainLine(sLine)[:120])); iListed += 1
    dVersions = {}
    for sFile in sorted(dTexts):
        sApp = os.path.basename(sFile).split("-")[0].split("_")[0]
        for oMatch in re.finditer(r"\b%s (\d+\.\d+\.\d+)\b" % re.escape(sApp), dTexts[sFile]):
            dVersions.setdefault(sApp, {}).setdefault(oMatch.group(1), set()).add(sFile)
    for sApp, dSeen in sorted(dVersions.items()):
        lsResults = [f for v in dSeen for f in dSeen[v] if "setup_results" in f]
        if lsResults and len(dSeen) > 1:
            print("  %s names %s versions in this batch (%s); a results file may be from an earlier run" % (sApp, len(dSeen), ", ".join(sorted(dSeen)))); iListed += 1
    print()
    print("== REVIEW: skipped checks")
    for sFile in sorted(dTexts):
        for sLine in dTexts[sFile].splitlines():
            if re.search(r"\bSKIP\b|\bskip\b --| -- not run|not checked:|\(in the run reused here\)", sLine) and not reNoise.search(sLine):
                print("  %s: %s" % (sFile, plainLine(sLine)[:200]))
                iListed += 1
    print()
    print("== REVIEW: cautions, in any wording (each distinct line once, with how often it appears)")
    dSeen = {}
    for sFile in sorted(dTexts):
        for sLine in dTexts[sFile].splitlines():
            if not reCaution.search(sLine) or reNoise.search(sLine): continue
            sPlain = plainLine(sLine)[:220]
            sKey = re.sub(r"\d+", "#", sPlain.lower())
            if sKey in dSeen: dSeen[sKey][2] += 1
            else: dSeen[sKey] = [sFile, sPlain, 1]
    for sFile, sPlain, iCount in sorted(dSeen.values()):
        print("  %s: %s%s" % (sFile, sPlain, "  (x%d)" % iCount if iCount > 1 else ""))
        iListed += 1
    print()
    print("REVIEW: %d line%s to account for before any conclusion." % (iListed, "" if iListed == 1 else "s"))
    return iListed


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
                fnSummarize = dSummarizers.get(sTask, summarizeOther)
                try:
                    lsFacts, bFailed = fnSummarize(readText(sPath))
                except Exception as oError:
                    lsFacts, bFailed = ["could not read: %s" % oError], True
                bAnyFailed = bAnyFailed or bFailed
                sMark = "FAILED " if bFailed else ""
                if not bFailed and "result=unfinished" in lsFacts:
                    # What it was doing when the log was gathered: the last line of
                    # the newest tutorials log, where a build waits for the voices.
                    sMark = "UNFINISHED "
                    lTutorials = dRuns.get((sApp, "tutorials"), [])
                    if lTutorials:
                        lsLast = [x.strip() for x in readText(lTutorials[0][1]).splitlines() if x.strip()]
                        if lsLast: lsFacts = lsFacts + ["tutorials, last: " + re.sub(r"^\S+ \S+\s+", "", lsLast[-1])[:120]]
                print("  %s%s %s: %s" % (sMark, sTask or "session", sStamp, "; ".join(lsFacts)))
    print("%d file%s skipped: not a Homer log name." % (iSkipped, "" if iSkipped == 1 else "s"))
    if "--review" in sys.argv[1:]: review(sFolder)
    return 1 if bAnyFailed else 0


if __name__ == "__main__":
    sys.exit(main())
