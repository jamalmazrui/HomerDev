"""getLlmsGuide.py version 1

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

import datetime, importlib.util, io, logging, os, platform, re, shutil, subprocess, sys, time, urllib.error, urllib.parse, urllib.request, urllib.robotparser

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
sVersion = "1"

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
        "sIndexUrl": "https://kiro.dev/llms.txt", "sMode": "pages", "sCategoryMode": "tree",
        "dSectionRoots": {"IDE": "/docs", "CLI": "/docs/cli", "Web": "/docs/web", "Shared": "/docs"},
        "dSectionLabels": {"IDE": "Kiro IDE", "CLI": "Kiro CLI", "Web": "Kiro Web", "Shared": "Account, billing and privacy"},
        "lSharedPrefixes": ["/docs/billing", "/docs/enterprise", "/docs/models", "/docs/privacy-and-security", "/docs/migrating-from-q-developer"],
        "lExcludeSections": [],
        "lExcludePatterns": [(r"^/docs/enterprise(/|$)", "administrator material for organisations"),
                             (r"^/docs/cli/mcp/registry$", "administrator material for organisations")],
        "sIntro": ("This guide holds the documentation Amazon publishes for Kiro, its coding agent for the desktop (the Kiro IDE), "
                   "the terminal (the Kiro CLI, which replaced the Amazon Q Developer CLI) and the browser (Kiro Web), gathered on "
                   "{date} from the Markdown copies Kiro publishes of each page: {count} articles. The categories follow Kiro's own "
                   "sections and page tree."),
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


def fetchText(sUrl):
    """Fetches one address, retrying a busy or failing host. Returns (status, text); status 0 means no answer."""
    for iAttempt in range(1, iRetries + 1):
        nStart = time.time()
        oRequest = urllib.request.Request(sUrl, headers={"User-Agent": sUserAgent, "Accept": sAccept})
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
    """The robots rules for an address's host, read once per host."""
    oParts = urllib.parse.urlsplit(sUrl)
    sHost = oParts.scheme + "://" + oParts.netloc
    if sHost in dRobots: return dRobots[sHost]
    iStatus, sText = fetchText(sHost + "/robots.txt")
    oRobots = urllib.robotparser.RobotFileParser()
    if iStatus == 200:
        oRobots.parse(sText.splitlines())
        for sLine in sText.splitlines()[:60]:
            if sLine.strip(): logging.info("robots.txt %s: %s", sHost, sLine.strip())
    else:
        oRobots.parse([])
        logging.info("robots.txt %s: none (status %d), so nothing is refused", sHost, iStatus)
    dRobots[sHost] = oRobots
    return oRobots


