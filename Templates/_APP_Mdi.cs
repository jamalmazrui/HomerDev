// _APP_.cs -- a Homer MDI app: one frame, a window for each thing you work on.
//
// This is the HomerDev starter for a multiple-window app, the shape of DbDo,
// EdSharp and FileDir. "newHomerApp _APP_ --mdi" wrote it with your app's name
// in place. It compiles and runs as it stands: File, New Window opens a window
// holding a list of items you can add to, and every key the Homer suite shares
// already works -- F4 for the window list, Control+F1 for the Key Describer,
// Alt+F10 for the Alternate Menu, F1 for the guide and the rest.
//
// The worked example with every feature is Templates\samples\FruitBasketMdiCs.cs
// in the kit; the guide is help\MdiFramework.md there.
//
// ------------------------------------------------------------------ AI NOTE
// If you are an AI asked to turn this into a working program, keep these rules.
//
//   * DECLARE, DON'T HANDLE KEYS. Every command is one addCommand line: a
//     caption with its ampersand letter, its keys in Homer spelling
//     ("Control+Shift+A", "Shift+R or F2", "" for none), a one-line summary,
//     and the function that does the work. Never write a KeyDown handler or
//     a ProcessCmdKey override: the kit's router decides where every key goes,
//     keeps typing in text boxes, and keeps first-letter navigation in lists.
//   * A HOTKEY'S LETTER IS THE FIRST LETTER OF A WORD IN ITS NAME, never a
//     letter from the middle of a word. Never bind Alt+Control with a letter,
//     digit, function key or punctuation: that space belongs to Windows
//     desktop shortcuts. KeyMap logs any key Windows or a screen reader owns.
//   * THE SUITE'S SHARED KEYS ARE TAKEN BY THE FRAME: F1, Shift+F1, Alt+F1,
//     Control+F1, Control+Shift+F1, Alt+Shift+F1, F4, Shift+F4, Control+F4,
//     Control+Shift+F4, Control+Tab, Alt+F10, Alt+Shift+H, Alt+Shift+E,
//     Control+Shift+I, Alt+Apostrophe, Alt+SemiColon, F11, Control+F12.
//   * A COMMAND THAT CANNOT RUN SAYS WHY: set its fUnavailable to a function
//     returning "" when it can run, or the reason when it cannot.
//   * SAY COMMANDS USE KeyMap.answer(sTitle, part, part...): one press speaks
//     the parts, a quick second press shows them in a window to review.
//   * A LIST WHERE SHIFT PLUS A LETTER RUNS COMMANDS is passed to manageList,
//     and those commands are declared with KeyMap.sListContext.
//   * THE TITLE RULE: the frame is titled with the app name only; a window
//     with what it shows only (setTitle), never the app name again.
//   * Speak only what the screen reader cannot know. It already announces
//     the window title and the focused control; do not repeat either.
//   * Camel Type: sString, iInteger, bBoolean, lsList, dDictionary, oObject;
//     lowerCamel methods; functions, not subprocedures; double quotes; no c_
//     prefix on constants. C# 5 syntax in this file keeps it buildable with
//     the compiler that comes with Windows.
// ---------------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Windows.Forms;
using Homer;

namespace _APP_
{

public static class Program
{

private static readonly string sAppName = "_APP_";

public class appFrame : MdiFrame
{
    private int iWindows = 0;

    public appFrame() : base(sAppName)
    {
        addMenu("&File");
        addCommand("&New Window", "Control+N", "Open another window.", newWindow);
        addCommand("E&xit", "Alt+F4", "Close every window and leave.", delegate() { this.Close(); return true; });

        addMenu("&Edit");
        KeyMap.Command oAdd = addCommand("&Add Item", "Control+Shift+A", "Put what is in the item field into the list.",
            delegate() { appWindow w = this.ActiveMdiChild as appWindow; return w == null || w.addItem(); });
        oAdd.fUnavailable = delegate() { return this.ActiveMdiChild == null ? "no window is open" : ""; };

        addMenu("&Query");
        addCommand("Say &Position", "Alt+Delete", "Say which item you are on, of how many, and how far through.",
            delegate() { appWindow w = this.ActiveMdiChild as appWindow; return w == null || w.sayPosition(); }).sRepeat = "review";

        finishMenus();
        newWindow();
    }

    public bool newWindow()
    {
        iWindows++;
        appWindow w = new appWindow(this, "Window " + iWindows.ToString());
        w.Show();
        return true;
    }
}

public class appWindow : MdiChild
{
    private ListBox lbItems;
    private TextBox txtItem;

    public appWindow(MdiFrame frmParent, string sName) : base(frmParent)
    {
        txtItem = lbc.addInputBox("&Item:", "", "Type an item, then press Control+Shift+A to add it.");
        lbItems = lbc.addPickBox("&List:", new List<string>(), "", "The items in this window.");
        finishLayout();
        manageList(lbItems);
        setTitle(sName, "empty");
        txtItem.Focus();
    }

    public bool addItem()
    {
        string sItem = txtItem.Text.Trim();
        if (sItem == "") { Say.sayForced("Type an item first"); txtItem.Focus(); return true; }
        lbItems.Items.Add(sItem);
        lbItems.SelectedIndex = lbItems.Items.Count - 1;
        txtItem.Text = "";
        setTitle(subject, lbItems.Items.Count == 1 ? "1 item" : lbItems.Items.Count.ToString() + " items");
        Say.say(sItem + " added");
        return true;
    }

    public bool sayPosition()
    {
        int iCount = lbItems.Items.Count;
        if (iCount == 0) return KeyMap.answer("Position", "0 items");
        int iItem = lbItems.SelectedIndex;
        if (iItem < 0) return KeyMap.answer("Position", "No item is selected");
        int iPercent = (int)Math.Round(100.0 * (iItem + 1) / iCount);
        return KeyMap.answer("Position", "Item " + (iItem + 1).ToString() + " of " + iCount.ToString(), iPercent.ToString() + " percent");
    }
}

[STAThread]
public static int Main(string[] aArguments)
{
    Application.EnableVisualStyles();
    Application.SetCompatibleTextRenderingDefault(false);
    Paths.start(sAppName);
    Log.start(sAppName);
    try
    {
        int iCode = MdiFrame.runOrExport(new appFrame());
        Log.close();
        return iCode;
    }
    catch (Exception oError)
    {
        Log.exception(oError);
        Log.close();
        throw;
    }
}

} // class Program

} // namespace _APP_
