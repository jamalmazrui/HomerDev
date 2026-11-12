r"""projectCycle.py -- the build and release steps of build_release for a project that is not an app: a
book project (MyBooks), a pages project (MyPages), and the collections of help guides (AppHelpGuides) and podcast
directories (PodcastDirectories). Part of the HomerDev kit (1.203.0).

    projectCycle build      what build_release's build step runs where a project has no build.cmd of its own
    projectCycle release    what its release step runs where a project has no release.cmd of its own

ONE CYCLE FOR EVERY KIND OF HOMER PROJECT. In an app's folder, "build_release" runs build, tidy, push and release.
It now does the same in each of these, on any drive and at any depth, with no build or release script written for
any one of them: kind.py's projectRole says what the folder is for, and this script does that role's step. tidy and
push are the kit's own, the same as an app's.

    role       build                                               release
    books      buildBooks: builds what changed                     kdpSubmit: submits what changed
    guides     the app-help-guide skill's buildGuide --build       nothing more: the push published the guides
    pages      nothing to compile: the pages are Markdown          post: posts each page that changed
    podcasts   fixPages --changed: each changed page's .htm        nothing more: the push published the pages

THE BUILD REFRESHES THE KIT'S TOOLS INTO scripts, as an app's build does with its kitTools, so tidy, push and this
script itself work on the project above them: a kit tool takes the folder above its scripts folder as its project.
A tool is copied only when the kit's differs, and every copy is logged.

WORK IS CLEARED FIRST. The build empties the project's work folder, the Homer scratch folder (w; t is templates),
and deletes a temp folder an older version left, since every new session may delete what an earlier one left there.

THE LOG is logs\<Project>-<step>-yyyyMMdd-HHmmss.log, UTF-8 with a byte order mark and Windows line endings: the
environment, the role and why, every copy, every command with its exit code. The console says one line a stage.
"""

import datetime, filecmp, io, os, platform, re, shutil, subprocess, sys

lsCommonTools = ["check.cmd", "check.py", "fixEncoding.cmd", "fixEncoding.py", "kind.cmd", "kind.py", "projectCycle.cmd",
                 "projectCycle.py", "push.cmd", "tidy.cmd", "tidy.py", "unpushed.cmd", "unpushed.py"]
dRoleTools = {
    "books": ["buildBooks.cmd", "buildBooks.py", "kdpBooks.cmd", "kdpBooks.py", "kdpFetch.cmd", "kdpFetch.py",
              "kdpSubmit.cmd", "kdpSubmit.py", "kdpUpdate.cmd", "kdpUpdate.py", "testKdpUpdate.py"],
    "collection": ["fixPages.cmd", "fixPages.py"],
    "guides": ["fixPages.cmd", "fixPages.py"],
    "pages": [],
    "podcasts": ["fixPages.cmd", "fixPages.py"]}
lsRoles = sorted(dRoleTools)
dState = {"fLog": None}


def log(sText):
    """One stamped line in this run's log."""
    if dState["fLog"] is None: return False
    dState["fLog"].write(datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3] + " " + sText + "\n")
    dState["fLog"].flush()
    return True


def say(sText):
    """One short line for the console, and the same in the log."""
    print(sText, flush=True)
    return log("SAY " + sText)


def projectFolder():
    """The project: the folder named on the command line; else the folder above this script when it sits in a
    project's scripts folder; else the current folder, as when build_release runs the kit's own copy."""
    lsFolders = [s for s in sys.argv[2:] if not s.startswith("-")]
    if lsFolders: return os.path.abspath(lsFolders[0])
    sHere = os.path.dirname(os.path.abspath(__file__))
    sAbove = os.path.dirname(sHere)
    if os.path.basename(sHere).lower() == "scripts" and not os.path.isfile(os.path.join(sAbove, "HomerDev.cs")): return sAbove
    return os.getcwd()


def loadKind(sRoot):
    """The kit's kind.py: beside this script, else the kit the project finds."""
    sHere = os.path.dirname(os.path.abspath(__file__))
    if sHere not in sys.path: sys.path.insert(0, sHere)
    import kind
    return kind


dRunEnvironment = {}   # names added to every command's environment; the kit's own folder as HomerDev, set in main


