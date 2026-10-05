#!/usr/bin/env python3
"""build.py -- the build step for the Homer Development Kit.

The kit has no executable of its own, so "building" it means two things:

  1. Convert every .md in the kit to a matching .htm with pandoc, because a
     Homer project ships both forms of every document. When pandoc is missing,
     this script fetches it with winget and tries again.
  2. Check the kit over: every component present, every text file in the Homer
     encoding, every template still carrying its _APP_ token, and no zero-byte
     file anywhere. Anything wrong is reported plainly and fails the build.

Usage (through build.cmd, which is how it is meant to be run):

    build                      convert the documents and check the kit
    build check                check only, convert nothing

A detailed log is written to logs\\HomerDev-build-yyyyMMdd-HHmmss.log,
one file per run, so the log of a run that went wrong is never overwritten
by the run that followed it.
"""

import datetime
import os
import platform
import re
import subprocess
import sys
import time
import traceback

c_lsExpected = [
    "exec/CSharp/Elevate.cs", "exec/CSharp/Inix.cs", "exec/CSharp/KeyName.cs", "exec/CSharp/KeyMap.cs", "exec/CSharp/Lbc.cs",
    "exec/CSharp/Log.cs", "exec/CSharp/Mdi.cs", "exec/CSharp/Media.cs", "exec/CSharp/MediaPlayer.cs", "exec/CSharp/Mpv.cs", "exec/CSharp/Paths.cs",
    "exec/CSharp/PdfRead.cs", "exec/CSharp/Say.cs", "exec/CSharp/Util.cs", "exec/CSharp/Web.cs",
    "exec/CSharp/inixVert.cs",
    "exec/Python/inix.py", "exec/Python/lbc.py", "exec/Python/lbcnet.py", "exec/Python/log.py",
    "exec/Python/mdi.py", "exec/Python/elevate.py", "exec/Python/paths.py", "exec/Python/say.py", "exec/Python/util.py", "exec/Python/web.py",
    "Templates/build_APP_.cmd", "Templates/build_APP_Py.cmd",
    "Templates/_APP__setup.iss", "Templates/_APP_.cs",
    "Templates/installModels.cmd",
    "scripts/installOllama.cmd", "scripts/installScreenReaderSupport.cmd", "scripts/finish.cmd",
    "Templates/HomerComponents.iss", "scripts/installCommon.cmd",
    "Templates/create_APP_Repo.cmd", "Templates/create_APP_Repo.ps1",
    "Templates/accept.inix", "Templates/gitignore.txt", "Templates/version.txt",
    "scripts/release.cmd", "scripts/release.ps1", "RepoFiles.txt", "LocalFiles.txt",
    "Templates/samples/FruitBasketCs.cs", "Templates/samples/FruitBasketMdiCs.cs",
    "Templates/samples/FruitBasketMdiPy.py", "Templates/samples/FruitBasketPy.py",
    "Templates/samples/accept.inix", "Templates/samples/uiTest.inix",
    "Templates/samples/buildFruitBasketCs.cmd", "Templates/samples/buildFruitBasketMdiCs.cmd",
    "Templates/samples/buildFruitBasketMdiPy.cmd", "Templates/samples/buildFruitBasketPy.cmd", "Templates/samples/version.txt",
    "checkHomerDev.cmd", "checkHomerDev.py", "releaseHomerDev.cmd",
    "scripts/evalSkills.cmd", "scripts/evalSkills.py", "scripts/kind.cmd", "scripts/kind.py", "scripts/post.cmd", "scripts/post.ps1", "scripts/push.cmd", "scripts/unpushed.cmd", "scripts/unpushed.py",
    "scripts/check.cmd", "scripts/check.py", "scripts/uiCheck.cmd", "scripts/uiCheck.py",
    "scripts/tidy.cmd", "scripts/tidy.py",
    "scripts/buildTutorials.cmd", "scripts/buildTutorials.ps1", "scripts/checkTutorial.cmd", "scripts/checkTutorial.py",
    "scripts/fixEncoding.cmd", "scripts/fixEncoding.py",
    "scripts/makeTutorials.cmd", "scripts/makeTutorials.py",
    "Templates/Tutorial_00_Overview_and_Table_of_Contents.inix", "Templates/Tutorial_01_Install_and_Launch.inix", "Templates/Tutorial_02_User_Interface_Concepts.inix", "Templates/Tutorial_03_Key_Patterns.inix", "Templates/Tutorial_04_Task_One.inix", "Templates/Tutorial_05_Task_Two.inix", "Templates/Tutorial_06_Task_Three.inix", "Templates/Tutorial_07_Task_Four.inix", "Templates/Tutorial_08_Task_Five.inix", "Templates/Tutorial_09_Glossary.inix", "Templates/Tutorial_10_Conclusion.inix", "Templates/Tutorial_11_More_Information.inix",
    ".claude/skills/ReadMe.md", ".claude/skills/app-help-guide/SKILL.md", ".claude/skills/blind-creators/SKILL.md",
    ".claude/skills/homer-build-release/SKILL.md", ".claude/skills/homer-code/SKILL.md",
    ".claude/skills/homer-convert/SKILL.md", ".claude/skills/homer-docs/SKILL.md", ".claude/skills/homer-ui/SKILL.md",
    ".claude/skills/homer-elevate/SKILL.md", ".claude/skills/homer-installer/SKILL.md", ".claude/skills/homer-migrate/SKILL.md", ".claude/skills/homer-new-app/SKILL.md",
    ".claude/skills/homer-db/SKILL.md", ".claude/skills/homer-page/SKILL.md", ".claude/skills/homer-page/templates/_layouts/default.html",
    ".claude/skills/homer-page/templates/assets/css/style.scss", ".claude/skills/homer-screen-reader/SKILL.md",
    ".claude/skills/homer-installer/references/components.md",
    ".claude/skills/homer-tutorial/SKILL.md", ".claude/skills/podcast-directory/SKILL.md",
    "Templates/makeHotkeys.py",
    "Templates/LocalFiles.txt",
    "Templates/_APP_.cmd",
    "help/CamelType_CSharp.md", "help/CamelType_CSharp_Reference.md",
    "help/CamelType_JAWSScript.md", "help/CamelType_Python.md",
    "ReadMe.md", "License.md",
    "help/Announce.md", "help/Developer.md", "help/History.md", "help/HomerDev.md",
    "help/FAQ.md", "help/FinishPage.md", "help/HomerDev_update.md", "help/Hotkeys.md", "help/Logging.md", "help/TutorialLearnings.md", "help/Tutorials.md",
    "help/Tutorial_HomerDev.inix",
    "License.md", "version.txt",
]

c_sLogName = "HomerDev-build-%s.log" % datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

# Folders a build makes, which are none of the kit's business. Walking into one
# means auditing thousands of somebody else's files: a virtual environment alone
# holds the whole of PyInstaller. Lowercase alphabetical, as every list in Homer
# code is.
c_lsSkipFolders = [".git", ".venv", "__pycache__", "build", "dist", "exec", "notes", "venv"]

# How many problems to print before saying how many more there are. The log
# always holds every one of them.
c_iShowProblems = 20

# Files a build writes. They are generated on every build, they are in the
# never-pushed list, and auditing their encoding says nothing about the kit.
c_lsGeneratedFiles = ["version.py", "version.cs"]

# Reports a check writes; they are dated, disposable and not part of the kit.
c_sEvidencePrefix = "evidence-"

# The standard document set. ReadMe and License sit at the top of the project;
# every other document lives in help, which is where the Homer layout puts them.
c_lsDocumentsTop = ["License", "ReadMe"]

# The samples, and the script that builds each. One command builds everything,
# so a problem anywhere is found by running one thing rather than four.
c_lsSampleScripts = [
    "buildFruitBasketCs.cmd",
    "buildFruitBasketMdiCs.cmd",
    "buildFruitBasketMdiPy.cmd",
    "buildFruitBasketPy.cmd",
]

