// Log.cs -- part of the shared Homer toolkit (namespace Homer).
//
// ONE SESSION, ONE LOG FILE, IN ONE PLACE EVERY HOMER PROGRAM AGREES ON.
//
//     %LOCALAPPDATA%\<App>\logs\<App>-<yyyyMMdd-HHmmss>.log
//
// The shape was taken from the two implementations that already worked:
// HomerScribe's session log, which names a file for the moment the run began,
// and HomerView's Python logger, which keeps the last thirty and deletes the
// rest. Both had grown the same answer separately, which is the usual sign that
// the answer belongs in the kit rather than in an app.
//
// WHY A FILE PER SESSION rather than one file appended to forever. A user who
// reports something an hour later still has the log from when it happened, and
// the log being read is never the log being written. Thirty of them reach back
// through a few weeks of ordinary use, and pruning keeps the folder readable.
//
// WHY %LOCALAPPDATA% rather than beside the program. A program installed under
// Program Files cannot write beside its own .exe. The log has to live somewhere
// the user owns, and the same folder holds the settings, so one folder is the
// whole of what a Homer program leaves on a machine.
//
// WHY SO MUCH DETAIL. Writing a line costs microseconds; not having the line
// costs an evening. The rule in this kit is that the log records the
// environment, every effective setting, every external command with its exit
// code, and every error with its full stack -- and that a failure never
// produces a console message with nothing in the log.
//
// WHAT GOES WHERE. The console gets short, plain sentences for a person. The
// log gets everything else. A log line is never spoken.
//
// Usage, which is three calls in the ordinary case:
//
//     using Homer;
//     Log.start("FruitBasketCs");                 // once, at startup
//     Log.info("Basket loaded, 4 fruits");        // whenever something happens
//     Log.close();                                // once, on the way out
//
// and, where it helps:
//
//     Log.section("Building the dialog");
//     Log.keyValue("Sort order", sSort);
//     Log.command("pandoc ReadMe.md", iExitCode);
//     Log.exception(oError);                      // message and stack
//     Log.warn("Pandoc was not found, so no HTML was written");
//
// THE LINE FORMAT (1.43.21), one event per line, every line stamped:
//     2026-09-27T16:16:40.123-07:00 INFO  session start app=2htm version=1.19.4 pid=4312
//     2026-09-27T16:16:40.125-07:00 INFO  env windows="Windows 11 25H2 (10.0.26200.7462)"
//     2026-09-27T16:16:41.002-07:00 ERROR run exit=1 ms=812 cmd="pandoc ReadMe.md"
//     2026-09-27T16:16:41.003-07:00 ERROR | at Homer.Web.get(...)
// An ISO 8601 time to the millisecond with its UTC offset, so logs from two
// machines or two programs sort and merge; the level in a five-character
// field; then the message. Facts are key=value (logfmt): a key is lower camel
// case; a value is written bare, or in double quotes when it holds a space, a
// quote or an equals sign, with an inner quote as \" and a final backslash
// doubled. A line that continues the one above -- a stack frame, a command's
// output -- starts its message with "| ". No line is left unstamped and no
// blank line is written, so every line can be read, filtered and sorted on
// its own. Log.py writes exactly the same.
//
// Nothing here throws. A program whose logging fails should still run, so every
// method swallows its own errors and sets Log.bWorking to false.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Text;
using Microsoft.Win32;

namespace Homer {

public static class Log
{
    // How many session logs to keep. Thirty reaches back through a few weeks.
    public const int c_iKeepLogs = 30;

    public static bool bWorking = false;

    private static DateTime dtStarted = DateTime.Now;
    private static object oGate = new object();
    private static string sAppName = "";
    private static string sFolder = "";
    private static string sPath = "";
    private static StreamWriter fLog = null;
    // Facts already written, so a program that repeats one of the header's
    // facts after start() -- FileDir writes Version and Program again -- does
    // not write it twice.
    private static HashSet<string> hsFacts = new HashSet<string>();