def run(lsCommand, sRoot):
    """Runs one command in the project, logs it with its exit code, and returns the code."""
    log("RUN " + " ".join('"%s"' % s if " " in s else s for s in lsCommand))
    try:
        # No __pycache__ left in the project's scripts, and HomerDev naming the kit this cycle found (1.209.0), so a
        # project script that looks for the kit -- PodcastDirectories' addShows -- finds the same one, at any depth.
        dEnvironment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", **dRunEnvironment)
        oRun = subprocess.run(lsCommand, cwd=sRoot, env=dEnvironment)
        iCode = oRun.returncode
    except Exception as oError:
        log("COULD NOT RUN: %s" % oError)
        iCode = 1
    log("EXIT %d" % iCode)
    return iCode


def clearWork(sRoot):
    """Empties the project's work folder and deletes a temp folder left by an older version."""
    iRemoved = 0
    for sFolder in (os.path.join(sRoot, "work"), os.path.join(sRoot, "temp")):
        if not os.path.isdir(sFolder): continue
        for sName in os.listdir(sFolder):
            sPath = os.path.join(sFolder, sName)
            try:
                if os.path.isdir(sPath): shutil.rmtree(sPath)
                else: os.remove(sPath)
                iRemoved += 1
                log("CLEARED %s" % sPath)
            except OSError as oError:
                log("COULD NOT CLEAR %s: %s" % (sPath, oError))
        if os.path.basename(sFolder) == "temp":
            try:
                os.rmdir(sFolder)
                log("REMOVED the old temp folder: scratch is work now")
            except OSError as oError:
                log("COULD NOT REMOVE %s: %s" % (sFolder, oError))
    return iRemoved


def refreshTools(sRoot, sRole):
    """Copies each kit tool this role uses into the project's scripts folder when the kit's copy differs."""
    sKitScripts = os.path.dirname(os.path.abspath(__file__))
    sScripts = os.path.join(sRoot, "scripts")
    if os.path.normcase(sKitScripts) == os.path.normcase(sScripts): return 0
    os.makedirs(sScripts, exist_ok=True)
    iCopied = 0
    for sName in sorted(lsCommonTools + dRoleTools.get(sRole, []), key=str.lower):
        sSource, sTarget = os.path.join(sKitScripts, sName), os.path.join(sScripts, sName)
        if not os.path.isfile(sSource):
            log("NOT IN THE KIT: %s" % sName)
            continue
        if os.path.isfile(sTarget) and filecmp.cmp(sSource, sTarget, shallow=False): continue
        shutil.copy2(sSource, sTarget)
        iCopied += 1
        log("COPIED %s -> %s" % (sSource, sTarget))
    return iCopied


# A COLLECTION'S RepoFiles.txt WHEN IT HAS NONE (1.203.0). tidy refuses to guess what belongs to a project with no
# list, and a collection's repository is its content: its pages, their .htm, its own documents and its harvesters.
# Written once, logged, and never over a list the project already has.
sCollectionRepoFiles = """# RepoFiles.txt -- what push puts on GitHub for this collection: its pages, each readable in a browser.
# Written by the kit's projectCycle (1.208.0) because there was none; edit it as the collection needs.
*.htm
.gitignore
"""
sCollectionLocalFiles = """# LocalFiles.txt -- what belongs to this collection on this disk, but never in the repository.
data/harvests/
results/
"""


def trackedRepoFiles(sRoot):
    """THE FIRST RepoFiles.txt OF A REPOSITORY IS WHAT GIT ALREADY TRACKS (1.206.0), so writing the list never changes
    what push sends: AppHelpGuides' repository holds its .htm pages and not its .md sources, and a list naming *.md
    would have pushed 270 files nobody asked to publish. A top-level extension shared by five files or more becomes a
    pattern such as *.htm; a folder becomes folder/. Returns the text, or "" when this is not a repository."""
    if not os.path.isdir(os.path.join(sRoot, ".git")): return ""
    try: oRun = subprocess.run(["git", "ls-files"], cwd=sRoot, capture_output=True, text=True, errors="replace")
    except Exception: return ""
    if oRun.returncode != 0: return ""
    dExtensions, setFolders, lsFiles = {}, set(), []
    for sPath in oRun.stdout.splitlines():
        if not os.path.exists(os.path.join(sRoot, sPath)): continue   # retired just now, or deleted: not to be pushed again
        if "/" in sPath: setFolders.add(sPath.split("/")[0] + "/")
        else:
            lsFiles.append(sPath)
            dExtensions.setdefault(os.path.splitext(sPath)[1].lower(), []).append(sPath)
    lsLines = []
    for sExtension, lsNames in dExtensions.items():
        lsLines += ["*" + sExtension] if sExtension and len(lsNames) >= 5 else lsNames
    # ONLY WHAT GIT ALREADY TRACKS (1.208.0): version 1.206.0 also named LocalFiles.txt, RepoFiles.txt and scripts/,
    # which push would then have added. Those are local; localFilesText names them.
    lsLines += sorted(setFolders) + [".gitignore"]
    lsUnique = sorted(set(lsLines), key=str.lower)
    return "# RepoFiles.txt -- what push puts on GitHub. Written by the kit's projectCycle (1.206.0) from what git\n# already tracked here, so push sends nothing new; edit it as the collection needs.\n" + "\n".join(lsUnique) + "\n"


