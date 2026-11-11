r"""_APP_.py -- a Homer MDI app in Python: one frame, a window for each thing you work on.

This is the HomerDev starter for a multiple-window app written in Python, the
twin of the C# starter _APP_Mdi.cs. "newHomerApp _APP_ --mdi --python" wrote it
with your app's name in place. It builds the very Homer.MdiFrame, MdiChild and
KeyMap a C# app does, from the kit's exec\Homer.dll through pythonnet, so every
key the Homer suite shares already works -- F4 for the window list, Control+F1
for the Key Describer, Alt+F10 for the Alternate Menu, F1 for the guide, the
clipboard family and the rest -- and every fix to the kit's frame reaches this
app on its next build.

The worked example with every feature is Templates\samples\FruitBasketMdiPy.py
in the kit; the guide is help\MdiFramework.md there.

------------------------------------------------------------------- AI NOTE
If you are an AI asked to turn this into a working program, keep these rules.

  * DECLARE, DON'T HANDLE KEYS. Every command is one mdi.addCommand call: the
    frame, a caption with its ampersand letter, its keys in Homer spelling
    ("Alt+Shift+A", "Shift+R or F2", "" for none), a one-line summary, and
    the Python function that does the work. Never handle a key yourself: the
    kit's router decides where every key goes, keeps typing in text boxes, and
    keeps first-letter navigation in lists.
  * A HOTKEY'S LETTER IS THE FIRST LETTER OF A WORD IN ITS NAME, and so is a
    menu's ampersand letter. Never bind Alt+Control with a letter, digit,
    function key or punctuation. The kit logs any key Windows or a screen
    reader owns.
  * THE SUITE'S SHARED KEYS ARE TAKEN BY THE FRAME: F1, Shift+F1, Alt+F1,
    Control+F1, Control+Shift+F1, Alt+Shift+F1, F4, Shift+F4, Control+F4,
    Control+Shift+F4, Control+Tab, Alt+F10, Alt+Shift+H, Alt+Shift+E,
    Control+Shift+I, Alt+Apostrophe, Control+Apostrophe,
    Alt+Shift+Apostrophe, Alt+Shift+Apostrophe, Alt+SemiColon, F11,
    Control+F12.
  * A COMMAND THAT CANNOT RUN SAYS WHY: pass fnUnavailable, a function
    returning "" when it can run, or the reason when it cannot.
  * SAY COMMANDS USE mdi.answer(sTitle, part, part...): one press speaks the
    parts, a quick second press spells them, a third shows them in a window.
  * A LIST WHERE SHIFT PLUS A LETTER RUNS COMMANDS is passed to the window's
    manageList, and those commands get sContext=Homer.KeyMap.sListContext.
  * THE TITLE RULE: the frame is titled with the app name only; a window with
    what it shows only (setTitle), never the app name again.
  * Speak only what the screen reader cannot know.
  * Camel Type: sString, iInteger, bBoolean, lsList, dDictionary, oObject;
    lowerCamel functions; double quotes; no c_ prefix on constants.
---------------------------------------------------------------------------
"""

import sys

import mdi

sAppName = "_APP_"
Homer = None


class AppWindow:
    """One window: an item field and a list of items."""

    def __init__(self, app, sName):
        from System import String
        from System.Collections.Generic import List
        self.child = Homer.MdiChild(app.frm)
        self.txtItem = self.child.lbc.addInputBox("&Item:", "", "Type an item, then press Alt+Shift+A to add it.")
        self.lbItems = self.child.lbc.addPickBox("&List:", List[String](), "", "The items in this window.")
        self.child.finishLayout()
        self.child.manageList(self.lbItems)
        self.child.setTitle(sName, "empty")
        self.txtItem.Focus()

    def addItem(self):
        sItem = self.txtItem.Text.strip()
        if sItem == "":
            Homer.Say.sayForced("Type an item first")
            self.txtItem.Focus()
            return True
        self.lbItems.Items.Add(sItem)
        self.lbItems.SelectedIndex = self.lbItems.Items.Count - 1
        self.txtItem.Text = ""
        iCount = self.lbItems.Items.Count
        self.child.setTitle(self.child.subject, "1 item" if iCount == 1 else "%d items" % iCount)
        Homer.Say.sayForced(sItem + " added")
        return True

    def sayPosition(self):
        iCount = self.lbItems.Items.Count
        if iCount == 0:
            return mdi.answer("Position", "0 items")
        iItem = self.lbItems.SelectedIndex
        if iItem < 0:
            return mdi.answer("Position", "No item is selected")
        iPercent = int(round(100.0 * (iItem + 1) / iCount))
        return mdi.answer("Position", "Item %d of %d" % (iItem + 1, iCount), "%d percent" % iPercent)


class App:
    def __init__(self):
        self.lsWindows = []
        self.iWindows = 0
        frm = Homer.MdiFrame(sAppName)
        self.frm = frm
        frm.addMenu("&File")
        mdi.addCommand(frm, "&New Window", "Control+N", "Open another window.", self.newWindow)
        mdi.addCommand(frm, "&Exit", "Alt+F4", "Close every window and leave.", lambda: frm.Close())
        frm.addMenu("&Edit")
        mdi.addCommand(frm, "&Add Item", "Alt+Shift+A", "Put what is in the item field into the list.",
                       lambda: self.withWindow(lambda w: w.addItem()),
                       fnUnavailable=lambda: "no window is open" if self.active() is None else "")
        frm.addMenu("&Query")
        mdi.addCommand(frm, "Say &Position", "Alt+Delete", "Say which item you are on, of how many, and how far through.",
                       lambda: self.withWindow(lambda w: w.sayPosition()), sRepeat="review")
        frm.finishMenus()
        self.newWindow()

    def active(self):
        from System import Object
        for w in self.lsWindows:
            if Object.ReferenceEquals(w.child, self.frm.ActiveMdiChild):
                return w
        return None

    def withWindow(self, fnWork):
        w = self.active()
        if w is None:
            Homer.Say.sayForced("No window is open")
            return True
        return fnWork(w)

    def newWindow(self):
        self.iWindows += 1
        w = AppWindow(self, "Window %d" % self.iWindows)
        self.lsWindows.append(w)
        w.child.FormClosed += lambda oSender, evArgs: self.lsWindows.remove(w) if w in self.lsWindows else None
        w.child.Show()
        return True


def main():
    global Homer
    Homer = mdi.load()
    Homer.Paths.start(sAppName)
    Homer.Log.start(sAppName)
    try:
        iCode = mdi.run(App().frm)
        Homer.Log.close()
        return iCode
    except Exception:
        mdi.logException(sAppName + " stopped on an error.")
        Homer.Log.close()
        raise


if __name__ == "__main__":
    sys.exit(main())
