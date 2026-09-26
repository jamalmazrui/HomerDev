# HomerDev Update: bringing a Homer app up to the current kit

*A briefing on the learnings, decisions and techniques of HomerDev as of
25 September 2026 (kit 1.38.3), written so that another Homer app -- DbDo,
part way there; FileDir, some of the way; EdSharp, not yet started -- can
take up the kit's code,
concepts and structure with less pain than HomerScribe went through. It is
a developer document: technical, dated, and specific about what went wrong.*

# What the kit is

`C:\HomerDev` is one repository holding everything the Homer apps share:

- `CSharp\` -- the shared classes an app compiles against: `Elevate.cs`,
  `Inix.cs`, `KeyMap.cs`, `KeyName.cs`, `Lbc.cs`, `Log.cs`, `Mdi.cs`,
  `Ollama.cs`, `Paths.cs`, `PdfRead.cs`, `Say.cs`, `Util.cs`, `Web.cs`,
  `inixVert.cs`. An app never carries a copy; it names the kit's file on the
  compiler line.
- `homer\` -- the same for Python: `inix.py`, `lbc.py`, `log.py`, `mdi.py`,
  `paths.py`, `say.py`, `util.py`, `web.py`.
- `scripts\` -- the tools every app inherits, refreshed into its own
  `scripts` folder on every build: `buildTutorials`, `checkHomerApp`,
  `checkTutorial`, `fixEncoding`, `gitPush`, `gitUnpushed`, `homerInstall`,
  `homerTidy`, `installOllama`, `installScreenReaderSupport`,
  `makeTutorials`, `tagRelease`.
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

# The contract between an app and the kit

## 1. Find the kit, state the version needed

Every build script begins the same way. From `buildHomerScribe.cmd`:

```
set "homerDev="
if defined HomerDev if exist "%HomerDev%\CSharp\Lbc.cs" set "homerDev=%HomerDev%"
if not defined homerDev if exist "C:\HomerDev\CSharp\Lbc.cs" set "homerDev=C:\HomerDev"
if not defined homerDev if exist "%CD%\CSharp\Lbc.cs" set "homerDev=%CD%"
if not defined homerDev (
  echo HomerScribe needs the Homer Development Kit and cannot find it.
  echo Unzip HomerDev.zip into C:\HomerDev, or set the HomerDev environment variable.
  exit /b 1
)
set "homerVer=0.0.0"
if exist "!homerDev!\version.txt" set /p homerVer=<"!homerDev!\version.txt"
set "kitNeeded=1.38.3"
powershell -NoProfile -Command "if ([version]'!homerVer!' -lt [version]'!kitNeeded!') { exit 1 } else { exit 0 }" >nul
if errorlevel 1 (
  echo HomerScribe needs HomerDev !kitNeeded! or later, and the kit is !homerVer!.
  echo Unzip HomerDev.zip into C:\HomerDev, then build again.
  exit /b 1
)
```

`kitNeeded` is raised whenever the app starts depending on something new in
the kit. A build against an older kit stops with that message rather than
failing somewhere inside the compiler.

## 2. Compile against the kit's sources; carry no copies

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

## 3. Refresh the kit's scripts into the app on every build

One source of truth. The app's build copies them in; a fix in the kit
reaches every app on its next build; nothing is edited in place.

```
if not exist "scripts" mkdir "scripts"
for %%F in (buildTutorials.cmd buildTutorials.ps1 checkHomerApp.cmd checkHomerApp.py checkTutorial.cmd checkTutorial.py fixEncoding.cmd fixEncoding.py gitPush.cmd gitUnpushed.cmd gitUnpushed.py homerInstall.cmd homerTidy.cmd homerTidy.py installOllama.cmd makeTutorials.py tagRelease.cmd tagRelease.ps1) do (
  if exist "!homerDev!\scripts\%%F" copy /y "!homerDev!\scripts\%%F" scripts\ >nul
)
rem Retired kit scripts an app may still carry from an earlier refresh: gone.
for %%F in (cleanDir.cmd cleanDir.py gitRelease.cmd homerPolicy.py installTools.cmd sayTutorial.cmd sayTutorial.py tidyRepo.cmd tidyRepo.py) do (
  if exist "scripts\%%F" del /q "scripts\%%F"
)
```

`installModels.cmd` is the one install script an app keeps as its own,
because it names the app's models. `installScreenReaderSupport.cmd` is
refreshed only by apps that ship reader scripts.

## 4. The folder layout, and why the first letters differ

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

## 5. RepoFiles.txt and LocalFiles.txt

Two lists decide what git carries. `RepoFiles.txt` names the files and
folders the repository holds (a trailing slash names a folder wholesale; a
wildcard is allowed). `LocalFiles.txt` names what stays on this disk and is
never pushed: `exec/`, `logs/`, `work/`, `notes/`, `packages/`, generated
audio, anything fetched. `homerTidy` writes `.gitignore` as a **whitelist**
from `RepoFiles.txt` -- everything ignored, then exactly the named files
allowed -- and `gitPush` rewrites it before every push. So `git add -A`
means "add everything the project has named", never "everything in the
folder".

The lesson behind this, 25 September: a project with no `RepoFiles.txt`
swept 480 fetched voice files into a commit. `gitPush` now stages nothing
without the list, and refuses any commit that stages a file over 10 MB.

## 6. The four scripts, and the order they run in

1. `build<App>` -- steps `version.txt`, writes `Version.cs`, builds the
   program and the installer, speaks any tutorial without audio, puts the
   project's own files into the Homer encoding, refreshes the scripts.
2. `scripts\gitPush "message"` -- rewrites the whitelist, adds what it names,
   commits, pushes, shows the status.
3. `scripts\homerTidy --do-it` -- the periodic clean: strays into `notes`,
   fetched things deleted, zero-byte files deleted, whitelist rewritten,
   strays untracked, commit. `--gitignore` alone rewrites the whitelist.
4. `scripts\tagRelease` -- runs the app's checks (`checkHomerApp --build`),
   then tags the pushed commit with the version stamped in
   `<App>_setup.exe` and publishes the installer as a GitHub release.
   `-SkipCheck` when the checks have just run.

And `scripts\gitUnpushed` undoes a local commit that should not go up,
keeping every file.

Every tool takes the project to be the folder it is run in, **or the parent
when that folder is the project's `scripts` or `exec`** -- so
`cd scripts` and `gitPush` is the same as running it at the top. Never keep
copies of these tools in `C:\bin` or anywhere on the PATH: they go stale
there and run instead of the app's own. The kit's build deletes such
copies when it finds them.

## 7. Versions

`version.txt` holds the current number and lives only on the developer's
machine -- never in a delivered zip, never in the repository (it is in
`LocalFiles.txt`). The build steps it, writes `Version.cs` from it, and
stamps the installer; `build<App> nobump` keeps the number. `tagRelease`
reads the version from the installer's own resource, so the tag can never
disagree with what was built.

## 8. Shared components install machine-wide

Whisper, Tesseract, Pandoc, ExifTool, ffmpeg, yt-dlp, Ollama and the like
go to their own default machine-wide directories -- `C:\Program Files\...`
-- so every Homer app finds and shares one copy, and an app upgrade (which
replaces the app's folder) cannot destroy them. Libraries the app links
(its DLLs) belong beside the executable in `exec`. An installer is
machine-wide and requires admin; there is no per-user fallback. Anyone
wanting a portable copy uses the zip.

## 9. The build fetches what it needs

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

## 10. Logs, console and encoding

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
- `homerInstall.cmd` is the logging half of every install script: each
  `install<Thing>.cmd` calls it to open a log, run a command, record the
  exit code. Every install script says "Downloading" before a long step.

## 11. The installer and its finish page

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

**List OK first** in every `Lbc.runWithButtons` call: Lbc makes the first
label the default button, and a wizard once opened Help on Enter because
"Help" was listed first. A length is spoken in words ("Took 19 minutes",
`Util.spokenLength`); a clock reading is a position.

## 12. F11 and the version box

`Elevate.configure(owner, repo, version)` at startup. Lbc's Help box then
carries a Version section; when a newer release exists on GitHub, the box
offers Yes (default) to fetch `<App>_setup.exe` and run it. F11 is the key
(elevate sounds like eleven). This is how a user updates without visiting
a web page.

## 13. Tutorials: the spoken walks

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
`Templates\skills\homer-tutorial\SKILL.md` teaches an AI to write them.

## 14. The check, and what "done" means

`scripts\checkHomerApp` (with `--build` to make the build itself evidence)
checks: the documents present, each with its `.htm` (ReadMe, License, the
app's guide, Developer, History, Hotkeys; Tutorials where walks exist);
`RepoFiles.txt` present and `.gitignore` the generated whitelist; the Homer
encoding of the project's own files; evidence of logging; the build script
named after the folder returning 0; `accept.inix` stating what done means.
`tagRelease` refuses to release when it fails. Its report goes in
`logs\<App>-evidence-<stamp>.md`.

# Lessons paid for, with dates

- **25 Sep, `%*` is not reset by a bare `call`.** A build run as
  `buildHomerScribe nobump` called the tutorial tool with no arguments, and
  "nobump" arrived there as a script name. Every call from a build passes an
  explicit argument (`-build`), and every tool ignores dash-arguments it
  does not know.
- **25 Sep, Windows does not tell `Scripts` from `scripts`.** A move-pair
  from an earlier layout deleted the freshly delivered
  `scripts\homerInstall.cmd`, taking it for the stale copy. Any list that
  moves files must skip a pair whose two sides are the same file.
- **25 Sep, similar-sounding names cause wrong tools to run.** `cleanDir`
  beside `homerTidy`, `gitRelease` beside `tagRelease`, `sayTutorial` beside
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

# The migration, step by step

For an app that has not yet moved to the kit. Each step is checkable by
`scripts\checkHomerApp` at the end.

1. **Install the kit**: unzip `HomerDev.zip` into `C:\HomerDev`; run
   `buildHomerDev`. It fetches the voices and says "0 problems found".
2. **Lay out the folders**: `configs`, `data`, `exec`, `help`, `logs`,
   `scripts`, `templates` as needed; move every document but ReadMe and
   License into `help`; the built program and its DLLs into `exec`; reader
   scripts into `scripts\jaws`; samples and starters into `templates`.
   Use `homerTidy` (plan first, then `--do-it`) to carry strays into `notes`.
3. **Write `RepoFiles.txt` and `LocalFiles.txt`** (start from
   `Templates\LocalFiles.txt`). Name the sources, the documents, `help/`,
   `scripts/`, the lists, the installer script, `ReadMe`, `License`. Do not
   name the Homer classes, `version.txt`, `exec/`, `logs/`.
4. **Delete the app's copies of the Homer classes** and compile against
   `C:\HomerDev\CSharp` (section 2). Add `Elevate.configure` at startup.
5. **Rewrite the build script from `Templates\build_APP_.cmd`**: the kit
   detection and `kitNeeded`; `version.txt` stepped and `Version.cs`
   written; the refresh and retire loops; `fixEncoding`; the tutorial call
   with `-build`; compile; installer. Name it `build<App>.cmd`, lowercase b,
   and `.cmd` first -- a `.ps1` needs a `.cmd` wrapper that forwards its
   arguments.
6. **Rewrite the installer from `Templates\_APP__setup.iss`** with
   `HomerComponents.iss`: install scripts from `scripts\` to `{app}\scripts`,
   the three-group finish page, the Results box from ticked boxes,
   machine-wide and admin.
7. **Write `accept.inix`** (from `Templates\accept.inix`): what done means.
8. **Write the first walk**, `help\Tutorial_00_Overview.inix`, from the
   template; run `scripts\checkTutorial`; let the build speak it.
9. **Create the repository** with `create<App>Repo` (from the template) if
   there is none; otherwise `homerTidy --do-it` to untrack strays and write
   the whitelist.
10. **Build, check, push, release**: `build<App>`, `scripts\checkHomerApp
    --build`, `scripts\gitPush "Move to the kit."`, `scripts\tagRelease`.

# DbDo: what it has, what it still needs

DbDo is part way there. It has `RepoFiles.txt` and `LocalFiles.txt`,
`version.txt` and `Version.cs`, `accept.inix`, `uiTest.inix`, a `help`
folder with the full document set, a `templates` folder of starter
databases, `scripts\buildTutorials` and `TutorialFeed.xml`, and it compiles
against `C:\HomerDev\CSharp` with `kitNeeded=1.25.0`. Thirteen kit versions
have passed since. To bring it current:

- **Raise `kitNeeded` to 1.38.3** and adopt the refresh and retire loops of
  section 3, so `checkHomerApp`, `checkTutorial`, `fixEncoding`, `gitPush`,
  `gitUnpushed`, `homerInstall`, `homerTidy`, `installOllama` and
  `tagRelease` arrive in `scripts` and stay current. Add `Elevate.cs` to the
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
- Then `checkHomerApp --build` should pass and `tagRelease` will carry it.

# EdSharp: the full migration

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
  kit's `CSharp` files by path, and delete the copies. `inixVert.cs` is in
  the kit too.
- **Build script**: `buildEdSharp.cmd` (lowercase b) wrapping the
  PowerShell, with the kit detection, `kitNeeded`, `version.txt` stepped
  and written to both `Version.cs` and the `.iss`, the refresh and retire
  loops, `fixEncoding`, the tutorial call with `-build`. The version-from-
  tags logic in `BuildEdSharp.ps1` gives way to `version.txt`.
- **Install scripts** -- `installCodeModel`, `installGitHub`,
  `installJawsScripts`, `installNode`, `installOllama`, `installPandoc`,
  `installPdfTools`, `installPython`, `installTranslateModel` -- go to
  `scripts`, each calling `homerInstall.cmd` for its log, `installOllama`
  refreshed from the kit, and the installer ships them from `scripts\` to
  `{app}\scripts` with the three-group finish page. `installJawsScripts`
  is the kit's `installScreenReaderSupport` pattern.
- **Retire**: `tidyRepo`, `repoPolicy`, `moveNotes`, `restoreMissing`,
  `prepareAuditFixes`, `applyConvertPolicy`, `dropLatexJawsKeys`,
  `auditEdSharp`, `summarizeSetup`, `ModernizePandocConfig`, and the root
  `tagRelease.cmd`/`.ps1` (the kit's replaces it) -- into `notes` if any is
  still wanted for reference, otherwise gone.
- **Walks**: EdSharp's `Tutorials.md` is prose; write the first
  `help\Tutorial_00_Overview.inix` from the template and the skill, and let
  the build speak it.

# FileDir: two branches, copied classes, binaries in the repository

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
`homerTidy` would read as a file name). Its `cleanFileDir`, `homerPolicy`,
`auditFileDir`, `buildTutorial`, `makeTutorial`, `summarizeSetup` and root
`tagRelease` are earlier editions of the kit's tools; the build is a
capital-B `BuildFileDir.ps1`; everything sits at the root, with the JAWS
scripts both there and in `scripts` (which holds only their installer
inputs). Follow the ten steps, with these particulars:

- **The two branches.** `main` is the published guide only; `master` is
  the project. Every kit tool acts on the branch checked out in the
  working folder, so make `master` the default branch on GitHub (so a
  download of the repository is the project, and `tagRelease` tags the
  right history), and keep `postPage` in `scripts` as the way
  `help\FileDir.md` reaches the Pages branch after a release. A branch
  whose only content is a copy of one document is a publishing target,
  not a project, and should never be what someone unzips to build from.
- **The shared classes.** Delete the seven copies and compile against
  `C:\HomerDev\CSharp` with `using Homer;` -- the kit's classes live in the
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
  root `tagRelease.cmd/.ps1` and `tagRelease_README.md`: `homerTidy`,
  `checkHomerApp`, `buildTutorials`, `makeTutorials` and the kit's
  `tagRelease` do these jobs.
- **Build and installer.** `buildFileDir.cmd` (lowercase b) with the kit
  detection, `kitNeeded`, the refresh and retire loops, `fixEncoding`, the
  tutorial call with `-build`, then the JScript.NET compile of
  `FileDirScript.dll` and the C# compile against the kit. `FileDir_setup.iss`
  ships install scripts from `scripts\` to `{app}\scripts`, with the
  three-group finish page and the Results box from ticked boxes; the JAWS
  scripts through `installScreenReaderSupport.cmd`. The guide's
  "dirsetup.exe" is stale text: the installer is `FileDir_setup.exe`, which
  is what `tagRelease` reads the version from. The desktop shortcut's
  Alt+Control+F is the sanctioned use of that key space and stays.
- **Walks.** Run `checkTutorial` over the two scripts before the build
  speaks them: they must name no screen reader, and the guide names JAWS
  freely, so the walks were likely written the same way.

# What HomerScribe looks like now, as the worked example

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

# Summary of the rules, one line each

- Compile against `C:\HomerDev\CSharp`; carry no copies; list `Elevate.cs` with `Lbc.cs`.
- State `kitNeeded`; stop with a message when the kit is older.
- Refresh the kit's scripts into `scripts` on every build; delete retired ones.
- Standard folders with distinct first letters; subfolders are fine.
- `RepoFiles.txt` names what git carries; `LocalFiles.txt` what stays local; `.gitignore` is generated.
- `version.txt` only on the developer's machine; the build steps it and writes `Version.cs`.
- The four scripts: build, gitPush, homerTidy, tagRelease; tools climb out of `scripts`.
- Shared components machine-wide; the app's DLLs in `exec`; installers admin and machine-wide.
- The build fetches what it needs; only the kit's build fetches the voices.
- One log per run in `logs`; a succinct console that names each thing as it is made.
- Homer encoding everywhere; `fixEncoding` before every compile; delete zero-byte files.
- Finish page in three groups; Results box from ticked boxes; OK listed first.
- `Elevate.configure` for F11.
- Walks in `Tutorial_NN_*.inix`; four beats; name silence; name no screen reader; `checkTutorial` first.
- `checkHomerApp` decides whether `tagRelease` may release.
