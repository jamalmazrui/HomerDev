r"""FruitBasketMdiPy.py -- the fruit basket as a Homer MDI app, in Python.

ITS TWIN IS FruitBasketMdiCs.cs, and since kit 1.73.6 they are not two
implementations of one design but one framework used from two languages. This
program builds the very Homer.MdiFrame, Homer.MdiChild and Homer.KeyMap the C#
sample builds, loaded from the kit's exec\Homer.dll through pythonnet (the kit's
mdi.py and lbcnet.py). The menus, keys, router, Say commands, clipboard family,
repeat presses, settings and help are therefore the same by construction, and
the kit's build checks it: it exports both samples' commands and fails if they
differ.

WHAT IT SHOWS, and what to try with a screen reader -- the same list as the C#
sample, since it is the same program:

  Two windows        Control+N opens another basket. F4 lists them,
                     Shift+F4 says them, Control+Tab moves between them.
  Typing             In the Fruit field, capital letters type, and so do
                     Shift+letter keys that are commands in the list.
  A managed list     In the basket list, type the start of a fruit to go to
                     it; Shift+F says the fruit, Shift+Y the count, and an
                     unbound Shift+letter says it has no command.
  An alias           Delete in the list runs Delete Fruit, whose main key
                     is Control+Shift+D. Delete in the Fruit field deletes
                     a character, as it should.
  Unavailable        Delete Fruit in an empty basket says why it cannot run.
                     Add Fruit in a full basket says so too.
  A modal dialog     F2 renames the basket. Its own keys come first.
  Repeat presses     Alt+Delete says the position; pressed twice quickly
                     it spells it; three times shows it in a window.
  Again              Control+J asks which fruit to jump to; Alt+J jumps to
                     the next one with no question; F3 repeats it too.
  Parts              F6 moves between the Fruit field and the basket list.
  Closing            Control+F4 on a basket that holds fruit asks first;
                     keeping it open is a real answer.
  Key Describer      Control+F1, then any key, says what it would do.
  Settings           Alt+Shift+E changes the basket size limit at once.
  Clipboard          Control+Apostrophe saves the clipboard to a new file,
                     Alt+Shift+Apostrophe appends it to one.
  Export             FruitBasketMdiPy.exe /exportkeys keys.inix writes every
                     command and key, then ends without a window.

Run it from source, from this folder, after the kit's build has made
exec\Homer.dll:

    python FruitBasketMdiPy.py

Or build FruitBasketMdiPy.exe with buildFruitBasketMdiPy.cmd. Camel Type. No
key-handling code anywhere: every key is declared with addCommand.
"""

import sys

import mdi

sAppName = "FruitBasketMdiPy"
Homer = None


# ------- a basket: one window -------

