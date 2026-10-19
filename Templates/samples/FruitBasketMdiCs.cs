// FruitBasketMdiCs.cs -- the fruit basket as a Homer MDI app, and the proof
// that the shared frame and key router behave as the suite contract says.
//
// It is the worked example for anybody building an app on the Homer MDI
// framework: every feature a real app needs appears here once, small enough to
// read in one sitting. Its twin, FruitBasketMdiPy.py, builds the same frame from
// Python, and the kit's build fails if the two ever declare different commands. help\MdiFramework.md in the kit walks through it, and
// help\HomerSuite.md lists the checks it is used for (stage 1, the desktop
// proof).
//
// WHAT IT SHOWS, and what to try with a screen reader:
//
//   Two windows        Control+N opens another basket. F4 lists them,
//                      Shift+F4 says them, Control+Tab moves between them.
//   Typing             In the Fruit field, capital letters type, and so do
//                      Shift+letter keys that are commands in the list.
//   A managed list     In the basket list, type the start of a fruit to go to
//                      it; Shift+F says the fruit, Shift+Y the count, and an
//                      unbound Shift+letter says it has no command.
//   An alias           Delete in the list runs Delete Fruit, whose main key
//                      is Control+Shift+D. Delete in the Fruit field deletes
//                      a character, as it should.
//   Unavailable        Delete Fruit in an empty basket says why it cannot run.
//                      Add Fruit in a full basket says so too.
//   A modal dialog     F2 renames the basket. Its own keys come first.
//   Repeat presses     Alt+Delete says the position; pressed twice quickly
//                      it spells it; three times shows it in a window.
//   Again              Control+J asks which fruit to jump to; Alt+J jumps to
//                      the next one with no question; F3 repeats it too.
//   Parts              F6 moves between the Fruit field and the basket list.
//   Closing            Control+F4 on a basket that holds fruit asks first;
//                      keeping it open is a real answer.
//   Key Describer      Control+F1, then any key, says what it would do.
//   Settings           Alt+Shift+E changes the basket size limit at once.
//   Clipboard          Control+Apostrophe saves the clipboard to a new file,
//                      Alt+Shift+Apostrophe appends it to one.
//   Export             FruitBasketMdiCs.exe /exportkeys keys.inix writes every
//                      command and key, then closes.
//
// Camel Type. No key-handling code anywhere: every key is declared with
// addCommand and the kit's router does the rest.

using System;
using System.Collections.Generic;
using System.Windows.Forms;
using Homer;

namespace FruitBasketMdiCs
{

public static class Program
{

private static readonly string sAppName = "FruitBasketMdiCs";

private static fruitFrame frmMain;

// ------- the frame: the menus and the commands -------

public class fruitFrame : MdiFrame
{
    private int iBaskets = 0;

    public fruitFrame() : base(sAppName)
    {
        addSetting("Basket Size", "10", "The most fruit one basket holds.");

        addMenu("&File");
        addCommand("&New Basket", "Control+N", "Open another basket in its own window.", newBasket);
        addCommand("&Rename Basket...", "F2", "Give this basket a new name.", delegate() { return withBasket(delegate(fruitChild c) { return c.renameBasket(); }); });
        addCommand("&Exit", "Alt+F4", "Close every basket and leave.", delegate() { this.Close(); return true; });

        addMenu("&Basket");
        KeyMap.Command oAdd = addCommand("&Add Fruit", "Alt+Shift+A", "Put what is in the fruit field into this basket.",
            delegate() { return withBasket(delegate(fruitChild c) { return c.addFruit(); }); });
        oAdd.fUnavailable = delegate() { fruitChild c = activeBasket(); return c != null && c.isFull() ? "the basket is full" : ""; };

        KeyMap.Command oDelete = addCommand("&Delete Fruit", "Control+Shift+D", "Take the fruit you are on out of this basket.",
            delegate() { return withBasket(delegate(fruitChild c) { return c.deleteFruit(); }); });
        oDelete.fUnavailable = delegate() { fruitChild c = activeBasket(); return c != null && c.count() == 0 ? "the basket is empty" : ""; };
        KeyMap.addAlias(oDelete.sId, "Delete");

        addCommand("&Jump to Fruit...", "Control+J", "Ask for a fruit and go to the next one that starts with it.",
            delegate() { return withBasket(delegate(fruitChild c) { return c.jump(true, 1); }); });
        addCommand("Jump &Again", "Alt+J", "Go to the next fruit that starts with the same letters, without asking.",
            delegate() { return withBasket(delegate(fruitChild c) { return c.jump(false, 1); }); });
        addCommand("Search &Next", "F3", "Repeat the last search in this basket.",
            delegate() { return withBasket(delegate(fruitChild c) { return c.searchAgain(1); }); });
        addCommand("Search &Previous", "Shift+F3", "Repeat the last search in this basket, backward.",
            delegate() { return withBasket(delegate(fruitChild c) { return c.searchAgain(-1); }); });
        addCommand("Next &Part", "F6", "Move between the fruit field and the basket list.",
            delegate() { return withBasket(delegate(fruitChild c) { return c.nextPart(); }); });

        addMenu("&Query");
        addCommand("Say &Position", "Alt+Delete", "Say which fruit you are on, of how many, and how far through.",
            delegate() { return withBasket(delegate(fruitChild c) { return c.sayPosition(); }); }).sRepeat = "review";
        addCommand("Say &Yield", "Alt+Y", "Say how full this basket is.",
            delegate() { return withBasket(delegate(fruitChild c) { return c.sayYield(); }); }).sRepeat = "review";

        // The list layer: Shift plus a letter, live only in the basket list.
        addCommand("Say &Fruit", "Shift+F", KeyMap.sListContext, "Say the fruit you are on.",
            delegate() { return withBasket(delegate(fruitChild c) { return c.sayFruit(); }); }).sRepeat = "review";
        addCommand("Say Yield in List", "Shift+Y", KeyMap.sListContext, "Say how full this basket is.",
            delegate() { return withBasket(delegate(fruitChild c) { return c.sayYield(); }); });

        finishMenus();
        newBasket();
    }

