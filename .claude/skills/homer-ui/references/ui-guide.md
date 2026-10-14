# The Homer interface, from HomerDev.md

Copied by the kit's build from help/HomerDev.md; edit that, not this.

## Contents

- Lbc: building a dialog
- Keys and key names
- Direct speech across screen readers
- Three kinds of Homer app

## Lbc: building a dialog

Lbc stands for Layout By Code. A Homer dialog is never drawn in a designer. It
is assembled in code out of ordinary Windows controls, each created with its
label, its accessible name and its tab position already correct.

The reason is simple. A designer places controls by pixel, and the tab order
ends up being whatever the mouse happened to do. Lbc has one rule instead:

> **Add order is focus order.**

The order the `add` calls appear in is the order the user tabs through, which is
the order the dialog is read in, and the layout follows from that rather than
the other way round. When the order is wrong, the fix belongs in Lbc or in the
order of the calls, never in a pile of `TabIndex` assignments in the app.

### The shape of a dialog

    using (LbcDialog dlg = new LbcDialog("Find", frm))
    {
        TextBox tbFind = dlg.addInputBox("&Find what:", sLast,
            "The text to look for. The last ten searches are remembered.");
        CheckBox cbCase = dlg.addCheckBox("Match &case", bCase,
            "Off means a and A are the same.");
        if (!dlg.runOkCancel()) return false;
        sFind = tbFind.Text;
        bCase = cbCase.Checked;
    }

That is the whole pattern. The dialog is disposable, every `add` returns the
real control so you can read it afterwards, and `runOkCancel` returns true when
the user accepted.

### What you can add

Every one of these takes a label with an `&` before its access-key letter, and
most take a tip that appears in the dialog's status bar when focus arrives and
in the Help box.

- `addLabel` -- a line of text.
- `addInputBox`, `addTextLine`, `addInlineInputBox` -- a single-line box. The
  inline form puts the label and box on one row.
- `addMemoBox`, `addTextMemo`, `addMemo` -- a multi-line box. A memo eats a
  bare Enter, which is why Control+Enter also accepts the dialog.
- `addCheckBox` -- a true or false answer.
- `addRadioButton` -- one of several.
- `addListBox`, `addPickBox` -- a list to choose one item from.
- `addCheckListBox` -- a list to tick several items in.
- `addComboBox`, `addComboPickBox`, `addComboEditBox`, `addComboHistoryBox` --
  a combo box; the history form is prefilled with recent answers.
- `addNumericUpDown` -- a number with arrows.
- `addButton` -- a push button on the current band.
- `addSeparator` -- a divider, which also closes an open band.

### Bands

By default each control sits on its own row. A band puts several on one row,
which is what you want for a field and the button that fills it in:

    dlg.addBand();
    TextBox tbSource = dlg.addInputBox("&Source:", sSource, "The file to work on.");
    Button btnBrowse = dlg.addButton("&Browse source...", "Pick it from a dialog.");
    dlg.endBand();

A band changes only the arrangement. The tab order is still the order of the
calls.

### Showing it

- `runOkCancel()` -- OK and Cancel; returns true on OK.
- `runWithButtons(new string[] { "Default settings", "OK", "Cancel" })` --
  returns the label of the button pressed, or an empty string if the user
  pressed Escape or closed the window.
- A **Help** button is added for you and placed rightmost, per Windows layout.
  It lists every field with its tip, then the universal dialog keys. F1 does
  the same.
- **Enter** presses the button that means accept, wherever it sits in the row,
  and **Control+Enter** does it from any control including a memo.
  **Escape** cancels.
- OK and Cancel deliberately get no access key: their keys are Enter and
  Escape, and an unnecessary Alt+O would take a letter another button may want.

### Other pieces

- `LbcTextBox` is the text box the boxes above are made of. It carries the
  convenience keys: copy or cut the current line with no selection, mark a
  selection in two keystrokes with F8 and Shift+F8, copy all with Control+F8,
  read all with Alt+F8, delete the line with Control+D, and open what is under
  the cursor with Shift+F5.
- `HelpDialog.show(owner, sTitle, sText)` is the plain read-only box: help
  text, results, a query answer. The user arrows through it line by line.
- `HelpDialog.showRecordView` is the same box with record navigation, for
  stepping through one record at a time.
- `LbcInixForm` builds a whole dialog from an `.inix` file describing the
  fields, and writes the answers back to one. It is how a form can be defined
  as data instead of code.
