r"""
evalSkills.py -- measure whether the Homer skills make an AI write a better
program. Part of the HomerDev kit; run it from the kit through evalSkills.cmd.

    evalSkills                 3 runs without the skills, 3 with them
    evalSkills --runs 5        5 of each
    evalSkills --model sonnet  the model Claude Code should use
    evalSkills --dry-run       set up every run folder and stop: no AI is asked

WHY. Every collection of accessibility skills says it helps, and almost none
shows it. Microsoft's A11y LLM Eval found a control pass rate of 12% but tested
a single skill. The kit already teaches the comparison by hand -- ask for the
fruit basket with no conventions, then again with the three sentences -- and
this turns that lesson into numbers anyone can rerun.

WHAT IT DOES, FOR EACH RUN
  1. Makes a folder FruitBasketCs in a fresh folder under %TEMP%, outside the
     kit, so the plain runs cannot find the kit's skills or notes by accident.
  2. Plain runs get only the task. Homer runs also get the kit's .claude\skills
     copied into the folder, the kit's folder added for reading, and the three
     sentences from HomerDev.md appended to the system prompt.
  3. Runs Claude Code once, headless: claude -p with --output-format json and
     --permission-mode acceptEdits, so it can write files but not run them.
  4. Builds the program with a copy of the kit's own sample build script,
     which compiles the source together with the kit's shared classes. A plain
     program that does not use them compiles the same way.
  5. Scores it: does the source exist, does it compile, what does check find,
     and what does uiCheck find when it types two fruits and looks for them
     and for a list named Basket in the UI Automation tree a screen reader reads.

THE REPORT, logs\HomerDev-evalSkills-<stamp>.md in the kit, gives each
condition's totals and every run, and says plainly what the numbers cannot
show. Three of check's findings (encoding, logging, naming) partly measure
Homer conventions, so they are reported apart from the neutral results. The
log, logs\HomerDev-evalSkills-<stamp>.log, records every command with its exit
code and time.

COST. Each run is one Claude Code session on your plan; six runs are six
sessions. --dry-run costs nothing and shows every command first.
"""
import argparse, datetime, json, os, platform, re, shutil, subprocess, sys, tempfile, time

c_iMaxTurns = 40
c_iRuns = 3
c_iTimeoutSeconds = 1800
c_sApp = "FruitBasketCs"

c_sTask = ("Write a Windows desktop program in C#, in one source file named FruitBasketCs.cs in this folder. "
           "It must compile with the Roslyn C# compiler against the .NET Framework 4.8 as a Windows Forms "
           "program; the build will add references to System.Windows.Forms, System.Drawing and the other "
           "Framework assemblies. The program shows one window titled Fruit Basket. It has a text box for the "
           "name of a fruit, a button that adds the fruit to a list, and the list itself, named Basket. Pressing "
           "Enter in the text box adds the fruit, just as the button does, and empties the text box. The person "
           "using it is blind and uses a screen reader such as JAWS or NVDA with the keyboard alone, so every "
           "control must be reachable with the Tab key and must have a name a screen reader can speak. Write "
           "only the source file; do not compile or run it.")

c_sThreeSentences = ("Use the Homer classes in {kit}\\exec\\CSharp; build the dialog with Lbc, in the order the "
                     "user should tab. Write in Camel Type, as {kit}\\help\\CamelType_CSharp.md describes. Follow "
                     "{kit}\\help\\HomerDev.md: speak only what the screen reader cannot know, save each answer when "
                     "it is given, match nouns to counts. The Homer skills in .claude\\skills apply.")

c_sUiTest = """; uiTest.inix for evalSkills: only what the task asked for.
FileTask = uiTest

[test]
Name = FruitBasketCs takes a fruit and shows it
Run = FruitBasketCs.exe

[step]
Keys = apple{ENTER}
Wants = apple
Note = the fruit is in the basket after Enter

[step]
Keys = pear{ENTER}
Wants = pear
Note = a second fruit goes in too

[step]
Keys = {TAB}
Wants = Basket
Note = the list has the name Basket, which a screen reader speaks
"""

c_lsConventionChecks = ["encoding", "logging", "naming"]
c_lsNeutralChecks = ["keys"]

sScriptDir = os.path.dirname(os.path.abspath(__file__))
sStamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
oLog = None


def logLine(sText, sLevel=""):
    """One line in the Homer log format."""
    if oLog is None: return True
    if not sLevel:
        sLevel = "ERROR" if re.search(r"\b(ERROR|FAIL|FAILED)\b", sText) else ("WARN" if "WARN" in sText else "INFO")
    for iIndex, sPart in enumerate(str(sText).splitlines() or [""]):
        sTime = datetime.datetime.now().astimezone().isoformat(timespec="milliseconds")
        oLog.write("%s %-5s %s%s\n" % (sTime, sLevel, "| " if iIndex else "", sPart))
    oLog.flush()
    return True


