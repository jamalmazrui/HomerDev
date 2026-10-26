# The Homer launch dialog

A **launch app** takes some source paths and a few settings, runs a process,
and writes files and folders into an output directory you name. 2htm, BatCon,
extCheck, HomerScribe, urlCheck and urlFido are launch apps. They all show one
dialog, built by the kit's `LaunchDialog` class in `exec\CSharp\Lbc.cs`, so
they look, sound and behave alike. This page says what that dialog is and why.

## The bands

A **band** is one row of controls, read and tabbed left to right. The bands
come in this order. A band with nothing in it is left out.

1. **Source.** The "Source paths" box, then the "Browse local source" button.
   The box holds one or more files, folders, patterns or web addresses,
   separated by spaces, with quotes around any that has a space. "Paths" is
   the word even for web addresses, because a list file or playlist can be
   given too.
2. **Transformations.** Checkboxes that choose what is done to the sources,
   such as HomerScribe's "Transcribe audio" and "Describe video".
3. **More choices.** Other controls that shape that work, such as BatCon's
   "Target format" list or urlFido's "File extensions" box.
4. **Output.** The "Output directory" box, then the "Choose output directory"
   button.
5. **Operation.** Checkboxes for the run as a whole, in alphabetical order:
   "Force replacements", "Use configuration" and "View output directory".
6. **Commands.** The "Default settings" and "Help" buttons, in alphabetical
   order. Neither closes the dialog for good: Help shows a box and returns, and
   Default settings opens the dialog again with everything as it was out of
   the box.
7. **Commit.** OK and Cancel, alone, at the bottom right.

## Force replacements

Force replacements works the same way in every launch app.

- **Unchecked,** a source whose result is already in the output directory is
  skipped and its result kept. The Results box counts them and says how to
  replace them: "Skipped 2 files whose results were already there. Check Force
  replacements, or use -f, to replace them."
- **Checked,** the work is done again, and the old result is kept aside until
  the new one is complete, so a run that fails never loses both. 2htm and
  urlFido move the old result aside and put it back on failure, BatCon writes
  the new result before replacing the old, urlCheck moves earlier reports
  aside, and extCheck writes its report only once checking is done.
- **On the command line** it is `-f` or `--force-replacements` (`--force` still
  works).
- **Its tip** is the same in every app, the kit's `LaunchDialog.forceTip`, and
  the Results line is the kit's `LaunchDialog.keptLine`.

**Where it sits.** It is the first checkbox of the operation band, before Use
configuration and View output directory, in alphabetical order. The other
place considered was the output band, after Choose output directory, since it
is about results already in the output directory. It stays in the operation
band for three reasons. First, View output directory is about the output too,
and it is in the operation band by the author's own layout; the two belong
together. Second, the output band then stays a box and its button, like the
source band, which keeps the two easy to learn as a pair. Third, Force
replacements changes how the whole run treats every source, which is what the
operation band is for.

## Why OK and Cancel stand alone

Microsoft's guidance for Windows dialogs (confirmed: the Windows 7 "Dialog
Boxes" and "Command Buttons" design guides, which Microsoft still publishes)
says three things that settle the last bands:

- Commit buttons go in one row along the bottom, aligned to the right.
- Only buttons that act on the whole window go in that row, and no other kind
  of control.
- Buttons that close the window should be clearly apart from buttons that do
  not.

OK and Cancel close the dialog. Help and Default settings do not, so they get
a band of their own above the row. The checkboxes are not buttons, so they
never sit in the row.

## Letters and keys

- **Alt letters.** The standard controls use the same letters in every app:
  S for Source paths, B for Browse local source, O for Output directory, C for
  Choose output directory, F for Force replacements, U for Use configuration,
  V for View output directory, D for Default settings and H for Help. An app's
  own control that comes earlier and already has one of these letters keeps
  it, by the Homer rule that the first control to claim a letter keeps it. The
  standard control then takes the first letter of its next word, or none.
- **OK and Cancel have no letter.** Control+Enter presses OK and Escape
  presses Cancel, from any control in the dialog.
- **F1** opens Help, the same as the Help button.
- **F11** checks the web for a newer version and offers to install it. It
  works from any control, though no control shows it, and the Help box says
  so.

## Opening and choosing folders

- The dialog opens with the focus in the Source paths box and its text
  selected, so typing replaces it and Tab leaves it alone. Insert+Tab says
  "Source paths" and the value.
