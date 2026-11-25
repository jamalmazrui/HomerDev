---
title: "Homer Key Groups"
subtitle: "Every key pattern group of the Homer Suite, counted and audited"
---

# Homer Key Groups

Jamal asked on 21 November 2026 for every Homer key pattern group to be named, counted and audited. A group is a set of keys that should behave alike, because their keys share a shape (all the F8 keys, every Alt key that repeats a search) or their commands share a topic (the clipboard, local AI). A key can be in more than one group. This page names each group and the properties its members should share. It says whether the suite practices them, and what changed when they did not.

The counts are at the end of the page. scripts\\keyGroups writes them from the four apps' key files, so they stay true as keys change. Run it with no arguments after a key change.

## How to read the audits

Each group has the same three parts.

- **Shares:** the properties every member should have.
- **Found:** where the suite already practices them, and where it did not.
- **Done or open:** what changed on 21 November 2026, or what is left for a decision. Each change is in data\\SuiteCommands.inix with the key it replaced, and in each app's History.

The groups are in lower-case alphabetical order, except the function keys, which run from F1 to F12.

## The audits

### again

- **Shares:** Alt and a search's own letter repeats that search forward, without asking again; the name is "<command> Again".
- **Found:** EdSharp (Go to Percent Again, Jump to Line Again), FileDir (Jump Again, Keywords Again) and HomerView (Go to Percent Again) followed it. DbDo called its one "Repeat Go to" and had no Jump Again or Keywords Again, though it has Jump and Keywords.
- **Done:** DbDo's is now Go to Record Again (Alt+G), and DbDo gains Jump Again (Alt+J) and Keywords Again (Alt+K), with FileDir's sentences, now in the catalog. F3 still repeats whichever search came last.

### ai and online help

- **Shares:** a command that sends text off the computer says so in its description; local and online are told apart.
- **Found:** the local AI commands are their own group, below. Lookup Term, Translate and HomerView's Query Web and Consult Copilot reach online services, and their descriptions say where.
- **Open:** none.

### apostrophe, clipboard text

- **Shares:** the Apostrophe key is the clipboard's text: Alt says it, Control saves it to a file, Control+Shift appends it to a file, Alt+Shift clears it.
- **Found:** all four keys in all four apps, word for word. The one exception is FileDir's plain Apostrophe and Shift+Apostrophe, which say the item's and the folder's names.
- **Open:** none. FileDir's two plain keys are typed keys in a list, where nothing else would use them.

### archives

- **Shares:** U for unarchive and Z for zip; the plain Control key is the everyday one.
- **Found:** FileDir only. Unarchive (Control+U) and its variants are one family; Zip (Control+Shift+Z) and Zip then Delete (Control+Z) another.
- **Done:** Zip List gave up Alt+Shift+L earlier today, for Read Lean Marked.

### back, forward and levels

- **Shares:** Alt+LeftArrow goes back and Alt+RightArrow forward; Backspace goes up a level.
- **Found:** DbDo's child tables and FileDir's folders follow it. EdSharp's Alt+Left and Alt+Right move by chunk, which is the text app's meaning of a step.
- **Open:** none.

### backslash, open elsewhere

- **Shares:** Backslash opens the current thing somewhere else: Alt in Explorer, Control at a command prompt, Control+Shift in the other Homer app.
- **Found:** all three MDI apps, all three keys.
- **Open:** none.

### bookmarks and favorites

- **Shares:** Control+B saves, Control+Shift+B clears, Alt+B lists; Shift+B says, where Shift letters say.
- **Found:** DbDo and EdSharp agree. EdSharp's favorites follow the same shape on L (Control+L, Control+Shift+L, Alt+L), though L begins no word of Set Favorite.
- **Open:** EdSharp's Set Favorite has a letter from no word of its name. A rename such as "List Favorite" would make L honest; it waits for Jamal's word, since favorites are old habits.

### case, lines and text shape

- **Shares:** a command that reshapes text changes data, so Control is preferred; families keep their own pattern.
- **Found:** EdSharp only. Case is four keys on U, Quote and Unquote on Q, Wrap and Unwrap on W, and the format pairs split Alt+Shift (set) from Control (move to the next change).
- **Done:** Insert Time moved to Control+Semicolon and Text Contents to Control+Shift+T earlier today.

### clipboard

- **Shares:** Control+C copies and replaces; Alt+C appends; Control+X cuts and Alt+X cuts and appends; Control+V pastes. A command that puts something on the clipboard is named "Copy <thing>", or "<thing> to Clipboard" when it is a path or name.
- **Found:** Copy, Copy Append, Cut and Paste agree across the apps. FileDir's "Copy Name" sat beside "Path to Clipboard" with a different shape. HomerView's Copy Log is Alt+Shift+L, not the suite's Control+F12, because Edge owns Control+F12.
- **Done:** FileDir's Copy Name is Name to Clipboard (Alt+Shift+N).
- **Open:** FileDir has Cut but not Cut Append (Alt+X is free there). Adding it needs a file-list append on the clipboard, which no app has yet.

### conversion and export

- **Shares:** Control+Shift+X exports and Control+Shift+I imports; every conversion runs the kit's shared code.
- **Found:** the keys agree. The names do not: Export Data (DbDo), Export Format (EdSharp) and Export Type (FileDir).
- **Open:** one name would be better for a suite. Each name fits what its app exports, and DbDo's pairs with Import Data, so this waits for Jamal's choice.

### data records and fields

- **Shares:** DbDo's own record commands keep the rest of the suite's modifiers.
- **Found:** DbDo only. The edit trio Edit Notes, Edit Tags and Edit url stays on Alt+Shift beside its Say keys, as recorded in KeyDecisions.
- **Open:** none.

### delete

- **Shares:** Control+D deletes the unit; Control+Shift+D deletes it harder, without asking or without the recycle bin.
- **Found:** DbDo, EdSharp and FileDir all follow it. DbDo wrote "Delete Without Confirmation" with a capital W, against the suite's small words.
- **Done:** it is Delete without Confirmation.

### editing basics

- **Shares:** Windows' own editing keys mean what they mean everywhere.
- **Found:** EdSharp and HomerView follow Windows. The list apps give Control+A and Control+Shift+A to Mark All and Unmark All, which is their selection.
- **Open:** none.

### f1 help

- **Shares:** F1 the guide, Shift+F1 what this does, Alt+F1 About, Control+F1 the key describer, Control+Shift+F1 history, Alt+Shift+F1 the ReadMe; with them, Control+Slash where am I and Alt+F10 the Alternate Menu.
- **Found:** DbDo, EdSharp and FileDir follow all of it. HomerView's exceptions are recorded: Edge owns F1 and Control+Slash.
- **Open:** none.

### f2 edit and rename

- **Shares:** F2 edits or renames; Shift+F2 renames on disk.
- **Found:** DbDo's Edit Cell and Pick Value (Control+F2), and EdSharp's and FileDir's Rename. FileDir's Reorder Names joined it on Control+F2 earlier today.
- **Open:** none.

### f3 search again

- **Shares:** F3 repeats the last search forward and Shift+F3 back; Control makes it a regular expression; Alt searches for the text at the cursor.
- **Found:** all four apps follow it. FileDir has no Find with Regex on Control+F3; its regex search is Mark with Regex.
- **Open:** whether FileDir needs Find with Regex, or Mark with Regex is enough.

### f4 windows

- **Shares:** F4 picks a window, Shift+F4 says them, Control+F4 closes one, Control+Shift+F4 closes the others.
- **Found:** all three MDI apps, and HomerView for its tabs. EdSharp already wrote "Close All but Current Window" with a small "but"; DbDo, FileDir, the kit and the catalog wrote "But", so EdSharp's was left out of the suite's check.
- **Done:** "Close All but Current Window" everywhere, and the catalog now checks it in all three apps.

### f5 refresh and run

- **Shares:** F5 reads again or runs.
- **Found:** DbDo and FileDir refresh; EdSharp runs, and its compile family sits around it. HomerView's one F5 key lists form fields, on the key JAWS uses for that.
- **Open:** none.

### f6 panes, sections and views

- **Shares:** F6 moves among the parts of a window; Control+F6 to the next thing of the same level.
- **Found:** each app's parts differ (views, sections, panes, folders), and each keeps the shape.
- **Open:** none.

### f7 review and language

- **Shares:** F7 checks spelling; with modifiers, the thesaurus, lookups and translation.
- **Found:** EdSharp has the full family, and FileDir has Translate File on Alt+Shift+F7, as EdSharp's Translate Language. HomerView's one F7 key lists links, on the key JAWS uses for that. EdSharp's Guard Document and No Guard (Control+F7, Control+Shift+F7) make a document read-only, which is not review.
- **Open:** Guard Document has no better home in the F keys yet; recorded, not moved.

