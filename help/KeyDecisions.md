# Key Decisions of 19 October 2026

Jamal asked for every pending key decision to be settled by best judgment under Homer's rules, moving other keys where that gave a better whole, with each choice justified and each one easy to take back. This page is that record. The suite manifest, data\SuiteCommands.inix, carries the same decisions command by command, each with the key it replaced.

## The Rules Weighed

The rules that decided these cases, in the order they usually won:

- **A key never fights Windows or a screen reader.** The kit's data\KeyOwnership.inix says which keys belong to Windows, JAWS or NVDA, and a Homer app does not take them.
- **No command becomes menu-only.** A legacy key may be lost, but the command keeps some key (the 19 October ruling).
- **The same command has the same key in every app.** Where two apps share a command, one key serves both.
- **Families before letters.** When letters run out, a command joins the function-key family of its kind: F1 help, F2 edit and rename, F3 search, F6 panels, F11 windows and version, F12 the files and conversations the program opens for you.
- **A letter starts a word of the name.** Never a letter from the middle of a word.
- **Fewer keys beat strained keys.** Where one command can absorb another without losing anything, that is better than a key nobody could guess.

## The Decisions

### 1. Play Tutorials on Alt+F12

- **Problem.** Control+Shift+F1 is to be Hotkeys in all four apps, so Play Tutorials needed a new key.
- **Weighed.** Every F1 combination is taken, and Alt+Control with a function key belongs to Windows desktop shortcuts. P and T keys are taken in every app (Path to Clipboard, Text Combine, Play Stream and others), and moving them would break four apps to fix one command. The Homer Player key, Control+Shift+H, is Hard Line Break in EdSharp.
- **Chosen.** Alt+F12, free in DbDo, EdSharp, FileDir and HomerView. F12 holds what the program opens for you: the log (Control+F12), the speech log (Alt+Shift+F12), the AI chat (Shift+F12), and now the tutorials, which play in the Homer Player.
- **Rollback.** Give Play Tutorials Control+Shift+F1 again and take Hotkeys off it, one line each in EdSharp.cs.

### 2. Extra Speech Log on Alt+Shift+F12

- **Problem.** Export Format took Alt+Shift+X, X for export.
- **Chosen.** Alt+Shift+F12, beside Copy Log on Control+F12; free in every app, and proposed for FileDir too.
- **Rollback.** Alt+Shift+X, after moving Export Format back to Alt+Shift+E.

### 3. Rename on Shift+F2, Reverse Items on Alt+Shift+R

- **Problem.** Extra Speech Toggle is to take Alt+Shift+Z, since Z keys are toggles, which left Reverse Items with no key, and no R or I key was free.
- **Weighed.** Rename belongs in the F2 family, as FileDir's Rename is on F2. EdSharp's plain F2 has long been Special Character, and in an editor F2 carries no Windows meaning, so Rename takes Shift+F2 rather than unseating it.
- **Chosen.** Rename moves to Shift+F2, freeing Alt+Shift+R. Reverse Items takes it, which completes EdSharp's family of item commands on Alt+Shift with their first letter: Keep Unique (K), List Different (L), Number (N), Order (O), Query Common (Q) and now Reverse (R).
- **Rollback.** Rename to Alt+Shift+R and Reverse Items to Alt+Shift+Z; Extra Speech Toggle then returns to Control+Shift+X.

### 4. Extra Speech Toggle on Alt+Shift+Z

As DbDo and FileDir have it: Z for toggles. Control+Shift+X is now free.

### 5. Say Font Joins Say Styles

- **Problem.** Say Font's key, Alt+Dash, opens a document window's system menu, and KeyOwnership.inix says never to bind it in an MDI app.
- **Weighed.** The font commands are a family on the Dash key: Next Font (Control+Dash), Previous Font (Control+Shift+Dash), Set Selection Font (Alt+Shift+Dash). Its natural Say key is the forbidden one, and no free key in or near the family has any mnemonic tie to fonts. Overriding the rule was weighed and refused, since the rule protects a Windows feature every MDI app shares.
- **Chosen.** Say Styles (Alt+Slash) already says everything about how text looks except the font: its style, alignment and baseline. It now ends with the font and color, so nothing Say Font did is lost, and one key answers "how does this text look?"
- **Rollback.** Restore the Font item in the Query menu with its own key, and remove the font from Say Styles.

### 6. Toggle Indentation on JAWSKey+Shift+GraveAccent

