---
title: "HomerDev: the Homer Development Kit"
author: "Jamal Mazrui"
---

# HomerDev: the Homer Development Kit

HomerDev is the shared toolbox behind the Homer Tools programs. It holds the
C# classes, the Python package, the build and release scripts, the project
templates, and the writing conventions that every Homer app is built on.

Before HomerDev, a fix to a shared class lived in whichever app folder it was
made in, and the next app to need it got whatever copy happened to be found
first. Now there is one copy, in `C:\HomerDev`, and every app compiles against
it.

This guide explains what is in the kit and how to use it. It is written for a
person, and for an AI asked to write a Homer app. An AI can be told: "use the
Homer namespace in `C:\HomerDev\CSharp` and follow HomerDev.md."

# Getting started

## What you need

- Windows 10 or later, 64-bit.
- The .NET Framework 4.8 Developer Pack, which supplies the reference
  assemblies the build needs.
- The Visual Studio Build Tools, free, for the Roslyn C# compiler.
- Python 3, for the kit's own scripts.
- Inno Setup 6, if you want an installer.
- Git and the GitHub CLI (`gh`), if you want to publish.

## Install the kit

Unzip `HomerDev.zip` into `C:\HomerDev`. That is the whole install. Then run:

    buildHomerDev

It converts every document to HTML with pandoc, fetching pandoc if the machine
does not have it, and then checks the kit over: every component present, every
text file in the right encoding, every template still holding its placeholder,
and no empty files. It reports problems plainly and writes the detail to
`buildHomerDev.log`.

If you keep the kit somewhere else, set the `HOMERDEV` environment variable to
that folder. Every build script looks there first.

## Start a new app

    newHomerApp JobDo

That writes `C:\JobDo` holding a starter `JobDo.cs`, `buildJobDo.cmd`,
`JobDo_setup.iss`, `createJobDoRepo.cmd` and `.ps1`, the local AI install
scripts, `version.txt`, and `.gitignore`. Nothing already in the folder is
touched. Two things need your hand afterwards, and both are marked CHANGE ME
in the installer script: a fresh AppId, and the desktop hotkey.

Then:

    cd \JobDo
    buildJobDo

# What is in the kit

## CSharp

Nine modules, all in the `Homer` namespace. Add `using Homer;` and compile the
ones you use straight from `C:\HomerDev\CSharp`; the build template already
does.

- **Lbc.cs** -- Layout By Code. Dialogs built from labelled standard controls.
  The biggest and most used module. Its own section is below.
- **Say.cs** -- direct speech to whichever screen reader is running.
- **Inix.cs** -- the `.inix` settings format, plus table conversion between
  `.inix`, `.csv`, `.tsv`, Markdown and `.xlsx`.
- **Keys.cs** -- one spelling for every key, and converters to what each API
  wants.
- **KeyMap.cs** -- one table of commands, summaries, and their keys, which the
  menus, the key describer and the hotkey list all read from.
- **Util.cs** -- string and file helpers, ported from the older HomerLib so the
  names match.
- **Web.cs** -- a small dependency-free web client: fetch a page, pull its
  links, download a file with a sensible name.
- **inixVert.cs** -- a command-line wrapper over the table converter in
  Inix.cs.
- **PdfRead.cs** -- reading a PDF with position and font size, so headings can
  be worked out. Optional: it needs the PdfPig package, which the app's own
  build script fetches.

## Python