### f8 selection, marking and reading all

- **Shares:** F8 starts a run, Shift+F8 completes it, Alt+Shift+F8 completes it the other way; Alt+F8 reads everything and Control+F8 copies everything.
- **Found:** EdSharp and HomerView read all on Alt+F8 and copy all on Control+F8. DbDo had a second start key, Start Unmark, on Alt+F8, where FileDir has one Start Mark or Unmark. Neither list app read or copied all on F8.
- **Done:** DbDo has FileDir's one Start Mark or Unmark (F8), and Start Unmark is retired into it. Alt+F8 reads everything in both list apps (Read Wide in DbDo, Read Lean in FileDir). Control+F8 is DbDo's Copy Grid.

### f9 readable view

- **Shares:** F9 shows a more readable view.
- **Found:** Preview Markdown (Control+F9) and HomerView's Extract Main Content (Shift+F9) fit. Check Markdown, Run Code Blocks and Record Macro sit here by earlier decisions.
- **Open:** none.

### f10 menus

- **Shares:** Shift+F10 the context menu, Control+F10 Send To, Alt+F10 the Alternate Menu.
- **Found:** all of it, wherever the app has the command.
- **Open:** none.

### f11 version and window layout

- **Shares:** F11 installs the newest version; with modifiers, the window layouts.
- **Found:** all three MDI apps; HomerView uses Control+F11, since Edge owns F11. The layouts are now on the File menu, with no Window menu.
- **Open:** none.

### f12 ai, logs, media and macros

- **Shares:** F12 asks the local AI, Shift+F12 asks about the current thing, Control+F12 copies the log, Alt+F12 plays the tutorials, Alt+Shift+F12 plays a macro.
- **Found:** all three MDI apps. HomerView leaves F12 to Edge.
- **Open:** none.

### filter and order

- **Shares:** Control+F filters and Control+Shift+F clears, in the list apps; Shift+F, Shift+O and Shift+8 say the filter, the order and both; Alt orders and Alt+Shift reverses.
- **Found:** DbDo said Filter Records and FileDir Set Filter.
- **Done:** FileDir's is Filter Items.

### folders and windows tools

- **Shares:** FileDir's folder commands come in Open (new window) and Go to (same window) pairs.
- **Found:** FileDir follows it throughout.
- **Open:** none.

### go to and open

- **Shares:** Control+O opens, in a new window where that applies; Control+G goes to, in the same window; Alt+R lists the recent ones.
- **Found:** all four apps.
- **Open:** none.

### grid table keys

- **Shares:** Alt+Control with the arrows, Home, End, PageUp and PageDown keep the screen readers' table meanings.
- **Found:** DbDo only, as its grid keyboard model of 31 October requires.
- **Open:** none.

### home and end

- **Shares:** Home and End go to the ends of a line or row; Control adds the ends of the column or list.
- **Found:** DbDo, EdSharp and FileDir follow their own grids and lines.
- **Open:** none.

### item lists in text

- **Shares:** EdSharp's list tools are one family on Alt+Shift with the first letter of the verb.
- **Found:** Order, Reverse, Keep Unique, Number, List Different and Query Common Items follow it.
- **Open:** none.

### launch from the desktop

- **Shares:** Alt+Control and the app's letter starts or brings forward the app. It is the one sanctioned use of Alt+Control with a letter.
- **Found:** EdSharp (E), FileDir (F) and HomerView (Alt+Control+Shift+H) list theirs. DbDo's Alt+Control+D is set by its installer's shortcut, and its key file does not list it.
- **Open:** listing Launch DbDo in DbDo's key file needs a [handled DbDo] line in the catalog, since the shortcut, not DbDo, owns the key.

### local ai

- **Shares:** F12 asks the model on this computer a plain question; Shift+F12 asks about the current thing; the name is "Chat with AI" and "Chat about <thing>".
- **Found:** DbDo, EdSharp and FileDir all follow it, with the thing named for each app: Table, Document, File.
- **Open:** none.

### mail, send and web

- **Shares:** one Mail on Control+M; Send To on Control+F10; Web Download on Alt+Shift+W; Burn to CD on Alt+Shift+B.
- **Done:** Mail became one command earlier today. DbDo's Mail Record has no key, since Control+M marks a record there.

### marking

- **Shares:** in the two list apps, the same names and keys for the same marking jobs.
- **Found:** DbDo and FileDir agreed on Mark All, Toggle Mark, Mark and Next, Next and Previous Marked and Invert Marked. They disagreed on the ends of a run, with these key sets.
  - **DbDo:** Mark to First and Last on Control+Shift+Home and End, and First and Last Marked on Control+PageUp and PageDown.
  - **FileDir:** Mark to Top and Bottom on Shift+Home and End, and Beginning and End Marked on Control+Shift+Home and End.
- The same key did opposite jobs: Control+Shift+Home marked in DbDo and moved in FileDir.
- **Done:** FileDir takes DbDo's names and keys, and keeps the Windows Shift+Home and End, and Alt+Shift+Home and End, as second keys. Both apps now have Mark to First, Mark to Last, Unmark to First, Unmark to Last, First Marked and Last Marked, word for word, checked by the catalog. FileDir's "Unmark All But Current" is Unmark All but Current.

### media and play

- **Shares:** Control+P plays, in the Homer Player; Control+Shift+P plays and records (Record Playback, P for Playback); Alt+F12 plays the tutorials.
- **Found:** DbDo and FileDir played media on Control+P, but FileDir's Play Media handed the list to mpv's own window, while its Homer Player (Control+Shift+H) and Play List (Control+Shift+L) were two more ways to play. Nothing recorded from a key.
- **Done (fourth round):** FileDir's Play Media plays in the Homer Player, as DbDo's does: the marked files, a play list or a document with media links, the clipboard, or the folder. Homer Player is retired into it, with its name as a former name. Play List keeps no key. Record Playback is Control+Shift+P in both, the player's Capture stream button pressed when it opens. Path List to Clipboard moved from Control+Shift+P to the freed Control+Shift+L, L for List, and Control+Shift+H is free.

### new and save

- **Shares:** Control+N new, Control+Shift+N a new copy of the current one; Control+S save, Control+Shift+S save as.
- **Found:** DbDo said New Copy and FileDir New Item Copy for the same job.
- **Done:** FileDir's is New Copy, now in the catalog.

### properties and details

- **Shares:** Alt+Enter shows properties.
- **Found:** EdSharp and FileDir show the file's, DbDo the table's.
- **Open:** none.

### reading aloud

- **Shares:** W wide, L lean, Y yield; Alt from the first, Alt+Shift the marked, Control from the current one; Alt+F8 reads all; any key stops a reading, and a second press shows it in a window.
- **Done:** earlier today, and Alt+F8 now.

### regex

- **Shares:** Control+Shift+E, R and Y extract, replace and yield; Control+F3 finds; every name ends "with Regex".
- **Found:** DbDo lacked Yield with Regex until earlier today. FileDir's R slot is Rename with Regex, which is its replace.
- **Open:** see f3, for Find with Regex in FileDir.

### rename

- **Shares:** F2 and Control+R; Control+Shift+R with regex.
- **Found:** FileDir follows it. Find Duplicates in Tree on Alt+Shift+J has a letter from no word of its name.
- **Open:** a better key for Find Duplicates in Tree.

### repeat and next or previous

- **Shares:** a Next command's Previous adds Shift, or swaps Down for Up, PageDown for PageUp, Period for Comma.
- **Found:** all four apps follow it.
- **Open:** none.

### say, on alt

- **Shares:** where Shift and a letter types (EdSharp, HomerView), Alt and a letter says. In the list apps, Alt says the suite's shared answers: Alt+Y, Alt+Z, Alt+P, Alt+Delete.
- **Found:** Say Status was "Shift+Z or Alt+Z" in DbDo and "Alt+Z or Shift+Z" in FileDir.
- **Done:** both list Alt+Z first, the suite key.

### say, on shift

- **Shares:** in the list apps, Shift and a letter says one fact and never acts; the letter starts the fact's word.
- **Found:** DbDo and FileDir follow it.
- **Open:** none.

### scripts and macros

- **Shares:** V for scripts: Alt+V invokes, Shift+V says which, Alt+Shift+V edits.
- **Found:** EdSharp's View Script and DbDo's Edit Script did the same job on different keys (Alt+Shift+V, Alt+Shift+S).
- **Done:** both are Edit Script on Alt+Shift+V, in the catalog. V is a recorded exception to the first-letter rule, as Invoke Script's Alt+V has been since 9 November.

