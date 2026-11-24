// DataReport.cs -- charts of a table for sighted colleagues, drawn by Python, for Homer Tools (kit 1.269.0, 21 November 2026).
//
// Copyright 2006-2026 by Jamal Mazrui
// MIT License. See License.md, which carries the terms in full.
//
// WHY THIS EXISTS
//
// DbDo's charts were drawn by Excel through COM: a blind analyst could hand a sighted colleague a chart only if
// Microsoft Office was installed. The kit now draws them itself, with free packages, and Excel stays as the fallback
// when Python cannot run (Jamal's rule: never drop the way that relies on commercial Office when no free way works).
//
// WHAT WAS WEIGHED (DbDo's help\AnalysisPlan.md has the whole comparison)
//
// - .NET, on NuGet: ScottPlot (MIT) draws good pictures on .NET Framework 4.6.2 and later, but version 5 brings
//   SkiaSharp's native libraries, and a picture is all it makes. OxyPlot (MIT) is older and the same. Math.NET
//   Numerics (MIT) computes, and draws nothing. NPOI (Apache 2.0) writes workbooks, but its charts are line and
//   scatter only. Each would add DLLs to every app's build for one command.
// - Python, on PyPI: pandas (BSD) reads and shapes the table, matplotlib (a PSF-based license, BSD-compatible) draws
//   it to PNG and SVG, seaborn (BSD) gives it a clean statistical style and the histogram, box and fitted-line plots,
//   and openpyxl (MIT) writes an .xlsx holding a NATIVE Excel chart that a colleague can restyle -- without Excel.
//   plotly (MIT) makes interactive pages, but they need its JavaScript and are harder to read with a screen reader.
//   Every one is compatible with the Homer MIT license. The kit already finds Python (Conversion.pythonProgram).
//
// So Python it is: one run gives four files from one table, and nothing is added to an app's build.
//
// WHAT A CHART IS
//
// Four files with one base name: a PNG (for a message or a slide), an SVG (for print), an .htm page holding the
// picture with an alt text that says what it shows, that same sentence above it, and the numbers as a real table,
// and an .xlsx with the numbers and a native chart beside them, then every record used. The sentence -- the takeaway,
// "The most common Region is North, with 15 records" -- is also what the app says, so the blind user knows what the
// sighted reader will see.
//
// The colors are a validated categorical palette in a fixed order, eight at most, so a reader with a color vision
// difference can tell the series apart; more than eight records drawn by row are cut to the first eight, and said so.
//
// The script is single-quoted throughout, since it lives in a verbatim C# string. It installs a missing package with
// pip on first use and says so in its output, which the log keeps; scripts\installDataTools.cmd installs Python and
// all four packages at once.

using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace Homer {

public static partial class Conversion {

// runPythonText: the kit's Python runner, for other kit classes (DataReport). The script's output comes back in sOut.
public static bool runPythonText(string sCode, string sFirst, string sSecond, out string sOut, out string sError) {
sOut = "";
if (pythonProgram() == "") { sError = "Python is not installed; installDataTools.cmd installs it with the chart packages"; return false; }
return runPythonOutput(sCode, sFirst, sSecond, out sOut, out sError);
} // runPythonText method

} // Conversion class

public class ChartSpec {
// sKind: bar, pareto, pie, histogram, box, scatter, datechart, line, rowbar or rowline.
public string sKind = "bar";
public string sTitle = "Chart";
// sArrange: column (each column a variable, the records its values) or row (each record a series across the columns).
public string sArrange = "column";
public string sX = "";
public string sY = "";
// sLabel: the column that names each record, when records are series.
public string sLabel = "";
// sPeriod for a date chart: month, year or monthofyear.
public string sPeriod = "month";
public List<string> lsColumns = new List<string>();
} // ChartSpec class

public static class DataReport {

// chartFolder: Documents\<app> Charts, made when missing. Charts are work to hand on, so they go where documents go.
public static string chartFolder(string sApp) {
string sDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), sApp + " Charts");
try { Directory.CreateDirectory(sDir); } catch (Exception ex) { Log.warn("Could not make " + sDir + ": " + ex.Message); }
return sDir;
} // chartFolder method

// safeName: a file name from a title, its unsafe characters dropped.
public static string safeName(string sTitle) {
StringBuilder sb = new StringBuilder();
foreach (char c in sTitle) sb.Append(Array.IndexOf(Path.GetInvalidFileNameChars(), c) >= 0 ? ' ' : c);
string s = sb.ToString().Trim();
while (s.Contains("  ")) s = s.Replace("  ", " ");
if (s.Length > 80) s = s.Substring(0, 80).Trim();
return s.Length == 0 ? "Chart" : s;
} // safeName method

// csvField: one CSV field, quoted when it must be.
private static string csvField(string s) {
if (s == null) s = "";
if (s.IndexOfAny(new char[] { ',', '"', '\r', '\n' }) < 0) return s;
return "\"" + s.Replace("\"", "\"\"") + "\"";
} // csvField method

