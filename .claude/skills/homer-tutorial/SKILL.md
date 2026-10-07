---
name: homer-tutorial
description: Writes, checks and builds the spoken walkthroughs of a Homer Tools app -- Tutorial_NN_*.inix scripts where a narrator works and a screen reader answers. Use when asked to write a tutorial, walk, or walkthrough for a Homer app, to simulate what a screen reader says, to add a Hear line, or to check tutorial scripts before building their audio. Names no screen reader in the scripts.
---

# Homer tutorial skill

A Homer tutorial is a dialogue: a person doing a real job in the app, and a
screen reader answering exactly as a reader does. Each script is a
`help\Tutorial_NN_Name.inix` file; `scripts\buildTutorials` speaks it into
`help\tutorials\NN_Name.mp3` -- the number and the title, without the word Tutorial -- with two voices and writes the text into
`help\Tutorials.md`. The reader's lines are the whole value: they must be
what the listener will hear on their own machine.

## The set: twelve walks, under an hour and a quarter

Every app's walks follow one pattern, so a listener who knows one app's knows
where to look in another's:

- **00_Overview_and_Table_of_Contents** -- a paragraph of prose on what the
  app is; the two reader keys, Insert plus Up Arrow to repeat a line and
  Insert plus Tab to say where you are; then the table of contents as its
  own clean list, one step per walk, the host saying the number and title
  and the reader saying what it covers. Prose first, then the list; never
  the two mixed.
- **01_Install_and_Launch**
- **02_User_Interface_Concepts** -- what the app is made of, and where help
  is: F1 the guide, Shift plus F1 the history, Alt plus F1 the version, the
  Help menu with Play Tutorials, and the menus themselves, which say every
  key.
- **03_Key_Patterns** -- the rules every key follows, and the keys that
  explain the keys: Control plus F1 the Key Describer, Hotkeys in the Help
  menu, F1, and the reader's Insert plus Tab.
- **04 to 08, the tasks** -- at least one, at most five, numbered from 04
  with no gap. Each is built around a plain want, said first -- the station
  carrying the home team; jazz from anywhere; jazz near home -- and the
  features appear as the way to it.
- **09_Glossary** -- the app's words, alphabetical, one step per term: the
  host says the term, the reader says the meaning.
- **10_Conclusion** -- four sentences to carry away, and where to begin.
- **11_More_Information** -- always last.

**Three to five minutes for parts 01 to 10; 00 and 11 may be shorter.**
Under three is too thin to repay the listener's start; over five loses them.
At the voices' pace, three minutes is about twenty steps and five about
thirty. A short walk gets more substance -- the adjacent thing the want
needs, a planned misstep and its recovery, a two-voice exchange -- never
padding; a long one is cut or split, never hurried. The tool measures the
audio and names what runs under or over. Twelve walks at three to five
minutes is "about an hour", which the ReadMe can promise.

**Later walks lean on earlier ones.** The set is a course, not a reference:
each walk says in its Intro which walks it assumes, and a thing taught
earlier is named, not retaught -- "Control plus F, which you know from walk
six".

**Two voices, never a chat.** The exchange is the teaching device: a recap
is the host saying the key and the reader saying the command; a glossary
entry is the term and its meaning; a key rule is the rule and an instance.
No greeting, no banter, no comment by one voice on the other; a turn of
phrase only where it helps a line stick.

`checkTutorial` enforces the seven fixed names, the task numbering, the
step ceiling, and the first walk's two reader keys.


## The recipe: applying the pattern to any Homer app

This is the whole method, as it was worked out on DbDo, EdSharp, FileDir and
the kit itself in October 2026. Follow it in order for HomerScribe, HomerView
or any app; nothing here needs the author of the pattern in the room.

### 1. Gather the truth before writing a line

- The app's `help\Hotkeys.md` (or hotkey summary): every command with its
  key and description. Keys and command names in the walks come from here,
  never from memory.
- Any real speech: a JAWS or NVDA speech-history capture, an earlier walk's
  Hear lines, the program's own `AddMessage` or `Say` strings in its source.
  A Hear line that was recorded is worth ten that were guessed.
