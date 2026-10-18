// Mdi.cs -- the Homer multiple-window frame, shared by every Homer MDI app.
//
// REQUIRES: KeyMap.cs, KeyName.cs, Elevate.cs, Inix.cs, Lbc.cs, Log.cs,
// Paths.cs, Say.cs, Util.cs. The build template compiles them together.
//
// THE SHAPE. One frame holds the menu bar and the app's name. Each thing being
// worked on -- a database table, a document, a folder, a basket of fruit --
// has a window of its own inside the frame. A window is a first-class object
// to a screen reader: the window list reaches it, its title is announced when
// it activates, and it keeps its own state. DbDo, EdSharp and FileDir are this
// shape, and so is any app made with newHomerApp --mdi.
//
// WHAT THE FRAME GIVES EVERY APP, so no app writes it again:
//
//   Window   F4 Current Windows, Shift+F4 Say Windows Open, Control+Tab and
//            Control+Shift+Tab Next and Previous Window, Control+F4 Close
//            Window, Control+Shift+F4 Close All But Current Window
//   Query    Alt+Apostrophe Say Clipboard, Alt+SemiColon Say Time
//   Misc     Alt+Shift+E Edit Settings, Control+Shift+I Invoke Script
//   Help     F1 Documentation, Shift+F1 History of Changes, Alt+F1 About,
//            Control+F1 Key Describer Toggle, Control+Shift+F1 Hotkeys,
//            Alt+Shift+F1 ReadMe, Alt+F10 Alternate Menu, Alt+Shift+H Hotkey
//            Summary, F11 Elevate Version, Control+F12 Copy Log, and Play
//            Tutorials in the Homer Player
//
// Every key goes through KeyMap.route, so a key that types in a text box
// types, a list keeps first-letter navigation, and a command that cannot run
// says why. The rules are in KeyMap.cs and the guide is help\MdiFramework.md.
//
// THE TITLE RULE. The FRAME carries the app name and nothing else. A CHILD
// carries what it is showing and nothing else. Windows merges a maximized
// child into the frame caption, so JAWS+T reads "DbDo - [contacts.db]"; a
// child that repeated the app name made the reader say it twice.
//
// THE LEVELS OF NEXT AND PREVIOUS (the suite contract, help\HomerSuite.md):
// Control+Tab moves between windows; Control+F6 between the things inside a
// window in a fixed order; Alt+F6 between them in the order last visited;
// F6 between the views or parts of the current thing. The frame owns the
// first; an app adds the others when it has such things.
//
// COMPATIBILITY. addItem(name, Keys, summary) and onCommand(name) still work,
// so an app written for the earlier frame compiles unchanged.
//
// Nothing here throws where it can help it: a frame that dies takes every
// open window with it, so failures are logged and stepped over.

using System;
using System.Collections.Generic;
using System.Collections.Specialized;
using System.Windows.Forms;

namespace Homer {

// ------- window services, usable by any frame -------

// MdiWindows: the window commands, for a frame of any kind -- this kit's
// MdiFrame, or an older app frame that has not moved to it yet.
public static class MdiWindows {

    public static List<string> titles(Form frmFrame) {
        List<string> lsTitles = new List<string>();
        if (frmFrame == null) return lsTitles;
        foreach (Form frm in frmFrame.MdiChildren) lsTitles.Add(frm.Text);
        return lsTitles;
    }

    public static string countText(int iCount) {
        return iCount == 1 ? "1 window open" : iCount.ToString() + " windows open";
    }

    // sayOpen: Shift+F4. The count, then the titles, as separate utterances.
    public static bool sayOpen(Form frmFrame) {
        List<string> lsTitles = titles(frmFrame);
        List<string> lsParts = new List<string>();
        lsParts.Add(countText(lsTitles.Count));
        lsParts.AddRange(lsTitles);
        return KeyMap.answer("Windows Open", lsParts.ToArray());
    }