// drawChart: the table (heads and rows of text) drawn by spec into sBase.png, .svg, .htm and .xlsx. sSummary is the
// chart's takeaway sentence; sHtm the page to open. False with sError when Python, a package or the data failed.
public static bool drawChart(List<string> lsHeads, List<List<string>> llRows, ChartSpec spec, string sBase, out string sSummary, out string sHtm, out string sError) {
sSummary = ""; sHtm = ""; sError = "";
string sStem = Path.Combine(Path.GetTempPath(), "homerChart_" + Guid.NewGuid().ToString("N").Substring(0, 8));
string sCsv = sStem + ".csv", sSpec = sStem + ".spec";
try {
StringBuilder sb = new StringBuilder();
List<string> lsLine = new List<string>();
foreach (string sHead in lsHeads) lsLine.Add(csvField(sHead));
sb.Append(String.Join(",", lsLine.ToArray())).Append("\r\n");
foreach (List<string> lsRow in llRows) {
lsLine.Clear();
foreach (string sCell in lsRow) lsLine.Add(csvField(sCell));
sb.Append(String.Join(",", lsLine.ToArray())).Append("\r\n");
}
File.WriteAllText(sCsv, sb.ToString(), new UTF8Encoding(true));
StringBuilder sbSpec = new StringBuilder();
sbSpec.Append("kind=").Append(spec.sKind).Append("\n");
sbSpec.Append("title=").Append(spec.sTitle.Replace("\r", " ").Replace("\n", " ")).Append("\n");
sbSpec.Append("arrange=").Append(spec.sArrange).Append("\n");
sbSpec.Append("x=").Append(spec.sX).Append("\n");
sbSpec.Append("y=").Append(spec.sY).Append("\n");
sbSpec.Append("label=").Append(spec.sLabel).Append("\n");
sbSpec.Append("period=").Append(spec.sPeriod).Append("\n");
sbSpec.Append("columns=").Append(String.Join("\t", spec.lsColumns.ToArray())).Append("\n");
sbSpec.Append("base=").Append(sBase).Append("\n");
File.WriteAllText(sSpec, sbSpec.ToString(), new UTF8Encoding(false));
Log.info("Chart: " + spec.sKind + ", " + spec.sTitle + ", " + llRows.Count + " rows, to " + sBase);
string sOut;
bool bRan = Conversion.runPythonText(sChartScript, sCsv, sSpec, out sOut, out sError);
foreach (string sLine in sOut.Replace("\r", "").Split('\n')) {
if (sLine.Trim().Length == 0) continue;
Log.info("  chart: " + sLine);
if (sLine.StartsWith("summary=")) sSummary = sLine.Substring(8);
else if (sLine.StartsWith("htm=")) sHtm = sLine.Substring(4);
}
if (!bRan) return false;
if (sHtm.Length == 0 || !File.Exists(sHtm)) { sError = "the chart script finished without writing its page"; return false; }
return true;
}
catch (Exception ex) {
sError = ex.Message;
Log.warn("Chart failed: " + ex.Message);
return false;
}
finally {
try { File.Delete(sCsv); } catch (Exception) { }
try { File.Delete(sSpec); } catch (Exception) { }
}
} // drawChart method

// WHERE THE POINTS FALL (23 November 2026, from BrailleR's WhereXY): a scatter plot as a sighted reader takes it in --
// not point by point but by where the points cluster -- told as a grid of counts. Each column's range is split into
// four equal parts, and the lines go from the highest quarter of Y down, each giving the counts across the quarters of
// X, lowest first; then the busiest cell. Plain lines rather than a table, so a text report reads them in order.
// Empty when either column has no spread. The chart script gives the same grid on its page, as a table.
public static string whereThePointsFall(List<double> lX, List<double> lY, string sX, string sY) {
int iCount = Math.Min(lX.Count, lY.Count);
if (iCount < 4) return "";
double nXLow = double.MaxValue, nXHigh = double.MinValue, nYLow = double.MaxValue, nYHigh = double.MinValue;
for (int i = 0; i < iCount; i++) {
nXLow = Math.Min(nXLow, lX[i]); nXHigh = Math.Max(nXHigh, lX[i]);
nYLow = Math.Min(nYLow, lY[i]); nYHigh = Math.Max(nYHigh, lY[i]);
}
if (nXHigh <= nXLow || nYHigh <= nYLow) return "";
int[,] aCounts = new int[4, 4];
for (int i = 0; i < iCount; i++) aCounts[quarterOf(lY[i], nYLow, nYHigh), quarterOf(lX[i], nXLow, nXHigh)]++;
StringBuilder sb = new StringBuilder();
sb.Append("Where the points fall, with ").Append(sX).Append(" and ").Append(sY).Append(" each split into four equal ranges.\r\n");
sb.Append("Across, ").Append(sX).Append(", lowest first: ");
for (int iX = 0; iX < 4; iX++) sb.Append(iX > 0 ? "; " : "").Append(rangeText(nXLow, nXHigh, iX));
sb.Append(".\r\n");
int iBestY = 0, iBestX = 0;
for (int iY = 3; iY >= 0; iY--) {
sb.Append(sY).Append(" ").Append(rangeText(nYLow, nYHigh, iY)).Append(": ");
for (int iX = 0; iX < 4; iX++) {
sb.Append(iX > 0 ? ", " : "").Append(aCounts[iY, iX]);
if (aCounts[iY, iX] > aCounts[iBestY, iBestX]) { iBestY = iY; iBestX = iX; }
}
sb.Append("\r\n");
}
sb.Append("Most points, ").Append(aCounts[iBestY, iBestX]).Append(" of ").Append(iCount).Append(", are where ").Append(sY).Append(" is ")
.Append(rangeText(nYLow, nYHigh, iBestY)).Append(" and ").Append(sX).Append(" is ").Append(rangeText(nXLow, nXHigh, iBestX)).Append(".\r\n");
return sb.ToString();
} // whereThePointsFall method

