---
title: "HomerDev History"
author: "Jamal Mazrui"
---

# History

Each version is a level-2 heading, newest first, so your screen reader's heading keys move from one version to the next.

## 1.92.1 -- 24 October 2026

- **extCheck's Word, Excel and PowerPoint rules are in the kit,** as OfficeCheck in Quality.cs, reading each file's XML rather than driving Office, with extCheck's rule names, wording and thresholds. Every Word, Excel and PowerPoint file the kit makes is now judged by them, as Markdown already was, through one door, QualityCheck. ColorUsedAlone and Word's own help text for a form field need Office and stay in extCheck for now. extCheck itself still uses Office for those files; moving it onto OfficeCheck waits until the two have been compared on the same files.
- The 1.92.0 build compiled the conversion classes with Quality.cs for the first time: the finishing code of 1.91.0 and 1.91.1 is sound.

## 1.92.0 -- 24 October 2026

- **An app's build uses the newest kit it finds.** Once the HomerDev variable was honoured (1.89.1), it named an installed kit in Program Files at 1.77.6, and BatCon's build stopped although C:\HomerDev held 1.91.0. Every build now considers the variable, C:\HomerDev and the folders above it, logs each kit it finds with its version, and uses the highest. Fixed in both build templates and in 2htm, BatCon, extCheck, HomerScribe, urlCheck and urlFido.
- **extCheck's Markdown rules live in the kit,** as MarkdownCheck in a new Quality.cs, moved word for word but for its two calls out. extCheck runs them from there, and Conversion runs them on every Markdown file it makes, finding them in the program at run time, so Quality.cs stands alone and an app without it still builds. The kit's check warns an app that compiles Conversion without Quality.
- **The conversion classes compile in the kit's build.** Nothing in the kit compiled Conversion.cs before: the C# 5 scan read it and the conversion test ran its Python twin. A compiler error in the shared C# now stops the kit's build instead of the next app's.
- **Every PDF made is checked for tags and a language,** from IsTagged in KeyLine: a structure tree, the marked-content flag and /Lang, reported as UntaggedPdf and MissingDocumentLanguage.

## 1.91.1 -- 24 October 2026

- **Workbooks laid out for reading, from xlFormat.vbs in KeyLine.** A workbook with no styles of its own -- one the kit's writer made -- gets columns as wide as their text up to 40 characters, longer text wrapped, a bold header row and every row set to the top. A formatted workbook is left alone. xlFormat deleted columns with blank headers; the kit keeps them and reports BlankOrGenericColumnHeader.
- **Word tables with header rows and header bookmarks, from docxIt in KeyLine.** A table whose first row is distinct text has it marked as the header row, its header-row style on, and a numbered ColumnTitle or Title bookmark for JAWS; docxIt's one ColumnTitle name for every table could hold only the last. A table without such a row is reported, TableMissingHeaderRow.
- Tested in Python: openpyxl and python-docx read the finished files, and finishing a file twice changes nothing the second time.

## 1.91.0 -- 24 October 2026

- **Every file a Homer app makes is finished for a screen reader, then checked.** Whatever engine wrote it, the kit opens it once more, in Conversion.cs and conversion.py alike, gives it a title, an author and a language where it has none, and logs what it cannot fix under extCheck's own rule names: a document without headings, a skipped heading level, a picture without alternative text, a slide without a title, merged cells. Markdown gets front matter; an EPUB gets a title from its first heading; Word's PDF export now asks for structure tags and heading bookmarks.
- **Header names in every workbook,** from the author's xlHeaders.vbs, now without Office and improved. JAWS and NVDA read column and row headers in a table whose top-left cell is named ColumnTitle, RowTitle or Title. The kit names every table region in every .xlsx it makes, recognizes a two-way table with an empty top-left corner (which xlHeaders missed), takes only text for headers, freezes the first table's headers, and names a lone default sheet for its file.
- **Databases in DbDo's form.** The sqlite engine makes a plural lower-case table with its singular id, added and edited, typed data fields, url, notes, tags, look, prime and marked, the edited and maps triggers, a unique prime index, and DbDo's lookups, maps and views. checkDb passes one with no warnings. checkDb now knows the irregular plurals the engine uses, so people has person_id.

## 1.90.0 -- 24 October 2026

- **Any two types convert, PDF included, with the same code in every app.** The author's rule: every Homer app converts between any pair of the types the kit knows, by their usual Windows extensions and .inix, with one shared conversion. The route table names 100 pairs; a pair it does not name, or whose every way fails, now goes in two of its own steps through Markdown, else a web page, in Conversion.cs and conversion.py alike. Of the 216 pairs from the 19 source types to BatCon's 12 targets, all but seven can be made; the seven are JSON to a table, EPUB or PowerPoint.
- **A PDF without Office.** A new engine, edge, has Microsoft Edge print a web page to a tagged PDF, headless and with a profile of its own. md2pdf and htm2pdf use it first; docx2pdf and odt2pdf keep Word first and use it when Word is missing. Every route that made a PDF used to need Office.
- **SQLite databases in and out.** A new engine, sqlite, makes a database of one table from a table, and turns a database into Markdown, each table under its heading. It is one Python script that both languages run, and the kit's build fails if the C# and Python copies ever differ. New routes: csv2db, inix2db, md2db, tsv2db, xlsx2db and db2md.
- **.htm, never .html, in Python too.** Python's typeOf now reads .html as .htm and .markdown as .md, as C# always did, so a Python app and a C# app take the same route for the same file. The four html2 sections, which could no longer be reached, are gone.
- **Every Homer app is held to the kit's conversion.** conversionsMoved now lists all eleven apps, so private conversion code fails any app's check rather than warning.
- **The kit's agent files have no byte order mark again,** and AGENTS.md counts 22 skills. The 1.89.1 build stopped on both.

## 1.89.1 -- 24 October 2026

- **The build scripts find the kit only where the kit is.** A new app's build climbed from its folder looking for any folder with exec\CSharp\Lbc.cs, and took C:\ itself for the kit when such a folder was there; BatCon's build then stopped with "kit 0.0.0 is older than 1.89.0". A kit is now a folder with HomerDev.cs at its top as well, C:\HomerDev is tried before any climbing, and the top of a drive is held as "C:" so no path doubles its backslash. Fixed in both build templates, build_APP_.cmd and build_APP_Py.cmd.
- **The HomerDev environment variable works.** Names in cmd ignore case, so the build's own `set "homerDev="` emptied it before it was read; it is now read first.

## 1.89.0 -- 23 October 2026

- **A field in a band is named again.** Lbc put a band field's label on the main stack, after the band, so the screen reader met the box with no name, then the band's button, then the stray label. That is why a launch app's Source paths box said nothing on Insert+Tab, its Browse button seemed to come first, and its Output directory box seemed to be missing. The label now goes into the band, just before its box, and the box is narrower so the row fits.
- **Bands wrap, and the dialog widens to fit them.** A band reads left to right; the dialog grows to its widest band, up to 900 pixels, and a wider band continues on the next line in the same order.
- **Help, F7 and Control+Home reach controls inside bands.** Three places still read only the top of the dialog.
- **One launch dialog for every launch app.** The new LaunchDialog class builds the source, output, operation and command bands, puts OK and Cancel alone at the bottom right, gives every standard control the same Alt letter in every app, presses OK with Control+Enter and Cancel with Escape from any control, and checks the version with F11 from anywhere. Its Help box says where the logs are, since logging is now automatic. Following Microsoft's dialog guidance, Help and Default settings sit in a band of their own rather than beside OK and Cancel. help\LaunchDialog.md explains each choice.
- **Every launch ends with one Results box,** LaunchDialog.showResults: titled with the app's name and Results, one focused OK button, and a long report cut to its first 15 lines with the rest in a file.
- **One progress window for every launch app,** LaunchProgress, from HomerScribe's rules, 2htm's and urlFido's windows and Microsoft's progress guidance: the title says "<App>, <status>"; a read-only Status box holds the focus; Cancel has no letter and Escape presses it; the status is spoken only while the app is the window in front, so work in another program is never talked over, and coming back speaks it once; the first three messages and every change of phase are spoken at once, later steps at most every five seconds with the newest winning; counts say work done, with the percentage done and, once it can be estimated honestly, the time left ("Budget.pdf, 2 of 5 done, 40%, about 3 min left"); the window has a real progress bar, as Microsoft asks, and the percentage is spoken too, because that is how a screen reader user receives a progress bar -- a deliberate, small departure from Microsoft's guidance, the author's ruling; times are said in HomerScribe's words, "11 min", now shared as LaunchProgress.spokenTime; every update pumps the message queue; every status is logged with whether it was spoken. The StatusBar-role labels it replaces were not reliably spoken.
- **Force replacements works one way in every launch app,** documented in LaunchDialog.md with why it sits first in the operation band: unchecked, a source whose result is there is skipped and kept, and the Results box says so with the kit's LaunchDialog.keptLine; checked, the work is redone and the old result kept aside until the new one is complete. Every app's tip is now the kit's LaunchDialog.forceTip.
- **Learnings from Microsoft's UWP guidelines** are in help\LaunchDialog.md.
- **A new skill, homer-launch-dialog,** with checkLaunch, which the kit's check runs on every app: a launch app fails when it does not use LaunchDialog, does not end with the Results box, or keeps a Guide button, a Log session checkbox, an Include subfolders checkbox or the old Browse source and Choose output captions; and when it does not use LaunchProgress, or still builds a StatusBar-role progress label.

## 1.88.7 -- 23 October 2026

- **Install with every default however it is typed.** An installer's default switch is now d, default or defaults, in any case, with or without leading slashes or hyphens: /default, -d, --default and plain default all work, where /d, --d and a bare word did not. The punctuation is stripped and the whole word compared, so none of Inno Setup's own switches, such as /dir=, can match.

## 1.88.6 -- 22 October 2026

- **The kit's Python starts no console windows.** Every tool conversion.py runs -- Pandoc, Whisper, ffmpeg, Tesseract, PowerShell -- now runs without one, so a windowed program converting through it, such as NVDA running HomerView, shows nothing over the user's work.
- **HomerView converts through the kit,** carrying conversion.py and conversions.inix in its add-on.

## 1.88.5 -- 22 October 2026

- **Two cycles of one project cannot corrupt each other's runner.** On 22 October a FileDir cycle spent over an hour speaking its tutorials; a second started beside it, and when the second failed it replaced build_release.bat under the first. Windows reads a running batch file a piece at a time, so the first went on from the middle of the new file: it ran its build again, wrote into the wrong log, and lost its timers -- the cause, too, of the earlier -33s and -36s step times. Now a cycle replaces build_release.bat, and removes the lock, only if it still holds the lock itself.
- **Unlock does not clear a cycle that is running.** build_release unlock clears a lock whose holder is gone; for a holder that is alive and older than the lock, it says a cycle is running and shows that cycle's latest log line, so a long step is seen to be working. build_release unlock force clears it regardless. A refusal shows the running cycle's latest line too.

## 1.88.4 -- 22 October 2026

- **The suite manifest lists DbDo's Count by Columns,** Alt+Shift+B, the first of the four DbDialog features accepted on 19 October.

## 1.88.3 -- 22 October 2026

- **The FruitBasket samples find the Build Tools' Roslyn.** Their compiler paths said Buildscripts for BuildTools, the remnant of a replace that turned Tools into scripts, so on a computer with only the Build Tools they fell back to the .NET Framework's C# 5 compiler. FileDir had the same fault, which is why it alone rejected ConversionPage.cs's newer syntax.
- **The kit's C# stays C# 5,** decided for the plan's Roslyn item and written in AGENTS.md: every build prefers Roslyn, and the kit's code still builds with the older compiler should a build fall back to it.

## 1.88.2 -- 22 October 2026

- **The PdfPig step runs the kit's own getPdfPig,** not the copy refreshed into an app's scripts: 2htm's and FileDir's builds refresh their kit scripts after compiling, so the step found nothing and stopped.
- **A cycle's step time is measured by PowerShell itself,** from a full timestamp, and both the stamp and the seconds go in the cycle log. Renaming the timers (1.87.6) did not cure the negative times: every step of a cycle still read -36s, so the values were not being renewed, and nothing showed why. A wrong time can now be traced; a time that cannot be measured says so.

## 1.88.1 -- 22 October 2026

- **getPdfPig keeps an app's own config.** -Base names a config the app authors (FileDir.exe.config): its settings are kept, and the binding redirects go into its runtime section; FileDir's build used to copy its config over the written one after compiling, which would have dropped PdfPig's redirects.
- **getPdfPig writes no redirect for a library without a strong name.** It wrote one for every library beside the program, and an unsigned one, such as FileDir's Ude or Tektosyne, would have given an empty public key token, a malformed config that can stop the program from starting.
- **2htm and FileDir read PDFs with the kit's PdfReader,** after BatCon proved the way on 22 October.

## 1.88.0 -- 22 October 2026

- **One PDF reader for every app: scripts\\getPdfPig.** PDFs were read two ways across the suite -- the kit's own PdfReader in bookFido and HomerScribe, PyMuPDF4LLM in the rest -- so a PDF could come out differently by app. getPdfPig, taken from HomerScribe where it was proven, fetches PdfPig 0.1.16 with every assembly its packages name into exec, and writes <App>.exe.config with the binding redirects they need; -App names the program, and packages unpack under work\\packages. BatCon is the first to use it, compiling ConversionPdf and PdfReader; DbDo, EdSharp, FileDir and 2htm follow once BatCon's build proves it.

## 1.87.7 -- 20 October 2026

- **KeyMap.bRunningCommand** is true while runCommand clicks a command's menu item for a key. An app whose menu items are its commands resets the press count to one on a click only when it is false, so a menu chosen by hand is one press while a routed key keeps its count of two or three. DbDo uses it as its Say keys move onto KeyMap.answer.

## 1.87.6 -- 20 October 2026

- **A cycle times its steps correctly.** build_release timed each step with variables named iStart and iEnd, in the same environment as the build it calls, and something the build runs set one of them, so DbDo's 50-minute build was logged as -33s. The runner's timers now have names of their own.

## 1.87.5 -- 20 October 2026

- **Every converting app compiles the whole conversion bundle:** Conversion with ConversionMedia, ConversionPage, Media, Table and Voice. EdSharp, bookFido and 2htm gain the media half, so a recording becomes a transcript and a document becomes speech in them as in every app. check.py's conversion check now fails an app whose build compiles Conversion without the rest of the bundle, and names what is missing; all six converting apps pass. The manifest lists all six as moved onto the kit's Conversion, 2htm, BatCon and bookFido among them.

## 1.87.4 -- 20 October 2026

- **2htm is a face over Conversion.convert,** the third and last step of its move onto the kit: its 3,338 lines of its own converters are retired into its notes\\retired, and Markdig is no longer fetched. Comma and tab separated tables reach a web page without Pandoc, through the table as Markdown and the markdown engine, as 2htm always did.

## 1.87.3 -- 20 October 2026

- **ConversionPage.cs is C# 5,** so DbDo, EdSharp and FileDir, which compile with the .NET Framework's own compiler, build again. Moved from 2htm, it used out var, patterns such as `is bool b`, the discard `out _` and expression-bodied members, which that compiler rejects; BatCon and bookFido, compiled with Roslyn, had accepted them. Each is rewritten with the same logic.
- **The kit's build checks that its C# is C# 5:** a scan of exec\\CSharp, comments and strings set aside, fails the build on any C# 6 or 7 form and names the file, since the kit's own Roslyn compile cannot notice what the older compiler rejects.
- **Python's table engine writes documents as C# does,** Word, web page, OpenDocument, rich text and EPUB, through Markdown and Pandoc; a new inix2txt route takes an inix table to text. The conversion test's sample table gains the marker row its workbook sample already had. Six table routes failed the test on the author's computer; all 54 routes this computer can test pass.

## 1.87.2 -- 20 October 2026

- **The convention-walking-guide skill learns from the host's own walkthrough.** The NFB of Virginia's own handout for its 2026 hotel, written by members who walked it, knew what the skill's map-based example did not: where the carpet starts and ends, that a key card calls the elevators, the building's one-floor shape, a central intersection described right, left and straight, doors by their order, steps and surface at relief, and volunteers as talking signs -- in 800 words. A new section tells the skill to ask for such a handout early, prefer it for route order and procedure, and adopt its strengths within a tasks-first guide; the template opens with the basics and names people who help; the handout is a method example; and the NFB example's worksheet lists the facts for its next revision.

## 1.87.1 -- 20 October 2026

- **Every web page the kit makes is in the Homer page form,** 2htm's: a page made by Pandoc, the markdown engine or any other way is finished with the base stylesheet, one H1, main labelled by it, headings moved under it, and images inlined or removed (images on the web are removed, as 2htm always has, so a page stands alone). The body's first H1 becomes the title first, so a Pandoc page titled by its file name still reads H1 the real title. In C# and Python alike; every converting app (BatCon, bookFido, DbDo, EdSharp, FileDir) now compiles ConversionPage.cs, so the same conversion makes the same page in every app.
- **Python has the page and json engines,** ported line for line. Tested here: Markdown through Pandoc came out with one H1, the real title, French kept; JSON became nested lists; a messy page lost its script, style, comment and web image, its German kept.

## 1.87.0 -- 20 October 2026

- **2htm's page form joins the kit,** the first step of 2htm becoming a face over Conversion.convert. ConversionPage.cs holds 2htm's page writer (the base stylesheet, a head with title and language, main labelled by the title, headings shifted under one H1, images inlined or removed, tables with headers), its clean-up of an existing web page, and its JSON converter, as two engines: page (htm to htm or txt) and json (json to htm or txt). An app that compiles the file has them; BatCon does from now on.
- **Routes 2htm needed:** htm2htm, json2htm and json2txt are new; text, OpenDocument, PowerPoint and Excel reach a web page without Pandoc through the markdown engine, a web page reaches text through the page engine, and Markdown reaches text by a copy.

## 1.86.0 -- 20 October 2026

- **Python converts as C# does.** conversion.py gains the table engine, reading and writing comma separated, tab separated, inix, Markdown tables and Excel workbooks in the same layouts as Table.cs, with the same formula guard and every workbook value kept as text; and the media half, with the same tools called the same way: Whisper for transcripts, HomerScribe for described video, Windows' own speech synthesis (through PowerShell) for audio and video from documents, and ffmpeg between media. canConvert answers for both halves. Tested here: a CSV with leading zeros, formula-like text and accented letters went to a workbook and back, to inix, Markdown and tab separated, and openpyxl read the workbook exactly; WAV became MP3 by ffmpeg; a missing Whisper was reported by name.
- **A missing tool is named.** A program the converter cannot start, or one that runs too long, is reported in words, not as Python's own error.

## 1.85.2 -- 20 October 2026

- **A video becomes a described document.** When HomerScribe is installed, the kit asks it for both halves of a video -- what is said and what can be seen -- and makes them one document, with headings for each, in any document format. HomerScribe is the kit's engine for description as Pandoc and Office are for documents, so the suite keeps one technique for it, in one program, rather than a copy here. Without HomerScribe, a video gets its transcript alone, and the log says why. A context file named after the video, beside it, still tells HomerScribe what it is watching.
- **Paths.homerProgram** finds another Homer app's program; SuiteCommands.homerProgram calls it, so media conversion can find HomerScribe without the window frame.

## 1.85.1 -- 20 October 2026

- **The kit build proves the app template.** It makes a throwaway app with newHomerApp in the temporary folder and compiles it as a new app's build would: its source, a Version.cs like the build's, and the kit modules the build template names. A template that would not compile now fails the kit's build, before anyone makes an app from it. It runs only when the template, newHomerApp or one of those modules has changed. BatCon, the first app made from the template in weeks, showed why: each of its first builds found one more thing the template had wrong.

## 1.85.0 -- 20 October 2026

- **/default installs as Enter on every screen would, with nothing to press,** in every Homer installer: `/default`, `/defaults`, `-d` or `--default`, in any case. Setup started with screens starts itself again silently with the same switches -- a progress window, every default taken, each default-ticked finish-page entry run, the Results box logged -- closing a running copy of the program first, which is the likeliest reason the first such restart failed on DbDo on 13 October. The second copy writes its own log in %TEMP%, named in the first's. In HomerComponents.iss, so every installer gains it at its next build. FinishPage.md says how.
- **Correction:** the kit build does not compile an app made by newHomerApp; the logs that suggested it came from a test outside the build. A build self-test that does is queued.

## 1.84.1 -- 20 October 2026

- **The app template's dialog is 2htm's and extCheck's,** the pattern of every Homer launchpad app, after the author's audit found BatCon had drifted from it by following the template. Source files and Output directory share a band with Browse source and Choose output; a separator; the app's own options; Force replacements, View output, Log session and Use configuration; then OK, Guide, Default settings and Cancel, with Lbc's Help and its version check, and F11. Source files starts at Documents, and Output directory follows the source until the user chooses another. Settings are kept only when Use configuration is checked at OK. The AI note now says to convert only through Conversion.convert, and gives Camel Type's c_ prefix for constants, which it had denied.
- **A new app's build no longer stops on its tutorial fingerprints.** buildTutorials writes <walk>.sha256 beside each mp3 to know whether a walk changed; the build's check that every help file is installed now leaves those out. BatCon's first build that spoke its walks stopped on all ten.

## 1.84.0 -- 20 October 2026

- **Speech becomes text, and text becomes speech, through the one conversion technique.** An audio or video file converts to a transcript as plain text, Markdown, a web page, Word, PDF, OpenDocument, rich text, EPUB or Word 97: ffmpeg takes the sound, Whisper transcribes it on this computer (Voice.transcribe), and the route table takes the Markdown to the target. A document converts to MP3, M4A, WAV, Ogg, FLAC or Opus by Windows' speech synthesis and ffmpeg, or to MP4, Matroska, WebM or QuickTime video, the speech over a plain black picture. Describing what a video shows is still HomerScribe's own, to move into the kit next.
- **Conversion.canConvert** answers for the route table and the media half together, and **allTargets** now lists the media formats too, so a picker or a batch sees everything the kit can make.
- **An app that compiles ConversionMedia compiles Voice.cs too;** DbDo's and FileDir's builds do. Speech synthesis is reached by reflection, so no build needs a new reference.

## 1.83.0 -- 20 October 2026

- **Conversion.allTargets lists every type the kit can make,** with its readable name, alphabetically by name, for a picker that offers every target before any source is known. BatCon's Target format is filled from it, and asks hasRoute for each file at run time.

## 1.82.2 -- 20 October 2026

- **A new app's build stops when its tutorials cannot be spoken,** as DbDo's always has. The build template only said "Not every tutorial could be spoken" and went on, so BatCon's first release went out without its tutorials while the cycle reported that every step had passed. Now the build names the checker's log and stops before the installer.

## 1.82.1 -- 20 October 2026

- **Python converts as C# does, for web pages.** conversion.py has the markdown engine too, ported line for line from Conversion.cs, so a Python app without Pandoc also makes a web page from Markdown or a PDF. Tested on Markdown like PdfReader's: its page matches Pandoc's in structure, and adds a main landmark, column headers in tables, and the title from the first heading.

## 1.82.0 -- 20 October 2026

- **A new app's first push makes its repository.** A new kit script, createRepo, runs the app's own create<App>Repo.cmd, or first writes one from the kit's Templates\create_APP_Repo.cmd and .ps1, with the app's name in place, as newHomerApp does. Those templates stay local-only, by the author's rule, so createRepo holds no account details; where they are absent it says so and stops. push calls createRepo by itself when a folder is not yet a repository, so a new app's first build_release goes all the way through. BatCon, made from a zip rather than newHomerApp, showed the gap: its push could only say to run a script it did not have.
- **The app templates take createRepo with the other kit scripts,** and list the generated create<App>Repo.cmd and .ps1 as local files, never pushed.

## 1.81.1 -- 20 October 2026

- **A new app's installer ships its tutorial walks.** The installer template shipped the help pages, the spoken tutorials and their feed, but not the Tutorial_*.inix walks themselves, so the build's check that every app file is installed stopped BatCon's first build on all ten. FileDir already shipped them; the template now does too.

## 1.81.0 -- 20 October 2026

- **A PDF becomes a web page without Pandoc.** A new engine, markdown, writes the Markdown the kit makes as an accessible page: headings, paragraphs, lists, tables, quotes, code, links, images with their alt text, and the language and title from front matter, inside main. It is the second way for md2htm and pdf2htm, after Pandoc, so a computer with Pandoc keeps Pandoc's page. It let bookFido move its companion PDFs onto the kit's one conversion technique without needing Pandoc on every computer.
- **A PDF's language travels with its Markdown.** PdfReader.toFile writes it as front matter, which Pandoc and the markdown engine both put on the page, so a screen reader picks the right voice.

## 1.80.3 -- 19 October 2026

- **A new app's first build keeps its version.** Before any release there is no tag, and cmd turns a substitution on an undefined variable into literal text, so the build template set the version to "v=" and the compiler refused "v=.0.1" (the first BatCon's build). The template now strips the v only from a tag that exists and ignores a tag that is not a version number; DbDo's and EdSharp's builds carry the same fix.

## 1.80.2 -- 19 October 2026

- **One conversion technique, in every app.** Conversion had three entry points that did different things: convert used the route table alone (DbDo, EdSharp), convertAny tried media, then the table, then text through Pandoc (FileDir), and convertFile was Pandoc alone (BatCon's first build, a mistake the 1.80.0 documents repeated). Now convert does the whole sequence, and convertAny and convertFile are the same function under older names. AGENTS.md states the rule: an app converts only through the kit, and a missing or poor conversion is fixed in the kit.

## 1.80.1 -- 19 October 2026

Found while making BatCon with newHomerApp, the way the kit now tells every agent to.

- **A picker lists every format a file converts to.** Conversion.targetsFor gave only a fixed menu per kind of file, so routes in conversions.inix such as inix2xlsx and md2pptx never appeared; ChatGPT's BatCon read the table itself because of it. The menu still comes first, in FileDir's order; every other route for the file's type follows, by the kit's name for that type.
- **The app templates do what homer-new-app says.** _APP_.cs starts the log, Paths and Elevate first, keeps its settings through Paths, and reads switches through the new Util.switchName, documented as /switch; the acceptance checks use /help and /source. newHomerApp sets kitNeeded to the kit it was made from, not a version weeks old, and its closing hint names runJob().
- **A new app's build and installer agree.** The build template copies the scripts its installer runs (installCommon, installOllama, installScreenReaderSupport), and an app that compiles Conversion gets exec\conversions.inix copied by its build and shipped by its installer. A stray bare line feed in the installer template is gone.
- **Util.switchName** gives a switch's name in lowercase whatever its prefix, /, - or --, so every app follows the one convention through one copy.

## 1.80.0 -- 19 October 2026

Learned from BatCon, an app another AI (ChatGPT) built from the kit's documents alone. It did much right, and showed where the kit did not describe itself.

- **The kit says its most important rules first.** AGENTS.md opens with them: use the kit and never copy it; change the kit itself and deliver HomerDev.zip when it lacks something; read homer-new-app to make an app; ask whether the kit already does a thing before writing it; no new top-level folders; one switch convention. A stray carriage return in it is gone.
- **homer-new-app covers working without the kit on the machine,** listing what newHomerApp would have written, and gives the kit's answer to common needs: the format list, conversion, settings, dialogs, speech, the log, updates and the suite's shared commands.
- **Conversion.cs names the functions a dialog or a batch should call,** such as targetLabelsFor for a format picker. BatCon had parsed conversions.inix itself, for want of that list.
- **The shared check fails a project that copies the kit, or cannot find it** (the new kituse check). BatCon's copy had made five comparison checks skip unseen. A declared folder outside the Homer tree is now a warning rather than a quiet pass.
- **One command-line switch convention,** in homer-code: lowercase words documented as /switch, with /, - and -- all accepted in any case.
- **From BatCon's own kit changes, reviewed and adopted:** Table writes .xlsx, a minimal workbook keeping every value as text (it replaces an earlier file rather than failing); nine table routes among CSV, inix, Markdown, TSV and XLSX; and every text conversion ends in the Homer encoding, UTF-8 with a byte order mark and CRLF, in C# and Python alike. The new table routes are C# only for now, since Python has no table engine yet; its conversion test reports them as not tested.

## 1.79.2 -- 19 October 2026

- **Installer scripts write one log per run.** finish.cmd, installScreenReaderSupport.cmd and the installModels.cmd template appended every install to one <App>_setup.log; each now writes <App>-<script>-<yyyymmdd-hhmmss>.log, as installCommon.cmd and help\Logging.md already had it, so the logs folder sorts by time and zips whole.

## 1.79.1 -- 19 October 2026

- **Old PowerPoint and Excel files convert to Markdown and web pages:** ppt2md, ppt2htm, xls2md and xls2htm. Office makes the newer format, its last resort, then the kit reads that as its .pptx or .xlsx route does. They let EdSharp retire its last private converters.

## 1.79.0 -- 19 October 2026

- **One Homer app can hand a file to another.** SuiteCommands.homerProgram finds another Homer app's program, under its Program Files folder or in Windows' App Paths, and openInHomerApp starts it on a path; each app is a single instance, so a running copy is handed the path. When the app is not installed, a message says so and points to the HomerDev dialog. FileDir's Open in DbDo and DbDo's Show in FileDir use it, both on Control+Shift+Backslash.

## 1.78.2 -- 19 October 2026

- **An installer knows EPUBCheck's version.** It is a .jar, which cannot answer --version, so every install said "its version could not be read". HomerComponents now reads a version.txt beside a component's file first, which EPUBCheck's install script already writes, and asks only a program (.exe or .cmd) for --version.

## 1.78.1 -- 19 October 2026

- **The shared check catches an install script that can leave a console waiting.** A finish-page entry that runs an install script must pass noPause (or, for installJawsScripts, -bQuiet) and must not use nowait. Inno runs these entries after the wizard has closed, so a script that pauses at its end leaves a console waiting for a key with nothing behind it. DbDo's Ollama and model entries did exactly that.

## 1.78.0 -- 19 October 2026

- **A new skill, convention-walking-guide,** researches and writes a walking guide to a convention's hotel for blind white cane and guide dog users, with a separate organizer worksheet. It was developed with ChatGPT on two 2026 Virginia state conventions, whose guides and worksheets are its worked examples. Every main section of a guide is a task a traveler sets out to do; a sort by place is allowed only in an appendix that links back to the tasks.
- **The HomerDev dialog lists every Homer project.** Run setup installs or updates the one you are on from its newest release on GitHub, and Download saves its installer in your Downloads folder. The download runs in the background, so the dialog keeps answering, and the list comes from the new data\Projects.inix.
- **The skills list is complete:** convention-database and readable-text were missing from the skills ReadMe.

## 1.77.7 -- 19 October 2026

- **An installer says "current" when winget says so.** winget's list fills its Available column only when an upgrade exists, so a component it lists with that column empty is the newest it knows. HomerComponents.iss logged each such component as "no newer version could be looked up": 17 of 19 in Jamal's setup log of 19 October, though ImageMagick, offered as an Update the day before, showed the comparison works. They are now logged "found, current (version is the newest)". The boxes were already right: Reinstall, unticked.

## 1.77.6 -- 19 October 2026

- **FileDir's suite names and keys are recorded as done** in the manifest: 51 entries, from Tag to Mark and Regular Expression to Regex, to the clipboard family, Edit Settings and Edit Settings File. Its F6 family, Play Tutorials and Open in DbDo are still to come.

## 1.77.5 -- 19 October 2026

- **PDFs keep their links, form answers and drop caps,** learned from FRAME PDF Studio (help\Conversions.md says what was taken and what was not). PdfReader makes a PDF's web and mail links into Markdown links on their words, lists a fillable form's fields with their values, and joins a large first letter back to its word instead of making it a heading. HomerScribe and Conversion's pdfstructure and ocr routes get all three; rebuild HomerScribe to take them up.

## 1.77.4 -- 19 October 2026

- **A command whose name ends in Properties is not echoed,** since its window names itself, as Alt+Enter's does throughout Windows. This closes the Window group's gap that DbDo's Table Properties showed.
- **The CommandEcho review is decided,** in help\CommandEcho.md: DbDo's copy commands and Delete Record tell you themselves, so they are Result; Table Properties is Window.

## 1.77.3 -- 19 October 2026

- **The build says when it starts packing HomerDev_setup.exe.** That last step runs quietly for minutes, and the console looked stuck after "Built exec\HomerDev.exe". It now says what it is doing, and that an app's build can start.

## 1.77.2 -- 19 October 2026

- **Python finds the same Pandoc as C#.** conversion.py asked the PATH first and could pick an old Pandoc (2.19.2 in c:\bin on Jamal's computer) over the machine-wide 3.12.1 that Conversion.cs uses. Both now look in the machine-wide folder first, then the PATH.
- **DbDo's suite commands are recorded as done** in the manifest: the clipboard family, Copy Log, Say Time, Say Path, Play Tutorials on Alt+F12, Export Data on Alt+Shift+X, the url and Go to names, and the second keys for Say Yield and Open Command Prompt.

## 1.77.1 -- 19 October 2026

- **DbDo converts through the kit.** It compiles Conversion.cs, ConversionMedia.cs and Table.cs and ships conversions.inix, and the shared check now fails it, as it does EdSharp and FileDir, on any private conversion code.
- **A tutorial build no longer hangs joining its pieces.** EdSharp's build of 18 October stopped for good after speaking a walk's 128 pieces, in the ffmpeg run that joins them into the mp3. Without -nostdin, ffmpeg watches its standard input for a keypress, and run from a script with no input given it can wait there forever. Every ffmpeg run in buildTutorials now passes -nostdin, and the log says when the join starts.

## 1.77.0 -- 19 October 2026

- **Every pending key decision is settled,** by best judgment under the Homer rules, in help\KeyDecisions.md: what was weighed, why each choice won, and how to take each one back. The suite manifest records each decision, with the key it replaced.
- **Web pages written by the kit carry math as MathML,** which screen readers read as math. A page without math is unchanged.
- **Proposed for DbDo and FileDir, to match EdSharp:** Play Tutorials on Alt+F12; and in FileDir, Extra Speech Log on Alt+Shift+F12, Edit Settings File on Alt+Shift+F2, and Tile Vertical on Shift+F11.

## 1.76.1 -- 19 October 2026

- **Text from Word is read correctly.** The new .doc routes were made, but reading them back failed: Word writes its text as UTF-16 from some documents and in the Windows code page from others, and the readers expected UTF-8. Word's text is now decoded by its byte order mark, then UTF-8, then the code page, and rewritten as UTF-8 with a byte order mark, in C# and Python alike. The conversion test, which failed five .doc routes on this, found it.

## 1.76.0 -- 19 October 2026

- **EdSharp converts through the kit.** It now compiles Conversion.cs and Table.cs and ships conversions.inix, and the shared check fails it, as it does FileDir, on any private conversion code.
- **Word's 1997 .doc format can be written,** as well as .rtf and .odt, by the officecom engine in C# and Python, and plain text can be opened by Word. New routes txt2doc, htm2doc, md2doc, rtf2doc, odt2doc and docx2doc serve an editor's Export. Only Word can write a .doc file, so each is Office alone, the last resort.
- **Office used for something other than converting can be marked.** A line ending in "// homer: not a conversion -- <why>" is logged with its reason by the shared check and not counted. EdSharp marks the two lines that start Word for its optional Word spelling, thesaurus and mail.

## 1.75.0 -- 19 October 2026

- **HomerScribe's PDF reader is now the kit's.** The new PdfReader.cs is the reader from HomerScribe's PdfRead.cs and the PDF half of HomerScribe.cs, moved whole into one shared class. It reads the PDF's own tags where they carry the document, otherwise the text layer in reading order with headings from type sizes, and reads scanned pages with Tesseract above a confidence floor. A picture model for pages and descriptions of figures are optional, supplied by the app. HomerScribe calls it, and so can any app.
- **It is Conversion's pdfstructure and ocr engine.** An app that compiles PdfReader.cs and the new ConversionPdf.cs, with PdfPig, gets it for pdf2md, pdf2docx and pdf2htm, and gets OCR in C# for the first time. An app that does not still uses pymupdf4llm, so nothing breaks.
- **Scanned documents get a second chance.** pdf2docx and pdf2htm now try OCR before Office. pdfstructure fails on a document of scans, so the OCR way is tried rather than an almost empty result.
- **Two faults fixed on the way.** The Markdown written was the version before its heading levels were closed; only the screen reader review saw the corrected one. Now the closed version is written. And a document read from its own tags no longer says its headings were worked out from the layout.

## 1.74.1 -- 19 October 2026

- **Command names are spoken if and only if they help.** The new KeyMap.shouldEcho decides, so every Homer app decides alike. A command that opens a dialog, opens a window that names itself, moves the focus, or speaks its own answer or state does not say its name. Every other command, such as Clear Filter, says its name at once, before its work. The kit's frame follows the rule; a frame command that speaks its own result, such as Clear Clipboard, carries bNoEcho. DbDo's Command Echo Toggle is retired.
- **help\\CommandEcho.md** lists where every menu command of DbDo, EdSharp, FileDir and the frame falls, for review.
- **Freed and restored keys in the manifest:** DbDo's Read Only Toggle takes Control+Shift+Z and its Say Status gains Alt+Z; FileDir's Zip then Delete has Control+Z again. Each is a recorded exception, since neither app has Undo or Redo there.

## 1.74.0 -- 19 October 2026

- **One copy of every file conversion.** The new Conversion.cs is the C# side of the kit's conversion code, which every app is to use. It began as FileDir's own Convert.cs, moved here and renamed so it cannot hide .NET's System.Convert. Table.cs moved with it and now reads .xlsx with .NET's own zip support. ConversionMedia.cs holds the audio, video and picture conversions, for apps that compile Media.cs.
- **Conversions are named source2target.** The routing table, exec\\conversions.inix, now has one section per conversion, such as pdf2txt or pdf2docx, each listing its ways best first with a note on why. Python's conversion.py and C#'s Conversion.cs read the same file.
- **Both the source and the target decide.** pdf2txt reads only the text layer, through PdfPig in-process when it is beside the program, else PyMuPDF's plain text. pdf2docx works out the structure first. A quick read never uses OCR.
- **New internal readers need no program at all:** docx2txt and odt2txt read the XML inside the file, and xlsx goes through the Table class.
- **Office is the last resort, and says so.** When a conversion needs Microsoft Office and it is missing, an Alert box explains it once per session and names the free way around it. A console program gets the same words as an error instead.
- **Every conversion is timed.** The log names the route and the milliseconds it took, so the order of the ways can be tuned from measurements.
- **The shared check has a conversion step.** It counts an app's private conversion code: its own Pandoc finder, a 2htm call, an Office COM object or pymupdf4llm. Apps listed as moved fail on it; FileDir is the first. The others are warned until they move.
- **Files are recognized by their bytes as well as their extension.** Conversion.recognize and Conversion.describe tell text from binary by magic numbers, byte order marks and zero bytes, and name the encoding through Ude when Ude.dll is beside the program. A .inix, a .m3u, or a file with an extension nobody listed is read as text when its bytes are text.
- **help\\Conversions.md** records the review of every app's conversions and the best engine for each.

- **The suite's shared commands are one piece of code.** The new SuiteCommands class in Mdi.cs holds Say Clipboard, Say Time, Copy Log, Save, Append and Clear Clipboard, and the Help openers for the guide, History, ReadMe and Hotkeys. The frame calls it, and so do EdSharp and FileDir from frames of their own, so the words and behavior match in every app.
- **The best of each app went in.**
  - Say Clipboard says how many files are copied and names them, as FileDir did.
  - Copy Log puts the log on the clipboard both as a file and as its path, as EdSharp and FileDir did.
- **The suite check holds apps to it.** A manifest command can carry a `shared=` line naming its SuiteCommands method. checkKeys fails when the method is missing, and, on an app's push, when the app's code does not call it. The shared check now passes the project folder for this. Ten commands in EdSharp and FileDir are marked so far.
- **A menu choice is always a first press.** A Say command picked from a menu no longer spells because the same key was pressed a moment before.
- **The kit's own program speaks to NVDA.** HomerDev's log said the NVDA controller client was missing. The kit now carries NV Access's 64-bit nvdaControllerClient.dll in exec, beside HomerDev.exe, and an app's build can copy it from there, as FileDir's now does.
- **Two documents corrected.** The suite contract and the framework guide both gave Alt+Shift+Apostrophe for Append Clipboard as well as Clear Clipboard. Append Clipboard is Control+Shift+Apostrophe, as the code always had it.

## 1.73.8 -- 19 October 2026

- **Repeat presses follow NVDA: one, two or three.** A Say command speaks its answer on one press, spells it on a quick second press, and shows it in a read-only window on a third. NVDA's Report Current Line spells on two presses and spells phonetically on three, and its Read Window Title copies on three. So EdSharp's and HomerView's spelling on a second press and DbDo's review window are both kept. The window lets the screen reader spell phonetically and copy.
- **Lbc's text-box keys belong to the text box in every MDI window.** In a text box that is not the app's editor, the keys Lbc's text boxes answer go to the control rather than to a frame command, so an Lbc field behaves as it does in an Lbc dialog. The keys are copy and cut the line, Alt+C and Alt+X to append, delete the line, the F8 family, Alt+Y, Alt+Apostrophe, Shift+F1, and the multi-line commands. KeyMap.cs lists Lbc's text, list and dialog keys in one place.
- **The fruit baskets add on Alt+Shift+A.** Control+Shift+A is Lbc's unselect in a text box, so it no longer reached Add Fruit from the fruit field. The starters' Add Item moved too. Enter still adds.
- **The suite contract records the principles and judgments of 19 October:** functionality is never lost to a key change, agreed changes are carried out, Lbc's patterns hold in the framework, Control+PageUp and PageDown have a purpose of their own or none, and one name, key and description means one piece of code. Each pending decision is settled there, with its stage.
- **FileDir's zip commands keep keys** in the manifest: Zip then Delete on Control+Shift+Delete, and Zip List keeping Control+Shift+Z as a recorded exception.

## 1.73.7 -- 18 October 2026

- **The suite check really runs in every app's push.** It found the kit through the kind.py already loaded, which can be the installed kit's in Program Files, older than the development kit and without checkKeys.py, so DbDo's, EdSharp's and FileDir's pushes all reported "the kit's checkKeys.py was not found" and skipped it. It now finds the kit with kind.findKit, which prefers the development kit, as tidy already did.
- **A top-level folder outside the Homer tree goes to notes, by tidy.** EdSharp's push stopped on a folder named "l;ogs", most likely "logs" mistyped. Tidy now applies check's own layout rule: a folder at the top that is neither standard for the project's kind, declared in RepoFiles.txt or LocalFiles.txt, nor in the kit's conformance backlog is moved whole into notes, under its own name. Nothing is deleted, the log names it, and the push that follows passes.
- **Confirmed on 18 October, from the first runs of 1.73.5 and 1.73.6:**
  - the Python fruit basket loaded the C# frame through pythonnet and exported the same 38 commands as its C# twin;
  - FileDir's tidy wrote its JAWS pass-through for Alt+Delete and named its bracket keys, and push committed them.

## 1.73.6 -- 18 October 2026

- **One frame for C# and Python.**
  - **The problem:** the Python MDI frame, exec\\Python\\mdi.py, was a wxPython copy of the C# one, and it had drifted. It still used the old keys (Alt+Shift+C for settings, Alt+Shift+S for scripts) and had none of the key router, managed lists, Say and clipboard commands, or double press.
  - **The cure:** exec\\Homer.dll now carries KeyMap, KeyName and Mdi, and mdi.py is a thin face over the C# Homer.MdiFrame, MdiChild and KeyMap, loaded through pythonnet as lbcnet.py already did for dialogs. Every fix to the C# frame reaches Python apps on their next build.
  - **Build order:** the kit builds Homer.dll before the samples, so the Python sample always bundles this build's frame.
- **The fruit basket twins are one program.**
  - FruitBasketMdiPy.py is rewritten to match FruitBasketMdiCs.cs command for command: two windows, typing, a managed list with Shift+letter commands, the Delete alias, unavailable commands, a modal dialog, the double press, Jump with Again and F3, F6 parts, refusing to close, settings, and the clipboard family.
  - Its build now finds Python 3.13 through the py launcher (pythonnet supports up to 3.13), installing it with winget if missing, and bundles Homer.dll with pythonnet instead of wxPython.
  - **Checked every build:** the kit's build exports both samples' commands and fails, naming each difference, if their identifiers, keys or contexts ever differ.
- **newHomerApp MyApp --mdi --python** makes a Python app on the same frame, from a new starter, Templates\\_APP_MdiPy.py, with its build set to bundle Homer.dll and pythonnet. The starter's AI NOTE gives an assistant the framework's rules.

## 1.73.5 -- 18 October 2026

- **JAWS hands Alt+Delete to the apps that use it, with nothing edited by hand.**
  - **Why:** JAWS takes Alt+Delete everywhere for Say Active Cursor, which in a list reports pixel coordinates. The suite's Say Position is the useful answer, by Jamal's ruling.
  - **How:** a new kit module, scripts\\jawsKeys.py, is run by the shared tidy after every build. It writes a marked block into an app's scripts\\jaws\\\<App\>.jkm that hands the allowed keys on with TypeCurrentScriptKey.
  - **Which keys:** the reviewed allowlist in data\\KeyOwnership.inix (passThrough=yes), never every key JAWS owns, and only when the app's own Hotkeys.md shows it binds the key. A key the app does not yet bind keeps its JAWS meaning, and a key the app maps itself is left alone.
  - **Checked:** the shared check confirms the block before every push.
  - **Who it affects today:** FileDir, whose Say Percent Through is on Alt+Delete; its next cycle writes the block and push commits it. EdSharp gets it once its own Say Position exists, and DbDo once it has a key map, in stage 3. HomerView is excepted in the data, since its key map is chained into the browsers'.
- **Bracket keys by name in JAWS key maps.** A key map line beginning "[" is read by JAWS as a new section. Tidy now renames a bare "[" or "]" key LeftBracket or RightBracket; FileDir.jkm had four such lines.
- **Stage 2 of the suite plan is complete.**

## 1.73.4 -- 18 October 2026

- **Settings files are safer, in every app that uses InixCodec.**
  - **Cached reads:** readValue keeps each file it has parsed and parses it again only when the file's time or length changes. An app reading forty settings at startup reads the file once, and an edit made outside the program is still seen at the next read.
  - **Atomic writes:** writeValue and writeAsConfig write a temporary file beside the real one and swap it into place, so a full disk or a power cut halfway leaves the old file whole rather than half written.
  - **Problems reported:** a file that cannot be read gives the defaults and is left untouched, as before, but is now reported once through InixCodec.onProblem instead of in silence. The Homer frame sends that report to the log; other apps can connect it the same way.
  
  Every member keeps its signature, and Inix.cs still depends on no other Homer class, so DbDo, EdSharp and FileDir compile it unchanged.

## 1.73.3 -- 18 October 2026

- **The clipboard family, in every app on the frame.**
  - **Control+Apostrophe, Save Clipboard,** proposes a new file in the results folder named for the date and time. It never replaces a file: a name already taken is refused and asked for again, and the file is opened in a way that cannot replace even by a race.
  - **Control+Shift+Apostrophe, Append Clipboard,** adds the text to the end of a text file you pick. It appends only to UTF-8, so a UTF-16 or older code-page file is refused with the reason, rather than mixing two encodings in one file. It never puts a byte order mark mid-file, starts a new line when the file does not end with one and says so, and writes through a temporary file swapped into place, so a failure leaves the original exactly as it was.
  - **Alt+Shift+Apostrophe, Clear Clipboard.**
  
  New text is UTF-8 with CRLF line endings.
- **One trigger letter per menu, enforced by the frame.** The first item on a menu to claim a letter keeps it; a later one that would repeat it loses its ampersand, and the log says which. An app's items and the frame's can no longer clash.
- **No more mid-word trigger letters.** Hotkeys and Close Window, which had them, now have none, since their menus have used those first letters already. The sample's Say Position, Jump Again and Exit now use the first letter of a word.

## 1.73.2 -- 18 October 2026

- **One table of key spellings, KeyName's.** KeyMap 1.73.0 had its own list of key names, which spelled two keys Accent and BackSlash, on the belief that those were the JAWS spellings. KeyName.cs, whose spellings were taken from JAWS 2026's own default.jkm, says GraveAccent and Backslash. KeyName is right, and a second list was the mistake the conventions forbid: conversion tables live in one shared class. KeyName gains fromWinFormsKeys, the reverse of toWinFormsKeys, read from the same table, and KeyMap names every key through it. Only keys KeyName has no name for, such as the number-pad digits, are spelled in KeyMap.
- **The suite data uses KeyName's spellings,** and checkKeys accepts the other spellings when comparing, as KeyName itself does: a forgiving reader, a strict writer.

## 1.73.1 -- 18 October 2026

- **The suite key check is a gate, in the kit's build and in every app's push.**
  - **The kit's build** fails when checkKeys finds a problem: a key bound twice with no reviewed reason, a key Windows or a screen reader takes everywhere, or a clash the program itself reported. Keys to test in their real control and first-letter misses are still reported, not failed.
  - **Every app's push** runs a new "suite" check in the shared check. An app on the Homer frame first exports its own keys, without a window, so the check reads what the program really declares; any other app in the suite manifest is checked against its entries there.
- **Shared keys carry their reason.** A command that shares a key on purpose has an exception= line in data\SuiteCommands.inix, and checkKeys counts it as reviewed rather than as a problem. The four shared keys found by the first gated run now say why: EdSharp's Open and Save dialog commands, and FileDir's parent-folder commands, which merge in stage 4. EdSharp's Set on Favorite List, a second name for Set Favorite, left the manifest.
- **checkKeys --app** checks one app.

## 1.73.0 -- 18 October 2026

- **One command and key mechanism for every Homer app.** KeyMap.cs now declares each command once: a stable identifier, the keys, the context they belong to, a summary, an "unavailable because" check, a checked state and a repeat behavior. One router decides where every key goes. A text box keeps its typing keys unless the app marks it as its editor, and a managed list keeps first-letter and typed-sequence navigation. Shift plus a letter in such a list runs its command or says that none is bound. A command that cannot run says why. The members EdSharp and FileDir use today are kept, so their builds compile unchanged.
- **Double presses, again, and search memory.** A quick second press of a Say command shows its answer in a window to review and copy; a held-down key never counts. Control plus a letter can remember its answer for each window, so Alt plus the letter repeats it, and F3 repeats whichever search ran last in that window. A closed window's memory goes with it.
- **The MDI frame gives every app the suite's shared commands.**
  - Window commands: F4, Shift+F4, Control+Tab, Control+F4 and Control+Shift+F4. Closing can be refused, and only the windows that really closed are counted.
  - Edit Settings on Alt+Shift+E, and Invoke Script on Control+Shift+I.
  - Say Clipboard and Say Time.
  - The Help family: Key Describer Toggle, Hotkeys, ReadMe, the Alternate Menu, Hotkey Summary, Elevate Version and Copy Log.
  - Play Tutorials in the Homer Player.
  
  Every key goes through the router; menu items show their keys without Windows' shortcut handling.
- **newHomerApp MyApp --mdi** starts a multi-window app from a new starter, Templates\_APP_Mdi.cs, whose AI NOTE gives an assistant the framework's rules. help\MdiFramework.md is the guide for anybody building an app on the frame.
- **The fruit basket sample is the stage 1 desktop proof.** It shows two windows, typing, a managed list, an alias, unavailable commands, a modal dialog, the double press, Again with F3, F6 parts, refusing to close, settings and the key export.
- **The Homer Suite contract.** help\HomerSuite.md holds the rulings and statuses, the key families, the AI attachment rules, the text-file and settings rules, HomerView's browser identity, the stages and the stage 1 test steps. Two new data files go with it:
  - data\SuiteCommands.inix: every command of DbDo, EdSharp, FileDir and HomerView.
  - data\KeyOwnership.inix: the keys Windows, the screen readers and the browsers own.
- **scripts\checkKeys** checks the manifest, the ownership file, KeyMap's own reserved list and any app's /exportkeys file. It reports for now; stage 2 makes it a gate.
- **The starter no longer suggests a c_ prefix for constants.**
- **The key checks run inside the build, with nothing to run by hand.** After building the samples, the build starts the MDI sample with /exportkeys, which now writes the export and ends before any window appears, so a build never takes focus. Then it runs checkKeys on the manifest and that export, and puts the summary in the build's output. An app's Main calls MdiFrame.runOrExport instead of Application.Run, which is what makes the export windowless.
- **llms.txt has no byte order mark again,** as KeepEncoding.txt requires; the first 1.73.0 build stopped on it.

## 1.72.58 -- 15 October 2026

- **Util.runResponsive does long work without "Not Responding."** It runs a job on a background thread while the window keeps answering Windows, disables the window so no second command starts halfway through, and returns focus where it was. A progress callback runs on the window's own thread, because screen reader calls do not belong on a background thread. An error in the job is thrown again to the caller. FileDir's Zip then Delete is the first user: zipping about 200 MB had left it "Not Responding" until it was closed by force.

## 1.72.57 -- 15 October 2026

- **Builds speak their tutorials in the order they arrived.** Only one build speaks at a time, so the others wait. But the lock went to whichever waiting build happened to check first, not the one that had waited longest. On 15 October, HomerScribe began waiting at 11:20 and spoke at 14:17, after eight builds that arrived later: 177 minutes of waiting for 32 minutes of speaking. Each waiting build now writes a ticket named for when it arrived, and only the oldest ticket waits on the lock. The console says how many builds are ahead. A ticket left by a build that has ended is removed, so it cannot hold up the line.

## 1.72.56 -- 15 October 2026

- **A component found outside winget has its version read.** winget lists only what it installed. DbDo's installer found mpv by its file under Program Files and stopped there, so its log said the version "could not be read," and its box could only ever say Reinstall. HomerComponents.iss now asks the program found for its version, compares that with the newest release winget offers, and offers Update, ticked, when it is older. Two numbers that cannot be compared, such as a dated build against a numbered release, stay Reinstall, and the setup log says why.
- **Updating a copy winget did not install now works.** winget upgrade answers such a copy with "no installed package found." installCommon's wingetUpgrade then installs the newest release in its default machine-wide folder, and reports the result like any other.

## 1.72.55 -- 15 October 2026

- **check fails a Windows program whose Main has lost [STAThread].** In DbDo 1.0.287, a function added between the attribute and Main took the attribute for itself. The compiler accepted that, but Copy Cell then failed with a clipboard error, and the file dialogs were at the same risk. The new mainthread check fails any Windows Forms source where Main lacks the attribute, or where the attribute sits on something else. It found exactly those two lines in DbDo 1.0.287.
- **check fails an installer that runs a script it does not install.** DbDo 1.0.287's finish page had no JAWS box on a computer running JAWS. Its installer asked installScreenReaderSupport.cmd whether the scripts needed installing, but never installed that script. Its mpv box ran installMpv.cmd, which the build never copied. The new shipped check reads each installer's [Run] and [UninstallRun] lines. Any program under the app's folder must be installed by a Source: line, and any script it names must be in the project. It found both of DbDo's gaps, and it passes all 55 programs the kit's own installer runs.
- **The kit holds itself to both checks.** checkHomerDev runs the same two functions from check.py against the kit, rather than keeping a copy of them.

## 1.72.54 -- 15 October 2026

- **The build repairs stray line endings instead of stopping.** Every build since 14 October afternoon stopped on two bare LF endings in scripts\kdpUpdate.py, left by an edit made elsewhere. Turning a bare LF into CRLF changes nothing a reader or interpreter sees, so the build now repairs such a file in place, says so, and logs the count; push commits the repaired file. A file that also holds a lone CR is still reported, since what it meant cannot be judged.
- **push tries four times before failing.** extCheck's push of three tutorial MP3s timed out (HTTP 408) on both of its tries, on a day when a fetch elsewhere was also reset. After the large-upload retry, push now waits 30 seconds and tries again, then 60 seconds and tries once more, logging each try. The commit is kept either way, so the next push sends it.
- **Directory subtitles are counted.** The homer-page skill's directory-entries rules gain a Subtitle rule: every directory's subtitle begins "A Directory of" and a count that code supplies, and the subtitle is not repeated in `pagetitle`, where it goes stale.

## 1.72.53 -- 15 October 2026

- **Blind Creators has a description.** buildCreators.py now writes a one-sentence description into the front matter of BlindCreators.md, for search results and link previews; MyPages' post had noted it missing on every run.
- **checkDirectory no longer counts the front matter as text.** It reported a page's license_url as a bare address, though the kit's front-matter standard requires that line; only the text after the front matter is now scanned, and a real bare address in the text is still caught.

## 1.72.52 -- 15 October 2026

- **Every directory's entries follow one set of rules.** A new reference in the homer-page skill, references\directory-entries.md, gives each rule in alphabetical order with its reason: a one- or two-sentence description right after the heading, with no label; Source page and Transcript links in paragraphs of their own; the other fields in alphabetical order; Presenter singular, in the source's order; Length in whole minutes with no "about"; near-constant fields such as Medium dropped; required values read from the work itself, or the entry left out and named; and only a few notable observations in By the Numbers.
- **Podcast directories follow them.** The podcast-directory builder now puts the summary first, cut to two sentences and unlabeled, says Source page rather than Episode page, and gives Length in whole minutes in place of the feed's Duration.

## 1.72.51 -- 14 October 2026

- **setup /defaults takes the defaults, with one Enter.** Given alone, /defaults left the whole wizard showing, so "homerdev_setup /defaults" asked every question. Inno decides before any code runs whether a run is silent, so code cannot make it silent; but it can skip pages, and with /defaults every page Inno allows to be skipped now is, each keeping its default. The finish page stays, with its default boxes ticked, and Enter finishes. For no screens at all, /verysilent /defaults, as before. This is in the shared HomerComponents.iss, so every Homer installer has it (from an audit by another AI, HomerDev-11).
- **help\AnnounceStandard.md announces the standardization:** ten apps on one tested foundation, written to be pasted unchanged into Facebook, LinkedIn and email lists, at grade 7.5 and under 2,300 characters, with one address.
- **help\AuditResponse.md answers the audit of 14 October midday:** HomerScribe-11, HomerDev-11 and MyBooks-07.


## 1.72.50 -- 14 October 2026

- **A build that builds nothing no longer sounds as if it builds.** The fingerprints were working -- Homer.dll, for one, was skipped in seven of ten builds on 13 and 14 October -- but every part found current was announced on its own: "exec\Homer.dll is unchanged since its last build; not built again", and five lines like it, every build. Each is now in the log, and one sentence says how many parts were current. (HomerDev.exe and the installer do build on every release: each carries the new version number.)
- **Finding the newest Pandoc no longer runs every copy each time.** newest.ps1 ran every copy it found for its version -- about four seconds on every build of every app. Each copy's version is now kept with its size and time in %LOCALAPPDATA%\HomerDev\newest-<name>.txt; an unchanged copy is not run, and a new or changed one is. Every copy is still found, so a newly installed one is noticed at once.
- **buildBooks keeps a book that is not ready, for a while.** Only a ready book's audit was kept, so Legacy of Mazrui was built and judged again on every run: its 14 missing pictures fetched and failed again, then EPUBCheck, Ace and Kindle Previewer, about 45 seconds for a known answer. A not-ready audit of the same build is now kept until it is toolRefreshDays old (7 days), when its pictures are tried again; a change to the book builds it at once. Tested on the real code: kept when unchanged and young, judged again when old or changed.
- **buildBooks says only what it does.** "Checking for EPUBCheck and Ace by DAISY" was said on every build, though the tools are usually taken from their record without checking; it is now logged, and a real check -- a record that is old, missing or broken -- is said. The 21 books kept as they were are counted in one sentence rather than named one by one.
- **The build date that stops needless resubmissions now takes effect.** It was written into MyBooks' own copy of buildBooks.py on 14 October, but buildBooks.cmd replaces that copy with the kit's on every run, so the fix never ran. It is now in the kit's copy, and was tested again there: an unchanged book keeps its date, an edited one gets a new one, and two builds under one date are byte-identical.


## 1.72.49 -- 14 October 2026

- **help\AuditResponse.md answers the audit of 14 October morning:** 2htm's undefined constant, HomerScribe's command-line source and its acceptance evidence, and HomerView's results file.


## 1.72.48 -- 14 October 2026

- **Replacing a file keeps two complete copies at every moment.** When File.Replace was refused, replaceFileSafely copied the new file over the old, so a full disk or an interrupted copy could leave it truncated, with no copy of the old content when no backup was asked for; and a backup that could not be rotated after the file was replaced made the call throw, so callers said "unchanged" of a changed file. Now the fallback is two renames, each atomic, putting the old file back if the second fails and naming both copies if even that fails; only a failed commit throws; a commit whose backup could not be rotated returns a warning naming where the previous content is; and the backup is swapped in atomically, so the earlier one stays until its successor exists. writeTextSafely keeps its staged copy when the target is missing, since it may then be the only complete one. Tested by a simulation of every combination of failures, 256 runs, before it was written here (from a second audit by another AI).
- **FileDir builds again.** Web.cs's new percent decoding called Convert.ToByte, which inside namespace Homer is FileDir's own Homer.Convert class, so FileDir's build failed; it now says System.Convert.
- **The KDP test suite runs in a clean checkout.** One test read the author's own catalog, which is not in the repository, so a fresh checkout stopped after 24 checks; it now says it skipped the catalog and goes on. That also showed kdpSubmit using its fallback reader where the kit was not at C:\HomerDev; it now looks first for the kit it is in. A checkout with no personal files and no HomerDev variable: 66 passed, 0 failed (from a second audit by another AI).


## 1.72.47 -- 14 October 2026

- **help\AuditResponse.md answers the coordinated audit, finding by finding.** For each of its 72 findings across the kit and ten apps it says what was changed, where, and how it was tested -- separating tests run on the real code, or a line-for-line prototype, from changes that still await a build or a run on Windows -- so the next audit can verify rather than rediscover. 57 are done, one of them with a check still open; 1 is partly done; 14 are open, each needing Windows, Office, a clean machine or a screen reader. The count was taken from the entries themselves, and every finding of the audit appears once.

## 1.72.46 -- 14 October 2026

- **A download's name is read from its header as the standard writes it.** Web.fileFromDisposition read the Content-Disposition header with patterns: a quoted name stopped at its first semicolon, filename* was decoded as UTF-8 whatever character set it named, and a backslash escape was kept as written. The header is now split into its parameters with quotes respected, a quoted value is unescaped, filename* is decoded by the character set it names, UTF-8 or ISO-8859-1, and a path in the name is cut to its last part, so a header cannot direct a file into another folder. Tested on twelve headers before it was written here (from an audit by another AI).
- **Web.sanitizeName keeps clear of Windows device names.** CON, PRN, AUX, NUL, COM1 to COM9 and LPT1 to LPT9 cannot be file names, with any extension, so a download called CON.pdf could not be saved; such a name now gets an underscore in front, while Console.pdf and COM10.txt keep theirs.


## 1.72.45 -- 14 October 2026

- **connectAI keeps your own instructions byte for byte.** It puts a short pointer to the kit in each AI tool's personal instruction file, between two marker lines. It read the file with errors replaced, trimmed the line breaks around its block, and wrote the file in place, so text that was not UTF-8 came back changed and an interruption could lose instructions that had nothing to do with the kit. Now a file that is not UTF-8 is left exactly as it is, and the reason given; markers that do not pair are reported, not guessed at; only the block changes, in the file's own kind of line break; a dated copy is kept before the first change; and each write goes to a temporary file that is swapped in. Tested as the audit asked: with and without a byte order mark, CRLF and LF, an empty file and a file whose last line had no line break, connecting and then removing gave the file back as it was -- the last only gaining that line break, which removing cannot tell from the person's own -- and connecting twice changed nothing the second time; text that was not UTF-8, three kinds of unpaired markers, and a failure during the write all left the file untouched (from an audit by another AI).
- **The chat says when an answer is incomplete.** A failed exit from Claude Code counted as an error only when nothing came out, so an answer cut off by a failure was shown as a whole one, with "Answered" spoken after it. Any failed exit is now an error: the text is kept, introduced as possibly incomplete with the error named, and the status and speech say "Incomplete answer, with an error". A failed first turn is still not taken for a session that can be resumed (from an audit by another AI).

## 1.72.44 -- 14 October 2026

- **Push and release read every file again.** The fingerprint cache trusts a file's remembered hash while its size and modification time are unchanged, which keeps build and tidy quick. But that is an optimization, not proof: a file replaced by different bytes of the same length, with its time put back, kept its old hash, and its work could be skipped. There is now a verifying mode that reads every file again and corrects the remembered hash. build_release turns it on before push and release, so nothing goes public on a stale hash; check --fresh uses it too, so "in full" means every file; and fingerprint.py takes --verify from a batch file. Tested as the audit asked: after a same-size, same-time swap the ordinary cache kept the old hash, and the verifying cache gave the true one (from an audit by another AI).

## 1.72.43 -- 14 October 2026

- **Homer.Util.fileSha256 gives any app a file's fingerprint by its content.** A file's size and time say only that nothing obvious changed: HomerScribe took a recording replaced by another of the same length, with its time kept, for the same file, and credited the old transcript to the new one. The kit had no shared way to fingerprint a file, so each app would have written its own; this one reads in one-megabyte blocks and shares the file for reading, so a file another program has open can still be fingerprinted (from an audit by another AI).


## 1.72.42 -- 14 October 2026

- **checkDocs measures a list fairly.** The reading grade ends a sentence at a full stop or a blank line, and list markers were removed before that, so a list with no full stops counted as one long sentence: urlFido's fourteen editing keys, one per line, scored grade 14.3. Each list item now ends the sentence before it, as readability tools treat bullets; the same list scores 5.5, and prose without lists measures exactly as before. With lists measured fairly, DbDo's and urlFido's guides meet the ninth-grade target without a word changed; EdSharp's, at 10.3, is genuinely dense.


## 1.72.41 -- 14 October 2026

- **New apps' help pages have a contents list.** The app template's build ran Pandoc without --toc, so a long guide made from it had no list of its sections, and checkDocs rightly reported it. It now builds with --toc --toc-depth=2, and a page without a contents list is rebuilt once to gain one, rather than waiting for its .md to change. Existing apps get the same change in their own builds.


## 1.72.40 -- 14 October 2026

- **makeTutorials proves its own output is settled.** After writing Tutorials.md it reads it back and applies the same walkthrough again in memory; if that would change anything, the build stops, and the log gives both fingerprints. Tested on DbDo's own files: the first run removed its 80 copies and wrote one, 3.7 MB to 70 KB, and a second run wrote the identical file; with the old duplicating splice put back on purpose, the build stopped as it should (from an audit by another AI, which asked for proof of two-run idempotence).


## 1.72.39 -- 14 October 2026

Learnings from the logs of 13 October evening.

- **No file is dated in the future.** Deliveries were zipped on a clock running on UTC, and a zip records local time with no zone, so files unzipped about seven hours in the future: a page rebuilt moments before was still reported older than its .md. fixEncoding, which every build runs, now sets any file dated more than two minutes ahead to now and logs each; deliveries are now stamped in Pacific time.
- **checkDocs reports fewer false findings.** An address in inline code, such as `https://example.com`, is an example, not a bare URL; fenced code was already left out. A long document whose .htm carries a contents list -- the `<nav id="TOC">` the page finisher writes -- has one, whatever its Markdown says; 25 such documents had been reported.
- **The log review lists warnings on their own.** A reused check's warning carries "(in the run reused here)", so it appeared among the skipped checks; warnings now have their own section, one line each.


## 1.72.38 -- 14 October 2026

- **A program that may hang can be given a deadline.** `Media.run` waited for a program with no limit, so a converter that hung held its caller with it. A new form takes a number of minutes: past it, the program and the processes it started are ended by their own id -- `Media.endProcessTree`, so no other copy of the program is touched -- and the call returns -2 with a plain message. The existing form is unchanged and has no limit, which is right for work that can take long, such as a download (from an audit by another AI).


## 1.72.37 -- 14 October 2026

- **A check no longer summarizes itself.** check runs the log summary over its own logs folder while its own log is still open, so the summary reported that very check as UNFINISHED. summarizeLogs takes `--skip=<file name>`, check names its own log, and the newest finished check is reported instead (from a follow-up audit by another AI).
- **The last `c_` in the kit's shared code is gone:** a comment in Elevate.cs still spoke of "the c_i outcomes" after its constants were renamed. Constants follow the variable rules and never carry `c_`.


## 1.72.36 -- 14 October 2026

From a follow-up audit by another AI, checked against the release logs.

- **Every app's Tutorials.md stops growing, and is repaired by its next build.** makeTutorials had two faults. It looked only at the first start and the first end marker, so one stray end marker ahead of the start made the markers seem absent, and every build inserted a whole new walkthrough above the old ones: DbDo's Tutorials.md held 80 copies, 3.7 MB, and its Tutorials.htm 6.3 MB, all shipped. And it removed only the contents entry for tutorial 0, so the entries for 1 to 9 were added again at every build: 16 to 78 copies of each in every app's contents list. Now every marked walkthrough and every stray marker is removed and exactly one is written, and every generated contents entry is removed before the current ones are added. Tested on DbDo's, 2htm's, HomerView's and urlFido's own files: DbDo's comes to 67 KB, every hand-written line is kept, and a second run changes nothing.
- **A check that finds something is no longer a pass.** checkDocs exited 1 with findings while its stage said PASS and the run ended "21 checks passed, 0 checks failed". A fourth verdict, warn, means a check ran and found things worth reading that do not block a release: the documents now have their own line, "docs", a warning when checkDocs has findings and a failure when it could not finish. The totals name checks with warnings, each is listed on the console and in the evidence report's new section, "What deserves a look", a reused check keeps its warnings, and the log summary lists them.


## 1.72.35 -- 14 October 2026

From a coordinated audit of every project by another AI (72 findings); the shared parts are here, each app's in its own History.

- **Safe replacement, one way for every app.** `Util.cs` gains `stagingPath`, `replaceFileSafely`, `recoveryPath` and `writeTextSafely`. Apps wrote straight over files, deleted a backup before its successor existed, or reused one fixed recovery name and so deleted the last recovery copy. A complete staged copy is now swapped in with `File.Replace`, the previous backup is kept until the new one exists, and every recovery name is new. 2htm, DbDo, EdSharp, FileDir, HomerScribe and urlFido use them.
- **The installer pattern requires starting the program as the person.** Eight apps' installers started the program with `Exec`, which, even through cmd, keeps the installer's elevated rights. The template had used `ExecAsOriginalUser` since 1.43.42 and the apps never took it up. All are corrected, and the check now fails an installer that starts its program with `Exec`, or leaves its launch marker without first creating the logs folder.
- **The skills' reference documents are published.** build copies twelve documents from help into the skills' references folders, and `.gitignore` kept the copies out of the repository, so the published skills had twelve broken links. They are published now; build still makes them at every build.
- **The number of skills AGENTS.md states is checked.** It said seventeen; there are twenty. build now compares a stated count with the skill folders. (The audit's other point, that AGENTS.md prescribes the `c_` prefix, did not hold for this version.)
- **The book test suite runs anywhere.** It read the author's own catalog and data files and stopped without them; where they are absent it now checks the same rules against an invented catalog and data file, in a temporary folder. In the kit: 66 passed, 0 failed.

## 1.72.34 -- 13 October 2026

- **A damaged found.inix is gathered again.** One book's found.inix held the text \\xef\\xbb\\xbf -- a byte order mark written out as characters -- before [found], so the section was invisible and the book lost its extra picture folders. The build gathered a book's sources only when found.inix was missing, so it would have stayed that way; a found.inix with no readable [found] section now counts as missing, and the log names the book.
- **The log summary reads kdpFetch and a book project's tidy by their results.** kdpFetch's first real run was summarized "no errors" though 14 items failed; it now reads "5 items fetched; 14 items could not be", marked failed. MyBooks' picture-placing tidy, which shares the tidy log name, was summarized "whitelist only"; it now gives its own result line.

## 1.72.33 -- 13 October 2026

- **kdpFetch, a new book tool.** It fetches what a book lacks through the same remembered Edge window the other KDP tools use: a missing cover from the book's Amazon page (the full-size original, found by its ASIN), and each picture a manuscript names by web address that the build cannot find, cannot read as a picture, or finds as YouTube's 120-by-90 "no thumbnail" placeholder. For YouTube the sizes are tried largest first. Sites refused buildBooks' plain downloads; a real browser is refused far less often. Nothing on KDP or Amazon is changed. `-metadata` runs `kdpBooks -export`; `-manuscripts` explains that KDP offers no download of a published manuscript; `-dry-run` lists what is missing and where it would come from, opening no browser. It looks for each picture exactly where buildBooks does, through buildBooks' own functions, so it never fetches a picture the build already has.
- **A picture saved from a Word file is found again after the Word files are retired.** The build saves a Word file's picture under the manuscript's name with the Word file's extension (Newcomb_s_problem.png for Newcomb_s_problem.svg), and found it only by exact name. While the Word files sat beside the manuscripts that did not matter; once 1.72.31 retired them, 24 pictures would have had to come from the web on every build, and any refused download would have made a ready book not ready. A file with the same name and another picture extension, whose bytes are a picture, is now that picture.
- **Legacy of Mazrui's two "good" pictures were placeholders.** Its regalia photo and documentary thumbnail were byte-identical, 1,097 bytes, 120 by 90 pixels: YouTube's grey image for a thumbnail size that does not exist. kdpFetch treats such a file as missing.
- Every book tool's wrapper now refreshes kdpFetch from the kit as well.

## 1.72.32 -- 13 October 2026

- **A reused kit check no longer claims a clean build.** 1.72.28's sentence decided from the samples it saw, and a check reused whole sees none, so it fell back to "built from a clean start" -- the claim it was written to stop. A reused check now says no sample was built and names the pass it reuses.
- **The log summary reads a reused check and the kit's check as what they are.** Both were listed UNFINISHED on every release: a reused check has no totals of its own, and the kit's check now reports checkHomerDev's exit code. They read "reused the pass at <time>" and "the kit: checkHomerDev exit code 0".
- **A book is judged again when the rules for ready change.** Each audit now records the rules it was judged by; an audit judged by earlier rules is not reused. When missing covers became errors, five books without covers kept their earlier "ready", because their build fingerprints had not changed -- and the fingerprint must not carry the rules, since kdpUpdate compares it and a change resends a book to KDP. The EPUBs are unchanged by this, so nothing is resent.

## 1.72.31 -- 13 October 2026

- **A book's manuscript is its Markdown, alone.** Compared paragraph by paragraph and fact by fact, the fifteen MyBooks titles that also had a Word file held the same content in their Markdown, revised and extended; one Word file carried an AI chat's "max length" message pasted mid-sentence, and one ".docx" was a downloaded web page. buildBooks now moves a Word file beside a manuscript to notes\\word\\<root>\\, never deleting it and still reading it to recover a named picture; gathering no longer copies a Word file for a book that has its manuscript; a Word file starts only a book with none; and the word-count comparison between the two is gone.
- **A book with a missing component is not ready.** A missing cover was only a warning; it is an error now, unless the book's KDP answers keep the cover already on KDP. A file in a book's images folder whose bytes are not a picture -- twelve web pages in Legacy of Mazrui, saved by failed downloads -- is moved to notes\\not-pictures\\<root>\\, and a picture that could not be read as one makes the book not ready.
- **kdpSubmit stops only for a failed build.** buildBooks exits 1 when any book is not ready, and that stopped every submission. Now only a failure (2 or more) stops it; each book is built again when submitted and must come back ready.

## 1.72.30 -- 13 October 2026

From ChatGPT's first audit of MyBooks.

- **kdpSubmit needs more than a page change to call a book submitted.** Leaving the pricing page counted as acceptance, and a sign-in page or any other page also leaves it. Now only a new acknowledgement counts at once; leaving the page sends the run to the Bookshelf, and it counts as submitted only when the book shows In review, Publishing or Live; a sign-in, or a status that cannot be read, is unknown (exit code 6), with the reason said.
- **buildBooks keeps the checkers' full reports with each edition.** Ace's report lived in a temporary folder until the next build. Ace's and EPUBCheck's reports now go to notes\\evidence\\<book>\\<first 12 of the EPUB's sha256>\\ with a record of the date, the checksum and the tool versions; the three newest editions of each book are kept, and the audit page points there.

## 1.72.29 -- 13 October 2026

From another round of ChatGPT's audit, four of whose findings were in the review's own list, unanswered.

- **Setup says "current" only when it compared.** mpv, Whisper, Ace by DAISY and EPUBCheck were logged "found, current; offered as Reinstall" with no version read. Reinstall, unticked, is still the offer; the log now says the version could not be read and whether a newer one exists is unknown, or that no newer version could be looked up, and "current" only beside the newest version it was compared with.
- **The HomerDev dialog knows its version.** It was compiled without one, so its log began "version=0.0.0.0" while a later line said 1.72.27. The kit's version.txt is now compiled in, and part of what decides whether the dialog is built again.
- **The review leads with what matters, and catches three more kinds of finding.** Contradictions come first, skips next, the long caution list last. New rules flag a component called current with no version, a version of 0.0.0.0, and one app named at two versions in one batch, as a stale results file is. Run again on the same logs, it put all four findings at the top. The build-release skill adds: a narrow question does not excuse the review; answer it, then report the rest.

## 1.72.28 -- 13 October 2026

- **Every default, with no screens: /verysilent /defaults.** Inno Setup decides whether to show screens from the command line, before any installer code runs, so /defaults alone used to start setup again with /verysilent added. On 13 October 2026 that start failed on DbDo with no reason given, and HomerDev's and HomerScribe's installers never tried it, so all three showed every screen. The restart is gone, and with it any need to press buttons for the user. /defaults now goes beside a silent switch, which is the installer's own decision to show no screens: /verysilent /defaults installs, runs each finish-page entry ticked by default, logs the Results box and launches the program; /silent /defaults shows a progress window. /defaults alone changes nothing, and the log says to add /verysilent. Switches are read in any case. HomerDev's own installer now honours /defaults: its 55 finish-page entries say Check: homerFinishRuns in place of skipifsilent. The guide's FinishPage.md says all this.

## 1.72.27 -- 13 October 2026

From comparing Claude's reading of a day's logs with ChatGPT's reading of the same files.

- **summarizeLogs --review finds what a keyword search misses.** It reads every text file, evidence reports and setup logs included, and lists each caution in any wording (skipped, unknown, possible, could not, flagged, partial, rate limits, compiler warnings, page messages), every skipped check, and every claim another file contradicts. Run on the day's logs, it found all that ChatGPT had and Claude had not, and more: all fourteen of the day's kit evidence reports, not one, claimed a clean build of reused samples. The homer-build-release skill now says to run it first, account for every line it lists, read each output whole, test claims against other files, verify a fix in every project it touches, and never filter a known warning unseen.
- **The kit's evidence report says whether the samples were built.** It said "The samples were built from a clean start" on every run, including runs that reused samples built the day before. It now says none, some or all were built, and when the reused ones last passed.
- **kdpSubmit keeps KDP's spelling list, not only its count.** KDP said "We found 16 possible spelling errors" for Blind Vibe Coding's new manuscript, and the log kept only that sentence. kdpSubmit now opens KDP's spelling review, logs each flagged line as KDP SPELLING, and closes it; it cannot stop a submission.

## 1.72.26 -- 13 October 2026

- **The book tools speak of the answers file, not of JSON.** The answers have been an .inix file for some time, yet kdpSubmit still said "as the JSON says", "Review of the answers the JSON asked for" and "the draft id in the JSON". Every such message now says the answers file. Reading an answers file or receipt saved in the older format still works.
- **buildBooks keeps its record of tools in toolCache.inix.** A Homer record is an .inix file, readable by a person and enough for what it holds; toolCache.json is read once, replaced, and removed by the next build. JSON written or read for other tools -- pandoc's metadata, EPUBCheck's and Ace's reports, GitHub's release data -- is their format and stays.

## 1.72.25 -- 13 October 2026

- **kdpSubmit no longer mistakes KDP's name for its acknowledgement.** After Publish was pressed, the test for success searched the page's messages and its title for words such as "publishing", and the title of every KDP page ends "Amazon Kindle Direct Publishing". So each publish was judged submitted five seconds after the press, on no evidence, and the run went at once to the Bookshelf, possibly before KDP had finished. Blind Vibe Coding's update of 13 October was reported submitted this way. Now only a specific phrase in a message that was not on the page before the press counts, or KDP leaving the pricing page; otherwise, after two minutes, the outcome is unknown (exit code 6), and a bare run does not record that book's answers as sent.

## 1.72.24 -- 13 October 2026

- **kdpSubmit's questions are heard.** Python's input() writes its question to the error stream when run in a console, and kdpSubmit.cmd sends that stream to logs\\<project>-kdpSubmit-errors.txt. So every question kdpSubmit asks -- whether to submit what changed, the yes-or-no questions of --ask, whether to publish, and the waits for Enter -- went into that file while the console stayed silent. A run waited 22 minutes on a question nobody heard, then stopped with nothing submitted, and the launcher reported a Python error that was only the question. Each question now goes to the console and the log, and only the answer is read.
- **A book without a receipt is described truly.** kdpSubmit said such books had never been submitted by it; they had been, before the receipt kept one record per book. It now says there is no receipt of what was last sent, and that --book submits the book once and starts its receipt.

## 1.72.23 -- 13 October 2026

From a ChatGPT audit of the kit, DbDo and HomerScribe, each finding checked against the code before it was acted on.

- **A reused check keeps what it did not check.** When nothing had changed, check and checkHomerDev reused the last pass but kept none of its findings, so the report said nothing went unchecked after a run that had skipped the build and smoke tests. The cache now keeps a pass's findings, and a reuse restores the skips, each marked "in the run reused here"; a pass recorded before this says its coverage is unknown.
- **installWhisper proves Whisper is usable, not only present.** The model downloads to a .part file renamed when whole; a model already there is measured against the server's size and fetched again if short; whisper-cli is started once to prove it runs; and each step is written to the log, which used to hold only its header. Program and model both present no longer skips these checks.
- **A contact known only by a first name has an identity.** The contact pattern's prime was empty for anyone with neither a last name nor a company, so the unique index let only one such person in; it is now first|middle| for them, and unchanged for everyone else.
- **The chat starts a Claude session only once Claude answers.** A first question that failed marked the session started, and every later question tried to resume a session that was never made.

## 1.72.22 -- 13 October 2026

- **kdpSubmit decides for itself which books to submit.** Version 39 made a run without --book do nothing when several books had answers files: it stopped the wrong book by stopping every book. Version 40 runs buildBooks first, which rebuilds only books whose sources changed, then compares each book's manuscript, cover (unless the answers keep KDP's) and answers file with that book's receipt, and submits only the books where something differs, each through the single-book path. A book kdpSubmit has never submitted has no receipt, so it is named, never submitted on a guess, and --book submits it the first time. Before anything is sent, the books and the reason for each are listed and Y submits them; --yes answers for an unattended run.
- **The receipt is kept per book.** It held one manuscript and one cover entry, so with several books each upload overwrote another book's record. Entries are now <Book>.manuscript, <Book>.cover and <Book>.answers; an older shared entry still counts for the book whose file it names.

## 1.72.21 -- 13 October 2026

- **A readable-text skill.** .claude/skills/readable-text guides an AI tool in editing machine text -- caption files, transcripts, OCR output, hard-wrapped or escaped text -- into readable, faithful prose: paragraphs joined at real boundaries, recognition errors corrected only on evidence, doubtful words marked rather than guessed, nothing summarized, and the source and its limits stated. It was written with ChatGPT, kept under its MIT license, and given a section on Homer: HomerScribe's provenance lines, Homer document rules, and preferring captions a person uploaded. connectAI links it into Claude Code and Gemini with the other skills.
- **Whisper large-v3 turbo by default.** installWhisper fetches ggml-large-v3-turbo-q5_0.bin, 547 MB and near large-v3's accuracy, unless a model is named.
- **A large push is tried again.** When git push fails -- DbDo's 60 files, with the walks' audio and the 67 MB RadioTrail.db, ended "HTTP 408 ... the remote end hung up" -- push tries once more with a 500 MB buffer over HTTP/1.1, the usual remedy for a large push to GitHub timing out.

## 1.72.20 -- 13 October 2026

- **Node.js was offered as Update on every install, and the update never happened.** Setup's comparison was right -- Node.js 25.9.0 installed, 26.8.1 the newest long-term release -- but installNode decided which winget package owned Node.js from winget list's exit code, which is 0 on some machines while it prints "No installed package found". It took the long-term package as installed, winget upgrade found nothing, and the script said Node.js was "already the newest winget offers" and succeeded. Nothing changed, so the next install offered Update again. Now a package counts as installed only when winget lists its id; Node.js installed outside winget is updated by installing the long-term package over it, as Node's installers allow; and the version before and after is logged.
- **No installer checks again what setup has decided.** Setup compares the installed version with the newest before the finish page and offers Install, Update or Reinstall accordingly, so the components no longer say "Checking for a newer version": an Update says "Updating <name> to the newest release".
- **A failed update is reported as a failure.** Every component installer said "already the newest winget offers" whenever winget upgrade returned anything but 0. Only winget's own "no newer version" counts as current now; anything else is a failure, said and logged. The detection and the update live once, in installCommon (wingetHas, wingetUpgrade), used by the Node.js, Git, GitHub CLI, Java, Python, ffmpeg, ImageMagick, mpv and yt-dlp installers.
- **The PDF tools no longer update Python.** They upgraded Python 3.13 by name, which on a machine with another Python found nothing; Python is its own component, installPython.

## 1.72.19 -- 13 October 2026

- **The contact pattern, from DbDialog, is a homer-db rule.** A table of people uses DbDialog's fields, named so that each has an Alt letter of its own -- title, first, middle and last name, job, enterprise, two address lines, city, state, zip, nation, office, home and wireless phone, business and personal email, date of birth, gender -- then url, notes and tags. The skill's new scripts/contactPattern.py holds the list and rebuilds a table into it, keeping every row, computed field, index and trigger. It writes each table's edited trigger from the table's own fields, since a copied trigger named only the old ones and a new field's change left edited stale. Convention.db gained Title and the pattern's order; the convention skill's vCard export writes the office phone, title, second address line and birthday.

## 1.72.18 -- 13 October 2026

- **Connecting the AI tools no longer reports links that are fine as failures.** On a reinstall, connectAI said 19 of Claude Code's skill links and 57 of Gemini's had failed. They were linked all along: it learned whether an entry was a link by following it, and treated any failure to do so as "nothing here", so it tried to make each junction again and Windows answered that it already existed. It now asks Windows whether an entry is a reparse point and reads its target without following it. A link already pointing to the kit's skill is counted and left alone; a dead link, unreadable or pointing where nothing is any more, is replaced; a folder or link of anyone else's is never touched. Tested by linking, relinking, breaking a link and adding a folder of one's own.
- **Logs stay in the logs folder.** buildCreators wrote its log beside itself, inside the blind-creators skill, so its runs left log files among the skill's files, and two were delivered with 1.72.17. It now logs to the kit's logs folder, and the kit's build removes any log left among a skill's files.

## 1.72.17 -- 13 October 2026

- **Blind Creators states its size in its subtitle, and its numbers.** buildCreators writes the subtitle as "A Directory of <count> People ...", computed from the people it lists, and a short By the Numbers section after the contents: the authors, developers and presenters, and how many people work in two or three of those ways. Both are computed each run, so neither can go stale the way a typed count did.

## 1.72.16 -- 13 October 2026

- **The development kit comes before the installed one, everywhere.** The installer sets the HomerDev variable to the installed kit, which lags the development kit until it is installed, and several finders looked at the variable first. So MyBooks' kdpSubmit.cmd copied in the installed kdpSubmit, version 38, over version 39, and kdpSubmit stopped at once, looking for the single answers file version 39 replaced with one per book. kdpSubmit, kdpBooks, kdpUpdate and buildBooks (their launchers and buildBooks.locateKit), kind.findKit, and the kind.py check.py imports now look beside and above the project, then at the top of each drive, and use the variable last. The book launchers write the kit they chose, and its version, to their setup log.

## 1.72.15 -- 12 October 2026

- **The kit's own build_release.bat was an old runner all day.** Every project's runner was replaced by the kit's build, but the kit's own cannot be -- the build runs inside it -- and a runner from before the cycle lock never replaces itself. So the kit's cycle ran without the lock, and two kit cycles started two minutes apart ran at once: the second failed on HomerDev_setup.building.exe, which the first was writing. HomerDev.zip now carries the current runner as build_release.bat, which from then on replaces itself at the end of each cycle, and the kit's build names an outdated one in the console.
- **The kit's release passes -SkipCheck,** as releaseHomerDev does: push's gate has just run checkHomerDev, and release.ps1's own check is the one for apps.

## 1.72.14 -- 12 October 2026

**Camel Type throughout: constants without c_.** Camel Type names a constant exactly like a variable, type prefix and all -- sFormat, iMaxRetries -- set apart only by being declared as a constant. The c_ prefix is obsolete, yet the C# and JAWS guides said so while the Python guide and the homer-code skill still prescribed it, and the kit's own code used it 308 times.

- **The kit's code is renamed:** 308 constants and 1,057 references in 66 files, Python, C#, PowerShell and JavaScript alike. Where a constant and a variable made from it shared a name, the constant now says what it holds: lAllSamples beside lSamples, dDefaultHeaders beside dHeaders, lAllShows, lBlockingNames, iRunsPlanned, dSourceFiles, sNotesName, sProjectName, sTextNamespace, lsTextExtensions, sHereFolder. Every Python file compiles, and the kit's self-tests pass: the 122 harvesters makeHarvester writes, tidy's, the KDP tests, fixPages and the fingerprint store.
- **tidy renames them in every project.** scripts\\camelType.py renames each constant written with the old prefix, and every reference to it -- through a module or a class too -- and leaves, and names in the log, any whose plain name is already used beside it, for a person to name. Library names such as ctypes.c_int are never touched, nor are documents. push's check builds an app before staging, so a rename that broke a build would stop there.
- **The guides agree.** A new CamelType.md gives the rules every language shares; guides for JavaScript, PowerShell and VBScript join those for C#, JAWS scripting and Python; the Python guide, HomerDev.md and the homer-code skill no longer prescribe c_. The build copies all of them into the homer-code skill, and the HomerDev dialog lists every one as a document.

**A rebuild names what changed.** A job that ran because its inputs changed said only that; bookFido's installer was rebuilt with nothing edited, and the log gave no clue why. The fingerprint store keeps each input's hash, and a job that runs now names up to eight files changed, added or gone.

**An app's kit tools are refreshed before the build decides.** The template refreshed them after deciding whether anything changed, so a kit update to them reached the installer one cycle late. DbDo's build already had the right order.

## 1.72.13 -- 12 October 2026

- **The installer pattern check knows the /DEFAULTS entries.** It found the JAWS Install box by the exact words Check: isInstallJaws, so after 1.72.12 made that Check: homerFinishRuns and isInstallJaws, DbDo's check said the installer offered no Install box, and push refused to stage anything. Both forms now count. DbDo and bookFido had already compiled their installers with the 1.72.12 changes and published.

## 1.72.12 -- 12 October 2026

- **Every Homer installer takes /DEFAULTS:** what pressing Enter at every step would do -- install, run each finish-page entry ticked by default (Install and Update, not Reinstall, not the user guide), take the Results box as read, and launch the program when Launch is ticked. Alone, it starts setup again very silently with the same parameters, so one switch is enough. The pieces are in Templates\\HomerComponents.iss: homerDefaults, homerFinishRuns, which each finish-page entry's Check now includes in place of skipifsilent, and homerStartForDefaults, called first in InitializeSetup. help\\FinishPage.md explains it.
- **A silent install no longer waits on a box nobody can see.** homerResultsBox drew the Results box with Windows' own MessageBox, which /SUPPRESSMSGBOXES does not reach, so a /VERYSILENT install of any app built from the template stopped at an invisible OK. Silent, the results now go to the setup log.

## 1.72.11 -- 12 October 2026

- **A project's runner can no longer be stranded behind a stale lock.** Each project's build_release.bat is a copy of the kit's runner, and it replaces itself with the newer one only on its last line. bookFido's and DbDo's copies came from before the stale-lock rules; the locks their own dead cycles had left refused them at the start, so they exited before that last line, never updated, and were refused for hours -- the fix could never arrive. Now the kit's build replaces any project runner without those rules, unless that project's lock is under 30 minutes old (a cycle may be running it); so one kit cycle repairs every project beside it.
- **The development kit's runner comes first.** A project took its runner from the HomerDev variable, which points to the installed kit and lags until it is installed; it now takes the kit beside the projects first.
- **build_release unlock** clears a project's lock and starts the cycle, for when you know nothing is running; a refusal now says so.

## 1.72.10 -- 12 October 2026

**Every push from 1.72.5 to here ended in a syntax error, and took its cycle with it.** push.cmd's size check held `echo ... RepoFiles.txt (under 100 MB).` inside an if block; Command Prompt reads a whole block before running it, so that bracket closed the block early and the line was a syntax error -- ". was unexpected at this time." -- whether or not anything was large. A syntax error in a called batch file ends every batch file above it, so push stopped right after its staged list, build_release stopped with it before releasing its lock, and neither log said why. The bracket is escaped; the kit's audit and every project's check now read each batch file for a bracket that closes its block early (one rule, in scripts\\fixEncoding.py); and a lock left by a runner older than this one, with no record of its holder, is stale once it is 30 minutes old, so the locks those cycles left no longer hold their projects back for four hours.

The Homer principle that nothing unchanged is rebuilt or downloaded again, carried through the whole cycle.

- **An app build that changed nothing builds nothing.** Every app build stepped its version and recompiled its program and installer, so a cycle with nothing to change still made a new release. The app build template (Templates\\build_APP_.cmd) now asks first, through the kit's fingerprint store, whether anything the app ships changed since its last success: what the program is made from -- its sources, resources, icon, manifest, build.cmd, version.txt, fetched libraries and the kit classes it compiles in -- and what the installer packs. If nothing did, the program, its number and its installer stay, and release finds the version already published. If anything did, even a help page, the build is the full one with a new number, so the change reaches users rather than going out as the same version again. `build fresh` builds regardless. Existing apps get this as their build.cmd is brought up to the template; bookFido and DbDo have it now.
- **A sample is built only when what it uses changed.** Its inputs were the whole of exec\\CSharp, and exec\\Python for a Python sample, so a change to any kit class rebuilt all four. They are now the classes its build script compiles and, for a Python sample, the kit modules its --hidden-import list imports, directly or in turn. HomerDev.exe likewise depends on its own fifteen classes, not the folder.
- **Homer.dll is built when its classes change.** It was compiled on every build.
- **Kit tools are refreshed into an app only when they differ,** so the log no longer says every tool was refreshed when none changed.
- **The fingerprint store accepts an input on another drive,** as an app's build names the kit's classes and the kit may sit elsewhere.
- **The build-release skill states the rule** for every new step: name its inputs and outputs, check before the work, record after success.
- **A convention-database skill,** for the convention or conference of any organization. It builds a DbDo database from the event's agenda -- sessions with their dates, times and rooms, speakers and sponsors, and the programs and products the sessions feature, linked so a screen reader user goes from a session to who presents it and where -- and ships an empty Convention.db with the schema and link kinds, the scripts that turn marked sessions into a calendar file, an accessible schedule and contact cards, the queries and reports, and the lessons of the 2026 convention database DbDo has retired.
- **A refused cycle points to the window that holds the lock.** A cycle still open in its own Command Prompt -- perhaps waiting at a sign-in window, or still uploading -- keeps its lock; the refusal now names that cycle's log and says that closing its window ends it, after which the next build_release starts at once.
- **SKILL.md files stay without a byte order mark,** as the kit's encoding rule says; the build-release skill's was written with one and stopped the 20:13 build.

## 1.72.9 -- 12 October 2026

- **tidy keeps every file the build compiles.** bookFido's build.cmd compiles PdfStructure.cs (its appSources line), but RepoFiles.txt did not name it, so tidy moved it into notes\\other as a stray, the repository never carried it, and the next build stopped: "Source file PdfStructure.cs could not be found". A file in appSources is now named whether or not RepoFiles.txt says so, pushed with the rest, and the omission is reported so the line gets added.
- **A lock whose cycle is gone is cleared at once.** A build_release window closed mid-cycle left its lock for four hours, refusing every cycle of that project. The lock now records the process running the cycle; when that process is gone, or its number belongs to a process started after the lock, the lock is stale whatever its age. A living holder only keeps the refusal, which now names the holding cycle's log, since a cycle stopped with Control+C leaves its Command Prompt running.
- **A semicolon comment ends a plain inix value.** An empty asin = in MyBooks' books.inix, followed by the comment lines describing the next book, read as a plain value holding those comments, and kdpReport printed them as Blind Vibe Coding's ASIN. inix.py and Inix.cs both end a plain value at a semicolon comment now, and help\\Inix.md says so. A line beginning with a number sign stays part of the value, since a Markdown heading begins that way; the writers fence every multi-line value, so nothing they wrote reads differently.

## 1.72.8 -- 12 October 2026

- **push says when a large upload is under way.** A 67 MB catalog takes minutes to commit and upload, and push said nothing in that time, so a log copied while it ran read like a hang to an auditor. When a large file named in RepoFiles.txt is going up, the console now says it can take several minutes, and the log stamps the start of the commit and of the upload, as it already stamped the finish.

## 1.72.7 -- 12 October 2026

- **kdpSubmit names the book, never guesses it.** With one answers file a bare run used it, so the run meant to republish two corrected music books opened Blind Vibe Coding, the only book on file (it changed nothing: every field was already right, and KDP would not open the Content tab of a book with an update in review). With more than one book on file, a run without --book now does nothing and lists the command for each.
- **A live book's manuscript can be replaced without touching anything else.** An answers file may keep, exactly as KDP holds them, the Details tab (keepDetails = Yes: the run starts at Content), the Pricing tab (keepPricing = Yes: nothing on it is clicked, since pressing All territories or the lending box would change a setting already right), the cover (coverFile = Keep KDP's cover) and the AI-generated content answers (aiContent used = Keep). The last matters for books whose text tools and image tool KDP holds separately: the single tools answer would have put the text tools in the image box. A kept book still needs its kdpTitleId and title, so the Bookshelf row is found and its status checked.

## 1.72.6 -- 12 October 2026

From audits of the help guides, the podcast directories and Tech Training, each finding checked against the published pages before any change.

- **Every finished page now declares its language, has a main landmark and a labeled contents list, and holds only links that go somewhere.** scripts\\fixEncoding.py gains finishPage beside the heading rule, so every Homer build applies it. Repeated IDs are made unique; a link to an anchor the page lacks is repaired when exactly one ID matches it but for punctuation or a numeric suffix, and otherwise becomes its own words; empty links are removed; a bare domain gains https://; Markdown inside an address yields the address inside; and an address relative to a publisher's site, which no reader of the page can reach, becomes its own words. A page is changed only where a rule applies, and a finished page comes back unchanged. On the published help guides it repaired 879 links, made 849 repeated IDs unique and removed 11,409 empty links; 8,810 links to anchors that never came with their articles became text.
- **scripts\\fixPages: one page finisher for every collection.** Version 3 lived in AppHelpGuides; the kit's version 4 rebuilds each page from its .md and finishes it, or with --pages finishes the published pages as they are, and logs to the collection's logs folder. A page with no title of its own takes its first line as its title -- version 3 titled the podcast announcement "Help guide". A collection's data\\linkFixes.inix holds verified corrections, so a fix survives the next build. AppHelpGuides and PodcastDirectories keep a small launcher, not a copy.
- **buildGuide resolves a publisher's relative links, and keeps text that names a tag as text.** A Zendesk article's own address now resolves its relative links exactly; without an address, a relative link keeps its words and drops the dead link. A publisher's sentence about heading tags had become real level-one headings on five guides (Calibre, Craigslist, HumanWare, Kindle Direct Publishing, Org Mode); text outside a code block now writes "<" as &lt;.

## 1.72.5 -- 12 October 2026

- **push publishes a large file that RepoFiles.txt names exactly.** Anything staged over 10 MB still stops the commit, since such a file was fetched, built or recorded, and the guard exists because 480 fetched voices were once swept in by a folder line. But a project may mean to publish one: DbDo ships its 67 MB RadioTrail catalog, and the repository now carries it too. A RepoFiles.txt line naming that one file, not a folder holding it, is the deliberate choice, and it passes up to GitHub's own limit of 100 MB. Over 100 MB, push stops rather than letting GitHub refuse the push.

## 1.72.4 -- 12 October 2026

The cache that lets a cycle skip unchanged work had three faults, found from the logs of the day's cycles, where the four sample programs were built four times with none of their sources changed.

- **A save no longer erases what others recorded.** fingerprint.py wrote back the whole store as it stood when it was opened, so a process opened earlier and saved later erased every record made in between. checkHomerDev opened the store, recorded each sample it built, then saved its own pass over them; the next build found four programs it had no record of and rebuilt them all. A save now rereads the store and writes only the entries it changed. Every script that uses the cache gains this, in every Homer project.
- **A pass is recorded for the files as the check left them.** check and checkHomerDev recorded the fingerprint taken before they ran, but a passing check runs builds that rewrite programs and generated files, so the next check, a minute later in release, found the files changed and ran in full: DbDo was compiled three times a cycle. Now release reuses push's pass.
- **A build product is not an input, and a check rebuilds only what changed.** FruitBasketPy rebuilt every cycle because version.py, which each Python sample's build writes naming itself, was counted as one of its sources; version.txt is the source. And checkHomerDev cleaned and rebuilt all four samples whenever it ran; it now builds only those the cache does not call current, and cleans only what it will build. --fresh and --deep still build everything from clean.

## 1.72.3 -- 12 October 2026

- **The chat no longer vanishes after a spoken question.** Two faults together. Lbc's runWithButtons replaced a dialog's own default button with its first footer button, so Enter in the question box pressed Close, not Send; and when the chat closed while Whisper was still writing down a question, the transcription thread reached for the closed dialog, and the error ended HomerDev on the spot. The log stopped right after Whisper's line, with no session end. Now a default the dialog sets is kept, for Enter and Control+Enter (Lbc, so every Homer app gains it on its next build); both chat workers are guarded and set aside anything that arrives after the chat closed; and closing the chat stops the listening and the recorder, and is logged.
- **A crash is always written down.** Log.start now records any error nothing caught, with its stack, before the program ends. Every Homer program that keeps a Log gains this.
- **connectAI takes away only its own links, and says when linking failed** (from an audit, both reproduced first). --remove removed any skill link of a kit skill's name, so another tool's link was disconnected too; it now removes only links into the kit, judged by whole folder names, so a folder such as HomerDevOld is not mistaken for the kit. And a tool was reported connected before a single link was tried; now a tool whose links failed is reported as not fully connected, with the count, and connectAI ends with code 3.

## 1.72.2 -- 12 October 2026

- **checkDb logs in the project's logs folder.** It wrote each database's log in a logs folder beside the database, so checking DbDo made a logs folder inside templates\\RadioTrail, twenty-four logs deep by 11 October, outside the project's logs and against the Homer pattern. A database inside a project now logs to that project's logs folder as `<Project>-checkDb-<Name>-<stamp>.log`; the project is the nearest folder above the database holding a build script or RepoFiles.txt. A database outside any project still logs beside itself. The log is opened for appending, so two checks in the same second no longer overwrite each other.
- **Four more help estates in makeHarvester:** edX (its learner and business help centres, one volume), Skillshare, MasterClass (each of its product sections) and The Great Courses Plus (its one FAQ page). Every seed was seen answering before it was written, and each fence is tested against addresses it must take and refuse, its own seeds included.
- **makeHarvester's chassis had every backslash doubled,** so each harvester it wrote found no links on any page and crashed writing its manifest: a pattern read `href\\s*=` and matched nothing, and a line ending read as the four characters backslash-r-backslash-n. The four learning-platform harvesters showed it on their first run. All seven lines are corrected, and makeHarvester now TESTS EVERY HARVESTER IT WRITES -- loading it, finding links in a sample page, and writing a manifest -- and refuses to call one written that fails. All 122 pass; today's broken ones fail it.
- **buildGuide's bare-address gate skipped the front matter.** It flagged each guide's own license address, which the builder itself writes, so every guide built here failed that gate.

## 1.72.1 -- 11 October 2026

- **The Results box's AI line reads as it should.** The first install to connect the AI tools said "Claude Code and Gemini CLI and Antigravity", the Gemini entry's own "and" running into the list's; it now says "Claude Code, and Gemini CLI with Antigravity".
- **createHomerDevRepo leaves RepoFiles.txt.** Both of its files were listed but in no folder and not in git, so every build warned about them since 1.70.1 began restoring listed files.

## 1.72.0 -- 11 October 2026

- **The setup program connects the AI tools; the dialog's button is gone.** Telling Claude Code, Codex, Gemini CLI and Antigravity where the kit is was a button in the HomerDev dialog; it is now a step of the install. connectAI runs hidden, as the person who started setup, since it writes into their own profile, and writes one line naming what it connected, which the Results box shows -- or says that none was found, or that Python is needed first. An earlier setup's line is cleared at the start, so it is never reported as this one's. Walks 2 and 8 and the guide say so.
- **The Results box reports every component.** Its list still named the first eight of 1.66.0's ten, so Ace by DAISY, EPUBCheck, Git, GitHub CLI, Java, Node.js, Python, Tesseract and Whisper never said what happened to them; all seventeen now do, and the model's line says it answers questions about the kit, not that it translates.

## 1.71.1 -- 11 October 2026

- **The leftover Samples folder is removed, as 1.69.2 meant.** Its removal failed with "cannot access local variable 'shutil'": an import of shutil further down the same function made the name local to all of it. That import is gone, since shutil is imported at the top. Tested: the folder is removed and logged.
- **The 60-minute build of 11 October was a one-time cost.** tidy's deletion took the help folder's spoken tutorials with it, which the kit's zip does not carry, since the build makes them; so all ten walks were spoken again, though only walk 2 had changed. The next build speaks only what changed.

## 1.71.0 -- 11 October 2026

- **A skill for adding a library: homer-library-source.** bookFido's five libraries were added the same way, and the NLS harvest, the newest, touches 26 functions. The skill writes that down: research where a library lives and how Windows can reach it, from a real sample, before any code; choose a browser, file or API source; build the ten touch points from the opening dialog to BookTrail; the rules every source keeps; and how to prove it. Apple Books is the worked example: its library lives in Apple's apps, so its candidate routes -- the Mac's library database copied across, Apple's purchase history in a browser -- are listed as unconfirmed until seen on the user's own devices.
- **Claude Code runs clean, after The Chat Place.** Kelly Ford's AIChat, the source of The Chat Place, strips the variables a host Claude Code session sets (some make a child wait for the host's login) and those that would move a turn off the subscription to per-use billing or another endpoint, such as ANTHROPIC_API_KEY. HomerDev's chat now does the same, by name and by family, and names its session "HomerDev questions" on every turn, so Claude's own session list shows it. Its question already went on standard input, never on the command line, which is the protection behind The Chat Place's refusal of the npm claude.cmd.

## 1.70.2 -- 11 October 2026

- **tidy no longer deletes the kit.** On 11 October, after HomerDev was installed, the HomerDev variable named the copy in Program Files. tidy, run in C:\\HomerDev, recognized the kit, but then compared it with that installed copy, found its files byte for byte the same, and deleted 235 of them as "stray kit files" -- the shared C# and Python classes, the skills and agents, the help, the templates, build.cmd, RepoFiles.txt and checkHomerDev.cmd -- so the cycle stopped with "checkHomerDev.cmd is not in this project". This is also the likeliest way exec\\conversions.inix went missing before. A folder that is a kit itself is now its own kit, so every test that skips the kit holds; and of several kits found, the newest is taken, so an older installed copy never feeds files into an app. Tested with the HomerDev variable naming a second kit: nothing in the kit removed, and a real stray in an app still removed. Unarchiving this kit's zip into C:\\HomerDev puts every deleted file back; the build restores exec\\conversions.inix from git, as it did at 16:27.
- **The new install scripts no longer print their comments.** installAce, installEpubCheck, installGit, installGitHubCli, installJava, installNode and installPython began with their rem lines and turned echo off only after them, so the finish page's windows showed every comment as a command.
- **Confirmed by a speech history and its log:** asked by voice, the chat wrote the question down, said "10 seconds" while waiting, answered in 16 seconds, and spoke the answer; Claude Code was found and offered.

## 1.70.1 -- 11 October 2026

- **The build restores what the repository carries.** exec\\conversions.inix, the conversion engine's route table, went missing from the kit's folder, and every build after it failed its conversion test; the error 1.69.2 began logging named it at once ("no conversions.inix beside exec\\Python"). Each single file RepoFiles.txt names that is not on disk is now taken back from the last commit, said and logged; one git lacks as well is logged as a warning. Tested in a scratch repository with the table force-added, as the kit's own is.
- **The fruit baskets stayed built.** The 16:16 build skipped all four samples as unchanged, the first build since 1.69.0 to do so.

## 1.70.0 -- 11 October 2026

- **Asked by voice, answered by voice.** An answer was written into the conversation but never spoken, even to a question asked aloud. Now a question sent as heard is answered aloud as well as in writing, and Speak answers speaks every answer. Send when heard is on by default, so a spoken question needs no key.
- **Claude Code can answer.** When it is installed (claude on the PATH, in .local\\bin, or from npm), Ask with offers it beside the local AI. It runs headless in the kit's folder, where CLAUDE.md and the skills describe the kit, in plan mode, so it reads and changes nothing; the question goes on its standard input, so no character in it can break the command; and the dialog is one conversation, named with --session-id and continued with --resume. The button is now Ask an AI.
- **Keys after The Chat Place**, Kelly Ford's accessible companion for Claude Code: Control+Period stops waiting (a late answer is set aside, and Claude Code is ended), Control+Shift+R says the last answer again, Control+Shift+C copies it.
- **Progress that leaves a trace.** Each ten-second update also sounds a soft tick and is logged by name, so a log shows whether it ran even if the speech was not heard. On 11 October the updates were reported unheard; the code was right, so the likeliest cause is an older installed copy, which the title's version now makes easy to check.

## 1.69.2 -- 11 October 2026

- **A failing conversion test now says why.** Two builds stopped with "the conversion test" failed and the log held only "testConversion exit 1": the test's standard error, where a crash writes its traceback, was captured and dropped. Every line of it is now in the log, and its last line is said.
- **The setup program ships no build leftovers.** A Samples folder at the kit's root, left from an older layout, held PyInstaller's work folders, and the setup program installed them. The build now retires that folder, and the setup program leaves out any root Samples folder and PyInstaller's work files.
- **Program output is quoted, not judged.** check.py logged a program's output at ERROR whenever it held the word FAIL, so extCheck's help, which lists its FAIL verdicts, put 123 ERROR lines into a check that passed. Output is now logged at INFO; the check decides pass or fail as before.

## 1.69.1 -- 11 October 2026

- **The developer's own tools are components too: Git, GitHub CLI, Node.js and Python.** HomerDev recommends all four -- push and release use Git and gh, the kit's scripts are Python, Ace by DAISY runs on Node.js -- so its setup program now offers them, seventeen components in all, alphabetically. Each script asks winget by every package id the tool is known by (Node.js as OpenJS.NodeJS.LTS or OpenJS.NodeJS, Python as 3.14 or 3.13) and upgrades the one found, so a copy registered under one id never gets a second beside it; Reinstall forces the same id. installAce now calls installNode rather than keeping its own copy of that logic. EdSharp's older installNode, installPython and installGitHub were the starting point; the kit's follow the shared pattern instead.
- **installModels.cmd is in the kit at last.** The setup program's model entry, for the chat's qwen2.5:7b, named it from 1.66.0 on, but it was never here, and the entry's "skip if it does not exist" flag hid that: it did nothing, in silence. It takes the models to fetch as arguments, defaults to the chat's, finds Ollama in its own folder when the PATH does not show it yet, and relies on ollama pull, which downloads only the layers that changed.
- **The kit's check names any script the setup program runs that the kit lacks**, so that cannot happen again. Tested both ways.

## 1.69.0 -- 11 October 2026

- **The fruit baskets are no longer rebuilt every cycle.** checkHomerDev, which push runs, builds every sample from clean, and a compiler stamps each program with the time, so the program it left differed byte for byte from the one the build had recorded; the next build saw "FruitBasketCs.exe changed since it was made" and rebuilt all four, with nothing changed. A sample the check builds is now recorded in the same cache, from the build's own list of what a sample is made from. Tested: build, a clean rebuild by the check, then a build that built nothing.
- **The book tools are machine-wide components, with version comparisons.** HomerDev's setup program now offers Ace by DAISY, EPUBCheck and Java alongside the other ten, each worded Install, Update or Reinstall by what is there. installJava asks winget for Microsoft's OpenJDK 21 by package id, not a java on the PATH, which an older Java 8 can answer for. installEpubCheck puts EPUBCheck, which has no installer, in %ProgramFiles%\\EPUBCheck, and downloads only a release newer than its version.txt. installAce installs Node.js if npm is missing, compares npm's latest Ace with the installed one, and installs only a newer one. buildBooks uses the machine-wide EPUBCheck when it is there, still compares it with GitHub's latest every toolRefreshDays, and says what updates it.
- **Kindle Previewer is left to buildBooks, on purpose.** winget's Amazon.KindlePreviewer is version 3, which Amazon no longer supports; version 4 installs as an app package winget does not list, and keeps itself current. A finish-page entry would have offered to install version 3 over version 4. buildBooks already finds version 4 first, installs with winget only when nothing is there, and runs version 3's own update weekly when it is all there is.

## 1.68.1 -- 11 October 2026

- **The HomerDev dialog says its version as it opens**, in its title. On 11 October its progress updates and Voice button seemed missing because Alt+Control+Shift+D opened the copy setup had installed, 1.66.0, while the kit had moved on to 1.68.0; both features were built, and the v1.68.0 setup program carries them. F11 in the dialog, or the latest setup program, brings an installed copy up to date.

## 1.68.0 -- 11 October 2026

- **Ask by voice, in the HomerDev dialog's chat.** Voice (Alt+V) records a spoken question and Whisper writes it into the Question box, all on this computer. It follows the convention of Windows+H voice typing: the same key starts and stops; silence after speech, about a second and a half, also stops; Escape throws the recording away and keeps the dialog open. Rising and falling tones, not speech, mark the start and the end, so the screen reader is not recorded into the question. The dialog then says what it heard, for the person to correct and send; Send when heard sends it at once.
- **Voice.cs, a new shared class**, so any Homer app can do the same: VoiceRecorder records 16 kHz mono through Windows' own waveIn, judges speech against the room's noise floor a tenth of a second at a time, and writes a WAV; Voice.transcribe runs whisper-cli on it, finding Whisper and its model where the Homer installers put them. Polled from a timer on the window's thread, so no callback thread touches the window; a final pass after the microphone is reset collects without requeuing, so no buffer is freed while Windows holds it.
- **Why a key, not a wake word (researched 11 October 2026).** Starting by a spoken word needs a wake-word model; the free one, openWakeWord, licenses its trained models CC BY-NC-SA 4.0, for non-commercial use only, which does not fit the kit's MIT license, and the strong alternatives are commercial. Whisper (MIT, via whisper.cpp) is already a Homer component.
- **The guide lists all seventeen C# classes.** It said "Twelve modules" and described ten; Elevate, Media, MediaPlayer, Mpv, Ollama, Paths and Voice are now listed, alphabetically, each checked against its own file.

## 1.67.0 -- 11 October 2026

- **Any project's AI assistant finds the kit: scripts\\connectAI, and Connect AI tools in the HomerDev dialog.** An assistant started in a person's own project knew nothing of the kit unless told each time. connectAI, run once, puts a short pointer to the kit -- where it is, and to read its AGENTS.md first -- in the personal instruction file of each AI tool on the computer (Claude Code's .claude\\CLAUDE.md, Codex's .codex\\AGENTS.md, Gemini CLI's and Antigravity's .gemini\\GEMINI.md), between marker lines it alone writes, and links each of the kit's skills, as a Windows junction, into each tool's personal skills folders (.claude\\skills; .agents\\skills and .codex\\skills; .gemini\\config\\skills and .gemini\\antigravity\\skills), so they are always the kit's own. Only tools whose profile folder exists are touched; a skill folder of the person's own is never replaced; --check reports, and --remove takes everything out and leaves each file exactly as it was. Tested both ways, including a person's own skill of the same name and their own instructions in the same file. The locations were checked against each tool's documentation and current reports on 11 October 2026.
- **The guide says what to tell an AI**, in a new chapter, "Telling your AI about HomerDev": connect once, or one sentence each session; examples of requests; and each tool's own way, including Claude Code's plugin. AGENTS.md says how to find the kit by itself, and llms.txt names connectAI.
- **The chat says it is still thinking.** Every ten seconds of waiting, it says how long, briefly, and the status line says the same; when the answer comes, how long it took. On 11 October a question met silence until "Answered", heard after its asker had moved on. The model is now asked for plain text, and any Markdown it writes anyway -- asterisks, pound signs, code ticks -- is removed before the answer is shown, since a screen reader read them aloud.
- **The tutorials cover the dialog and the AI connection.** Walk 2, Install and Launch, now installs with the setup program and its finish page, names C:\\HomerDev as the command-line choice, and opens the HomerDev dialog, searches it, runs the fruit basket from it and tours its buttons; it had said the kit is never installed in Program Files. Walk 8 connects the AI tools and says what to type, with and without connecting. Both stay under five minutes; reader lines not yet heard live carry the note asking for a live run.

## 1.66.1 -- 11 October 2026

From a follow-up audit by another AI, read against the logs of that day.

- **One cycle per project at a time.** Two cycles of the same project overlapped: an older cycle's release found an installer a newer, failed build had just written. build_release now takes a lock, a folder in %TEMP% named for the project, and a second cycle of that project refuses to start; different projects still run side by side. A lock older than four hours, left by a window that was closed, is cleared and logged. The lock is released on both exits.
- **An acceptance file that runs nothing fails.** FileDir's accept.inix stated its acceptance in prose, with no runnable check, and was reported as not checked release after release. A file present but holding no [check] with a Run line now fails the check; an app with no accept.inix is still reported as not checked. Every app's file was counted first: only FileDir's had none, and it is rewritten with sixteen runnable checks.
- **The setup program survives a failed build.** Inno removes its output before writing, so a failure left none. HomerDev_setup.building.exe now replaces HomerDev_setup.exe only when complete, and "EndUpdateResource" (error 110) is retried at most twice, ten seconds apart.

## 1.66.0 -- 11 October 2026

The kit gets a program, a setup program and a standard place: the kit now shows what it holds, and uses its own classes to do it.

- **The HomerDev dialog**, exec\\HomerDev.exe, opened by Alt+Control+Shift+D after setup. It lists everything the kit holds -- documents, the plugin, samples and their sources, scripts, shared code in both languages, skills, subagents, templates -- each with a line saying what it is, and opens the one chosen: a page in the browser, a sample program to run, any other file in a reading window. Its buttons play the kit's ten tutorials in the Homer Player; explain the inix format and show what the kit's own reader makes of an example; explain Layout by Code, then open the dialog that very code builds; and ask the local AI through Ollama, which is first given llms.txt, AGENTS.md and the list of the kit's files with their paths. F11 checks for a newer HomerDev. It is built only from kit classes: Lbc, MediaPlayer, HelpDialog, Ollama, InixCodec, Elevate, Paths and Log.
- **HomerDev_setup.exe** installs the kit to C:\\Program Files\\HomerDev, with the desktop hotkey, from HomerDev_setup.iss, which follows the shared installer pattern and passes its check. Its finish page offers every component any Homer app offers -- ExifTool, ffmpeg, ImageMagick, mpv, Ollama, Pandoc, PDF tools, Tesseract, Whisper and yt-dlp -- and the AI model the chat uses, each worded Install, Update or Reinstall by its state; there are no JAWS scripts or NVDA add-on, since the kit has none. It sets the machine-wide HomerDev variable only when none is set, so a developer's own copy, such as C:\\HomerDev, stays the kit every app builds against. Unzipping the kit anywhere still works the same.
- **The build makes both**, exec\\HomerDev.exe after Homer.dll and the setup program last, since it ships everything; each is skipped when nothing it is made from changed. Inno Setup is installed with winget when missing, as every app's build does.
- **The kit is still the kit** with a program and an installer of its own: kind.py now lets HomerDev.cs and HomerDev_setup.iss stand at the kit's top, while any other installer or program, such as DbDo's after a kit zip was unpacked into C:\\DbDo, still makes a folder that app. It also names a folder's own installer first. Tested on four layouts.
- **One copy of each component's install script, in the kit.** They lived only in the apps, and diverged: four versions of the Pandoc script, two of ExifTool's and two of PDF tools'. The kit's scripts folder now holds one of each, taken from the app whose copy was most complete, for HomerDev's setup and, next, for every app's. FileDir's PDF tools script, taken here, could not install anything: on a computer with no Python it said Python was installed and failed, and its install block sat under a label defined twice, which nothing reached. Its three paths -- install, update, reinstall -- are now each reached.
- **Tidy no longer crashes on an installer's excludes that hold a backslash.** Adding build leftovers to an installer's Excludes passed the new list to re.sub as a replacement pattern, so a path such as \\logs\\* read as an escape code and tidy stopped with "bad escape". The list is now inserted as plain text. Found by running tidy on the kit with its new installer.
- **Documents**: the guide's Install the kit gives both ways, setup or the zip, with C:\\HomerDev suggested for shorter paths at the command line, and a new chapter describes the HomerDev dialog; the ReadMe and Hotkeys say the same.

## 1.65.34 -- 11 October 2026

Work is done when what it depends on changed, and not otherwise. One cycle of the kit built the four samples three times -- in its build, in push's check and in release's check -- and ran the 42-second conversion test every build, with nothing changed.

- **One shared cache, scripts\\fingerprint.py.** A job's fingerprint is one SHA-256 over its input files (by relative path and content) and any extra text, such as a tool's version; it is current when that matches the fingerprint recorded after its last success, and its outputs still exist unaltered. A changed input, a missing or altered output, or no record runs the work, and only success is recorded, so a failure is always retried. Each file's hash is remembered with its size and date, so an unchanged tree is not read again. It also answers when a tool is due to be checked on the web. The store is exec\\fingerprints.json, beside the outputs and never in git; deleting exec makes everything run. Batch files use it as `python scripts\\fingerprint.py check|record <project> <key> --in ... --out ...`.
- **The samples build when they changed.** Each sample's inputs are its own source, its build script, the version files and the kit code it compiles in -- exec\\CSharp for every sample, exec\\Python too for the Python ones -- and its output is its program. Tested: an unchanged build built none; one edited source rebuilt one sample; a change to the kit's Python rebuilt the two Python samples; a deleted program rebuilt just that one.
- **The conversion test runs when a route could have changed:** the test, the kit's Python code, the routing table, or a converter on this computer, named by path and date so an upgrade counts. A failing result is never reused.
- **checkHomerDev and check reuse a pass for exactly the same inputs.** push and release both run the check; release now reuses push's pass when nothing changed between, and the evidence report says so, with when it passed and the fingerprint. `--fresh` runs every check anyway, as do checkHomerDev's --ui, --deep and --no-clean and check's --build; a failure clears the record.
- **buildBooks says what it knows about each tool.** It already kept each tool's path and version for seven days, in %LOCALAPPDATA%\\MyBooks\\data\\toolCache.json, but logged nothing when it had no record, so a first run and a lost record looked alike. It now says when it has no record, and when it writes one and for how long it holds. On 11 October Ace's check took 22 seconds (npm's folder, Ace's version, npm's newest); with a record, none of that runs.

## 1.65.33 -- 11 October 2026

- **Launch after setup works on a first install.** The installer template's Launch box wrote its marker into %LOCALAPPDATA%\\<App>\\logs before anything had made that folder -- setup makes it later, when it keeps its log -- so on a first install the marker failed (cmd exit 1, in bookFido's setup log) and the program did not start. The marker line now makes the folder first. Found by an audit of bookFido by another AI; Templates\\_APP__setup.iss and the six installers that copy it are fixed, and each still passes the installer pattern check.

## 1.65.32 -- 11 October 2026

Four high findings from an audit of the kit by another AI, each fixed with the audit's own closure test.

- **Tidy never commits or pushes.** With a tracked stray, tidy staged everything, committed and pushed before push had run the check, so a failing check could not stop what tidy had published, and a failed git step still let tidy succeed. Tidy now only untracks the stray (the file stays on disk), and a failed untrack fails tidy; push commits it after the check. Tested on a scratch repository: the remote stayed unchanged and no commit was made. Tidy also logs each phase, since a tidy that stopped after "Named by the project" on 11 October left no clue where.
- **The kit's check runs checkHomerDev.** scripts\\check said "run checkHomerDev instead" and returned 0, so release reported "The check passed" for the kit with no check run. It now runs checkHomerDev and returns its exit code; a missing checkHomerDev fails. Tested with a stub failing, passing and absent.
- **Required checks fail closed.** A build whose voices or tutorial audio failed said "The kit is complete"; it no longer does. The database check counted a failure only when its output matched a phrase, so a crash escaped it; it now trusts checkDb's exit code, treats a missing checker, timeout or crash as a failure, and checks every database rather than the first twenty. Tested with 21 databases and a malformed one.
- **A running build_release is never overwritten.** The kit's build rewrote every sibling project's build_release.bat that differed, even one running a cycle at that moment. It now only creates a missing one, and upgrades once a runner from before this version; every runner copies the kit's newest over itself on the line it exits by, which Windows reads whole before running.

## 1.65.31 -- 11 October 2026

- **The samples log in the kit's logs.** The four fruit-basket build scripts wrote their logs in Templates\\samples\\logs, outside the kit's logs folder, so a zip of logs left them out. They now write logs\\<Sample>-build-<stamp>.log at the top of the kit; a copy of a sample elsewhere logs beside itself. The kit's build moves any old sample logs into logs and removes the empty folder.
- **A sample that fails to compile says why again.** checkHomerDev read Templates\\samples\\build<Sample>.log for compiler errors, a name no build writes any more, so a failed sample build reported only its exit code. It now reads the newest <Sample>-build-<stamp>.log in logs.

## 1.65.30 -- 11 October 2026

- **Tidy keeps what the kit places.** Tidy took any file its project's lists did not name for a stray, including build_release.bat, which the kit writes at every project's top and which was running tidy at the time: DbDo's cycle ended in silence five times on 10 and 11 October, and scripts\\kind.cmd moved into notes on every run. build_release.bat and every kit tool in scripts now belong in the folder survey; git's whitelist is decided as before. `tidy --selftest` proves it in a scratch folder -- build_release.bat and a kit tool stay, a real stray still moves -- and fails the old behavior; the kit's build runs it as a gate.
- **Four scripts, gates inside.** build_release ran check as a fifth step. It now runs build, tidy, push and release only; push runs the project's check before it stages anything (checkHomerDev for the kit, scripts\\check for any other project) and commits nothing when it fails, and release runs it again before it tags. The build-release skill, AGENTS.md and the ReadMe say so.
- **Book scripts, from an audit of MyBooks by another AI.** buildBooks never replaces a manuscript with an older copy from a sources folder: an identical copy is removed, a different one is kept in notes and the conflict logged (the audit's reproduction now keeps the newer text). buildBooks refuses an unknown option or a --book with no name before doing anything. Its build fingerprint now reads the project's own templates where they are used. A failed build keeps the last EPUB: the new one is made as <name>.building.epub and replaces the old only when finished, tested with Pandoc succeeding, failing and succeeding again. kdpUpdate compares the build fingerprint, so a template fix with an unchanged manuscript is sent; builds only after its options pass, only the books named, and none for --list, --survey or --record. kdpSubmit reads each marketplace's price_vat_inclusive field alone, ending the false warnings that every price was blank.

## 1.65.29 -- 11 October 2026

- **The conversion table is published.** exec\\conversions.inix, the routing table conversion.py reads, was never pushed: .gitignore keeps all of exec out of git except its CSharp and Python folders. So the kit on GitHub had the conversion module without its table. RepoFiles.txt now names it, and tidy's whitelist puts it back, tested with git on a copy.
- **testConversion fetches pdfminer.six, and does not ask recognition for headings.** 1.65.28 began fetching pypdfium2, which made the text-recognition engine available. With pdfminer.six still missing, PDF to Markdown then fell past the structure route to recognition, which reads a picture of each page and so keeps no headings, and the build failed on "no heading". pdfminer.six is now fetched too, so the structure route runs, and the recognition route is held to the marker word alone.

## 1.65.28 -- 11 October 2026

- **One check and one push per cycle.** For the kit, build_release's release step was releaseHomerDev, which ran checkHomerDev and push again right after the cycle had run both; on 11 October each ran twice. The cycle now calls release directly, as for every project; releaseHomerDev remains the one command for releasing the kit by hand.
- **testConversion fetches its sample packages.** Without pypdfium2 it could not make the scanned-PDF sample, and said so. It now installs pypdfium2 and Pillow with its own Python when missing, each attempt logged.

## 1.65.27 -- 11 October 2026

- **releaseHomerDev passes -SkipCheck only when release takes it.** release.ps1 belongs to a separate project and is not in git. The copy in scripts on 11 October had no -SkipCheck, so PowerShell refused the parameter and kit 1.65.26 was pushed but never tagged. releaseHomerDev now asks release.ps1 first, passes -SkipCheck only when it is declared, and logs which.
- **releaseHomerDev writes in logs,** as `HomerDev-releaseHomerDev-<stamp>.log`, not beside itself.
- **Old logs move into logs.** The build moves checkHomerDev.log, releaseHomerDev.log, scripts\uiCheck.log and evidence-kit reports from their old places into logs, each move logged, rather than leaving them where a zip of logs misses them.

## 1.65.26 -- 11 October 2026

- **uiCheck runs only when asked.** build_release runs checkHomerDev as the kit's check, and checkHomerDev started every fruit-basket sample and pressed its keys, so windows opened in the middle of an unattended build and took the screen reader's focus. The programs check is now reported as not checked unless `checkHomerDev --ui` asks for it; nothing else runs uiCheck.
- **uiCheck finds each sample by its program, and closes every copy.** It held each sample by the process it launched. A one-file PyInstaller program starts a launcher, which starts the program as a second process, so the Python samples' windows were never seen and never closed; and a sample left open took each new launch by the one-copy rule. Windows are now found by the name of the program that owns them, looked up again at each step; every copy is ended before a test and after it, each logged; a failure inside UI Automation is named as one; and a list reporting lists of lists is flattened, which had failed with "expected str instance, list found".
- **checkHomerDev and uiCheck write in logs,** as `HomerDev-checkHomerDev-<stamp>.log`, `HomerDev-evidence-<stamp>.md`, `<Project>-uiCheck-<stamp>.log` and `<Project>-evidence-ui-<stamp>.md`. Written at the top of the kit, they were missing from a zip of the logs folder.
- **The kit's build no longer rewrites its own running build_release.** Windows reads a running batch file a piece at a time, so replacing it mid-run could make it execute garbage. The kit's copy now replaces itself on its last line, which Windows reads whole before running; projects' copies are written by the build as before.

## 1.65.25 -- 10 October 2026

- **A book build no longer pauses over tools it already has.** buildBooks searched the disk for Java and ran every Java it found, and searched for npm, started Node and searched for Ace, before reading the stamp that said Ace had been checked days ago. Each tool's path, version and check time are now kept in toolCache.json in the per-user data folder; while the record is younger than toolRefreshDays and its files exist, the tool is used at once, with no search and no process started. Only an old or broken record looks again and asks npm whether a newer Ace exists, installing only a newer one. A check is recorded even when npm or Kindle Previewer's -update fails, so a failure waits for the next period instead of costing every build. Tested: a fresh record is used, a record whose files are gone or that is eight days old is set aside, and no record means a search.
- **build_release is the kit's, and checks before it pushes.** Each project's build_release.bat was its own hand-made copy. scripts\build_release.cmd is now the one copy, and the kit's build writes it as build_release.bat at the top of the kit and of every project beside it, writing only when it differs, each logged; tidy and the kit's LocalFiles keep it local. It runs build, tidy, check, push and release, stopping at the first that fails: the acceptance checks used to run only inside release, after push had sent the code to GitHub. It writes logs\<Project>-build_release-<stamp>.log with the environment and each step's exit code and time, and ends with one line naming each step and its time. homer-build-release, AGENTS.md and the ReadMe describe the cycle.

## 1.65.24 -- 10 October 2026

- **Routes for AI agents.** The kit's skills reached only Claude Code working inside the kit's own folder. AGENTS.md now tells any agent -- Codex, GitHub Copilot, Gemini CLI, Claude -- what the kit is, how to use it from another project, where things are, which of the seventeen skills to read for which task, the two subagents, and the rules every agent follows; CLAUDE.md imports it, GEMINI.md and .github/copilot-instructions.md point to it, and llms.txt indexes the skills and documents.
- **The kit is a Claude Code plugin.** .claude-plugin/plugin.json makes the skills in .claude/skills and the agents in .claude/agents one plugin, homer-dev, and .claude-plugin/marketplace.json offers it from the repository: `/plugin marketplace add JamalMazrui/HomerDev`, then `/plugin install homer-dev@homer-dev-kit`. The skills stay in one place; the manifest points to them. Each build writes the kit's version into both files.
- **Two subagents, each for a review that would crowd a conversation.** homer-auditor audits projects against the kit -- installer pattern, tutorials, encoding, checks -- and reports, changing nothing; homer-listener reads tutorial walks against the app's real announcements and reports every reader line a screen reader would not say. No hooks or MCP servers: the builds already run every check, and nothing needs an outside service.
- **The check keeps the routes true:** every route present, both JSON files parse and carry the kit's version, every skill listed in AGENTS.md and llms.txt, every subagent's front matter naming it. The files other programs read keep UTF-8 without a byte order mark, listed in KeepEncoding.txt, which check now honours as fixEncoding does.

## 1.65.23 -- 10 October 2026

- **The reader speaks concrete words, and checkTutorial says so.** Many walks gave the reader a description in place of speech -- "(the current control, with its state and position)", "(the next record, its first column first)" -- which the template's walks began and every app copied; and the template's User Interface walk used one screen reader's name for a voice, "message voice". checkTutorial now fails a reader line in parentheses, the words "message voice", a template CHANGE ME left in a reader line, and an Overview that does not remind of Insert plus Up Arrow, Insert plus Tab and Insert plus T, each with a reader line, or that does not say Caps Lock serves in place of Insert. Tested both ways: it fails the old DbDo, EdSharp, FileDir and HomerView walks (37, 10, 9 and 24 problems) and passes every corrected project. The template's walks hold CHANGE ME lines for a new app's author; homer-tutorial states the rules.
- **HomerDev's own walks** follow them: the Overview's reminder of three keys with Caps Lock, the reader's typed words in place of "(each word echoed)", a named silence, and a long line in walk 7 split in two.

## 1.65.22 -- 10 October 2026

- **The installer pattern check reports as "pattern".** It shared the name "installer" with the older check that a function is not defined both in an app and in the kit, so a log line did not say which had run. That older check's failure no longer suggests defining the kit's guard to keep an app's own copy, which the pattern forbids; it says to remove the copy. Checked against the ten projects' latest logs: each passed the older check, and none had yet run the pattern check, which arrives with this kit.

## 1.65.21 -- 10 October 2026

- **One installer pattern, checked on every build.** Every Homer installer was meant to share one Finish page -- the verb (Install, Update, Reinstall) and tick of each box decided by the kit, so pressing Enter installs what is missing, updates what is stale and starts the app -- and to reuse the folder of an earlier install. The rule lived only in the homer-installer skill, and three apps kept code of their own: DbDo judged its JAWS scripts by DbDo's version, so every new installer said Update; EdSharp did not include HomerComponents.iss and asked for the folder on every reinstall; HomerView, like DbDo, kept its own wrappers behind HomerReaderWrappersInApp. check now has an installer check that fails any departure, naming each: no HomerComponents.iss, a folder not remembered (UsePreviousAppDir, DisableDirPage=auto, a fixed AppId), its own screen reader state, wrappers or version stamp, or no Install box for the JAWS scripts. Tested both ways: it fails the old DbDo, EdSharp and HomerView installers and passes the corrected ones, FileDir, HomerScribe, bookFido, 2htm, extCheck, urlCheck and urlFido.
- **An app's own screen reader script, asked the kit's way.** HomerComponents.iss asks the script HomerReaderScript names, by default installScreenReaderSupport.cmd; an app whose support needs more, as HomerView's chaining does, names its own, which answers the kit's question, "state jaws <file>". The verbs and ticks come from the kit's one function in every installer.
- **homer-installer states the pattern and the check;** components.md says the kit supplies the screen reader wrappers and how HomerReaderScript works.

## 1.65.20 -- 10 October 2026

- **homer-ui states when a choice is buttons and when it is a list.** A dialog whose whole job is choosing among options built into the program shows them as buttons with runWithButtons, each letter beginning a word, H left for Help, none for OK and Cancel; a pick list is for choices from the data or the session. DbDo's dialogs were reviewed against it and five were changed.

## 1.65.19 -- 10 October 2026

- **buildBooks compares Ace's version before installing it.** Every few days it ran npm install @latest whatever was installed, and npm reinstalled Ace by DAISY and its own copy of Chromium -- minutes of downloading when 1.4.6, the latest, was already there. It now compares the installed version with npm's (npm view downloads nothing) and installs only a newer or missing one, recording the version it checked; between checks it runs nothing at all, not even ace --version, which took 8 seconds. A check that cannot reach npm is tried again at the next build. Tested in five cases: current, within the refresh period, newer, missing and unreachable. The tutorial voices already follow this rule -- taken from exec, never downloaded again, each walk spoken again only when its fingerprint changes -- and their step took 1 to 5 seconds in every app.

## 1.65.18 -- 10 October 2026

- **tidy gives every page one level-one heading.** FileDir's and HomerView's releases failed the headings check although their builds' encoding passes had repaired the pages: HomerView's build.ps1 makes hotkeys.htm after the pass, and FileDir's build runs the pass before refreshing the kit's scripts, so its first build after a kit update ran the old fixEncoding. tidy runs after every build and before every push, already refreshed, so it now applies fixEncoding's own rule to each .htm beside a .md, skipping a library's folders. Tested on HomerView's hotkeys page (17 level-one headings to 1) and a FileDir page (2 to 1), with a library's page and a page without Markdown left alone and a second run doing nothing.
- **push names only what actually leaves the repository.** The step that untracks local files announced every candidate as "no longer pushed", 29 of them kit sources that git add -A put straight back, because the whitelist includes them. The untracking now goes to the log, and push names only a file staged for removal that is still on the disk; HomerScribe's two notes and package files were the real ones.
- **The announcement names the apps HomerDev stands behind:** DbDo, EdSharp, FileDir and HomerScribe, each in a few words, within its single address and grade 8.8.

## 1.65.17 -- 10 October 2026

- **A new announcement.** help\\Announce.md, from September, described the kit as foundations for Windows programs; it now announces HomerDev for building apps nonvisually with AI, in about 300 words of plain paragraphs with no headings or lists in its body, so the same text can be pasted into Facebook, LinkedIn and email lists. It directs readers to one address, the archive of the repository, and says that an AI assistant can examine that archive, take what is relevant and adapt it under the MIT License. checkDocs grades it 8.7; it notes the written-out address, which is deliberate, so it survives a paste.

## 1.65.16 -- 10 October 2026

- **The headings check skips a library's pages.** The check added in 1.65.14 walked into a sample's .venv and failed the kit's own release on wxPython's README and CHANGELOG, which are not the kit's pages. Folders starting with a dot, venv and site-packages are skipped, in check and in the kit's own check.
- **push untracks a file once it is local.** Git goes on staging a file it already tracks even when the whitelist .gitignore leaves it out, so a file newly named in LocalFiles.txt -- DbDo's 77 MB RadioTrail catalog, tracked since its 14-station start -- was staged again and refused as too large. push now untracks each file LocalFiles.txt names that Git still tracks; it stays on disk, and nothing LocalFiles.txt does not name is untracked. Tested with Git: the file untracked and kept on disk, nothing large staged, the commit made, a second run doing nothing.

## 1.65.15 -- 10 October 2026

- **Book editions for other stores.** A Draft2Digital edition of Blind Vibe Coding had been made by editing a copy of the Kindle EPUB by hand, so it would fall behind at the manuscript's next change. buildBooks now builds every edition named in configs\\editions\\<book>-<Edition>.inix beside the Kindle EPUB, from the same manuscript: exact passages replaced, each required to match exactly once or the book is not ready, and every link to a named host made plain text throughout the finished EPUB, citations included. Each edition is checked with EPUBCheck, has its own working folder and audit line, joins the build fingerprint, and keeps a book from being kept when its file is missing. The rules sit outside the book's folder, so the Kindle book's content fingerprint does not change and kdpUpdate, which sends only the Kindle EPUB, does not send it again. Tested by building Blind Vibe Coding's two editions: the Draft2Digital one matches the edition submitted by hand, its copyright page exactly, with no links to Amazon, and the Kindle one is unchanged.

## 1.65.14 -- 9 October 2026

- **One level-one heading on every page built from Markdown.** Nearly every Homer page had two: Pandoc made the front matter's title into a level-one heading, and the document's own `# ` line made another; pages that used `# ` for sections had many, and fixPages version 2, which emptied every title, left two pages with none. One rule now puts each page right, oneTitleHeading in scripts\\fixEncoding.py: a repeated title keeps one copy, an author's single `# ` heading stays the page's heading, only the extra level-one headings move down a level with the headings beneath them, and a page with none gets its own title. Every app's build already runs fixEncoding after converting its documents, so every app gets it with no change of its own; EdSharp, whose build.ps1 converts after the encoding pass, now runs the pass again. The kit's convertDocs no longer replaces a document's title with its file name, and normalizeHomer, makeTutorials, homer-convert's toHomerEncoding (which named fixEncoding its authoritative home) and the blind-creators skill use the same rule; fixPages version 3, for AppHelpGuides and PodcastDirectories, does too. check and the kit's own check fail a page built from Markdown without exactly one level-one heading. Tested on every page in every project: 199 of 199 come out with one, their structure kept.

## 1.65.13 -- 9 October 2026

- **The book wrappers refresh one another.** buildBooks.cmd and kdpUpdate.cmd refreshed only the book tools' .py files from the kit, so the kit's kdpUpdate.cmd, which builds first since 1.65.7, never reached the book project: the old copy there sent books without building, and Blind Vibe Coding was refused as stale. Each of the four book wrappers now refreshes the other three from the kit, never itself, since cmd reads a running batch file as it goes.
- **kdpUpdate says "their"** when several books are unchanged since their last submission.

## 1.65.12 -- 9 October 2026

- **Tutorials.htm uses the newest Pandoc, with a page title.** makeTutorials took the first Pandoc on the PATH, which on the author's machine was an old 2.19.2 ahead of 3.12, and every app's tutorial log warned that the page had no title. It now asks each copy its version and uses the newest, as the kit's other tools do, and gives the page a title from the guide's own heading, as a page title only, so no second heading appears.

## 1.65.11 -- 9 October 2026

- **pptx to PDF works.** The conversion engine hands each route a target ending in .part and renames it on success. Word saves under exactly that name, but PowerPoint adds the extension of the format it saves, so it wrote sample.pdf.part.pdf, and the rename failed with "cannot find the file specified"; the kit's pptx > pdf test failed on every build for a day. Office now saves into a folder of its own under a name with the right extension, and the result is moved to the target. Reproduced with an Office stand-in that saves as Word and PowerPoint do: the old engine failed and left the stray file, the new one wrote the PDF for both.
- **The build names what failed.** A failing conversion route ended the build with "1 sample build failed", which named the wrong thing. The closing line now names each failing part, with the failing routes themselves, such as "the conversion test (FAIL pptx > pdf)".

## 1.65.10 -- 9 October 2026

- **The log summary says "still running"** for a check that has failed a finding but not yet finished, where it said "no totals", which read as if the check had broken. A crash, with its traceback, still says "no totals".

## 1.65.9 -- 9 October 2026

From a conformance audit of eleven projects' logs.

- **check finds the kit's kind.py, however a folder is written.** loadKind searched the app's own scripts folder first and compared folder names as text, so a difference of letter case (c:\\ against C:\\) put the app's stale kind.py ahead of the kit's, and the checks of EdSharp, FileDir and HomerScribe crashed on a kind function they lacked. Kit folders now come first, and a module already loaded from elsewhere is replaced. Reproduced with the 1.65.5 check, which crashed with the same message, and passed with this one.
- **Apps refresh kind.py with check.py.** Five apps name the kit's tools in a written-out list that named check.py but not kind.py; updateAppBuilds now adds kind.cmd and kind.py to such lists too, and DbDo, EdSharp, FileDir, HomerScribe and HomerView carry the change.
- **Tutorials wait for the voices only to speak.** buildTutorials took the machine-wide voice lock before asking whether any walk needed speaking, so HomerView's build, all ten walks current, waited 34 minutes behind HomerScribe's. It now asks first; and an acceptance build (HomerAcceptance set) speaks nothing in every app, as DbDo's and EdSharp's builds already arranged for themselves.
- **makeTutorials writes Tutorials.htm** with Pandoc, in the Homer encoding, so an app whose build converts documents before the tutorial step still has the page; check had failed HomerView for its absence.
- **check's time limit ends the whole command.** A timed-out acceptance build is stopped with every process it started; HomerView's "timed out after 900 seconds" had come thirty-five minutes in.
- **check ignores __pycache__,** Python's own cache, which failed HomerView's layout check.
- **The log summary reports a running check or release as unfinished,** not failed; a crash keeps its traceback and stays a failure.
- **help\\examples, not examples:** the folder of tested projects for blind vibe coders moved into help, since a top-level examples folder shares its first letter with exec.


- **help\\examples: tested projects for blind vibe coders.** A folder in help (moved there in 1.65.9; a top-level examples folder shared its first letter with exec) holds small projects that go with the tutorials in *Blind Vibe Coding*, one folder each, with a ReadMe giving the request each answers. The first is the talking timer of chapter 2, moved here from the book's directory page so the kit is the one home for the book's projects. It was tested with a controllable clock: it refuses blank and out-of-range entries, runs one countdown at a time, announces each minute and the end, and keeps time from the clock on a slowed page.

## 1.65.7 -- 9 October 2026

- **One command for the books: scripts\kdpUpdate.cmd.** It builds any book that changed, then opens on KDP only the books that changed since their last submission, with no options to remember. buildBooks now keeps a book whose last audit names the same build fingerprint -- its sources by content, its catalog entry, the kdp and proposed sections of its data file, the kit's book templates and the Pandoc version -- says ready and names its exact EPUB; --all builds every book. kdpUpdate.cmd runs buildBooks first, and --no-build skips it. Tested: an unchanged book is kept with its warnings; an edit, a change to its proposals or a new Pandoc rebuilds it; kdpUpdate's own review notes do not; a book not ready, or whose EPUB is not the audited one, is never kept. testKdpUpdate: 102 pass.


- **kdpUpdate visits only books that changed (version 11).** A book's EPUB changed fingerprint with every build -- its time stamp and generated identifier -- so after buildBooks rebuilt all the books, kdpUpdate counted every one as changed and opened all their pages on KDP. A book is now unchanged when its sources and its answers match its last submission: kdpSubmit's bookSourcesSha hashes every file in the book's folder by relative path and content -- manuscript, cover, pictures, bibliography, styles -- counting text by its text, so line endings and a byte order mark alone are no change, and leaving out the build's own found.inix. No file name or time is trusted. buildBooks records the sources fingerprint in each audit, and kdpUpdate judges an EPUB stale when its sources no longer match, with the old time test only for audits from before. --record writes the current fingerprints as what KDP holds, without opening KDP, and --except leaves books out the way --book picks them. testKdpUpdate has ten new tests; 102 pass.

## 1.65.5 -- 9 October 2026

From the build, tidy, push and release logs of every project, 9 October 2026.

- **check uses the kit's kind.py.** DbDo's, EdSharp's, FileDir's and HomerScribe's builds refreshed check.py from the kit but not kind.py, which it imports, so their checks ran against an old kind.py and skipped the layout and installer findings ("kind.py has no standard folders"). When the kit is on the computer, check now imports the kit's own kind.py; an app's copy is used only without a kit.
- **A [Code] line that begins with ; fails check.** In an installer's [Code] section, which is Pascal, a semicolon is not a comment, and Inno stops with "BEGIN expected": HomerView's installer failed so, from comment lines added on 8 October. kind.issCodeSemicolons finds such lines, and check's isscode finding fails on them.
- **A subtitle is not a heading.** Three Announce documents, the kit's among them, repeated their front matter's subtitle as a heading under the title, so the page said it twice; checkDocs now reports it, and the kit's Announce no longer does it.

## 1.65.4 -- 9 October 2026

- **A project of several GitHub Pages.** MyPages keeps a folder per page in pages\, each named for the repository that serves it, and posts only the pages whose folders have changed since they were last posted. kind.py has publishesPages beside publishesBooks: such a project is a page project, pages joins its standard folders, and check judges its documents page by page -- each folder holds one page; a page with no title is noted, since posting names it after its folder -- with the ReadMe and License, and their .htm, at the top.

## 1.65.3 -- 9 October 2026

**The conformance backlog is empty: every departure found on 9 October is settled.**

- **PdfRead.cs went home to HomerScribe.** It was HomerScribe's own partial class, kept here as if shared; no other program could use it. The build retires the kit's copy, the guide, ReadMe, License and skills no longer describe it as a kit class, and the License now names the packages the conversion engine fetches instead. A shared way to read a PDF belongs to the conversion engine.
- **FileDir uses the kit's MediaPlayer.cs.** Its own copy was the same player before the kit made it general. The kit's player now moves an older settings file, kept one folder up beside data, into data the first time, so no choice is lost.
- **lbc.py works flat or in a package.** Its imports of say and util try the package form first, so HomerView's NVDA add-on can carry the kit's modules exactly; its build now copies them in. Tested both ways where it was written.
- **A copy, or only a name in common, for classes too.** check's class test matched on name alone, and listed EdSharp's MdiFrame and MdiChild -- the editor itself, over 14,000 lines each, sharing no member with the kit's Mdi -- as copies. A class now counts as a drifted copy only when it shares at least half its public members with the kit's class of that name; otherwise the clash is logged. DbDo's KeyMap, which shares a purpose with the kit's but 3 of its 11 members, is logged the same way.
- **The ReadMe and the guide list all sixteen C# modules,** which they had undercounted.

## 1.65.2 -- 9 October 2026

- **A copy, or only a name in common.** check's shared finding called any app file with a kit module's name a duplicate. HomerView's own paths.py and elevate.py, and a 23-line lbc.py, share 9 to 16 percent of their lines with the kit's files of the same names: different modules, not copies. A same-named file now counts as a drifted copy only when at least half of its meaningful lines are the kit's; otherwise the log names the clash, and suggests a different name, without failing. HomerView's backlog entry now lists its five real copies, in its homer package, with a plan that first brings into the kit what HomerView needs inside NVDA.

## 1.65.1 -- 9 October 2026

- **Only approved components convert.** The routing table had routes through a converting program that was never approved, and the scanned-page route drew pages with another; both are gone from the table, the engine, the test and this guide, and pages are now drawn by pypdfium2, a PyPI package. The approved components are Pandoc, NuGet and PyPI packages, and Tesseract, with Office by COM as the last resort -- and the only way, for now, for .doc, .xls and .ppt. An Excel workbook's first sheet becomes a comma-separated file read straight from its XML. testConversion now makes its samples with Pandoc and Python alone, including a PDF with a larger-type heading and a scanned page; 46 routes passed where it was written, none failed, and 21 needing Office or a sample only Office can make were reported as not tested.

## 1.65.0 -- 9 October 2026

**One way to convert a file, and two checks that keep the projects alike.**

- **The shared conversion engine.** Seven projects converted files, each its own way, and five reached for Office by COM. `exec\conversions.inix` is now the one routing table -- for each source type, the ways to each target, free engines first, Office last -- and `exec\Python\conversion.py` follows it: `convert`, `toText` and `plan`. Plain text takes the quickest route with no work on structure (a PDF's text layer in milliseconds); Markdown, HTML and Word keep headings, lists and tables; a scanned PDF falls back to Tesseract. `scripts\testConversion` proves every route on sample files made at the time -- 70 of 70 passed where it was written -- and the kit's build runs it. C#'s Conversion.cs, reading the same table, comes next, and then the apps move onto it, 2htm first. The homer-convert skill now sends any conversion to the engine.
- **The Homer tree is checked.** kind.py holds the folders a project of each kind may have, and check's layout finding fails a top-level folder outside them that the project's lists do not declare; a declared one is logged for the author to confirm. A folder had been added to a Homer project unasked.
- **One copy of every shared class is checked.** check's shared finding fails an app source that duplicates a kit module or class, unless it is the build's byte-identical copy.
- **Known debt in view, new debt refused.** `scripts\conformanceBacklog.inix` lists what the two checks found on 9 October -- duplicates in DbDo, EdSharp, FileDir and HomerView, EdSharp's Convert and Samples folders, and the kit's own PdfRead.cs, which is HomerScribe's code, not a shared class -- each with its plan. A listed item is reported on every check; anything else fails.


- **The project's own lists decide what tidy keeps.** Tidy's standing names included broad fallbacks from before every project declared its files: any .py, .cs, .inix, .js or .lua file anywhere, and any build*, get* or install* script, belonged. Once projects had RepoFiles.txt and LocalFiles.txt, those fallbacks quietly overruled them: DbDo's top folder held twelve stray scripts and settings files that no list named -- seven build_*.py, conform_samples.py, migratePrm.py and three .inix files -- and tidy reported 0 files to move into notes. A project with a RepoFiles.txt is now judged by its lists, the installer's Source lines, and the true standing names (the standard documents, version.txt, the list files, logs, tutorial fingerprints); a project without one keeps the fallback. A dry run over the kit and seven apps found nothing else affected; DbDo's twelve go to notes, and nothing is deleted.

## 1.64.7 -- 9 October 2026

- **A failed build leaves no installer.** The app templates removed the previous <App>_setup.exe, if at all, only just before compiling the installer, so a build that stopped earlier -- DbDo's, on a compile error -- left the last build's installer in place, and installing it looked like installing this build. Both templates now remove it before anything is compiled or bundled. An app's own kitNeeded must also rise whenever its code uses something new in the kit: DbDo's still said 1.55.0 when it began to call MediaPlayer.playTutorials, which needs 1.64.5, so a 1.64.4 kit failed to compile instead of being named.

## 1.64.6 -- 8 October 2026

From the logs of the books' build and KDP run of 8 October.

- **Book tasks are Homer logs.** summarizeLogs took a task name to be lowercase, so MyBooks-buildBooks and MyBooks-kdpUpdate, named in Camel Type, were skipped as not Homer logs. It now reads them: buildBooks as how many books are ready to submit, kdpUpdate as how many were submitted and which were not -- a book KDP locks for review is waiting, not failing, and "no spelling errors" is not an error.
- **A browser message once, not a thousand times.** kdpSubmit, whose browser kdpUpdate shares, logged KDP's pages' every repeated message: one 404 was 1,187 of a 13,858-line log. Each distinct error or warning is now written its first three times, then counted at 10, 100 and 1,000.

## 1.64.5 -- 8 October 2026

- **The walks play in the Homer Player.** MediaPlayer.playTutorials(owner, app name, help folder) opens an app's spoken tutorials in the Homer Player: the .mp3 files of its help\\tutorials folder, in the order of their one-digit prefix, each named as its walk is ("0 - Overview"). The player opens paused with the cursor on the first walk, so Enter plays it and Down Arrow hears the next. DbDo's Play Tutorials had handed its playlist to Windows, which opened whatever player owned .m3u files. Without mpv, the playlist still goes to Windows; with no walks installed, it returns false so the app can say where they belong.

## 1.64.4 -- 8 October 2026

From the logs of 8 October's builds and releases.

- **The template's installer compiled into a duplicate.** _APP__setup.iss defined the eight screen-reader wrappers (labelJaws, isInstallJaws and the rest, and NVDA's) that HomerComponents.iss supplies, so every new app's installer would have failed as HomerView's did: Duplicate identifier LABELJAWS. The template's copies are gone. kind.issFunctionClashes finds such a clash from the scripts themselves, honouring the #define that keeps the kit's copies out; check runs it for every app as the installer check, and the kit's build runs it on the template.
- **A walk's length predicted from what is spoken.** checkTutorial estimated from words at 186 a minute, which ran 21% short on average and up to 33% on walks of many short two-voice steps. Fitted to twenty walks the build measured: the host speaks at about 225 words a minute, the reader voice at about 575, and each step adds about 3.6 seconds. Average error 1%, worst 13%; the kit's own walk 8, outside the fit, measured 182 seconds and is predicted 188. A notice comes below 2.75 or above 5.25 predicted minutes, and says how it was reached.
- **Unfinished is not failed.** summarizeLogs reported three builds FAILED that were waiting their turn for the voices. A build with no end line is now UNFINISHED, not a failure, and shows the last line of its tutorials log -- still waiting, 27 minutes; EdSharp is speaking walk 9 of 10.

## 1.64.3 -- 8 October 2026

**A page's title said once.** Pandoc's standalone page puts the title in a header block as a top-level heading, and a Markdown file that also opens with the same # heading gave the page two: a screen reader said the title twice before anything else. Found by an audit of the AppHelpGuides and PodcastDirectories collections, where 216 and 86 pages did it.

- **homer-convert's toHomerEncoding removes the repeat.** When a page's title-block heading says exactly what its first heading says -- tags, entities, spacing and case aside -- the title block's goes, and the header with it if nothing else is in it. A title that differs is left alone. It is the one home of the rule.
- **The app-help-guide and podcast-directory skills finish every page with it.** cleanFeedback's rebuild and buildDirectory call it -- beside them in the kit, or through the HomerDev variable or C:\HomerDev for a copy kept in a collection's folder -- and fall back to the encoding alone when it cannot be found. Each skill's instructions name it, and say the collection's ReadMe keeps its CC BY-SA 4.0 license sentence.
- **Not yet for the apps.** An app's documents have a title-block heading taken from the file name (History) above a body heading that differs (extCheck History), so the rule leaves them, and every app page still has two top-level headings. Using pagetitle instead of title in the build templates' Pandoc call would make the body's heading the only one; that is a change to every app's build, and waits for the author's word.

## 1.64.2 -- 8 October 2026

- **The skills check catches a failing database.** It looked for the word "fail" in checkDb's report, which says "1 failure", so a failing database passed. It now reads the failure count. Found on DbDo, where it named two real failures -- a table with columns after marked, and a key still called prm -- both since fixed in DbDo.
- **check.py's line endings** are all CRLF again, after the edit above mixed in bare line feeds.
- **Seven kit files put into the Homer encoding**, which fixEncoding had not yet been run over: the books templates' epub.css and tocEpub.lua, the samples' two .spec files and version.py, the page skill's default layout, and the tutorial playlist. A UTF-8 mark is safe in each: Lua's loader and Jekyll both skip one.

## 1.64.1 -- 8 October 2026

- **MediaPlayer.cs reads ExifTool's two streams at once.** Its output and error streams were read one after the other, the hang the kit fixed in Media.cs in 1.62.5; found while auditing FileDir, which had the same code.
- **FileDir now compiles the kit's Media.cs and Mpv.cs.** Its own copies had drifted, lacking the 1.62.5 fix, the machine-wide mpv search and recording. MediaPlayer.cs is still compiled from FileDir's own copy, in its own namespace; moving it to the kit's is the next step for one shared Homer Player.

## 1.64.0 -- 8 October 2026

**Two principles, and the kit eats its own cooking.**

- **Convention over configuration, and don't repeat yourself.** The author made both Homer principles; Developer.md opens with them, and the homer-code skill teaches them.
- **The skills' checks run on every project.** check, which build and release run, now has a skills check: checkDocs (homer-docs) on the documents, checkDb (homer-db) on each DbDo database a project holds, and summarizeLogs (homer-build-release) on its recent runs, from the kit's own skill folders. A failing database fails it; document and log findings are recorded and named. Three of the five checking skills had never been run by any step.
- **One set of encoding rules.** fixEncoding.py and the homer-convert skill's toHomerEncoding.py had drifted: only the skill knew SKILL.md takes no byte order mark, read UTF-16 and Windows-1252, and knew .css, .csv, .js and .tsv; only fixEncoding knew .lua, .m3u and .spec. fixEncoding.py is now the rules' authoritative home with all of it, and the kit's build fails, naming the difference, if the skill's copy ever says otherwise -- tested by removing one type from the copy.

## 1.63.3 -- 8 October 2026

**push stops on a stale whitelist.** When tidy could not rewrite the whitelist
.gitignore, push warned and went on, and a stale whitelist can publish files
never meant for it. It now stops, says so, and pushes nothing. From an audit of
HomerScribe by another AI, which found its copy of push lacked the 1.62.5 fix
too; an app's copies of the kit's tools are refreshed by its build.

## 1.63.2 -- 8 October 2026

**When an update is live.** kdpUpdate knew when it submitted a book, never
when the update went live. KDP's email, "your book is now live and available",
does not settle it: it adds that a republished book's changes follow later.
The Bookshelf does: plain Live, with no update in review or publishing. Each
run now reads that at the start and records, in the book's receipt, when a
submitted update is first seen live, with the hours it took at most.
Mastery in Men's Tennis, submitted at 11:36, was live by 12:57 -- though KDP
quotes 24 to 72 hours -- so the receipts now measure it, book by book.
kdpUpdate --survey records it without changing anything on KDP.

## 1.63.1 -- 8 October 2026

**Learned from a morning of logs.** Four apps' tutorials, six apps' builds and
releases, and a kdpUpdate run over 22 books:

- **Tutorials: no sentence lost to a quote.** Windows PowerShell does not
  escape a double quote inside an argument to a program, so a line holding
  "Processing 3 of 9" reached Kokoro as several arguments, it refused, and
  the sentence was left out of the walk without a word -- twice in
  HomerScribe. Straight quotes now become curly ones before Kokoro speaks;
  a piece that makes no audio is counted and logged; a walk with one is not
  marked spoken and is spoken again next build. A walk spoken before this,
  whose text holds a straight quote, is spoken once more, so HomerScribe's
  two walks mend themselves.
- **Tutorials: who is speaking.** Four builds started within three minutes,
  and three waited up to 108 minutes hearing only "Another Homer build is
  speaking". The build speaking now writes its project and walk to a status
  file, and a waiting build says, for example, "HomerDev is speaking walk 6
  of 10, since 8:13".
- **checkTutorial: words, not steps.** DbDo's walks had 12 to 14 steps,
  passed the step rule, and ran 1:26 to 1:55. The kit's own walks are spoken
  at about 186 words a minute, so the spoken words now give the estimate,
  and a task walk clearly under three minutes, under about 465 words, gets a
  notice before any minute is spent speaking it.
- **tidy: the kit's sample programs out of an app.** DbDo's installer
  shipped 30 files of the kit's samples -- six sample programs, PyInstaller's
  build and dist folders, their logs -- left in templates\\samples by an
  earlier unarchive. None is in the kit's RepoFiles, so none was a stray by
  that test. An app's templates\\samples holding nothing but such leftovers
  is now removed whole, and logged; one holding anything else is kept, with
  the reason logged.
- **kdpUpdate: KDP's manuscript check is reported.** KDP found possible
  spelling errors in nine books (14 in one) and could not check two others,
  yet the outcome list said only "submitted". Each book's line now adds what
  KDP's check said, and its data file keeps it under [review].

## 1.63.0 -- 8 October 2026

**Book publishing tools, in the kit.** The scripts that build, audit and
publish Kindle books, proven on 22 books in the MyBooks project, now originate
in the kit, generic and free of personal data:

- **scripts:** buildBooks, kdpBooks, kdpSubmit and kdpUpdate, with their .cmd
  wrappers and testKdpUpdate.py. Each wrapper copies the kit's current book
  tools into the project's scripts folder before running, as an app's build
  copies its kit tools, and logs each copy; without the kit, the project's
  copies run as they are.
- **Templates\\books:** starting settings files -- books.inix, the catalog;
  buildBooks.inix, the build settings; Book_KDP.inix, a new book's KDP
  answers, moved here from Templates -- and the shared epub.css and
  tocEpub.lua, which a project's own templates folder may override.
- **kind:** publishesBooks tells a book publishing project by one fact,
  configs\\books.inix. It is a capability, not a kind: a page, a collection
  or a project of one book keeps its own kind and also publishes books.
- **help\\BookPattern.md** describes book publishing projects: their
  folders, settings files, tools, where the code comes from, and why personal
  data stays in the project. Its manuscript conventions are unchanged.
- **The homer-books skill** teaches an AI assistant the same.

Generalized on the way in: whose books are the project's own is the author
setting in buildBooks.inix, or a book's publicDomain key, not a name in the
code; kdpSubmit takes a book's answers file by --book and rebuilds a book
publishing project's EPUB with buildBooks; a book's newer files in another
folder are brought over by the catalog's importFrom; logs are named for the
project; no author's name, title ID or folder is in any tool. The two folders
of a book publishing project, books and results, start with letters no other
Homer folder uses.

## 1.62.5 -- 8 October 2026

**An audit by another AI.** ChatGPT audited the kit and reported 39 findings.
Checked against the code, these held and are fixed:

- **INIX keeps every value.** A value that is itself a fence mark -- one
  backtick, three double quotes, or { -- is written in quotes, in Python and
  C#, since bare it read back as the start of a fence and swallowed the rest of
  the file. A value holding both fence marks as lines of their own is refused
  with a clear message, where C# wrote it and hoped. An unterminated fence is
  still read to the end of the file but named in the diagnostics. Python's
  inix.write goes to a temporary file and replaces the original in one step.
- **Dialogs (Python lbc).** getValue reads a field's value before any selection,
  so a text field with nothing selected no longer reads empty; a handler that
  fails leaves the dialog open with a message, rather than closing as if it
  succeeded; and Control+Enter accepts through the default button's own handler.
- **Updates (Python elevate).** The setup program downloads to a .part file and
  is started only when complete; a failed download no longer starts a partial
  installer.
- **Programs (C# Media.run).** The error stream is read on its own task while
  the output stream is read, so a program that fills one cannot hang both.
- **Web (Python web).** Every relative link is made absolute, entities in links
  and their text are decoded, and Windows device names such as CON are made
  safe as file names.
- **Ollama (C#).** hasModel matches a whole model name, so qwen2.5:7b is no
  longer found inside qwen2.5vl:7b; a name with no tag means its :latest.
- **Tables of contents (kdpEpub).** The check now follows every NCX entry, the
  guide's and landmarks' places in the contents page, and requires the contents
  page to list every entry of the logical one, in order. All 22 MyBooks books
  pass; a deliberately broken copy fails on each of three faults.
- **A check observes only.** build check no longer retires walks or edits the
  environment; those repairs run in a real build.
- **checkHomerDev** looks for uiCheck in scripts, where it moved, and fails
  rather than skips when it is missing.
- **push** asks git whether anything is staged: a failed commit is a failure,
  no longer "nothing to commit", and commits already made are pushed from a
  clean tree.
- **A fresh copy of the kit works.** The release scripts and the new-repository
  templates are local-only by the author's rule; build no longer requires them,
  and newHomerApp skips the templates with a note. newHomerApp checks every
  template before writing anything, so it never leaves a half-made project.
- **Documents.** The ReadMe's retired Tools folder and single walk, and
  Developer.md's retired installTools, are replaced by what the kit does now;
  History's hand-kept contents list, stopped at 1.50.2, gives way to heading
  navigation.

Left for later, as larger changes needing Windows testing: atomic and locked
settings writes in C#, unique temporary folders and logs for simultaneous
instances, a dedicated STA thread for Pythonnet, background work for network
calls, update digests, request-and-reply for mpv, namespace-aware EPUB editing,
structured migration, and a pinned release toolchain.

## 1.62.4 -- 8 October 2026

**Apps move to the pattern of ten cleanly.** buildTutorials, which every app's
build runs, now retires an app's old two-digit walks once its one-digit walks
are in place, so an app's zip can bring its new set without its old one being
spoken beside it. DbDo, EdSharp, FileDir, HomerScribe and HomerView now
follow the pattern of ten; DbDo and HomerView have spoken tutorials for the
first time.

## 1.62.3 -- 7 October 2026

**The kit's build passes again after the pattern of ten.** Its 21:10 build
reported 26 problems and release rightly refused: the list of files the build
expects still named the 24 two-digit walks and templates the same build had
just retired, the homer-tutorial skill had been saved with a byte order mark,
and tidy.py had one line ending not CRLF. The list now names the ten walks and
ten templates of the pattern of ten, and both files are in the Homer encoding.
The tutorials themselves were already right: all ten spoken, and kept on the
next build by their fingerprints.

## 1.62.2 -- 7 October 2026

**kdpEpub may run any number of times over the same EPUB.** MyBooks runs
Blind Vibe Coding's own build, which already gives its EPUB KDP's tables of
contents through kdpEpub, and then gives the copy them again. On that second
pass the contents page already held a nested list, and kdpEpub replaced it
only up to the first closing tag, an inner one, leaving stray closing tags:
EPUBCheck called the page fatal and Ace could not read the book. kdpEpub now
finds the whole list by counting its opening and closing tags. Run four times
over the book's EPUB, the page stays the same: 33 links, well-formed, every
requirement met.

## 1.62.1 -- 7 October 2026

**The pattern of ten is always ten: exactly seven tasks.** 1.62.0 read the
task walks as one to seven; the author's intent is seven, numbered 2 to 8, so
every set is the full ten. checkTutorial now gives a notice for each missing
task number. The kit gains its seventh task, 8_Build_with_an_AI_Assistant:
the skills that teach an assistant the rules, checked by checkSkills; the
three sentences that carry the kit into a chat; the method, specify first in
accept dot inix, build small, verify without sight; and a planned misstep
check catches, fixed by a caption, not a key table. 9_Conclusion now runs in
the author's order: the conclusion and summary, then the glossary, then more
information, with the help built into every program. The overview lists all
ten; the templates gain 8_Task_Six, so a new app's set is the full ten; the
skill, Tutorials.md and HomerDev.md say seven tasks.

## 1.62.0 -- 7 October 2026

**The pattern of ten: one digit sorts every program's tutorials.** The twelve
two-digit walks give way to ten numbered 0 to 9: 0_Overview; 1_User_Interface,
which now holds what were the interface-concepts and key-patterns walks; the
task walks from 2 (usually 2_Install_and_Launch) to 8 with no gap; and
9_Conclusion, always number nine and so always last, which holds the
glossary, the reminders to carry away, the help built into every program
(F1, Shift plus F1, Alt plus F1, Control plus F1, Hotkeys, Play Tutorials)
and where to learn more.

- **The kit's own set** is nine walks, 0 to 7 and 9. Walk 1 was written new
  from walks 02 and 03, the reader speaking in 26 of its 30 steps, kept to
  five minutes; walk 9 from 09, 10 and 11, with the fifteen most useful
  glossary terms. The task walks were renumbered and their cross-references
  corrected; the overview's contents list was rewritten.
- **checkTutorial** knows the pattern of ten: walk 1 is held to show, then
  tell; walk 0 is not measured; walk 9 is exempt from the step count, since
  its glossary is many short exchanges. A set still named with two digits is
  told, as notices, what each old walk becomes, and is still spoken, so apps
  convert in their own time.
- **buildTutorials** retires, on a full run, any audio and fingerprint that
  no current walk makes, so renamed walks leave no stale files in the folder
  or the playlist. **tidy** keeps one-digit fingerprints.
- **Templates** hold the nine skeletons of the pattern, the walk 1 skeleton
  in show-then-tell form so a new app passes the check, and **newHomerApp**
  now copies them into a new app's help folder, as walk 3 says it does.
- **The kit's build** removes the old two-digit walks from help and
  Templates once the one-digit set is there, since unarchiving deletes
  nothing.
- **Tutorials.md, the homer-tutorial skill and HomerDev.md** describe the
  pattern of ten.

## 1.61.0 -- 7 October 2026

**exec\Python\kdpEpub.py: KDP's tables of contents, for every book project.**
KDP's Navigation Guidelines ask a Kindle book for a logical table of contents
(a toc nav or an NCX), an HTML table of contents page near the start that is a
separate document from the toc nav, made of nested links, and guide items
(landmarks and the package <guide>) pointing at that page. kdpEpub gives an
EPUB all of it, made from its own toc nav so the two always agree, and keeps
the toc nav out of the reading order so readers meet the contents once;
tocProblems checks every requirement in a finished EPUB. It moved here from
MyBooks' buildBooks so Blind Vibe Coding's build uses the same code: that
book's earlier EPUBs used the navigation document itself as the contents
page, which KDP does not allow.

## 1.60.3 -- 7 October 2026

**Spoken tutorials ship, made before release.** Every installer and every
repository carries the tutorial audio, made by the build before the installer
is compiled, so no user waits for it; help\Tutorials.md now says so. Both
build templates now call buildTutorials on every build that has walks (an
acceptance build excepted), leaving the decision to its fingerprints: the
Python template had looked for Tutorial_00_...mp3, a name the audio never has,
and the C# template compared dates, which a zip can shift by hours. tidy keeps
each tutorial's fingerprint (04_Open_and_Move.sha256) as a standing file, so
it is never moved to notes and the repository carries it with the audio.
Run updateAppBuilds to bring an app's build up to the template.

## 1.60.2 -- 7 October 2026

**From a day of logs across DbDo, EdSharp, FileDir, HomerDev and MyBooks.**

- **No build leftovers in an installer.** DbDo's installer took in
  templates\samples\.venv and shipped it: 4,650 of its 4,805 files, 2,290 of
  them compiled Python. tidy now adds Excludes for .venv, venv, __pycache__,
  compiled Python and .git to every Source: line of an <App>_setup.iss that
  takes in a folder with recursesubdirs, extending any Excludes already there.
  Tidy runs before release builds the installer, so the next release is clean.
- **The stray ERRORLEVEL variable is removed by the build.** A variable named
  ERRORLEVEL hides every program's exit code from %ERRORLEVEL%; nineteen kit
  wrappers read it that way, so on the author's PC every one reported 0, even
  for a failure. build.py now removes it from the user environment, telling
  Windows so new windows see the change, and reports a system-wide one, which
  needs an administrator. build.cmd reads its own exit code with "if errorlevel"
  from the highest down, since its window still has the variable.
- **Exit codes in a .cmd file: test from the highest down, in one statement.**
  A successful SET resets the error level to 0 in a .cmd file, so a ladder that
  first sets a default and then tests "if errorlevel 1" always reads 0. The
  MyBooks and Blind Vibe Coding wrappers that did this are fixed.

## 1.60.1 -- 7 October 2026

**Tutorial audio is kept by its content, not its date.** The 14:08 build
re-spoke all twelve walks although none had changed. The cause: a zip stores
each file's time without a time zone, so the kit, zipped on a computer seven
hours ahead, unzipped with every walk dated seven hours in the future, newer
than its audio. buildTutorials now writes a fingerprint beside each mp3
(<name>.sha256, the SHA-256 of the walk it was spoken from) and speaks a walk
again only when its fingerprint changes. Audio from before this rule is
trusted once and fingerprinted. Every Homer app with tutorials gains this
through the kit. Walk 07 and help\Tutorials.md now say so, which makes walk
07 the one walk spoken again on the next build.

## 1.60.0 -- 7 October 2026

**checkSkills learns the official validator.** Anthropic's skills repository
was read for the kit (help\HomerSkills.md has the lessons). checkSkills now
also allows only the six frontmatter keys the standard permits, limits a
name to 64 characters with no hyphen at either end and none doubled, and
gives notices, not problems, for a body past 5,000 words or 500 lines: run
over Anthropic's own 17 skills, it showed the word count is advice, not a
rule. The kit's 16 skills pass.

## 1.59.0 -- 7 October 2026

**Skills checked like code.** Four guides on building skills and agents were
read for the kit, and their lessons are in help\HomerSkills.md. The skill
guide's exact rules are now checked by a new scripts\checkSkills, which runs
over every skill in a project's .claude\skills and exits 1 on a problem:
kebab-case folder names, SKILL.md named exactly, frontmatter delimiters, a
name equal to the folder and free of reserved words, a description of at most
1,024 characters, no angle brackets in the frontmatter, no README inside a
skill, and a body of at most 5,000 words; with notices for a description that
does not say when to use the skill, a long body, and a missing linked file.
Its first run found four kit skills with angle brackets in their
descriptions, which can make a skill fail to upload; homer-build-release,
homer-db, homer-installer and homer-screen-reader now use the kit's own
placeholder, _APP_, or plain words.

## 1.58.0 -- 7 October 2026

**Show, then tell.** The User Interface Concepts walk ran on with the narrator
alone. Each part it named is now shown by the screen reader straight after:
the window that comes forward by its title, the control that takes focus by
its name, role, value and state, then its hint in the message voice. The
walk has 29 steps, 26 with the reader, and never two host-only steps in a
row. The Key Patterns walk shows its rules the same way, with Control plus K,
Shift plus Z, F4, Insert plus T and Alt plus K.

- checkTutorial measures it: in walks 02 and 03, a problem after two
  host-only steps in a row or when the reader speaks in fewer than half the
  steps; in walks 01 and 04 to 10, a notice after three; and a notice for any
  narrator line over sixty words. The log gives each walk's share. Walks 07,
  08 and 10 draw notices, the Conclusion most, with twelve host-only steps in
  a row.
- The homer-tutorial skill, help\Tutorials.md and the starter
  Templates\Tutorial_02_User_Interface_Concepts.inix carry the rule, so a
  walk written for any Homer app starts in two voices.
- Reader lines written from the phrasing rules rather than from a recording
  carry a Note asking for a live run to confirm them.

## 1.57.0 -- 7 October 2026

**One .inix format, read the same way in C# and Python.** A value that spans
lines is written in one of three ways: plain, with nothing after the equals
sign, for a value with no equals sign in it; between a backtick fence, for a
value with an equals sign or whenever a writer wants the reliable form; or
between triple quotes, for the rare value with a backtick. A name line is
trimmed, so spaces around the equals sign mean nothing.

- exec\Python\inix.py now reads exactly as Inix.cs does: plain values end
  at the next name or section line, by the same test; [;Name] comments out a
  section and [] makes Record1, Record2; quotes around a one-line value are
  stripped once. Its writer chooses the fence as Inix.cs does. Comments,
  blank lines and order still survive a round trip. The brace form it wrote
  before is still read, never written; readInix, writeInix and inixList now
  sit on the same reader.
- Inix.cs keeps a fenced value verbatim (it had dropped a blank last line),
  drops only the blank layout lines after a plain value, and writes a value
  containing a backtick between triple quotes, in writeValue as well as
  writeAsConfig.
- help\Inix.md describes the three forms, and BookPattern.md gives KDP's
  current definitions of AI-generated and AI-assisted with model wording for
  a book's copyright page.

## 1.56.0 -- 7 October 2026

**The newest Pandoc, not the first one on the PATH.** Every Python and cmd script
in the kit found Pandoc by taking the first copy on the PATH. On the author's
machine that was C:\bin\pandoc.exe, version 2.19.2, ahead of a current Pandoc
in Program Files, so MyBooks' book build asked winget to upgrade, winget
truthfully said the installed copy was current, and the build gave up. Media.cs
had met the same folder with mpv and already searched the official folders
before the PATH; that rule had simply never reached Python or the cmd builds.

- New exec\Python\media.py, the finding half of Media.cs in Python: findTool,
  findInstalled and the same table of official folders, plus newestInstalled,
  which runs every copy it finds and chooses the newest at or above an optional
  minimum version, as exifToolProgram does. pandocProgram and javaProgram are
  the common cases, and shadowNote says when an older copy is first on the PATH.
- New scripts\newest.ps1, with newest.cmd, the same search for cmd builds that
  do not require Python. It prints only the chosen path, for for /f, and puts
  every copy and its version in the log.
- exec\Python\inix.py gains readInix, writeInix and inixList, the reader of
  the multi-line block form that help\Inix.md documents and every KDP answers
  file uses, ported with their names from kdpSubmit.py, which Inix.md had named
  as the reference. The module's read and write are unchanged. The kit still
  holds three multi-line forms -- blocks in the documentation, braces in
  inix.read, backtick fences in Inix.cs -- and Inix.md now says so plainly.
- The kit's build.py, both app build templates and the four FruitBasket sample
  builds now use them. checkHomerDev's environment line reports the Pandoc a
  build will really use, and names any older copy ahead of it on the PATH.

## 1.55.0 -- 7 October 2026

**The tutorial pattern is a recipe.** The homer-tutorial skill now carries the
whole method for applying the twelve walks to any Homer app -- gather the
truth, choose tasks as wants, the shape of each walk, every line for the ear,
measure and adjust, and what this week's mistakes teach -- so HomerScribe,
HomerView and the rest can take the pattern without its author in the room.
The kit's own short walks, and DbDo's, EdSharp's and FileDir's, were given
their substance: twelve parts that ran under three minutes now carry worked
cases, reverse guessing exchanges, missteps and the shape of what each
program is for and is not.

## 1.54.2 -- 7 October 2026

**An acceptance build speaks nothing.** check runs an app's build as an
acceptance check with HomerAcceptance in its environment, and a build that sees
it leaves the speaking of tutorials to the ordinary build, which already did it;
DbDo's acceptance build on 7 October spoke twelve walks and ran out the
fifteen-minute clock, failing a release whose audio was complete. The build
template, DbDo's and EdSharp's builds honour the mark.

## 1.54.1 -- 6 October 2026

**An app stays an app under the kit's strays.** With the kit's Templates and
exec folders lying in C:\DbDo, kind.py called the folder the kit, and tidy's new
stray removal, which declines to tidy the kit, did nothing; DbDo built and
released around seventeen walks. An installer script or a program named for the
folder now settles the kind as an app first, and tidy runs the stray removal
regardless of kind, declining only when the folder is the kit's own.

## 1.54.0 -- 6 October 2026

**The build repairs what one-off scripts used to.** Three things delivered as
separate scripts on 5 and 6 October are now steps of every app's ordinary
build, each logged. tidy removes the kit's stray files from an app's folder -- a
file at a kit path, byte for byte the kit's, not one the app may share -- along
with the one-off scripts themselves, and the folders left empty. The build
template sets version.txt back to the app's last published tag when it holds
another series' number. The same two guards are in DbDo's and EdSharp's builds.
One set of commands, every time: unzip, build, release.

## 1.53.4 -- 6 October 2026

**buildTutorials speaks again.** In 1.53.2 the helper that writes minutes and
seconds was moved up the file and cut in half on the way: its first line went
up, its last two lines stayed behind, and everything between -- the whole
speaking loop -- became the body of a function nobody called. Every build on
1.53.2 or 1.53.3 listed its voices and then stopped at the script's last line
with nothing spoken, in DbDo and FileDir alike. The helper is whole again, the
file's braces balance, and the defensive endings of 1.53.3 stay.

## 1.53.2 -- 6 October 2026

**One build speaks at a time, and the clock is on the progress line.** Four
builds spoke their tutorials at once on 6 October and each step took twenty
seconds instead of five, which looked like a hang. buildTutorials now holds a
machine-wide mutex while it speaks -- a second build waits and says so, each
minute -- and its progress line carries elapsed time and an estimate, with one
plain note when the pace says the computer is busy.

## 1.53.1 -- 6 October 2026

**A high step count is a notice.** The tool's measurement of the audio is the
fact; a walk of many short two-voice exchanges is brisk, not long, and is no
longer refused for its count.

## 1.53.0 -- 6 October 2026

**The kit has its own twelve walks**, in the pattern it prescribes: overview,
install and launch -- the kit's build and the fruit basket --, the interface
and the key rules heard in DbDo, EdSharp and FileDir, then five tasks --
starting an app from the kit, build and check and release, the installer's
finish page, spoken tutorials, shared code and the Homer Player heard in two
programs -- then a glossary of twenty-six terms, a conclusion and more
information. Where the kit has no screen of its own, an app built on it shows
what the kit's code makes a person hear. The one earlier walk is retired, and
checkTutorial holds the kit to the pattern like any app.

## 1.52.8 -- 6 October 2026

**HomerComponents.iss supplies the screen reader wrappers** -- isInstallJaws,
isUpdateJaws, isReinstallJaws, labelJaws, and the same four for NVDA -- that an
app's [Components] lines call. An app that defines its own writes
`#define HomerReaderWrappersInApp` before the include. FileDir's installer
failed on 6 October because a kit without these had been laid over one that
had them.

## 1.52.7 -- 6 October 2026

**Three to five minutes a walk.** Parts 01 to 10 are to run between three and
five minutes -- under three is too thin, over five too long; 00 and 11 may be
short. buildTutorials names any walk under three as well as over five;
checkTutorial notices a thin walk and exempts the glossary from the step
ceiling, since its steps are two short lines. Tutorials.md and the skill have
the rule.

## 1.52.6 -- 6 October 2026

**An incomplete set is a notice, not a silence.** checkTutorial reports the
twelve-walk pattern's gaps, and a first walk without the orientation key, as
notices: the clean walks are spoken and the program releases, and every build
says what the set still lacks. A problem is something wrong inside a walk; work
not yet done is not a reason to leave a program with no audio, which is what
EdSharp and FileDir had on 6 October.

## 1.52.5 -- 6 October 2026

**buildTutorials measures, retires and re-speaks on its own.** Each walk's
length is read with ffprobe, written into Tutorials.m3u, named in the log and
summed aloud; a walk over five minutes is called out. Audio under the old names
is retired by the tool, so no app's build has to know the naming changed. And a
walk whose audio is older than the walk is spoken again -- the tool had kept any
file that existed, so a changed walk kept its old voice until the folder was
deleted by hand.

## 1.52.4 -- 5 October 2026

**The build template speaks walks by chapter name.** Its tutorial gate looks
for 04_X.mp3 beside Tutorial_04_X.inix, retires audio under the old names, and
calls the tool when a walk's audio is missing or older than the walk; the tool
speaks only those. Every app's build takes this through updateAppBuilds.

## 1.52.3 -- 5 October 2026

**Five minutes a walk, and walk 00 has a shape.** A walk is under five
minutes -- about twenty-five steps -- and checkTutorial sends back one plainly
over; twelve such walks are "about an hour". Walk 00 is prose, then the two
reader keys, then the table of contents as a clean two-voice list. Walks 02
and 03 say where help is and name the keys that explain the keys. All of it
is in Tutorials.md and in the homer-tutorial skill.

## 1.52.2 -- 5 October 2026

**Tasks are wants, and later walks lean on earlier ones**: a task walk
states a plain want first and shows the features as the way to it; each walk
assumes those before it and names rather than reteaches what they taught.
Tutorials.md has the rule.

## 1.52.1 -- 5 October 2026

**Twelve walks, with a glossary.** 09 Glossary joins the pattern, after the
tasks and before 10 Conclusion and 11 More Information, which is always last.
Tasks are 04 to 08, at least one and at most five, numbered without a gap. The
glossary is two voices -- the host says the term, the reader says the meaning
-- and so is every recap: the host says the key, the reader says the command.
Tutorials.md has the pattern and the rule for the two voices: an exchange that
teaches, never a chat.

## 1.52.0 -- 5 October 2026

**Eleven walks for every program**, by name: 00 Overview and Table of Contents,
01 Install and Launch, 02 User Interface Concepts, 03 Key Patterns, 04 to 08
five tasks, 09 Conclusion, 10 More Information. The templates carry a skeleton
of each; checkTutorial requires the fixed six by name and the five task numbers;
and the audio is named like a chapter -- 04_Open_and_Move.mp3 from
Tutorial_04_Open_and_Move.inix -- so a folder or a player shows the number and
the title. Tutorials.md has the pattern.

## 1.51.5 -- 5 October 2026

**The Homer Player records: two buttons and one key.** Record and Stop
recording are buttons beside Stop playback, each available only when it
applies, so the reader says which state you are in; Alt+Shift+R does whichever
applies from anywhere in the dialog, as Scroll Lock does for playing. Where am
I, Alt+Shift+W, says "recording for N minutes" while one runs, and closing the
player finishes a recording rather than cutting it. The buttons carry no
trigger letter: R is the Rate slider's and S is Stop playback's.

**The player records** Alt+Shift+R writes the stream as it
arrives to Music\Homer Player, named for the track and the time, and says the
file; Alt+Shift+R again stops and says how long it ran. A copy of the stream,
no re-encoding, no settings: enough to keep a programme to hear later, which
is all a player should offer. Anyone making audio to publish has a studio
program for that.

## 1.51.4 -- 5 October 2026

**buildTutorials speaks only what is missing or stale.** A walk whose audio is
newer than the walk is skipped, so adding four walks to a set of fifteen costs
four walks' speaking, not nineteen.

## 1.51.3 -- 5 October 2026

**MediaPlayer.cs stands on its own.** Two dialogs it had borrowed from
FileDir's own Lbc class -- a message box and a Save As -- are private helpers
now, so the player compiles in any app that takes it from the kit.

## 1.51.2 -- 5 October 2026

**Mpv.cs looks for mpv machine-wide only**: under Program Files, where a Homer
installer puts it, and on the PATH; never in a user's own profile.

## 1.51.1 -- 5 October 2026

**The Homer Player is a shared class.** Media.cs, Mpv.cs and MediaPlayer.cs
move into the kit from FileDir, where they were written, with three lines
changed: the namespace, the data folder, and the one voice. Any Homer app can
hand the player a queue of tracks -- `Homer.MediaPlayer.run(owner, title,
source, tracks)` -- and mpv plays them. DbDo's Play Stream is the first second
user.

## 1.51.0 -- 5 October 2026

**What the JAWS trainers do, applied to the walks.** From 98 transcripts of
Freedom Scientific training, `help\TutorialLearnings.md` records eleven habits
and their evidence. Tutorials.md now asks for five of them: Insert Tab to
verify inside a dialog (Insert T for the window), a lone letter spelled with
its alphabet word, the tutor message shown once and then off, one planned
misstep with its Escape, and a closing step naming the keys taught. The
overview template teaches the repeat key and the orientation key in its first
steps and ends with a recap; checkTutorial requires the first script to teach
both keys.

## 1.50.2 -- 2 October 2026

**Every Homer app is MIT, and the kit keeps it so.** HomerView was the one
app under the GPL, version 2, on the understanding that an NVDA add-on should
share NVDA's license. NV Access's own submission guide checks no license, the
store's form only records one, and MIT is compatible with the GPL, so
HomerView is MIT like the rest.

- **scripts\relicense** makes an app MIT throughout: License.md becomes the
  kit's MIT text (a LICENSE.md is renamed to License.md through git mv, with
  RepoFiles.txt, LocalFiles.txt and the installer script following), and the
  app's own claims to another license become "MIT License" -- a line naming
  Jamal Mazrui with a GNU license, a bare license line just after his
  copyright line, and "<App> is free software under the GNU ...". Lines about
  other people's software are left alone, as are History.md and History.htm.
  Each change is logged in logs\<App>-relicense-<stamp>.log. "relicense all"
  covers every app beside the kit.
- **tidy runs it before each push**, with --if-needed, so it does nothing and
  writes no log when an app is already MIT throughout.
- **check's "license" now also fails a remaining claim,** naming each line in
  the log: on the apps' current copies it found EdSharp's source header and
  About box (still "GNU Lesser General Public License"), the ";Modified GPL
  License" header of the homer.jss JAWS scripts in EdSharp and FileDir, and
  HomerView's installer page and license file.
- HomerDev.md's licenses section says why an app with an NVDA add-on is MIT.

## 1.50.1 -- 2 October 2026

**The skills take the settled lessons from the accessibility skills.** These
were written as 1.43.60, which never reached GitHub; they are the parts of
HomerSkills.md that agree with the HomerDev guidelines as they stand:

- homer-build-release: a fix is shown to work by the check or symptom that
  failed now passing, not by a successful build.
- homer-code: fix a fault in the shared class it comes from, not the app; a
  change to what is heard or which keys act is tried with JAWS and NVDA.
- homer-docs: link text says where it goes and reads well out of context; an
  image or diagram says what it shows. checkDocs now reports vague link text
  ("click here", "read more") and images with no text alternative.
- homer-screen-reader: declare an NVDA script with every field a person meets
  (description, gesture, category, speakOnDemand for scripts that only
  report); ui.message only for what NVDA cannot know; prove a script by
  pressing its key in the reader.
- homer-ui: the words on screen are the spoken words, for voice control as
  for screen readers; a one-key command acts only where it belongs (WCAG
  2.1.4); and a new reference, uia.md, says what each Lbc control exposes
  through UI Automation and how to look at the tree.

**summarizeLogs reports the kit's own check as what it is.** In C:\HomerDev,
check recognizes the kit and hands over to checkHomerDev, with no totals; the
summary had called that "FAILED: no totals".

## 1.50.0 -- 2 October 2026

**Stages: from a build to a release version.** HomerDev.md sets out the
sequence every Homer resource follows, since nothing built is finished for
good: a build on the builder's computer; a development release, public and
labelled as such, for the testers who asked for new work; and, from time to
time, a release version for everybody, after a higher bar -- no known serious
problem, testers' real use, a full JAWS and NVDA test pass, current documents
with the license named, an installer tried on a fresh computer, and for the
kit checkHomerDev and evalSkills. A serious problem in a release version is
fixed through a development release first. The homer-build-release skill
starts from the stages.

**homer-db says exactly how DbDo follows foreign keys.** DbDo follows fields
named <singular>_id; declared REFERENCES are shown by Table Summary and read by
checkDb, and following a differently named declared key is planned in DbDo.

## 1.49.1 -- 2 October 2026

**homer-db: two ways to relate records, both first-class.** The skill now sets
out that DbDo supports traditional foreign keys, named <singular>_id as in the
Northwind and Chinook templates and best also declared with REFERENCES, and the
maps table, which links any record to any other with a kind from lookups, in the
same database or apart. It adds two triggers per table that keep maps links
whole: when a record's prime changes its links follow it, and when it is
deleted its links go too. checkDb now reads declared foreign keys and warns
when a table in a database with maps lacks those triggers. The reference notes
two gaps in DbDo itself: links are re-pointed only when a prime definition is
rebuilt, not when a record is edited, and DbDo's own tables are recognized by
name alone.

## 1.49.0 -- 2 October 2026

**homer-db, a skill for SQLite databases the DbDo way.** It sets out the
conventions DbDo's generator and its Trail templates follow: plural lower-case
tables with a singular id, the standard fields added, edited, url, notes, tags,
look, prime and marked in their order, DbDo's field types, the edited trigger
and unique prime index, the lookups, maps and views tables, pick lists in
alphabetical order, rows short enough to be heard, a first letter for each
table, and a database's own folder with its .inix settings, reports and
scripts. Its checkDb script reads a .db file, or every .db under a folder, and
reports each departure as a failure or a warning, with a log beside the
database. Run over DbDo's templates, it found most tables without the edited
trigger, lookups and maps without a unique prime index, and DbDo's generator
deriving an id by dropping a trailing s (storie_id), all recorded in the
skill's reference.

**Homer creates .inix, never .ini.** HomerDev.md and the homer-code skill now
say so: .ini is deprecated in Homer and used only where another program requires
it, such as an NVDA add-on's manifest.ini, or to read an old Homer .ini once.

## 1.48.0 -- 2 October 2026

**Every resource names its license, briefly, with a link.** An app and the kit
are MIT, in License.md; a page is Creative Commons Attribution-ShareAlike 4.0,
the license Wikipedia's text uses; a collection is CC BY-SA 4.0 for its own
selection, arrangement and wording, while what it gathers from others keeps
its owners' terms and the document says so in one sentence. kind.py holds the
table (licenseFor). check gains a license finding for every kind. post adds the
kind's license to a page's front matter when the source lacks it and logs a
reminder; the kit's page layout shows the license in its footer. newHomerApp's
ReadMe names the MIT License. The podcast-directory, app-help-guide and
blind-creators builders write the license lines and the one-sentence notice
themselves. HomerDev.md has a new section, "Licenses for each kind".

## 1.47.0 -- 2 October 2026

**evalSkills: measuring whether the skills help.** scripts\evalSkills.cmd and
evalSkills.py ask Claude Code, headless, for the same small program several
times without the Homer skills and several times with them and the three
sentences, build each with the kit's sample build script, and score them with
check and uiCheck. The runs happen in a fresh folder outside the kit, so the
plain runs cannot see the kit by accident; uiCheck tests only what the task
asked for, and check's findings that partly measure Homer conventions are
reported apart. The report and log go to the kit's logs folder. --dry-run
prepares everything without asking the AI. HomerDev.md explains it under
"Measuring the difference the skills make".

**The gathered accessibility skills are linked, not copied.** help\A11ySkills.md
and its .htm leave the kit; the kit's build removes them when it finds them.
They live in their own repository, which states each skill's license: 142 are
MIT and 33 are under the GNU Affero General Public License, whose full texts
inside an MIT-licensed kit could be mistaken for MIT. HomerSkills.md,
HomerDev.md and the skills index link to that repository.

**Fewer proposed skills, measurement first.** HomerSkills.md now folds the
proposed homer-ui-check into an extension of uiCheck, which already reads the
UI Automation tree; joins homer-test-pass to homer-audit as its last step;
requires homer-listen to label every report as a prediction and name what
still needs a real screen reader; and puts evalSkills first in the suggested
order, rerun after every change.

**Comments match 1.46.0.** The build templates' and sample builds' opening
notes no longer say the kit is looked for in C:\HomerDev.

## 1.46.0 -- 2 October 2026

**Any drive, any depth.** Only Windows and folder names are now assumed: the
kit is a folder named HomerDev, a project is a folder named for itself, and
either may be on any drive and at any level -- C:\HomerDev beside C:\EdSharp
and D:\Work\HomerDev beside D:\Work\EdSharp work alike. Nothing in a script
names drive C any more.

Every script and build finds the kit the same way: the HomerDev environment
variable; then the current folder and every folder above it, and the script's
own folder and every folder above it, each either the kit or holding a
HomerDev folder; then a HomerDev folder at the top of any fixed drive. This
replaces "C:\HomerDev" in the app build templates, the four sample builds,
push, post, buildTutorials, tidy and the kind loader in every Python script.
kind.py gains findKit, and "kind --kit" prints the kit it finds.

newHomerApp puts a new app beside the kit rather than at the top of drive C.
The installer template, compiled by hand, takes the HomerDev folder beside the
app instead of C:\HomerDev. The sample builds find the compiler under
%ProgramFiles% and %ProgramFiles(x86)%, wherever Windows put them.
HomerDev.md has a new section, "Where the kit and your projects live", and the
ReadMe and Developer.md say the same.

## 1.45.0 -- 2 October 2026

**Four kinds of Homer resource, and every script knows which it is in.** The
kit now serves apps, collections, the kit itself and pages, and they need
different things: a page has no build, a collection has no installer, the kit
checks itself. scripts\kind.py decides which a folder holds from one fact
each, checked in order -- the kit's own files, then an installer script or a
program source named for the folder (an app), then a document named for the
folder (a page), then many documents at the top (a collection) -- and kind.cmd
says it aloud with the reason.

Every kit script now asks first and acts accordingly. check runs every check
on an app, only the document checks on a page or a collection (with a new
check that a page has its title and .htm, and a collection its ReadMe and an
.htm for every .md), and sends the kit to checkHomerDev. post publishes an
app's, the kit's or a collection's page to gh-pages and a page to main.
push, tidy and unpushed tell a page that is not a repository that post
publishes it. uiCheck and the three tutorial scripts leave a page or a
collection alone. fixEncoding covers a page's documents, scripts and site files
without a RepoFiles.txt. renameBuild leaves a page or collection alone.
newHomerApp will not start an app on top of another kind. updateAppBuilds
touches apps only, finds the build under its current name, build.cmd, and adds
kind.cmd and kind.py to each app's kitTools, as the build templates now do.

A script declines only on positive evidence. Where kind.py is missing or
cannot place a folder, a script does what it did before, so nothing that
worked stops working. HomerDev.md has a new chapter, "Four kinds of Homer
resource", listing what each script does for each kind; homer-build-release
and homer-page start from it.

**Not yet changed: release.** scripts\release.cmd and release.ps1 are kept on
this disk only, so they were not part of this update. They should release an
app and the kit, and decline a page (post releases it) and a collection.

## 1.44.0 -- 2 October 2026

**Publish a page with post, and a skill to go with it.** scripts\post.cmd and
post.ps1 publish a project's document as a GitHub Page that meets WCAG 2.2 AA
and the Homer conventions. An app (a folder that is a git repository) has its
guide, help\<App>.md, published to a gh-pages branch, so push and release keep
main and the tags to themselves, and no release is made. A page project (a
folder that is not a repository) is the repository: post creates it, publishes
to main, keeps its description equal to the title and subtitle, and releases
the document's version. -DryRun stages everything and stops. The log is
logs\<App>-post-yyyyMMdd-HHmmss.log. An app opts in by naming post.cmd and
post.ps1 in kitTools.

post prepares the page the way the first ones taught: the byte order mark is
removed from everything Jekyll reads, every heading gets Pandoc's id so one
contents list works in the .htm and on the web, a body h1 that repeats the
title is dropped so the page has one h1, Liquid-looking text is wrapped in raw,
kramdown's hard wraps are turned off, the .htm files beside the document go up
with it, self.md never does, and staged text is CRLF under "* -text" with
images marked binary.

The new homer-page skill gives the steps, the front matter fields (title,
subtitle, description, version, lang, and logo, image and image_alt for
pictures), and two references: what makes a page meet WCAG and the Homer rules,
and what Jekyll and git need. Its templates folder holds the kit's page layout
and stylesheet, which post uses when a project has none: one h1, a skip link,
landmarks, underlined links, colors measured against WCAG with each ratio
noted, a visible focus outline, Atkinson Hyperlegible, and support for reduced
motion and Windows high contrast. GitHub's Cayman theme alone fails several of
these.

**Where to read more.** HomerDev.md and the ReadMe now point to Blind Vibe
Coding, a directory of resources on building apps nonvisually with AI, which
lists HomerDev and was itself published with post.

## 1.43.59 -- 1 October 2026

**Two documents about skills, in help.** A11ySkills.md gathers 175 published
accessibility skills from eight collections, each with its facts, license and
full text, as a reference for anyone writing a Homer skill. HomerSkills.md
reads them for what they teach the kit: learnings that fit the HomerDev
guidelines, questions that need a decision before any guideline changes, and
proposed new skills (homer-listen, homer-ui-check, homer-audit,
homer-bug-report, homer-test-pass) and improvements to existing ones.
HomerDev.md's chapter on Claude skills and the skills index point to both.

**Dollar signs stay text in every document.** The kit's build converts
Markdown with Pandoc's dollar-sign mathematics turned off, so a workflow's
${{ secrets }} or a price in a document is shown as written.

## 1.43.58 -- 1 October 2026

**The kit's build command is "build" too.** In C:\HomerDev, as in every app
folder, the command is now `build`: buildHomerDev.cmd and buildHomerDev.py
are build.cmd and build.py, and the documents, skills, templates and scripts
say "build". The kit's own build removes the old pair when it finds them
beside the new one, so unzipping the kit over an older copy leaves nothing
behind, and the push records it. check's "buildname" now holds the kit to
the same rule as the apps; tidy and renameBuild still leave the kit to its
own build. renameBuild, when it renames an app, also changes the app's
messages that said "run buildHomerDev" to "run build".

## 1.43.57 -- 1 October 2026

**The kit keeps buildHomerDev, and its own release goes through.** 1.43.55
said the kit's build script keeps its name, but check's new "buildname" did
not know the kit from an app, and failed the kit's own release; 1.43.56's
tidy would even have renamed it. check, tidy and renameBuild now recognize
the kit by its buildHomerDev.py and leave it alone.

## 1.43.56 -- 1 October 2026

**tidy gives the build script its short name by itself.** After 1.43.55,
every app's release stopped at check's "buildname", because no app had been
renamed yet. Tidy runs before every push and is refreshed from the kit at
every build, so it now runs the kit's renameBuild whenever build<App>.cmd or
build<App>.ps1 is still there -- git mv, every reference updated, its own
log -- and the push that follows records it. The usual build, tidy, push,
release sequence needs no extra step.

## 1.43.55 -- 1 October 2026

**An app's build script is build.cmd.** The folder already names the app, so
build<App>.cmd said it twice. newHomerApp now writes build.cmd (and build.ps1
where a build has a PowerShell half); the templates, release's messages, push,
the documents and the skills say "build". check gains "buildname", which fails
an app whose script still has the old name, and names the fix: the new
scripts\renameBuild, which renames build<App>.cmd and .ps1 through git mv,
changes every reference in the app's own files -- .htm pages and .gitignore
included -- except History.md and History.htm, and logs
each change to logs\<App>-renameBuild-<time>.log. renameBuild all does every
app beside the kit. check's build step and the kit's scan for stale app
builds accept either name. The kit's own buildHomerDev, and the samples, which
share one folder, keep their names.

## 1.43.54 -- 1 October 2026

**A build steps over every released number, as it always meant to.** Each
build takes the next version and skips any number already tagged on GitHub,
by searching git's list of tags with findstr /e. git writes that list with LF
line ends, and findstr /e matches only before CR LF, so nothing ever matched.
For most apps it did not matter; EdSharp has releases from long ago above its
current number, so its builds chose v5.0.32, then 33, 34, 35 and 36, each
already on GitHub, and each release rightly refused. The tag list is now
rewritten with CR LF before the search, and the build log says how many tags
it read. The build templates and the four samples carry the fix; release 1.43.53's
evidence lines showed it ("GitHub has a published release tagged v5.0.36",
among 43). homer-build-release's failures reference gains the case.

## 1.43.53 -- 1 October 2026

**release shows GitHub's answer when it decides a version is already out.**
EdSharp's releases said "already on GitHub" for 5.0.32 through 5.0.35, each
straight after a build that had chosen a new number, and the log showed
nothing of what GitHub had said. Now release prints how many releases GitHub
lists, the newest tags, and whether the one asked for is among them. The list
is read as one block of text, however gh splits its output into lines. When
the list cannot be read, GitHub's own record of that tag is fetched and read
-- a published release names the tag and is not a draft -- instead of trusting
the exit code of gh release view, which through gh.cmd has said "found" for
releases that did not exist.

## 1.43.52 -- 1 October 2026

**No Ollama window left open after an install.** Ollama's own installer
starts its desktop app when it finishes, and the app opens a chat window,
which confuses someone who never asked for it: Homer apps call Ollama behind
the scenes and never use its window. installOllama now closes that window
after installing, updating or reinstalling -- politely, as Alt+F4 would, so
the app and the Ollama service keep running -- waiting up to 20 seconds for it
to appear, and logs whether it closed one. Apps whose builds copy the kit's
installOllama (DbDo, FileDir, HomerScribe) take it at their next build.

## 1.43.51 -- 30 September 2026

**check enforces the finish page.** EdSharp's installer, called migrated, still
left its Git, Node.js, Ollama and model boxes unticked, Install and Update
alike, and DbDo's left Ollama unticked, offered its model with no verb, and
opened its NVDA add-on, which starts NVDA. The new "finish" check reads the
installer the build compiles and fails: an Install or Update box not ticked, a
Reinstall box ticked, an unticked Launch box, a component box without Install,
Update or Reinstall, a box that starts NVDA, and a label saying NVDA must be
running. Run on the apps, it finds those two and passes the rest.

**The box decides, the script does.** installOllama announced "Checking for a
newer version" when the finish page had already compared versions and said
Update or Reinstall. It now takes `update` or `reinstall` from its box, says
"Updating Ollama to the newest version" or "Reinstalling Ollama", reinstalls
with winget install --force when asked, and reports what happened. The
template's Update and Reinstall boxes pass the word; FinishPage.md says so.

**check's "local" exemptions.** A JAWS settings path split over two lines,
and the one-time code that moves an earlier version's files out of Roaming,
no longer count as using the Roaming tree.

## 1.43.50 -- 30 September 2026

**Nothing of Homer's own in Roaming, JAWS's folders included.** The fingerprint
that tells Install, Update and Reinstall apart for the JAWS scripts was a file
written into each JAWS version's settings folder, under %APPDATA%. It is now a
line per JAWS version in %LOCALAPPDATA%\\<App>\\jawsScripts.inix, and an old
marker file is removed from the JAWS folder at the next install. The only files
a Homer installer puts under Roaming are the JAWS scripts and the NVDA add-on
themselves, where those readers read them. The same change is made in EdSharp's
and HomerView's own JAWS installers. HomerDev.md, homer-code and
homer-screen-reader say so.

## 1.43.49 -- 30 September 2026

**Only the local tree, never Roaming.** Every Homer app keeps everything of its
own under %LOCALAPPDATA%\\<App> and nothing under %APPDATA%\\<App>.

- Paths.moveFromRoaming (Python: paths.moveFromRoaming) moves what an earlier
  version left under the Roaming tree to the same place under the local one,
  keeps a Roaming file where a local one of that name already exists, removes
  the Roaming folder once it is empty, and returns a line per action for the
  log. An app calls it once, after the log starts.
- The JAWS settings record, jawsSettings.log, which Say's installer kept under
  %APPDATA%\\<App>, is now under %LOCALAPPDATA%\\<App>; an older record is moved
  there the first time it is looked for, so an uninstall still finds it.
- check gains "local": any use of the Roaming tree in a project's code,
  installer or scripts fails, except where it names JAWS's or NVDA's own
  folders, which live there. Run on the apps, it finds DbDo (now fixed),
  EdSharp, FileDir and HomerView.
- HomerDev.md, homer-code and homer-migrate say so.

## 1.43.48 -- 30 September 2026

**A running program's log cannot be deleted again.** 1.43.40 opened each
session log with delete sharing as well as read-write sharing, so that zipping
a logs folder would not stop on the log of a program still running. It also
let "Zip then delete" or the recycle bin remove that log while the program
went on writing to it -- into a file no one could see -- so a whole session's
record could vanish, as FileDir's did on 30 September. Read-write sharing
stays, so the live log can still be copied or zipped; deleting it is refused,
as it was before.

**Nowhere to write is not a reason to write nothing.** If a program's logs
folder cannot be made, its session is logged in the temporary folder, and the
log's first line says why.

## 1.43.47 -- 30 September 2026

**The skills learn from EdSharp's and HomerView's installers.** FinishPage.md
(which homer-installer carries) now says what the Results box holds -- the
install location first, the logs folder last, one line per ticked box, an
Update that says whether it happened, one blank line at most -- and how Launch
works: ticked, a marker, the app started as the person once the box is closed.
homer-installer's components reference gains "Failures that looked like
success": the winget update limited to machine scope that never updated, the
support folder that only grew until stale scripts reached every JAWS
settings folder, the check that passed on an old installer in exec, and NVDA
started over JAWS. homer-migrate's checklist gains the screen reader,
Results-box and cleared-folder items; homer-build-release's failures, the
release run twice.

## 1.43.46 -- 29 September 2026

**NVDA add-ons are installed without starting NVDA.** Starting nvda.exe
--install-add-on brought a second screen reader up talking over JAWS, and for
EdSharp on 29 September stopped on an invalid command line parameter with
nothing installed -- NVDA's own log recorded no add-on activity at all.
installScreenReaderSupport now does what NVDA's installAddonBundle does, to
the end NVDA's next start would reach: the add-on is unpacked, any installed
copy moved aside to <name>.delete (a suffix NVDA skips) and the new one moved
into %APPDATA%\\nvda\\addons\\<name>, with the old one put back if the move
fails. NVDA loads it at its next start. The log names the add-on, its version
and NVDA-version range, whether NVDA was running, every step, and an
installTasks.py whose install step this way does not run. homer-screen-
reader's notes say how.

## 1.43.45 -- 29 September 2026

**The screen reader state check shows its evidence.** For NVDA,
installScreenReaderSupport's state mode now logs the add-on's name, the
shipped version and the installed one (or "none"), and the lines about
add-ons from NVDA's own logs -- %TEMP%\\nvda.log and nvda-old.log for an
installed NVDA, read with sharing because NVDA holds them open -- so one setup
log shows what the installer offered and what NVDA did with the add-on.
homer-screen-reader's reference gains the rules learned with EdSharp: the
add-on carries the app's version, nvda.exe is started through the shell
(CreateProcess refuses it with code 740), an accepted add-on waits as
<name>.pendingInstall, and where NVDA keeps its log.

## 1.43.44 -- 29 September 2026

**An NVDA add-on waiting for NVDA's restart counts as installed.** NVDA keeps
an add-on it has just accepted as <name>.pendingInstall until it restarts, so
an install right after accepting it would still have offered "Install NVDA
add-on". The state check reads the pending copy's manifest too.

## 1.43.43 -- 29 September 2026

**The JAWS scripts and the NVDA add-on are components like any other.** Their
boxes say Install, Update or Reinstall by what is on the computer, ticked for
Install and Update and unticked for Reinstall, and they are no longer placed
first: each group -- Install, Update, Reinstall -- is in alphabetical order by
component name, ignoring case, with Launch and the user guide still last.

- installScreenReaderSupport gains a state mode, "state jaws <file>" and
  "state nvda <file>", which answers none, install, update or reinstall. For
  JAWS it compares a fingerprint of the script sources in <App>_JAWS.zip --
  their names and contents, since the zip's own bytes change with every build
  -- with the one it now writes into each JAWS version's settings folder when
  the scripts compile there (and removes with them on failure). A JAWS version
  installed since, or scripts from before fingerprints, read as Update. For
  NVDA it compares the add-on's manifest version with the installed one's.
- HomerComponents gains homerReaderState, homerReaderIs and homerReaderLabel,
  which ask once per reader, log the answer, and word the box.
- The template's finish page is rebuilt in the new order; FinishPage.md and
  homer-installer's components reference say how.

## 1.43.42 -- 29 September 2026

**The program the finish page launches runs as the person.** The template's
startIfAsked started it with Exec through cmd, which still runs it with the
installer's elevated rights; it now uses ExecAsOriginalUser, so the program
runs as it will every other time. Each app's installer gets the change when
it is next migrated; homer-migrate's checklist gains the item, with EdSharp's
case: its Launch box was unticked, so pressing Enter on its finish page
installed EdSharp and never opened it.

## 1.43.41 -- 29 September 2026

**A compiled script can still reach an installer through a wildcard.** FileDir
5.0.122's JAWS zip carried sources only, but its installer's `scripts\jaws\*`
line still packed filedir.jsb and homer.jsb. The failures reference gains the
case: add Excludes: "*.jsb", and have the build delete any .jsb left in
scripts\jaws.

## 1.43.40 -- 29 September 2026

**A program's live log can be read, copied or deleted while it is written.**
Log.cs opened the session log with a plain StreamWriter, which lets another
program read it only if that program does not also ask to write, and never
delete it. On 29 September FileDir's Zip then delete, run on its own logs
folder, met "File In Use" on the log of the FileDir that was running. The log
is now opened with read, write and delete sharing, so a zipper, an editor or
the recycle bin can work with it; the running program keeps writing.

## 1.43.39 -- 29 September 2026

**JAWS scripts are compiled on the user's machine or not installed at all.**
No compiled .jsb is shipped any more: one built by another JAWS version may
not suit the user's.

- The kit's installScreenReaderSupport, for each JAWS version, unpacks the
  sources, compiles each with that version's own scompile.exe, and checks for
  the .jsb. If a version has no compiler, or any source fails, every file the
  run put in that settings folder is removed and any file it replaced is put
  back; the compiler's words go to the setup log. It reports each version, and
  NVDA, in <App>_screenReaders.txt beside the setup log.
- HomerComponents gains homerScreenReaderOutcome, which the Results box reads
  for those lines -- "JAWS 2026 scripts: installed and compiled", or "NOT
  installed -- they did not compile (FileDir.jss); nothing was left behind" --
  and clears the file when Finish is pressed. The template's Results box and
  FileDir's call it.
- HomerView's installer no longer ships a prebuilt HomerView.jsb or falls back
  to one; when any version does not compile, its own removal takes out
  everything the run placed, and its Results box says the scripts are not
  installed and why. EdSharp's does the same, and treats a missing compiler as
  a failure rather than leaving uncompiled scripts. Both installers exclude
  any .jsb from what they carry.

**Every kit document has one H1, its title, and a contents list.** HomerDev.md,
History.md, Developer.md, HomerDev_update.md, License.md and Hotkeys.md used H1
for their chapters, versions or parts; each chapter is now an H2 and every
heading below it one level down, with a linked contents list after the title.
ReadMe.md gains a contents list and Announce.md's first section its proper
level. A heading in HomerDev.md that followed a list with no blank line was
not a heading at all to Pandoc; every heading now has a blank line before it.
homer-ui's reference is taken from HomerDev.md's H2 chapters accordingly.
The kit's documents check reports 0 findings.

## 1.43.38 -- 29 September 2026

**Compiled JAWS scripts are never shipped or pushed.** A .jsb runs on the JAWS
version that built it and on later ones, so one built on the developer's
machine may not suit the user's. The installer compiles each .jss with every
installed version's own scompile.exe (1.43.37); now nothing else supplies a
.jsb. tidy's never-pushed list gains *.jsb, and FileDir's build, which packed
filedir.jsb and homer.jsb into FileDir_JAWS.zip, packs the sources only.

**homer-screen-reader carries the publishers' own guides.** Freedom
Scientific's JAWS scripting documentation and NV Access's and the add-on
team's NVDA guides, as gathered on 30 and 31 August, go into the skill's
references, to be searched for a function or API rather than read whole. What
they taught is in jaws-and-nvda.md: how JAWS resolves a call and what
"unknown function call" means, scripts against functions, overriding with
Default:: and why a user default.jss must Use default.jsb, AutoStartEvent and
AutoFinishEvent, the standard includes, scompile, the byte order mark as
JAWS's sign of UTF-8, JAWS 2026's new syntax that older versions cannot
compile; and for NVDA, which script wins a key (a global plugin over every app
module), never blocking NVDA, relative imports against sys.path, ui.message,
and testing.

## 1.43.37 -- 29 September 2026

**A skill for screen reader scripting: homer-screen-reader.** When a script is
needed at all (most speech goes through Say from the app), the rules on both
readers -- one set of commands, measured for parity; the keys of homer-ui;
keys scoped to their program, never default.jkm or MyExtensions; speech -- and
where JAWS scripts and NVDA add-ons live, ship and install. Its reference,
jaws-and-nvda.md, holds what HomerView's and EdSharp's scripts taught: which
files JAWS loads, layering over the factory scripts, key-map sections,
compiling for each JAWS version and why the compilers disagree, an add-on's
structure and gestures, carrying the kit's modules inside an add-on, and how
to diagnose a script that does not load or answers "Unknown script call". It
carries the JAWS script style guide from help.

**installScreenReaderSupport compiles the JAWS scripts it unpacks.** It
unpacked <App>_JAWS.zip into each JAWS version's settings folder and stopped
there, so a .jss shipped without its .jsb was never run. Each .jss in the zip
is now compiled in place by that version's own scompile.exe, as EdSharp's and
HomerView's installers do, with each exit code in the setup log.

## 1.43.36 -- 28 September 2026

From the builds and releases of 28 September at 21:40, when nine apps were
built on the kit's new layout and eight released:

- **HomerView's installer could not find the kit.** Its build took the kit's
  folder to be two levels above a C# source, true until the sources moved into
  exec\\CSharp; it told Inno Setup the kit was C:\\HomerDev\\exec, and the
  include of HomerComponents.iss failed. It now climbs to the nearest folder
  holding Templates\\HomerComponents.iss. The release that followed stopped, as
  it should, on the failed build. The failures reference gains the case.
- **HomerView's build log is in the Homer line format**, as EdSharp's became in
  1.43.22.
- **summarizeLogs reads more version lines**: "Version: 1.0.261 -> 1.0.262"
  and EdSharp's "Version: 5.0.18 (from version.txt ...)".

## 1.43.35 -- 28 September 2026

**homer-new-app asks first whether it should be a program at all.** When the
need is keeping and reporting on records, a DbDo database is usually the better
answer, and JobTrail -- JobTrail.db with its .inix, reports and scripts under
DbDo's templates -- is the example the skill now describes, with DbDo's other
Trails. Taken from DbDo as it is on GitHub, 28 September.

**Only a project under git counts as an app.** The kit build's stale-script
warning named C:\\Jobrise, and it was then treated as an app. There is no such
app: Jobrise was a name considered and rejected for what became JobTrail, a
DbDo database rather than a program, and the folder is left from that. The
warning, and updateAppBuilds when no app is named, now pass over a folder with
no .git: the kit's build notes it as a possible leftover, and updateAppBuilds
changes it only when it is named.

## 1.43.34 -- 28 September 2026

**summarizeLogs shows a build's warnings.** The kit's build of 21:26 succeeded
and warned that Jobrise's build script still looks for the kit's old layout,
but the summary said only "result=succeeded". A build's WARN lines now follow
its result, even when it succeeded.

## 1.43.33 -- 28 September 2026

From the logs of 28 September at 21:03, when the kit's new warning named nine
apps and every app build but urlCheck's stopped with "no kit found":

- **updateAppBuilds, a kit tool that brings app build scripts to the kit's
  layout.** Run from C:\\HomerDev, it finds each app beside the kit whose build
  script still names the old CSharp or homer paths and changes only those:
  \\CSharp\\ to \\exec\\CSharp\\, homer\\log.py to exec\\Python\\log.py, PyInstaller's
  --paths to exec\\Python and its hidden imports to plain names, and in a Python
  app's own source "from homer import" to "import". Each changed file is copied
  first into the app's notes folder. It serves an app with no current zip --
  Jobrise, which the warning named -- and anyone who would rather not unzip
  ten.
- **The warning finds HomerView too.** It looked for CSharp\\Lbc.cs, and
  HomerView's build asks for CSharp\\Inix.cs; any kit path not under exec now
  counts. Its message names updateAppBuilds.
- **A leading level word is the level.** "WARN: ..." was written as
  "WARN  WARN: ..."; the word now sets the level and is not repeated.

## 1.43.32 -- 28 September 2026

**The last planned skill: homer-migrate.** Bringing an existing app onto the
kit, or auditing one that has drifted: read the current files before changing
anything, work through a checklist by area -- the build script's kit contract,
layout, lists, installer, checks, version, Elevate, documents and logging --
each item with what it looked like when it was wrong in the migrations of 25
to 28 September, then deliver only the files that change and prove the result
through a build, a check and a confirmed release.

**buildHomerDev names apps whose build script is stale.** On 28 September
urlFido's build stopped twice with "no kit found": its build script was still
the copy that looked for the kit's old layout, since its newest urlFido.zip
had not been unzipped. The kit's build now looks at each app folder beside
it and warns, by name, of any build script that still names the old CSharp or
homer paths.

## 1.43.31 -- 28 September 2026

**A skill for starting an app: homer-new-app.** Choosing the shape (a single
tool, a multiple-document app, an NVDA add-on) and the language, the fruit
basket to start from, newHomerApp, the starters to fill in -- source,
installer, build settings, acceptance checks, lists and documents -- and the
first build, repository and release, with a checklist.

**newHomerApp brought up to the kit.** Writing the skill showed it was behind:

- On a kit cloned from GitHub it stopped at once with "Template missing:
  self.md" -- git never carries a file named self.md -- and after that it
  would have wanted installOllama.cmd, installScreenReaderSupport.cmd and
  finish.cmd from Templates, where they no longer are. It no longer copies
  them: the first build puts the kit's scripts in scripts, where the Homer
  layout keeps them.
- It now writes RepoFiles.txt, LocalFiles.txt, .gitattributes, ReadMe.md,
  License.md (the MIT license) and starters in help for the guide, Announce,
  Developer and History, with the notebook self.md written from its own text.
- Its log goes to the kit's logs folder as
  HomerDev-newHomerApp-<stamp>.log, not beside the script.

**The template's acceptance checks run exec\\<App>.exe.** They ran a bare
<App>.exe, which is not found from the project folder, where the program
is built into exec.

**The kit check no longer asks for Templates\\self.md**, which git never
carries, so a fresh clone of the kit checks clean.

## 1.43.30 -- 28 September 2026

From the kit build of 28 September at 20:17:

- **buildHomerDev no longer rewrites old names inside a skill.** Its rename
  pass, which turns checkHomerApp into check and gitPush into push across the
  kit, rewrote homer-build-release's failures.md, whose point was to list the
  old names an old build script calls. It now passes over .claude.
- **No .htm beside a skill's files.** The document conversion made an .htm
  for every SKILL.md and reference -- 30 of them -- which then sat in git and
  in every packed skill. It now converts only the skills index,
  .claude\\skills\\ReadMe.md; the build deletes the ones earlier builds wrote,
  and the packer leaves any .htm out.
- **One line per command in the scripts' logs.** "RUN: ..." and then
  "EXIT: 0" on a separate line become `run start cmd="..."` and
  `run exit=0 ms=304 cmd="..."`, so a single line says what ran, how it ended
  and how long it took; a command that cannot start is an ERROR line naming
  both. In check, tidy, unpushed and buildHomerDev.

## 1.43.29 -- 28 September 2026

From the logs of 28 September, when HomerScribe's and urlFido's builds failed
and urlFido was released anyway:

- **release stops after a failed build.** urlFido's build stopped at once --
  its build script was still the copy that looked for the kit's old layout --
  and the release that followed republished the day-before installer as if new,
  since version.txt still matched it. release now reads the newest build log
  and goes on only when it says the build succeeded; -Force overrides.
- **release could not tell a published version from a new one** in Windows
  PowerShell 5.1, whose ConvertFrom-Json writes a JSON array as a single
  object: the check asked -not of the whole array, which is false, so every
  tag read as unreleased. The list is now assigned and then enumerated.
- **A failed build takes no number.** The templates' builds step version.txt
  when they begin; now, when one fails, the number goes back. HomerScribe's
  failed build had left 1.0.260 in version.txt beside a 1.0.259 installer, and
  its release refused. All eight app build scripts made from the templates
  carry the same, and require this kit.
- **HomerScribe's build ends its log on every failure.** Its "kit not found"
  and "kit too old" paths left with exit /b and wrote no build end line; they
  go through :failed. And its yt-dlp update ran twice; it runs once.
- **homer-build-release's failures reference** gains all four.

## 1.43.28 -- 28 September 2026

**A skill for documents: homer-docs.** The document set every app ships and
what each holds (document-set.md), the ninth-grade reading level, saying the
word a key comes from, key names, counts, lists rather than tables, verified
links with readable text, page breaks, the heading structure of a guide, and
how a History entry is written. Its script, checkDocs, reports documents
missing from the set, a .md without its .htm or with an older one, a document
without exactly one H1, a skipped heading level, bare URLs, a long document
with no contents list, and each document's reading grade, flagging one a user
reads that is above grade 9.

Run on the kit itself, it found two bare URLs, now links, in Announce.md and
Tutorials.md. It also finds that the kit's longest documents -- HomerDev.md,
History.md, Developer.md and the migration briefing -- use H1 for their
chapters and have no contents list, which the Homer heading rule asks of a
guide.

## 1.43.27 -- 28 September 2026

**A skill for the interface: homer-ui.** Lbc dialogs and their focus order,
labels and accessible names, access and trigger letters, flat menus, hotkeys
and their exceptions, the Alt+Control rule, the selection and navigation keys,
the function-key families, the grave accent, key names, the command table,
speech, and the three shapes of app -- the rules a screen reader user relies
on, in one place.

**A skill can carry chapters of a kit document.** homer-ui's reference,
ui-guide.md, is made at each build from four chapters of HomerDev.md -- Lbc,
keys and key names, direct speech, and the three kinds of app -- with a
contents list, so the skill never holds a second copy that drifts.

**HomerDev.md: two sections back where they belong.** "Claude skills" and
"Finish page wording" had been added inside the chapter on keys; the first is
now a chapter of its own, and the second sits with the installer's log.

## 1.43.26 -- 28 September 2026

**A skill for converting files: homer-convert.** It picks the tool by what is
converted: Pandoc for a Homer document's Markdown to .htm, with a title, a
contents list for a long document, and the pagebreak filter; 2htm for Word,
Excel, PowerPoint, PDF, CSV, JSON, HTML, Markdown and text to accessible .htm
or .txt, with its options; inixVert for tables among .inix, .csv, .tsv,
Markdown and .xlsx; and Pandoc for the rest. Its reference, conversions.md,
lists the 120 format pairs in EdSharp's Import and Export tables with the
command for each, noting that EdSharp reads GitHub's Markdown where a Homer
document uses Pandoc's. Its script, toHomerEncoding, puts converted files into
the Homer encoding -- UTF-8 with a byte order mark and CRLF, none for .cmd,
.bat and SKILL.md -- since Pandoc and most converters write neither.

## 1.43.25 -- 28 September 2026

**Two more skills, and the tutorial skill carries the kit's guide.**

- **homer-elevate**: the Elevate Version feature. F11 checks GitHub for a newer
  release and offers to fetch and run its installer: an item on a multiple-
  document app's Help menu, or the version section and Yes/No buttons of a
  single-dialog app's Help box, through the kit's Elevate class in C# or
  Python.
- **homer-installer**: the Inno Setup installer -- machine-wide installs, the
  folders things go to, which optional components to offer, install scripts,
  and the finish page. Its references are FinishPage.md, copied from help, and
  components.md, the kit's calls for declaring a component, its three [Run]
  entries, labels, outcomes, Ollama models and detection.
- **homer-tutorial** now carries the kit's Tutorials.md, copied from help at
  each build: the conventions for spoken walks refined over many tutorials.

**FinishPage.md is the one account of the finish page.** It now holds the
wording rules that were in HomerDev.md -- the verb first, a short use in
parentheses, a box each for JAWS and NVDA, JAWS first, no word the tick
already says -- with two more: offer only the app's own components, and
install shared ones machine-wide. HomerDev.md points to it. It also names the
Results box's title and the logged verdicts.

**One order for the boxes: Install, Update, Reinstall.** FinishPage.md said so
in one section and "Install, Reinstall, Update" in another, and homerGroup
followed the second. The ticked boxes now come first everywhere, then the
unticked ones, so homerOrder, which the Results box lists by, matches the page.

## 1.43.24 -- 28 September 2026

**A skill for writing Homer code: homer-code.** The second development skill.
Its SKILL.md holds the Camel Type rules that matter most -- Hungarian
prefixes, c_ constants, lower camel case, functions rather than subroutines,
one-line ifs, for-each loops, sorted declarations and imports, a detailed log
from every script -- with the encoding rule and the instruction to build on
the kit's classes. Its references are kit-libraries.md, what each C# class
and Python module offers and how an app compiles or imports it, and the kit's
own style guides.

**A skill carries the kit's documents, copied at each build.** A skill
uploaded to claude.ai cannot read C:\\HomerDev, so homer-code carries the style
guides for C#, Python and JAWS script and the logging convention. buildHomerDev
copies them from help into the skill's references before packing, so they are
always the kit's current rules; LocalFiles.txt keeps the copies out of git,
which carries the originals. Anthropic's guidance asks a reference longer than
100 lines to open with a contents list, so the three long style guides now
have one.

## 1.43.23 -- 28 September 2026

**A skill for the build and release cycle: homer-build-release.** The first of
the Homer development skills. It teaches Claude the cycle -- buildHomerDev,
build, a quick test, tidy, push, release -- and how to read what the steps
leave. Its three references hold what is not obvious from the logs: the
lists and git rules (RepoFiles.txt, LocalFiles.txt, KeepEncoding.txt, what
stays tracked, the whitelist, the folder layout), the Homer log line, and the
failures that have each cost a run, with symptom, cause and fix. Its script,
summarizeLogs, turns a folder or zip of uploaded logs into one report: per app,
the newest build's result and version, the check's counts and failures, the
release's outcome with its version and whether GitHub confirmed it as latest,
tidy's changes and push's outcome. It reads the kit's own build as well as an
app's, and skips files that are not Homer logs. Tested on the uploads of 26 to
28 September, where it found each failure this chat found by hand.

## 1.43.22 -- 27 September 2026

From the first run of all ten apps on 1.43.21, whose program and script logs
came out in the new format:

- **An abbreviation is a word in a key.** Log.cs made "CLR" into cLR; it and
  log.py now write clr, as they write nvdaClient for "NVDA client".
- **The scripts name Windows as the programs do**: "Windows 11 25H2
  (10.0.26200.9550)" in tidy's, check's and every kit script's log, where they
  wrote Python's "Windows-11-10.0.26200-SP0".
- **The build templates' ISO start and end lines reach the apps.** An app's
  build script is its own copy of the template, made when the app was, so
  1.43.21's change to the template reached no existing app: 2htm's log still
  began "2htm build started Sun 09/27/2026 17:06:47.56". All ten apps' build
  scripts now start and end with `build start app=...` and `build end
  result=...`, EdSharp's build engine stamps every line in the Homer format,
  and DbDo's no longer writes "(Pacific time, Seattle)" after a time with no
  offset.

**An empty log no longer stops a release.** The kit's release on 28 September
was refused over three zero-byte files in logs. check now passes over logs --
a run's record is not part of the project -- and tidy deletes a zero-byte log
as it does any other empty file.

**The libraries live in exec, each named for its platform.** exec holds the
code an app's core work runs on, in any form -- native, .NET, or source for an
interpreter -- and scripts the tools that maintain the code base or extend an
app beyond its core. So the kit's C# classes are now exec\\CSharp and its Python
modules exec\\Python, beside exec\\Homer.dll. C# and Python are equal platforms,
so neither goes by the name Homer on the Python side: each module is imported
by its own name -- `import log`, `import inix, paths` -- as each C# class is a
class of its own, and the homer package and its __init__.py are gone. This also
ends homer sharing its first letter with help at the top of the kit. Every
build template, sample and app build script finds the kit by
exec\\CSharp\\Lbc.cs or exec\\Python\\log.py; a Python app's build puts
exec\\Python on PyInstaller's path and names each module plainly with
--hidden-import. buildHomerDev removes the old copies from CSharp, homer and
exec\\homer once the new ones are in place, and the old folders once empty.
exec stays off every repository, but tidy now honours a RepoFiles.txt line
inside a folder kept off it: the kit's .gitignore ignores exec's contents
("/exec/*") and puts exec/CSharp and exec/Python back after, since git never
looks inside a folder it ignores whole. fixEncoding no longer passes over exec,
touching there, as everywhere, only what RepoFiles.txt names.

**The skills have a home: .claude\\skills.** Claude Code finds a project's
skills there and nowhere else -- `.claude\skills\<name>\SKILL.md`, one folder
deep -- and the leading dot gives the folder a first letter of its own beside
scripts. homer-tutorial moves there from Templates\\skills, since a skill is not
something an app is made from, and three join it: app-help-guide,
blind-creators and podcast-directory, their descriptions put in the third
person as Anthropic's guidance asks. An index, ReadMe.md, sits beside them.
buildHomerDev packs each into exec\\skills\\<name>.zip for claude.ai. A new
KeepEncoding.txt keeps SKILL.md free of a byte order mark, which would hide its
front matter, and HomerDev.md gains "Claude skills", the rules for writing one.

## 1.43.21 -- 27 September 2026

**One log line format, for machines and for people.** From the session logs
of 2htm, EdSharp, FileDir, urlCheck and urlFido, run on 27 September:

- **Every line is stamped** with an ISO 8601 time, milliseconds and UTC offset.
  Before, the header said "Started 2026-09-27 16:16:40" and each line after it
  only "16:16:40", with no date and no offset, and blank lines, headings and
  settings carried no stamp at all.
- **Facts are key=value.** "    Log file                 = C:\..." is now
  `env logFile=C:\...`; "Ran: pandoc   exit code 1" is `run exit=1 cmd=pandoc`,
  with `ms=` when timed; "Session ended ... after 0 seconds" is
  `session end seconds=0.214`.
- **Windows is reported truly.** 2htm and urlFido logged "Microsoft Windows NT
  6.2.9200.0" -- Windows 8 -- on Windows 11: Environment.OSVersion answers that
  to any program whose manifest does not name Windows 10. The version now comes
  from the registry: "Windows 11 25H2 (10.0.26200.7462)".
- **The screen reader facts are facts.** The header's "Screen reader = Speech
  pipeline diagnostic" line, followed by the diagnostic's lines unindented and
  unstamped, is four facts: jawsRunning, nvdaClient, nvdaRunning,
  screenReaderFlag. Say.speechDiagnostic, the text shown to a person, no longer
  tells 2htm's and urlFido's users to put a DLL beside EdSharp.exe.
- **Python programs log what C# programs do**: the same keys, the true Windows
  version, and the screen reader facts, where urlCheck's header had none.
- **A fact is written once**: FileDir's header repeated Version and Program,
  and DbDo's the command line.
- **The kit's Python scripts** -- check, tidy, fixEncoding, unpushed,
  checkTutorial, uiCheck, buildHomerDev, checkHomerDev and newHomerApp --
  stamp every line the same way, with ERROR on a line that says ERROR, FAIL or
  FAILED, and WARN on one that says WARN.

And from the build, tidy, push, check and release logs of the same day:

- **Each kit script opens and closes the same way.** "tidy started 2026-09-27
  16:20:06", "Script: ...", "Python: 3.14.3 (tags/v3.14.3:323c59a, Feb ...)",
  "Platform: ...", "Command line: ..." and "Finished ..." are now
  `tidy start pid=...`, `env script=...`, `env python=3.14.3`,
  `env windows=...`, `env project=...`, `env arguments=...`, `settings ...`
  and `tidy end`, in every script. tidy no longer logs do-it, which it has not
  had since 1.43.9.
- **The build templates, push and the release launcher** start and end with
  an ISO 8601 line -- `build start app=2htm`, `build end result=succeeded` or
  `result=failed`, `release launch end exit=0` -- instead of "%DATE% %TIME%",
  which Windows writes as "Sun 09/27/2026 16:18:38.77" and whose form changes
  with the regional settings. The lines between still carry no stamp: a
  command's own output, from csc or Inno Setup, is appended as it comes.

The format is set out in HomerDev.md, "How a log line is written".

## 1.43.20 -- 27 September 2026

From reinstalling all ten apps:

- **installScreenReaderSupport named the app "scripts".** Installers put it in
  scripts, and it climbed out of exec only, so FileDir's finish page looked for
  scripts_JAWS.zip, logged to %LOCALAPPDATA%\scripts\logs, and installed no
  JAWS scripts. It now climbs out of scripts too. It also takes "jaws" or
  "nvda" to install one reader's support, so each has its own box.
- **JAWS and NVDA have a box each, JAWS first**, in the template: "Install JAWS
  scripts" and "Install NVDA add-on", and the same with Update.
- **The Results box is titled "<App> Setup Results".** Inno's MsgBox has no
  caption of its own, so the box was announced as the wizard's. homerResultsBox
  shows the same OK box through Windows' MessageBox, with the title.
- **Every component verdict is logged**: what was found and whether its box
  offers Install, Update or Reinstall. Before, only EdSharp and DbDo, with
  their own probes, recorded why a box was ticked.
- **Finish page wording** is written down in HomerDev.md, and the template's
  Launch and guide boxes follow it.

## 1.43.19 -- 26 September 2026

**The grave accent family is a kit convention.** HomerDev.md's "Choosing a
key" now sets out EdSharp's arrangement: Alt+Grave and Alt+Shift+Grave for
volume, Control+Grave and Control+Shift+Grave for rate, and the screen reader
key plus Grave for toggling punctuation, so punctuation never shares a key with
the other four. HomerView had given Toggle Punctuation Control+Shift+Grave,
Voice Slower's key.

**The templates need this kit.** build_APP_.cmd and build_APP_Py.cmd name
1.43.19 as kitNeeded, so a new app starts with every tidy, check and release
fix of the day.

## 1.43.18 -- 26 September 2026

**check reads a key combination whole, and in Python reads the gestures.** It
matched "Alt+Control" plus one more word, so Alt+Control+Shift+H was read as
Alt+Control+Shift, with Shift taken for the key. It also counted every mention
of a key in a Python file -- HomerView tells its user "Press
Alt+Control+Shift+H" in eight places, and one docstring still named a key the
add-on no longer binds -- 15 "reserved" findings, none of them a binding.
Now a combination is read with its Shift and its key; in a .py file only the
gestures NVDA binds ("kb:alt+control+shift+h") are keys; and the app's own
desktop shortcut is compared whole, modifiers and all, with the HotKey its
installer gives the desktop icon. Proved: HomerView and FileDir pass, and a
C# Alt+Control+S and a Python kb:alt+control+t are still caught.

## 1.43.17 -- 26 September 2026

**check never waits for a key.** Each acceptance command now runs with empty
input, so a "pause" or a prompt in it returns at once. HomerView's quality
check ended with "Press any key to close this window"; check captured its
output, so nothing was shown, and the release sat silent until it was stopped
by hand. The console now also names each acceptance command as it starts, so
a long one -- HomerView's accept list rebuilds the whole program -- is seen to
be running.

## 1.43.16 -- 26 September 2026

**version.py is kept out of git at the top of a project only.** tidy never
pushes the version.py a Python app's build generates beside its source, but a
bare name matched anywhere: HomerView's NVDA add-on carries its own
homer\version.py, which the add-on imports, and tidy would have untracked it.
The name is now /version.py, and a leading / anchors any name in tidy's lists
to the top of the project, as it does in .gitignore. Proved on HomerView's
repository: the add-on's version.py stays tracked.

## 1.43.15 -- 26 September 2026

**release publishes a draft and proves the release is the latest.** EdSharp's
v5.0.15 already existed on GitHub as a draft, left by an earlier run: invisible
to the public, so the list of releases rightly said it was not released, while
"gh release view" found it. release uploaded the installer to the draft and
reported success, because the download link answers for any earlier release
with an installer of the same name. Now an existing release is edited with
--draft=false --latest, and a failure is shown; and before calling a release
published, release asks GitHub which release it calls latest and stops unless
it is this one.

**check reads only the .inix files the project names**, as it does its
sources. FileDir's pre-kit Hotkeys.inix at the top, superseded by
configs\Hotkeys.inix, still named keys the program no longer has.

## 1.43.14 -- 26 September 2026

**check's key test no longer cries wolf on an app with a menu bar.** Run on
FileDir it reported 47 key problems, 40 of them false, from three blind spots:

- A method declared with no modifier -- FileDir's "void menuEditRename_Click(
  object sender, EventArgs e) {" at the left margin -- did not start a new
  owner, so every caption after it was counted as one earlier method's.
- A caption tested again in code -- ButtonDialog(..., {"&No", "&Yes"}) and then
  case "&No" -- counted as a second claim on its letter. Only two DIFFERENT
  captions with one letter compete now.
- A whole menu bar built in one constructor was one owner. A caption assigned
  to menuEdit... or miEdit... now belongs to the Edit menu, and one assigned to
  menuEdit itself to the menu bar.

The app's own desktop shortcut letter, read from its installer's HotKey, is no
longer reported as a reserved Alt+Control key: FileDir's Hotkeys.inix lists
Alt+Control+F because that is how FileDir is opened. What remains for FileDir
are its three real Alt+Control timer keys.

**buildHomerDev stops trying the 1.42.1 patch to release.ps1**, which release
no longer needs; every kit build logged that it could not apply it.

## 1.43.13 -- 26 September 2026

**release reads GitHub's list of releases rather than trusting an exit code.**
Even asking GitHub alone (1.43.12), it said EdSharp 5.0.15 was already
released minutes after the build, which steps over every tagged number, had
chosen 5.0.15. On that machine gh is gh.cmd, and the exit code of a batch file
passed back through cmd is not a reliable yes or no. release now asks gh for
the tag names of the repository's releases as JSON and looks for the tag among
them, ignoring drafts; only if that list cannot be read does it fall back to
"gh release view".

## 1.43.12 -- 26 September 2026

**release asks GitHub whether a version is released, and no one else.** It
also counted a tag on this machine as a release, so a tag left by an earlier run
that stopped before publishing made EdSharp 5.0.14 "already released" when
nothing was on GitHub -- its build, which steps over every number tagged on
origin, had just used 5.0.14. Now a release exists only when gh finds it; a tag
on this machine alone is pushed and published by the tag step. Without gh, a
local tag is still the answer, as there is nothing else to ask.

## 1.43.11 -- 26 September 2026

**tidy leaves a file where the project says it lives.** EdSharp keeps the two
libraries its repository carries, and the ones its build fetches, at the top of
the project, and its installer ships them from exec, where the build copies
them. Seeing the installer's exec\ names, tidy "put them in place", found exec
already held a copy, and moved every one into notes -- and git recorded
Tektosyne.dll and nvdaControllerClient.dll as deleted. A file RepoFiles.txt or
LocalFiles.txt names where it is now stays. Proved: with the installer naming
exec\Tektosyne.dll, tidy moved neither Tektosyne.dll nor Markdig.dll.

**KeepEncoding.txt: other people's files keep their encoding.** A project may
carry third-party tools, dictionaries, or files that show another encoding; a
byte order mark on a Lua filter or a tool's config is read as part of its first
line. KeepEncoding.txt, beside RepoFiles.txt and in the same form, names what
fixEncoding and check leave exactly as they are. tidy treats it as a project
file, and the whitelist always keeps it. Proved: a .lua file under a kept
folder stayed without a mark while the project's own .inix was fixed.

**check looks only at the project's own sources**, the files RepoFiles.txt
names, as its encoding test already did. EdSharp's release was refused over a
fruitBasket.cs in its pre-kit Samples folder, still on disk but no longer part
of the project.

## 1.43.10 -- 26 September 2026

**A name in RepoFiles.txt outranks a pattern in LocalFiles.txt**, in tidy's
choice of what stays tracked and in the whitelist .gitignore. EdSharp carries
Tektosyne.dll, which cannot be fetched, while its LocalFiles.txt says *.dll for
the libraries the build fetches; 1.43.9 would have untracked it. A file named
exactly in RepoFiles.txt now stays tracked and is put back after the
LocalFiles.txt patterns. Anything the kit never pushes -- the release scripts,
Version.cs, any .exe -- is untracked wherever it is. Proved on an
EdSharp-shaped repository: Tektosyne.dll and nvdaControllerClient.dll stayed;
Markdig.dll, the release script, Version.cs, version.txt and a stale Lbc.cs
were untracked; a new .dll stayed ignored.

**The whitelist puts back .gitattributes** as it does .gitignore, so the file
that keeps the Homer CRLF line endings is never left out of a repository.

## 1.43.9 -- 26 September 2026

**tidy just does it.** It no longer prints a plan and waits for --do-it: one
run carries the plan out. Nothing is lost -- a stray goes into notes, which is
on this disk and never in git, and the log names every move; the only
deletions are zero-byte files and things the build fetches again. --do-it is
still accepted and changes nothing, so an old habit does no harm.

**tidy untracks what RepoFiles.txt leaves out.** Its repository survey used
the folder's test of belonging, which also accepts what LocalFiles.txt, the
installer and the standing names allow -- version.txt and any .cs among them.
So on DbDo it reported "0 files tracked that the project does not name" while
version.txt, Version.cs, release.cmd and release.ps1 were all tracked. A
tracked file now stays only when RepoFiles.txt names it and LocalFiles.txt does
not; the files themselves stay on disk. Proved on a DbDo-shaped repository:
those four and a stray temp.txt were untracked, the rest kept.

**release parses again.** 1.43.8's message "version.txt says $sFileVersion: the
last build" is a drive-qualified variable to PowerShell, and the whole script
failed to parse; the launcher log caught it. Written ${sFileVersion} now, and
no other string has the pattern.

## 1.43.8 -- 26 September 2026

**The renamed scripts called their neighbours by the old names.** After 1.42
renamed homerTidy to tidy and the rest, tidy.cmd still ran "%~dp0homerTidy.py",
check.cmd "%~dp0checkHomerApp.py", unpushed.cmd "%~dp0gitUnpushed.py",
installOllama.cmd "%~dp0homerInstall.cmd", and push.cmd asked whether
"%~dp0homerTidy.cmd" existed before rewriting the whitelist. The build's rename
step was meant to fix such lines, but its pattern would not match a name with a
digit before it, and every one of these follows the 0 of %~dp0. So in every
app that refreshed them, tidy and check stopped at once, and push skipped the
whitelist without a word -- DbDo's push that day committed version.txt,
Version.cs and the release scripts, which its RepoFiles.txt leaves out.

- The five scripts call tidy.py, check.py, unpushed.py and installCommon.cmd.
- The rename pattern allows a digit before a name.
- buildHomerDev reports any script in scripts that calls a neighbour which is
  not there, unless the same line first asks whether it exists. Proved by
  putting homerTidy.py back into a copy of tidy.cmd: the check named it.

**release asks git and gh through System.Diagnostics.Process**, with both
streams captured, instead of through cmd /c. The 1.43.7 edition built cmd
lines that Windows PowerShell 5.1 quotes its own way, and the first release
with it stopped on "The syntax of the command is incorrect".

**release.cmd keeps a launcher log**, logs\<App>-release-launch-<stamp>.log,
with the command line, PowerShell's error stream and the exit code, so a
failure before release.ps1's own transcript starts still leaves a record.

## 1.43.7 -- 26 September 2026

**release, the script that used to be tagRelease, fixed from the day's logs.**
It is not in the kit's repository -- by standing rule the release scripts never
are -- but it lives in C:\HomerDev\scripts and every app's build refreshes it
from there, so this zip carries it. Of six releases on 26 September, three
stopped and the three that published looked as if they had failed:

- **Where the installer is.** DbDo, EdSharp and FileDir stopped with "<App>_setup.exe
  not found". It looks at the top of the project, where every Homer build
  writes it, and now also in exec, where DbDo wrote it before 1.0.200, saying
  so. The message names both places and the build to run.
- **An older installer is not published.** HomerView was published as 1.48.53
  while its version.txt said 1.48.63: its builds had stepped the number without
  finishing a new installer, and the release tagged the old one with only a
  note. It now stops and says to build; -Force publishes the older one anyway.
- **No false alarms.** Every "is this tag here yet?" question printed red
  NativeCommandError blocks, because Windows PowerShell 5.1 records each line a
  native program writes to stderr as an error, even with 2>$null. Those
  questions now go through cmd, which discards stderr first.
- **The check runs first.** The documents said release runs scripts\check before
  publishing; only HomerScribe's own copy did. Now every copy does, and stops
  when the check fails. -NoCheck skips it.

## 1.43.6 -- 26 September 2026

**Python apps build their WinForms dialogs with the C# LbcDialog.** A Python
app with a WinForms interface had to write its dialogs by hand, since the
kit's homer\lbc.py is Lbc for wxPython, which NVDA code needs. Rather than a
second Lbc written in Python and kept in step by hand, the C# one is now
reachable from Python:

- **buildHomerDev compiles exec\Homer.dll** from CSharp\Elevate, Inix, Lbc,
  Log, Paths, Say, Util and Web, after the samples (whose C# build installs
  the Build Tools where needed). A failure is reported with the samples'.
- **homer\lbcnet.py** loads it through pythonnet from the program's bundle,
  beside the program, or the kit's exec folder; sets the thread to a
  single-threaded apartment; and returns the Homer namespace. strings() and
  keyHandler() give runWithButtons its string[] and commandKey its
  Func<Keys, bool>.
- **build_APP_Py.cmd** has a homerDll setting: 1 bundles
  C:\HomerDev\exec\Homer.dll into the program, and the build stops with a
  plain message when buildHomerDev has not made it yet.

The focus order, keys, Help box and version check are therefore the same in
both languages by construction. urlCheck 1.12.3 is the first user.

## 1.43.5 -- 26 September 2026

**seedVersion is a floor in both build templates.** It was only a starting
point, used when version.txt was missing, although its comment said "nothing
lower than this". 2htm showed the gap: its machine already had a version.txt
holding 1.18.4, so its first kit build stepped to 1.18.5 while its documents
named 1.19.0. Now a version.txt below seedVersion is raised to it, logged,
and taken as it is for that build, the same as a newly made one. A number
already at or above the floor is stepped as before.

## 1.43.4 -- 26 September 2026

**check no longer starts a windowed program.** Its smoke test ran the program
with --help, which a console program answers and exits; a windowed one --
bookFido, and every MDI app -- opens its window and waits for a person, so the
check sat for its whole fifteen-minute timeout and then called that a failure.
The PE header now says which kind a program is, and a windowed one is reported
as started by hand. Proved on the real executables: bookFido.exe reads as
windowed, urlFido.exe as console.

## 1.43.3 -- 26 September 2026

**Templates\build_APP_.cmd lost half a Python template.** 1.43.2's C# template
was assembled from the Python one, and the piece meant to be its version
subroutines was cut from the first ":seedVersion" in the file -- the one in
"call :seedVersion" -- so 278 lines of the Python template followed the C#
subroutines: a second :seedVersion, a second :failed, and the Python build
steps. cmd takes the first label it meets, so "call :seedVersion" landed in the
pasted copy, found no version.txt, and the build stopped with "Build FAILED"
written twice and nothing else. urlFido's first build did exactly that. The
pasted copy is gone.

**buildHomerDev checks every .cmd in Templates, Templates\samples and scripts
for a label defined twice, and for a goto or call to a label that does not
exist.** Neither is ever an error to cmd; both are now problems the kit build
reports. Proved by adding a second :failed and a jump to a missing label to a
copy of the template: the check named both.

## 1.43.2 -- 26 September 2026

**Templates\build_APP_.cmd keeps the same contract as the Python template,
clause for clause.** It had fallen behind: the program went to the top of the
project, no kit version was checked, a missing version.txt became 1.0.0, kit
tools were refreshed only if present and without a word when not, and any
running copy of the program -- the installed one included -- stopped the
build. Now: kitNeeded with a trimmed comparison; version.txt seeded from the
app's number or one past its newest release tag, written into Version.cs;
Roslyn found with vswhere or installed with winget as the Build Tools, never
the Framework's C# 5 csc; the kit classes named in homerModules compiled from
the kit, and an app's stale copies of them deleted; NuGet packages and NVDA's
controller client fetched (the client from NV Access's published
controllerClient.zip, 2025.3, beside the program or embedded); the program
built into exec\; only a copy running from the project's own exec reported,
never closed; the kit tools refreshed by name and retired ones deleted; every
.md given its .htm; fixEncoding; every help\ file checked against the
installer; /DHomerDev= to ISCC; one log per run in logs\. urlFido's
buildUrlFido.cmd is the worked example.

buildHomerDev no longer notes a missing retired loop in the C# template: the
list is a retiredTools= variable now, as in the Python template, and the
renaming leaves that line alone.

## 1.43.1 -- 26 September 2026

**buildHomerDev no longer rewrites the Python template's retired list.** Its
first 1.43.0 run did: "REWROTE old script names in Templates\build_APP_Py.cmd"
turned checkHomerApp, gitPush, homerTidy and tagRelease into check, push, tidy
and release, so an app made from the template would have deleted, on every
build, the tools it had just refreshed. The renaming skipped only the C#
template's retired loop; it now skips the retiredTools= line too, and this kit
ships the template whole again.

**The installer template takes the program from exec when it is there**, and
ships every document in help\. A build in the Homer layout -- the Python
template's, HomerScribe's, HomerView's -- leaves the program in exec\, and the
template named it only at the top of the project. An older build that leaves
it at the top still works. A new define, AppLaunchParams, is what the program
is started with after the Results box, as its desktop shortcut starts it.

**urlCheck's installer follows the template's pattern whole**: the component
table included from the kit the build names, the ticked boxes noted when Finish
is pressed, the Results box, then the launch -- with no components registered,
since urlCheck needs none.

## 1.43.0 -- 26 September 2026

**The Python side brought level with the C# side**, from moving urlCheck, the
first Python app, to the kit.

**homer\elevate.py**, the Python Elevate: configure, check, isNewer, describe,
update and offer, with the same outcome numbers as Elevate.cs. Its boxes are
Windows message boxes through ctypes, so it serves a wx program, a WinForms
program through pythonnet, or one with no window. It takes over the version
comparison of **homer\version.py, which is retired**: every build writes a
version.py of its own, so .gitignore and the checks treat the name as
generated, the module was never pushed, and the kit's check reported it
missing on every build.

**homer\say.py speaks outside NVDA.** Inside NVDA it still uses ui.message;
outside, it tries JAWS by COM (pywin32 or pythonnet, whichever is there), then
the NVDA controller client DLL through ctypes. say("Column 3", "Row 12",
"Paid") sends three utterances with nothing between them, as Say.cs does; a
trailing True is still the interrupt flag.

**Templates\build_APP_Py.cmd keeps the whole contract**: kitNeeded with a
trimmed comparison; version.txt seeded from the app's own number or one past
its newest release tag, never from 1.0.0 over a released app; version.py
written every build; Python found or installed by winget and a .venv rebuilt
when its Python differs; the program built into exec\ with PyInstaller's
scratch in work\ and the kit's modules named by --hidden-import; a copy running
from the project's own exec reported, never closed; the kit tools the app
names refreshed and retired ones deleted; every .md given its .htm when newer;
fixEncoding; every file in help\ and every scripts\install*.cmd checked
against the installer's Source: lines; /DHomerDev= passed to ISCC; one log per
run in logs\.

**scripts\check.py**: the smoke test looks in exec\ first -- before, it looked
only at the top of the project and found nothing for any app moved to the
layout; the key check reads a Python function as a window's builder, and does
not count an HTML entity such as &amp; as a trigger letter.

**Templates\_APP__setup.iss**: the previous install is read once, in
InitializeSetup. Read lazily, a fresh install cached nothing and the finish
page's Check: functions then found the install that had just been made,
offering "Update the JAWS scripts" where "Install" belonged. The component
table is included from the kit named by /DHomerDev.

**scripts\tidy.py puts back files named one by one in a subfolder.** The
whitelist began "/*", which ignores the folder help itself, and git never
looks inside an ignored folder, so "!/help/Announce.md" put back nothing:
every file named individually in help\ or scripts\ -- as the rules for
RepoFiles.txt ask -- was silently left out of the repository. The folder is
now put back and its contents ignored again ("!/help/" then "/help/*") before
the named files. Proved with git on urlCheck's list: before the fix 15 files
were staged and 19 left out; after it, all 34. **Run scripts\tidy --gitignore
in every app whose RepoFiles.txt names files inside a folder** (HomerView's
scripts, for one) and push: those files may never have gone up.

**help\CamelType_Python.md** joins the C# and JAWS script documents, moved
from urlCheck and updated for the c_ constant prefix and the kit's imports.
buildHomerDev now empties the old Python\ and Samples\ folders, whose last
files no move pair reached. HomerDev.md and paths.py no longer say to put
C:\HomerDev\Python on the path, or that a development folder stays flat.

## 1.42.1 -- 26 September 2026

release no longer shows two red error blocks on a release that
succeeded: asking git whether a tag exists, and gh whether a release
exists, normally gets the answer no, and that answer is no longer
recorded as an error. push now notices when GitHub says a repository
has moved, and points origin at the new address once, so the notice
stops. Both are patched into the scripts in place by buildHomerDev,
keeping everything else in them.

## 1.42.0 -- 26 September 2026

The scripts have shorter names: tidy (was homerTidy), push (gitPush),
unpushed (gitUnpushed), release (tagRelease), check (checkHomerApp),
finish (homerFinish) and installCommon (homerInstall). buildHomerDev
renames them in place, keeping their content, rewrites the old names
in the kit's files, and adds them to the template's retired list so each
app's build removes its old copies. Each app's own build script names
the new ones and needs kit 1.42.0. The renaming and retiring now run
whether or not pandoc is present. help\HomerDev_update.md now holds
everything HomerView's migration taught, as rules.

## 1.41.3 -- 26 September 2026

Three fixes to the installer template, all found by building FileDir's
installer from it -- the first app to do so on this machine.

**isOlderInstalled no longer uses PackVersionString**, which this Inno Setup 6
does not have: the compile stopped at the Code section with "Unknown identifier".
The comparison is written out in plain Pascal -- each dotted part read as a
number and compared in turn -- so an installer's version check does not depend
on the compiler's version.

**CopyFile in place of FileCopy**, which Inno has renamed and reports as a hint
on every build. The line keeps the setup log with the program's own logs.

**UsedUserAreasWarning=no.** The template writes the setup log and the launch
marker to the profile of whoever answered the elevation prompt, on purpose and
with a comment saying so. A warning read past on every build teaches people to
read past warnings.

## 1.41.2 -- 26 September 2026

`commandKey` is settable on the dialog, not only on its form. 1.41.1 put the
hook on LbcForm, where ProcessCmdKey runs, and forgot the property on
LbcDialog that hands it through -- so an app holding a dialog had no way to
reach it. The dialog wraps its form; the app sets `dlg.commandKey` and never has
to know which class holds the override.

## 1.41.1 -- 26 September 2026

**Lbc.cs takes in FileDir's work on it**, so that FileDir can stop carrying a
copy and every app gets what FileDir paid for. The two files had drifted 40 per
cent apart in both directions -- FileDir had thirty-eight methods the kit lacked
and the kit had forty-nine FileDir lacked -- so this is a merge rather than a
replacement, and nothing the kit already did was given up. The same merge
shipped as 1.40.0 and 1.40.1, was compiled clean by the kit's own samples, and
was then overwritten by the 1.41.0 update; it is recorded here so it is not lost
again.

**No control names itself after its own caption or its label.** Thirty-two
AccessibleName assignments are gone: a screen reader reads the caption or the
Label before the control AND the accessible name, so a name repeating either is
heard twice. Four remain, all empty, and for the opposite reason: a layout panel
with no name is reported under the WINDOW's name, so focus arriving through two
nested panels made a screen reader say the dialog's title three times. Help and
the F7 control list now work a control's name out from its Label through
fieldName and nameFromLabel.

**Finding in a list, rebuilt.** Control+J jumps by the line the list shows;
Control+K searches everything known about each item with the keyword syntax --
`red & blue` for both, `red | blue` for either, `chap*` for anything starting
that way; Control+F filters by the same syntax and Control+Shift+F clears it;
F3 and Shift+F3 repeat whichever search was last. Each prompt keeps its own last
ten answers through the historyRead and historyWrite hooks. setListItems,
listSourceIndex and listIsFiltered let an app rebuild a list and still know
which item a visible row is.

**Control+Home and Control+End belong to the control that has them** -- first
and last item in a list, top and bottom in a multiline box -- and move between
fields only where the control has no use for them. **A multiline box starts at
its beginning**, and a read-only one keeps Enter for the default button.

**The status line carries status.** setStatusExtra puts a standing note there,
read with the screen reader's own key and never announced; where a dialog has a
note the note is the whole line. appendStatus keeps a transcript of what a
command said.

**New to the toolkit:** LbcTrackBar and addSlider, a slider that reports its
value in words; commandKey and dialogKey on LbcForm, claimed in ProcessCmdKey
before any control and before the screen reader; focusedControl; runPlain and
close, for a dialog whose buttons are commands; stackFields, which flattens
bands; and an addButton overload with no tip.

**System.Convert is written in full.** Two lines said `Convert.ToString`, which
inside the Homer namespace binds to any app's own `Homer.Convert` class before
it reaches the framework's -- and FileDir has one. A shared class cannot assume
what an app does not define.

Util.cs gains looksLikeText and readSample: whether a file is text at all, and
the sample of bytes that decides it.

## 1.39.1 -- 25 September 2026

help\HomerDev_update.md: the briefing for bringing another Homer app up to
the current kit -- what the kit is, the contract between an app and it
(finding the kit, kitNeeded, compiling against its sources, refreshing its
scripts, the folder layout and why the first letters differ, the two lists,
the four scripts, versions, machine-wide components, the fetching build,
logs and encoding, the finish page, F11, the walks, the check), the lessons
paid for with their dates, the migration in ten steps, and what DbDo and
EdSharp each still need -- and, from 1.39.1, FileDir: its two-branch
repository, copied classes with a per-project namespace, binaries in git,
and earlier editions of the tools. The first release of HomerScribe through the whole
chain -- build, check, push, tag, installer asset -- went through today.

## 1.38.3 -- 25 September 2026

HomerScribe's first release through tagRelease's built-in check was refused
on three counts, two of them the check's own fault and one half mine. The
check demanded FAQ.md, which the default document set never included;
Announce and FAQ are welcome now, never required, and Tutorials is required
only where tutorial scripts exist. It accepted only the kit's Log.start as
evidence of logging; a program that opens its own file under a logs folder
counts. And it judged the encoding of every text file in the folder, strays
included; it judges the files RepoFiles.txt names, the project's own. The
half mine: eighteen delivered .htm files had never been put into the Homer
encoding. scripts\fixEncoding, new, puts every file RepoFiles.txt names into
UTF-8 with a mark and CRLF (.cmd and .bat without the mark), logs to
logs\<App>-encoding-<stamp>.log, and every app's build runs it before the
compile, so the check that follows has nothing to find. tagRelease's probe
for an existing release no longer logs "release not found" as an error.

## 1.38.2 -- 25 September 2026

The tutorial log is readable again: PowerShell's five-line wrapper around a
native program's first standard-error line, and piper's "[info]" progress,
are dropped -- a seven-walk run had logged 186 KB of them, and the "Error"
in "FullyQualifiedErrorId" had slipped through the earlier filter. The
loudness pass logs its setting once per walk and only a failure per piece.
The build log records the tutorial tool's exit code and the time beside its
outcome line.

## 1.38.1 -- 25 September 2026

One rule for where a tool is run: the project is the current folder, or its
parent when the current folder is the project's scripts or exec folder.
homerTidy and checkTutorial already worked that way; gitPush, tagRelease,
checkHomerApp and gitUnpushed now do too -- a push run from scripts had
logged to scripts\logs and looked for RepoFiles.txt there, and a release run
from scripts handed the checks the scripts folder to judge. checkHomerApp
runs build<App>.cmd, the script named after the folder, never another
build*.cmd: it had run buildTutorials.cmd with "nobump" as a script name,
which is where every stray "nobump.inix is not here" came from. Its log and
its evidence report go in logs, named like the rest. And the kit's build
removes the copies of kit tools it finds in C:\bin -- only files bearing a
kit tool's name, each removal logged -- since a push and a release ran from
those stale copies today.

## 1.38.0 -- 25 September 2026

One tool per job, and the names that sounded alike are gone. cleanDir and
tidyRepo, with homerPolicy that only tidyRepo read, are homerTidy; gitRelease
is tagRelease, which now runs the app's checks itself before touching a tag
(-SkipCheck when a caller has just run them, as releaseHomerDev does);
sayTutorial is buildTutorials; installTools, which copied tools into C:\bin
where they went stale, is gone, since every app refreshes its scripts from
the kit on each build. The build deletes a retired file when it finds one and
says so; checkHomerDev reports any kit tool found on the PATH outside the kit
as a copy to delete; buildHomerDev warns once when C:\bin holds one.

A move-pair bug: Windows does not tell Scripts from scripts, so the pair
that had once moved Scripts\homerInstall.cmd into Templates saw the newly
delivered scripts\homerInstall.cmd as the old copy and deleted it. The pair
is gone and the move list skips any pair whose two sides are the same file.
LocalFiles.txt names the sample programs' build products.

## 1.37.0 -- 25 September 2026

Two folders that broke the first-letter rule, and the kit's copies of shared
scripts. Samples shared its letter with scripts: the four fruit-basket
programs and their build scripts are under Templates\samples, and the
build's move list carries them over and removes the old folder. The shared
install scripts -- homerInstall, installOllama, installScreenReaderSupport,
homerFinish -- were starters in Templates that every app carried under
scripts and let drift; they are kit scripts now, refreshed into each app's
scripts folder by its build, and the newer installOllama from HomerScribe
(which updates through winget rather than saying "already installed") is
the kit's. installModels.cmd stays a template: it names an app's own
models. The template installer ships and runs them from scripts, as
HomerScribe does.

The tutorial tool: the reader speaks through piper even when Kokoro is
here, which halves the minutes; long text is cut at sentences and commas
before Kokoro sees it (a spelled-out web address took 71 seconds whole);
Kokoro runs on two threads, measured faster than all of them; every piece
is brought to one loudness, and ReaderGain scales the reader's; and a
"step N of M" line every four steps says the minutes are speaking.

## 1.36.2 -- 25 September 2026

A build was stopped by hand because its screen said one sentence and then
nothing for three minutes, and the silence read as a second download of
the voices. It was Kokoro speaking walk 01. Now the tutorial tool says once
which voices it has and where from ("Voices: Kokoro, from C:\HomerDev\exec.
Nothing is downloaded."), says "Creating <name>.mp3, N steps" as each walk
starts and "Created <name>.mp3 in N minutes" as it finishes, and both the
kit's build and an app's let those lines reach the screen instead of
capturing them into the build log. Kokoro runs on every processor core
rather than two, and its configuration and progress chatter -- which
PowerShell had been logging as a "NativeCommandError" -- is kept out of
the log except for its timings.

## 1.36.1 -- 25 September 2026

Three faults from the first full run of 1.35 and 1.36, and two more lines
of reader grammar. Kokoro was fetched and unpacked and then not recognised:
the int8 bundle names its model model.int8.onnx, and only model.onnx was
looked for; both are now. "nobump" arrived in the tutorial tool as a script
name, because cmd's %* is not reset by a bare "call": a build now passes
-build, an argument of its own, and the tool ignores any dash-argument it
does not know and names the scripts present when one is asked for by a
wrong name. cleanDir, which judged the folder it was run in and logged
beside itself, forwards to homerTidy with the same arguments. Tutorials.md
and the skill gain the reader's phrasing of a slider with a value, a numeric
edit, a tabbed dialog, a list view item, and a program's loading message.

## 1.36.0 -- 25 September 2026

The screen reader's speech in a tutorial is now checked by code and written
by a skill. scripts\checkTutorial reads every Tutorial_*.inix against the
format and the reader's grammar and names the script and step for each
problem; buildTutorials runs it first and speaks nothing while a problem
stands. It found twelve in HomerScribe's seven walks on its first run and
seven in the kit's own. Templates\skills\homer-tutorial\SKILL.md is a
skill for an AI writing these: the four beats, the grammar of every control
and of an edit box, where a Hear line's truth comes from, and the commands.

## 1.35.1 -- 25 September 2026

gitPush, in the form Jamal has used by hand -- clear the screen, add
everything, commit "Fix." or the message given, push, show the status --
with the guard the day taught: it stops when there is no RepoFiles.txt,
rewrites the whitelist .gitignore from RepoFiles.txt before staging, and
refuses a commit that stages anything over 10 MB, naming the file. Developer.md
gains "The five scripts, and the order they run in": build, gitPush,
homerTidy, tagRelease, gitUnpushed, and what RepoFiles.txt and
LocalFiles.txt each decide.

## 1.35.0 -- 25 September 2026

Four things learnt from one afternoon's logs.

ONLY THE KIT FETCHES THE VOICES. buildHomerDev runs scripts\buildTutorials
with -fetch, which is the one way the tool downloads engines and models; an
app's build finds them in C:\HomerDev\exec or says "Run buildHomerDev" and
speaks nothing. The sherpa-onnx package taken is the shared one, which
carries the executable; the static "lib" package it took before -- hundreds
of megabytes of link libraries and no executable -- is removed when found.

FETCHED THINGS ARE DELETED, NEVER ARCHIVED. A tidy found the old per-app
voices, called all 486 files strays, moved them into notes\other, and
committed them. homerTidy now recognises what a build fetches -- engines,
models, packages -- and deletes it, including anything an earlier tidy put
into notes.

NOTHING IS STAGED WITHOUT A WHITELIST. With no RepoFiles.txt, homerTidy's
"git add -A" swept those 480 files into a commit. Without RepoFiles.txt the
repository is now left exactly as it was, and the console says why.

scripts\gitUnpushed undoes the commits not yet pushed and keeps every file,
so a commit like that one is put right by one command and the next tidy.
gitRelease and gitPush log to logs\ like everything else. Every app's build
refreshes the whole tool set from the kit into its scripts folder --
buildTutorials, makeTutorials, homerTidy, checkHomerApp, tagRelease,
gitRelease, gitPush, gitUnpushed -- so scripts\tagRelease is the release
command in every Homer app, and the copy in C:\bin is retired.

help\Tutorials.md gains the reader's grammar inside an edit box, from a
class on reading and editing text: typing echo, Backspace, Blank, Top and
Bottom of file, the three ways of selecting and their words.

## 1.34.0 -- 25 September 2026

The kit follows the layout it asks of every app. Tools is now scripts:
every build script, every document and RepoFiles.txt say scripts, the
build's move list carries each of the 22 files over and removes the empty
Tools folder, and homerTidy is at C:\HomerDev\scripts\homerTidy.cmd. The
standard folders -- configs, data, exec, help, logs, results, scripts,
templates -- were chosen with distinct first letters so a list of them can
be walked by initial letter, and "tools" collided with "templates".

The tutorial voices live in C:\HomerDev\exec, not a new voices folder: exec
is the Homer folder for binaries that are not in git, and a fetched engine
with the model files beside it is exactly that. Piper's models sit in
exec\piper beside piper.exe, so exec holds one folder per engine.
LocalFiles.txt names exec as never pushed. (1.33.0's voices folder was
never released.)

## 1.33.0 -- 25 September 2026

The tutorial voices live in one place, C:\HomerDev\voices, fetched once and
found by every app's build; they are no longer fetched into each app's
scripts\voices. Neither piper nor sherpa-onnx has an installer, so the kit
names the place, as the one folder every Homer app already relies on.
HOMER_VOICES overrides it. The kit gains LocalFiles.txt, naming voices\ and
logs\ as local and never pushed, and its build skips the voices folder.

## 1.32.0 -- 25 September 2026

The spoken tutorials change shape, and the tools that make them move with
them. Tools\buildTutorials.ps1 writes one .mp3 per walk into help\tutorials
with Tutorials.m3u beside them, and no Tutorials.mkv; makeTutorials.py looks
for the audio there. The reader is a bit slower (ReaderScale 0.64, was 0.56),
at a beta tester's request. Kokoro-82M, run through sherpa-onnx, is the voice
when it can be fetched -- Apache 2.0 throughout, so the audio can be published
under MIT -- with piper's kristin and john as before when it cannot; the
licence findings are in help\Tutorials.md. Templates\build_APP_.cmd and
Templates\_APP__setup.iss carry the new step and ship the audio: the tools
are refreshed from the kit into the app's scripts\ on every build, because
the kit's copy run in place takes the kit for the project.

help\Tutorials.md gains "How a reader phrases a control", the grammar of a
screen reader's speech for every control, taken from two training classes and
naming no reader; and the tutorial scripts are to name none either.

## 1.31.1 -- 25 September 2026

Two build failures from 1.31.0, both fixed. homerNoteTicked was declared a
function with no return type, which Pascal refuses ("colon expected"); it is
a procedure. The two C# sample builds and Templates\build_APP_.cmd compiled
Lbc.cs without the Elevate.cs it now depends on; each lists it.

help\Tutorials.md gains "How a screen reader trainer narrates": nine beats
taken from a professional JAWS training recording -- key, press, hear, then
translate; letters with their phonetic word; the reader quoted word for word
and then paraphrased; silence named; focus verified after every change; the
repeat key taught first; counts used as orientation; controls named as the
reader names them; a breath before each key. Templates\Tutorial_00_Overview.inix
carries the short form.

## 1.31.0 -- 25 September 2026

Two patterns every Homer app is to follow, asked for on this date.

THE ORDER OF THE FINISH-PAGE BOXES: Install (screen reader scripts first,
then components alphabetically), ticked; Update, ticked, alphabetical;
Reinstall, unticked, alphabetical; Launch, ticked; Open the user guide,
unticked. Done with three [Run] entries per component, one per verb, using
the new homerIs(i, state) and homerModelIs(model, present) checks; Inno's
script order and Check: do the grouping. FinishPage.md states the rule.
Templates\_APP__setup.iss is rewritten to it -- it includes
HomerComponents.iss, registers Ollama with homerAdd, keeps the screen reader
script entries, reports the Results box from homerOutcomeLine, starts the
program after that box through the launch marker, and its [UninstallDelete]
names only logs and settings, never the whole app-data folder. homerFinish.cmd
is no longer shipped by the template.

THE HELP BOX CHECKS THE WEB FOR A NEWER VERSION. New shared class
CSharp\Elevate.cs: an app calls Elevate.configure(owner, repo, version) once
at startup; the Lbc Help box then ends with "This is version X. Version Y is
on the web." and its buttons become Yes and No -- Yes the default when a newer
version exists, No when this is the newest, OK alone when the web could not be
checked (eight-second timeout, so an offline machine never hangs the box).
Yes fetches <repo>_setup.exe from the latest GitHub release and starts it.
Elevate.offer(owner) does the same conversation in a message box for an F11
handler. LBC NOW REQUIRES ELEVATE.CS: add CSharp\Elevate.cs to every build
that compiles Lbc.cs.

Util.spokenLength(seconds) says a LENGTH in words -- "19 minutes", "1 hour
and 6 minutes", "45 seconds" -- because a screen reader reads "19:00" as
nineteen hundred hours and "1:06:06" as a time of day. HomerScribe reported a
nineteen-minute run as "Took 19:00". A clock reading is only for a POSITION:
where in a film or recording something is.

Lbc.runWithButtons gains a third argument naming the default button, so a
Yes/No box can keep Yes-then-No order with No as the default. The first
label is the default when the argument is absent -- so list OK first: with
Help first, Enter in HomerScribe's source paths field opened Help.

## 1.30.0 -- 25 September 2026

The Results box after an install reports only the boxes that were ticked,
from a probe made after the scripts ran: homerNoteTicked records the ticked
captions when Finish is pressed (from NextButtonClick at wpFinished);
homerOutcomeLine and homerModelOutcomeLine each return a past-tense line for
a ticked box and nothing for one that was not. Until now the box recited
every component from the probe made when the wizard opened -- so a minute
after Whisper was installed and Ollama updated, it said neither had
happened, and it listed three components nobody had asked about.

FinishPage.md gains the Results-box rule and the "Downloading" rule for
install-script console messages.

## 1.29.0 -- 25 September 2026

Four files delivered the day before had landed in folders the kit never had:
Docs, Inno and Scripts. They now sit where RepoFiles.txt says kit files go --
FinishPage.md and Logging.md in help; HomerComponents.iss and homerInstall.cmd
in Templates, beside _APP__setup.iss and installOllama.cmd. The build's move
list removes the old copies once the new ones are in place, and the emptied
folders after them, so nobody deletes anything by hand.

The build's log moves to logs\HomerDev-build-yyyyMMdd-HHmmss.log, one file
per run, and each sample build's log to logs\<App>-build-yyyyMMdd-HHmmss.log
beside its script -- the convention every Homer build follows. The fixed
buildHomerDev.log and build<App>.log at the old places go the same way.

version.txt carries no byte order mark. cmd's set /p, which the app build
scripts use to read it, cannot strip one, and a build refused a kit of
exactly the version it asked for when one was present. normalizeHomer
already knew this; the file had been saved wrongly.

## 1.28.0 -- 24 September 2026

HomerComponents.iss gained a sixth homerAdd argument, the registry Uninstall
key name, checked under HKLM, HKCU and WOW6432Node. An installer runs
elevated, where winget is often unreachable and a per-user tool is not on
the PATH, so Ollama read as absent on a machine that runs it daily. It also
gained Ollama model detection (homerModelPresent, homerModelWanted,
homerModelLabel) from one ollama list call, and Install-Reinstall-Update
grouping with case-insensitive alpha sorting within each group.

homerInstall.cmd resolves the app name with ~f first, so a path ending in
".." cannot yield ".." as the name, and takes a noPause argument in place of
an environment variable. It and the build scripts stamp their logs with
PowerShell's Get-Date; WMIC is gone from Windows 11 and every log had been
named with zeros.

homerTidy.py writes logs\<App>-tidy-yyyyMMdd-HHmmss.log in the project the
script belongs to, worked out by climbing out of scripts, tools or exec,
rather than surveying whatever the current directory was.

Two documents: FinishPage.md, the rule for what a finish-page checkbox says
and whether it starts ticked; Logging.md, where logs go and what they open
with.

## 1.27.0 -- 23 September 2026

**Repeated speech is handled in the kit, not app by app.** `Say.say` drops a
line that repeats the last one within a second and a half, or that matches the
title of the window in front or the name of the control with focus -- the three
shapes of duplicate announcement that have been reported for years. `sayForced`
is never guarded, so a toggle can answer twice. Anything dropped is logged with
the reason.

The other mechanism, an accessible name repeating a caption, cannot be fixed at
run time and is now audited instead: every accessible name is compared against
every caption in the same source, and a match fails the check. A new section in
the guide, **Not twice: speech that repeats**, says which is which.

## 1.26.0 -- 22 September 2026

**The published repository was missing most of itself.** The whitelist in
.gitignore still named the documents at the top level, where they were before
they moved into `help`, and named neither `help`, `Tools`, `version.txt` nor the
check and release scripts. So a clone or a downloaded zip had no guide, no
history, no tools and no checker -- which is what an outside audit of the
published archive found. The whitelist is generated from RepoFiles.txt again,
and createHomerDevRepo is in RepoFiles.

**The lesson worth keeping:** the checker runs on the working folder, so it
passed while the thing people actually download was missing sixteen paths. Check
the archive, not the folder it came from.

## 1.25.0 -- 21 September 2026

Runtime logs record the conversation. **Say.onSpoken** sends every utterance to
the app's log, including those withheld because extra speech was off, so a
runtime log holds what the program said beside what the user pressed. A new
**Evidence for the AI** section in the guide sets out the four records of a
session -- build, release, runtime and the screen reader's speech history -- and
how to gather each.

**_APP_.cmd**, a template: with programs built into exec, typing the program's
name at the top of the project would find nothing. This wrapper runs the fresh
build from there.

## 1.24.0 -- 21 September 2026

**LbcMenuItem**, in Lbc.cs: a menu item that tells the screen reader both its
shortcut and its access letter. A stock item's name leaves out the shortcut;
replacing the name to put it in hides the letter, and the reader falls back to
announcing a first letter that may not work. LbcMenuItem answers both itself.
Use it for every item that runs a command; submenus keep the stock item.

**The tutorial narrator** gains a NarratorPitch setting, in semitones, applied
with ffmpeg after piper speaks so the length does not change. The default is -2
with NarratorScale 0.80: a beta tester with the high-frequency loss that comes
with age found the narrator hard to follow at 0.72 and full pitch.

## 1.23.0 -- 21 September 2026

homerTidy learns the Homer layout, and apps stop writing their own clean-up
scripts. It moves a file the installer takes from exec or help into that folder,
sends stray logs to logs, and never surveys exec or logs. A project's
**LocalFiles.txt** names what belongs on this disk but not in the repository --
the per-app customization that a separate cleanDir used to carry -- and every
line of it is written into .gitignore as never pushed.

Also fixed: two identical files the project names, such as the same script in
two sample folders, are no longer treated as duplicates to remove.

## 1.22.1 -- 21 September 2026

tagRelease joins the logs folder: each run writes
`logs\<App>-release-<date>-<time>.log` instead of overwriting `tagRelease.log` at
the top of the project. Install it with `Tools\installTools`, which copies the
kit's tools to C:\bin.

## 1.22.0 -- 21 September 2026

Development logs join the tree. Every build, clean, tidy, tutorial and audit run
writes its own file in the project's `logs` folder, named as the program names
its runtime logs: `<App>-<task>-yyyyMMdd-HHmmss.log`. One session per file, an
alphabetical sort is a chronological one, and one zip gathers them all. The build
template, homerTidy, buildTutorials, makeTutorials and makeHotkeys all follow it.

## 1.21.0 -- 21 September 2026

The development folder takes the installed shape. Sources and build files stay at
the top with ReadMe and License; programs are built into `exec`, documents live
in `help`, tooling in `scripts`. A clean-up script that predates the layout moved
DbDo's `scripts` folder as obsolete, since Windows treats Scripts and scripts as
one name -- the guide now says so.

Also recorded: why Homer menus are long and flat, when a submenu earns its place,
the function-key families, the two rules for letters with the X, Un- and Z
exceptions, and the Hotkeys.md format.

## 1.20.0 -- 20 September 2026

A demo script declares its own terms.

The tutorial .inix gains a `[global]` first section: the voices, their speeds,
the screen reader's flatness, the silence before the first word and between
passages, and where the engines are when they are somewhere unusual. Script 00
sets the series defaults and any later script can override them for itself.

That also gives the file kind a name. An .inix whose sections are speech
passages is a **demo script**, and it says so: `FileTask = demo`, the way report
and accept files declare themselves.

## 1.19.0 -- 20 September 2026

Spoken tutorials become a kit capability.

DbDo grew a set of simulated walkthroughs -- a narrator and a screen reader,
built from text files -- and the tooling was app-specific by accident rather
than by design. It is in the kit now: `buildTutorials` and `makeTutorials` in
Tools, a starter script in Templates, and a section in the guide covering the
format, the tools, the voices and what may be published.

Two things in that section are worth stating on their own.

**The voices are chosen by licence first.** Most of piper's best-known English
voices cannot be redistributed -- lessac is Blizzard 2013, research only; ryan
and the hfc pair are CC BY-NC-SA; libritts_r is fine-tuned from lessac. The kit
installs kristin and john, both trained on public domain recordings, so the
audio an app publishes is free of restrictions.

**Say the word the key comes from.** Now a universal guideline rather than a
tutorial habit: wherever a key is introduced, name the word its letter comes
from. A key whose mnemonic goes unsaid is one somebody has to memorise rather
than understand, and the association is why that key was chosen.

The same rule governs HEADINGS, which is where it is easiest to miss. A section
called "Sorting" teaches the wrong letter, because the command is Order and the
key is O. The test is simple: if the heading were the only thing somebody
remembered, which key would they press?

sayTutorial, which spoke a single script in two SAPI voices, is replaced by
buildTutorials, which does that and everything after it.


## 1.18.0 -- 19 September 2026

A script that shells out to an installer says where the window went.

`buildTutorials` in DbDo appeared to hang while fetching a voice. It was not
hung: a User Account Control prompt had opened behind everything, without taking
focus, and was waiting for an answer nobody knew it had asked for. A sighted
user gets a taskbar flash; a screen reader user gets silence.

So the kit's installer scripts now say, before they start, that Windows may ask
for permission in a window behind this one, and that Alt+Tab finds it. Where the
wait can be watched -- `consent.exe` is the prompt itself -- a script can say
"Windows is asking for permission now" the moment it appears, and give the wait
a time limit so an answer that never comes ends in a sentence rather than a
hang. The guide says all three.


## 1.17.0 -- 19 September 2026

Everything DbDo's installer taught this week, folded back in.

### The destination page

`DisableDirPage=auto` with `UsePreviousAppDir=yes`. A reinstall or an update now
asks nothing and goes where the last one went; a first install still chooses.
HomerScribe already did this and the template did not.

### Probe quoting, which cost three releases

`cmd /c` strips the first and last quote of what follows it, so a probe
beginning with a quoted path -- `"C:\...\ollama.exe" --version` -- lost its
opening quote and ran nothing. Empty output read as "not installed", and an
installer kept offering to install a tool that was already there. The whole
command is now wrapped in one more pair of quotes.

### Detect by looking, not by running

The file and the uninstall registry key are checked first: no process, no
quoting, no PATH, and an elevated installer still sees them. The tool is run
only to learn its version, never to learn whether it exists. Ollama installs per
user, into a profile an elevated installer's PATH cannot reach, which is what
made this the failure it was.

### Three entries per component, with versions in the label

One entry per state -- install, update, already current -- grouped so the ones
that do something come first, only one ever shown. The label carries the
versions and nothing else:

    Install Ollama 0.34.1
    Update Ollama from 0.33.0 to 0.34.1
    Reinstall Ollama 0.34.1 (current version)

A purpose clause belongs only in the fallback, where no version is known. The
launch and guide entries keep the words the other apps use, name and key
substituted and nothing more.

### The Results box is not a checkbox

It always runs and it must run last, so it is started from code in
`DeinitializeSetup` rather than listed on the finish page. A launch checkbox
leaves a marker instead of starting the program, and the summary starts it once
the box has been closed.

### Every probe is logged

Command, exit code, output. Three rounds went into finding a fault that one
logged probe would have shown at once.


## 1.16.0 -- 19 September 2026

Finish-page checkboxes that look before they offer.

DbDo's installer offered to install Ollama on a machine that already had it.
The guideline said what the finish page should contain and not that a checkbox
must first ask the machine, so the template did not either.

Both now do. `ollamaState` asks winget, then looks for the per-user copy at
`%LOCALAPPDATA%\Programs\Ollama\ollama.exe`, and caches the answer: 0 not
installed, 1 out of date, 2 current. `ollamaNeedsInstall` and `ollamaIsPresent`
gate the entries, and `descOllama` writes the label -- install, update, or
reinstall -- so the checkbox says what it would actually do. The pattern is
EdSharp's `devToolState`, at the scale a smaller app needs.

The guide also now states what was previously only in the template: the last
checkbox runs `homerFinish.cmd` rather than the program, because Inno runs the
entries in order and a program started last puts its window over whatever the
other entries were still saying. And it says what the Results box should hold:
the program and where it is, one line per ticked checkbox, and the log's
location. Nothing about a step that did not run.


## 1.15.0 -- 19 September 2026

`jobs` became `scripts`, and `samples` folded into `templates`.

The folder layout is now, in the installed tree: `configs`, `data`, `exec`,
`help`, `scripts`, `templates`. In the per-user tree: `configs`, `data`, `logs`,
`results`, `scripts`, `temp`. Every initial is still distinct in each listing,
and `temp` and `templates` still never appear together.

**`jobs` became `scripts`** because the word arrived from mainframe batch
processing and everybody now says scripts. Same letter, better word. `Paths.jobs`
is `Paths.scripts`, `shippedJobs` is `shippedScripts`, and the MDI frame's
command is **Run a Script on Alt+Shift+S**, where it used to be Run a Job on
Alt+Shift+J.

**`samples` folded into `templates`.** A template that shows what is possible is
a sample with a purpose. The alternatives collided: `examples` wants e, which is
`exec`, and `demos` wants d, which is `data`. The installer template ships one
folder now, with a comment saying why.

DbDo needs no change for this: it already keeps its scripts in `Scripts\`.


## 1.14.1 -- 19 September 2026

The build template fetches what it needs.

Reviewing DbDo's build against the kit's own showed that the kit was not
following its own rule in two places. A build script asks the web for what it
needs rather than asking the person, and the template said "Inno Setup was not
found. To produce the installer, open the .iss and click Compile" -- which is a
manual step -- and left pandoc to the same fate.

Both are now installed with winget when they are missing. A missing Inno Setup
after that attempt fails the build rather than quietly skipping the installer,
because the installer is part of a release. And an ISCC that returns 0 without
writing the .exe now fails too.


## 1.14.0 -- 19 September 2026

A module can need an assembly, and now it says so.

DbDo's first build against the kit failed with four copies of

    error CS0246: The type or namespace name 'ZipArchive' could not be found

in `Inix.cs`. Nothing was wrong with `Inix.cs`: reading and writing .xlsx means
reading and writing a zip archive, csc does not resolve `System.IO.Compression`
from csc.rsp, and DbDo's build script did not pass it. The kit's own template
always had, which is why the samples never showed it.

That is the same class of fault as `Mdi.cs` needing `KeyMap.cs`, one level
lower, and nastier: a missing module reports a missing NAME and points at the
build script, while a missing assembly reports a missing TYPE and points at the
module.

So a module now declares both:

    // REQUIRES: KeyMap.cs, Lbc.cs, Log.cs, Paths.cs, Say.cs, Util.cs.
    // ASSEMBLIES: System.IO.Compression.dll, System.IO.Compression.FileSystem.dll.

`Inix.cs`, `Say.cs` and `Web.cs` carry ASSEMBLIES lines, and `checkHomerDev`
reads every build script -- the samples', the templates', and any other it is
pointed at -- for one that compiles a module without the references it names.


## 1.13.5 -- 19 September 2026

`Announce.md` carries the facts a reader asks for first.

Jamal's own explanation of the project, written after the first posting, added
what the draft had left out: that the project consolidates decades of screen
reader oriented development under Windows; that the classes come in equivalent
C# and Python versions, the C# for .NET Framework 4.8 which builds on any modern
Windows and the Python for any recent version; that the functionality covers
layout by code, standard dialogs, and components that help a screen reader user
work with AI assistance or by hand; and that template files help with a build
script and an Inno Setup installer.

All of that is now in the announcement, in the places where a reader would look
for it, and the piece is still one posting at about 2,800 characters.


## 1.13.4 -- 19 September 2026

`Announce.md` leads with what somebody gets.

The previous version listed what the kit contains and left the reader to work out
why that mattered. It now opens with the benefit -- building a small Windows tool
of your own should not require first discovering, by trial and error, what makes
a program work well with a screen reader -- and the features appear underneath as
what makes that possible.

It also follows the form of the other Homer announcements: a title and subtitle,
the date, the licence, the link, and plain paragraphs. One piece of content, 2,581
characters, which fits a LinkedIn post, a Facebook post, or an email as it
stands.


## 1.13.3 -- 19 September 2026

`Announce.md` is one announcement.

It held three versions and a page of notes about character limits and editorial
intent. None of that belongs in a document whose job is to be posted. The file is
now a single piece of content, 2,241 characters of body, which fits LinkedIn's
3,000-character cap, fits Facebook, and reads as an email.

It opens with what the kit is, then says what it is built on, then the features,
then the checks, then the samples, the licence and the link. No headings about
where to paste it and no commentary about itself.


## 1.13.2 -- 19 September 2026

The announcements say what this actually is.

### All four programs built at 1.13.1

FruitBasketCs, FruitBasketMdiCs, FruitBasketMdiPy and FruitBasketPy each
produced their executable, and the kit audit found 0 problems.

### Announce.md, rewritten around the honest claim

The three posts now say the true thing rather than the impressive one: this is
about twenty years of learning consolidated into one place, with AI making the
consolidation practical, so that somebody else can start from foundations that
work rather than from a blank file.

Both halves of that are stated plainly. The knowledge is not new and the posts
do not pretend it is. The consolidation is what is new -- gathering decisions
scattered across a dozen programs, writing down why each is what it is, and
checking that they still hold is work that was always worth doing and never
quite got done -- and it is honest to say that AI is what made it affordable.

The posts also say that the kit covers both shapes these tools take: a graphical
window, or a command line with the same settings and the same log.

The file now opens with what the announcements deliberately avoid: no claim to be
first, no promise about what somebody will build, no number that cannot be
checked.

Lengths are measured rather than estimated: the short post is about 1,600
characters, the standard post about 2,500, and the email version longer because
email has no limit.


## 1.13.1 -- 19 September 2026

One command for the whole release.

### All four samples built at 1.13.0

`buildHomerDev` converted the documents, built FruitBasketCs, FruitBasketMdiCs,
FruitBasketMdiPy and FruitBasketPy, and found 0 problems.

### releaseHomerDev

    releaseHomerDev "What changed."

Four steps, stopping at the first failure: `installTools` puts the kit's current
tools on the PATH so an old `tagRelease` cannot refuse the release;
`checkHomerDev` records the environment, builds everything from clean, checks the
dependency rule and the tools on the PATH, and drives every program through its
keys with uiCheck; `gitPush` commits and pushes what the whitelist allows; and
`gitRelease` tags and publishes.

Nothing in it is a test somebody has to remember. What it cannot do is read the
third list of its own evidence report -- what remains uncertain -- and that is
the one thing to do before announcing.

`gitRelease` now prefers `checkHomerDev` when the folder has one, so releasing
the kit runs the kit's own check rather than the per-app one.


## 1.13.0 -- 19 September 2026

The keys are now pressed by a script.

### uiCheck

    uiCheck                    every uiTest.inix beside the script
    uiCheck --path C:\JobDo    an app's own tests

It starts a real program, sends keystrokes, and reads back the Windows UI
Automation tree -- the same interface a screen reader uses to find out what is
on the screen. A control with no accessible name is invisible to both, so a
check that finds nothing has found something real.

Tests live beside the program in `uiTest.inix`: `Run` names the program, then
each `[step]` has `Keys` to send, `Wants` for a string that must appear in the
tree, `Title` for a window that must exist, and `Escape` to close what the step
opened. pywinauto does the driving and installs itself on first run.

`Samples\uiTest.inix` drives all four samples, including every key an MDI app
gets free: Control+N for a second window, F4 for the window list, Alt+Shift+J
for the job list, Alt+Shift+C for the settings list, Alt+F1 for about.

This replaces the last instruction in this project that said "open it and press
the keys". A check a person has to remember is a check that stops happening in
the week it matters.

### checkHomerDev checks the machine too

Two additions, both from faults that actually happened:

- **The environment is recorded** -- which Python and which pandoc the run
  actually used -- so a report says what it was produced with.
- **Every tool on your PATH is compared with the kit's copy.** A release failed
  on a `tagRelease` from before source-only releases were supported, and nothing
  could see it, because the kit only inspected itself. When the check reports a
  stale tool, `Tools\installTools` fixes it.

`checkHomerDev` now runs uiCheck as its last step, so one command builds
everything from clean and then drives it.

### What is still not automated

Speech. UI Automation reports that a control exists and what it is called, not
what JAWS said. NVDA can log what it speaks at debug level, so a future check
could run a scripted session and read that log back. It is written down as the
next step rather than claimed as done, and every report says so.


## 1.12.1 -- 19 September 2026

Everything builds; the release itself needed one more script.

### All four samples built, and the kit audited clean

`buildHomerDev` converted the documents, built FruitBasketCs, FruitBasketMdiCs,
FruitBasketMdiPy and FruitBasketPy, and found 0 problems. That is the first run
where the whole kit -- three shapes, two languages, one command -- came through
in one pass.

### tagRelease failed, and it was not tagRelease

    Could not find HomerDev_setup.iss in C:\HomerDev

That is a `tagRelease` from before source-only releases were supported. The kit
has carried the fixed one since 1.1, in `Tools`, but the copy that runs is the
one on the PATH, and nothing had ever updated it.

`Tools\installTools.cmd` does that now. It copies checkHomerApp, gitPush,
gitRelease, homerTidy, sayTutorial and tagRelease to a folder on the PATH --
`C:\bin` unless another is named -- and says plainly if that folder is not on
the PATH. Run it after updating the kit.

The lesson generalizes: a tool that acts on the current directory is meant to
have one copy, and one copy means one copy that can go stale. `Developer.md` now
opens with the release sequence, `installTools` included.

### Smaller things

- The migration list covers the MDI sample's rename, so the old
  `FruitBasketMdi.exe` and its log go on the next build.
- The tutorial playlist no longer implies the two planned episodes are written.
  They are not.


## 1.12.0 -- 19 September 2026

The MDI shape in both languages, two lists that matter, and an FAQ.

### FruitBasketMdiCs and FruitBasketMdiPy

The MDI sample is now a pair, like the single-dialog one. `homer\mdi.py` is the
Python side of `Mdi.cs`: same command names, same keys, same title rule, same
menus. So the claim the kit makes -- one behaviour, either language -- now holds
for all three shapes rather than two.

One honest note, which is in the file as well: `lbc.Dialog` builds a dialog, and
a wx dialog cannot be an MDI child, so the band layout in `mdi.py` is written
again rather than reused. Everything that makes a control accessible IS reused.
Lifting lbc's building methods into a mixin that a dialog and a panel can share
is the next refactor, and it has not been done.

### One command builds everything

`buildHomerDev` now converts the documents, **builds all four samples**, and
audits the kit. Somebody who changes a shared class should not have to remember
four build scripts; a problem anywhere surfaces from the one thing they already
run. Each sample still writes its own log beside itself, and a failure is named
on screen with the log that holds the compiler output.

`checkHomerDev` is unchanged in purpose and now covers all four: it cleans
first, checks the module dependency rule, and writes the evidence report.

### Run a Job, and Change a Setting

Every MDI app now gets two more commands free:

    Alt+Shift+J    run a job: a list of the scripts in the jobs folder
    Alt+Shift+C    change a setting: a list of what this program lets you change

Both are lists, and `HomerDev.md` says at length why. Briefly: without sight, a
folder is a sequence to be heard and a typed path is a spelling test, while a
list is reached by one key and narrowed by first letter. The job list is read
fresh every time, so dropping a script into the folder makes it available with
nothing to register. The user's own jobs live in the per-user tree, where an
update cannot overwrite them, and appear above the shipped ones.

Settings are declared by the app with `addSetting`, changed through one field,
saved the moment they are answered, and handed back to the app through
`onSettingChanged` so they take effect at once. No file to edit by hand, no
twenty-control preferences dialog, no restart.

### FAQ.md

A new standard document, in `help` with the others. It answers the question that
comes first from outside the Windows world -- why not Mac -- plainly: this kit
is built on decades of Windows screen reader experience and exists to make that
experience as good as it can be; that depth is missing for other platforms, and
writing conventions I had not lived with would produce confident guidance that
turned out to be wrong. The code is MIT licensed and developers on those
platforms are welcome to it.

The full document set is now `ReadMe.md` and `License.md` at the top, and in
`help`: `<App>.md`, `Announce.md`, `Developer.md`, `FAQ.md`, `History.md`,
`Hotkeys.md` and `Tutorials.md`.


## 1.11.0 -- 19 September 2026

Ready for a first public release.

### The documents now say what the kit does

A full pass over every document against the actual contents of the folder. What
had drifted:

- The kit has **twelve** C# modules, not nine. Inix, KeyMap, KeyName, Lbc, Log,
  Mdi, Paths, PdfRead, Say, Util, Web and inixVert.
- The Python side has **seven** modules -- inix, lbc, log, paths, say, util and
  web -- plus the package file and the version file the build writes.
- There are **three** samples, not two.
- `Style\` no longer exists; its files are in `help`. Three documents still
  pointed at the old path.
- `Developer.md` carried the folder tree from three layouts ago.
- `Hotkeys.md` had no section for the MDI frame's keys, which every
  multiple-document app gets for free.

### Announce.md is now three announcements, each already the right length

The Word document made from `Announce.md` was always far too long to paste into
a post, which is the wrong way round: the document should hold posts that are
ready to use.

It now holds three, with their character counts measured rather than estimated:

- **the short post, about 1,700 characters** -- fits anywhere, including a
  mailing list digest or a forum with a tight limit
- **the standard post, about 2,200 characters** -- for LinkedIn and Facebook
- **the email version** -- longer, plain text, with a subject line

LinkedIn caps a post at 3,000 characters including spaces, which its own help
page states, and that is the only limit that rejects a post outright. Facebook's
is far larger. The limit that decides whether anybody reads it is smaller than
either: roughly the first 140 to 210 characters are shown before a "see more"
link, so both posts are written to carry their point in the first two sentences.

The file also says what the announcements deliberately avoid: no claim to be the
first anything, no promise about what somebody will be able to build, and no
number that cannot be checked.


## 1.10.1 -- 19 September 2026

The build now clears up after a move.

### All three samples built at 1.10.0

FruitBasketCs, FruitBasketMdi and FruitBasketPy each produced their program
again, so moving the documents disturbed nothing that compiles.

### Twenty documents, when there are twelve

The 1.10.0 run converted 20 documents instead of 12. Unarchiving over an
existing folder adds and replaces; it never deletes. So every document that
moved into `help` was still sitting at the old path as well, and `Style` was
still there beside it. Two files with the same name and different contents is
worse than either alone.

The previous release answered that with a sentence telling the user to delete
the old copies. That was the wrong kind of answer, and it broke a standing rule
of this kit: ship a script that makes the change, not a step for somebody to
carry out.

`buildHomerDev` now does it. It carries a list of pairs -- where a file used to
be, and where it is now -- and removes the old copy when, and only when, the new
one is already in place. The same list clears the folders an earlier layout
left empty: `Style`, `Python\homer`, and the three per-sample folders from
before the samples were flattened. It is logged file by file and summarized in
one line on screen.

Every move the kit has made is in that list, back to `Keys.cs` becoming
`KeyName.cs`, so a machine carrying any earlier version tidies itself on the
next build.


## 1.10.0 -- 19 September 2026

A place for the documents, and two scripts for releasing.

### help, the tenth folder

`help` joins the layout, at the same level as configs, data, exec, jobs, logs,
results, samples, temp and templates. Its letter, h, was free, and it holds every
document -- the guide, `Tutorials.md`, `History.md`, `Hotkeys.md`, `Announce.md`,
`Developer.md`, the style guides and the tutorial scripts -- in both `.md` and
`.htm`.

`ReadMe` and `License` stay at the top of the project. That is not sentiment: it
is what GitHub recognizes, and it is where a person opening the folder for the
first time looks.

**Why not `docs`, which is the GitHub convention?** Because `d` is `data` here,
and the letters are the point of the layout. What that costs is one feature:
GitHub Pages published from a `/docs` folder. Homer apps are listed from the
separate HomerTools site instead, so nothing is actually given up. README
recognition is unaffected, since the ReadMe stays at the root. Community health
files, if a project ever wants them, go in `.github`, which GitHub also
recognizes and which leaves the letters alone.

### Tutorials.md and Announce.md join the standard set

The full documentation set is now: `ReadMe.md` and `License.md` at the top, and
in `help`: `<App>.md`, `Announce.md`, `Developer.md`, `History.md`,
`Hotkeys.md` and `Tutorials.md`. Every one has a matching `.htm`, and
`checkHomerApp` checks for all of them in their right place.

`Tutorials.md` holds nine worked scenarios -- starting an app, adding a field,
finding out what a key does, turning one window into many, reading a log,
writing acceptance criteria, changing a shared class, releasing, and asking an
AI for a Homer app -- plus the audio tutorial playlist and how to record more.

### gitPush and gitRelease

Both from the versions in daily use, with three changes. `gitPush` takes the
commit message as an argument instead of always saying "Fix.", refuses to run
outside a git repository rather than creating one by accident, and writes a log.
`gitRelease` runs `checkHomerApp --build` first and stops if anything failed,
because a release is the one moment where a fault costs somebody else time
rather than you. `--skip-check` is there for when you already know.

Both stage only what the whitelist allows, so `git add -A` means "everything the
project has named" rather than "everything in the folder".

### Every file, listed

`HomerDev.md` gained a manifest: every file in the kit with one line saying why
it is there, grouped by folder. A file you have not seen before can now be
looked up rather than guessed at.


## 1.9.0 -- 19 September 2026

The kit can now check itself with a compiler.

### All three samples built at 1.8.1

FruitBasketCs, FruitBasketMdi and FruitBasketPy each produced their program.
The MDI one is the news: it is the first real exercise of the adopting
constructor added to `LbcDialog`, so an MDI child laid out by the same builder
as a dialog now has a compiler's word for it.

### checkHomerDev

    checkHomerDev
    checkHomerDev --deep
    checkHomerDev --no-clean

It runs the kit audit, checks the module dependency rule, deletes what previous
builds wrote, builds all three samples with their own scripts, and writes
`evidence-kit-<yyyymmdd-hhmmss>.md` beside itself. Exit code 1 when anything
failed, so a release script can act on it.

The cleaning is the part that makes the answer mean something. A build that is
not run still leaves yesterday's executable in the folder, and an existence
check would call that a pass.

**The dependency check is new and general.** Every module may declare what it
needs in a `// REQUIRES:` line, and the check reads every build script -- the
samples' and the templates' -- for a script that includes a module without one
of its requirements, ignoring commented lines, since a commented module is one
deliberately left out. Today `Mdi.cs` is the only module with a REQUIRES line.
The check exists because that was not true a release ago.

**Why it exists, in three failures.** 1.5.0 shipped a class-name collision that
stopped `Lbc.cs` compiling. 1.6.0 shipped a build script that treated a missing
`version.txt` as fatal after the samples' were removed. 1.8.0 shipped `Mdi.cs`
without `KeyMap.cs` beside it. Every check in the kit read files; none compiled
anything; a user found all three. A compiler is the only instrument that answers
"does this still work."

**What it does not do**, and says so in every report: it does not run the
programs. All three samples are windowed, and a check that needs a person to
close a window is not a check. What a screen reader says is still for a person
to hear, and the report's uncertain list names that first.


## 1.8.1 -- 19 September 2026

Three faults from the first run of 1.8.0, and one of them is a new kind.

### The MDI sample would not compile

    Mdi.cs(137,13): error CS0103: The name 'KeyMap' does not exist in the current context

Nine times over. `Mdi.cs` registers every command with `KeyMap` as it is added,
and `KeyMap.cs` was commented out in the build script, as it has been in every
Homer build script since the switches were written.

This is a kind of fault the kit had not had before: **a shared module that needs
another shared module**. The module list was written as though every file were
independent, and until MDI arrived every file was. Three changes:

- `Mdi.cs` now states what it requires at the top, where a reader looks.
- The build template pairs KeyMap and Mdi under one comment, since turning on one
  without the other cannot work.
- The MDI sample's build script switches both on.

`Mdi.cs` and `KeyMap.cs` are the only pair in the kit. Everything else is
independent, and the comment in the template says so, so nobody hunts for
dependencies that are not there.

### The C# and Python samples both built and ran

FruitBasketCs and FruitBasketPy each produced their program on the first try at
1.8.0, which means the adopting-constructor change to `LbcDialog` did not disturb
ordinary dialogs. The MDI sample is still the real test of that seam.

### The kit check audited files the build had written

`Version.cs` and `version.py` are generated on every build and are already in the
never-pushed list, so their encoding says nothing about the kit. Both the kit
check and `checkHomerApp` now skip them.


## 1.8.0 -- 19 September 2026

MDI, and the three shapes named.

### Mdi.cs

`MdiFrame` and `MdiChild` carry the frame of a multiple-document app, so
EdSharp, FileDir and DbDo can share one implementation instead of three that
drift. Free with the frame: the window picker on F4, the spoken window list on
Shift+F4, next and previous, close and close-others, the alternate menu on
Alt+F10, the key describer on Control+F1, about on Alt+F1 and the guide on F1.
Commands are named sentences rather than control ids, registered with KeyMap as
they are added, so the menu, the alternate menu, the key describer and the
hotkey document cannot disagree.

The design is the Homer.NET MDI fruit basket of 2010 -- LbcMdiApp, LbcMdiFrame,
LbcMdiChild, a menu declared by name and key, focus tips, a window picker, an
alternate menu, a key describer. That program was right about the shape; this is
the same shape with today's classes under it.

The title rule is enforced rather than documented: the frame carries the app
name, a child carries its subject, and `setTitle` is the only way to set one.

### LbcDialog can adopt a form

A dialog and an MDI child differ in how they are shown, not in how they are laid
out. `LbcDialog` now takes an optional existing form and builds into it, so a
child gets add-order focus, the status line, the list search, the line chords
and the access keys from the same code a dialog uses. An adopted form is
finished with `layoutIntoForm`, which sizes it and sets the opening focus
without showing anything, because the frame shows the child.

### FruitBasketMdi.cs

The third sample. It does not repeat the nine decisions -- FruitBasketCs still
carries those -- and marks only what changes when a program holds several things
at once: the title rule, commands as sentences, what the frame gives free, state
per window, and closing the last window closing the program.

### The guide names the three shapes

A single tool with a command line and a dialog; a desktop-only program whose
dependencies decided that; and a multiple-document program. The consistent flags
for the first are written down -- `--help`, `--gui`, `--version`, `--log`, and an
unknown switch refused rather than ignored -- and so is the list of everything
all three share, which is nearly all of it.


## 1.7.0 -- 19 September 2026

The kit learnt to produce evidence.

### checkHomerApp

    checkHomerApp
    checkHomerApp --build
    checkHomerApp --path C:\JobDo

Eleven checks, each recorded with the command that ran it and the exit code it
returned: the document set and its HTML, encodings, zero-byte files, the
version's single source of truth, the publishing whitelist, whether the program
opens a log, accessible names that repeat a caption, reserved key combinations
and access keys claimed twice, the build, a smoke run of `--help`, and the app's
own acceptance criteria. It writes `evidence-<yyyymmdd-hhmmss>.md` and exits 1
when something failed, so a script can act on it.

The report says three things, and the third is the point: what was verified,
what was not checked, and what remains uncertain. A skip is never counted as a
pass. The uncertain list is printed every time, because a report claiming
everything is fine is worth nothing.

Two rules are built in, both learned on its first run. It ignores the kit's own
modules, since a shared class sets accessible names and names key combinations
on purpose, and it ignores comment lines, since a comment explaining that
Alt+Control is reserved is the rule rather than a breach of it. A checker that
cries wolf teaches people to ignore it.

On that first run it found a real fault: both fruit basket samples had given the
access key S to two controls at once. Fixed -- the speaking check is now
"Spea&k each change".

### accept.inix

What "done" means, written before the code is:

    [check]
    Name   = the help text names every switch
    Run    = JobDo.exe --help
    Expect = 0
    Wants  = --source

Four fields and no more, because the point is that criteria get written.
`Templates\accept.inix` starts a new app off; `Samples\accept.inix` checks that
both fruit baskets build and produce their programs.

### The guide gained two parts

"Evidence, and checking without sight" explains the instrument and the three
lists. The AI-assisted coding part gained "the method, in four moves" --
specify, build in small recoverable steps, verify, package and defend -- with
what in the kit carries each.


## 1.6.1 -- 19 September 2026

Two faults from the first run of 1.6.0, both mine.

### A missing version.txt stopped the build

Flattening the samples in 1.5.0 removed their `version.txt` files, on the
grounds that a sample is never released and so has no number to step. The build
script still treated a missing one as fatal, and both samples failed at the
first line that mattered:

    ERROR: version.txt not found.

A build needs a number whatever else is true -- the program reports it, the
installer carries it, the release tag is it. So a missing `version.txt` is now
created holding 1.0.0 and the build carries on, in both templates and both
samples. Stopping there left a manual step, which no Homer build does.

### The kit check walked into a virtual environment

`buildHomerDev` audits every text file in the kit. The Python sample's build had
left a `.venv` beside it holding the whole of PyInstaller, so the check dutifully
audited several thousand files that belong to somebody else and wrote 611 KB of
complaints about their line endings.

Two changes. The check and `homerTidy` now skip the folders a build makes --
`.git`, `.venv`, `__pycache__`, `build`, `dist`, `notes`, `venv` -- and those
folders join the never-pushed list. And the console now shows the first twenty
problems and says how many more there are, with every one of them in the log. A
console that scrolls for a minute tells a screen reader user nothing at all.

### Also

The Homer module list in the C# build template is now in lowercase alphabetical
order, which it had drifted out of when KeyName was renamed.


## 1.6.0 -- 19 September 2026

A folder layout whose initials are all different.

### The nine folders

`configs`, `data`, `exec`, `jobs`, `logs`, `results`, `samples`, `temp`,
`templates`. Nine folders, nine different first letters, because a screen reader
user reaches a folder by typing its initial and duplicated initials turn one
keystroke into several.

`temp` and `templates` both begin with t and never appear together: `temp`
exists only in the per-user tree, `templates` only in the installed tree. That
is where each belongs anyway -- a temp folder under Program Files cannot be
written to, and templates are shipped and read-only -- so no folder needed an
unobvious name, and the rule that makes it hold is simply that temp always lives
in the per-user tree, portable copies included.

### Paths.cs and homer/paths.py

New, and parallel: the two trees, the nine folders, and three things every app
was writing for itself.

- `configFile` hands back the user's copy of a settings file, making it from the
  shipped one the first time it is asked, so an update never overwrites a
  change somebody made.
- `clearTemp` empties the temp folder at startup. Whatever it finds is what a
  previous run could not clean up after itself.
- `tempFile` names a scratch file nothing else is using.

`Log` now asks `Paths` for its folder, so one class decides the layout.

### The installer lays the tree down

`[Dirs]` creates the six shipped folders, and the files go where they belong:
the executable and the DLLs in `exec`, the shipped `.inix` in `configs`, seed
data in `data`, scripts and the screen reader packages in `jobs`, and `samples`
and `templates` as shipped. The documents stay at the root of the installed
tree, where somebody looking for the ReadMe expects them.

One consequence to plan for: `{app}\<App>.exe` became `{app}\exec\<App>.exe`.
Shortcuts, the uninstall icon and the finish helper were all updated, but an app
adopting this layout should be reinstalled rather than updated in place the
first time.


## 1.5.0 -- 18 September 2026

A failed build, a flatter tree, and a tutorial.

### The C# build failed, and the cause was a name

The first real build of FruitBasketCs against the kit stopped with

    Lbc.cs(368,60): error CS0721: 'Keys': static types cannot be used as parameters
    Lbc.cs(368,29): error CS0115: 'LbcForm.ProcessCmdKey(ref Message, Keys)':
                    no suitable method found to override

Homer's key-name class was called `Keys`, and so is the WinForms enum that
`ProcessCmdKey` takes. In one namespace the static class wins the lookup, the
override no longer matches, and an app writing `Keys.Delete` gets an ambiguity
error as well. The class is now **KeyName**, in `CSharp\KeyName.cs`, and the
file says at the top what the old name cost. Nothing else calls it yet, so
nothing else breaks.

The Python build succeeded on the first try and produced FruitBasketPy.exe.

### A flatter tree

Two folder levels went, because navigating them by screen reader is slower than
reading a longer list:

- `Python\homer\` became `homer\`. A Python app now puts the kit itself on the
  path rather than a subfolder of it.
- `Samples\FruitBasketCs\` and `Samples\FruitBasketPy\` became a flat
  `Samples\` holding four files. The samples' `version.txt` files went with
  them: a sample is never released, so it never had a version to step.

Nothing is deeper than two levels now. Every build script, document and check
was repointed.

### The tutorial

`Tutorial_HomerDev.inix` is a spoken walkthrough in the step format the existing
makeTutorial.py already reads: `Say` for the narration, `Key` for the keystroke,
`Hear` for what the screen reader answers, `Note` for the written version. It
covers what the kit is, unarchiving it into `C:\HomerDev`, running
`buildHomerDev`, building and running both fruit baskets, and the point the
whole thing exists to make -- that the two behave the same because the behaviour
lives in the components rather than in either program.

`Tools\sayTutorial.cmd` and `.py` render it to audio in **two voices**: the
narration in one, the screen reader's answers in another, because a listener who
cannot see the screen has no other way to tell the teacher from the machine.
Windows' own voices do the speaking through System.Speech, so nothing is
installed and nothing is uploaded. One .wav per line, kept, and one .mp3 when
ffmpeg is present.


## 1.4.0 -- 18 September 2026

Logging, publishing, and a notebook.

### Every program and every installer keeps a log

`CSharp\Log.cs` and `homer\log.py` are the same class in two languages:
same file name, same folder, same header block, same method names -- start,
close, line, info, warn, error, section, keyValue, command, exception, prune,
show. Both were taken from the two implementations that already worked and had
converged separately, HomerScribe's C# session log and HomerView's Python
logger.

    %LOCALAPPDATA%\<App>\logs\<App>-<yyyymmdd-hhmmss>.log        one per run
    %LOCALAPPDATA%\<App>\logs\<App>-setup-<yyyymmdd-hhmmss>.log  one per install

One file per session, named for when the session began, with the most recent
thirty kept. The header block records the version, the program, the working
directory, the command line, the Windows build, the user, the machine and, in
C#, which screen reader Say can reach.

The installer template now sets `SetupLogging=yes` and copies Inno's own log
into the same folder at ssDone, after the final-page checkboxes have run. The
one caveat -- an elevated installer writes to the elevating account's profile --
is documented where it happens rather than left to be discovered.

Logging is deliberately not optional. When it becomes so, the switch goes inside
the class rather than into every caller.

### .gitignore became a whitelist

`RepoFiles.txt` names what the repository carries, and `homerTidy --gitignore`
turns it into a `.gitignore` that ignores everything and puts back exactly what
was named. A file dropped into the folder is invisible to git until somebody
names it.

This replaces a habit rather than codifying one, so it is worth saying why: a
list of exclusions is only ever as complete as the last time somebody remembered
to add a line, and the tidy scripts existed because things got pushed that should
not have. A blacklist cannot fix that class of problem.

A never-pushed list overrides the whitelist for private and generated files:
self.md, self.htm, tagRelease, create<App>Repo, every .log, notes\, Version.cs,
version.py, __pycache__\ and the build products.

### self.md

A new Homer convention: a dated, headed notebook in every project, never
published. It holds decisions with their rejected alternatives, findings, and
honest open items -- the things History.md cannot hold because History.md is
public and is about releases.

The kit's own `self.md` opens with a report on what a full reading of DbDo,
EdSharp, FileDir, HomerScribe, HomerView, 2htm, extCheck and urlCheck found:
what the apps had already converged on, what they disagreed about, what they got
wrong, and a review of every one of the kit's inclusion decisions against that
evidence. `newHomerApp` writes a starter into each new app.

### Smaller things

- Both samples now open a log first and record what they do, and their headers
  list the keys that arrive free with an Lbc text box and list box: Control+C
  with nothing selected, Control+J to search a list, F3 to repeat, Alt+F8 to
  read all, F8 and Shift+F8 to mark, Control+Enter to accept from anywhere.
- Hotkeys.md gained a list box section; the list-search keys had been missing.
- ReadMe.md's quick start now walks the whole path: install the kit, build and
  run both fruit baskets, try the free keys, read the two side by side, look at
  the log, start an app, publish it.


## 1.3.0 -- 18 September 2026

The two samples were rewritten to be read side by side.

### Twelve blocks, the same in both

Each sample now carries twelve markers of the form `---- BLOCK n: <title> ----`,
with the same numbers and the same titles in each file, and the same function
names throughout: addFruit, basketState, handleButton, saveBasket, settingsPath,
showReport, showState, sortBasket. Somebody with both files open can move
between them by block rather than by searching.

They deliberately do not track line for line. C# needs a class where Python
needs none, and pretending otherwise would teach padding rather than design. The
rule kept instead: nothing appears in one file without a counterpart in the
other, and the counterpart carries the same name.

Three places where the two genuinely differ are commented where they happen: how
each library keeps a dialog open while a button does work, the different shapes
of stringPlural, and the status line that C# has and wx does not.

### More of Lbc, on purpose

The samples now use a combo pick box for the sort order, a check box to turn the
speaking off, a read-only report window, a status line in C# and the window
title in Python, tips on every control, and the list search and line-editing
chords that come free with a list box and a field. More than a fruit basket
needs, which is the point of a sample; the guide now says so plainly, so nobody
reads the sample as a minimum.

### A wart found by making them parallel

`Util.stringPlural` in C# returns the count and the noun together, "3 fruits";
`util.stringPlural` in Python returns only the noun, "fruits". Two functions,
one name, two shapes. Neither was changed here, because the Python one has
callers in HomerView, but both samples now say so where they use it, and the
Python one should take the C# shape the next time that add-on is touched.


## 1.2.0 -- 18 September 2026

The kit became a teaching kit.

### The fruit basket came back

`Samples\FruitBasketCs.cs` and `Samples\FruitBasketPy.py` hold the same program twice:
once on the C# classes, once on the Python package, with `buildFruitBasketCs.cmd`
and `buildFruitBasketPy.cmd` producing `FruitBasketCs.exe` and
`FruitBasketPy.exe`. The Python one is a single file with Python and every
dependency inside it, built with PyInstaller in a virtual environment beside the
script, so it installs on the same terms as a C# program.

The specification is the one from 2005, and the legacy collection of thirty-six
implementations is what it comes from. That collection answered "what does this
language look like". These two answer "what does a program look like when it is
built out of components that already know the conventions", which is the
question a builder working with an AI actually has.

Nine numbered comments in each sample mark the nine decisions a working program
has to get right and an AI will not make unless it is asked: which library, add
order as focus order, bands, access keys, what the screen reader already says,
where the focus goes, counts that match their nouns, saving as the answer is
given, and the escape hatch. The two files number them identically so they can
be read side by side.

### AI-assisted coding, written down

A new part of HomerDev.md explains why the kit prefers that name to vibe coding,
gives the three sentences that carry most of the kit into an AI session, and
sets out a five-step teaching sequence around the samples: ask for the program
cold, read the sample, ask again with the conventions, read the other language,
then change one thing and watch which decisions it touches.

### The build scripts look in three places

Both build templates now find the kit in this order, first hit wins: the
`HomerDev` environment variable, then `C:\HomerDev`, then the current directory.
The third is what lets a sample, a demonstration, or a machine with no kit
installed still build, by carrying its own copy of the folder.

### The templates became opinionated

Every component any Homer app has ever needed is now listed in both build
templates as a switch. The ones used by more than one app are switched on --
configuration file, documentation through pandoc, icon, installer, manifest,
NuGet fetching, screen reader scripts, version stepping -- because that is the
evidence the next app will want them too. The ones used by a single app are
commented out with the app named, so turning one on is one character: exiftool,
ffmpeg, Markdig, NPOI, PdfPig, SQLite, Tesseract, Ude and Whisper on the C# side;
beautifulsoup4, pillow, playwright, pythonnet and requests on the Python side.

A single `:getNuGet` subroutine now does every package fetch, so Markdig, NPOI,
PdfPig, SQLite and Ude are one line each rather than five variations on the same
PowerShell.

### Smaller things

- `newHomerApp <App> --python` writes a Python app: the Python build script in
  place of the C# one, with the rest of the set unchanged.
- Alphabetical order is now a stated convention for every list in Homer code and
  documentation, unless another order is clearly more logical. The module lists,
  the component switches and the option catalogues in this release all follow it.


## 1.1.0 -- 18 September 2026

Everything in this release came from running 1.0.0 for a day and from the logs
of apps the kit had not yet been tried on.

### tagRelease could not release a source-only project

The log said it plainly: "Could not find HomerDev_setup.iss in C:\HomerDev".
The kit ships source and has no installer, and the script treated a missing
setup script as a fatal error rather than as an answer. It now recognizes two
kinds of project. One with an installer is released exactly as before, from the
version stamped into <App>_setup.exe with that installer attached. One without
is released from version.txt, with no asset and no URL check. Nothing on the
installer path changed, so EdSharp, FileDir, DbDo, HomerView and HomerScribe
behave as they always have.

Two smaller changes came with it. A -Path argument aims the script at a repo
without a cd first, and the header now says outright that the script acts on the
current directory, so one copy at C:\bin serves everything. The edition line in
the banner names the kit, so a log says which copy ran.

The version of tagRelease that the kit shipped in 1.0.0 was the older copy from
the EdSharp folder. The base is now the newer one, the copy actually in daily
use.

### cleanDir and tidyRepo became homerTidy

They asked the same question -- does this file belong to the project? -- of two
places, the folder and the repository, which meant two surveys, two plans, and
two chances to disagree. homerTidy asks it once and fixes both in one pass:
empty files deleted, duplicates and unnamed files moved into notes\ under
subfolders named for what they are, tracked files that do not belong untracked
and added to .gitignore under a dated comment, and anything large in the history
reported with the command that would remove it. History is never rewritten
automatically.

What belongs is still decided by the project's own <App>_setup.iss and
RepoFiles.txt, so the script needs no editing. homerPolicy.py is gone: it is
inside homerTidy now.

### The installer template learnt what is already installed

The [Code] section reads the version of any previous install from the app's own
uninstall key. The welcome page says "Install", "Update from X to Y" or
"Reinstall" accordingly, and each component checkbox is now a pair of [Run]
lines gated by a Check: function, so the wording matches the situation instead
of always saying "Install".

Three conventions were settled at the same time:

- A checkbox that installs SCREEN READER scripts or add-ons is CHECKED by
  default. A blind user installing a Homer tool wants them, and a cleared box
  they have to notice is the friction the whole suite exists to remove.
- The last two checkboxes are always documentation, unchecked, then launch,
  checked.
- The launch does not start the program. It runs homerFinish.cmd, which reads
  the setup log, shows one Results box describing what this install actually
  did, and starts the program only once that box is dismissed. Being last, it
  runs after every other checkbox, so the box can report all of them.

installScreenReaderSupport.cmd is new and generic: it unpacks <App>_JAWS.zip
into every JAWS settings folder it finds and hands <App>.nvda-addon to NVDA,
skipping without complaint whichever is absent.

### Smaller things

- version.txt is written without a byte order mark. A batch file's "set /p" and
  Inno's FileRead both take a mark as part of the number, which would have made
  every version wrong by one invisible character.
- The kit carries its own RepoFiles.txt, so homerTidy can tidy the kit.
- homerTidy leaves a project's own script logs where the scripts that write them
  expect to find them, rather than filing them into notes\logs.


## 1.0.0 -- 18 September 2026

First release. The kit was assembled by comparing every duplicated shared file
across DbDo, EdSharp, FileDir, HomerScribe and HomerView, and taking the better
version of each. What that comparison found is recorded here, because the
differences explain why the kit exists.

### Which version won, and why

- **Say.cs** -- byte for byte identical in DbDo, EdSharp and HomerScribe once
  line endings are normalized. The CRLF copy was taken.
- **Web.cs** -- identical in all four apps that carry it. The CRLF copy was
  taken.
- **Inix.cs** -- three generations were in circulation. DbDo and HomerScribe
  carried the original 29 KB codec. EdSharp carried the version that added
  `InixTable`, the converter between .inix, .csv, .tsv, Markdown and .xlsx.
  HomerView carried that plus `InixCodec.readValue`, the single-setting reader
  whose absence had every caller reading the whole file and walking the
  sections itself. HomerView's is a strict superset and was taken, which also
  means DbDo and HomerScribe had been two generations behind.
- **Lbc.cs** -- neither of the two newest copies was a superset of the other, so
  they were merged. EdSharp's is the base: it holds `LbcBandLayout`,
  `LbcBandDialog` and `LbcInixForm`, better access-key handling in the button
  row, the rule that Enter presses the button meaning accept wherever it sits,
  and `sortedIgnoringCase`. HomerScribe's contributed the horizontal band API --
  `addBand`, `endBand`, `bandTarget` and `addButton` -- with all thirteen `add`
  methods rerouted through `bandTarget()` and `addSeparator` closing an open
  band. Without that merge, HomerScribe would not compile against the kit and
  EdSharp would lose its form work.
- **KeyMap.cs, Keys.cs, Util.cs, inixVert.cs, PdfRead.cs** -- one copy each, no
  contest. Keys.cs came from HomerView, the rest from EdSharp and HomerScribe.
- **The Python homer package** -- only HomerView carries it, and it was already
  written to know nothing about HomerView.
- **tagRelease, cleanDir, tidyRepo, homerPolicy** -- these four say in their own
  headers that they are app-independent, and they are: tagRelease takes the app
  name from the directory, and cleanDir and tidyRepo decide what belongs by
  reading the project's own `<App>_setup.iss` and `RepoFiles.txt`. tidyRepo
  still named one app in five strings, and those were replaced with a name taken
  from the folder.
- **The install scripts for Pandoc, the GitHub CLI, Python, Node and Ollama** --
  these read as generic but each writes to its own app's folder and its own
  app's log, so they are not portable files. The pattern is documented in
  HomerDev.md instead, and the kit ships fresh generic `installOllama.cmd` and
  `installModels.cmd` for the local AI case.
- **The build script and the installer script** -- HomerScribe's are the newest
  and most refined of each, and became the templates.

### One behavior deliberately changed in the merge

HomerScribe's Lbc selects the text of the field that opens with the focus, and
extends that to the first focusable control rather than only an explicitly set
one. That was taken, with one change: a **multi-line** box now gets the caret at
position 0 instead of a full selection, because its value is a document rather
than a field and the Homer rule is that the caret opens on the first line. This
is the only place in the kit where the merged file is not simply the union of
what already existed.

### What is new rather than merged

- `buildHomerDev.cmd` and `.py` -- convert the documents and audit the kit:
  components present, encodings right, templates still holding their
  placeholder, no empty files.
- `newHomerApp.cmd` and `.py` -- write a new app folder from the templates.
- `Templates\_APP_.cs` -- a working launchpad app with the standard controls,
  the two message boxes, the matching command line, and settings saved as they
  are answered.
- `Templates\installOllama.cmd` and `installModels.cmd` -- local AI as an
  installer checkbox, now that more than one Homer app uses a model.
- The documentation set.
