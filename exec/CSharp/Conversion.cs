// Conversion.cs -- converting a file from one type to another, for every Homer app.
//
// ONE PLACE FOR EVERY CONVERSION (kit 1.74.0). FileDir, EdSharp, DbDo, HomerView,
// HomerScribe and 2htm each carried their own Pandoc finder, their own 2htm calls
// and their own Office COM code. This class is the one copy. FileDir's Convert.cs
// is its starting point; it moved here, renamed so it can never shadow .NET's own
// System.Convert inside the Homer namespace.
//
// THE ROUTE COMES FROM exec\conversions.inix, the table Python's conversion.py
// reads too. Each section is named <source>2<target> -- pdf2txt, pdf2docx,
// docx2md -- with its ways best first. Both the source and the target decide:
// pdf2txt wants speed and reads only the text layer; pdf2docx wants structure.
//
// INTERNAL OR EXTERNAL, JUDGED PER ENGINE:
//   copy, zipxml, table   internal: no program starts, so they are the quickest
//   pdftext               PdfPig in-process when it is beside the program; else
//                         PyMuPDF's plain text through Python
//   pdfstructure          HomerScribe's reader, PdfReader.cs (kit 1.75.0), where an
//                         app compiles it with ConversionPdf.cs; else pymupdf4llm
//   ocr                   the same reader with Tesseract, for scanned pages
//   pandoc                Pandoc, which no internal code could match
//   officecom             Microsoft Office: the LAST RESORT, used only when nothing
//                         approved will do, with an Alert box when it is missing
//
// FOR A DIALOG OR A BATCH, call these rather than reading conversions.inix (1.80.0):
//   targetLabelsFor(path, out exts)  the targets for a file, as labels a person reads
//                                    ("Markdown (.md)") with their extensions alongside:
//                                    the list a target picker shows
//   targetsFor(path)                 the same as [label, extension] pairs
//   hasAnyRoute(path)                whether a file can be converted at all
//   hasRoute(source, target)         whether one particular conversion exists
//   convert(source, target, out error)  convert one file: the one technique every app uses
//   typeOf(pathOrType)               the type a path or a name stands for (html -> htm)
// ChatGPT's BatCon parsed conversions.inix with a regular expression to find targets,
// because this list was not here to find; a picker built that way shows bare extensions.
//
// EVERY CONVERSION IS LOGGED WITH ITS ROUTE AND ITS TIME in milliseconds, so the
// order of the ways is tuned from measurements, not guesses.
//
// REQUIRES: Log.cs, Paths.cs, Table.cs, Util.cs. Media conversions (audio, video,
// pictures) are in ConversionMedia.cs, for apps that compile Media.cs. The PDF
// reader is in PdfReader.cs and ConversionPdf.cs, for apps that reference PdfPig.
//
// Copyright 2006-2026 by Jamal Mazrui. MIT License.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Text;
using System.Text.RegularExpressions;
using System.Windows.Forms;

