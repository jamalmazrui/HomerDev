"""kdpSubmit.py -- fills in the Kindle Direct Publishing form for Blind Vibe Coding.

HOW IT WORKS. The script drives a real Microsoft Edge window on this PC with Playwright
(Google Chrome with --chrome), using its own browser profile under %LOCALAPPDATA%\\KdpSubmit.
The first run asks you to sign in to KDP in that ordinary browser window, which works with
JAWS and NVDA; the script notices when the Bookshelf appears, and the sign-in is remembered
for later runs. The script never types a password or a one-time code.

It reads configs\\<Book>_KDP.inix in the project folder (the parent of scripts\\) -- the book named by --book, or the
only such file -- checks that every answer it needs
is there and supported, rebuilds the book's EPUB (with buildBooks in a book publishing project, or a build.py) when its
sources are newer than it, opens the existing draft of the book and confirms the draft's title,
enters only the answers that differ from what KDP already holds, uploads the EPUB and cover
when KDP does not hold these exact files (a receipt in logs\\kdpSubmit-receipt.inix records
what was sent), saves a draft after each tab and confirms the save, and then presses
Publish Your Kindle eBook and waits for KDP's acknowledgement. Nothing is reported as done
unless the page showed it.

USAGE
  kdpSubmit.cmd                        every answer from the JSON; publishes when nothing is left to check
  kdpSubmit.cmd --ask                  ask before the permanent Details fields, the Content tab, the Pricing tab, and Publish
  kdpSubmit.cmd --no-publish           do everything but stop with the draft saved
  kdpSubmit.cmd --stop-after details   stop after that tab, draft saved; also content or pricing
  kdpSubmit.cmd --book My_Book       the book whose answers are configs\\My_Book_KDP.inix
  kdpSubmit.cmd --title-id ABCDE12345 --start-at content   restart at the Content (or pricing) tab of that draft
  kdpSubmit.cmd --reupload             upload the EPUB and cover again even if the receipt says KDP has them
  kdpSubmit.cmd --create-new           allow a new title to be created when no draft of the book is found
  kdpSubmit.cmd --inspect              open KDP, wait while you move to a page, record its controls
  kdpSubmit.cmd --copy-profile         try copying your own browser's cookies into the automated profile (browser closed first)
  kdpSubmit.cmd --chrome               use Google Chrome instead of Microsoft Edge
Unknown options stop the script before it does anything.

EXIT CODES  0 submitted and the Bookshelf no longer shows Draft; 2 options, JSON or files wrong;
3 a page timed out; 4 crash; 5 draft kept (asked for, or items left to check); 6 Publish pressed but outcome unknown.

The console is short. Every step, value, question, warning and page message goes to
logs\\<Project>-kdpSubmit-<date>-<time>.log, appended as it happens.
Values of password, code, card and tax fields are never written to the log.
"""

import datetime, glob, json, os, platform, re, shutil, subprocess, sys, time, traceback
PlaywrightTimeout, sync_playwright = TimeoutError, None  # set by loadPlaywright() once the log is open, so an import failure is logged

c_iProcessingMinutes, c_iSaveWaitSeconds, c_iSettleSeconds, c_iSignInMinutes = 20, 45, 20, 15
c_sVersion = "2026-10-08 version 38: DRM that cannot be confirmed off blocks Publish; version 37: an upload is judged only by what KDP says after it, praise and recommendations are not problems, and done means KDP names the file just sent; version 36, from the 11:39 run: KDP took 33 seconds to leave the Details tab after the second Save and Continue, the page was still changing when its messages were read, and the third press landed on the Content tab's own Save and Continue, which moved to Pricing and skipped the EPUB upload, then crashed the control dump; now Save and Continue is never pressed again once the page has left its tab, a run whose messages cannot be read waits for the page to settle before deciding, the Content and Pricing steps open their own tab address when the browser is elsewhere, and a control dump interrupted by a navigation is read again; was version 35: before touching KDP, the EPUB is rebuilt with build.py when it is missing or older than the manuscript or its build files (the 6 October edition added Blind Apps passages), so a run always submits the latest text and a failed build stops the run with exit code 2; was version 34, from the 13:42 run of kdpBooks on 5 October, from the 13:42 run of kdpBooks, which finished twelve books and left four at two categories: Add another category does add a chain, but KDP pre-fills the new chain's top menu with the last chain's first step, so the script saw no empty top menu, pressed Add again, found it disabled and gave up; a chain that appears after Add another category is now used for the next path whether or not it is pre-filled, and the save-and-reopen fallback presses Add another category once the picker is open again; the Remove existing categories? dialog was answered with Continue on the four older books and their categories verified; was version 33, from the 10:43 run of kdpBooks, which chose all three categories on nine books but lost them on three older ones and stopped at two on two more: after Save categories, KDP asks Remove existing categories? on a book whose categories predate the picker, and closeNotice pressed that dialog's Close, throwing the choices away, so the dialog is now answered with its continue button and the buttons seen are logged; and when Add another category is disabled after a finished chain (Self-Help > Memory Improvement), the chosen categories are saved and the picker reopened, which gives a fresh chain for the next path; was version 32, from the 09:15 run of kdpBooks, which chose none or one of three categories on seven books: KDP keeps the menus of saved and reset chains on the page, so a path's first step was looked for after the last filled menu and found a sub-menu instead, where a containing name (Art for Arts & Photography) was taken and the real top menu never used; now the top-level menus are found by content, a new path starts in the last empty one (Add another category is pressed again when there is none), a menu is checked to have taken its option, only an exact name is accepted anywhere, and the wait after a pick is for the menu below to show new options or new boxes to appear, up to 10 seconds, with 15 seconds for the placement box; was version 31: no category is ever replaced by General or by an unrelated name; a path KDP does not offer is dropped and reported with the placements KDP offers there, a path whose placement name is already chosen for the book is skipped as a duplicate (Tennis twice, 19:10 run), and General is ticked only when no proposed path can be chosen at all, since KDP needs one category to save; the console names each category by its whole path; was version 30, from the 17:38 run of kdpBooks: a picker menu is used whether or not it is visible, since KDP hides its native menus behind styled drop-downs (version 29 required visibility and found no first step on three books); a Content tab that KDP leaves by itself no longer waits 30 seconds for DRM radios; was version 29, from the 16:46 run of kdpBooks: the picker's placement boxes are read as they are (KDP reuses the same box elements with new labels when a menu changes, so marking them as seen hid every placement and three books were published with one category); a step is looked for only in menus after the one the last step used; a chain that ends without a placement is dropped and its menus reused after Reset, since Add another category is disabled until the chain is complete; the Content tab's accuracy confirmation boxes are ticked when KDP asks (Confirm your answers are accurate and check the box), and that message now stops Save and Continue instead of being pressed through; a navigation aborted by a hand on the browser no longer crashes the run; DRM is left alone when KDP has already moved past the Content tab; was version 28, from the 15:15 run of kdpBooks: the picker's Reset clears only the newest chain of menus, so the saved chains are removed one by one through their Remove links (they had counted toward the three and hidden Add another category on nine books); the DRM consent box is found by its words (version 27 looked for a literal backslash) after waiting for the Content tab to draw; KDP's Categories update notice is closed before Save as Draft, and a button the ordinary click cannot reach is clicked by script; a path ending above a placement takes General or a placement sharing a word with the path, never an unrelated first one (Gun & Firearm Policy was ticked for Communication Policy); was version 27: the category picker uses only its newest menu and waits for the next menu to draw (on 4 October a History step was matched in the top menu and saved History > General instead of Mathematics > History); a step KDP does not offer is replaced by the nearest offered name, then the General placement, then the first placement, so every path ends on a placement and the book keeps three categories, with the paths chosen reported; the DRM No choice also ticks KDP's new consent box (Consent is required when not applying Digital Rights Management); page messages read during a navigation no longer crash the run; was version 26: the Bookshelf row's labels are all read, so Live followed by Updates in review stops the run before the setup page, and an aborted navigation to that page is treated as the same lock rather than a crash (the 16:42 run); was version 25: a live book with updates in review is reported as such and left alone until the update is live; was version 24: publishes unless KDP refused a save or a file failed to upload; everything else unconfirmed is listed to check afterwards; was version 23: the royalty radio selector is quoted (the 15:05 run crashed on it one step before Publish); a submission acknowledged by KDP counts as submitted even when the Bookshelf label cannot be read; was version 22: the accessibility radio is chosen by its label, since KDP briefly gives all four the same value after an upload; the release option and a missing Bookshelf status no longer count as problems; a processed upload is recognized by file name; was version 21: the Draft2Digital section no longer leaks into KDP's ISBN and publisher; saved categories are kept without opening the picker; KDP's spelling notice is not treated as a refusal; was version 20: .inix answers, Homer layout"
c_lProfileSkip = ["Cache", "Code Cache", "GPUCache", "Service Worker", "DawnCache", "GrShaderCache", "ShaderCache", "blob_storage", "File System", "IndexedDB", "Session Storage", "Storage", "Extensions", "Extension State", "Extension Rules", "optimization_guide_hint_cache_store", "Platform Notifications"]
c_lListKeys = ["afterPublishing", "categories", "contributors", "keywords", "priceReasoning", "recommended"]  # .inix keys whose value is a list: one item per line, or comma-separated on one line
c_lNestedSections = ["accessibility", "aiContent", "draft2digital", "notes"]  # .inix sections kept as dictionaries under their own name; every other section is flattened into the answers. draft2digital holds another store's answers (its isbn and publisher once overrode KDP's and KDP refused the save)
c_sBookshelfUrl, c_sTitleSetup = "https://kdp.amazon.com/en_US/bookshelf", "https://kdp.amazon.com/en_US/title-setup/kindle/"
# NO BOOK OF ITS OWN (8 October 2026, when these tools moved into the HomerDev kit): the answers file, its JSON
# predecessor, the log's name and the draft's title ID come from the project and the book, never from the script.
c_sKnownTitleId = ""
# c_dCategoryFixes corrects paths from an older JSON to the names KDP's picker used on 2 October 2026 (the JSON itself now carries the new names).
c_dCategoryFixes = {"Kindle eBooks > Computers & Technology > Computer Science > Artificial Intelligence": "Kindle eBooks > Computers & Technology > Computer Science > Artificial Intelligence > Generative AI", "Kindle eBooks > Computers & Technology > Web Development & Design > User Experience & Usability": "Kindle eBooks > Computers & Technology > Web Development > User Experience & Usability"}

bYes = "--ask" not in sys.argv  # questions are asked only with --ask; the JSON answers stand otherwise
dAnswers = {}
lLog = []
lUnresolved = []
sStatusText = ""  # the Bookshelf's words around the status, for precise messages
sBookStatus = ""  # Bookshelf status read before the run: Draft, In Review, Publishing, Live, Blocked or not shown
sFolder = os.path.dirname(os.path.abspath(__file__))
sProject = os.path.dirname(sFolder) if os.path.basename(sFolder).lower() in ("scripts", "tools") else sFolder  # Homer layout: the script lives in scripts\, the project is its parent
sLogPath = ""


# A BROWSER MESSAGE ONCE, NOT A THOUSAND TIMES (kit 1.64.6): KDP's own pages log the
# same 404 again and again -- 1,187 of one 13,858-line log on 8 October 2026. Each
# distinct message is written its first three times, then counted at 10, 100 and
# 1,000, so nothing is hidden and the log stays readable.
dBrowserSeen = {}


def logBrowserEntry(d):
    dEntry = d.get("entry", {})
    if dEntry.get("level") not in ("error", "warning"): return
    sText = "BROWSER log " + dEntry.get("level", "") + ": " + str(dEntry.get("text", ""))[:160]
    iSeen = dBrowserSeen.get(sText, 0) + 1
    dBrowserSeen[sText] = iSeen
    if iSeen <= 3: log(sText)
    elif iSeen in (10, 100, 1000): log("%s -- seen %d times so far" % (sText, iSeen))


def kitInix():
    """The HomerDev kit's inix module, which reads and writes every form of the format (help\\Inix.md in the kit), or None when
    the kit is not on this PC. Book projects share data files written by the kit's writer, with values between backtick fences
    that this script's own reader, kept below as the fallback, would misread (7 October 2026, from MyBooks)."""
    global oKitInix
    if oKitInix is not None: return oKitInix or None
    oKitInix = False
    for sDir in [os.environ.get("HomerDev", ""), os.environ.get("HOMERDEV", ""), r"C:\HomerDev"]:
        sPython = os.path.join(sDir, "exec", "Python") if sDir else ""
        if sPython and os.path.isfile(os.path.join(sPython, "inix.py")):
            if sPython not in sys.path: sys.path.insert(0, sPython)
            try:
                import inix as oModule
                oKitInix = oModule
            except Exception as oError:
                log("The kit's inix.py at " + sPython + " could not be loaded: " + str(oError)[:120] + "; using this script's own reader")
            break
    return oKitInix or None


oKitInix = None


def readInix(sPath):
    oKit = kitInix()
    if oKit: return oKit.readInix(sPath)
    return readInixOwn(sPath)


def readInixOwn(sPath):
    """Reads an .inix file into {section: {key: value}}. Rules of the dialect this script reads and writes (see help\\Inix.md):
    [section] lines start a section; key = value is one value; a key line with nothing after the equals sign starts a block value
    that runs, kept exactly as written, until the next key line, section line or end of file (blank lines inside it are kept,
    blank lines at its end are dropped); lines starting with ; or # outside a block are comments; a line of a block that would
    read as a key line is written with one leading space, which the reader removes."""
    dSections, sSection, sKey, lBlock, bBlock = {}, "", "", [], False
    oKeyLine = re.compile(r"^([A-Za-z_][\w.\-]*)\s*=(.*)$")
    def closeBlock():
        if sKey and bBlock:
            while lBlock and not lBlock[-1].strip(): lBlock.pop()
            dSections[sSection][sKey] = "\n".join(lBlock)
    with open(sPath, encoding="utf-8-sig") as f:
        for sLine in f.read().replace("\r\n", "\n").split("\n"):
            if bBlock and sLine.startswith(" ") and oKeyLine.match(sLine[1:]):
                lBlock.append(sLine[1:])  # an escaped line of a block value
                continue
            sTrim = sLine.strip()
            if sTrim.startswith("[") and sTrim.endswith("]"):
                closeBlock()
                sSection, sKey, bBlock = sTrim[1:-1].strip(), "", False
                dSections.setdefault(sSection, {})
                continue
            oMatch = oKeyLine.match(sLine)
            if oMatch:
                closeBlock()
                dSections.setdefault(sSection, {})
                sKey, sValue = oMatch.group(1), oMatch.group(2)
                if sValue.strip() == "":
                    bBlock, lBlock = True, []
                else:
                    bBlock = False
                    dSections[sSection][sKey] = sValue.strip()
                continue
            if bBlock:
                lBlock.append(sLine)
            elif sTrim.startswith((";", "#")) or not sTrim:
                continue
            else:
                log("Ignored line outside any key in " + os.path.basename(sPath) + ": " + sLine[:80])
    closeBlock()
    return dSections


def writeInix(sPath, dSections):
    oKit = kitInix()
    if oKit:
        dPlain = {sSection: {sKey: ("\n".join(v) if isinstance(v, list) else str(v)) for sKey, v in dValues.items()} for sSection, dValues in dSections.items()}
        return oKit.writeInix(sPath, dPlain)
    return writeInixOwn(sPath, dSections)


def writeInixOwn(sPath, dSections):
    """Writes {section: {key: value}} as .inix: one line when the value has no newline, a block otherwise. Lists are joined one item per line."""
    lOut = []
    oKeyLine = re.compile(r"^[A-Za-z_][\w.\-]*\s*=")
    for sSection, dKeys in dSections.items():
        lOut.append("[" + sSection + "]")
        for sKey, vValue in dKeys.items():
            if isinstance(vValue, (list, tuple)): vValue = "\n".join(str(v) for v in vValue)
            sValue = "" if vValue is None else str(vValue)
            if "\n" in sValue or (len(sValue) > 0 and oKeyLine.match(sValue)):
                lOut.append(sKey + " =")
                lOut.extend((" " + l if oKeyLine.match(l) else l) for l in sValue.split("\n"))
            else:
                lOut.append(sKey + " = " + sValue)
        lOut.append("")
    with open(sPath, "w", encoding="utf-8-sig", newline="\r\n") as f: f.write("\n".join(lOut))
    return True


def inixList(sValue):
    """A list from an .inix value: one item per line when it holds newlines, else comma-separated; an empty value is an empty list."""
    if not sValue or not sValue.strip(): return []
    if "\n" in sValue: return [l.strip() for l in sValue.split("\n") if l.strip()]
    return [v.strip() for v in sValue.split(",") if v.strip()]


def answersFromInix(dSections):
    """Flattens the KDP answers file into the dictionary the rest of the script uses: every section's keys at the top level,
    except the nested sections (aiContent, accessibility, notes), with list keys parsed into lists."""
    dOut = {}
    for sSection, dKeys in dSections.items():
        if sSection in c_lNestedSections:
            dOut[sSection] = dict(dKeys)
            continue
        for sKey, sValue in dKeys.items():
            dOut[sKey] = inixList(sValue) if sKey in c_lListKeys else sValue
    if "priceUsd" in dOut:
        try: dOut["priceUsd"] = float(dOut["priceUsd"])
        except ValueError: pass
    return dOut


def descriptionHtml(sText):
    """Turns the plain description (paragraphs separated by blank lines, list items starting with '- ', **bold** phrases)
    into the HTML KDP accepts: p, ul, li and b, with &, < and > escaped. No div tags, which KDP rejects."""
    fEscape = lambda t: t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    fBold = lambda t: re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", fEscape(t))
    lHtml = []
    for sPara in re.split(r"\n\s*\n", sText.strip()):
        lLines = [l.rstrip() for l in sPara.split("\n") if l.strip()]
        if lLines and all(l.lstrip().startswith("- ") for l in lLines):
            lHtml.append("<ul>" + "".join("<li>" + fBold(l.lstrip()[2:].strip()) + "</li>" for l in lLines) + "</ul>")
        else:
            lHtml.append("<p>" + fBold(" ".join(l.strip() for l in lLines)) + "</p>")
    return "".join(lHtml)


