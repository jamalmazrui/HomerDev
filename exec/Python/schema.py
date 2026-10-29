# schema.py -- upgrading an SQLite database's structure without loss, for the Homer Tools.
#
# In the kit since 1.94.0 (29 October 2026). The same rules as exec\CSharp\Schema.cs:
# the kit decides and writes the SQL; the app runs it on its own sqlite3
# connection. Fields a newer template has gained are added, empty; computed
# fields are left to the table's definition; records are never touched.
#
# Copyright 2006-2026 by Jamal Mazrui
# MIT License. See License.md, which carries the terms in full.

import re

aNotEdits = ("added", "edited", "marked")

def sColumnsSql(sTable, sSchema):
    return ("SELECT '#' || cid || '#' || name || '#' || type || '#' || hidden || '#' AS c FROM pragma_table_xinfo('"
        + sTable.replace("'", "''") + "', '" + sSchema.replace("'", "''") + "')")

def lParseColumns(sOutput):
    lColumns = []
    for m in re.finditer(r"#(\d+)#([A-Za-z0-9_]+)#([A-Za-z0-9_ ]*)#(\d+)#", sOutput or ""):
        lColumns.append({"iPosition": int(m.group(1)), "sName": m.group(2), "sType": m.group(3).strip(), "bComputed": m.group(4) != "0"})
    return lColumns

def lMissingColumns(lHere, lTemplate):
    if not lHere or not lTemplate: return []
    hHere = set(d["sName"].lower() for d in lHere)
    return [d for d in lTemplate if not d["bComputed"] and d["sName"].lower() not in hHere]

def sAddColumnSql(sTable, dColumn):
    return 'ALTER TABLE main."' + sTable + '" ADD COLUMN "' + dColumn["sName"] + '" ' + (dColumn["sType"] or "TEXTLINE")

def sEditedTriggerName(sTable):
    return "trg_" + sTable + "_edited"

def aEditedTriggerSql(sTable, lColumns):
    if not lColumns: return []
    sId = lColumns[0]["sName"]
    lFields = [d["sName"] for d in lColumns if d["iPosition"] != 0 and not d["bComputed"] and d["sName"].lower() not in aNotEdits]
    if not lFields: return []
    sName = sEditedTriggerName(sTable)
    sOf = ", ".join('"' + f + '"' for f in lFields)
    sWhen = " OR ".join('OLD."' + f + '" IS NOT NEW."' + f + '"' for f in lFields)
    return ['DROP TRIGGER IF EXISTS "' + sName + '"',
        'CREATE TRIGGER "' + sName + '" AFTER UPDATE OF ' + sOf + ' ON "' + sTable + '" FOR EACH ROW WHEN ' + sWhen
        + ' BEGIN UPDATE "' + sTable + '" SET edited = CURRENT_TIMESTAMP WHERE "' + sId + '" = NEW."' + sId + '"; END']
