---
title: "HomerDev History"
author: "Jamal Mazrui"
---

# History

# 1.0.0 -- 18 September 2026

First release. The kit was assembled by comparing every duplicated shared file
across DbDo, EdSharp, FileDir, HomerScribe and HomerView, and taking the better
version of each. What that comparison found is recorded here, because the
differences explain why the kit exists.

## Which version won, and why

- **Say.cs** -- byte for byte identical in DbDo, EdSharp and HomerScribe once
  line endings are normalized. The CRLF copy was taken.
- **Web.cs** -- identical in all four apps that carry it. The CRLF copy was
  taken.
- **Inix.cs** -- three generations were in circulation. DbDo and HomerScribe
  carried the original 29 KB codec. EdSharp carried the version that added
  `InixTable`, the converter between .inix, .csv, .tsv, Markdown and .xlsx.
  HomerView carried that plus `InixCodec.readValue`, the single-setting reader
  whose absence had every caller reading the whole file and walking the
  sections itself. HomerView's is a strict superset and was taken, which also
  means DbDo and HomerScribe had been two generations behind.
- **Lbc.cs** -- neither of the two newest copies was a superset of the other, so
  they were merged. EdSharp's is the base: it holds `LbcBandLayout`,
  `LbcBandDialog` and `LbcInixForm`, better access-key handling in the button
  row, the rule that Enter presses the button meaning accept wherever it sits,
  and `sortedIgnoringCase`. HomerScribe's contributed the horizontal band API --
  `addBand`, `endBand`, `bandTarget` and `addButton` -- with all thirteen `add`
  methods rerouted through `bandTarget()` and `addSeparator` closing an open
  band. Without that merge, HomerScribe would not compile against the kit and
  EdSharp would lose its form work.
- **KeyMap.cs, Keys.cs, Util.cs, inixVert.cs, PdfRead.cs** -- one copy each, no
  contest. Keys.cs came from HomerView, the rest from EdSharp and HomerScribe.
- **The Python homer package** -- only HomerView carries it, and it was already
  written to know nothing about HomerView.
- **tagRelease, cleanDir, tidyRepo, homerPolicy** -- these four say in their own
  headers that they are app-independent, and they are: tagRelease takes the app
  name from the directory, and cleanDir and tidyRepo decide what belongs by
  reading the project's own `<App>_setup.iss` and `RepoFiles.txt`. tidyRepo
  still named one app in five strings, and those were replaced with a name taken
  from the folder.
- **The install scripts for Pandoc, the GitHub CLI, Python, Node and Ollama** --
  these read as generic but each writes to its own app's folder and its own
  app's log, so they are not portable files. The pattern is documented in
  HomerDev.md instead, and the kit ships fresh generic `installOllama.cmd` and
  `installModels.cmd` for the local AI case.
- **The build script and the installer script** -- HomerScribe's are the newest
  and most refined of each, and became the templates.

## One behavior deliberately changed in the merge

HomerScribe's Lbc selects the text of the field that opens with the focus, and
extends that to the first focusable control rather than only an explicitly set
one. That was taken, with one change: a **multi-line** box now gets the caret at
position 0 instead of a full selection, because its value is a document rather
than a field and the Homer rule is that the caret opens on the first line. This
is the only place in the kit where the merged file is not simply the union of
what already existed.

## What is new rather than merged

- `buildHomerDev.cmd` and `.py` -- convert the documents and audit the kit:
  components present, encodings right, templates still holding their
  placeholder, no empty files.
- `newHomerApp.cmd` and `.py` -- write a new app folder from the templates.
- `Templates\_APP_.cs` -- a working launchpad app with the standard controls,
  the two message boxes, the matching command line, and settings saved as they
  are answered.
- `Templates\installOllama.cmd` and `installModels.cmd` -- local AI as an
  installer checkbox, now that more than one Homer app uses a model.
- The documentation set.
