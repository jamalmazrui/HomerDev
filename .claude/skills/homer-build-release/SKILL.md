---
name: homer-build-release
description: >-
  Runs and troubleshoots the build, check, tidy, push and release cycle of a
  Homer Tools app or of the Homer Development Kit (HomerDev) itself, and reads
  the logs those steps leave. Use when the user uploads Homer logs (often as
  temp.zip) and says "continue", asks why a build, check, tidy, push or release
  failed, asks whether an app is released or which version is latest, or asks
  what to run next for an app in C:\<App> or C:\HomerDev.
---

# Homer build and release

Every Homer app lives in `C:\<App>` and is built against the kit in
`C:\HomerDev`. The kit is used at build time only; an installed app never needs
it. The user runs each step in a Windows console from the project folder, then
uploads the `logs` folder, usually zipped as `temp.zip`.

## Four kinds of resource

Before advising on any step, know what the folder holds: `kind` says app,
collection, kit or page, and why. Only an app runs the app build, uiCheck and
the tutorials; the kit uses build, checkHomerDev and releaseHomerDev; a
collection is pushed and tidied like an app but has no build or installer; a
page is published and released by `post`. The kit's HomerDev.md, under "Four
kinds of Homer resource", lists what every script does for each kind.

## Stages

Know which stage a release is meant to be before running it: a build (the
builder alone), a development release (public, labelled as development, for
the testers who asked for new work), or a release version (made from time to
time, for everybody, after a full JAWS and NVDA test pass, testers' real use,
current documents and, for an app, an installer tried on a fresh computer).
HomerDev.md, "Stages: from a build to a release version", gives the bar for
each. A serious problem in a release version is fixed through a development
release first.

## The cycle

The steps, in order, with the commands as the user types them (backslashes:
cmd reads a forward slash as a switch):

1. `build` in C:\HomerDev, whenever the kit changed. App builds find
   the kit's code in `exec\CSharp` and `exec\Python`, and stop if the kit is
   older than their `kitNeeded`.
2. `build` (or `build nobump` to keep the version). Steps the version
   in `version.txt`, compiles into `exec`, builds `<App>_setup.exe` at the top
   of the project, refreshes the kit's scripts into `scripts`.
3. A quick test of `exec\<App>.exe`.
4. `scripts\tidy`: files into place, strays into `notes`, a whitelist
   `.gitignore` from RepoFiles.txt, untracks what the whitelist leaves out.
   Acts in one run; nothing it moves is lost.
5. `scripts\push "What changed."`: tidy, commit, push.
6. `scripts\release`: runs `scripts\check`, tags, publishes the installer,
   then confirms GitHub's latest release is this one.

When a change touches only build scripts, a build with `nobump` proves it; a
release can wait for the app's next real change.

## Reading uploaded logs

Run the summary first, then read only the logs it points at:

```bash
python scripts/summarizeLogs.py /path/to/unzipped/logs
```

It reports, per app and task: build result, check counts and failures,
release outcome with version and whether GitHub confirmed it as latest, tidy
changes, and any ERROR lines. Uploads may hold unrelated `.log` files from
elsewhere on the machine and names with numeric suffixes added on upload; the
script ignores what is not `<App>-<task>-yyyyMMdd-HHmmss.log`.

Then:

- A **release** is done only when its log says `=== <App> <version> published`
  and `GitHub's latest release: v<version>`. "Already released" can mean a
  draft; see failures.md.
- A **check** failure names its check (documents, empty, encoding, keys,
  naming, accept, and so on); the check log has one line per finding.
- A **build** ends with `build end result=succeeded` or `result=failed`
  (older logs: "Build succeeded" / "Build FAILED"). Search upward from the end
  for the first ERROR.

## Answering

State what succeeded with versions, what failed and why, the fix delivered
as files in `<App>.zip` (never manual edits), and the numbered next steps as
commands. Deliver a kit change as `HomerDev.zip` and say the kit must be
built before the apps.

## References

- **Lists, whitelist and git rules** (RepoFiles.txt, LocalFiles.txt,
  KeepEncoding.txt, what stays tracked): read
  [references/lists-and-git.md](references/lists-and-git.md).
- **The log line format** and where each log is written: read
  [references/log-format.md](references/log-format.md).
- **Failures that have each cost a run**, with symptom, cause and fix: read
  [references/failures.md](references/failures.md) before diagnosing anything
  not explained by the log itself.
