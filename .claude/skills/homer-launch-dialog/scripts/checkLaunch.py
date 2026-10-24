r"""checkLaunch.py -- part of the shared Homer toolkit (homer-launch-dialog skill).

Checks that a Homer launch app follows the launch-dialog pattern
(help\LaunchDialog.md in the kit, 23 October 2026).

    checkLaunch.py <project folder> [--app <name>]

A project is a launch app when its own source builds a LaunchDialog, or shows
a dialog with both Default settings and Use configuration. Exit codes: 0 not a
launch app, or it follows the pattern; 1 it breaks the pattern; 2 the check
could not run. Retired names still in the documents are printed as warnings
and do not change the exit code. Everything is printed, so the caller's log
holds the whole of it.
"""

import argparse, datetime, os, platform, re, sys

lsSkipFolders = {".git", "data", "exec", "logs", "notes", "results", "scripts", "templates"}

# Retired controls and captions, as they appear in code. Each is a failure.
dRetiredCode = {
    "a Guide button": r'"Guide"',
    "a Log session checkbox": r'&Log session',
    "an Include subfolders checkbox": r'Include subfolders',
    "the old Browse source caption": r'&Browse source\.\.\.',
    "the old Choose output caption": r'&Choose output\.\.\.',
}

# Retired names in the documents. Each is a warning.
dRetiredDocs = {
    "Guide button": r'\bGuide button\b',
    "Log session": r'\bLog session\b',
    "Include subfolders": r'\bInclude subfolders\b',
    "Browse source (old caption)": r'\bBrowse source\b(?! paths)',
    "Choose output (old caption)": r'\bChoose output\b(?! directory)',
}


def codeLines(sText):
    """The text with comment-only lines removed: a comment explaining a rule is not a breach of it."""
    return "\n".join(s for s in sText.splitlines() if not s.strip().startswith(("//", "#", "*", "rem ")))


def readText(sPath):
    try:
        return open(sPath, "rb").read().decode("utf-8-sig", errors="replace")
    except Exception:
        return ""


def ownFiles(sRoot, tExtensions):
    lsFiles = []
    for sDirPath, lsDirs, lsNames in os.walk(sRoot):
        lsDirs[:] = [s for s in lsDirs if s.lower() not in lsSkipFolders and not s.startswith(".")]
        for sName in sorted(lsNames):
            if sName.lower().endswith(tExtensions): lsFiles.append(os.path.join(sDirPath, sName))
    return lsFiles


def main():
    oParser = argparse.ArgumentParser(description="Check a Homer launch app against the launch-dialog pattern.")
    oParser.add_argument("project")
    oParser.add_argument("--app", default="")
    oArgs = oParser.parse_args()
    sRoot = os.path.abspath(oArgs.project)
    sApp = oArgs.app or os.path.basename(os.path.normpath(sRoot))
    print("checkLaunch %s, python %s, %s, cwd %s" % (datetime.datetime.now().isoformat(timespec="seconds"),
          platform.python_version(), platform.platform(), os.getcwd()))
    print("project=%s app=%s" % (sRoot, sApp))
    if not os.path.isdir(sRoot):
        print("No such folder: " + sRoot)
        return 2
    lsSources = ownFiles(sRoot, (".cs", ".py"))
    dCode = {sPath: codeLines(readText(sPath)) for sPath in lsSources}
    sAll = "\n".join(dCode.values())
    bLaunch = "LaunchDialog(" in sAll or ("Default settings" in sAll and "Use configuration" in sAll and "MdiFrame" not in sAll)
    if not bLaunch:
        print("checkLaunch: %s is not a launch app; nothing to check." % sApp)
        return 0
    lsFailures = []
    if "LaunchDialog(" not in sAll: lsFailures.append("the dialog is not built with the kit's LaunchDialog")
    if "showResults(" not in sAll and "LaunchDialog.finish(" not in sAll:
        lsFailures.append("no run ends with LaunchDialog.finish or LaunchDialog.showResults")
    # THE PROGRESS WINDOW (23 October 2026): a launch app shows its work in the kit's
    # LaunchProgress, or at least uses its in-front test, never a form of its own whose
    # StatusBar-role label is not reliably spoken, and never Say alone, which speaks
    # over whatever program is in front.
    if "LaunchProgress" not in sAll: lsFailures.append("the work is not shown with the kit's LaunchProgress")
    for sPath, sCode in dCode.items():
        if "AccessibleRole.StatusBar" in sCode:
            lsFailures.append("%s still builds a progress label with AccessibleRole.StatusBar; use LaunchProgress" % os.path.relpath(sPath, sRoot))
        for sWhat, sPattern in dRetiredCode.items():
            for oMatch in re.finditer(sPattern, sCode):
                iLine = sCode.count("\n", 0, oMatch.start()) + 1
                lsFailures.append("%s still has %s (code line %d)" % (os.path.relpath(sPath, sRoot), sWhat, iLine))
    lsWarnings = []
    for sPath in ownFiles(sRoot, (".md", ".inix")):
        sName = os.path.basename(sPath).lower()
        if sName.startswith(("history", "announce")): continue
        sText = readText(sPath)
        for sWhat, sPattern in dRetiredDocs.items():
            iCount = len(re.findall(sPattern, sText))
            if iCount: lsWarnings.append("%s mentions %s %d time%s" % (os.path.relpath(sPath, sRoot), sWhat, iCount, "" if iCount == 1 else "s"))
    for sLine in lsFailures: print("FAIL " + sLine)
    for sLine in lsWarnings: print("WARN " + sLine)
    print("checkLaunch: %s, %d failure%s, %d warning%s." % (sApp, len(lsFailures), "" if len(lsFailures) == 1 else "s",
          len(lsWarnings), "" if len(lsWarnings) == 1 else "s"))
    return 1 if lsFailures else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as oError:
        import traceback
        traceback.print_exc()
        sys.exit(2)