### search

- **Shares:** Control+J jumps by name or field, Control+K searches content; Shift reverses each.
- **Found:** DbDo had Reverse Jump; FileDir did not. Keywords' sentence said "whose fields holds the keywords" in DbDo.
- **Done:** FileDir gains Reverse Jump (Control+Shift+J). Keywords and Reverse Keywords now say "with the keywords in its fields" and "in its content", in the catalog.

### settings and toggles

- **Shares:** Alt+Shift+E edits settings everywhere; a toggle's name ends in Toggle.
- **Found:** Edit Settings agrees in all four. Toggle names do not: Toggle Mark (agreed 15 November) and Toggle Reading begin with the word; EdSharp's Indent Mode and Append from Clipboard are toggles without it.
- **Open:** one shape for toggle names waits for Jamal's word, since Toggle Mark's name was agreed.

### space bar

- **Shares:** Space alone toggles the mark in a list; Shift+Space says the selection, or the marked items; Control+Space marks in a list and selects a chunk in text, the Windows habits; Alt+Space is the window menu of Windows and is never bound. Alt+Shift+Space and Control+Shift+Space are left unbound, so a stray modifier never does something unexpected.
- **Found:** FileDir toggled with Space and Control+Space; DbDo with Control+Space only, though its grid is a list. DbDo's Shift+Space reads the marked records (Read Wide Marked), which is what Say Selected says elsewhere. EdSharp's key file named Alt+Shift+Space for Web Client Utilities, which is in fact a JAWS script on JAWS+Control+Space; EdSharp never bound the key.
- **Done (fourth round):** Space toggles the mark in DbDo too. A Space typed within a second of a letter goes on to the grid's type-ahead search instead, so "new y" still finds New York. EdSharp's key file names the real key of Web Client Utilities.

### web pages

- **Shares:** HomerView's own commands avoid every key Edge, NVDA and JAWS own.
- **Found:** recorded in HomerView's own notes.
- **Open:** none.

### windows

- **Shares:** the window commands are on the File menu; Control+Tab moves among windows.
- **Done:** no Window menu, earlier today; small "but" in Close All but Current Window.

### yield (counting)

- **Shares:** Y counts: Alt+Y all, Alt+Shift+Y marked, Control+Y from the current one; Control+Shift+Y is the regex count.
- **Found:** EdSharp's Yield Encoding (Alt+Shift+Y) converts text rather than counting. HomerView's Yield Structure counts the page's parts, which fits.
- **Open:** Yield Encoding's name says yield for a conversion; a better name waits for Jamal's word.

### z keys

- **Shares:** Z is the bottom of the alphabet: Alt+Z says status, and Z keys turn things on and off.
- **Found:** Alt+Z is Say Status in the three MDI apps. Control+Z is Undo in EdSharp and Zip then Delete in FileDir, with no undo. The toggles on Z are FileDir's Timer Toggle and DbDo's Read Only Toggle. HomerView's Z keys move by kind, a recorded exception.
- **Open:** none.

<!-- key groups start -->

## The groups, counted

Written by scripts\keyGroups from the four key files, 24 November 2026. Each count is key bindings: a command with two keys counts twice, and a binding may be in more than one group.

- **again** (key shape): 9 -- DbDo 3, EdSharp 3, FileDir 2, HomerView 1
- **ai and online help** (topic): 14 -- DbDo 2, EdSharp 5, FileDir 3, HomerView 4
- **apostrophe, clipboard text** (key shape): 16 -- DbDo 4, EdSharp 4, FileDir 4, HomerView 4
- **archives** (topic): 8 -- FileDir 8
- **back, forward and levels** (topic): 13 -- DbDo 5, FileDir 8
- **backslash, open elsewhere** (key shape): 11 -- DbDo 3, EdSharp 3, FileDir 5
- **bookmarks and favorites** (topic): 10 -- DbDo 4, EdSharp 6
- **case, lines and text shape** (topic): 43 -- EdSharp 43
- **clipboard** (topic): 55 -- DbDo 12, EdSharp 17, FileDir 17, HomerView 9
- **conversion and export** (topic): 17 -- DbDo 2, EdSharp 8, FileDir 5, HomerView 2
- **data records and fields** (topic): 35 -- DbDo 35
- **delete** (topic): 16 -- DbDo 3, EdSharp 8, FileDir 5
- **editing basics** (topic): 17 -- DbDo 1, EdSharp 12, HomerView 4
- **f1 help** (key shape): 30 -- DbDo 8, EdSharp 8, FileDir 8, HomerView 6
- **f2 edit and rename** (key shape): 9 -- DbDo 2, EdSharp 3, FileDir 4
- **f3 search again** (key shape): 18 -- DbDo 4, EdSharp 6, FileDir 2, HomerView 6
- **f4 windows** (key shape): 19 -- DbDo 5, EdSharp 5, FileDir 6, HomerView 3
- **f5 refresh and run** (key shape): 9 -- DbDo 1, EdSharp 6, FileDir 1, HomerView 1
- **f6 panes, sections and views** (key shape): 14 -- DbDo 2, EdSharp 5, FileDir 6, HomerView 1
- **f7 review and language** (key shape): 8 -- EdSharp 6, FileDir 1, HomerView 1
- **f8 selection, marking and reading all** (key shape): 20 -- DbDo 5, EdSharp 6, FileDir 4, HomerView 5
- **f9 readable view** (key shape): 5 -- DbDo 1, EdSharp 3, HomerView 1
- **f10 menus** (key shape): 9 -- DbDo 2, EdSharp 3, FileDir 3, HomerView 1
- **f11 version and window layout** (key shape): 13 -- DbDo 1, EdSharp 5, FileDir 5, HomerView 2
- **f12 ai, logs, media and macros** (key shape): 14 -- DbDo 5, EdSharp 5, FileDir 4
- **filter and order** (topic): 22 -- DbDo 9, FileDir 13
- **folders and windows tools** (topic): 38 -- DbDo 1, EdSharp 3, FileDir 34
- **go to and open** (topic): 55 -- DbDo 10, EdSharp 17, FileDir 23, HomerView 5
- **grid table keys** (key shape): 17 -- DbDo 17
- **home and end** (key shape): 16 -- DbDo 8, EdSharp 2, FileDir 6
- **item lists in text** (topic): 7 -- EdSharp 6, FileDir 1
- **launch from the desktop** (key shape): 3 -- EdSharp 1, FileDir 1, HomerView 1
- **local ai** (topic): 6 -- DbDo 2, EdSharp 2, FileDir 2
- **mail, send and web** (topic): 13 -- DbDo 1, EdSharp 5, FileDir 6, HomerView 1
- **marking** (topic): 60 -- DbDo 24, FileDir 36
- **media and play** (topic): 8 -- DbDo 4, EdSharp 1, FileDir 3
- **new and save** (topic): 13 -- DbDo 4, EdSharp 5, FileDir 4
- **properties and details** (topic): 8 -- DbDo 3, EdSharp 1, FileDir 4
- **reading aloud** (topic): 22 -- DbDo 10, EdSharp 3, FileDir 6, HomerView 3
- **regex** (topic): 17 -- DbDo 5, EdSharp 5, FileDir 4, HomerView 3
- **rename** (topic): 7 -- EdSharp 1, FileDir 6
- **repeat and next or previous** (topic): 46 -- DbDo 4, EdSharp 24, FileDir 10, HomerView 8
- **say, on alt** (key shape): 31 -- DbDo 6, EdSharp 11, FileDir 7, HomerView 7
- **say, on shift** (key shape): 48 -- DbDo 26, EdSharp 3, FileDir 17, HomerView 2
- **scripts and macros** (topic): 23 -- DbDo 9, EdSharp 13, FileDir 1
- **search** (topic): 39 -- DbDo 8, EdSharp 11, FileDir 8, HomerView 12
- **settings and toggles** (topic): 21 -- DbDo 5, EdSharp 8, FileDir 6, HomerView 2
- **space bar** (key shape): 11 -- DbDo 3, EdSharp 3, FileDir 3, HomerView 2
- **web pages** (topic): 31 -- HomerView 31
- **windows** (topic): 32 -- DbDo 6, EdSharp 10, FileDir 13, HomerView 3
- **yield (counting)** (topic): 15 -- DbDo 4, EdSharp 3, FileDir 5, HomerView 3
- **z keys** (key shape): 15 -- DbDo 3, EdSharp 3, FileDir 5, HomerView 4