namespace Homer {

public static partial class Conversion {

// ------- the routing table -------

public const string sTableName = "conversions.inix";
private static Dictionary<string, List<string>> dWays = null;
private static string sTableFound = "";

// tablePath: beside the program, in the exec folder beside it, or in the
// development kit, so an installed app and a build in the kit both find it.
public static string tablePath() {
List<string> lsFolders = new List<string>();
string sExeDir = AppDomain.CurrentDomain.BaseDirectory;
lsFolders.Add(sExeDir);
lsFolders.Add(Path.Combine(sExeDir, "exec"));
try { lsFolders.Add(Path.Combine(Path.GetDirectoryName(sExeDir.TrimEnd('\\')), "exec")); } catch (Exception) { }
string sKit = Environment.GetEnvironmentVariable("HomerDev");
if (!String.IsNullOrEmpty(sKit)) lsFolders.Add(Path.Combine(sKit, "exec"));
foreach (string sFolder in lsFolders) {
string sPath = Path.Combine(sFolder, sTableName);
if (File.Exists(sPath)) return sPath;
}
return "";
} // tablePath method

private static bool loadTable() {
if (dWays != null) return true;
dWays = new Dictionary<string, List<string>>(StringComparer.OrdinalIgnoreCase);
sTableFound = tablePath();
if (sTableFound == "") {
Log.warn("Conversion: " + sTableName + " was not found beside the program, so no route can be planned");
return false;
}
string sSection = "";
foreach (string sRaw in File.ReadAllLines(sTableFound, Encoding.UTF8)) {
string sLine = sRaw.Trim();
if (sLine.Length == 0 || sLine.StartsWith(";") || sLine.StartsWith("#")) continue;
if (sLine.StartsWith("[") && sLine.EndsWith("]")) { sSection = sLine.Substring(1, sLine.Length - 2).Trim(); continue; }
int iEqual = sLine.IndexOf('=');
if (iEqual < 0 || sSection == "") continue;
if (String.Compare(sLine.Substring(0, iEqual).Trim(), "ways", true) != 0) continue;
List<string> lsWays = new List<string>();
foreach (string sWay in sLine.Substring(iEqual + 1).Split(','))
if (sWay.Trim().Length > 0) lsWays.Add(sWay.Trim().ToLowerInvariant());
dWays[sSection] = lsWays;
}
Log.info("Conversion: " + dWays.Count + " conversions read from " + sTableFound);
return true;
} // loadTable method

// routeName: the pattern every Homer conversion is named by, e.g. pdf2txt.
public static string routeName(string sSource, string sTarget) {
return typeOf(sSource) + "2" + typeOf(sTarget);
} // routeName method

public static string typeOf(string sPathOrType) {
string sType = sPathOrType.IndexOf('.') >= 0 ? Path.GetExtension(sPathOrType) : sPathOrType;
sType = sType.TrimStart('.').ToLowerInvariant();
if (sType == "html") return "htm";
if (sType == "markdown") return "md";
return sType;
} // typeOf method

public static List<string> waysFor(string sRoute) {
loadTable();
List<string> lsWays;
if (dWays.TryGetValue(sRoute, out lsWays)) return lsWays;
return new List<string>();
} // waysFor method

public static bool hasRoute(string sSource, string sTarget) {
return waysFor(routeName(sSource, sTarget)).Count > 0;
} // hasRoute method

// ------- converting -------

// ONE CONVERSION TECHNIQUE (kit 1.80.2, Jamal's rule of 19 October 2026): converting between any
// two formats is done one way in every Homer app, and this is it. convert takes, in order:
//   1. media -- audio, video and pictures -- in an app that compiles ConversionMedia;
//   2. the route table, exec\conversions.inix, each route's ways best first;
//   3. for a type the table does not name, its text, then Pandoc to the target.
// convertAny and convertFile are the same function under older names, kept so callers compile:
// convertAny had this order, convertFile was Pandoc alone, and DbDo, EdSharp, FileDir and BatCon
// each called a different one. bQuick passes over engines that can take minutes (ocr), for a
// key that must answer at once.
public static bool convert(string sSource, string sTarget, out string sError) {
return convert(sSource, sTarget, false, out sError);
} // convert method

public static bool convert(string sSource, string sTarget, bool bQuick, out string sError) {
sError = "";
if (!File.Exists(sSource)) { sError = "the file was not found"; return false; }
bool bHandled = false, bMade = false;
mediaConvert(sSource, sTarget, ref bHandled, ref bMade, ref sError);
if (bHandled) return bMade;
if (hasRoute(sSource, sTarget)) {
if (convertByRoute(sSource, sTarget, bQuick, out sError)) return true;
string sDirect = sError;
string sHub = hubFor(sSource, sTarget);
if (sHub == "") return false;
Log.info("Conversion " + routeName(sSource, sTarget) + ": its own route could not, so through " + sHub + " -- " + sDirect);
if (convertByHub(sSource, sTarget, sHub, bQuick, out sError)) return true;
sError = sDirect + "; and through " + sHub + ": " + sError;
return false;
}
{
string sHub = hubFor(sSource, sTarget);
if (sHub != "") return convertByHub(sSource, sTarget, sHub, bQuick, out sError);
}
// A type the table does not name: its text, then Pandoc to the target.
string sText = toText(sSource, out sError);
if (sText.Length == 0) {
if (sError == "") sError = "no way to convert " + typeOf(sSource) + " to " + typeOf(sTarget) + " is known (" + routeName(sSource, sTarget) + ")";
return false;
}
string sMd = tempPath(sSource, ".md");
try {
File.WriteAllText(sMd, sText, new UTF8Encoding(true));
if (typeOf(sTarget) == "md" || typeOf(sTarget) == "txt") { File.Copy(sMd, sTarget, true); return true; }
return pandoc(sMd, sTarget, out sError);
}
finally { try { File.Delete(sMd); } catch (Exception) { } }
} // convert method

// THROUGH MARKDOWN (kit 1.90.0, Jamal's rule of 24 October 2026): every Homer app converts between
// ANY two of the types the kit knows, PDF included, with the same code. The table names 104 pairs
// and cannot name them all, so a pair it does not name -- or whose every way fails, as docx2pdf
// does without Office -- goes in two of the table's own steps through a hub: Markdown, which
// nearly every type reads into and writes out of, else a web page (json2pdf: json2htm, htm2pdf).
// Each step is an ordinary route, so each keeps its best-first ways, its logging, and its own
// finishing; nothing here is a second way of converting.
private static readonly string[] aHubs = { "md", "htm" };

// hubFor: the hub a pair would go through, or "" when the pair cannot be made that way.
public static string hubFor(string sSource, string sTarget) {
string sFrom = typeOf(sSource), sTo = typeOf(sTarget);
if (sFrom == "" || sTo == "" || sFrom == sTo) return "";
foreach (string sHub in aHubs) {
if (sFrom == sHub || sTo == sHub) continue;
if (hasRoute(sFrom, sHub) && hasRoute(sHub, sTo)) return sHub;
}
return "";
} // hubFor method

private static HashSet<string> hsIntermediates = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

private static bool convertByHub(string sSource, string sTarget, string sHub, bool bQuick, out string sError) {
string sMiddle = tempPath(sSource, "." + sHub);
hsIntermediates.Add(Path.GetFullPath(sMiddle));
try {
if (!convertByRoute(sSource, sMiddle, bQuick, out sError)) { sError = routeName(sSource, sHub) + ": " + sError; return false; }
if (!convertByRoute(sMiddle, sTarget, bQuick, out sError)) { sError = routeName(sHub, sTarget) + ": " + sError; return false; }
Log.info("Conversion " + routeName(sSource, sTarget) + " made through " + sHub + ", " + Path.GetFileName(sSource));
return true;
}
finally {
hsIntermediates.Remove(Path.GetFullPath(sMiddle));
try { if (File.Exists(sMiddle)) File.Delete(sMiddle); } catch (Exception) { }
}
} // convertByHub method

// convertByRoute: the route table's ways for this pair, best first, the first whose engines are
// all present; the middle step of convert.
private static bool convertByRoute(string sSource, string sTarget, bool bQuick, out string sError) {
sError = "";
if (!File.Exists(sSource)) { sError = "the file was not found"; return false; }
string sRoute = routeName(sSource, sTarget);
List<string> lsWays = waysFor(sRoute);
if (lsWays.Count == 0) {
sError = sTableFound == "" ? sTableName + " is missing beside the program, so nothing can be converted; reinstall the program"
: "no way to convert " + typeOf(sSource) + " to " + typeOf(sTarget) + " is known (" + sRoute + ")";
return false;
}
List<string> lsWhy = new List<string>();
foreach (string sWay in lsWays) {
string[] aSteps = sWay.Split('>');
string sMissing = "";
foreach (string sStep in aSteps) {
string sEngine = sStep.Split(':')[0].Trim();
if (bQuick && sEngine == "ocr") { sMissing = "ocr is too slow for a quick read"; break; }
string sWhy = engineMissing(sEngine, sSource);
if (sWhy != "") { sMissing = sWhy; break; }
}
if (sMissing != "") { lsWhy.Add(sWay + ": " + sMissing); continue; }
Stopwatch oClock = Stopwatch.StartNew();
string sStepError;
bool bMade = runWay(aSteps, sSource, sTarget, out sStepError);
oClock.Stop();
Log.info("Conversion " + sRoute + " by " + sWay + ": " + (bMade ? "made" : "failed") + " in " + oClock.ElapsedMilliseconds + " ms, " + Path.GetFileName(sSource)
+ (sStepError != "" ? " -- " + sStepError : ""));
if (bMade) {
// EVERY WEB PAGE IN THE HOMER FORM (1.87.1): a page made by any way but the page and json
// engines, which write it already, is finished as 2htm finishes its pages -- one H1, main
// labelled by it, the base stylesheet -- when the app compiles ConversionPage.cs.
if (typeOf(sTarget) == "htm" && !sWay.TrimEnd().EndsWith("page") && !sWay.TrimEnd().EndsWith("json")) {
string sPageError = "";
pageFinish(sTarget, ref sPageError);
if (sPageError != "") Log.info("Page form not applied to " + Path.GetFileName(sTarget) + ": " + sPageError);
}
// TEXT IN THE HOMER ENCODING (kit 1.80.0, from ChatGPT's BatCon work): whatever an engine wrote,
// a text result ends as UTF-8 with a byte order mark and CRLF, as every Homer text file is.
string sMadeType = typeOf(sTarget);
if (Array.IndexOf(new string[] {"csv", "htm", "inix", "md", "tsv", "txt"}, sMadeType) >= 0) {
string sMadeText = decodeText(File.ReadAllBytes(sTarget));
sMadeText = sMadeText.Replace("\r\n", "\n").Replace("\r", "\n").Replace("\n", "\r\n");
File.WriteAllText(sTarget, sMadeText, new UTF8Encoding(true));
}
// EVERY FILE FINISHED FOR A SCREEN READER, THEN CHECKED (kit 1.91.0): see finishOutput. The
// middle file of a two-step conversion is not, since the next step reads it, not a person.
if (!hsIntermediates.Contains(Path.GetFullPath(sTarget))) finishOutput(sTarget);
return true;
}
lsWhy.Add(sWay + ": " + sStepError);
}
sError = lsWhy.Count == 1 ? lsWhy[0] : "every way failed: " + String.Join("; ", lsWhy.ToArray());
return false;
} // convertByRoute method

// runWay: one way's steps, each handing a temporary file to the next.
private static bool runWay(string[] aSteps, string sSource, string sTarget, out string sError) {
sError = "";
string sNow = sSource;
List<string> lsTemps = new List<string>();
try {
for (int i = 0; i < aSteps.Length; i++) {
string[] aParts = aSteps[i].Split(':');
string sEngine = aParts[0].Trim();
bool bLast = i == aSteps.Length - 1;
string sOut = sTarget;
if (!bLast) {
string sHands = aParts.Length > 1 ? aParts[1].Trim() : "md";
sOut = tempPath(sSource, "." + sHands);
lsTemps.Add(sOut);
}
if (!runEngine(sEngine, sNow, sOut, out sError)) return false;
if (!File.Exists(sOut)) { sError = sEngine + " wrote no file"; return false; }
sNow = sOut;
}
return true;
}
finally {
foreach (string sTemp in lsTemps) { try { File.Delete(sTemp); } catch (Exception) { } }
}
} // runWay method

private static bool runEngine(string sEngine, string sSource, string sTarget, out string sError) {
sError = "";
try {
switch (sEngine) {
case "copy": File.Copy(sSource, sTarget, true); return true;
case "officecom": return officeCom(sSource, sTarget, out sError);
case "edge": return edgePdf(sSource, sTarget, out sError);
case "sqlite": return runPython(sSqliteScript, sSource, sTarget, out sError);
case "markdown": return markdownToHtml(sSource, sTarget, out sError);
case "pandoc": return pandoc(sSource, sTarget, out sError);
case "pdfstructure": return pdfStructure(sSource, sTarget, out sError);
case "pdftext": return pdfText(sSource, sTarget, out sError);
case "ocr": return ocrEngine(sSource, sTarget, out sError);
case "table": return tableEngine(sSource, sTarget, out sError);
case "zipxml": return zipXml(sSource, sTarget, out sError);
case "json": case "page": {
bool bMade = false; string sPageError = "";
pageConvert(sEngine, sSource, sTarget, ref bMade, ref sPageError);
sError = sPageError;
return bMade;
}
}
sError = "the engine " + sEngine + " is not part of the C# conversion code";
return false;
}
catch (Exception ex) {
Log.exception(ex);
sError = ex.Message;
return false;
}
} // runEngine method

// engineMissing: "" when the engine can run here, else why it cannot.
public static string engineMissing(string sEngine, string sSource) {
switch (sEngine) {
case "copy": case "markdown": case "table": case "zipxml": return "";
case "pandoc": return havePandoc() ? "" : "Pandoc is not installed";
case "pdftext": return havePdfPig() || pythonProgram() != "" ? "" : "neither PdfPig nor Python is present";
case "pdfstructure": return haveReader() || pythonProgram() != "" ? "" : "neither the PDF reader nor Python is present";
case "ocr": return !haveReader() ? "this program does not include the PDF reader, which OCR needs" : haveTesseract() ? "" : "Tesseract is not installed";
case "officecom": return officeApp(sSource) == "" ? "Office cannot open this type" : "";
case "edge": return edgePath() != "" ? "" : "Microsoft Edge is not installed";
case "sqlite": return pythonProgram() != "" ? "" : "Python is not installed, and an SQLite database is read and written by it";
case "json": case "page": { bool bPage = false; pageState(ref bPage); return bPage ? "" : "this program does not include the Homer page writer (ConversionPage.cs)"; }
}
return "the engine " + sEngine + " is unknown";
} // engineMissing method

// toText: the text of a file by the QUICKEST route, for a key that must answer
// at once, such as FileDir's ? key. Text files are read as they are.
public static string toText(string sPath, out string sError) {
sError = "";
if (!File.Exists(sPath)) { sError = "the file was not found"; return ""; }
// Text by its extension, or by its bytes when the extension is unknown, is read
// as it is, in the encoding it is in.
if (Array.IndexOf(aPlainSources, Path.GetExtension(sPath).ToLowerInvariant()) >= 0 || (!hasAnyRoute(sPath) && recognize(sPath).bText)) {
try { return Util.file2String(sPath); }
catch (Exception ex) { sError = ex.Message; return ""; }
}
string sTemp = tempPath(sPath, ".txt");
try {
if (!convert(sPath, sTemp, true, out sError)) return "";
string sText = Util.file2String(sTemp);
if (sText.Trim().Length == 0) {
sError = typeOf(sPath) == "pdf" ? "this PDF has no text layer; it is probably a scan, which HomerScribe can read" : "no text was found in it";
return "";
}
return sText;
}
finally { try { File.Delete(sTemp); } catch (Exception) { } }
} // toText method

// toPlainText: the earlier name, kept for FileDir's callers.
public static string toPlainText(string sPath, out string sError) {
return toText(sPath, out sError);
} // toPlainText method

private static string tempPath(string sSource, string sExt) {
return Path.Combine(Path.GetTempPath(), Path.GetFileNameWithoutExtension(sSource) + "_" + Guid.NewGuid().ToString("N").Substring(0, 8) + sExt);
} // tempPath method

// ------- recognizing a file (kit 1.74.0) -------

// FileKind: what a file is, worked out from its extension AND its bytes, so a
// .inix, .m3u or any file with no known extension is still recognized as text,
// and a binary file wearing a .txt name is not read aloud as gibberish.
public class FileKind {
public bool bText = false;
public int iLines = 0;
public string sEncoding = "";
public string sHow = "";
public string sName = "";
public string sType = "";
} // FileKind class

// The names a person hears for the common types, by extension.
private static readonly string[,] aTypeNames = {
{"bat", "Windows batch script"}, {"cmd", "Windows command script"}, {"cs", "C# source"}, {"css", "style sheet"},
{"csv", "comma separated table"}, {"cue", "CD cue sheet"}, {"doc", "Word 97 document"}, {"docx", "Word document"},
{"db", "SQLite database"}, {"epub", "EPUB book"}, {"exe", "program"}, {"htm", "web page"}, {"ini", "settings file"}, {"inix", "Homer settings file"},
{"iss", "Inno Setup script"}, {"jkm", "JAWS key map"}, {"jpg", "JPEG picture"}, {"js", "JavaScript source"},
{"jsd", "JAWS script documentation"}, {"jsh", "JAWS script header"}, {"json", "JSON data"}, {"jss", "JAWS script source"},
{"log", "log"}, {"m3u", "M3U play list"}, {"m3u8", "M3U play list"}, {"md", "Markdown document"}, {"mp3", "MP3 audio"},
{"mp4", "MP4 video"}, {"odt", "OpenDocument text"}, {"pdf", "PDF document"}, {"pls", "PLS play list"}, {"png", "PNG picture"},
{"ppt", "PowerPoint 97 presentation"}, {"pptx", "PowerPoint presentation"}, {"ps1", "PowerShell script"}, {"py", "Python script"},
{"rtf", "rich text document"}, {"sql", "SQL script"}, {"srt", "subtitles"}, {"tsv", "tab separated table"},
{"txt", "plain text"}, {"url", "internet shortcut"}, {"vbs", "VBScript"}, {"vtt", "subtitles"}, {"wav", "WAV audio"},
{"xls", "Excel 97 workbook"}, {"xlsx", "Excel workbook"}, {"xml", "XML data"}, {"yaml", "YAML data"}, {"yml", "YAML data"},
{"zip", "zip archive"}
};

private const int iSniffBytes = 65536;

// recognize: the extension says what a file claims to be; the first bytes say
// what it is. A byte-order mark, a magic number or a zero byte settles it; text
// with no mark gets its encoding from Ude, the NuGet port of Mozilla's detector,
// when Ude.dll is beside the program, and otherwise from a strict UTF-8 test.
public static FileKind recognize(string sPath) {
FileKind oKind = new FileKind();
oKind.sType = typeOf(sPath);
oKind.sName = typeName(oKind.sType);
byte[] ab = new byte[0];
try {
using (FileStream oStream = new FileStream(sPath, FileMode.Open, FileAccess.Read, FileShare.ReadWrite)) {
ab = new byte[(int) Math.Min(oStream.Length, (long) iSniffBytes)];
int iRead = 0;
while (iRead < ab.Length) { int i = oStream.Read(ab, iRead, ab.Length - iRead); if (i <= 0) break; iRead += i; }
}
}
catch (Exception ex) { oKind.sHow = "could not be read: " + ex.Message; return oKind; }
if (ab.Length == 0) { oKind.bText = true; oKind.sHow = "empty"; return oKind; }
string sMagic = magicType(ab);
if (sMagic != "") {
oKind.sHow = "by content";
if (oKind.sName == "" || (sMagic != "zip" && sMagic != oKind.sType)) { oKind.sType = sMagic; oKind.sName = typeName(sMagic); }
return oKind;
}
string sBom = bomEncoding(ab);
if (sBom != "" || Array.IndexOf(ab, (byte) 0) < 0) {
oKind.bText = true;
oKind.sEncoding = sBom != "" ? sBom : guessEncoding(ab);
oKind.sHow = Array.IndexOf(aPlainSources, "." + oKind.sType) >= 0 ? "by extension and content" : "by content";
if (oKind.sName == "") oKind.sName = "text file";
oKind.iLines = countLines(sPath, ab.Length < iSniffBytes ? ab : null);
return oKind;
}
oKind.sHow = "by content: it holds zero bytes, so it is not text";
if (oKind.sName == "" || Array.IndexOf(aPlainSources, "." + oKind.sType) >= 0) oKind.sName = "binary file";
return oKind;
} // recognize method

// describe: one line a person hears, such as "M3U play list, text in UTF-8, 12 lines".
public static string describe(string sPath) {
FileKind o = recognize(sPath);
string sName = o.sName == "" ? (o.sType == "" ? "file with no type" : o.sType + " file") : o.sName;
if (!o.bText) return sName;
if (o.sHow == "empty") return sName + ", empty";
string sLine = sName + (sName.EndsWith("text") ? "" : ", text") + (o.sEncoding != "" ? " in " + o.sEncoding : "");
if (o.iLines > 0) sLine += ", " + (o.iLines == 1 ? "1 line" : o.iLines + " lines");
return sLine;
} // describe method

public static string typeName(string sType) {
for (int i = 0; i < aTypeNames.GetLength(0); i++) if (aTypeNames[i, 0] == sType) return aTypeNames[i, 1];
return "";
} // typeName method

private static string magicType(byte[] ab) {
if (startsWith(ab, 0x25, 0x50, 0x44, 0x46)) return "pdf";
if (startsWith(ab, 0x50, 0x4B, 0x03, 0x04)) return "zip";
if (startsWith(ab, 0x89, 0x50, 0x4E, 0x47)) return "png";
if (startsWith(ab, 0xFF, 0xD8, 0xFF)) return "jpg";
if (startsWith(ab, 0x4D, 0x5A)) return "exe";
if (startsWith(ab, 0xD0, 0xCF, 0x11, 0xE0)) return "doc";
if (startsWith(ab, 0x49, 0x44, 0x33)) return "mp3";
return "";
} // magicType method

private static bool startsWith(byte[] ab, params int[] aWant) {
if (ab.Length < aWant.Length) return false;
for (int i = 0; i < aWant.Length; i++) if (ab[i] != aWant[i]) return false;
return true;
} // startsWith method

private static string bomEncoding(byte[] ab) {
if (startsWith(ab, 0xEF, 0xBB, 0xBF)) return "UTF-8 with byte order mark";
if (startsWith(ab, 0xFF, 0xFE)) return "UTF-16";
if (startsWith(ab, 0xFE, 0xFF)) return "UTF-16 big endian";
return "";
} // bomEncoding method

// guessEncoding: Ude when it is present; else UTF-8 if every byte sequence is
// valid UTF-8, else the Windows code page.
private static string guessEncoding(byte[] ab) {
string sUde = udeCharset(ab);
if (sUde != "") return sUde.ToUpperInvariant() == "ASCII" ? "ASCII" : sUde;
try {
new UTF8Encoding(false, true).GetString(ab);
foreach (byte b in ab) if (b > 127) return "UTF-8";
return "ASCII";
}
catch (Exception) { return "Windows code page " + Encoding.Default.CodePage; }
} // guessEncoding method

private static string udeCharset(byte[] ab) {
try {
string sUde = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "Ude.dll");
if (!File.Exists(sUde)) return "";
Type tDetector = Assembly.LoadFrom(sUde).GetType("Ude.CharsetDetector", false);
if (tDetector == null) return "";
object oDetector = Activator.CreateInstance(tDetector);
tDetector.GetMethod("Feed", new Type[] { typeof(byte[]), typeof(int), typeof(int) }).Invoke(oDetector, new object[] { ab, 0, ab.Length });
tDetector.GetMethod("DataEnd", Type.EmptyTypes).Invoke(oDetector, null);
return "" + tDetector.GetProperty("Charset").GetValue(oDetector, null);
}
catch (Exception) { return ""; }
} // udeCharset method

// countLines: from the bytes already read when the file is small, else by
// streaming, so a large log is counted without loading it whole.
private static int countLines(string sPath, byte[] abWhole) {
int iLines = 0;
bool bLastBreak = true;
try {
if (abWhole != null) {
foreach (byte b in abWhole) { if (b == 0x0A) iLines++; }
bLastBreak = abWhole.Length > 0 && abWhole[abWhole.Length - 1] == 0x0A;
}
else {
using (FileStream oStream = new FileStream(sPath, FileMode.Open, FileAccess.Read, FileShare.ReadWrite)) {
byte[] abBuffer = new byte[iSniffBytes];
int iRead;
while ((iRead = oStream.Read(abBuffer, 0, abBuffer.Length)) > 0) {
for (int i = 0; i < iRead; i++) if (abBuffer[i] == 0x0A) iLines++;
bLastBreak = abBuffer[iRead - 1] == 0x0A;
}
}
}
}
catch (Exception) { return 0; }
return bLastBreak ? iLines : iLines + 1;
} // countLines method

// ------- what a file can become (the lists FileDir's Convert command offers) -------

public static readonly string[,] aDocumentTargets = {
{"Word document", "docx"}, {"Web page", "htm"}, {"Markdown", "md"}, {"Plain text", "txt"},
{"OpenDocument text", "odt"}, {"Rich text", "rtf"}, {"EPUB book", "epub"}, {"LaTeX", "tex"},
{"reStructuredText", "rst"}, {"MediaWiki", "mediawiki"}
};

public static readonly string[] aPandocReadable = {
".docx", ".odt", ".epub", ".html", ".htm", ".rtf", ".md", ".markdown",
".rst", ".tex", ".latex", ".csv", ".tsv", ".org", ".textile", ".mediawiki",
".ipynb", ".fb2", ".typ", ".jats", ".opml", ".bib"
};

private static readonly string[] aDocumentSources = {
".docx", ".odt", ".epub", ".html", ".htm", ".rtf", ".md", ".markdown",
".rst", ".tex", ".latex", ".csv", ".tsv", ".org", ".textile", ".mediawiki",
".ipynb", ".fb2", ".typ", ".jats", ".opml", ".bib", ".txt", ".pptx", ".xlsx"
};

private static readonly string[] aLegacySources = {".doc", ".ppt", ".xls"};

private static readonly string[] aPlainSources = {
".m3u", ".m3u8", ".pls", ".url", ".cue", ".srt", ".vtt", ".sub", ".ass",
".txt", ".md", ".markdown", ".csv", ".tsv", ".log", ".ini", ".inix", ".json", ".xml",
".yml", ".yaml", ".cs", ".js", ".py", ".ps1", ".cmd", ".bat", ".vbs", ".sql",
".c", ".cpp", ".h", ".java", ".php", ".rb", ".go", ".rs", ".ts", ".css",
".jss", ".jsh", ".jsd", ".jkm", ".iss", ".bas", ".vb", ".sh", ".tex", ".rst"
};

private static readonly string[] aRichForms = {
".docx", ".odt", ".rtf", ".html", ".htm", ".epub", ".md", ".markdown",
".rst", ".tex", ".csv", ".tsv", ".inix", ".xlsx", ".pdf"
};

public static bool canRead(string sPath) {
return Array.IndexOf(aPandocReadable, Path.GetExtension(sPath).ToLowerInvariant()) >= 0;
} // canRead method

public static bool readableAsText(string sPath) {
string sExt = Path.GetExtension(sPath).ToLowerInvariant();
if (Array.IndexOf(aPlainSources, sExt) >= 0) return true;
if (hasRoute(sPath, "txt")) return true;
// An extension nobody listed: the bytes decide.
return !hasAnyRoute(sPath) && File.Exists(sPath) && recognize(sPath).bText;
} // readableAsText method

// hasAnyRoute: whether the routing table names any conversion from this type.
public static bool hasAnyRoute(string sPath) {
loadTable();
string sPrefix = typeOf(sPath) + "2";
foreach (string sKey in dWays.Keys) if (sKey.StartsWith(sPrefix, StringComparison.OrdinalIgnoreCase)) return true;
return false;
} // hasAnyRoute method

public static bool hasRichForm(string sPath) {
return Array.IndexOf(aRichForms, Path.GetExtension(sPath).ToLowerInvariant()) >= 0;
} // hasRichForm method

public static string categoryOf(string sPath) {
string sExt = Path.GetExtension(sPath).ToLowerInvariant();
if (Table.canRead(sPath) && sExt != ".md" && sExt != ".markdown") return "table";
if (sExt == ".pptx") return "openxml";
if (sExt == ".pdf") return "pdf";
if (Array.IndexOf(aDocumentSources, sExt) >= 0) return "document";
if (Array.IndexOf(aLegacySources, sExt) >= 0) return "legacy";
return mediaCategoryOf(sExt);
} // categoryOf method

static partial void mediaCategory(string sExt, ref string sCategory);
static partial void mediaTargets(string sCategory, ref string[,] aTargets);
static partial void mediaConvert(string sSource, string sTarget, ref bool bHandled, ref bool bMade, ref string sError);
static partial void mediaCan(string sSource, string sTarget, ref bool bCan);
static partial void mediaAllTargets(List<string[]> lsAll);

// canConvert: whether convert can make sTarget's type from sSource's (kit 1.84.0): the route
// table, or the media half -- media to media, speech to text, text to speech -- when the app
// compiles ConversionMedia. The question to ask before a batch, as BatCon does.
public static bool canConvert(string sSource, string sTarget) {
if (hasRoute(sSource, sTarget)) return true;
if (hubFor(sSource, sTarget) != "") return true;
bool bCan = false;
mediaCan(sSource, sTarget, ref bCan);
return bCan;
} // canConvert method

private static string mediaCategoryOf(string sExt) {
string sCategory = "";
mediaCategory(sExt, ref sCategory);
return sCategory;
} // mediaCategoryOf method

// targetsFor: what a file can become, as [label, extension] pairs (kit 1.80.1). First the
// category's curated list, in the order FileDir's Convert offers it; then every other target
// the route table has for this file's type, by the kit's name for that type, alphabetically.
// THE LIST NOW FOLLOWS THE ROUTES. It was only the curated menu, so a route added to
// conversions.inix -- inix2xlsx, md2pptx -- never appeared in a picker; ChatGPT's BatCon read
// conversions.inix itself for that reason, which was a fair reading of a real gap.
public static string[,] targetsFor(string sPath) {
string[,] aCurated = curatedTargetsFor(sPath);
List<string[]> lsAll = new List<string[]>();
HashSet<string> hsSeen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
for (int i = 0; i < aCurated.GetLength(0); i++)
if (hsSeen.Add(typeOf(aCurated[i, 1]))) lsAll.Add(new string[] { aCurated[i, 0], aCurated[i, 1] });
string sFrom = typeOf(sPath);
List<string[]> lsMore = new List<string[]>();
try {
loadTable();
if (dWays != null && sFrom != "")
foreach (string sRoute in dWays.Keys) {
// Split by the known source type: a type may hold a digit (mp3, epub3), so the first 2 is not the joint.
if (!sRoute.StartsWith(sFrom + "2", StringComparison.OrdinalIgnoreCase)) continue;
string sTo = typeOf(sRoute.Substring(sFrom.Length + 1));
if (sTo == "" || sTo == sFrom || !hsSeen.Add(sTo)) continue;
string sName = typeName(sTo);
if (string.IsNullOrEmpty(sName) || sName == sTo) sName = sTo.ToUpperInvariant() + " file";
lsMore.Add(new string[] { char.ToUpperInvariant(sName[0]) + sName.Substring(1), sTo });
}
} catch (Exception oError) { Log.warn("targetsFor: the route table could not be read: " + oError.Message); }
lsMore.Sort(delegate(string[] a, string[] b) { return string.Compare(a[0], b[0], StringComparison.OrdinalIgnoreCase); });
lsAll.AddRange(lsMore);
string[,] aAll = new string[lsAll.Count, 2];
for (int i = 0; i < lsAll.Count; i++) { aAll[i, 0] = lsAll[i][0]; aAll[i, 1] = lsAll[i][1]; }
return aAll;
}

// allTargets: every type some route in the table can make, as extensions with the kit's
// readable name for each, sorted alphabetically by that name (kit 1.83.0). For a picker that
// offers every target at once, before any source is known -- BatCon's Target format -- with
// hasRoute(source, target) asked per file at run time.
public static string[] allTargets(out string[] aLabels) {
List<string[]> lsAll = new List<string[]>();
HashSet<string> hsSeen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
try {
loadTable();
if (dWays != null)
foreach (string sRoute in dWays.Keys) {
// The joint is the first 2 whose left side is a type the kit names; a type may hold a
// digit (an mp32wav route would), so the first 2 alone is only the fallback.
int iJoint = sRoute.IndexOf('2');
for (int iTry = iJoint; iTry > 0; iTry = sRoute.IndexOf('2', iTry + 1)) {
string sLeft = sRoute.Substring(0, iTry);
if (typeName(sLeft) != "") { iJoint = iTry; break; }
}
if (iJoint <= 0 || iJoint >= sRoute.Length - 1) continue;
string sTo = typeOf(sRoute.Substring(iJoint + 1));
if (sTo == "" || !hsSeen.Add(sTo)) continue;
string sName = typeName(sTo);
if (string.IsNullOrEmpty(sName) || sName == sTo) sName = sTo.ToUpperInvariant() + " file";
lsAll.Add(new string[] { char.ToUpperInvariant(sName[0]) + sName.Substring(1) + " (" + sTo + ")", sTo });
}
} catch (Exception oError) { Log.warn("allTargets: the route table could not be read: " + oError.Message); }
// The media half's targets too (1.84.0), when the app compiles ConversionMedia.
List<string[]> lsMedia = new List<string[]>();
mediaAllTargets(lsMedia);
foreach (string[] aOne in lsMedia) {
if (!hsSeen.Add(aOne[1])) continue;
string sName = typeName(aOne[1]);
if (string.IsNullOrEmpty(sName)) sName = aOne[0];
lsAll.Add(new string[] { char.ToUpperInvariant(sName[0]) + sName.Substring(1) + " (" + aOne[1] + ")", aOne[1] });
}
lsAll.Sort(delegate(string[] a, string[] b) { return string.Compare(a[0], b[0], StringComparison.OrdinalIgnoreCase); });
aLabels = new string[lsAll.Count];
string[] aExtensions = new string[lsAll.Count];
for (int i = 0; i < lsAll.Count; i++) { aLabels[i] = lsAll[i][0]; aExtensions[i] = lsAll[i][1]; }
return aExtensions;
} // allTargets method

// curatedTargetsFor: the hand-ordered list for each kind of file, before the route table adds to it.
private static string[,] curatedTargetsFor(string sPath) {
string sCategory = categoryOf(sPath);
if (sCategory == "document") return aDocumentTargets;
if (sCategory == "table")
return new string[,] {{"Inix records", "inix"}, {"Comma separated", "csv"}, {"Tab separated", "tsv"},
{"Markdown table", "md"}, {"Word document", "docx"}, {"Web page", "htm"}, {"OpenDocument text", "odt"}};
if (sCategory == "openxml" || sCategory == "pdf")
return new string[,] {{"Markdown", "md"}, {"Plain text", "txt"}, {"Web page", "htm"}, {"Word document", "docx"},
{"OpenDocument text", "odt"}, {"Rich text", "rtf"}};
if (sCategory == "legacy")
return new string[,] {{"Plain text", "txt"}, {"Web page", "htm"}};
string[,] aMedia = new string[0, 2];
mediaTargets(sCategory, ref aMedia);
return aMedia;
} // curatedTargetsFor method

public static string[] targetLabelsFor(string sPath, out string[] aExtensions) {
string[,] aTargets = targetsFor(sPath);
string sOwn = Path.GetExtension(sPath).ToLowerInvariant().TrimStart('.');
List<string> lsLabels = new List<string>();
List<string> lsExts = new List<string>();
for (int i = 0; i < aTargets.GetLength(0); i++) {
string sExt = aTargets[i, 1];
if (String.Compare(sExt, sOwn, true) == 0) continue;
if (sOwn == "jpeg" && sExt == "jpg") continue;
if ((sOwn == "html" && sExt == "htm") || (sOwn == "htm" && sExt == "html")) continue;
lsLabels.Add(aTargets[i, 0] + " (" + sExt + ")");
lsExts.Add(sExt);
}
aExtensions = lsExts.ToArray();
return lsLabels.ToArray();
} // targetLabelsFor method

// convertAny: whatever the source, to the target path. Documents and tables go
// by the routing table, media through ConversionMedia.cs.
// convertAny: convert, under the name FileDir has always called (1.80.2).
public static bool convertAny(string sSource, string sTarget, out string sError) {
return convert(sSource, sTarget, false, out sError);
} // convertAny method

// convertFile: convert, under an older name (1.80.2). It was Pandoc alone, which gave a
// caller a different conversion from every other app's; now it is the same one.
public static bool convertFile(string sSource, string sTarget, out string sError) {
return convert(sSource, sTarget, false, out sError);
} // convertFile method

// toHtmlFragment: a file as HTML, for the clipboard.
public static string toHtmlFragment(string sPath, out string sError) {
sError = "";
string sTemp = tempPath(sPath, ".htm");
try {
if (!convertAny(sPath, sTemp, out sError)) return "";
return Util.file2String(sTemp);
}
finally { try { File.Delete(sTemp); } catch (Exception) { } }
} // toHtmlFragment method

public static string htmlClipboardFormat(string sHtml) {
string sPrefix = "<html><body><!--StartFragment-->";
string sSuffix = "<!--EndFragment--></body></html>";
string sHeader = "Version:0.9\r\nStartHTML:{0:D10}\r\nEndHTML:{1:D10}\r\nStartFragment:{2:D10}\r\nEndFragment:{3:D10}\r\n";
int iStartHtml = String.Format(sHeader, 0, 0, 0, 0).Length;
int iStartFragment = iStartHtml + Encoding.UTF8.GetByteCount(sPrefix);
int iEndFragment = iStartFragment + Encoding.UTF8.GetByteCount(sHtml);
int iEndHtml = iEndFragment + Encoding.UTF8.GetByteCount(sSuffix);
return String.Format(sHeader, iStartHtml, iEndHtml, iStartFragment, iEndFragment) + sPrefix + sHtml + sSuffix;
} // htmlClipboardFormat method

// ------- engine: pandoc -------

private static string sPandocCache = null;

public static string pandocPath() {
if (sPandocCache != null) return sPandocCache;
sPandocCache = findProgram("pandoc.exe", new string[] {
Environment.ExpandEnvironmentVariables(@"%ProgramFiles%\Pandoc\pandoc.exe"),
Environment.ExpandEnvironmentVariables(@"%LOCALAPPDATA%\Pandoc\pandoc.exe") });
return sPandocCache;
} // pandocPath method

public static bool havePandoc() {
return pandocPath().Length > 0;
} // havePandoc method

private static bool pandoc(string sSource, string sTarget, out string sError) {
string sExe = pandocPath();
if (sExe == "") { sError = "Pandoc is not installed"; return false; }
string sTo = typeOf(sTarget);
StringBuilder sb = new StringBuilder(Util.stringQuote(sSource));
if (sTo == "htm" || sTo == "epub" || sTo == "tex" || sTo == "rtf") sb.Append(" --standalone");
if (sTo == "txt") sb.Append(" -t plain --wrap=none");
if (sTo == "htm") sb.Append(" -t html5");
// MATH AS MATHML (kit 1.77.0, key decision 8): screen readers read MathML as math, through MathCAT in
// NVDA and JAWS's own math support, where Pandoc's default leaves TeX source. A page without math is unchanged.
if (sTo == "htm") sb.Append(" --mathml");
string sFilter = pageBreakFilter();
if (sFilter != "" && (sTo == "docx" || sTo == "htm" || sTo == "odt" || sTo == "epub")) sb.Append(" -L " + Util.stringQuote(sFilter));
sb.Append(" -o " + Util.stringQuote(sTarget));
string sOut;
return run(sExe, sb.ToString(), out sOut, out sError);
} // pandoc method

// pageBreakFilter: the official pandoc-ext pagebreak.lua, where the program
// ships it, so a \pagebreak paragraph becomes a real page break.
private static string pageBreakFilter() {
string sExeDir = AppDomain.CurrentDomain.BaseDirectory;
foreach (string sTry in new string[] { Path.Combine(sExeDir, "pagebreak.lua"), Path.Combine(sExeDir, "..\\scripts\\pagebreak.lua"), Path.Combine(sExeDir, "scripts\\pagebreak.lua") })
if (File.Exists(sTry)) return Path.GetFullPath(sTry);
return "";
} // pageBreakFilter method

// ------- engines: pdftext and pdfstructure -------

// havePdfPig: PdfPig's assembly beside the program, as HomerScribe ships it.
public static bool havePdfPig() {
return File.Exists(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "UglyToad.PdfPig.dll"));
} // havePdfPig method

