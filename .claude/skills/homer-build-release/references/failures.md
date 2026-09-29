# Failures that have cost a run

## Contents
- Release
- Check
- Tidy and push
- Build
- Installer

Each entry: the symptom in the log, the cause, the fix.

## Release

- **"ALREADY RELEASED" for a version never published.** A draft release or a
  local tag from an interrupted run. release reads GitHub's list as JSON and
  publishes a draft (`--draft=false --latest`). If it persists, the version
  truly exists: build without `nobump`.
- **Published, but an old installer.** An old `<App>_setup.exe` at the top was
  found first. Installers are built at the top (`OutputDir=.`); a build removes
  any copy left in `exec`.
- **"latest release is vX, not vY".** The new release is a draft or
  pre-release; the release page says which.
- **Release hangs with no output.** An acceptance command waited for a key;
  check gives commands empty input and names each as it starts.
- **A release republishes yesterday's installer.** The last build failed, so
  the installer at the top is the old one, and version.txt matches it. release
  now reads the newest build log and stops unless it says the build succeeded;
  `-Force` overrides.
- **Every tag reads as unreleased** in Windows PowerShell 5.1:
  `ConvertFrom-Json` writes a JSON array as one object, so
  `@(... | ConvertFrom-Json)` holds one element. Assign, then `foreach`.
- **PowerShell parse error.** `"$var: text"` reads as a drive; write
  `${var}:`.

## Check

- **accept: a `findstr` check fails** though the text is there. findstr reads
  a backslash as an escape even in `/c:` text: write `findstr /l /c:"help\\*.htm"`.
- **keys: an Alt+Control combination** is reserved for desktop shortcuts
  except the app's own shortcut (read from the installer's HotKey) and
  navigation keys. Only NVDA `kb:` gestures count in Python.
- **naming: an accessible name repeating a label** (read twice). Put the label
  before its field in tab order instead.
- **encoding: a generated file lacks the BOM.** The generator must write
  UTF-8 with BOM and CRLF (`encoding="utf-8-sig", newline="\r\n"`).
- **documents: no .htm for License.** Every `.md` needs its Pandoc `.htm`.
- **empty: zero-byte files.** tidy deletes them, including empty logs.

## Tidy and push

- **Push commits files that belong off GitHub.** The whitelist was not
  rewritten (an old tidy, or a script calling an old name); run the build to
  refresh `scripts`, then tidy.
- **A needed file untracked.** RepoFiles.txt does not name it (an installer's
  Source lines do not count), or a LocalFiles.txt pattern catches it and
  RepoFiles.txt names it only by folder. Name it exactly.
- **Capital-letter renames do not reach git.** Windows git treats a case-only
  change as none: `git rm --cached <Old>` then `git add <new>`, never renaming
  a running script.

## Build

- **"kit not found" right after the kit moved.** The app's build script is
  its own copy and still looks for the kit's old layout: unzip the app's
  latest `<App>.zip`, which carries the build script that knows the new one.
- **A failed build left version.txt one ahead.** Builds now put the number
  back when they fail; an old build script does not, so the release refuses
  (installer older than version.txt). Build again with the current script.

- **"kit not found" or "Update HomerDev"**: build the kit first; the app's
  `kitNeeded` is newer than the kit on disk.
- **A script calls an old kit name** (checkHomerApp, gitPush, homerTidy,
  tagRelease, homerInstall): the build retires old copies; rebuild.
- **Version in the installer one behind.** The installer read version.txt
  before the build wrote it; pass the build's number to Inno
  (`/DBuildVersion=`).

## Installer

- **JAWS scripts that work on one machine and not another.** A compiled `.jsb`
  was shipped, built by another JAWS version. Ship `.jss` sources only; the
  installer compiles them with each installed version's `scompile.exe`, and
  `.jsb` is never pushed.
- **A `.jsb` still in the installer** after the JAWS zip left it out. An
  installer's `Source: "scripts\jaws\*"` takes every file there, compiled
  ones included (FileDir 5.0.122): add `Excludes: "*.jsb"`, and have the build
  delete any `.jsb` left in `scripts\jaws`.

- **"File not found: C:\HomerDev\exec\Templates\HomerComponents.iss".** A
  build that works out the kit's folder by counting levels above a C# source
  counts wrong since the sources moved into `exec\CSharp`. Find the kit as the
  nearest folder above that holds `Templates\HomerComponents.iss`.

- **A component offered for install that is present.** Check the setup log's
  `Component <name>:` lines, which record what was found and the verb offered.
- **JAWS scripts never installed.** The finish page ran a script the installer
  put elsewhere; paths in [Files] and [Run] must agree.
- **Inno Setup: "BEGIN expected".** A `;` comment inside [Code]; Pascal
  comments are `//`.
