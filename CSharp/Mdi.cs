// Mdi.cs -- part of the shared Homer toolkit (namespace Homer).
//
// REQUIRES: KeyMap.cs, Lbc.cs, Log.cs, Paths.cs, Say.cs, Util.cs.
//
// KeyMap is the one that is easy to miss, because a build script can compile
// this file without it and fail with nine copies of "The name 'KeyMap' does not
// exist in the current context". Every command registers itself with KeyMap as
// it is added, which is what keeps the menu, the alternate menu, the key
// describer and the hotkey document in agreement. The two are switched on
// together in the build template for that reason.
//
// THE THIRD KIND OF HOMER APP: a multiple-document program, where each thing
// being worked on has its own window inside one frame. EdSharp, FileDir and
// DbDo are all this shape, and each grew its own version of the same frame
// code. This is that code, once.
//
// THE DESIGN IS NOT NEW. It comes from the Homer.NET MDI fruit basket of 2010 --
// LbcMdiApp, LbcMdiFrame, LbcMdiChild, with a menu built by name and key, focus
// tips per control, a window picker, a command list, and a key describer. That
// program was right about the shape twenty years before this file existed. What
// is new is that the three current apps can share one implementation instead of
// three that drift.
//
// WHY MDI AT ALL, when the rest of the world moved to tabs. Because a window is
// a first-class object to a screen reader and a tab is not. Alt+Tab reaches it,
// the window list reaches it, the title announces it on activation, and each
// window keeps its own state -- its own file, filter, position and focus. A
// tabbed interface has to reimplement every one of those, usually badly.
//
// WHAT THE FRAME GIVES YOU, and no app should write again:
//
//     F4                    current windows, as a pick list
//     Shift+F4              say how many windows are open, and their titles
//     Control+Tab           next window
//     Control+Shift+Tab     previous window
//     Control+F4            close this window
//     Control+Shift+F4      close all but this one
//     Alt+F10               alternate menu: every command in one filterable list
//     Alt+Shift+C           change a setting, from a list of what is settable
//     Alt+Shift+S           run a script, from a list of what is in the scripts folder
//     Control+F1            key describer: a key says what it would do
//     Alt+F1                about
//     F1                    documentation
//
// THE TITLE RULE, which cost DbDo a bug before it was written down. The FRAME
// carries the app name and nothing else. A CHILD carries what it is showing and
// nothing else. Windows merges a maximized child into the frame caption, so
// JAWS+T reads "DbDo - [contacts.db - contacts]". A child that repeated the app
// name made the reader say it twice.
//
// Usage, which is the whole of an MDI app's plumbing:
//
//     using Homer;
//
//     public class fruitFrame : MdiFrame
//     {
//         public fruitFrame() : base("FruitBasketMdi")
//         {
//             addMenu("&File");
//             addItem("&New basket", Keys.Control | Keys.N, "Open another basket.");
//             addMenu("&Window");           // the frame fills this one in
//             addMenu("&Help");             // and this one
//             finishMenus();
//         }
//         protected override bool onCommand(string sCommand) { ... }
//     }
//
// Nothing here throws where it can help it: a menu that cannot be built, a
// window that cannot be closed, or a title that cannot be set is logged and
// stepped over, because an MDI frame that dies takes every open document with
// it.

using System;
using System.Collections.Generic;
using System.Windows.Forms;

namespace Homer {

// ------- the frame -------

public class MdiFrame : LbcForm
{
    private Dictionary<string, ToolStripMenuItem> dMenus =
        new Dictionary<string, ToolStripMenuItem>(StringComparer.OrdinalIgnoreCase);
    private Dictionary<string, string> dSettable =
        new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
    private Dictionary<string, string> dSettableSummary =
        new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
    private MenuStrip menuBar;
    private ToolStripMenuItem menuNow;
    private string sAppName = "";

