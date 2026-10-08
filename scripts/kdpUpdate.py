r"""kdpUpdate.py -- sends each book's new EPUB, with its AI, DRM and accessibility answers, to its existing title on Kindle
Direct Publishing, applies any metadata its data file proposes, and republishes it.

HOW IT WORKS. Everything that touches KDP is kdpSubmit's and kdpBooks' own proven code, imported as they import each other: the
remembered Edge window and its sign-in, the Bookshelf reader, Save as Draft and Save and Continue with their confirmations, the
upload and its receipt, the AI answers, DRM with its consent box, and Publish with its acknowledgement. What this script adds is
the choice of books, a check before any browser opens, and the answers for each book:

  - the manuscript is results\<book>.epub, which buildBooks made and audited; it is uploaded only when KDP does not hold that
    exact file (a receipt per book in data\receipts\ records what was sent, as kdpSubmit's receipt does for one book);
  - the cover is left as KDP holds it;
  - the AI answers come from configs\books.inix -- aiTextExtent and aiImages in KDP's own words, with aiTools and aiImageTools
    -- but never disclose less than KDP already holds: for text, images and translations the stronger of the catalog's answer
    and KDP's current one is given, and a tool already named on KDP is never removed (version 3, after the 14:27 survey found
    the books' own earlier disclosures stronger than the catalog's in several places); a book with no AI either way is No;
  - DRM is No, with its consent box, so every book can also be bought as a DRM-free EPUB, as kdpBooks does;
  - the accessibility answer is measured from the manuscript: whether all, some or none of its pictures have descriptions;
  - the Details and Pricing tabs change only where the book's data\books file proposes something KDP does not hold, by
    kdpBooks' own test (description, keywords, categories, price, the Adult-only answer).

A book is skipped before the browser opens when its EPUB is missing, older than its manuscript, or not passed by its audit,
or when its data file has no title ID; and after the Bookshelf is read, when KDP shows an update of it in review, which locks
it.

USAGE
  scripts\kdpUpdate.cmd --list                          list every book and whether it is ready; no browser
  scripts\kdpUpdate.cmd --survey                        read each title's Content tab and record what KDP holds; change nothing
  scripts\kdpUpdate.cmd --book Returning_Alive --no-publish   one book, stopping at the saved draft
  scripts\kdpUpdate.cmd --book Returning_Alive          one book, published
  scripts\kdpUpdate.cmd --limit 4                       the next four ready books
  scripts\kdpUpdate.cmd                                 every ready book
--book takes a folder name, an ASIN or the start of a title, and may be given more than once. --ask asks before each Publish.
--reupload sends the EPUB even when the receipt says KDP holds it. Unknown options stop the script before it does anything.

Every run writes logs\MyBooks-kdpUpdate-<date>-<time>.log, every step as it happens. Exit codes: 0 every chosen book done;
2 options wrong or no book ready; 3 no sign-in; 4 crash; 5 some book kept as a draft, blocked, locked or of unknown outcome,
listed at the end.
"""

import datetime, hashlib, json, os, platform, re, sys, time, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kdpSubmit as k
import kdpBooks as kb

c_iProcessingMinutes = 20
c_lFlags = ["--ask", "--book", "--limit", "--list", "--no-publish", "--republish", "--reupload", "--survey"]
c_lValueFlags = ["--book", "--limit"]
c_sContentButton = "data-assets-interior-file-upload-browse-button-announce"
c_sVersion = "2026-10-08 version 10: readiness requires the audited EPUB fingerprint, a book unchanged since its last submission is not sent, only a submission counts as one, DRM failure blocks Publish, royalty follows the $2.99-$12.99 band; version 9: an AI answer the author has confirmed (aiConfirmed) is given exactly, even below what KDP holds; version 8: a recent submission is also known from the upload receipt, which survives a replaced data file; version 7: a title that will not open within 72 hours of being submitted is reported as in review, not as a problem; version 6: a book built by its own project, such as Blind Vibe Coding, is read from there, and a title with no ASIN is found on the Bookshelf by its title ID; version 5: when KDP stays on the Content tab without naming a problem, the boxes are checked again and the step tried once more; a live title with an update in review is reported as such; version 4: a title KDP shows as Publishing is locked like one In Review, and is not opened; version 3: AI answers never disclose less than KDP already holds, read live before answering; version 2: a manuscript dated in the future, as an unzipped one can be, no longer counts as newer than its EPUB; version 1 was the first, built on kdpSubmit version 36 and kdpBooks version 14"

sProject = k.sProject


def log(sText): return k.log(sText)
def say(sText): return k.say(sText)


def plural(iCount, sOne, sMany=""):
    """1 book, 2 books."""
    return str(iCount) + " " + (sOne if iCount == 1 else (sMany or sOne + "s"))


def optionValues(sFlag):
    """Every value given after a flag that may repeat, such as --book."""
    return [sys.argv[i + 1] for i, a in enumerate(sys.argv[:-1]) if a == sFlag]