private static int quarterOf(double n, double nLow, double nHigh) {
int i = (int) Math.Floor((n - nLow) / (nHigh - nLow) * 4);
return i < 0 ? 0 : (i > 3 ? 3 : i);
} // quarterOf method

private static string rangeText(double nLow, double nHigh, int iQuarter) {
double nStep = (nHigh - nLow) / 4;
return shortNumber(nLow + nStep * iQuarter) + " to " + shortNumber(nLow + nStep * (iQuarter + 1));
} // rangeText method

// shortNumber: a number as it is best heard: whole numbers whole, others to at most two places, no trailing zeros.
private static string shortNumber(double n) {
if (Math.Abs(n - Math.Round(n)) < 1e-9) return Math.Round(n).ToString("#,0", System.Globalization.CultureInfo.InvariantCulture);
return n.ToString("#,0.##", System.Globalization.CultureInfo.InvariantCulture);
} // shortNumber method

private const string sChartScript = @"# homerChart: a chart of a table, for colleagues who read it by sight, from the Homer kit's DataReport (21 November 2026).
# Arguments: the records as CSV (UTF-8, a header row), then a spec file of key=value lines: kind, title, arrange, x, y,
# columns (tab-separated), label, period, base. Writes base.png, base.svg, base.htm (the picture with its description
# and the data as a table) and base.xlsx (the data with a native Excel chart), and prints key=value lines for the log.
# Packages: pandas, matplotlib, seaborn and openpyxl, every one under a license compatible with MIT (BSD, PSF-based,
# BSD and MIT); a missing one is installed with pip on first use, and the run says so.
import csv, html, importlib, io, os, subprocess, sys

def needPackages():
    lMissing = []
    for sModule, sPackage in [('pandas', 'pandas'), ('matplotlib', 'matplotlib'), ('seaborn', 'seaborn'), ('openpyxl', 'openpyxl')]:
        try: importlib.import_module(sModule)
        except ImportError: lMissing.append(sPackage)
    if lMissing:
        print('installing=' + ' '.join(lMissing))
        sys.stdout.flush()
        oRun = subprocess.run([sys.executable, '-m', 'pip', 'install', '--user', '--disable-pip-version-check', '--quiet'] + lMissing, capture_output=True, text=True)
        if oRun.returncode != 0: raise SystemExit('pip could not install ' + ' '.join(lMissing) + ': ' + (oRun.stderr.strip().splitlines() or ['no message'])[-1])
        importlib.invalidate_caches()
        import site
        sUser = site.getusersitepackages()
        if sUser not in sys.path: sys.path.append(sUser)

needPackages()
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, PieChart, Reference, ScatterChart, Series

# A validated categorical palette in a fixed order (blue, orange, aqua, yellow, magenta, green, violet, red), on a near
# white surface, so a colleague with a color vision difference can still tell eight series apart.
lPalette = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948']
sSurface, sInk, sInkSoft = '#fcfcfb', '#0b0b0b', '#52514e'
iMostSeries, iMostBars = 8, 20

def readSpec(sPath):
    d = {}
    for sLine in open(sPath, encoding='utf-8-sig'):
        if '=' in sLine:
            sKey, sValue = sLine.rstrip('\r\n').split('=', 1)
            d[sKey.strip().lower()] = sValue
    return d

def number(v):
    try: return float(str(v).replace(',', '').strip())
    except ValueError: return None

def plural(i, sOne, sMany=None):
    return '%d %s' % (i, sOne if i == 1 else (sMany or sOne + 's'))

def fmt(n):
    if n is None: return ''
    if abs(n - round(n)) < 1e-9 and abs(n) < 1e15: return '{:,}'.format(int(round(n)))
    return '{:,.2f}'.format(n)

dSpec = readSpec(sys.argv[2])
sKind = dSpec.get('kind', 'bar').lower()
sTitle = dSpec.get('title', 'Chart')
sBase = dSpec['base']
sX, sY = dSpec.get('x', ''), dSpec.get('y', '')
lColumns = [s for s in dSpec.get('columns', '').split('\t') if s]
sLabel = dSpec.get('label', '')
sPeriod = dSpec.get('period', 'month').lower()
dfAll = pd.read_csv(sys.argv[1], dtype=str, keep_default_na=False, encoding='utf-8-sig')
iRecords = len(dfAll)

