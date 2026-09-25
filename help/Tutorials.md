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

    scripts\buildTutorials

An app's build script runs this itself whenever a walk has no audio yet, after
refreshing the three tools from the kit into `scripts\`: `buildTutorials.cmd`,
`buildTutorials.ps1` and `makeTutorials.py`. The kit's copies are the source of
truth; the app carries copies because the tool works out the project from its
own location. Calling the kit's copy in place builds the kit's tutorials, not
the app's.

What it writes, all under the app's `help` folder:

- `tutorials\<name>.mp3` -- one file per walk, named as the script is named.
  A folder of audio files is found by anybody who looks, each is recognised as
  audio by its extension, and a person plays the one they want. There is no
  longer a single chaptered `Tutorials.mkv`; players treated it as one track.
- `tutorials\Tutorials.m3u` -- a playlist of the same files in order, which the
  Homer Player in FileDir opens as one track per walk.
- `Tutorials.md` -- the written walks, spliced between two markers the tool
  maintains, so the hand-written head of the file stays yours.
- `TutorialFeed.xml` -- a podcast feed of the audio.

A walk whose `.mp3` exists is not spoken again. Delete the file to have it
spoken again; name one script on the command line to speak just that one.

### Where the voices live

One copy, in `C:\HomerDev\exec`, fetched the first time any app's build
speaks a tutorial and found by every app's build after that. Neither piper
nor sherpa-onnx has an installer, so there is no default location the way
there is for Whisper or Pandoc; the kit is the one place every Homer app
already relies on, and `exec` is the Homer folder for binaries that are not
in git -- which is what a fetched engine and its model files are. The folder
is local to the machine (`LocalFiles.txt` names it, so it is never pushed)
and the kit's own build skips it. To keep the voices somewhere else, set the
`HOMER_VOICES` environment variable to that folder; a `Piper` or
`sherpa-onnx` folder under Program Files is found too.

### The voices, and why these

Two voices, told apart three ways: who is speaking, how fast, and how flat.
The narrator is a woman at a rate just brisker than natural; the reader a man,
faster and even, the way a screen reader sounds to somebody who listens all
day. A beta tester asked for the reader to be a bit slower, so its speed is
0.64 on piper's scale (it was 0.56), still ahead of the narrator's 0.80.
`ReaderScale` in a script's `[global]` section changes it for a series.

**Kokoro, when it can be fetched.** Re-investigated on 25 September 2026.
Kokoro-82M is an open-weight neural voice model released under Apache 2.0,
trained on public-domain audio, audio under permissive licences, and
synthetic audio -- no share-alike clause and no non-commercial clause
anywhere in its lineage, so audio made with it can be published under MIT
beside the program. It is markedly more natural than piper's medium voices.
The tool runs it through sherpa-onnx, also Apache 2.0, as a single Windows
executable with the phoneme data inside the model bundle: nothing to install.
Narrator af_sarah, reader am_michael; `KokoroNarrator` and `KokoroReader` in
`[global]` take other speaker numbers, and `Engine=piper` forces piper.

**Piper, otherwise.** kristin (LJ Speech, public domain) and john (LibriVox,
public domain), chosen for licence before sound. Most of piper's better-known
English voices cannot be used this way: lessac's corpus is research-only,
ryan and the hfc voices are CC BY-NC-SA, and libritts_r is fine-tuned from
lessac.

**Ruled out again, on the evidence available.** The voices built into
Windows, and the neural voices behind Edge's Read Aloud, come with terms
written for reading on that computer; nothing in them clearly permits
publishing recordings made with them, and the safe reading is that they do
not. Among the open models: those trained on the Emilia corpus, such as
F5-TTS, publish under a non-commercial licence; Fish Speech is CC BY-NC-SA;
XTTS is under Coqui's non-commercial model licence. Chatterbox (MIT) and
Parler-TTS (Apache 2.0) are clean on licence but need Python and, in
practice, a graphics card; Kokoro gives the same permission at a size that
runs on any processor. Licences change; the tool's log names the voice used
for every file, so a later check knows what to look at.

### Writing one

One `[step]` per keystroke. `Say` is the narration, `Key` is what to press,
`Hear` is what the screen reader answers -- repeat it for several lines -- and
`Note` is for the written version only and is never spoken.

Write every `Hear` line the way the reader actually says it, not the way the
screen looks. "1 fruit in the basket", not "Count: 1".

### How a screen reader trainer narrates

These come from a professional JAWS training recording, "Introduction to
Windows", read back through HomerScribe on 25 September 2026. A tutorial
script follows the same beats, because they are the ones a listener who
cannot see the screen has come to expect.

- **Say the key, then press it, then let the reader speak, then translate.**
  Four beats, every time. "I'll press Insert T, Tango, to read the title of
  the current window." -- key -- "Title is Excel Backstage View." -- "JAWS
  confirmed that focus is in the Excel window." In a script that is `Say`,
  `Key`, `Hear`, then a second `Say` that turns what was heard into what it
  means.
- **Spell a letter key with its phonetic word.** "Insert T, Tango." "Windows
  key D, Delta." A single letter is the easiest thing to mishear in speech,
  and the phonetic word costs half a second.
- **Quote the reader word for word, then paraphrase.** "Start list box,
  toggle start navigation menu items, collapsed, 1 of 6" is what JAWS said;
  "JAWS reads it as toggle start navigation menu items" is what it meant. The
  `Hear` line is the quotation, exact and unimproved; the `Say` after it is
  the translation. Never tidy the quotation: the learner will hear the untidy
  version on their own machine and must recognise it.
- **Say when the reader says nothing.** "When I pressed Alt F4, JAWS didn't
  say anything." Silence after a key is information the learner cannot see,
  so a script names it: a `Hear` line reading exactly "(nothing)".
- **Verify after every change of focus.** The trainer presses Insert T to
  read the window title after every switch, and says he is doing it and why.
  A script does the same after Alt+Tab, after opening a dialog, after
  closing one -- and says the word: "to verify".
- **Teach the recovery key early.** "If you type too quickly and miss what
  is spoken, press Insert Up Arrow to repeat it." The first tutorial says
  this before the first thing worth missing.
- **Use the count as orientation.** "1 of 14" and "1 of 6" are how the
  listener knows the size of the place they have landed in. When the reader
  gives a count, the `Say` line uses it: "the first of 14 icons on the
  desktop".
- **Name the control as the reader names it.** "Search edit box", "list
  box", "split button", "up down slider". A tutorial that says "the search
  field" when the reader will say "edit box" makes the listener translate
  twice.
- **Pause before the next key.** The trainer leaves a breath between the
  reader's answer and his next instruction. `Pause=1` before each `[step]`
  is the script's breath.

### How a reader phrases a control

Taken from two screen reader training classes read back through HomerScribe on
25 September 2026: one at the reader's beginner verbosity, which speaks the
whole grammar, and one at intermediate, which drops the tutor phrase at the end.
`Hear` lines are written at intermediate. Nothing here names a reader; the
grammar is common to the readers people use.

- **A window appears:** its title alone first, then the title again with the
  word dialog, then the text, then the control that has focus. "HomerScribe
  results" / "HomerScribe results dialog" / "One source done. Took 14
  minutes." / "OK button".
- **Check box:** label, "check box", state, access key. "Transcribe audio
  check box, checked, Alt plus T". Toggled by its access key, the reader says
  the whole line again with the new state.
- **Button:** label, "button", access key. "OK button". A label with a symbol
  is read as the symbol's name: "Next greater button, Alt plus N".
- **Radio button:** label, "radio button", state, position, access key.
  "Words radio button, checked, 2 of 4, Alt plus T".
- **Combo box:** label with its colon, "combo box", the value, position,
  access key. "Use keyboard layout: combo box, Desktop, 1 of 3, Alt plus L".
- **Edit box:** label with its colon, "edit", then the contents. "Source paths:
  edit, https colon slash slash ...". Select All answers "selected" and the
  text; a paste answers nothing.
- **Slider:** label, direction, value. "Rate: left right slider, 50 percent".
- **Menus:** "Menu bar" on entry; each menu as "Options menu"; each item with
  its letter after it; a submenu as "Voices submenu, V"; "Leaving menu bar" on
  exit. Opening a dialog from a menu says "Leaving menus" first.
- **Access keys are words:** the reader says "Alt plus T", never a plus sign,
  so a `Hear` line writes the words.
- **Names are read as the synthesizer reads them:** "Introduction to Windows
  dot m p 3" for Introduction_to_Windows.mp3 at the default punctuation level;
  a web address is spelled through -- "https colon slash slash www dot" -- and
  a path is "C colon backslash Users backslash".
- **The reader also confirms actions the program did not ask it to:** "Copied
  selection to clipboard", "Select All", "376 characters". A tutorial that
  copies text should expect them.
- **A direct announcement from the program is a sentence of its own:**
  "Done. Introduction to Windows dot m p 3" -- the kind, a full stop, the
  detail -- and it arrives before the results box.

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
