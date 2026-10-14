"""getLlmsGuide.py version 2

Gathers a product's help from the publisher's own llms.txt index and builds the guide in one run.

WHY A NEW KIND OF HARVESTER. Some publishers now publish their documentation for machine reading: an index file
named llms.txt that lists every page by section, and a plain Markdown copy of each page (or of the whole manual in
one file, llms-full.txt). That is the publisher's own text, already free of menus, banners and scripts, with the
publisher's own sections. A crawler and a page reader would only throw that structure away, so this script reads
the index, fetches the Markdown, and builds the guide and its .htm pair directly.

WHAT IT KEEPS AND LEAVES OUT. Each product below names what it leaves out and why: developer material (programming
interfaces, writing plugins or modules, the program's own internals) and administrator material, as the collection's
ReadMe says. Every page left out is logged with its reason, and the guide's preamble counts them.

IT OBEYS ROBOTS.TXT. Before fetching from a host it reads that host's robots.txt and checks every address against the
rules for all agents. A refused address is logged and not fetched; if the index itself is refused, that product
stops and says so.

RUN IT with no arguments to gather and build every product, or name products: expo, hermes, kiro. Switches, in any
case: /gather (gather only), /build (build from what was gathered before), /fresh (fetch every page again rather
than reuse the copy saved last time). Harvests go in <Name>Help folders beside this script, zipped as <Name>Help.zip;
the guides are written as <Name>.md and <Name>.htm beside it. The .htm is built by fixPages.py from this folder or
from the kit, so it has one level-one heading and the Homer encoding.
"""

import datetime, hashlib, html, importlib.util, io, logging, os, platform, re, shutil, subprocess, sys, tempfile, time, urllib.error, urllib.parse, urllib.request

iMinimumWords, iRetries, iTimeoutSeconds = 15, 3, 60
nPauseSeconds = 1.0
sAccept = "text/markdown, text/plain;q=0.9, */*;q=0.1"
sLicense = ("The help text belongs to its publisher and is gathered here unchanged for accessible reading. "
              "This guide's own arrangement and wording are available under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).")
sLogName = "getLlmsGuide.log"
sMiscellaneous = "Miscellaneous"
sNewLine = "\r\n"
sPlaceholder = "\u0001"
sUserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
sVersion = "2"
lPageFurniture = ["copy as markdown", "copy page", "edit on github", "edit this page", "next", "on this page", "previous",
                  "view as markdown", "was this page helpful?"]
# A code fence, as CommonMark defines one: a run of three or more backticks with no backtick after it on the line (so
# ``` [details].tsx``matches``` is inline code, not a fence), or three or more tildes.
reFence = re.compile(r"^\s*(`{3,}(?=[^`]*$)|~{3,})")

# Each product: where its index lives, how its sections become categories, and what is left out and why. A pattern
# is matched against the page's path (lower case, without .md); a section is matched against the index's own heading.
lProducts = [
    {
        "sKey": "expo", "sName": "Expo", "sTitle": "Expo help", "sProduct": "Expo",
        "sIndexUrl": "https://docs.expo.dev/llms.txt", "sMode": "pages", "sCategoryMode": "headings",
        "lExcludeSections": [("Expo SDK", "the Expo SDK and library reference, written for programmers calling it from code"),
                             ("Third-party libraries", "the Expo SDK and library reference, written for programmers calling it from code"),
                             ("Expo UI", "the Expo SDK and library reference, written for programmers calling it from code"),
                             ("Expo Modules API", "the Expo Modules API, for writing native modules"),
                             ("Technical specs", "Expo's protocol specifications")],
        "lExcludePatterns": [(r"^/versions/latest/sdk(/|$)", "the Expo SDK and library reference, written for programmers calling it from code"),
                             (r"^/modules(/|$)", "the Expo Modules API, for writing native modules"),
                             (r"^/technical-specs(/|$)", "Expo's protocol specifications"),
                             (r"^/more/create-expo-module$", "the Expo Modules API, for writing native modules"),
                             (r"^/eas/workflows/rest-api$", "programming interfaces"),
                             (r"^/debugging/create-devtools-plugins$", "pages about writing plugins for other developers"),
                             (r"^/config-plugins/development-for-libraries$", "pages about writing plugins for other developers"),
                             (r"^/accounts/(sso|audit-logs)$", "administrator material for organisations"),
                             (r"^/llms$", "the page about these machine-readable files")],
        "sIntro": ("This guide holds the documentation Expo publishes for building, testing and publishing apps with Expo and its "
                   "cloud services (EAS), gathered on {date} from the Markdown copies Expo publishes of each page: {count} articles, "
                   "in the publisher's own sections."),
        "sCaution": ("To make an app by directing an AI coding agent, start with the Build with AI tutorial; Expo's cloud builds "
                     "are billed by use beyond the free plan, so read the billing articles before running many builds."),
        "sSiblings": "The Android Studio and Visual Studio Code guides in this collection cover two tools Expo projects are often opened in.",
    },
    {
        "sKey": "hermes", "sName": "HermesAgent", "sTitle": "Hermes Agent help", "sProduct": "Hermes Agent",
        "sIndexUrl": "https://hermes-agent.nousresearch.com/docs/llms.txt",
        "sFullUrl": "https://hermes-agent.nousresearch.com/docs/llms-full.txt",
        "sMode": "full", "sCategoryMode": "headings", "sSourcePrefix": "website/docs/", "sPathPrefix": "/docs/",
        "dPrefixCategory": {"getting-started": "Getting Started", "user-guide": "Using Hermes", "guides": "Guides & Tutorials",
                            "integrations": "Integrations", "reference": "Reference"},
        "lExcludeSections": [("Developer Guide", "the Developer Guide, about changing Hermes itself"),
                             ("More", "the community stories page, which quotes other people's posts")],
        "lExcludePatterns": [(r"^/docs/developer-guide(/|$)", "the Developer Guide, about changing Hermes itself"),
                             (r"^/docs/user-stories$", "the community stories page, which quotes other people's posts"),
                             (r"^/docs/guides/python-library$", "pages about building Hermes into other programs"),
                             (r"^/docs/user-guide/features/extending-the-dashboard$", "pages about building Hermes into other programs"),
                             (r"(^|/)(zh-hans|i18n)(/|$)", "translated editions")],
        "sIntro": ("This guide holds the documentation Nous Research publishes for Hermes Agent, gathered on {date} from the "
                   "single Markdown file Nous Research publishes for this purpose: {count} articles, in the publisher's own sections."),
        "sCaution": ("Hermes changes quickly, so treat this as a snapshot; it runs commands and can act through your accounts, "
                     "so read Security before connecting it to anything."),
        "sSiblings": ("The OpenClaw and Claude guides in this collection cover two of the agents Hermes can import its setup from, "
                      "and the Ollama guide covers running a model on your own computer."),
    },
    {
        "sKey": "kiro", "sName": "Kiro", "sTitle": "Kiro help", "sProduct": "Kiro",
        "sIndexUrl": "https://kiro.dev/sitemap.xml", "sMode": "sitemap", "sCategoryMode": "tree", "sPagePattern": r"^/docs(/|$)",
        "dSectionRoots": {"IDE": "/docs", "CLI": "/docs/cli", "Web": "/docs/web", "Shared": "/docs"},
        "dSectionLabels": {"IDE": "Kiro IDE", "CLI": "Kiro CLI", "Web": "Kiro Web", "Shared": "Account, billing and privacy"},
        "lSharedPrefixes": ["/docs/billing", "/docs/enterprise", "/docs/models", "/docs/privacy-and-security", "/docs/migrating-from-q-developer"],
        "lExcludeSections": [],
        "lExcludePatterns": [(r"^/docs/enterprise(/|$)", "administrator material for organisations"),
                             (r"^/docs/cli/mcp/registry$", "administrator material for organisations")],
        "sIntro": ("This guide holds the documentation Amazon publishes for Kiro, its coding agent for the desktop (the Kiro IDE), "
                   "the terminal (the Kiro CLI, which replaced the Amazon Q Developer CLI) and the browser (Kiro Web), gathered on "
                   "{date} from Kiro's documentation web pages: {count} articles. Kiro also publishes Markdown copies and an index for "
                   "machine reading, but its robots.txt asks automated readers to leave those alone, so the ordinary pages listed in its "
                   "sitemap were read instead. The categories follow Kiro's page tree."),
        "sCaution": "Kiro meters its work in credits, and the billing articles explain what happens when a plan's credits run out.",
        "sSiblings": ("The Claude, ChatGPT and Gemini guides in this collection cover Claude Code, Codex and Antigravity, and the "
                      "Visual Studio Code guide covers the editor Kiro is built on."),
    },
]


def startLog(sHere):
    """Opens the detailed log beside the script and records the environment."""
    sPath = os.path.join(sHere, sLogName)
    logging.basicConfig(filename=sPath, filemode="w", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        encoding="utf-8", errors="backslashreplace")
    logging.info("getLlmsGuide.py version %s", sVersion)
    logging.info("script %s; Python %s (%s) on %s", os.path.abspath(__file__), platform.python_version(), sys.executable, platform.platform())
    logging.info("working directory %s; command line: %s", os.getcwd(), " ".join(sys.argv))
    logging.info("settings: pause %.1f s, timeout %d s, retries %d, minimum words %d, user agent %s",
                 nPauseSeconds, iTimeoutSeconds, iRetries, iMinimumWords, sUserAgent)
    return sPath


