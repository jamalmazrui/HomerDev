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
