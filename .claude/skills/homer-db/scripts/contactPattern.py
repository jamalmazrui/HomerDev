"""contactPattern.py -- the DbDialog contact pattern for any Homer table of people, and a rebuild that applies it.

    python contactPattern.py <database.db> [table]       puts that table (default contacts) in the pattern

THE PATTERN (13 October 2026, from DbDialog). Jamal's DbDialog named the fields of its Contact table so that each has a
unique Alt letter, which a form built from the table, as Lbc and DbDo build theirs, can offer as its trigger:

    Title T, First Name F, Middle Name M, Last Name L, Job J, Enterprise E, Address1 1, Address2 2, City C, State S,
    Zip Z, Nation N, Office Phone O, Home Phone H, Wireless Phone W, Business Email B, Personal Email P, URL U,
    Date of Birth D, Gender G, and Extra Info X.

In a Homer table, URL and Extra Info are two of the standard fields every table ends with -- url, notes (Extra Info) and
tags -- so URL comes after Gender rather than before Date of Birth; its letter, U, is the same wherever it sits, and the
unique letters are the point of the pattern. The rest are columns in exactly DbDialog's order. A field a table needs beyond the pattern (JobTrail's role) comes right after enterprise
and keeps a letter of its own (R). The DbDo templates ContactTrail and JobTrail, and the convention-database skill's
Convention.db, follow it; a new table of people should start from lsContactFields below.

THE REBUILD keeps every row and value, adds any pattern field missing, puts the columns in the pattern's order, and keeps
the table's computed columns (look, prime), its indexes and its triggers as they were. SQLite cannot reorder columns in
place, so the table is copied into a new one and renamed, inside one transaction.
"""
import datetime, os, platform, re, sqlite3, sys

lsContactFields = ["title", "first_name", "middle_name", "last_name", "job", "enterprise", "address1", "address2", "city",
                   "state", "zip", "nation", "office_phone", "home_phone", "wireless_phone", "business_email",
                   "personal_email", "date_of_birth", "gender"]
# A CONTACT'S IDENTITY (13 October 2026): first|middle|last; the company when there is no last name; first|middle| when
# there is neither, so people known only by a first name stay distinct -- the key was empty for all of them, and the
# unique index let only one in. Every contact that had a last name or a company keeps its key, so no link moves.
sPrimeDef = ('"prime" TEXT GENERATED ALWAYS AS (iif(last_name IS NOT NULL AND length(last_name)>0, '
             "coalesce(first_name,'')||'|'||coalesce(middle_name,'')||'|'||coalesce(last_name,''), "
             "iif(enterprise IS NOT NULL AND length(enterprise)>0, enterprise, "
             "iif(length(coalesce(first_name,'')||coalesce(middle_name,''))>0, coalesce(first_name,'')||'|'||coalesce(middle_name,'')||'|', '')))) STORED")
lsLeading = ["added", "edited"]                 # after the id, as in every Homer table
lsTrailing = ["url", "notes", "tags"]           # the standard fields; notes is DbDialog's Extra Info


def columnDefs(sCreate):
    """The column definitions of a CREATE TABLE statement, split at top-level commas, as (name, definition)."""
    sBody = sCreate[sCreate.index("(") + 1: sCreate.rindex(")")]
    lParts, iDepth, sPart = [], 0, ""
    for sChar in sBody:
        if sChar == "(": iDepth += 1
        elif sChar == ")": iDepth -= 1
        if sChar == "," and iDepth == 0: lParts.append(sPart.strip()); sPart = ""
        else: sPart += sChar
    if sPart.strip(): lParts.append(sPart.strip())
    return [(re.match(r'"?(\w+)"?', s).group(1), s) for s in lParts]


def editedTrigger(oDb, sTable, fnLog):
    """THE EDITED TRIGGER NAMES EVERY FIELD (13 October 2026). A Homer table's trigger sets edited when a listed field
    changes, and the list was copied as it stood, so editing a field the pattern added -- office_phone -- left edited
    stale. It is written here from the table's own columns: every ordinary field but the id, added, edited and marked."""
    lCols = list(oDb.execute('PRAGMA table_xinfo("%s")' % sTable))
    sId = lCols[0][1]
    lsFields = [r[1] for r in lCols if r[6] == 0 and r[1] not in (sId, "added", "edited", "marked")]
    sName = "trg_%s_edited" % sTable
    sWant = ('CREATE TRIGGER "%s" AFTER UPDATE OF %s ON "%s" FOR EACH ROW WHEN %s BEGIN UPDATE "%s" SET edited = '
             'CURRENT_TIMESTAMP WHERE "%s" = NEW."%s"; END') % (sName, ", ".join('"%s"' % f for f in lsFields), sTable,
             " OR ".join('OLD."%s" IS NOT NEW."%s"' % (f, f) for f in lsFields), sTable, sId, sId)
    oHave = oDb.execute("SELECT sql FROM sqlite_master WHERE type='trigger' AND name=?", (sName,)).fetchone()
    if oHave and oHave[0] == sWant: return False
    oDb.execute('DROP TRIGGER IF EXISTS "%s"' % sName); oDb.execute(sWant)
    fnLog("%s: the edited trigger now covers %d fields" % (sTable, len(lsFields)))
    return True


