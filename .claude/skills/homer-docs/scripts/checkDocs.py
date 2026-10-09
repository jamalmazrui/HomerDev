"""
checkDocs.py -- check a Homer project's documents before a release.

Usage:
    python checkDocs.py <project-folder> [--app <Name>]

The app's name is the folder's name unless --app gives it. Reports, per
document: a document missing from the Homer set, a .md with no .htm or with an
.htm older than it, not exactly one H1, a skipped heading level, a bare URL,
link text that does not say where it goes ("click here", "read more"), an
image with no text alternative, a long document with no contents list, and the reading grade (Flesch-Kincaid),
flagged above grade 9 for the documents a user reads (ReadMe, the guide,
Announce). Developer and History may go further, so their grade is shown but
not flagged; Hotkeys is a list of key names, which no reading formula fits.

Exit code 0 with no findings, 1 with findings, 2 when the folder is missing.
"""

import os, re, sys

c_iContentsLines = 150  # a document this long needs a contents list
c_iContentsHeadings = 5  # ...when it also has this many H2 sections
c_nMaxGrade = 9.0
c_lsVagueLinks = ["click here", "here", "learn more", "link", "more", "read more", "this", "this link"]
c_lsHelpSet = ["Announce.md", "Developer.md", "History.md", "Hotkeys.md"]
c_lsTopSet = ["License.md", "ReadMe.md"]


def readText(sPath):
    binData = open(sPath, "rb").read()
    for sEncoding in ("utf-8-sig", "cp1252"):
        try:
            return binData.decode(sEncoding)
        except UnicodeDecodeError:
            continue
    return binData.decode("utf-8", "replace")


def proseOf(sText):
    """The running prose: no front matter, code, headings, tables or link targets."""
    sText = re.sub(r"(?s)\A---\n.*?\n---\n", "", sText)
    sText = re.sub(r"(?ms)^```.*?^```", "", sText)
    lsLines = []
    for sLine in sText.split("\n"):
        if sLine.startswith(("    ", "\t", "#", "|")): continue
        sLine = re.sub(r"^\s*([-*+]|\d+\.)\s+", "", sLine)
        sLine = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", sLine)
        sLine = re.sub(r"`[^`]*`", "code", sLine)
        sLine = re.sub(r"https?://\S+", "link", sLine)
        lsLines.append(sLine)
    return "\n".join(lsLines)


def syllables(sWord):
    sWord = sWord.lower()
    iCount = len(re.findall(r"[aeiouy]+", sWord))
    if sWord.endswith("e") and not sWord.endswith(("le", "ee")) and iCount > 1: iCount -= 1
    return max(iCount, 1)


def readingGrade(sText):
    """Flesch-Kincaid grade of the prose, or None when there is too little."""
    sProse = proseOf(sText)
    lsSentences = [s for s in re.split(r"[.!?]+(?:\s|$)|\n\s*\n", sProse) if re.search(r"[A-Za-z]", s)]
    lsWords = re.findall(r"[A-Za-z][A-Za-z'-]*", sProse)
    if len(lsWords) < 100 or not lsSentences: return None
    iSyllables = sum(syllables(s) for s in lsWords)
    return 0.39 * len(lsWords) / len(lsSentences) + 11.8 * iSyllables / len(lsWords) - 15.59


