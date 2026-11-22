# Learnings

*What building the Homer apps has taught, kept so it is not learned twice. Newest first. Started 5 November 2026 from the transition brief of 26 October and the work since.*

## 22 November 2026: learnings from ScanMaster

ScanMaster is an MIT-licensed, screen-reader-first document scanner and editor by another blind developer. Its source is private; this reading is of its installed help pages and its public changelog (226 releases). Each idea is named with what Homer could do with it, in alphabetical order. None is built yet.

- **Accessibility check before saving.** Review, Check Accessibility lists errors, then warnings, then tips, by the rules of the format the file is going to become (Word, PDF/UA, EPUB with Ace, DAISY, WCAG); Enter goes to the problem. Homer: the kit's conversions could run such a check before EdSharp's Export Format and BatCon write a file.
- **Announce when settled, on change, and again while a problem stays.** Camera guidance speaks only once a view has been still a moment, only when what it sees changes, and repeats every few seconds while a problem lasts. Homer: the rule for any watched state -- progress, a long conversion, the installer's checks -- in place of a fixed four-second throttle.
- **Background work that says when it is done.** Pages are read while the next is turned; the status line counts what waits, and "All pages are ready to read" is said at the end. Homer: BatCon, transcription and Generate Graphics could work in the background and say so once, at the end.
- **Bug reports that show what they send.** Report a Bug fills a GitHub issue with the version, Windows, the screen reader and the speech engine, shows exactly what will be added, adds the log's end only when asked, with the user name hidden, and works without a token by opening the prefilled page and copying it. Homer: DbDo's File GitHub Issue could become the kit's, for every app, on that pattern.
- **Context-menu verbs from the installer.** The installer offers a right-click submenu for the files it opens: Open, Open with automatic settings, Read aloud, Save as audio. Homer: EdSharp, BatCon and FileDir could offer such verbs as finish-page boxes.
- **Crash recovery of unsaved work.** A copy of every changed document is kept about once a minute; after a crash, Yes reopens each as "Recovered", No discards, Cancel asks again next time. Homer: EdSharp, whose work is most at risk.
- **Earcons: sounds instead of words.** Short rising and falling notes mark where bold, headings, lists, tables and links start and end, so the screen reader's words are not crowded. Homer: a quiet sound on reaching a marked item in FileDir or DbDo would say "marked" without a word.
- **Keys as settings, never silently shared.** Every menu command can be given another key in a Keyboard Manager, saved in named profiles; a key already in use is moved only after asking; keys that typing needs are refused. Homer: the kit's KeyMap already knows every command; a profile layer over it would answer "I want my old FileDir keys" without forking the defaults.
- **One job, one model, editable instructions.** Each AI job (OCR, proofreading, image description, grammar, assistant) has its own provider, model and prompt, with Reset to default; a prompt left unchanged keeps following the built-in one when the program updates. Homer: the kit's local AI uses (F12 chat, descriptions, Generate Graphics' takeaway) could share such a table.
- **Pronunciation with scopes.** A word's spoken form can be set for all voices, one engine or one voice, the narrowest winning. Homer: the tutorial voices and the kit's Say could share one pronunciation file.
- **Secrets in password boxes and encrypted at rest.** API keys are typed where a screen reader does not read them aloud, and stored encrypted for the Windows account (a portable copy uses a key in its own folder, and says what that means). Homer: any token a Homer app keeps -- GitHub, AI keys -- belongs in a password box and the Windows data protection API.
- **Single letters in a read-only view.** Browse Mode makes the document read-only, and H, 1 to 6, T, L, Q and G jump to the next heading, table, list, quote or picture, Shift going back. Homer: DbDo's Inspect Record and EdSharp's read-only views could take the same letters.
- **Updates that verify and roll back.** Check for Updates offers stable, release-candidate and beta channels, opens even when current so the channel can change, checks the download's signature, swaps a portable copy in only when complete and puts every file back if the new version does not start, and logs to %TEMP%. Homer: Elevate Version (F11) could check a hash published with each release before it runs an installer.
- **Version where it is asked for.** About has a Show list (version, license, credits and third-party licenses, disclaimer) and a Copy Version button; the title does not carry the version. This is the Homer guideline of 22 November, with a button worth borrowing.

## 6 November 2026

