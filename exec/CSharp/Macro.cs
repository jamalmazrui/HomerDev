// Macro.cs: Homer's macro recorder engine (kit 1.231.0, 15 November 2026), shared source an app compiles beside
// Inix.cs. The first app to use it is DbDo, which records its record-navigation commands.
//
// WHAT A MACRO IS. A list of the app's own commands, as the person ran them, saved as an .inix file with
// FileTask = macro in its header and one [step] section per command. Not keystrokes and not mouse clicks: a command
// replays the same way whatever window layout, screen reader or keyboard the person has.
//
// WHAT IS RECORDED. Only what the app says succeeded. A command handler that returns has not proved it did anything
// -- Go To can be cancelled, Next Record can sit on the last row -- so the app calls record() itself, after the
// outcome is known. Anything else the person did while recording is a gap: the recording is marked Incomplete and
// will not play, rather than playing a sequence that leaves something out.
//
// EXPECTED AGAINST ACTUAL. Before each step plays, the app is asked what the step should leave behind (expect),
// and after it, what it did leave (observe). The two are logged side by side for every step, and a step whose
// outcome differs stops playback there. The kit's own test (scripts\testMacro) proves this gate with a host that
// claims success without doing the work.
//
// THREADS. A session belongs to the thread that made it, a window's UI thread; playback awaits only a short yield
// between steps, so the window stays responsive and Escape can cancel. Application.Idle is never taken to mean a
// command has finished.
using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Threading.Tasks;

namespace Homer
{
    public sealed class MacroStep
    {
        public string sArgument = "";
        public string sCommand = "";
        public string sCommandId = "";
    }

    public sealed class MacroDocument
    {
        public bool bIncomplete;
        public List<MacroStep> lsSteps = new List<MacroStep>();
        public string sApp = "";
        public string sName = "Recorded macro";
        public string sRequires = "";
    }

    // What an app gives the engine. expect and observe speak the same words -- DbDo's are "row 7 of 12" -- so they
    // can be compared; expect returns "" when the outcome cannot be said in advance, and that step is then logged
    // but not compared.
    public interface IMacroHost
    {
        string sApp { get; }
        string sScope { get; }
        bool execute(MacroStep macroStep);
        string expect(MacroStep macroStep);
        bool log(string sMessage);
        string observe();
        bool validate(MacroStep macroStep);
    }

    public sealed class MacroSession
    {
        public const string sFileTask = "macro";
        public const string sVersion = "1";
        private const int iMaxBytes = 2097152;
        private const int iMaxSteps = 10000;
        private const int iMaxValue = 32768;
        private const int iYieldMs = 25;
        private CancellationTokenSource ctsPlay;
        private readonly IMacroHost macroHost;
        private MacroDocument macroDocument = new MacroDocument();
        private readonly int iThread;
        private readonly List<string> lsAudit = new List<string>();

        public bool bIncomplete { get { return macroDocument.bIncomplete; } }
        public bool bPlaying { get; private set; }
        public bool bRecording { get; private set; }
        public int iCount { get { return macroDocument.lsSteps.Count; } }
        public int iMismatches { get; private set; }
        public int iPlayed { get; private set; }
        public string sName { get { return macroDocument.sName; } }

        public MacroSession(IMacroHost hostGiven)
        {
            if (hostGiven == null) throw new ArgumentNullException("hostGiven");
            macroHost = hostGiven;
            iThread = Thread.CurrentThread.ManagedThreadId;
        }

        // The last playback, one line per step played: "commandId|argument|expected|actual". A test compares it
        // with what it meant to happen.
        public List<string> auditLines()
        {
            return new List<string>(lsAudit);
        }

        private bool checkThread()
        {
            if (Thread.CurrentThread.ManagedThreadId != iThread) throw new InvalidOperationException("Use the macro on the thread of its window.");
            return true;
        }

        private bool requireIdle()
        {
            checkThread();
            if (bPlaying || bRecording) throw new InvalidOperationException("Stop the macro first.");
            return true;
        }

        private static string normalizeScope(string sValue)
        {
            return (sValue ?? "").Replace("\r\n", "\n").Replace("\r", "\n");
        }

        private static string oneLine(string sValue)
        {
            return normalizeScope(sValue).Replace("\n", " / ");
        }

