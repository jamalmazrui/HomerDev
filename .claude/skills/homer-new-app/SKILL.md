---
name: homer-new-app
description: >-
  Starts a new Homer Tools app with the Homer Development Kit: runs
  newHomerApp for a C# or Python project, chooses the app's shape (a single
  tool with a command line and a dialog, a multiple-document app, or an NVDA
  add-on), fills in the starter files -- source, installer, lists, acceptance
  checks and documents -- and takes it through its first build, repository and
  release -- or, when the need is records rather than a program, makes it a
  DbDo database like JobTrail. Use when asked to create, scaffold or begin a
  new Homer app, tool or program, or to turn an idea into a working Homer
  project.
---

# A new Homer app

Every Homer app is made the same way, so a new one starts with everything the
others have: the same build, installer, logs, lists, documents and checks.

## 1. Decide the shape and the language

**First ask whether it needs to be a program at all.** When the job is keeping
and reporting on records -- leads, contacts, collections, a log -- it is
usually better as a DbDo database than as a new program: JobTrail is the
example. It is a folder under DbDo's `templates` (JobTrail.db with
JobTrail.inix beside it, which sets the table it opens on and how each table
is heard; report.inix for its reports; and `.dbdo` and `.sql` scripts such as
Today.dbdo), documented in DbDo's help as JobTrail.md, and it inherits
everything DbDo does by keyboard and screen reader. DbDo carries eleven such
Trails (BookTrail, RecipeTrail and others). Such a database is added to DbDo's
repository and installer rather than made with newHomerApp; the rest of this
skill is for a program.

- **A single tool**: one job, a command line that can be scripted, and one Lbc
  dialog when run with no arguments or `--gui` -- the same settings in both.
  2htm, extCheck, urlCheck and urlFido are this shape.
- **A multiple-document (MDI) app**: a desktop program with menus and several
  windows, one instance, opened by its desktop shortcut. DbDo, EdSharp and
  FileDir are this shape.
- **An NVDA add-on**, like HomerView.

C# and Python are equal platforms. The kit's worked examples are the fruit
baskets in `Templates/samples`: FruitBasketCs and FruitBasketPy (a single
tool), FruitBasketMdiCs and FruitBasketMdiPy (MDI). Start from the one that
matches.

## 2. Make the project

```
newHomerApp <App>            a C# app in C:\<App>
newHomerApp <App> --python   a Python app
```

It writes the source starter (C#), build script, installer script, repository
bootstrap, `version.txt` (1.0.0), `accept.inix`, `RepoFiles.txt`,
`LocalFiles.txt`, `.gitattributes`, ReadMe and License (MIT), and starters in
`help` for the guide, Announce, Developer and History, with the private
notebook `self.md`. It overwrites nothing. The kit's scripts arrive in
`scripts` with the first build.

## 3. Fill in the starters

- **The source.** Write the app in Camel Type on the kit's classes (see
  homer-code); the interface follows homer-ui. Start the log first and
  configure Elevate at startup (see homer-elevate).
- **The installer** (`<App>_setup.iss`): the two lines marked CHANGE ME -- a
  fresh AppId GUID, generated once and never changed, and the desktop hotkey
  (Alt+Control plus a letter of the app's name no other Homer app uses).
  Offer only the components the app uses (see homer-installer).
- **The build script's settings** at its top: `homerModules` (the kit classes
  or modules the app uses), and for C# `cscTarget`, resources and NuGet
  packages. The build fetches whatever it needs itself.
- **accept.inix**: what "done" means, as commands the check runs: the program
  answers `--help`, refuses a bad switch, and does its job on a sample.
- **RepoFiles.txt**: add each file the app adds; LocalFiles.txt for what stays
  on the disk (see homer-build-release).
- **The documents**: write them to the Homer rules (see homer-docs); add
  Hotkeys.md once there are keys.

## 4. First build, repository and release

```
cd \<App>
build<App>
exec\<App>.exe --help
create<App>Repo
scripts\tidy
scripts\push "First release."
scripts\release
```

`create<App>Repo` makes the GitHub repository once. After that the everyday
cycle of homer-build-release applies. Then add the app to the Homer Tools
page and to Homer Resources.

## Checklist

- [ ] Shape and language chosen; the matching fruit basket read
- [ ] newHomerApp run
- [ ] Source written; log started first; Elevate configured
- [ ] Installer: AppId, hotkey, components
- [ ] Build settings: homerModules and the rest
- [ ] accept.inix, RepoFiles.txt, LocalFiles.txt
- [ ] Documents written to the Homer rules
- [ ] Built, tested, repository made, pushed, released
