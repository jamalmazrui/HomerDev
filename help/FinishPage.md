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

## Two entries per component

In Inno, `Check:` decides whether an entry is **shown**, not whether it is
ticked. So each component has two `[Run]` entries with the same label
function: one shown when the component is wanted (missing or stale), ticked;
one shown when it is current, carrying the `unchecked` flag. The reader sees
one box per component, with the right verb and the right default.

One entry gated on "wanted" is not enough: every component already present
simply vanishes from the page, and the person never sees a Reinstall box.

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
