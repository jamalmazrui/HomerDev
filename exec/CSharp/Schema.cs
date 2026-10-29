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