// pdfText: the text layer, the quickest way there is. PdfPig in-process needs
// no program to start; it is loaded by reflection so an app without it still
// compiles, and any failure falls to PyMuPDF's plain text.
private static bool pdfText(string sSource, string sTarget, out string sError) {
sError = "";
if (havePdfPig()) {
string sText;
if (pdfPigText(sSource, out sText, out sError)) {
File.WriteAllText(sTarget, sText, new UTF8Encoding(true));
return true;
}
Log.info("PdfPig could not read " + Path.GetFileName(sSource) + ": " + sError + "; trying PyMuPDF");
}
return runPython(sPyMuPdfText, sSource, sTarget, out sError);
} // pdfText method

private static bool pdfPigText(string sSource, out string sText, out string sError) {
sText = ""; sError = "";
try {
Assembly oPig = Assembly.LoadFrom(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "UglyToad.PdfPig.dll"));
Type tDocument = oPig.GetType("UglyToad.PdfPig.PdfDocument", true);
MethodInfo mOpen = null;
foreach (MethodInfo m in tDocument.GetMethods(BindingFlags.Public | BindingFlags.Static)) {
ParameterInfo[] aParams = m.GetParameters();
if (m.Name == "Open" && aParams.Length >= 1 && aParams[0].ParameterType == typeof(string)) { mOpen = m; break; }
}
if (mOpen == null) { sError = "PdfPig has no Open(string)"; return false; }
object[] aArgs = new object[mOpen.GetParameters().Length];
aArgs[0] = sSource;
object oDoc = mOpen.Invoke(null, aArgs);
Type tExtractor = null;
foreach (Assembly a in AppDomain.CurrentDomain.GetAssemblies()) {
tExtractor = a.GetType("UglyToad.PdfPig.DocumentLayoutAnalysis.TextExtractor.ContentOrderTextExtractor", false);
if (tExtractor != null) break;
}
if (tExtractor == null) {
string sLayout = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "UglyToad.PdfPig.DocumentLayoutAnalysis.dll");
if (File.Exists(sLayout)) tExtractor = Assembly.LoadFrom(sLayout).GetType("UglyToad.PdfPig.DocumentLayoutAnalysis.TextExtractor.ContentOrderTextExtractor", false);
}
StringBuilder sb = new StringBuilder();
try {
IEnumerable oPages = (IEnumerable) tDocument.GetMethod("GetPages", Type.EmptyTypes).Invoke(oDoc, null);
foreach (object oPage in oPages) {
string sPage = "";
if (tExtractor != null) {
MethodInfo mGet = tExtractor.GetMethod("GetText", new Type[] { oPage.GetType() });
if (mGet == null) foreach (MethodInfo m in tExtractor.GetMethods()) if (m.Name == "GetText" && m.GetParameters().Length >= 1) { mGet = m; break; }
if (mGet != null) {
object[] aGet = new object[mGet.GetParameters().Length];
aGet[0] = oPage;
sPage = "" + mGet.Invoke(null, aGet);
}
}
if (sPage == "") sPage = "" + oPage.GetType().GetProperty("Text").GetValue(oPage, null);
if (sb.Length > 0) sb.Append("\r\n\r\n");
sb.Append(sPage.Trim());
}
}
finally {
IDisposable oDispose = oDoc as IDisposable;
if (oDispose != null) oDispose.Dispose();
}
sText = sb.ToString();
return true;
}
catch (Exception ex) {
sError = (ex.InnerException != null ? ex.InnerException.Message : ex.Message);
return false;
}
} // pdfPigText method

// ------- the PDF reader: pdfstructure and ocr -------

