// testMacro.cs: proves exec\CSharp\Macro.cs (kit 1.231.0). scripts\testMacro.py compiles it with the .NET
// Framework's own C# 5 compiler, beside Inix.cs and Macro.cs, runs it, and keeps every line it prints in
// logs\HomerDev-testMacro-<time>.log. Each check prints PASS or FAIL with what was expected and what happened.
//
// The host here is a pretend database view of 12 rows that answers the macro engine as DbDo's does: "row N of 12".
// A second host claims every step succeeded without moving, which the expected-against-actual gate must catch.
using Homer;
using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Threading.Tasks;

internal sealed class MacroTestContext : SynchronizationContext
{
    private readonly Queue<Action> lsWork = new Queue<Action>();

    public override void Post(SendOrPostCallback callback, object vState)
    {
        lock (lsWork) lsWork.Enqueue(delegate { callback(vState); });
    }

    // Runs posted work on this thread until the task ends, as a window's message loop would.
    public bool pump(Task task)
    {
        Action action;
        DateTime dtDeadline = DateTime.UtcNow.AddSeconds(10);
        while (!task.IsCompleted)
        {
            if (DateTime.UtcNow > dtDeadline) throw new TimeoutException("The test's message pump timed out.");
            action = null;
            lock (lsWork) { if (lsWork.Count > 0) action = lsWork.Dequeue(); }
            if (action != null) action();
            else Thread.Sleep(1);
        }
        task.GetAwaiter().GetResult();
        return true;
    }
}

internal sealed class MacroTestHost : IMacroHost
{
    public bool bFail, bLie;
    public int iCalls, iRow = 1, iRows = 12;
    public string sApp { get { return "DbDo"; } }
    public string sScope { get; set; }

    public bool execute(MacroStep macroStep)
    {
        if (bFail) return false;
        iCalls++;
        if (bLie) return true;
        iRow = target(macroStep);
        return true;
    }

    public string expect(MacroStep macroStep)
    {
        return "row " + target(macroStep) + " of " + iRows;
    }

    public bool log(string sMessage)
    {
        Console.WriteLine("  host log: " + sMessage);
        return true;
    }

    public string observe()
    {
        return "row " + iRow + " of " + iRows;
    }

    private int target(MacroStep macroStep)
    {
        int iTarget;
        if (macroStep.sCommandId == "firstRecord") return 1;
        if (macroStep.sCommandId == "lastRecord") return iRows;
        if (macroStep.sCommandId == "nextRecord") return Math.Min(iRow + 1, iRows);
        if (macroStep.sCommandId == "previousRecord") return Math.Max(iRow - 1, 1);
        if (macroStep.sCommandId == "goToRecord" && int.TryParse(macroStep.sArgument, out iTarget)) return iTarget;
        return iRow;
    }

    public bool validate(MacroStep macroStep)
    {
        int iTarget;
        if (macroStep.sCommandId == "goToRecord") return int.TryParse(macroStep.sArgument, out iTarget) && iTarget >= 1 && iTarget <= iRows;
        if (macroStep.sCommandId == "firstRecord" || macroStep.sCommandId == "lastRecord" || macroStep.sCommandId == "nextRecord" || macroStep.sCommandId == "previousRecord") return macroStep.sArgument == "";
        return false;
    }
}

internal static class MacroTests
{
    private static int iFailed, iPassed;

    private static bool check(bool bValue, string sName, string sExpected, string sActual)
    {
        if (bValue) { iPassed++; Console.WriteLine("PASS " + sName + ": " + sActual); }
        else { iFailed++; Console.WriteLine("FAIL " + sName + ": expected " + sExpected + "; actual " + sActual); }
        return bValue;
    }

    private static string failure(Action action)
    {
        try { action(); }
        catch (Exception exError) { return exError.GetType().Name + ": " + exError.Message; }
        return "";
    }

    private static bool refuses(string sName, Action action)
    {
        string sError = failure(action);
        return check(sError.Length > 0, sName, "an error", sError.Length > 0 ? "refused with " + sError : "no error");
    }

