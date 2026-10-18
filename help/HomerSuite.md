# The Homer Suite Contract

The Homer Suite is four programs that share one set of habits:

- **DbDo** for data.
- **EdSharp** for documents.
- **FileDir** for files and folders.
- **HomerView** for the web.

HomerDev is the kit beneath them, and DbDo is the reference for how a command is found, described and run.

This page is the contract: the rules all four follow, the data files that record them, the stages of the work, and where the work stands. It was settled over five rounds of planning, with Claude leading and ChatGPT reviewing, and with Jamal Mazrui's rulings deciding every disagreement.

## How to read a status

Every decision carries one of five statuses, and no status is assumed from another:

- **Current** means it is how the program works today, with no change planned.
- **Proposed** means both AIs recommend it; it waits for its stage.
- **Ruled** means Jamal decided it.
- **Implemented** means the code is written and delivered.
- **Verified** means it was tested on Windows with a screen reader, and the result was recorded.

## The data files

### Command manifest

The command manifest is data\\SuiteCommands.inix. It lists every command of the four apps, one section each, named by app and stable identifier, for example `[DbDo saveClipboard]`.

- **Each section** holds the command's name, its recommended keys, and its status.
- **A changed command** also says what changed, why, and its disposition: accepted, accepted with a stated correction, or removed by ruling.

### Key ownership

Key ownership is in data\\KeyOwnership.inix. It lists the keys that Windows, the screen readers and the browsers own. Each key records its owner, its kind, where it applies, what happens to it, and what a Homer app may do with it.

The kinds are:

- **System:** Windows takes the key first.
- **Convention:** the app receives the key, but it means one thing everywhere.
- **Conditional:** the key is taken only on some machines.
- **Reader global:** a screen reader takes the key everywhere.
- **Reader tables:** a screen reader takes the key only inside tables.
- **Reader laptop:** JAWS takes the key in the laptop layout.
- **Browser:** the browser owns the key, in HomerView only.
- **Historical:** Window-Eyes, kept for reference, not enforced.

### The checker

The checker is scripts\\checkKeys in the kit. It reads both files, and also any file an app writes when started with `/exportkeys <file>`. It reports:

- duplicate identifiers;
- a key bound twice in one app;
- a key that a system or a screen reader takes everywhere;
- keys to test in their real control;
- hotkey letters that start no word of their command;
- every difference between what a program declares and what the manifest says.

It runs inside the normal cycle, so nobody runs it by hand:

- **The kit's build** checks the whole manifest and the MDI sample's export, and fails on a problem.
- **Every app's push** runs the shared check, whose "suite" check exports the app's own keys when it is on the Homer frame and checks that app's manifest entries, and stops the push on a problem.

A key shared on purpose carries an exception= line in the manifest saying why, and is counted as reviewed, not as a problem. Keys to test in their real control and first-letter misses are reported, never failed.

## Rulings

- **Alt+C appends.** Control+C copies the current item (a line without a selection, a cell, a file), and Alt+C appends it to the clipboard. (Ruled)
- **Alt+Delete is Say Position.** It gives useful position information: a count and a percent for the current unit. Where JAWS would report pixel coordinates, each app's JAWS key map passes the key through to the app, from a reviewed allowlist. (Ruled)
- **Claude leads; ChatGPT advises and reviews.** (Ruled)
- **Control+Tab and Control+F6 never duplicate each other.** They are next-in-cycle at different levels or in different orders. (Ruled)
- **Edit Settings is Alt+Shift+E in every app.** Alt+E already opens the Edit menu. X for export is an accepted exception to the first-letter rule. (Ruled)
- **EdSharp's block movement is removed,** and its bookmarks move to the B keys. (Ruled)
- **HomerView joins the suite,** and records in an .inix file the browser installations it is active in. (Ruled)
- **New apps on a new core.** Settings are .inix only; the programs are 64-bit on .NET Framework 4.8.1, with NuGet; there is no transition code for existing users, beyond a History note. (Ruled)
- **No c_ prefix on constants,** and url is written in lower case. (Ruled)

## The key families

- **Levels of next and previous:**
  - **Control+Tab and Control+Shift+Tab:** the app's windows. In HomerView, the browser's tabs.
  - **Control+F6 and Control+Shift+F6:** the things inside a window, in a fixed order.
  - **Alt+F6 and Alt+Shift+F6:** the same things, in the order last visited.
  - **F6 and Shift+F6:** the views or parts of the current thing.
  
  An app fills only the levels it has. HomerView leaves F6 to the browser.
