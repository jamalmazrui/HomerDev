#!/usr/bin/env python3
"""buildCreators.py - regenerate BlindCreators.md from BlindAuthors.md,
BlindDevelopers.md and BlindPresenters.md in the same folder.

Each source entry is an H3 person heading (with an optional {#anchor}), a bio
paragraph, an optional "Profiles: [A](u), [B](u)." line, and up to three H4
works, each "#### [Title](url) {#anchor}" (or an unlinked title) followed by a
one-line description. The output lists every person once as an H2, with a
Profiles bullet list and Apps / Books / Presentations H3 subsections.

Run:
  buildCreators.cmd
  buildCreators.cmd --dir C:\\Directories --version v3.4.0 --htm

Without --version the minor number of the existing BlindCreators.md is bumped
when it has one; a file with no version field stays without one. A detailed log is written beside
this script.
"""
import argparse, datetime, os, re, subprocess, sys, unicodedata

c_lCategories = ["Apps", "Books", "Presentations"]
c_dSources = {"BlindDevelopers.md": "Apps", "BlindAuthors.md": "Books", "BlindPresenters.md": "Presentations"}
c_sSubtitle = "Authoring Books, Developing Apps, or Making Presentations While Blind or Low Vision"
oLog = None


def scriptDir():
    return os.path.dirname(os.path.abspath(__file__))


def logLine(sMsg, bConsole=False):
    sLine = "[" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] " + sMsg
    if bConsole: print(sMsg)
    if oLog:
        oLog.write(sLine + "\r\n"); oLog.flush()
    return True


def openLog():
    global oLog
    sPath = os.path.join(scriptDir(), "buildCreators-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".log")
    oLog = open(sPath, "w", encoding="utf-8-sig", newline="")
    logLine("script: " + os.path.abspath(__file__))
    logLine("python: " + sys.version.replace("\n", " "))
    logLine("platform: " + sys.platform)
    logLine("cwd: " + os.getcwd())
    logLine("command line: " + " ".join(sys.argv))
    return sPath


def foldName(s):
    return "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch)).lower()


def nameParts(sName):
    sBare = re.sub(r"\s*\(.*?\)\s*$", "", sName).strip()
    lParts = sBare.split()
    sLast = lParts[-1] if lParts else sBare
    sFirst = " ".join(lParts[:-1])
    return sFirst, sLast


def surnameKey(sName):
    sFirst, sLast = nameParts(sName)
    return foldName(re.sub(r"[^A-Za-z]", "", sLast)) + " " + foldName(sFirst)


def slugOf(s):
    s = foldName(s).replace("'", "").replace("\u2019", "")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "x"


def dropInternalLinks(s):
    return re.sub(r"\[([^\]]+)\]\(#[^)]+\)", r"\1", s)


def numberWord(i):
    lWords = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]
    return lWords[i] if 0 <= i < len(lWords) else str(i)


def plural(i, sOne, sMany):
    return str(i) + " " + (sOne if i == 1 else sMany)


def readSource(sPath):
    sText = open(sPath, "rb").read().decode("utf-8-sig").replace("\r\n", "\n")
    d = {}
    m = re.search(r"^## (?:Developers|Authors|Presenters|Writers)\b.*$", sText, re.M)
    sBody = sText[m.end():] if m else sText
    mEnd = re.search(r"^## ", sBody, re.M)
    if mEnd: sBody = sBody[:mEnd.start()]
    lBlocks = re.split(r"^(?=### )", sBody, flags=re.M)
    for sBlock in lBlocks:
        m = re.match(r"^### (.+?)\s*(?:\{#[^}]+\})?\s*\n", sBlock)
        if not m: continue
        if re.match(r"^## ", sBlock.split("\n", 1)[1] if "\n" in sBlock else ""): pass
        sName = m.group(1).strip()
        sRest = sBlock[m.end():]
        sRest = re.split(r"^## ", sRest, 1, flags=re.M)[0]
        mProf = re.search(r"^Profiles: (.*)$", sRest, re.M)
        lProfiles = re.findall(r"\[([^\]]+?)\]\(((?:[^()]|\([^()]*\))+)\)", mProf.group(1)) if mProf else []
        sBefore = sRest.split("\n#### ", 1)[0]
        sBefore = re.sub(r"^Profiles: .*$", "", sBefore, flags=re.M)
        sBio = dropInternalLinks(" ".join(x.strip() for x in sBefore.strip().split("\n") if x.strip()))
        lWorks = []
        for sWork in re.split(r"^(?=#### )", sRest, flags=re.M)[1:]:
            mW = re.match(r"^#### (.+?)\s*(?:\{#[^}]+\})?\s*\n(.*)", sWork, re.S)
            if not mW: continue
            sTitle = mW.group(1).strip()
            lDescLines = [x.strip() for x in mW.group(2).strip().split("\n") if x.strip()]
            lDescLines = [x for x in lDescLines if not re.match(r"^(Wikipedia|Format|Accessible edition|NLS|Bookshare|Also on):", x, re.I)]
            sDesc = dropInternalLinks(lDescLines[0]) if lDescLines else ""
            sDesc = re.sub(r"\s*\[?see the full entry.*$", "", sDesc, flags=re.I).strip()
            if re.search(r"\(co-created\)$", sTitle) and not sDesc: continue
            lWorks.append((sTitle, sDesc))
        d[sName] = {"bio": sBio, "profiles": lProfiles, "works": lWorks[:3]}
    logLine("read " + os.path.basename(sPath) + ": " + str(len(d)) + " entries")
    return d