        private bool checkScope()
        {
            if (macroDocument.sApp != macroHost.sApp) throw new InvalidOperationException("This macro was recorded in " + macroDocument.sApp + ", not " + macroHost.sApp + ".");
            if (macroDocument.sRequires.Length > 0 && normalizeScope(macroDocument.sRequires) != normalizeScope(macroHost.sScope))
                throw new InvalidOperationException("This macro was recorded for one view and plays only there: " + oneLine(macroDocument.sRequires));
            return true;
        }

        public bool start(bool bPortable)
        {
            requireIdle();
            if (string.IsNullOrEmpty(macroHost.sScope)) throw new InvalidOperationException("Open a database view with records first.");
            macroDocument = new MacroDocument();
            macroDocument.sApp = macroHost.sApp;
            macroDocument.sRequires = bPortable ? "" : macroHost.sScope;
            bRecording = true;
            macroHost.log("Macro recording started; " + (bPortable ? "any view" : "this view: " + oneLine(macroHost.sScope)) + "; state " + macroHost.observe());
            return true;
        }

        public bool stop()
        {
            checkThread();
            bRecording = false;
            macroHost.log("Macro recording stopped; steps " + iCount + "; incomplete " + (bIncomplete ? "yes" : "no"));
            return true;
        }

        // The app calls this only after it has seen the command succeed.
        public bool record(string sId, string sCommand, string sArgument)
        {
            MacroStep macroStep;
            checkThread();
            if (!bRecording || bPlaying) return false;
            checkScope();
            if (iCount >= iMaxSteps) { gap("the limit of " + iMaxSteps + " steps was reached"); return false; }
            macroStep = new MacroStep { sArgument = sArgument ?? "", sCommand = sCommand ?? "", sCommandId = sId ?? "" };
            validateStep(macroStep);
            if (!macroHost.validate(macroStep)) throw new InvalidOperationException("Command is not available for a macro: " + sCommand);
            macroDocument.lsSteps.Add(macroStep);
            macroHost.log("Recorded step " + iCount + ": " + describe(macroStep) + "; state after " + macroHost.observe());
            return true;
        }

        public bool gap(string sReason)
        {
            checkThread();
            if (!bRecording) return false;
            macroDocument.bIncomplete = true;
            macroHost.log("Recording gap, so the macro is incomplete: " + sReason);
            return true;
        }

        public bool cancel()
        {
            checkThread();
            if (ctsPlay != null) { ctsPlay.Cancel(); macroHost.log("Macro playback cancel requested"); }
            return true;
        }

        private static string describe(MacroStep macroStep)
        {
            return macroStep.sCommand + " (" + macroStep.sCommandId + ")" + (macroStep.sArgument.Length > 0 ? " with " + macroStep.sArgument : "");
        }

        public async Task<bool> playAsync()
        {
            int iStep = 0;
            string sActual, sBefore, sExpected, sVerdict;
            requireIdle();
            if (SynchronizationContext.Current == null) throw new InvalidOperationException("Playback needs the window's UI thread.");
            if (macroDocument.bIncomplete) throw new InvalidOperationException("This recording has actions a macro cannot repeat, so it does not play. Record it again with supported commands only.");
            if (iCount == 0) throw new InvalidOperationException("There are no macro steps.");
            checkScope();
            foreach (MacroStep macroStep in macroDocument.lsSteps)
                if (!macroHost.validate(macroStep)) throw new InvalidOperationException("Command is not available here: " + macroStep.sCommand);
            lsAudit.Clear();
            iMismatches = 0;
            iPlayed = 0;
            ctsPlay = new CancellationTokenSource();
            bPlaying = true;
            try
            {
                macroHost.log("Macro playback started: " + macroDocument.sName + "; steps " + iCount + "; state " + macroHost.observe());
                foreach (MacroStep macroStep in macroDocument.lsSteps)
                {
                    iStep++;
                    // A yield, so Escape and repainting get their turn; not a test that anything has finished.
                    await Task.Delay(iYieldMs, ctsPlay.Token);
                    ctsPlay.Token.ThrowIfCancellationRequested();
                    checkThread();
                    checkScope();
                    if (!macroHost.validate(macroStep)) throw new InvalidOperationException("Step " + iStep + ", " + macroStep.sCommand + ", is not available now.");
                    sBefore = macroHost.observe();
                    sExpected = macroHost.expect(macroStep) ?? "";
                    if (!macroHost.execute(macroStep)) throw new InvalidOperationException("Step " + iStep + ", " + macroStep.sCommand + ", did not complete.");
                    sActual = macroHost.observe() ?? "";
                    iPlayed++;
                    lsAudit.Add(macroStep.sCommandId + "|" + macroStep.sArgument + "|" + sExpected + "|" + sActual);
                    sVerdict = sExpected.Length == 0 ? "not compared" : (sExpected == sActual ? "same" : "DIFFERENT");
                    macroHost.log("Audit step " + iStep + " of " + iCount + ": " + describe(macroStep) + "; before " + sBefore + "; expected " + (sExpected.Length > 0 ? sExpected : "(not said)") + "; actual " + sActual + "; " + sVerdict);
                    if (sExpected.Length > 0 && sExpected != sActual)
                    {
                        iMismatches++;
                        throw new InvalidOperationException("Step " + iStep + ", " + macroStep.sCommand + ", left " + sActual + " where " + sExpected + " was expected.");
                    }
                }
                macroHost.log("Macro completed; steps played " + iPlayed + " of " + iCount + "; differences 0");
                return true;
            }
            catch (Exception exError)
            {
                macroHost.log("Macro stopped at step " + iStep + " of " + iCount + "; steps played " + iPlayed + "; differences " + iMismatches + "; " + exError.GetType().Name + ": " + exError.Message);
                throw;
            }
            finally
            {
                bPlaying = false;
                ctsPlay.Dispose();
                ctsPlay = null;
            }
        }