def checkOptions():
    """Stops on an unknown option or a value flag with nothing after it, before anything is done."""
    for i, a in enumerate(sys.argv[1:], 1):
        if a.startswith("--") and a not in c_lFlags: return "Unknown option " + a + ". Allowed: " + " ".join(c_lFlags) + "."
        if a in c_lValueFlags and (i + 1 >= len(sys.argv) or sys.argv[i + 1].startswith("--")): return a + " needs a value after it."
    if "--limit" in sys.argv and not optionValues("--limit")[0].isdigit(): return "--limit needs a whole number."
    return ""


def catalog():
    """[(folder name, catalog entry)] for every book in configs\\books.inix, in order by title."""
    dAll = k.readInix(os.path.join(sProject, "configs", "books.inix"))
    lBooks = [(sRoot, d) for sRoot, d in dAll.items() if isinstance(d, dict) and d.get("title")]
    return sorted(lBooks, key=lambda t: re.sub(r"^(a|an|the)\s+", "", t[1]["title"].lower()))


def royaltyFor(sPrice, sCurrent):
    """The royalty plan for a US price: 70% only within KDP's band for it, $2.99 to $12.99, and 35% outside it, either way.
    WHY (8 October 2026, from an audit by another AI): the update paths chose 70% for any price of $2.99 or more, with no
    ceiling, and kept 70% for a price lowered below $2.99, both of which KDP refuses. With no price, the current plan."""
    try: fPrice = float(sPrice)
    except (TypeError, ValueError): return sCurrent
    if fPrice != fPrice or fPrice <= 0: return sCurrent
    return "70%" if 2.99 <= fPrice <= 12.99 else "35%"


def fileSha(sPath):
    """The SHA-256 fingerprint of a file, or "" when it is missing."""
    return hashlib.sha256(open(sPath, "rb").read()).hexdigest() if os.path.exists(sPath) else ""


def auditProblem(sRoot, sEpub):
    """Why the book's audit does not approve the EPUB in results, or "" when it does: the audit must say ready to submit
    and name this exact EPUB's fingerprint. WHY (8 October 2026, from an audit by another AI): readiness was read from
    the audit's first line alone, so an old audit could approve a newer or damaged EPUB."""
    sAudit = os.path.join(sProject, "results", sRoot + "-audit.md")
    if not os.path.exists(sAudit): return "it has no audit; run scripts\\buildBooks.cmd"
    with open(sAudit, encoding="utf-8-sig") as f: sText = f.read()
    if not re.search(r"(?m)^Ready to submit", sText): return "its audit does not say ready to submit; read results\\" + sRoot + "-audit.htm"
    oSha = re.search(r"(?m)^- EPUB SHA-256: ([0-9a-f]{64})", sText)
    if not oSha: return "its audit names no EPUB fingerprint, as audits from before 8 October do not; run scripts\\buildBooks.cmd"
    if oSha.group(1) != fileSha(sEpub): return "the EPUB in results is not the one its audit approved; run scripts\\buildBooks.cmd"
    return ""


def auditReady(sRoot):
    """Whether the book's audit approves the exact EPUB in results."""
    return not auditProblem(sRoot, os.path.join(sProject, "results", sRoot + ".epub"))


def answersKey(dBook, sData):
    """A fingerprint of everything kdpUpdate answers from: the book's catalog entry and its data file's [proposed]
    section. A change in either means KDP has something new to be told."""
    dProposed = k.readInix(sData).get("proposed", {}) if os.path.exists(sData) else {}
    return hashlib.sha256(json.dumps([dBook, dProposed], sort_keys=True, default=str).encode("utf-8")).hexdigest()


def receiptFile(sRoot):
    """The book's receipt in data\\receipts: its uploads, and its submissions."""
    return os.path.join(sProject, "data", "receipts", sRoot + ".inix")


def bookState(sRoot, dBook):
    """What the run needs to know about one book before a browser opens, with every reason it cannot go yet."""
    sEpub = os.path.join(sProject, "results", sRoot + ".epub")
    # A book built by a project of its own (externalProject in its catalog entry) keeps its manuscript there.
    sManuscript = os.path.join(dBook["externalProject"], sRoot + ".md") if dBook.get("externalProject") else os.path.join(sProject, "books", sRoot, sRoot + ".md")
    sData = os.path.join(sProject, "data", "books", sRoot + ".inix")
    dKdp = k.readInix(sData).get("kdp", {}) if os.path.exists(sData) else {}
    lProblems = []
    if not os.path.exists(sEpub): lProblems.append("no EPUB in results; run scripts\\buildBooks.cmd")
    # A manuscript dated in the future was unzipped, not edited: a zip stores times without a time zone, so a project zipped
    # on a computer hours ahead arrives dated hours ahead (7 October 2026). Only a manuscript dated in the past, after its
    # EPUB, means the EPUB is stale.
    elif os.path.exists(sManuscript) and os.path.getmtime(sEpub) < os.path.getmtime(sManuscript) <= time.time() + 300: lProblems.append("the manuscript is newer than its EPUB; run scripts\\buildBooks.cmd")
    elif auditProblem(sRoot, sEpub): lProblems.append(auditProblem(sRoot, sEpub))
    if not dKdp.get("titleId"): lProblems.append("no KDP title ID in data\\books\\" + sRoot + ".inix; run scripts\\kdpBooks.cmd --export")
    # UNCHANGED SINCE ITS LAST SUBMISSION (8 October 2026, from an audit by another AI): a run used to open, save and
    # republish every unlocked book though nothing in it had changed, each time starting another KDP review.
    sSha, sKey = fileSha(sEpub), answersKey(dBook, sData)
    dSubmitted = k.readInix(receiptFile(sRoot)).get("submission", {}) if os.path.exists(receiptFile(sRoot)) else {}
    bUnchanged = bool(sSha) and dSubmitted.get("epubSha") == sSha and dSubmitted.get("answersKey") == sKey
    return {"sha": sSha, "answersKey": sKey, "unchanged": bUnchanged, "root": sRoot, "title": dBook["title"], "epub": sEpub, "manuscript": sManuscript, "data": sData, "titleId": dKdp.get("titleId", ""), "asin": dKdp.get("asin", ""), "problems": lProblems}


