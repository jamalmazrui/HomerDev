r"""getDocs.py -- fetches the documents named in data\getDocs.inix: a PDF or Word file where the page offers one,
otherwise the page itself as a structured, cleaned .md with its .htm. Part of the HomerDev kit (1.216.0).

    getDocs          every document in the kit's data\getDocs.inix
    getDocs <list>   the documents in another .inix of the same form

WHERE THINGS GO, by the Homer tree: into the current folder's results\getDocs, and the log into its logs folder as
<Folder>-getDocs-yyyyMMdd-HHmmss.log, in UTF-8 with a byte order mark and Windows line endings. A document already
there is fetched again, so a rerun gets the newest edition.

A FILE BEFORE A PAGE. Where a section names a files pattern, the page's links to .pdf, .docx and .doc files whose
text or address match it are gathered; of those, a link naming the newest year wins, and both its PDF and Word
forms are kept when the page offers both. Only when none matches is the page converted.

A PAGE AS A DOCUMENT. The page's main content -- its article or main element, else its body -- is kept, and its
navigation, headers, footers, side panels, forms, scripts, buttons and images without text are dropped. Pandoc turns
what is left into Markdown with one level-one heading, the document's title; the page's own headings sit below it.
A short source note at the top names the address and the date fetched. The .htm is the same document as a page.
"""

import datetime, html, io, os, platform, re, shutil, subprocess, sys, time, urllib.parse, urllib.request

sUserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
lsFileTypes = [".pdf", ".docx", ".doc"]
lsDropTags = ["aside", "button", "footer", "form", "header", "iframe", "nav", "noscript", "script", "select", "style", "svg"]
dState = {"fLog": None}


def log(sText):
    if dState["fLog"]: dState["fLog"].write(datetime.datetime.now().strftime("%H:%M:%S ") + sText + "\n"); dState["fLog"].flush()
    return True


def say(sText):
    print(sText, flush=True)
    return log("SAY " + sText)


def readList(sPath):
    """[(name, {key: value})] from an .inix list."""
    lOut, dCur = [], None
    for sLine in io.open(sPath, "rb").read().decode("utf-8-sig", "replace").splitlines():
        sLine = sLine.strip()
        if not sLine or sLine.startswith(";"): continue
        oSection = re.match(r"^\[(.+)\]$", sLine)
        if oSection:
            dCur = {}
            lOut.append((oSection.group(1).strip(), dCur))
        elif dCur is not None and "=" in sLine:
            sKey, sValue = sLine.split("=", 1)
            dCur[sKey.strip().lower()] = sValue.strip()
    return lOut