# WHERE FILES USED TO BE, AND WHERE THEY ARE NOW.
#
# A zip unarchived over an existing folder adds and replaces; it never deletes.
# So when the kit moves a file, the old copy stays on every machine that had the
# earlier version, and the result is two HomerDev.md files with different
# contents -- which is worse than either.
#
# Telling somebody to delete the old ones by hand is not an answer. A script
# that makes the change is, and this is it: for each pair below, when BOTH the
# old and the new file exist, the old one is removed. Both must exist, so
# nothing is ever deleted without its replacement already in place.
#
# Add a pair here whenever a file moves. Old entries can be dropped once nobody
# could still be carrying that version.
c_lMoved = [
    # PYTHON IS NAMED FOR ITS PLATFORM, AS C# IS (1.43.22): exec\\Python beside
    # exec\\CSharp, its modules imported by their own names ("import log"), not
    # through a homer package.
    ("exec/homer/__pycache__", "exec/Python/__pycache__"),
    ("exec/homer/elevate.py", "exec/Python/elevate.py"),
    ("exec/homer/inix.py", "exec/Python/inix.py"),
    ("exec/homer/lbc.py", "exec/Python/lbc.py"),
    ("exec/homer/lbcnet.py", "exec/Python/lbcnet.py"),
    ("exec/homer/log.py", "exec/Python/log.py"),
    ("exec/homer/mdi.py", "exec/Python/mdi.py"),
    ("exec/homer/paths.py", "exec/Python/paths.py"),
    ("exec/homer/say.py", "exec/Python/say.py"),
    ("exec/homer/util.py", "exec/Python/util.py"),
    ("exec/homer/web.py", "exec/Python/web.py"),
    # THE LIBRARIES ARE CODE THAT RUNS, SO THEY LIVE IN exec (1.43.22): the C#
    # classes in exec\\CSharp and the Python package in exec\\homer, beside the
    # Homer.dll compiled from them. At the top, homer shared its first letter
    # with help. And the skills moved from a skills folder, which shared its
    # first letter with scripts, to .claude\\skills, where Claude Code looks.
    ("CSharp/Elevate.cs", "exec/CSharp/Elevate.cs"),
    ("CSharp/Inix.cs", "exec/CSharp/Inix.cs"),
    ("CSharp/KeyMap.cs", "exec/CSharp/KeyMap.cs"),
    ("CSharp/KeyName.cs", "exec/CSharp/KeyName.cs"),
    ("CSharp/Lbc.cs", "exec/CSharp/Lbc.cs"),
    ("CSharp/Log.cs", "exec/CSharp/Log.cs"),
    ("CSharp/Mdi.cs", "exec/CSharp/Mdi.cs"),
    ("CSharp/Media.cs", "exec/CSharp/Media.cs"),
    ("CSharp/MediaPlayer.cs", "exec/CSharp/MediaPlayer.cs"),
    ("CSharp/Mpv.cs", "exec/CSharp/Mpv.cs"),
    ("CSharp/Ollama.cs", "exec/CSharp/Ollama.cs"),
    ("CSharp/Paths.cs", "exec/CSharp/Paths.cs"),
    ("CSharp/PdfRead.cs", "exec/CSharp/PdfRead.cs"),
    ("CSharp/Say.cs", "exec/CSharp/Say.cs"),
    ("CSharp/Util.cs", "exec/CSharp/Util.cs"),
    ("CSharp/Web.cs", "exec/CSharp/Web.cs"),
    ("CSharp/inixVert.cs", "exec/CSharp/inixVert.cs"),
    ("homer/__init__.py", "exec/Python/__init__.py"),
    ("homer/elevate.py", "exec/Python/elevate.py"),
    ("homer/inix.py", "exec/Python/inix.py"),
    ("homer/lbc.py", "exec/Python/lbc.py"),
    ("homer/lbcnet.py", "exec/Python/lbcnet.py"),
    ("homer/log.py", "exec/Python/log.py"),
    ("homer/mdi.py", "exec/Python/mdi.py"),
    ("homer/paths.py", "exec/Python/paths.py"),
    ("homer/say.py", "exec/Python/say.py"),
    ("homer/util.py", "exec/Python/util.py"),
    ("homer/web.py", "exec/Python/web.py"),
    ("skills/ReadMe.htm", ".claude/skills/ReadMe.htm"),
    ("skills/ReadMe.md", ".claude/skills/ReadMe.md"),
    ("skills/app-help-guide/SKILL.md", ".claude/skills/app-help-guide/SKILL.md"),
    ("skills/app-help-guide/references/fence-faults.md", ".claude/skills/app-help-guide/references/fence-faults.md"),
    ("skills/app-help-guide/references/guide-format.md", ".claude/skills/app-help-guide/references/guide-format.md"),
    ("skills/app-help-guide/references/refusal-rules.md", ".claude/skills/app-help-guide/references/refusal-rules.md"),
    ("skills/app-help-guide/scripts/buildGuide.cmd", ".claude/skills/app-help-guide/scripts/buildGuide.cmd"),
    ("skills/app-help-guide/scripts/buildGuide.py", ".claude/skills/app-help-guide/scripts/buildGuide.py"),
    ("skills/app-help-guide/scripts/cleanFeedback.cmd", ".claude/skills/app-help-guide/scripts/cleanFeedback.cmd"),
    ("skills/app-help-guide/scripts/cleanFeedback.py", ".claude/skills/app-help-guide/scripts/cleanFeedback.py"),
    ("skills/app-help-guide/scripts/makeHarvester.cmd", ".claude/skills/app-help-guide/scripts/makeHarvester.cmd"),
    ("skills/app-help-guide/scripts/makeHarvester.py", ".claude/skills/app-help-guide/scripts/makeHarvester.py"),
    ("skills/blind-creators/SKILL.md", ".claude/skills/blind-creators/SKILL.md"),
    ("skills/blind-creators/references/entry-formats.md", ".claude/skills/blind-creators/references/entry-formats.md"),
    ("skills/blind-creators/references/inclusion-rules.md", ".claude/skills/blind-creators/references/inclusion-rules.md"),
    ("skills/blind-creators/scripts/buildCreators.cmd", ".claude/skills/blind-creators/scripts/buildCreators.cmd"),
    ("skills/blind-creators/scripts/buildCreators.py", ".claude/skills/blind-creators/scripts/buildCreators.py"),
    ("skills/blind-creators/scripts/checkDirectory.cmd", ".claude/skills/blind-creators/scripts/checkDirectory.cmd"),
    ("skills/blind-creators/scripts/checkDirectory.py", ".claude/skills/blind-creators/scripts/checkDirectory.py"),
    ("skills/homer-tutorial/SKILL.md", ".claude/skills/homer-tutorial/SKILL.md"),
    ("skills/podcast-directory/SKILL.md", ".claude/skills/podcast-directory/SKILL.md"),
    ("skills/podcast-directory/scripts/buildDirectory.cmd", ".claude/skills/podcast-directory/scripts/buildDirectory.cmd"),
    ("skills/podcast-directory/scripts/buildDirectory.py", ".claude/skills/podcast-directory/scripts/buildDirectory.py"),
    ("skills/podcast-directory/scripts/harvestShows.cmd", ".claude/skills/podcast-directory/scripts/harvestShows.cmd"),
    ("skills/podcast-directory/scripts/harvestShows.py", ".claude/skills/podcast-directory/scripts/harvestShows.py"),
    ("Templates/skills/homer-tutorial/SKILL.md", ".claude/skills/homer-tutorial/SKILL.md"),
    ("Announce.md", "help/Announce.md"),
    ("Announce.htm", "help/Announce.htm"),
    ("Developer.md", "help/Developer.md"),
    ("Developer.htm", "help/Developer.htm"),
    ("History.md", "help/History.md"),
    ("History.htm", "help/History.htm"),
    ("HomerDev.md", "help/HomerDev.md"),
    ("HomerDev.htm", "help/HomerDev.htm"),
    ("Hotkeys.md", "help/Hotkeys.md"),
    ("Hotkeys.htm", "help/Hotkeys.htm"),
    ("Style/CamelType_CSharp.md", "help/CamelType_CSharp.md"),
    ("Style/CamelType_CSharp.htm", "help/CamelType_CSharp.htm"),
    ("Style/CamelType_CSharp_Reference.md", "help/CamelType_CSharp_Reference.md"),
    ("Style/CamelType_CSharp_Reference.htm", "help/CamelType_CSharp_Reference.htm"),
    ("Style/CamelType_JAWSScript.md", "help/CamelType_JAWSScript.md"),
    ("Style/CamelType_JAWSScript.htm", "help/CamelType_JAWSScript.htm"),
    ("Tutorial_HomerDev.inix", "help/Tutorial_HomerDev.inix"),
    ("Samples/FruitBasketMdi.cs", "Templates/samples/FruitBasketMdiCs.cs"),
    ("Samples/FruitBasketMdi.exe", "Templates/samples/FruitBasketMdiCs.exe"),
    ("Samples/buildFruitBasketMdi.log", "Templates/samples/buildFruitBasketMdiCs.log"),
    ("Samples/buildFruitBasketMdi.cmd", "Samples/buildFruitBasketMdiCs.cmd"),
    ("Tutorials.md", "help/Tutorials.md"),
    ("Tutorials.htm", "help/Tutorials.htm"),
    ("self.md", "help/self.md"),
    ("self.htm", "help/self.htm"),
    ("Samples/FruitBasketCs/FruitBasketCs.cs", "Templates/samples/FruitBasketCs.cs"),
    ("Samples/FruitBasketMdi/FruitBasketMdi.cs", "Templates/samples/FruitBasketMdi.cs"),
    ("Samples/FruitBasketPy/FruitBasketPy.py", "Templates/samples/FruitBasketPy.py"),
    ("Python/homer/inix.py", "exec/Python/inix.py"),
    ("Python/homer/lbc.py", "exec/Python/lbc.py"),
    ("Python/homer/say.py", "exec/Python/say.py"),
    ("Python/homer/util.py", "exec/Python/util.py"),
    ("Python/homer/web.py", "exec/Python/web.py"),
    # 1.43.0: the last two files of the old Python folder. __init__.py was
    # already at homer\; version.py is retired below, its work now in
    # homer\elevate.py.
    ("Python/homer/__init__.py", "exec/Python/__init__.py"),
    # 1.43.0: the per-sample folders of the old Samples layout, which the
    # 1.37.0 pairs did not reach, so Samples never emptied.
    ("Samples/FruitBasketCs/buildFruitBasketCs.cmd", "Templates/samples/buildFruitBasketCs.cmd"),
    ("Samples/FruitBasketCs/version.txt", "Templates/samples/version.txt"),
    ("Samples/FruitBasketPy/buildFruitBasketPy.cmd", "Templates/samples/buildFruitBasketPy.cmd"),
    ("Samples/FruitBasketPy/version.txt", "Templates/samples/version.txt"),
    ("exec/CSharp/Keys.cs", "exec/CSharp/KeyName.cs"),
    # 1.29.0: four files delivered on 24 Sep 2026 under folders the kit never
    # had (Docs, Inno, Scripts) now sit where RepoFiles.txt says kit files go.
    ("Docs/FinishPage.md", "help/FinishPage.md"),
    ("Docs/FinishPage.htm", "help/FinishPage.htm"),
    ("Docs/Logging.md", "help/Logging.md"),
    ("Docs/Logging.htm", "help/Logging.htm"),
    ("Inno/HomerComponents.iss", "Templates/HomerComponents.iss"),
    ("buildHomerDev.log", "build.py"),
    # 1.43.58: the kit's build script is build.cmd, as every app's is; the old
    # pair, left behind when the kit is unzipped over it, is removed.
    ("buildHomerDev.cmd", "build.cmd"),
    ("buildHomerDev.py", "build.py"),
    ("Samples/buildFruitBasketCs.log", "Templates/samples/buildFruitBasketCs.cmd"),
    ("Samples/buildFruitBasketMdiCs.log", "Templates/samples/buildFruitBasketMdiCs.cmd"),
    ("Samples/buildFruitBasketMdiPy.log", "Templates/samples/buildFruitBasketMdiPy.cmd"),
    ("Samples/buildFruitBasketPy.log", "Templates/samples/buildFruitBasketPy.cmd"),
    # 1.37.0: Samples shared its first letter with scripts, so the sample programs
    # live under Templates, the folder for what an app starts from.
    ("Samples/FruitBasketCs.cs", "Templates/samples/FruitBasketCs.cs"),
    ("Samples/FruitBasketMdiCs.cs", "Templates/samples/FruitBasketMdiCs.cs"),
    ("Samples/FruitBasketMdiPy.py", "Templates/samples/FruitBasketMdiPy.py"),
    ("Samples/FruitBasketMdiPy.spec", "Templates/samples/FruitBasketMdiPy.spec"),
    ("Samples/FruitBasketPy.py", "Templates/samples/FruitBasketPy.py"),
    ("Samples/FruitBasketPy.spec", "Templates/samples/FruitBasketPy.spec"),
    ("Samples/accept.inix", "Templates/samples/accept.inix"),
    ("Samples/buildFruitBasketCs.cmd", "Templates/samples/buildFruitBasketCs.cmd"),
    ("Samples/buildFruitBasketMdiCs.cmd", "Templates/samples/buildFruitBasketMdiCs.cmd"),
    ("Samples/buildFruitBasketMdiPy.cmd", "Templates/samples/buildFruitBasketMdiPy.cmd"),
    ("Samples/buildFruitBasketPy.cmd", "Templates/samples/buildFruitBasketPy.cmd"),
    ("Samples/uiTest.inix", "Templates/samples/uiTest.inix"),
    ("Samples/version.txt", "Templates/samples/version.txt"),
    # 1.37.0: the shared install scripts are scripts, refreshed into every app,
    # not starters; only installModels.cmd stays a template, naming an app's models.
    ("Templates/installOllama.cmd", "scripts/installOllama.cmd"),
    ("Templates/homerInstall.cmd", "scripts/installCommon.cmd"),
    ("Templates/installScreenReaderSupport.cmd", "scripts/installScreenReaderSupport.cmd"),
    ("Templates/homerFinish.cmd", "scripts/finish.cmd"),
    # 1.34.0: the kit follows the layout it asks of every app. Tools is scripts.
    ("Tools/buildTutorials.cmd", "scripts/buildTutorials.cmd"),
    ("Tools/buildTutorials.ps1", "scripts/buildTutorials.ps1"),
    ("Tools/checkHomerApp.cmd", "scripts/check.cmd"),
    ("Tools/checkHomerApp.py", "scripts/check.py"),
    ("Tools/gitPush.cmd", "scripts/push.cmd"),
    ("Tools/homerTidy.cmd", "scripts/tidy.cmd"),
    ("Tools/homerTidy.py", "scripts/tidy.py"),
    ("Tools/makeTutorials.cmd", "scripts/makeTutorials.cmd"),
    ("Tools/makeTutorials.py", "scripts/makeTutorials.py"),
    ("Tools/tagRelease.cmd", "scripts/release.cmd"),
    ("Tools/tagRelease.ps1", "scripts/release.ps1"),
    ("Tools/uiCheck.cmd", "scripts/uiCheck.cmd"),
    ("Tools/uiCheck.py", "scripts/uiCheck.py"),
]