- **A results folder holds outputs only.** Jamal moves a project's results away whenever he likes, so no script may rely on a file there; one that needs such data runs the script that makes it, at the time.
- **Look at every match, not the first.** A web page keeps hidden copies of its dialogs; the first match for a dialog's words was a hidden one while the real dialog showed, and kdpFix waited on it for two rounds.
- **Keep what a called script says.** kdpFix ran kdpSubmit and kept only its exit code; when it failed, nothing said why.
- **A file a Homer tool creates is .inix,** unless .inix cannot hold the data. The scan fingerprints went to JSON out of habit, though they are plainly sections of one-line values.
- **What a dialog shows beats what an app binds.** An app-wide Alt+letter (FileDir's Alt+Y, Yield Files) silently stole that letter from every dialog's buttons, because app commands were checked first. The access key a person can see in front of them must always win.
- **Read a page the way the script that already works reads it.** kdpFix's first run found neither Blind Vibe Coding row: it searched element ids KDP's Bookshelf does not have, and read one page of three. kdpReport had read both rows the day before; its reader, reused, was the fix.
- **Never say "the log has it" unless the log has it.** A message promised the page in the log; nothing had been written there.
- **Scan what a person meets, where it is cheap to scan.** A walk spent seven minutes on DbDo's main window, record list and all, which every push already scans; walks now scan the dialogs they open, and every scan stops at five minutes.
- **A repeated finding is one finding.** FileDir's list gave 60 of one Axe.Windows rule, and 1,086 with a longer list; reports now give each rule once, with its count and three examples.
- **The scans so far found no real fault.** FileDir's main window: list items without the ScrollItem pattern (Windows Forms' list box, not met by a screen reader user), and an unnamed list and menu bar, which the window title and the role already name.
- **A finish step should start the program, not a shell.** Two installers started their app through cmd.exe with its window shown and left a console open; the kit's template carried it to every new app.


## 5 November 2026, late

- **A script does the sensible whole with no arguments.** No parameter is to be recalled: recordWalk alone walks the pilot, scans each window and performs Tutorial 1 when its recording is due; axeWindow alone scans the app of the folder it is run from. Arguments are for the rare exception.
- **Routine checking belongs in build, tidy, push and release, as audit gates.** A manual command is for an occasional test or fix, and the gate says when one is due -- the walk check warns when the newest walk missed lines or is two weeks old -- so nothing has to be remembered.
- **No new top-level folder without the author's approval, asked in advance.** A samples folder was made in DbDo for one data file; its S clashed with scripts, DbDo's acceptance check already said no samples folder remains, and the build broke when the author deleted it. Review the existing tree first and use the folder that fits -- data for shipped data, templates for templates -- or a subfolder of an existing one; ask before adding anything at the top.
- **Never declare a folder to quiet the layout check.** The check fails a folder outside the Homer tree, and only warns when RepoFiles.txt declares it; declaring samples there turned the guard into a warning. A declaration is the author's to make.

## 5 November 2026, night

- **Anchor an insertion on a whole line, never on text that may sit inside another line.** Inserting before the first "[Database]" in nine .inix files split a comment that mentioned [Database]; DbDo's pattern audit, written after the same accident in JobTrail.inix, caught it.
- **A walk tests the installed program.** Until a build is released and installed, a walk drives the previous version; three walks in a row tested an older DbDo for that reason.
- **A new command's letter is checked against its whole menu.** "Update All from Templates" took A, already Alternate Menu's, and every word of its name began with a taken letter, so it was renamed.

- **Run the gate before delivering, not after.** The kit's tutorial check found five problems in a new walk -- Hear lines written with underscores, not as a screen reader says them, and a silent Escape -- after delivery; run first, it would have found them before.
- **A walk must say which build it walked.** Twice a walk's misses could only be explained by guessing an older DbDo had run, from the wording heard. recordWalk's report now names the program's path, version and build time.
- **One run's miss is not yet a regression.** A step heard as "Get one" passed on the next run: speech recognition slips. Judge a step over two runs before chasing it.
- **From "Improving the accessibility of scientific documents" (Allen Institute for AI):** no field had more than 6.5% of its paper PDFs meeting basic accessibility criteria, and alt text appears in only 5 to 10%; blind and low-vision readers valued headings, a table of contents, and links between citations and references above all, and wrong headings did most harm, since they break navigation and trust. The kit's PDF reader, already careful with headings, now adds the other two.
- **From the AI and accessibility literature (CSUN 2024 and 2025, CAST, the Zero Project, a 2024 systematic review):** overlays do not make inaccessible content accessible; AI-made captions and descriptions need a person's review; and people want agency -- tools that do what they ask, under their control. Homer already holds to these: homer-quality's "Needs a person", models that run on the user's own computer, and keys that do one thing.

## 5 November 2026, evening

