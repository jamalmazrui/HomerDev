"""buildGuide.py version 1

Turns a folder of harvested pages into one help guide: a Markdown file and its
HTML pair.

HOW TO USE IT. Run it with the folder holding the harvests and the folder to
write guides into: buildGuide.cmd harvests guides

Each product has a reader function here that knows the shape of that
publisher's pages — where the article's body is, where its title is, and how
its categories are named. To add a product, write a reader and add one line to
the build list. The readers already here cover most shapes you will meet:
Zendesk listings, Intercom, Google help centres, Microsoft support, Sphinx
manuals, VitePress and plain documentation sites.

THE GUIDE FORMAT, THE CATEGORY RULES AND THE GATES are in
references/guide-format.md.
"""

import html, html.parser, io, json, logging, os, platform, re, sys, urllib.parse

c_iMinCategory = 2
c_sBom = "\ufeff"
c_sEncoding = "utf-8-sig"
c_sLogName = "buildMagazines.log"
c_sMiscellaneous = "Miscellaneous"
c_sNewLine = "\r\n"

c_lLitterExact = ["print", "home", "sign in", "back to home", "all collections", "table of contents",
                  "skip to main content", "powered by", "powered by intercom", "we run on fin",
                  "return to top", "related articles", "was this helpful", "submit a request"]
c_lFeedback = ["was this article helpful", "was this page helpful", "was this helpful",
               "was this information helpful", "did this answer your question",
               "did you find it helpful", "how can we improve it",
               "how satisfied are you with this reply", "provide feedback about this article",
               "out of found this helpful", "of people found this helpful"]
c_lFeedbackAnswers = ["yes", "no", "yes no", "disappointed", "neutral", "smiley", "share"]
c_lLitterPrefix = ["did this answer your question", "was this article helpful", "still need help",
                   "have more questions", "use of this site constitutes acceptance", "all rights reserved"]


class markdownParser(html.parser.HTMLParser):
    """Turns a fragment of help markup into Markdown lines."""

    def __init__(self, iBaseLevel):
        super().__init__(convert_charrefs=True)
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
            if sUrl.startswith(("#", "/", ".")): return True
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
        self.sBuffer += sText
        return True


def readText(sPath):
    """Reads a saved page as text, tolerating a byte order mark."""
    fHandle = io.open(sPath, "r", encoding="utf-8", errors="replace")
    sText = fHandle.read()
    fHandle.close()
    return sText.lstrip(c_sBom)


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


def toMarkdown(sMarkup, iBaseLevel):
    """Turns one article body into Markdown lines, furniture removed."""
    oParser = markdownParser(iBaseLevel)
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
        if oOnlyLink and re.sub(r"[^a-z ]", "", oOnlyLink.group(1).lower()).strip() in c_lLitterExact: continue
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
        if sTest and any(sTest.startswith(sPhrase) for sPhrase in c_lFeedback):
            iFeedbackAt[0] = len(lOut)
            continue
        if sTest in c_lFeedbackAnswers and iFeedbackAt[0] >= 0 and len(lOut) - iFeedbackAt[0] <= 3: continue
        if sTest and not bHeading and sTest in c_lLitterExact: continue
        if sTest and not bHeading and any(sTest.startswith(sItem) for sItem in c_lLitterPrefix): continue
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
    return "zzzz" if sCategory == c_sMiscellaneous else sortKeyTitle(sCategory)


