"""connectAI.py -- tell the AI command-line tools on this computer where the Homer Development Kit is, once.

    connectAI              connect every AI tool found: Claude Code, OpenAI Codex, Gemini CLI and Antigravity
    connectAI --remove     take back out everything connectAI put in
    connectAI --check      say what is connected, and change nothing

WHY (1.67.0). An AI tool reads the kit's AGENTS.md and skills only when it is started in the kit's own folder. A blind
vibe coder works in their own project, C:\\MyApp, where nothing points to the kit, and should not have to explain
where it is in every session. Each tool reads a personal instruction file in every project, and personal skill
folders. This script puts a short pointer to the kit in each personal instruction file, between two marker lines it
alone writes, and links each of the kit's skills into each personal skills folder -- a Windows junction, so the skill
is always the kit's current one, never a copy that drifts. Only tools whose folder exists in the user profile are
touched. A skill folder of the person's own with the same name is never replaced; the log names it.

WHERE EACH TOOL LOOKS (checked 11 October 2026; these move, and the kit's AGENTS.md is the fallback):
    claude    instructions %USERPROFILE%\\.claude\\CLAUDE.md;  skills %USERPROFILE%\\.claude\\skills
    codex     instructions %USERPROFILE%\\.codex\\AGENTS.md;   skills %USERPROFILE%\\.agents\\skills, %USERPROFILE%\\.codex\\skills
    gemini    instructions %USERPROFILE%\\.gemini\\GEMINI.md;  skills %USERPROFILE%\\.gemini\\config\\skills,
              %USERPROFILE%\\.gemini\\antigravity\\skills, %USERPROFILE%\\.agents\\skills (Antigravity and Gemini CLI)

THE LOG goes to <kit>\\logs when the kit's folder can be written, else %LOCALAPPDATA%\\HomerDev\\logs (the installed
kit in Program Files is read-only to a person), as HomerDev-connectAI-<stamp>.log.
"""

import datetime, os, platform, shutil, subprocess, sys

c_sBegin = "<!-- HomerDev begin: written by the Homer Development Kit's connectAI; connectAI --remove takes it out -->"
c_sEnd = "<!-- HomerDev end -->"
c_dTools = {  # tool: (profile folder, instruction file, [skills folders]) -- all relative to the user profile
    "claude": (".claude", ".claude\\CLAUDE.md", [".claude\\skills"]),
    "codex": (".codex", ".codex\\AGENTS.md", [".agents\\skills", ".codex\\skills"]),
    "gemini": (".gemini", ".gemini\\GEMINI.md", [".gemini\\config\\skills", ".gemini\\antigravity\\skills", ".agents\\skills"]),
}

lsLog = []
sLogPath = ""


def logLine(sText):
    lsLog.append(datetime.datetime.now().strftime("%H:%M:%S ") + sText)
    if sLogPath:
        bNew = not os.path.exists(sLogPath)
        with open(sLogPath, "ab") as f: f.write((b"\xef\xbb\xbf" if bNew else b"") + (lsLog[-1] + "\r\n").encode("utf-8"))


def say(sText):
    print(sText)
    logLine("SAY " + sText)


def inProfile(sHome, sRelative):
    """A path under the profile, from the Windows-style relative path in c_dTools."""
    return os.path.join(sHome, *sRelative.split("\\"))


