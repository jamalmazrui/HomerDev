r"""auditTree.py -- checks every Homer project on this computer against the Homer tree (help\HomerTree.md) and
reports drift. Part of the HomerDev kit (1.204.0). It changes nothing.

    auditTree                  every project it finds: folders beside the kit, and the projects data\Projects.inix names
    auditTree <folder> ...     only these

WHAT IT REPORTS, per project: a top-level folder the tree does not name and the project's lists do not declare; a
folder whose name differs from the tree's only in case, such as Templates; a temp folder, now work; a script, log or
archive loose at the top; a kit tool kept at the top instead of in scripts. Each finding says what the tree expects.

THE REPORT is results\HomerDev-auditTree-yyyyMMdd-HHmmss.md in the kit, a list a screen reader moves through by
heading, one heading per project; the log is logs\HomerDev-auditTree-yyyyMMdd-HHmmss.log. The console says one line
per project.
"""

import datetime, io, os, platform, re, sys

dState = {"fLog": None}
lsKitTools = ["check", "fixencoding", "fixpages", "kind", "projectcycle", "push", "release", "tidy", "unpushed"]
lsTopScriptsAllowed = ["build", "build_release"]


def log(sText):
    if dState["fLog"] is not None: dState["fLog"].write(datetime.datetime.now().strftime("%H:%M:%S ") + sText + "\n")
    return True


def declared(sRoot):
    """Every line of RepoFiles.txt and LocalFiles.txt, lowercased with forward slashes."""
    lsLines = []
    for sName in ("RepoFiles.txt", "LocalFiles.txt"):
        sPath = os.path.join(sRoot, sName)
        if not os.path.isfile(sPath): continue
        for sLine in io.open(sPath, "rb").read().decode("utf-8-sig", "replace").splitlines():
            sLine = sLine.strip()
            if sLine and not sLine.startswith(("#", ";")): lsLines.append(sLine.replace("\\", "/").lower())
    return lsLines


def auditProject(sRoot, oKind):
    """Returns (kind, role, findings) for one project."""
    sKind, sWhy = oKind.projectKind(sRoot)
    sRole = oKind.projectRole(sRoot)[0]
    setStandard = oKind.standardFolders(sKind)
    lsDeclared = declared(sRoot)
    sName = os.path.basename(sRoot)
    lsFindings = []
    for sEntry in sorted(os.listdir(sRoot), key=str.lower):
        sPath = os.path.join(sRoot, sEntry)
        sLower = sEntry.lower()
        if os.path.isdir(sPath):
            if sLower == "temp": lsFindings.append("temp is now work: scratch belongs in work (w); t is templates only.")
            elif sLower in setStandard and sEntry != sLower: lsFindings.append("%s should be %s: Homer folder names are lower case." % (sEntry, sLower))
            elif sLower not in setStandard and sLower != "__pycache__" and not any(s.startswith(sLower + "/") for s in lsDeclared):
                lsFindings.append("%s is not a Homer folder: nest it in a standard one, declare it in LocalFiles.txt, or retire it to notes." % sEntry)
            continue
        sStem, sExtension = os.path.splitext(sLower)
        if sExtension == ".log": lsFindings.append("%s is a log at the top: logs go in logs." % sEntry)
        elif sExtension == ".zip" and not sLower.endswith("_guide.zip"): lsFindings.append("%s is an archive at the top: outputs go in results." % sEntry)
        elif sExtension in (".cmd", ".ps1", ".py", ".bat") and sStem in lsKitTools: lsFindings.append("%s is a kit tool at the top: kit tools belong in scripts." % sEntry)
        elif sExtension in (".cmd", ".ps1", ".py", ".bat") and sStem != sName.lower() and sStem not in lsTopScriptsAllowed and sKind != "kit":
            lsFindings.append("%s is a script at the top: scripts belong in scripts." % sEntry)
    if sKind in ("collection", "page") and not os.path.isfile(os.path.join(sRoot, "RepoFiles.txt")):
        lsFindings.append("There is no RepoFiles.txt: tidy needs one to know what belongs here.")
    log("%s: kind %s, role %s, %d finding%s" % (sRoot, sKind, sRole, len(lsFindings), "" if len(lsFindings) == 1 else "s"))
    for sFinding in lsFindings: log("    " + sFinding)
    return sKind, sRole, lsFindings


