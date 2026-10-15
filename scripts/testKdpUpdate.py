r"""testKdpUpdate.py -- tests what kdpUpdate decides without a browser: options, the choice of books, the check before a run,
the AI answers for every book in configs\books.inix, the accessibility measure and the per-book receipt.

    python scripts\testKdpUpdate.py

Prints one line per test and a count; exit code 0 when every test passes, 1 otherwise. Touches nothing on KDP and writes
only inside a temporary folder.
"""

import datetime, glob, os, re, shutil, sys, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kdpBooks as kb
import kdpSubmit as k
import kdpUpdate as u

lAllowedTexts = ["None", "Some sections, with minimal or no editing", "Some sections, with extensive editing", "Entire work, with minimal or no editing", "Entire work, with extensive editing"]
lAllowedImages = ["None", "One or a few, with minimal or no editing", "One or a few, with extensive editing", "Many, with minimal or no editing", "Many, with extensive editing"]

lFailures = []
iPassed = 0


def check(sName, bOk, sDetail=""):
    """Records one test."""
    global iPassed
    if bOk: iPassed += 1
    else: lFailures.append(sName + (": " + sDetail if sDetail else ""))
    print(("PASS " if bOk else "FAIL ") + sName + ("" if bOk else " -- " + sDetail))
    return bOk


def testOptions():
    sys.argv = ["kdpUpdate.py", "--book", "Returning_Alive", "--no-publish"]
    check("options: --book with a value and --no-publish are accepted", u.checkOptions() == "")
    sys.argv = ["kdpUpdate.py", "--publish-all"]
    check("options: an unknown option is refused", u.checkOptions().startswith("Unknown option"))
    sys.argv = ["kdpUpdate.py", "--book"]
    check("options: --book with no value is refused", "needs a value" in u.checkOptions())
    sys.argv = ["kdpUpdate.py", "--limit", "two"]
    check("options: --limit with a word is refused", "whole number" in u.checkOptions())
    sys.argv = ["kdpUpdate.py", "--book", "a", "--book", "b"]
    check("options: --book repeats", u.optionValues("--book") == ["a", "b"])
    return True


# A SYNTHETIC CATALOG WHERE THERE IS NO REAL ONE (1.72.35, from an audit by another AI): the suite read the author's own
# configs\books.inix and stopped wherever it was absent -- the kit itself, a fresh clone, an auditor's copy. In a book
# project the real catalog is checked, all 22 books; elsewhere one invented book for each kind of AI use is checked by
# the same rules, in a temporary folder.
sSyntheticCatalog = """[Generated_Book]
title = A Generated Book
aiUse = generated
aiTools = Claude
aiTextExtent = Entire work, with minimal or no editing
aiImages = One or a few, with minimal or no editing
aiImageTools = ChatGPT

[Assisted_Book]
title = An Assisted Book
aiUse = assisted
aiTools = Claude
aiTextExtent = None
aiImages = None

[Plain_Book]
title = A Plain Book
aiUse = none
"""


def catalogUnderTest():
    """(books, label): the project's own catalog when it has one, otherwise the synthetic one."""
    if os.path.isfile(os.path.join(u.sProject, "configs", "books.inix")): return u.catalog(), "real"
    sTemp = tempfile.mkdtemp(prefix="testKdpUpdate-catalog-")
    os.makedirs(os.path.join(sTemp, "configs"))
    with open(os.path.join(sTemp, "configs", "books.inix"), "w", encoding="utf-8-sig") as f: f.write(sSyntheticCatalog)
    sWas = u.sProject
    try:
        u.sProject = sTemp
        return u.catalog(), "synthetic"
    finally:
        u.sProject = sWas
        shutil.rmtree(sTemp, ignore_errors=True)


