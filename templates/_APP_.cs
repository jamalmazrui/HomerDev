// _APP_.cs -- a Homer LAUNCH APP: one dialog, one job, one Results box.
//
// This is the HomerDev starter. newHomerApp writes a copy of it with _APP_
// replaced by a real app name. It compiles and runs as it stands: it collects the
// source paths and an output directory, takes the options every launch app shares,
// and reports what it did. The only thing missing is the work itself, which goes
// in runJob().
//
// ------------------------------------------------------------------ AI NOTE
// If you are an AI asked to turn this into a working program, these are the
// rules the file already follows. Keep them.
//
//   * `using Homer;` gives you Lbc, LaunchDialog, Say, InixCodec, Util, Web,
//     Paths, Log and Elevate. Build on those rather than writing your own: they
//     are shared, tested, and tuned for screen readers. To convert files, use
//     the kit's Conversion.convert, never a converter of your own.
//   * THE DIALOG IS THE KIT'S LaunchDialog (kit 1.89.0, help\LaunchDialog.md and
//     the homer-launch-dialog skill). Never build its standard bands by hand. Put
//     the app's own controls between addSourceBand and addOutputBand, in bands
//     of their own: first the checkboxes choosing the transformations, then any
//     other controls shaping the work. Add no Guide button and no Log session
//     checkbox: logging is automatic and Help says where the logs are.
//   * ADD ORDER IS FOCUS ORDER. Never place a control by hand, never use a
//     visual designer, never set TabIndex.
//   * Camel Type naming: sString, iInteger, bBoolean, lsList, dDictionary,
//     oObject; lowerCamel methods; constants named like variables, on lines of
//     their own; double quotes; declarations alphabetical; functions, not
//     subprocedures.
//   * Speak only what the screen reader cannot know. It already announces the
//     window title and the focused control; do not repeat either.
//   * Every run from the dialog ends with LaunchDialog.finish: the Results box,
//     then the output directory if View output directory is checked, then the
//     app closes.
// ---------------------------------------------------------------------------
//
// THE STANDARD CONTROLS, in the order Tab moves through them, with the
// command-line switch for each (a long switch is the label, a short one the
// Alt letter; /switch, -switch or --switch, in any case):
//
//   Source paths             text box  &Source paths            bare paths, -s
//   Browse local source      button    &Browse local source
//   <the app's own bands>
//   Output directory         text box  &Output directory        -o, --output-directory
//   Choose output directory  button    &Choose output directory
//   Force replacements       check     &Force replacements      -f, --force-replacements
//   Use configuration        check     &Use configuration       -u, --use-configuration
//   View output directory    check     &View output directory   -v, --view-output-directory
//   Default settings, Help   buttons                            -d, --default-settings
//   OK and Cancel, alone at the bottom right.
//
// Control+Enter is OK and Escape is Cancel from any control; F1 is Help, whose box
// lists each field with its tip, names F11 and the log folder, and ends with the
// version check; F11 checks at once from anywhere.
//
// THE DEFAULTS ARE DELIBERATE: Source paths starts at the user's Documents
// folder; Output directory is derived from the source -- the folder itself, or
// the folder of a single file or pattern -- and follows the source while it still
// mirrors it, typed or browsed, until the user chooses another. Blank means each
// result goes beside its source.
//
// USE CONFIGURATION: when it is checked at OK, every field is saved in
// %LOCALAPPDATA%\_APP_\configs\_APP_.inix and loaded next time; when it is not,
// that file is removed and the app starts from its defaults. Default settings
// restores the defaults and removes it too.
//
// THE RESULTS BOX says what this run actually did. A count says "1 file", never
// "1 files", and "0 files" is a real answer.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Windows.Forms;
using Homer;

namespace _APP_
{

public static class Program
{
    private const string sAppName = "_APP_";
    // CHANGE ME: the GitHub account that publishes this app's releases, for Elevate's update check.
    private const string sGitHubOwner = "JamalMazrui";
    private const string sSection = "Settings";
    private const string sSettingsFile = "_APP_.inix";

    private static bool bForce = false;
    private static bool bUseConfig = false;
    private static bool bViewOutput = false;
    private static string sOutput = "";
    private static string sSource = "";

    [DllImport("kernel32.dll")]
    private static extern bool AttachConsole(int iProcessId);