def sayLine(sText=""):
    print(sText)
    logLine(sText)
    return True


def countNoun(iCount, sSingular, sPlural=None):
    return "%d %s" % (iCount, sSingular if iCount == 1 else (sPlural or sSingular + "s"))


def findKit():
    """The kit this script belongs to, or one kind.py finds anywhere."""
    sUp = os.path.dirname(sScriptDir)
    if os.path.isfile(os.path.join(sUp, "exec", "CSharp", "Lbc.cs")): return sUp
    sys.path.insert(0, sScriptDir)
    try:
        import kind
        return kind.findKit()
    except Exception:
        return ""


def runCommand(lsArgs, sCwd, iTimeout=600, dEnv=None):
    """Runs a command, logs it with its exit code and time, returns (code, output)."""
    fStart = time.time()
    try:
        oResult = subprocess.run(lsArgs, cwd=sCwd, capture_output=True, text=True, encoding="utf-8",
                                 errors="replace", timeout=iTimeout, env=dEnv)
        iCode, sOut = oResult.returncode, (oResult.stdout or "") + (oResult.stderr or "")
    except subprocess.TimeoutExpired as oError:
        iCode, sOut = -1, "TIMEOUT after %d seconds\n%s" % (iTimeout, oError.stdout or "")
    except Exception as oError:
        iCode, sOut = -2, "COULD NOT RUN: %s" % oError
    logLine("run exit=%d ms=%d cwd=\"%s\" cmd=\"%s\"" % (iCode, (time.time() - fStart) * 1000, sCwd,
            " ".join(a if len(a) < 120 else a[:117] + "..." for a in lsArgs)))
    if sOut.strip(): logLine(sOut.rstrip()[-6000:])
    return iCode, sOut


def prepareRun(sKit, sBase, sCondition, iRun):
    """Makes the run's folder and everything the build and uiCheck need."""
    sFolder = os.path.join(sBase, "%s-%d" % (sCondition, iRun), c_sApp)
    os.makedirs(sFolder)
    shutil.copyfile(os.path.join(sKit, "Templates", "samples", "build%s.cmd" % c_sApp),
                    os.path.join(sFolder, "build%s.cmd" % c_sApp))
    shutil.copyfile(os.path.join(sKit, "Templates", "samples", "version.txt"), os.path.join(sFolder, "version.txt"))
    open(os.path.join(sFolder, "uiTest.inix"), "w", encoding="utf-8-sig", newline="\r\n").write(c_sUiTest)
    if sCondition == "homer":
        shutil.copytree(os.path.join(sKit, ".claude", "skills"), os.path.join(sFolder, ".claude", "skills"))
    logLine("prepared condition=%s run=%d folder=\"%s\"" % (sCondition, iRun, sFolder))
    return sFolder


def askClaude(sClaude, sKit, sFolder, sCondition, sModel):
    """One headless Claude Code session in the run's folder."""
    lsArgs = [sClaude, "-p", c_sTask, "--output-format", "json", "--permission-mode", "acceptEdits",
              "--max-turns", str(c_iMaxTurns)]
    if sModel: lsArgs += ["--model", sModel]
    if sCondition == "homer":
        lsArgs += ["--add-dir", sKit, "--append-system-prompt", c_sThreeSentences.format(kit=sKit)]
    iCode, sOut = runCommand(lsArgs, sFolder, c_iTimeoutSeconds)
    dResult = {"exit": iCode}
    try:
        dJson = json.loads(sOut[sOut.index("{"):sOut.rindex("}") + 1])
        for sKey in ("total_cost_usd", "duration_ms", "num_turns", "is_error"):
            if sKey in dJson: dResult[sKey] = dJson[sKey]
    except Exception:
        logLine("WARN: Claude Code's output was not the JSON expected; the run is scored on its files alone")
    open(os.path.join(sFolder, "claude-output.json"), "w", encoding="utf-8").write(sOut)
    return dResult


def summaryCounts(sOut):
    """(passed, failed) from a kit checker's last line of counts."""
    oMatch = re.search(r"(\d+) checks? passed, (\d+) checks? failed", sOut)
    return (int(oMatch.group(1)), int(oMatch.group(2))) if oMatch else (0, 0)


