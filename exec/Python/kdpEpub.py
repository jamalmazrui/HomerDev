r"""kdpEpub.py -- gives an EPUB every table of contents and guide item Kindle Direct Publishing asks for, and checks them.
Part of the HomerDev kit (1.61.0), shared by every book project: MyBooks' buildBooks and Blind Vibe Coding's build.py.

    import kdpEpub
    lDone = kdpEpub.applyToFile(sEpub)      # fixes the EPUB in place; returns what it did, for a log
    lProblems = kdpEpub.tocProblems(sEpub)  # empty when every requirement is met

kdpNavigation(dData, lNames) does the same on an EPUB already read into memory ({name: bytes} and the names in order),
for a build that rewrites the package itself.
"""

import posixpath, re, urllib.parse, zipfile


def plural(iCount, sOne, sMany=""):
    """1 entry, 2 entries."""
    return str(iCount) + " " + (sOne if iCount == 1 else (sMany or sOne + "s"))


# ---------------------------------------------------------------- what KDP asks
# WHAT KDP ASKS (its Kindle Publishing Guidelines, Navigation Guidelines, read 7 October 2026). Two tables of contents and the
# items that point to one of them:
#   - the LOGICAL ToC, "Kindle Interactive TOC": a toc nav element (EPUB 3) or an NCX (EPUB 2), shown in the Kindle menu;
#     a missing one is a quality error. Pandoc writes both, nav.xhtml and toc.ncx.
#   - the HTML ToC, "TOC page": a page at the beginning of the book linking to each chapter -- links, never a table, no page
#     numbers, in order, nested, and for a bundle of several books one overarching ToC at the start. It must be a separate
#     document from the toc nav.
#   - GUIDE ITEMS for the cover and the ToC, as a landmarks nav (EPUB 3) and a <guide> (EPUB 2), pointing at the HTML ToC:
#     without them the Kindle menu shows those items greyed out.
# Pandoc's own guide pointed at nav.xhtml, which is not in the reading order, and its landmarks named only the title page;
# a book whose manuscript had no [TOC] marker had no HTML ToC at all. kdpNavigation makes all of it, the same way for every
# book, from the toc nav itself, so the two tables of contents always agree.

def epubPaths(dData, lNames):
    """(OPF path, OPF text, its folder, {manifest id: (href from the OPF folder, properties)}, [spine hrefs in order])."""
    sOpfPath = next(s for s in lNames if s.lower().endswith(".opf"))
    sOpf = dData[sOpfPath].decode("utf-8")
    sBase = posixpath.dirname(sOpfPath)
    dItems = {}
    for oItem in re.finditer(r"<item\b[^>]*>", sOpf):
        sTag = oItem.group(0)
        sId, sHref = re.search(r'\bid="([^"]+)"', sTag), re.search(r'\bhref="([^"]+)"', sTag)
        if sId and sHref: dItems[sId.group(1)] = (urllib.parse.unquote(sHref.group(1)), (re.search(r'\bproperties="([^"]*)"', sTag) or [None, ""])[1])
    lSpine = [dItems[sRef][0] for sRef in re.findall(r'<itemref\b[^>]*\bidref="([^"]+)"', sOpf) if sRef in dItems]
    return sOpfPath, sOpf, sBase, dItems, lSpine


def existingListEnd(sText, iAfter):
    """Where whatever follows a contents heading ends, so it can be replaced: a [TOC] marker paragraph, or a whole list,
    however deeply nested, found by counting its opening and closing list tags -- not the first closing tag, which in a
    nested list is an inner one (7 October 2026: a second pass over Blind Vibe Coding's EPUB, already given its nested
    contents, left stray closing tags and a page EPUBCheck refused as not well-formed). Returns iAfter when nothing is
    there to replace, so the module may run any number of times over the same EPUB."""
    oSpace = re.compile(r"\s*").match(sText, iAfter)
    iAt = oSpace.end()
    oMarker = re.compile(r"<p>\s*\[TOC\]\s*</p>").match(sText, iAt)
    if oMarker: return oMarker.end()
    if not re.compile(r"<(ol|ul)\b").match(sText, iAt): return iAfter
    iDepth = 0
    for oTag in re.compile(r"<(/?)(ol|ul)\b[^>]*>").finditer(sText, iAt):
        iDepth += -1 if oTag.group(1) else 1
        if iDepth == 0: return oTag.end()
    return iAfter