`Python\homer\` is the Python side of the same toolbox: `inix`, `lbc`, `say`,
`util`, `web` and `version`. It was written for NVDA add-ons and follows three
rules that make it portable. Nothing imports NVDA at the top of a module, so
every module can be imported and tested in plain Python. Nothing depends on
anything outside the standard library except wx, which NVDA already has.
Nothing knows the name of the program using it.

Copy the `homer` folder into an add-on, or put `C:\HomerDev\Python` on the
path.

## Templates

The files a new app needs, with `_APP_` where its name goes. `newHomerApp`
fills them in.

## Tools

Scripts that need no editing at all. They work out the app name from the folder
they are run in.

- **tagRelease** -- tag, push, and publish a GitHub release.
- **cleanDir** -- move what the project does not name into `notes\`, delete
  empty files, clear Python caches.
- **tidyRepo** -- survey the whole repository and fix it in one pass.
- **homerPolicy.py** -- the shared answer to "what belongs in this project",
  read by both cleanDir and tidyRepo.

Copy the pair you want into the app folder and run it there.

## Style

The Camel Type documents: the short rules, the long reference, and the JAWS
scripting version.

# Camel Type

Camel Type is the house coding style. It exists for one reason: code is read by
listening, and a name that carries its own type saves a trip back to the
declaration.

- **A prefix says the type.** `s` string, `i` integer, `n` real, `b` boolean,
  `a` array, `l` list, `d` dictionary, `dt` date and time, `f` file, `h` window
  handle, `bin` binary buffer, `o` any other object, `v` a variant. For other
  classes, use the class name in lower camel case, or the usual short form:
  `pd` for Pandas, `browser` for a browser object.
- **Lower camel case for names you define** -- functions, methods, variables,
  properties. Avoid upper camel case and snake case except where the language
  or an API demands them.
- **A constant is a variable with `c_` in front**: `c_sFormat`, `c_iMaximum`.
- **Functions, not subprocedures.** If a routine is needed, make it a function,
  even when the result is ignored.
- **A simple if-then goes on one line**, condition and consequence together.
- **Iterate the collection, not an index**, wherever for-each will do.
- **Declarations go at the top**, one line per type, each line's names in
  alphabetical order, and the lines themselves in alphabetical order by type.
- **Double quotes** for strings in any language that offers a choice.
- **Database identifiers are lower_snake_case**, which is the one place the
  rule turns over, because that is what SQL reads well.

`Style\CamelType_CSharp.md` has the rules with examples; the Reference file has
the long form; the JAWS Script version covers that language's differences.

# The .inix format

`.inix` is the settings and small-table format every Homer app uses. It is
classic `.ini` with four additions, and any plain `.ini` file is already valid
`.inix`.

## The basics

    ; a comment. # also starts one.
    [Section]
    Name = value
    Another = value

Section and key names are matched without regard to case. A file may start with
keys before any section header; those belong to an implicit `[Global]` section.
Reading a file and writing it back preserves the order of everything, so a
program editing one setting does not reshuffle the file.

## Multi-line values are verbatim

A value may be fenced, and what is inside is taken exactly as it stands:

    Message = `
    Dear friend,

        This whole block, including the blank line and the indent, is the value.
    `

The fence is a line holding only a backtick. When the value itself contains a
backtick, use a triple-quote fence instead. Nothing is trimmed and nothing is
transformed on the way in or out. If a program wants the value trimmed, that is
the program's decision after reading it, not the format's.

## Arrays

A key may hold several values. A few short items with no spaces or commas can
sit on one line:

    SelectFields = last_name, first_name, enterprise

Anything longer goes one item per line inside a fence, most recent first. Both
shapes read back as the same ordered list, which is how the recent-file and
recent-search lists in Homer apps are stored.

## As a table

This is the part people are surprised by. A table in `.inix` is one section per
record:

    [Record001]
    title = A Walk in the Woods
    author = Bryson, Bill
    read = 2026-03-14

    [Record002]
    title = The Sea Around Us
    author = Carson, Rachel

A spreadsheet row makes you count columns to know which value you are hearing.
A record like this puts each field on its own line with its own name. `Inix.cs`
converts between `.inix`, `.csv`, `.tsv`, Markdown pipe tables and `.xlsx` in
any direction, with `.inix` as the home format. The `.xlsx` side is plain
OpenXML over the zip support in .NET, so no Office and no database driver is
involved.

`inixVert.cs` is the command-line form of the same thing:

    inixVert data.xlsx data.inix
    inixVert data.inix data.md

## In code

    using Homer;

    string sVoice = InixCodec.readValue(sPath, "Speech", "Voice", "Default");
    InixCodec.writeValue(sPath, "Speech", "Voice", "Zira");

    List<InixCodec.Section> lsSections = InixCodec.read(sPath);
    InixCodec.writeAsConfig(sPath, lsSections);

    InixTable.convertFile("report.csv", "report.inix");

`readValue` returns the default for a missing file, a missing section, a
missing key, and a key with no value, because a caller asking for a setting
wants a usable answer rather than four ways of saying no.

The `.inix` extension belongs to files a Homer tool creates. Reading a `.ini`
file somebody else wrote is fine.

# Direct speech across screen readers

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

## How it reaches the reader

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

## What to speak, and what not to

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

# Lbc: building a dialog

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

## The shape of a dialog

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

## What you can add

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

## Bands

By default each control sits on its own row. A band puts several on one row,
which is what you want for a field and the button that fills it in:

    dlg.addBand();
    TextBox tbSource = dlg.addInputBox("&Source:", sSource, "The file to work on.");
    Button btnBrowse = dlg.addButton("&Browse source...", "Pick it from a dialog.");
    dlg.endBand();

A band changes only the arrangement. The tab order is still the order of the
calls.

## Showing it

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

## Other pieces

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

## Opening focus

The field that opens with the focus has its value selected, so typing or
pasting replaces it and Tab leaves it alone. A **multi-line** box is the
exception: its caret opens on the first line, because its value is a document
rather than a field.

# The launchpad app

Most Homer tools are one dialog with one job: 2htm, extCheck, urlCheck,
bookFido, urlFido, HomerScribe. They share a shape, and a user who learns one
has learnt them all. `Templates\_APP_.cs` is that shape, ready to fill in.

## The controls, in order

The order below is the order they are added, which is the order they are
tabbed through and read.

1. **Source** -- a text box named `&Source`. What to work on.
2. **Browse source** -- a button named `&Browse source...` on the same band,
   opening a standard Open dialog.
3. **Options** -- whatever check boxes this app needs, each with its own access
   key and tip.
4. **Output** -- a text box named `&Output`. Where the result goes. Blank means
   beside the source.
5. **Choose output** -- a button named `&Choose output...` on the same band,
   opening a standard folder dialog.
6. **Use configuration** -- a check box named `&Use configuration`. Take the
   saved answers next time without asking.
7. **View output** -- a check box named `&View output`. Open the result when
   the work finishes.
8. **Default settings** -- a button that puts every field back as it started.
9. **OK** -- starts the work. Enter and Control+Enter do the same.
10. **Cancel** -- closes without doing anything. Escape does the same.
11. **Help** -- shows the help box. F1 does the same. Lbc adds it and places it
    rightmost.

## The two boxes

- The **help box** says what the program does, what each field means, what each
  button does, and the command line that matches. It is the same text the
  `--help` switch prints.
- The **results box** says what this run actually did, one short line per fact.
  Only actions actually taken are listed. Counts match their nouns.

## The command line does everything the dialog does

Each field has a switch, and the switch is named after the field:

    <App> --source <path> [--output <path>] [--config] [--view]
    <App> --defaults
    <App> --help

With any argument the program runs without opening a window, so it can be
driven from a batch file, a scheduled task, or another program. A bare path
with no switch is taken as the source, because that is what dropping a file on
the program means.

## Settings are saved as they are answered

Every answer is written to `<App>.inix` the moment it is given, not at exit, so
a crash or a kill loses nothing. The file sits beside the executable when that
folder is writable, which is the portable case, and under
`%LOCALAPPDATA%\<App>` otherwise, which is the installed case.

# Keys and key names

## One spelling

`Keys.cs` holds the one spelling for every key, taken from how Freedom
Scientific writes key names in the JAWS key map files, with three Homer rules
on top:

- **Modifiers in alphabetical order**: Alt, Control, Shift, Windows. So
  `Alt+Control+Shift+F` and never `Shift+Control+Alt+F`.
- **"Control" spelled out**, never "Ctrl".
- **The screen reader key is "JAWS" or "NVDA"**, not "JAWSKey". On both readers
  it is usually Insert or CapsLock.

Then convert to whatever an API wants, rather than writing that table again:

    Keys.toJawsKeyMap("Alt+Shift+H")    // for a .jkm file
    Keys.toNvdaGesture("Alt+Shift+H")   // for an NVDA gesture
    Keys.toWinFormsText("Alt+Shift+H")  // for a menu item's shortcut text
    Keys.toWinFormsKeys("Alt+Shift+H")  // the .NET Keys value
    Keys.toWx("Alt+Shift+H")            // for wxPython
    Keys.toInnoHotKey("Alt+Shift+H")    // for an installer shortcut
    Keys.toSpoken("Alt+Shift+H")        // for speech and documentation

`Keys.same()` compares two spellings of the same key, and `Keys.parse()`
normalizes one.

## Choosing a key

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

## KeyMap

`KeyMap.cs` is the one table associating a context, a command name, a summary,
a longer description and a key. The menus, the alternate menu, the key
describer and the hotkey document all read from it, so a command is described
once and every surface agrees.

    KeyMap.register("Find Record", Keys.Control | Keys.F, mnuFind, "Grid");
    KeyMap.setSummary("Find Record", "Search every column for text.");

`KeyMap.lsConflicts` lists any key claimed twice, which is worth showing in a
developer command rather than discovering in use.

# Scripts, logs, and the release routine

## Every script writes a log

This is not optional, and the rules are the same for a build script, a clean-up
script, a repository tidy, and a release.

- **The log goes beside the script**, not in an output folder and not in
  whatever the current directory happened to be. The one exception is an
  **installed program**: something under Program Files cannot write beside its
  own executable, so its log goes with the output, or beside the first source
  file, or under `%LOCALAPPDATA%\<App>`.
- **The log is for debugging.** It records the script path, the interpreter
  version, the platform, the working directory and the command line; then every
  effective setting; then every command run with its exit code; then any error
  with its full traceback. A failure must never produce a console traceback and
  an empty log.
- **The console is for a person.** Short, plain sentences saying what is
  happening. Technical detail belongs in the log.
- **A `.ps1` never ships without a `.cmd`** that calls it and forwards its own
  arguments, so nobody has to type the execution-policy incantation. The same
  courtesy applies to a `.py`.

## The four scripts

- **build&lt;App&gt;.cmd** -- increments `version.txt`, generates `Version.cs`
  from it, finds the compiler and the three reference assemblies that are not
  on the default path, compiles the app with the Homer modules from
  `C:\HomerDev\CSharp`, converts the documents with pandoc, and compiles the
  installer if Inno Setup is present. It fetches what it needs from the web
  itself. Log: `build<App>.log`.
- **cleanDir** -- moves anything the project does not name into `notes\`,
  deletes empty files, clears Python caches. It prints the plan and stops;
  `--do-it` carries it out. What belongs is decided by `homerPolicy.py` reading
  `<App>_setup.iss` and `RepoFiles.txt`, so there is no list to maintain.
  Log: `cleanDir.log`.
- **tidyRepo** -- the same question asked of the repository rather than the
  folder: what is tracked that should not be, what is large in the history, what
  is on disk that belongs nowhere. It surveys everything first and fixes it in
  one pass, because fixing as you go is what turns one clean-up into four.
  Log: `tidyRepo.log`.
- **tagRelease** -- reads the version, bumps it if that number is already
  released, writes it back, tags, pushes, and publishes the GitHub release with
  the installer attached. Log: `tagRelease.log`.

## The release routine

1. Unzip the app archive into `C:\<App>`.
2. `build<App>` from that folder.
3. Run `<App>.exe` as a quick test.
4. Commit, then `tagRelease`.
5. Install from the published `<App>_setup.exe`, or update in place with F11.

# The installer

`Templates\_APP__setup.iss` is the Inno Setup script every app starts from.
What it settles, so no app has to decide again:

- **Machine wide, administrator required.** No per-user fallback and no "who is
  this for" page. Somebody who wants a portable copy uses the zip.
- **64-bit only**, installed under Program Files.
- **The version comes from `version.txt`**, read at compile time. No version
  number is written in the script, so a stale copy cannot rewind it.
- **Both forms of every document ship**: Markdown for an editor or a braille
  display, HTML for a browser, which is what the Start menu shortcut opens.
- **A desktop shortcut with a hotkey**, created without asking, and the hotkey
  named on the launch checkbox where the user is looking when it matters.
- **Local AI as a checkbox.** More than one Homer app now uses a model running
  on the user's own machine, so `installOllama.cmd` and `installModels.cmd` are
  part of the kit and every app that can use AI ships them. The first box
  installs Ollama and the model; the second installs the model alone, for
  somebody who already runs Ollama. Tick the first by default when the program
  cannot do its main job without a model; leave it unticked when the model only
  adds something. An app that calls no model deletes the two file lines and the
  two run lines.
- **The uninstall removes the settings too**, and never touches what the user
  made with the program.

# For an AI writing a Homer app

Everything above is the answer to "how should this be written". The short
version to hold in mind:

- Use the Homer namespace. If a shared class covers the job, use it instead of
  writing something project-specific. The more the shared classes are
  exercised, the better they get.
- Build every dialog from Lbc primitives, in the order the user should tab.
- Follow Camel Type, including in generated code.
- Settings in `.inix`, saved the moment they are answered.
- Speak only what the screen reader cannot know.
- Write a detailed log beside the script, and keep the console short.
- Match the noun to the count, and treat zero as an answer.
- Do not police the user's language. Readability and plain-language help are
  welcome; rules about which words are acceptable are not, and any word-policing
  package in a prose checker should be left out or switched off by name.