def checkFindings(sFolder):
    """Each check finding's verdict, read from check's newest evidence report."""
    dFindings = {}
    sLogs = os.path.join(sFolder, "logs")
    lsReports = sorted(f for f in os.listdir(sLogs) if "-evidence-" in f) if os.path.isdir(sLogs) else []
    if not lsReports: return dFindings
    sSection = ""
    for sLine in open(os.path.join(sLogs, lsReports[-1]), encoding="utf-8-sig"):
        if sLine.startswith("## What was verified"): sSection = "pass"
        elif sLine.startswith("## What failed"): sSection = "fail"
        elif sLine.startswith("## What was not checked"): sSection = "skip"
        elif sLine.startswith("## "): sSection = ""
        oMatch = re.match(r"- \*\*(.+?)\*\* -- ", sLine)
        if oMatch and sSection: dFindings[oMatch.group(1)] = sSection
    return dFindings


def scoreRun(sKit, sFolder):
    """Source, build, check and uiCheck results for one run."""
    dScore = {"source": os.path.isfile(os.path.join(sFolder, c_sApp + ".cs"))}
    dEnv = dict(os.environ, HomerDev=sKit)
    if dScore["source"]:
        sText = open(os.path.join(sFolder, c_sApp + ".cs"), encoding="utf-8-sig", errors="replace").read()
        dScore["usesKit"] = bool(re.search(r"\busing\s+Homer\b|\bHomer\.", sText))
        dScore["lines"] = sText.count("\n") + 1
        runCommand(["cmd", "/c", "build%s.cmd" % c_sApp, "nobump"], sFolder, 900, dEnv)
    dScore["built"] = os.path.isfile(os.path.join(sFolder, c_sApp + ".exe"))
    iCode, sOut = runCommand([sys.executable, os.path.join(sScriptDir, "check.py"), "--path", sFolder, "--quiet"],
                             sFolder, 900, dEnv)
    dScore["check"] = checkFindings(sFolder)
    if dScore["built"]:
        iCode, sOut = runCommand([sys.executable, os.path.join(sScriptDir, "uiCheck.py"), "--path", sFolder],
                                 sFolder, 300, dEnv)
        dScore["uiPassed"], dScore["uiFailed"] = summaryCounts(sOut)
    else:
        dScore["uiPassed"], dScore["uiFailed"] = 0, 0
    logLine("score folder=\"%s\" %s" % (sFolder, json.dumps(dScore)))
    return dScore


def writeReport(sKit, sBase, dRuns, sModel, bDry):
    """The report: totals per condition, every run, and what the numbers cannot show."""
    sPath = os.path.join(sKit, "logs", "HomerDev-evalSkills-%s.md" % sStamp)
    lsLines = ["---", 'title: "Homer skills evaluation, %s"' % sStamp, "---", "",
               "# Homer skills evaluation, %s" % "%d %s" % (datetime.datetime.now().day, datetime.datetime.now().strftime("%B %Y")), "",
               "The same task was given to Claude Code without the Homer skills (plain) and with them "
               "(homer). Model: %s. Run folders: %s." % (sModel or "Claude Code's default", sBase), ""]
    if bDry:
        lsLines += ["This was a dry run: the folders were prepared and no AI was asked.", ""]
    lsLines += ["## Totals", ""]
    for sCondition in ("plain", "homer"):
        lsScores = [d["score"] for d in dRuns.get(sCondition, []) if "score" in d]
        if not lsScores: continue
        iRuns = len(lsScores)
        lsLines.append("- **%s**: %d of %s wrote the program; %d built; %d passed every uiCheck step; "
                       "uiCheck steps passed %d, failed %d." % (
                           sCondition, sum(1 for d in lsScores if d["source"]), countNoun(iRuns, "run"),
                           sum(1 for d in lsScores if d["built"]),
                           sum(1 for d in lsScores if d["built"] and d["uiFailed"] == 0 and d["uiPassed"] > 0),
                           sum(d["uiPassed"] for d in lsScores), sum(d["uiFailed"] for d in lsScores)))
        for sName in c_lsNeutralChecks + c_lsConventionChecks:
            iPass = sum(1 for d in lsScores if d["check"].get(sName) == "pass")
            sNote = " (partly a Homer convention)" if sName in c_lsConventionChecks else ""
            lsLines.append("  - check's %s finding passed in %d of %s%s." % (sName, iPass, countNoun(iRuns, "run"), sNote))
        lsCosts = [d["claude"].get("total_cost_usd") for d in dRuns[sCondition] if d.get("claude", {}).get("total_cost_usd") is not None]
        if lsCosts: lsLines.append("  - reported cost: %.2f US dollars in all." % sum(lsCosts))
    lsLines += ["", "## Every run", ""]
    for sCondition in ("plain", "homer"):
        for dRun in dRuns.get(sCondition, []):
            dScore = dRun.get("score", {})
            lsLines.append("- **%s %d**: source %s; uses the kit's classes %s; built %s; uiCheck %d passed, %d failed; "
                           "check: %s." % (sCondition, dRun["run"], "yes" if dScore.get("source") else "no",
                                           "yes" if dScore.get("usesKit") else "no",
                                           "yes" if dScore.get("built") else "no",
                                           dScore.get("uiPassed", 0), dScore.get("uiFailed", 0),
                                           ", ".join("%s %s" % (k, v) for k, v in sorted(dScore.get("check", {}).items())) or "none"))
    lsLines += ["", "## What these numbers cannot show", "",
                "- **Chance.** A few runs of each condition can differ by luck. Run more before drawing a firm conclusion, and compare reports over time rather than trusting one.",
                "- **Fairness of the measures.** The uiCheck steps test only what the task asked for, so they are neutral. Check's encoding, logging and naming findings partly measure Homer conventions, which the homer runs were told to follow; they are listed apart for that reason.",
                "- **What a screen reader says.** Every result here is automated. Open the best and worst program of each condition with JAWS or NVDA before you quote these numbers.",
                "- **Other skills.** Claude Code also reads skills and notes from your user folder, the same in both conditions. The log lists what was there.",
                ""]
    open(sPath, "w", encoding="utf-8-sig", newline="\r\n").write("\n".join(lsLines))
    return sPath