    public fruitChild activeBasket()
    {
        return this.ActiveMdiChild as fruitChild;
    }

    // withBasket: run a command on the active basket, or say there is none.
    public bool withBasket(Func<fruitChild, bool> fWork)
    {
        fruitChild child = activeBasket();
        if (child == null) { Say.sayForced("No basket is open"); return true; }
        return fWork(child);
    }

    public int basketSize()
    {
        int iSize;
        return int.TryParse(settingValue("Basket Size"), out iSize) && iSize > 0 ? iSize : 10;
    }

    protected override bool onSettingChanged(string sName, string sValue)
    {
        Log.info("Basket size is now " + basketSize().ToString());
        return true;
    }

    public bool newBasket()
    {
        iBaskets++;
        fruitChild child = new fruitChild(this, "Basket " + iBaskets.ToString());
        child.Show();
        return true;
    }
}

// ------- a basket: one window -------

public class fruitChild : MdiChild
{
    private Button btnAdd;
    private fruitFrame frmFrame;
    private ListBox lbBasket;
    private TextBox txtFruit;

    public fruitChild(fruitFrame frmParent, string sName) : base(frmParent)
    {
        frmFrame = frmParent;
        lbc.addBand();
        txtFruit = lbc.addInputBox("F&ruit:", "", "Type a fruit, then press Enter.");
        btnAdd = lbc.addButton("&Add", "Put this fruit in the basket.");
        lbc.endBand();
        lbBasket = lbc.addPickBox("Bas&ket:", new List<string>(), "",
            "The fruit in this basket. Type the start of one to go to it.");
        finishLayout();

        manageList(lbBasket);
        btnAdd.Click += delegate(object oSender, EventArgs evArgs) { addFruit(); };
        this.AcceptButton = btnAdd;
        this.FormClosing += delegate(object oSender, FormClosingEventArgs evArgs) { evArgs.Cancel = !mayClose(); };

        setTitle(sName, "empty");
        setStatusText(state());
        txtFruit.Focus();
        Log.info("Opened " + sName);
    }

    public int count() { return lbBasket.Items.Count; }

    public bool isFull() { return count() >= frmFrame.basketSize(); }

    public string state()
    {
        int iCount = count();
        if (iCount == 0) return "empty";
        return (iCount == 1 ? "1 fruit" : iCount.ToString() + " fruit") + " of " + frmFrame.basketSize().ToString();
    }

    private bool showState()
    {
        setTitle(subject, state());
        setStatusText(state());
        return true;
    }

    public bool addFruit()
    {
        string sFruit = txtFruit.Text.Trim();
        if (sFruit == "") { Say.sayForced("Type a fruit first"); txtFruit.Focus(); return true; }
        lbBasket.Items.Add(sFruit);
        lbBasket.SelectedIndex = lbBasket.Items.Count - 1;
        txtFruit.Text = "";
        showState();
        Say.say(sFruit + " added", state());
        txtFruit.Focus();
        return true;
    }

