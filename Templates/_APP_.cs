// _APP_.cs -- a Homer LAUNCHPAD APP: one dialog, one job, one result.
//
// This is the HomerDev starter. newHomerApp.cmd writes a copy of it with _APP_
// replaced by a real app name. It compiles and runs as it stands: it collects a
// source and an output folder, remembers every answer, and reports what it did.
// The only thing missing is the work itself, which goes in runJob().
//
// ------------------------------------------------------------------ AI NOTE
// If you are an AI asked to turn this into a working program, these are the
// rules the file already follows. Keep them.
//
//   * `using Homer;` gives you Lbc, Say, InixCodec, Util, Web and Keys. Build
//     on those rather than writing your own: they are shared, tested, and
//     tuned for screen readers.
//   * Build every dialog from Lbc primitives. Never place a control by hand
//     and never use a visual designer. ADD ORDER IS FOCUS ORDER.
//   * Camel Type naming: sString, iInteger, bBoolean, lsList, dDictionary,
//     oObject; lowerCamel methods; c_ before a constant; double quotes;
//     declarations alphabetical; functions, not subprocedures.
//   * Every control that the dialog conventions below name keeps its name, its
//     ampersand letter, and its command-line equivalent. A user who learns one
//     Homer app has learnt the shape of all of them.
//   * Anything the user answers is saved THE MOMENT they answer it, not at
//     exit, so a crash loses nothing.
//   * Speak only what the screen reader cannot know. It already announces the
//     window title and the focused control; do not repeat either.
// ---------------------------------------------------------------------------
//
// THE STANDARD LAUNCHPAD CONTROLS, in the order they are added, which is the
// order the user tabs through them. Each has a command-line equivalent so the
// same program can be scripted, and the two are named the same thing:
//
//   Source          text box   &Source          --source <path>
//   Browse source   button     &Browse source   (no switch: the path is
//                                                the --source value)
//   <options>       checkboxes                  --<option>
//   Output          text box   &Output          --output <path>
//   Choose output   button     &Choose output   (no switch, as above)
//   Use configuration  check   &Use configuration  --config <file>
//   View output     check      &View output     --view
//   OK              button     accepts, Enter or Control+Enter
//   Cancel          button     cancels, Escape
//   Help            button     &Help, or F1
//   Default settings button    &Default settings  --defaults
//
// Lbc puts the button row at the bottom with Help rightmost, wires Enter to OK
// wherever OK sits in the row, Escape to Cancel, and Control+Enter to OK from
// any control including the memo boxes that eat a bare Enter.
//
// TWO MESSAGE BOXES, both plain read-only dialogs a screen reader can arrow
// through line by line:
//   the HELP box       -- what the program does and what each field means.
//   the RESULTS box    -- what this run actually did. Only actions taken this
//                         session are reported. A count says "1 file", never
//                         "1 files", and "0 files" is a real answer.

using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Windows.Forms;
using Homer;

namespace _APP_
{

public static class Program
{
    // ---- constants --------------------------------------------------------
    private const string c_sAppName = "_APP_";
    private const string c_sSettingsFile = "_APP_.inix";
    private const string c_sSection = "Settings";

    // ---- settings, each saved the moment it is answered --------------------
    private static bool bUseConfig = false;
    private static bool bViewOutput = true;
    private static string sOutput = "";
    private static string sSource = "";

    [STAThread]
    public static int Main(string[] aArguments)
    {
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        loadSettings();

        // The command line does everything the dialog does. With any argument
        // the program runs headless and never opens a window, so it can be
        // driven from a batch file or another program.
        if (aArguments != null && aArguments.Length > 0)
            return runFromCommandLine(aArguments);

        return runFromDialog();
    }

    // ---- where the settings live ------------------------------------------
    //
    // Beside the executable when that is writable, which is the portable case:
    // a copy unzipped into a folder carries its settings with it. Under
    // %LOCALAPPDATA% otherwise, which is the installed case, because a program
    // in Program Files cannot write beside its own .exe.
    private static string settingsPath()
    {
        string sBeside = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, c_sSettingsFile);
        try
        {
            if (File.Exists(sBeside)) return sBeside;
            File.AppendAllText(sBeside, "");
            return sBeside;
        }
        catch (Exception)
        {
        }
        string sLocal = Path.Combine(Environment.GetFolderPath(
            Environment.SpecialFolder.LocalApplicationData), c_sAppName);
        try { Directory.CreateDirectory(sLocal); } catch (Exception) { }
        return Path.Combine(sLocal, c_sSettingsFile);
    }

