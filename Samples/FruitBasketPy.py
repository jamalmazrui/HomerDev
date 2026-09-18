"""FruitBasketPy.py -- the fruit basket program on the Homer Python package.

THIS FILE AND Samples\\FruitBasketCs.cs ARE THE SAME PROGRAM.
Open them side by side. Every section below is marked

    # ---- BLOCK n: <title> ----

and the block with the same number and title in the other file does the same
job. The blocks do not line up line for line -- C# needs a class where Python
needs none, Python needs no type on a variable -- but nothing appears in one
that has no counterpart in the other, and the counterpart is named the same.

THE SPECIFICATION, the teaching exercise among blind programmers since 2005: a
window with a fruit field and an Add button, a basket list and a Delete button.
Adding an empty field says so rather than adding nothing. Deleting with nothing
selected says so too. After every action the focus lands where the next action
starts.

This version adds what the original could not: the basket survives being
closed, the basket can be sorted, a report opens in a readable window, and every
message a screen reader could not work out for itself is spoken.

WHAT TO NOTICE. Nine decisions are marked DECISION 1 to DECISION 9 where they
occur, and the same nine are marked in the C# file. Each is a decision a working
program has to get right and that an AI will not make for you unless you ask
for it.

WHAT IS BORROWED RATHER THAN WRITTEN. Everything below arrives with the call
that creates the control. None of it is in this file, which is the point of a
kit, and all of it is in the C# file too:

  IN THE FRUIT FIELD, because it is an lbc input box:
    Alt+C, Alt+X          append a copy or a cut to the clipboard
    Alt+F8                read the whole field aloud
    Control+C, Control+X  copy or cut the CURRENT LINE with nothing selected
    Control+D             delete the current line, speaking the next
    Control+F8            copy the whole field
    F8, Shift+F8          mark a selection in two keystrokes

  IN THE BASKET, because it is an lbc list:
    Control+C             copy the item under the cursor
    Control+J             search inside the list
    F3, Shift+F3          repeat that search forwards and back

  IN THE DIALOG ITSELF:
    Alt+letter            any control with an ampersand in its label
    Control+Enter         accept from anywhere, including a list or a memo
    Escape                cancel
    Shift+F1              speak the tip of whatever has focus

AND A LOG, from homer.log: one file per session in
%LOCALAPPDATA%\\FruitBasketPy\\logs, holding the environment, every setting, and
every error with its traceback.

Run it from source:

    python FruitBasketPy.py

Or build FruitBasketPy.exe with buildFruitBasketPy.cmd.
"""

# ---- BLOCK 1: what this file needs ----
import os
import sys

import wx

from homer import inix, lbc, log, paths, say, util

# ---- BLOCK 2: names ----
#
# Constants carry c_ and their type letter, as Camel Type has it, and they sit
# together at the top where a reader can find them.
c_sAppName = "FruitBasketPy"
c_sSection = "Basket"
c_sSettingsFile = "FruitBasketPy.inix"

# The two ways the basket can be ordered. Alphabetical, as every list in Homer
# code is unless another order is clearly more logical.
c_lSortOrders = ["added", "name"]


# ---- BLOCK 3: where the basket is kept ----
#
# %LOCALAPPDATA%\\FruitBasketPy\\configs\\FruitBasketPy.inix, which is where the
# Homer layout puts a setting the program writes. paths.configFile hands back
# the user's copy, making it from the one that shipped with the program the
# first time, so this file never has to know which case it is in.
#
# The letters are the point of that layout: configs, data, exec, jobs, logs,
# results, samples, temp and templates all start differently, so a screen reader
# user reaches any of them with one keystroke.
def settingsPath():
    return paths.configFile(c_sSettingsFile)


# The settings file is .inix, which is .ini with the corners knocked off: a
# value may run over several lines and be kept exactly as written, and reading
# one setting is one call. inix.getValue answers the default for a missing file,
# a missing section, a missing key and an empty value alike, because a caller
# asking for a setting wants an answer rather than four ways of saying no.
def loadBasket():
    return [s.strip() for s in inix.getValue(settingsPath(), c_sSection, "Fruit", "").split(",")
            if s.strip()]