    // pick: F4. A list of the open windows; Enter goes to the one chosen.
    public static bool pick(Form frmFrame) {
        Form[] afrmChildren = frmFrame.MdiChildren;
        if (afrmChildren.Length == 0) { Say.sayForced(countText(0)); return true; }
        List<string> lsTitles = titles(frmFrame);
        using (LbcDialog dlg = new LbcDialog("Current Windows", frmFrame)) {
            ListBox lb = dlg.addPickBox("&Window:", lsTitles,
                frmFrame.ActiveMdiChild == null ? "" : frmFrame.ActiveMdiChild.Text,
                "Type the start of a title, then press Enter to go to that window.");
            if (!dlg.runOkCancel()) return true;
            int iPick = lb.SelectedIndex;
            if (iPick >= 0 && iPick < afrmChildren.Length && !afrmChildren[iPick].IsDisposed) afrmChildren[iPick].Activate();
        }
        return true;
    }

    // step: Control+Tab and Control+Shift+Tab, in a fixed order.
    public static bool step(Form frmFrame, int iDirection) {
        Form[] afrmChildren = frmFrame.MdiChildren;
        if (afrmChildren.Length < 2) { Say.sayForced(countText(afrmChildren.Length)); return true; }
        int iNow = Array.IndexOf(afrmChildren, frmFrame.ActiveMdiChild);
        if (iNow < 0) iNow = 0;
        int iNext = (iNow + iDirection + afrmChildren.Length) % afrmChildren.Length;
        afrmChildren[iNext].Activate();
        return true;
    }

    // closeCurrent: Control+F4. A window that refuses (unsaved work the
    // person chose to keep) stays open; its own question said why.
    public static bool closeCurrent(Form frmFrame) {
        if (frmFrame.ActiveMdiChild == null) { Say.sayForced(countText(0)); return true; }
        frmFrame.ActiveMdiChild.Close();
        return true;
    }

    // closeOthers: Control+Shift+F4. Counts only the windows that really closed.
    public static bool closeOthers(Form frmFrame) {
        Form frmKeep = frmFrame.ActiveMdiChild;
        int iClosed = 0, iKept = 0;
        foreach (Form frm in frmFrame.MdiChildren) {
            if (frm == frmKeep) continue;
            frm.Close();
            if (frm.IsDisposed || !frm.Visible) iClosed++;
            else iKept++;
        }
        string sClosed = iClosed == 1 ? "1 window closed" : iClosed.ToString() + " windows closed";
        if (iKept > 0) Say.sayForced(sClosed + ", " + (iKept == 1 ? "1 kept open" : iKept.ToString() + " kept open"));
        else Say.sayForced(sClosed);
        return true;
    }
}

// ------- the frame -------

public class MdiFrame : LbcForm {
    private Dictionary<string, ToolStripMenuItem> dMenus =
        new Dictionary<string, ToolStripMenuItem>(StringComparer.OrdinalIgnoreCase);
    private Dictionary<string, string> dSettable =
        new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
    private Dictionary<string, string> dSettableSummary =
        new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
    private MenuStrip menuBar;
    private ToolStripMenuItem menuNow;
    private string sAppName = "";

    // bCloseWithLastWindow: when the last window closes there is no work left
    // and no menu worth having, so by default the frame closes too.
    public bool bCloseWithLastWindow = true;

    public MdiFrame(string sAppNameGiven) {
        sAppName = (sAppNameGiven == null ? "" : sAppNameGiven).Trim();
        if (sAppName == "") sAppName = "Homer";
        this.Text = sAppName;
        this.IsMdiContainer = true;
        this.StartPosition = FormStartPosition.CenterScreen;
        this.WindowState = FormWindowState.Maximized;

        menuBar = new MenuStrip();
        menuBar.Dock = DockStyle.Top;
        this.MainMenuStrip = menuBar;
        this.Controls.Add(menuBar);

        Say.attach(this);

        this.MdiChildActivate += delegate(object oSender, EventArgs evArgs) {
            if (bCloseWithLastWindow && this.MdiChildren.Length == 0 && this.Visible) this.Close();
        };
    }

    public string appName { get { return sAppName; } }

    // ProcessCmdKey: every key through the one router, first.
    protected override bool ProcessCmdKey(ref Message msg, Keys keyData) {
        if (KeyMap.route(this, ref msg, keyData)) return true;
        return base.ProcessCmdKey(ref msg, keyData);
    }

    // ------- building the menus -------

