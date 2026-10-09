"""cleanFeedback.py version 1

Removes the "Was this article helpful? Yes No" widgets, and their cousins from
other help platforms, from the guides in a folder.

WHAT IT REMOVES, AND WHY THAT LIST AND NOT A PATTERN. Every phrase below is a
FEEDBACK WIDGET PUT THERE BY A PUBLISHING PLATFORM, named by platform so the
list can be audited and argued with:

  - Zendesk           Was this article helpful? / Have more questions? /
                      Submit a request / Return to top / N out of M found this helpful
  - Intercom          Did this answer your question? / Powered by Intercom /
                      We run on Fin (and the emoji names Disappointed, Neutral, Smiley)
  - Google            Was this helpful? / How can we improve it? / Need more help? /
                      Send feedback / Try these next steps
  - Microsoft         Was this information helpful? / Thank you! Any more feedback? /
                      How satisfied are you with this reply?
  - Meta              Was this article helpful? (published as a HEADING, which is
                      why the builder's no-heading rule preserved it)
  - Freshdesk         Did you find it helpful?
  - Document360,      Was this article helpful? / Was this page helpful? /
    GitBook, Atlassian Provide feedback about this article

ANSWERS ARE ONLY REMOVED NEXT TO THEIR QUESTION. "Yes" and "No" are ordinary
English words: a line holding one of them is removed only when it stands alone
within three lines of a feedback question that was itself removed. A "Yes" in
the middle of an article is never touched.

NOTHING ELSE IS TOUCHED. Headings that are not on the list stay, prose stays,
and every removed line is written to the log exactly as it was, so anything
taken by mistake can be put back by reading the log.

RUN IT WITH NO ARGUMENTS to clean the folder it sits in. Run it with the word
report to list what it WOULD remove and change nothing.
"""

import io, logging, os, platform, re, shutil, subprocess, sys

c_iAnswerWindow = 3
c_lAnswers = ["yes", "no", "yes no", "disappointed", "neutral", "smiley",
              "still need help", "share", "thumbs up", "thumbs down"]
c_lQuestions = [
    ("Amazon", "was this information helpful"),
    ("Atlassian", "provide feedback about this article"),
    ("Document360", "was this page helpful"),
    ("Freshdesk", "did you find it helpful"),
    ("Google", "how can we improve it"),
    ("Google", "was this helpful"),
    ("Guardian", "did you find the information you need"),
    ("HelpDocs", "how did we do"),
    ("HelpDocs", "let us know how can we improve this article"),
    ("Intercom", "did this answer your question"),
    ("Microsoft", "how satisfied are you with this reply"),
    ("Microsoft", "thank you any more feedback"),
    ("Verizon", "is this bill info helpful"),
    ("Verizon", "is this helpful"),
    ("Zendesk", "was this article helpful"),
]
c_lAfterwards = [
    ("Amazon", "thanks while were unable to respond directly to your feedback"),
    ("Amazon", "thank you for your feedback"),
    ("Freshdesk", "sorry we couldnt be helpful help us improve this article with your feedback"),
    ("Freshdesk", "send feedback"),
    ("HelpDocs", "feedback sent"),
    ("HelpDocs", "sorry we couldnt be helpful"),
    ("HelpDocs", "thats great"),
    ("HelpDocs", "we appreciate your effort and will try to fix the article"),
]
c_lCounts = [r"^\d+ out of \d+ found this helpful$", r"^\d+ of \d+ people found this helpful$"]
c_sLogName = "cleanFeedback.log"


