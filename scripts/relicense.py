"""relicense.py -- make a Homer app MIT-licensed, everywhere it says so.

Every Homer app is under the MIT License (2 October 2026), the NVDA add-on in
HomerView included: NV Access's Add-on Store records an add-on's license but
does not require any particular one, and MIT is compatible with NVDA's GPL.
check fails an app whose License.md is not the MIT License; this script brings
one into line.

Usage:
  relicense                 the app in the current folder
  relicense C:\\HomerView ... the apps named
  relicense all             every app beside the kit

For each app:
  1. License.md: when it is not the MIT License, it becomes the kit's MIT text
     naming Jamal Mazrui, as newHomerApp writes it. A license file spelled
     another way (LICENSE.md) is renamed to License.md through git mv, and
     RepoFiles.txt, LocalFiles.txt and the installer script follow.
  2. The app's own claims to another license become "MIT License": a line
     naming Jamal Mazrui together with a GNU license; a line holding only a
     license name (";Modified GPL License") within three lines after a
     copyright line naming him; and "<App> is free software under the GNU
     ...". Lines about other people's software -- 7-Zip under the LGPL, mpv
     under the GPL -- name neither him nor the app, and are left alone, as
     are History.md and History.htm, which record what was true at the time.
  3. Each change goes to logs\\<App>-relicense-yyyyMMdd-HHmmss.log.

A file's encoding, byte order mark and line ends are kept. Running it again
on an MIT app changes nothing. The build turns License.md into License.htm.

Exit codes: 0 done, 1 something could not be changed (the log says what).
"""
import datetime, os, platform, re, subprocess, sys

c_lsTextExtensions = (".cmd", ".htm", ".inix", ".ini", ".iss", ".jsh", ".jss", ".md", ".ps1", ".py", ".txt", ".cs")
c_lsSkipFolders = (".git", "__pycache__", "exec", "logs", "node_modules", "notes")
c_sGnu = r"(?:the\s+)?(?:modified\s+)?(?:GNU\s+)?(?:Lesser\s+|Affero\s+)?General\s+Public\s+License(?:\s*\((?:A|L)?GPL\))?(?:,?\s+version\s+[\d.]+)?(?:\s+or\s+later)?|(?:modified\s+)?\b(?:A|L)?GPL\b(?:\s*v?\d(?:\.\d)?\+?)?(?:\s+or\s+later)?(?:\s+License)?"

oLog = None


def logLine(sText):
    if oLog:
        oLog.write("%s %s\r\n" % (datetime.datetime.now().isoformat(timespec="milliseconds"), sText))
        oLog.flush()


def sayLine(sText):
    print(sText)
    logLine("CONSOLE: " + sText)


def startLog(sAppDir, sApp):
    global oLog
    sLogDir = os.path.join(sAppDir, "logs")
    os.makedirs(sLogDir, exist_ok=True)
    sPath = os.path.join(sLogDir, "%s-relicense-%s.log" % (sApp, datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))
    oLog = open(sPath, "w", encoding="utf-8-sig", newline="")
    logLine("relicense start pid=%d" % os.getpid())
    logLine("env script=%s python=%s windows=%s" % (os.path.abspath(__file__), platform.python_version(), platform.platform()))
    logLine("env app=%s" % sAppDir)
    return sPath


def mitText():
    """The kit's MIT text, as newHomerApp writes it."""
    sKit = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sSource = open(os.path.join(sKit, "newHomerApp.py"), encoding="utf-8-sig").read()
    oMatch = re.search(r'c_sMitLicense = """(.*?)"""', sSource, re.S)
    return oMatch.group(1).replace("{year}", str(datetime.date.today().year))


def readKeep(sPath):
    """The text, and how to write it back the same way."""
    binData = open(sPath, "rb").read()
    bBom = binData.startswith(b"\xef\xbb\xbf")
    sText = binData[3 if bBom else 0:].decode("utf-8")
    return sText, bBom


def writeKeep(sPath, sText, bBom):
    open(sPath, "wb").write((b"\xef\xbb\xbf" if bBom else b"") + sText.encode("utf-8"))


def fixLicenseFile(sAppDir):
    """License.md holds the MIT text, under that exact name."""
    dNames = {s.lower(): s for s in os.listdir(sAppDir)}
    sFound = dNames.get("license.md")
    if sFound and sFound != "License.md":
        bGit = os.path.isdir(os.path.join(sAppDir, ".git"))
        try:
            if bGit:
                for lsArgs in (["git", "mv", sFound, "License.md.tmp"], ["git", "mv", "License.md.tmp", "License.md"]):
                    oResult = subprocess.run(lsArgs, cwd=sAppDir, capture_output=True, text=True)
                    logLine("RUN %s exit=%d %s" % (" ".join(lsArgs), oResult.returncode, (oResult.stdout + oResult.stderr).strip()))
                    if oResult.returncode: raise OSError("git mv failed")
            else:
                os.rename(os.path.join(sAppDir, sFound), os.path.join(sAppDir, "License.md"))
            sayLine("  Renamed %s to License.md." % sFound)
            # The other files that name it follow: the whitelist, the installer.
            for sOther in os.listdir(sAppDir):
                sOtherLower = sOther.lower()
                if not (sOtherLower in ("repofiles.txt", "localfiles.txt") or sOtherLower.endswith("_setup.iss")): continue
                sOtherPath = os.path.join(sAppDir, sOther)
                sText, bBom = readKeep(sOtherPath)
                sNew = re.sub(r"(?<![\\/\w])" + re.escape(sFound) + r"\b", "License.md", sText)
                if sNew != sText:
                    writeKeep(sOtherPath, sNew, bBom)
                    logLine("%s: %s renamed to License.md in it" % (sOther, sFound))
        except OSError as oError:
            sayLine("  Could not rename %s to License.md: %s" % (sFound, oError))
            return False
    sPath = os.path.join(sAppDir, "License.md")
    if os.path.isfile(sPath):
        sText, bBom = readKeep(sPath)
        if "MIT License" in sText:
            logLine("License.md already holds the MIT License")
            return True
        logLine("License.md before:\r\n" + sText)
    sMit = mitText()
    writeKeep(sPath, sMit.replace("\r\n", "\n").replace("\n", "\r\n"), True)
    sayLine("  License.md is now the MIT License.")
    return True


