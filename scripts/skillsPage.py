"""skillsPage.py -- the kit's skills as one web page, with every download an agent or a person needs beside it.

    skillsPage                   write the page where MyPages keeps it (<drive>:\\MyPages\\pages\\HomerSkills), or in
                                 the kit's work\\HomerSkills when there is no MyPages
    skillsPage <folder>          write it in that folder

WHY (26 November 2026). Jamal asked that the kit's skills be easier for agents to find -- ChatGPT, Codex, Copilot,
Claude, Gemini, Grok and others -- and for a Homer-structured page, HomerSkills, presenting all of them. The skills
themselves stay where they are, in .claude\\skills; everything here is made from them, so the page can never say
something the skills do not, and MyPages' post runs this before it posts, so the page is always the kit's current set.

WHAT IT WRITES in the folder, only when a file's bytes change, so the page is posted only when a skill changed:
    HomerSkills.md                       the page: an introduction, the numbers, how each agent takes a skill, then
                                         every skill under its group, and an appendix by name
    skills\\<name>.zip                   one skill as a zip holding its folder: the form Claude and ChatGPT upload
    skills\\HomerSkills.zip              every skill, one folder each, to unzip into a skills folder
    .well-known\\agent-skills\\index.json the Agent Skills discovery index (schema 0.2.0), which installers such as
                                         "npx skills add" read from a page's address
    .well-known\\agent-skills\\<name>.tar.gz  one skill with SKILL.md at the top, as that index requires
    llms.txt                             the same list for agents that read llms.txt
    _config.yml                          tells GitHub Pages to publish the .well-known folder, which it skips by default
A zip or archive of a skill that is gone is removed; nothing else in the folder is touched.

WHERE THE WORDS COME FROM. Each skill's one-line summary is its line in the kit's AGENTS.md, which the kit's check
keeps complete; its group is the group under metadata in its SKILL.md. Archives are made the same way every time --
fixed dates, sorted names -- so the same skills give the same bytes and the same digests.

THE LOG is HomerDev-skillsPage-<stamp>.log in the kit's logs folder, or %LOCALAPPDATA%\\HomerDev\\logs when the kit's
folder cannot be written.
"""

import datetime, gzip, hashlib, io, json, os, platform, re, string, sys, tarfile, zipfile

sOwner = "JamalMazrui"
sPage = "HomerSkills"
sSchema = "https://schemas.agentskills.io/discovery/0.2.0/schema.json"
tFixedDate = (2026, 1, 1, 0, 0, 0)

dGroupNotes = {
    "Building Apps": "Making, testing, installing and releasing Windows programs for keyboard and screen reader users.",
    "Data and Directories": "Databases and one-page directories that gather what is worth finding in one place.",
    "Documents, Books and Media": "Writing, converting and checking documents, books, guides and spoken tutorials.",
}
lsLog = []
sLogPath = ""


def logLine(sText):
    lsLog.append(datetime.datetime.now().strftime("%H:%M:%S ") + sText)
    if sLogPath:
        bNew = not os.path.exists(sLogPath)
        with open(sLogPath, "ab") as oFile: oFile.write((b"\xef\xbb\xbf" if bNew else b"") + (lsLog[-1] + "\r\n").encode("utf-8"))


def say(sText):
    print(sText)
    logLine("SAY " + sText)


def kitFolder():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def skillFiles(sSkills, sName):
    """The files of a skill that are published, as (path, path inside the skill folder with forward slashes), sorted:
    never a .htm made from a Markdown file, never Python's cache."""
    lFiles = []
    sFolder = os.path.join(sSkills, sName)
    for sDir, lsDirs, lsNames in os.walk(sFolder):
        lsDirs[:] = sorted(s for s in lsDirs if s != "__pycache__")
        for sFile in lsNames:
            if sFile.lower().endswith((".htm", ".pyc")): continue
            sPath = os.path.join(sDir, sFile)
            lFiles.append((sPath, os.path.relpath(sPath, sFolder).replace("\\", "/")))
    return sorted(lFiles, key=lambda t: t[1].lower())