def tocListFrom(sNavOl, sNavDir, sPageDir, sSkip):
    """The toc nav's list as the HTML ToC page's list: links rewritten to be relative to that page, ids dropped, entries for the
    page itself left out, and list markers turned off, so it reads as a nested list of links."""
    def relink(oMatch):
        sHref = oMatch.group(1)
        sFile, _, sAnchor = sHref.partition("#")
        sFull = posixpath.normpath(posixpath.join(sNavDir, sFile)) if sFile else ""
        sRel = posixpath.relpath(sFull, sPageDir) if sFull else ""
        return 'href="' + sRel + ("#" + sAnchor if sAnchor else "") + '"'
    sList = re.sub(r'href="([^"]+)"', relink, sNavOl)
    sList = re.sub(r'\s(id|epub:type)="[^"]*"', "", sList)
    sList = re.sub(r'<li>\s*<a href="(' + re.escape(sSkip) + r'|[^"]*title_page\.xhtml)(#[^"]*)?"[^>]*>[^<]*</a>\s*</li>', "", sList)
    sList = re.sub(r"<ol>", '<ol style="list-style-type: none;">', sList)
    return sList


def kdpNavigation(dData, lNames):
    """Gives the EPUB every table of contents and guide item KDP asks for; returns a list of what it did, for the log."""
    lDone = []
    sOpfPath, sOpf, sBase, dItems, lSpine = epubPaths(dData, lNames)
    sNavHref = next((h for h, sProps in dItems.values() if "nav" in sProps.split()), "")
    if not sNavHref: return ["no navigation document; nothing done"]
    sNavPath = posixpath.join(sBase, sNavHref)
    sNav = dData[sNavPath].decode("utf-8")
    oToc = re.search(r'<nav[^>]*epub:type="toc"[^>]*>(.*?)</nav>', sNav, re.S)
    iStart = oToc.group(1).find("<ol") if oToc else -1
    if iStart < 0: return ["no toc nav with a list; nothing done"]
    sNavOl = oToc.group(1)[iStart:oToc.group(1).rfind("</ol>") + 5]
    sNavOl = re.sub(r"<ol\b[^>]*>", "<ol>", sNavOl)
    # Pandoc puts a heading's anchor on the section around it, <section id="table-of-contents"><h1>...</h1>; older output
    # puts it on the heading. Either gives the anchor.
    oHeading = re.compile(r'<section\b[^>]*\bid="([^"]+)"[^>]*>\s*<h[1-6][^>]*>\s*(?:Table of Contents|Contents)\s*</h[1-6]>|<h[1-6][^>]*\bid="([^"]+)"[^>]*>\s*(?:Table of Contents|Contents)\s*</h[1-6]>', re.I)
    sTocHref, sTocAnchor = "", ""
    for sHref in lSpine[:8]:
        if sHref == sNavHref or not sHref.endswith(".xhtml"): continue
        sText = dData[posixpath.join(sBase, sHref)].decode("utf-8")
        oFound = oHeading.search(sText)
        if not oFound: continue
        sTocHref, sTocAnchor = sHref, oFound.group(1) or oFound.group(2)
        sList = tocListFrom(sNavOl, posixpath.dirname(sNavHref), posixpath.dirname(sHref), posixpath.basename(sHref))
        iAfter = oFound.end()
        iEnd = existingListEnd(sText, iAfter)
        sText = sText[:iAfter] + "\n" + sList + sText[iEnd:]
        dData[posixpath.join(sBase, sHref)] = sText.encode("utf-8")
        lDone.append("HTML ToC: the book's own contents page, " + sHref + ", now lists the logical ToC's entries")
        break
    if not sTocHref:
        sTemplate = next((dData[posixpath.join(sBase, h)].decode("utf-8") for h in lSpine if h.endswith(".xhtml") and h != sNavHref and "title_page" not in h), "")
        oHead = re.search(r"^(.*?<body[^>]*>)", sTemplate, re.S)
        sHead = re.sub(r"<title>.*?</title>", "<title>Table of Contents</title>", oHead.group(1), flags=re.S) if oHead else ""
        sHead = re.sub(r'<body[^>]*>', '<body epub:type="frontmatter">', sHead)
        sDir = posixpath.dirname(next((h for h in lSpine if h.endswith(".xhtml") and h != sNavHref), "text/x.xhtml"))
        sTocHref, sTocAnchor = posixpath.join(sDir, "kdp_toc.xhtml"), "table-of-contents"
        sList = tocListFrom(sNavOl, posixpath.dirname(sNavHref), sDir, "kdp_toc.xhtml")
        dData[posixpath.join(sBase, sTocHref)] = (sHead + '\n<section id="table-of-contents" epub:type="toc">\n<h1>Table of Contents</h1>\n' + sList + "\n</section>\n</body>\n</html>\n").encode("utf-8")
        lNames.append(posixpath.join(sBase, sTocHref))
        sOpf = re.sub(r"(\s*</manifest>)", '\n    <item id="kdp_toc" href="' + sTocHref + '" media-type="application/xhtml+xml" />\\1', sOpf, count=1)
        sTitleId = next((i for i, (h, p) in dItems.items() if "title_page" in h), "")
        if sTitleId and re.search(r'<itemref idref="' + re.escape(sTitleId) + r'"[^>]*/>', sOpf):
            sOpf = re.sub(r'(<itemref idref="' + re.escape(sTitleId) + r'"[^>]*/>)', '\\1\n    <itemref idref="kdp_toc" />', sOpf, count=1)
        else:
            sOpf = re.sub(r"(<spine\b[^>]*>)", '\\1\n    <itemref idref="kdp_toc" />', sOpf, count=1)
        lSpine = epubPaths({sOpfPath: sOpf.encode("utf-8"), **{k: v for k, v in dData.items() if k != sOpfPath}}, lNames)[4]
        lDone.append("HTML ToC: none in the book, so " + sTocHref + " was made after the title page from the logical ToC")
    # The toc nav leaves the reading order: the HTML ToC page is the visible contents page, and a second one right after it,
    # Pandoc's, would repeat it. It stays in the manifest, where EPUB 3 requires it, and in the Kindle menu.
    sNavId = next((i for i, (h, sProps) in dItems.items() if h == sNavHref), "")
    if sNavId and re.search(r'<itemref\s+idref="' + re.escape(sNavId) + r'"[^>]*/>', sOpf):
        sOpf = re.sub(r'\s*<itemref\s+idref="' + re.escape(sNavId) + r'"[^>]*/>', "", sOpf, count=1)
        lSpine = [h for h in lSpine if h != sNavHref]
        lDone.append("the toc nav left the reading order, so the contents page is not shown twice")
    sCover = next((h for h in lSpine if re.search(r"(^|/)cover\.xhtml$", h)), "")
    sTitle = next((h for h in lSpine if "title_page" in h), "")
    iToc = lSpine.index(sTocHref) if sTocHref in lSpine else -1
    sBody = lSpine[iToc + 1] if 0 <= iToc < len(lSpine) - 1 else ""
    # A build that chose its own start of content (Blind Vibe Coding skips its front matter) keeps that choice when it
    # reaches a page in the reading order after the table of contents.
    oOldBody = re.search(r'<a[^>]*href="([^"#]+)[^"]*"[^>]*epub:type="bodymatter"|<a[^>]*epub:type="bodymatter"[^>]*href="([^"#]+)', sNav)
    if oOldBody:
        sOld = posixpath.normpath(posixpath.join(posixpath.dirname(sNavHref), oOldBody.group(1) or oOldBody.group(2)))
        if sOld in lSpine and lSpine.index(sOld) > iToc: sBody = sOld
    def fromNav(sHref): return posixpath.relpath(sHref, posixpath.dirname(sNavHref)) if posixpath.dirname(sNavHref) else sHref
    lMarks = []
    if sCover: lMarks.append('<li><a href="' + fromNav(sCover) + '" epub:type="cover">Cover</a></li>')
    if sTitle: lMarks.append('<li><a href="' + fromNav(sTitle) + '" epub:type="titlepage">Title Page</a></li>')
    lMarks.append('<li><a href="' + fromNav(sTocHref) + "#" + sTocAnchor + '" epub:type="toc">Table of Contents</a></li>')
    if sBody: lMarks.append('<li><a href="' + fromNav(sBody) + '" epub:type="bodymatter">Start of Content</a></li>')
    sLandmarks = '<nav epub:type="landmarks" id="landmarks" hidden="hidden">\n  <ol>\n    ' + "\n    ".join(lMarks) + "\n  </ol>\n</nav>"
    if re.search(r'<nav[^>]*epub:type="landmarks".*?</nav>', sNav, re.S): sNav = re.sub(r'<nav[^>]*epub:type="landmarks".*?</nav>', lambda o: sLandmarks, sNav, count=1, flags=re.S)
    else: sNav = sNav.replace("</body>", sLandmarks + "\n</body>", 1)
    dData[sNavPath] = sNav.encode("utf-8")
    lGuide = ([('cover', 'Cover', sCover)] if sCover else []) + [("toc", "Table of Contents", sTocHref + "#" + sTocAnchor)]
    sGuide = "<guide>\n    " + "\n    ".join('<reference type="' + t + '" title="' + n + '" href="' + h + '" />' for t, n, h in lGuide) + "\n  </guide>"
    if "<guide>" in sOpf: sOpf = re.sub(r"<guide>.*?</guide>", lambda o: sGuide, sOpf, count=1, flags=re.S)
    else: sOpf = sOpf.replace("</package>", "  " + sGuide + "\n</package>", 1)
    dData[sOpfPath] = sOpf.encode("utf-8")
    lDone.append("landmarks and guide: " + ", ".join(t for t, n, h in lGuide) + (", titlepage" if sTitle else "") + (", bodymatter" if sBody else "") + "; ToC items point at " + sTocHref)
    return lDone


