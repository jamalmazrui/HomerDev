# Where the kit let an app down, 25 September 2026

*From the build, check and release logs of DbDo, EdSharp, FileDir, HomerScribe
and HomerView, read in the DbDo chat. Each item names the failure, what in the
kit caused or permitted it, and the fix -- made here where the kit's tools are
concerned, and recommended where the kit's classes or templates are.*

## Fixed in this patch (scripts\checkHomerApp.py)

- **Every acceptance check written as `cmd /c if exist X (exit 0) else (exit 1)`
  failed, whatever was true.** EdSharp: 7 of 7. DbDo: 9 of 12, until its tests
  were moved into a file. Cause: the checker runs each Run line with
  `shell=True`, which is itself `cmd /c`, so a line beginning `cmd /c` was
  parsed twice and its parentheses and else came apart. Fix: a line beginning
  `cmd /c` is now handed to cmd once, as `cmd /s /c "..."`, with no shell wrapper
  from Python. The template's `accept.inix` lines can stay as written.
- **Access letters were counted across a whole file.** DbDo, 175 items in eight
  menus, got 26 problems, none real. Now counted per menu (the container named
  in the call) or per dialog-building method.
- **Prose was read as captions.** An ampersand in a long help string counted as
  a trigger letter. Only strings of forty characters or fewer are captions now.
- **Python files were read for WinForms access keys.** HomerView's eight
  add-on files produced letter clashes they cannot have. A .py file is scanned
  only if it names System.Windows.Forms.
- **Alt+Control with a navigation key** (arrows, Home, End, Page Up, Page Down)
  is allowed, per the ruling of 25 September; letters and function keys remain
  reserved.

## For the kit's classes and templates (not changed here)

- **version.txt gained a byte order mark**, and every build that reads it with
  `set /p` then fails its own kit-version check: HomerView refused 1.40.1 as
  "older than 1.39.2", DbDo refused it as older than 1.38.3. `Templates\build_APP_.cmd`
  should read the version through PowerShell and trim `[char]0xFEFF`, as
  DbDo's build now does. And whatever wrote the mark -- `fixEncoding` exempts
  version.txt, so it was something else -- should be found.
- **"kit 1.40.1 is older than 1.40.1"** -- FileDir, 21:43. Equal versions
  refused, which means the two strings were not equal: something invisible
  rode along with the number. A trailing space is the usual culprit, and
  `echo !ver! > version.txt` writes one (the space before the redirect goes
  into the file); `> version.txt echo !ver!` does not. The byte order mark
  was the same fault in another coat. Two rules for the template and every
  app's build: WRITE version.txt with the redirect first, and READ it
  through PowerShell, trimming `[char]0xFEFF`, spaces, carriage return and
  line feed, before any comparison. DbDo does both; the message should also
  show the value quoted, so a stray character is visible.
- **The kit's own files arrive with bare line feeds.** `buildHomerDev check`
  reports 96 line-ending problems, all of them files a GitHub checkout or
  archive delivers as LF. Options: store CRLF in the repository (core.autocrlf
  false, fixEncoding, commit) so the archive matches; and have buildHomerDev run
  `scripts\fixEncoding` on itself before its check, as every app's build does.
- **PdfRead.cs needs Microsoft.Bcl.HashCode.dll**, which HomerScribe's build did
  not fetch ("[pdfpig] needs Microsoft.Bcl.HashCode.dll"). PdfPig's transitive
  dependencies belong in PdfRead.cs's ASSEMBLIES line so every build that
  compiles it knows to fetch them.
- **Inix renamed InixCodec**, and HomerView still uses the old name; it also
  fails on `Web`, which means Web.cs is not on its compiler line or the file
  lacks `using Homer;`. A rename in a shared class should appear in the kit's
  History with the old name, so an app's compiler error can be looked up.
- **The Python samples fail to build** (FruitBasketPy, FruitBasketMdiPy, exit
  code 1); their logs were not among those read. tagRelease refuses the kit
  until they pass.

## Seen in the apps, for their own chats

- **EdSharp**: four accessible names repeat captions; `auditEdSharp.py` is
  still present and claims a duplicate letter, though the briefing retired it.
- **HomerView**: the setup script names `HomerView.htm` at the root, which moved
  to `help`; and it binds Alt+Control+Shift chords, which the rule reserves.
- **FileDir**: "FileDir.exe is running" -- close it and build.
- **HomerScribe**: six assembly binding redirects in its .config do not match
  the DLLs on disk.