sns.set_theme(style='whitegrid', rc={'axes.facecolor': sSurface, 'figure.facecolor': sSurface, 'text.color': sInk,
    'axes.labelcolor': sInkSoft, 'xtick.color': sInkSoft, 'ytick.color': sInkSoft, 'grid.color': '#e6e5e1',
    'axes.edgecolor': '#d0cfca', 'font.size': 11})
oFig, oAx = plt.subplots(figsize=(10, 6))
lHeads, lRows = [], []          # the chart's own table, for the page and the workbook
sSummary, sNote, sNative = '', '', 'bar'

def counts(sColumn):
    oSeries = dfAll[sColumn].map(lambda s: s.strip() or 'blank')
    return oSeries.value_counts()

def foldOther(oCounts):
    if len(oCounts) <= iMostBars: return oCounts
    oTop = oCounts.iloc[:iMostBars - 1].copy()
    oTop['Other (' + plural(len(oCounts) - iMostBars + 1, 'value') + ')'] = oCounts.iloc[iMostBars - 1:].sum()
    return oTop

def recordNames(df):
    if sLabel and sLabel in df.columns: return [str(s) or 'blank' for s in df[sLabel]]
    return ['Record %d' % (i + 1) for i in range(len(df))]

if sKind in ('bar', 'pareto'):
    oCounts = foldOther(counts(sX))
    iTotal = int(oCounts.sum())
    lValues, lCounts = list(oCounts.index), [int(i) for i in oCounts.values]
    oAx.barh(lValues[::-1], lCounts[::-1], color=lPalette[0], height=0.7)
    oAx.set_xlabel('Records')
    oAx.set_ylabel(sX)
    iRunning, iCover = 0, 0
    lHeads = [sX, 'Records', 'Percent', 'Running percent']
    for sValue, iCount in zip(lValues, lCounts):
        iRunning += iCount
        if iRunning * 100.0 / iTotal < 80 or iCover == 0: iCover += 1
        lRows.append([sValue, iCount, round(iCount * 100.0 / iTotal, 1), round(iRunning * 100.0 / iTotal, 1)])
    if sKind == 'pareto':
        for iAt, (iCount, lRow) in enumerate(zip(lCounts[::-1], lRows[::-1])):
            oAx.text(iCount, iAt, '  %s%% so far' % lRow[3], va='center', color=sInkSoft, fontsize=9)
    sSummary = 'The most common %s is %s, with %s (%s%% of %s).' % (sX, lValues[0], plural(lCounts[0], 'record'), lRows[0][2], plural(iTotal, 'record'))
    if len(lValues) > 3: sSummary += ' The top %s cover%s 80%% of records.' % (plural(iCover, 'value'), 's' if iCover == 1 else '')
elif sKind == 'pie':
    oCounts = counts(sX)
    if len(oCounts) > 5: oCounts = foldOther(oCounts).iloc[:5]
    iTotal = int(oCounts.sum())
    lValues, lCounts = list(oCounts.index), [int(i) for i in oCounts.values]
    oAx.pie(lCounts, labels=['%s, %d%%' % (s, round(i * 100.0 / iTotal)) for s, i in zip(lValues, lCounts)], colors=lPalette[:len(lCounts)],
        startangle=90, counterclock=False, wedgeprops={'edgecolor': sSurface, 'linewidth': 2})
    oAx.axis('equal')
    oAx.grid(False)
    lHeads = [sX, 'Records', 'Percent']
    lRows = [[s, i, round(i * 100.0 / iTotal, 1)] for s, i in zip(lValues, lCounts)]
    sSummary = 'Of %s, %s are %s (%s%%).' % (plural(iTotal, 'record'), lCounts[0], lValues[0], lRows[0][2])
    sNative = 'pie'
elif sKind == 'histogram':
    lNumbers = [n for n in (number(v) for v in dfAll[sX]) if n is not None]
    if not lNumbers: raise SystemExit('No record holds a number in ' + sX)
    oSeries = pd.Series(lNumbers)
    sns.histplot(oSeries, ax=oAx, color=lPalette[0], edgecolor=sSurface, linewidth=2, bins='auto')
    oAx.set_xlabel(sX)
    oAx.set_ylabel('Records')
    lHeads = ['From', 'To', 'Records']
    for oPatch in oAx.patches:
        lRows.append([round(oPatch.get_x(), 4), round(oPatch.get_x() + oPatch.get_width(), 4), int(oPatch.get_height())])
    sSummary = '%s of %s run from %s to %s; the middle value is %s and the average %s.' % (plural(len(lNumbers), 'number'), sX,
        fmt(oSeries.min()), fmt(oSeries.max()), fmt(oSeries.median()), fmt(oSeries.mean()))
    lPeak = max(lRows, key=lambda l: l[2])
    sSummary += ' Most fall between %s and %s.' % (fmt(lPeak[0]), fmt(lPeak[1]))
