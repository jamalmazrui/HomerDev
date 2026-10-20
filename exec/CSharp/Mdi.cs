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
//   Edit     Control+Apostrophe Save Clipboard, Control+Shift+Apostrophe
//            Append Clipboard, Alt+Shift+Apostrophe Clear Clipboard
//   Query    Alt+Apostrophe Say Clipboard, Alt+SemiColon Say Time
//   Misc     Alt+Shift+E Edit Settings, Control+Shift+I Invoke Script
//   Help     F1 Documentation, Shift+F1 History of Changes, Alt+F1 About,
//            Control+F1 Key Describer Toggle, Control+Shift+F1 Hotkeys,
//            Alt+Shift+F1 ReadMe, Alt+F10 Alternate Menu, Alt+Shift+H Hotkey
//            Summary, F11 Elevate Version, Control+F12 Copy Log, and Play
//            Tutorials in the Homer Player
//
// The bodies of the Say, clipboard, log and Help commands are SuiteCommands,
// which an app with a frame of its own calls too (kit 1.74.0).
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

// ------- the clipboard and text files -------

// ClipFile: moving the clipboard's text into a file, by the suite's text-file
// rules (help\HomerSuite.md): a new file is UTF-8 with a byte order mark and
// CRLF line endings and never replaces a file; an append detects the file's
// encoding, never puts a second byte order mark mid-file, says whether it
// started a new line, and leaves the file as it was if anything fails.
public static class ClipFile {

    public static string clipboardText() {
        try { if (Clipboard.ContainsText()) return Clipboard.GetText(); }
        catch (Exception oError) { Log.exception(oError); }
        return "";
    }

    public static string toCrLf(string sText) {
        return (sText == null ? "" : sText).Replace("\r\n", "\n").Replace("\r", "\n").Replace("\n", "\r\n");
    }

    // proposedPath: "Clipboard 2026-10-18 1405.txt" in the folder, with a
    // number added when that name is taken, so the proposal never replaces.
    public static string proposedPath(string sFolder) {
        string sStem = "Clipboard " + DateTime.Now.ToString("yyyy-MM-dd HHmm");
        string sPath = System.IO.Path.Combine(sFolder, sStem + ".txt");
        for (int i = 2; System.IO.File.Exists(sPath); i++) sPath = System.IO.Path.Combine(sFolder, sStem + " " + i.ToString() + ".txt");
        return sPath;
    }

    // writeNew: a new file only. CreateNew fails if the file exists, so an
    // existing file can never be replaced, even by a race.
    public static bool writeNew(string sPath, string sText, out string sError) {
        sError = "";
        try {
            using (System.IO.FileStream oStream = new System.IO.FileStream(sPath, System.IO.FileMode.CreateNew, System.IO.FileAccess.Write)) {
                byte[] abBom = new byte[] { 0xEF, 0xBB, 0xBF };
                byte[] abText = new System.Text.UTF8Encoding(false).GetBytes(toCrLf(sText));
                oStream.Write(abBom, 0, abBom.Length);
                oStream.Write(abText, 0, abText.Length);
            }
            return true;
        }
        catch (Exception oError) {
            Log.exception(oError);
            sError = oError.Message;
            return false;
        }
    }

    // appendRefusal: "" when text can be appended to these bytes as UTF-8,
    // otherwise the plain reason it cannot. Only UTF-8 is appended to; any
    // other encoding would end up mixed in one file.
    public static string appendRefusal(byte[] abExisting) {
        if (abExisting.Length >= 2 && ((abExisting[0] == 0xFF && abExisting[1] == 0xFE) || (abExisting[0] == 0xFE && abExisting[1] == 0xFF)))
            return "it is in UTF-16, and adding UTF-8 text would mix two encodings in one file";
        int iStart = hasBom(abExisting) ? 3 : 0;
        try {
            new System.Text.UTF8Encoding(false, true).GetString(abExisting, iStart, abExisting.Length - iStart);
            return "";
        }
        catch (Exception) {
            return "it is not in UTF-8 (it may be in an older Windows code page), and adding UTF-8 text would mix two encodings in one file";
        }
    }

    private static bool hasBom(byte[] ab) {
        return ab.Length >= 3 && ab[0] == 0xEF && ab[1] == 0xBB && ab[2] == 0xBF;
    }

