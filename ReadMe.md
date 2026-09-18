---
title: "HomerDev ReadMe"
author: "Jamal Mazrui"
---

# HomerDev

HomerDev is the Homer Development Kit: the shared C# classes, Python modules,
build scripts and project templates that every Homer Tools program is built on.
One copy, in one place, so a fix reaches every app.

It is aimed at two readers. A developer who wants to build or change a Homer
app, and an AI asked to write one, which can be told: "use the Homer namespace
in `C:\HomerDev\CSharp` and follow HomerDev.md."

## Install

Unzip `HomerDev.zip` into `C:\HomerDev`. That is the install.

You also need, and the kit will tell you if one is missing:

- Windows 10 or later, 64-bit
- the .NET Framework 4.8 Developer Pack
- the Visual Studio Build Tools, free, for the C# compiler
- Python 3, for the kit's own scripts
- Inno Setup 6, to build an installer
- git and the GitHub CLI, to publish

If you keep the kit somewhere other than `C:\HomerDev`, set the `HOMERDEV`
environment variable to that folder.

## Quick start

### 1. Build the kit

    cd \HomerDev
    buildHomerDev

It converts every document to HTML with pandoc, fetching pandoc if this machine
does not have it, then checks the kit over and reports anything wrong. The
detail goes to `buildHomerDev.log`.

### 2. Start an app

    newHomerApp JobDo

That writes `C:\JobDo` with everything a new app needs:

- `JobDo.cs`, a working one-dialog program with the standard controls in place
- `buildJobDo.cmd`, which compiles it against the kit
- `JobDo_setup.iss`, the installer
- `createJobDoRepo.cmd` and `.ps1`, the one-time GitHub bootstrap
- `installOllama.cmd` and `installModels.cmd`, for local AI
- `version.txt` and `.gitignore`

Nothing already in the folder is overwritten.

### 3. Set two things by hand

Open `JobDo_setup.iss` and change the two lines marked CHANGE ME: a fresh
AppId, and the desktop hotkey. Everything else in that file is already right.

### 4. Build and run

    cd \JobDo
    buildJobDo
    JobDo

The starter program opens its dialog, remembers what you type, and reports what
it did. Fill in `runJob()` in `JobDo.cs` and it is your program.

### 5. Publish

    createJobDoRepo
    tagRelease

`createJobDoRepo` makes the GitHub repository and pushes the first commit.
After that, `tagRelease` is how every release goes out. Copy `tagRelease.cmd`
and `tagRelease.ps1` from `Tools\` into the app folder first; they need no
editing.

## What is in the kit

- `CSharp\` -- nine modules in the `Homer` namespace: Lbc (dialogs), Say
  (speech), Inix (settings and tables), Keys, KeyMap, Util, Web, inixVert,
  PdfRead.
- `Python\homer\` -- the same toolbox for Python and NVDA add-ons.
- `Templates\` -- the files a new app starts from.
- `Tools\` -- tagRelease, cleanDir, tidyRepo. No editing needed; they work out
  the app name from the folder.
- `Style\` -- the Camel Type coding guidelines.

## The other documents

- `HomerDev.md` -- the complete guide: the `.inix` format, Camel Type, direct
  speech across screen readers, Lbc and the standard dialogs, the launchpad app
  conventions, keys, scripts and logs, and the installer.
- `Developer.md` -- how to change the kit itself and how a fix reaches the apps.
- `Hotkeys.md` -- the keys every Homer dialog and text box gives you.
- `History.md` -- what changed, and when.
- `License.md` -- MIT.
