"""kdpFetch.py -- fetches what a book in the project is missing: its cover from its Amazon page, and the pictures its
manuscript names by web address, through the same remembered Edge window the other KDP tools use.

WHY A BROWSER. Legacy of Mazrui's pictures were refused when buildBooks downloaded them as a script: the sites sent web
pages instead. A real browser, signed in and with its cookies, is refused far less often. Nothing on KDP or Amazon is
changed by this script; it only reads and downloads.

WHAT IT FETCHES
  Covers: a book with no cover file (books\\<root>\\<root>.jpg, .jpeg or .png) gets the full-size cover from its Amazon
  page, found by the ASIN in configs\\books.inix -- the cover KDP published from the author's upload.
  Pictures: each picture the manuscript names by web address that is missing from books\\<root>\\images, is not a
  picture, or is YouTube's 120-by-90 "no thumbnail" placeholder. It is saved under the name buildBooks looks for. For a
  YouTube thumbnail the sizes are tried largest first, since the size a manuscript names does not exist for every video.
  Metadata: kdpBooks --export already reads every book's details and pricing; -metadata runs it.
  Manuscripts: KDP's Content tab offers no download of a published book's manuscript; -manuscripts says so and where the
  manuscript lives instead.

A file already in place is never replaced; a file in the way that is not a picture is moved to notes\\not-pictures.

USAGE
  scripts\\kdpFetch                 covers and pictures, for every book that lacks them
  scripts\\kdpFetch -book <root>    one book
  scripts\\kdpFetch -covers         covers only
  scripts\\kdpFetch -pictures       pictures only
  scripts\\kdpFetch -metadata       runs kdpBooks -export
  scripts\\kdpFetch -manuscripts    explains where manuscripts come from
  scripts\\kdpFetch -dry-run        lists what is missing and where it would come from; opens no browser

Every run writes logs\\<Project>-kdpFetch-<date>-<time>.log. Exit codes: 0 done (or nothing missing); 2 bad option;
3 no browser; 4 crash; 5 something could not be fetched, listed at the end.
"""

import datetime, json, os, platform, re, shutil, subprocess, sys, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import buildBooks as b
import kdpSubmit as k

sVersion = "2026-10-13 version 1: covers from Amazon pages and manuscript pictures through the remembered Edge window"
lFlags = ["book", "covers", "dry-run", "manuscripts", "metadata", "pictures"]
lYouTubeSizes = ["maxresdefault", "sddefault", "hqdefault", "mqdefault", "0"]
iPlaceholderBytes = 2000   # YouTube's grey placeholder is about 1,100 bytes; a real thumbnail is many times larger


def log(sText): return k.log(sText)


def say(sText): return k.say(sText)


def options(lArgs):
    """({option: value}, problem): switches take one or two dashes or a slash, in any case; -book takes the next word."""
    dOptions, i = {}, 0
    while i < len(lArgs):
        sName = lArgs[i].lstrip("-/").lower()
        if sName not in lFlags: return {}, "Unknown option " + lArgs[i] + ". Allowed: " + ", ".join("-" + s for s in lFlags) + "."
        if sName == "book":
            if i + 1 >= len(lArgs): return {}, "-book needs a book's root name after it."
            dOptions["book"], i = lArgs[i + 1], i + 2
            continue
        dOptions[sName], i = True, i + 1
    return dOptions, ""


def coverPath(sRoot):
    """The book's cover file, or "" when it has none."""
    for sExtension in b.lCoverExtensions:
        sPath = os.path.join(k.sProject, "books", sRoot, sRoot + sExtension)
        if os.path.isfile(sPath) and b.isPicture(sPath): return sPath
    return ""


def isYouTube(sUrl): return bool(re.search(r"(^|\.)ytimg\.com/", urllib.parse.urlsplit(sUrl).netloc + "/"))


def isPlaceholder(sPath, sUrl):
    """True for YouTube's grey "no thumbnail" image: a YouTube address whose file is tiny."""
    return isYouTube(sUrl) and os.path.isfile(sPath) and os.path.getsize(sPath) < iPlaceholderBytes