def testAiAnswers():
    lBooks, sKind = catalogUnderTest()
    if sKind == "real": check("catalog: 22 books, Blind Vibe Coding included", len(lBooks) == 22, str(len(lBooks)))
    else: check("catalog: the synthetic catalog's 3 books are read (this project has no configs\\books.inix)", len(lBooks) == 3, str(len(lBooks)))
    for sRoot, dBook in lBooks:
        d = u.aiAnswers(dBook)
        bShape = d["texts"] in lAllowedTexts and d["images"] in lAllowedImages and d["translations"] == "None"
        bUsed = (d["used"] == "Yes") == (d["texts"] != "None" or d["images"] != "None")
        bTools = (d["used"] == "No") or bool(d["tools"])
        # A book marked aiFromKdp (Blind Vibe Coding) leaves its extents at None on purpose: the answers its author gave KDP
        # through kdpSubmit stand, since kdpUpdate never discloses less than KDP holds.
        bGenerated = dBook.get("aiUse") != "generated" or d["texts"] != "None" or dBook.get("aiFromKdp", "").lower() == "yes"
        check("AI answers for " + sRoot, bShape and bUsed and bTools and bGenerated, str(d))
    dNone = u.aiAnswers({"aiUse": "none"})
    check("AI answers: a book without AI is answered No", dNone["used"] == "No" and dNone["tools"] == "")
    dAssisted = u.aiAnswers({"aiUse": "assisted", "aiTools": "GPT", "aiTextExtent": "None", "aiImages": "None"})
    check("AI answers: AI-assisted text alone is answered No, as KDP does not ask for it", dAssisted["used"] == "No")
    dCover = u.aiAnswers({"aiUse": "assisted", "aiTools": "GPT", "aiTextExtent": "None", "aiImages": "One or a few, with minimal or no editing", "aiImageTools": "Claude"})
    check("AI answers: an AI cover alone is answered Yes, naming only the image tool", dCover["used"] == "Yes" and dCover["tools"] == "Claude", str(dCover))
    for sAnswer, lWords in [("Entire work, with extensive editing", ["entire work", "extensive"]), ("One or a few, with minimal or no editing", ["one or a few", "minimal"]), ("None", ["none"])]:
        lFound = [w for w in ["none", "entire work", "some sections", "one or a few", "many"] if w in sAnswer.lower()][:1] + (["extensive"] if "extensive" in sAnswer.lower() else ["minimal"] if "minimal" in sAnswer.lower() else [])
        check("AI answers: kdpSubmit reads '" + sAnswer + "' as " + " ".join(lWords), lFound == lWords, str(lFound))
    return True


def testNeverLess():
    check("never less: KDP's Entire, minimal outranks the catalog's Entire, extensive", u.mergedExtent("Entire work, with extensive editing", "ENTIRE_AND_MINIMAL", "text") == "Entire work, with minimal or no editing")
    check("never less: KDP's few DALL-E images survive a catalog that says None", u.mergedExtent("None", "FEW_AND_MINIMAL", "images") == "One or a few, with minimal or no editing")
    check("never less: a catalog answer stands where KDP holds none", u.mergedExtent("Some sections, with extensive editing", "", "text") == "Some sections, with extensive editing")
    check("never less: None and none stay None", u.mergedExtent("None", "NONE", "text") == "None")
    check("tools: Claude is already held by Claude.AI", u.toolsMissing("Claude", ["ChatGPT", "Claude.AI", "Gemini"]) == [])
    check("tools: tools KDP lacks are added; ChatGPT, the product, does not stand for GPT-4, the model", u.toolsMissing("GPT-4, Claude", ["ChatGPT"]) == ["GPT-4", "Claude"], str(u.toolsMissing("GPT-4, Claude", ["ChatGPT"])))
    return True