def localFilesText(sRoot):
    """A collection's LocalFiles.txt: what belongs on this disk but never in the repository (1.208.0).

    THE SOURCES STAY HOME. A collection's pages are built from .md sources beside them; when git tracks the .htm and not
    the .md, the .md are local, and must be named so, or tidy takes them for strays. Version 1.206.0 named them nowhere,
    and tidy moved all 283 of AppHelpGuides' sources into notes\\drafts."""
    lsLines = ["data/", "LocalFiles.txt", "RepoFiles.txt", "results/", "scripts/"]
    bTop = any(s.lower().endswith(".md") for s in os.listdir(sRoot))
    if bTop or os.path.isdir(os.path.join(sRoot, "notes", "drafts")): lsLines.insert(0, "*.md")
    return "# LocalFiles.txt -- what belongs to this collection on this disk, but never in the repository.\n# Written by the kit's projectCycle (1.208.0).\n" + "\n".join(lsLines) + "\n"


def restoreDraftedSources(sRoot):
    """PUTS BACK THE SOURCES TIDY TOOK FOR STRAYS (1.208.0). A .md in notes\\drafts whose .htm is at the collection's
    top, with no .md there, is that page's source, moved by tidy under 1.206.0's lists; it goes back to the top,
    logged. Anything else in drafts stays."""
    sDrafts = os.path.join(sRoot, "notes", "drafts")
    if not os.path.isdir(sDrafts): return 0
    iBack = 0
    for sName in sorted(os.listdir(sDrafts)):
        if not sName.lower().endswith(".md"): continue
        sStem = sName[:-3]
        if os.path.isfile(os.path.join(sRoot, sStem + ".htm")) and not os.path.exists(os.path.join(sRoot, sName)):
            shutil.move(os.path.join(sDrafts, sName), os.path.join(sRoot, sName))
            log("RESTORED %s from notes\\drafts to the top: its page is there" % sName)
            iBack += 1
    if iBack: say("Put %d page source%s back beside %s page%s, from notes\\drafts." % (iBack, "" if iBack == 1 else "s", "its" if iBack == 1 else "their", "" if iBack == 1 else "s"))
    return iBack


# A PODCAST COLLECTION'S OLD COPIES (1.209.0): harvestShows and buildDirectory are the kit's podcast-directory skill
# scripts, which scripts\\addShows runs from the kit; postPage posts a one-page project and would publish whichever .md
# came first; Show_Harvester_ReadMe documented the old copies. All go to notes\\retired.
lsPodcastRetired = ["builddirectory.cmd", "builddirectory.py", "harvestshows.cmd", "harvestshows.py", "postpage.cmd",
                    "postpage.ps1", "show_harvester_readme.htm", "show_harvester_readme.md"]


def retireNamed(sRoot, lsNames, sWhy):
    """Moves each top-level file named (lower case) into notes\\retired, logged with the reason."""
    iMoved = 0
    for sName in sorted(os.listdir(sRoot)):
        if sName.lower() not in lsNames or not os.path.isfile(os.path.join(sRoot, sName)): continue
        sFolder = os.path.join(sRoot, "notes", "retired")
        os.makedirs(sFolder, exist_ok=True)
        sTo, iNext = os.path.join(sFolder, sName), 2
        while os.path.exists(sTo):
            sTo = os.path.join(sFolder, "%s-%d%s" % (os.path.splitext(sName)[0], iNext, os.path.splitext(sName)[1]))
            iNext += 1
        shutil.move(os.path.join(sRoot, sName), sTo)
        log("RETIRED %s -> %s: %s" % (sName, sTo, sWhy))
        iMoved += 1
    if iMoved: say("Retired %d old cop%s from the top." % (iMoved, "y" if iMoved == 1 else "ies"))
    return iMoved


