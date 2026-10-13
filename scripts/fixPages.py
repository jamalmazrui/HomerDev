"""fixPages.py version 4 -- the kit's page finisher for a collection: help guides, podcast directories, any folder of
.md pages and the .htm pages built from them.

    fixPages [folder]            rebuild each .htm from its .md, then finish it; finish any .htm that has no .md
    fixPages [folder] --pages    finish the .htm pages as they are, rebuilding nothing (fast; works on a repository
                                 that holds only the published pages)

WHERE IT CAME FROM. Version 3 lived in AppHelpGuides and gave every page one level-one heading. Audits of the help
guides and the podcast directories on 12 October 2026 found what it did not touch: pages with no language, no main
landmark, duplicate IDs, links to anchors that never came with the article, empty links and addresses relative to the
publisher's site, which lead nowhere from a downloaded copy or GitHub Pages. Those rules now live in the kit, in
scripts\\fixEncoding.py beside the heading rule, so every Homer build applies them too; this script applies them to a
collection, and reports what they could not settle.

A page with no title of its own takes its first line as its title -- the announcement's "Announcing Podcast
Directories" -- never a stock word: version 3 titled such a page "Help guide".

KNOWN CORRECTIONS. data\\linkFixes.inix in the collection maps an address known to be wrong to its verified
replacement, one "old = new" line each, so a fix survives the next build of the page.

THE LOG is logs\\<Collection>-fixPages-<date>-<time>.log in the collection, with every page and every change counted.
"""

import datetime, importlib.util, io, os, platform, re, shutil, subprocess, sys

c_sVersion = "2026-10-12 version 4: the kit's finisher; language, landmark, IDs, links; titles from the page itself"
sLogPath = ""


def log(sText):
    if not sLogPath: return False
    with open(sLogPath, "a", encoding="utf-8-sig") as fLog: fLog.write(datetime.datetime.now().strftime("%H:%M:%S ") + sText + "\n")
    return True


def say(sText):
    print(sText)
    log("SAY " + sText)
    return True


def readText(sPath):
    binBody = io.open(sPath, "rb").read()
    for sEncoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try: return binBody.decode(sEncoding)
        except UnicodeDecodeError: continue
    return binBody.decode("utf-8", "replace")


def writeText(sPath, sText):
    io.open(sPath, "wb").write(b"\xef\xbb\xbf" + sText.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))
    return True


def titleOf(sMarkdown, sFallback):
    """The page's own title: its front matter, its first heading, or its first line of text."""
    oFront = re.search(r'(?m)^title:\s*"?([^"\n]+)"?\s*$', sMarkdown[:800])
    if oFront: return oFront.group(1).strip()
    oHeading = re.search(r"(?m)^# (.+)$", sMarkdown)
    if oHeading: return oHeading.group(1).strip()
    for sLine in sMarkdown.lstrip("\ufeff").splitlines():
        if sLine.strip() and not sLine.startswith(("---", ":::")): return re.sub(r"[*_`#]", "", sLine).strip()
    return sFallback


def findPandoc():
    """The newest Pandoc on this computer: each copy found is asked its version."""
    lCandidates = []
    sOnPath = shutil.which("pandoc")
    if sOnPath: lCandidates.append(sOnPath)
    for sBase in (os.environ.get("ProgramFiles", ""), os.environ.get("LOCALAPPDATA", "")):
        sPath = os.path.join(sBase, "Pandoc", "pandoc.exe") if sBase else ""
        if sPath and os.path.isfile(sPath) and sPath.lower() not in [s.lower() for s in lCandidates]: lCandidates.append(sPath)
    tBest, sBest = (), ""
    for sPath in lCandidates:
        try:
            sFirst = subprocess.run([sPath, "--version"], capture_output=True, text=True, timeout=30).stdout.splitlines()[0]
            tVersion = tuple(int(s) for s in re.findall(r"\d+", sFirst.split()[-1]))
        except Exception:
            continue
        log("pandoc candidate %s, version %s" % (sPath, ".".join(str(i) for i in tVersion)))
        if tVersion > tBest: tBest, sBest = tVersion, sPath
    return sBest


def loadRules():
    """The kit's fixEncoding.py, beside this script."""
    sPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixEncoding.py")
    oSpec = importlib.util.spec_from_file_location("homerFixEncoding", sPath)
    oModule = importlib.util.module_from_spec(oSpec)
    oSpec.loader.exec_module(oModule)
    log("rules: " + sPath)
    return oModule


def readFixes(sFolder):
    """data\\linkFixes.inix: "old = new" lines; ; begins a comment."""
    sPath = os.path.join(sFolder, "data", "linkFixes.inix")
    dFixes = {}
    if os.path.isfile(sPath):
        for sLine in readText(sPath).splitlines():
            if sLine.strip().startswith((";", "[")) or " = " not in sLine: continue
            sOld, sNew = sLine.split(" = ", 1)
            if sOld.strip() and sNew.strip(): dFixes[sOld.strip()] = sNew.strip()
    log("known corrections: %d from %s" % (len(dFixes), sPath if dFixes else "none"))
    return dFixes


