r"""media.py -- part of the shared Homer toolkit.

FINDING A SHARED TOOL -- PANDOC, EXIFTOOL, FFMPEG, MPV, JAVA, NODE -- AND
CHOOSING THE RIGHT COPY WHEN A MACHINE HAS SEVERAL.

THIS MODULE IS THE FINDING HALF OF CSharp\Media.cs, IN PYTHON. Same names for
the same jobs: needsShell, findTool, findInstalled, searchLog, and the same
table of official folders. What Media.cs does with ExifTool afterwards (reading
tags) is not ported; a Python program that needs it runs the tool itself.

WHY IT EXISTS (1.56.0). Every Python and cmd script in the kit found Pandoc by
taking the first copy on the PATH. On the author's machine that was
C:\bin\pandoc.exe, version 2.19.2, while a current Pandoc sat in Program Files.
MyBooks' build asked winget to upgrade, winget truthfully answered that the
machine-wide copy was current, and the build looked at the old copy again and
gave up. Media.cs had met the same folder before -- C:\bin\mpv.cmd hid the real
player -- and had already learnt the answer: ask the official folder first,
because it is certain, and the PATH last, because a process's PATH is only as
current as the moment it started.

TWO WAYS TO ASK.

    findInstalled(sName)     the first copy in Media.cs's order: official
                             folders, then the usual install folders, then the
                             PATH. Real programs (.exe, .com) are preferred to
                             wrappers (.cmd, .bat). Use it when any working
                             copy will do.

    newestInstalled(sName, ...)  EVERY copy in all those places, each one RUN
                             for its version, and the newest chosen -- the rule
                             Media.cs's exifToolProgram follows. Give a minimum
                             when an older version would fail, as Pandoc 2.x
                             fails a book build that needs --split-level. Use
                             it whenever a version matters.

Both leave a plain account of where they looked in searchLog(), and
newestInstalled also fills dLast with what it saw, so a caller can say which copy
it chose and warn when an older one comes first on the PATH, where other
programs will still pick it up.

Nothing here raises. A tool that cannot be found comes back as "".

Usage:

    import media
    sPandoc = media.pandocProgram("3.1")     # newest Pandoc at 3.1 or later
    if not sPandoc: print(media.searchLog())
    sNote = media.shadowNote()               # "" unless an older copy is first on the PATH

From a Command Prompt, for checking a machine by hand:

    python media.py pandoc            every Pandoc, its version, and the one chosen
    python media.py pandoc 3.1        the same, with a minimum version
"""

import glob, os, re, subprocess, sys

c_dOfficialFolders = {
    "exiftool": ["ExifTool"],
    "ffmpeg": ["ffmpeg"],
    "ffprobe": ["ffmpeg"],
    "java": ["Microsoft\\jdk-*\\bin", "Eclipse Adoptium\\*\\bin", "Java\\*\\bin"],
    "magick": ["ImageMagick"],
    "mpv": ["MPV Player", "mpv", "MPV Media Player", "mpv.net"],
    "node": ["nodejs"],
    "npm": ["nodejs"],
    "pandoc": ["Pandoc"],
    "yt-dlp": ["yt-dlp"],
}
c_dUserFolders = {"pandoc": ["Pandoc"]}
c_iVersionTimeout = 30
c_lsPrograms = [".exe", ".com"]
c_lsRunnable = [".exe", ".com", ".cmd", ".bat"]

bWindows = os.name == "nt"
dLast = {}
sSearchLog = ""


def needsShell(sProgram):
    """True for a .cmd or .bat, which must be run through the command interpreter."""
    return os.path.splitext(sProgram)[1].lower() in (".cmd", ".bat")


def searchLog():
    """Where the last search looked, and what it found, for a log or for the person."""
    return sSearchLog


def extensionsFor(lsExtensions):
    """The file endings to try: on Windows the ones given, elsewhere the bare name."""
    return list(lsExtensions) if bWindows else [""]