        private static bool validateStep(MacroStep macroStep)
        {
            if (macroStep == null || string.IsNullOrEmpty(macroStep.sCommandId) || macroStep.sCommandId.Length > 128 ||
                macroStep.sCommand == null || macroStep.sCommand.Length > 256 || macroStep.sArgument == null || macroStep.sArgument.Length > iMaxValue)
                throw new InvalidDataException("Invalid macro step.");
            return true;
        }

        private static string fieldValue(InixCodec.Section section, string sKey, bool bRequired)
        {
            string sResult = null;
            foreach (InixCodec.Pair pair in section.Pairs)
            {
                if (!string.Equals(pair.Key, sKey, StringComparison.OrdinalIgnoreCase)) continue;
                if (sResult != null) throw new InvalidDataException("Duplicate macro field: " + sKey);
                sResult = pair.Value;
            }
            if (bRequired && string.IsNullOrEmpty(sResult)) throw new InvalidDataException("Missing macro field: " + sKey);
            return sResult ?? "";
        }

        // Version 1 knows these fields and no others: a Keys, Dot or Type field from a later design is refused,
        // not ignored, so a macro never plays with part of it unread.
        private static bool checkFields(InixCodec.Section section, string sAllowed)
        {
            foreach (InixCodec.Pair pair in section.Pairs)
                if (sAllowed.IndexOf("|" + pair.Key.ToLowerInvariant() + "|", StringComparison.Ordinal) < 0) throw new InvalidDataException("Unsupported macro field: " + pair.Key);
            return true;
        }

        public static bool isMacroFile(string sPath)
        {
            try
            {
                if (!File.Exists(sPath) || new FileInfo(sPath).Length > iMaxBytes) return false;
                foreach (InixCodec.Section section in InixCodec.read(sPath))
                    if (string.Equals(section.Name, "Global", StringComparison.OrdinalIgnoreCase)) return string.Equals(fieldValue(section, "FileTask", true), sFileTask, StringComparison.OrdinalIgnoreCase);
            }
            catch (Exception) { return false; }
            return false;
        }