elif sKind == 'box':
    lUse = lColumns or [sX]
    dNumbers = {}
    for sColumn in lUse:
        lNumbers = [n for n in (number(v) for v in dfAll[sColumn]) if n is not None]
        if lNumbers: dNumbers[sColumn] = lNumbers
    if not dNumbers: raise SystemExit('No shown column holds numbers')
    dfLong = pd.DataFrame([(s, n) for s, l in dNumbers.items() for n in l], columns=['Column', 'Value'])
    sns.boxplot(data=dfLong, x='Value', y='Column', ax=oAx, color=lPalette[0], width=0.5, fliersize=4)
    oAx.set_ylabel('')
    lHeads = ['Column', 'Count', 'Smallest', 'Lower quarter', 'Middle', 'Upper quarter', 'Largest']
    for sColumn, l in dNumbers.items():
        o = pd.Series(l)
        lRows.append([sColumn, len(l), o.min(), o.quantile(0.25), o.median(), o.quantile(0.75), o.max()])
    lWide = max(lRows, key=lambda l: l[5] - l[3])
    sSummary = 'The middle half of %s runs from %s to %s, around a middle value of %s.' % (lWide[0], fmt(lWide[3]), fmt(lWide[5]), fmt(lWide[4]))
    if len(lRows) > 1: sSummary = 'Of %s, %s spreads widest. ' % (plural(len(lRows), 'column'), lWide[0]) + sSummary
    sNative = ''
    sNote = 'Excel draws no box and whisker chart from a file, so the workbook holds the five numbers of each column.'
elif sKind == 'scatter':
    lPairs = [(number(a), number(b)) for a, b in zip(dfAll[sX], dfAll[sY])]
    lPairs = [(a, b) for a, b in lPairs if a is not None and b is not None]
    if len(lPairs) < 2: raise SystemExit('Fewer than two records hold numbers in both ' + sX + ' and ' + sY)
    dfPairs = pd.DataFrame(lPairs, columns=[sX, sY])
    sns.regplot(data=dfPairs, x=sX, y=sY, ax=oAx, color=lPalette[0], scatter_kws={'s': 40, 'edgecolors': sSurface, 'linewidths': 1}, line_kws={'color': lPalette[1], 'linewidth': 2}, ci=None)
    nR = dfPairs[sX].corr(dfPairs[sY])
    lHeads = [sX, sY]
    lRows = [list(l) for l in lPairs]
    sStrength = 'strongly' if abs(nR) >= 0.7 else ('somewhat' if abs(nR) >= 0.4 else 'hardly')
    sSummary = 'Across %s, %s and %s %s %s together (correlation %s).' % (plural(len(lPairs), 'record'), sX, sY, sStrength,
        'rise' if nR >= 0 else 'move oppositely', '{:.2f}'.format(nR))
    sNative = 'scatter'
elif sKind == 'datechart':
    oDates = pd.to_datetime(dfAll[sX].str.strip(), errors='coerce').dropna()
    if oDates.empty: raise SystemExit('No record holds a date in ' + sX)
    if sPeriod == 'year': oKeys = oDates.dt.strftime('%Y')
    elif sPeriod == 'monthofyear': oKeys = oDates.dt.strftime('%m %b')
    else: oKeys = oDates.dt.strftime('%Y-%m')
    oCounts = oKeys.value_counts().sort_index()
    oAx.plot(list(oCounts.index), list(oCounts.values), color=lPalette[0], linewidth=2, marker='o', markersize=6)
    oAx.set_xlabel(sX + ', by ' + {'year': 'year', 'monthofyear': 'month of the year'}.get(sPeriod, 'month'))
    oAx.set_ylabel('Records')
    if len(oCounts) > 12: plt.setp(oAx.get_xticklabels(), rotation=45, ha='right')
    lHeads = ['Period', 'Records']
    lRows = [[s, int(i)] for s, i in oCounts.items()]
    lBusy = max(lRows, key=lambda l: l[1])
    sSummary = '%s of %s run from %s to %s; the busiest period is %s, with %s.' % (plural(len(oDates), 'date'), sX, lRows[0][0], lRows[-1][0], lBusy[0], plural(lBusy[1], 'record'))
    sNative = 'line'
