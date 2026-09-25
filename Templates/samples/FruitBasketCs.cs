// FruitBasketCs.cs -- the fruit basket program on the Homer C# classes.
//
// THIS FILE AND Samples\FruitBasketPy.py ARE THE SAME PROGRAM.
// Open them side by side. Every section below is marked
//
//     // ---- BLOCK n: <title> ----
//
// and the block with the same number and title in the other file does the same
// job. The blocks do not line up line for line -- C# needs a class where Python
// needs none, Python needs no type on a variable -- but nothing appears in one
// that has no counterpart in the other, and the counterpart is named the same.
//
// THE SPECIFICATION, the teaching exercise among blind programmers since 2005:
// a window with a fruit field and an Add button, a basket list and a Delete
// button. Adding an empty field says so rather than adding nothing. Deleting
// with nothing selected says so too. After every action the focus lands where
// the next action starts.
//
// This version adds what the original could not: the basket survives being
// closed, the basket can be sorted, a report opens in a readable window, and
// every message a screen reader could not work out for itself is spoken.
//
// WHAT TO NOTICE. Nine decisions are marked DECISION 1 to DECISION 9 where they
// occur, and the same nine are marked in the Python file. Each is a decision a
// working program has to get right and that an AI will not make for you unless
// you ask for it.
//
// WHAT IS BORROWED RATHER THAN WRITTEN. Everything below arrives with the call
// that creates the control. None of it is in this file, which is the point of a
// kit, and all of it is in the Python file too:
//
//   IN THE FRUIT FIELD, because it is an Lbc text box:
//     Alt+C, Alt+X         append a copy or a cut to the clipboard
//     Alt+F8               read the whole field aloud
//     Control+C, Control+X copy or cut the CURRENT LINE with nothing selected
//     Control+D            delete the current line, speaking the next
//     Control+F8           copy the whole field
//     F8, Shift+F8         mark a selection in two keystrokes
//     Shift+F5             open the link, path or address under the cursor
//
//   IN THE BASKET, because it is an Lbc list:
//     Control+C            copy the item under the cursor
//     Control+J            search inside the list
//     F3, Shift+F3         repeat that search forwards and back
//
//   IN THE DIALOG ITSELF:
//     Alt+letter           any control with an ampersand in its label
//     Control+Enter        accept from anywhere, including a list or a memo
//     Escape               cancel
//     F1                   the Help window, built from the tips written below
//
// AND A LOG, from Homer.Log: one file per session in
// %LOCALAPPDATA%\FruitBasketCs\logs, holding the environment, every setting,
// and every error with its stack.
//
// Build with buildFruitBasketCs.cmd.

// ---- BLOCK 1: what this file needs ----
using System;
using System.Collections.Generic;
using System.IO;
using System.Windows.Forms;
using Homer;