In all, 713 key bindings in 52 groups; 0 in no group.

## Appendix: the members of each group

### again

- **DbDo:** Go to Record Again (Alt+G); Jump Again (Alt+J); Keywords Again (Alt+K).
- **EdSharp:** Go to Percent Again (Alt+G); Jump to Line Again (Alt+J); Open Again (Alt+O).
- **FileDir:** Jump Again (Alt+J); Keywords Again (Alt+K).
- **HomerView:** Go to Percent Again (Alt+G).

### ai and online help

- **DbDo:** Chat about Table (Shift+F12); Chat with AI (F12).
- **EdSharp:** Chat about Document (Shift+F12); Chat with AI (F12); Lookup Term (Alt+F7); Thesaurus (Shift+F7); Translate Language (Alt+Shift+F7).
- **FileDir:** Chat about File (Shift+F12); Chat with AI (F12); Translate File (Alt+Shift+F7).
- **HomerView:** Consult Copilot (Alt+NVDA+C); Instruct Page (Alt+I); Query Web (Alt+NVDA+Q); Query Web (Alt+Q).

### apostrophe, clipboard text

- **DbDo:** Append Clipboard (Control+Shift+'); Clear Clipboard (Alt+Shift+'); Save Clipboard (Control+'); Say Clipboard (Alt+').
- **EdSharp:** Append Clipboard (Control+Shift+'); Clear Clipboard (Alt+Shift+'); Save Clipboard (Control+'); Say Clipboard (Alt+').
- **FileDir:** Append Clipboard (Control+Shift+'); Clear Clipboard (Alt+Shift+'); Save Clipboard (Control+'); Say Clipboard (Alt+').
- **HomerView:** Append Clipboard (Control+Shift+'); Clear Clipboard (Alt+Shift+'); Save Clipboard (Control+'); Say Clipboard (Alt+').

### archives

- **FileDir:** Say Unarchive Test (Shift+U); Unarchive (Control+U); Unarchive Password (Alt+Shift+U); Unarchive to Same Name (Control+Shift+U); Unarchive without Subfolders (Alt+U); Zip (Control+Z); Zip then Delete (Control+Shift+Delete); Zip then Delete (Control+Shift+Z).

### back, forward and levels

- **DbDo:** Enter Child Table (Alt+RightArrow); Enter Child Table (Enter); Exit Child Table (Alt+LeftArrow); Exit Child Table (Backspace); Exit to Root Table (Alt+Home).
- **FileDir:** Come up Level (,); Come up Level (Backspace); Go Back (Alt+LeftArrow); Go Forward (Alt+RightArrow); Go to Parent Folder (,); Go to Parent Folder (Shift+Backspace); Open Parent Folder (Backspace); Parent Folder (Backspace).

### backslash, open elsewhere

- **DbDo:** Open Command Prompt (Control+\); Open in Explorer (Alt+\); Show in FileDir (Control+Shift+\).
- **EdSharp:** Open Command Prompt (Control+\); Open in Explorer (Alt+\); Show in FileDir (Control+Shift+\).
- **FileDir:** Go to Root Folder (Shift+\); Open Command Prompt (Control+\); Open in DbDo (Control+Shift+\); Open in Explorer (Alt+\); Open Root Folder (\).

### bookmarks and favorites

- **DbDo:** Clear Bookmark (Control+Shift+B); List Bookmarks (Alt+B); Save Bookmark (Control+B); Say Bookmark (Shift+B).
- **EdSharp:** Clear Bookmark (Control+Shift+B); Clear Favorite (Control+Shift+L); List Bookmarks (Alt+B); List Favorites (Alt+L); Save Bookmark (Control+B); Set Favorite (Control+L).

### case, lines and text shape