    [STAThread]
    public static int Main(string[] aArguments)
    {
        // FIRST, THE KIT'S SERVICES: the session log, the app's own folders, and
        // Elevate, which lets Help and F11 offer an update from GitHub.
        Log.start(sAppName);
        Paths.start(sAppName);
        Elevate.configure(sGitHubOwner, sAppName, BuildVersion.Version);
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        if (aArguments != null && aArguments.Length > 0)
        {
            // Print to the console the program was started from, unless its output is
            // already going somewhere, as when a script or the kit's check reads it.
            if (!Console.IsOutputRedirected) AttachConsole(-1);
            return runFromCommandLine(aArguments);
        }
        loadConfiguration();
        return runFromDialog();
    }

    // ---- settings: Use configuration ----------------------------------------

    private static string settingsPath() { return Paths.configFile(sSettingsFile); }

    private static string defaultSource()
    {
        return LaunchDialog.knownFolderPath(Environment.SpecialFolder.MyDocuments);
    }

    // deriveOutput: the Output directory a source implies: one folder gives itself, one
    // pattern or one file gives its folder, anything else gives nothing.
    private static string deriveOutput(string sSourceField)
    {
        string sOne = (sSourceField ?? "").Trim().Trim('"');
        if (sOne == "" || sOne.Contains("\" \"")) return "";
        try
        {
            sOne = Environment.ExpandEnvironmentVariables(sOne);
            if (Directory.Exists(sOne)) return Path.GetFullPath(sOne);
            if (sOne.IndexOfAny(new char[] { '*', '?' }) >= 0)
            {
                string sDir = Path.GetDirectoryName(sOne);
                return !string.IsNullOrEmpty(sDir) && Directory.Exists(sDir) ? Path.GetFullPath(sDir) : "";
            }
            if (File.Exists(sOne)) return Path.GetDirectoryName(Path.GetFullPath(sOne)) ?? "";
        }
        catch (Exception) { }
        return "";
    }

    private static bool restoreDefaults()
    {
        sSource = defaultSource();
        sOutput = deriveOutput(sSource);
        bForce = false; bViewOutput = false; bUseConfig = false;
        return true;
    }

    private static bool loadConfiguration()
    {
        restoreDefaults();
        string sPath = settingsPath();
        if (!File.Exists(sPath) || InixCodec.readValue(sPath, sSection, "UseConfig", "0") != "1") return true;
        sSource = InixCodec.readValue(sPath, sSection, "Source", sSource);
        sOutput = InixCodec.readValue(sPath, sSection, "Output", sOutput);
        bForce = InixCodec.readValue(sPath, sSection, "Force", "0") == "1";
        bViewOutput = InixCodec.readValue(sPath, sSection, "ViewOutput", "0") == "1";
        bUseConfig = true;
        Log.info("Configuration loaded from " + sPath);
        return true;
    }

    private static bool saveConfiguration()
    {
        string sPath = settingsPath();
        try
        {
            if (!bUseConfig) { if (File.Exists(sPath)) { File.Delete(sPath); Log.info("Configuration removed: " + sPath); } return true; }
            InixCodec.writeValue(sPath, sSection, "UseConfig", "1");
            InixCodec.writeValue(sPath, sSection, "Source", sSource);
            InixCodec.writeValue(sPath, sSection, "Output", sOutput);
            InixCodec.writeValue(sPath, sSection, "Force", bForce ? "1" : "0");
            InixCodec.writeValue(sPath, sSection, "ViewOutput", bViewOutput ? "1" : "0");
            Log.info("Configuration saved in " + sPath);
        }
        catch (Exception oError) { Log.error("Configuration: " + oError.Message); }
        return true;
    }

    // ---- the dialog ---------------------------------------------------------

