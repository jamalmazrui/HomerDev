"""FruitBasketMdiPy.py -- the fruit basket as an MDI app, in Python.

ITS TWIN IS Samples\\FruitBasketMdiCs.cs. The two are the same program in two
languages, exactly as FruitBasketCs and FruitBasketPy are, so the claim the kit
makes -- one behaviour, either language -- holds for the multiple-document shape
as well. Open both and read across: same five marked blocks, same command names,
same keys, same titles.

READ FruitBasketPy.py FIRST. That one is a single dialog and its twelve numbered
blocks explain the nine decisions every Homer program makes. This file does not
repeat them. It shows only what changes when a program holds SEVERAL things at
once.

  ---- MDI 1: the frame owns the app name, the child owns the subject ----
  ---- MDI 2: commands are named sentences, not control ids ----
  ---- MDI 3: the frame's own window and help commands come free ----
  ---- MDI 4: each child keeps its own state ----
  ---- MDI 5: closing the last window closes the program ----

Run it from source:

    python FruitBasketMdiPy.py

Or build FruitBasketMdiPy.exe with buildFruitBasketMdiPy.cmd.
"""

import os
import sys

import wx

from homer import inix, log, mdi, paths, say, util

c_sAppName = "FruitBasketMdiPy"


# ---- MDI 1: the frame owns the app name, the child owns the subject ----
#
# The frame is titled "FruitBasketMdiPy" and nothing else. A child is titled
# "Basket 1 - 3 fruits" and nothing else. A screen reader reading the title then
# says each part once. setTitle is the only way to set a child title, so the
# rule cannot be broken by accident.
class fruitFrame(mdi.MdiFrame):

    def __init__(self):
        mdi.MdiFrame.__init__(self, c_sAppName)
        self.iBaskets = 0

        # ---- MDI 2: commands are named sentences, not control ids ----
        #
        # addItem takes the command, its key and its one-line summary. The
        # summary becomes the status tip, the key describer's answer under
        # Control+F1, and the entry in the hotkey document. Written once, it
        # reaches a person three ways.
        self.addMenu("&File")
        self.addItem("New Basket", "Ctrl+N", "Open another basket in its own window.")
        self.addItem("Exit", "Alt+F4", "Close every basket and leave.")

        self.addMenu("&Basket")
        self.addItem("Add Fruit", "Ctrl+Shift+A", "Put what is in the fruit field into this basket.")
        self.addItem("Delete Fruit", "Ctrl+Shift+D", "Take the selected fruit out of this basket.")
        self.addItem("Count Fruit", "Alt+Shift+C", "Say how full this basket is.")

        # WHAT THE USER MAY CHANGE WHILE THE PROGRAM RUNS. The frame lists these
        # under Alt+Shift+C, reads and writes them itself, and calls back into
        # onSettingChanged. No restart, no settings dialog to build.
        self.addSetting("speak", "1", "1 to speak each change, 0 to stay silent.")
        self.addSetting("sort", "added", "added keeps the order fruit went in; name sorts alphabetically.")

        # ---- MDI 3: the frame's own window and help commands come free ----
        #
        # finishMenus fills in Window and Help: the window picker on F4, the
        # spoken window list on Shift+F4, next and previous, close and
        # close-others, the script list on Alt+Shift+S, the settings list on
        # Alt+Shift+C, the alternate menu on Alt+F10, the key describer on
        # Control+F1, about on Alt+F1 and the guide on F1. Not one of them is in
        # this file, and every Homer MDI app has all of them.
        self.finishMenus()
        self.newBasket()

    def onCommand(self, sCommand):
        child = self.GetActiveChild()
        if sCommand == "Add Fruit":
            if child: child.addFruit()
            return True
        if sCommand == "Count Fruit":
            if child: say.say(child.basketState(), True)
            return True
        if sCommand == "Delete Fruit":
            if child: child.deleteFruit()
            return True
        if sCommand == "Exit":
            self.Close()
            return True
        if sCommand == "New Basket": return self.newBasket()
        return False

    # The app acts on a changed setting here, at once.
    def onSettingChanged(self, sName, sValue):
        if sName == "sort":
            for child in self.children(): child.sortBasket()
        return True

    def newBasket(self):
        self.iBaskets += 1
        child = fruitChild(self, "Basket %d" % self.iBaskets)
        child.Show()
        return True