    // append: the clipboard text at the end of an existing UTF-8 file, on a
    // new line when the file does not already end with one. Written to a
    // temporary file beside it, then swapped in, so a failure halfway leaves
    // the original exactly as it was.
    public static bool append(string sPath, string sText, out bool bAddedBreak, out string sError) {
        bAddedBreak = false;
        sError = "";
        string sTemp = "";
        try {
            byte[] abExisting = System.IO.File.ReadAllBytes(sPath);
            string sWhy = appendRefusal(abExisting);
            if (sWhy.Length > 0) { sError = sWhy; return false; }
            List<byte> lsBytes = new List<byte>(abExisting);
            if (abExisting.Length == 0) lsBytes.AddRange(new byte[] { 0xEF, 0xBB, 0xBF });
            int iEnd = abExisting.Length;
            bool bEndsWithBreak = iEnd > 0 && abExisting[iEnd - 1] == 0x0A;
            bool bOnlyBom = iEnd == 3 && hasBom(abExisting);
            if (iEnd > 0 && !bEndsWithBreak && !bOnlyBom) {
                lsBytes.Add(0x0D);
                lsBytes.Add(0x0A);
                bAddedBreak = true;
            }
            lsBytes.AddRange(new System.Text.UTF8Encoding(false).GetBytes(toCrLf(sText)));
            sTemp = sPath + ".homer-append.tmp";
            System.IO.File.WriteAllBytes(sTemp, lsBytes.ToArray());
            System.IO.File.Replace(sTemp, sPath, null);
            return true;
        }
        catch (Exception oError) {
            Log.exception(oError);
            sError = oError.Message;
            try { if (sTemp.Length > 0 && System.IO.File.Exists(sTemp)) System.IO.File.Delete(sTemp); } catch (Exception) { }
            return false;
        }
    }
}

// ------- the suite's shared commands -------

// SuiteCommands: ONE NAME, KEY AND DESCRIPTION MEANS ONE PIECE OF CODE (the
// suite contract, help\HomerSuite.md). Every Homer app's Say Clipboard, Say
// Time, Copy Log, clipboard family and Help openers call these, whatever frame
// the app has -- this kit's MdiFrame, or an app's own frame that has not moved
// to it yet -- so the wording and the behavior are the same in every app.
//
// Each method takes only what it needs: an owner window for a dialog, a log
// path for an app that keeps its own log. The Say methods answer through
// KeyMap.answer, so one press speaks, two spell, and three show a read-only
// window, wherever the kit's router counted the presses.
//
// The window family is MdiWindows, above; ClipFile does the file work. The
// kit's checkKeys confirms, on every push, that each manifest command marked
// shared= really calls the method named here.
//
// BEST OF THE APPS (kit 1.74.0): Say Clipboard reads a list of copied files
// as FileDir did; Copy Log puts the log on the clipboard as a file AND as its
// path, as EdSharp and FileDir did; everything else is the frame's.
public static class SuiteCommands {

    public const string sNoText = "The clipboard holds no text";

    // ------- the Say family -------

    // sayClipboard: Alt+Apostrophe. Copied files are counted and named, one
    // utterance each; text is spoken as it is.
    public static bool sayClipboard() {
        List<string> lsFiles = new List<string>();
        string sText = "";
        try {
            if (Clipboard.ContainsFileDropList()) {
                foreach (string sPath in Clipboard.GetFileDropList()) lsFiles.Add(sPath);
            }
            else if (Clipboard.ContainsText()) {
                sText = Clipboard.GetText();
            }
        }
        catch (Exception oError) {
            Log.exception(oError);
        }
        if (lsFiles.Count > 0) {
            List<string> lsParts = new List<string>();
            lsParts.Add(lsFiles.Count == 1 ? "1 file on the clipboard" : lsFiles.Count.ToString() + " files on the clipboard");
            lsParts.AddRange(lsFiles);
            return KeyMap.answer("Clipboard", lsParts.ToArray());
        }
        if (sText.Length == 0) return KeyMap.answer("Clipboard", sNoText);
        return KeyMap.answer("Clipboard", sText);
    }

    // sayTime: Alt+SemiColon. The time, then the date, as two utterances.
    public static bool sayTime() {
        DateTime dtNow = DateTime.Now;
        return KeyMap.answer("Time", dtNow.ToShortTimeString(), dtNow.ToLongDateString());
    }

    // ------- the clipboard family -------

    // clearClipboard: Alt+Shift+Apostrophe.
    public static bool clearClipboard() {
        try {
            Clipboard.Clear();
            Say.sayForced("Clipboard cleared");
        }
        catch (Exception oError) {
            Log.exception(oError);
            Say.sayForced("The clipboard could not be cleared. The log has why.");
        }
        return true;
    }