def zipBytes(lEntries):
    """A zip of (path, name inside) entries, the same bytes every time: fixed dates, the given order."""
    oBuffer = io.BytesIO()
    with zipfile.ZipFile(oBuffer, "w", zipfile.ZIP_DEFLATED) as oZip:
        for sPath, sInside in lEntries:
            oInfo = zipfile.ZipInfo(sInside, tFixedDate)
            oInfo.compress_type = zipfile.ZIP_DEFLATED
            oInfo.external_attr = 0o644 << 16
            with open(sPath, "rb") as oFile: oZip.writestr(oInfo, oFile.read())
    return oBuffer.getvalue()


def packSkill(sSkills, sName, sZip=""):
    """One skill as a zip holding its folder, the form Claude and ChatGPT take; written to sZip when one is given.
    Returns the bytes. The kit's build packs exec\\skills with this too, so there is one way to pack a skill."""
    binZip = zipBytes([(sPath, sName + "/" + sInside) for sPath, sInside in skillFiles(sSkills, sName)])
    if sZip: writeIfChanged(sZip, binZip)
    return binZip


def archiveBytes(sSkills, sName):
    """One skill as a .tar.gz with SKILL.md at its top, as the discovery index requires, the same bytes every time."""
    oTar = io.BytesIO()
    with tarfile.open(fileobj=oTar, mode="w", format=tarfile.PAX_FORMAT) as oArchive:
        for sPath, sInside in skillFiles(sSkills, sName):
            with open(sPath, "rb") as oFile: binData = oFile.read()
            oInfo = tarfile.TarInfo(sInside)
            oInfo.size, oInfo.mtime, oInfo.mode, oInfo.uid, oInfo.gid, oInfo.uname, oInfo.gname = len(binData), 0, 0o644, 0, 0, "", ""
            oArchive.addfile(oInfo, io.BytesIO(binData))
    oGzip = io.BytesIO()
    with gzip.GzipFile(fileobj=oGzip, mode="wb", mtime=0, filename="") as oFile: oFile.write(oTar.getvalue())
    return oGzip.getvalue()


def writeIfChanged(sPath, binData):
    """Writes the bytes only when the file differs; returns True when it wrote."""
    if os.path.isfile(sPath):
        with open(sPath, "rb") as oFile:
            if oFile.read() == binData: return False
    os.makedirs(os.path.dirname(sPath), exist_ok=True)
    with open(sPath, "wb") as oFile: oFile.write(binData)
    logLine("wrote %s (%d bytes)" % (sPath, len(binData)))
    return True


def frontmatter(sText):
    """{key: value} of a SKILL.md's front matter; folded lines joined, and metadata's own keys as metadata.<key>."""
    oMatch = re.match(r"---[ \t]*\n(.*?)\n---[ \t]*\n", sText, re.S)
    dValues, sKey, sParent = {}, "", ""
    if not oMatch: return dValues
    for sLine in oMatch.group(1).split("\n"):
        oTop = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", sLine)
        oChild = re.match(r"^\s+([A-Za-z][\w-]*):\s*(.*)$", sLine)
        if oTop:
            sKey, sParent = oTop.group(1), oTop.group(1)
            sValue = oTop.group(2).strip()
            dValues[sKey] = "" if re.fullmatch(r"[>|][-+]?", sValue) else sValue
        elif oChild and sParent == "metadata":
            sKey = "metadata." + oChild.group(1)
            dValues[sKey] = oChild.group(2).strip()
        elif sKey and sLine.startswith((" ", "\t")):
            dValues[sKey] = (dValues[sKey] + " " + sLine.strip()).strip()
    return {k: v.strip().strip("\"'") for k, v in dValues.items()}


def summaries(sKit):
    """Each skill's one line in AGENTS.md: "- **name** -- what it does. `path`"."""
    dLines = {}
    sPath = os.path.join(sKit, "AGENTS.md")
    if not os.path.isfile(sPath): return dLines
    for sLine in open(sPath, encoding="utf-8-sig").read().splitlines():
        oMatch = re.match(r"^- \*\*([a-z0-9-]+)\*\* -- (.+?)\s*`\.claude/skills/", sLine)
        if oMatch: dLines[oMatch.group(1)] = oMatch.group(2).strip()
    return dLines


def sentence(sText):
    sText = sText.strip()
    if not sText: return sText
    sText = sText[0].upper() + sText[1:]
    return sText if sText.endswith((".", "!", "?")) else sText + "."


