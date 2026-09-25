---
name: homer-tutorial
description: Write, check and build the spoken walkthroughs of a Homer Tools app -- Tutorial_NN_*.inix scripts where a narrator works and a screen reader answers. Use when asked to write a tutorial, walk, or walkthrough for a Homer app, to simulate what a screen reader says, to add a Hear line, or to check tutorial scripts before building their audio. Names no screen reader in the scripts.
---

# Homer tutorial skill

A Homer tutorial is a dialogue: a person doing a real job in the app, and a
screen reader answering exactly as a reader does. Each script is a
`help\Tutorial_NN_Name.inix` file; `scripts\buildTutorials` speaks it into
`help\tutorials\Tutorial_NN_Name.mp3` with two voices and writes the text into
`help\Tutorials.md`. The reader's lines are the whole value: they must be
what the listener will hear on their own machine.

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

The voices live in `C:\HomerDev\exec`, fetched by `buildHomerDev` only.