class fruitDialog(lbc.Dialog):
    """The one window: fruit in, basket out."""

    # ---- BLOCK 4: the dialog, built in the order it is read ----
    def __init__(self):
        # DECISION 1: WHICH LIBRARY. homer.lbc builds the window out of ordinary
        # wxPython controls, which are the native Windows controls underneath,
        # which is why every screen reader already knows them. What it adds is
        # the arrangement: each control arrives with its label, its accessible
        # name and its place in the tab order already correct.
        #
        # Ask an AI for "a fruit basket window in Python" and you get wx with
        # sizers. It works, and its tab order is an accident. Asking for it "on
        # homer.lbc" is the whole difference.
        lbc.Dialog.__init__(self, None, "Fruit Basket")

        # DECISION 2: ADD ORDER IS FOCUS ORDER. The order of the calls below is
        # the order a person tabs through the window, which is the order they
        # hear it in. There is no tab-order code anywhere in this file, and
        # there should be none in yours: when the order is wrong, move the call.
        #
        # DECISION 3: BANDS. A band puts controls on one row. Fruit and Add
        # belong together because Add acts on what was just typed; the basket
        # and Delete belong together for the same reason.
        #
        # DECISION 4: ACCESS KEYS. The ampersand before a letter is the whole
        # mechanism. Close gets none, because Escape is already its key and a
        # letter it does not need is a letter another control may want.
        #
        # THE TIP is the sTip argument. Shift+F1 speaks the tip of whatever has
        # focus, so the explanation is written once and reaches a reader when
        # they want it rather than every time they pass.
        self.addBand()
        self.txtFruit = self.addInputBox("&Fruit:", "", "txtFruit",
            sTip="Type the name of a fruit, then press Enter or the Add button.")
        self.addButton("&Add", False, "btnAdd")

        # A list box from lbc has Control+J to search inside it, F3 to repeat
        # the search, and Control+C to copy the item under the cursor. All three
        # come from the kit, and this file does nothing to get them.
        self.addBand()
        self.lbBasket = self.addListBox("&Basket:", loadBasket(), 0, "lbBasket",
            sTip="The fruit in the basket. Press Delete to remove the one you are on.")

        self.addBand()
        self.addButton("&Delete", False, "btnDelete")
        self.addButton("&Report", False, "btnReport")

        # A combo pick box offers a short list of legal values and refuses
        # anything else, which is what a setting wants. Type-ahead works, and a
        # screen reader announces each value as the arrow keys pass it.
        self.addBand()
        self.cboSort = self.addComboPickBox("&Sort by:", c_lSortOrders,
            inix.getValue(settingsPath(), c_sSection, "Sort", "added"), "cboSort",
            sTip="added keeps the basket in the order fruit went in; name sorts it alphabetically.")
        self.cboSort.Bind(wx.EVT_COMBOBOX, lambda oEvent: self.sortBasket())

        self.addBand()
        self.cbSpeak = self.addCheckBox("Spea&k each change",
            inix.getValue(settingsPath(), c_sSection, "Speak", "1") == "1", "cbSpeak")
        self.dTips[self.cbSpeak] = \
            "When this is off, the program stays silent and the screen reader does all the talking."

        # DECISION 9: THE ESCAPE HATCH. Enter in the field should add the fruit,
        # which is this program's own arrangement rather than the dialog's
        # default. The wx control is right there when the wrapper does not cover
        # something. Reach for it rarely, and say why when you do.
        self.txtFruit.SetWindowStyleFlag(self.txtFruit.GetWindowStyle() | wx.TE_PROCESS_ENTER)
        self.txtFruit.Bind(wx.EVT_TEXT_ENTER, lambda oEvent: self.addFruit())

        self.lbBasket.Bind(wx.EVT_KEY_DOWN, self.basketKeyDown)
        log.section("Dialog built")
        log.keyValue("Sort order", self.cboSort.GetValue())
        log.keyValue("Speak changes", str(self.cbSpeak.GetValue()))
        self.setInitialFocus("txtFruit")

    # ---- BLOCK 5: the buttons that act without closing ----
    #
    # A dialog's buttons normally end it. Add, Delete and Report do work and
    # leave the window open, and each language has one way of saying so. In
    # Python the dialog's own handler is given every press and keeps the window
    # open by answering False. In C# a button added with addButton is an
    # ordinary button with an ordinary Click handler, and only the buttons named
    # in runWithButtons close the dialog. Both files route every button through
    # one handleButton function, so the dispatch reads the same in each.
    def run(self):
        return self.complete(["&Close"], 0, self.onButton)

    def onButton(self, dlgSelf, button):
        return self.handleButton(lbc.stripMnemonic(button.GetLabel()))

    # ---- BLOCK 6: one place that knows what every button does ----
    #
    # Returning False means "the window stays open", which is what Add, Delete
    # and Report all want. Close is not here: answering True lets the dialog end
    # as any dialog does.
    def handleButton(self, sLabel):
        if sLabel == "Add": return self.addFruit()
        if sLabel == "Delete": return self.deleteFruit()
        if sLabel == "Report": return self.showReport()
        return True

    # ---- BLOCK 7: what the screen reader cannot know ----
    #
    # DECISION 5: A screen reader announces the window title when the dialog
    # opens and a control's name when focus arrives, so this program never says
    # those. It says what the reader cannot work out: that a fruit went in, that
    # one came out, how full the basket is now. say.say reaches JAWS, NVDA and
    # Narrator the same way, and this file does not have to know which is
    # running.
    def sayChange(self, sMessage):
        if not self.cbSpeak.GetValue(): return False
        say.say(sMessage)
        return True

    # DECISION 7: COUNTS THAT MATCH THEIR NOUNS. util.stringPlural agrees the
    # noun with the number, so "1 fruit" is never "1 fruits". An empty basket is
    # a real answer, said plainly, not an error and not silence.
    #
    # NOTE FOR THE READER WITH BOTH FILES OPEN: the Python helper returns only
    # the noun ("fruits"); the C# one returns the count and the noun together
    # ("3 fruits"). Same name, different shape, which is a wart rather than a
    # design. Each file uses its own correctly.
    def basketState(self):
        iCount = self.lbBasket.GetCount()
        if iCount == 0: return "the basket is empty"
        return str(iCount) + " " + util.stringPlural("fruit", iCount) + " in the basket"

    # ---- BLOCK 8: add a fruit ----
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
        self.saveBasket()
        self.sayChange(sFruit + " added, " + self.basketState())

        # DECISION 6: WHERE THE FOCUS GOES. Back to the field, because the next
        # thing a person does after adding a fruit is add another. Leaving the
        # focus on the button makes them find their way back every time, and
        # finding your way back is what costs a screen reader user their
        # afternoon.
        self.txtFruit.SetFocus()
        return False

    # ---- BLOCK 9: delete a fruit ----
    def deleteFruit(self):
        iFruit = self.lbBasket.GetSelection()
        if iFruit == wx.NOT_FOUND:
            say.say("No fruit is selected", True)
            self.lbBasket.SetFocus()
            return False
        sFruit = self.lbBasket.GetString(iFruit)
        log.info("Deleting %s from position %d" % (sFruit, iFruit))
        self.lbBasket.Delete(iFruit)

        # Select the neighbour, so the list still has somewhere to speak from. A
        # list with nothing selected says nothing, and a person who hears
        # nothing assumes the program has stopped.
        if iFruit > self.lbBasket.GetCount() - 1: iFruit = self.lbBasket.GetCount() - 1
        if iFruit >= 0: self.lbBasket.SetSelection(iFruit)
        self.saveBasket()
        self.sayChange(sFruit + " deleted, " + self.basketState())
        self.lbBasket.SetFocus()
        return False

    # ---- BLOCK 10: sort the basket ----
    #
    # Case-insensitively, which sorts the way a person expects rather than the
    # way a computer does: Apple and apple sit together instead of every capital
    # letter coming first. Lbc's C# side has sortedIgnoringCase for this; in
    # Python the key argument says the same thing in one line.
    def sortBasket(self, sKeep=""):
        if self.cboSort.GetValue() != "name":
            self.showState()
            return False
        lFruit = sorted([self.lbBasket.GetString(i) for i in range(self.lbBasket.GetCount())],
                        key=lambda s: s.lower())
        self.lbBasket.Set(lFruit)
        if lFruit:
            iKeep = lFruit.index(sKeep) if sKeep in lFruit else 0
            self.lbBasket.SetSelection(iKeep)
        self.showState()
        return True

    # ---- BLOCK 11: the report ----
    #
    # lbc.dialogText is the package's plain read-only window: a person arrows
    # through it line by line, copies from it, and closes it with Escape. It is
    # the same window the kit uses for any long answer, which is why a report
    # does not need one of its own.
    def showReport(self):
        lLines = ["Fruit basket report", ""]
        lLines.append(self.basketState() + ".")
        lLines.append("Sorted by " + self.cboSort.GetValue() + ".")
        lLines.append("")
        for iNumber in range(self.lbBasket.GetCount()):
            lLines.append(str(iNumber + 1) + ". " + self.lbBasket.GetString(iNumber))
        lLines.append("")
        lLines.append("Kept in " + settingsPath())
        lbc.dialogText("Fruit basket report", "", "\n".join(lLines))
        return False

    # DECISION 8: SAVE THE ANSWER THE MOMENT IT IS GIVEN, not at exit. A program
    # that saves on the way out loses everything when it is killed, and the
    # person who loses it is the one who just typed twenty fruits.
    def saveBasket(self):
        lFruit = [self.lbBasket.GetString(i) for i in range(self.lbBasket.GetCount())]
        inix.setValue(settingsPath(), c_sSection, "Fruit", ", ".join(lFruit))
        inix.setValue(settingsPath(), c_sSection, "Sort", self.cboSort.GetValue())
        inix.setValue(settingsPath(), c_sSection, "Speak", "1" if self.cbSpeak.GetValue() else "0")
        log.info("Saved %d to %s" % (len(lFruit), settingsPath()))
        return True

    # Delete from the list itself, where the hand already is when a person
    # decides a fruit should go.
    def basketKeyDown(self, oEvent):
        if oEvent.GetKeyCode() == wx.WXK_DELETE: self.deleteFruit()
        else: oEvent.Skip()

    # The window title carries the state, which is where a screen reader looks
    # first and where a sighted reader looks anyway. The C# file puts the same
    # sentence in Lbc's status line; wx dialogs have no status line, so the
    # title does the job.
    def showState(self):
        self.SetTitle("Fruit Basket -- " + self.basketState())
        return True


# ---- BLOCK 12: the way in ----
def main():
    # The log opens first, so a failure in anything after it is explainable.
    # One file per session, in %LOCALAPPDATA%\\FruitBasketPy\\logs, pruned to the
    # most recent thirty. Writing a line costs microseconds; not having the line
    # costs an evening.
    paths.start(c_sAppName)
    log.start(c_sAppName)
    log.keyValue("Settings file", settingsPath())
    log.keyValue("Results folder", paths.results())
    log.info("Cleared %d leftover temporary items" % paths.clearTemp())
    try:
        oApp = wx.App(False)
        dlgFruit = fruitDialog()
        dlgFruit.showState()
        dlgFruit.run()
        log.close()
        return 0
    except Exception:
        log.exception()
        log.close()
        raise


if __name__ == "__main__":
    sys.exit(main())
