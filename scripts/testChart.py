r"""testChart: proves the kit's chart engine draws every kind of chart (HomerDev 1.269.0, 21 November 2026).

    testChart       run the checks; exit 0 when every chart is drawn

exec\CSharp\DataReport.cs holds the Python script that draws DbDo's Generate Graphics charts, in a verbatim C# string.
This test takes the script out of the C# file -- so what is tested is what the apps compile -- makes a small table
of 60 records, and draws each kind of chart from it: bar, pareto, pie, histogram, box, scatter, date, line by
column, line by row and bar by row. Each must write its picture (PNG and SVG), its page and its workbook, and say its
takeaway sentence. A missing package (pandas, matplotlib, seaborn, openpyxl) is installed by the script itself with
pip, as on a user's computer, and the run says so. Everything goes to logs\HomerDev-testChart-<time>.log: the
environment, each command with its exit code, the script's output and any error. The kit's build runs it."""

import csv, datetime, os, platform, random, shutil, subprocess, sys, tempfile, traceback

sScriptDir = os.path.dirname(os.path.abspath(__file__))
sRoot = os.path.dirname(sScriptDir)
if sScriptDir not in sys.path: sys.path.insert(0, sScriptDir)
from kind import writableLogDir
sLogDir = writableLogDir(sRoot)
sLog = os.path.join(sLogDir, "HomerDev-testChart-%s.log" % datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
oLog = None


def logLine(sText):
    oLog.write(sText + "\n")
    oLog.flush()


def chartScript():
    """The Python inside DataReport.cs's sChartScript string."""
    sCs = open(os.path.join(sRoot, "exec", "CSharp", "DataReport.cs"), encoding="utf-8-sig").read()
    sStart = 'sChartScript = @"'
    iStart = sCs.index(sStart) + len(sStart)
    return sCs[iStart:sCs.index('";', iStart)].replace("\r\n", "\n")


def main():
    global oLog
    os.makedirs(sLogDir, exist_ok=True)
    oLog = open(sLog, "w", encoding="utf-8")
    logLine("testChart, %s" % datetime.datetime.now().isoformat(timespec="seconds"))
    logLine("Script: %s" % os.path.abspath(__file__))
    logLine("Python: %s (%s)" % (sys.version.split()[0], sys.executable))
    logLine("Platform: %s" % platform.platform())
    logLine("Working folder: %s" % os.getcwd())
    logLine("Command line: %s" % " ".join(sys.argv))
    sWork = tempfile.mkdtemp(prefix="homerTestChart_")
    logLine("Work folder: %s" % sWork)
    sScript = os.path.join(sWork, "homerChart.py")
    open(sScript, "w", encoding="utf-8").write(chartScript())
    random.seed(1)
    lsHeads = ["Name", "Region", "Active", "Price", "Units", "Jan", "Feb", "Mar", "Added"]
    sCsv = os.path.join(sWork, "records.csv")
    with open(sCsv, "w", newline="", encoding="utf-8-sig") as oFile:
        oWriter = csv.writer(oFile)
        oWriter.writerow(lsHeads)
        for i in range(60):
            oWriter.writerow(["Item %d" % i, random.choice(["North", "South", "East", "West", "Central"]), random.choice(["Yes", "No"]),
                              round(random.uniform(5, 100), 2), random.randint(1, 50), random.randint(10, 90), random.randint(10, 90),
                              random.randint(10, 90), "2026-%02d-%02d" % (random.randint(1, 11), random.randint(1, 28))])
    dSpecs = {
        "bar": "kind=bar\nx=Region", "pareto": "kind=pareto\nx=Region", "pie": "kind=pie\nx=Active",
        "histogram": "kind=histogram\nx=Price", "box": "kind=box\ncolumns=Price\tUnits", "scatter": "kind=scatter\nx=Price\ny=Units",
        "date": "kind=datechart\nx=Added\nperiod=month", "line by column": "kind=line\ncolumns=Price\tUnits\nlabel=Name\narrange=column",
        "line by row": "kind=line\ncolumns=Jan\tFeb\tMar\nlabel=Name\narrange=row", "bar by row": "kind=rowbar\ncolumns=Jan\tFeb\tMar\nlabel=Name\narrange=row"}
    iFailed = 0
    for sName, sSpec in dSpecs.items():
        sBase = os.path.join(sWork, sName.replace(" ", "_"))
        sSpecFile = sBase + ".spec"
        open(sSpecFile, "w", encoding="utf-8").write("title=Test %s\nbase=%s\n%s\n" % (sName, sBase, sSpec))
        lsCommand = [sys.executable, sScript, sCsv, sSpecFile]
        oDone = subprocess.run(lsCommand, capture_output=True, text=True, timeout=900)
        logLine("Command: %s, exit code %d" % (" ".join(lsCommand), oDone.returncode))
        for sLine in (oDone.stdout or "").strip().splitlines(): logLine("  said: " + sLine)
        for sLine in (oDone.stderr or "").strip().splitlines(): logLine("  error: " + sLine)
        lsMissing = [sExt for sExt in ("png", "svg", "htm", "xlsx") if not os.path.isfile(sBase + "." + sExt)]
        bSummary = "summary=" in (oDone.stdout or "")
        if oDone.returncode != 0 or lsMissing or not bSummary:
            iFailed += 1
            sWhy = (oDone.stderr or "").strip().splitlines()[-1:] or ["no " + ", ".join(lsMissing) if lsMissing else "no takeaway sentence"]
            print("FAIL %s chart: %s" % (sName, sWhy[0]))
            logLine("FAIL %s: missing %s" % (sName, ", ".join(lsMissing) or "nothing"))
        else:
            logLine("PASS %s" % sName)
    shutil.rmtree(sWork, ignore_errors=True)
    iCount = len(dSpecs)
    if iFailed: print("The chart engine failed %d of %d charts; the log says why: %s" % (iFailed, iCount, sLog))
    else: print("The chart engine drew all %d kinds of chart." % iCount)
    logLine("Done: %d of %d failed" % (iFailed, iCount))
    return 1 if iFailed else 0


if __name__ == "__main__":
    try: iCode = main()
    except Exception:
        if oLog: logLine(traceback.format_exc())
        print("testChart stopped: %s; the log says why: %s" % (traceback.format_exc().strip().splitlines()[-1], sLog))
        iCode = 1
    sys.exit(iCode)