- The guide and ReadMe, for what the installer's boxes are, where data lives,
  what the program is for.
- The app's `accept.inix`, build log and session log, for console lines that
  can serve as Hear lines in a build-or-script walk.

### 2. Choose the tasks as wants, not features

List what a person comes to the app wanting -- the station carrying the home
team, a letter to finish, a Downloads folder cleaned, a video described --
and pick up to five, in the order a new person meets them. Each task walk is
one want from start to end; the features appear as the way to it. Write the
Intro as the want in plain words, and say which earlier walks it assumes.

### 3. Write the twelve, each to its shape

- **00**: one paragraph of prose on what the app is; the two reader keys
  (Insert plus Up Arrow, Insert plus Tab) as steps; then the table of
  contents as a clean two-voice list, one step per walk, host saying the
  number and title, reader saying what it covers; a closing line with the
  count and "about an hour". Prose and list never mix.
- **01**: download, the installer's pages, the finish page with each box's
  purpose and the three words Install, Update, Reinstall, the results box,
  where things went, the desktop key, F11 for later, one misstep (run while
  open; a mistaken tick).
- **02**: the parts of the program as heard -- window, main view, dialogs
  that work one way, Say keys, messages, settings -- and where help is: F1,
  Shift plus F1, Alt plus F1, the Help menu with Play Tutorials, the menus
  that say their keys. Every part is named in a sentence or two and then
  shown: the host presses the key, and the reader speaks the window that
  comes forward or the control that takes focus (see Show, then tell).
- **03**: the rules, each shown with a key and the reader's answer, then a guessing exchange both ways (host names a
  command, reader gives the key; host says a key, reader names the command),
  the keys that explain the keys (Control plus F1, Hotkeys, Insert plus Tab),
  one worked case of how a key was chosen, one misstep.
- **04 to 08**: the wants. Each: the want stated, the keys taught in four
  beats, one planned misstep with its recovery, things taught earlier named
  rather than retaught, the recap in two voices.
- **09**: the app's words, alphabetical, one step each: host says the term,
  reader says the meaning with its key; twenty to thirty-five terms; a last
  step with the count and "the guide has each in context".
- **10**: four principles with their keys in two voices; one thing kept from
  each task walk; three habits; three everyday tasks each in one breath;
  what the app is for and is not; where to begin; where to send a problem.
- **11**: the guide, history and version from inside the program; the
  documents and their web pages; F11; the GitHub page; the other Homer
  Tools. Short is fine here.

### 4. Write every line for the ear

- `Say=` lines are the host's, in the first person present ("I press"). A
  lone letter is spelled with its alphabet word: "T, Tango".
- `Key=` is one key or one typed string per step; typed text is a string,
  not a key, and the checker knows the difference.
- `Hear=` is what the reader says, word for word as spoken: "letter dot t x
  t", never "letter.txt"; "Control plus K", never "Control+K"; a count in the
  reader's own form ("1 of 60313"). Name no screen reader. Several Hear lines
  in one step are several utterances.
- A second `Say=` after Hear says what that meant, in one sentence.
- Recaps: "What this walk taught. I say the key; the reader says what it
  does." then one step per key, host says the key, reader says the command
  from Hotkeys.
- Numbers that the data will change -- a filter's count, a station's row --
  are plausible, round, and said as such in the Say line.

### 5. Measure, then adjust

Run `checkTutorial`; fix problems; read notices. Build, and read the
tool's lengths: parts 01 to 10 between 3:00 and 5:00; 00 and 11 may be short.
The pace is about ten seconds a step of ordinary length and three seconds a
two-voice exchange, so three minutes is about twenty ordinary steps or thirty
exchanges; a Key Patterns or Conclusion walk built of exchanges runs short
unless it also carries worked cases. A short walk gets the adjacent thing its
want needs, a misstep, or a worked case -- never padding. Build again; the
tool re-speaks only what changed.

### 6. What this week's mistakes teach

- A set that is not yet the pattern is a notice, not a silence: never leave
  a program with no audio for a guideline's sake.
- A Hear line with a plus sign, a file name as written, or a reader's name
  is a checker problem; fix the line, not the checker.
- A walk's steps are counted by the checker and timed by the tool; trust the
  tool.