    // The log this session is writing to, for an About box or a "show the log"
    // command. Blank before start is called.
    public static string path { get { return sPath; } }

    // The folder the log is in, which is also where the settings live.
    public static string folder { get { return sFolder; } }

    // ------- starting and stopping -------

    // start: open this session's log and write the header facts. Called once,
    // as early as possible: a failure before the log opens is the one failure
    // that cannot be explained afterwards.
    public static bool start(string sAppNameGiven)
    {
        try
        {
            sAppName = (sAppNameGiven ?? "").Trim();
            if (sAppName == "") sAppName = "Homer";
            dtStarted = DateTime.Now;
            Paths.start(sAppName);
            sFolder = Paths.logs();
            sPath = Path.Combine(sFolder, sAppName + "-" +
                dtStarted.ToString("yyyyMMdd-HHmmss") + ".log");
            string sFallbackReason = "";
            if (!Directory.Exists(sFolder))
            {
                // NOWHERE TO WRITE IS NOT A REASON TO WRITE NOTHING (1.43.48).
                // The session is logged in the temporary folder instead, and
                // the log says why.
                sFallbackReason = "the logs folder " + sFolder + " could not be made";
                sFolder = Path.GetTempPath();
                sPath = Path.Combine(sFolder, sAppName + "-" + dtStarted.ToString("yyyyMMdd-HHmmss") + ".log");
            }
            // SHARED FOR READING, NOT FOR DELETING (1.43.48). Read-write sharing
            // lets a zipper or an editor copy the live log. Delete sharing,
            // added in 1.43.40, also let "Zip then delete" or the recycle bin
            // remove the log of a program still running -- which then went on
            // writing to a file nobody could see, and a session's whole record
            // was lost. A live log is refused to deletion again, as it was.
            fLog = new StreamWriter(new FileStream(sPath, FileMode.Create, FileAccess.Write,
                FileShare.ReadWrite), new UTF8Encoding(true));
            fLog.AutoFlush = true;
            if (sFallbackReason != "") level("WARN", "log written to the temporary folder, because " + sFallbackReason);
            bWorking = true;
            writeHeader();
            prune();
            return true;
        }
        catch (Exception)
        {
            bWorking = false;
            return false;
        }
    }

    // close: the last line, with how long the session ran. Safe to call twice,
    // and safe not to call at all -- AutoFlush means nothing written is lost.
    public static bool close()
    {
        try
        {
            if (fLog == null) return false;
            level("INFO", "session end seconds=" +
                  (DateTime.Now - dtStarted).TotalSeconds.ToString("0.000",
                  System.Globalization.CultureInfo.InvariantCulture));
            fLog.Close();
            fLog = null;
            return true;
        }
        catch (Exception)
        {
            return false;
        }
    }

    // ------- writing -------

    // line: a line of plain text, stamped INFO. A blank line is not written:
    // every line in a Homer log is an event a program can read on its own.
    public static bool line(string sText)
    {
        if (String.IsNullOrEmpty(sText)) return true;
        return level("INFO", sText);
    }

    // The ordinary three. A log can be scanned for ERROR without reading it.
    public static bool info(string sText) { return level("INFO", sText); }
    public static bool warn(string sText) { return level("WARN", sText); }
    public static bool error(string sText) { return level("ERROR", sText); }

    // stamp: the time as every Homer log writes it -- ISO 8601, milliseconds,
    // UTC offset. Public so a program writing its own file can match it.
    public static string stamp()
    {
        return DateTimeOffset.Now.ToString("yyyy-MM-dd'T'HH:mm:ss.fffzzz",
            System.Globalization.CultureInfo.InvariantCulture);
    }