    private static bool loadSettings()
    {
        string sPath = settingsPath();
        sSource = InixCodec.readValue(sPath, c_sSection, "Source", "");
        sOutput = InixCodec.readValue(sPath, c_sSection, "Output", "");
        bUseConfig = InixCodec.readValue(sPath, c_sSection, "UseConfig", "0") == "1";
        bViewOutput = InixCodec.readValue(sPath, c_sSection, "ViewOutput", "1") == "1";
        return true;
    }

    // saveSetting: one answer, written now. Called as each field is answered
    // rather than once at the end, so nothing is lost if the program is killed.
    private static bool saveSetting(string sKey, string sValue)
    {
        return InixCodec.writeValue(settingsPath(), c_sSection, sKey, sValue);
    }

    // ---- the dialog -------------------------------------------------------
    private static int runFromDialog()
    {
        using (LbcDialog dlg = new LbcDialog(c_sAppName, null))
        {
            dlg.addBand();
            TextBox tbSource = dlg.addInputBox("&Source:", sSource,
                "The file or folder to work on. Type a path, or press Browse source.");
            Button btnBrowseSource = dlg.addButton("&Browse source...",
                "Pick the source with a standard Open dialog.");
            btnBrowseSource.Click += delegate(object oSender, EventArgs evArgs)
            {
                string sPicked = pickFile("Choose the source");
                if (sPicked == "") return;
                tbSource.Text = sPicked;
                saveSetting("Source", sPicked);
            };
            dlg.endBand();

            dlg.addBand();
            TextBox tbOutput = dlg.addInputBox("&Output:", sOutput,
                "Where the result is written. Leave it blank to write beside the source.");
            Button btnChooseOutput = dlg.addButton("&Choose output...",
                "Pick the output folder with a standard Browse For Folder dialog.");
            btnChooseOutput.Click += delegate(object oSender, EventArgs evArgs)
            {
                string sPicked = pickFolder("Choose the output folder");
                if (sPicked == "") return;
                tbOutput.Text = sPicked;
                saveSetting("Output", sPicked);
            };
            dlg.endBand();

            CheckBox cbUseConfig = dlg.addCheckBox("&Use configuration", bUseConfig,
                "Take the settings from " + c_sSettingsFile + " instead of asking again next time.");
            CheckBox cbViewOutput = dlg.addCheckBox("&View output", bViewOutput,
                "Open the result when the work finishes.");

            // Every answer is saved as it is given, not at the end.
            cbUseConfig.CheckedChanged += delegate(object oSender, EventArgs evArgs)
            { saveSetting("UseConfig", cbUseConfig.Checked ? "1" : "0"); };
            cbViewOutput.CheckedChanged += delegate(object oSender, EventArgs evArgs)
            { saveSetting("ViewOutput", cbViewOutput.Checked ? "1" : "0"); };
            tbSource.Leave += delegate(object oSender, EventArgs evArgs)
            { saveSetting("Source", tbSource.Text); };
            tbOutput.Leave += delegate(object oSender, EventArgs evArgs)
            { saveSetting("Output", tbOutput.Text); };

            // Help is added by Lbc itself and lands rightmost. Default settings
            // sits beside it. OK is the accept button wherever it appears.
            string sButton = dlg.runWithButtons(new string[] { "Default settings", "OK", "Cancel" });

            if (string.Equals(sButton, "Default settings", StringComparison.OrdinalIgnoreCase))
            {
                restoreDefaults();
                return runFromDialog();
            }
            if (!string.Equals(sButton, "OK", StringComparison.OrdinalIgnoreCase))
                return 0;

            sSource = tbSource.Text.Trim();
            sOutput = tbOutput.Text.Trim();
            bUseConfig = cbUseConfig.Checked;
            bViewOutput = cbViewOutput.Checked;
        }

        List<string> lsReport = new List<string>();
        int iResult = runJob(lsReport);
        showResults(lsReport);
        return iResult;
    }

    private static bool restoreDefaults()
    {
        sSource = "";
        sOutput = "";
        bUseConfig = false;
        bViewOutput = true;
        saveSetting("Source", "");
        saveSetting("Output", "");
        saveSetting("UseConfig", "0");
        saveSetting("ViewOutput", "1");
        Say.say("Settings restored to their defaults");
        return true;
    }