def main():
    global oLog
    oParser = argparse.ArgumentParser(description="Measure whether the Homer skills improve an AI's program.")
    oParser.add_argument("--dry-run", action="store_true", help="prepare the run folders and stop")
    oParser.add_argument("--model", default="", help="the model Claude Code should use")
    oParser.add_argument("--runs", type=int, default=c_iRuns, help="runs of each condition")
    dArguments = oParser.parse_args()

    sKit = findKit()
    if not sKit:
        print("The HomerDev kit was not found, so nothing was run.")
        return 1
    os.makedirs(os.path.join(sKit, "logs"), exist_ok=True)
    sLogPath = os.path.join(sKit, "logs", "HomerDev-evalSkills-%s.log" % sStamp)
    oLog = open(sLogPath, "w", encoding="utf-8-sig", newline="\r\n")
    logLine("evalSkills start pid=%d" % os.getpid())
    logLine("env script=\"%s\" python=%s windows=\"%s\" workingDirectory=\"%s\"" % (
        os.path.abspath(__file__), platform.python_version(), platform.platform(), os.getcwd()))
    logLine("arguments %s" % " ".join(sys.argv[1:]))
    logLine("settings kit=\"%s\" runs=%d model=\"%s\" dryRun=%s maxTurns=%d timeoutSeconds=%d" % (
        sKit, dArguments.runs, dArguments.model, dArguments.dry_run, c_iMaxTurns, c_iTimeoutSeconds))
    sUserSkills = os.path.join(os.path.expanduser("~"), ".claude", "skills")
    logLine("user skills present in both conditions: %s" % (", ".join(sorted(os.listdir(sUserSkills))) if os.path.isdir(sUserSkills) else "none"))

    if not sys.platform.startswith("win"):
        sayLine("evalSkills builds and drives Windows programs, so it runs only on Windows.")
        return 1
    sClaude = shutil.which("claude")
    if not sClaude and not dArguments.dry_run:
        sayLine("Claude Code was not found on the PATH. Install it, sign in, and run evalSkills again.")
        return 1
    logLine("setting claude=\"%s\"" % (sClaude or "not found"))

    sBase = tempfile.mkdtemp(prefix="HomerDevEval-%s-" % sStamp)
    sayLine("Run folders: %s" % sBase)
    dRuns = {"plain": [], "homer": []}
    for iRun in range(1, dArguments.runs + 1):
        for sCondition in ("plain", "homer"):
            sFolder = prepareRun(sKit, sBase, sCondition, iRun)
            dRun = {"run": iRun, "folder": sFolder}
            if not dArguments.dry_run:
                sayLine("Asking for run %d, %s." % (iRun, sCondition))
                dRun["claude"] = askClaude(sClaude, sKit, sFolder, sCondition, dArguments.model)
                sayLine("Scoring run %d, %s." % (iRun, sCondition))
                dRun["score"] = scoreRun(sKit, sFolder)
            dRuns[sCondition].append(dRun)

    sReport = writeReport(sKit, sBase, dRuns, dArguments.model, dArguments.dry_run)
    sayLine("The report is %s" % sReport)
    sayLine("The log is %s" % sLogPath)
    logLine("evalSkills end")
    return 0


if __name__ == "__main__":
    iCode = 1
    try:
        iCode = main()
    except Exception:
        import traceback
        logLine("ERROR exception\n" + traceback.format_exc(), "ERROR")
        print("Something unexpected stopped evalSkills. The log has it.")
    finally:
        if oLog is not None: oLog.close()
    sys.exit(iCode)