def answersName():
    """The book's answers file name: <book>_KDP.inix for the book named by --book, or the only *_KDP.inix in configs."""
    sBook = argValue("--book") if "--book" in sys.argv else ""
    if sBook: return sBook + "_KDP.inix"
    lFound = sorted(glob.glob(os.path.join(sProject, "configs", "*_KDP.inix")))
    return os.path.basename(lFound[0]) if len(lFound) == 1 else "Book_KDP.inix"


def logStem():
    """The log's name: the project folder's, then -kdpSubmit."""
    return os.path.basename(sProject) + "-kdpSubmit"


def loadAnswers():
    """Reads configs\\<Book>_KDP.inix (preferred), or the older JSON beside the script or the project, into dAnswers. Returns the path used or ''."""
    global dAnswers
    for sPath in [os.path.join(sProject, "configs", answersName()), os.path.join(sProject, answersName()), os.path.join(sFolder, answersName())]:
        if os.path.exists(sPath):
            dAnswers = answersFromInix(readInix(sPath))
            return sPath
    for sPath in [os.path.join(sProject, "configs", answersName()[:-5] + ".json"), os.path.join(sProject, answersName()[:-5] + ".json"), os.path.join(sFolder, answersName()[:-5] + ".json")]:
        if os.path.exists(sPath):
            with open(sPath, encoding="utf-8-sig") as f: dAnswers = json.load(f)
            return sPath
    return ""


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(sText):
    """Appends one line to the log at once (append and flush), so a crash never loses earlier lines."""
    sLine = now() + " " + re.sub(r"(ap/signin|/ap/)[^\s]*", r"\1...", sText)
    lLog.append(sLine)
    if sLogPath:
        bNew = not os.path.exists(sLogPath)
        with open(sLogPath, "a", encoding="utf-8" if not bNew else "utf-8-sig", newline="\r\n") as f:
            f.write(sLine + "\n")
            f.flush()
    return True


def saveLog():
    return True


def say(sText):
    print(sText)
    log("CONSOLE: " + sText)
    return True


def ask(sQuestion):
    """Yes/no question on the console. Without --ask every question is answered yes from the JSON and logged as AUTO-YES."""
    if bYes:
        log("AUTO-YES: " + sQuestion)
        return True
    sAnswer = input(sQuestion + " Type yes or no, then Enter: ").strip().lower()
    log("ASKED: " + sQuestion + " ANSWER: " + sAnswer)
    return sAnswer in ("y", "yes")


def pause(sMessage):
    print(sMessage)
    log("PAUSE: " + sMessage)
    input("Press Enter here when you are done: ")
    log("Resumed after pause.")
    return True


def argValue(sFlag):
    if sFlag not in sys.argv: return ""
    iIndex = sys.argv.index(sFlag)
    return sys.argv[iIndex + 1] if iIndex + 1 < len(sys.argv) else ""


def unresolved(sWhat, sWhy):
    lUnresolved.append(sWhat + ": " + sWhy)
    log("UNRESOLVED " + sWhat + " -- " + sWhy)
    return False


c_sDeepAll = """(sSelector) => { const lOut = []; const walk = (root) => { for (const e of root.querySelectorAll("*")) { if (e.matches(sSelector)) lOut.push(e); if (e.shadowRoot) walk(e.shadowRoot); } }; walk(document); return lOut; }"""
c_sDeepText = """() => { const l = []; const walk = (n) => { for (const c of n.childNodes) { if (c.nodeType === 3) l.push(c.textContent); else if (c.nodeType === 1 && !/^(SCRIPT|STYLE|NOSCRIPT|TEMPLATE)$/.test(c.tagName)) { if (c.shadowRoot) walk(c.shadowRoot); walk(c); } } }; if (document.body) walk(document.body); return l.join(" ").replace(/\\s+/g, " ").trim(); }"""
c_sDeepHtml = """() => { const ser = (n) => { let s = ""; for (const c of n.childNodes) { if (c.nodeType === 3) s += c.textContent; else if (c.nodeType === 1) { const sTag = c.tagName.toLowerCase(); let sAttr = ""; for (const a of c.attributes) sAttr += " " + a.name + "='" + String(a.value).replace(/'/g, "&#39;") + "'"; s += "<" + sTag + sAttr + ">"; if (c.shadowRoot) s += "<template shadowrootmode='open'>" + ser(c.shadowRoot) + "</template>"; s += ser(c) + "</" + sTag + ">"; } } return s; }; return "<!DOCTYPE html>" + ser(document.documentElement.parentNode); }"""


def deepText(page):
    """The page's text including the text inside shadow roots, which innerText and page.content() leave out; Author Central draws its
    book cards and buttons inside such roots, which is why the 11:56 run saw '1 EDITIONS' and 'ADDED' but no titles and no buttons."""
    try:
        return page.evaluate(c_sDeepText) or ""
    except Exception as oError:
        log("deepText raised " + str(oError)[:100])
        return ""


def deepHtml(page):
    """The page's HTML with every shadow root written out as a template element, for saving."""
    try:
        return page.evaluate(c_sDeepHtml) or page.content()
    except Exception as oError:
        log("deepHtml raised " + str(oError)[:100])
        return page.content()


def dumpControls(page, sLabel, bRetry=True):
    """Writes every visible form control on the page to the log, so a mismatch can be fixed. A page that changes while it is read is read once more after it settles."""
    try:
        lRows = controlRows(page)
    except Exception as oError:
        if not bRetry or "destroyed" not in str(oError): raise
        log("dumpControls: the page changed while it was read (" + str(oError).splitlines()[0][:120] + "); waiting and reading again")
        try:
            page.wait_for_load_state("domcontentloaded", timeout=20000)
        except Exception: pass
        time.sleep(3)
        return dumpControls(page, sLabel, False)
    log("CONTROLS ON PAGE (" + sLabel + "): " + str(len(lRows)) + " -- tag | type | id | name | label | value | checked")
    for sRow in lRows: log("  " + sRow)
    return True


def controlRows(page):
    """The visible form controls of the page as log rows."""
    return page.evaluate("""() => {
        const lOut = [];
        const lAll = []; const walk = (root) => { for (const e of root.querySelectorAll("*")) { if (e.matches("input, select, textarea, button, a[href], [role=radio], [role=checkbox], [role=combobox], [role=button], [role=link], [contenteditable=true], h5")) lAll.push(e); if (e.shadowRoot) walk(e.shadowRoot); } }; walk(document);  // shadow roots included
        for (const o of lAll) {
            const r = o.getBoundingClientRect();
            if (r.width === 0 && r.height === 0) continue;
            let sLabel = "";
            if (o.labels && o.labels.length) sLabel = o.labels[0].innerText;
            const sBy = o.getAttribute("aria-labelledby");
            if (!sLabel && sBy) { const e = document.getElementById(sBy.split(" ")[0]); if (e) sLabel = e.innerText; }
            if (!sLabel && o.closest("label")) sLabel = o.closest("label").innerText;
            const sIdName = ((o.id || "") + " " + (o.name || "") + " " + (o.autocomplete || "") + " " + (sLabel || "")).toLowerCase();
            const bSecret = o.type === "password" || /passw|otp|one-time|verification code|mfa|card|cvv|ssn|tax|routing|account number|iban|secret|token/.test(sIdName);
            const sValue = o.value === undefined ? "" : (bSecret ? "[redacted]" : String(o.value).slice(0, 60));
            lOut.push([o.tagName.toLowerCase(), o.type || o.getAttribute("role") || "", o.id || "", o.name || "", (sLabel || o.getAttribute("aria-label") || o.innerText || o.placeholder || "").trim().replace(/\\s+/g, " ").slice(0, 90), sValue, o.checked === undefined ? "" : String(o.checked)].join(" | "));
        }
        return lOut;
    }""")


def pageMessages(page):
    """Collects alert, error and status texts shown on the page. A page that is changing under the script (its execution context destroyed
    by a navigation, as at the ICT Standards book on 4 October 2026) gives an empty list instead of a crash."""
    try:
        lTexts = page.evaluate("""() => {
        const lOut = [];
        for (const o of document.querySelectorAll("[role=alert], .a-alert-content, [class*=error-message], [class*=errorMessage], [class*=warning], [class*=success], [class*=status], [data-status]")) {
            const r = o.getBoundingClientRect();
            if (r.width === 0 && r.height === 0) continue;
            const s = (o.innerText || "").trim();
            if (s && s.length < 600 && !lOut.includes(s)) lOut.push(s);
        }
        return lOut;
    }""")
    except Exception as oError:
        log("pageMessages could not read the page (it was changing): " + str(oError).splitlines()[0][:120])
        return []
    return [s for s in lTexts if s]


lPageMessages = []  # every message logMessages has seen, so a caller can read what KDP said (kdpUpdate's manuscript check)


def logMessages(page, sWhen):
    lTexts = pageMessages(page)
    lPageMessages.extend(lTexts)
    log("PAGE MESSAGES " + sWhen + ": " + (str(len(lTexts)) if lTexts else "none"))
    for sText in lTexts: log("  MESSAGE: " + sText.replace("\n", " / "))
    return lTexts


def firstVisible(page, lSelectors):
    for sSelector in lSelectors:
        try:
            oAll = page.locator(sSelector)
            for iIndex in range(oAll.count()):  # a published book can show a hidden disabled copy of a field beside the live one
                oLocator = oAll.nth(iIndex)
                if oLocator.is_visible(): return oLocator
        except Exception as oError:
            log("selector " + sSelector + " raised " + str(oError)[:120])
    return None


def fillText(page, sWhat, lSelectors, sValue):
    oField = firstVisible(page, lSelectors)
    if oField is None: return unresolved(sWhat, "no visible field matched " + " or ".join(lSelectors))
    sBefore = oField.input_value()
    if sBefore.strip() == sValue.strip():
        log("KEPT " + sWhat + " = " + sValue + " (already saved)")
        return True
    if not oField.is_enabled() or oField.get_attribute("readonly") is not None:
        return unresolved(sWhat, "KDP has locked this field (the book is published), and it holds '" + sBefore[:80] + "' rather than '" + sValue + "'")
    oField.click()
    oField.fill(sValue)
    oField.press("Tab")
    sNow = oField.input_value()
    log("FILLED " + sWhat + " = " + sValue + ("" if sBefore == "" else " (was: " + sBefore + ")"))
    if sNow.strip() != sValue.strip(): return unresolved(sWhat, "field holds '" + sNow[:80] + "' after filling")
    return True


def setNativeSelect(page, sWhat, sSelector, sValue):
    """Sets a hidden native select behind an Amazon dropdown by value or option text, then fires change."""
    bDone = page.evaluate("""([sSelector, sValue]) => {
        const l = Array.from(document.querySelectorAll(sSelector));
        const o = l.find(x => !x.disabled) || l[0];  // a published book shows a disabled copy of some selects beside the live one
        if (!o) return false;
        for (const opt of o.options) {
            if (opt.value.toLowerCase() === sValue.toLowerCase() || opt.text.trim().toLowerCase() === sValue.toLowerCase()) {
                if (o.value === opt.value) return "kept";
                o.value = opt.value;
                o.dispatchEvent(new Event("change", {bubbles: true}));
                return true;
            }
        }
        return false;
    }""", [sSelector, sValue])
    log(("KEPT " if bDone == "kept" else "SELECTED " if bDone else "COULD NOT SELECT ") + sWhat + " = " + sValue + " via " + sSelector + (" (already saved)" if bDone == "kept" else ""))
    if not bDone: unresolved(sWhat, "no option " + sValue + " in " + sSelector)
    return bDone


def clickRadio(page, sWhat, lSelectors):
    """Clicks the label around a radio or checkbox input, which Amazon styles over the real input."""
    for sSelector in lSelectors:
        oInput = page.locator(sSelector).first
        if not oInput.count(): continue
        if oInput.is_checked():
            log(sWhat + " already set (" + sSelector + ")")
            return True
        oLabel = oInput.locator("xpath=ancestor::label[1]")
        (oLabel.first if oLabel.count() else oInput).click(force=True)
        time.sleep(0.5)
        if oInput.is_checked():
            log("CHOSE " + sWhat + " (" + sSelector + ")")
            return True
    return unresolved(sWhat, "no radio matched " + " or ".join(lSelectors))


c_sDrmBoxesScript = """() => {
  const lOut = [];
  const lBoxes = Array.from(document.querySelectorAll("input[type=checkbox], [role=checkbox]"));
  lBoxes.forEach((o, i) => {
    const r = o.getBoundingClientRect();
    const sOwn = ((o.getAttribute("aria-label") || "") + " " + (o.labels && o.labels[0] ? o.labels[0].innerText : "") + " " + (o.closest("label") ? o.closest("label").innerText : "") + " " + (o.parentElement ? o.parentElement.innerText || "" : "")).replace(/\\s+/g, " ").trim().slice(0, 200);
    let p = o, bInDrm = false, iUp = 0;
    while (p && iUp < 8) { if (p.querySelector && p.querySelector("input[name='data[is_drm]-radio']")) { bInDrm = p !== document.body && p !== document.documentElement; break; } p = p.parentElement; iUp++; }
    const bChecked = o.checked === undefined ? (o.getAttribute("aria-checked") === "true") : o.checked;
    lOut.push({index: i, text: sOwn, visible: r.width > 0 && r.height > 0, inDrm: bInDrm, checked: bChecked});
  });
  return lOut;
}"""


def setDrm(page, bNoDrm):
    """Sets the Content tab's DRM radio and, for No, ticks the consent box KDP added in 2026: on 4 October 2026 Save and Continue answered
    'Consent is required when not applying Digital Rights Management' on two books. The box is found by its words or by sitting in the
    DRM section; when none is found, every check box on the page is logged so the next version can name it."""
    if "/content" not in page.url:
        log("Not on the Content tab (URL " + page.url + "), so DRM is left as KDP holds it; KDP itself moved past the tab")
        return True
    for iTick in range(30):  # the Content tab draws its controls a few seconds after the address changes; on 4 October 2026 the radio was looked for too soon
        if page.locator("input[name='data[is_drm]-radio']").count(): break
        if "/content" not in page.url:
            log("KDP moved on from the Content tab by itself (URL " + page.url + "), so DRM is left as KDP holds it")
            return True
        time.sleep(1)
    else:
        log("The DRM radios did not appear within 30 seconds")
    clickRadio(page, "DRM", ["input[name='data[is_drm]-radio'][value=" + ("false" if bNoDrm else "true") + "]"])
    if not bNoDrm: return True
    time.sleep(2)
    try:
        lBoxes = page.evaluate(c_sDrmBoxesScript)
    except Exception as oError:
        log("The check boxes could not be read: " + str(oError).splitlines()[0][:120])
        return True
    log("Check boxes on the Content tab: " + "; ".join(("[DRM section] " if d["inDrm"] else "") + (d["text"][:80] or "(no text)") + (" checked" if d["checked"] else "") for d in lBoxes if d["visible"]))
    lFits = [d for d in lBoxes if d["visible"] and (d["inDrm"] or re.search(r"digital rights|\bDRM\b|consent", d["text"], re.I)) and not re.search(r"answers are accurate", d["text"], re.I)]
    if not lFits:
        log("No DRM consent box found on the page; if KDP asks for consent, the control list above is the clue")
        return True
    for d in lFits:
        if d["checked"]:
            log("DRM consent already ticked: " + d["text"][:100])
            continue
        oBox = page.locator("input[type=checkbox], [role=checkbox]").nth(d["index"])
        oLabel = oBox.locator("xpath=ancestor::label[1]")
        say("Ticking the DRM consent box.")
        (oLabel.first if oLabel.count() else oBox).click(force=True)
        time.sleep(1)
        bNow = oBox.evaluate("o => o.checked === undefined ? o.getAttribute('aria-checked') === 'true' : o.checked")
        log("TICKED DRM consent: " + d["text"][:100] + (" (checked)" if bNow else " (NOT checked)"))
        if not bNow: oBox.check(force=True)
    return True


def confirmAnswers(page):
    """Ticks every unticked 'By clicking this, I confirm that my answers are accurate' box on the Content tab. KDP shows one under the
    AI-content questions and one under the accessibility questions, and asks for them again after a new upload or a changed answer;
    on 4 October 2026 Save and Continue was refused three times with 'Confirm your answers are accurate and check the box.'"""
    try:
        lIndexes = page.evaluate("""() => {
            const lOut = [];
            Array.from(document.querySelectorAll("[role=checkbox], input[type=checkbox]")).forEach((o, i) => {
                let p = o, sText = "";
                for (let k = 0; k < 4 && p; k++) { sText += " " + (p.innerText || p.getAttribute("aria-label") || ""); p = p.parentElement; }
                const r = o.getBoundingClientRect();
                const bChecked = o.checked === undefined ? o.getAttribute("aria-checked") === "true" : o.checked;
                if (r.width > 0 && /answers are accurate/i.test(sText) && !bChecked) lOut.push(i);
            });
            return lOut;
        }""")
    except Exception as oError:
        log("confirmAnswers could not read the page: " + str(oError).splitlines()[0][:120])
        return False
    if not lIndexes:
        log("No unticked confirmation box on the Content tab")
        return False
    say("Confirming that the answers are accurate (" + str(len(lIndexes)) + " box" + ("" if len(lIndexes) == 1 else "es") + ").")
    for iIndex in lIndexes:
        oBox = page.locator("[role=checkbox], input[type=checkbox]").nth(iIndex)
        oBox.scroll_into_view_if_needed()
        oBox.click(force=True)
        time.sleep(1)
        log("TICKED confirmation box " + str(iIndex) + ": now " + str(oBox.evaluate("o => o.checked === undefined ? o.getAttribute('aria-checked') : o.checked")))
    return True