- **Window family:**
  - **F4:** pick a window.
  - **Shift+F4:** say the windows open.
  - **Control+F4:** close this window.
  - **Control+Shift+F4:** close all but this one. A window holding unsaved work may refuse, and the count of windows kept open is spoken.
- **Key spellings** are KeyName.cs's, taken from JAWS's own default.jkm: modifiers in the order Alt, Control, Shift, Windows; Control spelled out; GraveAccent, Backslash and SemiColon for those keys. The checker accepts other spellings when comparing, but every file Homer writes uses these.
- **Help family:**
  - **F1:** Documentation.
  - **Shift+F1:** History of Changes.
  - **Alt+F1:** About.
  - **Control+F1:** Key Describer Toggle.
  - **Control+Shift+F1:** Hotkeys.
  - **Alt+Shift+F1:** ReadMe.
  - **Alt+F10:** Alternate Menu.
  - **Alt+Shift+H:** Hotkey Summary.
  - **F11:** Elevate Version.
  - **Control+F12:** Copy Log.
  - **Play Tutorials,** with no key, plays the walks in the Homer Player.
- **Say family:**
  - **Alt+Apostrophe:** Say Clipboard.
  - **Alt+P:** Say Path.
  - **Alt+Delete:** Say Position.
  - **Alt+Z:** Say Status.
  - **Alt+SemiColon:** Say Time.
  - **Shift+F4:** Say Windows Open.
  - **Alt+Y:** Say Yield.

  DbDo keeps its Shift+letter say layer as a second set of keys.
- **Clipboard family:**
  - **Alt+Apostrophe:** say the clipboard.
  - **Alt+Shift+Apostrophe:** clear it.
  - **Control+Apostrophe:** save the clipboard to a new text file.
  - **Control+Shift+Apostrophe:** append the clipboard to a text file.
- **Undo and Redo:** Control+Z and Control+Shift+Z everywhere.
- **Export:** Alt+Shift+X. In the editors, Alt+X stays Cut Append.
- **Repeat keys:** a quick second press of a Say key shows the same information in a read-only window you can review and copy. Control plus a letter asks; Alt plus the same letter repeats the last answer, but only where an app registers that pair. F3 and Shift+F3 repeat whichever search ran last in the window.
- **Managed lists** (the DbDo grid, the FileDir list):
  - unshifted letters move by first letter or by typed sequence;
  - Shift plus a letter runs a command or says none is bound;
  - Control+Space toggles the mark;
  - Control+Home and End go to the first and last item;
  - Control+Shift+Home and End go to the first and last marked item;
  - Control+UpArrow and DownArrow go to the previous and next marked item.