- **Problem.** It was Windows+GraveAccent, and Windows keys belong to Windows.
- **Chosen.** It is a JAWS-only feature, set in EdSharp's JAWS key map, so it takes the JAWS key beside its sibling Toggle Punctuation (JAWSKey+GraveAccent). The GraveAccent key is EdSharp's speech family: voice rate and volume, punctuation, and now indentation.
- **To test.** That JAWS itself does nothing with Insert+Shift+GraveAccent on your setup.
- **Rollback.** One line in scripts\jaws\edsharp.jkm.

### 7. Go to Special Folder on Control+Shift+G, Go to Environment on Control+Shift+F12

- **Problem.** Go to Special Folder was Control+Shift+0, which Windows takes as a keyboard-layout hotkey on many machines with more than one language; the key works on some computers and silently does nothing on others.
- **Weighed.** FileDir has Go to Special Folder on Control+Shift+G, so the same key in both apps is the suite answer. In EdSharp that key was Go to Environment, the interactive console of the current language, such as Python's prompt with your file already run.
- **Chosen.** Go to Special Folder takes Control+Shift+G, as in FileDir. Go to Environment moves to Control+Shift+F12, beside Chat about Document on Shift+F12: a conversation with an interpreter beside a conversation with a model.
- **Rollback.** Swap the two lines back; Control+Shift+0 would return its old problem with it.

### 8. Math in Web Pages as MathML

- **Problem.** EdSharp's own Export passed Pandoc's MathML option for Markdown to web page. The kit's conversion did not.
- **Chosen.** The kit's Pandoc now writes MathML for every web page, in C# and Python. Screen readers read MathML as math, through MathCAT in NVDA and JAWS's own math support, while Pandoc's default leaves TeX source. A page without math is unchanged.
- **Rollback.** Remove the --mathml argument in Conversion.cs and conversion.py.

### 9. Word 2003 XML Export Stays Retired

The format was replaced by .docx in 2007, which EdSharp exports through Pandoc. Keeping it would mean a Word-only route for a format no current program needs.

- **Rollback.** Add xml back to EdSharp's Export choices and an officecom route, txt2xml, to conversions.inix.

## Decided Earlier the Same Day

- **Edit Settings File on Alt+Shift+F2.** F2 edits, and Alt+Shift pairs it with Edit Settings on Alt+Shift+E. It is proposed for FileDir too.
- **Search for Topic on Alt+F6.** Search for Topic Again is gone, because Search Next (F3) now repeats Search for Topic when that was the last search.
- **Tile Vertical on Shift+F11.** Control+Shift+F11 is a JAWS key. Shift+F11 is free in every app, beside Tile Horizontal (Alt+Shift+F11) and Cascade (Control+F11).

## How to Roll Back

Each decision is one or two lines in the app's source, named in the comment beside EdSharp's Help menu with the key it replaced. The manifest's change line says what each key was, and git keeps every earlier version. To take a decision back, restore those lines and the manifest entry, then build.

### Where Am I on Alt+Shift+Slash (3 November 2026)

- **Problem.** A key to sum up where you are, the same in every Homer app and every dialog, with a question or help mnemonic.
- **Considered.** The F1 family: Alt+F1 About, Control+F1 Key Describer, Control+Shift+F1 Hotkeys and Alt+Shift+F1 ReadMe hold every variation in main windows. Q: Alt+Shift+Q is DbDo's Query History and Alt+Q HomerView's lookup. Slash: Alt+Slash is EdSharp's Say Styles.
- **Chosen.** Alt+Shift+Slash, Alt and the question mark: free in every app, in JAWS, NVDA and Windows by the kit's key ownership data, and never typed by accident in a text box. Pressed once, twice and three times, as Shift+F1 now is.
- **Rollback.** Remove the Alt+Shift+Slash branch from Lbc's wireUniversalKeys and set DbDo's Where Am I back to no key.

### The help keys of every main window (7 November 2026)

