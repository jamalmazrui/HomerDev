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

### The pattern of ten

Every Homer program's walks follow one pattern, numbered with one digit so a
folder or player sorts them (7 October 2026, replacing the twelve):

- **0_Overview** -- what the program is, the two reader keys, and the table of
  contents.
- **1_User_Interface** -- what the program is made of and the rules its keys
  follow, each part named and then shown by the reader, with help in its four
  places.
- **2 to 8** -- seven task walks, one for each number; usually
  2_Install_and_Launch first.
- **9_Conclusion** -- the conclusion and summary, the glossary, and more
  information, with the help built into the program.

Each is three to five minutes; the overview may be shorter. The kit's own
ten: Overview; User Interface; Install and Launch; Start an App from the Kit;
Build, Check and Release; The Installer and Its Finish Page; Spoken Tutorials;
Shared Code and the Homer Player; Build with an AI Assistant; and the
Conclusion.

### Making the audio

    scripts\buildTutorials

An app's build script runs this itself on every build, and it speaks only a walk whose text changed, after
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

The audio ships: every installer and every repository carries the `.mp3`
files, made by the build before the installer is compiled, so no user ever
waits for a tutorial to be spoken. The fingerprints go to the repository
only, with the audio, so a build on another computer speaks nothing it need
not.

A walk is spoken again only when its text has changed since it was last
spoken: each `.mp3` has a `.sha256` file beside it holding the fingerprint of
the walk it came from. Dates are not used, since a walk unzipped from a kit
can look newer than audio spoken from the same text. Delete an `.mp3` to have
its walk spoken again; name one script on the command line to speak just that one.

### Where the voices live, and who fetches them

One copy, in `C:\HomerDev\exec`, and **only `build` fetches it**.
The kit's build passes `-fetch` to the tutorial tool; an app's build never
does. So an app's build finds the voices in the kit, or, when they are not
there, says "Run build" and speaks nothing -- it never downloads a
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

`.claude\skills\homer-tutorial\SKILL.md` is a skill for Claude, or any
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
  closing one -- and says the word: "to verify". Inside a dialog the key is
  **Insert Tab**, which re-reads the control with its state, position and
  hint; Insert T is for the window. The Freedom Scientific trainers use both,
  and teach both in their first module.
- **Spell a lone letter.** "Windows key R, Romeo"; "Insert W, whiskey". A
  letter is the hardest thing to hear in speech, so when the key is one
  letter, the Say line gives its alphabet word.
- **Show the hint once, then turn it off.** One step shows a tutor message;
  the next Say line says they are off from here; the Hear lines after carry
  none. That is what the trainers do, and it is what a reader at
  intermediate verbosity says.
- **One wrong turn, and the way back.** Each walk has one planned misstep --
  the wrong letter, a dialog nobody wanted -- and the Escape that undoes it,
  narrated as calmly as the rest. A walk with no misstep teaches no recovery.
- **End with the keys.** The last step is a Say line naming the two or three
  keys the walk taught, and nothing else.

`TutorialLearnings.md` in this folder gives the evidence for each of these,
from 98 transcripts of JAWS training.
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

### Show, then tell

A walk is a conversation between the two voices, not a talk by one. Whenever the narrator names a part of a program or a pattern of keys, the screen reader shows it right away: the window that comes forward, read by its title; or the control that takes focus, read as its name, its role, its value or state, and then, after a pause, its hint, such as "Type in text." or "To activate press Spacebar." The narrator then says in a sentence what was just heard. A listener who hears a list box answer "status: list box, untried, 4 of 5" learns more, and remembers it longer, than one who is told what a list box says.

checkTutorial holds walk 1, the user interface, to this: no more than two steps in a row without the reader, and the reader in at least half the steps. Other walks get a notice after three host-only steps in a row, and any narrator line over sixty words gets a notice. A reader line written from these rules rather than from a recording carries a Note asking for a live run, `buildTutorials -live`, to confirm it.

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
    check --path \PatternRename

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

    check --path \PatternRename --build

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
    check --build
    push "Add the prefix field."
    release

`push` stages everything the whitelist allows, commits with your message, and
pushes. `release` runs `release`, which reads `version.txt`, tags, and
publishes the installer as a release asset.

