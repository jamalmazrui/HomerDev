// Table.cs -- reading and writing table data, for the Homer Tools.
//
// IN THE KIT SINCE 1.74.0. It was FileDir's own file, in the Homer namespace
// but in one app's folder; it moved here with Conversion.cs, and reads .xlsx
// with .NET's own zip support rather than a zip package, so any app can
// compile it with nothing beside it.
//
// Copyright 2006-2026 by Jamal Mazrui
// MIT License. See License.md, which carries the terms in full.
//
// WHAT THIS IS FOR
//
// Several formats hold a table: .inix in its list-of-records form, .csv, .tsv,
// .xlsx, and a Markdown pipe table. Converting between them was not possible
// before this: .inix was read as raw text and written not at all, .xlsx gave up
// a heap of loose strings with the rows and columns thrown away, and Pandoc has
// no writer for .csv or .tsv, so those were input only.
//
// THE INTERMEDIATE FORMAT IS A MARKDOWN PIPE TABLE.
//
// Every table format here can be read into rows and columns, and written back
// out from them. For the targets FileDir cannot write itself -- .docx, .html,
// .odt -- the rows are written as a Markdown pipe table and handed to Pandoc,
// which turns a pipe table into a real table in any of them. One intermediate
// serves every target, which is the same arrangement the PDF reader uses.
//
// So the round trip works in both directions:
//
//   inix <-> csv <-> tsv <-> xlsx(in) <-> md <-> docx/html/odt(out)
//
// WHAT IS NOT HERE
//
// Writing .xlsx. That needs the whole Open XML package written correctly --
// styles, shared strings, relationships -- and a spreadsheet that opens with a
// repair warning is worse than one that was never written. A table becomes .csv
// instead, which every spreadsheet opens directly.

