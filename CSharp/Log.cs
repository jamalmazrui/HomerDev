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
// Nothing here throws. A program whose logging fails should still run, so every
// method swallows its own errors and sets Log.bWorking to false.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Text;

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

    // The log this session is writing to, for an About box or a "show the log"
    // command. Blank before start is called.
    public static string path { get { return sPath; } }

    // The folder the log is in, which is also where the settings live.
    public static string folder { get { return sFolder; } }

    // ------- starting and stopping -------

    // start: open this session's log and write the header block.
    //
    // sAppNameGiven is the program's name, and it decides the folder, so pass
    // the same name the installer uses. Called once, as early as possible: a
    // failure before the log opens is the one failure that cannot be explained
    // afterwards.
    public static bool start(string sAppNameGiven)
    {
        try
        {
            sAppName = (sAppNameGiven ?? "").Trim();
            if (sAppName == "") sAppName = "Homer";
            dtStarted = DateTime.Now;
            // Paths owns the layout, so the log lands where the convention
            // says and nothing here has to know the folder names.
            Paths.start(sAppName);
            sFolder = Paths.logs();
            sPath = Path.Combine(sFolder, sAppName + "-" +
                dtStarted.ToString("yyyyMMdd-HHmmss") + ".log");
            fLog = new StreamWriter(sPath, false, new UTF8Encoding(true));
            fLog.AutoFlush = true;
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

    // close: write the footer and let the file go. Safe to call twice, and safe
    // not to call at all -- AutoFlush means nothing written is ever lost.
    public static bool close()
    {
        try
        {
            if (fLog == null) return false;
            line("");
            line("Session ended " + DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") +
                 " after " + (int) (DateTime.Now - dtStarted).TotalSeconds + " seconds");
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

    // line: one line, exactly as given, with no timestamp and no level. For a
    // banner, a blank line, or a block of text that is easier to read plain.
    public static bool line(string sText)
    {
        try
        {
            if (fLog == null) return false;
            lock (oGate) { fLog.WriteLine(sText ?? ""); }
            return true;
        }
        catch (Exception)
        {
            bWorking = false;
            return false;
        }
    }

    // The ordinary three. Each stamps the time and the level, so a log can be
    // scanned for ERROR without reading it.
    public static bool info(string sText) { return level("INFO", sText); }
    public static bool warn(string sText) { return level("WARN", sText); }
    public static bool error(string sText) { return level("ERROR", sText); }

    private static bool level(string sLevel, string sText)
    {
        return line(DateTime.Now.ToString("HH:mm:ss") + "  " +
                    sLevel.PadRight(5) + "  " + (sText ?? ""));
    }

    // section: a heading, so a long log can be read by its parts.
    public static bool section(string sTitle)
    {
        line("");
        line("---- " + (sTitle ?? "") + " ----");
        return true;
    }

    // keyValue: a setting and its value, one per line, which is what makes a
    // log answer "what was it actually set to" without anybody guessing.
    public static bool keyValue(string sKey, string sValue)
    {
        return line("    " + (sKey ?? "").PadRight(24) + " = " + (sValue ?? ""));
    }

    // command: an external program that was run, and what it answered. Every
    // Homer script logs this, and so should every program that starts a process.
    public static bool command(string sCommand, int iExitCode)
    {
        return level(iExitCode == 0 ? "INFO" : "ERROR",
                     "Ran: " + sCommand + "   exit code " + iExitCode);
    }

    // exception: the message AND the stack. The stack is the part that saves
    // the evening, so it is never left out.
    public static bool exception(Exception oError)
    {
        if (oError == null) return false;
        level("ERROR", oError.GetType().Name + ": " + oError.Message);
        line(oError.StackTrace ?? "    (no stack trace)");
        if (oError.InnerException != null)
        {
            line("    Inner: " + oError.InnerException.GetType().Name + ": " +
                 oError.InnerException.Message);
        }
        return true;
    }

    // ------- the header block -------
    //
    // Everything that will be wanted later and cannot be worked out afterwards:
    // which build this was, on which Windows, as whom, from where, with what on
    // the command line.
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

        line(sAppName + " session log");
        line("Started " + dtStarted.ToString("yyyy-MM-dd HH:mm:ss"));
        section("Environment");
        keyValue("Version", sVersion);
        keyValue("Log file", sPath);
        try
        {
            keyValue("Program", Assembly.GetEntryAssembly() == null ? "(unknown)"
                     : Assembly.GetEntryAssembly().Location);
            keyValue("Working directory", Environment.CurrentDirectory);
            keyValue("Command line", Environment.CommandLine);
            keyValue("Windows", Environment.OSVersion.VersionString);
            keyValue("64-bit process", "" + Environment.Is64BitProcess);
            keyValue("CLR", Environment.Version.ToString());
            keyValue("User", Environment.UserName);
            keyValue("Machine", Environment.MachineName);
            keyValue("Screen reader", Say.speechDiagnostic());
        }
        catch (Exception)
        {
        }
        return true;
    }

    // ------- housekeeping -------

    // prune: keep the most recent logs and remove the rest, so the folder stays
    // readable. Silent: a log that cannot be deleted is not worth a message.
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
            if (iRemoved > 0) info("Removed " + iRemoved + " old session log" +
                                   (iRemoved == 1 ? "" : "s") + ", keeping the most recent " + c_iKeepLogs);
        }
        catch (Exception)
        {
        }
        return iRemoved;
    }

    // show: open this session's log in whatever reads a text file, for a
    // program that offers a "show the log" command. EdSharp, when it is there.
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