def mergePeople(dSources):
    dPeople = {}
    for sFile, sCat in c_dSources.items():
        for sName, dEntry in dSources.get(sFile, {}).items():
            sKey = foldName(re.sub(r"\s*\(.*?\)\s*$", "", sName))
            p = dPeople.setdefault(sKey, {"name": sName, "bio": "", "profiles": {}, "works": {}})
            if len(sName) > len(p["name"]): p["name"] = sName
            if len(dEntry["bio"]) > len(p["bio"]): p["bio"] = dEntry["bio"]
            for sLabel, sUrl in dEntry["profiles"]:
                p["profiles"].setdefault(sLabel.lower(), (sLabel, sUrl))
            if dEntry["works"]: p["works"][sCat] = dEntry["works"]
    return sorted(dPeople.values(), key=lambda p: surnameKey(p["name"]))


def assignAnchors(lPeople):
    dCount = {}
    for p in lPeople:
        sFirst, sLast = nameParts(p["name"])
        dCount.setdefault(slugOf(sLast), []).append(p)
    for sLast, lSame in dCount.items():
        for p in lSame:
            sFirst, x = nameParts(p["name"])
            p["anchor"] = "cr-" + sLast + ("-" + slugOf(sFirst.split()[0]) if len(lSame) > 1 and sFirst else "")
    return lPeople


def nextVersion(sDir, sGiven):
    if sGiven: return sGiven
    sPath = os.path.join(sDir, "BlindCreators.md")
    if os.path.isfile(sPath):
        m = re.search(r'^version:\s*"?v(\d+)\.(\d+)\.(\d+)"?', open(sPath, "rb").read().decode("utf-8-sig"), re.M)
        if m: return "v" + m.group(1) + "." + str(int(m.group(2)) + 1) + ".0"
    return ""