def showsToAdd(sRoot):
    """The sections of data\\addShows.inix whose page, <Section>.md, is not at the top yet."""
    sPath = os.path.join(sRoot, "data", "addShows.inix")
    if not os.path.isfile(sPath): return []
    sText = io.open(sPath, "rb").read().decode("utf-8-sig", "replace")
    return [s for s in re.findall(r"(?m)^\[([^\]]+)\]", sText) if not os.path.isfile(os.path.join(sRoot, s + ".md"))]


def retireTopKitTools(sRoot, sRole):
    """A COPY OF A KIT TOOL AT A COLLECTION'S TOP GOES TO notes\\retired (1.206.0): the build refreshes the tool into
    scripts, and the copy at the top only drifts (fixPages at PodcastDirectories' top, in the first audit)."""
    lsRetired = []
    for sName in sorted(set(lsCommonTools + dRoleTools.get(sRole, []) + ["cleanFeedback.cmd", "cleanFeedback.py"]), key=str.lower):
        sPath = os.path.join(sRoot, sName)
        if not os.path.isfile(sPath): continue
        sFolder = os.path.join(sRoot, "notes", "retired")
        os.makedirs(sFolder, exist_ok=True)
        sTo, iNext = os.path.join(sFolder, sName), 2
        while os.path.exists(sTo):
            sTo = os.path.join(sFolder, "%s-%d%s" % (os.path.splitext(sName)[0], iNext, os.path.splitext(sName)[1]))
            iNext += 1
        shutil.move(sPath, sTo)
        log("RETIRED %s -> %s: the build refreshes it into scripts" % (sPath, sTo))
        lsRetired.append(sName)
    if lsRetired: say("Retired %d kit tool cop%s from the top: %s." % (len(lsRetired), "y" if len(lsRetired) == 1 else "ies", ", ".join(lsRetired)))
    return lsRetired


def ensureCollectionLists(sRoot):
    """Writes a collection's RepoFiles.txt and LocalFiles.txt when they are missing."""
    for sName, sText in (("RepoFiles.txt", trackedRepoFiles(sRoot) or sCollectionRepoFiles), ("LocalFiles.txt", localFilesText(sRoot))):
        sPath = os.path.join(sRoot, sName)
        if os.path.isfile(sPath): continue
        io.open(sPath, "wb").write(b"\xef\xbb\xbf" + sText.replace("\n", "\r\n").encode("utf-8"))
        say("Wrote %s, since tidy needs one to know what belongs here." % sName)
    return True


def findPagesProject(sRoot, sKit):
    """The pages project beside this one or beside the kit (MyPages), or ""."""
    for sParent in (os.path.dirname(sRoot), os.path.dirname(sKit)):
        sCandidate = os.path.join(sParent, "MyPages")
        if os.path.isdir(os.path.join(sCandidate, "pages")): return sCandidate
    return ""


