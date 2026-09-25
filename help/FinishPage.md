# The finish page: what is ticked and why

Every Homer installer ends with a list of checkboxes. This says what each kind
of box is called and whether it starts ticked, so that pressing Enter does the
right thing without reading the list.

## The rule

- **Install** a component or model that is missing — **ticked**
- **Update** a component whose newer version exists — **ticked**
- **Reinstall** something already current — **unticked**
- **Launch** the app — **ticked**
- **Install JAWS or NVDA scripts** — **ticked**
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

1. **Install** boxes, ticked. Screen reader scripts and add-ons come first;
   then the components, in alphabetical order.
2. **Update** boxes, ticked, in alphabetical order.
3. **Reinstall** boxes, unticked, in alphabetical order.
4. **Launch the app**, ticked.
5. **Open the user guide**, unticked.

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

## Order

Install first, then Reinstall, then Update, alphabetical within each. Launch
and documentation come last. `homerOrder()` returns the component indices in
that order.

## The launch comes after the Results box

The launch entry does not start the app. It writes a marker, and the app is
started only after the Results box has been read and closed — otherwise the
new window takes focus and the screen reader begins announcing it over the
summary of what just happened. See `startIfAsked` in any Homer installer.

## The Results box afterwards

The box that appears after the finish-page scripts have run reports **one line
per box that was ticked, and nothing else**. A component nobody asked about
is not an action taken this session, so it is not mentioned; when nothing was
ticked, the box says only that the app is installed and where the logs are.

Each line is in the past tense, from a probe made **after** the script ran:
"Whisper 1.9.4 was installed", "Ollama was updated from 0.34.3 to 0.34.4",
"Tesseract 5.4.0 was reinstalled", or "Whisper was not installed. Its log says
why." The probe made when the wizard opened is kept for the checkbox wording
and for the "before" half of the outcome; it is never what the Results box
reports, because by then it is a minute or more out of date.

The kit does this in three pieces: homerNoteTicked, called from
NextButtonClick when the page is wpFinished, records the ticked captions
before any script runs; homerOutcomeLine(i) and homerModelOutcomeLine(model,
use, size) each return a line when that box was ticked and an empty string
when it was not. The app adds each result to the box and skips the empty ones.

## Say "Downloading" before a long step

An install script says "Downloading" -- that plain word -- on the console
before anything that takes more than a few seconds, with a rough size and
time: "Downloading Ollama. This is about 1 GB and takes a few minutes." An
update path says so too: "Checking for a newer version" followed by a silent
two-minute download reads as a hang.