    // addMenu: start a top-level menu, named with its ampersand.
    public ToolStripMenuItem addMenu(string sTitle) {
        string sPlain = sTitle.Replace("&", "");
        ToolStripMenuItem menu;
        if (dMenus.TryGetValue(sPlain, out menu)) { menuNow = menu; return menu; }
        menuNow = new ToolStripMenuItem(sTitle);
        menuBar.Items.Add(menuNow);
        dMenus[sPlain] = menuNow;
        return menuNow;
    }

    // addCommand: one command on the current menu. The caption carries the
    // ampersand; sKeys is in Homer spelling ("Control+Shift+A", "Shift+R or
    // F2", "" for none); fRun does the work. Set the returned command's
    // fUnavailable, fChecked or sRepeat to say more.
    public KeyMap.Command addCommand(string sCaption, string sKeys, string sSummary, Func<bool> fRun) {
        return addCommand(sCaption, sKeys, KeyMap.sAnywhere, sSummary, fRun);
    }

    public KeyMap.Command addCommand(string sCaption, string sKeys, string sContext, string sSummary, Func<bool> fRun) {
        KeyMap.Command oCommand = KeyMap.addCommand(sCaption, sKeys, sContext, sSummary, fRun);
        if (oCommand == null) return null;
        LbcMenuItem item = new LbcMenuItem(sCaption);
        item.ToolTipText = sSummary;
        if (oCommand.lsKeys.Count > 0) item.ShortcutKeyDisplayString = oCommand.keysText();
        item.Click += delegate(object oSender, EventArgs evArgs) { KeyMap.runCommand(oCommand); };
        oCommand.oItem = item;
        oCommand.sMenu = menuNow == null ? "" : menuNow.Text.Replace("&", "");
        if (menuNow != null) {
            menuNow.DropDownItems.Add(item);
            // The state of a mode is shown, and a refusal is announced when
            // the command is chosen, never only greyed out.
            menuNow.DropDownOpening += delegate(object oSender, EventArgs evArgs) {
                if (oCommand.fChecked != null) {
                    try { item.Checked = oCommand.fChecked(); } catch (Exception) { }
                }
            };
        }
        return oCommand;
    }

    // addItem: the earlier form, kept so older apps compile. The command name
    // goes to onCommand.
    public ToolStripMenuItem addItem(string sCommand, Keys keyData, string sSummary) {
        string sPlain = KeyMap.plainName(sCommand);
        KeyMap.Command oCommand = addCommand(sCommand,
            keyData == Keys.None ? "" : KeyMap.friendlyKey(keyData), sSummary,
            delegate() { return runCommand(sPlain); });
        return oCommand == null ? null : oCommand.oItem;
    }

    public bool addSeparator() {
        if (menuNow != null) menuNow.DropDownItems.Add(new ToolStripSeparator());
        return true;
    }