using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace Homer {

public class Table {

// The column names, in order.
public List<string> lsFields = new List<string>();

// The rows, each a list of values matching lsFields by position. A short row is
// padded when it is written, so a ragged source does not lose its later columns.
public List<List<string>> lsRows = new List<List<string>>();

public int rowCount() { return lsRows.Count; }
public int fieldCount() { return lsFields.Count; }

public string cell(int iRow, int iField) {
if (iRow < 0 || iRow >= lsRows.Count) return "";
List<string> lsRow = lsRows[iRow];
if (iField < 0 || iField >= lsRow.Count) return "";
return lsRow[iField] == null ? "" : lsRow[iField];
} // cell method

// ---- What can be read and written -----------------------------------------

public static readonly string[] aReadable = {".inix", ".csv", ".tsv", ".xlsx", ".md", ".markdown"};
public static readonly string[] aWritable = {".inix", ".csv", ".tsv", ".md", ".markdown"};

// Written by handing a Markdown pipe table to Pandoc.
public static readonly string[] aViaPandoc = {".docx", ".html", ".htm", ".odt", ".rtf", ".epub", ".tex", ".rst"};

public static bool canRead(string sPath) {
return Array.IndexOf(aReadable, Path.GetExtension(sPath).ToLower()) >= 0;
} // canRead method

public static bool canWrite(string sPath) {
string sExt = Path.GetExtension(sPath).ToLower();
return Array.IndexOf(aWritable, sExt) >= 0 || Array.IndexOf(aViaPandoc, sExt) >= 0;
} // canWrite method

// ---- Reading ---------------------------------------------------------------

public static Table read(string sPath, out string sError) {
sError = "";
string sExt = Path.GetExtension(sPath).ToLower();
try {
if (sExt == ".inix") return fromInix(sPath, out sError);
if (sExt == ".csv") return fromSeparated(sPath, ',');
if (sExt == ".tsv") return fromSeparated(sPath, '\t');
if (sExt == ".xlsx") return fromXlsx(sPath, out sError);
if (sExt == ".md" || sExt == ".markdown") return fromMarkdown(sPath, out sError);
}
catch (Exception ex) {
sError = ex.Message;
return null;
}
sError = sExt + " does not hold a table FileDir can read.";
return null;
} // read method

public static Table fromInix(string sPath, out string sError) {
// InixCodec is Homer.InixCodec, and this file is in the Homer namespace too, so
// the name stands alone. It was written FileDir.InixCodec and the build stopped
// on five lines of "does not exist in the namespace FileDir" -- the namespace
// was assumed rather than read.
// The list-of-records form: each [Record1], [Record2] section is a row and the
// keys within it are the columns.
//
// The column order is the order the keys are first met, across all records,
// which keeps a table written by writeAsTable in the order it was written and
// still copes with a record that carries an extra field.
sError = "";
List<InixCodec.Section> lsSections = InixCodec.read(sPath);
Table table = new Table();
List<Dictionary<string, string>> lsDicts = new List<Dictionary<string, string>>();
foreach (InixCodec.Section section in lsSections) {
if (section == null) continue;
// The Global section holds settings about the file, not a row of data.
if (String.Equals(section.Name, "Global", StringComparison.OrdinalIgnoreCase)) continue;
Dictionary<string, string> dRow = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
foreach (InixCodec.Pair pair in section.Pairs) {
if (pair == null || pair.Key == null) continue;
bool bKnown = false;
foreach (string sField in table.lsFields)
if (String.Equals(sField, pair.Key, StringComparison.OrdinalIgnoreCase)) bKnown = true;
if (!bKnown) table.lsFields.Add(pair.Key);
dRow[pair.Key] = pair.Value == null ? "" : pair.Value;
}
lsDicts.Add(dRow);
}
foreach (Dictionary<string, string> dRow in lsDicts) {
List<string> lsRow = new List<string>();
foreach (string sField in table.lsFields) {
string sValue;
lsRow.Add(dRow.TryGetValue(sField, out sValue) ? sValue : "");
}
table.lsRows.Add(lsRow);
}
if (table.lsFields.Count == 0)
sError = "this .inix file holds settings rather than a table of records";
return table;
} // fromInix method

public static Table fromSeparated(string sPath, char cSeparator) {
// Comma or tab separated, with the first row taken as the column names.
//
// Quoting is handled properly, because a comma inside a quoted field is the
// whole reason the quoting exists: a naive Split on commas breaks every address
// and every "Surname, Forename" ever exported.
Table table = new Table();
string sText = Homer.Util.file2String(sPath);
List<List<string>> lsAll = parseSeparated(sText, cSeparator);
if (lsAll.Count == 0) return table;
foreach (string sField in lsAll[0]) table.lsFields.Add(sField);
for (int i = 1; i < lsAll.Count; i++) table.lsRows.Add(lsAll[i]);
return table;
} // fromSeparated method

public static List<List<string>> parseSeparated(string sText, char cSeparator) {
// A separated-values reader that understands quoting: a field may be wrapped in
// double quotes, a doubled quote inside one means a literal quote, and a
// separator or a line break inside quotes is part of the field.
List<List<string>> lsRows = new List<List<string>>();
List<string> lsRow = new List<string>();
StringBuilder sbField = new StringBuilder();
bool bQuoted = false;
if (sText == null) return lsRows;
sText = sText.Replace("\r\n", "\n").Replace('\r', '\n');
for (int i = 0; i < sText.Length; i++) {
char c = sText[i];
if (bQuoted) {
if (c != '"') { sbField.Append(c); continue; }
if (i + 1 < sText.Length && sText[i + 1] == '"') { sbField.Append('"'); i++; continue; }
bQuoted = false;
continue;
}
if (c == '"' && sbField.Length == 0) { bQuoted = true; continue; }
if (c == cSeparator) { lsRow.Add(sbField.ToString()); sbField.Length = 0; continue; }
if (c == '\n') {
lsRow.Add(sbField.ToString());
sbField.Length = 0;
// A blank line between rows is not a row of one empty field.
if (lsRow.Count > 1 || lsRow[0].Length > 0) lsRows.Add(lsRow);
lsRow = new List<string>();
continue;
}
sbField.Append(c);
}
if (sbField.Length > 0 || lsRow.Count > 0) {
lsRow.Add(sbField.ToString());
if (lsRow.Count > 1 || lsRow[0].Length > 0) lsRows.Add(lsRow);
}
return lsRows;
} // parseSeparated method

public static Table fromMarkdown(string sPath, out string sError) {
// The first pipe table in a Markdown file.
sError = "";
Table table = new Table();
string[] aLines = Homer.Util.file2String(sPath).Replace("\r\n", "\n").Split('\n');
List<string[]> lsCells = new List<string[]>();
foreach (string sRaw in aLines) {
string sLine = sRaw.Trim();
if (sLine.IndexOf('|') < 0) {
// A blank or non-table line ends the table, once one has started.
if (lsCells.Count > 0) break;
continue;
}
// The dashed line under the header is not data.
if (Regex.IsMatch(sLine, @"^\|?[\s:\-|]+\|?$")) continue;
string sTrim = sLine.Trim('|');
lsCells.Add(sTrim.Split('|'));
}
if (lsCells.Count == 0) {
sError = "no table was found in this Markdown file";
return table;
}
foreach (string sField in lsCells[0]) table.lsFields.Add(sField.Trim());
for (int i = 1; i < lsCells.Count; i++) {
List<string> lsRow = new List<string>();
foreach (string sCell in lsCells[i]) lsRow.Add(sCell.Trim());
table.lsRows.Add(lsRow);
}
return table;
} // fromMarkdown method

public static Table fromXlsx(string sPath, out string sError) {
// The first worksheet of a spreadsheet, with its rows and columns intact.
//
// This is what the plain-text reader could not do. That one gathered
// xl/sharedStrings.xml, which is every string in the workbook in one heap with
// no idea which cell each belongs to -- fine for reading a spreadsheet aloud,
// useless for converting one. Here the sheet itself is read, each cell placed
// by its reference, and a numeric cell taken from its own value rather than the
// string table.
sError = "";
Table table = new Table();
List<string> lsShared = new List<string>();
string sSheetXml = "";
try {
using (System.IO.Compression.ZipArchive zip = System.IO.Compression.ZipFile.OpenRead(sPath)) {
System.IO.Compression.ZipArchiveEntry entryShared = findEntry(zip, "xl/sharedStrings.xml");
if (entryShared != null) {
string sXml = readEntry(zip, entryShared);
foreach (Match match in Regex.Matches(sXml, @"<si>(.*?)</si>", RegexOptions.Singleline)) {
StringBuilder sb = new StringBuilder();
foreach (Match run in Regex.Matches(match.Groups[1].Value, @"<t(?:\s[^>]*)?>(.*?)</t>", RegexOptions.Singleline))
sb.Append(unescapeXml(run.Groups[1].Value));
lsShared.Add(sb.ToString());
}
}
// The first sheet by name, which is how a workbook numbers them.
string sWanted = "";
foreach (System.IO.Compression.ZipArchiveEntry entry in zip.Entries) {
if (entry.FullName.EndsWith("/")) continue;
string sName = entry.FullName.Replace('\\', '/').ToLower();
if (!sName.StartsWith("xl/worksheets/sheet") || !sName.EndsWith(".xml")) continue;
if (sWanted.Length == 0 || String.Compare(sName, sWanted, StringComparison.Ordinal) < 0)
sWanted = entry.FullName;
}
if (sWanted.Length == 0) {
sError = "no worksheet was found in this workbook";
return table;
}
sSheetXml = readEntry(zip, findEntry(zip, sWanted));
}
}
catch (Exception ex) {
sError = ex.Message;
return table;
}

// Every row, and within it every cell placed by the letters of its reference,
// so a gap in the middle of a row stays a gap.
List<List<string>> lsAll = new List<List<string>>();
foreach (Match rowMatch in Regex.Matches(sSheetXml, @"<row[^>]*>(.*?)</row>", RegexOptions.Singleline)) {
List<string> lsRow = new List<string>();
foreach (Match cellMatch in Regex.Matches(rowMatch.Groups[1].Value, @"<c([^>]*)>(.*?)</c>|<c([^>]*)/>", RegexOptions.Singleline)) {
string sAttrs = cellMatch.Groups[1].Success ? cellMatch.Groups[1].Value : cellMatch.Groups[3].Value;
string sBody = cellMatch.Groups[2].Success ? cellMatch.Groups[2].Value : "";
int iColumn = columnOf(sAttrs);
while (lsRow.Count < iColumn) lsRow.Add("");
lsRow.Add(cellText(sAttrs, sBody, lsShared));
}
lsAll.Add(lsRow);
}
if (lsAll.Count == 0) {
sError = "this worksheet has no rows in it";
return table;
}
foreach (string sField in lsAll[0]) table.lsFields.Add(sField);
for (int i = 1; i < lsAll.Count; i++) table.lsRows.Add(lsAll[i]);
return table;
} // fromXlsx method

// findEntry: a part by name, ignoring case, since Office and other writers
// differ in how they capitalize them.
private static System.IO.Compression.ZipArchiveEntry findEntry(System.IO.Compression.ZipArchive zip, string sName) {
foreach (System.IO.Compression.ZipArchiveEntry entry in zip.Entries)
if (String.Compare(entry.FullName.Replace('\\', '/'), sName, true) == 0) return entry;
return null;
} // findEntry method

private static string readEntry(System.IO.Compression.ZipArchive zip, System.IO.Compression.ZipArchiveEntry entry) {
if (entry == null) return "";
using (Stream stream = entry.Open())
using (StreamReader reader = new StreamReader(stream, Encoding.UTF8))
return reader.ReadToEnd();
} // readEntry method

private static int columnOf(string sAttrs) {
// The column number from a cell reference such as r="C7": C is the third
// column, and AA is the twenty-seventh. Without this, a row with an empty cell
// in the middle would shift every later value one place left.
Match match = Regex.Match(sAttrs, "r=\"([A-Za-z]+)");
if (!match.Success) return -1;
string sLetters = match.Groups[1].Value.ToUpper();
int iColumn = 0;
foreach (char c in sLetters) iColumn = iColumn * 26 + (c - 'A' + 1);
return iColumn - 1;
} // columnOf method

private static string cellText(string sAttrs, string sBody, List<string> lsShared) {
// A cell's value. t="s" means the body is an index into the shared strings;
// t="inlineStr" means the text is here; anything else is a number or a date
// serial, whose digits are the value.
Match value = Regex.Match(sBody, @"<v>(.*?)</v>", RegexOptions.Singleline);
bool bShared = Regex.IsMatch(sAttrs, "t=\"s\"");
if (bShared && value.Success) {
int iIndex = -1;
if (int.TryParse(value.Groups[1].Value, out iIndex) && iIndex >= 0 && iIndex < lsShared.Count)
return lsShared[iIndex];
return "";
}
StringBuilder sb = new StringBuilder();
foreach (Match run in Regex.Matches(sBody, @"<t(?:\s[^>]*)?>(.*?)</t>", RegexOptions.Singleline))
sb.Append(unescapeXml(run.Groups[1].Value));
if (sb.Length > 0) return sb.ToString();
if (value.Success) return unescapeXml(value.Groups[1].Value);
return "";
} // cellText method

private static string unescapeXml(string sText) {
if (sText == null) return "";
return sText.Replace("&lt;", "<").Replace("&gt;", ">").Replace("&quot;", "\"")
.Replace("&apos;", "'").Replace("&amp;", "&");
} // unescapeXml method

// ---- Writing ---------------------------------------------------------------

public bool write(string sTarget, out string sError) {
sError = "";
string sExt = Path.GetExtension(sTarget).ToLower();
try {
if (sExt == ".inix") { toInix(sTarget); return true; }
if (sExt == ".csv") { toSeparated(sTarget, ','); return true; }
if (sExt == ".tsv") { toSeparated(sTarget, '\t'); return true; }
if (sExt == ".md" || sExt == ".markdown") { toMarkdown(sTarget); return true; }
if (Array.IndexOf(aViaPandoc, sExt) >= 0) return viaPandoc(sTarget, out sError);
}
catch (Exception ex) {
sError = ex.Message;
return false;
}
sError = "FileDir cannot write a table as " + sExt + ".";
return false;
} // write method

public void toInix(string sTarget) {
// The list-of-records form, through the codec that owns the format, so the
// numbering and the quoting rules are its own rather than a second opinion.
List<Dictionary<string, string>> lsDicts = new List<Dictionary<string, string>>();
foreach (List<string> lsRow in lsRows) {
Dictionary<string, string> dRow = new Dictionary<string, string>();
for (int i = 0; i < lsFields.Count; i++) {
string sValue = i < lsRow.Count ? lsRow[i] : "";
if (sValue == null) sValue = "";
dRow[lsFields[i]] = sValue;
}
lsDicts.Add(dRow);
}
InixCodec.writeAsTable(sTarget, lsFields, lsDicts);
} // toInix method

public void toSeparated(string sTarget, char cSeparator) {
StringBuilder sb = new StringBuilder();
sb.Append(separatedRow(lsFields, cSeparator));
foreach (List<string> lsRow in lsRows) {
List<string> lsPadded = new List<string>(lsRow);
while (lsPadded.Count < lsFields.Count) lsPadded.Add("");
sb.Append(separatedRow(lsPadded, cSeparator));
}
// A byte order mark, because a spreadsheet opening a .csv without one guesses
// the code page and turns every accented letter into rubbish.
File.WriteAllText(sTarget, sb.ToString(), new UTF8Encoding(true));
} // toSeparated method

private static string separatedRow(List<string> lsValues, char cSeparator) {
StringBuilder sb = new StringBuilder();
for (int i = 0; i < lsValues.Count; i++) {
if (i > 0) sb.Append(cSeparator);
string sValue = lsValues[i] == null ? "" : lsValues[i];
// NO CELL BECOMES A FORMULA (8 October 2026, from an audit by another AI): a
// value beginning = or @ -- or + or - when it is not a number -- became a live
// formula when the file was opened in a spreadsheet, and file names and text
// come from anywhere. Such a cell starts with an apostrophe, shown as plain
// text; numbers such as -5 are left exactly as they are.
if (sValue.Length > 0) {
char cFirst = sValue[0];
double nIgnored;
bool bNumber = double.TryParse(sValue, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out nIgnored);
if (cFirst == '=' || cFirst == '@' || cFirst == '\t' || cFirst == '\r' || ((cFirst == '+' || cFirst == '-') && !bNumber)) sValue = "'" + sValue;
}
// Quoted when it has to be, and not otherwise: a file full of needless
// quotes is harder to read and no more correct.
bool bNeed = sValue.IndexOf(cSeparator) >= 0 || sValue.IndexOf('"') >= 0
|| sValue.IndexOf('\n') >= 0 || sValue.IndexOf('\r') >= 0;
if (bNeed) sb.Append('"').Append(sValue.Replace("\"", "\"\"")).Append('"');
else sb.Append(sValue);
}
sb.Append("\r\n");
return sb.ToString();
} // separatedRow method

public void toMarkdown(string sTarget) {
File.WriteAllText(sTarget, markdownText(), new UTF8Encoding(true));
} // toMarkdown method

public string markdownText() {
// A pipe table. A pipe inside a value is escaped, or it would end the cell.
StringBuilder sb = new StringBuilder();
sb.Append(markdownRow(lsFields));
List<string> lsRule = new List<string>();
foreach (string sField in lsFields) lsRule.Add("---");
sb.Append(markdownRow(lsRule));
foreach (List<string> lsRow in lsRows) {
List<string> lsPadded = new List<string>(lsRow);
while (lsPadded.Count < lsFields.Count) lsPadded.Add("");
sb.Append(markdownRow(lsPadded));
}
return sb.ToString();
} // markdownText method

private static string markdownRow(List<string> lsValues) {
StringBuilder sb = new StringBuilder("|");
foreach (string sValue in lsValues) {
string sCell = sValue == null ? "" : sValue;
sCell = sCell.Replace("|", "\\|").Replace("\r\n", " ").Replace('\n', ' ').Replace('\r', ' ');
sb.Append(' ').Append(sCell).Append(" |");
}
sb.Append("\r\n");
return sb.ToString();
} // markdownRow method

private bool viaPandoc(string sTarget, out string sError) {
// Written as a Markdown pipe table and handed to Pandoc, which turns it into a
// real table in a Word document, a web page or an OpenDocument file. One
// intermediate serves every one of them.
sError = "";
if (!Homer.Conversion.havePandoc()) {
sError = "Pandoc is not installed, and it is what makes a "
+ Path.GetExtension(sTarget).ToLower() + " table. "
+ "Run installPandoc.cmd in the FileDir folder as an administrator.";
return false;
}
string sTemp = Path.Combine(Path.GetTempPath(),
Path.GetFileNameWithoutExtension(sTarget) + "_" + Guid.NewGuid().ToString("N").Substring(0, 8) + ".md");
try {
File.WriteAllText(sTemp, markdownText(), new UTF8Encoding(true));
bool bMade = Homer.Conversion.convertFile(sTemp, sTarget, out sError);
return bMade;
}
finally {
try { if (File.Exists(sTemp)) File.Delete(sTemp); }
catch (Exception) { }
}
} // viaPandoc method

} // Table class

} // Homer namespace
