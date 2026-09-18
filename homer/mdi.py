r"""mdi.py -- the frame and child of a multiple-document app, in Python.

THIS MODULE AND CSharp\Mdi.cs ARE THE SAME CLASS IN TWO LANGUAGES. Same command
names, same keys, same title rule, same menus: MdiFrame and MdiChild, with
addMenu, addItem, finishMenus, runCommand, onCommand, windowTitles, sayWindows,
pickWindow, stepWindow, closeCurrent, closeOthers, runJob, changeSetting,
showAlternateMenu, showAbout, showDocumentation, setTitle and setStatusText.

WHAT THE FRAME GIVES YOU, and no app should write again:

    Alt+F1                about
    Alt+F10               alternate menu: every command in one filterable list
    Alt+Shift+C           change a setting, from a list of what is settable
    Alt+Shift+J           run a job, from a list of what is in the jobs folder
    Control+F1            key help: a key says what it would do
    Control+F4            close this window
    Control+Shift+F4      close all but this one
    Control+Shift+Tab     previous window
    Control+Tab           next window
    F1                    the guide
    F4                    current windows, as a pick list
    Shift+F4              say how many windows are open, and their titles

THE TITLE RULE. The frame carries the app name and nothing else; a child carries
what it is showing and nothing else. Windows merges a maximized child into the
frame caption, so a screen reader reading the title says each part once.
setTitle is the only way to set a child title, so the rule cannot be broken by
accident.

ONE HONEST NOTE ABOUT THIS FILE. lbc.Dialog builds a dialog, and a wx dialog
cannot be an MDI child, so the band layout below is written again here rather
than reused. Everything that makes a control accessible IS reused -- the label
handling, the accessible name, the list search on Control+J -- but the sizer
code is duplicated, which is the drift this kit exists to prevent. The fix is to
lift lbc.Dialog's building methods into a mixin that both a dialog and a panel
can use. It is recorded in self.md as the next refactor and has not been done.
"""

import os
import subprocess
import sys

import wx

from . import inix, lbc, log, paths, say, util


# --- the frame --------------------------------------------------------------