    // saveClipboard: Control+Apostrophe. A name is proposed in the results
    // folder; a name already taken is never replaced, and the question comes
    // again.
    public static bool saveClipboard(IWin32Window oOwner) {
        string sText = ClipFile.clipboardText();
        if (sText.Length == 0) { Say.sayForced(sNoText); return true; }
        string sFolder = Paths.results();
        string sName = System.IO.Path.GetFileName(ClipFile.proposedPath(sFolder));
        while (true) {
            using (LbcDialog dlg = new LbcDialog("Save Clipboard", oOwner)) {
                TextBox tb = dlg.addInputBox("&File name:", sName, "The new file, in the results folder. A file already there is never replaced.");
                if (!dlg.runOkCancel()) return true;
                sName = tb.Text.Trim();
            }
            if (sName == "" || sName.IndexOfAny(System.IO.Path.GetInvalidFileNameChars()) >= 0) {
                Say.sayForced("A file name cannot be empty or hold any of these: \\ / : * ? quote < > |");
                continue;
            }
            if (System.IO.Path.GetExtension(sName) == "") sName += ".txt";
            string sPath = System.IO.Path.Combine(sFolder, sName);
            if (System.IO.File.Exists(sPath)) {
                Say.sayForced(sName + " already exists. Choose another name.");
                continue;
            }
            string sError;
            if (ClipFile.writeNew(sPath, sText, out sError)) {
                Log.info("Saved the clipboard to " + sPath);
                Say.sayForced("Saved " + sName + " in the results folder");
            }
            else {
                Say.sayForced(sName + " could not be saved: " + sError);
            }
            return true;
        }
    }

    // appendClipboard: Control+Shift+Apostrophe. Pick a text file; the text
    // goes at its end, by the suite's append rules.
    public static bool appendClipboard(IWin32Window oOwner) {
        string sText = ClipFile.clipboardText();
        if (sText.Length == 0) { Say.sayForced(sNoText); return true; }
        string sPath = "";
        using (OpenFileDialog dlg = new OpenFileDialog()) {
            dlg.Title = "Append Clipboard";
            dlg.InitialDirectory = Paths.results();
            dlg.Filter = "Text files (*.txt, *.md, *.inix, *.csv)|*.txt;*.md;*.inix;*.csv|All files (*.*)|*.*";
            dlg.CheckFileExists = true;
            if (dlg.ShowDialog(oOwner) != DialogResult.OK) return true;
            sPath = dlg.FileName;
        }
        bool bAddedBreak;
        string sError;
        string sName = System.IO.Path.GetFileName(sPath);
        if (ClipFile.append(sPath, sText, out bAddedBreak, out sError)) {
            Log.info("Appended the clipboard to " + sPath + (bAddedBreak ? ", after a line break" : ""));
            Say.sayForced("Appended to " + sName + (bAddedBreak ? ", starting a new line" : ""));
        }
        else {
            Say.sayForced("Nothing was added to " + sName + ", because " + sError + ". Save Clipboard makes a new file instead.");
        }
        return true;
    }

    // ------- the log -------

    // copyLog: Control+F12. The log on the clipboard as a FILE, so Control+V
    // in an email attaches it, and as its PATH in text, so a program that
    // reads only text gets the path. One DataObject carries both.
    public static bool copyLog() {
        return copyLog(Log.path);
    }

    // copyLog(sLogPath): for an app that keeps its own log file.
    // ---- one Homer app handing a file to another (kit 1.79.0) ----

    // homerProgram: another Homer app's program -- its Program Files folder, under exec as the
    // Homer layout puts it or at the top as EdSharp's does, then Windows' registered App Paths.
    // "" when it is not installed.
    public static string homerProgram(string sApp) { return Paths.homerProgram(sApp); }

