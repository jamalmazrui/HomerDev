# The kit's shared code

## Contents
- Where it lives and how an app gets it
- C# classes
- Python modules
- Rules for using them

## Where it lives and how an app gets it

The kit (C:\HomerDev) keeps its libraries in `exec`, the folder for code an
app's core runs on:

- `exec/CSharp`: the C# classes, all in the `Homer` namespace. An app's build
  names the files it uses on the compiler line, straight from the kit
  (`!homerDev!\exec\CSharp\Lbc.cs`); an app never carries a copy.
- `exec/Python`: the Python modules, each imported by its own name
  (`import log`, `import inix, paths`), with no package around them. A Python
  app's build puts the folder on PyInstaller's path
  (`--paths "!homerDev!\exec\Python"`) and names each module with
  `--hidden-import`.
- `exec/Homer.dll`: the C# classes compiled for a Python app whose dialogs use
  WinForms through pythonnet (`lbcnet`).

The kit is needed only to build. A built program carries what it uses; an
installed app never needs C:\HomerDev. An NVDA add-on copies the modules it
uses into its own folder and puts that folder on the import path first.

## C# classes

- `Elevate`: version check against the latest GitHub release, and the F11
  update and elevation.
- `Inix`: the `.inix` settings format, plus conversion of tables among
  `.inix`, `.csv`, `.tsv`, Markdown and `.xlsx`.
- `KeyMap`: one table of commands, their summaries and keys, read by the
  menus, the key describer and the hotkey list.
- `KeyName`: one spelling for every key (`Alt+Control+Shift+H`, the reader key
  as `JAWS` or `NVDA`) and conversion to what each API wants.
- `Lbc`: Layout By Code, the dialogs: labelled standard controls added in
  focus order, Alt-letter access from the `&` in a caption or preceding label.
- `Log`: the session log in the Homer line format.
- `Mdi`: the frame and child of a multiple-document app.
- `Ollama`: talking to a local Ollama model.
- `Paths`: the folder layout, installed and per-user.
- `PdfRead`: reading a PDF with positions and font sizes (needs PdfPig, which
  the app's build fetches).
- `Say`: speech straight to JAWS or NVDA, each part of a grouped announcement
  a separate utterance.
- `Util`: string and file helpers.
- `Web`: fetch a page, pull its links, download with a sensible name.
- `inixVert`: the command-line wrapper over Inix's table conversion.

## Python modules

`elevate`, `inix`, `lbc` (wxPython dialogs), `lbcnet` (WinForms dialogs
through Homer.dll), `log`, `mdi`, `paths`, `say`, `util` and `web`: the same
names and behaviour as the C# classes, a module where C# has a static class
and a class where C# keeps state (`lbc.Dialog`).

## Rules for using them

- Start the log first, before anything can fail: `Log.start("<App>")` or
  `log.start("<App>")`.
- Take every folder from `Paths` or `paths`; never build one by hand.
- Only the local tree: everything of the app's own under `%LOCALAPPDATA%\<App>`,
  nothing under `%APPDATA%` (Roaming). The one thing a Homer installer puts
  there is the JAWS scripts and NVDA add-on themselves, where those readers
  read them; records and fingerprints about them stay in the local tree. An
  app that used Roaming before calls `Paths.moveFromRoaming()` once at startup,
  after the log starts, and logs each line it returns. `check` fails any other
  Roaming use.
- Save a setting as soon as the user answers, not at exit.
- Speak only what the screen reader cannot know; never repeat a dialog's
  title or a control's name.
- A fix to shared behaviour goes in the kit, not in one app.