def manuscriptPictures(sRoot):
    """[(picture's file path, address, text alternative, why it is needed)] for the web pictures this book lacks."""
    sManuscript = os.path.join(k.sProject, "books", sRoot, sRoot + ".md")
    if not os.path.isfile(sManuscript): return []
    with open(sManuscript, encoding="utf-8-sig") as f: sBody = f.read()
    sBookDir = os.path.dirname(sManuscript)
    sFoundFile = os.path.join(sBookDir, "found.inix")
    dFound = b.readInix(sFoundFile).get("found", {}) if os.path.isfile(sFoundFile) else {}
    lFolders = [os.path.join(sBookDir, "images")] + b.inixList(dFound.get("imageFolders", ""))
    lNeeded, dSeen = [], set()
    for dPicture in b.imageList(sBody):
        sUrl = dPicture["url"]
        if not re.match(r"^https?://", sUrl, re.I) or sUrl in dSeen: continue
        dSeen.add(sUrl)
        # WHERE buildBooks LOOKS, NOT JUST THE IMAGES FOLDER: a picture shared by two books is kept once, and the build
        # finds it through the folders its found.inix names. A picture the build finds is not fetched again.
        sName = b.cacheName(sUrl)
        sFound = b.findInFolders(lFolders, sName)
        sPath = os.path.join(sBookDir, "images", sName)
        if not sFound: sWhy = "missing"
        elif not b.isPicture(sFound): sWhy, sPath = "not a picture", sFound
        elif isPlaceholder(sFound, sUrl): sWhy, sPath = "YouTube's placeholder", sFound
        else: continue
        lNeeded.append((sPath, sUrl, dPicture["alt"], sWhy))
    return lNeeded


def youTubeAddresses(sUrl):
    """The thumbnail addresses to try for a YouTube picture, largest first."""
    oMatch = re.search(r"/vi(?:_webp)?/([^/]+)/", sUrl)
    if not oMatch: return [sUrl]
    return ["https://i.ytimg.com/vi/" + oMatch.group(1) + "/" + s + ".jpg" for s in lYouTubeSizes]


def download(page, sUrl):
    """The picture's bytes at this address, fetched with the browser's own cookies and identity, or None."""
    for sHow in ("request", "page"):
        try:
            if sHow == "request":
                oResponse = page.context.request.get(sUrl, timeout=30000)
                binData = oResponse.body() if oResponse.ok else b""
                log("  GET " + sUrl[:200] + ": status " + str(oResponse.status) + ", " + str(len(binData)) + " bytes")
            else:
                oResponse = page.goto(sUrl, wait_until="load", timeout=30000)
                binData = oResponse.body() if oResponse and oResponse.ok else b""
                log("  opened " + sUrl[:200] + " in the browser: status " + (str(oResponse.status) if oResponse else "none") + ", " + str(len(binData)) + " bytes")
        except Exception as oError:
            log("  " + sHow + " " + sUrl[:200] + " failed: " + str(oError).splitlines()[0][:200])
            continue
        if binData and pictureBytes(binData): return binData
        if binData: log("    what came back is not a picture: " + binData[:80].decode("utf-8", "replace").replace("\n", " "))
    return None


def pictureBytes(binData):
    """True when the bytes are a picture, by the same rule as buildBooks' isPicture."""
    binHead = binData[:512]
    if binHead.startswith(b"\xff\xd8\xff") or binHead.startswith(b"\x89PNG") or binHead[:4] == b"GIF8" or binHead.startswith(b"BM"): return True
    if binHead[:4] == b"RIFF" and binHead[8:12] == b"WEBP": return True
    return b"<svg" in binHead.lower()


def extensionOf(binData):
    if binData.startswith(b"\x89PNG"): return ".png"
    return ".jpg"


def setAside(sRoot, sPath):
    """Moves a file that is in the way and not a picture to notes\\not-pictures\\<root>."""
    sAside = os.path.join(k.sProject, "notes", "not-pictures", sRoot, os.path.basename(sPath))
    os.makedirs(os.path.dirname(sAside), exist_ok=True)
    if os.path.exists(sAside): os.remove(sAside)
    shutil.move(sPath, sAside)
    log("  set aside " + sPath + " -> " + sAside)
    return sAside


def save(sPath, binData):
    os.makedirs(os.path.dirname(sPath), exist_ok=True)
    with open(sPath, "wb") as f: f.write(binData)
    if not b.isPicture(sPath): raise RuntimeError("the picture saved at " + sPath + " does not read back as a picture")
    log("  saved " + sPath + ", " + str(len(binData)) + " bytes")
    return True