def chosen(lStates):
    """The books --book names, or all; --limit then keeps the first that many ready ones."""
    lWanted = [s.lower() for s in optionValues("--book")]
    if lWanted:
        lStates = [d for d in lStates if any(w in (d["root"].lower(), d["asin"].lower()) or d["title"].lower().startswith(w) or d["root"].lower().startswith(w) for w in lWanted)]
    if "--limit" in sys.argv:
        iLimit, lKept = int(optionValues("--limit")[0]), []
        for d in lStates:
            if d["problems"] or len([x for x in lKept if not x["problems"]]) < iLimit: lKept.append(d)
        lStates = lKept
    return lStates


def aiAnswers(dBook):
    """KDP's AI answers for one book, in the shape kdpSubmit's answerAiContent reads. AI-assisted text alone is not asked for by
    KDP, so a book with no AI-generated text and no AI-generated image is answered No."""
    sText = (dBook.get("aiTextExtent", "") or "None").strip()
    sImages = (dBook.get("aiImages", "") or "None").strip()
    bText, bImages = not sText.lower().startswith("none"), not sImages.lower().startswith("none")
    lTools = []
    if bText and dBook.get("aiTools", "").strip(): lTools.append(dBook["aiTools"].strip())
    if bImages and dBook.get("aiImageTools", "").strip() and dBook["aiImageTools"].strip() not in lTools: lTools.append(dBook["aiImageTools"].strip())
    return {"used": "Yes" if (bText or bImages) else "No", "texts": sText, "images": sImages, "translations": "None", "tools": ", ".join(lTools)}


def extentRank(sAnswer):
    """An AI extent as (amount, editing), so two can be compared: amount 0 none, 1 some sections or one or a few, 2 the entire
    work or many; editing 1 for minimal or no editing, the stronger disclosure, 0 for extensive. Takes the catalog's words or
    KDP's own codes (ENTIRE_AND_MINIMAL); None when no answer is given."""
    s = (sAnswer or "").strip().lower().replace("_", " ")
    if not s: return None
    if s.startswith("none"): return (0, 0)
    iAmount = 2 if re.search(r"\b(entire|many)\b", s) else 1
    return (iAmount, 1 if "minimal" in s else 0)


def extentWords(tRank, sKind):
    """KDP's words for a rank: ('Entire work', 'with minimal or no editing') and so on; images say One or a few, and Many."""
    if not tRank or tRank[0] == 0: return "None"
    sAmount = {("text", 1): "Some sections", ("text", 2): "Entire work", ("images", 1): "One or a few", ("images", 2): "Many", ("translations", 1): "Some sections", ("translations", 2): "Entire work"}[(sKind, tRank[0])]
    return sAmount + ", with " + ("minimal or no editing" if tRank[1] else "extensive editing")


def mergedExtent(sCatalog, sKdp, sKind):
    """The answer to give: never less than KDP already holds. The stronger of the catalog's answer and KDP's current one."""
    lRanks = [r for r in (extentRank(sCatalog), extentRank(sKdp)) if r is not None]
    return extentWords(max(lRanks), sKind) if lRanks else "None"


def toolsMissing(sWanted, lHeld):
    """The tools named in the catalog that no box on KDP names yet, matched loosely: Claude is held by 'Claude.AI'."""
    lHeldLower = [h.strip().lower() for h in lHeld if h.strip()]
    return [t.strip() for t in sWanted.split(",") if t.strip() and not any(t.strip().lower() in h or h in t.strip().lower() for h in lHeldLower)]


def aiWanted(dBook, dNow):
    """The AI answers to give for text, images and translations, from the catalog and what KDP holds now (dNow: KDP's own
    codes, such as MANY_AND_MINIMAL, or "" for no answer). An answer the author has confirmed (aiConfirmed in
    configs\\books.inix: text, images, translations) is given exactly, even below KDP's: on 7 October 2026 the author said
    the only images made with AI are the covers, so books that had declared "Many" AI images now declare one or a few.
    Every other answer never discloses less than KDP holds."""
    dKeys = {"images": "aiImages", "text": "aiTextExtent", "translations": ""}
    setConfirmed = {x.strip().lower() for x in dBook.get("aiConfirmed", "").split(",") if x.strip()}
    dWanted = {}
    for sKind, sKey in dKeys.items():
        sCatalog = dBook.get(sKey, "") if sKey else "None"
        dWanted[sKind] = extentWords(extentRank(sCatalog) or (0, 0), sKind) if sKind in setConfirmed else mergedExtent(sCatalog, dNow.get(sKind, ""), sKind)
    return dWanted


