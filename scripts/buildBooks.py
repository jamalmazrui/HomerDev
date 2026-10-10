"""buildBooks.py -- turns each book manuscript in books\\<root>\\<root>.md into an EPUB in results\\, and audits it.

WHAT IT DOES, FOR EACH BOOK IN configs\\books.inix
  1. Gathers, on the first run for a book or when you give --gather: the published Word file, the cover, and any images
     folder beside an earlier copy of the manuscript, from the folders listed in configs\\buildBooks.inix. Word files go
     to books\\<root>\\sources\\ and a cover to books\\<root>\\<root>.jpg. Nothing is taken out of the place it was found.
  2. Imports the Word file as books\\<root>\\<root>.md when there is no manuscript yet, pictures and all.
  3. Finds every picture the manuscript names, in this order: the book's images folder; an images folder found in
     step 1; the Word file, matched by the picture's own file name stored inside it; then the web address itself. A
     picture found any of these ways is saved into books\\<root>\\images\\, so the next build needs nothing else.
     A picture that cannot be found is an error, and the book is marked not ready.
  4. Builds the EPUB with Pandoc: title, subtitle and author as KDP shows them, the description and keywords from
     data\\books\\<root>.inix, a linked contents list, the cover, and the stylesheet in templates\\. Pictures are scaled
     down in the EPUB copy only. Accessibility metadata is then added to the package file.
  5. Audits the EPUB with EPUBCheck and with Ace by DAISY, and checks the manuscript itself: pictures and their text
     alternatives, headings, links, stray characters, reading level, and the sections every book of its kind carries.
  6. Writes results\\<root>-audit.md and .htm, and results\\Audit_Summary.md and .htm for all books.

It never changes a manuscript, a Word file or a picture you already have; it only adds missing pictures and imports
missing manuscripts. It installs or updates what it needs itself: Pandoc, Java and Node.js with winget, Pillow with pip,
EPUBCheck from its GitHub releases, and Ace with npm, keeping EPUBCheck and Ace under %LOCALAPPDATA%\\MyBooks\\tools.
It uses the HomerDev kit, 1.56.0 or later, wherever it is: media.py chooses the newest Pandoc, Java and npm on the
machine rather than the first on the PATH, and inix.py reads every .inix file.

USAGE
  scripts\\buildBooks.cmd                     build and audit every book
  scripts\\buildBooks.cmd --book Mental       only books whose root or title starts with Mental (may be repeated)
  scripts\\buildBooks.cmd --gather            search the folders again for Word files, covers and images folders
  scripts\\buildBooks.cmd --all             build every book, even those unchanged since their last build
A single dash works too, so -book means --book.

Only books that changed are built (9 October 2026): a book's audit records a build fingerprint -- its sources by content,
its catalog entry and data, the kit's book templates and the Pandoc version -- and a book whose ready audit names the
same fingerprint and its exact EPUB is kept as it is.

EXIT CODES  0 every book built and ready to submit; 1 at least one book not ready (see results\\Audit_Summary.md);
2 the settings or catalog could not be read; 3 the HomerDev kit, Pandoc or Pillow could not be found or installed; 4 crash.

Every run writes logs\\MyBooks-buildBooks-<date>-<time>.log in the project folder.
"""

import collections, datetime, glob, html, json, os, platform, posixpath, re, shutil, subprocess, sys, time, traceback, unicodedata, urllib.parse, urllib.request, uuid, zipfile

# The way an EPUB is made: raised when buildBooks changes what it puts in a book, so every book is built again once.
c_sBuildFormat = "2026-10-09"
c_dDefaults = {"author": "", "ownTemplates": "", "imageMaxBytes": "150000", "imageMaxEdge": "1000", "jpegQuality": "75", "pandocMinimum": "3.1", "searchDepth": "6", "toolRefreshDays": "7", "userAgent": "HomerBooksBuild/1"}
c_dSeriesSections = {"Strange Truths": ["Copyright", "Table of Contents", "Introduction", "Conclusion", "Key Terms", "Further Reading", "Also in the Strange Truths Series", "About the Author"]}
c_iLongSentence = 30
c_iWordDiffPercent = 5
c_lCoverExtensions = [".jpg", ".jpeg", ".png"]
c_lSourceExtensions = [".docx", ".epub", ".htm", ".html", ".pdf"]
c_lImageExtensions = ["png", "jpg", "jpeg", "gif", "svg", "webp", "tif", "tiff", "bmp"]
c_lSkipFolders = ["$recycle.bin", ".git", "appdata", "node_modules", "system volume information", "windows"]
c_nDeliveryFeePerMb = 0.15
c_sAceVersionCheck = "@daisy/ace"
c_sBrowserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
c_sKitNeeded = "1.63.0"
c_sEpubcheckApi = "https://api.github.com/repos/w3c/epubcheck/releases/latest"

lLog = []
sFolder = os.path.dirname(os.path.abspath(__file__))
sProject = os.path.dirname(sFolder) if os.path.basename(sFolder).lower() == "scripts" else sFolder
sLogPath = ""
sStamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
bWindows = platform.system() == "Windows"
dSettings = {}
dTools = {}
oImage = None
inix = None
kdpEpub = None
media = None
paths = None


# ---------------------------------------------------------------- logging, inix, commands

def log(sText):
    """Adds a timed line to the log and writes the log file as it goes, so a crash loses nothing."""
    sLine = datetime.datetime.now().strftime("%H:%M:%S") + " " + sText
    lLog.append(sLine)
    if sLogPath:
        # Appended a line at a time (8 October 2026, from an audit by another AI): rewriting the whole file for every line
        # grew with the square of the log, thousands of rewrites in a long build. The first line starts the file.
        bNew = not os.path.exists(sLogPath)
        with open(sLogPath, "ab") as f: f.write((b"\xef\xbb\xbf" if bNew else b"") + (sLine + "\r\n").encode("utf-8"))
    return True


def say(sText):
    """Prints a line for the person and logs it too."""
    print(sText, flush=True)
    return log("SAY " + sText)


def ownBook(dBook):
    """Whether the book is the project's own author's, rather than a public domain work it reproduces: its catalog entry
    may say publicDomain = yes; otherwise a book is the author's own when configs\\buildBooks.inix names no author, or
    when the book's author includes that name. Its own book gets a copyright line and an About the Author section; a
    reproduced work gets neither. The kit's book tools carry no author's name of their own."""
    if dBook.get("publicDomain", "").lower() == "yes": return False
    sOwner = dSettings.get("author", "").strip()
    return not sOwner or sOwner.lower() in dBook.get("author", "").lower()


def plural(iCount, sNoun, sPlural=""):
    """Matches the noun to the count: 1 error, 2 errors, 0 errors."""
    return str(iCount) + " " + (sNoun if iCount == 1 else (sPlural or sNoun + "s"))


def readInix(sPath):
    """{section: {key: value}} from an .inix file, through the kit's inix.readInix, the reader of the block form that
    help\\Inix.md documents. Trimming the end of each value is this script's choice, made here, not the reader's."""
    dSections = inix.readInix(sPath)
    for sLine in inix.lsIgnored: log("ignored line outside any key in " + os.path.basename(sPath) + ": " + sLine[:80])
    return {sSection: {sKey: sValue.rstrip() for sKey, sValue in dKeys.items()} for sSection, dKeys in dSections.items()}


def inixList(sValue):
    """A list from an .inix value, through the kit's inix.inixList: one item per line, or comma-separated on one line."""
    return inix.inixList(sValue)


def writeText(sPath, sText, bBom=True):
    """Writes text as UTF-8 with CRLF line ends, with a byte order mark unless told not to."""
    os.makedirs(os.path.dirname(sPath), exist_ok=True)
    with open(sPath, "wb") as f: f.write((b"\xef\xbb\xbf" if bBom else b"") + sText.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))
    return True


def run(lCommand, sCwd=None, iTimeout=1800):
    """Runs a command, logs it with its exit code and output, and returns (code, output)."""
    log("run: " + subprocess.list2cmdline(lCommand) + (" (in " + sCwd + ")" if sCwd else ""))
    try:
        oResult = subprocess.run(lCommand, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=sCwd, shell=bWindows, timeout=iTimeout)
    except FileNotFoundError as oError:
        log("  not found: " + str(oError))
        return 127, str(oError)
    except subprocess.TimeoutExpired:
        log("  timed out after " + str(iTimeout) + " seconds")
        return 124, "timed out"
    sOut = (oResult.stdout or "") + (oResult.stderr or "")
    log("  exit " + str(oResult.returncode))
    for sLine in sOut.strip().splitlines()[:80]: log("  | " + sLine)
    return oResult.returncode, sOut


def fetchBytes(sUrl, sAgent):
    """The bytes at a web address, fetched with the given program name."""
    oRequest = urllib.request.Request(sUrl, headers={"User-Agent": sAgent})
    with urllib.request.urlopen(oRequest, timeout=120) as oResponse: return oResponse.read()


def download(sUrl, sPath):
    """Downloads a web address to a file; returns an error message, or empty on success. It names this program as
    Wikimedia asks. A Wikimedia thumbnail of a size Wikimedia no longer makes (it answers 400, 'Use thumbnail sizes')
    is fetched as the original picture instead, which the build scales itself. A site that refuses a program by name
    (403) is asked once more as an ordinary browser."""
    log("download: " + sUrl + " -> " + sPath)
    lTries = [(sUrl, dSettings["userAgent"])]
    oThumb = re.match(r"^(https?://upload\.wikimedia\.org/wikipedia/[^/]+)/thumb/(.+?)/[^/]+$", sUrl)
    if oThumb: lTries.append((oThumb.group(1) + "/" + oThumb.group(2), dSettings["userAgent"]))
    if "wikimedia.org" not in sUrl: lTries.append((sUrl, c_sBrowserAgent))
    sLast = ""
    for sTry, sAgent in lTries:
        try:
            binData = fetchBytes(sTry, sAgent)
            os.makedirs(os.path.dirname(sPath), exist_ok=True)
            with open(sPath, "wb") as f: f.write(binData)
            log("  saved " + format(len(binData), ",") + " bytes from " + sTry + (" as a browser" if sAgent == c_sBrowserAgent else ""))
            return ""
        except Exception as oError:
            sLast = str(oError)
            log("  failed: " + sTry + (" as a browser" if sAgent == c_sBrowserAgent else "") + ": " + sLast)
    return sLast


def rootName(sTitle):
    """The file root for a book: its title without a leading A, An or The, other words joined by underscores."""
    s = re.sub(r"^(a|an|the)\s+", "", sTitle.strip(), flags=re.I).replace("\u2019", "").replace("'", "")
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")


def titleKey(sTitle):
    """Sort key for titles: case-insensitive, ignoring a leading A, An or The."""
    return re.sub(r"^(a|an|the)\s+", "", sTitle.strip(), flags=re.I).lower()


def workFolder(*lsParts):
    """A folder under MyBooks' per-user temp folder, %LOCALAPPDATA%\\MyBooks\\temp, from the kit's paths.temp(): the
    Homer place for scratch files, emptied at the start of each build."""
    sPath = os.path.join(paths.temp(), *lsParts)
    os.makedirs(sPath, exist_ok=True)
    return sPath


def bookFile(dBook, sName):
    """A file in the book's own folder, books\\<root>\\."""
    return os.path.join(sProject, "books", dBook["root"], sName)


def bookDocx(dBook):
    """The book's published Word files beside its manuscript, oldest first."""
    return sorted(glob.glob(bookFile(dBook, "*.docx")), key=os.path.getmtime)


def retireTo(sPath):
    """Moves a file into the project's notes folder, never deleting it. Like the kit's tidy, a name already there gets
    the run's date and time added, so nothing is overwritten. Returns the new path."""
    sNotes = os.path.join(sProject, "notes")
    os.makedirs(sNotes, exist_ok=True)
    sTarget = os.path.join(sNotes, os.path.basename(sPath))
    if os.path.exists(sTarget):
        sStem, sExt = os.path.splitext(os.path.basename(sPath))
        sTarget = os.path.join(sNotes, sStem + "-" + sStamp + sExt)
    shutil.move(sPath, sTarget)
    return sTarget


def tidyEarlierLayout(dCatalog):
    """Puts right what the first versions of this script left on disk, logging each step, so unzipping and building is
    all it takes: Word files and found.inix move out of each book's sources folder to sit beside the manuscript; the
    old temp folder in the project, results\\ace, and the old %LOCALAPPDATA%\\MyBooks\\tools folder are removed, since
    the build now keeps scratch files in the Homer per-user temp folder, EPUBCheck in the kit's exec folder, and Ace
    where npm installs it; a retired folder in notes is flattened into notes."""
    for dBook in dCatalog.values():
        sSources = bookFile(dBook, "sources")
        if not os.path.isdir(sSources): continue
        for sName in os.listdir(sSources):
            sTarget = bookFile(dBook, sName)
            if os.path.exists(sTarget): os.remove(sTarget)
            shutil.move(os.path.join(sSources, sName), sTarget)
            log(dBook["root"] + ": moved sources\\" + sName + " beside the manuscript")
        shutil.rmtree(sSources, ignore_errors=True)
    sLocal = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), ".cache")
    for sOld in (os.path.join(sProject, "temp"), os.path.join(sProject, "results", "ace"), os.path.join(sLocal, "MyBooks", "tools")):
        if os.path.isdir(sOld):
            shutil.rmtree(sOld, ignore_errors=True)
            log("removed " + sOld + ", which the earlier layout used")
    sRetired = os.path.join(sProject, "notes", "retired")
    if os.path.isdir(sRetired):
        for sDir, lDirs, lFiles in os.walk(sRetired):
            for sName in lFiles: log("flattened into notes: " + retireTo(os.path.join(sDir, sName)))
        shutil.rmtree(sRetired, ignore_errors=True)
    return True


# ---------------------------------------------------------------- tools

def isKit(sFolder):
    """Does this folder hold the kit's shared Python modules this script uses?"""
    return bool(sFolder) and all(os.path.isfile(os.path.join(sFolder, "exec", "Python", s)) for s in ("inix.py", "media.py"))


def locateKit():
    """The HomerDev kit's folder, found as the kit's kind.findKit finds it: the HomerDev environment variable, then
    from the project upward, then a HomerDev folder at the top of any drive. Only Windows and the folder name HomerDev
    are assumed, never a drive or a depth."""
    sEnv = os.environ.get("HomerDev", "")
    if isKit(sEnv): return os.path.abspath(sEnv)
    sDir = sProject
    while True:
        if isKit(sDir): return sDir
        if isKit(os.path.join(sDir, "HomerDev")): return os.path.join(sDir, "HomerDev")
        sUp = os.path.dirname(sDir)
        if sUp == sDir: break
        sDir = sUp
    for sLetter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
        if isKit(sLetter + ":\\HomerDev"): return sLetter + ":\\HomerDev"
    return ""


def bookTemplate(sName):
    """A file the build uses from templates: the kit's own, in Templates\\books, which every book publishing project
    shares, so an improvement made once in the kit reaches every project; or the project's own copy in templates, when
    configs\\buildBooks.inix says ownTemplates = yes. (A project's copy used first would go stale unnoticed the first
    time the kit's changed.)"""
    sOwn = os.path.join(sProject, "templates", sName)
    if dSettings.get("ownTemplates", "").lower() == "yes" and os.path.exists(sOwn):
        log("template " + sName + ": the project's own, " + sOwn)
        return sOwn
    sKit = locateKit()
    sShared = os.path.join(sKit, "Templates", "books", sName) if sKit else ""
    if sShared and os.path.exists(sShared):
        log("template " + sName + ": the kit's, " + sShared)
        return sShared
    log("template " + sName + ": the kit's copy was not found, so the project's, " + sOwn)
    return sOwn


def loadKit():
    """Finds the kit, checks its version, and imports its media and inix modules. Returns an empty string, or a plain
    sentence naming what is missing and where it belongs."""
    global inix, kdpEpub, media, paths
    sKit = locateKit()
    if not sKit: return "The HomerDev kit was not found. buildBooks uses its exec\\Python\\media.py and inix.py. Unzip HomerDev.zip into C:\\HomerDev, or set the HomerDev environment variable to the kit's folder."
    sVersionFile = os.path.join(sKit, "version.txt")
    sVersion = open(sVersionFile, "rb").read().decode("utf-8-sig").strip() if os.path.isfile(sVersionFile) else ""
    log("HomerDev kit " + (sVersion or "of unknown version") + " at " + sKit + "; this script needs " + c_sKitNeeded + " or later")
    if versionTuple(sVersion) < versionTuple(c_sKitNeeded): return "The HomerDev kit at " + sKit + " is version " + (sVersion or "unknown") + "; buildBooks needs " + c_sKitNeeded + " or later. Unzip the newest HomerDev.zip there and run its build."
    sPython = os.path.join(sKit, "exec", "Python")
    if sPython not in sys.path: sys.path.insert(0, sPython)
    import inix as oInix, kdpEpub as oKdpEpub, media as oMedia, paths as oPaths
    inix, kdpEpub, media, paths = oInix, oKdpEpub, oMedia, oPaths
    paths.start("MyBooks")
    dTools["kit"], dTools["kitVersion"] = sKit, sVersion
    return ""


def toolSearch(sChosen):
    """Writes the kit's account of a tool search to the log, says when an older copy comes first on the PATH, and
    returns the chosen path."""
    for sLine in media.searchLog().splitlines(): log(sLine)
    if sChosen and media.shadowNote(): say(media.shadowNote())
    return sChosen


def winget(sId):
    """Installs or upgrades a package with winget, the way every Homer build fetches what it needs."""
    if not bWindows:
        log("winget is Windows-only; " + sId + " must be installed by hand here")
        return False
    say("Installing or updating " + sId + " with winget. This can take a few minutes.")
    lCommon = ["--id", sId, "--exact", "--silent", "--accept-package-agreements", "--accept-source-agreements"]
    iCode, sOut = run(["winget", "install"] + lCommon)
    if iCode != 0 and "No available upgrade" not in sOut and "No newer package" not in sOut: iCode, sOut = run(["winget", "upgrade"] + lCommon)
    return iCode == 0 or "No available upgrade" in sOut or "No newer package" in sOut


def versionTuple(sText):
    """Turns the first dotted number in some text into a tuple for comparing versions."""
    oMatch = re.search(r"(\d+(?:\.\d+)+)", sText or "")
    return tuple(int(s) for s in oMatch.group(1).split(".")) if oMatch else (0,)


def ensurePandoc():
    """The newest Pandoc on the machine at or above the settings' minimum, from the kit's media.pandocProgram, never
    merely the first on the PATH; installs or upgrades it with winget only when no copy qualifies."""
    for iTry in range(2):
        sPandoc = toolSearch(media.pandocProgram(dSettings["pandocMinimum"]))
        if sPandoc:
            dTools["pandoc"], dTools["pandocVersion"] = sPandoc, media.dLast.get("version", "")
            return True
        if iTry == 0: winget("JohnMacFarlane.Pandoc")
    return False


def ensurePillow():
    """Pillow, for checking and scaling pictures; installs it with pip when missing."""
    global oImage
    try:
        from PIL import Image as oPilImage
    except ImportError:
        say("Installing Pillow with pip.")
        run([sys.executable, "-m", "pip", "install", "--upgrade", "pillow"])
        try:
            from PIL import Image as oPilImage
        except ImportError:
            return False
    oImage = oPilImage
    oImage.MAX_IMAGE_PIXELS = None
    log("Pillow " + getattr(oPilImage, "__version__", "") + " ready")
    return True


