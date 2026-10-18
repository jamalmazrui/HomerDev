// KeyMap.cs -- the one command and key mechanism of every Homer app.
//
// REQUIRES: KeyName.cs, Log.cs, Say.cs, Lbc.cs (for HelpDialog).
//
// WHAT THIS IS. Every command a Homer app offers is declared ONCE, here, with
// a stable identifier, a name a person would say, the keys that run it, the
// context its keys belong to, a one-line summary, and the code that runs it.
// From that one declaration come the menu item's shortcut text, the Alternate
// Menu (Alt+F10), the Key Describer (Control+F1), the Hotkey Summary
// (Alt+Shift+H), the generated Hotkeys document, the checker's export, and
// the JAWS pass-through lines. Nothing is described twice, so nothing drifts.
//
// WHY A ROUTER AND NOT MENU SHORTCUTS. Windows Forms refuses many keys as
// menu shortcuts -- Shift plus a letter, plain Delete, plain Enter -- and a
// menu shortcut fires wherever the window is, even in a text box where the
// person meant to type. So every Homer window passes its keys to route(),
// which decides in a fixed order:
//
//   1. A bare Shift, Control or Alt is never a command.
//   2. The Key Describer, when on, describes instead of running.
//   3. A key that types or edits text is left to the text box, unless the
//      app has marked that text box as its editor (EdSharp's document).
//   4. In a managed list (the DbDo grid, the FileDir list), unshifted letters
//      and digits are left to the list for first-letter and typed-sequence
//      navigation; Shift plus a letter runs that list's command, or says that
//      none is bound, so a question never meets silence.
//   5. A command bound in the focused control's context wins over one bound
//      anywhere in the window.
//   6. A command that is unavailable says why, and does not run.
//
// A modal dialog is its own window with its own keys, so it never reaches
// here: Windows sends its keys to it first. That is the "modal dialog first"
// rule, and it costs nothing.
//
// FOR SOMEBODY BUILDING AN APP OF THEIR OWN (with an AI or without): use the
// frame in Mdi.cs, which calls everything here for you. You add a command
// with one line:
//
//     KeyMap.Command oAdd = addCommand("&Add Fruit", "Control+Shift+A",
//         "Put what is in the fruit field into this basket.", addFruit);
//
// and you never write key-handling code. The frame's guide is
// help\MdiFramework.md in the kit.
//
// COMPATIBILITY. The members this file had before kit 1.73.0 -- register,
// setSummary, getSummary, the d* dictionaries and the rest -- are kept, with
// their old meanings, because EdSharp and FileDir compile this file today.
// They feed the same tables, so an app moving to the new members later loses
// nothing.
//
// Camel Type throughout. C# 5 syntax only, because the kit still builds with
// the .NET Framework's own compiler when Visual Studio Build Tools are absent:
// no string interpolation, no "?.", no expression-bodied members.

using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Windows.Forms;

namespace Homer {

public static class KeyMap {

    // ------------------------------------------------------------- contexts
    //
    // Where a command's keys are live. "anywhere" means anywhere in the app's
    // windows, except where the rules above leave a key to a text box or a
    // list. "list" means only while a managed list has focus. "text" means
    // only while a marked editor has focus.
    public const string sAnywhere = "anywhere";
    public const string sListContext = "list";
    public const string sTextContext = "text";

    // The old name for "anywhere", kept for the old members.
    public const string sGlobalContext = "Global";

    // ------------------------------------------------------------- commands

    // Command: one thing the app can do, declared once.
    public class Command {
        public bool bOpensDialog;            // the caption ends in "..."; the dialog names itself
        public Func<bool> fChecked;          // null, or true when the command is a mode that is on
        public Func<bool> fRun;              // the work; true when done
        public Func<string> fUnavailable;    // null, or "" when available, else the reason it is not
        public List<Keys> lsKeys = new List<Keys>();   // the first is the primary key
        public ToolStripMenuItem oItem;      // the menu item, when the command has one
        public string sContext = sAnywhere;
        public string sDescription = "";     // longer help, for the Alternate Menu's detail
        public string sId = "";              // stable lowerCamel identifier
        public string sMenu = "";            // the menu it sits on, without the ampersand
        public string sName = "";            // what a person would say, no ampersand
        public string sRepeat = "";          // "", "review" (double press shows a window) or "again"
        public string sSummary = "";         // one verb-first line

        public Keys primaryKey { get { return lsKeys.Count > 0 ? lsKeys[0] : Keys.None; } }

        public string keysText() {
            List<string> lsNames = new List<string>();
            foreach (Keys k in lsKeys) lsNames.Add(friendlyKey(k));
            return string.Join(" or ", lsNames.ToArray());
        }

        public string unavailableReason() {
            if (fUnavailable == null) return "";
            try {
                string sWhy = fUnavailable();
                return sWhy == null ? "" : sWhy;
            }
            catch (Exception oError) {
                Log.exception(oError);
                return "";
            }
        }
    }

    // Every command, by identifier, in the order they were added.
    public static Dictionary<string, Command> dCommands = new Dictionary<string, Command>(StringComparer.OrdinalIgnoreCase);
    public static List<string> lsCommandOrder = new List<string>();

