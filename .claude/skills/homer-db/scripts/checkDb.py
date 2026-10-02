r"""
checkDb.py -- check a SQLite database against the Homer database conventions
that DbDo follows, and say what differs. Part of the homer-db skill.

    checkDb BookTrail.db          one database
    checkDb templates             every .db under a folder

It only reads. Each finding is "pass", "warn" (a convention not followed, which
DbDo copes with) or "fail" (something DbDo relies on is missing or wrong). The
console gives each database's counts; the log beside the database, in
<folder>\logs\<Name>-checkDb-<stamp>.log, gives every finding with its evidence.
"""
import datetime, glob, os, platform, re, sqlite3, sys

c_lsFieldTypes = ["BLOB", "BOOLEAN", "INTEGER", "NUMERIC", "REAL", "TEXT", "TEXTLINE", "TEXTMARKDOWN", "TEXTMEMO", "TEXTTIME"]
c_lsOwnTables = ["lookups", "maps", "views"]
c_dOwnColumns = {"lookups": ["tbl", "fld", "val", "ordinal", "src"], "maps": ["tbl1", "prime1", "kind", "tbl2", "prime2"],
                 "views": ["tbl", "fld", "val"]}
c_sStamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def singular(sTable):
    """The English singular of a plural table name: stories gives story,
    boxes gives box, jobs gives job. (DbDo's generator only drops a trailing s,
    which makes storie_id; the templates use story_id, which is right.)"""
    if sTable.endswith("ies"): return sTable[:-3] + "y"
    if sTable.endswith(("sses", "xes", "ches", "shes")): return sTable[:-2]
    if sTable.endswith("s") and not sTable.endswith("ss"): return sTable[:-1]
    return sTable


def plurals(sSingular):
    """The table names an id field may refer to."""
    lsNames = [sSingular + "s", sSingular + "es"]
    if sSingular.endswith("y"): lsNames.append(sSingular[:-1] + "ies")
    return lsNames


def isSystemTable(sName):
    return sName.lower().startswith(("sqlite_", "sqlean_"))