    // openInHomerApp: start another Homer app on a path. Each is a single instance, so when it is
    // already running, Windows hands it the path and it opens it there. When the app is not
    // installed, a message says so and where to get it.
    public static bool openInHomerApp(IWin32Window owner, string sApp, string sPath) {
        string sExe = homerProgram(sApp);
        if (sExe.Length == 0) {
            Log.info("Open in " + sApp + ": not installed");
            MessageBox.Show(owner, sApp + " is not installed on this computer. The HomerDev dialog lists every Homer project and can install it.",
                sApp, MessageBoxButtons.OK, MessageBoxIcon.Information);
            return false;
        }
        try {
            System.Diagnostics.ProcessStartInfo oStart = new System.Diagnostics.ProcessStartInfo(sExe, "\"" + sPath + "\"");
            oStart.UseShellExecute = false;
            oStart.WorkingDirectory = System.IO.Path.GetDirectoryName(sExe);
            System.Diagnostics.Process.Start(oStart);
            Log.info("Open in " + sApp + ": " + sExe + " " + sPath);
            Say.say("Opening in " + sApp);
            return true;
        } catch (Exception oError) {
            Log.info("Open in " + sApp + " failed: " + oError.Message);
            MessageBox.Show(owner, sApp + " could not be started: " + oError.Message, sApp, MessageBoxButtons.OK, MessageBoxIcon.Information);
            return false;
        }
    }

    public static bool copyLog(string sLogPath) {
        if (string.IsNullOrEmpty(sLogPath) || !System.IO.File.Exists(sLogPath)) {
            Say.sayForced("There is no log for this session");
            return true;
        }
        try {
            DataObject oData = new DataObject();
            StringCollection lsFiles = new StringCollection();
            lsFiles.Add(sLogPath);
            oData.SetFileDropList(lsFiles);
            oData.SetText(sLogPath);
            Clipboard.SetDataObject(oData, true);
            Log.info("Copied the log to the clipboard: " + sLogPath);
            Say.sayForced("Log copied as a file, ready to paste as an attachment");
        }
        catch (Exception oError) {
            Log.exception(oError);
            Say.sayForced("The log could not be copied. Its path is " + sLogPath);
        }
        return true;
    }

    // ------- the Help openers -------

    // helpPath: a document from the shipped help folder, else from the top of
    // the program folder, else "" when it is in neither.
    public static string helpPath(string sFileName) {
        string sPath = System.IO.Path.Combine(Paths.shippedHelp(), sFileName);
        if (System.IO.File.Exists(sPath)) return sPath;
        sPath = System.IO.Path.Combine(Paths.installedFolder, sFileName);
        if (System.IO.File.Exists(sPath)) return sPath;
        return "";
    }

    public static bool openHelp(string sFileName) {
        string sPath = helpPath(sFileName);
        if (sPath == "") {
            Say.sayForced(sFileName + " was not found beside the program");
            return true;
        }
        return openPath(sPath);
    }

    // openDocumentation: F1, the app's own guide, <App>.htm.
    public static bool openDocumentation(string sAppName) {
        return openHelp(sAppName + ".htm");
    }

    // openHistory: Shift+F1, History of Changes.
    public static bool openHistory() {
        return openHelp("History.htm");
    }

    // openReadMe: Alt+Shift+F1, the quick start.
    public static bool openReadMe() {
        return openHelp("ReadMe.htm");
    }

    // openHotkeys: Control+Shift+F1, the document of every command and key.
    // When it is not installed, the Hotkey Summary window is shown instead.
    public static bool openHotkeys(IWin32Window oOwner) {
        string sPath = helpPath("Hotkeys.htm");
        if (sPath != "") return openPath(sPath);
        HelpDialog.show(oOwner, "Hotkey Summary", KeyMap.hotkeySummary());
        return true;
    }