# SCRIPTS RETIRED (25 Sep 2026) because their names sounded like another's and
# the other does the job: cleanDir and tidyRepo (with homerPolicy, which only
# tidyRepo read) are homerTidy; gitRelease is tagRelease, which runs the
# checks itself; sayTutorial is buildTutorials; installTools copied tools into
# C:\bin, where they went stale, and every app refreshes its scripts from the
# kit on each build instead. A retired file is deleted when the build finds
# it, and the log says so. One tool per job.
c_lsRetired = [
    # 1.47.0: the gathered accessibility skills live in their own repository,
    # A11ySkills, linked from the kit's documents rather than copied into it.
    # 33 of the 175 are under the GNU Affero GPL, which a copy inside an MIT
    # kit could be mistaken for; one current copy, kept where its licenses are
    # stated skill by skill, is also simply easier to keep current.
    "help/A11ySkills.htm", "help/A11ySkills.md",
    "homer/__init__.py", "exec/homer/__init__.py",
    "Templates/skills/homer-tutorial/SKILL.htm", "skills/homer-tutorial/SKILL.htm", "skills/ReadMe.md", "skills/ReadMe.htm",
    "scripts/cleanDir.cmd", "scripts/cleanDir.py", "scripts/gitRelease.cmd", "scripts/homerPolicy.py",
    "scripts/installTools.cmd", "scripts/sayTutorial.cmd", "scripts/sayTutorial.py",
    "scripts/tidyRepo.cmd", "scripts/tidyRepo.py",
    # fixKit140 put back what kit 1.40.0 lost; every machine has long since
    # passed that version, so the repair has nothing left to repair.
    "scripts/fixKit140.cmd", "scripts/fixKit140.py",
    "Tools/cleanDir.cmd", "Tools/cleanDir.py", "Tools/gitRelease.cmd", "Tools/homerPolicy.py",
    "Tools/installTools.cmd", "Tools/sayTutorial.cmd", "Tools/sayTutorial.py",
    "Tools/tidyRepo.cmd", "Tools/tidyRepo.py",
    # 1.43.0: homer\version.py could never be pushed -- every Homer build writes
    # a version.py of its own, so .gitignore and the checks treat the name as
    # generated -- and the kit's check reported it missing on every build. Its
    # version comparison is now part of homer\elevate.py, as it is of Elevate.cs.
    "Python/homer/version.py", "exec/Python/version.py",
]

# Folders that existed in an earlier layout and hold nothing the kit wants now.
# Removed only when empty, which they are once the pairs above have been applied.
c_lsOldFolders = ["skills/app-help-guide/references", "skills/app-help-guide/scripts", "skills/app-help-guide",
                  "skills/blind-creators/references", "skills/blind-creators/scripts", "skills/blind-creators",
                  "skills/homer-tutorial", "skills/podcast-directory/scripts", "skills/podcast-directory", "skills",
                  "Templates/skills/homer-tutorial", "Templates/skills", "CSharp", "exec/homer", "homer", "Docs", "Inno", "Python/homer", "Python", "Samples/FruitBasketCs", "Samples/FruitBasketPy",
                  "Templates/samples/FruitBasketCs",
                  "Templates/samples/FruitBasketMdi", "Templates/samples/FruitBasketPy", "Samples", "Style", "Tools"]
sScriptDir = os.path.dirname(os.path.abspath(__file__))
sLogPath = os.path.join(sScriptDir, "logs", c_sLogName)
oLog = None


def logLine(sText):
    """One event in the Homer log format (1.43.21), as log.py and Log.cs write:
    an ISO 8601 time with milliseconds and UTC offset, a five-character level,
    then the text; a line continuing the one above starts "| ", and no line is
    blank or unstamped. The level is ERROR or WARN when the text says so."""
    if oLog is None: return True
    import datetime as _datetime
    sText = (sText or "").replace("\r\n", "\n").rstrip("\n")
    if not sText.strip(): return True
    import re as _re
    sLevel = ("ERROR" if _re.search(r"\b(ERROR|FAIL|FAILED)\b", sText)
              else "WARN" if _re.search(r"\bWARN(ING)?\b", sText) else "INFO")
    # A LEADING LEVEL WORD IS THE LEVEL (1.43.33): "WARN: x" is written
    # "WARN  x", not "WARN  WARN: x".
    oLead = _re.match(r"(ERROR|WARN|WARNING)\b:?\s*", sText)
    if oLead: sText = sText[oLead.end():] or sText
    sPrefix = "%s %-5s " % (_datetime.datetime.now().astimezone().isoformat(timespec="milliseconds"), sLevel)
    lsOut = []
    for iAt, sOne in enumerate(sText.split("\n")):
        if iAt and not sOne.strip(): continue
        lsOut.append(sPrefix + ("| " if iAt else "") + sOne.rstrip())
    oLog.write("\n".join(lsOut) + "\n")
    oLog.flush()
    return True

def logValue(sValue):
    """A value as the Homer log format writes it: bare when it can be, quoted
    when it holds a space, a quote or an equals sign."""
    import re as _re
    s = "" if sValue is None else str(sValue)
    if s and not _re.search(r'[\s"=]', s): return s
    s = s.replace('"', '\\"')
    if s.endswith("\\"): s += "\\"
    return '"' + s + '"'


def logFact(sKey, sValue):
    """One environment fact: env key=value."""
    return logLine("env %s=%s" % (sKey, logValue(sValue)))

def logWindows():
    """The Windows actually running, worded as Log.cs and log.py word it:
    "Windows 11 25H2 (10.0.26200.9550)"."""
    try:
        import winreg as _winreg
        with _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as oKey:
            def read(sName):
                try: return str(_winreg.QueryValueEx(oKey, sName)[0])
                except OSError: return ""
            sBuild, sUbr, sDisplay = read("CurrentBuild"), read("UBR"), read("DisplayVersion")
        sName = "Windows 11" if sBuild.isdigit() and int(sBuild) >= 22000 else "Windows 10"
        return ("%s %s" % (sName, sDisplay)).strip() + " (10.0.%s%s)" % (sBuild, "." + sUbr if sUbr else "")
    except Exception:
        import platform as _platform
        return _platform.platform()




def sayLine(sText):
    print(sText)
    logLine("CONSOLE: " + sText)
    return True


def runCommand(lsArgs):
    """Run a command, log its exit code and output, return (iCode, sOutput)."""
    sCmd = " ".join(lsArgs)
    nStarted = time.time()
    logLine("run start cmd=" + logValue(sCmd))
    try:
        oResult = subprocess.run(lsArgs, capture_output=True, text=True)
    except Exception as oError:
        logLine("ERROR run failed message=%s cmd=%s" % (logValue(str(oError)), logValue(sCmd)))
        return (1, str(oError))
    logLine("run exit=%d ms=%d cmd=%s" % (oResult.returncode, (time.time() - nStarted) * 1000, logValue(sCmd)))
    if oResult.stdout: logLine("STDOUT:\n" + oResult.stdout.rstrip())
    if oResult.stderr: logLine("STDERR:\n" + oResult.stderr.rstrip())
    return (oResult.returncode, (oResult.stdout or "") + (oResult.stderr or ""))