    private static int runFromDialog()
    {
        while (true)
        {
            string sButton;
            using (LaunchDialog oLaunch = new LaunchDialog(sAppName))
            {
                // CHANGE ME: "files" (the default), "folder" or "list", and a filter for files.
                oLaunch.sourcePick = "folder";
                TextBox tbSource = oLaunch.addSourceBand(sSource,
                    "One or more files, folders or wildcard patterns such as *.docx, separated by spaces, each in quotes if it has a space.",
                    "Choose a folder of files to work on. It opens where Source paths points, else in Documents.");

                // CHANGE ME: the app's own bands go here -- first the checkboxes choosing the
                // transformations, then any other controls shaping the work. For example:
                //     oLaunch.dialog.addBand();
                //     CheckBox cbPlain = oLaunch.dialog.addCheckBox("&Plain text", bPlain, "Write .txt instead of .htm.");
                //     oLaunch.dialog.endBand();

                TextBox tbOutput = oLaunch.addOutputBand(sOutput,
                    "Where each result is written. Blank means beside its source.",
                    "Choose the folder the results go to.");

                // The output follows the source while it still mirrors it, typed or browsed;
                // a folder the user chose stays put.
                string sMirror = deriveOutput(tbSource.Text);
                Action followSource = delegate()
                {
                    bool bMirrors = tbOutput.Text.Trim() == "" || string.Equals(tbOutput.Text.Trim(), sMirror, StringComparison.OrdinalIgnoreCase);
                    sMirror = deriveOutput(tbSource.Text);
                    if (bMirrors) tbOutput.Text = sMirror;
                };
                oLaunch.sourceChosen = followSource;
                tbSource.Leave += delegate(object oSender, EventArgs evArgs) { followSource(); };

                oLaunch.addOperationBands(bForce, "Replace a result already there instead of keeping it.",
                    bUseConfig, "Load these settings next time, and save them when you press OK, in %LOCALAPPDATA%\\" + sAppName + "\\configs\\" + sSettingsFile + ".",
                    bViewOutput, "Open the output directory in File Explorer when the run is done.");

                sButton = oLaunch.run();

                // Harvest every field before the dialog is disposed, so a return keeps what was typed.
                sSource = (tbSource.Text ?? "").Trim();
                sOutput = (tbOutput.Text ?? "").Trim();
                bForce = oLaunch.forceBox.Checked;
                bViewOutput = oLaunch.viewOutputBox.Checked;
                bUseConfig = oLaunch.useConfigBox.Checked;
            }
            if (sButton == "Cancel") return 0;
            if (sButton == "Default settings")
            {
                restoreDefaults();
                try { if (File.Exists(settingsPath())) File.Delete(settingsPath()); } catch (Exception) { }
                Log.info("Default settings restored");
                continue;
            }
            if (!confirmOutput(sOutput)) continue;
            saveConfiguration();
            break;
        }
        List<string> lsReport = new List<string>();
        int iResult = runJob(lsReport);
        string sOpen = sOutput.Trim('"');
        LaunchDialog.finish(sAppName, string.Join("\r\n", lsReport.ToArray()), iResult == 3, bViewOutput ? sOpen : "");
        return iResult;
    }

