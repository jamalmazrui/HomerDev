// FruitBasketMdiCs.cs -- the fruit basket as an MDI app, the third Homer shape.
//
// ITS TWIN IS FruitBasketMdiPy.py. The two are the same program in two
// languages, as FruitBasketCs and FruitBasketPy are, so the claim the kit makes
// -- one behaviour, either language -- holds for the MDI shape too.
//
// READ FruitBasketCs.cs FIRST. That one is a single dialog, and its twelve
// numbered blocks explain the nine decisions every Homer program makes. This
// file does not repeat them. It shows only what changes when a program holds
// SEVERAL things at once -- several baskets here, several files in EdSharp,
// several folders in FileDir, several tables in DbDo.
//
// THE LINEAGE. The MDI fruit basket goes back to Homer.NET in 2010, with
// LbcMdiApp, LbcMdiFrame and LbcMdiChild, a menu declared by name and key, a
// focus tip on every control, a window picker, an alternate menu and a key
// describer. That program was right about the shape. What is different now is
// that the frame lives in the kit, so EdSharp, FileDir and DbDo can share one
// implementation instead of three that drift apart.
//
// WHAT CHANGES WHEN THERE IS MORE THAN ONE WINDOW:
//
//   ---- MDI 1: the frame owns the app name, the child owns the subject ----
//   ---- MDI 2: commands are named sentences, not control ids ----
//   ---- MDI 3: the frame's own window and help commands come free ----
//   ---- MDI 4: each child keeps its own state ----
//   ---- MDI 5: closing the last window closes the program ----
//
// Build with buildFruitBasketMdiCs.cmd.

using System;
using System.Collections.Generic;
using System.Windows.Forms;
using Homer;

namespace FruitBasketMdiCs
{

public static class Program
{

private const string c_sAppName = "FruitBasketMdiCs";

private static fruitFrame frmMain;

// ---- MDI 1: the frame owns the app name, the child owns the subject ----
//
// The frame is titled "FruitBasketMdiCs" and nothing else. A child is titled
// "Basket 1 - 3 fruits" and nothing else. Windows merges a maximized child into
// the frame caption, so JAWS+T reads
//
//     FruitBasketMdiCs - [Basket 1 - 3 fruits]
//
// A child that repeated the app name made the reader say it twice, which is a
// bug DbDo shipped once and now carries a comment against. MdiChild.setTitle is
// the only way to set a child title, so the rule cannot be broken by accident.
public class fruitFrame : MdiFrame
{
    private int iBaskets = 0;

    public fruitFrame() : base(c_sAppName)
    {
        // ---- MDI 2: commands are named sentences, not control ids ----
        //
        // addItem takes the command, its key and its one-line summary. The
        // summary is not decoration: it becomes the status tip, the key
        // describer's answer under Control+F1, and the entry in the hotkey
        // document. Written once, it reaches a person three ways.
        addMenu("&File");
        addItem("New Basket", Keys.Control | Keys.N, "Open another basket in its own window.");
        addItem("Exit", Keys.Alt | Keys.F4, "Close every basket and leave.");

        addMenu("&Basket");
        addItem("Add Fruit", Keys.Control | Keys.Shift | Keys.A, "Put what is in the fruit field into this basket.");
        addItem("Delete Fruit", Keys.Control | Keys.Shift | Keys.D, "Take the selected fruit out of this basket.");
        addItem("Count Fruit", Keys.Alt | Keys.Shift | Keys.C, "Say how full this basket is.");

        // ---- MDI 3: the frame's own window and help commands come free ----
        //
        // finishMenus fills in Window and Help: the window picker on F4, the
        // spoken window list on Shift+F4, next and previous, close, close
        // others, the alternate menu on Alt+F10, the key describer on
        // Control+F1, about on Alt+F1 and the guide on F1. Not one of them is
        // in this file, and every Homer MDI app has all of them.
        finishMenus();

        newBasket();
    }

    // onCommand answers the app's own commands and lets the frame have the
    // rest. One switch, in alphabetical order, reading like the menu does.
    protected override bool onCommand(string sCommand)
    {
        fruitChild child = this.ActiveMdiChild as fruitChild;
        switch (sCommand)
        {
            case "Add Fruit": if (child != null) child.addFruit(); return true;
            case "Count Fruit": if (child != null) Say.sayForced(child.basketState()); return true;
            case "Delete Fruit": if (child != null) child.deleteFruit(); return true;
            case "Exit": this.Close(); return true;
            case "New Basket": return newBasket();
            default: return false;
        }
    }