def findPandoc():
    """The path to pandoc, fetching it with winget if it is not there yet."""
    iCode, sOut = runCommand(["pandoc", "--version"])
    if iCode == 0: return "pandoc"
    if os.name != "nt":
        logLine("No pandoc and no winget (not Windows), so no conversion.")
        return ""
    sayLine("Pandoc is not here yet. Fetching it.")
    runCommand(["winget", "install", "--id", "JohnMacFarlane.Pandoc",
                "--architecture", "x64", "--scope", "machine",
                "--accept-source-agreements", "--accept-package-agreements",
                "--silent"])
    iCode, sOut = runCommand(["pandoc", "--version"])
    if iCode == 0: return "pandoc"
    logLine("Pandoc is still not on the PATH after the install attempt.")
    return ""


def normalizeHomer(sPath):
    """Put a file into the Homer encoding: UTF-8 with a BOM and CRLF.

    Pandoc writes UTF-8 with no BOM and bare newlines, so its output is fixed
    here rather than left for the check to complain about.
    """
    try:
        sText = open(sPath, "rb").read().decode("utf-8-sig")
    except Exception as oError:
        logLine("NORMALIZE FAILED: %s: %s" % (sPath, oError))
        return False
    sText = sText.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
    bBom = not sPath.lower().endswith((".cmd", ".bat", "version.txt"))
    open(sPath, "wb").write((("\ufeff" + sText) if bBom else sText).encode("utf-8"))
    logLine("NORMALIZED: %s" % sPath)
    return True


def buildSamples():
    """Build every sample, and report each one.

    build is the single command. Somebody who changes a shared class
    should not have to remember four build scripts and the order to run them in,
    and a problem in any of them should surface from the one thing they already
    run. Each script writes its own log beside itself; the failures are named
    here and the detail is there.
    """
    sSamples = os.path.join(sScriptDir, "Templates", "samples")
    if not os.path.isdir(sSamples): return 0
    iFailed = 0
    for sScript in c_lsSampleScripts:
        if not os.path.isfile(os.path.join(sSamples, sScript)): continue
        sName = sScript[5:-4] if sScript.lower().startswith("build") else sScript
        logLine("RUN: %s in %s" % (sScript, sSamples))
        try:
            oResult = subprocess.run('"%s" nobump' % sScript, shell=True, cwd=sSamples,
                                     capture_output=True, text=True, timeout=1800)
            iCode = oResult.returncode
            if oResult.stdout: logLine("STDOUT:\n" + oResult.stdout[-3000:])
            if oResult.stderr: logLine("STDERR:\n" + oResult.stderr[-3000:])
        except Exception as oError:
            logLine("RUN FAILED: %s" % oError)
            iCode = 1
        logLine("EXIT: %d" % iCode)
        if iCode == 0:
            sayLine("Built %s." % sName)
        else:
            iFailed += 1
            sayLine("%s FAILED. Its own log, build%s.log, has the compiler output."
                    % (sName, sName))
    return iFailed


# THE KIT'S C# CLASSES AS ONE LIBRARY, FOR PYTHON (1.43.6). A Python app with
# a WinForms interface loads exec\Homer.dll through pythonnet (exec\Python\lbcnet.py)
# and builds its dialogs with the very LbcDialog the C# apps use, so a Python
# dialog gets the same focus order, keys, Help box and F11 by construction
# rather than by a second implementation kept in step by hand. The list is
# what LbcDialog needs, the set every C# app with a dialog compiles.
c_lsHomerDllClasses = ["Elevate", "Inix", "Lbc", "Log", "Paths", "Say", "Util", "Web"]


def findRoslyn():
    """The Roslyn csc.exe of any Visual Studio or Build Tools, via vswhere."""
    sVsWhere = os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
                            "Microsoft Visual Studio", "Installer", "vswhere.exe")
    if not os.path.isfile(sVsWhere):
        logLine("No vswhere.exe at %s" % sVsWhere)
        return ""
    iCode, sOut = runCommand([sVsWhere, "-latest", "-products", "*", "-find",
                              "MSBuild\\**\\Bin\\Roslyn\\csc.exe"])
    for sLine in sOut.splitlines():
        sLine = sLine.strip()
        if sLine.lower().endswith("csc.exe") and os.path.isfile(sLine): return sLine
    return ""


def findReference(sName):
    """A .NET Framework reference assembly by full path, as the C# template finds it."""
    sRefBase = os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
                            "Reference Assemblies", "Microsoft", "Framework", ".NETFramework")
    for sVersion in ("v4.8.1", "v4.8", "v4.7.2", "v4.7.1", "v4.7", "v4.6.2"):
        sPath = os.path.join(sRefBase, sVersion, sName)
        if os.path.isfile(sPath): return sPath
    sWindows = os.environ.get("SystemRoot", r"C:\Windows")
    for sPath in (os.path.join(sWindows, "Microsoft.NET", "assembly", "GAC_MSIL", "System.Speech",
                               "v4.0_4.0.0.0__31bf3856ad364e35", sName),
                  os.path.join(sWindows, "Microsoft.NET", "Framework64", "v4.0.30319", "WPF", sName)):
        if os.path.isfile(sPath): return sPath
    return ""


def buildHomerDll():
    """Compile exec\\Homer.dll from the kit's C# classes. Returns a problem or ""."""
    if os.name != "nt": return ""
    sCsc = findRoslyn()
    if sCsc == "":
        return ("exec\\Homer.dll was not built: no Roslyn C# compiler. The C# samples "
                "install the Build Tools; build them, then build again.")
    lsRefs = []
    for sName in ("System.Speech.dll", "UIAutomationProvider.dll", "UIAutomationTypes.dll"):
        sPath = findReference(sName)
        if sPath == "": return "exec\\Homer.dll was not built: %s was not found" % sName
        lsRefs.append("/reference:" + sPath)
    for sName in ("System.dll", "System.Core.dll", "System.Data.dll", "System.Drawing.dll",
                  "System.Windows.Forms.dll", "System.Web.dll", "System.Web.Extensions.dll",
                  "System.Net.Http.dll", "System.Xml.dll", "System.IO.Compression.dll",
                  "System.IO.Compression.FileSystem.dll", "Microsoft.VisualBasic.dll"):
        lsRefs.append("/reference:" + sName)
    sExec = os.path.join(sScriptDir, "exec")
    if not os.path.isdir(sExec): os.makedirs(sExec)
    sOut = os.path.join(sExec, "Homer.dll")
    lsSources = [os.path.join(sScriptDir, "exec", "CSharp", sClass + ".cs") for sClass in c_lsHomerDllClasses]
    for sSource in lsSources:
        if not os.path.isfile(sSource): return "exec\\Homer.dll was not built: %s is missing" % sSource
    iCode, sOutput = runCommand([sCsc, "/nologo", "/target:library", "/platform:x64", "/optimize+",
                                 "/out:" + sOut] + lsRefs + lsSources)
    if iCode != 0 or not os.path.isfile(sOut):
        return "exec\\Homer.dll did not compile; the log has the compiler's messages"
    sayLine("Built exec\\Homer.dll for Python apps (%s)." % ", ".join(c_lsHomerDllClasses))
    return ""


# THE KIT'S DOCUMENTS A SKILL CARRIES (1.43.24). A skill uploaded to claude.ai
# cannot read C:\\HomerDev, so it carries its own references; copying these from
# help at every build keeps one source of truth -- the kit's own documents --
# instead of hand copies that drift. The copies are named in LocalFiles.txt:
# git carries the originals, and a build makes the copies again.
c_dSkillDocuments = {
    "homer-installer": ["help/FinishPage.md"],
    "homer-screen-reader": ["help/CamelType_JAWSScript.md"],
    "homer-tutorial": ["help/Tutorials.md"],
    "homer-code": ["help/CamelType_CSharp.md", "help/CamelType_CSharp_Reference.md",
                   "help/CamelType_JAWSScript.md", "help/CamelType_Python.md", "help/Logging.md"],
}


# PARTS OF A KIT DOCUMENT A SKILL CARRIES (1.43.27). HomerDev.md is two
# thousand lines; a skill needs a few of its chapters. Each entry names the
# document, its chapters (## headings) to take, in the order given, and the
# reference file they make, which opens with a contents list, as Anthropic's
# guidance asks of any reference over a hundred lines.
c_lSkillSections = [
    ("homer-ui", "help/HomerDev.md",
     ["Lbc: building a dialog", "Keys and key names", "Direct speech across screen readers",
      "Three kinds of Homer app"],
     "ui-guide.md", "The Homer interface, from HomerDev.md"),
]


def extractSkillSections():
    """Write each skill's reference made of chapters of a kit document. Returns
    the number written."""
    import re
    iWritten = 0
    for sSkill, sDocument, lsChapters, sTarget, sTitle in c_lSkillSections:
        sSkillDir = os.path.join(sScriptDir, ".claude", "skills", sSkill)
        sSource = os.path.join(sScriptDir, sDocument.replace("/", os.sep))
        if not (os.path.isdir(sSkillDir) and os.path.isfile(sSource)):
            logLine("ERROR skill section source missing skill=%s document=%s" % (sSkill, sDocument))
            continue
        sText = open(sSource, "rb").read().decode("utf-8-sig").replace("\r\n", "\n")
        dChapters = {}
        # A chapter is an H2 (1.43.39): the kit's documents have one H1, their
        # title, as every Homer document does.
        for oMatch in re.finditer(r"(?ms)^## (.+?)\n(.*?)(?=^## |\Z)", sText):
            dChapters[oMatch.group(1).strip()] = oMatch.group(2)
        lsOut = ["# " + sTitle, "", "Copied by the kit's build from %s; edit that, not this." % sDocument, "",
                 "## Contents", ""]
        lsOut += ["- " + s for s in lsChapters if s in dChapters]
        lsOut.append("")
        for sChapter in lsChapters:
            if sChapter not in dChapters:
                logLine("ERROR skill section missing skill=%s chapter=%s" % (sSkill, logValue(sChapter)))
                continue
            # A chapter stays a ## section, its own headings as they are.
            sBody = dChapters[sChapter]
            lsOut += ["## " + sChapter, sBody.rstrip("\n"), ""]
        sPath = os.path.join(sSkillDir, "references", sTarget)
        os.makedirs(os.path.dirname(sPath), exist_ok=True)
        open(sPath, "wb").write(("\ufeff" + "\r\n".join("\n".join(lsOut).split("\n")) + "\r\n").encode("utf-8"))
        logLine("skill sections written skill=%s file=%s chapters=%d" % (sSkill, sTarget, len(lsChapters)))
        iWritten += 1
    return iWritten


