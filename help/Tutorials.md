---
title: "HomerDev Tutorials"
author: "Jamal Mazrui"
---

# HomerDev Tutorials

Short walkthroughs of the things you will actually do with the kit. Each one is
a scenario, start to finish, with the commands you type and what comes back.

Read `ReadMe.md` first if you have not installed the kit. Read `HomerDev.md` for
the reference: what each class does and why the conventions are what they are.

## Contents

- Audio tutorials — the spoken walkthroughs and how to make more
- Scenario 1: start a new app from nothing
- Scenario 2: add a field to a dialog
- Scenario 3: work out what a key already does
- Scenario 4: turn a one-window app into a multiple-document app
- Scenario 5: find out why something failed
- Scenario 6: write down what "done" means, then prove it
- Scenario 7: change a shared class without breaking four apps
- Scenario 8: release it
- Scenario 9: ask an AI for a Homer app and get one

## Audio tutorials

The spoken tutorials live in `help`, beside this file, as `Tutorial_*.inix`.
Each is a script: what the narrator says, the key to press, and what the screen
reader answers in a different voice.

### The playlist

1. **Tutorial_HomerDev** — the kit in twelve minutes: what it is, unarchiving it
   into `C:\HomerDev`, running `buildHomerDev`, building and running both fruit
   baskets, and hearing that the two behave the same. Start here.

Two more are planned. Neither is written yet, and they are listed so the shape
of the series is clear rather than to promise a date:

2. **Tutorial_Verify** — the session that becomes the conference demonstration:
   specify a small change, generate it, reveal a plausible failure, show the
   check that catches it, fix it, and run the evidence again.
3. **Tutorial_Mdi** — the third shape, and why a window beats a tab for somebody
   using a screen reader.

### Making the audio

    cd Tools
    sayTutorial --list
    sayTutorial ..\help\Tutorial_HomerDev.inix

Two voices, from Windows' own speech: the narration in one, the screen reader's
answers in another. Nothing is installed and nothing is uploaded. One `.wav` per
spoken line is kept, so a single sentence can be re-recorded, and the parts are
joined into one `.mp3` when ffmpeg is on the PATH.

### Writing one

One `[step]` per keystroke. `Say` is the narration, `Key` is what to press,
`Hear` is what the screen reader answers -- repeat it for several lines -- and
`Note` is for the written version only and is never spoken.

Write every `Hear` line the way the reader actually says it, not the way the
screen looks. "1 fruit in the basket", not "Count: 1".

## Scenario 1: start a new app from nothing

You want a tool that renames files from a pattern. Call it PatternRename.

    cd \HomerDev
    newHomerApp PatternRename
    cd \PatternRename
    buildPatternRename
    PatternRename

`newHomerApp` writes a working one-dialog program, the build script, the
installer script, the GitHub bootstrap, `accept.inix`, `RepoFiles.txt`,
`.gitignore`, `self.md` and `version.txt`. Nothing already there is overwritten.
Add `--python` for a Python app instead.

Two things need your hand, both marked CHANGE ME in the installer script: a
fresh AppId, and the desktop hotkey.

Then open `self.md` and write the first entry: what this is for in two
sentences, which Homer components it uses, and what is still undecided. Two
minutes now saves an hour in a month.

## Scenario 2: add a field to a dialog

You want a "Prefix" box between the pattern and the folder.

Find the `add` calls in your source and put one line where the field belongs:

    txtPrefix = dlg.addInputBox("&Prefix:", "", "Text to put in front of each name.");

That is the whole change. **Add order is focus order**, so where you put the
line is where the field lands in the tab order. The ampersand is the whole of
the access key. The tip appears in the status line when focus arrives and again
in the Help window on F1.

Then check what you just did:

    cd \HomerDev\Tools
    checkHomerApp --path \PatternRename

If `&P` was already taken, the keys check says so. That is the check earning its
place: two controls claiming one letter is invisible when you read the code and
obvious when a script counts.

## Scenario 3: work out what a key already does

Before you bind Alt+Shift+R to something, find out what has it.

In an MDI app, press **Control+F1**. That is the key describer: every key now
says what it would do instead of doing it. Press the key you are wondering
about, listen, and press Control+F1 again to turn it off.

Outside a running program, `Hotkeys.md` in `help` lists every key three ways --
by key, by description, and by binding -- and `KeyMap` reports a key claimed
twice into the session log when the menus are built.

The rules that decide what you may use are in `HomerDev.md`: never Alt+Control
(Windows desktop shortcuts own it), never a key whose Windows meaning is
selection or navigation, and prefer Alt+Shift plus a letter that means something
in the command's name.

## Scenario 4: turn a one-window app into a multiple-document app

Your tool now opens one file at a time and you want several.

1. In the build script, uncomment the KeyMap and Mdi pair. They go on together:
   `Mdi.cs` registers every command with KeyMap, and turning on one without the
   other does not compile.
2. Make your form a `MdiFrame` subclass, declare the menus with `addMenu` and
   `addItem`, and call `finishMenus`.
3. Make your window a `MdiChild` subclass. Build its controls through
   `child.lbc`, which is the same builder a dialog uses, and finish with
   `finishLayout` instead of `run`.
