---
title: "Homer Tools: Response to the Coordinated App Audit"
lang: en-US
author: "Jamal Mazrui"
---

# Homer Tools: Response to the Coordinated App Audit

This ledger answers each of the 72 findings of the coordinated audit of the Homer apps and kit, as of 14 October 2026. **Done** means the change was made; the entry says how it was tested. Tests marked *here* were run without Windows, on the real code where it is Python and on a line-for-line prototype where it is C#; those marked *on Windows* await a build or a run on the author's machine. **Partly** means some of it was done; **open** means it needs a run on Windows, Office, a clean machine or a screen reader, and no change was made. Each project's History says more about each change.

## 2htm

- **2htm-01, launch marker folder. Done.** The installer creates the log folder before writing its marker; the kit's installer check requires it. Tested on Windows by installation.
- **2htm-02, installer elevation. Done.** The program starts with ExecAsOriginalUser, as in every Homer installer; the installer check requires it.
- **2htm-03, fixed backup name. Done.** Recovery copies get unique names from Homer.Util.recoveryPath.
- **2htm-04, Office deadline. Done.** Each Office call runs on its own thread with a 10-minute deadline, and only processes 2htm started are stopped (kit 1.72.38).
- **2htm-05, accessible HTML as a goal. Open.** A small set of documents with expected headings, table headers, charts and slide order is to be built and checked on Windows, with Office.
- **2htm-06, old kit paths. Done.** The developer guides of 2htm, bookFido, extCheck, FileDir and urlFido, and HomerView's handover notes, now name C:\HomerDev\exec\CSharp; 2htm's guide lists build, tidy, push and release in the order build_release runs them.

## bookFido

- **bookFido-01, friendly names trusted. Done.** bookFido-companions.txt records which book each companion file belongs to, with its address, size and SHA-256.
- **bookFido-02, title identity. Done.** A companion is found by its book, not its title.
- **bookFido-03, PDF magic alone. Done.** A PDF must have its end marker and the length the server gave.
- **bookFido-04, unbounded failure bodies. Done.** The body of a failed reply is bounded while it is read.
- **bookFido-05, redirect credentials. Open.**
- **bookFido-06, BookTrail migration cases. Open.**

## DbDo

- **DbDo-01, missing worksheet. Done.** A named worksheet that is missing is refused; the first sheet is used only when no name was given.
- **DbDo-02, workbook overwrite. Done.** The saved workbook is swapped in whole.
- **DbDo-03, delimited save. Done.** The save is staged, and the files before it are kept as -previous-dbdo and -before-dbdo.
- **DbDo-04, CSV formula triggers. Done.** CSV and TSV exports still hold values exactly; values a spreadsheet could run as formulas are counted, plain numbers like -5 excluded, and DbDo asks before opening such a file, No being the default; .xlsx, which keeps text as text, is named as the safe way into a spreadsheet. The test of what counts was tested here on 16 values; the C# awaits a build on Windows.
- **DbDo-05, rows a save leaves out. Done.** A deleted row has its data cells cleared, new rows are counted, an edit to a formula cell is listed by row and column and kept only in DbDo, and only rows DbDo read can be taken for deleted. Awaits a build on Windows.
- **DbDo-06, SQL by prefix. Done.** Statements are judged by their own words outside quotes, comments and brackets: WITH by the statement it leads into, PRAGMA with = as a setting, writes with RETURNING as giving rows. Tested here on 27 statements, by a prototype the C# follows line for line.
- **DbDo-07, template invariants. Done, with one open check.** Every build now checks each template's stored views, its .dbdo scripts and empty prime or look values, beside the links, kinds, triggers, SQL files, settings and reports it already checked. Tested here: all ten templates pass, and a copy with five faults put in on purpose failed on all five. Open: Update from Template on an edited older copy, on Windows.

## EdSharp

- **EdSharp-01, saves that truncate. Done.** Saves are written beside the file and swapped in.
- **EdSharp-02, backup rotation. Done.** The .bak survives until its replacement exists.
- **EdSharp-03, editing behavior. Open.** A Windows harness for opening, editing, saving and reloading.
- **EdSharp-04, encoding fidelity. Open.**
- **EdSharp-05, the installed tree. Open.** A test on a machine with no source or package cache.
- **EdSharp-06, legacy writes. Done.** Every one of the 68 places EdSharp writes, moves or deletes a file is listed in its developer guide by kind; the text utilities and Export now write through the kit, and export through a converter sets the earlier file aside instead of deleting it. Awaits a build on Windows.

## extCheck

- **extCheck-01, unavailable properties. Done.** Where Office cannot report what a rule needs, a CouldNotInspect row names it, in the category Not checked, instead of a false problem or a silent skip. Awaits a test in Office: an unreadable chart title should give CouldNotInspect, not ChartMissingTitle.
- **extCheck-02, Source labels. Done.** Source always says extCheck, and a new Modeled On column names the checker a rule follows.
- **extCheck-03, chart checks. Done.** Charts without axes, such as pie charts, are not asked for axis titles; an untitled axis is filed as Chart axis title; and the advice says a chart's figures or main point belong in text.
- **extCheck-04, Office deadline. Done.** A 10-minute deadline per file, stopping only the Office processes extCheck started (kit 1.72.38).
- **extCheck-05, rule precision. Open.** Documented heuristics and false-positive fixtures.
- **extCheck-06, whole reports. Done.** Reports and the rule registry are written through Homer.Util.writeTextSafely.

