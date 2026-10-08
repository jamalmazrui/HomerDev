"""kdpBooks.py -- keeps the metadata of every book on the KDP Bookshelf in step with one .inix file per book, under data\\books\\.

HOW IT WORKS. The script opens the KDP Bookshelf in the same remembered Edge window that kdpSubmit uses, reads every page of
the Bookshelf for each title's row id, ASIN and status, then, book by book, opens the Details and Pricing pages and reads what KDP
holds: title, subtitle, edition, author, series, language, description, publishing rights, adult content, primary marketplace,
keywords, categories, KDP Select and the US list price. That becomes the [kdp] section of data\\books\\<Title>.inix. When the
file's [proposed] section asks for something KDP does not yet hold (description, keywords, categories, price), the script applies
it: fills the Details tab, answers the Adult-only question with No when KDP has no answer, chooses the categories in KDP's picker,
sets DRM to No on the Content tab and ticks the consent box (so every book can also be bought as a DRM-free EPUB), sets the price
and royalty on the Pricing tab, and presses Publish. A book whose [kdp] already matches its [proposed] is left alone, so the run
can be repeated. Title, subtitle, author and edition are locked by KDP after publication and are never changed.

USAGE
  scripts\\kdpBooks.cmd                read every published book and apply what its file proposes
  scripts\\kdpBooks.cmd --asin B0...   one book
  scripts\\kdpBooks.cmd --no-publish   apply, but stop at each saved draft instead of pressing Publish
  scripts\\kdpBooks.cmd --export       read only; the files' [kdp] sections are rewritten and nothing on KDP is changed
  scripts\\kdpBooks.cmd --dry-run      read the Bookshelf only and list the books
  scripts\\kdpBooks.cmd --categories   walk KDP's whole category picker once and write every menu and placement to data\\kdpCategories.inix and .md; nothing is saved on KDP

Every run writes logs\\<Project>-kdpBooks-<date>-<time>.log. Exit codes: 0 done; 2 nothing to do or bad option;
3 no sign-in; 4 crash; 5 some book could not be read or applied, listed at the end.
"""

import datetime, glob, html, os, platform, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kdpSubmit as k

c_iSignInMinutes = 20
c_lFlags = ["--apply", "--asin", "--categories", "--dry-run", "--export", "--no-publish"]  # --apply is accepted and means nothing now: applying is what the script does
c_sAsinPattern = r"\b(B0[A-Z0-9]{8}|\d{9}[\dX])\b"
c_sVersion = "2026-10-05 version 14: a description that differs from KDP's only in its bullet markers (KDP shows a bullet character, the file writes a dash) no longer counts as a change, so a matching book is not resubmitted; was version 13, from the 08:13 categories run, which walked all 32 top-level categories in 26 minutes but read four of them wrongly (Science & Math came out as a copy of Romance, Parenting & Relationships as another tree, Foreign Languages and Nonfiction as empty), because KDP adds and removes picker menus as the chain changes and the walk counted menus from a fixed starting point: the chain's top menu is now found afresh at every step as the last menu holding the top-level list, every pick is checked by reading the menu's chosen option back, a level that shows the top-level list again or repeats the previous category's sub-menus is retried, and a category not read after two tries is left for the next run instead of being marked done; a plain run now checks each proposed category path against the walked list before the picker opens, drops a path KDP does not offer and says so, and leaves alone paths under a top-level category not yet walked; was version 12, from the 07:36 categories run, which walked four top-level categories in ten minutes and crashed when the Details page reloaded under it: the walk now writes data\\kdpCategories.inix and .md after every top-level category and skips, on the next run, the ones already walked; when the picker's menus vanish it reopens the picker, replays the path and goes on, trying each branch twice before skipping it; a top-level category that reads empty is retried the same way; was version 11: --categories walks KDP's whole category picker once, through one book's Details page, and writes every menu and placement to data\\kdpCategories.inix and .md, pressing Cancel at the end so nothing is saved; with that list the proposed paths can be ones KDP offers, and General is chosen only on purpose; was version 10, from the 16:46 run: the Content tab's accuracy confirmation boxes are ticked before Save and Continue, and a refusal for either box brings one more look; the picker fixes are in kdpSubmit version 29; was version 9, from the 15:15 run, which published 13 of 22 books: when KDP still asks for the DRM consent after the box was looked for, the Content tab's controls are logged and the box is looked for once more before giving up; KDP's Categories update notice is closed before the picker opens; the picker, DRM and placement fixes are in kdpSubmit version 28; was version 8: applying is the default: each book is read and then, when its file proposes something KDP does not hold, changed and published in the same pass, with --export for a read-only run; the Adult-only question is answered No where KDP has no answer (three older books had none, and the category picker refused to open); DRM is set to No with KDP's consent box ticked on every book, so each can be bought as a DRM-free EPUB; a book already matching its file is left alone; was version 7: a single-dash option such as -apply is read as --apply (the 14:12 run typed one dash and got a plain export); each Bookshelf row's cover image id is read, for matching Author Central's title-less cards; was version 6: the book files live in data\\books\\, which is kept across sessions, not data\\books\\; categories are read as paths from KDP's own list; --apply sends each file's [proposed] values to KDP through kdpSubmit's description, keyword, category and pricing routines and presses Publish, with --no-publish to stop at the saved draft; was version 5, from the 13:36 run, which logged the Bookshelf's controls at last: a 10, 25 or 50 Per Page drop-down and page links 1, 2, 3 and next. The drop-down is set to 50 Per Page first, so every book is on one page, and the page links are followed by number when it is not; rows are compared as sets of ids, since scrolling doubles the title spans; was version 4, from the 13:22 run: the Bookshelf loop is rebuilt so that scrolling, the foot-of-page control dump and the Next control are all reached (version 3 stopped before them when scrolling only doubled the title spans); the Next control is the last visible one of several candidates, since a carousel at the top has its own; was version 3, from the 13:12 run: the Bookshelf showed ten rows and no paging control at all, so the page is scrolled to its end and any Load more or Show more button pressed until the rows stop growing, and the controls at the foot of the page are logged; the series block is read whole; was version 2, from the 12:41 and 12:42 runs: the title id comes from the row's own title-setup link, or from clicking the title, not from the row's span id, which is a different code (every Details page opened as a 404); the Bookshelf's Next link is pressed only after the page has fully loaded, since its handler is not attached at domcontentloaded (page 1 was read twice); an interrupted navigation no longer crashes the run; was version 1: reads every published book's KDP metadata into data\\books\\<Title>.inix; nothing is changed on KDP"


def log(sText): return k.log(sText)
def say(sText): return k.say(sText)


def fileStem(sTitle):
    """Strange truths: Objective Stories... -> Strange_Truths; words capitalized, punctuation dropped, the subtitle after a colon dropped."""
    sMain = sTitle.split(":")[0]
    lWords = [w for w in re.sub(r"[^A-Za-z0-9 ]+", " ", sMain).split() if w]
    return "_".join(w[:1].upper() + w[1:] for w in lWords) or "Untitled"