def amazonCoverAddresses(page, sAsin):
    """The cover's addresses on the book's Amazon page, the full-size original first."""
    sPage = "https://www.amazon.com/dp/" + sAsin
    page.goto(sPage, wait_until="domcontentloaded", timeout=45000)
    log("  opened " + sPage + ": title " + page.title()[:120])
    lAddresses = []
    for sSelector in ["#ebooksImgBlkFront", "#imgBlkFront", "#landingImage", "#main-image"]:
        oElement = page.query_selector(sSelector)
        if not oElement: continue
        sDynamic = oElement.get_attribute("data-a-dynamic-image") or ""
        try:
            dSizes = json.loads(sDynamic) if sDynamic else {}
        except ValueError:
            dSizes = {}
        lBySize = sorted(dSizes.items(), key=lambda o: -(o[1][0] * o[1][1]) if isinstance(o[1], list) and len(o[1]) == 2 else 0)
        lAddresses += [s for s, _ in lBySize]
        for sAttribute in ("data-old-hires", "src"):
            sValue = oElement.get_attribute(sAttribute) or ""
            if sValue.startswith("http"): lAddresses.append(sValue)
        log("  cover element " + sSelector + ": " + str(len(dSizes)) + " sizes offered")
        break
    # Amazon names each size by a code before the extension (._SY342_); without the code it serves the original.
    lOriginals = [re.sub(r"\._[^./]+_(?=\.(?:jpg|jpeg|png)$)", "", s) for s in lAddresses]
    return list(dict.fromkeys([s for s in lOriginals + lAddresses if s]))


def fetchCover(page, dBook):
    sRoot, sAsin = dBook["root"], dBook.get("asin", "")
    if not sAsin: return "it has no ASIN in configs\\books.inix"
    lAddresses = amazonCoverAddresses(page, sAsin)
    if not lAddresses: return "its Amazon page showed no cover (the page's title is in the log)"
    for sUrl in lAddresses:
        binData = download(page, sUrl)
        if binData:
            sPath = os.path.join(k.sProject, "books", sRoot, sRoot + extensionOf(binData))
            save(sPath, binData)
            say("  " + sRoot + ": cover saved, " + "{:,}".format(len(binData)) + " bytes, from its Amazon page.")
            return ""
    return "none of the " + str(len(lAddresses)) + " cover addresses on its Amazon page gave a picture"


def fetchPicture(page, sRoot, sPath, sUrl, sAlt, sWhy):
    lAddresses = youTubeAddresses(sUrl) if isYouTube(sUrl) else [sUrl]
    for sTry in lAddresses:
        binData = download(page, sTry)
        if binData and isYouTube(sTry) and len(binData) < iPlaceholderBytes:
            log("    " + sTry + " is YouTube's placeholder; trying the next size")
            continue
        if binData:
            if os.path.exists(sPath): setAside(sRoot, sPath)
            save(sPath, binData)
            say("  " + sRoot + ": " + (sAlt or os.path.basename(sPath))[:60] + " saved (was " + sWhy + ").")
            return ""
    return (sAlt or os.path.basename(sPath))[:60] + ": the site gave no picture (" + sUrl[:90] + ")"