def copySkillDocuments():
    """Copy each skill's kit documents into its references folder. Returns
    the number copied."""
    import shutil
    iCopied = 0
    for sSkill, lsDocuments in sorted(c_dSkillDocuments.items()):
        sReferences = os.path.join(sScriptDir, ".claude", "skills", sSkill, "references")
        if not os.path.isdir(os.path.dirname(sReferences)): continue
        os.makedirs(sReferences, exist_ok=True)
        for sDocument in lsDocuments:
            sSource = os.path.join(sScriptDir, sDocument.replace("/", os.sep))
            if not os.path.isfile(sSource):
                logLine("ERROR skill document missing skill=%s document=%s" % (sSkill, sDocument))
                continue
            shutil.copyfile(sSource, os.path.join(sReferences, os.path.basename(sSource)))
            logLine("skill document copied skill=%s document=%s" % (sSkill, sDocument))
            iCopied += 1
    return iCopied


def findStaleAppBuilds():
    """Name the apps beside the kit whose build script still looks for the
    kit's old layout (1.43.32).

    The kit's libraries moved into exec\\CSharp and exec\\Python on 28 September
    2026. An app's build script is its own copy, updated only when its newest
    <App>.zip is unzipped; until then it stops with "no kit found", and on 28
    September urlFido's did so twice after its new build script had been
    delivered. So the kit's build looks at each folder beside it for a
    build.cmd (or an older build<App>.cmd) that still names the old paths,
    and says which to unzip.
    Returns the names found."""
    import glob
    lsStale = []
    sParent = os.path.dirname(sScriptDir)
    for sBuild in sorted(glob.glob(os.path.join(sParent, "*", "build*.cmd")), key=str.lower):
        sFolder = os.path.basename(os.path.dirname(sBuild))
        if os.path.normcase(os.path.dirname(sBuild)) == os.path.normcase(sScriptDir): continue
        if os.path.basename(sBuild).lower() not in ("build.cmd", ("build" + sFolder + ".cmd").lower()): continue
        try:
            sText = open(sBuild, "rb").read().decode("utf-8", "replace")
        except Exception:
            continue
        # Any kit path not under exec: HomerView's looked for CSharp\\Inix.cs,
        # not Lbc.cs, and the first version of this test missed it.
        bOld = bool(re.search(r"(?<!exec)\\CSharp\\\w+\.cs", sText) or
                    re.search(r"(?<!exec)\\homer\\\w+\.py", sText))
        # ONLY A PROJECT UNDER GIT IS AN APP (1.43.35). On 28 September the scan
        # named C:\\Jobrise, a folder left from a name considered and rejected
        # for what became JobTrail -- not an app at all -- and it was reported
        # as one. A folder without .git is named as a possible leftover instead.
        if bOld and not os.path.isdir(os.path.join(os.path.dirname(sBuild), ".git")):
            logLine("WARN: folder with a stale build script is not a git repository, possibly a leftover folder=%s"
                    % logValue(os.path.dirname(sBuild)))
            sayLine("NOTE: %s holds a build script but is not a git repository, so it is not counted as an app. "
                    "If it is left over, delete it." % os.path.dirname(sBuild))
            continue
        if bOld:
            lsStale.append(sFolder)
            logLine("WARN: app build script looks for the old kit layout app=%s script=%s" % (sFolder, logValue(sBuild)))
    if lsStale:
        sayLine("WARNING: %s still look%s for the kit's old layout and will stop with \"no kit found\". "
                "Unzip each app's newest zip into its folder, or run updateAppBuilds here to update the paths."
                % (", ".join(lsStale), "s" if len(lsStale) == 1 else ""))
    return lsStale


def removeSkillHtm():
    """Delete the .htm copies earlier builds wrote beside skill files (1.43.30).
    Returns the number removed."""
    iRemoved = 0
    sSkills = os.path.join(sScriptDir, ".claude", "skills")
    if not os.path.isdir(sSkills): return 0
    for sName in os.listdir(sSkills):
        sFolder = os.path.join(sSkills, sName)
        if not os.path.isdir(sFolder): continue
        for sDir, lsDirs, lsFiles in os.walk(sFolder):
            for sFile in lsFiles:
                if not sFile.lower().endswith(".htm"): continue
                try:
                    os.remove(os.path.join(sDir, sFile))
                    logLine("removed generated skill htm file=%s" % logValue(os.path.join(sDir, sFile)))
                    iRemoved += 1
                except Exception as oError:
                    logLine("ERROR could not remove file=%s message=%s" % (logValue(os.path.join(sDir, sFile)), logValue(str(oError))))
    return iRemoved


def packSkills():
    """Pack each skill into exec\\skills\\<name>.zip, ready to upload.

    THE SKILLS LIVE IN .claude\\skills\\<name>\\ (1.43.22), where Claude Code
    finds a project's skills by itself when it works in C:\\HomerDev -- only
    there, one folder deep -- and where the folder name, starting with a dot,
    shares its first letter with no other folder at the top of the kit. Each is
    in the shape Claude reads: SKILL.md at the top, references\\ to read before
    acting, scripts\\ with a .cmd beside every script. claude.ai takes a skill
    as a zip holding that one folder, so the build makes one per skill.
    Returns the number packed."""
    import zipfile
    sSkills = os.path.join(sScriptDir, ".claude", "skills")
    sOut = os.path.join(sScriptDir, "exec", "skills")
    if not os.path.isdir(sSkills): return 0
    os.makedirs(sOut, exist_ok=True)
    iPacked = 0
    for sName in sorted(os.listdir(sSkills)):
        sFolder = os.path.join(sSkills, sName)
        if not os.path.isfile(os.path.join(sFolder, "SKILL.md")): continue
        sZip = os.path.join(sOut, sName + ".zip")
        with zipfile.ZipFile(sZip, "w", zipfile.ZIP_DEFLATED) as oZip:
            for sDir, lsDirs, lsFiles in os.walk(sFolder):
                lsDirs[:] = [s for s in lsDirs if s != "__pycache__"]
                for sFile in sorted(lsFiles):
                    if sFile.lower().endswith(".htm"): continue
                    sPath = os.path.join(sDir, sFile)
                    oZip.write(sPath, os.path.relpath(sPath, sSkills))
        logLine("skill packed name=%s zip=%s" % (sName, logValue(sZip)))
        iPacked += 1
    return iPacked


def removeStaleBinCopies():
    """Kit tools once copied into C:\\bin go stale there and run in place of an
    app's own; on 25 Sep 2026 a push and a release ran from such copies. Only
    files bearing a kit tool's name are touched, and each removal is logged."""
    sBin = "C:\\bin"
    if not os.path.isdir(sBin): return True
    lsNames = ["checkHomerApp.cmd", "checkHomerApp.py", "cleanDir.cmd", "cleanDir.py", "gitPush.cmd",
               "gitRelease.cmd", "gitUnpushed.cmd", "gitUnpushed.py", "homerPolicy.py", "homerTidy.cmd",
               "homerTidy.py", "installTools.cmd", "sayTutorial.cmd", "sayTutorial.py", "tagRelease.cmd",
               "tagRelease.ps1", "tidyRepo.cmd", "tidyRepo.py"]
    lsGone = []
    for sName in lsNames:
        sPath = os.path.join(sBin, sName)
        if not os.path.isfile(sPath): continue
        try:
            os.remove(sPath)
            lsGone.append(sName)
            logLine("REMOVED FROM C:\\bin: %s (every app carries its own copy in scripts)" % sName)
        except Exception as oError:
            logLine("COULD NOT REMOVE %s: %s" % (sPath, oError))
            sayLine("C:\\bin\\%s could not be removed: %s" % (sName, oError))
    if lsGone:
        sayLine("Removed from C:\\bin: " + ", ".join(lsGone) + ". Every app carries its own copy in scripts.")
    return True


def buildTutorials():
    """Fetch the shared voices and speak the kit's own tutorials.

    THE KIT'S BUILD IS THE ONE THING THAT DOWNLOADS THE VOICES (25 Sep 2026).
    They live in exec, shared by every Homer app's build, so this is where
    they are fetched -- once -- with -fetch, which an app's build never passes.
    Then any kit tutorial without audio is spoken. The tool logs to
    logs\\HomerDev-tutorials-<stamp>.log; only the outcome is repeated here.
    """
    sTool = os.path.join(sScriptDir, "scripts", "buildTutorials.cmd")
    if not os.path.isfile(sTool):
        logLine("no scripts/buildTutorials.cmd; voices not fetched")
        return False
    # THE TOOL'S OWN LINES REACH THE SCREEN. It names each tutorial as it
    # starts and finishes, and the minutes between are speaking, not a
    # download; capturing them left seven silent minutes on 25 Sep 2026. It
    # keeps its own log in logs, so only the exit code is recorded here.
    sayLine("Fetching any voices not yet in exec, and speaking any tutorial without audio ...")
    logLine("RUN: %s -fetch -build (output on the console; its log is in logs)" % sTool)
    try:
        iCode = subprocess.call(["cmd.exe", "/c", sTool, "-fetch", "-build"])
    except Exception as oError:
        logLine("RUN FAILED: %s" % oError)
        iCode = 1
    logLine("EXIT: %d" % iCode)
    if iCode == 0:
        sayLine("Voices are in exec; tutorials are spoken.")
    else:
        sayLine("The voices or tutorials could not be completed; the tutorials log in logs says why.")
    return iCode == 0