    public MdiFrame(string sAppNameGiven)
    {
        sAppName = (sAppNameGiven ?? "").Trim();
        if (sAppName == "") sAppName = "Homer";

        // THE FRAME CARRIES THE APP NAME AND NOTHING ELSE. A child adds what it
        // is showing, and Windows merges the two for a maximized child.
        this.Text = sAppName;
        this.IsMdiContainer = true;
        this.StartPosition = FormStartPosition.CenterScreen;
        this.WindowState = FormWindowState.Maximized;

        menuBar = new MenuStrip();
        menuBar.AccessibleName = "Main menu";
        menuBar.Dock = DockStyle.Top;
        menuBar.AllowMerge = true;
        this.MainMenuStrip = menuBar;
        this.Controls.Add(menuBar);

        Say.attach(this);

        // When the last child closes there is no menu bar left, so an empty
        // frame is a dead end for a keyboard user. Close it instead.
        this.MdiChildActivate += delegate(object oSender, EventArgs evArgs)
        {
            if (this.MdiChildren.Length == 0 && this.Visible) this.Close();
        };
    }

    public string appName { get { return sAppName; } }

    // ------- building the menus -------

    // addMenu: start a top-level menu. Name it with an ampersand, as every
    // Homer label is; the plain Windows API does the rest.
    public ToolStripMenuItem addMenu(string sTitle)
    {
        menuNow = new ToolStripMenuItem(sTitle);
        menuBar.Items.Add(menuNow);
        dMenus[sTitle.Replace("&", "")] = menuNow;
        return menuNow;
    }

    // addItem: one command on the current menu, with its key and its tip.
    //
    // The command NAME is what onCommand receives, so an app dispatches on a
    // sentence a person would say rather than on a control id. The key and the
    // summary go to KeyMap, which is what makes the alternate menu, the key
    // describer and the hotkey document agree without being told twice.
    public ToolStripMenuItem addItem(string sCommand, Keys keyData, string sSummary)
    {
        ToolStripMenuItem item = new ToolStripMenuItem(sCommand);
        if (keyData != Keys.None) item.ShortcutKeys = keyData;
        item.ToolTipText = sSummary;
        string sPlain = sCommand.Replace("&", "");
        item.Click += delegate(object oSender, EventArgs evArgs) { runCommand(sPlain); };
        if (menuNow != null) menuNow.DropDownItems.Add(item);
        try
        {
            KeyMap.register(sPlain, keyData, item, sAppName);
            KeyMap.setSummary(sPlain, sSummary);
        }
        catch (Exception oError)
        {
            Log.exception(oError);
        }
        return item;
    }

    public bool addSeparator()
    {
        if (menuNow != null) menuNow.DropDownItems.Add(new ToolStripSeparator());
        return true;
    }

    // finishMenus: fill in the Window and Help menus the frame owns, and log
    // any key claimed twice. Call it once, after the app's own menus.
    public bool finishMenus()
    {
        if (!dMenus.ContainsKey("Window")) addMenu("&Window");
        menuNow = dMenus["Window"];
        addItem("Current Windows", Keys.F4, "Pick an open window from a list.");
        addItem("Say Windows Open", Keys.Shift | Keys.F4, "Say how many windows are open, and their titles.");
        addItem("Next Window", Keys.Control | Keys.Tab, "Go to the next window.");
        addItem("Previous Window", Keys.Control | Keys.Shift | Keys.Tab, "Go to the previous window.");
        addItem("Close Window", Keys.Control | Keys.F4, "Close this window.");
        addItem("Close All But Current Window", Keys.Control | Keys.Shift | Keys.F4, "Close every window but this one.");

        if (!dMenus.ContainsKey("Help")) addMenu("&Help");
        menuNow = dMenus["Help"];
        addItem("Documentation", Keys.F1, "Open the guide.");
        addItem("Run a Script", Keys.Alt | Keys.Shift | Keys.S,
                "Pick a script from the scripts folder and run it.");
        addItem("Change a Setting", Keys.Alt | Keys.Shift | Keys.C,
                "Change a setting and have it take effect now.");
        addItem("Alternate Menu", Keys.Alt | Keys.F10, "Every command in one list you can filter.");
        addItem("Key Help Toggle", Keys.Control | Keys.F1, "A key says what it would do instead of doing it.");
        addItem("About", Keys.Alt | Keys.F1, "The name, the version, and where this copy came from.");

        foreach (string sConflict in KeyMap.lsConflicts) Log.warn("Key claimed twice: " + sConflict);
        return true;
    }

    // ------- running a command -------