// Filled by ConversionPdf.cs, in apps that compile PdfReader.cs with PdfPig.
// Left out, they compile to nothing and the Python readers are used instead.
static partial void readerState(ref bool bReader, ref bool bTesseract);
// The Homer page writer, 2htm's page form (1.87.0), in ConversionPage.cs when the app compiles it.
static partial void pageState(ref bool bPage);
static partial void pageConvert(string sEngine, string sSource, string sTarget, ref bool bMade, ref string sError);
static partial void pageFinish(string sPath, ref string sError);
static partial void readerConvert(string sSource, string sTarget, bool bOcr, ref bool bMade, ref bool bScans, ref string sError);

// haveReader: true when this program compiled HomerScribe's PDF reader in.
public static bool haveReader() {
bool bReader = false, bTesseract = false;
readerState(ref bReader, ref bTesseract);
return bReader;
} // haveReader method

// haveTesseract: true when the reader is here and Tesseract is installed.
public static bool haveTesseract() {
bool bReader = false, bTesseract = false;
readerState(ref bReader, ref bTesseract);
return bReader && bTesseract;
} // haveTesseract method

// pdfStructure: headings, lists, tables and reading order. HomerScribe's reader
// when it is compiled in, the best there is; otherwise pymupdf4llm. A document of
// scans is not handed to pymupdf4llm, which would return almost nothing and stop
// the ocr way being tried.
private static bool pdfStructure(string sSource, string sTarget, out string sError) {
sError = "";
if (haveReader()) {
bool bMade = false, bScans = false;
string sReaderError = "";
readerConvert(sSource, sTarget, false, ref bMade, ref bScans, ref sReaderError);
if (bMade) return true;
sError = sReaderError;
if (bScans || pythonProgram() == "") return false;
Log.info("The PDF reader could not read " + Path.GetFileName(sSource) + ": " + sReaderError + "; trying pymupdf4llm");
}
return runPython(sPyMuPdfMarkdown, sSource, sTarget, out sError);
} // pdfStructure method

// ocrEngine: the reader again, with Tesseract reading every scanned page.
private static bool ocrEngine(string sSource, string sTarget, out string sError) {
sError = "";
if (!haveReader()) { sError = engineMissing("ocr", sSource); return false; }
bool bMade = false, bScans = false;
readerConvert(sSource, sTarget, true, ref bMade, ref bScans, ref sError);
return bMade;
} // ocrEngine method

// THE SQLITE ENGINE (kit 1.90.0): a table to an SQLite database -- one table named after the file,
// its first row the field names, every field text -- and a database to Markdown, each table under its
// own heading, so the Markdown hub takes a database anywhere. Python has SQLite built in and the kit
// has no SQLite of its own, so both languages run THIS SAME SCRIPT: exec\Python\conversion.py holds
// it word for word as sSqliteScript, and the kit's build fails if the two ever differ.
private const string sSqliteScript =
@"import csv, io, os, re, sqlite3, sys
sIn, sOut = sys.argv[1], sys.argv[2]
# A DATABASE IN DBDO'S FORM (kit 1.91.0, the homer-db skill): a plural lower-case table named for the
# file, <singular>_id, added and edited, the data fields, url, notes, tags, look, prime and marked in
# that order, the edited and maps triggers, a unique prime index, and DbDo's lookups, maps and views.
lsTypes = ['BLOB', 'BOOLEAN', 'INTEGER', 'NUMERIC', 'REAL', 'TEXT', 'TEXTLINE', 'TEXTMARKDOWN', 'TEXTMEMO', 'TEXTTIME']
lsKinds = ['affiliated_with', 'located_at', 'member_of', 'part_of', 'related_to']
lsHousekeeping = ['added', 'edited', 'look', 'prime', 'marked']
dIrregular = {'people': 'person', 'children': 'child', 'men': 'man', 'women': 'woman', 'data': 'data'}
def decode(ab):
    for sCodec in ('utf-8-sig', 'cp1252'):
        try: return ab.decode(sCodec)
        except UnicodeDecodeError: pass
    return ab.decode('utf-8', 'replace')
def cell(v):
    return ('' if v is None else str(v)).replace('|', '\\|').replace('\r', ' ').replace('\n', ' ')
def snake(s):
    s = re.sub(r'[^0-9a-z]+', '_', re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s.strip()).lower()).strip('_')
    return ('f_' + s) if s[:1].isdigit() else s
def plural(s):
    if s in dIrregular or s.endswith('s') and not s.endswith('ss'): return s
    if s.endswith('y') and s[-2:-1] not in ('a', 'e', 'i', 'o', 'u'): return s[:-1] + 'ies'
    if s.endswith(('x', 'ch', 'sh', 'ss', 'z')): return s + 'es'
    return s + 's'
def singular(s):
    if s in dIrregular: return dIrregular[s]
    if s.endswith('ies'): return s[:-3] + 'y'
    if s.endswith(('ches', 'shes', 'xes', 'sses', 'zes')): return s[:-2]
    if s.endswith('s') and not s.endswith('ss'): return s[:-1]
    return s
def q(s):
    return '""' + s.replace('""', '""""') + '""'
def joined(lsFields, sJoin, bSkipBlank):
    if not bSkipBlank: return "" || '|' || "".join(""coalesce(CAST(%s AS TEXT),'')"" % q(s) for s in lsFields)
    return ""rtrim("" + "" || "".join(""iif(%s IS NOT NULL AND length(CAST(%s AS TEXT))>0, CAST(%s AS TEXT) || ' | ', '')"" % (q(s), q(s), q(s)) for s in lsFields) + "", ' | ')""
def kind(lsValues):
    lsFilled = [v for v in lsValues if v.strip()]
    if any('\n' in v for v in lsFilled): return 'TEXTMEMO'
    if lsFilled and all(re.match(r'^-?\d{1,15}$', v.strip()) for v in lsFilled): return 'INTEGER'
    if lsFilled and all(re.match(r'^-?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$', v.strip()) for v in lsFilled): return 'REAL'
    return 'TEXTLINE'
def standardTable(oDb, sTable, lsData, dTypes, lsLook, bMaps):
    sId = singular(sTable) + '_id'
    lsColumns = [q(sId) + ' INTEGER PRIMARY KEY AUTOINCREMENT', 'added TEXTTIME NOT NULL DEFAULT CURRENT_TIMESTAMP', 'edited TEXTTIME NOT NULL DEFAULT CURRENT_TIMESTAMP']
    lsColumns += [q(s) + ' ' + dTypes.get(s, 'TEXTLINE') for s in lsData]
    lsColumns += ['url TEXTLINE', 'notes TEXTMARKDOWN', 'tags TEXTMEMO']
    lsColumns += ['look TEXT GENERATED ALWAYS AS (%s) STORED' % joined(lsLook, ' | ', True), 'prime TEXT GENERATED ALWAYS AS (%s) STORED' % joined(lsData, '|', False), 'marked INTEGER NOT NULL DEFAULT 0']
    oDb.execute('CREATE TABLE %s (%s)' % (q(sTable), ', '.join(lsColumns)))
    lsWatched = lsData + ['notes', 'tags']
    oDb.execute('CREATE TRIGGER %s AFTER UPDATE OF %s ON %s FOR EACH ROW WHEN %s BEGIN UPDATE %s SET edited = CURRENT_TIMESTAMP WHERE %s = NEW.%s; END'
        % (q('trg_' + sTable + '_edited'), ', '.join(q(s) for s in lsWatched), q(sTable), ' OR '.join('OLD.%s IS NOT NEW.%s' % (q(s), q(s)) for s in lsWatched), q(sTable), q(sId), q(sId)))
    oDb.execute('CREATE UNIQUE INDEX %s ON %s (prime)' % (q('idx_' + sTable + '_prime'), q(sTable)))
    if bMaps:
        oDb.execute(""CREATE TRIGGER %s AFTER UPDATE ON %s FOR EACH ROW WHEN OLD.prime IS NOT NEW.prime BEGIN UPDATE maps SET prime1 = NEW.prime WHERE tbl1 = '%s' AND prime1 = OLD.prime; UPDATE maps SET prime2 = NEW.prime WHERE tbl2 = '%s' AND prime2 = OLD.prime; END""
            % (q('trg_' + sTable + '_maps'), q(sTable), sTable, sTable))
        oDb.execute(""CREATE TRIGGER %s AFTER DELETE ON %s FOR EACH ROW BEGIN DELETE FROM maps WHERE (tbl1 = '%s' AND prime1 = OLD.prime) OR (tbl2 = '%s' AND prime2 = OLD.prime); END""
            % (q('trg_' + sTable + '_maps_delete'), q(sTable), sTable, sTable))
if open(sIn, 'rb').read(16) != b'SQLite format 3\x00':
    llAll = [r for r in csv.reader(io.StringIO(decode(open(sIn, 'rb').read())))]
    llAll = [r for r in llAll if any(v.strip() for v in r)]
    if not llAll: raise SystemExit('the table is empty')
    sTable = plural(snake(os.path.basename(sOut).split('.')[0]) or 'record')
    if sTable in ('lookups', 'maps', 'views'): sTable = 'user_' + sTable
    lsReserved = lsHousekeeping + [singular(sTable) + '_id']
    lsFields = []
    for i, sField in enumerate(llAll[0]):
        sField = snake(sField) or 'column_%d' % (i + 1)
        if sField in lsReserved: sField += '_value'
        while sField in lsFields: sField += '_'
        lsFields.append(sField)
    iWidth = len(lsFields)
    llRows = [(list(r) + [''] * iWidth)[:iWidth] for r in llAll[1:]]
    lsData = [s for s in lsFields if s not in ('url', 'notes', 'tags')]
    if not lsData: raise SystemExit('the table has no field but url, notes and tags')
    dTypes = {s: kind([r[i] for r in llRows]) for i, s in enumerate(lsFields)}
    if os.path.exists(sOut): os.remove(sOut)
    oDb = sqlite3.connect(sOut)
    oDb.execute('CREATE TABLE lookups (lookup_id INTEGER PRIMARY KEY AUTOINCREMENT, added TEXTTIME NOT NULL DEFAULT CURRENT_TIMESTAMP, edited TEXTTIME NOT NULL DEFAULT CURRENT_TIMESTAMP, '
        'src TEXTLINE, tbl TEXTLINE, fld TEXTLINE, val TEXTLINE, ordinal INTEGER, descrip TEXTMEMO, url TEXTLINE, notes TEXTMARKDOWN, tags TEXTMEMO, '
        ""look TEXT GENERATED ALWAYS AS (rtrim(iif(tbl IS NOT NULL AND length(tbl)>0, tbl || ' | ', '') || iif(fld IS NOT NULL AND length(fld)>0, fld || ' | ', '') || iif(val IS NOT NULL AND length(val)>0, val || ' | ', ''), ' | ')) STORED, ""
        ""prime TEXT GENERATED ALWAYS AS (coalesce(src,'') || '|' || coalesce(tbl,'') || '|' || coalesce(fld,'') || '|' || coalesce(val,'')) STORED, marked INTEGER NOT NULL DEFAULT 0)"")
    oDb.execute('CREATE UNIQUE INDEX idx_lookups_prime ON lookups (prime)')
    oDb.execute('CREATE TABLE maps (map_id INTEGER PRIMARY KEY AUTOINCREMENT, added TEXTTIME NOT NULL DEFAULT CURRENT_TIMESTAMP, edited TEXTTIME NOT NULL DEFAULT CURRENT_TIMESTAMP, '
        'tbl1 TEXTLINE, prime1 TEXTLINE, kind TEXTLINE, tbl2 TEXTLINE, prime2 TEXTLINE, notes TEXTMARKDOWN, tags TEXTMEMO, '
        ""look TEXT GENERATED ALWAYS AS (coalesce(tbl1,'') || ' ' || coalesce(prime1,'') || ' | ' || coalesce(kind,'') || ' | ' || coalesce(tbl2,'') || ' ' || coalesce(prime2,'')) STORED, ""
        ""prime TEXT GENERATED ALWAYS AS (coalesce(tbl1,'') || '|' || coalesce(prime1,'') || '|' || coalesce(kind,'') || '|' || coalesce(tbl2,'') || '|' || coalesce(prime2,'')) STORED, marked INTEGER NOT NULL DEFAULT 0)"")
    oDb.execute('CREATE UNIQUE INDEX idx_maps_prime ON maps (prime)')
    oDb.execute('CREATE INDEX idx_maps_1 ON maps (tbl1, prime1)')
    oDb.execute('CREATE INDEX idx_maps_2 ON maps (tbl2, prime2)')
    oDb.execute('CREATE TABLE views (tbl TEXTLINE NOT NULL, fld TEXTLINE NOT NULL, val TEXTLINE, PRIMARY KEY (tbl, fld))')
    for sOwn, sOwnId, lsOwn in (('lookups', 'lookup_id', ['src', 'tbl', 'fld', 'val', 'ordinal', 'descrip', 'url', 'notes', 'tags']), ('maps', 'map_id', ['tbl1', 'prime1', 'kind', 'tbl2', 'prime2', 'notes', 'tags'])):
        oDb.execute('CREATE TRIGGER %s AFTER UPDATE OF %s ON %s FOR EACH ROW WHEN %s BEGIN UPDATE %s SET edited = CURRENT_TIMESTAMP WHERE %s = NEW.%s; END'
            % (q('trg_' + sOwn + '_edited'), ', '.join(lsOwn), sOwn, ' OR '.join('OLD.%s IS NOT NEW.%s' % (s, s) for s in lsOwn), sOwn, sOwnId, sOwnId))
    lsSeeds = [('DbDo', '*', 'type', s) for s in lsTypes] + [('DbDo', 'maps', 'kind', s) for s in lsKinds]
    for sTbl, sFld in sorted(set((t, f) for _, t, f, _ in lsSeeds)):
        lsVals = sorted(v for _, t, f, v in lsSeeds if t == sTbl and f == sFld)
        oDb.executemany('INSERT INTO lookups (src, tbl, fld, val, ordinal) VALUES (?, ?, ?, ?, ?)', [('DbDo', sTbl, sFld, v, i + 1) for i, v in enumerate(lsVals)])
    standardTable(oDb, sTable, lsData, dTypes, lsData[:3], True)
    iSkipped = 0
    for r in llRows:
        dRow = dict(zip(lsFields, r))
        lsCols = lsData + [s for s in ('url', 'notes', 'tags') if s in lsFields]
        lsVals = [None if not dRow[s].strip() else (int(dRow[s]) if dTypes[s] == 'INTEGER' else float(dRow[s]) if dTypes[s] == 'REAL' else dRow[s]) for s in lsCols]
        oCur = oDb.execute('INSERT OR IGNORE INTO %s (%s) VALUES (%s)' % (q(sTable), ', '.join(q(s) for s in lsCols), ', '.join('?' * len(lsCols))), lsVals)
        if oCur.rowcount == 0: iSkipped += 1
    oDb.commit()
    oDb.close()
    print('%s: %d %s in table %s%s' % (os.path.basename(sOut), len(llRows) - iSkipped, 'record' if len(llRows) - iSkipped == 1 else 'records', sTable,
        '; %d duplicate %s left out' % (iSkipped, 'row' if iSkipped == 1 else 'rows') if iSkipped else ''))