elif sKind in ('line', 'rowbar', 'rowline'):
    lUse = [s for s in (lColumns or [sX]) if s in dfAll.columns]
    bByRow = dSpec.get('arrange', 'column').lower() == 'row' or sKind in ('rowbar', 'rowline')
    if bByRow:
        # BY ROW: each record is a series, each shown column a point along it (months across, say).
        dfUse = dfAll.head(iMostSeries)
        lNames = recordNames(dfUse)
        lUse = [s for s in lUse if s != sLabel and any(number(v) is not None for v in dfUse[s])]
        if not lUse: raise SystemExit('No shown column holds numbers for these records')
        lHeads = ['Record'] + lUse
        for sName, (_, oRow) in zip(lNames, dfUse.iterrows()): lRows.append([sName] + [number(oRow[s]) for s in lUse])
        if sKind == 'rowbar':
            nWidth = 0.8 / len(lRows)
            for iAt, lRow in enumerate(lRows):
                oAx.bar([i + iAt * nWidth - 0.4 + nWidth / 2 for i in range(len(lUse))], [n or 0 for n in lRow[1:]], width=nWidth * 0.92, color=lPalette[iAt], label=lRow[0])
            oAx.set_xticks(range(len(lUse)))
            oAx.set_xticklabels(lUse)
            sNative = 'bar'
        else:
            for iAt, lRow in enumerate(lRows): oAx.plot(lUse, lRow[1:], color=lPalette[iAt], linewidth=2, marker='o', markersize=6, label=lRow[0])
            sNative = 'line'
        if len(lRows) > 1: oAx.legend(frameon=False, loc='upper left', bbox_to_anchor=(1.01, 1))
        if len(lUse) > 8: plt.setp(oAx.get_xticklabels(), rotation=45, ha='right')
        lFirst = lRows[0]
        lPairs = [(s, n) for s, n in zip(lUse, lFirst[1:]) if n is not None]
        sHigh = max(lPairs, key=lambda l: l[1])
        sLow = min(lPairs, key=lambda l: l[1])
        sSummary = 'For %s, %s is highest at %s and %s lowest at %s.' % (lFirst[0], sHigh[0], fmt(sHigh[1]), sLow[0], fmt(sLow[1]))
        if len(lRows) > 1: sSummary = 'Compares %s across %s. ' % (plural(len(lRows), 'record'), plural(len(lUse), 'column')) + sSummary
        if len(dfAll) > iMostSeries: sNote = 'Only the first %d of %s are drawn, since more lines cannot be told apart.' % (iMostSeries, plural(len(dfAll), 'record'))
    else:
        # BY COLUMN: each number column a series, the records along the bottom in the grid's order.
        lUse = [s for s in lUse if s != sLabel and any(number(v) is not None for v in dfAll[s])][:iMostSeries]
        if not lUse: raise SystemExit('No shown column holds numbers')
        lNames = recordNames(dfAll)
        lHeads = ['Record'] + lUse
        for iAt, sName in enumerate(lNames): lRows.append([sName] + [number(dfAll.iloc[iAt][s]) for s in lUse])
        for iAt, sColumn in enumerate(lUse): oAx.plot(range(len(lNames)), [l[iAt + 1] for l in lRows], color=lPalette[iAt], linewidth=2, label=sColumn)
        oAx.set_xlabel('Records, in the order of the grid')
        if len(lNames) <= 20:
            oAx.set_xticks(range(len(lNames)))
            oAx.set_xticklabels(lNames, rotation=45, ha='right')
        if len(lUse) > 1: oAx.legend(frameon=False, loc='upper left', bbox_to_anchor=(1.01, 1))
        lFirst = [n for n in (l[1] for l in lRows) if n is not None]
        sSummary = '%s from %s to %s over %s.' % (lUse[0], fmt(lFirst[0]), fmt(lFirst[-1]), plural(len(lRows), 'record'))
        sNative = 'line'
else:
    raise SystemExit('Unknown chart kind: ' + sKind)

# WHAT THE CHART SHOWS (23 November 2026, from BrailleR's VI descriptions): the kind, each number axis with its label
# and the values marked on it, then what is drawn, in the words that fit the kind -- a histogram's bars, each box of a
# whisker plot with its middle, box, whiskers and outliers, a scatter plot's points as a grid of where they fall. The
# takeaway says what matters; this says what is there, so a blind reader knows what a sighted one is looking at.
def tickWord(n):
    s = fmt(n)
    return s.rstrip('0').rstrip('.') if '.' in s else s

def axisWords(sWhich):
    nLow, nHigh = oAx.get_xlim() if sWhich == 'x' else oAx.get_ylim()
    lTicks = [t for t in (oAx.get_xticks() if sWhich == 'x' else oAx.get_yticks()) if min(nLow, nHigh) - 1e-9 <= t <= max(nLow, nHigh) + 1e-9]
    sLabel = (oAx.get_xlabel() if sWhich == 'x' else oAx.get_ylabel()) or 'the values'
    if sLabel == 'Value': sLabel = 'the values'
    return '%s, marked at %s' % (sLabel, ', '.join(tickWord(t) for t in lTicks))

lDescribe, lGridHeads, lGridRows = [], [], []
if sKind in ('bar', 'pareto'):
    lDescribe.append('A bar chart of %s, one bar for each value of %s, the longest at the top. The bars run along %s.' % (plural(len(lRows), 'bar'), sX, axisWords('x')))
elif sKind == 'pie':
    lDescribe.append('A pie chart of %s, the largest first, going clockwise from the top.' % plural(len(lRows), 'slice'))
elif sKind == 'histogram':
    nWidth = lRows[0][1] - lRows[0][0] if lRows else 0
    lDescribe.append('A histogram of %s of equal width, %s each, from %s to %s.' % (plural(len(lRows), 'bar'), tickWord(nWidth), tickWord(lRows[0][0]), tickWord(lRows[-1][1])))
    lDescribe.append('Along the bottom: %s. Up the side: %s.' % (axisWords('x'), axisWords('y')))