def say(sText):
    """One succinct console line, flushed at once so a long run is never mistaken for a hang."""
    sys.stdout.write(sText + "\n")
    sys.stdout.flush()


def readText(sPath):
    """A saved file's text, whatever its encoding."""
    binBody = io.open(sPath, "rb").read()
    for sEncoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try: return binBody.decode(sEncoding)
        except UnicodeDecodeError: continue
    return binBody.decode("utf-8", "replace")


def writeText(sPath, sText):
    """Writes in the Homer encoding: UTF-8 with a byte order mark and Windows line endings."""
    sBody = sText.replace("\r\n", "\n").replace("\n", sNewLine)
    io.open(sPath, "wb").write(b"\xef\xbb\xbf" + sBody.encode("utf-8"))


def fetchText(sUrl, sWanted=sAccept):
    """Fetches one address, retrying a busy or failing host. Returns (status, text); status 0 means no answer."""
    for iAttempt in range(1, iRetries + 1):
        nStart = time.time()
        oRequest = urllib.request.Request(sUrl, headers={"User-Agent": sUserAgent, "Accept": sWanted})
        try:
            with urllib.request.urlopen(oRequest, timeout=iTimeoutSeconds) as oResponse:
                binBody = oResponse.read()
                sText = binBody.decode(oResponse.headers.get_content_charset() or "utf-8", "replace")
                logging.info("GET %s -> %d, %d bytes, %.1f s, %s", sUrl, oResponse.status, len(binBody), time.time() - nStart,
                             oResponse.headers.get("Content-Type", ""))
                return oResponse.status, sText
        except urllib.error.HTTPError as oError:
            logging.warning("GET %s -> %d (attempt %d of %d), %.1f s", sUrl, oError.code, iAttempt, iRetries, time.time() - nStart)
            if oError.code not in (429, 500, 502, 503, 504): return oError.code, ""
        except Exception as oError:
            logging.warning("GET %s failed (attempt %d of %d): %s: %s", sUrl, iAttempt, iRetries, type(oError).__name__, oError)
        time.sleep(nPauseSeconds * 5 * iAttempt)
    return 0, ""


def getRobots(dRobots, sUrl):
    """The robots rules for all agents on an address's host, read once per host: a list of (allowed, pattern)."""
    oParts = urllib.parse.urlsplit(sUrl)
    sHost = oParts.scheme + "://" + oParts.netloc
    if sHost in dRobots: return dRobots[sHost]
    iStatus, sText = fetchText(sHost + "/robots.txt")
    lRules = []
    if iStatus == 200:
        for sLine in sText.splitlines()[:80]:
            if sLine.strip(): logging.info("robots.txt %s: %s", sHost, sLine.strip())
        # Python's own robots parser ignores the * and $ wildcards that hosts now use ("Disallow: /docs/*.md"), so the
        # rules for all agents are read here: the longest matching pattern wins, and Allow wins a tie.
        bForAll, bInRules = False, False
        for sLine in sText.splitlines():
            sLine = sLine.split("#", 1)[0].strip()
            if ":" not in sLine: continue
            sField, sValue = [s.strip() for s in sLine.split(":", 1)]
            sField = sField.lower()
            if sField == "user-agent":
                if bInRules: bForAll, bInRules = False, False
                if sValue == "*": bForAll = True
            elif sField in ("allow", "disallow"):
                bInRules = True
                if bForAll and sValue: lRules.append((sField == "allow", sValue))
    else:
        logging.info("robots.txt %s: none (status %d), so nothing is refused", sHost, iStatus)
    dRobots[sHost] = lRules
    return lRules


def robotsAllow(lRules, sPathAndQuery):
    """Whether a path is allowed under robots rules with wildcards: the longest matching pattern decides."""
    iBest, bAllowed = -1, True
    for bAllow, sPattern in lRules:
        sRegex = "".join(".*" if sChar == "*" else re.escape(sChar) for sChar in sPattern.rstrip("$"))
        if sPattern.endswith("$"): sRegex += "$"
        if not re.match(sRegex, sPathAndQuery): continue
        if len(sPattern) > iBest or (len(sPattern) == iBest and bAllow): iBest, bAllowed = len(sPattern), bAllow
    return bAllowed


def mayFetch(dRobots, sUrl):
    """Whether robots.txt lets any agent fetch this address."""
    oParts = urllib.parse.urlsplit(sUrl)
    return robotsAllow(getRobots(dRobots, sUrl), (oParts.path or "/") + ("?" + oParts.query if oParts.query else ""))


def keyOfUrl(sUrl):
    """A page's identity: its path in lower case, without .md, /index or a trailing slash."""
    sPath = urllib.parse.urlsplit(sUrl).path.lower()
    sPath = re.sub(r"\.mdx?$", "", sPath)
    sPath = re.sub(r"/index$", "", sPath)
    return sPath.rstrip("/") or "/"


def parseIndex(sText):
    """The entries of an llms.txt: title, address, section and subsection, in the publisher's order."""
    if sText.count("\n") < 20:
        # Some indexes arrive with their line breaks flattened to spaces; restore one entry per line.
        sText = re.sub(r"\s+(#{2,3} )", r"\n\1", sText)
        sText = re.sub(r"\s+- \[", "\n- [", sText)
    lEntries, sSection, sSubsection = [], "", ""
    for sLine in sText.splitlines():
        oHeading = re.match(r"^(#{2,3})\s+(.+?)\s*$", sLine)
        if oHeading:
            if len(oHeading.group(1)) == 2: sSection, sSubsection = oHeading.group(2), ""
            else: sSubsection = oHeading.group(2)
            continue
        oEntry = re.match(r"^\s*[-*]\s+\[([^\]]+)\]\((https?://[^)\s]+)\)", sLine)
        if oEntry: lEntries.append({"sTitle": oEntry.group(1).replace("\\\"", "\"").strip(), "sUrl": oEntry.group(2),
                                    "sSection": sSection, "sSubsection": sSubsection})
    return lEntries


def exclusionReason(dProduct, sKey, sSection):
    """Why a page is left out, or an empty string when it is kept."""
    for sName, sReason in dProduct["lExcludeSections"]:
        if sSection.strip().lower() == sName.lower(): return sReason
    for sPattern, sReason in dProduct["lExcludePatterns"]:
        if re.search(sPattern, sKey): return sReason
    return ""


def fileNameFor(sKey):
    """A harvest file name for a page path."""
    sName = re.sub(r"[^a-z0-9._-]+", "_", sKey.strip("/")) or "index"
    return sName[:150] + ".md"


def gatherPages(dProduct, sFolder, lEntries, dRobots, bFresh):
    """Fetches the Markdown copy of every kept page into the harvest folder. Returns the manifest rows."""
    lRows, dSeen = [], {}
    lKept = []
    for dEntry in lEntries:
        sKey = keyOfUrl(dEntry["sUrl"])
        if sKey in dSeen: continue
        dSeen[sKey] = True
        if urllib.parse.urlsplit(dEntry["sUrl"]).netloc != urllib.parse.urlsplit(dProduct["sIndexUrl"]).netloc:
            logging.info("not fetched, another host: %s", dEntry["sUrl"])
            continue
        sReason = exclusionReason(dProduct, sKey, dEntry["sSection"])
        if sReason:
            logging.info("left out before fetching: %s (%s)", dEntry["sUrl"], sReason)
            lRows.append((dEntry["sUrl"], "", "left out: " + sReason))
            continue
        lKept.append(dEntry)
    iTotal = len(lKept)
    say("%s: %d pages to gather, about one a second" % (dProduct["sProduct"], iTotal))
    for iIndex, dEntry in enumerate(lKept, 1):
        sKey = keyOfUrl(dEntry["sUrl"])
        bHtml = dProduct["sMode"] == "sitemap"
        if bHtml: sUrl = dEntry["sUrl"]
        else: sUrl = dEntry["sUrl"] if re.search(r"\.mdx?$", dEntry["sUrl"]) else dEntry["sUrl"].rstrip("/") + ".md"
        sPath = os.path.join(sFolder, fileNameFor(sKey)[:-3] + (".htm" if bHtml else ".md"))
        say("%s %d of %d: %s" % (dProduct["sProduct"], iIndex, iTotal, sKey))
        if not mayFetch(dRobots, sUrl):
            logging.warning("robots.txt refuses %s; not fetched", sUrl)
            lRows.append((sUrl, "", "refused by robots.txt"))
            continue
        if not bFresh and os.path.isfile(sPath) and os.path.getsize(sPath) > 0:
            logging.info("kept from the last run: %s", sPath)
            lRows.append((sUrl, os.path.basename(sPath), "saved earlier"))
            continue
        iStatus, sText = fetchText(sUrl, "text/html" if bHtml else sAccept)
        time.sleep(nPauseSeconds)
        if iStatus != 200 or not sText.strip():
            lRows.append((sUrl, "", "status %d" % iStatus))
            continue
        if not bHtml and re.match(r"\s*(<!doctype|<html)", sText, re.I):
            logging.warning("%s answered with a web page rather than Markdown; not kept", sUrl)
            lRows.append((sUrl, "", "web page, not Markdown"))
            continue
        writeText(sPath, sText)
        lRows.append((sUrl, os.path.basename(sPath), "saved"))
    return lRows