- "Browse local source" and "Choose output directory" open where the box
  already points. When the box is empty or names a web address, they open in
  the Windows known folder for the kind of content: Documents for most apps,
  Videos for HomerScribe.

## Logs and results

- **Logging is automatic.** There is no log checkbox and no log switch. Every
  run writes a log in `%LOCALAPPDATA%\<App>\logs`, named
  `<App>-yyyyMMdd-HHmmss.log` for the date and time it started, so the newest
  is last in alphabetical order. The Help box says where.
- **Every run ends with a Results box**, titled "<App> Results". Its only
  button is OK, which has the focus, so Enter, Space or Escape closes it. Then
  the output directory opens, if View output directory is checked, and the app
  closes. The folder opens after the box rather than before it, so File
  Explorer does not take the focus away from the results. A long report shows
  its first 15 lines and gives the path of a file that holds the rest.

## While the work runs

After OK, a launch app shows the kit's progress window, `LaunchProgress`, until
the Results box. It follows these rules.

- **One window, named for where things stand.** Its title is the app's name and
  the latest status, such as "BatCon, Budget.pdf, 2 of 5 done". Alt+Tab, or the
  screen reader's Say Title command (Insert+T), answers "how far?" at any time.
- **A status box that holds the focus.** The window opens on a read-only
  "Status" box with the latest status, so Insert+Tab reads it again. The focus
  does not start on Cancel, because Microsoft's keyboard guidance says the
  opening focus should never be on a control with a destructive result.
- **Cancel, from anywhere.** The window's one button is Cancel, with no Alt
  letter; Escape presses it, and so does the window's close box. The app
  stops after the current item and says how many were left. Microsoft asks for
  a way to cancel any blocking job that takes longer than ten seconds.
- **Spoken only while the app is in front.** The screen reader speaks the
  status only while a window of the app is the one you are using. Switch to
  another program and the window keeps its title and status box up to date,
  but says nothing, so you can work without being talked over. Come back with
  Alt+Tab and it speaks the latest status once.
- **Not a torrent.** The first three messages, and every change of phase such
  as "Starting Edge", are spoken at once, so a run is never silent at the
  start. After that a step is spoken at most every five seconds, and the
  newest waiting message is the one you hear. Nothing spoken is longer than
  300 characters.
- **Counts say work done, with the percentage.** "Budget.pdf, 2 of 5 done,
  40%" while the third file runs, so 100 percent never shows while work is
  still going on. Work measured another way, such as minutes of a recording,
  says where it is and the percentage: "Film.mp4, 11 min, 23%".
- **Time left, when it can be estimated honestly.** Once a job has run 20
  seconds and finished something, the status adds "3 min left", or
  "under a minute left" near the end. Times are said the way HomerScribe says
  them: "11 min", "1 hour 5 min".