def fetch(sUrl):
    """(bytes, final address, content type); raises on failure."""
    oRequest = urllib.request.Request(sUrl, headers={"User-Agent": sUserAgent, "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(oRequest, timeout=90) as oResponse:
        binBody = oResponse.read()
        log("GET %s -> %d, %d bytes, %s" % (sUrl, oResponse.status, len(binBody), oResponse.headers.get("Content-Type", "")))
        return binBody, oResponse.geturl(), oResponse.headers.get("Content-Type", "")


def fileLinks(sHtml, sBase, sPattern):
    """Links to PDF or Word files whose text or address match the pattern: [(address, text, extension)]."""
    lOut = []
    for oMatch in re.finditer(r'(?is)<a\b[^>]*href\s*=\s*["\']([^"\']+)["\'][^>]*>(.*?)</a>', sHtml):
        sHref = urllib.parse.urljoin(sBase, html.unescape(oMatch.group(1)).strip())
        sText = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", oMatch.group(2)))).strip()
        sExtension = os.path.splitext(urllib.parse.urlsplit(sHref).path)[1].lower()
        if sExtension in lsFileTypes and re.search(sPattern, sText + " " + sHref, re.I): lOut.append((sHref, sText, sExtension))
    return lOut


def newestOf(lLinks):
    """The links of the newest year named in a link's text or address, every type kept; all, when none names a year."""
    def yearOf(t): return max([int(y) for y in re.findall(r"\b(20\d\d|19\d\d)\b", t[0] + " " + t[1])] or [0])
    iNewest = max(yearOf(t) for t in lLinks)
    lKeep = [t for t in lLinks if yearOf(t) == iNewest]
    lUnique, setSeen = [], set()
    for t in lKeep:
        if t[0] not in setSeen: setSeen.add(t[0]); lUnique.append(t)
    return lUnique


def mainContent(sHtml):
    """The page's article or main element, else its body, with its furniture dropped."""
    sHtml = re.sub(r"(?s)<!--.*?-->", "", sHtml)
    for sTag in lsDropTags: sHtml = re.sub(r"(?is)<%s\b.*?</%s\s*>" % (sTag, sTag), "", sHtml)
    sHtml = re.sub(r'(?is)<(div|section)\b[^>]*(?:class|id)="[^"]*(?:cookie|share|social|related|comment|newsletter|subscribe|sidebar|breadcrumb|advert|promo)[^"]*"[^>]*>', "<div>", sHtml)
    for sPattern in (r"(?is)<article\b[^>]*>(.*)</article>", r"(?is)<main\b[^>]*>(.*)</main>", r'(?is)<[^>]+role="main"[^>]*>(.*)', r"(?is)<body\b[^>]*>(.*)</body>"):
        oMatch = re.search(sPattern, sHtml)
        if oMatch and len(re.sub(r"<[^>]+>", "", oMatch.group(1)).strip()) > 400: return oMatch.group(1)
    return sHtml


def cleanAddress(sUrl):
    """An address without its tracking codes (utm_ and the like); every other part kept."""
    try: oParts = urllib.parse.urlsplit(sUrl)
    except ValueError: return sUrl   # a malformed address is left as it is, never the cause of a lost document
    if not oParts.query: return sUrl
    lKeep = [(k, v) for k, v in urllib.parse.parse_qsl(oParts.query, keep_blank_values=True) if not re.match(r"(?i)^(utm_|fbclid$|gclid$|mc_)", k)]
    return urllib.parse.urlunsplit(oParts._replace(query=urllib.parse.urlencode(lKeep)))


def pageToMarkdown(sHtml, sTitle, sUrl):
    """One structured, cleaned Markdown document: front matter, one level-one heading, a source note, the page."""
    sMd = subprocess.run(["pandoc", "-f", "html", "-t", "markdown-raw_html-native_divs-native_spans-fenced_divs-bracketed_spans-link_attributes-header_attributes-smart",
                          "--wrap=none"], input=mainContent(sHtml), capture_output=True, text=True, encoding="utf-8", check=True).stdout
    sMd = re.sub(r"!\[\]\([^)]*\)", "", sMd)                      # pictures with no text
    sMd = re.sub(r"(?m)^\[\s*\]\([^)]*\)\s*$", "", sMd)           # links with no text
    lLevels = [len(m.group(1)) for m in re.finditer(r"(?m)^(#{1,6}) ", sMd)]
    iShift = (2 - min(lLevels)) if lLevels else 0
    sMd = re.sub(r"(?m)^(#{1,6}) ", lambda m: "#" * min(6, max(2, len(m.group(1)) + iShift)) + " ", sMd)
    # The page's own title heading, now at level 2, repeats the document's title, perhaps with a volume or a site name
    # after it: dropped. Tracking codes leave every address, and a link to a part of the page the cleaning removed
    # keeps its words without the link.
    sMd = re.sub(r"(?m)^## " + re.escape(sTitle) + r"\b.*$\n?", "", sMd, count=1)
    sMd = re.sub(r"https?://[^)\s\"]+", lambda m: cleanAddress(m.group(0)), sMd)
    setIds = set(re.findall(r"\{#([^}]+)\}", sMd)) | set(re.sub(r"[^a-z0-9 -]", "", h.lower()).strip().replace(" ", "-") for h in re.findall(r"(?m)^#+ (.+)$", sMd))
    sMd = re.sub(r"\[([^\]]*)\]\(#([^)\s]+)[^)]*\)", lambda m: m.group(0) if m.group(2) in setIds else m.group(1), sMd)
    sMd = re.sub(r"\n{3,}", "\n\n", sMd).strip()
    sToday = datetime.date.today().strftime("%d %B %Y").lstrip("0")
    return ('---\ntitle: "%s"\nlang: en-US\n---\n\n# %s\n\n*Fetched %s from [the publisher\'s page](%s). The page\'s menus and side panels are left out.*\n\n%s\n'
            % (sTitle.replace('"', "'"), sTitle, sToday, sUrl, sMd))


def writeText(sPath, sText):
    io.open(sPath, "wb").write(b"\xef\xbb\xbf" + sText.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))


def getOne(sName, dDoc, sOut):
    """Fetches one document. Returns a short line for the console."""
    sUrl, sTitle = dDoc.get("url", ""), dDoc.get("title", sName.replace("_", " "))
    binPage, sFinal, sType = fetch(sUrl)
    sHtml = binPage.decode("utf-8", "replace")
    if dDoc.get("files"):
        lLinks = fileLinks(sHtml, sFinal, dDoc["files"])
        log("%s: %d matching file link%s: %s" % (sName, len(lLinks), "" if len(lLinks) == 1 else "s", "; ".join(t[0] for t in lLinks)))
        if lLinks:
            lsSaved = []
            for sHref, sText, sExtension in newestOf(lLinks):
                binFile, sFinalFile, sFileType = fetch(sHref)
                sPath = os.path.join(sOut, sName + sExtension)
                if os.path.exists(sPath) and sPath in lsSaved: sPath = os.path.join(sOut, sName + "-" + str(len(lsSaved) + 1) + sExtension)
                open(sPath, "wb").write(binFile)
                lsSaved.append(sPath)
                log("SAVED %s from %s (%s)" % (sPath, sHref, sText))
            return "%s: %s." % (sTitle, ", ".join(os.path.basename(s) for s in lsSaved))
        log("%s: no PDF or Word file matched, so the page is converted" % sName)
    sMd = pageToMarkdown(sHtml, sTitle, sUrl)
    sMdPath = os.path.join(sOut, sName + ".md")
    writeText(sMdPath, sMd)
    sHtm = subprocess.run(["pandoc", sMdPath, "-f", "markdown", "-s", "-M", "title=", "-M", "pagetitle=" + sTitle, "-M", "lang=en-US"],
                          capture_output=True, text=True, encoding="utf-8", check=True).stdout
    writeText(os.path.join(sOut, sName + ".htm"), sHtm)
    iWords = len(re.findall(r"\w+", sMd))
    log("CONVERTED %s: %d words" % (sMdPath, iWords))
    return "%s: %s.md and .htm, %s words." % (sTitle, sName, format(iWords, ","))


def main():
    sRoot = os.getcwd()
    sKit = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sList = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(sKit, "data", "getDocs.inix")
    sOut = os.path.join(sRoot, "results", "getDocs")
    for sFolder in (sOut, os.path.join(sRoot, "logs")): os.makedirs(sFolder, exist_ok=True)
    sLogPath = os.path.join(sRoot, "logs", "%s-getDocs-%s.log" % (os.path.basename(sRoot.rstrip("\\/")) or "getDocs", datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))
    dState["fLog"] = io.open(sLogPath, "w", encoding="utf-8-sig", newline="\r\n")
    log("getDocs.py (HomerDev 1.216.0); script %s; Python %s on %s; cwd %s; command line %s" % (
        os.path.abspath(__file__), platform.python_version(), platform.platform(), sRoot, " ".join(sys.argv)))
    log("settings: list %s; output %s" % (sList, sOut))
    iResult = 0
    if not shutil.which("pandoc"):
        say("Pandoc is needed to convert pages; the kit's build installs it. Run build_release in the kit first.")
        return 1
    lDocs = readList(sList)
    say("Fetching %d document%s into %s." % (len(lDocs), "" if len(lDocs) == 1 else "s", sOut))
    for sName, dDoc in lDocs:
        try:
            say(getOne(sName, dDoc, sOut))
        except Exception as oError:
            iResult = 1
            log("FAILED %s: %s: %s" % (sName, type(oError).__name__, oError))
            say("%s: could not be fetched (%s). The log has the details." % (dDoc.get("title", sName), oError))
        time.sleep(1)
    say("Log: " + sLogPath)
    log("RUN ENDED exit %d" % iResult)
    dState["fLog"].close()
    return iResult


if __name__ == "__main__":
    sys.exit(main())