def render(lPeople, sVersion):
    iTotal = len(lPeople)
    dCat = {c: sum(1 for p in lPeople if c in p["works"]) for c in c_lCategories}
    lMulti = [p for p in lPeople if len(p["works"]) > 1]
    lTwo = [p for p in lPeople if len(p["works"]) == 2]
    lThree = [p for p in lPeople if len(p["works"]) == 3]
    L = []
    w = L.append
    w("---")
    w('title: "Blind Creators"')
    w('subtitle: "' + c_sSubtitle + '"')
    w('author: "Jamal Mazrui"')
    w('date: "' + datetime.date.today().strftime("%B %Y") + '"')
    if sVersion: w('version: "' + sVersion + '"')
    w('lang: "en-US"')
    w('license: "CC BY-SA 4.0"')
    w('license_url: "https://creativecommons.org/licenses/by-sa/4.0/"')
    w("toc: true")
    w("toc-depth: 2")
    w('abstract: "A consolidated directory of ' + plural(iTotal, "person", "people") + ' who are blind or have low vision and who create in one or more of three ways: authoring books, developing apps, or making presentations. Creators are listed alphabetically by last name, each with a Profiles list and up to three works in every category that applies. It merges the companion Blind Authors, Blind Developers, and Blind Presenters directories."')
    w("keywords: [blindness, low vision, accessibility, blind authors, blind developers, blind presenters, screen readers]")
    w("---")
    w("")
    w("# Blind Creators")
    w("")
    w("## Introduction {#introduction}")
    w("")
    w("This directory brings together people who are blind or have low vision and who create in one or more of three ways: authoring books, developing apps, or making presentations. It consolidates three companion directories — [Blind Authors](https://jamalmazrui.github.io/BlindAuthors/), [Blind Developers](https://jamalmazrui.github.io/BlindDevelopers/), and [Blind Presenters](https://jamalmazrui.github.io/BlindPresenters/) — into a single alphabetical listing. It is meant as a resource for aspiring blind creators and as a way to find and reach the people listed.")
    w("")
    w("Creators are listed alphabetically by last name as second-level headings, each giving the person’s full name. Under each name is a bulleted “Profiles:” list, in alphabetical order by label, linking to whatever pages are available, such as a personal website, Amazon, GitHub, Goodreads, LinkedIn, or Wikipedia. Then come up to three subsections — Apps, Books, and Presentations — and a subsection appears only when that person has work in it. Each subsection lists up to three works, most significant or most recent first, with a link to where the work can be reached and a one-line description.")
    w("")
    w("Each listed work belongs to its creator. This directory's own text is available under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).")
    w("")
    w("A person qualifies in a category on these terms:")
    w("")
    w("- **Books.** The creator was blind or had low vision when the book was written; is the sole author; the book was first published in 2000 or later; and it is available today in a digital format — electronic text or audio — through a working link.")
    w("- **Apps.** The creator is blind or has low vision; created or led the development of the app or tool; the app is reachable today through a working link to where it can be obtained and used; and it has been actively developed or maintained in 2020 or later.")
    w("- **Presentations.** The creator is blind or has low vision; the work is contemporary, from 2010 onward; it shows sustained, notable leadership rather than a one-off clip — such as a keynote at a recognized event, an established regularly published series, a body of at least three published works, or professional standing like a broadcasting role; and the creator holds the role in their own right.")
    w("")
    sSpan = "The directory holds " + plural(iTotal, "person", "people") + " in all. Of these, " + str(dCat["Books"]) + (" appears" if dCat["Books"] == 1 else " appear") + " as book authors, " + str(dCat["Apps"]) + " as app developers, and " + str(dCat["Presentations"]) + " as presenters."
    if lMulti:
        sSpan += " Those figures add up to more than " + str(iTotal) + " because " + plural(len(lMulti), "person works", "people work") + " in more than one category — for example, an author who also speaks, or a developer who also writes — and each of them is counted once here, with every category that applies shown under their single entry."
        lClauses = []
        if lTwo: lClauses.append(numberWord(len(lTwo)) + " of them " + ("works" if len(lTwo) == 1 else "work") + " in two categories")
        if lThree:
            lNames = [p["name"] for p in lThree]
            sNames = lNames[0] if len(lNames) == 1 else ", ".join(lNames[:-1]) + (", and " if len(lNames) > 2 else " and ") + lNames[-1]
            lClauses.append(numberWord(len(lThree)) + ", " + sNames + ", " + ("works" if len(lThree) == 1 else "work") + " in all three")
        else:
            lClauses.append("none works in all three")
        sTwo = ", and ".join(lClauses)
        sSpan += " " + sTwo[0].upper() + sTwo[1:] + "."
    w(sSpan)
    w("")
    w("The directory is English-language in scope: it relies on books, code, talks, and sources that can be read, run, or followed in English. Blind creators who publish or present in other languages are not represented here.")
    w("")
    w("## Table of Contents {#table-of-contents}")
    w("")
    w("- [Introduction](#introduction)")
    for p in lPeople: w("- [" + p["name"] + "](#" + p["anchor"] + ")")
    w("- [Conclusion](#conclusion)")
    w("")
    for p in lPeople:
        w("## " + p["name"] + " {#" + p["anchor"] + "}")
        w("")
        if p["bio"]:
            w(p["bio"]); w("")
        if p["profiles"]:
            w("Profiles:"); w("")
            for sLabel, sUrl in sorted(p["profiles"].values(), key=lambda t: t[0].lower()): w("- [" + sLabel + "](" + sUrl + ")")
            w("")
        for sCat in c_lCategories:
            if sCat not in p["works"]: continue
            w("### " + sCat); w("")
            for sTitle, sDesc in p["works"][sCat]:
                w("- " + sTitle + (" — " + sDesc if sDesc else ""))
            w("")
    w("## Conclusion {#conclusion}")
    w("")
    w("Read together, the " + plural(iTotal, "entry makes", "entries make") + " one point plainly: blind and low-vision people are producing finished, publicly available work — books you can buy, software you can install, and series you can subscribe to — not prototypes or promises. Every item here was included only after a working link to the actual work could be confirmed, so the directory doubles as a set of live starting points rather than a list of names.")
    w("")
    if lMulti:
        w("The " + plural(len(lMulti), "person who appears", "people who appear") + " in more than one category " + ("is" if len(lMulti) == 1 else "are") + " worth noticing. The lines between author, developer, and presenter are thin: someone who builds a screen-reader tool often documents it in a book and demonstrates it on a podcast. Assistive technology in particular runs through all three categories at once, as subject, as tool, and as the thing being taught.")
        w("")
    w("The directory is deliberately bounded. It covers English-language work, it counts sole-authored books rather than collaborations, it counts apps with recent development activity rather than abandoned ones, and it counts presenters who lead in their own right. Those limits mean many worthy creators fall outside any single edition; the boundaries are meant to keep each entry verifiable, not to mark the edge of what blind people create.")
    w("")
    w("For the fuller treatment of any one field — additional works, appendices grouping books, apps, and media by type — see the companion directories: [Blind Authors](https://jamalmazrui.github.io/BlindAuthors/), [Blind Developers](https://jamalmazrui.github.io/BlindDevelopers/), and [Blind Presenters](https://jamalmazrui.github.io/BlindPresenters/).")
    w("")
    return "\n".join(L), iTotal, dCat, len(lMulti), len(lThree)