class Basket:
    """One basket window. The .NET window is self.child; the state is here."""

    def __init__(self, app, sName):
        from System import String
        from System.Collections.Generic import List
        self.app = app
        self.child = Homer.MdiChild(app.frm)
        lbc = self.child.lbc
        lbc.addBand()
        self.txtFruit = lbc.addInputBox("F&ruit:", "", "Type a fruit, then press Enter.")
        self.btnAdd = lbc.addButton("&Add", "Put this fruit in the basket.")
        lbc.endBand()
        self.lbBasket = lbc.addPickBox("Bas&ket:", List[String](), "",
                                       "The fruit in this basket. Type the start of one to go to it.")
        self.child.finishLayout()

        self.child.manageList(self.lbBasket)
        self.btnAdd.Click += lambda oSender, evArgs: self.addFruit()
        self.child.AcceptButton = self.btnAdd
        self.child.FormClosing += self.onClosing
        self.child.FormClosed += lambda oSender, evArgs: app.forget(self)

        self.child.setTitle(sName, "empty")
        self.child.setStatusText(self.state())
        self.txtFruit.Focus()
        Homer.Log.info("Opened " + sName)

    def count(self):
        return self.lbBasket.Items.Count

    def isFull(self):
        return self.count() >= self.app.basketSize()

    def state(self):
        iCount = self.count()
        if iCount == 0:
            return "empty"
        return ("1 fruit" if iCount == 1 else "%d fruit" % iCount) + " of %d" % self.app.basketSize()

    def showState(self):
        self.child.setTitle(self.child.subject, self.state())
        self.child.setStatusText(self.state())
        return True

    def addFruit(self):
        sFruit = self.txtFruit.Text.strip()
        if sFruit == "":
            Homer.Say.sayForced("Type a fruit first")
            self.txtFruit.Focus()
            return True
        self.lbBasket.Items.Add(sFruit)
        self.lbBasket.SelectedIndex = self.lbBasket.Items.Count - 1
        self.txtFruit.Text = ""
        self.showState()
        Homer.Say.say(mdi.lbcnet.strings([sFruit + " added", self.state()]))
        self.txtFruit.Focus()
        return True

    def deleteFruit(self):
        iFruit = self.lbBasket.SelectedIndex
        if iFruit < 0:
            Homer.Say.sayForced("Go to a fruit in the list first")
            self.lbBasket.Focus()
            return True
        sFruit = str(self.lbBasket.Items[iFruit]).strip()
        self.lbBasket.Items.RemoveAt(iFruit)
        if iFruit > self.lbBasket.Items.Count - 1:
            iFruit = self.lbBasket.Items.Count - 1
        if iFruit >= 0:
            self.lbBasket.SelectedIndex = iFruit
        self.showState()
        Homer.Say.say(mdi.lbcnet.strings([sFruit + " deleted", self.state()]))
        self.lbBasket.Focus()
        return True

    def renameBasket(self):
        dlg = Homer.LbcDialog("Rename Basket", self.child)
        try:
            tb = dlg.addInputBox("&Name:", self.child.subject, "The new name for this basket.")
            if not dlg.runOkCancel():
                return True
            sName = tb.Text.strip()
        finally:
            dlg.Dispose()
        if sName == "":
            Homer.Say.sayForced("A basket needs a name, so it was not renamed")
            return True
        self.child.setTitle(sName, self.state())
        Homer.Say.sayForced("Renamed " + sName)
        return True

    def sayFruit(self):
        iFruit = self.lbBasket.SelectedIndex
        if iFruit < 0:
            return mdi.answer("Fruit", "No fruit is selected")
        return mdi.answer("Fruit", str(self.lbBasket.Items[iFruit]))

    def sayYield(self):
        return mdi.answer("Yield", self.state())

    def sayPosition(self):
        """The suite's Alt+Delete: the unit and its denominator, and an empty
        basket is a plain answer, not a division by zero."""
        iCount = self.count()
        if iCount == 0:
            return mdi.answer("Position", "0 fruit")
        iFruit = self.lbBasket.SelectedIndex
        if iFruit < 0:
            return mdi.answer("Position", "No fruit is selected", "1 fruit" if iCount == 1 else "%d fruit" % iCount)
        iPercent = int(round(100.0 * (iFruit + 1) / iCount))
        return mdi.answer("Position", "Fruit %d of %d" % (iFruit + 1, iCount), "%d percent" % iPercent)

    def jump(self, bAsk, iDirection):
        """Control+J asks; Alt+J repeats without asking. The last answer is
        kept for THIS basket, and F3 knows it was the last search here."""
        sStart = Homer.KeyMap.recallInput("jumpToFruit", self.child)
        if bAsk or sStart == "":
            dlg = Homer.LbcDialog("Jump to Fruit", self.child)
            try:
                tb = dlg.addInputBox("&Starts with:", sStart, "The first letters of the fruit to go to.")
                if not dlg.runOkCancel():
                    return True
                sStart = tb.Text.strip()
            finally:
                dlg.Dispose()
            if sStart == "":
                return True
            Homer.KeyMap.rememberInput("jumpToFruit", self.child, sStart)
        Homer.KeyMap.setLastSearch(self.child, "jumpToFruit")
        iCount = self.count()
        if iCount == 0:
            Homer.Say.sayForced("The basket is empty")
            return True
        iFrom = self.lbBasket.SelectedIndex
        for i in range(1, iCount + 1):
            iTry = (iFrom + i * iDirection) % iCount
            if str(self.lbBasket.Items[iTry]).lower().startswith(sStart.lower()):
                self.lbBasket.SelectedIndex = iTry
                self.lbBasket.Focus()
                return True
        Homer.Say.sayForced("No fruit starts with " + sStart)
        return True

    def searchAgain(self, iDirection):
        if Homer.KeyMap.lastSearch(self.child) == "jumpToFruit":
            return self.jump(False, iDirection)
        Homer.Say.sayForced("Nothing has been searched for in this basket yet")
        return True

    def nextPart(self):
        if self.lbBasket.Focused:
            self.txtFruit.Focus()
        else:
            self.lbBasket.Focus()
        return True

    def onClosing(self, oSender, evArgs):
        """A basket with fruit in it asks first, and keeping it open is a real
        answer that Close All But Current Window counts as kept."""
        if self.count() == 0:
            return
        dlg = Homer.LbcDialog("Close Basket", self.child)
        try:
            dlg.addLabel(self.child.subject + " holds " + self.state() + ".")
            sAnswer = dlg.runWithButtons(mdi.lbcnet.strings(["Close", "Keep open"]), False, "Keep open")
        finally:
            dlg.Dispose()
        evArgs.Cancel = not (sAnswer is not None and str(sAnswer).replace("&", "").strip().lower() == "close")


# ------- the frame: the menus and the commands -------

