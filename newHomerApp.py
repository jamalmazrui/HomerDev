#!/usr/bin/env python3
r"""newHomerApp.py -- start a new Homer Tools app from the HomerDev templates.

Usage (through the wrapper, which is how it is meant to be run):

    newHomerApp                     ask for the app name, write into C:\<App>
    newHomerApp JobDo               write C:\JobDo, a C# app
    newHomerApp JobDo --python      write C:\JobDo, a Python app
    newHomerApp JobDo D:\Work\JobDo  write somewhere else

What it writes into the app folder (1.43.31):
    <App>.cs                the C# starter (a Python app writes its own .py)
    build.cmd               the build script, compiling from C:\HomerDev
    <App>_setup.iss         the installer script
    create<App>Repo.cmd     the one-time GitHub bootstrap, and its .ps1
    version.txt             1.0.0
    accept.inix             what "done" means, for scripts\check
    RepoFiles.txt           what the repository carries
    LocalFiles.txt          what stays on this disk only
    .gitattributes          "* -text": git keeps the CRLF files as they are
    ReadMe.md, License.md   at the top; License is the MIT license
    help\<App>.md, Announce.md, Developer.md, History.md
                            starters for the document set
    help\self.md            the project's private notebook, never pushed
The kit's scripts (check, tidy, push, release, the installers' shared half)
are not written here: the first build copies them into scripts\. An app that
uses Ollama models copies Templates\installModels.cmd into scripts\ itself.
Nothing already in the folder is overwritten. Every file is written in the
Homer encoding: UTF-8 with a BOM and CRLF line endings, except .cmd and .bat,
which take CRLF and no BOM.

A detailed log is written in the kit's logs folder as
HomerDev-newHomerApp-<stamp>.log, as every tool in a project logs: the
environment, every effective setting, every file written or skipped, and any
traceback. Camel Type throughout.
"""

import datetime
import os
import platform
import sys
import traceback

c_sToken = "_APP_"
c_sLogName = "newHomerApp.log"