def countNoun(iCount, sNoun, sPlural=""):
    return "%s %s" % ("{:,}".format(iCount), sNoun if iCount == 1 else (sPlural or sNoun + "s"))


def sizeText(iBytes):
    if iBytes < 1024 * 1024: return "%d KB" % max(1, round(iBytes / 1024.0))
    return "%.1f MB" % (iBytes / 1048576.0)


def listed(ls):
    return ls[0] if len(ls) == 1 else (" and ".join(ls) if len(ls) == 2 else ", ".join(ls[:-1]) + ", and " + ls[-1])


def catalog(sKit):
    """Every skill, with what the page says of it."""
    sSkills = os.path.join(sKit, ".claude", "skills")
    dSummary = summaries(sKit)
    lSkills = []
    for sName in sorted(os.listdir(sSkills)):
        sFile = os.path.join(sSkills, sName, "SKILL.md")
        if not os.path.isfile(sFile): continue
        sText = open(sFile, encoding="utf-8-sig").read().replace("\r\n", "\n")
        dFront = frontmatter(sText)
        lFiles = skillFiles(sSkills, sName)
        dKinds = {}
        for sPath, sInside in lFiles:
            if "/" in sInside: dKinds[sInside.split("/")[0]] = dKinds.get(sInside.split("/")[0], 0) + 1
        sBody = sText.split("\n---", 2)[-1] if sText.startswith("---") else sText
        lSkills.append({"name": sName, "description": dFront.get("description", ""), "group": dFront.get("metadata.group", "") or "Other Skills",
                        "summary": sentence(dSummary.get(sName, "") or re.split(r"(?<=[.!?])\s+", dFront.get("description", ""))[0]),
                        "files": len(lFiles), "kinds": dKinds, "words": len(re.findall(r"\w+", sBody)),
                        "license": dFront.get("license", "")})
        if sName not in dSummary: logLine("NOTE %s has no line in AGENTS.md; its description's first sentence is used" % sName)
    return sSkills, lSkills


def contentsText(dKinds):
    """SKILL.md and what is beside it: "SKILL.md, 3 references and 2 scripts"."""
    dNouns = {"references": ("reference note", "reference notes"), "scripts": ("script", "scripts"), "assets": ("asset", "assets"),
              "examples": ("example", "examples"), "templates": ("template", "templates")}
    lsParts = ["SKILL.md"]
    for sKind in sorted(dKinds):
        sOne, sMany = dNouns.get(sKind, ("file in " + sKind, "files in " + sKind))
        lsParts.append(countNoun(dKinds[sKind], sOne, sMany))
    return listed(lsParts)


def anchor(sText):
    return re.sub(r"[^a-z0-9]+", "-", sText.lower()).strip("-")