    // Each line of the text becomes its own stamped line; lines after the
    // first begin "| ", so a reader knows they continue the event above.
    private static bool level(string sLevel, string sText)
    {
        try
        {
            if (fLog == null) return false;
            string sPrefix = stamp() + " " + sLevel.PadRight(5) + " ";
            string[] aLines = (sText ?? "").Replace("\r\n", "\n").Split('\n');
            StringBuilder oOut = new StringBuilder();
            bool bFirst = true;
            foreach (string sOne in aLines)
            {
                if (!bFirst && sOne.Trim() == "") continue;
                oOut.Append(sPrefix).Append(bFirst ? "" : "| ").Append(sOne.TrimEnd()).Append("\r\n");
                bFirst = false;
            }
            lock (oGate) { fLog.Write(oOut.ToString()); }
            return true;
        }
        catch (Exception)
        {
            bWorking = false;
            return false;
        }
    }

    // section: a marker, so a long log can be read by its parts.
    public static bool section(string sTitle)
    {
        return level("INFO", "---- " + (sTitle ?? "") + " ----");
    }

    // keyValue: a setting and its value as one fact, key=value. The key is
    // made lower camel case -- "Sort order" is written sortOrder -- so the
    // same fact has the same name in every Homer log.
    public static bool keyValue(string sKey, string sValue)
    {
        string sFact = key(sKey) + "=" + value(sValue);
        if (hsFacts.Contains(sFact)) return true;
        hsFacts.Add(sFact);
        return level("INFO", "env " + sFact);
    }

    // command: an external program that was run, and what it answered.
    public static bool command(string sCommand, int iExitCode)
    {
        return level(iExitCode == 0 ? "INFO" : "ERROR",
                     "run exit=" + iExitCode + " cmd=" + value(sCommand));
    }

    // command, timed: the same, with how long it took.
    public static bool command(string sCommand, int iExitCode, long iMilliseconds)
    {
        return level(iExitCode == 0 ? "INFO" : "ERROR",
                     "run exit=" + iExitCode + " ms=" + iMilliseconds + " cmd=" + value(sCommand));
    }

    // exception: the type, the message AND the stack -- every frame on its own
    // continued line -- and each inner exception the same way.
    public static bool exception(Exception oError)
    {
        if (oError == null) return false;
        Exception oAt = oError;
        string sLead = "exception";
        while (oAt != null)
        {
            level("ERROR", sLead + " type=" + oAt.GetType().FullName + " message=" + value(oAt.Message)
                  + "\n" + (oAt.StackTrace ?? "(no stack trace)"));
            oAt = oAt.InnerException;
            sLead = "inner";
        }
        return true;
    }

    // ------- the pieces of a fact -------

    // key: lower camel case from any label -- "Log file" -> logFile,
    // "Process 64-bit" -> process64Bit.
    public static string key(string sLabel)
    {
        // Words are runs of letters and digits. The first is lower case; each
        // one after starts with a capital. A word in capitals throughout is an
        // abbreviation and is treated as a word: "CLR" -> clr, "NVDA client"
        // -> nvdaClient, not cLR.
        StringBuilder oOut = new StringBuilder();
        foreach (string sWord in System.Text.RegularExpressions.Regex.Split(sLabel ?? "", "[^A-Za-z0-9]+"))
        {
            if (sWord == "") continue;
            string sPart = sWord.ToUpperInvariant() == sWord ? sWord.ToLowerInvariant() : sWord;
            if (oOut.Length == 0) oOut.Append(Char.ToLowerInvariant(sPart[0])).Append(sPart.Substring(1));
            else oOut.Append(Char.ToUpperInvariant(sPart[0])).Append(sPart.Substring(1));
        }
        return oOut.Length == 0 ? "value" : oOut.ToString();
    }

    // value: bare when it can be, quoted when it must be.
    public static string value(string sValue)
    {
        string s = sValue ?? "";
        if (s != "" && s.IndexOfAny(new char[] { ' ', '"', '=', '\t' }) < 0) return s;
        s = s.Replace("\"", "\\\"");
        if (s.EndsWith("\\")) s += "\\";
        return "\"" + s + "\"";
    }