    // context -> key -> command identifier.
    private static Dictionary<string, Dictionary<Keys, string>> dContextKeys =
        new Dictionary<string, Dictionary<Keys, string>>(StringComparer.OrdinalIgnoreCase);

    // Problems found while commands were added: a duplicate identifier, a key
    // claimed twice in one context, a key Windows or a screen reader owns. The
    // frame writes them to the log at startup, and the checker reads them from
    // the export.
    public static List<string> lsProblems = new List<string>();

    // toId: "&Close All But Current Window..." -> "closeAllButCurrentWindow".
    public static string toId(string sName) {
        StringBuilder sbId = new StringBuilder();
        bool bNewWord = false;
        foreach (char ch in plainName(sName)) {
            if (char.IsLetterOrDigit(ch)) {
                if (sbId.Length == 0) sbId.Append(char.ToLowerInvariant(ch));
                else if (bNewWord) sbId.Append(char.ToUpperInvariant(ch));
                else sbId.Append(ch);
                bNewWord = false;
            }
            else bNewWord = true;
        }
        return sbId.ToString();
    }

    // plainName: a caption without its ampersand or a trailing "...".
    public static string plainName(string sCaption) {
        string s = (sCaption == null ? "" : sCaption).Replace("&", "").Trim();
        if (s.EndsWith("...")) s = s.Substring(0, s.Length - 3).TrimEnd();
        return s;
    }

    // addCommand: declare a command. Returns it, so the caller can set the
    // optional parts (fUnavailable, fChecked, sRepeat, sDescription).
    public static Command addCommand(string sCaption, string sKeys, string sContext, string sSummary, Func<bool> fRun) {
        Command oCommand = new Command();
        oCommand.sName = plainName(sCaption);
        oCommand.sId = toId(sCaption);
        oCommand.bOpensDialog = (sCaption == null ? "" : sCaption).TrimEnd().EndsWith("...");
        oCommand.sContext = string.IsNullOrEmpty(sContext) ? sAnywhere : sContext;
        oCommand.sSummary = sSummary == null ? "" : sSummary;
        oCommand.fRun = fRun;
        foreach (Keys k in parseKeys(sKeys, oCommand.sName)) oCommand.lsKeys.Add(k);
        return addCommand(oCommand);
    }

    public static Command addCommand(Command oCommand) {
        if (oCommand == null || string.IsNullOrEmpty(oCommand.sId)) return oCommand;
        if (dCommands.ContainsKey(oCommand.sId)) {
            lsProblems.Add("Identifier " + oCommand.sId + " is declared twice; the second, " + oCommand.sName + ", was not added.");
            return dCommands[oCommand.sId];
        }
        dCommands[oCommand.sId] = oCommand;
        lsCommandOrder.Add(oCommand.sId);
        foreach (Keys k in oCommand.lsKeys) bindKey(oCommand, k);
        // The old tables, so the old members keep answering.
        dCommandToKey[oCommand.sName] = oCommand.primaryKey;
        dCommandToSummary[oCommand.sName] = oCommand.sSummary;
        dCommandToContext[oCommand.sName] = oCommand.sContext;
        if (oCommand.sDescription.Length > 0) dCommandToDescription[oCommand.sName] = oCommand.sDescription;
        return oCommand;
    }

    // addAlias: a second key for a command already declared.
    public static bool addAlias(string sId, string sKeys) {
        Command oCommand;
        if (!dCommands.TryGetValue(sId, out oCommand)) {
            lsProblems.Add("Alias " + sKeys + " names " + sId + ", which is not declared.");
            return false;
        }
        foreach (Keys k in parseKeys(sKeys, oCommand.sName)) {
            if (oCommand.lsKeys.Contains(k)) continue;
            oCommand.lsKeys.Add(k);
            bindKey(oCommand, k);
        }
        if (oCommand.oItem != null) oCommand.oItem.ShortcutKeyDisplayString = oCommand.keysText();
        return true;
    }

    private static bool bindKey(Command oCommand, Keys k) {
        if (k == Keys.None) return false;
        Dictionary<Keys, string> dKeys;
        if (!dContextKeys.TryGetValue(oCommand.sContext, out dKeys)) {
            dKeys = new Dictionary<Keys, string>();
            dContextKeys[oCommand.sContext] = dKeys;
        }
        string sOther;
        if (dKeys.TryGetValue(k, out sOther) && !string.Equals(sOther, oCommand.sId, StringComparison.OrdinalIgnoreCase)) {
            lsProblems.Add(friendlyKey(k) + " is claimed by " + sOther + " and by " + oCommand.sId + " in the " + oCommand.sContext + " context; the first keeps it.");
            return false;
        }
        dKeys[k] = oCommand.sId;
        string sOwner = reservedReason(k);
        if (sOwner.Length > 0 && !lsAllowedOverrides.Contains(k))
            lsProblems.Add(friendlyKey(k) + " (" + oCommand.sId + "): " + sOwner);
        return true;
    }

