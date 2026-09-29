# Audit checklist

## Contents
- Build script
- Layout
- Lists
- Installer
- Checks
- Version
- Elevate
- Documents and logging

Each item, then in brackets what it looked like when wrong.

## Build script

- Finds the kit by `exec\CSharp\Lbc.cs` (C#) or `exec\Python\log.py`
  (Python), and names the kit's files from there on the compiler line or
  PyInstaller's path. [The old `CSharp` or `homer` paths: "no kit found".]
- Sets `kitNeeded` to the kit it was written for, and stops with a clear
  message when the kit is older.
- Copies the kit's tools into `scripts` under their current names -- check,
  push, release, tidy, unpushed, finish, fixEncoding, installCommon, the
  tutorial tools -- and deletes the old names (checkHomerApp, gitPush,
  gitUnpushed, homerFinish, homerInstall, homerTidy, tagRelease). [A push that
  ran an old tidy and committed files that belong off GitHub.]
- Deletes copies of the kit's classes at the top of the project; the kit's
  are compiled instead.
- Steps `version.txt` at the start and puts it back if the build fails; or
  writes it only on success. [An installer one version behind version.txt.]
- Starts and ends its log with the ISO lines `build start app=<App>` and
  `build end result=succeeded|failed`, and every failure path goes through
  the end line. [A log that ends mid-way; "result=unfinished".]
- Never closes or kills a running copy of the app.

## Layout

- `exec` holds the built program and its libraries; `scripts` the tools and
  install scripts; `help` every document but ReadMe and License; `configs`,
  `data`, `templates` as used. [Documents at the top; JAWS scripts beside the
  program.]
- The installer is built at the top of the project (`OutputDir=.`).
  [Released from `exec`, or an old one at the top published instead.]
- Folders at the top start with different letters.
- A case-only rename is recorded in git with `git rm --cached` and `git add`,
  never by renaming a running script.

## Lists

- RepoFiles.txt names everything the repository carries, including what the
  installer ships; nothing else counts. [An NVDA add-on's modules about to be
  untracked because only its manifest was named.]
- A file the repository carries despite a LocalFiles.txt pattern is named
  exactly. [`Tektosyne.dll` under `*.dll`.]
- LocalFiles.txt names the installer, `version.txt`, `Version.cs` or
  `version.py`, `exec/`, `logs/` and the release scripts.
- KeepEncoding.txt names third-party files: converters' configs, Lua filters,
  dictionaries. [A byte order mark added to a Lua filter.]
- `.gitattributes` is `* -text`.

## Installer

- Includes `HomerComponents.iss` through `/DHomerDev=`, inside `[Code]`, whose
  comments are `//`. ["BEGIN expected".]
- Ships `scripts\installCommon.cmd`; every install script calls it.
- [Files] and [Run] agree on every path. [JAWS scripts never installed: the
  script run from `scripts` was installed at the top.]
- Offers only this app's components, worded and ordered by FinishPage.md,
  with a Results box titled "<App> Setup Results".
- The Launch box is ticked, leaves a marker, and the program starts after the
  Results box is closed, with `ExecAsOriginalUser`. [EdSharp's was unticked,
  so Enter installed it and never opened it; the template's used Exec, which
  starts the program elevated.]
- Passes the version it is building to Inno, or reads version.txt only after
  the build has written it.

## Checks

- `accept.inix` runs `exec\<App>.exe`, and doubles every backslash inside a
  `findstr /l /c:` string. [A check that could never pass.]
- No acceptance command waits for a key. [A release that hung.]
- The key check passes: no Alt+Control binding except the desktop shortcut
  and navigation keys. The naming check passes: no accessible name repeating
  a label.

## Version

- `version.txt` is the one source; the program, the installer and the
  release tag agree. A number already tagged on GitHub is stepped over.

## Elevate

- `Elevate.configure` at startup with the build's version; F11 on the Help
  menu (MDI) or in the Help box (single dialog).

## Documents and logging

- The document set is complete, each `.md` with its `.htm`, at a ninth-grade
  reading level for what a user reads (run homer-docs' checkDocs).
- The program logs through the kit's Log, in the Homer line format, to
  `%LOCALAPPDATA%\<App>\logs`.
