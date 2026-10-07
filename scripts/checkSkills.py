r"""checkSkills.py -- check every Claude skill in a project against the rules a skill must meet to load and to be chosen.
Part of the HomerDev kit. Run it through checkSkills.cmd.

    checkSkills                 the skills of the project this is run from (its .claude\skills folder)
    checkSkills D:\Work\DbDo    another project's skills

WHY A SCRIPT (1.59.0). Anthropic's Complete Guide to Building Skills for Claude (January 2026) gives exact rules a
skill must meet, and advises checking exact rules with a script rather than by reading, since code is deterministic and
reading is not. Its rules, checked here:

  problems (exit code 1)
    - the folder name is kebab-case: lower case letters, digits and hyphens
    - the main file is named exactly SKILL.md
    - the frontmatter opens and closes with --- lines
    - name: is present and equals the folder name, at most 64 characters, with no hyphen at its start or end and no
      two hyphens together, and holds neither "claude" nor "anthropic", which are reserved
    - the frontmatter holds only the keys the standard allows: name, description, license, allowed-tools, metadata,
      compatibility (1.60.0, from the skill-creator's own validator, quick_validate.py)
    - description: is present and at most 1024 characters
    - no angle bracket, < or >, in any frontmatter value, since the frontmatter goes into the system prompt and a
      skill holding one is refused at upload ("Invalid frontmatter"); YAML's own > and | markers are fine
    - compatibility:, when present, is at most 500 characters
    - no README.md inside the skill folder; a skill's documentation goes in SKILL.md or references
    - (a notice since 1.60.0) SKILL.md's body past 5,000 words: the guide's advice, not a rule -- Anthropic's own
      skill-creator and claude-api skills pass it, and the official validator does not count words
  notices
    - the description does not say when to use the skill ("Use when ...", "Use this skill whenever ...")
    - a body over 3,000 words, on its way to the limit, or over 500 lines, the skill-creator's ideal
    - a relative link in SKILL.md to a file that is not there (some are copies the kit's build makes from help)

Every run writes <project>\logs\<Project>-checkSkills-yyyyMMdd-HHmmss.log. Exit codes: 0 no problems; 1 problems; 2 no
skills folder.
"""

import datetime, os, platform, re, sys

c_iBodyLines = 500
c_iBodyNotice = 3000
c_iBodyWords = 5000
c_iCompatibilityChars = 500
c_iDescriptionChars = 1024
c_iNameChars = 64
c_lsAllowedKeys = ["allowed-tools", "compatibility", "description", "license", "metadata", "name"]
c_lsReservedWords = ["anthropic", "claude"]
c_sWhenPattern = r"\b(use (this skill |it )?(when|whenever|for|if)|load (this skill )?whenever|when (the user|a user|someone|you|asked)|trigger)"

lsLog = []
sLogPath = ""


def log(sText):
    """A timed line in the log, written as it goes."""
    lsLog.append(datetime.datetime.now().strftime("%H:%M:%S") + " " + sText)
    if sLogPath:
        with open(sLogPath, "wb") as oFile: oFile.write(b"\xef\xbb\xbf" + ("\r\n".join(lsLog) + "\r\n").encode("utf-8"))
    return True


def say(sText):
    """A line for the person, logged too."""
    print(sText, flush=True)
    return log("SAY " + sText)


def projectRoot(sStart):
    """The project folder: the given one, or this script's project when run from a scripts folder."""
    sDir = os.path.abspath(sStart)
    if os.path.basename(sDir).lower() == "scripts" and os.path.isdir(os.path.join(os.path.dirname(sDir), ".claude")): return os.path.dirname(sDir)
    return sDir


def frontmatterValues(sFront):
    """{key: value} from a skill's frontmatter, folded and literal blocks joined, the > and | markers dropped."""
    dValues, sKey = {}, ""
    for sLine in sFront.split("\n"):
        oKey = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", sLine)
        if oKey:
            sKey = oKey.group(1)
            sValue = oKey.group(2).strip()
            dValues[sKey] = "" if re.fullmatch(r"[>|][-+]?", sValue) else sValue
        elif sKey and sLine.startswith((" ", "\t")):
            dValues[sKey] = (dValues[sKey] + " " + sLine.strip()).strip()
    return {k: v.strip().strip("\"'") for k, v in dValues.items()}