    // findCommand: the command a key runs in a context, or null.
    public static Command findCommand(string sContext, Keys k) {
        Dictionary<Keys, string> dKeys;
        string sId;
        if (dContextKeys.TryGetValue(sContext, out dKeys) && dKeys.TryGetValue(k, out sId)) return dCommands[sId];
        return null;
    }

    public static Command commandById(string sId) {
        Command oCommand;
        if (sId != null && dCommands.TryGetValue(sId, out oCommand)) return oCommand;
        return null;
    }

    // runCommand: the one way a command runs, from a key, a menu, the
    // Alternate Menu or a script. Availability is checked HERE, every time,
    // not only when the menu was last painted.
    public static bool runCommand(Command oCommand) {
        if (oCommand == null) return false;
        string sWhy = oCommand.unavailableReason();
        if (sWhy.Length > 0) {
            Say.sayForced(oCommand.sName + " is unavailable: " + sWhy);
            Log.info("command refused: " + oCommand.sId + ": " + sWhy);
            return true;
        }
        Log.info("command: " + oCommand.sId);
        try {
            if (oCommand.fRun != null) return oCommand.fRun();
            if (oCommand.oItem != null) { oCommand.oItem.PerformClick(); return true; }
        }
        catch (Exception oError) {
            Log.exception(oError);
            Say.sayForced(oCommand.sName + " failed. The log has why.");
        }
        return true;
    }

    public static bool runCommand(string sId) {
        return runCommand(commandById(sId));
    }

    // describe: what the Key Describer says for a key.
    public static string describe(Keys k, Command oCommand) {
        if (oCommand == null) return friendlyKey(k) + ". No command is bound to this key here.";
        StringBuilder sb = new StringBuilder();
        sb.Append(oCommand.sName).Append(". ").Append(friendlyKey(k)).Append(". ");
        if (oCommand.sSummary.Length > 0) sb.Append(oCommand.sSummary.TrimEnd('.')).Append(".");
        if (oCommand.sContext != sAnywhere) sb.Append(" In the ").Append(oCommand.sContext).Append(" only.");
        string sWhy = oCommand.unavailableReason();
        if (sWhy.Length > 0) sb.Append(" Unavailable now: ").Append(sWhy);
        return sb.ToString();
    }

    // ------------------------------------------------------------- routing

    [DllImport("user32.dll")]
    private static extern IntPtr GetFocus();

    // focusedControl: the control with keyboard focus, wherever it is nested.
    public static Control focusedControl() {
        try {
            IntPtr hFocus = GetFocus();
            if (hFocus == IntPtr.Zero) return null;
            return Control.FromChildHandle(hFocus);
        }
        catch (Exception) {
            return null;
        }
    }

    // Text boxes an app routes its own keys from (EdSharp's document), and
    // lists whose Shift+letter keys are commands (the DbDo grid, the FileDir
    // list). Held weakly in effect: a control is dropped when it is disposed.
    private static List<Control> lsEditors = new List<Control>();
    private static List<Control> lsManagedLists = new List<Control>();

    public static bool markEditor(Control ctl) {
        if (ctl == null || lsEditors.Contains(ctl)) return false;
        lsEditors.Add(ctl);
        ctl.Disposed += delegate(object oSender, EventArgs evArgs) { lsEditors.Remove(ctl); };
        return true;
    }

    // manageList: Shift+letter runs this list's commands, and a ListBox gets
    // typed-sequence navigation (a ListView already has it from Windows).
    public static bool manageList(Control ctl) {
        if (ctl == null || lsManagedLists.Contains(ctl)) return false;
        lsManagedLists.Add(ctl);
        ctl.Disposed += delegate(object oSender, EventArgs evArgs) { lsManagedLists.Remove(ctl); };
        ListBox lb = ctl as ListBox;
        if (lb != null) attachTypeAhead(lb);
        return true;
    }

    public static string controlKind(Control ctl) {
        if (ctl == null) return "";
        if (ctl is TextBoxBase) return sTextContext;
        ComboBox cbo = ctl as ComboBox;
        if (cbo != null && cbo.DropDownStyle != ComboBoxStyle.DropDownList) return sTextContext;
        if (ctl is UpDownBase) return sTextContext;
        if (ctl.GetType().Name.IndexOf("EditingControl", StringComparison.Ordinal) >= 0) return sTextContext;
        if (ctl is ListBox || ctl is ListView || ctl is DataGridView || ctl is TreeView) return sListContext;
        return "";
    }

    // isTypingKey: a key a text box needs for typing or editing.
    public static bool isTypingKey(Keys keyData) {
        Keys kCode = keyData & Keys.KeyCode;
        bool bControl = (keyData & Keys.Control) == Keys.Control;
        bool bAlt = (keyData & Keys.Alt) == Keys.Alt;
        if (bAlt) return false;
        if (kCode >= Keys.F1 && kCode <= Keys.F24) return false;
        if (kCode == Keys.Escape) return false;
        if (bControl) {
            // Windows' own editing chords: select all, copy, cut, paste,
            // undo, redo, word and document movement and deletion.
            switch (kCode) {
                case Keys.A: case Keys.C: case Keys.V: case Keys.X: case Keys.Y: case Keys.Z:
                case Keys.Insert: case Keys.Delete: case Keys.Back:
                case Keys.Left: case Keys.Right: case Keys.Up: case Keys.Down:
                case Keys.Home: case Keys.End:
                    return true;
                default:
                    return false;
            }
        }
        // No Control, no Alt: every printable key and every editing key.
        return true;
    }