def rewriteClaims(sAppDir, sApp, bDryRun=False):
    """The app's own claims to another license become MIT. Returns files changed,
    or with bDryRun, a list of "file line N: text" for each claim, changing nothing."""
    lsClaims = []
    oNamed = re.compile(r"(?i)(Jamal\s+Mazrui.*?)(" + c_sGnu + r")")
    oApp = re.compile(r"(?i)(" + re.escape(sApp) + r"\s+is\s+(?:free\s+software\s+)?(?:distributed\s+|released\s+|licensed\s+)?under\s+)(" + c_sGnu + r")")
    oAlone = re.compile(r"(?i)^(\W*)(" + c_sGnu + r")(\W*)$")
    oCopyright = re.compile(r"(?i)copyright.*Jamal\s+Mazrui")
    iFiles = 0
    for sDir, lsDirs, lsFiles in os.walk(sAppDir):
        lsDirs[:] = [s for s in lsDirs if s.lower() not in c_lsSkipFolders]
        for sName in lsFiles:
            sLower = sName.lower()
            if not sLower.endswith(c_lsTextExtensions): continue
            if sLower in ("history.md", "history.htm", "license.md", "license.htm"): continue
            sPath = os.path.join(sDir, sName)
            try:
                sText, bBom = readKeep(sPath)
            except (UnicodeDecodeError, OSError):
                continue
            lsLines = sText.split("\n")
            iChanged = 0
            iSinceCopyright = 99
            for iAt, sLine in enumerate(lsLines):
                sEnd = "\r" if sLine.endswith("\r") else ""
                sBody = sLine[:-1] if sEnd else sLine
                if oCopyright.search(sBody): iSinceCopyright = 0
                else: iSinceCopyright += 1
                sNew = oNamed.sub(lambda m: m.group(1) + "MIT License", sBody)
                sNew = oApp.sub(lambda m: m.group(1) + "the MIT License", sNew)
                if 0 < iSinceCopyright <= 3:
                    sNew = oAlone.sub(lambda m: m.group(1) + "MIT License" + m.group(3), sNew)
                sNew += sEnd
                if sNew != sLine and bDryRun:
                    lsClaims.append("%s line %d: %s" % (os.path.relpath(sPath, sAppDir), iAt + 1, sBody.strip()[:100]))
                    continue
                if sNew != sLine:
                    logLine("%s line %d: %r -> %r" % (os.path.relpath(sPath, sAppDir), iAt + 1, sLine.strip(), sNew.strip()))
                    lsLines[iAt] = sNew
                    iChanged += 1
            if iChanged:
                writeKeep(sPath, "\n".join(lsLines), bBom)
                iFiles += 1
    return lsClaims if bDryRun else iFiles


def needsRelicense(sAppDir, sApp):
    """Whether anything here is not yet MIT: License.md, or a claim elsewhere."""
    dNames = {s.lower(): s for s in os.listdir(sAppDir)}
    sFound = dNames.get("license.md")
    if sFound != "License.md": return True
    if "MIT License" not in readKeep(os.path.join(sAppDir, sFound))[0]: return True
    return bool(rewriteClaims(sAppDir, sApp, bDryRun=True))


def relicenseApp(sAppDir, bIfNeeded=False):
    sAppDir = os.path.abspath(sAppDir)
    sApp = os.path.basename(sAppDir.rstrip("\\/"))
    if bIfNeeded and not needsRelicense(sAppDir, sApp): return True
    sLog = startLog(sAppDir, sApp)
    sayLine("%s:" % sApp)
    bOk = fixLicenseFile(sAppDir)
    iFiles = rewriteClaims(sAppDir, sApp)
    if iFiles:
        sayLine("  Claims to another license changed to MIT in %d file%s." % (iFiles, "" if iFiles == 1 else "s"))
    sayLine("  Log: %s" % sLog)
    logLine("relicense end ok=%s" % bOk)
    return bOk


def main():
    lsArgs = sys.argv[1:]
    # --if-needed (tidy's call): do nothing, and write no log, when the app is
    # already MIT throughout.
    bIfNeeded = "--if-needed" in [s.lower() for s in lsArgs]
    lsArgs = [s for s in lsArgs if s.lower() != "--if-needed"]
    sKit = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if lsArgs and lsArgs[0].lower() == "all":
        sParent = os.path.dirname(sKit)
        lsApps = []
        for sName in sorted(os.listdir(sParent), key=str.lower):
            sDir = os.path.join(sParent, sName)
            if os.path.normcase(sDir) == os.path.normcase(sKit): continue
            if not os.path.isdir(os.path.join(sDir, ".git")): continue
            if os.path.isfile(os.path.join(sDir, "build.cmd")): lsApps.append(sDir)
    elif lsArgs:
        lsApps = lsArgs
    else:
        lsApps = [os.getcwd()]
    if not lsApps:
        print("No app folders found.")
        return 0
    bOk = True
    for sApp in lsApps:
        bOk = relicenseApp(sApp, bIfNeeded) and bOk
    if not bIfNeeded: print("Done. Build, then push, so git records the change.")
    return 0 if bOk else 1


if __name__ == "__main__":
    sys.exit(main())