def applyPattern(sDb, sTable="contacts", fnLog=print):
    oDb = sqlite3.connect(sDb)
    oDb.isolation_level = None
    sCreate = oDb.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (sTable,)).fetchone()[0]
    lDefs = columnDefs(sCreate)
    dDefs = dict(lDefs)
    sId = lDefs[0][0]
    lsGenerated = [n for n, s in lDefs if " GENERATED " in s.upper()]
    lsKnown = set([sId] + lsLeading + lsContactFields + lsTrailing + lsGenerated + ["marked"])
    lsExtra = [n for n, _ in lDefs if n not in lsKnown]
    lsOrder = [sId] + [n for n in lsLeading if n in dDefs]
    for sName in lsContactFields:
        lsOrder.append(sName)
        if sName == "enterprise": lsOrder += lsExtra
    lsOrder += [n for n in lsTrailing if n in dDefs] + lsGenerated + (["marked"] if "marked" in dDefs else [])
    lsAdded = [n for n in lsContactFields if n not in dDefs]
    lsNewDefs = [sPrimeDef if n == "prime" else dDefs.get(n, n + " TEXTLINE") for n in lsOrder]
    bPrimeSame = dDefs.get("prime", sPrimeDef) == sPrimeDef
    if [n for n, _ in lDefs] == lsOrder and bPrimeSame:
        bTrigger = editedTrigger(oDb, sTable, fnLog)
        fnLog("%s %s: already in the contact pattern%s" % (os.path.basename(sDb), sTable, "; its edited trigger was brought up to date" if bTrigger else ""))
        oDb.close(); return bTrigger
    lsSchema = [r[0] for r in oDb.execute("SELECT sql FROM sqlite_master WHERE tbl_name=? AND type IN ('index','trigger') AND sql IS NOT NULL", (sTable,))]
    iBefore = oDb.execute('SELECT count(*) FROM "%s"' % sTable).fetchone()[0]
    lsCopy = [n for n, _ in lDefs if n not in lsGenerated]
    oDb.execute("PRAGMA foreign_keys=OFF")
    oDb.execute("BEGIN")
    try:
        oDb.execute('CREATE TABLE "%s__pattern" (\n  %s\n)' % (sTable, ",\n  ".join(lsNewDefs)))
        oDb.execute('INSERT INTO "%s__pattern" (%s) SELECT %s FROM "%s"' % (sTable, ", ".join(lsCopy), ", ".join(lsCopy), sTable))
        oDb.execute('DROP TABLE "%s"' % sTable)
        oDb.execute('ALTER TABLE "%s__pattern" RENAME TO "%s"' % (sTable, sTable))
        for sSql in lsSchema: oDb.execute(sSql)
        editedTrigger(oDb, sTable, fnLog)
        iAfter = oDb.execute('SELECT count(*) FROM "%s"' % sTable).fetchone()[0]
        if iAfter != iBefore: raise RuntimeError("%d rows before, %d after" % (iBefore, iAfter))
        oDb.execute("COMMIT")
    except Exception:
        oDb.execute("ROLLBACK"); oDb.close(); raise
    sCheck = oDb.execute("PRAGMA integrity_check").fetchone()[0]
    oDb.execute("VACUUM"); oDb.close()
    fnLog("%s %s: %d rows kept; added %s; extra fields kept after enterprise: %s; integrity %s" % (
        os.path.basename(sDb), sTable, iAfter, ", ".join(lsAdded) or "none", ", ".join(lsExtra) or "none", sCheck))
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2: print(__doc__); sys.exit(2)
    sLog = os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), "contactPattern-%s.log" % datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    with open(sLog, "w", encoding="utf-8-sig") as fLog:
        def log(s): fLog.write(s + "\n"); print(s); return True
        log("contactPattern.py %s; Python %s on %s; %s" % (os.path.abspath(__file__), platform.python_version(), platform.platform(), " ".join(sys.argv[1:])))
        applyPattern(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "contacts", log)
    print("Log: " + sLog)
