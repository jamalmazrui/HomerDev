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

### Where the voices live, and who fetches them

One copy, in `C:\HomerDev\exec`, and **only `buildHomerDev` fetches it**.
The kit's build passes `-fetch` to the tutorial tool; an app's build never
does. So an app's build finds the voices in the kit, or, when they are not
there, says "Run buildHomerDev" and speaks nothing -- it never downloads a
copy of its own. Neither piper nor sherpa-onnx has an installer, so there is
no default location the way there is for Whisper or Pandoc; the kit is the
one place every Homer app already relies on, and `exec` is the Homer folder
for binaries that are not in git. `LocalFiles.txt` names it as never pushed,
and the kit's own build skips it. To keep the voices somewhere else, set the
`HOMER_VOICES` environment variable; a `Piper` or `sherpa-onnx` folder under
Program Files is found too.

The sherpa-onnx package taken is the **shared** one, `win-x64-shared`, which
carries `bin\sherpa-onnx-offline-tts.exe`. The "static … lib" packages are
libraries for linking, hundreds of megabytes and no executable; one was
fetched by mistake on 25 September 2026, and the tool now removes such a
folder when it finds one.

### The voices, and why these

Two voices, told apart three ways: who is speaking, how fast, and how flat.
The narrator is a woman at a rate just brisker than natural; the reader a man,
faster and even, the way a screen reader sounds to somebody who listens all
day. A beta tester asked for the reader to be a bit slower, so its speed is
0.64 on piper's scale (it was 0.56), still ahead of the narrator's 0.80.
`ReaderScale` in a script's `[global]` section changes it for a series.

**Two engines, one each.** Kokoro speaks the narrator; piper's john speaks
the reader. Half the lines in a walk are the reader's, and piper speaks a
line in a second where Kokoro takes twenty -- on a laptop Kokoro runs at two
to three times real time, and a long unbroken line, such as a web address
spelled out as words, far slower, which is what made a build look hung on
25 September 2026. Kokoro's naturalness goes where it is heard, and a
flattened piper voice is what a reader sounds like anyway. The tool cuts
long text at sentences and commas before handing it to Kokoro, and runs it
on two threads, which measured faster than all of them. `ReaderOnKokoro=1`
in `[global]` puts the reader on Kokoro too, at the cost in minutes.

**One loudness.** Every piece is brought to the same measured loudness
before the join, so the narrator is no longer louder than the reader;
`ReaderGain` in `[global]` scales the reader's pieces on top of that, 1.0
unless set.

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

### Checking one

    scripts\checkTutorial              every help\Tutorial_*.inix
    scripts\checkTutorial Tutorial_01  one of them

The check reads each script against the format and the reader's grammar and
names the script and step for every problem: a key with no `Hear` line and
nothing naming the silence; `Alt+T` in a `Hear` line, where the reader says
the words; a screen reader named anywhere; a check box line out of the
reader's order; a file name written rather than said; a first walk that does
not teach the repeat key. `buildTutorials` runs it first and speaks nothing
while it reports a problem. Zero problems is a real answer.

### The skill, for an AI writing these

`Templates\skills\homer-tutorial\SKILL.md` is a skill for Claude, or any
assistant that reads one: the format, the four beats, the reader's grammar,
where the truth of a `Hear` line comes from (the dialog's code, the program's
own announcements, a speech history, a transcript), and the check-then-build
commands. Give it to the assistant along with the app's dialog code and it
writes walks that pass the check. Name no screen reader is in there too.

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
- **A slider with a value:** label with colon, the value, the direction, the
  position as a percentage. `Voice rate: 68, left right slider, 25 percent`.
  An edit box holding a number reads the number: `Voice pitch change
  percent: edit, 20`.
- **A tabbed dialog:** the title with "dialog", then the tab with "page":
  `Properties dialog, Shortcut page`.
- **A list view item:** name, "object" or the item's kind, position;
  typing a letter jumps and reads the item that letter reached: `Folder view
  list view, not selected, Recycle Bin object, 1 of 12` then, after J,
  `JAWS object, 5 of 12` -- the name of whatever program it is.
