r"""lbcnet.py -- part of the shared Homer toolkit.

THE C# LBC, FROM PYTHON, THROUGH PYTHONNET.

Every Homer dialog is built from Lbc primitives on the 64-bit WinForms API.
A Python app with a WinForms interface (urlCheck, helpFido) does not get a
second Lbc written in Python: it loads exec\Homer.dll, which buildHomerDev
compiles from the kit's own CSharp\Elevate, Inix, Lbc, Log, Paths, Say, Util
and Web, and builds its dialogs with the very LbcDialog the C# apps use. The
focus order, the access keys, Control+Enter, Shift+F1, F7, the editing keys
and the Help box with its version check are therefore the same in both
languages by construction, and every fix to Lbc.cs reaches the Python apps on
their next build.

homer\lbc.py stays what it is: Lbc for wxPython, for code that must run
inside NVDA, where WinForms is not available.

    from homer import lbcnet
    Homer = lbcnet.load()                  # the Homer namespace, or None
    Homer.Elevate.configure("JamalMazrui", "urlCheck", sVersion)
    dlg = Homer.LbcDialog("urlCheck", None)
    tbSource = dlg.addInputBox("&Source urls:", "", "One or more urls.")
    dlg.commandKey = lbcnet.keyHandler(fnOnKey)      # fnOnKey(keys) -> bool
    sButton = dlg.runWithButtons(lbcnet.strings(["OK", "Cancel"]))
    dlg.Dispose()

WHERE Homer.dll IS LOOKED FOR, first found wins:
  1. PyInstaller's unpack folder, sys._MEIPASS: the build bundles it there
     (build_APP_Py.cmd, homerDll=1).
  2. Beside the program, and in an exec folder beside it.
  3. The kit's own exec folder, found from this module's location, for a run
     of the .py from the project.

THE THREAD. WinForms common dialogs need a single-threaded apartment. A C#
program gets one from [STAThread]; here load() sets it on the calling thread,
which must be the one that shows the dialogs. It fails harmlessly, and says so
in the log, if COM was already started in the other mode.
"""

import os
import sys

from homer import log

c_sDllName = "Homer.dll"

oHomer = None
sLoadedFrom = ""


def candidates():
    """Every place Homer.dll may be, in the order they are tried."""
    lsFolders = []
    sBundle = getattr(sys, "_MEIPASS", "")
    if sBundle: lsFolders.append(sBundle)
    sProgram = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, "frozen", False) else sys.argv[0]))
    lsFolders.append(sProgram)
    lsFolders.append(os.path.join(sProgram, "exec"))
    sKit = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    lsFolders.append(os.path.join(sKit, "exec"))
    return [os.path.join(sFolder, c_sDllName) for sFolder in lsFolders]


def load():
    """Load Homer.dll once and return the Homer namespace, or None with the reason logged."""
    global oHomer, sLoadedFrom
    if oHomer is not None: return oHomer
    sPath = ""
    for sCandidate in candidates():
        if os.path.isfile(sCandidate):
            sPath = sCandidate
            break
    if sPath == "":
        log.error("Homer.dll was not found; looked in: " + "; ".join(candidates()))
        return None
    try:
        import clr  # provided by the pythonnet package
        clr.AddReference("System.Windows.Forms")
        clr.AddReference("System.Drawing")
        clr.AddReference(sPath)
        import Homer as oNamespace
        from System.Threading import ApartmentState, Thread
        from System.Windows.Forms import Application
    except Exception as oError:
        log.error("Homer.dll could not be loaded from %s: %s" % (sPath, oError))
        return None
    try:
        oThread = Thread.CurrentThread
        sBefore = str(oThread.GetApartmentState())
        oThread.SetApartmentState(ApartmentState.STA)
        log.info("Thread apartment state: %s -> %s" % (sBefore, oThread.GetApartmentState()))
    except Exception as oError:
        log.warn("SetApartmentState(STA) failed, continuing: %s" % oError)
    try:
        Application.EnableVisualStyles()
        Application.SetCompatibleTextRenderingDefault(False)
    except Exception:
        pass
    oHomer = oNamespace
    sLoadedFrom = sPath
    log.info("Homer.dll loaded from " + sPath)
    return oHomer


def strings(lsValues):
    """A Python list of text as the .NET string[] that runWithButtons and friends take."""
    from System import Array, String
    return Array[String]([str(sValue) for sValue in lsValues])


def keyHandler(fnHandler):
    """A Python function taking a Keys value and returning True when it handled
    the key, as the Func<Keys, bool> that LbcDialog.commandKey takes."""
    from System import Boolean, Func
    from System.Windows.Forms import Keys
    return Func[Keys, Boolean](lambda keys: bool(fnHandler(keys)))
