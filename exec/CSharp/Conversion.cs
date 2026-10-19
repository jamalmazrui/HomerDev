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

// convert: sSource to the path sTarget, by the first way whose engines are all
// present. bQuick passes over engines that can take minutes (ocr), for a key
// that must answer at once.
public static bool convert(string sSource, string sTarget, out string sError) {
return convert(sSource, sTarget, false, out sError);
} // convert method

public static bool convert(string sSource, string sTarget, bool bQuick, out string sError) {
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
if (bMade) return true;
lsWhy.Add(sWay + ": " + sStepError);
}
sError = lsWhy.Count == 1 ? lsWhy[0] : "every way failed: " + String.Join("; ", lsWhy.ToArray());
return false;
} // convert method

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
case "pandoc": return pandoc(sSource, sTarget, out sError);
case "pdfstructure": return pdfStructure(sSource, sTarget, out sError);
case "pdftext": return pdfText(sSource, sTarget, out sError);
case "ocr": return ocrEngine(sSource, sTarget, out sError);
case "table": return tableEngine(sSource, sTarget, out sError);
case "zipxml": return zipXml(sSource, sTarget, out sError);
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
case "copy": case "table": case "zipxml": return "";
case "pandoc": return havePandoc() ? "" : "Pandoc is not installed";
case "pdftext": return havePdfPig() || pythonProgram() != "" ? "" : "neither PdfPig nor Python is present";
case "pdfstructure": return haveReader() || pythonProgram() != "" ? "" : "neither the PDF reader nor Python is present";
case "ocr": return !haveReader() ? "this program does not include the PDF reader, which OCR needs" : haveTesseract() ? "" : "Tesseract is not installed";
case "officecom": return officeApp(sSource) == "" ? "Office cannot open this type" : "";
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
{"epub", "EPUB book"}, {"exe", "program"}, {"htm", "web page"}, {"ini", "settings file"}, {"inix", "Homer settings file"},
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

private static string mediaCategoryOf(string sExt) {
string sCategory = "";
mediaCategory(sExt, ref sCategory);
return sCategory;
} // mediaCategoryOf method

public static string[,] targetsFor(string sPath) {
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
} // targetsFor method

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
public static bool convertAny(string sSource, string sTarget, out string sError) {
sError = "";
bool bHandled = false, bMade = false;
mediaConvert(sSource, sTarget, ref bHandled, ref bMade, ref sError);
if (bHandled) return bMade;
if (hasRoute(sSource, sTarget)) return convert(sSource, sTarget, out sError);
// A type the table does not name: its text, then Pandoc to the target.
string sText = toText(sSource, out sError);
if (sText.Length == 0) return false;
string sMd = tempPath(sSource, ".md");
try {
File.WriteAllText(sMd, sText, new UTF8Encoding(true));
if (typeOf(sTarget) == "md" || typeOf(sTarget) == "txt") { File.Copy(sMd, sTarget, true); return true; }
return pandoc(sMd, sTarget, out sError);
}
finally { try { File.Delete(sMd); } catch (Exception) { } }
} // convertAny method

// convertFile: Pandoc, for a type it reads, as FileDir's callers expect.
public static bool convertFile(string sSource, string sTarget, out string sError) {
sError = "";
if (!havePandoc()) { sError = "Pandoc is not installed. Install the program again and leave the Pandoc box ticked."; return false; }
if (!canRead(sSource)) { sError = "Pandoc cannot read " + Path.GetExtension(sSource).ToLowerInvariant() + " files"; return false; }
return pandoc(sSource, sTarget, out sError);
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

// ------- engine: officecom, the last resort -------

// Office's own numbers for the formats it saves, named rather than written bare.
private const int iWordFormatDocx = 16, iWordFormatFilteredHtml = 10, iWordFormatPdf = 17, iWordFormatUnicodeText = 7;
private const int iExcelFormatCsvUtf8 = 62, iExcelFormatHtml = 44, iExcelFormatXlsx = 51;
private const int iPowerPointFormatPdf = 32, iPowerPointFormatPptx = 24;
private const int iMsoFalse = 0, iMsoTrue = -1;

// bAlertBoxes: a program with windows shows an Alert box when Office is needed
// and missing; a console program sets this false and gets the words in sError.
public static bool bAlertBoxes = true;
private static List<string> lsAlerted = new List<string>();

private static string officeApp(string sSource) {
string sFrom = typeOf(sSource);
if (sFrom == "doc" || sFrom == "docx" || sFrom == "rtf" || sFrom == "odt" || sFrom == "pdf" || sFrom == "htm") return "Word";
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
int iFormat = sTo == "docx" ? iWordFormatDocx : sTo == "htm" ? iWordFormatFilteredHtml : sTo == "pdf" ? iWordFormatPdf : iWordFormatUnicodeText;
call(oDoc, "SaveAs2", sOut, iFormat);
call(oDoc, "Close", false);
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
