---
name: homer-screen-reader
description: >-
  Writes, installs and troubleshoots screen reader scripting for Homer Tools
  apps: JAWS scripts (.jss, .jsh, .jkm, .jsd) and NVDA add-ons (global plugins
  and app modules), with the same commands and keys on both readers, direct
  speech through the kit's Say, packaging as <App>_JAWS.zip and
  <App>.nvda-addon, and installation for every JAWS version and NVDA. Use when
  adding or fixing JAWS scripts or an NVDA add-on, choosing a reader key,
  making a command work under both readers, or diagnosing why scripts do not
  load, compile or answer.
---

# Screen reader scripting

A Homer app is used with JAWS or NVDA, and what it adds for one it adds for
the other: the same commands, on the same keys where the readers allow, worded
the same way. JAWS is the user's primary reader, NVDA the second.

## First, whether a script is needed

Most of what an app wants a reader to say goes through the kit's Say
(`Say.say`, `Say.sayParts`), which speaks directly through JAWS or NVDA from
the app itself, with no script at all. Write scripts only for what an app
cannot do from inside: keys that must work while the reader owns them (in a
browser's virtual cursor, say), announcements the reader must make on its own
events, or commands that act on another program's window.

## The rules on both sides

- **One set of commands, measured.** Every command has a JAWS and an NVDA
  form, or a stated reason it has not (the reader already does it). Parity is
  checked by a script, not asserted.
- **Keys**: the rules of homer-ui -- a word's first letter, JAWS .jkm names
  with the modifiers in order, the reader key written "JAWS" or "NVDA", the
  modifier dropped where nothing conflicts, Alt+Control left to desktop
  shortcuts, the grave accent for speech (Alt louder, Control faster, Shift the
  reverse, the reader key plus Grave for punctuation).
- **Scope**: a script's keys belong to the program it serves and nowhere
  else. Never write to the user's default.jkm, default.jss or MyExtensions:
  a key put there acts in every program (HomerView's Control+O once opened a
  document inside Outlook).
- **Speech**: speak what the reader cannot know; never a window title or a
  control's name it already announces; the parts of a grouped announcement as
  separate utterances.
- **Camel Type** in JAWS script and in add-on Python alike; the JAWS rules are
  in [references/CamelType_JAWSScript.md](references/CamelType_JAWSScript.md).

## An NVDA script, declared in full

Declare each NVDA script with the `@script` decorator from `scriptHandler`,
giving every field a person can meet: a `description` (what Input Help says
and what NVDA's Input Gestures dialog lists, so it can be reassigned), its
`gesture` or `gestures`, and a `category` named for the app. A script that
only reports information sets `speakOnDemand=True`, so it still speaks when
the person has chosen NVDA's "on demand" speech mode. `ui.message` is for
what NVDA cannot know on its own -- a result, a count, a status -- never a
control's name or a window title it already announces.

A script is proved in the reader itself: one that compiles or imports
cleanly can still fail to load, or lose its key to another script. Press its
key with JAWS or NVDA running before calling it done.

## Where it lives and how it ships

- JAWS sources in `scripts/jaws` (`<App>.jss`, `.jsh`, `.jsd`, `.jkm`, and a
  `.jcf` when settings are needed); the build packs them as
  `exec/<App>_JAWS.zip`.
- An NVDA add-on in `addon` (`manifest.ini`, `globalPlugins/<name>/` or
  `appModules/<program>.py`, `doc/en`); the build zips it as
  `exec/<App>.nvda-addon`.
- **Never ship a compiled `.jsb`.** A `.jsb` runs on the JAWS version that
  built it and later ones, so one built elsewhere may not suit the target.
  Ship sources only; the installer compiles them with each installed
  version's own `scompile.exe`. `.jsb` files are never pushed to git.
- The kit's `installScreenReaderSupport.cmd`, run from the finish page's two
  boxes ("Install JAWS scripts", ticked, then "Install NVDA add-on", ticked),
  unpacks the JAWS scripts into every JAWS version's user settings folder and
  compiles them there with that version's compiler, and hands the add-on to
  NVDA. It runs as the ordinary user, never elevated: JAWS keeps its settings
  in the user's own profile.

## The publishers' own guides

For anything the notes below do not settle -- a function's parameters, an
event's name, an NVDA API -- search the two gathered guides rather than
reading them whole: [references/JAWSScripting.md](references/JAWSScripting.md)
(Freedom Scientific's scripting documentation, 30 August 2026, about 100,000
lines, a function reference grouped by first letter) and
[references/NVDAScripting.md](references/NVDAScripting.md) (NV Access's
developer guide and the community add-on guide, 31 August 2026). Each opens
with a contents list; search for the name first.

## JAWS and NVDA in detail

Read [references/jaws-and-nvda.md](references/jaws-and-nvda.md) before
writing or diagnosing either: which script files JAWS actually loads,
layering over the factory scripts, key maps and their sections, compiling for
each JAWS version, an add-on's structure and gestures, carrying the kit's
Python modules inside an add-on, and how to diagnose a script that does not
load or a key that answers "Unknown script call".