def pageText(lSkills, dSizes):
    """The Markdown of the page. Links are reference-style, so no address is read aloud in the body."""
    lsGroups = sorted({d["group"] for d in lSkills}, key=str.lower)
    dByGroup = {g: [d for d in lSkills if d["group"] == g] for g in lsGroups}
    iFiles = sum(d["files"] for d in lSkills)
    lsRefs = []
    def ref(sLabel, sUrl):
        lsRefs.append("[%s]: %s" % (sLabel, sUrl))
        return sLabel
    sRepo = "https://github.com/%s/HomerDev" % sOwner
    sTree = sRepo + "/tree/main/.claude/skills/"
    lsOut = ["---",
             'title: "Homer Skills"',
             'subtitle: "A Directory of %s for AI Agents from the Homer Development Kit"' % countNoun(len(lSkills), "Skill"),
             'description: "Free skills that teach AI agents to build accessible Windows programs, documents, books, databases, installers and spoken tutorials for screen reader users, each ready to download for Claude, ChatGPT, Codex, Copilot, Gemini, Grok and other agents."',
             'author: "Jamal Mazrui"',
             "lang: en-US",
             'license: "CC BY-SA 4.0"',
             'license_url: "https://creativecommons.org/licenses/by-sa/4.0/"',
             "keywords:", "  - accessibility", "  - agent skills", "  - AI agents", "  - screen readers", "  - SKILL.md",
             "---", "", "# Homer Skills", "",
             "%s that teach an AI agent how Homer work is done, in %s, each ready to download." % (countNoun(len(lSkills), "skill"), countNoun(len(lsGroups), "group")),
             "", "## Contents {#contents}", "",
             "- [Introduction](#introduction)", "- [By the Numbers](#by-the-numbers)", "- [Getting the Skills](#getting-the-skills)"]
    for sGroup in lsGroups:
        lsOut.append("- [%s](#g-%s)" % (sGroup, anchor(sGroup)))
        for d in dByGroup[sGroup]: lsOut.append("    - [%s](#%s)" % (d["name"], d["name"]))
    lsOut += ["- [Appendix: Skills by Name](#appendix-skills-by-name)", "",
              "## Introduction {#introduction}", "",
              "A skill is a folder of instructions that an AI agent reads before it does one kind of work. Its file "
              "SKILL.md says what the skill is for and the steps to follow; notes and scripts may sit beside it. The "
              "agent reads only a skill's short description until a task calls for it, then reads the rest.", "",
              "These skills come from the [Homer Development Kit][%s], the shared code and rules behind the Homer "
              "Tools: free Windows programs, documents, books and databases made for people who work by keyboard and "
              "screen reader. Each skill holds what was learned the hard way about one kind of that work, so an agent "
              "does it the Homer way the first time. Some are useful well beyond the kit, such as making machine text "
              "readable, writing a help guide from a publisher's pages, or a walking guide to a convention hotel." % ref("kit", sRepo), "",
              "Every skill follows the open [Agent Skills standard][%s], so the same folder works in Claude, ChatGPT, "
              "Codex, GitHub Copilot, Gemini, Grok Build and many other agents. Skills are grouped by kind of work, "
              "under a heading at level 2 for each group, in alphabetical order. Each skill's name is a heading at "
              "level 3 and a link straight to its download. Under it come what it does, a link to its source, and "
              "what it holds, in alphabetical order. An appendix lists the skills again by name." % ref("standard", "https://agentskills.io/"), "",
              "Every skill is free under the [MIT license][%s]. This page's own text is available under "
              "[CC BY-SA 4.0][%s]. It is made from the skills themselves each time it is posted, so it always shows "
              "the kit's current set." % (ref("mit", sRepo + "/blob/main/License.md"), ref("cc-by-sa", "https://creativecommons.org/licenses/by-sa/4.0/")), "",
              "## By the Numbers {#by-the-numbers}", ""]
    lsOut.append("- %s in %s: %s." % (countNoun(len(lSkills), "skill"), countNoun(len(lsGroups), "group"),
                                       "; ".join("%s, %d" % (g, len(dByGroup[g])) for g in lsGroups)))
    iScripts = len([d for d in lSkills if d["kinds"].get("scripts")])
    iRefs = len([d for d in lSkills if d["kinds"].get("references")])
    lsOut.append("- %s in all; %d of the skills carry scripts that do the work, and %d carry reference notes to read first." % (countNoun(iFiles, "file"), iScripts, iRefs))
    dBig = max(lSkills, key=lambda d: d["files"])
    dLong = max(lSkills, key=lambda d: d["words"])
    lsOut.append("- The skill with the most files is [%s](#%s), with %d; the longest SKILL.md is [%s](#%s)'s, at %s words." % (
        dBig["name"], dBig["name"], dBig["files"], dLong["name"], dLong["name"], "{:,}".format(dLong["words"])))
    lsOut.append("- All %d download as one zip of %s." % (len(lSkills), sizeText(dSizes["*"])))
    lsOut += ["", "## Getting the Skills {#getting-the-skills}", "",
              "Each skill's heading downloads a zip that holds its folder. [One zip holds them all][%s], a folder "
              "for each, ready to unzip into an agent's skills folder." % ref("all", "skills/HomerSkills.zip"), "",
              "On Windows, the kit's installer, [HomerDev_setup.exe][%s], does this for every agent it finds: it links "
              "each skill into that agent's folder, so an updated kit updates them all at once." % ref("setup", sRepo + "/releases/latest/download/HomerDev_setup.exe"), "",
              "Each agent takes a skill its own way, listed here in alphabetical order. In the folder names, `~` means "
              "your home folder, such as `C:\\Users\\YourName` on Windows.", "",
              "- **ChatGPT**, in a workspace where skills are turned on: choose Skills, then Create, then Upload from "
              "your computer, and pick the skill's zip.",
              "- **Claude**, on the web or desktop: open Customize, then Skills, press the plus button, choose Create "
              "skill, then Upload a skill, and pick the skill's zip. Code execution must be on in Settings, "
              "Capabilities. A skill added there also loads in Claude Code and the Office add-ins under the same account.",
              "- **Claude Code**: add the whole kit as a plugin with `/plugin marketplace add JamalMazrui/HomerDev`, "
              "then `/plugin install homer-dev@homer-dev-kit`; or unzip skills into `~/.claude/skills`.",
              "- **Codex**: unzip skills into `~/.agents/skills`, or into a project's `.agents/skills`.",
              "- **GitHub Copilot**: unzip skills into `~/.copilot/skills` or `~/.agents/skills`, or into a project's "
              "`.github/skills`.",
              "- **Gemini CLI and Antigravity**: unzip skills into `~/.agents/skills`.",
              "- **Grok Build**: unzip skills into `~/.grok/skills` or `~/.agents/skills`.",
              "- **Other agents**: most agents that follow the standard read `~/.agents/skills`. An installer that "
              "reads a site's skills index, such as `npx skills add`, can be given this page's address; the index is "
              "at [.well-known/agent-skills/index.json][%s]." % ref("index", ".well-known/agent-skills/index.json"), ""]
    for sGroup in lsGroups:
        lsOut += ["## %s (%d) {#g-%s}" % (sGroup, len(dByGroup[sGroup]), anchor(sGroup)), "", dGroupNotes.get(sGroup, ""), ""]
        for d in dByGroup[sGroup]:
            sName = d["name"]
            lsOut += ["### [%s][zip-%s] {#%s}" % (sName, sName, sName), "", d["summary"], "",
                      "[Source page][src-%s]" % sName, "",
                      "**Contents:** %s" % contentsText(d["kinds"]), "",
                      "**Download size:** %s" % sizeText(dSizes[sName]), ""]
            lsRefs.append("[zip-%s]: skills/%s.zip" % (sName, sName))
            lsRefs.append("[src-%s]: %s%s" % (sName, sTree, sName))
    lsOut += ["## Appendix: Skills by Name {#appendix-skills-by-name}", ""]
    for d in sorted(lSkills, key=lambda d: d["name"]):
        lsOut.append("- [%s](#%s): %s" % (d["name"], d["name"], d["summary"]))
    lsOut += ["", "<!-- Link definitions: kept here, so no address is read aloud in the text above. -->", ""]
    lsOut += lsRefs
    return "\n".join(lsOut).replace("\n\n\n", "\n\n") + "\n"


