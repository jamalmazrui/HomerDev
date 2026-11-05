// Schema.cs -- upgrading an SQLite database's structure without loss, for the Homer Tools.
//
// IN THE KIT SINCE 1.94.0 (29 October 2026), from DbDo's Update from Template.
//
// Copyright 2006-2026 by Jamal Mazrui
// MIT License. See License.md, which carries the terms in full.
//
// WHAT THIS IS FOR
//
// A Homer app that ships a database template -- DbDo's RadioTrail and JobTrail,
// say -- may install a newer template that has gained a field. A person's own
// copy must never be overwritten: they may have added records. But a change that
// loses nothing -- an empty field added at the end of a table, a trigger taught
// the new field -- should happen by itself when they upgrade the app. Taking the
// template's RECORDS stays the person's choice, through the app's own merge.
//
// THE KIT DECIDES; THE APP RUNS THE SQL. The kit has no SQLite connection of its
// own (Conversion's SQLite engine runs Python), and each app already has one --
// DbDo through its driver, a Python app through sqlite3. So this file holds the
// rules and writes the SQL, and the app runs it on its own connection. The same
// rules are in exec\Python\schema.py, so every Homer app upgrades alike.
//
// Typical use, with the template attached as tplsrc:
//   run Schema.sColumnsSql(sTable, "main") and Schema.sColumnsSql(sTable, "tplsrc"),
//   parse each with Schema.lParseColumns, then for each column in
//   Schema.lMissingColumns(lHere, lTemplate) run Schema.sAddColumnSql(sTable, oColumn),
//   and when any was added, run Schema.aEditedTriggerSql(sTable, lHereAfter).

using System;
using System.Collections.Generic;
using System.Text.RegularExpressions;