- **A progress bar, and the percentage spoken anyway.** The window has a real
  progress bar, as Microsoft asks. Microsoft keeps the percentage out of
  status text because the bar beside it already shows it. But a screen reader
  user hears a progress bar as a percentage, and "40%" is the quickest way to
  know how much is done and how much remains, which is what planning needs.
  So the percentage is in the spoken status, the title and the Status box. This
  is a deliberate departure from Microsoft's guidance, kept as small as it can
  be (confirmed: the author's ruling of 24 October 2026).
- **The message pump.** Setting text is not enough: until the message queue is
  pumped, Windows has not repainted the window or told the screen reader the
  title changed. Every status update pumps (`Application.DoEvents`), at most
  ten times a second, and a long silent step should call `pump()` now and
  then. The window's only command sets a flag, so pumping cannot start the
  work a second time.
- **The window keeps the focus.** It runs on a thread of its own, with its own
  message loop, so it answers Windows even while a long step runs, and the
  focus stays in its Status box for as long as you want to read it. Running on
  the working thread, it once stopped answering during a long step, and Windows
  moved the focus away (kit 1.93.6).
- **Every status is logged,** with a note when it was not spoken because the
  app was not in front, so the log shows exactly what you heard.

HomerScribe built these rules over months of describing films, and it keeps
its own richer window: it groups descriptions that arrive every few seconds,
and it can show its progress in the dialog itself. It uses the kit's
`LaunchProgress.isInFront` test, so all six apps decide when to speak the same
way.

## The command line

The command line uses the same names as the dialog. A switch's long form is
the control's label, and its short form is the control's Alt letter. Switches
may be written with a slash, one hyphen or two, in any case, and the guides
show them in lowercase.

- **Sources** are the paths given without a switch.
- `-o`, `--output-directory` names the output directory.
- `-f`, `--force-replacements` replaces results that are already there.
- `-u`, `--use-configuration` loads the saved settings, and in the dialog saves
  them at OK.
- `-v`, `--view-output-directory` opens the output directory when the run is
  done.
- `-d`, `--default-settings` forgets the saved settings.
- `-h`, `--help` shows the switches.

An app keeps its older spellings, such as `--force` or `--view-output`, as
other names for the same switch.

## Learnings from Microsoft's UWP guidelines

Microsoft's 2015 guidelines for Universal Windows Platform apps were mined for
what fits a Homer launch app (confirmed: the August 2015 PDF of the guidelines).
These points shaped the rules above or confirm them:

- **Progress after two seconds.** Show progress for anything that takes more
  than two seconds; the progress window opens at OK.
- **Cancel after ten.** A blocking job longer than ten seconds needs a way to
  cancel from the moment it starts.
- **Status text says what is happening.** Show the subject of the task and its
  status. Microsoft leaves the percentage to the progress bar; Homer speaks it
  too, because that is how a screen reader user receives a progress bar (see
  above).
- **Give time remaining, without false precision.** Microsoft's Windows 7
  progress guidance asks for time remaining in plain units, rounded.
- **Opening focus is never destructive.** Put the first focus where the user
  will most likely act, and never on a control that loses work.
- **Tab order follows reading order,** and static text is not a tab stop. A
  band's label is in its band, just before its field, but is not a tab stop.
- **Space activates the focused control, Enter the default, Escape closes.**
  The Results box and the launch dialog follow this.
- **Every control has a name, role, value and state** a screen reader can
  read, and dynamic content uses a live region (in WinForms, the kit's Say,
  which raises a UI Automation notification).
- **Don't change context without the user.** Nothing moves the focus or opens a
  window while the work runs, except the Results box at the end, which the
  user is waiting for.
- **Don't refresh what has not changed.** The window repeats nothing: a status
  that has not changed is not set, spoken or logged again.
- **Use dialogs for what must be read and acknowledged;** the Results box is
  one. Notifications that pop up elsewhere are for things the user did not
  start, so launch apps do not use them.
- **Labels go above controls or to their left, the same way throughout.** The
  launch dialog puts each label to the left of its box, in its band.

## Building one

In C#:

```csharp
using (LaunchDialog oLaunch = new LaunchDialog("BatCon"))
{
    oLaunch.sourcePick = "folder";
    oLaunch.addSourceBand(sSource, "Files, folders or patterns.", "Choose a folder of files.");
    oLaunch.dialog.addBand();
    ListBox lbTarget = oLaunch.dialog.addPickBox("&Target format:", lsTargets, sTarget, "The format to make.");
    oLaunch.dialog.endBand();
    oLaunch.addOutputBand(sOutput, "Where results go.", "Choose the output directory.");
    oLaunch.addOperationBands(bForce, "Replace results.", bUseConfig, "Save settings.", bView, "Open the folder.");
    string sButton = oLaunch.run();   // "OK", "Cancel" or "Default settings"
}
using (LaunchProgress oProgress = new LaunchProgress("BatCon", "Converting 5 files", delegate(string s) { Log.info(s); }))
{
    foreach (string sFile in lsFiles)
    {
        if (oProgress.cancelled) break;
        oProgress.step(Path.GetFileName(sFile), iDone, lsFiles.Count);   // "Budget.pdf, 2 of 5 done, 40%"
        convert(sFile);
        iDone++;
    }
}
LaunchDialog.finish("BatCon", sReport, iFailed > 0, bView ? sOutput : "");
```

From Python through Homer.dll (urlCheck), the same calls work on
`Homer.LaunchDialog`. Set `ownPickers` to `True` before adding the bands and
wire the two buttons yourself, because the Windows shell pickers can hang under
pythonnet.

## The check

The kit's homer-launch-dialog skill carries `checkLaunch.py`, which the kit's
check runs on every app. A launch app fails it when it does not build its
dialog with `LaunchDialog`, does not end with `LaunchDialog.finish` or
`LaunchDialog.showResults`, or still has a
retired control: a Guide button, a Log session checkbox, an Include
subfolders checkbox, or the old Browse source and Choose output captions. It
also fails an app that does not use `LaunchProgress`, or that still builds a
progress label with the StatusBar role, which screen readers do not reliably
speak.