def main():
    dOptions, sProblem = options(sys.argv[1:])
    if sProblem:
        print(sProblem + " Nothing was done.")
        return 2
    os.makedirs(os.path.join(k.sProject, "logs"), exist_ok=True)
    k.sLogPath = os.path.join(k.sProject, "logs", os.path.basename(k.sProject) + "-kdpFetch-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".log")
    b.sProject, b.sLogPath = k.sProject, k.sLogPath
    log("kdpFetch.py started; " + sVersion + "; script " + os.path.abspath(__file__))
    log("Python " + sys.version.split()[0] + " on " + platform.platform() + "; project " + k.sProject + "; working folder " + os.getcwd() + "; command line " + " ".join(sys.argv))
    log("options: " + json.dumps(dOptions))
    print("kdpFetch " + sVersion.split(":")[0])
    if dOptions.get("manuscripts"):
        say("KDP's Content tab offers no download of a published book's manuscript, so there is none to fetch. Each book's")
        say("manuscript is its Markdown file, books\\<root>\\<root>.md, from which buildBooks makes the EPUB; earlier Word")
        say("manuscripts were kept in notes\\word when the Markdown became the only source.")
        if len(dOptions) == 1: return 0
    if dOptions.get("metadata"):
        say("Metadata: running kdpBooks -export, which reads every book's details and pricing from KDP and changes nothing.")
        oRun = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "kdpBooks.py"), "--export"])
        log("kdpBooks --export exit code " + str(oRun.returncode))
        if not (dOptions.get("covers") or dOptions.get("pictures") or dOptions.get("book")): return oRun.returncode
    sKitProblem = b.loadKit()
    if sKitProblem:
        say(sKitProblem)
        return 2
    dCatalog = b.loadCatalog()
    if dOptions.get("book") and dOptions["book"] not in dCatalog:
        say("No book named " + dOptions["book"] + " in configs\\books.inix. Nothing was done.")
        return 2
    bCovers = dOptions.get("covers") or not dOptions.get("pictures")
    bPictures = dOptions.get("pictures") or not dOptions.get("covers")
    lBooks = [dCatalog[dOptions["book"]]] if dOptions.get("book") else [dCatalog[s] for s in sorted(dCatalog, key=str.lower)]
    lCovers = [d for d in lBooks if bCovers and os.path.isdir(os.path.join(k.sProject, "books", d["root"])) and not coverPath(d["root"])]
    lPictures = [(d["root"], o) for d in lBooks if bPictures for o in manuscriptPictures(d["root"])]
    for d in lCovers: log("needs a cover: " + d["root"] + ", ASIN " + (d.get("asin") or "none"))
    for sRoot, o in lPictures: log("needs a picture: " + sRoot + ", " + o[0] + " (" + o[3] + ") from " + o[1])
    if not lCovers and not lPictures:
        say("Nothing is missing: every book " + ("asked for " if dOptions.get("book") else "") + "has its cover and its manuscript's pictures. Log: " + k.sLogPath)
        return 0
    say("Missing: " + b.plural(len(lCovers), "cover") + " and " + b.plural(len(lPictures), "picture") + ".")
    if dOptions.get("dry-run"):
        for d in lCovers: say("  " + d["root"] + ": cover, from https://www.amazon.com/dp/" + (d.get("asin") or "(no ASIN)"))
        for sRoot, o in lPictures: say("  " + sRoot + ": " + (o[2] or os.path.basename(o[0]))[:50] + " (" + o[3] + "), from " + urllib.parse.urlsplit(o[1]).netloc)
        say("A dry run: no browser was opened and nothing was saved. Log: " + k.sLogPath)
        return 0
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        say("Playwright is missing. Run scripts\\kdpSubmit.cmd once to install it, then run this again.")
        return 3
    sProfile = os.path.join(os.environ.get("LOCALAPPDATA", k.sFolder), "KdpSubmit", "edgeProfile")
    k.closeLeftovers(sProfile)
    os.makedirs(sProfile, exist_ok=True)
    lFailed, iFetched = [], 0
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(sProfile, channel="msedge", headless=False, args=["--start-maximized"], viewport=None)
            page = browser.pages[0] if browser.pages else browser.new_page()
            page.set_default_timeout(30000)
            k.watchBrowser(page)
            say("Fetching in Edge. Nothing on KDP or Amazon is changed by this run.")
            for d in lCovers:
                log("COVER " + d["root"])
                sFailure = fetchCover(page, d)
                if sFailure: lFailed.append(d["root"] + ", cover: " + sFailure)
                else: iFetched += 1
            for sRoot, (sPath, sUrl, sAlt, sWhy) in lPictures:
                log("PICTURE " + sRoot + ": " + sUrl)
                sFailure = fetchPicture(page, sRoot, sPath, sUrl, sAlt, sWhy)
                if sFailure: lFailed.append(sRoot + ", " + sFailure)
                else: iFetched += 1
            browser.close()
    except Exception as oError:
        import traceback
        log("CRASH: " + traceback.format_exc())
        say("The script hit an error: " + str(oError).splitlines()[0][:200] + ". The details are in the log.")
        return 4
    say(b.plural(iFetched, "item") + " fetched; " + b.plural(len(lFailed), "item") + " could not be" + (":" if lFailed else "."))
    for s in lFailed: say("  " + s[:300])
    if iFetched: say("Run scripts\\buildBooks next, so the books use what was fetched.")
    say("Log: " + k.sLogPath)
    return 5 if lFailed else 0


if __name__ == "__main__":
    sys.exit(main())
