r"""harvestQueue.py version 4 -- gathers the help guides a collection has asked for, as the first part of its build.

    harvestQueue <collection>       what the kit's projectCycle runs before buildGuide, in a guides collection
    harvestQueue                    the collection in the current folder, by hand
    harvestQueue <collection> --trim [Folder ...]
                                    trims the named harvests' archives now, or every harvest's when none is named;
                                    a collection's scripts\trimHarvest.cmd runs this for the current folder

WHY (14 November 2026). Gathering a new guide took four steps by hand: ask makeHarvester for the harvester, run it,
find its archive, upload it. build_release now does the first three, as PodcastDirectories' build adds the shows
listed in data\addShows.inix. A guide to gather is a section of data\addGuides.inix:

    [Word]
    harvester=getWordHelp
    asked=2026-11-14

The section is the guide's name (Word.md); harvester names the block in the kit's makeHarvester.py, by its script
name; asked is the day the gathering was asked for. To gather a guide again, give it a later day.

WHAT A RUN DOES, for each section in order:

1. Skips it when its harvest, data\harvests\<Folder>, holds request.txt saying it finished for that day. <Folder> is
   the harvester's name less "get" (getWordHelp gathers into WordHelp).
2. Resumes it when request.txt names that day but not a finish: an earlier cycle was stopped, and the pages it saved
   stay, since a harvester never fetches a page twice.
3. Otherwise starts it fresh. Pages an older gathering left under that name are moved, whole, to
   data\harvests\<Folder>-before-<day>, and logged, so nothing gathered is lost and nothing stale is kept.
4. Writes the harvesters it needs into the collection's scripts folder with the kit's makeHarvester, which tests each
   one it writes, and runs each. A harvester writes its archive, the file to upload, to results\<Folder>.zip, with its
   log inside.

A harvest that ends with an error, or saves no page, is reported and the next one runs: its archive still carries its
log, which says why, and request.txt records its exit code and page count. It counts as gathered; a later asked= day
gathers it again. Only a missing or failing makeHarvester stops the build, since then no harvester can be trusted. Control+C stops
the run at once; the next build resumes where it stopped.

THE ARCHIVE TO UPLOAD IS TRIMMED (version 2, 14 November 2026). Google's help pages are 99 parts in 100 script and
style: Calendar's 296 pages came to 476 MB, and the Docs editors' to over 500 MB, too large to upload. So once a
harvest finishes, its archive in results is written again from data\harvests with each web page's script, style,
drawings and comments taken out (a script holding JSON data stays): Calendar's became 8 MB, the same guide built from
either. The pages in data\harvests are never changed, so the guide built on this computer reads them whole. Every
finished harvest whose archive is not yet trimmed is trimmed on the next build, so archives gathered before this
version shrink too; request.txt records trimmed= when it is done.

TRIMMING ON DEMAND (version 3, 15 November 2026). The Google Docs editors' archive came to over 500 MB, too large to
upload, because the build that trims had not yet run on it. --trim trims an archive at once, whatever request.txt
says: each named folder of data\harvests (GoogleDocsEditorsHelp, or GoogleDocsEditors, or getGoogleDocsEditorsHelp),
or every folder there when none is named. It writes results\<Folder>.zip and says how large it now is. Nothing is
gathered and the pages in data\harvests are not changed.

MORE THAN ONE QUEUE FILE (version 4, 17 November 2026). A guide asked for in a chat arrived as a whole new
addGuides.inix, which would have replaced the sections already in the collection's copy, the record of every guide
gathered. Now data\addGuides-<anything>.inix files are read too, after addGuides.inix and in name order, so a delivery
adds its own file (addGuides-2026-11-17.inix) and never touches the one you have. When two files name the same guide,
the later asked= day wins, so asking again in a new file gathers again.

THE LOG is logs\<Collection>-harvestQueue-yyyyMMdd-HHmmss.log, UTF-8 with a byte order mark and Windows line endings:
the environment, each section and what was decided for it and why, every command with its exit code and time.
"""

import datetime, io, os, platform, re, shutil, subprocess, sys, time, zipfile

sQueueName = "addGuides.inix"
dState = {"fLog": None}


def log(sText):
    """One stamped line in this run's log."""
    if dState["fLog"] is None: return False
    dState["fLog"].write(datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3] + " " + sText + "\n")
    dState["fLog"].flush()
    return True