# THE SCRIPTS WERE RENAMED ON 26 SEPTEMBER 2026, to names a person can type.
# The prefixes said nothing the folder did not: every script here is Homer's,
# and git is how push and release work, not what they are. So homerTidy is
# tidy, gitPush is push, tagRelease is release. homerInstall is installCommon
# rather than install, because it is called by other install scripts and never
# run, and a bare install.cmd in a scripts folder looks like something to run.
#
# RENAMED IN PLACE, NOT SHIPPED UNDER THE NEW NAME. The kit on a working
# machine can be newer than any archive of it -- on 26 September the machine
# was at 1.41.3 and the GitHub archive at 1.41.0 -- and tagRelease is not in
# git at all, by standing rule. Shipping renamed copies would have replaced the
# newer content with the older and then deleted the newer original. So each
# file is renamed where it lies, keeping whatever it holds, and the old names
# are rewritten in the kit's own text files. Both steps do nothing on a second
# run, so this can stay in the build indefinitely.
c_lRenamedScripts = [
    ("checkHomerApp.cmd", "check.cmd"), ("checkHomerApp.py", "check.py"),
    ("gitPush.cmd", "push.cmd"),
    ("gitUnpushed.cmd", "unpushed.cmd"), ("gitUnpushed.py", "unpushed.py"),
    ("homerFinish.cmd", "finish.cmd"),
    ("homerInstall.cmd", "installCommon.cmd"),
    ("homerTidy.cmd", "tidy.cmd"), ("homerTidy.py", "tidy.py"),
    ("tagRelease.cmd", "release.cmd"), ("tagRelease.ps1", "release.ps1"),
]

# The same renames as words, for rewriting references. A name is replaced only
# as a whole word, so tagRelease_README, which names a file of the separate
# tagRelease project, is left alone.
c_lRenamedWords = [
    ("checkHomerApp", "check"), ("gitUnpushed", "unpushed"), ("gitPush", "push"),
    ("homerFinish", "finish"), ("homerInstall", "installCommon"),
    ("homerTidy", "tidy"), ("tagRelease", "release"),
]

# Files whose old names are history, not instructions: a dated record says
# what was true that day, and the briefing names the old scripts on purpose so
# a reader can recognise them in an old log. This file is here too -- it holds
# the old names as data.
c_lsKeepOldNames = ["build.py", "History.md", "History.htm",
                    "HomerDev_update.md", "HomerDev_update.htm"]
c_sKeepOldPrefixes = ("Kit-Findings-", "Rulings-")

c_lsRewriteExtensions = (".bat", ".cmd", ".cs", ".htm", ".inix", ".iss", ".jss", ".md",
                         ".ps1", ".py", ".txt", ".gitignore")


def renameScripts():
    """Rename the kit's scripts in place and rewrite their old names.

    A file is renamed only when its new name is not already taken; when both
    exist, the new one is the kit's and the old one is removed. Text files are
    rewritten only where an old name appears, and keep their own byte order
    mark and line endings, so a file with nothing to change is not touched.
    """
    sScripts = os.path.join(sScriptDir, "scripts")
    iRenamed = iRemoved = iRewritten = 0
    for sOld, sNew in c_lRenamedScripts:
        sOldPath = os.path.join(sScripts, sOld)
        sNewPath = os.path.join(sScripts, sNew)
        if not os.path.isfile(sOldPath): continue
        try:
            if os.path.isfile(sNewPath):
                os.remove(sOldPath)
                iRemoved += 1
                logLine("RENAMED EARLIER: scripts/%s is scripts/%s; removed the old copy" % (sOld, sNew))
            else:
                os.rename(sOldPath, sNewPath)
                iRenamed += 1
                logLine("RENAMED: scripts/%s to scripts/%s, keeping its content" % (sOld, sNew))
        except Exception as oError:
            logLine("COULD NOT RENAME scripts/%s: %s" % (sOld, oError))

    # Reports check used to write beside itself. It writes them in logs now,
    # and the ones left here were committed by accident.
    if os.path.isdir(sScripts):
        for sName in os.listdir(sScripts):
            if sName.lower().startswith(c_sEvidencePrefix):
                try:
                    os.remove(os.path.join(sScripts, sName))
                    iRemoved += 1
                    logLine("REMOVED STRAY REPORT: scripts/%s" % sName)
                except Exception as oError:
                    logLine("COULD NOT REMOVE scripts/%s: %s" % (sName, oError))

    # A digit may come before a name: %~dp0homerTidy.cmd is how a script calls
    # its neighbour, and the 0 of %~dp0 kept every such call from being
    # rewritten until 1.43.8 -- tidy.cmd went on running homerTidy.py, push
    # skipped the whitelist, and check ran a file that was no longer there.
    lPatterns = [(re.compile(r"(?<![A-Za-z_])%s(?![A-Za-z0-9_])" % re.escape(sOld)), sNew)
                 for sOld, sNew in c_lRenamedWords]
    for sRoot, lsDirs, lsFiles in os.walk(sScriptDir):
        # NOT .claude (1.43.30): a skill that names the old script names does
        # so on purpose -- homer-build-release's failures.md lists them as what
        # an old build script calls -- and rewriting them there emptied the
        # sentence of its meaning.
        lsDirs[:] = [s for s in lsDirs if s.lower() not in c_lsSkipFolders and s.lower() not in ("logs", ".claude")]
        for sName in lsFiles:
            if sName in c_lsKeepOldNames or sName.startswith(c_sKeepOldPrefixes): continue
            if not sName.lower().endswith(c_lsRewriteExtensions) and sName != ".gitignore": continue
            sPath = os.path.join(sRoot, sName)
            try:
                yRaw = open(sPath, "rb").read()
            except Exception:
                continue
            bBom = yRaw.startswith(b"\xef\xbb\xbf")
            try:
                sText = yRaw[3:].decode("utf-8") if bBom else yRaw.decode("utf-8")
            except UnicodeDecodeError:
                continue
            # LINE BY LINE, SO THE RETIRED LIST KEEPS ITS OLD NAMES. That list
            # exists to name the old scripts, and rewriting it turned them into
            # the new names -- which an app would then delete. A second run
            # caught it: it should change nothing, and it changed that line.
            lsLines = sText.split("\n")
            for iLine, sLine in enumerate(lsLines):
                if "for %%F in (cleanDir.cmd" in sLine: continue
                # The Python template's retired list is a variable, not a loop
                # (1.43.1): rewritten by 1.43.0's first run, it named check,
                # push, tidy and release as retired, and an app built from it
                # would have deleted the tools it had just refreshed.
                if "retiredTools=" in sLine: continue
                for oPattern, sNew in lPatterns:
                    sLine = oPattern.sub(sNew, sLine)
                lsLines[iLine] = sLine
            sNewText = "\n".join(lsLines)
            if sNewText == sText: continue
            yOut = (b"\xef\xbb\xbf" if bBom else b"") + sNewText.encode("utf-8")
            try:
                open(sPath, "wb").write(yOut)
                iRewritten += 1
                logLine("REWROTE old script names in %s" % os.path.relpath(sPath, sScriptDir))
            except Exception as oError:
                logLine("COULD NOT REWRITE %s: %s" % (sPath, oError))

    # Apps delete what the template lists as retired, so the old names join
    # that list: an app that carried homerTidy loses it on its next build
    # instead of keeping a copy that no longer refreshes.
    sTemplate = os.path.join(sScriptDir, "Templates", "build_APP_.cmd")
    if os.path.isfile(sTemplate):
        yRaw = open(sTemplate, "rb").read()
        sText = yRaw.decode("utf-8", errors="replace")
        sLoop = "for %%F in (cleanDir.cmd "
        iAt = sText.find(sLoop)
        if iAt >= 0:
            iEnd = sText.find(")", iAt)
            sList = sText[iAt + len("for %%F in ("):iEnd]
            lsHave = sList.split()
            lsAdd = [sOld for sOld, sNew in c_lRenamedScripts if sOld not in lsHave]
            if lsAdd:
                sText = sText[:iAt] + "for %%F in (" + " ".join(lsHave + lsAdd) + sText[iEnd:]
                open(sTemplate, "wb").write(sText.encode("utf-8"))
                logLine("ADDED to the template's retired list: %s" % " ".join(lsAdd))
        elif "retiredTools=" in sText:
            # 1.43.2: the C# template names its retired scripts in a
            # retiredTools= variable, as the Python one does, and already
            # lists every renamed name.
            pass
        else:
            logLine("NOTE: the template's retired-scripts loop was not found, so the old names were not added to it")

    # AND THE KIT'S HISTORY SAYS SO, ONCE. History.md is not shipped with this
    # change, because the copy on a working machine may be newer than the
    # archive; the entry is added in place, under the first heading, and a
    # second run finds it and adds nothing.
    sHistory = os.path.join(sScriptDir, "help", "History.md")
    sMarker = "# 1.42.0 -- 26 September 2026"
    if os.path.isfile(sHistory):
        yRaw = open(sHistory, "rb").read()
        bBom = yRaw.startswith(b"\xef\xbb\xbf")
        sText = (yRaw[3:] if bBom else yRaw).decode("utf-8", errors="replace")
        if sMarker not in sText:
            sEntry = (sMarker + "\r\n\r\n"
                "The scripts have shorter names: tidy (was homerTidy), push (gitPush),\r\n"
                "unpushed (gitUnpushed), release (tagRelease), check (checkHomerApp),\r\n"
                "finish (homerFinish) and installCommon (homerInstall). buildHomerDev\r\n"
                "renames them in place, keeping their content, rewrites the old names\r\n"
                "in the kit's files, and adds them to the template's retired list so each\r\n"
                "app's build removes its old copies. Each app's own build script names\r\n"
                "the new ones and needs kit 1.42.0. The renaming and retiring now run\r\n"
                "whether or not pandoc is present. help\\HomerDev_update.md now holds\r\n"
                "everything HomerView's migration taught, as rules.\r\n\r\n")
            iAt = sText.find("\n# ", sText.find("# History"))
            if iAt >= 0:
                sText = sText[:iAt + 1] + sEntry + sText[iAt + 1:]
                open(sHistory, "wb").write((b"\xef\xbb\xbf" if bBom else b"") + sText.encode("utf-8"))
                iRewritten += 1
                logLine("ADDED the 1.42.0 entry to help/History.md")

    if iRenamed or iRemoved or iRewritten:
        sayLine("Renamed %d script%s, removed %d old file%s, rewrote names in %d file%s." %
                (iRenamed, "" if iRenamed == 1 else "s", iRemoved, "" if iRemoved == 1 else "s",
                 iRewritten, "" if iRewritten == 1 else "s"))
    return iRenamed + iRemoved + iRewritten


