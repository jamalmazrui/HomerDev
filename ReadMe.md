---
title: "HomerDev ReadMe"
author: "Jamal Mazrui"
---

# HomerDev

HomerDev is the Homer Development Kit: the shared C# classes, Python modules,
build scripts and project templates that every Homer Tools program is built on.
One copy, in one place, so a fix reaches every app.

It is aimed at two readers. A developer who wants to build or change a Homer
app, and an AI asked to write one, which can be told: "use the Homer namespace
in `C:\HomerDev\CSharp` and follow HomerDev.md."

## Install

Unzip `HomerDev.zip` into `C:\HomerDev`. That is the install.

You also need, and the kit will tell you if one is missing:

- Windows 10 or later, 64-bit
- the .NET Framework 4.8 Developer Pack
- the Visual Studio Build Tools, free, for the C# compiler
- Python 3, for the kit's own scripts
- Inno Setup 6, to build an installer
- git and the GitHub CLI, to publish

If you keep the kit somewhere other than `C:\HomerDev`, set the `HOMERDEV`
environment variable to that folder.

## Quick start

### 1. Install the kit

Unzip `HomerDev.zip` into `C:\HomerDev`. That is the install. Then:

    cd \HomerDev
    buildHomerDev

It converts every document to HTML with pandoc, fetching pandoc with winget if
this machine does not have it, then checks the kit over and reports anything
wrong. The detail goes to `buildHomerDev.log` beside the script.

If you keep the kit somewhere else, set the `HomerDev` environment variable to
that folder. Every build script looks there first, then in `C:\HomerDev`, then
in the folder it is run from.

### 2. Build and run the fruit basket in C#

    cd Templates\samples
    buildFruitBasketCs
    FruitBasketCs

A window opens with a fruit field, an Add button, a basket list and a Delete
button. Type a fruit and press Enter. Arrow through the basket. Press Delete on
one. Press Report to see the whole basket in a window you can read line by line.
Close it and run it again: the basket is still there.

Then try what nothing in that program had to write:

- **Alt+F** reaches the fruit field, **Alt+A** adds, **Alt+D** deletes,
  **Alt+R** reports. One ampersand in a label is the whole mechanism.
- **Control+J** in the basket searches inside the list; **F3** repeats it.
- **Control+C** in the fruit field copies the whole line with nothing selected;
  **Alt+F8** reads the field aloud; **F8** then **Shift+F8** marks a selection in
  two keystrokes instead of holding Shift.
- **F1** opens a Help window listing every field with its explanation.
- **Control+Enter** accepts from anywhere.

All of that comes from Lbc, and the program is about 250 lines including its
comments.

### 3. Build and run the same program in Python

        buildFruitBasketPy
    FruitBasketPy

The first build makes a virtual environment beside the script and installs
PyInstaller and wxPython into it, which takes a few minutes once. What comes out
is one file: `FruitBasketPy.exe`, with Python and every dependency inside it, so
whoever you give it to needs no Python of their own.

### 4. Read the two side by side

This is the part worth the time. Both files carry the same twelve markers:

    ---- BLOCK n: <title> ----

Same numbers, same titles, same function names. Nine decisions are marked
DECISION 1 to DECISION 9 where they occur in each. They are the decisions a
working program has to get right and an AI will not make for you unless you ask
for them. The AI-assisted coding part of `HomerDev.md` is written around them.

### 5. Look at where it put things

    %LOCALAPPDATA%\FruitBasketCs

Six folders, and every one of them starts with a different letter, so you reach
any of them by typing that letter: `configs` holds the settings, `data` a
database, `scripts` your own scripts, `logs` one file per session, `results` what
the program produced, `temp` what a crash left behind. An installed program adds
`exec`, `samples` and `templates` in its own folder under Program Files.

### 6. Look at the log

    %LOCALAPPDATA%\FruitBasketCs\logs

One file per session, named for when it started, holding the environment, every
setting and every error with its stack. Every Homer program writes one, from the
same `Log` class, in the same place. So does every installer.

### 7. Build the third shape, in both languages

    buildFruitBasketMdiCs
    FruitBasketMdiCs
    buildFruitBasketMdiPy
    FruitBasketMdiPy

The same fruit basket as a multiple-document program. Press Control+N for
another basket, F4 to pick between them, Shift+F4 to hear how many are open,
Alt+F10 for every command in one list, and Control+F1 to turn on the key
describer and explore the keys without running anything.

Press Alt+Shift+S for the script list and Alt+Shift+C to change a setting while
the program is running. Both are lists you reach by first letter, which is the
whole point of them.

Homer apps come in three shapes -- a single tool with a command line and a
dialog, a desktop-only program whose dependencies decided that, and a
multiple-document program. They share almost everything; `HomerDev.md` says what
differs.

### 8. Check the whole kit with a compiler

    checkHomerDev