def say(sText):
    """One short line for the console, and the same in the log."""
    print(sText, flush=True)
    return log("SAY " + sText)


def readQueue(sPath):
    """The sections of addGuides.inix, in order: a list of (guide, {key: value})."""
    sText = io.open(sPath, "rb").read().decode("utf-8-sig", "replace")
    lSections, dCurrent = [], None
    for sLine in sText.splitlines():
        sTrim = sLine.strip()
        if not sTrim or sTrim.startswith((";", "#")): continue
        oSection = re.match(r"^\[([^\]]+)\]$", sTrim)
        if oSection:
            dCurrent = {}
            lSections.append((oSection.group(1).strip(), dCurrent))
            continue
        if dCurrent is None or "=" not in sTrim: continue
        sKey, sValue = sTrim.split("=", 1)
        dCurrent[sKey.strip().lower()] = sValue.strip()
    return lSections


def readQueues(sData):
    """Every queue file in data: addGuides.inix first, then addGuides-*.inix in name order. One section per guide;
    where a guide is named twice, the later asked= day wins. A list of (guide, {key: value}), and the files read."""
    lsFiles = [os.path.join(sData, sQueueName)] if os.path.isfile(os.path.join(sData, sQueueName)) else []
    if os.path.isdir(sData):
        lsFiles += [os.path.join(sData, s) for s in sorted(os.listdir(sData), key=str.lower)
                    if re.match(r"(?i)^addGuides-.+\.inix$", s)]
    lSections, dIndex = [], {}
    for sPath in lsFiles:
        for sGuide, dValues in readQueue(sPath):
            sKey = sGuide.lower()
            if sKey not in dIndex:
                dIndex[sKey] = len(lSections)
                lSections.append((sGuide, dValues))
            elif dValues.get("asked", "") >= lSections[dIndex[sKey]][1].get("asked", ""):
                lSections[dIndex[sKey]] = (sGuide, dValues)
    return lSections, lsFiles


def readRequest(sHarvest):
    """What request.txt in a harvest folder says: {"asked": day, "finished": time} or {} when there is none."""
    sPath = os.path.join(sHarvest, "request.txt")
    if not os.path.isfile(sPath): return {}
    dRequest = {}
    for sLine in io.open(sPath, "rb").read().decode("utf-8-sig", "replace").splitlines():
        if "=" in sLine:
            sKey, sValue = sLine.split("=", 1)
            dRequest[sKey.strip().lower()] = sValue.strip()
    return dRequest


def writeRequest(sHarvest, dRequest):
    """Writes request.txt, UTF-8 with a byte order mark and Windows line endings."""
    os.makedirs(sHarvest, exist_ok=True)
    sText = "".join("%s=%s\r\n" % (sKey, dRequest[sKey]) for sKey in sorted(dRequest))
    io.open(os.path.join(sHarvest, "request.txt"), "wb").write(b"\xef\xbb\xbf" + sText.encode("utf-8"))
    return True


def pageCount(sHarvest):
    """How many pages a harvest's manifest names: its lines less the heading line; 0 when it has none."""
    sPath = os.path.join(sHarvest, "manifest.txt")
    if not os.path.isfile(sPath): return 0
    lLines = [s for s in io.open(sPath, "rb").read().decode("utf-8-sig", "replace").splitlines() if s.strip()]
    return max(len(lLines) - 1, 0)


def trimPage(binPage):
    """A web page without its script, style, drawings and comments. A script that holds JSON data (JSON-LD, or a
    page's data island) stays, since a reader may read it; nothing a reader reads is in the rest."""
    sText = binPage.decode("utf-8", "replace")
    sText = re.sub(r"(?is)<script(?![^>]*application/(ld\+)?json)[^>]*>.*?</script>", "", sText)
    sText = re.sub(r"(?is)<(style|svg|noscript)[^>]*>.*?</\1>", "", sText)
    sText = re.sub(r"(?s)<!--.*?-->", "", sText)
    return sText.encode("utf-8")