- **EdSharp:** Align (Alt+Shift+A); Baseline (Alt+Shift+6); Calculate Date (Control+Shift+;); Delete Hard Line (Control+D); End Tag (Control+Shift+.); Enter New Line (Enter); Evaluate Expression (Control+=); Format Code (Control+4); Hard Line Break (Control+Shift+H); Indent (Tab); Indent Mode (Alt+Shift+I); Indent New Line (Shift+Enter); Indent New Line Previous (Alt+Shift+Enter); Infer Indent (Alt+]); Insert Time (Control+;); Join Lines (Control+Shift+J); Justify (Alt+Shift+J); Left Brace (Control+Shift+[); Lower Case (Control+Shift+U); Next Baseline (Control+6); Next Indent (Control+I); Outdent (Shift+Tab); Previous Baseline (Control+Shift+6); Previous Indent (Control+Shift+I); Proper Case (Alt+U); PyBrace (Alt+Shift+[); PyDent (Alt+[); Quote (Control+Q); Repeat Line (Control+Y); Replace Tokens (Control+Shift+=); Right Brace (Control+Shift+]); Say Braces (Alt+Shift+]); Say Indentation (Alt+I); Section Break (Control+Enter); Set Selection Font (Alt+Shift+Dash); Start Tag (Control+Shift+,); Swap Case (Alt+Shift+U); Transform Files (Alt+=); Trim Blanks (Control+Shift+Enter); Unquote (Control+Shift+Q); Unwrap (Control+Shift+W); Upper Case (Control+U); Word Wrap (Control+W).

### clipboard

- **DbDo:** Append Clipboard (Control+Shift+'); Clear Clipboard (Alt+Shift+'); Copy Append (Alt+C); Copy Append Record (Alt+Shift+C); Copy Cell (Control+C); Copy Grid (Control+F8); Copy Log (Control+F12); Copy Record (Control+Shift+C); Evaluate Expression (Control+=); Extract with Regex (Control+Shift+E); Save Clipboard (Control+'); Say Clipboard (Alt+').
- **EdSharp:** Append Clipboard (Control+Shift+'); Append from Clipboard (Alt+7); Clear Clipboard (Alt+Shift+'); Copy (Control+C); Copy All (Control+F8); Copy Append (Alt+C); Copy Log (Control+F12); Copy Rich Text (Control+Shift+C); Cut (Control+X); Cut Append (Alt+X); Merge File (Control+Shift+M); New from Clipboard (Control+Shift+N); Paste (Control+V); Paste as Markdown (Control+Shift+V); Path to Clipboard (Alt+Shift+P); Save Clipboard (Control+'); Say Clipboard (Alt+').
- **FileDir:** Append Clipboard (Control+Shift+'); Append File Contents (Alt+Shift+C); Clear Clipboard (Alt+Shift+'); Convert Units (Control+3); Copy (Control+C); Copy Append (Alt+C); Copy Log (Control+F12); Copy to Folder (Control+Shift+C); Cut (Control+X); Evaluate Expression (Control+=); Extract with Regex (Control+Shift+E); Name to Clipboard (Alt+Shift+N); Paste (Control+V); Paste Move (Control+Shift+V); Path List to Clipboard (Control+Shift+L); Save Clipboard (Control+'); Say Clipboard (Alt+').
- **HomerView:** Append Clipboard (Control+Shift+'); Clear Clipboard (Alt+Shift+'); Copy All (Control+F8); Copy Append (Alt+C); Copy Line (Control+C); Copy Log (Alt+Shift+L); Page Links to Clipboard (Alt+Shift+P); Save Clipboard (Control+'); Say Clipboard (Alt+').

### conversion and export

- **DbDo:** Export Data (Control+Shift+X); Import Data (Control+Shift+I).
- **EdSharp:** Export Format (Control+Shift+X); HTML Format (Control+H); Open Other Format (Control+Shift+O); Text Combine (Alt+Shift+T); Text Contents (Control+Shift+T); Text Convert (Control+T); Translate Language (Alt+Shift+F7); Yield Encoding (Alt+Shift+Y).
- **FileDir:** Convert Encoding (Control+2); Convert Units (Control+3); Export Type (Control+Shift+X); Say Character Encoding (Shift+2); Translate File (Alt+Shift+F7).
- **HomerView:** Open Document (Control+O); Save Page (Control+S).

### data records and fields

- **DbDo:** Copy Append Record (Alt+Shift+C); Copy Record (Control+Shift+C); Delete Record (Control+D); Delete Record (Delete); Design Database (Alt+Shift+D); Edit Cell (F2); Edit Notes (Alt+Shift+N); Edit Record (Control+E); Edit Tags (Alt+Shift+T); Edit url (Alt+Shift+U); Filter Records (Control+F); Generate Graphics (Alt+Shift+G); Generate Statistics (Alt+Shift+S); Go to Record (Control+G); Go to Record Again (Alt+G); Inspect Record (Alt+I); Mail Record (Control+M); Mark Record (;); Merge Data (Control+Shift+M); New Record (Control+N); Null Value (Control+Shift+Backspace); Order Records (Alt+O); Pick Value (Control+F2); Query (Control+Q); Query History (Alt+Shift+Q); Record Macro (Control+Shift+F9); Refresh Records (F5); Say Notes (Shift+N); Say Query (Shift+Q); Say Tags (Shift+T); Say Whole Record (Shift+W); Show Columns (Alt+S); Table Properties (Alt+Enter); Table Summary (Alt+T); Unmark Record (/).

### delete

- **DbDo:** Delete Record (Control+D); Delete Record (Delete); Delete without Confirmation (Control+Shift+D).
- **EdSharp:** Delete Down (Alt+Shift+Delete); Delete File (Alt+Shift+D); Delete Hard Line (Control+D); Delete Left (Control+Shift+Backspace); Delete Line (Alt+Backspace); Delete Paragraph (Control+Shift+D); Delete Right (Control+Shift+Delete); Delete Up (Alt+Shift+Backspace).
- **FileDir:** Delete (Delete); Delete and Recycle (Control+Delete); Delete and Recycle File Now (Control+D); Delete File Now (Control+Shift+D); Delete without Recycle (Shift+Delete).

### editing basics

- **DbDo:** Replace (Control+R).
- **EdSharp:** Complete Selection (Shift+F8); Enter New Line (Enter); Go to Start of Selection (Alt+Shift+F8); Redo (Control+Shift+Z); Replace (Control+R); Reselect (Control+Shift+F8); Select All (Control+A); Select Chunk (Control+Space); Special Character (F2); Start Selection (F8); Undo (Control+Z); Unselect All (Control+Shift+A).
- **HomerView:** Complete Selection (Shift+F8); Go to Start of Selection (Alt+Shift+F8); Select Chunk (Control+Space); Start Selection (F8).

### f1 help

- **DbDo:** About (Alt+F1); Alternate Menu (Alt+F10); Documentation (F1); History of Changes (Control+Shift+F1); Key Describer Toggle (Control+F1); ReadMe (Alt+Shift+F1); What This Does (Shift+F1); Where Am I (Control+/).
- **EdSharp:** About (Alt+F1); Alternate Menu (Alt+F10); Documentation (F1); History of Changes (Control+Shift+F1); Key Describer Toggle (Control+F1); ReadMe (Alt+Shift+F1); What This Does (Shift+F1); Where Am I (Control+/).
- **FileDir:** About (Alt+F1); Alternate Menu (Alt+F10); Documentation (F1); History of Changes (Control+Shift+F1); Key Describer Toggle (Control+F1); ReadMe (Alt+Shift+F1); What This Does (Shift+F1); Where Am I (Control+/).
- **HomerView:** About HomerView (Alt+F1); Alternate Menu (Alt+F10); History of Changes (Control+Shift+F1); Hotkey Summary (Alt+Shift+H); Key Describer Toggle (Control+F1); ReadMe (Alt+Shift+F1).

### f2 edit and rename

- **DbDo:** Edit Cell (F2); Pick Value (Control+F2).
- **EdSharp:** Rename (Shift+F2); Sample Programs (Control+Shift+F2); Special Character (F2).
- **FileDir:** Rename (F2); Rename (Shift+F2); Reorder Names (Control+F2); Stop Timer (Alt+F2).

### f3 search again

- **DbDo:** Forward Find with Regex (Control+F3); Reverse Find with Regex (Control+Shift+F3); Search Next (F3); Search Previous (Shift+F3).
- **EdSharp:** Forward Find at Cursor (Alt+F3); Forward Find with Regex (Control+F3); Reverse Find at Cursor (Alt+Shift+F3); Reverse Find with Regex (Control+Shift+F3); Search Next (F3); Search Previous (Shift+F3).
- **FileDir:** Search Next (F3); Search Previous (Shift+F3).
- **HomerView:** Forward Find at Cursor (Alt+F3); Forward Find with Regex (Control+F3); Reverse Find at Cursor (Alt+Shift+F3); Reverse Find with Regex (Control+Shift+F3); Search Next (F3); Search Previous (Shift+F3).

### f4 windows

- **DbDo:** Close All but Current Window (Control+Shift+F4); Close Window (Control+F4); Current Windows (F4); Exit DbDo (Alt+F4); Say Windows Open (Shift+F4).
- **EdSharp:** Close All but Current Window (Control+Shift+F4); Close Window (Control+F4); Current Windows (F4); Exit EdSharp (Alt+F4); Say Windows Open (Shift+F4).
- **FileDir:** Close All but Current Window (Control+Shift+F4); Close Window (Control+F4); Current Windows (F4); Exit FileDir (Alt+F4); Restart Windows (Alt+Shift+F4); Say Windows Open (Shift+F4).
- **HomerView:** Tab Close Others (Control+Shift+F4); Tab List (F4); Tab Names (Shift+F4).

### f5 refresh and run

- **DbDo:** Refresh Records (F5).
- **EdSharp:** Compile (Control+F5); Pick Compiler (Control+Shift+F5); Prompt Command (Alt+F5); Review Output (Alt+Shift+F5); Run (F5); Run at Cursor (Shift+F5).
- **FileDir:** Refresh Folder (F5).
- **HomerView:** List Form Fields (NVDA+F5).

### f6 panes, sections and views

- **DbDo:** View Cycle (F6); View Cycle Back (Shift+F6).
- **EdSharp:** Go to Contents (Shift+F6); Go to Section (F6); Next Section (Control+F6); Previous Section (Control+Shift+F6); Search for Topic (Alt+F6).
- **FileDir:** Next Pane (F6); Next Sibling Folder (Control+F6); Next Visited Folder (Alt+F6); Previous Pane (Shift+F6); Previous Sibling Folder (Control+Shift+F6); Previous Visited Folder (Alt+Shift+F6).
- **HomerView:** List Headings (NVDA+F6).

### f7 review and language

- **EdSharp:** Guard Document (Control+F7); Lookup Term (Alt+F7); No Guard (Control+Shift+F7); Spell Check (F7); Thesaurus (Shift+F7); Translate Language (Alt+Shift+F7).
- **FileDir:** Translate File (Alt+Shift+F7).
- **HomerView:** List Links (Shift+NVDA+F7).

### f8 selection, marking and reading all

- **DbDo:** Complete Mark (Shift+F8); Complete Unmark (Alt+Shift+F8); Copy Grid (Control+F8); Read Wide (Alt+F8); Start Mark or Unmark (F8).
- **EdSharp:** Complete Selection (Shift+F8); Copy All (Control+F8); Go to Start of Selection (Alt+Shift+F8); Read All (Alt+F8); Reselect (Control+Shift+F8); Start Selection (F8).
- **FileDir:** Complete Mark (Shift+F8); Complete Unmark (Alt+Shift+F8); Read Lean (Alt+F8); Start Mark or Unmark (F8).
- **HomerView:** Complete Selection (Shift+F8); Copy All (Control+F8); Go to Start of Selection (Alt+Shift+F8); Read All (Alt+F8); Start Selection (F8).

### f9 readable view

- **DbDo:** Record Macro (Control+Shift+F9).
- **EdSharp:** Check Markdown (Alt+F9); Preview Markdown (Control+F9); Run Code Blocks (Alt+Shift+F9).
- **HomerView:** Extract Main Content (Shift+F9).

### f10 menus

- **DbDo:** Alternate Menu (Alt+F10); Context Menu (Shift+F10).
- **EdSharp:** Alternate Menu (Alt+F10); Context Menu (Shift+F10); SendTo Menu (Control+F10).
- **FileDir:** Alternate Menu (Alt+F10); Context Menu (Shift+F10); SendTo Menu (Control+F10).
- **HomerView:** Alternate Menu (Alt+F10).

### f11 version and window layout

- **DbDo:** Elevate Version (F11).
- **EdSharp:** Arrange Icons (Alt+F11); Cascade (Control+F11); Elevate Version (F11); Tile Horizontal (Alt+Shift+F11); Tile Vertical (Shift+F11).
- **FileDir:** Arrange Icons (Alt+F11); Cascade (Control+F11); Elevate Version (F11); Tile Horizontal (Alt+Shift+F11); Tile Vertical (Shift+F11).
- **HomerView:** Elevate Version (Alt+NVDA+F11); Elevate Version (Control+F11).

### f12 ai, logs, media and macros

- **DbDo:** Chat about Table (Shift+F12); Chat with AI (F12); Copy Log (Control+F12); Play Macro (Alt+Shift+F12); Play Tutorials (Alt+F12).
- **EdSharp:** Chat about Document (Shift+F12); Chat with AI (F12); Copy Log (Control+F12); Go to Environment (Control+Shift+F12); Play Tutorials (Alt+F12).
- **FileDir:** Chat about File (Shift+F12); Chat with AI (F12); Copy Log (Control+F12); Play Tutorials (Alt+F12).

### filter and order

- **DbDo:** Add Column to Order (Alt+A); Add Column to Order Descending (Alt+Shift+A); Clear Filter (Control+Shift+F); Filter Records (Control+F); Order Records (Alt+O); Reverse Order (Alt+Shift+O); Say Filter (Shift+F); Say Filter and Order (Shift+8); Say Order (Shift+O).
- **FileDir:** Alpha Order (Alt+A); Clear Filter (Control+Shift+F); Date Order (Alt+D); Filter Items (Control+F); Reverse Alpha Order (Alt+Shift+A); Reverse Date Order (Alt+Shift+D); Reverse Size Order (Alt+Shift+S); Reverse Type Order (Alt+Shift+T); Say Filter (Shift+F); Say Filter and Order (Shift+8); Say Order (Shift+O); Size Order (Alt+S); Type Order (Alt+T).

### folders and windows tools

- **DbDo:** Context Menu (Shift+F10).
- **EdSharp:** Context Menu (Shift+F10); Environment Variables (Control+E); SendTo Menu (Control+F10).
- **FileDir:** Context Menu (Applications); Context Menu (Shift+F10); Copy to Folder (Control+Shift+C); Environment Variables (Control+E); Go to Folder (Control+G); Go to Parent Folder (,); Go to Parent Folder (Shift+Backspace); Go to Quick Folder (`); Go to Root Folder (Shift+\); Go to Special Folder (Control+Shift+G); Go to Virtual Folder (Alt+Shift+G); Move to Folder (Control+Shift+M); New Folder (Control+N); Next Sibling Folder (Control+F6); Next Visited Folder (Alt+F6); Open Folder (Control+O); Open Parent Folder (Backspace); Open Quick Folder (Control+Q); Open Root Folder (\); Open Special Folder (Control+Shift+O); Open Virtual Folder (Alt+Shift+O); Parent Folder (Backspace); Previous Sibling Folder (Control+Shift+F6); Previous Visited Folder (Alt+Shift+F6); Quick Shortcut (Control+Shift+Q); Quick url (Alt+Shift+Q); ReadOnly (]); ReadWrite ([); Recycle Bin (Control+B); Refresh Folder (.); Refresh Folder (F5); Restart Windows (Alt+Shift+F4); SendTo Menu (Control+F10); Windows Control Panel (Control+Shift+W).

### go to and open

- **DbDo:** Go to Record (Control+G); Open Cell Value (Control+Enter); Open Command Prompt (Control+\); Open Database (Control+O); Open Dot Prompt (Control+`); Open in Explorer (Alt+\); Open Table (Control+T); Open Template Database (Control+Shift+O); Open url (Control+Shift+U); Recent Databases (Alt+R).
- **EdSharp:** Choose Folder (Control+0); Go to Contents (Shift+F6); Go to Environment (Control+Shift+F12); Go to Part (Alt+Shift+G); Go to Percent (Control+G); Go to Section (F6); Go to Special Folder (Control+Shift+G); Go to Start of Selection (Alt+Shift+F8); Insert All Users Path (Control+Shift+I); Insert Script Path (Control+I); List Favorites (Alt+L); Open (Control+O); Open Command Prompt (Control+\); Open in Explorer (Alt+\); Open Other Format (Control+Shift+O); Path List (Control+Shift+P); Recent Files (Alt+R).
- **FileDir:** Drive Letter (Alt+1); Drive Letter (Alt+9); Go to Drive (Alt+G); Go to Folder (Control+G); Go to Item (Shift+Enter); Go to Parent Folder (,); Go to Parent Folder (Shift+Backspace); Go to Quick Folder (`); Go to Root Folder (Shift+\); Go to Special Folder (Control+Shift+G); Go to Virtual Folder (Alt+Shift+G); Open Command Prompt (Control+\); Open Drive (Alt+O); Open Folder (Control+O); Open in DbDo (Control+Shift+\); Open in Explorer (Alt+\); Open Item (Enter); Open Parent Folder (Backspace); Open Quick Folder (Control+Q); Open Root Folder (\); Open Special Folder (Control+Shift+O); Open Virtual Folder (Alt+Shift+O); Recent Folders (Alt+R).
- **HomerView:** Choose Browser (Alt+Shift+B); Go to Percent (Control+G); Go to Start of Selection (Alt+Shift+F8); Open Document (Control+O); Recent Pages (Alt+R).

### grid table keys

- **DbDo:** Cell Down (Control+Alt+DownArrow); Cell Left (Control+Alt+LeftArrow); Cell Right (Control+Alt+RightArrow); Cell Up (Control+Alt+UpArrow); Cell Value Down (Alt+DownArrow); Cell Value Up (Alt+UpArrow); Column Bottom (Control+Alt+PageDown); Column Top (Control+Alt+PageUp); Cursor Grid End (Control+Alt+End); Cursor Grid Start (Control+Alt+Home); Say Cell Coordinates (Control+Alt+Shift+NumPad5); Say Column (Control+Alt+Shift+DownArrow); Say Column Header (Control+Alt+Shift+UpArrow); Say Row (Control+Alt+Shift+RightArrow); Say Row Header (Control+Alt+Shift+LeftArrow); Unmark to First (Control+Alt+Shift+Home); Unmark to Last (Control+Alt+Shift+End).

### home and end

- **DbDo:** Cursor Column First (Control+Home); Cursor Column Last (Control+End); Cursor Grid End (Control+Alt+End); Cursor Grid Start (Control+Alt+Home); Cursor Row End (End); Cursor Row Start (Home); Unmark to First (Control+Alt+Shift+Home); Unmark to Last (Control+Alt+Shift+End).
- **EdSharp:** End Character (Alt+End); Home Character (Alt+Home).
- **FileDir:** Beginning File (Alt+B); Beginning File (Alt+Home); Unmark to First (Alt+Shift+Home); Unmark to First (Control+Alt+Shift+Home); Unmark to Last (Alt+Shift+End); Unmark to Last (Control+Alt+Shift+End).

### item lists in text

- **EdSharp:** Keep Unique Items (Alt+Shift+K); List Different Items (Alt+Shift+L); Number Items (Alt+Shift+N); Order Items (Alt+Shift+O); Query Common Items (Alt+Shift+Q); Reverse Items (Alt+Shift+R).
- **FileDir:** Filter Items (Control+F).

### launch from the desktop

- **EdSharp:** Launch EdSharp (Control+Alt+E).
- **FileDir:** Launch FileDir (Control+Alt+F).
- **HomerView:** Launch HomerView (Control+Alt+Shift+H).

### local ai

- **DbDo:** Chat about Table (Shift+F12); Chat with AI (F12).
- **EdSharp:** Chat about Document (Shift+F12); Chat with AI (F12).
- **FileDir:** Chat about File (Shift+F12); Chat with AI (F12).

### mail, send and web

- **DbDo:** Mail Record (Control+M).
- **EdSharp:** Burn to CD (Alt+Shift+B); Mail (Control+M); SendTo Menu (Control+F10); Web Client Utilities (Control+JAWS+Space); Web Download (Alt+Shift+W).
- **FileDir:** Burn to CD (Alt+Shift+B); Mail (Control+M); Send to Text Editor (Control+T); Send to Word Processor (Control+W); SendTo Menu (Control+F10); Web Download (Alt+Shift+W).
- **HomerView:** Web Download (Alt+Shift+W).

### marking

- **DbDo:** Complete Mark (Shift+F8); Complete Unmark (Alt+Shift+F8); First Marked (Control+PageUp); Invert Marked (Control+I); Last Marked (Control+PageDown); Mark All (Control+A); Mark and Next (Shift+.); Mark and Next (Shift+DownArrow); Mark and Previous (Shift+UpArrow); Mark Record (;); Mark to First (Control+Shift+Home); Mark to Last (Control+Shift+End); Next Marked (Control+DownArrow); Previous Marked (Control+UpArrow); Start Mark or Unmark (F8); Toggle Mark (Control+Space); Toggle Mark (Space); Unmark All (Control+Shift+A); Unmark and Next (Control+Shift+DownArrow); Unmark and Next (Shift+,); Unmark and Previous (Control+Shift+UpArrow); Unmark Record (/); Unmark to First (Control+Alt+Shift+Home); Unmark to Last (Control+Alt+Shift+End).
- **FileDir:** Complete Mark (Shift+F8); Complete Unmark (Alt+Shift+F8); First Marked (Control+PageUp); Invert Marked (Control+I); Last Marked (Control+PageDown); Mark (;); Mark All (Control+A); Mark All Files (Alt+.); Mark and Next (Shift+.); Mark and Next (Shift+DownArrow); Mark and Previous (Shift+UpArrow); Mark Duplicate Files (Alt+Shift+.); Mark Similar Files (Alt+Shift+,); Mark to First (Control+Shift+Home); Mark to First (Shift+Home); Mark to Last (Control+Shift+End); Mark to Last (Shift+End); Mark with Regex (Control+Shift+.); Next Marked (Control+DownArrow); Previous Marked (Control+UpArrow); Restore Marks (Control+Shift+S); Save Marks (Control+S); Start Mark or Unmark (F8); Toggle Mark (Control+Space); Toggle Mark (Space); Unmark (/); Unmark (Alt+Shift+NumPad5); Unmark All (Control+Shift+A); Unmark All but Current (Alt+,); Unmark and Next (Control+Shift+DownArrow); Unmark and Next (Shift+,); Unmark and Previous (Control+Shift+UpArrow); Unmark to First (Alt+Shift+Home); Unmark to First (Control+Alt+Shift+Home); Unmark to Last (Alt+Shift+End); Unmark to Last (Control+Alt+Shift+End).

### media and play

- **DbDo:** Play Macro (Alt+Shift+F12); Play Media (Control+P); Play Tutorials (Alt+F12); Record Playback (Control+Shift+P).
- **EdSharp:** Play Tutorials (Alt+F12).
- **FileDir:** Play Media (Control+P); Play Tutorials (Alt+F12); Record Playback (Control+Shift+P).

### new and save

- **DbDo:** New Copy (Control+Shift+N); New Record (Control+N); Save (Control+S); Save As (Control+Shift+S).
- **EdSharp:** New (Control+N); New from Clipboard (Control+Shift+N); Save (Control+S); Save As (Control+Shift+S); Save Copy (Alt+Shift+S).
- **FileDir:** New Copy (Control+Shift+N); New Folder (Control+N); Restore Marks (Control+Shift+S); Save Marks (Control+S).

### properties and details

- **DbDo:** Inspect Record (Alt+I); Table Properties (Alt+Enter); Table Summary (Alt+T).
- **EdSharp:** Properties (Alt+Enter).
- **FileDir:** Inquire Differences (Alt+Shift+I); Iterate Processes (Alt+I); Properties (Alt+Enter); Show Type Extended (Control+Shift+T).

### reading aloud

- **DbDo:** Read Headed from Current (Control+H); Read Headed Marked (Alt+Shift+H); Read Lean (Alt+L); Read Lean from Current (Control+L); Read Lean Marked (Alt+Shift+L); Read Wide (Alt+F8); Read Wide (Alt+W); Read Wide from Current (Control+W); Read Wide Marked (Alt+Shift+W); Read Wide Marked (Shift+Space).
- **EdSharp:** Read All (Alt+F8); Say Selected (Shift+JAWS+DownArrow); Say Selected (Shift+Space).
- **FileDir:** Read Lean (Alt+F8); Read Lean (Alt+L); Read Lean from Current (Control+L); Read Lean Marked (Alt+Shift+L); Say Selected (Shift+JAWS+DownArrow); Say Selected (Shift+Space).
- **HomerView:** Read All (Alt+F8); Say Selected (Shift+Space); Toggle Reading (ScrollLock).

### regex

- **DbDo:** Extract with Regex (Control+Shift+E); Forward Find with Regex (Control+F3); Replace with Regex (Control+Shift+R); Reverse Find with Regex (Control+Shift+F3); Yield with Regex (Control+Shift+Y).
- **EdSharp:** Extract with Regex (Control+Shift+E); Forward Find with Regex (Control+F3); Replace with Regex (Control+Shift+R); Reverse Find with Regex (Control+Shift+F3); Yield with Regex (Control+Shift+Y).
- **FileDir:** Extract with Regex (Control+Shift+E); Mark with Regex (Control+Shift+.); Rename with Regex (Control+Shift+R); Yield with Regex (Control+Shift+Y).
- **HomerView:** Forward Find with Regex (Control+F3); Reverse Find with Regex (Control+Shift+F3); Yield with Regex (Control+Shift+Y).

### rename

- **EdSharp:** Rename (Shift+F2).
- **FileDir:** Rename (F2); Rename (Shift+F2); Rename to Identify Content (Control+Shift+I); Rename with Regex (Control+Shift+R); Rename with Wildcards (Control+R); Reorder Names (Control+F2).

### repeat and next or previous

- **DbDo:** Next Marked (Control+DownArrow); Next Window (Control+Tab); Previous Marked (Control+UpArrow); Previous Window (Control+Shift+Tab).
- **EdSharp:** Next Alignment (Control+]); Next Baseline (Control+6); Next Chunk (Alt+RightArrow); Next Font (Control+Dash); Next Indent (Control+I); Next Paragraph (Control+DownArrow); Next Part (Alt+PageDown); Next Section (Control+F6); Next Sentence (Alt+DownArrow); Next Style (Alt+.); Next Window (Control+Tab); Next Word (Control+RightArrow); Previous Alignment (Control+[); Previous Baseline (Control+Shift+6); Previous Chunk (Alt+LeftArrow); Previous Font (Control+Shift+Dash); Previous Indent (Control+Shift+I); Previous Paragraph (Control+UpArrow); Previous Part (Alt+PageUp); Previous Section (Control+Shift+F6); Previous Sentence (Alt+UpArrow); Previous Style (Alt+,); Previous Window (Control+Shift+Tab); Previous Word (Control+LeftArrow).
- **FileDir:** Next Marked (Control+DownArrow); Next Pane (F6); Next Sibling Folder (Control+F6); Next Visited Folder (Alt+F6); Next Window (Control+Tab); Previous Marked (Control+UpArrow); Previous Pane (Shift+F6); Previous Sibling Folder (Control+Shift+F6); Previous Visited Folder (Alt+Shift+F6); Previous Window (Control+Shift+Tab).
- **HomerView:** Next Different Kind (Alt+Z); Next Paragraph (Control+DownArrow); Next Same Kind (Z); Next Sentence (Alt+DownArrow); Previous Different Kind (Alt+Shift+Z); Previous Paragraph (Control+UpArrow); Previous Same Kind (Shift+Z); Previous Sentence (Alt+UpArrow).

### say, on alt

- **DbDo:** Say Clipboard (Alt+'); Say Path (Alt+P); Say Position (Alt+Delete); Say Status (Alt+Z); Say Yield (Alt+Y); Say Yield Marked (Alt+Shift+Y).
- **EdSharp:** Say Address (Alt+A); Say Braces (Alt+Shift+]); Say Clipboard (Alt+'); Say Compiler (Alt+0); Say Indentation (Alt+I); Say Path (Alt+P); Say Position (Alt+Delete); Say Status (Alt+Z); Say Styles (Alt+/); Say Yield (Alt+Y); Topic (Alt+T).
- **FileDir:** Say Clipboard (Alt+'); Say Path (Alt+P); Say Position (Alt+Delete); Say Status (Alt+Z); Say Windows Open (Alt+NumPad5); Say Yield (Alt+Y); Say Yield Marked (Alt+Shift+Y).
- **HomerView:** Say Address (Alt+A); Say Clipboard (Alt+'); Say Metadata (Alt+M); Say Position (Alt+Delete); Say Position (Alt+NumPadDelete); Say url (Alt+U); Say Yield (Alt+Y).

### say, on shift

- **DbDo:** Say Added (Shift+A); Say Bookmark (Shift+B); Say Cell (Shift+C); Say Database (Shift+D); Say Edited (Shift+E); Say Filter (Shift+F); Say Filter and Order (Shift+8); Say Go to (Shift+G); Say Header (Shift+H); Say ID (Shift+I); Say Invoke Script (Shift+V); Say Jump (Shift+J); Say Keywords (Shift+K); Say Look (Shift+L); Say Marked (Shift+M); Say Notes (Shift+N); Say Order (Shift+O); Say Prime (Shift+P); Say Query (Shift+Q); Say Replace Values (Shift+R); Say Shown Columns (Shift+S); Say Status (Shift+Z); Say Tags (Shift+T); Say url (Shift+U); Say Whole Record (Shift+W); Say Windows Open (Shift+F4).
- **EdSharp:** Say Chunk (Shift+Backspace); Say Selected (Shift+Space); Say Windows Open (Shift+F4).
- **FileDir:** Say Character Encoding (Shift+2); Say Date (Shift+D); Say Filter (Shift+F); Say Filter and Order (Shift+8); Say Folder Name (Shift+'); Say Item Name ('); Say Marked (Shift+M); Say Order (Shift+O); Say Position (Shift+5); Say Selected (Shift+Space); Say Size (Shift+S); Say Status (Shift+Z); Say Type (Shift+T); Say Unarchive Test (Shift+U); Say What Content (Shift+/); Say Windows Open (Shift+F4); Say Yield on Drive (Shift+Y).
- **HomerView:** Say Chunk (Shift+Backspace); Say Selected (Shift+Space).

### scripts and macros

- **DbDo:** Edit Script (Alt+Shift+V); Invoke Script (Alt+V); Open Command Prompt (Control+\); Open Dot Prompt (Control+`); Play Macro (Alt+Shift+F12); Record Macro (Control+Shift+F9); Run Report (Alt+Shift+R); Say Invoke Script (Shift+V); Sqlean Console (Control+Shift+`).
- **EdSharp:** Compile (Control+F5); Edit Script (Alt+Shift+V); Go to Environment (Control+Shift+F12); Insert Script Path (Control+I); Invoke Script (Alt+V); Open Command Prompt (Control+\); Pick Compiler (Control+Shift+F5); Prompt Command (Alt+F5); Run (F5); Run at Cursor (Shift+F5); Run Code Blocks (Alt+Shift+F9); Save Script (Alt+S); Say Compiler (Alt+0).
- **FileDir:** Open Command Prompt (Control+\).

### search

- **DbDo:** Forward Find with Regex (Control+F3); Jump (Control+J); Keywords (Control+K); Reverse Find with Regex (Control+Shift+F3); Reverse Jump (Control+Shift+J); Reverse Keywords (Control+Shift+K); Search Next (F3); Search Previous (Shift+F3).
- **EdSharp:** File Find (Alt+Shift+F); Forward Find (Control+F); Forward Find at Cursor (Alt+F3); Forward Find with Regex (Control+F3); Jump to Line (Control+J); Reverse Find (Control+Shift+F); Reverse Find at Cursor (Alt+Shift+F3); Reverse Find with Regex (Control+Shift+F3); Search for Topic (Alt+F6); Search Next (F3); Search Previous (Shift+F3).
- **FileDir:** File Find (Alt+Shift+F); Find Duplicates in Tree (Alt+Shift+J); Jump (Control+J); Keywords (Control+K); Reverse Jump (Control+Shift+J); Reverse Keywords (Control+Shift+K); Search Next (F3); Search Previous (Shift+F3).
- **HomerView:** Find Contacts (Alt+Shift+C); Forward Find (Control+F); Forward Find at Cursor (Alt+F3); Forward Find with Regex (Control+F3); Jump to Main (Alt+NVDA+J); Jump to Main (J); Jump to Probable Main (Shift+J); Reverse Find (Control+Shift+F); Reverse Find at Cursor (Alt+Shift+F3); Reverse Find with Regex (Control+Shift+F3); Search Next (F3); Search Previous (Shift+F3).

### settings and toggles

- **DbDo:** Edit Settings (Alt+Shift+E); Key Describer Toggle (Control+F1); Read Only Toggle (Control+Shift+Z); Toggle Mark (Control+Space); Toggle Mark (Space).
- **EdSharp:** Append from Clipboard (Alt+7); Edit Settings (Alt+Shift+E); Guard Document (Control+F7); Indent Mode (Alt+Shift+I); Key Describer Toggle (Control+F1); No Guard (Control+Shift+F7); Reset Configuration (Alt+Shift+0); Set Default Font and Color (Alt+Shift+=).
- **FileDir:** Edit Settings (Alt+Shift+E); Key Describer Toggle (Control+F1); Recycle Toggle (Alt+Shift+R); Timer Toggle (Alt+Shift+Z); Toggle Mark (Control+Space); Toggle Mark (Space).
- **HomerView:** Edit Settings (Alt+Shift+E); Key Describer Toggle (Control+F1).

### space bar

- **DbDo:** Read Wide Marked (Shift+Space); Toggle Mark (Control+Space); Toggle Mark (Space).
- **EdSharp:** Say Selected (Shift+Space); Select Chunk (Control+Space); Web Client Utilities (Control+JAWS+Space).
- **FileDir:** Say Selected (Shift+Space); Toggle Mark (Control+Space); Toggle Mark (Space).
- **HomerView:** Say Selected (Shift+Space); Select Chunk (Control+Space).

### web pages

- **HomerView:** Check Accessibility (Alt+Shift+A); Choose Browser (Alt+Shift+B); Dismiss Dialog (Alt+Shift+D); Explore Page (Alt+NVDA+E); Explore Page (Y); Extract Main Content (Shift+F9); Find Contacts (Alt+Shift+C); Instruct Page (Alt+I); Jump to Main (Alt+NVDA+J); Jump to Main (J); Jump to Probable Main (Shift+J); Link Target (Alt+L); List Elements (Alt+NVDA+L); List Form Fields (NVDA+F5); List Links (Shift+NVDA+F7); List Names (Alt+N); Next Different Kind (Alt+Z); Next Same Kind (Z); Page Folder (Alt+Shift+F); Page Links to Clipboard (Alt+Shift+P); Previous Different Kind (Alt+Shift+Z); Previous Same Kind (Shift+Z); Recent Pages (Alt+R); Save Page (Control+S); Say Address (Alt+A); Say Address Anywhere (Alt+NVDA+U); Say Metadata (Alt+M); Session Log (Control+Shift+L); Submit Form (Control+Enter); Tab Names (Shift+F4); Yield Structure (Alt+Shift+Y).

### windows

- **DbDo:** Close All but Current Window (Control+Shift+F4); Close Window (Control+F4); Current Windows (F4); Next Window (Control+Tab); Previous Window (Control+Shift+Tab); Say Windows Open (Shift+F4).
- **EdSharp:** Arrange Icons (Alt+F11); Cascade (Control+F11); Close All but Current Window (Control+Shift+F4); Close Window (Control+F4); Current Windows (F4); Next Window (Control+Tab); Previous Window (Control+Shift+Tab); Say Windows Open (Shift+F4); Tile Horizontal (Alt+Shift+F11); Tile Vertical (Shift+F11).
- **FileDir:** Arrange Icons (Alt+F11); Cascade (Control+F11); Close All but Current Window (Control+Shift+F4); Close Window (Control+F4); Current Windows (F4); Next Window (Control+Tab); Previous Window (Control+Shift+Tab); Restart Windows (Alt+Shift+F4); Say Windows Open (Alt+NumPad5); Say Windows Open (Shift+F4); Tile Horizontal (Alt+Shift+F11); Tile Vertical (Shift+F11); Windows Control Panel (Control+Shift+W).
- **HomerView:** Tab Close Others (Control+Shift+F4); Tab List (F4); Tab Names (Shift+F4).

### yield (counting)

- **DbDo:** Say Yield (Alt+Y); Say Yield from Current (Control+Y); Say Yield Marked (Alt+Shift+Y); Yield with Regex (Control+Shift+Y).
- **EdSharp:** Say Yield (Alt+Y); Yield Encoding (Alt+Shift+Y); Yield with Regex (Control+Shift+Y).
- **FileDir:** Say Yield (Alt+Y); Say Yield from Current (Control+Y); Say Yield Marked (Alt+Shift+Y); Say Yield on Drive (Shift+Y); Yield with Regex (Control+Shift+Y).
- **HomerView:** Say Yield (Alt+Y); Yield Structure (Alt+Shift+Y); Yield with Regex (Control+Shift+Y).

### z keys

- **DbDo:** Read Only Toggle (Control+Shift+Z); Say Status (Alt+Z); Say Status (Shift+Z).
- **EdSharp:** Redo (Control+Shift+Z); Say Status (Alt+Z); Undo (Control+Z).
- **FileDir:** Say Status (Alt+Z); Say Status (Shift+Z); Timer Toggle (Alt+Shift+Z); Zip (Control+Z); Zip then Delete (Control+Shift+Z).
- **HomerView:** Next Different Kind (Alt+Z); Next Same Kind (Z); Previous Different Kind (Alt+Shift+Z); Previous Same Kind (Shift+Z).

<!-- key groups end -->
