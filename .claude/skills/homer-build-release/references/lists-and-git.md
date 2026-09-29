# Lists, whitelist and git rules

## Contents
- The three lists
- What stays tracked
- The whitelist .gitignore
- Folder layout

## The three lists

Each project root holds up to three plain lists, one entry per line: a file
path, a bare name, a pattern with `*`, or a folder ending in `/`. Lines
starting `#` or `;` are comments.

- **RepoFiles.txt**: everything the repository carries. It is the whole list;
  an installer's Source lines do not add to it.
- **LocalFiles.txt**: what belongs on this disk but never in git (built files,
  the installer, `version.txt` in apps, the release scripts, fetched DLLs).
- **KeepEncoding.txt**: files fixEncoding and check leave exactly as they are
  (third-party tools, dictionaries, each skill's SKILL.md).

## What stays tracked

tidy decides, for every tracked file, in this order:

1. Named **exactly** in RepoFiles.txt (a path, no wildcard): stays. This is
   how EdSharp keeps `Tektosyne.dll` despite `*.dll` in LocalFiles.txt.
2. Inside a **folder kept off the repository** but named more specifically in
   RepoFiles.txt (a carve-out, such as the kit's `exec/CSharp/` inside
   `exec/`): stays.
3. Matches the never-pushed list (`*.exe`, `*.log`, `Version.cs`,
   `/version.py`, `exec/`, `logs/`, `notes/`, `release.cmd`, `release.ps1`,
   `create*Repo.*` and others): untracked.
4. Matches LocalFiles.txt: untracked.
5. Named by RepoFiles.txt any other way: stays. Otherwise: untracked.

Untracking never deletes; the file stays on disk. A leading `/` anchors a name
to the project root, as in .gitignore.

## The whitelist .gitignore

tidy rewrites `.gitignore` on every run and push: ignore everything (`/*`),
put back what RepoFiles.txt names (a subfolder's parent first, since git never
looks inside an ignored folder), then the LocalFiles.txt and never-pushed
patterns, then exact RepoFiles names a pattern would hide, then carve-outs
(their outer folder written as `/exec/*`, so it is not ignored whole).
`.gitignore`, `.gitattributes` and `KeepEncoding.txt` are always put back.
`.gitattributes` is `* -text`: git stores the Homer CRLF files as they are, so
a project switched to it commits every text file once.

## Folder layout

- Top of the project: sources, build scripts, `<App>_setup.iss`, ReadMe,
  License, the three lists, `accept.inix`, and `<App>_setup.exe` once built.
- `exec`: the code the app's core runs on, in any form (the built program and
  its DLLs; in the kit, the libraries `exec/CSharp` and `exec/Python`).
- `scripts`: tools that maintain the code base or extend the app beyond its
  core; the kit's tools are refreshed here by each build.
- `help`: every document but ReadMe and License, each `.md` with a `.htm`.
- `configs`, `data`, `templates`, `logs`, and `notes` (strays; never in git).
- `.claude/skills`: Claude skills, one folder each.

Folders at the top start with different letters, for first-letter navigation.