def clickAria(page, sWhat, sRole, sText, bWantChecked=True):
    """Clicks a div-based radio or check box (role=radio or role=checkbox) whose own text, or its nearest container's text, holds sText."""
    oHandle = page.evaluate_handle("""([sRole, sText]) => {
        const sWant = sText.toLowerCase();
        const lAll = Array.from(document.querySelectorAll("[role=" + sRole + "]"));
        const fText = o => (o.innerText || o.getAttribute("aria-label") || "").trim().toLowerCase();
        let o = lAll.find(o => fText(o) === sWant) || lAll.find(o => { const p = o.parentElement; return p && fText(p).startsWith(sWant); }) || lAll.find(o => { let p = o; for (let i = 0; i < 4 && p; i++) { p = p.parentElement; if (p && fText(p).includes(sWant)) return true; } return false; });
        return o || null;
    }""", [sRole, sText])
    oElement = oHandle.as_element()
    if oElement is None: return unresolved(sWhat, "no " + sRole + " with the text " + sText)
    sWant = "true" if bWantChecked else "false"
    sState = oElement.get_attribute("aria-checked") or "false"
    if sState == sWant:
        log(sWhat + " already " + ("set" if bWantChecked else "clear") + " (" + sText + ")")
        return True
    oElement.scroll_into_view_if_needed()
    oElement.click(force=True)
    time.sleep(1.5)
    sState = oElement.get_attribute("aria-checked") or "false"
    log("CLICKED " + sWhat + " = " + sText + " (aria-checked now " + sState + ", wanted " + sWant + ")")
    if sState != sWant: return unresolved(sWhat, "state is " + sState + " after clicking; wanted " + sWant)
    return True


def waitForRadio(page, sSelector, iSeconds=60):
    dtEnd = datetime.datetime.now() + datetime.timedelta(seconds=iSeconds)
    while datetime.datetime.now() < dtEnd:
        if page.locator(sSelector).count(): return True
        time.sleep(2)
    return False


def clickLabel(page, sWhat, lTexts, sRole="radio"):
    """Chooses a radio or checkbox whose label text contains one of lTexts."""
    for sText in lTexts:
        for oLocator in [page.get_by_role(sRole, name=re.compile(re.escape(sText), re.I)), page.get_by_label(re.compile(re.escape(sText), re.I)), page.locator("label", has_text=re.compile(re.escape(sText), re.I))]:
            try:
                if oLocator.count() and oLocator.first.is_visible():
                    oLocator.first.click()
                    log("CHOSE " + sWhat + " = " + sText)
                    return True
            except Exception as oError:
                log("clickLabel " + sText + " raised " + str(oError)[:120])
    return unresolved(sWhat, "no visible " + sRole + " labelled " + " or ".join(lTexts))


def clickButton(page, sWhat, lSelectorsOrTexts, bRequired=True):
    """Clicks the first match; an entry starting with # or . is a selector, anything else is button text."""
    for sEntry in lSelectorsOrTexts:
        if sEntry[:1] in "#.[":
            oLocator = page.locator(sEntry)
        else:
            oLocator = page.get_by_role("button", name=re.compile(re.escape(sEntry), re.I))
            if not oLocator.count(): oLocator = page.get_by_role("link", name=re.compile(re.escape(sEntry), re.I))
            if not oLocator.count(): oLocator = page.locator("button, a, input[type=submit], span.a-button-text, h5", has_text=re.compile(re.escape(sEntry), re.I))
        try:
            if oLocator.count() and oLocator.first.is_visible():
                oLocator.first.click()
                log("CLICKED " + sWhat + " (" + sEntry + ")")
                page.wait_for_load_state("domcontentloaded")
                time.sleep(2)
                return True
        except Exception as oError:
            log("clickButton " + sEntry + " raised " + str(oError).replace("\n", " / ")[:400])
            try:  # a button present but covered or unsettled, as Save as Draft was behind the Categories update notice on 4 October 2026, is clicked by script
                if oLocator.count() and oLocator.first.is_disabled():
                    log(sWhat + " is disabled, so it is not pressed")
                elif oLocator.count():
                    closeNotice(page)
                    oLocator.first.evaluate("o => o.click()")
                    log("CLICKED " + sWhat + " (" + sEntry + ") by script, since the ordinary click did not go through")
                    page.wait_for_load_state("domcontentloaded")
                    time.sleep(2)
                    return True
            except Exception as oError2:
                log("the script click raised " + str(oError2).replace("\n", " / ")[:200])
    if bRequired: unresolved(sWhat, "nothing visible matched " + " or ".join(lSelectorsOrTexts))
    return False


def closeNotice(page):
    """Closes KDP's Categories update notice when it is showing. On 4 October 2026, on books whose categories predated KDP's
    three-category picker, Save categories left a notice ("Categories update: You can now choose three categories...") with a
    Close button that took the focus, and Save as Draft could not be pressed behind it."""
    try:
        if not re.search(r"Categories update", deepText(page)): return False
        oClose = page.get_by_role("button", name=re.compile("^\\s*Close\\s*$", re.I))
        for iIndex in range(oClose.count()):
            if oClose.nth(iIndex).is_visible():
                oClose.nth(iIndex).click(force=True)
                time.sleep(1)
                log("CLOSED the Categories update notice")
                return True
        page.keyboard.press("Escape")
        log("Categories update notice has no visible Close button; pressed Escape")
    except Exception as oError:
        log("closeNotice: " + str(oError).splitlines()[0][:160])
    return False


def confirmRemoveExisting(page):
    """Answers KDP's 'Remove existing categories?' question, which appears after Save categories on a book whose categories
    predate the three-category picker. On 5 October 2026 the Close button of that dialog was pressed by closeNotice and the new
    categories were thrown away on three books; the dialog's continue button is pressed instead, and the buttons seen are logged."""
    try:
        time.sleep(1.5)
        if not re.search(r"Remove existing categories", deepText(page)): return False
        oButtons = page.get_by_role("button")
        lNames = [(oButtons.nth(i).inner_text() or oButtons.nth(i).get_attribute("aria-label") or "").strip() for i in range(oButtons.count()) if oButtons.nth(i).is_visible()]
        log("Remove existing categories? dialog; visible buttons: " + "; ".join(n for n in lNames if n))
        for sPattern in ["^\\s*Continue\\s*$", "^\\s*Remove (existing )?categories", "^\\s*Remove and continue", "^\\s*Confirm", "^\\s*Yes", "^\\s*OK\\s*$"]:  # never a bare Remove, which is the link beside each saved chain
            oButton = page.get_by_role("button", name=re.compile(sPattern, re.I))
            for iIndex in range(oButton.count()):
                if oButton.nth(iIndex).is_visible():
                    oButton.nth(iIndex).click(force=True)
                    time.sleep(2)
                    log("CONFIRMED the removal of the old categories with the button matching " + sPattern)
                    return True
        log("Remove existing categories? dialog has no continue button among: " + "; ".join(lNames))
    except Exception as oError:
        log("confirmRemoveExisting: " + str(oError).splitlines()[0][:160])
    return False


def saveDraft(page):
    """Presses Save as Draft and returns True only when KDP reports the save."""
    closeNotice(page)
    if not clickButton(page, "Save as Draft", ["#save-announce", "Save as Draft"], True): return False
    for iTick in range(10):
        lTexts = pageMessages(page)
        if any("save successful" in t.lower() for t in lTexts): break
        time.sleep(1)
    lTexts = logMessages(page, "after Save as Draft")
    if not any("save successful" in t.lower() for t in lTexts):
        lProblems = [t for t in lTexts if re.search(r"fix the highlighted|must|required|invalid|error", t, re.I) and not re.search(r"possible spelling errors", t, re.I)]
        return unresolved("Save as Draft", "KDP did not report Save Successful" + ("; it says: " + " | ".join(lProblems)[:300] if lProblems else ""))
    log("Save as Draft confirmed by KDP")
    return True


def tabLooksReady(page, sExpected):
    """True when the page shows a control that belongs to the expected tab, so a URL alone is never trusted."""
    dMarkers = {"content": "input[type=file], input[name*='drm'], #data-is-drm, [id*='manuscript']", "pricing": "#data-is-select, input[id*='price'], input[name*='price']", "details": "#data-title"}
    try:
        return page.locator(dMarkers.get(sExpected, "body")).count() > 0
    except Exception as oError:
        log("tabLooksReady raised " + str(oError)[:120])
        return False


def saveAndContinue(page, sExpected):
    """Presses Save and Continue and checks that KDP moved to the next tab. KDP stays put when a field is rejected, but on
    3 October 2026 it also stayed put after a successful save of a published book until the button was pressed again, so the
    script now waits up to 30 seconds, presses again when KDP reported Save Successful without an error, and finally opens
    the next tab's own address, which is the same as the tab link, since the draft is already saved."""
    sBefore = page.url
    sTitleId = titleIdFrom(page.url)
    for iAttempt in range(1, 4):
        if sBefore.split("/")[-1] not in page.url.split("/")[-1]:
            log("The page has already left " + sBefore.split("/")[-1] + " (URL now " + page.url + "); Save and Continue is not pressed again")
            break
        clickButton(page, "Save and Continue (attempt " + str(iAttempt) + ")", ["#save-and-continue-announce", "Save and Continue"])
        for iTick in range(c_iSaveWaitSeconds):
            if "/" + sExpected in page.url: break
            time.sleep(1)
        lTexts = logMessages(page, "after Save and Continue, attempt " + str(iAttempt))
        if not lTexts and "/" + sExpected not in page.url:
            # The page may be changing under the script: on 6 October 2026 KDP took 33 seconds to leave Details after the second press, the messages could not be read, and a third press landed on the Content tab's own Save and Continue, which skipped that tab.
            log("No messages could be read; waiting for the page to settle before deciding")
            try:
                page.wait_for_load_state("domcontentloaded", timeout=20000)
            except Exception as oError:
                log("Waiting for the page to settle raised " + str(oError).splitlines()[0][:120])
            for iTick in range(c_iSettleSeconds):
                if "/" + sExpected in page.url: break
                time.sleep(1)
        log("URL now " + page.url)
        if "/" + sExpected in page.url: break
        lErrors = [t for t in lTexts if re.search(r"fix the highlighted|must |required|invalid|error|unsupported|remove any|check the box|confirm your answers", t, re.I) and not re.search(r"possible spelling errors", t, re.I)]  # KDP's spelling notice is advice, not a refusal
        if lErrors:
            unresolved("Save and Continue to " + sExpected, "KDP stayed on " + sBefore.split("/")[-1] + " and says: " + " | ".join(lErrors)[:400])
            say("KDP did not accept the tab. Its messages: " + " | ".join(lErrors) + ". Stopping here with the draft saved.")
            return False
        log("KDP stayed on " + sBefore.split("/")[-1] + " without an error message (" + " | ".join(lTexts)[:200] + "); pressing Save and Continue again")
        time.sleep(3)
    if "/" + sExpected not in page.url and sTitleId:
        sTarget = c_sTitleSetup + sTitleId + "/" + sExpected
        log("Save and Continue did not move on; the draft is saved (KDP said Save Successful), so opening the " + sExpected + " tab directly at " + sTarget)
        try:
            page.goto(sTarget)
            page.wait_for_load_state("domcontentloaded")
        except Exception as oError:  # a hand on the browser at the same moment (Save and Continue pressed by the user on 4 October 2026) aborts the script's own navigation
            log("Opening the " + sExpected + " tab directly was interrupted: " + str(oError).splitlines()[0][:160])
        time.sleep(4)
        logMessages(page, "after opening the " + sExpected + " tab directly")
    if "/" + sExpected not in page.url or not tabLooksReady(page, sExpected):
        unresolved("Save and Continue to " + sExpected, "KDP stayed on " + sBefore.split("/")[-1] + " and the " + sExpected + " tab could not be opened directly either (URL now " + page.url + ")")
        say("KDP would not show the " + sExpected + " tab. Stopping here with the draft saved.")
        return False
    say("Moved on to the " + sExpected + " tab.")
    return True


def titleIdFrom(sUrl):
    oMatch = re.search(r"title-setup/kindle/([A-Z0-9]+)/", sUrl)
    return oMatch.group(1) if oMatch else ""


def signedIn(page):
    """True when any open tab shows a KDP page other than the sign-in page."""
    for oPage in page.context.pages:
        sUrl = oPage.url
        if "kdp.amazon.com" in sUrl and "signin" not in sUrl and "/ap/" not in sUrl: return True
    return False


def waitForSignIn(page):
    if signedIn(page): return True
    try:
        page.bring_to_front()
    except Exception as oError:
        log("bring_to_front raised " + str(oError)[:120])
    say("KDP wants a sign-in. The automated browser window is on the Amazon sign-in page and is the window Alt+Tab reaches first. Sign in there, not in another browser window, then come back here. I never type passwords or codes.")
    say("Waiting up to " + str(c_iSignInMinutes) + " minutes. Every 30 seconds I quietly check whether the sign-in has taken, without touching the page you are typing in.")
    dtEnd = datetime.datetime.now() + datetime.timedelta(minutes=c_iSignInMinutes)
    iTick = 0
    while datetime.datetime.now() < dtEnd:
        time.sleep(3)
        iTick += 3
        if signedIn(page):
            log("Signed in; URLs " + str([o.url[:100] for o in page.context.pages]))
            say("Signed in. Carrying on.")
            return True
        if not page.context.pages:
            say("The automated browser window was closed, so I cannot continue. Run the script again and sign in inside the window it opens.")
            return False
        if iTick % 30 == 0:
            log("Still waiting; URLs " + str([o.url[:100] for o in page.context.pages]))
            try:
                oResponse = page.context.request.get(c_sBookshelfUrl, max_redirects=5)
                log("Quiet Bookshelf check: status " + str(oResponse.status) + ", landed on " + oResponse.url[:100])
                if "kdp.amazon.com" in oResponse.url and "signin" not in oResponse.url and "/ap/" not in oResponse.url:
                    page.goto(c_sBookshelfUrl)
                    page.wait_for_load_state("domcontentloaded")
                    time.sleep(2)
                    if signedIn(page):
                        say("Signed in. Carrying on.")
                        return True
            except Exception as oError:
                log("quiet check raised " + str(oError)[:120])
    say("No sign-in after " + str(c_iSignInMinutes) + " minutes. Stopping; run the script again when ready.")
    return False


c_sWatchScript = """(() => {
  if (window.__homerWatching) return; window.__homerWatching = true;
  const sLabel = (o) => { if (!o || !o.tagName) return ""; const s = (o.getAttribute && (o.getAttribute("aria-label") || "")) || (o.labels && o.labels[0] ? o.labels[0].innerText : "") || o.innerText || o.value || o.placeholder || ""; return (o.tagName.toLowerCase() + (o.type ? "[" + o.type + "]" : "") + " " + String(s).replace(/\\s+/g, " ").trim().slice(0, 60)).trim(); };
  const bField = (o) => o && (/^(INPUT|TEXTAREA|SELECT)$/.test(o.tagName) || o.isContentEditable);
  const send = (s) => { try { window.homerEvent(s); } catch (e) {} };
  document.addEventListener("keydown", (e) => {
    const bNamed = e.key.length > 1;  // Enter, Tab, F5, arrows, Escape, Backspace: named keys only; a typed character is never recorded, so nothing typed into a sign-in page can reach the log
    if (!bNamed && !(e.ctrlKey || e.altKey || e.metaKey)) { if (bField(e.target)) return; send("KEY character in " + sLabel(e.target)); return; }
    send("KEY " + (e.ctrlKey ? "Control+" : "") + (e.altKey ? "Alt+" : "") + (e.shiftKey ? "Shift+" : "") + (bNamed ? e.key : "letter") + " in " + sLabel(e.target));
  }, true);
  document.addEventListener("click", (e) => send("CLICK on " + sLabel(e.target.closest("a, button, input, [role=button], [role=link], label") || e.target) + (e.isTrusted ? " (by hand or by the script)" : " (by script)")), true);
  document.addEventListener("focusin", (e) => send("FOCUS " + sLabel(e.target)), true);
  document.addEventListener("visibilitychange", () => send("PAGE " + document.visibilityState));
})();"""