# PATCHES MADE IN PLACE, for the same reason the renaming is: the kit's
# scripts on a working machine can be newer than any archive, and release.ps1
# is not in git at all. Each patch finds ONE exact line, inserts after or in
# place of it, and marks what it did, so a second run sees the mark and does
# nothing. A line not found is logged, never guessed at.
#
# QUIET PROBES (1.42.1). release asks git whether a tag exists and gh whether
# a release exists. The normal answer is "no", which both print to stderr, and
# Windows PowerShell 5.1 records that as a red NativeCommandError in the
# transcript even with 2>$null -- so a clean release showed two error blocks.
# Silencing the error stream around the probe keeps the exit code, which is
# what the script reads.
#
# ORIGIN FOLLOWS A MOVE (1.42.1). GitHub answered every push with "This
# repository moved. Please use the new location" -- the remote said
# JamalMazrui and the account is jamalmazrui. A redirect works until it does
# not. push now reads that message from its own log and points origin at the
# new location, once; after that GitHub has nothing to say.
# The 1.42.1 QUIET PROBE patch to release.ps1 is gone (1.43.14): release.ps1
# has asked its questions through System.Diagnostics.Process since 1.43.8, so
# the line the patch looked for no longer exists, and every kit build logged
# that it could not apply it.
c_lPatches = [
    # AFTER THE FAILURE CHECK, NOT AFTER THE PUSH. The line after `git push`
    # is `if errorlevel 1`, and anything run between them resets errorlevel:
    # the first version of this patch sat there and would have reported every
    # failed push as a success. The anchor is the end of that check, in the
    # words the renaming has just written ("push finished").
    ("scripts/push.cmd", "ORIGIN FOLLOWS A MOVE (1.42.1)",
     ')\r\ngit status --short --branch\r\n>> "%log%" echo push finished',
     ')\r\n'
     'rem ORIGIN FOLLOWS A MOVE (1.42.1): when GitHub says the repository moved,\r\n'
     'rem point origin at the new location once, so it stops saying so. Placed\r\n'
     'rem after the push failure check, which must see git push\'s own errorlevel.\r\n'
     'powershell -NoProfile -Command "$l = @(Get-Content -LiteralPath \'%log%\'); for ($i = 0; $i -lt $l.Count - 1; $i++) { if ($l[$i] -match \'This repository moved\') { $u = ($l[$i + 1] -replace \'^remote:\\s*\', \'\').Trim(); if ($u -match \'^https://\') { git remote set-url origin $u; \'Origin now points at \' + $u }; break } }" >> "%log%" 2>&1\r\n'
     'git status --short --branch\r\n>> "%log%" echo push finished',
     "replace"),
]


def patchScripts():
    """Apply each patch once, in place, keeping everything else in the file."""
    iApplied = 0
    for sRelative, sMarker, sFind, sNew, sMode in c_lPatches:
        sPath = os.path.join(sScriptDir, sRelative.replace("/", os.sep))
        if not os.path.isfile(sPath): continue
        yRaw = open(sPath, "rb").read()
        bBom = yRaw.startswith(b"\xef\xbb\xbf")
        sText = (yRaw[3:] if bBom else yRaw).decode("utf-8", errors="replace")
        if sMarker in sText: continue
        sNewline = "\r\n" if "\r\n" in sText else "\n"
        sFindHere = sFind.replace("\r\n", sNewline)
        if sFindHere not in sText:
            logLine("NOTE: %s was not patched (%s); the line it expects is not there" % (sRelative, sMarker))
            continue
        sText = sText.replace(sFindHere, sNew.replace("\r\n", sNewline), 1)
        open(sPath, "wb").write((b"\xef\xbb\xbf" if bBom else b"") + sText.encode("utf-8"))
        iApplied += 1
        logLine("PATCHED %s: %s" % (sRelative, sMarker))
    # The 1.42.1 History entry, added once in place like the 1.42.0 one.
    sHistory = os.path.join(sScriptDir, "help", "History.md")
    sMarker = "# 1.42.1 -- 26 September 2026"
    if os.path.isfile(sHistory):
        yRaw = open(sHistory, "rb").read()
        bBom = yRaw.startswith(b"\xef\xbb\xbf")
        sText = (yRaw[3:] if bBom else yRaw).decode("utf-8", errors="replace")
        if sMarker not in sText:
            sEntry = (sMarker + "\r\n\r\n"
                "release no longer shows two red error blocks on a release that\r\n"
                "succeeded: asking git whether a tag exists, and gh whether a release\r\n"
                "exists, normally gets the answer no, and that answer is no longer\r\n"
                "recorded as an error. push now notices when GitHub says a repository\r\n"
                "has moved, and points origin at the new address once, so the notice\r\n"
                "stops. Both are patched into the scripts in place by buildHomerDev,\r\n"
                "keeping everything else in them.\r\n\r\n")
            iAt = sText.find("\n# ", sText.find("# History"))
            if iAt >= 0:
                sText = sText[:iAt + 1] + sEntry + sText[iAt + 1:]
                open(sHistory, "wb").write((b"\xef\xbb\xbf" if bBom else b"") + sText.encode("utf-8"))
                logLine("ADDED the 1.42.1 entry to help/History.md")
    if iApplied:
        sayLine("Patched %d script%s in place." % (iApplied, "" if iApplied == 1 else "s"))
    return iApplied


def removeMoved():
    """Delete a file the kit has moved, once its replacement is in place.

    Unarchiving over an existing folder never deletes, so without this a machine
    that had an earlier kit keeps both copies of every document that moved. Two
    files with the same name and different contents is worse than either alone,
    and working out which is which is not the user's job.

    Both the old and the new file must exist before anything is removed, so a
    file is never deleted without its replacement already in place.
    """
    iRemoved = 0
    for sOld, sNew in c_lMoved:
        sOldPath = os.path.join(sScriptDir, sOld.replace("/", os.sep))
        sNewPath = os.path.join(sScriptDir, sNew.replace("/", os.sep))
        # NEVER WHEN BOTH SIDES ARE THE SAME FILE. Windows does not tell
        # "Scripts" from "scripts": on 25 Sep 2026 a pair that had once moved
        # Scripts/homerInstall.cmd to Templates saw the newly delivered
        # scripts/homerInstall.cmd as the old copy and deleted it.
        if os.path.normcase(os.path.abspath(sOldPath)) == os.path.normcase(os.path.abspath(sNewPath)): continue
        if not (os.path.isfile(sOldPath) and os.path.isfile(sNewPath)): continue
        try:
            os.remove(sOldPath)
            iRemoved += 1
            logLine("MOVED: %s is now %s; removed the old copy" % (sOld, sNew))
        except Exception as oError:
            logLine("COULD NOT REMOVE %s: %s" % (sOldPath, oError))

    for sRetired in c_lsRetired:
        sPath = os.path.join(sScriptDir, sRetired.replace("/", os.sep))
        if not os.path.isfile(sPath): continue
        try:
            os.remove(sPath)
            iRemoved += 1
            logLine("RETIRED: %s removed; its job belongs to another script now" % sRetired)
        except Exception as oError:
            logLine("COULD NOT REMOVE %s: %s" % (sPath, oError))

    for sFolder in c_lsOldFolders:
        sPath = os.path.join(sScriptDir, sFolder.replace("/", os.sep))
        try:
            # A folder Python ran from keeps __pycache__, which would keep it
            # from ever being empty; its compiled copies go with it.
            sCache = os.path.join(sPath, "__pycache__")
            if os.path.isdir(sCache):
                import shutil
                shutil.rmtree(sCache, ignore_errors=True)
            if os.path.isdir(sPath) and not os.listdir(sPath):
                os.rmdir(sPath)
                iRemoved += 1
                logLine("REMOVED EMPTY FOLDER: %s" % sPath)
        except Exception as oError:
            logLine("COULD NOT REMOVE FOLDER %s: %s" % (sPath, oError))

    if iRemoved:
        sayLine("Removed %d file%s left by an earlier layout." %
                (iRemoved, "" if iRemoved == 1 else "s"))
    return iRemoved


def convertDocs(sPandoc):
    """Write a .htm beside every .md in the kit. Returns the number converted."""
    iDone = 0
    for sRoot, lsDirs, lsFiles in os.walk(sScriptDir):
        lsDirs[:] = [s for s in lsDirs if s.lower() not in c_lsSkipFolders]
        # Templates are not documents: a template is a starter for a new
        # app, and converting it would leave a stray .htm in the kit.
        if os.path.basename(sRoot).lower() == "templates": continue
        # A SKILL IS NOT A DOCUMENT SET (1.43.30). Its SKILL.md and references
        # are read by Claude as Markdown; an .htm beside each was noise in the
        # folder, in git and in every packed zip. Only the index,
        # .claude\\skills\\ReadMe.md, is a document a person reads.
        sRelRoot = os.path.relpath(sRoot, sScriptDir).replace(os.sep, "/").lower()
        bSkillsIndex = sRelRoot == ".claude/skills"
        if sRelRoot.startswith(".claude") and not bSkillsIndex: continue
        for sName in sorted(lsFiles):
            if not sName.lower().endswith(".md"): continue
            if bSkillsIndex and sName.lower() != "readme.md": continue
            sMd = os.path.join(sRoot, sName)
            sHtm = os.path.join(sRoot, sName[:-3] + ".htm")
            # Dollar signs are text, not mathematics (1.43.59): a skill quoting a
            # GitHub workflow's ${{ secrets }} or a price is not a formula.
            iCode, sOut = runCommand([sPandoc, "-f", "markdown-tex_math_dollars", "-t", "html5",
                                      "--standalone", "--metadata",
                                      "title=" + sName[:-3], "-o", sHtm, sMd])
            if iCode == 0:
                normalizeHomer(sHtm)
                iDone += 1
            else: sayLine("Pandoc could not convert %s." % sName)
    return iDone