def indexJson(lSkills, dDigests):
    lEntries = [{"name": d["name"], "type": "archive", "description": d["description"][:1024],
                 "url": d["name"] + ".tar.gz", "digest": "sha256:" + dDigests[d["name"]]} for d in lSkills]
    return json.dumps({"$schema": sSchema, "skills": lEntries}, indent=2, ensure_ascii=False) + "\n"


def llmsText(lSkills):
    lsOut = ["# Homer Skills", "",
             "> Skills that teach AI agents to build accessible Windows programs, documents, books, databases, installers "
             "and spoken tutorials for screen reader users, from the Homer Development Kit. Each follows the Agent Skills "
             "standard; download a skill's zip, or read its SKILL.md at its source.", "", "## Skills", ""]
    for d in lSkills:
        lsOut.append("- [%s](https://github.com/%s/HomerDev/blob/main/.claude/skills/%s/SKILL.md): %s" % (d["name"], sOwner, d["name"], d["summary"]))
    lsOut += ["", "## Downloads", "", "- [All skills in one zip](skills/HomerSkills.zip)",
              "- [Discovery index](.well-known/agent-skills/index.json)",
              "- [The kit's instructions for agents](https://github.com/%s/HomerDev/blob/main/AGENTS.md)" % sOwner]
    return "\n".join(lsOut) + "\n"


def defaultFolder(sKit):
    """MyPages' HomerSkills folder on any drive, else the kit's work folder."""
    lsTries = []
    if os.name == "nt":
        lsTries = ["%s:\\MyPages" % s for s in string.ascii_uppercase if os.path.isdir("%s:\\" % s)]
    lsTries.append(os.path.join(os.path.dirname(sKit), "MyPages"))
    for sTry in lsTries:
        if os.path.isdir(os.path.join(sTry, "pages")): return os.path.join(sTry, "pages", sPage)
    return os.path.join(sKit, "work", sPage)