    private static bool isLetterOrDigit(Keys kCode) {
        return (kCode >= Keys.A && kCode <= Keys.Z) || (kCode >= Keys.D0 && kCode <= Keys.D9)
            || (kCode >= Keys.NumPad0 && kCode <= Keys.NumPad9);
    }

    private static bool isModifierOnly(Keys keyData) {
        Keys kCode = keyData & Keys.KeyCode;
        return kCode == Keys.None || kCode == Keys.ShiftKey || kCode == Keys.ControlKey || kCode == Keys.Menu
            || kCode == Keys.LShiftKey || kCode == Keys.RShiftKey || kCode == Keys.LControlKey
            || kCode == Keys.RControlKey || kCode == Keys.LMenu || kCode == Keys.RMenu
            || kCode == Keys.LWin || kCode == Keys.RWin;
    }

    // route: decide what a key does in a Homer window. Call it first in the
    // window's ProcessCmdKey, and return true when it does. The message lets
    // a held-down key be told from a deliberate second press.
    // A key unhandled in a child window travels on to the frame, which routes
    // it again. The same Windows message is recognized and answered as before,
    // so one keystroke is never counted as two presses.
    private static IntPtr hLastWindow = IntPtr.Zero;
    private static IntPtr iLastWParam = IntPtr.Zero;
    private static IntPtr iLastLParam = IntPtr.Zero;
    private static int iLastMessageTick = 0;
    private static bool bLastResult = false;

    public static bool route(Form oWindow, ref Message msg, Keys keyData) {
        int iNow = Environment.TickCount;
        if (msg.HWnd == hLastWindow && msg.WParam == iLastWParam && msg.LParam == iLastLParam
            && unchecked(iNow - iLastMessageTick) >= 0 && unchecked(iNow - iLastMessageTick) < 50) {
            return bLastResult;
        }
        bool bAutoRepeat = false;
        try { bAutoRepeat = (msg.LParam.ToInt64() & 0x40000000L) != 0; } catch (Exception) { }
        hLastWindow = msg.HWnd;
        iLastWParam = msg.WParam;
        iLastLParam = msg.LParam;
        iLastMessageTick = iNow;
        bLastResult = false;
        bLastResult = route(oWindow, keyData, bAutoRepeat);
        return bLastResult;
    }

    public static bool route(Form oWindow, Keys keyData, bool bAutoRepeat) {
        if (isModifierOnly(keyData)) return false;
        Control oFocus = focusedControl();
        string sKind = controlKind(oFocus);
        Keys kCode = keyData & Keys.KeyCode;
        bool bShiftOnly = (keyData & Keys.Modifiers) == Keys.Shift;
        bool bNoModifier = (keyData & Keys.Modifiers) == Keys.None;
        bool bEditor = sKind == sTextContext && lsEditors.Contains(oFocus);
        bool bManagedList = sKind == sListContext && lsManagedLists.Contains(oFocus);

        Command oCommand = null;
        if (bEditor) oCommand = findCommand(sTextContext, keyData);
        if (oCommand == null && bManagedList) oCommand = findCommand(sListContext, keyData);
        bool bTypingInText = sKind == sTextContext && isTypingKey(keyData);
        bool bTypingInList = sKind == sListContext && bNoModifier && isLetterOrDigit(kCode);
        if (oCommand == null && !(bTypingInText && !bEditor) && !bTypingInList) oCommand = findCommand(sAnywhere, keyData);
        // A plain or shifted key in an unmarked text box always types.
        if (sKind == sTextContext && !bEditor && bTypingInText) oCommand = null;

        notePress(keyData, oWindow, bAutoRepeat);

        if (bKeyDescriber) {
            if (oCommand != null && oCommand.sId == "keyDescriberToggle") return runCommand(oCommand);
            if (bTypingInText && !bEditor && oCommand == null) return false;
            Say.sayForced(describe(keyData, oCommand));
            return true;
        }

        if (oCommand != null) return runCommand(oCommand);

        // THE LIST LAYER ALWAYS ANSWERS: a question that meets silence cannot
        // be told from a key that did not register.
        if (bManagedList && bShiftOnly && kCode >= Keys.A && kCode <= Keys.Z) {
            Say.sayForced("Shift+" + kCode.ToString() + ": no command on this key");
            return true;
        }
        return false;
    }

    // ------------------------------------------------------------- presses

    // iPressCount: 1 for a first press, 2 for the same key again within the
    // Windows double-click time in the same window, and so on. A key held
    // down is not a second press. Read it from inside a command.
    public static int iPressCount = 1;
    private static Keys keyLast = Keys.None;
    private static int iTickLast = 0;
    private static object oWindowLast = null;