def answerAiMerged(page, dBook):
    """KDP's AI questions: reads the current answers and gives aiWanted's -- an answer the author confirmed exactly, any
    other never less than KDP holds -- adding any catalog tool not yet named and leaving named tools in place. Uses
    kdpSubmit's clickAria and setSelectByWords."""
    dKinds = {"text": ("aiTextExtent", "aiTools", "texts"), "images": ("aiImages", "aiImageTools", "images"), "translations": ("", "", "")}
    def current(sKind):
        oSelect = page.locator("#generative-ai-questionnaire-" + sKind)
        return oSelect.first.input_value() if oSelect.count() else ""
    dNow = {sKind: current(sKind) for sKind in dKinds}
    dWanted = aiWanted(dBook, dNow)
    log("AI answers: KDP holds " + str(dNow) + "; giving " + str(dWanted))
    if all(v == "None" for v in dWanted.values()):
        say("AI-generated content: no.")
        return k.clickAria(page, "AI-generated content used", "radio", "No")
    say("AI-generated content: yes; " + "; ".join(sKind + " " + v for sKind, v in dWanted.items() if v != "None") + ".")
    if not k.clickAria(page, "AI-generated content used", "radio", "Yes"): return False
    time.sleep(2)
    for sKind, sAnswer in dWanted.items():
        oSelect = page.locator("#generative-ai-questionnaire-" + sKind)
        if not oSelect.count():
            k.unresolved("AI " + sKind + " extent", "no menu found for it")
            continue
        if extentRank(current(sKind)) == extentRank(sAnswer):
            log("KEPT AI " + sKind + " extent = " + sAnswer)
            continue
        lWords = ["none"] if sAnswer == "None" else [sAnswer.split(",")[0].lower(), "minimal" if "minimal" in sAnswer else "extensive"]
        k.setSelectByWords(page, "AI " + sKind + " extent", oSelect.first, lWords)
        time.sleep(1)
    for sKind, (sExtentKey, sToolKey, sLabel) in dKinds.items():
        if not sLabel or dWanted[sKind] == "None": continue
        oBoxes = page.get_by_label(re.compile("AI-generated " + sLabel, re.I))
        lVisible = [oBoxes.nth(i) for i in range(oBoxes.count()) if oBoxes.nth(i).is_visible()]
        lHeld = [o.input_value() for o in lVisible]
        lMissing = toolsMissing(dBook.get(sToolKey, ""), lHeld)
        if not lMissing and any(h.strip() for h in lHeld):
            log("KEPT AI tools for " + sLabel + ": " + "; ".join(h for h in lHeld if h.strip()))
            continue
        if not lMissing:
            k.unresolved("AI tool for " + sLabel, "KDP asks which tool made the AI-generated " + sLabel + ", and neither KDP nor configs\\books.inix names one")
            continue
        lEmpty = [o for o in lVisible if not o.input_value().strip()]
        for sTool in lMissing:
            if lEmpty:
                oBox = lEmpty.pop(0)
                oBox.click()
                oBox.fill(sTool)
            elif lVisible:
                oBox = lVisible[0]
                oBox.click()
                oBox.fill(oBox.input_value().strip() + ", " + sTool)
            else:
                k.unresolved("AI tool for " + sLabel, "no box to name " + sTool + " in")
                continue
            oBox.press("Tab")
            time.sleep(1)
            log("ADDED AI tool for " + sLabel + ": " + sTool)
    return True


def pictureDescriptions(sManuscript):
    """KDP's accessibility answer about pictures, measured from the manuscript: the start of the label KDP shows for all, some or
    none of the informative pictures having a description. A book without pictures has nothing undescribed, so it is all."""
    if not os.path.exists(sManuscript): return "i don't know"
    with open(sManuscript, encoding="utf-8-sig") as f: sText = f.read()
    lAlts = re.findall(r"!\[([^\]]*)\]\(", sText)
    iDescribed = sum(1 for s in lAlts if s.strip())
    if not lAlts or iDescribed == len(lAlts): return "all informative images"
    return "some informative images" if iDescribed else "none of the informative images"


def answersFor(dState, dBook, dFile):
    """kdpSubmit's answers dictionary for one existing title, as kdpBooks builds it, with this book's AI answers added."""
    dKdp, dProposed = dFile.get("kdp", {}), dFile.get("proposed", {})
    sPrice = dProposed.get("priceUsd", "").strip()
    return {"title": dKdp.get("title", ""), "subtitle": dKdp.get("subtitle", ""), "author": dKdp.get("author", "") or dBook.get("author", ""), "language": dKdp.get("language", "English"), "editionNumber": dKdp.get("edition", ""),
            "description": dProposed.get("description", "").strip() or dKdp.get("description", ""), "keywords": k.inixList(dProposed.get("keywords", "")) or k.inixList(dKdp.get("keywords", "")),
            "categories": k.inixList(dProposed.get("categories", "")) or k.inixList(dKdp.get("categories", "")),
            "drm": "No", "kdpSelect": dKdp.get("kdpSelect", "No"), "royalty": royaltyFor(sPrice, dKdp.get("royalty", "")), "priceUsd": sPrice or dKdp.get("priceUsd", ""),
            "territories": "All", "aiContent": aiAnswers(dBook), "manuscriptFile": os.path.relpath(dState["epub"], sProject)}