def gatherProduct(dProduct, sHere, dRobots, bFresh):
    """Reads the index and saves what the product's mode calls for. Returns True when there is something to build."""
    sFolder = os.path.join(sHere, dProduct["sName"] + "Help")
    os.makedirs(sFolder, exist_ok=True)
    say("%s: reading the %s" % (dProduct["sProduct"], "sitemap" if dProduct["sMode"] == "sitemap" else "index"))
    if dProduct["sMode"] == "sitemap": return gatherSitemap(dProduct, sFolder, dRobots, bFresh)
    if not mayFetch(dRobots, dProduct["sIndexUrl"]):
        say("%s: robots.txt refuses the index, so nothing was gathered (see the log)" % dProduct["sProduct"])
        logging.error("%s: robots.txt refuses %s", dProduct["sProduct"], dProduct["sIndexUrl"])
        return False
    iStatus, sIndex = fetchText(dProduct["sIndexUrl"])
    if iStatus != 200 or not parseIndex(sIndex):
        say("%s: the index did not answer (status %d), so nothing was gathered" % (dProduct["sProduct"], iStatus))
        logging.error("%s: index %s answered %d with %d entries", dProduct["sProduct"], dProduct["sIndexUrl"], iStatus, len(parseIndex(sIndex)))
        return False
    writeText(os.path.join(sFolder, "llms.txt"), sIndex)
    lEntries = parseIndex(sIndex)
    logging.info("%s: the index lists %d pages in %d sections", dProduct["sProduct"], len(lEntries), len({d["sSection"] for d in lEntries}))
    lRows = []
    if dProduct["sMode"] == "full":
        say("%s: downloading the whole manual (one file)" % dProduct["sProduct"])
        if not mayFetch(dRobots, dProduct["sFullUrl"]):
            say("%s: robots.txt refuses the manual file, so nothing was gathered" % dProduct["sProduct"])
            return False
        iStatus, sFull = fetchText(dProduct["sFullUrl"])
        if iStatus != 200 or "<!-- source:" not in sFull:
            say("%s: the manual file did not arrive whole (status %d)" % (dProduct["sProduct"], iStatus))
            logging.error("%s: %s answered %d, %d characters", dProduct["sProduct"], dProduct["sFullUrl"], iStatus, len(sFull))
            return False
        writeText(os.path.join(sFolder, "llms-full.txt"), sFull)
        lRows.append((dProduct["sFullUrl"], "llms-full.txt", "saved"))
    else:
        lRows = gatherPages(dProduct, sFolder, lEntries, dRobots, bFresh)
    lManifest = ["address\tfile\toutcome"] + ["\t".join(tRow) for tRow in lRows]
    writeText(os.path.join(sFolder, "manifest.txt"), "\n".join(lManifest) + "\n")
    iSaved = sum(1 for tRow in lRows if tRow[1])
    iRefused = sum(1 for tRow in lRows if tRow[2] == "refused by robots.txt")
    iLeft = sum(1 for tRow in lRows if tRow[2].startswith("left out: "))
    logging.info("%s: %d files saved or kept, %d left out, %d refused by robots.txt, %d failed", dProduct["sProduct"], iSaved, iLeft,
                 iRefused, len(lRows) - iSaved - iRefused - iLeft)
    if iRefused: say("%s: robots.txt refused %d page%s (named in the log)" % (dProduct["sProduct"], iRefused, "" if iRefused == 1 else "s"))
    shutil.make_archive(sFolder, "zip", sFolder)
    return iSaved > 0


def gatherSitemap(dProduct, sFolder, dRobots, bFresh):
    """For a publisher whose robots.txt refuses its machine-readable copies: the ordinary pages its sitemap lists."""
    lQueue, lEntries, dSeen = [dProduct["sIndexUrl"]], [], {}
    sHost = urllib.parse.urlsplit(dProduct["sIndexUrl"]).netloc
    while lQueue:
        sMapUrl = lQueue.pop(0)
        if not mayFetch(dRobots, sMapUrl):
            logging.error("%s: robots.txt refuses the sitemap %s", dProduct["sProduct"], sMapUrl)
            continue
        iStatus, sMap = fetchText(sMapUrl, "application/xml, text/xml")
        if iStatus != 200:
            logging.error("%s: sitemap %s answered %d", dProduct["sProduct"], sMapUrl, iStatus)
            continue
        writeText(os.path.join(sFolder, fileNameFor(urllib.parse.urlsplit(sMapUrl).path)[:-3] + ".xml"), sMap)
        # A sitemap index lists further sitemaps; a sitemap lists pages.
        bIndex = "<sitemapindex" in sMap
        for sLoc in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", sMap):
            sLoc = sLoc.replace("&amp;", "&")
            if bIndex:
                lQueue.append(sLoc)
                continue
            sKey = keyOfUrl(sLoc)
            if urllib.parse.urlsplit(sLoc).netloc != sHost or not re.search(dProduct["sPagePattern"], sKey) or sKey in dSeen: continue
            dSeen[sKey] = True
            lEntries.append({"sTitle": "", "sUrl": sLoc, "sSection": "", "sSubsection": ""})
    logging.info("%s: the sitemap lists %d documentation pages", dProduct["sProduct"], len(lEntries))
    if not lEntries:
        say("%s: the sitemap listed no documentation pages, so nothing was gathered" % dProduct["sProduct"])
        return False
    lRows = gatherPages(dProduct, sFolder, lEntries, dRobots, bFresh)
    lManifest = ["address\tfile\toutcome"] + ["\t".join(tRow) for tRow in lRows]
    writeText(os.path.join(sFolder, "manifest.txt"), "\n".join(lManifest) + "\n")
    iSaved = sum(1 for tRow in lRows if tRow[1])
    iLeft = sum(1 for tRow in lRows if tRow[2].startswith("left out: "))
    logging.info("%s: %d pages saved or kept, %d left out, %d not gathered", dProduct["sProduct"], iSaved, iLeft, len(lRows) - iSaved - iLeft)
    shutil.make_archive(sFolder, "zip", sFolder)
    return iSaved > 0


def resolveStreaming(sHtml):
    """Puts each streamed block into its place, as the browser's script would. A site built with React streaming (Kiro)
    sends a placeholder, <template id="B:1">, where the article goes, and the article itself later in a hidden
    <div hidden id="S:1">; a streamed block may hold placeholders of its own."""
    dBlocks = {}
    for oStart in list(re.finditer(r'<div hidden id="S:(\d+)">', sHtml)):
        iDepth, iAt = 1, oStart.end()
        for oTag in re.finditer(r"<div\b|</div>", sHtml[oStart.end():]):
            iDepth += 1 if oTag.group(0) == "<div" else -1
            if not iDepth:
                iAt = oStart.end() + oTag.start()
                break
        dBlocks[oStart.group(1)] = (oStart.start(), iAt + len("</div>"), sHtml[oStart.end():iAt])
    if not dBlocks: return sHtml
    for sId, (iStart, iEnd, sBlock) in sorted(dBlocks.items(), key=lambda tItem: -tItem[1][0]): sHtml = sHtml[:iStart] + sHtml[iEnd:]
    for iPass in range(len(dBlocks) + 1):
        sBefore = sHtml
        sHtml = re.sub(r'(?s)<!--\$\?--><template id="B:(\d+)"></template>.*?<!--/\$-->',
                       lambda oMatch: dBlocks[oMatch.group(1)][2] if oMatch.group(1) in dBlocks else "", sHtml)
        if sHtml == sBefore: break
    return sHtml