def pathCopies(sName, lsExtensions=None):
    """Every copy of a tool on the PATH, in PATH order, each folder read directly."""
    lsFound = []
    for sDir in os.environ.get("PATH", "").split(os.pathsep):
        sDir = sDir.strip().strip('"')
        if not sDir: continue
        for sExt in extensionsFor(lsExtensions or c_lsRunnable):
            sTry = os.path.join(sDir, sName + sExt)
            if os.path.isfile(sTry) and (bWindows or os.access(sTry, os.X_OK)): lsFound.append(sTry)
    return lsFound


def findTool(sName):
    """The first runnable copy on the PATH, as Media.cs's findTool answers."""
    lsFound = pathCopies(sName)
    return lsFound[0] if lsFound else ""


def placeCopies(sName, lsExtensions):
    """Every copy in the places installers put tools, official folders first: Program Files under each name the
    installer is known to use, then a folder named for the tool, the user's Programs and Pandoc folders, winget's
    shim folder, and the folder winget unpacks portable packages into."""
    lsRoots = [os.environ.get(s, "") for s in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432")]
    lsRoots = [s for i, s in enumerate(lsRoots) if s and s not in lsRoots[:i]]
    sLocal = os.environ.get("LOCALAPPDATA", "")
    lsPatterns = []
    for sRoot in lsRoots:
        for sFolder in c_dOfficialFolders.get(sName.lower(), []) + [sName]:
            for sExt in extensionsFor(lsExtensions):
                lsPatterns += [os.path.join(sRoot, sFolder, sName + sExt), os.path.join(sRoot, sFolder, "bin", sName + sExt)]
    if sLocal:
        for sFolder in c_dUserFolders.get(sName.lower(), []) + [os.path.join("Programs", sName)]:
            for sExt in extensionsFor(lsExtensions): lsPatterns.append(os.path.join(sLocal, sFolder, sName + sExt))
        for sExt in extensionsFor(lsExtensions): lsPatterns.append(os.path.join(sLocal, "Microsoft", "WinGet", "Links", sName + sExt))
        for sExt in extensionsFor(lsExtensions): lsPatterns.append(os.path.join(sLocal, "Microsoft", "WinGet", "Packages", "*" + sName + "*", "**", sName + sExt))
    lsFound = []
    for sPattern in lsPatterns:
        lsFound += sorted(glob.glob(sPattern, recursive=True)) if any(c in sPattern for c in "*?[") else ([sPattern] if os.path.isfile(sPattern) else [])
    return lsFound


def unique(lsPaths):
    """Paths without repeats, compared as Windows compares them, first occurrence kept."""
    lsOut, setSeen = [], set()
    for sPath in lsPaths:
        sKey = os.path.normcase(os.path.abspath(sPath))
        if sKey in setSeen: continue
        setSeen.add(sKey)
        lsOut.append(sPath)
    return lsOut


def findInstalled(sName):
    """The first working place for a tool in Media.cs's order -- official folders before the PATH -- trying real
    programs before wrappers."""
    global sSearchLog
    for lsExtensions in (c_lsPrograms, c_lsRunnable):
        lsFound = unique(placeCopies(sName, lsExtensions) + pathCopies(sName, lsExtensions))
        if lsFound:
            sSearchLog = "Looking for %s: found %s" % (sName, lsFound[0])
            return lsFound[0]
    sSearchLog = "Looking for %s: not in Program Files, the user's Programs, winget's folders or the PATH" % sName
    return ""


def versionTuple(sText):
    """The first dotted number in some text, as a tuple for comparing: 'pandoc 3.6.2' gives (3, 6, 2). A plain whole
    number counts only when the text holds no dotted one, so a minimum of '11' reads as (11,)."""
    oMatch = re.search(r"(\d+(?:\.\d+)+)", sText or "") or re.search(r"(\d+)", sText or "")
    return tuple(int(s) for s in oMatch.group(1).split(".")) if oMatch else ()


def versionOf(sProgram, lsArgs):
    """(version tuple, first line of output) from running a copy, or ((), reason) when it will not run."""
    try:
        oResult = subprocess.run([sProgram] + list(lsArgs), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=c_iVersionTimeout, shell=needsShell(sProgram))
        sOut = ((oResult.stdout or "") + (oResult.stderr or "")).strip()
        sFirst = sOut.splitlines()[0].strip() if sOut else ""
        if oResult.returncode != 0 and not versionTuple(sFirst): return (), "exit code %d" % oResult.returncode
        return versionTuple(sOut), sFirst
    except Exception as oError:
        return (), str(oError)


def newestInstalled(sName, lsVersionArgs=None, sMinimum="", lsExtraPatterns=None):
    """The newest working copy of a tool anywhere on the machine, at or above sMinimum when one is given; "" when no
    copy qualifies. Every copy is run, and dLast and searchLog() record them all."""
    global dLast, sSearchLog
    lsArgs = lsVersionArgs or ["--version"]
    tMinimum = versionTuple(sMinimum) if sMinimum else ()
    lsExtra = []
    for sPattern in lsExtraPatterns or []: lsExtra += sorted(glob.glob(os.path.expandvars(sPattern), recursive=True))
    lsPath = pathCopies(sName)
    lsAll = unique(placeCopies(sName, c_lsRunnable) + lsExtra + lsPath)
    lsSeen, sBest, tBest = [], "", ()
    lsLines = ["Looking for every copy of %s%s:" % (sName, " at %s or later" % sMinimum if sMinimum else "")]
    for sOne in lsAll:
        tVersion, sText = versionOf(sOne, lsArgs)
        lsSeen.append((sOne, tVersion))
        lsLines.append("  %s -- %s" % (sOne, ("version " + ".".join(str(i) for i in tVersion)) if tVersion else "will not run (" + sText + ")"))
        if not tVersion or (tMinimum and tVersion < tMinimum): continue
        if tVersion > tBest or (tVersion == tBest and not needsShell(sOne) and needsShell(sBest)): sBest, tBest = sOne, tVersion
    sFirst = lsPath[0] if lsPath else ""
    tFirst = next((t for s, t in lsSeen if s == sFirst), ())
    dLast = {"name": sName, "chosen": sBest, "version": ".".join(str(i) for i in tBest), "firstOnPath": sFirst, "firstVersion": ".".join(str(i) for i in tFirst), "seen": lsSeen, "minimum": sMinimum}
    if sBest: lsLines.append("Chosen: %s, version %s%s." % (sBest, dLast["version"], ", the newest of %d found" % len(lsSeen) if len(lsSeen) > 1 else ""))
    elif lsSeen: lsLines.append("None qualifies%s." % (": the newest is version " + ".".join(str(i) for i in max(t for s, t in lsSeen)) if any(t for s, t in lsSeen) else ""))
    else: lsLines.append("No copy found in Program Files, the user's Programs, winget's folders or the PATH.")
    sSearchLog = "\n".join(lsLines)
    return sBest


def shadowNote():
    """After newestInstalled: one plain sentence when an older copy comes first on the PATH, so other programs that
    run the tool by name still get the older one; "" otherwise."""
    if not dLast.get("chosen") or not dLast.get("firstOnPath"): return ""
    if os.path.normcase(os.path.abspath(dLast["chosen"])) == os.path.normcase(os.path.abspath(dLast["firstOnPath"])): return ""
    if versionTuple(dLast["firstVersion"]) >= versionTuple(dLast["version"]): return ""
    return "Using %s %s at %s. An older copy, %s at %s, comes first on the PATH, so other programs that run %s by name still get that one." % (
        dLast["name"], dLast["version"], dLast["chosen"], dLast["firstVersion"] or "of unknown version", dLast["firstOnPath"], dLast["name"])


def pandocProgram(sMinimum=""):
    """The newest Pandoc on the machine, at or above sMinimum when given."""
    return newestInstalled("pandoc", ["--version"], sMinimum)


def javaProgram(sMinimum="11"):
    """The newest Java on the machine, 11 or later by default, as EPUBCheck needs; Java 8 reports itself as 1.8, which
    compares below 11 as it should."""
    return newestInstalled("java", ["-version"], sMinimum)


def main():
    if len(sys.argv) < 2:
        print("Usage: python media.py <tool> [minimum version]")
        return 2
    sChosen = newestInstalled(sys.argv[1], ["-version"] if sys.argv[1].lower() == "java" else ["--version"], sys.argv[2] if len(sys.argv) > 2 else "")
    print(searchLog())
    if shadowNote(): print(shadowNote())
    return 0 if sChosen else 1


if __name__ == "__main__":
    sys.exit(main())