def useReceiptOf(sRoot):
    """Points kdpSubmit's upload receipt at this book's own file, data\\receipts\\<book>.inix."""
    sPath = os.path.join(sProject, "data", "receipts", sRoot + ".inix")
    k.receiptPath = lambda: (os.makedirs(os.path.dirname(sPath), exist_ok=True), sPath)[1]
    return sPath


def openTab(page, sId, sTab):
    """Opens one tab of an existing title and waits for it; False when KDP will not open it (an update in review locks it)."""
    try:
        page.goto(k.c_sTitleSetup + sId + "/" + sTab, wait_until="domcontentloaded")
    except Exception as oError:
        log("Opening the " + sTab + " tab of " + sId + " was interrupted: " + str(oError).splitlines()[0][:160])
    for iTick in range(30):
        time.sleep(1)
        if sId in page.url and k.tabLooksReady(page, sTab): break
        if "bookshelf" in page.url and sId not in page.url: break
    bOpen = sId in page.url and k.tabLooksReady(page, sTab)
    if not bOpen: log("KDP did not open the " + sTab + " tab of " + sId + "; URL " + page.url)
    time.sleep(2)
    return bOpen


def applyDetails(page, lWanted):
    """The Details tab changes kdpBooks makes, through kdpSubmit's routines, for whatever the data file proposes."""
    d = k.dAnswers
    if "description" in lWanted:
        say("Description.")
        k.fillDescription(page)
    if "keywords" in lWanted:
        say(plural(len(d["keywords"]), "keyword") + ".")
        for iIndex, sKeyword in enumerate((d["keywords"] + [""] * 7)[:7]): k.fillText(page, "Keyword " + str(iIndex + 1), ["#data-keywords-" + str(iIndex)], sKeyword)
    if "Adult-only answer" in lWanted:
        say("Adult-only question: No.")
        k.clickRadio(page, "Adult content: No", ["input[name='data[is_adult_content]-radio'][value=false]"])
        time.sleep(2)
    if "categories" in lWanted or "Adult-only answer" in lWanted:
        say("Categories; this takes about a minute.")
        k.closeNotice(page)
        k.chooseCategories(page)
    k.logMessages(page, "details changed")
    return k.saveDraft(page)


def fillContentFor(page, dState, dBook, sAccessibility):
    """The Content tab of an existing title: DRM No with consent, the EPUB when KDP lacks this exact file, the AI answers,
    the accessibility answer, the confirmation box, then Save as Draft. The cover is left as KDP holds it."""
    if not k.onTab(page, "content"): return k.unresolved("Content tab", "not on the Content page (URL " + page.url + ")")
    k.dumpControls(page, "content, before filling")
    say("DRM: No, with the consent box.")
    if not k.setDrm(page, True): k.unresolved("DRM", "No DRM, with its confirmation box, could not be confirmed; the book stays a draft")
    bManuscript, bCover, sJoined = k.uploadsDone(page)
    sName = os.path.basename(dState["epub"])
    if k.assetNeedsUpload("Manuscript", dState["epub"], bManuscript and sName.lower() in sJoined):
        if not k.uploadFile(page, "Manuscript", dState["epub"], c_sContentButton, r"manuscript .*uploaded successfully"): return False
    else:
        say("KDP already holds this EPUB; not uploading it again.")
    dtEnd = datetime.datetime.now() + datetime.timedelta(minutes=c_iProcessingMinutes)
    while datetime.datetime.now() < dtEnd and not k.uploadsDone(page)[0]: time.sleep(10)
    if not k.uploadsDone(page)[0]: k.unresolved("Manuscript", "KDP had not finished processing the EPUB after " + str(c_iProcessingMinutes) + " minutes")
    answerAiMerged(page, dBook)
    say("Accessibility: " + sAccessibility + " have a description.")
    k.chooseAccessibilityRadio(page, sAccessibility)
    if page.locator("[role=checkbox]").count(): k.clickAria(page, "Confirmation that the answers are accurate", "checkbox", "I confirm that my answers are accurate")
    k.confirmAnswers(page)
    k.dumpControls(page, "content, after filling")
    k.logMessages(page, "content filled")
    return k.saveDraft(page)