    // finishMenus: add the frame's own commands, after the app's. Call once.
    public bool finishMenus() {
        addMenu("&Query");
        addCommand("Say &Clipboard", "Alt+Apostrophe", "Say the text on the clipboard.", sayClipboard).sRepeat = "review";
        addCommand("Say &Time", "Alt+SemiColon", "Say the time and date.", sayTime).sRepeat = "review";

        addMenu("&Misc");
        addCommand("&Edit Settings...", "Alt+Shift+E", "Change a setting and have it take effect now.", changeSetting);
        addCommand("&Invoke Script...", "Control+Shift+I", "Pick a script from the scripts folder and run it.", runScript);

        addMenu("&Window");
        addCommand("&Current Windows...", "F4", "Pick an open window from a list.", delegate() { return MdiWindows.pick(this); });
        addCommand("&Say Windows Open", "Shift+F4", "Say how many windows are open, and their titles.", delegate() { return MdiWindows.sayOpen(this); }).sRepeat = "review";
        addCommand("&Next Window", "Control+Tab", "Go to the next window.", delegate() { return MdiWindows.step(this, 1); });
        addCommand("&Previous Window", "Control+Shift+Tab", "Go to the previous window.", delegate() { return MdiWindows.step(this, -1); });
        addCommand("C&lose Window", "Control+F4", "Close this window.", delegate() { return MdiWindows.closeCurrent(this); });
        addCommand("Close &All But Current Window", "Control+Shift+F4", "Close every window but this one.", delegate() { return MdiWindows.closeOthers(this); });

        addMenu("&Help");
        addCommand("&Documentation", "F1", "Open the guide.", delegate() { return openHelp(sAppName + ".htm"); });
        addCommand("&History of Changes", "Shift+F1", "Open the list of changes, newest first.", delegate() { return openHelp("History.htm"); });
        addCommand("&About", "Alt+F1", "The name, the version, and where this copy keeps its files.", showAbout);
        KeyMap.Command oDescriber = addCommand("&Key Describer Toggle", "Control+F1", "A key says what it would do instead of doing it.", toggleKeyDescriber);
        oDescriber.fChecked = delegate() { return KeyMap.bKeyDescriber; };
        addCommand("Hot&keys", "Control+Shift+F1", "Open the document of every command and key.", showHotkeys);
        addCommand("&ReadMe", "Alt+Shift+F1", "Open the quick start.", delegate() { return openHelp("ReadMe.htm"); });
        addCommand("Alternate &Menu...", "Alt+F10", "Every command in one list you can search.", showAlternateMenu);
        addCommand("Hotkey &Summary", "Alt+Shift+H", "Every command, key and summary in a window.", showHotkeySummary);
        addCommand("&Play Tutorials...", "", "Play the spoken tutorials in the Homer Player.", playTutorials);
        addCommand("&Elevate Version...", "F11", "Check for a newer release and offer to install it.", elevateVersion);
        addCommand("Copy &Log", "Control+F12", "Put this session's log on the clipboard as a file, ready to attach.", copyLog);

        foreach (string sProblem in KeyMap.lsProblems) Log.warn("Key map: " + sProblem);
        foreach (string sConflict in KeyMap.lsConflicts) Log.warn("Key claimed twice: " + sConflict);
        exportIfAsked();
        return true;
    }

    // bExportOnly: true when the program was started with /exportkeys. The
    // export is written as the menus are finished, and the app's Main then
    // ends without running the frame, so no window ever appears: the kit's
    // build runs the export of the sample on every build, and a window
    // flashing up would take focus from whatever the person was doing.
    public static bool bExportOnly = false;
    public static bool bExportWritten = false;

    // exportIfAsked: "<App>.exe /exportkeys <file>" writes every command and
    // key as declared. The kit's checkKeys reads the file.
    private bool exportIfAsked() {
        string[] aArgs = Environment.GetCommandLineArgs();
        for (int i = 1; i < aArgs.Length - 1; i++) {
            string sSwitch = aArgs[i].ToLowerInvariant();
            if (sSwitch != "/exportkeys" && sSwitch != "-exportkeys" && sSwitch != "--exportkeys") continue;
            bExportOnly = true;
            bExportWritten = KeyMap.exportInix(aArgs[i + 1], sAppName);
            Log.info("Exported commands to " + aArgs[i + 1] + (bExportWritten ? "" : " -- FAILED"));
            return bExportWritten;
        }
        return false;
    }

    // runOrExport: what an app's Main calls instead of Application.Run. It runs
    // the frame normally, or, after an export, returns at once: 0 when the
    // export was written, 1 when it was not.
    public static int runOrExport(MdiFrame frm) {
        if (bExportOnly) return bExportWritten ? 0 : 1;
        Application.Run(frm);
        return 0;
    }

    // ------- running a command by name (the earlier frame's way) -------

    public bool runCommand(string sCommand) {
        Log.info("Command: " + sCommand);
        if (KeyMap.bKeyDescriber) {
            KeyMap.Command c = KeyMap.commandById(KeyMap.toId(sCommand));
            Say.sayForced(c == null ? sCommand : KeyMap.describe(c.primaryKey, c));
            return true;
        }
        try {
            if (onCommand(sCommand)) return true;
            KeyMap.Command c = KeyMap.commandById(KeyMap.toId(sCommand));
            return c != null && c.fRun != null && c.fRun();
        }
        catch (Exception oError) {
            Log.exception(oError);
            Say.sayForced(sCommand + " failed. The log has why.");
            return false;
        }
    }

    // onCommand: an app written for the earlier frame handles its commands
    // here. An app using addCommand never needs it.
    protected virtual bool onCommand(string sCommand) {
        return false;
    }

    // ------- the earlier names for the window commands -------