def watchBrowser(page):
    """Records what the browser does and what is done to it, through the Chrome DevTools Protocol and a small script in every page:
    navigations with their reason (reload for F5, anchorClick for a link, scriptInitiated for the site), the lifecycle of each page
    (DOMContentLoaded, load, networkIdle), console messages and script errors, failed and document requests, dialogs, and in the page
    itself named key presses (Enter, Tab, F5, arrows; never a typed character), clicks and focus moves with the control they landed on.
    Every line goes to the log as BROWSER ..., so a run with manual nudges can be read afterwards."""
    dMain = {"id": ""}  # filled below; the handlers read it when events arrive (the 11:56 run crashed the watcher because it was assigned after them)
    try:
        oCdp = page.context.new_cdp_session(page)
        oCdp.send("Page.enable")
        oCdp.send("Page.setLifecycleEventsEnabled", {"enabled": True})
        oCdp.send("Runtime.enable")
        oCdp.send("Network.enable")
        oCdp.send("Log.enable")
        oCdp.on("Page.frameRequestedNavigation", lambda d: log("BROWSER navigation requested, reason " + d.get("reason", "?") + ", to " + d.get("url", "")[:140]))
        oCdp.on("Page.frameNavigated", lambda d: log("BROWSER navigated to " + d.get("frame", {}).get("url", "")[:140]) if not d.get("frame", {}).get("parentId") else None)
        oCdp.on("Page.navigatedWithinDocument", lambda d: log("BROWSER moved within the page to " + d.get("url", "")[:140]))
        oCdp.on("Page.lifecycleEvent", lambda d: log("BROWSER lifecycle " + d.get("name", "")) if d.get("name") in ("DOMContentLoaded", "load", "networkIdle") and d.get("frameId") == dMain.get("id") else None)
        oCdp.on("Page.javascriptDialogOpening", lambda d: log("BROWSER dialog " + d.get("type", "") + ": " + d.get("message", "")[:160]))
        oCdp.on("Page.frameStoppedLoading", lambda d: log("BROWSER frame finished loading") if d.get("frameId") == dMain.get("id") else None)
        oCdp.on("Runtime.consoleAPICalled", lambda d: log("BROWSER console." + d.get("type", "") + " " + " ".join(str(a.get("value", a.get("description", "")))[:120] for a in d.get("args", [])[:3])) if d.get("type") in ("error", "warning") else None)
        oCdp.on("Runtime.exceptionThrown", lambda d: log("BROWSER script error: " + str(d.get("exceptionDetails", {}).get("text", ""))[:160]))
        oCdp.on("Log.entryAdded", logBrowserEntry)
        oCdp.on("Network.requestWillBeSent", lambda d: log("BROWSER document request " + d.get("request", {}).get("method", "") + " " + d.get("request", {}).get("url", "")[:140]) if d.get("type") == "Document" else None)
        oCdp.on("Network.loadingFailed", lambda d: log("BROWSER request failed: " + d.get("errorText", "") + (" (" + d.get("type", "") + ")" if d.get("type") else "")) if not d.get("canceled") else None)
        dMain["id"] = oCdp.send("Page.getFrameTree").get("frameTree", {}).get("frame", {}).get("id", "")
        page.context.expose_binding("homerEvent", lambda oSource, sText: log("BROWSER " + str(sText)[:200]))
        page.context.add_init_script(c_sWatchScript)
        page.evaluate(c_sWatchScript)
        log("Browser watching is on: navigations with reasons, page lifecycle, console errors, failed requests, named keys, clicks and focus")
    except Exception as oError:
        log("watchBrowser could not start: " + str(oError)[:160])
    return True


def closeLeftovers(sProfile):
    """Ends browser processes left from an earlier run of this script (they lock the copied profile)."""
    if platform.system() != "Windows": return False
    sCommand = "Get-CimInstance Win32_Process | Where-Object { ($_.Name -eq 'msedge.exe' -or $_.Name -eq 'chrome.exe') -and $_.CommandLine -like '*" + sProfile + "*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; $_.ProcessId }"
    try:
        oResult = subprocess.run(["powershell", "-NoProfile", "-Command", sCommand], capture_output=True, text=True, timeout=60)
        lIds = [s for s in oResult.stdout.split() if s.isdigit()]
        log("Leftover browser processes from earlier runs ended: " + (", ".join(lIds) if lIds else "none"))
    except Exception as oError:
        log("closeLeftovers raised " + str(oError)[:120])
    return True


def browserRunning(sExeName):
    if platform.system() != "Windows": return False
    try:
        oResult = subprocess.run(["tasklist", "/FI", "IMAGENAME eq " + sExeName], capture_output=True, text=True, timeout=30)
        return sExeName.lower() in oResult.stdout.lower()
    except Exception as oError:
        log("tasklist raised " + str(oError)[:120])
        return False


def copyProfile(sSource, sTarget, sExeName):
    """Copies the browser profile's sign-in state (not its caches) so the automated window is signed in.
    The browser locks its Cookies file while it runs, so the user is asked to close it first."""
    if not os.path.isdir(sSource):
        log("No browser profile at " + sSource)
        return False
    closeLeftovers(sTarget)
    time.sleep(2)
    for iAttempt in range(3):
        if browserRunning(sExeName):
            say(sExeName + " is running, and it locks the sign-in cookies while open. Please close every " + sExeName.replace(".exe", "") + " window, then press Enter here. The script reopens the browser itself.")
            input("Press Enter when the browser is closed: ")
            log("User reports browser closed; running now: " + str(browserRunning(sExeName)))
        if os.path.isdir(sTarget): shutil.rmtree(sTarget, ignore_errors=True)
        os.makedirs(os.path.join(sTarget, "Default"), exist_ok=True)
        iCopied, lSkipped = 0, []
        sFrom = os.path.join(sSource, "Local State")
        if os.path.exists(sFrom): shutil.copy2(sFrom, os.path.join(sTarget, "Local State")); iCopied += 1
        sDefaultFrom, sDefaultTo = os.path.join(sSource, "Default"), os.path.join(sTarget, "Default")
        for sName in os.listdir(sDefaultFrom):
            if sName in c_lProfileSkip or sName.lower().startswith("lock"): continue
            sItemFrom, sItemTo = os.path.join(sDefaultFrom, sName), os.path.join(sDefaultTo, sName)
            try:
                if os.path.isdir(sItemFrom):
                    shutil.copytree(sItemFrom, sItemTo, ignore=shutil.ignore_patterns("LOCK", "LOG", "LOG.old", "*.ldb", "*-journal"))
                else:
                    shutil.copy2(sItemFrom, sItemTo)
                iCopied += 1
            except Exception as oError:
                lSkipped.append(sName)
                log("profile copy skipped " + sName + ": " + str(oError)[:160])
        sCookies = os.path.join(sDefaultTo, "Network", "Cookies")
        bCookies = os.path.exists(sCookies) and os.path.getsize(sCookies) > 0
        log("Profile copy attempt " + str(iAttempt + 1) + " from " + sSource + " to " + sTarget + ": " + str(iCopied) + " items copied, " + str(len(lSkipped)) + " skipped (" + ", ".join(lSkipped[:12]) + "); Cookies " + ("copied, " + format(os.path.getsize(sCookies), ",") + " bytes" if bCookies else "MISSING"))
        if bCookies: return True
        say("The sign-in cookies could not be copied because the browser still had them open.")
    say("Going on without the copied sign-in; KDP will ask you to sign in in the automated window.")
    return False


def titleMatches(sHeld):
    """True when a saved title equals the JSON title, ignoring case and a subtitle after a colon."""
    return sHeld.split(":")[0].strip().lower() == dAnswers["title"].strip().lower()


def bookshelfStatus(page, sWhen):
    """Reads the book's status from the Bookshelf page already open: Draft, In Review, Publishing, Live, Blocked, or 'not shown'.
    The page is read in document order: the first status label (a span whose id holds status-popover and ends with -label) that
    follows the book's title and comes before the next book's title is the book's status. This does not depend on table rows,
    which is how version 18's row-based reading came up empty on 3 October 2026 while the book was in review."""
    try:
        page.locator("span.title-link-label").first.wait_for(state="attached", timeout=20000)
    except Exception:
        log("No title rows appeared on the Bookshelf within 20 seconds")
    for iTry in range(5):  # the status labels render after the title rows; try for up to 20 seconds
        dRow = page.evaluate("""(sTitle) => {
        const sWant = sTitle.toLowerCase();
        const lAll = Array.from(document.querySelectorAll("span.title-link-label, span[id*='status-popover'][id$='-label'], span[id*='publishing-status']"));
        let bInside = false, sLabel = "", sRow = "", sTextAfter = "";
        for (const o of lAll) {
            const bTitle = o.classList.contains("title-link-label");
            const sText = (o.innerText || o.textContent || "").replace(/\\s+/g, " ").trim();
            if (bTitle) {
                if (bInside) break;
                if (sText.toLowerCase().startsWith(sWant)) { bInside = true; sRow = sText; }
                continue;
            }
            if (bInside && sText) sLabel = sLabel ? sLabel + "; " + sText : sText;  // every label of the row: a live book under review shows Live and then Updates in review
        }
        if (bInside && !sLabel) {
            const oTitle = Array.from(document.querySelectorAll("span.title-link-label")).find(o => (o.innerText || "").trim().toLowerCase().startsWith(sWant));
            let o = oTitle; for (let i = 0; i < 6 && o; i++) o = o.parentElement;
            sTextAfter = o ? (o.innerText || "").replace(/\\s+/g, " ").trim().slice(0, 400) : "";
        }
        return {label: sLabel, row: sRow.slice(0, 200), next: sTextAfter, found: bInside};
    }""", dAnswers["title"])
        if dRow["label"] or not dRow.get("found", True): break
        time.sleep(4)
    sText = (dRow["label"] + " " + dRow["next"]).lower()
    sStatus = next((w for w in ["In Review", "Publishing", "Live", "Draft", "Blocked"] if w.lower() in sText), "not shown")
    global sStatusText
    sStatusText = sText
    if "updates in review" in sText: sStatus = "In Review"  # a live book whose update KDP is still reviewing: its setup pages are locked until the update goes live
    if sStatus == "not shown" and dRow.get("found", True):
        try:
            sAround = page.evaluate("""(sTitle) => {
                const oTitle = Array.from(document.querySelectorAll("span.title-link-label")).find(o => (o.innerText || "").trim().toLowerCase().startsWith(sTitle.toLowerCase()));
                let o = oTitle; for (let i = 0; i < 10 && o && (o.innerText || "").length < 1500; i++) o = o.parentElement;
                const lIds = o ? Array.from(o.querySelectorAll("[id]")).map(x => x.id).filter(x => /status|state|live|draft|review/i.test(x)).slice(0, 20) : [];
                return (o ? (o.innerText || "").replace(/\\s+/g, " ").slice(0, 700) : "") + " || ids: " + lIds.join(", ");
            }""", dAnswers["title"])
            log("Bookshelf text around the title, for the next fix: " + sAround)
        except Exception as oError:
            log("Bookshelf surroundings could not be read: " + str(oError)[:100])
    log("Bookshelf status " + sWhen + ": " + sStatus + "; status label '" + dRow["label"] + "'; title '" + dRow["row"] + "'" + ("; nearby text '" + dRow["next"] + "'" if dRow["next"] else "") + ("" if dRow.get("found", True) else "; the title was not found on the Bookshelf"))
    return sStatus


def findDraft(page):
    """Returns the id of the existing draft of this book, verified by its title; "" when none, "AMBIGUOUS" for several, "STOP" when sign-in failed.
    The id comes from the JSON (kdpTitleId) or the built-in constant; the Bookshelf is searched only when that id does not open this book."""
    page.goto(c_sBookshelfUrl)
    page.wait_for_load_state("domcontentloaded")
    time.sleep(3)
    if not waitForSignIn(page): return "STOP"
    global sBookStatus
    sStatus = sBookStatus = bookshelfStatus(page, "before this run")
    say("The Bookshelf shows the book as " + sStatus + "." + (" This run updates the published book: changed files are uploaded, and Publish sends the update." if sStatus in ("Live", "In Review", "Publishing") else ""))
    if sStatus in ("In Review", "Publishing"):
        say("KDP is still reviewing the last submission" + (", the update of the live book" if "updates in review" in sStatusText else "") + ". It does not allow edits until that is done, usually within 72 hours. Nothing was changed; run this again once the Bookshelf shows Live alone.")
        log("Stopped: the book is " + sStatus + "; KDP locks the title setup pages during review")
        return "STOP"
    sKnown = str(dAnswers.get("kdpTitleId", "") or c_sKnownTitleId)
    if sKnown:
        try:
            page.goto(c_sTitleSetup + sKnown + "/details")
            page.wait_for_load_state("domcontentloaded")
        except Exception as oError:  # KDP aborts the navigation (net::ERR_ABORTED) and sends the browser to the Bookshelf while an update is in review; the 16:42 run on 3 October crashed here
            log("Opening the setup page was interrupted: " + str(oError).splitlines()[0][:160])
        time.sleep(3)
        if sKnown not in page.url:
            say("KDP sent the title's setup page back to the Bookshelf, which it does while a submission is in review or publishing. Nothing was changed; run this again once the Bookshelf shows Live.")
            log("Stopped: title-setup for " + sKnown + " redirected to " + page.url)
            return "STOP"
        if sKnown in page.url and page.locator("#data-title").count():
            sHeld = page.locator("#data-title").first.input_value()
            sAuthor = (page.locator("#data-primary-author-first-name").first.input_value() + " " + page.locator("#data-primary-author-last-name").first.input_value()).strip() if page.locator("#data-primary-author-first-name").count() else ""
            if titleMatches(sHeld) or not sHeld.strip():
                say("Opened your existing draft, id " + sKnown + ", currently titled '" + sHeld + "' by " + (sAuthor or "no author yet") + ". Your earlier entries stay unless the JSON says otherwise.")
                log("Using the known draft id " + sKnown + "; title '" + sHeld + "', author '" + sAuthor + "'")
                return sKnown
            log("The known draft id " + sKnown + " holds a different book: '" + sHeld + "'. Not touching it.")
            say("The draft id in the JSON belongs to a different book, '" + sHeld + "'. Nothing was changed.")
            return "AMBIGUOUS"
        log("The known draft id " + sKnown + " did not open a Details page (URL " + page.url + "); looking on the Bookshelf instead")
        page.goto(c_sBookshelfUrl)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(3)
    try:
        page.locator("span.title-link-label").first.wait_for(timeout=15000)
    except Exception:
        log("No title rows appeared on the Bookshelf within 15 seconds")
    oRows = page.locator("span.title-link-label")
    lMatches = [i for i in range(oRows.count()) if titleMatches(oRows.nth(i).inner_text())]
    lIds = sorted(set((oRows.nth(i).get_attribute("id") or "").split("-")[-1] for i in lMatches))  # the span id ends with the title's row id; the page can render a title twice
    log("Bookshelf rows whose title is exactly '" + dAnswers["title"] + "': " + str(len(lMatches)) + " of " + str(oRows.count()) + "; distinct titles " + str(len(lIds)) + " " + str(lIds))
    if not lMatches: return ""
    if len(lIds) > 1:
        log("More than one distinct title matches; refusing to guess")
        return "AMBIGUOUS"
    oRows.nth(lMatches[0]).click()
    try:
        page.wait_for_url(re.compile("title-setup/kindle/[A-Z0-9]+/"), timeout=20000)
    except Exception:
        log("Clicking the title did not open its setup page; URL " + page.url)
        return "AMBIGUOUS"
    oMatch = re.search(r"title-setup/kindle/([A-Z0-9]+)/", page.url)
    sId = oMatch.group(1) if oMatch else ""
    log("Opened the draft from the Bookshelf; id " + sId + "; URL " + page.url)
    return sId or "AMBIGUOUS"


def fillDescription(page):
    """Sets the description through KDP's CKEditor, using the JSON's HTML version, which has only the tags KDP supports."""
    sHtml = dAnswers.get("descriptionHtml") or descriptionHtml(dAnswers["description"])
    sWanted = re.sub(r"\*\*", "", dAnswers["description"])
    fPlain = lambda sText: re.sub(r"\W+", " ", re.sub(r"<[^>]+>", " ", sText)).strip().lower()
    try:
        sCurrent = page.evaluate("() => window.CKEDITOR && Object.values(CKEDITOR.instances).length ? Object.values(CKEDITOR.instances)[0].getData() : ''")
    except Exception:
        sCurrent = ""
    if sCurrent and fPlain(sCurrent) == fPlain(sHtml):
        log("KEPT Description (already saved; " + str(len(sCurrent)) + " characters of HTML)")
        return True
    try:
        iLength = page.evaluate("""(sHtml) => {
            if (!window.CKEDITOR) return -1;
            const lEditors = Object.values(CKEDITOR.instances);
            if (!lEditors.length) return -2;
            const oEditor = lEditors[0];
            oEditor.setData(sHtml);
            oEditor.updateElement();
            oEditor.fire("change");
            return oEditor.getData().length;
        }""", sHtml)
    except Exception as oError:
        iLength = -3
        log("CKEditor call raised " + str(oError)[:160])
    if iLength < 0:
        log("CKEditor API not reachable (code " + str(iLength) + "); typing the plain description instead")
        oBody = page.frame_locator("div.editor iframe").first.locator("body")
        oBody.click()
        page.keyboard.press("Control+A")
        page.keyboard.press("Delete")
        page.keyboard.insert_text(sWanted)
    time.sleep(1)
    sHeld = page.frame_locator("div.editor iframe").first.locator("body").inner_text()
    sFirst, sLast = sHeld.strip().split(".")[0], sHeld.strip()[-70:]
    log("DESCRIPTION set: editor HTML " + str(iLength) + " characters; visible text " + str(len(sHeld)) + " characters (plain version is " + str(len(sWanted)) + "). First sentence: " + sFirst[:120] + ". Ends: " + sLast)
    if len(sHeld.strip()) < len(sWanted) * 0.8: unresolved("Description", "editor shows only " + str(len(sHeld)) + " characters")
    return True


