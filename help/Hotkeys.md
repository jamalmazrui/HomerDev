---
title: "HomerDev Hotkeys"
author: "Jamal Mazrui"
---

# Hotkeys

The kit itself has no commands to press a key for. What it has is the keys that
Lbc gives every Homer dialog and every Homer text box, free, in every app built
on it. They are listed here three ways: by key, by what they do, and by where
they work.

Key names follow the Homer conventions: modifiers in alphabetical order,
"Control" spelled out, and the screen reader key called JAWS or NVDA.

# By key

- Alt+C -- append the current line or selection to the clipboard, in a text box
- Alt+F8 -- read the whole field aloud, in a text box
- Alt+H -- press the Help button, in a dialog
- Alt+X -- append the cut line to the clipboard, in a text box
- Control+C -- copy the current line when nothing is selected, in a text box
- Control+D -- delete the current line and speak the next one, in a text box
- Control+Enter -- accept the dialog from any control, including a memo box
- Control+F8 -- copy the whole field, in a text box
- Control+J -- search inside the list, in a list box
- Control+X -- cut the current line when nothing is selected, in a text box
- Escape -- cancel the dialog
- Enter -- press the accept button, from any control that does not use Enter
- F1 -- show the dialog's help
- F3, Shift+F3 -- repeat that search forwards and back, in a list box
- F8 -- start marking a selection, in a text box
- Shift+F5 -- open what is under the cursor: a link, a path, an address
- Shift+F8 -- complete the marked selection, in a text box
- Tab and Shift+Tab -- move through the controls in the order they were added

# By description

- Accept the dialog: Enter, or Control+Enter from anywhere
- Append to the clipboard rather than replacing it: Alt+C to copy, Alt+X to cut
- Cancel the dialog: Escape
- Copy the item under the cursor, in a list: Control+C
- Copy the whole field: Control+F8
- Copy or cut the current line without selecting it first: Control+C, Control+X
- Delete the current line: Control+D
- Help for this dialog: F1, or Alt+H
- Mark a selection in two keystrokes instead of holding Shift: F8 then Shift+F8
- Move through the controls: Tab and Shift+Tab
- Open the link, path or address under the cursor: Shift+F5
- Read the whole field aloud: Alt+F8
- Search inside a list: Control+J, repeated with F3 and Shift+F3

# By where it works

## In any Homer MDI app

These come with the frame. An app that uses `Mdi.cs` has all of them without
writing any.

- Alt+F1 -- about: the version, where this copy is, and where its log is
- Alt+F10 -- alternate menu: every command in one list you can filter
- Alt+Shift+C -- change a setting, from a list of what this program lets you change
- Alt+Shift+S -- run a script, from a list of what is in the scripts folder
- Control+F1 -- key help: a key says what it would do instead of doing it
- Control+F4 -- close this window
- Control+Shift+F4 -- close every window but this one
- Control+Shift+Tab -- previous window
- Control+Tab -- next window
- F1 -- the guide
- F4 -- current windows, as a pick list
- Shift+F4 -- say how many windows are open, and their titles

## In any Lbc dialog

- Control+Enter -- accept, from any control
- Enter -- accept
- Escape -- cancel
- F1 or Alt+H -- help
- Tab, Shift+Tab -- move through the controls in add order
- Alt plus the underlined letter -- jump to that control

## In any Lbc list box

- Control+C -- copy the item under the cursor
- Control+J -- search inside the list
- F3, Shift+F3 -- repeat the search forwards and back
- Arrow keys, Home, End -- move through it as any Windows list

## In any Lbc text box

- Alt+C, Alt+X -- append a copy or cut to the clipboard
- Alt+F8 -- read all
- Control+C, Control+X -- copy or cut the current line with no selection
- Control+D -- delete the current line
- Control+F8 -- copy all
- F8, Shift+F8 -- start and complete a selection
- Shift+F5 -- open what is under the cursor, after a confirmation

## In the help and results box

- Arrow keys -- read line by line
- Control+PageDown, Control+PageUp -- next and previous record, in the record
  view only
- Escape -- close

# Choosing keys for your own app

- Give every command a mnemonic: the first letter of one of its words.
- Never use Alt+Control combinations. That space belongs to Windows desktop
  shortcuts, function keys included.
- Prefer Alt+Shift plus a letter over Alt plus a letter: Chromium fires a web
  page's access key on Alt+letter and does not on Alt+Shift+letter.
- Do not take a key whose Windows meaning is selection or navigation.
- Aim for one key that works on both JAWS and NVDA.
- Register it with `KeyMap` so the menu, the key describer and the hotkey
  document all agree.