        public bool load(string sPath)
        {
            bool bGlobal = false;
            List<InixCodec.Section> lsSections;
            MacroDocument macroLoaded = new MacroDocument();
            MacroStep macroStep;
            string sIncomplete;
            requireIdle();
            if (new FileInfo(sPath).Length > iMaxBytes) throw new InvalidDataException("Macro exceeds 2 MiB.");
            lsSections = InixCodec.read(sPath);
            foreach (InixCodec.Section section in lsSections)
            {
                if (string.Equals(section.Name, "Global", StringComparison.OrdinalIgnoreCase))
                {
                    if (bGlobal) throw new InvalidDataException("Duplicate macro header.");
                    bGlobal = true;
                    checkFields(section, "|filetask|macroversion|app|name|requires|incomplete|note|");
                    if (!string.Equals(fieldValue(section, "FileTask", true), sFileTask, StringComparison.OrdinalIgnoreCase) || fieldValue(section, "MacroVersion", true) != sVersion)
                        throw new InvalidDataException("Unsupported macro format.");
                    macroLoaded.sApp = fieldValue(section, "App", true);
                    macroLoaded.sName = fieldValue(section, "Name", true);
                    macroLoaded.sRequires = fieldValue(section, "Requires", false);
                    if (macroLoaded.sRequires.Length > iMaxValue || macroLoaded.sName.Length > 256) throw new InvalidDataException("Macro header is too long.");
                    sIncomplete = fieldValue(section, "Incomplete", false);
                    if (sIncomplete != "" && sIncomplete != "yes") throw new InvalidDataException("Invalid Incomplete field.");
                    macroLoaded.bIncomplete = sIncomplete == "yes";
                }
                else if (string.Equals(section.Name, "step", StringComparison.OrdinalIgnoreCase))
                {
                    checkFields(section, "|commandid|command|argument|note|");
                    macroStep = new MacroStep { sArgument = fieldValue(section, "Argument", false), sCommand = fieldValue(section, "Command", true), sCommandId = fieldValue(section, "CommandId", true) };
                    validateStep(macroStep);
                    if (!macroHost.validate(macroStep)) throw new InvalidDataException("Unknown or unavailable command: " + macroStep.sCommandId);
                    macroLoaded.lsSteps.Add(macroStep);
                    if (macroLoaded.lsSteps.Count > iMaxSteps) throw new InvalidDataException("Too many macro steps.");
                }
                else throw new InvalidDataException("Unsupported macro section: " + section.Name);
            }
            if (!bGlobal || macroLoaded.sApp != macroHost.sApp) throw new InvalidDataException("Macro header is missing or belongs to another app.");
            macroDocument = macroLoaded;
            macroHost.log("Macro loaded from " + sPath + ": " + macroDocument.sName + "; steps " + iCount + "; incomplete " + (bIncomplete ? "yes" : "no") + "; " + (macroDocument.sRequires.Length > 0 ? "this view only" : "any view"));
            return true;
        }

        public bool save(string sPath, string sTitle)
        {
            List<InixCodec.Section> lsSections = new List<InixCodec.Section>();
            InixCodec.Section section = new InixCodec.Section("Global");
            string sFull = Path.GetFullPath(sPath);
            string sTemp = sFull + "." + Guid.NewGuid().ToString("N") + ".inix";
            requireIdle();
            if (string.IsNullOrWhiteSpace(sTitle) || sTitle.Length > 256) throw new ArgumentException("Give the macro a name of at most 256 characters.");
            section.Pairs.Add(new InixCodec.Pair("FileTask", sFileTask));
            section.Pairs.Add(new InixCodec.Pair("MacroVersion", sVersion));
            section.Pairs.Add(new InixCodec.Pair("App", macroDocument.sApp));
            section.Pairs.Add(new InixCodec.Pair("Name", sTitle));
            if (macroDocument.sRequires.Length > 0) section.Pairs.Add(new InixCodec.Pair("Requires", macroDocument.sRequires));
            if (macroDocument.bIncomplete) section.Pairs.Add(new InixCodec.Pair("Incomplete", "yes"));
            lsSections.Add(section);
            foreach (MacroStep macroStep in macroDocument.lsSteps)
            {
                section = new InixCodec.Section("step");
                section.Pairs.Add(new InixCodec.Pair("CommandId", macroStep.sCommandId));
                section.Pairs.Add(new InixCodec.Pair("Command", macroStep.sCommand));
                if (macroStep.sArgument.Length > 0) section.Pairs.Add(new InixCodec.Pair("Argument", macroStep.sArgument));
                lsSections.Add(section);
            }
            try
            {
                // The kit's writer, then the size check, before a good file is replaced.
                InixCodec.writeAsConfig(sTemp, lsSections);
                if (new FileInfo(sTemp).Length > iMaxBytes) throw new InvalidDataException("Macro exceeds 2 MiB.");
                if (File.Exists(sFull)) File.Replace(sTemp, sFull, null);
                else File.Move(sTemp, sFull);
            }
            finally
            {
                if (File.Exists(sTemp)) File.Delete(sTemp);
                if (File.Exists(sTemp + ".homer-write.tmp")) File.Delete(sTemp + ".homer-write.tmp");
            }
            macroDocument.sName = sTitle;
            macroHost.log("Macro saved to " + sFull + ": " + sTitle + "; steps " + iCount + "; incomplete " + (bIncomplete ? "yes" : "no"));
            return true;
        }
    }
}