def startLog():
    sHere = os.path.dirname(os.path.abspath(__file__))
    sPath = os.path.join(sHere, c_sLogName)
    logging.basicConfig(filename=sPath, filemode="w", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s", encoding="utf-8", errors="backslashreplace")
    logging.info("cleanFeedback.py running under Python %s on %s", platform.python_version(), platform.platform())
    logging.info("script at %s, working directory %s", os.path.abspath(__file__), os.getcwd())
    logging.info("command line: %s", " ".join(sys.argv))
    logging.info("%d feedback questions and %d answer words are on the list", len(c_lQuestions), len(c_lAnswers))
    return sPath


def readText(sPath):
    binBody = io.open(sPath, "rb").read()
    for sEncoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try: return binBody.decode(sEncoding)
        except UnicodeDecodeError: continue
    return binBody.decode("utf-8", "replace")


def plainOf(sLine):
    """The line reduced to lowercase letters and spaces, with heading marks, list
    marks, emphasis and punctuation off, so a heading and a paragraph carrying
    the same words look the same to the list."""
    sText = sLine.strip().lstrip("#-*> ").strip()
    sText = re.sub(r"[*_`]", "", sText)
    return re.sub(r"[^a-z0-9 ]", "", sText.lower()).strip()


def questionFor(sLine):
    """The platform whose widget this line is, or an empty string.

    A LINE IS THE WIDGET ONLY WHEN IT IS NOTHING BUT THE WIDGET. Wikipedia's
    archived reader feedback carries lines like "Was this page helpful? Please
    change the spelling of Billy's Lakota name" — the question followed by a
    reader's own words. Matching on the opening phrase alone would have deleted
    that reader's comment, so what remains after the phrase must be empty or an
    answer word."""
    sPlain = plainOf(sLine)
    if not sPlain: return ""
    for sPlatform, sPhrase in c_lQuestions:
        if sPlain == sPhrase:
            return sPlatform
        if sPlain.startswith(sPhrase + " "):
            sRest = sPlain[len(sPhrase):].strip()
            if all(sWord in ("yes", "no") for sWord in sRest.split()):
                return sPlatform
    return ""


def afterwardsFor(sLine):
    """A line the widget prints once it has been answered, or an empty string.

    THESE MATCH THE WHOLE LINE, NEVER ITS OPENING, and never a heading or a
    contents entry. "Send feedback" is a widget's word AND the title of real
    articles — YouTube, Windows and Zoom all have headings that begin with it —
    so a rule that matched an opening deleted five article titles and a contents
    line before this was written. Only the two long, distinctive apologies are
    allowed to match an opening, because nothing else begins that way."""
    if sLine.strip().startswith("#") or sLine.strip().startswith("- ["): return ""
    sPlain = plainOf(sLine)
    if not sPlain: return ""
    for sPlatform, sPhrase in c_lAfterwards:
        if sPlain == sPhrase: return sPlatform
        if len(sPhrase) > 45 and sPlain.startswith(sPhrase): return sPlatform
    return ""


def isAnswer(sLine):
    sPlain = plainOf(sLine)
    if not sPlain: return False
    if sPlain in c_lAnswers: return True
    return any(re.match(sPattern, sPlain) for sPattern in c_lCounts)


def cleanLines(lLines, sName):
    """Returns the cleaned lines and a list of what was removed."""
    lOut, lRemoved = [], []
    iIndex = 0
    while iIndex < len(lLines):
        sLine = lLines[iIndex]
        # A count line is furniture wherever it stands: no article says "3 out of
        # 7 found this helpful" about anything but itself, and Zendesk prints it
        # ABOVE its question as often as below.
        if any(re.match(sPattern, plainOf(sLine)) for sPattern in c_lCounts):
            lRemoved.append(("Zendesk, count", sLine))
            iIndex += 1
            continue
        sAfter = afterwardsFor(sLine)
        if sAfter:
            lRemoved.append((sAfter + ", afterwards", sLine))
            iIndex += 1
            continue
        sPlatform = questionFor(sLine)
        if not sPlatform:
            lOut.append(sLine)
            iIndex += 1
            continue
        lRemoved.append((sPlatform, sLine))
        iIndex += 1
        iTaken = 0
        while iIndex < len(lLines) and iTaken < c_iAnswerWindow:
            sNext = lLines[iIndex]
            if sNext.strip() == "":
                iIndex += 1
                continue
            if isAnswer(sNext):
                lRemoved.append((sPlatform + ", answer", sNext))
                iIndex += 1
                iTaken += 1
                continue
            break
        while lOut and lOut[-1].strip() == "": lOut.pop()
        lOut.append("")
    # Removing a block can leave two blank lines where there was one.
    lTidy, sLast = [], None
    for sLine in lOut:
        if sLine.strip() == "" and sLast is not None and sLast.strip() == "": continue
        lTidy.append(sLine)
        sLast = sLine
    return lTidy, lRemoved


def finishPage(sHtmPath):
    """PANDOC'S PAGE, PUT RIGHT (8 October 2026): the Homer encoding, and a title said
    once rather than twice. Both come from homer-convert's toHomerEncoding, beside this
    skill in the kit, so the rule lives in one place; a skill uploaded on its own,
    without it, still gets the encoding."""
    # Beside this skill in the kit; or, for a copy kept in a collection's folder,
    # in the kit wherever it is: the HomerDev variable, then C:\HomerDev.
    lsPlaces = [os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "homer-convert", "scripts")]
    for sKit in (os.environ.get("HomerDev", ""), r"C:\HomerDev"):
        if sKit: lsPlaces.append(os.path.join(sKit, ".claude", "skills", "homer-convert", "scripts"))
    try:
        for sConvert in lsPlaces:
            if os.path.isfile(os.path.join(sConvert, "toHomerEncoding.py")) and sConvert not in sys.path:
                sys.path.insert(0, sConvert)
                break
        import toHomerEncoding
        return toHomerEncoding.convert(sHtmPath)
    except ImportError:
        binData = open(sHtmPath, "rb").read()
        sText = binData.decode("utf-8-sig").replace("\r\n", "\n").replace("\n", "\r\n")
        open(sHtmPath, "wb").write(b"\xef\xbb\xbf" + sText.encode("utf-8"))
        return "changed"