## FileDir

- **FileDir-01, recovery files deleted. Done.** Recovery copies get unique names.
- **FileDir-02, conversion rename. Done.** The converted file is swapped in through Homer.Util.replaceFileSafely.
- **FileDir-03, silent rollback failure. Done.** A failed restore is spoken and logged.
- **FileDir-04, converter deadline. Done.** A 15-minute deadline (kit 1.72.38).
- **FileDir-05, installer elevation. Done.** ExecAsOriginalUser, as in every Homer installer.
- **FileDir-06, old 2htm contract. Done.** 2htm's exit code is trusted first, as its source defines it; the message names the file and the task, explains a missing assembly as an older 2htm, asks for no hand repair, and 2htm's full output goes to the log.
- **FileDir-07, path identity. Open.** A test matrix of links, case and ancestry on Windows.

## HomerDev

- **HomerDev-01, skill links. Done.** The skill reference documents are published (kit 1.72.35).
- **HomerDev-02, conflicting conventions. Done.** No c_ prefix remains in any instruction file or code, and the build counts the skills (kits 1.72.35 and 1.72.37).
- **HomerDev-03, cached hashes. Done.** build_release reads every file again before push and release, check --fresh does too, and fingerprint.py takes --verify. Tested here as the audit asked: after a same-size, same-time change the ordinary cache kept the old hash and the verifying one gave the true one (kit 1.72.44).
- **HomerDev-04, author-specific tests. Done.** The KDP regression suite runs without a personal catalog: 66 tests pass (kit 1.72.35).
- **HomerDev-05, chat exits. Done.** Any failed exit is an error; the text is kept and introduced as possibly incomplete, and a failed first turn is not taken for a session to resume (kit 1.72.45).
- **HomerDev-06, connectAI. Done.** Files that are not UTF-8, and unpaired markers, are left alone and reported; only the block changes, in the file's own line breaks; a dated copy is kept first; and writes are atomic. Tested here on the real code: byte-for-byte round trips with and without a byte order mark, CRLF and LF, and a failure during the write (kit 1.72.45).
- **HomerDev-07, shared installer defects. Done.** One installer pattern, checked by the kit in every app.
- **HomerDev-08, discoverability on a clean install. Open.**
- Also, from this round: the kit's Content-Disposition parser reads the header as the standard writes it, and Web.sanitizeName avoids Windows device names (kit 1.72.46); and Homer.Util.fileSha256 gives every app a file's fingerprint by content (kit 1.72.43).

## HomerScribe

- **HomerScribe-01, raw transcript reused. Done.** The finished transcript is kept as transcript.final.json and reused.
- **HomerScribe-02, reuse without Whisper. Done.** Only for the same recording.
- **HomerScribe-03, leftover JSON. Done.** The earlier transcript is cleared before Whisper runs.
- **HomerScribe-04, identity by metadata. Done.** The recording and the model are known by the SHA-256 of their content.
- **HomerScribe-05, speaker labels. Done.** Only the made-up label that opens half the stretches is taken off. Tested here with the audit's case: two real speakers and a spoken Note kept.
- **HomerScribe-06, loops. Done.** Lines are compared without case or punctuation, alternating pairs count, and 30 seconds is enough; a loop is only heard again, and what is heard is kept. A stretch that loops again is reported as uncertain, not empty. Tested here on eight cases.
- **HomerScribe-07, acceptance specification. Done.** accept.inix runs scripts\acceptReuse.py: the built program, with the real Whisper, four times on clips of its own tutorials, including a different recording of the same size and time. The test itself was tested here against stand-in programs: it passed one that judges by content and failed one that judges by size and time, at the step it should.

## HomerView

- **HomerView-01, parity gaps. Partly.** Five commands came to JAWS; two gaps were the check's own blind spots and are now counted; seven remain, each needing a helper command or a dialog of its own.
- **HomerView-02, attribute order. Done.** A page's head is read by an HTML parser. Tested here on 13 cases.
- **HomerView-03, sampled length. Done.** A page longer than what was read is given as at least so many words, with the limit named; menus are not counted. Tested here against a local server.
- **HomerView-04, redirect cap. Done.** The ninth redirect stops the fetch, naming the last address. Tested here against a local server with chains of eight and nine.
- **HomerView-05, acceptance rebuilds. Open.**
- **HomerView-06, active-tab fallback. Open.**
- **HomerView-07, cursor-to-DOM identity. Open.**

## urlCheck

