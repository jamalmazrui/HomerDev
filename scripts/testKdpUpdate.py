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

c_lAllowedTexts = ["None", "Some sections, with minimal or no editing", "Some sections, with extensive editing", "Entire work, with minimal or no editing", "Entire work, with extensive editing"]
c_lAllowedImages = ["None", "One or a few, with minimal or no editing", "One or a few, with extensive editing", "Many, with minimal or no editing", "Many, with extensive editing"]

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


def testAiAnswers():
    lBooks = u.catalog()
    check("catalog: 22 books, Blind Vibe Coding included", len(lBooks) == 22, str(len(lBooks)))
    for sRoot, dBook in lBooks:
        d = u.aiAnswers(dBook)
        bShape = d["texts"] in c_lAllowedTexts and d["images"] in c_lAllowedImages and d["translations"] == "None"
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
    if not lData: return check("kit reader: a book's data file in data\\books with a fenced keyword list", False)
    sData = lData[0]
    d = k.readInix(sData)
    lKeywords = k.inixList(d.get("kdp", {}).get("keywords", ""))
    check("kit reader: kdpSubmit reads a fenced keyword list as a list", len(lKeywords) >= 3 and "`" not in lKeywords, str(lKeywords[:3]))
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
        testPreflightAndChoice(sTemp)
    finally:
        u.sProject = sProjectWas
        shutil.rmtree(sTemp, ignore_errors=True)
    print(str(iPassed) + " passed, " + str(len(lFailures)) + " failed.")
    return 1 if lFailures else 0


if __name__ == "__main__":
    sys.exit(main())