def rebuildPage(sMarkdownPath):
    """Rebuilds the .htm beside a .md, if Pandoc is here to do it."""
    sPandoc = shutil.which("pandoc")
    if not sPandoc:
        logging.info("Pandoc was not found, so %s was not rebuilt", sMarkdownPath)
        return False
    sPagePath = sMarkdownPath[:-3] + ".htm"
    lCommand = [sPandoc, sMarkdownPath, "-f", "markdown", "-t", "html5", "--standalone",
                "--toc", "--toc-depth=2", "-o", sPagePath]
    oResult = subprocess.run(lCommand, capture_output=True)
    logging.info("rebuilt %s, exit code %d", sPagePath, oResult.returncode)
    if oResult.returncode != 0:
        logging.error("Pandoc said: %s", oResult.stderr.decode("utf-8", "replace")[:400])
        return False
    logging.info("finished %s: %s", sPagePath, finishPage(sPagePath))
    return True


def main():
    sLogPath = startLog()
    bReportOnly = len(sys.argv) > 1 and sys.argv[1].lower().startswith("report")
    sFolder = os.path.dirname(os.path.abspath(__file__))
    logging.info("folder %s, report only %s", sFolder, bReportOnly)
    lNames = sorted(s for s in os.listdir(sFolder) if s.lower().endswith(".md"))
    iFiles, iLines, iRebuilt = 0, 0, 0
    dPlatforms = {}
    for sName in lNames:
        sPath = os.path.join(sFolder, sName)
        sText = readText(sPath)
        lLines = sText.replace("\r\n", "\n").split("\n")
        lClean, lRemoved = cleanLines(lLines, sName)
        if not lRemoved: continue
        iFiles += 1
        iLines += len(lRemoved)
        logging.info("%s: %d lines to remove", sName, len(lRemoved))
        for sPlatform, sLine in lRemoved:
            dPlatforms[sPlatform.split(",")[0]] = dPlatforms.get(sPlatform.split(",")[0], 0) + 1
            logging.info("    [%s] %s", sPlatform, sLine.strip())
        if bReportOnly: continue
        io.open(sPath, "w", encoding="utf-8-sig", newline="").write("\r\n".join(lClean).rstrip() + "\r\n")
        if rebuildPage(sPath): iRebuilt += 1
    print("Guides read: %d" % len(lNames))
    if bReportOnly:
        print("Guides that WOULD change: %d, lines that WOULD go: %d" % (iFiles, iLines))
    else:
        print("Guides changed: %d, lines removed: %d, pages rebuilt: %d" % (iFiles, iLines, iRebuilt))
    for sPlatform in sorted(dPlatforms):
        print("  %s: %d" % (sPlatform, dPlatforms[sPlatform]))
    print("Log: " + sLogPath)
    return 0


if __name__ == "__main__":
    sys.exit(main())
