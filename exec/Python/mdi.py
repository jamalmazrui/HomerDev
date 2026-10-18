r"""mdi.py -- the Homer MDI frame, from Python.

THE SAME FRAME, NOT A SECOND ONE (kit 1.73.6). Until 1.73.6 this file was a
wxPython copy of the frame, and it drifted from the C# one: it still used the
old keys (Alt+Shift+C for settings, Alt+Shift+S for scripts) and had none of the
key router, the managed lists, the Say and clipboard commands, or the double
press. Now a Python app uses the very classes a C# app does -- Homer.MdiFrame,
Homer.MdiChild and Homer.KeyMap -- loaded from the kit's exec\Homer.dll through
pythonnet, as lbcnet.py already does for dialogs. Every fix to Mdi.cs or
KeyMap.cs reaches Python on its next build, and the two languages cannot drift.

What this module adds is only what Python needs to talk to them: a Python
function wrapped as the delegate a command runs, a Python function wrapped as an
"unavailable because" check, and answer() taking its parts as Python arguments.

    import mdi
    Homer = mdi.load()
    frm = Homer.MdiFrame("FruitBasketMdiPy")
    frm.addMenu("&File")
    mdi.addCommand(frm, "&New Basket", "Control+N", "Open another basket.", newBasket)
    frm.finishMenus()
    sys.exit(mdi.run(frm))

The guide is help\MdiFramework.md in the kit; the worked example is
Templates\samples\FruitBasketMdiPy.py, the twin of FruitBasketMdiCs.cs.

lbc.py stays as it is: Lbc for wxPython, for code that must run inside NVDA,
where WinForms is not available. Camel Type throughout.
"""

import ctypes
import traceback

import lbcnet
import log

Homer = None


def load():
    """Load Homer.dll and return the Homer namespace.

    When it cannot be loaded there is no frame to speak through, so the
    reason goes in a Python log and a Windows message box, and the program
    ends rather than half start."""
    global Homer
    if Homer is not None:
        return Homer
    Homer = lbcnet.load()
    if Homer is None:
        log.start("HomerMdi")
        log.error("Homer.dll could not be loaded, so the Homer frame cannot start.")
        ctypes.windll.user32.MessageBoxW(None, "Homer.dll could not be loaded, so this program cannot start. "
                                         "The log in the program's logs folder says why.", "Homer", 0x10)
        raise SystemExit(1)
    return Homer


def action(fnWork):
    """A Python function as the Func<bool> a command runs. A command that
    returns nothing counts as done."""
    from System import Boolean, Func

    def runIt():
        oResult = fnWork()
        return True if oResult is None else bool(oResult)
    return Func[Boolean](runIt)


def reason(fnReason):
    """A Python function as the Func<string> an "unavailable because" check is:
    an empty string when the command can run, else the reason it cannot."""
    from System import Func, String
    return Func[String](lambda: str(fnReason() or ""))


def addCommand(frm, sCaption, sKeys, sSummary, fnRun, sContext="", fnUnavailable=None, sRepeat=""):
    """One command on the frame's current menu, as MdiFrame.addCommand, with
    the optional parts given by name. Returns the KeyMap.Command."""
    oCommand = frm.addCommand(sCaption, sKeys, sContext or Homer.KeyMap.sAnywhere, sSummary, action(fnRun))
    if fnUnavailable is not None:
        oCommand.fUnavailable = reason(fnUnavailable)
    if sRepeat:
        oCommand.sRepeat = sRepeat
    return oCommand


def answer(sTitle, *lsParts):
    """KeyMap.answer: one press speaks the parts as separate utterances; a
    quick second press shows them in a window to review and copy."""
    return Homer.KeyMap.answer(sTitle, lbcnet.strings([str(s) for s in lsParts]))


def run(frm):
    """MdiFrame.runOrExport: run the frame, or, after /exportkeys, end at
    once without a window. Returns the exit code."""
    return int(Homer.MdiFrame.runOrExport(frm))


def logException(sWhat):
    """A Python error into the frame's log, with its traceback."""
    if Homer is not None:
        Homer.Log.error(sWhat + "\n" + traceback.format_exc())
    return True