def isStale(sStampFile):
    """True when a tool was last checked longer ago than the settings allow."""
    if not os.path.exists(sStampFile): return True
    return time.time() - os.path.getmtime(sStampFile) > float(dSettings["toolRefreshDays"]) * 86400


def ensureJava():
    """The newest Java on the machine, 11 or later, which EPUBCheck needs, from the kit's media.javaProgram; installs
    Microsoft's OpenJDK 21 with winget only when no copy qualifies."""
    for iTry in range(2):
        sJava = toolSearch(media.javaProgram("11"))
        if sJava:
            dTools["java"] = sJava
            return True
        if iTry == 0: winget("Microsoft.OpenJDK.21")
    return False


def ensureEpubcheck():
    """EPUBCheck, the W3C's EPUB validator, from its latest GitHub release; checked for a newer release every few days."""
    if not ensureJava(): return False
    sHome = os.path.join(dTools["kit"], "exec", "epubcheck")
    sStampFile = os.path.join(sHome, "version.txt")
    lJars = glob.glob(os.path.join(sHome, "**", "epubcheck.jar"), recursive=True)
    if lJars and not isStale(sStampFile):
        dTools["epubcheck"] = lJars[0]
        dTools["epubcheckVersion"] = open(sStampFile, encoding="utf-8").read().strip()
        return True
    try:
        oRequest = urllib.request.Request(c_sEpubcheckApi, headers={"User-Agent": dSettings["userAgent"], "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(oRequest, timeout=60) as oResponse: dRelease = json.loads(oResponse.read().decode("utf-8"))
        sTag = dRelease.get("tag_name", "")
        sInstalled = open(sStampFile, encoding="utf-8").read().strip() if os.path.exists(sStampFile) else ""
        log("EPUBCheck latest release " + sTag + ", installed " + (sInstalled or "none"))
        if sTag != sInstalled or not lJars:
            lAssets = [d for d in dRelease.get("assets", []) if d.get("name", "").lower().startswith("epubcheck") and d.get("name", "").lower().endswith(".zip")]
            if not lAssets: raise RuntimeError("no zip asset in release " + sTag)
            sZip = os.path.join(workFolder(), lAssets[0]["name"])
            sProblem = download(lAssets[0]["browser_download_url"], sZip)
            if sProblem: raise RuntimeError(sProblem)
            if os.path.isdir(sHome): shutil.rmtree(sHome, ignore_errors=True)
            zipfile.ZipFile(sZip).extractall(sHome)
            os.remove(sZip)
        writeText(sStampFile, sTag, False)
    except Exception as oError:
        log("EPUBCheck update check failed: " + str(oError))
    lJars = glob.glob(os.path.join(sHome, "**", "epubcheck.jar"), recursive=True)
    if not lJars: return False
    dTools["epubcheck"] = lJars[0]
    dTools["epubcheckVersion"] = open(sStampFile, encoding="utf-8").read().strip() if os.path.exists(sStampFile) else ""
    return True


def ensureAce():
    """Ace by DAISY, the EPUB accessibility checker, installed with npm's ordinary global install, so any project can
    run it; Node.js comes from winget. Checked for a newer release every few days, the check noted in MyBooks' per-user
    data folder."""
    sNpm = media.findInstalled("npm")
    log(media.searchLog())
    if not sNpm:
        winget("OpenJS.NodeJS.LTS")
        sNpm = media.findInstalled("npm")
        log(media.searchLog())
    if not sNpm: return False
    if bWindows: os.environ["PATH"] = os.path.dirname(sNpm) + os.pathsep + os.environ.get("PATH", "")
    iCode, sPrefix = run([sNpm, "prefix", "-g"])
    sGlobal = sPrefix.strip().splitlines()[-1].strip() if iCode == 0 and sPrefix.strip() else ""
    if sGlobal: os.environ["PATH"] = (sGlobal if bWindows else os.path.join(sGlobal, "bin")) + os.pathsep + os.environ.get("PATH", "")
    # COMPARE BEFORE INSTALLING (10 October 2026). Every few days this ran npm install @latest whatever was installed,
    # and npm reinstalled Ace and its own copy of Chromium -- minutes, for nothing, when 1.4.6 was already the latest.
    # Now the installed version is compared with the registry's (npm view downloads nothing), and npm installs only a
    # newer one, or a missing one. Between checks, the stamp file holds the version, so not even ace --version runs.
    sStampFile = os.path.join(paths.data(), "aceChecked.txt")
    sAce = media.findInstalled("ace")
    sStamped = open(sStampFile, encoding="utf-8").read().strip() if os.path.exists(sStampFile) else ""
    sStampedVersion = sStamped.split("|")[1] if "|" in sStamped else ""
    if sAce and sStampedVersion and not isStale(sStampFile):
        log("Ace by DAISY " + sStampedVersion + " was checked against npm within the last " + str(dSettings["toolRefreshDays"]) + " days; not checked again")
        dTools["ace"], dTools["aceVersion"] = sAce, sStampedVersion
        return True
    sInstalled = ""
    if sAce:
        iCode, sOut = run([sAce, "--version"])
        sInstalled = sOut.strip().splitlines()[-1].strip() if iCode == 0 and sOut.strip() else ""
    iCode, sOut = run([sNpm, "view", c_sAceVersionCheck, "version"])
    sLatest = sOut.strip().splitlines()[-1].strip() if iCode == 0 and sOut.strip() else ""
    log("Ace by DAISY: installed %s, latest on npm %s" % (sInstalled or "none", sLatest or "unknown (npm could not be asked)"))
    if not sAce or (sLatest and versionTuple(sLatest) > versionTuple(sInstalled)):
        say(("Updating Ace by DAISY from %s to %s" % (sInstalled, sLatest) if sAce else "Installing Ace by DAISY") + " with npm. This downloads a copy of Chromium and takes a few minutes.")
        iCode, _ = run([sNpm, "install", "--global", c_sAceVersionCheck + "@" + (sLatest or "latest")], iTimeout=3600)
        sAce = media.findInstalled("ace")
        if sAce:
            iCode, sOut = run([sAce, "--version"])
            sInstalled = sOut.strip().splitlines()[-1].strip() if iCode == 0 and sOut.strip() else sLatest
    log(media.searchLog())
    if not sAce: return False
    # The stamp is written only when npm answered, so a check that could not reach the registry is tried again next time.
    if sLatest: writeText(sStampFile, datetime.datetime.now().isoformat() + "|" + sInstalled, False)
    dTools["ace"], dTools["aceVersion"] = sAce, sInstalled
    return True


# ---------------------------------------------------------------- gathering sources

def searchIndex():
    """One walk of the search folders, indexing Word files, manuscripts, cover candidates and images folders by a simplified file stem."""
    dIndex = {}
    iDepth = int(dSettings["searchDepth"])
    sOwn = os.path.normcase(os.path.abspath(sProject))
    for sRaw in inixList(dSettings.get("searchFolders", "")):
        sTop = os.path.abspath(os.path.expandvars(sRaw))
        if not os.path.isdir(sTop):
            log("search folder not present: " + sTop)
            continue
        log("searching " + sTop)
        iTopDepth = sTop.rstrip("\\/").count(os.sep)
        for sDir, lDirs, lFiles in os.walk(sTop):
            sNorm = os.path.normcase(os.path.abspath(sDir))
            if sNorm.startswith(sOwn) and sNorm != sOwn:
                sRel = os.path.relpath(sNorm, sOwn).split(os.sep)[0]
                if sRel in ("books", "logs", "notes", "results"):
                    lDirs[:] = []
                    continue
            if sDir.count(os.sep) - iTopDepth >= iDepth: lDirs[:] = []
            lDirs[:] = [s for s in lDirs if s.lower() not in c_lSkipFolders]
            for sName in lFiles:
                sStem, sExt = os.path.splitext(sName)
                if sExt.lower() not in c_lSourceExtensions + [".md"] + c_lCoverExtensions: continue
                if os.path.basename(sDir).lower() == "images": continue
                dIndex.setdefault(simpleStem(sStem), []).append(os.path.join(sDir, sName))
    log("search index holds " + plural(len(dIndex), "name"))
    return dIndex


def simpleStem(sText):
    """Lower case letters and digits only, so Edges_of_Maps, The_Edges_Of_Maps and The Edges of Maps all compare alike."""
    s = re.sub(r"^(a|an|the)[\s_]+", "", sText.strip(), flags=re.I).replace("\u2019", "").replace("'", "")
    return re.sub(r"[^a-z0-9]", "", s.lower())


def safeTime(sPath):
    """A file's modified time, or 0 when it cannot be read, as with a OneDrive file whose provider is not running."""
    try:
        return os.path.getmtime(sPath)
    except OSError:
        return 0


lsUnreadable = []


def copyFound(sSource, sTarget):
    """Copies a file the search found; returns False, noting it for the closing message, when it cannot be read. Windows
    error 362 means OneDrive, or another cloud provider, holds only a placeholder and is not running."""
    try:
        shutil.copy2(sSource, sTarget)
        return True
    except OSError as oError:
        log("could not copy " + sSource + ": " + str(oError))
        lsUnreadable.append(sSource)
        return False


def gatherBook(dBook, dIndex):
    """Copies the newest Word file into sources, a cover beside the manuscript, and notes images folders found beside earlier copies."""
    sRoot = dBook["root"]
    sBookDir = os.path.join(sProject, "books", sRoot)
    lStems = {simpleStem(sRoot), simpleStem(dBook["title"]), simpleStem(dBook["title"] + " " + dBook["subtitle"])}
    for sName in dBook["formerNames"]: lStems.add(simpleStem(os.path.splitext(sName)[0]))
    lHits = []
    for sStem in lStems: lHits += dIndex.get(sStem, [])
    lHits = sorted(set(lHits))
    # The manuscript sources, best first: a Word file is the author's own manuscript; an EPUB is a finished book;
    # a PDF is a printed page, read back with the most guesswork. Only the best kind found is taken.
    lDocx = []
    for sExt in c_lSourceExtensions:
        lDocx = [s for s in lHits if s.lower().endswith(sExt) and not os.path.basename(s).startswith("~$")]
        if lDocx: break
    lCovers = [s for s in lHits if os.path.splitext(s)[1].lower() in c_lCoverExtensions]
    lImageDirs = []
    for sHit in lHits:
        if os.path.splitext(sHit)[1].lower() not in (".md", ".docx"): continue
        sImages = os.path.join(os.path.dirname(sHit), "images")
        if os.path.isdir(sImages) and sImages not in lImageDirs: lImageDirs.append(sImages)
    dFound = {"gatheredOn": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "docx": "", "cover": "", "imageFolders": "\n".join(lImageDirs)}
    if lDocx:
        sNewest = max(lDocx, key=safeTime)
        sTarget = os.path.join(sBookDir, os.path.basename(sNewest))
        if os.path.normcase(sNewest) != os.path.normcase(sTarget):
            os.makedirs(os.path.dirname(sTarget), exist_ok=True)
            if not copyFound(sNewest, sTarget): sNewest = ""
            log(sRoot + ": copied Word file " + sNewest)
        dFound["docx"] = sNewest
    bHaveCover = any(os.path.exists(os.path.join(sBookDir, sRoot + s)) for s in c_lCoverExtensions)
    if lCovers and not bHaveCover:
        sNewest = max(lCovers, key=safeTime)
        if not copyFound(sNewest, os.path.join(sBookDir, sRoot + os.path.splitext(sNewest)[1].lower())): sNewest = ""
        log(sRoot + ": copied cover " + sNewest)
        dFound["cover"] = sNewest
    lOut = ["[found]"] + [k + " = " + v if "\n" not in v and v else k + " =" + ("\n" + v if v else "") for k, v in dFound.items()]
    writeText(os.path.join(sBookDir, "found.inix"), "\n".join(lOut) + "\n")
    return dFound


def retireFormer(dBook):
    """Moves earlier copies under former names, at the top of the project and in data\\books, into notes, never
    deleting them."""
    lMoved = []
    sManuscript = bookFile(dBook, dBook["root"] + ".md")
    for sName in dBook["formerNames"] + [dBook["formerKdpInix"]]:
        if not sName: continue
        sOld = os.path.join(sProject, sName)
        if os.path.isfile(sOld):
            if sName.lower().endswith(".md") and os.path.exists(sManuscript) and open(sOld, "rb").read() != open(sManuscript, "rb").read():
                say("Note: " + sName + " at the top of the project differs from books\\" + dBook["root"] + "\\" + dBook["root"] + ".md; it is kept in notes for you to compare.")
            lMoved.append(sName + " -> " + retireTo(sOld))
    sOldInix = os.path.join(sProject, "data", "books", dBook["formerKdpInix"])
    sNewInix = os.path.join(sProject, "data", "books", dBook["root"] + ".inix")
    if dBook["formerKdpInix"] and os.path.isfile(sOldInix):
        if os.path.normcase(sOldInix) == os.path.normcase(sNewInix):
            if dBook["root"] + ".inix" not in os.listdir(os.path.dirname(sNewInix)):
                sTemp = sNewInix + ".renaming"
                os.rename(sOldInix, sTemp)
                os.rename(sTemp, sNewInix)
                lMoved.append(dBook["formerKdpInix"] + " (renamed in place)")
        elif os.path.isfile(sNewInix):
            lMoved.append("data\\books\\" + dBook["formerKdpInix"] + " -> " + retireTo(sOldInix))
    for s in lMoved: log(dBook["root"] + ": retired " + s)
    return lMoved


def bookSource(dBook):
    """The book's best source beside its manuscript folder: a Word file, else an EPUB, else a PDF; "" when none."""
    for sExt in c_lSourceExtensions:
        lFound = sorted(glob.glob(os.path.join(sProject, "books", dBook["root"], "*" + sExt)), key=safeTime)
        if lFound: return lFound[-1]
    return ""


def ensurePdfReader():
    """pdfplumber, which reads each word of a PDF with its size and font; installed with pip when missing."""
    try:
        import pdfplumber
    except ImportError:
        say("Installing pdfplumber with pip, to read a PDF manuscript.")
        run([sys.executable, "-m", "pip", "install", "--upgrade", "pdfplumber"])
        try:
            import pdfplumber
        except ImportError:
            return None
    return pdfplumber


def joinText(sBefore, sAfter):
    """Joins two lines of one paragraph; a web address broken at a hyphen, slash or dot is rejoined with nothing between."""
    if not sBefore: return sAfter
    if re.search(r"https?://\S*[-/.]$", sBefore): return sBefore + sAfter
    return sBefore + " " + sAfter


def pageColumns(lWords, oPage):
    """The text columns of a page as (left, right) spans, found from the vertical gaps no word crosses; a one-column
    page gives one span. A Federal Register page gives three."""
    if not lWords: return []
    lCovered = [0] * (int(oPage.width) + 2)
    for d in lWords:
        if d["x1"] - d["x0"] > oPage.width * 0.4: continue
        for x in range(max(0, int(d["x0"])), min(len(lCovered), int(d["x1"]) + 1)): lCovered[x] += 1
    # A gutter is a strip nearly empty beside the busiest strip, so a line or caption that bridges the columns here
    # and there does not merge them.
    nThreshold = max(1, max(lCovered) * 0.1)
    lSpans, iStart = [], None
    for x, iCount in enumerate(lCovered):
        if iCount >= nThreshold and iStart is None: iStart = x
        elif iCount < nThreshold and iStart is not None:
            lSpans.append([iStart, x])
            iStart = None
    if iStart is not None: lSpans.append([iStart, len(lCovered)])
    lMerged = []
    for lSpan in lSpans:
        if lMerged and lSpan[0] - lMerged[-1][1] < 8: lMerged[-1][1] = lSpan[1]
        else: lMerged.append(lSpan)
    lMerged = [l for l in lMerged if l[1] - l[0] > oPage.width * 0.12]
    return [tuple(l) for l in lMerged] or [(0, oPage.width)]


def columnOf(dWord, lColumns):
    """The index of the column a word sits in: the span holding its middle, else the nearest."""
    nMiddle = (dWord["x0"] + dWord["x1"]) / 2
    for i, (nLeft, nRight) in enumerate(lColumns):
        if nLeft - 3 <= nMiddle <= nRight + 3: return i
    return min(range(len(lColumns)), key=lambda i: min(abs(nMiddle - lColumns[i][0]), abs(nMiddle - lColumns[i][1]))) if lColumns else 0


def dropRunning(lWords, oPage, setRunning):
    """The words of a page without its running heads and printer's stamps: lines near the top or bottom whose letters
    repeat on most pages."""
    lOut = []
    for d in lWords:
        if d["top"] < oPage.height * 0.08 or d["top"] > oPage.height * 0.92:
            sKey = re.sub(r"[\d\W]+", "", " ".join(x["text"] for x in lWords if abs(x["top"] - d["top"]) < 2)).lower()
            if sKey in setRunning or not sKey: continue
        lOut.append(d)
    return lOut


def tableRows(lRaw):
    """Rows of a table pdfplumber found. A Federal Register table draws only its top and bottom rules, so a body
    row arrives holding every line of each column; when the cells of such a row hold equal numbers of lines, they are
    split back into rows. Dot leaders are dropped."""
    lRows = []
    for lRow in lRaw or []:
        lCells = [re.sub(r"\s*\.{3,}\s*", " ", c or "").strip() for c in lRow]
        lSplit = [c.split("\n") for c in lCells]
        lCounts = {len(l) for l, c in zip(lSplit, lCells) if c}
        if len(lCounts) == 1 and list(lCounts)[0] > 1 and all(c for c in lCells):
            for i in range(list(lCounts)[0]): lRows.append([re.sub(r"\s*\.{3,}\s*", " ", l[i]).strip() for l in lSplit])
        else: lRows.append([" ".join(c.split("\n")) for c in lCells])
    return [r for r in lRows if any(r)]


def renderTable(lRows):
    """A pipe table, its first row as the header."""
    iCols = max(len(r) for r in lRows)
    lRows = [[(c or "").replace("|", "/") for c in r] + [""] * (iCols - len(r)) for r in lRows]
    return "\n".join(["| " + " | ".join(lRows[0]) + " |", "|" + "---|" * iCols] + ["| " + " | ".join(r) + " |" for r in lRows[1:]])


def smallCapitals(sText):
    """Rejoins words set in small capitals, which a PDF splits after the first letter ("T ABLE 1—A NNUALIZED")."""
    if len(re.findall(r"\b[A-Z] [A-Z]{2,}", sText)) < 2: return sText
    return re.sub(r"\b([A-Z]) (?=[A-Z]{2,}\b)", r"\1", sText)


def federalRegisterOwn(lBlocks, lObserved):
    """For a Federal Register printing, only the book's own documents: each runs from its agency's name to its
    BILLING CODE line, and the pages it shares carry the end or start of other agencies' documents. The agency is the
    run of capitals that opens the first paragraph; a later document of the same agency, such as a correction, is
    kept. A paragraph is cut where a BILLING CODE line or the agency's name falls inside it."""
    if not any("BILLING CODE" in b[2] for b in lBlocks): return lBlocks
    oFirst = next((re.match(r"((?:[A-Z][A-Z,.&’'-]+ ){2,}[A-Z][A-Z,.&’'-]+)(?= |$)", b[2]) for b in lBlocks if b[0] == "p"), None)
    if not oFirst: return lBlocks
    sAgency = oFirst.group(1)
    lKept, bIn, iDropped = [], True, 0
    for sKind, iLevel, sText in lBlocks:
        while sText:
            if not bIn:
                iAt = sText.find(sAgency)
                if iAt < 0:
                    iDropped += 1
                    break
                sText, bIn = sText[iAt:], True
            oEnd = re.search(r"(\[FR Doc\.[^\]]*\]\s*)?BILLING CODE \S+", sText)
            if not oEnd:
                lKept.append((sKind, iLevel, sText))
                break
            sBefore = sText[:oEnd.start()].strip()
            if sBefore: lKept.append((sKind, iLevel, sBefore))
            sText, bIn = sText[oEnd.end():].strip(), False
    lObserved.append("Federal Register printing: kept the documents of %s; left out %d paragraphs of other agencies' documents" % (sAgency.title(), iDropped))
    return lKept


def contentsListsOut(lBlocks):
    """Regulatory text often opens a chapter with a list of its sections, set like the section headings themselves. A
    numbered heading (E205, 402, 1194.1) whose number heads a later heading too is such a list entry: it becomes an
    ordinary line, so only the real section keeps the heading."""
    def number(sText):
        o = re.match(r"^(?:§\s*)?([EC]?\d{3}(?:\.\d+)*)\s", sText)
        return o.group(1) if o else ""
    lNumbers = [number(b[2]) if b[0] == "h" else "" for b in lBlocks]
    lOut = []
    for i, b in enumerate(lBlocks):
        if b[0] == "h" and lNumbers[i] and lNumbers[i] in lNumbers[i + 1:]: lOut.append(("p", 0, b[2]))
        else: lOut.append(b)
    return lOut


def closedHeadingGaps(lLines):
    """Each heading at most one level deeper than the one before (PDF/UA's Matterhorn 14-003), as HomerScribe does:
    a reader moving by heading must never wonder what was skipped."""
    iLast, lOut = 0, []
    for sLine in lLines:
        oHead = re.match(r"^(#{1,6}) ", sLine)
        if oHead:
            iLevel = len(oHead.group(1))
            if iLast and iLevel > iLast + 1: iLevel = iLast + 1
            iLast = iLevel
            sLine = "#" * iLevel + sLine[len(oHead.group(1)):]
        lOut.append(sLine)
    return lOut


def mendedAddresses(sText):
    """Web addresses a printed page broke over lines, made whole again: a space after the scheme, or after a hyphen or
    slash inside an address, is closed when the next piece plainly continues the address. A scheme with nothing to
    continue it -- its address printed elsewhere -- is left as plain text, never a link to nowhere. Returns (text,
    number left plain)."""
    sText = re.sub(r"\b(https?://)\s+(?=[\w-]+\.[\w.-])", r"\1", sText)
    for i in range(6):
        sNew = re.sub(r"(https?://\S*[-/])\s+(?=[\w.~%?=&#:+-]*[/.=\d-][\w.~%?=&#:/+-]*)", r"\1", sText)
        if sNew == sText: break
        sText = sNew
    iPlain = len(re.findall(r"\bhttps?://(?=\s|$)", sText))
    sText = re.sub(r"\b(https?)://(?=\s|$)", r"\1\\://", sText)
    return sText, iPlain


def proseLine(sText):
    """A paragraph as Markdown that cannot turn into markup by accident, as HomerScribe's escapedForMarkdown does: a #,
    >, |, + or = that opens it is escaped. A paragraph opening with a bullet becomes a list item."""
    oBullet = re.match(r"^[•◦▪●]\s*(.*)$", sText)
    if oBullet: return "- " + oBullet.group(1)
    if re.match(r"^\s*[#>|+=]", sText): return "\\" + sText.lstrip()
    return sText


def textLayerSound(lPages):
    """Whether the text layer reads as text, as HomerScribe's textLayerIsSound judges it: a layer with almost no
    spaces, or with many characters that are neither letters, digits, spaces nor punctuation, would make a book of
    nonsense while every count looks healthy. Returns "" when sound, else why not."""
    sText = " ".join(d["text"] for oPage, lWords in lPages for d in lWords if d.get("size"))[:40000]
    if len(sText) < 40: return ""
    iJunk = sum(1 for c in sText if not (c.isalnum() or c.isspace() or unicodedata.category(c)[0] in "PS"))
    if iJunk > len(sText) / 10: return "more than a tenth of its characters are neither letters, digits nor punctuation"
    lWords = sText.split()
    if lWords and sum(len(w) for w in lWords) / len(lWords) > 15: return "its words run together, with almost no spaces between them"
    return ""


def pdfToMarkdown(sPdf, oPdfPlumber):
    """Markdown from a text PDF of the kind government offices publish, using each file's own type sizes: the most
    common size is the body, a smaller one the notes, the smallest the superscript note numbers, larger ones headings
    by rank, and a short numbered line at body size the lowest heading. Paragraphs come from first-line indents and
    gaps; note numbers become linked notes. Page numbers and dot-leader contents lines are dropped, since the EPUB
    makes its own contents, and so is the largest type, the title, which the metadata supplies. Returns (markdown,
    observations for the log)."""
    lObserved = []
    with oPdfPlumber.open(sPdf) as oPdf:
        lPages, oSizes = [], collections.Counter()
        for oPage in oPdf.pages:
            # Sideways characters are printer's stamps and margin notes, never the text.
            oPage = oPage.filter(lambda o: o.get("object_type") != "char" or o.get("upright", True))
            lTables = []
            for oTable in oPage.find_tables():
                lRows = tableRows(oTable.extract())
                # A real table has two columns or more; a rule above a page's notes can look like a one-column table.
                if len(lRows) >= 2 and sum(1 for r in lRows if sum(1 for c in r if c) >= 2) >= len(lRows) / 2: lTables.append((oTable.bbox, lRows))
            lWords = oPage.extract_words(x_tolerance=1.5, extra_attrs=["size", "fontname"])
            lWords = [d for d in lWords if not any(b[0] - 1 <= d["x0"] and d["x1"] <= b[2] + 1 and b[1] - 1 <= d["top"] and d["bottom"] <= b[3] + 1 for b, l in lTables)]
            for b, lRows in lTables: lWords.append({"text": "\u0000TABLE", "x0": b[0], "x1": b[2], "top": b[1], "bottom": b[1] + 1, "size": 0, "fontname": "table", "rows": lRows})
            lPages.append((oPage, lWords))
            for d in lWords:
                if d["size"]: oSizes[round(d["size"])] += len(d["text"])
    if not oSizes: return "", ["no text in the PDF; a scanned page needs OCR first"]
    sUnsound = textLayerSound(lPages)
    if sUnsound: return "", ["the PDF's text layer is unsound: " + sUnsound + "; a reading of its page pictures (OCR) is needed, as HomerScribe does"]
    nBody = oSizes.most_common(1)[0][0]
    lSmaller = sorted([s for s in oSizes if s < nBody], key=lambda s: -oSizes[s])
    nNote = max([s for s in lSmaller if s >= nBody * 0.8] or [nBody - 1])
    # Note numbers: a size well below the body whose words are nearly all one- to three-digit numbers. A Federal
    # Register page also sets chart labels and a printer's stamp in tiny type, so smallness alone proves nothing.
    oDigits, oAll = collections.Counter(), collections.Counter()
    for oPage, lWords in lPages:
        for d in lWords:
            if not d["size"]: continue
            oAll[round(d["size"])] += 1
            if re.fullmatch(r"\d{1,3}", d["text"]): oDigits[round(d["size"])] += 1
    lMarkerSizes = [n for n in oAll if n < nBody * 0.75 and oAll[n] >= 5 and oDigits[n] >= 0.85 * oAll[n]]
    nMarker = max(lMarkerSizes, key=lambda n: oDigits[n]) if lMarkerSizes else 0
    # Running heads and printer's stamps: a line whose letters, digits set aside, repeat on most pages.
    oRepeats = collections.Counter()
    for oPage, lWords in lPages:
        setSeen = set()
        for d in lWords:
            if d["top"] < oPage.height * 0.08 or d["top"] > oPage.height * 0.92: setSeen.add(round(d["top"]))
        for nTop in setSeen:
            sKey = re.sub(r"[\d\W]+", "", " ".join(x["text"] for x in lWords if abs(x["top"] - nTop) < 2)).lower()
            if sKey: oRepeats[sKey] += 1
    # Three pages are enough: a printing that holds two documents has a running head for each, and the shorter
    # document's head appears on only a few pages.
    setRunning = {k for k, n in oRepeats.items() if n >= 3}
    nTitle = max(oSizes)
    lHeadingSizes = sorted([s for s in oSizes if nBody < s < nTitle], reverse=True)
    lObserved.append("type sizes: body %s, notes %s, note numbers %s, headings %s, title %s" % (nBody, nNote, nMarker, lHeadingSizes, nTitle))
    lBlocks, dNotes, sNote, iLeft, sHeadingStyle = [], {}, "", 72, ""
    for oPage, lWords in lPages:
        lWords = dropRunning(lWords, oPage, setRunning)
        lColumns = pageColumns(lWords, oPage)
        lPlain = sorted([d for d in lWords if not (nMarker and round(d["size"]) == nMarker)], key=lambda d: (columnOf(d, lColumns), d["top"], d["x0"]))
        lLines = []
        for d in lPlain:
            if lLines and not d.get("rows") and not lLines[-1][0].get("rows") and columnOf(d, lColumns) == columnOf(lLines[-1][0], lColumns) and abs(d["top"] - lLines[-1][0]["top"]) <= 3: lLines[-1].append(d)
            else: lLines.append([d])
        for d in [d for d in lWords if nMarker and round(d["size"]) == nMarker]:
            nMiddle = (d["top"] + d["bottom"]) / 2
            lNear = sorted([l for l in lLines if columnOf(l[0], lColumns) == columnOf(d, lColumns)] or lLines, key=lambda l: abs((l[0]["top"] + l[0]["bottom"]) / 2 - nMiddle))
            if lNear and abs((lNear[0][0]["top"] + lNear[0][0]["bottom"]) / 2 - nMiddle) <= 9: lNear[0].append(d)
            else: lLines.append([d])
        lLines.sort(key=lambda l: (columnOf(l[0], lColumns), min(x["top"] for x in l)))
        iLeft = min([l[0]["x0"] for l in lLines] or [72])
        bInNotes, nPrevBottom = False, None
        for lLine in lLines:
            lLine.sort(key=lambda d: d["x0"])
            if lLine[0].get("rows"):
                lBlocks.append(("t", 0, renderTable(lLine[0]["rows"])))
                continue
            sText = " ".join(d["text"] for d in lLine).strip()
            lSizes = [round(d["size"]) for d in lLine if round(d["size"]) != nMarker]
            nSize = max(lSizes) if lSizes else nMarker
            bBold = all("Bold" in d["fontname"] for d in lLine if round(d["size"]) != nMarker)
            bItalic = all("Italic" in d["fontname"] or "Oblique" in d["fontname"] for d in lLine if round(d["size"]) != nMarker)
            sStyle = ("b" if bBold else "") + ("i" if bItalic else "")
            if re.fullmatch(r"\d{1,3}", sText) and (lLine[0]["top"] > oPage.height * 0.88 or lLine[0]["top"] < oPage.height * 0.08): continue
            if re.search(r"\.{5,}", sText) or sText.lower() == "table of contents" or nSize >= nTitle: continue
            if nMarker and len(lLine) == 1 and round(lLine[0]["size"]) == nMarker and re.fullmatch(r"\d{1,3}", lLine[0]["text"]):
                bInNotes, sNote = True, lLine[0]["text"]
                dNotes[sNote] = ""
                continue
            if nMarker and round(lLine[0]["size"]) == nMarker and len(lLine) > 1 and nSize <= nNote:
                bInNotes, sNote = True, lLine[0]["text"]
                dNotes[sNote] = " ".join(d["text"] for d in lLine[1:])
                continue
            if nSize <= nNote and sNote and (bInNotes or lLine[0]["top"] > oPage.height * 0.55):
                bInNotes = True
                dNotes[sNote] = joinText(dNotes[sNote], sText)
                continue
            lParts = []
            for d in lLine:
                if nMarker and round(d["size"]) == nMarker and re.fullmatch(r"\d{1,3}", d["text"]): lParts.append("[^" + d["text"] + "]")
                else: lParts.append((" " if lParts else "") + d["text"])
            sLine = "".join(lParts).strip()
            iLevel = 0
            if nSize in lHeadingSizes: iLevel = 2 + lHeadingSizes.index(nSize)
            elif nSize <= nBody and bBold and len(sText.split()) <= 16 and re.match(r"^(PART \d+|Appendix [A-Z]\b|§\s*\d)", sText): iLevel = 2 if not sText.startswith("§") else 3
            elif nSize <= nBody and bBold and len(sText.split()) <= 12 and re.match(r"^[EC]?\d{3}(\.\d+)*\s+[A-Z]", sText) and not re.search(r"[.;:,]$", sText):
                iLevel = min(6, 4 + re.match(r"^[EC]?\d{3}((\.\d+)*)", sText).group(1).count("."))
            elif nSize <= nBody and bBold and len(sText.split()) <= 12 and re.match(r"^\d{3} CHAPTER \d+|^CHAPTER \d+", sText): iLevel = 3
            elif nSize == nBody and len(sText.split()) <= 12 and re.match(r"^(\d+|[A-Z]|[IVX]+)\.\s", sText) and not re.search(r"[.;:,]$", sText) and (bBold or bItalic or (len(lColumns) <= 1 and lLine[0]["x0"] <= iLeft + 110)):
                # Same size as the body: the numbering gives the rank -- I. above A. above 1. -- below any larger heading.
                sMark = sText.split(".")[0]
                iRank = 0 if re.fullmatch(r"[IVX]+", sMark) and (bBold or len(sMark) > 1) else (1 if re.fullmatch(r"[A-Z]", sMark) else 2)
                iLevel = min(6, 2 + len(lHeadingSizes) + iRank)
            nGap = (lLine[0]["top"] - nPrevBottom) if nPrevBottom is not None else 99
            nPrevBottom = lLine[0]["bottom"]
            bNumbered = bool(re.match(r"^(\d+|[A-Z]|[IVX]+)\.\s", sText))
            if iLevel:
                if lBlocks and lBlocks[-1][0] == "h" and lBlocks[-1][1] == iLevel and nGap < nSize * 0.8 and not bNumbered: lBlocks[-1] = ("h", iLevel, lBlocks[-1][2] + " " + sLine)
                else: lBlocks.append(("h", iLevel, sLine))
                sHeadingStyle = sStyle
                continue
            if lBlocks and lBlocks[-1][0] == "h" and nGap < nSize * 0.5 and len(sText.split()) <= 12 and not re.search(r"[.;:,]$", lBlocks[-1][2]) and sStyle == sHeadingStyle:
                lBlocks[-1] = ("h", lBlocks[-1][1], lBlocks[-1][2] + " " + sLine)
                continue
            nColumnLeft = lColumns[columnOf(lLine[0], lColumns)][0] if lColumns else iLeft
            # A web address cut at the end of a line or column always continues on the next line.
            bOpenAddress = bool(lBlocks) and lBlocks[-1][0] == "p" and bool(re.search(r"https?://\S*$", lBlocks[-1][2])) and not re.search(r"[.;,)]$", lBlocks[-1][2])
            if not bOpenAddress and (not lBlocks or lBlocks[-1][0] == "h" or lLine[0]["x0"] > nColumnLeft + max(6, nBody * 0.6) or (0 <= nGap and nGap > nBody * 1.2)): lBlocks.append(("p", 0, sLine))
            else: lBlocks[-1] = ("p", 0, joinText(lBlocks[-1][2], sLine))
    lBlocks = federalRegisterOwn(lBlocks, lObserved)
    lBlocks = contentsListsOut(lBlocks)
    iPlain = 0
    lMended = []
    for sKind, iLevel, sText in lBlocks:
        if sKind == "p":
            sText, iCount = mendedAddresses(sText)
            iPlain += iCount
        lMended.append((sKind, iLevel, sText))
    if iPlain: lObserved.append("%d web address%s whose rest the printing set elsewhere left as plain text" % (iPlain, "" if iPlain == 1 else "es"))
    lOut = closedHeadingGaps([("#" * iLevel + " " + smallCapitals(sText)) if sKind == "h" else (sText if sKind == "t" else proseLine(smallCapitals(sText))) for sKind, iLevel, sText in lMended])
    lOut.append("")
    lOut += ["[^" + sNumber + "]: " + dNotes[sNumber].strip() for sNumber in sorted((k for k in dNotes if k.isdigit()), key=int)]
    lRefs = set(re.findall(r"\[\^(\d+)\](?!:)", "\n".join(lOut)))
    lObserved.append("%d headings, %d paragraphs, %d notes, %d referenced in the text" % (sum(1 for b in lBlocks if b[0] == "h"), sum(1 for b in lBlocks if b[0] == "p"), len(dNotes), len(lRefs & set(dNotes))))
    return "\n\n".join(lOut) + "\n", lObserved


def importSource(dBook):
    """Makes books\\<root>\\<root>.md from the book's source when there is no manuscript yet: a Word file or an EPUB
    through Pandoc, pictures into images\\; a PDF through pdfToMarkdown. A book not by the project's own author (the author setting) is a
    public-domain document; it opens with an About This Edition note saying so, and names no AI."""
    sBookDir = os.path.join(sProject, "books", dBook["root"])
    sSource = bookSource(dBook)
    if not sSource and dBook.get("sourceUrl"):
        # The catalog may name where the book's text is published as a web page; the build fetches it itself.
        sTarget = os.path.join(sBookDir, dBook["root"] + ".htm")
        sProblem = download(dBook["sourceUrl"], sTarget)
        if sProblem: return "could not fetch " + dBook["sourceUrl"] + ": " + sProblem
        sSource = sTarget
    if not sSource: return "no manuscript and no Word, EPUB, web page or PDF file"
    sExt = os.path.splitext(sSource)[1].lower()
    if sExt == ".pdf":
        oReader = ensurePdfReader()
        if not oReader: return "pdfplumber could not be installed to read " + os.path.basename(sSource)
        sBody, lObserved = pdfToMarkdown(sSource, oReader)
        for sLine in lObserved: log(dBook["root"] + ": " + sLine)
        if not sBody.strip(): return os.path.basename(sSource) + " holds no text"
    else:
        sOut = os.path.join(sBookDir, "temp-import.md")
        iCode, sText = run([dTools["pandoc"], sSource, "-f", {"htm": "html"}.get(sExt[1:], sExt[1:]), "-t", "markdown-simple_tables-multiline_tables-grid_tables+pipe_tables", "--wrap=none", "--extract-media=.", "-o", sOut], sCwd=sBookDir)
        if iCode != 0: return "Pandoc could not read " + os.path.basename(sSource)
        sMedia = os.path.join(sBookDir, "media")
        if os.path.isdir(sMedia):
            os.makedirs(os.path.join(sBookDir, "images"), exist_ok=True)
            for sDir, lDirs, lFiles in os.walk(sMedia):
                for sName in lFiles:
                    sTarget = os.path.join(sBookDir, "images", sName)
                    if not os.path.exists(sTarget): shutil.move(os.path.join(sDir, sName), sTarget)
            shutil.rmtree(sMedia, ignore_errors=True)
        sBody = open(sOut, encoding="utf-8").read()
        sBody = re.sub(r"\]\((?:\./)?media/(?:[^)]*/)?([^/)]+)\)", r"](images/\1)", sBody)
        os.remove(sOut)
    lYaml = ["---", "title: " + json.dumps(dBook["title"], ensure_ascii=False)]
    if dBook["subtitle"]: lYaml.append("subtitle: " + json.dumps(dBook["subtitle"], ensure_ascii=False))
    lYaml += ["author: " + json.dumps(dBook["author"], ensure_ascii=False), "lang: en-US", "---", ""]
    if not ownBook(dBook):
        sBody = "## About This Edition\n\nThis book reproduces, without change to its text, a work of the " + dBook["author"] + ", which as a work of the United States government is in the public domain. This Kindle edition adds a linked table of contents" + (" and linked notes" if "[^" in sBody else "") + ", and real headings for navigation with a screen reader.\n\n## Table of Contents\n\n[TOC]\n\n" + sBody
    writeText(os.path.join(sBookDir, dBook["root"] + ".md"), "\n".join(lYaml) + "\n" + sBody)
    say(dBook["title"] + ": imported from " + os.path.basename(sSource) + " as books\\" + dBook["root"] + "\\" + dBook["root"] + ".md.")
    return ""


# ---------------------------------------------------------------- manuscript parsing

def splitFrontMatter(sText):
    """Returns ({key: value} from a simple YAML block at the top, the text after it)."""
    oMatch = re.match(r"^\ufeff?---[ \t]*\r?\n(.*?)\r?\n(?:---|\.\.\.)[ \t]*\r?\n", sText, re.S)
    if not oMatch: return {}, sText.lstrip("\ufeff")
    d = {}
    for sLine in oMatch.group(1).splitlines():
        oKey = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", sLine)
        if oKey: d[oKey.group(1)] = oKey.group(2).strip().strip("\"'")
    return d, sText[oMatch.end():]


def outsideCode(sBody):
    """The manuscript with fenced code blocks blanked, so headings and pictures are only found in prose."""
    return re.sub(r"(?ms)^(```|~~~).*?^\1[ \t]*$", "", sBody)


def headingList(sBody):
    """(level, text) for every ATX heading outside code blocks."""
    lOut = []
    for oMatch in re.finditer(r"(?m)^(#{1,6})[ \t]+(.+?)[ \t#]*(\{[^}]*\})?[ \t]*\r?$", outsideCode(sBody)):
        lOut.append((len(oMatch.group(1)), oMatch.group(2).strip()))
    return lOut


c_sImagePattern = r"!\[(?P<alt>(?:[^\[\]]|\[[^\]]*\])*)\]\((?P<url><[^>]+>|[^)\s]+)(?P<title>\s+\"[^\"]*\")?\)(?P<attr>\{[^}]*\})?"


def imageList(sBody):
    """Every picture in the manuscript: its match, text alternative and address."""
    lOut = []
    for oMatch in re.finditer(c_sImagePattern, sBody):
        sAlt = oMatch.group("alt").strip()
        oAttrAlt = re.search(r"alt=\"([^\"]*)\"", oMatch.group("attr") or "")
        if not sAlt and oAttrAlt: sAlt = oAttrAlt.group(1).strip()
        lOut.append({"match": oMatch, "alt": sAlt, "url": oMatch.group("url").strip("<>")})
    return lOut


def cacheName(sUrl):
    """The images-folder file name for a web address, the same rule the Strange Truths Word build used: decoded, any NNNpx- thumbnail prefix dropped, and each run of characters other than letters, digits, dot, hyphen and underscore made one underscore."""
    sBase = urllib.parse.unquote(sUrl.split("?")[0].split("#")[0].rstrip("/").split("/")[-1])
    sBase = re.sub(r"^\d+px-", "", sBase)
    return re.sub(r"[^\w.\-]+", "_", sBase)


def docxPictures(sDocx):
    """{stored file name: bytes} for the pictures in a Word file, using the file name the Word build stored as each picture's description, plus an ordered list of all pictures for books where no names were stored."""
    dNamed, lOrdered = {}, []
    try:
        oZip = zipfile.ZipFile(sDocx)
        sDoc = oZip.read("word/document.xml").decode("utf-8")
        sRels = oZip.read("word/_rels/document.xml.rels").decode("utf-8")
    except Exception as oError:
        log("could not open " + sDocx + ": " + str(oError))
        return dNamed, lOrdered
    dRels = {}
    for sRel in re.findall(r"<Relationship\b[^>]*>", sRels):
        oId, oTarget = re.search(r"\bId=\"([^\"]+)\"", sRel), re.search(r"\bTarget=\"([^\"]+)\"", sRel)
        if oId and oTarget: dRels[oId.group(1)] = oTarget.group(1)
    for sPic in re.findall(r"<pic:pic\b.*?</pic:pic>", sDoc, re.S):
        oDescr = re.search(r"<pic:cNvPr\b[^>]*\bdescr=\"([^\"]*)\"", sPic)
        oEmbed = re.search(r"r:embed=\"([^\"]+)\"", sPic)
        if not oEmbed or oEmbed.group(1) not in dRels: continue
        sMember = "word/" + dRels[oEmbed.group(1)].lstrip("/").replace("word/", "", 1)
        try:
            binData = oZip.read(sMember)
        except KeyError:
            continue
        sExt = os.path.splitext(sMember)[1]
        lOrdered.append((binData, sExt))
        if oDescr and oDescr.group(1): dNamed[html.unescape(os.path.basename(oDescr.group(1).replace("\\", "/")))] = (binData, sExt)
    log("Word file " + os.path.basename(sDocx) + ": " + plural(len(lOrdered), "picture") + ", " + str(len(dNamed)) + " named")
    return dNamed, lOrdered


def lookupNamed(dNamed, sName):
    """A picture from a Word file by stored name, allowing a different case, a different extension, or an outer extension the Word build dropped."""
    if sName in dNamed: return dNamed[sName]
    sLower, sStem = sName.lower(), os.path.splitext(sName)[0].lower()
    for sKey, oValue in dNamed.items():
        if sKey.lower() in (sLower, sStem) or os.path.splitext(sKey)[0].lower() == sStem: return oValue
    # Then tolerantly: web encoding, a query string, the extension and punctuation set aside on both sides, since the
    # Word build stored the name a web address gave and the build makes a file name of it.
    def plain(s): return re.sub(r"[^a-z0-9]", "", os.path.splitext(urllib.parse.unquote(s).split("?")[0])[0].lower())
    sPlain = plain(sName)
    lHits = [oValue for sKey, oValue in dNamed.items() if sPlain and plain(sKey) == sPlain]
    return lHits[0] if len(lHits) == 1 else None


def findInFolders(lFolders, sName):
    """A picture by name in any of the given folders, case-insensitively, with the double-extension fallback."""
    lNames = [sName]
    oDouble = re.match(r"^(.*\.(?:" + "|".join(c_lImageExtensions) + r"))\.(?:" + "|".join(c_lImageExtensions) + r")$", sName, re.I)
    if oDouble: lNames.append(oDouble.group(1))
    for sDir in lFolders:
        if not os.path.isdir(sDir): continue
        dLower = {s.lower(): s for s in os.listdir(sDir)}
        for sTry in lNames:
            if sTry.lower() in dLower: return os.path.join(sDir, dLower[sTry.lower()])
    return ""


def resolvePictures(dBook, sBody, sWork, dFound):
    """Points every picture in a working copy of the manuscript at a local file, finding or fetching each one; returns (body, picture records, errors)."""
    sBookDir = os.path.join(sProject, "books", dBook["root"])
    sImages = os.path.join(sBookDir, "images")
    lFolders = [sImages] + inixList(dFound.get("imageFolders", ""))
    lPictures = imageList(sBody)
    dNamed, lOrdered, bDocxRead, dUsedDocx = {}, [], False, {}
    lRecords, lErrors, dDone = [], [], {}
    lDocx = sorted(glob.glob(os.path.join(sBookDir, "*.docx")), key=os.path.getmtime)
    lRemote = [d for d in lPictures if re.match(r"^https?://", d["url"], re.I)]
    for iIndex, dPicture in enumerate(lPictures):
        sUrl = dPicture["url"]
        if sUrl in dDone:
            lRecords.append(dict(dDone[sUrl], alt=dPicture["alt"], repeat=True))
            continue
        bRemote = bool(re.match(r"^https?://", sUrl, re.I))
        sName = cacheName(sUrl) if bRemote else os.path.basename(urllib.parse.unquote(sUrl))
        sPath, sSource = "", ""
        if not bRemote and os.path.isfile(os.path.join(sBookDir, urllib.parse.unquote(sUrl))):
            sPath, sSource = os.path.join(sBookDir, urllib.parse.unquote(sUrl)), "manuscript folder"
        if not sPath:
            sPath = findInFolders(lFolders, sName)
            if sPath: sSource = "images folder" if os.path.dirname(sPath) == sImages else "images folder found beside an earlier copy"
        if not sPath and lDocx:
            if not bDocxRead:
                dNamed, lOrdered = docxPictures(lDocx[-1])
                bDocxRead = True
            oHit = lookupNamed(dNamed, sName)
            lDistinct = list(dict.fromkeys(d["url"] for d in lRemote))
            if not oHit and not dNamed and bRemote and len(lOrdered) == len(lDistinct): oHit = lOrdered[lDistinct.index(sUrl)]
            if oHit:
                dUsedDocx[sUrl] = next((i for i, o in enumerate(lOrdered) if o[0] is oHit[0] or o[0] == oHit[0]), -1)
                sTargetName = sName if os.path.splitext(sName)[1].lower() == oHit[1].lower() else os.path.splitext(sName)[0] + oHit[1]
                sPath = os.path.join(sImages, sTargetName)
                os.makedirs(sImages, exist_ok=True)
                with open(sPath, "wb") as f: f.write(oHit[0])
                sSource = "Word file " + os.path.basename(lDocx[-1])
        if not sPath and bRemote:
            sTarget = os.path.join(sImages, sName)
            if not download(sUrl, sTarget): sPath, sSource = sTarget, "downloaded"
        if not sPath:
            lErrors.append("Picture not found anywhere: " + sUrl)
            dRecord = {"url": sUrl, "name": sName, "source": "", "file": "", "alt": dPicture["alt"]}
        else:
            if sSource.startswith("images folder found"):
                os.makedirs(sImages, exist_ok=True)
                shutil.copy2(sPath, os.path.join(sImages, os.path.basename(sPath)))
                sPath = os.path.join(sImages, os.path.basename(sPath))
            dRecord = {"url": sUrl, "name": os.path.basename(sPath), "source": sSource, "file": sPath, "alt": dPicture["alt"]}
            dRecord.update(preparePicture(sPath, sWork, len(dDone)))
        log(dBook["root"] + ": picture " + str(iIndex + 1) + " " + sName + " <- " + (sSource or "NOT FOUND"))
        dDone[sUrl] = dRecord
        lRecords.append(dRecord)
    # A second pass for pictures still missing when the Word file has pictures to spare: each run of missing pictures
    # between two neighbours matched in the Word file takes the unused Word pictures between those neighbours, when
    # the numbers agree, since the Word file holds the pictures in the manuscript's order.
    if lOrdered:
        lOrder = list(dict.fromkeys(d["url"] for d in lPictures))
        iAt = 0
        while iAt < len(lOrder):
            if dDone.get(lOrder[iAt], {}).get("file") or lOrder[iAt] not in dDone:
                iAt += 1
                continue
            iEnd = iAt
            while iEnd < len(lOrder) and lOrder[iEnd] in dDone and not dDone[lOrder[iEnd]].get("file"): iEnd += 1
            iLow = max([dUsedDocx[u] for u in lOrder[:iAt] if u in dUsedDocx] or [-1])
            iHigh = min([dUsedDocx[u] for u in lOrder[iEnd:] if u in dUsedDocx] or [len(lOrdered)])
            setUsed = set(dUsedDocx.values())
            lFree = [i for i in range(iLow + 1, iHigh) if i not in setUsed]
            if len(lFree) == iEnd - iAt:
                for sUrl, iPick in zip(lOrder[iAt:iEnd], lFree):
                    oHit, dOld = lOrdered[iPick], dDone[sUrl]
                    sName = dOld["name"]
                    sTargetName = sName if os.path.splitext(sName)[1].lower() == oHit[1].lower() else os.path.splitext(sName)[0] + oHit[1]
                    sPath = os.path.join(sImages, sTargetName)
                    os.makedirs(sImages, exist_ok=True)
                    with open(sPath, "wb") as f: f.write(oHit[0])
                    dRecord = {"url": sUrl, "name": os.path.basename(sPath), "source": "Word file " + os.path.basename(lDocx[-1]) + ", by position", "file": sPath, "alt": dOld["alt"]}
                    dRecord.update(preparePicture(sPath, sWork, len(dDone) + iPick))
                    dDone[sUrl] = dRecord
                    dUsedDocx[sUrl] = iPick
                    lErrors = [e for e in lErrors if not e.endswith(" " + sUrl)]
                    log(dBook["root"] + ": picture " + sName + " <- Word file, by position (picture " + str(iPick + 1) + " of " + str(len(lOrdered)) + ")")
                lRecords = [dDone.get(r["url"], r) if not r.get("file") else r for r in lRecords]
            iAt = iEnd
    def replace(oMatch):
        sUrl = oMatch.group("url").strip("<>")
        dRecord = dDone.get(sUrl, {})
        if not dRecord.get("epubName"):
            # A picture found nowhere is left out of the EPUB, its text alternative standing in its place, so the book
            # stays valid; the manuscript keeps the reference, so the picture returns when its source is found.
            return ("*[" + dRecord["alt"] + "]*") if dRecord.get("alt") else ""
        return oMatch.group(0).replace(oMatch.group("url"), "media/" + dRecord["epubName"], 1)
    return re.sub(c_sImagePattern, replace, sBody), lRecords, lErrors


def preparePicture(sPath, sWork, iNumber):
    """Copies a picture into the working folder for the EPUB, converted to a type every reader shows and scaled down if large; the original is untouched."""
    sExt = os.path.splitext(sPath)[1].lower()
    sStem = "picture" + str(iNumber + 1).zfill(3)
    sMedia = os.path.join(sWork, "media")
    os.makedirs(sMedia, exist_ok=True)
    dOut = {"bytesIn": os.path.getsize(sPath), "note": ""}
    if sExt == ".svg":
        shutil.copy2(sPath, os.path.join(sMedia, sStem + ".svg"))
        dOut.update(epubName=sStem + ".svg", bytesOut=dOut["bytesIn"], note="SVG kept as is; Kindle may show it smaller or not at all")
        return dOut
    try:
        oPicture = oImage.open(sPath)
        sFormat = (oPicture.format or "").upper()
        dOut["size"] = oPicture.size
        bAnimated = getattr(oPicture, "is_animated", False)
        iLimit = int(dSettings["imageMaxEdge"])
        bLarge = max(oPicture.size) > iLimit
        bHeavy = dOut["bytesIn"] > int(dSettings["imageMaxBytes"])
        if bAnimated: oPicture.seek(0)
        if sFormat in ("JPEG", "PNG", "GIF") and not bLarge and not bHeavy and not bAnimated:
            sName = sStem + {"JPEG": ".jpg", "PNG": ".png", "GIF": ".gif"}[sFormat]
            shutil.copy2(sPath, os.path.join(sMedia, sName))
        else:
            bAlpha = oPicture.mode in ("RGBA", "LA", "P") and "transparency" in oPicture.info or oPicture.mode in ("RGBA", "LA")
            if bLarge: oPicture.thumbnail((iLimit, iLimit))
            if bAlpha:
                sName = sStem + ".png"
                oPicture.convert("RGBA").save(os.path.join(sMedia, sName), "PNG", optimize=True)
            else:
                sName = sStem + ".jpg"
                oPicture.convert("RGB").save(os.path.join(sMedia, sName), "JPEG", quality=int(dSettings["jpegQuality"]), optimize=True, progressive=True)
            lNotes = (["scaled from " + str(max(dOut["size"])) + " pixels"] if bLarge else []) + (["first frame kept from an animation, since Kindle does not animate pictures and animation can flash"] if bAnimated else []) + (["converted from " + sFormat] if sFormat not in ("JPEG", "PNG") else []) + (["compressed from " + format(dOut["bytesIn"] // 1024, ",") + " KB"] if bHeavy else [])
            dOut["note"] = "; ".join(lNotes)
            dOut["size"] = oPicture.size
        dOut.update(epubName=sName, bytesOut=os.path.getsize(os.path.join(sMedia, sName)))
    except Exception as oError:
        log("could not read picture " + sPath + ": " + str(oError))
        dOut.update(epubName="", bytesOut=0, note="could not be read as a picture: " + str(oError))
    return dOut


# ---------------------------------------------------------------- EPUB

def bookMetadata(dBook, dYaml, dKdp, bPictures, iLevel):
    """The metadata file Pandoc gets: KDP's title, subtitle and author; description and keywords from the KDP metadata file; the manuscript's language, rights and date."""
    dSection = dKdp.get("proposed", {})
    dLive = dKdp.get("kdp", {})
    sDescription = dSection.get("description") or dLive.get("description", "")
    sDescription = re.sub(r"\*\*(.+?)\*\*", r"\1", sDescription).strip()
    lKeywords = inixList(dSection.get("keywords") or dLive.get("keywords", ""))
    sAuthor = re.sub(r"\s+", " ", dBook["author"])
    sYear = ""
    for sKey in ("date",):
        sValue = dYaml.get(sKey, "")
        oYear = re.search(r"\b(19|20)\d\d\b", sValue)
        if oYear: sYear = oYear.group(0)
    sRights = dYaml.get("rights", "") or ("Copyright \u00a9 " + (sYear or datetime.date.today().strftime("%Y")) + " " + sAuthor + ". All rights reserved." if ownBook(dBook) else "")
    sId = "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, "https://www.amazon.com/dp/" + (dBook["asin"] or dBook["root"])))
    dMeta = {"title": dBook["title"], "author": [sAuthor], "lang": dYaml.get("lang") or "en-US", "identifier": sId, "toc-title": "Contents"}
    if dBook["subtitle"]: dMeta["subtitle"] = dBook["subtitle"]
    if sRights: dMeta["rights"] = sRights
    if sYear: dMeta["date"] = sYear
    if sDescription: dMeta["description"] = sDescription
    if lKeywords: dMeta["subject"] = lKeywords
    if dBook["series"]: dMeta["belongs-to-collection"] = dBook["series"]
    return dMeta


def accessibilityMetadata(bPictures, bAllDescribed=True):
    """The schema.org accessibility metadata a MyBooks EPUB declares: only what the build itself can stand behind
    (8 October 2026, from an audit by another AI). No conformance claim and no certification are written: those need a
    person's review, which the build cannot make, and were declared before any check had run. The pictures are said to
    have text alternatives only when every picture's alternative text is filled in."""
    bDescribed = bPictures and bAllDescribed
    lModes = ["textual"] + (["visual"] if bPictures else [])
    lFeatures = ["structuralNavigation", "tableOfContents", "readingOrder", "displayTransformability"] + (["alternativeText"] if bDescribed else [])
    sSummary = "This publication has a heading for every section, a linked table of contents, and text that readers can resize and read aloud." + ((" Every picture has a text alternative." if bDescribed else " Some pictures are not yet described in text.") if bPictures else "")
    lMeta = ['<meta property="schema:accessMode">' + s + "</meta>" for s in lModes]
    lMeta += ['<meta property="schema:accessModeSufficient">' + ("textual" if bDescribed or not bPictures else "textual,visual") + "</meta>"]
    lMeta += ['<meta property="schema:accessibilityFeature">' + s + "</meta>" for s in lFeatures]
    lMeta += ['<meta property="schema:accessibilityHazard">none</meta>', '<meta property="schema:accessibilitySummary">' + html.escape(sSummary, quote=False) + "</meta>"]
    return lMeta


# The KDP tables of contents and their check live in the kit's kdpEpub.py (1.61.0), shared with Blind Vibe Coding's build.

def sourceTime(sManuscript):
    """The latest change to a book's sources -- its manuscript and the images folder beside it -- as a UTC datetime."""
    lTimes = [os.path.getmtime(sManuscript)] if os.path.exists(sManuscript) else []
    sPictures = os.path.join(os.path.dirname(sManuscript), "images")
    if os.path.isdir(sPictures): lTimes += [os.path.getmtime(os.path.join(d, f)) for d, _, lf in os.walk(sPictures) for f in lf]
    return datetime.datetime.fromtimestamp(max(lTimes) if lTimes else 0, datetime.timezone.utc)


def writeStableEpub(sEpub, lNames, dData, oWhen):
    """Writes the EPUB so that the same sources always make the same file, byte for byte: the package's modified date is
    the sources' last change, not the build's time, and every entry in the zip carries that same time.
    WHY (8 October 2026): every build stamped its own time into the EPUB, so the file changed though the book did not,
    and kdpUpdate, which sends a book only when KDP lacks that exact file, would have sent every book on every run, each
    upload starting another KDP review that locks the title."""
    sModified = oWhen.strftime("%Y-%m-%dT%H:%M:%SZ")
    tWhen = tuple(max(oWhen.timetuple()[:6], (1980, 1, 1, 0, 0, 0)))
    for sName in lNames:
        if sName.lower().endswith(".opf"):
            sOpf = dData[sName].decode("utf-8")
            sOpf = re.sub(r'(<meta property="dcterms:modified">)[^<]*(</meta>)', lambda m: m.group(1) + sModified + m.group(2), sOpf)
            dData[sName] = sOpf.encode("utf-8")
    sTemp = sEpub + ".tmp"
    with zipfile.ZipFile(sTemp, "w") as oOut:
        oInfo = zipfile.ZipInfo("mimetype", date_time=tWhen)
        oInfo.compress_type = zipfile.ZIP_STORED
        oOut.writestr(oInfo, b"application/epub+zip")
        for sName in lNames:
            if sName == "mimetype": continue
            oInfo = zipfile.ZipInfo(sName, date_time=tWhen)
            oInfo.compress_type = zipfile.ZIP_DEFLATED
            oInfo.external_attr = 0o644 << 16
            oOut.writestr(oInfo, dData[sName])
    os.replace(sTemp, sEpub)


def finishPackage(sEpub, bPictures, sSubtitle, sManuscript=""):
    """Adds the subtitle and the accessibility metadata to the package file, and writes the EPUB again with mimetype first and uncompressed, as the EPUB rules require."""
    sTemp = sEpub + ".tmp"
    with zipfile.ZipFile(sEpub) as oIn:
        lNames = oIn.namelist()
        dData = {s: oIn.read(s) for s in lNames}
    lOpf = [s for s in lNames if s.lower().endswith(".opf")]
    if lOpf:
        sOpf = dData[lOpf[0]].decode("utf-8")
        sOpf = re.sub(r"\s*<meta property=\"(schema:access[^\"]*|dcterms:conformsTo|a11y:[^\"]*)\">[^<]*</meta>", "", sOpf)
        bAllDescribed = not any(re.search(r'<img\b[^>]*\balt=""', dData[n].decode("utf-8", "replace")) for n in lNames if n.endswith(".xhtml"))
        lAdd = accessibilityMetadata(bPictures, bAllDescribed)
        oTitle = re.search(r"<dc:title id=\"([^\"]+)\">", sOpf)
        if sSubtitle and oTitle and "title-type" not in sOpf:
            lAdd = ['<meta refines="#' + oTitle.group(1) + '" property="title-type">main</meta>', '<dc:title id="epub-subtitle-1">' + html.escape(sSubtitle, quote=False) + "</dc:title>", '<meta refines="#epub-subtitle-1" property="title-type">subtitle</meta>'] + lAdd
        sOpf = re.sub(r"\s*</metadata>", "\n    " + "\n    ".join(lAdd) + "\n  </metadata>", sOpf, count=1)
        dData[lOpf[0]] = sOpf.encode("utf-8")
        for sLine in kdpEpub.kdpNavigation(dData, lNames): log(os.path.basename(sEpub) + ": " + sLine)
    writeStableEpub(sEpub, lNames, dData, sourceTime(sManuscript))
    return True


def externalManuscript(dBook):
    """The manuscript of a book whose own project builds it: <project>\\<root>.md."""
    return os.path.join(dBook["externalProject"], dBook["root"] + ".md")


def buildExternal(dBook, dAudit):
    """A book built by its own project rather than here (catalog keys externalProject, externalBuild, externalEpub): its own
    build runs in its own folder, so its manuscript, bibliography, cover and styles stay where the author edits them; the EPUB
    it makes is copied to results\\<root>.epub and given KDP's tables of contents and guide items, then audited like every
    other book. Returns the EPUB's path, or "" with the problem in the audit."""
    sProject2, sRoot = dBook["externalProject"], dBook["root"]
    sManuscript = externalManuscript(dBook)
    if not os.path.isdir(sProject2):
        dAudit["errors"].append("Its project folder, " + sProject2 + ", is not on this computer.")
        return ""
    if not os.path.exists(sManuscript):
        dAudit["errors"].append("Its manuscript, " + sManuscript + ", is not there.")
        return ""
    dYaml, sBody = splitFrontMatter(open(sManuscript, encoding="utf-8-sig").read())
    dAudit["yaml"], dAudit["body"] = dYaml, sBody
    sBuild = os.path.join(sProject2, dBook["externalBuild"] or "build.py")
    sMade = os.path.join(sProject2, dBook["externalEpub"] or os.path.join("exec", sRoot + ".epub"))
    if os.path.exists(sBuild):
        say(dBook["title"] + ": building with its own " + os.path.basename(sBuild) + " in " + sProject2 + ".")
        lCommand = [sys.executable, sBuild] if sBuild.lower().endswith(".py") else ["cmd", "/c", sBuild]
        iCode, sOut = run(lCommand, sCwd=sProject2)
        if iCode != 0:
            dAudit["errors"].append("Its own build, " + sBuild + ", ended with exit code " + str(iCode) + "; see the log.")
            return ""
    else:
        dAudit["warnings"].append("No build script at " + sBuild + ", so its existing EPUB was used as it is.")
    if not os.path.exists(sMade):
        dAudit["errors"].append("Its own build made no EPUB at " + sMade + ".")
        return ""
    if os.path.getmtime(sMade) < os.path.getmtime(sManuscript) and os.path.getmtime(sManuscript) <= time.time() + 300:
        dAudit["errors"].append("Its EPUB, " + sMade + ", is older than its manuscript, so it does not hold the latest text.")
    sEpub = os.path.join(sProject, "results", sRoot + ".epub")
    os.makedirs(os.path.dirname(sEpub), exist_ok=True)
    shutil.copyfile(sMade, sEpub)
    with zipfile.ZipFile(sEpub) as oIn:
        lNames = oIn.namelist()
        dData = {sName: oIn.read(sName) for sName in lNames}
    for sLine in kdpEpub.kdpNavigation(dData, lNames): log(sRoot + ".epub: " + sLine)
    # The cover is the one the book's own build placed, named by the package's cover-image item.
    sOpfText = next((dData[sName].decode("utf-8", "replace") for sName in lNames if sName.lower().endswith(".opf")), "")
    oCover = re.search(r'<item\b[^>]*properties="[^"]*cover-image[^"]*"[^>]*>', sOpfText)
    if oCover: dAudit["cover"] = posixpath.basename(re.search(r'href="([^"]+)"', oCover.group(0)).group(1)) + ", placed by its own build"
    writeStableEpub(sEpub, lNames, dData, sourceTime(sManuscript))
    oLevels = collections.Counter(iHeading for iHeading, _ in headingList(sBody))
    dAudit["epub"], dAudit["splitLevel"] = sEpub, min([i for i, n in oLevels.items() if n > 1] or list(oLevels) or [2])
    log(sRoot + ": built by its own project and copied to " + sEpub + ", " + format(os.path.getsize(sEpub), ",") + " bytes")
    return sEpub


def editionRules(sRoot):
    """EDITIONS FOR OTHER STORES (9 October 2026). The Kindle EPUB is built from the manuscript as it is; another store
    can need a few differences -- Apple Books, through Draft2Digital, rejects links to Amazon, and "Kindle book" reads
    oddly there. Each such edition is a file configs\\editions\\<root>-<Edition>.inix:
        [edition]  name = Draft2Digital   file = <root>_Draft2Digital.epub   unlinkHosts = amazon.
        [replace1] find = (exact manuscript text)   with = (its text in this edition)   ... [replace2], and so on.
    The files sit outside the book's folder, so an edition never changes the book's own content fingerprint and never
    sends the Kindle book to KDP again. Returns a list of {name, file, unlink, replacements}."""
    lEditions = []
    for sPath in sorted(glob.glob(os.path.join(sProject, "configs", "editions", sRoot + "-*.inix")), key=str.lower):
        dInix = readInix(sPath)
        dEdition = dInix.get("edition", {})
        sName = dEdition.get("name", "").strip() or os.path.basename(sPath)[len(sRoot) + 1:-5]
        lReplacements = [(dInix[s].get("find", ""), dInix[s].get("with", "")) for s in sorted(dInix, key=lambda s: (len(s), s)) if s.lower().startswith("replace") and dInix[s].get("find", "")]
        lEditions.append({"name": sName, "file": dEdition.get("file", "").strip() or sRoot + "_" + sName + ".epub",
                          "unlink": [s.strip().lower() for s in dEdition.get("unlinkHosts", "").split(",") if s.strip()],
                          "replacements": lReplacements, "path": sPath})
    return lEditions


def unlinkHosts(sEpub, lsHosts):
    """Every link in the EPUB's pages whose address names one of lsHosts becomes its plain text, citations included.
    The mimetype entry stays first and uncompressed, as EPUB requires. Returns how many links were removed."""
    import zipfile
    iRemoved = [0]
    def plain(oMatch):
        if any(sHost in oMatch.group(1).lower() for sHost in lsHosts):
            iRemoved[0] += 1
            return oMatch.group(2)
        return oMatch.group(0)
    sNew = sEpub + ".writing"
    with zipfile.ZipFile(sEpub) as zIn, zipfile.ZipFile(sNew, "w") as zOut:
        for oInfo in zIn.infolist():
            bData = zIn.read(oInfo.filename)
            if oInfo.filename.lower().endswith((".xhtml", ".html", ".htm")):
                sPage = bData.decode("utf-8")
                sPage = re.sub(r'(?s)<a\b[^>]*\bhref="(https?://[^"]*)"[^>]*>(.*?)</a>', plain, sPage)
                bData = sPage.encode("utf-8")
            zOut.writestr(oInfo, bData, compress_type=zipfile.ZIP_STORED if oInfo.filename == "mimetype" else zipfile.ZIP_DEFLATED)
    os.replace(sNew, sEpub)
    return iRemoved[0]


def buildEpub(dBook, dKdp, dAudit, dEdition=None):
    """Builds results\\<root>.epub from the manuscript; records pictures, warnings and errors in the audit. With
    dEdition (from editionRules), builds that edition instead, into its own file and working folder."""
    sRoot = dBook["root"]
    sBookDir = os.path.join(sProject, "books", sRoot)
    sManuscript = os.path.join(sBookDir, sRoot + ".md")
    sText = open(sManuscript, encoding="utf-8-sig").read()
    if dEdition:
        # Each replacement must find its text exactly once, so an edition never drifts silently from a revised manuscript.
        sText = sText.replace("\r\n", "\n")
        for sFind, sWith in dEdition["replacements"]:
            sFind, sWith = sFind.replace("\r\n", "\n").strip("\n"), sWith.replace("\r\n", "\n").strip("\n")
            iCount = sText.count(sFind)
            if iCount != 1:
                dAudit["errors"].append("The %s edition's replacement text was found %s in the manuscript, so the edition was not built: %s" % (dEdition["name"], "nowhere" if iCount == 0 else str(iCount) + " times", sFind[:90]))
                return ""
            sText = sText.replace(sFind, sWith)
    dYaml, sBody = splitFrontMatter(sText)
    dAudit["yaml"], dAudit["body"] = dYaml, sBody
    sWork = workFolder(sRoot) if not dEdition else workFolder(sRoot + "-" + dEdition["name"])
    dFoundAll = readInix(os.path.join(sBookDir, "found.inix")) if os.path.exists(os.path.join(sBookDir, "found.inix")) else {}
    sBody, lRecords, lErrors = resolvePictures(dBook, sBody, sWork, dFoundAll.get("found", {}))
    dAudit["pictures"] = lRecords
    if lErrors:
        lAddresses = [s.split(": ", 1)[-1] for s in lErrors]
        # Not ready, unless the book's catalog entry says a text-only edition is intended (allowMissingPictures = yes):
        # valid EPUB syntax does not mean the book kept its content (8 October 2026, from an audit by another AI).
        dAudit["warnings" if dBook.get("allowMissingPictures", "").lower() == "yes" else "errors"].append(plural(len(lAddresses), "picture") + " left out, found nowhere -- not in the images folder, a Word file, or at its address -- so each one's text alternative stands in its place. The book's Word file, if it has one, would restore them: start OneDrive and run with --gather. The addresses: " + "; ".join(lAddresses) + ".")
    # The chapter level is the shallowest heading level used more than once: a manuscript whose only level-1 heading is its
    # own title (WCAG in a Book) has its chapters one level down, and listing that title alone would make a table of contents
    # of one entry. A heading shifted above level 1 becomes plain text; the title page already shows the title.
    oLevels = collections.Counter(iHeading for iHeading, _ in headingList(sBody))
    iLevel = min([i for i, n in oLevels.items() if n > 1] or list(oLevels) or [2])
    iShift = 1 - iLevel
    dMeta = bookMetadata(dBook, dYaml, dKdp, bool(lRecords), iLevel)
    sMetaPath = os.path.join(sWork, "metadata.yaml")
    writeText(sMetaPath, json.dumps(dMeta, ensure_ascii=False, indent=1), False)
    sWorkMd = os.path.join(sWork, sRoot + ".md")
    writeText(sWorkMd, sBody, False)
    sEpub = os.path.join(sProject, "results", dEdition["file"] if dEdition else sRoot + ".epub")
    os.makedirs(os.path.dirname(sEpub), exist_ok=True)
    lCommand = [dTools["pandoc"], sWorkMd, "--from", "markdown+autolink_bare_uris-raw_html", "--to", "epub3", "--output", sEpub, "--metadata-file", sMetaPath, "--css", bookTemplate("epub.css"), "--lua-filter", bookTemplate("tocEpub.lua"), "--shift-heading-level-by", str(iShift), "--split-level", "1", "--resource-path", sWork, "--toc-depth", dBook.get("tocDepth") or "2"]
    bMarker = bool(re.search(r"(?m)^\[TOC\]\s*$", sBody))
    if not bMarker: lCommand.append("--toc")
    # A BOOK'S OWN STYLESHEET AND CITATIONS (8 October 2026, when Blind Vibe Coding moved here from its own project):
    # books\<root>\<root>.css is added after the shared stylesheet, so it can refine it; a <root>.bib beside the
    # manuscript turns on Pandoc's citations, numbered in the style of <root>.csl when there is one, each citation linked to
    # its note and the notes printed where the manuscript places ::: {#refs} :::. Any book may have either.
    sOwnCss = os.path.join(sBookDir, sRoot + ".css")
    if os.path.exists(sOwnCss): lCommand += ["--css", sOwnCss]
    sBib = os.path.join(sBookDir, sRoot + ".bib")
    if os.path.exists(sBib):
        lCommand += ["--citeproc", "--bibliography", sBib, "--reference-location=document", "--metadata", "link-citations=true", "--metadata", "link-bibliography=true", "--metadata", "notes-after-punctuation=true"]
        sCsl = os.path.join(sBookDir, sRoot + ".csl")
        if os.path.exists(sCsl): lCommand += ["--csl", sCsl]
        log(sRoot + ": citations from " + os.path.basename(sBib) + (" in the style of " + os.path.basename(sCsl) if os.path.exists(sCsl) else ""))
    lCovers = [os.path.join(sBookDir, sRoot + s) for s in c_lCoverExtensions if os.path.exists(os.path.join(sBookDir, sRoot + s))]
    if lCovers:
        lCommand += ["--epub-cover-image", lCovers[0]]
        dAudit["cover"] = os.path.basename(lCovers[0])
    else:
        dAudit["warnings"].append("No cover in books\\" + sRoot + "\\; the EPUB has none. KDP uses the cover you uploaded there, but the EPUB copy buyers download and other stores need one inside. Put the cover there as " + sRoot + ".jpg.")
    if os.path.exists(sEpub): os.remove(sEpub)
    iCode, sOut = run(lCommand, sCwd=sWork)
    for sLine in sOut.splitlines():
        if sLine.startswith("[WARNING]"): dAudit["warnings"].append("Pandoc: " + re.split(r": PandocHttpError| \(StatusCodeException", sLine[9:].strip())[0][:240])
    if iCode != 0 or not os.path.exists(sEpub):
        dAudit["errors"].append("Pandoc could not build the EPUB (exit code " + str(iCode) + "); see the log.")
        return ""
    finishPackage(sEpub, bool(lRecords), dBook["subtitle"], os.path.join(sProject, "books", dBook["root"], dBook["root"] + ".md"))
    if dEdition:
        iUnlinked = unlinkHosts(sEpub, dEdition["unlink"]) if dEdition["unlink"] else 0
        log("%s: built the %s edition, %s, %s bytes; %s replaced, %s to %s made plain text" % (sRoot, dEdition["name"], sEpub, format(os.path.getsize(sEpub), ","), plural(len(dEdition["replacements"]), "passage"), plural(iUnlinked, "link"), ", ".join(dEdition["unlink"]) or "no host"))
        return sEpub
    dAudit["epub"] = sEpub
    dAudit["splitLevel"] = iLevel
    log(sRoot + ": built " + sEpub + ", " + format(os.path.getsize(sEpub), ",") + " bytes")
    return sEpub


# ---------------------------------------------------------------- audits

def runEpubcheck(sEpub, dAudit):
    """EPUBCheck's verdict: fatal errors and errors make the book not ready; warnings are listed."""
    if "epubcheck" not in dTools:
        dAudit["errors"].append("EPUBCheck could not be installed, so the EPUB was not validated; see the log.")
        return False
    sJson = os.path.join(workFolder(dAudit["root"]), "epubcheck.json")
    # A report left by the last build must not stand for this one, if EPUBCheck fails to write a new one.
    if os.path.exists(sJson): os.remove(sJson)
    iCode, sOut = run([dTools["java"], "-jar", dTools["epubcheck"], sEpub, "--json", sJson], iTimeout=1200)
    if not os.path.exists(sJson):
        dAudit["errors"].append("EPUBCheck did not produce a report (exit code " + str(iCode) + "); see the log.")
        return False
    dReport = json.load(open(sJson, encoding="utf-8"))
    dAudit["epubcheck"] = {"ERROR": [], "WARNING": [], "USAGE": [], "INFO": []}
    for dMessage in dReport.get("messages", []):
        sSeverity = dMessage.get("severity", "INFO")
        lLocations = dMessage.get("locations", []) or [{}]
        sWhere = ", ".join((d.get("path", "") + (":" + str(d.get("line")) if d.get("line", -1) not in (-1, None) else "")) for d in lLocations[:3])
        sLine = dMessage.get("ID", "") + " " + dMessage.get("message", "").strip() + (" (" + sWhere + ")" if sWhere else "")
        dAudit["epubcheck"]["ERROR" if sSeverity in ("FATAL", "ERROR") else sSeverity if sSeverity in ("WARNING", "USAGE") else "INFO"].append(sLine)
    for sLine in dAudit["epubcheck"]["ERROR"]: dAudit["errors"].append("EPUBCheck: " + sLine)
    for sLine in dAudit["epubcheck"]["WARNING"]: dAudit["warnings"].append("EPUBCheck: " + sLine)
    return True


def aceFailures(oNode, lOut):
    """Every failed assertion in Ace's report, wherever the report nests it."""
    if isinstance(oNode, dict):
        dResult, dTest = oNode.get("earl:result"), oNode.get("earl:test")
        if isinstance(dResult, dict) and isinstance(dTest, dict) and dResult.get("earl:outcome") == "fail":
            dPointer = dResult.get("earl:pointer") or {}
            lCss = dPointer.get("css") or [] if isinstance(dPointer, dict) else []
            lOut.append({"impact": dTest.get("earl:impact", "minor"), "rule": dTest.get("dct:title", ""), "text": (dResult.get("dct:description") or dTest.get("dct:description") or "").strip(), "where": str(lCss[:1])})
        for oValue in oNode.values(): aceFailures(oValue, lOut)
    elif isinstance(oNode, list):
        for oValue in oNode: aceFailures(oValue, lOut)
    return lOut


# ---------------------------------------------------------------- Kindle Previewer
# AMAZON'S OWN CHECKS (8 October 2026). KDP's guidelines say to validate an EPUB with Kindle Previewer, whose errors
# block a book from being published. Its command line (from version 3.32) converts a book without the window:
#     <Kindle Previewer> <book.epub> -convert -log -output <folder>
# where -log writes only the validation logs, not a Kindle file. The log is a CSV of Type, Description, Source File,
# Line Number, the text before the problem, and a Recommended Fix; an Error blocks publishing, a Notice does not. The
# options and file names come from the MobileRead wiki and published logs, not Amazon's help pages, so this first
# version records everything -- the command, exit code, output, and every file produced, copied to
# logs\kindlePreviewer\<book> -- and reads any CSV it finds. Errors become audit errors, as Amazon treats them; a
# Previewer that cannot run is a warning while its behavior is being learned.

def kindlePreviewerCandidates():
    r"""Every Kindle Previewer program file worth trying, best first: the setting, the per-user install folder a
    default install uses (%LOCALAPPDATA%\Amazon\Kindle Previewer 3), the Program Files folders, and the install folder
    Windows' list of installed programs names."""
    lDirs = [os.path.join(os.environ.get("LOCALAPPDATA", ""), "Amazon", "Kindle Previewer 3"),
             os.path.join(os.environ.get("LOCALAPPDATA", ""), "Amazon", "Kindle Previewer"),
             os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Amazon", "Kindle Previewer 3"),
             os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "Amazon", "Kindle Previewer 3")]
    if bWindows:
        try:
            import winreg
            for oHive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                for sRoot in (r"Software\Microsoft\Windows\CurrentVersion\Uninstall", r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"):
                    try: oKey = winreg.OpenKey(oHive, sRoot)
                    except OSError: continue
                    for i in range(winreg.QueryInfoKey(oKey)[0]):
                        try:
                            oSub = winreg.OpenKey(oKey, winreg.EnumKey(oKey, i))
                            sName = winreg.QueryValueEx(oSub, "DisplayName")[0]
                        except OSError: continue
                        if "kindle previewer" not in str(sName).lower(): continue
                        try: dTools["kindlePreviewerVersion"] = str(winreg.QueryValueEx(oSub, "DisplayVersion")[0])
                        except OSError: pass
                        for sValue in ("InstallLocation", "DisplayIcon", "UninstallString"):
                            try: sFound = str(winreg.QueryValueEx(oSub, sValue)[0]).strip().strip('"').split(",")[0]
                            except OSError: continue
                            if sFound: lDirs.append(sFound if os.path.isdir(sFound) else os.path.dirname(sFound))
                        log("Windows lists " + str(sName) + " as installed")
        except Exception as oError:
            log("Could not read the list of installed programs: " + str(oError))
    lFiles = []
    sSetting = dSettings.get("kindlePreviewer", "").strip()
    if sSetting: lFiles.append(sSetting)
    # KINDLE PREVIEWER 4 FIRST (8 October 2026): Amazon replaced version 3 on 22 September 2026 and no longer supports
    # it. Version 4 is a Windows app package (KindlePreviewerApp) started by the command name Windows gives it,
    # kindlepreviewer, kept in the folder of app commands and found on the search path.
    for sAlias in (os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WindowsApps", "kindlepreviewer.exe"), shutil.which("kindlepreviewer") or ""):
        if sAlias and os.path.lexists(sAlias): lFiles.append(sAlias)
    for sDir in lDirs:
        if not sDir or not os.path.isdir(sDir): continue
        for sName in sorted(os.listdir(sDir)):
            if re.match(r"(?i)^kindle\s*previewer.*\.exe$", sName) and "uninst" not in sName.lower(): lFiles.append(os.path.join(sDir, sName))
    return list(dict.fromkeys(lFiles))


def kindlePreviewer4Package():
    """Kindle Previewer 4's app package as Windows lists it -- its version and folder -- or {} when it is not installed."""
    if not bWindows: return {}
    iCode, sOut = run(["powershell.exe", "-NoProfile", "-Command", "Get-AppxPackage -Name '*KindlePreviewer*' | ForEach-Object { $_.Name + '|' + $_.Version + '|' + $_.InstallLocation }"], iTimeout=120)
    for sLine in (sOut or "").splitlines():
        lParts = sLine.strip().split("|")
        if len(lParts) == 3 and "kindlepreviewer" in lParts[0].lower(): return {"name": lParts[0], "version": lParts[1], "folder": lParts[2]}
    return {}


def isPreviewer4(sPath):
    """Whether this program is Kindle Previewer 4's command (kindlepreviewer, an app command) rather than version 3."""
    return os.path.basename(sPath).lower() == "kindlepreviewer.exe" or "windowsapps" in sPath.lower()


def ensureKindlePreviewer():
    """Kindle Previewer, version 4 by preference, found or installed with winget (Amazon.KindlePreviewer). Version 4
    keeps itself current, as Amazon says. Version 3, which Amazon no longer supports, is used only when version 4 is
    absent, and then its own -update is run once a week (toolRefreshDays), since that is what installs version 4.
    WHY (8 October 2026): buildBooks found the old version 3 in AppData and ran its -update, which fetched Kindle
    Previewer 4.0.1's setup; that failed, because the author already had version 4.0.3 installed as an app package."""
    if not bWindows: return False
    lFound = [s for s in kindlePreviewerCandidates() if os.path.lexists(s)]
    if not lFound:
        log("Kindle Previewer was not found; installing it with winget")
        winget("Amazon.KindlePreviewer")
        lFound = [s for s in kindlePreviewerCandidates() if os.path.lexists(s)]
    dPackage = kindlePreviewer4Package()
    if dPackage:
        log("Kindle Previewer 4 is installed: " + dPackage["name"] + " version " + dPackage["version"] + " in " + dPackage["folder"])
        dTools["kindlePreviewerVersion"] = dPackage["version"]
    for s in kindlePreviewerCandidates(): log("Kindle Previewer candidate: " + s + (" (present)" if os.path.lexists(s) else " (absent)"))
    if not lFound: return False
    if not isPreviewer4(lFound[0]) and not dPackage:
        say("Only Kindle Previewer 3 is installed, which Amazon no longer supports; its checks still run.")
        sStampFile = os.path.join(paths.data(), "kindlePreviewerUpdated.txt")
        if isStale(sStampFile):
            say("Asking Kindle Previewer 3 to update itself, which installs Kindle Previewer 4.")
            iCode, sOut = run([lFound[0], "-update"], iTimeout=1800)
            log("Kindle Previewer -update: exit " + str(iCode))
            if iCode == 0: writeText(sStampFile, datetime.datetime.now().isoformat(), False)
            lFound = [s for s in kindlePreviewerCandidates() if os.path.lexists(s)] or lFound
    dTools["kindlePreviewer"] = lFound[0]
    log("Kindle Previewer: " + lFound[0] + ", version " + dTools.get("kindlePreviewerVersion", "unknown") + (" (version 4)" if isPreviewer4(lFound[0]) else " (version 3)"))
    if isPreviewer4(lFound[0]):
        # Version 4's own usage, logged once a build: its options may differ from version 3's, and the log shows them.
        iCode, sHelp = runPreviewerQuietly([lFound[0], "--help"], 120)
        for sLine in (sHelp or "").splitlines()[:80]: log("  KP4 help| " + sLine)
    return True


def runPreviewerQuietly(lCommand, iTimeout):
    """Runs Kindle Previewer where its words cannot reach the build window. WHY (8 October 2026): it is a windowed program
    that attaches to its parent's console and writes there directly, past any captured output, so its banner, progress
    and "A new version of Kindle Previewer is available" were spoken for every book. Started through a command prompt
    that has a hidden console of its own (CREATE_NO_WINDOW), it attaches to that one instead. Its findings are in the
    files it writes, which are read and kept, so nothing is lost."""
    log("run quietly: " + subprocess.list2cmdline(lCommand))
    if not bWindows: return run(lCommand, iTimeout=iTimeout)
    try:
        oResult = subprocess.run(["cmd.exe", "/c"] + lCommand, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=iTimeout, creationflags=0x08000000)
    except subprocess.TimeoutExpired:
        log("  timed out after " + str(iTimeout) + " seconds")
        return 124, "timed out"
    sOut = (oResult.stdout or "") + (oResult.stderr or "")
    log("  exit " + str(oResult.returncode))
    return oResult.returncode, sOut


def previewerRun(sEpub, sOut, sLabel):
    r"""One Kindle Previewer run over an EPUB into its own folder: the command, exit code, output and files logged.
    Returns (summary row as a dict, or {}; detail rows as dicts; files produced). What it writes, learned from the
    author's first run (8 October 2026): Summary_Log.csv, one row per book -- Book Name, Enhanced Typesetting Status,
    Conversion Status, Error Count, Quality Issue Count, Output File Path, Log File Path, Quality Report Path -- and
    Logs\<book>_log.csv, a notice line and then rows of Type, Description, Source File, Line Number, Text Preceding
    Warning or Error, Recommended Fix. -convert writes a KPF of the book under KPF\ even with -log."""
    import csv
    shutil.rmtree(sOut, ignore_errors=True)
    os.makedirs(sOut, exist_ok=True)
    oStart = time.time()
    iCode, sText = runPreviewerQuietly([dTools["kindlePreviewer"], sEpub, "-convert", "-log", "-output", sOut], 900)
    log(sLabel + ": Kindle Previewer exit code %d after %.0f seconds" % (iCode, time.time() - oStart))
    for sLine in (sText or "").splitlines()[:60]: log("  KP| " + sLine)
    lProduced = [os.path.join(d, f) for d, _, lf in os.walk(sOut) for f in lf]
    dSummary, lDetail = {}, []
    for sPath in lProduced:
        if os.path.basename(sPath).lower() == "summary_log.csv":
            lRows = list(csv.DictReader(open(sPath, encoding="utf-8-sig", errors="replace")))
            if lRows: dSummary = {k.strip(): (v or "").strip() for k, v in lRows[0].items() if k}
        elif sPath.lower().endswith("_log.csv"):
            lRows = list(csv.reader(open(sPath, encoding="utf-8-sig", errors="replace")))
            iHead = next((n for n, r in enumerate(lRows) if r and r[0].strip().lower() == "type"), -1)
            if iHead >= 0:
                lHead = [h.strip() for h in lRows[iHead]]
                lDetail += [dict(zip(lHead, [c.strip() for c in r])) for r in lRows[iHead + 1:] if r and "".join(r).strip()]
    log(sLabel + ": Kindle Previewer summary " + json.dumps(dSummary) + "; " + plural(len(lDetail), "detail row"))
    return dSummary, lDetail, lProduced


def enhancedTypesettingOk(sEpub, sLabel):
    """True, False or None: whether Kindle Previewer finds Enhanced Typesetting supported for this EPUB."""
    dSummary, _, _ = previewerRun(sEpub, os.path.join(paths.temp(), "kindlePreviewerProbe"), sLabel)
    sStatus = dSummary.get("Enhanced Typesetting Status", "").lower()
    return None if not sStatus else sStatus == "supported"


def probeEnhancedTypesetting(sEpub, dAudit):
    """Why Kindle Previewer finds Enhanced Typesetting unsupported, since it does not say: first the reading order is
    halved, a variant EPUB at a time, to the one chapter file whose presence turns it off; then one change at a time is
    tried on that file -- definition lists as plain paragraphs, GIF and PNG pictures out, preformatted text as plain,
    tables out -- to name the feature. Each variant is a copy; the book itself is never changed. Returns a sentence."""
    with zipfile.ZipFile(sEpub) as oZip:
        lNames = oZip.namelist()
        dData = {n: oZip.read(n) for n in lNames}
    sOpfPath, sOpf, sBase, dItems, lSpine = kdpEpub.epubPaths(dData, lNames)
    dIdByHref = {h: i for i, (h, p) in dItems.items()}
    lDocs = [h for h in lSpine if h.endswith(".xhtml") and "title_page" not in h and "cover" not in h]
    sVariant = os.path.join(paths.temp(), "kindlePreviewerProbe.epub")
    def write(dChanged, lKeep=None):
        sNewOpf = sOpf
        if lKeep is not None:
            for h in lSpine:
                if h not in lKeep and h.endswith(".xhtml") and "title_page" not in h and "cover" not in h:
                    sNewOpf = re.sub(r'\s*<itemref\s+idref="' + re.escape(dIdByHref.get(h, "\x00")) + r'"[^>]*/>', "", sNewOpf)
        with zipfile.ZipFile(sVariant, "w") as oOut:
            oOut.writestr(zipfile.ZipInfo("mimetype"), b"application/epub+zip", compress_type=zipfile.ZIP_STORED)
            for n in lNames:
                if n == "mimetype": continue
                oOut.writestr(n, sNewOpf.encode("utf-8") if n == sOpfPath else dChanged.get(n, dData[n]), compress_type=zipfile.ZIP_DEFLATED)
        return sVariant
    iRuns = 0
    lCandidates = lDocs
    while len(lCandidates) > 1 and iRuns < 8:
        lFirst, lSecond = lCandidates[:len(lCandidates) // 2], lCandidates[len(lCandidates) // 2:]
        iRuns += 1
        bFirst = enhancedTypesettingOk(write({}, lFirst), dAudit["root"] + " probe, first half of %d files" % len(lCandidates))
        if bFirst is False: lCandidates = lFirst; continue
        iRuns += 1
        bSecond = enhancedTypesettingOk(write({}, lSecond), dAudit["root"] + " probe, second half of %d files" % len(lCandidates))
        if bSecond is False: lCandidates = lSecond; continue
        log(dAudit["root"] + ": each half alone is supported, so no single file turns Enhanced Typesetting off")
        return "Every part of the book passes on its own, so no chapter file is the cause; Kindle Previewer's verdict on Enhanced Typesetting varies between runs of the same book (on 8 October its failing runs ended in about 15 seconds, its passing ones in about 43), so this is most likely Kindle Previewer, not the book, and KDP converts the book itself."
    if len(lCandidates) != 1: return "The probe could not narrow it to one chapter file; see the log."
    sDoc = lCandidates[0]
    sDocPath = posixpath.join(sBase, sDoc)
    sText = dData[sDocPath].decode("utf-8", "replace")
    oHeading = re.search(r"<h[1-6][^>]*>(.*?)</h[1-6]>", sText, re.S)
    sHeading = re.sub(r"<[^>]+>|\s+", " ", oHeading.group(1)).strip() if oHeading else sDoc
    log(dAudit["root"] + ": Enhanced Typesetting turns off with " + sDoc + " (" + sHeading + ")")
    lChanges = [
        ("definition lists as plain paragraphs", lambda t: re.sub(r"</?dl\b[^>]*>", "", re.sub(r"<(/?)d[td]\b([^>]*)>", r"<\1p\2>", t))),
        ("its GIF and PNG pictures left out", lambda t: re.sub(r'<img\b[^>]*src="[^"]+\.(gif|png)"[^>]*/?>', "", t, flags=re.I)),
        ("preformatted text as plain paragraphs", lambda t: re.sub(r"<(/?)pre\b([^>]*)>", r"<\1p\2>", t)),
        ("its tables left out", lambda t: re.sub(r"<table\b.*?</table>", "", t, flags=re.S)),
        ("all its pictures left out", lambda t: re.sub(r"<img\b[^>]*/?>", "", t))]
    # A feature such as definition lists may sit in many chapter files, so each trial change is made in every chapter
    # file at once: changing only the first file found would leave the others to keep Enhanced Typesetting off.
    lHelped = []
    for sChange, fChange in lChanges:
        if fChange(sText) == sText: continue
        dChanged = {}
        for sOther in lDocs:
            sOtherPath = posixpath.join(sBase, sOther)
            sOld = dData[sOtherPath].decode("utf-8", "replace")
            sNew = fChange(sOld)
            if sNew != sOld: dChanged[sOtherPath] = sNew.encode("utf-8")
        bOk = enhancedTypesettingOk(write(dChanged), dAudit["root"] + " probe, " + sChange + " in " + plural(len(dChanged), "chapter file"))
        if bOk: lHelped.append(sChange)
        if bOk: break
    sWhere = os.path.basename(sDoc) + ", the part headed \"" + sHeading + "\""
    if lHelped: return "Enhanced Typesetting turns off with " + sWhere + ", the first of the files that turn it off; it returns with " + lHelped[0] + " throughout the book."
    return "Enhanced Typesetting turns off because of " + sWhere + "; none of the trial changes brought it back, so the cause is something else in that file."


def runKindlePreviewer(sEpub, dAudit):
    r"""Amazon's conversion checks on the EPUB through Kindle Previewer's command line, read from its summary and its log:
    a failed conversion or any error makes the book not ready; quality issues and an unsupported Enhanced Typesetting are
    warnings, the second probed for its cause; notices, which Amazon says can be ignored, are logged only."""
    if "kindlePreviewer" not in dTools:
        dAudit["warnings"].append("Kindle Previewer was not found or could not be installed, so Amazon's own conversion checks were not run; see the log.")
        return False
    sOut = os.path.join(paths.temp(), "kindlePreviewer", dAudit["root"])
    dSummary, lDetail, lProduced = previewerRun(sEpub, sOut, dAudit["root"])
    sKeep = os.path.join(os.path.dirname(sLogPath), "kindlePreviewer", dAudit["root"])
    shutil.rmtree(sKeep, ignore_errors=True)
    for sPath in lProduced:
        if sPath.lower().endswith(".kpf"):
            log(dAudit["root"] + ": KPF written, " + format(os.path.getsize(sPath), ",") + " bytes, not kept in the logs")
            continue
        sTo = os.path.join(sKeep, os.path.relpath(sPath, sOut))
        os.makedirs(os.path.dirname(sTo), exist_ok=True)
        shutil.copyfile(sPath, sTo)
    if not dSummary:
        dAudit["warnings"].append("Kindle Previewer wrote no summary, so Amazon's checks gave no result; see the log.")
        return False
    dAudit["kindlePreviewer"] = dSummary
    sConversion, sTypesetting = dSummary.get("Conversion Status", ""), dSummary.get("Enhanced Typesetting Status", "")
    def number(sKey):
        try: return int(dSummary.get(sKey, "0") or 0)
        except ValueError: return 0
    if sConversion.lower() != "success": dAudit["errors"].append("Kindle Previewer could not convert the book: conversion status " + (sConversion or "missing") + ".")
    for d in lDetail:
        sType = d.get("Type", "").lower()
        sItem = "Kindle Previewer " + sType + ": " + d.get("Description", "") + ((" (" + os.path.basename(d.get("Source File", "")) + ((" line " + d.get("Line Number", "").lstrip("0")) if d.get("Line Number", "").strip("0") else "") + ")") if d.get("Source File") else "") + ((" Fix: " + d["Recommended Fix"]) if d.get("Recommended Fix") else "")
        if sType == "error": dAudit["errors"].append(sItem[:600])
        elif sType == "warning": dAudit["warnings"].append(sItem[:600])
        else: log(dAudit["root"] + ": " + sItem)
    if number("Error Count") and not any(x.startswith("Kindle Previewer error") for x in dAudit["errors"]):
        dAudit["errors"].append("Kindle Previewer counts " + plural(number("Error Count"), "error") + "; its log in logs\\kindlePreviewer names them.")
    if number("Quality Issue Count"):
        dAudit["warnings"].append("Kindle Previewer counts " + plural(number("Quality Issue Count"), "quality issue") + "; its quality report is in logs\\kindlePreviewer.")
    if sTypesetting.lower() == "not supported":
        # CONFIRMED BEFORE REPORTED (8 October 2026): Returning Alive's EPUB, the same 1,559,315 bytes in two builds, was
        # "Not Supported" at 8:58 and "Supported" at 9:24. One more run decides; a pass the second time is a glitch.
        dAgain, _, _ = previewerRun(sEpub, sOut + "_again", dAudit["root"] + " (second run, to confirm)")
        if dAgain.get("Enhanced Typesetting Status", "").lower() == "supported":
            log(dAudit["root"] + ": Enhanced Typesetting was reported unsupported once and supported on a second run; treated as supported")
            sTypesetting = "Supported (on a second run)"
            dSummary["Enhanced Typesetting Status"] = sTypesetting
    if sTypesetting.lower() == "not supported":
        sCause = probeEnhancedTypesetting(sEpub, dAudit) if dSettings.get("probeTypesetting", "yes").lower() != "no" else "the probe is turned off"
        dAudit["warnings"].append("Amazon's Enhanced Typesetting is not supported for this book, so it lacks the improved layout and features such as Page Flip. " + sCause)
    log(dAudit["root"] + ": Kindle Previewer -- conversion " + sConversion + ", Enhanced Typesetting " + sTypesetting + ", " + plural(number("Error Count"), "error") + ", " + plural(number("Quality Issue Count"), "quality issue"))
    return True


def runAce(sEpub, dAudit):
    """Ace by DAISY's verdict: critical and serious problems make the book not ready; moderate and minor ones are listed."""
    if "ace" not in dTools:
        dAudit["errors"].append("Ace by DAISY could not be installed, so accessibility was not checked; see the log.")
        return False
    sOut = os.path.join(paths.temp(), "ace", dAudit["root"])
    shutil.rmtree(sOut, ignore_errors=True)
    dAudit["aceReport"] = os.path.join(sOut, "report.html")
    iCode, sText = run([dTools["ace"], "--force", "--silent", "--outdir", sOut, sEpub], iTimeout=1800)
    sJson = os.path.join(sOut, "report.json")
    if not os.path.exists(sJson):
        dAudit["errors"].append("Ace did not produce a report (exit code " + str(iCode) + "); see the log.")
        return False
    lFailures = aceFailures(json.load(open(sJson, encoding="utf-8")), [])
    dSeen, lUnique = {}, []
    for d in lFailures:
        sKey = d["rule"] + "|" + d["text"]
        if sKey in dSeen:
            dSeen[sKey]["count"] += 1
            continue
        d["count"] = 1
        dSeen[sKey] = d
        lUnique.append(d)
    dAudit["ace"] = lUnique
    for d in lUnique:
        sLine = "Ace " + d["impact"] + ": " + d["rule"] + " -- " + d["text"] + (" (" + plural(d["count"], "place") + ")" if d["count"] > 1 else "")
        (dAudit["errors"] if d["impact"] in ("critical", "serious") else dAudit["warnings"]).append(sLine)
    return True


def syllables(sWord):
    """A close estimate of the syllables in an English word, good enough for a reading-level figure."""
    s = sWord.lower().strip("'")
    if len(s) <= 3: return 1
    s = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", s)
    s = re.sub(r"^y", "", s)
    return max(1, len(re.findall(r"[aeiouy]{1,2}", s)))


def readingLevel(sBody):
    """Flesch-Kincaid grade over the book's prose paragraphs, with the share of sentences longer than the limit."""
    lParagraphs = []
    for sBlock in re.split(r"\n\s*\n", outsideCode(sBody)):
        s = sBlock.strip()
        if not s or re.match(r"^(#|!\[|\||>|<|\[TOC\]|---|\*\*\*|\\)", s): continue
        if re.match(r"^([-*+]|\d+\.)\s", s): continue
        if re.match(r"^\*[^*].*\*$", s, re.S): continue
        s = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", s)
        s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
        s = re.sub(r"[*_`]+|\{[^}]*\}", "", s)
        lParagraphs.append(s)
    sText = " ".join(lParagraphs)
    lSentences = [x for x in re.split(r"(?<=[.!?])[\"\u201d\u2019)]*\s+", sText) if re.search(r"[A-Za-z]", x)]
    lWords = re.findall(r"[A-Za-z][A-Za-z'\u2019-]*", sText)
    if not lSentences or not lWords: return None
    iSyllables = sum(syllables(s) for s in lWords)
    nGrade = 0.39 * len(lWords) / len(lSentences) + 11.8 * iSyllables / len(lWords) - 15.59
    iLong = sum(1 for x in lSentences if len(re.findall(r"[A-Za-z][A-Za-z'\u2019-]*", x)) > c_iLongSentence)
    return {"grade": round(nGrade, 1), "sentences": len(lSentences), "words": len(lWords), "long": iLong}


def sectionText(sBody, sHeading):
    """The text under a heading of a given name, up to the next heading of the same or higher level."""
    oMatch = re.search(r"(?m)^(#{1,6})[ \t]+" + re.escape(sHeading) + r"[ \t]*(\{[^}]*\})?[ \t]*\r?$", sBody)
    if not oMatch: return None
    iLevel = len(oMatch.group(1))
    oNext = re.compile(r"(?m)^#{1," + str(iLevel) + r"}[ \t]").search(sBody, oMatch.end())
    return sBody[oMatch.end():oNext.start() if oNext else len(sBody)]


def auditManuscript(dBook, dAudit, dCatalog):
    """Checks of the manuscript that EPUBCheck and Ace cannot make: metadata, structure, pictures, characters, links, reading level, and the sections books of its kind carry."""
    dYaml, sBody = dAudit["yaml"], dAudit["body"]
    lWarnings, lErrors = dAudit["warnings"], dAudit["errors"]
    if rootName(dBook["title"]) != dBook["root"]: lErrors.append("The catalog root " + dBook["root"] + " does not follow the naming rule; it should be " + rootName(dBook["title"]) + ".")
    for sKey in ("title", "subtitle", "author"):
        sMine, sKdp = re.sub(r"\s+", " ", dYaml.get(sKey, "")).strip(), re.sub(r"\s+", " ", dBook[sKey]).strip()
        if sKey == "author" and sMine.lower().startswith("by "): sMine = sMine[3:]
        if sMine != sKdp: lWarnings.append("The manuscript's " + sKey + " is \u201c" + sMine + "\u201d but KDP shows \u201c" + sKdp + "\u201d. The EPUB uses KDP's.")
    if not dYaml.get("lang"): lWarnings.append("The manuscript does not state its language (lang); the EPUB says en-US.")
    lHeadings = headingList(sBody)
    iPrevious = 1
    for iLevel, sText in lHeadings:
        if iLevel > iPrevious + 1: lWarnings.append("Heading level jumps from " + str(iPrevious) + " to " + str(iLevel) + " at \u201c" + sText + "\u201d.")
        iPrevious = iLevel
    lGlued = []
    lLines = outsideCode(sBody).splitlines()
    for iIndex, sLine in enumerate(lLines):
        if iIndex and re.match(r"^#{1,6}[ \t]+\S", sLine) and lLines[iIndex - 1].strip(): lGlued.append(sLine.lstrip("#").strip())
    if lGlued: lErrors.append(plural(len(lGlued), "heading") + " with no blank line above, so Pandoc reads " + ("it" if len(lGlued) == 1 else "them") + " as ordinary text and the section loses its heading: " + ", ".join("\u201c" + s + "\u201d" for s in lGlued[:5]) + ".")
    if dAudit.get("splitLevel") == 1 and not any(iLevel == 2 for iLevel, sText in lHeadings): lWarnings.append("The manuscript uses level 1 headings for its sections. The EPUB works, but the other books use level 2 for sections, under the title.")
    lNames = [sText for iLevel, sText in lHeadings]
    bPublicDomain = not ownBook(dBook)
    lMissing = [s for s in ["Copyright"] if s not in lNames and not bPublicDomain]
    if ownBook(dBook) and "About the Author" not in lNames: lMissing.append("About the Author")
    for sSection in c_dSeriesSections.get(dBook["series"], []):
        if dBook["root"] == "Strange_Truths": break
        if sSection not in lNames and sSection not in lMissing: lMissing.append(sSection)
    if lMissing: lWarnings.append("Sections the house pattern calls for but this book lacks: " + ", ".join(lMissing) + ".")
    sCopyright = sectionText(sBody, "Copyright") or ""
    sCredit = sCopyright or sBody[:8000]
    lUncredited = [sTool for sTool in dBook["aiTools"] if not re.search(r"\b" + re.escape(sTool), sCredit)]
    if lUncredited: lWarnings.append("The Copyright section does not credit " + ", ".join(lUncredited) + ", which configs\\books.inix lists as helping with this book.")
    if dBook["aiUse"] == "generated" and not re.search(r"\bAI-generated\b", sCredit): lWarnings.append("An AI tool drafted this book's text, which KDP calls AI-generated, but its Copyright section does not say so; help\\BookPattern.md in the HomerDev kit has model wording.")
    if dBook["aiUse"] == "generated" and re.search(r"not AI-generated", sCredit): lWarnings.append("The Copyright section says the book is not AI-generated, but an AI tool drafted its text, which KDP calls AI-generated.")
    if dBook["aiUse"] == "assisted" and not re.search(r"\bAI-assisted\b", sCredit): lWarnings.append("The Copyright section does not say how AI assisted with this book.")
    if dBook["aiUse"] == "" and re.search(r"\bAI\b|GPT|Claude|artificial intelligence", sBody[:4000]): lWarnings.append("The book mentions AI, but configs\\books.inix does not say whether its use was generated or assisted, so its statement could not be checked.")
    if dBook["series"] == "Strange Truths" and dBook["root"] != "Strange_Truths":
        sAlso = sectionText(sBody, "Also in the Strange Truths Series") or ""
        lAbsent = [d["title"] for d in dCatalog.values() if d["series"] == "Strange Truths" and d["root"] != dBook["root"] and d["asin"] and d["asin"] not in sAlso]
        if sAlso and lAbsent: lWarnings.append("Also in the Strange Truths Series does not link: " + ", ".join(sorted(lAbsent, key=titleKey)) + ".")
    lPictures = dAudit.get("pictures", [])
    lUnique = [d for d in lPictures if not d.get("repeat")]
    iEmpty = sum(1 for d in lPictures if not d["alt"])
    if iEmpty: lWarnings.append(plural(iEmpty, "picture") + " of " + str(len(lPictures)) + " " + ("has" if iEmpty == 1 else "have") + " an empty text alternative, which tells a screen reader to skip " + ("it" if iEmpty == 1 else "them") + " as decoration. Photos of the people and places in a chapter carry meaning, so each should say in a sentence what it shows.")
    iEscaped = len(re.findall(r"&lt;/?[A-Za-z][^&\n]{0,60}&gt;|\\<a\s", sBody))
    if iEscaped: lWarnings.append(plural(iEscaped, "place") + " where HTML code shows as text, usually in a picture credit copied from Wikimedia, such as \u201c<a href=\u201d.")
    # An address in inline or fenced code, such as a placeholder like https://username.github.io, is shown as code on
    # purpose and is no bare link.
    sProse = re.sub(r"`[^`\n]*`", "", outsideCode(sBody))
    iBare = len(re.findall(r"\[(https?://[^\]]+)\]\(", sProse)) + len(re.findall(r"(?<![(<\[\"])\bhttps?://[^\s)>\]]+", re.sub(r"\]\([^)]*\)|\(<[^>]*>\)", "", sProse)))
    # A link to a file beside the page, or one opening with //, points at nothing inside an EPUB; EPUBCheck refuses it.
    lStray = [m for m in re.findall(r"(?<!!)\[[^\]]*\]\((?!#|[a-zA-Z][a-zA-Z0-9+.-]*:|images/)([^)\s]+)\)", sBody)]
    if lStray: lErrors.append(plural(len(lStray), "link") + " to a file or a //-address the EPUB does not hold, such as " + lStray[0] + "; give each its full address, beginning https://.")
    if iBare and not bPublicDomain: lWarnings.append(plural(iBare, "bare web address", "bare web addresses") + " in the text; give each readable link text instead.")
    iMojibake = len(re.findall("\u00e2\u20ac|\u00c3[\u00a0-\u00bf]|\ufffd", sBody))
    if iMojibake: lErrors.append(plural(iMojibake, "place") + " with garbled characters from a wrong text encoding, such as \u00e2\u20ac.")
    iViewImage = len(re.findall(r"\[View image\]", sBody))
    if iViewImage: lErrors.append(plural(iViewImage, "\u201cView image\u201d link") + " left where an earlier build could not find a picture.")
    dAudit["readingLevel"] = readingLevel(sBody)
    dLevel = dAudit["readingLevel"]
    if dLevel and dBook["readingGrade"] and dLevel["grade"] > dBook["readingGrade"]:
        lWarnings.append("Reading level is grade " + str(dLevel["grade"]) + " by the Flesch-Kincaid formula, above the target of grade " + str(dBook["readingGrade"]) + "; " + plural(dLevel["long"], "sentence") + " of " + str(dLevel["sentences"]) + " run past " + str(c_iLongSentence) + " words.")
    lDocx = bookDocx(dBook)
    if lDocx:
        iCodeA, sMd = run([dTools["pandoc"], os.path.join(sProject, "books", dBook["root"], dBook["root"] + ".md"), "-t", "plain", "--wrap=none"])
        iCodeB, sDocx = run([dTools["pandoc"], lDocx[-1], "-t", "plain", "--wrap=none"])
        iMd, iDocx = len(sMd.split()), len(sDocx.split())
        dAudit["wordCompare"] = (iMd, iDocx, os.path.basename(lDocx[-1]))
        if iCodeA == 0 and iCodeB == 0 and iMd and abs(iMd - iDocx) * 100 > c_iWordDiffPercent * iMd:
            lWarnings.append("The Word file " + os.path.basename(lDocx[-1]) + " has " + format(iDocx, ",") + " words and the manuscript " + format(iMd, ",") + "; check which holds the latest edits before submitting.")
    return True


def auditEpub(sEpub, dAudit, dKdp):
    """Checks inside the built EPUB: every picture has an alt attribute, every internal link has a target, every page states its language; plus size and KDP's delivery fee."""
    for sProblem in kdpEpub.tocProblems(sEpub): dAudit["errors"].append("Table of contents (KDP): " + sProblem)
    # Every page, the package and the NCX must be well-formed XML, which EPUBCheck reports as fatal; checked here too, so
    # a trial without EPUBCheck catches it and the message names the file and the place (7 October 2026: a second pass of
    # the table-of-contents fix left a nested list half replaced in Blind Vibe Coding's contents page).
    from xml.dom import minidom
    with zipfile.ZipFile(sEpub) as oZip:
        for sName in oZip.namelist():
            if not sName.lower().endswith((".xhtml", ".opf", ".ncx")): continue
            try: minidom.parseString(oZip.read(sName))
            except Exception as oError: dAudit["errors"].append("Not well-formed XML in " + sName + ": " + str(oError)[:120] + ". EPUBCheck would call this fatal.")
    with zipfile.ZipFile(sEpub) as oZip:
        dPages = {s: oZip.read(s).decode("utf-8", "replace") for s in oZip.namelist() if s.lower().endswith(".xhtml")}
    dIds = {s: set(re.findall(r"\bid=\"([^\"]+)\"", sText)) for s, sText in dPages.items()}
    iNoAlt, lBroken = 0, []
    for sPage, sText in dPages.items():
        iNoAlt += len([s for s in re.findall(r"<img\b[^>]*>", sText) if " alt=" not in s])
        if not re.search(r"<html\b[^>]*\bxml:lang=|<html\b[^>]*\blang=", sText): dAudit["errors"].append("Page " + os.path.basename(sPage) + " does not state its language.")
        for sHref in re.findall(r"\bhref=\"([^\"]+)\"", sText):
            if re.match(r"^[a-z]+:", sHref, re.I): continue
            sFile, _, sAnchor = sHref.partition("#")
            sTarget = os.path.normpath(os.path.join(os.path.dirname(sPage), urllib.parse.unquote(sFile))).replace("\\", "/") if sFile else sPage
            if sTarget not in dIds and not sFile.lower().endswith((".css", ".xhtml")):
                continue
            # A link to a chapter file that is not in the book is broken whether or not it names a place in it.
            if sFile.lower().endswith(".xhtml") and sTarget not in dIds: lBroken.append(sHref)
            elif sAnchor and sAnchor not in dIds.get(sTarget, set()): lBroken.append(sHref)
    if iNoAlt: dAudit["errors"].append(plural(iNoAlt, "picture") + " in the EPUB without an alt attribute.")
    if lBroken: dAudit["errors"].append(plural(len(lBroken), "internal link") + " with no matching target, such as " + ", ".join(sorted(set(lBroken))[:5]) + ".")
    iBytes = os.path.getsize(sEpub)
    nMb = iBytes / 1048576.0
    dAudit["size"] = iBytes
    sRoyalty = dKdp.get("kdp", {}).get("royalty", "")
    dAudit["deliveryFee"] = round(nMb * c_nDeliveryFeePerMb, 2)
    dAudit["royalty"] = sRoyalty
    return True


# ---------------------------------------------------------------- reports

def mdEscape(sText):
    """Keeps characters in a report line from being read as Markdown."""
    return re.sub(r"([\\`*_\[\]<>#|])", r"\\\1", sText)


def writeAudit(dBook, dAudit):
    """results\\<root>-audit.md and .htm: verdict first, then each check, problems as list items."""
    lErrors, lWarnings = dAudit["errors"], dAudit["warnings"]
    bReady = bool(dAudit.get("epub")) and not lErrors
    dAudit["ready"] = bReady
    l = ["---", "title: " + json.dumps("Audit of " + dBook["title"], ensure_ascii=False), "date: " + datetime.date.today().isoformat(), "lang: en-US", "---", ""]
    l += ["## Verdict", "", ("Ready to submit" if bReady else "Not ready to submit") + ": " + plural(len(lErrors), "error") + " and " + plural(len(lWarnings), "warning") + ".", ""]
    l += ["## Book", "", "- Title: " + mdEscape(dBook["title"]) + (": " + mdEscape(dBook["subtitle"]) if dBook["subtitle"] else ""), "- Manuscript: " + (mdEscape(externalManuscript(dBook)) + ", built by its own project" if dBook.get("externalProject") else "books\\\\" + dBook["root"] + "\\\\" + dBook["root"] + ".md")]
    if dAudit.get("epub"):
        l.append("- EPUB: results\\\\" + dBook["root"] + ".epub, " + "{:.2f}".format(dAudit["size"] / 1048576.0) + " MB" + (". At the 70 percent royalty KDP would deduct about $" + "{:.2f}".format(dAudit["deliveryFee"]) + " a sale in the US for delivery" + (", which this book pays now" if dAudit.get("royalty") == "70_PERCENT" else "; this book is at 35 percent, which has no delivery fee") + "." if dAudit.get("size") else ""))
    l.append("- Cover inside the EPUB: " + (dAudit.get("cover") or "none"))
    # The fingerprint of the EPUB this audit judged (8 October 2026, from an audit by another AI): kdpUpdate sends a book
    # only when the EPUB in results is this exact file, so an old audit cannot approve a newer or damaged one.
    if dAudit.get("epub") and os.path.exists(dAudit["epub"]):
        import hashlib
        l.append("- EPUB SHA-256: " + hashlib.sha256(open(dAudit["epub"], "rb").read()).hexdigest())
        if dAudit.get("buildKey"): l.append("- Build SHA-256: " + dAudit["buildKey"])
        for sEdition in dAudit.get("editions", []): l.append("- Edition: " + sEdition)
        # The sources this EPUB was made from, by content (9 October 2026): kdpUpdate knows an EPUB is stale when the
        # book's sources no longer have this fingerprint, without trusting file times.
        try:
            import kdpSubmit
            l.append("- Sources SHA-256: " + kdpSubmit.bookSourcesSha(os.path.join(sProject, "books", dBook["root"])))
        except Exception as oError:
            log("the sources fingerprint could not be taken: " + str(oError))
    if dAudit.get("wordCompare"): l.append("- Words: " + format(dAudit["wordCompare"][0], ",") + " in the manuscript, " + format(dAudit["wordCompare"][1], ",") + " in " + mdEscape(dAudit["wordCompare"][2]))
    dLevel = dAudit.get("readingLevel")
    if dLevel: l.append("- Reading level: grade " + str(dLevel["grade"]) + (" (target " + str(dBook["readingGrade"]) + ")" if dBook["readingGrade"] else " (no target for this book)") + "; " + plural(dLevel["long"], "sentence") + " of " + format(dLevel["sentences"], ",") + " over " + str(c_iLongSentence) + " words")
    l.append("")
    l += ["## Errors", ""] + (["- " + mdEscape(s) for s in lErrors] or ["None."]) + [""]
    l += ["## Warnings", ""] + (["- " + mdEscape(s) for s in lWarnings] or ["None."]) + [""]
    lPictures = dAudit.get("pictures", [])
    l += ["## Pictures", ""]
    if not lPictures: l += ["None.", ""]
    for iIndex, d in enumerate(lPictures):
        sLine = str(iIndex + 1) + ". " + mdEscape(d["name"]) + ": " + (("from the " + d["source"]) if d["source"] else "NOT FOUND")
        if d.get("repeat"): sLine += ", a repeat of an earlier picture"
        if d.get("note"): sLine += "; " + mdEscape(d["note"])
        sLine += "; text alternative: " + (mdEscape("\u201c" + d["alt"] + "\u201d") if d["alt"] else "empty")
        l.append(sLine)
    l.append("")
    l += ["## Tools", "", "- Pandoc " + dTools.get("pandocVersion", "not found"), "- EPUBCheck " + (dTools.get("epubcheckVersion", "") or ("installed" if "epubcheck" in dTools else "not available")), "- Ace by DAISY " + (dTools.get("aceVersion", "") or ("installed" if "ace" in dTools else "not available")) + (" (Ace's full report, until the next build: " + mdEscape(dAudit.get("aceReport", "")) + ")" if dAudit.get("aceReport") else ""), ""]
    sMd = os.path.join(sProject, "results", dBook["root"] + "-audit.md")
    writeText(sMd, "\n".join(l))
    run([dTools["pandoc"], sMd, "-s", "-o", sMd[:-3] + ".htm"])
    return bReady


def buildKey(dBook, sBookDir, dKdp):
    """THE BUILD FINGERPRINT (9 October 2026): everything that shapes a book's EPUB -- its sources by content, its catalog
    entry, the kdp and proposed sections of its data file, the kit's book templates, the Pandoc version and the build
    format. A book whose last audit names this fingerprint, says ready and names its exact EPUB is not built again, so
    a run builds only the books that changed. No file name or time is trusted."""
    import hashlib, kdpSubmit
    lsTemplates = []
    for sDir in (os.path.join(dTools.get("kit", ""), "Templates", "books"), os.path.join(sProject, "templates", "books")):
        if os.path.isdir(sDir):
            for sName in sorted(os.listdir(sDir), key=str.lower):
                sPath = os.path.join(sDir, sName)
                if os.path.isfile(sPath): lsTemplates.append(sName.lower() + ":" + hashlib.sha256(open(sPath, "rb").read()).hexdigest())
    lsEditions = [os.path.basename(s) + ":" + hashlib.sha256(open(s, "rb").read()).hexdigest() for s in sorted(glob.glob(os.path.join(sProject, "configs", "editions", dBook["root"] + "-*.inix")), key=str.lower)]
    lParts = [c_sBuildFormat, kdpSubmit.bookSourcesSha(sBookDir), dBook, {s: dKdp.get(s, {}) for s in ("kdp", "proposed")}, lsTemplates, dTools.get("pandocVersion", ""), lsEditions]
    return hashlib.sha256(json.dumps(lParts, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def keptAudit(dBook, sKey):
    """The book's last audit as a summary entry, when it was of this exact build and is still true: it names this build
    fingerprint, says ready, and names the EPUB in results byte for byte. Otherwise None, and the book is built."""
    import hashlib
    sAudit = os.path.join(sProject, "results", dBook["root"] + "-audit.md")
    sEpub = os.path.join(sProject, "results", dBook["root"] + ".epub")
    if not os.path.exists(sAudit) or not os.path.exists(sEpub): return None
    with open(sAudit, encoding="utf-8-sig") as f: sText = f.read().replace("\r\n", "\n")
    oBuild = re.search(r"(?m)^- Build SHA-256: ([0-9a-f]{64})", sText)
    oEpub = re.search(r"(?m)^- EPUB SHA-256: ([0-9a-f]{64})", sText)
    if not oBuild or oBuild.group(1) != sKey or not re.search(r"(?m)^Ready to submit", sText): return None
    if not oEpub or oEpub.group(1) != hashlib.sha256(open(sEpub, "rb").read()).hexdigest(): return None
    # An edition's file must still be there too; a missing one builds the book again.
    for dEdition in editionRules(dBook["root"]):
        if not os.path.isfile(os.path.join(sProject, "results", dEdition["file"])): return None
    oWarnings = re.search(r"(?ms)^## Warnings\n\n(.*?)(?:\n## |\Z)", sText)
    lWarnings = [s[2:].strip() for s in (oWarnings.group(1).splitlines() if oWarnings else []) if s.startswith("- ")]
    return {"root": dBook["root"], "title": dBook["title"], "errors": [], "warnings": lWarnings, "ready": True,
            "size": os.path.getsize(sEpub), "kept": True}


def writeSummary(lAudits):
    """results\\Audit_Summary.md and .htm: one paragraph per book in title order, and the most common problems across all books."""
    lAudits = sorted(lAudits, key=lambda d: titleKey(d["title"]))
    iReady = sum(1 for d in lAudits if d.get("ready"))
    l = ["---", "title: \"MyBooks EPUB Audit Summary\"", "date: " + datetime.date.today().isoformat(), "lang: en-US", "---", ""]
    l += [plural(iReady, "book") + " of " + str(len(lAudits)) + " ready to submit.", "", "## Books", ""]
    for d in lAudits:
        sLink = "[" + mdEscape(d["title"]) + "](" + d["root"] + "-audit.htm)"
        sSize = (", " + "{:.2f}".format(d["size"] / 1048576.0) + " MB") if d.get("size") else ""
        l.append("- " + sLink + ": " + ("ready" if d.get("ready") else "not ready") + "; " + plural(len(d["errors"]), "error") + ", " + plural(len(d["warnings"]), "warning") + sSize + ".")
    dCommon = {}
    for d in lAudits:
        for s in d["errors"] + d["warnings"]:
            sKind = re.sub(r"\d[\d,.]*", "N", s.split(" -- ")[0].split(":")[0] if s.startswith(("Ace", "EPUBCheck")) else re.sub(r"\u201c[^\u201d]*\u201d", "...", s))[:140]
            dCommon.setdefault(sKind, set()).add(d["title"])
    l += ["", "## Problems found in more than one book", ""]
    lShared = sorted([(len(v), k) for k, v in dCommon.items() if len(v) > 1], reverse=True)
    l += ["- " + mdEscape(k) + " (" + plural(n, "book") + ")" for n, k in lShared] or ["None."]
    sMd = os.path.join(sProject, "results", "Audit_Summary.md")
    writeText(sMd, "\n".join(l) + "\n")
    run([dTools["pandoc"], sMd, "-s", "-o", sMd[:-3] + ".htm"])
    return iReady


# ---------------------------------------------------------------- main

def loadCatalog():
    """configs\\books.inix as {root: book}, every field present."""
    dRaw = readInix(os.path.join(sProject, "configs", "books.inix"))
    dCatalog = {}
    for sRoot, d in dRaw.items():
        if sRoot in ("excluded", inix.globalSectionName) or not d.get("title"): continue
        dCatalog[sRoot] = {"root": sRoot, "title": d.get("title", ""), "subtitle": d.get("subtitle", ""), "author": d.get("author", ""), "series": d.get("series", ""), "asin": d.get("asin", ""), "aiUse": d.get("aiUse", "").lower(), "aiTools": inixList(d.get("aiTools", "")), "readingGrade": int(d.get("readingGrade", "0") or 0), "formerKdpInix": d.get("formerKdpInix", ""), "sourceUrl": d.get("sourceUrl", ""), "formerNames": inixList(d.get("formerNames", "")), "externalProject": d.get("externalProject", ""), "externalEpub": d.get("externalEpub", ""), "externalBuild": d.get("externalBuild", ""), "allowMissingPictures": d.get("allowMissingPictures", ""), "tocDepth": d.get("tocDepth", ""), "importFrom": d.get("importFrom", ""), "publicDomain": d.get("publicDomain", "")}
    return dCatalog


def chosenBooks(dCatalog, lArgs):
    """The books named with --book, by the start of a root or title, or all books."""
    lWanted = [lArgs[i + 1].lower() for i, s in enumerate(lArgs[:-1]) if s.lstrip("-").lower() == "book"]
    if not lWanted: return list(dCatalog.values())
    return [d for d in dCatalog.values() if any(d["root"].lower().startswith(s) or titleKey(d["title"]).startswith(s) or d["title"].lower().startswith(s) for s in lWanted)]


def importNewer(dCatalog):
    """Brings a book's files from the folder its catalog entry names in importFrom, when the copy there is newer than the
    one here, logging each: the manuscript, bibliography, citation style and cover by the book's own name, and a
    book.css as <root>.css. WHY (8 October 2026): a book moved into a project from a folder of its own must not lose an
    edit made in that folder after the move, nor wait for a manual copy. Once the book is edited here, the copy here is
    newer and nothing is brought over. Returns the number of files brought over."""
    iBrought = 0
    for sRoot, dBook in dCatalog.items():
        sOld = os.path.expandvars(dBook.get("importFrom", "").strip())
        sNew = os.path.join(sProject, "books", sRoot)
        if not sOld or not os.path.isdir(sOld) or not os.path.isdir(sNew): continue
        iBook = 0
        for sFrom, sTo in [(sRoot + sExt, sRoot + sExt) for sExt in (".md", ".bib", ".csl", ".jpg")] + [("book.css", sRoot + ".css")]:
            sFromPath, sToPath = os.path.join(sOld, sFrom), os.path.join(sNew, sTo)
            if os.path.exists(sFromPath) and (not os.path.exists(sToPath) or os.path.getmtime(sFromPath) > os.path.getmtime(sToPath) + 60):
                shutil.copy2(sFromPath, sToPath)
                log("Brought over " + sFromPath + " to " + sToPath + ", newer than the copy here")
                iBook += 1
        if iBook: say("Brought over " + plural(iBook, "file") + " of " + dBook.get("title", sRoot) + " from " + sOld + ", newer than the copies here; see the log.")
        iBrought += iBook
    return iBrought


def main():
    global sLogPath, dSettings
    os.makedirs(os.path.join(sProject, "logs"), exist_ok=True)
    sLogPath = os.path.join(sProject, "logs", "MyBooks-buildBooks-" + sStamp + ".log")
    log("buildBooks started: " + os.path.abspath(__file__))
    log("python " + sys.version.replace("\n", " ") + " at " + sys.executable)
    log("platform " + platform.platform() + "; cwd " + os.getcwd() + "; project " + sProject)
    log("command line: " + subprocess.list2cmdline(sys.argv))
    lArgs = sys.argv[1:]
    sKitProblem = loadKit()
    if sKitProblem:
        say(sKitProblem)
        return 3
    try:
        dSettings = dict(c_dDefaults)
        dSettings.update(readInix(os.path.join(sProject, "configs", "buildBooks.inix")).get("build", {}))
        dCatalog = loadCatalog()
    except Exception as oError:
        say("Could not read configs\\buildBooks.inix or configs\\books.inix: " + str(oError))
        return 2
    for sKey in sorted(dSettings): log("setting " + sKey + " = " + dSettings[sKey].replace("\n", "; "))
    lBooks = sorted(chosenBooks(dCatalog, lArgs), key=lambda d: titleKey(d["title"]))
    if not lBooks:
        say("No book in configs\\books.inix matches what you named.")
        return 2
    say("buildBooks: " + plural(len(lBooks), "book") + " to build and audit.")
    if not ensurePandoc():
        say("No Pandoc " + dSettings["pandocMinimum"] + " or later was found, and winget could not install one; nothing was built. The log lists every copy found: " + sLogPath)
        return 3
    if not ensurePillow():
        say("Pillow could not be installed; nothing was built. See " + sLogPath)
        return 3
    say("Checking for EPUBCheck and Ace by DAISY.")
    if not ensureEpubcheck(): say("EPUBCheck is not available, so every book will be marked not ready. See the log.")
    if not ensureAce(): say("Ace by DAISY is not available, so every book will be marked not ready. See the log.")
    importNewer(dCatalog)
    if not ensureKindlePreviewer(): say("Kindle Previewer is not available, so Amazon's own checks will be skipped. See the log.")
    paths.clearTemp()
    tidyEarlierLayout(dCatalog)
    bGather = any(s.lstrip("-").lower() == "gather" for s in lArgs)
    dIndex = None
    lAudits = []
    for dBook in lBooks:
        dAudit = {"root": dBook["root"], "title": dBook["title"], "errors": [], "warnings": [], "pictures": []}
        try:
            if dBook.get("externalProject"):
                sKdpPath = os.path.join(sProject, "data", "books", dBook["root"] + ".inix")
                dKdp = readInix(sKdpPath) if os.path.exists(sKdpPath) else {}
                sEpub = buildExternal(dBook, dAudit)
                if "body" in dAudit: auditManuscript(dBook, dAudit, dCatalog)
                if sEpub:
                    auditEpub(sEpub, dAudit, dKdp)
                    runEpubcheck(sEpub, dAudit)
                    runAce(sEpub, dAudit)
                    runKindlePreviewer(sEpub, dAudit)
                bReady = writeAudit(dBook, dAudit)
                lAudits.append(dAudit)
                say(dBook["title"] + ": " + ("ready" if bReady else "not ready") + ", " + plural(len(dAudit["errors"]), "error") + ", " + plural(len(dAudit["warnings"]), "warning") + ".")
                continue
            sBookDir = os.path.join(sProject, "books", dBook["root"])
            os.makedirs(sBookDir, exist_ok=True)
            if bGather or not os.path.exists(os.path.join(sBookDir, "found.inix")):
                if dIndex is None:
                    say("Looking through the search folders for Word files, covers and images folders.")
                    dIndex = searchIndex()
                gatherBook(dBook, dIndex)
            if not os.path.exists(os.path.join(sBookDir, dBook["root"] + ".md")):
                sProblem = importSource(dBook)
                if sProblem:
                    dAudit["errors"].append("No manuscript: " + sProblem + ". Put the book's Word file in books\\" + dBook["root"] + "\\sources\\ or its Markdown as books\\" + dBook["root"] + "\\" + dBook["root"] + ".md.")
                    say(dBook["title"] + ": no manuscript or Word file found.")
                    writeAudit(dBook, dAudit)
                    lAudits.append(dAudit)
                    continue
            retireFormer(dBook)
            sKdpPath = os.path.join(sProject, "data", "books", dBook["root"] + ".inix")
            dKdp = readInix(sKdpPath) if os.path.exists(sKdpPath) else {}
            dAudit["buildKey"] = buildKey(dBook, sBookDir, dKdp)
            dKept = None if any(s.lstrip("-").lower() == "all" for s in lArgs) else keptAudit(dBook, dAudit["buildKey"])
            if dKept:
                lAudits.append(dKept)
                log(dBook["root"] + ": unchanged since its last build (fingerprint " + dAudit["buildKey"][:12] + "), so its EPUB and audit are kept")
                say(dBook["title"] + ": unchanged since its last build; kept.")
                continue
            if not dKdp: dAudit["warnings"].append("No KDP metadata in data\\books\\" + dBook["root"] + ".inix, so the EPUB has no description or keywords.")
            sEpub = buildEpub(dBook, dKdp, dAudit)
            auditManuscript(dBook, dAudit, dCatalog)
            if sEpub:
                auditEpub(sEpub, dAudit, dKdp)
                runEpubcheck(sEpub, dAudit)
                runAce(sEpub, dAudit)
                runKindlePreviewer(sEpub, dAudit)
                # EVERY EDITION, built from the same manuscript and checked by EPUBCheck; an edition that fails makes the
                # book not ready, since what goes to another store must be as sound as what goes to KDP.
                for dEdition in editionRules(dBook["root"]):
                    dEditionAudit = {"root": dBook["root"] + "-" + dEdition["name"], "errors": [], "warnings": []}
                    sEditionEpub = buildEpub(dBook, dKdp, dEditionAudit, dEdition)
                    if sEditionEpub: runEpubcheck(sEditionEpub, dEditionAudit)
                    for sProblem in dEditionAudit["errors"]: dAudit["errors"].append(dEdition["name"] + " edition: " + sProblem)
                    dAudit.setdefault("editions", []).append("%s: %s, %s" % (dEdition["name"], dEdition["file"], "built and checked" if sEditionEpub and not dEditionAudit["errors"] else plural(len(dEditionAudit["errors"]) or 1, "problem")))
        except Exception as oError:
            log("CRASH in " + dBook["root"] + ": " + traceback.format_exc())
            dAudit["errors"].append("The build stopped on this book: " + str(oError) + "; see the log.")
        bReady = writeAudit(dBook, dAudit)
        lAudits.append(dAudit)
        say(dBook["title"] + ": " + ("ready" if bReady else "not ready") + ", " + plural(len(dAudit["errors"]), "error") + ", " + plural(len(dAudit["warnings"]), "warning") + ".")
    iReady = writeSummary(lAudits)
    if lsUnreadable:
        say("Could not read " + plural(len(lsUnreadable), "file") + " the search found, probably because OneDrive is not running: " + "; ".join(lsUnreadable[:5]) + ". Start OneDrive, then run scripts\\buildBooks.cmd --gather.")
    say(plural(iReady, "book") + " of " + str(len(lAudits)) + " ready to submit. Read results\\Audit_Summary.htm; the log is " + sLogPath + ".")
    return 0 if iReady == len(lAudits) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        log("CRASH: " + traceback.format_exc())
        print("buildBooks stopped unexpectedly; the details are in " + sLogPath)
        sys.exit(4)