What gets pushed is decided by `RepoFiles.txt`, not by habit: `tidy
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
   `check`, one commit.
3. **Verify without sight.** The checks for what a script can settle, the log
   for what happened, your own ears for the rest.
4. **Package, document and defend.** The build makes the installer; the evidence
   report answers "what gives you confidence that it works?"

Paste the sample into the session when the answers drift. A model that has read
FruitBasketCs writes Homer code; a model that has not writes pixel coordinates
and a tab order that is an accident.

<!-- walkthrough: written by makeTutorials.py, do not edit between the markers -->

## 0 - Overview

What the Homer Development Kit is, in a paragraph; the two reader keys every walk assumes; then the table of contents, one line per walk.

**Before you start:** Nothing is needed; this walk is listened to.

### Step 1

HomerDev is a kit of parts for building Windows programs that work well by keyboard and screen reader: shared C sharp classes and Python modules, build and release scripts, installer parts, templates for a new app, and skills that teach an AI assistant the house rules. Every decision that makes a program pleasant to use without sight -- where the focus goes, what is spoken, what the keys do -- has been made once and put in a class, so an app built on the kit inherits it. DbDo, EdSharp and FileDir are built on it, and these walks use their voices to show what the kit's code does for a person.

### Step 2: Insert+Up Arrow

You know your screen reader's own keys already, and three of them are worth remembering whenever you feel lost or unsure. Insert plus Up Arrow says the line you are on again.

Screen reader:

- Hello, world.

### Step 3: Insert+Tab

Insert plus Tab says what has the focus: its name, its role, and its value or state.

Screen reader:

- Untitled, edit, multiline, Hello, world.

### Step 4: Insert+T

Insert plus T says the title of the window.

Screen reader:

- EdSharp, Untitled

### Step 5

If you set your screen reader to use Caps Lock in place of Insert, Caps Lock works the same way for all three.

### Step 6

Now the table of contents. I say the number and the title; the reader says what the walk covers.

### Step 7

One, User Interface.

Screen reader:

- What a Homer program is made of, heard in DbDo, EdSharp and FileDir, and the rules every key follows, so a key can be guessed.

### Step 8

Two, Install and Launch.

Screen reader:

- Unarchiving the kit, running its own build, and launching the sample program it builds.

### Step 9

Three, Start an App from the Kit.

Screen reader:

- A new app from the template: its files, its first build, its first run.

### Step 10

Four, Build, Check and Release.

Screen reader:

- What build does, stage by stage; what check refuses; what release publishes.

### Step 11

Five, The Installer and Its Finish Page.

Screen reader:

- The shared installer parts: boxes that say their state, the results box, the summary.

### Step 12

Six, Spoken Tutorials.

Screen reader:

- Writing a walk, the two voices, the pattern of ten, and the tool that speaks and measures them.

### Step 13

Seven, Shared Code and the Homer Player.

Screen reader:

- The classes every app uses, and the player heard in FileDir and DbDo alike.

### Step 14

Eight, Build with an AI Assistant.

Screen reader:

- A feature written with an AI assistant in the kit's house style: the skills, the three sentences, and the check that proves it.

### Step 15

Nine, Conclusion.

Screen reader:

- The conclusion and summary, the words the kit uses, the help built into every program, and where to learn more.

### Step 16

Ten walks, three to five minutes each, under an hour together: the overview, the user interface, seven tasks, and the conclusion. They are a course, not a reference: each one assumes those before it.

**Something to try:** Listen to the walks in order; each one assumes the ones before it.

## 1 - User Interface

What a Homer program is made of, each part named by the narrator and then shown by the screen reader -- the window, the main view, the dialog, the Say keys, the pick list, the menus -- then the rules every key follows, so a key can be guessed in a program you have never opened, and the four places help lives.

**Before you start:** Nothing is needed; this walk is listened to.

### Step 1

A Homer program is heard before it is seen. I name each part; the reader shows it as it would on your machine: name, kind, value and state, then a hint. After that, the rules that let you guess any key.

### Step 2: Alt+Control+D

First, the window. One program, one copy. Its desktop key opens it or brings it forward. Alt plus Control plus D, D for DbDo.

Screen reader:

- DbDo
- DbDo ready

### Step 3: Alt+Control+E

The title, then the program's greeting. Next, the main view, a control the reader knows. In EdSharp, an edit box.

Screen reader:

- EdSharp
- Untitled, edit, multiline, blank
- Type in text.

### Step 4: Alt+Control+F

Name: Untitled. Role: edit, multiline. Value: blank. Then the hint, for a newcomer. In FileDir, the main view is a list.

Screen reader:

- FileDir
- ReadMe dot m d, 1 of 24

Confirm this list item's wording with a live run: buildTutorials -live.

### Step 5: Control+K

A list item says its name, then where it sits: 1 of 24. That count is your map. Now a dialog, built the same way in every Homer program: a label, then the control it names. Control plus K, K for Keywords.

Screen reader:

- Keywords dialog
- Keywords: edit
- Type in text.

Confirm with a live run: buildTutorials -live.

### Step 6: Tab

The title first, then the label read before its box, then the hint. Tab moves through the controls in the order they were added; OK and Cancel come last.

Screen reader:

- OK button
- To activate press Spacebar.

Confirm what Tab reaches first with a live run: buildTutorials -live.

### Step 7: Alt+K

Enter presses OK, Escape is Cancel, and Control plus Enter submits from any control in the dialog. Alt plus an underlined letter jumps straight to its control.

Screen reader:

- Keywords: edit
- Type in text.

### Step 8: Escape

Alt plus K, K for Keywords, and focus is back on the box. Escape closes the dialog.

Screen reader:

- FileDir

### Step 9: Alt+Control+D

Now the Say keys, in DbDo. They ask a question and change nothing.

Screen reader:

- DbDo

### Step 10: Shift+Z

Shift plus Z is Say Status: Z, the end of the alphabet, where the status line sits.

Screen reader:

- jobs, 12 records, no filter, sorted by employer

### Step 11: F4

Table, count, filter and sort in one breath; pressed twice, the words open in a window. Where a field has fixed values, F4 opens them.

Screen reader:

- status: list box, untried, 4 of 5
- To move through items press Up or Down Arrow.

### Step 12: F10

Name, role, value, position, then the hint. A letter jumps to a value, so nothing is typed that could be mistyped. Next, menus, which say their own keys. F10 opens the menu bar.

Screen reader:

- Menu bar
- File menu

### Step 13: Down Arrow

I arrow down to the first item.

Screen reader:

- Open Database..., Control plus O, O

### Step 14: Escape

The item, its hotkey, then its letter: learn a key from the menu once, then skip the menu.

Screen reader:

- Leaving menus

### Step 15

Now the rules behind every key, the same in every Homer program. The word gives the letter: Control plus K is Keywords wherever there is searching. Control plus a letter does something; Shift or Alt plus a letter asks and changes nothing.

### Step 16

Adding Shift to a doing key reverses it: Control plus M marks, Control plus Shift plus M unmarks. Alt plus Shift plus a letter is a command with no control of its own: Alt plus Shift plus P plays a stream.

### Step 17: Insert+T

The function keys follow Windows: F1 help, F2 edit, F3 find again, F4 pick, F10 the menus. Anything with Insert belongs to the screen reader; a Homer program never uses it. Insert plus T is the reader's own: the title.

Screen reader:

- DbDo

### Step 18: Control+F1

Two keys explain the keys. Control plus F1 is the Key Describer: while it is on, each key says what it does instead of doing it.

Screen reader:

- Key Describer On

### Step 19: Control+F1

Again, and it is off. Hotkeys, in the Help menu, lists every key by menu, by key and by command.

Screen reader:

- No Key Describer

### Step 20

Help is in four places, the same in every Homer program. I say which; the reader says the key. The guide.

Screen reader:

- F1, the guide

### Step 21

The changes, release by release.

Screen reader:

- Shift plus F1, History

### Step 22

The version, and a check for a newer one.

Screen reader:

- Alt plus F1, About

### Step 23

The name of any key you press.

Screen reader:

- Control plus F1, Key Describer

### Step 24: Alt+Control+E

The Help menu holds all four, with Hotkeys and Play Tutorials. Now a planned misstep: a Say key belongs to the window, not a field. In EdSharp's edit box, I press Shift plus Z.

Screen reader:

- EdSharp

### Step 25: Shift+Z

Shift plus Z.

Screen reader:

- Z

### Step 26: Control+Z

The reader echoed the letter, and the box now holds a Z. Control plus Z undoes it.

Screen reader:

- Undo

### Step 27

What this walk taught. I name the part or the command; the reader says the key.

### Step 28

Say Status, a question that changes nothing.

Screen reader:

- Shift plus Z

### Step 29

A field's fixed values.

Screen reader:

- F4, pick list

### Step 30

What any key does, without doing it.

Screen reader:

- Control plus F1, Key Describer

**Something to try:** Open any Homer program and guess three keys from their words, then check each with Control plus F1.

## 2 - Install and Launch

One want: the kit on this computer, proved working. Unarchiving it, running its own build, building the C sharp sample and launching it -- the first Homer program you hear -- and one planned misstep. This walk assumes walk zero.

**Before you start:** Windows 10 or later, 64-bit, a screen reader running, and HomerDev dot zip downloaded. Everything else the kit fetches for itself.

### Step 1: Control+V

The want: the kit on this computer, proved working. Unarchive HomerDev dot zip into a folder called C colon backslash HomerDev. That is the whole install: open the archive, choose Extract All, and type the folder name.

Screen reader:

- Destination, edit, C colon backslash HomerDev

### Step 2: build

Open a command prompt in that folder and run the kit's own build. The reader echoes what is typed and says nothing else until the command answers.

Screen reader:

- Homer Development Kit 1.52.8 in C colon backslash HomerDev
- 10 documents converted to HTML
- 0 problems found. The kit is complete.

### Step 3

Notice the last line. Zero problems is a real answer, said plainly. That is a rule in this kit: a count always matches its noun, and nothing reports zero as though it were an error.

### Step 4

What build did. It converted every document to HTML with pandoc, fetching pandoc if the machine had none; it checked the kit over -- every component present, every file in the Homer encoding, no empty files -- and it packed the sixteen skills an AI assistant reads. Its log is in the logs folder, every command with its exit code.

### Step 5: cd Templates\samples

Next, the samples: change into the samples folder under Templates. Two programs, a C sharp one and a Python one, and a build script for each. Both are the fruit basket: a window with a fruit box, a basket list, and a report. The command is silent until the next one answers.

Screen reader:

- Kit, C colon backslash HomerDev version 1.52.8
- Compiler, Microsoft Visual Studio Build Tools
- Built FruitBasketCs dot exe version 1.0.0

### Step 6: FruitBasketCs

Now run it. This is the launch: the first Homer program you hear.

Screen reader:

- Fruit Basket, the basket is empty
- Fruit, edit

### Step 7: apple

Type a fruit and press Enter.

Screen reader:

- apple added, 1 fruit in the basket

### Step 8: Tab

Add two more, then Tab to the basket and arrow through it.

Screen reader:

- Basket, list box, apple, 1 of 3

### Step 9: F1

F1 for help: every Homer dialog describes its own fields.

Screen reader:

- Help, Fields in this dialog, Fruit, type the name of a fruit

### Step 10: Alt+F4

Close it with Alt plus F4 and run it again: the basket was kept between sessions, in your local application data, without being asked to.

Screen reader:

- Fruit Basket, 2 fruits in the basket

### Step 11

The Python one builds and runs the same way, and answers every key exactly as the C sharp one did -- walk three hears it. Two languages, one behaviour, because the behaviour lives in the kit's components rather than in either program.

### Step 12

A planned misstep. Run build in an app folder whose kit is older than the app needs, and the build refuses in one line.

Screen reader:

- ERROR: DbDo needs HomerDev 1.52.8 or later, and C colon backslash HomerDev is 1.52.6.

### Step 13

Where things went. The kit stays in its folder and is never installed in Program Files; each sample keeps its data and its session log under your local application data, in a folder named for it -- the layout every Homer app follows.

### Step 14

What this walk taught. I say the idea or the key; the reader says the command or the name.

### Step 15

Run the kit's own check and documents.

Screen reader:

- build

### Step 16

Build the C sharp sample.

Screen reader:

- buildFruitBasketCs

**Something to try:** Unarchive the kit, run build, build and run the C sharp fruit basket.

## 3 - Start an App from the Kit

One want: a new program of your own, built on the kit, running by the end of the walk. newHomerApp, what it makes, the first build, the first run, the first change, and where the kit's classes come in. This walk assumes walks one to three.

**Before you start:** The kit is at C colon backslash HomerDev, and a command prompt is open there.

### Step 1: newHomerApp Recipes

The want: a new program of your own, built on the kit, running by the end of the walk. In the kit folder, newHomerApp with a name makes the folder and its files.

Screen reader:

- Made C colon backslash Recipes with 14 files. Run build there.

### Step 2

What is in it. The program file, Recipes dot cs, with the Homer classes referenced from the kit; build dot cmd, the stages every Homer build runs; the installer script with the shared finish page; accept dot inix, the acceptance checks; the tutorial skeletons in help, in the pattern of ten; the ReadMe, guide and history, each with its HTML pair; and the policy files that say which files travel to the repository.

### Step 3

The template program is the fruit basket's shape with the new name: a dialog with a field and a list, a report, F1 help on the fields, a session log. It runs before you have written a line, so every change is made against a working program.

### Step 4: build

Change into the folder and build.

Screen reader:

- Kit, C colon backslash HomerDev version 1.52.8
- Version, 1.0.0
- Built Recipes dot exe version 1.0.0

### Step 5: Recipes

Run it.

Screen reader:

- Recipes, the list is empty
- Name, edit

### Step 6: pancakes

Type a name and press Enter.

Screen reader:

- pancakes added, 1 item in the list

### Step 7: Alt+F4

Alt plus F4, and run it again: kept.

Screen reader:

- Recipes, 1 item in the list

### Step 8

Now the first real change. Open Recipes dot cs in EdSharp; the Camel Type conventions the kit's skill teaches are already followed in it: a prefix on every name says its type, functions in lower camel case, constants with c underscore. An AI assistant that has read the kit's skills writes the same way, so what it adds reads like what was there.

### Step 9

Where the Homer classes come in. Lbc builds every dialog; Say speaks; Log writes the session log; Inix reads settings; Web fetches; Util has the pluralizer that said one item and not one items. None of them is in your folder; they compile from the kit, so a kit update improves every app on the next build.

### Step 10

The Python template, newHomerApp with dash py, makes the same program in Python, built with the kit's Python modules; buildFruitBasketPy showed the shape in walk two: a build environment made, what the build needs installed, and an executable at the end.

Screen reader:

- Creating the build environment
- Installing what the build needs
- Built FruitBasketPy dot exe version 1.0.0

### Step 11

A planned misstep. Name the app with a space, and newHomerApp refuses in one line, because the name becomes a folder, a file, a class and a shortcut key.

Screen reader:

- A Homer app's name is one word in upper camel case, like FruitBasket.

### Step 12

From here the work is yours: fields in the dialog, commands on the menus with their keys named for their words, a template database or two. Walk four is what happens each time you type build.

### Step 13

The tutorial skeletons in help, one for each walk in the pattern of ten, are part of what newHomerApp made. Each is a walk in the pattern with placeholder steps, so the day a feature is finished its walk is a file to fill in, not to invent; walk six is about filling them.

### Step 14

accept dot inix is the app's own acceptance list: a name and a command each -- the program was produced, the installer was produced, no kit class was copied into the folder. check runs them, and the release refuses on any that fails. Add one for each promise the app makes.

### Step 15

The policy files. RepoFiles dot txt names what the repository carries; LocalFiles dot txt names what stays on your machine; a file in neither is one tidy asks about. Together they are why a stray file is noticed and a private one is never pushed.

### Step 16

What this walk taught. I say the idea or the key; the reader says the command or the name.

### Step 17

Make a new app from the template.

Screen reader:

- newHomerApp

### Step 18

Every stage, from encoding to installer.

Screen reader:

- build

**Something to try:** Make an app of your own with newHomerApp, build it, run it, and add one field to its dialog.

## 4 - Build, Check and Release

One want: a change made this morning, published by lunch, with nothing shipped that does not work. What build does, stage by stage; what check refuses, with the misstep everybody meets; what release publishes and what it leaves behind. This walk assumes walk four.

**Before you start:** An app built on the kit is open in a command prompt, with a change made and GitHub signed in.

### Step 1: build

The want: a change made this morning, published by lunch, with nothing shipped that does not work. Three commands do it, and each refuses when it should. First, build, in the app's folder.

Screen reader:

- Kit, C colon backslash HomerDev version 1.52.8
- Version, 1.0.228 (bumped)

### Step 2

The stages, in order, each logged. The kit's version is checked against what the app needs. Old file names are retired. The encoding of every file is put right: UTF-8 with a byte order mark, CRLF line endings. The hotkey list is generated from the program itself. Any tutorial whose audio is missing or older than its script is spoken. The program compiles. The installer is built.

### Step 3

Each stage says one line and writes the rest to the log. Here is the line that matters most.

Screen reader:

- Built DbDo underscore setup dot exe version 1.0.228

### Step 4: scripts\check

Second, check. It is also the first thing release runs, so you may skip it; but it is a few seconds, and it says exactly what release would refuse.

Screen reader:

- 13 checks passed, 0 checks failed, 2 checks not checked.

### Step 5

What the checks are. Every file in the Homer encoding. Every access letter unique within its dialog or menu. No key on a reader's key. The app's files under the Local tree, never Roaming. The hotkey list current. The tutorials clean. Each acceptance check in accept dot inix passing. And an evidence report written in Markdown, for anyone who asks what was checked.

### Step 6

A planned misstep, the one everybody meets. Change a dialog and reuse a letter, and check names the dialog and the two captions.

Screen reader:

- 12 checks passed, 1 check failed. failed: access letters -- Filter Records: F is used by Find and Filter

### Step 7: scripts\release

Third, release. It reads the version from the installer, refuses if the last build did not succeed, runs check, commits and pushes, tags the version, and publishes the installer on GitHub.

Screen reader:

- GitHub has no published release tagged v1.0.228.
- DbDo 1.0.228 published.

### Step 8

Release refuses for honest reasons and says which. A build still running: the last build did not succeed, build again, then release. A check failing: nothing was published, its report names it. And it never publishes an installer older than the source beside it.

### Step 9

What the release left behind. A tag, a release page with the installer, and in the logs folder a release log and an evidence report; the ReadMe's download link now points at the new installer. F11 in any installed copy finds it within the hour.

### Step 10

The logs. Every stage wrote its own: build, encoding, hotkeys, tutorials, check, push, release. The console said one line each; the logs say every command and its exit code. When something is wrong, the log is the thing to send -- never a description of the console.

### Step 11

A second planned misstep. Run release before the build has finished speaking its tutorials, and it refuses -- the build has not succeeded yet -- which is right, if blunt; wait for the Built line, then release.

### Step 12

What this walk taught. I say the idea or the key; the reader says the command or the name.

### Step 13

Every stage, encoding to installer.

Screen reader:

- build

### Step 14

What release would refuse, in seconds.

Screen reader:

- check

### Step 15

Tag, publish, and leave a log.

Screen reader:

- release

**Something to try:** Make a small change in an app of your own, then build, check and release it.

## 5 - The Installer and Its Finish Page

One want: a program that installs itself and its helpers in one run and says what it did. The shared installer parts heard in DbDo's installer: boxes that say their state in one word, the results box, the summary, and the ten lines an app writes to get all of it. This walk assumes walk five.

**Before you start:** A Homer program's installer is downloaded, and your reader is running.

### Step 1

The want: a program that installs itself and its helpers in one run, and tells you what it did. The kit's HomerComponents dot iss is the shared part of every Homer installer: the finish page, its boxes, their states, and the results. Here is DbDo's.

### Step 2: Alt+R

The installer is downloaded; Enter opens it, and Windows asks because it came from the internet. Alt plus R, Run; then Alt plus Y, Yes, for administrator rights, because a Homer program installs for everyone.

Screen reader:

- User Account Control dialog

### Step 3: Enter

The pages are a wizard: the folder, then Install. Enter presses the default button on each. The page that asks a decision is the last.

Screen reader:

- Setup, Finish page

### Step 4: DownArrow

The finish page lists the optional pieces as boxes. Arrow through them; each says its name, its state, and its size.

Screen reader:

- Update screen reader scripts checked, 1 of 6

### Step 5

The three words, from the kit. Install when the piece is not there. Update when it is there and a newer version is available -- the installer asked winget. Reinstall when it is there and current, unticked unless you want it. You never have to know what is on your machine; the box says.

### Step 6: DownArrow

Down Arrow to the player.

Screen reader:

- Install mpv checked, 2 of 6

### Step 7: Space

Ollama runs AI on your own computer. Its models are large, so it is unticked unless you tick it; Spacebar changes a box, and the answer is one word.

Screen reader:

- checked

### Step 8: Enter

Launch is ticked already. Enter presses Finish, and whatever was ticked installs now; a results box then says what was done, one line per piece.

Screen reader:

- DbDo Setup, screen reader scripts: updated. mpv: installed. Ollama: installed.

### Step 9

The same summary is saved in the logs folder under your local application data, and summarizeSetup, in the program folder, shows it again on any later day.

### Step 10

What the app's installer script writes, and what the kit writes. The app names its pieces in a table -- a name, a winget id, an executable to look for, what it is used for -- and the kit does the rest: the probing, the three states, the labels, the ordering, the results. Ten lines of the app's, for a page that behaves the same in every Homer program.

### Step 11

Screen reader scripts are a piece of their own: the kit knows where each reader keeps its settings or its add-ons, and the box reads Install, Update or Reinstall for them as for the rest.

### Step 12

A planned misstep. Run the installer a second time: every piece already present says so, and Install becomes Reinstall, unticked. Nothing is installed twice.

### Step 13

Removing a Homer program is Windows Settings, Apps; the pieces it installed are programs in their own right and stay for the other Homer programs, and your data folder stays unless you delete it.

### Step 14

What the table in the app's script looks like, in words: one line per piece -- the name the box shows, the winget id that installs it, the executable whose presence means it is there, and what it is for, which becomes the box's description. The kit reads the table and does everything else.

### Step 15

Why winget. It knows what is installed and what the newest version is, so the three states are read rather than guessed; it fetches from the maker's own feed; and it is on every Windows 10 and 11 machine. The kit asks it once per piece as the finish page is built, so the boxes are right before you reach them.

### Step 16

The installer's own log is written beside the results -- every piece, every command, every exit code -- so a piece that failed to install names why, and the summary points at the log.

### Step 17

What this walk taught. I say the idea or the key; the reader says the command or the name.

### Step 18

The one word that is the box's state.

Screen reader:

- Install, Update, or Reinstall

### Step 19

The shared installer parts.

Screen reader:

- HomerComponents dot iss

**Something to try:** Run a Homer installer, arrow its finish page, and read the results box.

## 6 - Spoken Tutorials

One want: a spoken tutorial for your app, in two voices, without a microphone. The walk file and its four beats, the two voices and what they never do, the pattern of ten, three to five minutes, the checker and its misstep, the tool that speaks and measures, and where the rules came from. This walk assumes walk five.

**Before you start:** An app built on the kit, with its help folder open.

### Step 1

The want: a spoken tutorial for your app, in the two voices, without a microphone. A walk is a text file in help, Tutorial underscore, a number, a title with underscores, dot inix. The build speaks it.

### Step 2

The format has four beats per key. Say: the host says the key with the word it comes from. Key: the key pressed. Hear: what the reader says, word for word, as it would be spoken -- a file name as said, not as written. Say again: what that meant. Name silence when a key says nothing. Name no screen reader.

### Step 3

Two voices, because a program has two: the person, and the reader answering. The exchange is the teaching device, and it is used for more than keystrokes: a glossary is the host saying the term and the reader saying the meaning; a recap is the host saying the key and the reader saying the command. What the voices never do is chat.

### Step 4

The pattern of ten, the same for every app, numbered with one digit so a folder sorts it. Zero, the overview and contents. One, the user interface and the key rules together. Two to eight, seven tasks, each built around a plain want -- usually install and launch first. Nine, the conclusion: the summary, the glossary, and more information, the help built in among it.

### Step 5

Three to five minutes for parts one to ten: under three is too thin to repay the listener's start; over five loses them. A thin walk gets substance -- the adjacent thing the want needs, a planned misstep and its recovery -- never padding. The tool measures the audio and says what runs under or over.

### Step 6: scripts\checkTutorial

checkTutorial reads every walk before anything is spoken. It wants Intro and Setup, a Say in every step, Hear lines in words, no reader named, the first walk teaching the two reader keys, and the pattern's names and numbers; a set not yet the pattern is a notice, not a silence.

Screen reader:

- 12 scripts checked, 0 problems.

### Step 7

A planned misstep. Write a Hear line with a plus sign in it, or a file name as written, and the checker names the step.

Screen reader:

- Tutorial underscore 17, step 6: Hear writes an access key with a plus sign; the reader says the words

### Step 8: scripts\buildTutorials -build

buildTutorials speaks them. Two voices: Kokoro, with a narrator and a reader, both licensed to redistribute; Piper when Kokoro is not there. The reader's voice shifts by context -- a cursor line, a message, a menu -- so a message is heard as a message.

Screen reader:

- Creating 4 underscore Open underscore and underscore Move dot mp3, 23 steps. A few minutes.

### Step 9

The audio is named like a chapter -- 4 underscore Open underscore and underscore Move dot mp3 -- so a folder or a player shows the number and the title. A walk is spoken again only when its text has changed since it was last spoken; the rest are kept.

### Step 10

At the end, the lengths, and the two lines that matter.

Screen reader:

- 4 underscore Open underscore and underscore Move dot mp3 runs 2 33
- Wrote Tutorials dot m3u naming 12 tutorials, 27 minutes in all.

### Step 11

Under three minutes or over five, the tool says so by name, with the guideline in one line. Tutorials dot m3u is the playlist Play Tutorials uses; Tutorials dot md is the transcript, made from the same scripts; TutorialFeed dot xml is a podcast feed of the same audio.

### Step 12

Two kinds of listener. A walk is written for the person who will press the keys tomorrow; it is also what an AI assistant reads to learn the program, which is why the skills folder points at it.

### Step 13

The learning behind the rules came from ninety-eight recorded screen reader training sessions and from Quill Radio's tutorials: spell a lone letter with its alphabet word; one planned misstep per walk; close by naming the two or three keys taught; a concrete want before a feature. TutorialLearnings dot md in the kit's help has the rest.

### Step 14

What this walk taught. I say the idea or the key; the reader says the command or the name.

### Step 15

Reads every walk before anything is spoken.

Screen reader:

- checkTutorial

### Step 16

Speaks what is missing or stale and measures it.

Screen reader:

- buildTutorials

### Step 17

The playlist Play Tutorials uses.

Screen reader:

- Tutorials dot m3u

**Something to try:** Write one task walk for your app, run checkTutorial, and let the build speak it.

## 7 - Shared Code and the Homer Player

One want: a feature written once and heard in every program. The Homer Player heard in FileDir and then in DbDo, the same window from the same class; the other shared classes and what each does for the listener; what sharing buys and the one rule it costs; a misstep from this week. This walk assumes walks two and four.

**Before you start:** FileDir and DbDo are installed, with mpv.

### Step 1: Control+Shift+L

The want: a feature written once and heard in every program. The kit's shared code is where that happens, and the Homer Player is the plainest case. Here it is in FileDir, on a saved podcast page.

Screen reader:

- 4 tracks from Access On

### Step 2

The player opens on its track list, and the first track plays.

Screen reader:

- Access On, Track list: list box, Episode 212, 1 of 4

### Step 3: Alt+Shift+P

Now the same player in DbDo, on a radio station.

Screen reader:

- 1 track from stations
- RadioTrail, Track list: list box, KIRO 710 ESPN Seattle, 1 of 1

### Step 4

Scroll Lock pauses and resumes; the Volume and Rate sliders are ordinary sliders; Alt plus Shift plus R records a copy of the stream; Escape closes it. Learned once in FileDir, known in DbDo, because MediaPlayer dot cs lives in the kit and both programs compile it from there.

### Step 5

The other classes work the same way, less visibly. Lbc builds every dialog you heard in walk one. Say speaks every message, choosing the channel of whichever screen reader is running, or the Windows voice when none is, and never speaking over a keystroke. Log writes the session log in one format for every program.

### Step 6

Inix reads the settings files -- the dot inix format, sections and lines, with the comments the kit's rules ask for, so a settings file is documentation too. Web fetches with the same user agent and the same patience. Util holds the small things: the pluralizer, the short path, the version string.

### Step 7

Mpv dot cs finds the player engine, machine-wide, and drives it: play, pause, record, the sliders. Media dot cs knows what a track is -- a file, a stream, an episode -- and what to say about one.

### Step 8

What sharing buys. A fix to the player on Monday is in every program's next build; a new Say channel for a new reader reaches all of them; and a person who learned the dialog in one program has learned it in the next.

### Step 9

The cost is one rule: an app never copies a kit class into its own folder; it compiles against the kit.

### Step 10

A planned misstep, from this very week. A kit class had a line that depended on one app, and compiled in that app alone; the kit's check now compiles every shared class on its own, so the mistake is caught in the kit and not in the fifth app to try it.

### Step 11

The Python side has the same shape: a Say, a Log, an Inix, a dialog builder, so a Python app -- HomerScribe is one -- speaks and logs and asks exactly as the C sharp ones do. Walk one's two fruit baskets were the proof.

### Step 12

Updating the kit is unarchiving HomerDev dot zip over the folder and building; every app's build checks the kit's version against the one it needs, and says so in one line when the kit is too old.

Screen reader:

- ERROR: FileDir needs HomerDev 1.52.8 or later, and C colon backslash HomerDev is 1.52.6.

### Step 13

How an app reaches the kit. Its build passes the kit's CSharp folder to the compiler, so Lbc dot cs, Say dot cs and the rest are compiled into the app from where they live; nothing is copied. The acceptance check named missing Lbc dot cs is the proof that nothing was.

### Step 14

A worked case of the gain. The Homer Player's recording -- Alt plus Shift plus R, a Record button and a Stop recording button -- was written once, in the kit, on 5 October. FileDir had it on its next build, and DbDo on its next, with no change to either program.

### Step 15

What belongs in the kit and what does not. A behaviour every app wants -- a dialog, speech, a log, a player -- belongs in the kit. A behaviour one app wants -- DbDo's grid, EdSharp's compiler table, FileDir's tags -- belongs in that app. The test: would a second app want it exactly as it is?

### Step 16

What this walk taught. I say the idea or the key; the reader says the command or the name.

### Step 17

The player every Homer program shares.

Screen reader:

- MediaPlayer dot cs

### Step 18

The dialog class.

Screen reader:

- Lbc

### Step 19

The speech class.

Screen reader:

- Say

**Something to try:** Play something in FileDir and in DbDo, and notice the keys that are the same.

## 8 - Build with an AI Assistant

One want: a new feature written with an AI assistant, in the kit's house style, and proved before anyone hears it. The skills that teach an assistant the rules, the three sentences that carry the kit into a chat, the method -- specify, build small, verify without sight -- and a planned misstep the check catches.

**Before you start:** An app made with newHomerApp, as in walk three, and a command prompt in its folder.

### Step 1

One want: a feature written with an AI assistant that follows the house rules, and proved before anyone hears it. This walk leans on walks three and four: an app from newHomerApp, and build, check and release.

### Step 2: scripts\checkSkills

The kit teaches an assistant through its skills: folders of instructions, one for each part of the work -- code, dialogs, installers, tutorials. Before trusting them, the kit checks them as it checks code. I type the command.

Screen reader:

- scripts\checkSkills

### Step 3: Enter

Enter runs it.

Screen reader:

- 16 skills checked, 0 problems.

### Step 4

Sixteen skills, none broken. A skill whose description held an angle bracket would be refused when uploaded, and this check names it first.

### Step 5

Three sentences carry the kit into a chat: what the program is; which classes to use -- Lbc for every dialog, Inix for settings, Log for the session log, Say only for what the reader cannot know; and the sample to follow, FruitBasketCs.

### Step 6: Control+O

Then the method the kit is shaped around. Specify before you generate: write accept dot inix first, a few named checks of what done means, so the assistant works to your idea of done, not its own. I open it in EdSharp.

Screen reader:

- Open dialog
- File name: edit

Confirm the wording with a live run: buildTutorials -live.

### Step 7: build

Each check is a name and a command, and check runs them all. Now one change, then one build: I ask for a Prefix box in the dialog, put the assistant's file in place, and type build.

Screen reader:

- build

### Step 8: Enter

Enter.

Screen reader:

- Built PatternRename underscore setup dot e x e, version 1.0.1

Confirm the wording with a live run: buildTutorials -live.

### Step 9: check

The installer is built. Then check, which refuses what release would refuse, and writes the evidence.

Screen reader:

- check

### Step 10: Enter

Enter.

Screen reader:

- 13 checks passed, 0 checks failed, 2 checks not checked.

### Step 11: Enter

The two not checked are the build and the smoke run, which come with dash dash build. A planned misstep: the assistant gave two controls captions that start with the same letter. I run check again.

Screen reader:

- access letters -- Prefix: P is used by Pattern and Prefix

Confirm the wording with a live run: buildTutorials -live.

### Step 12: Enter

The check names the caption and the clash; the fix is a caption, not a key table. The assistant renames the box Text Before Each Name, so it takes T from the first letter of a word; I rebuild, and check passes again.

Screen reader:

- 13 checks passed, 0 checks failed, 2 checks not checked.

### Step 13: Control+F1

Last, verify without sight: the log says what happened, and your ears do the rest. In the running program, Control plus F1 turns on the Key Describer, so the new box's key says what it does.

Screen reader:

- Key Describer On

### Step 14: Alt+T

Alt plus T, T for Text, the first letter of the new caption.

Screen reader:

- Alt plus T, Text Before Each Name

Confirm the wording with a live run: buildTutorials -live.

### Step 15: Control+F1

Control plus F1 again, and the keys act once more.

Screen reader:

- No Key Describer

### Step 16

What this walk taught. I name the step; the reader gives the command.

### Step 17

Say what done means, first.

Screen reader:

- accept dot inix

### Step 18

Prove it before release.

Screen reader:

- check

### Step 19

Make sure the instructions an assistant reads are sound.

Screen reader:

- checkSkills

**Something to try:** Write accept dot inix for one feature you want, then ask an assistant for it and run check.

## 9 - Conclusion

The conclusion and summary of the walks; the words the kit uses, in two voices; then more information: the help built into every Homer program and where to learn more.

**Before you start:** Nothing is needed; this walk is listened to.

### Step 1

To finish: what to carry away, the words the kit uses, and where to get help and learn more. First, the summary. Every decision that makes a program pleasant to use without sight was made once and put in a shared class; an app inherits it.

Screen reader:

- Lbc, Say, Log, Inix, Web, Util

### Step 2

The keys follow rules, so a key in a program you have never opened can be guessed; the word gives the letter.

Screen reader:

- Control plus K, Keywords, in every program that searches

### Step 3

Three commands take a change from the morning to a published installer by lunch, and each refuses when it should.

Screen reader:

- build, check, release

### Step 4

And a program teaches itself, in ten walks spoken by its build.

Screen reader:

- Play Tutorials, in the Help menu

### Step 5

From the seven task walks: newHomerApp gives a running program before you write a line; when something is wrong, send the log; an app never copies a kit class, so a fix reaches every program on its next build; and an assistant works to your idea of done when accept dot inix says it first.

### Step 6

Now the words, in alphabetical order. I say the term; the reader says what it means.

### Step 7

access letter.

Screen reader:

- The underlined letter in a caption, from the first letter of a word, one per dialog or menu; the check counts them.

### Step 8

build.

Screen reader:

- The command that puts an app's files in order, speaks its tutorials, compiles it and makes its installer, logging every stage.

### Step 9

check.

Screen reader:

- The command that refuses what release would refuse: encoding, access letters, keys, hotkeys, tutorials, acceptance.

### Step 10

finish page.

Screen reader:

- The installer's last page: optional pieces as boxes, each saying Install, Update or Reinstall, with a results box after.

### Step 11

Homer encoding.

Screen reader:

- UTF-8 with a byte order mark and CRLF line endings, for every text file the kit or an app ships.

### Step 12

Homer Player.

Screen reader:

- The player shared by every Homer program: a track list, Scroll Lock to pause, sliders, Alt plus Shift plus R to record.

### Step 13

inix.

Screen reader:

- The settings file format: sections and lines, with comments that make the file its own documentation.

### Step 14

Lbc.

Screen reader:

- Label before control: the class that builds every Homer dialog, with Tab, Alt letters, Control plus Enter and Escape.

### Step 15

newHomerApp.

Screen reader:

- The command that makes a new app from the template: its folder, its files, its tutorial skeletons.

### Step 16

pattern of ten.

Screen reader:

- The walks every program has: zero, the overview; one, the user interface; two to eight, seven tasks; nine, the conclusion.

### Step 17

release.

Screen reader:

- The command that checks, commits, pushes, tags and publishes the installer on GitHub, refusing when it should.

### Step 18

Say layer.

Screen reader:

- The question keys: Shift or Alt with a letter, speaking a fact and changing nothing; twice, the words in a window.

### Step 19

skill.

Screen reader:

- A folder of instructions an AI assistant reads to learn the kit's rules: coding, tutorials, installers, documents.

### Step 20

walk.

Screen reader:

- One spoken tutorial: a text file of steps, spoken by the build in two voices.

### Step 21

Last, more information. Help is built into every Homer program, the same in each. The guide, and what changed.

Screen reader:

- F1, the guide
- Shift plus F1, History

### Step 22

The version, and what any key does without doing it.

Screen reader:

- Alt plus F1, About
- Control plus F1, Key Describer

### Step 23

HomerDev dot md, in the kit's help folder, is the whole kit in one document; History dot md says what changed in every version and why, and is the first thing to read when a new kit arrives.

### Step 24

Tutorials dot md is the guideline for walks; the skills folder teaches an AI assistant the kit's rules; and the kit, with DbDo, EdSharp, FileDir and HomerScribe beside it, is on GitHub, at github dot com slash JamalMazrui. Where to begin: make an app with newHomerApp and build it; the running program will suggest what it should become.

**Something to try:** Make an app with newHomerApp, build it, and press F1 in it to read its guide.

<!-- walkthrough ends -->

## The twelve walks every Homer program has

The recipe for applying the pattern to a new app, step by step, is in the
homer-tutorial skill -- `.claude\skills\homer-tutorial\SKILL.md` -- which an
AI assistant reads before writing walks; the homer-tutorial skill carries the whole recipe, and this document the rules behind it.


A program's walks follow one pattern, so a listener who has heard one
program's knows where to find a thing in another's. The scripts are
`help\Tutorial_NN_Title_With_Underscores.inix`; the audio is
`help\tutorials\NN_Title_With_Underscores.mp3`, the same name without the
word Tutorial, so a folder or a player shows the number and the title.
Concepts come before the tasks; summaries come after them; More Information
is always last.

- **00_Overview_and_Table_of_Contents** -- what the program is, what each
  walk covers, and the two reader keys: Insert plus Up Arrow repeats a line,
  Insert plus Tab says where you are.
- **01_Install_and_Launch** -- the download, the installer's pages, the
  finish page, and the program opening by itself.
- **02_User_Interface_Concepts** -- what the program is made of: its windows,
  its main view, its dialogs, its status bar. Listened to more than pressed.
- **03_Key_Patterns** -- the rules every key follows, so a key can be
  guessed before it is learned.
- **04 to 08, the tasks** -- each a whole piece of work from start to end, in
  the order a new person meets them. At least one, at most five, numbered from
  04 with no gap. A program with more to teach merges tasks; a program with
  less stops early, and 09 to 11 keep their numbers.
- **09_Glossary** -- the program's words in alphabetical order, one step per
  term: the host says the term, the reader says what it means.
- **10_Conclusion** -- four sentences to carry away, and where to begin.
- **11_More_Information** -- the guide and history from inside the program,
  the documents, the project page, updates, and the other Homer Tools.

**Three to five minutes for parts 01 to 10.** Under three minutes is
usually too thin to repay a listener's start; over five loses them. A walk
that would run longer is cut -- a thing taught in an earlier walk is named
rather than shown again -- or split into two tasks while the slots last; it
is never hurried. A walk that runs short is given more substance -- the
adjacent thing the want needs, one planned misstep and its recovery, a
two-voice exchange -- never padding. The overview, 00, and More Information,
11, may be shorter. At the voices' pace, three minutes is about twenty steps
of ordinary length and five about thirty; the tool measures the audio and
says what runs under or over.

**Walk 00 has a shape.** Prose first: a paragraph on what the program is.
Then the two reader keys. Then the table of contents as its own clean list,
one step per walk, the host saying the number and the title and the reader
saying what the walk covers. The two never mix: a contents list that wanders
into explanation has lost its listener.

**Help is taught twice.** Walk 02 says where help is -- F1 the guide, Shift
plus F1 the history, Alt plus F1 the version, the Help menu with Play
Tutorials, and the menus themselves, which say every key. Walk 03 names the
keys that explain the keys: Control plus F1, the Key Describer; Hotkeys in
the Help menu; and the reader's own Insert plus Tab.

`checkTutorial` requires the seven fixed names, the task numbering, and the
step ceiling.

## Tasks are wants, and later walks lean on earlier ones

A task walk is built around a thing a person would actually want, stated
first and in plain words -- the station carrying the home team, jazz from
anywhere, jazz near home, a job to record, a book to find again -- and the
program's features are shown as the way to get it. Not "the Filter Records
dialog", but "jazz, from anywhere", and the filter appears because the want
needs it. A listener remembers the want and finds the feature attached to it.

The walks are a course, not a reference. Each assumes the ones before it and
says so in its Intro -- "this walk assumes walks four to six" -- and a thing
taught earlier is named, not retaught: "Control plus F, which you know from
walk six", "the same way as in walk four". A first walk explains a key; a
later walk says it and moves on. Anyone who needs the explanation has the
earlier walk, and the guide.

## Two voices, and what they are for

A walk has two voices because a program has two: the person, and the reader
answering. That exchange is what makes a walk memorable, and it is used for
more than keystrokes. A glossary is the host saying the term and the reader
saying the meaning. A recap is the host saying the key and the reader saying
the command. A key pattern is the host stating the rule and the reader giving
the instance. Each is two short lines, and each lands better than one voice
reading a list.

What the voices never do is chat. No greeting, no banter, no "great question",
no comment from one voice on the other. A turn of phrase or a change of tone
is allowed where it helps a line stick; nothing is allowed that costs the
listener a second and teaches nothing. The measure is useful information in
the least time, by the channel that makes it stay.