lsHomerMarks = ["build_release.bat", "LocalFiles.txt", "RepoFiles.txt"]


def registeredNames(sKit):
    """The project names data\\Projects.inix lists, lowercased: one [section] each."""
    sPath = os.path.join(sKit, "data", "Projects.inix")
    if not os.path.isfile(sPath): return []
    sText = io.open(sPath, "rb").read().decode("utf-8-sig", "replace")
    return [s.strip().lower() for s in re.findall(r"^\[([^\]]+)\]", sText, re.M)]


def findProjects(sKit, oKind):
    """The Homer projects beside the kit.

    ONLY HOMER PROJECTS (1.205.0). Version 1 asked kind.py about every folder beside the kit, and C:\\HomerDev sits at
    the top of drive C, beside Windows, Program Files and the rest; its first real run stopped on C:\\Config.Msi,
    which an account may not read. A folder is audited now when Projects.inix names it, kind.py knows its name as a
    role (MyBooks, MyPages, AppHelpGuides, PodcastDirectories), or it carries a Homer mark: build_release.bat,
    RepoFiles.txt or LocalFiles.txt. A folder that cannot be read is skipped and logged, never fatal."""
    sParent = os.path.dirname(sKit)
    setNames = set(registeredNames(sKit)) | set(oKind.dRolesByName)
    lsFound = []
    for sEntry in sorted(os.listdir(sParent), key=str.lower):
        sPath = os.path.join(sParent, sEntry)
        try:
            if not os.path.isdir(sPath) or sEntry.startswith((".", "$")) or os.path.normcase(sPath) == os.path.normcase(sKit): continue
            if sEntry.lower() in setNames or any(os.path.isfile(os.path.join(sPath, s)) for s in lsHomerMarks): lsFound.append(sPath)
        except OSError as oError:
            log("SKIPPED %s: %s" % (sPath, oError))
    return [sKit] + lsFound


def main():
    sHere = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, sHere)
    import kind as oKind
    sKit = os.path.dirname(sHere)
    sStamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    for sFolder in ("logs", "results"): os.makedirs(os.path.join(sKit, sFolder), exist_ok=True)
    sLogPath = os.path.join(sKit, "logs", "HomerDev-auditTree-%s.log" % sStamp)
    sReportPath = os.path.join(sKit, "results", "HomerDev-auditTree-%s.md" % sStamp)
    dState["fLog"] = io.open(sLogPath, "w", encoding="utf-8-sig", newline="\r\n")
    log("auditTree.py (HomerDev 1.205.0); script %s; Python %s on %s; cwd %s; command line %s" % (
        os.path.abspath(__file__), platform.python_version(), platform.platform(), os.getcwd(), " ".join(sys.argv)))
    lsRoots = [os.path.abspath(s) for s in sys.argv[1:]] or findProjects(sKit, oKind)
    lsLines = ["# Homer tree audit, %s" % datetime.date.today().strftime("%d %B %Y").lstrip("0"), "",
               "Each project is checked against help\\HomerTree.md. Nothing was changed.", ""]
    iTotal = 0
    for sRoot in lsRoots:
        try: sKind, sRole, lsFindings = auditProject(sRoot, oKind)
        except OSError as oError:
            sKind, sRole, lsFindings = "unknown", "unknown", ["Could not be read: %s." % oError]
            log("COULD NOT READ %s: %s" % (sRoot, oError))
        iTotal += len(lsFindings)
        print("%s: %s" % (os.path.basename(sRoot), "conforms" if not lsFindings else "%d finding%s" % (len(lsFindings), "" if len(lsFindings) == 1 else "s")))
        lsLines += ["## %s" % os.path.basename(sRoot), "", "Kind %s, role %s." % (sKind, sRole), ""]
        lsLines += ["- " + s for s in lsFindings] if lsFindings else ["Conforms."]
        lsLines.append("")
    io.open(sReportPath, "w", encoding="utf-8-sig", newline="\r\n").write("\n".join(lsLines))
    print("Projects: %d. Findings: %d. Report: %s" % (len(lsRoots), iTotal, sReportPath))
    log("RUN ENDED: %d projects, %d findings; report %s" % (len(lsRoots), iTotal, sReportPath))
    dState["fLog"].close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