def kitFolder():
    """The kit: the folder above this script's scripts folder."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def pointerText(sKit):
    """The block each instruction file gets: where the kit is, and what to read first. Short, since it is always on."""
    return "\r\n".join([
        c_sBegin,
        "## The Homer Development Kit (HomerDev)",
        "",
        "The Homer Development Kit is installed at %s (the HomerDev environment variable names it too)." % sKit,
        "It builds accessible Windows programs, documents, books, databases, installers and spoken tutorials for",
        "screen reader users. When a task involves a Homer app or project, or the person mentions Homer or HomerDev:",
        "",
        "1. Read %s first: the conventions, the build cycle and where everything is." % os.path.join(sKit, "AGENTS.md"),
        "2. Use the skill that matches the task; the kit's skills are linked into this tool's skills folder, and are",
        "   also in %s." % os.path.join(sKit, ".claude", "skills"),
        "3. Use the kit's code rather than writing your own: shared classes in %s and %s, templates in %s." % (
            os.path.join(sKit, "exec", "CSharp"), os.path.join(sKit, "exec", "Python"), os.path.join(sKit, "Templates")),
        "4. The cycle in a project folder is build_release: build, tidy, push and release. Read the logs it writes in",
        "   the project's logs folder before suggesting a fix.",
        c_sEnd, ""])


def setBlock(sPath, sBlock):
    """Puts sBlock in the file between the marker lines, replacing an earlier block; "" removes it. Returns what it did."""
    sText = ""
    if os.path.isfile(sPath):
        sText = open(sPath, "rb").read().decode("utf-8-sig", errors="replace")
    iStart, iEnd = sText.find(c_sBegin), sText.find(c_sEnd)
    sBefore, sAfter = (sText[:iStart], sText[iEnd + len(c_sEnd):]) if iStart >= 0 and iEnd > iStart else (sText, "")
    sAfter = sAfter.lstrip("\r\n")
    if not sBlock:
        if iStart < 0: return "nothing to remove"
        sNew = (sBefore.rstrip("\r\n") + "\r\n" if sBefore.strip() else "") + sAfter
    else:
        sNew = (sBefore.rstrip("\r\n") + "\r\n\r\n" if sBefore.strip() else "") + sBlock + (("\r\n" + sAfter) if sAfter.strip() else "")
    if sNew == sText: return "already current"
    os.makedirs(os.path.dirname(sPath), exist_ok=True)
    if sNew.strip(): open(sPath, "wb").write(sNew.encode("utf-8"))
    elif os.path.exists(sPath): os.remove(sPath)
    return ("updated" if iStart >= 0 else "added") if sBlock else "removed"


def linkTarget(sPath):
    """Where a junction or symbolic link points, or "" when sPath is an ordinary folder or absent."""
    try:
        if os.path.islink(sPath) or (hasattr(os.path, "isjunction") and os.path.isjunction(sPath)): return os.path.realpath(sPath)
    except OSError:
        pass
    return ""


def makeLink(sLink, sTarget):
    """A Windows junction, which needs no administrator rights; a symbolic link elsewhere."""
    if os.name == "nt":
        oDone = subprocess.run(["cmd", "/c", "mklink", "/J", sLink, sTarget], capture_output=True, text=True)
        logLine("mklink /J %s %s: exit %d %s" % (sLink, sTarget, oDone.returncode, (oDone.stdout + oDone.stderr).strip()))
        return oDone.returncode == 0
    os.symlink(sTarget, sLink, target_is_directory=True)
    return True


def removeLink(sLink):
    if os.name == "nt": os.rmdir(sLink)  # removes a junction, never what it points to
    else: os.unlink(sLink)


def main(lsArgs):
    global sLogPath
    bRemove, bCheck = "--remove" in lsArgs, "--check" in lsArgs
    lsUnknown = [s for s in lsArgs if s not in ("--remove", "--check")]
    sKit = kitFolder()
    sLogs = os.path.join(sKit, "logs")
    try:
        os.makedirs(sLogs, exist_ok=True)
        open(os.path.join(sLogs, ".write-test"), "w").close(); os.remove(os.path.join(sLogs, ".write-test"))
    except OSError:
        sLogs = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "HomerDev", "logs")
        os.makedirs(sLogs, exist_ok=True)
    sLogPath = os.path.join(sLogs, "HomerDev-connectAI-%s.log" % datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    logLine("connectAI %s; Python %s on %s; kit %s; working folder %s; command line %s" % (
        os.path.abspath(__file__), platform.python_version(), platform.platform(), sKit, os.getcwd(), " ".join(sys.argv)))
    if lsUnknown:
        say("Unknown option %s. The options are --remove and --check. Nothing was changed." % " ".join(lsUnknown)); return 2
    sHome = os.path.expanduser("~")
    sSkills = os.path.join(sKit, ".claude", "skills")
    lsSkills = sorted(s for s in os.listdir(sSkills) if os.path.isfile(os.path.join(sSkills, s, "SKILL.md"))) if os.path.isdir(sSkills) else []
    iFound = iChanged = 0
    lsConnected = []
    lsDoneFolders = set()
    for sTool in sorted(c_dTools):
        sProfile, sInstructions, lsSkillDirs = c_dTools[sTool]
        if not os.path.isdir(inProfile(sHome, sProfile)):
            logLine("%s: no %s folder in the profile, so it is not installed or never run; skipped" % (sTool, sProfile)); continue
        iFound += 1
        lsConnected.append({"claude": "Claude Code", "codex": "Codex", "gemini": "Gemini CLI with Antigravity"}.get(sTool, sTool))
        sFile = inProfile(sHome, sInstructions)
        if bCheck:
            bHas = os.path.isfile(sFile) and c_sBegin in open(sFile, "rb").read().decode("utf-8-sig", errors="replace")
            say("%s: %s %s the kit's pointer." % (sTool, sFile, "holds" if bHas else "does not hold"))
        else:
            sDid = setBlock(sFile, "" if bRemove else pointerText(sKit))
            logLine("%s: %s %s" % (sTool, sFile, sDid))
            if sDid in ("added", "updated", "removed"): iChanged += 1
        for sDir in lsSkillDirs:
            sFolder = inProfile(sHome, sDir)
            if os.path.normcase(sFolder) in lsDoneFolders: continue
            lsDoneFolders.add(os.path.normcase(sFolder))
            iLinked = iKept = 0
            for sSkill in lsSkills:
                sLink, sTarget = os.path.join(sFolder, sSkill), os.path.join(sSkills, sSkill)
                sNow = linkTarget(sLink)
                if bCheck:
                    if sNow and os.path.normcase(sNow) == os.path.normcase(os.path.realpath(sTarget)): iLinked += 1
                    continue
                if sNow:
                    if os.path.normcase(sNow).startswith(os.path.normcase(os.path.realpath(sKit))) or bRemove:
                        removeLink(sLink); logLine("removed link %s" % sLink)
                        if bRemove: iChanged += 1
                    else:
                        iKept += 1; logLine("kept %s: a link to %s, not the kit" % (sLink, sNow)); continue
                elif os.path.exists(sLink):
                    iKept += 1; logLine("kept %s: a folder of the person's own, never replaced" % sLink); continue
                if bRemove: continue
                os.makedirs(sFolder, exist_ok=True)
                if makeLink(sLink, sTarget): iLinked += 1
            if bCheck: say("%s: %d of %d skills linked in %s." % (sTool, iLinked, len(lsSkills), sFolder))
            elif not bRemove:
                logLine("%s: %d skills linked in %s%s" % (sTool, iLinked, sFolder, ("; %d kept as they were" % iKept) if iKept else ""))
                iChanged += 1 if iLinked else 0
    # ONE LINE FOR THE SETUP PROGRAM (1.72.0): HomerDev's setup connects the AI tools itself and says in its Results
    # box what it found, from this file; the dialog's Connect AI tools button is gone.
    def writeResult(sLine):
        if bCheck or bRemove: return
        try:
            sDir = os.path.join(os.environ.get("LOCALAPPDATA", ""), "HomerDev")
            os.makedirs(sDir, exist_ok=True)
            with open(os.path.join(sDir, "connectAI-result.txt"), "w", encoding="utf-8") as oFile: oFile.write(sLine)
        except Exception as oError: logLine("result line not written: %s" % oError)
    if iFound == 0:
        say("No AI command-line tool was found: none of .claude, .codex or .gemini is in %s. Run a tool once, then this again." % sHome)
        writeResult("AI tools: none found -- no Claude Code, Codex or Gemini in this profile. Run one once, then scripts\\connectAI in the kit's folder.")
        return 0
    # "Claude Code, and Gemini CLI with Antigravity": a comma before the last name, so a name with its own "with" reads
    # as one item (1.72.1; it read "Claude Code and Gemini CLI and Antigravity").
    writeResult("AI tools connected to the kit: %s." % (lsConnected[0] if len(lsConnected) == 1 else ", ".join(lsConnected[:-1]) + ", and " + lsConnected[-1]))
    if not bCheck:
        say(("Took the kit back out of %d AI tool%s." if bRemove else "Connected %d AI tool%s to the Homer Development Kit at " + sKit + ".") % (iFound, "" if iFound == 1 else "s"))
        if not bRemove: say("In any project, ask your AI about Homer or HomerDev, and it knows where to look. The log is " + sLogPath + ".")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as oError:
        import traceback
        logLine("CRASH " + traceback.format_exc())
        print("connectAI stopped: %s. The log is %s." % (oError, sLogPath))
        sys.exit(1)