def htmlToText(sHtml):
    """KDP's description HTML to the plain form the answers files use: paragraphs apart, '- ' bullets, **bold**."""
    s = sHtml or ""
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", "", s)
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</?(b|strong)\b[^>]*>", "**", s)
    s = re.sub(r"(?i)<h[1-6][^>]*>", "**", s)
    s = re.sub(r"(?i)</h[1-6]>", "**\n\n", s)
    s = re.sub(r"(?i)<li[^>]*>", "- ", s)
    s = re.sub(r"(?i)</li>", "\n", s)
    s = re.sub(r"(?i)</(p|div|ul|ol)>", "\n\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r" *\n *", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def bookshelfRows(page, dSettings=None):
    """Every title row on every page of the KDP Bookshelf: dictionaries with id, title, asin, status. Series rows (Book in ...) are skipped."""
    sUrl = (dSettings or {}).get("bookshelfUrl", k.c_sBookshelfUrl)
    page.goto(sUrl, wait_until="domcontentloaded")
    time.sleep(1)
    if "kdp.amazon.com" not in page.url or "/ap/" in page.url:
        say("KDP wants its own sign-in. Sign in in the window; I am waiting up to " + str(c_iSignInMinutes) + " minutes.")
        dtEnd = datetime.datetime.now() + datetime.timedelta(minutes=c_iSignInMinutes)
        while datetime.datetime.now() < dtEnd and ("kdp.amazon.com" not in page.url or "/ap/" in page.url): time.sleep(3)
        if "kdp.amazon.com" not in page.url or "/ap/" in page.url: return None
    lRows = []

    def readRows():
        return page.evaluate("""(sPattern) => {
            const o = new RegExp(sPattern);
            const lOut = [];
            for (const t of document.querySelectorAll("span.title-link-label")) {
                const sMine = (t.innerText || "").trim();
                if (!sMine || /^Book in /i.test(sMine)) continue;
                let e = t, sRow = "";
                for (let i = 0; i < 16 && e; i++) {
                    const sText = (e.innerText || "").replace(/\\s+/g, " ");
                    if (Array.from(e.querySelectorAll("span.title-link-label")).some(x => { const v = (x.innerText || "").trim(); return v && v !== sMine && !/^Book in /i.test(v); })) break;
                    sRow = sText;
                    if (/ASIN:?\\s*[A-Z0-9]{10}/i.test(sText)) break;
                    e = e.parentElement;
                }
                const m = sRow.match(/ASIN:?\\s*([A-Z0-9]{10})/i) || sRow.match(o);
                let sSetup = ""; if (e) for (const a of e.querySelectorAll("a[href]")) { const mm = (a.getAttribute("href") || "").match(/title-setup\\/kindle\\/([A-Z0-9]+)\\//); if (mm) { sSetup = mm[1]; break; } }
                const oImg = e ? e.querySelector("img[src*='/images/I/']") : null;
                const sCover = oImg ? ((oImg.getAttribute("src").match(/\\/images\\/I\\/([^._]+)/) || [, ""])[1]) : "";
                lOut.push({id: sSetup, cover: sCover, spanId: (t.id || "").split("-").pop(), hrefs: e ? Array.from(e.querySelectorAll("a[href]")).map(a => a.getAttribute("href")).slice(0, 6) : [], title: sMine, asin: m ? m[1].toUpperCase() : "", status: /\\bLive\\b/i.test(sRow) ? "Live" : (/In Review|Publishing/i.test(sRow) ? "In Review" : (/Draft/i.test(sRow) ? "Draft" : "")), review: /updates in review/i.test(sRow)});
            }
            return lOut;
        }""", c_sAsinPattern)

    def addRows(lHere):
        lNew = [r for r in lHere if not any(r["spanId"] == x["spanId"] and r["asin"] == x["asin"] and r["title"] == x["title"] for x in lRows)]
        lRows.extend(lNew)
        return len(lNew)

    def perPage50():
        """Sets the Bookshelf's Per Page drop-down to its largest value, so every book is on one page. Returns True when it changed."""
        try:
            oSelect = page.locator("select").filter(has_text=re.compile(r"per page", re.I))
            if not oSelect.count(): return False
            lValues = oSelect.first.evaluate("o => Array.from(o.options).map(x => [x.value, x.text])")
            lLarge = sorted(lValues, key=lambda v: int(re.sub(r"\D", "", v[1]) or 0))
            if not lLarge: return False
            sValue, sText = lLarge[-1]
            if oSelect.first.evaluate("o => o.options[o.selectedIndex] ? o.options[o.selectedIndex].text : ''") == sText:
                log("Per Page is already " + sText)
                return False
            say("Setting the Bookshelf to " + sText.strip() + ".")
            oSelect.first.select_option(value=sValue)
            try:
                page.wait_for_load_state("domcontentloaded")
            except Exception:
                pass
            time.sleep(3)
            log("Per Page set to " + sText.strip() + "; title spans now " + str(page.locator("span.title-link-label").count()))
            return True
        except Exception as oError:
            log("Per Page drop-down could not be set: " + str(oError)[:160])
            return False

    for iPage in range(1, 30):
        say("Reading Bookshelf page " + str(iPage) + "; waiting up to 20 seconds for its rows.")
        try:
            page.locator("span.title-link-label").first.wait_for(state="attached", timeout=20000)
        except Exception:
            log("No title rows on Bookshelf page " + str(iPage))
        try:
            page.wait_for_load_state("load", timeout=15000)  # the Bookshelf's links work only after its full load
        except Exception:
            log("The Bookshelf did not reach its load event within 15 seconds")
        time.sleep(1)
        if iPage == 1 and perPage50():
            try:
                page.locator("span.title-link-label").first.wait_for(state="attached", timeout=20000)
            except Exception:
                pass
            time.sleep(1)
        lHere = readRows()
        if iPage == 1 and lHere: log("Row links of the first row, for the next fix: " + str(lHere[0].get("hrefs")))
        iNew = addRows(lHere)
        say("Bookshelf page " + str(iPage) + ": " + str(len(lHere)) + " row" + ("" if len(lHere) == 1 else "s") + ", " + str(iNew) + " new.")
        if iPage > 1 and not iNew:
            log("Bookshelf page " + str(iPage) + " repeats the one before; the Bookshelf is read")
            break
        for iScroll in range(8):  # rows that load as the page scrolls, or behind a Load more button
            iSpans = page.locator("span.title-link-label").count()
            page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1.5)
            k.clickButton(page, "Load more", ["Load more", "View more", "More titles"], False)
            if page.locator("span.title-link-label").count() == iSpans and iScroll > 0: break
        iMore = addRows(readRows())
        if iMore: log("Scrolling the Bookshelf showed " + str(iMore) + " more row" + ("" if iMore == 1 else "s"))
        log("Controls at the foot of the Bookshelf: " + str(page.evaluate("() => Array.from(document.querySelectorAll('a, button, select, [role=button], [role=link]')).filter(o => o.getBoundingClientRect().top > window.innerHeight * 0.5 || /next|prev|page|more|per page|rows/i.test((o.innerText || '') + (o.getAttribute('aria-label') || '') + (o.title || '') + (o.querySelector('img') ? o.querySelector('img').alt : ''))).map(o => o.tagName.toLowerCase() + ' ' + ((o.innerText || o.getAttribute('aria-label') || o.title || (o.querySelector('img') ? o.querySelector('img').alt : '') || '').trim().slice(0, 40)) + ' [' + (o.className || '').toString().slice(0, 40) + '] ' + (o.getAttribute('href') || '').slice(0, 60)).slice(0, 30)")))
        oNext = page.locator("a[href='#" + str(iPage + 1) + "']")  # the Bookshelf's page links are 1, 2, 3 and next
        if not oNext.count(): oNext = page.locator("a[href='#next']")
        if not oNext.count(): oNext = page.get_by_role("link", name=re.compile(r"^next", re.I))
        if not oNext.count(): oNext = page.get_by_role("button", name=re.compile(r"^next", re.I))
        if not oNext.count(): oNext = page.locator("a[aria-label*='Next' i], button[aria-label*='Next' i], .a-pagination .a-last a, a[title*='Next' i], [class*='pagination'] a:last-child, [class*='Pagination'] a:last-child")
        lVisible = [oNext.nth(n) for n in range(oNext.count()) if oNext.nth(n).is_visible()]
        if not lVisible:
            log("No visible Next control on the Bookshelf; " + str(len(lRows)) + " rows read")
            break
        oLink = lVisible[-1]  # the paging control sits at the foot; a carousel's own Next sits higher
        sClass = (oLink.get_attribute("class") or "") + " " + (oLink.locator("xpath=..").get_attribute("class") or "")
        if "disabled" in sClass or oLink.get_attribute("aria-disabled") == "true":
            log("The Next control is disabled; the last Bookshelf page is read")
            break
        lBefore = set(r["spanId"] for r in lHere)
        say("Pressing the page " + str(iPage + 1) + " link of the Bookshelf.")
        oLink.scroll_into_view_if_needed()
        oLink.click()
        bChanged = False
        for iTick in range(15):  # wait until the rows are different ones, up to 15 seconds; sets, because scrolling doubles the spans
            time.sleep(1)
            lNow = set(page.evaluate("() => Array.from(document.querySelectorAll('span.title-link-label')).map(o => (o.id || '').split('-').pop())"))
            if lNow and lNow != lBefore: bChanged = True; break
        if not bChanged:
            log("Pressing Next did not change the rows within 15 seconds; the Bookshelf is read as far as it shows")
            break

    log("Bookshelf: " + str(len(lRows)) + " title row" + ("" if len(lRows) == 1 else "s"))
    for r in lRows: log("  " + (r["asin"] or "no ASIN   ") + " " + (r["status"] or "no status") + (" (updates in review)" if r["review"] else "") + " id " + r["id"] + (" cover " + r["cover"] if r.get("cover") else "") + " " + r["title"])
    return lRows