def surveyBook(page, dState, dFile):
    """Reads one title's Content tab and records what KDP holds in the data file's [kdpContent] section; changes nothing."""
    if not openTab(page, dState["titleId"], "content"): return "locked"
    k.dumpControls(page, "survey of the content tab")
    lMessages = k.pageMessages(page)
    lChosen = page.evaluate("""() => Array.from(document.querySelectorAll('input:checked, select')).map(o => {
        const l = o.labels && o.labels.length ? o.labels[0].innerText : (o.getAttribute('aria-label') || o.name || o.id || '');
        const v = o.tagName === 'SELECT' ? (o.options[o.selectedIndex] ? o.options[o.selectedIndex].text : '') : (o.value || '');
        return (l || '').replace(/\\s+/g, ' ').trim().slice(0, 100) + ' = ' + (v || '').trim().slice(0, 80); })""")
    sManuscript = next((t for t in lMessages if re.search(r"manuscript", t, re.I)), "")
    dFile["kdpContent"] = {"readOn": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "manuscript": sManuscript[:300], "chosen": "\n".join(lChosen[:40]), "messages": "\n".join(t[:200] for t in lMessages[:20])}
    k.writeInix(dState["data"], dFile)
    say(dState["title"][:60] + ": " + (sManuscript[:120] or "no manuscript message shown") + ".")
    return "surveyed"


def recentlySubmitted(sData, iHours=72):
    """Whether kdpUpdate submitted this book within the last iHours. KDP locks a title for its review at once, but its
    Bookshelf can still show it plain Live for an hour or more, so a title that will not open soon after a submission is
    in review, not in trouble. Two records say so, either will do: the [review] updated line in data\\books\\<book>.inix,
    and the [submission] record in data\\receipts\\<book>.inix. Only a submission counts, never an upload alone (8 October
    2026, from an audit by another AI: an upload followed by a failed save had counted as submitted), and a time in the
    future is no evidence."""
    def within(sStamp, sFormat):
        try: nAge = (datetime.datetime.now() - datetime.datetime.strptime(sStamp, sFormat)).total_seconds()
        except ValueError: return False
        return -300 <= nAge < iHours * 3600
    sLine = k.readInix(sData).get("review", {}).get("updated", "") if os.path.exists(sData) else ""
    oMatch = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}) submitted", sLine)
    if oMatch and within(oMatch.group(1), "%Y-%m-%d %H:%M"): return True
    sReceipt = os.path.join(os.path.dirname(os.path.dirname(sData)), "receipts", os.path.basename(sData))
    sAt = k.readInix(sReceipt).get("submission", {}).get("at", "").strip() if os.path.exists(sReceipt) else ""
    return bool(sAt) and within(sAt[:19], "%Y-%m-%d %H:%M:%S")