    public bool newBasket()
    {
        iBaskets++;
        fruitChild child = new fruitChild(this, "Basket " + iBaskets);
        child.Show();
        return true;
    }
}

// ---- MDI 4: each child keeps its own state ----
//
// This is the reason to use windows rather than tabs. A window is a first-class
// object to a screen reader: Alt+Tab reaches it, the window list names it, and
// its title is announced when it is activated. Each basket below holds its own
// fruit, its own selection and its own status line, and none of that needed any
// code to keep separate.
public class fruitChild : MdiChild
{
    private Button btnAdd;
    private ListBox lbBasket;
    private TextBox txtFruit;

    public fruitChild(MdiFrame frmParent, string sName) : base(frmParent)
    {
        // The controls are built with Lbc primitives, exactly as in the single
        // dialog version, so everything there is true here: add order is focus
        // order, an ampersand is the whole of an access key, and the list and
        // the field arrive with their search and their line chords already on.
        // THE MENU OWNS THE PLAIN LETTERS, so the controls take others: the
        // field is F&ruit and the list is Bas&ket, because Alt+F belongs to the
        // File menu and Alt+B to the Basket menu. In the single-dialog version
        // there is no menu bar and the same controls are &Fruit and &Basket.
        // checkHomerApp found this on its first run of this file, which is
        // exactly what it is for.
        lbc.addBand();
        txtFruit = lbc.addInputBox("F&ruit:", "", "Type a fruit, then press Enter.");
        btnAdd = lbc.addButton("&Add", "Put this fruit in the basket.");
        lbc.endBand();

        lbBasket = lbc.addPickBox("Bas&ket:", new List<string>(), "",
            "The fruit in this basket. Press Delete to remove the one you are on.");

        finishLayout();

        btnAdd.Click += delegate(object oSender, EventArgs evArgs) { addFruit(); };
        this.AcceptButton = btnAdd;
        lbBasket.KeyDown += delegate(object oSender, KeyEventArgs evKey)
        {
            if (evKey.KeyCode == Keys.Delete) { deleteFruit(); evKey.Handled = true; }
        };

        setTitle(sName, "empty");
        setStatusText(basketState());
        txtFruit.Focus();
        Log.info("Opened " + sName);
    }

    public string basketState()
    {
        int iCount = lbBasket.Items.Count;
        if (iCount == 0) return "the basket is empty";
        return Util.stringPlural("fruit", iCount) + " in the basket";
    }

    public bool addFruit()
    {
        string sFruit = txtFruit.Text.Trim();
        if (sFruit == "")
        {
            Say.sayForced("Type a fruit first");
            txtFruit.Focus();
            return false;
        }
        lbBasket.Items.Add(sFruit);
        lbBasket.SelectedIndex = lbBasket.Items.Count - 1;
        txtFruit.Text = "";
        showState();
        Say.say(sFruit + " added, " + basketState());
        txtFruit.Focus();
        return true;
    }

    public bool deleteFruit()
    {
        int iFruit = lbBasket.SelectedIndex;
        if (iFruit == -1)
        {
            Say.sayForced("No fruit is selected");
            lbBasket.Focus();
            return false;
        }
        string sFruit = ("" + lbBasket.Items[iFruit]).Trim();
        lbBasket.Items.RemoveAt(iFruit);
        if (iFruit > lbBasket.Items.Count - 1) iFruit = lbBasket.Items.Count - 1;
        if (iFruit >= 0) lbBasket.SelectedIndex = iFruit;
        showState();
        Say.say(sFruit + " deleted, " + basketState());
        lbBasket.Focus();
        return true;
    }

    // The count goes in the title AND the status line, and for different
    // readers. The title is what Alt+Tab and the window list say, so a person
    // choosing between three baskets hears which is which without opening them.
    private bool showState()
    {
        setTitle(subject, basketState());
        setStatusText(basketState());
        return true;
    }
}

// ---- MDI 5: closing the last window closes the program ----
//
// A frame with no children has no menu bar and nothing to tab to, which is a
// dead end for a keyboard user. MdiFrame closes itself when the last child
// goes, so this file does not have to think about it.
[STAThread]
public static int Main(string[] aArguments)
{
    Application.EnableVisualStyles();
    Application.SetCompatibleTextRenderingDefault(false);
    Paths.start(c_sAppName);
    Log.start(c_sAppName);
    try
    {
        frmMain = new fruitFrame();
        Application.Run(frmMain);
        Log.close();
        return 0;
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