- **Problem.** Shift+F1 meant two things. In a dialog, and in DbDo's main window, it says what the focused control does; in EdSharp's and FileDir's main windows and the kit's frame, it opened History of Changes. Alt+Shift+Slash, Where Am I, was not in fact free in every app: EdSharp's Style dialog had it, and FileDir's main window had no Where Am I. DbDo's History of Changes had no key at all. Both Claude's and ChatGPT's audits of 7 November found this.
- **Considered.** Keeping Shift+F1 for History in main windows only, which would teach one key two meanings. Giving History a letter key: Alt+Shift+H is Hotkey Summary, and every other F1 variation was taken. Merging Hotkey Summary into the Hotkeys document by a second press: the first press opens a window, so a second press never reaches the frame.
- **Chosen.**
  - Shift+F1 is What This Does in every main window, as in every dialog.
  - Alt+Shift+Slash is Where Am I in every main window.
  - History of Changes takes Control+Shift+F1, in every app.
  - The Hotkeys document gives that key up and stays in the Help menu. Alt+Shift+H, Hotkey Summary, lists the same commands and keys, live from the program, so the document was the duplicate (the 5 November rule: duplicative bindings are merged, keeping the best key). FileDir's Alt+Shift+H had been opening that same document, so it now shows the window, as DbDo's and EdSharp's do.
  - EdSharp's Style dialog moves to Alt+Slash pressed twice: Alt+Slash, Say Styles, says the styles, and a second press opens the dialog to change them, so the dialog keeps a key and joins the command it belongs with.
- **Rollback.** Kit: the What This Does, Where Am I, History and Hotkeys lines in Mdi.cs's Help menu. Apps: the Help-menu lines marked 7 November 2026 in DbDo.cs, EdSharp.cs and FileDir.cs, and their Hotkeys files. Rollback.zip of that date holds every file before the change.

### Three help keys, and two presses at most (9 November 2026)

- **Problem.** Jamal found the help keys overlapping: Alt+Shift+H and Control+Slash both opened Hotkey Summary, Alt+Shift+Slash's third press also spoke the keys, and a second press meant "more", "something else" or "spell" depending on the window. He saw Control+Slash as a friendlier Alt+Shift+Slash. In a dialog, Alt+Shift+H would also press the Help button, because Windows matches an access letter whether or not Shift is down.
- **Chosen.** Three keys, one question each: Shift+F1, what is this; Control+Slash, where am I and what can I do; Control+F1, what does this key do. The first press of Shift+F1 or Control+Slash reads everything -- Control stops speech -- and a second press shows the same in a read-only window; there is no third press. A command that says one short value keeps the screen readers' habit: a second press spells it. Control+Slash replaces Alt+Shift+Slash in every main window and Lbc dialog; its window in a main window ends with every command and key, so Hotkey Summary keeps only its menu item, and Alt+Shift+H is free.
- **JAWS and NVDA.** JAWS's Insert+H, Hot Key Help, has nothing to say about an app Freedom Scientific does not script, so each Homer app's JAWS scripts answer it by pressing Control+Slash twice. Insert+W, Windows Keys Help, and Insert+F1 stay JAWS's own. NVDA has no hot key help; Control+Slash serves its users.
- **HomerView.** Web pages own Control+Slash in Edge, so HomerView keeps Alt+Shift+Slash for Where Am I, its one exception.
- **Rollback.** Lbc.cs (allLevels, answer, pressCount and the three key handlers), Mdi.cs's Where Am I and Hotkey Summary lines, and the lines marked 9 November 2026 in DbDo.cs, EdSharp.cs, FileDir.cs and their JAWS scripts; Rollback.zip of that date holds every file before the change.

### Control+P plays media (9 November 2026)

- **Chosen.** Play Stream in DbDo and Play Media in FileDir take Control+P, as in Windows Media Player, the Windows 11 Media Player and Movies and TV; VLC and Spotify use it for preferences and browsers to print, and few people print now. Print keeps no key: on EdSharp's and FileDir's Misc menus, and hidden in DbDo until it prints. DbDo's Alt+Shift+P and FileDir's Alt+Shift+L are free. HomerView is unchanged: Control+P prints the page in Edge.

### Control+Slash lists the keys (8 November 2026; superseded 9 November 2026)