else:
    oDb = sqlite3.connect('file:' + os.path.abspath(sIn).replace('\\', '/') + '?mode=ro', uri=True)
    lsOut = ['# ' + os.path.splitext(os.path.basename(sIn))[0], '']
    for (sTable,) in oDb.execute(""SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name COLLATE NOCASE""):
        # DbDo's own tables are kept off every list, as DbDo keeps them.
        if sTable in ('lookups', 'maps', 'views'): continue
        oCursor = oDb.execute('SELECT * FROM %s' % q(sTable))
        lsFields = [d[0] for d in oCursor.description]
        llRows = oCursor.fetchall()
        # A DbDo table gives its data: not its id, its times, look, prime or marked, nor url, notes or tags left empty.
        bDbDo = 'prime' in lsFields and 'look' in lsFields
        lsKeep = [i for i, s in enumerate(lsFields) if not bDbDo or (s not in lsHousekeeping and s != singular(sTable) + '_id'
            and not (s in ('url', 'notes', 'tags') and not any(r[i] not in (None, '') for r in llRows)))]
        lsOut += ['## ' + sTable, '', '| ' + ' | '.join(cell(lsFields[i]) for i in lsKeep) + ' |', '|' + ' --- |' * len(lsKeep)]
        lsOut += ['| ' + ' | '.join(cell(r[i]) for i in lsKeep) + ' |' for r in llRows]
        lsOut.append('')
    oDb.close()
    open(sOut, 'w', encoding='utf-8-sig', newline='\r\n').write('\n'.join(lsOut))
";

private const string sPyMuPdfText =
"import sys\n" +
"try:\n    import pymupdf\nexcept ImportError:\n    import fitz as pymupdf\n" +
"oDoc = pymupdf.open(sys.argv[1])\n" +
"lsPages = [oPage.get_text() for oPage in oDoc]\n" +
"open(sys.argv[2], 'w', encoding='utf-8-sig').write('\\n\\n'.join(s.strip() for s in lsPages))\n";

private const string sPyMuPdfMarkdown =
"import sys\nimport pymupdf4llm\n" +
"open(sys.argv[2], 'w', encoding='utf-8-sig').write(pymupdf4llm.to_markdown(sys.argv[1]))\n";

private static bool runPython(string sCode, string sSource, string sTarget, out string sError) {
string sPython = pythonProgram();
if (sPython == "") { sError = "Python is not installed; installPdfTools.cmd installs it with the PDF readers"; return false; }
string sScript = Path.Combine(Path.GetTempPath(), "homerConversion_" + Guid.NewGuid().ToString("N").Substring(0, 8) + ".py");
try {
File.WriteAllText(sScript, sCode, new UTF8Encoding(false));
string sOut;
bool bRan = run(sPython, Util.stringQuote(sScript) + " " + Util.stringQuote(sSource) + " " + Util.stringQuote(sTarget), out sOut, out sError);
if (!bRan && sError.IndexOf("No module named", StringComparison.OrdinalIgnoreCase) >= 0)
sError = lastLine(sError) + ". installPdfTools.cmd installs the PDF readers";
return bRan;
}
finally { try { File.Delete(sScript); } catch (Exception) { } }
} // runPython method

private static string sPythonCache = null;

public static string pythonProgram() {
if (sPythonCache != null) return sPythonCache;
List<string> lsKnown = new List<string>();
foreach (string sVersion in new string[] { "313", "312", "311", "314" }) {
lsKnown.Add(Environment.ExpandEnvironmentVariables(@"%LOCALAPPDATA%\Programs\Python\Python" + sVersion + @"\python.exe"));
lsKnown.Add(Environment.ExpandEnvironmentVariables(@"%ProgramFiles%\Python" + sVersion + @"\python.exe"));
}
sPythonCache = findProgram("python.exe", lsKnown.ToArray());
return sPythonCache;
} // pythonProgram method

// ------- engine: zipxml -------

// zipXml: the text of a Word, PowerPoint, Excel or OpenDocument file, read from
// the XML inside it. No program starts, so this is the quickest way; for
// Markdown, headings come from Word's heading styles and slides get a heading
// each.
private static bool zipXml(string sSource, string sTarget, out string sError) {
sError = "";
string sFrom = typeOf(sSource);
bool bMarkdown = typeOf(sTarget) == "md";
StringBuilder sb = new StringBuilder();
using (System.IO.Compression.ZipArchive zip = System.IO.Compression.ZipFile.OpenRead(sSource)) {
if (sFrom == "docx") {
string sXml = entryText(zip, "word/document.xml");
foreach (Match oPara in Regex.Matches(sXml, @"<w:p[ >].*?</w:p>", RegexOptions.Singleline)) {
string sLine = runText(oPara.Value, @"<w:t(?:\s[^>]*)?>(.*?)</w:t>", "");
if (sLine.Trim().Length == 0) continue;
Match oStyle = Regex.Match(oPara.Value, "<w:pStyle w:val=\"(?:Heading|heading)\\s?(\\d)\"");
if (bMarkdown && oStyle.Success) sLine = new string('#', int.Parse(oStyle.Groups[1].Value)) + " " + sLine;
sb.Append(sLine.Trim()).Append("\r\n\r\n");
}
}
else if (sFrom == "pptx") {
List<string> lsSlides = new List<string>();
foreach (System.IO.Compression.ZipArchiveEntry e in zip.Entries)
if (Regex.IsMatch(e.FullName, @"^ppt/slides/slide\d+\.xml$", RegexOptions.IgnoreCase)) lsSlides.Add(e.FullName);
lsSlides.Sort(delegate(string a, string b) { return numberIn(a).CompareTo(numberIn(b)); });
foreach (string sName in lsSlides) {
string sText = runText(entryText(zip, sName), @"<a:t>(.*?)</a:t>", " ");
if (sText.Trim().Length == 0) continue;
if (bMarkdown) sb.Append("## Slide " + numberIn(sName) + "\r\n\r\n");
sb.Append(sText.Trim()).Append("\r\n\r\n");
}
}
else if (sFrom == "xlsx") {
foreach (Match oString in Regex.Matches(entryText(zip, "xl/sharedStrings.xml"), @"<si>(.*?)</si>", RegexOptions.Singleline))
sb.Append(runText(oString.Groups[1].Value, @"<t(?:\s[^>]*)?>(.*?)</t>", "")).Append("\r\n");
}
else if (sFrom == "odt" || sFrom == "odp" || sFrom == "ods") {
string sXml = entryText(zip, "content.xml");
foreach (Match oPara in Regex.Matches(sXml, @"<text:(h|p)\b([^>]*)>(.*?)</text:\1>", RegexOptions.Singleline)) {
string sLine = unescape(Regex.Replace(oPara.Groups[3].Value, "<[^>]+>", ""));
if (sLine.Trim().Length == 0) continue;
Match oLevel = Regex.Match(oPara.Groups[2].Value, "outline-level=\"(\\d)\"");
if (bMarkdown && oPara.Groups[1].Value == "h") sLine = new string('#', oLevel.Success ? int.Parse(oLevel.Groups[1].Value) : 1) + " " + sLine;
sb.Append(sLine.Trim()).Append("\r\n\r\n");
}
}
else { sError = "zipxml does not read " + sFrom + " files"; return false; }
}
if (sb.ToString().Trim().Length == 0) { sError = "no text was found inside " + Path.GetFileName(sSource); return false; }
File.WriteAllText(sTarget, sb.ToString().TrimEnd() + "\r\n", new UTF8Encoding(true));
return true;
} // zipXml method

private static string entryText(System.IO.Compression.ZipArchive zip, string sName) {
foreach (System.IO.Compression.ZipArchiveEntry e in zip.Entries) {
if (String.Compare(e.FullName.Replace('\\', '/'), sName, true) != 0) continue;
using (StreamReader oReader = new StreamReader(e.Open(), Encoding.UTF8)) return oReader.ReadToEnd();
}
return "";
} // entryText method

private static string runText(string sXml, string sPattern, string sJoin) {
StringBuilder sb = new StringBuilder();
foreach (Match oRun in Regex.Matches(sXml, sPattern, RegexOptions.Singleline)) {
if (sb.Length > 0) sb.Append(sJoin);
sb.Append(unescape(oRun.Groups[1].Value));
}
return Regex.Replace(sb.ToString(), "[ \t]{2,}", " ");
} // runText method

private static string unescape(string s) {
return s.Replace("&lt;", "<").Replace("&gt;", ">").Replace("&quot;", "\"").Replace("&apos;", "'").Replace("&amp;", "&");
} // unescape method

private static int numberIn(string sName) {
Match oDigits = Regex.Match(sName, @"(\d+)\.xml$", RegexOptions.IgnoreCase);
int i = int.MaxValue;
if (oDigits.Success) int.TryParse(oDigits.Groups[1].Value, out i);
return i;
} // numberIn method

// ------- engine: table -------

private static bool tableEngine(string sSource, string sTarget, out string sError) {
Table oTable = Table.read(sSource, out sError);
if (oTable == null || oTable.fieldCount() == 0) {
if (sError == "") sError = "no table was found in " + Path.GetFileName(sSource);
return false;
}
if (typeOf(sTarget) == "txt") {
File.WriteAllText(sTarget, oTable.markdownText(), new UTF8Encoding(true));
return true;
}
return oTable.write(sTarget, out sError);
} // tableEngine method

// ------- engine: markdown, a web page without Pandoc (kit 1.81.0) -------
//
// WHY. A PDF became a web page only through Pandoc, so an app that had always made
// its pages itself -- bookFido, from Audible's companion PDFs -- could not move onto the
// kit's one conversion technique without needing Pandoc on every computer. This writes
// the Markdown the kit makes (PdfReader, Table, zipxml) as an accessible page: headings,
// paragraphs, bullet and numbered lists, pipe tables, quotes, fenced code, rules, and
// inline links, images with their alt text, bold, italic and code. It is a second way
// after Pandoc, never in place of it, so a computer with Pandoc keeps Pandoc's page.
// The page: lang and title from front matter (title:, lang:), else the first heading,
// else the file name; the body inside main, as every Homer page is.
private static bool markdownToHtml(string sSource, string sTarget, out string sError) {
sError = "";
try {
string sText = decodeText(File.ReadAllBytes(sSource)).Replace("\r\n", "\n").Replace("\r", "\n");
string sTitle = "", sLang = "en";
string[] aLines = sText.Split('\n');
int iAt = 0;
if (aLines.Length > 0 && aLines[0].Trim() == "---") {
for (iAt = 1; iAt < aLines.Length && aLines[iAt].Trim() != "---"; iAt++) {
Match oMeta = Regex.Match(aLines[iAt], @"^\s*(title|lang)\s*:\s*""?(.*?)""?\s*$", RegexOptions.IgnoreCase);
if (!oMeta.Success) continue;
if (oMeta.Groups[1].Value.ToLowerInvariant() == "title") sTitle = oMeta.Groups[2].Value; else sLang = oMeta.Groups[2].Value;
}
iAt++;
}
StringBuilder oBody = new StringBuilder();
List<string> lsPara = new List<string>();
string sList = "";
Action closeList = delegate() { if (sList != "") { oBody.Append("</" + sList + ">\r\n"); sList = ""; } };
Action flush = delegate() {
if (lsPara.Count == 0) return;
oBody.Append("<p>" + markdownInline(string.Join(" ", lsPara.ToArray())) + "</p>\r\n");
lsPara.Clear();
};
for (int i = iAt; i < aLines.Length; i++) {
string sLine = aLines[i];
string sTrim = sLine.Trim();
if (sTrim.StartsWith("```")) {
flush(); closeList();
StringBuilder oCode = new StringBuilder();
for (i++; i < aLines.Length && !aLines[i].Trim().StartsWith("```"); i++) oCode.Append(htmlEscape(aLines[i]) + "\r\n");
oBody.Append("<pre><code>" + oCode + "</code></pre>\r\n");
continue;
}
if (sTrim == "") { flush(); closeList(); continue; }
Match oHead = Regex.Match(sTrim, @"^(#{1,6})\s+(.*?)\s*#*$");
if (oHead.Success) {
flush(); closeList();
int iLevel = oHead.Groups[1].Value.Length;
if (sTitle == "" && iLevel == 1) sTitle = Regex.Replace(oHead.Groups[2].Value, @"[*_`]", "");
oBody.Append("<h" + iLevel + ">" + markdownInline(oHead.Groups[2].Value) + "</h" + iLevel + ">\r\n");
continue;
}
if (Regex.IsMatch(sTrim, @"^(\*\s*\*\s*\*|-\s*-\s*-|_\s*_\s*_)[\s*_-]*$")) { flush(); closeList(); oBody.Append("<hr>\r\n"); continue; }
if (sTrim.StartsWith("|") && i + 1 < aLines.Length && Regex.IsMatch(aLines[i + 1].Trim(), @"^\|?\s*:?-{1,}:?\s*(\|\s*:?-{1,}:?\s*)*\|?$")) {
flush(); closeList();
oBody.Append("<table>\r\n<thead><tr>");
foreach (string sCell in markdownCells(sTrim)) oBody.Append("<th scope=\"col\">" + markdownInline(sCell) + "</th>");
oBody.Append("</tr></thead>\r\n<tbody>\r\n");
for (i += 2; i < aLines.Length && aLines[i].Trim().StartsWith("|"); i++) {
oBody.Append("<tr>");
foreach (string sCell in markdownCells(aLines[i].Trim())) oBody.Append("<td>" + markdownInline(sCell) + "</td>");
oBody.Append("</tr>\r\n");
}
i--;
oBody.Append("</tbody>\r\n</table>\r\n");
continue;
}
Match oBullet = Regex.Match(sLine, @"^\s*[-*+]\s+(.*)$");
Match oNumber = Regex.Match(sLine, @"^\s*\d+[.)]\s+(.*)$");
if (oBullet.Success || oNumber.Success) {
flush();
string sKind = oBullet.Success ? "ul" : "ol";
if (sList != sKind) { closeList(); oBody.Append("<" + sKind + ">\r\n"); sList = sKind; }
oBody.Append("<li>" + markdownInline((oBullet.Success ? oBullet : oNumber).Groups[1].Value) + "</li>\r\n");
continue;
}
if (sTrim.StartsWith(">")) { flush(); closeList(); oBody.Append("<blockquote><p>" + markdownInline(sTrim.TrimStart('>').Trim()) + "</p></blockquote>\r\n"); continue; }
closeList();
lsPara.Add(sTrim);
}
flush(); closeList();
if (sTitle == "") sTitle = Path.GetFileNameWithoutExtension(sSource);
string sPage = "<!DOCTYPE html>\r\n<html lang=\"" + htmlEscape(sLang) + "\">\r\n<head>\r\n<meta charset=\"utf-8\">\r\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\r\n"
+ "<title>" + htmlEscape(sTitle) + "</title>\r\n</head>\r\n<body>\r\n<main>\r\n" + oBody + "</main>\r\n</body>\r\n</html>\r\n";
File.WriteAllText(sTarget, sPage, new UTF8Encoding(true));
return true;
}
catch (Exception oError) { sError = "the Markdown could not be written as a web page: " + oError.Message; return false; }
} // markdownToHtml method

private static string[] markdownCells(string sRow) {
string s = sRow.Trim();
if (s.StartsWith("|")) s = s.Substring(1);
if (s.EndsWith("|") && !s.EndsWith("\\|")) s = s.Substring(0, s.Length - 1);
string[] aCells = Regex.Split(s, @"(?<!\\)\|");
for (int i = 0; i < aCells.Length; i++) aCells[i] = aCells[i].Trim().Replace("\\|", "|");
return aCells;
} // markdownCells method