def checkDatabase(sPath):
    """Returns a list of (verdict, subject, evidence) for one database."""
    lsFindings = []
    def note(sVerdict, sSubject, sEvidence): lsFindings.append((sVerdict, sSubject, sEvidence))
    oCon = sqlite3.connect("file:%s?mode=ro" % sPath.replace("\\", "/"), uri=True)
    lsTables = [r[0] for r in oCon.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                if not isSystemTable(r[0])]
    lsTriggers = [r[0].lower() for r in oCon.execute("SELECT name FROM sqlite_master WHERE type='trigger'")]
    lsUser = [s for s in lsTables if s.lower() not in c_lsOwnTables]
    dPrimes = {}
    for sTable in lsTables:
        lsCols = oCon.execute('PRAGMA table_xinfo("%s")' % sTable).fetchall()   # cid, name, type, notnull, dflt, pk, hidden
        lsNames = [c[1] for c in lsCols]
        dCol = {c[1]: c for c in lsCols}
        sLower = sTable.lower()
        if sLower == "views":
            bOk = all(s in lsNames for s in c_dOwnColumns["views"])
            note("pass" if bOk else "fail", "views", "holds tbl, fld and val" if bOk else "lacks tbl, fld or val")
            continue
        sSub = sTable
        if not re.fullmatch(r"[a-z][a-z0-9_]*", sTable): note("warn", sSub, "name is not lower case with underscores")
        if not sTable.endswith("s"): note("warn", sSub, "name is not plural, so the id is %s_id" % singular(sTable))
        sPk = singular(sTable) + "_id"
        oFirst = lsCols[0] if lsCols else None
        if oFirst and oFirst[1] == sPk and oFirst[5] == 1 and (oFirst[2] or "").upper() == "INTEGER":
            note("pass", sSub, "first column is %s, the integer primary key" % sPk)
        else:
            note("fail", sSub, "first column should be %s INTEGER PRIMARY KEY AUTOINCREMENT, found %s" % (sPk, oFirst[1] if oFirst else "none"))
        for iIndex, sName in ((1, "added"), (2, "edited")):
            oCol = lsCols[iIndex] if len(lsCols) > iIndex else None
            if oCol and oCol[1] == sName and (oCol[2] or "").upper() == "TEXTTIME" and "CURRENT_TIMESTAMP" in str(oCol[4] or "").upper():
                note("pass", sSub, "%s is column %d, TEXTTIME defaulting to the current time" % (sName, iIndex + 1))
            else:
                note("fail" if sName not in lsNames else "warn", sSub, "%s should be column %d, TEXTTIME NOT NULL DEFAULT CURRENT_TIMESTAMP" % (sName, iIndex + 1))
        if lsNames and lsNames[-1] == "marked" and dCol["marked"][3] == 1:
            note("pass", sSub, "marked is the last column, never null")
        else:
            note("fail", sSub, "marked should be the last column, INTEGER NOT NULL DEFAULT 0")
        for sName in ("look", "prime"):
            if sName in dCol and dCol[sName][6] == 3:
                note("pass", sSub, "%s is a stored generated column" % sName)
            else:
                note("fail", sSub, "%s should be TEXT GENERATED ALWAYS AS (...) STORED" % sName)
        lsTail = [s for s in lsNames if s in ("url", "notes", "tags", "look", "prime", "marked")]
        lsWanted = [s for s in ("url", "notes", "tags", "look", "prime", "marked") if s in lsNames]
        if lsNames[-len(lsWanted):] == lsWanted: note("pass", sSub, "ends with " + ", ".join(lsWanted))
        else: note("warn", sSub, "should end with url, notes, tags, look, prime, marked in that order; ends with " + ", ".join(lsNames[-len(lsWanted):]))
        for oCol in lsCols:
            sType = (oCol[2] or "").upper().split("(")[0].strip()
            if oCol[6] in (2, 3): continue
            if sType and sType not in c_lsFieldTypes:
                note("warn", sSub, "%s has type %s, not one of DbDo's field types" % (oCol[1], oCol[2]))
        lsIdx = oCon.execute('PRAGMA index_list("%s")' % sTable).fetchall()
        bPrimeIdx, bUnique = False, False
        for oIdx in lsIdx:
            lsIdxCols = [r[2] for r in oCon.execute('PRAGMA index_info("%s")' % oIdx[1])]
            if lsIdxCols == ["prime"]:
                bPrimeIdx = True
                bUnique = bUnique or oIdx[2] == 1
        if bUnique: note("pass", sSub, "prime has a unique index")
        elif bPrimeIdx: note("warn", sSub, "prime is indexed but not unique, so two records could share one identity")
        else: note("warn", sSub, "prime has no index")
        if ("trg_%s_edited" % sTable).lower() in lsTriggers: note("pass", sSub, "trg_%s_edited keeps edited current" % sTable)
        else: note("warn", sSub, "no trg_%s_edited trigger, so edited changes only when DbDo itself edits" % sTable)
        if "maps" in [t.lower() for t in lsTables] and sLower not in c_lsOwnTables and "prime" in lsNames:
            for sTrig, sWhat in (("trg_%s_maps" % sTable, "edit"), ("trg_%s_maps_delete" % sTable, "deletion")):
                if sTrig.lower() in lsTriggers: note("pass", sSub, "%s keeps maps links whole after an %s" % (sTrig, sWhat))
                else: note("warn", sSub, "no %s trigger, so a record's maps links break on its %s" % (sTrig, sWhat))
        for sName in lsNames:
            if sName.endswith("_id") and sName != sPk:
                lsDeclared = [r[2] for r in oCon.execute('PRAGMA foreign_key_list("%s")' % sTable) if r[3] == sName]
                lsTargets = lsDeclared or [t for t in plurals(sName[:-3]) if t in lsTables]
                if lsTargets: note("pass", sSub, "%s refers to %s" % (sName, lsTargets[0]))
                else: note("warn", sSub, "%s names no table %s" % (sName, plurals(sName[:-3])[0]))
        if "prime" in lsNames:
            dPrimes[sTable] = set(r[0] for r in oCon.execute('SELECT prime FROM "%s"' % sTable))
        if sLower in c_dOwnColumns:
            lsMissing = [s for s in c_dOwnColumns[sLower] if s not in lsNames]
            note("fail" if lsMissing else "pass", sSub, ("lacks " + ", ".join(lsMissing)) if lsMissing else "holds " + ", ".join(c_dOwnColumns[sLower]))
    dLetters = {}
    for sTable in lsUser: dLetters.setdefault(sTable[0].lower(), []).append(sTable)
    lsShared = [", ".join(v) for v in dLetters.values() if len(v) > 1]
    if lsShared: note("warn", "tables", "share a first letter, so typing it does not reach one table: " + "; ".join(lsShared))
    else: note("pass", "tables", "%d user tables, each with its own first letter" % len(lsUser))
    if "lookups" in lsTables:
        for sTbl, sFld, iCount in oCon.execute("SELECT tbl, fld, count(*) FROM lookups GROUP BY tbl, fld"):
            if sTbl == "*": continue
            if sTbl not in lsTables: note("warn", "lookups", "%d values for %s.%s, but there is no table %s" % (iCount, sTbl, sFld, sTbl)); continue
            lsCols = [c[1] for c in oCon.execute('PRAGMA table_xinfo("%s")' % sTbl)]
            if sFld not in lsCols: note("warn", "lookups", "%d values for %s.%s, but %s has no field %s" % (iCount, sTbl, sFld, sTbl, sFld))
    if "maps" in lsTables and all(s in [c[1] for c in oCon.execute('PRAGMA table_xinfo("maps")')] for s in c_dOwnColumns["maps"]):
        iLinks, iDangling = 0, 0
        for sTbl1, sPrime1, sTbl2, sPrime2 in oCon.execute("SELECT tbl1, prime1, tbl2, prime2 FROM maps"):
            iLinks += 1
            if sPrime1 not in dPrimes.get(sTbl1, set()) or sPrime2 not in dPrimes.get(sTbl2, set()): iDangling += 1
        if iDangling: note("warn", "maps", "%d of %d links point at a record that is not there" % (iDangling, iLinks))
        else: note("pass", "maps", "all %d links point at records that exist" % iLinks)
    oCon.close()
    return lsFindings