    public static int notePress(Keys keyData, object oWindow, bool bAutoRepeat) {
        int iNow = Environment.TickCount;
        if (bAutoRepeat) {
            iPressCount = 1;
        }
        else if (keyData == keyLast && object.ReferenceEquals(oWindow, oWindowLast)
                 && unchecked(iNow - iTickLast) >= 0 && unchecked(iNow - iTickLast) <= SystemInformation.DoubleClickTime) {
            iPressCount++;
        }
        else {
            iPressCount = 1;
        }
        keyLast = keyData;
        iTickLast = iNow;
        oWindowLast = oWindow;
        return iPressCount;
    }

    // answer: what every Say command calls. The first press speaks the parts
    // as separate utterances, at once. A quick second press shows the same
    // information in a read-only window, where the screen reader can review,
    // spell and copy it; Escape returns to where you were.
    public static bool answer(string sTitle, params string[] aParts) {
        if (aParts == null) aParts = new string[0];
        if (iPressCount >= 2) {
            HelpDialog.show(Form.ActiveForm, sTitle, string.Join("\r\n", aParts));
            iPressCount = 1;
            return true;
        }
        Say.say(aParts);
        return true;
    }

    // ------------------------------------------------------------- again

    // The last input of an asking command (Go to, Jump, a search), kept per
    // window, so Alt plus the same letter can repeat it without asking. A
    // pair is registered by the app; none is assumed.
    private static Dictionary<string, string> dLastInput = new Dictionary<string, string>();
    private static Dictionary<object, string> dLastSearch = new Dictionary<object, string>();

    private static string inputKey(string sId, object oTarget) {
        int iTarget = oTarget == null ? 0 : System.Runtime.CompilerServices.RuntimeHelpers.GetHashCode(oTarget);
        return sId + "|" + iTarget.ToString();
    }

    public static bool rememberInput(string sId, object oTarget, string sValue) {
        dLastInput[inputKey(sId, oTarget)] = sValue == null ? "" : sValue;
        return true;
    }

    public static string recallInput(string sId, object oTarget) {
        string sValue;
        return dLastInput.TryGetValue(inputKey(sId, oTarget), out sValue) ? sValue : "";
    }

    // The search F3 and Shift+F3 repeat in a window: whichever registered
    // search ran last there. A command that is not a search never sets it.
    public static bool setLastSearch(object oTarget, string sSearchId) {
        if (oTarget != null) dLastSearch[oTarget] = sSearchId;
        return true;
    }

    public static string lastSearch(object oTarget) {
        string sId;
        return oTarget != null && dLastSearch.TryGetValue(oTarget, out sId) ? sId : "";
    }

    // forgetTarget: a window has closed; its repeat and search state go with it.
    public static bool forgetTarget(object oTarget) {
        if (oTarget == null) return false;
        dLastSearch.Remove(oTarget);
        string sSuffix = "|" + System.Runtime.CompilerServices.RuntimeHelpers.GetHashCode(oTarget).ToString();
        List<string> lsGone = new List<string>();
        foreach (string sKey in dLastInput.Keys) if (sKey.EndsWith(sSuffix)) lsGone.Add(sKey);
        foreach (string sKey in lsGone) dLastInput.Remove(sKey);
        if (object.ReferenceEquals(oWindowLast, oTarget)) oWindowLast = null;
        return true;
    }

    // ------------------------------------------------------------- typing in lists

    // A ListBox moves by the first letter only. This lets a person type the
    // start of an item -- "gra" for grapes -- within a second, as a ListView
    // and Windows Explorer allow.
    private static void attachTypeAhead(ListBox lb) {
        StringBuilder sbTyped = new StringBuilder();
        int[] aiLast = new int[] { 0 };
        lb.KeyPress += delegate(object oSender, KeyPressEventArgs evKey) {
            if (char.IsControl(evKey.KeyChar)) return;
            int iNow = Environment.TickCount;
            if (unchecked(iNow - aiLast[0]) > 1000) sbTyped.Length = 0;
            aiLast[0] = iNow;
            sbTyped.Append(evKey.KeyChar);
            string sTyped = sbTyped.ToString();
            int iCount = lb.Items.Count;
            if (iCount == 0) return;
            // One letter steps to the next match; a longer start stays put if
            // the current item still matches it.
            int iStart = lb.SelectedIndex < 0 ? 0 : lb.SelectedIndex + (sTyped.Length == 1 ? 1 : 0);
            for (int i = 0; i < iCount; i++) {
                int iTry = (iStart + i) % iCount;
                string sItem = ("" + lb.Items[iTry]).TrimStart();
                if (sItem.StartsWith(sTyped, StringComparison.CurrentCultureIgnoreCase)) {
                    lb.SelectedIndex = iTry;
                    break;
                }
            }
            evKey.Handled = true;
        };
    }

    // ------------------------------------------------------------- key names