def build(sKit, sOut):
    """Writes everything into sOut; returns the number of files written."""
    sSkills, lSkills = catalog(sKit)
    if not lSkills: raise RuntimeError("no skill was found in " + sSkills)
    iWritten = 0
    dSizes, dDigests, lAll = {}, {}, []
    for d in lSkills:
        binZip = packSkill(sSkills, d["name"])
        dSizes[d["name"]] = len(binZip)
        iWritten += writeIfChanged(os.path.join(sOut, "skills", d["name"] + ".zip"), binZip)
        binArchive = archiveBytes(sSkills, d["name"])
        dDigests[d["name"]] = hashlib.sha256(binArchive).hexdigest()
        iWritten += writeIfChanged(os.path.join(sOut, ".well-known", "agent-skills", d["name"] + ".tar.gz"), binArchive)
        lAll += [(sPath, d["name"] + "/" + sInside) for sPath, sInside in skillFiles(sSkills, d["name"])]
    binAll = zipBytes(lAll)
    dSizes["*"] = len(binAll)
    iWritten += writeIfChanged(os.path.join(sOut, "skills", "HomerSkills.zip"), binAll)
    lsNames = {d["name"] for d in lSkills}
    for sSub, sExt in (("skills", ".zip"), (os.path.join(".well-known", "agent-skills"), ".tar.gz")):
        sDir = os.path.join(sOut, sSub)
        for sFile in sorted(os.listdir(sDir)):
            sStem = sFile[:-len(sExt)] if sFile.endswith(sExt) else ""
            if sStem and sStem != "HomerSkills" and sStem not in lsNames:
                os.remove(os.path.join(sDir, sFile)); logLine("removed %s, a skill that is gone" % os.path.join(sDir, sFile)); iWritten += 1
    def text(s): return s.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")
    iWritten += writeIfChanged(os.path.join(sOut, sPage + ".md"), b"\xef\xbb\xbf" + text(pageText(lSkills, dSizes)))
    iWritten += writeIfChanged(os.path.join(sOut, ".well-known", "agent-skills", "index.json"), indexJson(lSkills, dDigests).encode("utf-8"))
    iWritten += writeIfChanged(os.path.join(sOut, "llms.txt"), text(llmsText(lSkills)))
    iWritten += writeIfChanged(os.path.join(sOut, "_config.yml"), text("theme: jekyll-theme-cayman\ntitle: Homer Skills\ninclude:\n  - .well-known\n"))
    for d in lSkills:
        logLine("SKILL %s: group %s, %d files, zip %s" % (d["name"], d["group"], d["files"], sizeText(dSizes[d["name"]])))
    return iWritten, len(lSkills)


def main(lsArgs):
    global sLogPath
    sKit = kitFolder()
    sLogs = os.path.join(sKit, "logs")
    try:
        os.makedirs(sLogs, exist_ok=True)
        open(os.path.join(sLogs, ".write-test"), "w").close(); os.remove(os.path.join(sLogs, ".write-test"))
    except OSError:
        sLogs = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "HomerDev", "logs")
        os.makedirs(sLogs, exist_ok=True)
    sLogPath = os.path.join(sLogs, "HomerDev-skillsPage-%s.log" % datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    logLine("skillsPage %s; Python %s on %s; kit %s; working folder %s; command line %s" % (
        os.path.abspath(__file__), platform.python_version(), platform.platform(), sKit, os.getcwd(), " ".join(sys.argv)))
    lsFolders = [s for s in lsArgs if not s.startswith("-")]
    sOut = os.path.abspath(lsFolders[0]) if lsFolders else defaultFolder(sKit)
    logLine("output folder %s" % sOut)
    iWritten, iSkills = build(sKit, sOut)
    say("Homer Skills page: %s in %s; %s." % (countNoun(iSkills, "skill"), sOut, countNoun(iWritten, "file") + " written" if iWritten else "nothing changed"))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as oError:
        import traceback
        logLine("CRASH " + traceback.format_exc())
        print("skillsPage stopped: %s. The log is %s." % (oError, sLogPath))
        sys.exit(1)
