r"""homerFts.py -- gives an SQLite table a full-text index that keeps itself current, for any Homer database. Part of
the HomerDev kit (1.292.0). A module to import, not a command.

    import homerFts
    homerFts.createIndex(oDb, "articles", "article_id", ["title", "author", "body"])
    homerFts.rebuild(oDb, "articles_fts")
    sProblem = homerFts.integrityProblem(oDb, "articles_fts")   # "" when the index is sound

WHAT IT MAKES. An FTS5 table, named <table>_fts unless another name is given, that holds no copy of the text: it
reads the text from the table itself (an external-content index), so a database is not twice its size. Three
triggers keep it current, so a record added, edited or deleted in DbDo, by a script or by another program is
searchable at once:

    trg_<fts>_insert   after a record is added: its text goes into the index
    trg_<fts>_delete   after a record is deleted: its old text comes out
    trg_<fts>_update   after any indexed field changes: the old text comes out, then the new goes in

FTS5 is told what to take out by its 'delete' command with the old values, which is why the update trigger fires only
when an indexed field changes: marking a record touches no indexed field and costs the index nothing.

THE SETTINGS. sTokenize defaults to "unicode61 remove_diacritics 2": words are split on Unicode rules and accents
are folded, so cafe finds café. "porter unicode61 remove_diacritics 2" adds English stemming, so describe finds
described and description; it finds more and ranks less exactly, so a template tries both and keeps one. sPrefix
"2 3" adds prefix indexes, so a search for blind* is fast.

SEARCHING, for a database's saved queries (DbDo runs them as SQL):

    SELECT a.title, snippet(articles_fts, -1, '', '', ' ... ', 24) AS passage
    FROM articles_fts JOIN articles a ON a.article_id = articles_fts.rowid
    WHERE articles_fts MATCH 'guide NEAR(dog, 5)'
    ORDER BY bm25(articles_fts, 10.0, 5.0, 1.0)

bm25 takes one weight per indexed column, in order; a lower score is a better match, so ORDER BY bm25 puts the best
first. snippet with empty markers gives plain text, which a screen reader reads without symbols.

DbDo LEAVES THE INDEX OUT OF ITS LIST OF TABLES (DbDo, 25 November 2026), with its shadow tables (_config, _data,
_docsize, _idx), since they are SQLite's bookkeeping, not anybody's records.
"""

sVersion = "1.292.0"
sDefaultTokenize = "unicode61 remove_diacritics 2"
sDefaultPrefix = "2 3"


def quoted(sName):
    """An SQL name in double quotes."""
    return '"' + sName.replace('"', '""') + '"'


def available(oDb):
    """Whether this SQLite has FTS5: a temporary table is made, searched and dropped."""
    try:
        oDb.execute("CREATE VIRTUAL TABLE temp.homer_fts5_probe USING fts5(sText)")
        oDb.execute("INSERT INTO temp.homer_fts5_probe (sText) VALUES ('probe')")
        iHits = oDb.execute("SELECT count(*) FROM temp.homer_fts5_probe WHERE homer_fts5_probe MATCH 'probe'").fetchone()[0]
        oDb.execute("DROP TABLE temp.homer_fts5_probe")
        return iHits == 1
    except Exception:
        return False


def indexDdl(sTable, sKey, lsColumns, sFts="", sTokenize=sDefaultTokenize, sPrefix=sDefaultPrefix):
    """The statements that make the index and its three triggers, in order."""
    sFts = sFts or sTable + "_fts"
    sCols = ", ".join(quoted(s) for s in lsColumns)
    sNew = ", ".join("new." + quoted(s) for s in lsColumns)
    sOld = ", ".join("old." + quoted(s) for s in lsColumns)
    sOptions = "content=%s, content_rowid=%s, tokenize='%s'" % (quoted(sTable), quoted(sKey), sTokenize)
    if sPrefix: sOptions += ", prefix='%s'" % sPrefix
    sDelete = "INSERT INTO %s (%s, rowid, %s) VALUES ('delete', old.%s, %s);" % (quoted(sFts), quoted(sFts), sCols, quoted(sKey), sOld)
    sInsert = "INSERT INTO %s (rowid, %s) VALUES (new.%s, %s);" % (quoted(sFts), sCols, quoted(sKey), sNew)
    sChanged = " OR ".join("old.%s IS NOT new.%s" % (quoted(s), quoted(s)) for s in lsColumns)
    return ["CREATE VIRTUAL TABLE %s USING fts5(%s, %s)" % (quoted(sFts), sCols, sOptions),
            "CREATE TRIGGER %s AFTER INSERT ON %s BEGIN %s END" % (quoted("trg_" + sFts + "_insert"), quoted(sTable), sInsert),
            "CREATE TRIGGER %s AFTER DELETE ON %s BEGIN %s END" % (quoted("trg_" + sFts + "_delete"), quoted(sTable), sDelete),
            "CREATE TRIGGER %s AFTER UPDATE OF %s ON %s WHEN %s BEGIN %s %s END" % (quoted("trg_" + sFts + "_update"), sCols, quoted(sTable), sChanged, sDelete, sInsert)]


def dropIndex(oDb, sFts):
    """Takes away an index and its triggers, if they are there."""
    for sSuffix in ("_insert", "_delete", "_update"): oDb.execute("DROP TRIGGER IF EXISTS " + quoted("trg_" + sFts + sSuffix))
    oDb.execute("DROP TABLE IF EXISTS " + quoted(sFts))
    return True


def createIndex(oDb, sTable, sKey, lsColumns, sFts="", sTokenize=sDefaultTokenize, sPrefix=sDefaultPrefix):
    """Makes the index and its triggers afresh, fills it from the table, and returns its name."""
    sFts = sFts or sTable + "_fts"
    dropIndex(oDb, sFts)
    for sStatement in indexDdl(sTable, sKey, lsColumns, sFts, sTokenize, sPrefix): oDb.execute(sStatement)
    rebuild(oDb, sFts)
    return sFts


def rebuild(oDb, sFts):
    """Refills the index from its table: after a bulk load made with the triggers off, or to mend it."""
    oDb.execute("INSERT INTO %s (%s) VALUES ('rebuild')" % (quoted(sFts), quoted(sFts)))
    return True


def optimize(oDb, sFts):
    """Merges the index's pieces into one, for the fastest searches in a database that will be read more than written."""
    oDb.execute("INSERT INTO %s (%s) VALUES ('optimize')" % (quoted(sFts), quoted(sFts)))
    return True


def integrityProblem(oDb, sFts):
    """"" when the index agrees with its table, otherwise what SQLite said. rank 1 asks FTS5 to compare against the
    content table too, not only the index with itself."""
    try:
        oDb.execute("INSERT INTO %s (%s, rank) VALUES ('integrity-check', 1)" % (quoted(sFts), quoted(sFts)))
        return ""
    except Exception as oError:
        return str(oError) or "the integrity check failed"
