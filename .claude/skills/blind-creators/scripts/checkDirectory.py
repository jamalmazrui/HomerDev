#!/usr/bin/env python3
"""checkDirectory.py - audit one Blind Authors / Developers / Presenters /
Creators Markdown file and optionally rebuild its .htm with Pandoc.

Checks: UTF-8 BOM and CRLF endings; front matter fields; every internal link
targets an existing anchor; no duplicate anchors; no bare URLs; at most three
works per person; Profiles labels in alphabetical order; people in surname
order; the count in the subtitle and intro matches the number of entries.

Run:
  checkDirectory.cmd BlindDevelopers.md
  checkDirectory.cmd BlindDevelopers.md --htm

Exit code 0 when clean, 1 when a check failed, 2 when the file could not be
read. A detailed log is written beside this script.
"""
import argparse, datetime, os, re, subprocess, sys, unicodedata

c_iMaxWorks = 3
c_sBom = "\ufeff"
oLog = None


def scriptDir():
    return os.path.dirname(os.path.abspath(__file__))


def logLine(sMsg, bConsole=False):
    sLine = "[" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] " + sMsg
    if bConsole: print(sMsg)
    if oLog:
        oLog.write(sLine + "\r\n"); oLog.flush()
    return True


def openLog(sSlug):
    global oLog
    sPath = os.path.join(scriptDir(), "checkDirectory-" + sSlug + "-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".log")
    oLog = open(sPath, "w", encoding="utf-8-sig", newline="")
    logLine("script: " + os.path.abspath(__file__))
    logLine("python: " + sys.version.replace("\n", " "))
    logLine("platform: " + sys.platform)
    logLine("cwd: " + os.getcwd())
    logLine("command line: " + " ".join(sys.argv))
    return sPath


def foldName(s):
    return "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch)).lower()


def surnameKey(sName):
    sName = re.sub(r"\s*\(.*?\)\s*$", "", sName).strip()
    lParts = sName.split()
    if not lParts: return ""
    return foldName(re.sub(r"[^A-Za-z]", "", lParts[-1])) + " " + foldName(" ".join(lParts[:-1]))


def readText(sPath):
    bin = open(sPath, "rb").read()
    bBom = bin.startswith(b"\xef\xbb\xbf")
    sText = bin.decode("utf-8-sig")
    iLf = sText.count("\n")
    iCrLf = sText.count("\r\n")
    return sText, bBom, iLf, iCrLf


def frontMatter(sText):
    d = {}
    m = re.match(r"---\r?\n(.*?)\r?\n---", sText, re.S)
    if not m: return d
    for sLine in m.group(1).splitlines():
        m2 = re.match(r"^([A-Za-z_]+):\s*(.*)$", sLine)
        if m2: d[m2.group(1)] = m2.group(2).strip().strip('"')
    return d


def check(sPath):
    lFail = []
    sText, bBom, iLf, iCrLf = readText(sPath)
    sBody = sText.replace("\r\n", "\n")
    sSlug = os.path.splitext(os.path.basename(sPath))[0]
    bCreators = sSlug.lower() == "blindcreators"

    if not bBom: lFail.append("missing UTF-8 BOM")
    if iLf != iCrLf: lFail.append("line endings are not all CRLF (" + str(iLf - iCrLf) + " bare LF)")

    d = frontMatter(sBody)
    for sKey in ["title", "subtitle", "author", "lang"] + ([] if bCreators else ["version"]):
        if sKey not in d: lFail.append("front matter lacks " + sKey)
    if "version" in d and not re.match(r"^v\d+\.\d+\.\d+$", d["version"]):
        lFail.append("version is not vMAJOR.MINOR.PATCH: " + d["version"])
    logLine("front matter: " + str(d))

    # anchors and internal links
    lAnchors = re.findall(r"\{#([A-Za-z0-9\-]+)\}", sBody)
    sAnchorsDup = sorted(set(a for a in lAnchors if lAnchors.count(a) > 1))
    if sAnchorsDup: lFail.append("duplicate anchors: " + ", ".join(sAnchorsDup))
    sAnchors = set(lAnchors)
    lRefs = re.findall(r"\]\(#([A-Za-z0-9\-]+)\)", sBody)
    lBroken = sorted(set(r for r in lRefs if r not in sAnchors))
    if lBroken: lFail.append("broken internal links: " + ", ".join(lBroken))
    logLine("anchors " + str(len(sAnchors)) + ", internal links " + str(len(lRefs)))

    # bare urls: an http(s) address not inside (...) of a Markdown link
    lBare = [m.group(0) for m in re.finditer(r"(?<!\]\()https?://\S+", sBody)]
    lBare = [u for u in lBare if not re.search(r"\]\(" + re.escape(u.rstrip(").,")), sBody)]
    if lBare: lFail.append(str(len(lBare)) + " bare url(s), first: " + lBare[0])

    # entries
    sPersonRe = r"^## (?!Introduction|Table of Contents|Conclusion|Developers|Presenters|Authors|Projects|Media|Books|Appendix)(.+?)\s*(\{#[^}]+\})?\s*$" if bCreators else r"^### (.+?)\s*(\{#[^}]+\})?\s*$"
    lPeople = []
    sPeopleText = sBody
    if not bCreators:
        mSec = re.search(r"^## (?:Developers|Authors|Presenters|Writers)\b.*$", sBody, re.M)
        if mSec:
            sPeopleText = sBody[mSec.end():]
            mNext = re.search(r"^## ", sPeopleText, re.M)
            if mNext: sPeopleText = sPeopleText[:mNext.start()]
    lLines = sPeopleText.split("\n")
    i = 0
    while i < len(lLines):
        m = re.match(sPersonRe, lLines[i])
        if m and not re.match(r"^#{2,3} (Windows|macOS|iOS|Android|Linux|NVDA|JAWS|Alexa|Developer|Command|Web|Audio|Document|Hardware|Podcasts|Video|Television|Talks|Broadcast)", lLines[i]):
            sName = m.group(1).strip()
            iStart = i; i += 1
            while i < len(lLines) and not re.match(sPersonRe, lLines[i]) and not re.match(r"^## ", lLines[i] if not bCreators else "x"):
                i += 1
            sBlock = "\n".join(lLines[iStart:i])
            lPeople.append((sName, sBlock))
            continue
        i += 1
    logLine("entries found: " + str(len(lPeople)))

    lKeys = [surnameKey(n) for n, b in lPeople]
    for j in range(1, len(lKeys)):
        if lKeys[j] < lKeys[j - 1]:
            lFail.append("surname order breaks at " + lPeople[j][0] + " (after " + lPeople[j - 1][0] + ")")
            break

    for sName, sBlock in lPeople:
        if bCreators:
            for sCat in ["Apps", "Books", "Presentations"]:
                m = re.search(r"^### " + sCat + r"\n(.*?)(?=^### |\Z)", sBlock, re.S | re.M)
                if m:
                    iWorks = len(re.findall(r"^- ", m.group(1), re.M))
                    if iWorks > c_iMaxWorks: lFail.append(sName + ": " + str(iWorks) + " " + sCat.lower() + " (max " + str(c_iMaxWorks) + ")")
            m = re.search(r"^Profiles:\n\n((?:- .*\n?)+)", sBlock, re.M)
            lLabels = re.findall(r"^- \[(.+?)\]", m.group(1), re.M) if m else []
        else:
            iWorks = len(re.findall(r"^#### ", sBlock, re.M))
            if iWorks > c_iMaxWorks: lFail.append(sName + ": " + str(iWorks) + " works (max " + str(c_iMaxWorks) + ")")
            m = re.search(r"^Profiles: (.*)$", sBlock, re.M)
            lLabels = re.findall(r"\[(.+?)\]\(", m.group(1)) if m else []
        if lLabels != sorted(lLabels, key=lambda s: s.lower()):
            lFail.append(sName + ": Profiles not alphabetical: " + ", ".join(lLabels))

    # count claims
    iPeople = len(lPeople)
    lCounts = [int(x) for x in re.findall(r"\b(\d+) (?:Creators|developers|authors|writers|presenters|people)\b", d.get("subtitle", "") + " " + sBody[:6000])]
    if iPeople and lCounts:
        lWrong = sorted(set(c for c in lCounts if c != iPeople))
        if lWrong and not bCreators: lFail.append("count claims " + ", ".join(str(c) for c in lWrong) + " but " + str(iPeople) + " entries found")
    if bCreators:
        lTotals = [int(x) for x in re.findall(r"\b(\d+) (?:people in all|entries)\b", sBody)]
        if len(set(lTotals)) > 1: lFail.append("intro and conclusion disagree on the total: " + ", ".join(str(t) for t in lTotals))
        if lTotals and lTotals[0] != iPeople: lFail.append("total claims " + str(lTotals[0]) + " but " + str(iPeople) + " entries found")

    for s in lFail: logLine("FAIL " + s)
    return lFail, iPeople, d


def buildHtm(sPath):
    sHtm = os.path.splitext(sPath)[0] + ".htm"
    lCmd = ["pandoc", sPath, "-f", "markdown", "-t", "html5", "-s", "--toc", "-o", sHtm]
    logLine("run: " + " ".join(lCmd))
    try:
        oRun = subprocess.run(lCmd, capture_output=True, text=True)
    except FileNotFoundError:
        logLine("pandoc not found on PATH")
        return None
    logLine("exit code: " + str(oRun.returncode) + " " + (oRun.stderr or "").strip())
    if oRun.returncode != 0: return None
    sText = open(sHtm, "rb").read().decode("utf-8-sig").replace("\r\n", "\n").replace("\n", "\r\n")
    open(sHtm, "wb").write(b"\xef\xbb\xbf" + sText.encode("utf-8"))
    return sHtm


def main():
    oParser = argparse.ArgumentParser(description="Audit a blind-creators directory Markdown file.")
    oParser.add_argument("file", help="the .md file to check")
    oParser.add_argument("--htm", action="store_true", help="also rebuild the matching .htm with Pandoc")
    oArgs = oParser.parse_args()
    sPath = os.path.abspath(oArgs.file)
    sLog = openLog(os.path.splitext(os.path.basename(sPath))[0])
    if not os.path.isfile(sPath):
        logLine("file not found: " + sPath, True)
        return 2
    lFail, iPeople, d = check(sPath)
    sNoun = "entry" if iPeople == 1 else "entries"
    if lFail:
        print(os.path.basename(sPath) + ": " + str(len(lFail)) + (" problem" if len(lFail) == 1 else " problems") + " in " + str(iPeople) + " " + sNoun)
        for s in lFail: print("  " + s)
    else:
        print(os.path.basename(sPath) + ": clean, " + str(iPeople) + " " + sNoun + ", " + d.get("version", "no version"))
    if oArgs.htm:
        sHtm = buildHtm(sPath)
        print("htm: " + (os.path.basename(sHtm) if sHtm else "not built, see log"))
    print("log: " + sLog)
    return 1 if lFail else 0


if __name__ == "__main__":
    sys.exit(main())