def checkSkill(sSkillsDir, sName, lProblems, lNotices):
    """Every rule above, for one skill folder; each finding is added to the lists as text naming the skill."""
    sDir = os.path.join(sSkillsDir, sName)
    def problem(sText): lProblems.append(sName + ": " + sText)
    def notice(sText): lNotices.append(sName + ": " + sText)
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", sName): problem("the folder name is not kebab-case (lower case letters, digits and hyphens)")
    lFiles = os.listdir(sDir)
    if "SKILL.md" not in lFiles:
        lNear = [s for s in lFiles if s.lower() == "skill.md"]
        problem("no SKILL.md" + (" (found " + lNear[0] + "; the name must be exactly SKILL.md)" if lNear else ""))
        return False
    if any(s.lower() == "readme.md" for s in lFiles): problem("a README.md inside the skill folder; put its text in SKILL.md or references")
    sText = open(os.path.join(sDir, "SKILL.md"), encoding="utf-8-sig").read().replace("\r\n", "\n")
    oFront = re.match(r"---[ \t]*\n(.*?)\n---[ \t]*\n(.*)$", sText, re.S)
    if not oFront:
        problem("the frontmatter does not open and close with --- lines")
        return False
    dValues = frontmatterValues(oFront.group(1))
    sBody = oFront.group(2)
    sNameValue = dValues.get("name", "")
    if len(sNameValue) > c_iNameChars: problem("name: is %d characters; the limit is %d" % (len(sNameValue), c_iNameChars))
    if sNameValue.startswith("-") or sNameValue.endswith("-") or "--" in sNameValue: problem("name: may not start or end with a hyphen, or hold two hyphens together")
    lUnknown = sorted(k for k in re.findall(r"(?m)^([A-Za-z][\w-]*):", oFront.group(1)) if k not in c_lsAllowedKeys)
    if lUnknown: problem("the frontmatter holds keys the standard does not allow: " + ", ".join(lUnknown) + " (allowed: " + ", ".join(c_lsAllowedKeys) + "); put custom values under metadata:")
    if dValues.get("name", "") != sName: problem("name: is \"" + dValues.get("name", "") + "\"; it must equal the folder name")
    for sWord in c_lsReservedWords:
        if sWord in dValues.get("name", "").lower(): problem("name: holds \"" + sWord + "\", which is reserved")
    sDescription = dValues.get("description", "")
    if not sDescription: problem("no description:")
    elif len(sDescription) > c_iDescriptionChars: problem("description: is %d characters; the limit is %d" % (len(sDescription), c_iDescriptionChars))
    if sDescription and not re.search(c_sWhenPattern, sDescription, re.I): notice("the description does not say when to use the skill (\"Use when ...\")")
    for sKey, sValue in dValues.items():
        if re.search(r"[<>]", sValue): problem(sKey + ": holds an angle bracket (" + re.search(r".{0,20}[<>].{0,20}", sValue).group(0) + "); the frontmatter may hold none")
    if len(dValues.get("compatibility", "")) > c_iCompatibilityChars: problem("compatibility: is over %d characters" % c_iCompatibilityChars)
    iWords = len(sBody.split())
    iLines = sBody.count("\n") + 1
    if iWords > c_iBodyWords: notice("SKILL.md's body is %d words, past the guide's advice of %d; move detail into references" % (iWords, c_iBodyWords))
    elif iWords > c_iBodyNotice: notice("SKILL.md's body is %d words, on its way to the guide's %d" % (iWords, c_iBodyWords))
    if iLines > c_iBodyLines: notice("SKILL.md's body is %d lines; the skill-creator's ideal is %d, with detail in references" % (iLines, c_iBodyLines))
    for sLink in re.findall(r"\]\(([^)#\s]+)\)", sBody):
        if re.match(r"^[a-z]+:", sLink, re.I): continue
        if not os.path.exists(os.path.join(sDir, sLink)): notice("links to " + sLink + ", which is not there (a copy the kit's build makes, or a broken link)")
    log(sName + ": description %d characters, body %d words" % (len(sDescription), iWords))
    return True


def main():
    global sLogPath
    sProject = projectRoot(sys.argv[1] if len(sys.argv) > 1 else os.getcwd())
    sLogs = os.path.join(sProject, "logs")
    os.makedirs(sLogs, exist_ok=True)
    sLogPath = os.path.join(sLogs, os.path.basename(sProject) + "-checkSkills-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".log")
    log("checkSkills started: " + os.path.abspath(__file__))
    log("python " + sys.version.split()[0] + "; platform " + platform.platform() + "; cwd " + os.getcwd() + "; command line " + " ".join(sys.argv))
    log("project " + sProject)
    sSkillsDir = os.path.join(sProject, ".claude", "skills")
    if not os.path.isdir(sSkillsDir):
        say("No .claude\\skills folder in " + sProject + ", so there are no skills to check.")
        return 2
    lSkills = sorted(s for s in os.listdir(sSkillsDir) if os.path.isdir(os.path.join(sSkillsDir, s)))
    lProblems, lNotices = [], []
    for sName in lSkills: checkSkill(sSkillsDir, sName, lProblems, lNotices)
    for s in lNotices: log("NOTICE " + s)
    for s in lProblems: log("PROBLEM " + s)
    if lNotices: say("Notices:\n" + "\n".join("  " + s for s in lNotices))
    if lProblems: say("Problems:\n" + "\n".join("  " + s for s in lProblems))
    say("%d skill%s checked, %d problem%s." % (len(lSkills), "" if len(lSkills) == 1 else "s", len(lProblems), "" if len(lProblems) == 1 else "s"))
    return 1 if lProblems else 0


if __name__ == "__main__":
    sys.exit(main())