def titleIdByClicking(page, r):
    """Opens the book's setup page by clicking its title on the Bookshelf, as kdpSubmit does, and returns the title id from the URL."""
    page.goto(k.c_sBookshelfUrl, wait_until="domcontentloaded")
    try:
        page.wait_for_load_state("load", timeout=15000)
    except Exception:
        pass
    oSpan = page.locator("span.title-link-label[id$='" + r["spanId"] + "']")
    if not oSpan.count(): oSpan = page.locator("span.title-link-label", has_text=r["title"][:60])
    if not oSpan.count():
        log("The title " + r["title"][:60] + " is not on the Bookshelf page shown; its setup page cannot be opened by clicking")
        return ""
    oSpan.first.click()
    try:
        page.wait_for_url(re.compile(r"title-setup/kindle/[A-Z0-9]+/"), timeout=20000)
    except Exception:
        log("Clicking the title did not open its setup page; URL " + page.url)
        return ""
    sId = k.titleIdFrom(page.url)
    log("Title id of " + r["title"][:60] + " from its setup page: " + sId)
    return sId


def readDetails(page, sId):
    """Reads the Details page of one title. Returns a dictionary, or None when KDP would not open the page."""
    try:
        page.goto(k.c_sTitleSetup + sId + "/details", wait_until="domcontentloaded")
    except Exception as oError:  # KDP interrupts the navigation with its own redirect for a locked or unknown title
        log("Opening the Details page of " + sId + " was interrupted: " + str(oError).splitlines()[0][:160])
    for iTick in range(30):
        time.sleep(1)
        if sId in page.url and page.locator("#data-title").count(): break
        if "bookshelf" in page.url and sId not in page.url: break
    if sId not in page.url or not page.locator("#data-title").count():
        log("KDP did not open the Details page of " + sId + "; URL " + page.url + " (a book with an update in review is locked)")
        return None
    time.sleep(2)
    d = page.evaluate("""() => {
        const v = (s) => { const l = Array.from(document.querySelectorAll(s)); const o = l.find(x => !x.disabled) || l[0]; return o ? (o.value || "") : ""; };
        const t = (s) => { const o = document.querySelector(s); return o ? (o.innerText || "").replace(/\\s+/g, " ").trim() : ""; };
        const checked = (s) => { const o = Array.from(document.querySelectorAll(s)).find(x => x.checked); return o ? (o.value || o.id || "yes") : ""; };
        const d = {};
        d.title = v("#data-title"); d.subtitle = v("#data-subtitle"); d.edition = v("#data-edition-number");
        d.author = (v("#data-primary-author-first-name") + " " + v("#data-primary-author-last-name")).trim();
        d.language = v("#data-language-native");
        const oSeries = document.querySelector("#edit_series_description") || document.querySelector("[id*=series]");
        let e = oSeries; for (let i = 0; i < 4 && e && !/series/i.test(e.innerText || "") ; i++) e = e.parentElement;
        d.seriesText = e ? (e.innerText || "").replace(/\\s+/g, " ").trim().slice(0, 600) : "";
        const mSeries = d.seriesText.match(/(?:Series(?: name)?:?\\s*)([^\\.|]{2,80})/i);
        const aSeries = e ? e.querySelector("a[href*='series']") : null;
        d.series = (aSeries && aSeries.innerText.trim()) || (mSeries ? mSeries[1].trim() : "") || (d.seriesText ? "(in a series; name not read: " + d.seriesText.slice(0, 80) + ")" : "");
        d.publishingRights = checked("#non-public-domain") ? "I own the copyright and I hold the necessary publishing rights." : (checked("#public-domain") ? "Public domain" : "");
        d.adultContent = checked("input[name='data[is_adult_content]-radio']") === "true" ? "Yes" : (checked("input[name='data[is_adult_content]-radio']") === "false" ? "No" : "");
        d.readingAgeStart = v("#data-reading-interest-age-start-input-native"); d.readingAgeEnd = v("#data-reading-interest-age-end-input-native");
        d.primaryMarketplace = v("select[name='data[digital][home_marketplace]']");
        d.keywords = []; for (let i = 0; i < 7; i++) { const s = v("#data-keywords-" + i); if (s.trim()) d.keywords.push(s.trim()); }
        d.categoriesText = t(".react-categories");
        d.descriptionHtml = (window.CKEDITOR && Object.values(CKEDITOR.instances).length) ? Object.values(CKEDITOR.instances)[0].getData() : "";
        return d;
    }""")
    if not d.get("descriptionHtml"):
        try:
            d["descriptionHtml"] = page.frame_locator("div.editor iframe").first.locator("body").inner_html()
        except Exception as oError:
            log("Description editor not readable: " + str(oError)[:100])
    d["description"] = htmlToText(d.get("descriptionHtml", ""))
    d["categories"] = categoriesFromText(d.get("categoriesText", ""))
    log("Details of " + sId + ": title '" + d["title"] + "', subtitle '" + d["subtitle"] + "', series '" + d["series"] + "', " + str(len(d["keywords"])) + " keywords, " + str(len(d["categories"])) + " categories, description " + str(len(d["description"])) + " characters")
    return d


