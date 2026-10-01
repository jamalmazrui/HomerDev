# Components in HomerComponents.iss

## Contents
- Declaring a component
- The three entries per component
- Labels and outcomes
- Ollama models
- JAWS scripts and the NVDA add-on
- Detection
- Failures that looked like success

## Declaring a component

In `InitializeWizard` (or the first function that needs it), one call per
component, keeping the index:

```pascal
iPandoc := homerAdd('Pandoc', 'JohnMacFarlane.Pandoc', 'pandoc',
  '{commonpf}\Pandoc\pandoc.exe', 'converts documents',
  'Software\Microsoft\Windows\CurrentVersion\Uninstall\{...}');
```

The arguments: display name; winget ids separated by `;` (tried in order, for
a product published under more than one); the executable name for the PATH;
the file where it installs; the use, three or four words, shown in
parentheses; an uninstall registry key, or `''`.

## The three entries per component

Inno shows [Run] entries in the order written and hides those whose `Check:`
is false, so each component gets three, and the page groups itself:

```
Filename: "{app}\scripts\installPandoc.cmd"; Parameters: "noPause"; \
  Description: "{code:labelPandoc}"; Check: isInstallPandoc; \
  Flags: postinstall skipifsilent runascurrentuser waituntilterminated
; the same with Check: isUpdatePandoc for Update, and Check: isReinstallPandoc
; and the unchecked flag for Reinstall
```

A `Check:` names a function, so each component gets three one-line wrappers
in [Code], beside its label function:

```pascal
function isInstallPandoc(): Boolean;   begin Result := homerIs(iPandoc, 0); end;
function isUpdatePandoc(): Boolean;    begin Result := homerIs(iPandoc, 1); end;
function isReinstallPandoc(): Boolean; begin Result := homerIs(iPandoc, 2); end;
function labelPandoc(sParam: String): String; begin Result := homerLabel(iPandoc); end;
```

Write all the Install entries first (screen readers, then components
alphabetically), then all the Update entries, then all the Reinstall entries,
then Launch and the user guide. `homerWanted(i)` is true when a component is
missing or stale.

## Labels and outcomes

- `homerLabel(i)`: "Install X <latest> (use)", "Update X from <old> to <new>
  (use)" or "Reinstall X <version> (use)".
- `homerNoteTicked()`, from `NextButtonClick` on `wpFinished`, records the
  ticked captions before any script runs.
- `homerOutcomeLine(i)`: after the scripts, a past-tense line from a fresh
  probe ("Pandoc 3.11 was installed"), or `''` when the box was not ticked.
- `homerResultsBox(sBody)`: the Results box, titled "<App> Setup Results".
- The launch entry only writes a marker; the app starts after the Results box
  is closed, so its window does not talk over the summary.

## Ollama models

A model has no winget id and no Update (a pull always fetches the current
one): `homerModelLabel(model, use, size)`, `homerModelIs(model, False)` for
Install and `homerModelIs(model, True)` for Reinstall,
`homerModelOutcomeLine(model, use, size)` for the Results box. The size goes
in the label when it is large: "Install qwen2.5:7b (translates text, about
4.7 GB, needs Ollama)".

## JAWS scripts and the NVDA add-on

They are components too, sorted among the others by name ("JAWS scripts",
"NVDA add-on"), with three entries each like any component, calling
`installScreenReaderSupport.cmd` with `noPause jaws` or `noPause nvda`:

```pascal
function labelJaws(sParam: String): String; begin Result := homerReaderLabel('jaws'); end;
function isInstallJaws(): Boolean;          begin Result := homerReaderIs('jaws', 0); end;
function isUpdateJaws(): Boolean;           begin Result := homerReaderIs('jaws', 1); end;
function isReinstallJaws(): Boolean;        begin Result := homerReaderIs('jaws', 2); end;
```

and the same with `Nvda` and `'nvda'`. `homerReaderState` asks the script's
`state` mode once: a fingerprint of the JAWS sources against the one kept in
each JAWS version's settings folder, and the NVDA add-on's manifest version
against the installed one. A reader not on the computer gets no box. The
Results box reports each ticked reader through `homerScreenReaderOutcome`.

## Detection

`homerState(i)` tries every winget id, then the file, then the executable's
own `--version`, then the registry key, because the installer runs elevated,
where winget is often unreachable and per-user tools are not on the PATH.
Missing any of them makes an installed component read as absent. Each verdict
is written to the setup log: `Component Pandoc: 3.9 found, 3.11 available;
offered as Update`.

## Failures that looked like success

- **An Update that never updates.** A winget upgrade limited to `--scope
  machine` answered "No installed package found" (-1978335212) for a Python
  winget itself listed, so every install offered the same update. Retry
  without a scope when that code comes back, log both answers, and have the
  Results line compare the version found with the one offered.
- **A support folder that only grows.** [Files] adds and never removes, so
  files an old installer put in `{app}\scripts\jaws` stayed, and were copied
  into every JAWS settings folder. Clear such a folder with [InstallDelete]
  (`Type: filesandordirs`) and copy only the file types that belong there.
- **A check that passes on an old copy.** An acceptance check looked for the
  installer in `exec`, where an old one lingered, not at the top where the new
  one is built. Check the real location, and check that no old copy remains.
- **A screen reader started behind JAWS.** Opening an `.nvda-addon`, or
  running nvda.exe with an add-on argument (it has none), started NVDA over
  JAWS or failed with "invalid command line parameter". Install the add-on
  into NVDA's addons folder directly (homer-screen-reader).
- **A window nobody asked for.** Ollama's installer starts its desktop app,
  which opens a chat window. Homer apps use Ollama behind the scenes, so
  installOllama closes that window politely after installing, updating or
  reinstalling, leaving the service running, and logs whether it did.