// markdownInline: code spans first, kept literal; then images, links, bold and italic.
private static string markdownInline(string sText) {
List<string> lsCode = new List<string>();
string s = Regex.Replace(sText, @"`([^`]+)`", delegate(Match m) { lsCode.Add(m.Groups[1].Value); return "\u0001" + (lsCode.Count - 1) + "\u0002"; });
// An escaped character is set aside too, so \*not\* stays two asterisks, not italics.
List<string> lsEscaped = new List<string>();
s = Regex.Replace(s, @"\\([\\`*_{}\[\]()#+\-.!|>])", delegate(Match m) { lsEscaped.Add(m.Groups[1].Value); return "\u0003" + (lsEscaped.Count - 1) + "\u0004"; });
s = htmlEscape(s);
s = Regex.Replace(s, @"!\[([^\]]*)\]\(([^)\s]+)(?:\s+&quot;[^&]*&quot;)?\)", "<img src=\"$2\" alt=\"$1\">");
s = Regex.Replace(s, @"\[([^\]]+)\]\(([^)\s]+)(?:\s+&quot;[^&]*&quot;)?\)", "<a href=\"$2\">$1</a>");
s = Regex.Replace(s, @"(\*\*|__)(?=\S)(.+?)(?<=\S)\1", "<strong>$2</strong>");
s = Regex.Replace(s, @"(?<![\w*])\*(?=\S)(.+?)(?<=\S)\*(?![\w*])", "<em>$1</em>");
s = Regex.Replace(s, @"(?<![\w_])_(?=\S)(.+?)(?<=\S)_(?![\w_])", "<em>$1</em>");
s = Regex.Replace(s, "\u0003(\\d+)\u0004", delegate(Match m) { return htmlEscape(lsEscaped[int.Parse(m.Groups[1].Value)]); });
s = Regex.Replace(s, "\u0001(\\d+)\u0002", delegate(Match m) { return "<code>" + htmlEscape(lsCode[int.Parse(m.Groups[1].Value)]) + "</code>"; });
return s;
} // markdownInline method

private static string htmlEscape(string s) {
return (s ?? "").Replace("&", "&amp;").Replace("<", "&lt;").Replace(">", "&gt;").Replace("\"", "&quot;");
} // htmlEscape method

// ------- engine: officecom, the last resort -------

// Office's own numbers for the formats it saves, named rather than written bare.
private const int iWordFormatDoc = 0, iWordFormatDocx = 16, iWordFormatFilteredHtml = 10, iWordFormatOdt = 23, iWordFormatPdf = 17, iWordFormatRtf = 6, iWordFormatUnicodeText = 7;
private const int iExcelFormatCsvUtf8 = 62, iExcelFormatHtml = 44, iExcelFormatXlsx = 51;
private const int iPowerPointFormatPdf = 32, iPowerPointFormatPptx = 24;
private const int iMsoFalse = 0, iMsoTrue = -1;

// bAlertBoxes: a program with windows shows an Alert box when Office is needed
// and missing; a console program sets this false and gets the words in sError.
public static bool bAlertBoxes = true;
private static List<string> lsAlerted = new List<string>();

private static string officeApp(string sSource) {
string sFrom = typeOf(sSource);
if (sFrom == "doc" || sFrom == "docx" || sFrom == "rtf" || sFrom == "odt" || sFrom == "pdf" || sFrom == "htm" || sFrom == "txt") return "Word";
if (sFrom == "xls" || sFrom == "xlsx" || sFrom == "csv") return "Excel";
if (sFrom == "ppt" || sFrom == "pptx") return "PowerPoint";
return "";
} // officeApp method

public static bool haveOffice(string sApp) {
try { return Type.GetTypeFromProgID(sApp + ".Application") != null; }
catch (Exception) { return false; }
} // haveOffice method

private static bool officeCom(string sSource, string sTarget, out string sError) {
sError = "";
string sApp = officeApp(sSource);
string sTo = typeOf(sTarget);
if (!haveOffice(sApp)) {
string sSaveAs = typeOf(sSource) == "doc" ? ".docx" : typeOf(sSource) == "xls" ? ".xlsx" : typeOf(sSource) == "ppt" ? ".pptx" : "";
sError = "Converting " + Path.GetFileName(sSource) + " needs Microsoft " + sApp + ", which is not installed. No free reader for this format is approved."
+ (sSaveAs != "" ? " Saving the file as " + sSaveAs + " on a computer with Office avoids this; Homer reads " + sSaveAs + " without Office." : "");
alert(sApp, sError);
return false;
}
Log.info("Conversion: Microsoft " + sApp + " by COM, the last resort, for " + Path.GetFileName(sSource));
object oApp = null;
try {
oApp = Activator.CreateInstance(Type.GetTypeFromProgID(sApp + ".Application"));
string sFull = Path.GetFullPath(sSource), sOut = Path.GetFullPath(sTarget);
if (sApp == "Word") {
setProp(oApp, "DisplayAlerts", 0);
object oDocs = getProp(oApp, "Documents");
object oDoc = call(oDocs, "Open", sFull, false, true);
// .doc, .rtf and .odt as well (kit 1.76.0), for an editor's Export to a 1997 Word file.
int iFormat = sTo == "doc" ? iWordFormatDoc : sTo == "docx" ? iWordFormatDocx : sTo == "htm" ? iWordFormatFilteredHtml
: sTo == "odt" ? iWordFormatOdt : sTo == "pdf" ? iWordFormatPdf : sTo == "rtf" ? iWordFormatRtf : iWordFormatUnicodeText;
// A TAGGED PDF (kit 1.91.0): Word's export with its structure tags and heading bookmarks, rather
// than Save As, whose tags depend on the last choice someone made in Word's own dialog.
if (iFormat == iWordFormatPdf) call(oDoc, "ExportAsFixedFormat", sOut, iFormat, false, 0, 0, 1, 1, 0, true, true, 1, true, true, false);
else call(oDoc, "SaveAs2", sOut, iFormat);
call(oDoc, "Close", false);
// WORD'S TEXT IN THE HOMER ENCODING (1.76.1): Word writes UTF-16 from some documents and the
// Windows code page from others, so its text is rewritten as UTF-8 with a byte order mark.
if (iFormat == iWordFormatUnicodeText && File.Exists(sOut)) File.WriteAllText(sOut, decodeText(File.ReadAllBytes(sOut)), new UTF8Encoding(true));
}
else if (sApp == "Excel") {
setProp(oApp, "DisplayAlerts", false);
object oBook = call(getProp(oApp, "Workbooks"), "Open", sFull);
int iFormat = sTo == "xlsx" ? iExcelFormatXlsx : sTo == "htm" ? iExcelFormatHtml : iExcelFormatCsvUtf8;
string sSaveTo = sTo == "txt" ? Path.ChangeExtension(sOut, ".csv") : sOut;
call(oBook, "SaveAs", sSaveTo, iFormat);
call(oBook, "Close", false);
if (sSaveTo != sOut) File.Move(sSaveTo, sOut);
}
else {
object oShow = call(getProp(oApp, "Presentations"), "Open", sFull, iMsoTrue, iMsoFalse, iMsoFalse);
if (sTo == "txt" || sTo == "md") {
string sPptx = tempPath(sSource, ".pptx");
call(oShow, "SaveAs", sPptx, iPowerPointFormatPptx);
call(oShow, "Close");
try { return zipXml(sPptx, sTarget, out sError); }
finally { try { File.Delete(sPptx); } catch (Exception) { } }
}
call(oShow, "SaveAs", sOut, sTo == "pdf" ? iPowerPointFormatPdf : iPowerPointFormatPptx);
call(oShow, "Close");
}
return File.Exists(sTarget);
}
catch (Exception ex) {
sError = "Microsoft " + sApp + " could not convert it: " + (ex.InnerException != null ? ex.InnerException.Message : ex.Message);
return false;
}
finally {
if (oApp != null) {
try { call(oApp, "Quit"); } catch (Exception) { }
try { System.Runtime.InteropServices.Marshal.FinalReleaseComObject(oApp); } catch (Exception) { }
}
}
} // officeCom method

// decodeText: text from bytes whose encoding is not promised: the byte order mark
// first, then UTF-8 if every byte fits, then the Windows code page.
public static string decodeText(byte[] ab) {
if (ab.Length >= 2 && ((ab[0] == 0xFF && ab[1] == 0xFE) || (ab[0] == 0xFE && ab[1] == 0xFF))) return new StreamReader(new MemoryStream(ab), true).ReadToEnd();
if (ab.Length >= 3 && ab[0] == 0xEF && ab[1] == 0xBB && ab[2] == 0xBF) return new UTF8Encoding(false).GetString(ab, 3, ab.Length - 3);
try { return new UTF8Encoding(false, true).GetString(ab); }
catch (DecoderFallbackException) { return Encoding.Default.GetString(ab); }
} // decodeText method

// alert: once per Office program per session, so a batch of twenty legacy files
// brings one box, not twenty. Every later case is still logged and returned.
private static void alert(string sApp, string sText) {
Log.warn("Alert: " + sText);
if (!bAlertBoxes || lsAlerted.Contains(sApp)) return;
lsAlerted.Add(sApp);
try { MessageBox.Show(sText, "Alert", MessageBoxButtons.OK, MessageBoxIcon.Warning); }
catch (Exception) { }
} // alert method

private static object getProp(object o, string sName) {
return o.GetType().InvokeMember(sName, BindingFlags.GetProperty, null, o, null);
} // getProp method

private static void setProp(object o, string sName, object oValue) {
o.GetType().InvokeMember(sName, BindingFlags.SetProperty, null, o, new object[] { oValue });
} // setProp method

private static object call(object o, string sName, params object[] aArgs) {
return o.GetType().InvokeMember(sName, BindingFlags.InvokeMethod, null, o, aArgs);
} // call method

// ------- running a program -------

private const int iConverterMinutes = 15;

private static string findProgram(string sExe, string[] aKnown) {
foreach (string sTry in aKnown) if (sTry.Length > 0 && File.Exists(sTry)) return sTry;
string sPath = Environment.GetEnvironmentVariable("PATH") ?? "";
foreach (string sDir in sPath.Split(';')) {
if (sDir.Trim().Length == 0 || sDir.IndexOf("WindowsApps", StringComparison.OrdinalIgnoreCase) >= 0) continue;
try {
string sTry = Path.Combine(sDir.Trim(), sExe);
if (File.Exists(sTry)) return sTry;
}
catch (Exception) { }
}
return "";
} // findProgram method

private static bool run(string sExe, string sArguments, out string sOut, out string sError) {
sOut = ""; sError = "";
try {
ProcessStartInfo oInfo = new ProcessStartInfo(sExe, sArguments);
oInfo.UseShellExecute = false;
oInfo.CreateNoWindow = true;
oInfo.RedirectStandardOutput = true;
oInfo.RedirectStandardError = true;
using (Process oProcess = Process.Start(oInfo)) {
System.Threading.Tasks.Task<string> oErr = oProcess.StandardError.ReadToEndAsync();
System.Threading.Tasks.Task<string> oOut = oProcess.StandardOutput.ReadToEndAsync();
if (!oProcess.WaitForExit(iConverterMinutes * 60 * 1000)) {
try { oProcess.Kill(); } catch (Exception) { }
sError = Path.GetFileName(sExe) + " was still running after " + iConverterMinutes + " minutes, so it was stopped";
Log.warn("Stopped after " + iConverterMinutes + " minutes: " + sExe + " " + sArguments);
return false;
}
oProcess.WaitForExit();
sOut = oOut.Result;
string sErr = oErr.Result;
Log.command(sExe + " " + sArguments, oProcess.ExitCode);
if (!String.IsNullOrEmpty(sErr)) Log.info("  said: " + sErr.Trim());
if (oProcess.ExitCode != 0) {
sError = sErr.Trim().Length > 0 ? lastLine(sErr) : Path.GetFileName(sExe) + " returned " + oProcess.ExitCode;
return false;
}
}
return true;
}
catch (Exception ex) {
sError = ex.Message;
Log.info("Could not start " + sExe + ": " + ex.Message);
return false;
}
} // run method

// ------- accessible output (kit 1.91.0) -------
//
// EVERY FILE A HOMER APP MAKES IS FINISHED FOR A SCREEN READER, then checked (the author's rule of 24
// October 2026). Whatever engine wrote it -- the kit's own writers, Pandoc, Edge or Office -- the file is
// opened once more and given what extCheck would otherwise report as missing, and what cannot be fixed
// without a person is logged under extCheck's own rule names, so a log reads like an extCheck report:
//
//   xlsx  header names for every table region (below), a frozen header row, a sheet name for a lone
//         default sheet, and the workbook's title, author and language
//   docx  title, author and language, and the document language in its default style
//   pptx  title, author and language
//   epub  a title and a language in the package
//   md    YAML front matter with title and lang, when it has none
//   htm   the Homer page form, as before (ConversionPage): one H1, main, lang and title
//   pdf   tagged, from an htm that has lang and title (Edge), or Word's export with structure tags
//
// HEADER NAMES IN A WORKBOOK, from the author's xlHeaders.vbs (2024), improved. JAWS and NVDA read a
// region's column or row headers when the region's top-left cell carries a workbook name beginning
// ColumnTitle, RowTitle or Title (both). xlHeaders drove Excel to find the regions and test them; here
// the file's own XML is read, so no Office is needed. A region is a rectangle of filled cells bounded by
// blank rows and columns, as Excel's CurrentRegion. A region of at least two rows and two columns has
// column headers when every cell of its top row is filled, is text and is unique (ignoring case); row
// headers likewise down its first column. Two improvements on xlHeaders: an EMPTY TOP-LEFT CORNER no
// longer hides a two-way table -- the top row is tested from the second column and the first column
// from the second row, and both passing makes a Title -- and a header must be TEXT, so a row of unique
// numbers is not taken for headers. A region whose top-left cell already has a name keeps it; a new
// name takes the next free two-digit number, ColumnTitle01, ColumnTitle02.

private static readonly Regex rxCell = new Regex("<c\\b([^>]*?)(?:/>|>(.*?)</c>)", RegexOptions.Singleline);
private static readonly Regex rxAttr = new Regex("\\b([A-Za-z:]+)=\"([^\"]*)\"");
private static readonly Regex rxT = new Regex("<t\\b[^>]*>(.*?)</t>", RegexOptions.Singleline);

// finishOutput: the step every route ends with. Never fails a conversion: a finishing problem is logged.
public static bool finishOutput(string sPath) {
string sType = typeOf(sPath);
try {
List<string> lsFindings = new List<string>();
if (sType == "xlsx") finishXlsx(sPath, lsFindings);
else if (sType == "docx") finishOffice(sPath, "word", lsFindings);
else if (sType == "pptx") finishOffice(sPath, "ppt", lsFindings);
else if (sType == "epub") finishEpub(sPath, lsFindings);
else if (sType == "md") finishMarkdown(sPath, lsFindings);
else if (sType == "htm") checkPage(sPath, lsFindings);
foreach (string sFinding in lsFindings) Log.info("Quality " + Path.GetFileName(sPath) + ": " + sFinding);
return true;
}
catch (Exception oError) { Log.warn("Finishing " + Path.GetFileName(sPath) + " for a screen reader failed: " + oError.Message); return false; }
} // finishOutput method

// documentTitle: a title from a file's name, when it has none of its own.
public static string documentTitle(string sPath) {
string sStem = Path.GetFileNameWithoutExtension(sPath).Replace('_', ' ').Trim();
return sStem.Length == 0 ? "Untitled" : sStem;
} // documentTitle method

public static string documentLanguage() {
string sName = System.Globalization.CultureInfo.CurrentUICulture.Name;
return string.IsNullOrEmpty(sName) ? "en-US" : sName;
} // documentLanguage method

public static string documentAuthor() {
return Environment.UserName ?? "";
} // documentAuthor method

private static string xmlEscape(string s) {
return (s ?? "").Replace("&", "&amp;").Replace("<", "&lt;").Replace(">", "&gt;").Replace("\"", "&quot;");
} // xmlEscape method

private static string xmlText(string s) {
return System.Net.WebUtility.HtmlDecode(s ?? "");
} // xmlText method

// The package as names and texts, so a part can be read and replaced and the whole written back.
private static List<string> readPackage(string sPath, Dictionary<string, byte[]> dParts) {
List<string> lsOrder = new List<string>();
using (FileStream oFile = File.OpenRead(sPath))
using (System.IO.Compression.ZipArchive zip = new System.IO.Compression.ZipArchive(oFile, System.IO.Compression.ZipArchiveMode.Read)) {
foreach (System.IO.Compression.ZipArchiveEntry entry in zip.Entries) {
using (Stream oIn = entry.Open()) using (MemoryStream oBuffer = new MemoryStream()) { oIn.CopyTo(oBuffer); dParts[entry.FullName] = oBuffer.ToArray(); }
lsOrder.Add(entry.FullName);
}
}
return lsOrder;
} // readPackage method