def chooseCategories(page):
    """Opens KDP's category picker and chooses each path in dAnswers['categories'] with its drop-down menus.
    When the Details page already lists every wanted path, the picker is left closed: on a published book it opened empty on 3 October 2026.
    A path that KDP's menus do not offer exactly is completed as near as the menus allow (the step's closest offered name, then the
    General placement, then the first placement offered), said and logged as 'chosen instead', so every book still gets three categories."""
    lSaved = [c_dCategoryFixes.get(sPath, sPath) for sPath in dAnswers["categories"]]
    sShown = page.evaluate("""() => { const o = document.querySelector(".react-categories"); return o ? o.innerText.replace(/\\s+/g, " ") : ""; }""")
    if sShown and all(pathShown(sShown, sPath) for sPath in lSaved):
        say("Categories already saved as the answers file wants; leaving them.")
        log("KEPT categories; the Details page lists: " + sShown[:400])
        return True
    if not clickButton(page, "Choose categories", ["Edit categories", "Choose categories"], False):
        return unresolved("Categories", "no Choose categories or Edit categories button; the Adult-only question must be answered first")
    time.sleep(2)
    clickButton(page, "Remove existing categories warning", ["Continue"], False) if page.get_by_text("Remove existing categories?").count() else None
    try:
        page.locator("select[name^=react-aui]").first.wait_for(timeout=15000)
    except Exception:
        log("No picker menus appeared within 15 seconds")
    oModal = page  # the picker's menus are the only select[name^=react-aui] elements and the only check boxes on the Details page
    log("Picker menus on the page: " + str(page.locator("select[name^=react-aui]").count()) + "; check boxes: " + str(page.get_by_role("checkbox").count()))
    dumpControls(page, "category picker")
    lPaths = lSaved
    lWantedLeaves = sorted(sPath.split(">")[-1].strip().lower() for sPath in lPaths)
    lBoxes = oModal.get_by_role("checkbox")
    lChecked = sorted((lBoxes.nth(i).evaluate("o => (o.labels && o.labels[0] ? o.labels[0].innerText : (o.closest('label') ? o.closest('label').innerText : (o.getAttribute('aria-label') || '')))") or "").strip().lower() for i in range(lBoxes.count()) if lBoxes.nth(i).is_checked())
    log("Placements already chosen in the picker: " + str(lChecked) + "; wanted: " + str(lWantedLeaves))
    if lChecked == lWantedLeaves and pickerCount(oModal).startswith(str(len(lPaths))):
        say("Categories already saved as the answers file wants; leaving them.")
        log("KEPT categories: " + pickerCount(oModal))
        clickButton(page, "Cancel the category picker", ["Cancel"], False)
        time.sleep(1)
        return True
    clearCategories(page, oModal)
    time.sleep(2)
    if not oModal.locator("select[name^=react-aui]").count():
        clickButton(page, "Add another category (first picker)", ["Add another category"], False)
        time.sleep(2)
        log("Picker had no menus after clearing; added one")
    for sOld, sNew in zip(dAnswers["categories"], lPaths):
        if sOld != sNew: log("Category path from the answers corrected to KDP's current name: " + sOld + " -> " + sNew)
    lActual = []
    bLastTicked = True
    for iPath, sPath in enumerate(lPaths):
        lParts = [s.strip() for s in sPath.split(">")]
        if lParts and lParts[0].lower().startswith("kindle"): lParts = lParts[1:]
        say("Category " + str(iPath + 1) + ": " + " > ".join(lParts) + ".")
        if lParts and lParts[-1].lower() in [a.split(">")[-1].strip().lower() for a in lActual]:
            say("  Skipped: a category named " + lParts[-1] + " is already chosen for this book.")
            unresolved("Category " + sPath, "its placement name is already chosen under another path; a second category of the same name adds nothing, so it was dropped")
            continue
        dPicker["topsBefore"] = len(topMenus(oModal))
        if iPath > 0:
            if bLastTicked:  # Add another category is enabled only while the current chain ends on a ticked placement
                if not clickButton(page, "Add another category", ["Add another category"], False):
                    log("Add another category could not be pressed; the picker reports " + pickerCount(oModal) + " with " + str(oModal.locator("select[name^=react-aui]").count()) + " menus")
                    dumpControls(page, "picker without Add another category")
            else:  # the chain before chose nothing, so its menus are reused after Reset
                clearCategories(page, oModal, bRemoveSaved=False)
        time.sleep(1)
        if not oModal.locator("select[name^=react-aui]").count():
            clickButton(page, "Add another category (no menus yet)", ["Add another category"], False)
            time.sleep(2)
        lSelects = oModal.locator("select[name^=react-aui]")
        lTops = topMenus(oModal)
        lEmptyTops = [i for i in lTops if selectedText(lSelects.nth(i)).lower() in ("", "select one")]
        iTopsBefore = dPicker.get("topsBefore", 0)  # how many top menus there were before Add another category was pressed for this path
        bNewChain = iPath > 0 and len(lTops) > iTopsBefore  # Add another category added a chain; KDP pre-fills its top menu with the last chain's first step, so it is not empty
        if not lEmptyTops and not bNewChain and iPath > 0:
            if clickButton(page, "Add another category (no new chain yet)", ["Add another category"], False):
                time.sleep(2)
                lTops = topMenus(oModal)
                lEmptyTops = [i for i in lTops if selectedText(lSelects.nth(i)).lower() in ("", "select one")]
                bNewChain = len(lTops) > iTopsBefore
        log("  top menus at " + str(lTops) + ", empty ones at " + str(lEmptyTops) + (", a new chain" if bNewChain else "") + ", of " + str(lSelects.count()) + " menus; chosen so far: " + str(len(lActual)))
        if not lTops:
            unresolved("Category " + sPath, "the picker shows no top-level menu")
            continue
        if not lEmptyTops and not bNewChain and lActual:
            # Saving what is chosen and reopening the picker turns the chosen chains into saved links and lets Add another category work again (5 October 2026).
            log("  no fresh chain of menus; saving the chosen categories and reopening the picker")
            if clickButton(page, "Save categories (to reopen)", ["Save categories"], False):
                time.sleep(2)
                confirmRemoveExisting(page)
                time.sleep(2)
                closeNotice(page)
                time.sleep(1)
                if clickButton(page, "Edit categories (reopen)", ["Edit categories", "Choose categories"], False):
                    time.sleep(2)
                    closeNotice(page)
                    try:
                        page.locator("select[name^=react-aui]").first.wait_for(timeout=15000)
                    except Exception:
                        log("No picker menus appeared within 15 seconds after reopening")
                    time.sleep(2)
                    lSelects = oModal.locator("select[name^=react-aui]")
                    iTopsBefore = len(topMenus(oModal))
                    if clickButton(page, "Add another category (after reopening)", ["Add another category"], False): time.sleep(2)
                    lTops = topMenus(oModal)
                    lEmptyTops = [i for i in lTops if selectedText(lSelects.nth(i)).lower() in ("", "select one")]
                    bNewChain = len(lTops) > iTopsBefore
                    log("  after reopening: top menus at " + str(lTops) + ", empty ones at " + str(lEmptyTops) + (", a new chain" if bNewChain else "") + ", of " + str(lSelects.count()) + " menus; " + pickerCount(oModal))
            if not lEmptyTops and not bNewChain:
                unresolved("Category " + sPath, "the picker offered no new chain of menus, even after saving and reopening it, so this path could not be started without undoing one already chosen")
                continue
        iTop = lTops[-1] if bNewChain else (lEmptyTops[-1] if lEmptyTops else lTops[-1])
        dPicker["afterIndex"] = iTop - 1  # the path's first step is taken in this top menu, the next steps in the menus after it
        dPicker["lastWasBox"], dPicker["steps"] = False, 0
        lChosen = []
        for sPart in lParts:
            sGot = pickCategoryLevel(page, oModal, sPart)
            if not sGot: break
            lChosen.append(sGot)
        if lChosen and not lastStepWasPlacement(oModal, lChosen[-1]):
            sPlacement = tickPlacement(oModal, " > ".join(lChosen))
            if sPlacement: lChosen.append(sPlacement)
        bLastTicked = bool(lChosen) and lastStepWasPlacement(oModal, lChosen[-1])
        if lChosen and not bLastTicked:
            unresolved("Category " + sPath, "ended on " + lChosen[-1] + " without a placement, so it counts for nothing; the path is dropped")
            lChosen = []
        sActual = "Kindle eBooks > " + " > ".join(lChosen) if lChosen else ""
        if not lChosen:
            unresolved("Category " + sPath, "none of its steps is offered by KDP's menus")
        elif sActual.lower() == sPath.lower():
            log("CATEGORY chosen: " + sPath)
        else:
            say("  KDP's menus do not offer that path exactly; chosen instead: " + sActual.split(">", 1)[1].strip() + ".")
            log("CATEGORY chosen instead of " + sPath + ": " + sActual)
        if sActual: lActual.append(sActual)
        log("Picker now reports: " + pickerCount(oModal))
    if not lActual and lPaths:
        # KDP needs at least one category to save. Only then is General taken, under the first path's deepest menu that KDP offers.
        say("None of the proposed paths is offered, and KDP needs one category; ticking General under the first path's menus.")
        clearCategories(page, oModal, bRemoveSaved=False)
        lTops = topMenus(oModal)
        dPicker["afterIndex"], dPicker["lastWasBox"], dPicker["steps"] = (lTops[-1] - 1 if lTops else oModal.locator("select[name^=react-aui]").count() - 2), False, 0
        lChosen = []
        for sPart in [p.strip() for p in lPaths[0].split(">") if not p.strip().lower().startswith("kindle")]:
            sGot = pickCategoryLevel(page, oModal, sPart)
            if not sGot or dPicker.get("lastWasBox"): break
            lChosen.append(sGot)
        oBox = levelBox(oModal, "General")
        if lChosen and oBox is not None:
            oBox.check(force=True)
            time.sleep(1)
            if oBox.is_checked():
                lActual.append("Kindle eBooks > " + " > ".join(lChosen) + " > General")
                log("CATEGORY chosen as the one KDP requires: " + lActual[-1])
    sCount = pickerCount(oModal)
    log("Picker reports: " + sCount)
    if not sCount.startswith(str(len(lActual))): unresolved("Categories", "the picker reports " + sCount + " but " + str(len(lActual)) + " path" + ("" if len(lActual) == 1 else "s") + " were chosen")
    if len(lActual) < len(lPaths): say("  " + str(len(lActual)) + " of " + str(len(lPaths)) + " proposed categories could be chosen; the rest are reported, not replaced.")
    if not clickButton(page, "Save categories", ["Save categories"], True): return False
    time.sleep(2)
    confirmRemoveExisting(page)
    time.sleep(2)
    closeNotice(page)
    time.sleep(1)
    dAnswers["categoriesChosen"] = lActual
    return verifySavedCategories(page, lActual)


def pathShown(sShown, sPath):
    """True when the Details page's category text lists sPath whole, level by level (KDP writes 'Kindle Books › A › B ↗')."""
    sFlat = re.sub(r"\s*[›>]\s*", " > ", re.sub(r"\s+", " ", sShown or "")).lower()
    lParts = [p.strip() for p in sPath.split(">") if not p.strip().lower().startswith("kindle")]
    return " > ".join(lParts).lower() in sFlat


def verifySavedCategories(page, lPaths):
    """Reads the categories KDP now lists on the Details page and checks every chosen path, level by level."""
    sShown = page.evaluate("""() => { const o = document.querySelector(".react-categories"); return o ? o.innerText.replace(/\\s+/g, " ") : ""; }""")
    log("Categories shown on the Details page: " + sShown[:600])
    dAnswers["categoriesShown"] = sShown
    bOk = True
    for sPath in lPaths:
        if not pathShown(sShown, sPath):
            bOk = unresolved("Category " + sPath, "the saved categories do not show this path: " + sShown[:200])
    if bOk: log("All " + str(len(lPaths)) + " category paths verified on the Details page")
    return bOk


def pickerCount(oModal):
    oText = oModal.get_by_text(re.compile("out of 3 category placements selected"))
    return oText.first.inner_text().strip() if oText.count() else "count not shown"


dPicker = {"afterIndex": -1}  # the index of the menu the last step was chosen in; the next step is looked for only in menus after it


def levelBox(oModal, sName):
    """The visible placement check box named sName, newest first, or None. KDP's picker shows check boxes only for the chain being
    chosen (saved placements are links with Remove beside them), so every visible box belongs to the current level. Marking boxes as
    seen, tried on 4 October 2026, failed because KDP reuses the same box elements with new labels when a menu changes."""
    oPattern = re.compile("^\\s*" + re.escape(sName) + "\\s*$", re.I)
    lBoxes = oModal.get_by_role("checkbox")
    oTicked = None
    for iIndex in range(lBoxes.count() - 1, -1, -1):
        oBox = lBoxes.nth(iIndex)
        if oBox.is_visible() and oPattern.match(boxName(oBox) or ""):
            if not oBox.is_checked(): return oBox
            oTicked = oTicked or oBox
    return oTicked


def lastStepWasPlacement(oModal, sPart):
    """True when the last step chosen was a ticked placement box, not a menu."""
    return bool(dPicker.get("lastWasBox"))


def boxName(oBox):
    return (oBox.get_attribute("aria-label") or oBox.evaluate("o => (o.labels && o.labels[0] ? o.labels[0].innerText : (o.closest('label') ? o.closest('label').innerText : ''))") or "").strip()


def offeredPlacements(oModal):
    """The visible, unticked placement check boxes now offered, in page order."""
    lBoxes = oModal.get_by_role("checkbox")
    return [boxName(lBoxes.nth(i)) for i in range(lBoxes.count()) if lBoxes.nth(i).is_visible() and not lBoxes.nth(i).is_checked()]


def boxNames(oModal):
    lBoxes = oModal.get_by_role("checkbox")
    return [boxName(lBoxes.nth(i)) for i in range(lBoxes.count()) if lBoxes.nth(i).is_visible()]


def tickPlacement(oModal, sPath):
    """The path ended on a drop-down, so KDP wants one more choice: a placement check box. General is the usual fit; failing that,
    the first placement offered, so the book is not left short of a category. Returns the placement's name, or '' when there is none."""
    time.sleep(2)
    lNames = [n for n in offeredPlacements(oModal) if n]
    log("  placements offered below " + sPath.split(">")[-1].strip() + ": " + "; ".join(lNames))
    # No substitute is ticked: a General or a nearby placement is a wasted category (the author's ruling of 4 October 2026).
    # The path is dropped and reported with what KDP offered there, so the proposal can be corrected from data\kdpCategories.md.
    unresolved("Category " + sPath, "ends on a menu, not a placement, so it was dropped; placements KDP offers there: " + ("; ".join(lNames)[:300] or "none"))
    return ""


def clearCategories(page, oModal, bRemoveSaved=True):
    """Resets the picker's current chain of menus and, unless told otherwise, removes every saved placement, so the answers list
    replaces whatever was chosen."""
    oReset = oModal.get_by_role("button", name=re.compile("^Reset$", re.I))
    if not oReset.count(): oReset = oModal.locator("a, button", has_text=re.compile("^\\s*Reset\\s*$"))
    if oReset.count() and oReset.first.is_visible():
        oReset.first.click()
        time.sleep(2)
        log("Category picker reset; menus now: " + str(oModal.locator("select[name^=react-aui]").count()))
    else:
        log("No Reset button in the picker")
    # Reset clears only the newest chain of menus: on 4 October 2026 the saved chains stayed, counted toward the three, and hid
    # Add another category, so the third path was never offered. Each saved chain has its own Remove link; press them all.
    for iRound in range(6):
        if not bRemoveSaved: break
        oRemove = oModal.locator("a", has_text=re.compile("^\\s*Remove\\s*$"))
        lVisible = [oRemove.nth(i) for i in range(oRemove.count()) if oRemove.nth(i).is_visible()]
        if not lVisible: break
        lVisible[-1].click(force=True)
        time.sleep(1.5)
        log("Removed a saved category chain; Remove links left: " + str(len(lVisible) - 1) + "; menus now: " + str(oModal.locator("select[name^=react-aui]").count()))
    log("Picker cleared; menus: " + str(oModal.locator("select[name^=react-aui]").count()) + "; " + pickerCount(oModal))
    return True


def sameName(sA, sB):
    """True when two category names are the same apart from case, spacing and 'and' against '&'."""
    def norm(sText): return re.sub(r"\s+", " ", sText.strip().lower().replace(" and ", " & "))
    return norm(sA) == norm(sB)


def nearestOption(sPart, lOptions):
    """The offered name that is sPart itself, apart from case, spacing and 'and' against '&'; '' when none. No other substitute is
    taken: on 5 October 2026 a containing name let 'Art' stand in for 'Arts & Photography' and 'Instruction & Reference' for
    'Reference', so a path landed in the wrong tree."""
    for sOption in lOptions:
        if sameName(sOption, sPart): return sOption.strip()
    return ""


def topMenus(oModal):
    """The indices of the picker's top-level menus, found by content: every menu whose options are the same list as the first menu's,
    which is always a top-level menu. KDP keeps the menus of saved and reset chains on the page, so counting from the last menu is
    not safe (5 October 2026)."""
    lSelects = oModal.locator("select[name^=react-aui]")
    lTops, lTopOptions = [], None
    for iIndex in range(lSelects.count()):
        try:
            lOptions = [t.strip() for t in lSelects.nth(iIndex).locator("option").all_inner_texts()]
        except Exception:
            continue
        if lTopOptions is None: lTopOptions = lOptions
        if lOptions == lTopOptions: lTops.append(iIndex)
    return lTops


def selectedText(oSelect):
    try:
        return (oSelect.evaluate("o => o.selectedIndex >= 0 ? o.options[o.selectedIndex].text : ''", timeout=5000) or "").strip()
    except Exception:
        return ""


