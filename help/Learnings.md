# Learnings

*What building the Homer apps has taught, kept so it is not learned twice. Newest first. Started 5 November 2026 from the transition brief of 26 October and the work since.*

## 5 November 2026, night

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
