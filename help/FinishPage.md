# The finish page: what is ticked and why

Every Homer installer ends with a list of checkboxes. This says what each kind
of box is called and whether it starts ticked, so that pressing Enter does the
right thing without reading the list.

## The rule

- **Install** a component or model that is missing — **ticked**
- **Update** a component whose newer version exists — **ticked**
- **Reinstall** something already current — **unticked**
- **Launch** the app — **ticked**
- **JAWS scripts** and the **NVDA add-on** are components like any other,
  with a box each: Install or Update **ticked**, Reinstall **unticked**
- **Open documentation** (the guide, the ReadMe) — **unticked**

So Enter installs everything missing, updates everything stale, puts the
screen-reader scripts in place, and starts the app. It reinstalls nothing that
is already current, and it does not open a browser window on top of the app.

## Why the ticks are the point

The label alone is not enough. A person arrowing down a finish page should be
able to trust that the default is the sensible thing, and only untick what they
do not want. A box that proposes what has already been done, or that opens a
document over the program they just installed, teaches the reader to stop
trusting the page.

## The order of the boxes

The finish page lists its boxes in this order, always:

1. **Install** boxes, ticked, in alphabetical order.
2. **Update** boxes, ticked, in alphabetical order.
3. **Reinstall** boxes, unticked, in alphabetical order.
4. **Launch the app**, ticked.
5. **Open the user guide**, unticked.

Alphabetical order is by the component's name, ignoring case, and the JAWS
scripts and the NVDA add-on take their places among the others: "ExifTool,
ffmpeg, ImageMagick, JAWS scripts, mpv, NVDA add-on, Ollama". Launch and the
guide always come last.

## Whether the screen reader support is current

The JAWS scripts and the NVDA add-on are judged as every component is, so the
box says Install, Update or Reinstall, and a person pressing Enter updates
only what is stale. `installScreenReaderSupport.cmd state jaws` and `state
nvda` answer for the installer:

