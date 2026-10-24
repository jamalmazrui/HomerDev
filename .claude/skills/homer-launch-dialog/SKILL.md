---
name: homer-launch-dialog
description: >-
  Builds and reviews the dialog and command line of a Homer launch app: an app
  that takes source paths and settings, runs a process, and writes results to
  an output directory (2htm, BatCon, extCheck, HomerScribe, urlCheck,
  urlFido). Use when making a new launch app, changing one's dialog, switches,
  Results box or logging, or checking that one still follows the pattern.
---

# Homer launch dialog

Every launch app shows one dialog, built by the kit's `LaunchDialog` class in
`exec\CSharp\Lbc.cs` (C#, and Python through Homer.dll). Never build the
standard parts by hand; `help\LaunchDialog.md` explains each rule.

## The bands, in order (an empty band is left out)

1. "&Source paths:" box, then "&Browse local source" button: `addSourceBand`.
2. The app's transformation checkboxes: `dialog.addBand()` and `addCheckBox`.
3. The app's other controls shaping the work.
4. "&Output directory:" box, then "&Choose output directory": `addOutputBand`.
5. "&Force replacements", "&Use configuration", "&View output directory"
   checkboxes, and 6. "&Default settings", "&Help" buttons: `addOperationBands`.
7. OK and Cancel alone, at the bottom right: `run`.

## Rules

- **Force replacements works one way everywhere:** unchecked, a source whose
  result exists is skipped and kept, and the Results box adds
  `LaunchDialog.keptLine(count, noun)`; checked, the work is redone and the old
  result kept aside until the new one is complete. Pass "" as its tip to get
  `LaunchDialog.forceTip`. It sits first in the operation band.
- **No Guide button, no Log session checkbox, no Include subfolders
  checkbox.** Logging is automatic; Help says where the logs are.
- **Letters**: S, B, O, C, F, U, V, D, H for the standard controls; an earlier
  app control that claims one keeps it, and the standard control moves to its
  next word's initial or goes without. OK and Cancel have none.
- **Keys**: Control+Enter is OK and Escape is Cancel from any control; F1 is
  Help; F11 is the version check from anywhere, named in the Help box.
- **Pickers** open where the box points, else in the known folder for the
  content (`knownFolder`: Documents by default, Videos for HomerScribe).
- **Every run ends with `LaunchDialog.finish`**: the Results box, titled
  "<App> Results" with one focused OK button, then the output directory when
  View output directory is checked, and the app exits. (`showResults` is the
  box alone, for an app that opens its folder its own way.)
- **The command line matches the dialog**: long switch = label, short switch
  = Alt letter (`-o`, `-f`, `-u`, `-v`, `-d`, `-h`); slash, one or two hyphens,
  any case; older spellings stay as aliases; no log switch.

## While the work runs

- **Use `LaunchProgress`**, never a form of your own: `status(text)` for a new
  phase, `step(item, done, total)` for each item, `pump()` in a long silent
  step, `cancelled` checked between items, `Dispose()` before the Results box.
- **Speak only while the app is in front** (`LaunchProgress.isInFront`); the
  title and status box are always kept current, and returning speaks the latest
  status once.
- **First three messages and every phase change at once; steps at most every
  five seconds; newest wins.**
- **Say the percentage, and time left when honest:** `step` gives "Budget.pdf,
  2 of 5 done, 40%, about 3 min left"; `fraction(where, done, total)` gives
  "Film.mp4, 11 min, 23%". The window also has a real progress bar; the
  spoken percentage is how a screen reader user receives it (the author's
  ruling, 24 October 2026). Say time with `LaunchProgress.spokenTime`.
- **Pump after every update**, at most ten times a second; the window's only
  command, Cancel (Escape, no letter), just sets a flag.

## Check

`scripts\checkLaunch.py <project> [--app <name>]` exits 0 when the project is
not a launch app or follows the pattern, 1 when it breaks it, and lists
retired names still in its documents as warnings. The kit's `scripts\check`
runs it on every app.