    // ---- the command line, field for field with the dialog ----------------
    private static int runFromCommandLine(string[] aArguments)
    {
        List<string> lsReport = new List<string>();
        for (int i = 0; i < aArguments.Length; i++)
        {
            string sArgument = aArguments[i];
            string sNext = (i + 1 < aArguments.Length) ? aArguments[i + 1] : "";
            if (sArgument == "--help" || sArgument == "-h" || sArgument == "/?")
            {
                Console.WriteLine(helpText());
                return 0;
            }
            else if (sArgument == "--source") { sSource = sNext; i++; }
            else if (sArgument == "--output") { sOutput = sNext; i++; }
            else if (sArgument == "--config") { bUseConfig = true; }
            else if (sArgument == "--view") { bViewOutput = true; }
            else if (sArgument == "--defaults") { restoreDefaults(); }
            else if (sSource == "") { sSource = sArgument; }
            else
            {
                Console.WriteLine("I do not know the option " + sArgument + ".");
                Console.WriteLine("Run with --help to see the options.");
                return 1;
            }
        }
        int iResult = runJob(lsReport);
        foreach (string sLine in lsReport) Console.WriteLine(sLine);
        return iResult;
    }

    // ---- the work ---------------------------------------------------------
    //
    // AI NOTE: this is the one method to replace. Everything above and below it
    // is the shape every launchpad app shares. Add to lsReport only what was
    // actually done this run, one short line each, and return 0 on success.
    private static int runJob(List<string> lsReport)
    {
        if (sSource == "")
        {
            lsReport.Add("No source was given, so there was nothing to do.");
            return 1;
        }
        if (!File.Exists(sSource) && !Directory.Exists(sSource))
        {
            lsReport.Add("There is nothing at " + sSource + ".");
            return 1;
        }

        lsReport.Add("Source: " + sSource);
        if (sOutput != "") lsReport.Add("Output: " + sOutput);
        lsReport.Add("0 files written. The work itself is not written yet.");
        return 0;
    }

    // ---- the two message boxes --------------------------------------------
    private static bool showResults(List<string> lsReport)
    {
        StringBuilder sbText = new StringBuilder();
        foreach (string sLine in lsReport) sbText.AppendLine(sLine);
        HelpDialog.show(null, c_sAppName + " results", sbText.ToString());
        return true;
    }

    private static string helpText()
    {
        StringBuilder sbText = new StringBuilder();
        sbText.AppendLine(c_sAppName + " -- one dialog, one job, one result.");
        sbText.AppendLine("");
        sbText.AppendLine("Fields");
        sbText.AppendLine("  Source: the file or folder to work on.");
        sbText.AppendLine("  Output: where the result is written. Blank means beside the source.");
        sbText.AppendLine("  Use configuration: take the saved settings next time without asking.");
        sbText.AppendLine("  View output: open the result when the work finishes.");
        sbText.AppendLine("");
        sbText.AppendLine("Buttons");
        sbText.AppendLine("  OK starts the work. Enter and Control+Enter do the same.");
        sbText.AppendLine("  Cancel closes without doing anything. Escape does the same.");
        sbText.AppendLine("  Default settings puts every field back as it started.");
        sbText.AppendLine("  Help shows this. F1 does the same.");
        sbText.AppendLine("");
        sbText.AppendLine("Command line, which does everything the dialog does");
        sbText.AppendLine("  " + c_sAppName + " --source <path> [--output <path>] [--config] [--view]");
        sbText.AppendLine("  " + c_sAppName + " --defaults");
        sbText.AppendLine("  " + c_sAppName + " --help");
        return sbText.ToString();
    }

    // ---- the standard pickers ---------------------------------------------
    private static string pickFile(string sTitle)
    {
        using (OpenFileDialog dlg = new OpenFileDialog())
        {
            dlg.Title = sTitle;
            dlg.CheckFileExists = true;
            if (dlg.ShowDialog() != DialogResult.OK) return "";
            return dlg.FileName;
        }
    }

    private static string pickFolder(string sTitle)
    {
        using (FolderBrowserDialog dlg = new FolderBrowserDialog())
        {
            dlg.Description = sTitle;
            if (dlg.ShowDialog() != DialogResult.OK) return "";
            return dlg.SelectedPath;
        }
    }
}

} // namespace _APP_
