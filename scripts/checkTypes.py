"""checkTypes: proves Homer's column types (5 November 2026).

    checkTypes          check the vocabulary; on Windows, also how the SQLite ODBC driver reports each type to ADO

It checks three things and logs every finding in logs\\HomerDev-checkTypes-<time>.log:
  1. scripts\\columnTypes.py and Homer.ColumnTypes in exec\\CSharp\\Schema.cs list the same types, in the same order.
  2. A real SQLite gives each declared type the affinity its name says: TEXT names store text, BLOB names keep bytes.
  3. On Windows, with the SQLite3 ODBC Driver, the ADO type DbDo would see for each column: text types should come
     back as text, BLOB types as binary. This is logged and said, not failed, since the driver may be absent.
Exit 0 when 1 and 2 hold; 1 otherwise."""

import datetime, importlib.util, os, platform, re, sqlite3, sys, tempfile, traceback

sScriptDir = os.path.dirname(os.path.abspath(__file__))
sRoot = os.path.dirname(sScriptDir)
sLogDir = os.path.join(sRoot, "logs")
os.makedirs(sLogDir, exist_ok=True)
sLog = os.path.join(sLogDir, "HomerDev-checkTypes-%s.log" % datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))


def logLine(sText):
    with open(sLog, "a", encoding="utf-8") as oFile: oFile.write(datetime.datetime.now().isoformat(timespec="milliseconds") + "  " + sText + "\n")


def sayLine(sText):
    print(sText); logLine("CONSOLE: " + sText)


def main():
    logLine("checkTypes %s, python %s, %s, cwd %s, args %s" % (sys.argv[0], sys.version.split()[0], platform.platform(), os.getcwd(), sys.argv[1:]))
    logLine("SQLite %s" % sqlite3.sqlite_version)
    oSpec = importlib.util.spec_from_file_location("columnTypes", os.path.join(sScriptDir, "columnTypes.py"))
    oTypes = importlib.util.module_from_spec(oSpec); oSpec.loader.exec_module(oTypes)
    lsProblems = []
    # 1. the twins agree
    sCs = open(os.path.join(sRoot, "exec", "CSharp", "Schema.cs"), encoding="utf-8-sig").read()
    lCs = [tuple(m) for m in re.findall(r'new string\[\] \{ "((?:TEXT|BLOB)\w+)", "([^"]*)", "([^"]*)", "([^"]*)", "([^"]*)", "([^"]*)" \}', sCs)]
    if lCs != [tuple(t) for t in oTypes.lTypes]:
        lsProblems.append("columnTypes.py and Schema.cs differ: %d types in one, %d in the other" % (len(oTypes.lTypes), len(lCs)))
    else: logLine("twins agree: %d types" % len(lCs))
    # 2. SQLite gives each name the affinity it says
    lsNames = oTypes.names()
    oConn = sqlite3.connect(":memory:")
    oConn.execute("CREATE TABLE t (%s)" % ", ".join('"c%d" %s' % (i, s) for i, s in enumerate(lsNames)))
    oConn.execute("INSERT INTO t VALUES (%s)" % ", ".join(["123"] * len(lsNames)))
    lsStored = oConn.execute("SELECT %s FROM t" % ", ".join('typeof("c%d")' % i for i in range(len(lsNames)))).fetchone()
    for sName, sStored in zip(lsNames, lsStored):
        sWanted = "text" if sName.startswith("TEXT") else "integer"   # a number put in: TEXT affinity makes it text; BLOB keeps it
        sSaid = oTypes.affinityOf(sName)
        logLine("%-13s affinity %-7s; the number 123 stored as %s" % (sName, sSaid, sStored))
        if sStored != sWanted: lsProblems.append("%s: SQLite stored a number as %s, so its affinity is not what the name says" % (sName, sStored))
        if sSaid != ("TEXT" if sName.startswith("TEXT") else "BLOB"): lsProblems.append("%s: affinityOf says %s" % (sName, sSaid))
    # 3. the ODBC driver, as DbDo reads it
    if os.name == "nt":
        try:
            import win32com.client
            sDb = os.path.join(tempfile.gettempdir(), "HomerDev-checkTypes.db")
            if os.path.exists(sDb): os.remove(sDb)
            oFile = sqlite3.connect(sDb)
            oFile.execute("CREATE TABLE t (%s)" % ", ".join('"c%d" %s' % (i, s) for i, s in enumerate(lsNames))); oFile.commit(); oFile.close()
            oAdo = win32com.client.Dispatch("ADODB.Connection")
            oAdo.Open("DRIVER=SQLite3 ODBC Driver;Database=%s;" % sDb)
            oRs = win32com.client.Dispatch("ADODB.Recordset")
            oRs.Open("SELECT * FROM t", oAdo, 0, 1)
            setText, setBinary = {129, 130, 200, 201, 202, 203}, {128, 204, 205}
            lsOdd = []
            for i, sName in enumerate(lsNames):
                iType = oRs.Fields.Item(i).Type
                bOk = (iType in setText) if sName.startswith("TEXT") else (iType in setBinary)
                logLine("ODBC %-13s ADO type %d %s" % (sName, iType, "as expected" if bOk else "NOT as expected"))
                if not bOk: lsOdd.append("%s (ADO type %d)" % (sName, iType))
            oRs.Close(); oAdo.Close()
            try: os.remove(sDb)
            except Exception: pass
            if lsOdd: sayLine("Column types: the SQLite ODBC driver reports %d type%s unexpectedly to ADO: %s; the log has each one." % (len(lsOdd), "" if len(lsOdd) == 1 else "s", ", ".join(lsOdd)))
            else: sayLine("Column types: the SQLite ODBC driver reports all %d types to ADO as text or binary, as their names say." % len(lsNames))
        except Exception as oError:
            logLine("ODBC check not run: %s" % oError); logLine(traceback.format_exc())
            sayLine("Column types: the ODBC check could not run (%s); the log has why." % str(oError).splitlines()[0][:120])
    else: logLine("ODBC check skipped: not Windows")
    for s in lsProblems: logLine("PROBLEM: " + s)
    if lsProblems:
        sayLine("Column types: %d problem%s; the checkTypes log names each one." % (len(lsProblems), "" if len(lsProblems) == 1 else "s")); return 1
    sayLine("Column types: %d types; the twins agree and SQLite gives each the affinity its name says." % len(lsNames))
    return 0


if __name__ == "__main__":
    try: sys.exit(main())
    except Exception as oError:
        logLine(traceback.format_exc()); print("checkTypes stopped: %s" % oError); sys.exit(1)