    // runCommand: the one way in. Key Help turns every command into a
    // description of itself, which is how a person explores a program safely.
    public bool runCommand(string sCommand)
    {
        Log.info("Command: " + sCommand);
        if (KeyMap.bKeyDescriber)
        {
            Say.sayForced(sCommand + ". " + KeyMap.getSummary(sCommand));
            return true;
        }
        try
        {
            if (onCommand(sCommand)) return true;
            return runFrameCommand(sCommand);
        }
        catch (Exception oError)
        {
            Log.exception(oError);
            Say.sayForced(sCommand + " failed. The log has why.");
            return false;
        }
    }

    // onCommand: the app's own commands. Answer true when you handled one.
    protected virtual bool onCommand(string sCommand)
    {
        return false;
    }

    // The commands the frame owns, tried after the app has had its turn.
    private bool runFrameCommand(string sCommand)
    {
        switch (sCommand)
        {
            case "About": return showAbout();
            case "Alternate Menu": return showAlternateMenu();
            case "Close All But Current Window": return closeOthers();
            case "Close Window": return closeCurrent();
            case "Current Windows": return pickWindow();
            case "Change a Setting": return changeSetting();
            case "Documentation": return showDocumentation();
            case "Run a Script": return runScript();
            case "Key Help Toggle":
                KeyMap.bKeyDescriber = !KeyMap.bKeyDescriber;
                Say.sayForced(KeyMap.bKeyDescriber ? "Key help on" : "Key help off");
                return true;
            case "Next Window": return stepWindow(1);
            case "Previous Window": return stepWindow(-1);
            case "Say Windows Open": return sayWindows();
            default: return false;
        }
    }

    // ------- the window commands -------

    public List<string> windowTitles()
    {
        List<string> lsTitles = new List<string>();
        foreach (Form frm in this.MdiChildren) lsTitles.Add(frm.Text);
        return lsTitles;
    }

    public bool sayWindows()
    {
        List<string> lsTitles = windowTitles();
        // The noun matches the count, and zero is a real answer.
        string sCount = lsTitles.Count == 1 ? "1 window open" : lsTitles.Count + " windows open";
        Say.sayForced(sCount + (lsTitles.Count > 0 ? ": " + string.Join(", ", lsTitles.ToArray()) : ""));
        return true;
    }

    public bool pickWindow()
    {
        List<string> lsTitles = windowTitles();
        if (lsTitles.Count == 0) { Say.sayForced("0 windows open"); return true; }
        using (LbcDialog dlg = new LbcDialog("Current Windows", this))
        {
            ListBox lb = dlg.addPickBox("&Window:", lsTitles,
                this.ActiveMdiChild == null ? "" : this.ActiveMdiChild.Text,
                "Choose the window to go to.");
            if (!dlg.runOkCancel()) return true;
            int iPick = lb.SelectedIndex;
            if (iPick >= 0 && iPick < this.MdiChildren.Length) this.MdiChildren[iPick].Activate();
        }
        return true;
    }

    public bool stepWindow(int iDirection)
    {
        Form[] afrmChildren = this.MdiChildren;
        if (afrmChildren.Length < 2) { Say.sayForced("1 window open"); return true; }
        int iNow = Array.IndexOf(afrmChildren, this.ActiveMdiChild);
        int iNext = (iNow + iDirection + afrmChildren.Length) % afrmChildren.Length;
        afrmChildren[iNext].Activate();
        return true;
    }

    public bool closeCurrent()
    {
        if (this.ActiveMdiChild != null) this.ActiveMdiChild.Close();
        return true;
    }

    public bool closeOthers()
    {
        Form frmKeep = this.ActiveMdiChild;
        int iClosed = 0;
        foreach (Form frm in this.MdiChildren)
        {
            if (frm == frmKeep) continue;
            frm.Close();
            iClosed++;
        }
        Say.sayForced(iClosed == 1 ? "1 window closed" : iClosed + " windows closed");
        return true;
    }

    // ------- jobs -------

    // scriptFiles: every job, the user's first and the shipped ones after.
    //
    // A script is a script the user can run: .cmd, .ps1, .py, .js, .vbs. The
    // user's own live in the per-user tree so they survive an update; the
    // shipped ones come with the program and are read-only.
    public List<string> scriptFiles()
    {
        List<string> lsFound = new List<string>();
        List<string> lsSeen = new List<string>();
        foreach (string sFolder in new string[] { Paths.scripts(), Paths.shippedScripts() })
        {
            try
            {
                foreach (string sPath in System.IO.Directory.GetFiles(sFolder))
                {
                    string sName = System.IO.Path.GetFileName(sPath);
                    if (lsSeen.Contains(sName.ToLower())) continue;
                    lsSeen.Add(sName.ToLower());
                    lsFound.Add(sPath);
                }
            }
            catch (Exception)
            {
            }
        }
        lsFound.Sort(StringComparer.OrdinalIgnoreCase);
        return lsFound;
    }