It audits the kit, deletes what previous builds wrote, builds all three samples
from clean, and writes an evidence report. Run it after changing anything in
`CSharp` or `homer`, and before a release. It exists because three releases in a
row shipped a fault that only a compiler could see.

### 9. Gather evidence

    cd Tools
    checkHomerApp --path ..\Templates\samples

Eleven checks run, and an `evidence-<date>.md` appears saying what was verified,
what was not checked, and what remains uncertain. Open it. The third list is the
point: it names what no script can settle, so you know where your own judgement
is still needed.

`accept.inix` beside the source is where you write what "done" means for your
own program -- a name, a command, an expected exit code -- and the checker runs
every one of them.

### 10. Start your own app

    newHomerApp JobDo               a C# app
    newHomerApp JobDo --python      a Python app

That writes `C:\JobDo` with everything a new app needs: a working one-dialog
program, the build script, the installer script, the GitHub bootstrap, the local
AI and screen reader install scripts, `RepoFiles.txt`, `.gitignore`, `self.md`
and `version.txt`. Nothing already in the folder is overwritten.

Two things need your hand, and both are marked CHANGE ME in the installer
script: a fresh AppId, and the desktop hotkey.

### 11. Build, run and publish

    cd \JobDo
    buildJobDo
    JobDo
    createJobDoRepo
    tagRelease

`createJobDoRepo` makes the GitHub repository and pushes the first commit; after
that `tagRelease` is how every release goes out. Copy `tagRelease.cmd` and
`tagRelease.ps1` from `scripts\` into the app folder first, or keep one copy in a
folder on your PATH -- they act on the current directory, so one copy serves
every project.

### Listen instead

`Tutorial_HomerDev.inix` is the same walkthrough as a spoken tutorial: what the
kit is, unarchiving it, building both fruit baskets, and hearing that the two
behave the same. `scripts\buildTutorials.cmd` renders it to audio in two voices --
the narration in one, the screen reader's answers in another -- using Windows'
own voices, with nothing installed and nothing uploaded.

    cd Tools
    buildTutorials --list
    buildTutorials ..\Tutorial_HomerDev.inix

### What gets published, and what does not

`RepoFiles.txt` names what the repository carries, and `homerTidy --gitignore`
turns that into a `.gitignore` that ignores everything else. A file dropped into
the folder is invisible to git until somebody names it. `self.md`, the project's
own notebook, is in the never-pushed list and stays on your machine.

## What is in the kit

- `CSharp\` -- twelve modules in the `Homer` namespace: Inix (settings and
  tables), KeyMap, KeyName, Lbc (dialogs), Log (the session log), Mdi
  (multiple-document frames), Paths (the folder layout), PdfRead, Say (speech),
  Util, Web, inixVert.
- `homer\` -- the same toolbox for Python and NVDA add-ons: inix, lbc, log,
  paths, say, util and web, with the same names and the same behaviour.
- `Templates\` -- the files a new app starts from.
- `scripts\` -- checkHomerApp, gitPush, tagRelease, homerTidy, buildTutorials and
  tagRelease. No editing needed; they work out the app name from the folder, and
  any of them can be run from a shared tools folder.
- `Templates\samples\` -- four fruit basket programs: the single dialog in C# and in
  Python, and the multiple-document version in C# and in Python. Each pair is
  the same program in two languages, written block for block. The teaching
  material.
- `help\` -- every document, and the tutorial scripts.

`HomerDev.md` lists every file in the kit with one line saying why it is there.

## Where the documents are

`ReadMe` and `License` are here at the top. Everything else is in `help`:

- `HomerDev.md` -- the guide: the classes, the conventions, the three shapes of
  Homer app, the folder layout, the evidence checks, and a list of every file in
  the kit with a line saying why it is there
- `Tutorials.md` -- nine worked scenarios, and the audio tutorial playlist
- `Developer.md` -- how to rebuild or change the kit
- `HomerDev_update.md` -- the briefing for bringing another Homer app up to
  the current kit: the contract, the lessons, the migration steps, and what
  DbDo and EdSharp each still need
- `History.md` -- what changed in each version, and why
- `Hotkeys.md` -- every key three ways
- `FAQ.md` -- the questions people ask, including why Windows only
- `Announce.md` -- three ready-to-post announcements, already the right length
- `Tutorial_HomerDev.inix` -- the spoken walkthrough, in two voices

## The other documents

- `HomerDev.md` -- the complete guide: the `.inix` format, AI-assisted coding
  and how to teach with the samples, Camel Type, direct speech across screen
  readers, Lbc and the standard dialogs, the launchpad app conventions, keys,
  scripts and logs, and the installer.
- `Developer.md` -- how to change the kit itself and how a fix reaches the apps.
- `Hotkeys.md` -- the keys every Homer dialog and text box gives you.
- `History.md` -- what changed, and when.
- `License.md` -- MIT.