def residue(sHtml, setLocal):
    """What the rules could not settle: in-page links to nothing, repeated IDs, site-relative links."""
    setIds = set(re.findall(r'\sid="([^"]+)"', sHtml))
    iFragments = sum(1 for s in re.findall(r'href="#([^"]*)"', sHtml) if s not in setIds)
    iDuplicates = len(re.findall(r'\sid="([^"]+)"', sHtml)) - len(setIds)
    iRelative = sum(1 for s in re.findall(r'<a\b[^>]*\bhref="([^"#][^"]*)"', sHtml)
                    if not re.match(r"(?i)(https?:|mailto:|tel:|ftp:|data:|javascript:)", s) and s.split("#")[0].split("?")[0].lower() not in setLocal)
    return {k: v for k, v in (("in-page links to nothing", iFragments), ("repeated IDs", iDuplicates), ("site-relative links", iRelative)) if v}


def main(lsArgs):
    global sLogPath
    bPagesOnly = "--pages" in lsArgs
    lsFolders = [s for s in lsArgs if not s.startswith("--")]
    sFolder = os.path.abspath(lsFolders[0] if lsFolders else os.getcwd())
    sCollection = os.path.basename(sFolder.rstrip("\\/")) or "Pages"
    os.makedirs(os.path.join(sFolder, "logs"), exist_ok=True)
    sLogPath = os.path.join(sFolder, "logs", "%s-fixPages-%s.log" % (sCollection, datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))
    log("fixPages.py started; %s; script %s" % (c_sVersion, os.path.abspath(__file__)))
    log("Python %s at %s on %s; cwd %s; command line %s" % (platform.python_version(), sys.executable, platform.platform(), os.getcwd(), " ".join(sys.argv)))
    log("Settings: folder %s; pages only %s" % (sFolder, bPagesOnly))
    oRules = loadRules()
    dFixes = readFixes(sFolder)
    sPandoc = "" if bPagesOnly else findPandoc()
    if not bPagesOnly and not sPandoc:
        say("Pandoc was not found, so pages cannot be rebuilt. Install Pandoc, or run fixPages --pages to finish the pages as they are.")
        return 1
    setLocal = {s.lower() for s in os.listdir(sFolder)}
    lsMarkdown = [] if bPagesOnly else sorted(s for s in os.listdir(sFolder) if s.lower().endswith(".md"))
    setFromMarkdown = {s[:-3].lower() + ".htm" for s in lsMarkdown}
    lsPages = sorted(s for s in os.listdir(sFolder) if s.lower().endswith(".htm") and s.lower() not in setFromMarkdown)
    iTotal = len(lsMarkdown) + len(lsPages)
    say("%d page%s to %s in %s" % (iTotal, "" if iTotal == 1 else "s", "finish" if bPagesOnly else "rebuild and finish", sFolder))
    dChanges, dResidue, lsFailed = {}, {}, []
    for iIndex, sName in enumerate(lsMarkdown + lsPages, 1):
        print("%d of %d: %s" % (iIndex, iTotal, sName))
        sys.stdout.flush()
        if sName.lower().endswith(".md"):
            sMd = os.path.join(sFolder, sName)
            sHtm = sMd[:-3] + ".htm"
            sTitle = titleOf(readText(sMd), sName[:-3])
            lsCommand = [sPandoc, sMd, "-f", "markdown", "-t", "html5", "--standalone", "--toc", "--toc-depth=2",
                         "-M", "pagetitle=" + sTitle, "-M", "lang=" + oRules.c_sLang, "-o", sHtm]
            oRun = subprocess.run(lsCommand, capture_output=True)
            log("RUN %s: exit %d %s" % (" ".join(lsCommand), oRun.returncode, oRun.stderr.decode("utf-8", "replace")[-300:]))
            if oRun.returncode != 0:
                lsFailed.append(sName)
                continue
            sHtml = oRules.oneTitleHeading(readText(sHtm).replace("\r\n", "\n"))
        else:
            sHtm = os.path.join(sFolder, sName)
            sHtml = readText(sHtm).replace("\r\n", "\n")
        sBefore = sHtml
        sHtml, dDone = oRules.finishPage(sHtml, setLocal, dFixes)
        if sHtml != sBefore or sName.lower().endswith(".md"): writeText(sHtm, sHtml)
        for sKind, iCount in dDone.items(): dChanges[sKind] = dChanges.get(sKind, 0) + iCount
        dLeft = residue(sHtml, setLocal)
        iHeadings = len(re.findall(r"(?i)<h1\b", sHtml))
        if iHeadings != 1: dLeft["level-one headings, not one"] = iHeadings
        if dLeft: dResidue[os.path.basename(sHtm)] = dLeft
        log("%s: %s%s" % (os.path.basename(sHtm), ", ".join("%s %d" % t for t in sorted(dDone.items())) or "unchanged",
                          ("; LEFT " + ", ".join("%s %d" % t for t in sorted(dLeft.items()))) if dLeft else ""))
    say("Pages finished: %d." % (iTotal - len(lsFailed)))
    for sKind, iCount in sorted(dChanges.items()): say("  %s: %s" % (sKind, format(iCount, ",")))
    if lsFailed: say("Pandoc could not build %d: %s" % (len(lsFailed), ", ".join(lsFailed)))
    if dResidue:
        say("Pages with something the rules could not settle: %d; the log names each." % len(dResidue))
    say("Log: " + sLogPath)
    return 1 if (lsFailed or dResidue) else 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception:
        import traceback
        log("CRASH " + traceback.format_exc())
        print("fixPages stopped with an error; the log has the details: " + sLogPath)
        sys.exit(2)