def makeAnchor(sTitle):
    """Builds the Pandoc anchor for a heading."""
    sAnchor = re.sub(r"[^\w\s-]", "", sTitle.lower(), flags=re.U)
    return re.sub(r"\s+", "-", sAnchor.strip())


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
            sCategory = tSection[0] or dCategories.get(tSection[1], c_sMiscellaneous) or c_sMiscellaneous
            # A publisher may leave a section's name as a stray character —
            # iHeartRadio has one called "/". That is not a category name.
            if not re.search(r"\w", sCategory): sCategory = c_sMiscellaneous
            lArticles.append((sCategory, dArticle["title"], toMarkdown(dArticle.get("body") or "", 0)))
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
    sCategory = c_sMiscellaneous
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
    sCategory = c_sMiscellaneous
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
    sCategory = c_sMiscellaneous
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
        sCategory = lCrumbs[-1] if lCrumbs else c_sMiscellaneous
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
        sCategory = dGroups.get(oAnchor.group(1), sCategoryDefault or c_sMiscellaneous) if oAnchor else (sCategoryDefault or c_sMiscellaneous)
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
                    lArticles.append((sPublication + ": " + sCategory if sCategory != c_sMiscellaneous else sPublication,
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
        sCategory = dGroups.get(oAnchor.group(1), c_sMiscellaneous) if oAnchor else c_sMiscellaneous
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
        sCategory = lCrumbs[-1] if lCrumbs else c_sMiscellaneous
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
        sCategory = c_sMiscellaneous
        oAudience = re.search(r"(?is)•\s*([A-Za-z][A-Za-z ]{2,30})</div>", sBefore[-4000:])
        if oAudience: sCategory = oAudience.group(1).strip().title()
        sBody = sMarkup[oTitle.end():]
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 25: continue
        lArticles.append((sCategory, sTitle, lBody))
    return lArticles


c_oVerizonDevice = re.compile(r"(apple|samsung|google|motorola|pixel|iphone|ipad|galaxy|watch|tablet|kyocera|nokia|orbic|tcl|razr|blackberry|sonim|schok|jitterbug|hotspot|inseego|moto|nighthawk|verizon jetpack)", re.I)


def readVerizonDevices(sFolder):
    """The per-handset half of Verizon's knowledge base."""
    return [tArticle for tArticle in readVerizon(sFolder) if c_oVerizonDevice.search(tArticle[0])]


def readVerizonService(sFolder):
    """Everything in Verizon's knowledge base that is NOT about one handset:
    plans, billing, accounts, home internet, the network, international use and
    accessibility."""
    return [tArticle for tArticle in readVerizon(sFolder) if not c_oVerizonDevice.search(tArticle[0])]


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
        sCategory = c_sMiscellaneous
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
        sCategory = lCrumbs[0] if lCrumbs else c_sMiscellaneous
        # Google leaves 53 of these articles with no topic crumb at all, which
        # buries Lookout, Live Transcribe, braille and the display settings in
        # Miscellaneous. Where the trail says nothing, the article's own title
        # does: it names its subject in its first words.
        if sCategory == c_sMiscellaneous:
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


c_lMpvProgrammer = ["lua scripting", "javascript", "json ipc", "c plugins",
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
    if any(sName in sWhole for sName in c_lMpvProgrammer): return True
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
        sCategory = c_sMiscellaneous
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
        sCategory = c_sMiscellaneous
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
        sCategory = c_sMiscellaneous
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
        sBody = (findBalanced(sMarkup, r'<section[^>]*class="[^"]*section__article', "section")
                 or findBalanced(sMarkup, r"<main[^>]*>", "main"))
        if not sBody: continue
        lBody = toMarkdown(sBody, 0)
        if len(" ".join(lBody).split()) < 25: continue
        lArticles.append((sCategory, sTitle, lBody))
    return lArticles


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
        sCategory = c_sMiscellaneous
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
        sCategory = lCrumbs[0] if lCrumbs else c_sMiscellaneous
        # Google leaves 53 of these articles with no topic crumb at all, which
        # buries Lookout, Live Transcribe, braille and the display settings in
        # Miscellaneous. Where the trail says nothing, the article's own title
        # does: it names its subject in its first words.
        if sCategory == c_sMiscellaneous:
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
        sCategory = sCategoryRule(sName, sTitle) if sCategoryRule else c_sMiscellaneous
        lArticles.append((sCategory, sTitle, lBody))
    return lArticles


def readQuarto(sFolder):
    """Quarto's documentation groups itself by the first folder of its address —
    guide, computations, authoring, output-formats, dashboards and the rest."""
    def category(sName, sTitle):
        oSection = re.search(r"quarto\.org_docs_([a-z0-9-]+)", sName)
        if not oSection: return c_sMiscellaneous
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
        return c_sMiscellaneous
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
        sCategory = c_sMiscellaneous
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
        sCategory = c_sMiscellaneous
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
        sCategory = c_sMiscellaneous
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
        sCategory = lCrumbs[-1] if lCrumbs else c_sMiscellaneous
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
        sCategory = lCrumbs[-1] if lCrumbs else c_sMiscellaneous
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
        sCategory = c_sMiscellaneous
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
        sCategory = dFolders.get(oId.group(1) if oId else "", c_sMiscellaneous)
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
        sCategory = lCrumbs[-1] if lCrumbs else c_sMiscellaneous
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
    sCategory = c_sMiscellaneous
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
        sCategory = lNames[iBlock] if iBlock < len(lNames) else c_sMiscellaneous
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
    return [((sCategory if dCounts[sCategory] >= c_iMinCategory else c_sMiscellaneous), sTitle, lBody)
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
c_dDeveloperCategories = {
    "Handshake.md": ["API"],
    "Reddit.md": ["Developer Platform & Data API Usage"],
    "Todoist.md": ["Developers"],
}


def dropDeveloperMaterial(lArticles, sOutputPath):
    """Removes the developer categories named for this guide, and says how many."""
    lNames = c_dDeveloperCategories.get(os.path.basename(sOutputPath), [])
    if not lNames: return lArticles
    lKept = [tArticle for tArticle in lArticles if tArticle[0].strip() not in lNames]
    logging.info("%s: %d articles left out as developer material (%s)",
                 os.path.basename(sOutputPath), len(lArticles) - len(lKept), ", ".join(lNames))
    return lKept


def buildGuide(sProduct, sTitle, sPreamble, lArticles, sOutputPath):
    """Writes one guide and returns its text."""
    # Disambiguate BEFORE folding small categories, not after: folding moves
    # articles into Miscellaneous, and two articles that were distinguished by
    # their categories then arrive in the same one carrying the same title.
    lArticles = foldSmallCategories(disambiguate(dedupe(dropDeveloperMaterial(
        [tArticle for tArticle in lArticles if tArticle[2]], sOutputPath))))
    dCategories = {}
    for sCategory, sArticleTitle, lBody in lArticles: dCategories.setdefault(sCategory, []).append((sArticleTitle, lBody))
    lLines = ["---", 'title: "' + sTitle + '"', "lang: en", "---", "", "# " + sTitle, "", sPreamble, "", "## Contents", ""]
    for sCategory in sorted(dCategories, key=sortKeyCategory):
        lLines.append("- " + sCategory)
        for sArticleTitle, lBody in sorted(dCategories[sCategory], key=lambda tItem: sortKeyTitle(tItem[0])):
            lLines.append("    - [" + sArticleTitle + "](#" + makeAnchor(sArticleTitle) + ")")
    lLines.append("")
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
            lLines.extend(lClean)
            lLines.append("")
    lFlat = []
    for sLine in dropLitter(lLines): lFlat.extend(sLine.replace("\r\n", "\n").split("\n"))
    sText = c_sNewLine.join(lFlat) + c_sNewLine
    fHandle = io.open(sOutputPath, "w", encoding=c_sEncoding, newline="")
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
    for sLine in sText.split(c_sNewLine):
        oFence = re.match(r"\s*(`{3,})", sLine)
        if oFence:
            iRun = len(oFence.group(1))
            if not iFence: iFence = iRun
            elif iRun >= iFence: iFence = 0
            continue
        if not iFence: lOutside.append(sLine)
    sBare = c_sNewLine.join(lOutside)
    iArticles = len(re.findall(r"^### ", sBare, re.M))
    sContents = sBare.split("## Contents", 1)[-1].split(c_sNewLine + "## ", 1)[0]
    iContents = len(re.findall(r"^    - \[", sContents, re.M))
    if iArticles != iContents: lFailures.append("contents lists %d entries against %d articles" % (iContents, iArticles))
    if iArticles < 3: lFailures.append("fewer than three articles")
    lBodies = [s for s in re.split(r"(?m)^### .+$", sBare)[1:]]
    lWordCounts = sorted(len(s.split()) for s in lBodies)
    iMedian = lWordCounts[len(lWordCounts) // 2] if lWordCounts else 0
    if iMedian < 25: lFailures.append("the median article holds only %d words" % iMedian)
    bInCode = False
    lBare = []
    for sLine in sText.split(c_sNewLine):
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


def main():
    """Builds the magazine guides and reports what passed."""
    sScriptDir = os.path.dirname(os.path.abspath(__file__))
    logging.basicConfig(filename=os.path.join(sScriptDir, "buildMagazines.log"), filemode="w", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    sParent = sys.argv[1] if len(sys.argv) > 1 else "."
    sOutput = sys.argv[2] if len(sys.argv) > 2 else "."
    logging.info("buildMagazines.py version 1; script %s", os.path.abspath(__file__))
    logging.info("Python %s on %s; working directory %s", platform.python_version(), platform.platform(), os.getcwd())
    logging.info("harvests under %s; output to %s", os.path.abspath(sParent), os.path.abspath(sOutput))
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
         "This guide holds Google's own help for Gmail, gathered on 9 September 2026. The categories are Google's own topics, taken from the trail above each article.\r\n\r\nGoogle writes the same article once for each device it runs on, so where an article differs by platform the heading says which one it is for — Computer, Android, or iPhone and iPad. A reader on a phone can go straight to the version that matches."),
        ("Google Meet", "GoogleMeetHelp", readGoogleMeet, "GoogleMeet.md", "Google Meet help",
         "This guide holds Google's own help for Meet, gathered on 20 August 2026. The categories are Google's own topics, taken from the trail above each article.\r\n\r\nGoogle writes the same article once for each device it runs on, so where an article differs by platform the heading says which one it is for — Computer, Android, or iPhone and iPad. A reader on a phone can go straight to the version that matches."),
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
    ]
    lResults = []
    for sProduct, sFolder, functionRead, sFile, sTitle, sPreamble in lPlan:
        sHarvest = os.path.join(sParent, sFolder)
        if not os.path.isdir(sHarvest):
            logging.error("no harvest folder at %s", sHarvest)
            continue
        try:
            lArticles = functionRead(sHarvest)
            sPath = os.path.join(sOutput, sFile)
            sText = buildGuide(sProduct, sTitle, sPreamble, lArticles, sPath)
            lFailures = runGates(sProduct, sPath, sText)
            lResults.append((sProduct, len(re.findall(r"^### ", sText, re.M)), len(sText.split()), len(lFailures)))
        except Exception as oError:
            logging.exception("%s failed to build: %s", sProduct, oError)
            lResults.append((sProduct, 0, 0, -1))
    for sProduct, iArticles, iWords, iFailures in lResults:
        print("%-20s %4d articles %8d words %s" % (sProduct, iArticles, iWords,
                                                   "ALL CLEAN" if iFailures == 0 else "%d gate failures" % iFailures))
    print("Log: " + os.path.join(sScriptDir, "buildMagazines.log"))
    return 0


if __name__ == "__main__": sys.exit(main())