def pickCategoryLevel(page, oModal, sPart):
    """Chooses sPart at the current level of the picker: a placement is a check box, the levels above it are drop-down menus.
    A menu is used only if it comes after the menu the last step was chosen in, so a name that also exists higher up (History at
    the top as well as under Mathematics, 4 October 2026) cannot be taken from the wrong level; after a pick the script waits for
    the next menu or the next set of placement boxes to draw. Returns the name chosen, the nearest offered one when sPart itself is
    not offered, or '' when nothing at this level fits."""
    dtEnd = datetime.datetime.now() + datetime.timedelta(seconds=15)
    while datetime.datetime.now() < dtEnd:
        oBox = levelBox(oModal, sPart) if dPicker.get("steps", 0) else None  # a path's first step is a top menu, never a box; an earlier chain's ticked box with the same name stays visible until the picker is saved
        if oBox is not None:
            dPicker["steps"] = dPicker.get("steps", 0) + 1
            if not oBox.is_checked(): oBox.check(force=True)
            time.sleep(1)
            log("  ticked placement " + sPart + (" (checked)" if oBox.is_checked() else " (NOT checked)"))
            dPicker["lastWasBox"] = oBox.is_checked()
            return sPart if oBox.is_checked() else ""
        lSelects = oModal.locator("select[name^=react-aui]")
        iFirst = dPicker["afterIndex"] + 1
        iLast = iFirst + 1 if dPicker.get("steps", 0) == 0 else lSelects.count()  # a path's first step is taken only in its top menu; later steps in any menu after the last pick
        for iIndex in range(iFirst, min(iLast, lSelects.count())):
            oSelect = lSelects.nth(iIndex)  # KDP's native menus can be hidden behind its styled drop-downs, so visibility is not required; version 29 skipped them and found nothing
            lOptions = [t.strip() for t in oSelect.locator("option").all_inner_texts()]
            sGot = nearestOption(sPart, lOptions)
            if not sGot: continue
            lBefore, iSelectsBefore = boxNames(oModal), lSelects.count()
            lNextBefore = [t.strip() for t in lSelects.nth(iIndex + 1).locator("option").all_inner_texts()] if iIndex + 1 < iSelectsBefore else []
            try:
                oSelect.select_option(label=sGot, force=True, timeout=5000)
            except Exception as oError:
                log("  select_option raised " + str(oError)[:100] + "; setting the value by script")
            if not sameName(selectedText(oSelect), sGot):
                oSelect.evaluate("(o, s) => { for (const opt of o.options) if (opt.text.trim().toLowerCase() === s.toLowerCase()) { o.value = opt.value; o.dispatchEvent(new Event('change', {bubbles: true})); } }", sGot)
                time.sleep(1)
            if not sameName(selectedText(oSelect), sGot):
                log("  menu " + str(iIndex + 1) + " did not take " + sGot + "; it shows '" + selectedText(oSelect) + "'")
                continue
            dPicker["afterIndex"] = iIndex
            dPicker["lastWasBox"], dPicker["steps"] = False, dPicker.get("steps", 0) + 1
            log("  picked " + sGot + " in menu " + str(iIndex + 1) + " of " + str(iSelectsBefore))
            for iTick in range(20):  # up to 10 seconds for the next menu or the placement boxes below it to draw
                time.sleep(0.5)
                lNow = oModal.locator("select[name^=react-aui]")
                lNextNow = [t.strip() for t in lNow.nth(iIndex + 1).locator("option").all_inner_texts()] if iIndex + 1 < lNow.count() else []
                if lNextNow and lNextNow != lNextBefore: break
                if boxNames(oModal) != lBefore: break
            time.sleep(1)
            return sGot
        time.sleep(1)
    lPlacements = [n for n in offeredPlacements(oModal) if n]
    sNear = nearestOption(sPart, lPlacements)
    if sNear:
        oBox = levelBox(oModal, sNear)
        oBox.check(force=True)
        time.sleep(1)
        log("  '" + sPart + "' is not offered; ticked the nearest placement " + sNear + (" (checked)" if oBox.is_checked() else " (NOT checked)"))
        dPicker["lastWasBox"] = oBox.is_checked()
        return sNear if oBox.is_checked() else ""
    lSelects = oModal.locator("select[name^=react-aui]")
    lMenus = ["; ".join(t.strip() for t in lSelects.nth(i).locator("option").all_inner_texts()) for i in range(dPicker["afterIndex"] + 1, lSelects.count())]
    log("  '" + sPart + "' is not offered. Menus after the last pick: " + " || ".join(lMenus)[:600] + ". Placements: " + "; ".join(lPlacements)[:300])
    return ""


def fillDetails(page):
    say("Details tab.")
    d = dAnswers
    lName = d["author"].split()
    sFirst, sLast = " ".join(lName[:-1]), lName[-1]
    if not ask("Permanent answers: language " + d["language"] + "; title " + d["title"] + "; subtitle " + d["subtitle"] + "; edition " + d["editionNumber"] + "; author " + d["author"] + ". KDP never lets these change after publishing. Use them?"):
        say("Stopped at your request before entering the permanent fields.")
        return False
    page.wait_for_load_state("domcontentloaded")
    time.sleep(3)
    say("Recording the page's controls in the log, then filling. Each group of fields is announced here.")
    dumpControls(page, "details, before filling")
    say("Language, title, subtitle, edition, author.")
    setNativeSelect(page, "Language", "#data-language-native", d["language"])
    fillText(page, "Title", ["#data-title"], d["title"])
    fillText(page, "Subtitle", ["#data-subtitle"], d["subtitle"])
    fillText(page, "Edition number", ["#data-edition-number"], d["editionNumber"])
    fillText(page, "Author first name", ["#data-primary-author-first-name"], sFirst)
    fillText(page, "Author last name", ["#data-primary-author-last-name"], sLast)
    if page.locator("#edit_series_description").count() and page.locator("#edit_series_description").first.is_visible():
        unresolved("Series", "the draft is part of a series, but the JSON says it stands alone; remove it from the series in the browser window")
    else:
        log("Series: none, as the JSON says")
    say("Description.")
    fillDescription(page)
    say("Publishing rights, adult content, marketplace.")
    clickRadio(page, "Publishing rights", ["#non-public-domain" if d["publishingRights"].lower().startswith("i own") else "#public-domain"])
    clickRadio(page, "Adult content: " + d["sexuallyExplicit"], ["input[name='data[is_adult_content]-radio'][value=" + ("true" if d["sexuallyExplicit"].strip().lower() == "yes" else "false") + "]"])
    # On a published book KDP renders each of these selects twice (a live one and a disabled copy), so read through JavaScript, never a strict locator.
    for sAge in ["#data-reading-interest-age-start-input-native", "#data-reading-interest-age-end-input-native"]:
        sHeld = page.evaluate("(s) => { const l = Array.from(document.querySelectorAll(s)); const o = l.find(x => !x.disabled) || l[0]; return o ? (o.value || '') : ''; }", sAge)
        if sHeld.strip():
            unresolved("Reading age", "the draft has a reading age set (" + sHeld + "), but the JSON says to leave it blank; clear it in the browser window")
    log("Reading age: blank, as the JSON says") if not any(u.startswith("Reading age") for u in lUnresolved) else None
    setNativeSelect(page, "Primary marketplace", "select[name='data[digital][home_marketplace]']", "US" if d["primaryMarketplace"].lower() == "amazon.com" else d["primaryMarketplace"])
    lKeywords = (list(d["keywords"]) + [""] * 7)[:7]
    say(str(len(d["keywords"])) + " keyword" + ("" if len(d["keywords"]) == 1 else "s") + ".")
    for iIndex, sKeyword in enumerate(lKeywords):
        fillText(page, "Keyword " + str(iIndex + 1), ["#data-keywords-" + str(iIndex)], sKeyword)
    lHeld = [page.locator("#data-keywords-" + str(i)).first.input_value() for i in range(7)]
    log("Keyword boxes now hold: " + " | ".join(lHeld))
    if [k.strip() for k in lHeld] != [k.strip() for k in lKeywords]: unresolved("Keywords", "boxes hold " + " | ".join(lHeld))
    say("Categories, three paths. This takes about a minute.")
    chooseCategories(page)
    say("Release option, then Save as Draft.")
    if sBookStatus in ("Live", "In Review", "Publishing"):
        log("Release option: the book is already published (" + sBookStatus + "), so KDP no longer shows it; nothing to set")
    elif d.get("releaseOption", "Release now").lower().startswith("release now"):
        if not clickButton(page, "Release now", ["I am ready to release my book now"], False):
            log("Release option: not shown on this Details page; KDP shows it only for a book that has never been published, so nothing to set")
    else:
        unresolved("Release option", "the JSON asks for a pre-order, which this script does not set up")
    logMessages(page, "details filled")
    saveDraft(page)
    say("Details tab filled and saved as a draft." + ((" Items to check: " + str(len(lUnresolved))) if lUnresolved else ""))
    return True


def fileSha256(sPath):
    import hashlib
    oHash = hashlib.sha256()
    with open(sPath, "rb") as f:
        for bChunk in iter(lambda: f.read(1 << 20), b""): oHash.update(bChunk)
    return oHash.hexdigest()


def receiptPath():
    """The upload receipt lives in data\\, which is kept across sessions; logs\\ is emptied when its files are zipped and sent (moved from logs\\ on 4 October 2026)."""
    sNew, sOld = os.path.join(sProject, "data", "kdpSubmit-receipt.inix"), os.path.join(sProject, "logs", "kdpSubmit-receipt.inix")
    os.makedirs(os.path.dirname(sNew), exist_ok=True)
    if not os.path.exists(sNew) and os.path.exists(sOld):
        try:
            shutil.copy2(sOld, sNew)
            log("Receipt copied from logs to data: " + sNew)
        except Exception as oError:
            log("Receipt could not be copied to data: " + str(oError)[:100])
    return sNew


def readReceipt():
    """The receipt is an .inix file with one section per asset (manuscript, cover) holding file, sha256 and uploaded. An older JSON receipt is read too."""
    try:
        if os.path.exists(receiptPath()): return readInix(receiptPath())
        sOld = receiptPath()[:-5] + ".json"
        if os.path.exists(sOld):
            with open(sOld, encoding="utf-8-sig") as f: return json.load(f)
    except Exception as oError:
        log("Receipt could not be read: " + str(oError)[:120])
    return {}


def writeReceipt(dReceipt):
    os.makedirs(os.path.dirname(receiptPath()), exist_ok=True)
    return writeInix(receiptPath(), dReceipt)


def fileInputFor(page, sButtonId):
    """Returns the file input that belongs to the upload button with the given id, by walking up from the button, or None."""
    oHandle = page.evaluate_handle("""(sId) => {
        const oButton = document.getElementById(sId);
        if (!oButton) return null;
        let o = oButton;
        for (let i = 0; i < 10 && o; i++) {
            const oInput = o.querySelector("input[type=file]");
            if (oInput) return oInput;
            o = o.parentElement;
        }
        return null;
    }""", sButtonId)
    return oHandle.as_element()


def uploadFile(page, sWhat, sPath, sButtonId, sDonePattern):
    """Uploads one asset through its own section's file input and waits for KDP's message about that asset.
    sDonePattern is a regular expression that only this asset's success message matches."""
    if not os.path.exists(sPath): return unresolved(sWhat, "file missing: " + sPath)
    oInput = fileInputFor(page, sButtonId)
    if oInput is None: return unresolved(sWhat, "no file input found in the section of button #" + sButtonId)
    lBefore = pageMessages(page)
    try:
        oInput.set_input_files(sPath)
    except Exception as oError:
        return unresolved(sWhat, "upload failed: " + str(oError)[:200])
    sSha = fileSha256(sPath)
    log("UPLOADING " + sWhat + " from " + sPath + " (" + format(os.path.getsize(sPath), ",") + " bytes, sha256 " + sSha[:16] + "...)")
    say("Uploading the " + sWhat.lower() + ". KDP processing can take several minutes.")
    oDone, oError = re.compile(sDonePattern, re.I), re.compile(r"\b(error|errors|failed|not supported|could not|unable)\b", re.I)
    # Only what KDP says after this upload counts (7 October 2026, from MyBooks): a published book's Content tab already shows
    # messages about its old file -- "Missing Table of Contents", a recommendation, and "Well done! Your manuscript does not
    # have spelling errors", praise holding the word errors -- and reading those as a verdict on the new file stopped seven
    # uploads in their first second. Praise and recommendations are logged, never treated as problems; and done means KDP
    # names the file just sent, since the old file's "uploaded successfully" is on the page too.
    oFine = re.compile(r"^(well done|we recommend)|does not have|no (spelling )?errors", re.I)
    sSentName = os.path.basename(sPath).lower()
    setBefore = set(lBefore)
    bSeenChange = False
    dtEnd = datetime.datetime.now() + datetime.timedelta(minutes=c_iProcessingMinutes)
    while datetime.datetime.now() < dtEnd:
        lTexts = pageMessages(page)
        if lTexts != lBefore: bSeenChange = True
        lMine = [t for t in lTexts if re.search(sWhat.split()[0], t, re.I) and t not in setBefore]
        if any(oError.search(t) and not oFine.search(t) for t in lMine):
            logMessages(page, sWhat + " problem")
            say("KDP reported a problem with the " + sWhat.lower() + ". The exact message is in the log.")
            return unresolved(sWhat, " | ".join(lMine)[:300])
        lQuoted = [t for t in lTexts if oDone.search(t) and re.search(r'"[^"]+\.[a-z0-9]{2,5}"', t)]
        bNamed = any(sSentName in t.lower() for t in lQuoted) if lQuoted else True
        if bSeenChange and bNamed and any(oDone.search(t) for t in lTexts) and not any("processing your file" in t.lower() for t in lMine):
            for t in [t for t in lTexts if t not in setBefore and re.match(r"(?i)we recommend|missing ", t)]: log("KDP RECOMMENDS (not a problem): " + t[:300])
            logMessages(page, sWhat + " done")
            say(sWhat + " uploaded and processed.")
            dReceipt = readReceipt()
            dReceipt[sWhat.lower()] = {"file": os.path.basename(sPath), "sha256": sSha, "bytes": os.path.getsize(sPath), "uploaded": now(), "kdpMessage": next((t for t in lTexts if oDone.search(t)), "")[:200]}
            writeReceipt(dReceipt)
            log("Receipt written for " + sWhat.lower() + " (a local record of what was sent, not a server-side check)")
            return True
        time.sleep(10)
    return unresolved(sWhat, "KDP did not confirm the " + sWhat.lower() + " within " + str(c_iProcessingMinutes) + " minutes")


def setSelectByWords(page, sWhat, oSelect, lWords):
    """Chooses the option of a (possibly hidden) native select whose text contains every word in lWords."""
    lOptions = [t.strip() for t in oSelect.locator("option").all_inner_texts()]
    lHits = [o for o in lOptions if all(w.lower() in o.lower() for w in lWords)]
    if not lHits:
        log("  options for " + sWhat + ": " + "; ".join(lOptions))
        return unresolved(sWhat, "no option containing " + " and ".join(lWords) + "; offered: " + "; ".join(lOptions)[:300])
    oSelect.evaluate("(o, s) => { for (const opt of o.options) if (opt.text.trim() === s) { o.value = opt.value; o.dispatchEvent(new Event('change', {bubbles: true})); } }", lHits[0])
    log("SELECTED " + sWhat + " = " + lHits[0])
    return True


def answerAiContent(page):
    """Answers KDP's AI-generated content section from the JSON: Yes, then the extent of text, images and translations."""
    dAi = dAnswers["aiContent"]
    if not clickAria(page, "AI-generated content used", "radio", "Yes"): return False
    time.sleep(2)
    dumpControls(page, "AI content section after Yes")
    lSelects = page.locator("select")
    def wordsFor(sAnswer):
        """Turns a JSON answer such as 'Entire work, with extensive editing' into the words KDP's option must contain."""
        sLower = sAnswer.lower()
        lWords = []
        for sPhrase in ["none", "entire work", "some sections", "one or a few", "many"]:
            if sPhrase in sLower: lWords.append(sPhrase); break
        if "extensive" in sLower: lWords.append("extensive")
        elif "minimal" in sLower or "no editing" in sLower: lWords.append("minimal")
        return lWords or [sAnswer]
    dWanted = {"text": wordsFor(dAi["texts"]), "image": wordsFor(dAi["images"]), "translation": wordsFor(dAi["translations"])}
    log("AI extents wanted from the JSON: " + str(dWanted))
    dDone = {}
    for iIndex in range(lSelects.count()):
        oSelect = lSelects.nth(iIndex)
        sName = (oSelect.get_attribute("name") or "") + " " + (oSelect.get_attribute("id") or "")
        sLabel = oSelect.evaluate("o => { const r = o.closest('.a-row, .a-section, fieldset, div'); return r ? r.innerText.slice(0, 120) : ''; }")
        sKey = next((k for k in dWanted if k in (sName + " " + sLabel).lower()), "")
        if not sKey or sKey in dDone: continue
        dDone[sKey] = setSelectByWords(page, "AI " + sKey + " extent", oSelect, dWanted[sKey])
    for sKey in dWanted:
        if sKey not in dDone:
            lRadios = page.get_by_role("radio", name=re.compile(".*".join(re.escape(w) for w in dWanted[sKey]), re.I))
            if lRadios.count():
                lRadios.first.click()
                dDone[sKey] = True
                log("CHOSE AI " + sKey + " extent radio: " + " ".join(dWanted[sKey]))
            else:
                unresolved("AI " + sKey + " extent", "no menu or radio found for it; wanted " + " ".join(dWanted[sKey]))
    sTools = dAi["tools"]
    for sKind in ["texts", "images"]:
        lBoxes = page.get_by_label(re.compile("AI-generated " + sKind, re.I))
        iVisible = -1
        for iIndex in range(lBoxes.count()):
            if lBoxes.nth(iIndex).is_visible():
                iVisible = iIndex
                break
        if iVisible < 0:
            oAll = page.locator("input[type=text]")
            for iIndex in range(oAll.count()):
                sLabel = (oAll.nth(iIndex).get_attribute("aria-label") or oAll.nth(iIndex).get_attribute("placeholder") or "").lower()
                if "ai-generated " + sKind in sLabel and oAll.nth(iIndex).is_visible():
                    lBoxes, iVisible = oAll, iIndex
                    break
        if iVisible < 0:
            unresolved("AI tool for " + sKind, "no visible box asking which tool made the AI-generated " + sKind)
            continue
        oBox = lBoxes.nth(iVisible)
        if oBox.input_value().strip() == sTools:
            log("KEPT AI tool for " + sKind + " = " + sTools)
            continue
        oBox.click()
        oBox.fill(sTools)
        oBox.press("Tab")
        time.sleep(1)
        log("FILLED AI tool for " + sKind + " = " + sTools + " (box now holds '" + oBox.input_value() + "')")
    return True