The exceptions each app keeps on purpose (EdSharp's F2 and F5, FileDir's Shift+letter actions, HomerView's browser keys) are recorded in the manifest.

## AI attachment rules

These apply to Chat with AI (F12) and Chat about (Shift+F12) in every app.

- **No implicit attachment.** Chat with AI never attaches a document, table or file because of how a question is worded. When context is attached, the choice is shown plainly. EdSharp's current behavior, which attaches the document when the wording refers to it, must change, not merely be renamed.
- **Say the source and scope first.** Chat about names the actual source and scope before sending: the selection, the marked rows, the visible view, or the whole thing.
- **Report what happened.** Truncation, omitted content, conversion failures, and the model or service used are reported accurately.
- **Answers are content, not instructions.** Instructions inside a document or an answer are treated as text. No SQL, script, browser action or file operation runs automatically from an answer.

## Text files and settings

- **New text files** are UTF-8 with a byte order mark and CRLF line endings, the Homer encoding.
- **Appending to a file:**
  - detect the existing file's encoding first;
  - never put a second byte order mark in the middle of a file;
  - say whether a separating line break is added;
  - leave the file as it was if the append fails;
  - if a file cannot be appended to safely, say so and offer a new file or an explicit conversion, never a mix of encodings.
- **Saving the clipboard** proposes a new file name and never overwrites without asking.
- **Settings in .inix:**
  - writes are serialized and atomic, written to a temporary file and then swapped in;
  - before a cached file is replaced, a change made outside the program is detected, and then the file is reloaded and the change applied again, or the conflict is reported;
  - a malformed file is reported in plain words and kept intact, never treated as empty;
  - each settings file carries a schema version.

## HomerView: browsers and identity

Four ideas are kept apart:

- **The catalog** lists the known browser families, each with a stable browserId such as chrome. One authored file, configs\\HomerView.inix in the HomerView project, is the source. The build makes packaged copies (one inside the NVDA add-on) and checks them against it. Registry discovery stays, so browsers missing from the catalog are still found.
- **Eligibility** records each browser installation HomerView may be active in. Each has its own installationId, resolved path, channel where known, and active flag. Two Chrome installations share a browserId but never an installationId. A missing or moved installation is reported, never silently replaced by another of the same family.
- **The launch choice** names the installationId that Launch starts.
- **The verified session** is the connected browser process family, window, page and document generation actually in front of you.

Eligibility authorizes nothing. It only makes a window worth probing for a connection.

Two rules govern identity:

- **Identity is decided once, in identity.py,** by process, never by program name. With no process known, every key keeps its normal browser and screen reader meaning. (Implemented in stage 1.)
- **A queued request carries a TargetStamp** of the session, window, page and document generation it was made for. Before it acts, the stamp is compared with what is current, and stale work is cancelled with a spoken reason. A read-only result about a page you have left names its source. (The stamp is implemented and tested in stage 1; the queue adopts it in stage 5.)

The HomerView commands added to the manifest are:

- **Choose Active Browsers** (chooseActiveBrowsers), menu only.
- **Key Describer Toggle** (keyDescriberToggle), menu only. It describes HomerView's gestures without running them; gestures the browser or screen reader owns are named, not run.
- **Open Saved Page in EdSharp** (openSavedPageInEdSharp), menu only. It opens an identified saved copy, and offers saving or extraction when there is none.
- **Show Page Folder in FileDir** (showPageFolderInFileDir), menu only. Page Folder keeps opening Explorer.

## Building and compiling

- **Compiler.** Both AIs recommend the Roslyn compiler from Visual Studio Build Tools at C# 7.3, as the suite's chosen language baseline. The build would install it with winget when missing, then find it by an installation probe and verify that it can compile C#, rather than trusting that the install succeeded. (Proposed; awaiting your ruling.)
- **Until that ruling,** the shared classes keep to C# 5, so they still build with the compiler that comes with Windows.
- **.NET Framework 4.8.1.** A build pins the Microsoft.NETFramework.ReferenceAssemblies.net481 package and compiles against those references, not the installed runtime's. Each exe.config keeps version="v4.0" with sku=".NETFramework,Version=v4.8.1". The compiler's path, version and language option go in the build log.

## Stages

1. **Stage 0, the contract.** This page and the two data files. Implemented in kit 1.73.0.
2. **Stage 1, the proofs.**
   - **Desktop proof:** Templates\\samples\\FruitBasketMdiCs.cs on the new frame.
   - **Browser-identity proof:** HomerView's identity.py and scripts\\testIdentity.py.
   
   Implemented and released on 18 October 2026, in kit 1.73.0 and HomerView 1.48.110:
   - both full cycles passed;
   - the sample compiled with the compiler that comes with Windows;
   - its export listed all 35 commands with no problem;
   - testIdentity passed 18 of 18 on Windows.

   Verified needs one more thing: your JAWS and NVDA pass through the checklist below.
3. **Stage 2, the minimum core.**
   - **The checker is a gate** in the kit's build and in every app's push. Implemented in kit 1.73.1.
   - **One table of key spellings.** KeyMap names every key through KeyName.cs, whose spellings come from JAWS's own default.jkm: GraveAccent, Backslash, SemiColon. Implemented in kit 1.73.2.
   - **The clipboard family in the frame:** Save Clipboard, Append Clipboard and Clear Clipboard, by the text-file rules above. Every app on the frame has them. Implemented in kit 1.73.3.
   - **One trigger letter per menu, enforced by the frame.** A later item that would repeat a letter loses its ampersand, so an app's items and the frame's never clash. Implemented in kit 1.73.3.
   - **Safer .inix files.** InixCodec now does three things:
     - readValue parses a file once and again only when its time or length changes;
     - writeValue and writeAsConfig write a temporary file and swap it in;
     - a file that cannot be read is reported once, through onProblem, which the frame connects to the log, and is never taken as empty.
     
     Implemented in kit 1.73.4. The schema version in each settings file comes with each app's move to the frame.
   - **The reviewed JAWS pass-through.** Each tidy writes into an app's scripts\\jaws\\\<App\>.jkm the keys the suite allows it to hand on, which today is Alt+Delete, Say Position. The allowed keys are those with passThrough=yes in data\\KeyOwnership.inix; a key is handed on only when the app really binds it, by its own Hotkeys.md. The lines go in a marked block, and keys the app maps itself are left alone. Tidy also names bracket keys that a bare "[" would turn into a section. The shared check confirms the block before every push. HomerView is excepted in the data, because its key map is chained into the browsers'. Implemented in kit 1.73.5.
   - **Stage 2 is complete.** The menu repaint change is EdSharp's and FileDir's own code, so it moves to stage 4.
   - **One frame for both languages.** Homer.dll now carries KeyMap, KeyName and Mdi, so a Python app builds the C# frame through pythonnet (exec\\Python\\mdi.py), not a wxPython copy. The fruit basket samples in C# and Python are twins, and the kit's build exports both and fails if their commands, keys or contexts differ. newHomerApp makes a Python MDI app with `--mdi --python`. Implemented in kit 1.73.6.
4. **Stage 3, DbDo.** Its private KeyMap is replaced through an adapter and retired once equivalence is shown, then its key changes, JAWS scripts and laptop-layout tests follow.
5. **Stage 4, EdSharp, then FileDir,** each on its own, with new commands implemented before their keys are checked.
6. **Stage 5, HomerView.** The catalog, eligibility, verified session routing, per-browser JAWS script sets and the key alignment.
7. **Stage 6, documents, tutorials and packaging.**
8. **Stage 7, release** of each tested app, then one announcement.
9. **Later:** common frame inheritance, a combined installer, shared suite settings, round-trip edits between apps.

## Testing stage 1 on Windows

### The desktop proof

1. Run build_release in the kit, as usual. The build compiles the sample whenever it or the shared classes change, exports its keys without opening a window, and runs checkKeys; the build log has the results. Then start Templates\\samples\\FruitBasketMdiCs.exe.
2. Check each of these with JAWS, then with NVDA:
   - **Windows:** Control+N opens Basket 2. F4 lists both baskets, Shift+F4 says them, and Control+Tab moves between them.
   - **Typing:** in the Fruit field, type a word with capital letters; capitals and Shift+F type.
   - **The list:** Control+Shift+A adds fruit. In the basket list, typing the start of a fruit goes to it, Shift+F says the fruit, Shift+Y the count, and Shift+Q says it has no command.
   - **The alias:** Delete in the list deletes the fruit; Delete in the Fruit field deletes a character.
   - **Unavailable:** delete every fruit, then press Control+Shift+D; it says the basket is empty.
   - **Modal:** F2 renames the basket in a dialog, and the dialog's own keys work.
   - **Double press:** Alt+Delete says the position; press it twice quickly to review it in a window, and Escape returns.
   - **Again:** Control+J asks for a fruit, Alt+J and F3 go to the next match without asking, and the other basket has its own answer.
   - **Closing:** Control+F4 on a basket holding fruit asks first; choosing Keep open keeps it. Control+Shift+F4 says how many windows closed and how many were kept.
   - **Help:** Control+F1 makes keys describe themselves; Alt+F10 lists every command; Alt+Shift+E changes Basket Size at once.

### The browser-identity proof

1. Run build_release in HomerView, as usual. Its build now runs scripts\\testIdentity.py and stops if a case fails.
2. Under NVDA, with HomerView launched in Chrome, its page commands work there.
3. In an ordinary Chrome or Edge window, and before HomerView's browser is running, every key keeps its browser and screen reader meaning.

## Evidence so far

These results come from a Linux container with Python 3. No Windows build, installer or screen reader session was run.

- **The C# sources were not compiled.** Their braces and brackets balance, and they use no syntax newer than C# 5. The first Windows build is the real test.
- **checkKeys on the manifest reported:**
  - 5 shared keys needing review: EdSharp Control+I, Control+Shift+I and Control+L, and FileDir Backspace and Comma, each shared by context or listed twice;
  - 13 keys to test in their real control: the laptop-layout table keys and Control+Space;
  - 9 first-letter misses, such as FileDir's Play Media on Alt+Shift+L.
- **testIdentity:** 18 of 18 cases pass. Its first run found a real fault, Windows paths split wrongly on another system, which was fixed before delivery.