    // parseKeys: "Shift+R or F2" -> two keys. Screen reader keys (JAWS+...,
    // NVDA+...) belong in the screen reader's own key map and are skipped
    // here; a key Windows has no code for is reported, not guessed.
    public static List<Keys> parseKeys(string sKeys, string sForName) {
        List<Keys> lsKeys = new List<Keys>();
        if (string.IsNullOrEmpty(sKeys)) return lsKeys;
        string[] aParts = sKeys.Split(new string[] { " or ", ", or ", "," }, StringSplitOptions.RemoveEmptyEntries);
        foreach (string sPart in aParts) {
            string sKey = sPart.Trim();
            if (sKey.Length == 0 || sKey.Equals("None", StringComparison.OrdinalIgnoreCase)) continue;
            if (sKey.IndexOf("JAWS", StringComparison.OrdinalIgnoreCase) >= 0
                || sKey.IndexOf("NVDA", StringComparison.OrdinalIgnoreCase) >= 0) continue;
            Keys k = (Keys)KeyName.toWinFormsKeys(sKey);
            if (k == Keys.None) {
                lsProblems.Add("The key " + sKey + " for " + sForName + " has no Windows code.");
                continue;
            }
            if (!lsKeys.Contains(k)) lsKeys.Add(k);
        }
        return lsKeys;
    }

    // friendlyKey: the Homer name of a key, as JAWS writes it -- modifiers in
    // alphabetical order, Control spelled out, Accent, BackSlash, SemiColon.
    public static string friendlyKey(Keys key) {
        Keys keyBase = key & ~Keys.Modifiers;
        string sBase = baseKeyLabel(keyBase);
        if (sBase.Length == 0) return "";
        StringBuilder sb = new StringBuilder();
        if ((key & Keys.Alt) == Keys.Alt) sb.Append("Alt+");
        if ((key & Keys.Control) == Keys.Control) sb.Append("Control+");
        if ((key & Keys.Shift) == Keys.Shift) sb.Append("Shift+");
        sb.Append(sBase);
        return sb.ToString();
    }

    private static string baseKeyLabel(Keys keyBase) {
        if (keyBase == Keys.None) return "";
        if (keyBase >= Keys.A && keyBase <= Keys.Z) return keyBase.ToString();
        if (keyBase >= Keys.D0 && keyBase <= Keys.D9) return ((int)(keyBase - Keys.D0)).ToString();
        if (keyBase >= Keys.NumPad0 && keyBase <= Keys.NumPad9) return "NumPad" + ((int)(keyBase - Keys.NumPad0)).ToString();
        switch (keyBase) {
            case Keys.OemQuotes: return "Apostrophe";
            case Keys.OemSemicolon: return "SemiColon";
            case Keys.OemQuestion: return "Slash";
            case Keys.OemPeriod: return "Period";
            case Keys.Oemcomma: return "Comma";
            case Keys.OemMinus: return "Dash";
            case Keys.Oemplus: return "Equals";
            case Keys.OemOpenBrackets: return "LeftBracket";
            case Keys.OemCloseBrackets: return "RightBracket";
            case Keys.OemPipe: return "BackSlash";
            case Keys.OemBackslash: return "BackSlash";
            case Keys.Oemtilde: return "Accent";
            case Keys.Back: return "Backspace";
            case Keys.Return: return "Enter";
            case Keys.Escape: return "Escape";
            case Keys.Space: return "Space";
            case Keys.Tab: return "Tab";
            case Keys.Up: return "UpArrow";
            case Keys.Down: return "DownArrow";
            case Keys.Left: return "LeftArrow";
            case Keys.Right: return "RightArrow";
            case Keys.PageUp: return "PageUp";
            case Keys.PageDown: return "PageDown";
            case Keys.Home: return "Home";
            case Keys.End: return "End";
            case Keys.Insert: return "Insert";
            case Keys.Delete: return "Delete";
            case Keys.PrintScreen: return "PrintScreen";
            case Keys.CapsLock: return "CapsLock";
            case Keys.NumLock: return "NumLock";
            case Keys.Scroll: return "ScrollLock";
            case Keys.Clear: return "NumPad5";
            case Keys.Add: return "NumPadPlus";
            case Keys.Subtract: return "NumPadMinus";
            case Keys.Multiply: return "NumPadStar";
            case Keys.Divide: return "NumPadSlash";
            case Keys.Decimal: return "NumPadDelete";
        }
        return keyBase.ToString();
    }

    // ------------------------------------------------------------- owned keys

    // Keys that Windows or a screen reader takes before an app sees them, or
    // that mean one thing everywhere. The authoritative list, with each
    // entry's owner, context and allowed disposition, is the kit's
    // data\KeyOwnership.inix; scripts\checkKeys checks this table against it.
    // Only the entries that should stop a NEW binding are here: conventions
    // such as Control+C are kept by an app on purpose, and table or
    // laptop-layout keys are tested in their real control instead.
    private static readonly string[] aReserved = new string[] {
        "Alt+Escape|Windows: cycles windows",
        "Alt+Space|Windows: the window's system menu",
        "Alt+Dash|Windows: a document window's system menu",
        "Alt+Tab|Windows: switches apps",
        "Control+Escape|Windows: Start",
        "Control+Shift+Escape|Windows: Task Manager",
        "Control+Shift+0|Windows: a keyboard-layout hotkey on many machines with more than one language",
        "Alt+Delete|JAWS: Say Active Cursor -- override only through the app's JAWS allowlist",
        "Alt+Control+PageUp|JAWS: voice rate faster",
        "Alt+Control+PageDown|JAWS: voice rate slower",
        "Alt+Shift+UpArrow|JAWS: mouse up",
        "Alt+Shift+DownArrow|JAWS: mouse down",
        "Alt+Shift+LeftArrow|JAWS: mouse left",
        "Alt+Shift+RightArrow|JAWS: mouse right",
        "Shift+NumPad5|JAWS: says the current control's hotkey",
        "Control+Shift+F11|JAWS: system tray contents"
    };