    // confirmOutput: offer to make an output directory that does not exist yet, Yes by default.
    private static bool confirmOutput(string sFolder)
    {
        string sCandidate = (sFolder ?? "").Trim().Trim('"');
        if (sCandidate == "" || Directory.Exists(sCandidate)) return true;
        if (MessageBox.Show("Create " + sCandidate + "?", sAppName, MessageBoxButtons.YesNo, MessageBoxIcon.Question,
            MessageBoxDefaultButton.Button1) != DialogResult.Yes) return false;
        try { Directory.CreateDirectory(sCandidate); return true; }
        catch (Exception oError)
        {
            MessageBox.Show("Could not create the folder:\r\n" + sCandidate + "\r\n\r\n" + oError.Message, sAppName,
                MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return false;
        }
    }

    // ---- the command line ---------------------------------------------------

    private static int runFromCommandLine(string[] aArguments)
    {
        // USE CONFIGURATION FIRST, wherever it is written, so the switches after it can
        // still change any setting it loads.
        foreach (string sArgument in aArguments)
        {
            string sSwitch = Util.switchName(sArgument);
            if (sSwitch == "use-configuration" || sSwitch == "u") { loadConfiguration(); break; }
        }
        for (int i = 0; i < aArguments.Length; i++)
        {
            string sArgument = aArguments[i];
            // ONE SWITCH CONVENTION (homer-code): /switch, -switch and --switch alike, in any case.
            string sSwitch = Util.switchName(sArgument);
            string sNext = (i + 1 < aArguments.Length) ? aArguments[i + 1] : "";
            if (sSwitch == "help" || sSwitch == "h" || sArgument == "/?") { Console.WriteLine(helpText()); return 0; }
            else if (sSwitch == "source-paths" || sSwitch == "source" || sSwitch == "s") { sSource = (sSource + " " + sNext).Trim(); i++; }
            else if (sSwitch == "output-directory" || sSwitch == "output" || sSwitch == "o") { sOutput = sNext; i++; }
            else if (sSwitch == "force-replacements" || sSwitch == "force" || sSwitch == "f") bForce = true;
            else if (sSwitch == "use-configuration" || sSwitch == "u") { }
            else if (sSwitch == "view-output-directory" || sSwitch == "view-output" || sSwitch == "view" || sSwitch == "v") bViewOutput = true;
            else if (sSwitch == "default-settings" || sSwitch == "defaults" || sSwitch == "d")
            {
                try { if (File.Exists(settingsPath())) File.Delete(settingsPath()); } catch (Exception) { }
                Console.WriteLine("Default settings restored.");
                return 0;
            }
            else if (sSwitch != "")
            {
                Console.WriteLine("Unknown switch " + sArgument + ". Run with /help to see the switches.");
                Log.error("Unknown switch: " + sArgument);
                return 1;
            }
            else sSource = (sSource + " " + (sArgument.Contains(" ") ? "\"" + sArgument + "\"" : sArgument)).Trim();
        }
        List<string> lsReport = new List<string>();
        int iResult = runJob(lsReport);
        foreach (string sLine in lsReport) Console.WriteLine(sLine);
        string sOpen = sOutput.Trim('"');
        if (bViewOutput && sOpen != "" && Directory.Exists(sOpen))
        {
            try { Process.Start("explorer.exe", "\"" + sOpen + "\""); } catch (Exception oError) { Log.error("View output directory: " + oError.Message); }
        }
        return iResult;
    }

    // ---- the work -----------------------------------------------------------
    //
    // AI NOTE: this is the one method to replace. Everything above and below it is
    // the shape every launch app shares. Add to lsReport only what was actually
    // done this run, one short line each, the summary first; return 0 on success,
    // 1 when there was nothing to do, 3 when some of the work failed.
    private static int runJob(List<string> lsReport)
    {
        string sOne = sSource.Trim().Trim('"');
        if (sOne == "") { lsReport.Add("No source was given, so there was nothing to do."); return 1; }
        if (!File.Exists(sOne) && !Directory.Exists(sOne) && sOne.IndexOfAny(new char[] { '*', '?', '"' }) < 0)
        {
            lsReport.Add("There is nothing at " + sOne + ".");
            return 1;
        }
        lsReport.Add("0 files written. The work itself is not written yet.");
        lsReport.Add("Source paths: " + sSource);
        lsReport.Add("Output directory: " + (sOutput == "" ? "beside each source" : sOutput));
        lsReport.Add("The log: " + Log.path);
        return 0;
    }

    private static string helpText()
    {
        StringBuilder sbText = new StringBuilder();
        sbText.AppendLine(sAppName + " " + BuildVersion.Version + " -- one dialog, one job, one result.");
        sbText.AppendLine("");
        sbText.AppendLine("  " + sAppName.ToLowerInvariant() + "                               the dialog");
        sbText.AppendLine("  " + sAppName.ToLowerInvariant() + " <paths> [-o <folder>] [-f] [-u] [-v]");
        sbText.AppendLine("  " + sAppName.ToLowerInvariant() + " -d                            settings back to their defaults");
        sbText.AppendLine("  " + sAppName.ToLowerInvariant() + " -h");
        sbText.AppendLine("");
        sbText.AppendLine("  <paths>                         files, folders or patterns (or -s <path>)");
        sbText.AppendLine("  -o, --output-directory <folder> where results go; without it, beside each source");
        sbText.AppendLine("  -f, --force-replacements        replace results that are already there");
        sbText.AppendLine("  -u, --use-configuration         start from the settings the dialog saved");
        sbText.AppendLine("  -v, --view-output-directory     open the output directory when done");
        sbText.AppendLine("  -d, --default-settings          forget the saved settings");
        sbText.AppendLine("  -h, --help                      this list");
        sbText.AppendLine("");
        sbText.AppendLine("Switches may be written /switch, -switch or --switch, in any case. Logging is");
        sbText.AppendLine("automatic: each run writes %LOCALAPPDATA%\\" + sAppName + "\\logs\\" + sAppName + "-yyyyMMdd-HHmmss.log.");
        return sbText.ToString();
    }
}

} // namespace _APP_