elif sKind == 'box':
    lDescribe.append('A whisker plot of %s, one box each. Along the bottom: %s.' % (plural(len(dNumbers), 'column'), axisWords('x')))
    for sColumn, l in dNumbers.items():
        o = pd.Series(l)
        nQ1, nQ3 = o.quantile(0.25), o.quantile(0.75)
        nReach = 1.5 * (nQ3 - nQ1)
        lIn = [n for n in l if nQ1 - nReach <= n <= nQ3 + nReach]
        iOut = len(l) - len(lIn)
        lDescribe.append('%s: the middle value is %s; the box runs from %s to %s; the whiskers reach %s and %s; %s beyond them.' % (sColumn,
            tickWord(o.median()), tickWord(nQ1), tickWord(nQ3), tickWord(min(lIn)), tickWord(max(lIn)), ('1 point lies' if iOut == 1 else '%d points lie' % iOut) if iOut else 'no point lies'))
elif sKind == 'scatter':
    lDescribe.append('A scatter plot of %s, with the straight line that fits them best. Along the bottom: %s. Up the side: %s.' % (plural(len(lPairs), 'point'), axisWords('x'), axisWords('y')))
    lXs, lYs = [a for a, b in lPairs], [b for a, b in lPairs]
    nXLow, nXHigh, nYLow, nYHigh = min(lXs), max(lXs), min(lYs), max(lYs)
    if nXHigh > nXLow and nYHigh > nYLow:
        def quarter(n, nLow, nHigh): return min(3, max(0, int((n - nLow) / (nHigh - nLow) * 4)))
        def span(nLow, nHigh, i): return tickWord(nLow + (nHigh - nLow) * i / 4) + ' to ' + tickWord(nLow + (nHigh - nLow) * (i + 1) / 4)
        aGrid = [[0] * 4 for i in range(4)]
        for a, b in lPairs: aGrid[quarter(b, nYLow, nYHigh)][quarter(a, nXLow, nXHigh)] += 1
        lGridHeads = [sY + ' \\ ' + sX] + [span(nXLow, nXHigh, i) for i in range(4)]
        lGridRows = [[span(nYLow, nYHigh, iY)] + aGrid[iY] for iY in range(3, -1, -1)]
        iBestY, iBestX = max(((y, x) for y in range(4) for x in range(4)), key=lambda t: aGrid[t[0]][t[1]])
        lDescribe.append('Most points, %d of %d, are where %s is %s and %s is %s; the table after the chart counts the points in each of sixteen parts.' % (
            aGrid[iBestY][iBestX], len(lPairs), sY, span(nYLow, nYHigh, iBestY), sX, span(nXLow, nXHigh, iBestX)))
elif sKind == 'datechart':
    lDescribe.append('A line of %s, one for each period, from %s to %s. Up the side: %s.' % (plural(len(lRows), 'point'), lRows[0][0], lRows[-1][0], axisWords('y')))
elif sKind in ('line', 'rowbar', 'rowline'):
    sShape = 'bar chart' if sKind == 'rowbar' else 'line chart'
    iSeries = len(lRows) if sKind in ('rowbar', 'rowline') or lHeads[0] == 'Record' and dSpec.get('arrange', 'column').lower() == 'row' else len(lHeads) - 1
    lDescribe.append('A %s of %s. Up the side: %s.' % (sShape, plural(iSeries, 'series', 'series'), axisWords('y')))
sDescribe = ' '.join(lDescribe)

oAx.set_title(sTitle, loc='left', fontsize=14, color=sInk, pad=12)
sns.despine(ax=oAx, left=True)
oFig.tight_layout()
oFig.savefig(sBase + '.png', dpi=150)
oFig.savefig(sBase + '.svg')
plt.close(oFig)

# The workbook: the chart's table with a native chart beside it, then every record used.
oBook = Workbook()
oSheet = oBook.active
oSheet.title = 'Chart'
oSheet.append(lHeads)
for lRow in lRows: oSheet.append(lRow)
iLast = len(lRows) + 1
if sNative and lRows:
    if sNative == 'pie':
        oChart = PieChart()
        oChart.add_data(Reference(oSheet, min_col=2, min_row=1, max_row=iLast), titles_from_data=True)
        oChart.set_categories(Reference(oSheet, min_col=1, min_row=2, max_row=iLast))
    elif sNative == 'scatter':
        oChart = ScatterChart()
        oChart.style = 13
        oSeries = Series(Reference(oSheet, min_col=2, min_row=2, max_row=iLast), Reference(oSheet, min_col=1, min_row=2, max_row=iLast), title=sY)
        oSeries.marker.symbol = 'circle'
        oSeries.graphicalProperties.line.noFill = True
        oChart.series.append(oSeries)
        oChart.x_axis.title = sX
        oChart.y_axis.title = sY
    else:
        oChart = LineChart() if sNative == 'line' else BarChart()
        bRecordSeries = sKind in ('rowbar', 'rowline') or (sKind == 'line' and lHeads[0] == 'Record' and dSpec.get('arrange', 'column').lower() == 'row')
        if bRecordSeries:
            # Each record a series: the records are the rows, so the chart reads them across.
            for iRow in range(2, iLast + 1):
                oSeries = Series(Reference(oSheet, min_col=2, max_col=len(lHeads), min_row=iRow), title=str(oSheet.cell(iRow, 1).value))
                oChart.series.append(oSeries)
            oChart.set_categories(Reference(oSheet, min_col=2, max_col=len(lHeads), min_row=1))
        else:
            iDataColumns = 1 if sKind in ('bar', 'pareto', 'histogram', 'datechart') else len(lHeads) - 1
            iFirstData = 3 if sKind == 'histogram' else 2
            oChart.add_data(Reference(oSheet, min_col=iFirstData, max_col=iFirstData + iDataColumns - 1, min_row=1, max_row=iLast), titles_from_data=True)
            oChart.set_categories(Reference(oSheet, min_col=1, min_row=2, max_row=iLast))
        if sNative == 'bar' and sKind in ('bar', 'pareto'): oChart.type = 'bar'
    oChart.title = sTitle
    oChart.width, oChart.height = 22, 12
    oSheet.add_chart(oChart, 'H2')