    // ------- the header -------
    //
    // Everything that will be wanted later and cannot be worked out afterwards:
    // which build this was, on which Windows, as whom, from where, with what on
    // the command line, and which screen reader was listening.
    private static bool writeHeader()
    {
        string sVersion = "unknown";
        try
        {
            Assembly oAssembly = Assembly.GetEntryAssembly() ?? Assembly.GetExecutingAssembly();
            sVersion = "" + oAssembly.GetName().Version;
            Type oBuild = Type.GetType("BuildVersion");
            if (oBuild != null)
            {
                FieldInfo oField = oBuild.GetField("Version");
                if (oField != null) sVersion = "" + oField.GetValue(null);
            }
        }
        catch (Exception)
        {
        }

        level("INFO", "session start app=" + value(sAppName) + " version=" + value(sVersion)
              + " pid=" + Process.GetCurrentProcess().Id);
        keyValue("Log file", sPath);
        try
        {
            keyValue("Program", Assembly.GetEntryAssembly() == null ? "(unknown)"
                     : Assembly.GetEntryAssembly().Location);
            keyValue("Working directory", Environment.CurrentDirectory);
            keyValue("Arguments", String.Join(" ", Environment.GetCommandLineArgs(), 1,
                     Math.Max(0, Environment.GetCommandLineArgs().Length - 1)));
            keyValue("Windows", windowsVersion());
            keyValue("Process 64-bit", "" + Environment.Is64BitProcess);
            keyValue("CLR", Environment.Version.ToString());
            keyValue("User", Environment.UserName);
            keyValue("Machine", Environment.MachineName);
            foreach (KeyValuePair<string, string> oFact in Say.speechFacts())
                keyValue(oFact.Key, oFact.Value);
        }
        catch (Exception)
        {
        }
        return true;
    }

    // windowsVersion: the Windows actually running. Environment.OSVersion
    // answers 6.2.9200 -- Windows 8 -- to any program whose manifest does not
    // declare Windows 10, which 2htm's and urlFido's logs showed on Windows 11.
    // The registry does not lie.
    public static string windowsVersion()
    {
        try
        {
            string sKey = @"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion";
            string sBuild = "" + Registry.GetValue(sKey, "CurrentBuild", "");
            string sUbr = "" + Registry.GetValue(sKey, "UBR", "");
            string sDisplay = "" + Registry.GetValue(sKey, "DisplayVersion", "");
            int iBuild;
            Int32.TryParse(sBuild, out iBuild);
            string sName = iBuild >= 22000 ? "Windows 11" : "Windows 10";
            return (sName + " " + sDisplay).Trim() + " (10.0." + sBuild + (sUbr != "" ? "." + sUbr : "") + ")";
        }
        catch (Exception)
        {
            return Environment.OSVersion.VersionString;
        }
    }

    // ------- housekeeping -------

    // prune: keep the most recent logs and remove the rest.
    public static int prune()
    {
        int iRemoved = 0;
        try
        {
            List<FileInfo> loLogs = new List<FileInfo>(
                new DirectoryInfo(sFolder).GetFiles(sAppName + "-*.log"));
            loLogs.Sort(delegate(FileInfo oOne, FileInfo oTwo)
            { return oTwo.LastWriteTime.CompareTo(oOne.LastWriteTime); });
            for (int i = c_iKeepLogs; i < loLogs.Count; i++)
            {
                try { loLogs[i].Delete(); iRemoved++; } catch (Exception) { }
            }
            if (iRemoved > 0) info("prune removed=" + iRemoved + " kept=" + c_iKeepLogs);
        }
        catch (Exception)
        {
        }
        return iRemoved;
    }

    // show: open this session's log in whatever reads a text file.
    public static bool show()
    {
        try
        {
            if (sPath == "" || !File.Exists(sPath)) return false;
            Process.Start(sPath);
            return true;
        }
        catch (Exception)
        {
            return false;
        }
    }
}

} // namespace Homer (Log.cs)