def testConfirmed():
    dCover = {"aiImages": "One or a few, with minimal or no editing", "aiConfirmed": "images", "aiTextExtent": "Entire work, with minimal or no editing"}
    d = u.aiWanted(dCover, {"text": "ENTIRE_AND_MINIMAL", "images": "MANY_AND_MINIMAL", "translations": "NONE"})
    check("confirmed: the author's cover-only answer is given though KDP holds Many", d["images"] == "One or a few, with minimal or no editing", str(d))
    check("confirmed: an unconfirmed text answer still never falls below KDP's", d["text"] == "Entire work, with minimal or no editing", str(d))
    d2 = u.aiWanted({"aiImages": "None"}, {"images": "MANY_AND_MINIMAL"})
    check("unconfirmed: a catalog None keeps KDP's Many", d2["images"] == "Many, with minimal or no editing", str(d2))
    # THE AUTHOR'S OWN CATALOG ONLY WHERE IT IS (14 October 2026, from a second audit by another AI): this loop read
    # configs\books.inix, which is personal and not in the repository, so in a clean checkout the suite stopped here
    # after 24 checks. The rule itself is tested by the answers above; the catalog's books are checked when it is present.
    if not os.path.isfile(os.path.join(u.sProject, "configs", "books.inix")):
        print("SKIP confirmed: the author's own catalog is not here, so its books were not checked; the rule was, above")
        return True
    for sRoot, dBook in u.catalog():
        if "images" in dBook.get("aiConfirmed", ""):
            check("confirmed images for " + sRoot + " are the cover only", dBook.get("aiImages", "").startswith("One or a few"), dBook.get("aiImages", ""))
    return True