4. Title it with `setTitle(subject, view)` and never include the app name -- the
   frame already carries it, and Windows merges the two.

What you get without writing it: the window picker on F4, the spoken window list
on Shift+F4, next and previous, close and close-others, the alternate menu on
Alt+F10, the key describer on Control+F1, about on Alt+F1, the guide on F1.

`Samples\FruitBasketMdiCs.cs` and `Samples\FruitBasketMdiPy.py` are the worked examples, and its five marked blocks are
exactly the five things that change.

## Scenario 4b: let people extend your app without your help

Drop a script into the scripts folder and it is in the program's script list, at once,
with nothing to register.

    %LOCALAPPDATA%\PatternRename\jobs\Weekly report.cmd

Press Alt+Shift+S in the app, arrow or type the first letter, press Enter. The
shipped jobs come with the program; the user's own live in the per-user tree
where an update cannot overwrite them, and both appear in one list with the
user's first.

For settings, declare what may change:

    addSetting("folder", "", "Where renamed files go.");

and the frame gives you Alt+Shift+C: a list of what is settable, one field for
the new value, saved at once and handed back to your code through
`onSettingChanged`. No settings file to edit by hand, no preferences dialog to
build, and no restart.

## Scenario 5: find out why something failed

Something went wrong and the screen said one short sentence, as it should.

    %LOCALAPPDATA%\PatternRename\logs

Open the newest file. It is named for the moment the session began, and it holds
the version, the program path, the working directory, the command line, the
Windows build, every setting, every external command with its exit code, and
every error with its stack.

If the failure was in a build rather than a run, the log is `buildPatternRename.log`
beside the build script, because that is a developer's file and the developer is
standing in that folder.

If the failure was in an install, the setup log is in the same `logs` folder,
named `PatternRename-setup-<date>.log`.

The rule behind all three: the console is for a person, the log is for
debugging. Never add a print statement where a log line belongs.

## Scenario 6: write down what "done" means, then prove it

Before you ask an AI for anything, write `accept.inix`:

    [check]
    Name   = the help text names every switch
    Run    = PatternRename.exe --help
    Expect = 0
    Wants  = --pattern

    [check]
    Name   = a bad switch is refused rather than ignored
    Run    = PatternRename.exe --nonsense
    Expect = 1

Four fields and no more. Then:

    checkHomerApp --path \PatternRename --build

It builds, smoke-runs `--help`, runs every acceptance check, and writes
`evidence-<date>.md` saying what was verified, what was not checked, and what
remains uncertain.

Read the third list. It names what no script can settle -- whether the program
does the right thing, what a screen reader actually says, whether the code is
secure -- so you know exactly where your own judgement is still required.

## Scenario 7: change a shared class without breaking four apps

You fixed something in `Lbc.cs`. Four programs compile against it.

    cd \HomerDev
    checkHomerDev

It audits the kit, checks that every module's REQUIRES line is satisfied by
every build script, deletes what previous builds wrote, and builds all three
samples from clean. Exit code 1 if anything failed.

Then build the real apps, because `checkHomerDev` does not: EdSharp, FileDir,
DbDo and HomerScribe all carry these modules, and a kit change that compiles
against three samples can still break one of them. The evidence report says so
in its uncertain list, every time.

Finally, write what you changed and why in `self.md`. `History.md` is public and
is about releases; `self.md` is where the rejected alternative goes.

## Scenario 8: release it

    cd \PatternRename
    checkHomerApp --build
    gitPush "Add the prefix field."
    gitRelease

`gitPush` stages everything the whitelist allows, commits with your message, and
pushes. `gitRelease` runs `tagRelease`, which reads `version.txt`, tags, and
publishes the installer as a release asset.

What gets pushed is decided by `RepoFiles.txt`, not by habit: `homerTidy
--gitignore` turns that list into a `.gitignore` that ignores everything else, so
a file you dropped in the folder cannot go up by accident.

## Scenario 9: ask an AI for a Homer app and get one

Three sentences carry the kit into an AI session:

> This is a Windows program for screen reader users, built on the Homer
> Development Kit at `C:\HomerDev`. Use `Lbc` for every dialog, `Inix` for
> settings, `Log` for the session log, `Paths` for folders, and `Say` only for
> what a screen reader cannot work out for itself. Follow the nine decisions
> marked in `Samples\FruitBasketCs.cs`.

Then work in this order, which is the method the whole kit is shaped around:

1. **Specify before you generate.** Write `accept.inix` first. An AI asked for
   "a tool that does X" gives you its idea of done; an AI asked to satisfy five
   named checks gives you yours.
2. **Build in small, recoverable steps.** One change, one build, one
   `checkHomerApp`, one commit.
3. **Verify without sight.** The checks for what a script can settle, the log
   for what happened, your own ears for the rest.
4. **Package, document and defend.** The build makes the installer; the evidence
   report answers "what gives you confidence that it works?"

Paste the sample into the session when the answers drift. A model that has read
FruitBasketCs writes Homer code; a model that has not writes pixel coordinates
and a tab order that is an accident.