def writeTrimmedArchive(sRoot, sFolder, sHarvester):
    r"""Writes results\<Folder>.zip again from data\harvests\<Folder>, its web pages trimmed and everything else as
    it is, with the harvester's logs from logs. Returns (pages trimmed, bytes before, bytes after)."""
    sHarvest = os.path.join(sRoot, "data", "harvests", sFolder)
    sResults = os.path.join(sRoot, "results")
    os.makedirs(sResults, exist_ok=True)
    sArchive = os.path.join(sResults, sFolder + ".zip")
    sTemporary = sArchive + ".part"
    iPages = iBefore = iAfter = 0
    with zipfile.ZipFile(sTemporary, "w", zipfile.ZIP_DEFLATED) as oZip:
        for sDir, lDirs, lFiles in os.walk(sHarvest):
            lDirs.sort()
            for sName in sorted(lFiles):
                sPath = os.path.join(sDir, sName)
                sInside = os.path.join(sFolder, os.path.relpath(sPath, sHarvest)).replace("\\", "/")
                binData = io.open(sPath, "rb").read()
                iBefore += len(binData)
                if sName.lower().endswith((".html", ".htm")):
                    binData = trimPage(binData)
                    iPages += 1
                iAfter += len(binData)
                oZip.writestr(sInside, binData)
        sLogs = os.path.join(sRoot, "logs")
        if os.path.isdir(sLogs):
            for sName in sorted(os.listdir(sLogs)):
                if ("-%s-" % sHarvester).lower() in sName.lower(): oZip.write(os.path.join(sLogs, sName), sName)
    os.replace(sTemporary, sArchive)
    return iPages, iBefore, iAfter