private static void writePackage(string sPath, List<string> lsOrder, Dictionary<string, byte[]> dParts) {
string sTemp = sPath + ".finishing";
if (File.Exists(sTemp)) File.Delete(sTemp);
using (FileStream oOut = File.Create(sTemp))
using (System.IO.Compression.ZipArchive zip = new System.IO.Compression.ZipArchive(oOut, System.IO.Compression.ZipArchiveMode.Create)) {
foreach (string sName in lsOrder) {
// An EPUB's mimetype stays first and unpacked, as the standard asks.
System.IO.Compression.CompressionLevel oLevel = sName == "mimetype" ? System.IO.Compression.CompressionLevel.NoCompression : System.IO.Compression.CompressionLevel.Optimal;
using (Stream oIn = zip.CreateEntry(sName, oLevel).Open()) oIn.Write(dParts[sName], 0, dParts[sName].Length);
}
}
File.Copy(sTemp, sPath, true);
File.Delete(sTemp);
} // writePackage method

private static string partText(Dictionary<string, byte[]> dParts, string sName) {
byte[] ab;
return dParts.TryGetValue(sName, out ab) ? Encoding.UTF8.GetString(ab).TrimStart('\uFEFF') : "";
} // partText method

private static void setPart(Dictionary<string, byte[]> dParts, List<string> lsOrder, string sName, string sText) {
if (!dParts.ContainsKey(sName)) lsOrder.Add(sName);
dParts[sName] = Encoding.UTF8.GetBytes(sText);
} // setPart method

// ensureCoreProperties: docProps/core.xml with a title, an author and a language, made when missing.
private static bool ensureCoreProperties(Dictionary<string, byte[]> dParts, List<string> lsOrder, string sTitle, List<string> lsFindings) {
string sCore = partText(dParts, "docProps/core.xml");
string sLanguage = documentLanguage(), sAuthor = documentAuthor();
if (sCore == "") {
sCore = "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?><cp:coreProperties xmlns:cp=\"http://schemas.openxmlformats.org/package/2006/metadata/core-properties\" xmlns:dc=\"http://purl.org/dc/elements/1.1/\" xmlns:dcterms=\"http://purl.org/dc/terms/\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"></cp:coreProperties>";
string sTypes = partText(dParts, "[Content_Types].xml");
if (sTypes.IndexOf("/docProps/core.xml", StringComparison.Ordinal) < 0)
setPart(dParts, lsOrder, "[Content_Types].xml", sTypes.Replace("</Types>", "<Override PartName=\"/docProps/core.xml\" ContentType=\"application/vnd.openxmlformats-package.core-properties+xml\"/></Types>"));
string sRels = partText(dParts, "_rels/.rels");
if (sRels.IndexOf("core-properties", StringComparison.Ordinal) < 0)
setPart(dParts, lsOrder, "_rels/.rels", sRels.Replace("</Relationships>", "<Relationship Id=\"rIdHomerCore\" Type=\"http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties\" Target=\"docProps/core.xml\"/></Relationships>"));
}
string[,] aWanted = { { "dc:title", sTitle, "MissingDocumentTitle" }, { "dc:creator", sAuthor, "MissingAuthor" }, { "dc:language", sLanguage, "MissingDocumentLanguage" } };
for (int i = 0; i < aWanted.GetLength(0); i++) {
string sTag = aWanted[i, 0];
Match oHas = Regex.Match(sCore, "<" + sTag + "(?:\\s[^>]*)?>(.*?)</" + sTag + ">", RegexOptions.Singleline);
if (oHas.Success && xmlText(oHas.Groups[1].Value).Trim().Length > 0) continue;
if (aWanted[i, 1] == "") { lsFindings.Add(aWanted[i, 2] + ": left blank, nothing to fill it with"); continue; }
string sElement = "<" + sTag + ">" + xmlEscape(aWanted[i, 1]) + "</" + sTag + ">";
sCore = oHas.Success ? sCore.Substring(0, oHas.Index) + sElement + sCore.Substring(oHas.Index + oHas.Length)
: Regex.Replace(sCore, "<" + sTag + "\\s*/>", "") .Replace("</cp:coreProperties>", sElement + "</cp:coreProperties>");
lsFindings.Add(aWanted[i, 2] + ": fixed, " + sTag + " set to " + aWanted[i, 1]);
}
setPart(dParts, lsOrder, "docProps/core.xml", sCore);
return true;
} // ensureCoreProperties method

// finishOffice: a Word or PowerPoint file's properties, its language, and what extCheck would report.
private static bool finishOffice(string sPath, string sKind, List<string> lsFindings) {
Dictionary<string, byte[]> dParts = new Dictionary<string, byte[]>();
List<string> lsOrder = readPackage(sPath, dParts);
string sTitle = "";
if (sKind == "word") {
string sBody = partText(dParts, "word/document.xml");
// The title is the Title paragraph, else the first heading, else the file's name.
foreach (Match oPara in Regex.Matches(sBody, "<w:p\\b.*?</w:p>", RegexOptions.Singleline)) {
Match oStyle = Regex.Match(oPara.Value, "<w:pStyle w:val=\"([^\"]+)\"");
if (!oStyle.Success) continue;
string sStyle = oStyle.Groups[1].Value.ToLowerInvariant();
if (sStyle != "title" && !sStyle.StartsWith("heading")) continue;
StringBuilder sbText = new StringBuilder();
foreach (Match oRun in Regex.Matches(oPara.Value, "<w:t\\b[^>]*>(.*?)</w:t>", RegexOptions.Singleline)) sbText.Append(xmlText(oRun.Groups[1].Value));
if (sbText.ToString().Trim().Length > 0) { sTitle = sbText.ToString().Trim(); break; }
}
if (!Regex.IsMatch(sBody, "<w:pStyle w:val=\"(?:[Hh]eading|Title)")) lsFindings.Add("NoHeadings: the document has no headings, so a screen reader cannot move by them");
foreach (Match oPicture in Regex.Matches(sBody, "<wp:docPr\\b[^>]*>"))
if (!Regex.IsMatch(oPicture.Value, "\\bdescr=\"[^\"]+\"")) lsFindings.Add("MissingAltText: a picture has no alternative text");
// The language of the default style, so every run of text is read in it.
string sStyles = partText(dParts, "word/styles.xml");
Match oDefault = Regex.Match(sStyles, "<w:rPrDefault>\\s*<w:rPr>(.*?)</w:rPr>", RegexOptions.Singleline);
if (oDefault.Success && oDefault.Groups[1].Value.IndexOf("<w:lang", StringComparison.Ordinal) < 0) {
sStyles = sStyles.Substring(0, oDefault.Groups[1].Index) + oDefault.Groups[1].Value + "<w:lang w:val=\"" + documentLanguage() + "\"/>" + sStyles.Substring(oDefault.Groups[1].Index + oDefault.Groups[1].Length);
setPart(dParts, lsOrder, "word/styles.xml", sStyles);
lsFindings.Add("MissingLanguage: fixed, the default style's language set to " + documentLanguage());
}
}
else {
int iSlide = 0;
foreach (string sName in lsOrder) {
if (!Regex.IsMatch(sName, "^ppt/slides/slide\\d+\\.xml$")) continue;
iSlide++;
string sSlide = partText(dParts, sName);
Match oTitle = Regex.Match(sSlide, "<p:sp>(?:(?!</p:sp>).)*?type=\"(?:ctrTitle|title)\".*?</p:sp>", RegexOptions.Singleline);
if (!oTitle.Success) lsFindings.Add("SlideMissingTitle: " + Path.GetFileNameWithoutExtension(sName) + " has no title");
else if (sTitle == "") {
StringBuilder sbText = new StringBuilder();
foreach (Match oRun in Regex.Matches(oTitle.Value, "<a:t>(.*?)</a:t>", RegexOptions.Singleline)) sbText.Append(xmlText(oRun.Groups[1].Value));
sTitle = sbText.ToString().Trim();
}
foreach (Match oPicture in Regex.Matches(sSlide, "<p:pic>.*?</p:pic>", RegexOptions.Singleline))
if (!Regex.IsMatch(oPicture.Value, "<p:cNvPr\\b[^>]*\\bdescr=\"[^\"]+\"")) lsFindings.Add("MissingAltText: a picture on " + Path.GetFileNameWithoutExtension(sName) + " has no alternative text");
}
}
if (sTitle == "") sTitle = documentTitle(sPath);
ensureCoreProperties(dParts, lsOrder, sTitle, lsFindings);
writePackage(sPath, lsOrder, dParts);
return true;
} // finishOffice method

// finishEpub: a title and a language in the package, which Pandoc leaves out when the source has none.
private static bool finishEpub(string sPath, List<string> lsFindings) {
Dictionary<string, byte[]> dParts = new Dictionary<string, byte[]>();
List<string> lsOrder = readPackage(sPath, dParts);
foreach (string sName in lsOrder) {
if (!sName.EndsWith(".opf", StringComparison.OrdinalIgnoreCase)) continue;
string sOpf = partText(dParts, sName), sWas = sOpf;
Match oTitle = Regex.Match(sOpf, "<dc:title\\b[^>]*>(.*?)</dc:title>", RegexOptions.Singleline);
if (!oTitle.Success || xmlText(oTitle.Groups[1].Value).Trim().Length == 0 || xmlText(oTitle.Groups[1].Value).Trim().ToUpperInvariant() == "UNTITLED") {
// The book's first heading, as a Word file's title is found, else the file's name.
string sBookTitle = "";
foreach (string sPage in lsOrder) {
if (!Regex.IsMatch(sPage, "\\.x?html?$", RegexOptions.IgnoreCase)) continue;
Match oHeading = Regex.Match(partText(dParts, sPage), "<h1\\b(?![^>]*class=\"title\")[^>]*>(.*?)</h1>", RegexOptions.Singleline | RegexOptions.IgnoreCase);
// Pandoc's own title page says UNTITLED when the source had no title, so that heading is no title.
if (oHeading.Success) { sBookTitle = xmlText(Regex.Replace(oHeading.Groups[1].Value, "<[^>]+>", "")).Trim(); if (sBookTitle.ToUpperInvariant() == "UNTITLED") sBookTitle = ""; if (sBookTitle != "") break; }
}
if (sBookTitle == "") sBookTitle = documentTitle(sPath);
string sElement = "<dc:title id=\"epub-title-1\">" + xmlEscape(sBookTitle) + "</dc:title>";
sOpf = oTitle.Success ? sOpf.Substring(0, oTitle.Index) + sElement + sOpf.Substring(oTitle.Index + oTitle.Length) : sOpf.Replace("</metadata>", sElement + "</metadata>");
lsFindings.Add("MissingTitle: fixed, the book's title set to " + sBookTitle);
}
if (!Regex.IsMatch(sOpf, "<dc:language\\b[^>]*>\\s*\\S")) {
sOpf = Regex.Replace(sOpf, "<dc:language\\b[^>]*>\\s*</dc:language>|<dc:language\\s*/>", "");
sOpf = sOpf.Replace("</metadata>", "<dc:language>" + documentLanguage() + "</dc:language></metadata>");
lsFindings.Add("MissingLanguage: fixed, the book's language set to " + documentLanguage());
}
if (sOpf != sWas) setPart(dParts, lsOrder, sName, sOpf);
}
writePackage(sPath, lsOrder, dParts);
return true;
} // finishEpub method

// finishMarkdown: front matter with a title and a language when it has none; what extCheck reports.
private static bool finishMarkdown(string sPath, List<string> lsFindings) {
string sText = decodeText(File.ReadAllBytes(sPath)).Replace("\r\n", "\n");
int iLast = 0;
bool bHeading = false;
foreach (Match oHeading in Regex.Matches(sText, "^(#{1,6})[ \\t]+\\S", RegexOptions.Multiline)) {
int iLevel = oHeading.Groups[1].Value.Length;
if (iLast > 0 && iLevel > iLast + 1) lsFindings.Add("SkippedHeadingLevel: a level " + iLevel + " heading follows a level " + iLast);
iLast = iLevel;
bHeading = true;
}
if (!bHeading) lsFindings.Add("NoHeadings: the document has no headings, so a screen reader cannot move by them");
if (Regex.IsMatch(sText, "!\\[\\s*\\]\\(")) lsFindings.Add("MissingAltText: a picture has no alternative text");
if (!sText.StartsWith("---\n")) {
Match oFirst = Regex.Match(sText, "^#[ \\t]+(.+)$", RegexOptions.Multiline);
string sTitle = oFirst.Success ? oFirst.Groups[1].Value.Trim() : documentTitle(sPath);
sText = "---\ntitle: \"" + sTitle.Replace("\\", "\\\\").Replace("\"", "\\\"") + "\"\nlang: " + documentLanguage() + "\n---\n\n" + sText;
File.WriteAllText(sPath, sText.Replace("\n", "\r\n"), new UTF8Encoding(true));
lsFindings.Add("NoYamlFrontMatter: fixed, title and lang added");
}
return true;
} // finishMarkdown method

// checkPage: what extCheck would report in a web page the page form cannot fix.
private static bool checkPage(string sPath, List<string> lsFindings) {
string sHtml = decodeText(File.ReadAllBytes(sPath));
foreach (Match oImage in Regex.Matches(sHtml, "<img\\b[^>]*>", RegexOptions.IgnoreCase))
if (!Regex.IsMatch(oImage.Value, "\\balt=\"", RegexOptions.IgnoreCase)) lsFindings.Add("MissingAltText: a picture has no alternative text");
if (!Regex.IsMatch(sHtml, "<html\\b[^>]*\\blang=\"[^\"]+\"", RegexOptions.IgnoreCase)) lsFindings.Add("MissingDocumentLanguage: the page names no language");
return true;
} // checkPage method

// ---- workbooks ----

private class HeaderRegion { public int iTop, iLeft, iBottom, iRight; public string sStem = ""; }