- **A version number can claim files that never arrived.** C:\HomerDev said 1.132.0, yet its Lbc.cs predated LbcMessage: the zip that carried it was never unzipped, while later zips brought newer version files. DbDo's build now checks the kit's code for what it calls, not only the number. Every Homer app's build should do the same for the kit members it depends on.
- **Redeliver what changed, not just what is new.** When a delivery may have been missed, the next one should carry every file changed since the last build known to be good.
- **The kit's gates catch the writer's slips.** Adding a skill means listing it in AGENTS.md, llms.txt and the skills ReadMe, and updating the count; a new help page needs its byte order mark. The build said all three; trust the gates, and run them before delivering when possible.
- **From the Urban Institute's Do No Harm Guide, on data visualization:** give the meaning first and the numbers on demand, since a screen reader user hearing a table must hold each number in working memory; keep spoken text free of symbols that screen readers voice, such as pipes, slashes and semicolons; and give every chart a description -- its title and kind, then its takeaway -- with the numbers beside it.
- **From the Accessibility Metadata Display Guide 2.0:** reading systems show "ways of reading" and "conformance" first. A conformance claim belongs where it is verified -- a book that passed Ace and EPUBCheck -- not on every converted file.

## 3 to 5 November 2026

- **Read the code before stating status.** A plan's stage list had not been updated after the October work, and was reported as current: it said DbDo was not on the kit's router, when the code showed it had been since 19 October. The 26 October transition brief had it right: integration complete. Documents describe intentions; code describes facts.
- **An app's own copy of a shared capability drifts quietly.** DbDo routed every key through the kit, yet its older describer still answered first in describe mode, so the kit's never heard the key. When an app moves onto a shared component, retire the old path, not only add the new one.
- **A check run before the mode defeats the mode.** DbDo checked whether a command could run before checking whether the describer was on, so unavailable commands refused to describe themselves.
- **The repository's layout is not the installed layout.** DbDo looked for DbDo.inix beside DbDo.exe, where it is during development but not after installing, so its descriptions never loaded.
- **A rename reaches further than the code.** Renaming lookups to defs also meant: a file on disk (data\lookups.db) that the installer names; quoted table names inside triggers, which SQLite's rename leaves alone; index and trigger names; rows that name the table; an installer line deleting an old file; and English words that happen to match ("repeated lookups"), which must be guarded.
- **A migration must run before anything that opens what it migrates.** RadioTrail's conventions step expected defs and ran before the rename; old view rows still named the old table when retired. Order build steps by what each consumes.
- **Twins still drift; the gate is what catches it.** Retiring the views table changed the SQLite script in Conversion.cs but not conversion.py, and the kit's own twin check stopped the build.
- **Files mix line endings.** An edit that splits by one style misses lines in the other; edit by patterns that accept either.
- **Defaults belong in the data model, not in shipped settings that override it.** A views table DbDo created by itself, and template .inix files with saved columns and orders, hid look and prime, which are the real defaults.
- **Unauthorized additions surface late.** The views table was never approved; ask before adding a table, a key or a concept.
- **Check the suite manifest before calling a key a violation.** Alt+P, Alt+Y, Alt+Z and the X keys looked wrong in DbDo but are shared on purpose across the apps.
- **Symmetry with another app is not a reason on its own.** Keys tried to match FileDir (Alt+Shift+A, Shift+W, Shift+H) were withdrawn the same day: each must earn its key in this app.
- **Overlapping commands belong in one place.** Four analysis commands on four keys became one, Generate from Grid, with nothing lost.
- **Rehearse on copies, in the build's own order, with the user's machine state planted.** A rehearsal that planted the bad sections the real build had written caught what single edits did not.
- **Evidence from the running app beats inference.** recordWalk's 13 of 13 settled what reading code could not. Start every walk from the same state, listen until silence rather than for a fixed time, and match the essential words rather than exact sentences.
- **A pattern earns its place only if all the data fits it.** 111 field patterns were kept because every existing record matched; "required" goes only on the field that names a record.
- **A message box is a dialog too.** 109 Windows message boxes could not answer Alt+Shift+Slash until they became Lbc dialogs.

## Until 26 October 2026 (from the transition brief)

- **A kit in the wrong place misleads everything that climbs to find one.** Every lookup now follows one rule, and tidy clears stray copies.
- **A fix can be written and never wired in.** When a failure repeats, search for code that already handles it.
- **A check that tests order but not presence lets absence pass.**
- **Run the path you rarely run.**
- **The console must never go quiet for minutes:** say what is being waited on, every 30 seconds.
- **A window must stay responsive during long work:** give it its own thread.
- **Twins drift unless a build checks them.**
- **Readiness must be checked, not promised.**
