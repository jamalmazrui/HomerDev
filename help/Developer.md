---
title: "HomerDev Developer Guide"
author: "Jamal Mazrui"
---

# Developer Guide

This is for changing the kit itself. For building an app with it, read
HomerDev.md.

# Layout

    C:\HomerDev\
      CSharp\        the Homer namespace: Inix, KeyMap, KeyName, Lbc, Log, Mdi,
                     Paths, PdfRead, Say, Util, Web, inixVert
      homer\         the same toolbox for Python and NVDA add-ons: inix, lbc,
                     log, paths, say, util, web
      help\          every document, the style guides, the tutorial scripts
      Samples\       the four fruit basket programs and their build scripts
      Templates\     the files a new app is written from, carrying _APP_
      scripts\         checkHomerApp, gitPush, gitRelease, homerTidy,
                     sayTutorial, tagRelease
      buildHomerDev.cmd / .py     convert the documents, audit the kit
      checkHomerDev.cmd / .py     build all three samples and report
      newHomerApp.cmd / .py       write a new app folder
      ReadMe, License, RepoFiles.txt, version.txt, .gitignore

# Releasing the kit

    releaseHomerDev "What changed."   all four steps below, stopping at the first failure

or one step at a time:

    buildHomerDev                   documents, all four samples, the audit
    checkHomerDev                   environment, clean build of everything, the
                                    tools on your PATH, and every program driven
                                    through its keys by uiCheck
    scripts\installTools              put the current tools on the PATH
    gitPush "What changed."
    gitRelease

`installTools` matters more than it looks. `tagRelease`, `homerTidy`,
`checkHomerApp`, `gitPush` and `gitRelease` all act on the current directory, so
one copy on the PATH serves every project -- and an OLD copy on the PATH also
serves every project. A `tagRelease` from before source-only releases were
supported refuses to release a project that has no installer script, and the
error names a file that was never meant to exist:

    Could not find HomerDev_setup.iss in C:\HomerDev

That is the old copy talking. Run `installTools` after updating the kit and it
goes away.

# Building the kit

    buildHomerDev          convert the documents, build every sample, check the kit
    buildHomerDev check    check only
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

`buildHomerDev` reads files; it does not compile. `checkHomerDev` does, and it
is the one to run before a release: it audits, checks that every module's
`REQUIRES` line is satisfied, deletes what previous builds wrote, and builds all
three samples. Three releases shipped a compile failure that only this would
have caught.

Any failure exits non-zero and names the file. The detail is in
`buildHomerDev.log` beside the script.

The kit's modules are not compiled here, so a C# mistake in one of them
surfaces the first time an app builds. That is deliberate and matches the house
preference: a build error you can see beats a component quietly left out.

# How a change reaches the apps

An app's build script compiles the Homer modules straight out of
`%HOMERDEV%\CSharp`, defaulting to `C:\HomerDev`. There is no copy in the app
folder. So:

1. Change the module here.
2. Run `buildHomerDev` to check the kit still passes.
3. Rebuild each app that uses it.

The third step is the real test. A change to `Lbc.cs` that DbDo compiles and
HomerScribe does not is a change that is not finished.

Before removing or renaming a public member, grep the apps for it. The merge
that produced this kit exists because two apps had diverged on exactly that.

# Adding a module

1. Write it in Camel Type, in `namespace Homer`, with a header comment saying
   what it is for and what it depends on.
2. Depend on as little as possible. The existing modules depend on the .NET
   base class library, WinForms, and each other, and nothing else. `PdfRead.cs`
   is the one exception, which is why it sits apart and why an app's build
   script fetches its package rather than the kit carrying it.
3. Add it to `c_lsExpected` in `buildHomerDev.py`.
4. Add a commented line for it in `Templates\build_APP_.cmd`, so a new app can
   switch it on by uncommenting.
5. Describe it in HomerDev.md.

# Encodings

UTF-8 with a byte order mark and CRLF line endings, everywhere except `.cmd`
and `.bat`, which take CRLF and no BOM. The check enforces this, and
`newHomerApp` writes files this way. A file that reads text should detect its
encoding rather than assume, using the Ude package an app's build script
fetches.

# Templates

A template is an ordinary working file with `_APP_` wherever the app name
belongs, in the content and in the file name. `newHomerApp.py` replaces the
token and renames. Two rules:

- A template must still carry the token. The check fails if one has lost it,
  because a template that has been edited into a concrete app silently produces
  broken copies.
- Anything a person must change by hand after instantiation is marked
  `CHANGE ME` with a comment saying what to put there. Today that is the AppId
  and the hotkey in the installer.

# Versioning and release

`version.txt` holds one line and is the only place the kit's version is
written. `tagRelease` reads a version from the installer's version resource,
which the kit does not have, so the kit is tagged by hand:

    git tag v1.0.0
    git push origin v1.0.0

An app is different: its `build<App>.cmd` increments `version.txt`, generates
`Version.cs` from it, and the `.iss` reads the same file, so the program, the
installer and the tag cannot disagree. `tagRelease` then does the rest.

# Publishing the kit

    createHomerDevRepo            create the repository and push
    createHomerDevRepo -DryRun    report what would happen, change nothing

It needs git and an authenticated `gh`. It is a maintainer script and is named
in `.gitignore`, so it does not appear in the public source browser.

# Conventions worth not rediscovering

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