- `setStatusText` writes to the dialog's status line; `setInitialFocus` says
  which control opens with the focus.

### Opening focus

The field that opens with the focus has its value selected, so typing or
pasting replaces it and Tab leaves it alone. A **multi-line** box is the
exception: its caret opens on the first line, because its value is a document
rather than a field.

## Keys and key names

### One spelling

`KeyName.cs` holds the one spelling for every key, taken from how Freedom
Scientific writes key names in the JAWS key map files, with three Homer rules
on top:

- **Modifiers in alphabetical order**: Alt, Control, Shift, Windows. So
  `Alt+Control+Shift+F` and never `Shift+Control+Alt+F`.
- **"Control" spelled out**, never "Ctrl".
- **The screen reader key is "JAWS" or "NVDA"**, not "JAWSKey". On both readers
  it is usually Insert or CapsLock.

Then convert to whatever an API wants, rather than writing that table again:

    KeyName.toJawsKeyMap("Alt+Shift+H")    // for a .jkm file
    KeyName.toNvdaGesture("Alt+Shift+H")   // for an NVDA gesture
    KeyName.toWinFormsText("Alt+Shift+H")  // for a menu item's shortcut text
    KeyName.toWinFormsKeys("Alt+Shift+H")  // the .NET Keys value
    KeyName.toWx("Alt+Shift+H")            // for wxPython
    KeyName.toInnoHotKey("Alt+Shift+H")    // for an installer shortcut
    KeyName.toSpoken("Alt+Shift+H")        // for speech and documentation

`KeyName.same()` compares two spellings of the same key, and `KeyName.parse()`
normalizes one.

### Choosing a key

- **Give it a mnemonic**: the first letter of a word in the command's name.
- **Do not take a key Windows has already given a meaning**, especially one
  about selection or navigation.
- **Never use Alt+Control combinations.** That space belongs to Windows desktop
  shortcuts, function keys included. A desktop shortcut's own hotkey is the one
  sanctioned use of it.
- **Prefer Alt+Shift plus a letter** when dropping the screen reader modifier.
  Chromium fires a web page's access key on Alt+letter, and does not on
  Alt+Shift+letter.
- **Aim for one key that works on both JAWS and NVDA.** Perfect agreement is not
  realistic; keeping the differences few is.

### KeyMap

`KeyMap.cs` is the one table associating a context, a command name, a summary,
a longer description and a key. The menus, the alternate menu, the key
describer and the hotkey document all read from it, so a command is described
once and every surface agrees.

    KeyMap.register("Find Record", Keys.Control | Keys.F, mnuFind, "Grid");
    KeyMap.setSummary("Find Record", "Search every column for text.");

`KeyMap.lsConflicts` lists any key claimed twice, which is worth showing in a
developer command rather than discovering in use.

## Direct speech across screen readers

A Windows program cannot count on a screen reader noticing everything. Focus
changes and window titles it will announce by itself. A result, a count, a
status, a thing that happened in the background -- those it cannot know about.

`Say.cs` is the one way a Homer app says such a thing, and it works the same
whichever reader is running.

    using Homer;

    Say.attach(frm);              // once, at startup, on the main form
    Say.say("12 rows marked");    // spoken if speech is interrupted anyway
    Say.sayForced("Backup finished");   // spoken even mid-sentence
    Say.sayParts("Row 4", "Title", "The Sea Around Us");

### How it reaches the reader

`sayForced` tries each route in turn and stops at the first that works.

1. **JAWS**, through its COM interface. This is the most reliable route when
   JAWS is running, and it respects the user's own speech settings.
2. **NVDA**, through `nvdaControllerClient.dll`, the controller client NV
   Access publishes for exactly this.
3. **A UI Automation notification event**, raised from a hidden provider
   control. This is what reaches Narrator, and it also reaches any other
   assistive technology that listens for notifications.
4. **SAPI**, the Windows voices, and only if the app turns it on with
   `Say.bUseSapiAsBackup`. It is off by default, because a second voice talking
   over the user's screen reader is worse than silence.

`Say.speechDiagnostic()` reports which routes are available on this machine and
`Say.lastSpeechPath()` reports which one the last message actually took. Both
belong in an app's Help or About, so a user can say what happened.

### What to speak, and what not to

