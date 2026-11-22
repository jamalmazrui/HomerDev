# Key Decisions of 19 October 2026

Jamal asked for every pending key decision to be settled by best judgment under Homer's rules, moving other keys where that gave a better whole, with each choice justified and each one easy to take back. This page is that record. The suite manifest, data\SuiteCommands.inix, carries the same decisions command by command, each with the key it replaced.

## The Rules Weighed

Above every rule stands the suite's promise: a comprehensive, consistent and coherent keyboard interface, whether you are creating documents with EdSharp, navigating folders with FileDir, managing data with DbDo or viewing content with HomerView. Each decision below is judged by all four apps, not one.

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

## Fewer commands, and Marked or Current (17 November 2026)

Jamal asked to drop or combine commands that were new twenty years ago and now only add noise, and to give FileDir and DbDo one way to choose between the marked items and the current one. Each choice is in data\SuiteCommands.inix with the key it replaced; the rollback zip of the day restores every file.

- **Retired:**
  - Say Time, in all four apps. JAWS and NVDA say the time with Insert+F12, and twice for the date, in every program, so Homer's Alt+Semicolon only repeated them.
  - FileDir's Batch Mail. It signed in to your mail server with a saved password and sent many messages, which mail providers now refuse or mark as spam. A mail program's own mail merge does the job.
  - FileDir's Shift+letter and Shift+punctuation aliases that acted or repeated another key: Shift+Period and Shift+Comma (Shift+DownArrow and Control+Shift+DownArrow mark and unmark), Shift+B, Shift+E, Shift+N and Shift+P (Control+Shift+Home and End, Control+DownArrow and UpArrow). Every Shift key in FileDir now says something, or moves as Shift+DownArrow, Shift+Backslash and Shift+Space do.
- **Keyless, on their menus:** Initial Change, Extension Change, Stamp with Date and Time, Hide, Show, System, General, Short Path to Clipboard and Say Yield in Operating System. They act rarely, or Windows says the same, and their shifted keys broke the rule that a shifted key only says.
- **Combined:** DbDo's Say Database (Shift+D) now says the database and then its summary, and a second press shows it all in a read-only box, so Database Summary is gone and Alt+D is free.
- **Moved, so the pairs read alike in every app:**
  - Import Data: DbDo's Alt+I to Control+Shift+I; Export Data, EdSharp's Export Format and FileDir's Export Type: Alt+Shift+X to Control+Shift+X. I and X, in and out, on the same modifiers, beside Control+Shift+E (Extract with Regex), Control+Shift+R (Replace with Regex) and Control+Shift+Y (Yield with Regex).
  - Open Template Database: Alt+Shift+D to Alt+D, the simpler key for the friendlier command.
  - Inspect Record: Control+I to Alt+I; Invert Marked: Alt+Shift+I to Control+I, as in FileDir.
  - FileDir's Say Yield on Drive: Control+Shift+Y to Alt+Shift+Y, so Control+Shift+Y can be Yield with Regex, new in FileDir, as in EdSharp and HomerView.
- **Marked or Current.** When a FileDir or DbDo command can act on many items and some are marked in view, a small dialog titled with the command asks: Marked items (with the number), the default, so Enter keeps the batch; Current item; Cancel; and Help. Alt+M and Alt+C, or M and C, choose; Shift+F1 says what each button does, and Control+Slash says where you are. It is not asked when nothing is marked, or when the one marked item is the current one. (The first version also stayed silent whenever the current item was marked; Jamal pressed Control+Z with marked folders and heard no question, so since the evening of 17 November it asks.)
- **Kept, and why:**
  - Control+Shift+F3 stays Reverse Find with Regex, since Shift reverses through the F3 family in every app; Control+F3 is Forward Find with Regex.
  - Shift+V stays Say Invoke Script, beside Alt+V; Shift+W stays Say Whole Record, W for whole.
  - The names keep "with Regex" rather than "with Pattern", the word every Homer app and guide already uses.
  - Edit Settings is Alt+Shift+E in all four apps already.

## The keymap work finished (17 November 2026)

Jamal asked to complete the Homer keymap work. Nothing in data\SuiteCommands.inix is now proposed.

