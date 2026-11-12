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
    # WHAT THE PUBLISHER HIDES FROM SCREEN READERS STAYS HIDDEN (1.218.0): an element marked aria-hidden="true" --
    # Smashing Magazine's "(Large preview)" figure captions, eighteen of them -- is not meant to be read.
    sHtml = re.sub(r'(?is)<(\w+)\b[^>]*\baria-hidden\s*=\s*["\']true["\'][^>]*>.*?</\1\s*>', "", sHtml)
    for sTag in lsDropTags: sHtml = re.sub(r"(?is)<%s\b.*?</%s\s*>" % (sTag, sTag), "", sHtml)
    sHtml = re.sub(r'(?is)<(div|section)\b[^>]*(?:class|id)="[^"]*(?:cookie|share|social|related|comment|newsletter|subscribe|sidebar|breadcrumb|advert|promo)[^"]*"[^>]*>', "<div>", sHtml)
    # THE MOST SUBSTANTIAL PART WINS (1.217.0). Vispero's guide sits in a page whose only <article> elements are cards
    # for related posts, and taking everything from the first card to the last kept 141 words of cards and none of the
    # guide. Each article alone, the main element and the body are weighed by their text; the largest article wins
    # unless main holds half again as much, and inside the winner, a card -- an article of under 300 characters -- goes.
    def textOf(sPart): return len(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", sPart)).strip())
    lsArticles = re.findall(r"(?is)<article\b[^>]*>(.*?)</article>", sHtml)
    sBest = max(lsArticles, key=textOf) if lsArticles else ""
    for sPattern in (r"(?is)<main\b[^>]*>(.*)</main>", r'(?is)<[^>]+role="main"[^>]*>(.*)', r"(?is)<body\b[^>]*>(.*)</body>"):
        oMatch = re.search(sPattern, sHtml)
        if oMatch and textOf(oMatch.group(1)) > 1.5 * textOf(sBest): sBest = oMatch.group(1); break
    sBest = sBest or sHtml
    return re.sub(r"(?is)<article\b[^>]*>(.*?)</article>", lambda m: m.group(0) if textOf(m.group(1)) >= 300 else "", sBest)


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
    # PICTURES AS WORDS (1.218.0): a document read by ear has no use for an image link. A picture with real
    # alternative text keeps it as a line, "Picture: ..."; one with none, or with a link in place of text (Smashing
    # Magazine's "Large preview" wrappers), goes, and so does the empty link left around it.
    def picture(m):
        sAlt = m.group(1).strip()
        return "" if (len(sAlt) < 4 or re.search(r"[\[\]()]|https?://", sAlt)) else "*Picture: %s.*" % sAlt.rstrip(".")
    sMd = re.sub(r"!\[((?:[^\[\]]|\[[^\]]*\])*)\]\([^)]*\)", picture, sMd)
    sMd = re.sub(r"\[\s*\]\([^)]*\)", "", sMd)                       # links left with no text
    # A SIDE PANEL INSIDE THE ARTICLE (1.218.0): "About The Author", "Email Newsletter", "Related", "Share" and the
    # like are dropped with everything under them, up to the next heading of their level or higher.
    lsLines, lsOut, iSkip = sMd.split("\n"), [], 0
    for sLine in lsLines:
        oHead = re.match(r"^(#{1,6}) (.*)$", sLine)
        if oHead:
            iLevel = len(oHead.group(1))
            if iSkip and iLevel <= iSkip: iSkip = 0
            if not iSkip and re.match(r"(?i)(about the author|email newsletter|newsletter|related (posts|articles|reading)|share( this)?|comments?|further reading)\b", oHead.group(2).strip()):
                iSkip = iLevel
                continue
        if not iSkip: lsOut.append(sLine)
    sMd = "\n".join(lsOut)
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
    # NO SKIPPED LEVEL (1.217.0): with the repeated title gone, the page's headings start at level 2, never 3, so
    # a screen reader's heading levels mean what they say.
    lLevels = [len(m.group(1)) for m in re.finditer(r"(?m)^(#{2,6}) ", sMd)]
    if lLevels and min(lLevels) > 2:
        iUp = min(lLevels) - 2
        sMd = re.sub(r"(?m)^(#{2,6}) ", lambda m: "#" * (len(m.group(1)) - iUp) + " ", sMd)
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
    # A LANDING PAGE CAN LEAD TO THE DOCUMENT (1.217.0): Freedom Scientific's What's New page holds only a version list
    # and a link, "Latest JAWS Enhancements", to the notes themselves. A follow pattern names that link; its page is
    # the one fetched and converted.
    if dDoc.get("follow"):
        for oLink in re.finditer(r'(?is)<a\b[^>]*href\s*=\s*["\']([^"\']+)["\'][^>]*>(.*?)</a>', sHtml):
            sText = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", oLink.group(2)))).strip()
            if re.search(dDoc["follow"], sText, re.I):
                sUrl = urllib.parse.urljoin(sFinal, html.unescape(oLink.group(1)).strip())
                log("%s: following \"%s\" to %s" % (sName, sText, sUrl))
                binPage, sFinal, sType = fetch(sUrl)
                sHtml = binPage.decode("utf-8", "replace")
                break
        else:
            log("%s: no link matched the follow pattern %s; the page itself is used" % (sName, dDoc["follow"]))
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
    # OTHER ADDRESSES, IN ORDER (1.218.0): Freedom Scientific's What's New page builds its notes in the browser, so a
    # plain fetch gets only its frame. When a page gives under 300 words, each address in "also" is tried in turn,
    # and the first that gives a document of that size is kept; when none does, the first result stands.
    if len(re.findall(r"\w+", sMd)) < 300:
        for sAlso in [s.strip() for s in dDoc.get("also", "").split("|") if s.strip()]:
            try:
                binAlso, sFinalAlso, sTypeAlso = fetch(sAlso)
                sMdAlso = pageToMarkdown(binAlso.decode("utf-8", "replace"), sTitle, sAlso)
            except Exception as oError:
                log("%s: also %s failed: %s" % (sName, sAlso, oError)); continue
            log("%s: also %s gave %d words" % (sName, sAlso, len(re.findall(r"\w+", sMdAlso))))
            if len(re.findall(r"\w+", sMdAlso)) >= 300:
                sMd, sUrl = sMdAlso, sAlso
                break
    sMdPath = os.path.join(sOut, sName + ".md")
    writeText(sMdPath, sMd)
    sHtm = subprocess.run(["pandoc", sMdPath, "-f", "markdown", "-s", "-M", "title=", "-M", "pagetitle=" + sTitle, "-M", "lang=en-US"],
                          capture_output=True, text=True, encoding="utf-8", check=True).stdout
    writeText(os.path.join(sOut, sName + ".htm"), sHtm)
    iWords = len(re.findall(r"\w+", sMd))
    log("CONVERTED %s: %d words" % (sMdPath, iWords))
    sThin = " That is thin for a document; the log says which part of the page was kept, and a follow pattern may be needed." if iWords < 300 else ""
    return "%s: %s.md and .htm, %s words.%s" % (sTitle, sName, format(iWords, ","), sThin)


def main():
    sRoot = os.getcwd()
    # Run from inside a project's own folder -- logs, results, notes -- the project is the folder above (1.217.0): a run
    # in C:\\HomerDev\\logs had put its documents in logs\\results\\getDocs and its log in logs\\logs.
    if os.path.basename(sRoot.rstrip("\\/")).lower() in ("configs", "data", "help", "logs", "notes", "results", "scripts", "templates", "work"):
        sRoot = os.path.dirname(sRoot.rstrip("\\/"))
    sKit = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sList = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(sKit, "data", "getDocs.inix")
    sOut = os.path.join(sRoot, "results", "getDocs")
    for sFolder in (sOut, os.path.join(sRoot, "logs")): os.makedirs(sFolder, exist_ok=True)
    sLogPath = os.path.join(sRoot, "logs", "%s-getDocs-%s.log" % (os.path.basename(sRoot.rstrip("\\/")) or "getDocs", datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))
    dState["fLog"] = io.open(sLogPath, "w", encoding="utf-8-sig", newline="\r\n")
    log("getDocs.py (HomerDev 1.218.0); script %s; Python %s on %s; cwd %s; command line %s" % (
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