def htmlToMarkdown(sPandoc, sHtml, sKey):
    """A documentation web page as (title, Markdown): its main region, without menus, scripts or page furniture."""
    sHtml = resolveStreaming(sHtml)
    oRegion = re.search(r"(?is)<main\b[^>]*>(.*)</main>", sHtml) or re.search(r"(?is)<article\b[^>]*>(.*)</article>", sHtml) \
        or re.search(r"(?is)<body\b[^>]*>(.*)</body>", sHtml)
    sRegion = oRegion.group(1) if oRegion else sHtml
    for sTag in ("script", "style", "noscript", "svg", "nav", "aside", "footer", "header", "form", "button", "template", "iframe"):
        sBefore = None
        while sBefore != sRegion:
            sBefore = sRegion
            sRegion = re.sub(r"(?is)<%s\b[^>]*>(?:(?!<%s\b).)*?</%s>" % (sTag, sTag, sTag), "", sRegion)
    # A code block is rebuilt as plain text in its language: Kiro wraps its code in styled layers that Pandoc would
    # otherwise read as a block with no language, or name after a styling class.
    def plainCode(oMatch):
        oLanguage = re.search(r"language-([\w+#-]+)", oMatch.group(1))
        sCode = html.unescape(re.sub(r"<[^>]+>", "", re.sub(r"(?i)<br\s*/?>", "\n", oMatch.group(1))))
        return '<pre><code class="' + (oLanguage.group(1) if oLanguage else "text") + '">' + html.escape(sCode, quote=False) + "</code></pre>"
    sRegion = re.sub(r"(?is)<pre\b[^>]*>(.*?)</pre>", plainCode, sRegion)
    oHeading = re.search(r"(?is)<h1\b[^>]*>(.*?)</h1>", sRegion)
    oTitle = re.search(r"(?is)<title>(.*?)</title>", sHtml)
    sTitle = re.sub(r"<[^>]+>", "", oHeading.group(1) if oHeading else (oTitle.group(1) if oTitle else ""))
    sTitle = re.sub(r"\s+", " ", re.sub(r"\s*[|\-\u2013\u2014]\s*Kiro\s*$", "", html.unescape(sTitle))).strip()
    if not sPandoc: return sTitle, re.sub(r"<[^>]+>", " ", sRegion)
    oResult = subprocess.run([sPandoc, "-f", "html", "-t", "gfm-raw_html", "--wrap=none"], input=sRegion.encode("utf-8"), capture_output=True)
    if oResult.returncode != 0:
        logging.warning("Pandoc could not read the page %s: %s", sKey, oResult.stderr.decode("utf-8", "replace")[-300:])
        return sTitle, ""
    lKept = []
    for sLine in oResult.stdout.decode("utf-8", "replace").replace("\r\n", "\n").split("\n"):
        sBare = re.sub(r"[*_`\[\]]", "", re.sub(r"\]\([^)]*\)", "]", sLine)).strip().lower()
        # Page furniture, named rather than guessed at: these lines are the site's, not the article's.
        if sBare in lPageFurniture: continue
        lKept.append(sLine)
    return sTitle, "\n".join(lKept)


def splitFullManual(dProduct, sFull):
    """Splits llms-full.txt at its source markers. Returns (key, page address, text) for each page."""
    lPages = []
    lParts = re.split(r"<!--\s*source:\s*(\S+?)\s*-->", sFull)
    for iIndex in range(1, len(lParts) - 1, 2):
        sSource = lParts[iIndex]
        sBody = re.sub(r"\n-{3,}\s*$", "", lParts[iIndex + 1].rstrip())
        sRelative = sSource[len(dProduct["sSourcePrefix"]):] if sSource.startswith(dProduct["sSourcePrefix"]) else sSource
        sOrigin = "{0.scheme}://{0.netloc}".format(urllib.parse.urlsplit(dProduct["sIndexUrl"]))
        sPageUrl = sOrigin + dProduct["sPathPrefix"] + sRelative
        lPages.append((keyOfUrl(sPageUrl), sPageUrl, sBody))
    return lPages


def fenceStep(sLine, iFence):
    """Follows code fences the CommonMark way. iFence is the open fence's length (negative for tildes, zero when none
    is open). A fence opens on three or more backticks with no backtick after them, or tildes; it closes only on a run
    of the same character at least as long, WITH NOTHING ELSE ON THE LINE, so "```bash" inside a block is code.
    Returns (whether this line is a fence, the new state)."""
    if not iFence:
        oOpen = reFence.match(sLine)
        if not oOpen: return False, 0
        sRun = oOpen.group(1)
        return True, len(sRun) if sRun[0] == "`" else -len(sRun)
    oClose = re.match(r"^\s*(`{3,}|~{3,})\s*$", sLine)
    if oClose and (oClose.group(1)[0] == "`") == (iFence > 0) and len(oClose.group(1)) >= abs(iFence): return True, 0
    return False, iFence


def stripComponents(sText):
    """Turns the publisher's page components into plain Markdown, keeping every word a reader needs."""
    sText = re.sub(r"(?s)<AgentInstructions>.*?</AgentInstructions>", "", sText)
    sText = re.sub(r"(?m)^This documentation is available as Markdown for AI agents and LLMs\..*$", "", sText)
    sText = re.sub(r"(?s)<!--.*?-->", "", sText)
    sText = re.sub(r"(?is)<div[^>]*>\s*<iframe.*?</iframe>\s*</div>", "", sText)
    sText = re.sub(r"(?is)<iframe.*?(/>|</iframe>)", "", sText)
    sText = re.sub(r"(?is)<summary>(.*?)</summary>", lambda oMatch: "\n**" + re.sub(r"<[^>]+>", "", oMatch.group(1)).strip() + "**\n", sText)
    sText = re.sub(r"(?im)^\s*</?details>\s*$", "", sText)
    lOut, iFence = [], 0
    for sLine in sText.split("\n"):
        bFenceLine, iFence = fenceStep(sLine, iFence)
        if bFenceLine:
            lOut.append(sLine)
            continue
        if iFence:
            lOut.append(sLine)
            continue
        oAdmonition = re.match(r"^\s*:::\s*(\w+)\s*(.*)$", sLine)
        if oAdmonition:
            sLabel = oAdmonition.group(1).capitalize()
            sCaption = oAdmonition.group(2).strip()
            lOut.append("**" + sLabel + (": " + sCaption if sCaption else "") + "**")
            lOut.append("")
            continue
        if re.match(r"^\s*:::\s*$", sLine): continue
        # An MDX import line is the page's own plumbing.
        if re.match(r"^import\s+.+\s+from\s+['\"].+['\"];?\s*$", sLine): continue
        # A line that is nothing but a component tag (an upper-case JSX name) is scaffolding; its words are on the lines
        # it wraps, which are kept. A tab's or a panel's label is kept as a bold line, so "Linux" and "macOS" are not lost.
        oComponent = re.match(r"^\s*<(/?)([A-Z][A-Za-z0-9.]*)(\s[^>]*)?/?>\s*$", sLine)
        if oComponent:
            oLabel = re.search(r"\b(?:label|title)=[\"']([^\"']+)[\"']", oComponent.group(3) or "")
            if oLabel and not oComponent.group(1): lOut.extend(["", "**" + oLabel.group(1) + "**", ""])
            continue
        # A heading's own identifier served links inside the page, which the guide no longer needs, and two pages using
        # the same one would give the .htm a duplicate.
        if re.match(r"^#{1,6} ", sLine): sLine = re.sub(r"\s*\{#[^}]*\}\s*$", "", sLine)
        lOut.append(sLine)
    return "\n".join(lOut)


def dropTitleHeading(sText, sTitle):
    """Removes front matter and the page's own title heading, which the guide gives once as the article heading."""
    sText = re.sub(r"(?s)\A\ufeff?---\n.*?\n---\n", "", sText.replace("\r\n", "\n"))
    lLines = sText.split("\n")
    sWanted = re.sub(r"\W+", " ", sTitle.lower()).strip()
    while True:
        while lLines and not lLines[0].strip(): lLines.pop(0)
        # A page's opening level-one headings are its own title, sometimes given twice and sometimes worded longer than
        # the index's name for it ("Hermes Agent Quickstart" for "Quickstart"); the article heading already says it.
        if lLines and re.match(r"^# ", lLines[0]):
            sFound = re.sub(r"\W+", " ", lLines[0][2:].lower()).strip()
            if sFound != sWanted: logging.info("page title %r given as %r in the index", lLines[0][2:].strip(), sTitle)
            lLines.pop(0)
            continue
        break
    return "\n".join(lLines)


def pandocIdentifier(sHeading):
    """The identifier Pandoc itself gives a heading, before it makes duplicates unique."""
    oExplicit = re.search(r"\{#([^\s}]+)[^}]*\}\s*$", sHeading)
    if oExplicit: return oExplicit.group(1)
    sText = re.sub(r"\{[^}]*\}\s*$", "", sHeading)
    lParts = sText.split("`")
    for iPart in range(0, len(lParts), 2):
        sPart = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", lParts[iPart])
        sPart = re.sub(r"<[^>]+>", "", sPart)
        sPart = re.sub(r"(?<!\w)[*_]+|[*_]+(?!\w)", "", sPart)
        lParts[iPart] = re.sub(r"\\(.)", r"\1", sPart)
    sText = "".join(lParts)
    sId = "".join(sChar for sChar in sText if sChar.isalnum() or sChar in "_-." or sChar.isspace())
    sId = re.sub(r"\s+", "-", sId.strip()).lower()
    sId = re.sub(r"^[^a-z\u00c0-\uffff]+", "", sId)
    return sId or "section"


def assignIdentifiers(lLines):
    """Every heading's identifier as Pandoc assigns them, in document order. Returns a list of (line number, level, id)."""
    lFound, dUsed, iFence = [], {}, 0
    for iLine, sLine in enumerate(lLines):
        bFenceLine, iFence = fenceStep(sLine, iFence)
        if bFenceLine:
            continue
        if iFence: continue
        oHeading = re.match(r"^(#{1,6}) (.+?)\s*#*\s*$", sLine)
        if not oHeading: continue
        sBase = pandocIdentifier(oHeading.group(2))
        sId, iSuffix = sBase, 0
        while sId in dUsed:
            iSuffix += 1
            sId = sBase + "-" + str(iSuffix)
        dUsed[sId] = True
        lFound.append((iLine, len(oHeading.group(1)), sId))
    return lFound