- Never ship a project tree from an old checkout; deliver the walk files and
  the build changes, nothing the repository already holds.
- One build speaks at a time; the tool serializes them and says when it
  waits. Run builds in series anyway.
- An acceptance build speaks nothing; the ordinary build's audio ships.

## The format

```
[about]
Title=01 - Transcribe a Recording
Intro=One sentence: what this walk does.
Setup=The starting state: what is installed, what file exists, where focus is.
Homework=Something to try afterwards, one sentence.

[step]
Say=What the narrator says. One idea.
Key=Alt+T
Hear=Transcribe audio check box, checked, Alt plus T
Note=Written only, never spoken.
Pause=1
```

`Say` is the narrator; `Key` is the key pressed, in Homer key-name form
(modifiers alphabetical, "Control" spelled out); `Hear` is what the reader
answers, one line per utterance, repeat the key for several; `Note` is for
the written version only; `Pause` is seconds of silence before the step.
The first script only carries `[feed]` (title, description, author) and
`[global]` (NarratorScale, ReaderScale, LeadIn).

## Four beats per key

Every keystroke is narrated the way a screen reader trainer does it:

1. **Say the key**, with the word it comes from and, for a letter, its
   phonetic word: "Alt plus T is Transcribe audio, T for Transcribe."
2. **Press it** (`Key=`).
3. **Hear the reader, word for word** (`Hear=`), untidied.
4. **Say what that meant** in the next step's `Say`: "The reader said
   checked. That is the whole request."

Also:

- **Name silence.** When the reader says nothing after a key, say so:
  "The reader did not say anything, and that is right." `Hear=` stays
  empty; the following `Say` or the `Note` says why.
- **Verify after every change of focus** with Insert plus T, and say the
  word "verify".
- **Teach the repeat key early**: the reader's say-line key (Insert plus Up
  Arrow) in the first walk, before the first thing worth missing.
- **Counts are orientation**: when the reader says "1 of 14", the narrator
  uses it.
- **Name controls as the reader names them**: "edit box", "check box",
  "split button", never "field".
- **A breath before each key**: `Pause=1` where the listener needs it.
- **Name no screen reader.** Write "the screen reader" or "the reader".
  The scripts are for everyone's reader.

## Show, then tell

A walk is a conversation, not a lecture. Whenever the host names a concept
or a pattern, the reader shows it straight away, in the reader's own words:

- **A control taking focus** is read as name, role, value, state, then the
  hint, each its own `Hear=` line where the reader pauses: `Untitled, edit,
  multiline, blank` then `Type in text.`; `status: list box, untried, 4 of 5`
  then `To move through items press Up or Down Arrow.` Hint lines begin "To",
  "Press" or "Type in", so the build speaks them in the message voice, as a
  reader speaks a tutor message.
- **A window activating** is read by its title, then the program's own
  announcement, then the control with focus: `DbDo` then `DbDo ready`.
- **A pattern** is shown by pressing one key that follows it and hearing the
  result, then named in one sentence: Shift plus Z asks and changes nothing,
  and the reader proves it.

After the reader speaks, the host says in one sentence what the listener
just heard, naming the parts: "Name: Untitled. Role: edit. Value: blank.
Then the hint." Keep each `Say=` to two or three short sentences; a longer
explanation is a sign the reader should be showing it instead.

The checker measures this. In walks 02 and 03 no more than two steps in a
row may pass without the reader, and at least half the steps must carry the
reader; other walks get a notice after three host-only steps in a row, and
any `Say=` over sixty words gets a notice. Walk 00 (prose, then the
contents) and walk 11 are not measured. A `Hear=` line written from the
phrasing rules below rather than from a recording carries a `Note=` asking
for a live run (`buildTutorials -live`) to confirm it.

## How the reader phrases a control

At its middle verbosity. Taken from real speech; do not improve it.

- **A window appears:** title alone, then "<title> dialog", then the text,
  then the focused control. `HomerScribe results dialog` /
  `One source done. Took 14 minutes.` / `OK button`.
- **Check box:** label, "check box", state, access key as words.
  `Transcribe audio check box, checked, Alt plus T`. Toggled by its access
  key, the same line again with the new state.
