# HomerDev Update: bringing a Homer app up to the current kit

*A briefing on the learnings, decisions and techniques of HomerDev as of
26 September 2026 (kit 1.43.6), written so that another Homer app -- DbDo,
part way there; FileDir, some of the way; EdSharp, not yet started -- can
take up the kit's code, concepts and structure with less pain than
HomerScribe and HomerView went through. It is a developer document:
technical, dated, and specific about what went wrong. HomerScribe was the
first app moved; urlCheck, the first Python app, has its own section below;
HomerView, the second, is recorded below in its own section
because it met a different set of traps -- an existing PowerShell build, an
NVDA add-on, JAWS scripts, and a C# bridge -- and most of them will meet the
next app too.*

**Read "Lessons from HomerView" before starting.** Nearly every debugging
round in HomerView's migration was one of those lessons being learned. Each
is now a rule, and following the rules is what makes a migration a few
builds rather than twenty.

## Contents

- [What the kit is](#what-the-kit-is)
- [The contract between an app and the kit](#the-contract-between-an-app-and-the-kit)
- [Lessons paid for, with dates](#lessons-paid-for-with-dates)
- [The renaming of 26 September 2026](#the-renaming-of-26-september-2026)
- [Lessons from HomerView, 25-26 September 2026](#lessons-from-homerview-25-26-september-2026)
- [C# apps: urlFido, and a template brought level](#c-apps-urlfido-and-a-template-brought-level)
- [bookFido: a C# app with its own libraries and its own data](#bookfido-a-c-app-with-its-own-libraries-and-its-own-data)
- [Python apps: what urlCheck taught, 26 September 2026](#python-apps-what-urlcheck-taught-26-september-2026)
- [Installer template: the program from exec, the documents from help](#installer-template-the-program-from-exec-the-documents-from-help)
- [The kit renames only where it should](#the-kit-renames-only-where-it-should)
- [Installer template: read the previous version once](#installer-template-read-the-previous-version-once)
- [The migration, step by step](#the-migration-step-by-step)
- [DbDo: what it has, what it still needs](#dbdo-what-it-has-what-it-still-needs)
- [EdSharp: the full migration](#edsharp-the-full-migration)
- [FileDir: two branches, copied classes, binaries in the repository](#filedir-two-branches-copied-classes-binaries-in-the-repository)
- [What HomerView looks like now, as the second worked example](#what-homerview-looks-like-now-as-the-second-worked-example)
- [What HomerScribe looks like now, as the worked example](#what-homerscribe-looks-like-now-as-the-worked-example)
- [Summary of the rules, one line each](#summary-of-the-rules-one-line-each)

## What the kit is

`C:\HomerDev` is one repository holding everything the Homer apps share:

- `exec\CSharp\` -- the shared classes an app compiles against: `Elevate.cs`,
  `Inix.cs`, `KeyMap.cs`, `KeyName.cs`, `Lbc.cs`, `Log.cs`, `Mdi.cs`,
  `Ollama.cs`, `Paths.cs`, `PdfRead.cs`, `Say.cs`, `Util.cs`, `Web.cs`,
  `inixVert.cs`. An app never carries a copy; it names the kit's file on the
  compiler line.
- `exec\Python\` -- the same for Python, each a module imported by its own name: `elevate.py`, `inix.py`, `lbc.py`, `log.py`,
  `mdi.py`, `paths.py`, `say.py`, `util.py`, `web.py`.
- `scripts\` -- the tools every app inherits, refreshed into its own
  `scripts` folder on every build: `buildTutorials`, `check`,
  `checkTutorial`, `fixEncoding`, `push`, `unpushed`, `installCommon`,
  `tidy`, `installOllama`, `installScreenReaderSupport`,
  `makeTutorials`, `release`.
- `Templates\` -- what a new app starts from: `_APP_.cs`, `_APP_.cmd`,
  `_APP__setup.iss`, `build_APP_.cmd`, `build_APP_Py.cmd`,
  `create_APP_Repo.cmd`, `HomerComponents.iss`, `installModels.cmd`,
  `LocalFiles.txt`, `Tutorial_00_Overview.inix`, `accept.inix`,
  `makeHotkeys.py`, `gitignore.txt`; `samples\` (the four fruit-basket
  programs) and `skills\homer-tutorial\` (a skill for an AI writing walks).
- `help\` -- the kit's own documents, among them `Developer.md`,
  `FinishPage.md`, `Logging.md`, `Tutorials.md`, `History.md`.
- `exec\` -- binaries the kit's build fetches and never pushes: the tutorial
  voices (piper, sherpa-onnx, Kokoro).
- `version.txt` -- the kit's version. An app states the version it needs.

`buildHomerDev` builds the kit: converts its documents, builds the four
samples, fetches the voices, speaks its own walk, checks itself, and
carries files over from any earlier layout (it has a move list and a
retired list). `releaseHomerDev` checks, pushes and tags it.

## The contract between an app and the kit

### 1. Find the kit, state the version needed

Every build script begins the same way. From `buildHomerScribe.cmd`:

```
set "homerDev="
if defined HomerDev if exist "%HomerDev%\CSharp\Lbc.cs" set "homerDev=%HomerDev%"
if not defined homerDev if exist "C:\HomerDev\exec\CSharp\Lbc.cs" set "homerDev=C:\HomerDev"
if not defined homerDev if exist "%CD%\CSharp\Lbc.cs" set "homerDev=%CD%"
if not defined homerDev (
  echo HomerScribe needs the Homer Development Kit and cannot find it.
  echo Unzip HomerDev.zip into C:\HomerDev, or set the HomerDev environment variable.
  exit /b 1
)
set "homerVer=0.0.0"
if exist "!homerDev!\version.txt" set /p homerVer=<"!homerDev!\version.txt"
set "kitNeeded=1.42.0"
rem Trimmed, and a parse failure told from an old kit: the kit's version.txt
rem once carried a trailing space, and "1.40.1 is older than 1.40.1" followed.
powershell -NoProfile -Command "$h='!homerVer!'.Trim(); $n='!kitNeeded!'.Trim(); try { if ([version]$h -lt [version]$n) { exit 1 } else { exit 0 } } catch { exit 2 }"
if errorlevel 2 (
  echo The kit's version.txt at !homerDev! does not hold a version number.
  exit /b 1
)
if errorlevel 1 (
  echo HomerScribe needs HomerDev !kitNeeded! or later, and the kit is !homerVer!.
  echo Unzip HomerDev.zip into C:\HomerDev, then build again.
  exit /b 1
)
```

1.42.0 is the first kit with the renamed scripts, so an app that refreshes
`tidy`, `push` or `release` needs at least that.

`kitNeeded` is raised whenever the app starts depending on something new in
the kit. A build against an older kit stops with that message rather than
failing somewhere inside the compiler.

### 2. Compile against the kit's sources; carry no copies

```
set "homerSources="
set "homerSources=!homerSources! "!homerDev!\CSharp\Elevate.cs""
set "homerSources=!homerSources! "!homerDev!\CSharp\Inix.cs""
set "homerSources=!homerSources! "!homerDev!\CSharp\Lbc.cs""
...
csc ... HomerScribe.cs !homerSources!
```

**Lbc needs Elevate.cs in every build** (since kit 1.31): its Help box
carries the version section and the F11 update offer. Every build that
lists `Lbc.cs` lists `Elevate.cs`.

The copies of `Lbc.cs`, `Say.cs`, `Inix.cs`, `KeyMap.cs`, `Web.cs` that an
app used to keep had all drifted from the kit's by the time HomerScribe
moved over. Delete them; the whitelist (below) keeps them from returning.

### 3. Refresh the kit's scripts into the app on every build

One source of truth. The app's build copies them in; a fix in the kit
reaches every app on its next build; nothing is edited in place.

**Refresh only the tools this app uses** (26 September, HomerView). The
template's loop names every kit script, and taking it whole put
`installScreenReaderSupport` into HomerView beside its own
`installJawsScripts` -- two tools for one job -- plus tutorial tools for an
app with no tutorial. List what the app uses; add a tool the day it is used.

**Say when a named tool is missing; never skip it.** The loop used to copy
`if exist`, so when the kit renamed its scripts every copy would have been
skipped silently and the app kept stale old-named copies with nothing in the
log. The kit renamed its scripts on 26 September (see "The renaming"), which
is exactly that case.

```
if not exist "scripts" mkdir "scripts"
rem The kit tools this app uses. Name each; add one when it is used.
for %%F in (check.cmd check.py fixEncoding.cmd fixEncoding.py push.cmd release.cmd release.ps1 tidy.cmd tidy.py unpushed.cmd unpushed.py) do (
  if exist "!homerDev!\scripts\%%F" (
    copy /y "!homerDev!\scripts\%%F" scripts\ >nul && echo Refreshed scripts\%%F>> "%log%"
  ) else (
    echo NOT IN THE KIT: scripts\%%F>> "%log%"
    echo The kit has no scripts\%%F. Update HomerDev to !kitNeeded! or later.
  )
)
rem Retired and renamed kit scripts an app may still carry: gone.
for %%F in (checkHomerApp.cmd checkHomerApp.py cleanDir.cmd cleanDir.py gitPush.cmd gitRelease.cmd gitUnpushed.cmd gitUnpushed.py homerInstall.cmd homerPolicy.py homerTidy.cmd homerTidy.py installTools.cmd sayTutorial.cmd sayTutorial.py tagRelease.cmd tagRelease.ps1 tidyRepo.cmd tidyRepo.py) do (
  if exist "scripts\%%F" del /q "scripts\%%F" && echo Removed retired scripts\%%F>> "%log%"
)
```

Add to the first loop as the app needs them: `installCommon.cmd` (the
common half of `install<Thing>.cmd` scripts, if the app has any written in
cmd), `installOllama.cmd`, `installScreenReaderSupport.cmd` (only if the app
has no reader installer of its own), `finish.cmd`, and the tutorial tools
`buildTutorials`, `checkTutorial`, `makeTutorials` once a walk exists.
`installModels.cmd` stays the app's own, because it names the app's models.

### 4. The folder layout, and why the first letters differ

The development folder `C:\<App>` mirrors the installed tree: sources,
build files, ReadMe and License at the top, and these folders --
`configs`, `data`, `exec`, `help`, `logs`, `results`, `scripts`,
`templates`. **Every standard folder starts with a different letter**, so a
screen reader user walks a folder list by initial letter. Two violations
were found and fixed on 25 September: the kit's `Samples` (s, like scripts)
became `Templates\samples`; HomerScribe's `context` (c, like configs)
became `templates`. A subfolder under a standard folder is fine; a new
top-level folder is not.

What goes where:

- `configs` -- settings files the app reads; `.inix` for anything INI-shaped.
- `data` -- data the app ships or keeps: dictionaries, lookup databases.
- `exec` -- the built program and the binaries that sit beside it (the DLLs
  it links). Not in git. Fetched things go here or, if shared by every app,
  machine-wide (see 7).
- `help` -- every document but ReadMe and License: the guide, Developer,
  History, Hotkeys, Announce, Tutorials, the `Tutorial_NN_*.inix` walks and
  `tutorials\*.mp3`.
- `logs` -- one log per run of anything, `<App>-<task>-yyyyMMdd-HHmmss.log`.
- `scripts` -- the kit's tools (refreshed) and the app's own command scripts.
  Screen reader scripts an app ships go in a subfolder, `scripts\jaws`.
- `templates` -- what a person copies and edits: a worked example of a
  context file, a starter database, a sample document.

### 5. RepoFiles.txt and LocalFiles.txt

Two lists decide what git carries. `RepoFiles.txt` names the files and
folders the repository holds (a trailing slash names a folder wholesale; a
wildcard is allowed). `LocalFiles.txt` names what stays on this disk and is
never pushed: `exec/`, `logs/`, `work/`, `notes/`, `packages/`, generated
audio, anything fetched. `tidy` writes `.gitignore` as a **whitelist**
from `RepoFiles.txt` -- everything ignored, then exactly the named files
allowed -- and `push` rewrites it before every push. So `git add -A`
means "add everything the project has named", never "everything in the
folder".

The lesson behind this, 25 September: a project with no `RepoFiles.txt`
swept 480 fetched voice files into a commit. `push` now stages nothing
without the list, and refuses any commit that stages a file over 10 MB.

Three rules from HomerView, 26 September:

- **Do not name `scripts\` wholesale.** A folder named in `RepoFiles.txt`
  whitelists everything in it, and `scripts\` holds `release.cmd` and
  `release.ps1`, which by standing rule stay out of git in every repository
  (they are the separate tagRelease project's). Name the app's scripts and
  the kit tools one by one; put `release.*` in `LocalFiles.txt`.
- **No `local:` section in `RepoFiles.txt`.** An older tidy script
  understood one; `tidy` does not. It reads `local:` as a file name and
  everything after it -- `exec\`, `version.txt`, fetched engines -- as files
  to commit. Local files go in `LocalFiles.txt` and nowhere else.
- **Name every generated file you commit.** A generated `.htm` named nowhere
  looks like a stray draft to `tidy`, which moves it to `notes\drafts`; the
  next build then stops because the installer names a file that is gone.
  Both the `.md` and its `.htm` go in the list.

### 6. The four scripts, and the order they run in

1. `build` -- steps `version.txt`, writes `Version.cs`, builds the
   program and the installer, speaks any tutorial without audio, puts the
   project's own files into the Homer encoding, refreshes the scripts.
2. `scripts\push "message"` -- rewrites the whitelist, adds what it names,
   commits, pushes, shows the status.
3. `scripts\tidy` -- the periodic clean: strays into `notes`,
   fetched things deleted, zero-byte files deleted, whitelist rewritten,
   strays untracked, commit. `--gitignore` alone rewrites the whitelist.
4. `scripts\release` -- runs the app's checks (`check --build`),
   then tags the pushed commit with the version stamped in
   `<App>_setup.exe` and publishes the installer as a GitHub release.
   `-SkipCheck` when the checks have just run.

And `scripts\unpushed` undoes a local commit that should not go up,
keeping every file.

Every tool takes the project to be the folder it is run in, **or the parent
when that folder is the project's `scripts` or `exec`** -- so
`cd scripts` and `push` is the same as running it at the top. Never keep
copies of these tools in `C:\bin` or anywhere on the PATH: they go stale
there and run instead of the app's own. The kit's build deletes such
copies when it finds them.

### 7. Versions

`version.txt` holds the current number and lives only on the developer's
machine -- never in a delivered zip, never in the repository (it is in
`LocalFiles.txt`). The build steps it, writes `Version.cs` from it, and
stamps the installer; `build nobump` keeps the number. `release`
reads the version from the installer's own resource, so the tag can never
disagree with what was built.

**Everything else is written from `version.txt`, every build, bumped or
not** -- an NVDA add-on's `manifest.ini`, a `Version.cs` -- so they cannot
drift. HomerView had it backwards, with `manifest.ini` the source. **Seed a
missing `version.txt` from the app's existing number, never from 1.0.0**: a
fresh clone that reset HomerView to 1.0.0 would publish a release older than
every installed copy.

### 8. Shared components install machine-wide

Whisper, Tesseract, Pandoc, ExifTool, ffmpeg, yt-dlp, Ollama and the like
go to their own default machine-wide directories -- `C:\Program Files\...`
-- so every Homer app finds and shares one copy, and an app upgrade (which
replaces the app's folder) cannot destroy them. Libraries the app links
(its DLLs) belong beside the executable in `exec`. An installer is
machine-wide and requires admin; there is no per-user fallback. Anyone
wanting a portable copy uses the zip.

### 9. The build fetches what it needs

winget, NuGet, a direct download -- the build retrieves every component
needed to compile and to run, in a sufficiently current version, and never
leaves a manual fetch step. Two hard-won particulars:

- **whisper.cpp changed its release process on 20 August 2026**: version
  tags carry only source archives; compiled binaries hang off nightly
  build tags marked pre-release, so `/releases/latest` returns a release
  with no Windows build. `installWhisper.cmd` reads `/releases?per_page=30`
  and takes the first release with a Windows x64 CPU asset, with a pinned
  fallback. Any script that fetches from GitHub should expect this shape.
- **The tutorial voices are fetched only by the kit's build** into
  `C:\HomerDev\exec`. An app's build never downloads them; if they are
  absent, the tutorial tool says "Run buildHomerDev" and speaks nothing.

### 10. Logs, console and encoding

- Every CLI script writes a detailed log aimed at debugging -- script path,
  Python or PowerShell version, platform, working directory, command line,
  every effective setting, every command with its exit code, any error --
  in `logs\<App>-<task>-yyyyMMdd-HHmmss.log`. An installed program logs
  under `%LOCALAPPDATA%\<App>\logs`.
- The console is for a person: succinct, human-friendly, naming each thing
  as it is made ("Creating Tutorial_01_Transcribe.mp3, 12 steps"). Technical
  detail belongs in the log. A build was stopped by hand twice on 25
  September because its screen said one sentence and then nothing for
  minutes.
- The Homer encoding is UTF-8 with a byte order mark and CRLF, except that
  `.cmd` and `.bat` take CRLF and no mark. Pandoc writes neither, so every
  build runs `scripts\fixEncoding` over the files `RepoFiles.txt` names
  before compiling. Zero-byte files are deleted, not kept.
- `installCommon.cmd` is the logging half of every install script: each
  `install<Thing>.cmd` calls it to open a log, run a command, record the
  exit code. Every install script says "Downloading" before a long step.

### 11. The installer and its finish page

The template `_APP__setup.iss` with `HomerComponents.iss` gives the finish
page its shape (details in the kit's `help\FinishPage.md`):

1. Install screen reader scripts (ticked, `isFreshInstall`).
2. Install each component alphabetically (ticked, `homerIs(i,0)`).
3. Update each component alphabetically (ticked, `homerIs(i,1)`).
4. Reinstall each component alphabetically (unticked, `homerIs(i,2)`).
5. Models: Install (ticked), Reinstall (unticked).
6. Launch the program (ticked; deferred until after the Results box).
7. Open the user guide (unticked).

Script order plus `Check:` visibility does the grouping. The Results box
reports only what actually ran that session, in the past tense, built from
the boxes that were ticked (`homerNoteTicked`, `homerOutcomeLine`), never
from a probe made when the wizard opened. Install scripts live in
`scripts\` and are run from `{app}\scripts`.

**Offer only this app's components.** Before adopting the template, read
the app's installer as it was before the move and list what it offered.
The template's examples (Ollama, models) belong to the apps that use them;
the spell checker is EdSharp's, Whisper is HomerScribe's, pandoc is
HomerView's. `#include`-ing `HomerComponents.iss` adds nothing by itself --
a component exists only when the app calls `homerAdd` for it.

Seven installer rules HomerView paid for, 25-26 September:

- **Every screen reader line has its `Check:`.** HomerView's JAWS line had
  `HaveJaws`; its NVDA line had nothing, so a JAWS-only machine was offered
  an NVDA add-on, ticked, and a message box then warned it would fail. The
  message existed only to excuse the missing `Check: HaveNvda`.
- **`Source:` lines are relative** (`Source: "help\HomerView.htm"`), never
  `C:\<App>\...`. Inno resolves them against the script's folder either
  way, but `tidy` compares names, and an absolute path matches nothing --
  so every file named only there counted as a stray.
- **Run install scripts directly**: `Filename: "{app}\scripts\installX.cmd";
  Parameters: "noPause"`. Through `{cmd}` with doubled quotes they fail
  silently.
- **`#include` the component table from inside `[Code]`**, with
  `#ifndef HomerDev` / `#define HomerDev "C:\HomerDev"` / `#endif` above it,
  and have the build pass `/DHomerDev=<kit>` to ISCC. An include that
  declared its own `[Code]` would start a second section.
- **`[UninstallDelete]` names only what the app made for itself.** HomerView
  listed its whole `{localappdata}\HomerView`, which held the reader's
  recent-pages list and the browser profile with their sign-ins. List the
  logs, caches, temporary files -- the same list the app clears at startup.
- **`UsedUserAreasWarning=no`, with the reason in a comment**, when an admin
  installer deliberately touches `{localappdata}` or `{userappdata}` (reader
  scripts, the app's data). A warning in every build log hides the new one.
- **A pre-build check of `Source:` lines skips build output.** HomerView's
  build checked that every `Source:` existed at step 1, and `exec\` is
  filled at steps 3 to 5; it passed only while an old `build\` survived.

**List OK first** in every `Lbc.runWithButtons` call: Lbc makes the first
label the default button, and a wizard once opened Help on Enter because
"Help" was listed first. A length is spoken in words ("Took 19 minutes",
`Util.spokenLength`); a clock reading is a position.

### 12. F11 and the version box

`Elevate.configure(owner, repo, version)` at startup. Lbc's Help box then
carries a Version section; when a newer release exists on GitHub, the box
offers Yes (default) to fetch `<App>_setup.exe` and run it. F11 is the key
(elevate sounds like eleven). This is how a user updates without visiting
a web page.

### 13. Tutorials: the spoken walks

A walk is `help\Tutorial_NN_Name.inix`: `[about]` (Title, Intro, Setup,
Homework), then one `[step]` per keystroke with `Say` (narrator), `Key`,
`Hear` (the reader's answer, one line per utterance), `Note` (written only),
`Pause`. Four beats per key: say the key with the word it comes from; press
it; hear the reader word for word; say what that meant. Name silence.
Verify after every focus change with Insert plus T. Teach the repeat key in
the first walk. **Name no screen reader.** The reader's grammar per control
is in the kit's `help\Tutorials.md`, taken from real speech.

`scripts\checkTutorial` checks every script against the format and the
grammar; `scripts\buildTutorials` runs it first and speaks nothing while a
problem stands, then speaks each walk -- Kokoro for the narrator, piper for
the reader, every piece at one loudness -- into `help\tutorials\*.mp3`,
writes `help\Tutorials.md` and `TutorialFeed.xml`. The build calls it with
an explicit `-build` argument (see the `%*` quirk below).
`.claude\skills\homer-tutorial\SKILL.md` teaches an AI to write them.

### 14. The check, and what "done" means

`scripts\check` (with `--build` to make the build itself evidence)
checks: the documents present, each with its `.htm` (ReadMe, License, the
app's guide, Developer, History, Hotkeys; Tutorials where walks exist);
`RepoFiles.txt` present and `.gitignore` the generated whitelist; the Homer
encoding of the project's own files; evidence of logging; the build script
named after the folder returning 0; `accept.inix` stating what done means.
`release` refuses to release when it fails. Its report goes in
`logs\<App>-evidence-<stamp>.md`.

## Lessons paid for, with dates

- **25 Sep, `%*` is not reset by a bare `call`.** A build run as
  `buildHomerScribe nobump` called the tutorial tool with no arguments, and
  "nobump" arrived there as a script name. Every call from a build passes an
  explicit argument (`-build`), and every tool ignores dash-arguments it
  does not know.
- **25 Sep, Windows does not tell `Scripts` from `scripts`.** A move-pair
  from an earlier layout deleted the freshly delivered
  `scripts\installCommon.cmd`, taking it for the stale copy. Any list that
  moves files must skip a pair whose two sides are the same file.
- **25 Sep, similar-sounding names cause wrong tools to run.** `cleanDir`
  beside `tidy`, `gitRelease` beside `release`, `sayTutorial` beside
  `buildTutorials`, `makeTutorial` beside `makeTutorials`. One tool per job;
  the retired one is deleted by the build.
- **25 Sep, fetched things are deleted, never archived.** A tidy once moved
  486 voice files into `notes` and committed them.
- **25 Sep, Kokoro is slow on long unbroken text** (71 seconds for an
  8-second spelled-out web address) and slower on many threads (two threads
  beat all cores). Text is cut at sentences and commas; the reader speaks
  through piper; Kokoro runs on two threads. Seven walks take 23 minutes.
- **25 Sep, PowerShell logs a native program's first stderr line as a
  NativeCommandError**, five lines per piece. Filter the wrapper, keep the
  program's own words.
- **24-25 Sep, an installer's "checking for a newer version" hid a 1 GB
  download**; every long step now says "Downloading" first.
- **21 Sep, one log per run in `logs`**, never beside the script; alpha
  sort is chronological.
- **10 Sep, ship a build error rather than a quarantined feature.**
  Implement fully; let the failure surface in the normal build.

## The renaming of 26 September 2026

The kit's scripts lost the prefixes that said nothing a folder name did not.
Old logs, old briefings and other chats use the old names, so here is the map:

- `checkHomerApp` is now `check`
- `gitPush` is now `push`
- `gitUnpushed` is now `unpushed`
- `homerFinish` is now `finish`
- `homerInstall` is now `installCommon` -- not `install`, because it is
  called by other install scripts and never run, and a bare `install.cmd`
  in a scripts folder looks like something to run
- `homerTidy` is now `tidy`
- `tagRelease` is now `release` (the standalone project keeps its name)

`buildHomerDev` does the rename **in place** on the kit's own disk: it
renames each file, keeping its content, rewrites the old names in the kit's
text files, and adds the old names to the template's retired list so every
app's build deletes its stale copies. It does not ship renamed copies, for a
reason worth knowing: the kit on a working machine can be newer than any
archive of it (on 26 September the machine was at 1.41.3 and the GitHub
archive at 1.41.0), and `release.*` is never in git by rule. Shipping
renamed copies would have replaced the newer content with the older and
then deleted the newer original.

**Each app's own `build.cmd` is not in the kit and must be updated in
that app's chat**: the refresh loop to the new names, the retired loop to
include the old names, and `kitNeeded` raised to 1.42.0. The kit's build
cannot reach it. Until that is done the app's build will say "NOT IN THE
KIT" for each tool -- if it uses the loop in section 3 -- or, with the old
`if exist` loop, keep its stale copies without a word.

## Lessons from HomerView, 25-26 September 2026

HomerView was the second app moved to the kit. It had a working PowerShell
build, an NVDA add-on, a JAWS script set compiled against three JAWS
versions, and a C# bridge -- none of which the template knows about. Every
lesson below cost at least one build round; each is written as the rule
that would have saved it.

### Plan the move in passes, and build green between them

What worked, in order:

1. **The contract, without moving a file.** Kit detection, `kitNeeded`,
   compiling against the kit's C#, refreshing the kit's tools, retiring the
   old ones, `fixEncoding`, one log per session in `logs`. An existing build
   engine can stay the engine: HomerView kept `buildHomerView.ps1` and wrapped
   it in a `buildHomerView.cmd` that carries the contract and hands the engine
   the compiler and the kit sources as parameters.
2. **The folder layout, one group at a time**, each group built green before
   the next: documents to `help`, reader scripts to `scripts\jaws`, binaries
   to `exec`, generated config to `configs`, the start page to `templates`,
   the app's own tool scripts to `scripts`. Doing it all at once would have
   put five kinds of failure in one log.
3. **The installer**, against the pre-move installer's component list.
4. **The documents' checks** -- the guide against the key tables.

**Before moving anything, grep for every reference to it, in every
language.** HomerView's map found 25 files across C#, JAWS script, Python,
PowerShell and the installer, and turned up a file the installer had never
shipped (`chainJawsScripts.cmd`, which Choose Browser runs). A move is done
when a grep for the old path finds nothing live.

### Passing data from cmd to PowerShell

- **Nested quotes do not survive.** A list of quoted paths passed as one
  quoted argument arrived with the quotes stripped; the engine found nothing
  to split on, compiled without the kit, and csc said "InixCodec does not
  exist". Join lists with a character a path cannot hold (`;`), and make the
  receiving side **refuse an empty list** by name instead of carrying on.
- **`%*` is not reset by a bare `call`** (the HomerScribe lesson, confirmed
  again): pass every tool an explicit argument such as `-build`.

### The compiler

- **`Framework64\v4.0.30319\csc.exe` is the legacy compiler and stops at
  C# 5.** The kit's classes use newer C#, so an app compiling them needs
  Roslyn (Visual Studio or the free Build Tools); the wrapper finds it in the
  usual places or installs Build Tools with winget. Its failure message never
  mentions the language version -- it says `} expected` and forty consequent
  errors -- so a local function or `$"..."` looks like a brace problem.
- An app check that **forbade C# past version 5** was right while the app
  used the old compiler and became wrong the moment it compiled the kit's
  sources. Retire such a check with the reason recorded.

### Reading the kit's version

The kit's `version.txt` carried a trailing space, `[version]` would not parse
`"1.40.1 "`, PowerShell threw, and the non-zero exit was read as "older":
FileDir's build said "kit 1.40.1 is older than 1.40.1". **Trim both numbers,
and tell a parse failure from an old kit** (`exit 2` for the first). The
template does this since 1.41.0.

### Unzipping never deletes and never moves

This one caused more rounds than any other.

- **A delivery that moves a folder carries only the files it contains.** When
  HomerView's JAWS scripts moved from `jaws\` to `scripts\jaws`, only the one
  file a later delivery happened to include arrived; the other two stayed in
  `jaws\`, and the quality check, reading the new place, reported every
  command as undocumented. **The build carries a missing file across from the
  old place** and leaves one already there alone, as the newer.
- **Old copies stay, work, and drift.** The build removes each root copy of a
  moved script **only once its replacement exists**, and moves an old folder
  to `notes\` **only once nothing in it is unique** -- never deletes it.
- A warning that an old folder is still there, **repeated on four builds in a
  row, was not acted on.** Where the build can safely act, it should.

### A script that finds the project by its own location

Every HomerView tool took **its own folder** as the project root. Moving one
into `scripts\` silently moved the root with it, so every path it joined
pointed one level too deep. The rule for any script in `scripts\`:

```
$pathHere = Split-Path -Parent $MyInvocation.MyCommand.Path
$pathRoot = if ((Split-Path -Leaf $pathHere) -ieq "scripts") { Split-Path -Parent $pathHere } else { $pathHere }
```

Siblings are found in `$pathHere`, the project in `$pathRoot`; the fallback
keeps an older flat layout working. A Python tool changes directory to the
project first, so it runs from anywhere. The same for a program in `exec\`:
HomerView's bridge gained one `AppFolder()` helper -- the parent of `exec`,
or its own folder on an older install -- and every place that joined a name
to the exe's folder goes through it, so only one place knows about `exec`.

### Generated files: one source, and regenerate rather than mourn

- **Two copies drift.** HomerView had two start pages (the add-on's and the
  installer's), a stale `docs\` copy of every document, and a checked-in
  copy of the documents inside the add-on. Each was fixed by making one
  source and generating the rest on every build.
- **A generated file's version is its content.** The add-on refreshed the
  reader's start page only when a version number changed, and the page was
  edited without the number being raised; now the number is a hash of the
  page.
- **The build makes every `.htm` from its `.md`** when the `.md` is newer or
  the `.htm` is missing, then puts on the Homer encoding. A lost `.htm` is
  then a non-event.
- **Tables generate documents; documents do not restate tables by hand.**
  HomerView's hotkey list, its hotkey `.inix` and its start page are written
  from the key tables. The start page had been describing keys retired weeks
  earlier.

### A check that only prints is ignored

HomerView's documentation check printed "does not mention 1 command: Page
Folder" on every build for weeks. Its guide also named four NVDA keys that
had changed nine days before, and nothing checked keys at all. The guide
check now compares keys as well as names, **and both failures stop the
build**. A guide that names the wrong key is a program that does not do what
it says -- the standing preference is a build error over that. Prove a check
by putting a known error back and watching it fail.

### Reader scripts and the browser

- **An application script file extends the factory set by `Use`-ing it, and
  there is no factory set for Edge.** Kelly at Vispero's advice -- a user
  `<app>.jss` should `Use "<app>.jsb"` -- is right where JAWS ships that
  set; for Edge it does not, so `Use "msedge.jsb"` named the file's own
  output and nothing of HomerView loaded. Look for the factory binary in
  JAWS's **Scripts** folder (not Settings, where every earlier search looked)
  and `Use` it when present, `default.jsb` otherwise.
- **Read a written script file back.** The keys had been read back for weeks;
  the `Use` lines had not, and a wrong file passed through three JAWS
  versions silently.
- **Never give a factory routine's name to one of your own.** A user routine
  with a factory name replaces it, and calling the name from inside recurses.
  The `hV` prefix prevents it; a build check compares every routine against
  the factory `default.jss`.

### Changing the kit in place

The kit on a working machine is often ahead of any archive of it, and
`release.*` is never in an archive at all. So a change to a kit script is
made **in place** by `buildHomerDev`, never by shipping a replacement:

- **Rename** (`renameScripts`): rename the file where it lies, keeping its
  content; rewrite the old name in the kit's text files as whole words only,
  line by line, leaving any line that exists to name old files (the retired
  list); skip dated records.
- **Patch** (`patchScripts`): find **one exact line**, replace or extend it,
  and leave a **marker** so a second run sees it and does nothing. When the
  line is not there, log that it was not patched -- never guess.
- **Prove it by running it twice** on a copy: the first run changes things,
  the second changes nothing. That caught a real fault in the renaming.
- **History is updated the same way**, an entry inserted once under a marker
  heading, because shipping `History.md` could overwrite a newer one.

### Never run anything between a command and its errorlevel check

The first version of the origin patch for `push` inserted a PowerShell line
straight after `git push`, and the next line was `if errorlevel 1`. Anything
run in between resets errorlevel, so every failed push would have been
reported as a success. Insert after the check, never between.

### Probing with git and gh from PowerShell 5.1

`release` asks git whether a tag exists and gh whether a release exists, and
the normal answer is no, printed on stderr. Windows PowerShell 5.1 records
that as a red `NativeCommandError` in the transcript **even with `2>$null`**,
so a clean release showed two error blocks. Set `$ErrorActionPreference` to
`'SilentlyContinue'` around the probe and restore it after; the exit code,
which is what the script reads, is unaffected. The standalone tagRelease
project needs the same change.

### A remote that has moved

Every push and release answered "This repository moved. Please use the new
location" -- the remotes say `JamalMazrui` and the account is `jamalmazrui`.
A redirect works until it does not. `push` now reads that message from its
own log and runs `git remote set-url origin <new location>` once, after its
failure check; the notice then stops. Every repository whose remote was made
with the capitalised name is corrected on its first push after kit 1.42.1.

### Everything else

- **A running program cannot be overwritten**, and csc says so as a
  file-in-use error buried in its output. The build says "HomerView.exe is
  running" first -- **reporting only, never closing** the program.
- **Pandoc was being copied into the app's own folder**, against the
  machine-wide rule; it now installs to `Program Files\Pandoc`. The app's
  runtimes already searched there and on the PATH, so nothing else changed.
- **A warning Inno gives on every compile** (`UsedUserAreasWarning`) was
  acknowledged with its reason, so a new warning stands out.
- **The kit's `version.txt` on disk may be ahead of GitHub.** When an archive
  is older than the working copy, change the working copy in place (as the
  renaming does) rather than shipping files that would overwrite it.

## C# apps: urlFido, and a template brought level

urlFido, a C# console program with an Lbc dialog, moved to the kit on
26 September, and the C# build template turned out to be behind the Python
one written for urlCheck the day before. Kit 1.43.2 rewrote
`Templates\build_APP_.cmd` clause for clause against `build_APP_Py.cmd`, so
the two contexts stay separate but equal. What urlFido taught:

- **Check the app's calls against the kit's classes before deleting its
  copies.** urlFido called LbcDialog (two-argument constructor, addBand,
  addInputBox, addButton, addCheckBox, addSeparator, endBand, runWithButtons,
  form), InixCodec (read, writeValue, Section.Name, keys, get), Web, Util and
  Say. Every one exists in the kit with the same signature, so the copies
  could go. A mismatch would have been a compile error, which is the right
  way to find it, but a grep first saves a round.
- **The kit's classes need each other.** Lbc calls Elevate, Log and Say; Log
  and Paths call each other; Log calls Say. An app that used to compile Lbc,
  Say, Inix, Util and Web must add Elevate, Log and Paths. homerModules names
  them; the template's comment says which needs which.
- **Log.start comes after anything that must precede Say.** Log's header asks
  Say which reader is running, and Say's DllImport of the NVDA client
  resolves then. urlFido pre-loads its embedded client first, so Main runs
  nvdaLoader.preload, then Log.start, then Elevate.configure.
- **F11 goes through the dialog's commandKey**, which claims a key before any
  control sees it. When Elevate.offer returns true the setup program is
  running, and the dialog closes.
- **A const version.** Version.cs holds `public const string Version`, so an
  app can build constants from it: urlFido's user agent is
  `" urlFido/" + BuildVersion.Version`.
- **Fetch the NVDA client; never ask for it.** The old build said "put the
  64-bit DLL here and rebuild". The template now fetches it from NV Access,
  and takes a top-level copy the project already has.
- **Two tools, one hotkey.** urlFido and urlCheck both claimed Alt+Control+U;
  urlCheck moved to Alt+Control+Shift+U as urlFido's installer had long said
  it would. Check a new desktop hotkey against every Homer app's installer.
- **A build that says "Build FAILED" and nothing else jumped somewhere it
  should not.** urlFido's first build wrote "Build FAILED" twice and no reason:
  the C# template carried a pasted second copy of the Python template's
  version code, and `call :seedVersion` landed in it. cmd takes the first
  label it meets and never complains about a duplicate, so the kit build now
  checks every script for a label defined twice and for a jump to a label
  that does not exist. When a script is assembled from pieces of another,
  cut at the label line itself (a line starting with `:`), never at the first
  occurrence of the label's name, which is usually the `call` that uses it.
- **Set seedVersion to the number the move should start at, and it holds.**
  An app may already have a version.txt on the developer's machine, never in
  any zip. Since 1.43.5 seedVersion is a floor: a lower version.txt is raised
  to it. Before that, 2htm's 1.18.4 stepped to 1.18.5 under documents that
  said 1.19.0.
- **A Python app with WinForms dialogs uses the C# LbcDialog.** Set
  homerDll=1 and add lbcnet to homerModules; build the dialog with
  `Homer = lbcnet.load()` and `Homer.LbcDialog(...)` exactly as a C# app
  would, passing button lists through `lbcnet.strings()` and a key handler
  through `lbcnet.keyHandler()`. Keep pythonnet's own workarounds in the
  app's handlers (the legacy file picker, SHBrowseForFolder). homer.lbc
  (wx) stays for code that runs inside NVDA. urlCheck 1.12.3 is the worked
  example.
- **An app's standing choice outranks the template's default.** The template
  deletes saved settings on uninstall; urlFido always kept them, "their
  filesystem, their call", and still does.

## bookFido: a C# app with its own libraries and its own data

bookFido, the third app moved on 26 September, embeds a dozen NuGet libraries
and keeps a database worth hours of gathering. What it taught:

- **An app's special build steps stay in the app's build, as a section of
  their own.** bookFido's pinned NuGet fetch (by lib folder for most packages,
  by file-name search for the SQLite ones) was proven over many runs; it moved
  into buildbookFido.cmd unchanged in substance, fetching into `work\nuget`,
  rather than being squeezed into the template's simpler `nugetPackages`.
- **Moving the program into exec moves everything that says "beside the
  program".** bookFido kept its state and database beside its own exe. Built
  into exec, it would have started with an empty database. Its data now lives
  in `Paths.data()` whatever the exe's folder, and the first run MOVES the
  newest existing copy there from the old places -- beside the exe, the folder
  above exec, `%LOCALAPPDATA%\<App>`. Grep an app for BaseDirectory before
  moving it.
- **Keep the verified configuration where it matters.** bookFido's resolver
  prefers a library file beside the exe over embedded bytes (the cure for its
  assembly-instance trap), and every verified database run had the files
  beside it. The build copies them into exec too, so the project copy behaves
  exactly as before; the installer still ships the program alone.
- **An uninstaller keeps what cannot be made again.** The template deletes
  logs and settings; bookFido's uninstaller deletes logs and the engine it
  wrote out, and keeps the database and the Edge profile holding sign-ins.
- **A windowed program cannot be smoke-tested with --help.** check now reads
  the PE header and skips a windowed program rather than waiting fifteen
  minutes for it.

## Python apps: what urlCheck taught, 26 September 2026

urlCheck is one 7,000-line Python file: a console program with a WinForms
dialog through pythonnet, driving Edge with Playwright, frozen by PyInstaller.
It was the first Python app moved, and it found that the kit's Python side had
fallen behind the C# side in ways no C# migration would notice. Kit 1.43.0
fixed them; these are the rules that came out of it.

### The contract is the same; the template now says so

`Templates\build_APP_Py.cmd` keeps every clause of the contract above: kit
detection by `exec\homer\log.py` and a trimmed `kitNeeded`; `version.txt` stepped,
seeded when missing and written into `version.py`; one log per run in `logs`;
the kit tools refreshed by name and retired ones deleted; `fixEncoding -build`;
`/DHomerDev=` to ISCC. A Python app's build is the template with its SETTINGS
block filled in -- `kitNeeded`, `seedVersion`, `pyVersion`, `pyiMode`,
`homerModules`, `pyiExtra`, `pipPackages`, `kitTools` -- and, during a move,
one section of its own that carries over the old layout (see below).
buildUrlCheck.cmd is the worked example.

### The kit's modules are named, not copied

A frozen program cannot import from `C:\HomerDev` at run time, and a copy in
the app drifts. So the build passes `--paths C:\HomerDev\exec` and one
`--hidden-import homer.<module>` for each module in `homerModules`. The .exe
then carries the kit's code as it was at build time. An NVDA add-on is the
exception: NVDA gives add-ons no way to share one copy, so an add-on copies
`homer`.

### Never name a kit module version.py

Every Homer build writes `version.py` beside the program. `.gitignore`
ignores that name wherever it appears, and the checks skip it as generated.
The kit's `exec\homer\version.py` was therefore never pushed, sat stranded in an
old `Python\homer` folder, and the kit's own check called it missing on every
build. Its comparison is now in `exec\homer\elevate.py`. The general rule: a kit
file must not share a name with anything a build generates.

### Where each Python program goes

- The program: `exec\<App>.exe`, from `--distpath exec`.
- PyInstaller's scratch and `.spec`: `work\pyinstaller`, from `--workpath` and
  `--specpath`. **Pass the icon's full path**: PyInstaller resolves `--icon`
  against the `.spec` file's folder.
- The build environment: `.venv`, rebuilt when its Python is not `pyVersion`.
- `.venv/`, `exec/`, `version.py`, `version.txt` and `work/` in
  `LocalFiles.txt`.

urlCheck had committed a 70 MB PyInstaller `build\` folder and both .exe
files. The build now deletes those once the new program exists, and one
`scripts\tidy` untracks the rest. `push` refuses anything over 10 MB,
so a stray setup program cannot go up by accident.

### A program that runs from exec finds its documents one level up

`homer.paths.installedFolder()` answers the parent of `exec`, in the installed
tree and in the project alike. urlCheck's Help had looked for `README.htm`
beside the .exe; it now opens `help\<App>.htm` under that folder, then
`ReadMe.htm`. A command-line wrapper at the top, `<App>.cmd`, runs
`"%~dp0exec\<App>.exe" %*`.

### Logging: the session log is not optional

urlCheck wrote a log only when `-l` was given, into the output folder, in
append mode. The kit's rule is a log of every session in
`%LOCALAPPDATA%\<App>\logs`. The move kept the app's own `logger` class --
three programs share its surface -- and made it write every line through
`homer.log` as well, and its settings header as `log.keyValue` lines. `-l`
keeps its old meaning as an extra copy beside the results. The entry point
became `runLogged()`, which records any exception main() did not catch before
the program ends, and names the log on the console.

### Settings: .inix, and carry the old file over

`configs\<App>.inix` through `homer.paths.configs()` and `homer.inix`. Read the
old `.ini` when no `.inix` exists; delete it when the new one is first saved;
map the old key names onto the new. Test the carry-over: urlCheck's was run
against a real old file before delivery.

### WinForms through pythonnet keeps its own dialog

`homer.lbc` is wx. A program already on WinForms through pythonnet keeps its
dialog and uses the kit's other modules, and follows Lbc's rules by hand:
each label takes the tab stop just before its field -- WinForms names a text
box from the label before it in tab order -- and no field sets an
AccessibleName equal to its label. `check.py`'s naming check now reads Python
functions as a window's builders, so it catches the second.

### F11 in a Python program

`elevate.configure(owner, repo, version)` at startup; in the dialog's KeyDown,
F11 calls `elevate.offer(hwnd)` -- `frm.Handle.ToInt64()` in WinForms,
`frame.GetHandle()` in wx. When it returns True the setup program is running,
and the dialog closes.

### The old layout on disk: renames Windows will not do for you

Unzipping `ReadMe.md` over `README.md` replaces the content and keeps the old
capitals. The build's carry-over section renames by exact case -- through
`git mv -f` when git tracks the file, so the repository follows -- and deletes
a moved document (`announce.md`, `CamelType_Python.md`) only once its
replacement exists.

### The whitelist left out every file named inside a folder

Not a Python problem, but urlCheck found it. `tidy` wrote `/*` and then
`!/help/Announce.md`; `/*` ignores the folder `help` itself, git never looks
inside an ignored folder, and so every file named one by one in a subfolder
was silently left out of the repository -- in `help\`, and in `scripts\`,
which the rules above say must be named one by one. Tested with git: 15 of
urlCheck's 34 named files were staged. Kit 1.43.0's `tidy` puts the folder back
and re-ignores its contents first (`!/help/`, `/help/*`), then the files: all
34 staged. **Every app whose RepoFiles.txt names files inside a folder should
run `scripts\tidy --gitignore` and push**, and check GitHub for the files that
never went up.

### Checks that caught a Python app out

- `check`'s smoke test looked only at the top of the project; it now looks in
  `exec` first. This affected every app moved to the layout, C# included.
- `check`'s key check read a whole Python file as one window and counted
  `&amp;` as a trigger letter. It now starts a new owner at each top-level
  `def` and skips HTML entities.

## Installer template: the program from exec, the documents from help

Found by urlCheck's first build on the kit. `Templates\_APP__setup.iss` named
the program and the documents at the top of the project, while every build in
the Homer layout -- the Python template included -- leaves the program in
`exec\` and the documents in `help\`. Since 1.43.1 the template takes the
program from `exec\` when it is there (an `#if FileExists` choice at compile
time) and ships `help\*.md` and `help\*.htm`. `AppLaunchParams` says what the
program is started with after the Results box, matching its shortcut.

**The installer pattern is the template's, even with nothing to install.**
urlCheck registers no component, and still includes `HomerComponents.iss` from
the kit the build names, calls `homerNoteTicked` from `NextButtonClick`, shows
the Results box and only then starts the program. The next component is one
`homerAdd`, three `[Run]` entries and one `addAction`, not a new installer.

## The kit renames only where it should

buildHomerDev's renaming rewrites old script names in the kit's own files,
skipping the lines whose job is to name the old scripts. It knew the C#
template's retired loop and not the Python template's `retiredTools=` line,
and on its first 1.43.0 run turned that list into the current tools' names --
which an app would then have deleted after refreshing them. Any list whose
job is to name old things must be recognised by the renaming, or it will be
"corrected". Kit 1.43.1 skips both and ships the template whole again.

## Installer template: read the previous version once

Found while writing urlCheck's installer. The template read the previous
install's version lazily, and a fresh install has none to cache, so every later
call read the registry again. The finish page's `Check:` functions run after
setup has written its own uninstall key, found it, and a fresh install was
offered "Update the JAWS scripts" in place of "Install". Kit 1.43.0 reads it
once in `InitializeSetup`. **An app whose installer was made from the template
before 1.43.0 has the same fault** and needs the same two lines changed:
`sPriorVersion := priorVersion();` in `InitializeSetup`, and `isFreshInstall`
reduced to `Result := (sPriorVersion = '');`, with `priorVersion` moved above
`InitializeSetup`.

## The migration, step by step

For an app that has not yet moved to the kit. Build green after every step;
each is checkable by `scripts\check` at the end. The order matters: the
contract first without moving files, then the layout one group at a time.

1. **Install the kit**: unzip `HomerDev.zip` into `C:\HomerDev`; run
   `buildHomerDev`. It renames any old-named scripts in place, fetches the
   voices, and says "0 problems found".
2. **Read the app's installer as it is**, before touching anything, and write
   down what its finish page offers. That list, and nothing from the
   template's examples, is what the new installer offers.
3. **Map every reference** to every file that will move, in every language
   the app uses. Keep the map; a move is finished when a grep for the old
   path finds nothing live.
4. **The contract, moving nothing.** Rewrite the build from
   `Templates\build_APP_.cmd`, or wrap an existing engine in a
   `build.cmd` that carries the contract: kit detection and a trimmed
   `kitNeeded` comparison; the kit's C# compiled in by Roslyn and no local
   copies; the refresh loop naming only the tools this app uses and saying
   when one is missing; the retired loop including the renamed names;
   `fixEncoding` with `-build`; one log per session in `logs`. Pass lists to
   PowerShell semicolon-joined. Build green.
5. **Write `RepoFiles.txt` and `LocalFiles.txt`** (start from
   `Templates\LocalFiles.txt`): scripts named one by one, never `scripts\`
   wholesale; both `.md` and `.htm` of every document; no `local:` section;
   `release.*`, `exec/`, `logs/`, `version.txt` in `LocalFiles.txt`.
6. **The layout, one group per build**: documents to `help`, reader scripts
   to `scripts\jaws`, binaries to `exec`, configuration to `configs`,
   starters to `templates`, the app's own tools to `scripts`. For each group:
   move, repoint every reference from the map, make moved scripts find the
   project with the `$pathHere`/`$pathRoot` rule, have the build carry across
   any file the delivery did not, retire the old copies once replacements
   exist, build green.
7. **The installer from `Templates\_APP__setup.iss`** with
   `HomerComponents.iss`: only the components from step 2; a `Check:` on
   every reader line; relative `Source:` lines; install scripts run
   directly; `[UninstallDelete]` naming only what the app made for itself;
   `/DHomerDev=` passed by the build. Build green.
8. **Generate what can be generated**: every `.htm` from its `.md` in the
   build; any hotkey list or summary from the key tables. Make document
   checks stop the build.
9. **Write `accept.inix`** (from `Templates\accept.inix`): what done means.
10. **Write the first walk**, `help\Tutorial_00_Overview.inix`, if the app is
    to have tutorials, and add the tutorial tools to the refresh loop then.
11. **Create the repository** with `create<App>Repo` if there is none;
    otherwise `scripts\tidy`.
12. **Build, check, push, release**: `build`, `scripts\check --build`,
    `scripts\push "Move to the kit."`, `scripts\release`.

## DbDo: what it has, what it still needs

DbDo is part way there. It has `RepoFiles.txt` and `LocalFiles.txt`,
`version.txt` and `Version.cs`, `accept.inix`, `uiTest.inix`, a `help`
folder with the full document set, a `templates` folder of starter
databases, `scripts\buildTutorials` and `TutorialFeed.xml`, and it compiles
against `C:\HomerDev\exec\CSharp` with `kitNeeded=1.25.0`. Thirteen kit versions
have passed since. To bring it current:

- **Raise `kitNeeded` to 1.38.3** and adopt the refresh and retire loops of
  section 3, so `check`, `checkTutorial`, `fixEncoding`, `push`,
  `unpushed`, `installCommon`, `tidy`, `installOllama` and
  `release` arrive in `scripts` and stay current. Add `Elevate.cs` to the
  compiler line.
- **Pass `-build`** where the build calls `scripts\buildTutorials.cmd`, and
  let the tool's console lines reach the screen (do not redirect its output
  into the build log); add `fixEncoding` before the compile.
- **Retire the near-duplicates**: `scripts\makeTutorial.cmd` and
  `makeTutorial.py` (the kit's `makeTutorials.py` does this); `bumpVersion`
  and `syncIssVersion` (the build's version step does this);
  `summarizeSetup` unless still wanted, in which case it goes to `scripts`.
- **Clear the root**: `build.py`, `build_convention.py`,
  `build_ios_tutorials.py`, `build_more.py`, `build_reads.py`,
  `build_recipes.py`, `build_tutorials.py`, `build_windows_tutorials.py`,
  `conform_samples.py`, `migratePrm.py` are one-off builders; those still
  used go to `scripts`, the rest to `notes`. The tutorial builders are
  superseded by `Tutorial_NN_*.inix` walks spoken by `buildTutorials`. The
  saved web pages ("RE DBDo did not import my Notes column.htm" and the like)
  go to `notes`. `DbDo_setup.exe` and `DbDo_JAWS.zip` are build products and
  belong in `exec` and in `LocalFiles.txt`, not in the root or the history.
  `installOllama.cmd` and `installModels.cmd` move to `scripts` (the first
  refreshed from the kit, the second DbDo's own). `README.md` becomes
  `ReadMe.md`.
- **Installer**: install scripts from `scripts\` to `{app}\scripts`; the
  three-group finish page and the Results box from ticked boxes; the
  reader scripts (`DbDo_JAWS.zip` unpacked into `scripts\jaws`) installed by
  `installScreenReaderSupport.cmd`.
- **Walks**: keep `help\Tutorial_NN_*.inix` as the source of every
  tutorial; run `checkTutorial`; name no screen reader.
- Then `check --build` should pass and `release` will carry it.

## EdSharp: the full migration

EdSharp has not moved yet: about eighty files at the root, its own copies
of `Inix.cs`, `KeyMap.cs`, `Lbc.cs`, `Say.cs`, `Web.cs` and `inixVert.cs`, a
`BuildEdSharp.ps1` driven by `BuildEdSharp.cmd`, the version living only as
`AppVersion` in `EdSharp_Setup.iss`, and a `scripts` folder that holds the
JAWS scripts rather than tools. Its `tidyRepo`, `repoPolicy`, `moveNotes`,
`restoreMissing`, `prepareAuditFixes`, `applyConvertPolicy`,
`dropLatexJawsKeys`, `auditEdSharp` and `summarizeSetup` are earlier
editions of what the kit now does. Follow the ten steps above, with these
particulars:

- **Folders**: `EdSharp.md`, `Announce`, `Development` (rename to
  `Developer`), `FAQ`, `History`, `Hotkeys`, `Tutorial` and `Tutorials`
  (merge into one `Tutorials`) go to `help`, with their `.htm`; the
  `CamelType_*` documents are the kit's now and the copies go. `Convert`
  becomes `configs\convert`; `Dictionaries` becomes `data\dictionaries`;
  `Samples` and `Snippets` become `templates\samples` and
  `templates\snippets`; the JAWS scripts (`.jss`, `.jsh`, `.jsd`, `.jkm`,
  `.JCF`, `EdSharp_Scripts_Setup.iss`) become `scripts\jaws`; the NVDA
  add-on goes to `exec` or `data`. `EdSharp.ini`, `EdSharp.inix`,
  `Tools.inix`, `Hotkeys.ini`, `Transform_Example.inix` go to `configs`
  (or `templates` for the example). `history.txt` and `lgpl.txt` are
  notes or licence text in `help`.
- **Binaries**: `EdSharp.exe`, `EdSharp.dll`, `Tektosyne.dll`, `Ude.dll`,
  `WeCantSpell.Hunspell.dll`, `nvdaControllerClient.dll`, `sqlean.exe` go
  to `exec`, and the build fetches what it can (`FetchUde.ps1`,
  `FetchConvertTools.ps1` become steps in the build, not separate scripts).
  Nothing binary is in `RepoFiles.txt`.
- **The shared classes**: EdSharp builds `EdSharp.dll` from the shared
  classes so its JScript.NET side can call them. Build that DLL from the
  kit's `exec\CSharp` files by path, and delete the copies. `inixVert.cs` is in
  the kit too.
- **Build script**: `buildEdSharp.cmd` (lowercase b) wrapping the
  PowerShell, with the kit detection, `kitNeeded`, `version.txt` stepped
  and written to both `Version.cs` and the `.iss`, the refresh and retire
  loops, `fixEncoding`, the tutorial call with `-build`. The version-from-
  tags logic in `BuildEdSharp.ps1` gives way to `version.txt`.
- **Install scripts** -- `installCodeModel`, `installGitHub`,
  `installJawsScripts`, `installNode`, `installOllama`, `installPandoc`,
  `installPdfTools`, `installPython`, `installTranslateModel` -- go to
  `scripts`, each calling `installCommon.cmd` for its log, `installOllama`
  refreshed from the kit, and the installer ships them from `scripts\` to
  `{app}\scripts` with the three-group finish page. `installJawsScripts`
  is the kit's `installScreenReaderSupport` pattern.
- **Retire**: `tidyRepo`, `repoPolicy`, `moveNotes`, `restoreMissing`,
  `prepareAuditFixes`, `applyConvertPolicy`, `dropLatexJawsKeys`,
  `auditEdSharp`, `summarizeSetup`, `ModernizePandocConfig`, and the root
  `release.cmd`/`.ps1` (the kit's replaces it) -- into `notes` if any is
  still wanted for reference, otherwise gone.
- **Walks**: EdSharp's `Tutorials.md` is prose; write the first
  `help\Tutorial_00_Overview.inix` from the template and the skill, and let
  the build speak it.

## FileDir: two branches, copied classes, binaries in the repository

FileDir is some of the way there. Its working branch, `master`, has
`version.txt` (5.0.88) stepped by the build and written to `Version.cs`, a
`RepoFiles.txt`, two tutorial scripts (`Tutorial.inix`,
`Tutorial_Tagging.inix`) with a `TutorialFeed.xml`, and `postPage`, which
publishes the guide to the `main` branch as a GitHub Pages site. But it
compiles against no kit: it carries copies of `Inix.cs`, `Log.cs`,
`Say.cs`, `Util.cs`, `Web.cs`, `Ollama.cs` and a lowercase `lbc.cs` whose
header says the namespace line is edited per project, and it copies
`Ude.dll` from the EdSharp folder when the file is missing. Its repository
holds binaries -- 7-Zip (`7z.exe`, `7z.dll`, `7zFM.exe`, `7zG.exe`, three
`.sfx`), `Burn2CD`, `AssocOn.exe` and `AssocOff.exe` with their `.bas`,
`Tektosyne.dll`, `ICSharpCode.SharpZipLib.dll`, `Ude.dll`,
`nvdaControllerClient.dll`, `FileDirScript.dll` -- named in a
`RepoFiles.txt` of an older format (a `Tracked:` line, which the current
`tidy` would read as a file name). Its `cleanFileDir`, `homerPolicy`,
`auditFileDir`, `buildTutorial`, `makeTutorial`, `summarizeSetup` and root
`release` are earlier editions of the kit's tools; the build is a
capital-B `BuildFileDir.ps1`; everything sits at the root, with the JAWS
scripts both there and in `scripts` (which holds only their installer
inputs). Follow the ten steps, with these particulars:

- **The two branches.** `main` is the published guide only; `master` is
  the project. Every kit tool acts on the branch checked out in the
  working folder, so make `master` the default branch on GitHub (so a
  download of the repository is the project, and `release` tags the
  right history), and keep `postPage` in `scripts` as the way
  `help\FileDir.md` reaches the Pages branch after a release. A branch
  whose only content is a copy of one document is a publishing target,
  not a project, and should never be what someone unzips to build from.
- **The shared classes.** Delete the seven copies and compile against
  `C:\HomerDev\exec\CSharp` with `using Homer;` -- the kit's classes live in the
  Homer namespace, so the per-project namespace edit ends. `Ollama.cs`,
  `Log.cs` and `Util.cs` are in the kit too. `Elevate.cs` beside `Lbc.cs`;
  `Elevate.configure` at startup, so F11 joins Alt+F1 About.
- **Binaries out of git, fetched by the build, into `exec`.** 7-Zip by
  winget (`7zip.7zip`) or its direct download; Ude by NuGet, as EdSharp's
  `FetchUde.ps1` does, into `exec` -- never copied from another project's
  folder; Tektosyne, SharpZipLib and the NVDA controller client by their
  NuGet or release downloads; `FileDirScript.dll` and `FileDir.exe` are
  build products. `AssocOn`/`AssocOff` and `Burn2CD` are the app's own
  small programs: their sources (`.bas`) stay in the repository and the
  built `.exe` goes to `exec` and `LocalFiles.txt`. Rewrite `RepoFiles.txt`
  in the current format, one path per line, and name no binary in it.
- **Folders.** `help` takes `FileDir.md`, `Announce`, `Developer`, `FAQ`,
  `History`, `Hotkeys`, `Tutorials`, their `.htm`, the walks renamed
  `Tutorial_00_Overview.inix` and `Tutorial_01_Tagging.inix`,
  `TutorialFeed.xml`, and `tutorials\Tutorial_00_Overview.mp3` (the root
  `Tutorial.mp3`); the `CamelType_*` and `Camel_Type_C#` documents are the
  kit's and the copies go. `scripts` takes the kit's tools, the install
  scripts (`installImageTools`, `installMediaTools`, `installMpv`,
  `installOllama` refreshed from the kit, `installPandoc`,
  `installPdfTools`, `installTranslateModel`), `postPage`, `makeKeyMap.py`,
  `pdfRich.py`, and `jaws\` for `FileDir.jss/.jsd/.jsh/.jkm/.jcf`,
  `Homer.jss/.jsd/.jsh`, `MSAA.jsh`, the `mpv.*` scripts, the `.jsb` files
  and `FileDir_Scripts_setup.iss`. `configs` takes `Hotkeys.inix`,
  `Convert.txt` and `Quick.txt` (as `.inix` if they are INI-shaped) and
  `FileDir.ini`; `data` takes `chimes.wav`. `makeTutorial.log` goes; logs
  live in `logs`.
- **Retire** `cleanFileDir.cmd/.py`, `homerPolicy.py`, `auditFileDir.py`,
  `buildTutorial.cmd/.ps1`, `makeTutorial.cmd/.py`, `summarizeSetup`, the
  root `release.cmd/.ps1` and `tagRelease_README.md`: `tidy`,
  `check`, `buildTutorials`, `makeTutorials` and the kit's
  `release` do these jobs.
- **Build and installer.** `buildFileDir.cmd` (lowercase b) with the kit
  detection, `kitNeeded`, the refresh and retire loops, `fixEncoding`, the
  tutorial call with `-build`, then the JScript.NET compile of
  `FileDirScript.dll` and the C# compile against the kit. `FileDir_setup.iss`
  ships install scripts from `scripts\` to `{app}\scripts`, with the
  three-group finish page and the Results box from ticked boxes; the JAWS
  scripts through `installScreenReaderSupport.cmd`. The guide's
  "dirsetup.exe" is stale text: the installer is `FileDir_setup.exe`, which
  is what `release` reads the version from. The desktop shortcut's
  Alt+Control+F is the sanctioned use of that key space and stays.
- **Walks.** Run `checkTutorial` over the two scripts before the build
  speaks them: they must name no screen reader, and the guide names JAWS
  freely, so the walks were likely written the same way.

## What HomerView looks like now, as the second worked example

`buildHomerView.cmd` carries the contract and wraps the proven PowerShell
engine, handing it the Roslyn compiler, the kit sources (semicolon-joined)
and the log path. The engine: step 0 runs `makeDocs` (hotkeys, the hotkey
`.inix`, the start page, and the guide checks that stop the build) and makes
each `.htm`; step 1 checks the installer script and parses the PowerShell it
runs; step 2 compiles the JAWS scripts with every installed JAWS and runs the
agreement checks; step 3 builds the bridge into `exec`; step 4 builds the
NVDA add-on from `version.txt`; step 5 compiles the installer with
`/DHomerDev=`. The layout: `configs\Hotkeys.inix` (generated), `exec\`,
`help\`, `logs\`, `scripts\` (its own tools and the kit's six it uses),
`scripts\jaws\`, `templates\Start.htm` (generated). The installer offers the
NVDA add-on where NVDA is, the JAWS scripts where JAWS is, and pandoc in the
kit's install/update/reinstall shapes. 1.48.62 built with no errors and no
warnings.

## What HomerScribe looks like now, as the worked example

`C:\HomerScribe`: `HomerScribe.cs`, `PdfRead.cs`, `buildHomerScribe.cmd`,
`HomerScribe_setup.iss`, `ReadMe.md/.htm`, `License.md/.htm`,
`RepoFiles.txt`, `LocalFiles.txt`, `accept.inix`; `help\` with the guide,
Developer, History, Hotkeys, Announce, Tutorials, `Tutorial_00_Overview`
through `Tutorial_06_NewerVersion.inix` and `tutorials\*.mp3`; `scripts\`
with the kit's tools plus `installExifTool`, `installModels`,
`installPandoc`, `installTesseract`, `installWhisper`, `pdfPages`; `templates\`
with the context examples; `exec\` with the program, its DLLs and the
fetched tools; `logs\`. Its `buildHomerScribe.cmd` and `HomerScribe_setup.iss`
are the fullest current examples of everything above, and its
`help\Developer.md` names the four scripts and their order.

## Summary of the rules, one line each

- Compile against `C:\HomerDev\exec\CSharp`; carry no copies; list `Elevate.cs` with `Lbc.cs`.
- State `kitNeeded`; stop with a message when the kit is older.
- Refresh the kit's scripts into `scripts` on every build; delete retired ones.
- Standard folders with distinct first letters; subfolders are fine.
- `RepoFiles.txt` names what git carries; `LocalFiles.txt` what stays local; `.gitignore` is generated.
- `version.txt` only on the developer's machine; the build steps it and writes `Version.cs`.
- The four scripts: build, push, tidy, release; tools climb out of `scripts`.
- Shared components machine-wide; the app's DLLs in `exec`; installers admin and machine-wide.
- The build fetches what it needs; only the kit's build fetches the voices.
- One log per run in `logs`; a succinct console that names each thing as it is made.
- Homer encoding everywhere; `fixEncoding` before every compile; delete zero-byte files.
- Finish page in three groups; Results box from ticked boxes; OK listed first.
- `Elevate.configure` for F11.
- Walks in `Tutorial_NN_*.inix`; four beats; name silence; name no screen reader; `checkTutorial` first.
- `check` decides whether `release` may release.
- Refresh only the kit tools the app uses, and say when one is missing.
- Never name `scripts\` wholesale in `RepoFiles.txt`; `release.*` stays out of git.
- No `local:` section in `RepoFiles.txt`; local files go in `LocalFiles.txt`.
- Name both the `.md` and the `.htm` of every document you commit.
- `version.txt` is the source; everything else is written from it every build.
- Offer only the components the app's pre-move installer offered.
- Every screen reader line on the finish page has its `Check:`.
- `Source:` lines are relative; install scripts run directly, not via `{cmd}`.
- `[UninstallDelete]` names only what the app made for itself.
- Map every reference before moving a file; move one group per build.
- A delivery that moves a folder carries only its own files: the build carries the rest.
- A script in `scripts\` finds the project one level up; so does a program in `exec`.
- One source for anything with two copies; generate the rest every build.
- A check that only prints is ignored: make document checks fail the build.
- Pass lists from cmd to PowerShell semicolon-joined; refuse an empty list.
- Compile the kit's C# with Roslyn; the Framework csc stops at C# 5.
- Trim version numbers before comparing, and tell a parse failure from an old kit.
- When an archive is older than the working kit, change the working kit in place.
- Patch a kit script at one exact line, with a marker, logged when not found; run twice.
- Never run anything between a command and its `if errorlevel` check.
- Probe with git or gh under `$ErrorActionPreference = 'SilentlyContinue'` in PowerShell 5.1.
- When GitHub says a repository moved, point origin at the new location.
- A Python app's build is `Templates\build_APP_Py.cmd` with its SETTINGS filled in.
- Name the kit's Python modules with `--hidden-import`; never copy them into a standalone app.
- No kit file shares a name with anything a build generates (`version.py`).
- PyInstaller: program to `exec`, scratch and `.spec` to `work`, icon by full path.
- A program in `exec` finds `help` through `homer.paths.installedFolder()`.
- The session log is kept every run; an app's own log option is an extra copy.
- Carry an old settings file over, and prove it on a real one.
- A WinForms dialog through pythonnet keeps its code and follows Lbc's rules by hand.
- Read an installer's previous version once, in `InitializeSetup`.
- A whitelist that names a file in a subfolder must first put the subfolder back.