    public List<string> windowTitles() { return MdiWindows.titles(this); }
    public bool sayWindows() { return MdiWindows.sayOpen(this); }
    public bool pickWindow() { return MdiWindows.pick(this); }
    public bool stepWindow(int iDirection) { return MdiWindows.step(this, iDirection); }
    public bool closeCurrent() { return MdiWindows.closeCurrent(this); }
    public bool closeOthers() { return MdiWindows.closeOthers(this); }

    // ------- query -------

    public bool sayClipboard() {
        string sText = "";
        try { if (Clipboard.ContainsText()) sText = Clipboard.GetText(); } catch (Exception oError) { Log.exception(oError); }
        if (sText.Length == 0) return KeyMap.answer("Clipboard", "The clipboard holds no text");
        return KeyMap.answer("Clipboard", sText);
    }

    public bool sayTime() {
        DateTime dtNow = DateTime.Now;
        return KeyMap.answer("Time", dtNow.ToShortTimeString(), dtNow.ToLongDateString());
    }

    // ------- scripts -------

    // scriptFiles: the user's own scripts first, then the shipped ones.
    public List<string> scriptFiles() {
        List<string> lsFound = new List<string>();
        List<string> lsSeen = new List<string>();
        foreach (string sFolder in new string[] { Paths.scripts(), Paths.shippedScripts() }) {
            try {
                foreach (string sPath in System.IO.Directory.GetFiles(sFolder)) {
                    string sName = System.IO.Path.GetFileName(sPath);
                    if (lsSeen.Contains(sName.ToLower())) continue;
                    lsSeen.Add(sName.ToLower());
                    lsFound.Add(sPath);
                }
            }
            catch (Exception) {
            }
        }
        lsFound.Sort(StringComparer.OrdinalIgnoreCase);
        return lsFound;
    }

    // runScript: Invoke Script. A list of every script, reachable by its
    // first letters, with no path to type.
    public bool runScript() {
        List<string> lsScripts = scriptFiles();
        if (lsScripts.Count == 0) {
            Say.sayForced("0 scripts. Put one in " + Paths.scripts());
            return true;
        }
        List<string> lsNames = new List<string>();
        foreach (string sPath in lsScripts) lsNames.Add(System.IO.Path.GetFileName(sPath));
        using (LbcDialog dlg = new LbcDialog("Invoke Script", this)) {
            ListBox lb = dlg.addPickBox("&Script:", lsNames, "",
                "Type the start of a name, then press Enter to run it.");
            if (!dlg.runOkCancel()) return true;
            int iPick = lb.SelectedIndex;
            if (iPick < 0) return true;
            Log.info("Running script: " + lsScripts[iPick]);
            try {
                System.Diagnostics.ProcessStartInfo oStart = new System.Diagnostics.ProcessStartInfo(lsScripts[iPick]);
                oStart.UseShellExecute = true;
                oStart.WorkingDirectory = Paths.results();
                System.Diagnostics.Process.Start(oStart);
                Say.sayForced(lsNames[iPick] + " started");
            }
            catch (Exception oError) {
                Log.exception(oError);
                Say.sayForced("That script could not be started. The log has why.");
            }
        }
        return true;
    }

    // ------- settings -------

    // addSetting: declare a setting the person may change while the program
    // runs. The frame does the list, the reading, the writing and the call
    // back into the app.
    public bool addSetting(string sName, string sDefault, string sSummary) {
        dSettable[sName] = sDefault;
        dSettableSummary[sName] = sSummary;
        return true;
    }

    public string settingsFile() {
        return Paths.configFile(sAppName + ".inix");
    }

    public string settingValue(string sName) {
        string sDefault = dSettable.ContainsKey(sName) ? dSettable[sName] : "";
        return InixCodec.readValue(settingsFile(), "Settings", sName, sDefault);
    }

