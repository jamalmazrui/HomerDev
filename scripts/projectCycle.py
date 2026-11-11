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

import datetime, filecmp, io, os, platform, shutil, subprocess, sys

lsCommonTools = ["check.cmd", "check.py", "fixEncoding.cmd", "fixEncoding.py", "kind.cmd", "kind.py", "projectCycle.cmd",
                 "projectCycle.py", "push.cmd", "tidy.cmd", "tidy.py", "unpushed.cmd", "unpushed.py"]
dRoleTools = {
    "books": ["buildBooks.cmd", "buildBooks.py", "kdpBooks.cmd", "kdpBooks.py", "kdpFetch.cmd", "kdpFetch.py",
              "kdpSubmit.cmd", "kdpSubmit.py", "kdpUpdate.cmd", "kdpUpdate.py"],
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


def run(lsCommand, sRoot):
    """Runs one command in the project, logs it with its exit code, and returns the code."""
    log("RUN " + " ".join('"%s"' % s if " " in s else s for s in lsCommand))
    try:
        dEnvironment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")   # no __pycache__ left in the project's scripts
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
sCollectionRepoFiles = """# RepoFiles.txt -- what push puts on GitHub for this collection. Written by the kit's projectCycle (1.203.0)
# because there was none; edit it as the collection needs.
*.md
*.htm
.gitignore
LocalFiles.txt
RepoFiles.txt
data/linkFixes.inix
scripts/
"""
sCollectionLocalFiles = """# LocalFiles.txt -- what belongs to this collection on this disk, but never in the repository.
data/harvests/
results/
"""


def ensureCollectionLists(sRoot):
    """Writes a collection's RepoFiles.txt and LocalFiles.txt when they are missing."""
    for sName, sText in (("RepoFiles.txt", sCollectionRepoFiles), ("LocalFiles.txt", sCollectionLocalFiles)):
        sPath = os.path.join(sRoot, sName)
        if os.path.isfile(sPath): continue
        io.open(sPath, "wb").write(b"\xef\xbb\xbf" + sText.replace("\n", "\r\n").encode("utf-8"))
        say("Wrote %s, since tidy needs one to know what belongs here." % sName)
    return True


def build(sRoot, sRole, sKit):
    """The role's build."""
    if sRole in ("collection", "guides", "podcasts"): ensureCollectionLists(sRoot)
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
    if sRole in ("collection", "podcasts"): return run([sys.executable, os.path.join(sScripts, "fixPages.py"), sRoot, "--changed"], sRoot)
    if sRole == "pages":
        sPages = os.path.join(sRoot, "pages")
        iPages = len([s for s in os.listdir(sPages) if os.path.isdir(os.path.join(sPages, s))]) if os.path.isdir(sPages) else 0
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
