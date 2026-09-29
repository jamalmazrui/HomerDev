---
name: homer-migrate
description: >-
  Brings an existing Windows app onto the Homer Development Kit, or audits a
  Homer app that has drifted from it: the build script's kit contract, the
  folder layout, the file lists, the installer, the acceptance checks, the
  version, Elevate and the documents, one app at a time, delivering only the
  files that change. Use when asked to migrate, convert, port or modernize an
  app to HomerDev, to audit an app against the kit, or to find out why an app
  that once built no longer builds after a kit change.
---

# Bringing an app onto the kit

Migrate one app at a time, from its current files, and deliver only what
changes, as `<App>.zip` for the user to unzip into `C:\<App>`. Never rebuild a
file from memory or from an old copy: another conversation may have changed
it since. When the copy at hand may be stale -- GitHub's, or one from days
ago -- ask for the current file before changing it.

## 1. Read before changing

Gather the app's build script (and any `.ps1` it runs), `<App>_setup.iss`,
`RepoFiles.txt`, `LocalFiles.txt`, `accept.inix`, the top of the project and
of `scripts`, and its newest build, check and release logs. Run the
homer-build-release summary on the logs. Note what the app does that the
kit's templates do not, so that nothing it needs is lost.

## 2. Work through the checklist

[references/audit-checklist.md](references/audit-checklist.md) is the list,
by area, with what each item looked like when it was wrong in an earlier
migration: the build script's kit contract, layout, lists, installer, checks,
version, Elevate, documents and logging. Go through every area; most apps
fail several.

## 3. Deliver and prove

1. Deliver the changed files and the kit, if the kit changed, stating which
   to unzip first: the kit, then the app.
2. The user runs `buildHomerDev` (when the kit changed), `build<App>`, a
   quick test, `scripts\tidy`, `scripts\push` and `scripts\release`.
3. Read the logs they send. The migration is done when the build succeeds,
   the check passes (acceptance included), and the release reports
   `GitHub's latest release: v<version>`.

Expect the first push after `.gitattributes` becomes `* -text` to show every
text file as changed, once; and expect `scripts\tidy` to untrack what
RepoFiles.txt leaves out, which is the point.

## Keep it moving

- A kit problem found while migrating is fixed in the kit, with a History
  entry, not worked around in the app.
- A decision that is the user's -- a key, a component, a document structure
  -- is asked as a numbered choice, with the other work delivered meanwhile.
- When an app's build script is its own copy of a template, a template change
  does not reach it: deliver its build script too.