def settleBooks(sRoot, sKit):
    """MyBooks keeps the Homer tree (1.212.0), each move logged, nothing deleted that holds work:

    ONE SOURCE PER PAGE. MyBooks.md, its .htm, _config.yml and configs\\post.inix were MyBooks' own copy of its
    directory page, older than the one MyPages keeps and posts (pages\\MyBooks), and posting either would overwrite the
    other. When MyPages holds that page, MyBooks' copy goes to notes\\retired. kind.py counts MyBooks as a page project
    by its books catalog, so it stays unpushable without the page.

    TESTS LIVE IN scripts, as testKdpUpdate.py does. A file in a top-level tests folder that loads a script present in
    scripts moves there; one whose script is gone (test_createDropboxFolder.py tested a script that is in neither
    MyBooks nor the kit) goes to notes\\retired\\tests."""
    sName = os.path.basename(sRoot.rstrip("\\/"))
    sRetired = os.path.join(sRoot, "notes", "retired")
    sPages = findPagesProject(sRoot, sKit)
    if sPages and os.path.isfile(os.path.join(sPages, "pages", sName, sName + ".md")):
        for sRelative in (sName + ".md", sName + ".htm", "_config.yml", os.path.join("configs", "post.inix")):
            sPath = os.path.join(sRoot, sRelative)
            if not os.path.isfile(sPath): continue
            sTo = os.path.join(sRetired, sRelative.replace(os.sep, "-"))
            os.makedirs(sRetired, exist_ok=True)
            if os.path.exists(sTo): sTo = os.path.splitext(sTo)[0] + "-2" + os.path.splitext(sTo)[1]
            shutil.move(sPath, sTo)
            log("RETIRED %s -> %s: MyPages keeps and posts this page (%s)" % (sPath, sTo, os.path.join(sPages, "pages", sName)))
            say("Retired MyBooks' copy of its page, %s: MyPages keeps and posts it." % sRelative)
    sTests = os.path.join(sRoot, "tests")
    if os.path.isdir(sTests):
        for sFile in sorted(os.listdir(sTests)):
            sPath = os.path.join(sTests, sFile)
            if sFile == "__pycache__":
                shutil.rmtree(sPath, ignore_errors=True)
                continue
            sText = io.open(sPath, "rb").read().decode("utf-8", "replace") if os.path.isfile(sPath) else ""
            lsTargets = re.findall(r"'scripts'\s*/\s*'([^']+\.py)'|scripts[\\/]+([A-Za-z0-9_]+\.py)", sText)
            lsTargets = [a or b for a, b in lsTargets]
            bLive = bool(lsTargets) and all(os.path.isfile(os.path.join(sRoot, "scripts", s)) for s in lsTargets)
            sFolder = os.path.join(sRoot, "scripts") if bLive else os.path.join(sRetired, "tests")
            os.makedirs(sFolder, exist_ok=True)
            shutil.move(sPath, os.path.join(sFolder, sFile))
            log("MOVED %s -> %s: %s" % (sPath, sFolder, "its script is in scripts" if bLive else "the script it tests is gone"))
        try:
            os.rmdir(sTests)
            say("Moved the tests folder's files: tests live in scripts, and orphans go to notes\\retired\\tests.")
        except OSError as oError: log("tests folder left: %s" % oError)
    return True


def build(sRoot, sRole, sKit):
    """The role's build."""
    # Python's cache in scripts is remade when needed and never belongs to the project (1.212.0).
    shutil.rmtree(os.path.join(sRoot, "scripts", "__pycache__"), ignore_errors=True)
    if sRole == "books": settleBooks(sRoot, sKit)
    if sRole in ("collection", "guides", "podcasts"):
        restoreDraftedSources(sRoot)
        retireTopKitTools(sRoot, sRole)
        ensureCollectionLists(sRoot)
    iCleared = clearWork(sRoot)
    iCopied = refreshTools(sRoot, sRole)
    say("Work cleared: %d item%s. Kit tools refreshed: %d." % (iCleared, "" if iCleared == 1 else "s", iCopied))
    sScripts = os.path.join(sRoot, "scripts")
    if sRole == "books": return run([sys.executable, os.path.join(sScripts, "buildBooks.py")], sRoot)
    if sRole == "guides":
        sBuilder = os.path.join(sKit, ".claude", "skills", "app-help-guide", "scripts", "buildGuide.py")
        if not os.path.isfile(sBuilder):
            say("The kit's buildGuide.py was not found at %s, so no guide was built." % sBuilder)
            return 1
        return run([sys.executable, sBuilder, "--build", sRoot], sRoot)
    if sRole == "podcasts":
        retireNamed(sRoot, lsPodcastRetired, "the kit's podcast-directory skill does this now")
        # NEW SHOWS FIRST (1.209.0): a show listed in data\\addShows.inix without a page is found, fetched and built by
        # the collection's own scripts\\addShows, before the pages are finished. A show Apple's search cannot match is
        # logged by addShows and does not stop the cycle; only its option or crash codes (2, 4) do.
        lsNew = showsToAdd(sRoot)
        sAdd = os.path.join(sScripts, "addShows.py")
        if lsNew and os.path.isfile(sAdd):
            say("Adding %d show%s: %s." % (len(lsNew), "" if len(lsNew) == 1 else "s", ", ".join(lsNew)))
            iAdd = run([sys.executable, sAdd], sRoot)
            if iAdd == 1: say("Some shows could not be found or built; the addShows log names them. The rest are in.")
            elif iAdd != 0: return iAdd
    if sRole in ("collection", "podcasts"): return run([sys.executable, os.path.join(sScripts, "fixPages.py"), sRoot, "--changed"], sRoot)
    if sRole == "pages":
        sPages = os.path.join(sRoot, "pages")
        iPages = len([s for s in os.listdir(sPages) if os.path.isdir(os.path.join(sPages, s))]) if os.path.isdir(sPages) else 0
        # EVERY DIRECTORY'S SUBTITLE STARTS "A Directory of <number>" (1.213.0, his rule of 12 November 2026): the
        # mark that tells a free directory from a commercial book on the same subject, such as the Blind Vibe Coding
        # directory and the book. A page whose subtitle drifts stops the build, so it is never posted.
        lsDrift = []
        for sPage in sorted(os.listdir(sPages)) if os.path.isdir(sPages) else []:
            sSource = os.path.join(sPages, sPage, sPage + ".md")
            if not os.path.isfile(sSource): continue
            sHead = io.open(sSource, "rb").read(4000).decode("utf-8-sig", "replace")
            oSubtitle = re.search(r'(?m)^subtitle:\s*"?(.*?)"?\s*$', sHead)
            sSubtitle = oSubtitle.group(1) if oSubtitle else ""
            if not re.match(r"A Directory of [\d,]+ ", sSubtitle): lsDrift.append("%s (%s)" % (sPage, sSubtitle or "no subtitle"))
            log("SUBTITLE %s: %s" % (sPage, sSubtitle or "none"))
        if lsDrift:
            say("Each directory's subtitle must start \"A Directory of\" and its number; these do not: " + "; ".join(lsDrift) + ".")
            return 1
        say("Pages: %d. Nothing to compile: each page is Markdown, and release posts the ones that changed." % iPages)
        return 0
    say("projectCycle has no build for a project whose role is %s; an app or the kit has its own build." % sRole)
    return 1