- **A program's own loading message is read before its title:** `Please
  wait` and then the window title, then the focused control.
- **In an edit box, the reader echoes what the keys do.** Typing speaks each
  character as it lands -- "T", "H", "E", "space" -- and "Enter" for a new
  line, "Period" for the punctuation. Right Arrow speaks the character it
  moves onto; Control plus Right Arrow speaks the word it lands at the start
  of. Backspace speaks the character it erased. An empty line is "Blank".
  Control plus Home says "Top of file" and then the first line; Control plus
  End says "Bottom of file" and then the last line, which is often "Blank".
  Home and End say nothing on their own.
- **Selecting has its own words.** Shift plus Right Arrow: the character,
  then "selected"; moving back off it: "unselected". Control plus Shift plus
  Right Arrow: the word, then "selected". Shift plus Down Arrow: "Selected"
  and the whole line. The reader's own read-selection key answers "Selection
  is" and the text. Control plus C answers "Copied selection to clipboard".
- **Reading without moving.** The reader's say-line key reads the current line
  and the cursor stays; say-word reads the word, twice for a spelling; say-all
  reads on from the cursor until Control stops it. A tutorial that types into
  a field uses say-line to verify the line, the way the trainer does.
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

`Templates\samples\FruitBasketMdiCs.cs` and `Templates\samples\FruitBasketMdiPy.py` are the worked examples, and its five marked blocks are
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
    tagRelease

`gitPush` stages everything the whitelist allows, commits with your message, and
pushes. `tagRelease` runs `tagRelease`, which reads `version.txt`, tags, and
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
> marked in `Templates\samples\FruitBasketCs.cs`.

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

<!-- walkthrough: written by makeTutorials.py, do not edit between the markers -->

## 0. The Homer Development Kit, and two fruit baskets

This is a first look at HomerDev: what it is, how to install it, and how to build and run the two sample programs. It takes about twelve minutes. You can follow along, or just listen.

**Before you start:** You need Windows 10 or later, 64-bit, and a screen reader running. Everything else the kit fetches for itself. Nothing in this tutorial costs anything.

### Step 1

HomerDev is a kit of parts for building Windows programs that work well by keyboard and screen reader. Nine C sharp classes, seven Python modules, the build and release scripts, and two sample programs that do the same job in both languages. It is free and open source. If you miss a line the reader says, Insert plus Up Arrow says it again.

The kit is at https://github.com/JamalMazrui/HomerDev

### Step 2

The idea behind it is simple. Every decision that makes a program pleasant to use without sight -- where the focus goes, what gets spoken, what the keys do -- has already been made, tested, and put in a class. You get them by calling the class rather than by remembering them.

The guide calls these the nine decisions, and both samples mark them where they occur.

### Step 3: Control+V

Start by unarchiving HomerDev dot zip into a folder called C colon backslash HomerDev. That is the whole install. Open the archive, choose Extract All, and type the folder name.

Screen reader:

- Destination, edit, C colon backslash HomerDev

Any folder works. If you put it somewhere else, set an environment variable called HomerDev to that path, and every build script will find it.

### Step 4: buildHomerDev

Now open a command prompt in that folder and run the kit's own build.

Screen reader:

- Homer Development Kit 1.4.0 in C colon backslash HomerDev
- 10 documents converted to HTML
- 0 problems found. The kit is complete.

buildHomerDev converts every document to HTML with pandoc, fetching pandoc if this machine has none, then checks the kit over: every component present, every file in the right encoding, no empty files.

### Step 5

Notice the last line. Zero problems is a real answer, said plainly. That is a rule in this kit: a count always matches its noun, and nothing reports zero as though it were an error.

"1 match", never "1 matches"; "0 matches" rather than silence.

### Step 6: cd Templates\samples

Next, the samples. Change into the samples folder under Templates. There are four files: a C sharp program, a Python program, and a build script for each. Both programs are the fruit basket -- a window with a fruit field and an Add button, a basket list and a Delete button. Blind programmers have taught with that specification since 2005.

Typed at the prompt: the reader echoes the letters, and says nothing else until the next command answers. The legacy FruitBasket collection has thirty-six of these, one per language. These two are different: they are parallel to each other.

### Step 7: buildFruitBasketCs

Build the C sharp one.

Screen reader:

- Kit, C colon backslash HomerDev version 1.4.0
- Compiler, Microsoft Visual Studio Build Tools
- Built FruitBasketCs dot exe version 1.0.0

The script finds the compiler, finds the three reference assemblies that are not on the default path, compiles the program together with the Homer classes straight out of the kit, and writes buildFruitBasketCs.log beside itself.

### Step 8: FruitBasketCs

Now run it.

Screen reader:

- Fruit Basket, the basket is empty
- Fruit, edit

The window title carries the state and the focus starts in the field, because typing a fruit is the first thing anybody does.

### Step 9: apple, Enter

Type a fruit and press Enter.

Screen reader:

- apple added, 1 fruit in the basket

One fruit, not one fruits. The screen reader announced nothing about the field or the button, because it had nothing new to say; what you heard is the program telling you what it did.

### Step 10: Tab, DownArrow

Add two more, then tab to the basket and arrow through it.

Screen reader:

- Basket, list box, apple, 1 of 3

An ordinary Windows list box. No custom control, no special mode, nothing to learn.

### Step 11: Control+J

Press Control plus J to search inside the list.

Screen reader:

- Find in list, edit

That search, and F3 to repeat it, arrived with the list box. The program contains no code for either.

### Step 12: Delete

Press Delete on a fruit you no longer want.

Screen reader:

- banana deleted, 2 fruits in the basket

The selection moves to the neighbour, so the list still has somewhere to speak from. A list with nothing selected says nothing, and a person who hears nothing assumes the program has stopped.

### Step 13: Alt+R

Press Alt plus R for the report.

Screen reader:

- Fruit basket report, read only edit

A plain read-only window you arrow through line by line and close with Escape. The same window the Help button uses.

### Step 14: F1

Press F1 for help.

Screen reader:

- Help, Fields in this dialog, Fruit, type the name of a fruit

That help was written once, as a tip beside each field, and it reaches the reader twice: in the status line when focus arrives, and in this window on demand.

### Step 15: Alt+F4

Close the program, then run it again.

Screen reader:

- Fruit Basket, 2 fruits in the basket

The basket was saved the moment each fruit went in, not on the way out. A program that saves at exit loses everything when it is killed.

### Step 16: buildFruitBasketPy

Now the same program in Python. Build it.

Screen reader:

- Creating the build environment
- Installing what the build needs
- Built FruitBasketPy dot exe version 1.0.0

The first build makes a virtual environment beside the script and installs PyInstaller and wxPython into it, which takes a few minutes once. What comes out is one file with Python and every dependency inside it, so whoever you give it to needs no Python of their own.

### Step 17: FruitBasketPy

Run the Python one.

Screen reader:

- Fruit Basket, the basket is empty
- Fruit, edit

The same title, the same first control, the same starting focus.

### Step 18: cherry, Enter

Type a fruit and press Enter, exactly as before.

Screen reader:

- cherry added, 1 fruit in the basket

The same sentence, from a different language, because both programs call the same Say class through the same kit.

### Step 19: Control+J

Tab to the basket, press Control plus J, press Delete, press Alt plus R. Every key does what it did in the C sharp version.

Screen reader:

- Find in list, edit

Two differences, and only two. The C sharp dialog has a status line at the foot; a wx dialog has none, so the Python one puts the same sentence in the window title. And the tips are on Shift plus F1 in Python rather than in the status line.

### Step 20

That is the claim this kit makes, and you have just heard it tested. Two languages, one behaviour, because the behaviour lives in the components rather than in either program.

Both source files carry twelve markers -- BLOCK 1 to BLOCK 12 -- with the same numbers, the same titles and the same function names, so they can be read side by side in two windows.

### Step 21

One last thing. Look in your local application data folder, under FruitBasketCs, then logs.

Screen reader:

- FruitBasketCs dash 2026 09 18 dash 1 3 0 5 2 2 dot log

One log per session, named for when the session began, holding the environment, every setting and every error with its stack. Every Homer program writes one, from the same class, in the same place. So does every installer.

### Step 22

That is HomerDev. The guide, HomerDev dot md, has the rest: the Lbc dialogs, the inix settings format, the coding style, the release scripts, and a part on AI-assisted coding which is what the kit is really for. Thank you for listening.

Questions and corrections are welcome. The kit is early, and it improves by being used.

**Something to try:** Build the Python fruit basket the same way, and notice that it answers every key exactly as the C sharp one did.

<!-- walkthrough ends -->