    // changeSetting: Edit Settings. Pick the setting, type the value, and the
    // program acts on it at once -- no restart, no file to find.
    public bool changeSetting() {
        List<string> lsNames = new List<string>(dSettable.Keys);
        lsNames.Sort(StringComparer.OrdinalIgnoreCase);
        if (lsNames.Count == 0) {
            Say.sayForced("0 settings can be changed here");
            return true;
        }
        string sName = "";
        using (LbcDialog dlg = new LbcDialog("Edit Settings", this)) {
            ListBox lb = dlg.addPickBox("&Setting:", lsNames, "",
                "Pick the setting to change, then press Enter.");
            if (!dlg.runOkCancel()) return true;
            if (lb.SelectedIndex < 0) return true;
            sName = lsNames[lb.SelectedIndex];
        }
        string sNow = settingValue(sName);
        using (LbcDialog dlg = new LbcDialog("Edit Settings", this)) {
            TextBox tb = dlg.addInputBox("&" + sName + ":", sNow,
                dSettableSummary.ContainsKey(sName) ? dSettableSummary[sName] : "");
            if (!dlg.runOkCancel()) return true;
            if (!InixCodec.writeValue(settingsFile(), "Settings", sName, tb.Text)) {
                Say.sayForced(sName + " could not be saved. The log has why.");
                Log.error("Setting " + sName + " could not be written to " + settingsFile());
                return true;
            }
            Log.info("Setting " + sName + " = " + tb.Text);
            onSettingChanged(sName, tb.Text);
            Say.sayForced(sName + " is now " + tb.Text);
        }
        return true;
    }

    protected virtual bool onSettingChanged(string sName, string sValue) {
        return false;
    }

    // ------- help -------

    public bool toggleKeyDescriber() {
        KeyMap.bKeyDescriber = !KeyMap.bKeyDescriber;
        Say.sayForced(KeyMap.bKeyDescriber ? "Key Describer on" : "Key Describer off");
        return true;
    }

    // showAlternateMenu: every command in one searchable list. Its key and
    // summary follow its name, so the list answers "how do I" as well.
    public bool showAlternateMenu() {
        List<KeyMap.Command> lsCommands = new List<KeyMap.Command>();
        foreach (string sId in KeyMap.lsCommandOrder) lsCommands.Add(KeyMap.dCommands[sId]);
        lsCommands.Sort(delegate(KeyMap.Command a, KeyMap.Command b) { return string.Compare(a.sName, b.sName, StringComparison.OrdinalIgnoreCase); });
        if (lsCommands.Count == 0) { Say.sayForced("0 commands"); return true; }
        List<string> lsLines = new List<string>();
        foreach (KeyMap.Command c in lsCommands) {
            string sLine = c.sName + ", " + (c.lsKeys.Count > 0 ? c.keysText() : "no key");
            if (c.sSummary.Length > 0) sLine += ": " + c.sSummary;
            lsLines.Add(sLine);
        }
        KeyMap.Command oChosen = null;
        using (LbcDialog dlg = new LbcDialog("Alternate Menu", this)) {
            ListBox lb = dlg.addPickBox("&Command:", lsLines, "",
                "Type the start of a command, then press Enter to run it.");
            if (!dlg.runOkCancel()) return true;
            if (lb.SelectedIndex >= 0) oChosen = lsCommands[lb.SelectedIndex];
        }
        // Run after the list has closed, so the command acts on the window
        // the person was in, not on the list.
        if (oChosen != null) KeyMap.runCommand(oChosen);
        return true;
    }

    public bool showHotkeySummary() {
        HelpDialog.show(this, "Hotkey Summary", KeyMap.hotkeySummary());
        return true;
    }

    public bool showHotkeys() {
        string sPath = System.IO.Path.Combine(Paths.shippedHelp(), "Hotkeys.htm");
        if (System.IO.File.Exists(sPath)) return openPath(sPath);
        return showHotkeySummary();
    }