    private static Dictionary<Keys, string> dReserved = null;

    // Keys an app overrides on purpose, through its JAWS key map allowlist.
    // Alt+Delete is the suite's (your ruling of 18 October 2026): the JAWS
    // default reports pixel coordinates, which mean nothing in a Homer list.
    public static List<Keys> lsAllowedOverrides = new List<Keys>(new Keys[] { Keys.Alt | Keys.Delete });

    public static string reservedReason(Keys k) {
        if (dReserved == null) {
            dReserved = new Dictionary<Keys, string>();
            foreach (string sEntry in aReserved) {
                string[] a = sEntry.Split('|');
                Keys kReserved = (Keys)KeyName.toWinFormsKeys(a[0]);
                if (kReserved != Keys.None) dReserved[kReserved] = a[1];
            }
        }
        string sWhy;
        return dReserved.TryGetValue(k, out sWhy) ? sWhy : "";
    }

    // jawsPassThroughLines: the [Common Keys] lines an app's .jkm needs so
    // that JAWS hands its allowlisted keys to the app.
    public static List<string> jawsPassThroughLines() {
        List<string> lsLines = new List<string>();
        foreach (Keys k in lsAllowedOverrides) {
            foreach (string sId in lsCommandOrder) {
                if (dCommands[sId].lsKeys.Contains(k)) {
                    lsLines.Add(friendlyKey(k) + "=TypeCurrentScriptKey");
                    break;
                }
            }
        }
        return lsLines;
    }

    // ------------------------------------------------------------- exports

    // exportInix: every command as the program actually declared it, for the
    // checker and the hotkey document. One section per command.
    public static bool exportInix(string sPath, string sAppName) {
        StringBuilder sb = new StringBuilder();
        sb.Append("; Commands exported by ").Append(sAppName).Append(" itself, ").Append(DateTime.Now.ToString("yyyy-MM-dd HH:mm")).Append("\r\n");
        sb.Append("; Written by KeyMap.exportInix; read by scripts\\checkKeys in the kit.\r\n\r\n");
        sb.Append("[Export]\r\napp=").Append(sAppName).Append("\r\nschema=1\r\n");
        foreach (string sId in lsCommandOrder) {
            Command c = dCommands[sId];
            sb.Append("\r\n[Command ").Append(c.sId).Append("]\r\n");
            sb.Append("name=").Append(c.sName).Append("\r\n");
            sb.Append("keys=").Append(c.keysText()).Append("\r\n");
            sb.Append("context=").Append(c.sContext).Append("\r\n");
            sb.Append("menu=").Append(c.sMenu).Append("\r\n");
            sb.Append("summary=").Append(c.sSummary.Replace("\r", " ").Replace("\n", " ")).Append("\r\n");
            if (c.sRepeat.Length > 0) sb.Append("repeat=").Append(c.sRepeat).Append("\r\n");
            if (c.bOpensDialog) sb.Append("opensDialog=yes\r\n");
        }
        if (lsProblems.Count > 0) {
            sb.Append("\r\n[Problems]\r\n");
            for (int i = 0; i < lsProblems.Count; i++) sb.Append("problem").Append((i + 1).ToString()).Append("=").Append(lsProblems[i]).Append("\r\n");
        }
        try {
            File.WriteAllText(sPath, sb.ToString(), new UTF8Encoding(true));
            return true;
        }
        catch (Exception oError) {
            Log.exception(oError);
            return false;
        }
    }

    // hotkeySummary: command, keys and summary, one per line, sorted by name.
    public static string hotkeySummary() {
        List<Command> lsSorted = new List<Command>();
        foreach (string sId in lsCommandOrder) lsSorted.Add(dCommands[sId]);
        lsSorted.Sort(delegate(Command a, Command b) { return string.Compare(a.sName, b.sName, StringComparison.OrdinalIgnoreCase); });
        StringBuilder sb = new StringBuilder();
        foreach (Command c in lsSorted) {
            sb.Append(c.sName).Append(", ");
            sb.Append(c.lsKeys.Count > 0 ? c.keysText() : "no key");
            if (c.sContext != sAnywhere) sb.Append(" (").Append(c.sContext).Append(")");
            if (c.sSummary.Length > 0) sb.Append(": ").Append(c.sSummary);
            sb.Append("\r\n");
        }
        // Commands registered the old way, which have no Command record.
        foreach (KeyValuePair<string, Keys> kv in dCommandToKey) {
            if (dCommands.ContainsKey(toId(kv.Key))) continue;
            sb.Append(kv.Key).Append(", ").Append(kv.Value == Keys.None ? "no key" : friendlyKey(kv.Value));
            string sSummary = getSummary(kv.Key);
            if (sSummary.Length > 0) sb.Append(": ").Append(sSummary);
            sb.Append("\r\n");
        }
        return sb.ToString();
    }