def buildHtm(sPath):
    sHtm = os.path.splitext(sPath)[0] + ".htm"
    lCmd = ["pandoc", sPath, "-f", "markdown", "-t", "html5", "-s", "--toc", "-o", sHtm]
    logLine("run: " + " ".join(lCmd))
    try:
        oRun = subprocess.run(lCmd, capture_output=True, text=True)
    except FileNotFoundError:
        logLine("pandoc not found on PATH"); return None
    logLine("exit code: " + str(oRun.returncode) + " " + (oRun.stderr or "").strip())
    if oRun.returncode != 0: return None
    sText = open(sHtm, "rb").read().decode("utf-8-sig").replace("\r\n", "\n").replace("\n", "\r\n")
    open(sHtm, "wb").write(b"\xef\xbb\xbf" + sText.encode("utf-8"))
    return sHtm


def main():
    oParser = argparse.ArgumentParser(description="Regenerate BlindCreators.md from the three source directories.")
    oParser.add_argument("--dir", default=os.getcwd(), help="folder holding the source .md files (default: current folder)")
    oParser.add_argument("--version", default="", help="version to stamp, e.g. v3.4.0 (default: bump the minor number)")
    oParser.add_argument("--htm", action="store_true", help="also build BlindCreators.htm with Pandoc")
    oArgs = oParser.parse_args()
    sLog = openLog()
    sDir = os.path.abspath(oArgs.dir)
    logLine("dir: " + sDir)
    dSources = {}
    lMissing = []
    for sFile in c_dSources:
        sPath = os.path.join(sDir, sFile)
        if os.path.isfile(sPath): dSources[sFile] = readSource(sPath)
        else: lMissing.append(sFile)
    if lMissing:
        logLine("missing source file(s): " + ", ".join(lMissing), True)
        print("log: " + sLog)
        return 2
    lPeople = assignAnchors(mergePeople(dSources))
    sVersion = nextVersion(sDir, oArgs.version)
    sText, iTotal, dCat, iMulti, iThree = render(lPeople, sVersion)
    sOut = os.path.join(sDir, "BlindCreators.md")
    open(sOut, "wb").write(b"\xef\xbb\xbf" + sText.replace("\n", "\r\n").encode("utf-8"))
    logLine("wrote " + sOut + " " + (sVersion or "(no version)") + ": " + str(iTotal) + " people; apps " + str(dCat["Apps"]) + ", books " + str(dCat["Books"]) + ", presentations " + str(dCat["Presentations"]) + "; multi " + str(iMulti) + ", all three " + str(iThree))
    print("BlindCreators.md " + (sVersion + " " if sVersion else "") + ": " + plural(iTotal, "person", "people") + " (" + str(dCat["Books"]) + " authors, " + str(dCat["Apps"]) + " developers, " + str(dCat["Presentations"]) + " presenters; " + str(iMulti) + " in more than one category)")
    if oArgs.htm:
        sHtm = buildHtm(sOut)
        print("htm: " + (os.path.basename(sHtm) if sHtm else "not built, see log"))
    print("log: " + sLog)
    return 0


if __name__ == "__main__":
    sys.exit(main())