def noteLive(lStates, dRows, dRowsById):
    """Records when each submitted update is first seen live: the Bookshelf shows the book plain Live, with no update in
    review or publishing, after the submission its receipt records. WHY (8 October 2026): a run knew when it submitted a
    book but never when the update went live; KDP's email ("now live and available") does not settle it, since it adds
    that a republished book's changes follow later. Mastery in Men's Tennis, submitted at 11:36, was live by 12:57, though
    KDP quotes 24 to 72 hours; the receipts now measure it, book by book. Returns the number newly seen live."""
    iLive = 0
    for d in lStates:
        sReceipt = receiptFile(d["root"])
        if not os.path.exists(sReceipt): continue
        dReceipt = k.readInix(sReceipt)
        dSub = dReceipt.get("submission", {})
        if not dSub.get("at") or dSub.get("liveBy"): continue
        r = dRows.get(d["asin"], {}) if d.get("asin") else dRowsById.get(d.get("titleId", ""), {})
        sStatus = r.get("status", "")
        if r.get("review") or not re.search(r"\blive\b", sStatus, re.I) or re.search(r"review|publishing", sStatus, re.I): continue
        dSub["liveBy"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            nHours = (datetime.datetime.now() - datetime.datetime.strptime(dSub["at"][:19], "%Y-%m-%d %H:%M:%S")).total_seconds() / 3600
            dSub["hoursToLive"] = "at most %.1f" % nHours
        except ValueError:
            pass
        k.writeInix(sReceipt, dReceipt)
        log("Live: " + d["root"] + ", submitted " + dSub["at"] + ", seen live " + dSub["liveBy"])
        iLive += 1
    if iLive: say(plural(iLive, "update") + " submitted earlier now live on KDP, recorded in data\\receipts.")
    return iLive


def manuscriptCheck(lMessages):
    """What KDP's own manuscript check said, from the page messages, the latest first: its count of possible spelling
    errors, that it found none, or that it was unavailable; "" when it said nothing. WHY (8 October 2026): KDP reported 14
    possible spelling errors in one book and could not check two others, and a run's outcome list said only "submitted"."""
    for sText in reversed(lMessages):
        oFound = re.search(r"We found (\d+) possible spelling error", sText)
        if oFound: return "KDP found " + oFound.group(1) + " possible spelling error" + ("" if oFound.group(1) == "1" else "s") + "; see its Quality Issues Dashboard"
        if "does not have spelling errors" in sText: return "KDP's manuscript check found no spelling errors"
        if "Manuscript check unavailable" in sText: return "KDP's manuscript check was unavailable"
    return ""


def updateBook(page, dState, dBook):
    """One title, end to end, with kdpSubmit's and kdpBooks' routines. Returns submitted, draft, blocked, locked or unknown."""
    sId = dState["titleId"]
    dFile = k.readInix(dState["data"])
    k.lUnresolved.clear()
    k.lPageMessages.clear()
    k.sBookStatus = "Live"
    useReceiptOf(dState["root"])
    k.dAnswers = answersFor(dState, dBook, dFile)
    lWanted = kb.changesWanted(dFile)
    sAccessibility = pictureDescriptions(dState["manuscript"])
    log("Book " + dState["root"] + ": title ID " + sId + ", EPUB " + dState["epub"] + ", AI " + str(k.dAnswers["aiContent"]) + ", accessibility " + sAccessibility + ", details changes " + (", ".join(lWanted) or "none"))
    if not openTab(page, sId, "details"): return "locked"
    if lWanted:
        say("Details: " + ", ".join(lWanted) + ".")
        if not applyDetails(page, lWanted): return "blocked"
    if not k.saveAndContinue(page, "content"): return "blocked"
    time.sleep(2)
    if not fillContentFor(page, dState, dBook, sAccessibility): return "blocked"
    if not k.saveAndContinue(page, "pricing"):
        # KDP asked for a box, or stayed on the tab without naming any problem (Mastery in Men's Tennis, 18:46, moments before
        # Mastery in Music Genre went through the same way): either way the boxes are checked again and the step tried once more.
        oRefusal = re.compile(r"Consent is required|check the box|confirm your answers|stayed on content", re.I)
        if not any(oRefusal.search(sItem) for sItem in k.lUnresolved): return "blocked"
        say("KDP did not leave the Content tab; checking its boxes again and trying once more.")
        if page.locator("[role=checkbox]").count(): k.clickAria(page, "Confirmation that the answers are accurate", "checkbox", "I confirm that my answers are accurate")
        time.sleep(5)
        k.lUnresolved[:] = [sItem for sItem in k.lUnresolved if not oRefusal.search(sItem)]
        if not k.setDrm(page, True): k.unresolved("DRM", "No DRM, with its confirmation box, could not be confirmed; the book stays a draft")
        k.confirmAnswers(page)
        if not k.saveAndContinue(page, "pricing"): return "blocked"
    sPrice = dFile.get("proposed", {}).get("priceUsd", "").strip()
    if any(s.startswith("price") for s in lWanted) and sPrice:
        say("Price $" + sPrice + " at " + k.dAnswers["royalty"] + ".")
        if k.dAnswers["royalty"] == "70%": k.clickRadio(page, "Royalty 70 percent", ["input[name='data[digital][royalty_rate]-radio'][value='70_PERCENT']"])
        elif k.dAnswers["royalty"] == "35%": k.clickRadio(page, "Royalty 35 percent", ["input[name='data[digital][royalty_rate]-radio'][value='35_PERCENT']"])
        k.fillText(page, "US list price", ["input[name='data[digital][channels][amazon][US][price_vat_inclusive]']"], "%.2f" % float(sPrice))
        time.sleep(2)
    sOutcome = k.finalReview(page)
    if sOutcome == "submitted":
        dReceipt = k.readInix(receiptFile(dState["root"])) if os.path.exists(receiptFile(dState["root"])) else {}
        dReceipt["submission"] = {"at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "epubSha": dState["sha"], "answersKey": dState["answersKey"]}
        os.makedirs(os.path.dirname(receiptFile(dState["root"])), exist_ok=True)
        k.writeInix(receiptFile(dState["root"]), dReceipt)
    dFile = k.readInix(dState["data"])
    sCheck = manuscriptCheck(k.lPageMessages)
    dState["check"] = sCheck
    if sCheck: dFile.setdefault("review", {})["manuscriptCheck"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + " " + sCheck
    dFile.setdefault("review", {})["updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + " " + sOutcome + " by kdpUpdate" + (("; " + "; ".join(k.lUnresolved)) if k.lUnresolved else "")
    k.writeInix(dState["data"], dFile)
    log("UPDATE OUTCOME for " + dState["root"] + ": " + sOutcome)
    return sOutcome


def main():
    sProblem = checkOptions()
    if sProblem:
        print(sProblem + " Nothing was done.")
        return 2
    os.makedirs(os.path.join(sProject, "logs"), exist_ok=True)
    k.sLogPath = os.path.join(sProject, "logs", os.path.basename(sProject) + "-kdpUpdate-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".log")
    log("kdpUpdate.py started; " + c_sVersion + "; script " + os.path.abspath(__file__) + "; kdpSubmit " + k.c_sVersion.split(":")[0] + "; kdpBooks " + kb.c_sVersion.split(":")[0])
    log("Python " + sys.version.split()[0] + " on " + platform.platform() + "; project " + sProject + "; cwd " + os.getcwd() + "; command line " + " ".join(sys.argv))
    log("inix reader: " + ("the kit's, " + k.kitInix().__file__ if k.kitInix() else "kdpSubmit's own"))
    print("kdpUpdate " + c_sVersion.split(":")[0])
    dCatalog = dict(catalog())
    lStates = chosen([bookState(sRoot, dBook) for sRoot, dBook in dCatalog.items()])
    lReady = [d for d in lStates if not d["problems"]]
    lUnchanged = [] if "--republish" in sys.argv or "--survey" in sys.argv or "--list" in sys.argv else [d for d in lReady if d["unchanged"]]
    lReady = [d for d in lReady if d not in lUnchanged]
    for d in lUnchanged: log("Unchanged since its last submission, so not sent: " + d["root"])
    if lUnchanged: say(plural(len(lUnchanged), "book") + " unchanged since its last submission, so not sent again (--republish sends them).")
    for d in lStates: log("Preflight " + d["root"] + ": " + ("ready" if not d["problems"] else "; ".join(d["problems"])))
    if "--list" in sys.argv or not lReady:
        say(plural(len(lReady), "book") + " of " + str(len(lStates)) + " ready to send to KDP:")
        for d in lStates: say("  " + d["title"][:60] + ": " + ("ready" if not d["problems"] else "; ".join(d["problems"])))
        if not lReady and "--list" not in sys.argv: say("Nothing to do. Log: " + k.sLogPath)
        return 0 if "--list" in sys.argv or (lUnchanged and not any(d["problems"] for d in lStates)) else 2
    bSurvey = "--survey" in sys.argv
    sProfile = os.path.join(os.environ.get("LOCALAPPDATA", k.sFolder), "KdpSubmit", "edgeProfile")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        say("Playwright is missing. Run scripts\\kdpUpdate.cmd, which installs it, rather than the .py file directly.")
        return 2
    k.closeLeftovers(sProfile)
    os.makedirs(sProfile, exist_ok=True)
    lResults, lFailed = [], []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(sProfile, channel="msedge", headless=False, args=["--start-maximized"], viewport=None, ignore_default_args=["--enable-automation"])
            page = browser.pages[0] if browser.pages else browser.new_page()
            page.set_default_timeout(20000)
            k.watchBrowser(page)
            say("Opening the KDP Bookshelf in Edge. " + ("Nothing on KDP is changed by a survey." if bSurvey else plural(len(lReady), "book") + " to update" + (", stopping at each saved draft." if "--no-publish" in sys.argv else ", each published when its tabs are saved.")))
            lRows = kb.bookshelfRows(page)
            if lRows is None:
                say("KDP was not signed in within the time allowed. Nothing was changed.")
                return 3
            dRows = {r["asin"]: r for r in lRows if r.get("asin")}
            dRowsById = {r["id"]: r for r in lRows if r.get("id")}
            noteLive(lStates, dRows, dRowsById)
            for iIndex, d in enumerate(lReady):
                r = dRows.get(d["asin"], {}) if d["asin"] else dRowsById.get(d["titleId"], {})
                say(("Surveying " if bSurvey else "Updating ") + str(iIndex + 1) + " of " + str(len(lReady)) + ": " + d["title"][:70] + (" (Bookshelf: " + r.get("status", "") + ")" if r.get("status") else ""))
                if r.get("review") or re.search(r"review|publishing", r.get("status", ""), re.I):
                    # KDP is publishing an update of it, which locks the title; that is a book on its way, not a problem.
                    lResults.append((d["title"], (r.get("status") or "in review").lower() + (", update in review" if r.get("review") else "") + "; KDP locks it until then, so it was skipped"))
                    continue
                if r.get("id") and r["id"] != d["titleId"]: log("The Bookshelf gives title ID " + r["id"] + " where the data file has " + d["titleId"] + "; using the Bookshelf's")
                d["titleId"] = r.get("id") or d["titleId"]
                sOutcome = surveyBook(page, d, k.readInix(d["data"])) if bSurvey else updateBook(page, d, dCatalog[d["root"]])
                if sOutcome == "locked" and recentlySubmitted(d["data"]):
                    lResults.append((d["title"], "submitted recently; KDP still locks it for review, though its Bookshelf may not say so yet"))
                    continue
                lResults.append((d["title"], sOutcome + (("; " + d["check"]) if d.get("check") else "")))
                if sOutcome not in ("submitted", "surveyed") and not (sOutcome == "draft" and "--no-publish" in sys.argv):
                    lFailed.append(d["title"] + ": " + sOutcome + (("; " + "; ".join(k.lUnresolved)) if k.lUnresolved else ""))
            browser.close()
    except Exception as oError:
        log("CRASH: " + traceback.format_exc())
        say("The script hit an error: " + str(oError).splitlines()[0][:200] + ". The details are in the log.")
        return 4
    say("Outcome by book:")
    for sTitle, sOutcome in lResults: say("  " + sTitle[:60] + ": " + sOutcome)
    lSkipped = [d for d in lStates if d["problems"]]
    if lSkipped: say(plural(len(lSkipped), "book") + " not sent, not ready: " + "; ".join(d["title"][:40] for d in lSkipped) + ".")
    if lFailed:
        say(plural(len(lFailed), "book") + " to look at:")
        for s in lFailed: say("  " + s[:300])
    say("Done. Log: " + k.sLogPath)
    # A book stopped before the browser opened counts too (8 October 2026, from an audit by another AI): a run that left
    # a book out for a problem must not end as if everything were done.
    for d in lStates:
        if d["problems"]: lFailed.append(d["title"] + ": not sent -- " + "; ".join(d["problems"]))
    return 5 if lFailed else 0


if __name__ == "__main__":
    sys.exit(main())
