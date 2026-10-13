"""camelType.py -- renames constants from the obsolete c_ prefix to Camel Type's plain form, across a project's code.

    python scripts\\camelType.py [folder]          says what it would rename, and changes nothing
    python scripts\\camelType.py --fix [folder]    renames them

WHY. Camel Type names a constant exactly like a variable, type prefix and all -- sFormat, iMaxRetries -- and set apart
only by being declared as a constant. An earlier form put c_ in front, and that form is obsolete (12 October 2026). The
kit's tidy runs this with --fix on every project, so a project's code catches up without anybody renaming by hand.

WHAT IT RENAMES. A name shaped like Camel Type with c_ in front: c_, then a lowercase type prefix of one to five
letters, then a capital (c_sFormat, c_lsFiles, c_iMaxRetries). It never touches a library's own c_ names, such as
Python's ctypes.c_int or c_wchar_p, which are not that shape. A reference through a module or a class
(oRules.c_sLang) is renamed when the constant it names is defined in the project.

WHAT IT LEAVES. A constant whose plain name is already used for something else in a file that uses the constant -- a
list of every sample, c_lSamples, beside the samples being built this time, lSamples. Renaming it would merge two
different things, so it is left as it is and named in the report: it needs a person to give it a name that says what
it holds (lAllSamples). Documents are never changed: they may explain why c_ is obsolete.
"""

import collections, datetime, os, platform, re, sys

reName = re.compile(r"(?<![A-Za-z0-9_.])c_([a-z]{1,5}[A-Z][A-Za-z0-9]*)\b")
reDotted = re.compile(r"\.c_([a-z]{1,5}[A-Z][A-Za-z0-9]*)\b")
lsCodeExts = (".cs", ".iss", ".js", ".jsh", ".jss", ".ps1", ".py", ".vbs")
setSkipFolders = {".git", ".venv", "__pycache__", "logs", "node_modules", "notes", "venv", "work"}


def codeFiles(sRoot):
    """Every code file of the project; exec only where it holds a kit's own sources (exec\\CSharp, exec\\Python)."""
    for sDir, lsDirs, lsNames in os.walk(sRoot):
        sRelative = os.path.relpath(sDir, sRoot).replace("\\", "/").lower()
        lsDirs[:] = [s for s in lsDirs if s.lower() not in setSkipFolders]
        if sRelative.split("/")[0] == "exec" and not (sRelative.startswith("exec/csharp") or sRelative.startswith("exec/python")):
            lsDirs[:] = [s for s in lsDirs if s.lower() in ("csharp", "python")] if sRelative == "exec" else []
            if sRelative == "exec": continue
        for sName in lsNames:
            # This file describes the c_ form it renames, so it is never its own subject.
            if sName.lower().endswith(lsCodeExts) and sName.lower() != "cameltype.py": yield os.path.join(sDir, sName)


def readText(sPath):
    binRaw = open(sPath, "rb").read()
    return binRaw.decode("utf-8-sig", errors="replace"), binRaw.startswith(b"\xef\xbb\xbf")


def plan(sRoot):
    """(dRename {c_name: name}, dCollisions {c_name: [files]}, dTexts {file: (text, bBom)})."""
    dTexts = {sPath: readText(sPath) for sPath in codeFiles(sRoot)}
    dUses = collections.defaultdict(set)
    for sPath, (sText, bBom) in dTexts.items():
        for oMatch in reName.finditer(sText): dUses[oMatch.group(1)].add(sPath)
    dRename, dCollisions = {}, {}
    for sBare, setFiles in sorted(dUses.items()):
        reBare = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(sBare) + r"(?![A-Za-z0-9_])")
        lsTaken = sorted(sPath for sPath in setFiles if reBare.search(dTexts[sPath][0]))
        if lsTaken: dCollisions["c_" + sBare] = lsTaken
        else: dRename["c_" + sBare] = sBare
    return dRename, dCollisions, dTexts


def run(sRoot, bFix, fnLog=print):
    """Plans, and with bFix renames. Returns (names renamed, references changed, files changed, dCollisions)."""
    dRename, dCollisions, dTexts = plan(sRoot)
    iReferences = iFiles = 0
    for sPath, (sText, bBom) in sorted(dTexts.items()):
        sNew = reName.sub(lambda o: dRename.get("c_" + o.group(1), o.group(0)), sText)
        sNew = reDotted.sub(lambda o: "." + dRename["c_" + o.group(1)] if "c_" + o.group(1) in dRename else o.group(0), sNew)
        if sNew == sText: continue
        iChanged = sum(1 for _ in reName.finditer(sText)) + sum(1 for _ in reDotted.finditer(sText)) - sum(1 for _ in reName.finditer(sNew)) - sum(1 for _ in reDotted.finditer(sNew))
        iReferences += iChanged
        iFiles += 1
        fnLog("%s %s: %d reference%s" % ("RENAMED" if bFix else "WOULD RENAME", os.path.relpath(sPath, sRoot), iChanged, "" if iChanged == 1 else "s"))
        if bFix:
            with open(sPath, "wb") as fOut: fOut.write((b"\xef\xbb\xbf" if bBom else b"") + sNew.encode("utf-8"))
    for sOld, sNew in sorted(dRename.items()): fnLog("NAME %s -> %s" % (sOld, sNew))
    for sOld, lsFiles in sorted(dCollisions.items()):
        fnLog("KEPT %s: its plain name is already used in %s; give it a name that says what it holds" % (sOld, ", ".join(os.path.relpath(s, sRoot) for s in lsFiles)))
    return len(dRename), iReferences, iFiles, dCollisions


def main(lsArgs):
    bFix = "--fix" in lsArgs
    lsFolders = [s for s in lsArgs if not s.startswith("--")]
    sRoot = os.path.abspath(lsFolders[0] if lsFolders else os.getcwd())
    sLogDir = os.path.join(sRoot, "logs")
    os.makedirs(sLogDir, exist_ok=True)
    sLog = os.path.join(sLogDir, "%s-camelType-%s.log" % (os.path.basename(sRoot.rstrip("\\/")), datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))
    with open(sLog, "w", encoding="utf-8-sig") as fLog:
        def log(sText): fLog.write(sText + "\n"); return True
        log("camelType.py %s; Python %s on %s; folder %s; fix %s" % (os.path.abspath(__file__), platform.python_version(), platform.platform(), sRoot, bFix))
        iNames, iReferences, iFiles, dCollisions = run(sRoot, bFix, log)
    print("%s %d constant%s from c_ to Camel Type: %d reference%s in %d file%s." % ("Renamed" if bFix else "Would rename", iNames, "" if iNames == 1 else "s",
          iReferences, "" if iReferences == 1 else "s", iFiles, "" if iFiles == 1 else "s"))
    if dCollisions: print("%d kept c_, because their plain names are taken; the log names each." % len(dCollisions))
    print("Log: " + sLog)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