- **Button:** label, "button", access key. `OK button`. A symbol is read:
  `Next greater button, Alt plus N`.
- **Radio button:** label, "radio button", state, position, key.
  `Words radio button, checked, 2 of 4, Alt plus T`.
- **Combo box:** label with colon, "combo box", value, position, key.
  `Use keyboard layout: combo box, Desktop, 1 of 3, Alt plus L`.
- **Edit box:** label with colon, "edit", contents. `Source paths: edit,
  https colon slash slash ...`. Select All: `selected` and the text. Paste:
  nothing.
- **Slider:** label, direction, value. `Rate: left right slider, 50 percent`.
- **Menus:** `Menu bar`; `Options menu`; items with their letter after;
  `Voices submenu, V`; `Leaving menu bar`.
- **Slider with a value:** `Voice rate: 68, left right slider, 25 percent`;
  a numeric edit: `Voice pitch change percent: edit, 20`.
- **Tabbed dialog:** `Properties dialog, Shortcut page`.
- **List view item:** `Folder view list view, not selected, Recycle Bin
  object, 1 of 12`; a typed letter reads the item it reached.
- **A program's loading message comes before its title:** `Please wait`,
  then the title, then the focused control.
- **In an edit box:** typing echoes each character, `space`, `Enter`,
  `Period`; Right Arrow speaks the character; Control plus Right Arrow the
  word; Backspace the character erased; an empty line `Blank`; Control plus
  Home `Top of file` then the line; Control plus End `Bottom of file` then
  the line; Home and End nothing. Shift plus Right Arrow: the character then
  `selected`; back off it `unselected`; Control plus Shift plus Right Arrow:
  the word then `selected`; Shift plus Down Arrow: `Selected` and the line;
  read-selection: `Selection is` and the text; Control plus C: `Copied
  selection to clipboard`.
- **Access keys are words:** `Alt plus T`, never `Alt+T`, in a Hear line.
- **Names as the synthesizer says them:** `Introduction to Windows dot m p
  3`, `https colon slash slash www dot`, `C colon backslash Users`.
- **A direct announcement from the program is its own sentence,** before
  the results box: `Done. Introduction to Windows dot m p 3`.

## Where the truth comes from

Write a `Hear` line from evidence, never from expectation:

1. **The dialog's code.** In an Lbc dialog the add order is the focus order;
   a control's caption carries `&` before its access letter; the label
   before an input box is what the reader says with a colon. Read the
   `addInputBox`, `addCheckBox`, `addButton` calls and take the words from
   them.
2. **The program's own announcements.** Grep the source for `announce(`,
   `logMessage(` third arguments, results-box text; they are what the
   program says, and the reader reads them as written.
3. **A speech history.** When the person can paste what their reader spoke,
   that is the final word on phrasing; it beats every rule above.
4. **A transcript of a training class**, read back through HomerScribe,
   for grammar not yet in the list.

If none of these settles a line, say so in the `Note` rather than guessing.

## Check, then build

    scripts\checkTutorial              every help\Tutorial_*.inix
    scripts\checkTutorial Tutorial_01  one of them

The check parses each script and reports, with the script name and step
number: a step with a `Key` and a `Hear` that names no silence; `Alt+` in a
`Hear` line; a screen reader named anywhere; a Hear line for a check box
out of order; an underscore or a bare `.mp3`/`.pdf` in a `Hear` line; a
first script without the repeat key. `scripts\buildTutorials` runs it
first and speaks nothing while it reports problems. Zero problems is a
real answer.

    scripts\buildTutorials             speak what has no audio
    scripts\buildTutorials Tutorial_01 speak one again

The voices live in `C:\HomerDev\exec`, fetched by `build` only.

## The kit's tutorial guide

[references/Tutorials.md](references/Tutorials.md) is the kit's own guide,
copied from its help folder at each build. Read its "Audio tutorials" part --
the playlist, making the audio, the voices, checking one, writing one, how a
screen reader trainer narrates, and how a reader phrases a control -- before
writing or reviewing a walk; it holds the conventions refined over many
tutorials. Its scenarios are the kit's own walks, useful as worked examples.
