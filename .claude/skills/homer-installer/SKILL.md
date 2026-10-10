---
name: homer-installer
description: >-
  Writes and fixes the Inno Setup installer of a Homer Tools app: the kit's
  template and shared HomerComponents.iss, machine-wide installation, which
  optional components to offer, the finish page's checkbox wording, defaults,
  grouping and order, the JAWS and NVDA boxes, the Results box, and component
  logging. Use when creating or changing a _APP__setup.iss, when a finish-page
  box is worded, ticked or ordered wrongly, when a component is detected wrongly
  or reinstalled needlessly, or when an install script misbehaves.
---

# Homer installers

Each app has `<App>_setup.iss` at the top of its project, made from the kit's
`Templates/_APP__setup.iss`, and includes the kit's shared code with
`#include HomerDev + "\Templates\HomerComponents.iss"` inside `[Code]`. The
build passes the kit's folder as `/DHomerDev=` and the version it is building
as needed; the installer is written to the top of the project (`OutputDir=.`),
where the release script looks for it.

## Rules of the whole installer

- **Machine-wide, administrator only.** No per-user fallback; a portable user
  takes the zip.
- **The program in `{app}\exec`**, documents in `{app}\help`, install and
  support scripts in `{app}\scripts`, each script beside what it installs from.
  A [Run] entry and the [Files] entry it depends on must agree on the path.
- **Shared components go machine-wide**, to their own default folders, through
  their own install scripts (winget or the publisher's installer), never into
  the app's folder.
- **Offer only this app's components.** Check the app's install scripts from
  before HomerDev to see which it really uses.
- **Every install script** calls `scripts\installCommon.cmd`, writes its own
  log, and says "Downloading" with a rough size and time before a long step.
- **Pascal comments in [Code] are `//` or `(* *)`**; a `;` comment there stops
  the compile with "BEGIN expected".

## One pattern, checked

Every Homer installer follows one pattern, and `check` fails any that does
not, naming each departure. Pressing Enter through the wizard must do what
is wanted nine times in ten: install what is missing, update what is stale,
put the screen reader support in place, and start the app.

- **Include the kit's `Templates\HomerComponents.iss`** inside `[Code]`, and
  use its functions for every box: `homerAdd`, `homerLabel` and `homerIs`
  for components, and its own `labelJaws`, `isInstallJaws` and the rest for
  the screen readers. Never write your own state, label or check functions,
  never define `HomerReaderWrappersInApp`, and never stamp a version of your
  own: a verb must come from comparing what is installed with what is
  shipped, never from the app's version.
- **Run the kit's `installScreenReaderSupport.cmd`** for the JAWS and NVDA
  boxes. An app whose support needs more, as HomerView chains its scripts
  into JAWS's defaults, names its own script with
  `#define HomerReaderScript "installJawsScripts.cmd"` before the include;
  that script answers the kit's question, `state jaws <file>`, with install,
  update or reinstall, and the `[Run]` entries run it.
- **Remember the folder.** `UsePreviousAppDir=yes`, `DisableDirPage=auto` and
  a fixed `AppId`: a reinstall goes where the app already is, without asking.

## The finish page

Read [references/FinishPage.md](references/FinishPage.md) before writing or
changing any finish-page box: the ticked and unticked rule, the order (Install,
Update, Reinstall; screen readers first, JAWS then NVDA; then Launch and the
guide), the wording, the Results box, and the logging. In short: pressing
Enter on the finish page must install what is missing, update what is stale,
put the screen reader support in place and start the app -- and nothing else.

## Adding a component

Read [references/components.md](references/components.md) for the kit's calls:
declaring a component with `homerAdd`, the three [Run] entries per component
(Install, Update, Reinstall, each with its own `Check:`), the label and
outcome functions, and Ollama models.

## The Results box and Launch

One line per ticked box, the install location first and the logs folder last,
nothing else; an Update says whether it happened. Launch is ticked, leaves a
marker, and starts the app as the person once the Results box is closed.
FinishPage.md has the details, and components.md the failures that looked
like success.

## Checking an installer

After a change, build, then install on the machine and read two logs: the
setup log (`<App>-setup-<stamp>.log`), whose `Component <name>:` lines give
each verdict, and the Results box, which must name only what was ticked. A box
offered for something already current as Install, or a component the Results
box calls missing that the setup log found, points at detection; see
components.md.
