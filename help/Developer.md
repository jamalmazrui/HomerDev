---
title: "HomerDev Developer Guide"
author: "Jamal Mazrui"
---

# Developer Guide

This is for changing the kit itself. For building an app with it, read
HomerDev.md.

## Contents

- [Two principles](#two-principles)
- [Layout](#layout)
- [Converting files](#converting-files)
- [Releasing the kit](#releasing-the-kit)
- [Building the kit](#building-the-kit)
- [How a change reaches the apps](#how-a-change-reaches-the-apps)
- [The four scripts, and the order they run in](#the-four-scripts-and-the-order-they-run-in)
- [Adding a module](#adding-a-module)
- [Encodings](#encodings)
- [Templates](#templates)
- [Versioning and release](#versioning-and-release)
- [Publishing the kit](#publishing-the-kit)
- [Conventions worth not rediscovering](#conventions-worth-not-rediscovering)

## Two principles

Homer follows two principles, adopted on 8 October 2026. Everything after this section applies them.

- **Convention over configuration.** A project that follows the Homer conventions needs no settings to be understood. Its kind is settled by one fact about its folder; its folders have standard names; its build is `build.cmd`, its installer script `<App>_setup.iss`, its walks `help\Tutorial_N_*.inix`. A setting exists only for what truly differs between projects -- an author's name, a book's catalog entry -- never to say what a convention already says. When a script needs a setting to find something, the convention is missing, and the convention is the fix.
- **Don't repeat yourself.** Every rule, value and piece of code has one authoritative home. Code lives once, in the kit; an app or a book project receives a copy made by its build or wrapper, logged, and never edited by hand. A skill that must carry its own copy, to work when uploaded on its own, gets that copy from the kit's build, as the skills' reference documents do. A fix is made once, in the authoritative home, and reaches every project from there. When the same thing is found written twice, one becomes the source and the other is made from it.

The two meet in the checks: the rules a skill teaches are the rules the kit's `check` runs on every project, from the skill's own scripts, so what the kit asks of others it first proves on its own work.

## Layout

    C:\HomerDev\
      .claude\skills\   the Claude skills, one folder each
      exec\CSharp\    the Homer namespace: Elevate, Inix, inixVert, KeyMap,
                     KeyName, Lbc, Log, Mdi, Media, MediaPlayer, Mpv, Ollama,
                     Paths, Say, Util, Web
      exec\Python\    the same toolbox for Python and NVDA add-ons, a module
                     each: inix, lbc, log, paths, say, util, web
      help\          every document, the style guides, the tutorial scripts
      Templates\samples\       the four fruit basket programs and their build scripts
      Templates\     the files a new app is written from, carrying _APP_
      scripts\         check, push, release, tidy,
                     buildTutorials, release
      build.cmd / .py     convert the documents, audit the kit
      checkHomerDev.cmd / .py     build all three samples and report
      newHomerApp.cmd / .py       write a new app folder
      ReadMe, License, RepoFiles.txt, version.txt, .gitignore

## Converting files

Every Homer program that turns a file of one type into another uses the kit's shared engine, never Pandoc or Office directly. The routes are in `exec\conversions.inix`, one section per source type and one line per target, each listing the ways to get there, best first; the first whose engines are all on the computer is used, and a way can take steps through an intermediate type (`pdfstructure:md > pandoc`). Python's `exec\Python\conversion.py` reads it now; C#'s `Conversion.cs` will read the same table, so a route is decided once for both languages.

The route follows the purpose. Plain text takes the quickest way and spends nothing on structure: a PDF's text layer, or the text of a Word, Excel or PowerPoint file read straight from the XML inside it, in a few milliseconds. Markdown, HTML or Word asks for headings, lists and tables: Pandoc where it reads the source, and a PDF's headings worked out from its type sizes. A scanned PDF falls back to Tesseract, its pages drawn by pypdfium2.

Only approved components are used: Pandoc, NuGet and PyPI packages, and Tesseract. Microsoft Office by COM is the last resort, logged when used, and the only way for the older binary formats, .doc, .xls and .ppt, until a free package to read them is approved. No other converting program is looked for, offered or installed by any Homer project.

`scripts\testConversion` proves every route on sample files it makes at the time, and the kit's build runs it: a failing route fails the build; a route whose engine is missing on this computer is reported as not tested.

## Releasing the kit

    releaseHomerDev "What changed."   all four steps below, stopping at the first failure

or one step at a time:

    build                   documents, all four samples, the audit
    checkHomerDev                   environment, clean build of everything, the
                                    tools on your PATH, and every program driven
                                    through its keys by uiCheck
    push "What changed."
    release

Each app's build copies the kit's current tools into its own `scripts` folder,
so an app always runs the tools of the kit it was built with. Run them from the
app's folder -- `scripts\push`, `scripts\release` -- rather than relying on a copy
somewhere on your PATH, which may be older than the kit.

## Building the kit

    build          convert the documents, build every sample, check the kit
    build check    check only
    checkHomerDev          build all three samples from clean and report

There is no compiler step, because the kit is source. The check is what stands
in for one:

- every expected component is present and not empty
- every text file is UTF-8 with a BOM and CRLF, except `.cmd` and `.bat`, which
  are CRLF with no BOM
- every template still carries its `_APP_` placeholder
- no zero-byte file anywhere
- nothing left behind by an earlier layout: a file the kit has moved is removed
  once its replacement is in place

`build` reads files; it does not compile. `checkHomerDev` does, and it
is the one to run before a release: it audits, checks that every module's
`REQUIRES` line is satisfied, deletes what previous builds wrote, and builds all
three samples. Three releases shipped a compile failure that only this would
have caught.

Any failure exits non-zero and names the file. The detail is in
`build.log` beside the script.

The kit's modules are not compiled here, so a C# mistake in one of them
surfaces the first time an app builds. That is deliberate and matches the house
preference: a build error you can see beats a component quietly left out.

## How a change reaches the apps

An app's build script compiles the Homer modules straight out of
`%HomerDev%\exec\CSharp`, or the HomerDev folder found above or beside the app on any drive (see "Where the kit and your projects live" in HomerDev.md). There is no copy in the app
folder. So:

1. Change the module here.
2. Run `build` to check the kit still passes.
3. Rebuild each app that uses it.

The third step is the real test. A change to `Lbc.cs` that DbDo compiles and
HomerScribe does not is a change that is not finished.

Before removing or renaming a public member, grep the apps for it. The merge
that produced this kit exists because two apps had diverged on exactly that.

## The four scripts, and the order they run in

Every app carries these in `scripts`, refreshed from the kit by its build,
and runs them from its project folder. They share one fact: `.gitignore` is
a whitelist written from `RepoFiles.txt`, so "add everything" means "add
everything the project has named".

1. `build` -- steps `version.txt`, builds the program and the installer,
   speaks any tutorial without audio, puts the project's own files into the
   Homer encoding (`scripts\fixEncoding`), refreshes these scripts from the kit.
2. `scripts\push "message"` -- rewrites the whitelist from `RepoFiles.txt`,
   adds what it names, refuses anything over 10 MB, commits, pushes, shows
   the status. Without `RepoFiles.txt` it stages nothing and says so.
3. `scripts\tidy` -- the periodic clean: strays into place,
   fetched things deleted, the whitelist rewritten, strays untracked, commit.
   Same whitelist as push; it too stages nothing without `RepoFiles.txt`.
4. `scripts\release` -- tags the pushed commit with the version stamped in
   `<App>_setup.exe` and publishes the installer. `scripts	agRelease` runs
   the checks first, then this.
And `scripts\unpushed` -- when something was committed that should not
   have been and the push has not happened: undoes the local commits,
   keeps every file, and the next push or tidy makes the commit properly.

`RepoFiles.txt` names what the repository carries; `LocalFiles.txt` names
what stays on this disk and is never pushed -- fetched voices, built output,
logs, generated audio. A file that does not go up needs one line in the
first; a large file that must not go up needs one line in the second.

## Adding a module

1. Write it in Camel Type, in `namespace Homer`, with a header comment saying
   what it is for and what it depends on.
2. Depend on as little as possible. The existing modules depend on the .NET
   base class library, WinForms, and each other, and nothing else. A module
   that would need a package belongs to the app that needs it, or to the
   conversion engine, whose packages are fetched when they are used.
3. Add it to `c_lsExpected` in `build.py`.
4. Add a commented line for it in `Templates\build_APP_.cmd`, so a new app can
   switch it on by uncommenting.
5. Describe it in HomerDev.md.

## Encodings

UTF-8 with a byte order mark and CRLF line endings, everywhere except `.cmd`
and `.bat`, which take CRLF and no BOM. The check enforces this, and
`newHomerApp` writes files this way. A file that reads text should detect its
encoding rather than assume, using the Ude package an app's build script
fetches.

## Templates

A template is an ordinary working file with `_APP_` wherever the app name
belongs, in the content and in the file name. `newHomerApp.py` replaces the
token and renames. Two rules:

- A template must still carry the token. The check fails if one has lost it,
  because a template that has been edited into a concrete app silently produces
  broken copies.
- Anything a person must change by hand after instantiation is marked
  `CHANGE ME` with a comment saying what to put there. Today that is the AppId
  and the hotkey in the installer.

## Versioning and release

`version.txt` holds one line and is the only place the kit's version is
written. `release` reads a version from the installer's version resource,
which the kit does not have, so the kit is tagged by hand:

    git tag v1.0.0
    git push origin v1.0.0

An app is different: its `build.cmd` increments `version.txt`, generates
`Version.cs` from it, and the `.iss` reads the same file, so the program, the
installer and the tag cannot disagree. `release` then does the rest.

## Publishing the kit

    createHomerDevRepo            create the repository and push
    createHomerDevRepo -DryRun    report what would happen, change nothing

It needs git and an authenticated `gh`. It is a maintainer script and is named
in `.gitignore`, so it does not appear in the public source browser.

## Conventions worth not rediscovering

- **Add order is focus order** in Lbc. Fix the order of the calls, or fix Lbc.
  Never sprinkle `TabIndex` assignments through an app.
- **A `.ps1` never ships without a `.cmd`** that calls it and forwards its
  arguments.
- **A script's log goes beside the script**, except for an installed program
  under Program Files, which writes beside its output or under
  `%LOCALAPPDATA%\<App>`.
- **The console is for a person; the log is for debugging.**
- **Settings are written the moment they are answered**, not at exit.
- **Speak only what the screen reader cannot know.**