    public bool deleteFruit()
    {
        int iFruit = lbBasket.SelectedIndex;
        if (iFruit < 0) { Say.sayForced("Go to a fruit in the list first"); lbBasket.Focus(); return true; }
        string sFruit = ("" + lbBasket.Items[iFruit]).Trim();
        lbBasket.Items.RemoveAt(iFruit);
        if (iFruit > lbBasket.Items.Count - 1) iFruit = lbBasket.Items.Count - 1;
        if (iFruit >= 0) lbBasket.SelectedIndex = iFruit;
        showState();
        Say.say(sFruit + " deleted", state());
        lbBasket.Focus();
        return true;
    }

    public bool renameBasket()
    {
        using (LbcDialog dlg = new LbcDialog("Rename Basket", this))
        {
            TextBox tb = dlg.addInputBox("&Name:", subject, "The new name for this basket.");
            if (!dlg.runOkCancel()) return true;
            string sName = tb.Text.Trim();
            if (sName == "") { Say.sayForced("A basket needs a name, so it was not renamed"); return true; }
            setTitle(sName, state());
            Say.sayForced("Renamed " + sName);
        }
        return true;
    }

    public bool sayFruit()
    {
        int iFruit = lbBasket.SelectedIndex;
        if (iFruit < 0) return KeyMap.answer("Fruit", "No fruit is selected");
        return KeyMap.answer("Fruit", "" + lbBasket.Items[iFruit]);
    }

    public bool sayYield()
    {
        return KeyMap.answer("Yield", state());
    }

    // sayPosition: the suite's Alt+Delete. The unit and its denominator are
    // said, and an empty basket is a plain answer, not a division by zero.
    public bool sayPosition()
    {
        int iCount = count();
        if (iCount == 0) return KeyMap.answer("Position", "0 fruit");
        int iFruit = lbBasket.SelectedIndex;
        if (iFruit < 0) return KeyMap.answer("Position", "No fruit is selected", (iCount == 1 ? "1 fruit" : iCount.ToString() + " fruit"));
        int iPercent = (int)Math.Round(100.0 * (iFruit + 1) / iCount);
        return KeyMap.answer("Position", "Fruit " + (iFruit + 1).ToString() + " of " + iCount.ToString(), iPercent.ToString() + " percent");
    }

    // jump: Control+J asks; Alt+J repeats without asking. The last answer is
    // kept for THIS basket, and F3 knows it was the last search here.
    public bool jump(bool bAsk, int iDirection)
    {
        string sStart = KeyMap.recallInput("jumpToFruit", this);
        if (bAsk || sStart == "")
        {
            using (LbcDialog dlg = new LbcDialog("Jump to Fruit", this))
            {
                TextBox tb = dlg.addInputBox("&Starts with:", sStart, "The first letters of the fruit to go to.");
                if (!dlg.runOkCancel()) return true;
                sStart = tb.Text.Trim();
            }
            if (sStart == "") return true;
            KeyMap.rememberInput("jumpToFruit", this, sStart);
        }
        KeyMap.setLastSearch(this, "jumpToFruit");
        int iCount = count();
        if (iCount == 0) { Say.sayForced("The basket is empty"); return true; }
        int iFrom = lbBasket.SelectedIndex < 0 ? -1 : lbBasket.SelectedIndex;
        for (int i = 1; i <= iCount; i++)
        {
            int iTry = ((iFrom + i * iDirection) % iCount + iCount) % iCount;
            string sItem = "" + lbBasket.Items[iTry];
            if (sItem.StartsWith(sStart, StringComparison.CurrentCultureIgnoreCase))
            {
                lbBasket.SelectedIndex = iTry;
                lbBasket.Focus();
                return true;
            }
        }
        Say.sayForced("No fruit starts with " + sStart);
        return true;
    }

    public bool searchAgain(int iDirection)
    {
        if (KeyMap.lastSearch(this) == "jumpToFruit") return jump(false, iDirection);
        Say.sayForced("Nothing has been searched for in this basket yet");
        return true;
    }

    public bool nextPart()
    {
        if (lbBasket.Focused) txtFruit.Focus();
        else lbBasket.Focus();
        return true;
    }

    // mayClose: a basket with fruit in it asks first, and keeping it open is
    // a real answer that Close All But Current Window counts as kept.
    private bool mayClose()
    {
        if (count() == 0) return true;
        using (LbcDialog dlg = new LbcDialog("Close Basket", this))
        {
            dlg.addLabel(subject + " holds " + state() + ".");
            string sAnswer = dlg.runWithButtons(new string[] { "Close", "Keep open" }, false, "Keep open");
            return sAnswer != null && sAnswer.Replace("&", "").Trim().Equals("Close", StringComparison.OrdinalIgnoreCase);
        }
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
        frmMain = new fruitFrame();
        int iCode = MdiFrame.runOrExport(frmMain);
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

} // namespace FruitBasketMdiCs