- **Problem.** Jamal asked whether Homer should follow the key that web apps use to list their shortcuts.
- **Found.** The slash and question-mark key is the de facto convention. Control+Slash lists the shortcuts in Google Docs and Drive, Slack, ChatGPT, Claude Docs, Discord and on Chromebooks; the question mark alone does so in Gmail, Outlook and GitHub, apps whose shortcuts are single keys; Teams uses Control+Period and Figma Control+Shift+Slash.
- **Chosen.** Control+Slash becomes a second key for Hotkey Summary in the kit's frame, DbDo, EdSharp and FileDir. Alt+Shift+H stays, matching JAWS+H. The bare question mark is not used: FileDir's question mark is Say What Content, and in lists and text boxes it must type.
- **Moved to make room.** Open Command Prompt keeps Control+Backslash only, in DbDo and FileDir, as in EdSharp. EdSharp's Next Style and Previous Style move from Control+Slash and Control+Shift+Slash to Alt+Period and Alt+Comma, a next-and-previous pair free in EdSharp.
- **Not in HomerView.** HomerView runs inside Edge, where a web app's own Control+Slash -- Google Docs's, Slack's, ChatGPT's -- must reach the page, by the rule never to break the host program's keys. HomerView keeps Alt+Shift+H.
- **Rollback.** The Hotkey Summary line in Mdi.cs; the lines marked 8 November 2026 in DbDo.cs, EdSharp.cs and FileDir.cs; their key files. Rollback.zip of that date holds every file before the change.

## Key Describer rules (5 November 2026)

Jamal asked that Alt+F4 also turn the Key Describer off, for someone who turned it on by accident and does not know Control+F1, with a second Alt+F4 closing the app, and that this be the rule in every app. With it came what DbDo's describer had taught: describe every key even when its command cannot run, giving the true reason after the description; never guess a reason; ignore the nameless key a screen reader sends; and describe from the app's own command table. HomerSuite.md states the rules; the kit's KeyMap carries them out.

## Rulings since 19 October, to confirm (15 November 2026)

The keyboard audit of 15 November, by Claude and ChatGPT, found several of Jamal's rulings recorded nowhere in the kit, so an audit could not cite them. They are gathered here so the kit is the record.

**These are summaries, not quotations.** Each comes from Claude's notes of a conversation, with the date the ruling was given. Jamal confirms or corrects each one once. A confirmed line is marked *confirmed*, and a corrected one is rewritten in his words. Until then, each line is cited as "summary, to confirm," and no audit may treat it as his exact words.

- **18 October, settings.** Editing configuration settings is an Edit command on the same E key in every app: Alt+Shift+E. Alt+E opens the Edit menu. *Summary, to confirm.*
- **18 October, window cycles.** Control+Tab and Control+F6 must not duplicate each other. Each is next-in-cycle at a different level or in a different way. *Summary, to confirm.*
- **19 October, Page keys.** Control+PageUp and Control+PageDown must not duplicate Control+Tab or an F6-family command. They have a unique purpose, or none. *Summary, to confirm.*
- **19 October, habits as preferences.** Alt+C for appending is not universal, since FileDir uses Shift+A. Such habits are preferences, balanced to an optimum under constraints. *Summary, to confirm.* The audit later found that FileDir's Shift+A appends file contents, a different command from Copy Append on Alt+C.
- **19 October, one name, one code.** A command with the same name, key and description in several apps runs the same HomerDev code. *Summary, to confirm.*
- **19 October, no lost functionality.** A legacy key may be lost, but functionality must not be. A command made menu-only counts as lost functionality, so it keeps some key. This is already in The Rules Weighed, above.
- **5 November, distinct roles.** Every command plays a distinct role. Duplicate commands and bindings are dropped or merged, keeping the best mnemonic name and key. *Summary, to confirm.*
- **7 November, descriptions.** Every command description is one succinct sentence, parallel with its siblings, that reinforces why its key was chosen. *Summary, to confirm.*
- **9 November, help and media keys.** These are recorded in this page's 9 November sections:
  - Control+P plays media, and Print may be unbound.
  - Help keys are fewer and do not overlap.
  - Control+Slash is Where Am I, with Alt+Shift+Slash in HomerView.
  - A help key's first press reads everything.
- **10 November, the suite.** DbDo, EdSharp, FileDir and HomerView are the Homer Suite. The same command has the same name, description and key in each. Script, not snippet. A command bound to a function key or other non-letter key carries no menu letter. There are no speech-tweak commands, so their keys are free, among them Alt+Shift+F12, once the Extra Speech Log. *Summary, to confirm.*
- **Say Status.** Claude's notes give Shift+Z as Say Status ("Z is the bottom of the alphabet, like the status bar"). The source shows Alt+Z as the route DbDo, EdSharp and FileDir share, with DbDo also on Shift+Z. *Summary, to confirm;* question 5 of the audit's decisions asks which is primary.

## Keyless commands, by exception (15 November 2026)

The rule above is that no command becomes menu-only. These live commands have no key by a recorded decision. Any other keyless live command is reported to Jamal for a decision, not given a key just to make a count pass.