def rewriteLinks(sText, sPageUrl, dAnchors, sSiteHost):
    """Points a link at the article in this guide when the guide holds it, and at the live page when it does not."""
    def replaceLink(oMatch):
        sLabel, sTarget = oMatch.group(1), oMatch.group(2)
        if sTarget.startswith("#"): return sLabel
        if sTarget.startswith(("mailto:", "tel:")): return oMatch.group(0)
        sAbsolute = urllib.parse.urljoin(sPageUrl, sTarget)
        oParts = urllib.parse.urlsplit(sAbsolute)
        if oParts.netloc.lower() != sSiteHost.lower(): return "[" + sLabel + "](" + sAbsolute + ")"
        sKey = keyOfUrl(sAbsolute)
        if sKey in dAnchors: return "[" + sLabel + "](#" + sPlaceholder + sKey + sPlaceholder + ")"
        sPath = re.sub(r"\.mdx?$", "", oParts.path)
        sPath = re.sub(r"/index$", "/", sPath)
        return "[" + sLabel + "](" + oParts.scheme + "://" + oParts.netloc + sPath + ("#" + oParts.fragment if oParts.fragment else "") + ")"

    def replaceImage(oMatch):
        sAlt = oMatch.group(1).strip()
        return "(Image: " + sAlt + ")" if sAlt else ""

    lOut, iFence = [], 0
    for sLine in sText.split("\n"):
        bFenceLine, iFence = fenceStep(sLine, iFence)
        if bFenceLine:
            lOut.append(sLine)
            continue
        if iFence:
            lOut.append(sLine)
            continue
        # A link's label may itself hold code ([`pre_tool_call`](#pre_tool_call)), so links are found across the whole
        # line and only a link that STARTS inside a code span is left alone.
        lCode = [oSpan.span() for oSpan in re.finditer(r"`[^`]*`", sLine)]
        fnOutside = lambda oMatch, fnDo: oMatch.group(0) if any(iStart < oMatch.start() < iEnd for iStart, iEnd in lCode) else fnDo(oMatch)
        sLine = re.sub(r"!\[([^\]]*)\]\([^)]*\)", lambda oMatch: fnOutside(oMatch, replaceImage), sLine)
        # A link with no words (a heading's link icon) says nothing to a reader.
        lCode = [oSpan.span() for oSpan in re.finditer(r"`[^`]*`", sLine)]
        sLine = re.sub(r"(?<!!)\[\s*\]\([^)]*\)", lambda oMatch: fnOutside(oMatch, lambda oInner: ""), sLine)
        lCode = [oSpan.span() for oSpan in re.finditer(r"`[^`]*`", sLine)]
        sLine = re.sub(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", lambda oMatch: fnOutside(oMatch, replaceLink), sLine)
        lOut.append(sLine)
    return "\n".join(lOut)


def labelOneAddress(oMatch):
    """Builds the replacement for one address left bare in prose (the builder's rule)."""
    sUrl = oMatch.group(1).rstrip(".,;:")
    sTail = oMatch.group(1)[len(sUrl):]
    return "[" + readableAddress(sUrl) + "](" + sUrl + ")" + sTail


def readableAddress(sUrl):
    """An address as a reader hears it: host and path, without the scheme, a www or a closing slash."""
    return re.sub(r"^https?://(www\.)?", "", sUrl).rstrip("/")


def labelProse(lLines):
    """Labels bare addresses and escapes dollar signs in prose, leaving code exactly as the publisher wrote it."""
    lOut, iFence = [], 0
    for sLine in lLines:
        bFenceLine, iFence = fenceStep(sLine, iFence)
        if bFenceLine:
            lOut.append(sLine)
            continue
        if iFence:
            lOut.append(sLine)
            continue
        lParts = sLine.split("`")
        for iPart in range(0, len(lParts), 2):
            sPart = re.sub(r"(?<!\\)\$", r"\\$", lParts[iPart])
            sPart = re.sub(r"\[(https?://[^\]\s]+)\]\(([^)\s]+)\)", lambda oMatch: "[" + readableAddress(oMatch.group(1)) + "](" + oMatch.group(2) + ")", sPart)
            sPart = re.sub(r"(?<![\(\[<])(https?://[A-Za-z0-9-]+\.[A-Za-z]{2,}[^\s\)\]<>\"'`]*)", labelOneAddress, sPart)
            sPart = re.sub(r"<(https?://[^>\s]+)>", lambda oMatch: labelOneAddress(re.match(r"(.*)", oMatch.group(1))), sPart)
            lParts[iPart] = sPart
        lOut.append("`".join(lParts))
    return lOut


def balanceFences(lLines):
    """Closes a code fence an article leaves open (the builder's rule)."""
    iFence = 0
    for sLine in lLines:
        bFenceLine, iFence = fenceStep(sLine, iFence)
    if not iFence: return lLines
    logging.warning("an article left a code fence open; closing it")
    return list(lLines) + [("`" if iFence > 0 else "~") * abs(iFence), ""]


def renumberHeadings(lLines):
    """Renumbers an article's own headings by nesting depth from level four (the builder's rule)."""
    lOut, lStack, iFence = [], [], 0
    for sLine in lLines:
        bFenceLine, iFence = fenceStep(sLine, iFence)
        if bFenceLine:
            lOut.append(sLine)
            continue
        # A heading inside a list item arrives indented, and is still a heading to Pandoc.
        oHeading = None if iFence else re.match(r"^(\s*)(#{1,6}) (.+)$", sLine)
        if not oHeading:
            lOut.append(sLine)
            continue
        iSource = len(oHeading.group(2))
        while lStack and lStack[-1] >= iSource: lStack.pop()
        iLevel = min(6, 4 + len(lStack))
        lStack.append(iSource)
        # Pandoc reads a heading only after a blank line; without one, the line is text in a paragraph.
        if lOut and lOut[-1].strip(): lOut.append("")
        lOut.append(oHeading.group(1) + "#" * iLevel + " " + oHeading.group(3))
    return lOut


def sortKeyTitle(sTitle):
    """Case-insensitive title order, ignoring a leading A, An or The."""
    sKey = re.sub(r"\s+", " ", sTitle.strip().lower())
    for sArticle in ("a ", "an ", "the "):
        if sKey.startswith(sArticle): return sKey[len(sArticle):]
    return sKey


def sortKeyCategory(sCategory):
    """Alphabetical, except that Miscellaneous always comes last."""
    return "zzzz" if sCategory == sMiscellaneous else sortKeyTitle(sCategory)


def treeCategory(dProduct, sKey, sSection, dTitles):
    """For a publisher whose index gives few sections: the section, then the page tree beneath it."""
    sSectionName = sSection if sSection in dProduct["dSectionRoots"] else ""
    if not sSectionName:
        if sKey.startswith("/docs/cli"): sSectionName = "CLI"
        elif sKey.startswith("/docs/web"): sSectionName = "Web"
        elif any(sKey.startswith(sPrefix) for sPrefix in dProduct["lSharedPrefixes"]): sSectionName = "Shared"
        else: sSectionName = "IDE"
    sRoot = dProduct["dSectionRoots"][sSectionName]
    sLabel = dProduct["dSectionLabels"][sSectionName]
    sRest = sKey[len(sRoot):].strip("/") if sKey.startswith(sRoot) else sKey.strip("/")
    if not sRest or sRest == "index": return sLabel + ": Getting started", sLabel
    sGroup = sRest.split("/")[0]
    sGroupTitle = dTitles.get(sRoot.rstrip("/") + "/" + sGroup, sGroup.replace("-", " ").capitalize())
    return sLabel + ": " + sGroupTitle, sLabel


def collectArticles(dProduct, sFolder, sPandoc):
    """Reads the harvest into (category, title, key, page address, text) and counts what was left out and why."""
    sIndexPath = os.path.join(sFolder, "llms.txt")
    lEntries = parseIndex(readText(sIndexPath)) if os.path.isfile(sIndexPath) else []
    dIndex = {}
    for dEntry in lEntries: dIndex.setdefault(keyOfUrl(dEntry["sUrl"]), dEntry)
    dTitles = {sKey: dEntry["sTitle"] for sKey, dEntry in dIndex.items()}
    dLeftOut, lArticles = {}, []
    if dProduct["sMode"] == "full":
        lPages = splitFullManual(dProduct, readText(os.path.join(sFolder, "llms-full.txt")))
    elif dProduct["sMode"] == "sitemap":
        lPages = []
        lRows = [sLine.split("\t") for sLine in readText(os.path.join(sFolder, "manifest.txt")).splitlines()[1:]]
        say("%s: Pandoc is reading %d web pages" % (dProduct["sProduct"], sum(1 for lRow in lRows if len(lRow) >= 2 and lRow[1])))
        for lRow in lRows:
            if len(lRow) >= 3 and lRow[2].startswith("left out: "):
                dLeftOut[lRow[2][10:]] = dLeftOut.get(lRow[2][10:], 0) + 1
                continue
            if len(lRow) < 2 or not lRow[1]: continue
            sKey = keyOfUrl(lRow[0])
            sTitle, sText = htmlToMarkdown(sPandoc, readText(os.path.join(sFolder, lRow[1])), sKey)
            if not sText.strip():
                logging.warning("no article text found in %s", lRow[0])
                continue
            dIndex[sKey] = {"sTitle": sTitle or sKey.rsplit("/", 1)[-1].replace("-", " ").capitalize(), "sUrl": lRow[0],
                            "sSection": "", "sSubsection": ""}
            lPages.append((sKey, lRow[0], sText))
        dTitles = {sKey: dEntry["sTitle"] for sKey, dEntry in dIndex.items()}
    else:
        lPages = []
        dFiles = {}
        for sLine in readText(os.path.join(sFolder, "manifest.txt")).splitlines()[1:]:
            lParts = sLine.split("\t")
            if len(lParts) >= 2 and lParts[1]: dFiles[keyOfUrl(lParts[0])] = (lParts[0], lParts[1])
        sHost = urllib.parse.urlsplit(dProduct["sIndexUrl"]).netloc
        for sKey, dEntry in dIndex.items():
            if sKey in dFiles: lPages.append((sKey, dFiles[sKey][0], readText(os.path.join(sFolder, dFiles[sKey][1]))))
            elif urllib.parse.urlsplit(dEntry["sUrl"]).netloc == sHost:
                sReason = exclusionReason(dProduct, sKey, dEntry["sSection"])
                if sReason: dLeftOut[sReason] = dLeftOut.get(sReason, 0) + 1
                else: logging.warning("listed in the index but not gathered: %s", dEntry["sUrl"])
    dTexts = {}
    # Shorter addresses first, so a page served twice is kept at its plainer address (/docs/billing, not /docs/cli/billing).
    lPages.sort(key=lambda tPage: (tPage[0].count("/"), tPage[0]))
    for sKey, sPageUrl, sText in lPages:
        # A page served at two addresses (Kiro gives its shared pages an IDE and a CLI address) is kept once.
        sDigest = hashlib.sha1(re.sub(r"\s+", " ", sText).strip().encode("utf-8")).hexdigest()
        if sDigest in dTexts:
            sReason = "second copies of pages published at two addresses"
            dLeftOut[sReason] = dLeftOut.get(sReason, 0) + 1
            logging.info("left out: %s is the same page as %s", sKey, dTexts[sDigest])
            continue
        dTexts[sDigest] = sKey
        dEntry = dIndex.get(sKey)
        sSection = dEntry["sSection"] if dEntry else ""
        sReason = exclusionReason(dProduct, sKey, sSection)
        if sReason:
            dLeftOut[sReason] = dLeftOut.get(sReason, 0) + 1
            logging.info("left out: %s (%s)", sKey, sReason)
            continue
        if dEntry: sTitle = dEntry["sTitle"]
        else:
            oFirst = re.search(r"(?m)^# (.+)$", sText)
            sTitle = oFirst.group(1).strip() if oFirst else sKey.rsplit("/", 1)[-1].replace("-", " ").capitalize()
        if dProduct["sCategoryMode"] == "tree":
            sCategory, sShort = treeCategory(dProduct, sKey, sSection, dTitles)
        elif dEntry:
            sCategory = sSection + (": " + dEntry["sSubsection"] if dEntry["sSubsection"] else "")
            sShort = sSection
        else:
            sFirstSegment = sKey[len(dProduct.get("sPathPrefix", "/")):].split("/")[0] if sKey.startswith(dProduct.get("sPathPrefix", "/")) else ""
            sCategory = dProduct.get("dPrefixCategory", {}).get(sFirstSegment, sMiscellaneous)
            sShort = sCategory
            logging.info("not in the index, placed by its path: %s -> %s", sKey, sCategory)
        lArticles.append({"sCategory": sCategory.strip() or sMiscellaneous, "sShort": sShort, "sTitle": sTitle,
                          "sKey": sKey, "sPageUrl": sPageUrl, "sText": sText})
    return lArticles, dLeftOut


def settleTitles(lArticles):
    """Folds one-article categories and gives every article a title, and so an anchor, of its own."""
    dCount = {}
    for dArticle in lArticles: dCount[dArticle["sCategory"]] = dCount.get(dArticle["sCategory"], 0) + 1
    for dArticle in lArticles:
        if dCount[dArticle["sCategory"]] < 2:
            # In a tree, a lone page first joins its own section's general pages before it falls to Miscellaneous.
            dArticle["sCategory"] = dArticle["sShort"] + ": General" if dArticle["sShort"] and dArticle["sShort"] != dArticle["sCategory"] else sMiscellaneous
    dCount = {}
    for dArticle in lArticles: dCount[dArticle["sCategory"]] = dCount.get(dArticle["sCategory"], 0) + 1
    for dArticle in lArticles:
        if dCount[dArticle["sCategory"]] < 2: dArticle["sCategory"] = sMiscellaneous
    for dArticle in lArticles: dArticle["sBaseTitle"] = dArticle["sTitle"]
    dGroups = {}
    for dArticle in lArticles: dGroups.setdefault(dArticle["sTitle"].lower(), []).append(dArticle)
    lWays = [lambda dItem: dItem["sShort"], lambda dItem: dItem["sCategory"].split(": ")[-1],
             lambda dItem: dItem["sKey"].strip("/").replace("/", " ")]
    for lSame in dGroups.values():
        if len(lSame) < 2: continue
        # The first description that tells every copy apart: the section, then the category, then the page's path.
        for fnWay in lWays:
            lValues = [fnWay(dItem) for dItem in lSame]
            if all(lValues) and len({s.lower() for s in lValues}) == len(lValues): break
        for dItem in lSame: dItem["sTitle"] = dItem["sTitle"] + " (" + fnWay(dItem) + ")"
    dTaken = {}
    for dArticle in lArticles:
        sAnchor = pandocIdentifier(dArticle["sTitle"])
        if sAnchor in dTaken:
            dArticle["sTitle"] = dArticle["sTitle"] + " (" + dArticle["sKey"].strip("/").replace("/", " ") + ")"
            sAnchor = pandocIdentifier(dArticle["sTitle"])
        dTaken[sAnchor] = True
    return lArticles


def leftOutSentence(dLeftOut):
    """The preamble's count of what was left out, largest first."""
    if not dLeftOut: return "Nothing was left out."
    lParts = ["%s (%d page%s)" % (sReason, iCount, "" if iCount == 1 else "s")
              for sReason, iCount in sorted(dLeftOut.items(), key=lambda tItem: (-tItem[1], tItem[0]))]
    if len(lParts) == 1: return "Left out: " + lParts[0] + "."
    if len(lParts) == 2: return "Left out: " + lParts[0] + " and " + lParts[1] + "."
    return "Left out: " + "; ".join(lParts[:-1]) + "; and " + lParts[-1] + "."


def codeFilterPath():
    """A one-line Pandoc filter, written once, that labels a code block with no language as text. Pandoc writes a
    labelled block between fences, which every check here reads correctly; an unlabelled one it would indent, and an
    indented comment line or address then looks like prose."""
    sPath = os.path.join(tempfile.gettempdir(), "getLlmsGuideCode.lua")
    if not os.path.isfile(sPath):
        # Written without a byte order mark, which Lua would read as code.
        io.open(sPath, "w", encoding="utf-8").write("function CodeBlock(oBlock)\n  if #oBlock.classes == 0 then oBlock.classes = {\"text\"} end\n  return oBlock\nend\n")
    return sPath


def normalizeMarkdown(sPandoc, sText, sKey):
    """Reads an article as the publisher wrote it (GitHub-style Markdown) and writes it as Pandoc's Markdown, so a
    heading, a code block or a list means the same to this script as to Pandoc. Unchanged when Pandoc is not here."""
    if not sPandoc: return sText
    lCommand = [sPandoc, "-f", "gfm-gfm_auto_identifiers", "--lua-filter", codeFilterPath(), "-t",
                "markdown-smart-header_attributes-link_attributes-bracketed_spans-native_divs-native_spans-simple_tables-multiline_tables-grid_tables",
                "--wrap=none"]
    oResult = subprocess.run(lCommand, input=sText.encode("utf-8"), capture_output=True)
    if oResult.returncode != 0:
        logging.warning("Pandoc could not read %s (exit %d): %s; kept as gathered", sKey, oResult.returncode, oResult.stderr.decode("utf-8", "replace")[-300:])
        return sText
    return oResult.stdout.decode("utf-8", "replace").replace("\r\n", "\n")


def buildGuideText(dProduct, lArticles, dLeftOut, sDate, sPandoc):
    """The finished guide, in the collection's shape, with every internal link pointing at Pandoc's own identifier."""
    sHost = urllib.parse.urlsplit(dProduct["sIndexUrl"]).netloc
    dAnchors = {dArticle["sKey"]: True for dArticle in lArticles}
    sPreamble = " ".join([dProduct["sIntro"].format(date=sDate, count=len(lArticles)), leftOutSentence(dLeftOut),
                          dProduct["sCaution"], dProduct["sSiblings"]])
    lLines = ["---", "title: \"" + dProduct["sTitle"] + "\"", "lang: en", "license: \"CC BY-SA 4.0\"",
              "license_url: \"https://creativecommons.org/licenses/by-sa/4.0/\"", "---", "", "# " + dProduct["sTitle"], "",
              sPreamble, "", sLicense, "", "## Contents", ""]
    dCategories = {}
    for dArticle in lArticles: dCategories.setdefault(dArticle["sCategory"], []).append(dArticle)
    lOrder = []
    for sCategory in sorted(dCategories, key=sortKeyCategory):
        dCategories[sCategory].sort(key=lambda dItem: sortKeyTitle(dItem["sTitle"]))
        lOrder.extend(dCategories[sCategory])
        lLines.append("- " + sCategory)
        for dArticle in dCategories[sCategory]:
            lLines.append("    - [" + dArticle["sTitle"] + "](#" + sPlaceholder + dArticle["sKey"] + sPlaceholder + ")")
    lLines.append("")
    lThin = []
    if sPandoc: say("%s: Pandoc is reading %d articles" % (dProduct["sProduct"], len(lOrder)))
    for sCategory in sorted(dCategories, key=sortKeyCategory):
        lLines.extend(["## " + sCategory, ""])
        for dArticle in dCategories[sCategory]:
            sBody = dropTitleHeading(stripComponents(dArticle["sText"].replace("\r\n", "\n")), dArticle["sBaseTitle"])
            sBody = normalizeMarkdown(sPandoc, sBody, dArticle["sKey"])
            sBody = rewriteLinks(sBody, dArticle["sPageUrl"], dAnchors, sHost)
            lBody = labelProse(renumberHeadings(balanceFences(sBody.split("\n"))))
            lClean = []
            for sLine in lBody:
                if sLine.strip() == "" and lClean and lClean[-1].strip() == "": continue
                lClean.append(sLine.rstrip())
            while lClean and not lClean[0].strip(): lClean.pop(0)
            while lClean and not lClean[-1].strip(): lClean.pop()
            if len(" ".join(lClean).split()) < iMinimumWords: lThin.append(dArticle["sKey"])
            lLines.extend(["### " + dArticle["sTitle"], ""] + lClean + [""])
    for sKey in lThin: logging.info("a short article, kept as the publisher wrote it: %s", sKey)
    # The article headings are the level-three headings after the contents list, one per article in order.
    lFlat = []
    for sLine in lLines: lFlat.extend(sLine.split("\n"))
    iContents = lFlat.index("## Contents")
    # Pandoc decides the identifiers, so Pandoc is asked; working them out here is only the fallback, because a
    # publisher's page can hold a line that looks like a heading to a reader and is not one to Pandoc.
    lArticleIds = pandocArticleIds(sPandoc, "\n".join(lFlat))
    if lArticleIds is None or len(lArticleIds) != len(lOrder):
        logging.warning("Pandoc's heading identifiers could not be used (%s); working them out instead",
                        "no Pandoc" if lArticleIds is None else "%d for %d articles" % (len(lArticleIds), len(lOrder)))
        lArticleIds = [sId for iLine, iLevel, sId in assignIdentifiers(lFlat) if iLevel == 3 and iLine > iContents]
    dIds = {dArticle["sKey"]: sId for dArticle, sId in zip(lOrder, lArticleIds)}
    if len(lArticleIds) != len(lOrder): logging.error("%d article headings found for %d articles", len(lArticleIds), len(lOrder))
    for dArticle in lOrder:
        if dIds.get(dArticle["sKey"]) != pandocIdentifier(dArticle["sTitle"]):
            logging.info("identifier made unique by Pandoc: %s -> %s", dArticle["sTitle"], dIds.get(dArticle["sKey"]))
    sText = sNewLine.join(lFlat) + sNewLine
    sText = re.sub(re.escape(sPlaceholder) + r"(.*?)" + re.escape(sPlaceholder), lambda oMatch: dIds.get(oMatch.group(1), "missing"), sText)
    return sText, dCategories


def pandocArticleIds(sPandoc, sText):
    """The identifiers Pandoc itself gives the level-three headings, in order, or None when Pandoc cannot say."""
    if not sPandoc: return None
    oResult = subprocess.run([sPandoc, "-f", "markdown", "-t", "html5"], input=sText.encode("utf-8"), capture_output=True)
    logging.info("pandoc asked for heading identifiers: exit %d %s", oResult.returncode, oResult.stderr.decode("utf-8", "replace")[-300:])
    if oResult.returncode != 0: return None
    return re.findall(r"<h3\b[^>]*\bid=\"([^\"]*)\"", oResult.stdout.decode("utf-8", "replace"))


def pageGates(sPagePath, bRaw=False):
    """Checks the built .htm. As Pandoc built it: every internal link has a target. Finished: one level-one heading
    and no identifier used twice."""
    lFailures = []
    sPage = readText(sPagePath)
    if bRaw:
        dIds = {sId: True for sId in re.findall(r"\sid=\"([^\"]+)\"", sPage)}
        lMissing = sorted({sHref for sHref in re.findall(r"href=\"#([^\"]+)\"", sPage) if sHref not in dIds})
        if lMissing: lFailures.append("%d internal links in the .htm have no target, first #%s" % (len(lMissing), lMissing[0]))
        for sFailure in lFailures: logging.error("PAGE GATE FAILED for %s: %s", sPagePath, sFailure)
        return lFailures
    lIds = re.findall(r"\sid=\"([^\"]+)\"", sPage)
    dIds = {}
    for sId in lIds: dIds[sId] = dIds.get(sId, 0) + 1
    lDouble = [sId for sId, iCount in dIds.items() if iCount > 1]
    if lDouble: lFailures.append("%d identifiers used twice in the .htm, first %s" % (len(lDouble), lDouble[0]))
    lMissing = sorted({sHref for sHref in re.findall(r"href=\"#([^\"]+)\"", sPage) if sHref not in dIds})
    if lMissing: lFailures.append("%d internal links in the .htm have no target, first #%s" % (len(lMissing), lMissing[0]))
    iHeadings = len(re.findall(r"(?i)<h1\b", sPage))
    if iHeadings != 1: lFailures.append("the .htm has %d level-one headings" % iHeadings)
    for sFailure in lFailures: logging.error("PAGE GATE FAILED for %s: %s", sPagePath, sFailure)
    return lFailures


def runGates(sProduct, sPath, sText):
    """Checks one finished guide and logs every result (the builder's gates)."""
    lFailures = []
    binHead = io.open(sPath, "rb").read(3)
    if binHead != b"\xef\xbb\xbf": lFailures.append("no byte order mark")
    if b"\r\n" not in io.open(sPath, "rb").read(): lFailures.append("no Windows line endings")
    lOutside, iFence = [], 0
    for sLine in sText.split(sNewLine):
        bFenceLine, iFence = fenceStep(sLine, iFence)
        if bFenceLine:
            continue
        if not iFence: lOutside.append(sLine)
    sBare = sNewLine.join(lOutside)
    iArticles = len(re.findall(r"^### ", sBare, re.M))
    sContents = sBare.split("## Contents", 1)[-1].split(sNewLine + "## ", 1)[0]
    iContents = len(re.findall(r"^    - \[", sContents, re.M))
    if iArticles != iContents: lFailures.append("contents lists %d entries against %d articles" % (iContents, iArticles))
    if iArticles < 3: lFailures.append("fewer than three articles")
    lWordCounts = sorted(len(s.split()) for s in re.split(r"(?m)^### .+$", sBare)[1:])
    iMedian = lWordCounts[len(lWordCounts) // 2] if lWordCounts else 0
    if iMedian < 25: lFailures.append("the median article holds only %d words" % iMedian)
    lLines = sText.split(sNewLine)
    if lLines and lLines[0].strip().lstrip("\ufeff") == "---":
        iEnd = next((i for i in range(1, len(lLines)) if lLines[i].strip() == "---"), 0)
        lLines = lLines[iEnd + 1:]
    lBare, iFence = [], 0
    for sLine in lLines:
        bFenceLine, iFence = fenceStep(sLine, iFence)
        if bFenceLine:
            continue
        if iFence: continue
        sProse = "".join(sLine.split("`")[0::2])
        sWithoutLinks = re.sub(r"\]\([^)]*\)", "]", sProse)
        if re.search(r"\bhttps?://[A-Za-z0-9-]+\.[A-Za-z]{2,}", sWithoutLinks): lBare.append(sProse)
    if lBare:
        lFailures.append("%d lines carry a bare address" % len(lBare))
        for sLine in lBare[:5]: logging.info("bare address: %s", sLine[:200])
    dKnown = {sId: True for iLine, iLevel, sId in assignIdentifiers(sText.split(sNewLine))}
    lBroken = sorted({oMatch.group(1) for oMatch in re.finditer(r"\]\(#([^\)]+)\)", sBare) if oMatch.group(1) not in dKnown})
    if lBroken: logging.info("%d internal links point at no heading by this script's own reckoning, first #%s; the .htm check decides", len(lBroken), lBroken[0])
    if iFence: lFailures.append("a code fence is left open at the end of the guide")
    dSeen = {}
    for sHeading in re.findall(r"^### (.+)$", sBare, re.M):
        sTitleKey = sHeading.strip().lower()
        if sTitleKey in dSeen: lFailures.append("two articles share the title " + sHeading)
        dSeen[sTitleKey] = True
    iLevel = 1
    for oMatch in re.finditer(r"(?m)^(#{1,6}) ", sBare):
        iThis = len(oMatch.group(1))
        if iThis > iLevel + 1: lFailures.append("heading level jumps from %d to %d" % (iLevel, iThis))
        iLevel = iThis
    for sFailure in lFailures[:10]: logging.error("GATE FAILED for %s: %s", sProduct, sFailure)
    logging.info("%s gates: %d articles, median %d words, %d failures", sProduct, iArticles, iMedian, len(lFailures))
    return lFailures, iArticles, iMedian


def loadFixPages(sHere):
    """The kit's fixPages.py (version 4, with its page rules) or, failing that, the collection's own copy."""
    for sFolder in (os.path.join(os.environ.get("HomerDev", "") or r"C:\HomerDev", "scripts"), sHere):
        sPath = os.path.join(sFolder, "fixPages.py")
        if not os.path.isfile(sPath): continue
        try:
            oSpec = importlib.util.spec_from_file_location("fixPagesModule", sPath)
            oModule = importlib.util.module_from_spec(oSpec)
            oSpec.loader.exec_module(oModule)
        except Exception as oError:
            logging.warning("fixPages at %s could not be loaded: %s", sPath, oError)
            continue
        if hasattr(oModule, "loadRules") or hasattr(oModule, "buildPage"):
            logging.info("fixPages loaded from %s (%s)", sPath, "version 4 rules" if hasattr(oModule, "loadRules") else "version 3")
            return oModule
        logging.warning("fixPages at %s has neither loadRules nor buildPage; not used", sPath)
    logging.warning("fixPages.py was not found; the .htm is built with Pandoc directly")
    return None


def findPandoc(oFixPages):
    """The newest Pandoc, chosen the kit's way when the kit is here."""
    sPandoc = oFixPages.findPandoc() if oFixPages and hasattr(oFixPages, "findPandoc") else ""
    return sPandoc or shutil.which("pandoc") or ""


def buildPage(oFixPages, sMarkdownPath, sTitle):
    """Builds the .htm pair the kit's way. Returns True when it has exactly one level-one heading."""
    sPandoc = findPandoc(oFixPages)
    if not sPandoc:
        logging.error("Pandoc was not found, so %s has no .htm", sMarkdownPath)
        return False
    if oFixPages and hasattr(oFixPages, "buildPage") and not hasattr(oFixPages, "loadRules"):
        return oFixPages.buildPage(sPandoc, oFixPages.kitHeadingRule(), sMarkdownPath, sTitle)
    sFolder = os.path.dirname(os.path.abspath(sMarkdownPath))
    sPagePath = sMarkdownPath[:-3] + ".htm"
    oRules = oFixPages.loadRules() if oFixPages else None
    lCommand = [sPandoc, sMarkdownPath, "-f", "markdown", "-t", "html5", "--standalone", "--toc", "--toc-depth=2",
                "-M", "pagetitle=" + sTitle, "-M", "lang=" + (oRules.sLang if oRules else "en"), "-o", sPagePath]
    if not oRules: lCommand[-2:-2] = ["-M", "title="]
    oResult = subprocess.run(lCommand, capture_output=True)
    logging.info("RUN %s: exit %d %s", " ".join(lCommand), oResult.returncode, oResult.stderr.decode("utf-8", "replace")[-400:])
    if oResult.returncode != 0: return False
    sPage = readText(sPagePath).replace("\r\n", "\n")
    # Checked as Pandoc built it, before the kit's finish quietly turns a link to nothing into plain text.
    lRawFailures = pageGates(sPagePath, True)
    if lRawFailures: return False
    if oRules:
        # The kit's two page rules, exactly as fixPages version 4 applies them: one level-one heading, then the finish
        # (language, main landmark, unique identifiers, links that lead somewhere).
        sPage = oRules.oneTitleHeading(sPage)
        setLocal = {s.lower() for s in os.listdir(sFolder)}
        sPage, dDone = oRules.finishPage(sPage, setLocal, oFixPages.readFixes(sFolder))
        logging.info("%s finished by the kit's rules: %s", sPagePath, ", ".join("%s %d" % t for t in sorted(dDone.items())) or "unchanged")
    writeText(sPagePath, sPage)
    return len(re.findall(r"(?i)<h1\b", sPage)) == 1


def buildProduct(dProduct, sHere, oFixPages, sDate):
    """Builds one guide and its pair from the harvest. Returns True when every gate passed."""
    sFolder = os.path.join(sHere, dProduct["sName"] + "Help")
    if not os.path.isfile(os.path.join(sFolder, "manifest.txt")):
        say("%s: nothing gathered yet, so nothing to build" % dProduct["sProduct"])
        logging.error("%s: no harvest at %s", dProduct["sProduct"], sFolder)
        return False
    say("%s: building the guide" % dProduct["sProduct"])
    # "Gathered on" is the day the harvest was saved, so a later rebuild does not move the date.
    sDate = datetime.date.fromtimestamp(os.path.getmtime(os.path.join(sFolder, "manifest.txt"))).strftime("%d %B %Y").lstrip("0")
    lArticles, dLeftOut = collectArticles(dProduct, sFolder, findPandoc(oFixPages))
    lArticles = settleTitles(lArticles)
    sText, dCategories = buildGuideText(dProduct, lArticles, dLeftOut, sDate, findPandoc(oFixPages))
    sPath = os.path.join(sHere, dProduct["sName"] + ".md")
    writeText(sPath, sText)
    sText = readText(sPath).replace("\n", sNewLine).replace("\r\r\n", sNewLine)
    lFailures, iArticles, iMedian = runGates(dProduct["sProduct"], sPath, sText)
    logging.info("%s: %d articles in %d categories, %d words", dProduct["sProduct"], iArticles, len(dCategories), len(sText.split()))
    for sCategory in sorted(dCategories, key=sortKeyCategory): logging.info("    %s: %d", sCategory, len(dCategories[sCategory]))
    for sReason, iCount in sorted(dLeftOut.items()): logging.info("    left out, %s: %d", sReason, iCount)
    bPage = buildPage(oFixPages, sPath, dProduct["sTitle"])
    if not bPage: lFailures.append("the .htm pair did not build with one level-one heading")
    elif os.path.isfile(sPath[:-3] + ".htm"): lFailures.extend(pageGates(sPath[:-3] + ".htm"))
    say("%s: %s.md, %d article%s in %d categor%s, median %d words, %s" % (
        dProduct["sProduct"], dProduct["sName"], iArticles, "" if iArticles == 1 else "s", len(dCategories),
        "y" if len(dCategories) == 1 else "ies", iMedian, "all gates passed" if not lFailures else "%d gate%s failed (see the log)" % (
            len(lFailures), "" if len(lFailures) == 1 else "s")))
    return not lFailures


def main():
    sHere = os.path.dirname(os.path.abspath(__file__))
    sLogPath = startLog(sHere)
    lSwitches = [s.lower() for s in sys.argv[1:] if s.startswith("/")]
    lNames = [s.lower() for s in sys.argv[1:] if not s.startswith("/")]
    bGather = "/build" not in lSwitches
    bBuild = "/gather" not in lSwitches
    bFresh = "/fresh" in lSwitches
    lUnknown = [s for s in lNames if s not in [d["sKey"] for d in lProducts]]
    if lUnknown:
        say("Unknown product: " + ", ".join(lUnknown) + ". Known: " + ", ".join(d["sKey"] for d in lProducts) + ".")
        return 2
    lChosen = [d for d in lProducts if not lNames or d["sKey"] in lNames]
    logging.info("products %s; gather %s, build %s, fresh %s", ", ".join(d["sKey"] for d in lChosen), bGather, bBuild, bFresh)
    sDate = datetime.date.today().strftime("%d %B %Y").lstrip("0")
    dRobots = {}
    oFixPages = loadFixPages(sHere) if bBuild else None
    iFailed = 0
    for dProduct in lChosen:
        try:
            if bGather and not gatherProduct(dProduct, sHere, dRobots, bFresh):
                iFailed += 1
                continue
            if bBuild and not buildProduct(dProduct, sHere, oFixPages, sDate): iFailed += 1
        except Exception as oError:
            logging.exception("%s stopped with an error", dProduct["sProduct"])
            say("%s stopped with an error: %s (details in the log)" % (dProduct["sProduct"], oError))
            iFailed += 1
    say("Products needing a look: %d" % iFailed if iFailed else "Every product finished cleanly.")
    say("Log: " + sLogPath)
    return 1 if iFailed else 0


if __name__ == "__main__":
    sys.exit(main())