def checkKit():
    """Report anything wrong with the kit. Returns a list of problems."""
    lsProblems = []

    for sRelative in c_lsExpected:
        sPath = os.path.join(sScriptDir, sRelative.replace("/", os.sep))
        if not os.path.exists(sPath):
            lsProblems.append("missing: " + sRelative)
            continue
        if os.path.getsize(sPath) == 0:
            lsProblems.append("empty: " + sRelative)

    # Encoding: every text file UTF-8 with a BOM and CRLF, except .cmd and .bat,
    # which take CRLF and no BOM.
    lsTextExt = (".cs", ".py", ".ps1", ".md", ".htm", ".inix", ".txt", ".iss", ".cmd")
    sExecDir = os.path.join(sScriptDir, "exec")
    for sRoot, lsDirs, lsFiles in os.walk(sScriptDir):
        # exec holds built files too, but its CSharp and Python folders are the
        # kit's own source, and are checked like any other.
        if os.path.normcase(sRoot) == os.path.normcase(sExecDir):
            lsDirs[:] = [s for s in lsDirs if s in ("CSharp", "Python")]
            continue
        lsDirs[:] = [s for s in lsDirs if s.lower() not in c_lsSkipFolders or
                     (os.path.normcase(sRoot) == os.path.normcase(sScriptDir) and s.lower() == "exec")]
        for sName in sorted(lsFiles):
            if sName.lower() in c_lsGeneratedFiles: continue
            if sName.lower().startswith(c_sEvidencePrefix): continue
            if not sName.lower().endswith(lsTextExt): continue
            sPath = os.path.join(sRoot, sName)
            sShown = os.path.relpath(sPath, sScriptDir).replace(os.sep, "/")
            if os.path.getsize(sPath) == 0:
                lsProblems.append("empty: " + sShown)
                continue
            binData = open(sPath, "rb").read()
            bBom = binData.startswith(b"\xef\xbb\xbf")
            # A skill's SKILL.md opens with front matter, which a byte order
            # mark would hide; KeepEncoding.txt says so, and the check agrees.
            bWantBom = not (sName.lower().endswith((".cmd", ".bat", "version.txt")) or sName == "SKILL.md")
            if bBom != bWantBom:
                lsProblems.append("%s: %s a byte order mark" %
                                  (sShown, "should not have" if bBom else "needs"))
            iLf = binData.count(b"\n")
            iCrLf = binData.count(b"\r\n")
            if iLf != iCrLf:
                lsProblems.append("%s: %d of %d line endings are not CRLF" %
                                  (sShown, iLf - iCrLf, iLf))

    # EVERY LABEL ONCE, AND EVERY JUMP TO A LABEL THAT EXISTS (1.43.3). The C#
    # template of 1.43.2 was assembled with half of the Python template pasted
    # after its own subroutines: two :seedVersion labels, two :failed, and a
    # "call :seedVersion" that landed in the pasted copy, which found no
    # version.txt and failed twice without a word. cmd takes the first label
    # it meets, so a duplicate is never an error there -- only here.
    for sFolder in ("Templates", os.path.join("Templates", "samples"), "scripts"):
        sDir = os.path.join(sScriptDir, sFolder)
        if not os.path.isdir(sDir): continue
        for sName in sorted(os.listdir(sDir)):
            if not sName.lower().endswith((".cmd", ".bat")): continue
            sText = open(os.path.join(sDir, sName), "rb").read().decode("utf-8", errors="replace")
            lsLabels = [m.lower() for m in re.findall(r"(?im)^:(\w+)", sText)]
            for sLabel in sorted(set(lsLabels)):
                if lsLabels.count(sLabel) > 1:
                    lsProblems.append("%s/%s: the label :%s is defined %d times" %
                                      (sFolder.replace(os.sep, "/"), sName, sLabel, lsLabels.count(sLabel)))
            for sTarget in sorted(set(m.lower() for m in re.findall(r"(?i)\b(?:goto|call)\s+:(\w+)", sText))):
                if sTarget != "eof" and sTarget not in lsLabels:
                    lsProblems.append("%s/%s: jumps to :%s, which is not defined" %
                                      (sFolder.replace(os.sep, "/"), sName, sTarget))

    # EVERY SCRIPT CALLS NEIGHBOURS THAT EXIST (1.43.8). After the renames of
    # 1.42, tidy.cmd still ran "%~dp0homerTidy.py", check.cmd
    # "%~dp0checkHomerApp.py" and push.cmd tested for "%~dp0homerTidy.cmd"
    # -- files no longer there -- so tidy and check failed and push skipped the
    # whitelist without a word, in every app that refreshed them. A call to a
    # neighbour is a problem unless the file is in scripts, or the same line
    # first asks whether it exists.
    sScriptsDir = os.path.join(sScriptDir, "scripts")
    if os.path.isdir(sScriptsDir):
        lsHere = [sName.lower() for sName in os.listdir(sScriptsDir)]
        for sName in sorted(os.listdir(sScriptsDir)):
            if not sName.lower().endswith(".cmd"): continue
            sText = open(os.path.join(sScriptsDir, sName), "rb").read().decode("utf-8", errors="replace")
            for sLine in sText.splitlines():
                if sLine.lstrip().lower().startswith("rem"): continue
                for sCalled in re.findall(r"%~dp0([\w.]+\.(?:cmd|py|ps1))", sLine, re.I):
                    if sCalled.lower() in lsHere: continue
                    if re.search(r"if\s+exist\s+\"?%~dp0" + re.escape(sCalled), sLine, re.I): continue
                    lsProblems.append("scripts/%s calls %s, which is not in scripts" % (sName, sCalled))

    # A template that has lost its token would silently produce a broken app.
    for sName in ["build_APP_.cmd", "build_APP_Py.cmd", "_APP__setup.iss", "_APP_.cs",
                  "create_APP_Repo.cmd", "create_APP_Repo.ps1"]:
        sPath = os.path.join(sScriptDir, "Templates", sName)
        if not os.path.exists(sPath): continue
        if "_APP_" not in open(sPath, "rb").read().decode("utf-8-sig"):
            lsProblems.append("Templates/%s no longer carries the _APP_ token" % sName)

    return lsProblems


def main():
    global oLog
    if not os.path.isdir(os.path.dirname(sLogPath)): os.makedirs(os.path.dirname(sLogPath))
    oLog = open(sLogPath, "w", encoding="utf-8")
    logLine("build start pid=%d" % os.getpid())
    logFact("script", os.path.abspath(__file__))
    logFact("python", platform.python_version())
    logFact("windows", logWindows())
    logLine("Working directory: %s" % os.getcwd())
    logFact("arguments", " ".join(sys.argv[1:]))

    bCheckOnly = len(sys.argv) > 1 and sys.argv[1].lower() == "check"
    logLine("Check only: %s" % bCheckOnly)

    sVersion = "unknown"
    sVersionPath = os.path.join(sScriptDir, "version.txt")
    if os.path.exists(sVersionPath):
        sVersion = open(sVersionPath, "rb").read().decode("utf-8-sig").strip()
    sayLine("Homer Development Kit %s in %s" % (sVersion, sScriptDir))

    iSamplesFailed = 0
    if not bCheckOnly:
        # FIRST, AND WHETHER OR NOT PANDOC IS HERE. Renaming and retiring used
        # to run only inside the pandoc branch, so a machine without pandoc
        # kept every old file. Neither has anything to do with documents.
        renameScripts()
        patchScripts()
        removeMoved()
        sPandoc = findPandoc()
        if sPandoc == "":
            sayLine("Pandoc is not available, so the .htm files were left as they are.")
        else:
            iDone = convertDocs(sPandoc)
            sayLine("%d document%s converted to HTML." % (iDone, "" if iDone == 1 else "s"))
        iSamplesFailed = buildSamples()
        # After the samples, whose C# build installs the Build Tools if needed.
        sDllProblem = buildHomerDll()
        if sDllProblem != "":
            sayLine(sDllProblem)
            iSamplesFailed += 1
        buildTutorials()
        removeSkillHtm()
        findStaleAppBuilds()
        copySkillDocuments()
        extractSkillSections()
        iSkills = packSkills()
        sayLine("%d skill%s packed into exec\\skills, ready to upload to claude.ai." % (iSkills, "" if iSkills == 1 else "s"))
        removeStaleBinCopies()

    lsProblems = checkKit()
    if len(lsProblems) == 0 and iSamplesFailed == 0:
        sayLine("0 problems found. The kit is complete.")
        logLine("build end")
        return 0
    if len(lsProblems) == 0:
        sayLine("The kit itself is complete, but %d sample build%s failed."
                % (iSamplesFailed, "" if iSamplesFailed == 1 else "s"))
        logLine("build end")
        return 1

    sayLine("%d problem%s found:" % (len(lsProblems), "" if len(lsProblems) == 1 else "s"))
    # The console gets the first few; the log gets all of them. A console that
    # scrolls for a minute tells a screen reader user nothing at all.
    for sProblem in lsProblems[:c_iShowProblems]:
        sayLine("  " + sProblem)
    for sProblem in lsProblems[c_iShowProblems:]:
        logLine("PROBLEM: " + sProblem)
    if len(lsProblems) > c_iShowProblems:
        sayLine("  and %d more, all of them in %s." %
                (len(lsProblems) - c_iShowProblems, c_sLogName))
    logLine("build end result=problems")
    return 1


if __name__ == "__main__":
    iCode = 1
    try:
        iCode = main()
    except Exception:
        try:
            logLine("TRACEBACK:\n" + traceback.format_exc())
        except Exception:
            pass
        print("Something went wrong. The details are in %s." % sLogPath)
    finally:
        if oLog is not None: oLog.close()
    sys.exit(iCode)