class MdiFrame(wx.MDIParentFrame):
    """One window holding many, with the commands every Homer MDI app has."""

    def __init__(self, sAppName):
        self.sAppName = (sAppName or "").strip() or "Homer"
        # THE FRAME CARRIES THE APP NAME AND NOTHING ELSE.
        wx.MDIParentFrame.__init__(self, None, title=self.sAppName, size=(1000, 700))
        self.dCommands = {}          # command -> (key string, summary)
        self.dSettable = {}          # setting -> (default, summary)
        self.dMenus = {}
        self.menuBar = wx.MenuBar()
        self.menuNow = None
        self.bKeyHelp = False
        self.Bind(wx.EVT_MENU, self._onMenu)

    # --- building the menus ---

    def addMenu(self, sTitle):
        """Start a top-level menu. The ampersand is the whole access key."""
        self.menuNow = wx.Menu()
        self.menuBar.Append(self.menuNow, lbc.fixLabel(sTitle))
        self.dMenus[lbc.stripMnemonic(sTitle)] = self.menuNow
        return self.menuNow

    def addItem(self, sCommand, sKey="", sSummary=""):
        """One command, with its key and its one-line summary.

        The command NAME is what onCommand receives, so an app dispatches on a
        sentence a person would say rather than on a control id. The summary is
        not decoration: it is the status tip, the key describer's answer, and
        the entry in the hotkey document, written once.
        """
        iId = wx.NewIdRef()
        sLabel = lbc.fixLabel(sCommand) + ("\t" + sKey if sKey else "")
        item = self.menuNow.Append(iId, sLabel, sSummary)
        self.dCommands[lbc.stripMnemonic(sCommand)] = (sKey, sSummary)
        self.Bind(wx.EVT_MENU, self._onMenu, id=iId)
        return item

    def addSeparator(self):
        if self.menuNow is not None: self.menuNow.AppendSeparator()
        return True

    def finishMenus(self):
        """Fill in the Window and Help menus the frame owns. Call once."""
        self.addMenu("&Window")
        self.addItem("Current Windows", "F4", "Pick an open window from a list.")
        self.addItem("Say Windows Open", "Shift+F4", "Say how many windows are open, and their titles.")
        self.addItem("Next Window", "Ctrl+Tab", "Go to the next window.")
        self.addItem("Previous Window", "Ctrl+Shift+Tab", "Go to the previous window.")
        self.addItem("Close Window", "Ctrl+F4", "Close this window.")
        self.addItem("Close All But Current Window", "Ctrl+Shift+F4", "Close every window but this one.")

        self.addMenu("&Help")
        self.addItem("Documentation", "F1", "Open the guide.")
        self.addItem("Run a Job", "Alt+Shift+J", "Pick a script from the jobs folder and run it.")
        self.addItem("Change a Setting", "Alt+Shift+C", "Change a setting and have it take effect now.")
        self.addItem("Alternate Menu", "Alt+F10", "Every command in one list you can filter.")
        self.addItem("Key Help Toggle", "Ctrl+F1", "A key says what it would do instead of doing it.")
        self.addItem("About", "Alt+F1", "The name, the version, and where this copy came from.")
        self.SetMenuBar(self.menuBar)
        return True

    # --- running a command ---

    def _onMenu(self, oEvent):
        for sCommand, (sKey, sSummary) in self.dCommands.items():
            item = self.menuBar.FindItemById(oEvent.GetId())
            if item is not None and lbc.stripMnemonic(item.GetItemLabelText()) == sCommand:
                return self.runCommand(sCommand)
        oEvent.Skip()

    def runCommand(self, sCommand):
        """The one way in. Key help turns a command into a description of itself."""
        log.info("Command: " + sCommand)
        if self.bKeyHelp:
            sKey, sSummary = self.dCommands.get(sCommand, ("", ""))
            say.say("%s. %s %s" % (sCommand, sKey, sSummary), True)
            return True
        try:
            if self.onCommand(sCommand): return True
            return self._frameCommand(sCommand)
        except Exception:
            log.exception()
            say.say(sCommand + " failed. The log has why.", True)
            return False

    def onCommand(self, sCommand):
        """The app's own commands. Answer True when you handled one."""
        return False

    def _frameCommand(self, sCommand):
        if sCommand == "About": return self.showAbout()
        if sCommand == "Alternate Menu": return self.showAlternateMenu()
        if sCommand == "Change a Setting": return self.changeSetting()
        if sCommand == "Close All But Current Window": return self.closeOthers()
        if sCommand == "Close Window": return self.closeCurrent()
        if sCommand == "Current Windows": return self.pickWindow()
        if sCommand == "Documentation": return self.showDocumentation()
        if sCommand == "Key Help Toggle":
            self.bKeyHelp = not self.bKeyHelp
            say.say("Key help on" if self.bKeyHelp else "Key help off", True)
            return True
        if sCommand == "Next Window": return self.stepWindow(1)
        if sCommand == "Previous Window": return self.stepWindow(-1)
        if sCommand == "Run a Job": return self.runJob()
        if sCommand == "Say Windows Open": return self.sayWindows()
        return False

    # --- the window commands ---

    def children(self):
        return [w for w in self.GetChildren() if isinstance(w, wx.MDIChildFrame)]

    def windowTitles(self):
        return [w.GetTitle() for w in self.children()]

    def sayWindows(self):
        lTitles = self.windowTitles()
        sCount = "%d %s open" % (len(lTitles), util.stringPlural("window", len(lTitles)))
        say.say(sCount + (": " + ", ".join(lTitles) if lTitles else ""), True)
        return True

    def pickWindow(self):
        lTitles = self.windowTitles()
        if not lTitles:
            say.say("0 windows open", True)
            return True
        sPick = lbc.dialogChoose("Current Windows", "", lTitles, 0)
        if sPick in lTitles: self.children()[lTitles.index(sPick)].Activate()
        return True

    def stepWindow(self, iDirection):
        lChildren = self.children()
        if len(lChildren) < 2:
            say.say("1 window open", True)
            return True
        frameNow = self.GetActiveChild()
        iNow = lChildren.index(frameNow) if frameNow in lChildren else 0
        lChildren[(iNow + iDirection) % len(lChildren)].Activate()
        return True

    def closeCurrent(self):
        frameNow = self.GetActiveChild()
        if frameNow is not None: frameNow.Close()
        return True

    def closeOthers(self):
        frameKeep = self.GetActiveChild()
        iClosed = 0
        for frameOne in self.children():
            if frameOne is frameKeep: continue
            frameOne.Close()
            iClosed += 1
        say.say("%d %s closed" % (iClosed, util.stringPlural("window", iClosed)), True)
        return True

    # --- jobs ---

    def jobFiles(self):
        """Every job, the user's first and the shipped ones after.

        A job is a script the user can run: .cmd, .ps1, .py, .js, .vbs, or
        whatever else this app knows how to run. The user's own live in the
        per-user tree so they survive an update; the shipped ones come with the
        program and are read-only.
        """
        lFound = []
        for sFolder in [paths.jobs(), paths.shippedJobs()]:
            try:
                for sName in sorted(os.listdir(sFolder)):
                    sPath = os.path.join(sFolder, sName)
                    if os.path.isfile(sPath) and sName not in [os.path.basename(s) for s in lFound]:
                        lFound.append(sPath)
            except OSError:
                pass
        return lFound

    def runJob(self):
        """Pick a job from a list and run it.

        A LIST, not a folder browser and not a command line. The list is the
        whole design: every job this program can run, in one place, reachable by
        first letter, with no path to type and nothing to remember.
        """
        lJobs = self.jobFiles()
        if not lJobs:
            say.say("0 jobs. Put a script in " + paths.jobs(), True)
            return True
        lNames = [os.path.basename(s) for s in lJobs]
        sPick = lbc.dialogChoose("Run a Job", "", lNames, 0)
        if sPick not in lNames: return True
        sJob = lJobs[lNames.index(sPick)]
        log.info("Running job: " + sJob)
        try:
            subprocess.Popen(['cmd', '/c', 'start', '', sJob], cwd=paths.results())
            say.say(os.path.basename(sJob) + " started", True)
        except Exception:
            log.exception()
            say.say("That job could not be started. The log has why.", True)
        return True

    # --- settings ---

    def settingsFile(self):
        return paths.configFile(self.sAppName + ".inix")

    def addSetting(self, sName, sDefault="", sSummary=""):
        """Declare a setting the user may change while the program is running.

        The app names what is settable; the frame does the rest -- the list, the
        reading, the writing, and the call back into the app. A setting nobody
        declared cannot be changed by accident, and one that is declared needs no
        dialog of its own.
        """
        self.dSettable[sName] = (sDefault, sSummary)
        return True

    def changeSetting(self):
        """Change a setting from a list, and have it take effect now.

        A LIST OF WHAT IS SETTABLE, not a text file to edit and not a dialog of
        twenty controls. Pick the setting, type the value, and the program acts
        on it immediately -- no restart, no hunting for the file, no chance of
        breaking the syntax.
        """
        sPath = self.settingsFile()
        lNames = sorted(self.dSettable.keys(), key=lambda s: s.lower())
        if not lNames:
            say.say("0 settings can be changed here", True)
            return True
        sName = lbc.dialogChoose("Change a Setting", "", lNames, 0)
        if sName not in self.dSettable: return True
        sDefault, sSummary = self.dSettable[sName]
        sNow = inix.getValue(sPath, "Settings", sName, sDefault)
        sValue = lbc.dialogInput("Change a Setting", sName + ":", sNow)
        if sValue is None: return True
        inix.setValue(sPath, "Settings", sName, sValue)
        log.info("Setting %s = %s" % (sName, sValue))
        self.onSettingChanged(sName, sValue)
        say.say("%s is now %s" % (sName, sValue), True)
        return True

    def settingValue(self, sName):
        """What a declared setting is set to now."""
        sDefault, sSummary = self.dSettable.get(sName, ("", ""))
        return inix.getValue(self.settingsFile(), "Settings", sName, sDefault)

    def onSettingChanged(self, sName, sValue):
        """The app acts on the new value here. Nothing restarts."""
        return False

    # --- help ---

    def showAlternateMenu(self):
        lCommands = sorted(self.dCommands.keys(), key=lambda s: s.lower())
        if not lCommands:
            say.say("0 commands", True)
            return True
        sPick = lbc.dialogChoose("Alternate Menu", "", lCommands, 0)
        if sPick in self.dCommands: self.runCommand(sPick)
        return True

    def showAbout(self):
        lLines = [self.sAppName,
                  "Version: " + self._version(),
                  "Program: " + paths.installedFolder(),
                  "Settings and logs: " + paths.userFolder(),
                  "This session's log: " + log.sPath]
        lbc.dialogText("About " + self.sAppName, "", "\n".join(lLines))
        return True

    def _version(self):
        try:
            from . import version
            return getattr(version, "sVersion", "unknown")
        except Exception:
            return "unknown"

    def showDocumentation(self):
        sGuide = os.path.join(paths.shippedHelp(), self.sAppName + ".htm")
        if not os.path.isfile(sGuide):
            sGuide = os.path.join(paths.installedFolder(), "ReadMe.htm")
        if not os.path.isfile(sGuide):
            say.say("The guide was not found beside the program", True)
            return True
        try:
            os.startfile(sGuide)
        except Exception:
            log.exception()
        return True