def checkDocument(sPath, bUserDocument):
    lsFindings = []
    sText = readText(sPath).replace("\r\n", "\n")
    sBody = re.sub(r"(?ms)^```.*?^```", "", sText)
    lsHeadings = [(len(o.group(1)), o.group(2)) for o in re.finditer(r"(?m)^(#{1,6}) (.+)$", sBody)]
    iH1 = sum(1 for iLevel, s in lsHeadings if iLevel == 1)
    bTitle = bool(re.match(r"(?s)\A\ufeff?---\n.*?^title:", sText, re.M))
    if iH1 > 1: lsFindings.append("%d H1 headings; a document has one, its title" % iH1)
    if iH1 == 0 and not bTitle: lsFindings.append("no H1 heading and no title in front matter")
    # A SUBTITLE IS NOT A HEADING (1.65.5): three Announce documents repeated their front matter's subtitle as a
    # heading under the title, so the page said it twice, once as a heading that skipped a level.
    oSubtitle = re.search(r'(?m)^subtitle:\s*"?(.+?)"?\s*$', (re.match(r"(?s)\A\ufeff?---\n(.*?)\n---", sText) or re.match("", "")).group(0))
    if oSubtitle:
        for iLevel, sHeading in lsHeadings:
            if sHeading.strip() == oSubtitle.group(1).strip():
                lsFindings.append("the subtitle is repeated as an H%d heading; the front matter already shows it" % iLevel)
    iPrevious = 1
    for iLevel, sHeading in lsHeadings:
        if iLevel > iPrevious + 1:
            lsFindings.append("heading level skipped before \"%s\" (H%d after H%d)" % (sHeading.strip()[:60], iLevel, iPrevious))
        iPrevious = iLevel
    # A reference-style link definition ("[name]: https://...") is not bare.
    sLinks = re.sub(r"(?m)^\s*\[[^\]]+\]:\s+\S+.*$", "", sBody)
    for sUrl in re.findall(r"(?<![(<\"'])\bhttps?://[^\s)>\]]+", sLinks):
        lsFindings.append("bare URL: %s" % sUrl[:80])
    # LINK TEXT THAT SAYS WHERE IT GOES (1.50.1). A screen reader user often
    # lists a page's links out of context, where "click here" says nothing.
    for sLinkText in re.findall(r"(?<!!)\[([^\]\n]+)\]\s*[\[(]", sBody):
        if sLinkText.strip().lower().strip(".") in c_lsVagueLinks:
            lsFindings.append("vague link text: \"%s\"; say where the link goes" % sLinkText.strip())
    # AN IMAGE SAYS WHAT IT SHOWS. Empty alternative text leaves a picture
    # silent for a screen reader user.
    for sImage in re.findall(r"!\[\s*\]\(([^)\s]+)", sBody):
        lsFindings.append("image with no text alternative: %s" % sImage[:80])
    iH2 = sum(1 for iLevel, s in lsHeadings if iLevel == 2)
    if len(sText.split("\n")) > c_iContentsLines and iH2 >= c_iContentsHeadings and not re.search(r"(?mi)^#+ contents|^\[TOC\]|^## Table of Contents", sText):
        lsFindings.append("%d lines and %d sections with no contents list" % (len(sText.split("\n")), iH2))
    nGrade = readingGrade(sText)
    sGrade = "grade n/a" if nGrade is None else "grade %.1f" % nGrade
    if bUserDocument and nGrade is not None and nGrade > c_nMaxGrade:
        lsFindings.append("reading grade %.1f, above %d" % (nGrade, c_nMaxGrade))
    sHtm = sPath[:-3] + ".htm"
    if not os.path.isfile(sHtm): lsFindings.append("no .htm beside it")
    elif os.path.getmtime(sHtm) + 1 < os.path.getmtime(sPath): lsFindings.append(".htm is older than the .md; rebuild it")
    return sGrade, lsFindings


def main():
    lsArgs = sys.argv[1:]
    if not lsArgs:
        print(__doc__.strip())
        return 2
    sRoot = os.path.abspath(lsArgs[0])
    if not os.path.isdir(sRoot):
        print("Not a folder: " + sRoot)
        return 2
    sApp = lsArgs[lsArgs.index("--app") + 1] if "--app" in lsArgs else os.path.basename(sRoot.rstrip("\\/"))
    sHelp = os.path.join(sRoot, "help")
    lsExpected = [os.path.join(sRoot, s) for s in c_lsTopSet] + [os.path.join(sHelp, s) for s in c_lsHelpSet + [sApp + ".md"]]
    iFindings = 0
    for sPath in lsExpected:
        if not os.path.isfile(sPath):
            print("MISSING %s" % os.path.relpath(sPath, sRoot))
            iFindings += 1
    lsDocuments = [os.path.join(sRoot, s) for s in sorted(os.listdir(sRoot), key=str.lower) if s.lower().endswith(".md")]
    if os.path.isdir(sHelp):
        lsDocuments += [os.path.join(sHelp, s) for s in sorted(os.listdir(sHelp), key=str.lower) if s.lower().endswith(".md")]
    lsUser = [s.lower() for s in ("ReadMe.md", sApp + ".md", "Announce.md")]
    for sPath in lsDocuments:
        sGrade, lsFindings = checkDocument(sPath, os.path.basename(sPath).lower() in lsUser)
        print("%s  %s%s" % (os.path.relpath(sPath, sRoot), sGrade, "" if lsFindings else "  ok"))
        for sFinding in lsFindings: print("  " + sFinding)
        iFindings += len(lsFindings)
    print("%d finding%s in %d document%s." % (iFindings, "" if iFindings == 1 else "s",
                                             len(lsDocuments), "" if len(lsDocuments) == 1 else "s"))
    return 1 if iFindings else 0


if __name__ == "__main__":
    sys.exit(main())
