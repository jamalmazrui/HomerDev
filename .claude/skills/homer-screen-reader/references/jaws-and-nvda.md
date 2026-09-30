# JAWS and NVDA in detail

## Contents
- What JAWS loads
- Layering and scope
- Key maps
- Compiling
- NVDA add-ons
- Kit modules inside an add-on
- Diagnosing
- Learned from the publishers' guides

## What JAWS loads

JAWS loads the script file named after the program in focus
(`<executable>.jsb`) and the default file, and nothing else. A compiled
`HomerView.jsb` in the settings folder is loaded by no one when no program is
called HomerView.exe. So scripts for an app are named after its executable;
scripts that act inside another program (a browser, say) are reached through
a file named after that program's executable.

User settings are in `%APPDATA%\Freedom Scientific\JAWS\<version>\Settings\enu`,
one folder per installed version; the factory scripts are under the program
folder. A user file of a program's name replaces the factory one of that name
unless it brings it back in.

## Layering and scope

A user `<program>.jss` that serves another program must bring in the factory
scripts for it first, when JAWS ships any, and then the app's own: anything
not overridden is inherited, so everything the factory scripts provide still
works. Replacing them outright silently removes what users rely on.

Keep every change inside the program's own files. Nothing in default.jss,
default.jkm or MyExtensions: those act everywhere. Back up whatever is
replaced, record what was written, and provide an undo.

## Key maps

A `.jkm` binds keys to script names by section: `[Common Keys]` work
everywhere in the program (address bar, forms mode), `[Virtual Keys]` only
where a virtual cursor is active. A key in the wrong section either does
nothing or acts where it should not. Key names follow JAWS's own spelling.

## Compiling

Compile each `.jss` in each installed version's settings folder with that
version's own `scompile.exe`
(`%ProgramFiles%\Freedom Scientific\JAWS\<version>\scompile.exe`): a `.jsb`
built by one year's compiler is not reliably loaded by another year's JAWS,
so compiling once and copying the binary does not work. Compiling in the
settings folder also makes `Include "hjconst.jsh"` resolve as it will at run
time.

The compilers disagree: JAWS 2026's stops at what it cannot parse, while the
2024 and 2025 one also reports what it parsed and could not make sense of. A
file that satisfies one has not been shown to satisfy another, so a check
compiles a copy under every installed version and reports each compiler's
answer, then removes the copy. That takes a second; finding a syntax error by
building, installing and reading a setup log takes minutes.

## NVDA add-ons

