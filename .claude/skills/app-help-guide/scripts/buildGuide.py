r"""buildGuide.py version 2

Turns a folder of harvested pages into one help guide: a Markdown file and its
HTML pair.

HOW TO USE IT. A collection's own build runs it (version 2, 11 November 2026):

    build                          C:\AppHelpGuides\build.cmd, the first step of build_release
    buildGuide --build <collection>      what that build.cmd runs

and by hand:

    buildGuide [harvests] [guides] [products...] [--changed]

With --build, the collection's harvests are its data\harvests folder and its guides
are at its top. The build first settles the old layout into the Homer one, then
builds every guide whose harvest is newer than the guide, then has the kit's
fixPages build the .htm of every guide that changed. Each run writes its own log,
logs\<Collection>-buildGuide-<stamp>.log, in UTF-8
with a byte order mark and Windows line endings. A gate failure fails the run, so
build_release stops before anything is pushed.

Naming products builds only those, by product name or guide file name, and always
rebuilds them, so "build GoodMaps" brings a guide up to date after its reader changes.

Each product has a reader function here that knows the shape of that
publisher's pages — where the article's body is, where its title is, and how
its categories are named. To add a product, write a reader and add one line to
the build list. The readers already here cover most shapes you will meet:
Zendesk listings, Intercom, Google help centres, Microsoft support, Sphinx
manuals, VitePress and plain documentation sites.

THE GUIDE FORMAT, THE CATEGORY RULES AND THE GATES are in
references/guide-format.md.
"""

import datetime, html, html.parser, io, json, logging, os, platform, re, shutil, subprocess, sys, time, urllib.parse

iMinCategory = 2
sBom = "\ufeff"
sEncoding = "utf-8-sig"
sMiscellaneous = "Miscellaneous"
sNewLine = "\r\n"

lLitterExact = ["print", "home", "sign in", "back to home", "all collections", "table of contents",
                  "skip to main content", "powered by", "powered by intercom", "we run on fin",
                  "return to top", "related articles", "was this helpful", "submit a request"]
lFeedback = ["was this article helpful", "was this page helpful", "was this helpful",
               "was this information helpful", "did this answer your question",
               "did you find it helpful", "how can we improve it",
               "how satisfied are you with this reply", "provide feedback about this article",
               "out of found this helpful", "of people found this helpful"]
lFeedbackAnswers = ["yes", "no", "yes no", "disappointed", "neutral", "smiley", "share"]
lLitterPrefix = ["did this answer your question", "was this article helpful", "still need help",
                   "have more questions", "use of this site constitutes acceptance", "all rights reserved"]


reBareDomain = re.compile(r"^(?:www\.)?[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:ai|app|au|ca|co|com|de|dev|edu|fr|gov|info|io|me|net|org|tv|uk|us)(?:[/?#]|$)", re.I)


def normalizeHref(sUrl, sBaseUrl=""):
    """THE ADDRESS A LINK SHOULD CARRY, OR "" FOR NONE (12 October 2026, from an audit). A guide is read offline or
    from GitHub Pages, where an address relative to the publisher's article resolves against the wrong site: 30,523
    such links led nowhere across the collection. With the article's own address, a relative link is resolved exactly;
    without it, the link is dropped and its words kept. A bare domain ("bbc.com/subscribe") gains https://, and an
    address that carries Markdown inside it ("[angi.com](https://...)", even percent-encoded) yields the address inside.
    Mail and phone links are kept as they are."""
    sUrl = (sUrl or "").strip()
    if not sUrl: return ""
    sDecoded = urllib.parse.unquote(sUrl)
    oInside = re.search(r"\]\((https?://[^)\s]+)\)", sDecoded)
    if oInside: return oInside.group(1)
    if re.match(r"(?i)(https?:|mailto:|tel:)", sUrl): return sUrl
    if sUrl.startswith("//"): return "https:" + sUrl
    if sUrl.startswith("#"): return ""
    if sBaseUrl and re.match(r"(?i)https?://", sBaseUrl): return urllib.parse.urljoin(sBaseUrl, sUrl)
    if reBareDomain.match(sUrl) and not re.match(r"(?i)[^/]+\.(php|aspx?|html?|jsp)(?:[?#]|$)", sUrl): return "https://" + sUrl
    return ""


class markdownParser(html.parser.HTMLParser):
    """Turns a fragment of help markup into Markdown lines."""

    def __init__(self, iBaseLevel, sBaseUrl=""):
        super().__init__(convert_charrefs=True)
        self.sBaseUrl = sBaseUrl
        self.iBaseLevel = iBaseLevel
        self.iHeading = 0
        self.iPre = 0
        self.lLines = []
        self.lLinkStack = []
        self.lListStack = []
        self.lSkip = []
        self.sBuffer = ""

    def emit(self, sText):
        self.lLines.append(sText)
        return True

    def flush(self):
        # Collapse EVERY kind of whitespace, not only spaces and tabs. A heading
        # whose text carries a newline (Amazon wraps long titles in its markup)
        # produced a line the renumberer could not match, and the guide kept a
        # level-one heading in the middle of an article.
        sText = re.sub(r"\s+", " ", self.sBuffer).strip()
        # A dollar sign opens mathematics in Pandoc, but only a PAIR of them does
        # any harm, and a lone price ("$5 a month") is safe. mpv's manual writes
        # properties as ${playlist-count}, which Pandoc read as a broken formula.
        # So dollars are escaped only where they could actually pair up.
        if sText.count("$") > 1 or "${" in sText: sText = sText.replace("$", "\\$")
        self.sBuffer = ""
        if not sText: return False
        if self.iHeading:
            iLevel = min(6, self.iHeading + self.iBaseLevel)
            return self.emit("") and self.emit("#" * iLevel + " " + sText) and self.emit("")
        # A publisher writing ABOUT Markdown puts Markdown in its prose. Reddit's
        # help shows "# This is a heading" and fenced blocks as examples; left
        # alone they become real headings and unbalanced fences in the guide.
        sText = sText.replace("```", "\\`\\`\\`")
        sText = re.sub(r"^(#{1,6})(\s)", r"\\\1\2", sText)
        if self.lListStack:
            sLead = "    " * (len(self.lListStack) - 1)
            return self.emit(sLead + "- " + sText)
        return self.emit(sText) and self.emit("")

    def handle_starttag(self, sTag, lAttributes):
        dAttributes = dict(lAttributes)
        if sTag in ("script", "style", "svg", "noscript", "nav", "footer", "aside", "form", "button", "template", "head", "select"):
            self.lSkip.append(sTag)
            return True
        if self.lSkip: return True
        if sTag == "pre":
            self.flush()
            self.iPre += 1
            return self.emit("")
        if self.iPre:
            if sTag == "br": self.sBuffer += "\n"
            return True
        if sTag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.flush()
            self.iHeading = int(sTag[1])
            return True
        if sTag in ("ul", "ol"):
            self.flush()
            self.lListStack.append(sTag)
            return True
        if sTag in ("li", "p", "div", "section", "article", "tr", "br", "blockquote", "dt", "dd", "table", "th", "td"):
            self.flush()
            return True
        if sTag == "a":
            self.lLinkStack.append((len(self.sBuffer), dAttributes.get("href", "")))
            return True
        if sTag == "code":
            self.sBuffer += "`"
            return True
        return True

    def handle_endtag(self, sTag):
        if self.lSkip:
            if self.lSkip[-1] == sTag: self.lSkip.pop()
            return True
        if sTag == "pre" and self.iPre:
            self.iPre -= 1
            sCode = self.sBuffer.strip("\n").rstrip()
            self.sBuffer = ""
            if not sCode.strip(): return True
            if re.fullmatch(r"[\d\s]+", sCode): return True
            # An INDENTED code block rather than a fenced one. A publisher writing
            # about Markdown puts fences inside its own examples, and no fence
            # length is safe against that; indentation cannot be broken from
            # inside, and a screen reader reads it the same either way.
            self.emit("")
            for sCodeLine in sCode.split("\n"): self.emit("    " + sCodeLine.rstrip())
            return self.emit("")
        if self.iPre:
            if sTag == "div" and not self.sBuffer.endswith("\n"): self.sBuffer += "\n"
            return True
        if sTag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.flush()
            self.iHeading = 0
            return True
        if sTag in ("ul", "ol"):
            self.flush()
            if self.lListStack: self.lListStack.pop()
            # A BLANK LINE AFTER A LIST (17 November 2026). Kickstarter's paragraph after a list landed on the line
            # below the last item, so Markdown made it part of that item. Every guide built from now on gets the gap.
            if not self.lListStack and self.lLines and self.lLines[-1] != "": self.emit("")
            return True
        if sTag in ("li", "p", "div", "section", "article", "tr", "blockquote", "dt", "dd", "table"):
            self.flush()
            return True
        if sTag == "code":
            self.sBuffer += "`"
            return True
        if sTag == "a":
            if not self.lLinkStack: return True
            iStart, sUrl = self.lLinkStack.pop()
            if iStart > len(self.sBuffer): return True
            sVisible = self.sBuffer[iStart:]
            sTrimmed = sVisible.strip()
            if not sUrl or not sTrimmed: return True
            sUrl = normalizeHref(sUrl, self.sBaseUrl)
            if not sUrl: return True
            if sTrimmed.lower().startswith(("http://", "https://", "www.")): return True
            if "[" in sVisible or "]" in sVisible: return True
            iLead = len(sVisible) - len(sVisible.lstrip())
            iTrail = len(sVisible) - len(sVisible.rstrip())
            self.sBuffer = (self.sBuffer[:iStart] + sVisible[:iLead] + "[" + sTrimmed + "](" + sUrl + ")"
                            + (sVisible[len(sVisible) - iTrail:] if iTrail else ""))
            return True
        return True

    def handle_data(self, sText):
        if self.lSkip: return True
        # TEXT THAT NAMES A TAG STAYS TEXT (12 October 2026, from an audit). The parser decodes &lt;h1&gt; into "<h1>",
        # and Markdown passes that on as markup: a publisher's sentence about heading tags gave Calibre five level-one
        # headings and Org Mode a stray one. Outside a code block, a "<" that begins a tag is written as &lt;, which
        # every reader shows as "<". Inside a code block it stays as it is, since there an entity would show literally.
        if not self.iPre: sText = re.sub(r"<(?=[A-Za-z/!?])", "&lt;", sText)
        self.sBuffer += sText
        return True


def readText(sPath):
    """Reads a saved page as text, tolerating a byte order mark."""
    fHandle = io.open(sPath, "r", encoding="utf-8", errors="replace")
    sText = fHandle.read()
    fHandle.close()
    return sText.lstrip(sBom)


def findBalanced(sMarkup, sPattern, sTag):
    """Returns the markup of the first element matching sPattern, brackets balanced."""
    oMatch = re.search(sPattern, sMarkup, re.I)
    if not oMatch: return ""
    iStart = oMatch.start()
    iDepth = 0
    for oToken in re.finditer(r"<(/?)" + sTag + r"(\s[^>]*)?>", sMarkup[iStart:], re.I):
        iDepth = iDepth - 1 if oToken.group(1) else iDepth + 1
        if iDepth == 0: return sMarkup[iStart: iStart + oToken.end()]
    return sMarkup[iStart:]


def toMarkdown(sMarkup, iBaseLevel, sBaseUrl=""):
    """Turns one article body into Markdown lines, furniture removed. sBaseUrl, the article's own address where the
    reader knows it, resolves the publisher's relative links."""
    oParser = markdownParser(iBaseLevel, sBaseUrl)
    oParser.feed(sMarkup)
    oParser.flush()
    return labelAddresses(dropLitter(oParser.lLines))


def dropLitter(lLines):
    """Removes the publisher's furniture by naming the furniture, never by condemning words."""
    lOut = []
    iFeedbackAt = [-1]
    for sLine in lLines:
        # A conditional comment leaves its closing marker behind as ordinary text,
        # and how much of it survives depends on the Python version doing the reading.
        sLine = re.sub(r"(<!--|-->|<!\[endif\]|<!\[if [^\]]*\])", "", sLine)
        if sLine.strip() in ("", "-->", "<!--") and not sLine.strip(): 
            if not lOut or lOut[-1].strip() == "": continue
        # A line that is nothing but a link back to the top of the page is furniture
        # wherever the link happens to point.
        oOnlyLink = re.fullmatch(r"\s*\[([^\]]+)\]\([^\)]*\)\s*", sLine)
        if oOnlyLink and re.sub(r"[^a-z ]", "", oOnlyLink.group(1).lower()).strip() in lLitterExact: continue
        # Collapse the spaces left where digits were removed: "3 out of 7 found
        # this helpful" becomes "out of  found this helpful" with a double space,
        # and no phrase on any list would ever match that.
        sTest = re.sub(r"\s+", " ", re.sub(r"[^a-z ]", "", sLine.strip().lower().lstrip("-# "))).strip()
        bHeading = sLine.strip().startswith("#")
        # A litter list must name the furniture, never condemn a word. A short word
        # is refused only when it is the WHOLE line; a distinctive phrase may open one.
        # AN ARTICLE'S OWN TITLE IS NEVER FURNITURE, whatever it happens to say.
        # Freedom Scientific publishes a page called "Table of Contents", and the
        # litter list ate its heading while the contents list still named it.
        # NO HEADING IS EVER FURNITURE — not an article's title and not a heading
        # inside one. Dropping an inner heading orphans everything beneath it:
        # Udemy's labs article carries its own "Table of Contents" heading, and
        # removing it left the questions under it two levels below their parent.
        # A FEEDBACK WIDGET IS FURNITURE EVEN AS A HEADING. The rule above that
        # no heading is ever furniture was written to protect an article's own
        # title, and it wrongly protected Meta's "Was this article helpful?",
        # which Meta publishes as a level-five heading. This exception is narrow
        # and named: only the phrases on the feedback list, and the Yes and No
        # that follow one within three lines.
        # A count line reads "3 out of 7 found this helpful"; stripping its digits
        # leaves "out of found this helpful", which is why that phrase is on the
        # list in that odd-looking form.
        if sTest and any(sTest.startswith(sPhrase) for sPhrase in lFeedback):
            iFeedbackAt[0] = len(lOut)
            continue
        if sTest in lFeedbackAnswers and iFeedbackAt[0] >= 0 and len(lOut) - iFeedbackAt[0] <= 3: continue
        if sTest and not bHeading and sTest in lLitterExact: continue
        if sTest and not bHeading and any(sTest.startswith(sItem) for sItem in lLitterPrefix): continue
        if sLine.strip() == "" and lOut and lOut[-1].strip() == "": continue
        lOut.append(sLine.rstrip())
    while lOut and lOut[0].strip() == "": lOut.pop(0)
    while lOut and lOut[-1].strip() == "": lOut.pop()
    return lOut


def labelOneAddress(oMatch):
    """Builds the replacement for one address left bare in prose."""
    sUrl = oMatch.group(1).rstrip(".,;:")
    sTail = oMatch.group(1)[len(sUrl):]
    sHost = re.sub(r"^https?://(www\.)?", "", sUrl).split("/")[0]
    return "[" + sHost + "](" + sUrl + ")" + sTail


def labelAddresses(lLines):
    """Replaces a bare address with a link labelled by its host, outside code fences."""
    lOut = []
    bInCode = False
    for sLine in lLines:
        if sLine.strip().startswith("```"):
            bInCode = not bInCode
            lOut.append(sLine)
            continue
        if bInCode or "http" not in sLine:
            lOut.append(sLine)
            continue
        # An address inside backticks is code the reader must type exactly; it is
        # left alone, and only the prose between the backticks is labelled.
        lParts = sLine.split("`")
        for iPart in range(0, len(lParts), 2):
            lParts[iPart] = re.sub(r"(?<![\(\[])(https?://[A-Za-z0-9-]+\.[A-Za-z]{2,}[^\s\)\]<>\"'`]*)",
                                   labelOneAddress, lParts[iPart])
        lOut.append("`".join(lParts))
    return lOut


def balanceFences(lLines):
    """Closes a code fence an article leaves open.

    An article whose fences do not balance poisons everything after it: the
    renumberer believes it is inside code and stops renumbering, and the gates
    disagree with it about where the article's headings are."""
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
    """Renumbers an article's own headings BY NESTING DEPTH, so no level is ever
    skipped however the publisher numbered them. Fenced code is never read."""
    lOut = []
    lStack = []
    iFence = 0
    for sLine in lLines:
        # As in the gates: a fence closes only on a run at least as long as the
        # one that opened it. Reading an inner three-backtick example as a close
        # left the rest of the article unrenumbered.
        oFence = re.match(r"\s*(`{3,})", sLine)
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


def makeAnchor(sTitle):
    """Builds the anchor Pandoc gives a heading.

    PANDOC'S OWN RULE (version 2, 11 November 2026): letters, digits, _ - and . are kept, spaces become hyphens, and
    everything before the first letter goes. Version 1 kept a leading digit and dropped every period, so the contents
    entries for "2D Map View" (GoodMaps) and "Setting up llama.cpp" (AI Content Describer) linked to anchors Pandoc
    never made. The gates compared the contents with this same function, so they could not see it; fixPages counted
    such links as "in-page links to nothing" in the finished page."""
    sAnchor = re.sub(r"[^\w\s.-]", "", sTitle.lower(), flags=re.U)
    sAnchor = re.sub(r"\s+", "-", sAnchor.strip())
    iFirst = next((i for i, sCharacter in enumerate(sAnchor) if sCharacter.isalpha()), len(sAnchor))
    return sAnchor[iFirst:] or "section"


def readManifest(sFolder):
    """Returns file name to address, from the manifest rather than from the file name."""
    dManifest = {}
    sPath = os.path.join(sFolder, "manifest.txt")
    if not os.path.isfile(sPath): return dManifest
    for sLine in readText(sPath).replace("\r", "").split("\n")[1:]:
        lParts = sLine.split("\t")
        if len(lParts) >= 2: dManifest[lParts[1].strip()] = lParts[0].strip()
    return dManifest


def readZendesk(sFolder):
    """Reads a Zendesk estate from its own listings, so nothing depends on a rendered page."""
    dSections, dCategories, lArticles = {}, {}, []
    for sName in os.listdir(sFolder):
        if not sName.endswith(".json"): continue
        dPayload = json.loads(readText(os.path.join(sFolder, sName)))
        for dCategory in dPayload.get("categories", []): dCategories[dCategory["id"]] = dCategory["name"]
        for dSection in dPayload.get("sections", []): dSections[dSection["id"]] = (dSection["name"], dSection.get("category_id"))
    for sName in os.listdir(sFolder):
        if not sName.endswith(".json"): continue
        dPayload = json.loads(readText(os.path.join(sFolder, sName)))
        for dArticle in dPayload.get("articles", []):
            tSection = dSections.get(dArticle.get("section_id"), ("", None))
            sCategory = tSection[0] or dCategories.get(tSection[1], sMiscellaneous) or sMiscellaneous
            # A publisher may leave a section's name as a stray character —
            # iHeartRadio has one called "/". That is not a category name.
            if not re.search(r"\w", sCategory): sCategory = sMiscellaneous
            lArticles.append((sCategory, dArticle["title"], toMarkdown(dArticle.get("body") or "", 0, dArticle.get("html_url") or "")))
    return lArticles


def stripTags(sMarkup):
    """Returns the visible text of a fragment, on one line."""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"(?s)<[^>]+>", " ", sMarkup))).strip()


def readSnopes(sFolder):
    """Snopes writes its whole FAQ as one page: the questions are marked as
    collapsible headings, and the section titles above them are the categories."""
    sPath = os.path.join(sFolder, "www.snopes.com_faqs.html")
    if not os.path.isfile(sPath): return []
    sMarkup = readText(sPath)
    lArticles = []
    sCategory = sMiscellaneous
    lTokens = sorted([(oMatch.start(), "category", stripTags(oMatch.group(1)))
                      for oMatch in re.finditer(r'(?is)<span class="section_title[^"]*">(.*?)</span>', sMarkup)] +
                     [(oMatch.start(), "question", stripTags(oMatch.group(1)))
                      for oMatch in re.finditer(r'(?is)<strong id="faqs_question-\d+"[^>]*>(.*?)</strong>', sMarkup)])
    for iIndex, (iStart, sKind, sText) in enumerate(lTokens):
        if sKind == "category":
            # Snopes prints both "Membership" and "Memberships"; they are one category.
            sCategory = "Membership" if sText.strip().lower() in ("membership", "memberships") else sText
            continue
        iEnd = lTokens[iIndex + 1][0] if iIndex + 1 < len(lTokens) else len(sMarkup)
        sAnswer = findBalanced(sMarkup[iStart:iEnd], r'<div[^>]*class="[^"]*faqs_answer_wrap', "div")
        if not sAnswer: sAnswer = sMarkup[iStart:iEnd]
        lArticles.append((sCategory, sText, toMarkdown(sAnswer, 0)))
    return lArticles


def readNewScientist(sFolder):
    """New Scientist writes one page: an h2 opens a category, and each question is
    a bold line just after a named anchor. The list of links at the top is a
    contents list rather than the answers, so a chunk without a bold line is
    ignored instead of being guessed at."""
    sPath = os.path.join(sFolder, "www.newscientist.com_help.html")
    if not os.path.isfile(sPath): return []
    sMarkup = readText(sPath)
    lTokens = sorted([(oMatch.start(), "category", stripTags(oMatch.group(1)))
                      for oMatch in re.finditer(r"(?is)<h2[^>]*>(.*?)</h2>", sMarkup)] +
                     [(oMatch.start(), "question", "")
                      for oMatch in re.finditer(r'(?is)<a[^>]*class="faq-internal-link"[^>]*>(?:</a>)?', sMarkup)])
    lArticles = []
    sCategory = sMiscellaneous
    for iIndex, (iStart, sKind, sText) in enumerate(lTokens):
        if sKind == "category":
            if sText: sCategory = sText
            continue
        iEnd = lTokens[iIndex + 1][0] if iIndex + 1 < len(lTokens) else len(sMarkup)
        sChunk = sMarkup[iStart:iEnd]
        oQuestion = re.search(r"(?is)<b>(.*?)</b>", sChunk[:1200])
        if not oQuestion: continue
        sTitle = stripTags(oQuestion.group(1))
        if not sTitle: continue
        lArticles.append((sCategory, sTitle, toMarkdown(sChunk[oQuestion.end():], 0)))
    return lArticles


def readSciAm(sFolder):
    """Scientific American writes one page: an h1 opens a part and an h3 is a topic."""
    sPath = os.path.join(sFolder, "www.scientificamerican.com_contact-us.html")
    if not os.path.isfile(sPath): return []
    sMarkup = readText(sPath)
    lTokens = [(oMatch.start(), oMatch.group(1), stripTags(oMatch.group(2)))
               for oMatch in re.finditer(r"(?is)<h([13])[^>]*>(.*?)</h\1>", sMarkup)]
    lArticles = []
    sCategory = sMiscellaneous
    for iIndex, (iStart, sLevel, sText) in enumerate(lTokens):
        iEnd = lTokens[iIndex + 1][0] if iIndex + 1 < len(lTokens) else len(sMarkup)
        if sLevel == "1":
            sCategory = sText or sCategory
            if sText.lower() in ("contact us",): continue
        sChunk = sMarkup[iStart:iEnd]
        sTitle = sText
        if not sTitle: continue
        lArticles.append((sCategory if sLevel == "3" else "General contact information", sTitle, toMarkdown(sChunk, 0)))
    return lArticles


def readNation(sFolder):
    """The Nation writes two pages: reader help, where each question is an h2, and
    a donation FAQ, where each question is an h3."""
    lArticles = []
    for sName, sCategory, sPattern in [("www.thenation.com_help.html", "Reading and subscriptions", "2"),
                                       ("www.thenation.com_donation_faq.html", "Donations", "3")]:
        sPath = os.path.join(sFolder, sName)
        if not os.path.isfile(sPath): continue
        sMarkup = readText(sPath)
        lTokens = [(oMatch.start(), stripTags(oMatch.group(1)))
                   for oMatch in re.finditer(r"(?is)<h" + sPattern + r"[^>]*>(.*?)</h" + sPattern + ">", sMarkup)]
        for iIndex, (iStart, sTitle) in enumerate(lTokens):
            iEnd = lTokens[iIndex + 1][0] if iIndex + 1 < len(lTokens) else len(sMarkup)
            if not sTitle or sTitle.lower() in ("sections", "the nation", "current issue", "faq", "faqs"): continue
            lArticles.append((sCategory, sTitle, toMarkdown(sMarkup[iStart:iEnd], 0)))
    return lArticles


def readNature(sFolder):
    """Nature's help runs on Freshdesk. The article's own title is an h1 marked as
    the article title, its body is the article element, and its category comes from
    the breadcrumb the publisher prints above it: the LAST crumb before the article
    is the folder, and the one before that is the section."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if "_solutions_articles_" not in sName or not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r'(?is)<h1[^>]*class="[^"]*article__title[^"]*"[^>]*>(.*?)</h1>', sMarkup)
        if not oTitle: continue
        sTitle = stripTags(oTitle.group(1))
        # Read the breadcrumb TRAIL ITSELF, not every link on the page that happens
        # to mention solutions: the language selector does too, and it was filing
        # every article under "English".
        oTrail = re.search(r'(?is)<(ol|ul)[^>]*breadcrumb[^>]*>(.*?)</\1>', sMarkup)
        sTrail = oTrail.group(2) if oTrail else ""
        lCrumbs = [stripTags(sText) for sUrl, sText in
                   re.findall(r'(?is)<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', sTrail)
                   if "/solutions" in sUrl]
        lCrumbs = [s for s in lCrumbs if s and s.lower() not in ("solution home", "nature support")]
        sCategory = lCrumbs[-1] if lCrumbs else sMiscellaneous
        sBody = findBalanced(sMarkup, r'<article[^>]*class="[^"]*article[^"]*"', "article")
        if not sBody: continue
        if not sTitle: continue
        lArticles.append((sCategory, sTitle, toMarkdown(sBody, 0)))
    return lArticles


def readJumpListFaq(sFolder, sFileName, sCategoryDefault=None):
    """Reads the fulfilment host's definition-list FAQ, whichever magazine it is.

    The group a question belongs to CANNOT be read from what precedes it, because
    every group heading sits in a jump list above every answer. The jump list is
    the map: an h4 names a group and the links under it name its questions by
    anchor."""
    sPath = os.path.join(sFolder, sFileName)
    if not os.path.isfile(sPath): return []
    sMarkup = readText(sPath)
    dManifest = readManifest(sFolder)
    sMarkup = absolutize(sMarkup, dManifest.get(sFileName, "https://w1.buysub.com/"))
    dGroups = {}
    lHeadings = [(oMatch.start(), oMatch.end(), stripTags(oMatch.group(1)))
                 for oMatch in re.finditer(r"(?is)<h4[^>]*>(.*?)</h4>", sMarkup)]
    for iIndex, (iStart, iAfter, sGroup) in enumerate(lHeadings):
        iEnd = lHeadings[iIndex + 1][0] if iIndex + 1 < len(lHeadings) else len(sMarkup)
        for oLink in re.finditer(r'(?is)<a[^>]*href="[^"#]*#([^"]+)"', sMarkup[iAfter:iEnd]):
            dGroups.setdefault(oLink.group(1), sGroup.title())
    lTerms = [(oMatch.start(), oMatch.end(), oMatch.group(1)) for oMatch in re.finditer(r"(?is)<dt[^>]*>(.*?)</dt>", sMarkup)]
    lArticles = []
    for iIndex, (iStart, iAfter, sTerm) in enumerate(lTerms):
        iEnd = lTerms[iIndex + 1][0] if iIndex + 1 < len(lTerms) else len(sMarkup)
        sTitle = stripTags(sTerm)
        oAnchor = re.search(r'(?is)name="([^"]+)"', sTerm)
        sCategory = dGroups.get(oAnchor.group(1), sCategoryDefault or sMiscellaneous) if oAnchor else (sCategoryDefault or sMiscellaneous)
        oAnswer = re.search(r"(?is)<dd[^>]*>(.*)", sMarkup[iAfter:iEnd])
        if not oAnswer or not sTitle: continue
        lArticles.append((sCategory, sTitle, toMarkdown(oAnswer.group(1), 0)))
    return lArticles


def readGoodHousekeeping(sFolder):
    """Good Housekeeping's answers sit on the fulfilment host in the same shape as
    Cosmopolitan's."""
    return readJumpListFaq(sFolder, "w1.buysub.com_pubs_HR_GHK_GHK_FAQ.jsp_cds_mag_code-GHK.html")


def readPublicationFaqs(sFolder):
    """Six publications, four page shapes, one folder.

    The New Yorker and Wired print each question in bold inside ordinary prose;
    Esquire and the two Conde Nast pages on the fulfilment host use the
    definition-list shape already known from Cosmopolitan; USA Today publishes a
    short help centre in headings; Macworld and PC World publish one long page
    with almost no structure, which is kept whole."""
    dNames = {"www.newyorker.com_about_faq.html": "The New Yorker",
              "www.wired.com_about_faq.html": "WIRED",
              "www.macworld.com_faq.html": "Macworld",
              "www.pcworld.com_faq.html": "PC World",
              "help.usatoday.com.html": "USA Today"}
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oPageTitle = re.search(r"(?is)<title[^>]*>(.*?)</title>", sMarkup)
        if oPageTitle and stripTags(oPageTitle.group(1)).lower().startswith("error"): continue
        if "buysub.com" in sName:
            sPublication = ("Esquire" if "/ESQ/" in sName or "_ESQ_" in sName
                            else "WIRED" if "_WIR_" in sName else "The New Yorker")
            lParts = [(oMatch.start(), oMatch.end(), stripTags(oMatch.group(1)))
                      for oMatch in re.finditer(r"(?is)<h4[^>]*>(.*?)</h4>", sMarkup)]
            for iIndex, (iStart, iAfter, sTitle) in enumerate(lParts):
                iEnd = lParts[iIndex + 1][0] if iIndex + 1 < len(lParts) else len(sMarkup)
                if not sTitle or sTitle.isupper(): continue
                lBody = toMarkdown(sMarkup[iAfter:iEnd], 0)
                if len(" ".join(lBody).split()) < 12: continue
                lArticles.append((sPublication + " subscriptions", sTitle, lBody))
            if not [t for t in lArticles if t[0].startswith(sPublication)]:
                # Esquire's page is Cosmopolitan's shape, and its group names are
                # generic — "Manage Your Account" says nothing about whose account
                # in a guide covering six publications, so each carries its
                # publication.
                for sCategory, sTitle, lBody in readJumpListFaq(sFolder, sName, sPublication):
                    lArticles.append((sPublication + ": " + sCategory if sCategory != sMiscellaneous else sPublication,
                                      sTitle, lBody))
            continue
        sPublication = dNames.get(sName)
        if not sPublication: continue
        lMarks = [(oMatch.start(), oMatch.end(), stripTags(oMatch.group(2)))
                  for oMatch in re.finditer(r"(?is)<(strong|b)>(.*?)</\1>", sMarkup)]
        lMarks = [tMark for tMark in lMarks if 10 < len(tMark[2]) < 130]
        if len(lMarks) >= 3:
            for iIndex, (iStart, iAfter, sTitle) in enumerate(lMarks):
                iEnd = lMarks[iIndex + 1][0] if iIndex + 1 < len(lMarks) else len(sMarkup)
                lBody = toMarkdown(sMarkup[iAfter:iEnd], 0)
                if len(" ".join(lBody).split()) < 12: continue
                lArticles.append((sPublication, sTitle, lBody))
            continue
        lHeadings = [(oMatch.start(), oMatch.end(), stripTags(oMatch.group(2)))
                     for oMatch in re.finditer(r"(?is)<h([25])[^>]*>(.*?)</h\1>", sMarkup)]
        lHeadings = [tHeading for tHeading in lHeadings if tHeading[2]]
        if len(lHeadings) >= 2:
            for iIndex, (iStart, iAfter, sTitle) in enumerate(lHeadings):
                iEnd = lHeadings[iIndex + 1][0] if iIndex + 1 < len(lHeadings) else len(sMarkup)
                lBody = toMarkdown(sMarkup[iAfter:iEnd], 0)
                if len(" ".join(lBody).split()) < 12: continue
                lArticles.append((sPublication, sTitle, lBody))
            continue
        sBody = findBalanced(sMarkup, r"<main[^>]*>", "main") or findBalanced(sMarkup, r"<body[^>]*>", "body")
        lBody = toMarkdown(sBody, 0) if sBody else []
        if len(" ".join(lBody).split()) >= 60:
            lArticles.append((sPublication, sPublication + " subscriber questions", lBody))
    return lArticles


def readCosmopolitan(sFolder):
    """Cosmopolitan's answers are published by its subscription service as a
    definition list: the term is the question, the description is the answer.

    The group each question belongs to CANNOT be read from what precedes it,
    because every group heading sits in a jump list above every answer. The
    jump list itself is the map: an h4 names a group and the links under it
    name that group's questions by anchor."""
    sPath = os.path.join(sFolder, "w1.buysub.com_pubs_HR_COS_COS_FAQ.jsp_cds_mag_code-COS.html")
    if not os.path.isfile(sPath): return []
    sMarkup = readText(sPath)
    dGroups = {}
    lHeadings = [(oMatch.start(), oMatch.end(), stripTags(oMatch.group(1)))
                 for oMatch in re.finditer(r"(?is)<h4[^>]*>(.*?)</h4>", sMarkup)]
    for iIndex, (iStart, iAfter, sGroup) in enumerate(lHeadings):
        iEnd = lHeadings[iIndex + 1][0] if iIndex + 1 < len(lHeadings) else len(sMarkup)
        for oLink in re.finditer(r'(?is)<a[^>]*href="#([^"]+)"', sMarkup[iAfter:iEnd]):
            dGroups.setdefault(oLink.group(1), sGroup.title())
    lTerms = [(oMatch.start(), oMatch.end(), oMatch.group(1)) for oMatch in re.finditer(r"(?is)<dt[^>]*>(.*?)</dt>", sMarkup)]
    lArticles = []
    for iIndex, (iStart, iAfter, sTerm) in enumerate(lTerms):
        iEnd = lTerms[iIndex + 1][0] if iIndex + 1 < len(lTerms) else len(sMarkup)
        sTitle = stripTags(sTerm)
        oAnchor = re.search(r'(?is)name="([^"]+)"', sTerm)
        sCategory = dGroups.get(oAnchor.group(1), sMiscellaneous) if oAnchor else sMiscellaneous
        oAnswer = re.search(r"(?is)<dd[^>]*>(.*)", sMarkup[iAfter:iEnd])
        if not oAnswer or not sTitle: continue
        lArticles.append((sCategory, sTitle, toMarkdown(oAnswer.group(1), 0)))
    return lArticles


def readMensHealth(sFolder):
    """Men's Health publishes its answers on the same host as Cosmopolitan, but
    in a third shape again: an h3 names a topic and the bold lines under it are
    the questions within that topic."""
    sPath = os.path.join(sFolder, "w1.buysub.com_pubs_HR_MHL_MHL_FAQ.jsp_cds_mag_code-MHL.html")
    if not os.path.isfile(sPath): return []
    sMarkup = readText(sPath)
    dManifest = readManifest(sFolder)
    sMarkup = absolutize(sMarkup, dManifest.get(os.path.basename(sPath), "https://w1.buysub.com/pubs/HR/MHL/"))
    lArticles = []
    lTopics = [(oMatch.start(), oMatch.end(), stripTags(oMatch.group(1)))
               for oMatch in re.finditer(r"(?is)<h3[^>]*>(.*?)</h3>", sMarkup)]
    for iIndex, (iStart, iAfter, sTopic) in enumerate(lTopics):
        iEnd = lTopics[iIndex + 1][0] if iIndex + 1 < len(lTopics) else len(sMarkup)
        sChunk = sMarkup[iAfter:iEnd]
        lQuestions = [(oMatch.start(), oMatch.end(), stripTags(oMatch.group(1)))
                      for oMatch in re.finditer(r"(?is)<strong>(.*?)</strong>", sChunk)]
        if not sTopic: continue
        if not lQuestions:
            lArticles.append(("Subscriber service", sTopic.title(), toMarkdown(sChunk, 0)))
            continue
        sIntro = sChunk[:lQuestions[0][0]]
        if len(stripTags(sIntro).split()) >= 15:
            lArticles.append(("Subscriber service", sTopic.title(), toMarkdown(sIntro, 0)))
        for iQuestion, (iQStart, iQAfter, sQuestion) in enumerate(lQuestions):
            iQEnd = lQuestions[iQuestion + 1][0] if iQuestion + 1 < len(lQuestions) else len(sChunk)
            if not sQuestion: continue
            lArticles.append((sTopic.title(), sQuestion, toMarkdown(sChunk[iQAfter:iQEnd], 0)))
    return lArticles


def readPoe(sFolder):
    """Poe publishes only five help articles, but each is a whole FAQ: eighty-six
    questions between them. Splitting each FAQ at its own question headings turns
    five unnavigable walls into a volume a reader can jump around in, with each
    FAQ's title becoming the category.

    The level to split at is the one the article uses MOST, since Poe's tax
    article groups its questions under headings of a higher level and its
    questions sit a level below."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".json"): continue
        dPayload = json.loads(readText(os.path.join(sFolder, sName)))
        for dArticle in dPayload.get("articles", []):
            sBody = dArticle.get("body") or ""
            sTitle = stripTags(dArticle.get("title") or "")
            lHeadings = re.findall(r"(?is)<h([1-6])[^>]*>", sBody)
            if not lHeadings:
                lArticles.append(("Miscellaneous", sTitle, toMarkdown(sBody, 0)))
                continue
            sLevel = max(set(lHeadings), key=lHeadings.count)
            lParts = [(oMatch.start(), oMatch.end(), stripTags(oMatch.group(1)))
                      for oMatch in re.finditer(r"(?is)<h" + sLevel + r"[^>]*>(.*?)</h" + sLevel + ">", sBody)]
            sIntro = sBody[:lParts[0][0]]
            if len(stripTags(sIntro).split()) >= 25:
                lArticles.append((sTitle, sTitle + " — introduction", toMarkdown(sIntro, 0)))
            for iIndex, (iStart, iAfter, sQuestion) in enumerate(lParts):
                iEnd = lParts[iIndex + 1][0] if iIndex + 1 < len(lParts) else len(sBody)
                if not sQuestion: continue
                lArticles.append((sTitle, sQuestion, toMarkdown(sBody[iAfter:iEnd], 0)))
    return lArticles


def readFireTv(sFolder):
    """Amazon's help pages: the article is the cs-help-content block, its title is
    the page's h1, and its category is THE LAST CRUMB of the trail Amazon prints
    above it — "Fire TV Remotes", "Get Started with Fire TV" and so on.

    A page whose trail never mentions Fire TV was saved by the crawl (a page is
    always saved, only its links are gated) but does not belong in a Fire TV
    guide, so it is set aside here rather than filed under something invented."""
    lArticles = []
    iSetAside = 0
    iLicences = 0
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        oTrail = re.search(r'(?is)<div class="cs-help-breadcrumb"[^>]*>(.*)', sMarkup)
        sBody = findBalanced(sMarkup, r'<div[^>]*class="[^"]*cs-help-content[^"]*"', "div")
        if not oTitle or not sBody: continue
        sTitle = stripTags(oTitle.group(1))
        lCrumbs = [stripTags(sCrumb) for sCrumb in re.findall(r"(?is)<a[^>]*>(.*?)</a>", oTrail.group(1)[:3000])] if oTrail else []
        lCrumbs = [sCrumb for sCrumb in lCrumbs if sCrumb]
        sCategory = lCrumbs[-1] if lCrumbs else sMiscellaneous
        sWhole = " ".join(lCrumbs) + " " + sTitle
        if not re.search(r"(fire tv|fire stick|firestick|recast)", sWhole, re.I):
            iSetAside += 1
            continue
        # THE KINDLE LESSON AGAIN: Amazon publishes the open-source licences for
        # its software AS HELP ARTICLES. "Legal Notices for Fire TV Recast" alone
        # runs to 147,707 words of package names and licence text — half this
        # guide. Safety and compliance pages are KEPT; they are real device
        # documentation. Only the licence dumps go.
        if re.match(r"(?i)^legal notices\b", sTitle):
            iLicences += 1
            continue
        lArticles.append((sCategory, sTitle, toMarkdown(sBody, 0)))
    logging.info("Fire TV: %d pages set aside because neither their title nor their trail names Fire TV", iSetAside)
    logging.info("Fire TV: %d open-source licence pages left out", iLicences)
    return lArticles


def readRollingStone(sFolder):
    """Rolling Stone's FAQ pages carry the publisher's news headlines in a sidebar
    at the same heading level as their own questions, so the questions are taken
    from the numbered ones — "1. How do I access content" — and the page's own h1
    names the group."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        if not oTitle: continue
        sCategory = stripTags(oTitle.group(1))
        lTokens = [(oMatch.start(), oMatch.end(), stripTags(oMatch.group(1)))
                   for oMatch in re.finditer(r"(?is)<h3[^>]*>(.*?)</h3>", sMarkup)]
        lQuestions = [tToken for tToken in lTokens if re.match(r"^\d+\.", tToken[2].strip())]
        if lQuestions:
            for iIndex, (iStart, iAfter, sTitle) in enumerate(lQuestions):
                iEnd = lTokens[[t[0] for t in lTokens].index(iStart) + 1][0] if [t[0] for t in lTokens].index(iStart) + 1 < len(lTokens) else len(sMarkup)
                sTitle = re.sub(r"^\d+\.\s*", "", sTitle).strip()
                if not sTitle: continue
                lArticles.append((sCategory, sTitle, toMarkdown(sMarkup[iAfter:iEnd], 0)))
            continue
        sBody = findBalanced(sMarkup, r'<article[^>]*>', "article") or findBalanced(sMarkup, r"<body[^>]*>", "body")
        if sBody: lArticles.append(("Customer service", sCategory, toMarkdown(sBody, 0)))
    return lArticles


def readAirbnb(sFolder):
    """Airbnb's help articles: the title is the h1 and the body is everything
    after it in the page. Its category is the audience line printed above the
    heading — "Home host", "Guest", "Experience host" — which is the only
    grouping Airbnb offers a reader."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if "_help_article_" not in sName or not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        if not oTitle: continue
        sTitle = stripTags(oTitle.group(1))
        if not sTitle: continue
        sBefore = sMarkup[:oTitle.start()]
        sCategory = sMiscellaneous
        oAudience = re.search(r"(?is)•\s*([A-Za-z][A-Za-z ]{2,30})</div>", sBefore[-4000:])
        if oAudience: sCategory = oAudience.group(1).strip().title()
        sBody = sMarkup[oTitle.end():]
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 25: continue
        lArticles.append((sCategory, sTitle, lBody))
    return lArticles


oVerizonDevice = re.compile(r"(apple|samsung|google|motorola|pixel|iphone|ipad|galaxy|watch|tablet|kyocera|nokia|orbic|tcl|razr|blackberry|sonim|schok|jitterbug|hotspot|inseego|moto|nighthawk|verizon jetpack)", re.I)


def readVerizonDevices(sFolder):
    """The per-handset half of Verizon's knowledge base."""
    return [tArticle for tArticle in readVerizon(sFolder) if oVerizonDevice.search(tArticle[0])]


def readVerizonService(sFolder):
    """Everything in Verizon's knowledge base that is NOT about one handset:
    plans, billing, accounts, home internet, the network, international use and
    accessibility."""
    return [tArticle for tArticle in readVerizon(sFolder) if not oVerizonDevice.search(tArticle[0])]


def readVerizon(sFolder):
    """Verizon's knowledge base: the article is the topic block, its title is the
    h1 inside it (which Verizon assembles from two spans, so the whitespace
    matters), and the category is the last crumb of its trail."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        if not oTitle: continue
        sTitle = stripTags(oTitle.group(1))
        sBody = (findBalanced(sMarkup, r'<div[^>]*class="BodyContentSection"', "div")
                 or findBalanced(sMarkup, r"<main[^>]*>", "main"))
        if not sBody or not sTitle: continue
        sCategory = sMiscellaneous
        oTrail = re.search(r'(?is)<(nav|ol|ul)[^>]*breadcrumb[^>]*>(.*?)</\1>', sMarkup)
        if oTrail:
            lCrumbs = [stripTags(sCrumb) for sCrumb in re.findall(r"(?is)<a[^>]*>(.*?)</a>", oTrail.group(2))]
            lCrumbs = [sCrumb for sCrumb in lCrumbs if sCrumb and sCrumb.lower() not in ("home", "support", "verizon")]
            if lCrumbs: sCategory = lCrumbs[-1]
        lArticles.append((sCategory, sTitle, toMarkdown(sBody, 0)))
    return lArticles


def readGoogleMeet(sFolder):
    """Google's help centre: the article is the article element, its title is the
    h1 inside it, and its category is the FIRST crumb of the trail — the topic the
    article sits under, "Host controls" rather than the article's own name.

    Google publishes the same article once per platform and the address says which
    in its co= field, so the platform is added to the title: a reader searching for
    the Android instructions finds them by name rather than opening three copies."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if "_answer_" not in sName or not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        sBody = findBalanced(sMarkup, r'<article[^>]*class="[^"]*article[^"]*"', "article")
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        if not sBody or not oTitle: continue
        sTitle = stripTags(oTitle.group(1))
        if not sTitle: continue
        lCrumbs = [stripTags(sCrumb) for sCrumb in re.findall(r'(?is)<li[^>]*breadcrumb[^>]*>(.*?)</li>', sMarkup)]
        lCrumbs = [sCrumb for sCrumb in lCrumbs if sCrumb and sCrumb.lower() != sTitle.lower()]
        sCategory = lCrumbs[0] if lCrumbs else sMiscellaneous
        # Google leaves 53 of these articles with no topic crumb at all, which
        # buries Lookout, Live Transcribe, braille and the display settings in
        # Miscellaneous. Where the trail says nothing, the article's own title
        # does: it names its subject in its first words.
        if sCategory == sMiscellaneous:
            for sWords, sLabel in [
                    (r"lookout", "Lookout: Explore your surroundings"),
                    (r"braille|brailleback", "Braille"),
                    (r"live transcribe|sound notification|live caption|caption", "Live Transcribe and captions"),
                    (r"hearing aid|hearing device|audio|mono|volume", "Hearing"),
                    (r"magnif|colou?r|contrast|text & display|display size|font", "Seeing the screen"),
                    (r"talkback", "TalkBack: Hear your screen read out loud"),
                    (r"label|clickable|touch target|contrast ratio|view |element", "Making an app accessible"),
                    (r"voice access", "Voice Access: Control a device with your voice"),
                    (r"switch|autoclick|dwell|action", "Switches and timing")]:
                if re.search(sWords, sTitle, re.I):
                    sCategory = sLabel
                    break
        oPlatform = re.search(r"(?i)Platform_?3D([A-Za-z]+)", sName)
        if oPlatform:
            sPlatform = {"desktop": "Computer", "android": "Android", "ios": "iPhone and iPad",
                         "iphone": "iPhone and iPad"}.get(oPlatform.group(1).lower(), oPlatform.group(1))
            sTitle = sTitle + " (" + sPlatform + ")"
        lArticles.append((sCategory, sTitle, toMarkdown(sBody, 0)))
    return lArticles


def readZendeskTree(sFolder):
    """A Zendesk estate's articles with where each sits: (category, top section, section, title, body markup, url).
    The top section is the outermost section above the article, followed through parent_section_id, so Box's
    "Getting Started with Box Drive" is found under "Box Drive". Each article once, by its id."""
    dSections, dCategories, dArticles = {}, {}, {}
    lPayloads = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".json"): continue
        dPayload = json.loads(readText(os.path.join(sFolder, sName)))
        lPayloads.append(dPayload)
        for dCategory in dPayload.get("categories", []): dCategories[dCategory["id"]] = dCategory["name"]
        for dSection in dPayload.get("sections", []):
            dSections[dSection["id"]] = (dSection["name"], dSection.get("category_id"), dSection.get("parent_section_id"))
    for dPayload in lPayloads:
        for dArticle in dPayload.get("articles", []):
            if dArticle.get("draft") or dArticle["id"] in dArticles: continue
            iSection = dArticle.get("section_id")
            iTop, setVisited = iSection, set()
            while iTop in dSections and dSections[iTop][2] in dSections and iTop not in setVisited:
                setVisited.add(iTop)
                iTop = dSections[iTop][2]
            tTop = dSections.get(iTop, ("", None, None))
            dArticles[dArticle["id"]] = (dCategories.get(tTop[1], ""), tTop[0], dSections.get(iSection, ("",))[0],
                                         dArticle["title"], dArticle.get("body") or "", dArticle.get("html_url") or "")
    return list(dArticles.values())


def buildFromTree(sFolder, sProduct, fPlace):
    """Turns a Zendesk tree into articles. fPlace(category, top section, section, title) returns the guide's
    category for an article, or "" to leave it out; what is left out is counted by its reason in the log."""
    lArticles, dLeftOut = [], {}
    for sCategory, sTop, sSection, sTitle, sBody, sUrl in readZendeskTree(sFolder):
        sPlace = fPlace(sCategory, sTop, sSection, sTitle)
        sReason = "%s / %s" % (sCategory, sTop)
        # The collection's surfaces are Windows, the web, iPhone and iPad and Alexa: Android-only articles go.
        if sPlace and re.search(r"(?i)\bandroid\b", sSection + " " + sTitle) and not re.search(r"(?i)(iphone|ipad|\bios\b)", sTitle):
            sPlace, sReason = "", "Android only"
        if not sPlace:
            dLeftOut[sReason] = dLeftOut.get(sReason, 0) + 1
            continue
        lArticles.append((sPlace, sTitle, toMarkdown(sBody, 0, sUrl)))
    logging.info("%s: %d articles kept; %d left out: %s", sProduct, len(lArticles), sum(dLeftOut.values()),
                 "; ".join("%s %d" % (s, dLeftOut[s]) for s in sorted(dLeftOut)))
    return lArticles


# BOX (15 November 2026): 2,883 articles, of which a person who keeps, shares and signs files in Box needs about a
# third. Left out, as Bitwarden's administrator half and RIM's change log were: release notes and announcements (1,729
# articles of version history); the administrator's console and the products only an administrator runs (Admin Tools,
# Shield, Governance, Compliance, Archive, Shuttle for migrations, the developer Platform and the MCP server); the
# integrations with business systems (Salesforce, NetSuite, ServiceNow, Workday) and the partner programs; Box's
# training and certification pages; and the AI agent templates. Categories are Box's own products, its guides and its
# troubleshooting for each kept together, and every integration a person uses (Office, Teams, Slack, Google, Outlook,
# Zoom, Adobe, Copilot) is under one heading.
lBoxLeftOutTops = ["announcements", "release notes", "box admin tools", "box shield", "box governance", "box compliance",
                   "box archive", "box shuttle", "box platform", "box mcp server", "box for salesforce",
                   "box for oracle netsuite", "box for servicenow", "box for workday", "box partner programs",
                   "box security integrations", "virtual environments", "getting started for admins",
                   "ai agent templates", "how it works", "box certified professional", "box education",
                   "box guidance services", "box local", "intelligent content certification"]


def placeBox(sCategory, sTop, sSection, sTitle):
    sTopLower = sTop.lower()
    if sTopLower in lBoxLeftOutTops: return ""
    if sCategory == "Integrations": return "Box with other apps"
    if sCategory in ("Account and Billing", "Working with Box Support"): return "Your account, billing and support"
    if sCategory == "Getting started": return "Getting started"
    if sCategory == "Learning": return "Learning guides"
    if sTopLower == "box fundamentals": return "Using Box: files, folders and sharing"
    if sTopLower == "accessibility": return "Getting started"
    return sTop


def readBox(sFolder):
    return buildFromTree(sFolder, "Box", placeBox)


# EGNYTE (15 November 2026): 1,511 articles in 32 categories, written mostly for the company's administrators. Kept: the
# web app, the desktop app, the mobile app, the pages for everyday users, the Microsoft and Google integrations, the AI
# assistant, Document Room, Document Portal, DocuSign, the other integrations a person uses, billing and support. Left
# out: the announcements (579 release notes, the known issues and the support lifecycle); the administrators' half
# (Admin Users, Secure and Govern, Reporting, the Migration App, Smart Cache, Storage Sync, External Replication, Data
# Fabric, FTP server setup, the API, compliance and incident pages); and the industry editions for architects and life
# sciences. The web app's few administrator topics (encryption keys) go with the administrators.
lEgnyteKept = {"WebUI": "The web app", "Desktop App": "The desktop app", "Mobile": "The mobile app",
               "Non-Admin Users": "For everyday users", "Microsoft Integrations": "Egnyte with Microsoft 365",
               "Google Apps": "Egnyte with Google", "Egnyte's AI Assistant": "The AI assistant",
               "Document Room": "Document Room and Document Portal", "Document Portal": "Document Room and Document Portal",
               "DocuSign": "Other integrations", "Integrations": "Other integrations",
               "Billing": "Billing and support", "Egnyte": "Billing and support"}


def placeEgnyte(sCategory, sTop, sSection, sTitle):
    sPlace = lEgnyteKept.get(sCategory, "")
    if not sPlace: return ""
    if sTop in ("Enterprise Key Management (EKM)", "Security & Administration", "Single Sign-On", "Public Cloud"): return ""
    return sPlace


def readEgnyte(sFolder):
    return buildFromTree(sFolder, "Egnyte", placeEgnyte)


# CLUBHOUSE (17 November 2026): 116 articles in Clubhouse's own categories. Left out, under the collection's rule
# against legal language: the Legal category, the law enforcement and government requests, the policies, the copyright
# notices, the country notices (Germany's Impressum) and the UK and EEA cancellation form. The categories are
# Clubhouse's own, without the emoji some carry; a section filed in no category goes under its own name.
lClubhouseLeftOut = ["legal", "law enforcement", "policies", "copyright violation", "country-specific information"]


def placeClubhouse(sCategory, sTop, sSection, sTitle):
    # The community guidelines are the rules of the rooms, in plain words, so they stay beside the policies' other help.
    if re.search(r"(?i)guidelines", sTitle): return re.sub(r"[^\w&,'\-?: ]", "", sCategory or sTop or "").strip() or sMiscellaneous
    for sName in (sCategory, sTop, sSection):
        sPlain = re.sub(r"[^\w&,'\- ]", "", sName or "").strip().lower()
        if any(sPlain.startswith(s) for s in lClubhouseLeftOut): return ""
    if re.search(r"(?i)cancellation form|impressum", sTitle): return ""
    sPlace = re.sub(r"[^\w&,'\-?: ]", "", sCategory or sTop or "").strip()
    return sPlace.replace("Acitivty", "Activity") or sMiscellaneous


def readClubhouse(sFolder):
    return buildFromTree(sFolder, "Clubhouse", placeClubhouse)


# ONE PLACER FOR A PLAIN ZENDESK CENTRE (17 November 2026): Patreon, GoFundMe, Fiverr, Ko-fi and Wyzant. The category
# is the publisher's own, without emoji; the collection's standing rule leaves out legal language and developer pages,
# found by the words in the category, section or title. A community's guidelines are its rules in plain words, so
# they stay.
sLegalPattern = (r"(?i)(\blegal\b|terms of (use|service)|terms and conditions|privacy (policy|notice)|cookie|"
                 r"law enforcement|government (agency )?requests|impressum|\bdmca\b|copyright|"
                 r"\bapi\b|developers?\b)")


def plainCategory(sName):
    return re.sub(r"\s+", " ", re.sub(r"[^\w&,'\-?: ]", "", sName or "")).strip()


def placeZendeskPlain(sCategory, sTop, sSection, sTitle):
    if not re.search(r"(?i)guidelines", sTitle):
        for sName in (sCategory, sTop, sSection, sTitle):
            if re.search(sLegalPattern, sName or ""): return ""
    return plainCategory(sCategory) or plainCategory(sTop) or sMiscellaneous


def readZendeskPlain(sFolder):
    return buildFromTree(sFolder, os.path.basename(sFolder.rstrip("\\/")), placeZendeskPlain)


def readZendeskPages(sFolder):
    """A Zendesk centre with its listings turned off (Wyzant, 17 November 2026), read from its drawn pages: the title is
    the article's h1, the body its article-body region, and the trail of links above the title names the category and
    the section, as Zendesk's own themes draw them. The same placer as the listings route leaves out legal pages."""
    lArticles, iLeft = [], 0
    for sName in sorted(os.listdir(sFolder)):
        if "_articles_" not in sName or not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r'(?is)<h1[^>]*class="[^"]*article-title[^"]*"[^>]*>(.*?)</h1>', sMarkup) or re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        if not oTitle: continue
        sTitle = stripTags(oTitle.group(1))
        sBody = (findBalanced(sMarkup, r'<div[^>]*class="[^"]*\barticle-body\b', "div")
                 or findBalanced(sMarkup, r'<section[^>]*class="[^"]*\barticle-info\b', "section")
                 or findBalanced(sMarkup, r"<article[^>]*>", "article")
                 or findBalanced(sMarkup, r"<main[^>]*>", "main"))
        if not sTitle or not sBody: continue
        sTrail = (findBalanced(sMarkup, r'<ol[^>]*class="[^"]*breadcrumbs', "ol")
                  or findBalanced(sMarkup, r'<nav[^>]*(aria-label="[^"]*[Bb]readcrumb|class="[^"]*breadcrumb)', "nav") or "")
        lsTrail = [stripTags(s) for s in re.findall(r"(?is)<li[^>]*>(.*?)</li>", sTrail)]
        lsTrail = [s for s in lsTrail if s and s != sTitle]
        sCategory = lsTrail[1] if len(lsTrail) > 1 else ""
        sSection = lsTrail[-1] if len(lsTrail) > 2 else ""
        sPlace = placeZendeskPlain(sCategory, sSection, sSection, sTitle)
        if not sPlace:
            iLeft += 1
            continue
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 20: continue
        lArticles.append((sPlace, sTitle, lBody))
    logging.info("%s: %d articles read from drawn pages; %d legal pages left out", os.path.basename(sFolder), len(lArticles), iLeft)
    return lArticles


# BY SECTION WHEN THE CATEGORIES ARE AUDIENCES (17 November 2026). Patreon files 422 articles under three categories
# (creators, members, general) and Fiverr 299 under three (clients, freelancers, Pro clients): three headings over
# hundreds of articles is no help to someone moving by heading. Their sections are the subjects, so the heading is the
# audience and the section, "Creators: Going Live". Ko-fi files everything under "All Help Articles", so its sections
# alone are the headings. Each section's own name is kept, with the stray spaces and tabs some carry removed.
dAudience = {"creator topics": "Creators", "member topics": "Members", "general topics": "General",
             "for clients": "Clients", "for freelancers": "Freelancers", "for pro clients": "Pro clients",
             # Mercury (19 November 2026): Business and Personal accounts, each with its own Getting Started and Send Money.
             "business": "Business", "personal": "Personal", "mercury business": "Business", "mercury personal": "Personal"}
dSameSection = {"advanced": "Advanced features", "get started with": "Getting started"}


def placeZendeskSection(sCategory, sTop, sSection, sTitle):
    if not placeZendeskPlain(sCategory, sTop, sSection, sTitle): return ""
    sSub = plainCategory(sTop or sSection)
    sSub = dSameSection.get(sSub.lower(), sSub)
    if not sSub: return plainCategory(sCategory) or sMiscellaneous
    sAudience = dAudience.get(plainCategory(sCategory).lower(), "")
    return (sAudience + ": " + sSub if sAudience else sSub)


def readZendeskSection(sFolder):
    return buildFromTree(sFolder, os.path.basename(sFolder.rstrip("\\/")), placeZendeskSection)


# MICROSOFT 365 (15 November 2026): Excel, OneDrive, Outlook, PowerPoint, SharePoint and Word, each gathered from
# support.microsoft.com's own site map with its accessibility articles. One reader serves all six.

# THE COLLECTION'S SURFACES (15 November 2026): Windows, the web, iPhone and iPad (iOS) and Alexa; never Mac or
# Android, never legal language, never a developer's programming interface.
# Products an article can apply to that are outside those surfaces or not the latest version. An article is kept when
# at least one product it applies to is none of these, or when it names no product at all: "latest versions only".
sMicrosoftOlder = (r"(?i)(\bmac\b|macos|android|windows phone|\b20(0\d|1\d|2[0-4])\b|"
                   r"\bserver\b|subscription edition|starter|\bmac\)|for mac|online \(classic\)|sharepoint foundation)")
# Titles that are legal language or a developer's reference rather than help. Narrow on purpose: "Show the developer
# tab", "Save a presentation that contains VBA macros" and Word's legal blackline comparison are help for a person
# using the app, and stay.
sMicrosoftNotHelp = (r"(?i)(privacy (supplement|statement|notice)|terms of (use|service)|license terms|licensing terms|"
                     r"transparency (note|documentation)|ai transparency|visual basic for applications|vba macro to|"
                     r"visual basic project|javascript (api|library)|\bapi\b|\bsdk\b)")

# Topics by words in an article's title, for the articles Microsoft files in no folder of their own. The first match
# wins, so the narrower topics come first. Each product adds its own topics before these.
lMicrosoftTopicsCommon = [
    (r"(?i)\bcopilot\b", "Copilot"),
    (r"(?i)(accessib|screen reader|narrator|jaws|nvda|alt text|dictat|read aloud|immersive reader|high contrast|"
     r"keyboard shortcut|keyboard to|braille)", "Accessibility and keyboard"),
    (r"(?i)(\bshare\b|sharing|co-?author|collaborat|comment|track changes|@mention|permission|invite)", "Sharing and working together"),
    (r"(?i)(\bprint|\bsave\b|saving|\bpdf\b|file format|open a file|recover|autosave|version history|export|import|convert)",
     "Files, saving and printing"),
    (r"(?i)(spelling|grammar|proof|language|translat|editor\b|thesaurus|word count)", "Proofing and language"),
    (r"(?i)(picture|image|photo|shape|icon|smartart|chart|graphic|video|audio|3d model|drawing|\bink\b|wordart|text box)",
     "Pictures, charts and media"),
    (r"(?i)(table\b|tables\b)", "Tables"),
    (r"(?i)(\bfont|format|style|bullet|numbered list|indent|spacing|theme|color|colour|highlight|border|align)",
     "Formatting"),
    (r"(?i)(error|fix|troubleshoot|problem|not working|can.t|cannot|won.t|issue|repair|crash)", "Troubleshooting"),
    (r"(?i)(setting|option|customi|default|ribbon|toolbar|add-in|template|macro|account|sign in|license|subscri|install|"
     r"update|what.s new|new in|get started|basics|quick start|learn)", "Getting started and settings"),
]

dMicrosoftTopics = {
    "Word": [
        (r"(?i)field code", "Field codes"),
        (r"(?i)(track|revision|compare|combine|protect|restrict|signature|password|similarity|readability)",
         "Reviewing and protecting"),
        (r"(?i)(mail merge|envelope|label)", "Mail merge, envelopes and labels"),
        (r"(?i)(citation|bibliograph|footnote|endnote|caption|table of contents|index|cross-reference|equation|"
         r"\btoc\b|reference)", "References, contents and citations"),
        (r"(?i)(page|margin|section|header|footer|column|orientation|break|layout|watermark|line number|booklet|"
         r"brochure|business card|calendar|fax|hyphenat|tab stop)", "Pages and layout"),
        (r"(?i)(find|replace|bookmark|hyperlink|\blink|copy|paste|clipboard|autocorrect|autotext|text|content control|"
         r"heading|outline|snippet|annotation|emoji|checkbox|checked box|case of)", "Editing text"),
    ],
    "Excel": [
        (r"(?i)(pivot)", "PivotTables"),
        (r"(?i)(chart|graph|sparkline)", "Charts"),
        (r"(?i)(formula|function|calculat|#\w+|reference|\bsum\b|average|lookup|array|lambda|name manager|"
         r"defined name|operator)", "Formulas"),
        (r"(?i)(filter|sort|data validation|conditional format|power query|get & transform|import data|"
         r"data model|what-if|forecast|analy[sz]e|table\b|tables\b|duplicate|flash fill)", "Data and analysis"),
        (r"(?i)(cell|row|column|worksheet|workbook|sheet|freeze|merge|wrap|number format|date|time)",
         "Cells, sheets and workbooks"),
        (r"(?i)(3d maps)", "3D Maps"),
        (r"(?i)(python|office script|script|vba|visual basic|macro|activex|form control|userform|javascript)",
         "Python, scripts and macros"),
        (r"(?i)(connection|external|query|xml|refresh|data type|stock|exchange rate|olap|power bi|access|csv|"
         r"analysis toolpak|regression|scenario|monte carlo|histogram|drop-down)", "Data and analysis"),
        (r"(?i)(number|round|multiply|subtract|divide|digit|decimal|percent|square|negative|thousands|fraction|"
         r"currency|combine|names|text)", "Numbers and text"),
    ],
    "Outlook": [
        (r"(?i)(calendar|meeting|appointment|event|schedul|time zone|availability|room)", "Calendar and meetings"),
        (r"(?i)(contact|people|address book|contact group|distribution list)", "Contacts and people"),
        (r"(?i)(task|to do|to-do)", "Tasks"),
        (r"(?i)(group|delegate|shared mailbox)", "Groups and delegates"),
        (r"(?i)(new outlook|classic outlook|outlook on the web|web app|\bowa\b|compare outlook|outlook for windows)",
         "New and classic Outlook"),
        (r"(?i)(account|pst|ost|imap|pop|exchange|gmail|outlook\.com|sign in|password|profile|data file|"
         r"mailbox|storage|quota|archive)", "Accounts, mailboxes and data files"),
        (r"(?i)(rule|junk|spam|phishing|block|sweep|focused inbox|categor|folder|flag|search|clean up)",
         "Organizing mail"),
        (r"(?i)(email|e-mail|message|mail|attach|signature|reply|forward|send|recall|read receipt|automatic repl|"
         r"out of office|inbox)", "Email"),
    ],
    "PowerPoint": [
        (r"(?i)(animat|transition|motion path|morph)", "Animations and transitions"),
        (r"(?i)(present|slide show|presenter|rehears|record|speaker|live caption|subtitle|broadcast|kiosk|"
         r"laser|teleprompter)", "Presenting and recording"),
        (r"(?i)(slide|layout|master|design|section|background|theme|size|orientation|outline|notes)",
         "Slides and layout"),
    ],
    "OneDrive": [
        (r"(?i)(sync|files on-demand|known folder|back up|backup|sync app|status|icon)", "Syncing and backup"),
        (r"(?i)(storage|plan|space|quota|subscription|account|sign in|personal vault)", "Accounts, storage and plans"),
        (r"(?i)(photo|album|memories|camera upload|video)", "Photos"),
        (r"(?i)(restore|recycle|delete|version|ransomware|recover)", "Deleting and restoring"),
        (r"(?i)(upload|download|file|folder|move|copy|rename|search|find|preview)", "Files and folders"),
    ],
    "SharePoint": [
        (r"(?i)(list|column|view|field|lookup|formula|calculated|validation)", "Lists"),
        (r"(?i)(librar|document|check out|check in|version|metadata|file|folder|upload|download)",
         "Libraries and documents"),
        (r"(?i)(page|site|news|web part|hub|navigation|theme|branding|template)", "Sites and pages"),
        (r"(?i)(workflow|power automate|flow|approval|alert|notification|rule)", "Workflows and alerts"),
    ],
}

# Folders under an app's address that name a topic outright.
dMicrosoftFolders = {"training": "Training", "copilot": "Copilot", "functions": "Excel functions",
                     "get-started": "Getting started and settings", "getstarted": "Getting started and settings",
                     "mail": "Email", "calendar": "Calendar and meetings", "accessibility": "Accessibility and keyboard",
                     "sites-pages": "Sites and pages", "libraries": "Libraries and documents",
                     "functions-data": "Lists", "lists": "Lists", "sharepoint": "Working with SharePoint",
                     "windows": "Syncing and backup", "contacts": "Contacts and people", "people": "Contacts and people",
                     "tasks": "Tasks", "troubleshoot": "Troubleshooting"}


def microsoftLatestTabs(sBody):
    """An article written for several platforms shows them as tabs (Windows, macOS, iOS, Android, Web), each a
    section of its own. The tab list goes, and so does each panel for a Mac or Android; a panel kept for Windows, the
    web or iPhone and iPad starts with its platform's name as a heading, so a reader knows which one it is."""
    sBody = re.sub(r'(?is)<ul[^>]*role="tablist"[^>]*>.*?</ul>', "", sBody)
    sOut, iAt = "", 0
    for oMatch in re.finditer(r'(?is)<section[^>]*role="tabpanel"[^>]*data-tab="([^"]*)"[^>]*>', sBody):
        if oMatch.start() < iAt: continue
        sPanel = findBalanced(sBody[oMatch.start():], r'<section[^>]*>', "section")
        if not sPanel: continue
        sOut += sBody[iAt:oMatch.start()]
        sTab = oMatch.group(1).lower()
        if not re.search(r"(mac|android)", sTab):
            sLabel = {"windows": "Windows", "web": "Web", "new-outlook": "New Outlook", "classic-outlook": "Classic Outlook",
                      "newoutlook": "New Outlook", "classicoutlook": "Classic Outlook", "ios": "iPhone and iPad",
                      "iphone": "iPhone", "ipad": "iPad", "mobile": "iPhone and iPad"}.get(sTab, sTab.replace("-", " ").capitalize())
            sOut += "<h1>" + html.escape(sLabel) + "</h1>" + sPanel
        iAt = oMatch.start() + len(sPanel)
    return sOut + sBody[iAt:]


def readMicrosoftSupport(sFolder, sProduct):
    """One Microsoft 365 app's guide from its support.microsoft.com harvest.

    WHAT IS KEPT. The latest versions only: an article whose Applies To list names only Mac, mobile or older versions
    (2024 and before), or a server edition, is left out, as is one Microsoft writes for the administrator (an
    address with an admin folder). Each article is read once, though Microsoft serves some under two spellings of
    the same address (/en-us/Excel/ and /en-us/excel/).

    WHERE IT GOES. An article Microsoft files in a folder of its own (functions, training, copilot, mail, calendar,
    the accessibility articles) takes that folder's topic. The rest, filed under the app alone, are placed by the
    words in their titles, the app's own topics first and then those every app shares. The Applies To line is kept
    as the article's first line, so a reader knows which versions it describes."""
    lArticles, setSeen, setTexts = [], set(), set()
    iOlder = iAdmin = iCopies = iNotHelp = 0
    lTopics = dMicrosoftTopics.get(sProduct, []) + lMicrosoftTopicsCommon
    sArea = sProduct.lower()
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html") or "_sitemaps_" in sName: continue
        oPath = re.match(r"(?i)support\.microsoft\.com_en-us_(accessibility_)?" + re.escape(sArea) + r"(?:_(.+))?\.html$", sName)
        if not oPath or not oPath.group(2): continue
        lParts = oPath.group(2).lower().split("_")
        sKey = (oPath.group(1) or "").lower() + "/".join(lParts)
        if sKey in setSeen:
            iCopies += 1
            continue
        setSeen.add(sKey)
        if "admin" in lParts[:-1] or lParts[0] == "category":
            iAdmin += lParts[0] != "category"
            continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        sBody = findBalanced(sMarkup, r'<div[^>]*class="[^"]*learnArticleContent', "div") or \
                findBalanced(sMarkup, r'<main[^>]*>', "main")
        if not oTitle or not sBody: continue
        sTitle = stripTags(oTitle.group(1))
        lApplies = [stripTags(s) for s in re.findall(r'(?is)<span[^>]*class="appliesToItem"[^>]*>(.*?)</span>', sMarkup)]
        if lApplies and all(re.search(sMicrosoftOlder, s) for s in lApplies):
            iOlder += 1
            continue
        if re.search(r"(?i)(\bmac\b|android|outlook lite|\b20(0\d|1\d)\b)", sTitle) and \
           not re.search(r"(?i)(windows|\bweb\b|\bpc\b|\bios\b|iphone|ipad)", sTitle):
            iOlder += 1
            continue
        if re.search(sMicrosoftNotHelp, sTitle):
            iNotHelp += 1
            continue
        sBody = re.sub(r'(?is)<section[^>]*supAppliesToSection.*?</section>', "", sBody)
        sBody = microsoftLatestTabs(sBody)
        lBody = toMarkdown(sBody, 0, "https://support.microsoft.com/en-us/" + sArea + "/")
        sText = " ".join(lBody)
        if len(sText.split()) < 40 or sText in setTexts:
            iCopies += sText in setTexts
            continue
        setTexts.add(sText)
        if lApplies: lBody = ["Applies to: " + ", ".join(s for s in lApplies if not re.search(sMicrosoftOlder, s)) + ".", ""] + lBody
        sCategory = ""
        if oPath.group(1): sCategory = "Accessibility and keyboard"
        elif len(lParts) > 1: sCategory = dMicrosoftFolders.get(lParts[0], "")
        if not sCategory and sProduct == "Excel" and re.search(r"(?i)\bfunctions?$", sTitle): sCategory = "Excel functions"
        if not sCategory:
            for sPattern, sLabel in lTopics:
                if re.search(sPattern, sTitle):
                    sCategory = sLabel
                    break
        lArticles.append((sCategory or sMiscellaneous, sTitle, lBody))
    # A topic with one or two articles is not worth a heading of its own: they join Miscellaneous.
    dCounts = {}
    for sCategory, sTitle, lBody in lArticles: dCounts[sCategory] = dCounts.get(sCategory, 0) + 1
    lArticles = [(sCategory if dCounts[sCategory] >= 3 else sMiscellaneous, sTitle, lBody) for sCategory, sTitle, lBody in lArticles]
    logging.info("%s: %d articles; left out %d for older versions, Mac or Android only, %d for administrators, %d legal or "
                 "developer pages, %d copies", sProduct, len(lArticles), iOlder, iAdmin, iNotHelp, iCopies)
    return lArticles


def readMicrosoftExcel(sFolder): return readMicrosoftSupport(sFolder, "Excel")
def readMicrosoftOneDrive(sFolder): return readMicrosoftSupport(sFolder, "OneDrive")
def readMicrosoftOutlook(sFolder): return readMicrosoftSupport(sFolder, "Outlook")
def readMicrosoftPowerPoint(sFolder): return readMicrosoftSupport(sFolder, "PowerPoint")
def readMicrosoftSharePoint(sFolder): return readMicrosoftSupport(sFolder, "SharePoint")
def readMicrosoftWord(sFolder): return readMicrosoftSupport(sFolder, "Word")


def googleTopicNames(sFolder):
    """Google's topic names by topic number, read from the centre's own pages (14 November 2026). Google no longer
    puts a trail above an article, so the category is found the way a reader finds it: the front page lists its
    topics as headings with their articles under them, every link to an article carries the topic it was listed
    under (ref_topic=), and a topic page's own heading names its topic. Returns {topic number: name}."""
    dNames = {}
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html") or "_answer_" in sName: continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTopic = re.search(r"_topic_(\d+)", sName)
        if oTopic:
            oHeading = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
            if oHeading: dNames.setdefault(oTopic.group(1), stripTags(oHeading.group(1)))
        sHeading = ""
        for oMatch in re.finditer(r'(?is)<h3[^>]*>(.*?)</h3>|<a[^>]*href="[^"]*/answer/\d+[^"]*ref_topic=(\d+)[^"]*"', sMarkup):
            if oMatch.group(1) is not None:
                sHeading = stripTags(oMatch.group(1))
            elif sHeading and not oTopic:
                dNames.setdefault(oMatch.group(2), sHeading)
    return dNames


def readGoogleTopics(sFolder, fPlace=None):
    """A Google help centre whose articles carry no trail (Calendar, Chat, Keep, Sites, Tasks and the Docs editors,
    gathered November 2026). The article, title and platform are read as readGoogleMeet reads them; the category is
    the topic most links to the article name, by googleTopicNames. An article no topic lists goes to Miscellaneous.
    fPlace(answer number, title, category), when given, returns the category to file the article under, or "" to
    leave it out: one harvest can then make several guides, as the Docs editors' does (15 November 2026).
    Returns (category, title, body) like every reader."""
    dNames = googleTopicNames(sFolder)
    dVotes = {}
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        for oMatch in re.finditer(r'href="[^"]*/answer/(\d+)[^"]*ref_topic=(\d+)', sMarkup):
            if oMatch.group(2) in dNames:
                dCount = dVotes.setdefault(oMatch.group(1), {})
                dCount[dNames[oMatch.group(2)]] = dCount.get(dNames[oMatch.group(2)], 0) + 1
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if "_answer_" not in sName or not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        sBody = findBalanced(sMarkup, r'<article[^>]*class="[^"]*article[^"]*"', "article")
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        if not sBody or not oTitle: continue
        sTitle = stripTags(oTitle.group(1))
        if not sTitle: continue
        # Legal language is not help: Google's policy and notice pages are left out, as Microsoft's are.
        if re.search(r"(?i)(cookies notification|exceptions for educational|terms of service|privacy (policy|notice)|"
                     r"program policies|transparency (note|report))", sTitle): continue
        sBody = re.sub(r"(?is)<h1[^>]*>.*?</h1>", "", sBody, count=1)
        oId = re.search(r"_answer_(\d+)", sName)
        dCount = dVotes.get(oId.group(1), {}) if oId else {}
        sCategory = max(sorted(dCount), key=lambda s: dCount[s]) if dCount else sMiscellaneous
        if fPlace:
            sCategory = fPlace(oId.group(1) if oId else "", sTitle, sCategory)
            if not sCategory: continue
        oPlatform = re.search(r"(?i)Platform_?3D([A-Za-z]+)", sName)
        if oPlatform:
            # The collection's surfaces are Windows, the web, iPhone and iPad and Alexa: Google's Android edition of
            # an article is left out, its Computer and iPhone and iPad editions kept.
            if oPlatform.group(1).lower() == "android": continue
            sPlatform = {"desktop": "Computer", "ios": "iPhone and iPad",
                         "iphone": "iPhone and iPad"}.get(oPlatform.group(1).lower(), oPlatform.group(1))
            sTitle = sTitle + " (" + sPlatform + ")"
        elif re.search(r"(?i)\bandroid\b", sTitle) and not re.search(r"(?i)(iphone|ipad|\bios\b|computer|web)", sTitle):
            continue
        # THE PLATFORM SWITCHER IS NOT TEXT (15 November 2026): Google heads each platform's part with a row of links
        # to every edition, Android's included -- "[Computer](...) [Android phone & tablet](...)[iPhone & iPad](...)"
        # -- which a screen reader read as a line of links three times an article. The rows are dropped.
        lBody = [sLine for sLine in toMarkdown(sBody, 0)
                 if not re.match(r"^\s*(\[(Computer|Android phone & tablet|Android|iPhone & iPad)\]\([^)]*\)\s*)+$", sLine)]
        lArticles.append((sCategory, sTitle, lBody))
    return lArticles


# THE DOCS EDITORS (15 November 2026): Google keeps the help for Docs, Sheets, Slides, Forms and Vids in one centre,
# support.google.com/docs, and one harvest of it makes a guide for each. Each article goes to the product whose topic
# lists it most: a topic's product is found by following the ref_topic each topic page gives its subtopics up to
# Docs, Sheets, Slides, Forms or Vids. Google's older topics hang from none of these, so they are named here from what
# they hold (the function lists are Sheets', the page-setup topics Docs', the presenting topics Slides'). Topics that
# serve every editor -- sharing, Drive, offline work, accessibility, Gemini, getting help -- are placed by the product
# the article's title names, and an article that names none goes into the Docs, Sheets and Slides guides alike, under
# its own topic, since a reader of any one of them needs it. Google Pics, eight articles about an image maker, is left
# out as too thin for a guide; so is Drawings, which has no topic of its own.
dDocsEditorsRoots = {"9046002": "Docs", "9054603": "Sheets", "9052835": "Slides", "9055404": "Forms", "14950067": "Vids",
                     "17164909": "Pics"}
dDocsEditorsOlderTopics = {
    "1240289": "Sheets", "1361467": "Sheets", "1361471": "Sheets", "1361472": "Sheets", "1361474": "Sheets",
    "15158": "Sheets", "3046366": "Sheets",
    "1361461": "Docs", "1361462": "Docs", "1361463": "Docs", "1361464": "Docs", "9045752": "Docs", "9045753": "Docs",
    "9045929": "Docs", "9045930": "Docs", "9045931": "Docs",
    "1694827": "Slides", "1694924": "Slides", "1694925": "Slides", "1694926": "Slides", "19431": "Slides",
    "6063584": "Forms", "6063592": "Forms", "6063593": "Forms"}
lDocsEditorsTitleWords = [
    ("Docs", r"(?i)\b(google docs|in docs|docs with|a document|documents?\b)"),
    ("Sheets", r"(?i)\b(google sheets|in sheets|sheets with|spreadsheets?|pivot|formula|function|chart|cells?\b)"),
    ("Slides", r"(?i)\b(google slides|in slides|slides with|presentations?|presenter|speaker notes|slideshow)"),
    ("Forms", r"(?i)\b(google forms?|in forms|quiz|form responses|responders?)"),
    ("Vids", r"(?i)\b(google vids|in vids|vids with|voiceovers?)")]


def docsEditorsPlacer(sFolder, sProduct):
    """fPlace for readGoogleTopics: the category an article of the Docs editors' harvest takes in sProduct's guide."""
    dNames = googleTopicNames(sFolder)
    dParent, dVotes, dLinks = {}, {}, {}
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        for sChild, sParent in re.findall(r'/docs/topic/(\d+)[^"]*?ref_topic=(\d+)', sMarkup):
            if sChild != sParent: dParent.setdefault(sChild, sParent)
        for sAnswer, sTopic in re.findall(r'/docs/answer/(\d+)[^"]*?ref_topic=(\d+)', sMarkup):
            dCount = dVotes.setdefault(sAnswer, {})
            dCount[sTopic] = dCount.get(sTopic, 0) + 1
        oFrom = re.search(r"_answer_(\d+)", sName)
        if oFrom:
            for sTo in set(re.findall(r'/docs/answer/(\d+)', sMarkup)):
                if sTo != oFrom.group(1): dLinks.setdefault(sTo, []).append(oFrom.group(1))

    def productOf(sTopic):
        setSeen = set()
        while sTopic not in dDocsEditorsRoots and sTopic not in dDocsEditorsOlderTopics and sTopic in dParent and sTopic not in setSeen:
            setSeen.add(sTopic)
            sTopic = dParent[sTopic]
        return dDocsEditorsRoots.get(sTopic) or dDocsEditorsOlderTopics.get(sTopic) or ""

    def votedHome(sAnswer):
        dProducts = {}
        for sTopic, iCount in dVotes.get(sAnswer, {}).items():
            sOne = productOf(sTopic)
            if sOne: dProducts[sOne] = dProducts.get(sOne, 0) + iCount
        return max(sorted(dProducts), key=lambda s: dProducts[s]) if dProducts else ""

    def ownTopic(sAnswer, sHome):
        dOwn = dict((sTopic, iCount) for sTopic, iCount in dVotes.get(sAnswer, {}).items() if productOf(sTopic) == sHome and sTopic in dNames)
        return dNames[max(sorted(dOwn), key=lambda s: dOwn[s])] if dOwn else ""

    # AN ARTICLE NO TOPIC LISTS AT ALL goes where the articles that link to it went, with their heading: Sheets'
    # statistics functions (F.DIST.RT, T.INV.2T) are listed by no topic but linked from their siblings. Three rounds
    # let a chain of such articles settle. An article listed only by shared topics is not moved this way.
    dHome = {}
    for sAnswer in dVotes:
        sHome = votedHome(sAnswer)
        if sHome: dHome[sAnswer] = (sHome, ownTopic(sAnswer, sHome))
    for iRound in range(3):
        for sAnswer, lsFrom in dLinks.items():
            if sAnswer in dHome or sAnswer in dVotes: continue
            dLinked = {}
            for sFrom in lsFrom:
                if sFrom in dHome: dLinked[dHome[sFrom]] = dLinked.get(dHome[sFrom], 0) + 1
            if dLinked: dHome[sAnswer] = max(sorted(dLinked), key=lambda t: dLinked[t])

    def place(sAnswer, sTitle, sCategory):
        # A topic's word first, then a title that names one product ("Collaborate with Gemini in Google Slides"),
        # then the articles that link to it, and last every one of Docs, Sheets and Slides.
        sHome, sTopic = dHome.get(sAnswer, ("", "")) if sAnswer in dVotes else ("", "")
        if not sHome:
            lsNamed = [sName for sName, sPattern in lDocsEditorsTitleWords if re.search(sPattern, sTitle)]
            if len(lsNamed) == 1:
                sHome = lsNamed[0]
                sLinkedHome, sLinkedTopic = dHome.get(sAnswer, ("", ""))
                if sLinkedHome == sHome: sTopic = sLinkedTopic
        if not sHome: sHome, sTopic = dHome.get(sAnswer, ("all", ""))
        if sHome == "all": return sCategory if sProduct in ("Docs", "Sheets", "Slides") else ""
        if sHome != sProduct: return ""
        # The heading is the product's own topic that lists the article most, so a Docs article listed also under
        # a Slides topic is filed under the Docs topic.
        return sTopic or sCategory
    return place


def readGoogleDocs(sFolder): return readGoogleTopics(sFolder, docsEditorsPlacer(sFolder, "Docs"))
def readGoogleSheets(sFolder): return readGoogleTopics(sFolder, docsEditorsPlacer(sFolder, "Sheets"))
def readGoogleSlides(sFolder): return readGoogleTopics(sFolder, docsEditorsPlacer(sFolder, "Slides"))
def readGoogleVids(sFolder): return readGoogleTopics(sFolder, docsEditorsPlacer(sFolder, "Vids"))
def readGoogleFormsEditors(sFolder): return readGoogleTopics(sFolder, docsEditorsPlacer(sFolder, "Forms"))


lMpvProgrammer = ["lua scripting", "javascript", "json ipc", "c plugins",
                    "embedding into other programs (libmpv)", "changelog",
                    "using mpv from other programs or scripts", "hooks",
                    "commands specified as arrays", "asynchronous command details",
                    "encoding", "list of events", "synchronous vs. asynchronous",
                    "named arguments", "inconsistencies between options and properties"]


def isMpvProgrammer(sCategory, sTitle):
    """True for the parts of mpv's manual that assume the reader writes code.

    The collection is for END USERS. A command-line option or a keybinding in a
    configuration file is fair game, however technical; a Lua API, a C plugin
    header or a JSON protocol for controlling mpv from another program is not.
    """
    sWhole = (sCategory + " " + sTitle).lower()
    if any(sName in sWhole for sName in lMpvProgrammer): return True
    return bool(re.search(r"(\bapi\b|libmpv|\bipc\b|scripting|\bplugin\b|mpv_[a-z_]+\(|\bcallback\b)", sWhole))


def readMpv(sFolder):
    """mpv publishes its whole documentation as one reference manual. Its h1
    headings are the manual's own parts — SYNOPSIS, INTERACTIVE CONTROL, USAGE,
    OPTIONS — and its h2 headings are the sections within them, so the parts
    become categories and the sections become articles. A part with no sections
    of its own becomes a single article under its own name."""
    lArticles = []
    iProgrammer = 0
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        if "manual" not in sName:
            oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
            sBody = findBalanced(sMarkup, r"<main[^>]*>", "main") or findBalanced(sMarkup, r"<body[^>]*>", "body")
            if oTitle and sBody:
                lBody = toMarkdown(sBody, 0)
                if len(" ".join(lBody).split()) >= 40:
                    lArticles.append(("Installing mpv", stripTags(oTitle.group(1)) or "Installation", lBody))
            continue
        lTokens = sorted([(oMatch.start(), oMatch.end(), 1, stripTags(oMatch.group(1)))
                          for oMatch in re.finditer(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)] +
                         [(oMatch.start(), oMatch.end(), 2, stripTags(oMatch.group(1)))
                          for oMatch in re.finditer(r"(?is)<h2[^>]*>(.*?)</h2>", sMarkup)])
        sCategory = sMiscellaneous
        for iIndex, (iStart, iAfter, iLevel, sTitle) in enumerate(lTokens):
            iEnd = lTokens[iIndex + 1][0] if iIndex + 1 < len(lTokens) else len(sMarkup)
            if not sTitle: continue
            sTitle = sTitle.strip()
            lBody = toMarkdown(sMarkup[iAfter:iEnd], 0)
            if iLevel == 1:
                sCategory = sTitle.title() if sTitle.isupper() else sTitle
                if isMpvProgrammer(sCategory, ""):
                    iProgrammer += 1
                    continue
                if len(" ".join(lBody).split()) >= 40:
                    lArticles.append((sCategory, sCategory, lBody))
                continue
            if len(" ".join(lBody).split()) < 20: continue
            if isMpvProgrammer(sCategory, sTitle):
                iProgrammer += 1
                continue
            lArticles.append((sCategory, sTitle, lBody))
    logging.info("mpv: %d sections left out as programmer documentation", iProgrammer)
    return lArticles


def readEndNote(sFolder):
    """EndNote's online help is a page-per-topic system from the days of frames.
    It has no headings at all: the topic's name sits in a table cell marked
    heading_title, and the body is everything after the navigation banner. The
    category comes from the file name's own prefix, which is how this help
    system groups its pages — hsr for searching, hsrt for reference types, and
    so on."""
    dPrefixes = {"hsrt": "Reference types and their fields",
                 "hsr": "Searching and finding references",
                 "hsc": "Collecting references",
                 "hso": "Organising your library",
                 "hsf": "Formatting and citing",
                 "hsm": "Your account and settings",
                 "hsg": "Getting started",
                 "h": "General"}
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith((".html", ".htm")): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r'(?is)<td[^>]*class="heading_title"[^>]*>(.*?)</td>', sMarkup)
        if not oTitle: continue
        sTitle = stripTags(re.sub(r"(?is)<!--.*?-->", " ", oTitle.group(1)))
        if not sTitle: continue
        sBody = sMarkup[oTitle.end():]
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 20: continue
        # The prefix is the whole token before the first underscore, not its first
        # letter: hsrt, hsr, hsc. A non-greedy match took "h" from every name and
        # filed 127 of 129 articles under General.
        oPrefix = re.search(r"ENW_([a-z]+)[_.]", sName)
        sCategory = sMiscellaneous
        if oPrefix:
            for sKey in sorted(dPrefixes, key=len, reverse=True):
                if oPrefix.group(1).startswith(sKey):
                    sCategory = dPrefixes[sKey]
                    break
        lArticles.append((sCategory, sTitle, lBody))
    return lArticles


def readMendeley(sFolder):
    """Elsevier answers Mendeley questions one page at a time: the question is the
    h1 and the answer is what follows it."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        if not oTitle: continue
        sTitle = stripTags(oTitle.group(1))
        if not sTitle: continue
        lBody = toMarkdown(sMarkup[oTitle.end():], 0)
        if len(" ".join(lBody).split()) < 25: continue
        # Elsevier prints no topic on an answer page — its trail is only Support,
        # Mendeley, and the question itself — so the category is taken from what
        # the question is ABOUT, using the words Mendeley's own product names use.
        sCategory = "Using Mendeley"
        sWhole = sTitle.lower()
        for sWords, sName2 in [("institutional|mie|alumni|admin", "Institutional Edition"),
                               ("web importer|importer|browser", "Web Importer"),
                               ("cite|citation|word|plugin|bibliograph|style", "Citing and the Word plugin"),
                               ("sync|storage|space|library size", "Storage and syncing"),
                               ("account|password|sign in|login|email|profile", "Accounts and signing in"),
                               ("data|privacy|delete|gdpr", "Your data and privacy"),
                               ("install|update|version|system requirement", "Installing and updating"),
                               ("group|share|collaborat", "Groups and sharing"),
                               ("careers|funding|premium|subscription", "Subscriptions and services")]:
            if re.search(sWords, sWhole):
                sCategory = sName2
                break
        if "_answer_" not in sName: sCategory = "Topics and guides"
        lArticles.append((sCategory, sTitle, lBody))
    return lArticles


def readSphinxManual(sFolder, sProductName, sSkipPattern=""):
    """Reads a manual published with Sphinx — Calibre's is one. The body is the
    document region, the title is its h1, and the category is the manual's own
    part, taken from the first path segment of the address."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        if sSkipPattern and re.search(sSkipPattern, sName): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        sBody = (findBalanced(sMarkup, r'<div[^>]*class="[^"]*body[^"]*"[^>]*role="main"', "div")
                 or findBalanced(sMarkup, r'<div[^>]*class="[^"]*documentwrapper', "div")
                 or findBalanced(sMarkup, r"<main[^>]*>", "main"))
        if not oTitle or not sBody: continue
        sTitle = stripTags(oTitle.group(1)).rstrip("¶#").strip()
        if not sTitle: continue
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 30: continue
        lArticles.append((sProductName, sTitle, lBody))
    return lArticles


def readStack(sFolder):
    """Stack Overflow's help centre. Its badge pages are not help — there are 445
    of them, one per badge, each a sentence saying what earns it — so they are
    left out and counted. The privileges pages ARE help: they say what a reader
    may do at each level of reputation."""
    lArticles = []
    iBadges = 0
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        if "_help_badges_" in sName:
            iBadges += 1
            continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        if not oTitle: continue
        sTitle = stripTags(oTitle.group(1))
        if not sTitle: continue
        sBody = (findBalanced(sMarkup, r'<div[^>]*class="[^"]*js-help-content', "div")
                 or findBalanced(sMarkup, r'<div[^>]*id="content"', "div")
                 or findBalanced(sMarkup, r"<main[^>]*>", "main"))
        if not sBody: continue
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 25: continue
        sCategory = "Using the site"
        if "_privileges_" in sName: sCategory = "Privileges and reputation"
        elif re.search(r"_(licensing|dmca|legal|policy|gdpr|acceptable)", sName): sCategory = "Rules and legal"
        elif re.search(r"_(moderat|flag|close|delete|review)", sName): sCategory = "Moderation and review"
        elif re.search(r"_(account|password|email|profile|sign)", sName): sCategory = "Your account"
        elif re.search(r"_(asking|answer|question|format|edit|tag|vote|comment|bounty)", sName): sCategory = "Asking and answering"
        lArticles.append((sCategory, sTitle, lBody))
    logging.info("Stack Overflow: %d badge pages left out; a badge description is not help", iBadges)
    return lArticles


def readSimplePages(sFolder, sProduct, sTitlePattern=r"(?is)<h1[^>]*>(.*?)</h1>"):
    """A plain documentation site: the title is the page's h1 (or, where a page has
    none, its title element) and the body is the page's main region."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith((".html", ".htm")): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(sTitlePattern, sMarkup)
        sTitle = stripTags(oTitle.group(1)) if oTitle else ""
        if not sTitle:
            oPageTitle = re.search(r"(?is)<title[^>]*>(.*?)</title>", sMarkup)
            sTitle = re.sub(r"\s*[-|].*$", "", stripTags(oPageTitle.group(1))).strip() if oPageTitle else ""
        if not sTitle: continue
        sBody = (findBalanced(sMarkup, r'<div[^>]*class="[^"]*(inner-page|theme-default-content|content)', "div")
                 or findBalanced(sMarkup, r"<main[^>]*>", "main")
                 or findBalanced(sMarkup, r"<article[^>]*>", "article")
                 or findBalanced(sMarkup, r"<body[^>]*>", "body"))
        if not sBody: continue
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 30: continue
        lArticles.append((sProduct, sTitle.rstrip("#¶").strip(), lBody))
    return lArticles


def readOrgMode(sFolder):
    """Org mode publishes its manual one section per page, each numbered — the
    heading reads "11.3.3 Matching tags and properties" — so the number gives the
    chapter and the chapter gives the category. The chapters are collected in a
    first pass, because the pages arrive in alphabetical order and a section can
    be read before the chapter it belongs to.

    Appendix A is left out: it is the manual's hacking chapter, and every section
    of it — hooks, the property and mapping interfaces, adding export backends,
    translator functions — assumes the reader writes Emacs Lisp."""
    lPages = []
    dChapters = {}
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h[1-4][^>]*>(.*?)</h[1-4]>", sMarkup)
        if not oTitle: continue
        sHeading = stripTags(oTitle.group(1)).rstrip("¶").strip()
        if not sHeading: continue
        oNumber = re.match(r"^([0-9]+|[A-Z])((?:\.[0-9]+)*)\s+(.*)$", sHeading)
        sChapter = oNumber.group(1) if oNumber else ""
        sRest = oNumber.group(2) if oNumber else ""
        sTitle = oNumber.group(3).strip() if oNumber else sHeading
        if oNumber and not sRest and sChapter.isdigit(): dChapters[sChapter] = sTitle
        lPages.append((sName, sMarkup, sChapter, sTitle, sHeading))
    lArticles = []
    iHacking = 0
    for sName, sMarkup, sChapter, sTitle, sHeading in lPages:
        if sChapter == "A":
            iHacking += 1
            continue
        sBody = findBalanced(sMarkup, r"<body[^>]*>", "body") or sMarkup
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 30: continue
        if "_guide_" in sName: sCategory = "The compact guide"
        else: sCategory = dChapters.get(sChapter, "The manual")
        lArticles.append((sCategory, sTitle, lBody))
    logging.info("Org mode: %d sections of the hacking appendix left out; they assume the reader writes Emacs Lisp", iHacking)
    return lArticles


def readAngi(sFolder):
    """Angi answers its questions on one page, and publishes that page twice: once
    as prose and once as schema.org FAQPage data. The data is the better source,
    since it pairs each question with its own answer and needs no guessing about
    where one ends. Its section headings supply the categories.

    Angi's article library — how much a plumber costs, and eleven thousand more —
    is NOT help; the fence should have refused it and now does."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if "_articles_" in sName or not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        for oBlock in re.finditer(r'(?is)<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', sMarkup):
            try:
                dPayload = json.loads(oBlock.group(1))
            except Exception:
                continue
            if not isinstance(dPayload, dict) or dPayload.get("@type") != "FAQPage": continue
            for dQuestion in dPayload.get("mainEntity", []):
                sTitle = stripTags(str(dQuestion.get("name", "")))
                dAnswer = dQuestion.get("acceptedAnswer") or {}
                lBody = toMarkdown(str(dAnswer.get("text", "")), 0)
                if not sTitle or len(" ".join(lBody).split()) < 12: continue
                lArticles.append(("Questions Angi answers", sTitle, lBody))
    return lArticles


def readCraigslist(sFolder):
    """Craigslist's help pages: the body is the simple page section, the title is
    its first heading, and the category comes from the address — /help/posting/,
    /help/billing/, /help/accounts/ and so on, which is how Craigslist itself
    groups them."""
    dNames = {"posting": "Posting", "billing": "Paying for a posting", "accounts": "Accounts",
              "searching": "Searching", "flags": "Flags and community moderation",
              "images": "Images", "email": "Email and replies", "legal": "Legal and policy",
              "scams": "Scams and safety", "safety": "Scams and safety", "prohibited": "What may not be posted"}
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h[12][^>]*>(.*?)</h[12]>", sMarkup)
        sTitle = stripTags(oTitle.group(1)) if oTitle else ""
        if not sTitle:
            oPageTitle = re.search(r"(?is)<title[^>]*>(.*?)</title>", sMarkup)
            sTitle = stripTags(oPageTitle.group(1)).split("|")[-1].strip() if oPageTitle else ""
        if not sTitle: continue
        sBody = (findBalanced(sMarkup, r'<section[^>]*class="[^"]*simple-page-content', "section")
                 or findBalanced(sMarkup, r"<body[^>]*>", "body"))
        if not sBody: continue
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 20: continue
        sCategory = "General help"
        for sKey, sLabel in dNames.items():
            if re.search(r"_(about_)?(help_)?" + sKey, sName, re.I):
                sCategory = sLabel
                break
        lArticles.append((sCategory, sTitle, lBody))
    return lArticles


def readBitwarden(sFolder):
    """Bitwarden's help centre. The article is the article element and its title
    the h1 inside it.

    Two things are skipped. The site serves a MARKDOWN SOURCE of every page at
    the same address with .md added — 334 of them in this harvest, each a twin of
    a page already read. And the administrator's material that slipped past the
    fence is set aside here as well: single sign-on connectors, server
    deployment, the command-line tool and the like. Bitwarden documents the
    person keeping passwords and the person running a company's server in one
    place, and only the first belongs in this collection."""
    oAdministrator = re.compile(r"(?i)(saml|scim|sso|ldap|directory-connector|self-host|deploy|kubernetes"
                                r"|_cli|-cli|unified|smtp|reverse-proxy|certificate|licensing-on-premise"
                                r"|business-unit|provider-portal|secrets-manager-(cli|api)|public-api|api\.)")
    lArticles = []
    iSource = iAdmin = 0
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        if ".md." in sName:
            iSource += 1
            continue
        if oAdministrator.search(sName):
            iAdmin += 1
            continue
        sMarkup = readText(os.path.join(sFolder, sName))
        sBody = findBalanced(sMarkup, r"<article[^>]*>", "article") or findBalanced(sMarkup, r"<main[^>]*>", "main")
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        if not sBody or not oTitle: continue
        sTitle = stripTags(oTitle.group(1))
        if not sTitle: continue
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 30: continue
        sCategory = "Using Bitwarden"
        for sWords, sLabel in [
                (r"(?i)(password-manager|vault|item|folder|favorit|attachment|card|identity)", "Your vault and its items"),
                (r"(?i)(generator|passphrase|username)", "Generating passwords and usernames"),
                (r"(?i)(two-step|2fa|authenticator|passkey|fido|yubikey|duo)", "Two-step login and passkeys"),
                (r"(?i)(browser|extension|chrome|firefox|safari|edge)", "The browser extension"),
                (r"(?i)(mobile|android|ios|watch)", "The mobile apps"),
                (r"(?i)(desktop|windows|macos|linux-desktop)", "The desktop app"),
                (r"(?i)(import|export|migrat|condition)", "Moving your data in and out"),
                (r"(?i)(share|send|collection|organization|member|family)", "Sharing and organisations"),
                (r"(?i)(account|email|master-password|delete|recovery|billing|subscription|premium)", "Your account and subscription"),
                (r"(?i)(secrets-manager|machine-account|project)", "Secrets Manager"),
                (r"(?i)(passwordless|log-in-with-device|device-approval)", "Logging in without a password")]:
            if re.search(sWords, sName):
                sCategory = sLabel
                break
        lArticles.append((sCategory, sTitle, lBody))
    logging.info("Bitwarden: %d markdown twins and %d administrator pages left out", iSource, iAdmin)
    return lArticles


def readUdio(sFolder):
    """Udio's help site is Intercom underneath, and it publishes its own trail as
    schema.org BreadcrumbList data in the page head. That data is the better
    source for the category than the drawn trail, because it names the collection
    plainly and needs no guessing about which link is which."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if "_articles_" not in sName or not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        if not oTitle: continue
        sTitle = stripTags(oTitle.group(1))
        if not sTitle: continue
        sCategory = sMiscellaneous
        for oBlock in re.finditer(r'(?is)<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', sMarkup):
            try:
                dPayload = json.loads(oBlock.group(1))
            except Exception:
                continue
            if not isinstance(dPayload, dict) or dPayload.get("@type") != "BreadcrumbList": continue
            lNames = [str(dItem.get("name", "")) for dItem in dPayload.get("itemListElement", [])]
            lNames = [sName2 for sName2 in lNames
                      if sName2 and sName2.lower() not in ("all collections",) and sName2 != sTitle]
            if lNames: sCategory = lNames[-1]
        # THE ARTICLE'S OWN BODY FIRST (17 November 2026). Kickstarter's Intercom pages hold the text in an article_body
        # region; the wider article section also holds the title, the date and the related articles, so each Kickstarter
        # article began with its own title again as a heading and a date line.
        sBody = (findBalanced(sMarkup, r'<div[^>]*class="[^"]*\barticle_body\b', "div")
                 or findBalanced(sMarkup, r'<section[^>]*class="[^"]*section__article', "section")
                 or findBalanced(sMarkup, r"<main[^>]*>", "main"))
        if not sBody: continue
        sBody = re.sub(r'(?is)<section[^>]*class="[^"]*related_articles.*$', "", sBody)
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 25: continue
        lArticles.append((sCategory, sTitle, lBody))
    return lArticles

# CLAUDE, ONE HARVEST AND SIX GUIDES (19 November 2026). Anthropic's help centre is Intercom, as Kickstarter's is, but
# its collections nest: Claude Mobile apps holds Claude for iOS and Claude for Android, Claude Desktop holds Desktop
# extensions. So the whole trail is read, not only its last name, and each guide takes the articles whose first
# collection is its own. The trail comes from the page's schema.org BreadcrumbList, keeping only the steps that are
# collections, and from the drawn trail above the heading when that data is missing. The harvest is read once per build
# and kept, since six guides read it.
g_dClaudeCache = {}
sClaudeAdmin = (r"(?i)\b(admins?|administrators?|owners?|scim|sso|single sign-on|provision(ing|ed)?|domain (capture|verification)"
                r"|audit logs?|mdm|group polic(y|ies)|deploy(ing|ment)?|compliance api|retention controls|allowlist(ing)?"
                r"|enterprise configuration|centralized management|for your (organization|school or district)|organization's)\b")
# THE OWNERS' SUBCOLLECTIONS (19 November 2026): the first build kept 33 articles under Team and Enterprise plans: Admin
# management, and more under Analytics and usage, Billing, and Security and compliance -- all written for the people who
# run an organization's plan. Those four are left out by their trail; Capabilities, Get started and Plan overviews stay.
sClaudeOwners = r"(?i)team and enterprise plans / (admin management|analytics and usage|billing|security and compliance)"
sClaudeLeftOut = r"(?i)(api and console|amazon bedrock|bedrock|identity management|privacy and legal)"


def readClaudeTrails(sFolder):
    """Every Claude article in the harvest as (lTrail, sTitle, lBody). A trail is the list of collection names, outermost
    first; an article in no collection has an empty one."""
    if sFolder in g_dClaudeCache: return g_dClaudeCache[sFolder]
    lArticles = []
    # ONE ARTICLE, ONE ID (19 November 2026): Anthropic renames an article's address and keeps its number, and the old
    # addresses answer with the same page, so the first gathering saved Get started with Cowork three times, as
    # 13345190-get-started-with-cowork, -getting-started-with-cowork and -get-started-with-claude-cowork. 634 files held
    # 433 articles. The number decides: the first file of each is read and the others are logged.
    setIds = set()
    for sName in sorted(os.listdir(sFolder)):
        if "_articles_" not in sName or not sName.endswith(".html"): continue
        oId = re.search(r"_articles_(\d+)", sName)
        if oId and oId.group(1) in setIds:
            logging.info("Claude harvest: %s is another address of article %s, so it is not read again", sName, oId.group(1))
            continue
        if oId: setIds.add(oId.group(1))
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        if not oTitle: continue
        sTitle = stripTags(oTitle.group(1))
        if not sTitle: continue
        lTrail = []
        for oBlock in re.finditer(r'(?is)<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', sMarkup):
            try:
                vPayload = json.loads(oBlock.group(1))
            except Exception:
                continue
            for dPayload in (vPayload if isinstance(vPayload, list) else [vPayload]):
                if not isinstance(dPayload, dict) or dPayload.get("@type") != "BreadcrumbList": continue
                for dItem in dPayload.get("itemListElement", []):
                    if not isinstance(dItem, dict): continue
                    vItem = dItem.get("item", "")
                    sUrl = vItem.get("@id", "") if isinstance(vItem, dict) else str(vItem)
                    sStep = stripTags(str(dItem.get("name", "") or (vItem.get("name", "") if isinstance(vItem, dict) else "")))
                    if not sStep or sStep == sTitle or sStep.lower() == "all collections": continue
                    if sUrl and "/collections/" not in sUrl: continue
                    if not sUrl and re.search(r"(?i)help cent(er|re)", sStep): continue
                    lTrail.append(sStep)
            if lTrail: break
        if not lTrail:
            sBefore = sMarkup[:oTitle.start()]
            for oLink in re.finditer(r'(?is)<a[^>]*href="[^"]*/collections/[^"]*"[^>]*>(.*?)</a>', sBefore[-6000:]):
                sStep = stripTags(oLink.group(1))
                if sStep and sStep.lower() != "all collections" and sStep not in lTrail: lTrail.append(sStep)
        sBody = (findBalanced(sMarkup, r'<div[^>]*class="[^"]*\barticle_body\b', "div")
                 or findBalanced(sMarkup, r'<section[^>]*class="[^"]*section__article', "section")
                 or findBalanced(sMarkup, r"<main[^>]*>", "main"))
        if not sBody: continue
        sBody = re.sub(r'(?is)<section[^>]*class="[^"]*related_articles.*$', "", sBody)
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 25: continue
        lArticles.append((lTrail, sTitle, lBody))
    logging.info("Claude harvest: %d articles read from %s", len(lArticles), sFolder)
    g_dClaudeCache[sFolder] = lArticles
    return lArticles


def claudeSurface(lTrail, sTitle):
    """Which Claude guide an article belongs in: web, desktop, ios, cowork, code, duet, or "" for none."""
    sTrail = " / ".join(lTrail)
    sFirst = lTrail[0].lower() if lTrail else ""
    if re.search(sClaudeLeftOut, sTrail): return ""
    # Android and the Mac are outside this collection's surfaces. An article that names one of them in its title or
    # trail, and not Windows, the iPhone or the iPad as well, is left out.
    if re.search(r"(?i)\bandroid\b", sTrail + " " + sTitle) and not re.search(r"(?i)\b(ios|iphone|ipad)\b", sTitle): return ""
    if re.search(r"(?i)\b(mac|macos|macbook)\b", sTrail + " " + sTitle) and not re.search(r"(?i)\bwindows\b", sTitle): return ""
    if re.search(r"(?i)\bduet\b", sTrail + " " + sTitle): return "duet"
    if re.search(r"(?i)^claude cowork", sFirst): return "cowork"
    if re.search(r"(?i)^claude code", sFirst): return "code"
    if re.search(r"(?i)^claude desktop", sFirst): return "desktop"
    if re.search(r"(?i)mobile", sFirst): return "ios"
    return "web"


def readClaudeFor(sFolder, sSurface):
    """The articles of one Claude guide, each placed under its trail below the guide's own collection."""
    lArticles = []
    for lTrail, sTitle, lBody in readClaudeTrails(sFolder):
        if claudeSurface(lTrail, sTitle) != sSurface: continue
        # Pages written for an organization's administrators are left out of every Claude guide, as the preambles say.
        if re.search(sClaudeAdmin, sTitle) or re.search(sClaudeOwners, " / ".join(lTrail)):
            logging.info("Claude %s: left out as administrator material: %s", sSurface, sTitle)
            continue
        if sSurface == "web":
            lSteps = lTrail[1:] if lTrail and lTrail[0].lower() == "claude" and len(lTrail) > 1 else lTrail
        else:
            lSteps = lTrail[1:] if len(lTrail) > 1 else lTrail
        sCategory = ": ".join(lSteps) if lSteps else sMiscellaneous
        lArticles.append((sCategory, sTitle, lBody))
    logging.info("Claude %s: %d articles", sSurface, len(lArticles))
    return lArticles


def readClaudeWeb(sFolder): return readClaudeFor(sFolder, "web")
def readClaudeDesktop(sFolder): return readClaudeFor(sFolder, "desktop")
def readClaudeIos(sFolder): return readClaudeFor(sFolder, "ios")
def readClaudeCowork(sFolder): return readClaudeFor(sFolder, "cowork")
def readClaudeCode(sFolder): return readClaudeFor(sFolder, "code")
def readClaudeDuet(sFolder): return readClaudeFor(sFolder, "duet")

def readTwitch(sFolder):
    """TWITCH (19 November 2026). help.twitch.tv is a Salesforce help centre, drawn by Edge. Each article's own
    component holds the title as h1.articleTitle and the text in an article-body region, with an "On this page" list of
    its own headings in a category_list block, which is left out since the headings follow. The category is the
    Breadcrumbs navigation above it, a topic and sometimes a subtopic (Getting Started: Beginner Broadcasting)."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if "_s_article_" not in sName or not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        sBody = findBalanced(sMarkup, r'<div[^>]*class="article-body"', "div")
        if not sBody: continue
        oTitle = re.search(r'(?is)<h1[^>]*class="articleTitle"[^>]*>(.*?)</h1>', sBody) or re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        sTitle = stripTags(oTitle.group(1)) if oTitle else ""
        if not sTitle: continue
        sBody = re.sub(r'(?is)<h1[^>]*class="articleTitle".*?</h1>', "", sBody, count=1)
        sList = findBalanced(sBody, r'<div[^>]*class="category_list"', "div")
        if sList: sBody = sBody.replace(sList, "", 1)
        sCategory = sMiscellaneous
        oTrail = re.search(r'(?is)<nav[^>]*aria-label="Breadcrumbs".*?</nav>', sMarkup)
        if oTrail:
            lsSteps = [html.unescape(s).strip() for s in re.findall(r'<a[^>]*title="([^"]*)"', oTrail.group(0))]
            lsSteps = [s for s in lsSteps if s and s.lower() != "home"]
            if lsSteps: sCategory = ": ".join(lsSteps)
        lBody = toMarkdown(sBody, 0, "https://help.twitch.tv/s/article/" + sName.split("_s_article_", 1)[1][:-5])
        if len(" ".join(lBody).split()) < 25: continue
        lArticles.append((sCategory, sTitle, lBody))
    logging.info("Twitch: %d articles read", len(lArticles))
    return lArticles


# QGIS (28 November 2026). The categories are the manuals' own chapters and modules, in the publisher's own words,
# each prefixed with its manual, so the User Guide, the Training Manual and A Gentle Introduction to GIS stay apart.
dQgisChapters = {
    "user_manual": ("User Guide", {
        "introduction/getting_started": "Getting Started", "introduction/project_files": "Working with Project Files",
        "introduction/qgis_gui": "QGIS GUI", "introduction/browser": "The Browser panel",
        "introduction/qgis_configuration": "QGIS Configuration", "introduction/general_tools": "General Tools",
        "introduction": "Getting Started", "working_with_projections": "Working with Projections",
        "map_views": "Visualizing Maps", "expressions": "Level up with Expressions", "style_library": "The Style Library",
        "managing_data_source": "Managing Data Source", "working_with_vector": "Working with Vector Data",
        "working_with_raster": "Working with Raster Data", "working_with_mesh": "Working with Mesh Data",
        "working_with_vector_tiles": "Working with Vector Tiles", "working_with_point_clouds": "Working with Point Clouds",
        "working_with_3d_tiles": "Working with 3D Tiles", "print_layout": "Laying out the maps",
        "working_with_ogc": "Working with OGC / ISO protocols", "working_with_gps": "Working with GPS Data",
        "auth_system": "Authentication System", "grass_integration": "GRASS GIS Integration",
        "processing": "QGIS processing framework", "processing_algs": "Processing providers and algorithms",
        "plugins": "Plugins", "appendices": "Appendices", "literature_web": "Literature and Web References"}),
    "training_manual": ("Training Manual", {
        "foreword": "Course Introduction", "basic_map": "Creating and Exploring a Basic Map",
        "vector_classification": "Classifying Vector Data", "map_composer": "Laying out the Maps",
        "create_vector_data": "Creating Vector Data", "vector_analysis": "Vector Analysis", "rasters": "Rasters",
        "complete_analysis": "Completing the Analysis", "qgis_plugins": "Plugins", "online_resources": "Online Resources",
        "grass": "GRASS", "assessment": "Assessment", "forestry": "Forestry Application",
        "database_concepts": "Database Concepts with PostgreSQL",
        "spatial_databases": "Spatial Database Concepts with PostGIS / PostgreSQL",
        "databases": "Using Spatial Databases in QGIS", "processing": "The QGIS processing guide",
        "appendix": "Preparing Exercise Data"}),
}


def qgisCategory(sUrl):
    """The category of one QGIS page, from its address: the manual, then its chapter or module. A chapter not in the
    table keeps its folder's name, and the log says so, so a chapter QGIS adds later is seen rather than misfiled."""
    oMatch = re.search(r"/docs/(user_manual|training_manual|gentle_gis_introduction)/(.*)$", sUrl)
    if not oMatch: return ""
    if oMatch.group(1) == "gentle_gis_introduction": return "A Gentle Introduction to GIS"
    sManual, dChapters = dQgisChapters[oMatch.group(1)]
    lParts = oMatch.group(2).split("/")
    sKey = "/".join(lParts[:2]).rsplit(".", 1)[0]
    sChapter = dChapters.get(sKey) or dChapters.get(lParts[0])
    if not sChapter:
        sChapter = lParts[0].replace("_", " ").capitalize()
        logging.info("QGIS: chapter folder %s is not in the table; filed under %s", lParts[0], sChapter)
    return sManual + ": " + sChapter


def readQgis(sFolder):
    """QGIS's three manuals, published with Sphinx's Read the Docs theme. The body is the region marked articleBody and
    the title is its h1, with the chapter number ("23.8.") and the anchor mark taken off so titles sort by their words.
    A chapter's index page is only a list of its sections, so that list is removed first and a page with nothing else
    left is set aside and counted. The heading marks and the page's own local contents list go too: they link only
    within a page the guide does not keep whole."""
    dManifest = readManifest(sFolder)
    lArticles = []
    iIndexes = iRefused = 0
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        sUrl = dManifest.get(sName, "")
        if re.search(r"(_sources|genindex|search\.html|qgis_server|appendix_contribute)", sUrl or sName):
            iRefused += 1
            continue
        sCategory = qgisCategory(sUrl)
        if not sCategory:
            iRefused += 1
            logging.info("QGIS: %s is outside the three manuals; left out", sUrl or sName)
            continue
        sMarkup = readText(os.path.join(sFolder, sName))
        sBody = (findBalanced(sMarkup, r'<div[^>]*itemprop="articleBody"', "div")
                 or findBalanced(sMarkup, r'<div[^>]*role="main"', "div")
                 or findBalanced(sMarkup, r"<main[^>]*>", "main"))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sBody or "")
        if not sBody or not oTitle:
            iRefused += 1
            logging.info("QGIS: %s has no article region or no title; left out", sName)
            continue
        sTitle = re.sub(r"(?is)<a[^>]*class=[\"']headerlink[\"'][^>]*>.*?</a>", "", oTitle.group(1))
        sTitle = re.sub(r"^\d+(\.\d+)*\.?\s+", "", stripTags(sTitle).rstrip("#\u00b6").strip()).strip()
        if not sTitle: continue
        # The h1 goes from the body: the guide's own heading carries the title, and the publisher's numbered copy
        # ("23.8. Using processing from the command line") would sit under it as a second heading saying the same.
        sBody = sBody.replace(oTitle.group(0), "", 1)
        sBody = re.sub(r"(?is)<a[^>]*class=[\"']headerlink[\"'][^>]*>.*?</a>", "", sBody)
        for sPattern, sTag in ((r'<div[^>]*class="[^"]*toctree-wrapper', "div"), (r'<nav[^>]*class="[^"]*contents', "nav"),
                               (r'<div[^>]*class="[^"]*contents[^"]*topic', "div"), (r'<div[^>]*class="[^"]*rst-footer-buttons', "div")):
            while True:
                sBlock = findBalanced(sBody, sPattern, sTag)
                if not sBlock: break
                sBody = sBody.replace(sBlock, "", 1)
        lBody = toMarkdown(sBody, 0, sUrl)
        if len(" ".join(lBody).split()) - len(sTitle.split()) < 30:
            iIndexes += 1
            continue
        lArticles.append((sCategory, sTitle, lBody))
    logging.info("QGIS: %d articles read; %d chapter index pages holding only a list of sections set aside; %d pages "
                 "outside the manuals left out", len(lArticles), iIndexes, iRefused)
    return lArticles


def readPiccyBot(sFolder):
    """PICCYBOT (23 November 2026). piccybot.com is one page drawn by script, gathered through Edge, and it holds the
    help there is: how the app works, its features, setting it up on WhatsApp and on Meta's Ray-Ban glasses, and a list
    of questions. The publisher's level-two headings are the categories and each level-three heading is an article,
    its level-four headings kept inside it; words before a section's first level-three heading make an article named
    for the section. Left out, by heading, as not help: the welcome (vision, mission and values, printed twice), what
    users say, the video showcase, honors, donations, the technology partner and the closing call to download. The
    questions are left out too: the page draws each answer only when its question is opened, so the harvest holds the
    questions without their answers, and a question with no answer helps nobody. The preamble says so. A heading's line break is read as a space ("Visual Accessibility Made
    Simple", which the page draws on two lines)."""
    lArticles = []
    sFile = os.path.join(sFolder, "www.piccybot.com.html")
    if not os.path.isfile(sFile): return lArticles
    sMarkup = readText(sFile)
    sMarkup = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", "", sMarkup)
    sMarkup = re.sub(r"(?i)<br\s*/?>", " ", sMarkup)
    def headingText(sInner):
        return re.sub(r"\s+", " ", stripTags(re.sub(r"(?i)</(span|div)>", " </\\1>", sInner))).strip()
    lH2 = list(re.finditer(r"(?is)<h2[^>]*>(.*?)</h2>", sMarkup))
    sSkip = (r"(?i)^(welcome to piccybot|what piccybot users say|watch piccybot in action|frequently asked questions"
             r"|honors and recognitions|donation options|technology partner|start experiencing the visual world today)$")
    for iSection, oH2 in enumerate(lH2):
        sCategory = headingText(oH2.group(1))
        if not sCategory or re.match(sSkip, sCategory): continue
        iEnd = lH2[iSection + 1].start() if iSection + 1 < len(lH2) else len(sMarkup)
        sSection = sMarkup[oH2.end():iEnd]
        oFooter = re.search(r"(?is)<footer\b", sSection)
        if oFooter: sSection = sSection[:oFooter.start()]
        lH3 = list(re.finditer(r"(?is)<h3[^>]*>(.*?)</h3>", sSection))
        # A SECTION OF SHORT ITEMS IS ONE ARTICLE. How PiccyBot Works gives each of its four steps a sentence, and
        # its features list gives each feature one: as articles of their own they held 10 to 19 words each, and the
        # build's gate failed the guide for a median article of 19 words. Such a section is read whole, its items
        # kept as headings inside one article named for the section, which is how the publisher presents them.
        lItemWords = []
        for iItem, oItem in enumerate(lH3):
            iItemEnd = lH3[iItem + 1].start() if iItem + 1 < len(lH3) else len(sSection)
            lItemWords.append(len(" ".join(toMarkdown(sSection[oItem.end():iItemEnd], 1)).split()))
        if lH3 and max(lItemWords) < 25:
            lWhole = toMarkdown(sSection, 1, "https://www.piccybot.com/")
            if len(" ".join(lWhole).split()) >= 25: lArticles.append((sCategory, sCategory, lWhole))
            continue
        sLead = sSection[:lH3[0].start()] if lH3 else sSection
        lLead = toMarkdown(sLead, 1, "https://www.piccybot.com/")
        if len(" ".join(lLead).split()) >= 25: lArticles.append((sCategory, sCategory, lLead))
        for iArticle, oH3 in enumerate(lH3):
            sTitle = headingText(oH3.group(1))
            if not sTitle: continue
            iStop = lH3[iArticle + 1].start() if iArticle + 1 < len(lH3) else len(sSection)
            lBody = toMarkdown(sSection[oH3.end():iStop], 1, "https://www.piccybot.com/")
            if len(" ".join(lBody).split()) < 8: continue
            lArticles.append((sCategory, sTitle, lBody))
    logging.info("PiccyBot: %d articles read from its one page", len(lArticles))
    return lArticles


# STRIPE AND LINK (24 November 2026). Both support sites are Stripe's own: an article at /questions/<slug>, its title the
# page-title heading, its text the cms-support-content main region, and, on Stripe, its topics in the page-topic-list
# above it, broadest first. A topic page at /topics/<slug> lists its articles as links to /questions/, and is how an
# article without a topic list of its own -- every Link article, and about one Stripe article in seven -- finds its
# category. A page whose address no longer answers is Stripe's "Page not found", with no article region, and is
# skipped. Stripe serves some articles under two addresses; the build's dedupe keeps one copy.
# LEFT OUT, by the collection's standing rule (no developer programming interfaces, no legal language, no Android):
# the API, Webhooks and Legal topics, the shutdown of the legacy Sources API (a migration for programmers), any article
# whose title names an API, any article for Android alone, notices of new terms and the services agreement, and the
# few articles written in another language for one country. Each is counted in the log.
lStripeLeftOutTopics = ["api", "webhooks", "legal", "shutdown of the legacy sources api for non-card payment methods"]
dStripeSameTopic = {"connect (platform)": "Connect"}


def readStripeSupport(sFolder, sHost):
    """Reads a Stripe-run support site (support.stripe.com or support.link.com), as the comment above says."""
    dManifest = readManifest(sFolder)
    sPrefix = sHost + "_"
    def plain(sInner): return re.sub(r"\s+", " ", html.unescape(stripTags(sInner))).strip()
    dTopicOf = {}
    for sName in sorted(os.listdir(sFolder)):
        if not sName.startswith(sPrefix + "topics_") or not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        # The topic's name is its own heading; Link's page title is only "Link: Help & Support".
        oHeading = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        oTitle = re.search(r"(?is)<title>(.*?)</title>", sMarkup)
        sTopic = plain(oHeading.group(1)) if oHeading else ""
        if not sTopic and oTitle: sTopic = plain(oTitle.group(1)).split(" : ")[0].strip()
        if not sTopic or re.search(r"(?i)help (&|and) support", sTopic): continue
        # Link marks its list items as topic_list_item; Stripe lists them plainly, pinned under the topic's text.
        for oLink in re.finditer(r'(?is)<a\b[^>]*href="(?:https://' + re.escape(sHost) + r')?/questions/([^"?#]+)"', sMarkup):
            dTopicOf.setdefault(oLink.group(1).strip("/"), sTopic)
    lArticles = []
    dLeftOut = {"no article (page not found)": 0, "API, webhooks or legal topic": 0, "title names an API": 0, "Android only": 0,
                "terms or agreement": 0, "not in English": 0}
    for sName in sorted(os.listdir(sFolder)):
        if not sName.startswith(sPrefix + "questions_") or not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oMain = re.search(r'(?is)<main[^>]*data-testid="cms-support-content"[^>]*>(.*?)</main>', sMarkup)
        oTitle = re.search(r'(?is)<h1[^>]*data-testid="page-title"[^>]*>(.*?)</h1>', sMarkup)
        if not oMain or not oTitle:
            dLeftOut["no article (page not found)"] += 1
            continue
        sTitle = plain(oTitle.group(1))
        sSlug = sName[len(sPrefix + "questions_"):-5]
        oTopics = re.search(r'(?is)<ul[^>]*data-testid="page-topic-list"[^>]*>(.*?)</ul>', sMarkup)
        lsTopics = [plain(s) for s in re.findall(r"(?is)<li[^>]*>(.*?)</li>", oTopics.group(1))] if oTopics else []
        sCategory = lsTopics[0] if lsTopics else dTopicOf.get(sSlug, "Miscellaneous")
        sCategory = dStripeSameTopic.get(sCategory.lower(), sCategory)
        if sCategory.lower() in lStripeLeftOutTopics or any(s.lower() in lStripeLeftOutTopics for s in lsTopics[1:]):
            dLeftOut["API, webhooks or legal topic"] += 1
            continue
        if re.search(r"\bAPIs?\b", sTitle):
            dLeftOut["title names an API"] += 1
            continue
        if re.search(r"(?i)\bandroid\b", sTitle) and not re.search(r"(?i)(iphone|ipad|\bios\b)", sTitle):
            dLeftOut["Android only"] += 1
            continue
        # Legal language that carries no topic: Stripe's notices of new user terms and its services agreement.
        if re.search(r"(?i)(terms update|services agreement|^cookies$)", sTitle):
            dLeftOut["terms or agreement"] += 1
            continue
        # A few articles are written for one country in its own language, such as Brazil's in Portuguese.
        lsWords = stripTags(oMain.group(1)).lower().split()
        if len(lsWords) > 30 and sum(s in ("de", "que", "para", "não", "com", "los", "las", "el", "por", "uma", "um", "é", "se")
                                     for s in lsWords) / len(lsWords) > 0.08:
            dLeftOut["not in English"] += 1
            continue
        sBody = oMain.group(1)
        # Each article opens with its summary as a level-three heading and a rule under it; it is the first paragraph.
        sBody = re.sub(r"(?is)^\s*<h3[^>]*>(.*?)</h3>\s*<hr\s*/?>", r"<p>\1</p>", sBody)
        sAddress = dManifest.get(sName, "https://" + sHost + "/questions/" + sSlug)
        lBody = toMarkdown(sBody, 1, sAddress)
        if len(" ".join(lBody).split()) < 8: continue
        lArticles.append((sCategory, sTitle, lBody))
    # AN ARTICLE NO TOPIC CLAIMS goes to the topic its title names, longest name first, so "2024 updates to Canada
    # verification requirements" joins Verification and "Taxes on Stripe fees for Brazil" joins Taxes on Stripe fees.
    # Stripe tags about one article in seven with no topic, and its topic pages list only a few pinned articles each.
    lsNames = sorted({t[0] for t in lArticles if t[0] != "Miscellaneous"}, key=len, reverse=True)
    dWords = {"pricing": "Pricing", "price": "Pricing", "fee": "Pricing", "tax": "Taxes", "verif": "Verification",
              "payout": "Payouts", "refund": "Refunds", "dispute": "Disputes", "invoice": "Invoice", "subscription": "Billing",
              "connected account": "Connect", "platform": "Connect", "card": "Payments", "payment": "Payments",
              "bank": "Payouts", "account": "Account", "terminal": "Terminal", "reader": "Terminal"}
    iPlaced = 0
    for iArticle, (sCategory, sTitle, lBody) in enumerate(lArticles):
        if sCategory != "Miscellaneous": continue
        sFound = next((s for s in lsNames if re.search(r"(?i)\b" + re.escape(s) + r"\b", sTitle)), "")
        if not sFound:
            sFound = next((sName for sWord, sName in dWords.items() if sName in lsNames and re.search(r"(?i)\b" + re.escape(sWord), sTitle)), "")
        if sFound:
            lArticles[iArticle] = (sFound, sTitle, lBody)
            iPlaced += 1
    logging.info("%s: %d articles without a topic placed by the topic their title names", sHost, iPlaced)
    # ONE COPY OF AN ARTICLE SERVED AT TWO ADDRESSES, the one with a topic kept: Link serves two verification articles
    # under a second slug that no topic lists, and the copy under Verifying your identity is the one a reader looks for.
    lKept, setSeen = [], set()
    for tArticle in sorted(lArticles, key=lambda t: t[0] == "Miscellaneous"):
        sKey = (tArticle[1].lower(), " ".join(" ".join(tArticle[2]).split()))
        if sKey in setSeen: continue
        setSeen.add(sKey)
        lKept.append(tArticle)
    if len(lKept) < len(lArticles): logging.info("%s: %d copies of an article under a second address left out", sHost, len(lArticles) - len(lKept))
    lArticles = lKept
    logging.info("%s: %d articles read; left out: %s", sHost, len(lArticles), "; ".join("%s %d" % t for t in dLeftOut.items()))
    return lArticles


def readStripe(sFolder): return readStripeSupport(sFolder, "support.stripe.com")
def readLink(sFolder): return readStripeSupport(sFolder, "support.link.com")


def readWyzant(sFolder):
    """WYZANT, THIRD VERSION (19 November 2026). Wyzant's help is now a WordPress site in three levels: an audience
    section (students-parents), its topics (student-billing), and their articles (why-was-i-charged-1-00), so a page's
    level is the number of parts in its address. The category is the section's heading and the topic's, read from their
    own saved pages. A topic page with no article saved beneath it is read as an article itself, as some contact pages
    are. The title is the page's h1; the text is WordPress's entry-content region, else the article element, else main."""
    dHeadings, dPages = {}, {}
    for sName in sorted(os.listdir(sFolder)):
        if not sName.startswith("support.wyzant.com_") or not sName.endswith(".html"): continue
        lsParts = sName[len("support.wyzant.com_"):-5].split("_")
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        dHeadings["/".join(lsParts)] = stripTags(oTitle.group(1)) if oTitle else lsParts[-1].replace("-", " ").title()
        dPages["/".join(lsParts)] = sMarkup
    lArticles = []
    for sPath, sMarkup in sorted(dPages.items()):
        lsParts = sPath.split("/")
        if len(lsParts) < 2: continue
        if len(lsParts) == 2 and any(s.startswith(sPath + "/") for s in dPages): continue
        sTitle = dHeadings[sPath]
        sBody = (findBalanced(sMarkup, r'<div[^>]*class="[^"]*\bentry-content\b', "div")
                 or findBalanced(sMarkup, r"<article[^>]*>", "article")
                 or findBalanced(sMarkup, r"<main[^>]*>", "main"))
        if not sBody: continue
        sBody = re.sub(r"(?is)<h1[^>]*>.*?</h1>", "", sBody, count=1)
        lBody = [s for s in toMarkdown(sBody, 0, "https://support.wyzant.com/" + sPath + "/") if not re.match(r"(?i)\s*time to read\b", s)]
        if len(" ".join(lBody).split()) < 25: continue
        sCategory = ": ".join(dHeadings.get("/".join(lsParts[:i]), lsParts[i - 1]) for i in range(1, len(lsParts)))
        lArticles.append((sCategory or sMiscellaneous, sTitle, lBody))
    logging.info("Wyzant: %d articles read from %d pages", len(lArticles), len(dPages))
    return lArticles

# WHEN EACH READER LAST CHANGED, by guide file, in local time. Add a line when a reader changes in a way that should
# reach guides already built; the build then rebuilds each listed guide that is older, without being asked.
dReaderChanged = {
    "ClaudeWeb.md": "2026-11-20 00:00", "ClaudeDesktop.md": "2026-11-20 00:00", "ClaudeIos.md": "2026-11-20 00:00",
    "ClaudeCowork.md": "2026-11-20 00:00", "ClaudeCode.md": "2026-11-20 00:00", "ClaudeDuet.md": "2026-11-20 00:00",
}


def readerChangedTime(sFile):
    """The time a guide's reader last changed, as seconds since the epoch, or 0 when it is not listed."""
    sWhen = dReaderChanged.get(sFile, "")
    return time.mktime(time.strptime(sWhen, "%Y-%m-%d %H:%M")) if sWhen else 0

def readShopFor(sFolder, bPay):
    """SHOP AND SHOP PAY (20 November 2026). Shopify's help centre at help.shop.app holds both: sections at
    /en/shop/<section>, articles at /en/shop/<section>/<article>. Each page's text is its article element, whose
    h1.article-title is the title. A section's own page opens with an overview worth reading, so it comes first in its
    category, named by its own heading. The Shop Pay guide takes the sections whose names start with shop-pay (Shop
    Pay, its settings, Installments and their settings); the Shop guide takes the rest."""
    dHeadings, dPages = {}, {}
    for sName in sorted(os.listdir(sFolder)):
        if not sName.startswith("help.shop.app_en_shop_") or not sName.endswith(".html"): continue
        lsParts = sName[len("help.shop.app_en_shop_"):-5].split("_")
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r'(?is)<h1[^>]*class="article-title"[^>]*>(.*?)</h1>', sMarkup)
        if oTitle: dHeadings["/".join(lsParts)] = stripTags(oTitle.group(1))
        dPages["/".join(lsParts)] = sMarkup
    lArticles = []
    for sPath, sMarkup in sorted(dPages.items(), key=lambda t: (t[0].split("/")[0], len(t[0].split("/")), t[0])):
        lsParts = sPath.split("/")
        if lsParts[0].startswith("shop-pay") != bPay or sPath not in dHeadings: continue
        sBody = findBalanced(sMarkup, r'<article[^>]*class="article"', "article")
        if not sBody: continue
        sBody = re.sub(r'(?is)<h1[^>]*class="article-title".*?</h1>', "", sBody, count=1)
        lBody = toMarkdown(sBody, 0, "https://help.shop.app/en/shop/" + sPath)
        if len(" ".join(lBody).split()) < 25: continue
        sCategory = dHeadings.get(lsParts[0], lsParts[0].replace("-", " ").capitalize())
        sTitle = dHeadings[sPath] if len(lsParts) > 1 else "Overview: " + dHeadings[sPath]
        lArticles.append((sCategory, sTitle, lBody))
    logging.info("%s: %d articles read from %d pages", "Shop Pay" if bPay else "Shop", len(lArticles), len(dPages))
    return lArticles


def readShop(sFolder): return readShopFor(sFolder, False)
def readShopPay(sFolder): return readShopFor(sFolder, True)

# HUBSPOT, ONE HARVEST AND FOUR GUIDES (20 November 2026). HubSpot's knowledge base held 1,919 articles and about 1.9
# million words, too much for one guide a reader can move around in, so it is split by the first step of each
# article's trail, HubSpot's own top categories, into four of about half a million words each. A top category not named
# here goes to the account guide and is logged, so a new one is noticed.
dHubSpotGuides = {"account & setup": "account", "get started": "account", "ai": "account", "partners": "account",
                  "crm": "crm", "sales": "crm", "service": "crm", "revenue": "crm",
                  "automation": "data", "data": "data", "reporting & data": "data",
                  "marketing": "marketing", "content": "marketing"}
g_dHubSpotCache = {}


def readHubSpotAll(sFolder):
    """Every HubSpot article as (lTrail, sTitle, lBody), read once a build. An article is a two-part address
    (/workflows/<slug>); its text is the post body HubSpot's page template marks hs_cos_wrapper_post_body, and its
    trail the cl-breadcrumbs list, less Knowledge Base and the article itself. The /page/<n> listing pages, 1,906 of
    them in the first harvest, are not articles and are passed over."""
    if sFolder in g_dHubSpotCache: return g_dHubSpotCache[sFolder]
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.startswith("knowledge.hubspot.com_") or not sName.endswith(".html"): continue
        lsParts = sName[len("knowledge.hubspot.com_"):-5].split("_")
        if len(lsParts) != 2 or lsParts[0] == "page": continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        sBody = findBalanced(sMarkup, r'<span[^>]*id="hs_cos_wrapper_post_body"', "span")
        if not oTitle or not sBody: continue
        sTitle = stripTags(oTitle.group(1))
        oTrail = re.search(r'(?is)<ul class="cl-breadcrumbs[^"]*">(.*?)</ul>', sMarkup)
        lTrail = [stripTags(s) for s in re.findall(r'(?is)<a class="cl-breadcrumbs-link-text"[^>]*>(.*?)</a>', oTrail.group(1))] if oTrail else []
        lTrail = [s for s in lTrail if s and s.lower() != "knowledge base"]
        lBody = toMarkdown(sBody, 0, "https://knowledge.hubspot.com/" + "/".join(lsParts))
        if len(" ".join(lBody).split()) < 25: continue
        lArticles.append((lTrail, sTitle, lBody))
    logging.info("HubSpot harvest: %d articles read", len(lArticles))
    g_dHubSpotCache[sFolder] = lArticles
    return lArticles


def readHubSpotFor(sFolder, sGuide):
    lArticles = []
    for lTrail, sTitle, lBody in readHubSpotAll(sFolder):
        sTop = lTrail[0].lower() if lTrail else ""
        if sTop not in dHubSpotGuides and sGuide == "account": logging.info("HubSpot: top category %r not named, so in the account guide: %s", sTop, sTitle)
        if dHubSpotGuides.get(sTop, "account") != sGuide: continue
        # Android and Mac are outside this collection's surfaces; an article for one alone is left out.
        if re.search(r"(?i)\bandroid\b", sTitle) and not re.search(r"(?i)\b(ios|iphone|ipad)\b", sTitle): continue
        lArticles.append((": ".join(lTrail) if lTrail else sMiscellaneous, sTitle, lBody))
    logging.info("HubSpot %s: %d articles", sGuide, len(lArticles))
    return lArticles


def readHubSpotAccount(sFolder): return readHubSpotFor(sFolder, "account")
def readHubSpotCrm(sFolder): return readHubSpotFor(sFolder, "crm")
def readHubSpotData(sFolder): return readHubSpotFor(sFolder, "data")
def readHubSpotMarketing(sFolder): return readHubSpotFor(sFolder, "marketing")


def readSuno(sFolder):
    """Suno's help site: the title is the h1, the body is the page-content region,
    and the category is the LAST link of the trail printed above the heading —
    the collection the article sits in."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if "_articles_" not in sName or not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        if not oTitle: continue
        sTitle = stripTags(oTitle.group(1))
        if not sTitle: continue
        sCategory = sMiscellaneous
        # The trail's own div holds nested divs for its separator icons, so a
        # match that stops at the first closing div ends before the collection
        # name and leaves every article in Miscellaneous. It is read from the
        # trail's opening to the heading instead.
        oTrail = re.search(r'(?is)<div[^>]*class="kb-breadcrumb"[^>]*>(.*?)<h1', sMarkup)
        if oTrail:
            lCrumbs = [stripTags(sCrumb) for sCrumb in re.findall(r"(?is)<a[^>]*>(.*?)</a>", oTrail.group(1))]
            lCrumbs = [sCrumb for sCrumb in lCrumbs if sCrumb and sCrumb.lower() != "home"]
            if lCrumbs: sCategory = lCrumbs[-1]
        sBody = (findBalanced(sMarkup, r'<div[^>]*class="page-content"', "div")
                 or findBalanced(sMarkup, r"<main[^>]*>", "main"))
        if not sBody: continue
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 25: continue
        lArticles.append((sCategory, sTitle, lBody))
    return lArticles


def readAndroidAccessibility(sFolder):
    """Google's Android accessibility help centre. The article is the article
    element, the title is its h1, and the category is the FIRST crumb of the
    trail — the topic the article sits under.

    Lookout has no help centre of its own: it is documented here, beside
    TalkBack, Voice Access, Switch Access and the braille support, so the volume
    is the centre and Lookout is one of its subjects."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if "_answer_" not in sName or not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        sBody = findBalanced(sMarkup, r'<article[^>]*class="[^"]*article[^"]*"', "article")
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        if not sBody or not oTitle: continue
        sTitle = stripTags(oTitle.group(1))
        if not sTitle: continue
        lCrumbs = [stripTags(sCrumb) for sCrumb in re.findall(r'(?is)<li[^>]*breadcrumb[^>]*>(.*?)</li>', sMarkup)]
        lCrumbs = [sCrumb for sCrumb in lCrumbs if sCrumb and sCrumb.lower() != sTitle.lower()]
        sCategory = lCrumbs[0] if lCrumbs else sMiscellaneous
        # Google leaves 53 of these articles with no topic crumb at all, which
        # buries Lookout, Live Transcribe, braille and the display settings in
        # Miscellaneous. Where the trail says nothing, the article's own title
        # does: it names its subject in its first words.
        if sCategory == sMiscellaneous:
            for sWords, sLabel in [
                    (r"lookout", "Lookout: Explore your surroundings"),
                    (r"braille|brailleback", "Braille"),
                    (r"live transcribe|sound notification|live caption|caption", "Live Transcribe and captions"),
                    (r"hearing aid|hearing device|audio|mono|volume", "Hearing"),
                    (r"magnif|colou?r|contrast|text & display|display size|font", "Seeing the screen"),
                    (r"talkback", "TalkBack: Hear your screen read out loud"),
                    (r"label|clickable|touch target|contrast ratio|view |element", "Making an app accessible"),
                    (r"voice access", "Voice Access: Control a device with your voice"),
                    (r"switch|autoclick|dwell|action", "Switches and timing")]:
                if re.search(sWords, sTitle, re.I):
                    sCategory = sLabel
                    break
        oPlatform = re.search(r"(?i)Platform_?3D([A-Za-z]+)", sName)
        if oPlatform:
            sPlatform = {"android": "Android", "desktop": "Computer",
                         "ios": "iPhone and iPad"}.get(oPlatform.group(1).lower(), oPlatform.group(1))
            sTitle = sTitle + " (" + sPlatform + ")"
        lArticles.append((sCategory, sTitle, toMarkdown(sBody, 0)))
    return lArticles


def readPlainLanguage(sFolder):
    """The federal plain-language guide, at its new home on digital.gov. Its
    chapters are the four sections of the guide, and each page's own first
    section heading is the article's title — the h1 names the chapter rather
    than the page, so a reader given the h1 alone would meet "Principles of
    plain language" five times over.

    The topic index pages are the site's own listing of everything tagged plain
    language. They are kept as one article each, because they name material that
    lives elsewhere on digital.gov and a reader may want the pointers."""
    dChapters = {"principles": "Principles of plain language",
                 "writing": "Writing in plain language",
                 "design": "Designing for plain language",
                 "test": "Testing plain language"}
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        sBody = findBalanced(sMarkup, r"<article[^>]*>", "article") or findBalanced(sMarkup, r"<main[^>]*>", "main")
        if not sBody: continue
        oHeading = re.search(r"(?is)<h[12][^>]*>(.*?)</h[12]>", sBody)
        oFirst = re.search(r"(?is)<h2[^>]*>(.*?)</h2>", sBody)
        sTitle = stripTags((oFirst or oHeading).group(1)) if (oFirst or oHeading) else ""
        if not sTitle: continue
        sCategory = "The guide"
        for sKey, sLabel in dChapters.items():
            if re.search(r"_plain-language_" + sKey, sName): sCategory = sLabel
        if "_topics_" in sName:
            sCategory = "More plain-language material on digital.gov"
            oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sBody)
            sTitle = stripTags(oTitle.group(1)) if oTitle else "Plain language"
            oPage = re.search(r"_page_(\d+)", sName)
            if oPage: sTitle = sTitle + ", page " + oPage.group(1)
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 30: continue
        lArticles.append((sCategory, sTitle, lBody))
    return lArticles


def readDocsSite(sFolder, sCategoryRule=None, sSkipPattern=""):
    """A documentation site: the title is the h1 and the body is the main
    region. Used for Quarto, reveal.js and others built the same way."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        if sSkipPattern and re.search(sSkipPattern, sName): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        sTitle = stripTags(oTitle.group(1)).rstrip("#¶").strip() if oTitle else ""
        if not sTitle:
            oPageTitle = re.search(r"(?is)<title[^>]*>(.*?)</title>", sMarkup)
            sTitle = re.sub(r"\s*[–|-]\s*(Quarto|reveal\.js|MediaWiki).*$", "",
                            stripTags(oPageTitle.group(1))).strip() if oPageTitle else ""
        if not sTitle: continue
        sBody = (findBalanced(sMarkup, r'<main[^>]*id="quarto-document-content"', "main")
                 or findBalanced(sMarkup, r'<div[^>]*id="mw-content-text"', "div")
                 or findBalanced(sMarkup, r"<main[^>]*>", "main")
                 or findBalanced(sMarkup, r'<div[^>]*class="[^"]*(content|prose)', "div"))
        if not sBody: continue
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 40: continue
        sCategory = sCategoryRule(sName, sTitle) if sCategoryRule else sMiscellaneous
        lArticles.append((sCategory, sTitle, lBody))
    return lArticles


def readQuarto(sFolder):
    """Quarto's documentation groups itself by the first folder of its address —
    guide, computations, authoring, output-formats, dashboards and the rest."""
    def category(sName, sTitle):
        oSection = re.search(r"quarto\.org_docs_([a-z0-9-]+)", sName)
        if not oSection: return sMiscellaneous
        sWord = oSection.group(1).replace("-", " ")
        return {"get started": "Getting started", "output formats": "Output formats",
                "authoring": "Authoring", "computations": "Computations",
                "dashboards": "Dashboards", "websites": "Websites",
                "books": "Books", "presentations": "Presentations",
                "publishing": "Publishing", "projects": "Projects",
                "extensions": "Extensions", "reference": "Reference",
                "prerelease": "Prerelease features", "download": "Downloading Quarto",
                "cli": "The command line", "faq": "Frequently asked questions",
                "tools": "Tools and editors", "manuscripts": "Manuscripts",
                "interactive": "Interactive documents", "blog": "Blog"}.get(sWord, sWord.capitalize())
    return readDocsSite(sFolder, category)


def readReveal(sFolder):
    """reveal.js publishes one page per feature under /docs/."""
    def category(sName, sTitle):
        if re.search(r"revealjs\.com_(installation|markup|presentation-size|themes|config)", sName):
            return "Setting up a presentation"
        if re.search(r"revealjs\.com_(fragments|auto-animate|transitions|backgrounds|media|math|code|slide-visibility)", sName):
            return "What a slide can do"
        if re.search(r"revealjs\.com_(api|events|plugins|internal-links|keyboard|speaker-view|pdf-export)", sName):
            return "Controlling a presentation"
        return sMiscellaneous
    return readDocsSite(sFolder, category)


def readMediaWiki(sFolder):
    """MediaWiki's Help: pages.

    The page title always begins "Help :", which is the namespace rather than
    the article's name, so it comes off. The categories are read from the title
    that remains, because MediaWiki gives these pages no trail of their own.

    The pages about RUNNING a wiki — extensions, the interface, sysadmin
    matters — are left out under the rule that this collection documents using
    software rather than administering it."""
    oAdministrator = re.compile(r"(?i)(extension|sysadmin|maintenance|api|configur|install|"
                                r"manage blocks|patroll|oauth|bots|import|lint error|magic word|"
                                r"cite|map data|merge history|abuse|block|protect)")
    lArticles = []
    iAdmin = 0
    for sCategory, sTitle, lBody in readDocsSite(sFolder, None, r"(?i)(action=|oldid=|printable=)"):
        sName = re.sub(r"(?i)^help\s*:\s*", "", sTitle).strip()
        if oAdministrator.search(sName):
            iAdmin += 1
            continue
        sCategory = sMiscellaneous
        for sPattern, sLabel in [
                (r"(?i)(edit|format|wikitext|link|image|table|template|list|section|preview|revert|undo|move|redirect)",
                 "Writing and editing pages"),
                (r"(?i)(talk|discussion|notification|watchlist|email|user page|signature|ping|echo)",
                 "Talking to other people"),
                (r"(?i)(search|navigat|categor|special page|contents|all pages|namespace|go button|history|diff|recent)",
                 "Finding your way around"),
                (r"(?i)(preference|skin|mobile|accessib|language|keyboard|display)",
                 "Settings and appearance"),
                (r"(?i)(file|upload|media|image page|download|export|print)",
                 "Files and media"),
                (r"(?i)(log in|account|password|create account|email confirm)",
                 "Your account")]:
            if re.search(sPattern, sName):
                sCategory = sLabel
                break
        lArticles.append((sCategory, sName, lBody))
    logging.info("MediaWiki: %d pages about running a wiki left out", iAdmin)
    return lArticles


def readMuse(sFolder):
    """Meta's help pages for Muse, gathered through Edge because Meta refuses a
    plain request. The title is the h1 and the body is the article region.

    The categories are read from what each article is ABOUT, because Meta prints
    no trail above these pages and gives them numbers rather than paths. The two
    pages that are Meta talking about its product rather than helping a user of
    it — the product page and the Meta AI chat page — are kept apart from the
    help itself."""
    dCategory = [
        (r"(?i)(get started|try muse|download)", "Getting started"),
        (r"(?i)(privacy|safety|security|your muse data|don.t use muse)", "Privacy, safety and your data"),
        # Payments had one article of its own, which the two-article rule would
        # fold into Miscellaneous — a poor home for the page about Muse spending
        # money. It sits with the rest of what Muse does instead.
        (r"(?i)(connector|payment|purchase|billing)", "What Muse can do for you"),
        (r"(?i)(connector|files and apps|browses the web|skills|artifact|reminder|scheduled task|personality|memories|guidance|approval)", "What Muse can do for you"),
    ]
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        sTitle = stripTags(oTitle.group(1)) if oTitle else ""
        if not sTitle:
            oPageTitle = re.search(r"(?is)<title[^>]*>(.*?)</title>", sMarkup)
            sTitle = stripTags(oPageTitle.group(1)).split("|")[0].strip() if oPageTitle else ""
        if not sTitle: continue
        sBody = (findBalanced(sMarkup, r"<article[^>]*>", "article")
                 or findBalanced(sMarkup, r"<main[^>]*>", "main")
                 or findBalanced(sMarkup, r"<body[^>]*>", "body"))
        if not sBody: continue
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 40: continue
        # The product page, the Meta AI chat page and the help centre's own index
        # are Meta talking ABOUT Muse rather than helping a user of it.
        sCategory = "What Meta says about Muse"
        if re.search(r"(?i)(help center|features & capabilities|start a chat)", sTitle):
            lArticles.append((sCategory, sTitle, lBody))
            continue
        if re.search(r"(?i)muse", sTitle) or "help_artificial" in sName:
            sCategory = "Using Muse"
            for sPattern, sLabel in dCategory:
                if re.search(sPattern, sTitle):
                    sCategory = sLabel
                    break
        lArticles.append((sCategory, sTitle, lBody))
    return lArticles


def readHumanWare(sFolder):
    """HumanWare's support pages and the Victor Reader Stream user guide.

    THE GUIDE IS PUBLISHED IN EIGHT LANGUAGES AS EIGHT NEARLY IDENTICAL FILES,
    and the language is in the FILE NAME rather than the address — AR-UG, DA-UG,
    NL-UG, a Swedish "del 1 av 1", a French "Guide d'utilisation", and a German
    edition filed under the English name. So the language is decided by READING
    the page: a guide is kept only when its own contents heading is in English.

    The manual is one long page, split here at its numbered chapters."""
    lArticles = []
    iTranslated = 0
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        lHeadings = [stripTags(sHeading) for sHeading in re.findall(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)][:3]
        sJoined = " ".join(lHeadings)
        if "_uploads_" in sName:
            if not re.search(r"(?i)(table of contents|overview of)", sJoined):
                iTranslated += 1
                continue
            lMarks = [(oMatch.start(), oMatch.end(), stripTags(oMatch.group(1)))
                      for oMatch in re.finditer(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)]
            for iIndex, (iStart, iAfter, sTitle) in enumerate(lMarks):
                iEnd = lMarks[iIndex + 1][0] if iIndex + 1 < len(lMarks) else len(sMarkup)
                sTitle = re.sub(r"^\d+[.\s]+", "", sTitle).strip()
                if not sTitle: continue
                lBody = toMarkdown(sMarkup[iAfter:iEnd], 0)
                if len(" ".join(lBody).split()) < 30: continue
                lArticles.append(("The Victor Reader Stream user guide", sTitle, lBody))
            continue
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        if not oTitle: continue
        sTitle = stripTags(oTitle.group(1))
        sBody = findBalanced(sMarkup, r"<main[^>]*>", "main") or findBalanced(sMarkup, r"<body[^>]*>", "body")
        if not sBody or not sTitle: continue
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 30: continue
        lArticles.append(("HumanWare product support", sTitle, lBody))
    logging.info("HumanWare: %d translated editions of the same guide left out", iTranslated)
    return lArticles


def readRim(sFolder):
    """RIM's manual publishes one page per topic under each platform, and every
    page carries the same h1 — the product's name. The PAGE'S OWN h2 is its
    title, and the h3 headings beneath it are its sections, so the platform and
    the page together make the category and the sections make the articles."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        # The change log is a version-by-version list of fixes — 99 entries on
        # macOS alone, more than every other page together. It is history rather
        # than help, and it would swamp the guide.
        if not sName.endswith(".html") or "pneumasolutions" in sName or "changelog" in sName: continue
        sMarkup = readText(os.path.join(sFolder, sName))
        sPlatform = ("Windows" if "_windows_" in sName else
                     "macOS" if "_macos_" in sName else "About RIM")
        oPage = re.search(r"(?is)<h2[^>]*>(.*?)</h2>", sMarkup)
        sPage = stripTags(oPage.group(1)) if oPage else ""
        if not sPage:
            oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
            sPage = stripTags(oTitle.group(1)) if oTitle else sName
        sCategory = sPlatform if sPlatform == "About RIM" else sPlatform + ": " + sPage
        sScope = findBalanced(sMarkup, r"<main[^>]*>", "main") or sMarkup
        lMarks = [(oMatch.start(), oMatch.end(), stripTags(oMatch.group(1)))
                  for oMatch in re.finditer(r"(?is)<h3[^>]*>(.*?)</h3>", sScope)]
        if not lMarks:
            lBody = toMarkdown(sScope, 0)
            if len(" ".join(lBody).split()) >= 30:
                lArticles.append((sCategory, sPage, lBody))
            continue
        for iIndex, (iStart, iAfter, sTitle) in enumerate(lMarks):
            iEnd = lMarks[iIndex + 1][0] if iIndex + 1 < len(lMarks) else len(sScope)
            if not sTitle: continue
            lBody = toMarkdown(sScope[iAfter:iEnd], 0)
            if len(" ".join(lBody).split()) < 20: continue
            lArticles.append((sCategory, sTitle + " (" + sPlatform + ")", lBody))
    return lArticles


def readFormsPages(sFolder, sProductName, sReader):
    """Neither Google nor Microsoft gives Forms a help centre of its own, so the
    harvest carries neighbours reached from the Forms pages. An article is kept
    only when its OWN TITLE is about forms, quizzes, surveys or responses."""
    oSubject = re.compile(r"(?i)(\bforms?\b|\bquiz|\bsurvey|\bresponses?\b)")
    lKept, iOther = [], 0
    for tArticle in sReader(sFolder):
        if oSubject.search(tArticle[1]):
            lKept.append(tArticle)
        else:
            iOther += 1
    logging.info("%s: %d articles left out as neighbours rather than Forms", sProductName, iOther)
    return lKept


def readGoogleForms(sFolder):
    return readFormsPages(sFolder, "Google Forms", readGoogleMeet)


def readMicrosoftForms(sFolder):
    return readFormsPages(sFolder, "Microsoft Forms", readNarratorLike)


def readNarratorLike(sFolder):
    """Microsoft's support articles: body is the main region, title its h1."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        sBody = (findBalanced(sMarkup, r'<main[^>]*id="supMainContent"', "main")
                 or findBalanced(sMarkup, r"<main[^>]*>", "main"))
        if not oTitle or not sBody: continue
        sTitle = stripTags(oTitle.group(1))
        if not sTitle: continue
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 25: continue
        sCategory = "Using Microsoft Forms"
        if re.search(r"(?i)quiz", sTitle): sCategory = "Quizzes"
        elif re.search(r"(?i)(response|result|analy)", sTitle): sCategory = "Responses and results"
        elif re.search(r"(?i)(share|collaborat|co-author)", sTitle): sCategory = "Sharing and collaborating"
        elif re.search(r"(?i)(setting|theme|brand|design)", sTitle): sCategory = "Settings and appearance"
        elif re.search(r"(?i)(admin|tenant|policy|security|data)", sTitle): sCategory = "Administration and data"
        lArticles.append((sCategory, sTitle, lBody))
    return lArticles


def readNarrator(sFolder):
    """Microsoft's complete guide to Narrator: numbered chapters and lettered
    appendices, each its own page. The chapter number gives the order, and the
    body is the support article region."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html") or "narrator" not in sName.lower(): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        if not oTitle: continue
        sTitle = stripTags(oTitle.group(1))
        if not sTitle: continue
        sBody = (findBalanced(sMarkup, r'<main[^>]*id="supMainContent"', "main")
                 or findBalanced(sMarkup, r"<main[^>]*>", "main")
                 or findBalanced(sMarkup, r"<body[^>]*>", "body"))
        if not sBody: continue
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 25: continue
        sCategory = "The guide"
        if re.search(r"_chapter-", sName): sCategory = "The chapters"
        elif re.search(r"_appendix-", sName): sCategory = "The appendices"
        elif re.search(r"(what-s-new|whats-new|new-in)", sName): sCategory = "What is new"
        lArticles.append((sCategory, sTitle, lBody))
    return lArticles


def readNvdaScripting(sFolder):
    """Two documents from two publishers, in one volume.

    NV Access's developer guide is a plain page whose headings nest five deep.
    The add-on team's guide is a GitHub wiki page, so its body is the wiki
    content region and the page furniture around it has to go.

    The old community page at addons.nvda-project.org is kept because it says in
    its own words that it has moved, which is worth a reader knowing."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        if re.search(r"[0-9a-f]{40}|_history", sName): continue
        sBook = ("The NVDA developer guide" if "developerGuide" in sName
                 else "The add-on development guide" if "Development-Guide" in sName
                 else "The add-on team's wiki" if "DevGuide_wiki" in sName
                 else "The old community page")
        sMarkup = readText(os.path.join(sFolder, sName))
        sScope = (findBalanced(sMarkup, r'<div[^>]*class="[^"]*markdown-body', "div")
                  or findBalanced(sMarkup, r"<body[^>]*>", "body") or sMarkup)
        lTokens = sorted([(oMatch.start(), oMatch.end(), 2, stripTags(oMatch.group(1)))
                          for oMatch in re.finditer(r"(?is)<h2[^>]*>(.*?)</h2>", sScope)] +
                         [(oMatch.start(), oMatch.end(), 3, stripTags(oMatch.group(1)))
                          for oMatch in re.finditer(r"(?is)<h3[^>]*>(.*?)</h3>", sScope)])
        sCategory = sBook
        if not lTokens:
            lBody = toMarkdown(sScope, 0)
            oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sScope)
            if len(" ".join(lBody).split()) >= 40:
                lArticles.append((sBook, stripTags(oTitle.group(1)) if oTitle else sBook, lBody))
            continue
        for iIndex, (iStart, iAfter, iLevel, sTitle) in enumerate(lTokens):
            iEnd = lTokens[iIndex + 1][0] if iIndex + 1 < len(lTokens) else len(sScope)
            sTitle = re.sub(r"^\d+(\.\d+)*\.?\s+", "", sTitle).strip().rstrip("¶#")
            if not sTitle or sTitle.lower() in ("pages", "clone this wiki locally", "footer"): continue
            lBody = toMarkdown(sScope[iAfter:iEnd], 0)
            if iLevel == 2:
                sCategory = sBook + ": " + sTitle
                if len(" ".join(lBody).split()) >= 40:
                    lArticles.append((sCategory, sTitle, lBody))
                continue
            if len(" ".join(lBody).split()) < 25: continue
            lArticles.append((sCategory, sTitle, lBody))
    return lArticles


def readNvdaGuide(sFolder):
    """NV Access publishes the user guide as one long page and the key commands as
    another. Both are split at their own headings: a level-two heading becomes a
    category and a level-three heading becomes an article, with everything below
    left where it is.

    The changes file is gathered but not built into this guide. It is 89,433
    words of release notes — more than the user guide itself — and a reader
    looking for how to use NVDA should not have to walk past every fix since 2006
    to reach it."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html") or "changes" in sName: continue
        sMarkup = readText(os.path.join(sFolder, sName))
        sBook = "The user guide" if "userGuide" in sName else "Key commands"
        lTokens = sorted([(oMatch.start(), oMatch.end(), 2, stripTags(oMatch.group(1)))
                          for oMatch in re.finditer(r"(?is)<h2[^>]*>(.*?)</h2>", sMarkup)] +
                         [(oMatch.start(), oMatch.end(), 3, stripTags(oMatch.group(1)))
                          for oMatch in re.finditer(r"(?is)<h3[^>]*>(.*?)</h3>", sMarkup)])
        sCategory = sBook
        for iIndex, (iStart, iAfter, iLevel, sTitle) in enumerate(lTokens):
            iEnd = lTokens[iIndex + 1][0] if iIndex + 1 < len(lTokens) else len(sMarkup)
            sTitle = re.sub(r"^\d+(\.\d+)*\.?\s+", "", sTitle).strip()
            if not sTitle: continue
            lBody = toMarkdown(sMarkup[iAfter:iEnd], 0)
            if iLevel == 2:
                sCategory = sBook + ": " + sTitle if sBook == "Key commands" else sTitle
                if len(" ".join(lBody).split()) >= 40:
                    lArticles.append((sCategory, sTitle, lBody))
                continue
            if len(" ".join(lBody).split()) < 25: continue
            lArticles.append((sCategory, sTitle, lBody))
    return lArticles


def readMermaid(sFolder):
    """Mermaid's documentation, published with VitePress: the body is the main
    region and the title is its h1, which carries an invisible anchor character
    that has to come off. The categories are its own sections — the syntax pages
    are the bulk and the point."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        if not oTitle: continue
        sTitle = stripTags(oTitle.group(1)).replace("\u200b", "").rstrip("#¶ ").strip()
        if not sTitle: continue
        sBody = (findBalanced(sMarkup, r"<main[^>]*>", "main")
                 or findBalanced(sMarkup, r'<div[^>]*class="[^"]*(vp-doc|content)', "div")
                 or findBalanced(sMarkup, r"<body[^>]*>", "body"))
        if not sBody: continue
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 30: continue
        sCategory = "About Mermaid"
        if "_syntax_" in sName: sCategory = "Diagram syntax"
        elif "_intro" in sName: sCategory = "Getting started"
        elif "_ecosystem_" in sName: sCategory = "Tools that use Mermaid"
        elif "_news" in sName: sCategory = "About Mermaid"
        lArticles.append((sCategory, sTitle, lBody))
    return lArticles


def readTypora(sFolder):
    """Typora's support site, one page per topic."""
    return readSimplePages(sFolder, "Using Typora")


def readZettlr(sFolder):
    """Zettlr's documentation, one page per topic."""
    return readSimplePages(sFolder, "Using Zettlr")


def readTexLive(sFolder):
    """TeX Live's own pages. Several have no heading at all, so the title element
    carries the name."""
    return readSimplePages(sFolder, "Installing and running TeX Live")


def readSimplePages(sFolder, sProductName, sCategoryRule=None):
    """A plain documentation site: the title is the h1 (or the page's own title
    element where there is none) and the body is the main region."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith((".html", ".htm")): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        sTitle = stripTags(oTitle.group(1)).rstrip("#¶").strip() if oTitle else ""
        if not sTitle:
            oPageTitle = re.search(r"(?is)<title[^>]*>(.*?)</title>", sMarkup)
            sTitle = stripTags(oPageTitle.group(1)) if oPageTitle else ""
            sTitle = re.sub(r"\s*[|-]\s*(TeX Live|Typora|Zettlr).*$", "", sTitle).strip()
        if not sTitle: continue
        sBody = (findBalanced(sMarkup, r'<main[^>]*>', "main")
                 or findBalanced(sMarkup, r'<div[^>]*class="[^"]*(inner-page|theme-default-content|content)', "div")
                 or findBalanced(sMarkup, r"<body[^>]*>", "body"))
        if not sBody: continue
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 30: continue
        sCategory = sCategoryRule(sName) if sCategoryRule else sProductName
        lArticles.append((sCategory, sTitle, lBody))
    return lArticles


def readTypora(sFolder):
    """Typora's support site groups its pages by the first path segment."""
    def category(sName):
        if "Markdown-Reference" in sName: return "The Markdown reference"
        if re.search(r"(?i)(export|print|pdf)", sName): return "Exporting and printing"
        if re.search(r"(?i)(theme|style|css|appearance)", sName): return "Themes and appearance"
        if re.search(r"(?i)(image|diagram|math|table)", sName): return "Images, diagrams and tables"
        if re.search(r"(?i)(licen|purchase|activat|account)", sName): return "Licence and activation"
        return "Using Typora"
    return readSimplePages(sFolder, "Typora", category)


def readZettlr(sFolder):
    """Zettlr's documentation groups itself by the section in its address."""
    def category(sName):
        oSection = re.search(r"docs\.zettlr\.com_en_([a-z-]+)_", sName)
        if not oSection: return "Zettlr"
        return oSection.group(1).replace("-", " ").capitalize()
    return readSimplePages(sFolder, "Zettlr", category)


def readTexLive(sFolder):
    """TeX Live's pages are plain HTML with no headings at all, so the title
    comes from the page's own title element."""
    return readSimplePages(sFolder, "TeX Live")


def readJupyter(sFolder):
    """Jupyter's documentation, minus the parts about the Jupyter project itself,
    which the fence now refuses: what is left is installing, running and using
    notebooks. Published with Sphinx, so the body is the article region and the
    title is its h1 with the anchor mark stripped."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        sBody = (findBalanced(sMarkup, r'<article[^>]*class="[^"]*bd-article', "article")
                 or findBalanced(sMarkup, r"<article[^>]*>", "article")
                 or findBalanced(sMarkup, r"<main[^>]*>", "main"))
        if not oTitle or not sBody: continue
        sTitle = stripTags(oTitle.group(1)).rstrip("#¶").strip()
        if not sTitle: continue
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 30: continue
        sCategory = "Using Jupyter"
        if "_install" in sName: sCategory = "Installing Jupyter"
        elif "_start" in sName: sCategory = "Getting started"
        elif "_running" in sName: sCategory = "Running a notebook server"
        elif "_reference" in sName: sCategory = "Reference"
        elif "_glossary" in sName: sCategory = "Reference"
        lArticles.append((sCategory, sTitle, lBody))
    return lArticles


def readCalibre(sFolder):
    """Calibre's manual, minus its source-code listings and its translated
    editions, which the fence now refuses but this harvest still contains."""
    lArticles = readSphinxManual(sFolder, "The calibre manual",
                                 r"(_modules|/(zh|et|pt|de|fr|es|it|ja|ru)_|calibre-ebook\.com_(zh|et|pt|de|fr|es|it|ja|ru)_)")
    return lArticles


def readMiktex(sFolder):
    """MiKTeX publishes short answers under two headings — its FAQ and its
    how-to pages — and a manual on a second host. The address says which."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        if not oTitle: continue
        sTitle = stripTags(oTitle.group(1))
        if not sTitle: continue
        sBody = (findBalanced(sMarkup, r"<main[^>]*>", "main")
                 or findBalanced(sMarkup, r'<div[^>]*class="[^"]*content', "div")
                 or sMarkup[oTitle.end():])
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 20: continue
        sCategory = "About MiKTeX"
        if "_faq_" in sName: sCategory = "Frequently asked questions"
        elif "_howto_" in sName: sCategory = "How to"
        elif "docs.miktex.org" in sName: sCategory = "The MiKTeX manual"
        elif "_kb_" in sName: sCategory = "Knowledge base"
        lArticles.append((sCategory, sTitle, lBody))
    return lArticles


def readTodoist(sFolder):
    """Todoist's help articles: the title is the h1, the body is what follows it,
    and the category is the LAST crumb of the trail printed above the heading —
    "Reminders & Notifications" rather than the broad "Features"."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if "_help_articles_" not in sName or not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        if not oTitle: continue
        sTitle = stripTags(oTitle.group(1))
        if not sTitle: continue
        sCategory = sMiscellaneous
        oTrail = re.search(r'(?is)<nav[^>]*aria-label="Breadcrumb"[^>]*>(.*?)</nav>', sMarkup)
        if oTrail:
            lCrumbs = [stripTags(sCrumb) for sCrumb in re.findall(r"(?is)<a[^>]*>(.*?)</a>", oTrail.group(1))]
            lCrumbs = [sCrumb for sCrumb in lCrumbs if sCrumb]
            if lCrumbs: sCategory = lCrumbs[-1]
        lBody = toMarkdown(sMarkup[oTitle.end():], 0)
        if len(" ".join(lBody).split()) < 25: continue
        lArticles.append((sCategory, sTitle, lBody))
    return lArticles


def readMicrosoftToDo(sFolder):
    """Microsoft's support articles: the body is the main region and the title is
    its h1. Microsoft prints no trail, so the category is taken from the left-hand
    navigation heading the page belongs to, and where that is absent the article
    goes under the product's own name."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        sBody = findBalanced(sMarkup, r'<main[^>]*id="supMainContent"', "main") or findBalanced(sMarkup, r"<main[^>]*>", "main")
        if not oTitle or not sBody: continue
        sTitle = stripTags(oTitle.group(1))
        if not sTitle: continue
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 25: continue
        lArticles.append(("Microsoft To Do", sTitle, lBody))
    return lArticles


def readInternetArchive(sFolder):
    """The Internet Archive's help site is WordPress: an article is a page under
    /help/, its title is the h1 in the hero band, and its body is the section
    beneath. Two kinds of file in the harvest are NOT articles and are skipped
    here — the site's own programming interface (wp-json) and the comment feeds,
    which the fence should have refused before they were ever fetched."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        if "wp-json" in sName or sName.endswith("_feed.html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        if not oTitle: continue
        sTitle = stripTags(oTitle.group(1))
        if not sTitle: continue
        sBody = findBalanced(sMarkup, r'<section[^>]*class="section"', "section") or findBalanced(sMarkup, r"<body[^>]*>", "body")
        if not sBody: continue
        # The page prints its own trail, and the LAST category crumb is the useful
        # one: "Reporting problems or errors" rather than the broad "Archive.org".
        # Reading the category from the FILE NAME instead put 124 of 159 articles
        # in one bucket.
        sCategory = sMiscellaneous
        oTrail = re.search(r'(?is)<nav[^>]*class="breadcrumb[^"]*"[^>]*>(.*?)</nav>', sMarkup)
        if oTrail:
            lCrumbs = [stripTags(sCrumb) for sUrl, sCrumb in
                       re.findall(r'(?is)<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', oTrail.group(1))
                       if "/help/category/" in sUrl]
            if lCrumbs: sCategory = lCrumbs[-1]
        elif re.search(r"_help_category_", sName):
            sCategory = re.search(r"_help_category_([a-z0-9-]+)", sName).group(1).replace("-", " ").title()
        lArticles.append((sCategory, sTitle, toMarkdown(sBody, 0)))
    return lArticles


def readTMobile(sFolder):
    """T-Mobile puts the article's title and its trail inside the ATTRIBUTES of a
    custom element rather than in the page's text: heading-label carries the
    title and accent-label carries the breadcrumb as escaped markup. So the
    title is read from there rather than from an h1, of which these pages have
    none at all."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        # The attribute values hold escaped markup, ">" included, so the element
        # cannot be matched by stopping at the first ">": it is matched to its
        # own closing tag instead.
        oStack = re.search(r"(?is)<title-stack\b(.*?)</title-stack>", sMarkup)
        if not oStack: continue
        sAttributes = html.unescape(oStack.group(1))
        oHeading = re.search(r'(?is)heading-label="([^"]*)"', sAttributes)
        sTitle = stripTags(oHeading.group(1)) if oHeading else ""
        # The crumbs are inside SINGLE-quoted attributes within a double-quoted
        # one, so stripTags leaves the tail of the enclosing tag behind: a
        # category arrived as "Account'> Account". Only the visible text is kept.
        lCrumbs = [stripTags(sCrumb).split(">")[-1].strip()
                   for sCrumb in re.findall(r"(?is)<a[^>]*>(.*?)</a>", sAttributes)]
        lCrumbs = [sCrumb for sCrumb in lCrumbs if sCrumb and sCrumb.lower() != "support"]
        sCategory = lCrumbs[-1] if lCrumbs else sMiscellaneous
        sBody = findBalanced(sMarkup, r'<div[^>]*class="[^"]*page_content', "div") or findBalanced(sMarkup, r"<main[^>]*>", "main")
        if not sBody or not sTitle: continue
        lArticles.append((sCategory, sTitle, toMarkdown(sBody, 0)))
    return lArticles


def readAtt(sFolder):
    """AT&T's support articles: the body is the main article container, the title
    is its h1, and the category is the last crumb of the trail AT&T prints above
    it — Wireless, Internet, TV and so on, which are the publisher's own."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        if not oTitle: continue
        sTitle = stripTags(oTitle.group(1))
        sBody = (findBalanced(sMarkup, r'<div[^>]*class="[^"]*SupportArticleContainer_mainArticle', "div")
                 or findBalanced(sMarkup, r'<div[^>]*class="[^"]*SupportArticleContainer_articleContainer', "div"))
        if not sBody or not sTitle: continue
        oTrail = re.search(r'(?is)<ol[^>]*aria-label="Breadcrumb"[^>]*>(.*?)</ol>', sMarkup)
        lCrumbs = [stripTags(sCrumb) for sCrumb in re.findall(r"(?is)<a[^>]*>(.*?)</a>", oTrail.group(1))] if oTrail else []
        lCrumbs = [sCrumb for sCrumb in lCrumbs if sCrumb and sCrumb.lower() not in ("home", "support")]
        sCategory = lCrumbs[-1] if lCrumbs else sMiscellaneous
        lArticles.append((sCategory, sTitle, toMarkdown(sBody, 0)))
    return lArticles


def readFreedomScientific(sFolder):
    """Freedom Scientific publishes in four shapes on two hosts, and each needs
    its own container: Surf's Up and the teachers' lessons are plain old pages
    whose body is a content div; the support and product pages are a modern
    template whose body is the site-content region.

    The category is taken from the address, because that is where this publisher
    puts the subject: /SurfsUp/ is the web-navigation course, /teachers/lessons/
    is the teaching course, /Services/ and /training/ are the training and
    certification pages, and so on."""
    dNames = {"surfsup": "Surf's Up — browsing the web with JAWS",
              "teachers": "Lessons for teachers",
              "services": "Training and certification",
              "training": "Training resources",
              "accessibilitytraining": "Accessibility training",
              "webinars": "Webinars",
              "products": "Products",
              "about": "About Freedom Scientific",
              "support": "Support",
              "forms": "Forms and requests",
              "visionloss": "Living with vision loss"}
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith((".html", ".htm")): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        sTitle = stripTags(oTitle.group(1)) if oTitle else ""
        # MANY OF THE LESSON PAGES ARE TRANSCRIPTS WITH NO HEADING AT ALL: their
        # title is in the title element and their body is the whole page. Reading
        # only h1 threw away 139 of the 143 teaching pages.
        if not sTitle:
            oPageTitle = re.search(r"(?is)<title[^>]*>(.*?)</title>", sMarkup)
            sTitle = stripTags(oPageTitle.group(1)) if oPageTitle else ""
            sTitle = re.sub(r"\s*[|-]\s*Freedom Scientific.*$", "", sTitle).strip()
        if not sTitle: continue
        sBody = (findBalanced(sMarkup, r'<div[^>]*id="content"', "div")
                 or findBalanced(sMarkup, r'<div[^>]*class="[^"]*site-content', "div")
                 or findBalanced(sMarkup, r"<main[^>]*>", "main")
                 or findBalanced(sMarkup, r"<body[^>]*>", "body"))
        if not sBody: continue
        sCategory = sMiscellaneous
        for sKey, sLabel in dNames.items():
            if re.search(r"[_/.]" + sKey, sName, re.I): 
                sCategory = sLabel
                break
        lArticles.append((sCategory, sTitle, toMarkdown(sBody, 0)))
    return lArticles


def readSwordAndScale(sFolder):
    """Sword and Scale runs a Freshdesk help desk, the same shape as Slate's and
    Nature's: the first heading on the page is the site's name rather than the
    article's, and the folder the article sits in is its category."""
    dFolders = {}
    for sName in sorted(os.listdir(sFolder)):
        if "_solutions_folders_" not in sName or not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<title[^>]*>(.*?)</title>", sMarkup)
        if not oTitle: continue
        sFolderName = html.unescape(oTitle.group(1)).split(":")[0].strip()
        for oLink in re.finditer(r'href="([^"]*/solutions/articles/(\d+)[^"]*)"', sMarkup):
            dFolders[oLink.group(2)] = sFolderName
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if "_solutions_articles_" not in sName or not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        lTitles = [stripTags(s) for s in re.findall(r"(?is)<h[12][^>]*>(.*?)</h[12]>", sMarkup)]
        lTitles = [re.sub(r"\s*Print\s*$", "", s).strip() for s in lTitles]
        lTitles = [s for s in lTitles if s and s.lower() not in ("support", "sword and scale")]
        if not lTitles: continue
        oId = re.search(r"_articles_(\d+)", sName)
        sCategory = dFolders.get(oId.group(1) if oId else "", sMiscellaneous)
        sBody = findBalanced(sMarkup, r'<[a-z]+[^>]*id="article-body"', "div") or findBalanced(sMarkup, r"<article[^>]*>", "article")
        if not sBody: continue
        lArticles.append((sCategory, lTitles[0], toMarkdown(sBody, 0)))
    return lArticles


def readRiskShow(sFolder):
    """RISK! publishes no help centre. What it does publish for a listener is a
    contact page saying how to pitch a story and where to find the community, and
    a support page saying how to donate. Those are the two pages read here; the
    page titled "Help!" is an episode catalogue marked under construction and is
    left out, as is the About page, which is about the show rather than for the
    listener."""
    lArticles = []
    for sName, sCategory, sPattern in [("www.risk-show.com_contactus.html", "Taking part and getting in touch", "5"),
                                       ("www.risk-show.com_support.html", "Supporting the show", "2")]:
        sPath = os.path.join(sFolder, sName)
        if not os.path.isfile(sPath): continue
        sMarkup = readText(sPath)
        dManifest = readManifest(sFolder)
        sMarkup = absolutize(sMarkup, dManifest.get(sName, "https://www.risk-show.com/"))
        lTokens = [(oMatch.start(), oMatch.end(), stripTags(oMatch.group(1)))
                   for oMatch in re.finditer(r"(?is)<h" + sPattern + r"[^>]*>(.*?)</h" + sPattern + ">", sMarkup)]
        for iIndex, (iStart, iAfter, sTitle) in enumerate(lTokens):
            iEnd = lTokens[iIndex + 1][0] if iIndex + 1 < len(lTokens) else len(sMarkup)
            if not sTitle: continue
            if re.match(r"(?i)^(the risk! newsletter|post navigation)$", sTitle): continue
            lBody = toMarkdown(sMarkup[iAfter:iEnd], 0)
            if len(" ".join(lBody).split()) < 15: continue
            lArticles.append((sCategory, sTitle.rstrip("…").strip(), lBody))
    return lArticles


def readAtlassian(sFolder):
    """Atlassian's documentation: the article is the topic container marked as the
    main content, its title is the page's h1, and its category is the last crumb
    of the breadcrumb trail — "Create and edit content", "Manage space roles" and
    so on, which are the publisher's own groupings."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if "_docs_" not in sName or not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        sBody = findBalanced(sMarkup, r'<article[^>]*id="maincontent"', "article")
        if not oTitle or not sBody: continue
        oTrail = re.search(r'(?is)<nav aria-label="Breadcrumbs".*?</nav>', sMarkup)
        lCrumbs = [stripTags(sCrumb) for sCrumb in re.findall(r"(?is)<li[^>]*>(.*?)</li>", oTrail.group(0))] if oTrail else []
        lCrumbs = [sCrumb for sCrumb in lCrumbs if sCrumb]
        sCategory = lCrumbs[-1] if lCrumbs else sMiscellaneous
        sTitle = stripTags(oTitle.group(1))
        # A few pages never close their heading, so the "title" swallows the whole
        # article. A title that long is not a title: fall back to the page's own
        # title element, and say so in the log rather than shipping a heading
        # hundreds of words long.
        if len(sTitle) > 200:
            oPageTitle = re.search(r"(?is)<title[^>]*>(.*?)</title>", sMarkup)
            sPageTitle = stripTags(oPageTitle.group(1)).split("|")[0].strip() if oPageTitle else ""
            logging.warning("heading ran to %d characters in %s; using the page title '%s' instead",
                            len(sTitle), sName[:60], sPageTitle[:60])
            sTitle = sPageTitle
        if not sTitle: continue
        lArticles.append((sCategory, sTitle, toMarkdown(sBody, 0)))
    return lArticles


def readMoth(sFolder):
    """The Moth publishes its answers as an accordion: an h2 names a group, and
    each question is the button that opens its own panel. The panel that follows
    the button is the answer."""
    sPath = os.path.join(sFolder, "www.themoth.org_about_faq.html")
    if not os.path.isfile(sPath): return []
    sMarkup = readText(sPath)
    lTokens = sorted([(oMatch.start(), "category", stripTags(oMatch.group(1)))
                      for oMatch in re.finditer(r"(?is)<h2[^>]*>(.*?)</h2>", sMarkup)] +
                     [(oMatch.start(), "question", stripTags(oMatch.group(2)))
                      for oMatch in re.finditer(r'(?is)<button[^>]*id="accordion-heading-(\d+)"[^>]*>(.*?)</button>', sMarkup)])
    lArticles = []
    sCategory = sMiscellaneous
    for iIndex, (iStart, sKind, sText) in enumerate(lTokens):
        if sKind == "category":
            if sText and sText.lower() not in ("about", "your queue", "extras"): sCategory = sText
            continue
        iEnd = lTokens[iIndex + 1][0] if iIndex + 1 < len(lTokens) else len(sMarkup)
        sPanel = findBalanced(sMarkup[iStart:iEnd], r'<div[^>]*id="accordion-panel-\d+"', "div")
        if not sPanel or not sText: continue
        lArticles.append((sCategory, sText, toMarkdown(sPanel, 0)))
    return lArticles


def readCrimeCon(sFolder):
    """CrimeCon publishes its FAQ twice over: as an accordion a reader clicks,
    and as structured FAQ data for search engines. The structured data is the
    better source — every question with its own answer, nothing to guess — and
    the four blocks of it match the four headings the page prints above them."""
    lNames = ["General questions", "Badge questions", "Programming questions", "Participating questions"]
    sPath = os.path.join(sFolder, "www.crimecon.com_faq.html")
    if not os.path.isfile(sPath): return []
    sMarkup = readText(sPath).replace('\\"', '"').replace("\\\\", "\\").replace("\\n", "\n").replace("\\/", "/")
    lArticles = []
    iBlock = 0
    for oMatch in re.finditer(r'(?is)<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', sMarkup):
        try:
            dPayload = json.loads(oMatch.group(1))
        except Exception as oError:
            logging.warning("a structured data block was not readable: %s", oError)
            continue
        if not isinstance(dPayload, dict) or dPayload.get("@type") != "FAQPage": continue
        sCategory = lNames[iBlock] if iBlock < len(lNames) else sMiscellaneous
        iBlock += 1
        for dQuestion in dPayload.get("mainEntity", []):
            sTitle = stripTags(str(dQuestion.get("name") or ""))
            sAnswer = (dQuestion.get("acceptedAnswer") or {}).get("text") or ""
            if not sTitle or not sAnswer.strip(): continue
            lArticles.append((sCategory, sTitle, toMarkdown(sAnswer, 0)))
    return lArticles


def readVogueService(sFolder):
    """Vogue's answers are published by its subscription service, in two shapes:
    an accordion whose h4 is the question and whose panel body is the answer, and
    an older page whose topics are bold lines. Error pages are skipped by title,
    since the host answers 200 even when it has nothing to give."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<title[^>]*>(.*?)</title>", sMarkup)
        sPageTitle = stripTags(oTitle.group(1)) if oTitle else ""
        if sPageTitle.lower().startswith("error"):
            logging.info("skipped an error page: %s", sName)
            continue
        sCategory = ("Vogue Digital subscriptions" if "/VO3/" in sName or "_VO3_" in sName
                     else "Vogue print subscriptions")
        lPanels = [(oMatch.start(), oMatch.end(), stripTags(oMatch.group(1)))
                   for oMatch in re.finditer(r'(?is)<h4[^>]*class="panel-title"[^>]*>(.*?)</h4>', sMarkup)]
        if lPanels:
            for iIndex, (iStart, iAfter, sQ) in enumerate(lPanels):
                iEnd = lPanels[iIndex + 1][0] if iIndex + 1 < len(lPanels) else len(sMarkup)
                if sQ: lArticles.append((sCategory, sQ, toMarkdown(sMarkup[iAfter:iEnd], 0)))
            continue
        lTokens = [(oMatch.start(), stripTags(oMatch.group(1)))
                   for oMatch in re.finditer(r"(?is)<b>(.*?)</b>", sMarkup)]
        for iIndex, (iStart, sQ) in enumerate(lTokens):
            iEnd = lTokens[iIndex + 1][0] if iIndex + 1 < len(lTokens) else len(sMarkup)
            if not sQ or len(sQ) > 90: continue
            if sQ.isupper(): continue
            if re.match(r"(?i)^(toll[- ]free|phone|e-?mail|fax|mail)\b", sQ): continue
            lArticles.append(("Managing your Vogue account", sQ, toMarkdown(sMarkup[iStart:iEnd], 0)))
    return lArticles


def absolutize(sMarkup, sBase):
    """Makes every link in a fragment absolute against the page it came from, and
    drops a one-time session field from it. A relative link is useless in a guide,
    and a session field changes on every visit, which would make the same guide
    look different every time it was built."""
    def rewrite(oMatch):
        sUrl = urllib.parse.urljoin(sBase, html.unescape(oMatch.group(1)))
        oParts = urllib.parse.urlsplit(sUrl)
        lKeep = [(sField, sValue) for sField, sValue in urllib.parse.parse_qsl(oParts.query)
                 if sField.lower() not in ("nonce", "lsid", "vid", "sid", "cslogin")]
        sUrl = urllib.parse.urlunsplit((oParts.scheme, oParts.netloc, oParts.path,
                                        urllib.parse.urlencode(lKeep), oParts.fragment))
        return 'href="' + sUrl + '"'
    return re.sub(r'(?i)href="([^"]+)"', rewrite, sMarkup)


def readSmithsonian(sFolder):
    """Smithsonian's subscriber service is run by a contractor: each answer sits in
    a block of its own with a bold underlined title."""
    lArticles = []
    dManifest = readManifest(sFolder)
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        sMarkup = absolutize(sMarkup, dManifest.get(sName, "https://ssl.drgnetwork.com/SMT/cs/gidSMALL/"))
        if re.search(r'(?i)type="password"', sMarkup):
            logging.info("skipped a sign-in page: %s", sName)
            continue
        for oMatch in re.finditer(r'(?is)<div[^>]*id="([a-z0-9_-]+)"[^>]*>', sMarkup):
            sBlock = findBalanced(sMarkup[oMatch.start():], r"<div", "div")
            oTitle = re.search(r"(?is)<u>(.*?)</u>", sBlock[:600])
            if not oTitle: continue
            sTitle = stripTags(oTitle.group(1))
            if not sTitle: continue
            lArticles.append(("Subscriber service", sTitle, toMarkdown(sBlock, 0)))
    return lArticles


def foldSmallCategories(lArticles):
    """A category holding fewer than two articles is not a category."""
    dCounts = {}
    for sCategory, sTitle, lBody in lArticles: dCounts[sCategory] = dCounts.get(sCategory, 0) + 1
    return [((sCategory if dCounts[sCategory] >= iMinCategory else sMiscellaneous), sTitle, lBody)
            for sCategory, sTitle, lBody in lArticles]


def dedupe(lArticles):
    """Keeps the fullest copy when the same title arrives twice."""
    dBest = {}
    for sCategory, sTitle, lBody in lArticles:
        sKey = (sCategory, sortKeyTitle(sTitle))
        if sKey not in dBest or len(" ".join(lBody)) > len(" ".join(dBest[sKey][2])): dBest[sKey] = (sCategory, sTitle, lBody)
    return list(dBest.values())


def disambiguate(lArticles):
    """A publisher may file one article under two categories, and both copies are
    kept so a reader browsing either category finds it. The repeated title then
    carries its category, so that no two headings — and no two anchors — are the
    same."""
    dCounts = {}
    for sCategory, sTitle, lBody in lArticles:
        sKey = sortKeyTitle(sTitle)
        dCounts.setdefault(sKey, set()).add(sCategory)
    lOut = []
    lTaken = set()
    for sCategory, sTitle, lBody in lArticles:
        if len(dCounts[sortKeyTitle(sTitle)]) > 1: sTitle = sTitle.rstrip() + " (" + sCategory + ")"
        # Last resort, so that no two headings can ever share an anchor: if the
        # category did not tell them apart, the first words of the answer do.
        if makeAnchor(sTitle) in lTaken:
            sFirst = " ".join(" ".join(lBody).split()[:6])
            sTitle = sTitle.rstrip() + " (" + sFirst + ")" if sFirst else sTitle
        lTaken.add(makeAnchor(sTitle))
        lOut.append((sCategory, sTitle, lBody))
    return lOut


# Categories that document BUILDING SOFTWARE ON a product rather than USING it.
# The line, in his words: a technically minded reader is welcome — command-line
# options, configuration files, even a code-shaped feature met in the product's
# own interface — but nothing that assumes the reader writes code against an
# interface meant for programmers. Named one by one so the decision is auditable.
dDeveloperCategories = {
    "Handshake.md": ["API"],
    "Reddit.md": ["Developer Platform & Data API Usage"],
    "Todoist.md": ["Developers"],
}


def dropDeveloperMaterial(lArticles, sOutputPath):
    """Removes the developer categories named for this guide, and says how many."""
    lNames = dDeveloperCategories.get(os.path.basename(sOutputPath), [])
    if not lNames: return lArticles
    lKept = [tArticle for tArticle in lArticles if tArticle[0].strip() not in lNames]
    logging.info("%s: %d articles left out as developer material (%s)",
                 os.path.basename(sOutputPath), len(lArticles) - len(lKept), ", ".join(lNames))
    return lKept


def uniqueSubheadings(lLines, sArticleAnchor, setArticleAnchors):
    """Gives an article's own heading an identifier of its own when Pandoc would otherwise give it an article's.

    A CONTENTS ENTRY MUST LAND ON ITS ARTICLE (version 2, 11 November 2026). GoodMaps' "Building & Destination
    Information Cards" has a heading "Favorites" of its own, and comes before the article "Favorites", so Pandoc gave
    the first one the identifier "favorites" and the contents entry jumped to the wrong place. A heading inside an
    article whose identifier an article would have is now written with an explicit one, the article's identifier
    first ("building-destination-information-cards-favorites"), which Pandoc keeps as it is."""
    lOut, iFence = [], 0
    for sLine in lLines:
        oFence = re.match(r"\s*(`{3,})", sLine)
        if oFence:
            iRun = len(oFence.group(1))
            if not iFence: iFence = iRun
            elif iRun >= iFence: iFence = 0
        oHeading = None if iFence else re.match(r"^(#{4,6}) (.+?)\s*$", sLine)
        if oHeading and makeAnchor(oHeading.group(2)) in setArticleAnchors and not oHeading.group(2).endswith("}"):
            sLine = "%s %s {#%s-%s}" % (oHeading.group(1), oHeading.group(2), sArticleAnchor, makeAnchor(oHeading.group(2)))
        lOut.append(sLine)
    return lOut


# SECRETS ARE NEVER PUBLISHED, EVEN AN EXAMPLE (1.287.1, 24 November 2026). Stripe's help shows sample keys such as
# sk_test_ followed by twenty-four letters and digits, and GitHub's push protection refused the whole push of
# Stripe.htm as holding a "Stripe Test API Secret Key", five times. A help guide needs the shape of a key, never its
# letters, so every string shaped like a secret key, token or access key is cut to its prefix with "(key left out)".
# The patterns are the well-known ones GitHub scans for: Stripe secret and restricted keys, GitHub tokens, AWS access
# keys, Slack tokens and Google API keys. A publishable Stripe key (pk_) is meant to be public and stays.
lSecretPatterns = [
    (r"\b((?:sk|rk)_(?:test|live)_)[A-Za-z0-9]{8,}", "Stripe key"),
    (r"\b(whsec_)[A-Za-z0-9]{16,}", "Stripe webhook secret"),
    (r"\b(gh[pousr]_)[A-Za-z0-9]{30,}", "GitHub token"),
    (r"\b(github_pat_)[A-Za-z0-9_]{30,}", "GitHub token"),
    (r"\b(AKIA)[0-9A-Z]{16}\b", "AWS access key"),
    (r"\b(xox[abposr]-)[A-Za-z0-9-]{10,}", "Slack token"),
    (r"\b(AIza)[0-9A-Za-z_-]{35}", "Google API key"),
]


def maskSecrets(sText):
    """Returns the text with every secret-shaped string cut to its prefix, and how many were cut."""
    iCut = 0
    for sPattern, sKind in lSecretPatterns:
        sText, iCount = re.subn(sPattern, lambda oMatch: oMatch.group(1) + "(key left out)", sText)
        iCut += iCount
    return sText, iCut


def maskSecretsInGuides(sOutput):
    """Masks secret-shaped strings in every guide already in the collection, so a guide whose harvest is gone is
    mended too; a guide changed here is newer than its page, so fixPages --changed makes its page again. Returns the
    guides changed."""
    lChanged = []
    for sName in sorted(os.listdir(sOutput)):
        if not sName.lower().endswith(".md"): continue
        sPath = os.path.join(sOutput, sName)
        try: sText = io.open(sPath, "r", encoding=sEncoding, newline="").read()
        except Exception as oError:
            logging.error("secrets: could not read %s: %s", sName, oError)
            continue
        sMasked, iCut = maskSecrets(sText)
        if not iCut: continue
        io.open(sPath, "w", encoding=sEncoding, newline="").write(sMasked)
        logging.info("secrets: %s: %d secret-shaped string%s cut to the prefix", sName, iCut, "" if iCut == 1 else "s")
        lChanged.append(sName)
    return lChanged


def buildGuide(sProduct, sTitle, sPreamble, lArticles, sOutputPath):
    """Writes one guide and returns its text."""
    # Disambiguate BEFORE folding small categories, not after: folding moves
    # articles into Miscellaneous, and two articles that were distinguished by
    # their categories then arrive in the same one carrying the same title.
    lArticles = foldSmallCategories(disambiguate(dedupe(dropDeveloperMaterial(
        [tArticle for tArticle in lArticles if tArticle[2]], sOutputPath))))
    dCategories = {}
    for sCategory, sArticleTitle, lBody in lArticles: dCategories.setdefault(sCategory, []).append((sArticleTitle, lBody))
    # LICENSE (HomerDev 1.48.0): the help text is the publisher's, gathered
    # unchanged; only the guide's own arrangement and wording are CC BY-SA 4.0.
    sLicense = ("The help text belongs to its publisher and is gathered here unchanged for accessible reading. "
                "This guide's own arrangement and wording are available under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).")
    lLines = ["---", 'title: "' + sTitle + '"', "lang: en", 'license: "CC BY-SA 4.0"',
              'license_url: "https://creativecommons.org/licenses/by-sa/4.0/"', "---", "", "# " + sTitle, "", sPreamble, "", sLicense, "",
              "## Contents", ""]
    for sCategory in sorted(dCategories, key=sortKeyCategory):
        lLines.append("- " + sCategory)
        for sArticleTitle, lBody in sorted(dCategories[sCategory], key=lambda tItem: sortKeyTitle(tItem[0])):
            lLines.append("    - [" + sArticleTitle + "](#" + makeAnchor(sArticleTitle) + ")")
    lLines.append("")
    setArticleAnchors = {makeAnchor(sArticleTitle) for sCategory in dCategories for sArticleTitle, lBody in dCategories[sCategory]}
    for sCategory in sorted(dCategories, key=sortKeyCategory):
        lLines.append("## " + sCategory)
        lLines.append("")
        for sArticleTitle, lBody in sorted(dCategories[sCategory], key=lambda tItem: sortKeyTitle(tItem[0])):
            lLines.append("### " + sArticleTitle)
            lLines.append("")
            # Some publishers repeat the title as the first line of the answer;
            # under a heading that says the same thing, it is noise to a reader
            # moving by heading.
            lClean = list(renumberHeadings(balanceFences(lBody)))
            while lClean and not lClean[0].strip(): lClean.pop(0)
            if lClean and lClean[0].strip().lower() == sArticleTitle.strip().lower(): lClean.pop(0)
            lLines.extend(uniqueSubheadings(lClean, makeAnchor(sArticleTitle), setArticleAnchors))
            lLines.append("")
    lFlat = []
    for sLine in dropLitter(lLines): lFlat.extend(sLine.replace("\r\n", "\n").split("\n"))
    sText = sNewLine.join(lFlat) + sNewLine
    sText, iSecrets = maskSecrets(sText)
    if iSecrets: logging.info("%s: %d secret-shaped string%s cut to the prefix, so no key is published", sProduct, iSecrets, "" if iSecrets == 1 else "s")
    fHandle = io.open(sOutputPath, "w", encoding=sEncoding, newline="")
    fHandle.write(sText)
    fHandle.close()
    iWords = len(sText.split())
    logging.info("%s: %d articles in %d categories, %d words, %d bytes",
                 sProduct, len(lArticles), len(dCategories), iWords, len(sText.encode("utf-8")))
    for sCategory in sorted(dCategories, key=sortKeyCategory):
        logging.info("    %s: %d", sCategory, len(dCategories[sCategory]))
    return sText


def runGates(sProduct, sPath, sText):
    """Checks one finished guide and logs every result."""
    lFailures = []
    binHead = io.open(sPath, "rb").read(3)
    if binHead != b"\xef\xbb\xbf": lFailures.append("no byte order mark")
    if b"\r\n" not in io.open(sPath, "rb").read(): lFailures.append("no Windows line endings")
    # A publisher's own examples live inside fenced blocks and may look exactly
    # like headings, contents entries or links. Every structural check below
    # reads the guide WITH THE FENCED BLOCKS REMOVED.
    # A fence CLOSES only on a run of backticks at least as long as the one that
    # opened it. A four-backtick fence exists precisely because the publisher's
    # own example contains three, and treating that inner three as a close puts
    # the rest of the article outside the block.
    lOutside, iFence = [], 0
    for sLine in sText.split(sNewLine):
        oFence = re.match(r"\s*(`{3,})", sLine)
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
    lBodies = [s for s in re.split(r"(?m)^### .+$", sBare)[1:]]
    lWordCounts = sorted(len(s.split()) for s in lBodies)
    iMedian = lWordCounts[len(lWordCounts) // 2] if lWordCounts else 0
    if iMedian < 25: lFailures.append("the median article holds only %d words" % iMedian)
    bInCode = False
    lBare = []
    # THE FRONT MATTER IS NOT PROSE (12 October 2026): the guide's own license_url, written by this builder since
    # 2 October, failed this gate in every guide built here. Lines before the closing "---" are left out.
    lLines = sText.split(sNewLine)
    if lLines and lLines[0].strip().lstrip("\ufeff") == "---":
        iEnd = next((i for i in range(1, len(lLines)) if lLines[i].strip() == "---"), 0)
        lLines = lLines[iEnd + 1:]
    for sLine in lLines:
        if sLine.strip().startswith("```"):
            bInCode = not bInCode
            continue
        if bInCode: continue
        sProse = "".join(sLine.split("`")[0::2])
        if re.search(r"(?<![\(\[])\bhttps?://[A-Za-z0-9-]+\.[A-Za-z]{2,}", sProse) and not re.search(r"\]\(https?://", sProse): lBare.append(sProse)
    if lBare: lFailures.append("%d lines carry a bare address" % len(lBare))
    lAnchors = {makeAnchor(s) for s in re.findall(r"^### (.+)$", sBare, re.M)}
    # ONLY the contents list is checked. The builder writes internal links there
    # and nowhere else, and a publisher writing about Markdown puts example
    # links in its prose — Reddit's wiki guide does exactly that.
    for oMatch in re.finditer(r"\]\(#([^\)]+)\)", sContents):
        if oMatch.group(1) not in lAnchors: lFailures.append("broken internal link: " + oMatch.group(1))
    if iFence: lFailures.append("a code fence is left open at the end of the guide")
    lTitles = re.findall(r"^### (.+)$", sBare, re.M)
    lSeenAnchors = set()
    for sHeading in lTitles:
        sAnchor = makeAnchor(sHeading)
        if sAnchor in lSeenAnchors: lFailures.append("two articles share the anchor " + sAnchor)
        lSeenAnchors.add(sAnchor)
    iLevel = 1
    for oMatch in re.finditer(r"(?m)^(#{1,6}) ", sBare):
        iThis = len(oMatch.group(1))
        if iThis > iLevel + 1: lFailures.append("heading level jumps from %d to %d" % (iLevel, iThis))
        iLevel = iThis
    for sFailure in lFailures[:10]: logging.error("GATE FAILED for %s: %s", sProduct, sFailure)
    logging.info("%s gates: %d articles, median %d words, %d failures", sProduct, iArticles, iMedian, len(lFailures))
    return lFailures


# DOUG LEE'S SCRIPTED APPS (2 November 2026). Two readers for the estates makeHarvester gathered that are not
# Zendesk listings; Discord and TeamSpeak go through readZendesk.

def afterFirstHeading(sMarkup):
    """The markup after its first heading, so an article does not open with its own title a second time."""
    oHeading = re.search(r"(?is)<h[1-3][^>]*>.*?</h[1-3]>", sMarkup)
    return sMarkup[oHeading.end():] if oHeading else sMarkup


def readWireshark(sFolder):
    """The Wireshark User's Guide, chunked: one page per section. The category is the chapter or appendix, named
    from the guide's own contents page; each page's title is its section number and name."""
    dChapters = {"Preface": "Preface"}
    for sName in os.listdir(sFolder):
        if not sName.endswith("index.html"): continue
        for sHref, sText in re.findall(r'(?is)<a[^>]*href="([^"#]+)"[^>]*>(.*?)</a>', readText(os.path.join(sFolder, sName))):
            sText = stripTags(sText).replace("\xa0", " ").strip()
            # A chapter or appendix is a contents entry with one number or letter; the preface's own numbered
            # entries come first in the list and are not chapters. The category is the name alone, so the
            # categories sort by name, as the collection's guides do, rather than 11 before 2.
            oMatch = re.match(r"^([0-9]+|[A-Z])\.\s+(.+)$", sText)
            if oMatch and not sHref.startswith("Pre"): dChapters[oMatch.group(1)] = oMatch.group(2)
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html") or sName.endswith("index.html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<title[^>]*>(.*?)</title>", sMarkup)
        sTitle = stripTags(oTitle.group(1)).replace("\xa0", " ").strip() if oTitle else ""
        if not sTitle: continue
        sBody = (findBalanced(sMarkup, r'<div[^>]*class="(section|chapter|appendix|preface)"', "div") or "")
        if not sBody: continue
        sBody = re.sub(r'(?is)<div[^>]*class="nav(header|footer)".*?</div>', "", afterFirstHeading(sBody))
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 25: continue
        oNumber = re.match(r"^(?:Chapter\s+|Appendix\s+)?([0-9]+|[A-Z])\.", sTitle)
        sKey = oNumber.group(1) if oNumber and "_chunked_Pre" not in sName else "Preface"  # the preface numbers its sections 1 to 7 too
        lArticles.append((dChapters.get(sKey, sMiscellaneous), sTitle, lBody))
    return lArticles


def readVirtualAudioCable(sFolder):
    """The Virtual Audio Cable user manual: the article is the ContentFrame and its first h1 the title. The category
    is the manual's own contents: each page sits under the top-level entry of the contents list that links to it.
    The driver and filter API page is developer material and is left out, as the collection's rule asks."""
    # The manual's contents list is flat, one entry per page, so it offers no categories; the pages are grouped by
    # subject here, and the preamble says so.
    dGroups = {"main": "Getting started", "principles": "Getting started", "features": "Getting started",
               "sysreq": "Getting started", "install": "Getting started", "upgrade": "Getting started",
               "uninstall": "Getting started", "simple": "Using cables", "advanced": "Using cables",
               "examples": "Using cables", "howto": "Using cables", "ctlpan": "Using cables", "repeater": "Using cables",
               "configure": "Using cables", "defdev": "Using cables", "troubles": "Problems and answers",
               "faq": "Problems and answers", "dsound": "Problems and answers", "layers": "Problems and answers",
               "winbugs": "Problems and answers", "compat": "Problems and answers", "glossary": "About the product",
               "history": "About the product", "distrib": "About the product", "support": "About the product"}
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        sBody = findBalanced(sMarkup, r'<div[^>]*class="ContentFrame"', "div")
        if not sBody: continue
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sBody)
        sTitle = stripTags(oTitle.group(1)).strip() if oTitle else ""
        if not sTitle or re.search(r"\bAPI\b", sTitle): continue
        sTitle = re.sub(r"^fdu(?=[A-Z])", "", sTitle)  # a stray "fdu" before "Advanced cable usage" in the publisher's heading
        lBody = toMarkdown(afterFirstHeading(sBody), 0)
        if len(" ".join(lBody).split()) < 25: continue
        sPage = re.sub(r"^vac\.muzychenko\.net_en_manual_?", "", sName)[:-5].replace(".htm", "") or "main"
        lArticles.append((dGroups.get(sPage, sMiscellaneous), sTitle, lBody))
    return lArticles


def readThreeCx(sFolder):
    """The 3CX user manual: one page per app or feature, the article in the page's googledoc block. 3CX gives no
    groups above its pages, so they are grouped by subject, and the preamble says so."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        sMarkup = re.sub(r"(?is)<(script|style)\b.*?</\1>", "", readText(os.path.join(sFolder, sName)))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        sTitle = stripTags(oTitle.group(1)).strip() if oTitle else ""
        sBody = findBalanced(sMarkup, r'<div[^>]*class="[^"]*\bgoogledoc\b', "div")
        if not sTitle or not sBody: continue
        if sTitle.isupper(): sTitle = sTitle.capitalize().replace("3cx", "3CX")
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 40: continue
        sLower = sTitle.lower()
        sCategory = ("Apps and phones" if re.search(r"app|client|deskphone", sLower)
                     else "Meetings and conferencing" if re.search(r"conferenc|meet", sLower) else sMiscellaneous)
        lArticles.append((sCategory, sTitle, lBody))
    return lArticles


def readMicroSip(sFolder):
    """MicroSIP's two pages: the documentation, one article per section, and the questions page as one article."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        sMarkup = re.sub(r"(?is)<(script|style)\b.*?</\1>", "", readText(os.path.join(sFolder, sName)))
        sMarkup = re.sub(r"(?is)<h1[^>]*>\s*Please allow ads.*?</h1>(\s*<p>.*?</p>)?", "", sMarkup)
        sMain = findBalanced(sMarkup, r"<main[^>]*>", "main") or ""
        if not sMain: continue
        if "faq" in sName:
            lBody = toMarkdown(afterFirstHeading(sMain), 0)
            if len(" ".join(lBody).split()) >= 40: lArticles.append((sMiscellaneous, "Frequently asked questions", lBody))
            continue
        lParts = re.split(r"(?is)(<h2[^>]*>.*?</h2>)", afterFirstHeading(sMain))
        for iIndex in range(1, len(lParts) - 1, 2):
            sTitle = stripTags(lParts[iIndex]).strip()
            lBody = toMarkdown(lParts[iIndex + 1], 0)
            if sTitle and len(" ".join(lBody).split()) >= 10: lArticles.append(("Documentation", sTitle, lBody))
    return lArticles


def readMuseScore(sFolder):
    """The MuseScore Studio 4 handbook: the article is the page's article element, and the category is the chapter
    named in the page's own breadcrumb trail."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        sMarkup = re.sub(r"(?is)<(script|style)\b.*?</\1>", "", readText(os.path.join(sFolder, sName)))
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sMarkup)
        sTitle = stripTags(oTitle.group(1)).strip() if oTitle else ""
        sBody = findBalanced(sMarkup, r"<article[^>]*>", "article")
        if sBody:
            sCrumbs = findBalanced(sMarkup, r'<div[^>]*block-system-breadcrumb-block', "div") or ""
            lCrumbs = [stripTags(x).strip() for x in re.findall(r"(?is)<li[^>]*>(.*?)</li>", sCrumbs)]
            lCrumbs = [x for x in lCrumbs if x and x.lower() != "home"]
            sCategory = lCrumbs[1] if len(lCrumbs) > 1 else "About the handbook"
        else:
            # THE NEW HANDBOOK (2 November 2026). Most handbook addresses now redirect to MuseScore's new handbook,
            # built with GitBook: the article is the contents block, and the chapter is the first name in the trail
            # printed above the title, after the language picker.
            sBody = findBalanced(sMarkup, r'<div[^>]*class="contents"[^>]*data-content-ref-root', "div")
            iTitle = sMarkup.find("<h1")
            sHeader = sMarkup[sMarkup.rfind("<header", 0, iTitle):iTitle] if iTitle > 0 else ""
            lCrumbs = [x.strip() for x in stripTags(re.sub(r"<[^>]+>", "|", sHeader)).split("|") if x.strip()]
            iAfter = lCrumbs.index("English (US)") + 1 if "English (US)" in lCrumbs else len(lCrumbs)
            sCategory = lCrumbs[iAfter] if iAfter < len(lCrumbs) else "About the handbook"
        if not sTitle or not sBody: continue
        sBody = re.sub(r'(?is)<(nav|ul)[^>]*class="[^"]*(book-navigation|book-traversal|links inline)[^"]*".*?</\1>', "", sBody)
        lBody = toMarkdown(afterFirstHeading(sBody), 0)
        if len(" ".join(lBody).split()) < 40: continue
        lArticles.append((sCategory, sTitle, lBody))
    return lArticles


def readTeamTalk(sFolder):
    """The TeamTalk 5 client manual, a Doxygen-built help: the title follows "TeamTalk Help:" in the page title and
    the article is the contents block. The index pages that only list other pages are left out."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html") or re.search(r"(doxygen_crawl|_pages)\.html$", sName): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        oTitle = re.search(r"(?is)<title[^>]*>(.*?)</title>", sMarkup)
        sTitle = re.sub(r"^TeamTalk Help:\s*", "", stripTags(oTitle.group(1)).strip()) if oTitle else ""
        sBody = findBalanced(sMarkup, r'<div[^>]*class="contents"', "div")
        if not sTitle or not sBody: continue
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 40: continue
        lArticles.append(("TeamTalk 5 client", sTitle, lBody))
    return lArticles


def readTeamViewer(sFolder):
    """TeamViewer's knowledge base: the title is the heading marked data-kb-title and the article the block marked
    data-kb-main-content. The category is the product and the first part of the article's address, which is how
    TeamViewer files its articles; listing pages, which have no article block, are left out."""
    lArticles = []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        oPath = re.search(r"knowledge-base_teamviewer-(classic|remote)_([a-z0-9-]+)_", sName)
        if not oPath: continue
        sMarkup = re.sub(r"(?is)<(script|style|svg)\b.*?</\1>", "", readText(os.path.join(sFolder, sName)))
        oTitle = re.search(r"(?is)<h[1-3][^>]*data-kb-title[^>]*>(.*?)</h[1-3]>", sMarkup)
        sBody = findBalanced(sMarkup, r"<div[^>]*data-kb-main-content", "div")
        if not oTitle or not sBody: continue
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 25: continue
        sProduct = "TeamViewer Classic" if oPath.group(1) == "classic" else "TeamViewer Remote"
        sTopic = oPath.group(2).replace("-", " ")
        sTopic = re.sub(r"\bteamviewer ai\b", "TeamViewer AI", sTopic)
        lArticles.append((sProduct + ": " + sTopic[:1].upper() + sTopic[1:], stripTags(oTitle.group(1)).strip(), lBody))
    return lArticles


# Winlink's site mixes help with news, history and stories from the field. Only help is kept: these titles are the
# news, history, stories and Spanish-language pages, set aside and counted in the log.
sWinlinkNotHelp = (r"presentation|wildfires|healthcare|alachua|\bSK\b|shakeout|kuwait|\bMARS\b|muddle|carpe|jungle|"
                   r"seven seas shack|early history|feature article|workshop update|articles and application stories|"
                   r"sistema|tutorial para|communications at sea|staying connected|21st century")


def readWinlink(sFolder):
    """Winlink Express and the Winlink help pages on winlink.org, grouped by subject, since the site files its pages
    by date rather than by topic; the preamble says so."""
    lArticles = []
    iSetAside = 0
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        sMarkup = re.sub(r"(?is)<(script|style)\b.*?</\1>", "", readText(os.path.join(sFolder, sName)))
        oTitle = re.search(r"(?is)<title[^>]*>(.*?)</title>", sMarkup)
        sTitle = re.sub(r"\s*\|\s*Winlink Global Radio Email\s*$", "", stripTags(oTitle.group(1))).strip() if oTitle else ""
        if not sTitle: continue
        if re.search(sWinlinkNotHelp, sTitle, re.I):
            iSetAside += 1
            continue
        sBody = (findBalanced(sMarkup, r'<div[^>]*class="[^"]*\bfield-name-body\b', "div")
                 or findBalanced(sMarkup, r'<div[^>]*class="region region-content"', "div"))
        if not sBody: continue
        lBody = toMarkdown(afterFirstHeading(sBody), 0)
        if len(" ".join(lBody).split()) < 30: continue
        sLower = sTitle.lower()
        if re.search(r"account|callsign|acceptlist|password|message|precedence|tactical|mail|e-mail", sLower): sCategory = "Accounts and messages"
        elif re.search(r"ft-991|icom|ardop|signalink|sound|packet|vara|rms|brick|airmail|pactor|gateway|hybrid|mesh|radio", sLower): sCategory = "Radios, modems and networks"
        elif re.search(r"express|form|template|propagation|picture|linux|scale|call sign folder", sLower): sCategory = "Winlink Express"
        else: sCategory = "Getting started and reference"
        lArticles.append((sCategory, sTitle, lBody))
    logging.info("Winlink: %d pages of news, history, stories or Spanish-language material set aside", iSetAside)
    return lArticles



# GOODMAPS AND AI CONTENT DESCRIBER (11 November 2026).

def allBalanced(sMarkup, sPattern, sTag):
    """Every element matching sPattern, in order, brackets balanced."""
    lOut, iAt, oPattern = [], 0, re.compile(sPattern, re.I)
    while True:
        oMatch = oPattern.search(sMarkup, iAt)
        if not oMatch: return lOut
        sBlock = findBalanced(sMarkup[oMatch.start():], sPattern, sTag)
        lOut.append(sBlock)
        iAt = oMatch.start() + max(len(sBlock), 1)


def sourceOf(sFolder, sName, sMarkup, dManifest):
    """A saved page's own address: from the manifest, else from a source comment at its top."""
    if sName in dManifest: return dManifest[sName]
    oSource = re.match(r"\s*<!-- source: (\S+) -->", sMarkup)
    return oSource.group(1) if oSource else ""


def readGoodMaps(sFolder):
    """GoodMaps' HubSpot knowledge base. The article is the page's article-wrapper: its h1 is the title, its first
    h2 a one-line summary kept as an italic lead, and its rich-text fields the body. The trail above the article
    (ol.hs-kb-breadcrumbs) names the product and the section; the section is the category.

    HubSpot draws some section headings as large bold text in a div of its own ("Highlights & Specifications");
    those become real headings. Kept: the navigation app's own articles and "What is GoodMaps?". Set aside, and
    counted in the log: GoodMaps Studio, the mapping service, the lidar scanner, the client FAQ addressed to venue
    customers, and the sales page for venues -- all written for the buildings that host GoodMaps, not its users."""
    dManifest = readManifest(sFolder)
    lArticles, lSetAside = [], []
    for sName in sorted(os.listdir(sFolder)):
        if not sName.lower().endswith((".html", ".htm")): continue
        sMarkup = readText(os.path.join(sFolder, sName))
        sWrapper = findBalanced(sMarkup, r'<div[^>]*class="[^"]*\barticle-wrapper\b', "div")
        oTitle = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", sWrapper)
        if not oTitle: continue
        sTitle = stripTags(oTitle.group(1))
        sCrumbs = findBalanced(sMarkup, r'<ol[^>]*class="[^"]*hs-kb-breadcrumbs', "ol")
        lCrumbs = [stripTags(sCrumb) for sCrumb in re.findall(r"(?is)<li[^>]*>(.*?)</li>", sCrumbs)][1:]
        bApp = lCrumbs[:1] == ["GoodMaps Navigation App"] and "client faq" not in sTitle.lower()
        bIntro = lCrumbs[:1] == ["Products and Services"] and sTitle.lower() == "what is goodmaps?"
        if not (bApp or bIntro):
            lSetAside.append(" > ".join(lCrumbs) + ": " + sTitle)
            continue
        sCategory = lCrumbs[1] if bApp and len(lCrumbs) > 1 else "About GoodMaps"
        oLead = re.search(r"(?is)<h2[^>]*inline_text_field[^>]*>(.*?)</h2>", sWrapper)
        sLead = stripTags(oLead.group(1)) if oLead else ""
        sBody = "".join(allBalanced(sWrapper, r'<div[^>]*class="[^"]*hs_cos_wrapper_type_(?:inline_richtext_field|rich_text)\b', "div"))
        # The bold text stands alone in a div or a paragraph, sometimes after a no-break space.
        sBody = re.sub(r'(?is)<(div|p)[^>]*>(?:\s|&nbsp;)*<span[^>]*style="[^"]*(?:font-size[^"]*font-weight:\s*bold|font-weight:\s*bold[^"]*font-size)[^"]*"[^>]*>(.*?)</span>(?:\s|&nbsp;)*</\1>',
                       r"<h3>\2</h3>", sBody)
        lBody = toMarkdown(sBody, 0, sourceOf(sFolder, sName, sMarkup, dManifest))
        if len(" ".join(lBody).split()) < 20: continue
        if sLead: lBody = ["*" + sLead + ("" if sLead[-1:] in ".!?" else ".") + "*", ""] + lBody
        lArticles.append((sCategory, sTitle, lBody))
    logging.info("GoodMaps: %d articles kept, %d set aside as written for venues", len(lArticles), len(lSetAside))
    for sSetAside in lSetAside: logging.info("    set aside: %s", sSetAside)
    return lArticles


def splitMarkdown(lLines, sMarker):
    """Splits Markdown lines at headings of one level, outside fenced code: (lead lines, [(title, lines)])."""
    lLead, lSections, iFence = [], [], 0
    for sLine in lLines:
        oFence = re.match(r"\s*(`{3,})", sLine)
        if oFence:
            iRun = len(oFence.group(1))
            if not iFence: iFence = iRun
            elif iRun >= iFence: iFence = 0
        oHeading = None if iFence else re.match(r"^" + re.escape(sMarker) + r" (.+?)\s*$", sLine)
        if oHeading: lSections.append((oHeading.group(1).strip(), []))
        elif lSections: lSections[-1][1].append(sLine)
        else: lLead.append(sLine)
    return lLead, lSections


def readAiContentDescriber(sFolder):
    """AI Content Describer's manual is its GitHub readme, one Markdown file. Its level-two sections are articles, and
    so are the level-three ones under Getting started and Usage, one for each AI service and each way of working.
    Set aside, as written for people changing the add-on's code: Building the add-on, How to translate? and
    Contributions."""
    lFiles = [s for s in sorted(os.listdir(sFolder)) if "readme" in s.lower()]
    if not lFiles: return []
    sText = readText(os.path.join(sFolder, lFiles[0])).replace("\r\n", "\n")
    sText = re.sub(r"^\s*<!-- source:.*?-->\s*\n", "", sText)
    # A link whose words are its own address takes the words before the colon instead; a sample address in
    # quotation marks is an example to type, so it reads as code.
    sText = re.sub(r"(\w[\w -]{0,60}): \[(https?://[^\]]+)\]\(\2\)", r"[\1](\2)", sText)
    sText = re.sub(r'"(https?://localhost[^"]*)"', r"`\1`", sText)
    lLines = [sLine.rstrip() for sLine in sText.split("\n")]
    while lLines and not lLines[0].strip(): lLines.pop(0)
    if lLines and lLines[0].startswith("# "): lLines.pop(0)
    lIntro, lSections = splitMarkdown(lLines, "##")
    dSections = dict(lSections)
    lSetAside = [s for s in ("Building the add-on", "How to translate?", "Contributions") if s in dSections]
    lArticles = [("About the add-on", "What it does", lIntro)]
    for sName in ("Features", "Use case", "Models"):
        if sName in dSections: lArticles.append(("About the add-on", sName, dSections[sName]))
    for sParent, sCategory in (("Getting started", "Setting up a model"), ("Usage", "Using the add-on")):
        if sParent not in dSections: continue
        lLead, lSubsections = splitMarkdown(dSections[sParent], "###")
        lArticles.append((sCategory, sParent, lLead))
        for sTitle, lBody in lSubsections: lArticles.append((sCategory, sTitle.rstrip(":"), lBody))
    if "Dependencies" in dSections: lArticles.append(("Using the add-on", "Dependencies", dSections["Dependencies"]))
    logging.info("AI Content Describer: %d articles from %s; set aside as developer material: %s",
                 len(lArticles), lFiles[0], ", ".join(lSetAside) or "none")
    return lArticles



# THE NOVEMBER 2026 LIST (14 November 2026): Guide, Learning Ally and LibriVox, gathered by build_release's harvestQueue.

def pageText(sMarkup):
    """A page's words, for telling copies apart: its main region without markup, spacing made even."""
    sMain = findBalanced(sMarkup, r"<main[^>]*>", "main") or sMarkup
    return re.sub(r"\s+", " ", stripTags(re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", sMain))).strip()


def readGuide(sFolder):
    """Guide (guideinteraction.com) is a small site of plain pages. Each page's first heading names it, since every
    page's title is the same tagline. Its support pages are the help; the front page holds the questions people ask;
    the blog announces each release, which is where Guide says what a version added, so the posts are kept in a
    category of their own, as Hartgen's announcements were. The blog's index, a list of the posts, is left out."""
    lArticles, setSeen = [], set()
    for sName in sorted(os.listdir(sFolder)):
        if not sName.endswith(".html"): continue
        oPath = re.match(r"www\.guideinteraction\.com(?:_(support|blog|about|organizations)(?:_(.+))?)?\.html$", sName)
        if not oPath: continue
        sArea, sSlug = oPath.group(1) or "", oPath.group(2) or ""
        if sArea == "blog" and not sSlug: continue
        sMarkup = readText(os.path.join(sFolder, sName))
        sMain = findBalanced(sMarkup, r"<main[^>]*>", "main")
        if not sMain: continue
        sText = pageText(sMarkup)
        if sText in setSeen: continue
        setSeen.add(sText)
        lHeadings = [stripTags(s) for s in re.findall(r"(?is)<h[12][^>]*>(.*?)</h[12]>", sMain)]
        if not sArea:
            # THE FRONT PAGE'S QUESTIONS ARE A MANTINE ACCORDION: each question is the label inside a button, and its
            # answer the content of the panel after it. Each pair is an article; the page above them is the overview.
            iFaq = sMain.find("mantine-Accordion-root")
            sFaq = sMain[iFaq:] if iFaq >= 0 else ""
            for oMatch in re.finditer(r'(?is)<span[^>]*mantine-Accordion-label[^>]*>(.*?)</span>', sFaq):
                sAnswer = findBalanced(sFaq[oMatch.end():], r'<div[^>]*mantine-Accordion-content', "div")
                if sAnswer: lArticles.append(("Questions people ask", stripTags(oMatch.group(1)), toMarkdown(sAnswer, 0, "https://www.guideinteraction.com/")))
            if iFaq >= 0: sMain = sMain[:sMain.rfind("<h1", 0, iFaq) if sMain.rfind("<h1", 0, iFaq) >= 0 else iFaq]
            sCategory, sTitle = "About Guide", "What Guide is"
        elif sArea in ("about", "organizations"):
            sCategory, sTitle = "About Guide", {"about": "About the company", "organizations": "Guide for organizations"}[sArea]
        elif sArea == "support" and not sSlug:
            sCategory, sTitle = "Using Guide", "Support"
        else:
            sCategory = "Using Guide" if sArea == "support" else "Releases and news"
            sTitle = lHeadings[0] if lHeadings else sSlug.replace("-", " ").capitalize()
        lBody = toMarkdown(sMain, 0, "https://www.guideinteraction.com/")
        if len(" ".join(lBody).split()) < 40: continue
        lArticles.append((sCategory, sTitle, lBody))
    return lArticles


def readLearningAlly(sFolder):
    """Learning Ally's help centre is one page of questions, each a details element whose summary is the question,
    under group headings (School Resources, Tech Support and others); learningally.org/help and /help/techsupport
    serve that same page, so it is read once. The integration pages for schools (Clever, ClassLink, Google sign-on,
    rostering) are articles of their own. The membership page that says "You're all set" confirms a purchase and is
    not help."""
    lArticles, setQuestions = [], set()
    lPages = sorted(s for s in os.listdir(sFolder) if s.endswith(".html"))
    for sName in lPages:
        sMarkup = readText(os.path.join(sFolder, sName))
        sMain = findBalanced(sMarkup, r"<main[^>]*>", "main")
        if not sMain: continue
        if '<details class="la-faq__item"' in sMain:
            sGroup = "Frequently asked questions"
            for oMatch in re.finditer(r'(?is)<h3[^>]*la-faqhub__group[^>]*>(.*?)</h3>|<details class="la-faq__item">\s*<summary>(.*?)</summary>', sMain):
                if oMatch.group(1) is not None:
                    sGroup = stripTags(oMatch.group(1))
                    continue
                sQuestion = stripTags(oMatch.group(2))
                if sQuestion.lower() in setQuestions: continue
                setQuestions.add(sQuestion.lower())
                sAnswer = findBalanced(sMain[oMatch.end():], r'<div[^>]*class="la-faq__answer"', "div")
                if not sAnswer: continue
                lArticles.append((sGroup, sQuestion, toMarkdown(sAnswer, 0, "https://learningally.org/help/")))
            continue
        lHeadings = [stripTags(s) for s in re.findall(r"(?is)<h[12][^>]*>(.*?)</h[12]>", sMain)]
        sTitle = lHeadings[0] if lHeadings else ""
        if not sTitle or re.search(r"(?i)you.re all set", sTitle): continue
        lBody = toMarkdown(sMain, 0, "https://learningally.org/help/")
        if len(" ".join(lBody).split()) < 40: continue
        lArticles.append(("Schools and integrations", sTitle, lBody))
    return lArticles


# LibriVox's wiki: what is kept and where. Every page is read through readDocsSite (the article is mw-content-text).
lLibriVoxLeftOut = [r"^staff picks", r"^great books of the western world", r"^recordings of books on the ambleside",
                    r"^boy scout", r"^penguin.s great ideas", r"^52 books", r"^exercises in knitting", r"^spotlight on",
                    r"^featured weekly", r"^archives$", r"^donat", r"^librivox in the news", r"^initial database design",
                    r"^how to update the mw", r"^torrent todo", r"^review of iriver", r"^anniversary podcast",
                    r"^any soldier", r"^prison donations", r"^librivox and ebay", r"^main page$", r"^audacity 4$",
                    r"^audacity$", r"^guides from a sound engineer", r"^how to find a reader", r"^thank you$",
                    r"^catalog project", r"^cleanup crew", r"^banners and buttons", r"^book resources",
                    r"^example 1 minute test responses", r"^peegee.s script", r"^kmerline"]
lLibriVoxCategories = [
    (r"(?i)(how to listen|how to get librivox|podcast|cd player|digital audio player|bittorrent|torrent|m4b|id3|"
     r"choosing a|what is id3)", "Listening to LibriVox"),
    (r"(?i)(proof.?listen|checker)", "Proof-listening"),
    (r"(?i)(dramatic|play coordinator|voice character)", "Dramatic readings"),
    (r"(?i)(coordinator|\bbc\b|\bmc\b|catalog|word count|solo project|shepherd|thanking a reader|cd covers|covers)",
     "Coordinating a recording"),
    (r"(?i)(audacity|noise|editing|edit |de-essing|amplif|levell|replaygain|peaks|hum|silence|compression|"
     r"splitting|split with|merging|slowing|cutting audio|audio processing|garageband|editing method|measuring volume)",
     "Editing audio"),
    (r"(?i)(record|1-minute test|microphone|vocal booth|equipment|tech specs|pronunciation|accents|software we use|"
     r"newbie|what if i suck|computer performance|send your recording|volunteer)", "Recording for LibriVox"),
    (r"(?i)(policy|policies|copyright|public domain|disclaimer|artificial intelligence|forum|language policy|rules|"
     r"glossary|questions and answers|misc q|faq|librivox|how librivox works|promotional|instructional videos)",
     "About LibriVox and its rules"),
]


def isEnglishText(sText):
    """True when a page reads as English. LibriVox's wiki carries its guides in nine languages under their own titles
    (Anleitung zum Aufnehmen, Guide pour les débutants, 新手录音指南), which no address can tell apart. A page is
    taken as another language when Chinese, Japanese or Korean characters are a fifth of its letters, or when the
    commonest words of another language outnumber those of English; a share of English words alone was too strict
    for pages that are mostly tables or lists, such as Software We Use."""
    iCjk = len(re.findall(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]", sText))
    iLetters = len(re.findall(r"[^\W\d_]", sText))
    if iLetters and iCjk / float(iLetters) > 0.2: return False
    lWords = re.findall(r"[^\W\d_']+", sText.lower())
    setEnglish = {"the", "and", "to", "of", "you", "is", "in", "that", "it", "for", "your", "this", "with", "are", "be"}
    setOther = {"der", "die", "und", "das", "ist", "nicht", "mit", "le", "la", "les", "et", "des", "est", "une", "pour",
                "el", "los", "las", "que", "y", "por", "una", "para", "o", "os", "um", "uma", "não", "il", "di", "che",
                "è", "per", "ang", "mga", "sa", "na", "ng", "de", "het", "een", "en", "van", "je"}
    iEnglish = sum(1 for s in lWords if s in setEnglish)
    iOther = sum(1 for s in lWords if s in setOther)
    return iEnglish >= iOther


def readLibriVox(sFolder):
    """LibriVox's help is its wiki. Pages saved twice, under /index.php/Title and ?title=Title, are read once; pages in
    other languages, lists of recommended books, archived announcements and the wiki's own housekeeping are left out
    and counted. Categories come from what each page is about, since the wiki gives these pages no trail."""
    lArticles, setSeen = [], set()
    iCopies = iLanguages = iLists = 0
    for sCategory, sTitle, lBody in readDocsSite(sFolder, None, r"(?i)(action=|oldid=|printable=)"):
        sTitle = re.sub(r"\s*-\s*Librivox wiki$", "", sTitle).strip()
        if sTitle.lower() in setSeen:
            iCopies += 1
            continue
        setSeen.add(sTitle.lower())
        sText = " ".join(lBody)
        if any(re.search(s, sTitle.lower()) for s in lLibriVoxLeftOut):
            iLists += 1
            continue
        if not isEnglishText(sText) or not isEnglishText(sTitle):
            iLanguages += 1
            continue
        sCategory = sMiscellaneous
        for sPattern, sLabel in lLibriVoxCategories:
            if re.search(sPattern, sTitle):
                sCategory = sLabel
                break
        lArticles.append((sCategory, sTitle, lBody))
    logging.info("LibriVox: %d articles; left out %d copies, %d pages in other languages, %d book lists, archives and housekeeping pages",
                 len(lArticles), iCopies, iLanguages, iLists)
    return lArticles


# NVDA COACH (12 November 2026): an NVDA add-on, not a web estate. Its course is six chapters of lesson files inside the
# add-on (globalPlugins\nvdaCoach\lessons\en\*.json), and its own user guide and resources page sit in doc\en.

dNvdaKeyNames = {"downarrow": "Down Arrow", "leftarrow": "Left Arrow", "numpadenter": "Numpad Enter", "pagedown": "Page Down",
                 "pageup": "Page Up", "return": "Enter", "rightarrow": "Right Arrow", "uparrow": "Up Arrow"}
lsCoachGuideSkipped = ["lessons included", "what's new", "acknowledgments", "contact the developer"]


def coachKeys(sGesture):
    """kb:control+downArrow -> Control+Down Arrow."""
    sKeys = re.sub(r"^kb(\([^)]*\))?:", "", sGesture)
    return "+".join(dNvdaKeyNames.get(s.lower(), s.upper() if len(s) == 1 else s[:1].upper() + s[1:]) for s in sKeys.split("+"))


def coachStep(dStep, iNumber):
    """One lesson step as Markdown lines: what to do, the keys, what happens, the hints, any practice text."""
    lLines = ["#### Step %d" % iNumber, ""]
    for sPara in re.split(r"\n\s*\n", (dStep.get("instruction") or "").strip()): lLines += [sPara.strip(), ""]
    lsKeys = []
    for sGesture in dStep.get("expectedGestures") or []:
        sKey = coachKeys(sGesture)
        if sKey not in lsKeys: lsKeys.append(sKey)
    if lsKeys: lLines += ["Keys: " + " or ".join(lsKeys) + ".", ""]
    if dStep.get("successMessage"): lLines += ["When it works: " + dStep["successMessage"].strip(), ""]
    lsHints = [h.strip() for h in (dStep.get("hints") or []) if h and h.strip()]
    # The Coach's F2 cycles the list of hints; a single older "hint" field is used only when a step has no list.
    if not lsHints and dStep.get("hint") and dStep["hint"].strip(): lsHints = [dStep["hint"].strip()]
    if lsHints: lLines += ["Hints:", ""] + ["- " + h for h in lsHints] + [""]
    if dStep.get("practiceText"):
        # One quoted paragraph a line: Markdown would otherwise run the practice lines together.
        lsPractice = [s.strip() for s in dStep["practiceText"].strip().split("\n") if s.strip()]
        lLines += ["Practice text:", ""] + [s for sLine in lsPractice for s in ("> " + sLine, ">")][:-1] + [""]
    return lLines


def readNVDACoach(sFolder):
    """NVDA Coach's course from the newest .nvda-addon in its harvest folder: an About category from the add-on's user
    guide and resources page (less the lesson list, the old release notes and the thanks, which the course itself and
    the repository cover), then one category per chapter in course order, one article per lesson numbered so the
    builder's alphabetical order keeps the course's order (Lesson 1.01, 1.02 ...)."""
    import zipfile
    lsAddons = sorted((s for s in os.listdir(sFolder) if s.lower().endswith(".nvda-addon")),
                      key=lambda s: [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", s.lower())])
    if not lsAddons: return []
    sAddon = os.path.join(sFolder, lsAddons[-1])
    oZip = zipfile.ZipFile(sAddon)
    sManifest = oZip.read("manifest.ini").decode("utf-8-sig", "replace")
    dManifest = dict((m.group(1).strip(), m.group(2).strip().strip('"')) for m in re.finditer(r"(?m)^(\w+)\s*=\s*(.*)$", sManifest))
    lArticles = []
    lArticles.append(("About NVDA Coach", "About this guide", [
        "Built from NVDA Coach %s, the add-on file %s. It needs NVDA %s or later, and was tested through NVDA %s." % (
            dManifest.get("version", "?"), lsAddons[-1], dManifest.get("minimumNVDAVersion", "?"), dManifest.get("lastTestedNVDAVersion", "?")), "",
        "Each lesson below is laid out as the Coach presents it: one step at a time, with the keys the step expects, what the Coach says when it works, and the hints F2 gives. In the Coach itself, F1 repeats a step and F3 skips it."]))
    for sDoc in ("doc/en/readme.html", "doc/en/resources.html"):
        if sDoc not in oZip.namelist(): continue
        sHtml = oZip.read(sDoc).decode("utf-8-sig", "replace")
        sBody = re.sub(r"(?is)^.*?<body[^>]*>|</body>.*$", "", sHtml)
        for oSection in re.finditer(r"(?is)<h2[^>]*>(.*?)</h2>(.*?)(?=<h2|$)", sBody):
            sTitle = stripTags(oSection.group(1))
            if sTitle.lower() in lsCoachGuideSkipped: continue
            lBody = toMarkdown(oSection.group(2), 0, dManifest.get("url", ""))
            if len(" ".join(lBody).split()) >= 5: lArticles.append(("About NVDA Coach", sTitle, lBody))
    lsChapters = sorted((s for s in oZip.namelist() if re.match(r"globalPlugins/nvdaCoach/lessons/en/[^/]+\.json$", s)))
    lChapters = [json.loads(oZip.read(s).decode("utf-8-sig")) for s in lsChapters]
    iSteps = 0
    for dChapter in sorted(lChapters, key=lambda d: d.get("order", 99)):
        iChapter = dChapter.get("order", 0)
        sCategory = "Chapter %d: %s" % (iChapter, dChapter.get("title", ""))
        for iLesson, dLesson in enumerate(sorted(dChapter.get("lessons", []), key=lambda d: d.get("order", 99)), 1):
            lBody = []
            if iLesson == 1 and dChapter.get("description"): lBody += ["*" + dChapter["description"].strip() + "*", ""]
            for iStep, dStep in enumerate(dLesson.get("steps", []), 1):
                lBody += coachStep(dStep, iStep)
                iSteps += 1
            lArticles.append((sCategory, "Lesson %d.%02d: %s" % (iChapter, iLesson, dLesson.get("title", "")), lBody))
    logging.info("NVDA Coach %s from %s: %d chapters, %d lessons, %d steps, %d About articles", dManifest.get("version"),
                 lsAddons[-1], len(lChapters), sum(len(d.get("lessons", [])) for d in lChapters), iSteps,
                 sum(1 for t in lArticles if t[0] == "About NVDA Coach"))
    return lArticles


# THE HOMER LAYOUT FOR A COLLECTION OF GUIDES (version 2, 11 November 2026).
#
# Before, every harvester wrote its pages, its archive and a fixed-name log beside itself, so a collection's top
# filled with get*Help scripts, harvest folders, archives and logs, and copies of kit scripts. The build settles that
# once, logging every move and never overwriting: harvesters go to scripts; harvest folders to data\harvests, which
# the builder reads and a harvester resumes over; harvest archives to results, an output; logs to logs; and copies
# of the kit's own scripts, which only drift, to notes\retired. Guides, the ReadMe, the License and the project's own
# files are left where they are.

lsHomerFolders = ["configs", "data", "help", "logs", "notes", "results", "scripts", "templates"]
lsKitScripts = ["buildguide", "buildmagazines", "buildnewguides", "checkguides", "cleanfeedback", "fixpages",
                "getllmsguide", "makeharvester"]
lsLocalLines = ["*.md", "data/", "LocalFiles.txt", "RepoFiles.txt", "results/", "scripts/"]
lsRepoLines = []   # what the repository holds is the .htm pages; scripts are local (1.208.0)


def moveInto(sSource, sFolder, lMoves):
    """Moves one file or folder into sFolder without overwriting: a name already there gains -2, -3 and so on."""
    os.makedirs(sFolder, exist_ok=True)
    sName = os.path.basename(sSource)
    sTarget = os.path.join(sFolder, sName)
    iNext = 2
    while os.path.exists(sTarget):
        sStem, sExtension = os.path.splitext(sName)
        sTarget = os.path.join(sFolder, "%s-%d%s" % (sStem, iNext, sExtension))
        iNext += 1
    shutil.move(sSource, sTarget)
    lMoves.append((sSource, sTarget))
    logging.info("MOVED %s -> %s", sSource, sTarget)
    return sTarget


def ensureLines(sPath, lsWanted, lsUnwanted, sHeader):
    """Adds each wanted line a list file lacks, and removes each unwanted one. Creates the file only when sHeader is
    given. Returns a short account for the log, or "" when nothing changed."""
    if not os.path.isfile(sPath):
        if not sHeader: return ""
        sText = ""
    else:
        sText = io.open(sPath, "rb").read().decode("utf-8-sig", errors="replace").replace("\r\n", "\n")
    lLines = sText.split("\n") if sText else []
    lsHave = [sLine.strip().replace("\\", "/").lower() for sLine in lLines]
    lAdded = [sWanted for sWanted in lsWanted if sWanted.lower() not in lsHave]
    lKept = [sLine for sLine in lLines if sLine.strip().replace("\\", "/").lower() not in [s.lower() for s in lsUnwanted]]
    lRemoved = len(lLines) - len(lKept)
    if not lAdded and not lRemoved: return ""
    if not lLines and sHeader: lKept = sHeader.split("\n")
    while lKept and not lKept[-1].strip(): lKept.pop()
    sOut = "\n".join(lKept + lAdded) + "\n"
    io.open(sPath, "wb").write(b"\xef\xbb\xbf" + sOut.replace("\n", "\r\n").encode("utf-8"))
    return "%s: added %s; removed %d line%s" % (os.path.basename(sPath), ", ".join(lAdded) or "nothing", lRemoved, "" if lRemoved == 1 else "s")


def settleLayout(sRoot):
    """Moves an older collection's loose files into the Homer folders. Returns the list of (source, target)."""
    lMoves, lsRetired = [], []
    for sName in sorted(os.listdir(sRoot)):
        sPath = os.path.join(sRoot, sName)
        sLower = sName.lower()
        sStem, sExtension = os.path.splitext(sLower)
        if os.path.isdir(sPath):
            if sName.startswith(".") or sLower in lsHomerFolders: continue
            if os.path.isfile(os.path.join(sPath, "manifest.txt")) or re.match(r"^.+(help|faqs|guide)\d*$", sLower):
                sHarvests = os.path.join(sRoot, "data", "harvests")
                sTarget = os.path.join(sHarvests, sName)
                if not os.path.exists(sTarget):
                    moveInto(sPath, sHarvests, lMoves)
                    continue
                # A later harvest of the same estate already lives in data\harvests: its pages win, and any page only
                # the older folder holds joins them.
                for sFile in sorted(os.listdir(sPath)):
                    if not os.path.exists(os.path.join(sTarget, sFile)): moveInto(os.path.join(sPath, sFile), sTarget, lMoves)
                if not os.listdir(sPath): os.rmdir(sPath)
                else: moveInto(sPath, os.path.join(sRoot, "notes", "retired"), lMoves)
            continue
        if sExtension in (".py", ".cmd") and sStem in lsKitScripts:
            moveInto(sPath, os.path.join(sRoot, "notes", "retired"), lMoves)
            lsRetired.append(sName)
        elif sExtension in (".py", ".cmd") and sLower.startswith("get"):
            sScripts = os.path.join(sRoot, "scripts")
            if os.path.exists(os.path.join(sScripts, sName)):
                moveInto(sPath, os.path.join(sRoot, "notes", "retired"), lMoves)
                lsRetired.append(sName)
            else:
                moveInto(sPath, sScripts, lMoves)
                lsRetired.append(sName)
        elif sExtension == ".log":
            moveInto(sPath, os.path.join(sRoot, "logs"), lMoves)
        elif sExtension == ".zip" and re.match(r"^.+(help|faqs)\d*(_part\d+)?\.zip$", sLower) and not sLower.endswith("_guide.zip"):
            moveInto(sPath, os.path.join(sRoot, "results"), lMoves)
    # THE scripts FOLDER HOLDS THE COLLECTION'S OWN SCRIPTS (1.208.0): its harvesters and the kit tools the build
    # refreshes there. A copy of an app-help-guide skill script (cleanFeedback.py, buildGuide, makeHarvester,
    # getLlmsGuide.py), which runs from the kit, and removeStrays.cmd, a one-off whose three deletions were done, go to
    # notes\\retired; Python's __pycache__ is deleted. The scripts\\getLlmsGuide.cmd wrapper stays: it runs the kit's.
    sScripts = os.path.join(sRoot, "scripts")
    if os.path.isdir(sScripts):
        for sName in sorted(os.listdir(sScripts)):
            sPath = os.path.join(sScripts, sName)
            sStem, sExtension = os.path.splitext(sName.lower())
            if sName == "__pycache__" and os.path.isdir(sPath):
                shutil.rmtree(sPath, ignore_errors=True)
                logging.info("DELETED %s: Python's cache, remade when needed", sPath)
            elif (sStem in ("buildguide", "buildmagazines", "cleanfeedback", "makeharvester") and sExtension in (".py", ".cmd")) \
                    or sName.lower() in ("getllmsguide.py", "removestrays.cmd"):
                moveInto(sPath, os.path.join(sRoot, "notes", "retired"), lMoves)
    # AN ANNOUNCEMENT IS A DRAFT, NOT A GUIDE (1.208.0): Announce.md and its .htm, written to post about the collection,
    # would have been published with the guides by *.htm.
    for sName in sorted(os.listdir(sRoot)):
        if re.match(r"(?i)^announce.*\.(md|htm)$", sName): moveInto(os.path.join(sRoot, sName), os.path.join(sRoot, "notes", "drafts"), lMoves)
    # A HEADING TAG NAMED IN PROSE STAYS TEXT (1.208.0). The builder has escaped such tags since 12 October, but six
    # guides built before then (Calibre, Craigslist, HumanWare, KindleDirectPublishing, OrgMode, Shopify) still had a
    # bare <h1> in a sentence about headings, which Pandoc made a real heading: up to five level-one headings a page,
    # so check refused the push. Outside code, such a tag is written &lt;h1>, which every reader shows as <h1>; the
    # source becomes newer than its page, so fixPages rebuilds the page in this same build.
    for sName in sorted(os.listdir(sRoot)):
        if not sName.lower().endswith(".md"): continue
        sPath = os.path.join(sRoot, sName)
        sText = io.open(sPath, "rb").read().decode("utf-8-sig", errors="replace")
        lLines, iFence, iFixed = sText.split("\n"), 0, 0
        for iLine, sLine in enumerate(lLines):
            oFence = re.match(r"\s*(`{3,})", sLine)
            if oFence:
                iRun = len(oFence.group(1))
                if not iFence: iFence = iRun
                elif iRun >= iFence: iFence = 0
                continue
            # An indented line is a code block in Markdown, where an entity would show literally (RevealJs' examples).
            if iFence or re.match(r"( {4}|\t)", sLine) or ("<h" not in sLine.lower() and "</h" not in sLine.lower()): continue
            lParts = re.split(r"(`[^`]*`)", sLine)
            for iPart in range(0, len(lParts), 2):
                lParts[iPart], iCount = re.subn(r"(?i)<(?=/?h[1-6](\s[^>]*)?>)", "&lt;", lParts[iPart])
                iFixed += iCount
            lLines[iLine] = "".join(lParts)
        if iFixed:
            io.open(sPath, "wb").write(b"\xef\xbb\xbf" + "\n".join(lLines).encode("utf-8"))
            logging.info("ESCAPED %d heading tag%s named in the prose of %s", iFixed, "" if iFixed == 1 else "s", sName)
    sLocal = ensureLines(os.path.join(sRoot, "LocalFiles.txt"), lsLocalLines, [],
                         "# LocalFiles.txt -- what belongs to this collection on this disk, but never in the repository.\n"
                         "# Harvested pages are kept in data\\harvests for the next build; harvest archives are outputs.")
    if sLocal: logging.info("SETTLED %s", sLocal)
    sRepo = ensureLines(os.path.join(sRoot, "RepoFiles.txt"), lsRepoLines, lsRetired + ["LocalFiles.txt", "RepoFiles.txt", "scripts/", "*.md"], "")
    if sRepo: logging.info("SETTLED %s", sRepo)
    return lMoves


def startLog(sRoot, sCollection, sTask):
    """Opens this run's log, logs\\<Collection>-<task>-<stamp>.log, in UTF-8 with a byte order mark and Windows line
    endings, and returns its path."""
    sLogs = os.path.join(sRoot, "logs")
    os.makedirs(sLogs, exist_ok=True)
    sStamp = time.strftime("%Y%m%d-%H%M%S")
    sLogPath = os.path.join(sLogs, "%s-%s-%s.log" % (sCollection, sTask, sStamp))
    iSame = 2
    while os.path.exists(sLogPath):
        sLogPath = os.path.join(sLogs, "%s-%s-%s-%d.log" % (sCollection, sTask, sStamp, iSame))
        iSame += 1
    oHandler = logging.StreamHandler(io.open(sLogPath, "w", encoding="utf-8-sig", newline="\r\n", errors="backslashreplace"))
    oHandler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logging.getLogger().addHandler(oHandler)
    logging.getLogger().setLevel(logging.INFO)
    return sLogPath


def newestTime(sFolder):
    """When a harvest was gathered. THE GATHERING, NOT THE FILES (15 November 2026): harvestQueue's --trim rewrites
    request.txt to note the trimming, so every trimmed harvest looked newer than its guide, and the build of 12:12 that
    day set about rebuilding all six Microsoft guides in silence until it was stopped. request.txt's finished= time is
    when the pages were gathered, and trimming leaves it alone; manifest.txt's date serves a harvest without one, and
    only a harvest with neither is walked file by file, which across the collection took 24 seconds."""
    dRequest = {}
    sRequest = os.path.join(sFolder, "request.txt")
    if os.path.isfile(sRequest):
        for sLine in readText(sRequest).splitlines():
            if "=" in sLine: dRequest[sLine.split("=", 1)[0].strip().lower()] = sLine.split("=", 1)[1].strip()
    if dRequest.get("finished"):
        try: return time.mktime(datetime.datetime.strptime(dRequest["finished"][:19], "%Y-%m-%d %H:%M:%S").timetuple())
        except ValueError: pass
    sManifest = os.path.join(sFolder, "manifest.txt")
    if os.path.isfile(sManifest): return os.path.getmtime(sManifest)
    nNewest = 0.0
    for sDir, lDirs, lFiles in os.walk(sFolder):
        for sFile in lFiles: nNewest = max(nNewest, os.path.getmtime(os.path.join(sDir, sFile)))
    return nNewest


def kitFolder():
    """The kit this script belongs to: scripts -> app-help-guide -> skills -> .claude -> the kit."""
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))


def pruneHarvests(sParent, sOutput, lPlan, lResults):
    """HARVESTS GO ONCE THEIR GUIDES ARE BUILT (23 November 2026, Jamal's request). data\\harvests held every page
    every harvester saved, and it takes much room. After a build, a harvest folder is deleted when every guide in the
    plan read from it is built and passes its gates: built clean in this run, or already current and passing its gates
    when checked now. Its gathering is first recorded in data\\harvested.inix by the kit's harvestQueue (version 6), so
    the next build does not gather it again. Every older gathering set aside as <Folder>-before-<day> is deleted too.
    A harvest still being gathered (request.txt without finished) is kept. A guide whose reader changes later is
    gathered again by asking for it with a later asked= day; the build says so. Each deletion is logged with its size."""
    if os.path.basename(os.path.normpath(sParent)).lower() != "harvests" or not os.path.isdir(sParent): return 0
    sData = os.path.dirname(os.path.normpath(sParent))
    try:
        import importlib.util
        oSpec = importlib.util.spec_from_file_location("harvestQueue", os.path.join(os.path.dirname(os.path.abspath(__file__)), "harvestQueue.py"))
        oQueue = importlib.util.module_from_spec(oSpec)
        oSpec.loader.exec_module(oQueue)
    except Exception as oError:
        logging.error("prune: harvestQueue could not be loaded, so no harvest was deleted: %s", oError)
        return 0
    def folderSize(sDir):
        iSize = 0
        for sRoot, lsDirs, lsFiles in os.walk(sDir):
            for sName in lsFiles:
                try: iSize += os.path.getsize(os.path.join(sRoot, sName))
                except OSError: pass
        return iSize
    dBuilt = {t[0]: t[3] for t in lResults}
    dFolderOk = {}
    for sProduct, sFolder, functionRead, sFile, sTitle, sPreamble in lPlan:
        sGuide = os.path.join(sOutput, sFile)
        if sProduct in dBuilt: bOk = dBuilt[sProduct] == 0
        elif os.path.isfile(sGuide):
            try:
                # AS WRITTEN, LINE ENDINGS AND ALL (1.287.2): the gates split a guide at its Windows line endings, as
                # buildGuide writes it. This check turned them into bare line feeds first, so every guide read as one
                # line, its contents ran to the end of the file, and 346 guides failed a gate here that they had
                # passed when built -- in every build's log, and keeping their harvests from being deleted.
                sText = io.open(sGuide, "rb").read().decode("utf-8-sig", "replace")
                bOk = not runGates(sProduct, sGuide, sText)
            except Exception: bOk = False
        else: bOk = False
        dFolderOk[sFolder] = dFolderOk.get(sFolder, True) and bOk
    lDeleted, iFreed = [], 0
    for sFolder in sorted(os.listdir(sParent), key=str.lower):
        sHarvest = os.path.join(sParent, sFolder)
        if not os.path.isdir(sHarvest): continue
        if "-before-" in sFolder: sWhy = "an older gathering set aside"
        elif dFolderOk.get(sFolder):
            dRequest = oQueue.readRequest(sHarvest)
            if dRequest and not dRequest.get("finished"):
                logging.info("prune: %s kept, since its gathering has not finished", sFolder)
                continue
            if dRequest: oQueue.writeRecord(sData, sFolder, dRequest)
            sWhy = "its guides are built and clean"
        else: continue
        iSize = folderSize(sHarvest)
        try:
            shutil.rmtree(sHarvest)
        except Exception as oError:
            logging.error("prune: %s could not be deleted: %s", sFolder, oError)
            continue
        lDeleted.append(sFolder)
        iFreed += iSize
        logging.info("prune: deleted %s, %.1f MB, since %s", sFolder, iSize / 1e6, sWhy)
    if lDeleted:
        print("Deleted %d harvest%s whose guides are built, freeing %.0f MB; data\\harvested.inix keeps the record." % (
            len(lDeleted), "" if len(lDeleted) == 1 else "s", iFreed / 1e6), flush=True)
    logging.info("prune: %d deleted, %.1f MB freed", len(lDeleted), iFreed / 1e6)
    return len(lDeleted)


def main():
    """Builds the guides whose harvests are here, gates each one, and reports what passed."""
    lArgs = sys.argv[1:]
    bBuild = "--build" in lArgs
    bChanged = bBuild or "--changed" in lArgs
    lPlain = [s for s in lArgs if not s.startswith("--")]
    if bBuild:
        sOutput = os.path.abspath(lPlain[0] if lPlain else os.getcwd())
        sParent = os.path.join(sOutput, "data", "harvests")
        lOnly = lPlain[1:]
    else:
        sOutput = os.path.abspath(lPlain[1] if len(lPlain) > 1 else ".")
        sHarvests = os.path.join(sOutput, "data", "harvests")
        sParent = os.path.abspath(lPlain[0]) if lPlain else (sHarvests if os.path.isdir(sHarvests) else os.path.abspath("."))
        lOnly = lPlain[2:]
    sCollection = os.path.basename(sOutput.rstrip("\\/")) or "Guides"
    sLogPath = startLog(sOutput, sCollection, "buildGuide")
    logging.info("buildGuide.py version 2; script %s", os.path.abspath(__file__))
    logging.info("Python %s at %s on %s; working directory %s; command line %s", platform.python_version(), sys.executable,
                 platform.platform(), os.getcwd(), " ".join(sys.argv))
    logging.info("settings: build %s; changed only %s; harvests %s; guides %s; products %s", bBuild, bChanged, sParent,
                 sOutput, ", ".join(lOnly) or "all")
    if bBuild:
        lMoves = settleLayout(sOutput)
        if lMoves: print("Settled the Homer layout: %d item%s moved; the log names each." % (len(lMoves), "" if len(lMoves) == 1 else "s"))
    lPlan = [
        ("The Atlantic", "AtlanticHelp", readZendesk, "Atlantic.md", "The Atlantic help",
         "This guide holds The Atlantic's own reader help, gathered from the publisher's own listing on 18 August 2026, so every article arrived with its title, its section and its body. It covers subscriptions, accounts, apps, newsletters and the archive rather than The Atlantic's journalism."),
        ("New Scientist", "NewScientistHelp", readNewScientist, "NewScientist.md", "New Scientist help",
         "New Scientist publishes its reader help as one long page of questions and answers rather than as separate articles. This guide holds that page, one question per heading, gathered on 18 August 2026. The categories are New Scientist's own."),
        ("Snopes", "SnopesHelp", readSnopes, "Snopes.md", "Snopes help",
         "Snopes publishes its reader help as one page of collapsible questions. This guide holds that page, one question per heading, gathered on 18 August 2026. The categories are the section titles Snopes prints above each group."),
        ("Scientific American", "SciAmHelp", readSciAm, "ScientificAmerican.md", "Scientific American reader help",
         "Scientific American publishes its reader help as a single contact page covering subscriptions, permissions and reprints. This guide holds that page, gathered on 18 August 2026, and it is short because the source is short."),
        ("The Nation", "NationHelp", readNation, "TheNation.md", "The Nation reader help",
         "The Nation publishes its reader help across two pages: a set of frequently asked questions about reading and subscribing, and a second set about donations. This guide holds both, gathered on 18 August 2026."),
        ("Nature", "NatureHelp", readNature, "Nature.md", "Nature help",
         "This guide holds the help that Springer Nature publishes for readers, authors, reviewers and librarians of Nature and its sister journals, gathered on 18 August 2026. The categories are the publisher's own, taken from the trail printed above each article. Material written for librarians and institutions is kept under its own headings rather than left out, so a reader can skip it but does not lose it."),
        ("Fire TV", "FireTvHelp", readFireTv, "FireTv.md", "Fire TV help",
         "This guide holds the help Amazon publishes for Fire TV, gathered on 18 August 2026. Amazon publishes one help estate covering everything it sells, so the gathering was held to Fire TV by reading each page's own heading before following its links, and the build sets aside any page whose title and trail never mention Fire TV. The categories are Amazon's own, taken from the trail printed above each article.\r\n\r\nThe guide covers the streaming sticks and boxes, Fire TV built into televisions and soundbars, the remotes, profiles, settings, app and playback problems, and the Recast recorder. It does not cover Amazon's other devices or its shopping account, which are documented elsewhere in the same estate.\r\n\r\nFour pages are deliberately left out. Amazon publishes the open-source software licences for its devices as help articles, and the one for the Fire TV Recast alone runs to nearly 150,000 words of package names and licence text — half again as long as everything else here put together. Safety and compliance pages are kept, because those are real device documentation; only the licence lists are gone."),
        ("Rolling Stone", "RollingStoneHelp", readRollingStone, "RollingStone.md", "Rolling Stone subscriber help",
         "Rolling Stone publishes its reader help as a handful of separate pages rather than a help centre, and this guide holds them, gathered on 18 August 2026: the customer service page, the digital subscription questions, the app questions and the charts questions. Its addresses took three attempts to find, because the obvious ones do not exist."),
        ("Airbnb", "AirbnbHelp", readAirbnb, "Airbnb.md", "Airbnb help",
         "This guide holds Airbnb's own help articles, gathered on 18 August 2026. Airbnb writes for guests and for hosts in one estate, and both are here under their own headings, so a reader who only stays in places can skip what is written for people who let them.\r\n\r\nThe run stopped at its ceiling of 1,500 pages with 489 addresses still queued, so this is most of the estate rather than all of it. A second run would resume where this one stopped."),
        ("Verizon devices", "VerizonHelp", readVerizonDevices, "VerizonDevices.md", "Verizon device guides",
         "This guide holds the part of Verizon's knowledge base that is written about individual devices: phones, tablets, watches, hotspots and home internet equipment, each with its own set of articles. It was gathered on 18 August 2026 and separated from the rest because the two halves answer different questions — this one tells you how to do something on a particular handset, and its companion, Verizon.md, covers plans, billing, accounts and the network.\r\n\r\nThe categories are Verizon's own device names. Verizon publishes a fresh set for every device it sells, so this guide is a large slice of that material rather than all of it, and a device released after the gathering date will not be here."),
        ("Verizon", "VerizonHelp", readVerizonService, "Verizon.md", "Verizon support",
         "This guide holds Verizon's own support articles, gathered on 18 August 2026, including its accessibility page: the accessible formats it offers, the equipment it supports and how to reach its disability support team.\r\n\r\nArticles written about individual handsets are not here; they are in the companion guide, VerizonDevices.md, because the two halves answer different questions and together they run to nearly three million words. Everything else Verizon publishes for a customer is in this one: plans, billing, accounts, home internet, the network, international use and accessibility."),
        ("Internet Archive", "ArchiveHelp", readInternetArchive, "InternetArchive.md", "Internet Archive help",
         "This guide holds the Internet Archive's own help, gathered on 18 August 2026: the Wayback Machine, uploading and managing items, borrowing books from Open Library, searching, accounts and the problems people most often meet. It was found by accident while probing for old-time radio archives, which is worth saying because the collection had no volume for a service this widely used."),
        ("T-Mobile", "TMobileHelp", readTMobile, "TMobile.md", "T-Mobile support",
         "This guide holds T-Mobile's own support articles, gathered on 18 August 2026. The categories are T-Mobile's own, taken from the trail it prints above each article, so a reader can go straight to devices, plans, billing or account questions.\r\n\r\nOne page is missing and should be named: T-Mobile's accessibility support page answered a probe a few hours before this run and then returned 404 to the run itself, so what it says about accessible bill formats and its dedicated accessibility team is not here. Everything else the support tree links to is."),
        ("AT&T", "AttHelp", readAtt, "Att.md", "AT&T support",
         "This guide holds AT&T's own support articles, gathered on 18 August 2026. The categories are AT&T's own, taken from the trail printed above each article, so a reader can go straight to wireless, internet or television.\r\n\r\nThis is one slice of a very large estate rather than the whole of it: the run followed the support tree from its front page and stopped when the queue ran dry, so anything AT&T publishes only behind a search box is not here."),
        ("Freedom Scientific", "FreedomScientificHelp", readFreedomScientific, "FreedomScientific.md", "Freedom Scientific help and training",
         "This guide holds what Freedom Scientific publishes for the people who use JAWS, ZoomText and Fusion, gathered on 18 August 2026 from its support and training pages.\r\n\r\nTwo of its parts are whole courses rather than help articles: Surf's Up teaches web navigation with JAWS lesson by lesson, and the teachers' lessons train the people who teach it. Both are kept in full and named as courses, because they are the most substantial free training this publisher offers.\r\n\r\nOne thing is not here and is worth knowing: the JAWS, ZoomText and Fusion user guides live in a separate documentation centre that draws its pages in the browser, so a plain request cannot read them. That remains the single most useful thing this collection does not have."),
        ("Sword and Scale", "SwordAndScaleHelp", readSwordAndScale, "SwordAndScale.md", "Sword and Scale help",
         "This guide holds the help that Sword and Scale publishes for its listeners and members, gathered on 18 August 2026. It covers the ad-free feeds, the Plus membership, apps and podcast players, billing and account questions. The categories are the publisher's own folders.\r\n\r\nOne thing to know before reading: Sword and Scale is a true crime podcast, and a few answers mention the nature of its content in passing. Nothing here describes a case."),
        ("Jira", "JiraHelp", readAtlassian, "Jira.md", "Jira help",
         "This guide holds Atlassian's own documentation for Jira, gathered on 18 August 2026. The categories are Atlassian's own, taken from the trail printed above each article.\r\n\r\nJira is used by whole teams, so its documentation covers the person working through a board and the person administering the project in the same estate. Administration material is kept under its own headings rather than left out, so a reader can skip it without losing it."),
        ("Confluence", "ConfluenceHelp", readAtlassian, "Confluence.md", "Confluence help",
         "This guide holds Atlassian's own documentation for Confluence Cloud, gathered on 18 August 2026. The categories are Atlassian's own, taken from the trail printed above each article.\r\n\r\nConfluence is used by whole teams, so its documentation covers the person writing a page and the person administering the site in the same estate. Administration material is kept under its own headings rather than left out, so a reader can skip it without losing it."),
        ("The Moth", "MothHelp", readMoth, "TheMoth.md", "The Moth help",
         "The Moth publishes its answers for listeners, members and storytellers as one page of collapsible questions, and this guide holds them, gathered on 18 August 2026. The categories are The Moth's own headings on that page."),
        ("Furnished Finder", "FurnishedFinderHelp", readZendesk, "FurnishedFinder.md", "Furnished Finder and KeyCheck help",
         "This guide holds Furnished Finder's own help, gathered on 18 August 2026 from the publisher's own listing, so every article arrived with its title, its section and its body. It serves landlords and travellers alike, and both sides are here: listings and tenant screening as much as searching and booking.\r\n\r\nKeyCheck is Furnished Finder's sister company, and its help is published inside the same help centre rather than separately, so it is in this guide too — six articles name it in their titles and about forty mention it. Two limits worth knowing: tenant screening and credit reports are run by TransUnion, and several answers hand the reader off to them for disputes and identity checks; and rent payments have been moving from KeyCheck and Stripe to Baselane, so anything about paying or collecting rent should be checked against the live help centre before it is relied on."),
        ("Poe", "PoeHelp", readPoe, "Poe.md", "Poe help",
         "Poe publishes its help as five long frequently-asked-questions pages rather than as separate articles. This guide takes each of those pages apart at its own questions, so that every question is a heading a reader can jump to, and each page's title becomes the category. Gathered on 18 August 2026 from the publisher's own listing."),
        ("Substack", "SubstackHelp", readZendesk, "Substack.md", "Substack help",
         "This guide holds Substack's own help for readers and for writers, gathered on 18 August 2026 from the publisher's own listing, so every article arrived with its title, its section and its body. A reader looking only for how to manage subscriptions can skip the sections written for publishers, which are named as such."),
        ("mpv", "MpvHelp", readMpv, "Mpv.md", "mpv help",
         "mpv publishes its whole documentation as a single reference manual, and this guide takes that manual apart so it can be read a section at a time: the manual's own parts are the categories and its sections are the articles. Gathered on 20 August 2026 from the stable manual, together with the installation page.\r\n\r\nmpv is driven from the command line and a configuration file, so this guide is technical in places: it describes the options you can pass it, the keys it responds to, and how to write those choices into a configuration file. No programming is assumed anywhere in it.\r\n\r\nThe parts of the manual that do assume programming are deliberately left out — the Lua and JavaScript scripting interfaces, the C plugin headers, the JSON protocol for driving mpv from another program, and the library for embedding it. Those are written for people building software with mpv rather than for people using it. The unreleased master manual is not here either."),
        ("Gmail", "GmailHelp", readGoogleMeet, "Gmail.md", "Gmail help",
         "This guide holds Google's own help for Gmail, gathered on 9 September 2026. The categories are Google's own topics, taken from the trail above each article.\r\n\r\nGoogle writes the same article once for each device it runs on, so where an article differs by platform the heading says which one it is for: Computer, or iPhone and iPad. Google's Android editions are left out, as this collection covers Windows, the web, iPhone and iPad, and Alexa. A reader on a phone can go straight to the version that matches."),
        ("Google Meet", "GoogleMeetHelp", readGoogleMeet, "GoogleMeet.md", "Google Meet help",
         "This guide holds Google's own help for Meet, gathered on 20 August 2026. The categories are Google's own topics, taken from the trail above each article.\r\n\r\nGoogle writes the same article once for each device it runs on, so where an article differs by platform the heading says which one it is for: Computer, or iPhone and iPad. Google's Android editions are left out, as this collection covers Windows, the web, iPhone and iPad, and Alexa. A reader on a phone can go straight to the version that matches."),
        ("Zapier", "ZapierHelp", readZendesk, "Zapier.md", "Zapier help",
         "This guide holds Zapier's own help, gathered on 20 August 2026 from the publisher's own listing, so every article arrived with its title, its section and its body.\r\n\r\nMuch of it is about the services Zapier connects rather than about Zapier itself, and those articles are kept under their own headings rather than left out: a reader wanting to connect one particular application will find it named. The rest covers building and fixing Zaps, tables, interfaces, agents, accounts and billing."),
        ("Stack Overflow", "StackHelp", readStack, "StackOverflow.md", "Stack Overflow help",
         "This guide holds Stack Overflow's own help centre, gathered on 24 August 2026: asking and answering, reputation and privileges, editing and reviewing, moderation, accounts, and the rules of the site.\r\n\r\nEvery site in the Stack Exchange network — Super User, Ask Ubuntu and the rest — serves this same help centre with its own name substituted in, so this one guide covers them all. Its badge pages are not here: there are 445 of them, each a single sentence saying what earns that badge, and they are a list rather than help."),
        ("Org mode", "OrgModeHelp", readOrgMode, "OrgMode.md", "Org mode help",
         "This guide holds Org mode's own manual and its compact guide, gathered on 24 August 2026 — outlines and headings, to-do lists, tags and properties, agendas, dates and times, tables, exporting and publishing.\r\n\r\nOrg mode runs inside Emacs, so some of what it describes assumes that editor. The manual itself is written for people organising notes and writing documents rather than for people extending Emacs, which is why it is here."),
        ("TaskRabbit", "TaskRabbitHelp", readZendesk, "TaskRabbit.md", "TaskRabbit help",
         "This guide holds TaskRabbit's own help, gathered on 30 August 2026 from the publisher's own listing, so every article arrived with its title, its section and its body. It covers booking a Tasker, prices and payment, cancellations and the Happiness Pledge, and the Tasker side of the service is kept under its own headings."),
        ("Angi", "AngiHelp", readAngi, "Angi.md", "Angi help",
         "This guide holds the questions Angi answers about its own service, gathered on 30 August 2026 — memberships, pricing and payments, pro badges and reviews, screening and certification, project support, accounts and security.\r\n\r\nAngi was Angie's List until 2021 and has since absorbed HomeAdvisor, so a reader looking for either name will find the answers here. Angi's library of home-improvement articles is not in this guide: it is editorial writing about home projects rather than help with using Angi."),
        ("Craigslist", "CraigslistHelp", readCraigslist, "Craigslist.md", "Craigslist help",
         "This guide holds Craigslist's own help, gathered on 30 August 2026 — posting and renewing, paying for a posting where a fee applies, accounts, searching, flags and community moderation, what may not be posted, and its scams and personal safety pages.\r\n\r\nCraigslist runs hundreds of city sites and each serves this same help under its own name, so this one guide covers them all."),
        ("Bitwarden", "BitwardenHelp", readBitwarden, "Bitwarden.md", "Bitwarden help",
         "This guide holds Bitwarden's own help for people keeping their passwords, gathered on 9 September 2026: the vault and its items, generating passwords, two-step login and passkeys, the browser extension, the mobile and desktop apps, importing and exporting, sharing, and accounts and subscriptions.\r\n\r\nBitwarden documents two different readers in one place — the person keeping passwords and the person running a company's server. The second half is not here: single sign-on connectors, self-hosting, deployment and the command-line tools are for administrators, and this collection is for users."),
        ("ElevenLabs", "ElevenLabsHelp", readZendesk, "ElevenLabs.md", "ElevenLabs help",
         "This guide holds ElevenLabs's own help, gathered on 9 September 2026 from the publisher's own listing, so every article arrived with its title, its section and its body. It covers speech synthesis and voices, pronunciation, the Studio for long-form audio, the mobile apps, subscriptions and billing, and what ElevenLabs says about voice cloning and consent.\r\n\r\nIts developer documentation is not here. That is written for people calling its interface from code; this guide is for people using the product."),
        ("Udio", "UdioHelp", readUdio, "Udio.md", "Udio help",
         "This guide holds Udio's own help, gathered on 9 September 2026 — making and extending songs, accounts and subscriptions, downloads and stems, and what Udio says about ownership and commercial use.\r\n\r\nSuno, the service Udio is most often compared with, has a guide of its own in this collection."),
        ("Envision", "EnvisionHelp", readZendesk, "Envision.md", "Envision help",
         "This guide holds Envision's own help, gathered on 9 September 2026 from the publisher's own listing, so every article arrived with its title, its section and its body.\r\n\r\nIt covers four products in one estate: the Envision App, the Envision Glasses, Envision Ally and the Envision Companion. Each has its own headings, so a reader who has only the app can skip the rest."),
        ("Suno", "SunoHelp", readSuno, "Suno.md", "Suno help",
         "This guide holds Suno's own help, gathered on 9 September 2026: making music, credits and subscriptions, the Studio workstation, publishing and sharing, and what Suno says about ownership and licensing of the songs it makes.\r\n\r\nThose rights questions are unsettled outside this guide, and nothing here is legal advice: it is what the publisher tells its users, gathered on the date above."),
        ("Android accessibility", "LookoutHelp", readAndroidAccessibility, "AndroidAccessibility.md", "Android accessibility help, including Lookout",
         "This guide holds Google's own help for the accessibility features of Android, gathered on 9 September 2026: TalkBack, Lookout, Voice Access, Switch Access and Camera Switches, Sound Notifications, Live Transcribe, braille support, and the display and hearing settings.\r\n\r\nLookout is here rather than in a guide of its own because Google does not give it one: it is documented inside this centre alongside everything else. Its pages are gathered in full and sit under their own headings.\r\n\r\nJAWS, NVDA and Narrator have guides of their own in this collection, so the four screen readers can be read side by side — TalkBack being Android's."),
        ("Plain language", "PlainLanguageHelp", readPlainLanguage, "PlainLanguage.md", "The federal plain language guidelines",
         "This guide holds the United States government's plain-language guidance, gathered on 6 September 2026. The site that used to publish it, plainlanguage.gov, now redirects to digital.gov, and this is that guidance at its new home.\r\n\r\nIt covers the principles — writing for your reader, organising, keeping sentences short and simple, avoiding jargon — then writing style and special cases, then design: headings, lists, links, tables and visuals. It ends with how to test whether writing is actually understood, by usability testing, paraphrase testing and comparative studies.\r\n\r\nThis is the standard behind the Plain Writing Act of 2010, and it is the one volume in this collection about how to write the others."),
        ("Quarto", "QuartoHelp", readQuarto, "Quarto.md", "Quarto help",
         "This guide holds Quarto's own documentation, gathered on 25 September 2026: authoring documents, computations in several languages, the output formats it can produce, websites, books, presentations, dashboards and publishing.\r\n\r\nQuarto is built on Pandoc, so this guide sits beside the Pandoc manual in your own work."),
        ("reveal.js", "RevealHelp", readReveal, "RevealJs.md", "reveal.js help",
         "This guide holds reveal.js's own documentation, gathered on 25 September 2026 — setting up a presentation, what a slide can do, and how to control a presentation while giving it.\r\n\r\nPandoc can write reveal.js slides directly, which is why it is here."),
        ("MediaWiki", "MediaWikiHelp", readMediaWiki, "MediaWiki.md", "MediaWiki help",
         "This guide holds MediaWiki's own help pages, gathered on 25 September 2026 — writing and editing pages, talking to other people, finding your way around a wiki, and the settings a reader can change.\r\n\r\nThe developer manual is not here: it documents running and extending a wiki rather than using one. Wikipedia, which runs on MediaWiki, has a guide of its own in this collection."),
        ("Muse", "MuseHelp", readMuse, "Muse.md", "Muse help",
         "This guide holds Meta's own help for Muse, its personal AI agent, gathered on 17 September 2026 — nine days after Muse was released, so expect it to age quickly.\r\n\r\nIt covers what Muse does with your guidance and approval, how connectors work, how it handles privacy, safety and security, and how to manage the data it keeps. Muse can send mail and make purchases on your behalf, so read the approval and connector pages before you connect anything; nothing here is advice, and anything about money should be checked against Meta's own pages on the day.\r\n\r\nMeta refuses ordinary requests for these pages, so they were gathered with a web browser instead. That is why this guide is short: only the pages a browser could reach by following links are here."),
        ("HumanWare", "HumanWareHelp", readHumanWare, "HumanWare.md", "HumanWare help",
         "This guide holds HumanWare's own documentation for the Victor Reader Stream, gathered on 17 September 2026, together with its product support pages.\r\n\r\nHumanWare publishes the same user guide in eight languages as eight separate files. Only the English edition is here; the others are the same book in Arabic, Danish, Dutch, French, German and Swedish."),
        ("Remote Incident Manager", "RimHelp", readRim, "RemoteIncidentManager.md", "Remote Incident Manager help",
         "This guide holds the manual for Remote Incident Manager, the accessible remote desktop tool from Pneuma Solutions, gathered on 17 September 2026. It covers both the Windows and the macOS editions: installing, getting connected as a controller or a target, working with sessions, the dashboard, key commands, plans and troubleshooting.\r\n\r\nRIM's mobile edition, which lets a phone control a computer, is announced but is not yet in the manual. When Pneuma Solutions publishes those pages this guide can be gathered again."),
        ("Google Forms", "GoogleFormsHelp", readGoogleForms, "GoogleForms.md", "Google Forms help",
         "This guide holds Google's own help for Forms, gathered on 17 September 2026. Google documents Forms inside its editors help centre, beside Docs, Sheets and Slides, so only the articles about forms, quizzes, surveys and responses are here."),
        ("Microsoft Forms", "MicrosoftFormsHelp", readMicrosoftForms, "MicrosoftForms.md", "Microsoft Forms help",
         "This guide holds Microsoft's own help for Forms, gathered on 17 September 2026. Microsoft documents Forms inside its Office support pages, so only the articles about forms, quizzes, surveys and responses are here."),
        ("Narrator", "NarratorHelp", readNarrator, "Narrator.md", "The complete guide to Narrator",
         "This guide holds Microsoft's complete guide to Narrator, the screen reader built into Windows, gathered on 31 August 2026 from addresses that carry no version number and are revised in place, so this is the guide as it stood on that date.\r\n\r\nIts chapters run from introducing Narrator through scan mode, reading and navigating, braille, natural voices and customising, and its appendices hold every keyboard command and touch gesture, the supported languages and voices, the supported braille displays, Narrator's sounds, and its update history.\r\n\r\nJAWS, NVDA and their scripting references are in this collection too, so the three Windows screen readers can be read side by side."),
        ("NVDA scripting", "NvdaDevHelp", readNvdaScripting, "NVDAScripting.md", "Writing add-ons and plugins for NVDA",
         "This guide holds two documents from two publishers, gathered on 31 August 2026: NV Access's own NVDA Developer Guide, and the NVDA Add-on Development Guide written by the community add-on team.\r\n\r\nThe developer guide covers app modules, global plugins, the add-on API and its policy, translation, and the internals a plugin may use. The add-on team's guide covers what it takes to build, package and publish an add-on, and is the longer of the two. Read together they answer both halves of the question: what NVDA lets a plugin do, and how to ship one.\r\n\r\nThis guide is an exception to the rule this collection otherwise keeps, and the same exception as JAWSScripting: everything else here is written for someone using a program, and this is written for someone extending one. It is included because scripting a screen reader is how a blind user makes an inaccessible program usable, which is closer to self-defence than to software engineering."),
        ("NVDA", "NvdaHelp", readNvdaGuide, "NVDA.md", "NVDA user guide",
         "This guide holds NV Access's own user guide for NVDA, together with its quick reference of every key command, gathered on 31 August 2026 from the addresses that always point at the current release — version 2026.1.1 at the time of gathering.\r\n\r\nNVDA's changes file was gathered too and is deliberately not here: it is 89,433 words of release notes, more than the user guide itself, and a reader looking for how to use NVDA should not have to walk past every fix since 2006 to reach it. Say the word and it becomes a volume of its own.\r\n\r\nThe JAWS courses and the JAWS scripting reference are in this collection too, so the two screen readers can be read side by side."),
        ("Mermaid", "MermaidHelp", readMermaid, "Mermaid.md", "Mermaid help",
         "This guide holds Mermaid's own documentation, gathered on 30 August 2026. Mermaid turns text into diagrams — flowcharts, sequence diagrams, Gantt charts, mind maps and more — so the diagram's source stays readable, which is why it is worth having.\r\n\r\nThe syntax pages are the bulk of it and the reason to read it: one page for each kind of diagram, describing the words that make it. Mermaid's configuration reference is not here, because it is generated from the source code and written for people extending Mermaid rather than using it."),
        ("Typora", "TyporaHelp", readTypora, "Typora.md", "Typora help",
         "This guide holds Typora's own support pages, gathered on 24 August 2026: writing and formatting in Markdown, exporting to other formats, themes, images, and the diagram and mathematics extensions Typora supports."),
        ("Zettlr", "ZettlrHelp", readZettlr, "Zettlr.md", "Zettlr help",
         "This guide holds Zettlr's own documentation, gathered on 24 August 2026: writing in Markdown, projects and files, citations, exporting through Pandoc, and the editor's own settings."),
        ("TeX Live", "TexLiveHelp2", readTexLive, "TexLive.md", "TeX Live help",
         "This guide holds the TeX Live project's own pages, gathered on 24 August 2026: what TeX Live is, how to install it on Windows and elsewhere, how to keep it up to date, and what its licences and mirrors are.\r\n\r\nA first attempt gathered ten times as much and none of it useful, because the project's site links straight into a mirror of the whole TeX archive. This guide is the documentation itself and nothing below it."),
        ("Org mode", "OrgModeHelp", readOrgMode, "OrgMode.md", "Org mode help",
         "This guide holds Org mode's own manual and its compact guide, gathered on 24 August 2026 — outlines and headings, to-do lists, tags and properties, agendas, dates and times, tables, exporting and publishing.\r\n\r\nOrg mode runs inside Emacs, so some of what it describes assumes that editor. The manual itself is written for people organising notes and writing documents rather than for people extending Emacs, which is why it is here."),
        ("TaskRabbit", "TaskRabbitHelp", readZendesk, "TaskRabbit.md", "TaskRabbit help",
         "This guide holds TaskRabbit's own help, gathered on 30 August 2026 from the publisher's own listing, so every article arrived with its title, its section and its body. It covers booking a Tasker, prices and payment, cancellations and the Happiness Pledge, and the Tasker side of the service is kept under its own headings."),
        ("Angi", "AngiHelp", readAngi, "Angi.md", "Angi help",
         "This guide holds the questions Angi answers about its own service, gathered on 30 August 2026 — memberships, pricing and payments, pro badges and reviews, screening and certification, project support, accounts and security.\r\n\r\nAngi was Angie's List until 2021 and has since absorbed HomeAdvisor, so a reader looking for either name will find the answers here. Angi's library of home-improvement articles is not in this guide: it is editorial writing about home projects rather than help with using Angi."),
        ("Craigslist", "CraigslistHelp", readCraigslist, "Craigslist.md", "Craigslist help",
         "This guide holds Craigslist's own help, gathered on 30 August 2026 — posting and renewing, paying for a posting where a fee applies, accounts, searching, flags and community moderation, what may not be posted, and its scams and personal safety pages.\r\n\r\nCraigslist runs hundreds of city sites and each serves this same help under its own name, so this one guide covers them all."),
        ("Bitwarden", "BitwardenHelp", readBitwarden, "Bitwarden.md", "Bitwarden help",
         "This guide holds Bitwarden's own help for people keeping their passwords, gathered on 9 September 2026: the vault and its items, generating passwords, two-step login and passkeys, the browser extension, the mobile and desktop apps, importing and exporting, sharing, and accounts and subscriptions.\r\n\r\nBitwarden documents two different readers in one place — the person keeping passwords and the person running a company's server. The second half is not here: single sign-on connectors, self-hosting, deployment and the command-line tools are for administrators, and this collection is for users."),
        ("ElevenLabs", "ElevenLabsHelp", readZendesk, "ElevenLabs.md", "ElevenLabs help",
         "This guide holds ElevenLabs's own help, gathered on 9 September 2026 from the publisher's own listing, so every article arrived with its title, its section and its body. It covers speech synthesis and voices, pronunciation, the Studio for long-form audio, the mobile apps, subscriptions and billing, and what ElevenLabs says about voice cloning and consent.\r\n\r\nIts developer documentation is not here. That is written for people calling its interface from code; this guide is for people using the product."),
        ("Udio", "UdioHelp", readUdio, "Udio.md", "Udio help",
         "This guide holds Udio's own help, gathered on 9 September 2026 — making and extending songs, accounts and subscriptions, downloads and stems, and what Udio says about ownership and commercial use.\r\n\r\nSuno, the service Udio is most often compared with, has a guide of its own in this collection."),
        ("Envision", "EnvisionHelp", readZendesk, "Envision.md", "Envision help",
         "This guide holds Envision's own help, gathered on 9 September 2026 from the publisher's own listing, so every article arrived with its title, its section and its body.\r\n\r\nIt covers four products in one estate: the Envision App, the Envision Glasses, Envision Ally and the Envision Companion. Each has its own headings, so a reader who has only the app can skip the rest."),
        ("Suno", "SunoHelp", readSuno, "Suno.md", "Suno help",
         "This guide holds Suno's own help, gathered on 9 September 2026: making music, credits and subscriptions, the Studio workstation, publishing and sharing, and what Suno says about ownership and licensing of the songs it makes.\r\n\r\nThose rights questions are unsettled outside this guide, and nothing here is legal advice: it is what the publisher tells its users, gathered on the date above."),
        ("Android accessibility", "LookoutHelp", readAndroidAccessibility, "AndroidAccessibility.md", "Android accessibility help, including Lookout",
         "This guide holds Google's own help for the accessibility features of Android, gathered on 9 September 2026: TalkBack, Lookout, Voice Access, Switch Access and Camera Switches, Sound Notifications, Live Transcribe, braille support, and the display and hearing settings.\r\n\r\nLookout is here rather than in a guide of its own because Google does not give it one: it is documented inside this centre alongside everything else. Its pages are gathered in full and sit under their own headings.\r\n\r\nJAWS, NVDA and Narrator have guides of their own in this collection, so the four screen readers can be read side by side — TalkBack being Android's."),
        ("Plain language", "PlainLanguageHelp", readPlainLanguage, "PlainLanguage.md", "The federal plain language guidelines",
         "This guide holds the United States government's plain-language guidance, gathered on 6 September 2026. The site that used to publish it, plainlanguage.gov, now redirects to digital.gov, and this is that guidance at its new home.\r\n\r\nIt covers the principles — writing for your reader, organising, keeping sentences short and simple, avoiding jargon — then writing style and special cases, then design: headings, lists, links, tables and visuals. It ends with how to test whether writing is actually understood, by usability testing, paraphrase testing and comparative studies.\r\n\r\nThis is the standard behind the Plain Writing Act of 2010, and it is the one volume in this collection about how to write the others."),
        ("Quarto", "QuartoHelp", readQuarto, "Quarto.md", "Quarto help",
         "This guide holds Quarto's own documentation, gathered on 25 September 2026: authoring documents, computations in several languages, the output formats it can produce, websites, books, presentations, dashboards and publishing.\r\n\r\nQuarto is built on Pandoc, so this guide sits beside the Pandoc manual in your own work."),
        ("reveal.js", "RevealHelp", readReveal, "RevealJs.md", "reveal.js help",
         "This guide holds reveal.js's own documentation, gathered on 25 September 2026 — setting up a presentation, what a slide can do, and how to control a presentation while giving it.\r\n\r\nPandoc can write reveal.js slides directly, which is why it is here."),
        ("MediaWiki", "MediaWikiHelp", readMediaWiki, "MediaWiki.md", "MediaWiki help",
         "This guide holds MediaWiki's own help pages, gathered on 25 September 2026 — writing and editing pages, talking to other people, finding your way around a wiki, and the settings a reader can change.\r\n\r\nThe developer manual is not here: it documents running and extending a wiki rather than using one. Wikipedia, which runs on MediaWiki, has a guide of its own in this collection."),
        ("Muse", "MuseHelp", readMuse, "Muse.md", "Muse help",
         "This guide holds Meta's own help for Muse, its personal AI agent, gathered on 17 September 2026 — nine days after Muse was released, so expect it to age quickly.\r\n\r\nIt covers what Muse does with your guidance and approval, how connectors work, how it handles privacy, safety and security, and how to manage the data it keeps. Muse can send mail and make purchases on your behalf, so read the approval and connector pages before you connect anything; nothing here is advice, and anything about money should be checked against Meta's own pages on the day.\r\n\r\nMeta refuses ordinary requests for these pages, so they were gathered with a web browser instead. That is why this guide is short: only the pages a browser could reach by following links are here."),
        ("HumanWare", "HumanWareHelp", readHumanWare, "HumanWare.md", "HumanWare help",
         "This guide holds HumanWare's own documentation for the Victor Reader Stream, gathered on 17 September 2026, together with its product support pages.\r\n\r\nHumanWare publishes the same user guide in eight languages as eight separate files. Only the English edition is here; the others are the same book in Arabic, Danish, Dutch, French, German and Swedish."),
        ("Remote Incident Manager", "RimHelp", readRim, "RemoteIncidentManager.md", "Remote Incident Manager help",
         "This guide holds the manual for Remote Incident Manager, the accessible remote desktop tool from Pneuma Solutions, gathered on 17 September 2026. It covers both the Windows and the macOS editions: installing, getting connected as a controller or a target, working with sessions, the dashboard, key commands, plans and troubleshooting.\r\n\r\nRIM's mobile edition, which lets a phone control a computer, is announced but is not yet in the manual. When Pneuma Solutions publishes those pages this guide can be gathered again."),
        ("Google Forms", "GoogleFormsHelp", readGoogleForms, "GoogleForms.md", "Google Forms help",
         "This guide holds Google's own help for Forms, gathered on 17 September 2026. Google documents Forms inside its editors help centre, beside Docs, Sheets and Slides, so only the articles about forms, quizzes, surveys and responses are here."),
        ("Microsoft Forms", "MicrosoftFormsHelp", readMicrosoftForms, "MicrosoftForms.md", "Microsoft Forms help",
         "This guide holds Microsoft's own help for Forms, gathered on 17 September 2026. Microsoft documents Forms inside its Office support pages, so only the articles about forms, quizzes, surveys and responses are here."),
        ("Narrator", "NarratorHelp", readNarrator, "Narrator.md", "The complete guide to Narrator",
         "This guide holds Microsoft's complete guide to Narrator, the screen reader built into Windows, gathered on 31 August 2026 from addresses that carry no version number and are revised in place, so this is the guide as it stood on that date.\r\n\r\nIts chapters run from introducing Narrator through scan mode, reading and navigating, braille, natural voices and customising, and its appendices hold every keyboard command and touch gesture, the supported languages and voices, the supported braille displays, Narrator's sounds, and its update history.\r\n\r\nJAWS, NVDA and their scripting references are in this collection too, so the three Windows screen readers can be read side by side."),
        ("NVDA scripting", "NvdaDevHelp", readNvdaScripting, "NVDAScripting.md", "Writing add-ons and plugins for NVDA",
         "This guide holds two documents from two publishers, gathered on 31 August 2026: NV Access's own NVDA Developer Guide, and the NVDA Add-on Development Guide written by the community add-on team.\r\n\r\nThe developer guide covers app modules, global plugins, the add-on API and its policy, translation, and the internals a plugin may use. The add-on team's guide covers what it takes to build, package and publish an add-on, and is the longer of the two. Read together they answer both halves of the question: what NVDA lets a plugin do, and how to ship one.\r\n\r\nThis guide is an exception to the rule this collection otherwise keeps, and the same exception as JAWSScripting: everything else here is written for someone using a program, and this is written for someone extending one. It is included because scripting a screen reader is how a blind user makes an inaccessible program usable, which is closer to self-defence than to software engineering."),
        ("NVDA", "NvdaHelp", readNvdaGuide, "NVDA.md", "NVDA user guide",
         "This guide holds NV Access's own user guide for NVDA, together with its quick reference of every key command, gathered on 31 August 2026 from the addresses that always point at the current release — version 2026.1.1 at the time of gathering.\r\n\r\nNVDA's changes file was gathered too and is deliberately not here: it is 89,433 words of release notes, more than the user guide itself, and a reader looking for how to use NVDA should not have to walk past every fix since 2006 to reach it. Say the word and it becomes a volume of its own.\r\n\r\nThe JAWS courses and the JAWS scripting reference are in this collection too, so the two screen readers can be read side by side."),
        ("Mermaid", "MermaidHelp", readMermaid, "Mermaid.md", "Mermaid help",
         "This guide holds Mermaid's own documentation, gathered on 30 August 2026. Mermaid turns text into diagrams — flowcharts, sequence diagrams, Gantt charts, mind maps and more — so the diagram's source stays readable, which is why it is worth having.\r\n\r\nThe syntax pages are the bulk of it and the reason to read it: one page for each kind of diagram, describing the words that make it. Mermaid's configuration reference is not here, because it is generated from the source code and written for people extending Mermaid rather than using it."),
        ("Typora", "TyporaHelp", readTypora, "Typora.md", "Typora help",
         "This guide holds Typora's own support pages, gathered on 24 August 2026 — writing and editing in Markdown, images and diagrams, themes, exporting, and the licence."),
        ("Zettlr", "ZettlrHelp", readZettlr, "Zettlr.md", "Zettlr help",
         "This guide holds Zettlr's own documentation, gathered on 24 August 2026 — its editor, its sidebar and file management, citations, exporting through Pandoc, and its settings."),
        ("TeX Live", "TexLiveHelp2", readTexLive, "TexLive.md", "TeX Live help",
         "This guide holds TeX Live's own documentation pages, gathered on 24 August 2026: what it is, how to install it on Windows and elsewhere, how to keep it up to date, and how it is built.\r\n\r\nMiKTeX, the other LaTeX distribution most Windows users meet, has a guide of its own in this collection."),
        ("Jupyter", "JupyterHelp", readJupyter, "Jupyter.md", "Jupyter help",
         "This guide holds the part of Jupyter's documentation written for people using it, gathered on 23 August 2026: installing it, starting it, running a notebook server, and working with notebooks.\r\n\r\nMost of what the Jupyter project publishes is about the project itself — its governance, its meetings, how to contribute code — and none of that is here, because this collection is for people using software rather than building it. Pandoc reads and writes Jupyter notebooks, which is why the volume exists at all."),
        ("MiKTeX", "MiktexHelp", readMiktex, "Miktex.md", "MiKTeX help",
         "This guide holds MiKTeX's own help, gathered on 23 August 2026: its frequently asked questions, its how-to pages and its manual. MiKTeX is the LaTeX distribution most Windows users install, and it is what Pandoc calls on to make a PDF unless another engine is chosen."),
        ("Calibre", "CalibreHelp", readCalibre, "Calibre.md", "The calibre manual",
         "This guide holds calibre's own manual, gathered on 23 August 2026 — managing an ebook library, converting between formats, the ebook viewer and editor, the content server, and fetching news.\r\n\r\nTwo parts of the manual are deliberately not here: its translated editions, which repeat the English in other languages, and its source-code listings, which document calibre's internals for people writing code rather than reading books."),
        ("EndNote", "EndNoteHelp", readEndNote, "EndNote.md", "EndNote online help",
         "This guide holds EndNote's own online help, gathered on 23 August 2026. It documents EndNote online — collecting references, organising a library, citing them in a document, and the fields of every reference type EndNote knows.\r\n\r\nClarivate's separate knowledge base is not here and could not be: every page of it is drawn in the browser after loading, so a plain request sees nothing. This older help system is the part that answers. Zotero and Mendeley, the two products people most often compare EndNote with, have guides of their own in this collection."),
        ("Mendeley", "MendeleyHelp", readMendeley, "Mendeley.md", "Mendeley help",
         "This guide holds the help Elsevier publishes for Mendeley, gathered on 23 August 2026 — the reference manager, the web library, the Word plugin and the browser importer.\r\n\r\nEndNote and Zotero, the two products people most often compare Mendeley with, have guides of their own in this collection."),
        ("IFTTT", "IftttHelp", readZendesk, "Ifttt.md", "IFTTT help",
         "This guide holds IFTTT's own help, gathered on 20 August 2026 from the publisher's own listing, so every article arrived with its title, its section and its body. It covers making and troubleshooting applets, connecting services, the paid plans and the developer platform."),
        ("Todoist", "TodoistHelp", readTodoist, "Todoist.md", "Todoist help",
         "This guide holds Todoist's own help articles, gathered on 20 August 2026. The categories are Todoist's own, taken from the trail above each article."),
        ("Microsoft To Do", "MicrosoftToDoHelp", readMicrosoftToDo, "MicrosoftToDo.md", "Microsoft To Do help",
         "This guide holds Microsoft's own help for To Do, gathered on 20 August 2026. Microsoft publishes everything it sells in one support tree, so the gathering was held to To Do by reading each page's own heading before following its links.\r\n\r\nIt is a small volume, and that is the product rather than the gathering: Microsoft documents To Do briefly."),
        ("Handshake", "HandshakeHelp", readZendesk, "Handshake.md", "Handshake help",
         "This guide holds Handshake's own help, gathered on 19 August 2026 from the publisher's own listing, so every article arrived with its title, its section and its body.\r\n\r\nHandshake writes for three audiences in one estate: students and graduates looking for work, employers recruiting them, and the university careers staff who run it. All three are here under their own headings, so a student can skip the recruiter material without it being lost. The community forum is not here, since those posts are other users answering each other rather than the publisher's own words."),
        ("CNBC", "CnbcHelp", readZendesk, "Cnbc.md", "CNBC help",
         "This guide holds CNBC's own help for its readers and subscribers, gathered on 19 August 2026 from the publisher's own listing, so every article arrived with its title, its section and its body. It covers accounts and subscriptions, the apps, live television and streaming, newsletters, and CNBC Pro."),
        ("CQ Roll Call", "CqRollCallHelp", readZendesk, "CqRollCall.md", "CQ Roll Call help",
         "This guide holds the help CQ Roll Call publishes for people using its legislative tracking and news services, gathered on 19 August 2026 from the publisher's own listing. CQ Federal is the largest part of it."),
        ("Khan Academy", "KhanAcademyHelp", readZendesk, "KhanAcademy.md", "Khan Academy help",
         "This guide holds Khan Academy's own help, gathered on 18 August 2026 from the publisher's own listing, so every article arrived with its title, its section and its body. It is written for learners, teachers, parents and school administrators in one estate, and all of it is kept under its own headings — the teacher and parent material is likely to be the most useful part to anyone helping a student.\r\n\r\nThe community forum is not here. Those posts are other users answering each other rather than the publisher's own words, and this collection has held that line throughout."),
        ("Udemy", "UdemyHelp", readZendesk, "Udemy.md", "Udemy help",
         "This guide holds Udemy's own help, gathered on 18 August 2026 from the publisher's own listing, so every article arrived with its title, its section and its body. It is written for learners and for instructors in one estate: the instructor material is kept under its own headings, so a reader who only takes courses can skip it.\r\n\r\nOne thing worth knowing: as of May 2026 Udemy and Coursera are the same company, though they remain separate platforms with separate help. Udemy's own help says so, and this guide covers Udemy alone."),
        ("iHeartRadio", "IHeartHelp", readZendesk, "IHeartRadio.md", "iHeartRadio help",
         "This guide holds iHeartRadio's own help for listeners, gathered on 18 August 2026 from the publisher's own listing, so every article arrived with its title, its section and its body. It covers accounts and subscriptions, live radio and podcasts, playlists, the apps, cars and smart speakers, and what to do when something will not play."),
        ("Medium", "MediumHelp", readZendesk, "Medium.md", "Medium help",
         "This guide holds Medium's own help for readers and writers, gathered on 18 August 2026 from the publisher's own listing, so every article arrived with its title, its section and its body. It covers accounts and membership, reading and following, writing and publishing, publications, partner earnings and the apps."),
        ("Reddit", "RedditHelp", readZendesk, "Reddit.md", "Reddit help",
         "This guide holds Reddit's own help for the people who use it, gathered on 18 August 2026 from the publisher's own listing, so every article arrived with its title, its section and its body. Reddit refuses an ordinary request for its help pages; the listing answered."),
        ("Good Housekeeping", "GoodHousekeepingHelp", readGoodHousekeeping, "GoodHousekeeping.md", "Good Housekeeping subscriber help",
         "Good Housekeeping does not publish reader help on goodhousekeeping.com; its answers are published by the company that runs its subscription service, and this guide holds them, gathered on 18 August 2026. Anything behind a sign-in could not be gathered and is not here."),
        ("Halo", "HaloHelp", readZendesk, "Halo.md", "Halo help",
         "This guide holds the help that 343 Industries and Halo Studios publish for players of the Halo games, gathered on 18 August 2026 from the publisher's own listing, so every article arrived with its title, its section and its body. It covers accounts, installation, multiplayer, purchases and troubleshooting across the games rather than how to play them."),
        ("CrimeCon", "CrimeConHelp", readCrimeCon, "CrimeCon.md", "CrimeCon help",
         "CrimeCon publishes its answers for attendees on one page, and this guide holds them, gathered on 18 August 2026. The categories are CrimeCon's own four headings. It covers badges, the programme, the venue and taking part, including its accessibility arrangements."),
        ("Men's Health", "MensHealthHelp", readMensHealth, "MensHealth.md", "Men's Health subscriber help",
         "Men's Health does not publish reader help on menshealth.com; its answers are published by the company that runs its subscription service, and this guide holds them, gathered on 18 August 2026. Anything behind a sign-in could not be gathered and is not here."),
        ("Publication FAQs", "PublicationFaqs", readPublicationFaqs, "PublicationFaqs.md", "Subscriber questions for six publications",
         "Six publications answer their readers on a single page each rather than in a help centre, and this guide gathers all six, on 19 August 2026: The New Yorker, WIRED, Esquire, USA Today, Macworld and PC World. Each has its own heading, so a reader interested in one can ignore the others.\r\n\r\nThree of them are answered by the company that runs their subscriptions rather than by the magazine itself, which is why some answers speak of the publisher in the third person."),
        ("Cosmopolitan", "MagazineServiceHelp", readCosmopolitan, "Cosmopolitan.md", "Cosmopolitan subscriber help",
         "Cosmopolitan does not publish reader help on cosmopolitan.com; its answers are published by the company that runs its subscription service, and this guide holds them, gathered on 18 August 2026. Anything behind a sign-in could not be gathered and is not here."),
        ("Vogue", "MagazineServiceHelp", readVogueService, "Vogue.md", "Vogue subscriber help",
         "Vogue does not publish reader help on vogue.com; its answers are published by the company that runs its subscription service, and this guide holds them, gathered on 18 August 2026. It covers the print magazine and Vogue Digital separately, because the two are sold and served separately. Anything behind a sign-in could not be gathered and is not here."),
        ("Smithsonian", "SmithsonianHelp", readSmithsonian, "Smithsonian.md", "Smithsonian magazine subscriber service",
         "Smithsonian's subscriber service is run for the magazine by an outside company, and its help pages live on that company's site. This guide holds them, gathered on 18 August 2026. Anything that needed a sign-in could not be gathered and is not here."),
        # DOUG LEE'S SCRIPTED APPS (2 November 2026)
        ("Discord", "DiscordHelp", readZendesk, "Discord.md", "Discord help",
         "This guide holds Discord's own help centre, gathered on 2 November 2026 from the publisher's own listing, so every article arrived with its title, its section and its body. The categories are Discord's own sections. The developer help centre is a separate site and is not here. Doug Lee publishes JAWS scripts for the Discord desktop app; his documentation is in Ttcom.htm."),
        ("TeamSpeak", "TeamSpeakHelp", readZendesk, "TeamSpeak.md", "TeamSpeak help",
         "This guide holds TeamSpeak's own help centre, gathered on 2 November 2026 from the publisher's own listing. The categories are TeamSpeak's own sections, covering TeamSpeak 6 and the older TeamSpeak 3, whose articles TeamSpeak keeps for people still using it. Doug Lee publishes JAWS scripts and an NVDA add-on for TeamSpeak; his documentation is in Ttcom.htm."),
        ("Wireshark", "WiresharkHelp", readWireshark, "Wireshark.md", "Wireshark user's guide",
         "This guide holds the Wireshark User's Guide, the Wireshark project's own manual, gathered on 2 November 2026 from its edition published one section per page. The categories are the guide's own chapters and appendices, and each article keeps its section number, so the order of the original can be followed. Doug Lee publishes JAWS scripts for Wireshark; his documentation is in Ttcom.htm."),
        ("Virtual Audio Cable", "VirtualAudioCableHelp", readVirtualAudioCable, "VirtualAudioCable.md", "Virtual Audio Cable user manual",
         "This guide holds the Virtual Audio Cable user manual, published by its author, Eugene Muzychenko, gathered on 2 November 2026. The manual lists its pages in one flat run with no groups, so they are grouped here by subject: getting started, using cables, problems and answers, and about the product. The page describing the driver's programming interface is left out, as written for programmers. Doug Lee publishes JAWS scripts and an NVDA add-on for Virtual Audio Cable's applications; his documentation is in Ttcom.htm."),
        ("3CX", "ThreeCxHelp", readThreeCx, "ThreeCx.md", "3CX user manual",
         "This guide holds the 3CX user manual, the publisher's own pages for the people who make and take calls with 3CX, gathered on 2 November 2026: the web client, the Windows, Android and iOS apps, desk phones, voicemail and video meetings. 3CX gives its user pages no groups, so they are grouped here by subject. The administrator's manual is a separate set and is not here. Doug Lee publishes JAWS scripts for the 3CX apps; his documentation is in Ttcom.htm."),
        ("MicroSIP", "MicroSIPHelp", readMicroSip, "MicroSIP.md", "MicroSIP documentation",
         "This guide holds MicroSIP's own documentation and its questions page, gathered on 2 November 2026. The documentation is one long page, so each of its sections is an article here, under the page's own section names. Doug Lee publishes JAWS scripts for MicroSIP; his documentation is in Ttcom.htm."),
        ("MuseScore", "MuseScoreHelp", readMuseScore, "MuseScore.md", "MuseScore Studio 4 handbook",
         "This guide holds the MuseScore Studio 4 handbook, written by the MuseScore community on musescore.org, gathered on 2 November 2026. The categories are the handbook's own chapters, taken from the trail above each page. Most of the handbook's addresses now lead to MuseScore's new handbook, so most pages here come from it, with the chapters it prints above each page. It holds the pages the gathering reached, not the whole handbook. The handbook's own Accessibility page is among them. Doug Lee worked on the MuseScore 3 JAWS scripts, now distributed by MuseScore."),
        ("TeamTalk", "TeamTalkHelp", readTeamTalk, "TeamTalk.md", "TeamTalk 5 client manual",
         "This guide holds the TeamTalk 5 client manual published by BearWare.dk, gathered on 2 November 2026: the user interface, preferences, the server, .tt files, how-to answers and advanced settings. The developer kit's documentation is a separate set and is not here. Doug Lee publishes JAWS scripts for the TeamTalk Qt client and his own text client, TTCom; his documentation for both is in Ttcom.htm."),
        ("TeamViewer", "TeamViewerHelp", readTeamViewer, "TeamViewer.md", "TeamViewer knowledge base",
         "This guide holds TeamViewer's own knowledge base for TeamViewer Remote and TeamViewer Classic, gathered on 2 November 2026. The categories are TeamViewer's own, named by product and by the topic in each article's address. The enterprise products, Tensor and Frontline, are not here. Doug Lee publishes JAWS scripts for TeamViewer; his documentation is in Ttcom.htm."),
        ("Winlink Express", "WinlinkExpressHelp", readWinlink, "WinlinkExpress.md", "Winlink Express and Winlink help",
         "This guide holds the help pages on winlink.org for Winlink Express and the Winlink system it connects to, gathered on 2 November 2026. The site files its pages by date rather than by topic, so they are grouped here by subject. The site also carries news, history, stories from the field and two Spanish-language pages; those are set aside, and the build's log counts them. Doug Lee publishes JAWS scripts for Winlink Express; his documentation is in Ttcom.htm."),
        # INTERNET RADIO (3 November 2026)
        ("Shoutcast", "ShoutcastHelp", readZendesk, "Shoutcast.md", "Shoutcast help",
         "This guide holds Shoutcast's own help centre, gathered from the publisher's own listing: the Shoutcast directory, the Radio Manager where a station is listed and earns, and the Shoutcast server software. The categories are Shoutcast's own sections. RadioTrail, DbDo's radio template, draws its stations from Radio Browser and SomaFM; Shoutcast's directory needs a developer key to read."),
        ("NVDA Coach", "NVDACoachHelp", readNVDACoach, "NVDACoach.md", "NVDA Coach help",
         "This guide holds the whole course of NVDA Coach, Tony Gebhard's free add-on that teaches the NVDA screen reader from inside NVDA, in 45 guided lessons across six chapters, with the add-on's own user guide and resources page. It is read from the add-on itself, so every step, key, hint and message is the author's own wording; the add-on and its lessons are licensed under the GNU General Public License, version 2. Get the add-on from NVDA's Add-on Store, or from the releases of its GitHub repository."),
        # ASSISTIVE APPS FROM NO SIGHT REQUIRED (11 November 2026)
        ("GoodMaps", "GoodMapsHelp", readGoodMaps, "GoodMaps.md", "GoodMaps help",
         "This guide holds the official help for GoodMaps, the free indoor navigation app for iPhone and Android, gathered from the GoodMaps knowledge base on 11 November 2026. The categories are the knowledge base's own sections.\r\n\r\nMost parts of the app have two articles: a short how-to under Getting Started, and a fuller description under Features, often comparing the current app with version 1.0 and ending with a few questions and answers. GoodMaps finds where you are in a building through your phone's camera, so several articles explain how to hold the phone and why the app needs camera access. The help is written for every user, sighted and blind, and in places describes the visual map.\r\n\r\nLeft out on purpose: the pages written for the buildings that host GoodMaps rather than for people using the app. These cover GoodMaps Studio, the tool venues use to manage their maps; the mapping service and the safety of its lidar scanner; a sales page addressed to venues; and a 2023 notice to venue customers about the move to the new app. The screenshots are left out too, because their only descriptions are labels such as \"Check In 1.\" For questions the help does not answer, GoodMaps takes email at support@goodmaps.com."),
        ("AI Content Describer", "AiContentDescriberHelp", readAiContentDescriber, "AiContentDescriber.md", "AI Content Describer help",
         "This guide holds the documentation for AI Content Describer, a free add-on for the NVDA screen reader that asks an AI model to describe whatever is in focus, the navigator object, the whole screen, an image on the clipboard or a picture from your camera, and lets you ask follow-up questions. It was gathered from the add-on's GitHub repository on 11 November 2026.\r\n\r\nThe add-on's whole manual is one long readme, so this guide divides it at the readme's own headings. Setting up a model holds one article for each AI service the add-on supports, from those that need a key you get from the company to models that run on your own computer.\r\n\r\nLeft out on purpose: the parts written for people who change the add-on's code rather than use it -- the readme's sections on building, translating and contributing, and a separate developer document on adding a new AI service. The readme's translations into ten other languages were not gathered."),
        ("Guide", "GuideHelp", readGuide, "Guide.md", "Guide help",
         "This guide holds what the makers of Guide publish about it, gathered from guideinteraction.com on 14 November 2026. Guide is a Windows program for people who are blind or have low vision: you tell it, by voice or keyboard, what you want done on the screen, and it describes what is there and clicks, types or plays for you. It is meant to work beside a screen reader such as JAWS or NVDA, not to replace one. It is a paid subscription with a free trial.\r\n\r\nThe site is small, so this guide is too. The support pages are the help itself: settings, voices, keyboard shortcuts, the two assist modes and what to do when Guide cannot act in a program. The questions on Guide's front page are articles of their own. The release posts are kept in their own category, because they are where Guide says what each version added.\r\n\r\nThis is a different product from the recruiting service also called Guide."),
        ("Learning Ally", "LearningAllyHelp", readLearningAlly, "LearningAlly.md", "Learning Ally help",
         "This guide holds Learning Ally's own help, gathered from its public help pages on 14 November 2026. Learning Ally is a nonprofit library of human-read audiobooks for students with dyslexia, blindness and other reading barriers, used at home and in schools. Each question on its help page is an article here, under Learning Ally's own headings, and the pages for schools that sign in through Clever, ClassLink or Google have a category of their own.\r\n\r\nThe app guides Learning Ally offers as PDF files were not gathered. Bookshare, another accessible library, has its own guide in this collection."),
        ("LibriVox", "LibriVoxHelp", readLibriVox, "LibriVox.md", "LibriVox help",
         "This guide holds LibriVox's own help, gathered from the LibriVox wiki on 14 November 2026. LibriVox is a volunteer project that records books in the public domain and gives the recordings away free. Its help is written for two kinds of people: listeners, who want to find and play the audiobooks, and volunteers, who read, edit, proof-listen and coordinate the recordings. Both are here.\r\n\r\nThe wiki gives its pages no trail, so the categories come from what each page is about. Left out on purpose: the same guides in other languages, yearly lists of staff picks and other reading lists, old announcements, and pages about running the wiki itself. Much of the recording advice is about Audacity, which has its own guide in this collection."),
        ("Google Calendar", "GoogleCalendarHelp", readGoogleTopics, "GoogleCalendar.md", "Google Calendar help",
         "This guide holds Google's own help for Google Calendar, gathered from support.google.com on 14 November 2026. It covers calendars, events, appointment schedules, sharing, settings and Tasks in Calendar, on a computer and on an iPhone or iPad. Using Calendar with a screen reader is under Get started.\r\n\r\nGoogle writes the same article once for each device it runs on, so where an article differs by platform the heading says which one it is for: Computer, or iPhone and iPad. Google's Android editions are left out, as this collection covers Windows, the web, iPhone and iPad, and Alexa. The categories are Google's own topics: Google no longer puts a trail above each article, so each article is filed under the topic its help centre lists it in."),
        ("Google Chat", "GoogleChatHelp", readGoogleTopics, "GoogleChat.md", "Google Chat help",
         "This guide holds Google's own help for Google Chat, gathered from support.google.com on 14 November 2026. It covers messages, spaces, calls, files and notifications in Chat, on its own and inside Gmail.\r\n\r\nGoogle writes the same article once for each device it runs on, so where an article differs by platform the heading says which one it is for: Computer, or iPhone and iPad. Google's Android editions are left out, as this collection covers Windows, the web, iPhone and iPad, and Alexa. The categories are Google's own topics: Google no longer puts a trail above each article, so each article is filed under the topic its help centre lists it in."),
        ("Google Keep", "GoogleKeepHelp", readGoogleTopics, "GoogleKeep.md", "Google Keep help",
         "This guide holds Google's own help for Google Keep, gathered from support.google.com on 14 November 2026. It covers notes, lists, reminders, labels and sharing in Keep.\r\n\r\nGoogle writes the same article once for each device it runs on, so where an article differs by platform the heading says which one it is for: Computer, or iPhone and iPad. Google's Android editions are left out, as this collection covers Windows, the web, iPhone and iPad, and Alexa. The categories are Google's own topics: Google no longer puts a trail above each article, so each article is filed under the topic its help centre lists it in."),
        ("Google Sites", "GoogleSitesHelp", readGoogleTopics, "GoogleSites.md", "Google Sites help",
         "This guide holds Google's own help for Google Sites, gathered from support.google.com on 14 November 2026. It covers making, editing, sharing and publishing a site with Google Sites. Google's help for Sites is short, and so is this guide.\r\n\r\nGoogle writes the same article once for each device it runs on, so where an article differs by platform the heading says which one it is for: Computer, or iPhone and iPad. Google's Android editions are left out, as this collection covers Windows, the web, iPhone and iPad, and Alexa. The categories are Google's own topics: Google no longer puts a trail above each article, so each article is filed under the topic its help centre lists it in."),
        ("Google Tasks", "GoogleTasksHelp", readGoogleTopics, "GoogleTasks.md", "Google Tasks help",
         "This guide holds Google's own help for Google Tasks, gathered from support.google.com on 14 November 2026. It covers tasks and lists in the Tasks app and beside Gmail, Calendar, Chat and the Docs editors. Some of it repeats what the Google Calendar guide says about tasks there.\r\n\r\nGoogle writes the same article once for each device it runs on, so where an article differs by platform the heading says which one it is for: Computer, or iPhone and iPad. Google's Android editions are left out, as this collection covers Windows, the web, iPhone and iPad, and Alexa. The categories are Google's own topics: Google no longer puts a trail above each article, so each article is filed under the topic its help centre lists it in."),
        ("Google Docs", "GoogleDocsEditorsHelp", readGoogleDocs, "GoogleDocs.md", "Google Docs help",
         "This guide holds Google's own help for Google Docs, gathered from support.google.com on 14 November 2026. It covers writing and formatting documents, pages and layout, smart chips and building blocks, tabs, citations, tools, sharing and Gemini, on a computer and on an iPhone or iPad. Using Docs with a screen reader or a braille display is under Accessibility and Use a screen reader on your computer.\r\n\r\nGoogle keeps the help for Docs, Sheets, Slides, Forms and Vids in one help centre, and this guide holds the part of it about Docs. Articles that serve every editor alike -- sharing, Google Drive, working offline, accessibility, Gemini and getting help -- are in the Docs, Sheets and Slides guides alike, under their own topics, so a reader of any one of them has them.\r\n\r\nGoogle writes the same article once for each device it runs on, so where an article differs by platform the heading says which one it is for: Computer, or iPhone and iPad. Google's Android editions are left out, as this collection covers Windows, the web, iPhone and iPad, and Alexa, and so are its policy and legal notices. The categories are Google's own topics, each article filed under the topic of its own product that lists it most."),
        ("Google Sheets", "GoogleDocsEditorsHelp", readGoogleSheets, "GoogleSheets.md", "Google Sheets help",
         "This guide holds Google's own help for Google Sheets, gathered from support.google.com on 14 November 2026. It covers making and formatting spreadsheets, sorting and filtering, pivot tables, charts, connected data, tools and sharing, and it holds Google's whole function list: each function is an article of its own, under its family, such as Math, Statistical, Text, Date and Lookup.\r\n\r\nGoogle keeps the help for Docs, Sheets, Slides, Forms and Vids in one help centre, and this guide holds the part of it about Sheets. Articles that serve every editor alike -- sharing, Google Drive, working offline, accessibility, Gemini and getting help -- are in the Docs, Sheets and Slides guides alike, under their own topics, so a reader of any one of them has them.\r\n\r\nGoogle writes the same article once for each device it runs on, so where an article differs by platform the heading says which one it is for: Computer, or iPhone and iPad. Google's Android editions are left out, as this collection covers Windows, the web, iPhone and iPad, and Alexa, and so are its policy and legal notices. The categories are Google's own topics, each article filed under the topic of its own product that lists it most."),
        ("Google Slides", "GoogleDocsEditorsHelp", readGoogleSlides, "GoogleSlides.md", "Google Slides help",
         "This guide holds Google's own help for Google Slides, gathered from support.google.com on 14 November 2026. It covers making a presentation, editing and arranging slides, shapes and images, animations, presenting and printing, collaborating and Gemini, on a computer and on an iPhone or iPad.\r\n\r\nGoogle keeps the help for Docs, Sheets, Slides, Forms and Vids in one help centre, and this guide holds the part of it about Slides. Articles that serve every editor alike -- sharing, Google Drive, working offline, accessibility, Gemini and getting help -- are in the Docs, Sheets and Slides guides alike, under their own topics, so a reader of any one of them has them.\r\n\r\nGoogle writes the same article once for each device it runs on, so where an article differs by platform the heading says which one it is for: Computer, or iPhone and iPad. Google's Android editions are left out, as this collection covers Windows, the web, iPhone and iPad, and Alexa, and so are its policy and legal notices. The categories are Google's own topics, each article filed under the topic of its own product that lists it most."),
        ("Google Vids", "GoogleDocsEditorsHelp", readGoogleVids, "GoogleVids.md", "Google Vids help",
         "This guide holds Google's own help for Google Vids, Google's video maker for work, gathered from support.google.com on 14 November 2026. It covers starting a video, adding scenes, recordings, voiceovers and captions, customizing a video, and making one with Gemini. It is a young product, so this guide is short.\r\n\r\nGoogle keeps the help for Docs, Sheets, Slides, Forms and Vids in one help centre, and this guide holds the part of it about Vids. Google writes the same article once for each device it runs on, so where an article differs by platform the heading says which one it is for: Computer, or iPhone and iPad. Google's Android editions are left out, as this collection covers Windows, the web, iPhone and iPad, and Alexa. The categories are Google's own topics."),
        ("Google Forms", "GoogleDocsEditorsHelp", readGoogleFormsEditors, "GoogleForms.md", "Google Forms help",
         "This guide holds Google's own help for Google Forms, gathered from support.google.com on 14 November 2026, and replaces September's: it is fuller and current. It covers making and editing a form, question types, quizzes, sharing a form, and collecting and viewing responses.\r\n\r\nGoogle keeps the help for Docs, Sheets, Slides, Forms and Vids in one help centre, and this guide holds the part of it about Forms. Google writes the same article once for each device it runs on, so where an article differs by platform the heading says which one it is for: Computer, or iPhone and iPad. Google's Android editions are left out, as this collection covers Windows, the web, iPhone and iPad, and Alexa. The categories are Google's own topics."),
        ("Box", "BoxHelp", readBox, "Box.md", "Box help",
         "This guide holds Box's own help, gathered from support.box.com on 15 November 2026. Box is an online service for keeping, sharing, signing and working on files with other people. Its help centre has almost 2,900 articles; this guide keeps the 668 written for a person who uses Box on Windows, the web, or an iPhone or iPad, under Box's own product names, with each product's troubleshooting beside its guides. Files, folders and sharing come under Using Box, and every app Box works inside, such as Microsoft Office, Teams, Slack, Google Workspace, Outlook and Zoom, comes under Box with other apps.\r\n\r\nLeft out on purpose: 1,729 release notes and announcements, which are a history of changes rather than help; the administrator's console and the products only an administrator runs, such as Shield, Governance, Shuttle and the developer platform; the integrations with business systems such as Salesforce and NetSuite; and Box's training and certification pages. If you run Box for an organisation, Box's own help centre has those pages."),
        ("Fiverr", "FiverrHelp", readZendeskSection, "Fiverr.md", "Fiverr help",
         "This guide holds Fiverr's own help, gathered from help.fiverr.com in November 2026. Fiverr is a marketplace where people hire freelancers for small jobs, from writing and design to voice work and programming. It covers hiring as a client or a Pro client, selling as a freelancer, orders, payments and your account. Each heading names who it is for, then the subject.\r\n\r\nLeft out on purpose: legal pages such as terms and privacy policies, pages for law enforcement and developers, and Android-only articles, as this collection covers Windows, the web, iPhone and iPad, and Alexa. The categories are the publisher's own."),
        ("GoFundMe", "GoFundMeHelp", readZendeskPlain, "GoFundMe.md", "GoFundMe help",
         "This guide holds GoFundMe's own help, gathered from support.gofundme.com in November 2026. GoFundMe is a site for raising money for a person, a cause or a charity. It covers starting and sharing a fundraiser, donating, withdrawing the money, safety and refunds, and fundraising for nonprofits.\r\n\r\nLeft out on purpose: legal pages such as terms and privacy policies, pages for law enforcement and developers, and Android-only articles, as this collection covers Windows, the web, iPhone and iPad, and Alexa. The categories are the publisher's own."),
        ("Kickstarter", "KickstarterHelp", readUdio, "Kickstarter.md", "Kickstarter help",
         "This guide holds Kickstarter's own help, gathered from help.kickstarter.com in November 2026. Kickstarter is a site where creators raise money from backers to make a project, such as a book, a game, an album or a gadget. It covers the basics, backing a project, running one as a creator, and Kickstarter's resources for creators. The categories are Kickstarter's own collections.\r\n\r\nLeft out on purpose: Android-only articles, as this collection covers Windows, the web, iPhone and iPad, and Alexa."),
        ("Ko-fi", "KofiHelp", readZendeskSection, "Kofi.md", "Ko-fi help",
         "This guide holds Ko-fi's own help, gathered from help.ko-fi.com in November 2026. Ko-fi is a site where creators take tips, memberships, commissions and shop sales from their supporters. It covers getting started, ways to earn, payments, and using Ko-fi with other platforms. Patreon, a similar site, has a guide of its own in this collection.\r\n\r\nLeft out on purpose: legal pages such as terms and privacy policies, pages for law enforcement and developers, and Android-only articles, as this collection covers Windows, the web, iPhone and iPad, and Alexa. The categories are the publisher's own."),
        ("Shop", "ShopHelp", readShop, "Shop.md", "Shop help",
         "This guide holds Shopify's own help for Shop, gathered from help.shop.app in November 2026. Shop is Shopify's shopping and delivery tracking app, on the iPhone and on the web at shop.com. It covers getting started, shopping, tracking deliveries, managing orders, Shop Cash rewards, and reporting a problem.\r\n\r\n Shop and Shop Pay share one help centre, so this collection splits it in two: Shop.md for the Shop app and ShopPay.md for paying with Shop Pay and Shop Pay Installments. Each section opens with Shopify's own overview of it. Shopify's help for store owners is a separate guide, Shopify.md. Android-only articles are left out, as this collection covers Windows, the web, iPhone and iPad, and Alexa."),
        ("Shop Pay", "ShopHelp", readShopPay, "ShopPay.md", "Shop Pay help",
         "This guide holds Shopify's own help for Shop Pay, gathered from help.shop.app in November 2026. Shop Pay saves your payment and shipping details so you can check out faster at stores that use Shopify. It covers paying online and in stores, the cards it accepts, its settings and security, and Shop Pay Installments, which splits a purchase into payments.\r\n\r\n Shop and Shop Pay share one help centre, so this collection splits it in two: Shop.md for the Shop app and ShopPay.md for paying with Shop Pay and Shop Pay Installments. Each section opens with Shopify's own overview of it. Shopify's help for store owners is a separate guide, Shopify.md."),
        ("HubSpot account", "HubSpotHelp", readHubSpotAccount, "HubSpotAccount.md", "HubSpot help: account and setup",
         "This guide holds HubSpot's own help for setting up and running a HubSpot account, gathered from knowledge.hubspot.com in November 2026: users and permissions, settings, billing, security, integrations, getting started, HubSpot's AI tools, and its partner program.\r\n\r\nHubSpot's knowledge base is too large for one guide, so this collection splits it by HubSpot's own top categories into four: HubSpotAccount.md for account setup, getting started, its AI tools and partners; HubSpotCrm.md for the CRM, sales, service and revenue tools; HubSpotData.md for automation, data and reporting; and HubSpotMarketing.md for marketing and content. The categories are HubSpot's own, from the trail above each article. Android-only articles are left out, as this collection covers Windows, the web, iPhone and iPad, and Alexa. HubSpot's developer documentation is a separate site and is not here."),
        ("HubSpot CRM", "HubSpotHelp", readHubSpotCrm, "HubSpotCrm.md", "HubSpot help: CRM, sales, service and revenue",
         "This guide holds HubSpot's own help for its customer records and the tools built on them, gathered from knowledge.hubspot.com in November 2026: contacts, companies, deals and tickets, the sales tools, the help desk and other service tools, and payments, quotes and other revenue tools.\r\n\r\nHubSpot's knowledge base is too large for one guide, so this collection splits it by HubSpot's own top categories into four: HubSpotAccount.md for account setup, getting started, its AI tools and partners; HubSpotCrm.md for the CRM, sales, service and revenue tools; HubSpotData.md for automation, data and reporting; and HubSpotMarketing.md for marketing and content. The categories are HubSpot's own, from the trail above each article. Android-only articles are left out, as this collection covers Windows, the web, iPhone and iPad, and Alexa. HubSpot's developer documentation is a separate site and is not here."),
        ("HubSpot data", "HubSpotHelp", readHubSpotData, "HubSpotData.md", "HubSpot help: automation, data and reporting",
         "This guide holds HubSpot's own help for automating work and understanding data, gathered from knowledge.hubspot.com in November 2026: workflows and sequences, importing, cleaning and syncing data, and reports, dashboards and analytics.\r\n\r\nHubSpot's knowledge base is too large for one guide, so this collection splits it by HubSpot's own top categories into four: HubSpotAccount.md for account setup, getting started, its AI tools and partners; HubSpotCrm.md for the CRM, sales, service and revenue tools; HubSpotData.md for automation, data and reporting; and HubSpotMarketing.md for marketing and content. The categories are HubSpot's own, from the trail above each article. Android-only articles are left out, as this collection covers Windows, the web, iPhone and iPad, and Alexa. HubSpot's developer documentation is a separate site and is not here."),
        ("HubSpot marketing", "HubSpotHelp", readHubSpotMarketing, "HubSpotMarketing.md", "HubSpot help: marketing and content",
         "This guide holds HubSpot's own help for marketing and content, gathered from knowledge.hubspot.com in November 2026: email, forms, ads, social media, campaigns, and building websites, landing pages and blogs.\r\n\r\nHubSpot's knowledge base is too large for one guide, so this collection splits it by HubSpot's own top categories into four: HubSpotAccount.md for account setup, getting started, its AI tools and partners; HubSpotCrm.md for the CRM, sales, service and revenue tools; HubSpotData.md for automation, data and reporting; and HubSpotMarketing.md for marketing and content. The categories are HubSpot's own, from the trail above each article. Android-only articles are left out, as this collection covers Windows, the web, iPhone and iPad, and Alexa. HubSpot's developer documentation is a separate site and is not here."),
        ("Mercury", "MercuryHelp", readZendeskSection, "Mercury.md", "Mercury help",
         "This guide holds Mercury's own help, gathered from support.mercury.com in November 2026. Mercury is a financial technology company that offers business and personal banking through partner banks. The guide covers opening an account, sending and receiving money, cards, statements and documents, and Mercury's other business tools. Each heading names the category, Business or Personal, then the subject.\r\n\r\nLeft out on purpose: legal pages such as terms, privacy policies and disclosures, pages for law enforcement and developers, and Android-only articles, as this collection covers Windows, the web, iPhone and iPad, and Alexa."),
        ("Patreon", "PatreonHelp", readZendeskSection, "Patreon.md", "Patreon help",
         "This guide holds Patreon's own help, gathered from support.patreon.com in November 2026. Patreon is a site where creators earn from members who pay each month for their work. It covers joining and paying as a member, and setting up, earning and getting paid as a creator. Each heading names who it is for, then the subject. Ko-fi, a similar site, has a guide of its own in this collection.\r\n\r\nLeft out on purpose: legal pages such as terms and privacy policies, pages for law enforcement and developers, and Android-only articles, as this collection covers Windows, the web, iPhone and iPad, and Alexa. The categories are the publisher's own."),
        ("Twitch", "TwitchHelp", readTwitch, "Twitch.md", "Twitch help",
         "This guide holds Twitch's own help, gathered from help.twitch.tv in November 2026. Twitch is a live streaming site, best known for games, music and talk shows. Its help is written mostly for people who stream: setting up a channel and a broadcast, chat and moderation, the Affiliate and Partner programs and how they pay, and keeping an account safe. Viewers will find the account, purchase and safety articles most useful.\r\n\r\nTwitch's help centre draws every page with script, so each page was drawn by Microsoft Edge before it was saved, and the gathering followed the links between articles. An article no other article links to may be missing. The categories are Twitch's own, from the trail printed above each article. Legal pages such as terms of service are not part of the help centre and are not here."),
        ("Wyzant", "WyzantHelp", readWyzant, "Wyzant.md", "Wyzant help",
         "This guide holds Wyzant's own help, gathered from support.wyzant.com in November 2026. Wyzant is a site for finding a private tutor and taking lessons, online or in person. It covers students and parents, tutors, the online learning studio, and Wyzant's programs for schools and colleges.\r\n\r\nLeft out on purpose: legal pages such as terms and privacy policies, pages for law enforcement and developers, and Android-only articles, as this collection covers Windows, the web, iPhone and iPad, and Alexa. The categories are the publisher's own."),
        ("PiccyBot", "PiccyBotHelp", readPiccyBot, "PiccyBot.md", "PiccyBot help",
         "This guide holds PiccyBot's own words about using it, gathered from piccybot.com on 23 November 2026. PiccyBot describes photos and videos aloud on the iPhone and on Android, answers questions about them, and works through WhatsApp, including hands-free with Meta's Ray-Ban glasses. It covers how the app works, its features, setting it up on WhatsApp and the glasses, and what the free and Pro plans include.\r\n\r\nThis is a short guide, because PiccyBot publishes its help on a single page. That page also lists common questions, but it shows each answer only when its question is opened, so the answers did not come with the page and the questions are left out rather than given without answers. Also left out: the welcome, what users say, the video showcase, honors, donations and the technology partner, which are not help. The categories are PiccyBot's own headings."),
        ("Clubhouse", "ClubhouseHelp", readClubhouse, "Clubhouse.md", "Clubhouse help",
         "This guide holds Clubhouse's own help, gathered from support.clubhouse.com in November 2026. Clubhouse is a social app for talking live in rooms, sending voice messages and chats, and building groups called houses. It covers signing up and your profile, the hallway and explore, live rooms, messages, friends and houses, Clubhouse Plus, and trust and safety, for the iPhone and iPad app and the web. Android-only articles are left out, as this collection covers Windows, the web, iPhone and iPad, and Alexa.\r\n\r\nLeft out on purpose: Clubhouse's legal pages, its policies, its pages for law enforcement and government requests, its copyright notices and its country notices. The categories are Clubhouse's own."),
        ("Egnyte", "EgnyteHelp", readEgnyte, "Egnyte.md", "Egnyte help",
         "This guide holds Egnyte's own help, gathered from helpdesk.egnyte.com on 15 November 2026. Egnyte is an online service that businesses use to store, share and work on files. Its help centre has about 1,500 articles, most written for the company administrators who set it up; this guide keeps the 421 written for a person who uses it: the web app, the desktop app, the iPhone and iPad app, the AI assistant, and Egnyte with Microsoft 365 and Google.\r\n\r\nLeft out on purpose: 607 announcements, release notes and known issues, which are a history of changes rather than help; the administrators' pages, such as users and groups, governance, reporting, migration and the storage appliances; and the editions for architects and life sciences companies. If you run Egnyte for your company, Egnyte's own help centre has those pages."),
        ("Excel", "ExcelHelp", readMicrosoftExcel, "Excel.md", "Excel help",
         "This guide holds Microsoft's own help for Excel, gathered from support.microsoft.com on 14 November 2026. It is the largest guide in this collection: Microsoft documents every Excel function in an article of its own, and they are kept together under Excel functions.\r\n\r\nMicrosoft writes one article for many versions of each app. This guide keeps the latest only, on the surfaces this collection covers: the Microsoft 365 app on Windows, the web version, and the iPhone and iPad apps. An article Microsoft wrote only for a Mac, for Android, or for an older version such as 2016 or 2021 is left out, and so are legal pages and programmers' references. Each article's first line says which versions it applies to, and where an article has a part for each platform, each part is headed with its platform's name. Microsoft files many articles in no topic of their own, so this guide places them by the words in their titles; what fits no topic is under Miscellaneous. The accessibility articles, which include Microsoft's instructions for using the app with a screen reader, are under Accessibility and keyboard."),
        ("OneDrive", "OneDriveHelp", readMicrosoftOneDrive, "OneDrive.md", "OneDrive help",
         "This guide holds Microsoft's own help for OneDrive, gathered from support.microsoft.com on 14 November 2026. It replaces the guide gathered in August, which came from a crawl of the site rather than Microsoft's own list of articles.\r\n\r\nMicrosoft writes one article for many versions of each app. This guide keeps the latest only, on the surfaces this collection covers: the Microsoft 365 app on Windows, the web version, and the iPhone and iPad apps. An article Microsoft wrote only for a Mac, for Android, or for an older version such as 2016 or 2021 is left out, and so are legal pages and programmers' references. Each article's first line says which versions it applies to, and where an article has a part for each platform, each part is headed with its platform's name. Microsoft files many articles in no topic of their own, so this guide places them by the words in their titles; what fits no topic is under Miscellaneous. The accessibility articles, which include Microsoft's instructions for using the app with a screen reader, are under Accessibility and keyboard."),
        ("Outlook", "OutlookHelp", readMicrosoftOutlook, "Outlook.md", "Outlook help",
         "This guide holds Microsoft's own help for Outlook, gathered from support.microsoft.com on 14 November 2026. It covers both the new Outlook for Windows and classic Outlook, and Outlook on the web, which Microsoft documents side by side.\r\n\r\nMicrosoft writes one article for many versions of each app. This guide keeps the latest only, on the surfaces this collection covers: the Microsoft 365 app on Windows, the web version, and the iPhone and iPad apps. An article Microsoft wrote only for a Mac, for Android, or for an older version such as 2016 or 2021 is left out, and so are legal pages and programmers' references. Each article's first line says which versions it applies to, and where an article has a part for each platform, each part is headed with its platform's name. Microsoft files many articles in no topic of their own, so this guide places them by the words in their titles; what fits no topic is under Miscellaneous. The accessibility articles, which include Microsoft's instructions for using the app with a screen reader, are under Accessibility and keyboard."),
        ("PowerPoint", "PowerPointHelp", readMicrosoftPowerPoint, "PowerPoint.md", "PowerPoint help",
         "This guide holds Microsoft's own help for PowerPoint, gathered from support.microsoft.com on 14 November 2026. It covers making slides, animations, presenting and recording, and Copilot in PowerPoint.\r\n\r\nMicrosoft writes one article for many versions of each app. This guide keeps the latest only, on the surfaces this collection covers: the Microsoft 365 app on Windows, the web version, and the iPhone and iPad apps. An article Microsoft wrote only for a Mac, for Android, or for an older version such as 2016 or 2021 is left out, and so are legal pages and programmers' references. Each article's first line says which versions it applies to, and where an article has a part for each platform, each part is headed with its platform's name. Microsoft files many articles in no topic of their own, so this guide places them by the words in their titles; what fits no topic is under Miscellaneous. The accessibility articles, which include Microsoft's instructions for using the app with a screen reader, are under Accessibility and keyboard."),
        ("SharePoint", "SharePointHelp", readMicrosoftSharePoint, "SharePoint.md", "SharePoint help",
         "This guide holds Microsoft's own help for SharePoint, gathered from support.microsoft.com on 14 November 2026. It covers sites, pages, lists and document libraries as a person who uses SharePoint meets them. Microsoft's pages for administrators of SharePoint are left out.\r\n\r\nMicrosoft writes one article for many versions of each app. This guide keeps the latest only, on the surfaces this collection covers: the Microsoft 365 app on Windows, the web version, and the iPhone and iPad apps. An article Microsoft wrote only for a Mac, for Android, or for an older version such as 2016 or 2021 is left out, and so are legal pages and programmers' references. Each article's first line says which versions it applies to, and where an article has a part for each platform, each part is headed with its platform's name. Microsoft files many articles in no topic of their own, so this guide places them by the words in their titles; what fits no topic is under Miscellaneous. The accessibility articles, which include Microsoft's instructions for using the app with a screen reader, are under Accessibility and keyboard."),
        ("Word", "WordHelp", readMicrosoftWord, "Word.md", "Word help",
         "This guide holds Microsoft's own help for Word, gathered from support.microsoft.com on 14 November 2026. It covers writing, formatting, layout, reviewing, mail merge, references and Word's field codes.\r\n\r\nMicrosoft writes one article for many versions of each app. This guide keeps the latest only, on the surfaces this collection covers: the Microsoft 365 app on Windows, the web version, and the iPhone and iPad apps. An article Microsoft wrote only for a Mac, for Android, or for an older version such as 2016 or 2021 is left out, and so are legal pages and programmers' references. Each article's first line says which versions it applies to, and where an article has a part for each platform, each part is headed with its platform's name. Microsoft files many articles in no topic of their own, so this guide places them by the words in their titles; what fits no topic is under Miscellaneous. The accessibility articles, which include Microsoft's instructions for using the app with a screen reader, are under Accessibility and keyboard."),
        ("Claude web", "ClaudeHelp", readClaudeWeb, "ClaudeWeb.md", "Claude help: web, plans and connectors",
         "This guide holds Anthropic's own help for Claude on the web at claude.ai, gathered from support.claude.com in November 2026. It covers getting started, chats and projects, features such as artifacts, memory and research, settings, usage limits, troubleshooting, the paid plans, connectors to other apps, Claude in Chrome, Claude for Education, and Anthropic's safety rules for users.\r\n\r\nAnthropic writes one help centre for every way of using Claude, so this collection splits it into six guides: ClaudeWeb.md for Claude on the web and in Chrome, with plans, connectors and safety; ClaudeDesktop.md for the Windows app; ClaudeIos.md for the iPhone and iPad app; ClaudeCowork.md for Cowork; ClaudeCode.md for Claude Code; and ClaudeDuet.md for Duet. Each article is in one guide only. Articles written only for a Mac or for Android are left out, since this collection covers Windows, the web and the iPhone and iPad. Also left out are pages for an organization's administrators, and Anthropic's collections on its programming interface and Console, Amazon Bedrock, identity management, and privacy and legal terms. The categories are Anthropic's own, taken from the trail of collections printed above each article."),
        ("Claude desktop", "ClaudeHelp", readClaudeDesktop, "ClaudeDesktop.md", "Claude help: the Windows desktop app",
         "This guide holds Anthropic's own help for the Claude desktop app on Windows, gathered from support.claude.com in November 2026. It covers installing and updating the app, its settings and shortcuts, and desktop extensions, which let Claude reach programs and files on your computer.\r\n\r\nAnthropic writes one help centre for every way of using Claude, so this collection splits it into six guides: ClaudeWeb.md for Claude on the web and in Chrome, with plans, connectors and safety; ClaudeDesktop.md for the Windows app; ClaudeIos.md for the iPhone and iPad app; ClaudeCowork.md for Cowork; ClaudeCode.md for Claude Code; and ClaudeDuet.md for Duet. Each article is in one guide only. Articles written only for a Mac or for Android are left out, since this collection covers Windows, the web and the iPhone and iPad. Also left out are pages for an organization's administrators, and Anthropic's collections on its programming interface and Console, Amazon Bedrock, identity management, and privacy and legal terms. The categories are Anthropic's own, taken from the trail of collections printed above each article."),
        ("Claude iOS", "ClaudeHelp", readClaudeIos, "ClaudeIos.md", "Claude help: the iPhone and iPad app",
         "This guide holds Anthropic's own help for the Claude app on the iPhone and iPad, gathered from support.claude.com in November 2026. It covers installing the app, signing in, voice mode, and the features the app shares with the web.\r\n\r\nAnthropic writes one help centre for every way of using Claude, so this collection splits it into six guides: ClaudeWeb.md for Claude on the web and in Chrome, with plans, connectors and safety; ClaudeDesktop.md for the Windows app; ClaudeIos.md for the iPhone and iPad app; ClaudeCowork.md for Cowork; ClaudeCode.md for Claude Code; and ClaudeDuet.md for Duet. Each article is in one guide only. Articles written only for a Mac or for Android are left out, since this collection covers Windows, the web and the iPhone and iPad. Also left out are pages for an organization's administrators, and Anthropic's collections on its programming interface and Console, Amazon Bedrock, identity management, and privacy and legal terms. The categories are Anthropic's own, taken from the trail of collections printed above each article."),
        ("Claude Cowork", "ClaudeHelp", readClaudeCowork, "ClaudeCowork.md", "Claude help: Cowork",
         "This guide holds Anthropic's own help for Cowork, gathered from support.claude.com in November 2026. Cowork is Claude's way of taking on longer tasks that work with your files and apps and hand back finished work. The guide covers starting a task, connecting folders and apps, scheduled tasks, and what Cowork can and cannot do.\r\n\r\nAnthropic writes one help centre for every way of using Claude, so this collection splits it into six guides: ClaudeWeb.md for Claude on the web and in Chrome, with plans, connectors and safety; ClaudeDesktop.md for the Windows app; ClaudeIos.md for the iPhone and iPad app; ClaudeCowork.md for Cowork; ClaudeCode.md for Claude Code; and ClaudeDuet.md for Duet. Each article is in one guide only. Articles written only for a Mac or for Android are left out, since this collection covers Windows, the web and the iPhone and iPad. Also left out are pages for an organization's administrators, and Anthropic's collections on its programming interface and Console, Amazon Bedrock, identity management, and privacy and legal terms. The categories are Anthropic's own, taken from the trail of collections printed above each article."),
        ("Claude Code", "ClaudeHelp", readClaudeCode, "ClaudeCode.md", "Claude help: Claude Code",
         "This guide holds Anthropic's own help for Claude Code, gathered from support.claude.com in November 2026. Claude Code is Anthropic's coding agent, used from a terminal, the web, the desktop app or a phone. The guide covers setting it up with a paid plan, its usage limits, and Anthropic's launch guides. Anthropic's full technical reference for Claude Code lives in its developer documentation, which this guide does not hold.\r\n\r\nAnthropic writes one help centre for every way of using Claude, so this collection splits it into six guides: ClaudeWeb.md for Claude on the web and in Chrome, with plans, connectors and safety; ClaudeDesktop.md for the Windows app; ClaudeIos.md for the iPhone and iPad app; ClaudeCowork.md for Cowork; ClaudeCode.md for Claude Code; and ClaudeDuet.md for Duet. Each article is in one guide only. Articles written only for a Mac or for Android are left out, since this collection covers Windows, the web and the iPhone and iPad. Also left out are pages for an organization's administrators, and Anthropic's collections on its programming interface and Console, Amazon Bedrock, identity management, and privacy and legal terms. The categories are Anthropic's own, taken from the trail of collections printed above each article."),
        ("Claude Duet", "ClaudeHelp", readClaudeDuet, "ClaudeDuet.md", "Claude help: Duet",
         "This guide holds Anthropic's own help for Claude Duet, gathered from support.claude.com in November 2026. It covers getting started with Duet and paying through Link by Stripe or Shop Pay. It is short because the source is short.\r\n\r\nAnthropic writes one help centre for every way of using Claude, so this collection splits it into six guides: ClaudeWeb.md for Claude on the web and in Chrome, with plans, connectors and safety; ClaudeDesktop.md for the Windows app; ClaudeIos.md for the iPhone and iPad app; ClaudeCowork.md for Cowork; ClaudeCode.md for Claude Code; and ClaudeDuet.md for Duet. Each article is in one guide only. Articles written only for a Mac or for Android are left out, since this collection covers Windows, the web and the iPhone and iPad. Also left out are pages for an organization's administrators, and Anthropic's collections on its programming interface and Console, Amazon Bedrock, identity management, and privacy and legal terms. The categories are Anthropic's own, taken from the trail of collections printed above each article."),
        # PAYMENTS (24 November 2026)
        ("Stripe", "StripeHelp", readStripe, "Stripe.md", "Stripe help",
         "This guide holds Stripe's own support articles, gathered from support.stripe.com on 20 November 2026. Stripe is a service businesses use to take payments online and in person, send invoices, run subscriptions and get paid out to their bank. The articles are written for the people who run a Stripe account: payments, refunds and disputes, payouts, billing and invoices, taxes and tax forms, verifying a business, Connect for platforms and marketplaces, Terminal card readers, and keeping an account secure. The categories are Stripe's own topics.\r\n\r\nLeft out on purpose: articles for programmers, that is the API and Webhooks topics, the move off Stripe's older Sources API, and any article whose title names an API; legal notices and policy statements; and articles for Android alone, as this collection covers Windows, the web, iPhone and iPad, and Alexa. Stripe's developer documentation is a separate site and is not here. Link, Stripe's checkout for shoppers, has a guide of its own, Link.md."),
        ("Link", "LinkHelp", readLink, "Link.md", "Link help",
         "This guide holds the support articles for Link, gathered from support.link.com on 20 November 2026. Link is Stripe's way to save your payment details once and check out quickly at the many online stores that use Stripe. It covers your Link account, paying and purchases, verifying who you are, keeping your data private, the Link card and balance, buying cryptocurrency, and paying through AI agents. The categories are Link's own topics.\r\n\r\nLink is run by Stripe, whose help for businesses is a separate guide, Stripe.md. When a charge on your statement says it was sold through Link, the article on that charge explains who to contact."),
        # MAPPING (28 November 2026)
        ("QGIS", "QgisHelp", readQgis, "QGIS.md", "QGIS help",
         "This guide holds the QGIS project's own documentation for QGIS 3.44, gathered from docs.qgis.org in November 2026. QGIS is a free, open-source geographic information system: a desktop program for making maps and for studying data tied to places, such as the bus stops, routes and timetables a transit agency publishes. It holds three of the project's manuals, each under its own headings: the User Guide, which documents every part of the program; the Training Manual, a course of lessons with exercises; and A Gentle Introduction to GIS, which explains the ideas behind maps and spatial data.\r\n\r\nFor transit work, three places are worth knowing first. The network analysis algorithms, which find shortest paths and the area reachable within a distance or time along a network, are in the User Guide under Processing providers and algorithms, and the Training Manual teaches them in its Vector Analysis module. Using processing from the command line, under QGIS processing framework, describes qgis_process, which runs any of those algorithms from a command prompt rather than the map window. QGIS has no tools of its own for GTFS, the format transit agencies publish schedules in; that work is done with plugins, whose help is kept by their own authors and is not here.\r\n\r\nThe manuals are written for every desktop system QGIS runs on, so a few passages speak of macOS or Linux; they are left as the publisher wrote them. Left out on purpose: the PyQGIS cookbook, the server manual and the developers' guide, which are written for programmers and server administrators; the Training Manual's module on QGIS Server; the manual's page on contributing to itself; and the translated editions. A chapter's opening page that only lists its sections is not repeated here, since its sections are."),
    ]
    # ONE ENTRY PER GUIDE (version 2). The plan had grown a second copy of twenty entries, from Org mode to Remote
    # Incident Manager, so those guides were built twice in every run; the first entry for a guide now wins.
    # A GUIDE MADE FROM A NEWER HARVEST (15 November 2026): Google Forms is now built from the Docs editors' harvest,
    # and September's GoogleFormsHelp entry stays for its record. The first entry whose harvest is here wins; when none
    # is here, the first entry, as before.
    lPlan = sorted(lPlan, key=lambda t: 0 if os.path.isdir(os.path.join(sParent, t[1])) else 1)
    lUnique, setFiles = [], set()
    for tEntry in lPlan:
        if tEntry[3].lower() in setFiles:
            logging.info("plan: a second entry for %s is ignored", tEntry[3])
            continue
        setFiles.add(tEntry[3].lower())
        lUnique.append(tEntry)
    lPlan = lUnique
    if lOnly:
        setOnly = {s.lower() for s in lOnly}
        lPlan = [t for t in lPlan if t[0].lower() in setOnly or os.path.splitext(t[3])[0].lower() in setOnly or t[3].lower() in setOnly]
    lResults = []
    iNoHarvest = iCurrent = 0
    # NEVER SILENT FOR MINUTES (15 November 2026): Excel's guide takes minutes to build, and this script said nothing
    # until every guide was done, so a build that was working looked hung and was stopped. Each guide is now named as it
    # starts and its result said as it ends.
    print("Checking %d guide%s against their harvests." % (len(lPlan), "" if len(lPlan) == 1 else "s"), flush=True)
    for sProduct, sFolder, functionRead, sFile, sTitle, sPreamble in lPlan:
        sHarvest = os.path.join(sParent, sFolder)
        if not os.path.isdir(sHarvest):
            iNoHarvest += 1
            logging.info("%s: no harvest folder at %s, so it is not built", sProduct, sHarvest)
            # A READER CHANGED AFTER ITS HARVEST WAS DELETED (23 November 2026): the guide cannot be rebuilt here, so
            # say how to get it rebuilt rather than leave it silently stale.
            nGone = readerChangedTime(sFile)
            sGuideGone = os.path.join(sOutput, sFile)
            if nGone and os.path.isfile(sGuideGone) and os.path.getmtime(sGuideGone) < nGone:
                print("%s: its reader changed, but its harvest was deleted after it was built; ask for it again in an "
                      "addGuides file with a later asked= day to rebuild it." % sFile, flush=True)
                logging.info("%s: reader changed after its harvest was deleted; it needs a fresh gathering", sProduct)
            continue
        sGuide = os.path.join(sOutput, sFile)
        # A GUIDE IS REBUILT ONLY WHEN ITS HARVEST IS NEWER (version 2): the Homer rule that a build does again only
        # what has changed. A guide named on the command line is always rebuilt, which is how a guide whose reader
        # changed is brought up to date: build GoodMaps.
        # A READER THAT CHANGED REBUILDS ITS GUIDES (1.264.1, 20 November 2026): the Claude guides built on 19 November
        # kept duplicate articles and owners' pages after their reader was fixed, because their harvest was older than
        # they were, and naming them on a command line is a step outside build_release. dReaderChanged gives the time a
        # guide's reader last changed; a guide older than that is rebuilt by the ordinary build, once, and logged.
        nReader = readerChangedTime(sFile)
        if nReader and os.path.isfile(sGuide) and os.path.getmtime(sGuide) < nReader:
            logging.info("%s: its reader changed after %s was built, so it is rebuilt", sProduct, sFile)
        elif bChanged and not lOnly and os.path.isfile(sGuide) and os.path.getmtime(sGuide) >= newestTime(sHarvest):
            iCurrent += 1
            logging.info("%s: %s is newer than its harvest, so it is left as it is", sProduct, sFile)
            continue
        print("Building %s from %s..." % (sFile, sFolder), flush=True)
        nStarted = time.time()
        try:
            lArticles = functionRead(sHarvest)
            sPath = os.path.join(sOutput, sFile)
            sText = buildGuide(sProduct, sTitle, sPreamble, lArticles, sPath)
            lFailures = runGates(sProduct, sPath, sText)
            lResults.append((sProduct, len(re.findall(r"^### ", sText, re.M)), len(sText.split()), len(lFailures)))
        except Exception as oError:
            logging.exception("%s failed to build: %s", sProduct, oError)
            lResults.append((sProduct, 0, 0, -1))
        sProduct, iArticles, iWords, iFailures = lResults[-1]
        print("  %s: %d articles, %d words, %s, %d seconds" % (sProduct, iArticles, iWords,
              "all clean" if iFailures == 0 else ("failed to build" if iFailures < 0 else "%d gate failures" % iFailures),
              int(time.time() - nStarted)), flush=True)
    # A GUIDE REPLACED BY OTHERS IS RETIRED BY THE BUILD (19 November 2026). Claude.md, one guide for all of Claude, gave
    # way that day to six guides, one a surface. Once every guide that replaces it is built and passes its gates, the old
    # guide and its page move to notes\retired, logged, so the push drops them and nothing is deleted.
    if bBuild:
        for sOld, lNew in [("Claude.md", ["ClaudeWeb.md", "ClaudeDesktop.md", "ClaudeIos.md", "ClaudeCowork.md", "ClaudeCode.md", "ClaudeDuet.md"])]:
            if not os.path.isfile(os.path.join(sOutput, sOld)) and not os.path.isfile(os.path.join(sOutput, os.path.splitext(sOld)[0] + ".htm")): continue
            lMissing = [s for s in lNew if not os.path.isfile(os.path.join(sOutput, s))]
            lFailed = [t[0] for t in lResults if t[3] != 0 and any(os.path.splitext(s)[0].lower() == t[0].replace(" ", "").lower() for s in lNew)]
            if lMissing or lFailed:
                logging.info("retire %s: waiting, since %s", sOld, "missing " + ", ".join(lMissing) if lMissing else "failed " + ", ".join(lFailed))
                continue
            lRetiredNow = []
            for sName in (sOld, os.path.splitext(sOld)[0] + ".htm"):
                if os.path.isfile(os.path.join(sOutput, sName)):
                    moveInto(os.path.join(sOutput, sName), os.path.join(sOutput, "notes", "retired"), lRetiredNow)
            if lRetiredNow:
                logging.info("retire %s: replaced by %s; moved %s", sOld, ", ".join(lNew), "; ".join("%s -> %s" % t for t in lRetiredNow))
                print("Retired %s, replaced by %d guides; it is in notes\\retired." % (sOld, len(lNew)))
    iBuilt = len(lResults)
    print("Guides built: %d; already current: %d; no harvest here: %d." % (iBuilt, iCurrent, iNoHarvest))
    logging.info("SUMMARY: %d built, %d current, %d without a harvest", iBuilt, iCurrent, iNoHarvest)
    iResult = 1 if any(t[3] != 0 for t in lResults) else 0
    if iResult: print("A guide failed its gates or its build, so this run fails; the log names the failures.")
    if bBuild:
        lMasked = maskSecretsInGuides(sOutput)
        if lMasked: print("Cut secret-shaped keys from %s, so the push is not refused." % ", ".join(lMasked))
    # THE .htm OF EVERY CHANGED GUIDE (version 2): the kit's fixPages, which gives each page one level-one heading,
    # its language, a main landmark and working links, and reports what it could not settle.
    if bBuild:
        sFix = os.path.join(kitFolder(), "scripts", "fixPages.py")
        lCommand = [sys.executable, sFix, sOutput, "--changed"]
        if not os.path.isfile(sFix):
            logging.error("the kit's fixPages.py is not at %s, so no .htm was built", sFix)
            print("The kit's fixPages.py was not found, so no web page was built.")
            iResult = 1
        else:
            oRun = subprocess.run(lCommand, capture_output=True, text=True, errors="replace")
            logging.info("RUN %s: exit %d", " ".join(lCommand), oRun.returncode)
            for sLine in (oRun.stdout or "").splitlines(): logging.info("    fixPages: %s", sLine)
            for sLine in (oRun.stderr or "").splitlines(): logging.error("    fixPages: %s", sLine)
            sSaid = [sLine for sLine in (oRun.stdout or "").splitlines() if not re.match(r"\d+ of \d+: ", sLine)]
            for sLine in sSaid: print(sLine)
            if oRun.returncode != 0: iResult = 1
    if bBuild: pruneHarvests(sParent, sOutput, lPlan, lResults)
    logging.info("RUN ENDED %s", "with failures" if iResult else "cleanly")
    print("Log: " + sLogPath)
    return iResult


if __name__ == "__main__": sys.exit(main())