    // ============================================================= the old members
    //
    // Kept for EdSharp and FileDir, which compile this file and call them
    // today. They write the same tables the new members read.

    public static Dictionary<string, Keys> dCommandToKey =
        new Dictionary<string, Keys>(StringComparer.OrdinalIgnoreCase);
    public static Dictionary<Keys, ToolStripMenuItem> dKeyToMenu =
        new Dictionary<Keys, ToolStripMenuItem>();
    public static Dictionary<ToolStripMenuItem, string> dMenuToCommand =
        new Dictionary<ToolStripMenuItem, string>();
    public static Dictionary<string, string> dCommandToSummary =
        new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
    public static Dictionary<string, string> dCommandToDescription =
        new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
    public static Dictionary<string, string> dCommandToContext =
        new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
    public static List<string> lsConflicts = new List<string>();

    // Key Describer mode: a key says what it would do instead of doing it.
    public static bool bKeyDescriber = false;

    public class KeyBinding {
        public Keys keyData;
        public string sCommand, sContext, sSummary, sDescription;
        public KeyBinding(string sContextIn, string sCommandIn, string sSummaryIn, string sDescriptionIn, Keys keyDataIn) {
            keyData = keyDataIn;
            sCommand = sCommandIn;
            sContext = string.IsNullOrEmpty(sContextIn) ? sGlobalContext : sContextIn;
            sSummary = sSummaryIn == null ? "" : sSummaryIn;
            sDescription = sDescriptionIn == null ? "" : sDescriptionIn;
        }
        public bool bUnbound { get { return keyData == Keys.None; } }
    }

    public static List<KeyBinding> lsExtraBindings = new List<KeyBinding>();

    public static void register(string sCommand, Keys keyData, ToolStripMenuItem menuItem, string sContext) {
        if (string.IsNullOrEmpty(sCommand)) return;
        dCommandToKey[sCommand] = keyData;
        if (menuItem != null) dMenuToCommand[menuItem] = sCommand;
        if (menuItem != null && keyData != Keys.None) {
            if (dKeyToMenu.ContainsKey(keyData)) { if (!lsConflicts.Contains(sCommand)) lsConflicts.Add(sCommand); }
            else dKeyToMenu[keyData] = menuItem;
        }
        dCommandToContext[sCommand] = string.IsNullOrEmpty(sContext) ? sGlobalContext : sContext;
    }

    public static void addBinding(KeyBinding binding) { if (binding != null) lsExtraBindings.Add(binding); }

    public static void setSummary(string sCommand, string sSummary) {
        if (string.IsNullOrEmpty(sCommand)) return;
        dCommandToSummary[sCommand] = sSummary == null ? "" : sSummary;
        Command c = commandById(toId(sCommand));
        if (c != null) c.sSummary = sSummary == null ? "" : sSummary;
    }

    public static string getSummary(string sCommand) {
        string sValue;
        if (sCommand != null && dCommandToSummary.TryGetValue(sCommand, out sValue)) return sValue;
        return "";
    }

    public static void setDescription(string sCommand, string sDescription) {
        if (string.IsNullOrEmpty(sCommand)) return;
        dCommandToDescription[sCommand] = sDescription == null ? "" : sDescription;
        Command c = commandById(toId(sCommand));
        if (c != null) c.sDescription = sDescription == null ? "" : sDescription;
    }

    public static string getDescription(string sCommand) {
        string sValue;
        if (sCommand != null && dCommandToDescription.TryGetValue(sCommand, out sValue)) return sValue;
        return "";
    }

    public static string getContext(string sCommand) {
        string sValue;
        if (sCommand != null && dCommandToContext.TryGetValue(sCommand, out sValue)) return sValue;
        return sGlobalContext;
    }

    public static Keys getKey(string sCommand) {
        Keys keyData;
        if (sCommand != null && dCommandToKey.TryGetValue(sCommand, out keyData)) return keyData;
        return Keys.None;
    }

    public static string commandForKey(Keys keyData) {
        ToolStripMenuItem menuItem;
        if (dKeyToMenu.TryGetValue(keyData, out menuItem)) {
            string sCommand;
            if (dMenuToCommand.TryGetValue(menuItem, out sCommand)) return sCommand;
        }
        Command c = findCommand(sAnywhere, keyData);
        return c == null ? "" : c.sName;
    }

    public static List<KeyBinding> bindings() {
        List<KeyBinding> lsRows = new List<KeyBinding>();
        foreach (KeyValuePair<string, Keys> pair in dCommandToKey)
            lsRows.Add(new KeyBinding(getContext(pair.Key), pair.Key, getSummary(pair.Key), getDescription(pair.Key), pair.Value));
        foreach (KeyBinding binding in lsExtraBindings) lsRows.Add(binding);
        return lsRows;
    }

    public static List<string> commands() { return new List<string>(dCommandToKey.Keys); }
}

} // namespace Homer (KeyMap.cs)