- **JAWS**: a fingerprint of the script sources in `<App>_JAWS.zip` (their
  names and contents, not the zip's own bytes, which change with every build)
  is compared with the one written into each JAWS version's settings folder
  when the scripts last compiled there. None there: Install. Every version
  current: Reinstall. Otherwise, including a JAWS version installed since:
  Update. Scripts from before fingerprints were kept count as Update.
- **NVDA**: the version in the add-on's own `manifest.ini` is compared with
  the installed add-on's. Not installed: Install. Different: Update. The same:
  Reinstall.
- A reader not on the computer, or one the app ships nothing for, gets no box.

`homerReaderLabel`, `homerReaderIs` and `homerReaderState` in
HomerComponents.iss word and tick the boxes from that answer.

Inno shows `[Run]` entries in the order they are written, and `Check:` hides
the ones that do not apply. So each component gets three entries -- one per
verb, each with its own `Check:` -- and the page groups itself with no
sorting code. The kit supplies the checks: `homerIs(i, 0)` for Install,
`homerIs(i, 1)` for Update, `homerIs(i, 2)` for Reinstall, and
`homerModelIs(model, False)` / `homerModelIs(model, True)` for a model's
Install and Reinstall entries (a model has no Update: `ollama pull` always
fetches the current one). The Reinstall entries carry the `unchecked` flag.

One entry per component gated on "wanted" is not enough: every component
already present simply vanishes from the page, and the person never sees a
Reinstall box.

## How the wording is decided

A finish page is arrowed through, not studied, so each box says what it does in
the fewest words, and alike in every Homer installer:

- **The verb first** -- Install, Update or Reinstall -- then the name, then a
  version where one is known: "Update Ollama from 0.34.3 to 0.34.4".
- **A use in parentheses**, three or four words, for a component or a model:
  "Install Pandoc 3.11 (converts documents)". A size goes there too when it is
  large: "(translates text, about 4.7 GB)".
- **Screen readers get a box each, worded like any component**: "Install JAWS
  scripts", "Update NVDA add-on", "Reinstall JAWS scripts". A condition the box
  depends on may follow in parentheses: "(NVDA must be running)".
- **No word the tick already says**: not "recommended", not "(current version)"
  after Reinstall, not "for <App>" -- it is that app's installer.
- **Launch and the guide**: "Launch <App> (desktop hotkey Alt+Control+X)" and
  "Open the user guide (F1 in <App>)".
- **Only this app's components.** Offer what the app itself uses, and check
  its install scripts from before HomerDev to be sure: the spell checker
  belongs to EdSharp, Whisper to HomerScribe.
- **Shared components install machine-wide**, to their own default folders
  (Pandoc, Tesseract, ffmpeg, Ollama and the like), never inside the app's
  folder, where an upgrade would remove them.


The verb comes from what the machine actually has, worked out once per
component by `HomerComponents.iss`:

- `homerLabel(i)` gives "Install X <latest>", "Update X from <old> to <new>",
  or "Reinstall X <version>", with a three-or-four-word use in parentheses.
- `homerWanted(i)` is the `Check:` — true when missing or stale.
- `homerModelLabel(model, use, size)` and `homerModelWanted(model)` do the same
  for an Ollama model, asking `ollama list` rather than winget.

Detection tries every winget id, then the file, then the executable's own
`--version`, then the registry uninstall key — because the installer runs
elevated, where winget is often unreachable and per-user tools are not on the
PATH. Missing any one of these makes an installed component read as absent.

## Order in code

`homerOrder()` returns the component indices in the order above -- Install,
Update, Reinstall, alphabetical within each -- for anything that lists the
components itself, such as the Results box.

## The launch comes after the Results box

The launch entry does not start the app. It writes a marker, and the app is
started only after the Results box has been read and closed — otherwise the
new window takes focus and the screen reader begins announcing it over the
summary of what just happened. See `startIfAsked` in any Homer installer.

## The Results box afterwards

It is titled "<App> Setup Results": `homerResultsBox(sBody)` shows it through
Windows' own MessageBox, since Inno's MsgBox takes no title of its own. The box
that appears after the finish-page scripts have run reports **one line
per box that was ticked, and nothing else**. A component nobody asked about
is not an action taken this session, so it is not mentioned; when nothing was
ticked, the box says only that the app is installed and where the logs are.

Each line is in the past tense, from a probe made **after** the script ran:
"Whisper 1.9.4 was installed", "Ollama was updated from 0.34.3 to 0.34.4",
"Tesseract 5.4.0 was reinstalled", or "Whisper was not installed. Its log says
why." The probe made when the wizard opened is kept for the checkbox wording
and for the "before" half of the outcome; it is never what the Results box
reports, because by then it is a minute or more out of date.

What the box holds, learned from EdSharp and HomerView on 29 September 2026:

- **The first line says where the app is**: "EdSharp 5.0.30 is installed in
  C:\Program Files\EdSharp." **The last says where the logs are.** Nothing else
  but the ticked boxes' outcomes: no key hints, no "components" inventory, no
  reminders, no date line (the box has its own title).
- **The ticked captions are written down when Finish is pressed**, before any
  step runs, so a separate summary program can report only on them.
- **An Update says whether it happened.** "Update Python from 3.14.3 to 3.14.7"
  once ran and changed nothing, and the box said "Python: installed, 3.14.3";
  the line must compare the version found with the one offered: "updated to
  3.14.7", or "NOT updated -- still 3.14.3".
- **At most one blank line in a row**, whatever was ticked.

## Launch

The Launch box is ticked, like every Homer app's. Its [Run] entry only writes
a marker; the app is started when the Results box is closed, so the box is not
hidden behind the app, and with `ExecAsOriginalUser`, so it runs as the person
and not with the installer's elevated rights. EdSharp's Launch box was once
unticked, so pressing Enter installed it and never opened it.

The kit does this in three pieces: homerNoteTicked, called from
NextButtonClick when the page is wpFinished, records the ticked captions
before any script runs; homerOutcomeLine(i) and homerModelOutcomeLine(model,
use, size) each return a line when that box was ticked and an empty string
when it was not. The app adds each result to the box and skips the empty ones.

## Every verdict is logged

`homerState` writes one line per component to the setup log: what was found,
what is available, and whether its box offers Install, Update or Reinstall.
So a box that was ticked when it should not have been can be explained from
the log alone.

## Say "Downloading" before a long step

An install script says "Downloading" -- that plain word -- on the console
before anything that takes more than a few seconds, with a rough size and
time: "Downloading Ollama. This is about 1 GB and takes a few minutes." An
update path says so too: "Checking for a newer version" followed by a silent
two-minute download reads as a hang.