def booksFolder():
    """data\\books\\, kept across sessions; files from the earlier data\\books\\ are moved in once."""
    sNew, sOld = os.path.join(k.sProject, "data", "books"), os.path.join(k.sProject, "configs", "books")
    os.makedirs(sNew, exist_ok=True)
    if os.path.isdir(sOld):
        for sName in os.listdir(sOld):
            if sName.lower().endswith(".inix") and not os.path.exists(os.path.join(sNew, sName)):
                os.replace(os.path.join(sOld, sName), os.path.join(sNew, sName))
                log("Moved " + sName + " from configs\\books to data\\books")
    return sNew


def categoriesFromText(sText):
    """KDP lists the saved categories as 'Kindle Books › A › B ↗'; this returns them as 'Kindle eBooks > A > B' paths, the form the answers files use."""
    lPaths = [re.sub(r"\s*›\s*", " > ", "Kindle eBooks › " + c.strip()) for c in re.findall(r"Kindle Books\s*›\s*([^↗]+?)\s*↗", sText or "")]
    if not lPaths:
        for sPart in re.split(r"\s{2,}|\n", sText or ""):
            sPart = sPart.strip()
            if ">" in sPart and len(sPart) < 200 and sPart not in lPaths: lPaths.append(re.sub(r"\s*>\s*", " > ", sPart))
    return lPaths


def readPricing(page, sId):
    try:
        page.goto(k.c_sTitleSetup + sId + "/pricing", wait_until="domcontentloaded")
    except Exception as oError:
        log("Opening the Pricing page of " + sId + " was interrupted: " + str(oError).splitlines()[0][:160])
    for iTick in range(30):
        time.sleep(1)
        if sId in page.url and page.locator("input[name='data[digital][channels][amazon][US][price_vat_inclusive]']").count(): break
        if "bookshelf" in page.url and sId not in page.url: break
    if sId not in page.url:
        log("KDP did not open the Pricing page of " + sId)
        return {}
    time.sleep(1)
    d = page.evaluate("""() => {
        const v = (s) => { const l = Array.from(document.querySelectorAll(s)); const o = l.find(x => !x.disabled) || l[0]; return o ? (o.value || "") : ""; };
        const sel = document.querySelector("#data-is-select");
        const royalty = Array.from(document.querySelectorAll("input[name='data[digital][royalty_rate]-radio']")).find(x => x.checked);
        const lPrices = Array.from(document.querySelectorAll("input[name^='data[digital][channels][amazon]'][name*='price']")).map(o => [(o.name.match(/\\[amazon\\]\\[([A-Z]+)\\]/) || [,"?"])[1], o.value]);
        return {kdpSelect: sel ? (sel.checked ? "Yes" : "No") : "", royalty: royalty ? royalty.value : "", priceUsd: v("input[name='data[digital][channels][amazon][US][price_vat_inclusive]']"), prices: lPrices.map(p => p[0] + "=" + p[1]).join(", ")};
    }""")
    log("Pricing of " + sId + ": KDP Select " + d.get("kdpSelect", "") + ", royalty " + d.get("royalty", "") + ", US $" + d.get("priceUsd", "") + "; " + d.get("prices", ""))
    return d


def writeBook(r, dDetails, dPricing):
    """Writes data\\books\\<Title>.inix: [kdp] from the site, [proposed] kept from an existing file or left empty, [notes]."""
    sFolder = booksFolder()
    sPath = os.path.join(sFolder, fileStem(dDetails.get("title") or r["title"]) + ".inix")
    dOld = k.readInix(sPath) if os.path.exists(sPath) else {}
    dKdp = {"asin": r["asin"], "titleId": r["id"], "status": r["status"] + (" (updates in review)" if r.get("review") else ""), "readOn": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "title": dDetails.get("title", "").strip(), "subtitle": dDetails.get("subtitle", "").strip(), "edition": dDetails.get("edition", ""), "author": dDetails.get("author", ""), "series": dDetails.get("series", ""), "seriesText": dDetails.get("seriesText", ""), "language": dDetails.get("language", ""),
            "description": dDetails.get("description", ""), "publishingRights": dDetails.get("publishingRights", ""), "adultContent": dDetails.get("adultContent", ""), "readingAge": (dDetails.get("readingAgeStart", "") + "-" + dDetails.get("readingAgeEnd", "")).strip("-"),
            "primaryMarketplace": dDetails.get("primaryMarketplace", ""), "keywords": dDetails.get("keywords", []), "categories": dDetails.get("categories", []), "categoriesText": dDetails.get("categoriesText", ""),
            "kdpSelect": dPricing.get("kdpSelect", ""), "royalty": dPricing.get("royalty", ""), "priceUsd": dPricing.get("priceUsd", ""), "prices": dPricing.get("prices", "")}
    dSections = {"kdp": dKdp, "proposed": dOld.get("proposed", {"title": "", "subtitle": "", "series": "", "description": "", "keywords": "", "categories": "", "priceUsd": ""}),
                 "notes": dOld.get("notes", {"kdp": "What KDP held when kdpBooks last read it; rewritten on every run. Title, subtitle, author and edition are locked by KDP after publication and can be changed only through KDP support.",
                                              "proposed": "Revisions to apply. An empty value means keep what KDP holds. Description in the answers-file form: paragraphs apart, '- ' bullets, **bold**.",
                                              "format": "See help\\Inix.md. Block values start on the line after 'key =' and run to the next key line."})}
    k.writeInix(sPath, dSections)
    log("Wrote " + sPath)
    try:
        log("FILE " + os.path.basename(sPath) + " as written (the log carries a copy, since logs travel):\n" + open(sPath, encoding="utf-8-sig").read())
    except Exception as oError:
        log("The file could not be copied into the log: " + str(oError)[:100])
    return sPath