- **urlCheck-01, one title, two pages. Done.** A page is known by its address.
- **urlCheck-02, Force removes reports. Done.** Earlier reports are set aside until the new scan succeeds.
- **urlCheck-03, ownership by filename. Done.** urlCheck-source.txt names each folder's address.
- **urlCheck-04, aggregation. Done.** No criterion is marked Supports by automated checks; an automated pass is Not Evaluated with a note of what was found, and Supports is left to a reviewer. Tested here by generating a real ACR.docx with urlCheck's own code.
- **urlCheck-05, local-file scans. Open.**
- **urlCheck-06, worst-case progress and cancel. Open.**

## urlFido

- **urlFido-01, old collection deleted. Done.** Only after a complete run.
- **urlFido-02, backup deleted on the next Force. Done.** Recovery folders get unique names.
- **urlFido-03, identity by title. Done.** urlFido-source.txt names each folder's address.
- **urlFido-04, download receipt. Done.** A file's first bytes must fit its kind, a PDF must have its end, and a stated length must arrive; each folder's urlFido-downloads.txt records every download with its SHA-256. The content check was tested here on 11 files.
- **urlFido-05, Content-Disposition. Done.** Both download paths use the kit's parser. Tested here on 12 headers and 5 device names.
- **urlFido-06, Cancel. Done.** A transfer is copied a block at a time, the request is aborted the moment Cancel is pressed, and a cancelled file is not tried another way. Awaits a test on Windows with a slow download.

## The second audit of 14 October

That audit rechecked the current repositories and added these findings; each is answered here.

- **2htm-07, a timed-out Office worker. Done.** If the worker has not ended 30 seconds after Office is ended, the run ends, which ends it; the same in extCheck.
- **bookFido-07, markers alone. Done.** A PDF must open in PdfPig and have a page; an encrypted one is kept and logged as unchecked. Unrecorded files named for a title are no longer adopted.
- **DbDo-08, a cleared unsaved mark. Done.** It stays while edits Save could not write remain, and closing asks about them by name.
- **HomerDev-09, a destructive fallback. Done.** Two renames, never an overwrite; two complete copies at every moment. Tested here by a simulation of every combination of failures, 256 runs.
- **HomerDev-10, commit and rotation. Done.** Only a failed commit throws; a rotation problem is a returned warning naming the copy kept; EdSharp and DbDo log and say it.
- **HomerScribe-08, the last good cache. Done.** Only raw outputs are cleared before a hearing; the finished transcript and its identity are replaced only on success.
- **urlCheck-07, an unrecorded folder claimed. Done.** Adopted only when its own results.json names the address; urlFido and bookFido no longer adopt such folders or files. Tested here on the real code with the audit's case.
- **urlCheck-08, staging without a journal. Done.** Registered before the first move; a failed move puts back what moved. Tested here on the real code.
- **The KDP suite in a clean checkout. Done.** 66 passed, 0 failed, with no personal files and no HomerDev variable.
- **HomerView's metadata order and parity gaps.** Both were fixed on 14 October, but HomerView's build stopped on a naming check, so the repository the audit read did not have them; the naming check is answered (Yield Structure), and the next build carries them.

## The audit of 14 October morning

That audit read the morning's logs: nine releases succeeded, and two candidates were blocked. Its new findings:

- **2htm-08, an undefined constant. Done.** The guard used iExitFatal from another class; it now says program.iExitFatal.
- **HomerScribe-09, the acceptance test heard a remote video. Done, and it found a real fault.** A source named on the command line was added to the built-in sample instead of replacing it, so the sample was transcribed; the first source given now replaces it. The test counts only the test recording's transcripts, and was checked again here against its two stand-ins: a content-judging one passes all four steps, a size-and-time one fails exactly step 3.
- **HomerScribe-10, evidence deleted. Done.** A failed run keeps its folder -- each run's log, every transcript, both clips -- in logs, and the clips' fingerprints are logged.
- **HomerView-08, an incomplete results file. Done.** The file and the setup log now hold the whole summary shown, screen reader outcomes included.

## The audit of 14 October midday

- **HomerScribe-11, changed input skipped as done. Done.** Each results folder keeps the fingerprint of the recording that made it; a different recording, even of the same size and time, is made again. The acceptance test also takes a skip of an unchanged recording as success.
- **HomerDev-11, standalone /defaults. Done, with one Enter.** /defaults alone skips every page Inno allows to be skipped, each keeping its default; the finish page shows with its default boxes ticked. Inno decides silence before code runs, so /verysilent /defaults remains the way to show nothing. Awaits a run on Windows: setup /defaults should show only the finish page.
- **MyBooks-07, an ambiguous git message. Done.** No .git folder and no git program are now two answers; the second is a gap in the report.
- **MyBooks' other findings.** Legacy of Mazrui is not ready because 14 of its pictures cannot be found anywhere; that awaits the author's decision. The report's four missing parts and the title, edition and sales matching await a report run with their logs.

## In numbers

Of the 72 findings, 57 are done, one of them with a check still open; 1 is partly done; and 14 are open, each of them needing a run on Windows, Office, a clean machine or a screen reader.