def trimFinished(sRoot, lSections):
    """Trims the archive of every finished harvest not yet trimmed, gathered this run or before."""
    for sGuide, dKeys in lSections:
        sHarvester = os.path.splitext(dKeys.get("harvester", ""))[0]
        if not sHarvester: continue
        sFolder = sHarvester[3:] if sHarvester.lower().startswith("get") else sHarvester
        sHarvest = os.path.join(sRoot, "data", "harvests", sFolder)
        dRequest = readRequest(sHarvest)
        if not dRequest.get("finished") or dRequest.get("trimmed"): continue
        iPages, iBefore, iAfter = writeTrimmedArchive(sRoot, sFolder, sHarvester)
        dRequest["trimmed"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        writeRequest(sHarvest, dRequest)
        log("%s: archive trimmed: %d pages, %d bytes to %d" % (sGuide, iPages, iBefore, iAfter))
        say("%s: results\\%s.zip trimmed for upload, %.1f MB of pages to %.1f MB." % (sGuide, sFolder, iBefore / 1e6, iAfter / 1e6))
    return True


def moveAside(sHarvest, sAsked):
    """Moves an older gathering's folder out of the way, whole, and returns where it went."""
    sBase = "%s-before-%s" % (sHarvest, sAsked.replace("-", ""))
    sTo, iNext = sBase, 2
    while os.path.exists(sTo):
        sTo = "%s-%d" % (sBase, iNext)
        iNext += 1
    shutil.move(sHarvest, sTo)
    return sTo


def findKit(sRoot):
    """The kit, as every kit script finds it: the HomerDev variable projectCycle sets, else the folder three above
    this script (the kit's .claude\\skills\\app-help-guide\\scripts)."""
    sHere = os.path.dirname(os.path.abspath(__file__))
    sFromHere = os.path.abspath(os.path.join(sHere, "..", "..", "..", ".."))
    for sKit in (os.environ.get("HomerDev", ""), sFromHere):
        if sKit and os.path.isfile(os.path.join(sKit, ".claude", "skills", "app-help-guide", "scripts", "makeHarvester.py")): return sKit
    return ""


def runCommand(lCommand, sRoot):
    """Runs one command in the collection, its output to the console, and logs it with its exit code and time."""
    log("RUN " + " ".join('"%s"' % s if " " in s else s for s in lCommand))
    nStart = time.time()
    try:
        oRun = subprocess.run(lCommand, cwd=sRoot, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        iCode = oRun.returncode
    except OSError as oError:
        log("COULD NOT RUN: %s" % oError)
        iCode = 1
    log("EXIT %d after %d seconds" % (iCode, int(time.time() - nStart)))
    return iCode


def plan(sRoot, lSections):
    """Decides, for each section, whether to skip, resume or start it. Returns the list to gather: (guide,
    harvester, folder, day). Moves an older gathering aside when one is in the way."""
    sHarvests = os.path.join(sRoot, "data", "harvests")
    lToGather = []
    for sGuide, dKeys in lSections:
        sHarvester = os.path.splitext(dKeys.get("harvester", ""))[0]
        sAsked = dKeys.get("asked", "")
        if not sHarvester or not re.match(r"^\d{4}-\d{2}-\d{2}$", sAsked):
            say("%s: skipped, since addGuides.inix needs harvester= and asked=yyyy-mm-dd for it." % sGuide)
            continue
        sFolder = sHarvester[3:] if sHarvester.lower().startswith("get") else sHarvester
        sHarvest = os.path.join(sHarvests, sFolder)
        dRequest = readRequest(sHarvest)
        if dRequest.get("asked") == sAsked and dRequest.get("finished"):
            log("%s: gathered for %s, finished %s; skipped" % (sGuide, sAsked, dRequest["finished"]))
            continue
        if dRequest.get("asked") == sAsked:
            log("%s: an earlier cycle started it for %s and did not finish; resuming over its saved pages" % (sGuide, sAsked))
        elif os.path.isdir(sHarvest) and os.listdir(sHarvest):
            sTo = moveAside(sHarvest, sAsked)
            log("%s: an older gathering (%s) was in %s; moved to %s, so this one starts fresh" % (
                sGuide, dRequest.get("asked", "no request.txt"), sHarvest, sTo))
            say("%s: an older gathering was moved to %s." % (sGuide, os.path.relpath(sTo, sRoot)))
        else:
            log("%s: new; gathering for %s" % (sGuide, sAsked))
        lToGather.append((sGuide, sHarvester, sFolder, sAsked))
    return lToGather


def trimNamed(sRoot, lNames):
    """--trim: writes the trimmed archive of each named harvest, or of every harvest when none is named. A name may be
    the folder (GoogleDocsEditorsHelp), the guide (GoogleDocsEditors) or the harvester (getGoogleDocsEditorsHelp).
    Returns 0 when every named harvest was found and trimmed, 1 otherwise."""
    sHarvests = os.path.join(sRoot, "data", "harvests")
    if not os.path.isdir(sHarvests):
        say("There is no data\\harvests folder in %s, so nothing was trimmed." % sRoot)
        return 1
    lFolders = sorted(s for s in os.listdir(sHarvests) if os.path.isdir(os.path.join(sHarvests, s)) and "-before-" not in s)
    if lNames:
        lChosen, iMissing = [], 0
        for sName in lNames:
            sStem = os.path.splitext(os.path.basename(sName.rstrip("\\/")))[0]
            if sStem.lower().startswith("get"): sStem = sStem[3:]
            lMatch = [s for s in lFolders if s.lower() in (sStem.lower(), sStem.lower() + "help")]
            if lMatch: lChosen.append(lMatch[0])
            else:
                say("%s: no harvest by that name in data\\harvests." % sName)
                iMissing += 1
    else:
        lChosen, iMissing = lFolders, 0
    for iNumber, sFolder in enumerate(lChosen, 1):
        say("%d of %d: trimming %s." % (iNumber, len(lChosen), sFolder))
        iPages, iBefore, iAfter = writeTrimmedArchive(sRoot, sFolder, "get" + sFolder)
        sArchive = os.path.join(sRoot, "results", sFolder + ".zip")
        iZip = os.path.getsize(sArchive)
        sHarvest = os.path.join(sHarvests, sFolder)
        dRequest = readRequest(sHarvest)
        if dRequest:
            dRequest["trimmed"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writeRequest(sHarvest, dRequest)
        log("%s: %d pages, %d bytes to %d; archive %d bytes" % (sFolder, iPages, iBefore, iAfter, iZip))
        say("  results\\%s.zip is %.1f MB (the pages were %.0f MB, now %.0f MB)." % (sFolder, iZip / 1e6, iBefore / 1e6, iAfter / 1e6))
    if not lChosen: say("Nothing to trim.")
    return 1 if iMissing else 0


def main():
    lArgs = sys.argv[1:]
    bTrim = any(s.lower() in ("--trim", "/trim", "-trim") for s in lArgs)
    lArgs = [s for s in lArgs if s.lower() not in ("--trim", "/trim", "-trim")]
    sRoot = os.path.abspath(lArgs[0] if lArgs else os.getcwd())
    lTrimNames = lArgs[1:]
    sCollection = os.path.basename(sRoot.rstrip("\\/")) or "Guides"
    sLogs = os.path.join(sRoot, "logs")
    os.makedirs(sLogs, exist_ok=True)
    sStamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    sLogPath = os.path.join(sLogs, "%s-harvestQueue-%s.log" % (sCollection, sStamp))
    iSame = 2
    while os.path.exists(sLogPath):
        sLogPath = os.path.join(sLogs, "%s-harvestQueue-%s-%d.log" % (sCollection, sStamp, iSame))
        iSame += 1
    dState["fLog"] = io.open(sLogPath, "w", encoding="utf-8-sig", newline="\r\n")
    iResult = 0
    try:
        log("harvestQueue.py version 3; script %s" % os.path.abspath(__file__))
        log("Python %s at %s on %s" % (platform.python_version(), sys.executable, platform.platform()))
        log("working directory %s; command line %s" % (os.getcwd(), " ".join(sys.argv)))
        if bTrim:
            log("settings: collection %s; trim %s" % (sRoot, ", ".join(lTrimNames) or "every harvest"))
            iResult = trimNamed(sRoot, lTrimNames)
            return iResult
        lSections, lsQueues = readQueues(os.path.join(sRoot, "data"))
        log("settings: collection %s; queue files %s" % (sRoot, "; ".join(lsQueues) or "none"))
        if not lsQueues:
            log("no queue file, so nothing to gather")
            return 0
        log("queue: %d section%s: %s" % (len(lSections), "" if len(lSections) == 1 else "s", ", ".join(s for s, d in lSections)))
        lToGather = plan(sRoot, lSections)
        if not lToGather:
            say("Help guides to gather: none; every guide in data\\%s is gathered." % sQueueName)
            trimFinished(sRoot, lSections)
            return 0
        say("Help guides to gather: %d -- %s." % (len(lToGather), ", ".join(t[0] for t in lToGather)))
        sKit = findKit(sRoot)
        if not sKit:
            say("The kit's makeHarvester.py was not found, so nothing was gathered.")
            iResult = 1
            return iResult
        sScripts = os.path.join(sRoot, "scripts")
        os.makedirs(sScripts, exist_ok=True)
        sMaker = os.path.join(sKit, ".claude", "skills", "app-help-guide", "scripts", "makeHarvester.py")
        log("kit %s; makeHarvester %s" % (sKit, sMaker))
        iMade = runCommand([sys.executable, sMaker, sScripts] + [t[1] for t in lToGather], sRoot)
        if iMade != 0:
            say("makeHarvester failed its own test, so nothing was gathered; its lines above say which harvester.")
            iResult = 1
            return iResult
        lResults = []
        for iNumber, (sGuide, sHarvester, sFolder, sAsked) in enumerate(lToGather, 1):
            sScript = os.path.join(sScripts, sHarvester + ".py")
            if not os.path.isfile(sScript):
                say("%d of %d, %s: makeHarvester has no block named %s, so it was not gathered." % (iNumber, len(lToGather), sGuide, sHarvester))
                lResults.append((sGuide, "no harvester"))
                continue
            sHarvest = os.path.join(sRoot, "data", "harvests", sFolder)
            dRequest = readRequest(sHarvest)
            dRequest["asked"] = sAsked
            dRequest["started"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            dRequest.pop("finished", None)
            dRequest.pop("trimmed", None)
            writeRequest(sHarvest, dRequest)
            say("%d of %d: gathering %s help." % (iNumber, len(lToGather), sGuide))
            iCode = runCommand([sys.executable, sScript], sRoot)
            dRequest["finished"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            dRequest["exit"] = str(iCode)
            iPages = pageCount(sHarvest)
            dRequest["pages"] = str(iPages)
            writeRequest(sHarvest, dRequest)
            sNote = "" if iCode == 0 else "; it ended with an error its log names"
            if iPages == 0: sNote += "; no page was saved, and its log says why"
            lResults.append((sGuide, "results\\%s.zip, %d page%s%s" % (sFolder, iPages, "" if iPages == 1 else "s", sNote)))
        say("Gathered %d of %d. Upload from results:" % (len([t for t in lResults if t[1].startswith("results")]), len(lToGather)))
        for sGuide, sWhere in lResults: say("  %s: %s" % (sGuide, sWhere))
        trimFinished(sRoot, lSections)
        return 0
    except KeyboardInterrupt:
        log("STOPPED from the keyboard; the next build resumes")
        say("Stopped. The next build resumes where this one stopped.")
        iResult = 130
        return iResult
    except Exception:
        import traceback
        log("CRASH " + traceback.format_exc())
        say("harvestQueue stopped with an error; its log has the details: " + sLogPath)
        iResult = 2
        return iResult
    finally:
        log("RUN ENDED exit %d" % iResult)
        dState["fLog"].close()


if __name__ == "__main__":
    sys.exit(main())