    // runScript: pick a job from a list and run it.
    //
    // A LIST, not a folder browser and not a command line. The list is the whole
    // design: every job this program can run, in one place, reachable by first
    // letter, with no path to type and nothing to remember.
    public bool runScript()
    {
        List<string> lsScripts = scriptFiles();
        if (lsScripts.Count == 0)
        {
            Say.sayForced("0 scripts. Put one in " + Paths.scripts());
            return true;
        }
        List<string> lsNames = new List<string>();
        foreach (string sPath in lsScripts) lsNames.Add(System.IO.Path.GetFileName(sPath));
        using (LbcDialog dlg = new LbcDialog("Run a Script", this))
        {
            ListBox lb = dlg.addPickBox("&Script:", lsNames, "",
                "Type a letter or two to narrow the list, then press Enter to run it.");
            if (!dlg.runOkCancel()) return true;
            int iPick = lb.SelectedIndex;
            if (iPick < 0) return true;
            string sScript = lsScripts[iPick];
            Log.info("Running job: " + sScript);
            try
            {
                System.Diagnostics.ProcessStartInfo oStart =
                    new System.Diagnostics.ProcessStartInfo(sScript);
                oStart.UseShellExecute = true;
                oStart.WorkingDirectory = Paths.results();
                System.Diagnostics.Process.Start(oStart);
                Say.sayForced(lsNames[iPick] + " started");
            }
            catch (Exception oError)
            {
                Log.exception(oError);
                Say.sayForced("That job could not be started. The log has why.");
            }
        }
        return true;
    }

    // ------- settings -------

    // addSetting: declare a setting the user may change while the program runs.
    //
    // The app names what is settable; the frame does the rest -- the list, the
    // reading, the writing, and the call back into the app. A setting nobody
    // declared cannot be changed by accident, and one that is declared needs no
    // dialog of its own.
    public bool addSetting(string sName, string sDefault, string sSummary)
    {
        dSettable[sName] = sDefault;
        dSettableSummary[sName] = sSummary;
        return true;
    }

    public string settingsFile()
    {
        return Paths.configFile(sAppName + ".inix");
    }

    public string settingValue(string sName)
    {
        string sDefault = dSettable.ContainsKey(sName) ? dSettable[sName] : "";
        return InixCodec.readValue(settingsFile(), "Settings", sName, sDefault);
    }

    // changeSetting: change a setting from a list, and have it take effect now.
    //
    // A LIST OF WHAT IS SETTABLE, not a text file to edit and not a dialog of
    // twenty controls. Pick the setting, type the value, and the program acts on
    // it immediately -- no restart, no hunting for the file, no chance of
    // breaking the syntax.
    public bool changeSetting()
    {
        List<string> lsNames = new List<string>(dSettable.Keys);
        lsNames.Sort(StringComparer.OrdinalIgnoreCase);
        if (lsNames.Count == 0)
        {
            Say.sayForced("0 settings can be changed here");
            return true;
        }
        string sName = "";
        using (LbcDialog dlg = new LbcDialog("Change a Setting", this))
        {
            ListBox lb = dlg.addPickBox("&Setting:", lsNames, "",
                "Pick the setting to change, then press Enter.");
            if (!dlg.runOkCancel()) return true;
            if (lb.SelectedIndex < 0) return true;
            sName = lsNames[lb.SelectedIndex];
        }
        string sNow = settingValue(sName);
        using (LbcDialog dlg = new LbcDialog("Change a Setting", this))
        {
            TextBox tb = dlg.addInputBox("&" + sName + ":", sNow,
                dSettableSummary.ContainsKey(sName) ? dSettableSummary[sName] : "");
            if (!dlg.runOkCancel()) return true;
            InixCodec.writeValue(settingsFile(), "Settings", sName, tb.Text);
            Log.info("Setting " + sName + " = " + tb.Text);
            onSettingChanged(sName, tb.Text);
            Say.sayForced(sName + " is now " + tb.Text);
        }
        return true;
    }