# ---- MDI 4: each child keeps its own state ----
#
# This is the reason to use windows rather than tabs. A window is a first-class
# object to a screen reader: Alt+Tab reaches it, the window list names it, and
# its title is announced when it is activated. Each basket below holds its own
# fruit, its own selection and its own status line, and none of that needed any
# code to keep separate.
class fruitChild(mdi.MdiChild):

    def __init__(self, frameParent, sName):
        mdi.MdiChild.__init__(self, frameParent)

        self.txtFruit = self.addInputBox("F&ruit:", "", "Type a fruit, then press Enter.")
        self.btnAdd = self.addButton("&Add", self.addFruit)
        self.lbBasket = self.addListBox("Bas&ket:", [],
            "The fruit in this basket. Press Delete to remove the one you are on.")
        self.finishLayout()

        # THE MENU OWNS THE PLAIN LETTERS, so the controls take others: the field
        # is F&ruit and the list is Bas&ket, because Alt+F belongs to the File
        # menu and Alt+B to the Basket menu. In the single-dialog version there
        # is no menu bar and the same controls are &Fruit and &Basket.
        self.txtFruit.SetWindowStyleFlag(self.txtFruit.GetWindowStyle() | wx.TE_PROCESS_ENTER)
        self.txtFruit.Bind(wx.EVT_TEXT_ENTER, lambda oEvent: self.addFruit())
        self.lbBasket.Bind(wx.EVT_KEY_DOWN, self.basketKeyDown)

        self.setTitle(sName, "empty")
        self.setStatusText(self.basketState())
        self.txtFruit.SetFocus()
        log.info("Opened " + sName)

    def basketState(self):
        iCount = self.lbBasket.GetCount()
        if iCount == 0: return "the basket is empty"
        return "%d %s in the basket" % (iCount, util.stringPlural("fruit", iCount))

    def speaks(self):
        return self.frameParent.settingValue("speak") != "0"

    def addFruit(self):
        sFruit = self.txtFruit.GetValue().strip()
        if not sFruit:
            say.say("Type a fruit first", True)
            self.txtFruit.SetFocus()
            return False
        log.info("Adding " + sFruit)
        self.lbBasket.Append(sFruit)
        self.lbBasket.SetSelection(self.lbBasket.GetCount() - 1)
        self.txtFruit.SetValue("")
        self.sortBasket(sFruit)
        if self.speaks(): say.say(sFruit + " added, " + self.basketState())
        self.txtFruit.SetFocus()
        return True

    def deleteFruit(self):
        iFruit = self.lbBasket.GetSelection()
        if iFruit == wx.NOT_FOUND:
            say.say("No fruit is selected", True)
            self.lbBasket.SetFocus()
            return False
        sFruit = self.lbBasket.GetString(iFruit)
        log.info("Deleting %s from position %d" % (sFruit, iFruit))
        self.lbBasket.Delete(iFruit)
        # Select the neighbour, so the list still has somewhere to speak from.
        if iFruit > self.lbBasket.GetCount() - 1: iFruit = self.lbBasket.GetCount() - 1
        if iFruit >= 0: self.lbBasket.SetSelection(iFruit)
        self.showState()
        if self.speaks(): say.say(sFruit + " deleted, " + self.basketState())
        self.lbBasket.SetFocus()
        return True

    def sortBasket(self, sKeep=""):
        if self.frameParent.settingValue("sort") != "name":
            self.showState()
            return False
        lFruit = sorted([self.lbBasket.GetString(i) for i in range(self.lbBasket.GetCount())],
                        key=lambda s: s.lower())
        self.lbBasket.Set(lFruit)
        if lFruit:
            self.lbBasket.SetSelection(lFruit.index(sKeep) if sKeep in lFruit else 0)
        self.showState()
        return True

    def basketKeyDown(self, oEvent):
        if oEvent.GetKeyCode() == wx.WXK_DELETE: self.deleteFruit()
        else: oEvent.Skip()

    # The count goes in the title AND the status line, for different readers. The
    # title is what Alt+Tab and the window list say, so a person choosing between
    # three baskets hears which is which without opening them.
    def showState(self):
        self.setTitle(self.sSubject, self.basketState())
        self.setStatusText(self.basketState())
        return True


# ---- MDI 5: closing the last window closes the program ----
#
# A frame with no children has no menu bar and nothing to tab to, which is a
# dead end for a keyboard user.
def main():
    paths.start(c_sAppName)
    log.start(c_sAppName)
    try:
        oApp = wx.App(False)
        frame = fruitFrame()
        frame.Show()
        oApp.MainLoop()
        log.close()
        return 0
    except Exception:
        log.exception()
        log.close()
        raise


if __name__ == "__main__":
    sys.exit(main())