def chooseAccessibilityRadio(page, sLabelStart):
    """Chooses the image-reading radio by the words its label starts with. Right after a new upload KDP re-renders these four
    radios and for a moment every one carries the value 'readable', so choosing by value picked 'I don't know' on 3 October 2026;
    the label is the only thing that tells them apart. Waits up to 30 seconds for four radios with four different values."""
    sScript = """(sStart) => {
        const l = Array.from(document.querySelectorAll("input[name='data[accessibility][image_reading]']"));
        const lValues = new Set(l.map(o => o.value));
        const fLabel = o => (o.labels && o.labels[0] ? o.labels[0].innerText : (o.closest("label") ? o.closest("label").innerText : "")).replace(/\\s+/g, " ").trim().toLowerCase();
        const oWant = l.find(o => fLabel(o).startsWith(sStart));
        return {count: l.length, distinct: lValues.size, found: !!oWant, checked: oWant ? oWant.checked : false, value: oWant ? oWant.value : "", labels: l.map(o => fLabel(o).slice(0, 40) + "=" + o.value + (o.checked ? " (checked)" : ""))};
    }"""
    dState = {}
    for iTick in range(30):
        dState = page.evaluate(sScript, sLabelStart)
        if dState["count"] >= 4 and dState["distinct"] >= 4 and dState["found"]: break
        time.sleep(1)
    if not dState.get("found"): return unresolved("Accessibility: informative images", "no radio labelled '" + sLabelStart + "...' among " + str(dState.get("labels")))
    if dState["checked"]:
        log("Accessibility: informative images already set (" + sLabelStart + "..., value " + dState["value"] + ")")
        return True
    page.evaluate("""(sStart) => {
        const l = Array.from(document.querySelectorAll("input[name='data[accessibility][image_reading]']"));
        const fLabel = o => (o.labels && o.labels[0] ? o.labels[0].innerText : (o.closest("label") ? o.closest("label").innerText : "")).replace(/\\s+/g, " ").trim().toLowerCase();
        const o = l.find(o => fLabel(o).startsWith(sStart));
        (o.labels && o.labels[0] ? o.labels[0] : o).click();
    }""", sLabelStart)
    time.sleep(1)
    dState = page.evaluate(sScript, sLabelStart)
    if dState["checked"]:
        log("CHOSE Accessibility: informative images = " + sLabelStart + "... (value " + dState["value"] + "); radios now " + str(dState["labels"]))
        return True
    return unresolved("Accessibility: informative images", "the radio '" + sLabelStart + "...' did not take; radios now " + str(dState["labels"]))


def uploadsDone(page):
    lTexts = pageMessages(page)
    sJoined = " | ".join(lTexts).lower()
    bManuscript = any("manuscript" in t.lower() and "uploaded successfully" in t.lower() for t in lTexts) and not any("manuscript" in t.lower() and "processing your file" in t.lower() for t in lTexts)
    bCover = any("cover uploaded successfully" in t.lower() for t in lTexts) and not any("cover" in t.lower() and "processing your file" in t.lower() for t in lTexts)
    return bManuscript, bCover, sJoined


def assetNeedsUpload(sKind, sPath, bKdpShowsIt):
    """Decides from the local receipt whether KDP already holds this exact file. --reupload forces both assets."""
    if "--reupload" in sys.argv:
        log(sKind + ": --reupload given; uploading again")
        return True
    if not bKdpShowsIt:
        log(sKind + ": KDP does not show it as uploaded and processed; uploading")
        return True
    dEntry = readReceipt().get(sKind.lower(), {})
    sSha = fileSha256(sPath)
    if dEntry.get("sha256") == sSha and dEntry.get("file") == os.path.basename(sPath):
        log(sKind + ": the receipt from " + str(dEntry.get("uploaded")) + " matches this file's sha256 " + sSha[:16] + "...; not uploading again")
        return False
    log(sKind + ": no receipt matching this file (receipt sha256 " + str(dEntry.get("sha256", ""))[:16] + ", file " + sSha[:16] + "); uploading so KDP holds this exact version")
    return True


def onTab(page, sTab):
    """True once the browser shows the given setup tab, opening its address directly when it is elsewhere (the pricing tab, after the 6 October run's stray press), and waiting for the page to settle."""
    for iTry in range(2):
        try:
            page.wait_for_load_state("domcontentloaded", timeout=20000)
        except Exception as oError:
            log("Waiting for the " + sTab + " tab to load raised " + str(oError).splitlines()[0][:120])
        time.sleep(3)
        if "/" + sTab in page.url and tabLooksReady(page, sTab): return True
        sTitleId = titleIdFrom(page.url)
        if iTry == 1 or not sTitleId: break
        sTarget = c_sTitleSetup + sTitleId + "/" + sTab
        log("Not on the " + sTab + " tab (URL " + page.url + "); opening it directly at " + sTarget)
        try:
            page.goto(sTarget)
        except Exception as oError:
            log("Opening the " + sTab + " tab raised " + str(oError).splitlines()[0][:160])
    return "/" + sTab in page.url and tabLooksReady(page, sTab)


def fillContent(page):
    say("Content tab.")
    d = dAnswers
    if not onTab(page, "content"): return unresolved("Content tab", "not on the Content page (URL " + page.url + ") and it could not be opened directly; nothing clicked there")
    dumpControls(page, "content, before filling")
    if not ask("Content tab: DRM " + d["drm"] + "; upload " + d["manuscriptFile"] + " and " + d["coverFile"] + " if KDP does not already hold them; AI-generated content " + d["aiContent"]["used"] + " with the extents in the JSON, tool " + d["aiContent"]["tools"] + "; accessibility answer from the JSON. Proceed?"):
        return unresolved("Content tab", "you chose not to proceed")
    bNoDrm = d["drm"].strip().lower().startswith("no")
    say("DRM: " + ("no, as the JSON says." if bNoDrm else "yes, as the JSON says."))
    setDrm(page, bNoDrm)
    bManuscript, bCover, sJoined = uploadsDone(page)
    log("Before uploading, KDP shows manuscript done: " + str(bManuscript) + ", cover done: " + str(bCover))
    sManuscript, sCover = os.path.join(sProject, d["manuscriptFile"]), os.path.join(sProject, d["coverFile"])
    if assetNeedsUpload("Manuscript", sManuscript, bManuscript and os.path.basename(d["manuscriptFile"]).lower() in sJoined):
        uploadFile(page, "Manuscript", sManuscript, "data-assets-interior-file-upload-browse-button-announce", r"manuscript .*uploaded successfully")
    else:
        say("The manuscript " + d["manuscriptFile"] + " is already uploaded and processed; not uploading it again.")
    if assetNeedsUpload("Cover", sCover, bCover):
        clickButton(page, "Upload a cover you already have", ["Upload a cover you already have"], False)
        uploadFile(page, "Cover", sCover, "data-assets-cover-file-upload-browse-button-announce", r"cover uploaded successfully")
    else:
        say("The cover is already uploaded; not uploading it again.")
    say("Waiting for KDP to finish processing the files.")
    dtEnd = datetime.datetime.now() + datetime.timedelta(minutes=c_iProcessingMinutes)
    while datetime.datetime.now() < dtEnd:
        bManuscript, bCover, sJoined = uploadsDone(page)
        if bManuscript and bCover: break
        time.sleep(10)
    logMessages(page, "after processing wait")
    if bManuscript and bCover:
        say("Processing finished.")
    else:
        unresolved("File processing", "KDP had not finished processing the " + ("manuscript" if not bManuscript else "cover") + " after " + str(c_iProcessingMinutes) + " minutes")
        say("Processing is still running; this blocks publishing until it finishes.")
    say("AI-generated content: yes; text, images and translations as the JSON says.")
    answerAiContent(page)
    sAccess = str(d.get("accessibility", {}).get("imageReading", "All")).lower()
    sValue = "readable" if sAccess.startswith("all") else "partially_readable" if sAccess.startswith("some") else "not_readable" if sAccess.startswith("none") else "unknown"
    say("Accessibility: " + {"readable": "all informative images have alternative text.", "partially_readable": "some informative images have alternative text.", "not_readable": "no informative images have alternative text.", "unknown": "unknown."}[sValue])
    sLabelStart = {"readable": "all informative images", "partially_readable": "some informative images", "not_readable": "none of the informative images", "unknown": "i don't know"}[sValue]
    chooseAccessibilityRadio(page, sLabelStart)
    for sPart in ["navigation", "reading_order", "structure", "text_"]:
        oMore = page.locator("input[name^='data[accessibility]'][name*='" + sPart + "']")
        if oMore.count():
            log("Another accessibility question is on the page: " + sPart + "; its controls follow.")
            dumpControls(page, "accessibility " + sPart)
            unresolved("Accessibility question " + sPart, "answer it in the browser window: the EPUB is all text, navigable by headings, table of contents and landmarks, with a described cover")
    if page.locator("[role=checkbox]").count():
        say("Confirming that the answers are accurate.")
        clickAria(page, "Confirmation that the answers are accurate", "checkbox", "I confirm that my answers are accurate")
    else:
        log("No confirmation check box on the page this time (KDP shows it only after a new upload)")
    for sWhat, sSelector, sWanted in [("ISBN", "#data-digital-isbn", d.get("isbn", "")), ("Publisher", "#data-publisher", d.get("publisher", ""))]:
        sKeep = "" if sWanted.lower().startswith(("none", "leave blank", "blank")) else sWanted
        oField = page.locator(sSelector + ":not([disabled])").first if page.locator(sSelector + ":not([disabled])").count() else page.locator(sSelector).first
        if oField.count():
            sHeld = oField.input_value()
            if sHeld.strip() != sKeep.strip():
                oField.fill(sKeep)
                log("SET " + sWhat + " = '" + sKeep + "' (was '" + sHeld + "')")
            else:
                log("KEPT " + sWhat + " = '" + sHeld + "'")
    dumpControls(page, "content, after filling")
    logMessages(page, "content filled")
    saveDraft(page)
    say("Content tab filled and saved as a draft." + ((" Items to check: " + str(len(lUnresolved))) if lUnresolved else ""))
    return True


def fillPricing(page):
    say("Pricing tab.")
    d = dAnswers
    if not onTab(page, "pricing"): return unresolved("Pricing tab", "not on the Pricing page (URL " + page.url + ") and it could not be opened directly; nothing clicked there")
    dumpControls(page, "pricing, before filling")
    if not ask("Pricing tab: KDP Select " + d["kdpSelect"] + "; territories " + d["territories"] + "; royalty " + d["royalty"] + "; US list price $" + str(d["priceUsd"]) + ". Proceed?"):
        return unresolved("Pricing tab", "you chose not to proceed")
    oSelect = page.locator("#data-is-select").first
    if d["kdpSelect"].lower().startswith("do not"):
        if oSelect.count() and oSelect.is_checked():
            oSelect.locator("xpath=ancestor::label[1]").first.click(force=True) if oSelect.locator("xpath=ancestor::label[1]").count() else oSelect.click(force=True)
            log("KDP Select box was ticked; unticked it (now " + str(oSelect.is_checked()) + ")")
        say("KDP Select: not enrolling, as the JSON says.")
    else:
        clickRadio(page, "KDP Select", ["#data-is-select"])
    bAll = d["territories"].lower().startswith("all")
    say("Territories: " + ("all." if bAll else "individual, as the JSON says.") + " Royalty " + d["royalty"] + " at $" + str(d["priceUsd"]) + ".")
    if bAll:
        clickButton(page, "All territories", ["All territories (worldwide rights)", "All territories"], True)
    else:
        unresolved("Territories", "the JSON asks for individual territories, which this script does not fill; choose them in the browser window")
    sRate = "70_PERCENT" if d["royalty"].strip().startswith("70") else "35_PERCENT"
    clickRadio(page, "Royalty plan " + d["royalty"], ["input[name='data[digital][royalty_rate]-radio'][value='" + sRate + "']"])  # the value must be quoted: 70_PERCENT starts with a digit, and an unquoted one crashed the 15:05 run on 3 October
    sPrice = "%.2f" % float(d["priceUsd"])
    fillText(page, "US list price", ["input[name='data[digital][channels][amazon][US][price_vat_inclusive]']"], sPrice)
    time.sleep(3)
    lOther = page.locator("input[name^='data[digital][channels][amazon]'][name*='price']")
    lHeld = [(lOther.nth(i).get_attribute("name").split("][")[3], lOther.nth(i).input_value()) for i in range(lOther.count())]
    log("Marketplace prices now: " + "; ".join(sCode + "=" + (sValue or "blank") for sCode, sValue in lHeld))
    sUs = next((sValue for sCode, sValue in lHeld if sCode == "US"), "")
    if sUs.strip() not in (sPrice, sPrice.rstrip("0").rstrip(".")): unresolved("US list price", "box holds '" + sUs + "' instead of " + sPrice)
    lBlank = [sCode for sCode, sValue in lHeld if sCode != "US" and not sValue.strip()]
    if lBlank: log("Other marketplaces still blank after the US price: " + ", ".join(lBlank) + " (KDP normally converts them from the US price when saving)")
    clickLabel(page, "Kindle Book Lending", ["Allow lending", "Kindle Book Lending"], "checkbox") if page.get_by_text(re.compile("Book Lending", re.I)).count() else log("No Book Lending option seen")
    logMessages(page, "pricing filled")
    saveDraft(page)
    lAfter = [(lOther.nth(i).get_attribute("name").split("][")[3], lOther.nth(i).input_value()) for i in range(lOther.count())]
    log("Marketplace prices after Save as Draft: " + "; ".join(sCode + "=" + (sValue or "blank") for sCode, sValue in lAfter))
    lStillBlank = [sCode for sCode, sValue in lAfter if not sValue.strip()]
    if lStillBlank: unresolved("Marketplace prices", "still blank after saving: " + ", ".join(lStillBlank))
    lTexts = pageMessages(page)
    lProblems = [t for t in lTexts if re.search(r"fix the highlighted|must be|required|invalid|between \$", t, re.I)]
    if lProblems: unresolved("Pricing tab", "KDP says: " + " | ".join(lProblems)[:300])
    say("Pricing tab filled and saved as a draft." + ((" Items to check: " + str(len(lUnresolved))) if lUnresolved else ""))
    return True


def finalReview(page):
    d = dAnswers
    say("Review of the answers the JSON asked for. Title: " + d["title"] + ". Subtitle: " + d["subtitle"] + ". Author: " + d["author"] + ".")
    say("First sentence of the description: " + d["description"].split(".")[0] + ".")
    say("Categories: " + "; ".join(c_dCategoryFixes.get(sPath, sPath) for sPath in d["categories"]) + ".")
    say("Keywords: " + "; ".join(d["keywords"]) + ".")
    say("DRM: " + d["drm"] + ". KDP Select: " + d["kdpSelect"] + ". Royalty: " + d["royalty"] + " at $" + str(d["priceUsd"]) + ".")
    lBlocking = [u for u in lUnresolved if u.split(":")[0].strip() in c_lBlocking]
    lAdvisory = [u for u in lUnresolved if u not in lBlocking]
    if lBlocking:
        say(str(len(lBlocking)) + " item" + ("" if len(lBlocking) == 1 else "s") + " stop" + ("s" if len(lBlocking) == 1 else "") + " publishing, because KDP refused it or a file did not upload:")
        for sItem in lBlocking: say("  - " + sItem)
        for sItem in lAdvisory: say("  - also to check: " + sItem)
        say("The draft is saved. Fix those in the browser window, which stays open, or send the log back for a script fix.")
        return "blocked"
    if lAdvisory:
        say(str(len(lAdvisory)) + " item" + ("" if len(lAdvisory) == 1 else "s") + " could not be confirmed, but KDP accepted every save, so publishing goes ahead. Check these afterwards:")
        for sItem in lAdvisory: say("  - " + sItem)
    if "--no-publish" in sys.argv:
        say("Everything is saved as a draft. Not publishing, because --no-publish was given.")
        return "draft"
    if "--ask" in sys.argv:
        sAnswer = input("Everything is saved as a draft. Publishing makes the book available for sale on Amazon, usually within 72 hours, and the title, subtitle, author and edition can no longer be changed. Type publish to press Publish Your Kindle eBook, or press Enter to keep the draft: ").strip().lower()
        log("PUBLISH PROMPT ANSWER: " + sAnswer)
        if sAnswer != "publish":
            say("Draft kept. Nothing was published.")
            return "draft"
    say("Everything is filled and saved. Pressing Publish Your Kindle eBook now, as instructed. For a new book this makes title, subtitle, author and edition permanent; for a published book it sends the update, which KDP usually makes live within 72 hours.")
    dumpControls(page, "pricing, before Publish")
    sBefore = page.url
    if not clickButton(page, "Publish Your Kindle eBook", ["#save-and-publish-announce", "Publish Your Kindle eBook"]):
        say("The Publish button was not found. The draft is saved; nothing was submitted.")
        return "draft"
    time.sleep(5)
    for iTry in range(3):
        oConfirm = page.get_by_role("button", name=re.compile("^(Publish|Confirm|Yes, publish)$", re.I))
        if oConfirm.count() and oConfirm.first.is_visible():
            oConfirm.first.click()
            log("Confirmed a follow-up Publish dialog")
            time.sleep(5)
        else:
            break
    oAck = re.compile(r"congratulations|has been submitted|submitted for publishing|is publishing|in review|publishing\b|will be available|successfully published", re.I)
    sOutcome, lTexts = "unknown", []
    for iTry in range(24):
        lTexts = pageMessages(page)
        sAll = " | ".join(lTexts) + " | " + page.title()
        if oAck.search(sAll) or ("/pricing" not in page.url and "kdp.amazon.com" in page.url):
            sOutcome = "submitted"
            break
        if any(re.search(r"fix the highlighted|invalid|must be|is required", t, re.I) and not re.search(r"possible spelling errors", t, re.I) for t in lTexts):
            sOutcome = "rejected"
            break
        time.sleep(5)
    log("URL after Publish: " + page.url + "; outcome judged " + sOutcome)
    dumpControls(page, "after Publish")
    lTexts = logMessages(page, "after Publish")
    say("Page now: " + page.title() + ", at " + page.url)
    if sOutcome == "submitted":
        page.goto(c_sBookshelfUrl)
        time.sleep(5)
        sStatus = bookshelfStatus(page, "after publishing")
        say("Submitted. KDP's Bookshelf now shows the book as: " + sStatus + ". KDP said: " + (" | ".join(t for t in lTexts if oAck.search(t)) or "see the log") + ".")
        log("PUBLISH OUTCOME: submitted; Bookshelf status " + sStatus)
        if sStatus == "Draft":
            say("The Bookshelf still says Draft, so KDP may not have taken the submission; check it before running again.")
            return "unknown"
        if sStatus == "not shown": say("The Bookshelf's status label could not be read, which has happened on this account's page before; KDP's acknowledgement is the evidence that the submission was taken.")
        return "submitted"
    if sOutcome == "rejected":
        say("KDP refused to publish. Its messages: " + " | ".join(lTexts)[:400])
        unresolved("Publish", "KDP refused: " + " | ".join(lTexts)[:300])
        return "draft"
    say("Pressed Publish, but KDP showed neither an acknowledgement nor an error within two minutes. Outcome unknown; check the Bookshelf before trying again.")
    log("PUBLISH OUTCOME: unknown")
    return "unknown"


