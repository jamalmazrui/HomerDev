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