    // onSettingChanged: the app acts on the new value here. Nothing restarts.
    protected virtual bool onSettingChanged(string sName, string sValue)
    {
        return false;
    }

    // ------- help -------

    public bool showAlternateMenu()
    {
        List<string> lsCommands = KeyMap.commands();
        lsCommands.Sort(StringComparer.OrdinalIgnoreCase);
        if (lsCommands.Count == 0) { Say.sayForced("0 commands"); return true; }
        using (LbcDialog dlg = new LbcDialog("Alternate Menu", this))
        {
            ListBox lb = dlg.addPickBox("&Command:", lsCommands, "",
                "Type a letter or two to narrow the list, then press Enter.");
            if (!dlg.runOkCancel()) return true;
            if (lb.SelectedIndex >= 0) runCommand(lsCommands[lb.SelectedIndex]);
        }
        return true;
    }

    public bool showAbout()
    {
        System.Text.StringBuilder sbAbout = new System.Text.StringBuilder();
        sbAbout.AppendLine(sAppName);
        sbAbout.AppendLine("Version: " + versionText());
        sbAbout.AppendLine("Program: " + Paths.installedFolder);
        sbAbout.AppendLine("Settings and logs: " + Paths.userFolder);
        sbAbout.AppendLine("This session's log: " + Log.path);
        sbAbout.AppendLine("Speech: " + Say.speechDiagnostic());
        HelpDialog.show(this, "About " + sAppName, sbAbout.ToString());
        return true;
    }

    private string versionText()
    {
        try
        {
            Type oBuild = Type.GetType("BuildVersion");
            if (oBuild != null)
            {
                System.Reflection.FieldInfo oField = oBuild.GetField("Version");
                if (oField != null) return "" + oField.GetValue(null);
            }
        }
        catch (Exception)
        {
        }
        return "unknown";
    }

    public bool showDocumentation()
    {
        // The guide is in help; the ReadMe stays at the top of the folder.
        string sGuide = System.IO.Path.Combine(Paths.shippedHelp(), sAppName + ".htm");
        if (!System.IO.File.Exists(sGuide))
            sGuide = System.IO.Path.Combine(Paths.installedFolder, "ReadMe.htm");
        if (!System.IO.File.Exists(sGuide))
        {
            Say.sayForced("The guide was not found beside the program");
            return true;
        }
        try { System.Diagnostics.Process.Start(sGuide); } catch (Exception oError) { Log.exception(oError); }
        return true;
    }
}

// ------- the child -------

public class MdiChild : Form
{
    private string sSubject = "";
    private string sView = "";

    // THE CHILD IS BUILT BY THE SAME BUILDER AS A DIALOG.
    //
    // LbcDialog can adopt an existing form instead of making one, so everything
    // Lbc does for a dialog happens here too and nothing is written twice: add
    // order is focus order, an ampersand is the whole of an access key, the
    // status line at the foot carries each control's tip, a list arrives with
    // Control+J search and F3, and a field arrives with the line chords.
    //
    // Add controls through this, then call finishLayout.
    public LbcDialog lbc;

    public MdiChild(MdiFrame frmParent)
    {
        this.MdiParent = frmParent;
        this.WindowState = FormWindowState.Maximized;
        lbc = new LbcDialog("", frmParent, this);
    }

    // finishLayout: size to what was added and set the opening focus. The frame
    // shows the window; this never does.
    public bool finishLayout()
    {
        lbc.layoutIntoForm();
        return true;
    }

    // setTitle: what this window is showing.
    //
    // THE CHILD CARRIES NO APP NAME. The frame is already titled with it, and
    // Windows merges a maximized child's caption into the frame's, so repeating
    // it here makes a screen reader say it twice on JAWS+T.
    public bool setTitle(string sSubjectGiven, string sViewGiven)
    {
        sSubject = sSubjectGiven ?? "";
        sView = sViewGiven ?? "";
        this.Text = sView == "" ? sSubject : sSubject + " - " + sView;
        this.AccessibleName = this.Text;
        return true;
    }

    public string subject { get { return sSubject; } }
    public string view { get { return sView; } }

    public bool setStatusText(string sText)
    {
        lbc.setStatusText(sText ?? "");
        return true;
    }
}

} // namespace Homer (Mdi.cs)
