"""makeHarvester.py version 1

Writes a harvester: a standalone Python crawler for ONE product's help estate.

HOW TO USE IT. Add a block to the configuration list near the bottom of this
file — product name, script name, folder name, seed addresses, fence pattern,
optional subject gate — then run it. It writes get<Product>Help.py into the
folder you name (the current one by default), and that script is what you hand
to the person who will run it.

WHY A GENERATOR RATHER THAN ONE PARAMETERISED CRAWLER. Every harvester is a
single self-contained file needing nothing beyond the standard library, so it
can be sent to somebody, read, and run with no setup. The generator keeps the
crawling machinery in one place while each estate keeps its own fence, seeds
and ceiling.

WHAT EVERY GENERATED HARVESTER DOES: refuses addresses outside its fence,
refuses translated editions, sends a Referer naming the site's front page,
waits between requests, stops at a page ceiling, writes a debugging log beside
itself, saves each page with a manifest, and zips the folder at the end.

THE FENCE FAULTS THAT HAVE COST RUNS are in references/fence-faults.md. Read
that before writing a new fence.
"""

import io, os, sys

c_sChassis = r'''"""
{sScriptName}

Gathers the {sProduct} help estate ({sSystem}).
Run it from any folder; it writes everything BESIDE THIS SCRIPT:

    {sFolder}          a folder holding the saved pages
    {sFolder}/manifest.txt   every address and the file it became
    {sLogName}     a detailed log
    {sZipName}     the archive to upload

Nothing is fetched twice: a page already saved is skipped, so the script
can be stopped and run again.
"""

import hashlib, html, http.client, io, json, logging, os, platform, re, socket, sys, time, urllib.error, urllib.parse, urllib.request, zipfile

c_dHeaders = {{"Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
             "Accept-Language": "en-US,en;q=0.9",
             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}}
c_iMaxPages = {iMaxPages}
c_iMaxRepeatLines = 25
c_iRetries = 3
c_lLanguageCodes = ["af", "am", "ar", "az", "be", "bg", "bn", "bs", "ca", "cs", "cy", "da", "de", "el", "es", "et",
                    "eu", "fa", "fi", "fr", "ga", "gl", "gu", "ha", "he", "hi", "hr", "hu", "hy", "id", "is", "it",
                    "ja", "ka", "kk", "km", "kn", "ko", "lo", "lt", "lv", "mk", "ml", "mn", "mr", "ms", "mt", "my",
                    "nb", "ne", "nl", "nn", "no", "pa", "pl", "pt", "ro", "ru", "si", "sk", "sl", "sq", "sr", "sv",
                    "sw", "ta", "te", "th", "tl", "tr", "uk", "ur", "uz", "vi", "zh", "zu"]
c_nDelay = {nDelay}
c_nTimeout = 30
c_sFolderName = "{sFolder}"
c_sLogName = "{sLogName}"
c_sProduct = "{sProduct}"
c_sSubjectPattern = r"{sSubjectPattern}"
c_sZipName = "{sZipName}"

g_dRepeatCounts = {{}}
g_dSeenFingerprints = {{}}


def logCapped(sKind, sMessage):
    """Logs a repeating kind of line up to a cap, then only tallies it."""
    iCount = g_dRepeatCounts.get(sKind, 0) + 1
    g_dRepeatCounts[sKind] = iCount
    if iCount <= c_iMaxRepeatLines: logging.info(sMessage)
    elif iCount == c_iMaxRepeatLines + 1: logging.info("further '%s' lines are tallied rather than written", sKind)
    return True


def hasControlCharacters(sUrl):
    """True when an address carries characters no address may contain. calibre's
    manual quotes a Kindle position marker that looks like a link, and the fetcher
    raised on it three times before giving up; now it is refused once, quietly."""
    return any(ord(sCharacter) < 32 or ord(sCharacter) == 127 for sCharacter in sUrl)


def fetchAddress(sUrl):
    if hasControlCharacters(sUrl):
        logCapped("unfetchable address", "refused: it carries control characters")
        return 0, b"", "", sUrl
    """Fetches one address, returning status, body bytes, content type and the final address."""
    for iAttempt in range(1, c_iRetries + 1):
        try:
            # Send a Referer naming the site's own front page. A browser always
            # sends one when following a link, and some defended sites answer 404
            # to a request that carries none — Rolling Stone's FAQ answered a
            # probe and then refused the harvester minutes later.
            dHeaders = dict(c_dHeaders)
            oParts = urllib.parse.urlsplit(sUrl)
            dHeaders["Referer"] = oParts.scheme + "://" + oParts.netloc + "/"
            oRequest = urllib.request.Request(sUrl, headers=dHeaders)
            with urllib.request.urlopen(oRequest, timeout=c_nTimeout) as oResponse:
                binBody = oResponse.read()
                return oResponse.status, binBody, oResponse.headers.get_content_type(), oResponse.geturl()
        except urllib.error.HTTPError as oError:
            binBody = b""
            try: binBody = oError.read()
            except Exception: pass
            logging.warning("attempt %d for %s answered %d", iAttempt, sUrl, oError.code)
            if oError.code in (403, 404, 410): return oError.code, binBody, "", sUrl
        except (urllib.error.URLError, http.client.HTTPException, socket.timeout, ConnectionError) as oError:
            logging.warning("attempt %d for %s failed: %s", iAttempt, sUrl, oError)
        time.sleep(c_nDelay * iAttempt)
    return 0, b"", "", sUrl


def isEnglish(sUrl):
    """Refuses a translated edition, by path segment and by query field."""
    oParts = urllib.parse.urlsplit(sUrl)
    lSegments = [s for s in oParts.path.split("/") if s]
    # A translated edition may name its language with an underscore rather than a
    # hyphen — calibre publishes /zh_CN/, /pt_BR/, /et/ — so the segment is
    # normalised and only its BASE code is compared. Reading only the exact
    # segment let 128 translated pages into the calibre harvest.
    if lSegments:
        sFirst = lSegments[0].lower().replace("_", "-").split("-")[0]
        if sFirst in c_lLanguageCodes and sFirst != "en": return False
    dQuery = urllib.parse.parse_qs(oParts.query)
    for sField in ("lang", "language", "locale", "setln", "hl"):
        for sValue in dQuery.get(sField, []):
            if sValue.lower().split("-")[0] not in ("en", ""): return False
    return True


def cleanAddress(sUrl):
    """Drops tracking fields, keeps paging fields, and undoes HTML entities FIRST."""
    sUrl = html.unescape(sUrl).strip()
    oParts = urllib.parse.urlsplit(sUrl)
    lKeep = []
    for sField, sValue in urllib.parse.parse_qsl(oParts.query):
        if sField.lower() in ("page", "per_page", "start_page"): lKeep.append((sField, sValue))
        elif sField.lower() in ("cds_mag_code", "cds_page_id", "cds_to_id"): lKeep.append((sField, sValue))
        elif sField.lower() in ("nodeid",): lKeep.append((sField, sValue))
        elif sField.lower() in ("co", "answer", "topic", "sjid"): lKeep.append((sField, sValue)) if sField.lower() == "co" else None
    return urllib.parse.urlunsplit((oParts.scheme, oParts.netloc, oParts.path, urllib.parse.urlencode(lKeep), ""))


def makeFileName(sUrl):
    """Builds a file name that cannot collide, remembering that a name cannot tell a slash from a hyphen."""
    oParts = urllib.parse.urlsplit(sUrl)
    sName = (oParts.netloc + oParts.path).replace("/", "_").replace(":", "_")
    if oParts.query: sName = sName + "_" + oParts.query.replace("&", "_").replace("=", "-")
    sName = re.sub(r"[^A-Za-z0-9_.-]", "_", sName).strip("_")
    if not sName.lower().endswith((".html", ".json")): sName = sName + (".json" if "/api/" in oParts.path else ".html")
    return sName[:180]


def isReady(binBody, sContentType):
    """Tests for what the page MUST CONTAIN. Never a length test, and never an 'or' with one."""
    if "json" in sContentType: return True
    sText = binBody.decode("utf-8", "replace")
    return bool(re.search(r"{sReadyPattern}", sText, re.I))


def savePage(sFolder, sUrl, binBody, lManifest):
    """Writes one page byte for byte, refusing a twin already saved under another address."""
    sFingerprint = hashlib.sha1(binBody).hexdigest()
    if sFingerprint in g_dSeenFingerprints:
        logCapped("twin", "twin of " + g_dSeenFingerprints[sFingerprint] + " refused: " + sUrl)
        return False
    sName = makeFileName(sUrl)
    sPath = os.path.join(sFolder, sName)
    fHandle = io.open(sPath, "wb")
    fHandle.write(binBody)
    fHandle.close()
    g_dSeenFingerprints[sFingerprint] = sUrl
    lManifest.append(sUrl + "\\t" + sName + "\\t" + str(len(binBody)))
    return True


def belongs(sUrl):
    """The positive fence: an address is followed only if it is inside the help estate."""
    if not isEnglish(sUrl): return False
    if re.search(r"\\.(css|js|png|jpe?g|gif|svg|ico|woff2?|ttf|eot|pdf|zip)(\\?|$)", sUrl, re.I): return False
    return bool(re.search(r"{sFencePattern}", sUrl, re.I))


def gatherEstate(sFolder, lManifest):
    """Walks the estate and returns how many pages were saved."""
    lQueue = [{sSeeds}]
    lSeen = set()
    iSaved = 0
    # A run that refuses its own seeds must say so loudly rather than finish
    # quietly with nothing. That fault shipped once and cost a whole round.
    for sSeed in lQueue:
        if not belongs(sSeed):
            logging.error("SEED REFUSED BY ITS OWN FENCE: %s — the fence pattern is wrong, nothing will be gathered", sSeed)
            print("STOPPING: the seed " + sSeed + " fails this script's own fence. See " + c_sLogName)
            return 0
    while lQueue:
        if iSaved >= c_iMaxPages:
            logging.warning("SAFETY VALVE: stopped at %d pages with %d addresses still queued", iSaved, len(lQueue))
            break
        sUrl = cleanAddress(lQueue.pop(0))
        if sUrl in lSeen: continue
        lSeen.add(sUrl)
        if not belongs(sUrl):
            logCapped("outside", "outside the estate: " + sUrl)
            continue
        sName = makeFileName(sUrl)
        if os.path.isfile(os.path.join(sFolder, sName)):
            logCapped("already", "already saved, skipping: " + sUrl)
            binBody = io.open(os.path.join(sFolder, sName), "rb").read()
            if subjectAllows(binBody): lQueue.extend(queueable(findLinks(sUrl, binBody), lSeen, lQueue))
            continue
        iStatus, binBody, sContentType, sFinal = fetchAddress(sUrl)
        time.sleep(c_nDelay)
        if iStatus not in ({sOkStatuses}):
            logging.warning("%s answered %d and was not saved", sUrl, iStatus)
            continue
        if not isReady(binBody, sContentType):
            sText = binBody.decode("utf-8", "replace")
            oTitle = re.search(r"(?is)<title[^>]*>(.*?)</title>", sText)
            sPageTitle = re.sub(r"\s+", " ", html.unescape(re.sub(r"(?s)<[^>]+>", "", oTitle.group(1)))).strip() if oTitle else "no title"
            iWords = len(re.sub(r"(?s)<[^>]+>", " ", sText).split())
            logging.warning("%s answered %d but does not carry the expected content; kept out. It calls itself '%s' and holds %d words",
                            sUrl, iStatus, sPageTitle[:80], iWords)
            continue
        try:
            if savePage(sFolder, sUrl, binBody, lManifest): iSaved += 1
            if subjectAllows(binBody): lQueue.extend(queueable(findLinks(sUrl, binBody), lSeen, lQueue))
        except Exception as oError:
            logging.exception("one page raised an error and the crawl continues: %s (%s)", sUrl, oError)
        if iSaved % 25 == 0 and iSaved: logging.info("progress: %d saved, %d queued", iSaved, len(lQueue))
    return iSaved


def subjectAllows(binBody):
    """True when this page may have its links followed.

    On an estate that publishes everything a company sells under one help tree,
    an address says nothing about its subject, so the gate reads THE PAGE'S OWN
    HEADING instead. This is the rule that stopped an earlier Kindle crawl from
    drowning in Echo devices and business accounts."""
    if not c_sSubjectPattern: return True
    sText = binBody.decode("utf-8", "replace")
    lHeadings = re.findall(r"(?is)<h1[^>]*>(.*?)</h1>", sText) + re.findall(r"(?is)<title[^>]*>(.*?)</title>", sText)
    sHeading = " ".join(re.sub(r"(?s)<[^>]+>", " ", s) for s in lHeadings)
    if re.search(c_sSubjectPattern, html.unescape(sHeading), re.I): return True
    logCapped("off subject", "kept, but its links were not followed: " + sHeading.strip()[:70])
    return False


def queueable(lFound, lSeen, lQueue):
    """Keeps only addresses inside the estate that are not already seen or queued,
    so the queue depth the safety valve reports is a real number of pages to fetch
    rather than a count of every link on every page."""
    lQueued = set(lQueue)
    lOut = []
    for sUrl in lFound:
        sClean = cleanAddress(sUrl)
        if sClean in lSeen or sClean in lQueued: continue
        if not belongs(sClean): continue
        lQueued.add(sClean)
        lOut.append(sClean)
    return lOut


def findLinks(sUrl, binBody):
    """Scans EVERY href on the page, not the last per anchor, and resolves it against this address."""
    lFound = []
    sText = binBody.decode("utf-8", "replace")
{sExtraLinks}
    for oMatch in re.finditer(r'href\\s*=\\s*["\\\']([^"\\\']+)["\\\']', sText, re.I):
        sHref = html.unescape(oMatch.group(1)).strip()
        if sHref.startswith(("mailto:", "javascript:", "#", "tel:")): continue
        lFound.append(urllib.parse.urljoin(sUrl, sHref))
    # A FRAMESET NAMES ITS PAGES WITH src, NOT href. An older help system built
    # in frames therefore looks empty to a crawler that reads only href, which is
    # exactly how EndNote's manual measured as 241 words with one link.
    for oMatch in re.finditer(r'<(?:frame|iframe)[^>]*\\ssrc\\s*=\\s*["\\\']([^"\\\']+)["\\\']', sText, re.I):
        sHref = html.unescape(oMatch.group(1)).strip()
        if sHref.startswith(("mailto:", "javascript:", "#", "tel:", "data:", "about:")): continue
        lFound.append(urllib.parse.urljoin(sUrl, sHref))
    return lFound


def writeArchive(sFolder, sZipPath):
    """Packs the folder at level 6, walking subfolders so nothing is silently dropped."""
    oZip = zipfile.ZipFile(sZipPath, "w", zipfile.ZIP_DEFLATED, compresslevel=6)
    iFiles = 0
    for sRoot, lDirs, lFiles in os.walk(sFolder):
        for sFile in lFiles:
            sPath = os.path.join(sRoot, sFile)
            oZip.write(sPath, os.path.relpath(sPath, os.path.dirname(sFolder)))
            iFiles += 1
    oZip.close()
    return iFiles


def main():
    """Gathers the estate, writes the manifest and the archive, and says what to upload."""
    sScriptDir = os.path.dirname(os.path.abspath(__file__))
    sFolder = os.path.join(sScriptDir, c_sFolderName)
    if not os.path.isdir(sFolder): os.makedirs(sFolder)
    logging.basicConfig(filename=os.path.join(sScriptDir, c_sLogName), filemode="w", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s", encoding="utf-8", errors="backslashreplace")
    sys.excepthook = lambda oType, oValue, oTrace: logging.error(
        "UNCAUGHT %s: %s", oType.__name__, oValue, exc_info=(oType, oValue, oTrace))
    logging.info("{sScriptName} version 1 for %s", c_sProduct)
    logging.info("script %s", os.path.abspath(__file__))
    logging.info("Python %s on %s", platform.python_version(), platform.platform())
    logging.info("working directory %s; command line %s", os.getcwd(), " ".join(sys.argv))
    logging.info("settings: maxPages %d, delay %.1f, timeout %d, retries %d, folder %s",
                 c_iMaxPages, c_nDelay, c_nTimeout, c_iRetries, sFolder)
    lManifest = []
    iSaved = 0
    iResult = 0
    try:
        iSaved = gatherEstate(sFolder, lManifest)
    except KeyboardInterrupt:
        logging.warning("stopped from the keyboard; what is on disk is still good and a later run resumes")
    except BaseException as oError:
        logging.exception("the crawl ended with an error: %s: %s", type(oError).__name__, oError)
        iResult = 1
    # Everything below used to sit OUTSIDE any protection, so a fault here left a
    # console traceback and a log that simply stopped in mid air. It is inside now,
    # and the log always ends with a RUN ENDED line saying how the run finished.
    try:
        fHandle = io.open(os.path.join(sFolder, "manifest.txt"), "w", encoding="utf-8-sig", newline="\\r\\n")
        fHandle.write("address\\tfile\\tbytes\\r\\n")
        for sLine in lManifest: fHandle.write(sLine + "\\r\\n")
        fHandle.close()
    except BaseException as oError:
        logging.exception("the manifest could not be written: %s: %s", type(oError).__name__, oError)
        iResult = 1
    for sKind, iCount in sorted(g_dRepeatCounts.items()):
        logging.info("tally: %s occurred %d times", sKind, iCount)
    sZipPath = os.path.join(sScriptDir, c_sZipName)
    iFiles = 0
    try:
        iFiles = writeArchive(sFolder, sZipPath)
        logging.info("VERDICT: %d pages saved this run, %d files in the archive, %.1f MB",
                     iSaved, iFiles, os.path.getsize(sZipPath) / 1048576.0)
    except BaseException as oError:
        logging.exception("the archive could not be written: %s: %s", type(oError).__name__, oError)
        iResult = 1
    logging.info("RUN ENDED %s: %d pages saved, %d files archived",
                 "with an error" if iResult else "cleanly", iSaved, iFiles)
    print("Saved this run: %d" % iSaved)
    print("Files in the archive: %d" % iFiles)
    print("UPLOAD THIS FILE: " + sZipPath)
    print("Log: " + os.path.join(sScriptDir, c_sLogName))
    if iResult: print("THE RUN ENDED WITH AN ERROR. Its reason is written in the log.")
    return iResult


if __name__ == "__main__": sys.exit(main())
'''