class FruitApp:
    """The frame and its baskets. Every command is declared once, here."""

    def __init__(self):
        self.lsBaskets = []
        self.iBaskets = 0
        frm = Homer.MdiFrame(sAppName)
        self.frm = frm
        frm.addSetting("Basket Size", "10", "The most fruit one basket holds.")

        frm.addMenu("&File")
        mdi.addCommand(frm, "&New Basket", "Control+N", "Open another basket in its own window.", self.newBasket)
        mdi.addCommand(frm, "&Rename Basket...", "F2", "Give this basket a new name.",
                       lambda: self.withBasket(lambda b: b.renameBasket()))
        mdi.addCommand(frm, "&Exit", "Alt+F4", "Close every basket and leave.", lambda: frm.Close())

        frm.addMenu("&Basket")
        mdi.addCommand(frm, "&Add Fruit", "Alt+Shift+A", "Put what is in the fruit field into this basket.",
                       lambda: self.withBasket(lambda b: b.addFruit()),
                       fnUnavailable=lambda: "the basket is full" if self.active() is not None and self.active().isFull() else "")
        oDelete = mdi.addCommand(frm, "&Delete Fruit", "Control+Shift+D", "Take the fruit you are on out of this basket.",
                                 lambda: self.withBasket(lambda b: b.deleteFruit()),
                                 fnUnavailable=lambda: "the basket is empty" if self.active() is not None and self.active().count() == 0 else "")
        Homer.KeyMap.addAlias(oDelete.sId, "Delete")
        mdi.addCommand(frm, "&Jump to Fruit...", "Control+J", "Ask for a fruit and go to the next one that starts with it.",
                       lambda: self.withBasket(lambda b: b.jump(True, 1)))
        mdi.addCommand(frm, "Jump &Again", "Alt+J", "Go to the next fruit that starts with the same letters, without asking.",
                       lambda: self.withBasket(lambda b: b.jump(False, 1)))
        mdi.addCommand(frm, "Search &Next", "F3", "Repeat the last search in this basket.",
                       lambda: self.withBasket(lambda b: b.searchAgain(1)))
        mdi.addCommand(frm, "Search &Previous", "Shift+F3", "Repeat the last search in this basket, backward.",
                       lambda: self.withBasket(lambda b: b.searchAgain(-1)))
        mdi.addCommand(frm, "Next &Part", "F6", "Move between the fruit field and the basket list.",
                       lambda: self.withBasket(lambda b: b.nextPart()))

        frm.addMenu("&Query")
        mdi.addCommand(frm, "Say &Position", "Alt+Delete", "Say which fruit you are on, of how many, and how far through.",
                       lambda: self.withBasket(lambda b: b.sayPosition()), sRepeat="review")
        mdi.addCommand(frm, "Say &Yield", "Alt+Y", "Say how full this basket is.",
                       lambda: self.withBasket(lambda b: b.sayYield()), sRepeat="review")

        # The list layer: Shift plus a letter, live only in the basket list.
        mdi.addCommand(frm, "Say &Fruit", "Shift+F", "Say the fruit you are on.",
                       lambda: self.withBasket(lambda b: b.sayFruit()), sContext=Homer.KeyMap.sListContext, sRepeat="review")
        mdi.addCommand(frm, "Say Yield in List", "Shift+Y", "Say how full this basket is.",
                       lambda: self.withBasket(lambda b: b.sayYield()), sContext=Homer.KeyMap.sListContext)

        frm.finishMenus()
        self.newBasket()

    def active(self):
        """The basket whose window is active, or None."""
        from System import Object
        oActive = self.frm.ActiveMdiChild
        for b in self.lsBaskets:
            if Object.ReferenceEquals(b.child, oActive):
                return b
        return None

    def withBasket(self, fnWork):
        """Run a command on the active basket, or say there is none."""
        b = self.active()
        if b is None:
            Homer.Say.sayForced("No basket is open")
            return True
        return fnWork(b)

    def basketSize(self):
        try:
            iSize = int(self.frm.settingValue("Basket Size"))
            return iSize if iSize > 0 else 10
        except (TypeError, ValueError):
            return 10

    def newBasket(self):
        self.iBaskets += 1
        b = Basket(self, "Basket %d" % self.iBaskets)
        self.lsBaskets.append(b)
        b.child.Show()
        return True

    def forget(self, b):
        if b in self.lsBaskets:
            self.lsBaskets.remove(b)
        return True


def main():
    global Homer
    Homer = mdi.load()
    Homer.Paths.start(sAppName)
    Homer.Log.start(sAppName)
    try:
        app = FruitApp()
        iCode = mdi.run(app.frm)
        Homer.Log.close()
        return iCode
    except Exception:
        mdi.logException("FruitBasketMdiPy stopped on an error.")
        Homer.Log.close()
        raise


if __name__ == "__main__":
    sys.exit(main())
