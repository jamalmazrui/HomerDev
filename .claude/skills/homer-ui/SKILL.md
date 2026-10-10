---
name: homer-ui
description: >-
  Designs and reviews the user interface of a Homer Tools app for screen reader
  users: Lbc dialogs and their focus order, labels, accessible names and access
  letters, menus and trigger letters, hotkeys and key names, function-key
  families, speech through JAWS and NVDA, and the choice between a single
  dialog, a command line and a multiple-document (MDI) app. Use when building
  or changing a dialog, menu or key binding, choosing a hotkey, deciding what
  the app should speak, or reviewing a Homer app's interface for accessibility.
---

# Homer user interface

A Homer app is used with a keyboard and a screen reader. Every rule below
serves one aim: the person hears each thing once, in the order they meet it,
and can reach any command by a key they can guess.

## Dialogs (Lbc)

- **Build every dialog from Lbc**, never a designer. **Add order is focus
  order**: the order of the `add` calls is the tab order and the reading
  order. When it is wrong, fix the calls or Lbc, never with TabIndex in the app.
- **A label comes just before its field**; that names the field. Never set an
  accessible name equal to a control's caption or the label before it (the
  reader would say it twice). Only a control with no visible text gets one.
- **Access letters** come from `&` in a caption or the preceding label, first
  letter of a word, no extra code. **One trigger letter per menu or dialog**:
  the first item to claim a letter keeps it; a later one gets none.
- **Fixed choices are buttons; dynamic choices are a list.** When a dialog's
  whole job is a choice among options built into the program, such as a
  filter action, a chart type or a settings category, show them as buttons
  with `runWithButtons`, and Cancel. Each button's letter begins one of its
  words, the first to claim a letter keeps it, H stays free for Help, and
  OK and Cancel get none. A pick list is for choices that come from the data
  or the session: columns, tables, open windows, recent files. A choice that
  is one field among several in a form stays a list or combo box there.
- **The words on screen are the spoken words.** A control's name comes from
  its caption or the label before it, so what a screen reader says and what a
  voice-control user says (Windows Voice Access, Dragon) are the words shown.
- **Initial focus in a multi-line text box is at its start.**
- **Save a setting as soon as the person answers**, not at exit.
- **A field earns its line**: leave out empty values, a program's word for
  empty, and facts about a file rather than its content.
- Dialog-wide keys come with Lbc: Control+Enter accepts from anywhere, Escape
  cancels, F1 is Help (ending with the version, see homer-elevate), F7 lists
  the controls.

## Menus

Long, flat menus: arrowing is cheaper for a screen reader user than opening a
submenu. A submenu is at most one level deep, only to gather rarely used
items or to open a fresh set of trigger letters. A menu item's trigger letter
is its hotkey's letter when it has one.

## Keys

- **A hotkey's letter is the first letter of a word of its command name**,
  never mid-word; better no key than a mid-word one. Rare exceptions with a
  strong association: X for Export, Z for toggles (sleep), Shift+Z for Say
  Status (Z at the bottom, like the status bar). Explain an exception in the
  docs.
- **A one-key command works only where it belongs.** A command on a single
  printable key (Question Mark in FileDir's file list) acts only while its
  list or field has focus, never across the app, so typing elsewhere never
  sets it off (WCAG 2.1.4).
- **Alt+Control is for Windows desktop shortcuts**, never an app binding,
  function keys included. Two exceptions: the app's own desktop shortcut
  (Alt+Control+D opens DbDo), and Alt+Control with navigation keys to move
  within a window.
- **Drop the screen reader modifier** where nothing conflicts (Windows,
  Chromium, JAWS, NVDA), preferring Alt+Shift+letter to Alt+letter, since
  Chromium fires a page's access keys on Alt+letter. Keep one key on JAWS and
  NVDA where possible.
- **Do not fight Windows' selection and navigation keys.** In Homer apps:
  Shift+Home/End mark to the top or bottom, Alt+Shift+Home/End reverse that,
  Control+Home/End go to the first or last item, Control+Up/Down step through
  marked items, Control+PageUp/PageDown move between tables or windows,
  Backspace goes up a level, Alt+Left/Right go back and forward.
- **Function-key families**: F1 help (F1 guide, Shift+F1 history, Alt+F1
  About, Control+F1 key describer); F2 edit or rename; F3 search and repeat; F4
  pick, say or close windows; F5 refresh; F6 panel focus (Control+Tab and
  Control+Shift+Tab move among the app's windows, called "<App> windows");
  F7 spell check or review; F8 selection, copy all, say all; F9 readable view;
  F10 menus (Shift+F10 context, Alt+F10 alternate); F11 version and elevation;
  F12 open or close files, or AI.
- **The grave accent key is speech**, where an app has speech commands: Alt
  and Alt+Shift for louder and softer, Control and Control+Shift for faster and
  slower, the screen reader key plus Grave for punctuation.
- **Key names** are written as JAWS writes them: modifiers in alphabetical
  order (Alt, Control, Shift, Windows), "Control" spelled out, the reader key
  as "JAWS" or "NVDA". Convert with KeyName, never a table of one's own.
- **One command table (KeyMap)** feeds the menus, the key describer and the
  hotkey list, so they cannot disagree.

## Speech

- **Do not repeat what the screen reader says**: no speech for a dialog's
  title or a focused control's name. Speak only what the reader cannot know.
- **Report only what happened this session**, and match the noun to the count
  ("1 file"); zero is an answer, not an error.
- **Speak the parts of a grouped announcement as separate utterances**
  (`Say.sayParts`), with no added pauses: column, row position and value as
  three.

## Checking a control

Every control a person can reach exposes four things through UI Automation,
which is what JAWS, NVDA and Narrator read: its **name** (from its caption or
the label before it), its **role** (button, edit, list ...), its **value**
where it has one, and its **state** (checked, expanded, unavailable ...); and
it can be reached and used from the keyboard alone. What each Lbc control
exposes, and how to look at the tree with Accessibility Insights for Windows,
is in [references/uia.md](references/uia.md). A check confirms the tree; a
pass with JAWS and with NVDA confirms what the person hears.

## Shapes of app

A single tool (a command line and one dialog, the same settings in both), a
multiple-document app (DbDo, EdSharp, FileDir: one instance, opened or brought
forward by its desktop shortcut), or an NVDA add-on. The kit's guide explains
each in [references/ui-guide.md](references/ui-guide.md), with Lbc's calls,
Say's routes to each screen reader, and KeyName's conversions; it is taken
from the kit's HomerDev.md at each build.

Lists in the interface and in documents are in lowercase alphabetical order
unless another order is clearly more logical.