def testPreflightAndChoice(sTemp):
    sProject = os.path.join(sTemp, "MyBooks")
    for sDir in ["configs", "data\\books".replace("\\", os.sep), "results", os.path.join("books", "Demo_Book")]: os.makedirs(os.path.join(sProject, sDir), exist_ok=True)
    k.writeInix(os.path.join(sProject, "data", "books", "Demo_Book.inix"), {"kdp": {"asin": "B000000001", "titleId": "ADEMO1", "title": "Demo Book"}})
    with open(os.path.join(sProject, "books", "Demo_Book", "Demo_Book.md"), "w", encoding="utf-8") as f: f.write("---\ntitle: Demo Book\n---\n\n![A red square](images/a.png)\n\n![](images/b.png)\n")
    u.sProject = sProject
    d = u.bookState("Demo_Book", {"title": "Demo Book"})
    check("preflight: a missing EPUB is a reason not to send", any("no EPUB" in s for s in d["problems"]), str(d["problems"]))
    time.sleep(1.1)
    with open(os.path.join(sProject, "results", "Demo_Book.epub"), "wb") as f: f.write(b"PK")
    with open(os.path.join(sProject, "results", "Demo_Book-audit.md"), "w", encoding="utf-8") as f: f.write("# Audit\n\n## Verdict\n\nNot ready to submit: 1 error.\n")
    d = u.bookState("Demo_Book", {"title": "Demo Book"})
    check("preflight: an audit that is not ready stops the book", any("audit" in s for s in d["problems"]), str(d["problems"]))
    with open(os.path.join(sProject, "results", "Demo_Book-audit.md"), "w", encoding="utf-8") as f: f.write("# Audit\n\n## Verdict\n\nReady to submit: 0 errors, 1 warning.\n")
    d = u.bookState("Demo_Book", {"title": "Demo Book"})
    check("preflight: a ready audit with no EPUB fingerprint stops the book", any("fingerprint" in s for s in d["problems"]), str(d["problems"]))
    with open(os.path.join(sProject, "results", "Demo_Book-audit.md"), "w", encoding="utf-8") as f: f.write("# Audit\n\n- EPUB SHA-256: " + "0" * 64 + "\n\n## Verdict\n\nReady to submit: 0 errors, 1 warning.\n")
    d = u.bookState("Demo_Book", {"title": "Demo Book"})
    check("preflight: an audit of a different EPUB stops the book", any("not the one its audit approved" in s for s in d["problems"]), str(d["problems"]))
    with open(os.path.join(sProject, "results", "Demo_Book-audit.md"), "w", encoding="utf-8") as f: f.write("# Audit\n\n- EPUB SHA-256: " + u.fileSha(os.path.join(sProject, "results", "Demo_Book.epub")) + "\n\n## Verdict\n\nReady to submit: 0 errors, 1 warning.\n")
    d = u.bookState("Demo_Book", {"title": "Demo Book"})
    check("preflight: a newer EPUB with a ready audit of that EPUB and a title ID is ready", d["problems"] == [], str(d["problems"]))
    check("unchanged: a book never submitted is not unchanged", not d["unchanged"], str(d))
    os.makedirs(os.path.join(sProject, "data", "receipts"), exist_ok=True)
    k.writeInix(u.receiptFile("Demo_Book"), {"manuscript": {"uploaded": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}})
    check("submission: an upload alone is not a submission", not u.recentlySubmitted(d["data"]), "")
    k.writeInix(u.receiptFile("Demo_Book"), {"submission": {"at": (datetime.datetime.now() + datetime.timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"), "epubSha": d["sha"], "answersKey": d["answersKey"]}})
    check("submission: a time two days in the future is no evidence", not u.recentlySubmitted(d["data"]), "")
    k.writeInix(u.receiptFile("Demo_Book"), {"submission": {"at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "epubSha": d["sha"], "answersKey": d["answersKey"]}})
    check("submission: a submission an hour or less ago counts", u.recentlySubmitted(d["data"]), "")
    d = u.bookState("Demo_Book", {"title": "Demo Book"})
    check("unchanged: the same EPUB and answers as the last submission is unchanged", d["unchanged"], "")
    d = u.bookState("Demo_Book", {"title": "Demo Book", "aiImages": "One or a few, with minimal or no editing"})
    check("unchanged: a changed catalog answer is a change", not d["unchanged"], "")
    os.remove(u.receiptFile("Demo_Book"))
    os.utime(os.path.join(sProject, "books", "Demo_Book", "Demo_Book.md"), (time.time() + 7 * 3600, time.time() + 7 * 3600))  # the skew of a zip made seven hours ahead
    d2 = u.bookState("Demo_Book", {"title": "Demo Book"})
    check("preflight: a manuscript dated in the future, as an unzipped one can be, does not stop the book", not any("newer" in s for s in d2["problems"]), str(d2["problems"]))
    os.utime(os.path.join(sProject, "results", "Demo_Book.epub"), (time.time() - 120, time.time() - 120))
    os.utime(os.path.join(sProject, "books", "Demo_Book", "Demo_Book.md"), (time.time() - 30, time.time() - 30))
    d3 = u.bookState("Demo_Book", {"title": "Demo Book"})
    check("preflight: a manuscript edited after its EPUB stops the book", any("newer" in s for s in d3["problems"]), str(d3["problems"]))
    check("accessibility: one of two pictures described is some", u.pictureDescriptions(d["manuscript"]) == "some informative images")
    lStates = [dict(d, root="Alpha", asin="B1", title="Alpha"), dict(d, root="Beta", asin="B2", title="The Beta Book"), dict(d, root="Gamma", asin="B3", title="Gamma")]
    sys.argv = ["kdpUpdate.py", "--book", "b2", "--book", "gam"]
    check("choice: --book matches an ASIN and the start of a folder name", [x["root"] for x in u.chosen(lStates)] == ["Beta", "Gamma"])
    sys.argv = ["kdpUpdate.py", "--limit", "2"]
    check("choice: --limit keeps the first ready books", [x["root"] for x in u.chosen(lStates)] == ["Alpha", "Beta"])
    sPath = u.useReceiptOf("Demo_Book")
    check("receipt: kdpSubmit's receipt points at the book's own file", k.receiptPath() == sPath and sPath.endswith(os.path.join("receipts", "Demo_Book.inix")))
    return True


def testRoyalty():
    for sPrice, sNow, sWant in [("2.99", "35%", "70%"), ("12.99", "35%", "70%"), ("13.00", "70%", "35%"), ("20", "70%", "35%"), ("1.99", "70%", "35%"), ("", "70%", "70%"), ("abc", "35%", "35%")]:
        check("royalty: price " + (sPrice or "blank") + " gives " + sWant, u.royaltyFor(sPrice, sNow) == sWant, u.royaltyFor(sPrice, sNow))
        check("royalty, kdpBooks: price " + (sPrice or "blank") + " gives " + sWant, kb.royaltyFor(sPrice, sNow) == sWant, kb.royaltyFor(sPrice, sNow))
    return True


def testKitReader():
    # Any book's data file whose keywords are a fenced list, the case this test is about; no book is named.
    lData = [s for s in sorted(glob.glob(os.path.join(k.sProject, "data", "books", "*.inix"))) if re.search(r"(?m)^keywords\s*=\s*`\s*$", open(s, encoding="utf-8-sig").read())]
    # Without a book's own data file (the kit itself, a fresh clone), an invented one with a fenced list is read instead
    # (1.72.35, from an audit by another AI): the case is the fenced list, not any particular book.
    sTemp = ""
    if lData:
        sData = lData[0]
    else:
        sTemp = tempfile.mkdtemp(prefix="testKdpUpdate-reader-")
        sData = os.path.join(sTemp, "Demo_Book.inix")
        with open(sData, "w", encoding="utf-8-sig") as f: f.write("[kdp]\ntitle = A Demo Book\nkeywords = `\nfirst keyword\nsecond keyword\nthird keyword\n`\n")
    try:
        d = k.readInix(sData)
    finally:
        if sTemp: shutil.rmtree(sTemp, ignore_errors=True)
    lKeywords = k.inixList(d.get("kdp", {}).get("keywords", ""))
    check("kit reader: kdpSubmit reads a fenced keyword list as a list", len(lKeywords) >= 3 and "`" not in lKeywords, str(lKeywords[:3]))
    return True


# BOTH FALLBACK READERS, EVERY FORM (15 October 2026, from an audit of MyBooks): kdpSubmit's fallback could not read a
# fence and kdpReport's could not read a plain block, so a file read correctly by one was misread by the other. Each form
# the Homer INIX rules allow is read by both, and both must give the same, expected values.
sTripleQuote = '"' * 3
sInixForms = "\n".join([
    "[book]",
    "title = A Title",
    "url = https://example.org/a?b=c&d=e",
    "description =",
    "First line of a plain block.",
    "",
    "Third line, after a kept blank line.",
    " note = this line looks like a key, so it is written with one leading space",
    "",
    "keywords = `",
    "first keyword",
    "second = with an equals sign",
    "[looks like a section]",
    "`",
    "quoted = " + sTripleQuote,
    "a value with a ` backtick",
    sTripleQuote,
    "; a comment outside any value",
    "[second]",
    "empty =",
    "last = done",
    ""])


def testInixFallbacks(sTemp):
    sPath = os.path.join(sTemp, "forms.inix")
    with open(sPath, "w", encoding="utf-8-sig", newline="") as f: f.write(sInixForms.replace("\n", "\r\n"))
    dSubmit = k.readInixOwn(sPath)
    # kdpReport belongs to a book project such as MyBooks, not to the kit, so the two readers are compared only where
    # both are present; kdpSubmit's own reader is checked everywhere, against the expected values below.
    try:
        import kdpReport as r
    except ImportError:
        r = None
        print("NOTE inix: kdpReport is not in this project, so only kdpSubmit's reader is checked")
    if r: check("inix: both fallback readers give the same result for every form", dSubmit == r.readInixOwn(sPath), str(dSubmit) + " | " + str(r.readInixOwn(sPath)))
    dBook = dSubmit.get("book", {})
    check("inix: an equals sign inside a one-line value is kept", dBook.get("url") == "https://example.org/a?b=c&d=e", dBook.get("url", ""))
    check("inix: a plain block keeps its inner blank line and its escaped key-like line",
          dBook.get("description") == "First line of a plain block.\n\nThird line, after a kept blank line.\nnote = this line looks like a key, so it is written with one leading space",
          repr(dBook.get("description")))
    check("inix: a backtick fence keeps equals signs and section-like lines verbatim",
          dBook.get("keywords") == "first keyword\nsecond = with an equals sign\n[looks like a section]", repr(dBook.get("keywords")))
    check("inix: a triple-quote fence keeps a backtick", dBook.get("quoted") == "a value with a ` backtick", repr(dBook.get("quoted")))
    check("inix: a later section and an empty value are read", dSubmit.get("second", {}).get("last") == "done" and dSubmit.get("second", {}).get("empty") == "", str(dSubmit.get("second")))
    return True


# SAVED MEANS SEEN SAVED (15 October 2026, from an audit of MyBooks): Save and Continue opened the next tab directly
# whenever KDP stayed put without an error, as if the save were confirmed. A simulated page plays KDP's part: the next
# tab may be opened directly only after a save-success message was read.
class FakePage:
    def __init__(self, lMoveOnAttempt, sTitle="A1B2C3D4"):
        self.url = k.sTitleSetup + sTitle + "/details"
        self.lMoveOnAttempt, self.iPresses, self.lGoto, self.sTitle = lMoveOnAttempt, 0, [], sTitle
    def goto(self, sUrl):
        self.lGoto.append(sUrl)
        self.url = sUrl
    def wait_for_load_state(self, *lArgs, **dArgs):
        return True


def runSave(oPage, lMessages):
    """Runs saveAndContinue against oPage, with lMessages[i] the messages KDP shows after press i+1."""
    dSaved = {s: getattr(k, s) for s in ("clickButton", "logMessages", "tabLooksReady", "unresolved", "say", "iSaveWaitSeconds", "iSettleSeconds")}
    fSleep = time.sleep
    lUnresolved = []
    def fakeClick(page, sWhat, lSelectors):
        page.iPresses += 1
        if page.iPresses in page.lMoveOnAttempt: page.url = k.sTitleSetup + page.sTitle + "/content"
        return True
    try:
        k.clickButton = fakeClick
        k.logMessages = lambda page, sWhen: lMessages[min(page.iPresses, len(lMessages)) - 1] if lMessages else []
        k.tabLooksReady = lambda page, sTab: True
        k.unresolved = lambda sWhat, sWhy: lUnresolved.append(sWhy) or True
        k.say = lambda sText: True
        k.iSaveWaitSeconds, k.iSettleSeconds = 1, 1
        time.sleep = lambda n: None
        bOk = k.saveAndContinue(oPage, "content")
    finally:
        for sName, oValue in dSaved.items(): setattr(k, sName, oValue)
        time.sleep = fSleep
    return bOk, lUnresolved


def testSaveConfirmation():
    oPage = FakePage([1])
    bOk, lUnresolved = runSave(oPage, [["Save Successful!"]])
    check("save: moving on at once needs no direct opening", bOk and not oPage.lGoto and oPage.iPresses == 1, str((bOk, oPage.lGoto, oPage.iPresses)))
    oPage = FakePage([])
    bOk, lUnresolved = runSave(oPage, [["Save Successful!", "Complete"]] * 3)
    check("save: KDP stays put but said Save Successful, so the next tab is opened directly", bOk and len(oPage.lGoto) == 1 and oPage.lGoto[0].endswith("/content"), str((bOk, oPage.lGoto)))
    oPage = FakePage([])
    bOk, lUnresolved = runSave(oPage, [["Complete"]] * 3)
    check("save: KDP stays put and never confirms the save, so nothing is opened and the run stops", not bOk and not oPage.lGoto and lUnresolved and "never said the save succeeded" in lUnresolved[0], str((bOk, oPage.lGoto, lUnresolved)))
    oPage = FakePage([])
    bOk, lUnresolved = runSave(oPage, [["Please fix the highlighted fields"]])
    check("save: a refusal stops at once, with no direct opening", not bOk and not oPage.lGoto and oPage.iPresses == 1, str((bOk, oPage.lGoto, oPage.iPresses)))
    oPage = FakePage([])
    bOk, lUnresolved = runSave(oPage, [["Complete"], ["Save Successful!"], ["Complete"]])
    check("save: a confirmation in any attempt counts", bOk and len(oPage.lGoto) == 1, str((bOk, oPage.lGoto)))
    return True


# THE RUN RECORD (15 October 2026, from an audit of MyBooks): a run that never ended must be named by the next one.
def testRunRecord(sTemp):
    sProjectWas = u.sProject
    lSaid = []
    fSay = u.say
    try:
        u.sProject = os.path.join(sTemp, "runrecord")
        u.say = lambda sText: lSaid.append(sText) or True
        check("run record: with no record, nothing is said", u.warnUnfinished() == [] and not lSaid, str(lSaid))
        dRun = {"run": {"started": "2026-10-14 16:16:29", "updated": "", "finished": "", "state": "running", "kind": "update", "command": "kdpUpdate", "log": "x.log"},
                "Blind_Vibe_Coding": {"title": "Blind Vibe Coding", "stage": "planned", "at": ""},
                "Returning_Alive": {"title": "Returning Alive", "stage": "planned", "at": ""}}
        u.writeRun(dRun)
        u.setStage(dRun, "Returning_Alive", "submitted")
        u.setStage(dRun, "Blind_Vibe_Coding", "in progress")
        dBack = k.readInix(u.runPath())
        check("run record: stages read back as written", dBack.get("Blind_Vibe_Coding", {}).get("stage") == "in progress" and dBack.get("Returning_Alive", {}).get("stage") == "submitted", str(dBack))
        check("run record: no temporary file is left behind", not os.path.exists(u.runPath() + ".tmp"))
        lLeft = u.warnUnfinished()
        check("run record: a run that never ended names the book left in progress", lLeft == ["Blind_Vibe_Coding"] and lSaid and "Blind Vibe Coding was left in progress" in lSaid[-1], str((lLeft, lSaid)))
        u.endRun(dRun, "interrupted")
        lSaid.clear()
        check("run record: an interrupted run is named too", u.warnUnfinished() == ["Blind_Vibe_Coding"] and "(interrupted)" in lSaid[-1], str(lSaid))
        u.setStage(dRun, "Blind_Vibe_Coding", "submitted")
        u.endRun(dRun, "complete")
        lSaid.clear()
        check("run record: after a complete run, nothing is said", u.warnUnfinished() == [] and not lSaid, str(lSaid))
    finally:
        u.sProject = sProjectWas
        u.say = fSay
    return True


def testFingerprints(sTemp):
    """Version 11: a book's sources by content, an EPUB rebuilt from unchanged sources still unchanged, staleness from
    the audit's sources fingerprint, and --record's receipt (9 October 2026)."""
    sProject = os.path.join(sTemp, "fingerprints")
    sBook = os.path.join(sProject, "books", "Print_Book")
    os.makedirs(os.path.join(sBook, "images"))
    os.makedirs(os.path.join(sProject, "results"))
    os.makedirs(os.path.join(sProject, "data", "books"))
    sManuscript = os.path.join(sBook, "Print_Book.md")
    with open(sManuscript, "wb") as f: f.write("---\ntitle: Print Book\n---\n\nText.\n".encode("utf-8"))
    with open(os.path.join(sBook, "Print_Book.jpg"), "wb") as f: f.write(b"\xff\xd8 a cover")
    sFirst = k.bookSourcesSha(sBook)
    with open(sManuscript, "wb") as f: f.write(b"\xef\xbb\xbf" + "---\r\ntitle: Print Book\r\n---\r\n\r\nText.\r\n".encode("utf-8"))
    check("sources: line endings and a byte order mark alone are no change", k.bookSourcesSha(sBook) == sFirst)
    with open(os.path.join(sBook, "found.inix"), "w", encoding="utf-8") as f: f.write("[found]\nwhen = " + str(time.time()) + "\n")
    check("sources: the build's own found.inix is not a source", k.bookSourcesSha(sBook) == sFirst)
    with open(os.path.join(sBook, "Print_Book.jpg"), "wb") as f: f.write(b"\xff\xd8 a new cover")
    sCover = k.bookSourcesSha(sBook)
    check("sources: a new cover is a change", sCover != sFirst)
    with open(os.path.join(sBook, "images", "a.png"), "wb") as f: f.write(b"\x89PNG")
    sPicture = k.bookSourcesSha(sBook)
    check("sources: a new picture is a change", sPicture != sCover)
    os.rename(os.path.join(sBook, "images", "a.png"), os.path.join(sBook, "images", "b.png"))
    check("sources: a renamed picture is a change", k.bookSourcesSha(sBook) != sPicture)
    os.rename(os.path.join(sBook, "images", "b.png"), os.path.join(sBook, "images", "a.png"))
    k.writeInix(os.path.join(sProject, "data", "books", "Print_Book.inix"), {"kdp": {"asin": "B000000002", "titleId": "APRINT1", "title": "Print Book"}})
    def build(bEpub):
        with open(os.path.join(sProject, "results", "Print_Book.epub"), "wb") as f: f.write(bEpub)
        with open(os.path.join(sProject, "results", "Print_Book-audit.md"), "w", encoding="utf-8") as f:
            f.write("# Audit\n\n- EPUB SHA-256: " + u.fileSha(os.path.join(sProject, "results", "Print_Book.epub")) + "\n- Sources SHA-256: " + k.bookSourcesSha(sBook) + "\n\n## Verdict\n\nReady to submit: 0 errors.\n")
    u.sProject = sProject
    dBook = {"title": "Print Book"}
    build(b"PK built at nine")
    d = u.bookState("Print_Book", dBook)
    check("record: a book built from its sources is ready", d["problems"] == [], str(d["problems"]))
    u.recordReceipt(d, "recorded in a test")
    build(b"PK built again at ten, the same sources")
    d = u.bookState("Print_Book", dBook)
    check("unchanged: an EPUB rebuilt from the same sources is unchanged", d["unchanged"] and not d["problems"], str(d))
    with open(sManuscript, "a", encoding="utf-8") as f: f.write("More text.\n")
    d = u.bookState("Print_Book", dBook)
    check("preflight: a manuscript changed since its build stops the book, by content", any("changed since its EPUB was built" in s for s in d["problems"]), str(d["problems"]))
    build(b"PK built with the new text")
    d = u.bookState("Print_Book", dBook)
    check("unchanged: changed sources, rebuilt, are a change to send", not d["unchanged"] and not d["problems"], str(d))
    k.writeInix(u.receiptFile("Print_Book"), {"submission": {"at": "2026-10-08 10:00:00", "epubSha": d["sha"], "answersKey": d["answersKey"]}})
    d = u.bookState("Print_Book", dBook)
    check("unchanged: a receipt from before version 11, of this very EPUB, still counts", d["unchanged"], str(d))
    return True


def main():
    sTemp = tempfile.mkdtemp(prefix="testKdpUpdate-")
    sProjectWas = u.sProject
    try:
        testOptions()
        testAiAnswers()
        testNeverLess()
        testConfirmed()
        testRoyalty()
        testKitReader()
        testInixFallbacks(sTemp)
        testSaveConfirmation()
        testRunRecord(sTemp)
        testPreflightAndChoice(sTemp)
        testFingerprints(sTemp)
    finally:
        u.sProject = sProjectWas
        shutil.rmtree(sTemp, ignore_errors=True)
    print(str(iPassed) + " passed, " + str(len(lFailures)) + " failed.")
    return 1 if lFailures else 0


if __name__ == "__main__":
    sys.exit(main())