    public static bool openPath(string sPath) {
        try { System.Diagnostics.Process.Start(sPath); }
        catch (Exception oError) { Log.exception(oError); Say.sayForced("That could not be opened. The log has why."); }
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
    private Dictionary<ToolStripMenuItem, List<char>> dMenuLetters = new Dictionary<ToolStripMenuItem, List<char>>();
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
        // Command echo by the suite's rule, KeyMap.shouldEcho (kit 1.74.0).
        KeyMap.bEchoCommands = true;

        // A settings file that cannot be read is reported in the log, once,
        // instead of being taken silently as empty (kit 1.73.4).
        if (InixCodec.onProblem == null) InixCodec.onProblem = delegate(string sProblem) { Log.warn(sProblem); };

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
        LbcMenuItem item = new LbcMenuItem(uniqueTrigger(sCaption));
        item.ToolTipText = sSummary;
        if (oCommand.lsKeys.Count > 0) item.ShortcutKeyDisplayString = oCommand.keysText();
        // A menu choice is always a first press, whatever keys came before it.
        item.Click += delegate(object oSender, EventArgs evArgs) { KeyMap.iPressCount = 1; KeyMap.runCommand(oCommand); };
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

    // uniqueTrigger: ONE TRIGGER LETTER PER MENU. The first item in a menu to
    // claim a letter keeps it; a later item that would repeat it loses its
    // ampersand rather than take a letter from the middle of a word, so an
    // app's own items and the frame's can never fight over a letter.
    private string uniqueTrigger(string sCaption) {
        if (menuNow == null || sCaption == null) return sCaption;
        int iAmp = sCaption.IndexOf('&');
        if (iAmp < 0 || iAmp + 1 >= sCaption.Length) return sCaption;
        char chLetter = char.ToUpperInvariant(sCaption[iAmp + 1]);
        List<char> lsUsed;
        if (!dMenuLetters.TryGetValue(menuNow, out lsUsed)) {
            lsUsed = new List<char>();
            dMenuLetters[menuNow] = lsUsed;
        }
        if (lsUsed.Contains(chLetter)) {
            Log.info("Menu " + menuNow.Text.Replace("&", "") + ": " + KeyMap.plainName(sCaption) + " has no trigger letter, because " + chLetter.ToString() + " is taken");
            return sCaption.Remove(iAmp, 1);
        }
        lsUsed.Add(chLetter);
        return sCaption;
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
        addMenu("&Edit");
        addCommand("&Save Clipboard...", "Control+Apostrophe", "Save the clipboard's text in a new file.", saveClipboard);
        addCommand("&Append Clipboard...", "Control+Shift+Apostrophe", "Add the clipboard's text to the end of a text file.", appendClipboard);
        addCommand("&Clear Clipboard", "Alt+Shift+Apostrophe", "Empty the clipboard.", clearClipboard).bNoEcho = true;

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
        addCommand("Close Window", "Control+F4", "Close this window.", delegate() { return MdiWindows.closeCurrent(this); });
        addCommand("Close &All But Current Window", "Control+Shift+F4", "Close every window but this one.", delegate() { return MdiWindows.closeOthers(this); });

        addMenu("&Help");
        addCommand("&Documentation", "F1", "Open the guide.", delegate() { return openHelp(sAppName + ".htm"); }).bNoEcho = true;
        addCommand("&History of Changes", "Shift+F1", "Open the list of changes, newest first.", SuiteCommands.openHistory).bNoEcho = true;
        addCommand("&About", "Alt+F1", "The name, the version, and where this copy keeps its files.", showAbout).bNoEcho = true;
        KeyMap.Command oDescriber = addCommand("&Key Describer Toggle", "Control+F1", "A key says what it would do instead of doing it.", toggleKeyDescriber);
        oDescriber.fChecked = delegate() { return KeyMap.bKeyDescriber; };
        addCommand("Hotkeys", "Control+Shift+F1", "Open the document of every command and key.", showHotkeys).bNoEcho = true;
        addCommand("&ReadMe", "Alt+Shift+F1", "Open the quick start.", SuiteCommands.openReadMe).bNoEcho = true;
        addCommand("Alternate &Menu...", "Alt+F10", "Every command in one list you can search.", showAlternateMenu);
        addCommand("Hotkey &Summary", "Alt+Shift+H", "Every command, key and summary in a window.", showHotkeySummary).bNoEcho = true;
        addCommand("&Play Tutorials...", "", "Play the spoken tutorials in the Homer Player.", playTutorials);
        addCommand("&Elevate Version...", "F11", "Check for a newer release and offer to install it.", elevateVersion);
        addCommand("Copy &Log", "Control+F12", "Put this session's log on the clipboard as a file, ready to attach.", copyLog).bNoEcho = true;

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

    // The Say, clipboard, log and Help commands are SuiteCommands's, so every
    // app's copy of them is one piece of code (kit 1.74.0).
    public bool sayClipboard() {
        return SuiteCommands.sayClipboard();
    }

    public bool saveClipboard() {
        return SuiteCommands.saveClipboard(this);
    }

    public bool appendClipboard() {
        return SuiteCommands.appendClipboard(this);
    }

    public bool clearClipboard() {
        return SuiteCommands.clearClipboard();
    }

    public bool sayTime() {
        return SuiteCommands.sayTime();
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
        return SuiteCommands.openHotkeys(this);
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

    public bool copyLog() {
        return SuiteCommands.copyLog();
    }

    public bool openHelp(string sFileName) {
        return SuiteCommands.openHelp(sFileName);
    }

    public bool openPath(string sPath) {
        return SuiteCommands.openPath(sPath);
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