# --- the child --------------------------------------------------------------

class MdiChild(wx.MDIChildFrame):
    """One window showing one thing, built a band at a time."""

    def __init__(self, frameParent):
        wx.MDIChildFrame.__init__(self, frameParent, title="")
        self.frameParent = frameParent
        self.sSubject = ""
        self.sView = ""
        self.dControls = {}
        self.dTips = {}
        self.panel = wx.Panel(self)
        self.sizerStack = wx.BoxSizer(wx.VERTICAL)
        self.sizerBand = None
        self.labelStatus = wx.StaticText(self.panel, label="")
        self.addBand()

    # --- layout ---

    def addBand(self):
        """A band is one horizontal row. Controls added after it share the row."""
        if self.sizerBand is not None:
            self.sizerStack.Add(self.sizerBand, 0, wx.GROW | wx.ALL, 4)
        self.sizerBand = wx.BoxSizer(wx.HORIZONTAL)
        return True

    def _place(self, control, iProportion=0):
        self.sizerBand.Add(control, iProportion, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)
        return control

    def _remember(self, sName, control):
        self.dControls[sName] = control
        return control

    def addInputBox(self, sLabel="", sValue="", sTip=""):
        """A labelled single line field.

        The label is copied into the field's accessible name. A label beside a
        text control is not automatically announced as that control's name, so
        removing that line silently makes the field anonymous.
        """
        self._place(wx.StaticText(self.panel, label=lbc.fixLabel(sLabel)))
        textCtrl = wx.TextCtrl(self.panel, value=str(sValue), size=(240, -1))
        textCtrl.SetName(lbc.stripMnemonic(sLabel))
        self.dTips[textCtrl] = sTip
        return self._remember(lbc.stripMnemonic(sLabel), self._place(textCtrl, 1))

    def addButton(self, sLabel="", functionClick=None):
        button = wx.Button(self.panel, label=lbc.fixLabel(sLabel))
        if functionClick is not None:
            button.Bind(wx.EVT_BUTTON, lambda oEvent: functionClick())
        return self._remember(lbc.stripMnemonic(sLabel), self._place(button))

    def addListBox(self, sLabel="", lNames=None, sTip=""):
        """A labelled list, with Control+J to search inside it and F3 to repeat.

        The search comes from lbc, which is the point: the behaviour is shared
        even where the layout is not.
        """
        self.addBand()
        self._place(wx.StaticText(self.panel, label=lbc.fixLabel(sLabel)))
        self.addBand()
        listBox = wx.ListBox(self.panel, choices=list(lNames or []), size=(400, 260))
        listBox.SetName(lbc.stripMnemonic(sLabel))
        lbc.ListSearch.bind(listBox)
        self.dTips[listBox] = sTip
        return self._remember(lbc.stripMnemonic(sLabel), self._place(listBox, 1))

    def finishLayout(self):
        """Size to what was added and put the status line at the foot."""
        if self.sizerBand is not None:
            self.sizerStack.Add(self.sizerBand, 0, wx.GROW | wx.ALL, 4)
            self.sizerBand = None
        self.sizerStack.Add(self.labelStatus, 0, wx.GROW | wx.ALL, 4)
        self.panel.SetSizer(self.sizerStack)
        self.panel.Layout()
        for control in self.dControls.values():
            if isinstance(control, (wx.TextCtrl, wx.ListBox)):
                control.SetFocus()
                break
        return True

    # --- the title rule ---

    def setTitle(self, sSubject, sView=""):
        """What this window is showing. THE CHILD CARRIES NO APP NAME."""
        self.sSubject = sSubject or ""
        self.sView = sView or ""
        self.SetTitle(self.sSubject if not self.sView
                      else "%s - %s" % (self.sSubject, self.sView))
        return True

    def setStatusText(self, sText):
        self.labelStatus.SetLabel(sText or "")
        return True

    def findControl(self, sName):
        return self.dControls.get(sName)