c_lEstates = [
    {
        "sProduct": "Blinkist",
        "sScriptName": "getBlinkistHelp.py",
        "sSystem": "Intercom",
        "sFolder": "BlinkistHelp",
        "sLogName": "getBlinkistHelp.log",
        "sZipName": "BlinkistHelp.zip",
        "iMaxPages": 400,
        "nDelay": 1.0,
        "sSeeds": '"https://support.blinkist.com/en/"',
        "sFencePattern": r"^https://support\.blinkist\.com/en(/|$)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(intercom|help center|<article|collections/)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Vox",
        "sScriptName": "getVoxHelp.py",
        "sSystem": "Zendesk, by the listing route",
        "sFolder": "VoxHelp",
        "sLogName": "getVoxHelp.log",
        "sZipName": "VoxHelp.zip",
        "iMaxPages": 300,
        "nDelay": 1.0,
        "sSeeds": ('"https://voxmembership.zendesk.com/api/v2/help_center/en-us/articles.json?per_page=100",\n'
                   '              "https://voxmembership.zendesk.com/api/v2/help_center/en-us/categories.json?per_page=100",\n'
                   '              "https://voxmembership.zendesk.com/api/v2/help_center/en-us/sections.json?per_page=100",\n'
                   '              "https://voxmembership.zendesk.com/hc/en-us"'),
        "sFencePattern": r"^https://voxmembership\.zendesk\.com/(hc/en-us|api/v2/help_center/en-us)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(<article|hc/en-us/articles/|help center)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": ('    if sText.lstrip().startswith("{"):\n'
                        '        try:\n'
                        '            dPayload = json.loads(sText)\n'
                        '            if dPayload.get("next_page"): lFound.append(dPayload["next_page"])\n'
                        '        except Exception as oError:\n'
                        '            logging.warning("a listing page was not readable as JSON: %s", oError)\n'),
    },
    {
        "sProduct": "Slate",
        "sScriptName": "getSlateHelp.py",
        "sSystem": "Freshdesk",
        "sFolder": "SlateHelp",
        "sLogName": "getSlateHelp.log",
        "sZipName": "SlateHelp.zip",
        "iMaxPages": 300,
        "nDelay": 1.0,
        "sSeeds": ('"https://slatehelp.freshdesk.com/support/solutions",\n'
                   '              "https://slatehelp.freshdesk.com/support/home"'),
        "sFencePattern": r"^https://slatehelp\.freshdesk\.com/support/(solutions|home)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(support/solutions|freshdesk|<article)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "TIME",
        "sScriptName": "getTimeHelp.py",
        "sSystem": "one page, served whole",
        "sFolder": "TimeHelp",
        "sLogName": "getTimeHelp.log",
        "sZipName": "TimeHelp.zip",
        "iMaxPages": 20,
        "nDelay": 1.0,
        "sSeeds": '"https://support.time.com/"',
        "sFencePattern": r"^https://support\.time\.com/?$",
        "sSubjectPattern": "",
        "sReadyPattern": r"(Managing Your Subscription|Reaching Customer Care|support pages for time)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "The Atlantic",
        "sScriptName": "getAtlanticHelp.py",
        "sSystem": "Zendesk, by the listing route",
        "sFolder": "AtlanticHelp",
        "sLogName": "getAtlanticHelp.log",
        "sZipName": "AtlanticHelp.zip",
        "iMaxPages": 400,
        "nDelay": 1.0,
        "sSeeds": ('"https://support.theatlantic.com/api/v2/help_center/en-us/articles.json?per_page=100",\n'
                   '              "https://support.theatlantic.com/api/v2/help_center/en-us/categories.json?per_page=100",\n'
                   '              "https://support.theatlantic.com/api/v2/help_center/en-us/sections.json?per_page=100",\n'
                   '              "https://support.theatlantic.com/hc/en-us"'),
        "sFencePattern": r"^https://support\.theatlantic\.com/(hc/en-us|api/v2/help_center/en-us)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(hc/en-us/articles/|help center|\"articles\")",
        "sOkStatuses": "200, 202",
        "sExtraLinks": ('    if sText.lstrip().startswith("{"):\n'
                        '        try:\n'
                        '            dPayload = json.loads(sText)\n'
                        '            if dPayload.get("next_page"): lFound.append(dPayload["next_page"])\n'
                        '        except Exception as oError:\n'
                        '            logging.warning("a listing page was not readable as JSON: %s", oError)\n'),
    },
    {
        "sProduct": "Nature",
        "sScriptName": "getNatureHelp.py",
        "sSystem": "Freshdesk",
        "sFolder": "NatureHelp",
        "sLogName": "getNatureHelp.log",
        "sZipName": "NatureHelp.zip",
        "iMaxPages": 400,
        "nDelay": 1.0,
        "sSeeds": ('"https://support.nature.com/en/support/home",\n'
                   '              "https://support.nature.com/en/support/solutions"'),
        "sFencePattern": r"^https://support\.nature\.com/en/support/(home|solutions)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(support/solutions|freshdesk|knowledge base)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "New Scientist",
        "sScriptName": "getNewScientistHelp.py",
        "sSystem": "one page, served whole",
        "sFolder": "NewScientistHelp",
        "sLogName": "getNewScientistHelp.log",
        "sZipName": "NewScientistHelp.zip",
        "iMaxPages": 20,
        "nDelay": 1.0,
        "sSeeds": '"https://www.newscientist.com/help/"',
        "sFencePattern": r"^https://www\.newscientist\.com/help/?$",
        "sSubjectPattern": "",
        "sReadyPattern": r"(subscription|account|newsletter)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Snopes",
        "sScriptName": "getSnopesHelp.py",
        "sSystem": "one page, served whole",
        "sFolder": "SnopesHelp",
        "sLogName": "getSnopesHelp.log",
        "sZipName": "SnopesHelp.zip",
        "iMaxPages": 20,
        "nDelay": 1.0,
        "sSeeds": '"https://www.snopes.com/faqs/"',
        "sFencePattern": r"^https://www\.snopes\.com/faqs/?$",
        "sSubjectPattern": "",
        "sReadyPattern": r"(frequently asked|faq|snopes)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "The Nation",
        "sScriptName": "getNationHelp.py",
        "sSystem": "two pages, served whole",
        "sFolder": "NationHelp",
        "sLogName": "getNationHelp.log",
        "sZipName": "NationHelp.zip",
        "iMaxPages": 20,
        "nDelay": 1.0,
        "sSeeds": ('"https://www.thenation.com/help/",\n'
                   '              "https://www.thenation.com/donation/faq/"'),
        "sFencePattern": r"^https://www\.thenation\.com/(help|donation/faq)/?$",
        "sSubjectPattern": "",
        "sReadyPattern": r"(subscription|donation|account|faq)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Scientific American",
        "sScriptName": "getSciAmHelp.py",
        "sSystem": "one page, served whole",
        "sFolder": "SciAmHelp",
        "sLogName": "getSciAmHelp.log",
        "sZipName": "SciAmHelp.zip",
        "iMaxPages": 20,
        "nDelay": 1.0,
        "sSeeds": '"https://www.scientificamerican.com/contact-us/"',
        "sFencePattern": r"^https://www\.scientificamerican\.com/(page/)?contact-us/?$",
        "sSubjectPattern": "",
        "sReadyPattern": r"(subscription|customer service|contact)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Smithsonian",
        "sScriptName": "getSmithsonianHelp.py",
        "sSystem": "an outsourced customer service site",
        "sFolder": "SmithsonianHelp",
        "sLogName": "getSmithsonianHelp.log",
        "sZipName": "SmithsonianHelp.zip",
        "iMaxPages": 60,
        "nDelay": 1.5,
        "sSeeds": '"https://ssl.drgnetwork.com/SMT/cs/gidSMALL/faq"',
        "sFencePattern": r"^https://ssl\.drgnetwork\.com/SMT/cs/",
        "sSubjectPattern": "",
        "sReadyPattern": r"(subscription|faq|customer service)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Nature",
        "sScriptName": "getNatureHelp2.py",
        "sSystem": "Freshdesk, second run",
        "sFolder": "NatureHelp",
        "sLogName": "getNatureHelp2.log",
        "sZipName": "NatureHelp2.zip",
        "iMaxPages": 2500,
        "nDelay": 1.0,
        "sSeeds": ('"https://support.nature.com/en/support/home",\n'
                   '              "https://support.nature.com/en/support/solutions"'),
        "sFencePattern": r"^https://support\.nature\.com/en/support/(home|solutions)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(support/solutions|freshdesk|knowledge base)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Magazine subscriber service (Vogue, Glamour, Cosmopolitan, Men's Health)",
        "sScriptName": "getMagazineServiceHelp.py",
        "sSystem": "the fulfilment contractor that publishes these magazines' answers",
        "sFolder": "MagazineServiceHelp",
        "sLogName": "getMagazineServiceHelp.log",
        "sZipName": "MagazineServiceHelp.zip",
        "iMaxPages": 300,
        "nDelay": 1.5,
        "sSeeds": ('"https://w1.buysub.com/pubs/N3/VO3/FAQ_new.jsp?cds_mag_code=VO3",\n'
                   '              "https://w1.buysub.com/pubs/N3/VO3/Sitemap.jsp?cds_mag_code=VO3",\n'
                   '              "https://w1.buysub.com/pubs/N3/VOG/VOG_FAQ2.jsp?cds_mag_code=VOG",\n'
                   '              "https://w1.buysub.com/pubs/N3/VOG/FAQ_new.jsp?cds_mag_code=VOG",\n'
                   '              "https://w1.buysub.com/pubs/N3/GLM/FAQ_new.jsp?cds_mag_code=GLM",\n'
                   '              "https://w1.buysub.com/pubs/N4/GLM/FAQ_new.jsp?cds_mag_code=GLM",\n'
                   '              "https://w1.buysub.com/pubs/HR/COS/FAQ_new.jsp?cds_mag_code=COS",\n'
                   '              "https://w1.buysub.com/pubs/HR/COS/COS_FAQ2.jsp?cds_mag_code=COS",\n'
                   '              "https://w1.buysub.com/pubs/HR/MEH/FAQ_new.jsp?cds_mag_code=MEH",\n'
                   '              "https://w1.buysub.com/pubs/HR/MEH/MEH_FAQ2.jsp?cds_mag_code=MEH"'),
        "sFencePattern": r"^https://w1\.buysub\.com/pubs/[A-Z0-9]{1,3}/(VO3|VOG|GLM|COS|MEH)/(?!.*(RegistrationGateway|account_summary|login|signin|cofe_new|payment|renew_))",
        "sSubjectPattern": "",
        "sReadyPattern": r"(frequently asked questions|customer (service|care))",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Magazine subscriber service, second run",
        "sScriptName": "getMagazineServiceHelp2.py",
        "sSystem": "the fulfilment contractor, with more page names tried",
        "sFolder": "MagazineServiceHelp",
        "sLogName": "getMagazineServiceHelp2.log",
        "sZipName": "MagazineServiceHelp2.zip",
        "iMaxPages": 300,
        "nDelay": 1.5,
        "sSeeds": ('"https://w1.buysub.com/pubs/HR/COS/COS_FAQ.jsp?cds_mag_code=COS",\n'
                   '              "https://w1.buysub.com/pubs/HR/COS/faq.jsp?cds_mag_code=COS",\n'
                   '              "https://w1.buysub.com/pubs/HR/COS/COS_faq2.jsp?cds_mag_code=COS",\n'
                   '              "https://w1.buysub.com/pubs/HR/COS/Sitemap.jsp?cds_mag_code=COS",\n'
                   '              "https://w1.buysub.com/pubs/HR/COS/customer_service.jsp?cds_mag_code=COS",\n'
                   '              "https://w1.buysub.com/pubs/HR/MEH/MEH_FAQ.jsp?cds_mag_code=MEH",\n'
                   '              "https://w1.buysub.com/pubs/HR/MEH/faq.jsp?cds_mag_code=MEH",\n'
                   '              "https://w1.buysub.com/pubs/HR/MEH/Sitemap.jsp?cds_mag_code=MEH",\n'
                   '              "https://w1.buysub.com/pubs/HR/MH1/FAQ_new.jsp?cds_mag_code=MH1",\n'
                   '              "https://w1.buysub.com/pubs/N3/GLA/FAQ_new.jsp?cds_mag_code=GLA",\n'
                   '              "https://w1.buysub.com/pubs/N3/GLR/FAQ_new.jsp?cds_mag_code=GLR",\n'
                   '              "https://w1.buysub.com/pubs/N3/GL1/FAQ_new.jsp?cds_mag_code=GL1",\n'
                   '              "https://w1.buysub.com/pubs/N3/VOG/FAQ_new.jsp?cds_mag_code=VOG",\n'
                   '              "https://w1.buysub.com/pubs/N3/VO3/FAQ_new.jsp?cds_mag_code=VO3"'),
        "sFencePattern": r"^https://w1\.buysub\.com/pubs/[A-Z0-9]{1,3}/(VO3|VOG|GLM|GLA|GLR|GL1|COS|MEH|MH1)/(?!.*(RegistrationGateway|account_summary|login|signin|cofe_new|payment|renew_))",
        "sSubjectPattern": "",
        "sReadyPattern": r"(frequently asked questions|customer (service|care))",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Men's Health",
        "sScriptName": "getMensHealthHelp.py",
        "sSystem": "the fulfilment contractor, magazine code MHL",
        "sFolder": "MensHealthHelp",
        "sLogName": "getMensHealthHelp.log",
        "sZipName": "MensHealthHelp.zip",
        "iMaxPages": 200,
        "nDelay": 1.5,
        "sSeeds": ('"https://w1.buysub.com/pubs/HR/MHL/MHL_FAQ.jsp?cds_mag_code=MHL",\n'
                   '              "https://w1.buysub.com/pubs/HR/MHL/FAQ_new.jsp?cds_mag_code=MHL",\n'
                   '              "https://w1.buysub.com/pubs/HR/MHL/MHL_FAQ2.jsp?cds_mag_code=MHL",\n'
                   '              "https://w1.buysub.com/pubs/HR/MHL/Sitemap.jsp?cds_mag_code=MHL",\n'
                   '              "https://w1.buysub.com/servlet/CSGateway?cds_mag_code=MHL"'),
        "sFencePattern": r"^https://w1\.buysub\.com/(pubs/[A-Z0-9]{1,3}/MHL/(?!.*(RegistrationGateway|account_summary|login|signin|cofe_new|payment|renew_))|servlet/CSGateway)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(frequently asked questions|customer (service|care))",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Strava",
        "sScriptName": "getStravaHelp.py",
        "sSystem": "Intercom",
        "sFolder": "StravaHelp",
        "sLogName": "getStravaHelp.log",
        "sZipName": "StravaHelp.zip",
        "iMaxPages": 600,
        "nDelay": 1.0,
        "sSeeds": ('"https://support.strava.com/en-us/",\n'
                   '              "https://support.strava.com/en-us/collections/19657601-getting-started"'),
        "sFencePattern": r"^https://support\.strava\.com/en-us(/|$)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(intercom|help center|<article|collections/)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Halo",
        "sScriptName": "getHaloHelp.py",
        "sSystem": "Zendesk, by the listing route",
        "sFolder": "HaloHelp",
        "sLogName": "getHaloHelp.log",
        "sZipName": "HaloHelp.zip",
        "iMaxPages": 600,
        "nDelay": 1.0,
        "sSeeds": ('"https://support.halowaypoint.com/api/v2/help_center/en-us/articles.json?per_page=100",\n'
                   '              "https://support.halowaypoint.com/api/v2/help_center/en-us/categories.json?per_page=100",\n'
                   '              "https://support.halowaypoint.com/api/v2/help_center/en-us/sections.json?per_page=100",\n'
                   '              "https://support.halowaypoint.com/hc/en-us"'),
        "sFencePattern": r"^https://support\.halowaypoint\.com/(hc/en-us|api/v2/help_center/en-us)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(hc/en-us/articles/|help center|\"articles\")",
        "sOkStatuses": "200, 202",
        "sExtraLinks": ('    if sText.lstrip().startswith("{"):\n'
                        '        try:\n'
                        '            dPayload = json.loads(sText)\n'
                        '            if dPayload.get("next_page"): lFound.append(dPayload["next_page"])\n'
                        '        except Exception as oError:\n'
                        '            logging.warning("a listing page was not readable as JSON: %s", oError)\n'),
    },
    {
        "sProduct": "CrimeCon",
        "sScriptName": "getCrimeConHelp.py",
        "sSystem": "one page, served whole",
        "sFolder": "CrimeConHelp",
        "sLogName": "getCrimeConHelp.log",
        "sZipName": "CrimeConHelp.zip",
        "iMaxPages": 20,
        "nDelay": 1.5,
        "sSeeds": ('"https://www.crimecon.com/faq",\n'
                   '              "https://www.crimecon.com/contact"'),
        "sFencePattern": r"^https://www\.crimecon\.com/(faq|contact)/?$",
        "sSubjectPattern": "",
        "sReadyPattern": r"(frequently asked|faq|ticket|badge)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Medium",
        "sScriptName": "getMediumHelp.py",
        "sSystem": "Zendesk, by the listing route",
        "sFolder": "MediumHelp",
        "sLogName": "getMediumHelp.log",
        "sZipName": "MediumHelp.zip",
        "iMaxPages": 800,
        "nDelay": 1.0,
        "sSeeds": ('"https://help.medium.com/api/v2/help_center/en-us/articles.json?per_page=100",\n'
                   '              "https://help.medium.com/api/v2/help_center/en-us/categories.json?per_page=100",\n'
                   '              "https://help.medium.com/api/v2/help_center/en-us/sections.json?per_page=100",\n'
                   '              "https://help.medium.com/hc/en-us"'),
        "sFencePattern": r"^https://help\.medium\.com/(hc/en-us|api/v2/help_center/en-us)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(hc/en-us/articles/|help center|articles.:)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": ('    if sText.lstrip().startswith("{"):\n        try:\n            dPayload = json.loads(sText)\n            if dPayload.get("next_page"): lFound.append(dPayload["next_page"])\n        except Exception as oError:\n            logging.warning("a listing page was not readable as JSON: %s", oError)\n'),
    },
    {
        "sProduct": "Substack",
        "sScriptName": "getSubstackHelp.py",
        "sSystem": "Zendesk, by the listing route",
        "sFolder": "SubstackHelp",
        "sLogName": "getSubstackHelp.log",
        "sZipName": "SubstackHelp.zip",
        "iMaxPages": 800,
        "nDelay": 1.0,
        "sSeeds": ('"https://support.substack.com/api/v2/help_center/en-us/articles.json?per_page=100",\n'
                   '              "https://support.substack.com/api/v2/help_center/en-us/categories.json?per_page=100",\n'
                   '              "https://support.substack.com/api/v2/help_center/en-us/sections.json?per_page=100",\n'
                   '              "https://support.substack.com/hc/en-us"'),
        "sFencePattern": r"^https://support\.substack\.com/(hc/en-us|api/v2/help_center/en-us)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(hc/en-us/articles/|help center|articles.:)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": ('    if sText.lstrip().startswith("{"):\n        try:\n            dPayload = json.loads(sText)\n            if dPayload.get("next_page"): lFound.append(dPayload["next_page"])\n        except Exception as oError:\n            logging.warning("a listing page was not readable as JSON: %s", oError)\n'),
    },
    {
        "sProduct": "Reddit",
        "sScriptName": "getRedditHelp.py",
        "sSystem": "Zendesk, by the listing route",
        "sFolder": "RedditHelp",
        "sLogName": "getRedditHelp.log",
        "sZipName": "RedditHelp.zip",
        "iMaxPages": 800,
        "nDelay": 1.0,
        "sSeeds": ('"https://support.reddithelp.com/api/v2/help_center/en-us/articles.json?per_page=100",\n'
                   '              "https://support.reddithelp.com/api/v2/help_center/en-us/categories.json?per_page=100",\n'
                   '              "https://support.reddithelp.com/api/v2/help_center/en-us/sections.json?per_page=100",\n'
                   '              "https://support.reddithelp.com/hc/en-us"'),
        "sFencePattern": r"^https://support\.reddithelp\.com/(hc/en-us|api/v2/help_center/en-us)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(hc/en-us/articles/|help center|articles.:)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": ('    if sText.lstrip().startswith("{"):\n        try:\n            dPayload = json.loads(sText)\n            if dPayload.get("next_page"): lFound.append(dPayload["next_page"])\n        except Exception as oError:\n            logging.warning("a listing page was not readable as JSON: %s", oError)\n'),
    },
    {
        "sProduct": "Good Housekeeping",
        "sScriptName": "getGoodHousekeepingHelp.py",
        "sSystem": "the fulfilment contractor, magazine code GHK",
        "sFolder": "GoodHousekeepingHelp",
        "sLogName": "getGoodHousekeepingHelp.log",
        "sZipName": "GoodHousekeepingHelp.zip",
        "iMaxPages": 200,
        "nDelay": 1.5,
        "sSeeds": ('"https://w1.buysub.com/pubs/HR/GHK/GHK_FAQ.jsp?cds_mag_code=GHK",\n'
                   '              "https://w1.buysub.com/pubs/HR/GHK/FAQ_new.jsp?cds_mag_code=GHK"'),
        "sFencePattern": r"^https://w1\.buysub\.com/pubs/[A-Z0-9]{1,3}/GHK/(?!.*(RegistrationGateway|account_summary|login|signin|cofe_new|payment|renew_))",
        "sSubjectPattern": "",
        "sReadyPattern": r"(frequently asked questions|customer (service|care))",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Sports Illustrated",
        "sScriptName": "getSportsIllustratedHelp.py",
        "sSystem": "the fulfilment contractor, magazine code SPI",
        "sFolder": "SportsIllustratedHelp",
        "sLogName": "getSportsIllustratedHelp.log",
        "sZipName": "SportsIllustratedHelp.zip",
        "iMaxPages": 200,
        "nDelay": 1.5,
        "sSeeds": ('"https://w1.buysub.com/pubs/MT/SPI/SPI_FAQ.jsp?cds_mag_code=SPI",\n'
                   '              "https://w1.buysub.com/pubs/MT/SPI/FAQ_new.jsp?cds_mag_code=SPI",\n'
                   '              "https://w1.buysub.com/pubs/MT/SPI/Sitemap.jsp?cds_mag_code=SPI"'),
        "sFencePattern": r"^https://w1\.buysub\.com/pubs/[A-Z0-9]{1,3}/SPI/(?!.*(RegistrationGateway|account_summary|login|signin|cofe_new|payment|renew_))",
        "sSubjectPattern": "",
        "sReadyPattern": r"(frequently asked questions|customer (service|care))",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Jira",
        "sScriptName": "getJiraHelp.py",
        "sSystem": "Atlassian's own documentation site",
        "sFolder": "JiraHelp",
        "sLogName": "getJiraHelp.log",
        "sZipName": "JiraHelp.zip",
        "iMaxPages": 2000,
        "nDelay": 1.0,
        "sSeeds": ('"https://support.atlassian.com/jira-software-cloud/",\n'
                   '              "https://support.atlassian.com/jira-software-cloud/docs/"'),
        "sFencePattern": r"^https://support\.atlassian\.com/jira-software-cloud/",
        "sSubjectPattern": "",
        "sReadyPattern": r"(atlassian|jira)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Confluence",
        "sScriptName": "getConfluenceHelp.py",
        "sSystem": "Atlassian's own documentation site",
        "sFolder": "ConfluenceHelp",
        "sLogName": "getConfluenceHelp.log",
        "sZipName": "ConfluenceHelp.zip",
        "iMaxPages": 2000,
        "nDelay": 1.0,
        "sSeeds": ('"https://support.atlassian.com/confluence-cloud/",\n'
                   '              "https://support.atlassian.com/confluence-cloud/docs/"'),
        "sFencePattern": r"^https://support\.atlassian\.com/confluence-cloud/",
        "sSubjectPattern": "",
        "sReadyPattern": r"(atlassian|confluence)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Rocket Money",
        "sScriptName": "getRocketMoneyHelp.py",
        "sSystem": "Intercom",
        "sFolder": "RocketMoneyHelp",
        "sLogName": "getRocketMoneyHelp.log",
        "sZipName": "RocketMoneyHelp.zip",
        "iMaxPages": 600,
        "nDelay": 1.0,
        "sSeeds": ('"https://help.rocketmoney.com/en/",\n'
                   '              "https://help.rocketmoney.com/en/articles/934773-common-linking-issues"'),
        "sFencePattern": r"^https://help\.rocketmoney\.com/en(/|$)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(intercom|help center|<article|collections/)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Poe",
        "sScriptName": "getPoeHelp.py",
        "sSystem": "Zendesk, by the listing route",
        "sFolder": "PoeHelp",
        "sLogName": "getPoeHelp.log",
        "sZipName": "PoeHelp.zip",
        "iMaxPages": 600,
        "nDelay": 1.0,
        "sSeeds": ('"https://help.poe.com/api/v2/help_center/en-us/articles.json?per_page=100",\n'
                   '              "https://help.poe.com/api/v2/help_center/en-us/categories.json?per_page=100",\n'
                   '              "https://help.poe.com/api/v2/help_center/en-us/sections.json?per_page=100",\n'
                   '              "https://help.poe.com/hc/en-us"'),
        "sFencePattern": r"^https://help\.poe\.com/(hc/en-us|api/v2/help_center/en-us)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(hc/en-us/articles/|help center|articles.:)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": ('    if sText.lstrip().startswith("{"):\n'
                        '        try:\n'
                        '            dPayload = json.loads(sText)\n'
                        '            if dPayload.get("next_page"): lFound.append(dPayload["next_page"])\n'
                        '        except Exception as oError:\n'
                        '            logging.warning("a listing page was not readable as JSON: %s", oError)\n'),
    },
    {
        "sProduct": "Fire TV",
        "sScriptName": "getFireTvHelp.py",
        "sSystem": "Amazon's one help tree, held to Fire TV by a subject gate",
        "sFolder": "FireTvHelp",
        "sLogName": "getFireTvHelp.log",
        "sZipName": "FireTvHelp.zip",
        "iMaxPages": 500,
        "nDelay": 2.0,
        "sSeeds": ('"https://www.amazon.com/gp/help/customer/display.html?nodeId=GHH5TUHA7677G4HJ",\n'
                   '              "https://www.amazon.com/gp/help/customer/display.html?nodeId=GYCLCP2N9RUB5G6R",\n'
                   '              "https://www.amazon.com/gp/help/customer/display.html?nodeId=G8ZS4V2RFVDTEPWZ"'),
        "sFencePattern": r"^https://www\.amazon\.com/gp/help/customer/display\.html\?nodeId=[A-Z0-9]+$",
        "sSubjectPattern": r"(fire tv|fire stick|firestick|fire television|alexa voice remote|omni|4k stick)",
        "sReadyPattern": r"(help|amazon)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Sword and Scale",
        "sScriptName": "getSwordAndScaleHelp.py",
        "sSystem": "Freshdesk",
        "sFolder": "SwordAndScaleHelp",
        "sLogName": "getSwordAndScaleHelp.log",
        "sZipName": "SwordAndScaleHelp.zip",
        "iMaxPages": 300,
        "nDelay": 1.0,
        "sSeeds": ('"https://support.swordandscale.com/support/home",\n'
                   '              "https://support.swordandscale.com/support/solutions"'),
        "sFencePattern": r"^https://support\.swordandscale\.com/support/(home|solutions)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(support/solutions|freshdesk|knowledge base|sword)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "The Moth",
        "sScriptName": "getMothHelp.py",
        "sSystem": "one page, served whole",
        "sFolder": "MothHelp",
        "sLogName": "getMothHelp.log",
        "sZipName": "MothHelp.zip",
        "iMaxPages": 20,
        "nDelay": 1.5,
        "sSeeds": '"https://www.themoth.org/about/faq"',
        "sFencePattern": r"^https://www\.themoth\.org/about/faq/?$",
        "sSubjectPattern": "",
        "sReadyPattern": r"(frequently asked|faq|story|moth)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "RISK!",
        "sScriptName": "getRiskShowHelp.py",
        "sSystem": "two pages, served whole",
        "sFolder": "RiskShowHelp",
        "sLogName": "getRiskShowHelp.log",
        "sZipName": "RiskShowHelp.zip",
        "iMaxPages": 20,
        "nDelay": 1.5,
        "sSeeds": ('"https://www.risk-show.com/podcast/help/",\n'
                   '              "https://risk-show.com/faq/"'),
        "sFencePattern": r"^https://(www\.)?risk-show\.com/(podcast/help|faq)/?$",
        "sSubjectPattern": "",
        "sReadyPattern": r"(podcast|faq|episode|risk)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "RISK!, second run",
        "sScriptName": "getRiskShowHelp2.py",
        "sSystem": "a handful of named pages, no crawling",
        "sFolder": "RiskShowHelp",
        "sLogName": "getRiskShowHelp2.log",
        "sZipName": "RiskShowHelp2.zip",
        "iMaxPages": 20,
        "nDelay": 1.5,
        "sSeeds": ('"https://www.risk-show.com/podcast/help/",\n'
                   '              "https://www.risk-show.com/podcast/faq/",\n'
                   '              "https://www.risk-show.com/faq/",\n'
                   '              "https://www.risk-show.com/help/",\n'
                   '              "https://www.risk-show.com/support/",\n'
                   '              "https://www.risk-show.com/about-us/",\n'
                   '              "https://www.risk-show.com/contactus/",\n'
                   '              "https://www.risk-show.com/contact/"'),
        "sFencePattern": r"^https://(www\.)?risk-show\.com/(podcast/(help|faq)|faq|help|support|about-us|contact|contactus)/?$",
        "sSubjectPattern": "",
        "sReadyPattern": r"(risk|podcast|story|contact)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Truepic",
        "sScriptName": "getTruepicHelp.py",
        "sSystem": "Intercom",
        "sFolder": "TruepicHelp",
        "sLogName": "getTruepicHelp.log",
        "sZipName": "TruepicHelp.zip",
        "iMaxPages": 300,
        "nDelay": 1.0,
        "sSeeds": '"https://help.truepic.com/en/"',
        "sFencePattern": r"^https://help\.truepic\.com/en(/|$)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(intercom|help center|<article|collections/)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Fire TV, second run",
        "sScriptName": "getFireTvHelp2.py",
        "sSystem": "Amazon's one help tree, held to Fire TV by a subject gate",
        "sFolder": "FireTvHelp",
        "sLogName": "getFireTvHelp2.log",
        "sZipName": "FireTvHelp2.zip",
        "iMaxPages": 1200,
        "nDelay": 2.0,
        "sSeeds": ('"https://www.amazon.com/gp/help/customer/display.html?nodeId=GHH5TUHA7677G4HJ",\n'
                   '              "https://www.amazon.com/gp/help/customer/display.html?nodeId=GYCLCP2N9RUB5G6R",\n'
                   '              "https://www.amazon.com/gp/help/customer/display.html?nodeId=G8ZS4V2RFVDTEPWZ"'),
        "sFencePattern": r"^https://www\.amazon\.com/gp/help/customer/display\.html\?nodeId=[A-Z0-9]+$",
        "sSubjectPattern": r"(fire tv|fire stick|firestick|fire television|alexa voice remote|omni|4k stick|recast)",
        "sReadyPattern": r"(help|amazon)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Furnished Finder and KeyCheck",
        "sScriptName": "getFurnishedFinderHelp.py",
        "sSystem": "Zendesk, by the listing route",
        "sFolder": "FurnishedFinderHelp",
        "sLogName": "getFurnishedFinderHelp.log",
        "sZipName": "FurnishedFinderHelp.zip",
        "iMaxPages": 800,
        "nDelay": 1.0,
        "sSeeds": ('"https://support.furnishedfinder.com/api/v2/help_center/en-us/articles.json?per_page=100",\n'
                   '              "https://support.furnishedfinder.com/api/v2/help_center/en-us/categories.json?per_page=100",\n'
                   '              "https://support.furnishedfinder.com/api/v2/help_center/en-us/sections.json?per_page=100",\n'
                   '              "https://support.furnishedfinder.com/hc/en-us"'),
        "sFencePattern": r"^https://support\.furnishedfinder\.com/(hc/en-us|api/v2/help_center/en-us)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(hc/en-us/articles/|help center|articles.:)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": ('    if sText.lstrip().startswith("{"):\n'
                        '        try:\n'
                        '            dPayload = json.loads(sText)\n'
                        '            if dPayload.get("next_page"): lFound.append(dPayload["next_page"])\n'
                        '        except Exception as oError:\n'
                        '            logging.warning("a listing page was not readable as JSON: %s", oError)\n'),
    },
{
        "sProduct": "Sports Illustrated, second run",
        "sScriptName": "getSportsIllustratedHelp2.py",
        "sSystem": "the fulfilment contractor, more page names tried",
        "sFolder": "SportsIllustratedHelp",
        "sLogName": "getSportsIllustratedHelp2.log",
        "sZipName": "SportsIllustratedHelp2.zip",
        "iMaxPages": 200,
        "nDelay": 1.5,
        "sSeeds": ('"https://w1.buysub.com/pubs/MT/SPI/contact_cs_conf.jsp?cds_mag_code=SPI",\n'
                   '              "https://w1.buysub.com/pubs/MT/SPI/contact_cs_new.jsp?cds_mag_code=SPI",\n'
                   '              "https://w1.buysub.com/pubs/MT/SPI/SPI_FAQ2.jsp?cds_mag_code=SPI",\n'
                   '              "https://w1.buysub.com/pubs/MT/SPI/faq.jsp?cds_mag_code=SPI",\n'
                   '              "https://w1.buysub.com/pubs/MT/SPI/help.jsp?cds_mag_code=SPI",\n'
                   '              "https://w1.buysub.com/pubs/MT/SPI/customer_service.jsp?cds_mag_code=SPI",\n'
                   '              "https://w1.buysub.com/pubs/MT/SPI/SPI_customer_service.jsp?cds_mag_code=SPI",\n'
                   '              "https://w1.buysub.com/servlet/CSGateway?cds_mag_code=SPI"'),
        "sFencePattern": r"^https://w1\.buysub\.com/(pubs/[A-Z0-9]{1,3}/SPI/(?!.*(RegistrationGateway|account_summary|login|signin|cofe_new|payment|renew_))|servlet/CSGateway)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(frequently asked questions|customer (service|care))",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "iHeartRadio",
        "sScriptName": "getIHeartHelp.py",
        "sSystem": "Zendesk, by the listing route",
        "sFolder": "IHeartHelp",
        "sLogName": "getIHeartHelp.log",
        "sZipName": "IHeartHelp.zip",
        "iMaxPages": 600,
        "nDelay": 1.0,
        "sSeeds": ('"https://help.iheart.com/api/v2/help_center/en-us/articles.json?per_page=100",\n'
                   '              "https://help.iheart.com/api/v2/help_center/en-us/categories.json?per_page=100",\n'
                   '              "https://help.iheart.com/api/v2/help_center/en-us/sections.json?per_page=100",\n'
                   '              "https://help.iheart.com/hc/en-us"'),
        "sFencePattern": r"^https://help\.iheart\.com/(hc/en-us|api/v2/help_center/en-us)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(hc/en-us/articles/|help center|articles.:)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": ('    if sText.lstrip().startswith("{"):\n'
                        '        try:\n'
                        '            dPayload = json.loads(sText)\n'
                        '            if dPayload.get("next_page"): lFound.append(dPayload["next_page"])\n'
                        '        except Exception as oError:\n'
                        '            logging.warning("a listing page was not readable as JSON: %s", oError)\n'),
    },
    {
        "sProduct": "Freedom Scientific",
        "sScriptName": "getFreedomScientificHelp.py",
        "sSystem": "the publisher's own support and training pages",
        "sFolder": "FreedomScientificHelp",
        "sLogName": "getFreedomScientificHelp.log",
        "sZipName": "FreedomScientificHelp.zip",
        "iMaxPages": 900,
        "nDelay": 1.0,
        "sSeeds": ('"https://support.freedomscientific.com/support",\n'
                   '              "https://support.freedomscientific.com/SurfsUp/1-StartHere.htm",\n'
                   '              "https://support.freedomscientific.com/Services/TrainingAndCertification",\n'
                   '              "https://support.freedomscientific.com/teachers/lessons/7.1.1_WhatIsSurfsUp.htm",\n'
                   '              "https://www.freedomscientific.com/training/jaws/",\n'
                   '              "https://www.freedomscientific.com/training/"'),
        "sFencePattern": r"^https://(support|www)\.freedomscientific\.com/(?!.*(/downloads/|\.exe|\.msi|\.zip|\.dmg|/cart|/store))",
        "sSubjectPattern": "",
        "sReadyPattern": r"(jaws|zoomtext|fusion|freedom scientific|surf)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Ablr",
        "sScriptName": "getAblrHelp.py",
        "sSystem": "the company's own reference pages",
        "sFolder": "AblrHelp",
        "sLogName": "getAblrHelp.log",
        "sZipName": "AblrHelp.zip",
        "iMaxPages": 200,
        "nDelay": 1.5,
        "sSeeds": ('"https://ablr360.com/faqs/",\n'
                   '              "https://ablr360.com/accessibility-dictionary/",\n'
                   '              "https://ablr360.com/welcome-to-ablr/",\n'
                   '              "https://ablr360.com/disability-inclusion/accessibility-training-sessions/",\n'
                   '              "https://ablr360.com/resources/"'),
        "sFencePattern": r"^https://(www\.)?ablr360\.com/(?!(wp-|category/|tag/|author/|podcast|news|press-release|20\d\d/))(faqs|accessibility-dictionary|welcome-to-ablr|resources|disability-inclusion|services|training)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(accessibility|ablr|disability)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Rolling Stone",
        "sScriptName": "getRollingStoneHelp.py",
        "sSystem": "one FAQ page, plus the fulfilment host tried by name",
        "sFolder": "RollingStoneHelp",
        "sLogName": "getRollingStoneHelp.log",
        "sZipName": "RollingStoneHelp.zip",
        "iMaxPages": 60,
        "nDelay": 1.5,
        "sSeeds": ('"https://www.rollingstone.com/faq/",\n'
                   '              "https://w1.buysub.com/pubs/BA/RST/RST_FAQ.jsp?cds_mag_code=RST",\n'
                   '              "https://w1.buysub.com/pubs/BA/RST/FAQ_new.jsp?cds_mag_code=RST",\n'
                   '              "https://w1.buysub.com/pubs/BA/RST/contact_cs_conf.jsp?cds_mag_code=RST",\n'
                   '              "https://w1.buysub.com/pubs/BA/RST/Sitemap.jsp?cds_mag_code=RST"'),
        "sFencePattern": r"^https://(www\.rollingstone\.com/faq/?$|w1\.buysub\.com/pubs/[A-Z0-9]{1,3}/RST/(?!.*(RegistrationGateway|account_summary|login|signin|cofe_new|payment|renew_)))",
        "sSubjectPattern": "",
        "sReadyPattern": r"(frequently asked|faq|subscription|customer (service|care))",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Rolling Stone, second run",
        "sScriptName": "getRollingStoneHelp2.py",
        "sSystem": "one FAQ page, asked more patiently",
        "sFolder": "RollingStoneHelp",
        "sLogName": "getRollingStoneHelp2.log",
        "sZipName": "RollingStoneHelp2.zip",
        "iMaxPages": 60,
        "nDelay": 4.0,
        "sSeeds": ('"https://www.rollingstone.com/faq",\n'
                   '              "https://www.rollingstone.com/faq/",\n'
                   '              "https://rollingstone.com/faq/",\n'
                   '              "https://www.rollingstone.com/subscribe-faq/",\n'
                   '              "https://w1.buysub.com/pubs/BA/RST/RST_FAQ2.jsp?cds_mag_code=RST"'),
        "sFencePattern": r"^https://((www\.)?rollingstone\.com/(faq|subscribe-faq)/?$|w1\.buysub\.com/pubs/[A-Z0-9]{1,3}/RST/(?!.*(RegistrationGateway|account_summary|login|signin|cofe_new|payment|renew_)))",
        "sSubjectPattern": "",
        "sReadyPattern": r"(frequently asked|faq|subscription|customer (service|care))",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Udemy",
        "sScriptName": "getUdemyHelp.py",
        "sSystem": "Zendesk, by the listing route",
        "sFolder": "UdemyHelp",
        "sLogName": "getUdemyHelp.log",
        "sZipName": "UdemyHelp.zip",
        "iMaxPages": 1200,
        "nDelay": 1.0,
        "sSeeds": ('"https://support.udemy.com/api/v2/help_center/en-us/articles.json?per_page=100",\n'
                   '              "https://support.udemy.com/api/v2/help_center/en-us/categories.json?per_page=100",\n'
                   '              "https://support.udemy.com/api/v2/help_center/en-us/sections.json?per_page=100",\n'
                   '              "https://support.udemy.com/hc/en-us"'),
        "sFencePattern": r"^https://support\.udemy\.com/(hc/en-us|api/v2/help_center/en-us)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(hc/en-us/articles/|help center|articles.:)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": ('    if sText.lstrip().startswith("{"):\n'
                        '        try:\n'
                        '            dPayload = json.loads(sText)\n'
                        '            if dPayload.get("next_page"): lFound.append(dPayload["next_page"])\n'
                        '        except Exception as oError:\n'
                        '            logging.warning("a listing page was not readable as JSON: %s", oError)\n'),
    },
    {
        "sProduct": "Khan Academy",
        "sScriptName": "getKhanAcademyHelp.py",
        "sSystem": "Zendesk, by the listing route",
        "sFolder": "KhanAcademyHelp",
        "sLogName": "getKhanAcademyHelp.log",
        "sZipName": "KhanAcademyHelp.zip",
        "iMaxPages": 1200,
        "nDelay": 1.0,
        "sSeeds": ('"https://support.khanacademy.org/api/v2/help_center/en-us/articles.json?per_page=100",\n'
                   '              "https://support.khanacademy.org/api/v2/help_center/en-us/categories.json?per_page=100",\n'
                   '              "https://support.khanacademy.org/api/v2/help_center/en-us/sections.json?per_page=100",\n'
                   '              "https://support.khanacademy.org/hc/en-us"'),
        "sFencePattern": r"^https://support\.khanacademy\.org/(hc/en-us(?!/community)|api/v2/help_center/en-us)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(hc/en-us/articles/|help center|articles.:)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": ('    if sText.lstrip().startswith("{"):\n'
                        '        try:\n'
                        '            dPayload = json.loads(sText)\n'
                        '            if dPayload.get("next_page"): lFound.append(dPayload["next_page"])\n'
                        '        except Exception as oError:\n'
                        '            logging.warning("a listing page was not readable as JSON: %s", oError)\n'),
    },
{
        "sProduct": "Rolling Stone, third run",
        "sScriptName": "getRollingStoneHelp3.py",
        "sSystem": "four named FAQ pages found by their own titles",
        "sFolder": "RollingStoneHelp",
        "sLogName": "getRollingStoneHelp3.log",
        "sZipName": "RollingStoneHelp3.zip",
        "iMaxPages": 60,
        "nDelay": 3.0,
        "sSeeds": ('"https://www.rollingstone.com/customer-service-subscriptions/",\n'
                   '              "https://www.rollingstone.com/digital-subscription-faq/",\n'
                   '              "https://www.rollingstone.com/app-faq/",\n'
                   '              "https://www.rollingstone.com/charts-faq/",\n'
                   '              "https://www.rollingstone.com/contact/"'),
        "sFencePattern": r"^https://(www\.)?rollingstone\.com/(customer-service-subscriptions|digital-subscription-faq|app-faq|charts-faq|contact)/?$",
        "sSubjectPattern": "",
        "sReadyPattern": r"(subscription|faq|customer service|rolling stone)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Airbnb",
        "sScriptName": "getAirbnbHelp.py",
        "sSystem": "the publisher's own help articles, numbered",
        "sFolder": "AirbnbHelp",
        "sLogName": "getAirbnbHelp.log",
        "sZipName": "AirbnbHelp.zip",
        "iMaxPages": 1500,
        "nDelay": 1.5,
        "sSeeds": ('"https://www.airbnb.com/help",\n'
                   '              "https://www.airbnb.com/help/home",\n'
                   '              "https://www.airbnb.com/help/article/832",\n'
                   '              "https://www.airbnb.com/help/article/1319"'),
        "sFencePattern": r"^https://www\.airbnb\.com/help(/|$)(?!.*(/contact|/feedback))",
        "sSubjectPattern": "",
        "sReadyPattern": r"(airbnb|help center|host|reservation)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "T-Mobile",
        "sScriptName": "getTMobileHelp.py",
        "sSystem": "the publisher's own support tree",
        "sFolder": "TMobileHelp",
        "sLogName": "getTMobileHelp.log",
        "sZipName": "TMobileHelp.zip",
        "iMaxPages": 1200,
        "nDelay": 1.5,
        "sSeeds": ('"https://www.t-mobile.com/support",\n'
                   '              "https://www.t-mobile.com/support/phones-tablets-devices",\n'
                   '              "https://www.t-mobile.com/support/plans-features",\n'
                   '              "https://www.t-mobile.com/support/account/accessibility-support"'),
        "sFencePattern": r"^https://www\.t-mobile\.com/support(/|$)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(t-mobile|support|account|device)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Verizon",
        "sScriptName": "getVerizonHelp.py",
        "sSystem": "the publisher's own support tree",
        "sFolder": "VerizonHelp",
        "sLogName": "getVerizonHelp.log",
        "sZipName": "VerizonHelp.zip",
        "iMaxPages": 1200,
        "nDelay": 1.5,
        "sSeeds": ('"https://www.verizon.com/support/",\n'
                   '              "https://www.verizon.com/about/accessibility"'),
        "sFencePattern": r"^https://www\.verizon\.com/(support/|about/accessibility)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(verizon|support|account|device)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "AT&T",
        "sScriptName": "getAttHelp.py",
        "sSystem": "the publisher's own support tree",
        "sFolder": "AttHelp",
        "sLogName": "getAttHelp.log",
        "sZipName": "AttHelp.zip",
        "iMaxPages": 800,
        "nDelay": 1.5,
        "sSeeds": ('"https://www.att.com/support/",\n'
                   '              "https://www.att.com/support/wireless/",\n'
                   '              "https://www.att.com/support/article/wireless/KM1008618/"'),
        "sFencePattern": r"^https://www\.att\.com/support(/|$)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(at&t|att|support|wireless)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Internet Archive",
        "sScriptName": "getArchiveHelp.py",
        "sSystem": "the publisher's own help site, listing tried first",
        "sFolder": "ArchiveHelp",
        "sLogName": "getArchiveHelp.log",
        "sZipName": "ArchiveHelp.zip",
        "iMaxPages": 800,
        "nDelay": 1.5,
        "sSeeds": ('"https://help.archive.org/",\n'
                   '              "https://help.archive.org/hc/en-us",\n'
                   '              "https://help.archive.org/api/v2/help_center/en-us/articles.json?per_page=100",\n'
                   '              "https://help.archive.org/help/"'),
        "sFencePattern": r"^https://help\.archive\.org/(?!.*(wp-json|/feed/?$|/comment))",
        "sSubjectPattern": "",
        "sReadyPattern": r"(archive|help|wayback|item)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": ('    if sText.lstrip().startswith("{"):\n'
                        '        try:\n'
                        '            dPayload = json.loads(sText)\n'
                        '            if dPayload.get("next_page"): lFound.append(dPayload["next_page"])\n'
                        '        except Exception as oError:\n'
                        '            logging.warning("a listing page was not readable as JSON: %s", oError)\n'),
    },
    {
        "sProduct": "shopDisney",
        "sScriptName": "getShopDisneyHelp.py",
        "sSystem": "one customer service page and what it links to",
        "sFolder": "ShopDisneyHelp",
        "sLogName": "getShopDisneyHelp.log",
        "sZipName": "ShopDisneyHelp.zip",
        "iMaxPages": 120,
        "nDelay": 2.0,
        "sSeeds": ('"https://www.shopdisney.com/faq",\n'
                   '              "https://www.shopdisney.com/customer-service"'),
        "sFencePattern": r"^https://www\.shopdisney\.com/(faq|customer-service|help|shipping|returns|order)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(shopdisney|order|shipping|return|disney)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Airbnb, second run",
        "sScriptName": "getAirbnbHelp2.py",
        "sSystem": "the publisher's own help articles, resuming",
        "sFolder": "AirbnbHelp",
        "sLogName": "getAirbnbHelp2.log",
        "sZipName": "AirbnbHelp2.zip",
        "iMaxPages": 2600,
        "nDelay": 1.5,
        "sSeeds": ('"https://www.airbnb.com/help",\n'
                   '              "https://www.airbnb.com/help/home",\n'
                   '              "https://www.airbnb.com/help/article/832"'),
        "sFencePattern": r"^https://www\.airbnb\.com/help(/|$)(?!.*(/contact|/feedback))",
        "sSubjectPattern": "",
        "sReadyPattern": r"(airbnb|help center|host|reservation)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Verizon, second run",
        "sScriptName": "getVerizonHelp2.py",
        "sSystem": "the publisher's own support tree, resuming",
        "sFolder": "VerizonHelp",
        "sLogName": "getVerizonHelp2.log",
        "sZipName": "VerizonHelp2.zip",
        "iMaxPages": 3500,
        "nDelay": 1.5,
        "sSeeds": ('"https://www.verizon.com/support/",\n'
                   '              "https://www.verizon.com/about/accessibility"'),
        "sFencePattern": r"^https://www\.verizon\.com/(support/|about/accessibility)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(verizon|support|account|device)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Handshake",
        "sScriptName": "getHandshakeHelp.py",
        "sSystem": "Zendesk, by the listing route",
        "sFolder": "HandshakeHelp",
        "sLogName": "getHandshakeHelp.log",
        "sZipName": "HandshakeHelp.zip",
        "iMaxPages": 1500,
        "nDelay": 1.0,
        "sSeeds": ('"https://support.joinhandshake.com/api/v2/help_center/en-us/articles.json?per_page=100",\n'
                   '              "https://support.joinhandshake.com/api/v2/help_center/en-us/categories.json?per_page=100",\n'
                   '              "https://support.joinhandshake.com/api/v2/help_center/en-us/sections.json?per_page=100",\n'
                   '              "https://support.joinhandshake.com/hc/en-us"'),
        "sFencePattern": r"^https://support\.joinhandshake\.com/(hc/en-us(?!/community)|api/v2/help_center/en-us)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(hc/en-us/articles/|help center|articles.:)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": ('    if sText.lstrip().startswith("{"):\n'
                        '        try:\n'
                        '            dPayload = json.loads(sText)\n'
                        '            if dPayload.get("next_page"): lFound.append(dPayload["next_page"])\n'
                        '        except Exception as oError:\n'
                        '            logging.warning("a listing page was not readable as JSON: %s", oError)\n'),
    },
    {
        "sProduct": "CNBC",
        "sScriptName": "getCnbcHelp.py",
        "sSystem": "Zendesk, by the listing route",
        "sFolder": "CnbcHelp",
        "sLogName": "getCnbcHelp.log",
        "sZipName": "CnbcHelp.zip",
        "iMaxPages": 1200,
        "nDelay": 1.0,
        "sSeeds": ('"https://cnbc.zendesk.com/api/v2/help_center/en-us/articles.json?per_page=100",\n'
                   '              "https://cnbc.zendesk.com/api/v2/help_center/en-us/categories.json?per_page=100",\n'
                   '              "https://cnbc.zendesk.com/api/v2/help_center/en-us/sections.json?per_page=100",\n'
                   '              "https://cnbc.zendesk.com/hc/en-us"'),
        "sFencePattern": r"^https://cnbc\.zendesk\.com/(hc/en-us(?!/community)|api/v2/help_center/en-us)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(hc/en-us/articles/|help center|articles.:)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": ('    if sText.lstrip().startswith("{"):\n'
                        '        try:\n'
                        '            dPayload = json.loads(sText)\n'
                        '            if dPayload.get("next_page"): lFound.append(dPayload["next_page"])\n'
                        '        except Exception as oError:\n'
                        '            logging.warning("a listing page was not readable as JSON: %s", oError)\n'),
    },
    {
        "sProduct": "CQ Roll Call",
        "sScriptName": "getCqRollCallHelp.py",
        "sSystem": "Zendesk, by the listing route",
        "sFolder": "CqRollCallHelp",
        "sLogName": "getCqRollCallHelp.log",
        "sZipName": "CqRollCallHelp.zip",
        "iMaxPages": 1200,
        "nDelay": 1.0,
        "sSeeds": ('"https://cqhelp.zendesk.com/api/v2/help_center/en-us/articles.json?per_page=100",\n'
                   '              "https://cqhelp.zendesk.com/api/v2/help_center/en-us/categories.json?per_page=100",\n'
                   '              "https://cqhelp.zendesk.com/api/v2/help_center/en-us/sections.json?per_page=100",\n'
                   '              "https://cqhelp.zendesk.com/hc/en-us"'),
        "sFencePattern": r"^https://cqhelp\.zendesk\.com/(hc/en-us(?!/community)|api/v2/help_center/en-us)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(hc/en-us/articles/|help center|articles.:)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": ('    if sText.lstrip().startswith("{"):\n'
                        '        try:\n'
                        '            dPayload = json.loads(sText)\n'
                        '            if dPayload.get("next_page"): lFound.append(dPayload["next_page"])\n'
                        '        except Exception as oError:\n'
                        '            logging.warning("a listing page was not readable as JSON: %s", oError)\n'),
    },
    {
        "sProduct": "Publication FAQs",
        "sScriptName": "getPublicationFaqs.py",
        "sSystem": "six named pages on five hosts",
        "sFolder": "PublicationFaqs",
        "sLogName": "getPublicationFaqs.log",
        "sZipName": "PublicationFaqs.zip",
        "iMaxPages": 60,
        "nDelay": 2.5,
        "sSeeds": ('"https://www.newyorker.com/about/faq",\n'
                   '              "https://www.wired.com/about/faq/",\n'
                   '              "https://w1.buysub.com/pubs/HR/ESQ/ESQ_FAQ.jsp?cds_mag_code=ESQ",\n'
                   '              "https://help.usatoday.com/",\n'
                   '              "https://www.macworld.com/faq",\n'
                   '              "https://www.pcworld.com/faq",\n'
                   '              "https://w1.buysub.com/pubs/N3/WIR/FAQ_new.jsp?cds_mag_code=WIR",\n'
                   '              "https://w1.buysub.com/pubs/N3/NYR/FAQ_new.jsp?cds_mag_code=NYR"'),
        "sFencePattern": r"^https://(www\.newyorker\.com/about/faq|www\.wired\.com/about/faq|help\.usatoday\.com/|www\.(macworld|pcworld)\.com/faq|w1\.buysub\.com/pubs/[A-Z0-9]{1,3}/(ESQ|WIR|NYR)/)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(frequently asked|faq|subscription|customer (service|care))",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Google Meet",
        "sScriptName": "getGoogleMeetHelp.py",
        "sSystem": "Google's own help centre",
        "sFolder": "GoogleMeetHelp",
        "sLogName": "getGoogleMeetHelp.log",
        "sZipName": "GoogleMeetHelp.zip",
        "iMaxPages": 900,
        "nDelay": 1.5,
        "sSeeds": ('"https://support.google.com/meet/?hl=en",\n'
                   '              "https://support.google.com/meet/answer/7317473?hl=en",\n'
                   '              "https://support.google.com/meet/topic/7306097?hl=en",\n'
                   '              "https://support.google.com/meet/answer/9302870?hl=en"'),
        "sFencePattern": r"^https://support\.google\.com/meet/(answer|topic)?",
        "sSubjectPattern": "",
        "sReadyPattern": r"(meet|google|meeting)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "IFTTT",
        "sScriptName": "getIftttHelp.py",
        "sSystem": "Zendesk, by the listing route",
        "sFolder": "IftttHelp",
        "sLogName": "getIftttHelp.log",
        "sZipName": "IftttHelp.zip",
        "iMaxPages": 600,
        "nDelay": 1.0,
        "sSeeds": ('"https://help.ifttt.com/api/v2/help_center/en-us/articles.json?per_page=100",\n'
                   '              "https://help.ifttt.com/api/v2/help_center/en-us/categories.json?per_page=100",\n'
                   '              "https://help.ifttt.com/api/v2/help_center/en-us/sections.json?per_page=100",\n'
                   '              "https://help.ifttt.com/hc/en-us"'),
        "sFencePattern": r"^https://help\.ifttt\.com/(hc/en-us(?!/community)|api/v2/help_center/en-us)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(hc/en-us/articles/|help center|articles.:)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": ('    if sText.lstrip().startswith("{"):\n'
                        '        try:\n'
                        '            dPayload = json.loads(sText)\n'
                        '            if dPayload.get("next_page"): lFound.append(dPayload["next_page"])\n'
                        '        except Exception as oError:\n'
                        '            logging.warning("a listing page was not readable as JSON: %s", oError)\n'),
    },
    {
        "sProduct": "Zapier",
        "sScriptName": "getZapierHelp.py",
        "sSystem": "Zendesk, by the listing route",
        "sFolder": "ZapierHelp",
        "sLogName": "getZapierHelp.log",
        "sZipName": "ZapierHelp.zip",
        "iMaxPages": 2000,
        "nDelay": 1.0,
        "sSeeds": ('"https://help.zapier.com/api/v2/help_center/en-us/articles.json?per_page=100",\n'
                   '              "https://help.zapier.com/api/v2/help_center/en-us/categories.json?per_page=100",\n'
                   '              "https://help.zapier.com/api/v2/help_center/en-us/sections.json?per_page=100",\n'
                   '              "https://help.zapier.com/hc/en-us"'),
        "sFencePattern": r"^https://help\.zapier\.com/(hc/en-us(?!/community)|api/v2/help_center/en-us)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(hc/en-us/articles/|help center|articles.:)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": ('    if sText.lstrip().startswith("{"):\n'
                        '        try:\n'
                        '            dPayload = json.loads(sText)\n'
                        '            if dPayload.get("next_page"): lFound.append(dPayload["next_page"])\n'
                        '        except Exception as oError:\n'
                        '            logging.warning("a listing page was not readable as JSON: %s", oError)\n'),
    },
    {
        "sProduct": "Todoist",
        "sScriptName": "getTodoistHelp.py",
        "sSystem": "the publisher's own help site",
        "sFolder": "TodoistHelp",
        "sLogName": "getTodoistHelp.log",
        "sZipName": "TodoistHelp.zip",
        "iMaxPages": 800,
        "nDelay": 1.5,
        "sSeeds": ('"https://www.todoist.com/help",\n'
                   '              "https://www.todoist.com/help/articles"'),
        "sFencePattern": r"^https://www\.todoist\.com/help(/|$)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(todoist|task|project|help)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Microsoft To Do",
        "sScriptName": "getMicrosoftToDoHelp.py",
        "sSystem": "Microsoft's own support pages",
        "sFolder": "MicrosoftToDoHelp",
        "sLogName": "getMicrosoftToDoHelp.log",
        "sZipName": "MicrosoftToDoHelp.zip",
        "iMaxPages": 300,
        "nDelay": 1.5,
        "sSeeds": ('"https://support.microsoft.com/en-us/todo",\n'
                   '              "https://support.microsoft.com/en-us/office/microsoft-to-do-help"'),
        "sFencePattern": r"^https://support\.microsoft\.com/en-us/(todo|office/)",
        "sSubjectPattern": r"(to do|to-do|todo|task)",
        "sReadyPattern": r"(to do|task|microsoft)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "mpv",
        "sScriptName": "getMpvHelp.py",
        "sSystem": "the project's own reference manual",
        "sFolder": "MpvHelp",
        "sLogName": "getMpvHelp.log",
        "sZipName": "MpvHelp.zip",
        "iMaxPages": 40,
        "nDelay": 1.5,
        "sSeeds": ('"https://mpv.io/manual/stable/",\n'
                   '              "https://mpv.io/faq/",\n'
                   '              "https://mpv.io/installation/"'),
        "sFencePattern": r"^https://mpv\.io/(manual/stable|faq|installation)(/|$)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(mpv|player|option|playback)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Windows Media Player",
        "sScriptName": "getWindowsMediaPlayerHelp.py",
        "sSystem": "Microsoft's own support pages, held to the player by a subject gate",
        "sFolder": "WindowsMediaPlayerHelp",
        "sLogName": "getWindowsMediaPlayerHelp.log",
        "sZipName": "WindowsMediaPlayerHelp.zip",
        "iMaxPages": 300,
        "nDelay": 1.5,
        "sSeeds": ('"https://support.microsoft.com/en-us/windows/windows-media-player-d10303a5-896c-2ce2-53d4-5bd5b9fd888b",\n'
                   '              "https://support.microsoft.com/en-us/windows/media-player-in-windows-11-4a4a3e2a-3f1c-4d5a-8b1e-1a1b1c1d1e1f",\n'
                   '              "https://support.microsoft.com/en-us/windows/getting-started-with-media-player-8c0dcb4b-0d34-4dd1-9d1f-1e6a2f1a8a3a"'),
        "sFencePattern": r"^https://support\.microsoft\.com/en-us/(windows|topic|office)/",
        "sSubjectPattern": r"(media player|windows media|groove music|movies ?& ?tv)",
        "sReadyPattern": r"(media player|windows|microsoft)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Windows Media Player, second run",
        "sScriptName": "getWindowsMediaPlayerHelp2.py",
        "sSystem": "Microsoft's own support pages, seeded from addresses that exist",
        "sFolder": "WindowsMediaPlayerHelp",
        "sLogName": "getWindowsMediaPlayerHelp2.log",
        "sZipName": "WindowsMediaPlayerHelp2.zip",
        "iMaxPages": 300,
        "nDelay": 1.5,
        "sSeeds": ('"https://support.microsoft.com/en-us/windows/help-in-windows-media-player-9b5f941d-466b-0573-d1f5-badff727b557",\n'
                   '              "https://support.microsoft.com/en-us/windows/windows-media-player-d10303a5-896c-2ce2-53d4-5bd5b9fd888b",\n'
                   '              "https://support.microsoft.com/en-us/windows/windows-media-player-on-windows-10-c7d62061-c106-6005-10c9-52bb8df98ef1",\n'
                   '              "https://support.microsoft.com/en-us/windows/apps/windowsmediaplayer/troubleshoot-windows-media-player-errors",\n'
                   '              "https://support.microsoft.com/en-us/topic/resources-for-troubleshooting-issues-in-windows-media-player-e638202d-ecdc-2154-2ea1-d129fc0f63b4",\n'
                   '              "https://support.microsoft.com/en-us/windows/experience/platform-variants/media-feature-pack-for-windows-n"'),
        "sFencePattern": r"^https://support\.microsoft\.com/en-us/(windows|topic)/",
        "sSubjectPattern": r"(media player|windows media|codec|groove music|movies ?& ?tv|media feature pack)",
        "sReadyPattern": r"(media player|windows|microsoft)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "EndNote",
        "sScriptName": "getEndNoteHelp.py",
        "sSystem": "the older online help, built in frames",
        "sFolder": "EndNoteHelp",
        "sLogName": "getEndNoteHelp.log",
        "sZipName": "EndNoteHelp.zip",
        "iMaxPages": 600,
        "nDelay": 1.5,
        "sSeeds": ('"https://www.myendnoteweb.com/help/en_us/ENW/help.htm",\n'
                   '              "https://www.myendnoteweb.com/help/en_us/ENW/hs_toc.htm",\n'
                   '              "https://www.myendnoteweb.com/help/en_us/ENW/hsr_home.htm"'),
        "sFencePattern": r"^https://www\.myendnoteweb\.com/help/en_us/",
        "sSubjectPattern": "",
        "sReadyPattern": r"(endnote|reference|citation|library|help)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Mendeley",
        "sScriptName": "getMendeleyHelp.py",
        "sSystem": "Elsevier's support site",
        "sFolder": "MendeleyHelp",
        "sLogName": "getMendeleyHelp.log",
        "sZipName": "MendeleyHelp.zip",
        "iMaxPages": 600,
        "nDelay": 1.5,
        "sSeeds": ('"https://www.elsevier.support/mendeley",\n'
                   '              "https://www.elsevier.support/mendeley/topics",\n'
                   '              "https://www.mendeley.com/guides"'),
        "sFencePattern": r"^https://(www\.elsevier\.support/mendeley|www\.mendeley\.com/guides)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(mendeley|reference|citation|library)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "MiKTeX",
        "sScriptName": "getMiktexHelp.py",
        "sSystem": "the project's own documentation",
        "sFolder": "MiktexHelp",
        "sLogName": "getMiktexHelp.log",
        "sZipName": "MiktexHelp.zip",
        "iMaxPages": 600,
        "nDelay": 1.5,
        "sSeeds": ('"https://miktex.org/docs",\n'
                   '              "https://docs.miktex.org/manual/",\n'
                   '              "https://miktex.org/faq",\n'
                   '              "https://miktex.org/howto"'),
        "sFencePattern": r"^https://(miktex\.org/(docs|faq|howto|kb)|docs\.miktex\.org/)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(miktex|tex|package|latex)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "TeX Live",
        "sScriptName": "getTexLiveHelp.py",
        "sSystem": "the project's own documentation",
        "sFolder": "TexLiveHelp",
        "sLogName": "getTexLiveHelp.log",
        "sZipName": "TexLiveHelp.zip",
        "iMaxPages": 300,
        "nDelay": 1.5,
        "sSeeds": ('"https://tug.org/texlive/doc.html",\n'
                   '              "https://tug.org/texlive/",\n'
                   '              "https://tug.org/texlive/quickinstall.html"'),
        "sFencePattern": r"^https://tug\.org/texlive/",
        "sSubjectPattern": "",
        "sReadyPattern": r"(tex live|texlive|install|package)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Typst",
        "sScriptName": "getTypstHelp.py",
        "sSystem": "the project's own documentation",
        "sFolder": "TypstHelp",
        "sLogName": "getTypstHelp.log",
        "sZipName": "TypstHelp.zip",
        "iMaxPages": 900,
        "nDelay": 1.5,
        "sSeeds": ('"https://typst.app/docs/",\n'
                   '              "https://typst.app/docs/tutorial/",\n'
                   '              "https://typst.app/docs/reference/"'),
        "sFencePattern": r"^https://typst\.app/docs/",
        "sSubjectPattern": "",
        "sReadyPattern": r"(typst|document|reference|tutorial)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "reveal.js",
        "sScriptName": "getRevealHelp.py",
        "sSystem": "the project's own documentation",
        "sFolder": "RevealHelp",
        "sLogName": "getRevealHelp.log",
        "sZipName": "RevealHelp.zip",
        "iMaxPages": 300,
        "nDelay": 1.5,
        "sSeeds": ('"https://revealjs.com/",\n'
                   '              "https://revealjs.com/installation/",\n'
                   '              "https://revealjs.com/markdown/"'),
        "sFencePattern": r"^https://revealjs\.com/(?!.*(#|/pricing))",
        "sSubjectPattern": "",
        "sReadyPattern": r"(reveal|slide|presentation|markdown)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "WeasyPrint",
        "sScriptName": "getWeasyPrintHelp.py",
        "sSystem": "the project's own documentation",
        "sFolder": "WeasyPrintHelp",
        "sLogName": "getWeasyPrintHelp.log",
        "sZipName": "WeasyPrintHelp.zip",
        "iMaxPages": 300,
        "nDelay": 1.5,
        "sSeeds": ('"https://doc.courtbouillon.org/weasyprint/stable/",\n'
                   '              "https://doc.courtbouillon.org/weasyprint/stable/first_steps.html"'),
        "sFencePattern": r"^https://doc\.courtbouillon\.org/weasyprint/stable/",
        "sSubjectPattern": "",
        "sReadyPattern": r"(weasyprint|pdf|css|document)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Quarto",
        "sScriptName": "getQuartoHelp.py",
        "sSystem": "the project's own documentation",
        "sFolder": "QuartoHelp",
        "sLogName": "getQuartoHelp.log",
        "sZipName": "QuartoHelp.zip",
        "iMaxPages": 1500,
        "nDelay": 1.5,
        "sSeeds": ('"https://quarto.org/docs/guide/",\n'
                   '              "https://quarto.org/docs/get-started/",\n'
                   '              "https://quarto.org/docs/reference/"'),
        "sFencePattern": r"^https://quarto\.org/docs/",
        "sSubjectPattern": "",
        "sReadyPattern": r"(quarto|document|render|markdown)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Calibre",
        "sScriptName": "getCalibreHelp.py",
        "sSystem": "the project's own documentation",
        "sFolder": "CalibreHelp",
        "sLogName": "getCalibreHelp.log",
        "sZipName": "CalibreHelp.zip",
        "iMaxPages": 600,
        "nDelay": 1.5,
        "sSeeds": ('"https://manual.calibre-ebook.com/",\n'
                   '              "https://manual.calibre-ebook.com/gui.html"'),
        "sFencePattern": r"^https://manual\.calibre-ebook\.com/(?!(zh|et|pt|de|fr|es|it|ja|ru|nl|pl|tr|ko|cs|sv|fi|da|nb|uk|hu|ro|sr|sk|bg|el|he|ar|fa|hi|id|vi|th|ca|gl|eu)/)(?!.*(_static|_sources|_modules|generated/|/api))",
        "sSubjectPattern": "",
        "sReadyPattern": r"(calibre|ebook|library|book)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Jupyter",
        "sScriptName": "getJupyterHelp.py",
        "sSystem": "the project's own documentation",
        "sFolder": "JupyterHelp",
        "sLogName": "getJupyterHelp.log",
        "sZipName": "JupyterHelp.zip",
        "iMaxPages": 600,
        "nDelay": 1.5,
        "sSeeds": ('"https://docs.jupyter.org/en/latest/",\n'
                   '              "https://docs.jupyter.org/en/latest/start/index.html"'),
        "sFencePattern": r"^https://docs\.jupyter\.org/en/latest/(?!(contributing|community|projects)/)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(jupyter|notebook|kernel|install)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "TeX Live, second run",
        "sScriptName": "getTexLiveHelp2.py",
        "sSystem": "the project's own documentation, fenced away from the archive",
        "sFolder": "TexLiveHelp2",
        "sLogName": "getTexLiveHelp2.log",
        "sZipName": "TexLiveHelp2.zip",
        "iMaxPages": 300,
        "nDelay": 1.5,
        "sSeeds": ('"https://tug.org/texlive/doc.html",\n'
                   '              "https://tug.org/texlive/",\n'
                   '              "https://tug.org/texlive/quickinstall.html",\n'
                   '              "https://tug.org/texlive/windows.html",\n'
                   '              "https://tug.org/texlive/upgrade.html"'),
        "sFencePattern": r"^https://tug\.org/texlive/([a-z0-9-]*\.html)?$",
        "sSubjectPattern": "",
        "sReadyPattern": r"(tex live|texlive|install|package)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Stack Overflow and Stack Exchange",
        "sScriptName": "getStackHelp.py",
        "sSystem": "the network's shared help centre, on both hosts",
        "sFolder": "StackHelp",
        "sLogName": "getStackHelp.log",
        "sZipName": "StackHelp.zip",
        "iMaxPages": 600,
        "nDelay": 2.0,
        "sSeeds": ('"https://stackoverflow.com/help",\n'
                   '              "https://stackoverflow.com/help/asking",\n'
                   '              "https://stackoverflow.com/help/whats-reputation",\n'
                   '              "https://stackoverflow.com/help/privileges"'),
        "sFencePattern": r"^https://stackoverflow\.com/help(/|$)(?!badges)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(help center|stack|question|answer|reputation)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "MediaWiki",
        "sScriptName": "getMediaWikiHelp.py",
        "sSystem": "the project's own documentation",
        "sFolder": "MediaWikiHelp",
        "sLogName": "getMediaWikiHelp.log",
        "sZipName": "MediaWikiHelp.zip",
        "iMaxPages": 400,
        "nDelay": 1.5,
        "sSeeds": ('"https://www.mediawiki.org/wiki/Help:Contents",\n'
                   '              "https://www.mediawiki.org/wiki/Help:Formatting",\n'
                   '              "https://www.mediawiki.org/wiki/Help:Editing_pages"'),
        "sFencePattern": r"^https://www\.mediawiki\.org/wiki/Help:(?!.*(/|Special:))",
        "sSubjectPattern": "",
        "sReadyPattern": r"(mediawiki|wiki|page|edit)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Org mode",
        "sScriptName": "getOrgModeHelp.py",
        "sSystem": "the project's own documentation",
        "sFolder": "OrgModeHelp",
        "sLogName": "getOrgModeHelp.log",
        "sZipName": "OrgModeHelp.zip",
        "iMaxPages": 500,
        "nDelay": 1.5,
        "sSeeds": ('"https://orgmode.org/manual/",\n'
                   '              "https://orgmode.org/guide/",\n'
                   '              "https://orgmode.org/features.html"'),
        "sFencePattern": r"^https://orgmode\.org/(manual|guide|features\.html|quickstart\.html)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(org|emacs|document|outline)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Typora",
        "sScriptName": "getTyporaHelp.py",
        "sSystem": "the project's own documentation",
        "sFolder": "TyporaHelp",
        "sLogName": "getTyporaHelp.log",
        "sZipName": "TyporaHelp.zip",
        "iMaxPages": 300,
        "nDelay": 1.5,
        "sSeeds": ('"https://support.typora.io/",\n'
                   '              "https://support.typora.io/Markdown-Reference/"'),
        "sFencePattern": r"^https://support\.typora\.io/",
        "sSubjectPattern": "",
        "sReadyPattern": r"(typora|markdown|document|export)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Zettlr",
        "sScriptName": "getZettlrHelp.py",
        "sSystem": "the project's own documentation",
        "sFolder": "ZettlrHelp",
        "sLogName": "getZettlrHelp.log",
        "sZipName": "ZettlrHelp.zip",
        "iMaxPages": 300,
        "nDelay": 1.5,
        "sSeeds": ('"https://docs.zettlr.com/en/",\n'
                   '              "https://docs.zettlr.com/en/getting-started/"'),
        "sFencePattern": r"^https://docs\.zettlr\.com/en/",
        "sSubjectPattern": "",
        "sReadyPattern": r"(zettlr|markdown|document|project)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Mermaid",
        "sScriptName": "getMermaidHelp.py",
        "sSystem": "the project's own documentation",
        "sFolder": "MermaidHelp",
        "sLogName": "getMermaidHelp.log",
        "sZipName": "MermaidHelp.zip",
        "iMaxPages": 400,
        "nDelay": 1.5,
        "sSeeds": ('"https://mermaid.js.org/intro/",\n'
                   '              "https://mermaid.js.org/syntax/flowchart.html",\n'
                   '              "https://mermaid.js.org/ecosystem/tutorials.html"'),
        "sFencePattern": r"^https://mermaid\.js\.org/(?!(config|community)/)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(mermaid|diagram|chart|syntax)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Craigslist",
        "sScriptName": "getCraigslistHelp.py",
        "sSystem": "the site's own help pages",
        "sFolder": "CraigslistHelp",
        "sLogName": "getCraigslistHelp.log",
        "sZipName": "CraigslistHelp.zip",
        "iMaxPages": 400,
        "nDelay": 2.0,
        "sSeeds": ('"https://www.craigslist.org/about/help/",\n'
                   '              "https://www.craigslist.org/about/scams",\n'
                   '              "https://www.craigslist.org/about/safety",\n'
                   '              "https://www.craigslist.org/about/prohibited",\n'
                   '              "https://www.craigslist.org/about/help/posting"'),
        "sFencePattern": r"^https://www\.craigslist\.org/about/(help|scams|safety|prohibited|charges|classified|craigslist_is_hiring|terms)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(craigslist|posting|account|help|scam)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "TaskRabbit",
        "sScriptName": "getTaskRabbitHelp.py",
        "sSystem": "Zendesk, by the listing route",
        "sFolder": "TaskRabbitHelp",
        "sLogName": "getTaskRabbitHelp.log",
        "sZipName": "TaskRabbitHelp.zip",
        "iMaxPages": 600,
        "nDelay": 1.0,
        "sSeeds": ('"https://support.taskrabbit.com/api/v2/help_center/en-us/articles.json?per_page=100",\n'
                   '              "https://support.taskrabbit.com/api/v2/help_center/en-us/categories.json?per_page=100",\n'
                   '              "https://support.taskrabbit.com/api/v2/help_center/en-us/sections.json?per_page=100",\n'
                   '              "https://support.taskrabbit.com/hc/en-us"'),
        "sFencePattern": r"^https://support\.taskrabbit\.com/(hc/en-us(?!/community)|api/v2/help_center/en-us)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(hc/en-us/articles/|help center|articles.:)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": ('    if sText.lstrip().startswith("{"):\n'
                        '        try:\n'
                        '            dPayload = json.loads(sText)\n'
                        '            if dPayload.get("next_page"): lFound.append(dPayload["next_page"])\n'
                        '        except Exception as oError:\n'
                        '            logging.warning("a listing page was not readable as JSON: %s", oError)\n'),
    },
    {
        "sProduct": "Angi",
        "sScriptName": "getAngiHelp.py",
        "sSystem": "the one page of theirs that answers, and what it links to",
        "sFolder": "AngiHelp",
        "sLogName": "getAngiHelp.log",
        "sZipName": "AngiHelp.zip",
        "iMaxPages": 200,
        "nDelay": 2.0,
        "sSeeds": ('"https://www.angi.com/faq.htm",\n'
                   '              "https://www.angi.com/membership.htm",\n'
                   '              "https://www.angi.com/about.htm"'),
        "sFencePattern": r"^https://www\.angi\.com/(faq|membership|aboutus|about\.htm|company/|terms|privacy)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(angi|angie|member|pro|review|question)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Mermaid accessibility page",
        "sScriptName": "getMermaidHelp2.py",
        "sSystem": "the one page the first fence wrongly refused",
        "sFolder": "MermaidHelp",
        "sLogName": "getMermaidHelp2.log",
        "sZipName": "MermaidHelp2.zip",
        "iMaxPages": 20,
        "nDelay": 1.5,
        "sSeeds": ('"https://mermaid.js.org/config/accessibility.html",\n'
                   '              "https://mermaid.js.org/config/theming.html",\n'
                   '              "https://mermaid.js.org/config/usage.html"'),
        "sFencePattern": r"^https://mermaid\.js\.org/config/(accessibility|theming|usage|math|img-size|directives)\.html$",
        "sSubjectPattern": "",
        "sReadyPattern": r"(mermaid|diagram|accessib|theme)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "NVDA user guide",
        "sScriptName": "getNvdaUserGuide.py",
        "sSystem": "NV Access's own documentation",
        "sFolder": "NvdaHelp",
        "sLogName": "getNvdaUserGuide.log",
        "sZipName": "NvdaHelp.zip",
        "iMaxPages": 40,
        "nDelay": 1.5,
        "sSeeds": ('"https://download.nvaccess.org/documentation/userGuide.html",\n'
                   '              "https://download.nvaccess.org/documentation/keyCommands.html",\n'
                   '              "https://download.nvaccess.org/documentation/changes.html"'),
        "sFencePattern": r"^https://download\.nvaccess\.org/documentation/(userGuide|keyCommands|changes)\.html$",
        "sSubjectPattern": "",
        "sReadyPattern": r"(nvda|screen reader|nv access)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "NVDA developer documentation",
        "sScriptName": "getNvdaDeveloperDocs.py",
        "sSystem": "NV Access's developer guide, and the add-on guide if it answers",
        "sFolder": "NvdaDevHelp",
        "sLogName": "getNvdaDeveloperDocs.log",
        "sZipName": "NvdaDevHelp.zip",
        "iMaxPages": 120,
        "nDelay": 1.5,
        "sSeeds": ('"https://download.nvaccess.org/documentation/developerGuide.html",\n'
                   '              "https://addonteam.github.io/DevGuide/",\n'
                   '              "https://addonteam.github.io/DevGuide/dev-guide.html",\n'
                   '              "https://github.com/nvdaaddons/DevGuide/blob/master/dev-guide.md",\n'
                   '              "https://www.nvaccess.org/files/nvda/documentation/developerGuide.html"'),
        "sFencePattern": r"^https://(download\.nvaccess\.org/documentation/developerGuide\.html|www\.nvaccess\.org/files/nvda/documentation/developerGuide\.html|addonteam\.github\.io/DevGuide|github\.com/nvdaaddons/DevGuide)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(nvda|add-?on|plugin|developer)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "NVDA add-on development guide",
        "sScriptName": "getNvdaAddonGuide.py",
        "sSystem": "the add-on team's wiki, where the guide actually lives",
        "sFolder": "NvdaDevHelp",
        "sLogName": "getNvdaAddonGuide.log",
        "sZipName": "NvdaAddonHelp.zip",
        "iMaxPages": 120,
        "nDelay": 1.5,
        "sSeeds": ('"https://github.com/nvdaaddons/DevGuide/wiki/NVDA-Add-on-Development-Guide",\n'
                   '              "https://github.com/nvdaaddons/DevGuide/wiki",\n'
                   '              "https://addons.nvda-project.org/devDocs/devDocs.en.html"'),
        "sFencePattern": r"^https://(github\.com/nvdaaddons/DevGuide/wiki(?!.*(/_|_history|/[0-9a-f]{40}))|addons\.nvda-project\.org/devDocs/)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(add-?on|nvda|plugin|guide)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Windows Narrator",
        "sScriptName": "getNarratorHelp.py",
        "sSystem": "Microsoft's complete guide to Narrator",
        "sFolder": "NarratorHelp",
        "sLogName": "getNarratorHelp.log",
        "sZipName": "NarratorHelp.zip",
        "iMaxPages": 300,
        "nDelay": 1.5,
        "sSeeds": ('"https://support.microsoft.com/en-us/windows/complete-guide-to-narrator-e4397a0d-ef4f-b386-d8ae-c172f109bdb1",\n'
                   '              "https://support.microsoft.com/en-us/accessibility/windows/narrator/complete-guide-to-narrator",\n'
                   '              "https://support.microsoft.com/en-us/windows/chapter-1-introducing-narrator-af1ad9b1-8e07-1b04-a9b3-b8e60b0c088a",\n'
                   '              "https://support.microsoft.com/en-us/windows/appendix-a-supported-languages-and-voices-4486e345-7730-53da-fcfe-55cc64300f01"'),
        "sFencePattern": r"^https://support\.microsoft\.com/en-us/(windows|accessibility/windows|topic)/",
        "sSubjectPattern": r"(narrator|screen reader|braille|speech|voice access)",
        "sReadyPattern": r"(narrator|windows|microsoft)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Plain language",
        "sScriptName": "getPlainLanguageHelp.py",
        "sSystem": "the United States government's plain-language guidance, at its new home",
        "sFolder": "PlainLanguageHelp",
        "sLogName": "getPlainLanguageHelp.log",
        "sZipName": "PlainLanguageHelp.zip",
        "iMaxPages": 300,
        "nDelay": 1.5,
        "sSeeds": ('"https://digital.gov/guides/plain-language/",\n'
                   '              "https://digital.gov/topics/plain-language/",\n'
                   '              "https://digital.gov/guides/plain-language/write-for-your-audience/",\n'
                   '              "https://digital.gov/guides/plain-language/plain-language-checklist/"'),
        "sFencePattern": r"^https://digital\.gov/(guides/plain-language|topics/plain-language)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(plain language|writing|audience|guideline)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Android accessibility, including Lookout",
        "sScriptName": "getLookoutHelp.py",
        "sSystem": "Google's Android accessibility help centre",
        "sFolder": "LookoutHelp",
        "sLogName": "getLookoutHelp.log",
        "sZipName": "LookoutHelp.zip",
        "iMaxPages": 500,
        "nDelay": 1.5,
        "sSeeds": ('"https://support.google.com/accessibility/android/answer/9031274?hl=en",\n'
                   '              "https://support.google.com/accessibility/android/?hl=en",\n'
                   '              "https://support.google.com/accessibility/android/topic/6007234?hl=en",\n'
                   '              "https://support.google.com/accessibility/android/answer/6283677?hl=en"'),
        "sFencePattern": r"^https://support\.google\.com/accessibility/android/(answer|topic)?",
        "sSubjectPattern": "",
        "sReadyPattern": r"(lookout|talkback|accessibility|android)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "VDScan",
        "sScriptName": "getVdscanHelp.py",
        "sSystem": "the publisher's own site and its help host, whichever answers",
        "sFolder": "VdscanHelp",
        "sLogName": "getVdscanHelp.log",
        "sZipName": "VdscanHelp.zip",
        "iMaxPages": 200,
        "nDelay": 2.0,
        "sSeeds": ('"https://vdscan.app/",\n'
                   '              "https://vdscan.app/help",\n'
                   '              "https://vdscan.app/support",\n'
                   '              "https://www.voicedream.com/support/",\n'
                   '              "https://help.voicedream.com/"'),
        "sFencePattern": r"^https://(vdscan\.app/|(www\.)?voicedream\.com/(support|help)|help\.voicedream\.com/)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(vdscan|voice dream|scan|ocr|reader)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "MakeMKV",
        "sScriptName": "getMakeMkvHelp.py",
        "sSystem": "the publisher's own online help",
        "sFolder": "MakeMkvHelp",
        "sLogName": "getMakeMkvHelp.log",
        "sZipName": "MakeMkvHelp.zip",
        "iMaxPages": 200,
        "nDelay": 2.0,
        "sSeeds": ('"https://www.makemkv.com/onlinehelp/",\n'
                   '              "https://www.makemkv.com/developers/",\n'
                   '              "https://www.makemkv.com/developers/usage.txt",\n'
                   '              "https://www.makemkv.com/faq/"'),
        "sFencePattern": r"^https://www\.makemkv\.com/(onlinehelp|developers|faq)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(makemkv|disc|title|mkv|drive)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Envision",
        "sScriptName": "getEnvisionHelp.py",
        "sSystem": "Zendesk, by the listing route",
        "sFolder": "EnvisionHelp",
        "sLogName": "getEnvisionHelp.log",
        "sZipName": "EnvisionHelp.zip",
        "iMaxPages": 600,
        "nDelay": 1.0,
        "sSeeds": ('"https://support.letsenvision.com/api/v2/help_center/en-us/articles.json?per_page=100",\n'
                   '              "https://support.letsenvision.com/api/v2/help_center/en-us/categories.json?per_page=100",\n'
                   '              "https://support.letsenvision.com/api/v2/help_center/en-us/sections.json?per_page=100",\n'
                   '              "https://support.letsenvision.com/hc/en-us"'),
        "sFencePattern": r"^https://support\.letsenvision\.com/(hc/en-us(?!/community)|api/v2/help_center/en-us)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(hc/en-us/articles/|help center|articles.:)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": ('    if sText.lstrip().startswith("{"):\n'
                        '        try:\n'
                        '            dPayload = json.loads(sText)\n'
                        '            if dPayload.get("next_page"): lFound.append(dPayload["next_page"])\n'
                        '        except Exception as oError:\n'
                        '            logging.warning("a listing page was not readable as JSON: %s", oError)\n'),
    },
    {
        "sProduct": "Suno",
        "sScriptName": "getSunoHelp.py",
        "sSystem": "the publisher's own help site",
        "sFolder": "SunoHelp",
        "sLogName": "getSunoHelp.log",
        "sZipName": "SunoHelp.zip",
        "iMaxPages": 600,
        "nDelay": 1.5,
        "sSeeds": ('"https://help.suno.com/en/",\n'
                   '              "https://help.suno.com/",\n'
                   '              "https://help.suno.com/en/collections",\n'
                   '              "https://help.suno.com/en/articles/2551617"'),
        "sFencePattern": r"^https://help\.suno\.com/(en(/|$)|$)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(suno|song|music|credit|prompt)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Jammable",
        "sScriptName": "getJammableHelp.py",
        "sSystem": "whichever of its help addresses answers",
        "sFolder": "JammableHelp",
        "sLogName": "getJammableHelp.log",
        "sZipName": "JammableHelp.zip",
        "iMaxPages": 400,
        "nDelay": 1.5,
        "sSeeds": ('"https://help.jammable.com/en/",\n'
                   '              "https://help.jammable.com/",\n'
                   '              "https://www.jammable.com/help",\n'
                   '              "https://support.jammable.com/",\n'
                   '              "https://www.jammable.com/faq"'),
        "sFencePattern": r"^https://(help\.jammable\.com/|support\.jammable\.com/|(www\.)?jammable\.com/(help|faq|support))",
        "sSubjectPattern": "",
        "sReadyPattern": r"(jammable|voice|cover|model|song)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "ElevenLabs",
        "sScriptName": "getElevenLabsHelp.py",
        "sSystem": "Zendesk, by the listing route",
        "sFolder": "ElevenLabsHelp",
        "sLogName": "getElevenLabsHelp.log",
        "sZipName": "ElevenLabsHelp.zip",
        "iMaxPages": 800,
        "nDelay": 1.0,
        "sSeeds": ('"https://help.elevenlabs.io/api/v2/help_center/en-us/articles.json?per_page=100",\n'
                   '              "https://help.elevenlabs.io/api/v2/help_center/en-us/categories.json?per_page=100",\n'
                   '              "https://help.elevenlabs.io/api/v2/help_center/en-us/sections.json?per_page=100",\n'
                   '              "https://help.elevenlabs.io/hc/en-us"'),
        "sFencePattern": r"^https://help\.elevenlabs\.io/(hc/en-us(?!/(community|requests))|api/v2/help_center/en-us)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(hc/en-us/articles/|help center|articles.:)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": ('    if sText.lstrip().startswith("{"):\n'
                        '        try:\n'
                        '            dPayload = json.loads(sText)\n'
                        '            if dPayload.get("next_page"): lFound.append(dPayload["next_page"])\n'
                        '        except Exception as oError:\n'
                        '            logging.warning("a listing page was not readable as JSON: %s", oError)\n'),
    },
    {
        "sProduct": "Udio",
        "sScriptName": "getUdioHelp.py",
        "sSystem": "whichever of its help addresses answers",
        "sFolder": "UdioHelp",
        "sLogName": "getUdioHelp.log",
        "sZipName": "UdioHelp.zip",
        "iMaxPages": 400,
        "nDelay": 1.5,
        "sSeeds": ('"https://help.udio.com/en/",\n'
                   '              "https://help.udio.com/",\n'
                   '              "https://support.udio.com/",\n'
                   '              "https://www.udio.com/help",\n'
                   '              "https://udio.com/faq"'),
        "sFencePattern": r"^https://(help\.udio\.com/|support\.udio\.com/|(www\.)?udio\.com/(help|faq|support))",
        "sSubjectPattern": "",
        "sReadyPattern": r"(udio|song|music|credit|prompt)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Bitwarden",
        "sScriptName": "getBitwardenHelp.py",
        "sSystem": "the publisher's own help centre",
        "sFolder": "BitwardenHelp",
        "sLogName": "getBitwardenHelp.log",
        "sZipName": "BitwardenHelp.zip",
        "iMaxPages": 900,
        "nDelay": 1.5,
        "sSeeds": ('"https://bitwarden.com/help/",\n'
                   '              "https://bitwarden.com/help/getting-started-webvault/",\n'
                   '              "https://bitwarden.com/help/password-manager-overview/"'),
        "sFencePattern": r"^https://bitwarden\.com/help/(?!(api|contributing|release-notes|self-host|deploy|install-on|kubernetes|cli|scim|directory-connector|sdk|secrets-manager-cli|public-api))",
        "sSubjectPattern": "",
        "sReadyPattern": r"(bitwarden|vault|password|item|login)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Gmail",
        "sScriptName": "getGmailHelp.py",
        "sSystem": "Google's own help centre",
        "sFolder": "GmailHelp",
        "sLogName": "getGmailHelp.log",
        "sZipName": "GmailHelp.zip",
        "iMaxPages": 900,
        "nDelay": 1.5,
        "sSeeds": ('"https://support.google.com/mail/?hl=en",\n'
                   '              "https://support.google.com/mail/answer/6579?hl=en",\n'
                   '              "https://support.google.com/mail/topic/7065107?hl=en",\n'
                   '              "https://support.google.com/mail/answer/7190?hl=en"'),
        "sFencePattern": r"^https://support\.google\.com/mail/(answer|topic)?",
        "sSubjectPattern": "",
        "sReadyPattern": r"(gmail|mail|inbox|message)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "HumanWare",
        "sScriptName": "getHumanWareHelp.py",
        "sSystem": "the publisher's own support pages and user guides",
        "sFolder": "HumanWareHelp",
        "sLogName": "getHumanWareHelp.log",
        "sZipName": "HumanWareHelp.zip",
        "iMaxPages": 600,
        "nDelay": 1.5,
        "sSeeds": ('"https://support.humanware.com/en-usa/support",\n'
                   '              "https://www.humanware.com/en-usa/support",\n'
                   '              "https://support.humanware.com/en-canada/support/victor_reader_stream_user_guide",\n'
                   '              "https://www.humanware.com/en-usa/support/victor_reader_stream_2/victor_reader_stream_2_faq",\n'
                   '              "https://www.humanware.com/wp-content/uploads/2024/11/Victor-Reader-Stream-User-Guide.html"'),
        "sFencePattern": r"^https://(support\.humanware\.com/en-(usa|canada)/|www\.humanware\.com/(en-usa/support|wp-content/uploads/[0-9]{4}/[0-9]{2}/(?!(AR|DA|NL|DE|ES|IT|PT|SV|NO|FI|PL|JA|ZH|KO|RU)-)[A-Za-z0-9-]+\.html))",
        "sSubjectPattern": "",
        "sReadyPattern": r"(humanware|victor|braille|stream|support)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Remote Incident Manager",
        "sScriptName": "getRimHelp.py",
        "sSystem": "the product's own manual site",
        "sFolder": "RimHelp",
        "sLogName": "getRimHelp.log",
        "sZipName": "RimHelp.zip",
        "iMaxPages": 400,
        "nDelay": 1.5,
        "sSeeds": ('"https://manual.getrim.app/",\n'
                   '              "https://manual.getrim.app/mobile/",\n'
                   '              "https://manual.getrim.app/windows/",\n'
                   '              "https://manual.getrim.app/mac/",\n'
                   '              "https://pneumasolutions.com/remote-incident-manager-rim/"'),
        "sFencePattern": r"^https://(manual\.getrim\.app/|pneumasolutions\.com/remote-incident-manager)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(rim|remote incident|controller|target|session)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Google Forms",
        "sScriptName": "getGoogleFormsHelp.py",
        "sSystem": "Google's editors help centre, held to Forms by a subject gate",
        "sFolder": "GoogleFormsHelp",
        "sLogName": "getGoogleFormsHelp.log",
        "sZipName": "GoogleFormsHelp.zip",
        "iMaxPages": 500,
        "nDelay": 1.5,
        "sSeeds": ('"https://support.google.com/docs/topic/9055404?hl=en",\n'
                   '              "https://support.google.com/docs/answer/6281888?hl=en",\n'
                   '              "https://support.google.com/docs/answer/2839737?hl=en",\n'
                   '              "https://support.google.com/docs/answer/2917686?hl=en"'),
        "sFencePattern": r"^https://support\.google\.com/docs/(answer|topic)?",
        "sSubjectPattern": r"(\bforms?\b|\bquiz|\bsurvey|\bresponses?\b)",
        "sReadyPattern": r"(form|google|docs)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Microsoft Forms",
        "sScriptName": "getMicrosoftFormsHelp.py",
        "sSystem": "Microsoft's support pages, held to Forms by a subject gate",
        "sFolder": "MicrosoftFormsHelp",
        "sLogName": "getMicrosoftFormsHelp.log",
        "sZipName": "MicrosoftFormsHelp.zip",
        "iMaxPages": 400,
        "nDelay": 1.5,
        "sSeeds": ('"https://support.microsoft.com/en-us/forms",\n'
                   '              "https://support.microsoft.com/en-us/office/create-a-form-with-microsoft-forms-4ffb64cc-7d5d-402f-b82e-b1d49418fd9d",\n'
                   '              "https://support.microsoft.com/en-us/office/microsoft-forms-help-and-learning-7145d8e0-f4de-4bd0-a4b7-fbc9d4e8a90f"'),
        "sFencePattern": r"^https://support\.microsoft\.com/en-us/(office|forms|topic)",
        "sSubjectPattern": r"(forms?|quiz|survey|response)",
        "sReadyPattern": r"(forms|microsoft|quiz)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Muse",
        "sScriptName": "getMuseHelp.py",
        "sSystem": "Meta's help centre for Muse, whichever address answers",
        "sFolder": "MuseHelp",
        "sLogName": "getMuseHelp.log",
        "sZipName": "MuseHelp.zip",
        "iMaxPages": 400,
        "nDelay": 1.5,
        "sSeeds": ('"https://help.meta.com/muse/",\n'
                   '              "https://muse.ai/help",\n'
                   '              "https://www.muse.ai/help",\n'
                   '              "https://help.meta.com/",\n'
                   '              "https://muse.ai/faq"'),
        "sFencePattern": r"^https://(help\.meta\.com/|(www\.)?muse\.ai/(help|support|faq))",
        "sSubjectPattern": r"(muse|agent|connector|secure vm|subscription)",
        "sReadyPattern": r"(muse|meta|agent|help)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
{
        "sProduct": "Muse, second run",
        "sScriptName": "getMuseHelp2.py",
        "sSystem": "the Meta Help Center section where Muse actually lives",
        "sFolder": "MuseHelp",
        "sLogName": "getMuseHelp2.log",
        "sZipName": "MuseHelp2.zip",
        "iMaxPages": 400,
        "nDelay": 2.0,
        "sSeeds": ('"https://www.meta.com/help/artificial-intelligence/1687253048996149/",\n'
                   '              "https://www.meta.com/help/artificial-intelligence/1047255454427887/",\n'
                   '              "https://www.meta.com/help/artificial-intelligence/",\n'
                   '              "https://ai.meta.com/muse/"'),
        "sFencePattern": r"^https://(www\.meta\.com/help/artificial-intelligence/|ai\.meta\.com/muse)",
        "sSubjectPattern": r"(muse|agent|connector|virtual machine|subscription|approval)",
        "sReadyPattern": r"(muse|meta|agent|connector)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "BrailleBlaster",
        "sScriptName": "getBrailleBlasterHelp.py",
        "sSystem": "the publisher's own user guide",
        "sFolder": "BrailleBlasterHelp",
        "sLogName": "getBrailleBlasterHelp.log",
        "sZipName": "BrailleBlasterHelp.zip",
        "iMaxPages": 400,
        "nDelay": 1.5,
        "sSeeds": ('"https://brailleblaster.org/userGuide.php",\n'
                   '              "https://www.brailleblaster.org/",\n'
                   '              "https://brailleblaster.org/faq.php"'),
        "sFencePattern": r"^https://(www\.)?brailleblaster\.org/",
        "sSubjectPattern": "",
        "sReadyPattern": r"(braille|blaster|document|translat)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Paperback",
        "sScriptName": "getPaperbackHelp.py",
        "sSystem": "the publisher's own documentation",
        "sFolder": "PaperbackHelp",
        "sLogName": "getPaperbackHelp.log",
        "sZipName": "PaperbackHelp.zip",
        "iMaxPages": 400,
        "nDelay": 1.5,
        "sSeeds": ('"https://paperback.dev/docs/",\n'
                   '              "https://paperback.dev/",\n'
                   '              "https://paperback.dev/help/"'),
        "sFencePattern": r"^https://paperback\.dev/",
        "sSubjectPattern": "",
        "sReadyPattern": r"(paperback|book|read|library)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Hartgen Consultancy",
        "sScriptName": "getHartgenHelp.py",
        "sSystem": "one publisher, three products: J-Say, Leasey and the Zoom scripts",
        "sFolder": "HartgenHelp",
        "sLogName": "getHartgenHelp.log",
        "sZipName": "HartgenHelp.zip",
        "iMaxPages": 400,
        "nDelay": 1.5,
        "sSeeds": ('"https://hartgenconsultancy.com/leaseycentral/",\n'
                   '              "https://hartgenconsultancy.com/j-say/",\n'
                   '              "https://hartgenconsultancy.com/zoom-professional-scripts/",\n'
                   '              "https://hartgenconsultancy.com/support/"'),
        "sFencePattern": r"^https://(www\.)?hartgenconsultancy\.com/(?!(cart|checkout|my-account|product/|shop|basket))",
        "sSubjectPattern": "",
        "sReadyPattern": r"(leasey|j-say|jaws|zoom|script|support)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Get Accessible Apps",
        "sScriptName": "getAccessibleAppsHelp.py",
        "sSystem": "one publisher, two products: CAPTCHA Be Gone and QRead",
        "sFolder": "AccessibleAppsHelp",
        "sLogName": "getAccessibleAppsHelp.log",
        "sZipName": "AccessibleAppsHelp.zip",
        "iMaxPages": 400,
        "nDelay": 1.5,
        "sSeeds": ('"https://getaccessibleapps.com/",\n'
                   '              "https://getaccessibleapps.com/qread/",\n'
                   '              "https://getaccessibleapps.com/captchabegone/",\n'
                   '              "https://getaccessibleapps.com/support/"'),
        "sFencePattern": r"^https://(www\.)?getaccessibleapps\.com/(?!(cart|checkout|my-account|shop))",
        "sSubjectPattern": "",
        "sReadyPattern": r"(qread|captcha|accessible|document|read)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "ACB Link",
        "sScriptName": "getAcbLinkHelp.py",
        "sSystem": "the publisher's own help pages",
        "sFolder": "AcbLinkHelp",
        "sLogName": "getAcbLinkHelp.log",
        "sZipName": "AcbLinkHelp.zip",
        "iMaxPages": 400,
        "nDelay": 1.5,
        "sSeeds": ('"https://link.acb.org/",\n'
                   '              "https://link.acb.org/help",\n'
                   '              "https://link.acb.org/faq",\n'
                   '              "https://www.acb.org/acb-link"'),
        "sFencePattern": r"^https://(link\.acb\.org/|(www\.)?acb\.org/acb-link)",
        "sSubjectPattern": "",
        "sReadyPattern": r"(acb|link|app|stream|event)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "TifloAcosta",
        "sScriptName": "getTifloAcostaHelp.py",
        "sSystem": "the app's own library of guides",
        "sFolder": "TifloAcostaHelp",
        "sLogName": "getTifloAcostaHelp.log",
        "sZipName": "TifloAcostaHelp.zip",
        "iMaxPages": 400,
        "nDelay": 1.5,
        "sSeeds": ('"https://tifloacosta.com/",\n'
                   '              "https://tifloacosta.com/guias",\n'
                   '              "https://tifloacosta.com/en/",\n'
                   '              "https://tifloacosta.com/en/guides"'),
        "sFencePattern": r"^https://(www\.)?tifloacosta\.com/",
        "sSubjectPattern": "",
        "sReadyPattern": r"(tiflo|guia|guide|iphone|voiceover)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Start Testing",
        "sScriptName": "getStartTestingHelp.py",
        "sSystem": "the publisher's own site",
        "sFolder": "StartTestingHelp",
        "sLogName": "getStartTestingHelp.log",
        "sZipName": "StartTestingHelp.zip",
        "iMaxPages": 300,
        "nDelay": 1.5,
        "sSeeds": ('"https://starttesting.net/",\n'
                   '              "https://starttesting.net/help",\n'
                   '              "https://starttesting.net/docs"'),
        "sFencePattern": r"^https://(www\.)?starttesting\.net/",
        "sSubjectPattern": "",
        "sReadyPattern": r"(test|start|accessib|screen reader)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "GLOW Accessibility Toolkit",
        "sScriptName": "getGlowHelp.py",
        "sSystem": "the BITS site that publishes it",
        "sFolder": "GlowHelp",
        "sLogName": "getGlowHelp.log",
        "sZipName": "GlowHelp.zip",
        "iMaxPages": 300,
        "nDelay": 1.5,
        "sSeeds": ('"https://bits-acb.org/",\n'
                   '              "https://bits-acb.org/glow",\n'
                   '              "https://bits-acb.org/resources"'),
        "sFencePattern": r"^https://(www\.)?bits-acb\.org/",
        "sSubjectPattern": "",
        "sReadyPattern": r"(glow|toolkit|accessib|bits)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Quill",
        "sScriptName": "getQuillHelp.py",
        "sSystem": "one publisher, the reader and the radio service",
        "sFolder": "QuillHelp",
        "sLogName": "getQuillHelp.log",
        "sZipName": "QuillHelp.zip",
        "iMaxPages": 300,
        "nDelay": 1.5,
        "sSeeds": ('"https://quillforall.org/",\n'
                   '              "https://quillforall.org/radio.html",\n'
                   '              "https://quillforall.org/help.html"'),
        "sFencePattern": r"^https://(www\.)?quillforall\.org/",
        "sSubjectPattern": "",
        "sReadyPattern": r"(quill|read|radio|book)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "TTCom",
        "sScriptName": "getTtcomHelp.py",
        "sSystem": "the author's own documentation",
        "sFolder": "TtcomHelp",
        "sLogName": "getTtcomHelp.log",
        "sZipName": "TtcomHelp.zip",
        "iMaxPages": 300,
        "nDelay": 1.5,
        "sSeeds": ('"https://www.dlee.org/",\n'
                   '              "https://www.dlee.org/ttcom/",\n'
                   '              "https://www.dlee.org/ttcom/doc/"'),
        "sFencePattern": r"^https://(www\.)?dlee\.org/",
        "sSubjectPattern": "",
        "sReadyPattern": r"(ttcom|teamtalk|client|command)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "Sam Tupy games",
        "sScriptName": "getSamTupyHelp.py",
        "sSystem": "one publisher, several audio games",
        "sFolder": "SamTupyHelp",
        "sLogName": "getSamTupyHelp.log",
        "sZipName": "SamTupyHelp.zip",
        "iMaxPages": 300,
        "nDelay": 1.5,
        "sSeeds": ('"https://samtupy.com/",\n'
                   '              "https://samtupy.com/games.php",\n'
                   '              "https://survivethewild.net/"'),
        "sFencePattern": r"^https://(www\.)?(samtupy\.com|survivethewild\.net)/",
        "sSubjectPattern": "",
        "sReadyPattern": r"(game|wild|play|manual|guide)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
    {
        "sProduct": "LWorks audio games",
        "sScriptName": "getLWorksHelp.py",
        "sSystem": "one publisher, several audio games",
        "sFolder": "LWorksHelp",
        "sLogName": "getLWorksHelp.log",
        "sZipName": "LWorksHelp.zip",
        "iMaxPages": 300,
        "nDelay": 1.5,
        "sSeeds": ('"https://l-works.net/",\n'
                   '              "https://l-works.net/games.php",\n'
                   '              "https://l-works.net/support.php"'),
        "sFencePattern": r"^https://(www\.)?l-works\.net/",
        "sSubjectPattern": "",
        "sReadyPattern": r"(game|play|manual|guide|support)",
        "sOkStatuses": "200, 202",
        "sExtraLinks": "",
    },
]


def writeScripts(sOutputFolder):
    """Writes one standalone harvester per estate and returns their paths."""
    lPaths = []
    for dEstate in c_lEstates:
        sText = c_sChassis.format(**dEstate)
        sPath = os.path.join(sOutputFolder, dEstate["sScriptName"])
        fHandle = io.open(sPath, "w", encoding="utf-8-sig", newline="\r\n")
        fHandle.write(sText)
        fHandle.close()
        lPaths.append(sPath)
    return lPaths


def main():
    """Writes one harvester per estate into the folder named on the command line."""
    sOutputFolder = sys.argv[1] if len(sys.argv) > 1 else "."
    for sPath in writeScripts(sOutputFolder): print("wrote " + sPath)
    return 0


if __name__ == "__main__": sys.exit(main())