    private static int Main()
    {
        string[] aParts;
        byte[] binFile;
        int iCalls;
        List<string> lsActual, lsExpected;
        MacroTestContext macroContext = new MacroTestContext();
        MacroTestHost macroHost = new MacroTestHost { sScope = "C:\\DATA\\TEST.DB\ncustomers\nfilter | city=Boston\norder" };
        MacroTestHost macroLiar = new MacroTestHost { sScope = macroHost.sScope, bLie = true };
        MacroSession macroLiarSession = new MacroSession(macroLiar);
        MacroSession macroSession = new MacroSession(macroHost);
        string sDirectory = Path.Combine(Path.GetTempPath(), "HomerMacro-" + Guid.NewGuid().ToString("N"));
        string sPath = Path.Combine(sDirectory, "test.inix");
        string sScope = macroHost.sScope;
        string sText;
        Task task;
        Console.WriteLine("testMacro: .NET " + Environment.Version + ", " + (Environment.Is64BitProcess ? "64" : "32") + "-bit, " + Environment.OSVersion);
        Directory.CreateDirectory(sDirectory);
        SynchronizationContext.SetSynchronizationContext(macroContext);
        try
        {
            // 1. A recording of six navigation steps, saved, loaded and played from another row.
            macroHost.iRow = 4;
            macroSession.start(false);
            foreach (string sStep in new string[] { "firstRecord|First Record|", "nextRecord|Next Record|", "nextRecord|Next Record|", "goToRecord|Go To|9", "previousRecord|Previous Record|", "lastRecord|Last Record|" })
            {
                aParts = sStep.Split('|');
                macroSession.record(aParts[0], aParts[1], aParts[2]);
            }
            refuses("a second Record while recording", delegate { macroSession.start(false); });
            refuses("Play while recording", delegate { macroContext.pump(macroSession.playAsync()); });
            macroSession.stop();
            macroSession.save(sPath, "Six steps");
            binFile = File.ReadAllBytes(sPath);
            check(binFile.Length > 3 && binFile[0] == 239 && binFile[1] == 187 && binFile[2] == 191, "UTF-8 with BOM", "EF BB BF", binFile.Length > 3 ? binFile[0].ToString("X2") + " " + binFile[1].ToString("X2") + " " + binFile[2].ToString("X2") : "a short file");
            sText = File.ReadAllText(sPath);
            check(!sText.Replace("\r\n", "").Contains("\n"), "CRLF line ends", "every line ending CRLF", sText.Replace("\r\n", "").Contains("\n") ? "a bare LF" : "every line ending CRLF");
            Console.WriteLine("  saved macro:\r\n" + sText);
            check(MacroSession.isMacroFile(sPath), "macro file found by its header", "FileTask = macro", MacroSession.isMacroFile(sPath) ? "found" : "not found");
            macroSession.load(sPath);
            check(macroSession.iCount == 6, "repeated [step] sections kept", "6 steps", macroSession.iCount + " steps");
            macroHost.iRow = 7;
            iCalls = macroHost.iCalls;
            macroContext.pump(macroSession.playAsync());
            lsExpected = new List<string> { "firstRecord||row 1 of 12|row 1 of 12", "nextRecord||row 2 of 12|row 2 of 12", "nextRecord||row 3 of 12|row 3 of 12", "goToRecord|9|row 9 of 12|row 9 of 12", "previousRecord||row 8 of 12|row 8 of 12", "lastRecord||row 12 of 12|row 12 of 12" };
            lsActual = macroSession.auditLines();
            check(string.Join("; ", lsActual) == string.Join("; ", lsExpected), "audit trail of playback", string.Join("; ", lsExpected), string.Join("; ", lsActual));
            check(macroSession.iMismatches == 0 && macroSession.iPlayed == 6, "no differences", "6 played, 0 different", macroSession.iPlayed + " played, " + macroSession.iMismatches + " different");
            check(macroHost.iRow == 12, "final row", "row 12", "row " + macroHost.iRow);
            check(macroSession.iCount == 6 && !macroSession.bPlaying && macroHost.iCalls == iCalls + 6, "nothing recorded during playback", "6 steps, 6 calls", macroSession.iCount + " steps, " + (macroHost.iCalls - iCalls) + " calls");

            // 2. The gate: a host that says a step succeeded without doing it is stopped at that step.
            macroLiar.iRow = 7;
            macroLiarSession.load(sPath);
            refuses("a step whose outcome differs", delegate { macroContext.pump(macroLiarSession.playAsync()); });
            check(macroLiarSession.iMismatches == 1 && macroLiarSession.iPlayed == 1 && macroLiar.iCalls == 1, "playback stops at the first difference", "1 played, 1 different, 1 call", macroLiarSession.iPlayed + " played, " + macroLiarSession.iMismatches + " different, " + macroLiar.iCalls + " call(s)");

            // 3. Scope: a macro for this view does nothing in another.
            iCalls = macroHost.iCalls;
            macroHost.sScope = "C:\\DATA\\OTHER.DB\ncustomers\n\norder";
            refuses("this-view macro in another view", delegate { macroContext.pump(macroSession.playAsync()); });
            check(macroHost.iCalls == iCalls, "no effect in the wrong view", "0 calls", (macroHost.iCalls - iCalls) + " calls");
            macroHost.sScope = sScope;

            // 4. A step that reports failure stops playback.
            macroHost.bFail = true;
            refuses("a step that fails", delegate { macroContext.pump(macroSession.playAsync()); });
            check(!macroSession.bPlaying && macroHost.iCalls == iCalls, "failure stops playback", "not playing, 0 calls", (macroSession.bPlaying ? "playing" : "not playing") + ", " + (macroHost.iCalls - iCalls) + " calls");
            macroHost.bFail = false;

            // 5. Cancel before the first step runs.
            task = macroSession.playAsync();
            macroSession.cancel();
            refuses("cancelled playback", delegate { macroContext.pump(task); });
            check(macroHost.iCalls == iCalls && !macroSession.bPlaying, "cancel before the first step", "0 calls", (macroHost.iCalls - iCalls) + " calls");

            // 6. Files the engine must refuse, keeping the macro it has.
            File.WriteAllText(sPath, sText.Replace("CommandId = nextRecord", "CommandId = deleteRecord"));
            refuses("an unknown command", delegate { macroSession.load(sPath); });
            check(macroSession.iCount == 6, "a refused load keeps the current macro", "6 steps", macroSession.iCount + " steps");
            File.WriteAllText(sPath, sText.Replace("MacroVersion = 1", "MacroVersion = 2"));
            refuses("a later macro version", delegate { macroSession.load(sPath); });
            File.WriteAllText(sPath, sText.Replace("CommandId = nextRecord", "CommandId = nextRecord\r\nKeys = {DOWN}"));
            refuses("a Keys field", delegate { macroSession.load(sPath); });
            File.WriteAllText(sPath, sText.Replace("MacroVersion = 1", "MacroVersion = 1\r\nMacroVersion = 1"));
            refuses("a duplicate field", delegate { macroSession.load(sPath); });
            File.WriteAllText(sPath, sText.Replace("App = DbDo", "App = EdSharp"));
            refuses("another app's macro", delegate { macroSession.load(sPath); });
            File.WriteAllText(sPath, sText.Replace("Argument = 9", "Argument = 99"));
            refuses("a Go To past the last row", delegate { macroSession.load(sPath); });
            File.WriteAllBytes(sPath, new byte[2097153]);
            refuses("a file over 2 MiB", delegate { macroSession.load(sPath); });
            check(macroSession.iCount == 6, "an oversized load keeps the current macro", "6 steps", macroSession.iCount + " steps");

            // 7. An any-view macro plays in another view.
            macroSession.start(true);
            macroSession.record("nextRecord", "Next Record", "");
            macroSession.stop();
            macroHost.sScope = "another view";
            macroHost.iRow = 2;
            macroContext.pump(macroSession.playAsync());
            check(macroHost.iRow == 3 && macroSession.iMismatches == 0, "any-view macro reused", "row 3, 0 different", "row " + macroHost.iRow + ", " + macroSession.iMismatches + " different");

            // 8. A recording with a gap does not play.
            iCalls = macroHost.iCalls;
            macroSession.start(true);
            macroSession.record("nextRecord", "Next Record", "");
            macroSession.gap("a key no command claims");
            macroSession.stop();
            macroSession.save(sPath, "Incomplete");
            macroSession.load(sPath);
            check(macroSession.bIncomplete, "Incomplete = yes survives saving", "incomplete", macroSession.bIncomplete ? "incomplete" : "complete");
            refuses("an incomplete macro", delegate { macroContext.pump(macroSession.playAsync()); });
            check(macroHost.iCalls == iCalls, "an incomplete macro has no effect", "0 calls", (macroHost.iCalls - iCalls) + " calls");
        }
        catch (Exception exError)
        {
            iFailed++;
            Console.WriteLine("FAIL unexpected error: " + exError);
        }
        finally
        {
            try { Directory.Delete(sDirectory, true); } catch (Exception) { }
        }
        Console.WriteLine("testMacro: " + iPassed + " passed, " + iFailed + " failed");
        return iFailed == 0 ? 0 : 1;
    }
}