- **Print.** Unbound by the 9 November ruling that Control+P plays media.
- **Hotkey Summary and the Hotkeys document.** Unbound by the 9 November ruling for fewer, non-overlapping help keys. The Alternate Menu (Alt+F10) reaches both.
- **Help documents other than the guide, History, ReadMe and Tutorials.** By the 10 November ruling: one Help menu item per document, with keys only for the most important.
- **FileDir's Timer.** Its Alt+Control+Y went on 15 November, because Alt+Control is for Windows desktop shortcuts. Say Status (Alt+Z) now says the timer, so the time is still one key away, and Timer keeps its menu item for anyone who looks for it by name.
- **HomerView's Hotkey Summary keeps Alt+Shift+H.** It is the one app where Hotkey Summary has a key. See question 7 below.
- **Planned commands.** A planned command is not live. It holds no key until it works. DbDo's Pick Value was such a stub on Control+F2; on 15 November it was built instead, because Tutorial 4 teaches it.

Each new exception is added here with its command, app, reason, ruling and date, and its other route.

## The ten decisions, taken under the standing rule (15 November 2026)

Jamal's rule of 19 October says to decide a pending question by best judgment, justify it, and keep a rollback, rather than wait. Claude put ten questions to him on 15 November and, with no answer yet, decided them as below. Each can be reversed by answering its question; the rollback zip of that day restores every file. Two answers differ from Claude's first recommendation, because checking the keys showed something the static scan had missed.

1. **Record Macro: Control+Shift+F9.** No Homer app, Windows or screen reader claims it. EdSharp keeps Go to Environment on Control+Shift+F12. The F9 family is the readable view, so the key is learned rather than guessed.
2. **Play Macro: Alt+Shift+F12,** beside Play Tutorials on Alt+F12, so "Alt with F12 plays."
3. **Timer Toggle: Alt+Shift+Z.** Z keys are toggles. FileDir's Start Timer already started, paused and resumed, so it is named for what it does.
4. **Stop Timer: Alt+F2.** *Changed from the first recommendation.* Control+Shift+F11 is JAWS's system tray (data\KeyOwnership.inix says never bind it), and checkKeys would have caught it. Alt+F2 is claimed by no Homer app, Windows or screen reader. Control+Shift+F10 was passed over, being next to Shift+F10, the context menu.
5. **Say Status: Shift+Z first in DbDo, Alt+Z second.** No key moves. Alt+Z is the key all three MDI apps share.
6. **Invert Marked: FileDir keeps Control+I, as a permanent recorded exception.** *Changed from the first recommendation.* Moving it to Alt+Shift+I needs a new key for Inquire Differences, and FileDir has every I and D key taken: Shift, Alt, Control, Alt+Shift and Control+Shift, with each letter. DbDo cannot move to Control+I either, since that is its Inspect Record.
7. **HomerView's Hotkey Summary keeps Alt+Shift+H, as a recorded exception.** The audit's A16 would have retired it, but Jamal's 8 November ruling approved Alt+Shift+H for Hotkey Summary, beside JAWS's own Hot Key Help on JAWS+H. His 9 November concern, that Alt+Shift+H fails in a dialog, does not arise in a web page. HomerView also has no menu bar; Alt+Shift+H is how its guide, Developer notes and three tutorials confirm which build is loaded, from the summary's first line. The other three apps leave Hotkey Summary unbound, as before.
8. **HomerView's Z keys stay a browse-mode family,** a recorded exception: next and previous of the same kind and of a different kind, on keys NVDA leaves free.
9. **The rulings summaries above stay labeled "Summary, to confirm."** Only Jamal can confirm his own words.
10. **The agreed renames wait for Phase 1,** when the command record keeps old names searchable. Timer Toggle is the one rename made now, because the timer change (A15) names it.

## One Edit Settings (15 November 2026, the keyboard audit's A4)

Edit Settings (Alt+Shift+E) is the one entry to an app's settings. In EdSharp and FileDir it is the kit's LbcAsk.settingsDialog: the fields, then a button for each settings file, left of OK, so Enter still saves the fields. Edit Settings File (Alt+Shift+F2) is retired, as A4 allowed once one entry offered the fields, the raw file and EdSharp's compiler file. DbDo's Edit Settings already offers its file among its buttons, and HomerView's opens its file. Alt+Shift+F2 is free in every Homer app.

