# The reader's voices in a spoken walk

*What was learned from the JAWS training and scripting documentation on
25 September 2026, and what the tutorial tool now does with it. For folding
into the kit's Tutorials.md.*

## How JAWS actually varies its voice

JAWS speaks through **voice contexts**, each with its own rate, pitch and
volume in Voice Adjustment: PC cursor, JAWS cursor, keyboard, tutor and
message, menu and dialog, screen. Its scripts send each kind of speech to one
context with `SayUsingVoice` and an output type -- `OT_CONTROL_NAME`,
`OT_HELP` (tutor), `OT_MESSAGE`, `OT_STATUS`, `OT_DIALOG_NAME`, `OT_POSITION`
and so on. So a control's name, role, value and state arrive through the PC
cursor voice; a tutor message, a JAWS message and a program's own `SayString`
through the tutor-and-message voice; a menu item or a dialog title through the
menu-and-dialog voice; an echoed keystroke through the keyboard voice.

Two things vary in every JAWS, out of the box: a **capital letter is spoken 20
percent higher** in pitch, and **spelling runs 20 percent slower**. Beyond
those, the six contexts sound the same until the listener changes one. The one
listeners most often change is tutor and message, raised a little so that a
hint or an announcement stands apart from the screen.

What JAWS does **not** do, out of the box, is speak name, role, value, state
and hint in five voices. The parts of a control are one utterance in one
voice; the hint that follows is a second utterance in the message voice. A
walk that gave each part its own pitch would be teaching something JAWS does
not do.

## What the tutorial tool does now

Each Hear line is placed in a context by its shape, as a listener places it by
ear, and shifted by that context's offset in semitones, set in `[global]`:

- **ReaderPitchMessage** (default 2): tutor hints ("To activate press
  Spacebar"), JAWS messages ("Leaving menus"), and the program's own
  announcements ("DbDo ready", "Marked row 2", "status: jobs, row 2 of 4").
- **ReaderPitchMenu** (default 0): menu items ("Open Database..., Control+O,
  O") and dialog titles ("Filter Records dialog").
- **ReaderPitchKeyboard** (default 0): a single echoed character.
- The PC cursor voice is the reader's own, unshifted: controls, rows, cells.

A Hear line can force a context with a leading `@cursor:`, `@message:`,
`@menu:` or `@key:`, which is removed before speaking. The tutorial log names
each line's context, so a misplaced one is easy to find.

The defaults follow the common practice rather than the factory setting: a
listener who leaves every context alone hears one voice, and a walk that
raised nothing would be right for them but would hide the distinction that the
walks themselves rely on -- which line is the screen, and which is the program
talking to you.

## The say routines

`Say.say(params string[])` in Say.cs speaks each string as its own utterance,
in order, with nothing inserted between them. Three facts handed to it sound
like three facts; the same three joined with commas sound like one line with
pauses the synthesizer chooses. DbDo's Say Cell and Say Select use it.