- **Do not repeat what the reader already says.** It announces a dialog's title
  when the dialog opens and a control's name when focus lands on it. An app
  that says these too makes the user hear everything twice.
- **Do not set a control's accessible-name property to its own caption or to
  the label before it.** Same fault, same cause. That property is for a control
  with no visible text.
- **Report only what happened this session.** A summary that lists what the
  program can do, rather than what it just did, teaches a user to ignore
  summaries.
- **Match the noun to the count.** "1 file", not "1 files". A count of zero is a
  real answer: "0 matches" is information, not an error.

## Three kinds of Homer app

Every Homer program is one of three shapes. They share far more than they
differ, and what they share is the whole of this kit: the same classes, the same
folder layout, the same session log, the same settings format, the same key
conventions, the same document set, the same build, installer and release
scripts, and the same evidence checks. What differs is only how the program
meets the person.

### One: a single tool, with a command line and a dialog

One independent 64-bit executable that does one job. It answers `--help`, it can
be scripted from a batch file or a scheduled task, and with no arguments -- or
with `--gui` -- it opens one Lbc dialog instead.

Both modes take the same settings and write the same log, so a person can learn
the dialog and then automate what they learned. `FruitBasketCs.cs` and
`FruitBasketPy.py` are this shape.

The flags are the same in every Homer tool of this kind:

- `--help` -- what it does and every switch, to standard output, exit code 0
- `--gui` -- open the dialog even when arguments were given
- `--version` -- the version and nothing else
- `--log` -- say where this session's log is
- an unknown switch is refused with exit code 1 rather than ignored

### Two: a desktop program that could not be a command line

The same single-window shape, but graphical only, because of what it carries: a
local AI model, a browser engine, a media pipeline, a speech stack. HomerScribe
is this. The dependencies decide the shape, not the interface.

It should still answer `--help` and still take arguments where that is
meaningful, but it does not promise that every feature works without the
desktop. Say so in its guide rather than leaving somebody to discover it.

### Three: a multiple-document program

One frame holding many windows, each showing one thing: a file in EdSharp, a
folder in FileDir, a table in DbDo, a basket in `FruitBasketMdi.cs`.

Use this shape when a person genuinely works on several things at once, and not
otherwise. A window is a first-class object to a screen reader -- Alt+Tab
reaches it, the window list names it, its title is announced when it activates,
and it keeps its own state. A tabbed interface has to reimplement all of that,
usually badly. That is the argument for MDI, and it is the only one needed.

`MdiFrame` and `MdiChild` in `Mdi.cs` carry the frame, so an app writes its own
commands and nothing else. Free with the frame:

- F4 -- current windows, as a pick list
- Shift+F4 -- say how many windows are open, and their titles
- Control+Tab and Control+Shift+Tab -- next and previous window
- Control+F4 and Control+Shift+F4 -- close this window, close all but this one
- Alt+F10 -- alternate menu: every command in one list you can filter
- Control+F1 -- key describer: a key says what it would do instead of doing it
- Alt+F1 -- about; F1 -- the guide

The design is not new. It comes from the Homer.NET MDI fruit basket of 2010,
which already had the menu declared by name and key, a focus tip on every
control, a window picker, an alternate menu and a key describer. What is new is
that the three current apps can share one implementation instead of three that
drift.

**The title rule, which cost DbDo a bug.** The frame carries the app name and
nothing else; a child carries what it is showing and nothing else. Windows
merges a maximized child into the frame caption, so JAWS+T reads
`DbDo - [contacts.db - contacts]`. A child that repeated the app name made the
reader say it twice. `MdiChild.setTitle` is the only way to set a child title,
so the rule cannot be broken by accident.

**One builder for both.** `LbcDialog` can adopt an existing form instead of
making one, so an MDI child is laid out by exactly the same code as a dialog --
add order as focus order, the status line, the list search, the line chords, the
access keys. `MdiChild.lbc` is that builder; finish with `finishLayout` rather
than `run`, because the frame shows the window.

### What all three share

Everything else, which is the point of the kit: `Inix` for settings, `Log` for
the session log, `Paths` for the folder layout, `Say` for what the screen reader
cannot know, `KeyName` and `KeyMap` for keys, `Lbc` for every control, the
document set, `build.cmd`, `<App>_setup.iss`, `RepoFiles.txt`, `accept.inix`
and `check`. A person who learns one shape has learnt most of the other
two.

