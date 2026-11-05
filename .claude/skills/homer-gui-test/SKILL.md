---
name: homer-gui-test
description: >-
  Drives a running Homer app through Windows UI Automation to test its
  accessibility and to confirm its tutorials: uiCheck presses keys and reads the
  accessibility tree back; recordWalk presses a walk's keys while JAWS or NVDA
  runs, records and transcribes what the screen reader said, and sets it beside
  what the walk expected, what has focus and what the app logged, with an
  optional Axe.Windows scan after each step; whoOpens names the program behind a
  stray "Select an app to open this file" prompt. Use when asked to test an app
  with a screen reader, check that a dialog or key says what it should, confirm a
  tutorial's Hear lines, find unnamed or unreachable controls, or record a
  session for a tutorial. Not for checking a document file (use homer-quality) or
  writing a tutorial script (use homer-tutorial, which these runs confirm).
---

# Testing an app the way a screen reader user meets it

A file can be checked by reading it, but a program has to be run. The kit drives
a real, running Homer app through Windows UI Automation -- the interface a screen
reader itself reads -- presses its keys, and gathers evidence of what happened,
instead of a person remembering to try it.

## The three tools

All three live in the kit's scripts folder. Run them from the app's folder, such
as C:\DbDo; each finds the app from there.

- **uiCheck** -- runs the app, sends keys, and reads the accessibility tree back.
  Fast and repeatable, with no screen reader needed. It does not hear speech, and
  says so. Its tests live beside the program in uiTest.inix: [test] with Run=,
  then [step]s with Keys= (pywinauto syntax: {ENTER}, %x for Alt+x, ^x for
  Control+x, +x for Shift+x), Wants= (text that must appear in the tree),
  Title= and Escape=.
- **recordWalk** -- the live run. With JAWS or NVDA running as usual, it presses
  each step's key in the app, records the computer's own sound, writes it down
  with a local speech recognizer (faster-whisper), and reports, step by step:
  what the walk expected, what was heard, what UI Automation says has focus, and
  what the app said in its own speech log. Exit code 0 when every expected line
  was heard.
- **whoOpens** -- when a "Select an app to open this file" prompt appears from
  nowhere, it watches for OpenWith.exe and logs the program chain that caused it.

## A walk

A walk is a tutorial's format, so one file both teaches and tests. An app keeps
its walks in scripts\walks (DbDo's pilot.inix), and its tutorials in
help\Tutorial_NN_*.inix, which recordWalk also runs.

    [step]
    Say=Alt plus S opens Select Columns, which says what is shown before its buttons.
    Key=Alt+S
    Hear=Select Columns dialog
    Hear=Shown now
    Wait=6

- **Key** -- one key per step, in the suite's spelling (Alt+Shift+F, Control+F1).
- **Hear** -- a phrase the screen reader should say; matched loosely, by most of
  its words in any order, since speech recognition is not exact.
- **Say** -- the narrator's line, for the tutorial; recordWalk shows it in the
  report.
- **Type** -- text typed letter by letter before the key.
- **Wait** -- the longest to listen after the key, in seconds.

## Running recordWalk

    recordWalk                          the app's scripts\walks\pilot.inix
    recordWalk --walk help\Tutorial_03_Find_a_Station.inix
    recordWalk --steps 3                the first three steps only
    recordWalk --axe                    also scan after each step with Axe.Windows
    recordWalk --keep                   leave the app open at the end
    recordWalk --speaker Headphones     record that sound output
    recordWalk --model base.en          a faster, less accurate recognizer

- **Hands off.** It presses keys in the app; switching to another window stops
  it before the next step.
- **It listens for silence, not a clock.** Before each key it waits for the
  screen reader to be quiet; after it, it records until speech ends, up to 15
  seconds, and flags a step still speaking then.
- **The first run installs** pywinauto, comtypes, soundcard, numpy and
  faster-whisper for this user, and the speech model (about 500 MB), once.
- **Its report** is logs\<App>-recordWalk-<time>.md, with one .wav per step in
  results\recordWalk-<time>, to listen to what was really said.
- **Axe.Windows,** the engine of Accessibility Insights, is fetched once into
  %LOCALAPPDATA%\HomerDev\tools; --axe writes its findings per step and counts
  errors in the report.

## Accessibility scans

The kit's scripts\axeScan.py runs Axe.Windows, the rule engine of Accessibility Insights for Windows, and fetches its command-line tool once into %LOCALAPPDATA%\HomerDev\tools. It is used in three places:

- **The shared check, when asked:** `check --scan` starts a windowed app's program, scans its window, closes it by WM_CLOSE (nothing pressed), and writes logs\<App>-a11yScan-<time>.md. The verdict is a warning at most, never a failure. It is not run at every push: AxeWindowsCLI scans the whole program, and a window holding a long list (DbDo's 49,186 records) is beyond it. The Axe.Windows library can scan one window by its handle -- ScanOptions(scanId, scanRootWindowHandle), version 2.4.1 -- which a kit helper is to use for dialogs.
- **Walks:** `recordWalk --axe` scans after every step, saying so at the start and the total at the end; a scan that cannot finish stops the scans for the rest of the walk.
- **Tutorials performed live:** `recordWalk --tutorial --walk 1` drives the app through Tutorial 1 for real -- menus and all -- with the host's lines in one Windows voice (made into a file, never played, so they cannot spill into the reader's recording), the real screen reader recorded at each key, and the tutorial's simulated reading in a second voice; everything joins into results\recordWalk-<time>\<tutorial>-live.mp3, the step-by-step report beside it as always.
- **By hand:** `axeScan --exe <program>` or `axeScan --pid <id>`.

**A finding is a question, not an order.** Before changing anything, check what a screen reader user would meet. Never add an accessible name where the label just before a control in the focus order, its own caption (a check box, a button), or the window's title already names it: JAWS and NVDA say that name, and an accessible name with the same words is said twice -- an Lbc violation. Fix without asking only what is plainly a bug under Homer's rules, such as a name that repeats its control's kind, or a control the keyboard cannot reach; bring anything else to the person first. A finding reviewed and accepted goes in the app's a11yAccepted.txt, one per line, as the report prints it, and is no longer counted as new.

## What it has taught

- **Start every walk from the same state.** A grid left on other columns from an
  earlier test read a whole notes paragraph at each return; DbDo's pilot walk now
  first restores the default columns.
- **Expected words, not exact sentences.** Recognizers mishear names ("ACB" as
  "ACP"); a Hear line that names the essential words survives that.
- **Listen until silence.** Fixed listening windows cut long speech off and
  wasted time on short.
- **An app's own speech log is the tie-breaker** when the recording and the walk
  disagree: it shows what the app asked the screen reader to say.

## Confirming a tutorial

homer-tutorial writes a tutorial's Hear lines as what a screen reader should say,
marked to confirm with a live run. Run the tutorial as a walk with recordWalk,
compare its report's Heard lines with the Hear lines, and change whichever is
wrong -- the tutorial, or the app.