def release(sRoot, sRole):
    """The role's release."""
    sScripts = os.path.join(sRoot, "scripts")
    if sRole == "books": return run([sys.executable, os.path.join(sScripts, "kdpSubmit.py")], sRoot)
    if sRole == "pages":
        for sName in ("post.py", "post.cmd"):
            sPost = os.path.join(sScripts, sName)
            if os.path.isfile(sPost):
                return run([sys.executable, sPost] if sName.endswith(".py") else ["cmd", "/c", sPost], sRoot)
        say("There is no scripts\\post here, so no page was posted.")
        return 1
    if sRole in ("collection", "guides", "podcasts"):
        say("Released: the push published the collection, so there is nothing more to do.")
        return 0
    say("projectCycle has no release for a project whose role is %s; an app or the kit has its own release." % sRole)
    return 1


def main():
    sStep = (sys.argv[1] if len(sys.argv) > 1 else "").lower()
    sRoot = projectFolder()
    sProject = os.path.basename(sRoot.rstrip("\\/")) or "Homer"
    sLogs = os.path.join(sRoot, "logs")
    os.makedirs(sLogs, exist_ok=True)
    sStamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    sLogPath = os.path.join(sLogs, "%s-%s-%s.log" % (sProject, sStep or "cycle", sStamp))
    iSame = 2
    while os.path.exists(sLogPath):
        sLogPath = os.path.join(sLogs, "%s-%s-%s-%d.log" % (sProject, sStep or "cycle", sStamp, iSame))
        iSame += 1
    dState["fLog"] = io.open(sLogPath, "w", encoding="utf-8-sig", newline="\r\n")
    log("projectCycle.py (HomerDev 1.203.0) step %s" % (sStep or "none"))
    log("script %s" % os.path.abspath(__file__))
    log("Python %s at %s on %s" % (platform.python_version(), sys.executable, platform.platform()))
    log("working directory %s; command line %s" % (os.getcwd(), " ".join(sys.argv)))
    iResult = 1
    try:
        if sStep not in ("build", "release"):
            say("Say which step: projectCycle build, or projectCycle release.")
            return 2
        oKind = loadKind(sRoot)
        sRole, sWhy = oKind.projectRole(sRoot)
        sKit = oKind.findKit([sRoot]) or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log("project %s; role %s because %s; kit %s" % (sRoot, sRole, sWhy, sKit))
        dRunEnvironment["HomerDev"] = sKit
        say("%s: %s for %s." % (sProject, sStep, sRole))
        iResult = build(sRoot, sRole, sKit) if sStep == "build" else release(sRoot, sRole)
        say("%s %s." % (sStep.capitalize(), "finished" if iResult == 0 else "failed; its log says why: " + sLogPath))
        return iResult
    except Exception:
        import traceback
        log("CRASH " + traceback.format_exc())
        say("projectCycle stopped with an error; its log has the details: " + sLogPath)
        return 2
    finally:
        log("RUN ENDED exit %d" % iResult)
        dState["fLog"].close()


if __name__ == "__main__":
    sys.exit(main())