- **Built earlier, recorded now:** 13 HomerView renames and key moves (Copy Log, Developer Notes, Check with Equal Access, the four Previous commands, ReadMe, Say url, Search Next and Search Previous, Hotkeys, Key Describer Toggle).
- **Built now:**
  - HomerView: Forward Find with Regex, Reverse Find with Regex, Yield with Regex (EdSharp's names), Choose Active Browsers in the command table, Open Saved Page in EdSharp, Show Page Folder in FileDir.
  - EdSharp: Say Position (Alt+Delete), Show in FileDir (Control+Shift+Backslash).
- **Two judgments, recorded so they can be argued with:**
  - EdSharp keeps Say Address (Alt+A) beside Say Position (Alt+Delete). They overlap, but Say Address gives pages when HardPageAddress is on and has been EdSharp's key for years, while Say Position is the suite's command, word for word as in DbDo, FileDir and HomerView, and counts lines in the text rather than wrapped screen lines. Merging them would take Alt+A's page mode or the suite's sentence away.
  - EdSharp's Show in FileDir takes DbDo's Control+Shift+Backslash rather than staying menu-only, since the suite rule is one name, one key; it completes the Backslash family there too (Alt: Explorer, Control: command prompt).
- **Found on the way:** 58 of DbDo's command lines sat inside the tsv connection string's backtick fence, so no check saw them and DbDo never loaded their descriptions; they are back in [Hotkeys].

## Shift+letter only says or moves: FileDir (16 November 2026)

Jamal asked for a new phase: FileDir should use Shift+letter keys as DbDo does, to say information and never to act. His own ideas were Control+Shift+C for Copy to Folder and Control+Shift+M for Move to Folder, with displaced commands moved or, when hardly relevant, left on a menu with no key. Claude proposed a map, Jamal said go, and every choice below is recorded in data\SuiteCommands.inix with the key it replaced. The rollback zip of that day restores every file.

**The rule.** A Shift+letter never changes anything on disk, the clipboard or settings. It says something, or it moves focus. A Shift+letter pressed by mistake then costs nothing. Shift+B, Shift+E, Shift+I, Shift+N, Shift+P and Shift+X move, so they stay.

**Moved,** alphabetically:

- **Append File Contents:** Shift+A to Alt+Shift+C, beside Copy Append on Alt+C: the items' text beside the items.
- **Convert Units:** Shift+3 to Control+3, beside Convert Encoding on Control+2.
- **Copy Name:** Control+Shift+C to Alt+Shift+N, N for Name, beside Path to Clipboard on Alt+Shift+P.
- **Copy to Folder:** Shift+C to Control+Shift+C, Jamal's choice.
- **Export Type,** renamed from Output Type: Shift+O to Alt+Shift+X. X for export is the suite's export key, as DbDo's Export Data and EdSharp's Export Format; the rename lets the key's letter come from the name. The Alternate Menu finds it as "Formerly Output Type."
- **Move to Folder:** Shift+M to Alt+Shift+M. *Changed from Jamal's first idea.* Control+Shift+M is the suite's Mail Attachment, which EdSharp shares, and EdSharp's Alt+Shift+M is Manual Options, so Mail Attachment could not move in both apps. M for Move keeps the letter.
- **Quick Shortcut:** Shift+Q to Control+Shift+Q, beside Open Quick Folder (Control+Q) and Quick url (Alt+Shift+Q).
- **Rename:** loses Shift+R and keeps F2 and Shift+F2.
- **Unarchive:** Shift+U to Control+U, the fewest modifiers for a command used daily. Unarchive without Subfolders moves from Control+U to Alt+U.
- **Zip:** Shift+Z to Control+Shift+Z, beside Zip then Delete on Control+Z. Zip List moves from Control+Shift+Z to Alt+Shift+L, L for List.

**Left on the menu with no key:** Folder to Clipboard (Backspace, then Control+C, copies the same folder or archive), FTP Put and Get FTP (FTP is rarely used now), Network Connections (Windows maps drives itself), and Unarchive Test (rarely needed). Jamal allowed this for commands hardly relevant now, which narrows his 19 October principle that a menu-only command counts as lost.

**New say commands,** on the freed letters, as in DbDo: Say Filter (Shift+F), Say Marked (Shift+M) and Say Order (Shift+O). Say Status gains Shift+Z beside Alt+Z, as in DbDo. Shift+A, C, G, Q, R, U and 3 stay free for future say commands.

## One Edit Settings (15 November 2026, the keyboard audit's A4)

Edit Settings (Alt+Shift+E) is the one entry to an app's settings. In EdSharp and FileDir it is the kit's LbcAsk.settingsDialog: the fields, then a button for each settings file, left of OK, so Enter still saves the fields. Edit Settings File (Alt+Shift+F2) is retired, as A4 allowed once one entry offered the fields, the raw file and EdSharp's compiler file. DbDo's Edit Settings already offers its file among its buttons, and HomerView's opens its file. Alt+Shift+F2 is free in every Homer app.

## Evaluate Expression keeps three effects, each named (15 November 2026, the keyboard audit's A8)

The audit offered two ways: one way of presenting the result, with Insert Result and Copy Result as separate commands; or, if that waits, an accurate sentence naming each app's effect. The second is chosen. Copy Result would need one key in DbDo, EdSharp and FileDir, and no C or R key is free in all three: Control+C, Alt+C and Control+Shift+C copy other things in each, and the Equals keys are taken in EdSharp. Splitting the command would also add a keystroke to every use, in the app where it is used most. So Control+Equals evaluates in each app and does the one thing that app is for -- EdSharp inserts the result below the line, FileDir copies it to the clipboard, DbDo says it -- and the catalog's sentence names that effect.

## What each app binds, compared with what it shows (15 November 2026, Phase 1)

DbDo, EdSharp and FileDir answer "/exportkeys <file>" with every command and key they declare, through the kit's KeyMap. check's exported keys step compares that file with the app's key file at every push. It warns for now, and becomes a failure once its first findings are settled. This is the first part of the command record (A1): the program's own declarations are now what the gates read.

## The key comparison blocks a push (15 November 2026, A2)

Since HomerDev 1.240.0, a push stops when the keys DbDo, EdSharp or FileDir binds differ from the keys its key file shows. Keys an app handles outside the kit's router are named in the catalog's [handled <App>] sections, each with where it is handled; adding a line there is a decision, recorded with its reason, not a way round the check.

## The agreed names, and how old names stay findable (15 November 2026, A5 and A11)

- **DbDo:** Copy Append (Alt+C, was Append Cell), Copy Append Record (Alt+Shift+C, was Append Record), Toggle Mark (Control+Space, was Marked Toggle), Say Marked Records (Shift+Space, was Say Records of Marked), Say Marked Records from Current (Alt+Shift+M, was Say Records from Current Marked).
- **FileDir:** Say List, Say List Marked, Say List Files, Say Yield, Say Yield Marked, Say Yield Files, Say Yield on Drive, Say Yield in Operating System, Say Character Encoding, Show Type Extended, and Append File Contents (Shift+A, was Append to Clipboard).
- **One key moved.** FileDir's Say Yield takes Alt+Y, the suite's key, and Say Yield Files takes Control+Y, where Yield was. Jamal's 9 November ruling described Alt+Y as the yield of everything "as in FileDir"; now it is, in every app.
- **Findable.** Each app names a renamed command's former name to the kit's KeyMap, and the Alternate Menu ends its line with "Formerly <name>.".
- **Retired.** FileDir's Timer, since Say Status says the timer (A15).

## The command record, as built (15 November 2026, A1)

An app's key file is the one authored record of its commands: name, keys and sentence. Every surface is made from it or checked against it at every push -- FileDir's Hotkeys page and built-in table by its makeKeyMap, EdSharp's Hotkeys page by the kit's makeHotkeys, DbDo's Hotkeys page from its menus, HomerView's key file and page from its command table. The catalog records what the suite shares, and /exportkeys proves the program binds what the record shows. SuiteCommands.inix is kept, not retired: it is the record of each key's history -- every change with its date and reason -- and checkKeys' ownership data, and that is the home A1 asked its history to have.

## Alt says, Control changes (21 November 2026)

Jamal asked to fine-tune the suite's keys by a preference he named: when a letter needs a modifier, which one, Alt or Control? He asked for his instincts to be weighed among the other rules, not to outrank them, and for optimization, not perfection. This section records the factors, the review of DbDo, EdSharp, FileDir and HomerView against them, and what changed in two rounds the same evening. Every change is in data\SuiteCommands.inix with the key it replaced, and the rollback zip of the day restores every file.

### The factors

- **Data:** a command that changes data -- records, files on disk, the text of a document, settings -- prefers Control to Alt.
- **Groups:** a key that belongs to a group with its own pattern keeps the group's pattern. Extract, Replace and Yield with Regex on Control+Shift+E, R and Y are such a group, and Jamal likes it.
- **Pick lists:** a command that mainly offers a list to pick from may take Alt or Control equally.
- **Speech:** a command that only says something prefers Alt to Control. Shift and a letter stays the first place for a one-fact Say command, as in DbDo and FileDir.
- **Suite:** DbDo and FileDir, the two list apps, have the same commands on the same keys, even where that means relearning, since a new user expects it of a suite.
- **Typing:** a plain Alt and a letter, with no Shift, should not open a box for typing whatever you like.

These sit beside the older rules: never fight Windows or a screen reader, one command one key across the suite, a letter starts a word of the name, families before letters, and no command loses its key without a reason. "Data" here does not include the clipboard: Copy Append (Alt+C), Cut Append (Alt+X) and the other clipboard commands keep their long-standing keys.

### Wide, lean and yield in DbDo and FileDir

Jamal's design, adjusted in the second round. W is wide, the grid's width: every shown column of a record. L is lean, one column: DbDo's current column, FileDir's item names. W and L are the widest and narrowest letters of the alphabet, which helps them stick. Y is yield, a count.

- **Alt** starts from the first record or item; **Alt+Shift** keeps only the marked ones; **Control** starts from the current one.
- **Read Wide** (Alt+W), Read Wide Marked (Alt+Shift+W, and Shift+Space as before) and Read Wide from Current (Control+W) are DbDo's former Read List commands, which were on L. FileDir has no W keys, since its list has one column, and Alt+W stays free there.
- **Read Lean** (Alt+L), Read Lean Marked (Alt+Shift+L) and Read Lean from Current (Control+L) are in both apps. In DbDo they were the Say Column as List commands, with no keys; in FileDir, Say List (Control+L) and Say List Marked (Shift+L). Both apps now read one value or name at a time, through the kit's ReadAloud, and a second press shows them in a window.
- **Say Yield** (Alt+Y), **Say Yield Marked** (Alt+Shift+Y, was Shift+Y) and **Say Yield from Current** (Control+Y, new) are in both apps. Shift+Y is free in DbDo; in FileDir it now says the yield on the drive.
- **The fourth form, marked from the current one on, has no key** in any of the three families, in either app. The first round gave it Control+Shift, but Control+Shift+Y is Yield with Regex in every suite app, and FileDir's Control+Shift+L is Play List, which its tutorial 5 teaches. Leaving Control+Shift off all three keeps the families alike, keeps the regex group whole, and leaves Control+Shift with a letter for commands that change things. The three commands are on the menus and in the Alternate Menu.
- **DbDo gains Yield with Regex** on Control+Shift+Y. It asks what Extract with Regex asks and says how many matches there are, in how many records, so DbDo's regex group is now E, R and Y, as in EdSharp, FileDir and HomerView.
- **FileDir lets three keys go:** Say List Files (was Alt+L) and Say Yield Files (was Control+Y) keep no key, since marking the files with Alt+Period and pressing Alt+Shift+L or Alt+Shift+Y gives the same answer; Zip List (was Alt+Shift+L) is rarely wanted.
- **Old names find the new commands** in the Alternate Menu, as "Formerly Say List" and the like.

### No Window menu

Jamal's ruling, so Alt+W is free in DbDo. The menu goes in every MDI app and in the kit's frame, since a menu the suite shares should look the same everywhere.

- **DbDo:** Current Windows, Next Window, Previous Window, Window Toggle, Say Windows Open, Close Window and Close All But Current Window move to the File menu, before Exit DbDo. Open Table moves beside Choose Table.
- **EdSharp:** Next Window and Previous Window join Current Windows on the File menu; Arrange Icons, Cascade, Tile Horizontal and Tile Vertical go just before Exit EdSharp.
- **FileDir:** the four layout commands go just before Exit FileDir; Drive A through Drive I (Alt+1 to Alt+9) follow Open Drive and Go to Drive.
- **The kit's frame (Mdi.cs):** its window commands join the app's File menu, and the app's Exit item is moved after them.
- **No keys changed.** Each of these commands has a function key, Tab or a digit, so none takes a trigger letter. With no Window menu, Windows' own list of open windows is gone too; F4, Current Windows, lists them.

### Mail: one command

Jamal asked whether both Mail Body and Mail Attachment were needed. No: FileDir's Mail Attachment already put a lone file's text in the body as well as attaching it.

- **Mail, Control+M,** in EdSharp and FileDir. EdSharp puts the text in the body and attaches the file when it is saved on disk. FileDir attaches the current item or the marked ones, and a lone file's text goes in the body too.
- **Control+Shift+M is free,** in both apps.

### Other moves, by the factors

- **EdSharp, Insert Time:** Alt+Shift+Semicolon to Control+Semicolon. It changes the text, and Control+Semicolon inserts the date in Excel.
- **EdSharp, Text Contents and Text Combine swap:** Text Contents, which adds a table of contents to the document, takes Control+Shift+T; Text Combine, which makes a new window, takes Alt+Shift+T.
- **FileDir, Move to Folder:** Alt+Shift+M to Control+Shift+M, beside Copy to Folder on Control+Shift+C. This was Jamal's first choice on 16 November; Mail Attachment held the key then.
- **FileDir, Paste Copy:** Alt+V to no key, on the Edit menu. After Copy, Paste already copies. Alt+V is now free in FileDir, so it no longer contradicts "Alt+V runs a script" in the rest of the suite.
- **FileDir, Paste Move:** Alt+Shift+V to Control+Shift+V, beside Paste on Control+V.
- **FileDir, Reorder Names:** Alt+Shift+K to Control+F2. It renames, so it joins the F2 family on Control; K began no word of its name.
- **FileDir, Say Yield on Drive:** Alt+Shift+Y to Shift+Y. A Shift+letter only says.
- **FileDir, Volume Format:** Control+Shift+V to no key, on the Misc menu. Formatting a disk is rare and cannot be undone.

### Kept, and why

These break one of the factors and keep their keys, because another weighs more. Each can be argued with.

- **Clipboard commands on Alt:** Copy Append (Alt+C), Cut Append (Alt+X), Copy Append Record and Append File Contents (Alt+Shift+C), Copy Name (Alt+Shift+N), Path to Clipboard (Alt+Shift+P) and Clear Clipboard (Alt+Shift+Apostrophe). The clipboard is not counted as data, and Alt+C for append is Jamal's long-standing convention.
- **DbDo, Edit Notes, Edit Tags and Edit url (Alt+Shift+N, T and U):** they change data, but they are one family beside Say Notes, Say Tags and Say url on Shift, and Control+Shift+N is New Copy in every app. Moving two of the three would split the family.
- **DbDo, Merge Data (Alt+M):** it adds records, but both Control M keys mark and unmark, which change data too and are used far more.
- **DbDo and FileDir, reading on Control:** Control+W, Control+L and Control+Y only speak. Their family's pattern gives Control the meaning "from the current one", as Control+Home and Control+End mean the ends, and the everyday form is on Alt.
- **EdSharp, case and item families:** Proper Case (Alt+U) and Swap Case (Alt+Shift+U) beside Upper and Lower Case on Control; Order, Reverse, Keep Unique and Number Items on Alt+Shift. Each family needs more keys than Control can give its letter.
- **EdSharp, Delete Line, Delete Up, Delete Down and Delete File (Alt+Backspace, Alt+Shift+Backspace, Alt+Shift+Delete, Alt+Shift+D):** the Control delete keys are taken by their siblings and by Windows' delete-word habit.
- **EdSharp, formatting on Alt+Shift:** Justify, Baseline, Set Selection Font, Set Default Font and Color, Align, PyDent and PyBrace. Their next-and-previous partners use Control, so each pair already splits the modifiers by role.
- **EdSharp, Save Script (Alt+S) and Save Copy (Alt+Shift+S):** Save Script asks for a name, which the typing factor dislikes on a plain Alt key. It stays beside Invoke Script (Alt+V) and View Script (Alt+Shift+V), the script family every app shares; Control+S and Control+Shift+S are Save and Save As.
- **EdSharp, Yield Encoding (Alt+Shift+Y), Transform Files (Alt+Equals) and Reset Configuration (Alt+Shift+0):** each changes data on Alt; the Control key of its letter or symbol is taken by a sibling, and Control+Shift+0 belongs to Windows' keyboard layouts.
- **Every app, Edit Settings (Alt+Shift+E):** Jamal's ruling of 18 October gives it the same key everywhere.
- **Every app, Evaluate Expression (Control+Equals):** in DbDo it only says the result, but it is one suite command on one key.
- **Every app with it, Yield with Regex (Control+Shift+Y):** it only says a count, but it is the regex group's Y.
- **FileDir, Unarchive without Subfolders (Alt+U):** it completes a family whose Control keys are taken.
- **FileDir and EdSharp, Web Download (Alt+Shift+W) and Burn to CD (Alt+Shift+B):** suite commands that write files, kept on one key in each app.
- **HomerView, Instruct Page (Alt+I) and Query Web (Alt+Q):** each opens a box for typing on a plain Alt key. Edge and web pages own most Control letters, so HomerView's choices are narrow.

### Key groups, the third round

The same evening Jamal asked for every key pattern group to be named, counted and audited. help\KeyGroups.md is that record: 51 groups (52 after the fourth round added the space bar), from "again" to "z keys", each with what its members should share, what was found and what was done, and counts that scripts\keyGroups writes from the key files. Its fixes: DbDo and FileDir now share their marking, search and Again keys and names (Mark to First and Last, First and Last Marked, Start Mark or Unmark, Reverse Jump, Jump Again, Keywords Again, New Copy); Alt+F8 reads all and Control+F8 copies all in DbDo, as in EdSharp and HomerView; Edit Script is Alt+Shift+V in DbDo and EdSharp; and small words stay small in command names (Close All but Current Window).

### Play, record, Space, statistics and graphics, the fourth round

Jamal asked for one way to play and one to record, a Space bar scheme, and a new look at DbDo's statistics and charts.

- **Play Media, Control+P, plays in the Homer Player in DbDo and FileDir.** FileDir's handed its list to mpv's own window, and it had two more ways to play: Homer Player (Control+Shift+H) and Play List (Control+Shift+L). Homer Player is retired into Play Media, which now finds the marked files, a play list or a document with media links, the clipboard, or the folder. Play List keeps no key; it is on the Misc menu for keeping a list or starting something and walking away.
- **Record Playback, Control+Shift+P, in both.** Shift adds recording to Play Media, and P begins Playback, so the letter is in the name, as the house rule wants. It opens the player, plays at once and presses the player's Capture stream button, which records to Music, Homer Player.
- **The freed keys.** FileDir's Path List to Clipboard moved from Control+Shift+P to Control+Shift+L, L for List. Control+Shift+H is free in FileDir.
- **The Space bar.** Space alone toggles the mark in a list; Shift+Space says the selection or the marked items; Control+Space marks in a list and selects a chunk in text; Alt+Space is Windows' window menu, never bound; Alt+Shift+Space and Control+Shift+Space stay unbound. DbDo gains Space for Toggle Mark, with one guard: a Space typed within a second of a letter belongs to the grid's type-ahead search, so "new y" still finds New York. EdSharp's key file named Alt+Shift+Space for Web Client Utilities, which is a JAWS script on JAWS+Control+Space; the file now names the real key.
- **Generate Statistics (Alt+Shift+S) and Generate Graphics (Alt+Shift+G) replace Generate from Grid.** Statistics are read; graphics are handed to sighted colleagues as files. So the two are separate commands, but they share one dataset dialog: Which columns, Which records (all in view, marked, or current, which takes the place of the Marked or Current question), Arrange (by column, each column a variable, or by row, each record a series), and Kind; Graphics adds Drawn by. A checkbox in one shared command was weighed and set aside, since the key already makes that choice.
- **Why not Control+Shift+S and G, as Jamal proposed.** Control+Shift+S is Save As in every Homer app. By the suite's own factor, Control is for commands that change data; these change none, and a pick dialog is as much Alt's as Control's. Alt+Shift+S was free once Edit Script moved to Alt+Shift+V, and Alt+Shift+G was Generate from Grid's key, so charts stay where his fingers know them.
- **Charts without Microsoft Office.** The kit's DataReport draws them with Python: pandas, matplotlib, seaborn and openpyxl, all free and MIT-compatible. A chart is a PNG, an SVG, a web page with the takeaway sentence and the numbers as a table, and an Excel workbook holding a native chart, made without Excel. Excel through COM stays as Drawn by Excel, and as the fallback when Python cannot draw, as Jamal asked. help\AnalysisPlan.md has the comparison of NuGet and PyPI packages.

### Rollback

Each change is one or two lines in the app's source, marked "21 November 2026", and one line in its key file; data\SuiteCommands.inix gives what each key was. Rollback.zip of the day holds every file as it was before any of the four rounds. The fourth round's new files -- exec\CSharp\DataReport.cs, scripts\installDataTools.cmd and scripts\testChart -- are listed in Rollback.txt, to delete when rolling back.