def applyToFile(sEpub):
    """kdpNavigation on an EPUB file, written back with mimetype first and uncompressed, as the EPUB rules require."""
    with zipfile.ZipFile(sEpub) as oIn:
        lNames = oIn.namelist()
        dData = {sName: oIn.read(sName) for sName in lNames}
    lDone = kdpNavigation(dData, lNames)
    sTemp = sEpub + ".tmp"
    with zipfile.ZipFile(sTemp, "w") as oOut:
        oOut.writestr(zipfile.ZipInfo("mimetype"), b"application/epub+zip", compress_type=zipfile.ZIP_STORED)
        for sName in lNames:
            if sName != "mimetype": oOut.writestr(sName, dData[sName], compress_type=zipfile.ZIP_DEFLATED)
    import os
    os.replace(sTemp, sEpub)
    return lDone


def tocProblems(sEpub):
    """Every KDP table-of-contents requirement, checked in the finished EPUB; returns the problems, empty when all are met:
    a logical ToC in a toc nav and an NCX, both with entries that reach their targets; an HTML ToC page, separate from the nav,
    in the first pages of the reading order, made of links that reach their targets, with no table; and landmarks and guide
    items pointing at that page."""
    lProblems = []
    with zipfile.ZipFile(sEpub) as oZip:
        lNames = oZip.namelist()
        dData = {s: oZip.read(s) for s in lNames if s.lower().endswith((".opf", ".xhtml", ".ncx"))}
    sOpfPath, sOpf, sBase, dItems, lSpine = epubPaths(dData, lNames)
    dIds = {sPath: set(re.findall(r'\bid="([^"]+)"', v.decode("utf-8", "replace"))) for sPath, v in dData.items() if sPath.endswith(".xhtml")}
    def reaches(sFrom, sHref):
        sFile, _, sAnchor = urllib.parse.unquote(sHref).partition("#")
        sTarget = posixpath.normpath(posixpath.join(posixpath.dirname(sFrom), sFile)) if sFile else sFrom
        return sTarget in dData and (not sAnchor or sAnchor in dIds.get(sTarget, set()))
    sNavHref = next((h for h, sProps in dItems.values() if "nav" in sProps.split()), "")
    sNavPath = posixpath.join(sBase, sNavHref)
    sNav = dData.get(sNavPath, b"").decode("utf-8", "replace")
    oToc = re.search(r'<nav[^>]*epub:type="toc"[^>]*>(.*?)</nav>', sNav, re.S)
    lTocLinks = re.findall(r'href="([^"]+)"', oToc.group(1)) if oToc else []
    if not lTocLinks: lProblems.append("No logical table of contents: the navigation document has no toc nav with entries (KDP: Kindle Interactive TOC, required).")
    lMissed = [h for h in lTocLinks if not reaches(sNavPath, h)]
    if lMissed: lProblems.append(plural(len(lMissed), "logical table of contents entry", "logical table of contents entries") + " lead nowhere, such as " + lMissed[0] + ".")
    sNcxHref = next((h for h, sProps in dItems.values() if h.endswith(".ncx")), "")
    sNcx = dData.get(posixpath.join(sBase, sNcxHref), b"").decode("utf-8", "replace") if sNcxHref else ""
    if not re.search(r"<navPoint\b", sNcx): lProblems.append("No NCX with entries, the older form of the logical table of contents that some Kindle readers use.")
    oGuide = re.search(r'<reference[^>]*type="toc"[^>]*href="([^"]+)"', sOpf)
    oMark = re.search(r'<a[^>]*href="([^"]+)"[^>]*epub:type="toc"|<a[^>]*epub:type="toc"[^>]*href="([^"]+)"', re.search(r'<nav[^>]*epub:type="landmarks".*?</nav>', sNav, re.S).group(0) if re.search(r'<nav[^>]*epub:type="landmarks"', sNav) else "")
    sGuideFile = urllib.parse.unquote(oGuide.group(1)).partition("#")[0] if oGuide else ""
    sMarkFile = posixpath.normpath(posixpath.join(posixpath.dirname(sNavHref), urllib.parse.unquote(oMark.group(1) or oMark.group(2)).partition("#")[0])) if oMark else ""
    if not oGuide: lProblems.append("No guide item for the table of contents in the package file, so the Kindle menu's Table of Contents would be greyed out.")
    if not oMark: lProblems.append("No landmarks entry for the table of contents in the navigation document.")
    if sGuideFile == sNavHref or sMarkFile == sNavHref: lProblems.append("The table of contents items point at the navigation document; KDP wants them on the HTML table of contents page, a separate page.")
    if sGuideFile and sMarkFile and sGuideFile != sMarkFile: lProblems.append("The guide item and the landmarks entry point at different tables of contents: " + sGuideFile + " and " + sMarkFile + ".")
    if sGuideFile and sGuideFile != sNavHref:
        if sGuideFile not in lSpine: lProblems.append("The HTML table of contents page, " + sGuideFile + ", is not in the reading order.")
        elif lSpine.index(sGuideFile) > 7: lProblems.append("The HTML table of contents page comes " + str(lSpine.index(sGuideFile) + 1) + "th in the reading order; KDP wants it at the beginning.")
        sPage = posixpath.join(sBase, sGuideFile)
        sText = dData.get(sPage, b"").decode("utf-8", "replace")
        lLinks = re.findall(r'<a\b[^>]*href="([^"#][^"]*#?[^"]*|#[^"]+)"', sText)
        lInternal = [h for h in lLinks if not re.match(r"^[a-z]+:", h)]
        if not lInternal: lProblems.append("The HTML table of contents page has no links; KDP requires its entries to be links.")
        if re.search(r"<table\b", sText): lProblems.append("The HTML table of contents page uses a table; KDP forbids tables for a table of contents.")
        lMissed = [h for h in lInternal if not reaches(sPage, h)]
        if lMissed: lProblems.append(plural(len(lMissed), "HTML table of contents link") + " lead nowhere, such as " + lMissed[0] + ".")
    return lProblems