- `manifest.ini`: name, summary, description, author, version (the app's),
  `minimumNVDAVersion`, `lastTestedNVDAVersion`, url, docFileName.
- `globalPlugins/<name>/__init__.py` for commands everywhere;
  `appModules/<program>.py` for one program.
- Commands are methods named `script_<name>` with the `@script` decorator
  giving the description, the category (the app's name) and the gesture,
  `gesture="kb:NVDA+alt+f10"`. Only `kb:` gestures count as keys.
- Documents in `doc/en`, the add-on's help in NVDA's add-on store.
- Packed as `<App>.nvda-addon` (a zip of the folder); installed with
  `nvda --install-add-on=<file>`, and NVDA asks the user to confirm.

- **The add-on's version is the app's.** The build sets the `version` line of
  the shipped add-on's manifest.ini to the app's version, so the installer's
  comparison with the installed add-on says Update after a release and
  Reinstall otherwise.
- **Install the add-on without starting NVDA.** NVDA's own installer
  (`addonHandler.installAddonBundle`) unpacks the `.nvda-addon` zip into
  `%APPDATA%\nvda\addons\<name>.pendingInstall` and, at its next start, moves
  it to `addons\<name>`; an add-on already there under its own name is simply
  loaded. A Homer installer puts it there directly: unpacked to a temporary
  folder, any old copy moved aside to `<name>.delete` (a suffix NVDA skips),
  the new one moved into place, the old one put back if that fails. No second
  screen reader starts talking over JAWS. An add-on's `installTasks.py` does
  not run this way, so its presence is logged. (Starting `nvda.exe
  --install-add-on` did start NVDA, which talked over JAWS; it must be started
  through the shell, as CreateProcess refuses it with code 740.)
- **An accepted add-on waits as `<name>.pendingInstall`** under
  `%APPDATA%\nvda\addons` until NVDA restarts; count it as installed.
- **NVDA's own log** is `%TEMP%\nvda.log` for an installed copy (the folder of a
  portable copy), with the previous session's kept as `nvda-old.log`. Its
  add-on handler writes there when it installs, loads or refuses an add-on;
  read it with read-write sharing, since NVDA holds it open, and copy the lines
  naming the add-on into the installer's log.

## Kit modules inside an add-on

NVDA cannot share one copy of a module between add-ons, so an add-on carries
copies of the kit's Python modules it uses, from `exec/Python` in the kit, in
its own folder. A copy is refreshed from the kit, never edited in place. The
kit's modules import each other by plain name, so an add-on either puts its
folder on `sys.path` just for the import and removes it afterwards, or keeps
its copies inside its own package with relative imports; the second keeps a
module named `log` from meeting another add-on's (see the last section).

## Diagnosing

- **Nothing happens on a script's key.** Is the `.jsb` present for this JAWS
  version, and is it named after the executable in focus? Was it compiled by
  this version's compiler?
- **"Unknown script call to ..."** A key map named a script that is not
  loaded -- usually a user file that replaced the factory one without bringing
  it back in. Find which key map supplies the key and which script it names.
- **A key acts in the wrong program.** It is in default.jkm, or a section
  whose scope is wider than meant.
- Gather facts before proposing a fix: a probe that only reads -- which files
  exist in which folders, which key map binds the key -- ends a round of
  guessing faster than another guess.

## Learned from the publishers' guides

From Freedom Scientific's scripting documentation (JAWSScripting.md):

- **How a call is resolved.** The application's script file first, then the
  files it brings in with `Use`, then default, then the built-in functions.
  Nothing found: JAWS says "unknown function call to" and spells the name --
  a misspelling, a deleted function, or a file not loaded.
- **A script is bound to a key and returns nothing; a function is called**
  from a script, a function or an event, and may take parameters and return
  a value. Event functions cannot be invented, only overridden.
- **Overriding safely.** An app's file may override a default script or
  function; to defer to the default, call it by scope, `Default::SayLine()`,
  or with PerformScript, CallScriptByName or CallFunctionByName. A user
  default.jss must `Use "default.jsb"`, or every default script not in it
  fails -- one more reason Homer never writes one. MyExtensions is for adding
  scripts, not overriding them.
- **Starting and stopping.** `AutoStartEvent` runs when the script set loads,
  `AutoFinishEvent` when it unloads: set up and release there.
- **Includes.** A script source begins with `Include "hjConst.jsh"`,
  `Include "hjGlobal.jsh"` and `Include "common.jsm"`, then its own headers.
- **Compiling.** `scompile.exe` in the JAWS program folder takes source file
  names, wildcards allowed, and writes each `.jsb` beside its source; JAWS
  loads it the next time the program of that name comes to the foreground.
- **Encoding.** A byte order mark tells JAWS a script file is UTF-8; without
  one it is read as ANSI, and any character above 127 is at risk. Homer
  script files carry the mark, as the Homer encoding asks.
- **JAWS 2026's modern compiler** adds nested collection access
  (`a.domains[4].name`). A script that must also run on JAWS 2024 or 2025
  cannot use it.

From NV Access's and the add-on team's guides (NVDAScripting.md):

- **Which script wins a key.** Global plugins, then the focused program's app
  module, then NVDA objects, then NVDA's global commands. So a global plugin's
  key overrides every app module's everywhere: prefer an app module when a
  command belongs to one program, and check NVDA's command reference and
  other add-ons for a clash before choosing a key.
- **Never block NVDA.** Anything slow -- a download, a long computation --
  runs on a thread (`threading`, `concurrent.futures`); a repeating task uses
  `wx.Timer`. `multiprocessing` cannot be used inside NVDA.
- **Carrying other modules.** A relative import (`from . import x`) keeps a
  module private to the add-on; putting a folder on `sys.path` makes its
  modules visible to all of NVDA, so do it only around the import and remove
  the folder afterwards. The kit's modules import each other by plain name
  (`import paths` inside `log`), which needs the path method -- and plain
  names such as `log` or `paths` could meet another add-on's module of the same
  name in `sys.modules`, so an add-on's copies are best renamed or imported
  relatively.
- **Speaking.** `ui.message(text)` speaks and brailles; `speech.speakMessage`
  speaks only; `speech.cancelSpeech()` stops.
- **Testing.** The NVDA Python console and NVDA's log are the first tools;
  test on more than one computer, and read "Changes for developers" in each
  NVDA release, since the API moves (the control types change of 2021.2).

## Nothing of Homer's own in Roaming

The JAWS scripts go into JAWS's settings folders and the NVDA add-on into
NVDA's addons folder, both under `%APPDATA%`, because those readers read
nowhere else. Everything the installer keeps about them -- the list of files
placed (`jawsSettings.log`) and the fingerprint of the scripts compiled in each
JAWS version (`jawsScripts.inix`) -- is under `%LOCALAPPDATA%\<App>`.