namespace FruitBasketCs
{

public static class Program
{

// ---- BLOCK 2: names ----
//
// Constants carry c_ and their type letter, as Camel Type has it, and they sit
// together at the top where a reader can find them.
private const string c_sAppName = "FruitBasketCs";
private const string c_sSection = "Basket";
private const string c_sSettingsFile = "FruitBasketCs.inix";

// The two ways the basket can be ordered. Alphabetical, as every list in Homer
// code is unless another order is clearly more logical.
private static readonly string[] c_asSortOrders = { "added", "name" };

// The controls the handlers need after the dialog is built.
private static CheckBox cbSpeak;
private static ComboBox cboSort;
private static LbcDialog dlgFruit;
private static ListBox lbBasket;
private static TextBox txtFruit;

// ---- BLOCK 3: where the basket is kept ----
//
// %LOCALAPPDATA%\FruitBasketCs\configs\FruitBasketCs.inix, which is where the
// Homer layout puts a setting the program writes. Paths.configFile hands back
// the user's copy, making it from the one that shipped with the program the
// first time, so this file never has to know which case it is in.
//
// The letters are the point of that layout: configs, data, exec, jobs, logs,
// results, samples, temp and templates all start differently, so a screen
// reader user reaches any of them with one keystroke.
private static string settingsPath()
{
    return Paths.configFile(c_sSettingsFile);
}

// The settings file is .inix, which is .ini with the corners knocked off: a
// value may run over several lines and be kept exactly as written, and reading
// one setting is one call. InixCodec.readValue answers the default for a
// missing file, a missing section, a missing key and an empty value alike,
// because a caller asking for a setting wants an answer rather than four ways
// of saying no.
private static List<string> loadBasket()
{
    List<string> lsFruit = new List<string>();
    foreach (string sOne in InixCodec.readValue(settingsPath(), c_sSection, "Fruit", "").Split(','))
    {
        string sTrimmed = sOne.Trim();
        if (sTrimmed != "") lsFruit.Add(sTrimmed);
    }
    return lsFruit;
}

// DECISION 8: SAVE THE ANSWER THE MOMENT IT IS GIVEN, not at exit. A program
// that saves on the way out loses everything when it is killed, and the person
// who loses it is the one who just typed twenty fruits.
private static bool saveBasket()
{
    List<string> lsFruit = new List<string>();
    foreach (object oItem in lbBasket.Items) lsFruit.Add(("" + oItem).Trim());
    InixCodec.writeValue(settingsPath(), c_sSection, "Fruit",
                         string.Join(", ", lsFruit.ToArray()));
    InixCodec.writeValue(settingsPath(), c_sSection, "Sort", ("" + cboSort.SelectedItem));
    InixCodec.writeValue(settingsPath(), c_sSection, "Speak", cbSpeak.Checked ? "1" : "0");
    Log.info("Saved " + lbBasket.Items.Count + " to " + settingsPath());
    return true;
}

// ---- BLOCK 4: the dialog, built in the order it is read ----
private static int runDialog()
{
    // DECISION 1: WHICH LIBRARY. The controls below are ordinary Windows
    // controls -- the same edit box, list box and buttons every other program
    // uses, which is why every screen reader already knows them. What Lbc adds
    // is the arrangement: each control arrives with its label, its accessible
    // name and its place in the tab order already correct.
    //
    // Ask an AI for "a fruit basket window in C#" and you get a Form with
    // controls placed at pixel coordinates. It works, it looks right, and its
    // tab order is whatever order the controls happened to be created in.
    // Asking for it "on Homer Lbc" is the whole difference.
    using (LbcDialog dlg = new LbcDialog("Fruit Basket", null))
    {
        dlgFruit = dlg;
        // DECISION 2: ADD ORDER IS FOCUS ORDER. The order of the calls below is
        // the order a person tabs through the window, which is the order they
        // hear it in. There is no TabIndex anywhere in this file, and there
        // should be none in yours: when the order is wrong, move the call.
        //
        // DECISION 3: BANDS. A band puts controls on one row. Fruit and Add
        // belong together because Add acts on what was just typed; the basket
        // and Delete belong together for the same reason.
        //
        // DECISION 4: ACCESS KEYS. The ampersand before a letter is the whole
        // mechanism: the plain Windows API does the rest, with no keyboard code
        // at all. Close gets none, because Escape is already its key and a
        // letter it does not need is a letter another control may want.
        //
        // THE TIP is the third argument. It appears in the dialog's status line
        // when focus arrives, and again in the Help window, so the explanation
        // is written once and reaches a reader two ways.
        dlg.addBand();
        txtFruit = dlg.addInputBox("&Fruit:", "",
            "Type the name of a fruit, then press Enter or the Add button.");
        dlg.addButton("&Add", "Put what is in the fruit field into the basket.");
        dlg.endBand();

        // A pick box is a list with a label. Control+J searches inside it and
        // F3 repeats the search; Control+C copies the item under the cursor.
        // All three come from Lbc, and this file does nothing to get them.
        lbBasket = dlg.addPickBox("&Basket:", loadBasket(), "",
            "The fruit in the basket. Press Delete to remove the one you are on.");

        dlg.addBand();
        dlg.addButton("&Delete", "Take the selected fruit out of the basket.");
        dlg.addButton("&Report", "Show the whole basket in a window you can read line by line.");
        dlg.endBand();

        // A combo pick box offers a short list of legal values and refuses
        // anything else, which is what a setting wants. Type-ahead works, and a
        // screen reader announces each value as the arrow keys pass it.
        cboSort = dlg.addComboPickBox("&Sort by:", c_asSortOrders,
            InixCodec.readValue(settingsPath(), c_sSection, "Sort", "added"),
            "added keeps the basket in the order fruit went in; name sorts it alphabetically.");
        cboSort.SelectedIndexChanged += delegate(object oSender, EventArgs evArgs) { sortBasket(); };

        cbSpeak = dlg.addCheckBox("Spea&k each change",
            InixCodec.readValue(settingsPath(), c_sSection, "Speak", "1") == "1",
            "When this is off, the program stays silent and the screen reader does all the talking.");

        // ---- BLOCK 5: the buttons that act without closing ----
        //
        // A dialog's buttons normally end it. Add, Delete and Report do work
        // and leave the window open, and each language has one way of saying
        // so. In C# a button added with addButton is an ordinary button with an
        // ordinary Click handler, and only the buttons named in runWithButtons
        // close the dialog. In Python the dialog's own handler is given every
        // press and keeps the window open by answering False. Both files route
        // every button through one handleButton function, so the dispatch reads
        // the same in each.
        foreach (Control ctl in dlg.form.Controls) hookButtons(ctl);

        // DECISION 9: THE ESCAPE HATCH. Lbc wires Enter to the button that
        // means accept, which here would be Close -- right for a settings
        // dialog, wrong for this one, where Enter in the field should add the
        // fruit. dlg.form is the underlying Form, provided for exactly this:
        // the one thing the wrapper does not cover. Reach for it rarely, and
        // say why when you do.
        dlg.form.AcceptButton = (Button) dlg.findControl("Button_Add");

        Log.section("Dialog built");
        Log.keyValue("Sort order", "" + cboSort.SelectedItem);
        Log.keyValue("Speak changes", "" + cbSpeak.Checked);
        dlg.setInitialFocus(txtFruit);
        dlg.setStatusText(basketState());
        sortBasket();

        // Lbc adds a Help button of its own and places it rightmost, where
        // Windows puts one. F1 opens the same window. It lists every field with
        // its tip, so the tips written above are the help.
        dlg.runWithButtons(new string[] { "Close" });
    }
    return 0;
}

// Attach one handler to every button in the dialog, whatever the band. The
// handler reads the button's own caption, so adding a button needs no change
// here -- only a case in handleButton.
private static bool hookButtons(Control ctlParent)
{
    foreach (Control ctl in ctlParent.Controls)
    {
        Button btn = ctl as Button;
        if (btn != null)
            btn.Click += delegate(object oSender, EventArgs evArgs)
            { handleButton(("" + ((Button) oSender).Text).Replace("&", "")); };
        hookButtons(ctl);
    }
    return true;
}

// ---- BLOCK 6: one place that knows what every button does ----
//
// Returning false means "the window stays open", which is what Add, Delete and
// Report all want. Close is not here: Lbc's own button row ends the dialog.
private static bool handleButton(string sLabel)
{
    if (sLabel == "Add") return addFruit();
    if (sLabel == "Delete") return deleteFruit();
    if (sLabel == "Report") return showReport();
    return true;
}

// ---- BLOCK 7: what the screen reader cannot know ----
//
// DECISION 5: A screen reader announces the window title when the dialog opens
// and a control's name when focus arrives, so this program never says those.
// It says what the reader cannot work out: that a fruit went in, that one came
// out, how full the basket is now. Say.say reaches JAWS through its own
// interface, NVDA through its controller, and Narrator through a UI Automation
// notification, and this file does not have to know which is running.
private static bool sayChange(string sMessage)
{
    if (cbSpeak != null && !cbSpeak.Checked) return false;
    Say.say(sMessage);
    return true;
}

// DECISION 7: COUNTS THAT MATCH THEIR NOUNS. Util.stringPlural puts the number
// and the noun together and agrees them, so "1 fruit" is never "1 fruits". An
// empty basket is a real answer, said plainly, not an error and not silence.
//
// NOTE FOR THE READER WITH BOTH FILES OPEN: the C# helper returns the count and
// the noun together ("3 fruits"); the Python one returns only the noun
// ("fruits"). Same name, different shape, which is a wart rather than a design.
// Each file uses its own correctly.
private static string basketState()
{
    int iCount = lbBasket.Items.Count;
    if (iCount == 0) return "the basket is empty";
    return Util.stringPlural("fruit", iCount) + " in the basket";
}

// ---- BLOCK 8: add a fruit ----
private static bool addFruit()
{
    string sFruit = txtFruit.Text.Trim();
    if (sFruit == "")
    {
        Say.sayForced("Type a fruit first");
        txtFruit.Focus();
        return false;
    }
    Log.info("Adding " + sFruit);
    lbBasket.Items.Add(sFruit);
    lbBasket.SelectedIndex = lbBasket.Items.Count - 1;
    txtFruit.Text = "";
    sortBasket(sFruit);
    saveBasket();
    sayChange(sFruit + " added, " + basketState());

    // DECISION 6: WHERE THE FOCUS GOES. Back to the field, because the next
    // thing a person does after adding a fruit is add another. Leaving the
    // focus on the button makes them find their way back every time, and
    // finding your way back is what costs a screen reader user their afternoon.
    txtFruit.Focus();
    return false;
}

// ---- BLOCK 9: delete a fruit ----
private static bool deleteFruit()
{
    int iFruit = lbBasket.SelectedIndex;
    if (iFruit == -1)
    {
        Say.sayForced("No fruit is selected");
        lbBasket.Focus();
        return false;
    }
    string sFruit = ("" + lbBasket.Items[iFruit]).Trim();
    Log.info("Deleting " + sFruit + " from position " + iFruit);
    lbBasket.Items.RemoveAt(iFruit);

    // Select the neighbour, so the list still has somewhere to speak from. A
    // list with nothing selected says nothing, and a person who hears nothing
    // assumes the program has stopped.
    if (iFruit > lbBasket.Items.Count - 1) iFruit = lbBasket.Items.Count - 1;
    if (iFruit >= 0) lbBasket.SelectedIndex = iFruit;
    saveBasket();
    sayChange(sFruit + " deleted, " + basketState());
    lbBasket.Focus();
    return false;
}

// ---- BLOCK 10: sort the basket ----
//
// sortedIgnoringCase is Lbc's, and it sorts the way a person expects rather
// than the way a computer does: Apple and apple sit together instead of every
// capital letter coming first.
private static bool sortBasket()
{
    return sortBasket("");
}

private static bool sortBasket(string sKeep)
{
    if (("" + cboSort.SelectedItem) != "name")
    {
        showState();
        return false;
    }
    List<string> lsFruit = new List<string>();
    foreach (object oItem in lbBasket.Items) lsFruit.Add("" + oItem);
    List<string> lsSorted = LbcDialog.sortedIgnoringCase(lsFruit);
    lbBasket.Items.Clear();
    foreach (string sFruit in lsSorted) lbBasket.Items.Add(sFruit);
    if (lbBasket.Items.Count > 0)
    {
        int iKeep = (sKeep == "") ? 0 : lsSorted.IndexOf(sKeep);
        lbBasket.SelectedIndex = (iKeep < 0) ? 0 : iKeep;
    }
    showState();
    return true;
}

// ---- BLOCK 11: the report ----
//
// HelpDialog.show is Lbc's plain read-only window: a person arrows through it
// line by line, copies from it, and closes it with Escape. It is the same
// window the Help button uses, which is why a report does not need one of its
// own.
private static bool showReport()
{
    System.Text.StringBuilder sbReport = new System.Text.StringBuilder();
    sbReport.AppendLine("Fruit basket report");
    sbReport.AppendLine("");
    sbReport.AppendLine(basketState() + ".");
    sbReport.AppendLine("Sorted by " + ("" + cboSort.SelectedItem) + ".");
    sbReport.AppendLine("");
    int iNumber = 0;
    foreach (object oItem in lbBasket.Items)
    {
        iNumber++;
        sbReport.AppendLine(iNumber + ". " + oItem);
    }
    sbReport.AppendLine("");
    sbReport.AppendLine("Kept in " + settingsPath());
    HelpDialog.show(null, "Fruit basket report", sbReport.ToString());
    return false;
}

// The state, where a reader can find it without asking. Lbc puts a status line
// at the foot of every dialog, and it is worth using: it says what the speech
// says, for a person who reads the screen rather than listening, and for one who
// has turned the speaking off. The Python file has no status line to use -- wx
// dialogs have none -- so it puts the same sentence in the window title.
private static bool showState()
{
    if (dlgFruit == null) return false;
    dlgFruit.setStatusText(basketState());
    return true;
}

// ---- BLOCK 12: the way in ----
[STAThread]
public static int Main(string[] aArguments)
{
    Application.EnableVisualStyles();
    Application.SetCompatibleTextRenderingDefault(false);

    // The log opens first, so a failure in anything after it is explainable.
    // One file per session, in %LOCALAPPDATA%\FruitBasketCs\logs, pruned to
    // the most recent thirty. Writing a line costs microseconds; not having the
    // line costs an evening.
    Paths.start(c_sAppName);
    Log.start(c_sAppName);
    Log.keyValue("Settings file", settingsPath());
    Log.keyValue("Results folder", Paths.results());
    Log.info("Cleared " + Paths.clearTemp() + " leftover temporary items");
    try
    {
        int iResult = runDialog();
        Log.close();
        return iResult;
    }
    catch (Exception oError)
    {
        Log.exception(oError);
        Log.close();
        throw;
    }
}

} // class Program

} // namespace FruitBasketCs