oRecords = oBook.create_sheet('Records')
oRecords.append(list(dfAll.columns))
for lRow in dfAll.itertuples(index=False): oRecords.append([number(v) if number(v) is not None else v for v in lRow])
oBook.save(sBase + '.xlsx')

# The page: what the chart shows in words, the picture, and the same numbers as a table.
sName = os.path.basename(sBase)
lPage = ['<!DOCTYPE html>', '<html lang=\'en\'>', '<head>', '<meta charset=\'utf-8\'>', '<title>' + html.escape(sTitle) + '</title>',
    '<style>body{font-family:Segoe UI,Arial,sans-serif;max-width:60rem;margin:2rem auto;padding:0 1rem;color:#0b0b0b;background:#fcfcfb}'
    'img{max-width:100%;height:auto}table{border-collapse:collapse}th,td{border:1px solid #d0cfca;padding:.25rem .6rem;text-align:left}'
    'td.n{text-align:right}caption{text-align:left;font-weight:bold;margin-bottom:.4rem}</style>', '</head>', '<body>', '<main>',
    '<h1>' + html.escape(sTitle) + '</h1>', '<p>' + html.escape(sSummary) + '</p>']
if sNote: lPage.append('<p>' + html.escape(sNote) + '</p>')
lPage += ['<figure>', '<img src=\'' + html.escape(sName) + '.png\' alt=\'' + html.escape(sTitle + '. ' + sSummary + ' The table below has the numbers.', quote=True) + '\'>',
    '<figcaption>' + html.escape(sTitle) + ', drawn from ' + plural(iRecords, 'record') + '. Also as <a href=\'' + html.escape(sName) + '.svg\'>a scalable picture</a> and <a href=\'' + html.escape(sName) + '.xlsx\'>an Excel workbook with the chart</a>.</figcaption>',
    '</figure>']
if sDescribe: lPage += ['<h2>What the chart shows</h2>', '<p>' + html.escape(sDescribe) + '</p>']
if lGridRows:
    lPage += ['<table>', '<caption>Where the points fall: ' + html.escape(sY) + ' down the side, highest first; ' + html.escape(sX) + ' across, lowest first</caption>',
        '<thead><tr>' + ''.join('<th scope=\'col\'>' + html.escape(str(s)) + '</th>' for s in lGridHeads) + '</tr></thead>', '<tbody>']
    for lRow in lGridRows: lPage.append('<tr><th scope=\'row\'>' + html.escape(lRow[0]) + '</th>' + ''.join('<td class=\'n\'>' + str(i) + '</td>' for i in lRow[1:]) + '</tr>')
    lPage += ['</tbody>', '</table>']
lPage += ['<h2>The numbers</h2>', '<table>', '<caption>The numbers in the chart</caption>', '<thead><tr>' + ''.join('<th scope=\'col\'>' + html.escape(str(s)) + '</th>' for s in lHeads) + '</tr></thead>', '<tbody>']
for lRow in lRows:
    lCells = []
    for iAt, v in enumerate(lRow):
        if iAt == 0: lCells.append('<th scope=\'row\'>' + html.escape(str(v)) + '</th>')
        elif isinstance(v, (int, float)): lCells.append('<td class=\'n\'>' + html.escape(fmt(v)) + '</td>')
        else: lCells.append('<td>' + html.escape('' if v is None else str(v)) + '</td>')
    lPage.append('<tr>' + ''.join(lCells) + '</tr>')
lPage += ['</tbody>', '</table>', '</main>', '</body>', '</html>']
open(sBase + '.htm', 'w', encoding='utf-8', newline='\r\n').write('\n'.join(lPage) + '\n')
print('summary=' + sSummary)
if sDescribe: print('description=' + sDescribe)
if sNote: print('note=' + sNote)
for sExtension in ('htm', 'png', 'svg', 'xlsx'): print(sExtension + '=' + sBase + '.' + sExtension)
";

} // DataReport class

} // namespace Homer
