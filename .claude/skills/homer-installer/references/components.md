# Components in HomerComponents.iss

## Contents
- Declaring a component
- The three entries per component
- Labels and outcomes
- Ollama models
- Detection

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

## Detection

`homerState(i)` tries every winget id, then the file, then the executable's
own `--version`, then the registry key, because the installer runs elevated,
where winget is often unreachable and per-user tools are not on the PATH.
Missing any of them makes an installed component read as absent. Each verdict
is written to the setup log: `Component Pandoc: 3.9 found, 3.11 available;
offered as Update`.
