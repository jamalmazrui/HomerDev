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

It is also a teaching kit, and the teaching is the subject of its own part
below: **AI-assisted coding**, which is the name this kit uses for what other
people call vibe coding. The difference is not the AI. It is that the person
holding the keyboard knows what a good program is before the AI writes one.

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

Twelve modules, all in the `Homer` namespace. Add `using Homer;` and compile the
ones you use straight from `C:\HomerDev\CSharp`; the build template already
does.

- **Mdi.cs** -- the frame and child of a multiple-document app.
- **Lbc.cs** -- Layout By Code. Dialogs built from labelled standard controls.
  The biggest and most used module. Its own section is below.
- **Log.cs** -- the session log every Homer program writes.
- **Say.cs** -- direct speech to whichever screen reader is running.
- **Inix.cs** -- the `.inix` settings format, plus table conversion between
  `.inix`, `.csv`, `.tsv`, Markdown and `.xlsx`.
- **KeyName.cs** -- one spelling for every key, and converters to what each API
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

`homer\` is the Python side of the same toolbox: `inix`, `lbc`, `log`,
`say`, `util`, `web` and `version`. It was written for NVDA add-ons and follows three
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

- **tagRelease** -- tag, push, and publish a GitHub release. It acts on the
  current directory, or on `-Path <folder>`, so one copy in `C:\bin` on the
  PATH serves every project. An app with an installer is released from the
  version stamped into `<App>_setup.exe`, with the installer attached; a project
  that ships source and has no `<App>_setup.iss` is released from `version.txt`,
  with no asset.
- **homerTidy** -- tidy the folder and the repository in one pass. It replaces
  cleanDir and tidyRepo, which asked the same question of two places and could
  disagree about the answer.

Copy the pair you want into the app folder and run it there.

## Templates\samples

Two fruit basket programs, the same design in two languages, each with the build
script that produces it:

- `Templates\samples\` -- `FruitBasketCs.cs` and `buildFruitBasketCs.cmd`,
  which produce `FruitBasketCs.exe` on the C# classes.
- `Templates\samples\` -- `FruitBasketPy.py` and `buildFruitBasketPy.cmd`,
  which produce `FruitBasketPy.exe` on the Python package, with Python and every
  dependency inside the one file.

The two are written to be opened side by side: twelve blocks with the same
numbers and titles in each, and the same function names throughout.

Both are read alongside the AI-assisted coding part below, which is what they
are for.

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

`help\CamelType_CSharp.md` has the rules with examples; the Reference file has
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

# Every file in the kit, and why it is here

One line each, so a file you have not seen before can be looked up rather
than guessed at. Folders are in the order you meet them.

## Top level

- **ReadMe.md, ReadMe.htm** -- the introduction and the quick start; stays at the root because GitHub surfaces it and because it is the first thing anybody opens
- **License.md, License.htm** -- the MIT license, naming the kit and its author
- **buildHomerDev.cmd, buildHomerDev.py** -- converts every document to HTML with pandoc, fetching pandoc if the machine has none, then audits the kit: components present, encodings right, no empty files
- **releaseHomerDev.cmd** -- the whole release as one command: tools, checks, push, tag
- **checkHomerDev.cmd, checkHomerDev.py** -- proves the kit still builds by building with it: audit, dependency rule, clean, all three samples, evidence report
- **newHomerApp.cmd, newHomerApp.py** -- writes a new app folder from the templates, C# or Python, overwriting nothing
- **_APP_.cmd** -- runs `exec\_APP_.exe` from the top of the project, so typing the program's name there still runs the fresh build
- **LocalFiles.txt** -- what belongs on this disk but never in the repository; homerTidy keeps it and writes each line into .gitignore as never pushed
- **RepoFiles.txt** -- the whitelist: what the repository carries, and the source homerTidy generates .gitignore from
- **version.txt** -- the kit's version, one line, no byte order mark, read by every script
- **.gitignore** -- generated from RepoFiles.txt; ignores everything and puts back only what is named

## CSharp -- the shared C# classes

- **Inix.cs** -- the .inix settings format: read and write one value, or whole tables, with multiline values kept verbatim
- **KeyMap.cs** -- the command-to-key registry behind the alternate menu, the key describer and the hotkey document
- **KeyName.cs** -- key names as JAWS writes them, and the conversions to Windows, .NET, wxPython and Inno forms
- **Lbc.cs** -- Layout By Code: every dialog, every control, add order as focus order, the status line, the list search, the line chords
- **Log.cs** -- the session log: one file per run, named for when it began, with the environment and every error
- **Mdi.cs** -- the frame and child of a multiple-document app, with the window, job, settings and help commands built in
- **Paths.cs** -- the folder layout: the two trees, the nine folders, and the shipped-default-then-user-copy pattern
- **PdfRead.cs** -- reading text out of a PDF, including a tagged one
- **Say.cs** -- speech that reaches JAWS, NVDA and Narrator without the program knowing which is running
- **Util.cs** -- the small shared helpers, including the plural that matches a count to its noun
- **Web.cs** -- fetching a page, a file, or an API answer
- **inixVert.cs** -- converting .inix to and from other tabular formats

## homer -- the same toolbox in Python

- **__init__.py** -- the package
- **inix.py, lbc.py, log.py, mdi.py, paths.py, say.py, util.py, web.py** -- the Python counterparts of Inix, Lbc, Log, Paths, Say, Util and Web, with the same names and the same behaviour
- **version.py** -- written by the build; not a source file

## Templates\samples

- **FruitBasketCs.cs** -- the single-dialog shape, with twelve marked blocks and the nine decisions
- **FruitBasketMdiCs.cs, FruitBasketMdiPy.py** -- the multiple-document shape in both languages, marking only what changes when there are several windows
- **FruitBasketPy.py** -- the same program as FruitBasketCs, in Python, block for block
- **accept.inix** -- what done means for the samples, run by checkHomerApp
- **uiTest.inix** -- what the samples must do when driven, run by uiCheck
- **buildFruitBasketCs.cmd, buildFruitBasketMdiCs.cmd, buildFruitBasketMdiPy.cmd, buildFruitBasketPy.cmd** -- one build script each; `buildHomerDev` runs all four

## Templates -- what newHomerApp copies

- **_APP_.cs** -- a working one-dialog program to start from
- **_APP__setup.iss** -- the Inno installer: the structured tree, the component checkboxes, the setup log kept with the program's own
- **accept.inix** -- the acceptance-criteria starter
- **build_APP_.cmd, build_APP_Py.cmd** -- the C# and Python build scripts, with the component switches
- **create_APP_Repo.cmd, create_APP_Repo.ps1** -- makes the GitHub repository and pushes the first commit
- **gitignore.txt** -- the whitelist starter, replaced by homerTidy
- **homerFinish.cmd** -- shows what the install did, then starts the program
- **installModels.cmd, installOllama.cmd** -- local AI, for the apps that need it
- **installScreenReaderSupport.cmd** -- unpacks the JAWS scripts and hands the add-on to NVDA
- **self.md** -- the private notebook a new app starts with
- **version.txt** -- 1.0.0, with no byte order mark

## Tools -- scripts that act on a project

- **checkHomerApp.cmd, checkHomerApp.py** -- gathers evidence about an app: encodings, names, keys, build, smoke run, acceptance criteria, and a report saying what it did not check
- **gitPush.cmd** -- stage, commit and push what the whitelist allows
- **gitRelease.cmd** -- check first, then tag and publish
- **uiCheck.cmd, uiCheck.py** -- starts a program, sends the keys, and reads the accessibility tree back; driven by uiTest.inix beside the program
- **installTools.cmd** -- copies the tools to a folder on the PATH, so one current copy serves every project
- **homerTidy.cmd, homerTidy.py** -- tidies folder and repository together, and generates the whitelist .gitignore
- **buildTutorials.cmd, buildTutorials.ps1** -- fetches the voices, speaks every tutorial script, joins them into Tutorials.mkv with a chapter each, and writes the playlist and the feed
- **makeTutorials.cmd, makeTutorials.py** -- writes the tutorial scripts into Tutorials.md and the feed, speaking nothing
- **tagRelease.cmd, tagRelease.ps1** -- reads version.txt, tags, and publishes the installer as a release asset

## help -- the documents

- **HomerDev.md** -- this guide: the classes, the conventions, the three shapes, the layout, the evidence
- **Announce.md** -- three ready-to-post announcements, at measured lengths
- **FAQ.md** -- the questions people ask, including why Windows only
- **Developer.md** -- how to rebuild or change the kit
- **History.md** -- what changed in each version, and why
- **Hotkeys.md** -- every key three ways: by key, by description, by binding
- **Tutorials.md** -- walkthroughs of common scenarios, and the audio tutorial playlist
- **Tutorial_HomerDev.inix** -- the spoken walkthrough, narration and screen reader in two voices
- **CamelType_CSharp.md, CamelType_CSharp_Reference.md, CamelType_JAWSScript.md** -- the coding style
- **self.md** -- the private notebook: decisions, findings and open items. Never pushed
# Three kinds of Homer app

Every Homer program is one of three shapes. They share far more than they
differ, and what they share is the whole of this kit: the same classes, the same
folder layout, the same session log, the same settings format, the same key
conventions, the same document set, the same build, installer and release
scripts, and the same evidence checks. What differs is only how the program
meets the person.

## One: a single tool, with a command line and a dialog

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

## Two: a desktop program that could not be a command line

The same single-window shape, but graphical only, because of what it carries: a
local AI model, a browser engine, a media pipeline, a speech stack. HomerScribe
is this. The dependencies decide the shape, not the interface.

It should still answer `--help` and still take arguments where that is
meaningful, but it does not promise that every feature works without the
desktop. Say so in its guide rather than leaving somebody to discover it.

## Three: a multiple-document program

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

## What all three share

Everything else, which is the point of the kit: `Inix` for settings, `Log` for
the session log, `Paths` for the folder layout, `Say` for what the screen reader
cannot know, `KeyName` and `KeyMap` for keys, `Lbc` for every control, the
document set, `build<App>.cmd`, `<App>_setup.iss`, `RepoFiles.txt`, `accept.inix`
and `checkHomerApp`. A person who learns one shape has learnt most of the other
two.

# Scripts and settings: the two lists every MDI app gets

An MDI frame comes with two commands that look small and are not:

    Alt+Shift+S    run a script: a list of what is in the scripts folder
    Alt+Shift+C    change a setting: a list of what this program lets you change

Both are lists. Neither is a folder browser, a command line, a text file to
edit, or a page of check boxes. That is the design, and it comes from decades of
doing this work by ear.

## Why a list, rather than a path to type

A sighted user glances at a folder and picks. Without sight, the same folder is
a sequence: you arrow through it, each name is spoken, and the wrong ones have to
be heard before the right one arrives. Typing the path instead means remembering
the path exactly -- every folder, every spelling, every extension -- and getting
a silent failure when you are one character out.

A list box solves both. It holds only the things that are actually runnable, it
is reached by one key, and **first-letter navigation is the fast path**: press
the first letter of the job and you are on it, or near it. That is one keystroke
against a dozen, and it is why the Homer folder names all start with different
letters as well.

The same argument is why `Run a Script` reads the folder every time rather than
caching a menu. The list is always what is there now, so dropping a new script
into the folder makes it available immediately, with nothing to register and no
restart.

## Why the jobs live in a folder, not in the program

A script is the part of the program the user gets to write. The program ships the
jobs it knows about; the user's own go in the per-user tree, where an update
cannot overwrite them. Both appear in the same list, the user's first.

This is the oldest pattern in this whole kit, and it predates the kit by a long
way: a screen reader user who can automate a repetitive task does so, and the
program's job is to make that easy rather than to anticipate every need. A
program with a job folder can be extended by the person using it, at three in
the morning, without asking anybody.

## Why settings change without a restart

`Change a Setting` lists what the app declared with `addSetting`, asks for the
new value in one field, writes it, and calls the app back so it acts at once.

Three things follow from that, all of them learned the hard way:

- **No settings file to edit by hand.** Editing INI syntax in a text editor is
  where a screen reader user loses an hour to a missing bracket that nothing
  reports.
- **No twenty-control preferences dialog.** Those are slow to hear and slower to
  navigate; a list plus one field is two keystrokes and one answer.
- **No restart.** A program that needs restarting to honour a setting turns a
  ten-second change into a minute of reopening files and finding your place.

And the value is saved the moment it is answered, not at exit, so a crash never
costs somebody the answers they already gave.

## What this means for a console program

The same reasoning shapes the command-line shape of a Homer tool:

- Every switch has a long, spelled-out name, because a spoken `--source` is
  unambiguous and a spoken `-s` is not.
- `--help` lists every switch, to standard output, exit code 0, so it can be
  read in an editor or piped to a file rather than scrolled past.
- The console says short, plain sentences; the detail goes to the log. A console
  that scrolls for a minute tells a screen reader user nothing at all.
- A count always matches its noun, and zero is a real answer said plainly.
- With no arguments -- or with `--gui` -- the same program opens one dialog, so
  the thing you learned in the dialog is the thing you can automate.

# Where an app puts its files

## The letters are the design

A screen reader user moves through a folder listing by first letter. Nine
folders whose names all begin with the same letter cost nine keystrokes each
time; nine whose initials differ cost one. So every folder in the Homer layout
starts with a different letter:

- **c** -- `configs`, settings that decide how the program starts
- **d** -- `data`, databases and seed data
- **h** -- `help`, the documents: the guide, the tutorials, the history
- **e** -- `exec`, the program itself: `.exe`, `.dll`, `.py`, `.vbs`
- **j** -- `scripts`, scripts, add-ons and plugins that change behaviour later
- **l** -- `logs`, one file per session
- **r** -- `results`, what the program produced
- **t** -- `temp`, scratch, deletable at the start of the next run
- **t** -- `templates`, files a user copies and fills in

The line between `configs` and `scripts` is worth stating: configs decide how the
program starts, jobs change what it does once running. A settings file is a
config; a script the user can invoke is a job.

**Why `scripts` and not `jobs`.** It was `jobs` until somebody pointed out that
the word arrived from mainframe batch processing and that everyone now says
scripts. The letter is the same either way; the word people already use wins.

**Why there is no `samples`.** A template that shows what is possible is a
sample with a purpose, so the two folded into one. The alternatives all collided:
`examples` wants **e**, which is `exec`, and `demos` wants **d**, which is
`data`.

## Two names begin with t, and they never meet

`temp` exists only in the per-user tree. `templates` exists only in the
installed tree. No listing ever holds both, so first-letter navigation stays
exact, and nothing had to be given an unobvious name to keep it that way.

That split is not a trick to save a letter; it is where those folders belong
anyway. A `temp` folder under Program Files could not be written to, which is
the whole reason the per-user tree exists, and `templates` is shipped and
read-only, which is why it has no place in a folder the program writes.

Windows' own temporary folder is still the right home for a file that lives and
dies inside one run. `<App>\temp` is for the other kind: what a crash left
behind, somewhere the program knows to look at its next start rather than
somewhere shared with every other program on the machine.

## Where the documents live, and what GitHub thinks

`help` holds every document -- the guide, `Tutorials.md`, `History.md`,
`Hotkeys.md`, `Announce.md`, `Developer.md`, the style guides and the tutorial
scripts -- in both `.md` and `.htm`. `ReadMe` and `License` stay at the top of
the project.

**Why not `docs`, which is what GitHub expects?** Because `d` is already `data`
in this layout, and the letters are the point. The question is what that costs,
and the answer is: one feature, which these projects do not use.

GitHub's own documentation says that a README placed in the repository's
`.github`, root, or `docs` directory is recognized and surfaced to visitors.
Keeping `ReadMe.md` at the root satisfies that, so nothing is lost there.
GitHub Pages can also publish from a `/docs` folder on the main branch, and that
is the feature `help` gives up -- but Homer apps are listed from the separate
HomerTools site rather than from each repository's own Pages, so there is
nothing to give up in practice.

Community health files -- CONTRIBUTING, CODE_OF_CONDUCT and the issue templates
-- are the one case where GitHub really does look in named places. If a project
ever wants them, they go in `.github`, which GitHub recognizes and which does not
disturb the letters.

So: **`ReadMe.md` and `License.md` at the root for GitHub and for a person
opening the folder; everything else in `help` for the letter that reaches it in
one keystroke.**

## Three trees

**The installed tree**, `C:\Program Files\<App>`, read-only to the user:

    <App>\configs   <App>\data   <App>\exec   <App>\help   <App>\scripts
    <App>\scripts  <App>\templates
    and ReadMe.md and ReadMe.htm at the root, where a person opening the folder
    for the first time will find them

**The per-user tree**, `%LOCALAPPDATA%\<App>`, which the program owns and writes:

    <App>\configs   <App>\data   <App>\scripts   <App>\logs
    <App>\results   <App>\temp

No `exec` and no `templates` there: those are shipped, not made.

**The development folder**, `C:\<App>`, has the same shape as the installed
tree. Sources and build files stay at the top, with ReadMe and License, because
the compiler, the installer script and the release script expect them there.
Everything else sits in the folder it is installed to: the build compiles and
fetches into `exec`, the documents live in `help`, tooling in `scripts`, samples
in `templates`. And like the per-user tree it has **`logs`**: every build, clean,
tidy, tutorial and audit run writes its own file there, named as the program
names its runtime logs -- `<App>-<task>-yyyyMMdd-HHmmss.log`, such as
`DbDo-build-20260921-114210.log`. One file per session, so nothing is appended to
or overwritten; an alphabetical sort is a chronological one; and zipping the
folder gathers every log there is. Git ignores it. So what a developer sees is what a user gets, and "where does
this file go" has one answer.

`exec` is built, never committed. `help` holds the published documents and, local
only, anything like `self.md` the repository does not want. **homerTidy**
puts a folder back into this shape: a file the installer takes from `exec` or
`help` is moved there, a stray log goes to `logs`, and anything the project does
not name goes to `notes`. What belongs is read from the project itself -- the
installer script, `RepoFiles.txt` for what the repository carries, and
**`LocalFiles.txt`** for what belongs on this disk only, such as a tutorial's
working scripts or fetched voice models. There is no per-app clean-up script;
LocalFiles.txt is where an app says what is special about it.

A clean-up script must know the layout. One written before it -- moving a
`Scripts` folder as obsolete -- will move `scripts`, which Windows treats as the
same name, and take the tooling with it.

## Asking for a folder

`Paths` in C# and `homer.paths` in Python are the same class in two languages,
and no app should work out a path for itself:

    using Homer;                              from homer import paths
    Paths.start("JobDo");                     paths.start("JobDo")
    Paths.configFile("JobDo.inix");           paths.configFile("JobDo.inix")
    Paths.results();                          paths.results()
    Paths.clearTemp();                        paths.clearTemp()
    Paths.tempFile(".xml");                   paths.tempFile(".xml")

`configFile` is the pattern every app needs: it hands back the user's copy of a
settings file, making it from the one that shipped the first time it is asked.
So an update never overwrites what somebody changed, and the app never has to
know which case it is in.

`clearTemp` belongs at startup, once. Whatever it finds is what a previous run
could not clean up after itself, which is exactly what that folder is for.

# Evidence, and checking without sight

A sighted developer checks by looking: skim the diff, glance at the window,
notice that a control landed in the wrong place. A blind developer checks by
instrumenting. With AI writing the first draft, that is not an accommodation. It
is the only method that scales, because nobody reads generated code fast enough
to trust it by reading.

The kit's answer is one script and one file.

## checkHomerDev, for the kit itself

    checkHomerDev             audit, clean, build all three samples, report
    checkHomerDev --deep      delete the Python virtual environment too
    checkHomerDev --no-clean  build over what is there (fast, weaker)

`checkHomerApp` checks an app. This checks the kit, and it does it the only way
that settles the question: with a compiler. It runs the kit audit, checks the
module dependency rule, removes what previous builds wrote, builds all three
samples with their own scripts, and writes `evidence-kit-<date>.md`.

Run it after changing anything in `CSharp` or `homer`, and before `tagRelease`.

**The dependency rule.** A module may declare what it needs, in two forms:

    // REQUIRES: KeyMap.cs, Lbc.cs, Log.cs, Paths.cs, Say.cs, Util.cs.
    // ASSEMBLIES: System.IO.Compression.dll, System.IO.Compression.FileSystem.dll.

The second is the one that bites. A module needing an assembly reference fails
as a missing TYPE -- `error CS0246: The type or namespace name 'ZipArchive'
could not be found` -- which points at the module rather than at the build
script that under-referenced it. `Inix.cs` reads and writes .xlsx, which are zip
archives, and DbDo hit exactly this on its first build against the kit.

**The module rule.** A module may also declare what it needs:

    // REQUIRES: KeyMap.cs, Lbc.cs, Log.cs, Paths.cs, Say.cs, Util.cs.

and the check reads every build script for one that includes a module without
its requirements. `Mdi.cs` is the only module with a REQUIRES line today. The
check is general anyway, because the fault class was invisible until it
happened.

**What it does not do.** It does not run the programs -- all three samples are
windowed, and a check that needs a person to close a window is not a check --
and it does not build EdSharp, FileDir, DbDo or HomerScribe, which compile
against these same modules. After changing a shared class, build those four.
Both limits are printed in every report.

## checkHomerApp

    cd \JobDo
    checkHomerApp
    checkHomerApp --build

It runs every check that can answer yes or no, records the command and the exit
code for each, and writes `evidence-<yyyymmdd-hhmmss>.md` beside itself. Eleven
checks come with it: the document set and its HTML, file encodings, zero-byte
files, the version's single source of truth, the publishing whitelist, whether
the program opens a log, accessible names that repeat a caption a screen reader
already speaks, reserved key combinations and access keys claimed twice, the
build, a smoke run of `--help`, and the app's own acceptance criteria.

It exits 0 when nothing failed and 1 when something did, so a build script or a
scheduled task can act on it.

## The report says three things

- **What was verified** -- a check ran and passed, and here is the command.
- **What was not checked** -- a check was skipped, and here is why. A skip is
  never counted as a pass.
- **What remains uncertain** -- whether the program does the right thing, what a
  screen reader actually says, whether the keyboard order is usable, whether the
  code is secure, and whether any of it still works next month.

That last list is the honest part, and it is printed every time. A report
claiming everything is fine is worth nothing; one that says what it did not look
at is worth a great deal, because it tells a person exactly where their own
judgement is still required.

## accept.inix: what "done" means, written before the code

Acceptance criteria belong to the app, not to the checker:

    [check]
    Name   = the help text names every switch
    Run    = JobDo.exe --help
    Expect = 0
    Wants  = --source

`Run` is a command, `Expect` its exit code, `Wants` an optional string its
output must contain. That is the whole language, on purpose: a criterion nobody
can read is a criterion nobody writes. `Templates\accept.inix` is the starting
point, and `Templates\samples\accept.inix` shows a real one.

A criterion that cannot be written this way is still worth writing. Put it in
`self.md` under what a person has to check by hand, so it is not quietly
forgotten.

## A checker that cries wolf is worse than none

Two rules were learned on its first run and are built in. It ignores the kit's
own modules, because a shared class sets accessible names and names key
combinations on purpose. And it ignores comment lines, because a comment
explaining that Alt+Control is reserved is the rule rather than a breach of it.

On that same first run it found a real fault: both fruit basket samples had
given `&S` to two controls at once. That is what the tool is for.

# Automated checks, and the one thing still done by hand

Four commands, each answering a different question, and between them almost
nothing is left for a person to remember:

    buildHomerDev      documents, all four samples, the kit audit
    checkHomerDev      the environment, a clean build of everything, the tools
                       on your PATH, and every program driven through its keys
    checkHomerApp      one app: encodings, names, keys, build, smoke run, and
                       the acceptance criteria you wrote
    uiCheck            one program: started, driven, and read back

The rule behind them is the rule behind the whole kit. **A check a person has to
remember is a check that stops happening in the week it matters.** So every
check that can be automated is, and the ones that cannot are named in the report
rather than left to be inferred.

## uiCheck: pressing the keys without a person

`uiCheck` starts a real program, sends keystrokes to it, and asks the Windows UI
Automation tree what is there afterwards -- the same interface a screen reader
uses to find out what is on the screen.

That last part is what makes it worth having. A control with no accessible name
is invisible to UI Automation and to a screen reader alike, so a check that
finds nothing has found something real.

Tests live beside the program in `uiTest.inix`, so an app carries its own:

    [test]
    Name = the basket takes a fruit and shows it
    Run = FruitBasketCs.exe

    [step]
    Keys = apple{ENTER}
    Wants = apple
    Note = the fruit is in the list after Enter

    [step]
    Keys = %r
    Title = Fruit basket report
    Escape = yes

`Keys` is pywinauto syntax -- `{ENTER}`, `{ESC}`, `{F4}`, `%x` for Alt+x, `^x`
for Control+x, `+x` for Shift+x. `Wants` is a string that must appear somewhere
in the accessibility tree. `Title` is a window that must exist. `Escape` closes
what the step opened. pywinauto installs itself on first run.

`Templates\samples\uiTest.inix` drives all four samples, including the keys an MDI app
gets free: Control+N for a second window, F4 for the window list, Alt+Shift+S
for the jobs, Alt+Shift+C for the settings, Alt+F1 for about.

## Checking the machine, not just the kit

`checkHomerDev` also records what the build actually ran with -- the Python and
pandoc it found -- and compares every tool on your PATH against the kit's copy.
That second check exists because a release once failed on a `tagRelease` from
before source-only releases were supported, with an error naming a file that was
never meant to exist. One shared copy is the point of those tools, and one
shared copy is what can go stale. `scripts\installTools` fixes what it reports.

## What is still not automated

**Speech.** UI Automation reports that a control exists and what it is called.
It does not report what JAWS said. That is the one gap that matters, and it is
not unbridgeable: NVDA can log what it speaks at debug level, so a future check
could run a scripted session and read that log back. It is written down as the
next step rather than claimed as done.

Until then, one thing is worth doing by hand before a release, once: open a
program, tab through it, and listen. Everything else the scripts now do.

## The installer's own pages

`DisableDirPage=auto` with `UsePreviousAppDir=yes`: when a previous install of
the same AppId is found, the destination page is skipped and the update goes
where the last one went. A first install still chooses the folder.
`DisableProgramGroupPage=yes`, because a Homer app creates a desktop shortcut
with a hotkey rather than a Start Menu folder.

## Anything that shells out to an installer says so first

A script that runs winget, an MSI or any other installer has to tell the person
that **Windows may ask for permission in a window behind this one**, and name
Alt+Tab as the way to find it. The User Account Control prompt opens without
taking focus: a sighted user sees a flash on the taskbar, and a screen reader
user gets nothing at all. The script looks hung, and is not.

Where the wait can be watched, watch it: `consent.exe` IS the prompt, so a
script polling for that process can say "Windows is asking for permission now"
the moment it appears. And give the wait a time limit with a way out, so an
answer that never comes ends in a sentence rather than a hang.

## Finish-page checkboxes

**Every component appears three times** -- one entry per state, install, update
and already current -- grouped so the ones that do something come first. Only
one is ever shown, because the others are skipped by their `Check` function.

**The label carries the versions and nothing else:** "Install Ollama 0.34.1",
"Update Ollama from 0.33.0 to 0.34.1", "Reinstall Ollama 0.34.1 (current
version)". A purpose clause belongs only in the fallback label, where no version
is known. The launch and guide entries keep the wording the other apps use:
"Launch <App> (Alt+Control+<key> starts it any time)" and "Open the user guide
(F1 opens it inside <App>)".

**Detect by looking, not by running.** Check for the file and the uninstall
registry key first: no process to start, no quoting to get wrong, no PATH to
depend on, and an elevated installer still sees them. Run the tool only to learn
its version.

**Quote the whole probe command.** `cmd /c` strips the first and last quote of
what follows it, so a command beginning with a quoted path loses its opening
quote and silently runs nothing -- which reads as "not installed". Wrap the
whole command in one more pair.

**Log every probe**, with its command, exit code and output. A detection that
goes wrong on somebody else's machine cannot be diagnosed otherwise.

A checkbox must know what is already installed. Offering to install something
that is already there wastes a download and tells the user the installer did not
look. Gate every optional component with a Check function that asks the machine,
and label it with a `{code:...}` function that says whether this is an install,
an update or a reinstall. Ask winget AND the tool's own executable: tools like
Ollama install per user, into a profile an elevated installer's PATH cannot see.
Cache the answers, because each query costs a second and the page asks twice.

The last checkbox runs `homerFinish.cmd`, never the program directly. Inno runs
the entries in order and the launch is last, so a program started there puts its
window on top of whatever the other entries were still saying. `homerFinish.cmd`
reads the setup log, shows ONE Results box, waits for it to be dismissed, and
only then starts the program.

The Results box says: that the program is installed and where; the disposition
of each checkbox that was ticked, one line each; and where the log is. Nothing
about a step that did not run, nothing the wizard already said, and every count
matching its noun.

# Spoken tutorials

Every Homer app can carry a short set of spoken walkthroughs, built from text
files and produced by two tools in the kit. Nothing is recorded: one synthetic
voice works through a task and a second answers as a screen reader would.

## The format: a demo script

A tutorial is a **demo script** -- an `.inix` whose sections are speech
passages. It lives in `help`, named `Tutorial_NN_Topic.inix`, with two digits so
ten and eleven sort after nine.

The FIRST section is `[global]`, and what it holds governs every passage after
it. Script 00 sets the defaults for the whole series; a later script may carry
its own `[global]` to override any of them for itself. Every key is optional:

- `FileTask = demo` -- what kind of .inix this is, as report and accept files
  declare themselves.
- `NarratorVoice`, `ReaderVoice` -- a piper voice, as "kristin medium".
- `NarratorScale`, `ReaderScale` -- duration; less is quicker. 0.80 for the
  narrator suits listeners of every age; 0.72 proved too quick for an older ear.
- `NarratorPitch` -- semitones, applied after speaking without changing length.
  -2 lowers a woman's voice into the range age-related hearing loss spares.
- `ReaderFlatness` -- piper's noise settings, lowered together. 0.333 is even and
  screen-reader-like; piper's own default near 0.667 sounds like a person.
- `LeadIn`, `Gap` -- seconds of silence before the first word, and after each
  passage.
- `VoiceFolder`, `PiperPath`, `FfmpegPath` -- where the engines are, when they
  are somewhere the build script would not look.

Then `[feed]` on the first script only, `[about]` for the title and homework,
and one `[step]` per exchange:

- `Say=` what the narrator says. One idea, no padding.
- `Key=` the keystroke, in Homer key-name form.
- `Hear=` what the screen reader answers -- one line per utterance, written the
  way a fresh reader at its middle verbosity would say it: **name, role, value,
  state, position**. That order is nervish, and it never varies.
- `Note=` written only, never spoken.
- `Pause=` seconds of silence before the passage. SSML calls this
  `<break time="2s"/>`; this is the same idea without the brackets.

`[about]` carries Title, Intro, Setup and Homework. `[feed]`, on the first script
only, carries the podcast details.

**Why an .inix rather than SSML.** SSML is the W3C standard and is the right
answer when the engine speaks it -- Azure, Google and Polly do. Piper does not,
from the command line, so an SSML file would have to be parsed and turned back
into flags. The settings that SSML would carry -- which voice, how fast, how flat
-- are identical for every passage in a series, so they live in the build script
instead, in one place. If a passage ever needs its own voice, add `Voice=` and
borrow SSML's names: rate, pitch, volume.

## Writing from a speech history

The best Hear lines are copied from a real screen reader's speech history, not
imagined. Record one while doing the task, then keep only what belongs to the
task. Leave out:

- **Task switching.** "Lost focus", "Press ALT Tab", "Task Switching", and the
  list of other windows while looking for the right one.
- **The window you came back to between steps** -- a file manager or browser
  announcing itself because focus passed through it.
- **Finding a window that did not take focus**, such as a User Account Control
  prompt opened behind everything. The tutorial says the prompt can hide and how
  to find it; it does not replay the search.
- **Repeated group text.** An installer's finish page reads its whole paragraph
  before every option as you arrow; say it once, when the page arrives.
- **Structural chatter** such as "level 0" on a tree view toggle.

Keep: the dialog title when it appears, the focused control in name, role,
value, state and position order, the access key where one exists, and the
program's own direct speech ("DbDo ready").

**A speech history is not a strict sequence.** A line heard twice may be a say
line, or an Up Arrow and a Down Arrow to find one's place again, rather than
something the program said twice. Before calling a repeat a bug, check the code:
DbDo's File menu seemed to list two items twice, and each is added once.

**Never replace a menu item's accessible name.** Doing so hides its access
letter, and the screen reader falls back to announcing the item's first letter
instead -- "Add Table, A" for an item whose letter is T, so the letter it teaches
does nothing. The shortcut needs no help: ShortcutKeyDisplayString carries it.

**Check every key against the program before teaching it.** A key written from
what a command does, rather than from the menu that defines it, is wrong often
enough to matter: DbDo's tutorials once taught Control+O for Order, which is
Open, and Control+S for Select Columns, which is Save.

## The tools

- **`buildTutorials`** fetches the voices if they are missing, speaks each
  script into its own `.mp3`, joins them into `Tutorials.mkv` with a chapter per
  tutorial, writes `Tutorials.m3u`, and rewrites the feed.
- **`makeTutorials`** writes the same scripts into `Tutorials.md` and the feed,
  without speaking anything.

Both are in `Tools`, both look for the scripts in `help`, and both work in any
app that follows the layout.

## The voices, and what may be published

Choose by licence first. Most of piper's best-known English voices cannot be
redistributed: **lessac** comes from the Blizzard 2013 corpus, research use
only; **ryan**, **hfc_male** and **hfc_female** are CC BY-NC-SA; **libritts_r**
is fine-tuned from lessac. The build script installs two that can be published
anywhere:

- **kristin**, female, trained from scratch on LJ Speech, public domain.
- **john**, male, from LibriVox recordings, public domain.

Credit them in the app's guide even though public domain material requires no
acknowledgement.

## What ships

`Tutorials.mkv` goes in the repository. The `.inix` scripts, the `.mp3` files
and the `.m3u` do not: the audio is rebuilt by one command and is far larger
than the rest of the project, and the scripts are working material. The
transcript, `Tutorials.md`, ships like any other document.

## Not twice: speech that repeats

Homer programs have said the same thing twice for years, and there are only two
mechanisms behind it.

**An accessible name that repeats words the control already carries.** A list
box labelled "&Fields:" whose AccessibleName is also "Fields" is named twice,
and every reader says it twice. Set an accessible name only for a control with
no words of its own -- a grid with no label beside it. Not for a button, which
carries its caption; not for a box with a label before it; never for a form,
whose caption IS its accessible name. FileDir had forty-eight of these in one
file, DbDo nineteen. `checkHomerApp` and an app's own audit compare every
accessible name against every caption in the same source and fail on a match.

**Direct speech that says what the reader is about to say anyway** -- the window
title as a dialog opens, the control that just took focus, the same sentence
twice in a breath. `Say.say` now drops a line that repeats the last one within a
second and a half, or that matches the title of the window in front or the name
of the control with focus. `Say.sayForced` is never guarded: a toggle answering
"Marked" twice is answering twice. Everything dropped is logged with the reason,
so a missing announcement can be traced rather than guessed at.

The guard is a safety net, not a licence. Speech that duplicates the reader is
still a fault to fix where it is written; the net keeps it from reaching the
person while it is still there.

## Evidence for the AI

Building with an AI goes as fast as the evidence it is given. Four records make
up a session, and between them they say what happened without anybody having to
describe it:

- **The build log** -- `logs\<App>-build-<date>-<time>.log`: every command the
  build ran and its exit code.
- **The release log** -- `logs\<App>-release-<date>-<time>.log`, from tagRelease.
- **The runtime log** -- under `%LOCALAPPDATA%\<App>\logs`: not only what the
  program did, but **what came in and what went out** -- every key it saw, by its
  Homer name; every command it ran; and every sentence it spoke through Say,
  including those withheld because extra speech was off. Read top to bottom it is
  the session as it happened. `Say.onSpoken` sends speech to the app's log.
- **The screen reader's speech history** -- what the user actually heard, which is
  the one thing the program cannot log itself. In JAWS, Insert+Space then
  Control+H copies the whole history to the clipboard, and Insert+Space then
  Shift+H clears it, which is worth doing just before a session you mean to
  share. NVDA's Speech Viewer, on its Tools menu, shows the same.

The first three are gathered by zipping the logs folders. When a bug is hard to
find, the fix is often first a better log: add what was missing, reproduce, and
look again. Multiple rounds of that are normal, not a failure.

A speech history is not a strict sequence -- a line heard twice may be a say
line or an arrow up and back. And someone else's history holds their whole
session, so use it only as far as they agreed.

## Why Homer menus are long and flat

Homer programs have large, flat command spaces on purpose. For a screen reader
user, pressing Down Arrow again is cheaper than entering a submenu: Enter or
Right Arrow, waiting for focus to settle, often some extra speech, exploring, and
then a careful Escape or Left Arrow back -- careful, because one press too many
closes the whole menu system -- and waiting for focus to settle again at the
point you left.

A flat menu is only fast if the keys behind it can be remembered. That is why the
letter rules below matter as much as they do: a key that is recalled rather than
looked up is a command that is available at once, without walking any menu.

**Submenus, when they earn it.** Never more than one level deep. Use one only
when it helps a screen reader user more than it costs:

- to gather many **rarely used** items that would otherwise be arrowed past every
  time, such as a program's secondary documents;
- to open a **fresh set of initial letters** for a group large enough to run out
  of them, such as DbDo's thirty-seven Say commands;
- where flattening would push the parent menu past about **25 items**, the limit
  the Windows UX guidelines set for one menu level.

The published guidance agrees on the depth: Windows' own guidelines recommend a
single level of cascading menus and warn against putting frequently used
commands in one, and Visual Studio's say never to cascade past one level.

## Function-key families

Each function key is a family of related commands, drawn from Windows and Office
habits and extended. A command that belongs to a family takes a key from it; a
key that belongs to one family is not spent on another.

- **F1, help.** F1 the guide, Shift+F1 the history of changes, Alt+F1 About,
  Control+F1 the key describer. The rest of the family opens other documents.
- **F2, editing or renaming,** as F2 renames a file in Windows.
- **F3, searching** and repeating a search.
- **F4, picking, saying or closing open windows.** F4 picks one, Shift+F4 says
  which are open, Control+F4 closes this one.
- **F5, refreshing.**
- **F6, moving focus among panels.** Control+Tab and Control+Shift+Tab move among
  the program's windows -- call them "DbDo windows", not "MDI child windows".
- **F7, spell checking or other review.**
- **F8, selection,** copying all, or saying all.
- **F9, a more readable view,** such as extracting the main content in HomerView.
- **F10, menus.** F10 the menu bar, Shift+F10 the context menu, Alt+F10 the
  alternate menu.
- **F11, the version.** Elevate sounds like eleven.
- **F12, opening or closing files, or AI.**

## Two rules for letters

**Universal, for every key and every menu in every Homer app.**

1. **A trigger letter is the first letter of one of the command's words.** Never
   a letter from the middle of a word. It is better to have no letter, and no
   key, than one whose letter has to be memorised rather than understood.
   Standing exceptions, because the association is strong in another way: **X**
   for a word with the "ex" sound -- Export, Exit, Extract; **Shift reversing**
   a command whose name begins Un-, as Control+M marks and Control+Shift+M
   unmarks; and **Z for sleep**. Every Z key is a toggle that wakes a behavior
   or puts it to sleep -- catching some Z's -- and Control+Z's undo-and-restore
   sense in Windows sits with it. Few English words contain a Z, so this is the
   letter's best use.
2. **In a menu, the trigger letter is the letter of the item's hotkey,** when the
   hotkey has one. If the hotkey is Control+Q, the menu letter is Q, never
   another. Two items may then share a letter; Windows cycles through them, and
   that is better than a letter that contradicts the key.

When a key's letter starts none of its command's words, rename the command if a
word honestly carries it -- Open Table in New Window on Control+Shift+T -- and
rebind it if not. When nothing free fits, leave the command on its menu with no
key at all.

**Never replace a menu item's accessible name**, which hides its letter from the
screen reader. If a reader then announces a letter that does not work, that is
the reader's fault -- but the program must not give it cause.

## Hotkeys.md

Generate it from the source rather than keep it by hand: every key lives in one
place in the code, and a list kept by hand drifts the first time a key changes.
DbDo's `scripts/makeHotkeys.py` is the model; `build<App>` runs it before the
documents are converted.

Three sections, each an H2 with H3 groups inside: **by menu**, **by key** (grouped
by modifier family, function keys together), and **by command**. Every entry is
one list item whose lines are joined with a backslash hard break -- the sorted-on
thing, what it does, then the other half of the pair. Lists, because pandoc line
blocks show their bars on GitHub and blank-line paragraphs split one key into
three unrelated things. The **memory association** for every key is written once,
in the by-menu section, beside its description; a group whose keys share a reason
gets one line above them instead. The rules behind every association open the
document.

## Say the word the key comes from

**Universal, and not only in tutorials.** Wherever a key is introduced -- a
tutorial, a guide, a status line, a message box -- name the word its letter
comes from: "Shift plus C is Say Cell", "Control plus W sets the Where filter",
"F2 edits in place, the same F2 that renames a file in Windows". A key whose
mnemonic goes unsaid is a key somebody has to memorise rather than understand,
and the association is the whole reason that key was chosen over another.

Where the mnemonic is a Windows convention rather than a Homer one, say that
instead: it is the memory the person already has.

**And this applies to headings and titles, which is where it is easiest to
miss.** A tutorial called "Sorting and Filtering" teaches the wrong letter: a
reader reaches for S, and the key is Control+O, because the command is Order.
The heading is called "Order and Where Filter" instead -- the words the keys
come from, with the plain-language idea alongside them in the first sentence
rather than in the title.

The test: **if the heading were the only thing somebody remembered, which key
would they press?** Titles that fail it:

- "Sorting" for Order, on O
- "Choosing columns" for Select, on S
- "Producing output" for Report, Save and Copy, on R, S and C
- "Adding a record" for New, on N
- "Searching" for Find and Jump, on F and J

# Logging

Every Homer program writes a log, and so does every Homer installer. This is not
a debugging aid switched on when something goes wrong; it is on always, because
the thing that goes wrong is never reproducible on demand. Writing a line costs
microseconds. Not having the line costs an evening.

## Where a log goes, and what it is called

    %LOCALAPPDATA%\<App>\logs\<App>-<yyyymmdd-hhmmss>.log        one per run
    %LOCALAPPDATA%\<App>\logs\<App>-setup-<yyyymmdd-hhmmss>.log  one per install

One folder holds the whole story of a program on a machine: the install, and
every run since. Beside the program will not do, because a program under Program
Files cannot write next to its own .exe.

One file per session, named for the moment the session began, rather than one
file appended to forever. A user who reports something an hour later still has
the log from when it happened, and the log being read is never the log being
written. The most recent thirty are kept and the rest deleted, which reaches
back through a few weeks of ordinary use and keeps the folder readable.

A build script is the exception, and it stays one: `build<App>.log` sits beside
the build script, because that is a developer's file and the developer is
standing in that folder.

## Writing to it

`Log` in C# and `homer.log` in Python are the same class in two languages, with
the same method names, so a log written by either reads the same:

    using Homer;                           from homer import log
    Log.start("JobDo");                    log.start("JobDo")
    Log.section("Reading the database");   log.section("Reading the database")
    Log.keyValue("Path", sPath);           log.keyValue("Path", sPath)
    Log.info("4 rows loaded");             log.info("4 rows loaded")
    Log.warn("No index; this is slow");    log.warn("No index; this is slow")
    Log.command("pandoc x.md", iCode);     log.command("pandoc x.md", iCode)
    Log.error("The file is locked");       log.error("The file is locked")
    Log.exception(oError);                 log.exception(oError)
    Log.close();                           log.close()

`start` writes a header block first: the version, the log's own path, the
program, the working directory, the command line, the Windows build, the user,
the machine, and -- in C# -- which screen reader `Say` can reach. All of it is
what somebody will want later and cannot work out afterwards.

Nothing in either throws. A program whose logging fails should still run.

## What to log

- The environment and every effective setting, at startup.
- Every external command, with its exit code. `Log.command` exists for this.
- Every error, with its stack or traceback. The stack is the part that saves the
  evening, so it is never left out.
- Every decision the program made that a user might question: which file it
  chose, which fallback it took, what it skipped and why.

And the rule that governs all of it: **the console is for a person; the log is
for debugging**. Short plain sentences on screen, everything else in the file. A
log line is never spoken.

## What gets published

## A whitelist, not a list of exclusions

`RepoFiles.txt` names what the repository carries. `homerTidy --gitignore` turns
that into a `.gitignore` that ignores everything and then puts back exactly what
was named:

    /*
    !/.gitignore
    !/ReadMe.md
    !/CSharp/

A list of exclusions is only ever as complete as the last time somebody
remembered to add a line, and the file that gets pushed by accident is always
the one nobody thought of. Turning it around costs one line in `RepoFiles.txt`
before a new file can be committed -- which is also the line that records why
the file is there.

`homerTidy --do-it` rewrites the whitelist on every pass, so `RepoFiles.txt` and
`.gitignore` cannot drift apart.

## What is public and what stays on your machine

Public, because somebody rebuilding the program needs it:

- the source, the installer script, `build<App>.cmd`, `version.txt`
- `RepoFiles.txt` and the generated `.gitignore`
- the documentation set, in both `.md` and `.htm`
- `homerFinish.cmd` and the `install*.cmd` scripts the installer ships

Private, and in the never-pushed list whatever `RepoFiles.txt` says:

- `self.md` and `self.htm` -- the project's own notebook
- `tagRelease.cmd` and `tagRelease.ps1` -- a maintainer's tools, and noise in a
  source browser
- `create<App>Repo.cmd` and `.ps1` -- run once, then never again
- every `.log`, `notes\`, `Version.cs`, `version.py`, `__pycache__\`
- the build products: `<App>.exe`, `<App>_setup.exe`, any fetched `.dll`

The build products are release assets rather than repository content. A
repository that carries its own binaries is slow to clone and wrong by the
second commit.

# self.md, the project's notebook

Every Homer project carries a `self.md`, and it is never published.

It holds what a repository cannot: a decision and the alternatives it beat, a
finding somebody would otherwise learn the same slow way, an honest open item.
`History.md` is public and is about releases; `self.md` is internal and is about
thinking. Keeping them apart is what lets both be truthful.

The form is fixed so it stays readable as it grows:

- every entry starts at heading level 2 with its date, newest first
- headings below that are level 3 and further down
- entries are audits, plans, post-mortems and findings, not a diary

`newHomerApp` writes a starter into every new app. The kit's own `self.md` opens
with a report on what a full reading of the Homer apps found, and a review of
each of the kit's inclusion decisions against it -- which is the shape a first
entry should take.

# The installer's log

`SetupLogging=yes` makes Inno write a detailed log of every file, registry key
and run entry. The template's `[Code]` section copies it into the program's own
logs folder when setup finishes, after the final-page checkboxes have run, so
the copy includes what they did.

One caveat, stated because it will be noticed: the installer runs elevated, so
`{localappdata}` is the profile of whoever answered the elevation prompt. When
that is a different account from the one that will use the program, the setup
log lands in the administrator's folder. The program's own logs always land in
the user's.

## Later

Logging is not optional today, on purpose. When it becomes optional, the switch
belongs inside the `Log` class -- one setting, read once -- and not as an `if`
in every caller.

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
- **homerTidy** -- the folder and the repository, surveyed together and fixed in
  one pass. It prints the plan and stops; `--do-it` carries it out. In the
  folder: empty files deleted, duplicates and files the project does not name
  moved into `notes\logs`, `notes\drafts`, `notes\mail`, `notes\archives` or
  `notes\other`. In the repository: tracked files that do not belong untracked
  and added to `.gitignore` under a dated comment, then committed and pushed.
  Anything larger than 10 MB in the history is reported with the command that
  would remove it, and never rewritten automatically. What belongs is decided by
  the project's own `<App>_setup.iss` and `RepoFiles.txt`, so there is no list to
  maintain. `--folder-only` and `--repo-only` do one half.
  Log: `homerTidy.log`.

  A file that is large and fetched at run time -- a model, a converter, an
  installer payload -- belongs in neither place. The app's own install script
  should get it, and homerTidy reports such a file rather than guessing.
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
- **It knows what is already installed.** The `[Code]` section reads the version
  of any previous install from the app's own uninstall key. The welcome page
  says "Install", "Update from X to Y" or "Reinstall", and each component
  checkbox is a pair of `[Run]` lines gated by a `Check:` function, so the
  wording matches the situation instead of always saying "Install".
- **Screen reader scripts are checked by default.** A checkbox that installs an
  app's JAWS scripts or NVDA add-on is never `unchecked`. A blind user
  installing a Homer tool wants them, and a cleared box they have to notice is
  the friction this suite exists to remove.
  `installScreenReaderSupport.cmd` does the work: it unpacks `<App>_JAWS.zip`
  into every JAWS settings folder it finds and hands `<App>.nvda-addon` to NVDA,
  skipping whichever is absent.
- **The last two checkboxes are always the same two**, in this order:
  documentation, unchecked, then launch, checked.
- **The Results box comes before the launch.** The launch entry runs
  `homerFinish.cmd` rather than the program. That script reads the setup log,
  shows one Results box saying what this install actually did, and starts the
  program only when the box is dismissed. Being last in `[Run]`, it runs after
  every other checkbox, so the box can report all of them, and the program's
  window cannot cover the summary.
- **The uninstall removes the settings too**, and never touches what the user
  made with the program.

# AI-assisted coding

## Why the name

An AI can write the fruit basket program in a minute. It can write a passable
one in any of a dozen languages, and it will not stop to ask a single question
worth asking. That is what makes "vibe coding" a poor name for what happens
next: the vibe is not the hard part.

The hard part is knowing, before the AI starts, what a good program is:

- what the platform's conventions already are, so a program does not invent its
  own and make every user learn them
- what the library can do, so the request is for the thing it does well rather
  than the thing it can be forced into
- what a screen reader already says, so the program does not say it again
- where the focus should be after every action
- what the user will do next, and how many keystrokes it takes them

None of that comes out of a model. All of it can be given to one, and the giving
is the skill. **AI-assisted coding** is that skill: the AI types, and the
builder decides.

This kit is what makes the decisions transmissible. Every convention in it was
paid for by somebody's afternoon, and each is written down here so it can be
handed to an AI in one sentence instead of discovered again.

## The method, in four moves

The kit is built around the same four moves a careful builder makes with an AI,
and each has something in the kit that carries it:

1. **Specify before you generate.** Write `accept.inix` first: what must be true
   for this to be finished, stated so a script can settle it. An AI asked for
   "a tool that does X" gives you its idea of done; an AI asked to satisfy five
   named checks gives you yours.
2. **Build in small, recoverable steps.** One change, one build, one run of
   `checkHomerApp`, one commit. `version.txt` and `tagRelease` mean any release
   can be returned to, and `homerTidy` means nothing unintended is ever pushed.
3. **Verify without sight.** `checkHomerApp` for what a script can settle, the
   session log for what happened, and your own ears for what the log cannot
   hold. The evidence report separates the three.
4. **Package, document and defend.** The build makes the installer, the document
   set travels in both Markdown and HTML, and the evidence report answers the
   only question that matters at the end: what gives you confidence that it
   works?

## The three sentences

Most of the value of this kit reaches an AI in three sentences. Say them at the
start of a session and the difference is immediate:

1. "Use the Homer classes in `C:\HomerDev\CSharp` (or `\Python`); build the
   dialog with Lbc, in the order the user should tab."
2. "Write in Camel Type, as `C:\HomerDev\help\CamelType_CSharp.md` describes."
3. "Follow `C:\HomerDev\HomerDev.md`: speak only what the screen reader cannot
   know, save each answer when it is given, match nouns to counts."

Everything after that is ordinary review: read what came back, run it, and ask
for the one thing that is wrong.

## How to teach with it

The fruit basket is the exercise, and it has been since 2005, because it is
small enough to hold in your head and big enough to get wrong in every
interesting way. A good session runs in this order:

1. **Ask an AI for the fruit basket program**, with no kit and no conventions.
   Read what comes back. It works. Note what it does not do: where the focus
   goes, what it says when the field is empty, whether the basket survives
   being closed.
2. **Read `Templates\samples\FruitBasketCs.cs`.** Twelve marked blocks, and
   nine marked decisions inside them. Each decision is one a program has to get
   right and an AI will not make for you unless you ask.
3. **Ask for the same program again**, this time with the three sentences
   above. Compare.
4. **Open `Templates\samples\FruitBasketPy.py` in a second window** and
   walk the two files block by block. Same twelve blocks, same twelve titles,
   same function names, same nine decisions. The language changed; the design
   did not. That is the lesson worth keeping.
5. **Change one thing.** Add a Clear button, or sort the basket, or keep a
   count. Watch which of the nine decisions the change touches.

## Twelve blocks, two languages

`FruitBasketCs.cs` and `FruitBasketPy.py` are the same program in two languages,
written to be read side by side in two windows. `FruitBasketMdi.cs` is the third
shape and marks only what changes when a program holds several windows at once. Every section of each carries the same marker:

    ---- BLOCK n: <title> ----

Twelve blocks, the same twelve numbers and the same twelve titles in both
files: what this file needs, names, where the basket is kept, the dialog built
in the order it is read, the buttons that act without closing, one place that
knows what every button does, what the screen reader cannot know, add a fruit,
delete a fruit, sort the basket, the report, and the way in.

They do not line up line for line, and trying to make them would teach the
wrong thing. C# needs a class where Python needs none; Python needs no type on a
variable. What matters is that nothing appears in one file without a counterpart
in the other, and that the counterpart carries the same name -- `addFruit`,
`basketState`, `handleButton`, `saveBasket`, `showReport`, `showState`,
`sortBasket` in both.

Where the two genuinely differ, the comment says so at the place it happens.
There are three such places, and each is worth the minute it takes to read:

- **Block 5, the buttons that act without closing.** Each library has one way
  of saying "this button does work and leaves the window open". In C# a button
  added with `addButton` has an ordinary `Click` handler and only the buttons
  named in `runWithButtons` end the dialog. In Python the dialog's own handler
  is given every press and keeps the window open by answering `False`. Both
  files then route every press through one `handleButton`, so the dispatch
  reads the same.
- **Block 7, the counts.** `Util.stringPlural` in C# returns the number and the
  noun together; `util.stringPlural` in Python returns only the noun. Same name,
  different shape. The samples each use their own correctly and say so, because
  a reader comparing the two files deserves to know it is a wart rather than a
  design.
- **Block 11 and `showState`.** Lbc gives a C# dialog a status line at the foot;
  a wx dialog has none, so the Python file puts the same sentence in the window
  title.

## What the samples borrow rather than write

Everything the dialog does for a screen reader comes from the kit and costs one
call. None of it is in either sample, which is the point:

- access keys, from an ampersand in a label and nothing else
- bands, so a field and its button share a row
- Control+Enter accepting from any control, including a list or a memo
- the Help window, listing every field with its tip -- and the tips themselves,
  spoken in the status line in C# and on Shift+F1 in Python
- line-editing chords inside the field: copy or cut the current line with no
  selection, mark a selection in two keystrokes, read all, delete the line
- search inside the list on Control+J, repeated with F3, and copy on Control+C
- speech that reaches JAWS, NVDA and Narrator without the program knowing which
  is running

## The nine decisions

They are marked DECISION 1 to DECISION 9 at the place each occurs, the same nine
in both samples, so the two can be read side by side:

1. **Which library.** Lbc, not hand-placed controls. An AI defaults to placing
   controls; that works and its tab order is an accident.
2. **Add order is focus order.** No `TabIndex` anywhere. When the order is
   wrong, move the call.
3. **Bands.** What belongs on one row, and what does not.
4. **Access keys.** An ampersand is the whole mechanism. OK, Cancel and Close
   get none, because Enter and Escape are already their keys.
5. **What the screen reader already says.** It announces the window title and
   the focused control. The program says what the reader cannot know.
6. **Where the focus goes after an action.** Back where the next action starts.
7. **Counts that match their nouns.** "1 fruit", never "1 fruits"; zero said
   plainly.
8. **Saving the answer the moment it is given**, not at exit.
9. **The escape hatch.** `dlg.form` in C#, the wx control in Python, for the one
   thing the wrapper does not cover. Reach for it rarely, and say why.

A word on scale. The samples use more of Lbc than a fruit basket needs -- a
combo pick box for the sort order, a check box for the speaking, a report
window, a status line. That is deliberate: a sample exists to show what is
there. Your own program should use what it needs and nothing more. The kit is
meant to be the easy path, not a set of boxes to tick, and a dialog with three
controls in it is a perfectly good Homer dialog.

## The legacy FruitBasket collection

The original collection holds thirty-six fruit baskets in thirty-six languages
and toolkits, written between 2005 and 2015, from AutoIt and Boo through
PowerShell and wxPython. It answered a different question -- what does this
language look like -- and it answered it well.

These two answer a newer one: what does a program look like when it is built out
of components that already know the conventions. The old collection is still
worth reading for the breadth; these two are what to copy.

## Tutorials that can be heard

`Tutorial_HomerDev.inix` is the kit's own walkthrough, written in the step
format the tutorial tooling reads:

    [step]
    Say  = the narration
    Key  = the keystroke, named the way a person says it
    Hear = what the screen reader answers   (repeat for several lines)
    Note = written version only; never spoken

`scripts\buildTutorials.cmd` turns the scripts into audio **in two voices** and
into one .mkv with a chapter per tutorial. See the Spoken tutorials section for
the format, the tools, the voices and what may be published.

Windows' own voices do the speaking, so nothing is installed and nothing leaves
the machine. One `.wav` per spoken line is kept, so a single sentence can be
re-recorded without redoing the tutorial, and the parts are joined into one
`.mp3` when ffmpeg is on the PATH.

Write a tutorial the same way: one `[step]` per keystroke, the narration short
enough to say in a breath, and every screen-reader answer written as the reader
actually says it rather than as the screen shows it.

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
- Write a detailed log: `Log.start` at the top of the program, the environment
  and every setting after it, every command with its exit code, every error with
  its stack. Keep the console short.
- Put private thinking in `self.md`, not in a comment and not in History.md.
- Match the noun to the count, and treat zero as an answer.
- Sort every list alphabetically, in code and in documentation alike -- module
  lists, declarations, options, switches, catalogues of anything -- unless
  another order is clearly more logical, which chronology, a pipeline's own
  sequence, and a wizard's page order all are. A reader who knows the order can
  find an item without reading the whole list, and a list nobody sorted grows by
  accretion into one nobody can check.
- Do not police the user's language. Readability and plain-language help are
  welcome; rules about which words are acceptable are not, and any word-policing
  package in a prose checker should be left out or switched off by name.
