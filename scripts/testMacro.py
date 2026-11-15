"""testMacro: proves the macro recorder engine, exec\\CSharp\\Macro.cs (kit 1.231.0, 15 November 2026).

    testMacro           compile and run scripts\\testMacro.cs; exit 0 when every check passes

It compiles the test with the .NET Framework's own csc.exe at C# 5, the compiler DbDo, EdSharp and FileDir build
with, beside exec\\CSharp\\Inix.cs and Macro.cs, so a later C# form fails here before an app meets it. The test
records six navigation steps on a pretend 12-row view, saves and loads them, plays them, and compares the trail of
expected and actual rows step by step; then it proves the gate catches a host that claims success without moving,
and that a wrong view, a failing step, a cancel, a gap and malformed files are all refused.

Every line goes to logs\\HomerDev-testMacro-<time>.log: the computer, the compiler and its messages, the saved macro,
each check with its expected and actual values, and the closing count. The build runs this (build.py, checkMacro)
and fails when it fails; on a computer that is not Windows it says so and passes, since there is no csc.exe."""

import datetime, os, platform, subprocess, sys, tempfile, traceback

sScriptDir = os.path.dirname(os.path.abspath(__file__))
sRoot = os.path.dirname(sScriptDir)
sLogDir = os.path.join(sRoot, "logs")
os.makedirs(sLogDir, exist_ok=True)
sLog = os.path.join(sLogDir, "HomerDev-testMacro-%s.log" % datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))


def logLine(sText):
    with open(sLog, "a", encoding="utf-8") as oFile: oFile.write(datetime.datetime.now().isoformat(timespec="milliseconds") + "  " + sText + "\n")
    return True


def sayLine(sText):
    print(sText)
    logLine("CONSOLE: " + sText)
    return True


def findFrameworkCsc():
    """The .NET Framework 4 csc.exe, 64-bit first. Returns "" when there is none."""
    sWindows = os.environ.get("SystemRoot", r"C:\Windows")
    for sFolder in ("Framework64", "Framework"):
        sPath = os.path.join(sWindows, "Microsoft.NET", sFolder, "v4.0.30319", "csc.exe")
        if os.path.isfile(sPath): return sPath
    return ""


def main():
    logLine("testMacro %s, python %s, %s, cwd %s, args %s" % (sys.argv[0], sys.version.split()[0], platform.platform(), os.getcwd(), sys.argv[1:]))
    if os.name != "nt":
        sayLine("The macro engine test needs Windows and its csc.exe; not run here.")
        return 0
    sCsc = findFrameworkCsc()
    if not sCsc:
        sayLine("The macro engine test could not run: no .NET Framework csc.exe under %SystemRoot%\\Microsoft.NET.")
        return 1
    lsSources = [os.path.join(sRoot, "exec", "CSharp", "Inix.cs"), os.path.join(sRoot, "exec", "CSharp", "Macro.cs"),
                 os.path.join(sScriptDir, "testMacro.cs")]
    for sSource in lsSources:
        if not os.path.isfile(sSource):
            sayLine("The macro engine test could not run: %s is missing." % sSource)
            return 1
        logLine("source %s, %d bytes, modified %s" % (sSource, os.path.getsize(sSource), datetime.datetime.fromtimestamp(os.path.getmtime(sSource)).isoformat(timespec="seconds")))
    sExe = os.path.join(tempfile.gettempdir(), "HomerDev-testMacro.exe")
    lsCommand = [sCsc, "/nologo", "/langversion:5", "/out:" + sExe, "/reference:System.Core.dll", "/reference:System.Xml.dll",
                 "/reference:System.IO.Compression.dll", "/reference:System.IO.Compression.FileSystem.dll"] + lsSources
    logLine("compile: " + subprocess.list2cmdline(lsCommand))
    oDone = subprocess.run(lsCommand, capture_output=True, text=True, timeout=300)
    for sLine in ((oDone.stdout or "") + (oDone.stderr or "")).splitlines(): logLine("csc: " + sLine)
    logLine("csc exit %d" % oDone.returncode)
    if oDone.returncode != 0 or not os.path.isfile(sExe):
        lsErrors = [s for s in (oDone.stdout or "").splitlines() if " error " in s]
        sayLine("The macro engine did not compile at C# 5" + (": " + lsErrors[0].strip() if lsErrors else "") + ". See " + sLog)
        return 1
    oRun = subprocess.run([sExe], capture_output=True, text=True, timeout=120)
    lsFailed = []
    sSummary = ""
    for sLine in (oRun.stdout or "").splitlines():
        logLine("test: " + sLine)
        if sLine.startswith("FAIL "): lsFailed.append(sLine[5:])
        if sLine.startswith("testMacro: ") and " passed, " in sLine: sSummary = sLine[len("testMacro: "):]
    for sLine in (oRun.stderr or "").splitlines(): logLine("test stderr: " + sLine)
    logLine("test exit %d" % oRun.returncode)
    try: os.remove(sExe)
    except OSError: pass
    for sLine in lsFailed: sayLine("Macro test FAIL " + sLine)
    if oRun.returncode != 0 or lsFailed or not sSummary:
        sayLine("The macro engine test failed (%s). See %s" % (sSummary or "exit %d" % oRun.returncode, sLog))
        return 1
    sayLine("The macro engine passed its test: %s; playback matched what was expected at every step." % sSummary)
    return 0


if __name__ == "__main__":
    try: iCode = main()
    except Exception as oError:
        logLine(traceback.format_exc())
        sayLine("The macro engine test stopped with: %s" % oError)
        iCode = 1
    sys.exit(iCode)