c_lFlags = ["--ask", "--book", "--chrome", "--copy-profile", "--create-new", "--inspect", "--no-publish", "--reupload", "--start-at", "--stop-after", "--title-id"]
c_dExit = {"submitted": 0, "draft": 5, "blocked": 5, "unknown": 6}
c_lBlocking = ["DRM", "Manuscript", "Cover", "Confirmation that the answers are accurate", "Save as Draft", "Save and Continue to content", "Save and Continue to pricing", "Pricing tab", "Publish"]  # only these stop Publish: a refused save, a failed upload, or the confirmation box; everything else is read out afterwards


def checkOptions():
    """Rejects unknown or misspelled options and impossible combinations before anything else happens."""
    lArgs = sys.argv[1:]
    iIndex = 0
    while iIndex < len(lArgs):
        sArg = lArgs[iIndex]
        if sArg not in c_lFlags: return "Unknown option " + sArg + ". Allowed: " + " ".join(c_lFlags)
        if sArg in ("--book", "--start-at", "--stop-after", "--title-id"):
            if iIndex + 1 >= len(lArgs) or lArgs[iIndex + 1].startswith("--"): return sArg + " needs a value"
            sValue = lArgs[iIndex + 1]
            if sArg == "--start-at" and sValue not in ("content", "pricing"): return "--start-at takes content or pricing"
            if sArg == "--stop-after" and sValue not in ("details", "content", "pricing"): return "--stop-after takes details, content or pricing"
            if sArg == "--title-id" and not re.fullmatch(r"[A-Z0-9]{10,16}", sValue): return "--title-id should look like ABCDE12345, ten to sixteen capital letters and digits"
            iIndex += 1
        iIndex += 1
    sStart, sStop = argValue("--start-at"), argValue("--stop-after")
    if sStart == "pricing" and sStop in ("details", "content"): return "--stop-after " + sStop + " comes before --start-at pricing"
    if sStart == "content" and sStop == "details": return "--stop-after details comes before --start-at content"
    return ""


def checkAnswers(d):
    """Makes sure the JSON holds every answer the script needs, with values it knows how to enter."""
    lProblems = []
    for sKey in ["language", "title", "subtitle", "editionNumber", "author", "description", "publishingRights", "sexuallyExplicit", "primaryMarketplace", "categories", "keywords", "manuscriptFile", "drm", "coverFile", "aiContent", "kdpSelect", "territories", "royalty", "priceUsd"]:
        if sKey not in d: lProblems.append("missing " + sKey)
    if lProblems: return lProblems
    if len(d["author"].split()) < 2: lProblems.append("author needs a first and last name")
    if not d["publishingRights"].lower().startswith("i own"): lProblems.append("publishingRights: only 'I own the copyright...' is supported")
    if d["sexuallyExplicit"].strip().lower() not in ("yes", "no"): lProblems.append("sexuallyExplicit must be Yes or No")
    if d["primaryMarketplace"].lower() not in ("amazon.com", "us"): lProblems.append("primaryMarketplace: only Amazon.com is supported")
    if len(d["categories"]) != 3: lProblems.append("categories must list exactly 3 paths")
    if not (1 <= len(d["keywords"]) <= 7): lProblems.append("keywords must list 1 to 7 phrases")
    if not d["drm"].strip().lower().startswith(("yes", "no")): lProblems.append("drm must start with Yes or No")
    for sKey in ["used", "texts", "images", "translations", "tools"]:
        if sKey not in d["aiContent"]: lProblems.append("aiContent." + sKey + " missing")
    if d["aiContent"].get("used", "").lower() != "yes": lProblems.append("aiContent.used: only Yes is supported by this script")
    if not d["kdpSelect"].lower().startswith(("do not", "enroll")): lProblems.append("kdpSelect must start with 'Do not' or 'Enroll'")
    if not d["territories"].lower().startswith("all"): lProblems.append("territories: only 'All territories' is filled by this script")
    if not d["royalty"].strip().startswith(("35", "70")): lProblems.append("royalty must be 35% or 70%")
    try:
        fPrice = float(d["priceUsd"])
        if d["royalty"].strip().startswith("70") and not (2.99 <= fPrice <= 12.99): lProblems.append("priceUsd must be 2.99 to 12.99 for the 70% plan")
    except Exception:
        lProblems.append("priceUsd must be a number")
    return lProblems


def finish(page, browser, sState, sNote):
    """Reports the run's outcome, keeps the browser open for checking, and returns the exit code for that state."""
    say(sNote + " Log: " + sLogPath)
    if sState == "submitted": say("Follow-ups: listen to the book's Amazon page when it goes live; add the book to your Amazon author page; with DRM off, download the published ebook and spot-check notes and links.")
    log("RUN OUTCOME: " + sState + " (exit code " + str(c_dExit.get(sState, 1)) + ")")
    pause("The browser window stays open so you can check anything. Close it yourself when done.")
    try:
        browser.close()
    except Exception as oError:
        log("Browser already closed: " + str(oError)[:80])
    return c_dExit.get(sState, 1)


def loadPlaywright():
    """Imports Playwright after the log is open, so a missing or broken installation leaves a useful log line."""
    global PlaywrightTimeout, sync_playwright
    try:
        from playwright.sync_api import TimeoutError as oTimeout, sync_playwright as fStart
        import playwright
        PlaywrightTimeout, sync_playwright = oTimeout, fStart
        log("Playwright " + str(getattr(playwright, "__version__", "version unknown")) + " imported from " + os.path.dirname(playwright.__file__))
        return True
    except Exception as oError:
        log("Playwright could not be imported: " + traceback.format_exc())
        say("The Playwright package is not usable: " + str(oError)[:160] + ". Run kdpSubmit.cmd again so it can install it, and send the log if that fails.")
        return False


def ensureEpub(sEpub):
    """Rebuilds the EPUB with build.py when it is missing or older than the manuscript and its build files, so the submission carries the latest text. Returns an empty string, or the reason the build failed."""
    sStem = os.path.splitext(os.path.basename(sEpub))[0]
    # A BOOK PUBLISHING PROJECT (configs\\books.inix, books\\<Book>\\) builds with buildBooks; an older project of one
    # book builds with its own build.py beside the manuscript.
    sBookDir = os.path.join(sProject, "books", sStem)
    if os.path.isfile(os.path.join(sProject, "configs", "books.inix")) and os.path.isdir(sBookDir):
        lSources = [os.path.join(sBookDir, sStem + sExt) for sExt in (".md", ".bib", ".csl", ".jpg", ".css")]
        lSources = [sPath for sPath in lSources if os.path.exists(sPath)]
        bStale = not os.path.exists(sEpub) or any(os.path.getmtime(sPath) > os.path.getmtime(sEpub) for sPath in lSources)
        if not bStale: return ""
        sBuild = os.path.join(sFolder, "buildBooks.py")
        if not os.path.exists(sBuild): return "the EPUB is out of date and scripts\\buildBooks.py is missing"
        say("Rebuilding " + sStem + " with buildBooks, since its sources are newer than its EPUB.")
        oResult = subprocess.run([sys.executable, sBuild, "--book", sStem], cwd=sProject, capture_output=True, text=True, encoding="utf-8", errors="replace")
        log("buildBooks exit " + str(oResult.returncode))
        for sLine in ((oResult.stdout or "") + (oResult.stderr or "")).strip().splitlines()[-40:]: log("  | " + sLine)
        if oResult.returncode != 0 or not os.path.exists(sEpub): return "buildBooks did not produce a ready EPUB; read its audit in results\\"
        return ""
    lSources = [os.path.join(sProject, sStem + sExt) for sExt in (".md", ".yaml", ".bib", ".csl", ".jpg")] + [os.path.join(sProject, sName) for sName in ("book.css", "tocMarker.lua")]
    lSources = [sPath for sPath in lSources if os.path.exists(sPath)]
    if not lSources: return "no manuscript source found beside the project; expected " + sStem + ".md"
    bStale = not os.path.exists(sEpub) or any(os.path.getmtime(sPath) > os.path.getmtime(sEpub) for sPath in lSources)
    log("EPUB " + sEpub + (" is missing" if not os.path.exists(sEpub) else " is " + ("older than a source; rebuilding" if bStale else "newer than every source; kept")) + "; sources checked: " + ", ".join(os.path.basename(sPath) for sPath in lSources))
    if not bStale: return ""
    sBuild = os.path.join(sProject, "build.py")
    if not os.path.exists(sBuild): return "the EPUB is out of date and build.py is missing"
    say("Rebuilding the EPUB from " + sStem + ".md with build.py, since the manuscript is newer than the EPUB.")
    oResult = subprocess.run([sys.executable, sBuild], cwd=sProject, capture_output=True, text=True, encoding="utf-8", errors="replace")
    sOut = ((oResult.stdout or "") + (oResult.stderr or "")).strip()
    log("build.py exit " + str(oResult.returncode))
    for sLine in sOut.splitlines()[-40:]: log("  | " + sLine)
    if oResult.returncode != 0: return "build.py ended with exit code " + str(oResult.returncode) + "; see its log in logs\\"
    if not os.path.exists(sEpub): return "build.py finished but " + sEpub + " was not produced"
    log("EPUB rebuilt: " + format(os.path.getsize(sEpub), ",") + " bytes, sha256 " + fileSha256(sEpub)[:16])
    return ""


def main():
    global dAnswers, sLogPath
    os.makedirs(os.path.join(sProject, "logs"), exist_ok=True)
    sLogPath = os.path.join(sProject, "logs", logStem() + "-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".log")
    log("kdpSubmit.py started; " + c_sVersion + "; script " + os.path.abspath(__file__))
    print("kdpSubmit " + c_sVersion.split(":")[0])
    log("Python " + sys.version.split()[0] + " on " + platform.platform() + "; script folder " + sFolder + "; project folder " + sProject + "; command line " + " ".join(sys.argv))
    sBad = checkOptions()
    if sBad:
        say(sBad + ". Nothing was done.")
        return 2
    if not loadPlaywright(): return 2
    sStopAfter, sTitleId, sStartAt = argValue("--stop-after"), argValue("--title-id"), argValue("--start-at")
    sAnswers = loadAnswers()
    if not sAnswers:
        say("Missing " + os.path.join(sProject, "configs", answersName()))
        return 2
    log("Answers loaded from " + sAnswers + "; prepared " + str(dAnswers.get("prepared")) + "; status: " + str(dAnswers.get("status")))
    lProblems = checkAnswers(dAnswers)
    if lProblems:
        say("The answers file cannot be used as it stands: " + "; ".join(lProblems) + ". Nothing was done.")
        return 2
    sBuildProblem = ensureEpub(os.path.join(sProject, dAnswers["manuscriptFile"]))
    if sBuildProblem:
        say("The EPUB could not be brought up to date: " + sBuildProblem + ". Nothing was sent to KDP.")
        return 2
    for sKey in ("manuscriptFile", "coverFile"):
        sPath = os.path.join(sProject, dAnswers[sKey])
        log(sKey + " " + sPath + (" exists, " + format(os.path.getsize(sPath), ",") + " bytes, sha256 " + fileSha256(sPath)[:16] if os.path.exists(sPath) else " MISSING"))
        if not os.path.exists(sPath):
            say("Missing file " + dAnswers[sKey] + ". Run build.cmd first.")
            return 2
    bChrome = "--chrome" in sys.argv
    sLocal = os.environ.get("LOCALAPPDATA", sFolder)
    sSource = os.path.join(sLocal, "Google", "Chrome", "User Data") if bChrome else os.path.join(sLocal, "Microsoft", "Edge", "User Data")
    sProfile = os.path.join(sLocal, "KdpSubmit", "chromeProfile" if bChrome else "edgeProfile")
    closeLeftovers(sProfile)
    time.sleep(2)
    if "--copy-profile" in sys.argv:
        copyProfile(sSource, sProfile, "chrome.exe" if bChrome else "msedge.exe")
    elif os.path.isdir(sProfile):
        log("Keeping the automated browser profile from the last run at " + sProfile + "; its KDP sign-in is remembered")
    else:
        os.makedirs(sProfile, exist_ok=True)
        log("New automated browser profile at " + sProfile + "; KDP will ask for one sign-in, which is then remembered")
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(sProfile, channel="chrome" if bChrome else "msedge", headless=False, args=["--start-maximized"], viewport=None, accept_downloads=True, ignore_default_args=["--enable-automation"])
        log("Launched " + ("Google Chrome" if bChrome else "Microsoft Edge") + " with the automated profile")
        page = browser.pages[0] if browser.pages else browser.new_page()
        page.set_default_timeout(20000)
        watchBrowser(page)
        say("Opening KDP in " + ("Chrome" if bChrome else "Edge") + ".")
        if "--inspect" in sys.argv:
            page.goto(c_sBookshelfUrl)
            time.sleep(3)
            if not waitForSignIn(page): return 1
            pause("Inspect mode. In the browser window, move to the KDP page you want recorded, then come back here.")
            dumpControls(page, "inspect: " + page.url)
            logMessages(page, "inspect")
            say("Controls written to " + sLogPath)
            return 0
        if not sTitleId:
            sFound = findDraft(page)
            if sFound == "STOP": return finish(page, browser, "blocked", "Nothing was changed.") if sBookStatus or "bookshelf" in page.url else 1
            if sFound == "AMBIGUOUS": return finish(page, browser, "blocked", "More than one draft matches the title, so nothing was changed.")
            sTitleId = sFound
        if not sTitleId and "--create-new" not in sys.argv:
            return finish(page, browser, "blocked", "No draft of " + dAnswers["title"] + " was found and --create-new was not given, so no title was created.")
        if sTitleId and sStartAt:
            page.goto(c_sTitleSetup + sTitleId + "/" + sStartAt)
            log("Opened draft " + sTitleId + " at the " + sStartAt + " tab, as asked")
            if "signin" in page.url and not waitForSignIn(page): return 1
            if sStartAt == "content":
                fillContent(page)
                if sStopAfter == "content": return finish(page, browser, "draft" if not lUnresolved else "blocked", "Stopped after Content, as asked.")
                if not saveAndContinue(page, "pricing"):
                    finalReview(page)
                    return finish(page, browser, "blocked", "KDP would not leave the Content tab.")
            fillPricing(page)
            if sStopAfter == "pricing": return finish(page, browser, "draft" if not lUnresolved else "blocked", "Stopped after Pricing, as asked; nothing was published.")
            sState = finalReview(page)
            return finish(page, browser, sState, "Finished with outcome: " + sState + ".")
        if sTitleId:
            page.goto(c_sTitleSetup + sTitleId + "/details")
            log("Opened draft " + sTitleId)
        else:
            page.goto(c_sBookshelfUrl)
            time.sleep(2)
            clickButton(page, "Create new title", ["Create new title", "Create"])
            clickButton(page, "Create eBook", ["Create eBook", "Kindle eBook"], False)
            time.sleep(3)
            log("New title URL " + page.url + " (--create-new was given)")
        if "signin" in page.url and not waitForSignIn(page): return 1
        if not fillDetails(page): return finish(page, browser, "blocked", "Stopped on the Details tab.")
        if sStopAfter == "details": return finish(page, browser, "draft" if not lUnresolved else "blocked", "Stopped after Details, as asked. Draft saved.")
        if not saveAndContinue(page, "content"):
            finalReview(page)
            return finish(page, browser, "blocked", "KDP would not leave the Details tab.")
        fillContent(page)
        if sStopAfter == "content": return finish(page, browser, "draft" if not lUnresolved else "blocked", "Stopped after Content, as asked. Draft saved.")
        if not saveAndContinue(page, "pricing"):
            finalReview(page)
            return finish(page, browser, "blocked", "KDP would not leave the Content tab.")
        fillPricing(page)
        if sStopAfter == "pricing": return finish(page, browser, "draft" if not lUnresolved else "blocked", "Stopped after Pricing, as asked; nothing was published.")
        sState = finalReview(page)
        return finish(page, browser, sState, "Finished with outcome: " + sState + ".")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except PlaywrightTimeout as oError:
        log("TIMEOUT: " + traceback.format_exc())
        say("A page did not respond in time: " + str(oError)[:200] + ". Details in the log.")
        sys.exit(3)
    except KeyboardInterrupt:
        say("Stopped by Control+C. The draft saved so far stays on KDP.")
        sys.exit(130)
    except SystemExit:
        raise
    except Exception as oError:
        log("CRASH: " + traceback.format_exc())
        say("The script hit an error: " + str(oError)[:200] + ". The full details are in the log; the draft saved so far stays on KDP.")
        sys.exit(4)