def mayFetch(dRobots, sUrl):
    """Whether robots.txt lets any agent fetch this address."""
    return getRobots(dRobots, sUrl).can_fetch("*", sUrl)


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
            continue
        lKept.append(dEntry)
    iTotal = len(lKept)
    say("%s: %d pages to gather, about one a second" % (dProduct["sProduct"], iTotal))
    for iIndex, dEntry in enumerate(lKept, 1):
        sKey = keyOfUrl(dEntry["sUrl"])
        sUrl = dEntry["sUrl"] if re.search(r"\.mdx?$", dEntry["sUrl"]) else dEntry["sUrl"].rstrip("/") + ".md"
        sPath = os.path.join(sFolder, fileNameFor(sKey))
        say("%s %d of %d: %s" % (dProduct["sProduct"], iIndex, iTotal, sKey))
        if not mayFetch(dRobots, sUrl):
            logging.warning("robots.txt refuses %s; not fetched", sUrl)
            lRows.append((sUrl, "", "refused by robots.txt"))
            continue
        if not bFresh and os.path.isfile(sPath) and os.path.getsize(sPath) > 0:
            logging.info("kept from the last run: %s", sPath)
            lRows.append((sUrl, os.path.basename(sPath), "saved earlier"))
            continue
        iStatus, sText = fetchText(sUrl)
        time.sleep(nPauseSeconds)
        if iStatus != 200 or not sText.strip():
            lRows.append((sUrl, "", "status %d" % iStatus))
            continue
        if re.match(r"\s*(<!doctype|<html)", sText, re.I):
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
    say("%s: reading the index" % dProduct["sProduct"])
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
    logging.info("%s: %d files saved or kept, %d refused by robots.txt, %d failed", dProduct["sProduct"], iSaved, iRefused,
                 len(lRows) - iSaved - iRefused)
    if iRefused: say("%s: robots.txt refused %d page%s (named in the log)" % (dProduct["sProduct"], iRefused, "" if iRefused == 1 else "s"))
    shutil.make_archive(sFolder, "zip", sFolder)
    return iSaved > 0


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
        oFence = re.match(r"\s*(`{3,}|~{3,})", sLine)
        if oFence:
            iRun = len(oFence.group(1))
            if not iFence: iFence = iRun
            elif iRun >= iFence: iFence = 0
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
        oFence = re.match(r"\s*(`{3,}|~{3,})", sLine)
        if oFence:
            iRun = len(oFence.group(1))
            if not iFence: iFence = iRun
            elif iRun >= iFence: iFence = 0
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
        oFence = re.match(r"\s*(`{3,}|~{3,})", sLine)
        if oFence:
            iRun = len(oFence.group(1))
            if not iFence: iFence = iRun
            elif iRun >= iFence: iFence = 0
            lOut.append(sLine)
            continue
        if iFence:
            lOut.append(sLine)
            continue
        lParts = sLine.split("`")
        for iPart in range(0, len(lParts), 2):
            sPart = re.sub(r"!\[([^\]]*)\]\([^)]*\)", replaceImage, lParts[iPart])
            sPart = re.sub(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", replaceLink, sPart)
            lParts[iPart] = sPart
        lOut.append("`".join(lParts))
    return "\n".join(lOut)


def labelOneAddress(oMatch):
    """Builds the replacement for one address left bare in prose (the builder's rule)."""
    sUrl = oMatch.group(1).rstrip(".,;:")
    sTail = oMatch.group(1)[len(sUrl):]
    sHost = re.sub(r"^https?://(www\.)?", "", sUrl).split("/")[0]
    return "[" + sHost + "](" + sUrl + ")" + sTail


def labelProse(lLines):
    """Labels bare addresses and escapes dollar signs in prose, leaving code exactly as the publisher wrote it."""
    lOut, iFence = [], 0
    for sLine in lLines:
        oFence = re.match(r"\s*(`{3,}|~{3,})", sLine)
        if oFence:
            iRun = len(oFence.group(1))
            if not iFence: iFence = iRun
            elif iRun >= iFence: iFence = 0
            lOut.append(sLine)
            continue
        if iFence:
            lOut.append(sLine)
            continue
        lParts = sLine.split("`")
        for iPart in range(0, len(lParts), 2):
            sPart = re.sub(r"(?<!\\)\$", r"\\$", lParts[iPart])
            sPart = re.sub(r"(?<![\(\[<])(https?://[A-Za-z0-9-]+\.[A-Za-z]{2,}[^\s\)\]<>\"'`]*)", labelOneAddress, sPart)
            sPart = re.sub(r"<(https?://[^>\s]+)>", lambda oMatch: labelOneAddress(re.match(r"(.*)", oMatch.group(1))), sPart)
            lParts[iPart] = sPart
        lOut.append("`".join(lParts))
    return lOut


def balanceFences(lLines):
    """Closes a code fence an article leaves open (the builder's rule)."""
    iFence = 0
    for sLine in lLines:
        oFence = re.match(r"\s*(`{3,})", sLine)
        if not oFence: continue
        iRun = len(oFence.group(1))
        if not iFence: iFence = iRun
        elif iRun >= iFence: iFence = 0
    if not iFence: return lLines
    logging.warning("an article left a code fence open; closing it")
    return list(lLines) + ["`" * iFence, ""]


def renumberHeadings(lLines):
    """Renumbers an article's own headings by nesting depth from level four (the builder's rule)."""
    lOut, lStack, iFence = [], [], 0
    for sLine in lLines:
        oFence = re.match(r"\s*(`{3,}|~{3,})", sLine)
        if oFence:
            iRun = len(oFence.group(1))
            if not iFence: iFence = iRun
            elif iRun >= iFence: iFence = 0
            lOut.append(sLine)
            continue
        oHeading = None if iFence else re.match(r"^(#{1,6}) (.+)$", sLine)
        if not oHeading:
            lOut.append(sLine)
            continue
        iSource = len(oHeading.group(1))
        while lStack and lStack[-1] >= iSource: lStack.pop()
        iLevel = min(6, 4 + len(lStack))
        lStack.append(iSource)
        lOut.append("#" * iLevel + " " + oHeading.group(2))
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


def collectArticles(dProduct, sFolder):
    """Reads the harvest into (category, title, key, page address, text) and counts what was left out and why."""
    lEntries = parseIndex(readText(os.path.join(sFolder, "llms.txt")))
    dIndex = {}
    for dEntry in lEntries: dIndex.setdefault(keyOfUrl(dEntry["sUrl"]), dEntry)
    dTitles = {sKey: dEntry["sTitle"] for sKey, dEntry in dIndex.items()}
    dLeftOut, lArticles = {}, []
    if dProduct["sMode"] == "full":
        lPages = splitFullManual(dProduct, readText(os.path.join(sFolder, "llms-full.txt")))
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
    for sKey, sPageUrl, sText in lPages:
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


def buildGuideText(dProduct, lArticles, dLeftOut, sDate):
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
    for sCategory in sorted(dCategories, key=sortKeyCategory):
        lLines.extend(["## " + sCategory, ""])
        for dArticle in dCategories[sCategory]:
            sBody = dropTitleHeading(stripComponents(dArticle["sText"].replace("\r\n", "\n")), dArticle["sBaseTitle"])
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
    lArticleIds = [sId for iLine, iLevel, sId in assignIdentifiers(lFlat) if iLevel == 3 and iLine > iContents]
    dIds = {dArticle["sKey"]: sId for dArticle, sId in zip(lOrder, lArticleIds)}
    if len(lArticleIds) != len(lOrder): logging.error("%d article headings found for %d articles", len(lArticleIds), len(lOrder))
    for dArticle in lOrder:
        if dIds.get(dArticle["sKey"]) != pandocIdentifier(dArticle["sTitle"]):
            logging.info("identifier made unique by Pandoc: %s -> %s", dArticle["sTitle"], dIds.get(dArticle["sKey"]))
    sText = sNewLine.join(lFlat) + sNewLine
    sText = re.sub(re.escape(sPlaceholder) + r"(.*?)" + re.escape(sPlaceholder), lambda oMatch: dIds.get(oMatch.group(1), "missing"), sText)
    return sText, dCategories


def pageGates(sPagePath):
    """Checks the built .htm: every internal link has a target, and no identifier is used twice."""
    lFailures = []
    sPage = readText(sPagePath)
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
        oFence = re.match(r"\s*(`{3,}|~{3,})", sLine)
        if oFence:
            iRun = len(oFence.group(1))
            if not iFence: iFence = iRun
            elif iRun >= iFence: iFence = 0
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
        oFence = re.match(r"\s*(`{3,}|~{3,})", sLine)
        if oFence:
            iRun = len(oFence.group(1))
            if not iFence: iFence = iRun
            elif iRun >= iFence: iFence = 0
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
    if lBroken: lFailures.append("%d internal links point at no heading, first #%s" % (len(lBroken), lBroken[0]))
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
    """fixPages.py from this folder, or from the kit, so the .htm is built the collection's way."""
    for sFolder in (sHere, os.path.join(os.environ.get("HomerDev", "") or r"C:\HomerDev", "scripts")):
        sPath = os.path.join(sFolder, "fixPages.py")
        if not os.path.isfile(sPath): continue
        try:
            oSpec = importlib.util.spec_from_file_location("fixPagesModule", sPath)
            oModule = importlib.util.module_from_spec(oSpec)
            oSpec.loader.exec_module(oModule)
            logging.info("fixPages loaded from %s", sPath)
            return oModule
        except Exception as oError:
            logging.warning("fixPages at %s could not be loaded: %s", sPath, oError)
    logging.warning("fixPages.py was not found; the .htm is built with Pandoc directly")
    return None


def buildPage(oFixPages, sMarkdownPath, sTitle):
    """Builds the .htm pair. Returns True when it has exactly one level-one heading."""
    if oFixPages:
        sPandoc = oFixPages.findPandoc()
        if not sPandoc: return False
        return oFixPages.buildPage(sPandoc, oFixPages.kitHeadingRule(), sMarkdownPath, sTitle)
    sPandoc = shutil.which("pandoc")
    if not sPandoc: return False
    sPagePath = sMarkdownPath[:-3] + ".htm"
    lCommand = [sPandoc, sMarkdownPath, "-f", "markdown", "-t", "html5", "--standalone", "--toc", "--toc-depth=2",
                "-M", "title=", "-M", "pagetitle=" + sTitle, "-o", sPagePath]
    logging.info("running: %s", " ".join(lCommand))
    oResult = subprocess.run(lCommand, capture_output=True)
    logging.info("pandoc exit %d %s", oResult.returncode, oResult.stderr.decode("utf-8", "replace")[:400])
    if oResult.returncode != 0: return False
    sPage = readText(sPagePath)
    writeText(sPagePath, sPage)
    return len(re.findall(r"(?i)<h1\b", sPage)) == 1


def buildProduct(dProduct, sHere, oFixPages, sDate):
    """Builds one guide and its pair from the harvest. Returns True when every gate passed."""
    sFolder = os.path.join(sHere, dProduct["sName"] + "Help")
    if not os.path.isfile(os.path.join(sFolder, "llms.txt")):
        say("%s: nothing gathered yet, so nothing to build" % dProduct["sProduct"])
        logging.error("%s: no harvest at %s", dProduct["sProduct"], sFolder)
        return False
    say("%s: building the guide" % dProduct["sProduct"])
    lArticles, dLeftOut = collectArticles(dProduct, sFolder)
    lArticles = settleTitles(lArticles)
    sText, dCategories = buildGuideText(dProduct, lArticles, dLeftOut, sDate)
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
