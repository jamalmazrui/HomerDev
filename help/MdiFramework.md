# Build Your Own App on the Homer MDI Framework

This guide is for anybody who wants to build a Windows program that works well with a screen reader, alone or with an AI assistant. You need some comfort with code, but you do not need to know Windows Forms. The kit's frame does the hard parts: windows, menus, keys, help and speech.

DbDo, EdSharp and FileDir are this kind of program. So is the fruit basket sample, which shows every feature in one small file: Templates\\samples\\FruitBasketMdiCs.cs.

## What You Get Without Writing Anything

A new app on the frame already has all of this:

- **A window for each thing you work on,** inside one frame. F4 lists the windows, Shift+F4 says them, Control+Tab moves between them, and Control+F4 closes one.
- **A Help menu.** F1 opens the guide, Shift+F1 the history, and Alt+F1 About. Control+F1 makes every key describe itself instead of running. Alt+F10 lists every command in one searchable list.
- **Settings.** Alt+Shift+E changes a setting at once, with nothing to restart.
- **The clipboard and files.**
  - Alt+Apostrophe says the clipboard.
  - Control+Apostrophe saves it in a new text file. It never replaces a file.
  - Control+Shift+Apostrophe adds it to the end of a text file you pick.
  - Alt+Shift+Apostrophe clears it.
- **Small conveniences.** Alt+SemiColon says the time, and Control+F12 copies the log as a file, ready to attach to an email.
- **Keys that never fight your screen reader.** Typing in a text box always types, and a list keeps first-letter navigation.

## C# or Python

The frame is written once, in C#. A Python app uses that same frame, not a copy: the kit's mdi.py loads it from exec\\Homer.dll through pythonnet. Every command, key and help feature on this page is therefore the same in both languages. The fruit basket comes in both, FruitBasketMdiCs.cs and FruitBasketMdiPy.py, and the kit's build fails if the two ever declare different commands.

## Start an App

1. **Make the project.** In a command prompt in the HomerDev folder, type `newHomerApp MyApp --mdi` for C#, or `newHomerApp MyApp --mdi --python` for Python. This makes a MyApp folder beside the kit, with the source, a build script, an installer script and starter documents. A Python project's build installs Python 3.13 and pythonnet if they are missing, and bundles the kit's frame into the program.
2. **Build it.** In the MyApp folder, type `build`. The program is exec\\MyApp.exe.
3. **Try it.** Start it, press Control+N for a new window, and try the keys above.

## Add a Command

A command is one line where you build your frame. In C#:

```
addCommand("&Add Item", "Control+Shift+A", "Put the typed item in the list.", addItem);
```

In Python, the frame comes first:

```
mdi.addCommand(frm, "&Add Item", "Control+Shift+A", "Put the typed item in the list.", addItem)
```

The four parts are:

- **The caption,** with an ampersand before its menu letter.
- **The keys,** in Homer spelling: "Control+Shift+A", "Shift+R or F2" for two keys, or "" for a command found only on its menu.
- **A one-line summary** that starts with a verb. The menu, the Key Describer and the Alternate Menu all speak it.
- **The function that does the work.** It returns true when it has dealt with the command.

You never write a KeyDown handler. Every key goes through one router in the kit, which knows where your keys belong.

## Menu Letters

Put the ampersand before the first letter of a word, never in the middle of one. If two items on one menu claim the same letter, the frame keeps it for the first and gives the later one no letter, and the log says so. Arrowing still reaches every item, and its hotkey still works.

## Choose Good Keys

- **Use the first letter of a word in the command's name,** never a letter from the middle of a word. X for export and Z for a toggle are the accepted exceptions.
- **Leave Alt+Control with letters, digits, function keys and punctuation alone.** Windows uses those for desktop shortcuts.
- **Do not take keys the frame already uses.** The AI NOTE at the top of your MyApp.cs lists them.
- **Your keys are checked for you.** Started with `/exportkeys <file>`, a program on the frame writes every command and key it declares and ends without opening a window. The kit's checkKeys reads that file and reports any key Windows or a screen reader owns, and any key used twice. You never run it by hand: the kit's build checks the sample on every build, and the shared check that runs when you push checks your app the same way, stopping the push if a key clashes.

## Say Why a Command Cannot Run

A command that cannot run should say why, not stay silent. Set its fUnavailable to a function that returns an empty string when the command can run, and the reason when it cannot:

```
KeyMap.Command oDelete = addCommand("&Delete Item", "Control+Shift+D", "Remove the item you are on.", deleteItem);
oDelete.fUnavailable = delegate() { return countItems() == 0 ? "the list is empty" : ""; };
```

Pressing Control+Shift+D on an empty list then says "Delete Item is unavailable: the list is empty".

## Give Answers the Homer Way

A command that tells the person something calls KeyMap.answer with a title and the parts to say:

```
return KeyMap.answer("Position", "Item 3 of 10", "30 percent");
```

One press speaks each part, as its own utterance. A quick second press shows the same text in a window, where the screen reader can spell it, and Control+C copies it. Mark such a command with `.sRepeat = "review"` so the Hotkeys list says so.

Speak only what the screen reader cannot know. It already says the window title and the focused control, so never repeat those.

## Lists with Shift+Letter Commands

In a list, letters move by first letter. If you want Shift plus a letter to run commands while the list has focus, pass the list to manageList in your window, and declare those commands with the list context:

```
manageList(lbItems);
addCommand("Say &Item", "Shift+I", KeyMap.sListContext, "Say the item you are on.", sayItem);
```

Typing the start of an item still goes to it, and an unbound Shift+letter says it has no command, so a question never meets silence.

## Ask, Then Repeat

A command that asks a question can remember the answer for each window, so a partner command repeats it without asking. Control+J for Jump and Alt+J for Jump Again are the usual pair:

```
KeyMap.rememberInput("jumpToItem", this, sAnswer);
string sLast = KeyMap.recallInput("jumpToItem", this);
```

Call KeyMap.setLastSearch so F3 knows which search to repeat in that window. When a window closes, its memory goes with it.

## Titles

The frame's title is your app's name and nothing else. A window's title is what it shows, set with setTitle, and never the app's name again. A screen reader reads the two together, and a repeated name is read twice.

## Settings

Declare a setting once, in your frame's constructor:

```
addSetting("Basket Size", "10", "The most fruit one basket holds.");
```

Alt+Shift+E lists your settings, saves a change to MyApp.inix the moment it is made, and calls your onSettingChanged so the program acts on it at once. Read a setting with settingValue.

## Working with an AI Assistant

Give your AI assistant MyApp.cs and this guide, and ask for one command at a time. The AI NOTE at the top of MyApp.cs states the rules it must keep. For example:

> Add a command, Sort Items, on Control+Shift+S, that sorts the list in this window alphabetically and says how many items it sorted.

After each change:

1. **Build.**
2. **Try the new key with your screen reader.**
3. **Press Control+F1 and then the key,** to hear that it describes itself correctly.
4. **Run your build again.**

When something goes wrong, Control+F12 copies the log, ready to hand to the assistant.

## Learn from the Sample

Templates\\samples\\FruitBasketMdiCs.cs uses every feature on this page. Its opening comment lists what to try with a screen reader. help\\HomerSuite.md is the contract the four Homer Suite apps follow, and the rules your app inherits from the frame.