def sameText(sA, sB):
    """Two texts are the same when they agree after whitespace, quote and bullet-marker differences are ignored: KDP shows a list
    item as a bullet character, the answers file writes it as '- ', and the 16:42 run on 5 October resubmitted a book for that alone."""
    def f(sText):
        sText = re.sub(r"(?m)^\s*[\u2022\-\*]\s+", "- ", (sText or "").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"'))
        return re.sub(r"\s+", " ", sText).strip().lower()
    return f(sA) == f(sB)


def changesWanted(dFile):
    """Which of a file's [proposed] values KDP does not hold yet, as a list of words; empty when the book is already as the file wants."""
    dKdp, dProposed = dFile.get("kdp", {}), dFile.get("proposed", {})
    lWanted = []
    sDescription = dProposed.get("description", "").strip()
    if sDescription and not sameText(sDescription, dKdp.get("description", "")): lWanted.append("description")
    lKeywords = k.inixList(dProposed.get("keywords", ""))
    if lKeywords and [w.lower() for w in lKeywords] != [w.lower() for w in k.inixList(dKdp.get("keywords", ""))]: lWanted.append("keywords")
    lCategories = [k.c_dCategoryFixes.get(c, c) for c in k.inixList(dProposed.get("categories", ""))]
    lHeld = [k.c_dCategoryFixes.get(c, c) for c in k.inixList(dKdp.get("categories", ""))]
    if lCategories and sorted(c.lower() for c in lCategories) != sorted(c.lower() for c in lHeld): lWanted.append("categories")
    sPrice = dProposed.get("priceUsd", "").strip()
    if sPrice and ("%.2f" % float(sPrice)) != ("%.2f" % float(dKdp.get("priceUsd") or 0)): lWanted.append("price $" + sPrice)
    if not dKdp.get("adultContent", "").strip(): lWanted.append("Adult-only answer")
    return lWanted


def royaltyFor(sPrice, sCurrent):
    """The royalty plan for a US price: 70% only within KDP's band for it, $2.99 to $12.99, and 35% outside it, either way
    (8 October 2026, from an audit by another AI: 70% was chosen for any price of $2.99 or more, with no ceiling)."""
    try: fPrice = float(sPrice)
    except (TypeError, ValueError): return sCurrent
    if fPrice != fPrice or fPrice <= 0: return sCurrent
    return "70%" if 2.99 <= fPrice <= 12.99 else "35%"


def applyBook(page, sPath):
    """Sends one file's [proposed] values to KDP: description, keywords and categories on the Details tab (answering the Adult-only
    question with No first when KDP holds no answer), DRM No with its consent box on the Content tab, the price on the Pricing tab,
    then Publish, all through kdpSubmit's own routines. Returns kdpSubmit's outcome word: submitted, draft, blocked or unknown; or kept."""
    dFile = k.readInix(sPath)
    dKdp, dProposed = dFile.get("kdp", {}), dFile.get("proposed", {})
    sTitle = dKdp.get("title", "").strip() or os.path.basename(sPath)
    lLocked = [sField for sField in ("title", "subtitle") if dProposed.get(sField, "").strip() and dProposed[sField].strip() != dKdp.get(sField, "").strip()]
    lWanted = changesWanted(dFile)
    if not lWanted:
        say(sTitle + ": already as its file proposes; nothing to change" + ("; " + " and ".join(lLocked) + " differ but are locked by KDP, a request for KDP support" if lLocked else "") + ".")
        return "kept"
    sId = dKdp.get("titleId", "")
    if not sId:
        k.unresolved(sTitle, "no titleId in the file; the Bookshelf did not give one")
        return "blocked"
    lKeywords = k.inixList(dProposed.get("keywords", ""))
    lCategories = k.inixList(dProposed.get("categories", ""))
    if lCategories:
        lOffered, lDropped, lUnchecked = checkCategories(lCategories)
        for sPath in lDropped: say("Category not offered by KDP, per data\\kdpCategories.inix, so it is dropped: " + sPath.replace("Kindle eBooks > ", ""))
        if lUnchecked and (lOffered or lDropped): log("Categories under a top-level category not yet walked, left for the picker to judge: " + "; ".join(lUnchecked))
        lCategories = [sPath for sPath in lCategories if sPath not in lDropped]
    sDescription = dProposed.get("description", "").strip()
    sPrice = dProposed.get("priceUsd", "").strip()
    say("Applying to " + sTitle + ": " + ", ".join(lWanted) + "; DRM No with consent." + (" " + " and ".join(lLocked).capitalize() + " differ but are locked by KDP; left as they are." if lLocked else ""))
    k.lUnresolved.clear()
    k.sBookStatus = "Live"
    k.dAnswers = {"title": dKdp.get("title", ""), "subtitle": dKdp.get("subtitle", ""), "author": dKdp.get("author", ""), "language": dKdp.get("language", "English"), "editionNumber": dKdp.get("edition", ""),
                  "description": sDescription or dKdp.get("description", ""), "keywords": lKeywords or k.inixList(dKdp.get("keywords", "")), "categories": lCategories or k.inixList(dKdp.get("categories", "")),
                  "drm": "No", "kdpSelect": dKdp.get("kdpSelect", "No"), "royalty": royaltyFor(sPrice, dKdp.get("royalty", "")), "priceUsd": sPrice or dKdp.get("priceUsd", ""), "territories": "All"}
    try:
        page.goto(k.c_sTitleSetup + sId + "/details", wait_until="domcontentloaded")
    except Exception as oError:
        log("Opening the Details page was interrupted: " + str(oError).splitlines()[0][:160])
    for iTick in range(30):
        time.sleep(1)
        if sId in page.url and page.locator("#data-title").count(): break
    if sId not in page.url or not page.locator("#data-title").count():
        k.unresolved(sTitle, "KDP would not open the Details page (URL " + page.url + "); an update in review locks it")
        return "blocked"
    time.sleep(2)
    if "description" in lWanted:
        say("Description.")
        k.fillDescription(page)
    if "keywords" in lWanted:
        say(str(len(lKeywords)) + " keywords.")
        lBoxes = (lKeywords + [""] * 7)[:7]
        for iIndex, sKeyword in enumerate(lBoxes): k.fillText(page, "Keyword " + str(iIndex + 1), ["#data-keywords-" + str(iIndex)], sKeyword)
    if "Adult-only answer" in lWanted:
        say("Adult-only question: No.")
        k.clickRadio(page, "Adult content: No", ["input[name='data[is_adult_content]-radio'][value=false]"])
        time.sleep(2)
    if "categories" in lWanted or "Adult-only answer" in lWanted:
        say("Categories; this takes about a minute.")
        k.closeNotice(page)
        k.chooseCategories(page)
    k.logMessages(page, "details changed")
    if not k.saveDraft(page): return "blocked"
    if not k.saveAndContinue(page, "content"): return "blocked"
    time.sleep(2)
    say("DRM: No, with the consent box, so the book can be bought as a DRM-free EPUB.")
    k.setDrm(page, True)
    if "/content" in page.url: k.confirmAnswers(page)
    k.logMessages(page, "after DRM")
    if not k.saveAndContinue(page, "pricing"):
        oRefusal = re.compile(r"Consent is required|check the box|confirm your answers", re.I)
        if not any(oRefusal.search(sItem) for sItem in k.lUnresolved): return "blocked"
        say("KDP still asks for a box on the Content tab; looking once more.")
        k.dumpControls(page, "content tab after the refusal")
        k.lUnresolved[:] = [sItem for sItem in k.lUnresolved if not oRefusal.search(sItem)]
        k.setDrm(page, True)
        k.confirmAnswers(page)
        if not k.saveAndContinue(page, "pricing"): return "blocked"
    if sPrice:
        say("Price $" + sPrice + " at " + k.dAnswers["royalty"] + ".")
        if k.dAnswers["royalty"] == "70%": k.clickRadio(page, "Royalty 70 percent", ["input[name='data[digital][royalty_rate]-radio'][value='70_PERCENT']"])
        elif k.dAnswers["royalty"] == "35%": k.clickRadio(page, "Royalty 35 percent", ["input[name='data[digital][royalty_rate]-radio'][value='35_PERCENT']"])
        k.fillText(page, "US list price", ["input[name='data[digital][channels][amazon][US][price_vat_inclusive]']"], "%.2f" % float(sPrice))
        time.sleep(2)
        k.logMessages(page, "after the price")
    sOutcome = k.finalReview(page)
    log("APPLY OUTCOME for " + sTitle + ": " + sOutcome + ("; unresolved: " + " | ".join(k.lUnresolved) if k.lUnresolved else ""))
    dFile.setdefault("review", {})["applied"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + " " + sOutcome + ("; " + "; ".join(k.lUnresolved) if k.lUnresolved else "")
    if k.dAnswers.get("categoriesChosen"): dFile["review"]["categoriesChosen"] = k.dAnswers["categoriesChosen"]
    k.writeInix(sPath, dFile)
    return sOutcome


class PickerLost(Exception):
    """Raised when the picker's menus are gone, usually because the Details page reloaded under the walk."""


def openPicker(page, sId):
    """Opens one book's Details page and its category picker; returns True when the picker's menus can be reached."""
    try:
        page.goto(k.c_sTitleSetup + sId + "/details", wait_until="domcontentloaded")
    except Exception as oError:
        log("Opening the Details page was interrupted: " + str(oError).splitlines()[0][:160])
    for iTick in range(30):
        time.sleep(1)
        if page.locator("#data-title").count(): break
    time.sleep(2)
    k.closeNotice(page)
    if not k.clickButton(page, "Choose categories", ["Edit categories", "Choose categories"], False):
        say("The category picker would not open (the Adult-only question may be unanswered on this book).")
        return False
    time.sleep(2)
    return True


def walkCategories(page, sId):
    """Opens one book's category picker and walks every menu, depth first, recording the sub-menus and the placement boxes at each
    level, then presses Cancel so nothing is saved. Writes data\\kdpCategories.inix (sections [menus] and [placements], one line per
    path) and data\\kdpCategories.md (an indented list). KDP offers no list of its Kindle store categories; this makes one, so that
    the paths proposed for a book are ones the picker offers and the General placement is chosen only when it is the right one.
    The files are written after every top-level category, and a later run skips the top-level categories already walked, so an
    interrupted walk resumes where it stopped; if the page reloads under the walk, the picker is reopened and the path replayed."""
    if not openPicker(page, sId): return False
    return walkPicker(page, sId)


def categoriesFiles():
    sFolder = os.path.join(k.sProject, "data")
    os.makedirs(sFolder, exist_ok=True)
    return os.path.join(sFolder, "kdpCategories.inix"), os.path.join(sFolder, "kdpCategories.md")


def writeCategories(dMenus, dPlacements, lDone):
    """Writes the two category files from what has been walked so far."""
    sInix, sMd = categoriesFiles()
    sCount = str(len([x for x in set(dMenus) | set(dPlacements) if dMenus.get(x) or dPlacements.get(x)])) + " menus, " + str(sum(len(l) for l in dPlacements.values())) + " placements"
    def lines(d): return "\n".join(sPath + " :: " + "; ".join(l) for sPath, l in d.items() if l)
    dOut = {"menus": {"list": lines(dMenus)}, "placements": {"list": lines(dPlacements)},
            "notes": {"readOn": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "done": "; ".join(lDone),
                      "menus": "One line per menu path below Kindle eBooks: the path, then two colons, then the sub-menus it opens, separated by semicolons (category names can hold commas).",
                      "placements": "One line per menu path: the path, two colons, then the placement boxes offered there, separated by semicolons. A category is a path plus one placement, or a path whose last step is itself a placement.",
                      "done.note": "The top-level categories walked to the end; a later --categories run skips them and walks the rest. Delete this file to walk everything afresh.",
                      "count": sCount}}
    k.writeInix(sInix, dOut)
    lLines = ["# KDP Kindle eBook Categories", "", "Read from KDP's category picker on " + dOut["notes"]["readOn"] + ": " + sCount + ". A line ending in (placement) can be ticked; the other lines are menus." + ("" if len(lDone) == len(dMenus.get("Kindle eBooks", [])) else " The walk is not yet complete; " + str(len(lDone)) + " of " + str(len(dMenus.get("Kindle eBooks", []))) + " top-level categories are done."), ""]
    def emit(sPath, iDepth):
        for sBox in dPlacements.get(sPath, []): lLines.append("  " * iDepth + "- " + sBox + " (placement)")
        for sMenu in dMenus.get(sPath, []):
            lLines.append("  " * iDepth + "- " + sMenu)
            emit(sPath + " > " + sMenu, iDepth + 1)
    emit("Kindle eBooks", 0)
    open(sMd, "w", encoding="utf-8-sig", newline="\r\n").write("\n".join(lLines) + "\n")
    return sCount


def loadCategories():
    """Reads data\\kdpCategories.inix into (dMenus, dPlacements, lDone); empty when the walk has not been run."""
    sInix, sMd = categoriesFiles()
    if not os.path.exists(sInix): return {}, {}, []
    dOld = k.readInix(sInix)
    def parse(sBlock):
        d = {}
        for sLine in sBlock.split("\n"):
            if " :: " not in sLine: continue
            sPath, sItems = sLine.split(" :: ", 1)
            d[sPath.strip()] = [x.strip() for x in sItems.split(";") if x.strip()]
        return d
    return parse(dOld.get("menus", {}).get("list", "")), parse(dOld.get("placements", {}).get("list", "")), [x.strip() for x in dOld.get("notes", {}).get("done", "").split(";") if x.strip()]


def checkCategories(lPaths):
    """Splits proposed category paths into (lOffered, lDropped, lUnchecked) against the walked list: a path is offered when its menus
    and its last step are in the list; dropped when its top-level category was walked to the end and the path is not there; unchecked
    when that top-level category has not been walked yet, so the picker itself decides."""
    dMenus, dPlacements, lDone = loadCategories()
    lOffered, lDropped, lUnchecked = [], [], []
    for sPath in lPaths:
        lSteps = [x.strip() for x in sPath.split(">") if x.strip()]
        if lSteps and lSteps[0].lower() == "kindle ebooks": lSteps = lSteps[1:]
        if not lSteps or not lDone or lSteps[0] not in lDone:
            lUnchecked.append(sPath)
            continue
        bOk = True
        for iStep in range(len(lSteps)):
            sParent = " > ".join(["Kindle eBooks"] + lSteps[:iStep])
            sStep = lSteps[iStep]
            bLast = iStep == len(lSteps) - 1
            if sStep in dMenus.get(sParent, []): continue
            if bLast and (sStep in dPlacements.get(sParent, []) or sStep == "General"): continue
            bOk = False
            break
        (lOffered if bOk else lDropped).append(sPath)
    return lOffered, lDropped, lUnchecked


def walkPicker(page, sId=""):
    """The walk itself, with the picker already open; kept apart so the mock picker can exercise it."""
    dMenus, dPlacements, lDone = loadCategories()
    if lDone: say(str(len(lDone)) + " top-level categor" + ("y was" if len(lDone) == 1 else "ies were") + " walked on an earlier run and will be skipped: " + ", ".join(lDone))
    oSelects = page.locator("select[name^=react-aui]")
    dState = {"top": [], "topBoxes": []}

    def optionsOf(iIndex):
        return [t.strip() for t in oSelects.nth(iIndex).locator("option").all_inner_texts() if t.strip() and t.strip().lower() != "select one"]

    def selectedText(iIndex):
        try:
            return (oSelects.nth(iIndex).evaluate("o => o.selectedIndex >= 0 ? o.options[o.selectedIndex].text : ''", timeout=5000) or "").strip()
        except Exception:
            return ""

    def topIndex():
        """The index of the chain's top menu: the last select whose options are the top-level list. KDP adds and removes menus
        as the chain changes, so this is found afresh at every step rather than remembered."""
        iCount = oSelects.count()
        for iIndex in range(iCount - 1, -1, -1):
            try:
                if optionsOf(iIndex) == dState["top"]: return iIndex
            except Exception:
                continue
        return -1

    def menuIndex(iDepth):
        iTop = topIndex()
        if iTop < 0: raise PickerLost("the top menu is not on the page")
        iIndex = iTop + iDepth
        return iIndex if iIndex < oSelects.count() else -1

    def resetChain():
        k.clearCategories(page, page, bRemoveSaved=False)
        if not oSelects.count():
            k.clickButton(page, "Add another category (no menus yet)", ["Add another category"], False)
            time.sleep(2)
        if not oSelects.count(): return False
        if not dState["top"]:
            lBest = []
            for iIndex in range(oSelects.count()):
                lOptions = optionsOf(iIndex)
                if "Arts & Photography" in lOptions and len(lOptions) > len(lBest): lBest = lOptions  # KDP's top-level list
            dState["top"] = lBest or optionsOf(oSelects.count() - 1)  # or the newest menu, as on a mock picker
        dState["topBoxes"] = [n for n in k.boxNames(page) if n]  # boxes showing before any pick belong to saved chains or the page, not to a level
        return bool(dState["top"]) and topIndex() >= 0

    def options(iDepth):
        iIndex = menuIndex(iDepth)
        return optionsOf(iIndex) if iIndex >= 0 else []

    def pick(iDepth, sOption):
        iIndex = menuIndex(iDepth)
        if iIndex < 0: raise PickerLost("menu at depth " + str(iDepth) + " is not on the page")
        iBefore, lBefore = oSelects.count(), k.boxNames(page)
        lNextBefore = optionsOf(iIndex + 1) if iIndex + 1 < iBefore else []
        try:
            oSelects.nth(iIndex).select_option(label=sOption, force=True, timeout=5000)
        except Exception as oError:
            log("select_option failed at depth " + str(iDepth) + " for " + sOption + ": " + str(oError).splitlines()[0][:100])
        if selectedText(iIndex) != sOption:
            try:
                oSelects.nth(iIndex).evaluate("(o, s) => { for (const opt of o.options) if (opt.text.trim() === s) { o.value = opt.value; o.dispatchEvent(new Event('change', {bubbles: true})); } }", sOption, timeout=5000)
            except Exception as oError:
                raise PickerLost(str(oError).splitlines()[0][:120])
        for iTick in range(16):  # up to 8 seconds for KDP to draw the level below
            time.sleep(0.5)
            iTopNow = topIndex()
            if iTopNow < 0: continue
            iNow = iTopNow + iDepth
            if iNow >= oSelects.count(): continue
            if selectedText(iNow) != sOption: continue
            lNextNow = optionsOf(iNow + 1) if iNow + 1 < oSelects.count() else []
            if lNextNow and lNextNow != lNextBefore: break
            if oSelects.count() != iBefore or k.boxNames(page) != lBefore: break
        time.sleep(0.5)
        iNow = menuIndex(iDepth)
        if iNow < 0 or selectedText(iNow) != sOption: raise PickerLost("the menu did not take " + sOption)

    def reopen(lPath):
        """The page reloaded or the picker closed: open it again and replay the path so the walk can go on."""
        say("The picker closed, usually because the page reloaded; reopening it and returning to " + " > ".join(lPath) + ". Please leave the window alone during the walk.")
        if sId and not openPicker(page, sId): raise PickerLost("the picker would not reopen")
        if not resetChain(): raise PickerLost("no menus after reopening")
        for iDepth, sStep in enumerate(lPath[1:]): pick(iDepth, sStep)

    def level(lPath, iDepth):
        """Reads the sub-menus and placements at the current level and records them."""
        sPath = " > ".join(lPath)
        lNext = options(iDepth + 1)
        if lNext == dState["top"]: raise PickerLost("the menu below " + sPath + " shows the top-level list")
        lAll = [n for n in k.boxNames(page) if n and not re.search(r"answers are accurate", n, re.I)]
        lBoxes = [n for n in lAll if n not in dState["topBoxes"]]  # KDP shows only the current level's boxes
        dMenus[sPath], dPlacements[sPath] = lNext, lBoxes
        log("MENU " + sPath + " -- sub-menus: " + "; ".join(lNext) + " -- placements: " + "; ".join(lBoxes))
        return lNext

    def walk(lPath, iDepth):
        lNext = level(lPath, iDepth)
        for sOption in lNext:
            for iTry in range(2):
                try:
                    pick(iDepth + 1, sOption)
                    walk(lPath + [sOption], iDepth + 1)
                    break
                except PickerLost as oError:
                    log("Picker lost at " + " > ".join(lPath + [sOption]) + ": " + str(oError))
                    if iTry: say("Skipping " + " > ".join(lPath + [sOption]) + " after two tries; see the log.")
                    else: reopen(lPath)
        return True

    if not resetChain():
        say("No picker menus appeared.")
        return False
    say("Walking KDP's category menus. This takes half an hour or more; each top-level category is announced as it is reached, the files in data\\ are rewritten after each one, and a stopped walk resumes on the next run. Please leave the Edge window alone.")
    lTop = list(dState["top"])
    dMenus["Kindle eBooks"], dPlacements["Kindle eBooks"] = lTop, []
    sPrevious = ""
    for sTop in lTop:
        if sTop in lDone: continue
        say("  " + sTop)
        dtStart = datetime.datetime.now()
        bDone = False
        for iTry in range(2):
            try:
                pick(0, sTop)
                walk(["Kindle eBooks", sTop], 0)
                sKey = "Kindle eBooks > " + sTop
                if not dMenus.get(sKey) and not dPlacements.get(sKey): raise PickerLost("nothing read under " + sTop)
                if sPrevious and dMenus.get(sKey) and dMenus.get(sKey) == dMenus.get("Kindle eBooks > " + sPrevious): raise PickerLost(sTop + " read the same sub-menus as " + sPrevious)
                bDone = True
                break
            except PickerLost as oError:
                log("Picker lost at " + sTop + ": " + str(oError))
                if iTry: say("Skipping " + sTop + " after two tries; it will be tried again on the next run. See the log.")
                else: reopen(["Kindle eBooks"])
        if bDone:
            lDone.append(sTop)
            sPrevious = sTop
        else:
            for sKey in [x for x in list(dMenus) + list(dPlacements) if x == "Kindle eBooks > " + sTop or x.startswith("Kindle eBooks > " + sTop + " > ")]:
                dMenus.pop(sKey, None); dPlacements.pop(sKey, None)
        sCount = writeCategories(dMenus, dPlacements, lDone)
        log(("Done " if bDone else "Not done ") + sTop + " in " + str(int((datetime.datetime.now() - dtStart).total_seconds())) + " s; " + sCount + " so far; " + str(len(lDone)) + " of " + str(len(lTop)) + " top-level categories written to data\\kdpCategories.inix")
    k.clickButton(page, "Cancel the category picker", ["Cancel"], False)
    sCount = writeCategories(dMenus, dPlacements, lDone)
    lLeft = [x for x in lTop if x not in lDone]
    say("Wrote data\\kdpCategories.inix and data\\kdpCategories.md: " + sCount + ". Nothing on KDP was changed." + (" Not yet walked: " + ", ".join(lLeft) + "; run --categories again for them." if lLeft else " Every top-level category is done."))
    return True


def main():
    sys.argv = [("-" + a) if re.match(r"^-[a-z]", a) else a for a in sys.argv]  # -export means --export; the 14:12 run typed one dash and was misread
    if any(a.startswith("--") and a not in c_lFlags for a in sys.argv[1:]):
        print("Unknown option. Allowed: " + " ".join(c_lFlags) + ". Nothing was done.")
        return 2
    os.makedirs(os.path.join(k.sProject, "logs"), exist_ok=True)
    sStem = os.path.basename(k.sProject)  # the project's own name: one copy of the kit's tools serves every project
    k.sLogPath = os.path.join(k.sProject, "logs", sStem + "-kdpBooks-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".log")
    log("kdpBooks.py started; " + c_sVersion + "; script " + os.path.abspath(__file__))
    log("Python " + sys.version.split()[0] + " on " + platform.platform() + "; project " + k.sProject + "; command line " + " ".join(sys.argv))
    print("kdpBooks " + c_sVersion.split(":")[0])
    sOnly = k.argValue("--asin").upper()
    bExport = "--export" in sys.argv
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        say("Playwright is missing. Run scripts\\kdpSubmit.cmd once to install it, then run this again.")
        return 2
    sProfile = os.path.join(os.environ.get("LOCALAPPDATA", k.sFolder), "KdpSubmit", "edgeProfile")
    k.closeLeftovers(sProfile)
    os.makedirs(sProfile, exist_ok=True)
    lFailed, lResults = [], []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(sProfile, channel="msedge", headless=False, args=["--start-maximized"], viewport=None, ignore_default_args=["--enable-automation"])
            page = browser.pages[0] if browser.pages else browser.new_page()
            page.set_default_timeout(20000)
            k.watchBrowser(page)
            say("Opening the KDP Bookshelf in Edge. " + ("Nothing on KDP is changed by this run." if bExport else "Each book is read, then changed and published where its file in data\\books\\ proposes something new" + (", stopping at the saved draft instead of Publish" if "--no-publish" in sys.argv else "") + "."))
            lRows = bookshelfRows(page)
            if lRows is None: return 3
            lBooks = [r for r in lRows if r["asin"] and (not sOnly or r["asin"] == sOnly)]
            say(str(len(lBooks)) + " published book" + ("" if len(lBooks) == 1 else "s") + " with an ASIN" + (" matching " + sOnly if sOnly else "") + ".")
            if "--dry-run" in sys.argv:
                for r in lBooks: say("  " + r["asin"] + " " + r["title"])
                browser.close()
                return 0
            if "--categories" in sys.argv:
                lWithId = [r for r in lBooks if r["id"]]
                bOk = walkCategories(page, lWithId[0]["id"]) if lWithId else False
                browser.close()
                return 0 if bOk else 5
            for iIndex, r in enumerate(lBooks):
                say("Reading " + str(iIndex + 1) + " of " + str(len(lBooks)) + ": " + r["title"][:70])
                if not r["id"]: r["id"] = titleIdByClicking(page, r)
                if not r["id"]:
                    lFailed.append(r["asin"] + " " + r["title"] + ": its title-setup id could not be found")
                    continue
                dDetails = readDetails(page, r["id"])
                if dDetails is None:
                    lFailed.append(r["asin"] + " " + r["title"] + ": KDP would not open its Details page" + (" (update in review)" if r.get("review") or r["status"] == "In Review" else ""))
                    continue
                dPricing = readPricing(page, r["id"])
                sPath = writeBook(r, dDetails, dPricing)
                if bExport: continue
                sOutcome = applyBook(page, sPath)
                lResults.append((r["title"].strip(), sOutcome))
                if sOutcome in ("blocked", "unknown"): lFailed.append(r["asin"] + " " + r["title"] + ": " + sOutcome + ("; " + "; ".join(k.lUnresolved) if k.lUnresolved else ""))
            browser.close()
    except Exception as oError:
        import traceback
        log("CRASH: " + traceback.format_exc())
        say("The script hit an error: " + str(oError).splitlines()[0][:200] + ". The details are in the log.")
        return 4
    if lResults:
        say("Outcome by book:")
        for sTitle, sOutcome in lResults: say("  " + sTitle[:60] + ": " + sOutcome)
    if lFailed:
        say(str(len(lFailed)) + " book" + ("" if len(lFailed) == 1 else "s") + " could not be " + ("read" if bExport else "read or applied") + ":")
        for s in lFailed: say("  " + s[:300])
    say("Done. The files are in data\\books\\. Log: " + k.sLogPath)
    return 5 if lFailed else 0


if __name__ == "__main__":
    sys.exit(main())