    public bool showAbout() {
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

    public string versionText() {
        try {
            Type oBuild = Type.GetType("BuildVersion");
            if (oBuild != null) {
                System.Reflection.FieldInfo oField = oBuild.GetField("Version");
                if (oField != null) return "" + oField.GetValue(null);
            }
        }
        catch (Exception) {
        }
        return "unknown";
    }

    // configureUpdates: the GitHub owner and repository that Elevate Version
    // asks for a newer release. Call it once at startup.
    public bool configureUpdates(string sOwner, string sRepo) {
        return Elevate.configure(sOwner, sRepo, versionText());
    }

    public bool elevateVersion() {
        if (!Elevate.isConfigured) {
            Say.sayForced("This program has no release address, so it cannot look for a newer version");
            return true;
        }
        Elevate.offer(this);
        return true;
    }

    // playTutorials: the walks play in the Homer Player when the app compiles
    // it in; otherwise the written tutorials open.
    public bool playTutorials() {
        try {
            Type oPlayer = Type.GetType("Homer.MediaPlayer");
            if (oPlayer != null) {
                System.Reflection.MethodInfo oPlay = oPlayer.GetMethod("playTutorials",
                    new Type[] { typeof(IWin32Window), typeof(string), typeof(string) });
                if (oPlay != null) {
                    object oResult = oPlay.Invoke(null, new object[] { this, sAppName, Paths.shippedHelp() });
                    if (oResult is bool && (bool)oResult) return true;
                }
            }
        }
        catch (Exception oError) {
            Log.exception(oError);
        }
        return openHelp("Tutorials.htm");
    }

    // copyLog: the log as a FILE on the clipboard, so Control+V in an email
    // attaches it rather than pasting its name.
    public bool copyLog() {
        string sLog = Log.path;
        if (string.IsNullOrEmpty(sLog) || !System.IO.File.Exists(sLog)) {
            Say.sayForced("There is no log for this session");
            return true;
        }
        try {
            StringCollection lsFiles = new StringCollection();
            lsFiles.Add(sLog);
            Clipboard.SetFileDropList(lsFiles);
            Say.sayForced("Log copied as a file, ready to paste as an attachment");
        }
        catch (Exception oError) {
            Log.exception(oError);
            Say.sayForced("The log could not be copied. Its path is " + sLog);
        }
        return true;
    }

    // openHelp: a document from the shipped help folder, or the ReadMe from
    // the top of the program folder.
    public bool openHelp(string sFileName) {
        string sPath = System.IO.Path.Combine(Paths.shippedHelp(), sFileName);
        if (!System.IO.File.Exists(sPath)) sPath = System.IO.Path.Combine(Paths.installedFolder, sFileName);
        if (!System.IO.File.Exists(sPath)) {
            Say.sayForced(sFileName + " was not found beside the program");
            return true;
        }
        return openPath(sPath);
    }

    public bool openPath(string sPath) {
        try { System.Diagnostics.Process.Start(sPath); }
        catch (Exception oError) { Log.exception(oError); Say.sayForced("That could not be opened. The log has why."); }
        return true;
    }

    // showDocumentation: the earlier name.
    public bool showDocumentation() { return openHelp(sAppName + ".htm"); }
}

// ------- the child -------

public class MdiChild : Form {
    private string sSubject = "";
    private string sView = "";

    // THE CHILD IS BUILT BY THE SAME BUILDER AS A DIALOG. Add controls through
    // lbc -- add order is focus order, an ampersand is the whole of an access
    // key -- then call finishLayout.
    public LbcDialog lbc;

    public MdiChild(MdiFrame frmParent) {
        this.MdiParent = frmParent;
        this.WindowState = FormWindowState.Maximized;
        lbc = new LbcDialog("", frmParent, this);
        // A closed window's repeat and search state go with it.
        this.FormClosed += delegate(object oSender, FormClosedEventArgs evArgs) { KeyMap.forgetTarget(this); };
    }

    // ProcessCmdKey: a key in a child goes to the one router, with the frame
    // as its window, before the child's controls can take it.
    protected override bool ProcessCmdKey(ref Message msg, Keys keyData) {
        Form frmFrame = this.MdiParent;
        if (frmFrame != null && KeyMap.route(frmFrame, ref msg, keyData)) return true;
        return base.ProcessCmdKey(ref msg, keyData);
    }

    public bool finishLayout() {
        lbc.layoutIntoForm();
        return true;
    }

    // manageList: Shift+letter in this list runs the list's commands, and
    // typing the start of an item goes to it.
    public bool manageList(Control ctl) {
        return KeyMap.manageList(ctl);
    }

    // setTitle: what this window is showing. NEVER the app name.
    public bool setTitle(string sSubjectGiven, string sViewGiven) {
        sSubject = sSubjectGiven == null ? "" : sSubjectGiven;
        sView = sViewGiven == null ? "" : sViewGiven;
        this.Text = sView == "" ? sSubject : sSubject + " - " + sView;
        return true;
    }

    public string subject { get { return sSubject; } }
    public string view { get { return sView; } }

    public bool setStatusText(string sText) {
        lbc.setStatusText(sText == null ? "" : sText);
        return true;
    }
}

} // namespace Homer (Mdi.cs)