def main():
    lsArgs = [s for s in sys.argv[1:] if not s.startswith("-")]
    if not lsArgs:
        print("Name a .db file or a folder of them, such as: checkDb BookTrail.db")
        return 1
    lsPaths = []
    for sArg in lsArgs:
        if os.path.isdir(sArg): lsPaths += sorted(glob.glob(os.path.join(sArg, "**", "*.db"), recursive=True))
        elif os.path.isfile(sArg): lsPaths.append(sArg)
        else: print("%s is not a file or folder." % sArg)
    iFailedAll = 0
    for sPath in lsPaths:
        sPath = os.path.abspath(sPath)
        sName = os.path.splitext(os.path.basename(sPath))[0]
        sLogDir = os.path.join(os.path.dirname(sPath), "logs")
        os.makedirs(sLogDir, exist_ok=True)
        sLog = os.path.join(sLogDir, "%s-checkDb-%s.log" % (sName, c_sStamp))
        with open(sLog, "w", encoding="utf-8-sig", newline="\r\n") as oLog:
            def logLine(sLevel, sText):
                oLog.write("%s %-5s %s\n" % (datetime.datetime.now().astimezone().isoformat(timespec="milliseconds"), sLevel, sText))
            logLine("INFO", "checkDb start pid=%d" % os.getpid())
            logLine("INFO", 'env script="%s" python=%s platform="%s" workingDirectory="%s" sqlite=%s' % (
                os.path.abspath(__file__), platform.python_version(), platform.platform(), os.getcwd(), sqlite3.sqlite_version))
            logLine("INFO", 'arguments database="%s"' % sPath)
            try:
                lsFindings = checkDatabase(sPath)
            except Exception as oError:
                import traceback
                logLine("ERROR", "exception " + str(oError))
                for sLine in traceback.format_exc().splitlines(): logLine("ERROR", "| " + sLine)
                print("%s could not be read: %s. The log has the details: %s" % (os.path.basename(sPath), oError, sLog))
                iFailedAll += 1
                continue
            for sVerdict, sSubject, sEvidence in lsFindings:
                logLine({"pass": "INFO", "warn": "WARN", "fail": "ERROR"}[sVerdict], "%s %s: %s" % (sVerdict, sSubject, sEvidence))
            dCount = {s: sum(1 for t in lsFindings if t[0] == s) for s in ("pass", "warn", "fail")}
            def noun(i, s): return "%d %s" % (i, s if i == 1 else s + "s")
            print("%s: %s passed, %s, %s." % (os.path.basename(sPath), noun(dCount["pass"], "check"),
                                               noun(dCount["warn"], "warning"), noun(dCount["fail"], "failure")))
            logLine("INFO", "checkDb end pass=%d warn=%d fail=%d" % (dCount["pass"], dCount["warn"], dCount["fail"]))
            iFailedAll += 1 if dCount["fail"] else 0
    if lsPaths: print("Each database's log, in its logs folder, lists every finding.")
    return 1 if iFailedAll else 0


if __name__ == "__main__":
    sys.exit(main())