sScriptDir = os.path.dirname(os.path.abspath(__file__))
sLogPath = os.path.join(sScriptDir, "logs", "HomerDev-newHomerApp-%s.log" % datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
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
    """Console messages stay short and human; detail belongs in the log."""
    print(sText)
    logLine("CONSOLE: " + sText)
    return True


def readTemplate(sPath):
    """Read a template file, discarding any BOM."""
    return open(sPath, "rb").read().decode("utf-8-sig")


def writeHomer(sPath, sText):
    """UTF-8 with a BOM and CRLF, except .cmd, .bat and version.txt.

    version.txt is read by "set /p" in a batch file and by Inno Setup's
    FileRead, and both would take a byte order mark as part of the number, so
    it goes out bare like a .cmd.
    """
    sBody = sText.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
    bBom = not sPath.lower().endswith((".cmd", ".bat", "version.txt"))
    binData = (("\ufeff" + sBody) if bBom else sBody).encode("utf-8")
    open(sPath, "wb").write(binData)
    logLine("WROTE: %s, %d bytes, bom=%s" % (sPath, len(binData), bBom))
    return True


c_sMitLicense = """# License

MIT License

Copyright (c) {year} Jamal Mazrui

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

{app} is released under this license.
"""


def newProjectFiles(sApp, bPython):
    """The lists and document starters of a new project, as (path, text)."""
    sToday = datetime.date.today().strftime("%d %B %Y").lstrip("0")
    sSource = sApp + (".py" if bPython else ".cs")
    lsRepo = ["# RepoFiles.txt -- what the %s repository carries. tidy writes the" % sApp,
              "# .gitignore whitelist from this list alone.", "",
              ".gitattributes", "LocalFiles.txt", "License.htm", "License.md", "ReadMe.htm", "ReadMe.md",
              "RepoFiles.txt", "accept.inix", "build.cmd", "help/", sApp + "_setup.iss", sSource,
              "scripts/", ""]
    lsLocal = ["# LocalFiles.txt -- what belongs to %s on this disk, but never in the repository." % sApp, "",
               "exec/", "logs/", "notes/", sApp + "_setup.exe", "scripts/release.cmd", "scripts/release.ps1",
               "version.txt"]
    if bPython: lsLocal += [".venv/", "version.py", "work/"]
    else: lsLocal += ["Version.cs"]
    return [
        (".gitattributes", "* -text\n"),
        ("RepoFiles.txt", "\n".join(lsRepo)),
        ("LocalFiles.txt", "\n".join(lsLocal) + "\n"),
        ("License.md", c_sMitLicense.replace("{year}", str(datetime.date.today().year)).replace("{app}", sApp)),
        ("ReadMe.md", "# %s\n\n%s is a Homer Tools app. This ReadMe is its quick start; the full guide\n"
                      "is help\\%s.htm.\n" % (sApp, sApp, sApp)),
        ("help/%s.md" % sApp, "# %s\n\nThe full guide to %s, in topics by heading.\n" % (sApp, sApp)),
        ("help/Announce.md", "# %s: what is new\n\n%s 1.0.0 is the first release.\n" % (sApp, sApp)),
        ("help/Developer.md", "# %s: how it is built\n\n%s is built with the Homer Development Kit in\n"
                              "C:\\HomerDev: build makes exec\\%s.exe and %s_setup.exe.\n"
                              % (sApp, sApp, sApp, sApp)),
        ("help/History.md", "# %s History\n\n## 1.0.0, %s\n\nThe first release.\n" % (sApp, sToday)),
        ("help/self.md", "# %s notebook\n\nThe project's private notebook: plans, decisions and notes to\n"
                         "self. It is never pushed.\n" % sApp),
    ]


def main():
    global oLog
    os.makedirs(os.path.dirname(sLogPath), exist_ok=True)
    oLog = open(sLogPath, "w", encoding="utf-8-sig")
    logLine("newHomerApp start pid=%d" % os.getpid())
    logFact("script", os.path.abspath(__file__))
    logFact("python", platform.python_version())
    logFact("windows", logWindows())
    logLine("Working directory: %s" % os.getcwd())
    logFact("arguments", " ".join(sys.argv[1:]))

    lsWords = [s for s in sys.argv[1:] if s.lower() not in ("--python", "-python", "python")]
    bPython = len(lsWords) < len(sys.argv) - 1
    logLine("Language: %s" % ("Python" if bPython else "C#"))

    sApp = lsWords[0] if len(lsWords) > 0 else ""
    if sApp == "":
        sApp = input("Name of the new app (for example JobDo): ").strip()
    if sApp == "":
        sayLine("No app name was given, so nothing was written.")
        return 1
    for sBad in " \t/\\:*?\"<>|":
        if sBad in sApp:
            sayLine("An app name cannot contain %r." % sBad)
            logLine("ERROR: bad character %r in app name %r" % (sBad, sApp))
            return 1

    sTarget = lsWords[1] if len(lsWords) > 1 else os.path.join("C:\\", sApp)
    if os.name != "nt" and len(lsWords) <= 1:
        sTarget = os.path.join(os.getcwd(), sApp)
    sTemplates = os.path.join(sScriptDir, "Templates")

    logLine("App: %s" % sApp)
    logLine("Target: %s" % sTarget)
    logLine("Templates: %s" % sTemplates)

    if not os.path.isdir(sTemplates):
        sayLine("The Templates folder is missing from the kit.")
        logLine("ERROR: no Templates folder at %s" % sTemplates)
        return 1

    lsScripts = [
        ("_APP_.cs",             sApp + ".cs"),
        ("build_APP_.cmd",       "build.cmd"),
        ("_APP__setup.iss",      sApp + "_setup.iss"),
        ("create_APP_Repo.cmd",  "create" + sApp + "Repo.cmd"),
        ("create_APP_Repo.ps1",  "create" + sApp + "Repo.ps1"),
        ("version.txt",          "version.txt"),
        ("accept.inix",          "accept.inix"),
    ]

    if bPython:
        #  A Python app takes the Python build script instead of the C# one and
        #  writes its source from the Python sample rather than the C# starter.
        lsScripts = [t for t in lsScripts if t[0] not in ("_APP_.cs", "build_APP_.cmd")]
        lsScripts.insert(0, ("build_APP_Py.cmd", "build.cmd"))

    os.makedirs(sTarget, exist_ok=True)
    iWritten = 0
    iSkipped = 0
    for sFrom, sTo in lsScripts:
        sFromPath = os.path.join(sTemplates, sFrom)
        sToPath = os.path.join(sTarget, sTo)
        if not os.path.exists(sFromPath):
            sayLine("Template missing: %s" % sFrom)
            logLine("ERROR: template missing %s" % sFromPath)
            return 1
        if os.path.exists(sToPath):
            iSkipped += 1
            logLine("SKIPPED, already there: %s" % sToPath)
            continue
        writeHomer(sToPath, readTemplate(sFromPath).replace(c_sToken, sApp))
        iWritten += 1

    # THE REST OF A NEW PROJECT (1.43.31). newHomerApp used to copy install
    # scripts to the top of the app, which the Homer layout keeps in scripts
    # and the first build refreshes there anyway, and it asked for a
    # Templates\\self.md that git never carries -- so on a kit cloned from
    # GitHub it stopped at "Template missing: self.md". It now writes the lists
    # and document starters every Homer project has, and the notebook from text
    # of its own.
    for sTo, sText in newProjectFiles(sApp, bPython):
        sToPath = os.path.join(sTarget, sTo.replace("/", os.sep))
        if os.path.exists(sToPath):
            iSkipped += 1
            logLine("SKIPPED, already there: %s" % sToPath)
            continue
        os.makedirs(os.path.dirname(sToPath), exist_ok=True)
        writeHomer(sToPath, sText)
        iWritten += 1

    sayLine("%d file%s written in %s." % (iWritten, "" if iWritten == 1 else "s", sTarget))
    if iSkipped:
        sayLine("%d file%s left alone, already there." % (iSkipped, "" if iSkipped == 1 else "s"))
    if bPython:
        sayLine("Next: write %s.py -- Templates\\samples\\FruitBasketPy is the worked example --"
                % sApp)
        sayLine("set the AppId and hotkey in %s_setup.iss, then run build." % sApp)
    else:
        sayLine("Next: fill in runScript() in %s.cs, set the AppId and hotkey in %s_setup.iss, then run build."
                % (sApp, sApp))
    logLine("newHomerApp end")
    return 0


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