private static bool finishXlsx(string sPath, List<string> lsFindings) {
Dictionary<string, byte[]> dParts = new Dictionary<string, byte[]>();
List<string> lsOrder = readPackage(sPath, dParts);
string sBook = partText(dParts, "xl/workbook.xml");
string sBookRels = partText(dParts, "xl/_rels/workbook.xml.rels");
// The shared strings, each its runs joined.
List<string> lsShared = new List<string>();
foreach (Match oItem in Regex.Matches(partText(dParts, "xl/sharedStrings.xml"), "<si>(.*?)</si>", RegexOptions.Singleline)) {
StringBuilder sbItem = new StringBuilder();
foreach (Match oRun in rxT.Matches(oItem.Groups[1].Value)) sbItem.Append(xmlText(oRun.Groups[1].Value));
lsShared.Add(sbItem.ToString());
}
// The names the workbook already has.
HashSet<string> hsNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
HashSet<string> hsNamedCells = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
foreach (Match oName in Regex.Matches(sBook, "<definedName\\b([^>]*)>(.*?)</definedName>", RegexOptions.Singleline)) {
Match oAttr = Regex.Match(oName.Groups[1].Value, "\\bname=\"([^\"]+)\"");
if (oAttr.Success) hsNames.Add(oAttr.Groups[1].Value);
hsNamedCells.Add(xmlText(oName.Groups[2].Value).Replace("'", "").Trim());
}
MatchCollection oSheets = Regex.Matches(sBook, "<sheet\\b[^>]*/>");
bool bOneSheet = oSheets.Count == 1;
StringBuilder sbNewNames = new StringBuilder();
foreach (Match oSheet in oSheets) {
string sSheetName = xmlText(Regex.Match(oSheet.Value, "\\bname=\"([^\"]*)\"").Groups[1].Value);
string sRid = Regex.Match(oSheet.Value, "\\br:id=\"([^\"]*)\"").Groups[1].Value;
Match oTarget = Regex.Match(sBookRels, "<Relationship\\b[^>]*\\bId=\"" + Regex.Escape(sRid) + "\"[^>]*>");
string sTarget = Regex.Match(oTarget.Value, "\\bTarget=\"([^\"]*)\"").Groups[1].Value;
string sPart = sTarget.StartsWith("/") ? sTarget.TrimStart('/') : "xl/" + sTarget;
string sXml = partText(dParts, sPart);
if (sXml == "") continue;
// A lone sheet with a default name takes the file's name, where no formula could refer to the old one.
if (bOneSheet && Regex.IsMatch(sSheetName, "^(Sheet\\d*|Data)$") && sXml.IndexOf("<f", StringComparison.Ordinal) < 0 && hsNames.Count == 0) {
string sNewName = Regex.Replace(documentTitle(sPath), "[\\[\\]:*?/\\\\]", " ").Trim();
if (sNewName.Length > 31) sNewName = sNewName.Substring(0, 31).Trim();
if (sNewName.Length > 0 && sNewName != sSheetName) {
sBook = sBook.Replace(oSheet.Value, oSheet.Value.Replace("name=\"" + xmlEscape(sSheetName) + "\"", "name=\"" + xmlEscape(sNewName) + "\""));
lsFindings.Add("DefaultSheetName: fixed, " + sSheetName + " renamed " + sNewName);
sSheetName = sNewName;
}
}
if (sXml.IndexOf("<mergeCell ", StringComparison.Ordinal) >= 0) lsFindings.Add("MergedCells: " + sSheetName + " has merged cells, which screen readers announce poorly");
// The cells, by row and column: text or not.
Dictionary<long, string> dText = new Dictionary<long, string>();
HashSet<long> hsIsText = new HashSet<long>();
foreach (Match oCell in rxCell.Matches(sXml)) {
string sRef = "", sType = "";
foreach (Match oAttr in rxAttr.Matches(oCell.Groups[1].Value)) {
if (oAttr.Groups[1].Value == "r") sRef = oAttr.Groups[2].Value;
else if (oAttr.Groups[1].Value == "t") sType = oAttr.Groups[2].Value;
}
string sInner = oCell.Groups[2].Value;
if (sRef == "" || sInner == "") continue;
string sValue;
if (sType == "inlineStr") { StringBuilder sb = new StringBuilder(); foreach (Match oRun in rxT.Matches(sInner)) sb.Append(xmlText(oRun.Groups[1].Value)); sValue = sb.ToString(); }
else {
Match oV = Regex.Match(sInner, "<v>(.*?)</v>", RegexOptions.Singleline);
if (!oV.Success) continue;
sValue = xmlText(oV.Groups[1].Value);
if (sType == "s") { int iIndex; sValue = int.TryParse(sValue, out iIndex) && iIndex >= 0 && iIndex < lsShared.Count ? lsShared[iIndex] : ""; }
}
if (sValue.Trim().Length == 0) continue;
int iRow, iColumn;
if (!cellPosition(sRef, out iRow, out iColumn)) continue;
long iKey = cellKey(iRow, iColumn);
dText[iKey] = sValue.Trim();
if (sType == "s" || sType == "inlineStr" || sType == "str") hsIsText.Add(iKey);
}
List<HeaderRegion> lsRegions = findRegions(dText);
bool bFrozen = sXml.IndexOf("<pane ", StringComparison.Ordinal) >= 0;
foreach (HeaderRegion oRegion in lsRegions) {
oRegion.sStem = headerStem(oRegion, dText, hsIsText);
if (oRegion.sStem == "") continue;
string sCell = "$" + columnName(oRegion.iLeft) + "$" + oRegion.iTop;
if (hsNamedCells.Contains(sSheetName + "!" + sCell)) continue;
int iNumber = 1;
while (hsNames.Contains(oRegion.sStem + iNumber.ToString("00"))) iNumber++;
string sName = oRegion.sStem + iNumber.ToString("00");
hsNames.Add(sName);
sbNewNames.Append("<definedName name=\"" + sName + "\">" + xmlEscape("'" + sSheetName.Replace("'", "''") + "'!" + sCell) + "</definedName>");
lsFindings.Add("Header names: " + sName + " for " + sSheetName + " " + columnName(oRegion.iLeft) + oRegion.iTop + ":" + columnName(oRegion.iRight) + oRegion.iBottom);
// HeaderRowNotFrozen: the sheet's first table keeps its headers in view.
if (!bFrozen) {
bool bColumns = oRegion.sStem != "RowTitle", bRows = oRegion.sStem != "ColumnTitle";
int iYSplit = bColumns ? oRegion.iTop : 0, iXSplit = bRows ? oRegion.iLeft : 0;
string sPane = "<pane" + (iXSplit > 0 ? " xSplit=\"" + iXSplit + "\"" : "") + (iYSplit > 0 ? " ySplit=\"" + iYSplit + "\"" : "")
+ " topLeftCell=\"" + columnName(iXSplit + 1) + (iYSplit + 1) + "\" activePane=\"" + (iXSplit > 0 && iYSplit > 0 ? "bottomRight" : iYSplit > 0 ? "bottomLeft" : "topRight") + "\" state=\"frozen\"/>";
Match oView = Regex.Match(sXml, "<sheetView\\b[^>]*?(/?)>");
if (oView.Success && oView.Groups[1].Value == "/") sXml = sXml.Substring(0, oView.Index) + oView.Value.Substring(0, oView.Value.Length - 2) + ">" + sPane + "</sheetView>" + sXml.Substring(oView.Index + oView.Length);
else if (oView.Success) sXml = sXml.Substring(0, oView.Index + oView.Length) + sPane + sXml.Substring(oView.Index + oView.Length);
else {
Match oBefore = Regex.Match(sXml, "<(?:sheetFormatPr|cols|sheetData)\\b");
if (oBefore.Success) sXml = sXml.Substring(0, oBefore.Index) + "<sheetViews><sheetView workbookViewId=\"0\">" + sPane + "</sheetView></sheetViews>" + sXml.Substring(oBefore.Index);
}
bFrozen = true;
setPart(dParts, lsOrder, sPart, sXml);
}
}
}
if (sbNewNames.Length > 0) {
if (sBook.IndexOf("</definedNames>", StringComparison.Ordinal) >= 0) sBook = sBook.Replace("</definedNames>", sbNewNames.ToString() + "</definedNames>");
else if (Regex.IsMatch(sBook, "<definedNames\\s*/>")) sBook = Regex.Replace(sBook, "<definedNames\\s*/>", "<definedNames>" + sbNewNames.ToString() + "</definedNames>");
else sBook = sBook.Replace("</sheets>", "</sheets><definedNames>" + sbNewNames.ToString() + "</definedNames>");
}
setPart(dParts, lsOrder, "xl/workbook.xml", sBook);
ensureCoreProperties(dParts, lsOrder, documentTitle(sPath), lsFindings);
writePackage(sPath, lsOrder, dParts);
return true;
} // finishXlsx method

private static long cellKey(int iRow, int iColumn) { return (long)iRow * 100000L + iColumn; }

private static bool cellPosition(string sRef, out int iRow, out int iColumn) {
iRow = 0; iColumn = 0;
Match oRef = Regex.Match(sRef, "^\\$?([A-Za-z]+)\\$?(\\d+)$");
if (!oRef.Success) return false;
foreach (char c in oRef.Groups[1].Value.ToUpperInvariant()) iColumn = iColumn * 26 + (c - 'A' + 1);
iRow = int.Parse(oRef.Groups[2].Value);
return true;
} // cellPosition method

private static string columnName(int iColumn) {
string sName = "";
while (iColumn > 0) { int iRest = (iColumn - 1) % 26; sName = (char)('A' + iRest) + sName; iColumn = (iColumn - 1) / 26; }
return sName;
} // columnName method

// findRegions: the rectangles Excel's CurrentRegion would give -- filled cells joined across rows,
// columns and corners, each group's bounds grown until no filled cell touches them from outside.
private static List<HeaderRegion> findRegions(Dictionary<long, string> dText) {
List<HeaderRegion> lsRegions = new List<HeaderRegion>();
HashSet<long> hsSeen = new HashSet<long>();
foreach (long iStart in dText.Keys) {
if (hsSeen.Contains(iStart)) continue;
HeaderRegion oRegion = new HeaderRegion();
oRegion.iTop = oRegion.iBottom = (int)(iStart / 100000L);
oRegion.iLeft = oRegion.iRight = (int)(iStart % 100000L);
Queue<long> qNext = new Queue<long>();
qNext.Enqueue(iStart); hsSeen.Add(iStart);
while (qNext.Count > 0) {
long iKey = qNext.Dequeue();
int iRow = (int)(iKey / 100000L), iColumn = (int)(iKey % 100000L);
if (iRow < oRegion.iTop) oRegion.iTop = iRow;
if (iRow > oRegion.iBottom) oRegion.iBottom = iRow;
if (iColumn < oRegion.iLeft) oRegion.iLeft = iColumn;
if (iColumn > oRegion.iRight) oRegion.iRight = iColumn;
for (int iDown = -1; iDown <= 1; iDown++)
for (int iAcross = -1; iAcross <= 1; iAcross++) {
long iNear = cellKey(iRow + iDown, iColumn + iAcross);
if (dText.ContainsKey(iNear) && hsSeen.Add(iNear)) qNext.Enqueue(iNear);
}
}
lsRegions.Add(oRegion);
}
// Rectangles that touch, even at a corner, are one region, as CurrentRegion makes them.
bool bMerged = true;
while (bMerged) {
bMerged = false;
for (int i = 0; i < lsRegions.Count && !bMerged; i++)
for (int j = i + 1; j < lsRegions.Count && !bMerged; j++) {
HeaderRegion a = lsRegions[i], b = lsRegions[j];
if (a.iLeft - 1 <= b.iRight && b.iLeft - 1 <= a.iRight && a.iTop - 1 <= b.iBottom && b.iTop - 1 <= a.iBottom) {
a.iTop = Math.Min(a.iTop, b.iTop); a.iBottom = Math.Max(a.iBottom, b.iBottom);
a.iLeft = Math.Min(a.iLeft, b.iLeft); a.iRight = Math.Max(a.iRight, b.iRight);
lsRegions.RemoveAt(j);
bMerged = true;
}
}
}
lsRegions.Sort(delegate(HeaderRegion a, HeaderRegion b) { return a.iTop != b.iTop ? a.iTop.CompareTo(b.iTop) : a.iLeft.CompareTo(b.iLeft); });
return lsRegions;
} // findRegions method

// headerStem: ColumnTitle, RowTitle, Title, or "" when the region has no headers to name.
private static string headerStem(HeaderRegion oRegion, Dictionary<long, string> dText, HashSet<long> hsIsText) {
if (oRegion.iBottom - oRegion.iTop < 1 || oRegion.iRight - oRegion.iLeft < 1) return "";
bool bCorner = dText.ContainsKey(cellKey(oRegion.iTop, oRegion.iLeft));
int iFirstColumn = bCorner ? oRegion.iLeft : oRegion.iLeft + 1;
int iFirstRow = bCorner ? oRegion.iTop : oRegion.iTop + 1;
bool bColumns = labelsRun(dText, hsIsText, oRegion.iTop, iFirstColumn, 0, 1, oRegion.iRight - iFirstColumn + 1);
bool bRows = labelsRun(dText, hsIsText, iFirstRow, oRegion.iLeft, 1, 0, oRegion.iBottom - iFirstRow + 1);
if (bColumns && bRows) return "Title";
if (bColumns) return "ColumnTitle";
if (bRows) return "RowTitle";
return "";
} // headerStem method

// labelsRun: iCount cells from a start, stepping down or across, each filled, text and unique.
private static bool labelsRun(Dictionary<long, string> dText, HashSet<long> hsIsText, int iRow, int iColumn, int iDown, int iAcross, int iCount) {
if (iCount < 1) return false;
HashSet<string> hsSeen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
for (int i = 0; i < iCount; i++) {
long iKey = cellKey(iRow + i * iDown, iColumn + i * iAcross);
string sValue;
if (!dText.TryGetValue(iKey, out sValue) || !hsIsText.Contains(iKey) || !hsSeen.Add(sValue)) return false;
}
return true;
} // labelsRun method

// ------- PDF from a web page, by Microsoft Edge (kit 1.90.0) -------
//
// A PDF WITHOUT OFFICE. Every route that made a PDF needed Microsoft Office, so a computer
// without Office could make none. Edge comes with Windows, and Homer apps already drive it
// (HomerView, urlFido), so it prints a Homer web page to PDF: headless, with a fresh profile of
// its own so it never joins the person's open Edge, and no header or footer. Chromium writes a
// tagged PDF with an outline from the page's headings (unconfirmed for every Edge version: test a
// result with a screen reader). Office stays the first way for Word and PowerPoint files, whose
// own PDF export keeps more of their layout.
public static string edgePath() {
string sX86 = Environment.GetEnvironmentVariable("ProgramFiles(x86)") ?? "";
string sAll = Environment.GetEnvironmentVariable("ProgramFiles") ?? "";
string sLocal = Environment.GetEnvironmentVariable("LOCALAPPDATA") ?? "";
return findProgram("msedge.exe", new string[] {
sX86 == "" ? "" : Path.Combine(sX86, @"Microsoft\Edge\Application\msedge.exe"),
sAll == "" ? "" : Path.Combine(sAll, @"Microsoft\Edge\Application\msedge.exe"),
sLocal == "" ? "" : Path.Combine(sLocal, @"Microsoft\Edge\Application\msedge.exe") });
} // edgePath method

private static bool edgePdf(string sSource, string sTarget, out string sError) {
sError = "";
if (typeOf(sSource) != "htm") { sError = "Edge prints only a web page to PDF"; return false; }
string sEdge = edgePath();
if (sEdge == "") { sError = "Microsoft Edge is not installed"; return false; }
string sProfile = Path.Combine(Path.GetTempPath(), "HomerEdgePdf_" + Guid.NewGuid().ToString("N").Substring(0, 8));
string sOut = Path.GetFullPath(sTarget);
try {
if (File.Exists(sOut)) File.Delete(sOut);
string sUrl = new Uri(Path.GetFullPath(sSource)).AbsoluteUri;
string sArguments = "--headless --disable-gpu --no-first-run --no-default-browser-check --disable-extensions"
+ " --user-data-dir=\"" + sProfile + "\" --no-pdf-header-footer --generate-pdf-document-outline --export-tagged-pdf"
+ " --print-to-pdf=\"" + sOut + "\" \"" + sUrl + "\"";
string sSaid;
bool bRan = run(sEdge, sArguments, out sSaid, out sError);
if (!File.Exists(sOut) || new FileInfo(sOut).Length < 5) {
if (sError == "") sError = "Edge wrote no PDF";
return false;
}
byte[] abHead = new byte[4];
using (FileStream oIn = File.OpenRead(sOut)) oIn.Read(abHead, 0, 4);
if (Encoding.ASCII.GetString(abHead) != "%PDF") { sError = "Edge wrote something that is not a PDF"; return false; }
if (!bRan) Log.info("Edge reported a problem but wrote a whole PDF: " + sError);
sError = "";
return true;
}
catch (Exception ex) { sError = ex.Message; return false; }
finally { try { if (Directory.Exists(sProfile)) Directory.Delete(sProfile, true); } catch (Exception) { } }
} // edgePdf method

private static string firstLine(string sText) {
foreach (string sLine in sText.Replace("\r\n", "\n").Split('\n')) if (sLine.Trim().Length > 0) return sLine.Trim();
return sText.Trim();
} // firstLine method

private static string lastLine(string sText) {
string sLast = "";
foreach (string sLine in sText.Replace("\r\n", "\n").Split('\n')) if (sLine.Trim().Length > 0) sLast = sLine.Trim();
return sLast;
} // lastLine method

} // Conversion class

} // namespace Homer