namespace Homer {

// COLUMN TYPES (5 November 2026). A Homer database says what a column holds through its declared type, in names that
// follow SQLite's affinity rules and the web's de facto conventions together. The prefix states storage, which SQLite
// decides from the name: TEXT for UTF-8 text, BLOB for bytes. The rest names the format by its usual file extension,
// the download convention Windows also uses to choose a program -- TEXTJSON, TEXTINIX, BLOBPNG, BLOBZIP -- and each type
// records its MIME type, for export and web headers. Formats that are text are TEXT whatever MIME's first word says
// (application/json is TEXTJSON, image/svg+xml is TEXTSVG); binary ones are BLOB (application/zip is BLOBZIP). Value
// types name a single value with a natural action, after HTML's input types: TEXTURL is browsed, TEXTEMAIL mailed,
// TEXTPHONE called, TEXTPATH opened. Tested on 5 November 2026: SQLite gives INTEGER affinity to any name containing
// INT, so no name may contain it (TEXTPOINT stores '123' as a number); after that, TEXT affinity to any name containing
// CHAR, CLOB or TEXT, so no BLOB name may contain those (BLOBTEXT is text); then BLOB affinity to any name containing
// BLOB, before REAL, FLOA and DOUB. STRICT tables refuse every name here, so a Homer table is never STRICT. Twin:
// scripts\columnTypes.py; change both together; the kit's build checks that they agree and that SQLite gives each
// name the affinity it says. Each row: type, file extension, MIME type, lines (multi, single, binary), action
// (browse, call, edit, mail, open, show, or none), meaning.
public static class ColumnTypes {
    public static readonly string[][] aTypes = new string[][] {
        new string[] { "BLOBDOCX", ".docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "binary", "show", "a Word document" },
        new string[] { "BLOBEPUB", ".epub", "application/epub+zip", "binary", "show", "an EPUB book" },
        new string[] { "BLOBGIF", ".gif", "image/gif", "binary", "show", "a GIF picture" },
        new string[] { "BLOBJPG", ".jpg", "image/jpeg", "binary", "show", "a JPEG photo" },
        new string[] { "BLOBM4A", ".m4a", "audio/mp4", "binary", "show", "AAC audio" },
        new string[] { "BLOBMP3", ".mp3", "audio/mpeg", "binary", "show", "MP3 audio" },
        new string[] { "BLOBMP4", ".mp4", "video/mp4", "binary", "show", "MP4 video" },
        new string[] { "BLOBOGG", ".ogg", "audio/ogg", "binary", "show", "Ogg audio" },
        new string[] { "BLOBPDF", ".pdf", "application/pdf", "binary", "show", "a PDF document" },
        new string[] { "BLOBPNG", ".png", "image/png", "binary", "show", "a PNG picture" },
        new string[] { "BLOBPPTX", ".pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation", "binary", "show", "a PowerPoint deck" },
        new string[] { "BLOBWAV", ".wav", "audio/wav", "binary", "show", "WAV audio" },
        new string[] { "BLOBWEBM", ".webm", "video/webm", "binary", "show", "WebM video" },
        new string[] { "BLOBWEBP", ".webp", "image/webp", "binary", "show", "a WebP picture" },
        new string[] { "BLOBXLSX", ".xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "binary", "show", "an Excel workbook" },
        new string[] { "BLOBZIP", ".zip", "application/zip", "binary", "show", "a zip archive" },
        new string[] { "TEXTCSV", ".csv", "text/csv", "multi", "edit", "comma-separated values" },
        new string[] { "TEXTDBDO", ".dbdo", "text/x-dbdo", "multi", "edit", "a DbDo routine of dot-prompt commands" },
        new string[] { "TEXTEMAIL", "", "", "single", "mail", "an email address, written to with mailto" },
        new string[] { "TEXTHTML", ".htm", "text/html", "multi", "edit", "a web page" },
        new string[] { "TEXTICS", ".ics", "text/calendar", "multi", "edit", "iCalendar events" },
        new string[] { "TEXTINIX", ".inix", "text/x-inix", "multi", "edit", "Homer settings, in sections of key = value lines" },
        new string[] { "TEXTJSCRIPT", ".js", "text/javascript", "multi", "edit", "a JScript .NET program" },
        new string[] { "TEXTJSON", ".json", "application/json", "multi", "edit", "JSON data" },
        new string[] { "TEXTLINE", "", "text/plain", "single", "", "one line of plain text" },
        new string[] { "TEXTM3U", ".m3u", "audio/x-mpegurl", "multi", "edit", "a playlist" },
        new string[] { "TEXTMARKDOWN", ".md", "text/markdown", "multi", "edit", "Markdown" },
        new string[] { "TEXTMEMO", ".txt", "text/plain", "multi", "edit", "lines of plain text" },
        new string[] { "TEXTPATH", "", "", "single", "open", "the path of a file or folder, opened by Windows" },
        new string[] { "TEXTPHONE", "", "", "single", "call", "a phone number, called with tel" },
        new string[] { "TEXTSQL", ".sql", "application/sql", "multi", "edit", "SQL statements" },
        new string[] { "TEXTSRT", ".srt", "application/x-subrip", "multi", "edit", "SubRip captions" },
        new string[] { "TEXTSVG", ".svg", "image/svg+xml", "multi", "edit", "an SVG drawing, which is text" },
        new string[] { "TEXTTIME", "", "", "single", "", "a date and time, as YYYY-MM-DD HH:MM:SS" },
        new string[] { "TEXTTSV", ".tsv", "text/tab-separated-values", "multi", "edit", "tab-separated values" },
        new string[] { "TEXTURL", "", "", "single", "browse", "a web address, opened in the default browser" },
        new string[] { "TEXTVCAL", ".vcs", "text/x-vcalendar", "multi", "edit", "vCalendar events" },
        new string[] { "TEXTVCARD", ".vcf", "text/vcard", "multi", "edit", "vCard contacts" },
        new string[] { "TEXTVTT", ".vtt", "text/vtt", "multi", "edit", "WebVTT captions" },
        new string[] { "TEXTXML", ".xml", "application/xml", "multi", "edit", "XML" },
    };
    private static readonly Dictionary<string, string> dExtAlias = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase) {
        { ".html", "TEXTHTML" },
        { ".ini", "TEXTINIX" },
        { ".jpeg", "BLOBJPG" },
        { ".m3u8", "TEXTM3U" },
        { ".markdown", "TEXTMARKDOWN" },
        { ".text", "TEXTMEMO" },
    };
    private static readonly Dictionary<string, string> dTypeAlias = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase) {
        { "BLOBJPEG", "BLOBJPG" },
        { "TEXTJAVASCRIPT", "TEXTJSCRIPT" },
        { "TEXTJS", "TEXTJSCRIPT" },
        { "TEXTMD", "TEXTMARKDOWN" },
        { "TEXTPLAIN", "TEXTMEMO" },
        { "TEXTTEL", "TEXTPHONE" },
        { "TEXTTXT", "TEXTMEMO" },
    };
    private static string[] rowOf(string sType) {
        string s = canonical(sType);
        foreach (string[] a in aTypes) if (string.Equals(a[0], s, StringComparison.OrdinalIgnoreCase)) return a;
        return null;
    }
    // names: every type, alphabetical.
    public static string[] names() { List<string> l = new List<string>(); foreach (string[] a in aTypes) l.Add(a[0]); return l.ToArray(); }
    // canonical: a type's own name, from an alias such as BLOBJPEG, TEXTJS, TEXTMD or TEXTTEL; any other name upper-cased.
    public static string canonical(string sType) {
        string s = (sType ?? "").Trim().ToUpperInvariant(), sTo;
        return dTypeAlias.TryGetValue(s, out sTo) ? sTo : s;
    }
    // typeForName: the type for a file, by its extension; TEXTMEMO when the extension names no format.
    public static string typeForName(string sFileName) {
        string sExt = System.IO.Path.GetExtension(sFileName ?? "");
        if (string.IsNullOrEmpty(sExt)) return "TEXTMEMO";
        foreach (string[] a in aTypes) if (a[1].Length > 0 && string.Equals(a[1], sExt, StringComparison.OrdinalIgnoreCase)) return a[0];
        string sType; return dExtAlias.TryGetValue(sExt, out sType) ? sType : "TEXTMEMO";
    }
    // typeForMime: the type for a MIME type, such as image/png or application/json; "" when none matches.
    public static string typeForMime(string sMime) {
        string s = (sMime ?? "").Split(';')[0].Trim();
        foreach (string[] a in aTypes) if (a[2].Length > 0 && string.Equals(a[2], s, StringComparison.OrdinalIgnoreCase)) return a[0];
        return "";
    }
    public static string extensionFor(string sType) { string[] a = rowOf(sType); return a != null && a[1].Length > 0 ? a[1] : (isBinary(sType) ? ".bin" : ".txt"); }
    public static string mimeOf(string sType) { string[] a = rowOf(sType); return a != null && a[2].Length > 0 ? a[2] : (isBinary(sType) ? "application/octet-stream" : "text/plain"); }
    public static string actionOf(string sType) { string[] a = rowOf(sType); return a != null ? a[4] : ""; }
    public static string meaningOf(string sType) { string[] a = rowOf(sType); return a != null ? a[5] : ""; }
    // isBinary: whether the type stores bytes -- its name gives BLOB affinity.
    public static bool isBinary(string sType) { return affinityOf(canonical(sType)) == "BLOB" && (sType ?? "").Trim().Length > 0; }
    // isMultiline: whether the type holds lines of text: a format that is text, or an unknown TEXT name other than
    // TEXT, TEXTLINE and TEXTTIME; never a value type or a binary one.
    public static bool isMultiline(string sType) {
        string[] a = rowOf(sType);
        if (a != null) return a[3] == "multi";
        string s = canonical(sType);
        return affinityOf(s) == "TEXT" && s.StartsWith("TEXT") && s != "TEXT";
    }
    // affinityOf: the affinity SQLite gives a declared type, by its rules in their order (sqlite.org/datatype3.html).
    public static string affinityOf(string sDeclared) {
        string s = (sDeclared ?? "").ToUpperInvariant();
        if (s.Contains("INT")) return "INTEGER";
        if (s.Contains("CHAR") || s.Contains("CLOB") || s.Contains("TEXT")) return "TEXT";
        if (s.Contains("BLOB") || s.Trim().Length == 0) return "BLOB";
        if (s.Contains("REAL") || s.Contains("FLOA") || s.Contains("DOUB")) return "REAL";
        return "NUMERIC";
    }
}

public static class Schema {

// Column: one field as SQLite reports it. bComputed is true for a generated
// column (table_xinfo's hidden is not 0), which belongs to the table's own
// definition and is never added on its own.
public class Column {
    public int iPosition;
    public string sName = "";
    public string sType = "";
    public bool bComputed;
}

// The fields an edited trigger never watches: the trigger sets edited itself,
// added never changes, and marking a record is not editing it.
public static readonly string[] aNotEdits = new string[] { "added", "edited", "marked" };

// sColumnsSql: the query that lists a table's fields, one row each, in a form
// lParseColumns reads whatever the app's output writer does with it.
public static string sColumnsSql(string sTable, string sSchema) {
    return "SELECT '#' || cid || '#' || name || '#' || type || '#' || hidden || '#' AS c FROM pragma_table_xinfo('"
        + sTable.Replace("'", "''") + "', '" + sSchema.Replace("'", "''") + "')";
}

// lParseColumns: the fields from sColumnsSql's output, in table order.
public static List<Column> lParseColumns(string sOutput) {
    List<Column> lColumns = new List<Column>();
    foreach (Match m in Regex.Matches(sOutput ?? "", @"#(\d+)#([A-Za-z0-9_]+)#([A-Za-z0-9_ ]*)#(\d+)#")) {
        Column oColumn = new Column();
        oColumn.iPosition = int.Parse(m.Groups[1].Value);
        oColumn.sName = m.Groups[2].Value;
        oColumn.sType = m.Groups[3].Value.Trim();
        oColumn.bComputed = m.Groups[4].Value != "0";
        lColumns.Add(oColumn);
    }
    return lColumns;
}

// lMissingColumns: the template's ordinary fields the copy lacks, in the
// template's order. Computed fields are left to the table's definition. An
// empty lHere means the copy has no such table, and nothing is added to it.
public static List<Column> lMissingColumns(List<Column> lHere, List<Column> lTemplate) {
    List<Column> lMissing = new List<Column>();
    if (lHere == null || lHere.Count == 0 || lTemplate == null) return lMissing;
    HashSet<string> hHere = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
    foreach (Column oColumn in lHere) hHere.Add(oColumn.sName);
    foreach (Column oColumn in lTemplate) {
        if (oColumn.bComputed || hHere.Contains(oColumn.sName)) continue;
        lMissing.Add(oColumn);
    }
    return lMissing;
}

// sAddColumnSql: add one field, empty, at the end of the table. A field with
// no declared type is added as TEXTLINE, the Homer default for a line of text.
public static string sAddColumnSql(string sTable, Column oColumn) {
    return "ALTER TABLE main.\"" + sTable + "\" ADD COLUMN \"" + oColumn.sName + "\" "
        + (oColumn.sType.Length > 0 ? oColumn.sType : "TEXTLINE");
}

// sEditedTriggerName: the Homer name of a table's edited trigger.
public static string sEditedTriggerName(string sTable) {
    return "trg_" + sTable + "_edited";
}

// aEditedTriggerSql: the two statements that write a table's edited trigger
// again to watch every ordinary field but the id (the first column), added,
// edited and marked. Empty when there is nothing to watch. Run them only when
// the table already has the trigger.
public static string[] aEditedTriggerSql(string sTable, List<Column> lColumns) {
    if (lColumns == null || lColumns.Count == 0) return new string[0];
    string sId = lColumns[0].sName;
    List<string> lFields = new List<string>();
    foreach (Column oColumn in lColumns) {
        if (oColumn.iPosition == 0 || oColumn.bComputed) continue;
        if (Array.IndexOf(aNotEdits, oColumn.sName.ToLowerInvariant()) >= 0) continue;
        lFields.Add(oColumn.sName);
    }
    if (lFields.Count == 0) return new string[0];
    string sName = sEditedTriggerName(sTable);
    string sOf = string.Join(", ", lFields.ConvertAll(f => "\"" + f + "\"").ToArray());
    string sWhen = string.Join(" OR ", lFields.ConvertAll(f => "OLD.\"" + f + "\" IS NOT NEW.\"" + f + "\"").ToArray());
    return new string[] {
        "DROP TRIGGER IF EXISTS \"" + sName + "\"",
        "CREATE TRIGGER \"" + sName + "\" AFTER UPDATE OF " + sOf + " ON \"" + sTable + "\" FOR EACH ROW WHEN " + sWhen
            + " BEGIN UPDATE \"" + sTable + "\" SET edited = CURRENT_TIMESTAMP WHERE \"" + sId + "\" = NEW.\"" + sId + "\"; END"
    };
}

} // class Schema

} // namespace Homer
